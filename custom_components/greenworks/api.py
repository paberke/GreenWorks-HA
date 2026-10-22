"""Asynchroner Client fuer die Greenworks-Cloud (xapi.globetools.systems).

Basiert auf den Erkenntnissen aus Boes24/GreenWorks-Core (MIT-Lizenz),
ist aber tolerant gegenueber fehlenden oder neuen Feldern.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any

import aiohttp

from .const import (
    BASE_URL,
    CORP_ID,
    DP_DEVICE_INFO,
    DP_DRIVE_PAST_WIRE,
    DP_ERROR_HISTORY,
    DP_FIRMWARE,
    DP_SCHEDULE_READ,
    DP_SCHEDULE_WRITE,
    DP_START_POINTS,
    DP_WIRE_CORRIDOR,
    APPLICATION_KEY,
    FIRMWARE_URL,
    DP_LAST_ERROR,
    DP_POSITION,
    DP_STATISTICS,
    DP_STATUS_A,
    DP_STATUS_B,
    NO_TIMESTAMP,
)

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=20)


class GreenworksError(Exception):
    """Allgemeiner Fehler bei der Kommunikation mit der Cloud."""


class GreenworksAuthError(GreenworksError):
    """Falsches Passwort (von der Cloud mit Code 4001007 gemeldet)."""


class GreenworksLoginRejected(GreenworksError):
    """Anmeldung aus einem anderen Grund abgelehnt (z. B. unbekannte E-Mail,
    zu viele Versuche). Loest in HA keine Passwort-Abfrage aus."""


# Fehlercode der Cloud fuer ein falsches Passwort
ERROR_WRONG_PASSWORD = 4001007

# Mindestgueltigkeit eines Tokens, damit es keine Dauer-Neuanmeldung gibt
MIN_TOKEN_LIFETIME = 600


def _error_code(data: Any) -> int | None:
    """Fehlercode aus einer Cloud-Antwort wie {"error": {"code": ...}} lesen."""
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        return _to_int(data["error"].get("code"))
    return None


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------


def _parse_value(value: Any) -> Any:
    """Datenpunkte kommen oft als JSON-String - wenn moeglich auspacken."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in ("{", "["):
            try:
                return json.loads(stripped)
            except ValueError:
                return value
    return value


def _flatten_datapoint(value: Any) -> dict[str, Any]:
    """Fuehrt request und response eines Datenpunkts zu einem dict zusammen."""
    value = _parse_value(value)
    if not isinstance(value, dict):
        return {}
    merged: dict[str, Any] = {}
    for part in ("request", "response"):
        sub = value.get(part)
        if isinstance(sub, dict):
            merged.update(sub)
    if not merged:
        merged.update(value)
    return merged


def _blade_time(cutting_time: int | None, raw: Any) -> int | None:
    """Messer-Laufzeit wie die App: gesamte Maehzeit minus Summe der Reset-Staende."""
    if cutting_time is None:
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = None
    resets = raw.get("BladeUsageTime") if isinstance(raw, dict) else None
    if not isinstance(resets, list):
        resets = []  # noch nie zurueckgesetzt
    total = 0
    for value in resets:
        number = _to_int(value)
        if number is None:
            return None
        total += number
    result = cutting_time - total
    return result if result >= 0 else None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_timestamp(value: Any) -> datetime | None:
    """Unix-Zeit in datetime umwandeln, Platzhalter ergeben None."""
    ts = _to_int(value)
    if ts is None or ts <= 0 or ts >= NO_TIMESTAMP:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _to_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _parse_schedule(data: dict[str, Any]) -> dict[int, list[tuple[int, int]]] | None:
    """Wochenplan aus den Feldern <tag>_timer_<n>_... lesen."""
    if not any(k.endswith("_timer_mode") for k in data):
        return None
    plan: dict[int, list[tuple[int, int]]] = {}
    for idx, day in enumerate(WEEKDAYS):
        windows: list[tuple[int, int]] = []
        for slot in (1, 2):
            pre = f"{day}_timer_{slot}_"
            mode = _to_int(data.get(pre + "timer_mode"))
            hour = _to_int(data.get(pre + "start_time_hour"))
            minute = _to_int(data.get(pre + "start_time_minute"))
            length = _to_int(data.get(pre + "length_minutes"))
            if not mode or not length or hour is None or minute is None:
                continue
            if not (0 <= hour < 24 and 0 <= minute < 60 and 0 < length <= 1440):
                continue
            windows.append((hour * 60 + minute, length))
        plan[idx] = sorted(windows)
    return plan


def _dp_time(value: Any, *keys: str) -> datetime | None:
    flat = _flatten_datapoint(value)
    for key in keys:
        ts = _to_iso(flat.get(key))
        if ts:
            return ts
    return None


def _dp_newest(datapoints: dict[str, Any], keys: tuple[str, ...], needed: str):
    """Neuesten Datenpunkt (nach Antwort-/Anfragezeit) waehlen, der `needed` enthaelt."""
    best: tuple[datetime, dict[str, Any]] | None = None
    for key in keys:
        raw = datapoints.get(key)
        flat = _flatten_datapoint(raw)
        if not any(k.startswith(needed) for k in flat):
            continue
        when = _dp_time(raw, "response_time", "request_time") or datetime.min.replace(
            tzinfo=timezone.utc
        )
        if best is None or when > best[0]:
            best = (when, flat)
    return best


# --------------------------------------------------------------------------
# Datenmodell
# --------------------------------------------------------------------------


@dataclass
class GreenworksMower:
    """Aufbereitete Daten eines Maehers."""

    device_id: int
    product_id: str
    name: str
    serial: str | None = None
    online: bool | None = None
    model: str | None = None
    firmware: str | None = None

    state_code: int | None = None
    sub_state_code: int | None = None
    park_reason: int | None = None
    battery: int | None = None
    next_start: datetime | None = None
    status_time: datetime | None = None
    signal_quality: int | None = None

    rain_sensor: bool | None = None
    frost_sensor: bool | None = None

    last_error_code: int | None = None
    last_error_time: datetime | None = None
    fatal_errors: int | None = None

    statistics_time: datetime | None = None
    cutting_time: int | None = None
    running_time: int | None = None
    charging_time: int | None = None
    # Maehzeit der Messer seit dem letzten Zuruecksetzen in der App (Sekunden)
    blade_time: int | None = None
    # Seit der letzten echten Statistik mitgezaehlte Maehzeit (Sekunden)
    counted_cutting: int = 0

    latitude: float | None = None
    longitude: float | None = None
    gps_accuracy: float | None = None

    # Maehplan: Wochentag (0 = Montag) -> Liste (Startminute, Dauer in Minuten)
    schedule: dict[int, list[tuple[int, int]]] | None = None
    schedule_time: datetime | None = None
    # Fehlerverlauf: (Zeitpunkt, Fehlercode), neueste zuerst
    error_history: list[tuple[datetime, int]] | None = None
    error_history_time: datetime | None = None
    # Softwarestaende weiterer Bauteile
    sw_cutting: str | None = None
    sw_charging_station: str | None = None
    # Volle Version (z. B. "6.65.1775739325") und Geraetekennung fuer die Update-Pruefung
    firmware_full: str | None = None
    device_type: str | None = None

    # Nur in Home Assistant: Winterpause eingeschaltet, offline seit
    winter_pause: bool = False
    offline_since: datetime | None = None

    # Einstellungen (nur Anzeige; aktuell, wenn die App sie zuletzt gelesen hat)
    drive_past_wire: int | None = None  # Millimeter
    drive_past_wire_time: datetime | None = None
    # "boundary" / "guide_1" / "guide_2" -> (min, max)
    wire_corridor: dict[str, tuple[int, int]] | None = None
    wire_corridor_time: datetime | None = None
    # (Nummer, Draht-Art, Entfernung in m, Anteil der Starts in %)
    start_points: list[tuple[int, int, int, int]] | None = None
    start_points_time: datetime | None = None

    raw_properties: dict[str, Any] = field(default_factory=dict)
    raw_datapoints: dict[str, Any] = field(default_factory=dict)


def build_mower(
    device: dict[str, Any],
    properties: dict[str, Any],
    datapoints: dict[str, Any],
) -> GreenworksMower:
    """Baut aus den drei Cloud-Antworten ein GreenworksMower-Objekt."""
    mower = GreenworksMower(
        device_id=int(device.get("id")),
        product_id=str(device.get("product_id")),
        name=str(device.get("name") or "Greenworks"),
        serial=(str(device["sn"]) if device.get("sn") else None),
        online=device.get("is_online"),
        raw_properties=properties,
        raw_datapoints={k: _parse_value(v) for k, v in datapoints.items()},
    )

    # --- Eigenschaften ----------------------------------------------------
    mower.model = properties.get("device_model_name") or None
    if "is_rain_sensor_on" in properties:
        mower.rain_sensor = bool(properties["is_rain_sensor_on"])
    if "is_frost_sensor_on" in properties:
        mower.frost_sensor = bool(properties["is_frost_sensor_on"])

    # --- Online-Status aus den Datenpunkten, falls vorhanden ---------------
    if isinstance(datapoints.get("online"), bool):
        mower.online = datapoints["online"]

    # --- Status: der neuere von Datenpunkt 31 und 32 ----------------------
    candidates = [
        _flatten_datapoint(datapoints.get(key))
        for key in (DP_STATUS_A, DP_STATUS_B)
    ]
    candidates = [c for c in candidates if "mower_main_state" in c]
    if candidates:
        candidates.sort(
            key=lambda c: _to_iso(c.get("request_time"))
            or datetime.min.replace(tzinfo=timezone.utc)
        )
        status = candidates[-1]
        mower.state_code = _to_int(status.get("mower_main_state"))
        mower.sub_state_code = _to_int(status.get("mower_sub_state"))
        mower.park_reason = _to_int(status.get("source_for_next_start"))
        battery = _to_int(status.get("battery_status"))
        mower.battery = battery if battery is not None and 0 <= battery <= 100 else None
        mower.next_start = _to_timestamp(status.get("next_start"))
        mower.status_time = _to_iso(status.get("request_time"))
        # Signalstaerke steht nicht in jedem Status-Datenpunkt
        for cand in reversed(candidates):
            if "signal_quality" in cand:
                mower.signal_quality = _to_int(cand.get("signal_quality"))
                break

    # --- Letzter Fehler ----------------------------------------------------
    err = _flatten_datapoint(datapoints.get(DP_LAST_ERROR))
    if err:
        mower.last_error_code = _to_int(err.get("event_id"))
        mower.last_error_time = _to_timestamp(err.get("timestamp_for_error"))
        # Ist die Fehlermeldung neuer als die letzte Statusmeldung, gilt der
        # Zustand aus der Fehlermeldung (sonst bliebe z. B. "Sucht Station" stehen,
        # obwohl der Maeher mit Fehler steht).
        err_state = _to_int(err.get("current_mower_main_state"))
        err_received = _to_iso(err.get("request_time"))
        if (
            err_state is not None
            and 0 <= err_state <= 12
            and err_received is not None
            and (mower.status_time is None or err_received > mower.status_time)
        ):
            mower.state_code = err_state
            mower.sub_state_code = _to_int(err.get("mower_sub_state"))
            mower.park_reason = None
            mower.status_time = err_received

    # --- Statistik ---------------------------------------------------------
    stats = _flatten_datapoint(datapoints.get(DP_STATISTICS))
    if stats:
        mower.cutting_time = _to_int(stats.get("cutting_time"))
        mower.running_time = _to_int(stats.get("running_time"))
        mower.charging_time = _to_int(stats.get("charging_time"))
        mower.fatal_errors = _to_int(stats.get("no_of_fatal_error"))
        # Zeitpunkt, zu dem der Maeher die Statistik zuletzt geschickt hat
        # (nur wenn die App sie abfragt)
        mower.statistics_time = _to_iso(stats.get("response_time")) or _to_iso(
            stats.get("request_time")
        )

    # --- Messer-Laufzeit (wie in der App: Maehzeit minus Stand beim Zuruecksetzen) ---
    mower.blade_time = _blade_time(mower.cutting_time, properties.get("device_blade_usage_time"))

    # --- Firmware ----------------------------------------------------------
    fw = _flatten_datapoint(datapoints.get(DP_FIRMWARE))
    major = fw.get("mower_main_application_major_sw_version")
    minor = fw.get("mower_main_application_minor_sw_version")
    if major is not None and minor is not None:
        mower.firmware = f"{major}.{minor}"
        build = fw.get("mower_main_application_build_no")
        mower.firmware_full = f"{major}.{minor}.{build}" if build is not None else mower.firmware

    # --- Geraetekennung (Gruppe.Untergeraet.Variante) aus Datenpunkt 25 -------
    ident = _flatten_datapoint(datapoints.get(DP_DEVICE_INFO))
    parts = [ident.get(k) for k in ("device_group_no", "sub_device_no", "variant_no")]
    if all(p is not None for p in parts):
        mower.device_type = ".".join(str(p) for p in parts)

    # --- Softwarestaende von Maehwerk und Ladestation ---------------------
    for attr, prefix in (("sw_cutting", "mower_cutting"), ("sw_charging_station", "mower_cs")):
        major = fw.get(f"{prefix}_application_major_sw_version")
        minor = fw.get(f"{prefix}_application_minor_sw_version")
        if major is not None and minor is not None:
            setattr(mower, attr, f"{major}.{minor}")

    # --- Maehplan: 125 (gelesen) oder 124 (zuletzt gespeichert), der neuere --
    plans = []
    for key, time_keys in (
        (DP_SCHEDULE_READ, ("response_time", "request_time")),
        (DP_SCHEDULE_WRITE, ("request_time",)),
    ):
        raw = datapoints.get(key)
        plan = _parse_schedule(_flatten_datapoint(raw))
        if plan is not None:
            plans.append((_dp_time(raw, *time_keys), plan))
    if plans:
        plans.sort(key=lambda p: p[0] or datetime.min.replace(tzinfo=timezone.utc))
        mower.schedule_time, mower.schedule = plans[-1]

    # --- Fehlerverlauf (nur aktuell, wenn die App die Fehlerliste abfragt) --
    hist = _flatten_datapoint(datapoints.get(DP_ERROR_HISTORY)).get("data")
    if isinstance(hist, list):
        entries = []
        for item in hist:
            if not isinstance(item, dict):
                continue
            code = _to_int(item.get("event_id"))
            when = _to_timestamp(item.get("timestamp"))
            if code is not None and when is not None:
                entries.append((when, code))
        entries.sort(key=lambda e: e[0], reverse=True)
        mower.error_history = entries
        mower.error_history_time = _dp_time(
            datapoints.get(DP_ERROR_HISTORY), "response_time", "request_time"
        )

    # --- Einstellungen: Ueberfahrweite (89 gesetzt / 90 gelesen) ------------
    found = _dp_newest(datapoints, DP_DRIVE_PAST_WIRE, "drive_past_wire_distance")
    if found:
        value = _to_int(found[1].get("drive_past_wire_distance"))
        if value is not None and 0 < value <= 1000:
            mower.drive_past_wire, mower.drive_past_wire_time = value, found[0]

    # --- Einstellungen: Abstand beim Drahtfolgen (55/56 gesetzt, 122 gelesen) --
    found = _dp_newest(datapoints, DP_WIRE_CORRIDOR, "min_distance_to_boundary_wire")
    if found:
        flat, corridor = found[1], {}
        for name, prefix in (
            ("boundary", "boundary"),
            ("guide_1", "guide_wire_1"),
            ("guide_2", "guide_wire_2"),
        ):
            lo = _to_int(flat.get(f"min_distance_to_{prefix}_wire", flat.get(f"min_distance_to_{prefix}")))
            hi = _to_int(flat.get(f"max_distance_to_{prefix}_wire", flat.get(f"max_distance_to_{prefix}")))
            if lo is not None and hi is not None:
                corridor[name] = (lo, hi)
        if corridor:
            mower.wire_corridor, mower.wire_corridor_time = corridor, found[0]

    # --- Einstellungen: Startpunkte (58-60 gesetzt, 123 gelesen) -------------
    found = _dp_newest(datapoints, DP_START_POINTS, "start_position_1_")
    if found:
        flat, points = found[1], []
        for n in range(1, 6):
            how = _to_int(flat.get(f"start_position_{n}_how"))
            dist = _to_int(flat.get(f"start_position_{n}_distance"))
            often = _to_int(flat.get(f"start_position_{n}_how_often"))
            if how is None or dist is None or not often or not 0 < often <= 100:
                continue  # Startpunkt nicht belegt
            points.append((n, how, dist, often))
        mower.start_points, mower.start_points_time = points, found[0]

    # --- Position ----------------------------------------------------------
    pos = _flatten_datapoint(datapoints.get(DP_POSITION))
    lat, lon = _to_float(pos.get("latitude")), _to_float(pos.get("longitude"))
    if (
        lat is not None
        and lon is not None
        and -90 <= lat <= 90
        and -180 <= lon <= 180
        and not (lat == 0 and lon == 0)
    ):
        mower.latitude, mower.longitude = lat, lon
        hdop = _to_float(pos.get("hdop"))
        # grobe Umrechnung HDOP -> Meter (ca. 5 m pro HDOP-Einheit)
        mower.gps_accuracy = round(hdop * 5, 1) if hdop is not None else None

    return mower


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------


class GreenworksClient:
    """Minimaler Client fuer die Greenworks-Cloud."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: float = 0
        self.user_id: int | None = None
        self._lock = asyncio.Lock()

    # --- Anmeldung -------------------------------------------------------

    async def async_login(self) -> None:
        """Mit E-Mail und Passwort anmelden."""
        body = {"corp_id": CORP_ID, "email": self._email, "password": self._password}
        try:
            async with self._session.post(
                f"{BASE_URL}user_auth", json=body, timeout=TIMEOUT
            ) as resp:
                data = await resp.json(content_type=None)
                status = resp.status
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise GreenworksError(f"Login nicht moeglich: {err}") from err

        if status != 200:
            code = _error_code(data)
            if code == ERROR_WRONG_PASSWORD:
                raise GreenworksAuthError("Falsches Passwort (Code 4001007)")
            if status in (400, 401, 403):
                raise GreenworksLoginRejected(
                    f"Login abgelehnt (HTTP {status}, Code {code}): {data}"
                )
        if status != 200 or not isinstance(data, dict) or "access_token" not in data:
            raise GreenworksError(f"Unerwartete Login-Antwort (HTTP {status})")

        self._store_tokens(data)
        self.user_id = data.get("user_id")
        _LOGGER.debug("Greenworks-Login erfolgreich (user_id=%s)", self.user_id)

    def _store_tokens(self, data: dict[str, Any]) -> None:
        self._access_token = data.get("access_token")
        self._refresh_token = data.get("refresh_token") or self._refresh_token
        expire_in = _to_int(data.get("expire_in")) or 3600
        # 5 Minuten Puffer, aber nie kuerzer als MIN_TOKEN_LIFETIME
        lifetime = max(expire_in - 300, MIN_TOKEN_LIFETIME)
        self._expires_at = time.time() + lifetime

    async def _async_refresh(self) -> None:
        """Token erneuern, bei Problemen neu anmelden."""
        if not self._refresh_token:
            await self.async_login()
            return
        try:
            async with self._session.post(
                f"{BASE_URL}user/token/refresh",
                json={"refresh_token": self._refresh_token},
                headers={"Access-Token": self._access_token or ""},
                timeout=TIMEOUT,
            ) as resp:
                data = await resp.json(content_type=None)
                ok = resp.status == 200 and isinstance(data, dict) and "access_token" in data
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            ok = False
            data = None
        if ok:
            self._store_tokens(data)
        else:
            await self.async_login()

    async def _async_ensure_token(self) -> None:
        async with self._lock:
            if self._access_token is None:
                await self.async_login()
            elif time.time() > self._expires_at:
                await self._async_refresh()

    # --- Anfragen ----------------------------------------------------------

    async def _async_get(
        self, path: str, params: dict[str, str] | None = None, _retry: bool = True
    ) -> Any:
        await self._async_ensure_token()
        try:
            async with self._session.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"Access-Token": self._access_token or ""},
                timeout=TIMEOUT,
            ) as resp:
                status = resp.status
                try:
                    data = await resp.json(content_type=None)
                except ValueError:
                    # z. B. leere Antwort bei 401: trotzdem neu anmelden koennen
                    data = None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise GreenworksError(f"Anfrage {path} fehlgeschlagen: {err}") from err
        if status == 200 and data is None:
            raise GreenworksError(f"Anfrage {path}: Antwort ist kein JSON")

        if status in (401, 403) and _retry:
            _LOGGER.debug("Token abgelehnt (HTTP %s), melde neu an", status)
            async with self._lock:
                await self.async_login()
            return await self._async_get(path, params, _retry=False)
        if status in (401, 403):
            # Neu angemeldet und trotzdem abgelehnt: kein Passwortproblem
            raise GreenworksError(f"Zugriff verweigert (HTTP {status})")
        if status != 200:
            raise GreenworksError(f"Anfrage {path}: HTTP {status}")
        return data

    async def async_get_devices(self) -> list[dict[str, Any]]:
        if self.user_id is None:
            await self.async_login()
        data = await self._async_get(
            f"user/{self.user_id}/subscribe/devices", {"version": "0"}
        )
        devices = data.get("list") if isinstance(data, dict) else None
        return devices if isinstance(devices, list) else []

    async def async_check_firmware(self, mower: GreenworksMower) -> dict[str, Any]:
        """Beim Update-Server von Greenworks fragen, ob es neue Maeher-Software gibt.

        Gleiche Anfrage wie die App auf ihrer Seite "Software". Es wird nur gelesen,
        am Maeher aendert sich dadurch nichts.
        """
        if not mower.device_type or not mower.firmware_full:
            raise GreenworksError("Geraetekennung oder Softwarestand unbekannt")
        await self._async_ensure_token()
        url = (
            f"{FIRMWARE_URL}api/Update/v2/DeviceSwUpdateLink/RLM2/"
            f"{mower.device_type}/{mower.firmware_full}"
        )
        body = {
            "brand": "Greenworks",
            "deviceIdentifyCode": mower.serial or "",
            "model": mower.model or "",
            "region": "eu",
        }
        headers = {
            "ApplicationKey": APPLICATION_KEY,
            "Brand": "Greenworks",
            "Access-Token": self._access_token or "",
            "Xlink-Access-Token": self._access_token or "",
            "Content-Type": "application/json",
        }
        if self.user_id is not None:
            headers["Xlink-User-Id"] = str(self.user_id)
        try:
            async with self._session.post(
                url, json=body, headers=headers, timeout=TIMEOUT
            ) as resp:
                status = resp.status
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise GreenworksError(f"Update-Pruefung nicht moeglich: {err}") from err
        if status != 200 or not isinstance(data, dict):
            raise GreenworksError(f"Update-Pruefung: HTTP {status}")
        # Feldnamen wie in der App; manche Server schreiben sie anders gross
        lower = {str(k).lower(): v for k, v in data.items()}
        if "isneedupdate" not in lower:
            raise GreenworksError(f"Update-Pruefung: unbekannte Antwort {sorted(data)}")
        return {
            "need_update": bool(lower.get("isneedupdate")),
            "current_version": lower.get("currentversion"),
            "target_version": lower.get("targetversion") or lower.get("downloadversion"),
            "name": lower.get("name"),
        }

    async def async_get_mowers(self) -> dict[int, GreenworksMower]:
        """Alle Maeher des Kontos mit aktuellen Daten abrufen."""
        result: dict[int, GreenworksMower] = {}
        for device in await self.async_get_devices():
            pid, did = device.get("product_id"), device.get("id")
            if pid is None or did is None:
                continue
            try:
                properties = await self._async_get(f"product/{pid}/device/{did}/property")
            except GreenworksAuthError:
                raise
            except GreenworksError as err:
                _LOGGER.debug("Eigenschaften fuer %s nicht abrufbar: %s", did, err)
                properties = {}
            datapoints = await self._async_get(f"product/{pid}/v_device/{did}")
            mower = build_mower(
                device,
                properties if isinstance(properties, dict) else {},
                datapoints if isinstance(datapoints, dict) else {},
            )
            result[mower.device_id] = mower
        return result


# Version 0.3.0

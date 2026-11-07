"""Steuerung des Maehers ueber den MQTT-Kanal der Greenworks-Cloud.

Nur aktiv, wenn unter "Konfigurieren" die Steuerung auf "Lesen und steuern"
steht. Die Befehle sind genau die, die auch die Greenworks-App schickt
(Parken, Starten, Pause, Maehen ohne Unterbrechung, Maehplan speichern).
Andere Einstellungen werden nie geschrieben.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import hashlib
import json
import logging
import secrets
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util
from homeassistant.util.ssl import client_context

from .const import DOMAIN

if TYPE_CHECKING:
    from .api import GreenworksClient

_LOGGER = logging.getLogger(__name__)

MQTT_HOST = "mqtt.globetools.systems"
MQTT_PORT = 1884
# Antworten des Maehers kommen auf $6, Befehle gehen an $7
TOPIC_REPLY = "$6"
TOPIC_COMMAND = "$7"
CONFIRM_TIMEOUT = 30  # Sekunden

# Befehle wie in der App: (Kopf bis vor die Daten, Erkennung der Antwort)
_PARK = ("0007000b003e6000A005e60002", "e60002")
_START = ("0007000d003a6000A007e40004", "e400040000")
_PAUSE = ("0007000b00386000A005e20002", "e200020000")
_CONTINUOUS = ("0007000c00366000A0064a0103", "4a0103")
# Nach einem erfolgreichen Befehl fragt die App den Status neu ab
_STATUS_REQUEST = "0007000900406000A003500000"
# Abfrage "Maehen ohne Unterbrechung" (wie die App auf der Seite Zeitplan)
_CONTINUOUS_REQUEST = "0007000900346000A0034c0100"
_CONTINUOUS_QUERY_KEY = "4c0100"
# Abfragen, deren Antwort komplett gebraucht wird (Maehplan lesen)
_QUERY_KEYS = ("420100",)

PARK_UNTIL_FURTHER_NOTICE = 0xFFFE
# Eigene Zeit wie in der App: 1 bis 24 Stunden bzw. Tage
MAX_PARK_HOURS = 24
MAX_CONTINUOUS_DAYS = 24


def le16(value: int) -> str:
    """Zahl als 2 Byte, niedriges Byte zuerst (wie StringUtils.getPin der App)."""
    if not 0 <= value <= 0xFFFF:
        raise ValueError(value)
    return f"{value & 0xFF:02x}{value >> 8:02x}"


def minutes_until_midnight(now: datetime | None = None) -> int:
    """Minuten bis 23:59:59 heute (wie "Fuer den Rest des Tages" in der App)."""
    now = now or dt_util.now()
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return max(int((end - now).total_seconds() // 60), 1)


def park_payload(minutes: int | None) -> str:
    """Parken fuer X Minuten, None = bis auf Weiteres."""
    value = PARK_UNTIL_FURTHER_NOTICE if minutes is None else minutes
    return _PARK[0] + le16(value)


def start_payload(pin: int | None = None) -> str:
    """Maehen starten bzw. Zeitplan fortsetzen.

    Ohne PIN wie bisher 0000. Mit PIN wie die App nach der PIN-Abfrage:
    die vierstellige PIN als Zahl, niedriges Byte zuerst.
    """
    return _START[0] + le16(0) + le16(pin or 0)


def pause_payload() -> str:
    return _PAUSE[0] + "0000"


def continuous_payload(minutes: int) -> str:
    """Maehen ohne Unterbrechung fuer X Minuten, 0 = aus."""
    if minutes <= 0:
        return _CONTINUOUS[0] + "000000"
    return _CONTINUOUS[0] + le16(minutes) + "01"


def _reply_key(payload: str) -> str:
    """Woran die Antwort des Maehers zu erkennen ist (Anfang von request_payload)."""
    body = payload[20:].lower()  # ohne Kopf "0007LLLLMMMM6000A0NN"
    for _, key in (_PARK, _START, _PAUSE, _CONTINUOUS):
        if body.startswith(key):
            return key
    return body[:6]


def parse_reply(raw: bytes) -> dict[str, Any] | None:
    """Antwort vom Thema $6: vor dem JSON stehen ein paar Bytes Kopf."""
    # Der Kopf kann selbst ein "{" enthalten (z. B. als Laengenbyte bei langen
    # Antworten wie dem Maehplan): dann ab dem naechsten "{" versuchen
    start = raw.find(b"{")
    tries = 0
    while 0 <= start and tries < 4:
        try:
            data = json.loads(raw[start:].decode("utf-8", "replace"))
        except ValueError:
            start = raw.find(b"{", start + 1)
            tries += 1
            continue
        return data if isinstance(data, dict) else None
    return None


class GreenworksControl:
    """MQTT-Verbindung zum Senden von Befehlen und Empfangen der Bestaetigung."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: GreenworksClient,
        device_ids: list[int],
        on_continuous: Callable[[int, datetime | None], None] | None = None,
    ) -> None:
        self._hass = hass
        # Wird mit (device_id, Ende oder None) aufgerufen, wenn der Maeher den
        # Stand "Maehen ohne Unterbrechung" meldet
        self._on_continuous = on_continuous
        self._api = client
        self._device_ids = device_ids
        self._mqtt: Any = None
        self.connected = False
        # Wartende Befehle: (device_id, Erkennung) -> Future
        self._waiting: dict[tuple[str, str], asyncio.Future[bool]] = {}
        # Wartende Abfragen (z. B. Maehplan lesen): (device_id, Erkennung) -> Antwort
        self._queries: dict[tuple[str, str], asyncio.Future[dict[str, Any]]] = {}

    def _credentials(self) -> tuple[str, str]:
        user = str(self._api.user_id)
        password = hashlib.md5(f"{user}{self._api.authorize}".encode()).hexdigest()
        return user, password

    async def async_start(self) -> None:
        """Verbindung im Hintergrund aufbauen."""
        if not self._api.authorize or not self._api.user_id:
            _LOGGER.warning(
                "Steuerung nicht moeglich: die Greenworks-Anmeldung liefert keinen "
                "Schluessel fuer den Steuerkanal"
            )
            return
        context = await self._hass.async_add_executor_job(client_context)
        await self._hass.async_add_executor_job(self._start, context)

    def _start(self, context: Any) -> None:
        import paho.mqtt.client as mqtt  # noqa: PLC0415

        client_id = f"X:APP;A:4;V:1;RES:{secrets.token_hex(8)};"
        if hasattr(mqtt, "CallbackAPIVersion"):  # paho 2.x (ab HA 2025.3)
            client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                clean_session=True,
            )
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
        else:  # paho 1.x (HA 2025.2)
            client = mqtt.Client(client_id=client_id, clean_session=True)
            client.on_connect = lambda c, u, f, rc: self._on_connect(c, u, f, _Rc(rc), None)
            client.on_disconnect = lambda c, u, rc: self._on_disconnect(c, u, None, _Rc(rc), None)
        client.tls_set_context(context)
        client.username_pw_set(*self._credentials())
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=10, max_delay=300)
        self._mqtt = client
        client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            _LOGGER.warning("Steuerkanal: Anmeldung abgelehnt (%s)", reason_code)
            return
        for device_id in self._device_ids:
            client.subscribe(f"{TOPIC_REPLY}/{device_id}", qos=1)
        self.connected = True
        _LOGGER.debug("Steuerkanal verbunden")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        self.connected = False
        _LOGGER.debug("Steuerkanal getrennt (%s)", reason_code)
        # Das Passwort haengt an der letzten Anmeldung: vor dem Neuverbinden aktualisieren
        if self._api.authorize:
            client.username_pw_set(*self._credentials())

    def _on_message(self, client, userdata, message) -> None:
        reply = parse_reply(bytes(message.payload))
        if reply is None:
            return
        request = reply.get("request") or {}
        payload = str(request.get("request_payload", "")).lower()
        if not payload:
            return
        device_id = message.topic.partition("/")[2]
        _LOGGER.debug("Antwort von %s auf %s", device_id, payload[:6])
        if payload.startswith(_QUERY_KEYS):
            # Antwort auf eine Abfrage (Maehplan lesen): komplett weiterreichen
            self._hass.loop.call_soon_threadsafe(
                self._resolve_query, device_id, payload, reply
            )
            return
        if payload.startswith(_CONTINUOUS_QUERY_KEY):
            response = reply.get("response") or {}
            if "time_minute" in response:
                self._hass.loop.call_soon_threadsafe(
                    self._continuous_reply, device_id, response
                )
            return
        ok = json.dumps(reply.get("response")).replace(" ", "").find('"return_code":0') >= 0
        self._hass.loop.call_soon_threadsafe(self._resolve, device_id, payload, ok)

    @callback
    def _continuous_reply(self, device_id: str, response: dict[str, Any]) -> None:
        if self._on_continuous is None or not device_id.isdigit():
            return
        try:
            minutes = int(response.get("time_minute") or 0)
            option = int(response.get("override_option") or 0)
        except (TypeError, ValueError):
            return
        until = (
            dt_util.utcnow() + timedelta(minutes=minutes)
            if minutes and option in (1, 2)
            else None
        )
        self._on_continuous(int(device_id), until)

    @callback
    def _resolve(self, device_id: str, payload: str, ok: bool) -> None:
        for (dev, key), future in list(self._waiting.items()):
            if dev == device_id and payload.startswith(key) and not future.done():
                future.set_result(ok)

    @callback
    def _resolve_query(self, device_id: str, payload: str, reply: dict[str, Any]) -> None:
        for (dev, key), future in list(self._queries.items()):
            if dev == device_id and payload.startswith(key) and not future.done():
                future.set_result(reply)

    async def async_query(
        self, device_id: int, payload: str, key: str
    ) -> dict[str, Any]:
        """Abfrage senden (aendert nichts am Maeher) und die Antwort zurueckgeben."""
        if self._mqtt is None or not self.connected:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_not_connected"
            )
        wait_key = (str(device_id), key)
        future: asyncio.Future[dict[str, Any]] = self._hass.loop.create_future()
        self._queries[wait_key] = future
        _LOGGER.debug("Abfrage an %s: %s", device_id, payload[20:])
        try:
            await self._hass.async_add_executor_job(
                self._mqtt.publish,
                f"{TOPIC_COMMAND}/{device_id}",
                bytes.fromhex(payload),
                1,
            )
            async with asyncio.timeout(CONFIRM_TIMEOUT):
                return await future
        except TimeoutError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_no_reply"
            ) from err
        finally:
            self._queries.pop(wait_key, None)

    async def async_send(
        self, device_id: int, payload: str, timeout: float | None = None
    ) -> None:
        """Befehl senden und auf die Bestaetigung des Maehers warten."""
        if self._mqtt is None or not self.connected:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_not_connected"
            )
        key = (str(device_id), _reply_key(payload))
        future: asyncio.Future[bool] = self._hass.loop.create_future()
        self._waiting[key] = future
        topic = f"{TOPIC_COMMAND}/{device_id}"
        _LOGGER.debug("Sende Befehl an %s: %s", device_id, payload[20:])
        try:
            await self._hass.async_add_executor_job(
                self._mqtt.publish, topic, bytes.fromhex(payload), 1
            )
            async with asyncio.timeout(timeout or CONFIRM_TIMEOUT):
                ok = await future
        except TimeoutError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_no_reply"
            ) from err
        finally:
            self._waiting.pop(key, None)
        if not ok:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="control_rejected"
            )
        # Wie die App: Stand neu abfragen, damit die Anzeige schnell nachzieht
        follow_up = (
            _CONTINUOUS_REQUEST
            if key[1] == _CONTINUOUS[1]
            else _STATUS_REQUEST
        )
        await self._hass.async_add_executor_job(
            self._mqtt.publish, topic, bytes.fromhex(follow_up), 1
        )

    async def async_stop(self) -> None:
        """Verbindung beenden."""
        for future in [*self._waiting.values(), *self._queries.values()]:
            if not future.done():
                future.cancel()
        self._waiting.clear()
        self._queries.clear()
        if self._mqtt is not None:
            client, self._mqtt = self._mqtt, None
            self.connected = False
            await self._hass.async_add_executor_job(_stop, client)


class _Rc:
    """Antwortcode von paho 1.x wie bei paho 2.x darstellen."""

    def __init__(self, rc: int) -> None:
        self.value = rc
        self.is_failure = rc != 0

    def __str__(self) -> str:
        return str(self.value)


def _stop(client: Any) -> None:
    client.disconnect()
    client.loop_stop()


# Version 0.5.0

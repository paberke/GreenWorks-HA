"""Maehplan schreiben, genau wie die Greenworks-App (Seite Zeitplan bearbeiten).

Die App schickt immer die ganze Woche (Montag bis Sonntag), je Tag zwei
Zeitfenster. Darum wird vor dem Speichern der aktuelle Plan frisch vom
Maeher gelesen und nur die gewaehlten Tage werden ersetzt. Alle anderen
Tage gehen unveraendert zurueck.

Je Zeitfenster: Stunde, Minute, Dauer in Minuten (2 Byte, niedriges Byte
zuerst) und Modus (1 = an, 0 = aus).
"""

from __future__ import annotations

from typing import Any

from .control import le16

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
SLOTS = (1, 2)
PARTS = ("start_time_hour", "start_time_minute", "length_minutes", "timer_mode")

# Wie in der App: 7 Tage x 2 Fenster x 5 Byte = 70 Byte
SAVE_HEAD = "0007004f00326000A049400146"
SAVE_KEY = "400146"
READ_REQUEST = "0007000900306000A003420100"
READ_KEY = "420100"

MINUTES_PER_DAY = 1440

Window = tuple[int, int]  # (Beginn, Ende) in Minuten ab Mitternacht


class ScheduleError(ValueError):
    """Ungueltiger Plan; `key` ist der Uebersetzungsschluessel."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _key(day: str, slot: int, part: str) -> str:
    return f"{day}_timer_{slot}_{part}"


def fields_from_reply(response: Any) -> dict[str, int]:
    """Alle 56 Werte aus der Antwort des Maehers holen, sonst Fehler.

    Fehlt auch nur ein Wert oder ist er ausserhalb des Bereichs, wird nichts
    gespeichert: lieber kein neuer Plan als ein halb geratener.
    """
    if not isinstance(response, dict):
        raise ScheduleError("schedule_read_failed")
    fields: dict[str, int] = {}
    for day in WEEKDAYS:
        for slot in SLOTS:
            for part in PARTS:
                key = _key(day, slot, part)
                value = response.get(key)
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ScheduleError("schedule_read_failed")
                fields[key] = value
            hour = fields[_key(day, slot, "start_time_hour")]
            minute = fields[_key(day, slot, "start_time_minute")]
            length = fields[_key(day, slot, "length_minutes")]
            mode = fields[_key(day, slot, "timer_mode")]
            if not (
                0 <= hour <= 0xFF
                and 0 <= minute <= 0xFF
                and 0 <= length <= 0xFFFF
                and 0 <= mode <= 0xFF
            ):
                raise ScheduleError("schedule_read_failed")
    return fields


def check_windows(windows: list[Window]) -> list[Window]:
    """Pruefen wie die App: Ende nach Beginn, am selben Tag, keine Ueberschneidung."""
    if len(windows) > len(SLOTS):
        raise ScheduleError("schedule_invalid")
    for begin, end in windows:
        if not 0 <= begin < end < MINUTES_PER_DAY:
            raise ScheduleError("schedule_end_before_start")
    if len(windows) == 2:
        (b1, e1), (b2, e2) = windows
        if b1 < e2 and b2 < e1:
            raise ScheduleError("schedule_overlap")
    return windows


def apply_days(
    fields: dict[str, int], days: list[str], windows: list[Window]
) -> dict[str, int]:
    """Neuer Plan: die gewaehlten Tage ersetzen, alle anderen bleiben gleich."""
    check_windows(windows)
    new = dict(fields)
    for day in days:
        if day not in WEEKDAYS:
            raise ScheduleError("schedule_invalid")
        for idx, slot in enumerate(SLOTS):
            if idx < len(windows):
                begin, end = windows[idx]
                values = (begin // 60, begin % 60, end - begin, 1)
            else:
                values = (0, 0, 0, 0)  # wie die App: Fenster aus
            for part, value in zip(PARTS, values, strict=True):
                new[_key(day, slot, part)] = value
    return new


def save_payload(fields: dict[str, int]) -> str:
    """Befehl "Zeitplan speichern" wie ScheduleEditActivity.save der App."""
    body = ""
    for day in WEEKDAYS:
        for slot in SLOTS:
            body += f"{fields[_key(day, slot, 'start_time_hour')]:02x}"
            body += f"{fields[_key(day, slot, 'start_time_minute')]:02x}"
            body += le16(fields[_key(day, slot, "length_minutes")])
            body += f"{fields[_key(day, slot, 'timer_mode')]:02x}"
    return SAVE_HEAD + body


def active_windows(fields: dict[str, int]) -> dict[str, list[tuple[int, int, int]]]:
    """Nur die eingeschalteten Fenster (zum Vergleichen nach dem Speichern)."""
    result: dict[str, list[tuple[int, int, int]]] = {}
    for day in WEEKDAYS:
        result[day] = sorted(
            (
                fields[_key(day, slot, "start_time_hour")],
                fields[_key(day, slot, "start_time_minute")],
                fields[_key(day, slot, "length_minutes")],
            )
            for slot in SLOTS
            if fields[_key(day, slot, "timer_mode")]
            and fields[_key(day, slot, "length_minutes")]
        )
    return result


# Version 0.5.0

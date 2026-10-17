"""0.2.3: Naechster Start / Maehende je nach Zustand (Werte von heute, 13.10.)."""

import json

import pytest
from custom_components.greenworks.api import build_mower
from custom_components.greenworks.sensor import _mowing_end, _next_start

DEV = {"id": 1, "product_id": "p", "name": "M"}
# echte Zeitpunkte vom 13.10.2026 (UTC)
WINDOW_END = 1791808200      # 12:30 Uhr
RESUME_EST = 1791806111      # 11:55 Uhr (Schaetzung beim Laden)
TOMORROW = 1791874800 + 86400  # morgen 09:00 Uhr


def mower(state, next_start):
    dp = {"32": json.dumps({"request": {
        "mower_main_state": state, "next_start": next_start,
        "battery_status": 50, "request_time": "2026-10-13T10:00:00Z"}})}
    return build_mower(DEV, {}, dp)


@pytest.mark.parametrize("state,ns,expect_start,expect_end", [
    (4, WINDOW_END, False, True),    # maeht -> Maehende
    (5, WINDOW_END, False, True),    # verlaesst Station -> Maehende
    (6, 4294967295, False, False),   # faehrt zur Station -> beides leer
    (7, RESUME_EST, True, False),    # laedt -> naechster Start (Schaetzung)
    (2, TOMORROW, True, False),      # geparkt -> naechster Start morgen
])
def test_split(state, ns, expect_start, expect_end):
    m = mower(state, ns)
    assert (_next_start(m) is not None) == expect_start
    assert (_mowing_end(m) is not None) == expect_end

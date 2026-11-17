"""0.6.3: Das Debug-Log enthaelt nie die PIN, nur die Kennung des Befehls."""

import logging
from types import SimpleNamespace

from .test_greenworks import DID
from .test_v030 import _setup, eid
from .test_v050 import CHARGING, CONTROL, _connect


async def test_debug_log_hides_pin(hass, aioclient_mock, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.greenworks")
    entry = await _setup(hass, aioclient_mock, options={**CONTROL, "pin": "8357"},
                         datapoints=CHARGING)
    control = _connect(entry)
    sent = []

    def publish(topic, payload, qos):
        sent.append(payload.hex())
        if len(sent) == 1:
            raw = b'{"request":{"request_payload":"e400040000a520"},"response":{"return_code":0}}'
            hass.loop.call_soon_threadsafe(control._on_message, None, None,
                                           SimpleNamespace(topic=f"$6/{DID}", payload=raw))
    control._mqtt.publish.side_effect = publish
    await hass.services.async_call("lawn_mower", "start_mowing",
                                   {"entity_id": eid(hass, "lawn_mower", "mower")}, blocking=True)
    # Gesendet wird die PIN (8357 = a520), im Log steht nur die Kennung
    assert sent[0].endswith("e400040000a520")
    assert "Sende Befehl" in caplog.text
    assert "e400040000" in caplog.text
    assert "a520" not in caplog.text
    assert "8357" not in caplog.text


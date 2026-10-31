"""Testzweig: der MQTT-Zuhoerer abonniert nur und sendet nie etwas."""

import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.greenworks.mqtt_listen import (
    MQTT_HOST,
    MQTT_PORT,
    GreenworksMqttListener,
)

pytestmark = pytest.mark.real_listener


def _api(authorize="abc", user_id=4711):
    return SimpleNamespace(authorize=authorize, user_id=user_id, login_keys=["access_token"])


async def test_ohne_authorize_keine_verbindung(hass, caplog):
    listener = GreenworksMqttListener(hass, _api(authorize=None), [1])
    with patch("paho.mqtt.client.Client") as client_cls:
        await listener.async_start()
    client_cls.assert_not_called()
    assert "kein 'authorize'" in caplog.text


async def test_verbindet_abonniert_und_sendet_nie(hass):
    listener = GreenworksMqttListener(hass, _api(), [123, 456])
    fake = MagicMock()
    with patch("paho.mqtt.client.Client", return_value=fake):
        await listener.async_start()

    user, password = fake.username_pw_set.call_args.args
    assert user == "4711"
    assert password == hashlib.md5(b"4711abc").hexdigest()
    fake.connect_async.assert_called_once_with(MQTT_HOST, MQTT_PORT, keepalive=60)
    fake.loop_start.assert_called_once()

    listener._on_connect(fake, None, None, SimpleNamespace(is_failure=False), None)
    topics = sorted(c.args[0] for c in fake.subscribe.call_args_list)
    assert topics == ["$6/123", "$6/456", "$8/123", "$8/456", "$y/123", "$y/456"]

    listener._on_message(fake, None, SimpleNamespace(topic="$6/123", payload=b'{"a":1}'))
    fake.publish.assert_not_called()

    await listener.async_stop()
    fake.disconnect.assert_called_once()
    fake.loop_stop.assert_called_once()


async def test_fehlgeschlagene_anmeldung_abonniert_nichts(hass):
    listener = GreenworksMqttListener(hass, _api(), [1])
    fake = MagicMock()
    listener._on_connect(fake, None, None, SimpleNamespace(is_failure=True), None)
    fake.subscribe.assert_not_called()

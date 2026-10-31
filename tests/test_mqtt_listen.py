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


async def test_alte_paho_version(hass):
    """HA 2025.2 bringt paho 1.x ohne CallbackAPIVersion mit."""
    listener = GreenworksMqttListener(hass, _api(), [7])
    fake = MagicMock()
    fake_module = SimpleNamespace(Client=MagicMock(return_value=fake))
    with patch.dict("sys.modules", {"paho.mqtt.client": fake_module}), patch(
        "paho.mqtt.client", fake_module, create=True
    ):
        await listener.async_start()
    fake_module.Client.assert_called_once()
    assert "callback_api_version" not in fake_module.Client.call_args.kwargs
    fake.on_connect(fake, None, {}, 0)
    fake.subscribe.assert_any_call("$6/7")
    fake.on_disconnect(fake, None, 1)
    fake.publish.assert_not_called()

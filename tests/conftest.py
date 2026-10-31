from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def no_real_mqtt(request):
    """In Tests nie echt mit dem Greenworks-Broker verbinden.

    Wird vor hass aufgebaut und erst danach abgebaut, damit auch ein
    Neuladen beim Herunterfahren nicht echt verbindet.
    """
    if "real_listener" in request.keywords:
        yield
        return
    with patch("custom_components.greenworks.mqtt_listen.GreenworksMqttListener._start"):
        yield


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(no_real_mqtt, enable_custom_integrations):
    yield

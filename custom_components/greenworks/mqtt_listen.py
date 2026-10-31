"""Testzweig: dem MQTT-Kanal der Greenworks-Cloud nur zuhoeren.

Verbindet sich mit dem Broker, den auch die App nutzt, und schreibt alle
Nachrichten ins Home-Assistant-Log. Es wird NICHTS gesendet: kein publish,
keine Befehle an den Maeher. Nur zum Herausfinden, wie die Antworten aussehen.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.util.ssl import client_context

if TYPE_CHECKING:
    from .api import GreenworksClient

_LOGGER = logging.getLogger(__name__)

MQTT_HOST = "mqtt.globetools.systems"
MQTT_PORT = 1884
# Themen, die die App fuer ein Geraet abonniert ($7 ist nur zum Senden)
TOPIC_PREFIXES = ("$6", "$8", "$y")
MAX_LOGGED = 300  # danach nur noch zaehlen, damit das Log nicht volllaeuft
LOG_PREFIX = "Greenworks MQTT (nur zuhoeren)"


class GreenworksMqttListener:
    """Hoert dem MQTT-Kanal zu, sendet nie etwas."""

    def __init__(
        self, hass: HomeAssistant, client: GreenworksClient, device_ids: list[int]
    ) -> None:
        self._hass = hass
        self._api = client
        self._device_ids = device_ids
        self._mqtt = None
        self._count = 0

    def _credentials(self) -> tuple[str, str]:
        user = str(self._api.user_id)
        password = hashlib.md5(f"{user}{self._api.authorize}".encode()).hexdigest()
        return user, password

    async def async_start(self) -> None:
        """Verbindung im Hintergrund aufbauen."""
        if not self._api.authorize or not self._api.user_id:
            _LOGGER.warning(
                "%s: Login liefert kein 'authorize', Zuhoeren nicht moeglich. "
                "Felder in der Login-Antwort: %s",
                LOG_PREFIX,
                self._api.login_keys,
            )
            return
        context = await self._hass.async_add_executor_job(client_context)
        await self._hass.async_add_executor_job(self._start, context)

    def _start(self, context) -> None:
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
        client.reconnect_delay_set(min_delay=30, max_delay=600)
        self._mqtt = client
        _LOGGER.warning(
            "%s: verbinde mit %s:%s fuer %s Geraet(e)",
            LOG_PREFIX,
            MQTT_HOST,
            MQTT_PORT,
            len(self._device_ids),
        )
        client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        _LOGGER.warning("%s: verbunden, Antwort %s", LOG_PREFIX, reason_code)
        if reason_code.is_failure:
            return
        for device_id in self._device_ids:
            for prefix in TOPIC_PREFIXES:
                client.subscribe(f"{prefix}/{device_id}")
        _LOGGER.warning("%s: Themen abonniert: %s", LOG_PREFIX, ", ".join(TOPIC_PREFIXES))

    def _on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        _LOGGER.warning("%s: getrennt, Grund %s", LOG_PREFIX, reason_code)
        # Das Passwort haengt am Login; nach einem neuen Login das aktuelle nehmen
        if self._api.authorize:
            client.username_pw_set(*self._credentials())

    def _on_message(self, client, userdata, message) -> None:
        self._count += 1
        if self._count > MAX_LOGGED:
            if self._count % 100 == 0:
                _LOGGER.warning("%s: %s Nachrichten bisher", LOG_PREFIX, self._count)
            return
        prefix = message.topic.split("/", 1)[0]
        payload = bytes(message.payload)
        text = payload.decode("utf-8", "replace") if prefix == "$6" else ""
        _LOGGER.warning(
            "%s: Nr. %s, Thema %s, %s Bytes, hex=%s %s",
            LOG_PREFIX,
            self._count,
            prefix,
            len(payload),
            payload[:64].hex(),
            text[:2000],
        )

    async def async_stop(self) -> None:
        """Verbindung beenden."""
        if self._mqtt is not None:
            client, self._mqtt = self._mqtt, None
            await self._hass.async_add_executor_job(_stop, client)


class _Rc:
    """Antwortcode von paho 1.x wie bei paho 2.x darstellen."""

    def __init__(self, rc: int) -> None:
        self.value = rc
        self.is_failure = rc != 0

    def __str__(self) -> str:
        return str(self.value)


def _stop(client) -> None:
    client.disconnect()
    client.loop_stop()


# Version 0.4.1 (Testzweig, nur zuhoeren)

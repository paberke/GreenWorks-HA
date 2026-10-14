"""Einrichtung der Greenworks-Integration ueber die Oberflaeche."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    GreenworksAuthError,
    GreenworksClient,
    GreenworksError,
    GreenworksLoginRejected,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
)


class GreenworksConfigFlow(ConfigFlow, domain=DOMAIN):
    """Konfigurationsablauf fuer Greenworks."""

    VERSION = 1

    async def _async_validate(
        self, email: str, password: str
    ) -> tuple[dict[str, str], int | None, int]:
        """Zugangsdaten pruefen. Gibt Fehler, user_id und Anzahl Maeher zurueck."""
        errors: dict[str, str] = {}
        client = GreenworksClient(async_get_clientsession(self.hass), email, password)
        try:
            await client.async_login()
            devices = await client.async_get_devices()
        except GreenworksAuthError:
            errors["base"] = "invalid_auth"
            return errors, None, 0
        except GreenworksLoginRejected:
            errors["base"] = "login_rejected"
            return errors, None, 0
        except GreenworksError:
            errors["base"] = "cannot_connect"
            return errors, None, 0
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unerwarteter Fehler bei der Einrichtung")
            errors["base"] = "unknown"
            return errors, None, 0
        if not devices:
            errors["base"] = "no_devices"
        return errors, client.user_id, len(devices)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            errors, user_id, _ = await self._async_validate(
                email, user_input[CONF_PASSWORD]
            )
            if not errors:
                await self.async_set_unique_id(str(user_id))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Greenworks ({email})",
                    data={CONF_EMAIL: email, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            errors, _, _ = await self._async_validate(
                entry.data[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )


# Version 0.2.9

"""Einrichtung der Greenworks-Integration ueber die Oberflaeche."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import (
    GreenworksAuthError,
    GreenworksClient,
    GreenworksError,
    GreenworksLoginRejected,
)
from .const import (
    BLADE_LIMIT_RANGE,
    CONF_BLADE_LIMIT,
    CONF_OUTAGE_GRACE,
    DEFAULT_BLADE_LIMIT,
    DEFAULT_OUTAGE_GRACE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OUTAGE_GRACE_RANGE,
    SCAN_INTERVAL_RANGE,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
)


class GreenworksConfigFlow(ConfigFlow, domain=DOMAIN):
    """Konfigurationsablauf fuer Greenworks."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GreenworksOptionsFlow()

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


def _number(minimum: int, maximum: int, unit: str) -> NumberSelector:
    """Zahlenfeld zum Eintippen (statt Schieberegler), mit Einheit."""
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


class GreenworksOptionsFlow(OptionsFlow):
    """Einstellungen der Integration (Knopf "Konfigurieren")."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={key: int(value) for key, value in user_input.items()}
            )
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): _number(*SCAN_INTERVAL_RANGE, "s"),
                vol.Required(
                    CONF_OUTAGE_GRACE,
                    default=options.get(CONF_OUTAGE_GRACE, DEFAULT_OUTAGE_GRACE),
                ): _number(*OUTAGE_GRACE_RANGE, "min"),
                vol.Required(
                    CONF_BLADE_LIMIT,
                    default=options.get(CONF_BLADE_LIMIT, DEFAULT_BLADE_LIMIT),
                ): _number(*BLADE_LIMIT_RANGE, "h"),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


# Version 0.2.14

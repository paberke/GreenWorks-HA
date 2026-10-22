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
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
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
    CONF_GROUPS,
    CONF_OFFLINE_HOURS,
    CONF_OUTAGE_GRACE,
    DEFAULT_BLADE_LIMIT,
    DEFAULT_GROUPS_EXISTING,
    DEFAULT_GROUPS_NEW,
    DEFAULT_OFFLINE_HOURS,
    DEFAULT_OUTAGE_GRACE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OFFLINE_HOURS_RANGE,
    OPTIONAL_GROUPS,
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
    # 1.2: Gruppen in den Optionen (ab 0.3.0)
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._title = ""

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
                self._title = f"Greenworks ({email})"
                self._data = {CONF_EMAIL: email, CONF_PASSWORD: user_input[CONF_PASSWORD]}
                return await self.async_step_groups()
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_groups(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 2: Was soll angezeigt werden? (Standard ist immer dabei)"""
        if user_input is not None:
            return self.async_create_entry(
                title=self._title,
                data=self._data,
                options={CONF_GROUPS: list(user_input.get(CONF_GROUPS, []))},
            )
        schema = vol.Schema(
            {vol.Optional(CONF_GROUPS, default=list(DEFAULT_GROUPS_NEW)): _groups_selector()}
        )
        return self.async_show_form(step_id="groups", data_schema=schema)

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


def _groups_selector() -> SelectSelector:
    """Auswahl der Gruppen als Liste mit Haken."""
    return SelectSelector(
        SelectSelectorConfig(
            options=list(OPTIONAL_GROUPS),
            multiple=True,
            mode=SelectSelectorMode.LIST,
            translation_key="groups",
        )
    )


class GreenworksOptionsFlow(OptionsFlow):
    """Einstellungen der Integration (Knopf "Konfigurieren")."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            data: dict[str, Any] = {
                key: int(value) for key, value in user_input.items() if key != CONF_GROUPS
            }
            data[CONF_GROUPS] = list(user_input.get(CONF_GROUPS, []))
            return self.async_create_entry(data=data)
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_GROUPS,
                    default=list(options.get(CONF_GROUPS, DEFAULT_GROUPS_EXISTING)),
                ): _groups_selector(),
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
                vol.Required(
                    CONF_OFFLINE_HOURS,
                    default=options.get(CONF_OFFLINE_HOURS, DEFAULT_OFFLINE_HOURS),
                ): _number(*OFFLINE_HOURS_RANGE, "h"),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


# Version 0.3.1

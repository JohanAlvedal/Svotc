"""Config flow for SVOTC."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_INDOOR_TEMPERATURE,
    CONF_OUTDOOR_TEMPERATURE,
    CONF_PRICE_ENTITY,
    CONF_WEATHER_ENTITY,
    DOMAIN,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the config schema with optional entity selectors."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_INDOOR_TEMPERATURE,
                default=defaults.get(CONF_INDOOR_TEMPERATURE),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(
                CONF_OUTDOOR_TEMPERATURE,
                default=defaults.get(CONF_OUTDOOR_TEMPERATURE),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(
                CONF_PRICE_ENTITY,
                default=defaults.get(CONF_PRICE_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Optional(
                CONF_WEATHER_ENTITY,
                default=defaults.get(CONF_WEATHER_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["weather"])
            ),
        }
    )


def _clean_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Remove empty values to allow auto-detection."""
    return {key: value for key, value in user_input.items() if value not in ("", None)}


class SVOTCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SVOTC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            data = _clean_input(user_input)
            return self.async_create_entry(title="SVOTC", data=data)

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return SVOTCOptionsFlow(config_entry)


class SVOTCOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SVOTC."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            options = _clean_input(user_input)
            return self.async_create_entry(title="", data=options)

        defaults = {
            **self._config_entry.data,
            **self._config_entry.options,
        }
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))

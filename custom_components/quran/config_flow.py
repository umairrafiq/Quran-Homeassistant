"""Config flow for Quran integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuranAPI, QuranApiError
from .const import (
    DOMAIN,
    CONF_RECITER,
    CONF_TRANSLATION,
    CONF_DAILY_AYAH,
    DEFAULT_RECITER,
    DEFAULT_TRANSLATION,
    RECITERS,
    TRANSLATIONS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input."""
    session = async_get_clientsession(hass)
    api = QuranAPI(session)

    # Test API connection
    try:
        await api.get_ayah(1, data.get(CONF_RECITER, DEFAULT_RECITER))
    except QuranApiError as err:
        raise ValueError(f"Cannot connect to API: {err}") from err

    return {"title": "Quran"}


class QuranConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Quran."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id("quran_integration")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_RECITER, default=DEFAULT_RECITER): vol.In(RECITERS),
                vol.Required(CONF_TRANSLATION, default=DEFAULT_TRANSLATION): vol.In(TRANSLATIONS),
                vol.Optional(CONF_DAILY_AYAH, default=True): bool,
            }),
            errors=errors,
        )


class QuranOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_RECITER,
                    default=self.config_entry.data.get(CONF_RECITER, DEFAULT_RECITER),
                ): vol.In(RECITERS),
                vol.Required(
                    CONF_TRANSLATION,
                    default=self.config_entry.data.get(CONF_TRANSLATION, DEFAULT_TRANSLATION),
                ): vol.In(TRANSLATIONS),
                vol.Optional(
                    CONF_DAILY_AYAH,
                    default=self.config_entry.data.get(CONF_DAILY_AYAH, True),
                ): bool,
            }),
        )

"""The Quran integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuranAPI
from .const import (
    DOMAIN,
    CONF_RECITER,
    CONF_TRANSLATION,
    DEFAULT_RECITER,
    DEFAULT_TRANSLATION,
    SURAH_NAMES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Service schemas
SERVICE_PLAY_SURAH = "play_surah"
SERVICE_PLAY_AYAH = "play_ayah"
SERVICE_PLAY_AYAT_UL_KURSI = "play_ayat_ul_kursi"

ATTR_SURAH = "surah"
ATTR_AYAH = "ayah"
ATTR_RECITER = "reciter"
ATTR_MEDIA_PLAYER = "media_player"

SERVICE_PLAY_SURAH_SCHEMA = vol.Schema({
    vol.Required(ATTR_SURAH): vol.All(vol.Coerce(int), vol.Range(min=1, max=114)),
    vol.Required(ATTR_MEDIA_PLAYER): cv.entity_id,
    vol.Optional(ATTR_RECITER): cv.string,
})

SERVICE_PLAY_AYAH_SCHEMA = vol.Schema({
    vol.Required(ATTR_AYAH): vol.All(vol.Coerce(int), vol.Range(min=1, max=6236)),
    vol.Required(ATTR_MEDIA_PLAYER): cv.entity_id,
    vol.Optional(ATTR_RECITER): cv.string,
})

SERVICE_PLAY_AYAT_UL_KURSI_SCHEMA = vol.Schema({
    vol.Required(ATTR_MEDIA_PLAYER): cv.entity_id,
    vol.Optional(ATTR_RECITER): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quran from a config entry."""
    session = async_get_clientsession(hass)
    api = QuranAPI(session)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "config": entry.data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_play_surah(call: ServiceCall) -> None:
        """Handle the play_surah service."""
        surah = call.data[ATTR_SURAH]
        media_player = call.data[ATTR_MEDIA_PLAYER]
        reciter = call.data.get(ATTR_RECITER, entry.data.get(CONF_RECITER, DEFAULT_RECITER))

        try:
            audio_urls = await api.get_surah_audio_urls(surah, reciter)
            if audio_urls:
                # Play first ayah, the rest will need playlist support
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": media_player,
                        "media_content_type": "music",
                        "media_content_id": audio_urls[0],
                    },
                    blocking=True,
                )
                surah_name = SURAH_NAMES.get(surah, (f"Surah {surah}", ""))[0]
                _LOGGER.info(f"Playing {surah_name} on {media_player}")
        except Exception as err:
            _LOGGER.error(f"Error playing surah: {err}")

    async def handle_play_ayah(call: ServiceCall) -> None:
        """Handle the play_ayah service."""
        ayah = call.data[ATTR_AYAH]
        media_player = call.data[ATTR_MEDIA_PLAYER]
        reciter = call.data.get(ATTR_RECITER, entry.data.get(CONF_RECITER, DEFAULT_RECITER))

        try:
            audio_url = await api.get_audio_url(ayah, reciter)
            if audio_url:
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": media_player,
                        "media_content_type": "music",
                        "media_content_id": audio_url,
                    },
                    blocking=True,
                )
                _LOGGER.info(f"Playing ayah {ayah} on {media_player}")
        except Exception as err:
            _LOGGER.error(f"Error playing ayah: {err}")

    async def handle_play_ayat_ul_kursi(call: ServiceCall) -> None:
        """Handle the play_ayat_ul_kursi service."""
        media_player = call.data[ATTR_MEDIA_PLAYER]
        reciter = call.data.get(ATTR_RECITER, entry.data.get(CONF_RECITER, DEFAULT_RECITER))

        try:
            audio_url = await api.get_audio_url(262, reciter)  # Ayat ul Kursi is ayah 262
            if audio_url:
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": media_player,
                        "media_content_type": "music",
                        "media_content_id": audio_url,
                    },
                    blocking=True,
                )
                _LOGGER.info(f"Playing Ayat ul Kursi on {media_player}")
        except Exception as err:
            _LOGGER.error(f"Error playing Ayat ul Kursi: {err}")

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_SURAH, handle_play_surah, schema=SERVICE_PLAY_SURAH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_AYAH, handle_play_ayah, schema=SERVICE_PLAY_AYAH_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_AYAT_UL_KURSI, handle_play_ayat_ul_kursi, schema=SERVICE_PLAY_AYAT_UL_KURSI_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # Unregister services if no more entries
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_PLAY_SURAH)
        hass.services.async_remove(DOMAIN, SERVICE_PLAY_AYAH)
        hass.services.async_remove(DOMAIN, SERVICE_PLAY_AYAT_UL_KURSI)

    return unload_ok

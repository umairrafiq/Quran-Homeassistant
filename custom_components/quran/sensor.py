"""Sensor platform for Quran integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import hashlib

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import QuranAPI
from .const import (
    DOMAIN,
    CONF_RECITER,
    CONF_TRANSLATION,
    CONF_DAILY_AYAH,
    DEFAULT_RECITER,
    DEFAULT_TRANSLATION,
    SURAH_NAMES,
    AYAH_COUNT,
)

_LOGGER = logging.getLogger(__name__)


def get_daily_ayah_number() -> int:
    """Get a deterministic ayah number based on the date."""
    today = datetime.now().strftime("%Y-%m-%d")
    # Use hash to get a consistent ayah for each day
    hash_val = int(hashlib.md5(today.encode()).hexdigest(), 16)
    return (hash_val % AYAH_COUNT) + 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Quran sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    api: QuranAPI = data["api"]
    config = data["config"]

    if config.get(CONF_DAILY_AYAH, True):
        reciter = config.get(CONF_RECITER, DEFAULT_RECITER)
        translation = config.get(CONF_TRANSLATION, DEFAULT_TRANSLATION)

        coordinator = QuranCoordinator(hass, api, reciter, translation)
        await coordinator.async_config_entry_first_refresh()

        async_add_entities([
            QuranDailyAyahSensor(coordinator, entry),
            QuranDailyAyahArabicSensor(coordinator, entry),
            QuranDailyAyahAudioSensor(coordinator, entry),
        ])


class QuranCoordinator(DataUpdateCoordinator):
    """Coordinator for Quran data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: QuranAPI,
        reciter: str,
        translation: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),  # Check hourly, changes daily
        )
        self.api = api
        self.reciter = reciter
        self.translation = translation
        self._last_ayah_number = None

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        ayah_number = get_daily_ayah_number()

        # Only fetch if ayah changed (new day)
        if ayah_number == self._last_ayah_number and self.data:
            return self.data

        self._last_ayah_number = ayah_number

        try:
            # Fetch ayah in multiple editions
            editions = await self.api.get_ayah_editions(
                ayah_number,
                ["quran-uthmani", self.translation, self.reciter]
            )

            arabic = next((e for e in editions if e.get("edition", {}).get("identifier") == "quran-uthmani"), {})
            translation = next((e for e in editions if e.get("edition", {}).get("identifier") == self.translation), {})
            audio = next((e for e in editions if e.get("edition", {}).get("identifier") == self.reciter), {})

            surah_info = arabic.get("surah", {})
            surah_number = surah_info.get("number", 1)
            surah_names = SURAH_NAMES.get(surah_number, ("Unknown", "Unknown"))

            return {
                "ayah_number": ayah_number,
                "ayah_in_surah": arabic.get("numberInSurah", 0),
                "surah_number": surah_number,
                "surah_name": surah_names[0],
                "surah_translation": surah_names[1],
                "arabic_text": arabic.get("text", ""),
                "translation_text": translation.get("text", ""),
                "translation_edition": self.translation,
                "audio_url": audio.get("audio", ""),
                "reciter": self.reciter,
            }
        except Exception as err:
            _LOGGER.error(f"Error fetching daily ayah: {err}")
            raise


class QuranDailyAyahSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily Quran ayah (translation)."""

    _attr_has_entity_name = True
    _attr_name = "Daily Ayah"
    _attr_icon = "mdi:book-open-page-variant"

    def __init__(self, coordinator: QuranCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_ayah"
        self._entry = entry

    @property
    def native_value(self) -> str | None:
        """Return the translation text."""
        if self.coordinator.data:
            return self.coordinator.data.get("translation_text", "")[:255]  # Truncate for state
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        
        data = self.coordinator.data
        return {
            "ayah_number": data.get("ayah_number"),
            "surah_number": data.get("surah_number"),
            "surah_name": data.get("surah_name"),
            "surah_translation": data.get("surah_translation"),
            "ayah_in_surah": data.get("ayah_in_surah"),
            "reference": f"{data.get('surah_number')}:{data.get('ayah_in_surah')}",
            "full_text": data.get("translation_text"),
            "translation_edition": data.get("translation_edition"),
            "audio_url": data.get("audio_url"),
        }


class QuranDailyAyahArabicSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily Quran ayah (Arabic)."""

    _attr_has_entity_name = True
    _attr_name = "Daily Ayah Arabic"
    _attr_icon = "mdi:abjad-arabic"

    def __init__(self, coordinator: QuranCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_ayah_arabic"
        self._entry = entry

    @property
    def native_value(self) -> str | None:
        """Return the Arabic text."""
        if self.coordinator.data:
            return self.coordinator.data.get("arabic_text", "")[:255]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        
        data = self.coordinator.data
        return {
            "ayah_number": data.get("ayah_number"),
            "reference": f"{data.get('surah_number')}:{data.get('ayah_in_surah')}",
            "full_text": data.get("arabic_text"),
        }


class QuranDailyAyahAudioSensor(CoordinatorEntity, SensorEntity):
    """Sensor for daily Quran ayah audio URL."""

    _attr_has_entity_name = True
    _attr_name = "Daily Ayah Audio"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator: QuranCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_ayah_audio"
        self._entry = entry

    @property
    def native_value(self) -> str | None:
        """Return the audio URL."""
        if self.coordinator.data:
            return self.coordinator.data.get("audio_url", "")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        
        data = self.coordinator.data
        return {
            "ayah_number": data.get("ayah_number"),
            "reference": f"{data.get('surah_number')}:{data.get('ayah_in_surah')}",
            "reciter": data.get("reciter"),
        }

"""API client for AlQuran.cloud."""
import aiohttp
import logging
from typing import Any

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class QuranApiError(Exception):
    """Exception for Quran API errors."""


class QuranAPI:
    """Client for the AlQuran.cloud API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session

    async def _request(self, endpoint: str) -> dict[str, Any]:
        """Make a request to the API."""
        url = f"{API_BASE_URL}/{endpoint}"
        try:
            async with self._session.get(url) as response:
                if response.status != 200:
                    raise QuranApiError(f"API returned status {response.status}")
                data = await response.json()
                if data.get("code") != 200:
                    raise QuranApiError(data.get("status", "Unknown error"))
                return data.get("data", {})
        except aiohttp.ClientError as err:
            raise QuranApiError(f"Connection error: {err}") from err

    async def get_surah(self, surah_number: int, edition: str = "quran-uthmani") -> dict:
        """Get a complete surah."""
        return await self._request(f"surah/{surah_number}/{edition}")

    async def get_surah_info(self, surah_number: int) -> dict:
        """Get surah metadata only."""
        return await self._request(f"surah/{surah_number}")

    async def get_all_surahs(self) -> list[dict]:
        """Get list of all surahs."""
        return await self._request("surah")

    async def get_ayah(self, ayah_number: int, edition: str = "quran-uthmani") -> dict:
        """Get a specific ayah by its absolute number (1-6236)."""
        return await self._request(f"ayah/{ayah_number}/{edition}")

    async def get_ayah_editions(self, ayah_number: int, editions: list[str]) -> list[dict]:
        """Get an ayah in multiple editions."""
        editions_str = ",".join(editions)
        return await self._request(f"ayah/{ayah_number}/editions/{editions_str}")

    async def get_ayah_by_reference(self, surah: int, ayah: int, edition: str = "quran-uthmani") -> dict:
        """Get a specific ayah by surah:ayah reference."""
        return await self._request(f"ayah/{surah}:{ayah}/{edition}")

    async def get_juz(self, juz_number: int, edition: str = "quran-uthmani") -> dict:
        """Get a complete juz (para)."""
        return await self._request(f"juz/{juz_number}/{edition}")

    async def search(self, query: str, edition: str = "en.asad", surah: str = "all") -> dict:
        """Search the Quran."""
        return await self._request(f"search/{query}/{surah}/{edition}")

    async def get_editions(self, format_type: str | None = None, language: str | None = None) -> list[dict]:
        """Get available editions."""
        if format_type:
            return await self._request(f"edition/format/{format_type}")
        if language:
            return await self._request(f"edition/language/{language}")
        return await self._request("edition")

    async def get_audio_url(self, ayah_number: int, reciter: str = "ar.alafasy") -> str:
        """Get the audio URL for a specific ayah."""
        data = await self.get_ayah(ayah_number, reciter)
        return data.get("audio", "")

    async def get_surah_audio_urls(self, surah_number: int, reciter: str = "ar.alafasy") -> list[str]:
        """Get all audio URLs for a surah."""
        data = await self.get_surah(surah_number, reciter)
        return [ayah.get("audio", "") for ayah in data.get("ayahs", []) if ayah.get("audio")]

    async def get_random_ayah(self, edition: str = "quran-uthmani") -> dict:
        """Get a random ayah."""
        import random
        ayah_number = random.randint(1, 6236)
        return await self.get_ayah(ayah_number, edition)

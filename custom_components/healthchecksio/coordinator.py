"""Add coordinator for Healthchecks.io integration."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession, ClientTimeout
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

LOGGER = getLogger(__name__)


class HealthchecksioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Healthchecks.io data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        api_key: str,
        session: ClientSession,
        self_hosted: bool = False,
        check_id: str | None = None,
        site_root: str | None = None,
        ping_endpoint: str | None = None,
    ):
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=MIN_TIME_BETWEEN_UPDATES,
        )
        self._api_key = api_key
        self._site_root = site_root
        self._session = session
        self._self_hosted = self_hosted
        self._check_id = check_id
        self._ping_endpoint = ping_endpoint

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        check_url = (
            f"https://hc-ping.com/{self._check_id}"
            if not self._self_hosted
            else f"{self._site_root}/{self._ping_endpoint}/{self._check_id}"
        )

        try:
            await self._session.get(
                check_url,
                timeout=ClientTimeout(total=10),
            )
        except Exception:
            LOGGER.exception("Could not ping")

        try:
            data = await self._session.get(
                f"{self._site_root}/api/v1/checks/",
                headers={"X-Api-Key": self._api_key},
                timeout=ClientTimeout(total=10),
            )
            return await data.json()
        except Exception as error:
            raise UpdateFailed(error) from error

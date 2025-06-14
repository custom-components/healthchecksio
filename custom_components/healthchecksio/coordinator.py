"""Coordinator for Healthchecks.io integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession, ClientTimeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


_LOGGER: logging.Logger = logging.getLogger(__name__)


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
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=MIN_TIME_BETWEEN_UPDATES,
        )
        self._api_key: str = api_key
        self._site_root: str | None = site_root
        self._session: ClientSession = session
        self._self_hosted: bool = self_hosted
        self._check_id: str | None = check_id
        self._ping_endpoint: str | None = ping_endpoint

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        check_url: str = (
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
            _LOGGER.exception("Could not ping")

        try:
            data = await self._session.get(
                f"{self._site_root}/api/v1/checks/",
                headers={"X-Api-Key": self._api_key},
                timeout=ClientTimeout(total=10),
            )
            return await data.json()
        except Exception as error:
            raise UpdateFailed(error) from error

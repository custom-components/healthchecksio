"""Coordinator for Healthchecks.io integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError, ClientSession, ClientTimeout

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
        ping_session: ClientSession,
        check_session: ClientSession,
        self_hosted: bool = False,
        ping_id: str | None = None,
        ping_site_root: str,
        check_site_root: str,
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
        self._ping_site_root: str | None = ping_site_root
        self._check_site_root: str | None = check_site_root
        self._ping_session: ClientSession = ping_session
        self._check_session: ClientSession = check_session
        self._self_hosted: bool = self_hosted
        self._ping_id: str | None = ping_id
        self._ping_endpoint: str | None = ping_endpoint

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        if self._ping_id:
            ping_url: str = (
                f"https://hc-ping.com/{self._ping_id}"
                if not self._self_hosted
                else f"{self._ping_site_root}/{self._ping_endpoint}/{self._ping_id}"
            )
            _LOGGER.debug("ping_url: %s", ping_url)

            try:
                await self._ping_session.get(
                    ping_url,
                    timeout=ClientTimeout(total=10),
                )
            except ClientError as e:
                _LOGGER.error(
                    "Could Not Send Ping using URL: %s. %s: %s",
                    ping_url,
                    e.__class__.__qualname__,
                    e,
                )
            _LOGGER.debug("Send Ping Ok")
        else:
            _LOGGER.debug("Ping ID not set, skipping")

        get_checks_url: str = f"{self._check_site_root}/api/v1/checks/"
        _LOGGER.debug("get_checks_url: %s", get_checks_url)
        try:
            data = await self._check_session.get(
                get_checks_url,
                headers={"X-Api-Key": self._api_key},
                timeout=ClientTimeout(total=10),
            )
            check_data = await data.json()
            _LOGGER.debug("check_data: %s", check_data)
        except ClientError as e:
            _LOGGER.error(
                "Update Checks Failed with URL: %s. %s: %s",
                get_checks_url,
                e.__class__.__qualname__,
                e,
            )
            raise UpdateFailed(e) from e
        else:
            return check_data

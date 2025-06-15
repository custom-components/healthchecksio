"""Coordinator for Healthchecks.io integration."""

from __future__ import annotations

from collections.abc import MutableMapping
from json import JSONDecodeError
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
        api_key: str,
        ping_session: ClientSession,
        check_session: ClientSession,
        site_root: str,
        ping_endpoint: str,
        ping_uuid: str | None = None,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=MIN_TIME_BETWEEN_UPDATES,
        )
        self._api_key: str = api_key
        self._site_root: str = site_root
        self._ping_endpoint: str = ping_endpoint
        self._ping_session: ClientSession = ping_session
        self._check_session: ClientSession = check_session
        self._ping_uuid: str | None = ping_uuid

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data."""
        if self._ping_uuid:
            ping_url: str = f"{self._ping_endpoint}/{self._ping_uuid}"
            _LOGGER.debug("ping_url: %s", ping_url)

            try:
                await self._ping_session.get(
                    ping_url,
                    timeout=ClientTimeout(total=10),
                )
            except (TimeoutError, ClientError) as e:
                _LOGGER.error(
                    "Could Not Send Ping using URL: %s. %s: %s",
                    ping_url,
                    e.__class__.__qualname__,
                    e,
                )
            _LOGGER.debug("Send Ping Ok")
        else:
            _LOGGER.debug("Ping UUID not set, skipping")

        get_checks_url: str = f"{self._site_root}/api/v1/checks/"
        _LOGGER.debug("get_checks_url: %s", get_checks_url)
        try:
            data = await self._check_session.get(
                get_checks_url,
                headers={"X-Api-Key": self._api_key},
                timeout=ClientTimeout(total=10),
            )
            check_data = await data.json()
            # _LOGGER.debug("check_data: %s", check_data)
        except (TimeoutError, ClientError) as e:
            _LOGGER.error(
                "Update Checks Failed with URL: %s. %s: %s",
                get_checks_url,
                e.__class__.__qualname__,
                e,
            )
            raise UpdateFailed(e) from e
        except (ValueError, JSONDecodeError) as e:
            _LOGGER.error(
                "Data JSON Decode Error. %s: %s",
                e.__class__.__qualname__,
                e,
            )
            raise UpdateFailed(e) from e
        if not isinstance(check_data, MutableMapping):
            _LOGGER.error("Update Checks Failed, unable to parse data")
            raise UpdateFailed("Update Checks Failed, unable to parse data")
        check_dict: dict[str, Any] = {}
        for check in check_data.get("checks", []):
            if check.get("uuid"):
                check_dict[check.get("uuid")] = check
        # _LOGGER.debug("check_dict: %s", check_dict)
        return check_dict

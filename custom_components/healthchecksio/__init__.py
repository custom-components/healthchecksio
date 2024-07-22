"""
Integration to integrate with healthchecks.io

For more details about this component, please refer to
https://github.com/custom-components/healthchecksio
"""

import asyncio
from datetime import timedelta
from logging import getLogger

import async_timeout
from homeassistant import config_entries, core
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import (
    DOMAIN_DATA,
    OFFICIAL_SITE_ROOT,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)
PLATFORMS = [
    Platform.BINARY_SENSOR,
]

LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Create DATA dict
    if DOMAIN_DATA not in hass.data:
        hass.data[DOMAIN_DATA] = {}
        if "data" not in hass.data[DOMAIN_DATA]:
            hass.data[DOMAIN_DATA] = {}

    # Get "global" configuration.
    api_key = config_entry.data.get("api_key")
    check = config_entry.data.get("check")
    self_hosted = config_entry.data.get("self_hosted")
    site_root = config_entry.data.get("site_root")
    ping_endpoint = config_entry.data.get("ping_endpoint")

    # Configure the client.
    hass.data[DOMAIN_DATA]["client"] = HealthchecksioData(
        hass, api_key, check, self_hosted, site_root, ping_endpoint
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.BINARY_SENSOR
    )
    if unload_ok:
        hass.data.pop(DOMAIN_DATA, None)
        LOGGER.info("Successfully removed the healthchecksio integration")
    return unload_ok


class HealthchecksioData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, api_key, check, self_hosted, site_root, ping_endpoint):
        """Initialize the class."""
        self.hass = hass
        self.api_key = api_key
        self.check = check
        self.self_hosted = self_hosted
        self.site_root = site_root if self_hosted else OFFICIAL_SITE_ROOT
        self.ping_endpoint = ping_endpoint

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update_data(self):
        """Update data."""
        LOGGER.debug("Running update")
        # This is where the main logic to update platform data goes.
        try:
            verify_ssl = not self.self_hosted or self.site_root.startswith("https")
            session = async_get_clientsession(self.hass, verify_ssl)
            headers = {"X-Api-Key": self.api_key}
            async with async_timeout.timeout(10):
                data = await session.get(
                    f"{self.site_root}/api/v1/checks/", headers=headers
                )
                self.hass.data[DOMAIN_DATA]["data"] = await data.json()

                if self.self_hosted:
                    check_url = f"{self.site_root}/{self.ping_endpoint}/{self.check}"
                else:
                    check_url = f"https://hc-ping.com/{self.check}"
                await asyncio.sleep(1)  # needed for self-hosted instances
                await session.get(check_url)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Could not update data")

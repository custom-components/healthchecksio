"""
Integration to integrate with healthchecks.io

For more details about this component, please refer to
https://github.com/custom-components/healthchecksio
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    OFFICIAL_SITE_ROOT,
    PLATFORMS,
)
from .coordinator import HealthchecksioDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant import config_entries, core

LOGGER = getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    self_hosted = config_entry.data.get("self_hosted", False)
    site_root = config_entry.data.get("site_root", OFFICIAL_SITE_ROOT)

    # Configure the client.
    config_entry.runtime_data = coordinator = HealthchecksioDataUpdateCoordinator(
        hass=hass,
        api_key=config_entry.data["api_key"],
        session=async_get_clientsession(
            hass=hass,
            verify_ssl=not self_hosted or site_root.startswith("https"),
        ),
        self_hosted=self_hosted,
        check_id=config_entry.data["check"],
        site_root=site_root,
        ping_endpoint=config_entry.data.get("ping_endpoint"),
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

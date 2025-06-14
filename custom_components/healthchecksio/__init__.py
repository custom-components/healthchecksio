"""Integration to integrate Home Assistant with HealthChecks.io."""

from __future__ import annotations

import logging

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_SELF_HOSTED,
    CONF_SITE_ROOT,
    DEFAULT_SELF_HOSTED,
    DOMAIN,
)
from .coordinator import HealthchecksioDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up this integration using UI."""

    # Get "global" configuration.
    self_hosted: bool = config_entry.data.get(CONF_SELF_HOSTED, DEFAULT_SELF_HOSTED)
    site_root: str | None = config_entry.data.get(CONF_SITE_ROOT)
    platforms: list[Platform] = []
    if config_entry.data.get(CONF_CREATE_BINARY_SENSOR):
        platforms.append(Platform.BINARY_SENSOR)
    if config_entry.data.get(CONF_CREATE_SENSOR):
        platforms.append(Platform.SENSOR)

    # Configure the client.
    coordinator: HealthchecksioDataUpdateCoordinator = HealthchecksioDataUpdateCoordinator(
        hass=hass,
        api_key=config_entry.data["api_key"],
        session=async_get_clientsession(
            hass=hass,
            verify_ssl=bool(
                not self_hosted or (isinstance(site_root, str) and site_root.startswith("https"))
            ),
        ),
        self_hosted=self_hosted,
        check_id=config_entry.data["check"],
        site_root=site_root,
        ping_endpoint=config_entry.data.get("ping_endpoint"),
    )
    config_entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    _LOGGER.debug("Config Entry: %s", config_entry.as_dict())

    return True


async def async_unload_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Config Entry: %s", config_entry.as_dict())
    curr_plat = [
        p.domain
        for p in entity_platform.async_get_platforms(hass, DOMAIN)
        if (
            p.config_entry is not None
            and config_entry.entry_id == p.config_entry.entry_id
            and p.config_entry.state == config_entries.ConfigEntryState.LOADED
        )
    ]

    _LOGGER.debug("Unloading Platforms: %s", curr_plat)
    unload_ok = True
    if curr_plat:
        unload_ok = await hass.config_entries.async_unload_platforms(
            config_entry,
            curr_plat,
        )
    if unload_ok:
        _LOGGER.info("Successfully removed the HealthChecks.io integration")

    return unload_ok

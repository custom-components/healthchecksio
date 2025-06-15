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
    CONF_API_KEY,
    CONF_CHECK_SITE_ROOT,
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_PING_ID,
    # CONF_SITE_ROOT,
    # CONF_CHECK,
    CONF_PING_SITE_ROOT,
    CONF_SELF_HOSTED,
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

    _LOGGER.debug("config_entry: %s", config_entry)
    _LOGGER.debug("config_entry.data: %s", config_entry.data)
    # Get "global" configuration.
    self_hosted: bool = config_entry.data.get(CONF_SELF_HOSTED, DEFAULT_SELF_HOSTED)
    check_site_root: str = config_entry.data.get(CONF_CHECK_SITE_ROOT)
    ping_site_root: str = config_entry.data.get(CONF_PING_SITE_ROOT)
    platforms: list[Platform] = []
    if config_entry.data.get(CONF_CREATE_BINARY_SENSOR):
        platforms.append(Platform.BINARY_SENSOR)
    if config_entry.data.get(CONF_CREATE_SENSOR):
        platforms.append(Platform.SENSOR)

    # Configure the client.
    coordinator: HealthchecksioDataUpdateCoordinator = HealthchecksioDataUpdateCoordinator(
        hass=hass,
        api_key=config_entry.data.get(CONF_API_KEY),
        ping_session=async_get_clientsession(
            hass=hass,
            verify_ssl=bool(
                not self_hosted
                or (isinstance(ping_site_root, str) and ping_site_root.startswith("https"))
            ),
        ),
        check_session=async_get_clientsession(
            hass=hass,
            verify_ssl=bool(
                not self_hosted
                or (isinstance(check_site_root, str) and check_site_root.startswith("https"))
            ),
        ),
        self_hosted=self_hosted,
        ping_id=config_entry.data.get(CONF_PING_ID),
        ping_site_root=ping_site_root,
        check_site_root=check_site_root,
        ping_endpoint=config_entry.data.get(CONF_PING_ENDPOINT),
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

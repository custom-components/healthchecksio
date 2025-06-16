"""Integration to integrate Home Assistant with HealthChecks.io."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_PING_UUID,
    CONF_SITE_ROOT,
    DOMAIN,
)
from .coordinator import HealthchecksioDataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _LOGGER.debug("Config Entry: %s", config_entry.as_dict())

    site_root: str = config_entry.data[CONF_SITE_ROOT]
    ping_endpoint: str = config_entry.data[CONF_PING_ENDPOINT]
    platforms: list[Platform] = []
    if config_entry.data.get(CONF_CREATE_BINARY_SENSOR):
        platforms.append(Platform.BINARY_SENSOR)
    if config_entry.data.get(CONF_CREATE_SENSOR):
        platforms.append(Platform.SENSOR)

    # Configure the client.
    coordinator: HealthchecksioDataUpdateCoordinator = HealthchecksioDataUpdateCoordinator(
        hass=hass,
        api_key=config_entry.data[CONF_API_KEY],
        site_root=site_root,
        ping_endpoint=ping_endpoint,
        ping_session=async_get_clientsession(
            hass=hass,
            verify_ssl=ping_endpoint.startswith("https"),
        ),
        check_session=async_get_clientsession(
            hass=hass,
            verify_ssl=site_root.startswith("https"),
        ),
        ping_uuid=config_entry.data.get(CONF_PING_UUID),
    )
    config_entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Config Entry: %s", config_entry.as_dict())
    curr_plat: list[str] = [
        p.domain
        for p in entity_platform.async_get_platforms(hass, DOMAIN)
        if p.config_entry is not None and config_entry.entry_id == p.config_entry.entry_id
    ]

    if curr_plat:
        _LOGGER.debug("Unloading Platforms: %s", curr_plat)
        try:
            unload_ok = await hass.config_entries.async_unload_platforms(
                config_entry,
                curr_plat,
            )
        except ValueError as e:
            unload_ok = False
            _LOGGER.error(
                "Unable to unload platforms. %s: %s",
                e.__class__.__qualname__,
                e,
            )
    else:
        unload_ok = False
        _LOGGER.error("Unable to identify platforms to unload")
    if unload_ok:
        _LOGGER.info("Successfully removed the HealthChecks.io integration")
    return unload_ok

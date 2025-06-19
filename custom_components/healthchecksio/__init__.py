"""Integration to integrate Home Assistant with HealthChecks.io."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_PING_UUID,
    CONF_SELF_HOSTED,
    CONF_SITE_ROOT,
    DEFAULT_PING_ENDPOINT,
    DEFAULT_SITE_ROOT,
)
from .coordinator import HealthchecksioDataUpdateCoordinator
from .helpers import clean_url

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

    platforms: list[Platform] = []
    if config_entry.data.get(CONF_CREATE_BINARY_SENSOR):
        platforms.append(Platform.BINARY_SENSOR)
    if config_entry.data.get(CONF_CREATE_SENSOR):
        platforms.append(Platform.SENSOR)

    _LOGGER.debug("Unloading Platforms: %s", platforms)
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry,
        platforms,
    )

    if unload_ok:
        _LOGGER.info("Successfully removed the HealthChecks.io integration")
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate an old config entry."""
    version = config_entry.version

    if version > 2:
        # This means the user has downgraded from a future version
        _LOGGER.error(
            "HealthChecks.io downgraded and current config not compatible with earlier versions. Integration must be removed and reinstalled."
        )
        return False

    _LOGGER.debug("Migrating from version %s", version)

    if version == 1:
        v1to2: bool = _migrate_1_to_2(hass, config_entry)
        if not v1to2:
            return False
        version = 2

    _LOGGER.info("Migration to version %s successful", version)
    return True


def _migrate_1_to_2(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    entity_registry = er.async_get(hass)
    data = dict(config_entry.data)

    CONF_CHECK = "check"

    data[CONF_CREATE_BINARY_SENSOR] = True
    data[CONF_CREATE_SENSOR] = False
    data[CONF_PING_UUID] = data.get(CONF_CHECK)
    data.pop(CONF_CHECK, None)
    if data.get(CONF_SELF_HOSTED):
        ping_endpoint = f"{data.get(CONF_SITE_ROOT)}/{data.get(CONF_PING_ENDPOINT)}"
        data[CONF_PING_ENDPOINT] = clean_url(ping_endpoint)
    else:
        data[CONF_SITE_ROOT] = DEFAULT_SITE_ROOT
        data[CONF_PING_ENDPOINT] = DEFAULT_PING_ENDPOINT

    new_device_unique_id = data.get(CONF_API_KEY)

    for ent in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        # _LOGGER.debug("[migrate_1_to_2] ent: %s", ent)
        platform = ent.entity_id.split(".")[0]
        if platform != Platform.BINARY_SENSOR or ent.unique_id.startswith("binary_sensor_"):
            continue

        new_unique_id = f"binary_sensor_{ent.unique_id}"

        _LOGGER.debug(
            "[migrate_1_to_2] ent: %s, platform: %s, unique_id: %s, new_unique_id: %s",
            ent.entity_id,
            platform,
            ent.unique_id,
            new_unique_id,
        )

        try:
            new_ent = entity_registry.async_update_entity(
                ent.entity_id, new_unique_id=new_unique_id
            )
            _LOGGER.debug(
                "[migrate_1_to_2] new_ent: %s, unique_id: %s",
                new_ent.entity_id,
                new_ent.unique_id,
            )
        except ValueError as e:
            _LOGGER.error(
                "Error migrating entity: %s. %s: %s",
                ent.entity_id,
                e.__class__.__qualname__,
                e,
            )

    _LOGGER.debug(
        "[migrate_1_to_2] data: %s, new_data: %s, unique_id: %s, new_unique_id: %s",
        config_entry.data,
        data,
        config_entry.unique_id,
        new_device_unique_id,
    )
    new_entry_bool = hass.config_entries.async_update_entry(
        config_entry, data=data, unique_id=new_device_unique_id, version=2
    )
    if new_entry_bool:
        _LOGGER.debug("[migrate_1_to_2] config_entry update sucessful")
    else:
        _LOGGER.error("Migration of config_entry to version 2 unsucessful")
        return False
    return True

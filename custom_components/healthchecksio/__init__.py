"""
Integration to integrate with healthchecks.io

For more details about this component, please refer to
https://github.com/custom-components/healthchecksio
"""
import asyncio
import json
import logging
import os
from datetime import timedelta

import aiohttp
from homeassistant import config_entries, core
from homeassistant.const import Platform
from homeassistant.helpers import entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
from integrationhelper.const import CC_STARTUP_VERSION

from .const import (
    CONF_API_KEY,
    CONF_CHECK,
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_SELF_HOSTED,
    CONF_SITE_ROOT,
    DATA_CLIENT,
    DATA_DATA,
    DOMAIN,
    DOMAIN_DATA,
    INTEGRATION_NAME,
    INTEGRATION_VERSION,
    ISSUE_URL,
    OFFICIAL_SITE_ROOT,
    REQUIRED_FILES,
)

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)


async def async_setup(
    hass: core.HomeAssistant, config: config_entries.ConfigEntry
) -> bool:
    """Set up this component using YAML is not supported."""
    if config.get(DOMAIN) is not None:
        _LOGGER.error("Configuration with YAML is not supported")

    return True


async def async_setup_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
) -> bool:
    """Set up this integration using UI."""
    # Print startup message
    _LOGGER.info(
        CC_STARTUP_VERSION.format(
            name=INTEGRATION_NAME, version=INTEGRATION_VERSION, issue_link=ISSUE_URL
        )
    )

    # Check that all required files are present
    file_check = await check_files(hass)
    if not file_check:
        return False

    # Create DATA dict
    if DOMAIN_DATA not in hass.data:
        hass.data[DOMAIN_DATA] = {}
    if DATA_DATA not in hass.data[DOMAIN_DATA]:
        hass.data[DOMAIN_DATA][DATA_DATA] = {}

    # Get "global" configuration.
    api_key = config_entry.data.get(CONF_API_KEY)
    check = config_entry.data.get(CONF_CHECK)
    self_hosted = config_entry.data.get(CONF_SELF_HOSTED)
    site_root = config_entry.data.get(CONF_SITE_ROOT)
    ping_endpoint = config_entry.data.get(CONF_PING_ENDPOINT)
    platforms = []
    if config_entry.data.get(CONF_CREATE_BINARY_SENSOR):
        platforms.append(Platform.BINARY_SENSOR)
    if config_entry.data.get(CONF_CREATE_SENSOR):
        platforms.append(Platform.SENSOR)

    # Configure the client.
    hass.data[DOMAIN_DATA][DATA_CLIENT] = HealthchecksioData(
        hass, api_key, check, self_hosted, site_root, ping_endpoint
    )
    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    _LOGGER.debug(f"Config Entry: {config_entry.as_dict()}")

    return True


async def async_unload_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading Config Entry: {config_entry.as_dict()}")
    curr_plat = []
    for p in entity_platform.async_get_platforms(hass, DOMAIN):
        if (
            p.config_entry is not None
            and config_entry.entry_id == p.config_entry.entry_id
            and p.config_entry.state == config_entries.ConfigEntryState.LOADED
        ):
            curr_plat.append(p.domain)
    _LOGGER.debug(f"Unloading Platforms: {curr_plat}")
    unload_ok = True
    if curr_plat:
        unload_ok = await hass.config_entries.async_unload_platforms(
            config_entry,
            curr_plat,
        )
    if unload_ok:
        hass.data[DOMAIN_DATA].pop(DATA_CLIENT, None)
        hass.data[DOMAIN_DATA].pop(DATA_DATA, None)
        _LOGGER.info("Successfully removed the HealthChecks.io integration")

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
        _LOGGER.debug("Running Update")
        # This is where the main logic to update platform data goes.
        verify_ssl = not self.self_hosted or self.site_root.startswith("https")
        session = async_get_clientsession(self.hass, verify_ssl)
        timeout10 = aiohttp.ClientTimeout(total=10)
        headers = {"X-Api-Key": self.api_key}
        if self.check is not None:
            if self.self_hosted:
                check_url = f"{self.site_root}/{self.ping_endpoint}/{self.check}"
            else:
                check_url = f"https://hc-ping.com/{self.check}"
            await asyncio.sleep(1)  # needed for self-hosted instances
            try:
                check_response = await session.get(check_url, timeout=timeout10)
            except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                _LOGGER.error(f"Could Not Send Check: {error}")
            else:
                if check_response.ok:
                    _LOGGER.debug(
                        f"Send Check HTTP Status Code: {check_response.status}"
                    )
                else:
                    _LOGGER.error(
                        f"Error: Send Check HTTP Status Code: {check_response.status}"
                    )
        else:
            _LOGGER.debug("Send Check is not defined")
        try:
            async with session.get(
                f"{self.site_root}/api/v1/checks/",
                headers=headers,
                timeout=timeout10,
            ) as data:
                self.hass.data[DOMAIN_DATA][DATA_DATA] = await data.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            _LOGGER.error(f"Could Not Update Data: {error}")
        except (ValueError, json.decoder.JSONDecodeError) as error:
            _LOGGER.error(f"Data JSON Decode Error: {error}")
        else:
            if data.ok:
                _LOGGER.debug(f"Get Data HTTP Status Code: {data.status}")
            else:
                _LOGGER.error(f"Error: Get Data HTTP Status Code: {data.status}")


async def check_files(hass: core.HomeAssistant) -> bool:
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = f"{hass.config.path()}/custom_components/{DOMAIN}/"
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        _LOGGER.critical(f"The following files are missing: {missing}")
        return False
    else:
        return True

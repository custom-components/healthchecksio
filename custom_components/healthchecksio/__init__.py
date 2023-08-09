"""
Integration to integrate with healthchecks.io

For more details about this component, please refer to
https://github.com/custom-components/healthchecksio
"""
import asyncio
import json
import os
from datetime import timedelta

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
from integrationhelper import Logger
from integrationhelper.const import CC_STARTUP_VERSION

from .const import (
    DOMAIN,
    DOMAIN_DATA,
    INTEGRATION_VERSION,
    ISSUE_URL,
    OFFICIAL_SITE_ROOT,
    REQUIRED_FILES,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)


async def async_setup(hass, config):
    """Set up this component using YAML is not supported."""
    if config.get(DOMAIN) is not None:
        Logger("custom_components.healthchecksio").error(
            "Configuration with YAML is not supported"
        )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    # Print startup message
    Logger("custom_components.healthchecksio").info(
        CC_STARTUP_VERSION.format(
            name=DOMAIN, version=INTEGRATION_VERSION, issue_link=ISSUE_URL
        )
    )

    # Check that all required files are present
    file_check = await check_files(hass)
    if not file_check:
        return False

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

    # Add binary_sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    return True


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
        Logger("custom_components.healthchecksio").debug("Running Update")
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
                Logger("custom_components.healthchecksio").error(
                    f"Could Not Send Check: {error}"
                )
            else:
                if check_response.ok:
                    Logger("custom_components.healthchecksio").debug(
                        f"Send Check HTTP Status Code: {check_response.status}"
                    )
                else:
                    Logger("custom_components.healthchecksio").error(
                        f"Error: Send Check HTTP Status Code: {check_response.status}"
                    )
        else:
            Logger("custom_components.healthchecksio").debug(
                "Send Check is not defined."
            )
        try:
            async with session.get(
                f"{self.site_root}/api/v1/checks/",
                headers=headers,
                timeout=timeout10,
            ) as data:
                self.hass.data[DOMAIN_DATA]["data"] = await data.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            Logger("custom_components.healthchecksio").error(
                f"Could Not Update Data: {error}"
            )
        except (ValueError, json.decoder.JSONDecodeError) as error:
            Logger("custom_components.healthchecksio").error(
                f"Data JSON Decode Error: {error}"
            )
        else:
            if data.ok:
                Logger("custom_components.healthchecksio").debug(
                    f"Get Data HTTP Status Code: {data.status}"
                )
            else:
                Logger("custom_components.healthchecksio").error(
                    f"Error: Get Data HTTP Status Code: {data.status}"
                )


async def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = f"{hass.config.path()}/custom_components/{DOMAIN}/"
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        Logger("custom_components.healthchecksio").critical(
            f"The following files are missing: {missing}"
        )
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    Logger("custom_components.healthchecksio").info(
        "Successfully removed the healthchecksio integration"
    )

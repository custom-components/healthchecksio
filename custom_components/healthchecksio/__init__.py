"""
Integration to integrate with healthchecks.io

For more details about this component, please refer to
https://github.com/custom-components/healthchecksio
"""
import os
import async_timeout
import asyncio
from datetime import timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.util import Throttle

from sampleclient.client import Client
from integrationhelper.const import CC_STARTUP_VERSION
from integrationhelper import Logger, WebClient

from .const import DOMAIN_DATA, DOMAIN, ISSUE_URL, PLATFORMS, REQUIRED_FILES, VERSION

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
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
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
    monitor = config_entry.data.get("monitor")

    # Configure the client.
    hass.data[DOMAIN_DATA]["client"] = HealthchecksioData(hass, api_key, monitor)

    # Add binary_sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    return True


class HealthchecksioData:
    """This class handle communication and stores the data."""

    def __init__(self, hass, api_key, monitor):
        """Initialize the class."""
        self.hass = hass
        self.api_key = api_key
        self.monitor = monitor

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update_data(self):
        """Update data."""
        Logger("custom_components.healthchecksio").debug("Running update")
        # This is where the main logic to update platform data goes.
        try:
            session = async_get_clientsession(self.hass)
            headers = {"X-Api-Key": self.api_key}
            async with async_timeout.timeout(10, loop=asyncio.get_event_loop()):
                data = await session.get(
                    "https://healthchecks.io/api/v1/checks/", headers=headers
                )
                self.hass.data[DOMAIN_DATA]["data"] = await data.json()

            await session.get(f"https://hc-ping.com/{self.monitor}")
        except Exception as error:  # pylint: disable=broad-except
            Logger("custom_components.healthchecksio").error(
                f"Could not update data - {error}"
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

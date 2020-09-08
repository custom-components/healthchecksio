"""Adds config flow for Blueprint."""
import async_timeout
import asyncio
from collections import OrderedDict
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from integrationhelper import Logger
from homeassistant import config_entries

from .const import DOMAIN, DOMAIN_DATA


@config_entries.HANDLERS.register(DOMAIN)
class BlueprintFlowHandler(config_entries.ConfigFlow):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(
        self, user_input={}
    ):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        self._errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input["site_root"], user_input["ping_endpoint"],
                user_input["api_key"], user_input["check"]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input["check"], data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""

        # Defaults
        site_root = "https://healthchecks.io"
        ping_endpoint = "ping"
        api_key = ""
        check = ""

        if user_input is not None:
            if "site_root" in user_input:
                site_root = user_input["site_root"]
            if "ping_endpoint" in user_input:
                ping_endpoint = user_input["ping_endpoint"]
            if "api_key" in user_input:
                api_key = user_input["api_key"]
            if "check" in user_input:
                check = user_input["check"]

        data_schema = OrderedDict()
        data_schema[vol.Required("site_root", default=site_root)] = str
        data_schema[vol.Required("ping_endpoint", default=ping_endpoint)] = str
        data_schema[vol.Required("api_key", default=api_key)] = str
        data_schema[vol.Required("check", default=check)] = str
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def _test_credentials(self, site_root, ping_endpoint, api_key, check):
        """Return true if credentials is valid."""
        try:
            verify_ssl = site_root.startswith("https")
            session = async_get_clientsession(self.hass, verify_ssl)
            headers = {"X-Api-Key": api_key}

            async with async_timeout.timeout(10, loop=asyncio.get_event_loop()):
                Logger("custom_components.healthchecksio").info("Checking API Key")
                data = await session.get(
                    f"{site_root}/api/v1/checks/", headers=headers
                )
                self.hass.data[DOMAIN_DATA] = {"data": await data.json()}
                Logger("custom_components.healthchecksio").info("Checking Check ID")
                data = await session.get(f"{site_root}/{ping_endpoint}/{check}")
            return True
        except Exception as exception:  # pylint: disable=broad-except
            Logger("custom_components.healthchecksio").error(exception)
        return False

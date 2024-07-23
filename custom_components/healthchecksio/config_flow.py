"""Adds config flow for Blueprint."""

from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from logging import getLogger

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, OFFICIAL_SITE_ROOT

LOGGER = getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class BlueprintFlowHandler(config_entries.ConfigFlow):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.initial_data = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if user_input["self_hosted"]:
                # don't check yet, we need more info
                self.initial_data = user_input
                return await self._show_self_hosted_config_flow(user_input)
            else:
                valid = await self._test_credentials(
                    user_input["api_key"],
                    user_input["check"],
                    False,
                    OFFICIAL_SITE_ROOT,
                    None,
                )
                if valid:
                    user_input["self_hosted"] = False
                    return self.async_create_entry(
                        title=user_input["check"], data=user_input
                    )
                else:
                    self._errors["base"] = "auth"

        return await self._show_initial_config_form(user_input)

    async def _show_initial_config_form(self, user_input):
        """Show the configuration form to edit check data."""
        # Defaults
        api_key = ""
        check = ""
        self_hosted = False

        if user_input is not None:
            if "api_key" in user_input:
                api_key = user_input["api_key"]
            if "check" in user_input:
                check = user_input["check"]
            if "self_hosted" in user_input:
                self_hosted = user_input["self_hosted"]

        data_schema = OrderedDict()
        data_schema[vol.Required("api_key", default=api_key)] = str
        data_schema[vol.Required("check", default=check)] = str
        data_schema[vol.Required("self_hosted", default=self_hosted)] = bool
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_self_hosted(self, user_input):
        """Handle the step for a self-hosted instance."""
        self._errors = {}
        valid = await self._test_credentials(
            self.initial_data["api_key"],
            self.initial_data["check"],
            True,
            user_input["site_root"],
            user_input["ping_endpoint"],
        )
        if valid:
            # merge data from initial config flow and this flow
            data = {**self.initial_data, **user_input}
            return self.async_create_entry(title=self.initial_data["check"], data=data)
        else:
            self._errors["base"] = "auth"

        return await self._show_self_hosted_config_flow(user_input)

    async def _show_self_hosted_config_flow(self, user_input):
        """Show the configuration form to edit self-hosted instance data."""
        # Defaults
        site_root = "https://checks.mydomain.com"
        ping_endpoint = "ping"

        if "site_root" in user_input:
            site_root = user_input["site_root"]
        if "ping_endpoint" in user_input:
            ping_endpoint = user_input["ping_endpoint"]

        data_schema = OrderedDict()
        data_schema[vol.Required("site_root", default=site_root)] = str
        data_schema[vol.Required("ping_endpoint", default=ping_endpoint)] = str
        return self.async_show_form(
            step_id="self_hosted",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(
        self, api_key, check, self_hosted, site_root, ping_endpoint
    ):
        """Return true if credentials is valid."""
        LOGGER.debug("Testing Credentials")
        verify_ssl = not self_hosted or site_root.startswith("https")
        session = async_get_clientsession(self.hass, verify_ssl)
        timeout10 = aiohttp.ClientTimeout(total=10)
        headers = {"X-Api-Key": api_key}
        if self_hosted:
            check_url = f"{site_root}/{ping_endpoint}/{check}"
        else:
            check_url = f"https://hc-ping.com/{check}"
        await asyncio.sleep(1)  # needed for self-hosted instances
        try:
            check_response = await session.get(check_url, timeout=timeout10)
        except (TimeoutError, aiohttp.ClientError):
            LOGGER.exception("Could Not Send Check")
            return False
        else:
            if check_response.ok:
                LOGGER.debug("Send Check HTTP Status Code: %s", check_response.status)
            else:
                LOGGER.error("Send Check HTTP Status Code: %s", check_response.status)
                return False
        try:
            request = await session.get(
                f"{site_root}/api/v1/checks/", headers=headers, timeout=timeout10
            )
        except (TimeoutError, aiohttp.ClientError):
            LOGGER.exception("Could Not Update Data")
            return False
        except (ValueError, json.decoder.JSONDecodeError):
            LOGGER.exception("Data JSON Decode Error")
            return False
        else:
            if not request.ok:
                LOGGER.error("Got Data HTTP Status Code: %s", request.status)
                return False
            LOGGER.debug("Got Data HTTP Status Code: %s", request.status)
            return True

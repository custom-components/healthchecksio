"""Adds config flow for HealthChecks.io"""
from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from logging import getLogger

import asyncio
import json
import logging


import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, OFFICIAL_SITE_ROOT

from .const import (
    CONF_API_KEY,
    CONF_CHECK,
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_SELF_HOSTED,
    CONF_SITE_ROOT,
    DEFAULT_CREATE_BINARY_SENSOR,
    DEFAULT_CREATE_SENSOR,
    DEFAULT_PING_ENDPOINT,
    DEFAULT_SELF_HOSTED,
    DEFAULT_SITE_ROOT,
    DOMAIN,
    DOMAIN_DATA,
    OFFICIAL_SITE_ROOT,
)

_LOGGER = logging.getLogger(__name__)


async def _test_credentials(
    hass, api_key, check, self_hosted, site_root, ping_endpoint
):
    """Return true if credentials is valid."""
    _LOGGER.debug("Testing Credentials")
    verify_ssl = not self_hosted or site_root.startswith("https")
    session = async_get_clientsession(hass, verify_ssl)
    timeout10 = aiohttp.ClientTimeout(total=10)
    headers = {"X-Api-Key": api_key}
    if check is not None:
        if self_hosted:
            check_url = f"{site_root}/{ping_endpoint}/{check}"
        else:
            check_url = f"https://hc-ping.com/{check}"
        await asyncio.sleep(1)  # needed for self-hosted instances
        try:
            check_response = await session.get(check_url, timeout=timeout10)
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            _LOGGER.error(f"Could Not Send Check: {error}")
            return False
        else:
            if check_response.ok:
                _LOGGER.debug(f"Send Check HTTP Status Code: {check_response.status}")
            else:
                check_url = f"https://hc-ping.com/{check}"
            await asyncio.sleep(1)  # needed for self-hosted instances
            try:
                check_response = await session.get(check_url, timeout=timeout10)
            except (aiohttp.ClientError, asyncio.TimeoutError) as error:
                _LOGGER.error(f"Could Not Send Check: {error}")
                return False
    else:
        _LOGGER.debug("Send Check is not defined")
    try:
        data = await session.get(
            f"{site_root}/api/v1/checks/", headers=headers, timeout=timeout10
        )
        hass.data[DOMAIN_DATA] = {"data": await data.json()}
    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        _LOGGER.error(f"Could Not Update Data: {error}")
        return False
    except (ValueError, json.decoder.JSONDecodeError) as error:
        _LOGGER.error(f"Data JSON Decode Error: {error}")
        return False
    else:
        if not data.ok:
            _LOGGER.error(f"Error: Get Data HTTP Status Code: {data.status}")
            return False
        _LOGGER.debug(f"Get Data HTTP Status Code: {data.status}")
        return True


class HealchecksioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HealthChecks.io"""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.initial_data = None

    async def async_step_user(self, user_input=None, errors=None):
        self._errors = {}
        if self._async_current_entries() or self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            if not user_input.get(CONF_CREATE_BINARY_SENSOR) and not user_input.get(
                CONF_CREATE_SENSOR
            ):
                self._errors["base"] = "need_a_sensor"
            elif user_input.get(CONF_SELF_HOSTED):
                # don't check yet, we need more info
                self.initial_data = user_input
                return await self.async_step_self_hosted()
            else:
                valid = await _test_credentials(
                    self.hass,
                    user_input.get(CONF_API_KEY),
                    user_input.get(CONF_CHECK),
                    False,
                    OFFICIAL_SITE_ROOT,
                    None,
                )
                if valid:
                    user_input[CONF_SELF_HOSTED] = False
                    return self.async_create_entry(
                        title=user_input.get(CONF_CHECK, DOMAIN), data=user_input
                    )
                else:
                    self._errors["base"] = "auth"

        DATA_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=user_input.get(CONF_API_KEY)
                    if user_input is not None
                    else None,
                ): str,
            }
        )

        if user_input is not None and user_input.get(CONF_CHECK) is not None:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_CHECK, default=user_input.get(CONF_CHECK)): str,
                }
            )
        else:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_CHECK): str,
                }
            )
        DATA_SCHEMA = DATA_SCHEMA.extend(
            {
                vol.Optional(
                    CONF_CREATE_BINARY_SENSOR,
                    default=user_input.get(
                        CONF_CREATE_BINARY_SENSOR, DEFAULT_CREATE_BINARY_SENSOR
                    )
                    if user_input is not None
                    else DEFAULT_CREATE_BINARY_SENSOR,
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(
                    CONF_CREATE_SENSOR,
                    default=user_input.get(CONF_CREATE_SENSOR, DEFAULT_CREATE_SENSOR)
                    if user_input is not None
                    else DEFAULT_CREATE_SENSOR,
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                vol.Optional(
                    CONF_SELF_HOSTED,
                    default=user_input.get(CONF_SELF_HOSTED, DEFAULT_SELF_HOSTED)
                    if user_input is not None
                    else DEFAULT_SELF_HOSTED,
                ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=self._errors
        )

    async def async_step_self_hosted(self, user_input=None):
        """Handle the step for a self-hosted instance."""
        self._errors = {}
        if user_input is not None:
            valid = await _test_credentials(
                self.hass,
                self.initial_data.get(CONF_API_KEY),
                self.initial_data.get(CONF_CHECK),
                True,
                user_input.get(CONF_SITE_ROOT),
                user_input.get(CONF_PING_ENDPOINT),
            )
            if valid:
                # merge data from initial config flow and this flow
                data = {**self.initial_data, **user_input}
                return self.async_create_entry(
                    title=self.initial_data.get(CONF_CHECK, DOMAIN), data=data
                )
            else:
                self._errors["base"] = "auth_self"

        SELF_HOSTED_DATA_SCHEMA = vol.Schema(
            {
                vol.Required(
                    CONF_SITE_ROOT,
                    default=user_input.get(CONF_SITE_ROOT, DEFAULT_SITE_ROOT)
                    if user_input is not None
                    else DEFAULT_SITE_ROOT,
                ): str,
                vol.Optional(
                    CONF_PING_ENDPOINT,
                    default=user_input.get(CONF_PING_ENDPOINT, DEFAULT_PING_ENDPOINT)
                    if user_input is not None
                    else DEFAULT_PING_ENDPOINT,
                ): str,
            }
        )

        return self.async_show_form(
            step_id="self_hosted",
            data_schema=SELF_HOSTED_DATA_SCHEMA,
            errors=self._errors,
        )

"""Config flow for HealthChecks.io integration."""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
import json
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY,
    CONF_CHECK_SITE_ROOT,
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_PING_ID,
    CONF_PING_SITE_ROOT,
    CONF_SELF_HOSTED,
    DEFAULT_CHECK_SITE_ROOT,
    DEFAULT_CREATE_BINARY_SENSOR,
    DEFAULT_CREATE_SENSOR,
    DEFAULT_PING_ENDPOINT,
    DEFAULT_PING_SITE_ROOT,
    DEFAULT_SELF_HOSTED,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def _test_credentials(
    hass: HomeAssistant,
    api_key: str,
    ping_id: str,
    self_hosted: bool,
    ping_site_root: str,
    check_site_root: str,
    ping_endpoint: str | None,
) -> bool:
    """Return true if credentials are valid."""
    _LOGGER.debug("Testing Credentials")
    ping_verify_ssl: bool = not self_hosted or ping_site_root.startswith("https")
    ping_session: aiohttp.ClientSession = async_get_clientsession(hass, ping_verify_ssl)
    check_verify_ssl: bool = not self_hosted or check_site_root.startswith("https")
    check_session: aiohttp.ClientSession = async_get_clientsession(hass, check_verify_ssl)
    timeout10: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=10)
    headers: MutableMapping[str, Any] = {"X-Api-Key": api_key}
    if ping_id is not None:
        if self_hosted:
            ping_url: str = f"{ping_site_root}/{ping_endpoint}/{ping_id}"
        else:
            ping_url = f"https://hc-ping.com/{ping_id}"
        _LOGGER.debug("ping_url: %s", ping_url)
        await asyncio.sleep(1)  # needed for self-hosted instances

        try:
            ping_response = await ping_session.get(ping_url, timeout=timeout10)
        except ClientError as e:
            _LOGGER.error(
                "Could Not Send Ping using URL: %s. %s: %s",
                ping_url,
                e.__class__.__qualname__,
                e,
            )
            return False
        else:
            if ping_response.ok:
                _LOGGER.debug("Send Ping HTTP Status Code: %s", ping_response.status)
            else:
                _LOGGER.error("Error: Send Ping HTTP Status Code: %s", ping_response.status)
                return False
    else:
        _LOGGER.debug("Send Ping is not defined")

    try:
        data = await check_session.get(
            f"{check_site_root}/api/v1/checks/", headers=headers, timeout=timeout10
        )
    except (TimeoutError, aiohttp.ClientError) as e:
        _LOGGER.error(
            "Could Not Update Data. %s: %s",
            e.__class__.__qualname__,
            e,
        )
        return False
    except (ValueError, json.decoder.JSONDecodeError) as e:
        _LOGGER.error(
            "Data JSON Decode Error. %s: %s",
            e.__class__.__qualname__,
            e,
        )
        return False
    else:
        if not data.ok:
            _LOGGER.error("Error: Get Data HTTP Status Code: %s", data.status)
            return False
        _LOGGER.debug("Get Data HTTP Status Code: %s", data.status)
        return True


class HealthchecksioConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for HealthChecks.io integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: MutableMapping[str, Any] = {}
        self.initial_data: MutableMapping[str, Any] = {}

    async def async_step_user(
        self,
        user_input: MutableMapping[str, Any] | None = None,
        errors: MutableMapping[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """User Input step."""
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
                user_input[CONF_CHECK_SITE_ROOT] = DEFAULT_CHECK_SITE_ROOT
                user_input[CONF_PING_SITE_ROOT] = DEFAULT_PING_SITE_ROOT
                valid: bool = await _test_credentials(
                    hass=self.hass,
                    api_key=user_input.get(CONF_API_KEY, ""),
                    ping_id=user_input.get(CONF_PING_ID, ""),
                    self_hosted=False,
                    ping_site_root=user_input.get(CONF_PING_SITE_ROOT, ""),
                    check_site_root=user_input.get(CONF_CHECK_SITE_ROOT, ""),
                    ping_endpoint=None,
                )
                if valid:
                    user_input[CONF_SELF_HOSTED] = False
                    return self.async_create_entry(
                        title=user_input.get(CONF_PING_ID, DOMAIN), data=user_input
                    )
                self._errors["base"] = "auth"

        DATA_SCHEMA: vol.Schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=user_input.get(CONF_API_KEY) if user_input is not None else None,
                ): str,
            }
        )

        if user_input is not None and user_input.get(CONF_PING_ID) is not None:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_PING_ID, default=user_input.get(CONF_PING_ID)): str,
                }
            )
        else:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_PING_ID): str,
                }
            )
        DATA_SCHEMA = DATA_SCHEMA.extend(
            {
                vol.Optional(
                    CONF_CREATE_BINARY_SENSOR,
                    default=user_input.get(CONF_CREATE_BINARY_SENSOR, DEFAULT_CREATE_BINARY_SENSOR)
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

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=self._errors)

    async def async_step_self_hosted(self, user_input: MutableMapping[str, Any] | None = None):
        """Handle the step for a self-hosted instance."""
        self._errors = {}
        if user_input is not None:
            valid: bool = await _test_credentials(
                hass=self.hass,
                api_key=self.initial_data.get(CONF_API_KEY, ""),
                ping_id=self.initial_data.get(CONF_PING_ID, ""),
                self_hosted=True,
                ping_site_root=user_input.get(CONF_PING_SITE_ROOT, ""),
                check_site_root=user_input.get(CONF_CHECK_SITE_ROOT, ""),
                ping_endpoint=user_input.get(CONF_PING_ENDPOINT),
            )
            if valid:
                # merge data from initial config flow and this flow
                data: MutableMapping[str, Any] = {**self.initial_data, **user_input}
                return self.async_create_entry(
                    title=self.initial_data.get(CONF_PING_ID, DOMAIN), data=data
                )
            self._errors["base"] = "auth_self"

        SELF_HOSTED_DATA_SCHEMA: vol.Schema = vol.Schema(
            {
                vol.Required(
                    CONF_PING_SITE_ROOT,
                    default=user_input.get(CONF_PING_SITE_ROOT, DEFAULT_PING_SITE_ROOT)
                    if user_input is not None
                    else DEFAULT_PING_SITE_ROOT,
                ): str,
                vol.Required(
                    CONF_CHECK_SITE_ROOT,
                    default=user_input.get(CONF_CHECK_SITE_ROOT, DEFAULT_CHECK_SITE_ROOT)
                    if user_input is not None
                    else DEFAULT_CHECK_SITE_ROOT,
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

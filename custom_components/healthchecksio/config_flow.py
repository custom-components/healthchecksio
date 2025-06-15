"""Config flow for HealthChecks.io integration."""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
import logging
import re
from typing import Any
from urllib.parse import ParseResult, urlparse, urlunparse

from aiohttp import ClientError, ClientSession, ClientTimeout
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CREATE_BINARY_SENSOR,
    CONF_CREATE_SENSOR,
    CONF_PING_ENDPOINT,
    CONF_PING_UUID,
    CONF_SELF_HOSTED,
    CONF_SITE_ROOT,
    DEFAULT_CREATE_BINARY_SENSOR,
    DEFAULT_CREATE_SENSOR,
    DEFAULT_PING_ENDPOINT,
    DEFAULT_SELF_HOSTED,
    DEFAULT_SITE_ROOT,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def _test_credentials(
    hass: HomeAssistant,
    api_key: str,
    site_root: str,
    ping_endpoint: str,
    ping_uuid: str | None = None,
) -> bool:
    """Return true if credentials are valid."""
    _LOGGER.debug("Testing Credentials")
    check_verify_ssl: bool = site_root.startswith("https")
    check_session: ClientSession = async_get_clientsession(hass, check_verify_ssl)
    timeout10: ClientTimeout = ClientTimeout(total=10)
    headers: MutableMapping[str, Any] = {"X-Api-Key": api_key}
    if ping_uuid is not None:
        ping_verify_ssl: bool = ping_endpoint.startswith("https")
        ping_session: ClientSession = async_get_clientsession(hass, ping_verify_ssl)
        ping_url: str = f"{ping_endpoint}/{ping_uuid}"
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
            f"{site_root}/api/v1/checks/", headers=headers, timeout=timeout10
        )
    except (TimeoutError, ClientError) as e:
        _LOGGER.error(
            "Could Not Update Data. %s: %s",
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


def _clean_url(url: str) -> str:
    """Cleanup slashes from URL."""
    parsed: ParseResult = urlparse(url)

    if not parsed.scheme:
        parsed = urlparse("https://" + url)

    cleaned_path: str = re.sub(r"/+", "/", parsed.path)
    if cleaned_path != "/":
        cleaned_path = cleaned_path.rstrip("/")

    cleaned: ParseResult = parsed._replace(path=cleaned_path)
    return urlunparse(cleaned)


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
                user_input[CONF_SITE_ROOT] = DEFAULT_SITE_ROOT
                user_input[CONF_PING_ENDPOINT] = DEFAULT_PING_ENDPOINT
                user_input[CONF_SELF_HOSTED] = False
                valid: bool = await _test_credentials(
                    hass=self.hass,
                    api_key=user_input[CONF_API_KEY],
                    site_root=user_input[CONF_SITE_ROOT],
                    ping_endpoint=user_input[CONF_PING_ENDPOINT],
                    ping_uuid=user_input.get(CONF_PING_UUID),
                )
                if valid:
                    return self.async_create_entry(
                        title=user_input.get(CONF_PING_UUID, DOMAIN), data=user_input
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

        if user_input is not None and user_input.get(CONF_PING_UUID) is not None:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_PING_UUID, default=user_input.get(CONF_PING_UUID)): str,
                }
            )
        else:
            DATA_SCHEMA = DATA_SCHEMA.extend(
                {
                    vol.Optional(CONF_PING_UUID): str,
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
            user_input[CONF_SITE_ROOT] = _clean_url(user_input[CONF_SITE_ROOT])
            if user_input.get(CONF_PING_ENDPOINT) is None:
                user_input[CONF_PING_ENDPOINT] = f"{user_input.get(CONF_SITE_ROOT)}/ping"
            user_input[CONF_PING_ENDPOINT] = _clean_url(user_input[CONF_PING_ENDPOINT])
            valid: bool = await _test_credentials(
                hass=self.hass,
                api_key=self.initial_data[CONF_API_KEY],
                site_root=user_input[CONF_SITE_ROOT],
                ping_endpoint=user_input[CONF_PING_ENDPOINT],
                ping_uuid=self.initial_data.get(CONF_PING_UUID),
            )
            if valid:
                # merge data from initial config flow and this flow
                data: MutableMapping[str, Any] = {**self.initial_data, **user_input}
                return self.async_create_entry(
                    title=self.initial_data.get(CONF_PING_UUID, DOMAIN), data=data
                )
            self._errors["base"] = "auth_self"

        SELF_HOSTED_DATA_SCHEMA: vol.Schema = vol.Schema(
            {
                vol.Required(
                    CONF_SITE_ROOT,
                    default=user_input.get(CONF_SITE_ROOT, DEFAULT_SITE_ROOT)
                    if user_input is not None
                    else DEFAULT_SITE_ROOT,
                ): str,
                vol.Optional(
                    CONF_PING_ENDPOINT,
                    default=user_input.get(CONF_PING_ENDPOINT) if user_input is not None else None,
                ): str,
            }
        )

        return self.async_show_form(
            step_id="self_hosted",
            data_schema=SELF_HOSTED_DATA_SCHEMA,
            errors=self._errors,
        )

"""Config flow for HealthChecks.io integration."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, MutableMapping
import logging
import re
from typing import Any
from urllib.parse import ParseResult, urlparse, urlunparse

from aiohttp import ClientError, ClientSession, ClientTimeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
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
    INTEGRATION_NAME,
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


def _build_user_input_schema(
    user_input: MutableMapping[str, Any] | None,
    fallback: Mapping[str, Any] | None = None,
    reconf: bool = False,
) -> vol.Schema:
    if user_input is None:
        user_input = {}
    if fallback is None:
        fallback = {}
    if reconf:
        schema: vol.Schema = vol.Schema({})
    else:
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=user_input.get(CONF_API_KEY, fallback.get(CONF_API_KEY, "")),
                ): str,
            }
        )
    return schema.extend(
        {
            vol.Optional(
                CONF_PING_UUID,
                default=user_input.get(CONF_PING_UUID, fallback.get(CONF_PING_UUID, "")),
            ): str,
            vol.Optional(
                CONF_CREATE_BINARY_SENSOR,
                default=user_input.get(
                    CONF_CREATE_BINARY_SENSOR,
                    fallback.get(CONF_CREATE_BINARY_SENSOR, DEFAULT_CREATE_BINARY_SENSOR),
                ),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_CREATE_SENSOR,
                default=user_input.get(
                    CONF_CREATE_SENSOR, fallback.get(CONF_CREATE_SENSOR, DEFAULT_CREATE_SENSOR)
                ),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            vol.Optional(
                CONF_SELF_HOSTED,
                default=user_input.get(
                    CONF_SELF_HOSTED, fallback.get(CONF_SELF_HOSTED, DEFAULT_SELF_HOSTED)
                ),
            ): selector.BooleanSelector(selector.BooleanSelectorConfig()),
        }
    )


def _build_self_hosted_schema(
    user_input: MutableMapping[str, Any] | None,
    fallback: Mapping[str, Any] | None = None,
    reconf: bool = False,
) -> vol.Schema:
    if user_input is None:
        user_input = {}
    if fallback is None:
        fallback = {}

    return vol.Schema(
        {
            vol.Required(
                CONF_SITE_ROOT,
                default=user_input.get(
                    CONF_SITE_ROOT, fallback.get(CONF_SITE_ROOT, DEFAULT_SITE_ROOT)
                ),
            ): str,
            vol.Optional(
                CONF_PING_ENDPOINT,
                default=user_input.get(CONF_PING_ENDPOINT, fallback.get(CONF_PING_ENDPOINT, "")),
            ): str,
        }
    )


class HealthchecksioConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for HealthChecks.io integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors: dict[str, str] = {}
        self._initial_data: MutableMapping[str, Any] = {}
        self._reconfigure_entry: ConfigEntry | None = None
        self._prev_data: Mapping[str, Any] = {}

    async def async_step_user(
        self,
        user_input: MutableMapping[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """User Input step."""
        self._errors = errors or {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
            await self.async_set_unique_id(user_input.get(CONF_API_KEY))
            self._abort_if_unique_id_configured()

            if not user_input.get(CONF_CREATE_BINARY_SENSOR) and not user_input.get(
                CONF_CREATE_SENSOR
            ):
                self._errors["base"] = "need_a_sensor"
            elif user_input.get(CONF_SELF_HOSTED):
                # don't check yet, we need more info
                self._initial_data = user_input
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
                    return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)
                self._errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_input_schema(user_input=user_input),
            errors=self._errors,
        )

    async def async_step_self_hosted(
        self, user_input: MutableMapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step for a self-hosted instance."""
        self._errors = {}
        if user_input is not None:
            user_input[CONF_SITE_ROOT] = _clean_url(user_input[CONF_SITE_ROOT])
            if user_input.get(CONF_PING_ENDPOINT) is None:
                user_input[CONF_PING_ENDPOINT] = f"{user_input.get(CONF_SITE_ROOT)}/ping"
            user_input[CONF_PING_ENDPOINT] = _clean_url(user_input[CONF_PING_ENDPOINT])
            valid: bool = await _test_credentials(
                hass=self.hass,
                api_key=self._initial_data[CONF_API_KEY],
                site_root=user_input[CONF_SITE_ROOT],
                ping_endpoint=user_input[CONF_PING_ENDPOINT],
                ping_uuid=self._initial_data.get(CONF_PING_UUID),
            )
            if valid:
                # merge data from initial config flow and this flow
                data: MutableMapping[str, Any] = {**self._initial_data, **user_input}
                return self.async_create_entry(title=INTEGRATION_NAME, data=data)
            self._errors["base"] = "auth_self"

        return self.async_show_form(
            step_id="self_hosted",
            data_schema=_build_self_hosted_schema(user_input=user_input),
            errors=self._errors,
        )

    async def async_step_reconfigure(
        self, user_input: MutableMapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Config flow reconfigure step."""
        reconfigure_entry: ConfigEntry = self._get_reconfigure_entry()
        prev_data: Mapping[str, Any] = reconfigure_entry.data
        self._errors = {}
        if user_input is not None:
            # https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
            user_input[CONF_API_KEY] = prev_data[CONF_API_KEY]
            await self.async_set_unique_id(user_input.get(CONF_API_KEY))
            self._abort_if_unique_id_mismatch()

            if not user_input.get(CONF_CREATE_BINARY_SENSOR) and not user_input.get(
                CONF_CREATE_SENSOR
            ):
                self._errors["base"] = "need_a_sensor"
            elif user_input.get(CONF_SELF_HOSTED):
                # don't check yet, we need more info
                self._initial_data = user_input
                self._reconfigure_entry = reconfigure_entry
                self._prev_data = prev_data
                return await self.async_step_reconfigure_self_hosted()
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
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates=user_input,
                    )
                self._errors["base"] = "auth"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_user_input_schema(
                user_input=user_input, fallback=prev_data, reconf=True
            ),
            errors=self._errors,
            description_placeholders={
                "api_key": prev_data.get(CONF_API_KEY, ""),
            },
        )

    async def async_step_reconfigure_self_hosted(
        self, user_input: MutableMapping[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reconfigure step for a self-hosted instance."""
        self._errors = {}
        if user_input is not None:
            user_input[CONF_SITE_ROOT] = _clean_url(user_input[CONF_SITE_ROOT])
            if user_input.get(CONF_PING_ENDPOINT) is None:
                user_input[CONF_PING_ENDPOINT] = f"{user_input.get(CONF_SITE_ROOT)}/ping"
            user_input[CONF_PING_ENDPOINT] = _clean_url(user_input[CONF_PING_ENDPOINT])
            valid: bool = await _test_credentials(
                hass=self.hass,
                api_key=self._initial_data[CONF_API_KEY],
                site_root=user_input[CONF_SITE_ROOT],
                ping_endpoint=user_input[CONF_PING_ENDPOINT],
                ping_uuid=self._initial_data.get(CONF_PING_UUID),
            )
            if valid and self._reconfigure_entry is not None:
                # merge data from initial config flow and this flow
                data: MutableMapping[str, Any] = {**self._initial_data, **user_input}
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    data_updates=data,
                )
            self._errors["base"] = "auth_self"

        return self.async_show_form(
            step_id="reconfigure_self_hosted",
            data_schema=_build_self_hosted_schema(
                user_input=user_input, fallback=self._prev_data, reconf=True
            ),
            errors=self._errors,
        )

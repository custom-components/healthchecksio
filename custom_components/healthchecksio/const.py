"""Constants for HealthChecks.io integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

# Base component constants
DOMAIN = "healthchecksio"
INTEGRATION_NAME = "HealthChecks.io"
VERSION = "0.0.0"
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

ATTRIBUTION = "Data is provided by HealthChecks.io."

ATTR_ATTRIBUTION = "attribution"
ATTR_CHECKS = "checks"
ATTR_LAST_PING = "last_ping"
ATTR_NAME = "name"
ATTR_PING_URL = "ping_url"
ATTR_STATUS = "status"

CONF_API_KEY = "api_key"
CONF_PING_ID = "ping_id"
CONF_CREATE_BINARY_SENSOR = "create_binary_sensor"
CONF_CREATE_SENSOR = "create_sensor"
CONF_PING_ENDPOINT = "ping_endpoint"
CONF_SELF_HOSTED = "self_hosted"
CONF_PING_SITE_ROOT = "ping_site_root"
CONF_CHECK_SITE_ROOT = "check_site_root"

# Legacy
CONF_SITE_ROOT = "site_root"
CONF_CHECK = "check"

DATA_CLIENT = "client"
DATA_DATA = "data"

DEFAULT_CREATE_BINARY_SENSOR = True
DEFAULT_CREATE_SENSOR = False
DEFAULT_PING_ENDPOINT = "ping"
DEFAULT_SELF_HOSTED = False
DEFAULT_PING_SITE_ROOT = "https://hc-ping.com"
DEFAULT_CHECK_SITE_ROOT = "https://healthchecks.io/"

ICON_DEFAULT = "mdi:cloud"
ICON_DOWN = "mdi:cloud-off"
ICON_GRACE = "mdi:cloud-alert"
ICON_PAUSED = "mdi:cloud-question"
ICON_UP = "mdi:cloud-check-variant"

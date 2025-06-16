"""Constants for HealthChecks.io integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

# Base component constants
DOMAIN = "healthchecksio"
INTEGRATION_NAME = "HealthChecks.io"
VERSION = "v1.0.1"
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

ATTRIBUTION = "Data is provided by HealthChecks.io."

ATTR_CHECKS = "checks"
ATTR_LAST_PING = "last_ping"
ATTR_STATUS = "status"

CONF_PING_UUID = "ping_uuid"
CONF_CREATE_BINARY_SENSOR = "create_binary_sensor"
CONF_CREATE_SENSOR = "create_sensor"
CONF_PING_ENDPOINT = "ping_endpoint"
CONF_SELF_HOSTED = "self_hosted"
CONF_SITE_ROOT = "site_root"

DEFAULT_CREATE_BINARY_SENSOR = True
DEFAULT_CREATE_SENSOR = False
DEFAULT_SELF_HOSTED = False
DEFAULT_SITE_ROOT = "https://healthchecks.io"
DEFAULT_PING_ENDPOINT = "https://hc-ping.com"

ICON_DEFAULT = "mdi:cloud"
ICON_DOWN = "mdi:cloud-off"
ICON_GRACE = "mdi:cloud-alert"
ICON_PAUSED = "mdi:cloud-question"
ICON_UP = "mdi:cloud-check-variant"

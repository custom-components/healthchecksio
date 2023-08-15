"""Constants for blueprint."""
from homeassistant.const import Platform

# Base component constants
DOMAIN = "healthchecksio"
DOMAIN_DATA = f"{DOMAIN}_data"
INTEGRATION_NAME = "HealthChecks.io"
INTEGRATION_VERSION = "main"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]
REQUIRED_FILES = [
    "translations/en.json",
    "binary_sensor.py",
    "const.py",
    "config_flow.py",
    "manifest.json",
]
ISSUE_URL = "https://github.com/custom-components/healthchecksio/issues"
ATTRIBUTION = "Data from this is provided by HealthChecks.io."

OFFICIAL_SITE_ROOT = "https://healthchecks.io"

ATTR_ATTRIBUTION = "attribution"
ATTR_NAME = "name"
ATTR_LAST_PING = "last_ping"
ATTR_STATUS = "status"
ATTR_PING_URL = "ping_url"
ATTR_CHECKS = "checks"

CONF_API_KEY = "api_key"
CONF_CHECK = "check"
CONF_PING_ENDPOINT = "ping_endpoint"
CONF_SELF_HOSTED = "self_hosted"
CONF_SITE_ROOT = "site_root"
CONF_CREATE_SENSOR = "create_sensor"
CONF_CREATE_BINARY_SENSOR = "create_binary_sensor"

DATA_CLIENT = "client"
DATA_DATA = "data"

DEFAULT_PING_ENDPOINT = "ping"
DEFAULT_SELF_HOSTED = False
DEFAULT_SITE_ROOT = "https://checks.mydomain.com"
DEFAULT_CREATE_BINARY_SENSOR = True
DEFAULT_CREATE_SENSOR = False

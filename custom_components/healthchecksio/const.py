"""Constants for blueprint."""
# Base component constants
DOMAIN = "healthchecksio"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.2"
PLATFORMS = ["binary_sensor"]
REQUIRED_FILES = [
    ".translations/en.json",
    "binary_sensor.py",
    "const.py",
    "config_flow.py",
    "manifest.json",
]
ISSUE_URL = "https://github.com/custom-components/healthchecksio/issues"
ATTRIBUTION = "Data from this is provided by healthchecks.io."

BINARY_SENSOR_DEVICE_CLASS = "connectivity"

OFFICIAL_SITE_ROOT = "https://healthchecks.io"

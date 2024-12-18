"""Constants for blueprint."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "healthchecksio"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)
PLATFORMS = [
    Platform.BINARY_SENSOR,
]

ISSUE_URL = "https://github.com/custom-components/healthchecksio/issues"
ATTRIBUTION = "Data from this is provided by healthchecks.io."

BINARY_SENSOR_DEVICE_CLASS = "connectivity"

OFFICIAL_SITE_ROOT = "https://healthchecks.io"

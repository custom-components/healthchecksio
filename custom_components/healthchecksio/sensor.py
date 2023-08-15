"""Sensor platform for Healthchecksio."""
import logging

from homeassistant.components.sensor import SensorEntity

from .const import (
    ATTR_ATTRIBUTION,
    ATTR_CHECKS,
    ATTR_LAST_PING,
    ATTR_NAME,
    ATTR_PING_URL,
    ATTR_STATUS,
    ATTRIBUTION,
    DATA_CLIENT,
    DATA_DATA,
    DOMAIN,
    DOMAIN_DATA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    await hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
    checks = []
    for check in hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, []):
        check_data = {
            ATTR_NAME: check.get(ATTR_NAME),
            ATTR_LAST_PING: check.get(ATTR_LAST_PING),
            ATTR_STATUS: check.get(ATTR_STATUS),
            ATTR_PING_URL: check.get(ATTR_PING_URL),
        }
        checks.append(HealthchecksioSensor(hass, check_data, config_entry))
    async_add_devices(checks, True)


class HealthchecksioSensor(SensorEntity):
    """Healthchecksio Sensor class."""

    def __init__(self, hass, check_data, config_entry):
        self.hass = hass
        self.config_entry = config_entry
        self.check_data = check_data
        self._attr_name = None
        self._attr_unique_id = self.check_data.get(ATTR_PING_URL, "").split("/")[-1]
        self._attr_extra_state_attributes = {}
        self._attr_native_value = None
        self.check = {}

    async def async_update(self):
        """Update the Sensor."""
        await self.hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
        for check in (
            self.hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, [])
        ):
            if self._attr_unique_id == check.get(ATTR_PING_URL).split("/")[-1]:
                self.check = check
                break
        self._attr_name = self.check.get(ATTR_NAME)
        self._attr_native_value = self.check.get(ATTR_STATUS)
        if isinstance(self._attr_native_value, str):
            self._attr_native_value = self._attr_native_value.title()
        self._attr_extra_state_attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        self._attr_extra_state_attributes[ATTR_LAST_PING] = self.check.get(
            ATTR_LAST_PING
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "HealthChecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

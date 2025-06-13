"""Binary sensor platform for HealthChecks.io integration."""

from collections.abc import MutableMapping
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
    """Setup Binary Sensor platform."""
    await hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
    checks: list[HealthchecksioBinarySensor] = []
    for check in hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, []):
        check_data: MutableMapping[str, Any] = {
            ATTR_NAME: check.get(ATTR_NAME),
            ATTR_LAST_PING: check.get(ATTR_LAST_PING),
            ATTR_STATUS: check.get(ATTR_STATUS),
            ATTR_PING_URL: check.get(ATTR_PING_URL),
        }
        checks.append(HealthchecksioBinarySensor(hass, check_data, config_entry))
    async_add_devices(checks, True)


class HealthchecksioBinarySensor(BinarySensorEntity):
    """HealthChecks.io binary sensor class."""

    def __init__(self, hass, check_data, config_entry) -> None:
        """Initialize the binary sensor."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry
        self.check_data: MutableMapping[str, Any] = check_data
        self._attr_name: str | None = None
        self._attr_device_class: BinarySensorDeviceClass = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_unique_id: str = self.check_data.get(ATTR_PING_URL, "").split("/")[-1]
        self._attr_extra_state_attributes: MutableMapping[str, Any] = {}
        self._attr_is_on: bool | None = None
        self.check: MutableMapping[str, Any] = {}

    async def async_update(self) -> None:
        """Update the binary sensor."""
        await self.hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
        for check in self.hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, []):
            if self._attr_unique_id == check.get(ATTR_PING_URL).split("/")[-1]:
                self.check = check
                break
        self._attr_name = self.check.get(ATTR_NAME)
        self._attr_is_on = self.check.get(ATTR_STATUS) != "down"
        self._attr_extra_state_attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        self._attr_extra_state_attributes[ATTR_LAST_PING] = self.check.get(ATTR_LAST_PING)

    @property
    def device_info(self) -> MutableMapping[str, Any]:
        """Return the device info."""
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "HealthChecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

"""Sensor platform for HealthChecks.io integration."""

from collections.abc import MutableMapping
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    ICON_DEFAULT,
    ICON_DOWN,
    ICON_GRACE,
    ICON_PAUSED,
    ICON_UP,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup the sensor platform."""
    await hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
    checks: list[HealthchecksioSensor] = []
    for check in hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, []):
        check_data: MutableMapping[str, Any] = {
            ATTR_NAME: check.get(ATTR_NAME),
            ATTR_LAST_PING: check.get(ATTR_LAST_PING),
            ATTR_STATUS: check.get(ATTR_STATUS),
            ATTR_PING_URL: check.get(ATTR_PING_URL),
        }
        checks.append(HealthchecksioSensor(hass, check_data, config_entry))
    async_add_devices(checks, True)


class HealthchecksioSensor(SensorEntity):
    """HealthChecks.io Sensor class."""

    def __init__(
        self, hass: HomeAssistant, check_data: MutableMapping[str, Any], config_entry: ConfigEntry
    ) -> None:
        """Initialize the sensor platform."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry
        self.check_data: MutableMapping[str, Any] = check_data
        self._attr_name: str | None = None
        self._attr_unique_id: str = self.check_data.get(ATTR_PING_URL, "").split("/")[-1]
        self._attr_extra_state_attributes: MutableMapping[str, Any] = {}
        self._attr_native_value: Any | None = None
        self._attr_icon: str = ICON_DEFAULT
        self.check: MutableMapping[str, Any] = {}

    async def async_update(self) -> None:
        """Update the Sensor."""
        await self.hass.data[DOMAIN_DATA][DATA_CLIENT].update_data()
        for check in self.hass.data[DOMAIN_DATA].get(DATA_DATA, {}).get(ATTR_CHECKS, []):
            if self._attr_unique_id == check.get(ATTR_PING_URL).split("/")[-1]:
                self.check = check
                break
        self._attr_name = self.check.get(ATTR_NAME)
        self._attr_native_value = self.check.get(ATTR_STATUS)
        if isinstance(self._attr_native_value, str):
            if self._attr_native_value.lower() == "new":
                self._attr_icon = ICON_DEFAULT
            elif self._attr_native_value.lower() == "up":
                self._attr_icon = ICON_UP
            elif self._attr_native_value.lower() == "grace":
                self._attr_icon = ICON_GRACE
            elif self._attr_native_value.lower() == "down":
                self._attr_icon = ICON_DOWN
            elif self._attr_native_value.lower() == "paused":
                self._attr_icon = ICON_PAUSED
            else:
                self._attr_icon = ICON_DEFAULT
            self._attr_native_value = self._attr_native_value.title()
        else:
            self._attr_icon = ICON_DEFAULT
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

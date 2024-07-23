"""Binary sensor platform for Healthchecksio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.healthchecksio import LOGGER

from .const import ATTRIBUTION, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import HealthchecksioDataUpdateCoordinator


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    # Send update "signal" to the component
    coordinator: HealthchecksioDataUpdateCoordinator = config_entry.runtime_data
    async_add_devices(
        HealthchecksioBinarySensor(
            hass=hass,
            ping_url=check.get("ping_url"),
            coordinator=coordinator,
        )
        for check in coordinator.data.get("checks", [])
    )


class HealthchecksioBinarySensor(BinarySensorEntity, CoordinatorEntity):
    """Healthchecksio binary_sensor class."""

    coordinator: HealthchecksioDataUpdateCoordinator

    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        coordinator: HealthchecksioDataUpdateCoordinator,
        ping_url: str,
    ):
        super().__init__(coordinator)
        self.hass = hass
        self._ping_url = ping_url

        self._attr_unique_id = ping_url.split("/")[-1]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.coordinator.config_entry.entry_id)},
            "name": "Healthchecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

    def get_check(self) -> dict[str, Any]:
        """Get check data."""
        for check in self.coordinator.data.get("checks", []):
            if self._ping_url == check.get("ping_url"):
                return check
        return {}

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        check = self.get_check()
        return check.get("name")

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        check = self.get_check()
        LOGGER.debug("Check: %s", check)
        return check.get("status") != "down"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        check = self.get_check()
        return {"last_ping": check.get("last_ping")}

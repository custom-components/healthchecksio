"""Binary sensor platform for HealthChecks.io integration."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ATTRIBUTION,
    ATTR_LAST_PING,
    ATTR_NAME,
    ATTR_PING_URL,
    ATTR_STATUS,
    ATTRIBUTION,
    DOMAIN,
    ICON_DEFAULT,
    ICON_DOWN,
    ICON_GRACE,
    ICON_PAUSED,
    ICON_UP,
)
from .coordinator import HealthchecksioDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Setup Binary Sensor platform."""
    coordinator: HealthchecksioDataUpdateCoordinator = config_entry.runtime_data
    entities: list[HealthchecksioBinarySensor] = [
        HealthchecksioBinarySensor(
            hass=hass,
            ping_url=check.get(ATTR_PING_URL),
            coordinator=coordinator,
            config_entry=config_entry,
        )
        for check in coordinator.data.get("checks", [])
    ]
    async_add_entities(entities)


class HealthchecksioBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """HealthChecks.io binary sensor class."""

    def __init__(
        self,
        hass: HomeAssistant,
        ping_url: str,
        coordinator: HealthchecksioDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry
        self._attr_available = False
        self._ping_url: str = ping_url
        self._attr_name: str | None = None
        self._attr_device_class: BinarySensorDeviceClass = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_is_on: bool | None = None
        self._attr_icon: str = ICON_DEFAULT
        self._attr_unique_id: str = ping_url.split("/", maxsplit=1)[-1]

        self._attr_device_info: DeviceInfo | None = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "HealthChecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the binary sensor."""
        checks = self.coordinator.data.get("checks", [])
        check = None
        for chk in checks:
            if chk.get(ATTR_PING_URL, "").split("/", maxsplit=1)[-1] == self._attr_unique_id:
                check = chk
                break
        if not check:
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        self._attr_name = check.get(ATTR_NAME)
        self._attr_is_on = check.get(ATTR_STATUS) != "down"
        self._attr_extra_state_attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        self._attr_extra_state_attributes[ATTR_STATUS] = check.get(ATTR_STATUS)
        self._attr_extra_state_attributes[ATTR_LAST_PING] = check.get(ATTR_LAST_PING)
        if isinstance(check.get(ATTR_STATUS), str):
            value_lower = check.get(ATTR_STATUS).lower()
            icon_map = {
                "new": ICON_DEFAULT,
                "up": ICON_UP,
                "grace": ICON_GRACE,
                "down": ICON_DOWN,
                "paused": ICON_PAUSED,
            }
            self._attr_icon = icon_map.get(value_lower, ICON_DEFAULT)
        else:
            self._attr_icon = ICON_DEFAULT

        self.async_write_ha_state()

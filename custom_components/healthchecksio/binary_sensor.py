"""Binary sensor platform for HealthChecks.io integration."""

from collections.abc import MutableMapping
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_PING,
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

PLATFORM = Platform.BINARY_SENSOR
ENTITY_ID_FORMAT = PLATFORM + ".{}"


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
            ping_uuid=uuid,
            name=check.get(ATTR_NAME),
            coordinator=coordinator,
        )
        for uuid, check in coordinator.data.items()
    ]
    async_add_entities(entities)


class HealthchecksioBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """HealthChecks.io binary sensor class."""

    def __init__(
        self,
        hass: HomeAssistant,
        ping_uuid: str,
        name: str,
        coordinator: HealthchecksioDataUpdateCoordinator,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.hass: HomeAssistant = hass
        self._attr_available = False
        self._ping_uuid: str = ping_uuid
        self._attr_name: str = name
        self._attr_device_class: BinarySensorDeviceClass = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_is_on: bool | None = None
        self._attr_icon: str = ICON_DEFAULT
        self._attr_unique_id: str = f"binary_sensor_{ping_uuid}"

        registry = er.async_get(self.hass)
        current_entity_id = registry.async_get_entity_id(PLATFORM, DOMAIN, self._attr_unique_id)
        if current_entity_id is not None:
            self.entity_id = current_entity_id
        else:
            self.entity_id = generate_entity_id(
                ENTITY_ID_FORMAT, f"healthchecksio_{name}", hass=self.hass
            )

        self._attr_device_info: DeviceInfo | None = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "HealthChecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

    async def async_added_to_hass(self) -> None:
        """Run once integration has been added to HA."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the binary sensor."""
        _LOGGER.debug("Updating: %s", self._attr_name)
        checks: MutableMapping[str, Any] = self.coordinator.data
        # _LOGGER.debug("checks: %s", checks)
        check: MutableMapping[str, Any] | None = checks.get(self._ping_uuid)
        # _LOGGER.debug("check: %s", check)
        if not check:
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_available = True
        self._attr_name = check.get(ATTR_NAME) or self._attr_name
        if check.get(ATTR_STATUS) == "paused":
            self._attr_is_on = None
        else:
            self._attr_is_on = check.get(ATTR_STATUS) != "down"
        self._attr_extra_state_attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        self._attr_extra_state_attributes[ATTR_STATUS] = check.get(ATTR_STATUS)
        self._attr_extra_state_attributes[ATTR_LAST_PING] = check.get(ATTR_LAST_PING)
        value: str | None = check.get(ATTR_STATUS)
        if isinstance(value, str):
            value_lower: str = value.lower()
            icon_map: MutableMapping[str, str] = {
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

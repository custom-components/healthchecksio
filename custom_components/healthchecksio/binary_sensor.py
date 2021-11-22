"""Binary sensor platform for Healthchecksio."""
try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
except ImportError:
    from homeassistant.components.binary_sensor import (
        BinarySensorDevice as BinarySensorEntity,
    )

from .const import ATTRIBUTION, BINARY_SENSOR_DEVICE_CLASS, DOMAIN_DATA, DOMAIN


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    # Send update "signal" to the component
    await hass.data[DOMAIN_DATA]["client"].update_data()
    checks = []
    for check in hass.data[DOMAIN_DATA].get("data", {}).get("checks", []):
        check_data = {
            "name": check.get("name"),
            "last_ping": check.get("last_ping"),
            "status": check.get("status"),
            "ping_url": check.get("ping_url"),
        }
        checks.append(HealthchecksioBinarySensor(hass, check_data, config_entry))
    async_add_devices(checks, True)


class HealthchecksioBinarySensor(BinarySensorEntity):
    """Healthchecksio binary_sensor class."""

    def __init__(self, hass, config, config_entry):
        self.hass = hass
        self.attr = {}
        self.config_entry = config_entry
        self._status = None
        self.config = config

    async def async_update(self):
        """Update the binary_sensor."""
        # Send update "signal" to the component
        await self.hass.data[DOMAIN_DATA]["client"].update_data()

        # Check the data and update the value.
        for check in self.hass.data[DOMAIN_DATA]["data"]["checks"]:
            if self.unique_id == check.get("ping_url").split("/")[-1]:
                self.config = check
                break
        self._status = self.config.get("status") == "up"

        # Set/update attributes
        self.attr["attribution"] = ATTRIBUTION
        self.attr["last_ping"] = self.config.get("last_ping")

    @property
    def unique_id(self):
        """Return a unique ID to use for this binary_sensor."""
        return self.config.get("ping_url").split("/")[-1]

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": "Healthchecks.io",
            "manufacturer": "SIA Monkey See Monkey Do",
        }

    @property
    def name(self):
        """Return the name of the binary_sensor."""
        return self.config.get("name")

    @property
    def device_class(self):
        """Return the class of this binary_sensor."""
        return BINARY_SENSOR_DEVICE_CLASS

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        return self._status

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self.attr

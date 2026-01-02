"""Sensory PGE Dynamic Energy."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime
from .const import DOMAIN, CONF_MARGIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    margin = entry.data.get(CONF_MARGIN, 0.0)
    
    sensors = []
    # Sensory dla każdej godziny
    for hour in range(24):
        sensors.append(PGEPriceSensor(coordinator, hour, margin))
    # Sensor aktualny
    sensors.append(PGECurrentPriceSensor(coordinator, margin))
    
    async_add_entities(sensors)

class PGEPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, hour, margin):
        super().__init__(coordinator)
        self.hour = hour
        self.margin = margin
        self._attr_name = f"PGE Cena {hour:02d}:00"
        self._attr_unique_id = f"{DOMAIN}_h_{hour}"
        self._attr_native_unit_of_measurement = "PLN/kWh"

    @property
    def native_value(self):
        prices = self.coordinator.data.get("hourly", {})
        price = prices.get(self.hour)
        if price is not None:
            return round((price + self.margin) * 1.23, 4)
        return None

class PGECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, margin):
        super().__init__(coordinator)
        self.margin = margin
        self._attr_name = "PGE Cena Aktualna"
        self._attr_unique_id = f"{DOMAIN}_current"
        self._attr_native_unit_of_measurement = "PLN/kWh"

    @property
    def native_value(self):
        hour = datetime.now().hour
        prices = self.coordinator.data.get("hourly", {})
        price = prices.get(hour)
        if price is not None:
            return round((price + self.margin) * 1.23, 4)
        return None
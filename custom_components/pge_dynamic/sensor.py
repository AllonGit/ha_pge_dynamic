"""Definicja sensorów dla PGE Dynamic Energy."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime
from .const import DOMAIN, CONF_TARIFF

async def async_setup_entry(hass, entry, async_add_entities):
    """Konfiguracja platformy sensorów."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    tariff = entry.data.get(CONF_TARIFF, "G1x")
    
    sensors = []
    # 24 sensory godzinne (00:00 do 23:00)
    for hour in range(24):
        sensors.append(PGEPriceSensor(coordinator, hour))
    
    # Główny sensor aktualnej ceny
    sensors.append(PGECurrentPriceSensor(coordinator, tariff))
    
    async_add_entities(sensors)

class PGEPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor ceny dla konkretnej godziny."""
    
    def __init__(self, coordinator, hour):
        super().__init__(coordinator)
        self.hour = hour
        self._attr_unique_id = f"{DOMAIN}_h_{hour}"
        self._attr_name = f"PGE Cena {hour:02d}:00"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:cash-clock"

    @property
    def native_value(self):
        prices = self.coordinator.data.get("hourly", {})
        val = prices.get(self.hour)
        return round(val, 4) if val is not None else None

class PGECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor ceny dla aktualnej godziny."""
    
    def __init__(self, coordinator, tariff):
        super().__init__(coordinator)
        self.tariff = tariff
        self._attr_unique_id = f"{DOMAIN}_current"
        self._attr_name = "PGE Cena Aktualna"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:lightning-bolt"

    @property
    def native_value(self):
        hour = datetime.now().hour
        prices = self.coordinator.data.get("hourly", {})
        val = prices.get(hour)
        return round(val, 4) if val is not None else None

    @property
    def extra_state_attributes(self):
        return {"wybrana_taryfa": self.tariff}
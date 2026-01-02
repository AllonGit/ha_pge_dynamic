"""Sensory PGE Dynamic Energy - Wersja Naprawiona."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Konfiguracja sensorów po dodaniu integracji."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    # Tworzymy 24 sensory godzinne
    for hour in range(24):
        # Przekazujemy tylko 2 argumenty: coordinator i hour
        sensors.append(PGEPriceSensor(coordinator, hour))
    
    # Dodajemy sensor ceny aktualnej
    sensors.append(PGECurrentPriceSensor(coordinator))
    
    async_add_entities(sensors)

class PGEPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor dla konkretnej godziny."""
    def __init__(self, coordinator, hour):
        super().__init__(coordinator)
        self.hour = hour
        self._attr_name = f"PGE Cena {hour:02d}:00"
        self._attr_unique_id = f"{DOMAIN}_h_{hour}"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Pobieranie wartości z koordynatora."""
        prices = self.coordinator.data.get("hourly", {})
        price = prices.get(self.hour)
        if price is not None:
            return round(float(price), 4)
        return None

class PGECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor dla aktualnej godziny."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "PGE Cena Aktualna"
        self._attr_unique_id = f"{DOMAIN}_current"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Pobieranie ceny dla bieżącej godziny."""
        hour = datetime.now().hour
        prices = self.coordinator.data.get("hourly", {})
        price = prices.get(hour)
        if price is not None:
            return round(float(price), 4)
        return None
"""Sensory PGE Dynamic Energy - Wersja Cena Netto."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Konfiguracja sensorów po dodaniu integracji."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    # 24 sensory godzinne
    for hour in range(24):
        sensors.append(PGEPriceSensor(coordinator, hour))
    
    # Sensor ceny aktualnej
    sensors.append(PGECurrentPriceSensor(coordinator))
    
    async_add_entities(sensors)

class PGEPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor dla konkretnej godziny (Netto)."""
    def __init__(self, coordinator, hour):
        super().__init__(coordinator)
        self.hour = hour
        self._attr_name = f"PGE Cena {hour:02d}:00"
        self._attr_unique_id = f"{DOMAIN}_h_{hour}"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:lightning-bolt"

    @property
    def native_value(self):
        """Pobieranie czystej wartości z koordynatora."""
        prices = self.coordinator.data.get("hourly", {})
        price_netto = prices.get(self.hour)
        if price_netto is not None:
            # Zwracamy czystą cenę (PLN/kWh) bez mnożnika VAT
            return round(float(price_netto), 4)
        return None

class PGECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor dla aktualnej godziny (Netto)."""
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "PGE Cena Aktualna"
        self._attr_unique_id = f"{DOMAIN}_current"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_icon = "mdi:lightning-bolt-circle"

    @property
    def native_value(self):
        """Pobieranie aktualnej ceny netto."""
        hour = datetime.now().hour
        prices = self.coordinator.data.get("hourly", {})
        price_netto = prices.get(hour)
        if price_netto is not None:
            return round(float(price_netto), 4)
        return None
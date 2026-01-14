# custom_components/pge_dynamic/sensor.py
"""Definicje sensorów dla integracji PGE Dynamic Energy."""
from homeassistant.components.sensor import (
    SensorEntity, SensorDeviceClass, SensorStateClass, RestoreSensor
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from datetime import datetime, date
import logging
from statistics import mean

from .const import (
    DOMAIN, CONF_OPERATION_MODE, CONF_ENERGY_SENSOR,
    CONF_G12_SETTINGS, CONF_G12W_SETTINGS, MODE_COMPARISON,
    CONF_PRICE_PEAK, CONF_PRICE_OFFPEAK, CONF_HOURS_PEAK
)
from .coordinator import PGEDataCoordinator
from .helpers import parse_hour_ranges, is_holiday

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Konfiguruje sensory na podstawie wpisu konfiguracy-jnego."""
    coordinator: PGEDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    # Sensory podstawowe
    sensors.extend([PGEPriceSensor(coordinator, hour, "today") for hour in range(24)])
    sensors.append(PGECurrentPriceSensor(coordinator))
    sensors.extend([PGEPriceSensor(coordinator, hour, "tomorrow") for hour in range(24)])
    sensors.append(PGEMinMaxPriceSensor(coordinator, "today", "min"))
    sensors.append(PGEMinMaxPriceSensor(coordinator, "today", "max"))
    sensors.append(PGEMinMaxPriceSensor(coordinator, "tomorrow", "min"))
    sensors.append(PGEMinMaxPriceSensor(coordinator, "tomorrow", "max"))

    # Sensory trybu porównawczego
    if entry.data.get(CONF_OPERATION_MODE) == MODE_COMPARISON:
        energy_sensor_id = entry.data.get(CONF_ENERGY_SENSOR)
        g12_settings = entry.data.get(CONF_G12_SETTINGS, {})
        g12w_settings = entry.data.get(CONF_G12W_SETTINGS, {})

        if energy_sensor_id:
            # Poziom 1: Koszty dzienne i miesięczne
            for tariff in ["dynamic", "g12", "g12w"]:
                settings = g12_settings if tariff == "g12" else g12w_settings if tariff == "g12w" else {}
                daily_cost_sensor = PGEDailyCostSensor(coordinator, tariff, energy_sensor_id, settings)
                monthly_cost_sensor = PGEMonthlyCostSensor(daily_cost_sensor, tariff)
                sensors.extend([daily_cost_sensor, monthly_cost_sensor])
        else:
            # Poziom 2: Porównanie średnich cen
            sensors.append(PGEPriceComparisonSensor(coordinator, g12_settings, g12w_settings))

    async_add_entities(sensors, update_before_add=True)


# --- Sensory Podstawowe ---
class PGEPriceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, hour, day_type):
        super().__init__(coordinator)
        self._hour, self._day_type = hour, day_type
        day_name = "Jutro" if day_type == "tomorrow" else "Dziś"
        self._attr_name = f"Cena {day_name} {self._hour:02d}:00"
        self._attr_unique_id = f"{DOMAIN}_{day_type}_h_{self._hour}"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        prices = self.coordinator.data.get(self._day_type, {})
        return prices.get(self._hour)

class PGECurrentPriceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cena Aktualna"
        self._attr_unique_id = f"{DOMAIN}_current"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        prices = self.coordinator.data.get("today", {})
        return prices.get(dt_util.now().hour)

class PGEMinMaxPriceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator, day_type, mode):
        super().__init__(coordinator)
        self._day_type, self._mode = day_type, mode
        day_name = "Jutro" if day_type == "tomorrow" else "Dziś"
        mode_name = "Minimalna" if mode == "min" else "Maksymalna"
        self._attr_name = f"Cena {mode_name} {day_name}"
        self._attr_unique_id = f"{DOMAIN}_{mode}_{day_type}"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        prices = self.coordinator.data.get(self._day_type, {})
        if not prices: return None
        return min(prices.values()) if self._mode == "min" else max(prices.values())

    @property
    def extra_state_attributes(self):
        prices = self.coordinator.data.get(self._day_type, {})
        if not prices or (value := self.native_value) is None: return None
        hours = [f"{h:02d}:00" for h, p in prices.items() if p == value]
        return {"hour": hours[0]} if len(hours) == 1 else {"hours": hours}

# --- Sensory Trybu Porównawczego ---
class PGEDailyCostSensor(CoordinatorEntity, RestoreSensor):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    def __init__(self, coordinator, tariff_type, energy_sensor_id, config):
        super().__init__(coordinator)
        self.tariff_type, self.energy_sensor_id, self.config = tariff_type, energy_sensor_id, config
        self._attr_name = f"Koszt Dzienny ({tariff_type})"
        self._attr_unique_id = f"{DOMAIN}_daily_cost_{tariff_type}"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._last_energy_reading, self._native_value = None, 0.0

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None: self._native_value = float(last_state.state)
        if (last_energy_state := self.hass.states.get(self.energy_sensor_id)) and last_energy_state.state not in ("unknown", "unavailable"): self._last_energy_reading = float(last_energy_state.state)
        self.async_on_remove(async_track_state_change_event(self.hass, [self.energy_sensor_id], self._handle_energy_change))
        self.async_on_remove(async_track_time_change(self.hass, self._midnight_reset, hour=0, minute=0, second=1))

    @callback
    def _midnight_reset(self, now):
        self._native_value = 0.0
        self.async_write_ha_state()

    @callback
    def _handle_energy_change(self, event):
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"): return
        current_energy = float(new_state.state)
        if self._last_energy_reading is None or current_energy < self._last_energy_reading:
            self._last_energy_reading = current_energy
            return
        energy_delta = current_energy - self._last_energy_reading
        if energy_delta > 0 and (current_price := self._get_current_price_for_tariff()) is not None:
            self._native_value += energy_delta * current_price
            self.async_write_ha_state()
        self._last_energy_reading = current_energy

    def _get_current_price_for_tariff(self):
        now = dt_util.now()
        if self.tariff_type == "dynamic": return self.coordinator.data.get("today", {}).get(now.hour)
        is_weekend, is_holiday_today = now.weekday() >= 5, is_holiday(now.date())
        if self.tariff_type == "g12w" and (is_weekend or is_holiday_today): return self.config.get(CONF_PRICE_OFFPEAK)
        peak_hours = parse_hour_ranges(self.config.get(CONF_HOURS_PEAK, ""))
        return self.config.get(CONF_PRICE_PEAK) if now.hour in peak_hours else self.config.get(CONF_PRICE_OFFPEAK)

    @property
    def native_value(self): return round(self._native_value, 2)

class PGEMonthlyCostSensor(RestoreSensor, SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    def __init__(self, daily_cost_sensor: PGEDailyCostSensor, tariff_type: str):
        self._daily_sensor_id = daily_cost_sensor.entity_id
        self._attr_name = f"Koszt Miesięczny ({tariff_type})"
        self._attr_unique_id = f"{DOMAIN}_monthly_cost_{tariff_type}"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._native_value, self._daily_value = 0.0, 0.0

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None: self._native_value = float(last_state.state)
        self.async_on_remove(async_track_state_change_event(self.hass, [self._daily_sensor_id], self._handle_daily_cost_change))
        self.async_on_remove(async_track_time_change(self.hass, self._monthly_reset, hour=0, minute=0, second=2))

    @callback
    def _monthly_reset(self, now: datetime):
        if now.day == 1: self._native_value = 0.0; self.async_write_ha_state()

    @callback
    def _handle_daily_cost_change(self, event):
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"): return
        current_daily_cost = float(new_state.state)
        if current_daily_cost < self._daily_value: self._daily_value = 0.0 # Reset dzienny
        cost_increase = current_daily_cost - self._daily_value
        if cost_increase > 0: self._native_value += cost_increase; self.async_write_ha_state()
        self._daily_value = current_daily_cost

    @property
    def native_value(self): return round(self._native_value, 2)

class PGEPriceComparisonSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:compare-horizontal"
    def __init__(self, coordinator, g12_config, g12w_config):
        super().__init__(coordinator)
        self.g12_config, self.g12w_config = g12_config, g12w_config
        self._attr_name = "Porównanie Taryf"
        self._attr_unique_id = f"{DOMAIN}_tariff_comparison"
        self._attr_unit_of_measurement = "%"

    def _calculate_average_price(self, tariff_type: str, day: date):
        if tariff_type == "dynamic":
            prices = self.coordinator.data.get("today", {}).values()
            return mean(prices) if prices else None
        config = self.g12_config if tariff_type == "g12" else self.g12w_config
        price_peak, price_offpeak = config.get(CONF_PRICE_PEAK), config.get(CONF_PRICE_OFFPEAK)
        if price_peak is None or price_offpeak is None: return None
        if tariff_type == "g12w" and (day.weekday() >= 5 or is_holiday(day)): return price_offpeak
        peak_hours = parse_hour_ranges(config.get(CONF_HOURS_PEAK, ""))
        num_peak_hours, num_offpeak_hours = len(peak_hours), 24 - len(peak_hours)
        return ((num_peak_hours * price_peak) + (num_offpeak_hours * price_offpeak)) / 24

    @property
    def native_value(self):
        today = dt_util.now().date()
        avg_dynamic = self._calculate_average_price("dynamic", today)
        avg_g12 = self._calculate_average_price("g12", today)
        if avg_dynamic is None or avg_g12 is None or avg_g12 == 0: return None
        return round(((avg_g12 - avg_dynamic) / avg_g12) * 100, 2)

    @property
    def extra_state_attributes(self):
        today = dt_util.now().date()
        avg_dynamic = self._calculate_average_price("dynamic", today)
        avg_g12 = self._calculate_average_price("g12", today)
        avg_g12w = self._calculate_average_price("g12w", today)
        return {
            "srednia_cena_dynamiczna": round(avg_dynamic, 4) if avg_dynamic is not None else None,
            "srednia_cena_g12": round(avg_g12, 4) if avg_g12 is not None else None,
            "srednia_cena_g12w": round(avg_g12w, 4) if avg_g12w is not None else None
        }

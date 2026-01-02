import datetime
import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    marza = entry.data.get("marza", 0.099)
    
    async def async_get_pge_data():
        today = datetime.date.today().isoformat()
        # Twój sprawdzony URL z Node-RED
        url = f"https://datahub.gkpge.pl/api/tge/quote?source=TGE&contract=Fix_1&date_from={today} 00:00:00&date_to={today} 23:59:59&limit=100"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    res = await response.json()
                    data = res.get("data", [])
                    
                    prices = [0.0] * 24
                    for item in data:
                        dt_str = item.get("date_time", "")
                        # Wyciąganie godziny z formatu PGE
                        hour = int(dt_str.split(" ")[1].split(":")[0])
                        p_raw = next(a['value'] for a in item['attributes'] if a['name'] == 'price')
                        # Obliczenie ceny brutto (Twoja logika)
                        prices[hour] = round((float(p_raw)/1000 + marza) * 1.23, 4)
                    return prices
        except Exception as e:
            raise UpdateFailed(f"Błąd połączenia z PGE DataHub: {e}")

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name="pge_dynamic_prices",
        update_method=async_get_pge_data,
        update_interval=datetime.timedelta(minutes=15)
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    # 24 sensory godzinne
    for i in range(24):
        entities.append(PGEPriceSensor(coordinator, i))
    # Sensor Min i Max
    entities.append(PGEMinMaxSensor(coordinator, "min"))
    entities.append(PGEMinMaxSensor(coordinator, "max"))
    
    async_add_entities(entities)

class PGEPriceSensor(SensorEntity):
    """Sensor dla konkretnej godziny."""
    def __init__(self, coordinator, hour):
        self.coordinator = coordinator
        self._hour = hour
        self._attr_name = f"PGE Cena {hour:02d}:00"
        self._attr_unique_id = f"pge_price_h_{hour}"
        self._attr_native_unit_of_measurement = "zł/kWh"
        self._attr_device_class = "monetary"

    @property
    def native_value(self):
        return self.coordinator.data[self._hour]

class PGEMinMaxSensor(SensorEntity):
    """Sensor ceny minimalnej/maksymalnej."""
    def __init__(self, coordinator, mode):
        self.coordinator = coordinator
        self._mode = mode
        self._attr_name = f"PGE Cena {'Minimalna' if mode == 'min' else 'Maksymalna'}"
        self._attr_unique_id = f"pge_price_{mode}"
        self._attr_native_unit_of_measurement = "zł/kWh"

    @property
    def native_value(self):
        return min(self.coordinator.data) if self._mode == "min" else max(self.coordinator.data)
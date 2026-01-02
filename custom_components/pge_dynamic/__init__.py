import logging
import async_timeout
import aiohttp
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import Platform
from .const import DOMAIN, API_URL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = PGEDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class PGEDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # Twoja dokładna logika z Node-RED
        url = f"{API_URL}?source=TGE&contract=Fix_1&date_from={today} 00:00:00&date_to={today} 23:59:59&limit=100"
        
        try:
            async with async_timeout.timeout(30):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            _LOGGER.error("PGE API zwróciło status: %s", response.status)
                            raise UpdateFailed(f"Błąd API: {response.status}")
                        data = await response.json()
            
            # Debugowanie - zapisze w logach co przyszło z PGE
            _LOGGER.debug("Otrzymane dane z PGE: %s", data)
            
            results = data if isinstance(data, list) else data.get("quotes", [])
            if not results:
                _LOGGER.warning("API PGE nie zwróciło żadnych cen na dziś (%s)", today)
                return {"hourly": {}}

            prices = {}
            for item in results:
                dt_str = item.get("date")
                price_val = item.get("price")
                if dt_str and price_val is not None:
                    # Wyciąganie godziny z formatu "YYYY-MM-DD HH:MM:SS"
                    hour = int(dt_str.split(" ")[1].split(":")[0])
                    prices[hour] = float(price_val) / 1000.0
            return {"hourly": prices}
            
        except Exception as err:
            _LOGGER.error("Błąd podczas pobierania danych PGE: %s", err)
            raise UpdateFailed(f"Błąd połączenia: {err}")
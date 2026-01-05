"""Inicjalizacja integracji PGE Dynamic Energy."""
import logging
import async_timeout
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import Platform
from .const import DOMAIN, API_URL, UPDATE_INTERVAL, CONF_TARIFF

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ustawienie wpisu konfiguracyjnego."""
    coordinator = PGEDataCoordinator(hass, entry)
    
    # Pierwsze pobranie danych
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Odładowanie integracji."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class PGEDataCoordinator(DataUpdateCoordinator):
    """Klasa zarządzająca pobieraniem danych z PGE."""

    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.entry = entry

    async def _async_update_data(self):
        """Pobieranie danych - logika z Twojego download_data.py."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # Budowanie URL z datami
        url = f"{API_URL}?source=TGE&contract=Fix_1&date_from={today} 00:00:00&date_to={today} 23:59:59&limit=100"
        
        # Nagłówki
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            # Używamy sesji HA
            session = async_get_clientsession(self.hass)
            
            async with async_timeout.timeout(30):
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Błąd API PGE: {response.status}")
                    data = await response.json()

            # Logika przetwarzania
            processed_data = {}
            for item in data:
                try:
                    dt_str = item.get('date_time')
                    if not dt_str:
                        continue
                        
                    # Wyciąganie godziny
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    hour = dt.hour
                    
                    # Wyciąganie ceny z atrybutów
                    attributes = {attr['name']: attr['value'] for attr in item.get('attributes', [])}
                    price_mwh = float(attributes.get('price', 0))
                    
                    # Konwersja na kWh (Twoja logika: / 1000)
                    processed_data[hour] = price_mwh / 1000.0
                    
                except (ValueError, KeyError) as e:
                    _LOGGER.warning("Błąd przetwarzania wiersza danych: %s", e)
                    continue
            
            if not processed_data:
                _LOGGER.warning("Pobrano dane z API, ale słownik cen jest pusty.")

            return {"hourly": processed_data}

        except Exception as err:
            raise UpdateFailed(f"Błąd połączenia: {err}")
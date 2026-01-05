import logging
import async_timeout
import aiohttp
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import Platform
from .const import DOMAIN, API_URL, UPDATE_INTERVAL, CONF_TARIFF  # Dodaj CONF_TARIFF do importu

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja integracji po dodaniu przez interfejs."""
    # Wyciągamy wybraną taryfę z konfiguracji (na razie leży nieużywana)
    tariff = entry.data.get(CONF_TARIFF, "G1x")
    _LOGGER.debug("Uruchomiono PGE Dynamic z wybraną taryfą: %s", tariff)

    coordinator = PGEDataCoordinator(hass, entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usunięcie integracji."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class PGEDataCoordinator(DataUpdateCoordinator):
    """Koordynator pobierający dane z PGE DataHub."""

    def __init__(self, hass, entry):
        super().__init__(
            hass, 
            _LOGGER, 
            name=DOMAIN, 
            update_interval=UPDATE_INTERVAL
        )
        self.entry = entry # Zapisujemy entry, żeby mieć dostęp do taryfy w przyszłości

    async def _async_update_data(self):
        """Pobieranie i procesowanie danych z API PGE."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        url = f"{API_URL}?source=TGE&contract=Fix_1&date_from={today} 00:00:00&date_to={today} 23:59:59&limit=100"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            async with async_timeout.timeout(20):
                # Tutaj mała uwaga: lepiej użyć hass.helpers.aiohttp_client.async_get_clientsession(self.hass)
                # zamiast tworzyć nową sesję za każdym razem, ale Twój kod też zadziała.
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            _LOGGER.error("PGE API Error: %s", response.status)
                            raise UpdateFailed(f"Status błędu API: {response.status}")
                        
                        data = await response.json()

            prices = {}
            for item in data:
                try:
                    dt_str = item.get('date_time')
                    if not dt_str:
                        continue
                    
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    hour = dt.hour
                    
                    attributes = {attr['name']: attr['value'] for attr in item.get('attributes', [])}
                    price_mwh = float(attributes.get('price', 0))
                    
                    # Tutaj w przyszłości sprawdzisz self.entry.data.get(CONF_TARIFF)
                    # i np. doliczysz inne opłaty dla C1x
                    prices[hour] = price_mwh / 1000.0
                    
                except (KeyError, ValueError, TypeError) as e:
                    _LOGGER.debug("Pominięto niepełny wpis: %s", e)
                    continue

            if not prices:
                _LOGGER.warning("Brak aktualnych cen w PGE DataHub na dzień %s", today)
                if self.data:
                    return self.data
                raise UpdateFailed("Nie otrzymano żadnych danych cenowych.")

            _LOGGER.info("Pomyślnie pobrano %s cen z PGE DataHub", len(prices))
            return {"hourly": prices}

        except Exception as err:
            _LOGGER.error("Błąd krytyczny podczas pobierania danych PGE: %s", err)
            raise UpdateFailed(f"Błąd połączenia: {err}")
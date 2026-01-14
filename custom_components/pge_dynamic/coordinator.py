# custom_components/pge_dynamic/coordinator.py
"""Koordynator danych dla integracji PGE Dynamic Energy."""
import logging
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PGEApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class PGEDataCoordinator(DataUpdateCoordinator):
    """Zarządza pobieraniem i przetwarzaniem danych z API PGE."""

    def __init__(self, hass):
        """Inicjalizacja koordynatora."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        self.api_client = PGEApiClient(async_get_clientsession(hass))
        self._last_successful_data = None

    async def _async_update_data(self):
        """Główna metoda pobierania i przetwarzania danych."""
        now = datetime.now()
        yesterday = (now - timedelta(days=1)).date()
        today = now.date()

        # Pobieramy ceny na dziś (pytając o wczoraj)
        prices_today_raw = await self.api_client.async_get_prices(yesterday)

        # Zawsze czyścimy dane na jutro, aby uniknąć przestarzałych prognoz
        prices_tomorrow_raw = None
        if now.hour >= 14:
            prices_tomorrow_raw = await self.api_client.async_get_prices(today)

        # Jeśli API zawiedzie, a nie mamy żadnych danych w pamięci, rzuć błąd
        if prices_today_raw is None and (self._last_successful_data is None or not self._last_successful_data.get("today")):
            raise UpdateFailed("Nie udało się pobrać danych cenowych na dziś i brak danych z poprzedniej sesji.")

        # Użyj starych danych, jeśli nowe zapytanie zawiodło
        processed_today = self._parse_prices(prices_today_raw) if prices_today_raw else self._last_successful_data.get("today", {})
        processed_tomorrow = self._parse_prices(prices_tomorrow_raw) if prices_tomorrow_raw else {} # Zawsze zaczynaj od pustych danych na jutro

        processed_data = {
            "today": processed_today,
            "tomorrow": processed_tomorrow,
        }

        # Jeśli dzisiejsze ceny zostały pomyślnie pobrane, aktualizujemy cache
        if prices_today_raw:
            self._last_successful_data = processed_data

        return processed_data

    def _parse_prices(self, raw_data):
        """Przetwarza surowe dane z API na słownik cen godzinowych."""
        prices = {}
        if not raw_data:
            return prices

        for item in raw_data:
            try:
                dt = datetime.strptime(item['date_time'], "%Y-%m-%d %H:%M:%S")
                price_val = 0
                for attr in item.get('attributes', []):
                    if attr['name'] == 'price':
                        price_val = float(attr['value'])
                        break
                prices[dt.hour] = round(price_val / 1000, 4)
            except (ValueError, KeyError, TypeError) as e:
                _LOGGER.warning("Błąd podczas przetwarzania rekordu ceny: %s. Rekord: %s", e, item)

        if len(prices) != 24 and raw_data: # Sprawdzaj tylko jeśli były jakieś dane
            _LOGGER.warning("Otrzymano niekompletne dane cenowe. Oczekiwano 24 rekordów, otrzymano %d.", len(prices))

        return prices

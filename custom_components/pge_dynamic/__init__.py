# custom_components/pge_dynamic/__init__.py
"""Integracja PGE Dynamic Energy dla Home Assistant."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .coordinator import PGEDataCoordinator
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Konfiguruje integrację na podstawie wpisu konfiguracyjnego."""
    # Tworzenie i inicjalizacja koordynatora danych
    coordinator = PGEDataCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    # Przechowanie koordynatora w globalnym obszarze danych hass
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Przekazanie konfiguracji do platformy sensorów
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    # Nasłuchiwanie na zmiany w opcjach, aby przeładować integrację
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Odładowuje wpis konfiguracyjny."""
    # Odładowanie platformy sensorów
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Obsługuje aktualizacje opcji konfiguracyjnych."""
    await hass.config_entries.async_reload(entry.entry_id)

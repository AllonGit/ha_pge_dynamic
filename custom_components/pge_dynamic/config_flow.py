"""Obsługa konfiguracji przez interfejs (UI)."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TARIFF, TARIFF_OPTIONS

class PGEDynamicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Klasa obsługująca konfigurację w UI."""
    
    # Wersja konfiguracji
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Wyświetlenie formularza."""
        errors = {}

        if user_input is not None:
            # Jeśli użytkownik kliknął "Zatwierdź"
            return self.async_create_entry(
                title="PGE Dynamic Energy",
                data=user_input
            )

        # Definicja formularza (wybór taryfy)
        data_schema = vol.Schema({
            vol.Required(CONF_TARIFF, default=TARIFF_OPTIONS[0]): vol.In(TARIFF_OPTIONS),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
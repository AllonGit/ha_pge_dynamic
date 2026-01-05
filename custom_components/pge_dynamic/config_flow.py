import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TARIFF, TARIFF_OPTIONS

class PGEDynamicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Obsługa przepływu konfiguracji dla PGE Dynamic."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok wyboru nazwy i taryfy."""
        if user_input is not None:
            # Tworzy wpis w Home Assistant
            return self.async_create_entry(
                title=f"PGE Dynamic ({user_input[CONF_TARIFF].split(' ')[0]})", 
                data=user_input
            )

        # Formularz z listą rozwijaną
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="PGE Dynamic Energy"): str,
                vol.Required(CONF_TARIFF, default=TARIFF_OPTIONS[0]): vol.In(TARIFF_OPTIONS),
            })
        )
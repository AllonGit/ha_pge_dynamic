"""Konfiguracja PGE."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TARIFF, CONF_MARGIN, CONF_FEE

TARIFFS = {"G1x": 36.90, "C1x": 49.20, "Inna": 0.0}

class PGEDynamicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            tariff = user_input.get(CONF_TARIFF)
            if user_input.get(CONF_FEE) == 0:
                user_input[CONF_FEE] = TARIFFS.get(tariff, 0.0)
            return self.async_create_entry(title="PGE Dynamic", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TARIFF, default="G1x"): vol.In(list(TARIFFS.keys())),
                vol.Optional(CONF_MARGIN, default=0.0): float,
                vol.Optional(CONF_FEE, default=0.0): float,
            })
        )
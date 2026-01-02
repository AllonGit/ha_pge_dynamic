import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

class PGEConfigFlow(config_entries.ConfigFlow, domain="pge_dynamic"):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="PGE Smart Energy", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("marza", default=0.099): float,
                vol.Required("taryfa", default="G1x"): vol.In(["G1x", "C1x"]),
                vol.Required("oplata_handlowa", default=36.90): float
            })
        )
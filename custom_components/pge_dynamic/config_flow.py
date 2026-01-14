# custom_components/pge_dynamic/config_flow.py
"""Przepływ konfiguracji dla integracji PGE Dynamic Energy."""
import voluptuous as vol
import re

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector, SelectSelectorConfig, SelectSelectorMode,
    EntitySelector, EntitySelectorConfig
)

from .const import (
    DOMAIN,
    CONF_OPERATION_MODE, CONF_ENERGY_SENSOR,
    CONF_G12_SETTINGS, CONF_G12W_SETTINGS,
    CONF_G12_PRICE_PEAK, CONF_G12_PRICE_OFFPEAK, CONF_G12_HOURS_PEAK,
    CONF_G12W_PRICE_PEAK, CONF_G12W_PRICE_OFFPEAK, CONF_G12W_HOURS_PEAK,
    MODE_DYNAMIC, MODE_COMPARISON,
    DEFAULT_G12_PEAK_HOURS, DEFAULT_G12W_PEAK_HOURS
)
from .helpers import parse_hour_ranges

def validate_hour_format(user_input: str) -> bool:
    """Sprawdza poprawność formatu godzin (np. '6-13,15-22')."""
    pattern = re.compile(r"^\d{1,2}-\d{1,2}(,\d{1,2}-\d{1,2})*$")
    return pattern.match(user_input) is not None

class PGEDynamicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Obsługuje przepływ konfiguracji dla PGE Dynamic Energy."""
    VERSION = 1

    def __init__(self):
        """Inicjalizacja przepływu."""
        self.data_schema = {}

    async def async_step_user(self, user_input=None):
        """Krok 1: Wybór trybu pracy."""
        if user_input is not None:
            self.data_schema.update(user_input)
            if user_input[CONF_OPERATION_MODE] == MODE_COMPARISON:
                return await self.async_step_comparison_config()
            # Tryb dynamiczny - kończymy konfigurację
            return self.async_create_entry(title="PGE Dynamic Energy", data=self.data_schema)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_OPERATION_MODE, default=MODE_DYNAMIC): SelectSelector(
                    SelectSelectorConfig(
                        options=[MODE_DYNAMIC, MODE_COMPARISON],
                        mode=SelectSelectorMode.DROPDOWN,
                        translation_key="operation_mode"
                    )
                ),
            })
        )

    async def async_step_comparison_config(self, user_input=None):
        """Krok 2 (Opcjonalny): Konfiguracja trybu porównawczego."""
        if user_input is not None:
            self.data_schema.update(user_input)
            return await self.async_step_g12_config()

        return self.async_show_form(
            step_id="comparison_config",
            data_schema=vol.Schema({
                vol.Optional(CONF_ENERGY_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
            })
        )

    async def async_step_g12_config(self, user_input=None):
        """Krok 3: Konfiguracja taryfy G12."""
        errors = {}
        if user_input is not None:
            if not validate_hour_format(user_input[CONF_G12_HOURS_PEAK]):
                errors["base"] = "invalid_hour_range"
            else:
                self.data_schema[CONF_G12_SETTINGS] = user_input
                return await self.async_step_g12w_config()

        return self.async_show_form(
            step_id="g12_config",
            data_schema=vol.Schema({
                vol.Required(CONF_G12_PRICE_PEAK, default=0.80): vol.Coerce(float),
                vol.Required(CONF_G12_PRICE_OFFPEAK, default=0.50): vol.Coerce(float),
                vol.Required(CONF_G12_HOURS_PEAK, default=DEFAULT_G12_PEAK_HOURS): str,
            }),
            errors=errors
        )

    async def async_step_g12w_config(self, user_input=None):
        """Krok 4: Konfiguracja taryfy G12w."""
        errors = {}
        if user_input is not None:
            if not validate_hour_format(user_input[CONF_G12W_HOURS_PEAK]):
                errors["base"] = "invalid_hour_range"
            else:
                self.data_schema[CONF_G12W_SETTINGS] = user_input
                title = "PGE Dynamic Energy (Comparison)" if self.data_schema[CONF_OPERATION_MODE] == MODE_COMPARISON else "PGE Dynamic Energy"
                return self.async_create_entry(title=title, data=self.data_schema)

        return self.async_show_form(
            step_id="g12w_config",
            data_schema=vol.Schema({
                vol.Required(CONF_G12W_PRICE_PEAK, default=0.85): vol.Coerce(float),
                vol.Required(CONF_G12W_PRICE_OFFPEAK, default=0.55): vol.Coerce(float),
                vol.Required(CONF_G12W_HOURS_PEAK, default=DEFAULT_G12W_PEAK_HOURS): str,
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Zwraca przepływ opcji dla tej integracji."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Obsługuje przepływ opcji dla PGE Dynamic Energy."""

    def __init__(self, config_entry):
        """Inicjalizacja przepływu opcji."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Główny krok opcji."""
        # W trybie dynamicznym nie ma opcji do zmiany
        if self.config_entry.data.get(CONF_OPERATION_MODE) != MODE_COMPARISON:
            return self.async_create_entry(title="", data={})

        # W trybie porównawczym, zaczynamy od konfiguracji ogólnej
        return await self.async_step_comparison_config()

    async def async_step_comparison_config(self, user_input=None):
        """Opcje dla trybu porównawczego."""
        if user_input is not None:
            self.options.update(user_input)
            return await self.async_step_g12_config()

        return self.async_show_form(
            step_id="comparison_config",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_ENERGY_SENSOR,
                    default=self.options.get(CONF_ENERGY_SENSOR, self.config_entry.data.get(CONF_ENERGY_SENSOR))
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            })
        )

    async def async_step_g12_config(self, user_input=None):
        """Opcje dla taryfy G12."""
        errors = {}
        g12_settings = self.options.get(CONF_G12_SETTINGS, self.config_entry.data.get(CONF_G12_SETTINGS, {}))

        if user_input is not None:
            if not validate_hour_format(user_input[CONF_G12_HOURS_PEAK]):
                errors["base"] = "invalid_hour_range"
            else:
                self.options[CONF_G12_SETTINGS] = user_input
                return await self.async_step_g12w_config()

        return self.async_show_form(
            step_id="g12_config",
            data_schema=vol.Schema({
                vol.Required(CONF_G12_PRICE_PEAK, default=g12_settings.get(CONF_G12_PRICE_PEAK)): vol.Coerce(float),
                vol.Required(CONF_G12_PRICE_OFFPEAK, default=g12_settings.get(CONF_G12_PRICE_OFFPEAK)): vol.Coerce(float),
                vol.Required(CONF_G12_HOURS_PEAK, default=g12_settings.get(CONF_G12_HOURS_PEAK)): str,
            }),
            errors=errors
        )

    async def async_step_g12w_config(self, user_input=None):
        """Opcje dla taryfy G12w."""
        errors = {}
        g12w_settings = self.options.get(CONF_G12W_SETTINGS, self.config_entry.data.get(CONF_G12W_SETTINGS, {}))

        if user_input is not None:
            if not validate_hour_format(user_input[CONF_G12W_HOURS_PEAK]):
                errors["base"] = "invalid_hour_range"
            else:
                self.options[CONF_G12W_SETTINGS] = user_input
                return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="g12w_config",
            data_schema=vol.Schema({
                vol.Required(CONF_G12W_PRICE_PEAK, default=g12w_settings.get(CONF_G12W_PRICE_PEAK)): vol.Coerce(float),
                vol.Required(CONF_G12W_PRICE_OFFPEAK, default=g12w_settings.get(CONF_G12W_PRICE_OFFPEAK)): vol.Coerce(float),
                vol.Required(CONF_G12W_HOURS_PEAK, default=g12w_settings.get(CONF_G12W_HOURS_PEAK)): str,
            }),
            errors=errors
        )

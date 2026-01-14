# custom_components/pge_dynamic/const.py
"""Stałe dla integracji PGE Dynamic Energy."""
from datetime import timedelta

DOMAIN = "pge_dynamic"
API_URL = "https://datahub.gkpge.pl/api/tge/quote"

# --- Konfiguracja ---
CONF_OPERATION_MODE = "operation_mode"
CONF_ENERGY_SENSOR = "energy_sensor"
CONF_G12_SETTINGS = "g12_settings"
CONF_G12W_SETTINGS = "g12w_settings"

# --- Ustawienia taryf ---
CONF_PRICE_PEAK = "price_peak"
CONF_PRICE_OFFPEAK = "price_offpeak"
CONF_HOURS_PEAK = "hours_peak"

# --- Tryby pracy ---
MODE_DYNAMIC = "dynamic"
MODE_COMPARISON = "comparison"

# --- Wartości domyślne ---
DEFAULT_G12_PEAK_HOURS = "6-13,15-22"
DEFAULT_G12W_PEAK_HOURS = "6-13,15-22"

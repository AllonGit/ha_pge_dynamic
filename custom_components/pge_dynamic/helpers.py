# custom_components/pge_dynamic/helpers.py
"""Funkcje pomocnicze dla integracji PGE Dynamic Energy."""
import logging
from datetime import date
import holidays

_LOGGER = logging.getLogger(__name__)
PL_HOLIDAYS = holidays.Poland()

def is_holiday(day: date) -> bool:
    """Sprawdza, czy podany dzień jest świętem w Polsce."""
    return day in PL_HOLIDAYS

def parse_hour_ranges(range_str: str):
    """
    Konwertuje ciąg znaków z zakresami godzin (np. '6-13,15-22')
    na zbiór liczb całkowitych reprezentujących te godziny.
    """
    hours = set()
    if not isinstance(range_str, str):
        _LOGGER.warning("Nieprawidłowy typ danych dla zakresu godzin: %s", type(range_str))
        return hours

    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                # Zakres jest [start, end), więc dodajemy godziny od `start` do `end-1`
                hours.update(range(start, end))
            except ValueError:
                _LOGGER.warning("Nieprawidłowy format w zakresie godzin: '%s'", part)
        else:
            try:
                hours.add(int(part))
            except ValueError:
                _LOGGER.warning("Nieprawidłowa godzina w zakresie: '%s'", part)

    return hours

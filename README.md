# PGE Dynamic Energy dla Home Assistant

<p align="center">
  <img src="https://raw.githubusercontent.com/AllonGit/ha_pge_dynamic/main/custom_components/pge_dynamic/icon/icon.png" width="150" alt="PGE Dynamic Logo">
</p>

Integracja pobierająca aktualne ceny energii elektrycznej z API PGE DataHub (Rynek Bilansujący). Dane są pobierane bezpośrednio z TGE (Towarowa Giełda Energii) przez bramkę PGE.

## Funkcje
- 24 sensory (po jednym na każdą godzinę doby).
- Sensor ceny aktualnej.
- **Automatyczne przeliczanie:** MWh na kWh.
- **Podatek VAT:** Ceny zawierają podatek VAT 23%.
- **Format:** PLN/kWh.

## Instalacja

### Metoda 1: HACS (Zalecana)
1. Otwórz HACS w Home Assistant.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Custom repositories**.
3. Wklej link do tego repozytorium i wybierz kategorię **Integration**.
4. Zainstaluj `PGE Dynamic Energy`.
5. Zrestartuj Home Assistant.

### Metoda 2: Ręczna
1. Skopiuj folder `custom_components/pge_dynamic` do folderu `config/custom_components/` w swoim Home Assistant.
2. Zrestartuj Home Assistant.

## Konfiguracja
1. Wejdź w **Ustawienia** -> **Urządzenia oraz usługi**.
2. Kliknij **Dodaj integrację** i wyszukaj `PGE Dynamic Energy`.
3. Wybierz swoją taryfę (np. G1x).

## Wykresy (ApexCharts)
Aby uzyskać ładny wykres cen na całą dobę, zainstaluj `ApexCharts Card` z HACS i użyj poniższego kodu:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Ceny Energii PGE (brutto)
  show_states: true
  colorize_states: true
series:
  - entity: sensor.pge_cena_aktualna_brutto
    type: column
    data_generator: |
      # Logika generowania wykresu z 24 sensorów godzinnych
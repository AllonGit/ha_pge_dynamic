# PGE Dynamic Energy (Ceny Dynamiczne) dla Home Assistant

![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![version](https://img.shields.io/github/v/release/AllonGit/ha_pge_dynamic)
![license](https://img.shields.io/github/license/AllonGit/ha_pge_dynamic)

Integracja pobierająca aktualne ceny energii elektrycznej (Rynek Bilansujący) bezpośrednio z oficjalnego API **PGE DataHub**. Narzędzie pozwala na monitorowanie stawek rynkowych w czasie rzeczywistym bezpośrednio w Twoim panelu Home Assistant.

## 🌟 Główne Funkcje

* **Konfiguracja przez UI:** Proste dodawanie integracji przez interfejs Home Assistant (Config Flow).
* **Cena Netto:** Wyświetla aktualną stawkę rynkową w **PLN/kWh**.
* **Dokładność:** Dane pobierane z kontraktu Fix_1 (Rynek Bilansujący).
* **Kompletna doba:** 24 odrębne sensory godzinne (od `00:00` do `23:00`).
* **Sensor bieżący:** `sensor.pge_cena_aktualna` – cena dla obecnej godziny.
* **Optymalizacja:** Używa `DataUpdateCoordinator` dla minimalnego obciążenia systemu.

## 🚀 Instalacja

### Przez HACS (Zalecane)

1. W Home Assistant przejdź do **HACS** -> **Integracje**.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Custom repositories**.
3. Wklej URL tego repozytorium: `https://github.com/AllonGit/ha_pge_dynamic`
4. Wybierz kategorię **Integration** i kliknij **Dodaj**.
5. Znajdź integrację na liście, kliknij **Pobierz**, a następnie zrestartuj Home Assistant.

## ⚙️ Konfiguracja

1. Przejdź do **Ustawienia** -> **Urządzenia oraz usługi**.
2. Kliknij **Dodaj integrację** i wyszukaj `PGE Dynamic Energy`.
3. Wpisz nazwę oraz wybierz swoją taryfę (np. **G1x**).

## 📊 Wykresy (ApexCharts)
Przykład konfiguracji dla karty `ApexCharts Card` (wyświetla ceny godzinowe na całą dobę):

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Ceny Energii PGE (Netto)
  show_states: true
graph_span: 24h
span:
  start: day
yaxis:
  - decimals: 3
series:
  - entity: sensor.pge_cena_aktualna
    type: column
    color: "#ff9800"
    float_precision: 3
    data_generator: |
      const prices = [];
      for (let i = 0; i < 24; i++) {
        const entity = `sensor.pge_cena_${i.toString().padStart(2, '0')}_00`;
        const state = hass.states[entity];
        if (state) {
          prices.push([new Date().setHours(i, 0, 0, 0), parseFloat(state.state)]);
        }
      }
      return prices;
```

## 🤝 Współtworzenie i społeczność

Chcesz pomóc w rozwoju projektu? Zapraszamy!

* **Masz pomysł lub znalazłeś błąd?** Otwórz [Issue](https://github.com/AllonGit/ha_pge_dynamic/issues).
* **Zasady współpracy:** Sprawdź nasz plik [CONTRIBUTING.md](CONTRIBUTING.md).
* **Standardy społeczności:** Obowiązuje nas [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 🛡️ Bezpieczeństwo

Jeśli znalazłeś lukę w bezpieczeństwie, prosimy o zapoznanie się z naszą polityką bezpieczeństwa w pliku [SECURITY.md](SECURITY.md).

## ⚖️ Licencja

Projekt udostępniany na licencji **MIT**. Pełną treść znajdziesz w pliku [LICENSE](LICENSE).

## ⚠️ Nota prawna

Integracja ma charakter open-source i hobbystyczny. Dane są pobierane z publicznie dostępnego API PGE DataHub. Autor nie ponosi odpowiedzialności za ewentualne błędy w danych ani decyzje finansowe podejmowane na ich podstawie. Zawsze weryfikuj dane u dostawcy energii.
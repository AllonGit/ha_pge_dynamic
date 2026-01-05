![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)
![version](https://img.shields.io/github/v/release/AllonGit/ha_pge_dynamic)
![license](https://img.shields.io/github/license/AllonGit/ha_pge_dynamic)

# PGE Dynamic Energy (Ceny Dynamiczne) dla Home Assistant

Integracja pobierająca aktualne ceny energii elektrycznej (Rynek Bilansujący) bezpośrednio z oficjalnego API **PGE DataHub**. Narzędzie pozwala na monitorowanie stawek giełdowych TGE (Towarowa Giełda Energii) w czasie rzeczywistym bezpośrednio w Twoim panelu Home Assistant.

## 🌟 Główne Funkcje
- **Cena Netto:** Wyświetla aktualną stawkę rynkową w **PLN/kWh**.
- **Dokładność:** Dane pobierane z kontraktu Fix_1 (Rynek Bilansujący).
- **Kompletna doba:** 24 odrębne sensory godzinne (od `00:00` do `23:00`).
- **Sensor bieżący:** `sensor.pge_cena_aktualna` – zawsze pokazuje cenę dla obecnej godziny.
- **Optymalizacja:** Używa DataUpdateCoordinator dla minimalnego obciążenia sieci i procesora.
- **Interfejs:** Estetyczne ikony błyskawic (`mdi:lightning-bolt`) i poprawna klasa walutowa.

## 🚀 Instalacja

### Przez HACS (Zalecane)
1. W Home Assistant przejdź do **HACS** -> **Integracje**.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Custom repositories**.
3. Wklej URL tego repozytorium: `https://github.com/AllonGit/ha_pge_dynamic`
4. Wybierz kategorię **Integration** i kliknij **Dodaj**.
5. Znajdź integrację na liście, kliknij **Pobierz**, a następnie zrestartuj Home Assistant.

### Ręczna
1. Skopiuj folder `custom_components/pge_dynamic` do folderu `config/custom_components/`.
2. Zrestartuj Home Assistant.

## ⚙️ Konfiguracja
1. Przejdź do **Ustawienia** -> **Urządzenia oraz usługi**.
2. Kliknij **Dodaj integrację** i wyszukaj `PGE Dynamic Energy`.
3. Wybierz taryfę (np. G1x) i zatwierdź.

## 📊 Wykresy (ApexCharts)
Dla najlepszego efektu wizualnego zaleca się użycie karty `ApexCharts Card`. Przykład konfiguracji:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Ceny Energii - Dzisiaj (PLN/kWh)
  show_states: true
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.pge_cena_aktualna
    type: column
    color: "#ff9800"
    data_generator: |
      # Dane generowane automatycznie z sensorów godzinnych
```
### 💡 Masz pomysł? Zgłoś go!
Projekt jest stale rozwijany i jestem otwarty na nowe funkcjonalności!

Masz pomysł na nowe sensory (np. cena średnia, najtańsze godziny)?

Chcesz zaproponować zmiany w kodzie?

Znalazłeś błąd?

Zapraszam do sekcji [Issues](https://github.com/AllonGit/ha_pge_dynamic/issues) – każda sugestia pomaga ulepszyć tę integrację!

### ✉️ Kontakt i Wsparcie

- **Problemy techniczne:** Proszę zgłaszać poprzez [Issues](https://github.com/AllonGit/ha_pge_dynamic/issues).
- **Pytania i Dyskusja:** Zapraszam do sekcji [Discussions](https://github.com/AllonGit/ha_pge_dynamic/discussions).
- **Kontakt bezpośredni:** Jeśli masz sprawę, która wymaga kontaktu prywatnego, możesz wysłać wiadomość poprzez profil GitHub.

### ⚖️ Licencja:
Projekt udostępniany na licencji MIT. Szczegóły w pliku [LICENSE](LICENSE).

### Nota prawna: 
Integracja ma charakter open-source i hobbystyczny. Dane są pobierane z publicznego API PGE DataHub. Autor nie ponosi odpowiedzialności za decyzje finansowe podejmowane na podstawie wyświetlanych cen.
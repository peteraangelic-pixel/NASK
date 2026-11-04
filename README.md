# NASK: badania programów Bug Bounty

Stan prac: 4 listopada 2026, edycje 11/2026. Repozytorium źródłowe: https://github.com/peteraangelic-pixel/NASK (publiczne).

Aktywny kierunek: **wyłącznie program NASK**, zgodnie z decyzją użytkownika z 4 listopada. Starsze analizy pozostałych programów zachowujemy jako materiały historyczne.

- [Aktualny stan, ograniczenia i centralny indeks materiałów](research/AKTUALNY-STAN.md)
- [Wykonana runda NASK i analiza lokalna](research/nask-focus-2026-11-04.md)
- [Historyczne porównanie pięciu programów](research/porownanie-programow.md)
- [Przegląd narzędzi Arena.ai i rozpoznanie dostępu](research/arena-review-2026-11-03.md)
- [Aktualny następny etap po ocenie materiałów z Dysku](research/nastepny-etap-2026-11-03.md)
- [NASKLab: Python FFI + Rust/Rayon, kolejka wielu programów](tools/recon/README.md)
- [Transfer metod z Riemann, ARC i Ctrader](research/transfer-actions-2026-11-03.md)
- [Wynik pilota Actions i dalsza kolejka badań](research/pilot-actions-2026-11-03.md)
- [Jednorazowy przebieg nocny: ekspozycja plików i kontrole catch-all](research/night-operation-2026-11-03.md)
- [Zapis warunków i zakresów w JSON](programs/2026-11.json)
- [Szablon zgłoszenia](templates/zgloszenie.md)
- `research/sources/`: pobrane publiczne regulaminy PDF i ich ekstrakcje tekstowe; adresy i SHA-256 zapisano w JSON.

Wykonano analizę publicznych zasad oraz pilot kolektora przez Actions: 48 odczytów publicznych stron i wskazanych skryptów, 24 hosty w czterech programach. To rozpoznanie powierzchni aplikacji; potwierdzonych podatności: **0**. Szczegóły, ograniczenia i identyfikatory przebiegów znajdują się w raporcie pilota.

Przebieg nocny wykonał dodatkowo 71 odczytów do celów oraz cztery weryfikacje regulaminów, z kontrolami catch-all i badaniem dwóch formatów ekspozycji plików. Kandydatów: 0, pokrycie częściowe po blokadach i błędach. Wynik i ograniczenia opisuje raport operacji nocnej; zadanie jest zakończone.

NASKLab implementuje kolejkę rozpoznania wielu programów i analizę lokalną w Rust/Rayon wywoływaną z Pythona. Część sieciowa ma wspólny ogranicznik tempa. Kontrolowane rozpoznanie i analiza wskazują powierzchnie do badań; nie stanowią automatycznego potwierdzenia podatności. Starsze plany w `research/` opisują stan z momentu ich sporządzenia.

Dowody, sesje, dane kont i nieujawnione zgłoszenia przechowujemy lokalnie w ignorowanych katalogach `private/`, `evidence/`, `captures/` i `reports/`. `.gitignore` nie jest granicą bezpieczeństwa: przed ewentualnym pushem trzeba sprawdzić zawartość zmian. Publiczne repo ani logi Actions nie służą do przechowywania nieujawnionych luk.

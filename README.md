# NASK: badania programów Bug Bounty

Stan rozpoznania: 3 listopada 2026, edycje 11/2026. Repozytorium źródłowe: https://github.com/peteraangelic-pixel/NASK (publiczne).

Rekomendowany pierwszy kierunek: **program NASK**, następnie **CERT Polska**. Rekomendacja wynika z regulaminów i zakresów, a nie z potwierdzonych podatności ani zmierzonej trudności.

- [Porównanie pięciu programów i plan pierwszego etapu](research/porownanie-programow.md)
- [Przegląd narzędzi Arena.ai i rozpoznanie dostępu](research/arena-review-2026-11-03.md)
- [Aktualny następny etap po ocenie materiałów z Dysku](research/nastepny-etap-2026-11-03.md)
- [Zapis warunków i zakresów w JSON](programs/2026-11.json)
- [Szablon zgłoszenia](templates/zgloszenie.md)
- `research/sources/`: pobrane publiczne regulaminy PDF i ich ekstrakcje tekstowe; adresy i SHA-256 zapisano w JSON.

Dotychczas wykonano analizę publicznych zasad, nie skanowanie podatności. Zwykłe otwarcie stron eObieg i BIP Władysławowa nie powiodło się w używanej przeglądarce; nie jest to ustalenie o ich bezpieczeństwie ani dostępności z innych sieci.

Narzędzia obliczeniowe będziemy pisać przede wszystkim w Rust; Rayon zastosujemy do pracy na lokalnych danych, gdy pomiary uzasadnią równoległość. Automatyzacja HTTP musi mieć wspólny ogranicznik tempa. Opis architektury w planie jest propozycją, nie zaimplementowanym skanerem.

Dowody, sesje, dane kont i nieujawnione zgłoszenia przechowujemy lokalnie w ignorowanych katalogach `private/`, `evidence/`, `captures/` i `reports/`. `.gitignore` nie jest granicą bezpieczeństwa: przed ewentualnym pushem trzeba sprawdzić zawartość zmian. Publiczne repo ani logi Actions nie służą do przechowywania nieujawnionych luk.

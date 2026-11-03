# Transfer metod z wcześniejszych projektów do NASKLab

Data: 2026-11-03. Odczyt przez podpięty GitHub i API: bieżące końce 9 gałęzi `riemann`, 5 gałęzi `Smak-Domu-Konkurs` i 2 gałęzi prywatnego `Ctrader`. Sprawdzono listy workflowów i wybrane źródła; nie czytano wszystkich linii wszystkich gałęzi. Nie uruchamiano ani nie zmieniano tych trzech projektów.

## Co znaleziono i wykorzystano

| Źródło | Potwierdzona metoda | Wdrożenie w NASKLab |
| --- | --- | --- |
| Riemann `compute.yml` | Zadania na żądanie, ograniczony czas, artefakty zachowywane także po błędzie, start znacznikiem commitu | Ograniczone operacje i osobny workflow integracyjny ze znacznikiem `[lab-surface]` |
| Riemann `kaggriculture-rust.yml` | Locked dependencies, testy Rust i adaptera Python, parytet, końcowe sprawdzenie wyników etapów | Cargo.lock, rzeczywisty test ctypes na zbudowanej bibliotece, brak tłumienia błędów CI |
| Riemann `kaggriculture-meta-lab.yml` | Krótki test przed kosztowniejszym przebiegiem, ograniczony budżet | Testy kontrolne przed integracją; pierwsza operacja do 48 odczytów |
| Riemann niezależny gate | Osobny etap sprawdzający kandydata, utrwalenie wyniku | Receipty i testy integralności zamiast uznawania samego outputu za sukces |
| ARC `arc3-ops.yml` | Jedno wejście operacyjne z ID, tryby rozdzielające odczyt i publikację, kolejka concurrency, artefakty | `request.json`, stały tryb `public-surface-validation`, jeden koordynator ruchu |
| Ctrader utrzymywane komponenty | Hash rzeczywiście użytego kodu i danych, błąd dla brakujących/powtórzonych wyników, Rust/Rayon przez ctypes | Hash paczki kodu, manifestu i DLL/SO; kontrola kompletności rekordów; własny adapter FFI |

Na obu bieżących gałęziach `Ctrader` nie znaleziono katalogu `.github/workflows`. Przydatne elementy pochodzą z komponentów i dokumentacji tego projektu. Nie kopiowano do publicznego repo prywatnych kodów strategii, danych finansowych ani treści prywatnego repo.

## Przypięte źródła publiczne

- [Riemann compute](https://github.com/peteraangelic-pixel/riemann/blob/f68168bbdabc039320069059af187f720b36b75c/.github/workflows/compute.yml)
- [Riemann Rust/Python parity](https://github.com/peteraangelic-pixel/riemann/blob/5af9d573f1353cae899f5cffbfd30d5e92ec1f6e/.github/workflows/kaggriculture-rust.yml)
- [Riemann Meta-Lab](https://github.com/peteraangelic-pixel/riemann/blob/41b1641a2f1fef01c33fb594b40202bee8a29194/.github/workflows/kaggriculture-meta-lab.yml)
- [Riemann independent gate](https://github.com/peteraangelic-pixel/riemann/blob/7a3e4ca78e40d3b905c0143c764b69b29ee7bd9b/.github/workflows/kaggriculture-farmosa-v16-independent-gate.yml)
- [ARC ops Arena](https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/blob/4edd44cb03eb6a9626c495cde3d0a4df7567798e/.github/workflows/arc3-ops.yml)
- [ARC ops Codex](https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/blob/ff77784286bc68d81b0326595b8f6166a9a06c91/.github/workflows/arc3-ops.yml)

Źródła Ctrader sprawdzono na `f77f4752540aca2ee717db1b8371a3bfaf47f097`: `components/experiment_batch.py`, `components/README.md`, `native/tick-exits/README.md`, `docs/TRANSFER_KAGGLE_I_DRIVE_2026-11-02.md`. Kopie do odczytu i pozostała dokumentacja robocza pozostają w ignorowanym `private/workflow-patterns/`.

## Czego nie przenosimy

- Dziesiątki runnerów CPU nie oznaczają zgody na sumowanie wielu limitów sieciowych. NASKLab ma jeden koordynator, a domyślny pilot 1 żądanie/s łącznie.
- Automatyczny commit wyników Kaggle nie jest odpowiedni dla nieujawnionych podatności w publicznym repo. Zamiast tego używamy zaszyfrowanego artefaktu i lokalnych wyników.
- Zielony etap po `continue-on-error` nie wystarcza. W źródle Riemann występuje końcowy gate sprawdzający outcomes; Arena NASK wcześniej go nie miała. Nasze kroki błędów nie ignorują.
- Parytet obliczeń, szybkość Rusta i liczba odkrytych ścieżek nie są dowodem podatności ani przyszłej nagrody.

## Bieżący zakres działania

Pierwsza integracja obejmuje publiczne strony i już wskazane skrypty z dokładnie wypisanych hostów NASK, CERT, Gov.pl i Władysławowa. mSzyfr pozostaje odroczony, bo nie wybrano jeszcze jednoznacznego hosta z jego zakresu wildcard. Nie dodajemy wymyślonych nazw ani nie rozszerzamy zakresu do wszystkich subdomen.

Ta operacja jest walidacją własnego kolektora i jakości dowodów, nie testem exploitów. Nie ma POST, wysyłania formularzy, zgadywania kont, odczytywania prywatnych danych ani obchodzenia uwierzytelniania. Wyniki służą wyborowi kolejnych konkretnych hipotez.

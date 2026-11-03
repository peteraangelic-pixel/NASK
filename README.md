# NASK — Bug Bounty Toolkit & Strategia (hack.cert.pl)

Projekt wspierający udział w konkursie Bug Bounty NASK / CERT Polska
(platforma https://hack.cert.pl/, edycja 11/2026, 03.11–30.11.2026).

## Co tu jest

* **`STRATEGIA.md`** — konkretny plan, jak wygrać nagrody (300–20 000 PLN za błąd, pula 1 mln PLN).
* **`rust/`** — szybkie narzędzia recon/fuzzing napisane w **Rust + Rayon** (wykorzystanie wszystkich rdzeni — idealnie pod Ryzen 9 5950X, 16 rdzeni / 32 wątki, 64 GB RAM).
* **`python/`** — moduły tam, gdzie Rust nie jest praktyczny, wywoływane przez **Python FFI + multiprocessing**.
* **`.github/workflows/`** — GitHub Actions (większa moc obliczeniowa niż sandbox): buduje narzędzia, uruchamia testy, przykładowe skany.

## ⚠️ Ważne — zasady i granice

* Testujemy **tylko w zakresie (scope)** programów na hack.cert.pl: NASK, CERT Polska, Portal Gov.pl, mSzyfr, Gmina Władysławowo.
* Ataki poza scope to nie jest bug bounty — to już wykroczenie / przestępstwo. Narzędzia z tego repo nie wolno używać przeciwko systemom, do których nie masz pisemnej zgody (program bug bounty constituye taką zgodę tylko w obrębie podanego scope).
* Zgłoszenia wysyłamy wyłącznie przez formularz na hack.cert.pl z pełnym PoC (Proof of Concept) i instrukcją odtworzenia.
* Zachowujemy pełną dyskrecję do momentu wdrożenia poprawki przez administratorów.
* Nie przeprowadzamy ataków typu DoS ani niczego, co mogłoby zagrozić ciągłości działania usług państwowych.

Jako agent dostarczam kod, narzędzia i strategię. Rzeczywiste testy intruzycyjne i zgłoszenia wykonuje użytkownik — ja nie wykonuję aktywnych ataków przeciwko systemom NASK/CERT.

## Wymagania

* Rust (stable) + cargo — na Twoim Ryzenie lub w GitHub Actions.
* Python 3.11+ — moduły FFI/multiprocessing.

## Licencja

Edukacyjne / własne użytkowe. Narzędzia do legalnych badań w ramach programów bug bounty.

# Arena.ai: przegląd przed użyciem narzędzi

Źródło: NASK codex/multi-program-lab-20261103, research/arena-review-2026-11-03.md

Data: 2026-11-03. Repo: https://github.com/peteraangelic-pixel/NASK.
Gałąź: `arena/a29ca234-nask`. Sprawdzony commit: `362d02c`.

## Co można wykorzystać

Podział na narzędzia Rust, analizę JS, szablony raportów i osobny workflow uruchamiany
ręcznie jest przydatnym szkieletem. Konkretne narzędzia wymagają weryfikacji i poprawek
przed pracą z serwerami programu.

## Potwierdzone problemy

1. **Kompilacja.** `cargo check` zakończyło się kodem 101. `probe` i `ffuzz` wywołują
   `timeout_connect` na `ureq::Request`; metoda jest niedostępna w użytej wersji.
   Rozwiązano `ureq` 2.12.1. Mogą wystąpić dalsze błędy po poprawieniu pierwszych;
   nie uznano całego kodu za sprawdzony kompilacyjnie.

2. **Brak ogranicznika tempa.** `probe` i `ffuzz` wykonują żądania w `par_iter()`
   z liczbą wątków zależną od CPU lub argumentu. Liczba wątków nie ogranicza żądań/s
   do wymaganego maksimum. Potrzebny wspólny limiter uwzględniający wszystkie wysyłane
   żądania i przekierowania.

3. **Brak wymuszenia zakresu.** Narzędzia przyjmują dowolne URL lub domenę, a komentarze
   są jedynym ograniczeniem. Potrzebne sprawdzanie dokładnego hosta przed żądaniem oraz
   kontrola przekierowań. Odkrycie subdomeny w DNS nie potwierdza zgody na testy HTTP
   tego hosta.

4. **Błędne przykłady.** W `ffuzz` występują `gov.pl` i `mszyfr.gov.pl`, podczas gdy
   zweryfikowane zakresy to odpowiednio `www.gov.pl` oraz `*.komunikator.narodowy.gov.pl`.
   Program NASK nie zawiera wildcardu na wszystkie subdomeny `nask.pl`.

5. **CI nie potwierdza poprawności.** W sprawdzonym `ci.yml` formatowanie może się nie
   udać bez porażki zadania, a `cargo clippy --all-targets || true` tłumi porażkę
   kompilacji/lintera. Osobne kroki kompilacji i testów usunięto. Zielony wynik takiego
   workflow nie stanowi dowodu poprawności kodu.

6. **HTTPS.** Workspace używa `ureq` z `default-features = false` bez jawnego włączenia
   TLS. Przed użyciem celów HTTPS trzeba przywrócić obsługę TLS.

## Pierwsze rozpoznanie publicznych stron

Odczytano zwykłe strony główne `nask.pl`, `dns.pl` i `dyzurnet.pl`. Nie podawano danych
formularzy ani prób podatności.

- `nask.pl` przekierowuje do `www.nask.pl`. Zwykły odczyt strony nie oznacza rozszerzenia
  scope testów.
- `dns.pl` udostępnia publiczne informacje i odsyła m.in. do `panel.dns.pl`. Panel nie
  jest jawnie wymieniony w zakresie programu NASK.
- `dyzurnet.pl` udostępnia publiczne treści i odnośnik do zgłoszeń. Nie wysłano zgłoszenia
  ani nie badano danych osób trzecich.

## NASK a mSzyfr

mSzyfr jest sensownym kandydatem, ale wiek instytucji i produktu nie mierzy jakości
implementacji konkretnej funkcji. Karta programu nie zapewnia dedykowanych kont testowych.
NASK pozostaje pierwszym kierunkiem.

## Deklaracja o legalnych testach

Zdanie o testach wyłącznie w scope jest poprawnym opisem celu. Nie stanowi gwarancji
prawnej ani technicznego wymuszenia warunków. Dokładniejszy zapis: „Narzędzia są
przeznaczone do badań bezpieczeństwa systemów wskazanych w aktualnym zakresie programu
hack.cert.pl, zgodnie z regulaminem platformy i konkretnej edycji, limitami testowania
oraz zasadami poufności i ochrony danych”.

## Uzupełnienie po analizie instrukcji Arena.ai

- `jsminer.py` może służyć jako pomysł na ekstrakcję ścieżek i komentarzy z JS. Obecnie
  łączy analizę z równoległym pobieraniem URL przez `multiprocessing.Pool`, nie ma
  wspólnego limitera tempa ani kontroli scope i przekierowań. Do naszego etapu lepszy
  będzie rozdział: kontrolowane pobranie, potem równoległa analiza lokalna.
- `jsminer.py` nie importuje ani nie wywołuje `ffi_native.py`; nie korzysta obecnie z
  przyspieszenia FFI.
- Pokazana sekwencja `subenum | cut | probe` przekazuje do `probe` hosty bez schematu
  URL, choć narzędzie oczekuje URL HTTP(S).
- `build-native.sh` po przejściu do `rust/native` kopiuje bibliotekę do `../python`,
  czyli `rust/python`, zamiast katalogu `python` w głównym repo.
- Osobne `cargo check --manifest-path tmp/arena-review/rust/native/Cargo.toml` zakończyło
  się kodem 101: pakiet `native` jest pod katalogiem workspace, ale nie został dodany
  do `members` ani `exclude` i nie definiuje własnego workspace.

## Stan monitora

Utworzono aktywny monitor w tym czacie co 2 godziny: `nask-monitor-zmian-arena-ai`.

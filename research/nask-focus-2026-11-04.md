# NASK: aktualny kierunek i wykonana runda 4 listopada

Aktywny kierunek użytkownika: **wyłącznie program NASK, edycja 11/2026**. Starsze plany wieloprogramowe pozostają historycznym zapisem; nie są poleceniem uruchamiania tamtych operacji. Monitor gałęzi nie został wznowiony.

## Wykonany zakres

- Ponownie pobrano oficjalny regulamin NASK: hash SHA256 zgodny z zapisanym PDF. Dokładny zakres obejmuje 12 hostów, bez automatycznego dodawania aliasów/subdomen. Dopuszczalne tempo automatyki wynosi 5 req/s. [Karta programu](https://hack.cert.pl/programs/nask-pib/nask/editions/1).
- Lokalnie skompilowano bibliotekę Rust/Rayon i użyto jej przez Python FFI. Testy: 12 Rust, 23 Python, rzeczywiste FFI i Clippy z błędami ostrzeżeń — zaliczone na Windows. Nie jest to wynik nowego CI Linux/Windows w Actions.
- Połączono zapisane materiały NASK z własnych przebiegów i paczki Drive, z weryfikacją hashy i zachowaniem pochodzenia kopii. Po aktualizacji: **110 obserwacji, 89 dokumentów, 8 159 235 B, 21 kopii** wyłączonych z powtórnych obliczeń.
- Pobrano 12 publicznych, jawnie wskazanych modułów klienta jednej aplikacji objętej zakresem: 12 x 200, 109 172 B, sekwencyjnie przy ustawieniu 0,25 req/s. Bez kont, cookies, wywołań API, redirectów i tworzenia zgłoszeń. Rejestrowano rzeczywiste czasy i rozmiary. Limit tej operacji nie koordynuje automatycznie innych repozytoriów/sesji.
- Nowe wyniki opisują kontrakty klienta i dokładniejsze pokrycie. **Potwierdzone podatności: 0.** Szczegółowe mapy, źródła i kolejka hipotez pozostają pod `private/nask-focus-2026-11-04/`.

## Adaptowane metody

Nowe pole `client_contracts` w analizie natywnej zachowuje metody, offsety bajtowe, rozróżnienie wywołania od literału i nazwy parametrów query bez ich wartości. Rozpoznaje też część klientów używających prefiksu i względnych tras. To heurystyka statyczna: nie wykonuje JS, nie rozwiązuje pełnego AST/scope/importów i nie potwierdza działania endpointu.

`tools/recon/python/corpus.py` weryfikuje SHA256 każdego wejścia i dokładny origin NASK. Deduplikacja obejmuje origin i hash; identyczny kod z różnych usług nie zostaje połączony jako jedna usługa. Archiwalne pochodzenie jest jawnie oddzielone od własnego przechwycenia HTTP.

## PC i Actions

Lokalna kompilacja ma sens i została wykonana. Biblioteka nie wysyła ruchu. Nie potrzebowała GPU ani długiego zadania na całe 64 GB RAM. Narzędzia analizujące JS/HAR można wykonywać offline; klient sieciowy/fuzzer jest odrębnym rodzajem zadania. Tempo sieciowe nadal wynika z regulaminu i wspólnej kolejki, niezależnie od CPU i runnera.

Do budowania i testów syntetycznych pozostaje workflow `lab-ci.yml`. W tej rundzie nie uruchomiono nowego zadania sieciowego Actions. Przed kolejną rundą ruchu należy ustalić jednego koordynatora dla wszystkich sesji pracujących nad NASK.

## Odtwarzanie analizy offline

```powershell
cargo build --locked --release --manifest-path tools/recon/Cargo.toml
python tools/recon/python/corpus.py --inventory private/nask-focus-2026-11-04/corpus-inputs.json --library tools/recon/target/release/nasklab.dll --output private/nask-focus-2026-11-04/analysis.json --threads 16
```

Wejścia i wyniki nie są częścią publicznego repo. Cały wynik pozostaje prywatny: redakcja nowych hintów nie usuwa literałów zachowanych w starszych polach analizy. Nie uruchamiano programów dołączonych do cudzych paczek.

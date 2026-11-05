# Aktualny stan projektu NASK

Stan: 5 listopada 2026. Ten plik wskazuje bieżącą interpretację; starsze raporty pozostają zapisem historycznym. Bieżąca kolejność: [plan rundy z 5 listopada](PLAN-2026-11-05.md).

## Zakres i tryb

Aktywny program: **NASK, edycja 11/2026**. Pozostałe programy nie są bieżącą kolejką. Nie wznawiamy historycznych jobów wieloprogramowych ani monitora Arena.

Operacja dalszego rozpoznawania tras HIVE, kolejnego pobierania modułów i wynikających z tej mapy prób pozostaje wstrzymana na prośbę użytkownika. Dokładna przyczyna komunikatu platformy nie została udostępniona w logu. Sama kolejność zdarzeń nie dowodzi wyzwalacza. Wznowienie projektu nie oznacza ponawiania tej operacji w innym interfejsie.

Po audycie lokalnym wykonano ograniczoną kontrolę zwykłego przepływu publicznego katalogu oraz próbę publicznego wyszukiwania w innym serwisie NASK. HIVE nie było ponawiane.

## Wyniki i kompletność

- Potwierdzone podatności: **0**. Nie wysłano zgłoszenia podatności.
- Baza analizy: 110 obserwacji, 89 dokumentów, 8 159 235 B, 21 powtórzeń zachowanych w pochodzeniu.
- Działający analizator Rust/Rayon + Python FFI: commit `8fc3191`; lokalne kontrole Windows zaliczone, bez nowego wyniku CI dla tego commita.
- Audyt statyczny: cztery przepływy w jednym zapisanym skrypcie klienta; dziewięć lokalizatorów źródłowych i osiem rozliczonych wystąpień właściwości renderowania HTML. Nie jest to pełny audyt hosta ani ocena backendu.
- Kontrola katalogu: jeden zwykły POST zwrócił HTTP 200 z typem HTML zamiast JSON; pozostałe trzy przypadki wstrzymano. Brak poprawnego baseline JSON, bez odczytu treści tej odpowiedzi.
- Kontrola wyszukiwania: jedna próba zakończona błędem transportu bez odpowiedzi HTTP; zapytania kontrolnego nie wykonano. Nie jest to dowód błędu aplikacji.
- W poprzedniej rundzie narzędzie przeglądarki było niedostępne. 5 listopada potwierdzono w UI zmianę strony katalogu, odwrotne sortowanie i filtr „Polska” (10 widocznych rekordów po zakończeniu odpowiedzi). Nie przechwycono ruchu, więc wcześniejsza odpowiedź HTML skryptu pozostaje niewyjaśniona.
- Zwykłe wyszukiwanie „NASK” w science.nask.pl wyświetliło 10 publicznych wyników na pierwszej z sześciu stron. To działający punkt odniesienia, nie wynik testu podatności.
- Dalszą rundę przerwał komunikat zabezpieczenia platformy o 10:12:15 CET. Ostatnią ukończoną operacją był odczyt dokumentacji możliwości przeglądarki; nie rozpoczęto zbierania zasobów. Szczegółowa przyczyna nie została ujawniona (`additionalDetails: null`). Zapis i szkic diagnostyczny zachowano lokalnie, bez wysyłki i bez ponawiania tej ścieżki w innym narzędziu.
- Odróżniamy: kontrakt z kodu klienta, obserwację odpowiedzi, kontrolę własności zasobu oraz powtarzalny dowód skutku. Te poziomy nie są zamienne.

## Gdzie są materiały

| Materiał | Lokalizacja |
| --- | --- |
| Wykonana runda Rust/FFI i korpus | `private/nask-focus-2026-11-04/REPORT.md` |
| Nowy audyt przepływów i rejestr przypadków | `private/nask-dns-review-2026-11-04/REVIEW.md`, `case-ledger.json`, `checks.json` |
| Kontrole zwykłych odczytów i zatrzymania | `private/nask-dns-baseline-2026-11-04/REVIEW.md`, `receipt.json`, `science-search/REVIEW.md` |
| Ocena gałęzi, Drive i korekty twierdzeń | `private/refresh-2026-11-04-1136/REVIEW.md`, `ADOPTION.md`, `claim-ledger.json` |
| Diagnoza dostępnego błędu platformy | `private/nask-focus-2026-11-04/interface-block-latest.json` |
| Przekazanie do CLI | `private/CLI-HANDOFF.md` |
| Aktualny plan i sprawdzenie gotowości przeglądarki | `research/PLAN-2026-11-05.md`, `private/nask-plan-2026-11-05/browser-observation.json` |
| Wykonane interakcje UI i nowe przerwanie | `private/nask-ui-session-2026-11-05/REVIEW.md`, `dns-ui-observations.json`, `science-ui-observations.json`, `interface-block.json`, `FEEDBACK-DRAFT.txt` |

Pliki `private/` są lokalne i nie wchodzą do publicznego repozytorium. Kopia samego GitHuba nie zawiera całego stanu badań.

## Następne decyzje badawcze

Priorytet ma nowy dowód, legalny dostęp do własnych danych albo wiarygodny kontrakt, który usuwa niepewność konkretnej próby. Nie ma obecnie potwierdzonego PoC gotowego do wysłania. Szczegółowa kolejka i warunki są prywatne. Przed przyszłym ruchem należy ponownie sprawdzić aktualny regulamin oraz wspólną koordynację wszystkich aktywnych sesji; osobne repozytoria nie tworzą wspólnego ogranicznika.

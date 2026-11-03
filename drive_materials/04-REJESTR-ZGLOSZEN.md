# Rejestr zgłoszeń — NASK Bug Bounty 11/2026

Uzupełniaj na bieżąco. Ten plik jest jedynym miejscem, gdzie wiadomo, co już zgłoszone
(duplikat = zero nagrody, §7 pkt 8).

## Zgłoszenia wysłane

| # | data | domena | klasa (§8) | CVSS 4.0 | tier | oczekiwana kwota | status | ref |
|---|---|---|---:|---:|---:|---:|---|---|
| — | — | — | — | — | — | — | jeszcze nic nie wysłano | — |

## Kandydaci w toku

| domena | co sprawdzamy | klasa | zmierzony wynik | następny krok |
|---|---|---|---|---|
| `dataannotation.pllum.org.pl` | dostęp do cudzych zadań po ID | 9.2 IDOR | — | dwa konta, mapa endpointów |
| `zglos-dezinformacje.nask.pl` | walidacja uploadu | 7 | — | przepływ zgłoszenia z załącznikiem |
| `zglos-dezinformacje.nask.pl` | pobieranie linku przez serwer | 5 SSRF | — | pole "źródło" + własny endpoint |
| `oad.nask.pl` | omijanie middleware Next.js | 9/12 | test w `naskrecon hypotheses` | sprawdź wersję Next.js |
| `dns.pl` | odczyt danych abonenta domeny | 3.1 | — | wyszukiwarka whois |

## Sprawdzone i PUSTE (nie wracać)

| obszar | co testowano | wynik |
|---|---|---|
| 12 domen × 16 ścieżek | `.git`, `.env`, `actuator`, `swagger`, `openapi`, `/api/users` | **zero** — wszystko catch-all SPA (192 żądania) |
| `nask.pl` | nagłówki, technologia | tylko redirect na www, brak powierzchni |
| `pllum.org.pl` | strona prezentacyjna | statyczna, brak API |

## Stawki przypominacz (§7 pkt 6)

| tier | niska | średnia | wysoka | krytyczna |
|---:|---:|---:|---:|---:|
| **Tier 1** | 600 zł | 4 000 zł | 9 000 zł | **20 000 zł** |
| **Tier 2** | 300 zł | 2 000 zł | 4 500 zł | **10 000 zł** |

NASK dopłaca podatek zryczałtowany — kwota z tabeli to kwota "na rękę" w sensie podatkowym.

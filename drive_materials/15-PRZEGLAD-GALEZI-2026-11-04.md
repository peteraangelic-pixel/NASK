# PRZEGLĄD NOCNEJ PRACY INNYCH SESJI (4.11, rano) + INTEGRACJA

Źródła: gałęzie Pokemon `c87f7a48`/`7911f950`/`a450b00f`, Gemma `6d081d52`/`c4eeb067`,
Smak-Domu `5ed750ef`, repo NASK `arena/a29ca234`(10cbb62)/`codex/multi-program-lab`(a4fb58d).

## Bilans nocy 6 sesji: ~2500+ żądań, **0 potwierdzonych podatności** — powierzchnia anonimowa UTWARDZONA

**Zamknięte (NIE wracać):** `_next/image` SSRF (7 hostów; WAF Azure 403 na zglos/oad/
dataannotation/pllum), traversal/LFI (science downloadFile — 20 wariantów; oad podglad-pdf —
tylko prefiks /media/, 500 bez danych), CORS (brak odbicia Origin na 8 endpointach),
SQLi czasowa/boolean (WAF ucina), ekspozycje statyczne (192 req, 0), sourcemapy (47
bundle'ów bez .map), X-Forwarded-Host, middleware bypass CVE-2025-29927 (4 hosty),
IDOR science `/api/downloadFile` (kontrakt: `fileId` numeryczny; sweep 85 ID → same
publiczne zdjęcia z aktualności), XSS refleksyjny wyszukiwarki, open redirect.
**mwdb = server_version 2.20.0** (sprawdzone u nas 4.11 10:14) → poprawka XSS Rich
attributes (#1272/#1274) WDROŻONA → wątek zamknięty (oszczędzone 10 min konta).

## Żywe leady — WSZYSTKIE wymagają kont usera (zgoda 6/6 sesji)

| # | Cel | Dlaczego | Klasa / stawka |
|---|---|---|---|
| 1 | **hack.cert.pl** (T1) | pełna mapa /api/v1 (nasza, H1–H7) + odkrycie Gemmy: **`/users/me/profile/payout`** (dane wypłat), `/users/{id}/view` | IDOR/BAC = 9–20k |
| 2 | **HIVE dataannotation.pllum** (T2) | FastAPI `/api/v1`; SPA zna `/admin`, `/admin/logs` (guardy TYLKO klienta); `/api/v1/users` → 401; reset hasła (L2: token w query? jednorazowość?) | IDOR/mass-ass = 4.5–10k |
| 3 | **mSzyfr** (T2) | Element Web; bez konta nic nie rozstrzygalne (2 sesje zgodne) | IDOR rozmów = 9–20k |
| 4 | **n6portal** (T1) | NASZA mapa z 4.11: `/login/oidc`, `/oidc/refresh_token`, MFA flow (`/mfa_config/confirm`), `/api_key`, `/search/events/sources`, `/incidents` | authz/MFA-bypass |
| 5 | **dyzurnet.pl / dns.pl** (T1) | API koncepcyjnie jest (`/api/` 308), mapa chunków JS niewykonana (nikt) | 4–9k |
| 6 | **bezpiecznewybory.pl** (T2) | WAF 403 z IP Actions — **testowalne tylko z domu usera** | ? |
| 7 | **secure.edu.pl** (T2) | martwy z Actions (timeout) — sprawdzić z Polski | ? |

Testy poranne Gemmy (do wykonania przez usera, 15 min): ~~mwdb wersja~~ (zrobione: 2.20.0, zamknięte),
**awatar SVG na hack.cert.pl** (stored XSS → klasa 08), **konta HIVE/mSzyfr**.

## Lekcje metodologiczne (przyjęte do naszego warsztatu)

1. **Sonda bez grupy kontrolnej = generator pracy** (Gemma: 706 req → 52 „trafień",
   ~50 fałszywych; porównywać TEN SAM adres z bodźcem i bez, próg ilościowy różnicy).
2. Fałszywa reguła „200+JSON=kandydat" — usunięta u źródła; u nas: verdict Candidate
   wymaga nazwanej klasy regulaminu (u nas już tak jest w endminerze §8-klasyfikatorze).
3. **Rejestr leadów** (wzór c87): lead żyje tylko z klasą z regulaminu + planem PoC
   na własnych kontach + warunkiem odrzucenia.
4. Zawsze nagłówki PRZED `r.bytes()` (bug E0505 z 7911f950).
5. Limiter globalny + audyt `out/requests.jsonl` + weryfikacja hash regulaminów PRZED
   skanem (wzór codex `night-operation`).
6. Rust/Rayon = analiza offline (nasz endminer: słuszny kierunek); przy 5 req/s wąskim
   gardłem jest decyzja co wysłać, nie CPU.
7. **`www.nask.pl` — kwestia literału §5** („nask.pl"): inne sesje nie testują ofensywnie
   www bez wyjaśnienia z organizatorem. Nasz rekonesans GET-owy był ok; testy ofensywne
   → najpierw pytanie przez formularz.

## Stan narzędzi w nask/ (po integracji)

- endminer (Rust+Rayon, offline, §8-klasyfikator): 8/8 testów; **UWAGA: po odtworzeniu
  workspace trzeba `chmod +x bin/endminer`** (snapshot zdejmuje bit x).
- Evidence 20261103: 6 hostów NASK/CERT + mwdb-server.json (2.20.0) + n6portal (main.js).
- Ostatni pomiar: 902 obserwacje (n6portal: 74 — mapa auth/OIDC/MFA/API-key/incidents).

## Podział pracy na dziś (4.11)

- **User (15–30 min, przeglądarka):** konto hack.cert.pl → (a) format ID własnego zgłoszenia
  (test-draft; sekwencyjny czy UUID — decyduje o H1–H7), (b) awatar SVG wg instrukcji Gemmy,
  (c) konta: HIVE, mSzyfr ×2, moje.cert.pl; (d) bezpiecznewybory.pl + secure.edu.pl Z DOMU.
- **Agent (następne tury):** miner na dyzurnet.pl + dns.pl (chunki) → mapy; runbooki H1–H7
  jako instrukcje krok-po-kroku dla usera; draft raportów gotowy przed trafieniem.

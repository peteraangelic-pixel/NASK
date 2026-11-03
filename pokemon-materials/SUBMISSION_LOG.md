# SUBMISSION_LOG

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/SUBMISSION_LOG.md
(pełny plik, pierwszy z 21 chunków — kontynuacja w repo źródłowym)

## Local evidence ledger

Everything below was measured on the real `cabt` engine via `tools/ab_test.py`
(identical deck both sides, sides alternating every game).

| # | Change | Test | Result | Verdict |
|---|---|---|---|---|
| L1 | **GO_FIRST** = go first vs go second | 120 games, BO1 | first player wins **63.3 %** (76–44, z ≈ +2.9) | **adopt** `GO_FIRST = True` |
| L2 | **Variable-damage estimation** (`PTCG_VAR_DMG`) vs raw printed damage | 2000 games, BO1 | **56.65 %** (1113–887, **z = +5.05**) | **adopt** (default on) |
| L3 | Heuristic vs random-move agent | 100 games, BO1 | **94 %** win rate | baseline established |
| L4 | Robustness fuzz vs freshly generated rules-legal opponent decks | 120 + 40 games | 0 exceptions, 0 contract violations | **ship-ready** |
| L5 | Contract check: never return more than `maxCount` | all fuzz games | 0 violations | **ship-ready** |
| L6 | Deck-construction rules (`errorType 4`) | 1431 cards instrumented | 4-copy limit is **by card name**; ≤ 1 ACE SPEC | documented |
| L7 | Local gauntlet: our deck vs 11 auto-assembled archetypes | 200 games/seat | overall 0.748; lose to **2 anti-ex walls** | walls are Phase 2 target |
| L8 | Damage-prevention detection + switch to attacker that can hit | 120 games/seat | overall 0.748→**0.780** | **adopt** |
| L10 | Wall v2: retreat 340 when walled | 60 games/seat gauntlet | overall 0.776→**0.809** | **adopt** |
| L9 | Deck variants: `+2 Boss's Orders` etc. | 120 games/seat | both **worse everywhere** | **reject** |

### Why L2 mattered so much

429 of the engine's 1755 attacks (24 %) print `damage = 0` and put the real
number in the effect text. Our first heuristic scored all of them as zero —
Mega Abomasnow ex's Hammer-lanche (~330 avg damage) was rated *below* the
printed 200-damage Frost Barrier. It was playing the deck backwards.

## Uploads

### 2026-10-09 — FIRST ATTEMPT: both submissions FAILED ⚠️

Root cause: Kaggle does not *import* our module — it compiles and `exec`s it,
so `__file__` does not exist. Our `_candidate_dirs()` touched it outside
try/except → agent died at import time.

**Fix:** `_HERE` computed inside `try/except NameError`; Kaggle absolute paths
tried first. Module-level loads wrapped so import-time failure degrades to
hardcoded fallback.

**New mandatory gate:** `tools/test_kaggle_import.py` unpacks the built `.tar.gz`
and execs `main.py` into a namespace with **no `__file__`**.

### 2026-10-09 — SECOND ATTEMPT: random passed, heuristic failed ⚠️

Root cause: Kaggle's `get_last_callable()` takes whatever callable was defined
**last** in the file — not one named `agent`. Our helpers (`_score_yes_no`)
were defined *below* `agent`, so Kaggle called `_score_yes_no(obs)` and it
blew up on missing arguments.

**Fix:** `agent` moved to the very end of `main_heuristic.py`.

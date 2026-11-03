# DISCOVERIES.md — cross-branch knowledge base

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/DISCOVERIES.md
(pełny plik, pierwszy z trzech chunków)

## 0. TL;DR for agents picking this project up

1. **v11 + 30W (`v12_30_boss4` deck) is the verified optimum** of the heuristic
   family; weight-space search is exhausted (160+ candidates two branches,
   40-parallel screening best 0.684).
2. **v21 (archetype-scan hybrid) is the first config to beat it
   statistically: +1.10pp over 43 600 PAIRED games (≈3.4σ), 12/13 jobs ≥0**.
   Agent: `agents/main_heuristic_v21.py`, bundle
   `bundles/phase1_tuned_v21_hybrid.tar.gz`.
3. **Before v21, every "improvement layer" (v18/v19b) was DEAD CODE** — it
   compared v11 to v11. Rule: if your agent references an undefined symbol and
   has `except: pass` anywhere, it silently no-ops.
4. **Draws vs stall were an infinite Riptide/Hammer self-mill loop**; breaking
   it converts ~12% draws into wins (0.78 → 0.86 vs the stall team).
5. Test methodology: **paired A/B in the same run, ≥600g per critical matchup
   with repeats**. Noise floor ±3pp @600g per matchup; 5–20g numbers are noise.

## 1. DEAD CODE pattern — cross-branch comparisons were void

`agents/main_heuristic_v18.py`, `v19b.py` append a rules layer referencing
`MIRROR_IDS`, `RIPTIDE_ID`, `HAMMER_ID`, `WALL_IDS` — **none of which are defined**
anywhere in the v11 family. The `NameError` is swallowed by `except: pass`,
so the wrapper scores the base result and the agent plays as v11.

**Consequences:** all "v18 vs v11" comparisons on ALL branches were
**v11 vs v11 = noise**. Only v19 (different rules elsewhere in the file) actually
differed — and was a catastrophe (0.591 top30 / 0.536 broad @30g).

## 2. Kaggle loader boundary — wrapper MUST be defined BEFORE `def agent()`

Kaggle's loader picks the LAST function named `agent`-candidate heuristics;
empirically a wrapper function defined AFTER `def agent(...)` gets picked
**instead of `agent`** → submission plays garbage. `build_submission.py --smoke`
catches this ("REFUSING TO SHIP").

## 3. Engine & observation facts (libcg.so FFI, verified)

- Opponent's **deck is NOT visible** (only `deckCount`); their **hand is None**.
- **VISIBLE for archetype scanning:** their active + bench pokemon **ids**,
  their **discard pile** (ids), both players' `deckCount`, `prize` lists,
  statuses, energies on board pokemon.
- `result == 2` = draw. The engine does **NOT** enforce deckout on the draw
  step → if both decks are empty and nobody can take a prize, the game loops
  forever.
- Attack IDs are card_index-scoped: Riptide=1042, Hammer-lanche=1046,
  Frost Barrier=1047, Swirling Waves=1043.

## 4. Draws → wins: the stall mechanism and the fix

**12–16% of games hit step_limit at turn ~1240–1660** with our last Pokemon vs
an energy-less wall, prizes 0–0, both decks empty.

v21 STALL mode:
- Hammer: **−200 when our deckCount ≤ 20**, −40 at ≤30
- Riptide: −120 while deckCount > 12
- +30 to any other attack

Result: draws 12–16% → 7.5%, WR 0.78–0.85 → **0.915**.

## 5. v21 hybrid spec

- Base: v11 unchanged. Thin `_score_main_option` wrapper (defined BEFORE
  `def agent`) adjusts scores; a sticky per-process `_V21_SEEN` set accumulates
  opponent card ids from active+bench+discard each turn (archetype scan).
- Bundle: `bundles/phase1_tuned_v21_hybrid.tar.gz` (built via
  build_submission.py, smoke-passed, loader-check-passed).

## 7. Negative results register

| idea | verdict | evidence |
|---|---|---|
| Weight tuning of v11 family | plateau | 160+ candidates, best 0.684 |
| LOW_E_AGGRO opening rule | ≈v11 | rejected @100g |
| v19 early-gust T0–1 | **catastrophe** | 0.591/0.536 @30g |
| Riptide boost at low deck | **hurts ALL Water decks** | v20: 5/5 worst broad regressions |

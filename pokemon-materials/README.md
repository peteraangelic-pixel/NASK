# pokemon-agent — PTCG AI Battle Challenge (Playground)

Źródło: https://github.com/peteraangelic-pixel/Pokemon, gałąź `arena/a450b00f-pokemon`
Skopiowane pliki kluczowe (nie całe repo — tylko najważniejsze materiały).

Oryginalny opis: praca nad agentem AI do konkursu The Pokémon Company PTCG AI Battle Challenge
(Kaggle). Cel: stabilny, wyjaśnialny agent czyści ~600 rating w Phase 1.

## Pliki w tym katalogu

| Plik | Co zawiera |
|---|---|
| `NOTES_STRATEGY.md` | Dziennik projektowy — uzasadnienia decyzji, nauki z edycji letniej 2026 ($240k), architektura agenta |
| `DISCOVERIES.md` | Baza wiedzy krzyżowa — wyniki 65k+ gier, v21 hybrid, wykrycie dead code w v18/v19b, mechanizm drawów |
| `SUBMISSION_LOG.md` | Rejestr_uploadów Kaggle — hipotezy, wyniki lokalne, błędy packagingu (__file__, get_last_callable) |
| `BENCH_PC.md` | Benchmark PG na własnym PC (Rust + Rayon + FFI) |
| `BENCH_PC_V2.md` | Benchmark v2 — poprawiona metodologia |
| `NOTES_RIEMANN_INSPIRATION.md` | Przeniesienie koncepcji z Kaggriculture (Kaggle $50k) na PTCG: tape opening, self-repairing valve, cow5 vs cow8, Rust port 100x |
| `deck.csv` | 60 kart w talii submisa (Mega Abomasnow ex line) |
| `policy_alakazam_trigger.txt` | Plik wyzwalający iterację polityki Alakazam |
| `policy_iter_trigger.txt` | Plik wyzwalający iterację (count=9) |
| `AUDYT-V13-4-2026-10-30.md` | Audyt duck-v13.4-unified (arc-agi-3) — werdykt, patchy, plan slotów |

## Kluczowe wnioski (TL;DR)

1. **Deck dominuje nad polityką** — meta-counter (rock–paper–scissors) to jedyny udokumentowany dźwignia z dużym эффектem.
2. **Rule-based agent ma sufit ~600–700** — Phase 1 celuje w ~600+, Phase 2 to learning lub search.
3. **GO_FIRST = True** — zweryfikowane lokalnie: 63.3% wygranych dla gracza wybierającego pierwszy ruch (120 gier, z≈+2.9).
4. **Variable-damage estimation (PTCG_VAR_DMG)** — zweryfikowane: 56.65% (z=+5.05) vs raw printed damage.
5. **Dead code w v18/v19b** — wrappery z `except: pass` ukrywają NameError; wszystkie porównania v18 vs v11 to v11 vs v11 = szum.
6. **Rust port symulatora** — 100x speedup (0.01s/gra vs 1.5s Python), ale crashe przy pełnym buforze na 2 vCPU.

# Benchmark PC v2 — Rust + Rayon + FFI (metodologia v2)

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/BENCH_PC_V2.md

Wersja v2 mierzy ten sam rzeczywisty workload PG (policy_rollout + konwersja +
trening), ale z poprawioną metodologią:

| aspekt | v1 (stary) | v2 (ten) |
|---|---|---|
| pomiar per jobs | 1 bieg, stałe 8000 gier | warm-up + partie do min. 60 s, mediana/min/max |
| skalowanie | same g/s | g/s + efektywność vs baza |
| obciążenie | mirror jednej talii | mirror + produkcyjna pula PG |
| miara pracy | gry/s | gry/s + decyzje/s + MB rolloutu |
| koszt loopa | epoka + zgadywane +30 s | zmierzone etapy: rollout→convert→train→export |
| walidacja | brak | valid==games, liczniki błędów silnika == 0 |
| raport | tekst | tekst + JSON z metadanymi maszyny i kodu |

## Uruchomienie

```bash
cd Pokemon/pokemon-agent
bash tools/bench_pc_v2.sh
```

Czas: typowo 10–20 minut.

Zmienne: `BENCH_JOBS`, `BENCH_BATCH_GAMES`, `BENCH_MIN_SECONDS`, `BENCH_MAX_BATCHES`,
`BENCH_WARMUP_GAMES`, `BENCH_POOL`, `BENCH_TRAIN`, `BENCH_REPORT`.

Wynik, który warto wkleić: blok `SUMMARY bench_pc_v2` albo cały plik JSON z `BENCH_REPORT`.

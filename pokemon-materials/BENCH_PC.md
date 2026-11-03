# Benchmark PG na własnym PC (Rust + Rayon + FFI)

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/BENCH_PC.md

Mierzy dokładnie to obciążenie, które liczy łańcuch policy-gradient:
generowanie gier self-play silnikiem `policy_rollout` (Rust, Rayon,
FFI do `libcg.so`) + jedną epokę treningu JAX. Na końcu wypisuje tabelę
`SUMMARY` z czasami dla 240 tys. i 1,6 mln gier.

## Wymagania

- Linux albo WSL2 (`libcg.so` to linuksowa biblioteka ELF)
- Rust: https://rustup.rs (`cargo --version` ma działać)
- Python 3.11
- ~4 GB wolnego miejsca

## Uruchomienie

```bash
git pull
cd Pokemon/pokemon-agent
bash tools/bench_pc.sh
```

Całość trwa zwykle 5–15 minut.

## Co mierzymy

- **rollout train-mode** — generowanie danych PG (~cały koszt „gier”)
- **eval-mode** — odpowiednik bramek (argmax)
- **1 epoka treningu PG** na prawdziwym `rollout.npz` (91 MB)

## Jak czytać wynik

- `best rollout = X g/s @ N jobs` — skalowanie Rayona na Twojej maszynie;
  w GitHub Actions mamy ~70 g/s przy 4 jobs.
- `1.6M total (40 iters) = T h` — realistyczny czas całego PG z treningiem.

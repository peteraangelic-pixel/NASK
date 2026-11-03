# Inspiracje z repo riemann (Kaggriculture) → PTCG

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/NOTES_RIEMANN_INSPIRATION.md

Przejrzane gałęzie: `arena/01a06bce`, `01a075fa`, `01a087c0` itd. – tam był konkurs Kaggle
**Kaggriculture** (2 graczy, 720 tur, $50k, 5 sub/dzień, liczą się 2 ostatnie – identyczny
format jak PTCG Playground).

## Co działało w Kaggriculture i jak przenieść na PTCG

### 1. Scripted tape vs reactive – 2x różnicy
Najlepsze agenty to były **frozen tape**: pre-komputowane optymalne sekwencje (opening +
zapis gry elitarnego gracza), skompresowane zlib+base85, ~140-147k cash.
Reactive policies – ~70k, czyli 2x gorzej.

**Wniosek PTCG:** Nasz heuristic jest reactive. Top decki PTCG to trochę jak tape –
zoptymalizowany deck + opening (T1 Snover, T2 Aboma). Możemy zrobić **tape opening**:
np. jeśli ręka startowa ma Snover + Water, zawsze zagraj Snover na bench, a dopiero potem
przełącz na reactive.

### 2. Stable foundation (pszenica) vs premium (marchew, melon)
**Przeniesienie PTCG:**
- **Water 34W = pszenica** – stabilny fundament, 34W daje 340 dmg, odporny na Hammer.
- **Boss x4 = marchew** – premia za deficyt gustu, areał dobierany do widocznego popytu.
- **Powerglass / Cyrano = melon** – wysoka marża, ale limitowana.

### 3. Rust port – 100x speedup
Port wyłącznie symulatora, sweep i statystyki zostają w Pythonie. Rust dostaje rozpakowane
taśmy JSON. Weryfikacja: SHA źródeł, cash bitowo jako binary64, pełne stany tur, Rayon
1 vs wiele wątków identyczne jako bajty JSONL.

**PTCG:** Przenieść heurystykę do Rusta i wołać `libcg.so` via `libloading` + Rayon –
wtedy 100x (0.01s/gra vs 1.5s Python).

## Konkretne pomysły do zaimplementowania w PTCG

1. **Tape opening**: Jeśli opening hand ma 2x Snover + Water, zawsze zagraj Snover na bench T1, Aboma T2 – frozen sekwencja, potem reactive.
2. **Self-repairing valve**: Sadź Powerglass tylko gdy discard Water>=1 i active Kyogre.
3. **Cow5 vs Cow8**: Przetestuj Pad2 vs Pad1, Night1 vs Night2 – więcej nie zawsze lepiej.
4. **Full Rust port**: Przenieść `_score_generic_context` do Rusta, wołaj `libcg.so` via libloading.
5. **Adversarial benchmark**: Róbmy sweep jak w Kaggriculture: `jobs.csv` z seed,tape_a,tape_b,reverse, Rayon 16 threads.
6. **Conditional families**: Jeśli opp ma 35W → więcej draw (Pad2 Cyrano1), jeśli opp ma Hammer x4 → więcej Boss.

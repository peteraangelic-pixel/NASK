# NOTES_STRATEGY — why this agent is built the way it is

Źródło: Pokemon arena/a450b00f-pokemon, pokemon-agent/NOTES_STRATEGY.md
(pełny plik, pierwszy z dwóch chunków pobrany — kontynuacja w repo źródłowym)

## 1. The setup, and what we are actually optimising

The leaderboard is a **Gaussian skill estimate N(μ, σ²)** seeded at μ₀ = 600, not a
win rate. Three consequences that shape the whole project:

* **σ matters as much as μ early on.** New submissions get a higher episode rate to
  shrink σ fast, so the first day of a new submission is the cheapest information we
  will ever get. Day-1 noise must not be over-interpreted.
* **Margin of victory is irrelevant** — only win/draw/loss updates μ. So there is no
  reason to play for style or speed, and every reason to play for *stability*: one
  crash costs a whole submission slot (5/day).
* **Only the latest 2 submissions are live.** A new submission does not just add an
  agent, it *retires* an older one. So we should never "just try something" with both
  slots occupied by something known-good — the cost of a bad experiment is losing a
  working agent.

**Therefore the prime directive is: never Error.** An agent that is mediocre but
never crashes accumulates μ. An agent that is brilliant but crashes on one rare
observation shape loses the entire run.

## 2. What we learned from the summer 2026 (paid) edition

The playground is a continuation of `pokemon-tcg-ai-battle` (simulation, 6,807 teams)
and `pokemon-tcg-ai-battle-challenge-strategy` ($240k, judged on writeup quality).
Public writeups — this is the highest-value research we have:

### 2.1 The proven lever is the *deck*, not the policy  **[reported]**

One team's project notes are blunt: *\"The ONE proven lever: meta-counter
(rock–paper–scissors). Dragapult > Trevenant > Alakazam > Dragapult. Read replays →
find the rising archetype → ship its counter, do NOT mirror it.\"* Their own attempt
to mirror the meta *flopped at 460*, while shipping the counter hit ~900–978.

Another team reported that **53 % of their losses were structural** — decided by the
matchup, before any play decision. And the 1st-place simulation solution spent a large
part of its effort on **deck archetype clustering and card-by-card mutation** rather
than only on the network.

**Implication for us:** policy quality has a ceiling set by the deck. Our Phase 1
should therefore not be judged only by \"does the heuristic play well\", but by
\"is this deck worth playing well with\". Deck work is Phase 2's first item.

### 2.2 Rule-based agents ceiling at ~600–700  **[reported]**

A team that deliberately went rule-based (and chose the *same* Mega Abomasnow ex deck
we start on) reported: *\"climbed to a stable rating of around 600, winning roughly
50–60 % of its matches… around 600–700 the bot stops improving because it cannot look
ahead.\"* This independently validates the user's Phase 1 target of ~600+ and tells us
the Phase 2 trigger: **when μ stalls near 650, stop tuning rules.**

### 2.3 Hand-written rules *hurt* the top RL agents  **[reported]**

7th place: *\"hand-written rules and mechanical teachers — every one we tested cost win
rate, by up to 36 points. Our reading: a rule covers only the cases we thought of, and
training writes the rest into the weights as error.\"*

This is **not** an argument against our Phase 1. It is an argument about *where rules
belong*: they cost a top-tier learned policy because the policy can already learn the
case; they *help* a Phase 1 agent that has no policy at all. The same team kept exactly
one class of hand-written logic at inference — **a lethal check** — because *\"lethal
detection is computation, not strategy\"*. That distinction is the design line we should
copy: **hand-code computation (rules of arithmetic), learn judgement.**

### 2.4 Feature exposure beat feature engineering  **[reported]**

7th place again: *\"When the policy played badly, we looked for a quantity it could not
see rather than a rule to impose… The line that added the knockout distance gained 4.3
points of win rate (z=2.5 over 1,500 games per arm).\"*

### 2.5 Sample-size discipline  **[reported]**

*At least 500 games per opponent are needed.* 1,500 games per arm is the bar for a
feature decision. Our local arena runs a full BO1 game in ~0.15 s, so 2,000 games ≈ 5 minutes.

### 2.6 Going first is worth ~6–8 points of win rate  **[verified, ours]**

A/B'd our own agent against itself with only the `IS_FIRST` answer flipped:
**76–44 over 120 games = 63.3 % for the player who chooses to go first** (z ≈ +2.9).

### 2.7 A trap worth remembering  **[reported]**

Playing cards whose *cost* it could not pay (Buddy-Buddy Poffin with fewer than 2 Basic
Pokémon in hand, or a search card whose target was already in hand). Engine offers legal
options but *pre-condition* checks are on us.

## 3. Architecture decisions

### 3.1 Single-file, stdlib-only agent  **[decision]**

`main.py` imports nothing but `json`, `os`, `random`, `re`. The card database is a
separate `card_index.json` (443 KiB, 1,431 cards + 1,755 attacks). If it fails to load,
the agent still plays legally — all lookups degrade to neutral defaults rather than raising.

### 3.2 Bands, not weights  **[decision]**

Scores are **bands with a hard ordering**:
```
340  play a Supporter (draw / search)
330  play an Item (search / utility)
320  put a Basic on the Bench
310  evolve
300  attach Energy / Tool
290  play a Stadium
270  use an Ability
260  attack that takes a prize
200  any other attack
120  retreat
 20  discard / junk
  0  end turn
```
Every setup band is strictly above every attack band.

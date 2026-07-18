# team-02 — IS Report

Submission family: `t02-breakout-channel-v2` (approved pivot). All Part-II numbers below are
sourced EXCLUSIVELY from `out/is_metrics.json` as produced by
`cli.py team-run --team team-02` (schema 1, window 2020-01-01 → 2024-07-01 exclusive).
Part-I numbers are scratch-evaluator provenance (same engine, pre-QE), labeled as such.

## Part I — Registered family `t02-oi-crowding-fade-v1`: honest negative (falsifier FIRED)

Full documentation: `research_brief.md` §1-§9; ledger `experiments.jsonl` e01-e06 (7
evaluator-stamped entries). Provenance: scratch evaluator runs, NOT team-run — no strategy
was built from this family. Summary of record: all 10 core-grid cells negative @1×
(A: −1.45..−1.66; B: −0.80..−2.15); gross (cost-free, funding-off) Sharpe negative in every
decomposed config (−0.25..−0.94) ⇒ signal-failure, not cost-failure; stagnation form C,
inverse-vol, and equal-weight rescues all negative; even the reverse sign is net-negative
(−0.65/−0.34) — no tradable 8h edge of either sign in the OI panel at tournament costs.
Material data finding for the record: real OI-panel breadth begins ~Dec-2021, not 2020-09
(0-1 eligible names with OI until 2021Q3; ~40 from 2022Q1). The pivot was requested,
approved, and journaled at choice time.

## Part II — Submission: breakout/channel (`t02-breakout-channel-v2`)

Signal (fixed in brief §II.8): per-name 60-candle close-channel position, deadband 0.25,
EMA span 6 — price-only, no aux usage, no cross-sectional transform.

### Headline (team-run, `out/is_metrics.json`)

| Metric | @1× | @2×-stress |
|---|---|---|
| Net IS Sharpe (monthly, √12, after all costs + funding) | **+2.0687** | **+1.8214** |
| MaxDD | −28.84% | −31.05% |
| Total return (vol-targeted, compounded) | +1946.5% | +1300.1% |
| Ann. turnover | 123.88 | 123.88 |
| Months | 54 | 54 |

### Breadth vs floor (Critic-checked floor: median ≥ 5 names/side)

Median names long/short = **17.0 / 18.0** — comfortably above the floor. Mean gross 0.830,
mean net −0.0073 (the engine's net cap makes the held book effectively market-neutral).

### Per-regime Sharpe

| Bucket | @1× | @2×-stress |
|---|---|---|
| bull | +3.0235 | +2.8362 |
| bear | +1.4888 | +1.2367 |
| chop | +0.3130 | +0.0208 |

No negative bucket at either tier; bull-heaviest as pre-registered (§II.5). Chop is the
weak bucket and is essentially break-even at 2×-stress — stated plainly.

### Funding & costs

Total funding P&L +0.0257 vs total cost 0.3503 @1× (0.7006 @2×): funding is a rounding
error either way — the edge is price behavior, not carry (funding-off scratch check e11:
Sharpe +2.04 vs +2.07).

### Stability (scratch provenance, e11 ledger entry)

Half-sample Sharpe: **+3.17** (2020-01→2022-03) vs **+1.14** (2022-04→2024-06). Both
positive; the recent half is materially weaker. Yearly net: 2020 +1.33, 2021 +1.04,
2022 +0.19, 2023 +0.83, 2024H1 −0.09. Worst months −13.8% (2022-02), −13.3% (2023-02),
−11.6% (2020-05). Parameter plateau: all 8 core-grid cells positive at both tiers
(N ∈ {30,60,90,180} × forms D/E); selection was rule-mechanical (brief §II.7 audit trail),
including one rejected refinement (inverse-vol) and one non-override (N=60 kept over
post-hoc-better N=90).

## Honest expectations for the sealed holdout

The full-window +2.07 is flattered by 2020-21, when crypto trends were exceptional. The
right run-rate prior for 2024-07→2026-06 is the recent-half figure — **nearer 1 than 2** —
because the holdout era likely contains more chop (our weakest bucket, +0.31 @1×, ~0 @2×)
and post-2021 trend edge is thinner. What would NOT surprise us: Sharpe in the 0.5-1.5
band, a −25..−35% drawdown episode, extended flat stretches in ranges. What WOULD surprise
us and challenge the mechanism: a deeply negative holdout (< −0.5) over the full 24 months
— that would say range escapes on top-40 perps have stopped propagating trend at 8h scale,
not merely that trends were scarce. We accept the chop bleed as the structural price of the
family's trend convexity; we did not tune it away, because every anti-chop patch we could
add is a new degree of freedom the holdout would audit.

## Provenance of every number

- Part II headline/regime/breadth/funding/cost tables: `out/is_metrics.json` (team-run).
- Part I negatives + Part II stability split: scratch evaluator runs logged in
  `experiments.jsonl` (e01-e06, e11) and documented in `research_brief.md` §9 / §II.7 —
  labeled scratch provenance; not team-run artifacts.

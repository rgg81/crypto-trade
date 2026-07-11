# MN4 IDEA-05 — Phase-B REVEAL

**Construction:** Kalman Stat-Arb on Major Pairs (10 majors, 45 pairs, KF-adaptive
hedge, rolling-z signal, rolling-ADF structural-break kill-switch, rank_neutral
daily rebal, BTC-vol Layer-2 crisis throttle).
**Authorization:** Orchestrator directive + user "reveal all 10" Phase-B mandate. OVERRIDES Phase-A IS-only.
**Window:** [2024-07-01, 2026-07-01) — sealed 2-year holdout. ONE look, single-use forever.
**Stage-3 guard:** No candle with `open_time >= 2026-07-01` was read (panel load hard-codes `grid_ms < MN3_HOLDOUT_END_MS = 1782864000000`; asserted at runtime).
**Model:** Opus 4.8 (Claude). Disclosed per charter §"Model".
**Token:** MN4-05 (spent; marker at `data/mn4_reveal/spend_MN4-05.json`).

## What was re-run

The FROZEN byte-exact Phase-A construction (`mn4_idea05_kalman.py`,
`mn4_idea05_run.py` — no code changes, no threshold adjustments, no re-fitting).
The KF state carries continuously from IS into holdout — the natural deployment
interpretation (at 2024-07-01 you would have IS history loaded; the KF doesn't
cold-start). The engine backtest runs over the IS+holdout panel; **all metrics
below are SLICED to the holdout window only**.

## Holdout scorecard

| Metric | Holdout (1× cost) | Holdout (2× cost) | IS reference (1×) |
|---|---|---|---|
| **Sharpe** | **−2.28** | **−4.66** | −2.91 |
| MaxDD | −48.2% | −74.0% | −90.2% |
| Ann return | −28.0% | — | −39.4% |
| Ann vol | 13.9% | — | — |
| Turnover (annualized one-way) | 460× | — | 436× |
| Per-trade gross edge | **−0.14 bps** | — | −3.10 bps |
| Funding drag (cumulative) | −164 bps | — | −133 bps |

### Per-half Sharpe (holdout)

| Half | Sharpe |
|---|---|
| 2024-H2 | −4.19 |
| 2025-H1 | −0.67 |
| 2025-H2 | −2.56 |
| 2026-H1 | −2.34 |

All four halves negative. 2025-H1 (the choppiest half) was the "least bad";

no half found a profitable regime.

### Regime buckets (holdout, mean per 8h candle)

| Bucket | n | book_mean | btc_mean | β ratio |
|---|---|---|---|---|
| CRASH | 302 | −0.00042 | −0.00230 | +0.18 |
| CHOP  | 1794 | −0.00026 | +0.00019 | −1.36 |
| MANIA | 93 | −0.00055 | +0.00305 | −0.18 |

**Rolling β_BTC over holdout: mean −0.010, max +0.028, min −0.061** — the book
IS market-neutral by construction (the bucket-ratio numbers are noisy because
both numerators and denominators are small per-candle means; the rolling β is
the proper measure).

### Other holdout diagnostics

| Metric | Value |
|---|---|
| # pairs traded | 45 / 45 |
| Avg active pairs / rebal | 22.5 |
| Kill-switch alive fraction | 0.501 |
| Crisis throttle (flat / half / full) | 0 / 16 / 2173 |
| n holdout candles | 2189 (after dropping the engine's stale final index) |

The kill-switch + crisis throttle both fired as designed on holdout (kill-
switch alive 50.1%, slightly higher than IS's 41.3%; crisis throttle never
went flat — BTC vol stayed below the 3× threshold for the entire holdout,
fired 16 half-stress candles).

## Gate verdict (vs FROZEN Phase-A gates; no re-gating)

| Gate | Threshold | Holdout value | Verdict |
|---|---|---|---|
| 1. Sharpe 1× cost > 0.0 | > 0.0 | **−2.28** | **FAIL** |
| 2. Sharpe 2× cost > 0.0 | > 0.0 | **−4.66** | **FAIL** |
| 3. Per-trade gross edge > 7.5 bps | > 7.5 bps | **−0.14 bps** | **FAIL** |

**OVERALL: FAIL.** The construction is CLOSED. No rescue, no second reveal.

## Honest generalization read

The null **generalizes cleanly**. The IS Sharpe was −2.91; the holdout Sharpe
is −2.28 — same sign, same order of magnitude, no sign-flip. The per-trade
gross edge went from −3.10 bps (IS) to −0.14 bps (holdout) — actually *less*
negative on holdout, but still far below the +7.5 bps cost-coverage threshold.
The strategy never found a positive regime in either window.

The mechanism documented in the IS diary — the apparent KF state-aware spread
reversion being largely a 1-candle leak artifact of the KF's own state update,
with the tradeable entry-β-frozen edge being negative — held exactly on
holdout. No surprise, no inversion, no "the edge appeared in a new regime."
The four-half breakdown confirms: no half was positive; 2025-H1 was the
"least bad" at −0.67 (still negative); 2024-H2 was the worst at −4.19.

The book IS market-neutral by construction (rolling β_BTC mean = −0.010,
max +0.028 on holdout), so the failure is NOT a hidden BTC exposure — it is
the per-pair anti-edge plus the structural 460× turnover cost drag that the
IS diary already documented. The construction's neutrality design worked
exactly as intended; the underlying signal just is not there at daily cadence
on crypto majors.

This is the methodology working as designed. The IS diagnostic predicted a
holdout null, the holdout null is what we observe, and the token is spent.
The diagnostic finding (state-aware spread IC overstates tradeability — the
core lesson from `data/mn4_idea05/holdout_results.json` and the IS diary)
remains a contribution to the dead-paths record that protects future stat-arb
work in this track.

## Files

- `analysis/portfolio/mn4_idea05_reveal.py` — reveal runner (byte-exact frozen construction on IS+holdout panel, sliced to holdout for scoring)
- `data/mn4_idea05/holdout_results.json` — full holdout scorecard
- `data/mn4_reveal/spend_MN4-05.json` — token spend marker
- `data/mn4_idea05/pair_features.npz` — KF features cached on IS+holdout panel (T=7119 candles)

## Final Verdict

**FAIL on every frozen gate. The null generalizes. The construction is closed.**

Per the charter's HONEST PRIOR ("expect most of the 10 to fail; a FAIL on the
holdout is the methodology working, not a disappointment") this is one of the
failures, and the IS→holdout consistency is itself a positive methodological
signal (the IS analysis was not overfit — it correctly predicted OOS failure).

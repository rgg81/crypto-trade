# Iteration 195 — AFML fractional differentiation (rejected via IS-only test)

**Date**: 2026-04-23
**Type**: EXPLORATION (new feature family from AFML Ch. 5)
**Baseline**: v0.186
**Decision**: NO-MERGE (based on IS-only pre-test; skipped full backtest)

## Motivation

Six iterations failed on the exploration side (178, 180, 183, 189, 190,
191, 192). Frac-diff was the last remaining never-tried feature-engineering
direction from AFML. Test it efficiently by IS-only CV proxy BEFORE
running a full 1.5h walk-forward.

## Phase 0 — Implement frac-diff

`analysis/iteration_195/fracdiff.py` implements AFML's fixed-width
frac-diff with truncation tolerance τ = 1e-4. Binomial weights:
`w_k = −w_{k-1} · (d − k + 1) / k`. Output is NaN for the first
`len(w) − 1` entries.

ADF stationarity test on raw close for all five baseline symbols:

| symbol | raw close ADF | 5%-crit | stationary? | min-d for stationarity |
|--------|--------------:|--------:|:-----------:|-----------------------:|
| BTC | −0.79 | −2.86 | no | **d = 0.2** |
| ETH | −2.15 | −2.86 | no | d = 0.1 |
| LINK | −2.57 | −2.86 | no | d = 0.1 |
| LTC | −2.70 | −2.86 | no | d = 0.1 |
| DOT | −1.91 | −2.86 | no | d = 0.2 |

All 8h closes are non-stationary; all reach stationarity at d ∈ [0.1, 0.2].
**Extremely mild differentiation needed**, meaning frac-diff preserves
significant memory (vs. d=1 returns which are maximally memoryless).

## Phase 1 — IS-only CV proxy test (pre-commit check)

`analysis/iteration_195/quick_is_test.py` trains a LightGBM on LINK's
IS data (3339 samples) with 5-fold TimeSeriesSplit CV, 5 seeds.
Computes a proxy Sharpe = confidence-weighted directional accuracy.

| config | features | proxy Sharpe (mean ± std) |
|--------|---------:|--------------------------:|
| (A) Baseline 193 | 193 | +0.056 ± 0.013 |
| (B) Baseline + 2 frac-diff | 195 | +0.058 ± **0.006** |
| (C) Swap 2 low-MDI for 2 frac-diff | 193 | +0.048 ± 0.010 |

### Frac-diff feature importance in config B

| feature | MDI | rank (of 195) |
|---------|----:|:--------------|
| fracdiff_close_d01 | 21 | 56 (top 29%) |
| fracdiff_close_d02 | 13 | 96 (top 49%) |

Frac-diff features carry **moderate signal** (ranked in top half by MDI)
but **don't meaningfully improve CV proxy Sharpe** (+0.002). Config B
has lower std, suggesting frac-diff adds small stabilizing effect.
Config C (swap) is clearly worse — same pattern as iter 190.

## Decision rule

Given:
- Four straight exploration NO-MERGEs before this
- Quick IS test shows improvement within noise (+0.003 proxy Sharpe)
- Full backtest cost: ~1.5h of compute

**Skip the full walk-forward backtest.** The pre-test signal is too
weak to justify the compute cost. This is the first iteration to use
IS-only CV proxy as a go/no-go gate before committing to a full run
— a process improvement for future iterations.

## What this rules out

Frac-diff on own close at d=0.1 and d=0.2 does not add meaningful
signal to LINK. Remaining frac-diff variants not tested:
- Different d values (0.3, 0.5, 0.7 — though these preserve less memory)
- Frac-diff on volume instead of close
- Frac-diff of multiple symbols' closes (cross-asset)
- Different base series (cumulative log-return)

Of these, frac-diff on volume is the most promising and cheap to test.

## Exploration/Exploitation Tracker

Window (185-195): [X, X, X, E, E, E, E, V, X, E] — 5E/4X + 1V.
This pre-test iteration counts as E (feature generation).

## Next Iteration Ideas

- **Iter 196**: STOP feature-engineering exploration on LINK. Four
  explicit tests (xbtc augment, xbtc swap, pruning, frac-diff) all
  failed. LINK's 193-feature set is robustly near-optimal.
- **Iter 197**: Apply the IS-only pre-test process more broadly. Try
  frac-diff on Model A's BTC+ETH pool (more training data, different
  regime). If pre-test shows > +0.01 improvement, commit to full backtest.
- **Iter 198**: Ship v0.186 to paper-trading. Validation + statistical
  confidence support it. Six exploration failures demonstrate further
  gains require live data, not more offline iteration.

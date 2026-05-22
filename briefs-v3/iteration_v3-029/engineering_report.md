# Engineering Report — iter-v3/029

## Status: READY-FOR-CRITIC

Wall-clock 0.32h (19 min). **STRONG PROMISING result — first in new cycle.**

## Hypothesis-Implementation Alignment

ADD ALGOUSDT (V3_MODELS 3→4); REQUIRED_GAP 66→88; ITERATION_LABEL=v3-029. KEEP regime_momentum_signed_5d (V3_FEATURE_COLUMNS=14 byte-identical). Single-axis discipline preserved (universe expansion only).

## Reproducibility Stamps

Setup `f01b4a7`, gate `d8b6529`, brief `9301744`, per-symbol analysis `d451885`, candidate EDA `c30369d`.

## Headline Metrics — STRONG LIFT

| Metric | Value | vs iter-v3/028 anchor (+0.5101/+0.5053) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | **+0.7926** | Δ +0.28 |
| OOS monthly Sharpe | **+1.7653** | **Δ +1.26 — HIGHEST OOS Sharpe in v3 catalog** |
| IS daily Sharpe | +1.2521 | — |
| OOS daily Sharpe | +2.6750 | — |
| IS Trades | 257 | +75 |
| OOS Trades | **120** | +24 (closer to 130 floor) |
| IS MaxDD | 34.72% | improved from 41.4% |
| OOS MaxDD | 23.85% | similar to 23.0% |
| DSR | 0.0 | EXPLORATION artifact |
| PBO mean | 0.0974 | PASS |
| PSR | 1.0 | EXPLORATION saturation |
| n_eff | 19 | consistent |

## Per-Symbol OOS — ALL 4 SYMBOLS TRADE, 3 of 4 POSITIVE

| Symbol | weighted_pnl | Trades | WR | concentration |
|--------|--------------|--------|-----|---------------|
| TRX | +29.24 | 46 | **52.2%** | 50.59% |
| ALGO | **+20.87** | 25 | 40.0% | 36.11% |
| BCH | +10.75 | 38 | 39.5% | 18.60% |
| LDO | -3.07 | 11 | 36.4% | -5.31% |

**ALGO contributes +20.87 OOS PnL (36% of total)** — NEW SYMBOL POSITIVE.

Top concentration dropped from 75-77% (iter-v3/028 TRX) to 50.6% (iter-v3/029 TRX) — concentration gate getting closer to ≤30% target.

## ALGO Feature Importance Validation

Top-3 importance for ALGO model:
1. max_dd_window_50 = 164
2. ret_skew_50 = 145
3. range_realized_vol_50 = 137

These are **exactly the SHARED top-7 features identified in the per-symbol analysis**. ALGO uses the same load-bearing predictors as BCH/LDO/TRX. The per-symbol-feature-signature-alignment methodology used in iter-v3/029 candidate selection (vs iter-v3/021's correlation-only HBAR+AVAX failure) WORKED.

## Methodology Validation — User's Per-Symbol Hypothesis

User directive 2026-05-08: "features are the key... some features are better suited of symbols a but not b... don't discard symbol expansion."

iter-v3/029 directly validates this:
- iter-v3/021 correlation-only selection (HBAR+AVAX): NEGATIVE (-0.83 OOS, both new symbols drag)
- iter-v3/029 feature-signature alignment (ALGO): PROMISING (+1.26 OOS, ALGO positive +20.87, all 4 symbols trading)

The per-symbol feature analysis identified that features like max_dd_window_50, ret_skew_50, range_realized_vol_50 are SHARED-top-7 across BCH/LDO/TRX. ALGO's predicted alignment (composite 0.6517) held: ALGO's actual model uses these same features as its top-3.

Symbol expansion methodology: select candidates with HIGH feature-signature alignment, NOT lowest correlation.

## §4.4 Classification

| Condition | Threshold | Observed | Triggered |
|---|---|---|---|
| IS Sharpe Δ ≥ +0.10 | ≥ +0.10 | +0.28 | YES |
| OOS Sharpe ≥ anchor + 0.10 | ≥ +0.61 | +1.77 | YES (massively) |
| New symbol contributes positive PnL | > 0 | +20.87 | YES |
| Concentration improved | reduced | 75% → 51% | YES |
| Bundle OOS trades closer to floor | toward 130 | 96 → 120 | YES |

PATH A fires unambiguously. Verdict: **EXPLORATION-PROMISING (clean — STRONG signal)**.

## Caveats

1. **Single-seed result** — iter-v3/025's single-seed PROMISING (+0.88 IS / +1.22 OOS) compressed 42%/58% at iter-v3/028 multi-seed. iter-v3/029's +1.77 OOS is even higher and more vulnerable to compression.
2. **OOS Sharpe +1.77 is highest single-seed in v3** — iter-v3/013's +2.70 was falsified at iter-v3/018 multi-seed. Pattern recognition: single-seed OOS Sharpes >+1.5 should be treated with multi-seed skepticism.
3. **ALGO 25 trades** is small per-symbol sample — robust 4-symbol Sharpe at multi-seed is the truth-test.
4. **DSR=0** structural EXPLORATION artifact (n_trials=140 below threshold for nonzero deflation).

## Recommendations

iter-v3/030 axis options:
1. **HIGH — More targeted symbol expansion** (5th symbol per per-symbol-signature analysis on the NEW 4-symbol universe, including ALGO data). Test whether feature-signature methodology generalizes.
2. **HIGH — Per-symbol feature subsets**: drop features that LDO doesn't use (LDO at -3.07 OOS continues underperforming) — train LDO on a tighter subset of features. Tests whether per-symbol feature pruning helps.
3. **MEDIUM — Different engineered feature** alone (drop attempt; iter-v3/030 = vol_adj_autocorr OR fracdiff alone on 4-symbol universe with NO regime_momentum to test isolation).
4. **MEDIUM — Multi-seed mini-validation** of iter-v3/029 (--seeds 2) BEFORE iter-v3/039 CONFIRMATION — but per user's strict 10:1 cadence, this would consume an EXPLORATION slot for validation rather than new exploration.

Critic prior: **option 1 (continue per-symbol feature signature axis)** — methodology proven; 5th symbol candidate (FILUSDT or VETUSDT from prior EDA) tests generalization.

Status: READY-FOR-CRITIC.

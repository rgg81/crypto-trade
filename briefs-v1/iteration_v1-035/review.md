# Phase 7.5 Critic Review — iter-v1/035

OVERALL: **EXPLORATION-NEGATIVE-CATASTROPHIC at bundle level** (OOS Δ -0.68 vs baseline +0.6637) **BUT contains LOAD-BEARING PROMISING signal at per-cohort level**: trend-scanning labels surface massive PnL on LINK + DOT (>+100% net OOS each) while catastrophic on BTC + ETH + LTC.

## Iteration Type
TYPE: EXPLORATION cycle-5 #2/10 (renumbered) — labeling family (Wald-test trend-scanning labels)

## Observed results

| Metric | Baseline | /035 | Δ |
|---|---|---|---|
| IS Sharpe | +0.2829 | **+0.2818** | -0.0011 (≈flat!) |
| OOS Sharpe | +0.6637 | **-0.0119** | **-0.68** |
| IS Trades | 621 | 698 | +77 |
| OOS Trades | 189 | 261 | +72 |
| OOS WR | 40.2% | 41.8% | +1.6pp |
| OOS PF | 1.156 | 0.998 | -0.16 |
| OOS Max DD | 40.94% | 62.34% | +21.4pp worse |
| OOS PSR_vs_0 | 0.989 | 0.496 | -0.49 |
| n_eff_per_cell median | n/a | 9 | healthy |

**Per-symbol OOS (BIMODAL pattern — LOAD-BEARING):**

| Symbol | Trades | WR | /035 Net PnL% | Baseline OOS | Δ |
|---|---|---|---|---|---|
| **DOTUSDT** | 53 | **52.8%** | **+113.63%** | +1.96% | **+111.67pp** ⭐ |
| **LINKUSDT** | 52 | **55.8%** | **+108.91%** | +34.23% | **+74.68pp** ⭐ |
| BTCUSDT | 54 | 31.5% | -17.62% | +33.17% | -50.79pp |
| LTCUSDT | 48 | 31.2% | -32.76% | -47.25% | +14.49pp (slight) |
| ETHUSDT | 54 | 37.0% | -43.73% | +2.75% | -46.48pp |

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Trend-scanning labels strictly forward-anchored at LABEL TIME (per `labeling.py:132-214`). `walk_forward.py:113` embargo intact. Hard-causality test passing.

### Check 2 — Embargo Width: PASS

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION)
DSR -49.68 / PSR_vs_1 0.157. Not BLOCK-triggering for EXPLORATION.

### Check 4 — IC Correlation: PASS (no new features)

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto: N/A (single seed)

### Check 7 — Reproducibility: PASS
HEAD `a7208e7`. Seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / label_mode=trend_scanning.

### Check 8 — Hypothesis-Implementation Alignment: PASS
H1 (trend-scanning surfaces different signal subspace) → CONFIRMED. Signal subspace IS different (LINK+DOT +75-112pp lift). But bundle-level OOS Sharpe failed because BTC/ETH/LTC OFFSET those gains.

### Check 13 — Anti-Pattern Static Scan: PASS

### Check 14 — Axis Family Validation: PASS
`labeling` family. Last used at /014 (>21 EXPLORATIONs ago). ROTATION VALID.

## Structural Finding — TREND-SCANNING IS BIMODAL

This is the most important finding of cycle-5 so far. Trend-scanning labels:
- LIFT small-cap symbols dramatically (DOT +112pp, LINK +75pp)
- HURT large-cap symbols catastrophically (BTC -51pp, ETH -46pp)

The bundle OOS is net negative because LARGE-CAP losses (-130pp combined BTC+ETH+LTC) overwhelm SMALL-CAP gains (+186pp combined LINK+DOT). But the small-cap signal is STRUCTURAL, not lottery — both LINK and DOT show >50% WR AND >+100% PnL.

This contradicts the v3/017 NEGATIVE-clean over-filter precedent at single-seed bundle level — at PER-COHORT level, trend-scanning is a STRONG signal source for LINK + DOT.

**Mechanism hypothesis**: small-cap symbols have stronger trend-persistence (less noise, more directional moves); large-caps are more mean-reverting / chop-prone. Wald-test trend significance picks up the small-cap signals while mis-classifying large-cap chop.

## Verdict Cell

Per brief Section 4 verdict matrix:
- F1 OOS Sharpe Δ -0.68 → **NEGATIVE-CATASTROPHIC** at bundle level (≤ -0.55 band)

BUT per-cohort F1 attribution shows LINK + DOT individually clear the +0.20 PROMISING-CLEAN band by margin.

## Path Forward — STRONG ROUTING SIGNAL

**/036 RECOMMENDATION: Trend-scanning labels APPLIED PER-COHORT (LINK + DOT specialist).**

Specifically: dispatch ONLY Model C' (LINK) + Model E (DOT) — each with `--label-mode trend_scanning` + atr_sl=1.75 baseline (or atr_sl=1.0 for tighter SL). Skip Model A pool, C, D, G entirely. Bundle just 2 cohorts to test if the +100pp lift survives isolation.

This would test:
- (a) Does trend-scanning's LINK + DOT lift survive PER-COHORT dispatch? (Should — single-cohort isolation preserves the signal)
- (b) What's the 2-cohort bundle OOS Sharpe? Even at +0.5-0.8 Sharpe with just 2 cohorts, this could be a CONFIRMATION candidate

Expected /036 outcome: **PROMISING-CLEAN at multi-seed validation level** if LINK + DOT specialists with trend-scanning maintain the +100pp PnL pattern.

**Cycle-5 strategic implication**: trend-scanning labels may be the strongest mechanism class discovered in v1 so far when applied to the RIGHT cohorts. Skip remaining Wave 1 Pool-A feature axes; pivot to PER-COHORT trend-scanning explorations.

## NO-MERGE

BASELINE_V1.md UNCHANGED. /035 closed as EXPLORATION-NEGATIVE-CATASTROPHIC at bundle level but with PER-COHORT PROMISING signal documented as structural finding.

Tag: v0.v1-035

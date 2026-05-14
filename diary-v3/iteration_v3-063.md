# iter-v3/063 — Cycle 1 #4 SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE / EXPLORATION-NEGATIVE

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #4 of 10; MASS FEATURE EXPANSION 14 → 46 features after pre-flight ban filter)
**Verdict**: EXPLORATION-NEGATIVE per Critic FINAL `7cbc136`
**Classification**: SUSPICIOUS-OOS-DOMINANT (Section 8.3) + IS-COLLAPSE subtype
**BASELINE_V3.md**: UNCHANGED (still anchors `v0.v3-059`)
**Branch**: `iteration-v3/063`

## 1. What was done

iter-v3/063 was the cycle 1 #4 mandated MASS FEATURE EXPANSION per `feedback_v3_mass_feature_expansion.md` (target 100, minimum 50). QR EDA at SHA `c833f48` produced 48 features via greedy LDP IC-pruning (user-approved 48 < 50 mandate deviation per methodology > strict count). Phase 5.5 gate PASS at `de53eae`. Pre-flight assertion blocked initial backtest launch at 2 historically-banned features in the 48-set:

- `vol_normalized_ret_5d` — DROPPED at /049 (OOS Δ -3.15)
- `hurst_drift_50_200` — PARKED at /054 (Critic FINAL `c056354`)

User-approved drop to 46 features (commit chain: `8c1c22b` setup → fix `<sha>` drop 2 banned + bump count assertion 48 → 46). Backtest re-launched cleanly at PID 516548; wall-clock 0.94h.

## 2. Results

| Metric | /060 anchor | /063 mass expansion | Δ |
|---|---|---|---|
| IS monthly Sharpe | +0.8325 | **-0.5507** | **-1.38** |
| OOS monthly Sharpe | +0.1403 | **+0.4557** | +0.31 |
| OOS/IS daily ratio | 0.28 | -0.66 | sign flip |
| IS Profit Factor | 1.49 | 0.76 | LOSING IS |
| IS MaxDD | 30.97% | 68.72% | +38% |
| OOS MaxDD | 34.53% | 21.84% | -13% |
| IS trades | 159 | 128 | -31 |
| OOS trades | 94 | **63** | -31 (FAILS [66, 122]) |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| DSR_relative | 0.0 | 0.0182 | marginal |

**Per-symbol OOS**: BCH +15.99 (30 tr, 43.3% WR, **118.54% concentration**), LDO **-3.92 (only 3 trades!)**, TRX +1.42 (30 tr, 26.7% WR, marginal).

## 3. Per-symbol decomposition + per-symbol forensic

- **BCH OOS dominance**: 118.54% concentration. The +0.31 OOS lift comes entirely from BCH — 30 trades at 43.3% WR. Per Critic Check 13 forensic, NEW features are mid-low importance for BCH (top-5 dominated by BASELINE_V3 features); the BCH OOS lift is NOT cleanly attributable to NEW signal — likely BCH trade-selection lottery at 46-dim space.
- **LDO trade count collapse**: 12 OOS trades at /060 → **3 OOS trades at /063** (75% reduction). Confidence threshold tightened with the expanded feature set; LDO model became too uncertain to fire signals.
- **TRX win-rate collapse**: 39.6% (/060) → 26.7% (/063). Same trade count (~30) but worse direction prediction. Signal degraded with feature space expansion.

## 4. Critic verdict summary

OVERALL=EXPLORATION-NEGATIVE per Critic FINAL `7cbc136`. 13/13 standard Checks PASS or WARN:
- Foundation Audit (Boot Steps 9-11): walk_forward fix intact at `e149e9d`; labeling/lgbm/validation_v3 unchanged; mode-flag wiring correct; banned features absent
- §11 Anti-Pattern Scan: 13/13 PASS (1 WARN on Check 4 IC matrix; 1 WARN on Check 8 hypothesis-impl divergence)
- Look-Ahead Audit on 9 NEW features: all verified past-only (adx_14, calendar pair, trend_efficiency_signed, vol_regime_x_momentum, sym_vs_btc_ret_3d/vol_14d, taker_buy_imbalance_20, ret_1d)

Two notable Critic adversarial findings:

1. **Engineering report Section 12 FACTUAL ERROR**: QE incorrectly stated "the walk-forward lookahead bias bug is present in this worktree". This is FALSE — the fix from main `5566a69` was cherry-picked at `e149e9d` and is present in `walk_forward.py:113`. Doesn't affect the iteration verdict (the fix being present means IS+OOS are unbiased post-fix), but undermines the engineering report's diligence.

2. **atr_pct_rank_200 silent process slip**: EDA's `T8_pruning_decisions.csv:19` explicitly DROPPED `atr_pct_rank_200` (|IC|=0.820 with atr_pct_rank_500). Yet `features_v3/__init__.py:190` INCLUDED it as "promoted from parquet". Brief Section 3 line 304 flagged it as "reserved" pending T8 verification — verification said DROP but implementation added it. Engineering report makes NO mention. Process slip; not fatal but concerning.

## 5. PATH classification

**SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE** (Section 8.3 LOCKED + Section 8.5 NEGATIVE simultaneously triggered; 8.3 takes precedence as more informative).

Two binding gates FAILED:
- Gate A.1 (IS Sharpe shift > -0.20): observed -1.38, FAILED by 1.18 Sharpe units
- Gate C.7 (OOS trade count [66, 122]): 63 trades, FAILED lower bound

The IS Sharpe collapse from +0.83 to NEGATIVE -0.55 is structurally consistent with `feedback_v3_inert_features_at_higher_budget.md`: at n_trials=35 with 46-dim colsample space, Optuna's TPE warmup is shallower relative to dimensionality, finding IS-OOF-optimizing parameter regions that fail on held-out IS test periods.

The OOS lift is BCH-concentrated lottery, not signal discovery.

## 6. Hypothesis check — pre-registered failure modes ACTIVATED

Brief Section 7 pre-registered 4 failure modes. Two co-activated at /063:

- **Mode B (SUSPICIOUS-OOS-DOMINANT)**: predicted "single-seed lottery at expanded feature space; OOS spikes spuriously while IS doesn't track" — OBSERVED exactly.
- **Mode C (NEGATIVE from inert features at higher Optuna budget)**: predicted IS collapse per `feedback_v3_inert_features_at_higher_budget.md` — OBSERVED at -1.38 IS Sharpe.

Mass feature expansion at single-seed EXPLORATION (--exploration n_trials=35) is **structurally inadequate** for signal discovery in 46-dim space. The user's mandate target (100, min 50) requires either (a) higher n_trials per cell (≥100), (b) multi-seed validation BEFORE mass expansion, or (c) phased expansion (3-5 features at a time validated individually).

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at tag `v0.v3-059`. Cycle 1 EXPLORATIONs do not update BASELINE_V3.md per `feedback_v3_baseline_update_policy.md`. SUSPICIOUS-OOS-DOMINANT iterations explicitly do NOT advance to CONFIRMATION as PROMISING per Section 8.3.

## 8. Critic Recommendations carried forward

1. **Engineering report factual-accuracy gate** — future engineering reports must verify foundation-file claims against actual code (especially walk-forward lookahead status at `walk_forward.py:113`)
2. **EDA-implementation parity gate** — V3_FEATURE_COLUMNS_TOP_N must be BIT-IDENTICAL to EDA's `T8_final_feature_set.csv` (after documented bans). Phase 5.5 gate should assert symmetric-difference equals documented banned-feature set.
3. **Mass-expansion mandate amendment** — `feedback_v3_mass_feature_expansion.md` updated below to require phased expansion at single-seed EXPLORATION (3-5 features at a time) OR multi-seed CONFIRMATION-mode for full mass expansion.

## 9. Next Iteration Ideas

The mass-expansion failure means cycle 1 needs to recover. Options for iter-v3/064:

- **Path A — REVERT to /061's 14-feature stack** (safest; restores anchor; cycle 1 #5 testable from clean baseline)
- **Path B — Phased expansion: add 3-5 high-importance features individually** (per amended mandate; tests whether SOME of the 9 NEW features are real signal)
- **Path C — Single-feature axis EXPLORATION on a non-mass-expansion topic** (axis selection per QR EDA; per `feedback_v3_axis_selection_quant_discipline.md`)

Cycle 1 progress: 4/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (axis CLOSED) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /069) |
| **#4** | **/063** | **MASS FEATURE EXPANSION (Path B 46 features)** | **SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (axis CLOSED)** |
| #5 | /064 | TBD per orchestrator + user | TBD |
| #6-9 | /065-068 | TBD | TBD |
| CONFIRMATION | /069 | Bundle + Path B4 implementation | TBD |

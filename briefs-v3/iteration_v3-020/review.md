# Phase 7.5 Critic Review — iter-v3/020

OVERALL: EXPLORATION-NEGATIVE (clean / PATH C confirmed) — concur with Engineer §4.4 row 5; per-symbol cap (primitive 8) propagated, fired at expected rate, and subtracted edge proportional to conviction. Methodology checks 1-12 all PASS.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Per-symbol cap state populated by `record_trade_result(trade)` keyed on close_time; `_per_symbol_cap_scale` computes share strictly from past closed trades. Adversarial test `test_per_symbol_cap_past_only` verifies current trade is not in own denominator. 13 features identical to iter-v3/018 baseline.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3 verified at runtime.

### Check 3 — Multiple-Testing Correction: PASS-EXPLORATION (informational)
DSR=0.0, PBO=0.119, PSR=0.0009. PSR collapse from iter-v3/019's saturation (1.0) to 0.0009 is methodological IMPROVEMENT — at n_trials=105, E[max_SR]≈3.25 deflates observed annualized Sharpe ≈0.95 honestly. n_eff=19 vs iter-v3/019's 7 — meaningfully better Optuna search coverage at n_trials=35. PBO 0.119 < 0.40 PASS.

### Check 4 — IC Correlation: PASS
Max |IC| 0.685 (max_dd_window_50 ↔ range_realized_vol_50). 13-feature surface bit-identical to iter-v3/018.

### Check 5 — ADF Stationarity: PASS
End-of-training-window (2025-03) all 13 features stationary at p<0.05 for all 3 symbols. Earlier-month False entries are warm-up artifacts.

### Check 6 — Pareto Dominance: WAIVED (single-seed)
Single-seed EXPLORATION; vacuous Pareto check.

### Check 7 — Reproducibility: PASS
Setup `37df8a9`, gate `68a02ae`, brief `de82b8e`, EDA `bbbe783`. Library stack pinned (sklearn `>=1.8,<1.9` per Critic FINAL Rec 12 of iter-v3/019).

### Check 8 — Hypothesis-Implementation Alignment: PASS
Single-axis discipline preserved: cap mechanism added; funding reverted (V3_FEATURE_COLUMNS 14→13); ITERATION_LABEL=v3-020; sklearn pin. 8 unit tests covering basic/no-fire/scaling/past-only/disabled/window/counter/negative-share.

### Check 9 — Symbol Exclusion Enforcement: PASS

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS

### Check 12 — Library Version Pinning: PASS
sklearn pinned `>=1.8,<1.9`. Stack matches BASELINE_V3.md.

## n_trials=35 EXPLORATION Validation Status: PRELIMINARY-VALIDATED

Three diagnostic improvements over iter-v3/019:
1. **n_eff=19** (vs iter-v3/019 n_eff=7) — higher absolute search coverage at n_trials=105 vs 30
2. **DSR=0.0** (vs iter-v3/019 +0.0167 single-seed lottery) — deflation gradient correctly pushes DSR to 0 when observed Sharpe is genuinely modest
3. **PSR=0.0009** (collapsed from iter-v3/019 saturation at 1.0) — honest readout of P(true Sharpe>0) at n_trials=105

**Caveat**: ONE data point cannot validate a default change. Critic prior is that the next 2-3 EXPLORATIONs (iter-v3/021-023) at n_trials=35 should also exhibit DSR/PSR/n_eff in this honest regime. Continue at n_trials=35; do not roll back; record metric trajectories in catalog.

## Verdict — §4.4 row 5 verbatim trigger

| Condition | Threshold | Observed | Triggered? |
|---|---|---|---|
| IS Sharpe Δ < -0.10 | < -0.10 | -0.1043 | YES |
| OOS Sharpe < anchor -0.10 (+0.2869) | < +0.2869 | -0.3296 | YES |
| Cap fire rate ≥ 5% | ≥ 5% | BCH 12.8%, LDO 9.4%, TRX 10.4% | YES (PASS) |
| Non-bit-identical roster | \|Δ\|≥11 OR per-sym>5 | \|Δ\|=28; LDO +13; BCH +11 | YES |

§4.4 row 5 unambiguously fires. Verdict = **EXPLORATION-NEGATIVE (clean / PATH C)**. Cap mechanism propagated, fired at expected counterfactual rate, subtracted edge proportional to conviction in profitable symbols (BCH IS +38.4%, LDO IS +41.9%). Concentration is lottery-REWARD source, NOT lottery-RISK source.

## iter-v3/021 axis prior — HIGH-priority axis #2b (universe expansion)

PATH C confirmation demonstrates 3-symbol concentration carries genuine signal; per-symbol caps subtract edge proportional to conviction. The orthogonal mechanism is **denominator expansion**: adding 1-2 NEW symbols to V3_MODELS to dilute concentration mechanically without removing edge from any single symbol. This was sub-axis B in iter-v3/020 brief, deferred by single-axis discipline.

**Why universe expansion elevates over alternatives**:
- MEDIUM #3 (DSR gate reformulation) is a process fix, not a strategy lever
- MEDIUM #4 (TRX/2022-Q4 regime gate) is symbol-specific, narrower upside
- HIGH-priority #1 (NEW feature family) tested at iter-v3/019; retest at n_trials=35 is lower-priority than orthogonal-mechanism universe-expansion given PATH C confirmation

**Symbol candidates** (excluded per `project_tried_symbols.md` + V3_EXCLUDED_SYMBOLS: DOGE, SOL, XRP, NEAR, BTC, ETH, LINK, LTC, DOT, BNB, MKR):
- AVAXUSDT, ADAUSDT — viable candidates subject to QR's IS-only Gate 1-2 EDA

## Recommendations to QR

1. **Diary**: lock NEGATIVE-clean / PATH C verdict. Document counterfactual-vs-observed gap (-0.36 to -0.26 predicted vs -0.72 observed) as evidence that Optuna at n_trials=35 did NOT compensate for the cap — the cap+Optuna interaction degraded OOS further than static counterfactual estimate. Cap-axis CLOSED for post-bootstrap cycle.

2. **Catalog row**: 
`| iter-v3/020 | 2026-05-07 | NEW risk primitive: per-symbol PnL cap at 0.40 (concentration architecture; HIGH-priority axis #2 sub-axis A) | -0.1043 (vs iter-v3/018 multi-seed +0.3788) | -0.3296 (Δ -0.7165; below trade-rate floor at 86 trades; PATH C) | EXPLORATION-NEGATIVE (clean) | NO — cap subtracts edge proportional to conviction; concentration is lottery-REWARD; iter-v3/021 = universe expansion |`

3. **NEW memory rule** `feedback_v3_concentration_is_signal.md`: "iter-v3/020 confirmed concentration in 3-symbol BCH+LDO+TRX carries genuine signal; per-symbol caps that scale weight proportional to share subtract edge proportional to conviction. Future axes touching concentration MUST use orthogonal mechanisms (universe expansion = denominator expansion; per-symbol drawdown brake = loss-stop semantics; vol-target ceiling = exposure ceiling). Per-symbol PnL share caps CLOSED at catalog level until fundamentally different mechanism proposed with new IS-only counterfactual evidence."

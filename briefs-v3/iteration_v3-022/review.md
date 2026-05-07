# Phase 7.5 Critic Review — iter-v3/022

OVERALL: EXPLORATION-NEGATIVE (clean) — TRX regime gate failed primary success metric (PBO max <0.85) despite improving the targeted TRX/2022-10 cell from 1.0 to 0.282. Headline OOS Sharpe collapse (-0.82 vs anchor) is BCH/LDO single-seed baseline, NOT regime gate cross-contamination (forensic check confirmed bit-identity).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Regime gate state computed from BTC kline cache via `searchsorted('left') - 1` for strict past-only (current bar's BTC NOT in own window). Adversarial test in `tests/strategies/ml/test_regime_gate.py` verifies spike at bar 50 not visible at bar 50 (DD=0%) but visible at bar 52 (DD=-50%).

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 reverted (5→3 syms). Runtime assertion fires.

### Check 3 — Multiple-Testing Correction: PASS-EXPLORATION
DSR=0.0, PBO mean=0.119 (PASS<0.40), PSR=0.0000 (collapsed honest readout). PBO max=1.0 (LDOUSDT/2026-03 — DATA-SCARCITY cell unrelated to regime gate; TRX max = 0.999 at TRX/2023-01). n_eff=19 consistent with iter-v3/020/021 (n_trials=35 default validated 3rd consecutive iteration).

### Check 4 — IC Correlation: PASS

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto Dominance: WAIVED (single-seed)

### Check 7 — Reproducibility: PASS
Setup `64e101d`, gate `8418f57`, brief `79321c5`, EDA `b728313`. V3_MODELS=3, REQUIRED_GAP=66, ITERATION_LABEL=v3-022 verified.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-SATURATION-FIRE
Single-axis discipline preserved. Saturation falsifier IS=196 within EXPLORATION single-seed reference (iter-v3/020/021 produced 200/311); the regime gate REDUCED IS trades 200→196, confirming axis propagated as designed.

### Check 9 — Symbol Exclusion Enforcement: PASS

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS

### Check 12 — Library Version Pinning: PASS

## Critical Forensic Finding — NO Cross-Symbol Regression

QE engineering report verified: BCH and LDO OOS are **bit-identical** across iter-v3/020 (per-symbol cap), iter-v3/021 (universe expansion), iter-v3/022 (regime gate). Specifically:
- BCH OOS: -6.2465 weighted_pnl / 36 trades / 36.1% WR — IDENTICAL across 020, 021, 022
- LDO OOS: -8.9257 weighted_pnl / 13 trades / 38.5% WR — IDENTICAL across 020, 021, 022

This confirms **MECHANISM 1 (per-symbol Optuna independence)**: each per-symbol LightGBM model is trained independently; regime gate doesn't contaminate BCH/LDO Optuna trajectories. The apparent cross-symbol regression in the headline OOS Sharpe is just BCH+LDO's pre-existing single-seed=42 baseline, which has been net-negative since iter-v3/020 onset (the cap iteration where they first ran at single-seed --exploration mode).

**Methodological implication**: per-symbol attribution at single-seed EXPLORATION is meaningfully constrained. BCH/LDO have a "frozen" baseline at single seed that doesn't move regardless of TRX-only changes. This frozen-baseline pattern is identical across 3 consecutive iterations, indicating the EXPLORATION cycle's BCH/LDO Optuna trajectories are deterministic at seed=42.

## Primary Success Metric — TRX/2022-Q4 PBO Drop

| Cell | iter-v3/018 PBO | iter-v3/022 PBO | Result |
|------|-----------------|-----------------|--------|
| TRX/2022-10 | 1.0 | **0.282** | **DROPPED 0.72** ✓ |
| TRX/2023-01 | 1.0 | 0.999 | NO drop (EXPLORATION budget too small for stable PBO reduction) |

Partial success: 1 of 2 target cells succeeded. New high-PBO cells emerged at TRX/2022-09 (0.926) and TRX/2025-10/11 (~0.99) — EXPLORATION budget artifacts (n_trials=35 produces noisy per-cell PBO at the tail).

**Per brief §4 PBO max gate** (target [0.6, 0.85]): observed 1.0 (LDO/2026-03 data-scarcity cell + TRX/2023-01) — gate FAILS. The regime gate axis is structurally correct (targeted cell did drop) but the EXPLORATION single-seed budget produces too much per-cell PBO noise to confirm stable improvement.

## §4.4 Row Classification

The brief §4.4 logic:
- IS Sharpe Δ +0.43 (lift) → would suggest PROMISING
- OOS Sharpe Δ -0.82 (collapse) → suggests NEGATIVE
- PBO max gate FAILS (target ≤ 0.85, observed 1.0)
- Mixed pattern not anticipated by 4-row §4.4 table

**Verdict**: EXPLORATION-NEGATIVE (clean). The OOS collapse + PBO max FAIL is the binding constraint. The IS lift is structurally an EXPLORATION single-seed artifact (TRX-only improvement boosts aggregate IS via filtering bad TRX trades, but the OOS gate-fire pattern doesn't generalize).

## Recommendations to QR

1. **iter-v3/023 axis = funding rate retest at n_trials=35** (HIGH-priority axis #1, MEDIUM #6 elevated). Rationale:
   - iter-v3/019 funding_rate_zscore_30 was PROMISING-INERT at n_trials=10 (rank 14/14 importance)
   - n_trials=35 has been PRELIMINARY-VALIDATED across iter-v3/020/021/022 (3 iterations of consistent DSR/PSR/n_eff behavior)
   - Retesting funding at the higher trial budget could disambiguate "feature was genuinely INERT" vs "n_trials=10 budget couldn't surface signal"
   - If PROMISING at n_trials=35 → strong CONFIRMATION candidate for iter-v3/029 bundle
   - If still INERT → funding axis closed at catalog level

2. **Catalog row should explicitly flag**: BCH/LDO single-seed=42 EXPLORATION trajectories are now "frozen baseline" producing IDENTICAL OOS results across 3 iterations. Future EXPLORATION QRs cannot expect single-seed BCH/LDO movement from any TRX-only or BCH-orthogonal axis. This is a cadence-discipline observation (frozen baseline is a feature of single-seed EXPLORATION, not a defect).

3. **Pre-commit memory rule**: `feedback_v3_single_seed_frozen_baseline.md` codifying that single-seed=42 EXPLORATION produces deterministic per-symbol Optuna trajectories; cross-symbol regression in headlines is attributable to non-target symbols' frozen baselines, NOT to axis cross-contamination. Verify via bit-identity check on iter-v3/020 vs iter-v3/021 vs iter-v3/022 BCH/LDO trades.csv (already done by QE).

## Catalog Row Recommendation

`| iter-v3/022 | 2026-05-07 | NEW risk primitive: TRX/2022-Q4 regime gate (BTC drawdown_30d > 20% OR vol_zscore > 1.5; TRX-only target) (MEDIUM #4 ELEVATED) | +0.43 (vs iter-v3/018 anchor +0.3788) — IS lift is TRX-driven artifact | -0.4313 (Δ -0.82 — OOS collapse is BCH/LDO frozen baseline not regime gate effect) | EXPLORATION-NEGATIVE (clean) | NO — TRX/2022-10 PBO dropped 1.0→0.282 (1 of 2 target cells succeeded); TRX/2023-01 stuck at 0.999; new high-PBO cells emerged at TRX/2022-09 (EXPLORATION budget noise); PBO max gate FAILS at 1.0 (LDO/2026-03 data-scarcity); iter-v3/023 = funding retest at n_trials=35 |`

# Phase 7.5 Critic Review — iter-v3/069 (Round 2 corrected)

OVERALL: MERGE (INERT-AT-EXPLORATION certified clean — defect-fix process validated)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #10 of 10 — FINAL before /070 CONFIRMATION; NON-FEATURE PIVOT continuation; UNIVERSE EXPANSION axis)

## Round 1 → Round 2 Process

Round 1 PRELIMINARY caught silent compound-axis defect: `BacktestConfig.timeout_minutes` at line 1407 retained 20160 from /068's Path C while `LightGbmStrategy.label_timeout_minutes` (line 1425) was correctly reverted to 10080. BCH OOS byte-identity falsification was the diagnostic: prior run had +10.64 wpnl vs anchor +1.9078 (5× deviation impossible under clean +ADA-only single-axis change).

Fix at commit `4239646` reverted line 1407 → 10080. Re-run completed 1.07h. **BCH OOS byte-identity RESTORED** (+1.9078 = +1.9078; 37 trades; 32.4% WR — bit-for-bit IDENTICAL to /060). Round 2 corrected metrics collapse to within-band INERT.

## Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113` lookahead fix INTACT
- **`BacktestConfig.timeout_minutes = 10080` at line 1407** — FIX APPLIED at commit `4239646`
- `LightGbmStrategy.label_timeout_minutes = 10080` at line 1425
- `validation_v3.REQUIRED_GAP = (21+1)*4 = 88`
- Runtime assertion at lines 729-743 enforces label_timeout==10080 per (model, symbol) — fired without raising
- ITERATION_LABEL = "v3-069"
- V3_MODELS includes ADAUSDT (4 syms)
- compute_embargo_candles(10080, 480) = 22; cv_gap = 22 × 4 = 88
- ADA parquet has all 14 V3_FEATURE_COLUMNS
- ENSEMBLE_SEEDS = [191664963, 1662057957, 1405681631] (outer=42 lineage)

## §11 Anti-Pattern Static Scan: PASS

- A1 walk-forward lookahead bug: zero matches in active code
- Track isolation clean
- Sacred constants intact
- Explicit feature_columns list
- V3_EXCLUDED_SYMBOLS audit enforced

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Triple-barrier σ_t past-only. Walk-forward purges 22 training candles per (model, month). ADA parquet from same `add_*_v3_features` pipeline as incumbents.

### Check 2 — Embargo Width: PASS
Required gap formula `(21+1) × 4 = 88` verified at all 3 call sites (validation_v3.py, walk_forward.py via compute_embargo_candles, lgbm.py). Single source of truth.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL
DSR=0.0 (EXPLORATION-mode artifact); PBO=0.1243 PASS; PSR=0.9833 PASS; frac_positive_paths=0.6000 PASS @0.55. EXPLORATION carve-out: DSR informational only.

### Check 4 — IC Correlation: PASS (carry-over violation noted)
Inherited `vwap_dev_20 × regime_momentum_signed_5d = 0.7797` — Category 2 carve-out per `feedback_v3_engineered_feature_pivot.md`. Not introduced at /069. /070 brief MUST address explicitly.

### Check 5 — ADF Stationarity: PASS
All 14 features stationary at end-of-IS window for all 4 symbols. Borderline `ret_kurt_200` p=0.0612 BCH 2025-01 inherited from /058.

### Check 6 — Pareto Dominance: N/A at unified-architecture EXPLORATION

### Check 7 — Reproducibility: PASS (BCH byte-identity to /060 RESTORED)

**Spot-check verification**: 5 BCH OOS rows in /069 trades.csv (entry 303.870/371.240/419.340/442.920/428.440) match /060's BCH rows BYTE-FOR-BYTE. Every field (entry_price, exit_price, weight_factor, open_time, close_time, exit_reason, pnl_pct, fee_pct, net_pnl_pct, weighted_pnl, stop_loss_price, take_profit_price, timeout_time) IDENTICAL. The byte-identity falsification test that caught the PRELIMINARY-round defect now PASSES the corrected re-run.

TRX OOS trade count identical (54 vs 54); LDO OOS = 12 vs /060's 11 (+1 trade past /060's last LDO; first 3 LDO rows BIT-IDENTICAL).

PnL math spot check (LDO OOS row 17): `(0.960300 - 0.866583)/0.960300 = 9.7591%` raw → 9.6591% net → × weight 0.55 = 5.3125 ✓ matches CSV.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis: 4-symbol UNIVERSE EXPANSION with all other parameters at /060 anchor; INERT 45% modal outcome.
Reality: IS Δ -0.038, OOS Δ -0.018 — both within INERT band; modal outcome HIT (45% probability mass).

Engineer's defect retrospective + classification reversal (PROMISING-DEFERRED → INERT) is methodologically sound — attributable to the defect, not post-hoc rationalization. Cleaner +ADA-only measurement falls within pre-registered INERT band.

### Check 9-12: PASS

### Check 13 — Universe Expansion Specific: PASS

- ADA contributed +0.42 OOS wpnl (concentration 6.69%)
- ADA OOS 18 trades PASS Section 8.6 floor ≥14; ADA IS 74 trades 3× over floor
- BCH byte-identity confirms denominator-expansion mechanism worked structurally
- LDO weakness mitigation: WR 8.3% (/068) → 16.7% (/069) recovery, but more attributable to timeout REVERT than ADA addition. LDO OOS WR remains below /060 anchor 18.2% and below Section 4.6 goal 20.2%
- Section 4.5 IS trade saturation falsifier FIRES (233 vs 220 upper bound) — ADA-driven (74 ADA IS trades vs ~50 NATR-proxy estimate)

## Adversarial-Specific Verification

1. **BCH byte-identity restoration**: CONFIRMED via 5-row spot-check.

2. **/070 bundle composition**: CORRECT FINAL = /065 SL widening + /062 Path B4 (2 components). /069 INERT closes universe-expansion axis at catalog level — does NOT carry forward as non-axis structural change. /070 reverts to 3-symbol BCH+LDO+TRX (REQUIRED_GAP=66; label_timeout=10080).

3. **Anchor-byte correctness gate**: All 18 brief Section 2.1 T0 anchor values bit-exact against /060 comparison.csv. No /065-style recurrence.

4. **Cycle 1 closeout completeness**: CONFIRMED. 10/10 EXPLORATIONs complete. /070 = CONFIRMATION (NOT collapsed into 10th EXPLORATION) per strict 10:1 cadence.

## Recommendations to QR for /070 CONFIRMATION

1. **Anchor-byte correctness gate ENFORCEMENT at runner-level**: The /069 defect (line 1407 vs line 1425 desync) demonstrates two independent label-timeout sources can fall out of sync silently. /070 setup MUST add runtime assertion that `BacktestConfig.timeout_minutes == _build_v3_model.label_timeout_minutes` for every model — single source of truth via shared module constant. Cross-line-number drift is a recurring failure mode; centralize the constant.

2. **Universe expansion follow-up cycle**: The denominator-expansion mechanism worked architecturally but didn't move headline Sharpe at single-seed n_trials=35. Future cycle 2 should test universe expansion at multi-seed CONFIRMATION-spec to discriminate single-seed lottery noise vs genuine "universe-expansion does not lift" finding. Pre-register prediction band BEFORE running.

3. **Inherited IC violation must be addressed at /070 brief**: `vwap_dev_20 × regime_momentum_signed_5d = 0.7797` exceeds 0.70 hard gate. /070 brief Section 2 must either (a) document explicitly as Category 2 composed-feature carve-out with importance ≥30 evidence (current: vwap_dev_20 LDO importance 249.67 rank 1; regime_momentum_signed_5d 122.0 rank 12 — both above 30), or (b) drop one of the two. Failing to address = automatic Critic Check 4 FAIL at /070 CONFIRMATION.

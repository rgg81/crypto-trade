# Phase 7.5 Critic Review — iter-v3/052

OVERALL: **EXPLORATION-NEGATIVE (PATH C-suspicious)** — IS-OOS daily Sharpe ratio = 2.3267 fires the pre-registered Section 8 LOCKED PATH C-suspicious trigger (band [0.5, 2.0]); regime_momentum_signed_3d ranks 14-15/15 across ALL 3 symbols (portfolio 15/15); OOS lift +0.924 attributable to TRX OOS WR jump 41.3% → 52.5% on a feature ranked 15/15 for TRX = Optuna hyperparameter lottery, not signal. regime_momentum_signed_3d UNIVERSAL axis CLOSED for cycle 4 per pre-registration.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION — Cycle 4 #2 of 10 (PIVOTED axis; orchestrator's LDO-removal pick PRE-FALSIFIED by /052 EDA SHA `0a10581` and superseded by /051 EDA RANKED #2 SHA `290f37b` per `feedback_v3_axis_selection_quant_discipline.md` rule 4). Spec: `--seeds 1 --n-trials 35 --clean-oof`; ENSEMBLE_SIZE=5; outer seed=42; 1.25h wall-clock under 2h cap.

## QR Response Considered (Round 2 only)

Round 1 PRELIMINARY skipped — orchestrator dispatched directly with FINAL mode. The verdict pathway is mechanically determined by the pre-registered Section 8 LOCKED PATH C-suspicious trigger (`IS-OOS daily Sharpe ratio outside [0.5, 2.0]`); observed 2.3267 is unambiguously outside the band. No QR clarification could change the verdict without violating `feedback_no_cheating.md` post-hoc renegotiation discipline. The carve-out at `feedback_v3_engineered_feature_pivot.md` applies to the |IC|<0.50 strict gate for Category-2 composed features only, NOT to the IS-OOS daily ratio band.

## Per-Check Status (12 standard methodology checks)

### Check 1 — Look-Ahead Audit: PASS
`compute_regime_momentum_signed_3d` at `engineered_v3.py:330-376` uses `close.shift(1) / close.shift(4) - 1.0` for ret_3d and `np.sign(hurst.shift(1) - 0.5)` for the regime indicator. Both factors strictly past-only. No leak path.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21 + 1) × 3 (UNCHANGED from /051). CPCV (45 paths) PBO=0.1090. Path distribution (29/45 positive, median +0.335) essentially identical to /051 — confirms gap parameter intact and OOS spike is single-window artifact.

### Check 3 — Multiple-Testing Correction: EXPLORATION-INFORMATIONAL
DSR=0.000 (structural at n_trials=525, informational per `feedback_v3_dsr_mode_artifact.md`); PBO=0.1090 PASS; PSR=1.000 PASS; n_eff=19.

### Check 4 — IC Correlation: PASS (with sister-stacking note)
Runtime IC: max |IC| with non-sister features = 0.498 (vwap_dev_20). IC with sister regime_momentum_signed_5d = **0.4446** — below 0.50 stacking-risk threshold per `feedback_v3_engineered_features_dont_stack.md`. **However**, sister-stacking displacement DID occur despite IC < 0.50: 5d recovered rank from 14-15/15 (/051) to 11-13/15 (/052); 3d pushed to 14-15/15. The IC threshold did not prevent displacement.

### Check 5 — ADF Stationarity: PASS
End-of-IS per-symbol ADF for regime_momentum_signed_3d: BCH p=0 (stat -8.31), LDO p=0 (-10.17), TRX p=0 (-10.18). All clear 0.05 by >100x.

### Check 6 — Pareto Dominance: PASS (single-seed trivially non-dominated; carries lottery caveat)
Single-seed=42 OOS_Sharpe +1.43, max_dd 30.42%, calmar 1.47. Per `feedback_v3_single_seed_frozen_baseline.md`: TRX OOS WR 52.5% on 40 trades with 3d ranked 15/15 for TRX cannot mechanistically attribute to 3d signal contribution.

### Check 7 — Reproducibility: PASS
Setup commit `4cf49e5`. Head SHA `9cb4344`. ITERATION_LABEL="v3-052". Explicit `feature_columns`. PnL spot-check OOS row 7 (BCH SHORT, weight 0.52): pnl_pct=-3.37% / net_pnl_pct=-3.47% / weighted_pnl=-1.8035 — matches CSV.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Implementation matches brief:
- `engineered_v3.py:610` activates compute_regime_momentum_signed_3d dispatch
- V3_FEATURE_COLUMNS_TOP_N 15th element = regime_momentum_signed_3d (SWAPPED from fracdiff_d05_close)
- V3_MODELS, REQUIRED_GAP, block_long_for unchanged
- ONE-VARIABLE rule honored (15th slot identity change; net feature count UNCHANGED at 15)

Hypothesis was tested cleanly; verdict of NEGATIVE comes from LOCKED PATH C-suspicious trigger firing, NOT from hypothesis-implementation gap.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS
### Check 10 — Feature Isolation Enforcement: PASS
### Check 11 — Forming-Candle Audit: PASS
### Check 12 — Library Version Pinning: PASS (no new deps; fracdiff still imported but column PARKED)

## Pre-Registered Path Adjudication

| Path | Triggers | Observed | Fired? |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 AND ratio ∈ [0.5, 2.0] AND rank ≤ 10 | IS Δ +0.006 (FAIL ≥+0.05); rank min 14 (FAIL ≤10); ratio 2.33 (FAIL band) | NO |
| PATH B (PROMISING-INERT) | rank ≥ 14 ALL syms AND \|IS Δ\| ≤ 0.10 AND \|OOS Δ\| ≤ 0.30 | rank fires; \|OOS Δ\|=0.924 (FAIL ≤0.30) | NO |
| PATH C-clean | IS Δ < -0.10 OR OOS Δ < -0.30 with ratio ∈ band | None fire; ratio out-of-band | NO |
| **PATH C-suspicious** | **IS-OOS daily ratio outside [0.5, 2.0]** | **2.3267 OUT** | **YES — UNAMBIGUOUS** |
| PATH D (NULL-RESULT) | IS Δ ∈ (-0.10, +0.05) AND OOS Δ ∈ (-0.20, +0.20) AND axis LEARNED | OOS Δ +0.924 outside (-0.20, +0.20) | NO |

**PATH C-suspicious is the sole path whose conditions are met. No discretion.**

## Critical Adversarial Findings

### 1. TRX OOS WR +11.2pp jump on rank-15/15 feature confirms Optuna-lottery attribution
TRX OOS WR jumped 41.3% → 52.5% on 40 trades — largest single-symbol WR lift in v3 EXPLORATION history. The 3d feature ranks 15/15 for TRX (last place). Tree models cannot manufacture +11pp WR lift from a feature with dead-last split contribution; the lift must come from a different Optuna hyperparameter draw on the 14 base features. Per `feedback_v3_single_seed_frozen_baseline.md` REVISED: when V3_FEATURE_COLUMNS_TOP_N changes universally, per-symbol Optuna trajectories perturb — what looks like "axis lift" is search-trajectory artifact.

### 2. Sister-stacking displacement DID occur despite IC < 0.50 stacking-risk threshold
The brief argued IC 0.43-0.47 with 5d sister was below /026 stacking-risk threshold of 0.50. **The observed displacement falsifies the threshold's protective claim for sister features**:
- 5d rank: /051 14-15/15 → /052 11-13/15 (RECOVERED 2-3 ranks)
- 3d rank: /052 14-15/15 (DEAD-LAST except BCH at 14)

Optuna at n_trials=35 single-seed allocated split budget to ONE of the two regime_momentum variants. The colsample/split allocation is competitive across same-family features even when pairwise IC is below the redundancy-collinearity threshold. The `feedback_v3_engineered_features_dont_stack.md` rule should be EXPANDED to cover same-family sister stacking explicitly.

### 3. IS-OOS daily ratio 2.33 is the cleanest signature of single-seed Optuna lottery
The brief predicted ratio band [0.60, 1.50] mean 1.05. Observed 2.33 is 0.33 outside [0.5, 2.0] LOCKED falsifier band. CPCV path distribution IDENTICAL to /051 (29/45 positive, median +0.335 to 4 decimals) — the 0.84 OOS Sharpe jump is NOT broadly distributed; it is concentrated in the OOS window where seed=42 hyperparameter region produced a favorable BCH+TRX win-rate cluster (May +19.47%, Jun +9.37%, Jul +9.96% three-month chain). The OOS-window-specific artifact is what the [0.5, 2.0] band was DESIGNED to detect.

### 4. PATH B INERT criterion fires partially
3d importance ranks 14-15/15 across all 3 syms + portfolio = unambiguous saturation-INERT per `feedback_v3_axis_saturation_predictor.md`. PATH B combined with |OOS Δ| ≤ 0.30 would have classified PROMISING-INERT cleanly, but OOS magnitude (+0.924) eclipses the band. The combination (saturation-INERT feature + large OOS spike unattributable to the feature) is textbook PATH C-suspicious.

### 5. ONE-VARIABLE rule honored cleanly; engineering and EDA discipline is high-quality
Despite NEGATIVE verdict, execution is exemplary: (a) Section 10 audit trail documents PIVOT supersession; (b) QR EDA correctly inverted orchestrator's LDO premise via weighted_pnl vs net_pnl_pct correction; (c) pre-registered Section 8 paths CORRECTLY anticipated PATH C-suspicious as 10% tail outcome; (d) engineering report applies verdict mechanically.

## Recommendations to QR

1. **Expand `feedback_v3_engineered_features_dont_stack.md` to cover SAME-FAMILY sister stacking at any IC.** The current rule was framed around two DIFFERENT engineered features and high IC. The /052 evidence shows displacement at moderate IC (0.44) when features are time-scale variants of same composition (`ret_Nd × sign(hurst - 0.5)`). Proposed: "Do NOT stack two engineered features from same compose family (same primitive structure with different lookback) at single-seed EXPLORATION; defer to multi-seed CONFIRMATION."

2. **regime_momentum family is exhausted at universal single-seed EXPLORATION scope.** One CONFIRMATION-MERGE edge (5d at /028) + zero further universal lifts. Per LOCKED Section 7: CLOSE 3d UNIVERSAL. Cycle 4 #3 should pivot to structurally distinct feature family per `feedback_v3_structural_over_knob_exploration.md`. Top recommendation: `hurst_drift_50_200` (/051 EDA candidate #4); secondary: CatBoost head-to-head (NEW model architecture per /050 Critic recommendation).

3. **Behavioral-effect predictor needs revision for SWAP axes.** Future SWAP-axis briefs Section 4.4 should add importance-rank-ONLY saturation trigger (rank ≥ N-1/N in ALL syms = saturation regardless of trade-count change), because for SWAPs the trade roster size is bounded by the unchanged 14 base features even when the swap fires INERT.

## Catalog Row

`| iter-v3/052 | 2026-05-11 | EXPLORATION cycle 4 #2 of 10: SWAP V3_FEATURE_COLUMNS_TOP_N 15th element — DROP fracdiff_d05_close + ADD regime_momentum_signed_3d UNIVERSAL (V3_MODELS UNCHANGED 3-sym BCH+LDO+TRX; REQUIRED_GAP=66 unchanged); --seeds 1 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof. PIVOT from orchestrator LDO-removal axis (pre-falsified by /052 EDA SHA 0a10581 — orchestrator misread net_pnl_pct as IS drag; weighted_pnl shows LDO +36.78% IS contributor; 2-sym counterfactual triggers PATH C-suspicious ratio 3.58 by construction) to QR-EDA-backed /051 RANKED #2 (SHA 290f37b regime_momentum_signed_3d UNIVERSAL). Setup SHA 4cf49e5. | +0.006 (vs iter-v3/028 baseline +0.5101 → +0.5161) | +0.924 (vs iter-v3/028 baseline +0.5053 → +1.4295; BCH +33.42 / LDO -13.96 / TRX +25.35 wpnl; TRX OOS WR 41.3% → 52.5% on 3d rank 15/15 for TRX = Optuna lottery on 14 base features; CPCV path distribution IDENTICAL to /051; IS-OOS daily ratio **2.327 OUT-OF-BAND of [0.5, 2.0]** = pre-registered PATH C-suspicious trigger; 3d importance rank 14/15/15/15 = saturation-INERT; sister 5d displacement /051 14-15→/052 11-13) | EXPLORATION-NEGATIVE (PATH C-suspicious) per Section 8 LOCKED pre-registration | NO — regime_momentum_signed_3d UNIVERSAL axis CLOSED for cycle 4 per pre-registered Section 7 PATH C-suspicious action. Sister-stacking-displacement anti-pattern documented at moderate IC 0.44 (below /026's 0.50 threshold) — `feedback_v3_engineered_features_dont_stack.md` expansion recommended. regime_momentum family exhausted at universal single-seed EXPLORATION scope. Cycle 4 cadence 2/10 → /053. NEXT axis priorities: hurst_drift_50_200 (HIGH; /051 EDA candidate #4); CatBoost head-to-head (HIGH; NEW model architecture); DSR gate reformulation (MEDIUM). Tag NOT issued. |`

## Files Audited

- `briefs-v3/iteration_v3-052/research_brief.md` (PIVOT SHA `41ff0b8`)
- `briefs-v3/iteration_v3-052/phase5p5_gate.md` (SHA `4cf49e5`)
- `briefs-v3/iteration_v3-052/engineering_report.md` (SHA `5eae673`)
- `reports-v3/iteration_v3-052/` (all artifacts; PnL spot-check on OOS row 7)
- `src/crypto_trade/features_v3/engineered_v3.py` (lines 330-376 compute + 583-613 dispatch)
- `run_baseline_v3.py` (ITERATION_LABEL, _verify_feature_columns)
- `analysis/iteration_v3-051/axis_c_regime_3d_*.csv` (EDA backing SHA `290f37b`)
- `analysis/iteration_v3-052/` (supersession audit SHA `0a10581`)
- `briefs-v3/iteration_v3-051/review.md` (immediate predecessor)
- `BASELINE_V3.md` (iter-v3/028 anchor)

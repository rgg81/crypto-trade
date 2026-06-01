# LightGBM Master Advisor — iter-v1/047 — Phase 4.5 (Pre-Design)

## Context Read

- Track: v1 (cycle-6 EXP-2; cycle-6 EXP-1 was /046 PROMISING-DIVERGENCE on methodology axis)
- Axis: feature-family — realized skewness 21-bar z-score (`skew_zscore_21`)
- Feature formula:
  ```
  log_returns = np.log(close / close.shift(1))
  skew_21bar  = log_returns.rolling(21, min_periods=21).apply(scipy.stats.skew, bias=False)
  skew_mean_90 = skew_21bar.rolling(90, min_periods=90).mean()
  skew_std_90  = skew_21bar.rolling(90, min_periods=90).std()
  skew_zscore_21 = (skew_21bar - skew_mean_90) / skew_std_90
  ```
- Feature stack: V1_FEATURE_COLUMNS_PRUNED at 44 cols post-/040; this iter adds 1 → 45 cols.
- Budget: ENSEMBLE_SIZE=3, n_trials=35, single-seed=42 (EXPLORATION standard); wall-clock ≤2h.
- Cohorts: BTC/ETH/LINK/LTC/DOT pooled-and-per-symbol (Model A pooled BTC+ETH, Models C/D/E per-symbol).

## Critical Surfaced Concern: `stat_skew_20` ALREADY in V1_FEATURE_COLUMNS_PRUNED

`stat_skew_20` (20-bar rolling skew of pct_change) is already at line 116 of `features_v1/__init__.py`. `skew_zscore_21` is the **regime form** (z-scored over 90 bars) of the same algebraic primitive. Pre-EDA F5 IC computation against `stat_skew_20` is the load-bearing diagnostic for this iteration.

## Top 3 Recommendations

### 1. Keep Optuna search space FROZEN for the +1 feature ADD

Do **NOT** adjust `colsample_bytree` / `feature_fraction` / `lambda_l1` bounds defensively to "accommodate" the new feature — that compounds the axis and breaks single-axis isolation.

The 5% dimensionality expansion (1/44 = 2.3% → 1/45 = 2.2% per-feature sampling probability at `feature_fraction=1.0`) is **sub-noise at n_trials=35**.

**CRITICAL ADD**: pre-register a frozen `--features-base-hash` of `V1_FEATURE_COLUMNS_PRUNED` in `run_iteration_047.py` so Critic Check 17 can verify no defensive bound tweaks slipped in.

**Secondary HP flag**: if pre-EDA F5 returns max |IC| with `stat_skew_20` ∈ [0.40, 0.50], LightGBM's depth-3 split-finding will alternate between `skew_zscore_21` and `stat_skew_20` across seeds — at single-seed=42 EXPLORATION this manifests as INERT (rank ~30/45), but at multi-seed CONFIRMATION the redundancy averages out and one wins. Expect a **single-seed under-reading** of the feature's true value if IC is in that band.

### 2. Window-choice analysis — defensible but under-defended

21-bar / 90-bar choice is structurally OK:
- 21 bars at 8h = 7 days = 1 funding-cycle-week — consistent with `regime_momentum_signed_5d` (5-day) and outpaces `stat_skew_20` (20-bar pct_change).
- 90-bar = 30 days for z-normalization matches `funding_rate_zscore_30` and `oi_delta_30_z90` conventions.

LM Master would prefer **18-bar** for the inner window — at 21-bar n=21 the G1 sample skewness estimator (bias=False) has σ_skew ≈ √(6/21) = **0.53 under Gaussian** — HIGH NOISE. 18-bar gives σ_skew ≈ 0.58 (marginal difference) but 18 = 6×3 aligns to 3 trading days × 2 funding cycles per day.

**NOT recommending the change** — single-feature-at-a-time rule per `feedback_v3_engineered_features_dont_stack.md`. Flag for cycle-7 follow-on if /047 is PROMISING.

Z-score window: 90 bars is fine. Alternatives: 60-bar (20 days, tighter regime), 120-bar (40 days, slower regime) bracket it. **DON'T go above 120** — z-norm window > 120 collapses the feature back to a level-indicator (z-scoring against quasi-stationary statistics).

### 3. Predicted importance rank + per-cohort hypothesis

**Portfolio-level mean-gain rank prediction: 18-25 of 45** (just outside the top-15 F1 gate).

Per-cohort breakdown:
- **BTC** — rank 15-22, weakest signal: BTC's return distribution is closest to Gaussian at 8h (lowest `stat_skew_20` variance across symbols); skew z-score has least information here.
- **ETH** — rank 12-18, marginally better than BTC, similar microstructure.
- **LINK** — rank 8-15, mid-cap fat-tail makes z-scored skew more informative; **possibly the cohort that swings F1 PASS/FAIL**.
- **LTC** — rank 15-25, "background symbol" in v1 — Optuna struggles to find LTC-specific signal across the 44-feature pruned stack; new features tend to land mid-table for LTC.
- **DOT** — rank 10-18, smallest-cap of the 5, most exposed to asymmetric-tail events; **the cohort most likely to benefit**.

**Cross-cohort dispersion in importance rank (range 8-25 across cohorts) is itself a diagnostic** — wide dispersion = cohort-conditional signal; narrow dispersion (all rank ~18) = mechanically allocated splits without learned signal.

## Prior Distribution (8 verdict bands)

| Band | Prior |
|---|---|
| UNIVERSAL | 5% |
| REGIME-SPECIALIST-IS | 8% |
| REGIME-SPECIALIST-OOS | 5% |
| TAIL-CONTROL | 7% |
| EXPLORATION-PROMISING | 18% |
| TRUE-NEG | 10% |
| **NEGATIVE-no-effect** | **35% (MODAL)** |
| LEARNED-NEG | 12% |

Sum = 100%.

**Modal MEAN reflects 3 base rates**:
1. `stat_skew_20` already captures level-form skewness — z-score regime form may be redundant in v1's pruned 44-feature stack.
2. iter-v3/019 `funding_rate_zscore_30` precedent: INERT-by-z-score-of-existing-primitive pattern.
3. Single-seed=42 EXPLORATION budget under-reads moderately-IC-correlated features (per Rec 1 secondary flag).

**LEARNED-NEG 12%** reflects iter-v3/023 inert-features-at-higher-budget pattern: moderately-correlated additions (IC 0.4-0.6 with `stat_skew_20`) divert split-budget from genuinely orthogonal features → IS noise + OOS regression.

## Risk Flags

1. **HP search-space defensive widening risk** — see Rec 1.
2. **F5 IC borderline 0.40-0.50 single-seed under-reading** — see Rec 1 secondary.
3. **`basis_zscore_30` precedent**: iter-v1/034 was LEARNED-NEG with same "rolling z-score of new primitive" design. Relevant base rate; not a structural reason to skip /047 but tighter F1 gate is justified.
4. **Cross-cohort dispersion** as diagnostic per Rec 3.

## What I Did NOT Recommend

- No HP region change (Optuna search-space frozen).
- No companion feature (kurtosis z-score) at /047 — single-feature-at-a-time discipline.
- No window-parameterization sweep at /047 — would compound axis.
- No SWAP with `stat_skew_20` — F5 IC will arbitrate; if PROMISING and IC < 0.30, ADD alongside; if PROMISING-WITH-CORRELATED-PRIMITIVE (IC 0.40-0.60), revisit at /048 stack-pruning iteration.
- No ENSEMBLE_SIZE bump from 3 — single-seed=42 EXPLORATION standard.

## Closing Note

**Single most important point: pre-EDA F5 IC value vs `stat_skew_20` is the load-bearing diagnostic.**

- If |IC| < 0.30: experiment is informative in either direction.
- If |IC| ∈ [0.40, 0.60]: verdict is ambiguous between NEGATIVE-no-effect and PROMISING-WITH-CORRELATED-PRIMITIVE; Critic should treat F1 dual-gate as the genuine arbiter.
- If |IC| ≥ 0.60: ABORT pre-launch (F5 falsifier fires).

**Confidence: MEDIUM**. Axis is well-chosen (asymmetric tail is real edge in crypto per Karagiorgis 2024 + Harvey-Siddique JoF 2000). Design is methodologically clean (F4/F5 pre-EDA gates protect against pathological additions). But base rate for single-feature-ADD on a 44-feature pruned stack at 35-trial single-seed EXPLORATION is empirically low: /037 PROMISING at IS Δ +0.10 was OBJECTIVE-FUNCTION axis not feature; /040 PROMISING at IS Δ +0.06 was COMPOSED feature; /034 + /015/019 were LEARNED-NEG / INERT for "z-score of new primitive" pattern. **Modal expected outcome: NEGATIVE-no-effect, not PROMISING.**

Path Forward if NEGATIVE-no-effect at /047:
- /048 = NEW feature family from genuinely different mechanism class (microstructure / cross-asset / on-chain) — close the skew-z-score axis at catalog level after 1 EXPLORATION verdict.

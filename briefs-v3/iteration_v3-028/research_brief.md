# Iteration v3-028 — Research Brief

**Type**: SPECIAL EXPLORATION — MINI-VALIDATION (cadence #10 of 10 in the post-bootstrap cycle; **MULTI-SEED REPLICATION of iter-v3/025** at `--seeds 2` rather than `--exploration --seeds 1`; NOT a new feature/methodology axis. Per Critic FINAL Recommendation of iter-v3/027 (review SHA `966f4c1`) + user directive 2026-05-08.)
**Track**: v3 (rigor arm) — twenty-eighth iteration
**Branch**: `iteration-v3/028` (off `iteration-v3/027` head; brief authored after iter-v3/027 closeout SHA `ef48e94`)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # DEFAULT (NOT --exploration; --seeds 2 mini-validation)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=5)
n_trials         = 35             # DEFAULT (NOT --exploration; matches both EXPLORATION default and CONFIRMATION budget per the post-bootstrap cycle)
colsample_bytree = (default Optuna search; NOT hardcoded to 1.0)
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–027 briefs / engineering reports / Critic FINALs / diaries. NO new EDA needed (this is a multi-seed replication of iter-v3/025, no new feature is added).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: SPECIAL EXPLORATION — MINI-VALIDATION (cadence #10 of 10 post-bootstrap)
Wall-clock budget: ~30 min target / 1h hard cap
Single-axis variation: REPLICATE iter-v3/025 (regime_momentum_signed_5d ALONE
                       on top of iter-v3/013 baseline = V3_FEATURE_COLUMNS=14)
                       at --seeds 2 (multi-seed) instead of --seeds 1
                       (single-seed). DROP cross_asset_divergence_norm
                       (revert iter-v3/027's swap; V3_FEATURE_COLUMNS 15 → 14).
                       KEEP regime_momentum_signed_5d (proven at iter-v3/025;
                       per `feedback_v3_engineered_features_proven.md` mandate).
                       NO new feature added. NO methodology change.
                       Per Critic FINAL Rec of iter-v3/027 (SHA `966f4c1`)
                       + user directive 2026-05-08.
Cadence: SPECIAL EXPLORATION #10 of 10 needed before next CONFIRMATION
         (iter-v3/029 = CONFIRMATION at full --seeds 2 + n_trials=35
         + ENSEMBLE_SIZE=5; ~3-4h)
Axis category: 7 (MULTI-SEED REPLICATION at intermediate budget — NOT a
               feature/methodology/architecture axis; structurally a
               "mini-CONFIRMATION" sanity check)
ANCHOR (formal BASELINE_V3.md anchor): iter-v3/018 BOOTSTRAP baseline
        (multi-seed mean +0.3788 IS / +0.3869 OOS)
REFERENCE (single-seed parent being validated): iter-v3/025 (+0.8788 IS / +1.2244 OOS
        — single-seed reference; PROMISING but lottery-suspect per
        `feedback_v3_single_seed_frozen_baseline.md`)
NOT a gate-threshold knob. NOT an off-the-shelf indicator addition.
NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED).
NOT a new feature add (regime_momentum_signed_5d already validated at iter-v3/025).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — MINI-VALIDATION of iter-v3/025 at --seeds 2 (per Critic FINAL `966f4c1` of iter-v3/027 Recommendation + user directive 2026-05-08)**:

After 9 EXPLORATIONs in the post-bootstrap cycle (iter-v3/019 through iter-v3/027), the catalog has converged on **a single PROMISING result — iter-v3/025 (regime_momentum_signed_5d ALONE)**. All other candidates fall into one of three categories:

1. **PROMISING-INERT** at single-seed lottery: iter-v3/019 funding rate (importance 14/14, Falsifier 4 fired)
2. **NEGATIVE-clean (PATH C)**: iter-v3/020 per-symbol PnL cap, iter-v3/021 universe expansion HBAR+AVAX, iter-v3/022 TRX/2022-Q4 regime gate, iter-v3/023 funding retest at n=35, iter-v3/024 BTC funding cross-asset
3. **NEGATIVE-SUSPICIOUS-OOS** at engineered-feature stacking: iter-v3/026 (vol_adj_autocorr stacked on regime_momentum), iter-v3/027 (cross_asset_divergence_norm swapped for vol_adj_autocorr) — 3-iter monotonic IS degradation REPLICATED across 2 stacking compositions; structural single-seed lottery

**The iter-v3/025 PROMISING result is single-seed AND has ZERO independent validation evidence.** Per `feedback_v3_single_seed_frozen_baseline.md` + iter-v3/013 precedent (single-seed +1.0088 IS / +2.6970 OOS Sharpe FALSIFIED at multi-seed iter-v3/018 CONFIRMATION; 62% IS / 86% OOS reduction; LDO 80% WR was Optuna-path lottery), single-seed Sharpe values at EXPLORATION are subject to Optuna-trajectory lottery noise.

**iter-v3/029 CONFIRMATION at full --seeds 2 + n_trials=35 + ENSEMBLE_SIZE=5 costs ~3-4h compute.** The bundle is single-feature MINIMAL (iter-v3/013 baseline + regime_momentum_signed_5d). If the iter-v3/025 result was single-seed lottery, iter-v3/029 is dead-on-arrival and we waste 3-4h of compute budget.

**Pre-validating iter-v3/025 at --seeds 2 (~30 min compute; 2× single-seed budget) gives early signal whether iter-v3/029 will succeed.** This is a LOWER-budget mini-CONFIRMATION sanity check before committing to the full CONFIRMATION budget.

**Critic FINAL Recommendation of iter-v3/027 (review SHA `966f4c1`)**:

> **iter-v3/028 axis = REPLICATE iter-v3/025 ALONE at --seeds 2** (mini-CONFIRMATION sanity check):
>
> Rationale:
> 1. iter-v3/025's single-seed +0.88 IS / +1.22 OOS is the CONFIRMATION bundle's only edge ingredient
> 2. iter-v3/013 single-seed +1.01 / +2.70 was falsified at iter-v3/018 multi-seed (62%/86% reduction)
> 3. Pre-validating iter-v3/025 at --seeds 2 (~30 min compute, 2× single-seed budget) gives early signal whether iter-v3/029 CONFIRMATION at --seeds 2 + n_trials=35 + ENSEMBLE_SIZE=5 (~3-4h compute) is worth the budget
> 4. If iter-v3/025 multi-seed falsifies → iter-v3/029 is dead-on-arrival; we save CONFIRMATION budget
> 5. If iter-v3/025 multi-seed holds → iter-v3/029 launches with high confidence

**iter-v3/028 first EXPLORATION axis = MINI-VALIDATION mandate.** Cannot be renegotiated post-hoc per Critic FINAL `966f4c1` of iter-v3/027 + user directive 2026-05-08.

**Why the 10th of 10 EXPLORATION slot used for validation rather than another axis**:

After 9 of 10 post-bootstrap EXPLORATIONs, the empirical evidence concentrates on one and only one PROMISING result. The decision-information-value calculation:

- **Another EXPLORATION axis (e.g., NEW labeling architecture, fracdiff_d05_close, or hurst_drift_50_200)**: would generate an additional candidate signal, but each candidate is single-seed-untrustable per the cycle's pattern (iter-v3/025 is the only PROMISING out of 9 single-seed runs, and even iter-v3/025 needs multi-seed validation). Each new EXPLORATION axis adds 1 NEW data point of an unknown distribution.
- **MINI-VALIDATION of iter-v3/025 at --seeds 2**: directly de-risks the iter-v3/029 CONFIRMATION decision by 3-4× (CONFIRMATION compute ~3-4h vs MINI-VALIDATION ~30 min). The expected value is HIGH because the bundle is single-feature MINIMAL — if iter-v3/025 multi-seed falsifies, the entire iter-v3/029 CONFIRMATION wastes ~3-4h of compute. This is the FIRST iteration in v3 where the next-CONFIRMATION's success depends materially on a single prior single-seed result.

**The information value of MINI-VALIDATION is asymmetrically large given the cycle's empirical distribution.**

---

## Section 0.5b — Special EXPLORATION Type Justification

This iter-v3/028 is structurally a **SPECIAL EXPLORATION** because it uses `--seeds 2` instead of the typical `--exploration --seeds 1` for EXPLORATION iterations. This deviates from the post-bootstrap EXPLORATION default in 2 ways:

1. **--seeds 2 instead of --seeds 1**: 2 outer seeds × 5 inner ensemble seeds = 10 model fits per cell (vs single-seed 1 × 1 = 1 model fit per cell at EXPLORATION).
2. **NO --exploration flag**: ENSEMBLE_SIZE=5 (default) instead of 1 (--exploration); colsample_bytree NOT hardcoded to 1.0; n_trials=35 (default; same as EXPLORATION).

Per `feedback_v3_outer_seed_cap_2_v3.md`: "v3 CONFIRMATION runs use --seeds 2 max (5 inner × 2 outer = 10 models/cell, vs 25). Inner ensemble stays at 5 for live-prediction variance reduction. Supersedes the 10-seed rule for v3 only; v1/v2 still 10."

This iter-v3/028 mini-validation uses `--seeds 2` even though it's classified EXPLORATION — **accepted exception per "validate before CONFIRMATION budget" justification**. The classification rationale:

- It is NOT a CONFIRMATION because it does NOT update BASELINE_V3.md regardless of outcome (CONFIRMATION-MERGE updates baseline; this is a sanity check).
- It IS a SPECIAL EXPLORATION because it occupies the 10th of 10 EXPLORATION slots before iter-v3/029 CONFIRMATION (cadence-discipline math holds).
- It uses `--seeds 2` to match the iter-v3/029 CONFIRMATION outer-seed budget (so falsification at iter-v3/028 directly predicts falsification at iter-v3/029).

**Compute budget**: ~30 min wall-clock target / 1h hard cap. iter-v3/025 at --exploration --seeds 1 ran in 14 min; multiplying by ~2.1× for ENSEMBLE_SIZE=5 + 2 outer seeds (additive overhead, not 10× multiplicative because Optuna trials are reused per outer seed) gives ~30 min target. Hard cap 1h is conservative.

**This iteration NEVER updates BASELINE_V3.md regardless of outcome.** PATH A (PROMISING-CONFIRMED) does NOT trigger a CONFIRMATION-MERGE; iter-v3/029 is the binding CONFIRMATION step.

---

## Section 1 — Hypothesis

**iter-v3/025's single-seed +0.88 IS / +1.22 OOS holds at multi-seed --seeds 2 with similar magnitude (within ±0.30 on each axis).**

Predicted IS Sharpe band [+0.55, +1.10] median +0.80 (some compression expected from single-seed +0.88 due to seed-averaging variance reduction); predicted OOS Sharpe band [+0.85, +1.40] median +1.10 (some compression expected from single-seed +1.22). Both seeds positive on Pareto.

**Mechanism explanation** (why iter-v3/025's single-seed result MAY hold at multi-seed):

- iter-v3/025's PATH A criteria fired unambiguously across all 4 cuts (importance ≥30 BCH 43, LDO 232, TRX 123, Portfolio 398; LDO rank ~8-9/14 in TOP HALF). The composed feature regime_momentum_signed_5d contributed 51% of top portfolio importance — approximately 2× the contribution of any prior NEW feature (iter-v3/015/019/023/024 were all 22-25%).
- The frozen-baseline pattern (BCH OOS −6.2465 / LDO OOS −8.9257 bit-identical across iter-v3/020-024) DISSOLVED at iter-v3/025: BCH OOS shifted +6.25 → +11.31 (a +17.56 weighted_pnl swing), LDO OOS shifted −8.93 → −1.98 (a +6.95 swing toward neutral). This is structurally consistent with the frozen-baseline rule per `feedback_v3_single_seed_frozen_baseline.md` — different V3_FEATURE_COLUMNS produces different per-symbol Optuna trajectories. The dissolution direction was POSITIVE (BCH+LDO IMPROVED), not random.
- IS+OOS co-directional lift (+0.50 IS / +0.84 OOS) is NOT structurally suspect (unlike iter-v3/026's 27× IS/OOS daily ratio or iter-v3/027's IS-negative anomaly). iter-v3/025's IS/OOS daily ratio was 0.92 — within normal range.

**Counter-mechanism** (why iter-v3/025's single-seed result MAY FAIL to hold at multi-seed):

- iter-v3/013 precedent: single-seed +1.0088 IS / +2.6970 OOS Sharpe was FALSIFIED at multi-seed iter-v3/018 CONFIRMATION (62% IS / 86% OOS reduction); LDO 80% WR was single-seed Optuna-path lottery at n_trials=10. iter-v3/025 had TRX 52.2% WR (highest single-symbol single-seed WR in v3 catalog) — possibly suggestive of similar lottery-favorable Optuna trajectory.
- iter-v3/025's per-symbol importance is uneven: BCH 43 (rank 14/14), LDO 232 (rank ~8-9/14), TRX 123 (rank ~10-11/14). LDO carries the bulk; if LDO's Optuna trajectory differs at seed=123 vs seed=42, the LDO importance may be very different at multi-seed.
- The 3 OOS-MaxDD trajectory measurements (iter-v3/025's 21.35% versus anchor 27.74% versus iter-v3/024's 49.97%) span a wide range; at multi-seed, OOS-MaxDD will likely be the multi-seed mean, which may regress to the iter-v3/018 anchor levels.

**Why prior iterations don't directly predict iter-v3/028's outcome**:

- iter-v3/018 CONFIRMATION (multi-seed validation of iter-v3/013 baseline) had a 62%/86% reduction from single-seed reference; this is the CLOSEST precedent. But iter-v3/018 had 13 features (NO regime_momentum_signed_5d); iter-v3/028 has 14 features (with regime_momentum). The feature stack differs, so per-symbol Optuna trajectories will differ. iter-v3/018's 62%/86% reduction is the WORST-CASE scenario; the actual reduction at iter-v3/028 may be smaller because the new feature genuinely provides signal.
- iter-v3/025 single-seed used --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 3 symbols = 105 fits per cell; colsample_bytree=1.0 hardcoded). iter-v3/028 uses --seeds 2 default (2 outer × 5 inner × 35 n_trials × 3 symbols = 1050 fits per cell; colsample_bytree default Optuna search). The increased fit budget per cell (10×) and the un-hardcoded colsample_bytree may produce systematically different (and likely better) performance at multi-seed.
- The hypothesis is falsifiable in 3 directions: (a) PATH A (PROMISING-CONFIRMED) — iter-v3/025 result HOLDS at multi-seed → iter-v3/029 CONFIRMATION proceeds with high confidence; (b) PATH B (PROMISING-COMPRESSION) — partial multi-seed reduction but still meaningfully positive → iter-v3/029 still proceeds but with lowered expectations; (c) PATH C (FALSIFIED) — iter-v3/025 was single-seed lottery, multi-seed reduces below floor → iter-v3/029 dead-on-arrival; pivot to fundamentally different bundle.

**Direction symmetry**: regime_momentum_signed_5d encodes regime-conditional momentum sign-flip (positive when Hurst > 0.5 indicates trending; negative when Hurst < 0.5 indicates mean-reverting). The mechanism is naturally symmetric and was empirically validated at iter-v3/025 across all 3 symbols (BCH, LDO, TRX). Multi-seed should preserve this symmetry on average.

---

## Section 2 — Implementation Spec

### 2.1 Atomic feature column count revert (single axis preserved)

iter-v3/028 first commit must atomically:
1. **DROP** `cross_asset_divergence_norm` from `V3_FEATURE_COLUMNS_TOP_N` (revert iter-v3/027's swap; V3_FEATURE_COLUMNS 15 → 14).
2. **KEEP** `regime_momentum_signed_5d` in `V3_FEATURE_COLUMNS_TOP_N` (proven at iter-v3/025; per `feedback_v3_engineered_features_proven.md` mandate).
3. Net column count: 14 (matches iter-v3/025 anchor exactly).
4. Single axis preserved: ATOMIC drop (no add); other gates BYTE-IDENTICAL to iter-v3/025 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled).

### 2.2 Module structure — NO changes to engineered_v3.py

The module `src/crypto_trade/features_v3/engineered_v3.py` retains BOTH `compute_regime_momentum_signed_5d` AND `compute_cross_asset_divergence_norm` and `compute_vol_adj_autocorr` functions at zero revert cost. Only the V3_FEATURE_COLUMNS_TOP_N tuple changes (cross_asset_divergence_norm dropped from the list); the underlying compute functions stay in repo for any HYPOTHETICAL future re-architecture.

`add_engineered_v3_features` dispatch must be updated to call ONLY `compute_regime_momentum_signed_5d` (drop the call to `compute_cross_asset_divergence_norm`).

### 2.3 Feature columns assertion update — `_verify_feature_columns`

```python
def _verify_feature_columns() -> None:
    """Verifies V3_FEATURE_COLUMNS contents per current brief (iter-v3/028).

    iter-v3/028: 14 columns — atomic drop:
      DROP cross_asset_divergence_norm (iter-v3/027 stacking falsified; revert
        15 → 14; matches iter-v3/025 anchor exactly).
      KEEP regime_momentum_signed_5d (Category 2 composed feature, iter-v3/025;
        MUST NOT be reverted — iter-v3/025 PROMISING; mini-validation target).
    Net count: 14 (matches iter-v3/025 anchor).
    tbr_zscore_30 MUST NOT be present (dropped iter-v3/016).
    vwap_dev_50 MUST NOT be present (dropped iter-v3/008 per Critic SHA a544621).
    funding_rate_zscore_30 MUST NOT be present (per-symbol variant PERMANENTLY-CLOSED).
    btc_funding_rate_zscore_30 MUST NOT be present (cross-asset variant PERMANENTLY-CLOSED).
    vol_adj_autocorr MUST NOT be present (stacking FALSIFIED at iter-v3/026).
    cross_asset_divergence_norm MUST NOT be present (stacking FALSIFIED at iter-v3/027).
    regime_momentum_signed_5d MUST be present (Category 2 composed feature, iter-v3/025).
    """
    n = len(V3_FEATURE_COLUMNS)
    if n != 14:
        raise RuntimeError(
            f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 14. "
            "iter-v3/028: atomic drop cross_asset_divergence_norm (revert iter-v3/027 swap; "
            "15 → 14; matches iter-v3/025 anchor exactly). "
            "Check features_v3/__init__.py V3_FEATURE_COLUMNS_TOP_N."
        )
    # ... (existing tbr_zscore_30, vwap_dev_50, funding_rate_zscore_30, btc_funding_rate_zscore_30,
    #      vol_adj_autocorr ABSENT assertions UNCHANGED)
    if "cross_asset_divergence_norm" in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "cross_asset_divergence_norm FOUND in V3_FEATURE_COLUMNS — must be ABSENT per "
            "iter-v3/028 brief §2.1 (DROPPED; stacking FALSIFIED at iter-v3/027: "
            "IS Sharpe collapse -0.2817 + OOS spike +1.6786; "
            "TRX 91.57% concentration regression). "
            "Remove it from V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
        )
    if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS:
        raise RuntimeError(
            "regime_momentum_signed_5d MISSING from V3_FEATURE_COLUMNS — must be "
            "PRESENT per iter-v3/028 brief §2.1 (KEEP; iter-v3/025 PROMISING; "
            "mini-validation target). Do NOT revert."
        )
    print(f"  V3_FEATURE_COLUMNS: {n} columns  PASS")
```

### 2.4 ITERATION_LABEL update

```python
# run_baseline_v3.py
ITERATION_LABEL = "v3-028"
```

### 2.5 Run command — multi-seed budget

```bash
uv run python run_baseline_v3.py --seeds 2
```

Note: NO `--exploration` flag. This produces:
- 2 outer seeds (42, 123) × 5 inner ensemble × 35 n_trials × 3 symbols = **1050 fits per cell**
- ENSEMBLE_SIZE = 5 (default)
- colsample_bytree: default Optuna search (NOT hardcoded to 1.0)
- n_trials = 35 (default; matches both EXPLORATION default and CONFIRMATION budget)

Wall-clock budget: ~30 min target / 1h hard cap.

### 2.6 No new EDA needed

This is a multi-seed replication of iter-v3/025. No new feature is added; no new mechanism is introduced. The brief Section 2 cites iter-v3/025's existing EDA at SHA `917605b` (analysis/iteration_v3-025/feature_engineering_eda.py + 5 CSV outputs + synthesis.md; 6 of 7 candidates evaluated; #3 adx_signed_momentum REJECTED; regime_momentum_signed_5d selected via Critic FINAL Rec + user directive pre-commit). The iter-v3/025 EDA already covered:

- IC / rank-IC at horizons 1-30 across all 3 symbols
- Composite leaderboard score
- ADF stationarity test (PASS)
- Per-symbol distribution analysis
- Source-primitive overlap analysis (cross-feature correlation)

No incremental EDA is needed because the feature is already in the repo, the past-only adversarial test already passed at SHA `3b1f979`, and no new mechanism is being introduced. iter-v3/028 is purely a multi-seed budget upgrade.

### 2.7 Pre-existing past-only adversarial test (already validated at iter-v3/025)

The 20 adversarial tests at SHA `3b1f979` verified `compute_regime_momentum_signed_5d` is past-only:
- `ret_5d` via `.shift(15)`-rooted log-close diff (already past-only)
- `hurst_100` via rolling 100-bar trailing R/S window (already past-only)
- `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` (no new past-only construction needed)

The tests are committed to the repo at iter-v3/025 SHA `3b1f979` and remain valid for iter-v3/028. No new tests are needed.

---

## Section 3 — Methodology Plan

### 3.1 Backtest configuration (DEFAULT not --exploration)

```
--seeds 2                    # 2 outer seeds (42, 123)
                             # NOT --exploration
n_trials = 35                # default
ENSEMBLE_SIZE = 5            # default
colsample_bytree             # default Optuna search
training_months = 24         # IMMUTABLE
OOS_CUTOFF_DATE = 2025-03-24 # IMMUTABLE
3-symbol universe            # BCHUSDT + LDOUSDT + TRXUSDT (UNCHANGED from iter-v3/018+)
```

### 3.2 Track isolation grep

Before launching the run, the QE must verify no v1 or v2 reference is introduced:

```bash
git diff iteration-v3/027 iteration-v3/028 -- run_baseline_v3.py src/crypto_trade/features_v3/ | grep -E "(v1|v2|features_v2|backtest_models_v1)" || echo "PASS: no v1/v2 cross-reference"
```

Expected output: `PASS: no v1/v2 cross-reference`.

### 3.3 Embargo / gap

`REQUIRED_GAP = 66 = (21 + 1) × 3`. Same as iter-v3/025 (3-symbol universe + 21-bar timeout = 22 candles per symbol × 3 = 66 candles total embargo). No change needed.

### 3.4 DSR / PBO / PSR

At --seeds 2 (NOT --exploration), the DSR/PBO/PSR computations run with MULTI-SEED data. n_eff is expected to be > 19 (EXPLORATION reference) and < 25 (iter-v3/018 CONFIRMATION reference at --seeds 2). DSR is expected to be POTENTIALLY non-zero (unlike EXPLORATION's structural 0.0). PBO max-aggregator may now be informative at the cell level.

This is INTENTIONALLY similar to iter-v3/029 CONFIRMATION's spec — that's the entire point of MINI-VALIDATION. The DSR/PBO/PSR values from iter-v3/028 are **directly comparable** to iter-v3/029's expected DSR/PBO/PSR.

### 3.5 Look-ahead audit checklist

- [x] No new feature added — pre-existing iter-v3/025 features only
- [x] iter-v3/025 past-only adversarial tests (SHA `3b1f979`) remain valid
- [x] No labeling change
- [x] No risk gate change
- [x] σ_t for ATR via past-only EWMA — UNCHANGED from iter-v3/018+
- [x] Hurst via rolling 100-bar trailing R/S window (past-only) — UNCHANGED
- [x] BTC features lagged 1 candle behind block-publication time — UNCHANGED
- [x] forming-candle filter active — UNCHANGED
- [x] OOS_CUTOFF_DATE = 2025-03-24 — UNCHANGED
- [x] training_months = 24 — UNCHANGED

---

## Section 4 — Pre-Registered Verdict Pathways

### 4.1 PATH A (PROMISING-CONFIRMED)

**Trigger conditions** (BOTH must hold):
- IS monthly Sharpe (multi-seed mean) ≥ +0.55 (vs iter-v3/025 single-seed +0.8788; allowing 37% compression)
- OOS monthly Sharpe (multi-seed mean) ≥ +0.85 (vs iter-v3/025 single-seed +1.2244; allowing 31% compression)

**Implication**: iter-v3/025 result HOLDS at multi-seed; the regime_momentum_signed_5d feature provides genuine signal (not single-seed lottery). iter-v3/029 CONFIRMATION launches with HIGH confidence.

**Action**: Phase 8 diary catalogs as `MINI-VALIDATION-CONFIRMED`; iter-v3/029 brief authored with the pre-validated bundle:
- Base: iter-v3/013 baseline (BCH+LDO+TRX, 13 features, ATR labeling, 7 risk gates)
- ADD: regime_momentum_signed_5d (V3_FEATURE_COLUMNS=14)
- Spec: --seeds 2 --n-trials=35, ENSEMBLE_SIZE=5, full DSR/PBO/PSR, 6h cap

### 4.2 PATH B (PROMISING-COMPRESSION)

**Trigger conditions** (one or both):
- IS monthly Sharpe (multi-seed mean) in [+0.30, +0.55) — partial compression on IS axis
- OOS monthly Sharpe (multi-seed mean) in [+0.50, +0.85) — partial compression on OOS axis

**Implication**: iter-v3/025's single-seed magnitude was somewhat lottery-favorable, but the underlying feature still provides edge at multi-seed (not pure noise). iter-v3/029 CONFIRMATION still proceeds but with LOWERED expectations.

**Action**: Phase 8 diary catalogs as `MINI-VALIDATION-COMPRESSION`; iter-v3/029 brief authored with bundle as PATH A but with updated predicted bands (lower median expected based on iter-v3/028 multi-seed result). Consider whether the compressed magnitude clears Gate 1+2 floors (≥+1.0 IS+OOS) at iter-v3/029 multi-seed; if marginal, document the risk.

### 4.3 PATH C (FALSIFIED)

**Trigger conditions** (BOTH must hold):
- IS monthly Sharpe (multi-seed mean) < +0.30
- OOS monthly Sharpe (multi-seed mean) < +0.50

**Implication**: iter-v3/025 was single-seed lottery (analogous to iter-v3/013 → iter-v3/018 falsification: 62%/86% reduction). The regime_momentum_signed_5d feature does NOT provide multi-seed-stable signal. iter-v3/029 CONFIRMATION at this bundle is DEAD-ON-ARRIVAL.

**Action**: Phase 8 diary catalogs as `MINI-VALIDATION-FALSIFIED`; iter-v3/029 CONFIRMATION CANCELED with current bundle. Re-evaluate strategy:
- Option (i): pivot to fundamentally different bundle for iter-v3/029 (e.g., iter-v3/013 baseline alone with fracdiff_d05_close as a NEW Category 2 axis untested in post-bootstrap)
- Option (ii): extend EXPLORATION cycle — request 5 additional EXPLORATION axes before next CONFIRMATION (would be cadence #11-15 of an extended cycle)
- Option (iii): accept iter-v3/018 BOOTSTRAP baseline as the binding baseline; defer all next CONFIRMATION attempts pending fundamental architectural changes (different model class, different labeling, different universe)

### 4.4 §4.4 Classification (decision flow)

```
IS Sharpe (multi-seed) | OOS Sharpe (multi-seed) | Verdict
─────────────────────────────────────────────────────────────
≥ +0.55                 | ≥ +0.85                 | PATH A (PROMISING-CONFIRMED)
≥ +0.30                 | < +0.85                 | PATH B (PROMISING-COMPRESSION)
< +0.55                 | ≥ +0.50                 | PATH B (PROMISING-COMPRESSION)
< +0.30                 | < +0.50                 | PATH C (FALSIFIED)
```

**Decisive axis**: Both IS and OOS must pass for PATH A. Either alone falling short triggers PATH B (compression). Both falling short triggers PATH C (falsified).

**Rationale**: At --seeds 2 multi-seed, both IS and OOS are now controlled axes (vs single-seed EXPLORATION where only IS is decisive). The seed-averaging variance reduction makes both axes diagnostically relevant.

---

## Section 5 — Risk Mitigation

### 5.1 Compute risk

- Wall-clock target: ~30 min (vs ~14 min at iter-v3/025 single-seed). 2.1× multiplier reasonable given ENSEMBLE_SIZE 1 → 5 + 1 outer → 2 outer (additive overhead because Optuna trials are reused per outer seed; the multiplier is closer to 2.1× than 10×).
- Hard cap: 1h. If --seeds 2 multi-validation runs longer than 1h, the QE must abort and report.
- Cap is conservative — iter-v3/018 CONFIRMATION at --seeds 2 + n_trials=1500 + ENSEMBLE_SIZE=5 ran in ~5h; at n_trials=35 (matching this iter-v3/028) the budget is ~1/40th of iter-v3/018 CONFIRMATION compute.

### 5.2 Reproducibility risk

- iter-v3/028 must produce DETERMINISTIC results given the same code + data + seeds. Outer seeds 42 + 123 are FIXED.
- The 5-inner ensemble seeds derive from outer seed via `_derive_ensemble_seeds(outer_seed, size=5)`. Same as iter-v3/018 CONFIRMATION.
- The QE must note in the engineering report: HEAD SHA at backtest run, V3_FEATURE_COLUMNS list (post-revert; should be 14 entries with regime_momentum_signed_5d present and cross_asset_divergence_norm/vol_adj_autocorr ABSENT).

### 5.3 PATH C (FALSIFIED) downstream-decision risk

- If PATH C fires, the entire 9-EXPLORATION post-bootstrap cycle has produced ZERO multi-seed-validated PROMISING results. This is a structural outcome the QR must accept honestly.
- Mitigation: the diary entry in Phase 8 must NOT bury the falsification. The catalog row must explicitly note `MINI-VALIDATION-FALSIFIED` and `iter-v3/029 CONFIRMATION CANCELED with current bundle`.
- This iteration is informational regardless of outcome — even PATH C is a successful compute investment because it prevents wasting the iter-v3/029 CONFIRMATION budget.

### 5.4 Concentration risk (single-symbol carry)

- iter-v3/025 single-seed had TRX 71% concentration (above Gate 7 30% threshold). At multi-seed, concentration may compress to a lower ceiling but remains structurally high in 3-symbol BCH+LDO+TRX universe.
- iter-v3/018 CONFIRMATION at multi-seed had TRX 66% / 56% across 2 outer seeds (mean ~61%). iter-v3/028 is expected to fall in a similar range.
- Concentration is NOT a verdict-blocking criterion at iter-v3/028 mini-validation; it is informational. Gate 7 evaluation is deferred to iter-v3/029 CONFIRMATION.

### 5.5 OOS trade count

- iter-v3/025 single-seed had 95 OOS trades (below 130 floor; informational at EXPLORATION).
- iter-v3/028 at --seeds 2 + ENSEMBLE_SIZE=5 should produce more OOS trades (each outer seed produces trades; mean OOS trades expected to be ~95-180 per seed × 2 seeds = ~190-360 BUNDLE OOS trades — clears 130 floor at bundle level per `feedback_v3_trade_rate_floor_bundle_level.md`).
- Trade-rate floor at the BUNDLE level is the binding criterion at iter-v3/029 CONFIRMATION; iter-v3/028 mini-validation provides directional evidence on whether the bundle clears.

---

## Section 6 — Falsifiers

### 6.1 Falsifier 1 — Methodology check fails

If any of the 12 standard methodology checks FAIL or produce unexpected output (look-ahead audit, track isolation grep, embargo width, REQUIRED_GAP=66, DSR/PBO/PSR computation, pareto_front.csv generation), iter-v3/028 is INVALID and must be re-run after fix. This is operational, not a verdict.

### 6.2 Falsifier 2 — Compute budget exceeded

If wall-clock exceeds 1h hard cap, iter-v3/028 is ABORTED. The QE reports the abort to the QR; the QR re-evaluates whether to retry with --seeds 1 first OR proceed directly to iter-v3/029 CONFIRMATION (with full budget commitment).

### 6.3 Falsifier 3 — Saturation behavioral effect

Per `feedback_axis_saturation_predictor.md`, every EXPLORATION brief Section 2 must include behavioral-effect predictor with explicit estimate of how many IS trades will change.

iter-v3/028 IS trade count predicted band: [129, 215] mean ~194 (matches iter-v3/025 single-seed 194 IS trades; multi-seed at --seeds 2 produces ~mean of per-seed counts; --seeds 2 inner-ensemble produces a single per-seed trade roster ensemble-averaged). At --seeds 2 mean trade count expected within iter-v3/025's range.

If observed IS trade count at --seeds 2 is OUTSIDE [129, 215] band by > 25%, this is informational anomaly (not verdict-blocking). The behavioral effect of multi-seed on trade roster is via ensemble averaging — different outer seed produces a different LightGBM model, which may take different trades. The aggregate trade count at --seeds 2 is a sum across both seeds.

### 6.4 Falsifier 4 — Per-cell PBO max regression

If iter-v3/028's PBO max-aggregator across all (cell × seed) combinations exceeds 0.85 (vs iter-v3/018 CONFIRMATION's PBO max=1.0 on TRX/2022-Q4 + LDO/2026-03), this is informational. The TRX/2022-Q4 regime gate from iter-v3/022 was PARTIALLY-EFFECTIVE; LDO/2026-03 data-scarcity is structural. PBO max is NOT a verdict-blocking criterion at iter-v3/028 (mini-validation); Gate 5 evaluation is deferred to iter-v3/029 CONFIRMATION.

### 6.5 Falsifier 5 — IS/OOS daily Sharpe ratio anomaly

Per iter-v3/026/027 SUSPICIOUS-OOS pattern (27× and -2.24× IS/OOS daily Sharpe ratios respectively), iter-v3/028 must produce IS/OOS daily Sharpe ratio in the NORMAL range (e.g., between 0.5 and 2.0). If observed ratio is outside this range, the result is structurally suspect and the QR must flag it in Phase 8 diary as anomalous (similar to iter-v3/026 NEGATIVE-SUSPICIOUS-OOS classification).

iter-v3/025 single-seed had IS/OOS daily ratio 0.92 (normal range). At multi-seed --seeds 2, the expected range is similar (0.5-2.0). If iter-v3/028 produces a ratio outside this range, the verdict classification may need to incorporate a SUSPICIOUS qualifier.

---

## Section 7 — Pre-Commits

The following are LOCKED at brief-publication time (THIS commit). Cannot be renegotiated post-hoc per `feedback_iteration_quality.md` + Critic FINAL `966f4c1` of iter-v3/027 + user directive 2026-05-08.

1. **Hypothesis** is iter-v3/025's single-seed +0.88 IS / +1.22 OOS holds at multi-seed --seeds 2 with similar magnitude (within ±0.30 on each axis).
2. **Predicted bands**: IS Sharpe [+0.55, +1.10] median +0.80; OOS Sharpe [+0.85, +1.40] median +1.10.
3. **§4.4 Classification** is the LOCKED decision flow:
   - PATH A: IS ≥ +0.55 AND OOS ≥ +0.85
   - PATH B: IS [+0.30, +0.55) OR OOS [+0.50, +0.85)
   - PATH C: IS < +0.30 AND OOS < +0.50
4. **Falsifiers** 1-5 are LOCKED with thresholds and informational/blocking distinctions.
5. **iter-v3/029 CONFIRMATION bundle** is LOCKED single-feature MINIMAL: iter-v3/013 baseline + regime_momentum_signed_5d at --seeds 2 + n_trials=35 + ENSEMBLE_SIZE=5; 6h cap.
6. **Behavioral-effect predictor**: IS trade count band [129, 215] mean ~194.
7. **Saturated axes** (must be SKIPPED in iter-v3/029+): off-the-shelf indicator additions (microstructure, funding family per-symbol + cross-asset BTC), engineered-feature stacking at single-seed, per-symbol PnL cap mechanism, universe expansion HBAR+AVAX, BTC trend filter ±15% (no effect), ADX threshold 25 (highest negative OOS delta).
8. **Open Category 2 (engineered features) for iter-v3/030+ if iter-v3/029 NEGATIVE**:
   - fracdiff_d05_close (López de Prado AFML Ch. 5; explicit v3 skill mandate from iter-v3/001 scope)
   - hurst_drift_50_200 = hurst_50 − hurst_200 (multi-timeframe regime drift; requires hurst_50/hurst_200 primitives not currently in V3_FEATURE_COLUMNS)
   - adx_signed_momentum (REJECTED at iter-v3/025 EDA but worth retesting if regime_momentum_signed_5d falsifies)

---

## Section 8 — Catalog Carry-Forwards (Background Context)

This iteration carries forward from prior iterations:

- **iter-v3/027 closeout SHA `ef48e94`**: third engineered feature stacking (cross_asset_divergence_norm) FALSIFIED at single-seed; 3-iter monotonic IS degradation pattern REPLICATED across 2 stacking compositions; ONLY iter-v3/025 PROMISING survives.
- **iter-v3/026 closeout SHA `1b60947`**: second engineered feature stacking (vol_adj_autocorr) FALSIFIED at single-seed; engineered features DON'T STACK at single-seed; NEW memory rule `feedback_v3_engineered_features_dont_stack.md` enshrined.
- **iter-v3/025 closeout SHA `511934a`**: regime_momentum_signed_5d PROMISING (single-seed; multi-seed validation deferred to iter-v3/028 mini-validation + iter-v3/029 CONFIRMATION); first Category 2 axis in v3 catalog; STRONG CONFIRMATION-BUNDLE CANDIDATE.
- **iter-v3/024 closeout SHA `5a47f5d`**: funding family (per-symbol + cross-asset BTC) PERMANENTLY CLOSED for v3 across 3 EXPLORATION data points.
- **iter-v3/022 closeout SHA `da7047c`**: TRX/2022-Q4 regime gate axis PARTIALLY-EFFECTIVE-CLOSED; CONFIRMATION re-evaluation deferred to iter-v3/029+.
- **iter-v3/021 closeout SHA `92290fd`**: HBAR + AVAX universe expansion CLOSED-symbols-cycle.
- **iter-v3/020 closeout SHA `5287bd6`**: per-symbol PnL share cap CLOSED-mechanism.
- **iter-v3/018 closeout SHA `199cbe4`**: FIRST v3 CONFIRMATION COMPLETE with OUTCOME = `CONFIRMATION-MERGE-BOOTSTRAP`. BASELINE_V3.md established. iter-v3/013 single-seed +1.0088 IS / +2.6970 OOS Sharpe formally FALSIFIED (62%/86% reduction). Outstanding constraints: Gate 1 IS Sharpe floor (lift +0.62), Gate 2 OOS Sharpe floor (lift +0.61), Gate 4 DSR (structural — reformulate gate), Gate 5 PBO max-aggregator, Gate 7 top-symbol concentration (TRX 66%; structural 3-symbol universe), Gate 8 bundle OOS trades < 130.

EXPLORATION-mode DSR/PSR INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md`. iter-v3/028 at --seeds 2 NOT --exploration → DSR/PSR may be informative beyond the EXPLORATION-mode artifact.

Cadence: 9 of 10 EXPLORATIONs done in post-bootstrap cycle; iter-v3/028 = MINI-VALIDATION (10th of 10); iter-v3/029 = CONFIRMATION (earliest); EXPLORATION cap 2h; CONFIRMATION cap 6h.

---

## Section 9 — Hand-Off

After this brief is published (THIS commit; SHA TBD):
1. **Phase 5.5 Critic gate**: Critic reads brief + verifies §0.5 type declaration is correct (SPECIAL EXPLORATION — MINI-VALIDATION) + verifies §2 implementation spec is consistent with iter-v3/025 anchor + verifies §4 classification thresholds align with `feedback_v3_outer_seed_cap_2_v3.md` + recommendations align with Critic FINAL `966f4c1`. If Critic gate PASS, proceed to Phase 6.
2. **Phase 6 — Engineer setup**: QE applies §2 implementation (drop cross_asset_divergence_norm from V3_FEATURE_COLUMNS_TOP_N; update _verify_feature_columns; update ITERATION_LABEL=v3-028; verify track-isolation grep PASS; verify pre-existing past-only adversarial tests still pass).
3. **Phase 6 — Engineer dispatch**: Run `uv run python run_baseline_v3.py --seeds 2`. Wall-clock budget ~30 min target / 1h hard cap.
4. **Phase 6 — Engineer report**: After backtest completes, write `briefs-v3/iteration_v3-028/engineering_report.md` with HEAD SHA, V3_FEATURE_COLUMNS list, headline metrics from comparison.csv, dsr.json, seed_summary.json, per-symbol attribution, importance comparison.
5. **Phase 7 — Critic FINAL review**: Critic verifies methodology, classifies §4 PATH A/B/C, recommends iter-v3/029 next steps.
6. **Phase 8 — QR diary**: Diary catalogs as `MINI-VALIDATION-CONFIRMED` / `MINI-VALIDATION-COMPRESSION` / `MINI-VALIDATION-FALSIFIED`; iter-v3/029 launch decision based on outcome.

QR is NOT modifying production code. The iter-v3/028 implementation belongs to Engineer (Phase 6). Brief is research only.

---

## Reproducibility Stamp (this brief)

- Setup commit SHA: TBD (will be assigned by QE in Phase 6 first commit)
- Brief SHA: TBD (this commit)
- Phase 5.5 gate SHA: TBD
- Engineering+Critic FINAL SHA: TBD
- HEAD SHA at backtest run: TBD
- Reports: `reports-v3/iteration_v3-028/comparison.csv`, `dsr.json`, `seed_summary.json`, `pareto_front.csv`, `ic_matrix.csv`, `in_sample/model_importance_last_month_*.csv`
- Tag (informational): NONE (mini-validation; not a baseline-update event regardless of outcome)

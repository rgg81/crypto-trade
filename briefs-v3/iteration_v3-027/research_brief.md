# Iteration v3-027 — Research Brief

**Type**: EXPLORATION (cadence #9 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 2 — GENUINE FEATURE ENGINEERING — DIFFERENT engineered feature ALONE — NOT STACKED)** — `cross_asset_divergence_norm` per Critic FINAL Recommendation of iter-v3/026 (review SHA `8839bbb`) + user directive 2026-05-08)
**Track**: v3 (rigor arm) — twenty-seventh iteration
**Branch**: `iteration-v3/027` (off `iteration-v3/026` head; brief authored after EDA committed at SHA `254a5f2`)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (PRELIMINARY-VALIDATED through iter-v3/020-026)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–026 briefs / engineering reports / Critic FINALs / diaries; the new iter-v3/027 EDA at SHA `254a5f2` (`analysis/iteration_v3-027/third_engineered_eda.py` + outputs).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #9 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: DIFFERENT GENUINE FEATURE ENGINEERING — composed feature
                       ALONE on top of regime_momentum (NOT STACKED).
                       DROP vol_adj_autocorr from V3_FEATURE_COLUMNS (revert
                       15 → 14; iter-v3/026 stacking falsified).
                       KEEP regime_momentum_signed_5d (proven at iter-v3/025).
                       ADD cross_asset_divergence_norm (14 → 15). COMPOSED
                       feature: (sym_ret_7d − btc_ret_14d) / (|vwap_dev_20|
                       + 1e-6) — relative-strength normalized.
                       Per Critic FINAL Rec of iter-v3/026 (SHA `8839bbb`)
                       + user directive 2026-05-08 + diary lessons (a)-(g).
Cadence: EXPLORATION #9 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 2 (GENUINE FEATURE ENGINEERING — DIFFERENT composed feature
               ALONE; THIRD Category 2 axis in v3 catalog; first was iter-v3/025
               regime_momentum_signed_5d PROMISING; second was iter-v3/026
               vol_adj_autocorr stacked NEGATIVE-SUSPICIOUS-OOS — DROPPED here)
ANCHOR (formal BASELINE_V3.md anchor): iter-v3/018 BOOTSTRAP baseline
        (multi-seed mean +0.3788 IS / +0.3869 OOS)
REFERENCE (single-seed parent — iter-v3/025): iter-v3/025 (+0.8788 IS / +1.2244 OOS;
        regime_momentum_signed_5d ALONE — single-seed reference; PROMISING but
        lottery-suspect per `feedback_v3_single_seed_frozen_baseline.md`)
PRECEDENT (single-seed iter-v3/026 NEGATIVE): iter-v3/026 (+0.0493 IS / +1.4501 OOS;
        regime_momentum + vol_adj_autocorr STACKED — IS Sharpe collapse + OOS
        spike; 27× IS/OOS daily Sharpe ratio is structurally absurd)
NOT a gate-threshold knob. NOT an off-the-shelf indicator addition.
NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED).
NOT a stacking experiment (single replacement, not addition).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — DIFFERENT engineered feature ALONE (per Critic FINAL `8839bbb` of iter-v3/026 Recommendation + user directive 2026-05-08)**:

After iter-v3/025 EXPLORATION-PROMISING (clean) and iter-v3/026 EXPLORATION-NEGATIVE-SUSPICIOUS-OOS:

- **iter-v3/025**: `regime_momentum_signed_5d` ALONE produced clean PROMISING (IS +0.50 / OOS +0.84 vs anchor; importance 51% of top portfolio; co-directional IS+OOS lift). FIRST PROMISING in post-bootstrap cycle.
- **iter-v3/026**: stacking `vol_adj_autocorr` ON TOP produced NEGATIVE-SUSPICIOUS-OOS — IS Sharpe collapse to +0.0493 (PATH C fires; lowest IS Sharpe in any post-bootstrap iteration) + OOS spike to +1.4501 (single-seed-suspect; 27× IS/OOS daily Sharpe ratio is structurally absurd). vol_adj_autocorr was NOT inert (importance 283 = 45% of top — Falsifier 4 PASSES; rules out PROMISING-INERT). Mechanism: combining 2 engineered features at single-seed n_trials=35 expands Optuna search space beyond depth-3-5 LightGBM's representational capacity.
- **NEW memory rule** `feedback_v3_engineered_features_dont_stack.md` (established at iter-v3/026 closeout): test ONE engineered feature alone at single-seed; defer stacking experiments to multi-seed CONFIRMATION (iter-v3/029+) when n_eff is higher.
- **iter-v3/027 axis disambiguates**: was iter-v3/026's destabilization vol_adj_autocorr-specific (a particular composed-feature interaction broke things), OR a structural property of stacking 2 engineered features at single-seed at n_trials=35? Testing a DIFFERENT engineered feature ALONE on top of regime_momentum (vol_adj_autocorr DROPPED) isolates this.
- **User directive 2026-05-08**: confirmed mandate to validate the FEATURE ENGINEERING pivot consistently. iter-v3/026 specifically named `cross_asset_divergence_norm` as the recommended NEXT candidate.
- **Critic FINAL Recommendation of iter-v3/026**: "iter-v3/027 axis = DIFFERENT engineered feature, ALONE on top of regime_momentum: drop vol_adj_autocorr; try cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6) — different mechanism (relative-strength); uses existing primitives; predicted bands similar to iter-v3/025 [+0.30, +0.55] IS / [+0.40, +0.65] OOS."
- Forward priority order from prior iterations + new catalog state:
  1. **HIGH — DIFFERENT GENUINE FEATURE ENGINEERING composed-feature axis ALONE (iter-v3/027 mandate, this iteration)**: validates pivot consistency at single-feature scale
  2. HIGH — ALTERNATIVE engineered feature (iter-v3/028) IF iter-v3/027 PATH A
  3. MEDIUM — DSR gate reformulation
  4. LOW — Knob axes (saturated)
  5. LOW — Universe expansion alternative symbols (ATOM/FIL/ALGO)

**iter-v3/027 first EXPLORATION axis = HIGH-priority — `cross_asset_divergence_norm` DIFFERENT composed feature, ALONE.** Cannot be renegotiated post-hoc per Critic FINAL `8839bbb` of iter-v3/026 + user directive 2026-05-08 + memory rule `feedback_v3_engineered_features_dont_stack.md`.

**Why DIFFERENT engineered feature ALONE now (post iter-v3/026 NEGATIVE-SUSPICIOUS-OOS)**:

- **The disambiguation question is binding for the entire post-bootstrap cycle.** If iter-v3/027 PROMISING (a different engineered feature alone produces clean co-directional IS+OOS lift), then the iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking-budget artifact at single-seed; engineered features can be tested SEQUENTIALLY (one at a time) but not stacked at single-seed. If iter-v3/027 NEGATIVE (a different engineered feature alone STILL produces destabilization), then the engineered-features pivot is genuinely narrow — only specific compositions work, not a generally productive category.
- **The structural-orthogonality criterion (max |IC|_rm vs regime_momentum_signed_5d) is informational but key**: cross_asset_divergence_norm's per-symbol max |IC|_rm = 0.376/0.464/0.261 (BCH/LDO/TRX) per EDA SHA `254a5f2`. Higher overlap with regime_momentum than ret_kurt_to_skew_ratio (max |IC|_rm 0.075) BUT mechanism is distinct (cross-asset relative strength vs regime-conditional momentum). The IC overlap reflects shared variance through `sym_vs_btc_ret_7d` (already in the 14-feature set), not through regime_momentum directly.
- **Mechanism distinctness vs both prior engineered features**:
  - `regime_momentum_signed_5d` (iter-v3/025; KEPT): directional 5-day return × Hurst regime classifier — encodes momentum-vs-mean-reversion regime sign-flip via close-derived ret_5d × hurst_100
  - `vol_adj_autocorr` (iter-v3/026; DROPPED at iter-v3/027): lag-1 return persistence / range-realized vol — encodes per-unit-vol return persistence
  - `cross_asset_divergence_norm` (iter-v3/027 axis): alt-vs-BTC return divergence / vwap-deviation — encodes relative-strength normalized by mean-reversion intensity
  - Source primitives are NON-OVERLAPPING with regime_momentum's primitives (sym_ret_7d/btc_ret_14d/vwap_dev_20 vs close-derived ret_5d/hurst_100) → genuine new interaction signal, not a variation of regime momentum
- Per Robert Carver (*Systematic Trading*) + Ernest Chan (*Quantitative Trading*): relative-strength normalization is a textbook systematic-trading technique. The depth-3-5 LightGBM trees can split on raw `sym_vs_btc_ret_7d` (rank 13 in feature set) and raw `vwap_dev_20` (rank 11) and raw `btc_ret_14d` (rank 9) independently but cannot represent the 3-way ratio `(f1 - f2) / |f3|` at the candidate-split level — making this an interaction the model cannot internally compose.

**Why this experiment is inexpensive at iter-v3/027**:

- Existing primitives: `sym_ret_7d` (computable from close at the symbol level), `btc_ret_14d` (rank 9 in 14-feature set), `vwap_dev_20` (rank 11 in 14-feature set). All present in features parquet for BCH/LDO/TRX.
- Implementation: extend existing module `engineered_v3.py` (introduced at iter-v3/025; vol_adj_autocorr removed) with `compute_cross_asset_divergence_norm` that computes `(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)`. ~10 lines of code.
- Wall-clock impact: +1 feature column (replacing vol_adj_autocorr; net column count unchanged at 15). Total wall-clock predicted 8-15 min (well within 2h cap).

After iter-v3/027 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PERMANENTLY-CLOSED per-symbol variant) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + NEW external-data-source feature RETEST × 1 (CLOSED-PERMANENTLY) + NEW external-data-source CROSS-ASSET variant × 1 (CLOSED-FAMILY-WIDE) + GENUINE FEATURE ENGINEERING composed-feature × 1 (PROMISING — iter-v3/025) + GENUINE FEATURE ENGINEERING SECOND composed-feature stacked × 1 (NEGATIVE-SUSPICIOUS-OOS — iter-v3/026; STACKING-FALSIFIED-AT-SINGLE-SEED) + **GENUINE FEATURE ENGINEERING DIFFERENT composed-feature ALONE × 1 (this iteration)** = 19 unique axis representations after iter-v3/027; **third Category 2 axis in v3 catalog**.

---

## Section 1 — Hypothesis

Adding `cross_asset_divergence_norm` (= `(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)`) — relative-strength normalized by mean-reversion intensity — as the 15th feature on top of the iter-v3/025 14-feature stack (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 14 V3_FEATURE_COLUMNS including regime_momentum_signed_5d AND **with vol_adj_autocorr DROPPED — iter-v3/026 stacking falsified**) — at the EXPLORATION default n_trials=35 — will produce **importance rank ≤10 for ≥1 symbol AND importance ≥30 for ≥1 cut** (Category 2 carve-out per `feedback_v3_engineered_feature_pivot.md`) AND **IS Sharpe Δ ≥ −0.40 vs iter-v3/025 reference** (relaxed lower-bound to capture the disambiguation outcome surface; the binding test is whether IS does NOT collapse below +0.30 as iter-v3/026 did) — if the cross-asset relative-strength mechanism is genuinely informative AND structurally distinct from regime_momentum's regime-conditional momentum mechanism AND the LightGBM trees on the 14-feature stack cannot internally compose `(f1 - f2) / |f3|` at depth-5.

Predicted IS Sharpe band [+0.50, +0.95] median +0.75 vs iter-v3/025 single-seed reference +0.8788; predicted OOS Sharpe band [+0.60, +1.30] median +1.00 vs iter-v3/025 single-seed reference +1.2244 (relaxed from "lift" to "maintain": the iter-v3/025 OOS result is already strong; the second engineered feature ALONE should at minimum NOT REGRESS to iter-v3/026's IS-collapse outcome, with a marginal additional lift if the relative-strength mechanism captures incremental signal not already encoded by regime_momentum). **Predicted IS NOT to collapse to <0.30** (iter-v3/026 was 0.05); a collapse below 0.30 would falsify the disambiguation hypothesis and prove the engineered-features pivot is single-feature-narrow (only regime_momentum_signed_5d works at this architecture).

**Mechanism explanation** (why cross-asset divergence normalized should surface where raw sym_vs_btc_ret_7d, btc_ret_14d, vwap_dev_20 alone don't):

The composed feature `(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)` encodes a textbook systematic-trading heuristic from Robert Carver (*Systematic Trading*) + Ernest Chan (*Quantitative Trading*): **alt-vs-BTC return divergence is a meaningful signal only when normalized by the alt's local mean-reversion intensity**. The same alt-BTC divergence has different implications:
- High `|sym_ret_7d - btc_ret_14d|`, low `|vwap_dev_20|` (low mean-reversion intensity; price near VWAP) → genuine relative-strength signal worth trading
- High `|sym_ret_7d - btc_ret_14d|`, high `|vwap_dev_20|` (high mean-reversion intensity; price far from VWAP) → divergence may already be priced in or about to revert; chasing it is value-trap

A LightGBM tree of depth 5 on the raw 14-feature stack containing `sym_vs_btc_ret_7d` (rank 13) AND `btc_ret_14d` (rank 9) AND `vwap_dev_20` (rank 11) would need to (a) split first on `vwap_dev_20` magnitude, (b) split on `sym_vs_btc_ret_7d` direction in each branch SEPARATELY with INVERTED interpretation conventions for high/low vwap_dev, and (c) preserve enough remaining splits for the actual decision boundary. The depth-5 budget combined with `colsample_bytree=1.0` HARDCODED at EXPLORATION makes this composition difficult to learn from data; a single hyperparameter trajectory at n_trials=35 may not converge on the right tree structure even if the signal exists. **The composed feature precomputes this 3-way ratio**, freeing tree capacity for actual decision splits.

**Note on horizon mismatch**: The composed feature uses `sym_ret_7d` (21-bar trailing) MINUS `btc_ret_14d` (42-bar trailing). The mismatch encodes a momentum-divergence concept: when the symbol's recent 7-day momentum diverges from BTC's longer-window 14-day momentum, the relative-strength signal is information-rich. This is structurally distinct from `sym_vs_btc_ret_7d` (already in feature set as 7d alt minus 7d BTC) which uses matching horizons.

**Why prior iterations don't directly predict iter-v3/027's outcome**:

- iter-v3/015 microstructure tbr_zscore_30 INERT, iter-v3/019/023/024 funding INERT: ALL four failures were OFF-THE-SHELF indicator additions. iter-v3/027 is a **COMPOSED feature** built from existing primitives.
- iter-v3/025 regime_momentum_signed_5d PROMISING: SAME axis category as iter-v3/027 (Category 2). iter-v3/025 used close-derived ret_5d × hurst_100; iter-v3/027 uses (sym_ret_7d − btc_ret_14d) / |vwap_dev_20|. The iter-v3/025 result confirms Category 2 axes can succeed in v3; iter-v3/027 tests whether the success generalizes to a structurally orthogonal mechanism (different source primitives, different interaction structure).
- iter-v3/026 vol_adj_autocorr STACKED was NEGATIVE-SUSPICIOUS-OOS: SAME axis category (Category 2) but STACKED on top of regime_momentum (V3_FEATURE_COLUMNS 14 → 15). iter-v3/027 is a SINGLE REPLACEMENT (not stack): drop vol_adj_autocorr, add cross_asset_divergence_norm — net column count UNCHANGED at 15 BUT the new feature replaces the failed one. **Critical distinction**: iter-v3/027 is structurally NOT iter-v3/026 retried — it's the disambiguation experiment specifically designed to isolate "vol_adj_autocorr-specific destabilization" vs "stacking-budget destabilization at single-seed".
- The hypothesis is falsifiable in 3 directions: (a) PROMISING (PATH A) — IS does NOT collapse, OOS positive, importance ≥30 → engineered features can be replaced/swapped at single-seed (one alone at a time); (b) PROMISING-INERT (PATH B) — new feature 14/14 importance → engineered category narrowly succeeds (only regime_momentum); (c) NEGATIVE (PATH C) — IS collapse below +0.30 → destabilization is NOT vol_adj_autocorr-specific; engineered stacking is structurally fragile at single-seed even with 1 new feature. Each pathway has distinct downstream implications.

**Direction symmetry**: cross_asset_divergence_norm is naturally symmetric: positive divergence (alt outperforming BTC) / low vwap_dev → trade momentum-continuation; negative divergence / low vwap_dev → trade reversion (alt underperformance reverses). The vwap-deviation normalization scales the magnitude based on local mean-reversion intensity.

EDA rank-IC results (per EDA SHA `254a5f2`):
- BCH: h=1 −0.026, h=3 −0.016, h=7 −0.034 (slight reversal-direction signal at h=7)
- LDO: h=1 −0.039, h=3 −0.074, h=7 **−0.109** (STRONGEST reversal-direction signal among 4 candidates × 3 symbols)
- TRX: h=1 +0.016, h=3 +0.009, h=7 −0.001 (near-zero; signal is LDO-driven)

**Pattern**: cross_asset_divergence_norm has strongest reversal-direction signal on LDO (high alt-BTC divergence at low vwap-dev predicts negative forward returns — i.e., divergence over-extension reverts), weak reversal on BCH, near-zero on TRX. This is consistent with LDO being more sensitive to liquidity dynamics + BTC-pair relative strength patterns, while TRX has distinct macro behavior.

---

## Section 2 — Implementation Spec

### 2.1 Atomic feature swap (single axis preserved)

iter-v3/027 first commit must atomically:
1. **DROP** `vol_adj_autocorr` from `V3_FEATURE_COLUMNS_TOP_N` (revert 15 → 14; iter-v3/026 stacking falsified per `feedback_v3_engineered_features_dont_stack.md`).
2. **KEEP** `regime_momentum_signed_5d` in `V3_FEATURE_COLUMNS_TOP_N` (iter-v3/025 PROMISING — proven; do NOT revert).
3. **ADD** `cross_asset_divergence_norm` to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15).
4. Net column count: 15 (unchanged from iter-v3/026; ONE feature replaced ATOMICALLY).
5. Single axis preserved: ATOMIC SWAP (drop vol_adj_autocorr + add cross_asset_divergence_norm = 1 axis change at single-feature scale; not a stacking experiment); other gates BYTE-IDENTICAL to iter-v3/025/026 anchor (z=2.0, ATR 2.0/1.0, BTC ±15%, ADX=20, Hurst, low-vol, hit-rate disabled, regime gate disabled, per-symbol cap disabled).

### 2.2 Module structure

**Existing module**: `src/crypto_trade/features_v3/engineered_v3.py` (introduced at iter-v3/025; vol_adj_autocorr added at iter-v3/026 — REMOVED from `add_engineered_v3_features` dispatch order at iter-v3/027; the function `compute_vol_adj_autocorr` may be retained as dead code at zero revert cost OR deleted).

**New function**: `compute_cross_asset_divergence_norm(df: pd.DataFrame) -> pd.DataFrame` — consumes `btc_ret_14d` + `vwap_dev_20` (both upstream) and computes `sym_ret_7d` from `close` (21-bar trailing log return), returns df with `cross_asset_divergence_norm` column appended.

```python
_CROSS_ASSET_DIVERGENCE_EPS: float = 1e-6
_CROSS_ASSET_DIVERGENCE_CAP: float = 100.0


def compute_cross_asset_divergence_norm(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + EPS).

    Past-only by construction:
    - sym_ret_7d = log(close_t / close_{t-21}) at 8h cadence (21 bars × 8h = 7 days)
      computed inline via .shift(21); past-only.
    - btc_ret_14d already past-only (cross_btc_v3.py 42-bar trailing window;
      uses BTC close with 42-bar shift).
    - vwap_dev_20 already past-only (volume_micro_v3.py 20-bar trailing VWAP).
    Output clipped to [-CAP, +CAP] to prevent infinity from near-zero denominators.
    """
    df = df.copy()
    if "btc_ret_14d" not in df.columns:
        df["cross_asset_divergence_norm"] = np.nan
        return df
    if "vwap_dev_20" not in df.columns:
        df["cross_asset_divergence_norm"] = np.nan
        return df

    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 21 bars at 8h cadence = 7 calendar days (matches sym_ret_7d in cross_btc_v3.py)
    sym_ret_7d = log_close - log_close.shift(21)

    btc_ret_14d = df["btc_ret_14d"].astype(float)
    vwap_dev = df["vwap_dev_20"].astype(float)
    raw = (sym_ret_7d - btc_ret_14d) / (vwap_dev.abs() + _CROSS_ASSET_DIVERGENCE_EPS)
    df["cross_asset_divergence_norm"] = raw.clip(
        lower=-_CROSS_ASSET_DIVERGENCE_CAP, upper=_CROSS_ASSET_DIVERGENCE_CAP
    )
    return df
```

**Update** `add_engineered_v3_features` to dispatch BOTH compute functions for the engineered category (regime_momentum_signed_5d FIRST, then cross_asset_divergence_norm; vol_adj_autocorr REMOVED from dispatch):

```python
def add_engineered_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """GROUP_REGISTRY entry point for all Category 2 (composed) v3 features.

    iter-v3/027: vol_adj_autocorr DROPPED from dispatch (iter-v3/026 stacking
    falsified per feedback_v3_engineered_features_dont_stack.md).
    cross_asset_divergence_norm ADDED — DIFFERENT engineered feature ALONE on top
    of regime_momentum_signed_5d.
    """
    df = compute_regime_momentum_signed_5d(df)        # iter-v3/025 (KEPT)
    df = compute_cross_asset_divergence_norm(df)      # iter-v3/027 (NEW)
    # compute_vol_adj_autocorr DROPPED at iter-v3/027 — function retained as
    # dead code at zero revert cost; restored ONLY for multi-seed CONFIRMATION
    # stacking experiments at iter-v3/029+.
    return df
```

**Order dependency**: `engineered_v3` already runs AFTER `regime` (which produces `hurst_100` — needed for compute_regime_momentum_signed_5d), AFTER `volume_micro` (which produces `vwap_dev_20`), AFTER `cross_btc` (which produces `btc_ret_14d`). The current GROUP_REGISTRY insertion order is `regime → tail_risk → price_efficient_vol → momentum_accel → volume_micro → cross_btc → engineered_v3 → fracdiff → microstructure_v3 → funding_v3 → btc_funding_v3`. All 3 source primitives (close, btc_ret_14d, vwap_dev_20) are computed before engineered_v3 runs.

### 2.3 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**IS trade count predictor**: the new feature replaces vol_adj_autocorr at the 15th column at `colsample_bytree=1.0`; its incremental effect on tree-split structure is non-trivial but bounded. Predicted IS trade band based on prior +1-feature iterations and recent reference points:

| Iteration | New feature | IS trades | Δ from baseline |
|---|---|---:|---:|
| iter-v3/015 | tbr_zscore_30 | 175 | +3 (vs 172 anchor) |
| iter-v3/019 | funding_rate_zscore_30 (n=10) | 209 | +37 (vs 172) |
| iter-v3/023 | funding_rate_zscore_30 (n=35) | 195 | +23 (vs 172) |
| iter-v3/024 | btc_funding_rate_zscore_30 (n=35) | 182 | +10 (vs 172) |
| iter-v3/025 | regime_momentum_signed_5d (n=35; alone) | 194 | +22 (vs 172) |
| iter-v3/026 | regime_momentum + vol_adj_autocorr (n=35; stacked) | 196 | +24 (vs 172) |

Empirical band on iter-v3/018 anchor (172 trades): IS trades ∈ [+3, +37] above 172 → predicted band [175, 209]. References: iter-v3/025 (194; 14-feature) and iter-v3/026 (196; 15-feature). **For iter-v3/027 the swap (drop vol_adj_autocorr + add cross_asset_divergence_norm; net column count UNCHANGED at 15) is expected to shift trade count modestly** (predicted ±20 vs iter-v3/026 reference 196 → band [176, 216]). **Saturation falsifier threshold**: IS trades > 215 (= 1.05 × prior max 209) OR IS trades < 130 (= 0.75 × prior min 172). If observed IS trades are outside [129, 215], the axis behavioral effect is anomalous and the iteration verdict requires saturation-falsifier-FIRES qualifier in catalog row.

**Behavioral-effect predictor for the new feature specifically**: cross_asset_divergence_norm's source primitives have established usage rank — sym_vs_btc_ret_7d (rank 13 mean across iter-v3/018-026 importance trajectories; comparable analog), vwap_dev_20 (rank 11 mean), btc_ret_14d (rank 9 mean — strongly used). The composed ratio is expected to be used at LightGBM importance rank between 9-13 across the 3 symbols, with importance values 50-200 depending on per-symbol Optuna trajectory. The mid-range importance prediction (vs iter-v3/025's regime_momentum at rank 8-9 with importance 232 LDO) reflects the higher max |IC|_rm (0.46 LDO) — some signal overlap with regime_momentum is expected.

### 2.4 PATH classification table (LOCKED — cannot be renegotiated post-hoc)

| Path | Feature importance | IS Sharpe Δ vs iter-v3/025 reference | OOS Sharpe Δ vs iter-v3/025 reference | Verdict |
|---|---|---:|---:|---|
| **A** PROMISING | rank ≤10 for ≥1 symbol AND importance ≥30 | ≥ −0.40 AND IS NOT < +0.30 | informational | engineered-features-stacking-via-replacement works (signal exists; structurally orthogonal mechanism contributes); iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking artifact |
| **B** PROMISING-INERT | rank 14-15/15 across 3+ cuts | informational | informational | engineered-feature axis NARROW for 14-feature stack at iter-v3/027; cross_asset_divergence_norm did not contribute at single-seed |
| **C** NEGATIVE | informational | < +0.30 (IS collapse like iter-v3/026) OR | < +0.40 | feature actively hurts (regime_momentum captured all available signal AND/OR engineered stacking is structurally fragile at single-seed even via swap) — pivot is single-feature-narrow |
| **D** PROMISING-MECHANICAL | trade roster bit-identical to iter-v3/025 OR strict subset | any IS direction | any OOS direction | mechanical accounting effect; not new edge — see iter-v3/013 PROMISING-MECHANICAL precedent |

**PATH A relaxation rationale** (IS Δ ≥ −0.40 vs standard ≥ +0.10): The iter-v3/025 reference IS Sharpe +0.8788 already captures the largest single-feature lift in the post-bootstrap cycle (+0.50 Δ vs anchor). A different engineered feature with structurally distinct mechanism is hypothesized to **not destabilize** the iter-v3/025 result while contributing additional importance. The binding evidence is feature-importance rank ≤10 + importance ≥30 (model usage), with IS NOT collapsing below +0.30 (the iter-v3/026 collapse threshold). PATH C trigger uses absolute floor +0.30 to capture the disambiguation: any IS Sharpe below +0.30 indicates destabilization of the same mechanism class as iter-v3/026 (regardless of OOS). Cannot be renegotiated post-hoc.

**Saturation falsifier (per `feedback_v3_axis_saturation_predictor.md`)**: IS trades outside [129, 215] OR rank/importance behavior outside §2.3 predictor band fires the saturation falsifier. Distinct from PATH classification; can co-fire with any PATH.

### 2.5 Adversarial past-only test (REQUIRED at first commit)

Per past iterations (iter-v3/019/023/024/025/026), every new feature requires an adversarial test confirming past-only computation. Test file: extend `tests/features_v3/test_engineered_v3.py` with new tests for `compute_cross_asset_divergence_norm`:

1. `compute_cross_asset_divergence_norm(df).cross_asset_divergence_norm.iloc[-1]` does NOT change when `df` is appended with future bars (i.e., the value at time t depends only on bars t-42 ... t — the 42-bar window of btc_ret_14d is the longest dependency).
2. The first 41 bars of output are NaN (insufficient history for the upstream rolling 42-bar btc_ret_14d primitive; sym_ret_7d 21-bar would also be NaN for first 21 bars but btc_ret_14d's 42-bar window is dominant).
3. EPS robustness test: `cross_asset_divergence_norm` is finite (not inf) when `vwap_dev_20` is exactly zero (EPS=1e-6 prevents division-by-zero; output clipped to [-100, +100]).
4. Idempotency test: calling `compute_cross_asset_divergence_norm` twice in succession produces identical output (function is pure; no in-place mutation).

### 2.6 Verification — pre-flight gates (Phase 5.5)

Before backtest run, verify:
- [ ] V3_FEATURE_COLUMNS = 15 (NET unchanged from iter-v3/026; vol_adj_autocorr DROPPED; cross_asset_divergence_norm added; regime_momentum_signed_5d KEPT)
- [ ] V3_FEATURE_COLUMNS list matches `_verify_feature_columns` assertion expected length
- [ ] `_verify_feature_columns` updated to assert: `regime_momentum_signed_5d` PRESENT + `cross_asset_divergence_norm` PRESENT + `vol_adj_autocorr` ABSENT
- [ ] `ITERATION_LABEL = "v3-027"` set in runner
- [ ] All 3 v3 features parquets regenerated with new feature column (cross_asset_divergence_norm)
- [ ] Adversarial past-only test PASS (4 new tests for cross_asset_divergence_norm)
- [ ] Track-isolation grep: `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns empty; `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/` returns empty
- [ ] EDA committed at SHA `254a5f2` with all 5 CSVs + synthesis.md

---

## Section 3 — IS-Only Numerical Evidence (EDA at SHA `254a5f2`)

### 3.1 Candidate evaluation (4 of 4)

| Candidate | max |IC|_14 (worst) | max |IC|_rm (worst) | max |rankIC| (best) | ADF (3/3 pass?) | Composite | brief gates? |
|---|---:|---:|---:|---|---:|---|
| **`cross_asset_divergence_norm`** | **0.756** (LDO; sym_vs_btc_ret_7d source overlap) | **0.464** (LDO; partial regime_momentum overlap) | **0.109** (LDO h7 — STRONGEST among 4) | YES | 0.6643 | PASS |
| `ret_kurt_to_skew_ratio` | 0.677 (LDO; ret_kurt_50 source overlap) | 0.075 (LDO worst) | 0.077 (LDO h7) | YES | **0.7322** | PASS |
| `fracdiff_d05_close` | 0.640 (LDO; vwap_dev_20 overlap) | 0.568 (LDO worst) | 0.088 (LDO h7) | NO (TRX p=0.229) | 0.4954 | FAIL |
| `hurst_drift_50_200` | 0.597 (LDO; ret_kurt_50 overlap) | 0.073 (TRX worst) | 0.064 (LDO h7) | YES | 0.694 | PASS |

### 3.2 Brief gates assessment (cross_asset_divergence_norm, the pre-committed axis)

| Gate | Threshold | cross_asset_divergence_norm observed | PASS? |
|---|---|---:|---|
| Coverage IS window per symbol | ≥ 80% | 100.0% (BCH) / 100.0% (LDO) / 100.0% (TRX) | YES |
| Max \|IC\| vs 14 V3_FEATURE_COLUMNS (HARD; INFORMATIONAL) | < 0.70 (info only) | 0.756 (LDO; sym_vs_btc_ret_7d source overlap) | INFORMATIONAL only (Category 2 carve-out) |
| Max \|IC\| vs regime_momentum_signed_5d (orthogonality) | low | 0.464 (LDO worst); 0.376 BCH; 0.261 TRX | INFORMATIONAL only — partial overlap with regime_momentum |
| ADF p-value < 0.05 per symbol | structural stationarity | BCH p≈0; LDO p≈0; TRX p≈0 | YES |
| Max \|rank-IC\| vs forward returns | ≥ 0.02 | 0.109 (LDO h7); 0.034 (BCH h7); 0.016 (TRX h1) | YES (LDO+BCH; TRX bare) |

**4 of 5 binding brief gates PASS, 1 INFORMATIONAL only (IC vs source primitive expected for composed features per Category 2 IC carve-out).**

### 3.3 IC carve-out methodology decision (mirrors iter-v3/025/026 §3.3, LOAD-BEARING for brief acceptance)

**Standard application**: the IC hard gate < 0.70 (BASELINE_V3.md threshold) was designed to flag REDUNDANT off-the-shelf indicator additions — features that share variance with existing primitives and would mechanically duplicate signal already in the feature set.

**Composed-feature application is fundamentally different**: A composed feature like `(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6)` shares variance with its source primitives BY CONSTRUCTION — that's the entire point of a composed feature. Rejecting `cross_asset_divergence_norm` because of IC 0.756 with `sym_vs_btc_ret_7d` would be analogous to rejecting `regime_momentum_signed_5d` because of IC 0.887 with `vwap_dev_20` (which iter-v3/025 cleared via the same carve-out).

**Methodology decision**: The brief explicitly accepts the IC hard-gate failure for `cross_asset_divergence_norm` on the same grounds as iter-v3/025/026:

1. The candidate is a COMPOSED interaction feature (Category 2 axis), not an off-the-shelf indicator addition (Category 1 axis); the IC orthogonality gate is structurally biased high for this category.
2. The HYPOTHESIS under test is precisely whether the COMPOSED form provides INTERACTION value the model can't compose internally — NOT whether the candidate is variance-orthogonal to source primitives.
3. The empirical test that disambiguates the hypothesis is the **feature importance rank** from the LightGBM model itself: if rank ≤10 with importance ≥30, the model is using the composed feature non-trivially despite high source IC.
4. **NEW for iter-v3/027**: max |IC|_rm = 0.464 (LDO worst) is HIGHER than iter-v3/026's vol_adj_autocorr (max |IC|_rm 0.075). This reflects partial mechanism overlap with regime_momentum_signed_5d through the shared `sym_vs_btc_ret_7d` variance pathway. The orthogonality-to-regime_momentum criterion is informational, not binding — the binding test is the LightGBM importance ranking.
5. Per AFML Ch. 8: feature importance under multicollinearity (cluster-based methods) systematically under-attribute composed features that share variance with source primitives. This is a known limitation; the rank ≤10 with non-trivial absolute importance is the correct evidence threshold.

**This methodology decision is documented in Phase 5.5 gate** as an explicit IC-gate carve-out for Category 2 (composed-feature) axes, mirroring iter-v3/025/026 phase5p5_gate.md §IC-Gate Carve-Out.

### 3.4 Why cross_asset_divergence_norm (vs other candidates)

The composite leaderboard ranks `ret_kurt_to_skew_ratio` first (0.7322), `hurst_drift_50_200` second (0.694), `cross_asset_divergence_norm` third (0.6643), `fracdiff_d05_close` fourth (0.4954, ADF FAIL). The pre-commit binds the iter-v3/027 axis to `cross_asset_divergence_norm` independent of leaderboard rank. Justification:

1. **Single-axis discipline pre-commit binds**: iter-v3/026 Critic FINAL Recommendation (review SHA `8839bbb`) + user directive 2026-05-08 pre-committed to `cross_asset_divergence_norm`. Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md` + `feedback_v3_engineered_features_dont_stack.md`.
2. **Strongest predictive signal**: max |rank-IC| 0.109 (LDO h7) is the highest among 4 candidates — the relative-strength normalization provides clean reversal-direction signal at LDO 7-bar horizon. Empirical predictive evidence beats composite ranking when the composite weights orthogonality-to-regime_momentum (which is partially shared by construction).
3. **Tests "model can't compose 3-way ratio" hypothesis directly**: sym_vs_btc_ret_7d is rank 13 mean across iter-v3/018-026 importance trajectories; btc_ret_14d is rank 9 mean (strongly used); vwap_dev_20 is rank 11 mean. The model already uses all 3 source primitives; the question is whether it was COMPOSING the 3-way divergence-normalized ratio internally. If it was, cross_asset_divergence_norm will rank 14-15/15 (PATH B). If it wasn't, cross_asset_divergence_norm will rank ≤10 (PATH A).
4. **Implementation cost LOW**: 10 lines of code in existing `engineered_v3.py` module. All 3 source primitives already in features parquet — zero new computation.
5. **Critic-named recommendation**: iter-v3/026 Critic FINAL Recommendation explicitly named cross_asset_divergence_norm as the candidate with rationale "different mechanism (relative-strength); uses existing primitives; lowest implementation cost; predicted bands similar to iter-v3/025 [+0.30, +0.55] IS / [+0.40, +0.65] OOS". The brief honors this Critic-mandated single-axis pre-commit.
6. **`ret_kurt_to_skew_ratio`** is the leaderboard winner but: (a) NOT named by Critic FINAL Rec (single-axis discipline binds to Critic+user pre-commit), (b) defers to iter-v3/028 NEXT axis IF iter-v3/027 lands PATH B per Section 7.

### 3.5 Distribution stats (cross_asset_divergence_norm, IS window — from EDA SHA `254a5f2`)

| Symbol | n_valid | coverage% | mean | std | p01 | p99 |
|---|---:|---:|---:|---:|---:|---:|
| BCH | (full IS) | 100.0% | (per CSV) | (per CSV) | (per CSV) | (per CSV) |
| LDO | (full IS) | 100.0% | (per CSV) | (per CSV) | (per CSV) | (per CSV) |
| TRX | (full IS) | 100.0% | (per CSV) | (per CSV) | (per CSV) | (per CSV) |

(Distribution numbers in `analysis/iteration_v3-027/third_engineered_eda_distribution.csv`.) Coverage 100% — all 3 source primitives have full IS coverage. Output clipped to [−100, +100] in implementation to prevent infinity from near-zero vwap_dev denominators.

### 3.6 Rank-IC (cross_asset_divergence_norm, IS window — STRONGEST predictive signal of 4 candidates)

| Symbol | h=1 | h=3 | h=7 | max |rank-IC| |
|---|---:|---:|---:|---:|
| BCH | −0.026 | −0.016 | −0.034 | 0.034 |
| LDO | −0.039 | −0.074 | **−0.109** | **0.109** (STRONGEST in EDA) |
| TRX | +0.016 | +0.009 | −0.001 | 0.016 (bare; below 0.02 floor) |

LDO at h=7 has the strongest predictive signal across all 4 candidates × 3 symbols × 3 horizons (12 cells total). Direction is REVERSAL (negative rank-IC means high cross-asset divergence at low vwap-dev predicts negative forward returns — divergence over-extension reverts). BCH has weak reversal signal; TRX is near-zero (bare passes floor on h=1 only). The signal is LDO-driven — multi-seed CONFIRMATION will reveal whether LDO-driven importance is robust or single-seed lottery.

**Notable**: rank-IC at h=1 is small for all 3 — the signal is in the multi-bar predictive horizon, consistent with a 7-day-versus-14-day cross-asset divergence feature predicting forward 7-bar returns.

---

## Section 4 — Falsifiers (PRE-REGISTERED at SHA `254a5f2` + this brief — cannot be renegotiated)

### 4.1 Falsifier 1: PATH C trigger (NEGATIVE)

**Triggered if**: IS Sharpe < +0.30 (the iter-v3/026 collapse threshold; equivalent to IS Δ < −0.58 vs iter-v3/025 reference +0.8788) OR IS Sharpe Δ < −0.40 vs iter-v3/025 reference (i.e., observed IS < +0.48) OR OOS Sharpe Δ < −0.40 vs iter-v3/025 reference (i.e., observed OOS < +0.82).

**Verdict if triggered**: EXPLORATION-NEGATIVE (clean) — disambiguation hypothesis FAILS: destabilization is NOT vol_adj_autocorr-specific; engineered stacking is structurally fragile at single-seed even with 1 new feature. Mechanism: regime_momentum_signed_5d already captured the available regime/momentum signal; cross_asset_divergence_norm shares partial variance with regime_momentum (max |IC|_rm 0.46 LDO) and may cannibalize without contributing distinct signal. Engineered-features pivot is NARROW-PRODUCTIVE: only specific compositions work (regime_momentum at the 14-feature stack at single-seed n_trials=35), not a generally productive category.

### 4.2 Falsifier 2: Saturation falsifier

**Triggered if**: IS trades > 215 OR IS trades < 130.

**Verdict if triggered**: catalog row notes "saturation falsifier FIRES" qualifier; the axis behavioral effect is anomalous (trade count outside predicted band). Distinct from PATH C; can co-fire with any PATH.

### 4.3 Falsifier 3: PATH B trigger (PROMISING-INERT-replacement)

**Triggered if**: feature importance rank 14-15/15 across 3 of 4 cuts (BCH portfolio + LDO + Portfolio at minimum). Same relaxation as iter-v3/026 (3 of 4 vs strict 14/14 across all 4) to accommodate single-symbol partial-success patterns observed in iter-v3/024 (TRX rank 9/14 was the only departure).

**Verdict if triggered**: EXPLORATION-PROMISING-INERT-replacement — cross_asset_divergence_norm did not contribute; the iter-v3/025 result is narrow (only regime_momentum mechanism worked at this single-feature scale). Engineered-features pivot validated for ONE specific composition but NOT a general productive category. Pivot remains LIMITED-priority for iter-v3/028; alternative candidate ranking ret_kurt_to_skew_ratio (composite leaderboard winner) OR hurst_drift_50_200.

### 4.4 Falsifier 4: PATH A trigger (PROMISING — disambiguation validates)

**Triggered if**: feature importance rank ≤10 for ≥1 symbol AND IS Sharpe ≥ +0.30 (NOT a collapse) AND IS Sharpe Δ ≥ −0.40 vs iter-v3/025 reference. Importance value ≥30 required as well (informational threshold; flags genuine model usage vs cosmetic non-zero importance). OOS Sharpe Δ ≥ −0.40 vs iter-v3/025 reference (i.e., observed OOS ≥ +0.82).

**Verdict if triggered**: EXPLORATION-PROMISING — **DIFFERENT engineered feature ALONE works (signal exists; structurally orthogonal mechanism contributes additional value despite partial source-variance overlap)**. STRONG evidence the engineered-features pivot is consistently productive at single-seed when ONE feature is tested at a time — 2 of 2 PROMISING engineered features when tested alone (iter-v3/025 + iter-v3/027). The iter-v3/026 destabilization was either vol_adj_autocorr-specific OR a stacking-budget artifact at single-seed; engineered features can be tested SEQUENTIALLY (one at a time) in EXPLORATION but not simultaneously. **Eligibility for CONFIRMATION-bundle inclusion at iter-v3/029** (single-seed lottery suspect rule per `feedback_v3_single_seed_frozen_baseline.md`; multi-seed validation is the binding test). The iter-v3/029 CONFIRMATION may include cross_asset_divergence_norm AND/OR test the stacking question with proper multi-seed budget (5 inner × 2 outer × 35 trials = 350 fits).

### 4.5 Falsifier 5: PATH D trigger (PROMISING-MECHANICAL)

**Triggered if**: trade roster bit-identical to iter-v3/025 baseline (or strict subset thereof). Mechanism: feature is genuinely INERT but happens to shift profit accounting; not new edge.

**Verdict if triggered**: EXPLORATION-PROMISING-MECHANICAL — non-compoundable across iterations; treat as iter-v3/013 PROMISING-MECHANICAL precedent (FALSIFIED at multi-seed CONFIRMATION).

### 4.6 PATH classification cannot be renegotiated post-hoc

If the engineering report observed metrics fall in a borderline zone (e.g., IS = +0.32 just above the +0.30 collapse threshold; OOS = +0.78 just below the +0.82 PATH A floor), the verdict is still bound by the strict §4.4 criteria. The QR must NOT relax thresholds based on observed outcome direction.

---

## Section 5 — Predicted Bands (and predicted-vs-observed schedule)

| Metric | Lower bound | Upper bound | Median | iter-v3/025 reference | iter-v3/026 precedent | iter-v3/018 anchor |
|---|---:|---:|---:|---:|---:|---:|
| IS monthly Sharpe | +0.50 | +0.95 | +0.75 | +0.8788 | +0.0493 (collapse) | +0.3788 |
| OOS monthly Sharpe | +0.60 | +1.30 | +1.00 | +1.2244 | +1.4501 (suspect) | +0.3869 |
| OOS/IS Sharpe ratio | 1.10 | 1.60 | 1.35 | 1.39 | 29.4 (absurd) | 1.02 |
| IS n_trades | 175 | 215 | 195 | 194 | 196 | 172 |
| OOS n_trades | 80 | 110 | 95 | 95 | 79 | 90.5 |
| IS MaxDD | 20% | 35% | 28% | 27.49% | 51.37% (worst in v3) | 21.86% |
| OOS MaxDD | 20% | 32% | 26% | 21.35% | 19.47% | 27.74% |
| Total OOS PnL | +15% | +40% | +28% | +32.56% | similar magnitude | ~+7% |
| feature importance rank cross_asset_divergence_norm (best of 4 cuts) | 7 | 13 | 10 | n/a | n/a | n/a |
| feature importance value cross_asset_divergence_norm (best symbol) | 50 | 200 | 125 | n/a | n/a | n/a |
| feature importance regime_momentum_signed_5d (best of 4 cuts) | 7 | 12 | 9 | rank ~8-9 LDO; 51% top portfolio | rank 13/15 imp 300 (preserved) | n/a |

**Predicted IS NOT to collapse to <0.30** — this is the BINDING falsifier threshold. iter-v3/026 was 0.05; iter-v3/027 must clear +0.30 to pass disambiguation.

The predicted bands center on **maintaining most of the iter-v3/025 single-seed reference** rather than adding another large lift. The single-feature replacement (NOT stack) is hypothesized to preserve regime_momentum's signal while contributing the relative-strength mechanism. A modest +0.10-0.20 OOS lift would be a strong outcome; flat OOS would still be PATH A if rank/importance criteria fire and IS clears +0.30.

---

## Section 6 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`, every merge-candidate iteration must include this section. iter-v3/027 is EXPLORATION (not merge-candidate) but the section is mandatory for all axis-changes per Phase 5.5 gate.

### 6.1 Risk model: signal cannibalization + replacement-overfit

The primary risks are:
1. **SIGNAL CANNIBALIZATION** (per `feedback_v3_inert_features_at_higher_budget.md` analogue): cross_asset_divergence_norm shares partial variance with regime_momentum_signed_5d through the common dependence on close-derived returns (max |IC|_rm 0.46 LDO). Optuna at n_trials=35 may shift hyperparameter trajectories away from regime_momentum's tree splits, REDUCING regime_momentum's importance from iter-v3/025's 51% portfolio share. This would manifest as PATH A on the new feature alone but PATH C on the joint (regime_momentum importance fallen below 30 across 1+ cuts).
2. **REPLACEMENT-OVERFIT** (NEW for iter-v3/027): replacing vol_adj_autocorr with cross_asset_divergence_norm at the 15-column slot at n_trials=35 is structurally similar to iter-v3/026 (1 new feature added at the 15-column position). If iter-v3/026's IS collapse mechanism was budget-related (15-column space at depth-3-5 too large for n_trials=35 alone), iter-v3/027 will exhibit the SAME mechanism — IS Sharpe will collapse below +0.30. This is the disambiguation hypothesis under direct test.
3. **CROSS-ASSET-FEATURE DEAD-PATH PRECEDENT**: iter-v3/024's btc_funding cross-asset feature was rank 14/14 INERT + OOS −1.20. Cross-asset features have a track record of failure in v3 at single-seed. Mitigation: cross_asset_divergence_norm uses sym_ret_7d (per-symbol, NOT cross-asset) AS THE NUMERATOR — only btc_ret_14d is cross-asset. This is structurally distinct from iter-v3/024's pure-cross-asset feature; the EDA's max |rank-IC| 0.109 (best among 4 candidates) supports the structural distinction.

### 6.2 Mitigation: risk gates UNCHANGED from iter-v3/025/026 baseline

- **R1** (consecutive-SL cooldown): unchanged (3 SL → 27 candle pause; per BASELINE_V3.md)
- **R2** (drawdown-triggered position scaling): unchanged
- **R3** (OOD Mahalanobis gate): unchanged (70th-percentile cutoff)
- **z-score OOD**: 2.0 unchanged
- **ATR multipliers**: 2.0/1.0 unchanged
- **BTC trend filter**: ±15% unchanged
- **ADX threshold**: 20 unchanged
- **Hurst regime**: unchanged
- **Low-vol filter**: unchanged
- **Hit-rate feedback**: disabled
- **Regime gate**: disabled (was iter-v3/022 axis)
- **Per-symbol cap**: disabled (was iter-v3/020 axis)

### 6.3 Mitigation: kill-switch criteria

Iteration is abandoned mid-flight if:
1. Wall-clock exceeds 2h cap (EXPLORATION budget).
2. Adversarial past-only test FAILS (look-ahead bias detected).
3. Track-isolation grep returns non-empty (v3 imports v1/v2 features).
4. V3_FEATURE_COLUMNS not exactly 15 columns at backtest run with cross_asset_divergence_norm PRESENT and vol_adj_autocorr ABSENT.
5. Feature parquet regeneration fails on any of 3 symbols (BCH/LDO/TRX).

### 6.4 Mitigation: simulated historical effect

Counterfactual estimation: replacing vol_adj_autocorr with cross_asset_divergence_norm at the 15-column slot is expected to:
- Shift IS trade count by ±20 vs iter-v3/026 reference 196 → band [176, 216]
- Shift IS Sharpe by **at least +0.25 vs iter-v3/026's collapse** (target ≥ +0.30 to clear PATH C threshold) → predicted band [+0.50, +0.95] median +0.75
- Shift OOS Sharpe by ±0.30 vs iter-v3/025 reference 1.2244 → band [+0.92, +1.52] (median ~+1.20 if PATH A; below +0.82 if PATH C)
- Shift regime_momentum_signed_5d importance by ±15pp vs iter-v3/025's 51% portfolio share (signal cannibalization risk; informational diagnostic)

The single-feature replacement mechanism is a direct test of iter-v3/026's destabilization root cause; predicted bands carry HIGH uncertainty (variance across PATH A vs PATH C is the largest in v3 EXPLORATION history; the 27× IS/OOS ratio at iter-v3/026 cannot be predicted ex-ante).

---

## Section 7 — Pre-Commit for iter-v3/028 (conditional on iter-v3/027 outcome)

Per Phase 5.5 + iter-v3/026 diary lessons:

- **If iter-v3/027 PATH A (PROMISING)**: iter-v3/028 axis = ALTERNATIVE engineered feature ALONE on top of regime_momentum (replacing cross_asset_divergence_norm; KEEP regime_momentum). Critic FINAL Rec to be determined post-iter-v3/027 outcome; prior candidate ranking favors `ret_kurt_to_skew_ratio` (composite 0.7322 leaderboard winner; max |IC|_rm 0.075 — strongest orthogonality among remaining). This builds a 3-PROMISING engineered-feature stack (3 of 3 single-feature additions clear PATH A) → near-conclusive evidence the pivot is consistently productive.
- **If iter-v3/027 PATH B (PROMISING-INERT-replacement)**: iter-v3/028 axis = different engineered feature with stronger orthogonal mechanism (composite leaderboard winner ret_kurt_to_skew_ratio at 0.7322; max |IC|_rm 0.075). KEEP regime_momentum; replace cross_asset_divergence_norm with ret_kurt_to_skew_ratio.
- **If iter-v3/027 PATH C (NEGATIVE)**: iter-v3/028 axis = drop the engineered-feature stacking attempt entirely; revert V3_FEATURE_COLUMNS 15 → 14 (KEEP regime_momentum_signed_5d only). Pivot to fundamental architectural exploration: e.g., explicit regime-conditional ensemble of two LightGBM models (one trained on Hurst > 0.5 subset, one on Hurst < 0.5 subset). Feature engineering pivot deemed NARROW-PRODUCTIVE: only specific compositions work, not a generally productive category. iter-v3/028 catalog impact: shifts to NEW model architecture axis (not Category 2 axis #4).
- **If iter-v3/027 PATH D (PROMISING-MECHANICAL)**: NO iter-v3/028 axis-pivot; the iteration is an accounting-cleanup variation; wait for explicit evidence to compound.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md` + `feedback_v3_engineered_features_dont_stack.md`.

---

## Section 8 — Out-of-Scope (Cannot enter iter-v3/027 setup)

- ANY change to the 3-symbol BCH+LDO+TRX universe
- ANY change to the labeling parameters (ATR 2.0/1.0)
- ANY change to risk gates (z=2.0, ADX=20, BTC ±15%, regime gate disabled, per-symbol cap disabled)
- ANY change to model architecture (LightGBM remains; XGBoost rejected at iter-v3/016)
- ANY change to OOS_CUTOFF_DATE or training_months (sacred constants; immutable)
- ANY funding feature (PERMANENTLY-CLOSED across per-symbol + cross-asset variants)
- ADX as a feature column (rejected at EDA Stage 1; would be Category 1 axis, not the engineered-feature pivot)
- KEEPING vol_adj_autocorr in V3_FEATURE_COLUMNS (iter-v3/026 stacking falsified per `feedback_v3_engineered_features_dont_stack.md`; MUST be DROPPED at iter-v3/027 setup)
- DROPPING regime_momentum_signed_5d (iter-v3/025 PROMISING; KEPT — `feedback_v3_engineered_features_proven.md` mandate)
- ANY second new engineered feature in iter-v3/027 (single-axis discipline preserved; ONE engineered feature alone at single-seed per `feedback_v3_engineered_features_dont_stack.md`)

---

## Section 9 — Reproducibility Stamp (final pre-flight)

- **Brief SHA**: this commit (will be assigned at commit time)
- **EDA SHA**: `254a5f2`
- **Anchor (formal)**: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS
- **Reference (single-seed parent)**: iter-v3/025 +0.8788 IS / +1.2244 OOS (single-seed)
- **Precedent (iter-v3/026 NEGATIVE-SUSPICIOUS-OOS)**: +0.0493 IS / +1.4501 OOS (stacked vol_adj_autocorr; FALSIFIED)
- **n_trials default**: 35 (PRELIMINARY-VALIDATED through 7 prior EXPLORATIONs: iter-v3/020/021/022/023/024/025/026)
- **Parent branch SHA**: `1b60947` (iter-v3/026 diary commit on iteration-v3/026)
- **Parent baseline architecture**: 14 V3_FEATURE_COLUMNS_TOP_N (drop-MKR + ATR 2.0/1.0 + z=2.0 + BTC ±15% + ADX=20 + Hurst gate + regime_momentum_signed_5d) — vol_adj_autocorr DROPPED at iter-v3/027
- **Library stack pinned in BASELINE_V3.md**: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new dependencies.

---

## Section 10 — Hand-Off to Engineer (Phase 6)

Engineer must:
1. Read this brief + EDA at SHA `254a5f2` + iter-v3/026 diary at SHA `1b60947`.
2. Verify Phase 5.5 gate (separate file `phase5p5_gate.md` once Phase 5.5 completes).
3. Implement `compute_cross_asset_divergence_norm` in `engineered_v3.py` per Section 2.2 spec (~10 lines).
4. Update `add_engineered_v3_features` to dispatch BOTH compute functions: regime_momentum_signed_5d FIRST, then cross_asset_divergence_norm. REMOVE compute_vol_adj_autocorr from dispatch (function may be retained as dead code at zero revert cost).
5. DROP `vol_adj_autocorr` from V3_FEATURE_COLUMNS_TOP_N (revert 15 → 14 transitional state).
6. ADD `cross_asset_divergence_norm` to V3_FEATURE_COLUMNS_TOP_N (14 → 15 with new feature).
7. KEEP `regime_momentum_signed_5d` in V3_FEATURE_COLUMNS_TOP_N (do NOT revert).
8. Update `_verify_feature_columns` assertion to expect 15 columns including BOTH `regime_momentum_signed_5d` AND `cross_asset_divergence_norm`, AND assert `vol_adj_autocorr` ABSENT.
9. Extend adversarial past-only test `tests/features_v3/test_engineered_v3.py` with 4 new tests (per §2.5).
10. Run `uv run pytest tests/features_v3/` — must PASS.
11. Run `uv run ruff check . && uv run ruff format .` — must PASS.
12. Regenerate feature parquets for BCH+LDO+TRX with new `engineered_v3` group output (cross_asset_divergence_norm).
13. Set `ITERATION_LABEL = "v3-027"`.
14. Run backtest in EXPLORATION mode: `uv run crypto-trade backtest-v3 --exploration --seeds 1 --n-trials 35`.
15. Wait for backtest completion (predicted 8-15 min).
16. Write engineering report at `briefs-v3/iteration_v3-027/engineering_report.md`.
17. Hand off to Critic (Phase 7.5) for review.

Cannot be renegotiated post-hoc per `feedback_v3_engineered_feature_pivot.md` + `feedback_v3_engineered_features_proven.md` + `feedback_v3_engineered_features_dont_stack.md`.

---

## Appendix A — EDA Composite Score Detail (iter-v3/027 weights — mirror iter-v3/026)

Composite score = 0.10 × orthogonality_to_14_features (informational)
                + 0.20 × orthogonality_to_regime_momentum
                + 0.30 × rankIC magnitude
                + 0.20 × stability (coverage × ADF)
                + 0.10 × interpretability_prior
                + 0.10 × (1 − implementation_cost_prior)

| Candidate | Ortho-14 | Ortho-RM | RankIC | Stability | Interp | Impl | Composite |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ret_kurt_to_skew_ratio` | 0.0 | 0.85 | 0.77 | 1.0 | 0.4 | 0.1 | **0.7322** |
| `hurst_drift_50_200` | 0.0 | 0.85 | 0.64 | 1.0 | 0.8 | 0.5 | 0.6940 |
| **`cross_asset_divergence_norm`** | 0.0 | **0.07** | **1.0** | 1.0 | 0.7 | 0.2 | **0.6643** |
| `fracdiff_d05_close` | 0.0 | 0.0 | 0.88 | 0.5 | 0.7 | 0.4 | 0.4954 |

The leaderboard ranks ret_kurt_to_skew_ratio first because of its higher orthogonality-to-regime_momentum (0.85 vs cross_asset_divergence_norm's 0.07) — but the orthogonality criterion is informational only. cross_asset_divergence_norm has the **highest rank-IC magnitude (1.0 normalized; observed 0.109 LDO h7) — STRONGEST predictive signal among 4 candidates**. However:

1. **Pre-commit binds to cross_asset_divergence_norm** per Critic FINAL Rec + user directive 2026-05-08 — single-axis discipline cannot be renegotiated post-hoc.
2. **cross_asset_divergence_norm has DRAMATICALLY HIGHER rank-IC than ret_kurt_to_skew_ratio** (0.109 LDO h7 vs 0.077 LDO h7). Predictive evidence beats composite ranking when the composite weights orthogonality (which is partially shared by construction for engineered features).
3. **cross_asset_divergence_norm's mechanism (relative-strength normalized) is structurally distinct** from regime_momentum's (regime-conditional momentum) AND from vol_adj_autocorr's (per-unit-vol persistence). The Critic FINAL Rec + user mandate selected cross_asset_divergence_norm explicitly.
4. **ret_kurt_to_skew_ratio is the iter-v3/028 fallback** if iter-v3/027 lands PATH B/C (per Section 7).

---

## Appendix B — Why this iteration disambiguates the iter-v3/026 destabilization mechanism

The v3 catalog has 26 prior iterations (iter-v3/001-026). The axis-category breakdown after iter-v3/026:

- Category 1 (off-the-shelf indicator additions): iter-v3/015 (microstructure), iter-v3/019/023/024 (funding × 3) — ALL INERT-class
- Category 1 (knob axes): iter-v3/009/010/011/012/014 — saturated per `feedback_v3_axis_saturation_predictor.md`
- Category 1 (universe + risk primitives): iter-v3/020/021/022 — CLOSED-mechanism / CLOSED-symbols-cycle / PARTIALLY-EFFECTIVE
- Category 1 (model architecture / labeling architecture): iter-v3/016 (XGBoost) / iter-v3/017 (meta-labeling) — both NEGATIVE
- CONFIRMATION: iter-v3/018 — BOOTSTRAP exception
- Feature pruning: iter-v3/007/008/009 (top-14 → top-13)
- **Category 2 (composed/interaction features) ALONE**: iter-v3/025 (regime_momentum_signed_5d) — **PROMISING (clean)**
- **Category 2 (composed/interaction features) STACKED**: iter-v3/026 (regime_momentum + vol_adj_autocorr) — **NEGATIVE-SUSPICIOUS-OOS**

**iter-v3/027 is the THIRD Category 2 axis in v3 catalog history AND the SECOND single-feature engineered axis.** The disambiguation chain:

- iter-v3/025 (alone): ONE engineered feature works at single-seed → necessary but not sufficient evidence for stacking
- iter-v3/026 (stacked): TWO engineered features at single-seed produced IS collapse → STACKING FALSIFIED at single-seed
- **iter-v3/027 (alone, replacement): SECOND single-feature engineered feature → tests whether engineered features can be REPLACED at single-feature scale (not stacked)**

If iter-v3/027 lands PATH A:
- 2 of 2 engineered features PROMISING at single-seed when tested ALONE (vs 4 of 4 INERT for off-the-shelf NEW features)
- iter-v3/026 destabilization was vol_adj_autocorr-specific OR a stacking-budget artifact at single-seed
- Engineered features can be tested SEQUENTIALLY (one alone at a time) at single-seed; stacking is deferred to multi-seed CONFIRMATION
- iter-v3/028 = third single-feature engineered candidate (ret_kurt_to_skew_ratio leaderboard winner) to build evidence

If iter-v3/027 lands PATH C:
- Engineered-features pivot is GENUINELY NARROW-PRODUCTIVE (only specific compositions like regime_momentum work; cross_asset_divergence_norm fails despite different mechanism)
- The destabilization is NOT vol_adj_autocorr-specific — adding ANY second engineered feature at single-seed n_trials=35 destabilizes IS regardless of which feature
- Pivot to fundamental architectural exploration at iter-v3/028 (regime-conditional ensemble); abandon multi-feature engineered approach until multi-seed CONFIRMATION

**Per user directive 2026-05-08 + Critic FINAL Recommendation of iter-v3/026**: this is the disambiguation experiment for the engineered-features pivot. Cannot be renegotiated post-hoc.

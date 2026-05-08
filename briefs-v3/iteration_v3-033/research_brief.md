# Iteration v3-033 — Research Brief

**Type**: EXPLORATION (cadence #5 of 10 in post-iter-v3/028 cycle; **STRUCTURAL axis (Category 5 — UNIVERSE expansion)** — ADD a 5th symbol with per-symbol-feature-signature alignment)
**Track**: v3 (rigor arm) — thirty-third iteration
**Branch**: `iteration-v3/033` (off `iter-v3/032` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # default per feedback_v3_exploration_n_trials_35
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–032 briefs / engineering reports / Critic FINALs / diaries; iter-v3/033 EDA artifact (committed BEFORE this brief at SHA `06d4ba9` — per_symbol_5th_candidate_eda). The EDA reads ONLY pre-OOS-cutoff IS-window kline data + iter-v3/032 IS-only `model_importance_last_month_<SYM>.csv` files for ALL 4 incumbents (BCH+LDO+TRX+ALGO). OOS-window data is reported informationally only and does NOT enter the candidate scoring or recommendation logic.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #5 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: ADD 5th symbol — V3_MODELS expands 4 → 5 symbols
                       (BCH+LDO+TRX+ALGO incumbents) + (VETUSDT addition)
                       per per_symbol_feature_signature criterion
Cadence: 5 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 5 (NEW universe — denominator expansion; SECOND application
                  of per-symbol-feature-signature methodology after iter-v3/029
                  ALGO success at +20.87 OOS)
ANCHOR: iter-v3/032 single-seed (IS +0.2360 / OOS +1.9338)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a feature-add
variation. NOT a labeling change beyond carry-forward of LDO ATR (1.5, 0.75).
NOT a model architecture change. NOT a risk-primitive variation.
This iteration NEVER updates BASELINE_V3.md (single-seed --exploration mode).
```

**Justification — STRUCTURAL universe-expansion axis, SECOND application of validated per-symbol-feature-signature methodology**:

iter-v3/032 outstanding aspirational MERGE-gate gaps (recorded against BASELINE_V3.md iter-v3/028 anchor +0.5101/+0.5053):
- Top-symbol concentration 45.10% (TRX) > 30% threshold → -15pp gap
- Bundle OOS trades 129 < 130 floor → -1
- IS aggregate Sharpe +0.24 < +1.0 absolute floor → -0.76 gap (single-seed-suspect; multi-seed truth-test at iter-v3/039 CONFIRMATION)

A 5th symbol mechanically addresses concentration (denominator expansion) AND bundle trade volume (additional symbol contributes 20-30 trades at single-seed). The per-symbol-feature-signature methodology is the corrected criterion validated at iter-v3/029 (ALGO contribution +20.87 OOS; methodology PROVEN vs iter-v3/021's failed raw-correlation HBAR+AVAX criterion).

**Why VETUSDT and not FIL or ATOM** (per `analysis/iteration_v3-033/candidate_targeted_ranking.csv`):

| Rank | Symbol | composite | alignment_score | NATR_21% | btc_coupling_std | gate1+2 |
|---:|---|---:|---:|---:|---:|:---:|
| 1 | **VETUSDT** | **0.6833** | **0.5176** | 3.97 | 0.0935 | PASS |
| 2 | FILUSDT | 0.6502 | 0.4619 | 4.15 | 0.0938 | PASS |
| 3 | ATOMUSDT | 0.5164 | 0.4867 | 3.54 | 0.0793 | PASS |

VET wins on composite by +0.033 vs FIL and +0.167 vs ATOM. VET's edge is dominated by the highest alignment_score (0.5176 — driven by `range_realized_vol_50` alignment 0.7107, the highest across candidates and aligned with the dominant SHARED-top feature). FIL has higher liquidity ($220M/day vs VET $38M/day) but materially weaker feature-signature alignment. ATOM has the lowest btc_coupling_std (0.0793), pulling its composite down.

**Note on iter-v3/029 candidate ordering swap**: at iter-v3/029, the methodology used 4 SHARED-top features against 3 incumbents — VET led on alignment_score (0.4771) but ALGO led on composite (0.6517 vs VET 0.5865) due to ALGO's btc_coupling advantage. At iter-v3/033 with 4 incumbents (incl. ALGO post-success), the SHARED-top set has shrunk to 3 features (range_realized_vol_50, ret_kurt_50, ret_skew_200 — natural dilution as universe widens) and VET now leads on BOTH alignment AND composite. The ordering swap is consistent with the per-symbol-feature-signature methodology — it is data-driven by the current incumbent universe.

**Single-axis discipline**: ONE NEW symbol (VETUSDT); V3_MODELS 4 → 5; REQUIRED_GAP 88 → 110 = (21+1)×5. KEEP V3_FEATURE_COLUMNS=14 byte-identical (regime_momentum_signed_5d preserved). KEEP V3_ATR_MULTIPLIERS_PER_SYMBOL with LDO entry only — VET inherits default ATR (2.0, 1.0). KEEP 7-primitive risk gate stack byte-identical. NO labeling change for incumbents. NO ENSEMBLE_SIZE change. NO Optuna budget change.

After iter-v3/033 the catalog will have: 16 unique axis representations (15 prior + 1 new universe expansion 4→5).

---

## Section 1 — Hypothesis

Adding VETUSDT to V3_MODELS (universe 4 → 5 symbols; 7-primitive risk gate stack BYTE-IDENTICAL to iter-v3/032 anchor; V3_FEATURE_COLUMNS=14 BYTE-IDENTICAL including regime_momentum_signed_5d; V3_ATR_MULTIPLIERS_PER_SYMBOL preserved with LDO (1.5, 0.75) entry; new symbol uses default ATR (2.0, 1.0); per-symbol cap remains DISABLED) will **mechanically dilute single-symbol concentration without removing edge from any incumbent symbol**, because (a) the candidate was selected on per-symbol feature-signature alignment (the same corrected criterion that validated at iter-v3/029 with ALGO contribution +20.87 OOS), and (b) VET's alignment_score 0.5176 is the highest among candidates and is driven by range_realized_vol_50 alignment 0.7107 — the strongest SHARED-top feature across all 4 current incumbents. Predicted IS Sharpe band [+0.30, +0.70] median +0.50 (anchor +0.24; modest lift expected as 5th symbol adds productive contribution per iter-v3/029 precedent). Predicted OOS Sharpe band [+1.50, +2.10] median +1.80 (anchor +1.93; maintain or modest, single-seed iter-v3/032's high OOS reading is pre-multi-seed-validation; expansion either propagates or compresses).

**Mechanism explanation** (per-symbol-feature-signature criterion, second application): in the 4-symbol incumbent universe, LightGBM at n_trials=35 fits per-symbol heads using the 14-feature stack. For a NEW symbol to add productive signal, its features' time-series must capture the same regime/microstructure patterns as the incumbents'. Phase 1 finding identifies that 3 features are SHARED-top-7-across-all-4-incumbents: `range_realized_vol_50`, `ret_kurt_50`, `ret_skew_200`. The candidate's compatibility with these 3 features' driving factors is the load-bearing predictor. iter-v3/021's raw-return correlation captured price-level diversity but NOT signal-driver compatibility — HBAR+AVAX failed at -86% combined PnL. iter-v3/029's per-symbol-feature-signature alignment criterion was validated by ALGO's +20.87 OOS contribution. iter-v3/033 is the SECOND application of the validated methodology.

VET's per-symbol feature-signature alignment scores (mean abs Pearson of 3 SHARED-top features vs 4 incumbents): 0.5176 — the highest in the candidate pool. Driven by range_realized_vol_50 alignment 0.7107, which is the dominant SHARED-top feature (top-7 in BCH AND LDO AND TRX AND ALGO simultaneously). NATR_21 3.97% is in band [3.0%, 7.0%] (similar to BCH's ~3.5% and TRX's ~3.0%; below LDO's ~6.8%). btc_coupling_std 0.0935 is mid-band (similar to ATOM and FIL).

**Why VET universe expansion may NOT lift OOS** (3 PATH-C-suspect scenarios):

1. **PATH C-1: VET model underperforms in iter-v3/032 fitted regime.** Single-seed n_trials=35 may not surface a productive Optuna trajectory for VET (alignment_score 0.5176 is moderate-strong; iter-v3/029 ALGO at 0.4642 alignment did surface productive fit, but VET alignment is higher — bear-prior is moderate).
2. **PATH C-2: 5-symbol concentration regression to ALGO/TRX.** Despite VET's positive alignment, the LightGBM model may surface the same regime classifiers (BTC-trend-aligned momentum bursts) for VET as for incumbents, leading to crowded losses in regime-cells that single-seed fits poorly.
3. **PATH C-3: VET's OOS contribution near-zero (NEGATIVE-no-effect).** VET trades but adds no signal — concentration arithmetic doesn't fire because numerator unchanged at zero contribution. Falsifier 5 fires.

**Bear-prior baseline**: iter-v3/021's HBAR+AVAX failure is the structural prior on universe expansion. The per-symbol-feature-signature criterion is the corrected mechanism, validated once at iter-v3/029. A second positive application strengthens the methodology evidence; a single negative breaks the streak but does not falsify the criterion (single-seed lottery noise).

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Phase 1+3 EDA**: `analysis/iteration_v3-033/per_symbol_5th_candidate_eda.py` (committed at SHA `06d4ba9` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only):
- `reports-v3/iteration_v3-032/in_sample/model_importance_last_month_{BCH,LDO,TRX,ALGO,portfolio}.csv` (Phase 1 — re-extract per-symbol importance from iter-v3/032 4-symbol baseline)
- `reports-v3/iteration_v3-032/{in_sample,out_of_sample}/per_symbol.csv` (sanity check, NOT used for selection)
- `data/{BTC,BCH,LDO,TRX,ALGO,FIL,VET,ATOM}USDT/8h.csv` IS-window 2023-04-01 → 2025-03-24 (Phase 3)

**Outputs** (committed alongside the script):
- `per_symbol_feature_signature.csv` (long format), `feature_dispersion_ranking.csv`, `symbol_specific_features.csv`, `symbol_specific_top_bottom.csv` (Phase 1)
- `candidate_features_alignment.csv`, `candidate_targeted_ranking.csv` (Phase 3)
- `synthesis.md` (combined narrative)

### 2.1 Phase 1 finding — per-symbol feature dispersion across 4 incumbents

For each of the 14 V3 features, rank within each symbol's IS-only `model_importance_last_month` CSV (1=highest), then compute rank_range = max-min across BCH/LDO/TRX/ALGO. Sorted by rank_range descending:

| Feature | rank_BCH | rank_LDO | rank_TRX | rank_ALGO | rank_range | classification |
|---|---:|---:|---:|---:|---:|---|
| vwap_dev_20 | 12 | 2 | 4 | 5 | 10 | HIGH-DISP-SYMBOL-SPECIFIC |
| hurst_100 | 9 | 10 | 3 | 12 | 9 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_skew_50 | 8 | 11 | 7 | 2 | 9 | HIGH-DISP-SYMBOL-SPECIFIC |
| sym_vs_btc_ret_7d | 5 | 7 | 12 | 13 | 8 | HIGH-DISP-SYMBOL-SPECIFIC |
| max_dd_window_50 | 4 | 9 | 9 | 1 | 8 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_kurt_200 | 7 | 4 | 11 | 7 | 7 | HIGH-DISP-SYMBOL-SPECIFIC |
| ema_spread_atr_20 | 2 | 6 | 2 | 8 | 6 | MID-DISP |
| ret_autocorr_lag1_50 | 10 | 12 | 8 | 9 | 4 | MID-DISP |
| range_realized_vol_50 | 3 | 5 | 1 | 3 | 4 | MID-DISP |
| ret_kurt_50 | 1 | 1 | 5 | 4 | 4 | MID-DISP |
| hurst_diff_100_50 | 14 | 13 | 13 | 11 | 3 | LOW-DISP-SHARED |
| ret_skew_200 | 6 | 3 | 6 | 6 | 3 | LOW-DISP-SHARED |
| btc_ret_14d | 11 | 8 | 10 | 10 | 3 | LOW-DISP-SHARED |
| **regime_momentum_signed_5d** | **13** | **14** | **14** | **14** | **1** | **LOW-DISP-SHARED** |

**Findings**:
- 6 HIGH-DISP-SYMBOL-SPECIFIC features (rank_range ≥ 7): vwap_dev_20, hurst_100, ret_skew_50, sym_vs_btc_ret_7d, max_dd_window_50, ret_kurt_200. These are symbol-regime-specific.
- 4 MID-DISP features: ema_spread_atr_20, ret_autocorr_lag1_50, range_realized_vol_50, ret_kurt_50.
- 4 LOW-DISP-SHARED features: hurst_diff_100_50, ret_skew_200, btc_ret_14d, regime_momentum_signed_5d. Universal-but-moderately-ranked predictors.
- regime_momentum_signed_5d ranks bottom-1 to bottom-2 across all 4 symbols (uniform; LOW-DISP-SHARED). It is **uniformly the lowest-importance feature in the LightGBM gain accounting yet contributes +0.13 IS / +0.12 OOS Sharpe** at iter-v3/028 — this is the meta-feature paradox and a known property of regime-coupled signals (low gain in tree splits but reliable directional bias).

**SHARED top-7 features (top-7 in ALL 4 incumbents simultaneously)**: `range_realized_vol_50, ret_kurt_50, ret_skew_200`. **3 features** (vs 4 in iter-v3/029's 3-symbol incumbent universe). The natural dilution as the universe widens is expected — adding more symbols increases the AND constraint count.

### 2.2 Phase 3 candidate ranking under per-symbol-feature-signature criterion

For each candidate (FIL, VET, ATOM), compute alignment_score = mean abs Pearson of 3 SHARED-top features' time-series vs each of 4 incumbents (mean abs across 4 incumbents per feature, mean across 3 features). Composite = 0.65·alignment_score + 0.20·natr_band_OK + 0.15·btc_coupling_z. All 3 candidates PASS Gate 1 (data quality) and Gate 2 (liquidity); ranking driven by Gate 3.

| Rank | Symbol | composite | alignment_score | NATR_21% | NATR_OK | btc_coupling_std | IS qvol mean | gates_pass |
|---:|---|---:|---:|---:|:---:|---:|---:|:---:|
| 1 | **VETUSDT** | **0.6833** | **0.5176** | 3.97 | PASS | 0.0935 | $38.4M | PASS |
| 2 | FILUSDT | 0.6502 | 0.4619 | 4.15 | PASS | 0.0938 | $220.7M | PASS |
| 3 | ATOMUSDT | 0.5164 | 0.4867 | 3.54 | PASS | 0.0793 | $105.8M | PASS |

**VETUSDT selected as TOP candidate**. Per-feature alignment detail (all candidates):

| Symbol | align_range_realized_vol_50 | align_ret_kurt_50 | align_ret_skew_200 |
|---|---:|---:|---:|
| **VETUSDT** | **0.7107** | 0.4434 | 0.3988 |
| FILUSDT | 0.6557 | 0.4042 | 0.3258 |
| ATOMUSDT | 0.6631 | 0.4652 | 0.3319 |

VET dominates the dominant alignment dimension (`range_realized_vol_50` 0.7107 vs FIL 0.6557 / ATOM 0.6631). The dominance on this feature anchors VET's composite advantage.

### 2.3 VETUSDT decision tile

| Property | Value | Threshold | Verdict |
|---|---:|---:|---|
| Composite score | 0.6833 | rank-1 of 3 candidates | TOP |
| alignment_score (3 SHARED-top features) | 0.5176 | rank-1 (vs FIL 0.4619, ATOM 0.4867) | TOP |
| range_realized_vol_50 alignment | 0.7107 | rank-1 across candidates | TOP |
| raw_corr_mean_abs vs 4 incumbents | 0.6058 | (informational) | mid-band |
| NATR_21 IS | 3.97% | band [3.0%, 7.0%] | PASS |
| btc_coupling_std | 0.0935 | mid-band | OK |
| IS coverage | 100.0% | ≥99% | PASS |
| Pre-IS history | 37.5 months | ≥18mo | PASS |
| Avg daily quote volume IS | $38.4M | >$20M | PASS |
| P10 daily qvol | $9.7M | >$5M | PASS |
| Gate 1 | PASS | — | PASS |
| Gate 2 | PASS | — | PASS |
| Gate 3 | PASS | — | PASS |

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted IS bundle-level trade volume change** (single-seed --exploration; iter-v3/032 single-seed ENSEMBLE_SIZE=1, n_trials=35, colsample=1.0):
- iter-v3/032 single-seed IS bundle trades = 256 (per `comparison.csv`: 94 BCH + 85 TRX + 14 LDO + 63 ALGO).
- Per iter-v3/029 precedent (4-symbol single-seed produced 257 IS trades; +75 vs iter-v3/028 anchor 182 multi-seed cumulative or ~91 per-seed): the new symbol contributes ~30-50 IS trades.
- Predicted IS bundle trades band: **[290, 350]** (+13% to +37% over single-seed anchor 256). Center ~320.

**Saturation falsifier (per ±25% rule)**: if observed IS trades < 240 (lower bound 256 × 0.94), axis SATURATED at saturation point (Falsifier "axis-saturated"). If observed > 380 (upper bound 256 × 1.49), axis OVERSHOOT — flag for risk-amplification review.

**Falsifier 4 — Importance rank**: VET's `range_realized_vol_50` per-cell importance must be ≥ rank 7/14 in at least one cell (model uses the dominant SHARED-top feature on the new symbol AT LEAST as moderate-ranked as the SHARED-top property implies). If VET ranks range_realized_vol_50 at 12-14 (model didn't learn it on VET), Falsifier 4 FIRES — diagnose as PROMISING-INERT.

**Falsifier 5 — Concentration shift**: TRX OOS concentration must drop from 45.10% (iter-v3/032 anchor) below 40%. If TRX OOS concentration stays ≥ 42%, the universe expansion did NOT propagate meaningfully to the concentration metric.

**Falsifier 6 — New-symbol drag**: VET OOS weighted_pnl must NOT be < -10%. If VET produces large negative drag (similar to HBAR -36.5% / AVAX -49.2% at iter-v3/021), Falsifier 6 FIRES — PATH B (NEGATIVE-DILUTION; closes VET axis; closes 5th-symbol-add axis at this baseline; methodology survives but generalization questioned).

### 2.5 Counterfactual: 5-symbol mechanical concentration dilution

iter-v3/032 single-seed OOS bundle metrics (per `reports-v3/iteration_v3-032/out_of_sample/per_symbol.csv`):

| Symbol | OOS net_pnl% (seed=42) | OOS Concentration % |
|---|---:|---:|
| TRX | +29.24 | 45.10% |
| ALGO | +20.87 | 32.19% |
| BCH | +10.75 | 16.58% |
| LDO | +3.98 | 6.13% |
| **Total (4-sym)** | **+64.84** | (numerator) |

Under counterfactual ADD VET at OOS PnL ~ 0% (lottery-symmetric prior):

| Symbol | OOS PnL | OOS Conc % (5-sym counterfactual zero VET) |
|---|---:|---:|
| TRX | +29.24 | 45.10% (UNCHANGED — denominator unchanged) |
| ALGO | +20.87 | 32.19% |
| BCH | +10.75 | 16.58% |
| LDO | +3.98 | 6.13% |
| VET | 0.00 | 0.00% |

**Mechanical dilution at zero-contribution VET does not alter percentages**. For the dilution mechanism to fire, VET must contribute non-trivial positive PnL. Under VET contribution +5%: TRX concentration drops from 45.10% to 29.24/(64.84+5) = 41.87%; under +10%: drops to 39.07%. The mechanical dilution requires **positive PnL contribution from VET** — exactly the iter-v3/029 ALGO precedent (ALGO contributed +20.87, dropping TRX from 75-77% to 50.6%).

This is the same lesson as iter-v3/021 / iter-v3/029: universe expansion's concentration relief requires the new symbol to contribute positive PnL, NOT just to be added. The brief's hypothesis is therefore conditional on the per-symbol-feature-signature criterion correctly predicting VET's compatibility — VET's higher alignment_score 0.5176 (vs ALGO's 0.4642 at iter-v3/029) is the strongest a-priori evidence available.

---

## Section 3 — Sub-fixes (7-item) with Verifier Commands

| # | Sub-fix | Description | Verifier |
|---|---|---|---|
| 1 | **V3_MODELS expansion 4 → 5** | Add `("E (VETUSDT)", "VETUSDT")` to V3_MODELS in `run_baseline_v3.py`. Letter "E" follows the convention (A=BCH, C=LDO, D=TRX, E=VET, F=ALGO; B reserved for v1 historical). | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==5; assert any('VETUSDT'==sym for _,sym in m.V3_MODELS), m.V3_MODELS"` exits 0 |
| 2 | **REQUIRED_GAP update 88 → 110** | Update `src/crypto_trade/strategies/ml/validation_v3.py` `REQUIRED_GAP: int = (21 + 1) * 5  # 110`. Update docstrings to reflect 5-symbol universe. | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==110, REQUIRED_GAP"` exits 0 |
| 3 | **`_verify_label_leakage_gap()` message update** | Update message in `run_baseline_v3.py:_verify_label_leakage_gap()` to print `n_symbols=5` and 110 instead of 88. | `_verify_label_leakage_gap()` exits 0 with message reflecting `n_symbols=5` |
| 4 | **ITERATION_LABEL update v3-032 → v3-033** | Update `ITERATION_LABEL = "v3-033"` in `run_baseline_v3.py`. | `grep '^ITERATION_LABEL' run_baseline_v3.py | grep -q '"v3-033"'` |
| 5 | **Feature parquet regen for VET** | Run `uv run crypto-trade features --symbols VETUSDT --interval 8h --track v3 --format parquet --workers 4` to generate `data/features_v3/VETUSDT_8h_features.parquet`. | `ls data/features_v3/VETUSDT_8h_features.parquet` exists |
| 6 | **V3_FEATURE_COLUMNS BYTE-IDENTICAL UNCHANGED** | KEEP V3_FEATURE_COLUMNS_TOP_N at 14 cols (iter-v3/032 byte-identical including regime_momentum_signed_5d). NO new feature, NO removal. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"` exits 0 |
| 7 | **V3_ATR_MULTIPLIERS_PER_SYMBOL UNCHANGED** | KEEP `V3_ATR_MULTIPLIERS_PER_SYMBOL = {"LDOUSDT": (1.5, 0.75)}` byte-identical. VET inherits default (2.0, 1.0) via `V3_ATR_MULTIPLIERS.get(symbol, DEFAULT_ATR_MULTIPLIERS)`. | `python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {'LDOUSDT': (1.5, 0.75)}"` exits 0 |

**Reconciliation table** (Engineer Phase 5.5 verifier — 7 commands):

```
1. uv run python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==5; assert any(s=='VETUSDT' for _,s in m.V3_MODELS), m.V3_MODELS"
2. uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==110, REQUIRED_GAP"
3. uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"
4. uv run python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {'LDOUSDT': (1.5, 0.75)}, V3_ATR_MULTIPLIERS_PER_SYMBOL"
5. ls data/features_v3/VETUSDT_8h_features.parquet
6. grep '^ITERATION_LABEL' run_baseline_v3.py | grep -q '"v3-033"'
7. uv run pytest tests/strategies/ml/test_validation_v3.py -v  # adversarial label-leakage gap test against new gap=110
```

---

## Section 4 — Predicted Bands & Catalog Framings

**Anchor (iter-v3/032 single-seed)**:
- IS Sharpe = +0.2360 (single-seed; flagged IS-collapse pattern at iter-v3/032)
- OOS Sharpe = +1.9338 (single-seed; highest in v3 catalog at single-seed; pre-multi-seed-validation)

**Single-seed iter-v3/033 expectation** (5th-symbol axis; iter-v3/029 ALGO precedent: IS +0.7926 / OOS +1.7653 from anchor +0.5101 / +0.5053; +0.28 IS / +1.26 OOS lift):

| Band | IS Sharpe | OOS Sharpe | Interpretation |
|---|---:|---:|---|
| PATH A — PROMISING (clean) | [+0.50, +0.70] | [+1.50, +2.10] | VET contributes positive PnL; concentration dilutes; iter-v3/039 candidate |
| PATH B — NEGATIVE (DILUTION drag) | < +0.10 | < +1.30 | VET drags IS+OOS materially; closes VET axis |
| PATH C — INERT (concentration unchanged) | [+0.20, +0.40] | [+1.50, +2.00] | VET trades but adds no signal; concentration stays ≥42% |
| PATH C-2 — NEGATIVE-no-effect | ~+0.24 | ~+1.93 | VET not productively fitted (Falsifier 4 fires) |

**§4.4 catalog framing table** (5 rows):

| # | Verdict | Conditions | Catalog row tag |
|---|---|---|---|
| 1 | EXPLORATION-PROMISING (clean) | IS ≥ +0.50 AND OOS ≥ +1.50 AND VET weighted_pnl > 0 AND TRX OOS concentration < 40% | YES — STRONG candidate; iter-v3/039 CONFIRMATION-bundle ingredient (5-symbol expansion architectural decision; compoundable with regime_momentum_signed_5d + ALGO + LDO ATR) |
| 2 | EXPLORATION-NEGATIVE (DILUTION) | OOS Sharpe < +1.30 (Δ < -0.60 vs anchor) AND VET weighted_pnl < -10% AND non-bit-identical incumbent roster | NO — closes VET axis; 5th-symbol-add axis CLOSED at this baseline; methodology generalization questioned (single negative breaks streak but does not falsify) |
| 3 | EXPLORATION-PROMISING-INERT | Falsifier 4 fires (range_realized_vol_50 rank ≥ 12 on VET) AND OOS Sharpe in [+1.50, +2.00] | NO — VET model not productively fitted at single-seed; retest at multi-seed deferred |
| 4 | EXPLORATION-NEGATIVE-no-effect | Falsifier 5 fires (TRX OOS concentration ≥ 42%) AND IS ~ +0.24 AND OOS ~ +1.93 | NO — universe expansion didn't propagate; PATH C; pivot iter-v3/034 to non-universe axis |
| 5 | EXPLORATION-NEGATIVE-DILUTION (clean) — Falsifier 6 FIRES | VET OOS weighted_pnl < -10% AND non-bit-identical roster AND saturation falsifier within band | NO — replication of iter-v3/021 failure mode at 1-symbol scale; per-symbol-feature-signature methodology challenged but iter-v3/029 ALGO success retained as evidence |

---

## Section 5 — Risk Mitigation

### Cadence-discipline risks (4)

| Risk | Mitigation |
|---|---|
| iter-v3/033 EXPLORATION budget overrun | Hard 2h wall-clock cap. VET is a 5-symbol single-seed run. iter-v3/032 4-symbol ran 19 min; estimate 22-30 min for 5-symbol. Well within cap. |
| Cycle-cadence inflation | iter-v3/033 is FIFTH EXPLORATION of cycle (iter-v3/029, iter-v3/030, iter-v3/031, iter-v3/032 prior). CONFIRMATION at iter-v3/039. STRICT 10:1. |
| Catalog-row pre-commit cleanup | Section 11 pre-commits 4 dispositions. Diary commit closes catalog row regardless of outcome. |
| Single-axis discipline drift | ONE NEW symbol; V3_FEATURE_COLUMNS UNCHANGED; risk gates UNCHANGED; VET inherits default ATR (2.0, 1.0). Engineer Phase 6 rejection if any other knob is tuned. |

### Methodology-hygiene risks (4)

| Risk | Mitigation |
|---|---|
| OOS contamination | EDA reads only IS-window data + iter-v3/032 IS-only importance CSVs. Phase 7 is QR's first OOS view. |
| Look-ahead in VET features | Feature parquets regenerated via `crypto-trade features --track v3` which uses the same scale-invariant features as incumbents (no rolling-window leakage for VET that BCH/LDO/TRX/ALGO don't share). |
| Survivorship bias | VET listed 2021-09-29 with 37.5 months pre-IS history. No survivorship issue. |
| n_trials=35 single-seed lottery | EXPLORATION budget; multi-seed validation deferred to iter-v3/039 CONFIRMATION. Single-seed result is INFORMATIONAL not load-bearing for BASELINE_V3.md update. |

### Axis-specific risks (3)

| Risk | Mitigation |
|---|---|
| VET model collapse at single-seed n_trials=35 | Falsifier 4 fires if range_realized_vol_50 rank ≥ 12; classified PROMISING-INERT not catastrophic. iter-v3/034 may retest at multi-seed if enough other PROMISINGs accumulate. |
| Incumbent fits perturb on 5-symbol Optuna context | Per-symbol architecture isolates per-cell Optuna; incumbent cells should fit identically to iter-v3/032 conditions (each cell is independent). iter-v3/021 saw incumbent perturbation at 5-sym; iter-v3/029 4-sym was clean — 5-sym risk is moderate. |
| VET-driven concentration regression | Falsifier 5 + Falsifier 6 both fire if VET drags. iter-v3/034 reverts to 4-sym at first commit if iter-v3/033 PATH B. |

---

## Section 6 — 7-Primitive Risk Gate Stack — UNCHANGED

| Primitive | Threshold | Status |
|---|---|---|
| BTC trend kill | ±15% over 14d (42 bars 8h) | UNCHANGED from iter-v3/032 |
| Vol scaling | RiskV2Wrapper internal | UNCHANGED |
| ADX gate | 20.0 | UNCHANGED |
| Hurst regime | hurst_100 in [0.3, 0.7] band | UNCHANGED |
| Feature z-score OOD | |z| ≤ 2.0 across 35 v2-feature-set | UNCHANGED |
| Low-vol filter | NATR-percentile-based | UNCHANGED |
| Hit-rate feedback | DISABLED (per iter-v2/045) | UNCHANGED |
| Per-symbol cap | DISABLED (iter-v3/020 closed) | UNCHANGED |
| Regime-conditional kill switch | DISABLED outside iter-v3/022 | UNCHANGED |

VET inherits the 7-primitive stack byte-identical to incumbents.

---

## Section 7 — 8 Failure-Mode Predictions

Calibrated against iter-v3/007–032 prior EXPLORATIONs + iter-v3/029 ALGO precedent + iter-v3/033 EDA priors:

| # | Mode | Probability | Evidence |
|---|---|---:|---|
| P1 | OOS contamination via EDA | <5% | EDA explicitly IS-only-window (mechanical OOS_CUTOFF_MS partition) |
| P2 | Optuna budget overrun | <5% | EXPLORATION default n_trials=35; 5-sym single-seed estimated 22-30 min |
| P3 | Pre-commit non-compliance | <5% | 7 sub-fixes in §3 are atomic; reconciliation table covers all |
| P4 | PATH A — VET contributes positive PnL | 35-45% | EDA alignment_score 0.5176 is the highest in candidate pool; iter-v3/029 ALGO precedent at lower 0.4642 succeeded — moderately-strong bull prior |
| P5 | PATH B — VET drag (similar to iter-v3/021) | 20-30% | Bear prior — iter-v3/021 failed at low raw correlation; VET has moderate raw correlation 0.6058. The per-symbol-feature-signature criterion is fundamentally different, validated once at iter-v3/029. |
| P6 | PATH C — VET INERT (Falsifier 4) | 10-15% | Per-symbol arch should fit VET at single-seed n_trials=35; INERT requires range_realized_vol_50 to fail to propagate. |
| P7 | PATH C-2 — concentration unchanged | 10-15% | VET contributes ~0% PnL; Falsifier 5 fires; common scenario in iter-v3/015/019. |
| P8 | OOS-suspicious lottery (single-seed v3 pattern) | 15-25% | iter-v3/013/025/026/027/032 all showed single-seed OOS divergence; iter-v3/032 has high baseline prior at +1.93 OOS. |

**Combined PROMISING (P4) ≈ 35-45%; combined PATH C/INERT (P6+P7) ≈ 20-30%; combined PATH B/NEGATIVE-DILUTION (P5) ≈ 20-30%.** This is a moderate-to-high-prior EXPLORATION; the Phase 1 + Phase 3 EDA evidence + the iter-v3/029 ALGO success strengthens the prior over iter-v3/021's HBAR+AVAX experiment.

---

## Section 8 — 11 Pre-Registered EXPLORATION Criteria

EXPLORATION never updates BASELINE_V3.md. 11 criteria for catalog-row decision:

1. **OOS Sharpe ≥ +1.50** (anchor +1.93): catalog row records PROMISING (PATH A). Aspirational maintain-or-modest-lift.
2. **OOS Sharpe < +1.30** (anchor -0.60): Falsifier 1 fires — EXPLORATION-NEGATIVE if non-bit-identical roster (PATH B / DILUTION) or NEGATIVE-no-effect if axis didn't propagate.
3. **OOS Sharpe in [+1.30, +1.50]**: PROMISING-INERT (catalog INERT).
4. **n_trades ≥ 50 IS, ≥ 50 OOS bundle-level**: BUNDLE-LEVEL trade-rate floor. Predicted IS in [290, 350]; OOS predicted ~140-160 bundle-level (well above floor at single-seed EXPLORATION).
5. **PBO < 0.40 (per-cell mean)** AND `n_high_pbo_cells_99 ≤ 4`: methodology hygiene; iter-v3/032 PBO mean was 0.097. New VET cells may add new high-PBO cells (e.g., VET/2024-08 yen-carry).
6. **IC max abs < 0.70**: NO new feature; existing 14-feature IC matrix unchanged. VET's per-symbol IC matrix should be reported in engineering report for completeness.
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS for ALL 5 symbols**: 14 features unchanged; incumbent ADF inherits PASS from iter-v3/032; VET ADF must be re-run and reported. Expected PASS (features are scale-invariant).
8. **Reproducibility verifier**: SHAs stamped (Phase 1+3 EDA `06d4ba9`; brief commit; setup commit; Phase 5.5 gate; engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (waiver inherited from iter-v3/006-032).
10. **Symbol exclusion + feature isolation + track isolation**: `set({BCH, LDO, TRX, ALGO, VET}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; VET is NOT in V3_EXCLUDED_SYMBOLS list (BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/DOGE/NEAR/MKR). No new imports from features modules. Zero cross-track contamination.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS bundle trades in **[290, 350]** AND incumbent BCH+LDO+TRX+ALGO combined ≥ 220 (Falsifier 4: incumbent stability — iter-v3/032 single-seed was 256; -15% lower bound = 218) AND VET contributes ≥ 20 IS trades (Falsifier 5: new-symbol propagation) AND no VET OOS PnL drag < -10% (Falsifier 6: new-symbol drag). Critic uses ALL FOUR signals to disambiguate clean PATH A / PATH B / NULL-RESULT.

**Catalog-axis verdicts** map to §4.4 table.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/032** — no version updates:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0
scikit-learn = 1.8.0
pyarrow = 23.0.1
mlfinpy = 1.4.0
pypbo = 0.10.0
fracdiff = 0.10.0
statsmodels = 0.14.6
optuna = 4.8.0
scipy = 1.17.0
httpx = (kline + funding fetcher; reused)
```

No new package additions. Universe expansion uses only existing infrastructure (V3_MODELS tuple expansion + REQUIRED_GAP constant + feature parquet regen).

---

## Section 10 — Single-Axis Verifier (Engineer Phase 5.5 must check)

The Phase 5.5 Engineer verifies these single-axis claims:

| # | Check | Verifier |
|---|---|---|
| A1 | V3_FEATURE_COLUMNS unchanged at 14 | `len(V3_FEATURE_COLUMNS) == 14` AND `'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS` |
| A2 | V3_FEATURES_PER_SYMBOL unchanged (empty) | `V3_FEATURES_PER_SYMBOL == {}` |
| A3 | V3_ATR_MULTIPLIERS_PER_SYMBOL unchanged (LDO only) | `V3_ATR_MULTIPLIERS_PER_SYMBOL == {'LDOUSDT': (1.5, 0.75)}` |
| A4 | V3_MODELS exactly 5 entries with VETUSDT present | `len(V3_MODELS) == 5` AND `('E (VETUSDT)', 'VETUSDT') in V3_MODELS` |
| A5 | REQUIRED_GAP == 110 (5-symbol formula) | `REQUIRED_GAP == 110` |
| A6 | ITERATION_LABEL == 'v3-033' | `ITERATION_LABEL == 'v3-033'` |
| A7 | Risk gate config UNCHANGED | `BTC_TREND_CONFIG`, `HIT_RATE_CONFIG`, `RiskV2Config` byte-identical to iter-v3/032 setup |
| A8 | VET feature parquet exists | `data/features_v3/VETUSDT_8h_features.parquet` exists and has matching schema |

Pass criterion: ALL 8 checks PASS. Any failure → BLOCK.

---

## Section 11 — Catalog Row Pre-Commit

```
| iter-v3/033 | 2026-05-08 | NEW universe expansion → V3_MODELS 4 → 5 (+VETUSDT; per-symbol-feature-signature criterion 2nd application after iter-v3/029 ALGO success) | IS Sharpe Δ TBD vs iter-v3/032 anchor +0.2360 | OOS Sharpe TBD vs anchor +1.9338 | TBD verdict | TBD candidate? |
```

**Pre-committed dispositions** (cannot be renegotiated post-hoc):

1. **PATH A (PROMISING) AND Falsifier 4-6 ALL PASS**: catalog YES — iter-v3/039 CONFIRMATION-bundle ingredient (5-symbol expansion architectural decision; compoundable with regime_momentum_signed_5d + ALGO + LDO ATR multipliers).
2. **PATH B (NEGATIVE-DILUTION; VET drag)**: catalog NO; VET axis CLOSED-SYMBOL-CYCLE; 5th-symbol-add axis CLOSED at this baseline; methodology generalization questioned (single negative does not falsify the per-symbol-feature-signature criterion but reduces evidence weight); iter-v3/034 explores a DIFFERENT axis (e.g., another engineered feature, OR per-symbol features for incumbent that underperforms).
3. **PATH C (INERT)**: catalog NO; per-symbol-feature-signature criterion VALIDATED-INERT (criterion correctly predicted compatibility but Optuna at single-seed couldn't surface signal — retest at multi-seed deferred).
4. **PATH C-2 (NEGATIVE-no-effect)**: catalog NO; universe expansion didn't propagate; iter-v3/034 explores DIFFERENT axis category (likely engineered feature or per-symbol labeling axis).

**Catalog count after iter-v3/033**: 5 of 10 EXPLORATIONs in post-iter-v3/028 cycle; 5 EXPLORATIONs remaining; next CONFIRMATION = iter-v3/039.

**Forward axis pipeline** (iter-v3/034+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_engineered_features_proven.md` LOCKED):

- **iter-v3/034 candidates** (depending on iter-v3/033 verdict):
  - PATH A: another engineered feature ALONE on top of iter-v3/033's 5-symbol baseline (per iter-v3/028 catalog hint: `fracdiff_d05_close` OR `hurst_drift_50_200` OR `adx_signed_momentum`).
  - PATH B/C/C-2: DIFFERENT axis category — engineered features (HIGH-priority per `feedback_v3_engineered_features_proven.md`) OR per-symbol features for incumbent that underperforms OR DSR gate reformulation (MEDIUM #3) OR TRX/2022-Q4 regime gate retest (MEDIUM #4).

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (5 of 10 in post-iter-v3/028 cycle); STRUCTURAL axis Category 5 declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_strict_10_to_1_cadence.md`.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (per-symbol feature-signature alignment 2nd application after iter-v3/029 ALGO success); predicted IS [+0.30, +0.70] median +0.50 / OOS [+1.50, +2.10] median +1.80.
- [x] §2 IS-only numerical evidence with COMMITTED EDA SHA `06d4ba9` (Phase 1+3); 14-feature dispersion ranking across 4 incumbents + 3-candidate composite ranking + VETUSDT decision tile + behavioral-effect predictor with derived saturation band [290, 350] anchored at iter-v3/032 single-seed + per-symbol increment proxies.
- [x] §3 sub-fixes (7-item) with reconciliation table 7 rows; new V3_MODELS expansion + REQUIRED_GAP update + ITERATION_LABEL update + feature regen for VET + V3_FEATURE_COLUMNS BYTE-IDENTICAL + V3_ATR_MULTIPLIERS_PER_SYMBOL BYTE-IDENTICAL + verify_label_leakage_gap message update.
- [x] §4 predicted IS Sharpe band [+0.30, +0.70] median +0.50, OOS Sharpe band [+1.50, +2.10] median +1.80; 5 catalog framings + Falsifier 4-6 + process locked.
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks).
- [x] §6 7-primitive risk gate stack UNCHANGED (per-symbol cap stays disabled; regime gate stays disabled outside iter-v3/022).
- [x] §7 8 failure-mode predictions calibrated against 26 prior EXPLORATIONs + iter-v3/029 ALGO precedent + iter-v3/032 single-seed anchor + iter-v3/033 EDA evidence (P4 PROMISING 35-45%; P5 PATH B 20-30%; P6+P7 INERT/concentration-unchanged 20-30%).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [290, 350] + Falsifier 4 (incumbent stability ≥ 220) + Falsifier 5 (VET ≥ 20 IS trades) + Falsifier 6 (VET drag < -10%).
- [x] §9 library stack UNCHANGED from iter-v3/032; no new dependencies for universe expansion.
- [x] §10 Single-Axis Verifier with 8 checks (Engineer Phase 5.5 verifies all).
- [x] §11 catalog row pre-commit + 4 dispositions; forward axis pipeline.

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.

---

## Section 13 — Status

`READY-FOR-PHASE-5.5-GATE`. Brief contains all 10 mandatory sections + verifier. EDA SHA `06d4ba9` committed before this brief per Phase 5.5 reproducibility rule.

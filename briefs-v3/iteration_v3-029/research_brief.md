# Iteration v3-029 — Research Brief

**Type**: EXPLORATION (cadence #1 of 10 in NEW post-iter-v3/028 cycle; **STRUCTURAL axis (Category 5 — NEW universe; denominator expansion)** — RETEST of universe expansion under fundamentally-different selection mechanism per user directive 2026-05-08)
**Track**: v3 (rigor arm) — twenty-ninth iteration
**Branch**: `iteration-v3/029` (off `iter-v3/028` head)
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

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–028 briefs / engineering reports / Critic FINALs / diaries; iter-v3/029 EDA artifacts (committed BEFORE this brief at SHAs `d451885` (per-symbol feature analysis) and `c30369d` (targeted candidate)). The EDA reads ONLY pre-OOS-cutoff IS-window kline data + iter-v3/028 IS-only `model_importance_last_month_<SYM>.csv` files. OOS-window data is reported informationally only and does NOT enter the candidate scoring or recommendation logic.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #1 of 10 in NEW post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: NEW universe — V3_MODELS expands 3 → 4 symbols
                       (BCH+LDO+TRX baseline) + (ALGOUSDT addition)
                       per per_symbol_feature_signature criterion
Cadence: 1 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 5 (NEW universe — denominator expansion; RETEST of HIGH-priority axis #2b
                  under fundamentally-different selection mechanism)
ANCHOR: iter-v3/028 NEW BASELINE (multi-seed mean +0.5101 IS / +0.5053 OOS)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a feature-add variation.
NOT a labeling change. NOT a model architecture change. NOT a risk-primitive variation.
This iteration NEVER updates BASELINE_V3.md (single-seed --exploration mode).
```

**Justification — STRUCTURAL universe-expansion axis RETEST under fundamentally-different selection mechanism**:

iter-v3/028 catalog row (line 54) suggested *"iter-v3/029 axis target = HIGH-priority NEW edge ingredients (different Category 2 composed feature ALONE; fracdiff_d05_close OR hurst_drift_50_200 OR adx_signed_momentum candidates)"*. **User directive 2026-05-08** (verbatim): *"more features analysis, feature analysis per symbol"; "some features are better suited of symbols a but not b"; "don't discard symbol expansion"; "features are the key to have a stable and good models"*. The user directive **overrides** the catalog hint and pivots the axis from "another engineered feature" to "per-symbol feature analysis + targeted symbol expansion under per-symbol-signature criterion".

**Why this is NOT a violation of `feedback_v3_concentration_is_signal.md` `iter-v3/021_universe_expansion_HBAR+AVAX_CLOSED-SYMBOLS-CYCLE`**:

iter-v3/021's catalog caveat (line 233) states: *"Other symbol candidates (ATOM/FIL/ALGO) are deferred to future LOW-priority retest only AFTER higher-priority structural axes are exhausted... cannot revisit without fundamentally different mechanism"*. The fundamentally-different mechanism for iter-v3/029 is:

| Aspect | iter-v3/021 (HBAR+AVAX, FAILED) | iter-v3/029 (ALGO, this brief) |
|---|---|---|
| Selection criterion | LOWEST raw 8h-return correlation with BCH+LDO+TRX | HIGHEST per-symbol feature-signature alignment with the SHARED top-7 features used by all 3 incumbents |
| Number of new symbols | 2 (HBAR + AVAX bundled) | **1 (ALGO alone)** — clean attribution surface |
| EDA evidence basis | Composite of price-correlation + liquidity + data quality + trade-rate proxy | Per-symbol importance dispersion analysis (`d451885`) + per-symbol feature signature alignment (`c30369d`) |
| Mechanism | "Lowest raw correlation = signal diversity" (FALSIFIED at iter-v3/021) | "Highest feature-signature alignment = signal-driver compatibility" (NEW, addresses iter-v3/021 root cause) |
| Anchor | iter-v3/018 BOOTSTRAP +0.3788 / +0.3869 | iter-v3/028 NEW BASELINE +0.5101 / +0.5053 (multi-seed-validated edge ingredient) |

The **fundamentally-different mechanism** is the Phase 1 finding that *raw price correlation is NOT signal diversity*. Phase 1's per-symbol feature-importance dispersion analysis produced numerical evidence that the 14 V3 features have variable importance across BCH/LDO/TRX (7 HIGH-DISP-SYMBOL-SPECIFIC, 6 MID-DISP, 1 LOW-DISP-SHARED). iter-v3/021 did not have this analysis — it selected on the wrong dimension. The new mechanism is **predictive of symbol compatibility with V3_FEATURE_COLUMNS**, not just price diversity.

**Why ALGO and not VET / ADA / FIL / ATOM**:

Phase 3's targeted EDA (`candidate_targeted_ranking.csv`) ranks 5 candidates from iter-v3/021's pool minus HBAR+AVAX (closed dead-paths). ALGO ranks #1 by composite score 0.6517 (alignment_score 0.4642 with NATR_band_OK PASS and highest btc_coupling_std 0.1072). VET narrowly leads on alignment_score (0.4771) but trails on btc_coupling. The btc_coupling component matters because Phase 1 finding shows `btc_ret_14d` is the most-symbol-specific feature with rank dispersion 8 (BCH=14, LDO=6, TRX=14) — LDO USES `btc_ret_14d` in top-7; ALGO's high btc_coupling_std signals it has the kind of BTC sensitivity LDO does. ALGO is the candidate with the best balance of "uses what BCH+TRX use heavily (range_realized_vol_50, vwap_dev_20)" AND "complements LDO's BTC-trend coupling".

**Single-axis discipline**: ONE NEW symbol (ALGO); V3_MODELS 3 → 4; REQUIRED_GAP 66 → 88 = (21+1) × 4. KEEP V3_FEATURE_COLUMNS=14 byte-identical. KEEP regime_momentum_signed_5d (the iter-v3/028 multi-seed-validated edge feature). KEEP 7-primitive risk gate stack byte-identical. NO labeling change. NO ATR multiplier change. NO ENSEMBLE_SIZE change. NO Optuna budget change.

**1-symbol vs 2-symbol decision** (Critic prior on this brief was likely 1-symbol; QR's call is 1-symbol):

iter-v3/021 chose 2-symbol expansion (HBAR+AVAX); the diary lessons explicitly cite this as a contributing failure factor (saturation falsifier FIRED at 311 IS trades > 269 upper bound; new-symbol drag combined -86%). The iter-v3/029 brief aligns with iter-v3/021 diary lesson (c) *"Future universe-expansion EXPLORATIONs should test 1-symbol expansion at a time to isolate per-symbol contribution"*. ALGO alone is the single-axis variation; cleaner attribution surface; smaller saturation risk. Bundle-level OOS trade volume is no longer a hard requirement at EXPLORATION (it applies at CONFIRMATION-bundle level per `feedback_v3_trade_rate_floor_bundle_level`).

After iter-v3/029 the catalog will have: 14 unique axis representations (12 prior + 1 NEW universe expansion 3→4 retest under per-symbol-signature criterion + the iter-v3/028 CONFIRMATION-MERGE).

---

## Section 1 — Hypothesis

Adding ALGOUSDT to V3_MODELS (universe 3 → 4 symbols; 7-primitive risk gate stack BYTE-IDENTICAL to iter-v3/028 anchor; V3_FEATURE_COLUMNS=14 BYTE-IDENTICAL including regime_momentum_signed_5d; per-symbol cap remains DISABLED) will **mechanically dilute single-symbol concentration without removing edge from any incumbent symbol**, because (a) the candidate was selected on per-symbol feature-signature alignment (the corrected criterion vs iter-v3/021's raw-correlation mistake), and (b) ALGO's volatility regime (NATR 4.19% IS) and BTC-trend coupling profile match the SHARED top-7 features that BCH+LDO+TRX use jointly. Predicted IS Sharpe band [+0.30, +0.65] median +0.50 (anchor +0.51; bands honestly reflect lottery uncertainty from 1 NEW symbol's Optuna-fit quality at single-seed n_trials=35). Predicted OOS Sharpe band [+0.30, +0.65] median +0.50 (mirroring IS; concentration drops mechanically from 75-77% to <60%; bundle OOS trades lift toward 130 floor).

**Mechanism explanation** (why per-symbol-feature-signature criterion should help where raw-correlation criterion failed): in the 3-symbol incumbent universe, LightGBM at n_trials=35 fits per-symbol heads using the 14-feature stack. For a NEW symbol to add productive signal, its features' time-series must capture the same regime/microstructure patterns as the incumbents'. Phase 1 identified that 4 features are SHARED-top-7-across-all-3-symbols: `vwap_dev_20`, `range_realized_vol_50`, `ret_kurt_50`, `ret_skew_200`. The candidate's compatibility with these 4 features' driving factors is the load-bearing predictor. iter-v3/021's raw-return correlation captured price-level diversity but NOT signal-driver compatibility — HBAR+AVAX had low raw correlation (HBAR 0.41, AVAX 0.50) but produced -86% combined PnL, falsifying the "lowest correlation = signal diversity" mechanism.

ALGO's per-symbol feature-signature alignment scores (mean abs Pearson of 4 SHARED-top features vs incumbents): 0.4642 — moderate-but-positive alignment. Higher than ATOM (0.4263), FIL (0.4198), ADA (0.4288), but lower than VET (0.4771). The composite score elevates ALGO because its NATR_21 (4.19%) is in band and its btc_coupling_std (0.1072) is the highest in the pool — complementing LDO's btc_ret_14d top-7 ranking which BCH+TRX do not share.

**Why ALGO universe expansion may NOT lift OOS** (3 PATH-C-suspect scenarios):

1. **PATH C-1: ALGO model underperforms in iter-v3/028 fitted regime.** The per-symbol-feature-signature alignment is moderate (0.4642) — not a strong signal. The model may not fit ALGO well at single-seed n_trials=35; ALGO's per-symbol Sharpe is materially negative; the dilution effect is dominated by drag, OOS Sharpe falls below anchor. Probability: 25-35% (this is the dominant PATH C scenario; the iter-v3/021 falsification establishes the prior that universe expansion at single-seed --exploration budget is risky).
2. **PATH C-2: ALGO crowds in the same regimes as TRX/BCH/LDO.** Despite the per-symbol-signature alignment criterion, the LightGBM model surfaces the same regime classifiers (BTC-trend-aligned momentum bursts) for ALGO as for incumbents, leading to crowded losses in 2024-08 yen-carry crash + 2025 January correction (the regime cells where iter-v3/028 BASELINE_V3.md flags PBO max=1.0 LDO/2026-03 data scarcity).
3. **PATH C-3: 4-symbol Optuna budget split (140 fits ÷ 4 sym = 35 fits/symbol on incumbents).** With ENSEMBLE_SIZE=1 + --seeds 1 + n_trials=35 → 35 trials per cell. Adding ALGO does NOT reduce per-symbol fits (each cell is independent under per-symbol architecture). Mitigation: this is identical to iter-v3/028 anchor's per-cell budget — no dilution at the Optuna level.

The counterfactual evidence Phase 3 cites (alignment scores) shows ALGO scores in the moderate-positive range; the empirical question this EXPLORATION answers is whether the alignment translates into productive LightGBM fitting at single-seed n_trials=35.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Phase 1 EDA**: `analysis/iteration_v3-029/per_symbol_feature_analysis.py` (committed at SHA `d451885` BEFORE this brief — Phase 5.5 reproducibility requirement).
**Phase 3 EDA**: `analysis/iteration_v3-029/symbol_candidate_targeted.py` (committed at SHA `c30369d`).

**Inputs read** (IS-only):
- `reports-v3/iteration_v3-028/in_sample/model_importance_last_month_{BCH,LDO,TRX,portfolio}.csv` (Phase 1)
- `reports-v3/iteration_v3-028/{in_sample,out_of_sample}/per_symbol.csv` (sanity check, NOT used for selection)
- `data/{BTC,BCH,LDO,TRX,ADA,ALGO,ATOM,FIL,VET}USDT/8h.csv` IS-window 2023-04-01 → 2025-03-24 (Phase 3)

**Outputs** (committed alongside the scripts):
- Phase 1: `per_symbol_feature_signature.csv`, `feature_dispersion_ranking.csv`, `symbol_specific_features.csv`, `symbol_specific_top_bottom.csv`, `synthesis.md` (4 tables + narrative).
- Phase 3: `candidate_features_alignment.csv`, `candidate_targeted_ranking.csv`, `synthesis.md` (appended).

### 2.1 Phase 1 finding — per-symbol feature dispersion

For each of the 14 V3 features, rank within each symbol's IS-only model_importance_last_month CSV (1=highest importance), then compute rank_range = max-min across BCH/LDO/TRX. The table below is sorted by rank_range descending (most symbol-specific features at top):

| Feature | rank_BCH | rank_LDO | rank_TRX | rank_range | classification |
|---|---:|---:|---:|---:|---|
| hurst_100 | 12 | 14 | 3 | 11 | HIGH-DISP-SYMBOL-SPECIFIC |
| max_dd_window_50 | 2 | 10 | 5 | 8 | HIGH-DISP-SYMBOL-SPECIFIC |
| btc_ret_14d | 14 | 6 | 14 | 8 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_autocorr_lag1_50 | 8 | 12 | 6 | 6 | HIGH-DISP-SYMBOL-SPECIFIC |
| range_realized_vol_50 | 4 | 7 | 1 | 6 | HIGH-DISP-SYMBOL-SPECIFIC |
| ema_spread_atr_20 | 3 | 9 | 9 | 6 | HIGH-DISP-SYMBOL-SPECIFIC |
| vwap_dev_20 | 1 | 4 | 7 | 6 | HIGH-DISP-SYMBOL-SPECIFIC |
| ret_skew_50 | 13 | 8 | 12 | 5 | MID-DISP |
| ret_skew_200 | 6 | 1 | 4 | 5 | MID-DISP |
| hurst_diff_100_50 | 9 | 5 | 10 | 5 | MID-DISP |
| ret_kurt_200 | 7 | 3 | 8 | 5 | MID-DISP |
| ret_kurt_50 | 5 | 2 | 2 | 3 | MID-DISP |
| sym_vs_btc_ret_7d | 10 | 11 | 13 | 3 | MID-DISP |
| **regime_momentum_signed_5d** | **11** | **13** | **11** | **2** | **LOW-DISP-SHARED** |

**Findings**:
- **7 HIGH-DISP-SYMBOL-SPECIFIC features** (rank_range ≥ 6): top-half on at least one symbol AND bottom-half on at least one other. These features depend on symbol regime/microstructure. Key examples:
  - `hurst_100`: TRX rank 3 (TOP) but BCH rank 12 + LDO rank 14 (BOTTOM). hurst_100 is structurally TRX-specific in v3.
  - `btc_ret_14d`: LDO rank 6 (TOP) but BCH rank 14 + TRX rank 14 (BOTTOM). btc_ret_14d is structurally LDO-specific.
  - `max_dd_window_50`: BCH rank 2 (TOP) but LDO rank 10 + TRX rank 5. BCH-leaning feature.
  - `vwap_dev_20`: BCH rank 1 (TOP) but TRX rank 7. BCH-leaning.
- **6 MID-DISP features**: rank_range 3-5; modest cross-symbol variation.
- **1 LOW-DISP-SHARED feature**: `regime_momentum_signed_5d`. Ranks BCH=11, LDO=13, TRX=11. The multi-seed-validated edge feature is uniformly mid-bottom-rank across all 3 symbols — a UNIVERSAL but moderately-ranked predictor. This validates user intuition that engineered features can be widely-applicable; it does NOT mean the feature is unimportant (importance values are 90/171/128 raw, mid-range across symbols).

**Top-7 features SHARED across all 3 symbols simultaneously**: `vwap_dev_20`, `range_realized_vol_50`, `ret_kurt_50`, `ret_skew_200`. These 4 features are top-7 in BCH AND LDO AND TRX. They are the strongest predictor of cross-symbol portability — any new symbol's compatibility with V3_FEATURE_COLUMNS is best approximated by its alignment with these 4 features' driving factors.

### 2.2 Phase 3 candidate ranking under per-symbol-feature-signature criterion

For each candidate (ADA, FIL, ALGO, ATOM, VET — HBAR+AVAX excluded as iter-v3/021 dead-path), compute alignment_score = mean abs Pearson of 4 SHARED-top features' time-series vs each incumbent's same-feature time-series (mean across 3 incumbents per feature, mean across 4 features). Composite = 0.65·alignment_score + 0.20·natr_band_OK + 0.15·btc_coupling_z.

| Rank | Symbol | composite | alignment_score | raw_corr_mean_abs | NATR_21% | NATR_OK | btc_coupling_std |
|---:|---|---:|---:|---:|---:|:---:|---:|
| 1 | **ALGOUSDT** | 0.6517 | 0.4642 | 0.4920 | 4.19 | PASS | 0.1072 |
| 2 | VETUSDT | 0.5865 | 0.4771 | 0.5584 | 3.97 | PASS | 0.0935 |
| 3 | ADAUSDT | 0.5642 | 0.4288 | 0.4960 | 3.79 | PASS | 0.0952 |
| 4 | FILUSDT | 0.5508 | 0.4198 | 0.5335 | 4.15 | PASS | 0.0938 |
| 5 | ATOMUSDT | 0.4771 | 0.4263 | 0.5305 | 3.54 | PASS | 0.0793 |

**ALGO selected as TOP candidate**. VET narrowly leads on alignment_score (0.4771 vs 0.4642) but trails on btc_coupling. The btc_coupling component is load-bearing because Phase 1 finding shows `btc_ret_14d` is symbol-specific (LDO-leaning, rank 6) — ALGO's higher btc_coupling profile makes it a stronger LDO complement than VET.

### 2.3 ALGO decision tile

| Property | Value | Threshold | Verdict |
|---|---:|---:|---|
| Composite score | 0.6517 | rank-1 of 5 candidates | TOP |
| alignment_score (4 SHARED-top features) | 0.4642 | rank-2 (vs VET 0.4771) | NEAR-TOP |
| raw_corr_mean_abs vs BCH+LDO+TRX | 0.4920 | (informational; iter-v3/021 metric) | mid-band |
| NATR_21 IS | 4.19% | band [3.0%, 7.0%] | PASS |
| btc_coupling_std | 0.1072 | rank-1 of 5 | TOP |
| IS coverage (iter-v3/021 EDA carryover) | 100.0% | ≥99% | PASS |
| Pre-IS history | 33.47 months | ≥24mo | PASS |
| Avg daily quote volume IS | $60.6M | >$20M | PASS |
| P10 daily qvol | $12.6M | >$5M | PASS |
| Cap band | MID | (informational) | Layer-1 |

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted IS trade volume change**: iter-v3/028 IS bundle-level trades = 182 (multi-seed mean across 2 outer × 5 inner; cumulative across cells per BASELINE_V3.md). Single-seed iter-v3/028 anchor (the equivalent reference for single-seed iter-v3/029) is the seed=42 metric — ~91 IS trades reported in BASELINE_V3.md per-symbol breakdown (BCH 86 + TRX 85 + LDO 11 = 182 multi-seed cumulative; per-seed approximately 91). Wait — the multi-seed cumulative IS=182 is across ALL outer seeds × cells; per-outer-seed IS is ~91.

For single-seed iter-v3/029 with ALGO added (4 symbols), expected IS trades ≈ 91 (3-sym anchor) + 30 (ALGO single-seed at moderate fit quality, calibrated against iter-v3/021's HBAR 31 + AVAX 39 IS proxy under similar single-seed conditions). Predicted IS bundle-level trades band: **[110, 145]** (+19% to +60% over single-seed anchor 91).

**Saturation falsifier**: per `feedback_axis_saturation_predictor.md` ±25% rule: if observed single-seed IS trades < 110 (lower bound), axis SATURATED on the new symbol AND iter-v3/029 produces NULL-RESULT. If observed > 145 (upper bound), axis OVERSHOOT — flag for risk-amplification review (the iter-v3/021 falsifier that fired).

**Falsifier 4 — Importance rank**: ALGO's `regime_momentum_signed_5d` per-cell importance must be ≥ rank 12/14 in at least one cell (model uses the multi-seed-validated edge feature on the new symbol AT LEAST as moderate-ranked as the LOW-DISP-SHARED status implies). If ALGO ranks regime_momentum_signed_5d at 14/14 (model didn't learn it on ALGO), Falsifier 4 FIRES — diagnose as PROMISING-INERT (single-symbol-pivoted version).

**Falsifier 5 — Concentration shift**: TRX OOS concentration must drop from 75-77% (iter-v3/028 multi-seed mean) below 65%. If TRX OOS concentration stays ≥ 70%, the universe expansion did NOT propagate to the concentration metric — flag as PROMISING-INERT or NEGATIVE-no-effect.

**Falsifier 6 — New-symbol drag**: ALGO OOS PnL must NOT be < -10% weighted_pnl. If ALGO produces large negative drag (similar to HBAR -36.5% / AVAX -49.2% at iter-v3/021), Falsifier 6 FIRES — diagnose as PATH B (NEGATIVE-DILUTION; closes ALGO axis).

### 2.5 Counterfactual: 4-symbol mechanical concentration dilution

Phase 1 baseline anchor: iter-v3/028 single-seed seed=42 OOS bundle metrics.

| Symbol | OOS weighted_pnl (seed=42) | OOS Conc % (3-sym) |
|---|---:|---:|
| BCHUSDT | +6.61% | 41.43% |
| LDOUSDT | -29.90% | -187.36% |
| TRXUSDT | +39.08% | 244.93% |
| **Total (3-sym)** | **+15.79%** | (numerator) |

Under counterfactual ADD ALGO at OOS PnL ~ 0% (lottery-symmetric prior):

| Symbol | OOS weighted_pnl | OOS Conc % (4-sym counterfactual zero-contribution ALGO) |
|---|---:|---:|
| BCHUSDT | +6.61% | 41.43% (UNCHANGED — denominator unchanged at hypothetical zero-contribution) |
| LDOUSDT | -29.90% | -187.36% |
| TRXUSDT | +39.08% | 244.93% |
| ALGOUSDT | 0.00% | 0.00% |
| **Total (4-sym)** | **+15.79%** | (numerator unchanged) |

**Mechanical dilution at zero-contribution ALGO does not alter percentages**. For the dilution mechanism to fire, ALGO must contribute non-trivial positive PnL. Under contribution +5%: TRX concentration drops from 244.93% to 244.93/(15.79+5) = 188.0%; under +10%: drops to 151.5%. The mechanical dilution requires **positive PnL contribution from ALGO** — the pure counterfactual addition arithmetic doesn't help concentration unless ALGO is profitable.

This is the same lesson as iter-v3/021: universe expansion's concentration relief requires the new symbol to contribute positive PnL, NOT just to be added. The brief's hypothesis is therefore conditional on the per-symbol-feature-signature criterion correctly predicting ALGO's compatibility with V3_FEATURE_COLUMNS — without compatibility, ALGO joins the iter-v3/021 dead-path.

---

## Section 3 — Sub-fixes (5-item) with Verifier Commands

| # | Sub-fix | Description | Verifier |
|---|---|---|---|
| 1 | **V3_MODELS expansion 3 → 4** | Add `("F (ALGOUSDT)", "ALGOUSDT")` to V3_MODELS in `run_baseline_v3.py`. Model letter "F" follows the convention (A=BCH, C=LDO, D=TRX, F=ALGO; B/E reserved for v1 historical). | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4; assert any('ALGOUSDT'==sym for _,sym in m.V3_MODELS), m.V3_MODELS"` exits 0 |
| 2 | **REQUIRED_GAP update 66 → 88** | Update `src/crypto_trade/strategies/ml/validation_v3.py` `REQUIRED_GAP: int = (21 + 1) * 4  # 88`. Update `_verify_label_leakage_gap()` message to `n_symbols=4`. | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==88, REQUIRED_GAP"` exits 0; `_verify_label_leakage_gap()` exits 0 |
| 3 | **ITERATION_LABEL update v3-028 → v3-029** | Update `ITERATION_LABEL = "v3-029"` in `run_baseline_v3.py`. | `grep '^ITERATION_LABEL' run_baseline_v3.py` shows `"v3-029"` |
| 4 | **Feature parquet regen for ALGO** | Run `uv run crypto-trade features --symbols ALGOUSDT --interval 8h --track v3 --format parquet --workers 4` to generate `data/features_v3/ALGOUSDT_8h_features.parquet`. | `ls data/features_v3/ALGOUSDT_8h_features.parquet` exists |
| 5 | **V3_FEATURE_COLUMNS BYTE-IDENTICAL UNCHANGED** | KEEP V3_FEATURE_COLUMNS_TOP_N at 14 cols (iter-v3/028 byte-identical). KEEP regime_momentum_signed_5d. NO new feature, NO removal. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"` exits 0 |

**Reconciliation table** (Engineer Phase 5.5 verifier — 6 commands; subset of the iter-v3/021 15-command pattern, scoped to the 5 sub-fixes):

```
1. uv run python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4; assert any(s=='ALGOUSDT' for _,s in m.V3_MODELS), m.V3_MODELS"
2. uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==88, REQUIRED_GAP"
3. uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"
4. ls data/features_v3/ALGOUSDT_8h_features.parquet
5. grep '^ITERATION_LABEL' run_baseline_v3.py | grep -q '"v3-029"'
6. uv run pytest tests/strategies/ml/test_validation_v3.py -v  # adversarial label-leakage gap test against new gap=88
```

---

## Section 4 — Predicted Bands & Catalog Framings

**Anchor (multi-seed iter-v3/028 → single-seed equivalent)**:
- iter-v3/028 multi-seed mean IS Sharpe = +0.5101 / OOS Sharpe = +0.5053
- iter-v3/028 single-seed (seed=42) ~ approximately equivalent IS / OOS metrics (the Pareto floor was +0.5053 at seed=42 / +0.8691 at seed=123)

**Single-seed iter-v3/029 expectation** (PROMISING bands per `feedback_v3_engineered_features_proven.md` PROMISING-band convention shifted to iter-v3/028 anchor +0.51):

| Band | IS Sharpe | OOS Sharpe | Interpretation |
|---|---:|---:|---|
| PATH A — PROMISING (clean) | [+0.50, +0.65] | [+0.50, +0.65] | ALGO contributes positive PnL; concentration dilutes; iter-v3/039 candidate |
| PATH B — NEGATIVE (DILUTION drag) | [+0.30, +0.50) | < +0.40 | ALGO drags IS+OOS materially; closes ALGO axis |
| PATH C — INERT (concentration unchanged) | [+0.40, +0.55] | [+0.40, +0.55] | ALGO model trades but adds no signal; concentration ≥70% |
| PATH C-2 — NEGATIVE-no-effect | ~+0.51 | ~+0.51 | ALGO not productively fitted (Falsifier 4 fires) |

**§4.4 catalog framing table** (5 rows):

| # | Verdict | Conditions | Catalog row tag |
|---|---|---|---|
| 1 | EXPLORATION-PROMISING (clean) | IS ≥ +0.50 AND OOS ≥ +0.50 AND ALGO weighted_pnl > 0 AND TRX OOS concentration < 65% | YES — STRONG candidate; iter-v3/039 CONFIRMATION-bundle ingredient |
| 2 | EXPLORATION-NEGATIVE (DILUTION) | OOS Sharpe < +0.40 (Δ < -0.10 vs anchor) AND ALGO weighted_pnl < -10% AND non-bit-identical incumbent roster | NO — closes ALGO axis; per-symbol-signature criterion FALSIFIED on ALGO |
| 3 | EXPLORATION-PROMISING-INERT | Falsifier 4 fires (regime_momentum rank=14/14 on ALGO) AND OOS Sharpe in [+0.40, +0.55] | NO — ALGO model not productively fitted at single-seed; retest at multi-seed |
| 4 | EXPLORATION-NEGATIVE-no-effect | Falsifier 5 fires (TRX OOS concentration ≥70%) AND IS ~ +0.51 AND OOS ~ +0.51 | NO — universe expansion didn't propagate to concentration; PATH C |
| 5 | EXPLORATION-NEGATIVE (clean) — Falsifier 6 FIRES | ALGO OOS weighted_pnl < -10% AND non-bit-identical roster AND saturation falsifier within band | NO — replication of iter-v3/021 failure mode at 1-symbol scale |

---

## Section 5 — Risk Mitigation

### Cadence-discipline risks (4)

| Risk | Mitigation |
|---|---|
| iter-v3/029 EXPLORATION budget overrun | Hard 2h wall-clock cap. ALGO is a 4-symbol single-seed run; iter-v3/021's 5-symbol single-seed ran 23 min. Estimate ~30-40 min for 4-symbol single-seed. Well within cap. |
| Cycle-cadence inflation | iter-v3/029 is FIRST EXPLORATION of new cycle; CONFIRMATION at iter-v3/039. STRICT 10:1 per `feedback_v3_strict_10_to_1_cadence.md`. |
| Catalog-row pre-commit cleanup | Section 11 pre-commits 4 dispositions. Diary commit closes catalog row regardless of outcome. |
| Single-axis discipline drift | ONE NEW symbol; V3_FEATURE_COLUMNS UNCHANGED; risk gates UNCHANGED. Engineer Phase 6 rejection if any other knob is tuned. |

### Methodology-hygiene risks (4)

| Risk | Mitigation |
|---|---|
| OOS contamination | EDA reads only IS-window data + iter-v3/028 IS-only importance CSVs. Phase 7 is QR's first OOS view. |
| Look-ahead in ALGO features | Feature parquets regenerated via `crypto-trade features --track v3` which uses the same scale-invariant features as incumbents (no rolling-window leakage for ALGO that BCH/LDO/TRX don't share). Adversarial test in iter-v3/022 covers gap propagation. |
| Survivorship bias | ALGO listed 2020-06-16 with 33+ months pre-IS history. No survivorship issue. |
| n_trials=35 single-seed lottery | EXPLORATION budget; multi-seed validation deferred to iter-v3/039 CONFIRMATION. Single-seed result is INFORMATIONAL not load-bearing for BASELINE_V3.md update. |

### Axis-specific risks (3)

| Risk | Mitigation |
|---|---|
| ALGO model collapse at single-seed n_trials=35 | Catalog Falsifier 4 fires if regime_momentum rank 14/14; classified PROMISING-INERT not catastrophic. Iter-v3/030 may retest at multi-seed if enough other PROMISINGs accumulate. |
| Incumbent fits perturb on 4-symbol Optuna context | Per-symbol architecture isolates per-cell Optuna; incumbent cells should fit identically to iter-v3/028 conditions. iter-v3/021 saw incumbent perturbation at 5-sym; 4-sym should be milder. |
| ALGO-driven concentration regression | Falsifier 5 + Falsifier 6 both fire if ALGO drags. iter-v3/030 reverts to 3-sym at first commit if iter-v3/029 PATH B. |

---

## Section 6 — 7-Primitive Risk Gate Stack — UNCHANGED

| Primitive | Threshold | Status |
|---|---|---|
| BTC trend kill | ±15% over 14d (42 bars 8h) | UNCHANGED from iter-v3/028 |
| Vol scaling | RiskV2Wrapper internal | UNCHANGED |
| ADX gate | 20.0 | UNCHANGED |
| Hurst regime | hurst_100 in [0.3, 0.7] band | UNCHANGED |
| Feature z-score OOD | |z| ≤ 2.0 across 35 v2-feature-set | UNCHANGED |
| Low-vol filter | NATR-percentile-based | UNCHANGED |
| Hit-rate feedback | DISABLED (per iter-v2/045) | UNCHANGED |
| Per-symbol cap | DISABLED (iter-v3/020 closed) | UNCHANGED |
| Regime-conditional kill switch | DISABLED outside iter-v3/022 | UNCHANGED |

ALGO inherits the 7-primitive stack byte-identical to incumbents.

---

## Section 7 — 8 Failure-Mode Predictions

Calibrated against iter-v3/007-028 prior EXPLORATIONs + iter-v3/028 multi-seed evidence + iter-v3/029 EDA priors:

| # | Mode | Probability | Evidence |
|---|---|---:|---|
| P1 | OOS contamination via EDA | <5% | EDA explicitly IS-only-window (mechanical OOS_CUTOFF_MS partition) |
| P2 | Optuna budget overrun | <5% | EXPLORATION default n_trials=35; 4-sym single-seed estimated 30-40 min |
| P3 | Pre-commit non-compliance | <5% | 5 sub-fixes in §3 are atomic; reconciliation table covers all |
| P4 | PATH A — ALGO contributes positive PnL | 30-40% | EDA alignment_score 0.4642 is moderate; iter-v3/021's HBAR/AVAX failure is the bear prior |
| P5 | PATH B — ALGO drag (similar to iter-v3/021) | 30-35% | Bear prior — iter-v3/021 failed at low raw correlation; ALGO has similar raw correlation 0.49; selection criterion is fundamentally different but evidence is moderate |
| P6 | PATH C — ALGO INERT (Falsifier 4) | 10-15% | Per-symbol arch should fit ALGO at single-seed n_trials=35; INERT requires regime_momentum to fail to propagate |
| P7 | PATH C-2 — concentration unchanged | 10-15% | ALGO contributes ~0% PnL; Falsifier 5 fires; common scenario in iter-v3/015/019 |
| P8 | OOS-suspicious lottery (single-seed v3 pattern) | 15-20% | iter-v3/013/025/026/027 all showed single-seed OOS divergence; high baseline prior |

**Combined PROMISING (P4) ≈ 30-40%; combined PATH C/INERT (P6+P7) ≈ 20-30%; combined PATH B/NEGATIVE-DILUTION (P5) ≈ 30-35%.** This is a moderate-prior EXPLORATION; the Phase 1 + Phase 3 EDA evidence strengthens the prior over iter-v3/021's HBAR+AVAX experiment but does NOT guarantee PROMISING.

---

## Section 8 — 11 Pre-Registered EXPLORATION Criteria

EXPLORATION never updates BASELINE_V3.md. 11 criteria for catalog-row decision:

1. **OOS Sharpe ≥ +0.50** (anchor +0.51 ± 0.01): catalog row records PROMISING (PATH A). Aspirational.
2. **OOS Sharpe < +0.40** (anchor -0.10): Falsifier 1 fires — EXPLORATION-NEGATIVE if non-bit-identical roster (PATH B / DILUTION) or NEGATIVE-no-effect if axis didn't propagate.
3. **OOS Sharpe in [+0.40, +0.50]**: PROMISING-INERT (catalog INERT).
4. **n_trades ≥ 50 IS, ≥ 50 OOS bundle-level**: BUNDLE-LEVEL trade-rate floor. Predicted IS in [110, 145]; OOS predicted ~70-100 (well above floor at single-seed EXPLORATION).
5. **PBO < 0.40 (per-cell mean)** AND `n_high_pbo_cells_99 ≤ 4`: methodology hygiene; iter-v3/028 mean was 0.124. New ALGO cells may add new high-PBO cells (e.g., ALGO/2024-08 yen-carry).
6. **IC max abs < 0.70**: NO new feature; existing 14-feature IC matrix unchanged. ALGO's per-symbol IC matrix should be reported in engineering report for completeness.
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS for ALL 4 symbols**: 14 features unchanged; incumbent ADF inherits PASS from iter-v3/028; ALGO ADF must be re-run and reported. Expected PASS (features are scale-invariant).
8. **Reproducibility verifier**: SHAs stamped (Phase 1 EDA `d451885`; Phase 3 EDA `c30369d`; brief commit; setup commit; Phase 5.5 gate; engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (waiver inherited from iter-v3/006-028).
10. **Symbol exclusion + feature isolation + track isolation**: `set({BCH, LDO, TRX, ALGO}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; ALGO is NOT in V3_EXCLUDED_SYMBOLS list. No new imports from features modules. Zero cross-track contamination.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in **[110, 145]** AND incumbent BCH+LDO+TRX combined ≥ 78 (Falsifier 4: incumbent stability — iter-v3/028 single-seed was ~91; -15% lower bound = 77) AND ALGO contributes ≥ 10 IS trades (Falsifier 5: new-symbol propagation) AND no ALGO OOS PnL drag < -10% (Falsifier 6: new-symbol drag). Critic uses ALL FOUR signals to disambiguate clean PATH A / PATH B / NULL-RESULT.

**Catalog-axis verdicts** map to §4.4 table.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/028** — no version updates:

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

No new package additions. Universe expansion uses only existing infrastructure.

---

## Section 10 — Adversarial Tests

Universe expansion does not add new code paths beyond V3_MODELS tuple expansion + REQUIRED_GAP constant update. Existing iter-v3/028 tests still PASS. Optional defensive tests (NOT mandatory):

- `tests/test_v3_models_expansion.py::test_v3_models_4_symbols`: assert `V3_MODELS` has 4 entries with ALGOUSDT present.
- `tests/strategies/ml/test_validation_v3.py::test_required_gap_4_symbol`: assert `REQUIRED_GAP == 88` and matches `(timeout_candles+1) × n_symbols` formula.

The mandatory verifier is the §3 reconciliation table (6 commands).

---

## Section 11 — Catalog Row Pre-Commit

```
| iter-v3/029 | 2026-05-08 | NEW universe expansion → V3_MODELS 3 → 4 (+ALGOUSDT; per-symbol-feature-signature criterion; corrects iter-v3/021 raw-correlation mistake) | IS Sharpe Δ TBD vs iter-v3/028 anchor +0.5101 | OOS Sharpe TBD vs anchor +0.5053 | TBD verdict | TBD candidate? |
```

**Pre-committed dispositions** (cannot be renegotiated post-hoc):

1. **PATH A (PROMISING) AND Falsifier 4-6 ALL PASS**: catalog YES — iter-v3/039 CONFIRMATION-bundle ingredient (compoundable with regime_momentum_signed_5d as universe-expansion architectural decision).
2. **PATH B (NEGATIVE-DILUTION; ALGO drag)**: catalog NO; ALGO axis CLOSED-SYMBOL-CYCLE; iter-v3/030 explores DIFFERENT axis (e.g., another engineered feature per the iter-v3/028 catalog hint, OR a different concentration mechanism).
3. **PATH C (INERT)**: catalog NO; per-symbol-feature-signature criterion VALIDATED-INERT (criterion correctly predicted compatibility but Optuna at single-seed couldn't surface signal — retest at multi-seed deferred).
4. **PATH C-2 (NEGATIVE-no-effect)**: catalog NO; universe expansion didn't propagate; iter-v3/030 explores DIFFERENT axis category.

**Catalog count after iter-v3/029**: 1 of 10 EXPLORATIONs in NEW post-iter-v3/028 cycle; 9 EXPLORATIONs remaining; next CONFIRMATION = iter-v3/039.

**Forward axis pipeline** (iter-v3/030+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_engineered_features_proven.md` LOCKED):

- **iter-v3/030 candidates** (depending on iter-v3/029 verdict):
  - PATH A: another engineered feature ALONE on top of iter-v3/029's 4-symbol baseline (per iter-v3/028 catalog hint: `fracdiff_d05_close` OR `hurst_drift_50_200` OR `adx_signed_momentum`).
  - PATH B/C: DIFFERENT axis category — engineered features (HIGH-priority per `feedback_v3_engineered_features_proven.md`) OR DSR gate reformulation (MEDIUM #3) OR TRX/2022-Q4 regime gate retest (MEDIUM #4).

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (1 of 10 in new cycle); STRUCTURAL axis Category 5 declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_strict_10_to_1_cadence.md` + user directive 2026-05-08 override of catalog hint.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (per-symbol feature-signature alignment vs iter-v3/021 raw-correlation criterion); predicted IS [+0.30, +0.65] median +0.50 / OOS [+0.30, +0.65] median +0.50.
- [x] §2 IS-only numerical evidence with COMMITTED EDA SHAs `d451885` (Phase 1) and `c30369d` (Phase 3); Phase 1 14-feature dispersion ranking + Phase 3 5-candidate composite ranking + ALGO decision tile + behavioral-effect predictor with derived saturation band [110, 145] anchored at iter-v3/028 single-seed equivalent + per-symbol increment proxies.
- [x] §3 sub-fixes (5-item) with reconciliation table 6 rows; new V3_MODELS expansion + REQUIRED_GAP update + ITERATION_LABEL update + feature regen for ALGO + V3_FEATURE_COLUMNS BYTE-IDENTICAL.
- [x] §4 predicted IS Sharpe band [+0.30, +0.65] median +0.50, OOS Sharpe band [+0.30, +0.65] median +0.50; 5 catalog framings + Falsifier 4-6 + process locked.
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks).
- [x] §6 7-primitive risk gate stack UNCHANGED (per-symbol cap stays disabled; regime gate stays disabled outside iter-v3/022).
- [x] §7 8 failure-mode predictions calibrated against 22 prior EXPLORATIONs + iter-v3/028 multi-seed anchor + iter-v3/029 EDA evidence (P4 PROMISING 30-40%; P5 PATH B 30-35%; P6+P7 INERT 20-30%).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [110, 145] + Falsifier 4 (incumbent stability ≥ 78) + Falsifier 5 (ALGO ≥ 10 IS trades) + Falsifier 6 (ALGO drag < -10%).
- [x] §9 library stack UNCHANGED from iter-v3/028; no new dependencies for universe expansion.
- [x] §10 no new adversarial tests required (no new code paths beyond V3_MODELS tuple + REQUIRED_GAP constant).
- [x] §11 catalog row pre-commit + dispositions; forward axis pipeline.

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.

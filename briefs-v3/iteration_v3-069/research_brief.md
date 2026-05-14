# iter-v3/069 — Research Brief

**Branch**: `iteration-v3/069`
**EDA SHA**: `95038dd`
**Setup commit SHA**: `cde507b` (to be re-committed in a follow-up backfill commit after Phase 5.5 gate; this brief was first committed at `cde507b` as part of the setup commit; brief Section 10 SHA stamps backfilled to this brief via a follow-up `docs(iter-v3/069): backfill setup SHA in brief` commit)
**Iteration type**: EXPLORATION (cycle 1 #10 of 10 — FINAL before /070 CONFIRMATION; NON-FEATURE PIVOT continuation; UNIVERSE EXPANSION axis — denominator-expansion mechanism per `feedback_v3_concentration_is_signal.md`)
**Axis**: UNIVERSE EXPANSION — V3_MODELS expands 3 → 4 symbols (BCH+LDO+TRX + **ADAUSDT**); 14 V3_FEATURE_COLUMNS UNCHANGED; 7-primitive risk gate stack BYTE-IDENTICAL to /060; ATR multipliers UNCHANGED at default (2.0, 1.0); label_timeout REVERTED from /068's 20160 back to 10080; REQUIRED_GAP scaled 66 → 88 = (21+1)×4

---

## Section 0 — Data Split Declaration

**UNCHANGED.** OOS_CUTOFF_DATE = `2025-03-24` (IMMUTABLE; sacred constant per `feedback_no_cheating.md`). Training window = 24 months walk-forward (IMMUTABLE per `feedback_training_window.md`). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT, **ADAUSDT** (4 symbols, +1 vs /051 SYSTEM-LEVEL REVERT 3-symbol architecture). Feature universe = 14 V3_FEATURE_COLUMNS (UNCHANGED post-/064 revert at commit `04080c4`).

## Section 0.5 — Iteration Type Declaration

**TYPE**: EXPLORATION (cycle 1 #10 of 10 — FINAL before /070 CONFIRMATION; NON-FEATURE PIVOT continuation; UNIVERSE EXPANSION axis; `--exploration` mode 3 seeds; ~1.5h target wall-clock due to 4-symbol scale).

- **Cycle 1 EXPLORATION slot**: #10 of 10 — **FINAL** EXPLORATION before /070 CONFIRMATION (per `feedback_v3_strict_10_to_1_cadence.md` Directive 2: STRICT 10:1 EXPLORATION:CONFIRMATION; do NOT collapse 10th EXPLORATION into CONFIRMATION).
- **Sub-type**: **NON-FEATURE PIVOT CONTINUATION — UNIVERSE EXPANSION axis**. Per Critic /064 Rec #4 NON-FEATURE pivot mandate (LOCKED for /065-/069 per `feedback_v3_iter064_process_lessons.md` Rule 5). /065 chose UNIVERSAL labeling SL widening (SUSPICIOUS-OOS-DOMINANT — first /070 candidate); /066 chose UNIVERSAL vol_scale_ceiling=0.8 (INERT-AT-EXPLORATION; closed); /067 chose universal inference-threshold floor (INERT-AT-EXPLORATION; Path D non-activation closed); /068 chose UNIVERSAL labeling timeout doubling Path C (NEGATIVE; labeling-timeout family CLOSED both directions). /069 pivots to UNIVERSE EXPANSION — addressing Critic /068 Rec #3 LDO weakness pattern (/060 18.2% / /064 7.1% / /068 8.3% OOS WR — three consecutive cycle 1 LDO failures) via the denominator-expansion mechanism explicitly permitted by `feedback_v3_concentration_is_signal.md` LOCKED orthogonal-mechanism rule.
- **Run mode**: `--exploration` (ENSEMBLE_SIZE=3, seeds from outer=42 lineage subset `[191664963, 1662057957, 1405681631]`).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total trials = 35 × 4 syms × 3 seeds = **420** (vs 315 at /060-/068 EXPLORATION at 3 syms). **Per-symbol Optuna budget UNCHANGED at 35 × 3 = 105 fits/cell** (each LightGbmStrategy instance fits independently per symbol — CONTRA the flawed /021 reasoning that "5 sym × 35 trials = 175 split 5 ways").
- **Wall-clock target**: ~1.5h (within 2h EXPLORATION HARD CAP per `feedback_v3_cadence_discipline.md`). Scales linearly with symbol count: 0.7h at 3 syms (/068 wall-clock) → 0.93h naive scaling → 1.5h reserved for the 4-symbol training + Optuna budget growth (33% scale-up).

**Cycle 1 catalog status before /069**:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor; IS +0.8325 / OOS +0.1403) | PROMISING-EXPLORATION |
| #2 | /061 | TRX RiskV2 anti-Kelly (Path B vol_scale_floor) | INERT-AT-EXPLORATION (closed) |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred to /070) |
| #4 | /063 | MASS FEATURE EXPANSION (Path B 46 features) | SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (closed) |
| #5 | /064 | Phased mass-expansion #1 (+adx_14) | NEGATIVE (closed) |
| #6 | /065 | NON-FEATURE PIVOT: UNIVERSAL SL widen 1.0 → 1.5 (Path D) | SUSPICIOUS-OOS-DOMINANT (first /070 candidate) |
| #7 | /066 | NON-FEATURE PIVOT: UNIVERSAL vol_scale_ceiling 1.0 → 0.8 (Path E0.8) | INERT-AT-EXPLORATION (closed) |
| #8 | /067 | NON-FEATURE PIVOT cont: UNIVERSAL inference-threshold TIGHTEN 0.60 (Path D) | INERT-AT-EXPLORATION (closed) |
| #9 | /068 | NON-FEATURE PIVOT cont: UNIVERSAL labeling TIMEOUT widen 21 → 42 (Path C) | NEGATIVE (closed both directions) |
| **#10** | **/069** | **NON-FEATURE PIVOT cont: UNIVERSE EXPANSION 3 → 4 symbols (+ADAUSDT)** | **TBD** |
| CONFIRMATION | /070 | Bundle: /065 SL widening + /062 Path B4 deferred spec + (potentially /069 if PROMISING) | TBD |

**Why UNIVERSE EXPANSION axis at slot #10**:

1. **Critic /068 Rec #3 directive (BINDING)**: "LDO weakness pattern: /060 18.2% / /064 7.1% / /068 8.3% OOS WR demands LDO-targeted axis at /069 or post-/070. Three consecutive cycle 1 failures. Escalate to feature/model axis (NOT labeling-timeout/SL — closed). Candidates: LDO-only feature_columns variation, LDO-only ATR override, OR **universe expansion to dilute concentration** per `feedback_v3_concentration_is_signal.md`." Universe expansion is the UNIVERSAL-axis-discipline-compatible LDO-targeting mechanism (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` 2-CONFIRMATION-confirmed CLOSED axis at system level: per-symbol customizations bundled at CONFIRMATION = ANTI-PATTERN). Universe expansion delivers LDO dilution via the universe denominator (4 syms instead of 3) without introducing per-symbol customization. NOT per-symbol features. NOT per-symbol ATR. UNIVERSAL: ADA gets the same 14 V3_FEATURE_COLUMNS, same default (2.0, 1.0) ATR multipliers, same 7-primitive risk gate stack as BCH/LDO/TRX.

2. **`feedback_v3_concentration_is_signal.md` LOCKED 2026-05-07**: per-symbol PnL share caps CLOSED (iter-v3/020 PATH C). Permitted alternatives for "concentration" axes:
   - (a) Universe expansion (denominator expansion — adds more symbols rather than scaling existing ones)
   - (b) Per-symbol drawdown brake (loss-stop semantics)
   - (c) Vol-target ceiling (exposure ceiling)
   - (d) Regime-conditional kill switch (binary off/on)
   /069 picks (a). (b) was attempted at iter-v3/054 — entered permanent deadlock per `feedback_v3_oracle_eda_validity.md`. (c) is mostly INFERENCE-time + already partially explored at /066. (d) is the most aggressive — defer.

3. **Critic /066 Rec #2 directive (locked at cycle 1)**: AVOID universal symmetric clip/cap mechanisms. /069 axis is structurally distinct: universe expansion is NOT a clip/cap mechanism — it ADDS a new per-symbol head with its own independent Optuna fit, then aggregates trades into the unified portfolio. Each existing symbol's trade emission is BYTE-IDENTICAL on the 3-symbol overlap (BCH/LDO/TRX retain their own Optuna fits; the 4th ADA head is independently learned).

4. **`feedback_v3_engineered_features_dont_stack.md`**: ONE substantive axis at EXPLORATION. /069's single change is V3_MODELS adds ADAUSDT. All prior axis settings REVERT to /060 baseline:
   - /065 ATR multipliers REVERT to default (2.0, 1.0) — already reverted at /066/067/068
   - /066 vol_scale_ceiling REMAINS at default 1.0 — already reverted at /067/068
   - /067 inference_threshold_floor REMAINS at default 0.0 — already reverted at /068
   - /068 label_timeout_minutes REVERTS from 20160 back to 10080 (REQUIRED_GAP changes from 129 to 88)
   - /069 V3_MODELS adds ADAUSDT — single substantive change

5. **Distinct from iter-v3/021 universe expansion (HBAR+AVAX NEGATIVE-clean closed)**:
   - /021 added 2 symbols (HBAR + AVAX); /069 adds 1 symbol (ADA) per `feedback_v3_iter064_process_lessons.md` lesson (b) "Universe expansion at n_trials=35 split N ways" — but /021's mechanism analysis was WRONG (Optuna fits independently per symbol; per-symbol budget UNCHANGED). The REAL reason for 1-symbol expansion: cleaner single-axis attribution.
   - /021 selected HBAR+AVAX via correlation-only EDA (HBAR rank 1, AVAX rank 2 on 0.30-weighted-correlation composite). /069 selects ADA via feature-space-proximity-dominant composite (per /021 diary lesson (a): "EDA correlation ranking is necessary but not sufficient"). ADA has the LOWEST mean Euclidean distance in z-score feature space to incumbents (BCH+LDO+TRX): mean_z_dist = 0.6524, vs FIL 0.759, ATOM 0.751, ALGO 0.842, VET 0.866.
   - HBAR + AVAX are CLOSED at the catalog level per /021 diary lesson (c); excluded from /069 candidate pool.

6. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`** (system-level CONFIRMED across 2 CONFIRMATIONs /039 + /050): per-symbol customizations break IS aggregate at multi-seed. UNIVERSAL universe expansion (adding a symbol without per-symbol customizations) is the STRUCTURALLY SAFE alternative — the 4th symbol uses the SAME 14 V3_FEATURE_COLUMNS, SAME default (2.0, 1.0) ATR multipliers, SAME 7-primitive risk gate stack. No per-symbol differentiation. This is the discipline-compatible LDO-targeting mechanism per `feedback_v3_axis_selection_quant_discipline.md`.

7. **Per `feedback_v3_oracle_eda_validity.md`**: universe expansion is ORACLE-EDA-valid (the per-symbol head's labeling function is STATELESS w.r.t. signal-emission state; the cross-symbol portfolio aggregator does not introduce stateful coupling because each symbol's RiskV3Wrapper operates on its own state). NO deadlock risk per /054 closure rule (which CLOSED stateful per-symbol drawdown brake; ADA addition adds a STATELESS per-symbol head).

## Section 1 — Testable Hypothesis (ONE sentence)

> Adding ADAUSDT to V3_MODELS (universe 3 → 4 symbols; 14 V3_FEATURE_COLUMNS UNCHANGED; 7-primitive risk gate stack BYTE-IDENTICAL to /060; ATR multipliers default (2.0, 1.0); label_timeout REVERTED to 10080; REQUIRED_GAP scaled 66 → 88) — exploiting ADA's structurally CLOSEST feature-regime overlap with the BCH+LDO+TRX incumbents (mean Euclidean z-distance 0.6524; per /021 lesson (a) the dominant axis of symbol selection) — produces a Sharpe shift centered near INERT-band (~45% probability) with non-zero PROMISING upside (~20% probability) by mechanically diluting LDO concentration (LDO IS trade-share 11/159 = 6.9% → 11/(159+~50) = 5.3%) and adding an independent per-symbol Optuna fit at 35 trials × 3 seeds, at the structural COST of a +1% per-cell training-sample loss from REQUIRED_GAP scaling 66 → 88; predicted IS Δ band [-0.50, +0.27] (PROMISING upper [+0.10, +0.27] / NEGATIVE lower [-0.50, -0.20]) and OOS Δ band [-0.50, +0.36] (PROMISING upper [+0.10, +0.36] / NEGATIVE lower [-0.50, -0.30]) per Critic /068 Rec #1 widening; NEGATIVE-AT-EXPLORATION is calibrated at 25% probability given the /021 universe-expansion precedent + Critic /068 Rec #1 wider envelope.

## Section 2 — Numerical EDA Tables

EDA committed at SHA `95038dd` (`analysis/iteration_v3-069/universe_expansion_eda.py`). Produces 6 tables (T0-T6) + 1 ranking CSV + 1 per-symbol z-score CSV. Anchor = iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403; 3-seed lineage subset of /059's unified 10-seed mass). NOT iter-v3/065 nor /068 (parallel cycle 1 axes; /060 is the canonical EXPLORATION-mode anchor per `feedback_v3_cycle1_axis_pass_criteria.md`).

### Section 2.1 — T0 Anchor-value declaration (Rule 1 compliance)

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+0.8325** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.1403** | `reports-v3/iteration_v3-060/comparison.csv:2` |
| max_drawdown_in_sample | **31.8701** | `reports-v3/iteration_v3-060/comparison.csv:4` |
| max_drawdown_out_of_sample | **35.7804** | `reports-v3/iteration_v3-060/comparison.csv:4` |
| n_trades_in_sample | **159** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| n_trades_out_of_sample | **102** | `reports-v3/iteration_v3-060/comparison.csv:7` |
| weighted_pnl_total_in_sample | **+51.8906** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| weighted_pnl_total_out_of_sample | **+5.4989** | `reports-v3/iteration_v3-060/comparison.csv:10` |
| dsr | **0.0** | `reports-v3/iteration_v3-060/comparison.csv:11` |
| pbo | **0.1278** | `reports-v3/iteration_v3-060/comparison.csv:12` |
| psr | **0.9763** | `reports-v3/iteration_v3-060/comparison.csv:13` |
| BCH_OOS_weighted_pnl | **+1.9078** | `reports-v3/iteration_v3-060/comparison.csv:18 (per_symbol weighted_pnl col)` |
| LDO_OOS_weighted_pnl | **-19.7208** | `reports-v3/iteration_v3-060/comparison.csv:19 (per_symbol weighted_pnl col)` |
| TRX_OOS_weighted_pnl | **+23.3119** | `reports-v3/iteration_v3-060/comparison.csv:20 (per_symbol weighted_pnl col)` |
| BCH_OOS_n_trades | **37** | `reports-v3/iteration_v3-060/comparison.csv:18 (n_trades col)` |
| LDO_OOS_n_trades | **11** | `reports-v3/iteration_v3-060/comparison.csv:19 (n_trades col)` |
| TRX_OOS_n_trades | **54** | `reports-v3/iteration_v3-060/comparison.csv:20 (n_trades col)` |
| BCH_OOS_win_rate | **32.4%** | `reports-v3/iteration_v3-060/comparison.csv:18 (win_rate col)` |
| LDO_OOS_win_rate | **18.2%** | `reports-v3/iteration_v3-060/comparison.csv:19 (win_rate col)` |
| TRX_OOS_win_rate | **48.1%** | `reports-v3/iteration_v3-060/comparison.csv:20 (win_rate col)` |
| BCH_IS_n_trades | **73** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| LDO_IS_n_trades | **11** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| TRX_IS_n_trades | **75** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| BCH_IS_win_rate | **45.2%** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| LDO_IS_win_rate | **27.3%** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| TRX_IS_win_rate | **29.3%** | `reports-v3/iteration_v3-060/in_sample/per_symbol.csv` |
| frac_positive_paths_cpcv | **0.6444** | BASELINE_V3.md Headline Metrics (CPCV invariant across architectures) |
| current_universe | **BCH+LDO+TRX (3 symbols)** | `run_baseline_v3.py:139-143 V3_MODELS` |
| current_required_gap | **66** | `validation_v3.py:56 — will need 88 = (21+1)*4 for /069` |
| LDO_OOS_WR_iter060 | **18.2%** | Critic /068 Rec #3 baseline |
| LDO_OOS_WR_iter064 | **7.1%** | diary-v3/iteration_v3-068.md:34 cite |
| LDO_OOS_WR_iter068 | **8.3%** | diary-v3/iteration_v3-068.md:34 cite |

These are the BIT-EXACT /060 anchor values per Phase 5.5 anchor-value correctness gate (Rule 1 of `feedback_v3_iter064_process_lessons.md`). All Section 4 falsifier bands reference these. RECURRENCE-flag awareness: /065 brief Section 2.5 originally cited "+24.75 OOS wpnl (BCH)" (13× error vs +1.9078 actual); /066-/068 briefs CLEAN; /069 brief explicitly cross-checks all anchor values against the source file via T0 EDA output before commit.

### Section 2.2 — T1 Per-candidate Gate 1 (data quality) + Gate 2 (liquidity)

Source: `data/{symbol}/8h.csv` IS-window 2023-04-01 → 2025-03-24.

| symbol | pre_is_months | is_coverage_pct | gap_count | avg_qvol_M_usd | p10_qvol_M_usd | gate1_pass | gate2_pass |
|---|---:|---:|---:|---:|---:|:-:|:-:|
| **ATOMUSDT** | 37.74 | 100.0 | 0 | $105.8M | $39.1M | YES | YES |
| **FILUSDT** | 29.47 | 100.0 | 0 | $220.6M | $68.3M | YES | YES |
| **ALGOUSDT** | 33.47 | 100.0 | 0 | $60.6M | $12.6M | YES | YES |
| **ADAUSDT** | 37.97 | 100.0 | 0 | $390.6M | $101.4M | YES | YES |
| **VETUSDT** | 37.51 | 100.0 | 0 | $38.3M | $9.5M | YES | YES |

**Reading**: All 5 candidates PASS Gate 1 (24mo pre-IS history + IS coverage ≥99% + gaps≤5) and Gate 2 (avg qvol > $20M AND p10 > $5M). ADA has the **HIGHEST liquidity** at $390.6M average daily quote volume (3× ATOM, 1.8× FIL, 6.4× ALGO, 10× VET). Listing date 2020-01-31 gives 37.97 months pre-IS history (well above 24-month requirement).

### Section 2.3 — T2 Cross-correlation with BCH/LDO/TRX (8h log returns, IS window)

| symbol | corr_BCH | corr_LDO | corr_TRX | mean_abs_corr | max_abs_corr | gate3_corr_pass |
|---|---:|---:|---:|---:|---:|:-:|
| ATOMUSDT | 0.5801 | 0.6013 | 0.4100 | 0.5305 | 0.6013 | YES |
| FILUSDT | 0.6038 | 0.5843 | 0.4123 | 0.5335 | 0.6038 | YES |
| ALGOUSDT | 0.5558 | 0.5601 | 0.3601 | 0.4920 | 0.5601 | YES |
| **ADAUSDT** | **0.5523** | **0.5553** | **0.3804** | **0.4960** | **0.5553** | **YES** |
| VETUSDT | 0.6035 | 0.5576 | 0.5141 | 0.5584 | 0.6035 | YES |

**Reading**: All 5 candidates have max_abs_corr < 0.70 (IC hard gate). ADA mean |corr| = 0.4960 (3rd lowest after ALGO 0.4920 and ATOM 0.5305). Correlation alone is NOT decisive for symbol selection per /021 diary lesson (a) — feature-space proximity matters more.

### Section 2.4 — T3 Feature-space proximity (PER /021 LESSON (a) — DOMINANT SELECTION AXIS)

Source: 6 stationary feature proxies (log_return_8h, ret_5d, vol_50bar, skew_50bar, kurt_50bar, autocorr_lag1_50) computed on IS-window 8h returns. Per-symbol mean z-scores pooled across all 8 symbols. Euclidean distance in z-score space to each of 3 incumbents.

| symbol | z_dist_BCH | z_dist_LDO | z_dist_TRX | **mean_z_dist** |
|---|---:|---:|---:|---:|
| **ADAUSDT** | **0.2630** | **0.6306** | **1.0634** | **0.6524** (lowest) |
| ATOMUSDT | 0.4746 | 0.8670 | 0.9123 | 0.7513 |
| FILUSDT | 0.4505 | 0.6576 | 1.1695 | 0.7592 |
| ALGOUSDT | 0.6002 | 0.5916 | 1.3332 | 0.8416 |
| VETUSDT | 0.6236 | 0.7066 | 1.2685 | 0.8662 |

**Reading**:
- **ADA has the LOWEST mean z-distance (0.6524)** to incumbents — strongest feature-regime overlap. The 14 V3_FEATURE_COLUMNS (built on statistical moments: ret_kurt_50/200, ret_skew_50/200, range_realized_vol_50, hurst_diff_100_50, ret_autocorr_lag1_50, etc.) operate in a space where ADA most closely resembles the 3 incumbents.
- **ADA's z_dist_BCH = 0.2630** is REMARKABLY low — ADA and BCH have very similar feature-regime characteristics in the 6-proxy space. This implies the 14 V3_FEATURE_COLUMNS trained per-symbol Optuna fit on ADA will encounter feature distributions close to what it learned for BCH.
- TRX is the OUTLIER incumbent across all 5 candidates (highest z_dist for every candidate). This reflects TRX's structural distinctness (price stability, low volatility, "stablecoin-like" return distribution within the v3 universe).
- ALGO (8.42) and VET (8.66) have the LARGEST feature-regime distance. The /021 ranking would have picked ADA first if it had weighted feature-proximity correctly.
- **Critical context** (per /021 diary lesson (a)): /021 picked HBAR by correlation (0.41 mean |corr|, rank 1 by correlation) but HBAR was the WORST IS contributor (-36.5%). The feature-space proximity for HBAR was likely much higher than ADA's — consistent with the post-hoc finding that HBAR's feature regime didn't match the 14-feature stack's design assumptions.

### Section 2.5 — T4 Trade-rate proxy (informational)

Source: NATR_21 IS-window × 90 candles/month × gate retention 0.25.

| symbol | NATR_21_IS_pct | raw_trades_per_month_proxy | gate_retained_trades_per_month_proxy |
|---|---:|---:|---:|
| ATOMUSDT | 3.54% | 7.96/mo | 1.99/mo |
| FILUSDT | 4.15% | 9.33/mo | 2.33/mo |
| ALGOUSDT | 4.19% | 9.42/mo | 2.36/mo |
| **ADAUSDT** | **3.79%** | **8.54/mo** | **2.13/mo** |
| VETUSDT | 3.97% | 8.94/mo | 2.24/mo |

**Reading**: ADA's trade-rate proxy of ~2.13/month is in the middle of the candidate pool. Comparison to incumbents: BCH /060 ≈ 3.04/mo, LDO ≈ 0.46/mo, TRX ≈ 3.13/mo. ADA's proxy is between LDO and BCH/TRX. Over 14 OOS months, this projects to ~30 OOS ADA trades — sufficient for per-symbol signal evaluation.

### Section 2.6 — T5 Composite ranking + final pick

Composite scoring (REWEIGHTED per /021 diary lesson (a) — feature-space proximity dominant):
```
Composite = 0.35 × feature_proximity (1 - mean_z_dist / max_z_dist)
          + 0.20 × complementarity (1 - mean_abs_corr_baseline)
          + 0.20 × data_quality (gate1_pass × 0.5 + gate2_pass × 0.5)
          + 0.15 × liquidity (log10(avg_qvol_M) / log10(1000))
          + 0.10 × trade_rate (gate_retained / 5.0 trade/month proxy)
```

| Rank | Symbol | Composite | feat_prox (0.35) | compl (0.20) | dq (0.20) | liq (0.15) | tr (0.10) |
|---:|---|---:|---:|---:|---:|---:|---:|
| **1** | **ADAUSDT** | **0.5594** | **0.2468** | **0.5040** | 1.0 | 0.8639 | 0.4260 |
| 2 | FILUSDT | 0.5003 | 0.1235 | 0.4665 | 1.0 | 0.7812 | 0.4660 |
| 3 | ATOMUSDT | 0.4814 | 0.1326 | 0.4695 | 1.0 | 0.6748 | 0.3980 |
| 4 | ALGOUSDT | 0.4479 | 0.0284 | 0.5080 | 1.0 | 0.5942 | 0.4720 |
| 5 | VETUSDT | 0.4123 | 0.0000 | 0.4416 | 1.0 | 0.5277 | 0.4480 |

**TOP PICK: ADAUSDT** — wins on feature-space proximity (0.2468 vs FIL 0.1235, 2× margin) AND liquidity (0.8639 vs FIL 0.7812). ADA's composite 0.5594 vs runner-up FIL 0.5003 = +11.8% margin — decisive ranking.

**Quantitative justification for ADA selection**:
1. **Feature-space proximity dominant (35% weight)**: ADA has the lowest mean z-distance to incumbents (0.6524). The 14 V3_FEATURE_COLUMNS were tuned on BCH/LDO/TRX feature distributions; ADA's feature regime is the closest match in the pool, predicting the trained LightGBM head will TRANSFER best.
2. **Highest liquidity in the candidate pool (15% weight)**: $390.6M avg daily qvol is 3× ATOM and 1.8× FIL. Liquidity matters for live-deployment-compatibility (per BASELINE_V3.md unified architecture goal).
3. **Adequate complementarity (20% weight)**: ADA mean |corr| = 0.4960 — below the 0.70 IC hard gate by 0.20 margin. Lower than FIL/ATOM. Trade-off vs ALGO (0.4920) lost on feature-space proximity (ADA 0.6524 vs ALGO 0.8416).
4. **Data quality 100% PASS**: 37.97mo pre-IS history (well above 24-mo requirement), 100% IS coverage, 0 gap candles.
5. **Trade rate in middle of pool**: 2.13/mo proxy projects to ~30 OOS trades, sufficient for signal evaluation.

### Section 2.7 — T6 Predicted impact

| axis | before | after | delta | interpretation |
|---|---:|---:|---:|---|
| REQUIRED_GAP | 66 | 88 | +22 | +1% per-cell train sample loss (small; far smaller than /068's +3-5% from timeout doubling) |
| n_trials_total | 315 | 420 | +105 | Optuna INDEPENDENT per-symbol; per-symbol budget UNCHANGED at 35 trials × 3 seeds = 105 fits/cell |
| n_symbols | 3 | 4 | +1 | denominator expansion (per `feedback_v3_concentration_is_signal.md` permitted alternative #a) |
| predicted_IS_trades | 159 | [194, 209] | +35 to +50 | from NATR-derived ADA trade-rate proxy (~50 IS trades over 24mo) |
| predicted_OOS_trades | 102 | [122, 132] | +20 to +30 | bundle-level floor 130 may or may not clear at +30 trades (cushion margin = 2 trades) |
| wall_clock_estimate | 0.4-0.7h (/068 ran 0.7h) | 1.5h target | +0.8-1.1h | 4 syms × 3 seeds × 35 trials at single-seed EXPLORATION |
| predicted_IS_Sharpe_PROMISING | +0.83 | [+0.93, +1.10] | +0.10 to +0.27 | 4th symbol contributes IS Sharpe ~+0.3 + dilution effect |
| predicted_IS_Sharpe_NEGATIVE | +0.83 | [+0.33, +0.63] | -0.20 to -0.50 | 4th symbol drags IS (Optuna doesn't fit at single-seed) — per /021 failure mode |
| predicted_OOS_Sharpe_PROMISING | +0.14 | [+0.24, +0.50] | +0.10 to +0.36 | 4th symbol contributes OOS + concentration dilution lifts TRX edge denominator |
| predicted_OOS_Sharpe_NEGATIVE | +0.14 | [-0.36, -0.16] | -0.30 to -0.50 | envelope per Critic /068 Rec #1 widening; 4th sym OOS-negative scenario |

**Reading**:
- Per-cell training-sample loss from REQUIRED_GAP scaling is SMALL (+1%) — much smaller than /068's +3-5% from timeout doubling. The LDO catastrophe at /068 (8.3% WR, 1/12 wins) was attributable to training-sample loss + Optuna re-convergence; at +1% loss, the LDO model has substantially more headroom for similar-quality fit.
- **Critical mechanism note (CORRECTING the iter-v3/021 reasoning)**: Optuna fits INDEPENDENTLY per symbol. Each LightGbmStrategy instance has its own 35-trial × 3-seed budget. Adding a 4th symbol does NOT reduce the per-symbol budget for existing symbols. The /021 brief's reasoning that "5 sym × 35 trials = 175 split 5 ways = 35/sym vs 1500/3 = 500/sym at iter-v3/018 CONFIRMATION" conflated EXPLORATION budget (single-seed) vs CONFIRMATION budget (multi-seed), but the per-symbol per-seed budget is UNCHANGED.
- Bundle-level OOS trades floor 130 (per `feedback_v3_trade_rate_floor_bundle_level.md`) — projected /069 OOS trades [122, 132] BARELY straddles the floor; lower-bound 122 FAILS the floor. PROMISING-AT-EXPLORATION classification will require the upper-bound 132 PASS scenario.
- Predicted Sharpe band widens per Critic /068 Rec #1 mandate. NEGATIVE band reaches -0.50 (matching /021's worst-in-v3-catalog -0.83 historical precedent at 2-symbol expansion; 1-symbol expansion should be less extreme).

## Section 3 — Spec (LOCKED — single-axis variation)

ONE substantive change at /069: **V3_MODELS adds ADAUSDT (4th symbol)**. All other axis settings REVERT to /060 baseline.

Code edits (this brief LOCKS):

1. **`run_baseline_v3.py`**: V3_MODELS expanded 3 → 4:
   ```python
   V3_MODELS: tuple[tuple[str, str], ...] = (
       ("A (BCHUSDT)", "BCHUSDT"),
       ("C (LDOUSDT)", "LDOUSDT"),
       ("D (TRXUSDT)", "TRXUSDT"),
       ("F (ADAUSDT)", "ADAUSDT"),   # iter-v3/069 — 4th symbol; UNIVERSE EXPANSION axis
   )
   ```
2. **`src/crypto_trade/strategies/ml/validation_v3.py`**: REQUIRED_GAP scaled 129 → **88** = (21+1)×4 (timeout REVERT 42 → 21; n_symbols 3 → 4).
3. **`run_baseline_v3.py:1417`**: `label_timeout_minutes=20160` REVERTED to `label_timeout_minutes=10080` (10080 min = 21 candles at 8h).
4. **`run_baseline_v3.py:128`**: ITERATION_LABEL bumped to `"v3-069"`.
5. **`run_baseline_v3.py:721-738`**: /068 runtime assertion block REVERTED — expected_label_timeout updated 20160 → 10080.

Cross-iteration carry-over (NOT changes — REVERSIONS already in /068 anchor state):
- ATR multipliers REMAIN at default (2.0, 1.0) — already reverted at /066/067/068
- V3_FEATURES_PER_SYMBOL REMAINS empty dict {} — already reverted at /051 SYSTEM-LEVEL REVERT
- V3_ATR_MULTIPLIERS_PER_SYMBOL REMAINS empty dict {} — already reverted at /051
- vol_scale_ceiling REMAINS at default 1.0 — already reverted at /067/068
- inference_threshold_floor REMAINS at default 0.0 — already reverted at /068
- block_long_for/block_short_for REMAIN empty () — already reverted at /051
- enable_per_symbol_drawdown_brake REMAINS False — already disabled at /054
- adx_threshold_per_symbol REMAINS empty dict {} — already cleared at /050 closeout
- 14 V3_FEATURE_COLUMNS UNCHANGED — local optimum per `feedback_v3_iter064_process_lessons.md` Rule 5

Why this is ONE substantive axis change despite multiple code touches:
- Adding ADA to V3_MODELS is the single conceptual axis (UNIVERSE EXPANSION 3→4).
- REQUIRED_GAP scaling (66 → 88) is the FORMULA consequence of n_symbols change (validation_v3.py REQUIRED_GAP = (timeout_candles+1) × n_symbols). NOT an independent axis.
- label_timeout_minutes REVERT 20160 → 10080 is restoring the /060 anchor state (/068 was a temporary axis change that did NOT survive Critic — pre-/068 was 10080). Reverting is the symmetric counterpart to /068's setup commit.
- ITERATION_LABEL is mechanical.

## Section 4 — Falsifier Bands (LOCKED — predicted intervals per Critic /068 Rec #1 widening)

Per Critic /068 Rec #1 (`diary-v3/iteration_v3-068.md` Section 8): "Pre-register magnitude bands wider for labeling-axis EXPLORATIONs. Future labeling-DURATION axes use [-0.50, +0.50] envelope." Universe-expansion axis has similar structural-change risk to labeling — applying the wider envelope here as a forward-discipline measure.

### Section 4.1 — PROMISING-AT-EXPLORATION bands (IF /069 advances to /070 BUNDLE)

Disjunctive OR: any single threshold PASS qualifies as PROMISING:

- **IS Sharpe Δ ≥ +0.10** (vs anchor +0.8325 → ≥ +0.93)
- **OR OOS Sharpe Δ ≥ +0.10** (vs anchor +0.1403 → ≥ +0.24)

(Conjunctive AND for /070 BUNDLE inclusion at QR's Critic discretion; disjunctive OR is the EXPLORATION-promotion threshold per `feedback_v3_cycle1_axis_pass_criteria.md`.)

### Section 4.2 — NEGATIVE bands (closes axis at catalog level)

Disjunctive OR: any single threshold FAIL qualifies as NEGATIVE per Critic /068 Rec #1:

- **IS Sharpe Δ < -0.20** (vs anchor +0.8325 → < +0.63)
- **OR OOS Sharpe Δ < -0.30** (vs anchor +0.1403 → < -0.16)

### Section 4.3 — INERT-AT-EXPLORATION zone

If both IS Sharpe Δ in [-0.20, +0.10] AND OOS Sharpe Δ in [-0.30, +0.10] (excluding NEGATIVE single-gate failures), the verdict is INERT-AT-EXPLORATION. Axis CLOSED (universe expansion as single-symbol-add fails to lift) but residual diagnostic value retained for future architecture.

### Section 4.4 — SUSPICIOUS-OOS-DOMINANT sub-mode (per /065 precedent)

If IS Δ < +0.10 AND OOS Δ ≥ +0.20 (large OOS-only lift while IS near-flat or below anchor), classify as SUSPICIOUS-OOS-DOMINANT (per /065 precedent). This sub-mode can still advance to /070 as a "deferred-validation" candidate (like /065's SL widening); requires QR-Critic adjudication.

### Section 4.5 — Saturation falsifier (per `feedback_axis_saturation_predictor.md`)

Per /021 saturation precedent FIRED at IS trades 311 vs 269 upper bound:

- **IS trade count predicted band**: [194, 209]
  - If observed IS trades > 220 (10% over upper bound): saturation falsifier FIRES; ADA emitted more trades than NATR-proxy predicted — second-order Optuna behavior dominant.
  - If observed IS trades < 175 (10% under lower bound): saturation falsifier FIRES; ADA's per-symbol model fit produced fewer emissions than expected — Optuna confidence threshold filtering too aggressively.

- **OOS trade count predicted band**: [122, 132]
  - If observed OOS trades < 130 AND result is otherwise PROMISING: trade-rate floor BLOCKS bundle inclusion per `feedback_v3_trade_rate_floor_bundle_level.md`. Result reclassified PROMISING-INERT or DEFERRED.

### Section 4.6 — Per-symbol Δ ±2pp WR saturation falsifier (PER-SYMBOL CRITIC /068 REC #3)

The dominant LDO-targeting mechanism of universe expansion is concentration dilution. Specific per-symbol falsifiers:

- **LDO OOS WR Δ** ≥ +2pp (i.e., LDO OOS WR ≥ 20.2% vs anchor 18.2%): GOAL ACHIEVED for the LDO-targeting axis.
- **LDO OOS WR Δ** in [-2pp, +2pp] (i.e., 16.2% to 20.2%): unchanged; concentration dilution is mechanical but didn't restore LDO edge.
- **LDO OOS WR Δ** < -2pp (i.e., LDO OOS WR < 16.2%): WORSENED LDO at /069; the 4th-symbol addition coupled with REQUIRED_GAP +22 caused LDO collapse similar to /068 (8.3% WR). This is the NEGATIVE-LDO-COUPLED sub-mode.

(LDO is the SECOND-largest cycle 1 concern per Critic /068 Rec #3. The other Critic priorities: BCH IS concentration sensitivity per BASELINE_V3.md /059 audit; TRX OOS stability.)

### Section 4.7 — BCH IS concentration sensitivity (per Critic /059 Rec #3 + BASELINE_V3.md audit)

BCH IS concentration at /060 was 176.68% (pct_of_total_pnl); at /059 unified 10-seed it was 95.76% (4-symbol baseline). Cycle 1 priorities mandate every brief's Section 4 projects BCH IS sensitivity.

- **BCH IS WR Δ** ≥ -2pp (i.e., BCH IS WR ≥ 43.2% vs anchor 45.2%): BCH IS stable; concentration dilution mechanical (BCH-share 73/(159+~50) = 35% vs 73/159 = 46% at /060 — 11pp dilution).
- **BCH IS WR Δ** < -5pp (i.e., BCH IS WR < 40.2%): BCH IS damaged; universe expansion may have broken BCH's Optuna fit through portfolio aggregation effects. NEGATIVE-BCH-DAMAGE sub-mode.

## Section 5 — Cross-Axis Orthogonality

Per `feedback_v3_engineered_features_dont_stack.md`: ONE substantive axis at EXPLORATION.

/069 axis = UNIVERSE EXPANSION (denominator change) is structurally distinct from all cycle 1 sibling axes:

- /060 EXPLORATION-mode reference (3 seeds; ENSEMBLE_SIZE=3) — /069 inherits the EXPLORATION mode (same 3 seeds; same ENSEMBLE_SIZE=3)
- /061 TRX vol_scale_floor (per-symbol RiskV2 tune) — REVERTED at /066 universal pivot; UNCHANGED at /069
- /062 DSR_relative recalibration (passive diagnostic; carry to /070) — UNCHANGED at /069
- /063 mass feature expansion 14→46 (FEATURE axis) — REVERTED at /064; 14-feature anchor confirmed local optimum
- /064 single-feature add adx_14 (FEATURE axis) — REVERTED; feature axis CLOSED at single-seed n_trials=35 per Rule 5
- /065 SL widening (TRAIN-TIME MAGNITUDE) — UNCHANGED at default (2.0, 1.0); /065 PROMISING already in /070 bundle
- /066 vol_scale_ceiling 0.8 (INFERENCE-TIME) — UNCHANGED at default 1.0
- /067 inference_threshold_floor 0.6 (INFERENCE-TIME) — UNCHANGED at default 0.0
- /068 label_timeout 21 → 42 (TRAIN-TIME DURATION) — REVERTED at /069 (back to 21)
- **/069 universe 3 → 4 (UNIVERSE DENOMINATOR)** — current axis; no prior cycle 1 axis touches this dimension

Sister to historical /021 (universe 3 → 5 with HBAR+AVAX, NEGATIVE-clean) but distinct in 3 ways:
1. 1-symbol expansion (not 2) per /021 lesson (b)
2. Feature-space-proximity-dominant ranking (not correlation-only) per /021 lesson (a)
3. ADA picked (HBAR/AVAX CLOSED at catalog level) per /021 lesson (c)

## Section 6 — Risk Mitigation

| Risk Category | Threshold (IS-calibrated) | Simulated Historical Effect | Justification |
|---|---|---|---|
| **R1: Consecutive-SL Cooldown** | DISABLED (inherited from /060 anchor) | Per /060 baseline reproduction; no change | No new evidence at /069 |
| **R2: Drawdown Position Scaling** | DISABLED (inherited from /060 anchor) | Per /054 closeout | Stateful primitive deadlock risk |
| **R3: OOD Mahalanobis Gate (v2-7 stack feature z-score)** | Active at zscore_threshold=2.0 (UNCHANGED) | Per /060 anchor; ADA features will pass through SAME gate as BCH/LDO/TRX | UNIVERSAL gate per /046 |
| **R4: Vol Kill-Switch (vol_scale_ceiling)** | At default 1.0 (UNCHANGED) | /066 closed the ceiling axis | No new evidence at /069 |
| **R5: Concentration Cap (universe expansion = orthogonal alternative)** | Denominator-expansion via 4th symbol | LDO IS-share 11/159 = 6.9% → 11/(159+50) = 5.3% (dilution) | THIS iteration; orthogonal mechanism per `feedback_v3_concentration_is_signal.md` |
| **R-NEW: Bundle-level trade-rate floor** | Predicted OOS trades [122, 132] vs floor 130 | Lower-bound 122 = FAIL; upper-bound 132 = +2 cushion | If observed OOS < 130, PROMISING reclassified DEFERRED |
| **R-NEW: BCH IS concentration sensitivity** | BCH IS WR Δ < -5pp triggers NEGATIVE-BCH-DAMAGE sub-mode | Per /059 audit + Critic /059 Rec #3 carry-forward | Required per cycle 1 brief discipline |
| **R-NEW: LDO weakness pattern (Critic /068 Rec #3 binding)** | LDO OOS WR Δ ≥ +2pp = GOAL; < -2pp = NEGATIVE-LDO-COUPLED | Universe expansion dilutes LDO denominator share | 3 consecutive cycle 1 LDO failures |

## Section 7 — Failure-Mode Probability Calibration

Per `feedback_v3_iter064_process_lessons.md` Rule 3: NEGATIVE probability for non-feature single-axis at single-seed n_trials=35 calibrated UP (≥25%). Per Critic /068 Rec #1: labeling-axis widen to [-0.50, +0.50] envelope. Universe expansion is structurally analogous (axis touches per-cell training data + Optuna search space).

Calibration distribution:

| Mode | Probability | Justification |
|---|---:|---|
| **INERT-AT-EXPLORATION** | **45%** | ADA's feature-space proximity is favorable (lowest mean_z_dist 0.6524), but Optuna at n_trials=35 single-seed plus per-symbol independent fit may produce a mediocre ADA head that neither helps nor hurts. Most likely outcome given universe-expansion structural similarity to /021 + UNIVERSAL discipline. |
| **PROMISING-AT-EXPLORATION** | **20%** | If ADA's Optuna fit produces a positive per-symbol Sharpe contribution (~+0.3 to +0.5) AND concentration dilution restores LDO bandwidth, IS and/or OOS Δ may cross the +0.10 threshold. Calibrated 5pp above /068 Path C's 15% PROMISING due to ADA's favorable feature-space proximity (vs /068's structural label-cleanup mechanism). |
| **NEGATIVE-AT-EXPLORATION** | **25%** | Per Critic /068 Rec #1 widening + /021 precedent (universe expansion at single-seed EXPLORATION = -0.83 OOS Sharpe Δ historical worst). ADA's per-symbol Optuna fit at n_trials=35 may produce a degenerate model; the REQUIRED_GAP +22 may degrade training-sample quality slightly; concentration dilution may damage BCH IS aggregate. /021 mode: NEGATIVE-clean. Per /066 Path D + /068 Rec #1 forced-wider envelope. |
| **SUSPICIOUS-OOS-DOMINANT** | **10%** | Per /065 precedent + /026/027 historical SUSPICIOUS-OOS-DOMINANT pattern (single-seed lottery on per-symbol Optuna trajectory). ADA's OOS may show outsize positive while IS regresses, due to single-seed Optuna lottery. Calibrated lower than /068's 10% due to UNIVERSAL discipline + ADA's higher trade count (~30 OOS vs LDO's 11) reducing lottery variance. |

**Σ = 100%**. NEGATIVE at 25% (above Rule 3 minimum 25% — consistent with /021 precedent + Critic /068 Rec #1 wider envelope mandate). PROMISING at 20% (within Rule 3 maximum 25%). INERT at 45% (modal outcome).

## Section 8 — LOCKED PASS/FAIL Criteria (PER CYCLE 1 AXIS-PASS DISCIPLINE)

Per `feedback_v3_cycle1_axis_pass_criteria.md` LOCKED.

### Section 8.1 — Disjunctive-OR PROMISING-AT-EXPLORATION threshold

ADVANCE to /070 BUNDLE if ANY:
- IS Sharpe Δ ≥ +0.10 (vs +0.8325 → ≥ +0.93)
- OR OOS Sharpe Δ ≥ +0.10 (vs +0.1403 → ≥ +0.24)

### Section 8.2 — Conjunctive-AND BUNDLE-INCLUSION threshold (QR-Critic discretion)

Recommend bundle inclusion at /070 only if BOTH:
- IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ +0.10 (both directionally PROMISING)
- AND per-symbol Δ ≥ -2pp WR for each incumbent (BCH/LDO/TRX retention)

### Section 8.3 — DISJUNCTIVE NEGATIVE-CLOSE threshold

CLOSE the axis at catalog level (NEGATIVE) if ANY:
- IS Sharpe Δ < -0.20 (vs +0.8325 → < +0.63)
- OR OOS Sharpe Δ < -0.30 (vs +0.1403 → < -0.16)

### Section 8.4 — INERT-AT-EXPLORATION zone

If neither PROMISING nor NEGATIVE: INERT-AT-EXPLORATION. /069 axis CLOSED; /070 BUNDLE stays at 2 components (/065 SL widening + /062 Path B4 deferred spec).

### Section 8.5 — Trade-rate-floor safety net

If PROMISING per Section 8.1 BUT OOS trades < 130 (bundle-level floor): RECLASSIFY as PROMISING-DEFERRED (cannot bundle at /070 without trade-rate-floor remediation). Per `feedback_v3_trade_rate_floor_bundle_level.md` BINDING.

### Section 8.6 — 4th-symbol minimum trade-rate floor

The 4th symbol (ADA) MUST produce:
- IS trades ≥ 10/month proxy (≥ 24 over 24mo) — per orchestrator dispatch constraint
- OOS trades ≥ 5/month proxy (≥ 14 over 14mo) — per orchestrator dispatch constraint

If ADA's IS trade count < 24 OR OOS trade count < 14, the per-symbol head is non-viable; classify as INERT-PER-SYMBOL (not the same as INERT-AT-EXPLORATION; specifically the 4th-symbol-add failed to contribute meaningful trade volume).

## Section 9 — Library Stack

Per BASELINE_V3.md Reproducibility Stamp (line 130):
- `lightgbm 4.6.0`
- `optuna 4.8.0`
- `numpy 2.2.6`
- `pandas 3.0.0`
- `scikit-learn 1.8.0`
- `scipy 1.17.0`
- `statsmodels 0.14.6`
- `pyarrow 23.0.1`

Python 3.13+; managed via `uv`. No new dependencies introduced at /069. EDA reads CSVs via stdlib + numpy + pandas only.

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md` (LOCKED 2026-05-09): the orchestrator's original pre-EDA dispatch identified UNIVERSE EXPANSION as the axis (per Critic /068 Rec #3 LDO-targeting candidates list). QR's EDA-driven decision on the 4th-symbol identity:

**Orchestrator's pre-EDA pick**: UNIVERSE EXPANSION axis (no specific 4th symbol pre-committed).

**QR's EDA-driven selection (this brief)**:
- **Axis: CONFIRMED UNIVERSE EXPANSION** (per Critic /068 Rec #3 binding + `feedback_v3_concentration_is_signal.md` orthogonal mechanism #a + UNIVERSAL discipline per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`).
- **4th symbol = ADAUSDT** (per EDA-driven composite ranking: feature-space proximity 0.2468 + complementarity 0.5040 + data quality 1.0 + liquidity 0.8639 + trade rate 0.4260 = composite 0.5594, rank 1 of 5 PASSING candidates).
- **NOT HBARUSDT or AVAXUSDT** (CLOSED at catalog level per iter-v3/021 diary lesson (c)).
- **NOT FILUSDT, ATOMUSDT, ALGOUSDT, VETUSDT** (ranked 2-5 by composite; ADA's +11.8% margin is decisive).
- **NOT 2-symbol expansion** (per iter-v3/021 diary lesson (b): "1-symbol expansion at a time to isolate per-symbol contribution"; cleaner single-axis attribution).
- **Critic /068 Rec #1 wider envelope APPLIED** (NEGATIVE band widened to [-0.50, +0.50] per directive).

**Path selection** (between Critic /068 Rec #3 candidate axes):
- Path A: LDO-only feature_columns variation — REJECTED per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` system-level CLOSED axis (per-symbol customizations break IS aggregate at multi-seed; 2-CONFIRMATION confirmed).
- Path B: LDO-only ATR labeling override — REJECTED per same `feedback_v3_per_symbol_lifts_oos_breaks_is.md` rule (per-symbol ATR is a per-symbol customization).
- **Path C: Universe expansion (THIS BRIEF)** — SELECTED per UNIVERSAL discipline + `feedback_v3_concentration_is_signal.md` orthogonal mechanism #a.

**EDA SHA**: `95038dd` (`analysis/iteration_v3-069/universe_expansion_eda.py` + 7 CSV outputs: T0_anchor_values, T1_per_candidate_data_quality, T2_correlation_diversification, T3_feature_space_proximity, T3b_per_symbol_feature_z_means, T4_trade_rate_proxy, T5_composite_ranking, T6_predicted_impact)

**Setup commit SHA**: `cde507b` (this brief was first committed as part of the setup commit; SHA backfilled to brief via follow-up `docs(iter-v3/069): backfill setup commit SHA in brief Section 10` commit)

**Phase 5.5 gate SHA**: (TBD at gate)

**Wall-clock estimate**: ~1.5h (4 syms × 3 seeds × 35 trials × ~9 walk-forward months ≈ 33% scale-up from /068's 0.7h baseline; reservation accounts for ADA feature regeneration first-time cache miss).

**Predicted classification (modal outcome)**: INERT-AT-EXPLORATION (45% probability) with 20% PROMISING-AT-EXPLORATION upside + 25% NEGATIVE downside + 10% SUSPICIOUS-OOS-DOMINANT tail.

If PROMISING-AT-EXPLORATION: /069 joins /070 CONFIRMATION bundle (3 components: /065 SL widening + /062 Path B4 deferred spec + /069 universe expansion +ADA).
If INERT/NEGATIVE: /069 axis CLOSED at catalog level; /070 CONFIRMATION bundle stays at 2 components.

Cycle 1 cadence is COMPLETE after /069 per `feedback_v3_strict_10_to_1_cadence.md` Directive 2.

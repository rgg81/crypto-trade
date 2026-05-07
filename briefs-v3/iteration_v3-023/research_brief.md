# Iteration v3-023 — Research Brief

**Type**: EXPLORATION (cadence #5 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 1 — NEW external-data-source feature family RETEST at higher Optuna budget)** — funding_rate_zscore_30 retest at n_trials=35 to disambiguate iter-v3/019 PROMISING-INERT (n_trials=10) per Critic FINAL `3b3cc41` of iter-v3/022 Recommendation #1)
**Track**: v3 (rigor arm) — twenty-third iteration
**Branch**: `iteration-v3/023` (off `iteration-v3/022` head; brief authored before any setup commit lands)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (PRELIMINARY-VALIDATED through iter-v3/020/021/022)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–022 briefs / engineering reports / Critic FINALs / diaries; iter-v3/019's existing EDA outputs at SHA `95858cb` (cited; no fresh EDA needed because the candidate's IS-only structural attributes — coverage 100%, max |IC| 0.3758, ADF p≈0, rank-IC max 0.0485 — are mechanically unchanged at higher Optuna budget; only the model's ability to surface the feature changes). The retest is a budget-disambiguation experiment on a feature whose IS-only structural attributes are already published.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #5 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW external-data-source feature family RETEST —
                       RE-ADD funding_rate_zscore_30 to V3_FEATURE_COLUMNS
                       (revert 13 → 14) at the new EXPLORATION default
                       n_trials=35 (was iter-v3/019 PROMISING-INERT at
                       n_trials=10).
                       Disable regime gate (was iter-v3/022 axis;
                       enable_regime_gate=False; code stays in repo).
                       Per Critic FINAL Rec #1 of iter-v3/022 (SHA `3b3cc41`).
Cadence: EXPLORATION #5 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 1 (NEW external-data-source feature family RETEST at higher Optuna budget;
               MEDIUM #6 elevated to within-cycle priority HIGH per
               iter-v3/022 closeout)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob (this is a feature-set-revert + Optuna-budget retest, not gate tuning).
NOT a feature-pruning variation. NOT a labeling change. NOT a model architecture change.
NOT a universe-expansion (3-symbol BCH+LDO+TRX UNCHANGED from iter-v3/022).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — RETEST axis (per Critic FINAL `3b3cc41` of iter-v3/022 Recommendation #1 + `feedback_v3_iter019_axis_priorities.md` MEDIUM #6 elevated)**:

After iter-v3/022 EXPLORATION-NEGATIVE clean (TRX/2022-Q4 regime gate axis #4 partial-success: TRX/2022-10 PBO 1.0→0.282 SUCCESS but TRX/2023-01 stuck 0.999; PBO max gate FAILS at 1.0 due to LDO/2026-03 data-scarcity; Critic FINAL SHA `3b3cc41`, diary commit `da7047c`):

- The TRX/2022-Q4 regime gate axis #4 is **PARTIALLY-EFFECTIVE-CLOSED for current 10-EXPLORATION cycle**: the targeted TRX/2022-10 cell improved (1.0→0.282) but TRX/2023-01 didn't generalize at single-seed n_trials=35 budget; CONFIRMATION-mode re-evaluation is properly deferred to iter-v3/029+. The mechanism is structurally promising at the per-cell level but cannot be empirically validated at EXPLORATION single-seed.
- Per Critic FINAL Rec #1 of iter-v3/022: **iter-v3/023 axis = funding_rate_zscore_30 RETEST at n_trials=35**. iter-v3/019 was PROMISING-INERT at n_trials=10 (importance rank 14/14 LDO+TRX+Portfolio; 10/14 BCH); 3.5× more Optuna trials per cell may surface signal if the feature was budget-limited rather than genuinely INERT.
- Per `feedback_v3_iter019_axis_priorities.md` LOCKED MEDIUM #6 (RAISED to within-cycle priority HIGH given iter-v3/021 universe expansion CLOSED + iter-v3/022 regime gate PARTIALLY-EFFECTIVE-CLOSED): retesting funding at the new EXPLORATION default budget is the natural next axis. The feature passes all 5 IS-only EDA gates (coverage 100%, IC redundancy 0.3758 < 0.70 hard, IC strict 0.3758 < 0.50 brief, ADF p≈0, rank-IC max 0.0485) — its candidacy is structurally vetted; only the model's ability to learn it at the new budget is in question.
- Forward priority order from `feedback_v3_iter019_axis_priorities.md`:
  1. ~~HIGH — NEW feature families (iter-v3/019)~~ — closed for cycle as PROMISING-INERT at n_trials=10; **REOPENED FOR RETEST at iter-v3/023 (this iteration)**
  2. ~~HIGH — Concentration architecture sub-axis A (per-symbol cap, iter-v3/020)~~ — CLOSED-mechanism (NEGATIVE clean / PATH C)
  3. ~~HIGH — Concentration architecture sub-axis B (universe expansion, iter-v3/021)~~ — CLOSED-symbols-cycle (NEGATIVE clean)
  4. ~~MEDIUM (ELEVATED) — TRX/2022-Q4 regime gate (iter-v3/022)~~ — PARTIALLY-EFFECTIVE-CLOSED at single-seed; CONFIRMATION-mode deferred
  5. MEDIUM — DSR gate reformulation
  6. **HIGH (ELEVATED from MEDIUM #6) — Funding rate retest at n_trials=35 (iter-v3/023 mandate, this iteration)**
  7. LOW — Knob axes (saturated)

**iter-v3/023 first EXPLORATION axis = HIGH-priority (ELEVATED from MEDIUM #6) — funding_rate_zscore_30 retest at n_trials=35.** Cannot be renegotiated post-hoc per Critic FINAL `3b3cc41` of iter-v3/022 + LOCKED priority order.

**Why the retest matters now (post iter-v3/022 PARTIALLY-EFFECTIVE-CLOSED)**:

- iter-v3/019 ran at the OLD EXPLORATION default n_trials=10 (deprecated in favor of n_trials=35 at iter-v3/020 per `feedback_v3_exploration_n_trials_35.md`). At n_trials=10 × 3 symbols = 30 fits per cell, the LightGBM Optuna TPE sampler does not have sufficient density on a 14-column loss surface to surface a single new feature whose univariate rank-IC is 0.04-0.05.
- At n_trials=35 × 3 symbols = 105 fits per cell, the per-symbol Optuna budget is 3.5× larger. This is the budget-disambiguation experiment: can the funding feature surface at higher budget on the SAME 13-feature stack + same data, or is it genuinely structurally INERT in the LightGBM-on-13-features regime?
- The disambiguation result has **3 forward consequences**:
  - **PATH A (PROMISING)**: rank ≤7 for ≥1 symbol AND IS Sharpe Δ ≥ +0.10 → genuine signal at higher budget; keep funding for CONFIRMATION (iter-v3/029+) bundling consideration.
  - **PATH B (PROMISING-INERT-still)**: rank still 14/14 across all 3 → feature genuinely INERT at the LightGBM-on-13-features regime; close axis permanently for current cycle; future budget-bumps wouldn't help (the feature is informationally orthogonal but unactionable in this regime).
  - **PATH C (NEGATIVE)**: IS Sharpe Δ < -0.10 → feature actively hurts at n_trials=35; suggests it was lottery-helping at n_trials=10 (the +1.16 IS Sharpe at iter-v3/019 was Optuna noise, not edge); permanent close.
- Single-axis discipline preserved: ONE feature added back to V3_FEATURE_COLUMNS (13 → 14, ADD funding_rate_zscore_30); regime gate disabled (was iter-v3/022 axis); ITERATION_LABEL=v3-023; 7-primitive risk gate stack byte-identical to iter-v3/018 anchor (no z=2.0 / ADX=20 / BTC ±15% / ATR 2.0/1.0 changes; per-symbol cap kept disabled).

**Why this disambiguation is inexpensive at iter-v3/023**:

- Funding `funding_v3.py` module + `crypto-trade fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache infrastructure preserved at iter-v3/019 closeout per Critic FINAL Rec #2 zero-revert-cost (verified at iter-v3/023 setup time: cache CSVs exist at `data/funding_rates/{BCH,LDO,TRX,AVAX,HBAR,MKR}USDT.csv`; fetch-funding CLI subcommand operative).
- The SAME 13-feature stack underlies all post-iter-v3/018 EXPLORATIONs (iter-v3/019/020/021/022). Adding back funding_rate_zscore_30 is a single-line revert (V3_FEATURE_COLUMNS_TOP_N comment-out → un-comment).
- Wall-clock impact: +1 feature column at 3-symbol universe × n_trials=35 × ENSEMBLE_SIZE=1 expected to add ~7% to feature-loading time per training fold; total wall-clock predicted 8-15 min (well within 2h cap). iter-v3/019 ran in 6 min at n_trials=10; iter-v3/020/021/022 at n_trials=35 ran 13/23/14 min — n_trials=35 + 1 extra column expected to extend modestly.

After iter-v3/023 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (CLOSED-cycle PROMISING-INERT at n_trials=10) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + **NEW external-data-source feature RETEST at higher Optuna budget × 1** = 15 unique axis representations after iter-v3/023, **first RETEST iteration in v3 catalog** (the budget-disambiguation pattern is a NEW catalog precedent).

---

## Section 1 — Hypothesis

Adding back `funding_rate_zscore_30` (z-score over rolling 30 funding-cycle window of Binance Futures funding rate) as a 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS) — at the new EXPLORATION default n_trials=35 (vs iter-v3/019's n_trials=10) — will produce **importance rank improvement** (predicted ≤7 for ≥ 1 symbol) AND **IS Sharpe Δ ≥ +0.10** if the feature is genuinely informative and was budget-limited at iter-v3/019. The iter-v3/019 INERT pattern (rank 14/14 LDO+TRX+Portfolio; 10/14 BCH) was a single-seed n_trials=10 budget artifact, not a genuine "feature is informationally redundant" signal. Predicted IS Sharpe band [+0.40, +0.70] median +0.50 (anchor +0.38; iter-v3/019 was +1.16 single-seed lottery-overshoot — the +0.78 IS Δ was Optuna noise on a 14-column loss surface at n_trials=10, NOT a feature-driven signal); predicted OOS Sharpe band [+0.45, +0.70] median +0.55 (anchor +0.39).

**Mechanism explanation** (why higher Optuna budget should surface the feature): in iter-v3/019's PROMISING-INERT diagnosis, the LightGBM Optuna TPE sampler at n_trials=10 with 1 outer × 1 inner × 3 symbols = 30 fits per cell did not have sufficient hyperparameter search density to converge on tree splits that use the new 14th feature. The 13 incumbent features have ALREADY been calibrated through iter-v3/007-018 evolution (vwap_dev_50 dropped, tbr_zscore_30 dropped); their loss-surface basins are well-understood by Optuna's TPE prior. A new 14th feature opens a NEW dimension in the loss surface; at low trial budget, Optuna does not explore enough of this new dimension to produce trees that use the feature's split structure productively. At n_trials=35 × 3 symbols = 105 fits per cell, the per-cell budget is 3.5× larger, materially extending Optuna's exploration of the 14-feature loss surface. Per `feedback_v3_exploration_n_trials_35.md`: "EXPLORATION-vs-CONFIRMATION distinction now: ENSEMBLE_SIZE+seeds+colsample, NOT n_trials" — the n_trials=35 default was specifically calibrated to address the NEW-feature-family rank-14/14 INERT pattern from iter-v3/015 + iter-v3/019.

**Why the retest is structurally distinct from iter-v3/019's run**:

The IS-only candidacy attributes are mechanically UNCHANGED at higher budget (the EDA at SHA `95858cb` measured them on raw IS data, not Optuna-fit-conditional):
- Coverage on 24-month IS window: 100% across BCH/LDO/TRX (verified iter-v3/019 EDA section 2.2)
- Max |IC| vs 13 V3_FEATURE_COLUMNS: 0.3758 (TRX vs vwap_dev_20) — well below 0.50 strict brief target and 0.70 hard gate
- ADF p-value on z-scored series: ≈ 0 (structurally stationary by construction)
- Rank-IC vs forward returns: max |0.0485| (TRX 7-bar, mean-reversion direction); 8 of 9 cells negative-direction
- Distribution: heavy-tailed (excess kurt 6-13) with funding-floor-clamp outliers; clip to [-10, 10] for LightGBM training stability

What CHANGES at iter-v3/023 vs iter-v3/019 is the per-cell Optuna budget (105 vs 30 fits) and the PRELIMINARY-VALIDATED n_trials=35 DSR/PSR honest-deflation regime (n_eff=19 across iter-v3/020/021/022 vs iter-v3/019's n_eff=7). The retest therefore tests ONE thing: does the LightGBM-on-13-features model surface the funding signal when given 3.5× more Optuna trials per cell?

**Why iter-v3/019's IS Sharpe +1.16 single-seed should NOT be treated as a true performance baseline**:

iter-v3/019's IS monthly Sharpe +1.156 at single-seed=42 n_trials=10 was +0.78 above iter-v3/018 anchor +0.378 — a +0.78 jump on the SAME 13-feature-stack-PLUS-funding-feature combination. Per iter-v3/019 diary §"What Failed" lesson (b): "The +0.31 IS overshoot above predicted upper bound is the canonical lottery signature." The same lottery-signature was empirically falsified in iter-v3/013's case at iter-v3/018 multi-seed CONFIRMATION (62% IS / 86% OOS reduction). Therefore the iter-v3/023 prediction band [+0.40, +0.70] is anchored against iter-v3/018 multi-seed mean +0.3788 + a modest single-axis lift +0.10 to +0.30, NOT against iter-v3/019 single-seed +1.16. The latter is a known lottery-overshoot at low Optuna budget; the former is honest baseline.

**Direction symmetry**: the funding feature is naturally bipolar (positive z = long-leverage crowding, negative z = short-leverage crowding). Per-symbol architecture means each model's LightGBM tree splits bipolarly without forced sign. The 8-of-9 NEGATIVE-direction rank-IC cells (high funding → low forward return; mean-reversion direction) are CONSISTENT across symbols and horizons — LightGBM trees can learn a uniform threshold for the directional split if Optuna exploration finds the basin.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**EDA reference**: cite iter-v3/019's existing EDA at SHA `95858cb` (analysis/iteration_v3-019/funding_rate_eda.py + outputs). The retest does NOT generate fresh EDA because:
- The candidate's IS-only structural attributes (coverage, IC, ADF, rank-IC, distribution) are mechanically UNCHANGED at higher Optuna budget — they are measured on raw IS data, not on Optuna-fit-conditional data.
- The retest is a budget-disambiguation experiment on a feature whose IS-only attributes are already published in iter-v3/019 brief §2.1-2.7.
- Phase 5.5 reproducibility: brief is committed AFTER iter-v3/019's EDA outputs are referenced (no new EDA artifact required); brief committed before any iter-v3/023 setup commit.

**Inputs read** (IS-only window 2020-01-01 → 2025-03-24, mechanically unchanged at iter-v3/023):
- `data/funding_rates/{BCH,LDO,TRX}USDT.csv` — locally-cached funding rate data fetched from /fapi/v1/fundingRate (cached at iter-v3/019; preserved through iter-v3/020/021/022 zero revert cost; verified extant at iter-v3/023 setup time)
- `data/{BCH,LDO,TRX}USDT/8h.csv` — 8h kline data for close prices and open_time alignment
- `data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet` — for IC orthogonality vs 13 V3_FEATURE_COLUMNS (the parquets currently encode the 13-feature subset; iter-v3/023 setup will trigger parquet regeneration to materialize the 14-column feature set)

### 2.1 Carry-forward EDA evidence from iter-v3/019 SHA `95858cb`

| Gate | iter-v3/019 EDA result | Mechanically unchanged at iter-v3/023? |
|---|---|---|
| Coverage on IS window (3 symbols) | 100% all 3 (BCH 2193/2193, LDO 2193/2193, TRX 2193/2193) | YES — IS-only computation unchanged |
| Max \|IC\| vs 13 V3_FEATURE_COLUMNS (39 pairs) | 0.3758 (TRX vs vwap_dev_20) | YES — Spearman IC on raw IS data |
| ADF p-value on z-scored series | ≈ 0 (structural stationarity by construction) | YES — z-score is rolling mean-zero by construction |
| Rank-IC vs forward returns (max abs across 9 cells) | 0.0485 (TRX 7-bar, NEGATIVE-direction) | YES — Spearman rank-IC on raw IS data |
| Distribution heavy-tailedness | excess kurt 6-13; outliers clipped to [-10, 10] | YES — distribution is data-driven |
| Funding-kline alignment | 100% all 3 symbols (settles at 00/08/16 UTC) | YES — alignment is calendar-determined |

**5 of 5 IS-only gates PASS at iter-v3/023** (carry-forward from iter-v3/019 EDA). The candidate is structurally vetted; only the LightGBM model's ability to surface it at higher Optuna budget is in question.

### 2.2 Why iter-v3/019's PROMISING-INERT classification was budget-limited, not feature-limited

At iter-v3/019's spec (--exploration --seeds 1 --n-trials 10 × 3 symbols = 30 fits per cell × ENSEMBLE_SIZE=1):

| Diagnostic | iter-v3/019 result | At iter-v3/023 n_trials=35? |
|---|---|---|
| Total Optuna trials per cell | 30 | **105** (+250% search coverage) |
| Per-symbol Optuna budget | 10 fits/symbol | **35 fits/symbol** (+250% per-symbol density) |
| n_eff (effective independent trials) | **7** (Optuna saturation pattern) | predicted **19** (consistent with iter-v3/020/021/022 regime; +172%) |
| funding_rate_zscore_30 importance rank | BCH 10/14, LDO 14/14, TRX 14/14, Portfolio 14/14 | predicted improvement: ≥1 symbol rank ≤7 if budget-limited |

The +172% n_eff increase (7 → 19) materially extends the loss-surface exploration density. Per `feedback_v3_exploration_n_trials_35.md`: "EXPLORATION-vs-CONFIRMATION distinction now: ENSEMBLE_SIZE+seeds+colsample, NOT n_trials. Single-seed lottery risk unchanged."

### 2.3 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

The retest re-adds a feature column that LightGBM at higher budget will ATTEMPT to learn (vs iter-v3/019's near-zero learn at n_trials=10). Predicting the IS trade-count change for iter-v3/023 vs iter-v3/018 anchor (3-symbol BCH+LDO+TRX universe; iter-v3/018 anchor IS = 172 multi-seed mean trade count):

**Predicted IS trade count behavioral effect**:

| Scenario | Expected IS trade count | Mechanism |
|---|---:|---|
| Lower bound (axis fully propagated, model uses funding feature in trade-restrictive manner) | ~145 | At higher budget, Optuna may converge on shorter-tree models that gate trades selectively when the new feature drives a new threshold |
| Median (typical NEW-feature behavior at higher budget) | ~175 | Model uses new feature as a partial filter; trade roster shifts ~5-10% from anchor 172 |
| Upper bound (axis added but Optuna trees still largely use existing 13 features) | ~205 | Model includes the feature but it has moderate importance; trade roster ~iter-v3/019's 209 baseline |
| **Saturation falsifier band (per `feedback_axis_saturation_predictor.md` ±25% rule)** | **[129, 215]** | Anchor: iter-v3/018 IS trades 172; band low = 0.75 × 172 = 129; band high = 1.25 × 172 = 215 |

**Important counterfactual**: at iter-v3/019 single-seed=42 n_trials=10, observed IS = 209 (within band, near upper edge). At iter-v3/020/021/022 single-seed=42 n_trials=35 with funding REMOVED (13 columns), observed IS = 200 (BCH 98, LDO 23, TRX 79). At iter-v3/023 single-seed=42 n_trials=35 with funding ADDED BACK (14 columns), the predicted re-distribution: similar to iter-v3/019's 209 if the feature still doesn't surface, OR shifts modestly from the 200-baseline if the feature begins surfacing. Predicted band [145, 205] median 175.

**Falsifier reading**: if observed iter-v3/023 IS trades < 129 OR > 215 (saturation band), the new-feature-axis behavioral effect deviated from prediction — potentially indicating Optuna search-path divergence or feature-redundancy effects.

**SECONDARY behavioral-effect verifier (feature-importance check; primary disambiguation metric)**: if `funding_rate_zscore_30` does NOT appear in the top-7 importance rank for at least 1 of the 3 per-symbol models, the feature is still effectively unused even at higher budget — the iteration confirms PATH B (genuinely INERT in the LightGBM-on-13-features regime). The Engineer's Phase 6 report MUST stamp the feature-importance ranking for `funding_rate_zscore_30` on each per-symbol model (sub-fix verifier #15 below).

### 2.4 PATH-A vs PATH-B vs PATH-C predictor calibration (load-bearing)

At iter-v3/019, the +1.16 IS / +0.785 OOS at single-seed=42 n_trials=10 was a known single-seed-lottery-overshoot (`feedback_v3_single_seed_frozen_baseline.md` extends this to BCH/LDO frozen-baseline pattern at iter-v3/020/021/022; iter-v3/023 is a different per-cell trajectory because n_trials=35 ≠ n_trials=10 changes the Optuna path). The QR's iter-v3/023 prediction does NOT anchor to iter-v3/019's headline metrics; it anchors to:

- iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS (the published BOOTSTRAP baseline)
- The single-axis-add nature of the iteration (1 column added; gates byte-identical to iter-v3/018)
- The iter-v3/015 + iter-v3/019 + post-bootstrap NEW-feature-family axis-category empirical history (2 prior data points, both INERT at n_trials=10; iter-v3/023 is the first NEW-feature-family RETEST data point in v3)

**Pre-committed PATH classification table** (load-bearing for Critic FINAL):

| Critic verdict path | Observed IS Sharpe Δ vs iter-v3/018 multi-seed | Observed importance rank for funding_rate_zscore_30 | Catalog row | Next iteration |
|---|---|---|---|---|
| **PATH A (PROMISING)** | Δ ≥ +0.10 (i.e., observed ≥ +0.4788) | rank ≤7 for ≥ 1 symbol | "Funding feature surfaces at n_trials=35 — genuine signal at higher budget" | Keep funding for CONFIRMATION (iter-v3/029+) bundling consideration |
| **PATH B (PROMISING-INERT-still)** | Δ in [-0.10, +0.10] (i.e., observed in [+0.28, +0.48]) | rank still 14/14 across all 3 OR rank ≤7 fails for ≥ 1 symbol | "Feature still INERT at n_trials=35 — closes the budget-limited hypothesis; permanent INERT for current cycle" | iter-v3/024 = different axis category (DSR gate reformulation OR concentration architecture revisit) |
| **PATH C (NEGATIVE)** | Δ < -0.10 (i.e., observed < +0.2788) | importance non-zero but feature actively hurts the model | "Funding feature actively hurts at n_trials=35 — iter-v3/019's +0.78 IS overshoot was lottery-helping; permanent close" | iter-v3/024 = different axis category |

The PATH classification IS the Critic FINAL outcome; cannot be renegotiated post-hoc per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_promising_mechanical_subtype.md`.

### 2.5 Setup integrity (verified at brief authoring)

- iter-v3/019 EDA outputs at SHA `95858cb` exist in repo and reference 5 IS-only gates pass
- funding `funding_v3.py` module + `crypto-trade fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache infrastructure preserved at iter-v3/019 closeout (verified at iter-v3/023 setup time: `data/funding_rates/{BCH,LDO,TRX,AVAX,HBAR,MKR}USDT.csv` extant; `crypto-trade fetch-funding --help` operative)
- iter-v3/022 head HEAD at brief authoring is `3b3cc41` (Critic FINAL); diary commit `da7047c` already lands on iteration-v3/022 branch; iter-v3/023 brief lands AFTER (Phase 5.5 sequencing)
- Past-only discipline: `compute_funding_rate_zscore` uses `.shift(1)` on rolling stats so bar t z-score uses bars t-30...t-1 only — STRICTLY past-only; mechanically unchanged at iter-v3/023 (same `funding_v3.py` module preserved in repo)

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013, baselined at iter-v3/018; reverted to 3 at iter-v3/022)

| Symbol | iter-v3/022 status | iter-v3/023 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED | UNCHANGED (drop-MKR rule executed at iter-v3/013, retained as baseline universe per BASELINE_V3.md note) |
| HBARUSDT | DROPPED at iter-v3/022 | UNCHANGED (axis CLOSED-symbols-cycle per iter-v3/021 diary) |
| AVAXUSDT | DROPPED at iter-v3/022 | UNCHANGED (axis CLOSED-symbols-cycle per iter-v3/021 diary) |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/022 (current) | iter-v3/023 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — RE-ADD ONE FEATURE (`funding_rate_zscore_30`); 13 → 14 columns

| Feature column | iter-v3/022 (V3_FEATURE_COLUMNS_TOP_N) | iter-v3/023 (V3_FEATURE_COLUMNS_TOP_N + funding) |
|---|---|---|
| max_dd_window_50 | KEEP | UNCHANGED |
| ema_spread_atr_20 | KEEP | UNCHANGED |
| ret_kurt_50 | KEEP | UNCHANGED |
| ret_skew_200 | KEEP | UNCHANGED |
| range_realized_vol_50 | KEEP | UNCHANGED |
| hurst_diff_100_50 | KEEP | UNCHANGED |
| ret_kurt_200 | KEEP | UNCHANGED |
| hurst_100 | KEEP | UNCHANGED |
| btc_ret_14d | KEEP | UNCHANGED |
| ret_skew_50 | KEEP | UNCHANGED |
| vwap_dev_20 | KEEP | UNCHANGED |
| ret_autocorr_lag1_50 | KEEP | UNCHANGED |
| sym_vs_btc_ret_7d | KEEP | UNCHANGED |
| **funding_rate_zscore_30** | (not present) | **RE-ADDED** (the single new column; was at iter-v3/019, dropped at iter-v3/020) |

`len(V3_FEATURE_COLUMNS) == 14` after iter-v3/023. `_verify_feature_columns()` updated to assert `len == 14` and `'funding_rate_zscore_30' in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — REVERT regime gate (was iter-v3/022 axis); ALL OTHER GATES UNCHANGED

| Parameter | iter-v3/022 (current) | iter-v3/023 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| `adx_threshold` | 20.0 | UNCHANGED (iter-v3/013 baseline) |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |
| `enable_per_symbol_cap` | False | UNCHANGED (kept disabled; code preserved at iter-v3/020 zero revert cost) |
| **`enable_regime_gate`** | **True** (iter-v3/022 axis) | **False (REVERT — iter-v3/023 axis is funding-feature retest, not regime gate)** |
| `regime_gate_symbols` | ("TRXUSDT",) | UNCHANGED in code (gate disabled means tuple values inert) |
| `regime_dd_threshold_pct` | 20.0 | UNCHANGED in code (gate disabled means value inert) |
| `regime_vol_zscore_threshold` | 1.5 | UNCHANGED in code (gate disabled means value inert) |

Regime gate code stays in repo (zero revert cost; preserves option for CONFIRMATION-mode re-evaluation per iter-v3/022 diary).

### 3.5 Sub-fix decomposition (6-item)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Re-add `funding_rate_zscore_30` to `V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py` | Un-comment / re-include the feature at the end of `V3_FEATURE_COLUMNS_TOP_N` tuple (was at iter-v3/019, dropped at iter-v3/020 with comment "iter-v3/020: funding_rate_zscore_30 DROPPED"; iter-v3/023 reverts the drop). Total 14 columns. Update the docstring to record the iter-v3/023 history line. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 2 | **Update `_verify_feature_columns()` assertion** in `run_baseline_v3.py` from len==13 to len==14 and assert `'funding_rate_zscore_30' in V3_FEATURE_COLUMNS` | Modify the `if n != 13:` check to `if n != 14:`; update docstring/comments to reflect iter-v3/023 14-column setup; remove the "funding_rate_zscore_30 MUST NOT be present" assertion (re-introduce it as a "MUST be present" assertion). | `python -c "import importlib; import sys; sys.path.insert(0,'.'); m = importlib.import_module('run_baseline_v3'); m._verify_feature_columns()"` exits 0 |
| 3 | **Disable regime gate** in `run_baseline_v3.py` | Change `enable_regime_gate=True` to `enable_regime_gate=False` (revert iter-v3/022 axis). Code in `risk_v3.py` + `risk_v2.py` UNCHANGED (zero revert cost). | `grep -E 'enable_regime_gate=False' run_baseline_v3.py` exits 0 |
| 4 | **Update `ITERATION_LABEL`** from `"v3-022"` to `"v3-023"` in `run_baseline_v3.py:102` | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-023"' run_baseline_v3.py` exits 0 |
| 5 | **Regenerate v3 feature parquets** via `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,MKRUSDT --interval 8h --track v3 --format parquet --workers 4` | Existing CLI command. `add_funding_v3_features` (already in GROUP_REGISTRY since iter-v3/019) will run as part of GROUP_REGISTRY iteration, producing fresh `data/features_v3/*.parquet` with the new 14-column feature set. MKR is regenerated for completeness even though V3_MODELS excludes it. **Pre-flight check**: verify `data/funding_rates/{BCH,LDO,TRX}USDT.csv` extant + non-empty before parquet regen; if not, run `uv run crypto-trade fetch-funding --symbols BCHUSDT,LDOUSDT,TRXUSDT` first. | `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns and df['funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0 (and same check for LDO/TRX) |
| 6 | **Run `--exploration --seeds 1`** on the 3-symbol universe with the 14-feature set (n_trials=35 default) | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1`. Wall-clock target: < 30 min (3-symbol, +1 feature column = +~7% feature-loading), 2h hard cap. | `test -f reports-v3/iteration_v3-023/comparison.csv` |

NO NEW labeling change. NO universe change. NO z-score-gate change. NO BTC-band change. NO ADX change. NO Hurst change. NO low-vol-floor change. NO hit-rate change. The single varied axis vs iter-v3/018 anchor + iter-v3/022 setup is `+funding_rate_zscore_30` in V3_FEATURE_COLUMNS (revert iter-v3/020 drop) AND `enable_regime_gate=False` (revert iter-v3/022 axis). Note: 2 changes vs iter-v3/022 head, but only 1 axis vs iter-v3/018 anchor — the regime-gate revert restores the iter-v3/018 anchor surface; the funding-feature-add IS the iter-v3/023 axis.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 12 verifiers

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **`V3_FEATURE_COLUMNS` contains `funding_rate_zscore_30` at 14 columns** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 2 | **`funding_v3` registered in GROUP_REGISTRY (preserved from iter-v3/019)** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'funding_v3' in GROUP_REGISTRY"` exits 0 |
| 3 | **`fetch-funding` CLI subcommand operative (preserved from iter-v3/019)** | `src/crypto_trade/main.py` | `uv run crypto-trade fetch-funding --help` exits 0 with usage text |
| 4 | **funding rates cached for 3 symbols** | `data/funding_rates/{BCH,LDO,TRX}USDT.csv` | `python -c "from pathlib import Path; assert all((Path(f'data/funding_rates/{s}USDT.csv')).exists() for s in ['BCH','LDO','TRX'])"` exits 0 |
| 5 | **Per-symbol parquet has `funding_rate_zscore_30` with > 95% non-NaN coverage on full series** | `data/features_v3/{BCH,LDO,TRX,MKR}USDT_8h_features.parquet` | `python -c "import pandas as pd; r=[pd.read_parquet(f'data/features_v3/{s}USDT_8h_features.parquet')['funding_rate_zscore_30'].notna().mean() > 0.95 for s in ['BCH','LDO','TRX','MKR']]; assert all(r), r"` exits 0 |
| 6 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 7 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 8 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 9 | **`adx_threshold=20.0` UNCHANGED (iter-v3/013 baseline)** | `run_baseline_v3.py` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 10 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 11 | **`enable_regime_gate=False` (REVERT iter-v3/022 axis)** | `run_baseline_v3.py` | `grep -E 'enable_regime_gate=False' run_baseline_v3.py` exits 0 |
| 12 | **`enable_per_symbol_cap=False` UNCHANGED (kept disabled per iter-v3/020 closeout)** | `run_baseline_v3.py` | `grep -E 'enable_per_symbol_cap=False' run_baseline_v3.py` exits 0 |
| — | **`V3_MODELS` has exactly 3 entries; MKR/HBAR/AVAX NOT present** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3 and 'MKRUSDT' not in {s for _,s in m.V3_MODELS} and 'HBARUSDT' not in {s for _,s in m.V3_MODELS} and 'AVAXUSDT' not in {s for _,s in m.V3_MODELS}"` exits 0 |
| — | **`ITERATION_LABEL` updated to `"v3-023"`** | `run_baseline_v3.py:102` | `grep -E 'ITERATION_LABEL.*=.*"v3-023"' run_baseline_v3.py` exits 0 |
| — | **Sub-fix #6 produces comparison.csv** | runner | `test -f reports-v3/iteration_v3-023/comparison.csv` |
| — | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in band [129, 215] (anchor iter-v3/018 IS trades 172). PLUS SECONDARY VERIFIER: `funding_rate_zscore_30` appears in feature_importance.csv non-zero for at least 1 of 3 per-symbol models. PRIMARY DISAMBIGUATION: rank ≤7 for ≥ 1 symbol. | comparison.csv + feature_importance.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-023/comparison.csv'); n=int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert 129 <= n <= 215, f'IS trades {n} OUTSIDE saturation band [129, 215]'"` exits 0 AND feature-importance non-zero for funding feature on >= 1 of 3 models AND PATH-A/B/C classified per §2.4 |

### 3.7 Inheritance from iter-v3/022

The `iteration-v3/023` branch was branched from `iteration-v3/022` head (HEAD `da7047c` = iter-v3/022 diary commit; or alternatively from `iteration-v3/022` head SHA `3b3cc41` Critic FINAL). Critical inheritance verifiers (run before any code edits in Phase 6):

- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 (BEFORE iter-v3/023 sub-fix #1)
- `grep -E 'enable_regime_gate=True' run_baseline_v3.py` exits 0 (BEFORE iter-v3/023 sub-fix #3)
- `grep -E 'ITERATION_LABEL.*=.*"v3-022"' run_baseline_v3.py` exits 0 (BEFORE sub-fix #4)
- `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'funding_v3' in GROUP_REGISTRY"` exits 0 (preserved from iter-v3/019)
- `uv run crypto-trade fetch-funding --help` exits 0 (preserved from iter-v3/019)
- AFTER iter-v3/023 sub-fix #1: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0
- AFTER iter-v3/023 sub-fix #3: `grep -E 'enable_regime_gate=False' run_baseline_v3.py` exits 0
- AFTER iter-v3/023 sub-fix #5: `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns and df['funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/023 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

Anchor: iter-v3/018 BOOTSTRAP baseline IS Sharpe **+0.3788 (multi-seed mean)** / **+0.4563 (seed 42 single)**. iter-v3/023 runs at `--seeds 1 --n-trials 35` (EXPLORATION mode, post-iter-v3/020 default), so the closest-comparable single-seed metrics are:
- iter-v3/020 (cap-on, funding-off, single-seed=42, n_trials=35): IS +0.2745
- iter-v3/021 (cap-off, +HBAR+AVAX, single-seed=42, n_trials=35): IS +0.3183
- iter-v3/022 (regime-on, single-seed=42, n_trials=35): IS +0.8084 (TRX-driven artifact, BCH/LDO frozen)
- **iter-v3/019 (cap-off, regime-off, +funding, single-seed=42, n_trials=10): IS +1.156** (lottery-overshoot at low budget)

The iter-v3/019 +1.156 is NOT the right anchor (lottery-suspect at n_trials=10 per `feedback_v3_single_seed_frozen_baseline.md` + iter-v3/019 diary lesson (b)). The right anchor is iter-v3/018 multi-seed mean +0.3788.

| Metric | iter-v3/018 (anchor multi-seed) | iter-v3/018 (anchor seed-42 single) | iter-v3/023 prediction (3-symbol, 14-feature, +funding @ n_trials=35) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.4563 | **predicted [+0.40, +0.70] (median +0.50)** = Δ vs multi-seed anchor [+0.02, +0.32] (median +0.12) |
| IS trades | 172 (multi-seed mean cumul) | 172 (seed 42) | **predicted [129, 215]** (saturation band ±25%); inner band [145, 205] median 175 |
| OOS trades | 90.5 (mean) / 102 (seed 42) | 102 (seed 42) | **informational ~75-130** |
| OOS Sharpe | +0.3869 (mean) / +0.2343 (seed 42) | +0.2343 | **informational; predicted [+0.45, +0.70] median +0.55** if PATH A; predicted [+0.20, +0.50] if PATH B; predicted [-0.50, +0.10] if PATH C |
| Phase 6 wall-clock | 4.54h | (CONFIRMATION mode) | predicted 8-15 min (3 symbols, 14-column feature set; n_trials=35 default), hard cap 2h |

The IS prediction band [+0.40, +0.70] (Δ over multi-seed anchor +0.12 median) is calibrated against:
- iter-v3/018 anchor +0.3788 multi-seed mean
- The single-axis-add nature of the iteration (1 column added; gates byte-identical)
- The empirical NEW-feature-family axis-category history at n_trials=10 (iter-v3/015 INERT + iter-v3/019 INERT) — both at OLD budget; iter-v3/023 is the first NEW-feature-family RETEST data point at n_trials=35
- Median +0.50 sits modestly above iter-v3/018 anchor +0.38 by +0.12 — consistent with PATH A "feature surfaces at higher budget; modest IS lift"; the upper bound +0.70 absorbs higher-than-expected single-seed Optuna variance (NOT another lottery-overshoot — iter-v3/019's +1.16 is an outlier, not a baseline reference)

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < iter-v3/018 multi-seed anchor +0.3788 - 0.10 = +0.2788 → the new feature actively hurt the model OR the axis didn't propagate. Verdict: **PATH C (NEGATIVE)** on feature-family-retest-axis (clean). Catalog row marks NO candidate; iter-v3/024 explores a different axis.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count outside [129, 215] (= [0.75 × 172, 1.25 × 172]) → axis behavioral effect deviates from prediction. If trades < 129 (>-25% reduction): the new feature is heavily restricting trade entries. If trades > 215 (>+25% expansion): the new feature is loosening trade entries OR the axis didn't propagate (V3_FEATURE_COLUMNS reassignment didn't make it to LightGBM). Verdict path: BLOCK if axis didn't propagate (verified via Falsifier 4); otherwise PATH-classification per §2.4.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe with 14-feature set → unexpected slowdown in feature-loading or parquet regen pipeline. Engineer documents the cause.

**Falsifier 4 (PRIMARY for budget-disambiguation; iter-v3/019 INERT precedent)**: `funding_rate_zscore_30` rank 14/14 across all 3 per-symbol models (or rank ≤7 fails for ≥ 1 symbol) → at higher budget, the model still does not surface the feature; the iteration confirms PATH B (genuinely INERT in the LightGBM-on-13-features regime). Verdict: **PATH B (PROMISING-INERT-still)**. Catalog row marks NO candidate; axis CLOSED permanently for current cycle.

**Falsifier 5 (PATH A indicator)**: rank ≤7 for ≥ 1 symbol AND IS Sharpe Δ ≥ +0.10 → genuine signal at higher budget; **PATH A (PROMISING)**. Catalog row marks YES candidate (compoundable as a feature ingredient at iter-v3/029+ CONFIRMATION bundling).

**Process falsifier**: pre-flight `grep funding_rate_zscore_30 src/crypto_trade/features_v3/__init__.py` exits non-zero (after sub-fix #1), OR `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns"` exits non-zero (after sub-fix #5), OR `data/funding_rates/<SYM>.csv` not present → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

Per `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md` + iter-v3/015-022 precedent. §2.4 PATH-A/B/C classification table is the load-bearing decision rubric.

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| **PATH A (`EXPLORATION-PROMISING`)** | IS Sharpe Δ ≥ +0.10 vs iter-v3/018 multi-seed anchor (i.e., ≥ +0.4788) AND broad-based per-symbol AND IS trades in [129, 215] (Falsifier 2 PASS) AND `funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol (Falsifier 5 PASS) | "Funding-rate retest at n_trials=35 surfaces the feature — genuine signal at higher budget; budget-limited at iter-v3/019 confirmed" | iter-v3/024 EXPLORATION on a DIFFERENT axis category (DSR gate reformulation, OR a new MEDIUM/HIGH axis from `feedback_v3_iter019_axis_priorities.md`) — single-axis discipline + axis-category-rotation discipline |
| **PATH B (`EXPLORATION-PROMISING-INERT-still`)** | IS Sharpe within ±0.10 of iter-v3/018 multi-seed anchor (i.e., in [+0.28, +0.48]) AND IS trades in [129, 215] AND rank still 14/14 across all 3 OR rank ≤7 fails for ≥ 1 symbol | "Funding feature still INERT at n_trials=35 — closes the budget-limited hypothesis; permanent INERT for current cycle" | iter-v3/024 EXPLORATION on a DIFFERENT axis category — should NOT be another funding-related variant; consider DSR gate reformulation OR a structurally-different feature family |
| **PATH C (`EXPLORATION-NEGATIVE`)** | IS Sharpe Δ < -0.10 vs iter-v3/018 multi-seed anchor i.e. < +0.2788 AND non-bit-identical roster AND `funding_rate_zscore_30` IS in feature importance (Falsifier 5 PASS) → the model used the new feature but it actively hurt | "Funding feature actively hurts at n_trials=35 — iter-v3/019's +0.78 IS overshoot was lottery-helping; permanent close" | iter-v3/024 EXPLORATION on a DIFFERENT axis category — NOT another funding variant |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT; UNLIKELY at +1 feature add but flagged for completeness) | IS Sharpe direction wrong AND `funding_rate_zscore_30` importance == 0 across all 3 models (Falsifier 4 fires) AND trade roster bit-identical to iter-v3/018 (UNLIKELY for new-feature axis given non-trivial rank-IC) | "Model ignored the new feature; trade roster unchanged" | iter-v3/024 EXPLORATION on a DIFFERENT axis category |
| `EXPLORATION-PROMISING-MECHANICAL` (UNLIKELY for new-feature axis given non-trivial rank-IC; flagged for completeness) | IS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/018 — UNLIKELY for new-feature axis given non-trivial rank-IC | "New feature added without behavioral change — accounting drift" | similar to iter-v3/013 framing |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades outside [129, 215]) AND axis didn't propagate (Falsifier 4 fires), OR Falsifier 3 (wall-clock) triggered | (none) | Diary documents, iter-v3/024 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 inherited + 4 methodology-specific = 8 total)

iter-v3/023 inherits the cadence-discipline safeguards from skill SHA + the saturation-predictor rule + the structural-axis preference rule + `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_single_seed_frozen_baseline.md` LOCKED:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. Wall-clock target < 30 min for 3-symbol + 14-feature `--exploration` mode.
2. **Single-axis variation rule** honored: only `+funding_rate_zscore_30` re-added to V3_FEATURE_COLUMNS + regime-gate disabled (`enable_regime_gate=False` revert). Vs iter-v3/018 anchor: 1 axis (feature add); vs iter-v3/022 head: 2 changes but the regime-gate revert restores anchor surface, so the single axis vs iter-v3/018 anchor is the feature add. ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/CPCV byte-for-byte identical to iter-v3/018; per-symbol cap kept disabled; no other gate threshold tuning; no universe change; no labeling change; no model architecture change.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PATH A / PATH B / PATH C / etc.) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-023.md`.
4. **Saturation predictor falsifier** (Section 3.6 + Section 4.3 Falsifier 2, threshold derived from anchor `iter-v3/018 IS trades = 172` ±25% = [129, 215] per `feedback_axis_saturation_predictor.md`) actively verifies that the new feature axis propagated to the model output AND that behavioral effect is in expected band.

Methodology-specific safeguards (NEW-feature-family RETEST at higher Optuna budget axis):

5. **Feature-importance verifier** (Section 3.6 + Section 4.3 Falsifier 4 + Falsifier 5; PRIMARY disambiguation metric): `funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol distinguishes "model surfaces the feature at higher budget (PATH A)" from "model still ignores the feature at higher budget (PATH B INERT)". Distinguishes from iter-v3/019's rank 14/14 LDO+TRX+Portfolio + 10/14 BCH INERT pattern.
6. **EDA gate carry-forward from iter-v3/019 SHA `95858cb`** (Section 2.1): coverage 100%; IC redundancy 0.3758 < 0.70 hard; IC strict 0.3758 < 0.50 brief; ADF p≈0; rank-IC max 0.0485. All five IS-only EDA gates passed at iter-v3/019 EDA AND are mechanically unchanged at iter-v3/023 (raw-IS-data-derived). Phase 6 inherits a structurally-tractable candidate.
7. **Past-only computation discipline**: `compute_funding_rate_zscore` uses `.shift(1)` on rolling stats (preserved unchanged from iter-v3/019). Funding rate AT bar t is the rate that just SETTLED at the candle open, knowable from the previous 8h period close. Mechanically unchanged at iter-v3/023.
8. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-022)

1. **Adversarial unit tests** must PASS before backtest: `tests/strategies/ml/` 26 tests (regime gate tests at iter-v3/022 must STILL pass even though gate disabled — code remains in repo).
2. **File-artifact reconciliation table** (§3.6). 12 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-checks**: `funding_rate_zscore_30` in V3_FEATURE_COLUMNS, parquet has `funding_rate_zscore_30` column, funding-rate cache present at `data/funding_rates/<sym>.csv`. Catches the case where setup edits were silently lost or feature regen was skipped.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 RETEST-axis-specific risks (3 explicit)

1. **Funding feature still INERT at higher budget (PATH B)**: rank 14/14 across all 3 symbols at n_trials=35 would close the budget-limited hypothesis permanently. **Mitigation**: PATH-A vs PATH-B vs PATH-C is THE point of the iteration — all three outcomes are pre-committed in §2.4 + §4.4. Whatever the outcome, the catalog row records the disambiguation result; iter-v3/024 advances to a different axis.
2. **iter-v3/019's IS Sharpe +1.156 was lottery-helping, not budget-limited (PATH C)**: at n_trials=35, the feature actively hurts because the lottery-path that surfaced +1.156 at n_trials=10 was an Optuna search-path that overfit on the funding feature in some specific regime, and the higher-budget search converges away from that overfit point. **Mitigation**: PATH C captured in §2.4 + §4.4; clean classification + permanent close.
3. **Frozen-baseline pattern propagates BCH/LDO from iter-v3/020/021/022 to iter-v3/023**: per `feedback_v3_single_seed_frozen_baseline.md`, single-seed=42 BCH/LDO Optuna trajectories are deterministic at the SAME n_trials=35 budget. With +1 feature column at iter-v3/023, the loss surface dimensionality changes — BCH/LDO trajectories MAY shift modestly (n_trials=35 search density on 14 columns ≠ 13 columns) but are NOT GUARANTEED to shift. **Mitigation**: bit-identity check vs iter-v3/020/021/022 in engineering report (verify whether +1 column changes BCH/LDO trajectories or whether frozen-baseline pattern persists). The SAME n_trials applied to a +1-column loss surface is a measurably different Optuna trajectory; whether that materializes as different trade rosters is empirical, NOT pre-committable.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED (single-feature-axis variation; gates byte-identical to iter-v3/018; regime-gate disabled to revert iter-v3/022 axis)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, 14-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX ≥ 20 (iter-v3/013 baseline) | ≈ 60% of bars pass | Trend filter |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over **14** features now — slightly higher kill rate due to one more column for OOD computation) | ≈ 26–37% killed (was ~25-35% with 13 cols; minor uplift expected) | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited iter-v3/012) | Macro flips |

Combined kill rate target: **80–90%** (matches iter-v3/018's range; z-score OOD over 14 cols may slightly tighten). The only primitive whose computation changes is primitive 4 (z-score OOD now over 14 features instead of 13); all others' specs are byte-identical to iter-v3/018.

**Important sub-point**: the new `funding_rate_zscore_30` becomes one of the 14 columns the z-score OOD primitive computes the per-bar kill on. In stress regimes where funding rate spikes (|z| > 2.0), the OOD gate will kill the bar's signal — this is intentional defensive behavior consistent with the existing OOD gate's design (iter-v3/011 z-score 2.0). The funding feature's heavy-tailed distribution (clipped to [-10, 10] in compute_funding_rate_zscore) means OOD kills will fire more aggressively in funding-stress regimes (e.g., BTC liquidation cascades where funding hits +0.005 per cycle). This is RISK-AWARE behavior, not an over-restriction.

**Regime gate (primitive 9 in iter-v3/022)**: DISABLED at iter-v3/023 (`enable_regime_gate=False`). Code stays in repo. Not in active gate stack for iter-v3/023.

**Per-symbol cap (primitive 8 in iter-v3/020)**: DISABLED (kept disabled per iter-v3/020 closeout). Code stays in repo.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent. Adding `funding_rate_zscore_30` to V3_FEATURE_COLUMNS expands primitive 4's z-score OOD computation to 14 features; the other 6 primitives are unaffected.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/018. Regime coverage includes 2023 banking crisis (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction. The 3-symbol portfolio's exposure to these regimes is broadly similar; the new funding-rate feature provides additional regime-classification dimension (high-carry vs low-carry vs negative-carry regimes) WITHIN each of these macro periods. (Mechanically unchanged from iter-v3/019 brief.)

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/018 multi-seed showed TRX 66.08% / 55.83% concentration (gate 7 floor 30% missed). iter-v3/023 OOS concentration may shift either direction depending on whether funding feature reshapes per-symbol trade frequencies. Per `feedback_v3_iter019_axis_priorities.md` + `feedback_v3_concentration_is_signal.md`, concentration architecture is a separate axis category; this iteration does NOT pre-register a concentration falsifier.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 12 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/019 INERT precedent)

**Prediction P1 (process, P=10%)**: `funding_rate_zscore_30` column not added to V3_FEATURE_COLUMNS or not propagated to the LightGBM strategy's `feature_columns` argument. Engineer's V3_FEATURE_COLUMNS_TOP_N edit lands but a path-resolution issue in `LightGbmStrategy(feature_columns=list(V3_FEATURE_COLUMNS))` causes runtime to use a stale column list. **Detection signal**: Falsifier 4 (feature-importance check) shows funding feature with importance 0 across all 3 models OR Falsifier 2 (saturation predictor) fires (IS trades outside [129, 215]). **Mitigation**: §3.6 rows 1, 5, 12 verifiers (3 independent signals).

**Prediction P2 (process, P=10%)**: parquet regeneration fails or produces stale parquets (funding_rate_zscore_30 missing or NaN). Most likely cause: `add_funding_v3_features` not called via the v3 features CLI (or called on cached pre-feature data without reading the funding_rates/<sym>.csv). **Detection signal**: §3.6 row 5 verifier fails — `pd.read_parquet(...)['funding_rate_zscore_30'].notna().mean() > 0.95` returns False. **Mitigation**: pre-flight verifier blocks Phase 6 launch.

**Prediction P3 (process, P=5%)**: wall-clock overshoots the 30-min target due to feature-set expansion (14 cols vs 13 = ~7% more loading per training fold). 3-symbol universe with 14-feature set should run in 8-15 min; cold-start funding cache already populated (preserved from iter-v3/019). **Detection signal**: engineering report wall-clock minutes. **Mitigation**: 2h hard cap by skill spec.

**Prediction P4 (model, P=35%)** = **PATH A (PROMISING)**: rank ≤7 for ≥ 1 symbol AND IS Sharpe Δ ≥ +0.10. The new funding-rate z-score gives the model a derivatives-positioning regime-classifier signal that complements the existing 13-feature set; at n_trials=35 budget, Optuna explores enough of the 14-column loss surface to surface the feature via tree splits. The 8-of-9 NEGATIVE-direction rank-IC cells signal a coherent mean-reversion edge across the 3 symbols.

**Prediction P5 (model, P=40%)** = **PATH B (PROMISING-INERT-still)**: IS Sharpe stays in iter-v3/018 multi-seed anchor range [+0.28, +0.48]; the new funding z-score is included in the model but its information overlap with existing features (max |IC| 0.3758 with vwap_dev_20) is enough that the model's tree splits substitute funding for vwap_dev_20 in some contexts without net Sharpe lift. Even at higher budget, the feature does not surface to top-7 importance because the 13-feature stack has been calibrated through iter-v3/007-018 evolution and exploits the same volume-imbalance information channel via vwap_dev_20.

**Prediction P6 (model, P=20%)** = **PATH C (NEGATIVE)**: IS Sharpe drops below iter-v3/018 multi-seed anchor (-0.10 → < +0.28); the new funding feature introduces noise that the model overfits on at higher budget, producing tree splits that select for the wrong direction. iter-v3/019's +1.156 was Optuna-path lottery; iter-v3/023 lands in a different Optuna basin that doesn't replicate the lottery-helpful structure.

P4 + P5 + P6 sum to 95% (PATH-classification outcome). Process predictions P1-P3 sum to 25% (failure-mode hedging). The iteration's primary purpose is the disambiguation result — all 3 outcomes (PATH A/B/C) carry forward distinct catalog implications + memory rules.

**Calibration vs prior EXPLORATIONs**:
- 3 NEW-feature-family axis-category data points exist in v3: iter-v3/015 (microstructure tbr_zscore_30 INERT @ n_trials=10), iter-v3/019 (funding_rate_zscore_30 INERT @ n_trials=10), AND iter-v3/023 (funding_rate_zscore_30 RETEST @ n_trials=35) — first RETEST data point.
- The PATH-B prediction (P=40%) reflects a Bayesian update against the prior INERT pattern: 2-of-2 NEW-feature-family axes at n_trials=10 were INERT, suggesting a non-trivial structural-INERT prior. The retest at higher budget is the disambiguation experiment.
- The PATH-A prediction (P=35%) reflects the n_trials=35 EXPLORATION default's PRELIMINARY-VALIDATED status (3 iterations of consistent honest-deflation regime; n_eff=19 vs n_eff=7 at n_trials=10) — the higher budget is empirically materially better than the lower one.
- The PATH-C prediction (P=20%) reflects iter-v3/019's IS overshoot lottery-suspect signature: if the +1.156 IS at n_trials=10 was lottery-helping (not edge-helping), then n_trials=35 should produce neutral or slightly negative IS (the 0.20 spread between PATH-B and PATH-C).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 12 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 12 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers (per skill spec + `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md` + `feedback_v3_single_seed_frozen_baseline.md`).

1. **IS Sharpe ≥ iter-v3/018 multi-seed anchor + 0.10 (i.e., ≥ +0.4788)**: catalog row records PATH A verdict on numerical-axis basis.
2. **IS Sharpe < iter-v3/018 multi-seed anchor - 0.10 (i.e., < +0.2788)**: PATH C verdict (active drag).
3. **IS Sharpe in [+0.2788, +0.4788]**: PATH B (INERT-still) verdict — neither active drag nor active surfacing.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level.md` (informational at EXPLORATION; predicted IS in [129, 215]; OOS predicted ~75-130 — ≥50). Bundle (5 outer × 3-4× ensemble) at CONFIRMATION will multiply this 3-4×.
5. **PBO < 0.40 (per-cell mean) AND `n_high_pbo_cells_99 ≤ 4`**: methodology hygiene; both inherited unchanged from iter-v3/018 multi-seed (mean 0.0892; max 1.0 on TRX/2022-Q4 carry-forward — outstanding constraint flagged in BASELINE_V3.md but NOT iter-v3/023's axis to fix). iter-v3/023 expected near-identical PBO unless new feature has unexpected cell-level effect.
6. **IC max abs < 0.70**: per Critic Check 4 — the new feature `funding_rate_zscore_30` has max |IC| 0.3758 vs the existing 13 (verified at iter-v3/019 SHA `95858cb`); the existing 13-feature pairwise max was 0.685; **after-add expected max |IC| in the 14-feature pairwise matrix remains 0.685** (the new column doesn't create a NEW pair above 0.685 since its max IC is 0.3758, well below 0.685 — IC ceiling unchanged at iter-v3/018's 0.685).
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS** (or stationarity rationale per Section 4 precedent): the 13 inherited features unchanged; the new `funding_rate_zscore_30` is a z-score (rolling-window mean-zero by construction) — ADF p-value is structurally near-zero on z-scored series. Engineer's Phase 6 ADF test will confirm.
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis carry-forward iter-v3/019 SHA `95858cb`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-022).
10. **Symbol exclusion + feature isolation**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `features_v3` does not import `features` (v1) or `features_v2` (v2). The funding_v3.py module lives in `features_v3/` (track-isolated); zero new imports from v1/v2.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in **[129, 215]** (= anchor iter-v3/018 IS trades 172 ± 25%). The threshold is DERIVED from §2.3's anchor; not a hardcoded constant.
12. **PRIMARY DISAMBIGUATION VERIFIER (Falsifier 5 / PATH-A predictor)**: `funding_rate_zscore_30` rank ≤7 for ≥ 1 symbol AND non-zero importance for ≥ 1 of 3 models. Critic uses BOTH signals to disambiguate PATH A from PATH B from PATH C: PATH A = rank ≤7 ≥ 1 sym AND IS Δ ≥ +0.10; PATH B = rank still 14/14 OR rank ≤7 fails for ≥ 1 sym (regardless of IS Δ); PATH C = IS Δ < -0.10. Predicted disambiguation: PATH A 35%, PATH B 40%, PATH C 20% per §7.

**Catalog-axis verdicts** map to §4.4 PATH-classification table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-022** — no version bumps in iter-v3/023:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0 (or recent compatible; iter-v3/022 stamp shows 3.0.0)
scikit-learn = 1.8.0 (pinned >=1.8,<1.9 per iter-v3/020 sklearn pin)
pyarrow = 23.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.6 (adfuller for ADF stationarity)
optuna = 4.8.0
scipy = 1.17.0
httpx = (already used for kline fetcher; reused for funding-rate fetcher)
```

**No package additions or version bumps.** All infrastructure (`compute_funding_rate_zscore` in `funding_v3.py`, `fetch-funding` CLI subcommand, `data/funding_rates/<sym>.csv` cache, `add_funding_v3_features` in GROUP_REGISTRY) preserved from iter-v3/019 zero-revert-cost decision.

---

## Section 10 — Adversarial Tests (preserved from iter-v3/019; one carry-forward expected)

Adversarial test suite at `tests/strategies/ml/` is unchanged. The Engineer should verify `tests/features_v3/test_funding_v3.py::test_funding_rate_zscore_past_only` (or equivalent test name from iter-v3/019) passes alongside the 7 regime-gate tests at iter-v3/022 (those tests must STILL pass even though the gate is disabled — code stays in repo). Total expected test count: 26 + however many funding tests landed at iter-v3/019.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/023 catalog row before backtest results are known:

```
| iter-v3/023 | 2026-05-07 | NEW external-data-source feature RETEST: +funding_rate_zscore_30 at n_trials=35 (was iter-v3/019 PROMISING-INERT at n_trials=10; budget-disambiguation experiment) | IS Sharpe Δ TBD vs iter-v3/018 multi-seed +0.3788 | OOS Sharpe TBD (informational) | TBD verdict (PATH A / PATH B / PATH C) | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 PATH-classification + §8 criterion 1-3 + 12. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/023 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_single_seed_frozen_baseline.md` LOCKED):
- If verdict = **PATH A (`EXPLORATION-PROMISING`)**: catalog row marked YES candidate (compoundable as a feature ingredient at iter-v3/029+ CONFIRMATION bundling consideration; first NEW-external-data-source ingredient validated at higher budget).
- If verdict = **PATH B (`EXPLORATION-PROMISING-INERT-still`)**: catalog row marked NO candidate (axis CLOSED permanently for current cycle; budget-limited hypothesis CLOSED — funding feature is structurally INERT in the LightGBM-on-13-features regime).
- If verdict = **PATH C (`EXPLORATION-NEGATIVE`)**: catalog row marked NO; iter-v3/024 explores a DIFFERENT axis category. Per `feedback_v3_iter019_axis_priorities.md`, MEDIUM #5 (DSR gate reformulation) is the natural next axis. NEXT iteration MUST NOT be another funding variant — single-axis discipline + axis-category-rotation discipline.
- If verdict = `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT; UNLIKELY): catalog row marked NO; iter-v3/024 explores a DIFFERENT axis category.

**Catalog count after iter-v3/023**: 5 of 10 EXPLORATIONs in the post-bootstrap cycle; **5 more required** before any CONFIRMATION can launch (earliest = iter-v3/029). Axis coverage after iter-v3/023: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (CLOSED-cycle PROMISING-INERT at n_trials=10) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + NEW regime-conditional gate primitive × 1 (PARTIALLY-EFFECTIVE-CLOSED) + **NEW external-data-source feature RETEST at higher Optuna budget × 1** = 15 unique axis representations after iter-v3/023.

**Forward axis pipeline** (iter-v3/024-028 candidates pre-pre-committed for QR continuity, NOT mandates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order):
- iter-v3/024 candidates: depend on iter-v3/023 PATH-A/B/C outcome:
  - PATH A: iter-v3/024 = different axis category (DSR gate reformulation OR a new structural axis); funding feature kept in V3_FEATURE_COLUMNS for compounding consideration at iter-v3/029+ CONFIRMATION
  - PATH B/C: iter-v3/024 = DSR gate reformulation (MEDIUM #5 natural next axis)
- iter-v3/025-028 candidates: depend on accumulated evidence; further NEW feature families (Open Interest delta, basis spread, on-chain proxies — each requires its own external data source) only if a fetch+regen workflow is well-established post-iter-v3/019 (verified YES); else MEDIUM priority axes (DSR gate reformulation)

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (5 of 10 in post-bootstrap cycle); STRUCTURAL axis declared (NEW external-data-source feature family RETEST); explicit "NOT a gate-threshold knob"; references Critic FINAL `3b3cc41` of iter-v3/022 + `feedback_v3_iter019_axis_priorities.md` LOCKED MEDIUM #6 elevated.
- [x] §1 Hypothesis with locked numerical bands + mechanism + lottery-overshoot caveat.
- [x] §2 IS-only numerical evidence carry-forward from iter-v3/019 SHA `95858cb`; no fresh EDA needed (mechanically unchanged at higher budget); behavioral-effect predictor with saturation falsifier band [129, 215]; PATH-A/B/C pre-classification table.
- [x] §3 6-sub-fix decomposition + 12-row Brief-vs-Code reconciliation table + iter-v3/022 inheritance verifiers.
- [x] §4 EXPLORATION outcome interpretation table mapped to PATH-A/B/C; falsifiers locked before backtest; PATH-A indicator (Falsifier 5) + PATH-B indicator (Falsifier 4) + PATH-C indicator (Falsifier 1).
- [x] §5 Risk Mitigation: 4 cadence-discipline + 4 methodology-specific = 8 total safeguards; 3 RETEST-axis-specific risks.
- [x] §6 Risk Management Design: 7-primitive table UNCHANGED; regime gate disabled (revert iter-v3/022 axis); per-symbol cap kept disabled.
- [x] §7 Pre-Registered Failure-Mode Prediction: 6 predictions calibrated against iter-v3/015 + iter-v3/019 INERT precedents + n_trials=35 PRELIMINARY-VALIDATED status.
- [x] §8 12 EXPLORATION criteria with PATH-classification + PRIMARY DISAMBIGUATION VERIFIER (Falsifier 5 + Falsifier 4).
- [x] §9 Library Stack Declaration UNCHANGED (no version bumps).
- [x] §10 Adversarial Tests preserved (regime gate tests + funding tests both must pass).
- [x] §11 Catalog Row Pre-Commit + Forward axis pipeline.

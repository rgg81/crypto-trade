# Iteration iter-v3/019 — Diary

## Decision: EXPLORATION-PROMISING-INERT

NOT clean-PROMISING. Falsifier 4 fires (`funding_rate_zscore_30` importance rank 14/14 across LDO + TRX + Portfolio aggregations; 10/14 on BCH). The model demonstrably did not learn the funding-rate signal at the n_trials=10 single-seed EXPLORATION budget. The IS Sharpe lift is real in the run but is attributable to hyperparameter / colsample noise on a 14-column loss surface, NOT to the funding-rate feature itself — the same INERT pattern as iter-v3/015's microstructure precedent.

NOT a CONFIRMATION-bundle candidate. Funding-rate axis is CLOSED for the current 10-EXPLORATION cycle (iter-v3/019–028). A funding-rate retest at higher trial budget is properly deferred to iter-v3/028+ CONFIRMATION when multiple HIGH-priority axes have accumulated PROMISING evidence. Cannot be renegotiated post-hoc.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `funding_rate_zscore_30` (z-score over rolling 30 funding-cycle window of Binance Futures funding rate) as a 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline will produce IS Sharpe lift of +0.20 (median) over the iter-v3/018 anchor +0.3788 (predicted IS Sharpe band [+0.45, +0.85]) by giving the LightGBM model a derivatives-market-positioning regime-classifier signal — funding-rate z-score captures persistent leveraged-long/short positioning crowding, structurally orthogonal to the existing 13 features (max |IC| = 0.3758 with vwap_dev_20)."

**Spec (locked, single-axis variation):**
- V3_FEATURE_COLUMNS 13 → 14 (`funding_rate_zscore_30` added; computed in new `funding_v3.py` module via past-only rolling z-score on Binance `/fapi/v1/fundingRate` API)
- New `crypto-trade fetch-funding` CLI subcommand + `data/funding_rates/<sym>.csv` cache
- Ran in EXPLORATION mode: `--exploration --seeds 1` (1 outer × 1 inner × 10 n_trials × 3 symbols = 30 fits per cell; colsample_bytree=1.0 hardcoded)
- ENSEMBLE_SIZE=1 (EXPLORATION budget)
- All other strategy parameters byte-identical to iter-v3/018 multi-seed BOOTSTRAP baseline (3-symbol BCH+LDO+TRX universe, ATR labeling 2.0/1.0, zscore_threshold=2.0, BTC trend ±15%, ADX threshold=20, 7-primitive risk gate stack)
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS (NOT iter-v3/013 single-seed +1.0088/+2.6970 — formally falsified at iter-v3/018)

This was iter-v3/019, the **first POST-BOOTSTRAP EXPLORATION** (cadence #1 of 10 in the new cycle that follows iter-v3/018 CONFIRMATION-MERGE-BOOTSTRAP). The iteration is also the first NEW-external-data-source feature axis ever attempted in v3 catalog.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/019 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | **+1.156** | **+0.78** (way above predicted [+0.45, +0.85] upper bound) |
| OOS monthly Sharpe | +0.3869 | **+0.785** | +0.40 |
| OOS/IS Sharpe ratio | 1.02 | 0.679 | -0.34 |
| IS n_trades | 196 (mean) | **209** | bit-identical to iter-v3/013 portfolio total |
| OOS n_trades | 90.5 (mean) | **91** | <130 trade-rate floor (informational) |
| IS MaxDD | 21.86% (mean) | 20.55% | -1.31pp |
| OOS MaxDD | 27.74% (best seed 42) | 25.70% | -2.04pp |
| Top OOS conc | TRX 66.08% (seed 42) / 55.83% (seed 123) | BCH 53.94%, TRX 48.37% | improved balance |
| LDO OOS contribution | -10.24 (seed 42) | -2.31% (10 trades) | LDO neutral both sides |
| DSR | 0.0 (n_trials=1500) | **+0.0167** (n_trials=30) | first positive in v3 — REGIME-SPECIFIC ARTIFACT |
| PSR | 0.9936 | 1.0 saturated | EXPLORATION artifact |
| PBO mean / max | 0.0892 / 1.00 | 0.0971 / 1.00 | TRX/2025-Q4 carry-forward |
| n_eff | 25 | 7 | EXPLORATION budget structurally lower |

### vs iter-v3/013 single-seed EXPLORATION reference (same run mode; for IS-trade-roster comparison)

| Metric | iter-v3/013 | iter-v3/019 | Δ |
|---|---:|---:|---:|
| IS monthly_sharpe | +1.0088 | +1.1560 | +0.147 |
| OOS monthly_sharpe | +2.6970 | +0.7847 | -1.912 |
| IS n_trades portfolio | 209 | 209 | 0 (identical portfolio total — see audit below) |
| Per-symbol IS distribution | BCH 100, LDO 21, TRX 88 | BCH 96, LDO 23, TRX 90 | -4 / +2 / +2 |

### Falsifier 4 evidence

| Model | funding_rate_zscore_30 importance | Rank | Top-half (≤7)? |
|---|---:|---:|---|
| BCHUSDT | 25 (4.2% gain share) | **10/14** | No (Q3) |
| LDOUSDT | 173 (3.2% gain share) | **14/14** | No (dead last) |
| TRXUSDT | 118 (3.0% gain share) | **14/14** | No (dead last) |
| Portfolio agg | 316 (3.2% gain share) | **14/14** | No (dead last) |

Brief §4.4 PROMISING (clean) row requires top-half rank (≤7) for ≥1 symbol. BCH at rank 10 is Q3, not top-half. Zero symbols clear the bar → **PROMISING-INERT** correctly mapped (not clean-PROMISING).

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS. Look-ahead audit verified by spike-perturbation unit tests in `funding_v3.py` (`compute_funding_rate_zscore` strictly past-only via `s.shift(1)` then rolling). Embargo width REQUIRED_GAP=66 unaffected by 14th feature. Reproducibility stamp clean (Setup `d9f643b`, fix `9806dfb`, gate `f728e7f`, brief `db6e326`). Single-axis discipline preserved (V3_FEATURE_COLUMNS 13→14 is the SOLE varied axis).
- **IC orthogonality clean.** Max |IC| funding_rate_zscore_30 vs existing 13 = 0.287 (vs vwap_dev_20). Below 0.50 strict target and 0.70 hard gate. The feature is structurally orthogonal — carries position/leverage information not captured by price/return/volume features. The 14/14 importance ranking is NOT a redundancy artifact (rules out iter-v2/070's failure mode).
- **ADF stationarity clean.** Z-scoring is structurally stationary; ADF stat at IS-window-end: BCH -17.06, LDO -14.10, TRX ~-13.5, all p=0.
- **EXPLORATION budget held the wall-clock cap.** 6 minutes wall-clock (well within 2h EXPLORATION HARD CAP). Demonstrates fetch-funding CLI + funding cache + funding_v3 module added negligible overhead.
- **OOS concentration improved over iter-v3/018 anchor.** Top OOS concentration shifted from TRX 66.08% (seed 42) to BCH 53.94% / TRX 48.37% / LDO -2.31% — a meaningfully more balanced distribution. However this is a single-seed result and could be lottery-driven (see Lessons (b)).
- **Infrastructure delivered to spec.** New `crypto-trade fetch-funding` CLI subcommand, `data/funding_rates/<sym>.csv` local cache (zero-cost re-fetch via `--start` / `--symbols`), `funding_v3.py` module (209 lines, stdlib + numpy + pandas only), runtime `_verify_feature_columns` asserts len==14 + funding_rate_zscore_30 present. KEEP infrastructure in repo (zero revert cost; preserves option for iter-v3/028+ CONFIRMATION retest).

## What Failed

- **Falsifier 4 fires unambiguously.** Funding rate importance rank 14/14 across LDO + TRX + Portfolio aggregations. BCH at rank 10/14 is Q3 (above bottom quartile but not top-half). Zero symbols clear the rank ≤ 7 (top-half) threshold required for clean-PROMISING. The model demonstrably did not meaningfully learn the funding-rate signal at the EXPLORATION budget. **This is the same INERT pattern as iter-v3/015 microstructure (rank 14/14 across all 3 symbols at n_trials=10).**
- **IS Sharpe overshoots predicted band by +0.31 — single-seed lottery suspect.** Predicted band [+0.45, +0.85] median +0.58. Observed +1.156. The IS lift is +0.31 above the upper bound of the predicted PROMISING band on a SINGLE-SEED EXPLORATION run, the same overshoot signature as iter-v3/013's +1.0088 IS / +2.6970 OOS at single-seed --exploration --n-trials 10 — which was formally falsified at iter-v3/018 multi-seed CONFIRMATION (62% IS / 86% OOS reduction). The catalog row MUST flag this overshoot as "single-seed lottery suspect; multi-seed re-evaluation required before any bundling".
- **OOS n_trades = 91 < 130 trade-rate floor.** Informational caveat at EXPLORATION (`feedback_trade_rate_floor`); the floor applies at CONFIRMATION-bundle level per `feedback_trade_rate_floor_bundle_level`. Single-seed underpowering is structural at EXPLORATION budget.
- **DSR=+0.0167 first positive in v3 catalog — but EXPLORATION-mode regime-specific artifact, NOT edge significance.** Mechanism: at n_trials=30, López de Prado E[max_SR] = √(2 ln 30) = 2.608; observed annualized Sharpe = monthly +1.156 × √12 = 4.004 → marginal positive deflation. NOT comparable to BASELINE_V3.md DSR=0.0 at iter-v3/018 (n_trials=1500, observed_SR=1.7, E[max_SR]=3.369). The +0.0167 is the structural floor of "barely positive" at EXPLORATION trial counts — a regime-specific artifact that MUST NOT be cited as evidence of edge in the CONFIRMATION sense. New memory rule `feedback_v3_dsr_mode_artifact.md` enshrines this distinction so the iter-v3/019 INERT result is not mis-cited as edge evidence in a future bundle.
- **Trade roster non-bit-identical to iter-v3/013 at per-symbol level.** Portfolio total identical (209 = 209) but per-symbol shifts (BCH -4, LDO +2, TRX +2). The 14th feature altered LightGBM tree structure enough to redistribute a small number of signals between symbols — distinguishes from clean NULL-RESULT (iter-v3/012-style bit-identical), supports PROMISING-INERT classification (model partially used the feature for re-routing without learning useful signal).
- **Saturation falsifier just barely passes (96.3% of band max).** IS portfolio total 209 vs derived saturation band [129, 215]. Within band but at upper edge. The +12 IS trade redistribution is consistent with mode collapse on a 14-feature loss surface at n_trials=10.
- **sklearn version drift 1.8.0→1.6.0** noted in Critic Check 12. Not a BLOCK (v3 ML pipeline does not use sklearn-version-sensitive functions) but pyproject.toml needs explicit pin to prevent silent drift.

## Critical Lessons

(a) **NEW feature family at n_trials=10 EXPLORATION budget produces rank 14/14 regardless of feature quality.** iter-v3/015 (microstructure tbr_zscore_30 rank 14/14 across all 3 symbols) and iter-v3/019 (funding rate rank 14/14 LDO + TRX + Portfolio, 10/14 BCH) calibrate this prior. The Optuna TPE sampler at 10 trials does not have sufficient density on a 14-column loss surface to surface a single new feature whose univariate rank-IC is 0.04-0.05. INERT classification at EXPLORATION is INDETERMINATE between (i) genuinely-INERT feature and (ii) budget-constraint mode collapse. The unique resolution is CONFIRMATION-mode at higher trial count (~5h wall-clock), which is properly deferred to iter-v3/028+ when multiple HIGH-priority axes have accumulated.

(b) **Single-seed --exploration runs cannot definitively distinguish "feature inert" from "single-seed lottery overshoot".** iter-v3/013 produced +1.0088 IS / +2.6970 OOS at single-seed --exploration --n-trials 10 with colsample_bytree=1.0 → formally FALSIFIED at iter-v3/018 multi-seed (62% IS / 86% OOS reduction). iter-v3/019 produces +1.156 IS / +0.785 OOS — even larger IS overshoot vs predicted band on the same single-seed surface. The +0.31 IS overshoot above predicted upper bound is the canonical lottery signature. Catalog row MUST flag "single-seed lottery suspect; do NOT bundle pre-multi-seed-validation".

(c) **Funding-rate retest properly deferred to iter-v3/028+ CONFIRMATION.** A dedicated CONFIRMATION of `funding_rate_zscore_30` at --seeds 2 --n-trials 35 (post-iter-v3/018 default) would consume ~5h wall-clock and is NOT cost-justified at iter-v3/020 — funding rate is a single-feature axis and there are 9 more EXPLORATIONs to run before the next CONFIRMATION budget cycle. The right time is iter-v3/028+ when other HIGH-priority axes (concentration architecture, additional NEW feature families) have produced PROMISING-class evidence and a CONFIRMATION can bundle multiple candidates simultaneously. KEEP `funding_v3.py` module + `fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache infrastructure (zero revert cost; preserves option for iter-v3/028+ retest without re-implementing the fetcher).

(d) **sklearn version drift 1.8.0→1.6.0 noted; pyproject.toml needs explicit pin.** Library Stack reproducibility stamp showed sklearn 1.6.0 at runtime vs 1.8.0 in earlier briefs. Not a methodology defect for iter-v3/019 (v3 ML pipeline does not use sklearn-version-sensitive functions; LightGBM is the active ML backend). Flag for future iterations: `pyproject.toml` should pin sklearn explicitly with a tilde or caret constraint to prevent silent drift between runs of nominally-identical configurations. Pre-commit candidate for iter-v3/020.

(e) **EXPLORATION-mode DSR/PSR are regime-specific artifacts and MUST NOT be compared to CONFIRMATION-mode.** The +0.0167 DSR at iter-v3/019 is the first positive DSR in v3 catalog and could be misread as edge evidence by a future CONFIRMATION-bundling QR. The truth is the opposite: at EXPLORATION mode (--exploration --seeds 1 --n-trials 10), n_trials_per_cell=30 → E[max_SR]=2.608; observed annualized Sharpe ≈ 4.004 → marginal positive deflation results when observed_SR > E[max_SR]; +0.0167 is the floor of "barely positive". In CONFIRMATION mode (--seeds 2 --n-trials 35), n_trials_per_cell=1050 → E[max_SR]=3.42; a genuinely strong strategy needs observed annualized Sharpe > 3.42 to clear DSR > 0.95. Only CONFIRMATION-mode DSR enters MERGE gate evaluation per BASELINE_V3.md. New memory rule `feedback_v3_dsr_mode_artifact.md` enshrines this distinction.

## Pre-Commit for iter-v3/020

Per `feedback_v3_iter019_axis_priorities.md` LOCKED 2026-05-07 + Critic FINAL Recommendation #1 (SHA `1bc6028`):

- **iter-v3/020 axis = HIGH-priority #2 (concentration architecture).** Either (a) hard `max_per_symbol_pnl_share = 0.40` portfolio constraint at the aggregation layer, OR (b) universe expansion to 5+ symbols to dilute concentration mechanically. Cannot be renegotiated post-hoc. Funding-rate axis #1 is CLOSED for the current 10-EXPLORATION cycle.
- **DROP `funding_rate_zscore_30` from V3_FEATURE_COLUMNS at iter-v3/020 setup commit (revert 14 → 13).** Rationale: iter-v3/020's single-axis concentration-architecture variation requires a clean comparison surface against the iter-v3/018 anchor. Carrying an INERT feature forward into a different-axis EXPLORATION injects second-axis variance — Optuna would still see funding_rate_zscore_30 in the loss surface; iter-v3/020 attribution would be contaminated.
- **KEEP `funding_v3.py` module + `crypto-trade fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache infrastructure** (zero revert cost). Preserves the option of revisiting funding rate at iter-v3/028+ CONFIRMATION without re-implementing the fetcher.
- **Pre-commit memory rule** `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR/PSR values are INFORMATIONAL ONLY per the EXPLORATION carve-out; do NOT cite EXPLORATION DSR as evidence of edge significance. Only CONFIRMATION-mode DSR > 0.95 triggers MERGE gate evaluation. iter-v3/019's +0.0167 DSR MUST NOT be cited as edge evidence in catalog rows, briefs, or future CONFIRMATION-bundling QR.

## Cadence Status

**1 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 completed; 9 EXPLORATIONs remaining before next CONFIRMATION (earliest = iter-v3/028).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/019 ran 6 min — well within).

**Funding-rate axis CLOSED for current 10-EXPLORATION cycle.** A funding-rate retest at higher trial budget is properly deferred to iter-v3/028+ CONFIRMATION when multiple HIGH-priority axes have accumulated.

## Reproducibility

- Setup commit SHA: `d9f643b` (feat: fetch-funding CLI + funding_v3 module + V3_FEATURE_COLUMNS 13→14 + ITERATION_LABEL=v3-019)
- Fix commit SHA: `9806dfb` (fix: _verify_feature_columns asserts len==14)
- Phase 5.5 gate SHA: `f728e7f`
- Brief SHA: `db6e326`
- EDA analysis SHA: `95858cb`
- Engineering report SHA: `00d9b33`
- Critic FINAL SHA: `1bc6028`
- HEAD SHA at backtest run: `9806dfb`
- Reports: `reports-v3/iteration_v3-019/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-019/dsr.json` (DSR/PBO/PSR EXPLORATION-mode), `reports-v3/iteration_v3-019/per_cell_pbo.csv` (TRX/2025-Q4 high-PBO carry-forward), `reports-v3/iteration_v3-019/seed_summary.json`, `reports-v3/iteration_v3-019/pareto_front.csv`, `reports-v3/iteration_v3-019/ic_matrix.csv`, `reports-v3/iteration_v3-019/adf_test.csv`
- No tag (PROMISING-INERT — feature dropped at iter-v3/020; not a baseline-update event)

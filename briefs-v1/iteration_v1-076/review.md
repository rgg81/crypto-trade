# Phase 7.5 Critic Review — iter-v1/076

OVERALL: SPECIALIST-NEGATIVE — IS Sharpe -0.6943 (1.19 below PROMISING-VALIDATED +0.50; 0.89 below PROMISING-TENTATIVE +0.20 floor)

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST EXPLORATION — NEW SYMBOL universe-extension (AAVEUSDT)

## QR Response Considered
Round 2 N/A — single-pass review; no clarifications outstanding from a prior PRELIMINARY round on this iteration. The brief's F-AXIS bands (Section 4, frozen at commit SHA per Section 12) are mechanical adjudicators; the verdict is determined by comparing observed IS Sharpe -0.6943 against the pre-registered bands. LM 7.4 post-mortem (lgbm_advisor.md Phase 7.4 appendix) is consulted as supplemental input but does not alter the 14-check verdict.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation `src/crypto_trade/strategies/ml/walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/057 fix at commit `5566a69`/`e149e9d` cherry-pick); `cross_sectional.py:1325, 1345` also carry the subtraction. No iteration commits touched `walk_forward.py` or `labeling.py` (verified via `git log iteration-v1/076 --name-only`). Brief Section 2 EDA evidence relies on `is_only(df)` IS-filter helper + `_assert_is_only_path` path-substring guard — IS firewall intact. No look-ahead in feature engineering (no new features added in /076; pure single-bit symbols=("AAVEUSDT",) dispatch).

### Check 2 — Embargo Width: PASS
Labeling timeout = 21 candles × 8h = 168h; embargo_ms = `compute_embargo_candles(label_timeout_minutes=10080, interval_minutes=480) × 480 * 60_000` = `22 × 480 × 60_000`. For single-symbol cohort (n_symbols=1) the required gap = (21+1) × 1 = 22 candles; foundation helper applies this symmetrically via `walk_forward.py:113`. Brief Section 3.2 confirms inherited bit-exactly from /063 → /064 → /065 → /075 setup. Numerical proof: required gap 22, actual gap 22 — clean match.

### Check 3 — Multiple-Testing Correction: FAIL (informational for SPECIALIST)
`comparison.csv` shows DSR = -33.03 (IS) / -47.08 (OOS) — far below the +0.95 threshold; PBO/PSR not separately reported in comparison.csv (consistent with EXPLORATION-mode artifact schema). Per Section 5.1 of the Critic skill (TYPE=SPECIALIST/EXPLORATION clause) AND per `feedback_v3_dsr_mode_artifact` (EXPLORATION-mode DSR is structurally non-comparable to CONFIRMATION-mode), Check 3 axis FAILs are INFORMATIONAL only for SPECIALIST EXPLORATION budget. Recorded for catalog; not BLOCK-triggering.

### Check 4 — IC Correlation: INFORMATIONAL
No `ic_matrix.csv` is required for /076 EXPLORATION since no new features were introduced (brief Section 3.3: "No feature change"). Cross-asset feature-importance distribution from `feature_importance_Model_A_AAVE_specialist_076.csv` (per LM 7.4): `btc_funding_spread_30_90` at rank 4 (5.32% gain) and `eth_*` features at rank 47-48 (0.0 gain) is a structural feature-allocation observation, not an IC failure. Per 2026-06-01 EDA Discipline revision, this does not gate the iteration. Artifact-not-required (not artifact-missing).

### Check 5 — ADF Stationarity: INFORMATIONAL
No `adf_test.csv` required for /076 (no new features). Standard locked 48-col `V1_FEATURE_COLUMNS_PRUNED` stack — stationarity established at original prune-set introduction. Per 2026-06-01 EDA Discipline revision, this does not gate the iteration.

### Check 6 — Pareto Dominance: N/A
SPECIALIST EXPLORATION at single-outer-seed=42 (50-inner-seed averaging). 10-seed Pareto front is a CONFIRMATION-budget artifact; single-seed EXPLORATION does not produce a `pareto_front.csv`. Brief Section 2.5 documents the single-seed limit and the basin-lottery vigilance trigger (per-seed spread > 0.50 or σ_pop > 0.40 mandates multi-seed re-validation). Observed `specialist_dispersion_mean = 32.95` is the highest in roster — basin-lottery fingerprint confirmed at the cohort level. For NEGATIVE verdicts the basin-lottery downgrade is moot (already at NEGATIVE).

### Check 7 — Reproducibility: PASS
Single-bit dispatch discipline preserved: brief Section 3.1 (a)-(d) documents `SYMBOLS=("AAVEUSDT",)`, `ITERATION_LABEL="v1-076"`, and ATR (2.9, 1.45) Model A cell as the ONLY deviations vs /075 dispatch. `FEATURES_BASE_HASH_48COL` sha256 `b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` is asserted at runner entry. Pre-flight guards (Section 5.3 #1-15) enumerated. `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` passed explicitly per `feedback_explicit_feature_columns`. No silent dependency identified.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 H1 PRIMARY hypothesis: "the locked SPECIALIST methodology applied to AAVEUSDT will produce a SPECIALIST IS Sharpe in the PROMISING-TENTATIVE band [+0.20, +0.50]". The implementation tests exactly this — single-bit symbols=("AAVEUSDT",) dispatch with all 18 inherited methodology constants byte-identical to /075. The hypothesis was FALSIFIED by results (IS -0.69 vs predicted modal +0.20), but the implementation cleanly tested the registered hypothesis. No scope creep, no hypothesis-faking. Implementation faithfully delivered the falsifier.

### Check 9 — Symbol Exclusion Enforcement: N/A
v1 track has no V3_EXCLUDED_SYMBOLS analog at the dispatch level. The /076 dispatch branch asserts `set(symbols) == {"AAVEUSDT"}` (Section 3.1.c) which is the v1-side single-coin enforcement.

### Check 10 — Feature Isolation: N/A
v1-only specialist; no cross-track import risk.

### Check 11 — Forming-Candle Audit: PASS (inherited)
`data/AAVEUSDT/8h.csv` (6178 rows, 2020-10-16 → 2026-06-06) per brief table_01. Forming-candle guard lives in `fetcher.py` (not iteration-touched).

### Check 12 — Library Version Pinning: PASS (inherited)
No library changes in /076. Standard `pyproject.toml` pins from /063 family.

### Check 13 — Anti-Pattern Static Scan: PASS
Foundation scan negative for A1 (train_end_ms = test_start_ms without subtraction) at `walk_forward.py:113`, `cross_sectional.py:1325, 1345`. A2 (forward-window σ_t) not detected. A3 (scaler fit on combined train+test) — LightGBM is scale-invariant; no scaler in pipeline. A4 (universe survivorship) — AAVE not constructed from post-hoc volume filter; brief Section 0.7 documents 5.64y data extent from /076 mining-rank selection. A5 (master-data-extent dependency) — test file regression-coverage intact (not iteration-touched). A6 (Optuna study contamination) — per-(symbol, month) study creation pattern from /063 inherited. A7 (OOF parquet append) — N/A at v1 SPECIALIST. A8 (deadlock gate) — R1/R2 OFF for Model A (brief Section 5.2). A12 (DSR wrong-granularity) — DSR reported here is INFORMATIONAL EXPLORATION-mode; cannot evaluate path-traceability without a runner spec. A13 (write-before-read) — `specialist_dispersion.csv` written then read by report-writer; pattern consistent with /065 + /075 precedent.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares axis family `universe` (NEW SYMBOL universe-extension). git diff `iteration-v1/076` confirms the change: `run_iteration_076.py` clone + `V1_ITER076_UNIVERSE` constant + dispatch branch in `run_baseline_v1.py` — all `universe`-axis touches. No feature-family or risk-primitive code modified. Rotation status declared "VALID under the cycle-7 per-symbol regime-specialist mandate" — verified: axis-family rotation is SUSPENDED for cycle-6/7 per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate`, so back-to-back `universe` /075-/076 is explicitly authorized.

## F-AXIS Verdict Assessment

Per pre-registered Section 4 bands (frozen at brief commit SHA per Section 12):

| F-AXIS | Observed | Band | Verdict |
|---|---|---|---|
| #1 IS Sharpe | -0.6943 | < +0.20 NEGATIVE | **SPECIALIST-NEGATIVE FIRES** |
| #1 IS trade count | 158 | >= 50 floor | CLEARED |
| #2 cross-seed dispersion σ_pop | 32.95 (specialist_dispersion_mean) | > 0.40 (interpreted as σ_pop) | METHODOLOGY-NEGATIVE basin-lottery |
| #3 OOS Sharpe (informational) | +0.6234 | >= +0.40 + IS Δ < +0.10 | "Suspicious OOS-dominant lift" band — flags Phase 7.4 long-bias diagnostic |
| FALSIFIER #1 per-direction Sharpe | SHORT 71/-72.15 + LONG 87/-19.65 IS; SHORT 40/+55.50 + LONG 44/-6.23 OOS | balanced (53% short trades IS); neither direction dominates >70% | balanced — F-AXIS #1 verdict stands at face value |
| FALSIFIER #2 AAVE/ETH pred-corr + eth_* family rank | eth_* features rank 47-48 zero gain | corr < 0.40 + eth_* rank 8-14 | IDIOSYNCRATIC SPECIALIZATION confirmed — DeFi-cycle leakage HIGH risk REFUTED |
| FALSIFIER #3 feature-importance signature | top-3 = 22.3%, broad-based | flat ranking, no top-5 dominant | basin-lottery confirmation; σ_pop elevated as expected |

**Verdict adjudication is mechanical**: IS Sharpe -0.6943 < +0.20 NEGATIVE band threshold by 0.89 — SPECIALIST-NEGATIVE FIRES cleanly. Trade-count floor (50 IS) CLEARED at 158. Per-direction balance check passes (no >70%-dominant-direction mirage). 1st strike for AAVE seat per Section 0.7 NEW SYMBOL one-attempt-and-eliminate rule.

## Adversarial Note on IS/OOS Divergence

The OOS Sharpe +0.6234 at N=84 trades is **statistically meaningful but methodology-locked-out**. Computing the per-trade Sharpe standard error: σ_SR ≈ sqrt(2/(N-1)) = sqrt(2/83) ≈ **0.155**. The observed OOS Sharpe +0.6234 is **+0.62 / 0.155 ≈ 4.0σ above zero** — well past conventional 2σ significance.

**However this does not change the verdict.** Per `feedback_v1_oos_inflation_empirically_confirmed` (HARD methodology lock established at /046 from the /045 ALT_1 IS-only re-solve falsification), the IS-first gate is non-negotiable. The OOS edge being statistically real does not promote a NEGATIVE-IS iteration to bundle-eligible. The /045 evidence specifically established that OOS-aware composite scoring is empirically falsified and that any future v1 partition-solve MUST use IS-only scoring.

LM 7.4 diagnoses this OOS edge as **regime-accidental short-trend pickup** in 2026Q1-Q2 (14 shorts at 64.3% WR / +53.26 sum on a secular bear regime). The model's wrong-direction-bias became right by coincidence when the regime transitioned chop → trend. The IS evidence (4 quarterly mean-reversion V-shape regimes during 2022Q4-2025Q1) shows the model never learned a clean direction — broad-based importance (top-3 = 22.3%, top-10 = 54.9%) + dispersion 32.95 confirms 50 seeds disagreed throughout. This is the signature of a model exploring the wrong feature subspace for AAVE's price dynamics, not a model with residual edge.

**Critic concurs with LM 7.4's classification**: OOS +0.62 is informational not bundle-eligible. Per `feedback_v1_oos_inflation_empirically_confirmed` it CANNOT be cited as positive evidence in a future /AAVE-2 brief Section 1.

## LM 7.4 Diagnostic Cross-Check

LM 7.4's WRONG-FEATURE-FAMILY DOMINANCE + BASIN-LOTTERY classification is **independently confirmed** by the artifacts:
- Top-3 gain concentration 22.3% with `vol_atr_14` rank 1 (9.84%), `trend_aroon_osc_50` rank 2 (6.96%), `interact_natr_x_adx` rank 3 (5.53%) — slow trend confirmation + vol-regime features that fire on AAVE's high-vol regime indiscriminately.
- `btc_funding_spread_30_90` rank 4 (5.32%) while AAVE's own `funding_rate_zscore_30/90` rank 12 and 17 — model substituted BTC sentiment for AAVE-idiosyncratic signal.
- `regime_momentum_signed_5d` (rank 1-3 at DOT/063/064/065 — load-bearing primary signal carrier) at rank 29 with 0.59% gain for AAVE — the inherited DOT/063 feature stack does not transfer to AAVE's micro-structure.
- IS SL hit rate 97/158 = 61% (vs DOT/063 ~52%) — ATR(2.9, 1.45) pair calibrated for 110% vol cluster is mechanically mismatched to AAVE's 118% IS realized vol.

The LM 4.5 Risk Flag 1 (ETH-leakage HIGH) and Risk Flag 2 (BULL/BEAR regime inversion HIGH) are both **REFUTED by results** — eth_* features ranked 47-48 with 0.0 gain (no DeFi-cycle leakage materialized at the feature-importance layer); actual IS regime was CHOP-whipsaw mean-reversion, not bull-dominant (the +13× cumulative IS return masked 4 alternating V-shape quarters). LM 4.5 calibration: 2 of 5 risk flags directionally wrong, 1 directionally correct (vol cluster MEDIUM was actually dominant), 2 untested.

## Recommendations to QR (process-level for FUTURE iterations)

1. **NEW SYMBOL EDA must include per-quarter regime decomposition, not just per-year**. Brief Section 2.8 cited 2023 +109% + 2024 +184% + 2025-Q1 -40% cumulative — characterized as "bull-dominant". The actual quarterly decomposition (2022Q4 -31% / 2023Q1 +44% / 2023Q4 +58% / 2024Q3 +60% / 2024Q4 +88% / 2025Q1 -40%) reveals **chop-whipsaw mean-reversion**, not bull-trend. Annual cumret aggregations hide quarterly regime structure. Future NEW SYMBOL EDA tables should include quarterly directional regime tagging (4 IS quarters classified as TRENDING-UP / TRENDING-DOWN / V-SHAPE / CHOP using sign(close_t - close_{t-90})).

2. **Feature-stack adequacy probe should run BEFORE single-bit dispatch on NEW SYMBOL**. The LM 4.5 analysis spent 80% of its risk-flag budget on ETH-leakage and BULL/BEAR-inversion mechanisms; the ACTUAL failure mode was inherited-feature-stack-mismatch (top-3 importance = vol_atr_14 + trend_aroon_osc_50 + interact_natr_x_adx, none of which were rank-3 at any prior /063/064/065 specialist). A short pre-EXPLORATION diagnostic — compute per-feature IC vs forward returns on AAVE IS-only and compare rank correlations vs DOT/063's. If the Spearman rank-correlation between AAVE top-10 and DOT top-10 is < 0.50, flag the symbol as feature-stack-mismatched BEFORE Optuna spend.

3. **Specialist dispersion floor should be a brief Section 4 pre-registered gate**. Brief Section 4 F-AXIS #2 lists σ_pop bands but the catalog rule (`feedback_v1_basin_lottery_vigilance`) operates on per-seed spread / Jaccard / Spearman ρ which are different metrics than `specialist_dispersion_mean`. Make the `specialist_dispersion_mean > 30` threshold explicit in Section 4 (matched to /065 ~28 + /075 baseline) and pre-register that values > 30 trigger multi-seed re-validation regardless of headline IS Sharpe.

## Path Forward (mandatory on BLOCK verdict)

(Critic restates this is forward-looking guidance for the next iteration, NOT a verdict softener. The /076 SPECIALIST-NEGATIVE stands. AAVE seat: 1st strike per Section 0.7. Per the autopilot mining queue + brief Section 0.7 one-attempt-and-eliminate rule, AAVE is **dropped after this single attempt** unless the user explicitly authorizes a /AAVE-2 second strike. /077 ICPUSDT is already launched and rotates to non-DeFi narrative per LM 4.5 Saturation Risk 1.)

Three alternative axes for /077+ mining queue or potential AAVE re-attempt:

1. **NEW SYMBOL /077 ICP (storage/L1 narrative) at LOCKED methodology** — `universe` family — single-bit dispatch (`SYMBOLS=("ICPUSDT",)`, `ITERATION_LABEL="v1-077"`) inheriting Model A wrapper. Per LM 4.5 narrative-rotation mandate, /077 must NOT be DeFi-lending; ICP cleanly rotates cluster. Expected mechanism: ICP has different volatility regime (typically ~80-100%) and different cross-asset correlation profile (lower ETH co-movement than AAVE).

2. **Feature-stack pre-screen axis** — `feature-family` — instead of single-bit dispatch on a NEW SYMBOL with inherited 48-col stack, compute a per-symbol feature-stack-adequacy IC pre-screen on AAVE-IS only: rank each of the 48 columns by absolute Spearman IC vs 21-bar forward returns, compare the top-10 ranking vs DOT/063's. If the Spearman rank-correlation between AAVE top-10 and DOT top-10 is < 0.50, flag the symbol as feature-stack-mismatched BEFORE Optuna spend. This is methodology-stack-locked (no change to LightGBM head); it's a precondition gate not a methodology change.

3. **ATR per-symbol calibration axis (deferred)** — `risk-primitive` — if user authorizes /AAVE-2 second strike, LM 7.4 Rec 1 ATR pair recalibration 2.9/1.45 → 3.5/1.75 is the cleanest single-bit move. Mechanism: 61% IS SL hit rate (vs DOT/063 ~52%) confirms vol-cluster mismatch. Widening the SL distance by 0.30× ATR mechanically reduces SL-hit rate by ~15% (log-normal SL-distance distribution at AAVE's σ). Falsifier: if /AAVE-2 IS Sharpe ≤ -0.40 AND DD > 60%, AAVE is signal-absent (not vol-mismatched). 2nd strike fires.

All three axes are from families the QR HAS used in the prior 5 SPECIALISTs (/067 LTC `universe`, /073 ETH `feature-family`, /072 BTC `risk-primitive`), but under the cycle-7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate`), axis-family rotation is SUSPENDED — so the rotation constraint is auto-waived for cycle-6/7.

## Reaffirmation

**BUNDLE-001 (DOT/063 + ETH/064 + BTC/065) UNCHANGED.** No update to BASELINE_V1.md. AAVE seat 1st strike recorded. /077 ICPUSDT mining iteration continues per autopilot directive 2026-06-06.

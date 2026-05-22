# Phase 7.5 Critic Review — iter-v3/013 — FINAL (Round 2)

**OVERALL: EXPLORATION-PROMISING-MECHANICAL**

**Iteration Type**: EXPLORATION (single-axis: universe; drop MKR; 4-symbol → 3-symbol BCH+LDO+TRX; MANDATORY per `feedback_mkr_threshold_compression.md` FIRED at iter-v3/012)
**Round**: 2 FINAL (PRELIMINARY SHA `3f85e86`; QR Response SHA `36a4042` accepted in full)

## QR Response Considered

QR's 4 clarifications fold cleanly into the verdict:

1. **Clarification 1 (ADF demotion)**: ACCEPTED. 384/2041 non-stationary cells concentrate in early walk-forward (2020-2021 sparse-data months) where ADF is underpowered (n_obs < 200). V3_FEATURE_COLUMNS byte-identical to iter-v3/009 — no new feature audit obligation. Check 5 demotes WARN → PASS.

2. **Clarification 2 (catalog framing)**: ACCEPTED. New subtype `EXPLORATION-PROMISING-MECHANICAL` adopted as sister classification to `NEGATIVE-no-effect`. Trade-roster bit-identity proves +1.11 OOS Sharpe lift is mechanical drag-removal, **not** signal discovery via 3-symbol Optuna re-optimization.

3. **Clarification 3 (TRX caveat YES, drop-TRX rule NO)**: ACCEPTED. Catalog row records `n_high_pbo_cells_99=2` (TRX/2025-10, TRX/2025-11) with explicit pre-commit that future CONFIRMATION QR uses (1 − max_per_cell_pbo) aggregator. TRX has 0/1 OOS-negative iterations vs MKR's 5/5; drop-TRX rule fires only after 5 consecutive OOS-negative TRX iterations (parallel pre-committed threshold).

4. **Clarification 4 (docstrings + saturation parametrization)**: ACCEPTED. iter-v3/014 first commit fixes stale `= 88` strings at `run_baseline_v3.py:206, 211, 218` to parametrize against `REQUIRED_GAP`. Saturation falsifier in iter-v3/014 brief uses `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)`.

The new PROMISING-MECHANICAL subtype is structurally parallel to iter-v3/012's NEGATIVE-no-effect discipline and prevents misattribution of mechanical accretion as signal discovery.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
13-feature V3_FEATURE_COLUMNS byte-identical to iter-v3/009 audit. Universe-axis variation introduces no new feature paths. Triple-barrier ATR multipliers (2.0/1.0) act on past-only NATR. No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3 confirmed at runtime. CPCV n_paths=45, embargo=27 symmetric. Note: stale `= 88` docstrings at `run_baseline_v3.py:206, 211, 218`; runtime correct, hygiene fix pre-committed for iter-v3/014.

### Check 3 — Multiple-Testing Correction: WAIVED-INFORMATIONAL (EXPLORATION)
PBO=0.1075 (well below 0.4 even by CONFIRMATION standard). 2/127 cells with PBO > 0.99 (TRX/2025-10, TRX/2025-11) — pre-committed max-aggregator usage at CONFIRMATION.

### Check 4 — IC Correlation: PASS
Max off-diagonal |IC| ≈ 0.685 — below 0.7 threshold.

### Check 5 — ADF Stationarity: PASS (promoted from WARN per QR Clarification 1)
1657/2041 (81.2%) cells stationary. 384 non-stationary concentrate in early walk-forward (2020-2021 sparse-data) where ADF is underpowered. V3_FEATURE_COLUMNS byte-identical to iter-v3/009; no new feature design defect.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed --exploration)

### Check 7 — Reproducibility: PASS
Engineering report stamps SHA `e3168f2`. Single seed=42 literal. Spot-check OOS trades.csv reproduces. wall-clock 360s.

### Check 8 — Hypothesis-Implementation Alignment: PASS
V3_MODELS now 3 entries (BCH/LDO/TRX); ITERATION_LABEL="v3-013"; REQUIRED_GAP=66. Section 3.6 reconciliation 15/15 PASS. Saturation falsifier criterion 11: 209 IS trades < 240 threshold, Δ=−31 buffer — MKR drop propagated cleanly. Single-axis discipline holds.

### Check 9 — Symbol Exclusion Enforcement: PASS
{BCH, LDO, TRX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS (inherited)

### Check 12 — Library Version Pinning: PASS

## EXPLORATION-Specific Catalog Attribution

The PROMISING-MECHANICAL subtype is the correct framing because:

- BCH/LDO/TRX OOS trade rosters are byte-identical between iter-v3/012 and iter-v3/013.
- LDO weighted_pnl numerator (+40.60) is identical; concentration improvement (87.57% → 65.65%) is denominator-driven (total OOS PnL grew 46.36 → 61.85 from MKR's −15.49 removal), NOT diversification.
- The +1.11 OOS Sharpe lift attributes ENTIRELY to mechanical removal of MKR's −15.49% drag; ZERO contribution from 3-symbol Optuna re-optimization. Per-symbol architecture means MKR training was independent of other symbols by construction.
- 3rd consecutive favorable IS calibration overshoot (010, 011, 013; 012 was null). Empirical priors are systematically conservative.

## Recommendations to QR

1. **iter-v3/014 axis selection**: must vary a non-axis-already-tried. Current catalog: features×2 + labeling×1 + gate-zscore×1 + gate-btc-trend×1 + universe×1 = 5 unique axes. Suggested: **ADX threshold (currently 20)** — try 18 (looser, more trades) or 25 (tighter, more selective). Structurally orthogonal to all 5 prior axes; not subject to mechanical-accretion artifact.

2. **iter-v3/013 catalog row** must capture: subtype `EXPLORATION-PROMISING-MECHANICAL` (NEW); trade-roster bit-identity proof; denominator-driven LDO concentration improvement (87.57% → 65.65%, NOT diversification); 3rd consecutive favorable IS calibration overshoot vs predicted bands; TRX 2025-Q4 recurring tail caveat (`n_high_pbo_cells_99=2`, max-aggregator pre-commit); drop-TRX rule trigger pre-committed at 5 consecutive OOS-negative iterations (currently 0/1).

3. **iter-v3/014 first commit must**:
   (a) Fix stale `= 88` docstrings + comments in `run_baseline_v3.py:206, 211, 218` — parametrize against `REQUIRED_GAP` (e.g., `f"= {REQUIRED_GAP}"`).
   (b) Saturation predictor falsifier in iter-v3/014 brief Section 8 must derive `falsifier_threshold = ceil(1.2 × counterfactual_n_trades)` — replaces fragile hardcoded 240 with per-iteration derivation, robust to single-axis universe variations.

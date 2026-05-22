# Phase 7.5 Critic Review — iter-v3/125

OVERALL: EXPLORATION-NEGATIVE — NEGATIVE-catastrophic; IS Δ −1.25 and OOS Δ −0.86 both breach Section 8.1 PUBLIC-anchor thresholds; IS MaxDD 82.97% (predicted band [20%, 50%]); frac_positive_paths 0.467 below 0.55 floor; failure mode is architecture-distribution mismatch — 14-feature stack calibrated on BCH/LDO/TRX kurtosis/magnitude regime misfits ATOM/RUNE/UNI.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-7 slot #4/10; first under LIFTED constraints — universe + frequency unlocked per `feedback_v3_cycle7_constraints_lifted.md`)

## QR Response Considered (Round 2 only)
No clarifications requested; verdict unambiguous NEGATIVE-catastrophic; single round.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
EDA + production both clean. Feature pipeline `process_symbol_v3` symbol-agnostic. Single axis is V3_MODELS tuple substitution; no new look-ahead surface.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 unchanged. /058 walk-forward fix intact.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
PBO=0.1064 PASS (the only EXPLORATION-mode hard gate); DSR/PSR informational. frac_positive_paths=0.4667 < 0.55 floor is the corroborating EXPLORATION-mode signal: distribution centered slightly negative.

### Check 4 — IC Correlation: PASS (carry-forward)
No new features; ic_matrix carries forward known /025 carve-out pairs.

### Check 5 — ADF Stationarity: PASS
T4 EDA shows 9/9 candidate-symbol × incumbent-feature pairs p < 1e-6.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
Commit SHA `85f413b` stamped; ITERATION_LABEL v3-125; V3_MODELS verified at runner; PnL math spot-check clean.

### Check 8 — Hypothesis-Implementation Alignment: PASS
V3_MODELS replacement implemented exactly per brief Section 3; 0% trade-roster overlap with /121 (zero BCH/LDO/TRX in OOS trades); behavioral-effect predictor satisfied. Modal expectation NEGATIVE (50% prior); observed NEGATIVE-catastrophic (25% prior bucket) — within prior distribution at worse tail.

## Verdict Synthesis

NEGATIVE-catastrophic on multiple gates:
- IS Δ −1.248 (threshold −0.40; breached by −0.848)
- OOS Δ −0.858 (threshold −0.30; breached by −0.558)
- IS MaxDD 82.97% (ceiling 50%; breached by +33pp)
- frac_positive_paths 0.4667 < 0.55 floor

**Load-bearing finding**: 14-feature stack + (2.0, 1.0)-ATR K=21 calibration is BCH/LDO/TRX-cohort-shaped (lower per-bar magnitudes 85-168 bps; higher kurtosis 1.09-1.83). ATOM/RUNE/UNI present higher magnitudes (150-195 bps) + lower kurtosis (0.99-1.36) per T2 EDA — same EDA that PASSED at Phase 5.5. Pre-flight gates G1/G2/G3 (data-depth + return-correlation + ADF) are necessary but NOT sufficient for cross-cohort architecture transfer; tell nothing about whether trained model's *implicit calibration on tail-event structure* transfers.

Per-symbol attribution: ATOM IS +72.5% (sole carrier, 44% WR); RUNE −37% (30% WR); UNI −28% (39% WR). OOS inversion: UNI becomes the drag (−27%, 26% WR); ATOM (+22%) and RUNE (+4%) mildly positive. F2 (1-symbol carrier) + F3 (cross-cohort transfer failure) both fire.

**4th consecutive cycle-7 NEGATIVE** (after /122 NEGATIVE-INERT, /123/124 catastrophic). 8th universe-substitution attempt in v3 history (/021/069/078/083/087/110/111/125), all NEGATIVE-or-NEUTRAL.

## Recommendations to QR — /126 Axis Selection

**PRIMARY recommendation**: Multi-frequency feature stack — 8h base candles + 24h-aggregated features (NEW dimension in v3 catalog). Not equivalent to /124 K=63 longer-cadence labels (which was LABEL-DURATION at fixed base cadence); multi-frequency is FEATURE-CADENCE-STACK at fixed label horizon. Orthogonal axis classes. NO prior /124-equivalent precedent exists. Per `feedback_v3_structural_over_knob_exploration.md`: NEW feature families > universe > knobs. Data availability: FEATURES_DIR_24H at runner line 134; 24h features may already be generated. Single-axis brief committing to ONE specific 24h-feature subset (e.g., add 24h hurst + 24h ret_kurt to 14-feature 8h stack → 16-feature mixed-frequency).

**SECONDARY recommendation if (b) infeasible**: Vol-kurtosis-matched universe with EXPLICIT pre-registered falsifier on vol/kurtosis transfer mechanism — pick 3 symbols with T2 moments within 1 std of /121 incumbents, pre-register that NEGATIVE classification falsifies the broader "architecture-distribution sensitivity" hypothesis (closes much larger axis class if it fires).

**REJECT**: Per-symbol ATR multiplier (Critic option c) — axis-closure-violation of /074; would require 2-axis variation. Feature decimation by MI (Critic option d) — too close to "knob tuning" per saturation rules.

Cycle-7 catalog will benefit MOST from PRIMARY (b) — only option that genuinely expands v3 catalog's search-space dimension; universe substitution is 8th attempt in CLOSED family.

## Clarifications Requested from QR — NONE

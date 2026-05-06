# Phase 7.5 Critic Review — iter-v3/009 — FINAL

**Iteration Type**: EXPLORATION (catalog row #2 since last CONFIRMATION)
**Mode**: Round 2 — FINAL with OVERALL verdict
**Code SHA**: `43b3ed8` | Brief SHA: `96ec4d5` | Phase 5.5 Gate SHA: `7b72845` | QR Response SHA: `2158d0c`

---

## OVERALL: EXPLORATION-NEGATIVE

**Verdict basis**: Falsifier 1 (pre-registered in brief Section 4.3) mechanically activated by IS Sharpe = +0.0802 < +0.10 threshold. QR endorsed mechanical reading per "no cheating" pre-registration discipline. OOS = +1.1223 catalogued as INFORMATIONAL with sample-size and concentration caveats. All methodology checks (1-12) PASS / WARN-carry-forward / WAIVED-single-seed; no process-level BLOCK conditions.

---

## QR Response Considered

| # | Clarification | QR Position | Critic Disposition |
|---|---|---|---|
| 1 | Falsifier 1 disposition | Mechanical EXPLORATION-NEGATIVE; honor pre-registration on FIRST cadence-rule iteration | ACCEPTED — pre-registration discipline value of recording NEGATIVE on FIRST falsifier-trip exceeds informational gain from over-promoting an LDO-concentrated 12-trade lottery to PROMISING. The "no cheating" project-memory rule (`feedback_no_cheating`: never override registered measurement on un-pre-registered evidence) is decisive. |
| 2 | LDO concentration interpretation | 12-trade LDO lottery (95% CI [42.8%, 94.5%] on 75% WR), not robust 13-feature edge | ACCEPTED — bootstrap CI is too wide to claim signal; "BCH-dominated iter-v3/007 / LDO-dominated iter-v3/009" pattern is consistent with structural single-seed concentration-fragility, not per-symbol edge. MKR worsening (-6.5% → -13.1%) argues against uniform "redundancy drop helped" reading. |
| 3 | Stale `_verify_feature_columns` docstring | Defer to iter-v3/010 first commit (cosmetic, parametrize against `ITERATION_LABEL`) | ACCEPTED — non-blocking for v3-009 verdict; tracked as process improvement for next iteration. |
| 4 | Sample-size caveat for catalog | YES — record `OOS_trades=87 (< 130 trade-rate floor; OOS metrics informational only)` | ACCEPTED — explicit catalog-row caveat is the audit-trail mechanism that keeps `feedback_trade_rate_floor` operative across iterations. Prevents future CONFIRMATION QRs from over-weighting +1.12 OOS Sharpe when bundling exploration evidence. |

---

## Per-Check Status (carried forward from Round 1)

### Check 1 — Look-Ahead Audit: PASS

No new feature code in this iteration. iter-v3/009 introduces ZERO new features and ZERO modifications to feature computation. The active 13-feature set inherits from iter-v3/007/008 audit lineage; `vwap_dev_50` was DROPPED (not added). Labeling (triple-barrier with past-only ATR), purge gap (88 = (21+1)×4), and walk-forward boundary (`OOS_CUTOFF_MS = 1742774400000`) are byte-for-byte unchanged. No leak vector introduced.

### Check 2 — Embargo Width: PASS

Required gap = (timeout_candles + 1) × n_symbols = (21+1) × 4 = 88. Engineering report quotes the runtime banner: `Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88 [matches REQUIRED_GAP=88] PASS`. Inner CV gap = 22 rows (184h). Source-verified at `run_baseline_v3.py:212`.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL

Per TYPE=EXPLORATION: methodology axis (PBO + n_eff) enforced; edge axis (DSR/PSR) is informational only.
- **PBO (per-cell mean) = 0.1145** — well below the 0.40 threshold. iter-v3/007's PBO was 0.1419. PBO improved by ~0.027.
- **n_eff (per-cell median) = 7** — sensible; not pathologically low.
- **n_trials = 40** (10 trials × 4 symbols, single-seed exploration). Matches budget.
- **DSR = 0.0** and **PSR = 1.0** — well-documented exploration-mode artifact (DSR collapsed at single-seed; PSR saturated). EDGE axis is INFORMATIONAL per cadence rule and Section 8 of brief.

Methodology axis: PASS.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` confirms 13×13 matrix, max off-diagonal `|IC| = 0.6602` (`max_dd_window_50` × `range_realized_vol_50`, negative rho), 0 pairs at or above the 0.70 threshold. Highest cross-family ICs are all below 0.55. The IC-redundancy reduction promised by iter-v3/008's setup commit is empirically delivered. No new families added to scrutinize.

### Check 5 — ADF Stationarity: WARN (carry-forward, no regression)

ADF totals: 2278 stationary / 491 non-stationary out of 2769 rows = 17.7% non-stationary. Same per-month low-T artifact (60-bar windows + early IS months with sparse coverage). The non-stationary fraction has not regressed from iter-v3/007 baseline (same 13 features minus `vwap_dev_50`, so structurally must be ≤ iter-v3/007). Walk-forward retraining + ADF-as-monitoring (not gate) was waived in iter-v3/004 and stands; no NEW features introduced means no NEW ADF risk.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)

`pareto_front.csv` has exactly 1 row (seed=42). Per Section 8 criterion 9 of the brief and the cadence rule (`--seeds 1` for EXPLORATION), the 10-seed Pareto frontier comparison is structurally vacuous. WAIVED. Note for record: max_concentration = 98.61% (LDOUSDT-driven), informational only per Section 6.3.

### Check 7 — Reproducibility: PASS

- Code SHA stamped: `43b3ed8` in engineering report header.
- `ITERATION_LABEL = "v3-009"` confirmed at `run_baseline_v3.py:99`.
- `feature_columns` explicit via `V3_FEATURE_COLUMNS` (13-tuple, hardcoded literal at `features_v3/__init__.py:118-139`).
- `_verify_feature_columns()` at `run_baseline_v3.py:181-203` raises if `len != 13` OR `'vwap_dev_50' in V3_FEATURE_COLUMNS`. Belt-and-suspenders.
- Library versions stamped (lightgbm 4.6.0, numpy 2.2.6, etc.).

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1: drop `vwap_dev_50`, expect IS Sharpe ≥ +0.20. Code change in iter-v3/009 is single-line `ITERATION_LABEL` cosmetic update (the feature drop landed in inherited SHA `56b8f8b`). Single-axis variation respected. Hypothesis is testable (numeric IS Sharpe band [+0.18, +0.28] pre-registered). Falsifier 1 pre-registered AT IS-axis; the brief did NOT pre-register OOS predictions. The IS = +0.0802 fell BELOW Falsifier 1's +0.10 threshold — falsifier mechanically activated per the brief's own pre-registration. Per QR's Round 2 response (Clarification 1), mechanical reading is honored: the OOS = +1.1223 is INFORMATIONAL only and does NOT logically retract the IS-axis falsifier. Pre-registration discipline preserved.

### Check 9 — Symbol Exclusion Enforcement: PASS

`run_baseline_v3.py:151-158` (`_verify_symbols`) raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` is non-empty. Engineering report confirms `set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` verified at runtime.

### Check 10 — Feature Isolation Enforcement: PASS

`_verify_track_isolation()` at `run_baseline_v3.py:223-244` runs grep against `^from crypto_trade\.features ` and `^from crypto_trade\.features_v2` in `src/crypto_trade/features_v3/`. Engineering report confirms `Track isolation (features_v3 does not import v1/v2): PASS`.

### Check 11 — Forming-Candle Audit: PASS (no change)

Same data-staleness guard as iter-v3/007; data extent runs through 2026-04-30+ candle close (gates fire on full universe with 706+ rows in 2026-04 retrain month). No forming-candle issue identified.

### Check 12 — Library Version Pinning: PASS

Engineering report stamps versions: lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, pytest 9.0.2, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6. Stack matches iter-v3/007. No new external deps per brief Section 9.

---

## Anomaly Disposition Summary

The headline IS/OOS divergence (IS Δ -0.144, OOS Δ +1.060, ratio ~14x) is dispositioned as **mechanically NEGATIVE on the registered IS-axis falsifier with INFORMATIONAL OOS observation**:

| Axis | Pre-registered? | Result | Disposition |
|---|---|---|---|
| IS Sharpe | YES — Falsifier 1 at +0.10, predicted band [+0.18, +0.28] | +0.0802 (below threshold AND below predicted band) | NEGATIVE — Falsifier 1 mechanically activated |
| OOS Sharpe | NO (brief assumed IS direction → OOS) | +1.1223 (highest OOS in v3 track) | INFORMATIONAL — recorded with caveats |

**Concentration / sample-size caveats catalogued for v3-009 row**:
- `OOS_trades = 87` (< 130 trade-rate floor per `feedback_trade_rate_floor`)
- `OOS_concentration = 98.61%` (LDOUSDT-driven; 12 trades; 75% WR with binomial 95% CI [42.8%, 94.5%])
- `MKRUSDT got worse OOS` (-6.5% → -13.1%; argues against uniform redundancy-drop benefit)
- `DSR = 0.0 / PSR = 1.0` (single-seed exploration artifact)

PBO comparison: iter-v3/007 = 0.1419 → iter-v3/009 = 0.1145 (slight improvement, methodology axis is not getting WORSE).

---

## Recommendations to QR

(Process-level pointers for iter-v3/010 EXPLORATION; iter-v3/009 verdict is final.)

1. **iter-v3/010 should test a DIFFERENT axis (not features)** per the single-axis-variation rule and the diversity goal of the 10-EXPLORATION cadence. Two consecutive features-axis EXPLORATION rows (iter-v3/007 top-14 and iter-v3/009 top-13) leave the catalog under-diverse for downstream CONFIRMATION bundling. Candidate non-features axes: (a) labeling parameters (e.g., ATR multipliers `tp=2.9 / sl=1.45` perturbation), (b) risk-gate thresholds (e.g., z-score OOD threshold 2.5 → 2.0 or 3.0), (c) BTC trend filter band (currently ±20%), or (d) drop a DIFFERENT feature than `vwap_dev_50` (e.g., `ema_spread_atr_20` or `vwap_dev_20`) to triangulate which redundancy removal accounts for the IS drop. Catalog axis-diversity metric should be a Phase-8 explicit input.

2. **Catalog row for iter-v3/009 must explicitly record the dual-axis observation** so future CONFIRMATION-bundling QRs treat it correctly. Required fields: `verdict=EXPLORATION-NEGATIVE`, `IS_sharpe=+0.0802`, `falsifier1_activated=True`, `OOS_sharpe=+1.1223 (INFORMATIONAL)`, `OOS_trades=87 (<130 floor)`, `OOS_concentration=98.61% (LDO-driven, 12 trades, exact-binomial 95% CI on 75% WR = [42.8%, 94.5%])`, `MKR_OOS_regression=-6.5%→-13.1%`. The +1.12 OOS Sharpe MUST NOT be read as evidence of edge in any future bundle without independent multi-seed validation.

3. **Process improvement: parametrize the `_verify_feature_columns()` docstring against `ITERATION_LABEL`** in iter-v3/010's first commit (per Clarification 3). The current docstring at `run_baseline_v3.py:182-185` references `"iter-v3/008 brief Section 3.3"` and `"iter-v3/008 CONFIRMATION"`, both of which are stale (iter-v3/009 is EXPLORATION, not CONFIRMATION; the active brief is iter-v3/010's). This is the second iteration with a stale docstring banner reference (iter-v3/007 had the same drift). Add to the running "process improvements" list: parametrize all banner/docstring references against `ITERATION_LABEL` so they cannot drift across rebases. Same fix-pattern that was deferred from iter-v3/007 Clarification 4 — promote it to a P1 cleanup so the third instance does not occur.

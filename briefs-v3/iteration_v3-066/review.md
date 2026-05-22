# Phase 7.5 Critic Review — iter-v3/066

OVERALL: EXPLORATION-INERT-CERTIFIED-CLEAN — axis CLOSED; not advancing to /070 CONFIRMATION bundle. No methodology FAIL; the INERT classification is the pre-registered 50% prior-probability outcome, faithfully realized.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #7 of 10; NON-FEATURE PIVOT CONTINUATION per Critic /064 Rec #4; RISK PRIMITIVE axis — UNIVERSAL `vol_scale_ceiling 1.0 → 0.8` Path E0.8; concurrent REVERT of /065's DEFAULT_ATR_MULTIPLIERS=(2.0, 1.5) back to (2.0, 1.0) for axis isolation).

## Foundation Audit (Boot Steps 9-11): PASS

- `walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms` INTACT.
- `features_v3/__init__.py:222`: `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` REVERTED from /065's (2.0, 1.5).
- `risk_v2.py:594-610::_vol_scale`: `np.clip(raw, floor, self.config.vol_scale_ceiling)` — single inference-time call site.
- `run_baseline_v3.py:1455`: `vol_scale_ceiling=0.8` in RiskV2Config init.
- `run_baseline_v3.py:691-716`: NEW pre-flight runtime assertion `config.vol_scale_ceiling == 0.8` IN PLACE.
- `validation_v3.py:54`: `REQUIRED_GAP = 66` UNCHANGED.
- `ITERATION_LABEL = "v3-066"` ✓; V3_FEATURE_COLUMNS_TOP_N = 14 features BIT-IDENTICAL to /060 anchor (no adx_14).

## §11 Anti-Pattern Static Scan: PASS (13/13)

- A1 frozen-baseline: NOT triggered. IS bit-identity to /060 is STRUCTURAL — Optuna objective at `optimization.py:295` uses LABEL-derived raw PnLs computed BEFORE RiskV2's `_vol_scale`; identical seeds + training data + objective → identical hyperparameter convergence → identical trade emission roster. Only `weight_factor` and `weighted_pnl` differ between /060 and /066. Not stale-result bug.
- A2-A13: all PASS.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
vol_scale_ceiling=0.8 is config-time-static. No historical-data leak.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 66 = (21+1)×3; cv_gap = 22×3 = 66; symmetric application.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION mode)
DSR=0.0, PBO=0.1278 (PASS), PSR=0.9935 (PASS >0.95), DSR_relative≈0 (EXPLORATION-mode informational), frac_positive_paths=0.6444 PASS. n_trials=315, n_eff=19.

### Check 4 — IC Correlation: PASS
`ic_matrix.csv` BYTE-IDENTICAL to /060 (vol_scale_ceiling doesn't alter feature covariance — only weights). Max |IC|=0.7642 (composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`).

### Check 5 — ADF Stationarity: PASS
All 14 features stationary at end-of-training-window for BCH/LDO/TRX.

### Check 6 — Gate 10-CPCV: PASS
`cpcv_frac_positive_paths = 0.6444` IDENTICAL to /060 anchor (architecture-invariant under inference-time-only weight modification).

### Check 7 — Reproducibility: PASS
- Setup `8598f1c` → phase 5.5 `59821fa`. Chain intact.
- ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631) confirmed in `ensemble_summary.json`.
- Trade-math spot-check (3 OOS trades): all match CSV to ±0.002%.
- **Ceiling-integrity audit**: 0/159 IS + 0/103 OOS trades violate `weight_factor ≤ 0.8`. 22 IS + 18 OOS trades bound exactly at ceiling=0.8.

### Check 8 — Hypothesis-Implementation Alignment: PASS-with-disclosure
- Brief Section 1 hypothesis predicted INERT-AT-EXPLORATION most likely; ORACLE predicted IS Δ +0.008 / OOS Δ +0.022.
- Observed: IS Δ -0.0017 / OOS Δ +0.0353 — both within INERT band; ORACLE within ±0.04 (TIGHTEST in cycle 1).
- Section 4.4 D.14 saturation falsifier FIRES (per-symbol WR Δ all within ±2pp; total OOS trades 102→103 within ±5%) — confirms vol_scale_ceiling=0.8 has no behavioral impact on trade selection (only weights changed).

**DISCLOSURE**: /066-vs-/060 comparison reflects TWO carry-forward changes: (a) axis (`vol_scale_ceiling` 1.0→0.8), AND (b) inherited `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` from /061. DECLARED in brief Section 2.5; consistent with cycle 1 anchor convention. ORACLE used new_floor=0.3 (not 0.5), under-modeling actual config — but observed Δ still within ±0.04 of ORACLE on both axes. Flagged as Rec #1.

### Check 9-12: PASS

### Check 13 — RISK PRIMITIVE axis specific: PASS

- vol_scale_ceiling correctly threaded through RiskV2Config → _vol_scale.
- Universal application — all 3 symbols share ceiling=0.8.
- Per-symbol WR Δ (saturation falsifier per Critic /065 Rec #3 ±2pp band): BCH 0.0pp / LDO -1.5pp / TRX 0.0pp — all within band. D.14 fires correctly.
- **Dispatch context error**: orchestrator's prose cited /060 TRX OOS WR as 39.6% (incorrect) leading to "+8.5pp" claim. Actual /060 TRX OOS WR per `comparison.csv` is 48.1% — same as /066. Δ=0.0pp. Engineering report used byte-exact comparison.csv; orchestrator-prose error did NOT propagate into brief or runner. Documented in engineering report "Anomaly Notes".

## Adversarial Findings

### Q1 — IS bit-identity to /060: stale-result fingerprint or structural artifact?

**Structural artifact**. Optuna objective uses LABEL-derived raw PnLs computed BEFORE RiskV2's _vol_scale. Same seeds + training data + objective → same hyperparameter convergence → same trade emission roster. Only weight_factor/weighted_pnl differ. Random row sampling of in_sample/trades.csv between /060 and /066 confirms byte-identical (symbol, direction, entry_price, exit_price, open_time, close_time, exit_reason) tuples.

### Q2 — Why OOS trade count 102 → 103?

Walk-forward training per (symbol, month, seed) for OOS months ≥ 2025-04 uses post-cutoff candles during catch-up. The +1 LDO OOS trade arises from Optuna's hyperparameter trajectory diverging by chance in one (LDO, month) cell. The new trade is a loser (12 trades / 16.7% WR vs /060's 11 / 18.2%), offsetting some of the LDO anti-Kelly gain. Not a leakage indicator.

### Q3 — Anchor inconsistency

The /060 anchor predates /061's TRX-floor=0.5 introduction. /066 inherits the floor from /061's INERT carry-forward. ORACLE EDA used new_floor=0.3 (not 0.5), under-modeling actual config. Empirically ORACLE was still within ±0.04 on both axes. Recommendation #1 for /070 CONFIRMATION.

### Q4 — LDO OOS lift: real anti-Kelly correction or noise?

**Mixed**. ORACLE T3 predicted LDO OOS Δ +2.66 (capping 6 of 11 wf≥0.8 trades); observed +2.59 matches within 0.07 wpnl. Mechanism is REAL (capping high-wf losers reduces magnitude of losses). But LDO OOS remains -17.14 wpnl, 16.7% WR — the ceiling correction provides partial relief, not reversal.

### Q5 — Does the ceiling create cross-symbol asymmetry despite universal config?

**Yes — by mechanism, not config**. Ceiling=0.8 is universal in config but binds asymmetrically because trade-level wf distributions differ across symbols:
- BCH IS: 24 of 73 trades had wf≥0.8 → Kelly cost -9.40 wpnl
- LDO IS: 4 of 11 → near-neutral
- TRX IS: 30 of 75 → mixed

Net IS -3.92 wpnl (BCH dominates); Net OOS +0.28 (LDO anti-Kelly correction barely outweighs BCH+TRX Kelly costs). This asymmetric mechanism IS the structural reason why a UNIVERSAL ceiling axis cannot produce PROMISING when one symbol is Kelly-aligned (TRX) and another is anti-Kelly (LDO) — universal change cannot exploit per-symbol opportunity without violating `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. **INERT verdict is structurally inevitable given per-symbol Kelly heterogeneity. Universal-ceiling family STRUCTURALLY EXHAUSTED for current 3-symbol bundle.**

## Recommendations to QR

1. **Anchor consistency for /070 CONFIRMATION bundle**: when evaluating multi-seed Δ at /070, document EXPLICITLY whether the anchor includes /061's TRX vol_scale_floor=0.5 (and any "INERT-but-preserved" carry-forwards). The /060 anchor predates the TRX floor; CONFIRMATION-mode comparison should select either post-/061 unified anchor OR re-run /060-spec under current config.

2. **Per-symbol Kelly heterogeneity is the structural ceiling-axis falsifier**. /066 closes the universal-ceiling axis cleanly. Future /067-068 risk-primitive EXPLORATIONs SHOULD avoid universal symmetric clip/cap mechanisms when ORACLE T3-equivalent decomposition shows opposing Kelly directions across the 3 symbols. Per-symbol ceiling would violate `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — universal-ceiling family STRUCTURALLY EXHAUSTED.

3. **Orchestrator dispatch anchor-value error pattern (SECOND RECURRENCE)**: /065 Critic Rec #1 (anchor-value propagation error in QR brief) recurred at /066 in orchestrator dispatch prose (incorrect /060 IS WR 28.99% / OOS WR 36.17% / TRX OOS +4.16). Brief itself and runner were CLEAN (byte-exact /060 values). QE engineering report corrected explicitly under "Anomaly Notes". Recommend: orchestrator dispatch prose ALWAYS sources headlines from `comparison.csv` byte-exact lookups, never from prior-iteration narrative recollection.

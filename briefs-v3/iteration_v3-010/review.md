# Phase 7.5 Critic Review — iter-v3/010 — FINAL (Round 2)

**OVERALL: EXPLORATION-PROMISING with caveats**

**Iteration Type**: EXPLORATION (catalog row #3 since last CONFIRMATION; non-features axis = labeling, per Critic FINAL Rec 1 of iter-v3/009)
**Mode**: Round 2 — FINAL
**Code SHA**: `b55086a` | Brief SHA: `fdb17b1` | Phase 5.5 Gate SHA: `5a227c7` | Analysis SHA: `80332c1` | QR Response SHA: `55464bd`

---

## QR Response Considered (4 Clarifications)

The QR submitted a written response to all four Critic Round 1 Clarifications. Critic dispositions:

**Clarification 1 (Mechanism attribution)** — Disposition: **ACCEPTED**. QR endorses mechanism (c) "tighter labels reduce label noise so features find real momentum more cleanly" with structural reasoning that rules out (a) and (b): the IS lift is broad-based at the per-symbol level (3/4 symbols turned positive) rather than concentrated, and PBO IMPROVED (0.1145 → 0.1077) on the strictly-tighter label distribution — structurally inconsistent with mechanism (a)'s "edge was always there but masked" since (a) would predict neutral or worse PBO. Same 2:1 TP:SL ratio preserved means the only mechanical change is absolute barrier tightness, which compresses noise bandwidth without rotating directional structure. QR's explicit deferral of the per-exit-type breakdown to a future axis-diagnostic EXPLORATION respects the single-axis cadence rule and is correct discipline. Catalog will cite mechanism (c).

**Clarification 2 (MKR structural failure)** — Disposition: **ACCEPTED**. QR pre-commits the per-symbol-exclusion threshold at 6-7 consecutive negatives (3-4 more EXPLORATIONs) before the universe-change axis is consumed. This honors `feedback_insist_on_symbols` ("don't reject candidates after one Gate 3 fail; run feature importance, labeling, and lookback analysis first") while acknowledging the pattern in catalog. The catalog row will record `MKR_OOS=-10.6%` with note "3rd consecutive negative; revisit at 6-7 if pattern persists" — sufficient audit trail without re-deriving the rule each iteration.

**Clarification 3 (OOS trade-rate floor implications)** — Disposition: **ACCEPTED**. QR pre-commits to option (c): **the floor applies at the BUNDLE level at CONFIRMATION, not per EXPLORATION row**. Reasoning is sound: 5-seed × `n_trials=50` × `ensemble_size=5` at CONFIRMATION density should multiply OOS trades 3-4× per row via independent ensemble decisions, plausibly bringing 109-trade EXPLORATIONs to 350-450 trades at CONFIRMATION. Pre-commitment NOW (in iter-v3/010 catalog row, before knowing the CONFIRMATION outcome) prevents post-hoc rationalization at the future CONFIRMATION boundary. QR commits to adding `feedback_trade_rate_floor_bundle_level` to memory — exactly the discipline this kind of rule needs.

**Clarification 4 (Per-cell PBO outliers)** — Disposition: **ACCEPTED**. QR will record `n_high_pbo_cells = 5/175` in the catalog row, enabling future CONFIRMATION QRs to choose between `(1 - mean_pbo)` vs `(1 - max_per_cell_pbo)` weighting on bundle evidence without forcing a methodology change at iter-v3/010.

All four QR dispositions are coherent, pre-commit before benefit, and preserve audit-trail discipline. None reverse-engineer outcomes.

---

## Per-Check Status (carried forward from Round 1, no regressions on Round 2 review)

### Check 1 — Look-Ahead Audit: PASS
ZERO new feature code. Single behavior change is labeling barrier multipliers (`atr_tp_multiplier=2.0`, `atr_sl_multiplier=1.0`) at `run_baseline_v3.py:862-863`. `LightGbmStrategy._load_atr_for_master()` reads past-only `natr_21_raw` per (symbol, open_time); `label_trades()` scans forward only from entry. Multipliers act on past-only ATR; no leakage path created.

### Check 2 — Embargo Width: PASS
Required gap = `(timeout_candles+1) × n_symbols = (21+1) × 4 = 88`. Pre-flight banner confirms `Label-leakage gap: ... = 88 [matches REQUIRED_GAP=88] PASS`. Per-symbol fold gap = 22 rows. Timeout unchanged at 21 candles; barrier-distance shrinkage cannot reduce temporal width of overlapping forward windows.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL
Per TYPE=EXPLORATION cadence rule: methodology axis (PBO, n_eff) enforced; edge axis (DSR/PSR) informational only.
- PBO (per-cell mean) = **0.10770** << 0.40 threshold; slight improvement vs iter-v3/009's 0.1145.
- PBO `frac_positive_paths=0.600` from 45 return-proxy paths.
- n_eff (per-cell median) = **7** > 4 minimum.
- n_trials = 40 (10 × 4 symbols, single-seed). Matches budget.
- DSR=0.0, PSR=1.0 — single-seed exploration artifact, INFORMATIONAL per cadence.
- 5 cells with PBO ≥ 0.9 (TRX/2025-10, TRX/2025-11, MKR/2024-10, MKR/2025-04, MKR/2025-07) noted; mean aggregator dilutes; will be recorded as `n_high_pbo_cells=5/175` in catalog per QR Clarification 4 disposition.

Methodology axis: PASS.

### Check 4 — IC Correlation: PASS
13×13 `ic_matrix.csv`. Max off-diagonal `|IC| = 0.660` (`max_dd_window_50 × range_realized_vol_50`); ZERO pairs ≥ 0.70 threshold. No new feature families introduced; feature axis byte-for-byte unchanged from iter-v3/009.

### Check 5 — ADF Stationarity: WARN (carry-forward, no regression)
2769 (symbol, feature, month) cells; 82.3% stationary; non-stationary cluster concentrates in early months and persistent-by-construction features (max_dd_window_50, hurst_100, ret_skew_200). Walk-forward retraining + ADF-as-monitoring waiver from iter-v3/004 stands; feature set unchanged means structurally same ADF profile as iter-v3/009.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)
`pareto_front.csv` has exactly 1 row (seed=42). Per Section 8 criterion 9 + cadence rule (`--seeds 1` for EXPLORATION), 10-seed Pareto frontier comparison is structurally vacuous. WAIVED. Note: `max_concentration_pct = 52.51%` (BCH) exceeds the 35% per-symbol cap that would apply at CONFIRMATION; informational under EXPLORATION per brief Section 6.3 — to be recorded in catalog row.

### Check 7 — Reproducibility: PASS
Code SHA `b55086a` stamped; `ITERATION_LABEL = "v3-010"` confirmed; `feature_columns` explicit via `V3_FEATURE_COLUMNS` 13-tuple; `_verify_feature_columns()` raises if drift. Trade-row spot-check (3 random OOS rows): MKR LONG 1067.7→1200.0559 weight=0.67 net+12.2964% matches; MKR SHORT 1436.1→1487.6081 net-3.6867% matches. Library versions stamped (lightgbm 4.6.0, etc.) — identical to iter-v3/009.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 stipulates `(tp=2.0, sl=1.0)` with same 2:1 ratio, expected IS Sharpe ≥ +0.10. Code change literally implements only this; ITERATION_LABEL is `v3-010`; docstring partially parametrized. The 13-feature set, risk gates, CPCV, training_months=24, OOS_CUTOFF_DATE all byte-for-byte unchanged from iter-v3/009. Falsifiers 1, 2, 3 NOT triggered. IS Sharpe (+0.5683) overshoots the predicted band's upper end (+0.40) by 0.17 — calibration miss in the FAVORABLE direction; QR Clarification 1 attributes to mechanism (c) and the catalog will cite that.

### Check 9 — Symbol Exclusion Enforcement: PASS
`_verify_symbols` enforced; `V3_EXCLUDED_SYMBOLS` ∩ {BCH, MKR, LDO, TRX} = ∅. 4/4 active models confirmed in run.log.

### Check 10 — Feature Isolation Enforcement: PASS
ZERO new files in iter-v3/010 commits; inherited isolation guarantee from `_verify_track_isolation()` unchanged.

### Check 11 — Forming-Candle Audit: PASS (no change)
Same data-staleness guard inherited from iter-v3/007 (`max_lag_hours=16.0`). Per-cell PBO data extends through 2026-05 retrain month; no forming-candle anomaly.

### Check 12 — Library Version Pinning: PASS
Stack identical to iter-v3/009: lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, pytest 9.0.2, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6. No new external deps per brief Section 9.

---

## Verdict Reasoning

All 12 checks resolve to PASS, WARN-carry-forward, or WAIVED-single-seed. **No BLOCK conditions exist.**

**Pre-registered falsifiers (Brief Section 7) — outcomes:**
- Falsifier 1 (IS Sharpe < +0.10) — **NOT triggered**. IS Sharpe = +0.5683, +0.47 above threshold.
- Falsifier 2 (IS trades < 267) — **NOT triggered**. 357 IS trades, +33.7% scaling.
- Falsifier 3 (wall-clock > 30 min) — **NOT triggered**. 7 min actual.
- Process falsifier — **NOT triggered**. All pre-flight checks PASS.

**Differentiation from iter-v3/009 (the EXPLORATION-NEGATIVE precedent):**
- iter-v3/009's headline OOS was a 12-trade-LDO single-symbol lottery (98.6% concentration); iter-v3/010's per-symbol OOS is materially different — 3 of 4 symbols positive (BCH +35.27%, LDO +27.41%, TRX +10.82%) with only MKR negative (-10.65%); concentration 52.51% (BCH-driven) is high but not single-symbol-dominant.
- iter-v3/009's IS Sharpe was +0.0802 (below Falsifier 1 threshold); iter-v3/010's IS Sharpe is +0.5683 (well above), and the IS lift is broad-based per QR Clarification 1.
- The IS Sharpe overshoot is in the FAVORABLE direction; per brief Section 7 calibration discipline, this is documented as a calibration miss to be recorded in diary.
- Methodology axes are clean: PBO 0.1077 < 0.40, n_eff 7 > 4, broad-based IS lift, mechanism (c) consistent with PBO improvement.

**Caveats requiring catalog documentation (per QR pre-commits):**
1. Mechanism cited: **(c) tighter labels reduce label noise so features find real momentum more cleanly**.
2. **MKR pattern flag**: 3rd consecutive negative; per-symbol diagnostic threshold at 6-7 consecutive.
3. **n_high_pbo_cells = 5/175**: structural instability cells in (TRX/2025-10, TRX/2025-11, MKR/2024-10, MKR/2025-04, MKR/2025-07) for future weighting decisions.
4. **OOS trade-rate 8.07/month < 10/month floor**: informational under EXPLORATION; floor applies at BUNDLE level at CONFIRMATION per QR Clarification 3 pre-commitment.
5. **OOS BCH concentration 57.17%** > 35% CONFIRMATION cap: informational under EXPLORATION per brief Section 6.3.

This is the FIRST EXPLORATION-PROMISING since iter-v3/007 and a real candidate for next CONFIRMATION bundling.

---

## Recommendations to QR

1. **iter-v3/011 should test ANOTHER non-features axis** to maximize catalog axis diversity before CONFIRMATION bundling. Suggested: **risk-gate axis — z-score OOD threshold 2.5 → 2.0 (tighter) or 3.0 (looser)** as single-axis variation. The labeling axis just produced PROMISING; gate sensitivity is the natural next probe and is structurally orthogonal to both features (iter-v3/007/009) and labeling (iter-v3/010). After iter-v3/011 the catalog will have axis coverage of features × 2, labeling × 1, risk-gate × 1 — meaningful diversity for the eventual CONFIRMATION bundle.

2. **Catalog row for iter-v3/010 must explicitly capture all four caveats** verbatim from QR's response: (a) mechanism = (c) tighter-labels-reduce-noise; (b) MKR pattern flag = "3rd consecutive negative; revisit at 6-7 if pattern persists"; (c) n_high_pbo_cells = 5/175 (TRX/2025-10, TRX/2025-11, MKR/2024-10, MKR/2025-04, MKR/2025-07); (d) OOS_trade_rate = 8.07/month < 10/month floor (informational at EXPLORATION; floor applies at bundle level per Clarification 3); (e) OOS_max_concentration = 57.17% (BCH-driven) > 35% CONFIRMATION cap (informational at EXPLORATION). Future CONFIRMATION QRs must inherit this audit trail without re-deriving any of these caveats under post-hoc pressure.

3. **Add `feedback_trade_rate_floor_bundle_level` to project memory** per QR Clarification 3 disposition. The rule: "OOS trade-rate floor (`feedback_trade_rate_floor`: ≥10/month, ≥130 total) is satisfied at the CONFIRMATION-bundle level, not per EXPLORATION row. Each EXPLORATION row need only be counted, not floor-cleared, for inclusion in a CONFIRMATION bundle. CONFIRMATION-time bundled trades < 130 legitimately fails the edge axis at MERGE evaluation." Pre-committing this NOW (before any CONFIRMATION decision is in hand) is exactly the discipline the cadence framework requires; without it the next CONFIRMATION QR could easily rationalize a floor-relaxation under pressure to merge a near-miss bundle.

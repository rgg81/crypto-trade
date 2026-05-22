# Phase 7.5 Critic Review — iter-v3/014 — FINAL (Round 2)

**OVERALL: EXPLORATION-NEGATIVE**

**Mode**: ROUND 2 FINAL — issued after QR Response (`qr_response.md`, SHA `f96a9f3`) addressed all 5 Round 1 PRELIMINARY clarifications.
**Scope discipline**: Per Section 0.5 TYPE=EXPLORATION, methodology axes 1, 2, 4, 5, 6, 8 enforced; edge axis (DSR/PSR Check 3) INFORMATIONAL only.
**Round 1 PRELIMINARY**: SHA `bf42814` (carry-forward of per-check status preserved below; QR Round 2 dispositions accepted).

---

## Per-Check FINAL Status

### Check 1 — Look-Ahead Audit: PASS
V3_FEATURE_COLUMNS unchanged (13). The single-axis variation (`adx_threshold` 20 → 25) touches gate logic only, not feature pipeline. ADX is computed via 14-period Wilder rolling on past-only OHLC. No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 confirmed at runtime. CPCV n_paths=45. Symmetric purge gap=66 with embargo=27. **Stale `= 88` docstrings REMOVED** per Critic FINAL Rec 3 of iter-v3/013 — `grep -nE '= 88' run_baseline_v3.py` returns 0 matches. Hygiene fix landed at SHA `bdcce5d`.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (per EXPLORATION protocol)
DSR=0.0, PSR=1.0, n_trials=30, n_eff=7, PBO=0.1075 (stable bit-identical to iter-v3/013). `n_high_pbo_cells_99` = 2 (TRXUSDT/2025-10 = 1.000, TRXUSDT/2025-11 = 1.000) — same TRX 2025-Q4 carry-forward as iter-v3/013, confirmed by QR Clarification 3. BCH/2024-10 at PBO = 0.9868 below the 0.99 cutoff, not counted. No new 99-tail entries. Mean aggregator at 0.1075 statistically identical to iter-v3/013. Per audit-trail discipline, future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` aggregation.

### Check 4 — IC Correlation: PASS
Max off-diagonal |IC| = 0.6847 (range_realized_vol_50 × max_dd_window_50); below 0.70 threshold. Bit-identical to iter-v3/013 (zero new features).

### Check 5 — ADF Stationarity: PASS (PROMOTED from PRELIMINARY WARN per QR Clarification 1)
1657/2041 (81.2%) cells stationary. 384 non-stationary concentrate in 2020-Q1 sparse-data months where ADF is structurally underpowered (n_obs < 200) — confirmed by QR Clarification 1(a). V3_FEATURE_COLUMNS bit-identical to iter-v3/009 (Check 5 PASS-promoted at iter-v3/013 Round 2 SHA `1ee0213`); iter-v3/014 inherits the audit informational-only — confirmed by QR Clarification 1(b). Demotion WARN → PASS (carry-forward).

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed --exploration)

### Check 7 — Reproducibility: PASS
Code SHA `bdcce5d` stamped (runner setup commit). Analysis SHA `33f389f` stamped (committed BEFORE brief per Phase 5.5 reproducibility requirement). ITERATION_LABEL=v3-014. RiskV2Config(zscore_threshold=2.0, adx_threshold=25.0). All other parameters byte-identical to iter-v3/013.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FAILED-HYPOTHESIS
Implementation matches single-axis change. Single-axis discipline holds. **Hypothesis NOT SUPPORTED**: IS Sharpe +0.6593 = Δ −0.35 vs iter-v3/013's +1.0088. Per brief §4.4 row 5 (`EXPLORATION-NEGATIVE`): "IS Sharpe down > 0.10 AND non-bit-identical roster" — observed Δ −0.35 < −0.10, roster non-identical (153 vs 209). Saturation falsifier (IS trades 153 < derived threshold 167) PASS — gate fire-rate verifier confirms axis propagated. **NOT a NULL-RESULT** (distinguishing from iter-v3/012). The gate change took effect; the gate change just hurt the model.

### Checks 9-12: PASS

| # | Check | Status | Detail |
|---:|---|:---:|---|
| 9 | Symbol exclusion | PASS | `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` |
| 10 | Feature isolation | PASS | `features_v3` does not import `features` (v1) or `features_v2` (v2) |
| 11 | Forming-candle | PASS | Pre-flight staleness guard functioning per spec |
| 12 | Library pinning | PASS | Stack identical to iter-v3/008-013 (no version bumps) |

---

## EXPLORATION-Specific Methodology Notes

**LDO trade collapse 10 → 2 (-80%) is dominant OOS Sharpe collapse driver**. LDO ADX kills increased +58.5% (224 → 355, largest proportional). 2-trade sample (1W/1L) is statistically meaningless — exact-binomial 95% CI on 50% WR at n=2 is approximately [1.3%, 98.7%]. The OOS Sharpe Δ −1.83 attributes primarily to LDO's near-disappearance from the OOS trade roster.

**Largest negative OOS delta in v3 history (Δ −1.83)**. Mirrors iter-v3/013's Δ +1.11 in opposite direction at 1.65× magnitude. Brief §2.1 OOS_caveat correctly pre-registered: "the OOS [20, 25) bucket carried 61.48% of iter-v3/013 OOS PnL". P6 of brief §7 (20% probability) materialized — the low-probability adversarial outcome.

**OOS MaxDD doubled (12.47% → 25.15%, +12.68pp)**. Meaningful downside-profile deterioration. WR degraded on 3/3 symbols (BCH 41.9% → 35.0%, LDO 80.0% → 50.0% n=2 noise, TRX 43.2% → 42.1%).

**Saturation predictor parametrization PASSED** (Critic FINAL Rec 3 of iter-v3/013 worked). Predicted counterfactual_n_trades=139; observed IS=153; threshold ceil(1.2×139)=167. The 1.2× factor absorbed Optuna re-optimization variance (+14 trades) without false-triggering.

**3rd-consecutive-overshoot pattern broken**. Brief widened band [+0.50, +1.30] median +0.90 per Critic Rec 4 of iter-v3/013. Observed +0.6593 lands BELOW median, breaking the favorable-overshoot trend (010, 011, 013). The widening was appropriate for behavior-changing axes, but iter-v3/014 returned a NEGATIVE outcome rather than continuing the overshoot streak.

---

## QR Response Considered (Round 2)

QR Round 2 response at SHA `f96a9f3` addressed all 5 Round 1 clarifications. Critic accepts all dispositions.

### Disposition 1 — ADF demotion (ACCEPTED)
QR confirmed (a) 384 non-stationary cells concentrate in 2020-Q1 sparse-data months (n_obs < 200, ADF underpowered) and (b) V3_FEATURE_COLUMNS bit-identical to iter-v3/009 (informational-only inherit from iter-v3/013 Round 2 promotion). Check 5 demotes WARN → PASS (carry-forward).

### Disposition 2 — Catalog framing (ACCEPTED)
QR accepts (a) clean `EXPLORATION-NEGATIVE` per brief §4.4 row 5. Critic concurs:
- Trade roster non-identical (153 IS vs 209) — distinguishes from `NEGATIVE-no-effect` (which requires bit-identity)
- Axis propagated (saturation falsifier PASS, gate fire-rate increased on all 3 symbols)
- IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold
- All three §4.4 row 5 conditions met cleanly

Subtype proliferation cost reasoning is sound: `PROMISING-MECHANICAL` was justified at iter-v3/013 because trade-roster bit-identity was load-bearing for misattribution prevention. For iter-v3/014, no analogous load-bearing distinction exists. Asymmetric magnitude observation lives in catalog caveats, not in a new subtype.

### Disposition 3 — High-PBO cells (ACCEPTED)
QR confirmed (a) `n_high_pbo_cells_99 = 2` strict ≥0.99 cutoff (TRX/2025-10, TRX/2025-11) and (b) TRX/2025-Q4 carry-forward continues; no new 99-tail entries. BCH/2024-10 at 0.9868 below threshold, not counted.

### Disposition 4 — iter-v3/015 axis (ACCEPTED)
QR accepts (a) ADX threshold = 18 (looser direction) for iter-v3/015. Critic concurs strongly:
- Asymmetric magnitude (Δ OOS −1.83 = 1.65× iter-v3/013's +1.11) demonstrates ADX is one of the most impactful single-axis variations tested in v3 to date
- Cataloguing only the tighter direction without testing the looser direction leaves the catalog with asymmetric understanding
- iter-v3/015 ADX=18 closes the ADX axis (regardless of outcome)
- Pre-committed disposition cannot be renegotiated post-hoc; new memory rule `feedback_adx_axis_asymmetric_v3.md` saves the pre-commit

### Disposition 5 — Trade-rate floor (ACCEPTED)
QR confirmed (a) catalog row records `oos_n_trades_60_below_130_floor` caveat and (b) verdict is purely IS-axis driven; OOS Sharpe +0.87 records as informational caveat. Bundle-level math (60 × 5 × 3-4 = 900-1200 OOS bundle trades) clears the 130-trade floor at CONFIRMATION; single-seed EXPLORATION underpowering is structural, not a methodology issue.

---

## Recommendations to QR

1. **iter-v3/015 axis MANDATORY = ADX threshold 18** (looser direction) for direction-asymmetry validation. Pre-committed per QR Clarification 4 disposition. The asymmetric magnitude (Δ OOS −1.83 vs iter-v3/013's +1.11 = 1.65× ratio) requires the symmetric-direction test to complete the catalog's understanding of the ADX axis. After iter-v3/015 completes, ADX axis is CLOSED for further EXPLORATION; iter-v3/016+ moves to a different axis regardless of iter-v3/015 outcome (low-vol floor 0.33, vol-scaling clip range [0.3, 1.0], or ±25% BTC band looser direction deferred since iter-v3/012). New memory rule `feedback_adx_axis_asymmetric_v3.md` saves this pre-commit and cannot be renegotiated post-hoc.

2. **iter-v3/014 catalog row captures**: NEGATIVE clean verdict, asymmetric magnitude caveat (`largest_negative_OOS_delta_in_v3_history = -1.83`), LDO 10→2 collapse caveat (-80% kill rate; OOS sample statistically meaningless at n=2), `oos_n_trades_60_below_130_floor` caveat (informational; OOS Sharpe +0.87 informational only), axis-saturation predictor PASS (153 < 167; 1.2× factor parametrization continues to work), `iter-v3/015_axis_mandated = ADX 20 → 18` per Critic Rec #1. The 5 caveats are explicit pre-commitments that travel with the catalog row to inform future bundling decisions.

3. **Process improvement**: ADX axis should not be tested at MORE than 25 (over-restriction confirmed at iter-v3/014); iter-v3/015 ADX=18 closes the symmetric direction; iter-v3/016+ moves to different axis regardless of iter-v3/015 outcome. The principle: when a single axis produces an asymmetric high-magnitude outcome (|Δ OOS| > 1.5σ of v3 history), the symmetric-direction test is mandatory to complete catalog coverage; further extreme-direction tests are NOT warranted because the marginal information gain has diminishing returns relative to coverage of unexplored axes (low-vol floor, vol-scaling clip, BTC band looser direction).

---

## Status

**OVERALL: EXPLORATION-NEGATIVE** (clean per brief §4.4 row 5).

Phase 8 may proceed. Diary entry catalogues NEGATIVE verdict + 5 caveats. Catalog row records iter-v3/014 entry with NEGATIVE verdict and `iter-v3/015_axis_mandated = ADX 20 → 18` pre-commit. New memory rule `feedback_adx_axis_asymmetric_v3.md` saves the pre-commit alongside the catalog row update.

Catalog count after iter-v3/014: **7 of 10 EXPLORATIONs**; **3 more required** before any CONFIRMATION can launch. Axis coverage: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 = 6 unique axis representations. iter-v3/015 ADX=18 will produce the symmetric-direction completion of gate-adx axis; iter-v3/016+ adds new axis representations (low-vol filter floor, vol-scaling clip range, or ±25% BTC band looser direction).

**End of FINAL Round 2 review.**

# Phase 7.5 Critic Review — iter-v3/114 — FINAL

OVERALL: EXPLORATION-NEGATIVE — Check 1 FAIL (no-cheating: `ldo_realvol_zscore_floor=0.30` hand-chosen, false brief provenance, no auditable IS-only temporal fence) compounded by Check 8 FAIL (registered surgical ~13% gate delivered as a ~59% broad LDO suppressor); the +0.66 OOS lift is a conceded thin-roster aggregate artifact.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-6 EXPLORATION slot #5 of 10). Checks 1, 2, 4, 5, 6, 8 are verdict-driving; Check 3 is informational.

## QR Response Considered (Round 2)

The QR's Round-2 response (`qr_response.md`) takes the position **STAND BY VERDICT** and concedes the PRELIMINARY in full — no new evidence, no new analysis script, no new backtest. I independently re-verified the decisive source claim against `analysis/iteration_v3-114/trigger_selection_synthesis.py`; the QR's traces are correct on every checkable point. The three clarifications resolve:

1. **Threshold-0.30 provenance (Check 1, decisive) → FAIL confirmed.** No committed EDA table or code path produced 0.30 as an optimization output. `trigger_selection_synthesis.py:323` is a literal hardcoded `chosen_thr = 0.30`; the S3 sweep grid is `np.linspace(min, max, 21)` and 0.30 enters it ONLY via `extra_thr` force-injection (docstring lines 132-133: appended "so the honest-classification lookup lands on it exactly"); S3's natural band-selector would have picked a different threshold. T3 sweeps the opposite `kill_HIGH` polarity at thresholds 1.12-1.75. The QR withdraws the brief's "T3 IS-only sweep" provenance as **false**. The QR concedes it cannot demonstrate from committed IS-only artifacts that 0.30 was placed on IS-only information: `s1_consolidated_ranking`, `t9_oos_coverage_annex`, and the A2 annex all call `load_059_ldo_roster("out_of_sample")` in the same atomic commit `d8a9725`, with no committed ordering fencing the hardcoding from the OOS-roster scripts; 0.30 was selected over strictly-IS-better wider thresholds in `[0.3331, 0.5240]` (which suppress 2 IS losers, `cf_wpnl_delta=+4.8694`, vs 0.30's 1 trade, `+2.3586`) and placed at the lower edge of the narrowest one-trade gap `(0.2694, 0.3126)`. Per `feedback_no_cheating.md` the QR declines to argue Check 1 to PASS. **Check 1 FAIL stands.**

2. **The "13% panel fire-rate" claim (Check 8) → FAIL confirmed.** The QR concedes the 13.0% figure is computed in no committed table — it appears only as hardcoded comment strings and the literal S4 row dict `"0.13 (thr=0.30)"`. The brief's surgicality argument — the stated reason `ldo_realvol_zscore` was admitted over `ldo_vs_btc_30d` (S4-disqualified for a 46-79% fire-rate) — was made on a base that does not exist. The production kill_LOW gate fired ~59% of the LDO candidate-candle space, inside the "near-constant off" regime S4 used to reject the alternative. **Check 8 FAIL stands.**

3. **OOS-lift attribution + per-symbol metric → QR concession matches the PRELIMINARY.** The QR will use `concentration_pct` from `comparison.csv` (TRX OOS +95.61%) as the single Phase-8 metric and disclaims `pct_of_total_pnl` (+189.64%) as the unstable near-zero-denominator column. The QR agrees the +0.66 aggregate OOS Sharpe delta is a thin-roster aggregate-arithmetic artifact, not an attributable LDO-kill-switch edge: 54/55 TRX OOS trades bit-identical to /060, the 5 surviving LDO OOS trades still net-negative (−7.39%), and +0.7991 is 3× the top of the EDA's own `S2_honest_classification.csv` band `[−0.05, +0.25]`.

The QR's response is honest, artifact-grounded, and offers no counter-argument. A false defense would have been a worse violation than an admitted error; the concession is the correct conduct. It does not rescue the iteration — a concession that Check 1 and Check 8 both FAIL produces EXPLORATION-NEGATIVE.

## Per-Check Status

### Check 1 — Look-Ahead Audit: FAIL

The `ldo_realvol_zscore` *trigger series* is past-only and clean (`risk_v3._build_ldo_realvol_lookup` applies `.shift(1)` before the rolling std; `_ldo_realvol_gate_fires` uses the strict `searchsorted(..., side="left") - 1` past-only as-of contract; byte-faithful to the EDA `_shared`). **The leak surface is the threshold `0.30`.** Per `feedback_no_cheating.md` ("verify EDA code is IS-only, don't trust the brief's prose"), the brief claims an IS-only calibration the committed code does not bear out: 0.30 is a hardcoded constant (not an optimization output); the brief's "T3 IS-only sweep" provenance is factually false; the OOS-roster trigger values were computed in the same atomic commit `d8a9725` with no committed ordering fencing the threshold choice from the OOS-window outputs; and 0.30 was selected over strictly-IS-better wider thresholds. There is no auditable temporal fence demonstrating 0.30 was placed on IS-only information, and the QR explicitly cannot rule out that the OOS-roster trigger distribution informed the placement. A hand-tuned scalar threshold whose IS-only provenance cannot be demonstrated, in a workflow governed by `feedback_no_cheating.md`, is a look-ahead FAIL — the burden of proof is on the artifacts, and the artifacts do not discharge it. The QR concedes. **FAIL.**

### Check 2 — Embargo Width: PASS

Required cross-cell purge gap = `(21 + 1) × 3 = 66`. `REQUIRED_GAP = 66`; the runner independently recomputed 66 and matched, per-symbol CV gap `184h (22 rows)`. The `e149e9d` walk-forward embargo fix is inherited unchanged — this iteration touched only `RiskV2Config` and `risk_v3.py`. Clean.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

`dsr.json`: DSR=0.0, PBO=0.1278, PSR=1.0, n_trials=315, n_eff=19. PBO clears <0.4. DSR/PSR are EXPLORATION-mode structural artifacts per `feedback_v3_dsr_mode_artifact.md`; only PBO is meaningful at EXPLORATION budget and it passes. Informational; does NOT trigger the verdict. At iter-v3/120 CONFIRMATION all three axes become hard BLOCK-triggering.

### Check 4 — IC Correlation: PASS (non-applicable)

Risk-management axis — zero feature families added. `V3_FEATURE_COLUMNS` reverts 22→14 (mandatory /113-closeout housekeeping). No new-vs-existing IC pair to evaluate. Non-applicable.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` present. At the IS-window-end month (2025-03) nearly all 14 features stationary at p ≈ 0; the only marginals recover True at the IS-end month; all-False early-history rows are warm-up sentinels. The 14 features are scale-invariant constructs. Clean.

### Check 6 — Pareto Dominance: PASS (non-applicable)

Not applicable to an EXPLORATION under the unified-ensemble architecture — `pareto_front.csv` not produced; `ensemble_summary.json` confirms `mode=exploration`, 3 seeds, outer=42 lineage. 10-seed Pareto validation is a CONFIRMATION concern (iter-v3/120).

### Check 7 — Reproducibility: PASS

Commit SHA stamped; explicit 14-element `feature_columns` list, never `None`; ensemble seeds literal in `ensemble_summary.json`; PnL spot-checks reconcile against the 2:1 ATR barrier geometry. The run is bit-reproducible. (Reproducibility — the run can be re-derived — and correctness — the run tested the registered hypothesis — are orthogonal; this check is the former and it passes; Check 8 is the latter and it fails.)

### Check 8 — Hypothesis-Implementation Alignment: FAIL

The brief Section 1 registered a "surgical ~13% fire-rate low-volatility-chop gate," with the Section 2.3 / S4 surgicality screen disqualifying the alternative trigger `ldo_vs_btc_30d` for its 46-79% "near-constant off-switch" fire-rate. Surgicality was the registered design property and the stated reason `ldo_realvol_zscore` was chosen. The implemented gate is not surgical: the production gate fired 842 times on LDO against `signals_seen=595` — ~59% of the LDO candidate-candle space, inside the 46-79% regime S4 used to disqualify the alternative. The "13% IS-panel fire-rate" was never computed in any committed table. The hypothesis as registered ("a surgical chop-gate that fixes LDO") was not what ran ("broadly turn LDO off"), and the gate did not fix LDO — the 5 surviving LDO OOS trades are still net-negative. A gate that suppresses ~59% of a chronically-losing symbol's signal space and leaves the residual net-negative is a degenerate near-universe-drop, not the surgical regime gate the brief registered. The QR concedes. **FAIL.**

## Disposition of the Three QE-Flagged Concerns

- **Concern 1 — OOS-lift attribution: confirmed an artifact.** 54/55 TRX OOS trades bit-identical to /060 (`feedback_v3_single_seed_frozen_baseline.md` frozen-baseline pattern); the 5 surviving LDO OOS trades still net-negative; the gate suppressed an LDO winner. Removing 6 LDO trades from a thin 3-symbol monthly-return series mechanically re-weights the aggregate Sharpe — a thin-roster arithmetic effect, not a discovered edge; it would not survive a multi-seed CONFIRMATION dissolving the frozen baseline.
- **Concern 2 — gate-design mismatch:** the Check 8 FAIL.
- **Concern 3 — no-cheating / look-ahead:** the Check 1 FAIL.

## Prediction-Miss Assessment

The brief pre-registered OOS +0.18, 80% interval `[−0.10, +0.45]`; actual +0.7991 — +0.35 above the upper bound. The EDA's own `S2_honest_classification.csv` predicted `[−0.05, +0.25]`; the realized is 3× the top of the EDA's own band. A result 3× above the EDA's own prediction, on a 5-trade OOS LDO residual, where the lift traces to aggregate re-weighting rather than the gate's named mechanism, is the signature of a fragile artifact. The engineering report's mechanical Section-8 classification of EXPLORATION-PROMISING is overridden: a pre-registered-criteria PASS computed on top of a Check-1 no-cheating FAIL and a Check-8 mechanism mismatch cannot stand as PROMISING.

## Recommendations to QR

This iteration is NOT salvageable; the verdict is final. Process-level fixes for FUTURE iterations:

1. **Catalogue iter-v3/114 as EXPLORATION-NEGATIVE with an explicit no-cheating Check-1 FAIL.** The LDO-realvol kill_LOW gate does NOT advance to the iter-v3/120 CONFIRMATION bundle. The Phase-8 diary must record this as a NEGATIVE *and* a research-integrity failure (the false brief provenance), not merely NEGATIVE-no-effect: the headline +0.80 OOS was a thin-roster aggregate artifact, and the threshold whose lift the brief claimed was hand-placed with an unauditable IS/OOS fence. RiskV3 primitive 9 (the regime kill-switch) is now NEGATIVE/INERT across three data points (iter-v3/022 TRX, iter-v3/074 TRX, iter-v3/114 LDO) — record the kill-switch primitive as a closed path absent genuinely new, properly-fenced IS-only counterfactual evidence.

2. **Brief-parameter-provenance discipline — a hard pre-registration rule.** Every tuned scalar parameter cited in a brief must name the exact committed table that produced it, and that named source must actually produce the value when run — a hardcoded constant with an `# IS-calibrated` comment is not a calibration, and a value force-injected into a sweep grid via an `extra_thr` argument is not a sweep output. For any hand-chosen threshold, the brief must (i) declare it hand-chosen, not laundered as a sweep result, and (ii) demonstrate IS-only calibration with an auditable temporal fence: the IS-only selection rule, its explicit objective, and its selecting table must be committed in a commit (or clearly-ordered script step) that demonstrably runs before any script touches an OOS-window file. The iter-v3/114 EDA collapsed the IS-only selector and the OOS-roster annex into one atomic commit — that destroys the fence. Future risk-axis EDAs that select a scalar threshold must split: IS-only threshold-selection committed first; the FENCED OOS coverage annex in a separate later commit.

3. **iter-v3/115 direction.** Cycle 6 has EXPLORATION slots #6-#10 (iter-v3/115-119) remaining before the iter-v3/120 CONFIRMATION. iter-v3/115 should (a) abandon the RiskV3-primitive-9 kill-switch family — three NEGATIVE/INERT data points is sufficient to close it; (b) per `feedback_v3_structural_over_knob_exploration.md`, prefer a structural axis (NEW feature family, NEW model architecture, NEW labeling) over another risk-primitive knob; and (c) attribute any per-symbol axis on the target symbol's own roster, never on the portfolio aggregate Sharpe — the single-lineage frozen-baseline pattern means the aggregate OOS Sharpe delta of a per-symbol change is dominated by the unchanged non-target symbols' arithmetic, and a per-symbol axis evaluated on the aggregate will keep manufacturing artifactual headlines like /114's +0.80.

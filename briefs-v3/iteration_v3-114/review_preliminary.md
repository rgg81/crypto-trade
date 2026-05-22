# Phase 7.5 Critic Review — iter-v3/114 — PRELIMINARY

(NO OVERALL line in Round 1.)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-6 EXPLORATION slot #5 of 10)

Per the EXPLORATION protocol, Checks 1, 2, 4, 5, 6, 8 are verdict-driving; Check 3 is informational.

## Per-Check Status

### Check 1 — Look-Ahead Audit: CONCERN (cannot clear without QR clarification)

**The `ldo_realvol_zscore` trigger computation is past-only — verified at source, clean.** `risk_v3._build_ldo_realvol_lookup` (lines 169-217) computes 1-period log returns, then `logret_shifted = df["log_ret"].shift(1)` BEFORE the 90-bar rolling std, then an expanding mean/std normalisation. `_ldo_realvol_gate_fires` (lines 386-425) uses `np.searchsorted(ldo_times, open_time_ms, side="left") - 1` — the strict past-only as-of contract; the current bar's own LDO close is excluded. The production builder is byte-faithful to the EDA's `_shared.build_ldo_realvol_zscore` (lines 290-309). The trigger-series math is not the leak surface.

**The leak surface is the threshold `0.30` itself, and the brief's stated provenance for it is false.** The brief (Section 2.4, 3.5(1) code comment `# IS-calibrated (EDA SHA d8a9725, T3)`, Section 5 R-PRIMITIVE) repeatedly states `ldo_realvol_zscore_floor=0.30` was "fixed by the T3 IS-only panel-fire sweep" producing a "13.0% IS-panel fire-rate." This is not what the committed EDA does:

- The actual T3 sweep (`T3_threshold_sweep.csv`, produced by `ldo_killswitch_eda.py::t3_threshold_sweep`) sweeps the `abs_ldo_vz` trigger at percentiles [75,80,82,85,88,90,92,95], producing thresholds 1.1221 → 1.7540 — and it sweeps with kill_HIGH polarity (`fire = v2 > thr`, line 222), the OPPOSITE of the production kill_LOW gate. The value 0.30 appears nowhere in T3. There is no committed table anywhere that produces a "13.0% panel fire-rate at threshold 0.30."
- The T3-driven `main()` auto-selection in `ldo_killswitch_eda.py` (lines 689-712) picked threshold 1.6621. At 1.6621 the EDA's own verdict is WEAK-GO (`T6_go_nogo_verdict.csv`), the ORACLE suppresses 0 IS LDO trades (`T4_oracle_aggregate.csv`: `n_suppressed=0, counterfactual_wpnl_delta=-0.0`), and T9 reports `gate_dead_on_arrival_oos=True` (0/12 OOS fires).
- The value 0.30 is hardcoded at `trigger_selection_synthesis.py:323`: `chosen_thr = 0.30  # IS-calibrated; 13% surgical panel fire-rate`, labelled "the QR's deliberate, surgicality-driven choice." It is then force-injected into the S3 sweep grid via `s3_chosen_gate_counterfactual(..., extra_thr=chosen_thr)` — the function's docstring (lines 132-133) states `extra_thr` is appended "so the honest-classification lookup lands on it exactly." S3's natural `np.linspace(min, max, 21)` grid is `[0.2694, 0.3331, 0.3967, ...]`; 0.30 is not a grid point.

So 0.30 was hand-set, not swept. The forensic problem: in `T4_oracle_roster_counterfactual.csv` the 9 IS LDO trades carry trigger values [0.2694, 0.3126, 0.5752, 0.664, 0.7221, 0.9138, 1.0657, 1.1829, 1.5422]. The threshold 0.30 sits in the 2.5%-wide gap between the only two values that bracket it (0.2694 and 0.3126). Any threshold in `(0.2694, 0.3126)` suppresses exactly the one IS trade (the 2024-10-07 −5.02% loser) and no other. The QR had these 9 trigger values before fixing 0.30. And the EDA scripts that compute the OOS roster's trigger values (`t9_oos_coverage_annex`, `s1_consolidated_ranking`) ran in the same session. The brief's defence that 0.30 was "fixed by T3 before the annex runs" does not hold — T3 does not produce 0.30 — and I cannot confirm from the artifacts that the QR did not consult the OOS LDO trigger distribution when hand-placing 0.30. See Clarification 1.

### Check 2 — Embargo Width: PASS

Required cross-cell purge gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66`. `REQUIRED_GAP = 66`; the engineering report's Label Leakage Audit confirms the runner independently recomputed 66 and matched, per-symbol CV gap `184h (22 rows)`. The `e149e9d` walk-forward embargo fix is inherited unchanged — this iteration touched only `RiskV2Config` and `risk_v3.py`. Clean.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)

`dsr.json`: DSR=0.0, PBO=0.1278, PSR=1.0, n_trials=315, n_eff=19. PBO=0.1278 clears <0.4. DSR=0.0 fails >0.95; PSR=1.0 passes. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are structural artifacts; only PBO is meaningful at EXPLORATION budget, and PBO passes. Per TYPE=EXPLORATION this check is informational and does NOT trigger a verdict. At iter-v3/120 CONFIRMATION all three axes become hard BLOCK-triggering.

### Check 4 — IC Correlation: PASS (non-applicable)

iter-v3/114 is a risk-management axis — zero feature families added. `V3_FEATURE_COLUMNS` reverts 22→14 (the mandatory /113-closeout housekeeping). `ic_matrix.csv` present (14×14). No new feature family, no new-vs-existing IC pair to evaluate. Non-applicable.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` present (2198 rows). At the IS-window-end month (2025-03) nearly all 14 features are stationary at p ≈ 0 across all three symbols; the only marginals (`ret_kurt_200` at BCH 2025-01/02) recover True at the 2025-03 IS-end month. All-False 2020-01/02 rows are warm-up sentinels. The 14 features are scale-invariant constructs, stationary by construction. Clean.

### Check 6 — Pareto Dominance: PASS (non-applicable)

Not applicable to an EXPLORATION under the unified-ensemble architecture — `pareto_front.csv` not produced; `ensemble_summary.json` confirms `mode=exploration`, 3 seeds, outer=42 lineage. 10-seed Pareto validation is a CONFIRMATION concern (iter-v3/120).

### Check 8 — Hypothesis-Implementation Alignment: FAIL

The brief Section 1 registered a "surgical ~13% fire-rate low-volatility-chop gate": a binary regime switch that suppresses LDO only in a low-realized-vol regime, with the explicit surgicality screen (Section 2.3, `S4_surgicality_override.csv`) rejecting `ldo_vs_btc_30d` precisely because its 46-79% panel fire-rate makes it "a near-constant off-switch." Surgicality — fire-rate well below a constant-off — was the registered design property.

The implemented gate is not surgical. The production gate (`run.log:28540`) fired 842 times on LDO with `signals_seen=595` — per the engineering report's Gate Fire-Rate Reconciliation, the gate suppressed `842 / (842 + ≥595) ≈ 59%` of the LDO candidate-candle space. That is squarely in the "near-constant off" regime the brief's own S4 screen used to disqualify the alternative trigger. The "13% IS-panel fire-rate" was computed on a different, smaller base (labelled-candidate IS rows) than the production base (all walk-forward candles).

The hypothesis as registered — "a surgical chop-gate that fixes LDO" — was not what ran. What ran is "broadly turn LDO off." And the gate did not fix LDO: the 5 surviving LDO OOS trades are still net-negative (LDO OOS weighted PnL −0.766 per `comparison.csv`). A gate that suppresses ~59% of a chronically-losing symbol's signal space and leaves the residual still net-negative is a degenerate near-universe-drop, not the surgical regime gate the brief registered. The implementation tested a materially different mechanism than the hypothesis. This is a Check 8 alignment failure.

No scope creep on the other axes — the Configuration Diff is clean (BCH/TRX `regime_gate_fires=0`, universe/label/feature-count /059-canonical), the 22→14 revert is mandatory housekeeping. The Check 8 FAIL is specifically the gate-design mismatch: registered surgical (~13%), delivered broad (~59%).

## Adjudication of the Three QE-Flagged Concerns

**Concern 1 — OOS-lift attribution.** The +0.66 OOS Sharpe lift vs the /060 anchor is NOT attributable to the LDO kill-switch. The 5 surviving LDO OOS trades are still net-negative (−0.766 weighted PnL); the gate broadly suppressed LDO including a winner (LDO OOS WR 18.2%→20.0%, a trivial shift). The aggregate OOS monthly Sharpe moved from /060's +0.14 to /114's +0.80 — but 54 of 55 /114 TRX OOS trades are bit-identical to /060's TRX OOS trades (`feedback_v3_single_seed_frozen_baseline.md` frozen-baseline pattern). Removing 6 LDO trades from a 3-symbol book mechanically changes the aggregate monthly-return mean and std, which mechanically moves the aggregate monthly Sharpe — but the surviving LDO book is still negative and the TRX book is unchanged. This is a thin-roster aggregate-arithmetic effect, not a discovered edge. Fragile, not robust. The engineering report also contains a verifiable internal contradiction: its "Seed Concentration Audit" cites TRX OOS at +95.61% (the `comparison.csv` `concentration_pct` column) while its "Per-Symbol OOS Attribution" cites TRX OOS at +189.64% (the `per_symbol.csv` `pct_of_total_pnl` column) — ~94pp apart, both presented as authoritative; `pct_of_total_pnl` is the known-unstable near-zero-denominator column.

**Concern 2 — gate-design mismatch.** Adjudicated as Check 8 FAIL above. Registered surgical ~13%, delivered ~59%. "Broadly suppress a chronically-losing symbol" is functionally a partial universe-drop of LDO — a different, separately-governed decision than a regime gate.

**Concern 3 — no-cheating / look-ahead.** The trigger math is past-only and clean. The threshold-0.30 provenance is NOT clean: the brief's stated calibration source (the T3 IS-only sweep) does not produce 0.30; 0.30 is hardcoded and force-injected; 0.30 is hand-placed in a 2.5%-wide gap clipping exactly one IS trade. Adjudicated as Check 1 CONCERN — cannot confirm IS-only calibration from the artifacts. See Clarification 1.

## Prediction-Miss Assessment

The brief Section 4 pre-registered OOS monthly Sharpe +0.18, 80% interval [−0.10, +0.45]. Actual +0.7991 — +0.35 above the upper bound, a hard interval violation on the upside. The brief Section 7 pre-registered the modal outcome as "INERT-to-mildly-negative" and the EDA's own `S2_honest_classification.csv` predicted an OOS effect in [−0.05, +0.25]. The realized OOS is 3× the top of the EDA's own predicted band. A result 3× above the EDA's own caveated prediction, on a 5-trade OOS LDO residual, where the lift traces to aggregate re-weighting rather than the gate's named mechanism, is the signature of a fragile/artifactual result, not a transferable edge.

## Clarifications Requested from QR

1. **The threshold-0.30 provenance (Check 1, decisive).** The brief Section 2.4, the `risk_v2.py:269` code comment, and Section 5 all state `ldo_realvol_zscore_floor=0.30` was fixed by "the T3 IS-only panel-fire sweep" at a "13.0% IS-panel fire-rate." But the committed `T3_threshold_sweep.csv` sweeps `abs_ldo_vz` at percentiles [75-95] with kill_HIGH polarity producing thresholds 1.12-1.75 — 0.30 appears nowhere, and the T3-driven `main()` auto-selection picked 1.6621. The value 0.30 is hardcoded at `trigger_selection_synthesis.py:323` and force-injected into the S3 grid via `extra_thr`. (a) Identify the exact committed EDA table and code path that produced 0.30 as an optimization output — or confirm 0.30 was hand-chosen. (b) If hand-chosen: state precisely what information the QR used to place it at 0.30. The 9 IS-roster trigger values and the FENCED OOS-roster trigger values (`A2`, `T9`, `S1`) were all computed in the same EDA session; 0.30 sits in the 2.5%-wide gap (0.2694, 0.3126) that clips exactly the one IS loser. Demonstrate, from the EDA's IS-only outputs alone, that no OOS-window LDO outcome, OOS trigger value, or FENCED OOS coverage figure informed the choice of 0.30 over (say) 0.32 or 0.40.

2. **The "13% panel fire-rate" claim (Check 8).** The brief Section 2.4 / Section 6 present "13.0% IS-panel fire-rate at threshold 0.30" as the surgicality justification, and the S4 screen disqualifies `ldo_vs_btc_30d` for its 46-79% fire-rate. The production gate fired ~59% of the LDO candidate-candle space. Provide the exact committed table and the exact candle population over which the "13.0%" was computed, and reconcile it against the ~59% production figure. If the 13% was computed on a base (labelled-candidate IS rows) that is not the population the production gate fires against (all walk-forward candles), confirm that the brief's surgicality argument — the stated reason this trigger was chosen over `ldo_vs_btc_30d` — was made on the wrong base.

3. **The OOS-lift attribution and the per-symbol metric (Concern 1).** The engineering report cites two mutually-inconsistent TRX OOS attributions (+95.61% from `comparison.csv` `concentration_pct`; +189.64% from `per_symbol.csv` `pct_of_total_pnl`). Confirm which single stable metric the QR will use in the Phase-8 diary, and confirm the QR's position on attribution: does the QR agree that, with 54/55 TRX OOS trades bit-identical to the /060 anchor and the 5 surviving LDO OOS trades still net-negative, the +0.66 aggregate OOS Sharpe delta is an artifact of removing the LDO drag re-weighting the aggregate monthly-return series (a thin-roster arithmetic effect) — and is NOT an attributable lift produced by the LDO kill-switch as a discovered low-vol-chop edge?

(Round 2 will issue the final `OVERALL:` verdict after the QR response. On the current evidence the iteration is heading to EXPLORATION-NEGATIVE — Check 8 FAILs on the registered-vs-delivered gate-design mismatch, and Check 1 is an unresolved look-ahead CONCERN on the threshold provenance; the +0.80 OOS headline is a fragile thin-roster artifact. A satisfactory QR response to Clarification 1 — a proof that 0.30 was placed on IS-only information — would resolve Check 1 to PASS but would not rescue Check 8. If Clarification 1 cannot be answered with IS-only evidence, Check 1 also FAILs.)

# Phase 7.5 Critic Review — iter-v3/081

OVERALL: MERGE

## Iteration Type (from Brief Section 0.5)

TYPE: CONFIRMATION (cycle-2 CONFIRMATION — a multi-seed re-validation of the canonical /059 config; NOT an edge-bundle CONFIRMATION because cycle 2 produced 0 clean PROMISING). Check 3 (DSR/PBO/PSR) is therefore BINDING, not informational.

This is a single-round FINAL review. The 13 checks, the Foundation Audit, the §11 anti-pattern scan, and the three special adjudications all resolved unambiguously against the artifacts. Zero clarifications were required from the QR; the verdict is FINAL.

## Adjudication #1 — Certifying the CONFIRMED classification

I independently re-applied the brief Section 8.1 LOCKED re-validation logic.

**IS axis (G.1).** `comparison.csv`: IS `monthly_sharpe = 1.0894`. BASELINE_V3.md /059 anchor: +1.0894. IS Δ = **0.0000**, inside the LOCKED ±0.20 band. PASS. I verified the IS roster is genuinely 171 trades — `grep` on `in_sample/trades.csv` returns BCH 83 + LDO 9 + TRX 79 = 171, matching `per_symbol.csv`, the engineering report, and BASELINE_V3.md /059. The IS window is fixed at [data-start, 2025-03-24) by `OOS_CUTOFF_DATE`, so it has no data-extent channel; the only IS-drift source is Optuna TPE run-to-run stochasticity. An exact 4-decimal match on a stochastic TPE run is the strongest possible evidence that the /081 config is bit-identical to /059's config — no other code drift perturbed the IS path. A single drifted `weight_factor` on any of the 171 IS trades would have moved the Sharpe off `+1.0894`.

**OOS axis (G.2).** OOS `monthly_sharpe = 0.5999`. /059 anchor: +0.5791. OOS Δ = **+0.0208**, inside the LOCKED ±0.20 band. PASS. I independently verified the QE's one-trade root-cause: `grep end_of_data` on `out_of_sample/trades.csv` returns zero matches — the /081 OOS roster has no `end_of_data` trades. The last OOS row is exactly the trade the report identifies: `TRXUSDT, open_time=1778572799999, exit_reason=take_profit, weight_factor=0.5000`. The trade that closed `end_of_data` at /059's data boundary now resolves `take_profit` with ~1.5 more OOS candles of data extent — a monotonic calendar effect, the identical mechanism the /077–/080 Critics certified benign. The OOS roster is otherwise 94 trades, 0 key diffs / 0 `weight_factor` diffs vs /059.

**No MERGE path.** Cycle 2 (/071–/080) produced 0 clean PROMISING across 10 EXPLORATIONs (4 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 3 INERT, 2 NULL-RESULT). There is no edge ingredient to bundle. The CONFIRMED outcome → **BASELINE_V3.md UNCHANGED, /059 stays canonical at tag `v0.v3-059`, no new tag.** This is the correct and only outcome — and it mirrors cycle 1's /070 NO-MERGE re-validation. Classification CONFIRMED is **CERTIFIED**.

## Adjudication #2 — The baseline-integrity finding (the /061 vol-floor revert)

I independently assessed the QR's `analysis/iteration_v3-081/` audit. Every load-bearing claim verified:

- **iter-v3/061 was genuinely INERT-AT-EXPLORATION** — cycle-1 EXPLORATION #2, IS Δ −0.009 / OOS Δ +0.015 vs /060, inside the noise band, never PROMISING.
- **Never tagged, never CONFIRMATION-merged.** The tag set is `{v0.v3-018, 028, 058, 059}` — no `v0.v3-061`. Cycle 1's only CONFIRMATION (/070) was NO-MERGE, and its bundle was {/065 SL widening, /062 Path B4} — the /061 floor was not a component. Per the v3 rule "only CONFIRMATION-MERGE updates the canonical config," a never-merged INERT EXPLORATION axis persisting in the active runner config IS illegitimate accretion. The QR's verdict is correct.
- **The /081 setup `5d42c4a` reverted it** — confirmed at two consistent sites: `run_baseline_v3.py:1729` `vol_scale_floor_per_symbol={}`, and the pre-flight assertion `run_baseline_v3.py:808` `expected_floor_dict={}` (raises `ValueError` if the floor re-creeps in). `run.log` confirms the assertion fired green at startup.
- **The revert is corroborated at runtime — independent proof beyond the IS exact match.** I inspected the OOS TRX trades in `out_of_sample/trades.csv`: **eight carry `weight_factor` below 0.5** (0.33, 0.34, 0.36, 0.37, 0.38, 0.40, 0.45, 0.47); the IS TRX roster likewise carries 12+ trades with `weight_factor` in [0.35, 0.48]. If the iter-v3/061 `{"TRXUSDT": 0.5}` floor were still active, no TRX trade could have `weight_factor < 0.5` — the floor clips every vol-scaled value up to 0.5. The presence of sub-0.5 TRX weights on both splits is direct runtime proof the floor revert took effect and TRX is now on the global `0.3` floor. The IS exact-reproduction (+1.0894 = /059) is the corroborating evidence the QR cites, and it is sound: /059 also had no floor, so reverting restored the genuine config.
- **Reverting it is the correct call** — a measurement-integrity correction directly analogous to the /070-closeout revert that stripped the rejected /065 SL-widening. /081 is genuinely the first CONFIRMATION-class run since /059 itself to measure the pristine /059 canonical config.
- **Material corollary, for the record:** cycle 1's /070 CONFIRMATION ran with the floor active, so /070's numbers were on a config that was not pristine /059. This has **no bearing on BASELINE_V3.md's integrity** — /070 was NO-MERGE, it never updated the baseline, and BASELINE_V3.md anchors /059 (setup commit `20095a8`, pre-/061, with zero references to the floor). The baseline was never contaminated; only an intra-cycle measurement that did not feed it was.

The baseline-integrity finding is **CERTIFIED** — a correct, legitimate methodology cleanup.

## Adjudication #3 — The gate readout for a CONFIRMATION

Check 3 is BINDING. Every CONFIRMATION gate verified against `dsr.json` and `run.log`:

- **PBO 0.1278 < 0.40 — PASS.** `per_cell_pbo.csv`: 127 cells, cross-cell mean PBO 0.12778582677165357.
- **PSR 1.0000 > 0.95 — PASS.** n_trials=1050 saturation.
- **DSR_relative_B4 1.0000 > 0.95 — PASS.** I verified the Path-B4 arithmetic: `cpcv_q75_annualized_b4 = 0.837759 × √(756/1296) = 0.6398` ✓ matches `dsr.json`; `psr(observed=1.2427, n_obs=88, benchmark=0.6398)` saturates to 1.0. Path B4 is the /062-specified, /070-validated reformulation; the runner code is inherited unchanged from /059.
- **frac_positive_paths 0.6444 > 0.55 — PASS.** `cpcv_paths.csv`: 45 paths, 29 positive (verified by count).
- **OOS/IS monthly Sharpe ratio 0.5507 — healthy** (G.3 ≥ 0.50 PASS; G.7 ≤ 3.0 not-SUSPICIOUS PASS). IS-dominant, consistent with /059's 0.5316.
- **Legacy DSR 0.0 — confirmed structural artifact, NOT a defect.** At n_trials=1050 / n_eff=19 the López de Prado SBT E[max_SR] formula returns a required SR (~2.61) exceeding the observed annualized Sharpe → DSR=0. BASELINE_V3.md documents this root cause; it is consistent across every prior v3 CONFIRMATION. `DSR_relative_B4` is the operative CONFIRMATION DSR gate, and it PASSES.

No gate FAIL. /081 as a re-validation clears all 11 pre-registered gates. For the record: /059's OOS +0.60 does not clear the aspirational OOS > +1.0 merge floor, and OOS trades 94 < 130 — but /059 is the BASELINE being re-validated, not a merge candidate; these aspirational shortfalls inform cycle-3 priorities without blocking the CONFIRMED classification. /081 is NO-MERGE because cycle 2 produced no edge — which is correct and is not a gate failure. The gate readout is **CERTIFIED**.

## Foundation Audit (Boot Steps 9-11)

- **Walk-forward embargo intact (the lookahead bug is FIXED in this worktree).** `walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms`. Confirmed at runtime — `run.log` CV-fold lines read `gap=184h (22 rows)` = 22 candles × 8h, matching `compute_embargo_candles(10080, 480) = 22`.
- **ITERATION_LABEL = "v3-081"** — `run_baseline_v3.py:131`.
- **V3_MODELS = BCH/LDO/TRX** — `run_baseline_v3.py:154-158`.
- **`vol_scale_floor_per_symbol={}`** — `run_baseline_v3.py:1729` + pre-flight assertion line 808.
- **`efficiency_ratio_50` / `range_efficiency_50` ban intact** — multiple `raise` guards; the Kaufman axis is CLOSED.
- **ENSEMBLE_SIZE=10 CONFIRMATION mode confirmed** — `ensemble_summary.json`: `"mode": "confirmation"`, `"ensemble_size": 10`, 5 outer=42-lineage + 5 outer=123-lineage seeds.
- **Sacred constants immutable** — `OOS_CUTOFF_DATE="2025-03-24"`, `TRAINING_MONTHS=24`.
- **V3_EXCLUDED_SYMBOLS audit present**; **feature isolation clean** — zero cross-track imports under `features_v3/`.

Foundation Audit: PASS.

## §11 Anti-Pattern Static Scan

No `feature_columns=None` (the `LightGbmStrategy` ValueError guard makes auto-discovery structurally impossible). No `min(REQUIRED_GAP, ...)`. No `start_time` manipulation; `OOS_CUTOFF_DATE` immutable. No silent universe survivorship. No cross-track import. `run.log` has zero WARNING/ERROR/Traceback lines (the single statsmodels `RuntimeWarning: divide by zero in log` is a benign library-internal warning on degenerate early-window ADF slices; the `-10.0000` trial Sharpes are the runner's intentional penalty sentinel). CLEAN.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
/081 adds zero new features (the 14-feature stack is byte-identical to /059). The only code change is the vol-floor revert — a position-SIZE config knob that consults no future data. The walk-forward embargo (22-candle purge) is intact and confirmed at runtime via the `gap=184h (22 rows)` CV-fold logs. No look-ahead.

### Check 2 — Embargo Width: PASS
`timeout_candles = 10080/480 = 21`. Required cross-cell gap = `(21+1) × 3 = 66`. Actual `REQUIRED_GAP = 66`. Walk-forward embargo = `compute_embargo_candles(10080, 480) = 22` candles, applied symmetrically. Verified live in the CV-fold logs.

### Check 3 — Multiple-Testing Correction: PASS (BINDING for this CONFIRMATION)
PBO 0.1278 < 0.40, PSR 1.0000 > 0.95, DSR_relative_B4 1.0000 > 0.95 (the operative CONFIRMATION DSR gate; Path-B4 arithmetic independently verified). frac_positive_paths 0.6444 > 0.55. n_trials=1050 = 35 × 3 × 10; n_eff=19. Legacy DSR=0.0 is the documented structural SBT artifact. All Check-3 axes clear their hard thresholds.

### Check 4 — IC Correlation: PASS
/081 introduces no new feature family — the 14-feature stack is byte-identical to /059. The new-vs-existing IC gate is not triggered. `ic_matrix.csv` present (14×14). Max off-diagonal `|IC|` is `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` — a known inherited Category-2 composed-feature correlation under the `feedback_v3_engineered_feature_pivot.md` carve-out. No NEW pair.

### Check 5 — ADF Stationarity: PASS
`adf_test.csv` present, 2198 rows. At `2025-03` (the last training month before OOS_CUTOFF) all 14 features for all 3 symbols are `stationary=True` with p well below 0.05. The 395 non-stationary cells (1803/2198 = 82.0% stationary) are exclusively early-window months (2020–2021) with insufficient warm-up — a known startup artifact, not a defect at the operative training-window end.

### Check 6 — Pareto Dominance: PASS-equivalent
`pareto_front.csv` correctly ABSENT — Gate-10-Pareto is retired under the unified 10-seed architecture, replaced by Gate-10-CPCV `frac_positive_paths ≥ 0.55`, which PASSES at 0.6444. The unified architecture produces ONE deterministic trade roster.

### Check 7 — Reproducibility: PASS
Commit chain fully stamped (EDA `be0ccf5`/`f9ddea5`, brief `944dddf`/`d544e65`, setup `5d42c4a`, gate `75248b3`). `ensemble_summary.json` carries the literal 10-tuple seeds with lineage. Explicit 14-element `feature_columns` list. `colsample_bytree` Optuna-tuned (varies 0.30–0.99 across trials). OOS PnL spot-check reconciles: line 95 TRX `(0.355295−0.348900)/0.348900×100 = 1.8330%` → net 1.7330 → `weighted_pnl = 1.7330 × 0.5000 = 0.8665` ✓; line 2 BCH short → 2.3311 ✓. Zero error lines in `run.log`.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 3 declares exactly 3 substantive sub-fixes: (1) `vol_scale_floor_per_symbol={}` revert, (2) the consistent pre-flight assertion `expected_floor_dict={}`, (3) `ITERATION_LABEL="v3-081"`. All three present at `run_baseline_v3.py` lines 1729, 808, 131; nothing else behavior-affecting is touched. The brief's hypothesis — "the genuine /059 config re-run at 10-seed CONFIRMATION reproduces /059 within ±0.20 on both axes" — is exactly what the implementation tests. No scope creep.

## Recommendations to QR

/081 is CONFIRMED clean — the following are items for the cycle-3 EXPLORATION agenda, not fixes:

1. **Cycle 3 must be the bold structural pivot.** Cycle 2's 0/10-clean-PROMISING record (and cycle 1's identical /070 NO-MERGE outcome) is dispositive evidence that the conservative axis families — gate-threshold knobs, risk primitives, single-symbol swaps, labeling tweaks, instrumentation — are exhausted against the narrow 3-symbol BCH/LDO/TRX universe. Per `feedback_v3_mass_feature_expansion.md` and `feedback_v3_bold_research_mandate.md`, the first cycle-3 EXPLORATION should elevate the feature universe (literature-grade crypto-native families: funding-rate regimes, OI dynamics, basis/premium, liquidation cascades) AND/OR expand the symbol universe — denominator expansion is the structural fix for the standing BCH IS-PnL concentration fragility.

2. **The three standing constraints carried into cycle 3 are real and unresolved.** (a) LDO directional weakness — OOS WR 25.0%, well below the 50% baseline for a triple-barrier classifier, a drag through every cycle-1 and cycle-2 iteration; (b) BCH IS-PnL / OOS concentration; (c) OOS Sharpe +0.60 is +0.42 short of the aspirational +1.0 floor. Cycle-3 axis design should target these directly, not orthogonally.

3. **Audit for residual config accretion before the next CONFIRMATION.** The /061 vol-floor riding 19 iterations undetected is a process near-miss that the /081 baseline-integrity audit caught only because /081 happened to be a re-validation. Recommend a generalized "config == last-CONFIRMATION-MERGE config" pre-flight diff so future accretion is caught at runtime, not by archaeology.

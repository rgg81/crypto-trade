# Phase 7.5 Critic Review — iter-v3/110 — PRELIMINARY

(NO OVERALL line in Round 1.)

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION (Cycle 6, EXPLORATION #1 of 10; iter-v3/120 is the mandatory CONFIRMATION).

Per the EXPLORATION protocol and `feedback_v3_dsr_mode_artifact.md`, Checks 1, 2, 4, 5, 6, 8 are scored for verdict; Check 3 (DSR/PSR/PBO edge thresholds) is informational only at single-seed/35-trial EXPLORATION budget.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

iter-v3/110's only intended `src/` change is a universe swap; no feature, label, or model code was edited (verified by reading `run_baseline_v3.py` — `V3_FEATURE_COLUMNS` asserted to be exactly the 14-feature /059 stack, `label_timeout_minutes=10080`, `atr_multipliers_for_symbol` returns the default `(2.0,1.0)` for all four symbols since `V3_ATR_MULTIPLIERS_PER_SYMBOL={}`). The walk-forward path is the `e149e9d`-fixed one — engineering report Section 4 confirms `train_end_ms = test_start_ms − embargo_ms` and every CV fold log records `gap=184h (22 rows)`. The first OOS trade `open_time` is 2025-03-28, four days after the immutable `OOS_CUTOFF_DATE=2025-03-24`; last IS trade `close_time` is 2025-02-16 — clean split, no boundary contamination. The Phase-2 EDA loader (`analysis/iteration_v3-110/_shared.py`) asserts `close_time < OOS_CUTOFF_MS (1742774400000)` per symbol both before and after labeling; the labeler is a verbatim copy of /109's /059-faithful triple-barrier; fold construction purges 22 candles. No contemporaneous-or-future data path found. Note: the look-ahead audit covers the *execution* layer and is clean; the Check 8 finding below concerns *which label* was trained, which is a hypothesis-alignment defect, not a leak.

### Check 2 — Embargo Width: PASS

Label timeout = 10080 min / 480 min per 8h candle = 21 candles. Required cross-cell gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88`. `validation_v3.py` line 76 carries `REQUIRED_GAP = (21 + 1) * 4 # 88` — correctly updated from the /059 value of 66. The runner's `_verify_label_leakage_gap()` (lines 1188-1209) recomputes `(timeout_candles+1) × len(V3_MODELS) = 88` and asserts equality with `REQUIRED_GAP`; `run.log` line 25 records the PASS. The per-symbol walk-forward embargo is 22 candles (`compute_embargo_candles(10080,480)`), applied symmetrically at every fold boundary. Actual ≥ required, symmetric. The stale parenthetical at `run.log` line 33 (`"(= (21+1)*3; ...3-sym /059 universe BCH+LDO+TRX...)"`) is a cosmetic copy-paste artefact in a diagnostic print string — the authoritative computed value at line 25 is 88 and is correct. Flagged for runner cleanup; not a computation error.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION — NOT verdict-triggering)

`dsr.json`: DSR=0.0, PSR=0.0 (both below the 0.95 threshold), PBO=0.1267 (clears the <0.4 gate). `n_trials=420`, `n_eff=17`. Per Section 0.5 TYPE=EXPLORATION and `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR at 35-trial/3-seed budget are structural regime artifacts, not edge-significance evidence — Check 3 axis FAILs do NOT trigger the verdict for an EXPLORATION iteration. Flagged here for record only. (Standalone observation: DSR=0.0/PSR=0.0 are unsurprising and uninformative here — the OOS book is net-negative, so there is no positive Sharpe for the deflation machinery to act on. `frac_positive_paths=0.622` clears the informational 0.55 CPCV gate, but with the headline OOS at −0.4455 this is not exculpatory.)

### Check 4 — IC Correlation: PASS (no new feature family — not applicable)

iter-v3/110 is a universe-only axis: zero new features. `V3_FEATURE_COLUMNS` is asserted by the runner to be exactly the /059 14-feature stack (`run.log` line 2). `ic_matrix.csv` is present (no automatic-FAIL trigger) and shows the known /059 intra-stack correlations — `regime_momentum_signed_5d` vs `vwap_dev_20` at 0.813 and vs `sym_vs_btc_ret_7d` at 0.714. These are pre-existing composed-feature correlations carved out at iteration time per `feedback_v3_engineered_feature_pivot.md` (composed features mechanically correlate with their primitives) and are not introduced by this iteration. There is no new-vs-existing pair to test. PASS by non-applicability.

### Check 5 — ADF Stationarity: PASS

`adf_test.csv` is the per-(symbol, feature, retraining-month) dump on the /059-identical 14-feature stack for the new universe: 3136 rows, 2531 stationary (80.7%), 605 not. The 605 `stationary=False` rows are dominated by early-history months where the symbol had insufficient candles for ADF to run — the runner (`run_baseline_v3.py` lines 1349-1413) assigns `stationary=False` with NaN statistic when the window is too short; that is a "could-not-test" sentinel, not a stationarity failure. At the IS-end window (2025-01/02/03), the only computed-test failures are `ret_skew_200` and `ret_kurt_200` on CRV (p 0.21-0.35) and `ret_kurt_200` on AAVE (p 0.064, borderline) — long-window distributional-moment features whose ADF p-value naturally hovers near the threshold; GRT and ADA have zero IS-end-window failures. Critically, no feature was added or modified — this is the /059 anchor stack, and the same ADF profile is the /059 baseline's accepted state. No new price-derived feature fails. PASS.

### Check 6 — Pareto Dominance: PASS (single-seed EXPLORATION — multi-seed Pareto not applicable)

iter-v3/110 ran in EXPLORATION mode (ENSEMBLE_SIZE=3, single outer-seed lineage=42). `ensemble_summary.json` confirms `mode=exploration, ensemble_size=3, seeds=[191664963,1662057957,1405681631]` all `lineage=outer=42`. Per the unified-ensemble architecture, EXPLORATION mode produces one deterministic roster and `ensemble_summary.json` replaces `pareto_front.csv` — there is no 10-seed Pareto front to evaluate, and none is required at EXPLORATION budget. No seed-selection defect. PASS by non-applicability (multi-seed Pareto is a CONFIRMATION-mode concern, correctly deferred to iter-v3/120).

### Check 7 — Reproducibility: PASS

Commit SHA `f7e564f` is stamped in the engineering report. The runner passes an explicit `feature_columns=list(features_for_symbol(symbol))` (line 1904) — never `None`, never auto-discovered; the `_verify_feature_columns` block asserts the 14-column stack. `ITERATION_LABEL` is `"v3-110"` (line 131). Inner ensemble seeds are literal (`ensemble_summary.json`). PnL arithmetic spot-check (independent re-computation): OOS row 2 (CRV short, entry 0.507000 → exit 0.449360): `pnl = (0.507000−0.449360)/0.507000×100 − 0.1 = 11.2688`, `weighted = 11.2688 × 0.55 = 6.1978` — matches the CSV exactly; 2:1 geometry consistent (SL 0.535820 ⇒ 1·ATR=0.028820, TP=entry−2·ATR=0.449360). IS row 2 (ADA long, 1.268100 → 1.384069): `pnl = 9.0451`, `weighted = 9.0451 × 0.34 = 3.0753` — matches; TP=1.268100+2·0.057985=1.384070 (1-tick rounding). IS sum +41.3249 vs `comparison.csv` +41.3253; OOS sum −28.2851 vs −28.2848 — sub-0.01 float drift. Reproducibility properties hold for the run as configured.

### Check 8 — Hypothesis-Implementation Alignment: FAIL

**The runner trained every /110 model on the wrong label. The brief's central "ONE axis" claim is false at the implementation level.**

The brief is emphatic that this is a single-axis iteration:
- Section 0.5: "the ONLY change vs the /059 baseline is the symbol universe `V3_MODELS`. Features ..., labeling (2:1 ATR triple-barrier, 21-candle timeout), the LightGBM architecture ... are all /059-identical."
- Section 3.2: "Labeling — UNCHANGED. 2:1 ATR triple-barrier (`atr_tp=2.0`, `atr_sl=1.0`), 21-candle (10080-min) timeout ... All /059-identical."
- Section 3 header: "**ONE axis: `V3_MODELS` is replaced wholesale.** No feature, label, model, or risk-gate change."

The implementation contradicts this directly. In `run_baseline_v3.py`:
- **Line 1917**: `_build_v3_model` `common_kwargs` carries `label_mode="trend_scanning"`.
- **Line 1918**: `trend_scan_grid=(5, 8, 13, 21)`.
- **Lines 1125-1133**: the runner's own pre-flight block *asserts* `label_mode == "trend_scanning"` and `raise RuntimeError` if it is anything else — i.e. the runner would have *refused to run* with the /059-canonical `triple_barrier` label.
- **`run.log` line 20**: the run executed with `label_mode (iter-v3/105): 'trend_scanning' grid=(5, 8, 13, 21)` — PASS.

This is the stale state left by iter-v3/105. The /105 closeout diary (`diary-v3/iteration_v3-105.md`) is explicit and repeated:
- Header / `**Decision**` line: "`label_mode` **REVERTS to `triple_barrier`** at the iter-v3/106 setup."
- Lines 322-330 ("The revert"): "`label_mode` **REVERTS to `triple_barrier`** at the iter-v3/106 setup — a **two-line config change** (`label_mode` and `trend_scan_grid` in `run_baseline_v3.py`). ... Only the `label_mode` value reverts ... **The trend-scanning label must not be re-proposed.**"

iter-v3/105 closed `trend_scanning` as **EXPLORATION-NEGATIVE** — it collapsed the IS fit (the /105 diary records IS monthly Sharpe **+0.2201** under the trend-scanning label, hard F2 fire). The mandated two-line revert to `triple_barrier` was never executed. iter-v3/106–109 were all NULL-AT-EDA (no backtest, no runner execution), so the un-reverted `label_mode` lay dormant and undetected for four iterations. **iter-v3/110 is the first iteration since /105 to actually execute `run_baseline_v3.py`** — and it executed it with the stale, known-NEGATIVE `trend_scanning` label.

Consequences:
1. **iter-v3/110 varied two variables, not one.** The intended universe swap AND the unintended `label_mode` carry-over. Attribution of the /110 result to the universe axis is destroyed — the headline IS +0.2942 is statistically indistinguishable from /105's trend-scanning IS-collapse figure (+0.2201), so the /110 result may be measuring the labeling drag rather than (or confounded with) the universe effect. The brief's Section 4 "Expected OOS Impact" reasoning assumes the /059 `triple_barrier` machinery — which is not what ran.
2. **The Phase-2 EDA and the backtest are on different label geometries.** `analysis/iteration_v3-110/_shared.py` (lines 21-25) explicitly replicates `labeling.label_trades` with `label_mode="triple_barrier"`. Every Section-2 table (T1-T10), the +0.25 raw gated proxy, the per-symbol gated books, the screen ranking — all computed under `triple_barrier`. The backtest trained models under `trend_scanning`. The EDA cannot be used to predict or interpret the backtest, which voids the brief's entire Section 2 → Section 4 inferential chain.
3. **The config-accretion guard did not catch it.** The `_canonical_v059` guard (lines 1032-1050) lists 11 knobs; `label_mode` is not among them. The guard that exists specifically to catch illegitimate config drift has a blind spot exactly where the drift occurred.
4. **The engineering report missed it.** The "Configuration Diff vs Baseline (/059)" table asserts "All other knobs ... /059-identical" — false. The QE did not flag the `label_mode` carry-over despite `run.log` line 20 recording it in plain text. The Phase 5.5 gate also missed it.

This is the textbook scope-creep / hypothesis-faking pattern Check 8 exists to catch: the iteration's registered hypothesis (a clean universe swap on the /059 `triple_barrier` baseline) was not the experiment that ran.

## Clarifications Requested from QR

1. **`label_mode` carry-over (Check 8).** `run_baseline_v3.py` line 1917 carries `label_mode="trend_scanning"`, the runner's own pre-flight (lines 1125-1133) asserts it, and `run.log` line 20 confirms iter-v3/110 trained on the trend-scanning label — while the brief Section 0.5/3.2 declares labeling "UNCHANGED / /059-identical / 2:1 ATR triple-barrier" and the /105 closeout diary mandated a two-line revert of `label_mode` to `triple_barrier` "at the iter-v3/106 setup." Three independent artifacts (runner config, runner assertion, run.log) agree the run used `trend_scanning`. Is there any artifact the Critic has not seen that shows iter-v3/110 in fact ran under `triple_barrier` — or do you concur that the /105-mandated revert was never executed and that iter-v3/110 therefore tested two variables (universe swap + a known-NEGATIVE label change) rather than the single registered axis? If you concur, state whether the universe-axis verdict can be salvaged from this run's artifacts at all, or whether iter-v3/110 must be re-run under `triple_barrier` before any universe conclusion can be drawn.

(Note for the QR: this is the only clarification, and the Critic's preliminary read is that Check 8 FAILs regardless of the response — the evidence is documentary and threefold-corroborated. The clarification exists solely to surface any counter-artifact the Critic could not see. Absent such an artifact, the Round-2 FINAL verdict will be **EXPLORATION-NEGATIVE** with the highest-priority concern being that the universe-axis result is uninterpretable due to the un-reverted `trend_scanning` label confound — and the process recommendation will be that the universe axis must be re-tested on a `triple_barrier`-corrected runner before cycle 6 can draw any symbol-selection conclusion. The brief's pre-registered Section 8 falsifiers did fire on the as-run numbers, so the iteration is NEGATIVE on its own criteria as well; but "NEGATIVE because the screened universe carries no edge" and "NEGATIVE because the runner trained on the wrong label" are different findings, and only a `triple_barrier` re-run can distinguish them.)

# iter-v3/110 — Cycle-6 EXPLORATION slot #1 — SYMBOL SELECTION: a signal-screened wholesale universe replacement (BCH/LDO/TRX → CRV/AAVE/GRT/ADA) — FILED EXPLORATION-NEGATIVE — LABEL CONFOUND — the runner trained every /110 model under the stale, known-NEGATIVE `trend_scanning` label (carry-over from iter-v3/105) instead of the brief-declared `triple_barrier`, so the run varied TWO variables; the universe-selection axis is UNRESOLVED, not closed, and must be cleanly re-tested under a `triple_barrier`-corrected runner at iter-v3/111

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-6 slot #1 of 10; iter-v3/120 is the mandatory CONFIRMATION) — ran a full Phase 1-8 (brief + backtest + Critic), classified at Phase 7.5
**Verdict**: **EXPLORATION-NEGATIVE — label confound.** iter-v3/110 was the cycle-6 first EXPLORATION, opening the post-/109 structural axis menu (`project_v3_cycle6_axis_menu.md`) with symbol selection. The QR ran a QR-led, EDA-backed wholesale universe replacement: `V3_MODELS` swapped from the saturated incumbent BCH/LDO/TRX to CRV/AAVE/GRT/ADA, a 4-symbol universe selected by a per-symbol, walk-forward-faithful feature→label predictive-signal screen (10 result tables T1-T10, committed `analysis/iteration_v3-110/`, EDA SHA `cfeaf34`). The Phase-6 backtest produced **IS monthly Sharpe +0.2942 / OOS monthly Sharpe −0.4455** (`reports-v3/iteration_v3-110/comparison.csv`). The Phase-7.5 Critic returned **OVERALL: EXPLORATION-NEGATIVE** — Check 8 (Hypothesis-Implementation Alignment) FAIL is the verdict driver: the runner trained every /110 model under `label_mode="trend_scanning"` (stale carry-over from iter-v3/105), NOT the brief-declared `triple_barrier`. The brief's central "ONE axis" claim is false at the implementation level; the run varied TWO variables — the intended universe swap AND the unintended labeling-geometry change — so the symbol-selection axis is not cleanly tested.
**Classification**: **EXPLORATION-NEGATIVE — label confound.** Per Critic Recommendation 1, this is recorded as a label-confound NEGATIVE: the universe-selection axis is **UNRESOLVED**, NOT closed. It is explicitly NOT "universe-no-edge NEGATIVE" — that would retire a structural axis on the cycle-6 menu on a false attribution. The CRV/AAVE/GRT/ADA screen is QR-led, EDA-backed, and was computed under `triple_barrier`; the axis *design* survives — only the as-run *measurement* is void.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION). An EXPLORATION never updates the baseline regardless of outcome; a NEGATIVE EXPLORATION does not advance.
**Branch**: `iteration-v3/110`

---

## 1. The axis — and why the run did not cleanly test it

iter-v3/110 is cycle-6 EXPLORATION slot #1. The axis is **symbol selection** — the first item on the post-/109 structural axis menu (`project_v3_cycle6_axis_menu.md`, user directive 2026-05-19): a wholesale replacement of the saturated BCH/LDO/TRX universe.

The /105→/109 convergent chain established that v3's 14-feature / 8h / BCH-LDO-TRX representation carries no IS-detectable directional signal *within that fixed scope* (the /109 permutation null: LightGBM real-label feature→label AUC 0.497, p=0.64). The /109 closeout was explicit that this null is **universe-specific** — a property of the BCH/LDO/TRX 8h joint feature→label distribution that does not transfer to a different universe. "A different universe" was the listed first structural escape (Option A). iter-v3/110 took that escape: the QR's committed IS-only EDA ran the exact /109 measurement (walk-forward, embargo-purged, 5-seed-averaged LightGBM) plus a per-symbol permutation null across 21 candidate symbols, reproduced the /109 null on the incumbents (T1/T10: BCH/LDO/TRX all at or below their permutation q50, p ≫ 0.10), and screened CRV/AAVE/GRT/ADA as a universe carrying measurably stronger IS feature→label signal. The brief (Section 2) is QR-led and EDA-backed; the axis design is sound.

**But the experiment that ran was not the experiment the brief registered.** The brief is emphatic that this is a single-axis iteration — Section 0.5 ("the ONLY change vs the /059 baseline is the symbol universe `V3_MODELS` … labeling … all /059-identical"), Section 3.2 ("Labeling — UNCHANGED. 2:1 ATR triple-barrier … All /059-identical"), Section 3 header ("**ONE axis: `V3_MODELS` is replaced wholesale.** No feature, label, model, or risk-gate change"). The runner contradicts this directly: `run_baseline_v3.py:1917-1918` carried `label_mode="trend_scanning"`, `trend_scan_grid=(5, 8, 13, 21)`, passed to every v3 model constructor; `run.log` line 20 records the run executed under `label_mode (iter-v3/105): 'trend_scanning' grid=(5, 8, 13, 21)`. **iter-v3/110 ran the universe swap on top of the stale, known-NEGATIVE `trend_scanning` label.**

## 2. The label confound — the chain of evidence

The confound is fourfold-corroborated (the QR independently re-verified all four artifacts in the Round-2 response; the Critic independently verified all three runner artifacts at source). The chain:

| # | Artifact | Location | What it shows |
|---|---|---|---|
| 1 | Runner config — `_build_v3_model` `common_kwargs` | `run_baseline_v3.py:1917-1918` | `label_mode="trend_scanning"`, `trend_scan_grid=(5, 8, 13, 21)` — passed to every v3 model constructor at lines 1925/1927/1932. |
| 2 | Runner pre-flight assertion | `run_baseline_v3.py:1125-1133` | `expected_label_mode = "trend_scanning"`; `raise RuntimeError` if `label_mode != expected_label_mode`. The runner would have **refused to start** under `triple_barrier`. There is no execution path by which /110 ran `triple_barrier`. |
| 3 | Run log | `run.log` line 20 | `label_mode (iter-v3/105): 'trend_scanning' grid=(5, 8, 13, 21) max_h=21 <= timeout_candles=21 PASS` — the executed value, printed at runtime, announcing in plain text it is the /105 setting. |
| 4 | The mandated revert | `diary-v3/iteration_v3-105.md` line 7 + lines 322-330 | "`label_mode` **REVERTS to `triple_barrier`** at the iter-v3/106 setup … a two-line config change … The trend-scanning label must not be re-proposed." |

**How the stale state survived four iterations.** iter-v3/105 closed `trend_scanning` EXPLORATION-NEGATIVE (IS monthly Sharpe collapsed to +0.2201, hard F2 fire) and mandated the two-line `label_mode` revert at the iter-v3/106 setup. iter-v3/106, /107, /108, /109 were **all NULL-AT-EDA** — they produced EDA + a diary but never ran a runner setup, so the un-reverted `label_mode` lay dormant for four iterations. **iter-v3/110 is the first iteration since /105 to execute `run_baseline_v3.py`** — and it inherited the stale value. The runner comment blocks at `run_baseline_v3.py:1114-1118` and `1912-1916` are still tagged verbatim `iter-v3/105` and still describe the trend-scanning label as "the ONE clean variable for this iteration" — /105 prose never rewritten for /110.

**Why the confound voids the measurement.** Three points, all endorsed by the Critic and concurred by the QR:

1. **Attribution is destroyed.** The /110 headline IS monthly Sharpe is +0.2942; the /105 trend-scanning IS-collapse figure was +0.2201. These differ by 0.074 — inside 3-seed EXPLORATION-mode noise. The /110 IS result is statistically indistinguishable from the /105 labeling-drag figure; there is no estimator in this run that decomposes +0.2942 into a universe component and a label component.
2. **The EDA → brief inferential chain is voided by label-geometry mismatch.** The Phase-2 EDA loader (`analysis/iteration_v3-110/_shared.py`) replicates `labeling.label_trades` with `label_mode="triple_barrier"`. Every Section-2 table (T1-T10), the +0.25 raw gated proxy, the screen ranking that selected CRV/AAVE/GRT/ADA — all computed under `triple_barrier`. The backtest trained under `trend_scanning`. The EDA predicts the behavior of a model trained on one estimand; the backtest measured a model trained on a different estimand. The brief's Section 2 → Section 4 inferential chain cannot interpret the as-run backtest.
3. **The confound is an active interaction, not a passive additive bias.** The /105 closeout established that `trend_scanning` is geometrically mismatched to the unchanged triple-barrier execution layer — it gives the multi-seed Optuna fit a noisier estimand to overfit in-sample. It is not a fixed additive bias that could be subtracted off; it is an interaction term — the trend-scanning IS-overfitting hazard acts on the new universe's per-symbol fits in an unmeasured way. It can flip the sign as well as scale the magnitude of any universe effect. No sub-result of this run is label-clean.

## 3. Phase 7 — OOS evaluation (honest read, with the confound caveat foregrounded)

This is the QR's first look at the /110 OOS reports. **The headline finding of Phase 7 is that the OOS result cannot be attributed to the symbol-selection axis** — the runner trained under `trend_scanning`, so the OOS book is as confounded as the IS book. The numbers below are reported for completeness and to document the as-run NEGATIVE; they do NOT speak to whether the CRV/AAVE/GRT/ADA universe carries edge.

### 3.1 Headline OOS metrics (`comparison.csv`)

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly Sharpe | +0.2942 | **−0.4455** | −1.5143 |
| daily Sharpe | +0.6398 | −1.4865 | −2.3235 |
| profit factor | 1.0878 | 0.8275 | 0.7607 |
| win rate | 33.60% | 29.21% | 0.8694 |
| n_trades | 250 | 89 | 0.3560 |
| total PnL | +41.3253 | **−28.2848** | −0.6844 |
| max drawdown | 70.49% | 72.28% | 1.0254 |

The OOS book is net-negative on every metric. OOS monthly Sharpe −0.4455 sits well below the Section 8 falsifier (OOS < −0.10). IS monthly Sharpe +0.2942 sits 0.006 below the Section 8 falsifier (IS < +0.30) — essentially AT the falsifier, not far below it; this is a clean NEGATIVE on the as-run numbers.

### 3.2 Per-symbol OOS attribution (`out_of_sample/per_symbol.csv`)

| Symbol | OOS Trades | Win Rate | Net PnL (%) | Avg PnL/trade | Role |
|---|---:|---:|---:|---:|---|
| **CRVUSDT** | 19 | **36.8%** | **+5.679** | +0.299 | **sole carrier** — only OOS-positive symbol; only WR above the 33.3% 2:1 breakeven |
| ADAUSDT | 24 | 29.2% | −9.796 | −0.408 | dragger (32.84% of total loss) |
| GRTUSDT | 26 | 30.8% | −12.680 | −0.488 | dragger (42.51% of total loss) |
| AAVEUSDT | 20 | 30.0% | **−13.034** | −0.652 | **largest dragger** (43.69% of total loss) |

CRV is the sole OOS carrier at +5.68% (36.8% WR — the only symbol clearing the 2:1-barrier breakeven). AAVE drags most at −13.03% (30.0% WR), GRT second at −12.68%, ADA third at −9.80%. **3 of 4 symbols are OOS-negative.**

### 3.3 OOS monthly trajectory (`out_of_sample/monthly_pnl.csv`)

13 OOS months; only 2 are positive — 2025-08 (+38.84) and 2026-05 (+5.13). 2025-07 is the worst (−35.87). The early OOS run (2025-05 −13.92, 2025-06 −18.51, 2025-07 −35.87) is a sustained loss streak; 2025-08's +38.84 partly recovers it, but the book closes net-negative.

### 3.4 Why none of this attributes to the universe axis

The Critic's framing, which the QR endorses: "NEGATIVE because the screened universe carries no edge" and "NEGATIVE because the runner trained on a known-NEGATIVE label" are **two different findings** with two different cycle-6 consequences. The first closes the universe axis; the second indicts the runner state and closes nothing about the universe. This run's artifacts cannot distinguish them — the OOS book is trained through the same mismatched `trend_scanning` label /105 proved produces an IS-collapse/OOS-overfitting signature, so the OOS −0.4455, the CRV-only-carries pattern, and the 3-of-4-symbols-negative tell are all confounded. Recording /110 as "universe axis closed — no edge" would be a false attribution and would corrupt the cycle-6 axis sequence. **The universe axis is UNRESOLVED.**

## 4. What Worked / What Failed

### What Worked — iter-v3/110 was a PROCESS WIN despite the NEGATIVE verdict

This must be recorded honestly: iter-v3/110 produced a NEGATIVE result, but the iteration was a **process win** on two distinct counts.

1. **It ran a real experiment.** iter-v3/103, /104, /106, /107, /108, /109 were all NULL-AT-EDA — six consecutive iterations that concluded at a Phase-1 gating EDA without ever running a runner. /110 broke that chain: it wrote a full 10-section brief, the QE implemented the universe swap, a 1.08h backtest ran, and the Critic audited eight checks against the report artifacts. Running the experiment — rather than killing the axis at the EDA — is what surfaced the bug (see point 2). The cycle-6 axis menu explicitly mandates "every EXPLORATION produces a brief + backtest (no EDA-kill)"; /110 honored that mandate.

2. **The Critic surfaced a latent bug the NULL-AT-EDA chain had buried for four iterations.** The `label_mode="trend_scanning"` stale state was introduced at /105 and should have been reverted at the /106 setup. Because /106-109 never ran a setup, the un-reverted knob lay dormant and undetected for four iterations. /110 is the first iteration to run the runner since /105 — and the Phase-7.5 Critic's Check 8, by cross-referencing the brief's "ONE axis" prose against `run.log` line 20 and the runner source, caught it. Without /110 running a real experiment and being audited, the stale `label_mode` would have ridden silently into iter-v3/111 and every subsequent runner execution. The bug is now identified, the fix is specified (Critic Rec 2/3), and iter-v3/111 will land it as a precondition. **A NEGATIVE iteration that surfaces a four-iteration-old latent bug has positive information value.**

3. **The QR's Section 7 pre-registration was disciplined.** The brief pre-registered AAVE and ADA as at-least-equally-likely per-symbol weak links (Section 7 modes #3/#4), with the AAVE dead-path "OOS −35%" and ADA dead-path "5-seed ensemble washes the edge" both disclosed in Section 10. On the as-run numbers AAVE is indeed the largest dragger and ADA the third — the pre-registration fired. (Caveat: see Section 6 — the confound means this is not a clean confirmation.)

### What Failed

1. **The registered single-axis hypothesis is not the experiment that ran.** The brief's "ONE axis: `V3_MODELS` is replaced wholesale" is false at the implementation level. The run varied two variables. This is the textbook scope-creep / hypothesis-faking pattern Check 8 exists to catch — though here it is unintentional (stale state), not deliberate.

2. **The `_canonical_v059` config-accretion guard had a blind spot exactly where the drift occurred.** The guard (`run_baseline_v3.py:1032-1050`) enumerates 11 knobs — `V3_MODELS` symbols, `REQUIRED_GAP`, the ATR multipliers, the per-symbol dicts, four RiskV2 thresholds, the block lists, the drawdown brake. `label_mode` and `trend_scan_grid` are **not among them.** The guard built specifically to catch illegitimate config drift did not cover the knob that drifted across four NULL-AT-EDA iterations.

3. **The runner pre-flight asserted the wrong target.** The pre-flight at `run_baseline_v3.py:1125-1133` *did* assert `label_mode` — but asserted `expected_label_mode = "trend_scanning"`, enforcing the stale state rather than catching it. An assertion is only protective if the asserted target is correct.

4. **The engineering report and the Phase-5.5 gate missed it.** The engineering report's "Configuration Diff vs Baseline (/059)" table asserts "All other knobs … /059-identical" — false — despite `run.log` line 20 recording the carry-over in plain text. The Phase-5.5 gate did not verify the runner's actual config against the brief's prose.

## 5. Critic Review Summary (Phase 7.5 — 8 checks)

The Phase-7.5 Critic review (`briefs-v3/iteration_v3-110/review.md`, FINAL) scored the EXPLORATION on Checks 1, 2, 4, 5, 6, 8 (verdict-driving) with Check 3 informational at EXPLORATION budget per `feedback_v3_dsr_mode_artifact.md`. The QR Round-2 response was **STAND BY VERDICT** — the QR independently re-verified the four confound artifacts, produced no counter-artifact, and concurred in full.

| Check | Topic | Status | Note |
|---|---|---|---|
| 1 | Look-Ahead Audit | **PASS** | `e149e9d`-fixed walk-forward in effect (`train_end_ms = test_start_ms − embargo_ms`, every fold `gap=184h/22 rows`). First OOS trade 2025-03-28, four days after the immutable cutoff; last IS trade 2025-02-16 — clean split. The Check 8 finding is a hypothesis-alignment defect, NOT a temporal leak. |
| 2 | Embargo Width | **PASS** | Required cross-cell gap `(21+1)×4 = 88`; `validation_v3.py:76` carries `REQUIRED_GAP=88`; runner recomputes and asserts 88; `run.log` line 25 PASS. The as-run `trend_scanning` grid max is 21 (`run.log` line 20 `max_h=21 <= timeout_candles=21`), so the embargo is not under-sized for the as-run label either. (Stale `(21+1)*3` parenthetical at `run.log` line 33 is a cosmetic copy-paste artifact — flagged for cleanup.) |
| 3 | Multiple-Testing Correction | FAIL (**informational** — NOT verdict-triggering) | `dsr.json`: DSR=0.0, PSR=0.0, PBO=0.1267 (clears <0.4). Per Section 0.5 TYPE=EXPLORATION and `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are structural regime artifacts. DSR=0.0/PSR=0.0 are uninformative — the OOS book is net-negative, so there is no positive Sharpe for the deflation machinery to act on. Moot for verdict. |
| 4 | IC Correlation | **PASS** (non-applicable) | Universe-only axis, zero new features. `V3_FEATURE_COLUMNS` asserted as the exact /059 14-feature stack. No new-vs-existing pair to test. |
| 5 | ADF Stationarity | **PASS** | `/059`-identical 14-feature stack — no feature added or modified. See ADF summary §7 below. |
| 6 | Pareto Dominance | **PASS** (non-applicable) | EXPLORATION mode (`ensemble_summary.json`: `mode=exploration, ensemble_size=3`); `ensemble_summary.json` replaces `pareto_front.csv`. Multi-seed Pareto is a CONFIRMATION concern, correctly deferred to iter-v3/120. |
| 7 | Reproducibility | **PASS** | Commit SHA `f7e564f` stamped; explicit `feature_columns` passed; `ITERATION_LABEL="v3-110"`; PnL arithmetic spot-check consistent (sub-0.01 float drift). The run is bit-reproducible — and bit-reproducibly trained on the wrong label. Reproducibility and correctness are orthogonal; this check is the former. |
| 8 | Hypothesis-Implementation Alignment | **FAIL — VERDICT DRIVER** | The runner trained every /110 model on the wrong label (`trend_scanning`, not `triple_barrier`). The brief's central "ONE axis" claim is false at the implementation level. The run varied two variables. Verified at source (`run_baseline_v3.py:1917-1918` / `1125-1133`; `run.log` line 20; `iter-v3/105` comment blocks at `1114-1118` / `1912-1916`). |

**Check 8 FAIL is the verdict driver. OVERALL: EXPLORATION-NEGATIVE.** The Critic notes the brief's pre-registered Section 8 falsifiers also fired on the as-run numbers, so the iteration is NEGATIVE on its own criteria — but "NEGATIVE because the universe carries no edge" and "NEGATIVE because the runner trained on a known-NEGATIVE label" are different findings, and only a `triple_barrier` re-run can distinguish them.

## 6. Pre-Registered Failure-Mode vs Reality

The brief Section 7 pre-registered four failure modes. On the **as-run numbers** they fired — but the label confound means this is **NOT a clean confirmation of the universe hypothesis**, because the as-run book is not the universe-on-`triple_barrier` book the brief modeled.

| # | Pre-registered failure mode | As-run reality | Clean confirmation? |
|---|---|---|---|
| 1 | IS signal screen ranks symbols on broad-population AUC that does not survive IS→OOS regime shift; IS-fit / OOS-decay signature; 3 of 4 symbols OOS-negative = "universe is a selection artifact" tell | IS +0.2942 / OOS −0.4455, OOS/IS ratio −1.51; 3 of 4 symbols OOS-negative (CRV the only positive) — the *pattern* matches | **NO** — the IS-fit / OOS-decay signature is exactly what the /105 trend-scanning label produces on ANY axis (the IS-collapse / OOS-overfit signature). The confound and the predicted failure mode are observationally identical here; the run cannot tell them apart. |
| 2 | Universe swap helps concentration but not edge (PROMISING-MECHANICAL outcome) | Not reached — the book is net-negative, not merely unconcentrated | N/A |
| 3 | ADA specifically underperforms (v2 dead-path, /078 closed) | ADA −9.80% OOS, the 3rd-largest dragger | **NO** — ADA's per-symbol fit was trained through `trend_scanning`; the dead-path is not cleanly re-confirmed. |
| 4 | AAVE specifically underperforms (v2 "OOS −35%" dead-path; weakest IS evidence of the four) | AAVE −13.03% OOS, the **largest** dragger, 43.69% of total loss | **NO** — same reason. AAVE being the weak link is consistent with the brief's pre-registration, but the AAVE per-symbol fit ran through `trend_scanning`; this is not a clean test of the AAVE-on-`triple_barrier` hypothesis. |

**The honest statement:** the brief's Section 7 modes #1, #3, #4 fired on the as-run numbers, and the QR's pre-registration of AAVE/ADA as weak links was disciplined. But because the confound (the /105 trend-scanning IS-collapse signature) produces the *same observable* — an IS-fit / OOS-decay pattern with most symbols negative — the firing of the modes is **NOT** independent evidence that the universe carries no edge. A clean test requires the `triple_barrier`-corrected re-run (iter-v3/111).

## 7. ADF Report Summary

`reports-v3/iteration_v3-110/adf_test.csv` runs the Augmented Dickey-Fuller stationarity test on the /059-identical 14-feature stack, per symbol per walk-forward month (3137 rows; ADF evaluates feature stationarity, label-independent — the Check 8 confound does not affect it).

- The `stationary=False` rows are dominated by early-history months with insufficient candles for ADF to compute (a "could-not-test" sentinel — 96 rows have an empty `stationary` field where the test could not run).
- At the IS-end window (2024-10 → 2025-03), the great majority of computed tests return `stationary=True` with p ≪ 0.01. The standard scale-invariant features (`vwap_dev_20`, `regime_momentum_signed_5d`, `hurst_100`, `ret_autocorr_lag1_50`, `sym_vs_btc_ret_7d`, `ema_spread_atr_20`, etc.) are decisively stationary on every symbol at IS-end (p typically 0.0–1e-5).
- The only computed-test borderline failures at IS-end are the long-window distributional-moment features — `ret_skew_200` and `ret_kurt_200` on CRV (p ≈ 0.21–0.35) and `ret_kurt_200` on AAVE (p ≈ 0.064, borderline) — long-window skew/kurtosis features whose ADF p naturally hovers near the threshold. This is a known property of 200-bar distributional moments, not a stationarity failure introduced by this iteration.
- No feature was added or modified; this is the /059 anchor stack. **Check 5 ADF: PASS.**

## 8. Lessons

1. **The NULL-AT-EDA pattern has a hidden cost: a setup-side config revert mandated by a closed iteration is silently lost if no subsequent iteration runs a setup.** iter-v3/105 mandated the `label_mode` → `triple_barrier` revert "at the iter-v3/106 setup." iter-v3/106, /107, /108, /109 were all NULL-AT-EDA — they killed their axes at a Phase-1 gating EDA and never ran a runner setup. So the /105-mandated revert was **never carried for four consecutive iterations**, and the stale `trend_scanning` knob lay dormant and undetected. NULL-AT-EDA is a legitimate fail-fast discipline (`feedback_fail_fast.md`) — but its hidden cost is that **a NULL-AT-EDA iteration cannot discharge a setup-side obligation left by a prior iteration.** Generalizable rule: a config revert mandated by iteration N's closeout must be discharged by the *next iteration that runs a runner setup*, not "the next iteration" — and the closeout's hand-off must say so explicitly. When a NULL-AT-EDA iteration inherits an outstanding setup-side obligation, its diary must re-state the obligation and carry it forward to the next runner-executing iteration.

2. **The `_canonical_v059` config-guard had a blind spot exactly where the drift occurred — a guard that enumerates a fixed knob list does not cover knobs added by later EXPLORATIONs.** The guard was built (at the /059 anchor) to catch illegitimate config drift across 11 enumerated knobs. `label_mode` and `trend_scan_grid` were introduced as runner knobs *after* the guard's list was fixed (at iter-v3/105's trend-scanning axis), so the guard never covered them. The guard's coverage silently lagged the runner's actual config surface. Generalizable rule: every EXPLORATION that adds a new runner knob must add that knob to the `_canonical_v059` guard against its /059-canonical value in the *same* setup commit — otherwise the guard's protection erodes with every axis that touches a new knob. iter-v3/111 must (Critic Rec 3) sweep all label/model knobs touched by EXPLORATIONs /072-/105 (fixed-horizon, trend-scanning, inference-threshold-floor) and confirm the guard covers every knob any closed EXPLORATION mutated.

3. **The QE / Phase-5.5 gate must verify the runner's ACTUAL config against the brief's prose — never trust the prose** (`feedback_no_cheating.md`: "verify EDA code is IS-only, don't trust the brief's prose"). The /110 engineering report's "Configuration Diff vs Baseline (/059)" table asserted "All other knobs … /059-identical" — and this was false, despite `run.log` line 20 recording `label_mode (iter-v3/105): 'trend_scanning'` in plain text. The brief said `triple_barrier`; the runner ran `trend_scanning`; the engineering report copied the brief's claim instead of reading the runner. A runner pre-flight that *asserts* a config value is only protective if the asserted target is correct — and here the pre-flight asserted the *stale* target (`expected_label_mode = "trend_scanning"`), so it enforced the bug rather than catching it. Generalizable rule (Critic Rec 4): the QE must grep `run.log` for the executed `label_mode` value and quote it verbatim in the engineering report's reconciliation section; both the runner pre-flight target and the engineering-report config diff must be re-derived from the brief *each iteration*, never carried forward. The `feedback_no_cheating.md` discipline — "don't trust the brief's prose, verify the code" — extends from the EDA scripts to the runner config.

4. **A NEGATIVE iteration that runs a real experiment can have higher information value than a NULL-AT-EDA that kills an axis cheaply.** iter-v3/110 is NEGATIVE, and its as-run measurement is void — but it surfaced a four-iteration-old latent bug that the NULL-AT-EDA chain had buried. The cycle-6 mandate ("every EXPLORATION produces a brief + backtest, no EDA-kill") is vindicated here: running the experiment is what exposed the stale state. NULL-AT-EDA saves compute but also skips the runner, the engineering report, and the Critic's implementation audit — the very steps that catch runner-state bugs. Fail-fast and run-the-experiment each have a place; this iteration is evidence that the run-the-experiment discipline catches a failure class the EDA-kill discipline structurally cannot.

5. **Brief Section 0.5's "ENSEMBLE_SIZE forced to 1 / single-seed" wording is STALE.** The /110 brief Section 0.5 states `--exploration` forces `ENSEMBLE_SIZE=1` / single-seed. This is wrong — the current v3 EXPLORATION mode has been `ENSEMBLE_SIZE=3` since the iter-v3/060 RE-ANCHOR (`ensemble_summary.json` for /110 confirms `mode=exploration, ensemble_size=3, seeds=[191664963, 1662057957, 1405681631]`), per `feedback_v3_cycle1_axis_pass_criteria.md`. The mechanical effect on /110 is NONE — the run *was* the correct current-standard 3-seed EXPLORATION; only the brief's prose description is stale. The committed /110 brief is NOT retroactively edited (it is a historical artifact). The **iter-v3/111 brief must state the EXPLORATION mode correctly** as `ENSEMBLE_SIZE=3` and drop the "single-seed" / "forced to 1" language. (This is a documentation-staleness twin of Lesson 1's `label_mode` staleness — both are /105-era prose that survived un-updated; the /111 setup must rewrite the stale `iter-v3/105` comment blocks at `run_baseline_v3.py:1114-1118` and `1912-1916` as part of Critic Rec 2.)

## 9. Next Iteration Ideas

**iter-v3/111 = the clean re-test of the CRV/AAVE/GRT/ADA universe-selection axis under a `triple_barrier`-corrected runner** (Critic Recommendation 4). iter-v3/110's universe and brief are kept intact; the re-run executes on a corrected runner so the EDA (computed under `triple_barrier`) and the backtest share one label geometry, making the brief's Section 2 → Section 4 inferential chain valid. The universe axis remains an open cycle-6 axis (`project_v3_cycle6_axis_menu.md` item 1); /110 spent an EXPLORATION slot (it consumed a runner execution) but did not resolve it.

**The iter-v3/111 setup MUST first land Critic Recommendations 2 and 3 — these are preconditions; no v3 runner execution may occur until they are committed and the pre-flight confirms `triple_barrier`:**

- **Critic Rec 2 — revert `label_mode` to `triple_barrier`:**
  - `run_baseline_v3.py:1917-1918`: `label_mode="trend_scanning"` → `label_mode="triple_barrier"`; remove or neutralize `trend_scan_grid=(5, 8, 13, 21)`.
  - `run_baseline_v3.py:1125`: `expected_label_mode = "trend_scanning"` → `"triple_barrier"`; revise the lines 1126-1163 assertion/print block so the pre-flight enforces and announces `triple_barrier`.
  - Rewrite the stale `iter-v3/105` comment blocks at `run_baseline_v3.py:1114-1118` and `1912-1916` for the /111 universe-axis context (and, per Lesson 5, drop the stale "single-seed" EXPLORATION-mode prose wherever it appears).
- **Critic Rec 3 — add `label_mode` and `trend_scan_grid` to the `_canonical_v059` accretion guard (`run_baseline_v3.py:1032-1050`):** add two entries against the /059-canonical values (`label_mode == "triple_barrier"`; `trend_scan_grid` neutralized). Sweep all label/model knobs touched by EXPLORATIONs /072-/105 (fixed-horizon, trend-scanning, inference-threshold-floor) and confirm the guard now covers every knob any closed EXPLORATION mutated. Clean the stale `(= (21+1)*3; ...3-sym /059 universe...)` diagnostic string at the `run.log`-source print (`run.log` line 33).

**The iter-v3/111 brief must additionally:**

- Carry a Configuration Diff that the QE verifies against `run.log` line-by-line — including an explicit `label_mode: triple_barrier` row — rather than asserting "all other knobs /059-identical" (Lesson 3).
- Instruct the QE to grep `run.log` for the executed `label_mode` value and quote it verbatim in the engineering report's reconciliation section, so a future label carry-over is caught at Phase 6.
- Pre-register the Section 8 falsifiers afresh against the /060 cycle-1-style EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403), per `feedback_v3_cycle1_axis_pass_criteria.md` (cycle-1 axis-PASS: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs the anchor AND frac_positive_paths ≥ 0.50; PROMISING-AT-EXPLORATION must cross-validate at the cycle CONFIRMATION against /059's CONFIRMATION baseline).
- State the EXPLORATION mode correctly as `ENSEMBLE_SIZE=3` (Lesson 5) — drop the stale /105-era "single-seed / forced to 1" wording.
- Keep iter-v3/110's universe (CRV/AAVE/GRT/ADA) and the QR-led EDA basis intact — the axis design survives; only the as-run measurement was void.

**If the corrected /111 re-run is itself NEGATIVE,** that is the result that legitimately closes the symbol-selection-by-feature-AUC-screen axis — and iter-v3/112 then advances to the next cycle-6 menu item (pooled vs per-symbol model architecture, multi-frequency feature engineering, or risk management), per `project_v3_cycle6_axis_menu.md`. **If /110's Section 7 fallback logic still applies after a clean /111 run** — e.g. AAVE is again the universe's OOS-worst symbol on `triple_barrier` — the brief's pre-registered drop-AAVE / drop-ADA variants (CRV+GRT+ADA, or the all-novel U_A = CRV+AAVE+GRT) are the scoped follow-ups.

## 10. Commit chain

- EDA SHA: `cfeaf34` — `analysis/iteration_v3-110/` (`_shared.py` the /059-faithful IS-only triple-barrier labeler, `symbol_signal_screen.py`, `universe_construction.py`, `t6_recompute.py`, `gated_book_2to1.py`, `universe_finalize.py`; result tables T1-T10).
- Brief SHA: `a7386e7` (setup) — `briefs-v3/iteration_v3-110/research_brief.md` (10-section brief; **NOT retroactively edited** — the Section 0.5 "ENSEMBLE_SIZE forced to 1 / single-seed" wording is stale, see Lesson 5; the iter-v3/111 brief states it correctly).
- Code SHA (pre-backtest): `f7e564f` — the universe swap implementation (`V3_MODELS` 3→4, `REQUIRED_GAP` 66→88, `ITERATION_LABEL` "v3-110", `_canonical_v059` guard symbols + gap). NOTE: this commit did NOT revert the `label_mode` knob — the source of the confound.
- Engineering report SHA: `3172169` — `briefs-v3/iteration_v3-110/engineering_report.md`.
- QR response SHA: `84c0517` — `briefs-v3/iteration_v3-110/qr_response.md` (Round-2 STAND BY VERDICT).
- Critic review SHA: `348795d` — `briefs-v3/iteration_v3-110/review.md` (OVERALL: EXPLORATION-NEGATIVE; Check 8 FAIL the verdict driver).
- Reports: `reports-v3/iteration_v3-110/` — a backtest WAS run (1.08h); `comparison.csv` IS +0.2942 / OOS −0.4455. The reports are RETAINED as the record of the confounded run; they are NOT the clean universe-axis measurement (iter-v3/111 produces that).
- Diary SHA: this closeout — `docs(iter-v3/110): diary entry`.
- Catalog update SHA: committed with the catalog edit — `briefs-v3/exploration_catalog.md` /110 row (classification "NEGATIVE — label confound; universe axis UNRESOLVED").
- BASELINE_V3.md: documentation-only banner update (the "Last updated:" line) — `v0.v3-059` UNCHANGED as canonical; an EXPLORATION never changes baseline metrics.
- **No `src/` revert in this iteration** — the `label_mode` revert is a precondition for the iter-v3/111 *setup*, not a /110 closeout action; iter-v3/110's `src/` state (the universe swap on top of the stale `trend_scanning` knob) is left as the record of the run, and the /111 setup lands Critic Rec 2/3.
- **Tag**: `v0.v3-110` — a closeout marker only, tagged by the orchestrator (NOT a baseline update — the `v0.v3-082`…`v0.v3-109` pattern).

iter-v3/110 is cycle-6 EXPLORATION slot #1. It ran a real experiment — the first runner execution since iter-v3/105 — and is classified **EXPLORATION-NEGATIVE — label confound**: the runner trained every model under the stale `trend_scanning` label instead of the brief-declared `triple_barrier`, so the symbol-selection axis is **UNRESOLVED**, not closed. The iteration was a process win — running the experiment surfaced a four-iteration-old latent bug. iter-v3/111 is the clean re-test of the CRV/AAVE/GRT/ADA universe under a `triple_barrier`-corrected runner, with Critic Rec 2/3 as preconditions.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`) is inherited unchanged (Critic Check 1 PASS — clean IS/OOS split, first OOS trade 2025-03-28). This EXPLORATION does NOT update BASELINE_V3.md regardless of outcome — `v0.v3-110` is a closeout marker only. All Phase 1-5 EDA was strictly IS-only (`analysis/iteration_v3-110/_shared.py` asserts `close_time < OOS_CUTOFF_MS` per symbol); the QR did not inspect the post-cutoff OOS during Phases 1-5 — the OOS reports were first read in Phase 7. The IS window did NOT change — the as-run NEGATIVE is reported honestly, not by trimming the evaluation window. The label confound is reported in full; the as-run OOS −0.4455 is explicitly NOT attributed to the universe axis.

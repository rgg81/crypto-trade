# iter-v3/105 — Cycle-5 EXPLORATION slot #5 — LABEL GEOMETRY: the trend-scanning label (triple-barrier → López de Prado MLAM §5.4 per-bar data-selected horizon) — FILED EXPLORATION-NEGATIVE — IS-collapse (F2 fires hard); the /102 IS-collapse / OOS-spike structural twin; the /104 "label is the binding constraint" hypothesis is FALSIFIED

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #5) — 3-seed EXPLORATION mode (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, `--n-trials 35`)
**Verdict**: **EXPLORATION-NEGATIVE** — the pre-registered Falsifier **F2 (IS monthly Sharpe < +0.60) FIRES** at IS monthly Sharpe **+0.2201** (a −0.61 collapse below the /060 EXPLORATION-mode anchor +0.8325). The pre-registered Falsifier **F5 (IS/OOS daily-Sharpe ratio outside [0.2, 5]) also FIRES** at ratio **5.06**. The OOS monthly Sharpe +1.1897 is **NOT an edge** and **NOT a look-ahead leak** — the Phase-7.5 Critic Check 1 traced `_trend_scan_label` line-by-line and conclusively ruled out look-ahead (the forward window never exceeds 21 candles; the embargo 22 over-covers it by 1 candle; the hard-causality test is genuine). It is the iter-v3/026/027/030/034/036/037/102 IS-collapse / OOS-spike overfitting signature — an OOS spike sitting on a collapsed IS fit.
**Classification**: **EXPLORATION-NEGATIVE** — brief Section 8 LOCKED disjunctive taxonomy step 2 (F1 OR F2 OR F3 fires; first match wins). F2 fires at IS +0.2201 < +0.60. F5 (step 3, SUSPICIOUS) also fires at ratio 5.06 but is superseded by F2 under first-match precedence — recorded for completeness; the iteration is NEGATIVE whichever leg is cited.
**Decision**: **NO-MERGE.** BASELINE_V3.md baseline metrics UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION). `label_mode` **REVERTS to `triple_barrier`** at the iter-v3/106 setup.
**Branch**: `iteration-v3/105`
**Tag**: `v0.v3-105` — a closeout marker only (the `v0.v3-082`…`v0.v3-104` pattern; an EXPLORATION never updates the baseline).

---

## 1. The axis tested — and why

iter-v3/105 is the cycle-5 EXPLORATION slot #5 and the **first v3 axis to attack the
estimand** — *what the model is asked to predict* — rather than the inputs to, or the
estimator of, a fixed prediction problem. The single clean variable is the **training
label geometry**: `label_mode` `triple_barrier` → `trend_scanning`. The v3 single fixed
21-candle triple-barrier training label was replaced with a **trend-scanning label**
(López de Prado, *Machine Learning for Asset Managers* §5.4): per bar, fit an OLS linear
trend over a horizon grid `{5, 8, 13, 21}`, select the horizon with the largest
|t-statistic|, label the bar by the sign of that slope. The prediction horizon is
**data-selected per bar**, not a fixed hyperparameter.

The axis was QR-led per `feedback_v3_axis_selection_quant_discipline.md` — it is the
iter-v3/104 closeout's Recommendation #1 (TOP), pre-registered there with an explicit
F-HORIZON / F-IC / F-RATE gating-EDA mandate. Three committed IS-only EDA scripts under
`analysis/iteration_v3-105/` (EDA SHA `857e176`) returned a Phase-1 **GO**: the
14-feature `V3_FEATURE_COLUMNS` stack predicts the trend-scanning label **+52% better**
(gating grid, mean |IC| 0.04622 vs 0.03034) — and **+31% better** under the
longest-wins-confound-removed capped grid `{5,8,13,21}` (mean |IC| 0.03977 vs 0.03034,
Wilcoxon signed-rank p=0.013 over 42 cells, 25/42 cells improved). The lift was
robustness-checked: the gating grid's 43-46% mass on the longest horizon h=34 was probed
adversarially (an extended grid with h=55 showed the mechanical longest-wins signature),
and the decisive capped-grid check `{5,8,13,21}` — capped at the incumbent 21-candle
horizon — confirmed the lift held with the confound removed, with ~51-53% of bars
genuinely selecting a horizon strictly *shorter* than the incumbent.

**Everything else was kept bit-identical to /059** — the 14 features, the BCH/LDO/TRX
universe, the triple-barrier TP/SL EXITS (ATR 2.0/1.0, 21-candle timeout), the 7-gate
RiskV2 stack, the per-symbol depth-3-5 LightGBM architecture, `REQUIRED_GAP=66`, the
embargo 22. **Only the training label the model is fit on changed.** The grid was capped
at the incumbent 21 precisely so the embargo (sized for the triple-barrier
`timeout//interval + 1`) over-covers the trend-scanning forward window with zero new
leakage surface — the Critic verified this numerically (Section 3 below).

The hypothesis under test (brief Section 1): *a label the existing features predict
materially better, that is also more temporally stable, lifts the OOS monthly Sharpe vs
the /060 anchor without collapsing the IS fit.* The IS fit collapsed.

---

## 2. Phase-7.5 Critic review — OVERALL = MERGE (methodology-clean; no BLOCK)

The Critic (`briefs-v3/iteration_v3-105/review.md`) returned **OVERALL = MERGE** — the
BLOCK/MERGE methodology gate only; the EXPLORATION classification is the QR's Phase-8
call (this diary). All 8 mandatory checks PASS except Check 3 (DSR), which is
INFORMATIONAL-ONLY for a 3-seed EXPLORATION per `feedback_v3_dsr_mode_artifact.md`.

**Check 1 — Look-Ahead Audit: PASS — the dispatch-priority check.** The
IS-collapse (+0.2201) / OOS-spike (+1.1897) signature demanded look-ahead be
conclusively ruled out before any other reading. The Critic traced `_trend_scan_label`
(`src/crypto_trade/strategies/ml/labeling.py:132-214`) independently, line by line:

1. **The forward look never exceeds 21 candles.** `max_h = max((5,8,13,21)) = 21`. The
   forward gather loop collects at most 21 forward closes; the per-horizon OLS builds
   `y = [entry_close, available[0..h-1]]` for `h ∈ grid` — the forward window is
   `close[t+1 .. t+h]`, `h ≤ 21`. No horizon, no fitted statistic, reaches beyond
   `t + 21`.
2. **The embargo fully covers the forward look.** `compute_embargo_candles(10080, 480)
   = 22` candles. `walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms`.
   The latest forward bar a training-set label can touch is
   `t + 21 ≤ test_start − 22 + 21 = test_start − 1 candle` — strictly inside the
   training period, one full candle short of the test month. The grid-capping at the
   incumbent 21-candle horizon is precisely what makes this hold.
3. **The OLS at bar `t` uses only `close[t .. t+h]`** — the prediction *target* window,
   correct by construction (a label may look forward; the model's *features* must not).
   The features are the 14 unchanged `V3_FEATURE_COLUMNS`, carrying no future info.
4. **No centered window, no full-series statistic, no `bfill`.** The forward gather
   stays within the entry bar's own symbol — no cross-symbol bleed.

The QE's hard-causality test (`test_trend_scanning_hard_causality`) is genuine and
sufficient — it builds a 23-bar frame (entry + 21 forward + 1 deadline), appends 5 extra
bars, and asserts bar 0's label/`long_pnl`/`short_pnl` are bit-identical between the
short and long frames. Bar 0's full grid maximum h=21 is exercised at the boundary.
**No look-ahead found. The OOS +1.1897 is NOT a leak.**

**Checks 2/4/5/7/8/9/10/12 — PASS.** Embargo unchanged from /059 by design (`REQUIRED_GAP
= 66 = (21+1)×3`); no feature added (`V3_FEATURE_COLUMNS` stays at 14, bit-identical to
/059, so the IC and ADF gates are inherited); reproducibility stamped (HEAD
`a819727b…`); the implementation matches the brief's ONE-variable hypothesis with no
scope creep (the `triple_barrier` branch is byte-identical preserved). Check 3 (DSR=0.0)
FAIL is informational only for a 3-seed EXPLORATION (`n_trials=315` regime artifact);
PBO 0.1153 (the BLOCK-triggering axis) clears 0.40 decisively, `frac_positive_paths`
0.644 clears the CPCV 0.55 gate. The Critic verified DSR/PBO/PSR are genuinely computed,
not hard-coded placeholders (the /090/092 defect) — `cpcv_paths.csv` is a genuine 45-row
path matrix, `per_cell_pbo.csv` 109 distinct per-cell rows. Check 6 (Pareto) not
applicable — single-mode 3-seed EXPLORATION. Check 11 (forming-candle) deferred to the
Engineer pre-flight (Critic read-only limitation; no anomaly observed).

---

## 3. Phase 7 — OOS evaluation: the F1-F6 falsifier cross-audit

The brief Section 4 pre-registered six numerical falsifiers, evaluated at Phase 7
against the /060 3-seed EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403). The
headline result from `reports-v3/iteration_v3-105/comparison.csv`:

| Metric | IS | OOS | ratio |
|---|---:|---:|---:|
| monthly Sharpe | **+0.2201** | **+1.1897** | 5.41 |
| daily Sharpe | +0.4330 | +2.1910 | 5.06 |
| max drawdown | 32.47% | 30.05% | 0.93 |
| profit factor | 1.0632 | 1.3136 | 1.24 |
| win rate | 31.18% | 42.22% | 1.35 |
| n_trades | 186 | 90 | 0.48 |

### The six falsifiers — each checked against the reports

| # | Falsifier | Fires if | Observed | Verdict |
|---|---|---|---|:--:|
| **F1** | Headline OOS regression | OOS monthly Sharpe < +0.00 | OOS **+1.1897** > 0 | **NO FIRE** |
| **F2** | IS collapse | IS monthly Sharpe < +0.60 | IS **+0.2201** < +0.60 (Δ **−0.61** below /060 anchor +0.8325) | **FIRES** |
| **F3** | BCH-only artifact | OOS lift carried entirely by BCH **AND both** LDO and TRX OOS weighted-pnl regress | BCH OOS +26.98 wpnl, **TRX OOS +8.94 wpnl (positive — does NOT regress)**, LDO OOS −2.75 wpnl. Only LDO regresses, not both | **NO FIRE** |
| **F4** | F-RATE trade-rate floor | bundle-level OOS trade count < 60 | OOS **90 trades** ≥ 60 (and 276 total ≥ the 130 bundle floor) | **NO FIRE** |
| **F5** | SUSPICIOUS — divergence | IS/OOS daily-Sharpe ratio outside [0.2, 5] | ratio **5.06** (IS daily 0.4330 / OOS daily 2.1910) — **outside [0.2, 5]** | **FIRES** |
| **F6** | F-SATURATION | OOS roster changes < 10% vs the /060 3-seed OOS roster | The /105 OOS roster is entirely re-fit on a different estimand (90 OOS trades vs /060's 102; per-symbol fits trained on a materially different target). The behavioral-effect predictor (brief Section 4) predicted 25-60% roster change; the IS-collapse confirms the fits moved substantially | **NO FIRE** |

**Two falsifiers fire: F2 (IS-collapse, the NEGATIVE step) and F5 (the divergence-ratio
leg of SUSPICIOUS).** F1, F3, F4, F6 do not fire. Both F2 and F5 were independently
verified by the Critic (review.md Recommendations 1 and 2). Under the brief Section 8
LOCKED disjunctive taxonomy (first-match-wins), F2 at step 2 settles the classification
at NEGATIVE before step 3 (SUSPICIOUS / F5) is reached — F5 is recorded for completeness.

**F5 — the duration-gap leg.** F5 has two legs: (a) the /076 trade-selection
mean-duration gap > +1.0 candles on a symbol with a material OOS lift, and (b) the
IS/OOS daily-Sharpe ratio outside [0.2, 5]. Leg (b) fires unambiguously at 5.06. Leg (a)
would require a Phase-8 OOS roster-diff script comparing added-vs-removed trade
durations against the /060 roster; it was not separately computed because F2 already
settles the classification at NEGATIVE under first-match precedence and the
classification does not change — the iteration is NEGATIVE whichever F5 leg is cited.
The ratio leg (b) firing is sufficient and verified.

### F1/F3/F4 — the supporting reads from the OOS reports

- **F1 — OOS is net-positive.** `out_of_sample/per_symbol.csv`: total OOS net_pnl
  +33.17%, profit factor 1.31, 42.2% win rate. The book is not net-losing OOS — but
  this is precisely the trap: a net-positive OOS headline is the *visible half* of the
  IS-collapse / OOS-spike signature, not evidence of edge.
- **F3 — not BCH-only.** BCH OOS +26.98 wpnl (98.88% of total OOS PnL by the
  `comparison.csv` concentration column) AND TRX OOS +8.94 wpnl (positive). LDO OOS
  −2.75 wpnl is the only regressing symbol. F3 requires *both* LDO and TRX to regress;
  TRX is positive, so F3 does not fire. (BCH 81.35% PnL concentration is well above the
  ≤30% aspirational cap — a known v3 outstanding constraint, not an F-falsifier here.)
- **F4 — trade rate clears.** 90 OOS trades / 14 OOS months ≈ 6.4 trades/month at the
  bundle level; 276 total trades. Above the F4 60-trade floor and the 130-trade
  bundle-level floor (`feedback_v3_trade_rate_floor_bundle_level.md`). The OOS monthly
  distribution (`out_of_sample/monthly_pnl.csv`) is broad — 14 months, no single month
  carrying the result; but 8 of 14 OOS months are positive only by a thin margin and 6
  are losing, consistent with a thin signal whose OOS Sharpe is a regime artifact.

---

## 4. Phase 7 — the brief's Section-7 pre-registered prediction vs the actual outcome

The brief Section 7 pre-registered, in probability order, four failure modes. The
**modal predicted outcome was EXPLORATION-PROMISING** — "OOS improving over the /060
anchor by ≥ +0.20 with the IS fit holding ≥ +0.60." The actual outcome is
**EXPLORATION-NEGATIVE by IS-collapse**.

**The specific prediction miss — documented honestly.** The brief made an explicit,
named, and **wrong** sub-prediction. Section 4 (the F2 row) and Section 7 (failure mode
#3) both stated:

> "F2 (IS-collapse) is specifically predicted UNLIKELY: /102 collapsed IS because a 15th
> feature widened the Optuna search space; /105 adds NO feature and does not widen the
> search space — the IS-collapse mechanism is structurally absent."

**This prediction was wrong.** The IS fit collapsed anyway — IS monthly Sharpe +0.2201,
a −0.61 drop below the /060 anchor, F2 fires hard. The brief's reasoning identified one
specific IS-collapse *mechanism* (a 15th feature widening the Optuna search space) and,
having ruled that mechanism out, concluded the *outcome* (IS-collapse) was structurally
absent. That is a category error: the brief reasoned from "this particular mechanism is
absent" to "this outcome cannot occur," when a different mechanism produces the same
outcome. The Critic flagged exactly this (Recommendation 1): **the IS-collapse mechanism
here is not a search-space widening — it is that the trend-scanning label is a
*different and noisier estimand* the multi-seed Optuna fit overfits in-sample.** The
trend-scanning label and the triple-barrier label are different prediction targets; the
per-symbol fits trained on the re-framed target found IS-fitting solutions that did not
hold up — the classic overfitting signature, independent of feature count.

The brief's honest meta-prediction (Section 7) was, in its other half, correct: "if the
backtest does NOT confirm it, the most informative reading is structural — the label
was not the constraint." That is exactly what happened, and it is the key meta-finding
(Section 6 below). But the specific F2-is-unlikely sub-prediction was a miss, and a
future label-geometry brief must rank IS-collapse as a **leading** predicted mode for any
estimand re-framing, not a structurally-absent tail. Re-framing the training label to a
noisier estimand is itself an IS-overfitting risk — the feature count is not the only
channel.

---

## 5. Phase 8 — Classification: EXPLORATION-NEGATIVE

Per the brief Section 8 LOCKED disjunctive taxonomy, evaluated in precedence order
(first match wins) against the Phase-7 OOS results, anchor /060:

1. **BLOCKED** — Critic OVERALL=BLOCK. **Does not apply** — the Critic returned
   OVERALL=MERGE; no methodology defect, look-ahead conclusively ruled out.
2. **NEGATIVE** — Falsifier F1 OR F2 OR F3 fires. ✅ **MATCH — F2 fires** (IS monthly
   Sharpe +0.2201 < +0.60).
3. **SUSPICIOUS** — Falsifier F5 fires. (F5 *does* fire at ratio 5.06 — but step 2
   already matched; recorded for completeness.)
4. **INERT** — Falsifier F6 fires. Not reached; F6 does not fire.
5. **NULL-RESULT** — no falsifier fires, OOS does not clear anchor + 0.20. Not reached.
6. **PROMISING** — none of F1-F6 fires AND OOS clears anchor + 0.20 AND IS ≥ +0.60.
   Not reached; F2 and F5 both fire.

**Classification: EXPLORATION-NEGATIVE** (step 2; F2 fires; first-match-wins). F5 also
fires (step 3) and is recorded — the iteration is NEGATIVE whichever leg is cited, per
the Critic's disjunctive-precedence note (Recommendation 2).

**The honest reading of the result.** The OOS monthly Sharpe +1.1897 is **NOT an edge.**
The Phase-7.5 Critic Check 1 conclusively ruled out look-ahead — the trend-scanning
forward window is embargo-covered with a 1-candle margin, the hard-causality test is
genuine, the leak path is closed numerically. The OOS +1.19 is the
iter-v3/026/027/030/034/036/037/102 **IS-collapse / OOS-spike overfitting signature** —
an OOS spike sitting on a collapsed IS fit (IS +0.2201, F2 fires). /105 is the direct
structural twin of /102: both attacked a single training-side variable (a feature in
/102, the label geometry in /105), both collapsed the multi-seed Optuna IS fit below the
+0.60 floor, both spiked OOS, both had look-ahead conclusively ruled out by the Critic.
A NEGATIVE EXPLORATION does not advance; per `feedback_v3_strict_both_is_oos_baseline.md`
a CONFIRMATION must improve **both** IS and OOS over /059, and there is no IS-improvement
thesis here — the IS fit was *destroyed*. The trend-scanning label is not carried
forward.

---

## 6. The key meta-finding — iter-v3/105 FALSIFIES the /104 "label is the binding constraint" hypothesis

This is the most informative output of /105, and the Critic stated it directly
(Recommendation 3).

**The /104 closeout hypothesis.** The /100→/104 closeout chain converged on a structural
diagnosis: every closed v3 axis attacked the *inputs to* (features ×4 families,
derivative data, on-chain) or the *estimator of* (model architecture ×4, training
objective, label class, universe) a **fixed prediction problem** — and not one moved the
thin v3 signal. The /104 diary's structural read: the thin signal is plausibly an
artifact of the single fixed 21-candle prediction horizon — and re-framing the
**estimand** (what the model predicts) was named the one un-attacked structural frontier.
The /104 closeout's Recommendation #1 (TOP) was the trend-scanning label, with the
explicit thesis that *the label geometry / the estimand is the binding constraint.*

**iter-v3/105 FALSIFIES that hypothesis.** The trend-scanning label was the literal test
of "the label geometry is the binding constraint." The IS-only EDA confirmed the label
re-framing is *real and substantive* — the 14-feature stack predicts the trend-scanning
label +31-52% better (Wilcoxon p=0.013, robustness-checked against the longest-wins
confound). If "the label was the constraint" were true, a label the features predict
31-52% better should have *lifted* the IS fit. It did the **opposite** — the IS fit
**collapsed** −0.61. **Re-framing the estimand to trend-scanning did not lift the IS
fit; it collapsed it.** The /104 hypothesis is falsified at one decisive data point.

**Where the binding constraint actually is.** The /105 result localizes it: the binding
constraint is **DOWNSTREAM of the training label** — in the **trade-construction / exit
/ risk layer.** The mechanism is a *mismatch*: the model was trained on a trend-scanning
label (per-bar data-selected horizon, sign of the most-resolvable local trend) but the
trades were executed through an **unchanged triple-barrier execution layer** (ATR 2.0/1.0
TP/SL, fixed 21-candle timeout). The model learned to predict one thing — the sign of a
data-selected-horizon trend — and the execution layer resolved the trade by a different
rule — first-touch of a fixed ±ATR barrier within a fixed window. A better-predicted
training label that is **mismatched to the execution geometry** does not translate into
trade-Sharpe; it gave the multi-seed Optuna fit a different (and, on this thin 8h
signal, noisier-to-fit) target to overfit in-sample. The brief Section 6 anticipated
exactly this conditional: "a better-predicted IS label that does not transfer to OOS
Sharpe means the EXECUTION layer is the binding constraint, and the next axis is the
trade-construction layer."

**This directly supports the iter-v3/106 direction.** iter-v3/106 is already
directed — a **user-directed risk-management axis**: analyze the IS loss-months → detect
the unseen-regime condition under which the book loses → stop or reduce trading in that
condition to lift the Sharpe. That is squarely a **trade-construction / risk-layer**
intervention — downstream of the label, exactly where /105 localizes the binding
constraint. The /105 finding is not a dead end; it is a *direction-confirming* result.
It tells iter-v3/106 to stop attacking the training-side of the problem (features,
labels, model, objective — all now closed) and work the **execution and risk layer**,
which is precisely the /106 mandate.

---

## 7. Dead Idea — the trend-scanning label

The **trend-scanning label** (`label_mode="trend_scanning"`; López de Prado, *Machine
Learning for Asset Managers* §5.4) is recorded as a v3 **Dead Idea** — NEGATIVE,
IS-collapse.

**The failure mode — stated precisely (the generalizable lesson).** The trend-scanning
label has a **measurably better feature→label IC** than the incumbent triple-barrier
label — the IS-only EDA measured a **+31-52% lift** (gating grid 1.52; capped grid 1.31,
Wilcoxon signed-rank p=0.013 over 42 cells; robustness-checked against the mechanical
longest-wins confound by capping the grid at the incumbent 21-candle horizon, with
~52% of bars genuinely re-framing to a shorter horizon). The label is also *more*
temporally stable than the incumbent (EDA T3, quartile-resolution sign-stability). And
yet it **COLLAPSED the multi-seed Optuna IS fit** — IS monthly Sharpe +0.2201, a −0.61
collapse below the /060 anchor, F2 fires.

**The lesson: a better feature→label IC does NOT predict trade-Sharpe when the training
label and the triple-barrier execution geometry are mismatched.** The trend-scanning
label trains the model to predict the sign of a per-bar data-selected-horizon OLS
trend; the v3 execution layer resolves trades by first-touch of a fixed ±ATR barrier
within a fixed 21-candle window. A label that is better-predicted *as a labeling
target* but geometrically mismatched to *how the trade actually resolves* gives the
Optuna fit a different and noisier estimand to overfit in-sample — it does not produce a
better trade-Sharpe. **Feature→label IC is a property of the labeling problem; it is
not a sufficient statistic for the trade-construction problem when label geometry ≠
execution geometry.** This generalizes the /102 lesson ("a held-out-tail accuracy proxy
does not predict the multi-seed Optuna IS fit") to the label-geometry axis: an IS-only
*IC* screen — even a strong, robustness-checked one — does not predict the production
trade-Sharpe of an estimand re-framing, because the screen measures the
feature→label relationship in isolation from the execution layer that the re-framed
label is now mismatched to.

**The revert.** `label_mode` **REVERTS to `triple_barrier`** at the iter-v3/106 setup —
the standard baseline-restore of a NEGATIVE/NO-MERGE axis. The runner change is two
lines (`label_mode` and `trend_scan_grid` in `run_baseline_v3.py`). The
`_trend_scan_label` function, the `trend_scanning` branch in `label_trades`, the
`trend_scan_grid` parameter plumbed through `LightGbmStrategy` / `MetaLabelingStrategy`,
and the unit/integration tests **STAY in the tree as zero-revert-cost dead-code
infrastructure** — the `fixed_horizon` / `formulaic_v3.py` / `basis_v3.py` /
`fetch-spot` retained-infrastructure precedent. Only the `label_mode` value reverts; no
code is deleted. The trend-scanning label must not be re-proposed.

---

## 8. Lessons

1. **iter-v3/105 falsifies the /104 "the label geometry is the binding constraint"
   hypothesis — the binding constraint is DOWNSTREAM of the label.** The trend-scanning
   label was the literal test of that hypothesis. A label the 14 features predict
   31-52% better (robustness-checked) should, if the label were the constraint, have
   lifted the IS fit; it collapsed it −0.61. The binding constraint is in the
   trade-construction / exit / risk layer — the execution geometry the model's
   predictions are resolved through — not in what the model is trained to predict. This
   is the key generalizable finding and it directs all remaining v3 work to the
   execution/risk layer.

2. **A better feature→label IC does NOT predict trade-Sharpe when the training label is
   geometrically mismatched to the execution layer.** The trend-scanning training label
   was mismatched to the unchanged triple-barrier execution geometry. The +31-52% IC
   lift was a real property of the labeling problem and a genuine, robustness-checked
   number — and it was the *wrong* statistic for predicting production trade-Sharpe,
   because trade-Sharpe is a property of the label-and-execution system, and the
   re-framed label broke the match between the two. An IS-only IC screen for a
   label-geometry axis must be paired with — or subordinated to — an explicit
   label-vs-execution-geometry consistency check.

3. **IS-collapse must be ranked a LEADING predicted mode for ANY estimand re-framing —
   not a structurally-absent tail.** The /105 brief explicitly predicted F2 (IS-collapse)
   UNLIKELY, reasoning that the /102 IS-collapse mechanism (a 15th feature widening the
   Optuna search space) was absent here. That reasoning was a category error: it ruled
   out one *mechanism* and concluded the *outcome* was impossible. A different
   mechanism — a noisier, mismatched estimand the multi-seed Optuna fit overfits —
   produced the same IS-collapse outcome. Any axis that changes *what the model is
   trained to predict* (label class /099, label normalization /101, label geometry /105)
   is an IS-overfitting risk regardless of feature count; future briefs must pre-register
   IS-collapse as a leading mode for such axes.

4. **The IS-collapse / OOS-spike signature is now a 9-iteration v3 pattern, and the
   Critic Check 1 look-ahead audit is the load-bearing check that distinguishes it from a
   leak.** iter-v3/026/027/030/034/036/037/102/105 (and /039 at multi-seed) all show an
   OOS spike on a collapsed IS fit. In every case the Critic Check 1 line-by-line
   look-ahead trace is what rules out a leak and confirms the signature is overfitting,
   not a bug. /105 reinforces the dispatch discipline: when IS collapses and OOS spikes,
   the look-ahead audit is the priority check, and a genuine hard-causality test in the
   QE's suite is what makes it conclusive.

5. **The training-side of the v3 prediction problem is now comprehensively closed.** With
   /105, every training-side lever has been attacked and closed: features (the 7-FEED
   INERT verdict, /098, /102, /103), the external-data layer (/104), the model
   architecture (/016/093/096/100), the training objective (/101), the label class
   (/099), the universe (/097), and now the label geometry (/105). No input-side or
   estimator-side lever has moved the thin per-symbol 8h signal. The productive frontier
   — the only one not yet worked — is the trade-construction / exit / risk layer, which
   is exactly the iter-v3/106 mandate.

---

## 9. Next Iteration — iter-v3/106 (cycle-5 EXPLORATION slot #6)

iter-v3/106 is **already directed** — a **user-directed risk-management axis**: analyze
the IS loss-months to detect the unseen-regime condition under which the book loses, and
stop or reduce trading under that condition to lift the Sharpe. The /105 finding
**directly supports** this direction:

- /105 falsified the hypothesis that the training-side (label/feature/model/objective)
  is the binding constraint — it localized the constraint **downstream of the label**, in
  the trade-construction / exit / risk layer.
- iter-v3/106's risk-management axis is squarely a **trade-construction / risk-layer**
  intervention — it does not touch features, the label, the model, or the training
  objective; it works the execution-and-risk layer where /105 localized the constraint.
- This is the productive next axis on the /105 evidence: the training-side is
  comprehensively closed (Lesson 5); the IS loss-month / unseen-regime risk axis attacks
  the layer /105 identified as binding.

Practical guidance for the iter-v3/106 QR, carried from /105:

1. **The axis must be QR-led** with a committed `analysis/iteration_v3-106/*.py` EDA
   basis preceding the brief, per `feedback_v3_axis_selection_quant_discipline.md`. The
   EDA should characterize the IS loss-months — which months lose, the regime
   conditions (BTC drawdown, volatility z-score, Hurst regime, etc.) that co-occur with
   the loss-months — strictly on `open_time < OOS_CUTOFF_MS`.
2. **The regime-conditional kill switch is CLOSED at the catalog level** (primitive 9,
   tested twice at /022 and /074 — no signal). A /106 risk axis must use a *different*
   construction than a binary BTC-drawdown/vol-z kill switch — e.g. a loss-month
   *detector* keyed on a richer or composite unseen-regime signal, a per-symbol
   drawdown brake with closed-loop state (note the `feedback_v3_oracle_eda_validity.md`
   STATEFUL-gate caveat — a stateful gate needs a closed-loop simulator or a
   deadlock-impossibility proof in the brief, per the /054 drawdown-brake deadlock), or
   a vol-target exposure ceiling. The brief must show the chosen construction is
   orthogonal to the closed primitives.
3. **Pre-register IS-collapse as a leading predicted mode** if the /106 axis touches the
   training label or the sample weighting (Lesson 3). A pure risk-gate overlay that
   leaves the model and label bit-identical to /059 is *not* an IS-overfitting risk in
   the /105 sense — but the brief must state this explicitly and pre-register a
   behavioral-effect predictor (how many IS trades the gate suppresses), per
   `feedback_v3_axis_saturation_predictor.md`.

---

## 10. Commit chain

- EDA SHA: `857e176` — `analysis/iteration_v3-105/` (3 scripts:
  `trend_scanning_gating_eda.py`, `trend_scanning_robustness.py`,
  `trend_scanning_grid_sensitivity.py` + 10 result CSVs `T1`–`T5`, `R1`–`R3`, `G1`/`G2`).
- Brief setup SHA: `3541997` — `briefs-v3/iteration_v3-105/research_brief.md` (the full
  10-section brief; setup SHA backfilled into Section 10 at `2b996fd`).
- Implementation HEAD: `a819727b724ee3894643e01ca3d1baa7d45c27c8` — the `_trend_scan_label`
  + `trend_scanning` branch in `labeling.py`, `trend_scan_grid` plumbed through
  `LightGbmStrategy` / `MetaLabelingStrategy`, the `run_baseline_v3.py` runner change
  (`ITERATION_LABEL = "v3-105"`), the unit + integration tests
  (`tests/strategies/ml/test_trend_scanning_label_mode.py`).
- Phase-7.5 Critic gate SHA: `3ce01acf6f4009a7263ebef58968fe7b9a489b88` — review
  `briefs-v3/iteration_v3-105/review.md`, OVERALL=MERGE.
- Diary SHA: this closeout — `docs(iter-v3/105): closeout diary — FILED
  EXPLORATION-NEGATIVE / IS-collapse (F2 + F5 fire); trend-scanning label → Dead Idea;
  /104 "label is the binding constraint" hypothesis FALSIFIED`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md`
  /105 row (classification EXPLORATION-NEGATIVE).
- BASELINE_V3.md Dead Ideas update SHA: committed with this diary — a new Dead Ideas
  entry for the trend-scanning label (documentation only; **no baseline metric change**).
- Reports: `reports-v3/iteration_v3-105/` (3-seed EXPLORATION backtest — `comparison.csv`,
  `dsr.json`, `in_sample/`, `out_of_sample/`, `cpcv_paths.csv`, `per_cell_pbo.csv`,
  `ic_matrix.csv`, `adf_test.csv`, `ensemble_summary.json`).
- **Tag**: `v0.v3-105` — a closeout marker only, tagged by the orchestrator (NOT a
  baseline update — the `v0.v3-082`…`v0.v3-104` pattern; BASELINE_V3.md UNCHANGED at
  `v0.v3-059`, IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION).

iter-v3/105 is cycle-5 EXPLORATION slot #5; the cadence advances. iter-v3/106 is slot #6
— the user-directed risk-management axis (IS loss-month / unseen-regime detection),
directly supported by the /105 finding that the binding constraint is downstream of the
label, in the trade-construction / risk layer.

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched.
The walk-forward embargo fix (`e149e9d`) is inherited unchanged. This EXPLORATION does
NOT update BASELINE_V3.md baseline metrics regardless of outcome — `v0.v3-105` is a
closeout marker only. All Phase 1-5 EDA was strictly IS-only (`open_time <
OOS_CUTOFF_MS`, verified across the 3 committed EDA scripts); the QR did not inspect the
post-cutoff OOS — the QR saw OOS for the first time in Phase 7.

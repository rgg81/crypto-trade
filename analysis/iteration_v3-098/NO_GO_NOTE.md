# iter-v3/098 — Phase-1 GO/NO-GO EDA closeout note — VERDICT: NO-GO

**Date**: 2026-05-18
**Type**: cycle-4 EXPLORATION slot #6 of 10 — Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
**Verdict**: **NO-GO** — the FEATURE-EXPANSION axis is KILLED at the EDA. No 10-section research brief was written; no runner change; no backtest.
**Classification**: **NULL-AT-EDA** — no candidate feature family clears the OOS-robustness bar from a committed IS-only EDA. Killing it cheaply at the EDA is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical /059 (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791, tag `v0.v3-059`).
**Branch**: `iteration-v3/098`

---

## 1. The axis and the decisive question

iter-v3/098 is the FEATURE-EXPANSION iteration mandated by the user's
2026-05-18 directive (`feedback_v3_bold_research_mandate.md` — "the features
are crucial ... work on the features based on 8h candles") and the /097
Critic's Recommendation 2 (symbol-screening as a lever is empirically
exhausted — pivot to features). v3 has run the SAME 14 price-derived
features (`V3_FEATURE_COLUMNS_TOP_N`) since /007; the /096 EDA found the
feature->label IC is thin on BCH (+0.025) and TRX (+0.029).

The decisive question, set as a hard Phase-1 GO/NO-GO: **is there a
candidate feature set that genuinely improves on the 14-feature stack in an
OOS-robust way** — not just an IS-CV-IC rank — on the /059 universe
BCH/LDO/TRX (NO universe axis, per the /097 Critic ruling)?

## 2. The two binding reckonings — and how this EDA addressed each

The /097 closeout flagged two non-negotiable constraints for /098. Both were
designed into the EDA, not waived:

### 2.1 — Constraint 1: OOS-robust selection, NOT IS-CV-IC rank

/096 and /097 demonstrated that a genuine, seed-stable IS feature->label IC
does NOT predict OOS in the v3 per-symbol framing — a naive IS-CV-IC ranking
is exactly the trap that produced /097's IS-up/OOS-down NEGATIVE. So the
selection statistic here was **not** IS-CV-IC. It was a **nested
expanding-window walk-forward held-out-tail test**: the candidate family is
added only if it lifts predictive accuracy on the **last 6 IS months** (the
"held-out tail" — strictly `open_time < OOS_CUTOFF`, the real OOS never
touched) when the model is trained ONLY on data before that tail. This is a
genuine pseudo-OOS generalization test — the closest IS-only proxy to the
real OOS question. The decisive lift statistic is paired across walk-forward
folds and symbols with a **block-bootstrap 95% CI** (block = the 21-bar
label horizon — the iter-v3/096 significance discipline), so a point-estimate
lift with a CI straddling zero is NOT a GO.

### 2.2 — Constraint 2: reconcile the prep memo against prior evidence

The prep memo (`briefs-v3/iter098_feature_research_memo.md`) flags order-flow
(Family A) as its #1 family. But iter-v3/094 ALREADY tested order-flow as a
directional signal and found it WEAK (NO-GO; return-IC ~0.10; signed
taker-volume imbalance sub-0.04). This EDA did **not** naively follow the
memo's headline. It re-tested order-flow under the two changes that make the
test genuinely fairer than /094's:

1. **The CORRECT label horizon.** /094 measured order-flow IC against a
   9-candle-timeout label. /094's own §3.1 horizon table shows order-flow IC
   PEAKS at the **21-bar** horizon (0.1286) and /094 explicitly states its
   9-candle label "cannot reach 21 bars." But /059's CANONICAL label is a
   **21-candle (10080-min) timeout**. /094 measured order-flow against the
   WRONG label horizon. This EDA uses the correct /059 21-candle label.
2. **As an AUGMENTATION, not standalone.** /094 tested order-flow as a
   standalone directional panel. This EDA tests it as an addition to the
   14-feature stack (`+A`) — a different question (does it help the model
   that already works?).

The 7-FEED INERT verdict (funding/OI/basis families, /019/023/024/082/085/086)
was honoured: Family G (the non-OHLCV caches) is NOT tested here. Family A
reads the `taker_buy_volume` / `quote_volume` / `trades` columns that are
ALREADY IN every `data/<SYM>/8h.csv` — NOT a separate cache. Family D
(statistical/complexity/entropy) was tested as the orthogonal runner-up the
memo §10 names.

## 3. The three candidate sets and the pre-registered 4-gate GO rule

| Set | Features | Family rationale |
|---|---|---|
| BASE | 14 (`V3_FEATURE_COLUMNS`) | the /059 anchor — the control |
| +A | 14 + 5 order-flow | taker-buy imbalance z, taker-buy ratio momentum, signed-volume OBV slope, log-Amihud illiquidity, trade-intensity z — Kyle 1985 / Amihud 2002 / VPIN grounding |
| +D | 14 + 4 stat/complexity | permutation entropy, sample entropy, variance ratio VR(2), return ACF lag-2 — Bandt-Pompe / Lo-MacKinlay |
| +AD | 14 + Family A + Family D (23 features) | the combined stack |

GO rule (pre-registered BEFORE the run; the GO threshold g1 is an absolute
floor SEPARATED from any predicted-band edge per the /097 Critic Rec 3): GO
if AT LEAST ONE candidate set clears all four gates —
- **g1** dShACC point estimate >= +0.010 (>=1pp held-out-tail accuracy lift),
- **g2** dShACC block-bootstrap 95% CI LOWER BOUND > 0 (statistically supported),
- **g3** dPnL point estimate > 0 (the accuracy lift translates to non-negative economic improvement — no accuracy/PnL inversion),
- **g4** the new family is NOT INERT — summed gain-importance share >= the uniform-parity share `n_new/n_total` (`feedback_v3_inert_features_at_higher_budget`: an INERT feature at higher budget HARMS OOS).

## 4. The result — NO-GO on every set, every gate

Source: `T4_paired_lift_bootstrap.csv`, `T5_importance_share.csv`,
`T6_go_nogo_verdict.csv`.

| Set | dShACC mean | dShACC 95% CI | dPnL mean | importance share / parity | Gates | Verdict |
|---|---:|---|---:|---|---|---|
| +A | **−0.0008** | [−0.0388, +0.0396] | **−0.27** | 0.169 / 0.263 | g1 FAIL, g2 FAIL, g3 FAIL, g4 FAIL | no |
| +D | **+0.0008** | [−0.0307, +0.0331] | **−0.02** | 0.180 / 0.222 | g1 FAIL, g2 FAIL, g3 FAIL, g4 FAIL | no |
| +AD | **−0.0242** | [−0.0686, +0.0170] | **−0.57** | 0.303 / 0.391 | g1 FAIL, g2 FAIL, g3 FAIL, g4 FAIL | no |

**Not one candidate set clears a single gate.** The verdict is decisive, not
borderline:

- **+A (order-flow) does NOT help — even against the correct 21-candle
  label.** Held-out-tail accuracy is fractionally WORSE than BASE
  (dShACC −0.0008), held-out-tail pred-side PnL is −0.27 worse, and the
  order-flow family claims only **16.9%** gain-importance vs its **26.3%**
  uniform-parity share — INERT. This is the central reconciliation finding:
  the EDA gave order-flow its fairest possible test (the /059 21-candle label
  /094 missed, AND the augmentation framing rather than standalone) and it
  STILL fails. /094's NO-GO is confirmed, not overturned — the horizon-mismatch
  caveat did not rescue order-flow.
- **+D (entropy) is statistically indistinguishable from BASE.** dShACC is
  +0.0008 — a point estimate of essentially zero — and its 95% CI
  [−0.031, +0.033] straddles zero by a wide margin (no statistical support,
  the /096 discipline). dPnL is −0.02 (flat-to-negative). Importance share
  18.0% < 22.2% parity — INERT. Entropy is orthogonal (it clears the |IC|
  gate, T2) but orthogonal-and-INERT is still INERT.
- **+AD (the combined stack) is the WORST — stacking actively HARMS.** dShACC
  −0.0242 (the model is materially LESS accurate on the held-out tail with
  23 features than with 14), dPnL −0.57. This is the
  `feedback_v3_inert_features_at_higher_budget` mechanism realized in the
  pseudo-OOS: a wider stack of INERT-importance features lets the tree fit
  IS noise that does not generalize. It also reproduces the
  `feedback_v3_engineered_features_dont_stack` lesson — two families stacked
  at single-seed do not add linearly; here they subtract.

**Redundancy gate (T2).** 8 of 9 candidate features clear the |IC|<0.7
pairwise gate vs the 14 incumbents. The one failure is `se_variance_ratio_2_50`
(Family D), max |Spearman| = 0.96 with `ret_autocorr_lag1_50` — a variance
ratio VR(2) is algebraically near-equivalent to lag-1 autocorrelation, so this
is expected and would be dropped in any GO build. It is recorded for
completeness; it does not change the verdict (even with VR(2) removed, +D
fails g1/g2/g3/g4).

## 5. The honest methodology read — why this NO-GO is structural, not a tuning miss

This is the **fourth consecutive cycle-4 EXPLORATION to fail on the same
underlying constraint**, and the pattern is now a structural verdict:

- /094 — order-flow as a directional ALPHA feature: NO-GO at EDA.
- /096 — pooled cross-symbol model: NO-GO at EDA (cross-symbol transfer CIs straddle zero).
- /097 — symbol-universe re-selection: NEGATIVE (IS-up/OOS-down).
- /098 — feature expansion (order-flow + entropy augmentation): NO-GO at EDA.

The binding constraint is NOT *which* features, NOT *which* symbols, and NOT
*which* model architecture. It is that **the v3 per-symbol BCH/LDO/TRX 8h
triple-barrier prediction problem has thin signal that the existing 14-feature
stack already substantially captures.** /096 measured this directly (within-
symbol IC +0.025 BCH / +0.029 TRX — thin); /098 now shows that two
theoretically well-grounded NEW feature families — order-flow (the memo's #1,
re-tested at the correct label horizon) and statistical-complexity (the
orthogonal runner-up) — add nothing the 14 incumbents do not already encode,
and stacked, they actively degrade held-out-tail accuracy. The memo's
remaining families (B volatility estimators, C TA-Lib momentum, E jump,
F cross-asset) all share an information source with the 14 incumbents (all
price-derived) — the |IC| gate would bind hardest there and the /063
mass-expansion collapse (14->46 features, IS Sharpe −1.38) already showed a
wide price-derived stack does not transfer. There is no foreseeable feature
family with untapped OOS-robust signal in the kline data on this universe.

Killing this at the EDA cost **one committed IS-only EDA script: no `fetch`,
no runner change, no backtest, no Critic, no agent dispatch.**

## 6. Next-axis recommendation

The feature-expansion axis is the third v3 forward lever (after symbols, after
features) to close. Within the kline-data + per-symbol-LightGBM frame, the
EXPLORATION space is genuinely exhausted: features (this iteration), symbols
(/097 Critic ruling), pooled-vs-single architecture (/096), crypto-native
feeds (the 7-FEED verdict). The next iteration must step OUTSIDE that frame.

**Recommended iter-v3/099 axis — a NEW MODEL ARCHITECTURE that can compose
feature interactions a depth-3-5 tree cannot: a shallow MLP or an
attention-pooled sequence model on the existing validated 14-feature stack.**
This is the axis the /094 AND /095 closeouts BOTH named as the remaining
un-tried structural lever, and it attacks the actual binding constraint
honestly: if the 14 features carry thin *linear/low-order* signal that a
depth-3-5 tree cannot compose into a higher-order interaction, a learner with
genuine interaction capacity is the one thing that has not been tested. The
caveat is real and must gate the iteration: iter-v3/016's LightGBM->XGBoost
change was the worst OOS Δ in v3 history (−2.53), so a model-architecture axis
cannot be a cheap EDA GO/NO-GO — it requires a full build + backtest. The
iter-v3/099 QR should therefore treat it as a deliberate, pre-registered
CONFIRMATION-discipline bet (multi-seed, pre-registered PROMISING bands),
NOT a single-seed lottery. Per `feedback_v3_axis_selection_quant_discipline.md`
the /099 QR commits an EDA-driven quantitative basis before the brief — here
the EDA is necessarily a *characterization* (e.g. measuring residual
predictability after the tree, or interaction-strength diagnostics) rather
than a GO/NO-GO, and the brief Section 10 must state that explicitly.

A genuine fallback if the model-architecture axis is judged too expensive:
re-examine the LABEL (a meta-labeled or volatility-scaled target — the /096
closeout's recommendation, never actually run as an EXPLORATION; iter-v3/017
closed only the meta-labeling over-filter failure mode at one configuration).
The label, like the model, is a frame-level lever that the feature and symbol
exhaustion leaves open.

---

**Artifacts (committed to `iteration-v3/098`):**
- `analysis/iteration_v3-098/feature_expansion_go_nogo_eda.py` — the GO/NO-GO EDA.
- `analysis/iteration_v3-098/T1_is_panel_summary.csv` — per-symbol IS panel + held-out-tail row counts.
- `analysis/iteration_v3-098/T2_redundancy_vs_incumbents.csv` — candidate-family |IC| vs the 14 incumbents.
- `analysis/iteration_v3-098/T3_walkforward_tail_eval.csv` — per-(set, symbol) held-out-tail accuracy + pred-side PnL.
- `analysis/iteration_v3-098/T4_paired_lift_bootstrap.csv` — PRIMARY: paired dShACC + dPnL over BASE with block-bootstrap 95% CI.
- `analysis/iteration_v3-098/T5_importance_share.csv` — multivariate gain-importance share — the INERT screen.
- `analysis/iteration_v3-098/T6_go_nogo_verdict.csv` — the decisive verdict table (VERDICT = NO-GO).
- `analysis/iteration_v3-098/eda_output.txt` — full stdout transcript.
- `analysis/iteration_v3-098/NO_GO_NOTE.md` — this note.
- `diary-v3/iteration_v3-098.md` — the NULL-AT-EDA closeout stub.

**`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The EDA
is strictly IS-only — every measurement restricted to `open_time <
OOS_CUTOFF_MS`; the held-out tail is the last 6 IS months, still strictly
inside IS. The real OOS was never touched.** BASELINE_V3.md UNCHANGED —
canonical /059 (IS +1.0894 / OOS +0.5791, tag `v0.v3-059`).

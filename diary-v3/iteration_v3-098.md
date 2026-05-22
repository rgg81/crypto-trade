# iter-v3/098 — Cycle-4 EXPLORATION #6 — FEATURE EXPANSION — FILED NULL-AT-EDA — Phase-1 GO/NO-GO returned NO-GO; axis killed cheaply at the EDA, no brief, no backtest

**Date**: 2026-05-18
**Type**: EXPLORATION (cycle-4 slot #6 of 10) — Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
**Verdict**: **NO-GO** — Phase-1 IS-only EDA. The feature-expansion axis is killed at the EDA. No 10-section research brief was written; no runner change; no backtest was run.
**Classification**: **NULL-AT-EDA** — no candidate feature family clears the OOS-robustness bar from a committed IS-only EDA artifact. Killing it cheaply at the EDA is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**).
**Branch**: `iteration-v3/098`

---

## 1. What iter-v3/098 tested

iter-v3/098 is the FEATURE-EXPANSION iteration mandated by the user's
2026-05-18 directive (`feedback_v3_bold_research_mandate.md` — features are
the crucial 8h-candle lever) and the /097 Critic Recommendation 2
(symbol-screening exhausted — pivot to features). v3 has run the same 14
price-derived features since /007; /096 found feature->label IC is thin
(+0.025 BCH / +0.029 TRX).

Phase 1 was a hard FAIL-FAST GO/NO-GO. A committed IS-only EDA
(`analysis/iteration_v3-098/feature_expansion_go_nogo_eda.py`) tested whether
expanding the 14-feature stack genuinely lifts the per-symbol model's
predictive power on BCH/LDO/TRX (the /059 universe — NO universe axis, per
the /097 Critic). Three candidate sets: **+A** (14 + 5 order-flow features:
taker-buy imbalance z, taker-buy ratio momentum, signed-volume OBV slope,
log-Amihud illiquidity, trade-intensity z — from the `taker_buy_volume` /
`trades` kline columns the 14 incumbents ignore), **+D** (14 + 4
statistical/complexity features: permutation entropy, sample entropy,
variance ratio, return ACF lag-2), **+AD** (the combined 23-feature stack).

The two binding reckonings the /097 closeout mandated were designed INTO the
EDA, not waived:

1. **OOS-robust selection — NOT IS-CV-IC rank.** /096/097 proved IS-CV-IC
   does not predict OOS. The selection statistic here was a **nested
   expanding-window walk-forward held-out-tail test** — the candidate family
   is added only if it lifts predictive accuracy on the last 6 IS months
   (held-out tail, strictly `open_time < OOS_CUTOFF`, real OOS never touched)
   when the model is trained ONLY on data before that tail. The lift is
   paired across folds and symbols with a block-bootstrap 95% CI (block = the
   21-bar label horizon — the /096 significance discipline). A point-estimate
   lift with a CI straddling zero is not a GO.

2. **Reconcile the prep memo against /094.** The memo flags order-flow as #1,
   but /094 already found order-flow WEAK as a directional signal. This EDA
   did NOT follow the memo's headline naively — it re-tested order-flow under
   the two changes that make the test genuinely fairer than /094's:
   **(a)** the CORRECT /059 21-candle label (/094 used a 9-candle label, and
   /094's own §3.1 table shows order-flow IC PEAKS at the 21-bar horizon
   0.1286 — /094 measured against the wrong label horizon); **(b)** as an
   AUGMENTATION to the 14-stack, not standalone. The 7-FEED INERT verdict was
   honoured — Family G (non-OHLCV caches) was NOT tested; Family A reads
   columns already in every kline CSV.

## 2. Result — NO-GO on every set, every gate

Source: `analysis/iteration_v3-098/T4_paired_lift_bootstrap.csv`,
`T5_importance_share.csv`, `T6_go_nogo_verdict.csv`.

| Set | dShACC mean | dShACC 95% CI | dPnL mean | importance / parity | Verdict |
|---|---:|---|---:|---|---|
| +A | **−0.0008** | [−0.0388, +0.0396] | **−0.27** | 0.169 / 0.263 | no |
| +D | **+0.0008** | [−0.0307, +0.0331] | **−0.02** | 0.180 / 0.222 | no |
| +AD | **−0.0242** | [−0.0686, +0.0170] | **−0.57** | 0.303 / 0.391 | no |

The pre-registered 4-gate GO rule (g1 dShACC ≥ +0.010; g2 CI lower bound > 0;
g3 dPnL > 0; g4 importance share ≥ uniform parity) is FAILED on all four
gates by all three sets. The verdict is decisive, not borderline:

- **+A (order-flow) does NOT help — even against the correct 21-candle
  label.** Held-out-tail accuracy fractionally WORSE than BASE (−0.0008),
  pred-side PnL −0.27 worse, importance share 16.9% vs 26.3% parity → INERT.
  This is the central reconciliation finding: the EDA gave order-flow its
  fairest test (the 21-candle label /094 missed + the augmentation framing)
  and it STILL fails. **/094's NO-GO is confirmed, not overturned** — the
  horizon-mismatch caveat did not rescue order-flow.
- **+D (entropy) is statistically indistinguishable from BASE.** dShACC
  +0.0008 ≈ zero; 95% CI [−0.031, +0.033] straddles zero widely; importance
  18.0% < 22.2% parity → INERT. Orthogonal (clears |IC|, T2) but
  orthogonal-and-INERT is still INERT.
- **+AD (combined) is the WORST — stacking actively HARMS.** dShACC −0.0242
  (the model is materially LESS accurate on the held-out tail with 23
  features than with 14), dPnL −0.57. The
  `feedback_v3_inert_features_at_higher_budget` mechanism realized in the
  pseudo-OOS, and a reproduction of `feedback_v3_engineered_features_dont_stack`.

One Family-D feature (`se_variance_ratio_2_50`) fails the |IC|<0.7 redundancy
gate (0.96 with `ret_autocorr_lag1_50`, expected — VR(2) ≈ lag-1 autocorr);
recorded for completeness, immaterial to the verdict.

## 3. The methodology read — the binding constraint is the signal, not the features

This is the **fourth consecutive cycle-4 EXPLORATION to fail on the same
underlying constraint**: /094 (order-flow alpha — NO-GO), /096 (pooled model —
NO-GO), /097 (symbol re-selection — NEGATIVE), /098 (feature expansion —
NO-GO). The binding constraint is NOT *which* features, NOT *which* symbols,
NOT *which* architecture — it is that **the v3 per-symbol BCH/LDO/TRX 8h
triple-barrier prediction problem has thin signal that the 14-feature stack
already substantially captures.** Two theoretically well-grounded NEW
families — order-flow (the memo's #1, re-tested at the correct label horizon)
and statistical-complexity (the orthogonal runner-up) — add nothing the
incumbents do not encode; stacked, they degrade held-out-tail accuracy. The
memo's other families (B/C/E/F) are all price-derived, so the |IC| gate binds
hardest there and the /063 mass-expansion collapse (14→46, IS −1.38) already
showed a wide price-derived stack does not transfer.

Killed for the cost of one committed IS-only EDA: no `fetch`, no runner
change, no backtest, no Critic, no agent dispatch.

## 4. Next-axis recommendation — iter-v3/099

The feature lever is the third v3 forward lever to close (after symbols,
after pooled-vs-single). Within the kline-data + per-symbol-LightGBM frame
the EXPLORATION space is exhausted. The next iteration must step OUTSIDE that
frame.

**Recommended iter-v3/099 axis — a NEW MODEL ARCHITECTURE that can compose
feature interactions a depth-3-5 tree cannot: a shallow MLP or an
attention-pooled sequence model on the existing validated 14-feature stack.**
Both the /094 and /095 closeouts named this as the remaining un-tried
structural lever. It attacks the binding constraint honestly: if the 14
features carry thin low-order signal a depth-3-5 tree cannot compose into a
higher-order interaction, a learner with genuine interaction capacity is the
one thing untested. CAVEAT (must gate the iteration): iter-v3/016's
LightGBM→XGBoost change was the worst OOS Δ in v3 history (−2.53), so a
model-architecture axis cannot be a cheap EDA GO/NO-GO — it requires a full
build + backtest, and the /099 QR must treat it as a deliberate
CONFIRMATION-discipline bet (multi-seed, pre-registered PROMISING bands), NOT
a single-seed lottery. Per `feedback_v3_axis_selection_quant_discipline.md`
the /099 QR commits an EDA-driven quantitative basis before the brief — here
necessarily a *characterization* EDA (residual-predictability /
interaction-strength diagnostics), not a GO/NO-GO; the brief Section 10 must
state that explicitly.

Genuine fallback if the model axis is judged too expensive: re-examine the
LABEL (a meta-labeled or volatility-scaled target — the /096 closeout's
never-run recommendation; iter-v3/017 closed only the meta-labeling
over-filter at one configuration). The label, like the model, is a
frame-level lever the feature/symbol exhaustion leaves open.

## 5. Commit chain

- EDA SHA: `9e69cd0` — `analysis(iter-v3/098): feature-expansion GO/NO-GO EDA + T1-T6 + NO_GO_NOTE`.
- Diary SHA: this closeout — `docs(iter-v3/098): closeout diary — FILED NULL-AT-EDA / Phase-1 GO/NO-GO = NO-GO`.
- **No brief** (`briefs-v3/iteration_v3-098/` not created — NO-GO stopped the iteration at Phase 1).
- **No reports** (no backtest run).
- **Tag**: `v0.v3-098` (closeout marker; NOT a baseline update — the `v0.v3-082`…`v0.v3-097` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`).

iter-v3/098 is cycle-4 EXPLORATION slot #6 of 10; the cadence advances.
iter-v3/099 is slot #7 — the NEW-MODEL-ARCHITECTURE iteration (Section 4).

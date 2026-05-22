# iter-v3/099 — Cycle-4 EXPLORATION #7 — ABSTENTION-AWARE LABEL — FILED NULL-AT-EDA — Phase-1 GO/NO-GO returned NO-GO; axis killed cheaply at the EDA, no brief, no backtest

**Date**: 2026-05-18
**Type**: EXPLORATION (cycle-4 slot #7 of 10) — Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
**Verdict**: **NO-GO** — Phase-1 IS-only EDA. The abstention-aware-label axis is killed at the EDA. No 10-section research brief was written; no runner change; no backtest was run.
**Classification**: **NULL-AT-EDA** — the decisive premise (the NO-TRADE class is feature-learnable at decision time) fails out-of-window on a committed IS-only EDA artifact. Killing it cheaply at the EDA is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**).
**Branch**: `iteration-v3/099`

---

## 1. The axis committed — and why over the alternatives

Per `feedback_v3_axis_selection_quant_discipline.md` the /099 axis was committed by the QR with a committed EDA basis. The user (2026-05-18) named three candidate axis-types — labeling re-architecture, NEW engineered-feature families, regime-switching constructions — and asked for an altcoin axis with a CHEAP Phase-1 GO/NO-GO.

The axis committed: a **LABELING RE-ARCHITECTURE — an abstention-aware triple-class label {LONG, SHORT, NO-TRADE}.** v3's canonical label (`labeling.py:label_trades`, `label_mode="triple_barrier"`) produces a BINARY direction for EVERY candle. When no TP barrier is hit in either direction (`labeling.py` lines 337-347), the label falls back to `sign(fwd_return)` — so a candle whose forward path chops sideways, where BOTH net directional PnLs are negative, STILL receives a confident long/short training label. The primary LightGBM is trained to call a side on candles with NO tradeable directional edge. The abstention axis relabels those edge-free candles to a third NO-TRADE class so the primary model learns *where* edge exists, not only *which side*. The barrier mechanics are unchanged.

This is a genuinely NEW labeling construction, not a retread of the three prior labeling iterations:
- **/010** (ATR multipliers 2.9/1.45 → 2.0/1.0) — a barrier-geometry knob; the abstention axis changes the label's class structure, not the barrier scale.
- **/017** (meta-labeling) — an M2 secondary classifier FILTERS M1's side post-hoc; the abstention here is IN THE LABEL, learned by the PRIMARY model — a different object.
- **/072** (fixed-horizon-21 return-sign) — still a binary return-sign label; failed on a label-execution mismatch; the abstention axis preserves the barrier execution semantics.

Why this over the user's other two named types: a **regime-switching MODEL** (the /095/096 non-tree-sequence-learner recommendation) cannot be a cheap EDA GO/NO-GO — /016's LightGBM→XGBoost model-arch change was the worst OOS Δ in v3 history (−2.53), so a model-arch axis requires a full build + backtest, contradicting the user's strong fail-fast preference. A **NEW composed engineered feature** was just NO-GO'd one slot earlier at /098 (feature expansion); the /096/097/098 closeouts converge that the binding constraint is the label/signal, not the feature space. The abstention-label axis attacks the actual binding constraint AND admits a cheap, non-circular Phase-1 GO/NO-GO — exactly the fail-fast profile /094/095/096/098 were killed under.

## 2. Phase 1 — the FAIL-FAST GO/NO-GO EDA — NO-GO

A committed IS-only EDA (`analysis/iteration_v3-099/abstention_label_go_nogo_eda.py`, walk-forward-faithful, strictly `open_time < OOS_CUTOFF_MS = 1742774400000`) tested the axis's decisive premise on BCH/LDO/TRX. Two binding sub-premises, four pre-registered gates:

- **P1 FORCING** — is the binary label forced on a material fraction of edge-free candles?
- **P2 LEARNABILITY** — is the NO-TRADE class PREDICTABLE FROM FEATURES at decision time, above chance, OUT-OF-WINDOW? This is the load-bearing, **non-circular** test: an abstention label is useful only if the primary model can LEARN it; if edge-free vs traded is feature-indistinguishable, relabeling ~30% of candles NO-TRADE merely deletes training rows at random.

The methodology was OOS-robust, NOT a naive IS-IC ranking (the /096/097 lesson). The P2 statistic is the held-out AUC of a LightGBM classifier (the exact learner family the v3 primary model uses) trained to predict the `edge_free` label from a scale-invariant feature panel — drawn from the same families as `V3_FEATURE_COLUMNS` (realized vol, momentum, range, autocorrelation, skew/kurtosis, RSI, volume z) — under an expanding-window walk-forward over the last 6 one-month IS folds, each fold's classifier trained ONLY on candles strictly before it. Non-circularity is structural: the classifier sees ONLY past-only features (NEVER `best_edge`, NEVER any barrier outcome) and predicts the `edge_free` label out-of-window. Significance was a genuine candle-level block-bootstrap 95% CI (block = the 21-bar label horizon, the /096 overlapping-label discipline). Source: `analysis/iteration_v3-099/T1_forcing.csv`, `T3_bootstrap_ci.csv`, `T4_go_nogo_verdict.csv`.

| Gate | Statistic | Threshold | Value | Verdict |
|---|---|---|---:|---|
| g1 FORCING | pooled edge-free candle fraction | ≥ 0.15 | **0.2968** | PASS |
| g2 LEARNABILITY | pooled held-out AUC of the edge_free classifier | ≥ 0.55 | **0.5480** | **FAIL** |
| g3 LEARNABILITY sig | candle-level block-bootstrap 95% CI lower bound of the AUC | > 0.50 | 0.5018 | pass (marginal) |
| g4 EDGE GRADIENT | mean net barrier PnL, top vs bottom feature-score tercile | > 0 | 0.5074 | pass |

The pre-registered GO rule is `g1 AND g2 AND g3 AND g4`. **g2 FAILS — VERDICT NO-GO.**

## 3. The result read — the abstention class exists in the LABEL but is NOT feature-learnable

The verdict is decisive, and the two-part split is the substantive finding:

- **g1 PASS confirms the binding-constraint diagnosis.** ~29.7% of v3 candles are genuinely edge-free — no TP hit in either direction AND the better of the two net directional PnLs is negative. The binary label IS forced onto a large noise population, exactly as the axis hypothesized. The diagnosis is real.
- **g2 FAIL is the kill.** When a LightGBM classifier is trained on prior IS data to predict the edge-free class, its held-out-fold AUC is **0.548 — barely above the 0.50 coin-flip**, below the pre-registered 0.55 substantive floor. The per-fold AUCs (`T2_holdout_learnability.csv`) oscillate around 0.50 with no stability — BCH 0.474–0.725, LDO 0.378–0.750, TRX 0.444–0.686 — the fold-lottery signature of a class that is NOT genuinely learnable, not a consistent above-chance signal. g3's CI lower bound (0.5018) clears 0.50 only on the strength of the few high-AUC folds; the substantive point estimate fails.

The honest read: the abstention LABEL would be a coherent, genuinely-new construction — but a label is only useful if the primary model can LEARN it from the features it sees at the candle close, and the EDA shows it cannot. At AUC 0.548, relabeling ~30% of candles NO-TRADE is close to deleting training rows at random — it would not concentrate the model's learning on edge-bearing candles, it would just shrink the training set. This is the same binding constraint /094-/098 hit, sharpened: the thin per-symbol 8h triple-barrier signal does not carry enough structure for a model to predict even *where* directional edge is absent.

Killed for the cost of one committed IS-only EDA: no `fetch`, no runner change, no backtest, no Critic, no agent dispatch. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched; every measurement strictly IS-only; OOS never touched.

## 4. Next-axis recommendation — iter-v3/099 is cycle-4 slot #7; slot #8 is next

This is the **fifth consecutive cycle-4 EXPLORATION to fail on the same binding constraint** — /094 (order-flow alpha, NO-GO), /096 (pooled model, NO-GO), /097 (universe re-selection, NEGATIVE), /098 (feature expansion, NO-GO), /099 (abstention label, NO-GO). Across symbols, architecture, features, and now the label's class structure, the recurring finding is unchanged: the v3 per-symbol BCH/LDO/TRX 8h triple-barrier prediction problem has thin signal, and the lever under test never carries enough structure to lift it. /099 adds a specific new fact: the edge-free population, though large (~30%), is not feature-separable out-of-window — so an in-label abstention class cannot be the fix.

**Recommended iter-v3/099-slot-#8 axis — a REGIME-SWITCHING MODEL construction (the user's third named axis-type), specifically a per-symbol two-expert mixture: separate LightGBM models trained on the trending vs mean-reverting regime sub-samples (split by a past-only Hurst/ADX gate), each expert specializing in its regime.** This is genuinely distinct from /093's regime OVERLAY (which gated position SIZE on a single base book and was BLOCKED as a confounded build) — a two-expert mixture trains *different models* on *different regime sub-populations*, so each expert sees a less heterogeneous label distribution. It attacks the /099 finding directly: if the aggregate signal is thin partly because trending-regime and mean-reverting-regime candles demand opposite directional responses (the `regime_momentum_signed_5d` /025 finding showed exactly this interaction is real), then conditioning the *model* on regime — not the label, not a size overlay — is the untested lever. CAVEAT: a model-architecture axis is NOT a cheap EDA GO/NO-GO; the slot-#8 QR must treat it as a deliberate build with pre-registered PROMISING bands, and the Phase-1 EDA can only be a *characterization* EDA (does the per-regime feature→label IC differ materially between the two sub-samples — the necessary precondition for two experts to beat one), not a hard GO/NO-GO. Genuine cheaper fallback if the model axis is judged too expensive: a volatility-scaled CONTINUOUS label target (regress the volatility-normalized forward return instead of classifying its sign) — a frame-level labeling lever the abstention NO-GO leaves open and distinct from /072's fixed-horizon sign relabel.

## 5. Commit chain

- EDA SHA: `d8c5eb1` — `analysis(iter-v3/099): abstention-aware label GO/NO-GO EDA + T1-T4 + verdict` — `analysis/iteration_v3-099/abstention_label_go_nogo_eda.py` + `T1_forcing.csv` + `T2_holdout_learnability.csv` + `T3_bootstrap_ci.csv` + `T4_go_nogo_verdict.csv`.
- Diary SHA: this closeout — `docs(iter-v3/099): closeout diary — FILED NULL-AT-EDA / Phase-1 GO/NO-GO = NO-GO`.
- **No brief** (`briefs-v3/iteration_v3-099/` not created — NO-GO stopped the iteration at Phase 1).
- **No reports** (no backtest run).
- **Tag**: `v0.v3-099` (closeout marker; NOT a baseline update — the `v0.v3-082`…`v0.v3-098` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`).

iter-v3/099 is cycle-4 EXPLORATION slot #7 of 10; the cadence advances. Slot #8 is the regime-switching-model iteration (Section 4).

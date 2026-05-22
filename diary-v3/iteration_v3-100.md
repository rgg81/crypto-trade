# iter-v3/100 — Cycle-4 EXPLORATION #8 — REGIME-SWITCHING TWO-EXPERT MIXTURE — FILED NULL-AT-EDA — Phase-1 GO/NO-GO returned NO-GO; axis killed cheaply at the EDA, no brief, no backtest

**Date**: 2026-05-18
**Type**: EXPLORATION (cycle-4 slot #8 of 10) — Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
**Verdict**: **NO-GO** — Phase-1 IS-only EDA. The regime-switching two-expert-mixture axis is killed at the EDA. No 10-section research brief was written; no runner change; no backtest was run.
**Classification**: **NULL-AT-EDA** — the decisive premise (the trending vs mean-reverting regime sub-samples carry genuinely different, separately-learnable feature→label structure) fails out-of-window on a committed IS-only EDA artifact. Killing it cheaply at the EDA is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**).
**Branch**: `iteration-v3/100`

---

## 1. The axis committed — and why

Per `feedback_v3_axis_selection_quant_discipline.md` the /100 axis was committed by the QR with a committed EDA basis. The /099 closeout recommended /100 = a **per-symbol two-expert REGIME-SWITCHING MIXTURE** — separate LightGBM models trained on the trending vs the mean-reverting regime sub-samples of each symbol's IS data (a past-only Hurst/ADX regime split), with the live model selected by the contemporaneous past-only regime. This is one of the user's three named axis-types ("regime-switching constructions").

It is genuinely distinct from iter-v3/093's BLOCKED regime size-*overlay*: /093 gated POSITION SIZE on a single base book (a confounded build that was BLOCKED); /100 is a MODEL-CONSTRUCTION split — two *different models* trained on two *different regime sub-populations*, so each expert sees a less heterogeneous label distribution. The /099 hypothesis: if the aggregate signal is thin partly because trending-regime and mean-reverting-regime candles demand different directional responses, conditioning the *model* on regime is the untested lever.

## 2. Phase 1 — the FAIL-FAST GO/NO-GO EDA — NO-GO

A committed IS-only EDA (`analysis/iteration_v3-100/regime_split_go_nogo_eda.py`, walk-forward-faithful, strictly `open_time < OOS_CUTOFF_MS = 1742774400000`) tested the axis's decisive premise on BCH/LDO/TRX. The methodology is OOS-robust, NOT a naive IS-CV-IC ranking (the /096/097 lesson): the load-bearing test (T3) is a **held-out-fold horse race** — an expanding-window walk-forward over the last 8 one-month IS folds; per fold, train ONE pooled LightGBM on all prior IS candles AND TWO regime-expert LightGBMs each on the prior IS candles of one regime; on the held-out fold, route each candle to its regime expert (the mixture) and compare the mixture against the pooled model on directional accuracy and net side-PnL. Regime routing is PAST-ONLY (Hurst-100/ADX-14 at the candle close — trailing windows only). Labels replicate `labeling.py:label_trades` exactly (ATR triple-barrier 2.0/1.0, `natr_21_raw`, timeout 21 candles, fee 0.1%). Significance is a candle-level block bootstrap, block = the 21-bar label horizon (the /096 overlapping-label discipline).

Four pre-registered gates, GO rule `g1 AND g2 AND g3 AND g4`:

| Gate | Statistic | Threshold | Value | Verdict |
|---|---|---|---:|---|
| g1 SEPARABILITY | pooled minority-regime fraction | ≥ 0.20 | **0.4942** | PASS |
| g2 STRUCTURE-DIFF | mean own-minus-other-regime held-out AUC gap | ≥ 0.04 | **−0.0033** | **FAIL** |
| g3 MIXTURE-LIFT | mixture−pooled held-out acc lift; mean > 0 AND block-bootstrap 95% CI lower bound > 0 | mean>0 & CI_lo>0 | **+0.0068** | **FAIL** |
| g4 MIXTURE-PNL | mixture−pooled held-out side-PnL lift; mean > 0 | mean > 0 | **−0.0155** | **FAIL** |

T3 acc_lift block-bootstrap 95% CI = **[−0.0110, +0.0283]** — straddles zero. **g2, g3 (the decisive gate), and g4 all FAIL — VERDICT NO-GO.** Source: `analysis/iteration_v3-100/T1_regime_separability.csv` … `T4_go_nogo_verdict.csv`.

## 3. The result read — the regime split is REAL but carries no SEPARABLE structure

- **g1 PASS — the split is real and well-balanced.** The past-only Hurst-100 > 0.5 AND ADX-14 ≥ IS-median conjunction places ~49% of candles trending / ~51% mean-reverting on every symbol (BCH 49.4/50.6, LDO 49.2/50.9, TRX 49.6/50.4). Both experts would have ample training data — the axis is NOT killed by a degenerate split. The regime partition itself is sound.

- **g2 FAIL — the regimes do NOT carry different feature→label maps.** The cross-regime degradation test (train an expert on regime A, score it held-out on regime A vs regime B) returns a mean own-minus-other AUC gap of **−0.0033 — essentially zero, and the WRONG sign**. Decomposed (`T2_cross_regime_structure.csv`): the **mean-reverting experts score the held-out TRENDING fold BETTER than their own regime** (gaps −0.045 BCH / −0.067 LDO / −0.119 TRX), while the trending experts score the mean-rev fold only slightly worse. If the two regimes carried genuinely different structure, each expert would score its OWN regime best (positive gap both ways). They do not — there is one shared, thin feature→label map, with a harder slice (trending) and an easier slice (mean-reverting), not two different maps.

- **g3 FAIL — the decisive gate.** The two-expert mixture's held-out-fold directional accuracy beats the pooled model by only **+0.0068**, statistically indistinguishable from zero (95% CI [−0.011, +0.028]). The per-symbol split is the fold-lottery signature, NOT a consistent edge: the mixture "wins" BCH (+0.0144) and TRX (+0.0248) and LOSES LDO (−0.0187). A genuine regime-specialist gain would be sign-consistent across all three symbols.

- **g4 FAIL — and it does not convert to PnL.** Mixture side-PnL lift **−0.0155**, dragged negative by LDO (−0.3791): splitting LDO's already-thin 2,641-candle IS sample into two halves, each expert overfits and the mixture materially underperforms the pooled LDO model.

The honest read: the trending vs mean-reverting regime split is a real, well-balanced partition — but the two halves carry the SAME thin feature→label structure, not different separable structure. Routing to a regime expert merely halves each expert's training set; on LDO (the thinnest symbol) this strictly HURTS. Same binding constraint /094-/099 hit, in a new dress: the v3 per-symbol BCH/LDO/TRX 8h triple-barrier signal is so thin there is not even enough regime-conditional structure for two specialists to beat one generalist. Note also `feedback_v3_engineered_features_proven.md`: `regime_momentum_signed_5d` (= ret_5d × sign(hurst_100 − 0.5)) ALREADY encodes the regime×momentum interaction as a FEATURE inside the single /059 model — the pooled model already has the regime signal; promoting regime from a feature to a model-construction split adds nothing and costs each expert half its data.

Killed for the cost of one committed IS-only EDA: no `fetch`, no runner change, no backtest, no Critic, no agent dispatch. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched; every measurement strictly IS-only; OOS never touched.

## 4. Next-axis recommendation — iter-v3/100 is cycle-4 slot #8; slot #9 is next

This is the **sixth consecutive cycle-4 EXPLORATION to fail on the same binding constraint** — /094 (order-flow alpha, NO-GO), /096 (pooled model, NO-GO), /097 (universe re-selection, NEGATIVE), /098 (feature expansion, NO-GO), /099 (abstention label, NO-GO), /100 (regime-switching mixture, NO-GO). The recurring finding across symbols, architecture, features, the label's class structure, and now a regime-conditional model split is unchanged: the v3 per-symbol BCH/LDO/TRX 8h triple-barrier prediction problem has thin signal, and the lever under test never carries enough structure to lift it. /100 adds a specific new fact: the regime sub-samples are well-balanced but NOT separately learnable — they share one thin feature→label map.

**Recommended iter-v3/100-slot-#9 axis — a SAMPLE-WEIGHTING / LABEL-RECONSTRUCTION axis attacking the thin-signal constraint directly rather than re-partitioning the model: AFML-Ch.4 uniqueness-weighted training combined with a magnitude-weighted (best-edge-proportional) sample weight, EDA-gated.** The /100 g2/g3 evidence sharpens the diagnosis — the model does not need a different *partition*, it needs the existing thin signal *concentrated*. v3's `label_trades` already returns a fee-aware `weight` (the net-PnL magnitude, normalized to [1,10]) but the runner's downstream use of it is worth a focused EDA: does up-weighting high-`best_edge` candles AND down-weighting overlapping (low-uniqueness) candles measurably lift held-out-fold directional skill on BCH/LDO/TRX? `compute_sample_uniqueness` is ALREADY in `labeling.py` (the AFML overlapping-label correction) and is cheaply Phase-1-gateable with the same held-out-fold horse-race harness this EDA built — a strictly cheaper, non-circular GO/NO-GO than a model-architecture axis. It attacks the binding constraint (thin signal) at the training-objective level, the one frame /094-/100 left untouched (symbols, features, model arch, label class structure, regime split all closed). Genuine fallback if sample-weighting is judged exhausted: given that six consecutive cycle-4 EXPLORATIONs have now confirmed the v3 per-symbol 8h signal is structurally thin, the slot-#9 QR should also weigh whether cycle 4 should close early to a CONFIRMATION-style re-validation of /059 rather than spend slots #9-#10 on further thin-signal levers — but per the user's "try a bit more" directive, the sample-weighting axis is the recommended next altcoin axis within the v3 mandate.

## 5. Commit chain

- EDA SHA: `analysis(iter-v3/100): regime-split GO/NO-GO EDA + T1-T4 + NO_GO_NOTE` — `analysis/iteration_v3-100/regime_split_go_nogo_eda.py` + `T1_regime_separability.csv` + `T2_cross_regime_structure.csv` + `T3_mixture_horse_race.csv` + `T3_bootstrap_ci.csv` + `T4_go_nogo_verdict.csv` + `NO_GO_NOTE.md`.
- Catalog backfill SHA: `f255edf` — `docs(iter-v3/099): backfill exploration_catalog row` (Task 0, separate).
- Diary SHA: this closeout — `docs(iter-v3/100): closeout diary — FILED NULL-AT-EDA / Phase-1 GO/NO-GO = NO-GO`.
- **No brief** (`briefs-v3/iteration_v3-100/` not created — NO-GO stopped the iteration at Phase 1).
- **No reports** (no backtest run).
- **Tag**: `v0.v3-100` (closeout marker; NOT a baseline update — the `v0.v3-082`…`v0.v3-099` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`).

iter-v3/100 is cycle-4 EXPLORATION slot #8 of 10; the cadence advances. Slot #9 is the sample-weighting / label-reconstruction iteration (Section 4).

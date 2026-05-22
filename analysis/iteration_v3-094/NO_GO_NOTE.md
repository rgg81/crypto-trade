# iter-v3/094 — Phase-1 GO/NO-GO EDA closeout note — VERDICT: NO-GO

**Date**: 2026-05-18
**Type**: cycle-4 EXPLORATION slot #2 of 10 — Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
**Verdict**: **NO-GO** — the derivatives ORDER-FLOW-directional axis is KILLED at the EDA. No 10-section brief, no backtest.
**Classification**: **NULL-AT-EDA** — the axis is foreseeably-modest from a committed IS-only EDA artifact already in hand; killing it cheaply at the EDA is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure.

---

## 1. The decisive question and the GO/NO-GO rule

iter-v3/094 is the cycle-4 PIVOT recommended by the /093 closeout (`diary-v3/iteration_v3-093.md` Section 5): use derivatives microstructure as a **directional ALPHA signal** — a per-symbol directional LightGBM whose feature panel is the **derivatives order-flow state** (signed taker-volume imbalance, OI delta, long/short positioning ratios), predicting the /059-style triple-barrier label. Universe BCH/LDO/TRX.

Research grounding: Anastasopoulos, Gradojevic, Liu, Maynard & Tsiakas, "Order Flow and Cryptocurrency Returns" (Journal of Financial Markets; SSRN 5020002) — non-linear ML on **daily** crypto order flow yields long-short alpha ~0.79%/day, annualized Sharpe ~3.6.

Phase 1 is a hard FAIL-FAST GO/NO-GO. The decisive question: **do derivatives order-flow features carry genuine, exploitable RETURN predictability on v3's actual data** — BCH/LDO/TRX, 8h bars, the walk-forward IS-eval window 2023-03-24..OOS_CUTOFF?

The committed EDA (`analysis/iteration_v3-094/orderflow_return_ic_eda.py`) constructed a 22-feature order-flow panel and measured return-IC against (T2) forward returns and (T3) the /059 triple-barrier label, **walk-forward-faithful** (`feedback_v3_eda_walkforward_faithful` — restricted to the runner's actual IS-eval window 2023-03-24..OOS, not the full on-disk panel).

GO criterion: order-flow return-IC must be **materially stronger** than /093's ~0.08 price-myopic ceiling — operationalized as headline cross-symbol mean best |IC| > 0.12 (= 1.5 x 0.08) AND >= 2 of 3 symbols individually clear 0.08 AND T2 corroborates.

## 2. The result — NO-GO (T5_go_nogo_summary.csv)

| Metric | Value | vs /093 ~0.08 ceiling |
|---|---|---|
| **T3 barrier-label-IC, per-symbol-best, cross-symbol MEAN** (headline) | **0.0981** | marginal — only +0.018 over ceiling |
| T3 barrier-label-IC, per-symbol-best, MAX | 0.1223 (BCH `of_oi_logdelta_9`) | one-symbol spike |
| T2 return-IC, per-symbol-best, cross-symbol MEAN (mixed-horizon) | 0.1406 | inflated by horizon-mixing — see §3 |
| max \|corr\| order-flow vs price proxies (T4) | 0.6015 | not strongly redundant, but irrelevant given §3 |

GO rule (a) FAIL: headline mean 0.0981 < 0.12 threshold.

The headline architecture-faithful number — **T3 barrier-label-IC mean = 0.0981** — sits in the **0.10 band**, only marginally above /093's 0.08 price-myopic ceiling. That alone fails the GO rule. But the *reason* it fails — §3 — makes the NO-GO unambiguous, not borderline.

## 3. Why the NO-GO is unambiguous, not a coin-flip — three structural findings

The T2 mixed-horizon headline (0.1406) superficially looks above the 0.12 threshold. It is not a GO, for three structural reasons that an honest adjudication surfaces:

### 3.1 — The signal lives at the WRONG (horizon-mismatched) forecast horizon

Per-symbol-best |IC| broken down by forward horizon:

| Forward horizon | per-symbol-best \|IC\| MEAN | architecture-relevant? |
|---|---|---|
| 3 bars (1 day) | **0.0729** | yes — *below* the 0.08 ceiling |
| 9 bars (3 days) | **0.1110** | **yes — this is the label's 9-candle-timeout horizon** |
| 21 bars (7 days) | **0.1286** | **NO — the 9-candle-timeout label cannot reach 21 bars** |

The /059 triple-barrier label has a **9-candle (4320 min) timeout**. The strongest order-flow signal sits at the **21-bar horizon** — a 7-day-forward signal the label structurally cannot exploit. At the architecturally-correct **9-bar** horizon, the return-IC mean is **0.1110**, and the barrier-label-IC (T3) is **0.0981**. Both sit at ~0.10 — the price-myopic ceiling, not a breakout. The T2 0.1406 headline was inflated by taking a per-symbol max *across* horizons, picking up the unusable 21-bar tail.

### 3.2 — The features that DO clear 0.08 are sign-INCONSISTENT across symbols

A genuine cross-sectional order-flow edge (the literature's claim) must keep a **consistent sign** across symbols. The strongest features do not:

| Feature | h=9 return-IC: BCH / LDO / TRX | sign-consistent? |
|---|---|---|
| `of_oi_logdelta_9` (BCH's headline feature) | **+0.145** / −0.014 / **−0.097** | NO — sign flips |
| `of_retail_lsr` | +0.002 / +0.088 / −0.028 | NO — sign flips |
| `of_top_pos_lsr` | −0.021 / −0.010 / −0.067 | weak, ~consistent but all sub-0.08 |

BCH's "strongest" feature `of_oi_logdelta_9` is **+0.145 on BCH but −0.097 on TRX** — the sign inverts. This is per-symbol curve-fit noise, not a transferable directional edge — the exact pattern that closed prior v3 per-symbol axes. A per-symbol LightGBM *can* fit a per-symbol sign, but a sign that flips across a 3-symbol universe with no economic reason is the textbook single-seed/per-symbol lottery the v3 memory rules (`feedback_v3_single_seed_frozen_baseline.md` family) warn is non-transferable to OOS.

### 3.3 — The literature's actual headline signal (signed taker-volume imbalance) FAILS

The Anastasopoulos et al. paper's signal is **daily signed order flow** — realized signed taker volume. The EDA's direct analogue is the `of_taker_imb` family (signed taker-volume imbalance from per-kline `taker_buy_volume`). It is the **weakest** feature group:

- `of_taker_imb` barrier-label-IC: BCH +0.015, LDO −0.036, TRX +0.015 — all sub-0.04, signs flip.
- Best taker-imbalance variant `of_taker_imb_z30`: BCH label-IC +0.042 (one symbol), LDO −0.027, TRX +0.009.

**Every signed-taker-imbalance feature sits below /093's 0.08 ceiling on every symbol.** The paper's result — a *cross-sectional, broad-universe, daily* long-short — **does not transfer** to v3's per-symbol 8h BCH/LDO/TRX construction. (This is consistent with /082's funding-rate INERT verdict and the /086 7-feed structural finding: crypto-native non-OHLCV feeds have repeatedly under-delivered on v3's per-symbol depth-3-5 LightGBM at the 8h cadence.) The only features clearing 0.08 are the slow positioning ratios at a mismatched horizon — and those are sign-inconsistent (§3.2).

## 4. Verdict and the cheap-kill accounting

**NO-GO.** The order-flow-directional axis is killed at the Phase-1 EDA. Held against the GO criterion (return-IC materially stronger than /093's ~0.08), the honest evidence is:

- Architecture-faithful return-predictability (9-bar return-IC 0.1110; barrier-label-IC 0.0981) sits at the **~0.10 price-myopic band** — marginally above 0.08, decisively below the 0.12 GO threshold.
- The only above-ceiling signal is **horizon-mismatched** (21-bar; the label times out at 9 bars) and **sign-inconsistent across symbols** — non-transferable.
- The literature's headline signal — signed taker-volume imbalance — **fails outright** (sub-0.04, sign-flipping). The Sharpe-3.6 daily cross-sectional result does not transfer to per-symbol 8h on this 3-symbol universe.

This is exactly the foreseeable-modest outcome `feedback_fail_fast.md` says resources should NOT go to — and it was killed for the cost of one committed IS-only EDA script, **no `fetch`, no runner, no backtest**. The /093 closeout's own caveat (iii) — "if the 8h-bar order-flow IC sits at the ~0.08 price-myopic ceiling, the axis is KILLED at Phase 5/5.5 with a committed EDA and no backtest" — is precisely what fired. The cheap GO/NO-GO worked as designed.

**`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The EDA is strictly IS-only — every measurement restricted to `open_time < OOS_CUTOFF_MS`. OOS was never touched.** BASELINE_V3.md UNCHANGED — canonical /059 (IS +1.0894 / OOS +0.5791, tag `v0.v3-059`).

## 5. Next-axis recommendation

The cycle-4 derivatives-microstructure line is now **closed in both roles tested**:
- /093 — derivatives microstructure as a **risk-regime OVERLAY**: BLOCKED (confounded base book) AND low-ceiling (regime gate fired 1.5% of bars; derivatives predict vol-regime not returns).
- /094 — derivatives order-flow as a **directional ALPHA signal**: NO-GO at the EDA (return-IC at the ~0.10 price-myopic ceiling; sign-inconsistent; the literature's taker-imbalance signal fails).

The honest structural lesson, consistent with /082 (funding INERT) and /086 (7-feed structural verdict): **crypto-native non-OHLCV feeds have not delivered transferable directional alpha on v3's per-symbol 8h BCH/LDO/TRX architecture**, in either the overlay or the directional-feature role. The next EXPLORATION should NOT be an 8th crypto-native feed variant.

**Recommended next axis (iter-v3/095): the recorded cycle-4 fallback — Candidate B, crypto cointegration statistical arbitrage**, OR a genuine NEW model-architecture axis (the /088-092 cross-sectional `LGBMRanker` line and the per-symbol LightGBM line are both tapped out; an axis that has NOT been tried is a non-tree learner — e.g. a shallow MLP or an attention-pooled sequence model — on the *existing* validated 14-feature price-derived stack, attacking the "depth-3-5 tree cannot compose interactions" structural limitation directly). Candidate B's caveat (altcoin cointegration is regime-fragile and turnover-sensitive) stands; it too must clear its own Phase-1 EDA GO/NO-GO (a cointegration-stability + turnover pre-screen on the IS-eval window) before any brief. The QR for iter-v3/095 must select the axis with a committed EDA-driven quantitative basis per `feedback_v3_axis_selection_quant_discipline.md`.

---

**Artifacts (committed to `iteration-v3/094`):**
- `analysis/iteration_v3-094/orderflow_return_ic_eda.py` — the GO/NO-GO EDA.
- `analysis/iteration_v3-094/T1_orderflow_return_ic_full_panel.csv` — full-IS-panel return-IC (secondary reference).
- `analysis/iteration_v3-094/T2_orderflow_return_ic_walkforward.csv` — PRIMARY: walk-forward IS-eval-window return-IC.
- `analysis/iteration_v3-094/T3_orderflow_barrier_label_ic.csv` — IC vs the /059 triple-barrier label.
- `analysis/iteration_v3-094/T4_orderflow_redundancy_vs_price.csv` — order-flow vs price-feature \|corr\|.
- `analysis/iteration_v3-094/T5_go_nogo_summary.csv` — the decisive verdict table (VERDICT = NO-GO).
- `analysis/iteration_v3-094/orderflow_return_ic_eda_output.txt` — full stdout transcript.
- `analysis/iteration_v3-094/NO_GO_NOTE.md` — this note.
- `diary-v3/iteration_v3-094.md` — the NULL-AT-EDA closeout stub.

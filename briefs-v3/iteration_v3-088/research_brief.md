# iter-v3/088 — Research Brief — RE-ARCHITECTURE: cross-sectional relative-value RANKING model (cycle-3 EXPLORATION #7)

**Iteration**: iter-v3/088
**Type**: EXPLORATION (cycle-3 slot #7 of 10) — but a **RE-ARCHITECTURE**, not an incremental axis. The most ambitious v3 iteration since iter-v3/001.
**Branch**: `iteration-v3/088`
**Date**: 2026-05-17
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **IMMUTABLE** (`src/crypto_trade/config.py`, `OOS_CUTOFF_MS = 1742774400000`).
- `training_months = 24` — **IMMUTABLE**.
- IS = every bar with `open_time < OOS_CUTOFF_MS`. OOS = every bar at/after it.
- The QR sees OOS for the FIRST time in Phase 7. Every design parameter in this brief — the universe, the label, the forward horizon, the quantile cutoffs, the position sizing, the model objective — is selected on **IS data only** or set **a-priori from research/convention**. This is scrutinised in Section 10.3.

## Section 0.5 — Iteration Type Declaration

iter-v3/088 is a **RE-ARCHITECTURE EXPLORATION**. It is cycle-3 slot #7 of 10 and runs in EXPLORATION mode (3-seed, `--n-trials 35`), but its axis is not an incremental knob/feature/universe change — it **replaces the v3 model architecture**. Per `feedback_v3_bold_research_mandate.md` (SHARPENED 2026-05-17): *"Re-architecture is fully in-bounds and encouraged ... A genuine re-architecture IS a legitimate single iteration's axis (cf. iter-v3/001)."*

This brief **supersedes the cycle-3 incremental plan** (`briefs-v3/cycle3_plan.md`). The cycle-3 plan's three Directions are now closed by evidence (Section 1.2): Direction 1 (crypto-native feature families) by the 7-feed structural verdict; Direction 2 (universe expansion) by a 4-failure track record; Direction 3-naive by the /085 EDA. iter-v3/088 pivots v3 to the **cross-sectional architecture** — the structural root-cause fix the /087 closeout's diagnosis demands.

---

## Section 1 — Hypothesis

### 1.1 — The architectural root cause (the /087 closeout diagnosis)

Three v3 cycles (~26 EXPLORATIONs) found exactly ONE edge ingredient (`regime_momentum_signed_5d`, /025). The /087 closeout's FRANK STRATEGIC ASSESSMENT diagnosed the binding constraint as **architectural, not feature-level**:

> *"a per-symbol depth-3-5 tree on ~3-6k IS rows, predicting an absolute TP/SL barrier hit, overfits IS and does not generalize — and that is true whether you feed it OHLCV features, crypto-native features, or more symbols."*

iter-v3/087 demonstrated it brutally: each of the 3 added symbols' per-symbol models scored strongly positive IS and inverted OOS — **MANA +101.6% IS net PnL → −27.2% OOS; GALA +67.2% IS → −19.0% OOS**. The per-symbol absolute-barrier model trains N starved, independent classifiers, each predicting "does THIS symbol hit +2 ATR before −1 ATR within 21 candles" — an **absolute** target that loads the symbol's own regime and is high-variance on thin data.

### 1.2 — Why the conventional axes are closed

| Direction | Status | Evidence |
|---|---|---|
| D1 — crypto-native feature families | CLOSED — 7-feed structural verdict | funding /019/023/024/082/085, microstructure /015, basis /086 — all 7 INERT-by-importance |
| D2 — universe expansion (per-symbol books) | CLOSED — 4-failure record | /021 (HBAR+AVAX), /069 (ADA), /083 (FIL), /087 (GALA+MANA+SAND) — all NEGATIVE |
| D3-naive — naive pooled model | EDA-falsified at /085 | only 7/14 features sign-agree on feature→label IC across symbols |

The incremental space is genuinely played out. Per the bold-research mandate this is **not a stopping point** — it is the cue to re-architect.

### 1.3 — The hypothesis

> **A pooled cross-sectional relative-value RANKING model — one model trained on the pooled cross-section of a WIDE universe, predicting whether each symbol will OUT/UNDER-perform the rest of the universe over a short forward horizon, traded as a cross-sectional long-short book — will produce a structurally lower-variance, lower-overfit edge than the per-symbol absolute-barrier architecture, because (a) a RELATIVE label nets out market-wide moves, removing the dominant variance component; (b) ONE pooled model trained on ~100k+ cross-sectional rows replaces N starved ~3-6k-row models; (c) the cross-sectional ranking operation is exactly what the per-symbol absolute model cannot do — and the IS evidence (Section 2) confirms a cross-sectional relative-value signal genuinely exists in this universe.**

This is the equity-quant cross-sectional factor-model playbook (AQR / Two Sigma / the Jegadeesh-Titman → Poh-Lim-Zohren learning-to-rank tradition) ported to crypto perpetual futures. The supporting research is in Section 10.2.

---

## Section 2 — IS-Only Numerical Evidence

All tables from the committed EDA `analysis/iteration_v3-088/cross_sectional_signal_eda.py` (SHA `aebd9f3`), computed on **IS rows only** (`open_time < OOS_CUTOFF_MS`). 22 liquid non-v1/v2 Binance-USDT perps, 5,547 unique 8h timestamps, the 14-feature /059 anchor stack.

### 2.1 — T1: a WIDE cross-section is available (the screening that the failed 3-symbol book never had)

`T1_universe_screen.csv` — all 22 candidates clear the screen (≥1,500 IS rows post-60-day listing burn-in AND median 8h quote-volume ≥ $2M). Depth ranges 2,561 (LDO) to 5,547 (BCH) IS bars; median 8h liquidity $9.3M (HBAR) to $92.8M (ADA). **The pooled cross-section has ≈ 100,000 IS (symbol, timestamp) rows** — vs the ≈ 3-6k rows each per-symbol model trains on. This is the breadth a cross-sectional model needs and the per-symbol architecture could never use.

### 2.2 — T2/T3: a cross-sectional relative-value signal EXISTS, and it is highly significant

`T3_horizon_rank_ic.csv` — the per-snapshot Spearman rank-IC of a 12-bar (4-day) trailing-return predictor against the forward cross-sectional return, across forward horizons:

| Fwd horizon | mean rank-IC | std | IC-IR | t-stat | frac snapshots IC>0 |
|---:|---:|---:|---:|---:|---:|
| 1 bar (0.33d) | −0.03381 | 0.317 | −0.107 | **−7.85** | 0.448 |
| 2 bars (0.67d) | −0.03728 | 0.319 | −0.117 | **−8.59** | 0.442 |
| **3 bars (1.0d)** | **−0.04097** | 0.318 | **−0.1287** | **−9.45** | 0.443 |
| 4 bars (1.33d) | −0.03599 | 0.314 | −0.115 | **−8.43** | 0.454 |
| 6 bars (2.0d) | −0.03187 | 0.312 | −0.102 | −7.50 | 0.449 |
| 9 bars (3.0d) | −0.02681 | 0.308 | −0.087 | −6.39 | 0.446 |

**The signal is real and strongly significant** — every horizon's mean rank-IC t-stat is between −6.4 and −9.5, far past the Harvey-Liu factor-zoo bar of |t| > 3.0. The sign is **NEGATIVE — a short-horizon cross-sectional REVERSAL**: the recent cross-sectional winners *underperform* the forward cross-section, the recent losers outperform. This is the well-documented crypto short-horizon reversal (Liu-Tsyvinski JoF 2022 find cross-sectional momentum is weak/insignificant at sub-weekly horizons; the reversal dominates intraday-to-daily). **A negative rank-IC is a fully tradeable cross-sectional signal — a ranking model learns the sign from the labels; the design simply trades the loser-quantile long and the winner-quantile short.**

### 2.3 — T3 forward-horizon selection: H = 3 bars (1 day)

Selected by the **strongest |IS IC-IR|** — an IS-only, sign-agnostic criterion. H=3 has |IC-IR| = 0.1287, the maximum of the grid. OOS was never consulted. (My EDA's first draft selected by raw IC-IR and wrongly picked the *weakest* horizon; the committed version selects by magnitude — see the EDA's T3 block comment.)

### 2.4 — T4: the long-short quantile spread at H=3

`T4_long_short_spread.csv` — at H=3, ranking the 22-symbol cross-section by the 12-bar trailing return and forming top/bottom quantiles:

| Quantile | winner fwd ret | loser fwd ret | reversal-book spread | reversal-book per-snapshot Sharpe |
|---|---:|---:|---:|---:|
| tercile | +0.415% | +0.176% | +0.239% (long losers / short winners) | 0.069 |
| quartile | +0.486% | +0.187% | +0.298% | 0.070 |

The unconditional past-return-sorted reversal book has a +0.24-0.30% per-1-day spread. The per-snapshot spread Sharpe (0.07) is modest — **this is the floor, the classical single-predictor cross-sectional reversal, deliberately reported un-enhanced.** T7 shows the ranking model's headroom over it.

### 2.5 — T5: breadth matters — the cross-section needs real width

`T5_universe_width_sensitivity.csv` — rank-IC at H=3 on the full universe vs liquidity-narrowed subsets:

| Universe width | mean rank-IC | IC-IR |
|---:|---:|---:|
| 3 symbols | −0.05602 | −0.0779 |
| 5 | −0.04125 | −0.0773 |
| 8 | −0.04820 | −0.1119 |
| 12 | −0.05028 | **−0.1368** |
| 22 | −0.04097 | −0.1287 |

|IC-IR| at width 12 (0.137) and 22 (0.129) is **~70% larger** than at width 3 (0.078). The signal's information ratio strengthens materially with breadth and plateaus around 12-22 symbols. **This is direct IS evidence that a wide cross-section is the *point* of the architecture** — not the failed /083/087 "add weak symbols to a per-symbol book" (where each added symbol's own per-symbol model overfit). In a cross-sectional model the universe is the denominator the ranking is computed *within*; width is signal, not risk. The /087 closeout anticipated exactly this: *"the cross-sectional model finally makes constructive use of the breadth that Direction-2-as-an-expansion-of-per-symbol-models could not."*

### 2.6 — T6: feature cross-sectional dispersion — `btc_ret_14d` must be cross-sectionally dropped

`T6_feature_xs_rank_ic.csv` — per-feature cross-sectional rank-IC at H=3, plus cross-sectional dispersion (per-snapshot std/|mean| across symbols):

| Feature | xs rank-IC | IC-IR | xs dispersion |
|---|---:|---:|---:|
| range_realized_vol_50 | −0.06069 | −0.171 | 0.253 |
| regime_momentum_signed_5d | −0.04205 | −0.129 | 4.298 |
| sym_vs_btc_ret_7d | −0.03957 | −0.126 | 8.680 |
| ema_spread_atr_20 | −0.03345 | −0.111 | 11.793 |
| vwap_dev_20 | −0.03034 | −0.101 | 5.489 |
| ret_skew_200 | −0.02830 | −0.096 | 7.070 |
| max_dd_window_50 | +0.02779 | +0.083 | 0.256 |
| ... (7 more) ... | | | |
| **btc_ret_14d** | **NaN** | **NaN** | **0.000** |

`btc_ret_14d` has **exactly zero cross-sectional dispersion** — it is identical for every symbol at a given timestamp (it is a market-wide BTC return, not a per-symbol feature), so it carries **zero cross-sectional information** and its within-snapshot rank degenerates. It MUST be **dropped from the cross-sectional feature set**. `hurst_100` is near-degenerate (dispersion 0.038) but non-zero — it stays. The 13 features with genuine cross-sectional dispersion are the cross-sectional feature set (Section 3.5).

### 2.7 — T7 (THE HEADLINE): a multi-feature ranking model has real headroom over classical cross-sectional momentum

`T7_composite_vs_momentum.csv` — the load-bearing test. An equal-weight composite of the 13 cross-sectionally-dispersed anchor features, each feature's per-snapshot cross-sectional rank **sign-aligned to its own IS rank-IC** (the sign-alignment uses the *same IS* rank-IC from T6 — no OOS), vs the single 12-bar momentum predictor:

| Predictor | mean rank-IC | IC-IR | t-stat |
|---|---:|---:|---:|
| single 12-bar momentum | −0.04158 | −0.1264 | −9.29 |
| **equal-weight 13-feature composite** | **+0.05900** | **+0.1953** | **+14.35** |

The 13-feature composite scores **|IC-IR| = 0.195 — 55% stronger than single momentum (0.126)** — and at **t = +14.3**, even more significant. (The composite IC is positive because each feature is sign-aligned to its own IS rank-IC; the magnitude is the comparison point.) **This is direct IS evidence that a multi-feature ranking model has real headroom over the classical single-predictor cross-sectional strategy** — the central empirical claim of the re-architecture, and exactly what Poh/Lim/Zohren (arXiv 2012.07149) report for equities (a learning-to-rank model trebles the Sharpe of classical cross-sectional momentum). And this is only an *equal-weight* composite — a LightGBM ranking model that learns the feature interactions and non-linearities has further headroom on top of T7.

### 2.8 — Summary of IS evidence

1. A wide (22-symbol) cross-section is available — ≈100k pooled IS rows.
2. A cross-sectional relative-value signal genuinely exists — rank-IC t = −6 to −9.5.
3. The signal is a short-horizon reversal; H = 3 bars (1 day) by strongest |IS IC-IR|.
4. The signal strengthens with breadth — |IC-IR| ~70% larger at width 12-22 than width 3.
5. A 13-feature composite beats single momentum by 55% on |IC-IR| — a ranking model has headroom.
6. `btc_ret_14d` must be dropped from the cross-sectional feature set (zero dispersion).

The IS evidence fully supports the re-architecture.

---

## Section 3 — Proposed Changes (the re-architecture — the QE Phase-6 build spec)

This is a substantial Phase-6 build. The QR owns the design; the QE builds it. Section 3.8 specifies the staging.

### 3.1 — The label: a cross-sectional relative-value rank

The new label replaces the absolute triple-barrier (`labeling.py::label_trades`). For each (symbol, timestamp t) IS row:

1. Compute the **forward H-bar return** `r_fwd(i,t) = close(i, t+H) / close(i,t) − 1` with **H = 3 bars** (Section 2.3).
2. Within each timestamp's cross-section (all symbols trading at t), compute the **cross-sectional rank** of `r_fwd` — `rank ∈ {1, ..., N_t}` ascending, then map to a **discrete relevance grade** in `{0, 1, 2}` by tercile: bottom-third → grade 0, middle → grade 1, top-third → grade 2. (Discrete graded relevance is the standard learning-to-rank label form — Poh/Lim/Zohren; LightGBM's `lambdarank` objective consumes integer relevance grades with `label_gain`.)

The label is **RELATIVE** — it encodes "did this symbol out/under-perform the rest of the universe over the next 3 bars," NOT "did it hit an absolute barrier." Market-wide moves cancel: when the whole market rallies, every symbol's `r_fwd` rises but the cross-sectional *rank* is unchanged. This is the structural variance reduction the hypothesis rests on.

**Look-ahead safety**: `r_fwd` uses `close(t+H)` — a forward value. This is the *label* (the prediction TARGET), which is correct: a label is always forward-looking. The look-ahead-critical surface is the FEATURE/training boundary — the walk-forward train window must end H bars + the embargo before the test window so no training label's forward window overlaps the test set. Section 3.6 specifies the embargo.

### 3.2 — The model: ONE pooled LightGBM ranking model

Replace the N per-symbol `LightGbmStrategy` instances with **ONE pooled model** trained on the pooled cross-section of the whole universe.

**Objective**: LightGBM's native ranking objective **`lambdarank`** (LambdaMART — `LGBMRanker`). The research basis (Section 10.2): Poh/Lim/Zohren show LambdaMART is the strongest learning-to-rank algorithm for cross-sectional strategy construction (it directly optimises a ranking metric — NDCG — rather than pointwise MSE, and pointwise regression is demonstrably sub-optimal for ranking). LightGBM supports it natively via `objective="lambdarank"` + the `group` parameter.

- **`group`** = one query per timestamp: the number of symbols in the cross-section at each timestamp. `sum(group) = n_training_rows`.
- **`label_gain`** — relevance grades {0,1,2}; default `label_gain` handles grades ≤ 31, so no customisation needed.
- The model is trained per calendar month (the existing v3 lazy monthly-retrain cadence) on the trailing 24-month window — `training_months` UNCHANGED.

**Fallback if `lambdarank` underperforms in the Phase-6 smoke test** (Section 3.8): a pooled `LGBMRegressor` on the cross-sectionally-demeaned forward return (regress-then-rank), or a pooled `LGBMClassifier` on the top/bottom-tercile binary. The brief's PRIMARY is `lambdarank`; the regression fallback is the documented contingency. The choice between them is made in Phase 6 on an **IS-only** smoke test (rank-IC of the model's OOF predictions vs the forward-return rank on IS months) — never on OOS.

### 3.3 — The universe: the 22-symbol IS-screened cross-section

`XS_UNIVERSE` (a new constant) = the 22 symbols that passed the T1 IS-only screen:

```
ADAUSDT, AVAXUSDT, FILUSDT, FTMUSDT, BCHUSDT, GALAUSDT, EOSUSDT, CRVUSDT,
AAVEUSDT, SANDUSDT, ATOMUSDT, LDOUSDT, AXSUSDT, TRXUSDT, RUNEUSDT, MANAUSDT,
ICPUSDT, ALGOUSDT, GRTUSDT, THETAUSDT, VETUSDT, HBARUSDT
```

All 22 are non-v1/v2 (none in `V3_EXCLUDED_SYMBOLS`) and non-MKR. The screen is committed and IS-only (`T1_universe_screen.csv`). **This is NOT the failed /083/087 universe expansion** — those added weak symbols to a *per-symbol book*, where each new symbol got its own overfit per-symbol model. Here the universe is the cross-section the single pooled model ranks *within*; T5 shows width is signal. A 60-day listing burn-in is applied per symbol (drop the first 180 8h-bars after listing — the crypto new-listing non-stationarity pitfall).

`V3_MODELS` (the legacy 3-symbol per-symbol tuple) is RETAINED in the runner for the legacy per-symbol path's pre-flight checks but is NOT the iter-v3/088 trading universe. The cross-sectional path trades `XS_UNIVERSE`.

### 3.4 — Position construction: dollar-neutral cross-sectional long-short

At each timestamp t (every 8h bar — the rebalance cadence; see Section 3.4.1):

1. The pooled model scores every symbol in the cross-section → a predicted ranking score.
2. **Long the bottom tercile** of the predicted ranking (the model's predicted forward-cross-sectional losers — which, given the reversal, are the recent winners) and **short the top tercile**. Tercile (top/bottom 33%) is chosen a-priori from the cross-sectional factor convention (Jegadeesh-Titman use deciles for ~500-stock universes; for a 22-symbol crypto universe a tercile gives ~7 names per leg — enough for diversification without forcing thin/illiquid names into the book; the T4 EDA confirms the tercile spread is positive and stable). The grade-0/grade-2 label terciles and the trading terciles are deliberately the same partition.
3. **Dollar-neutral**: equal gross long and gross short notional. Within each leg, **inverse-volatility weight** the symbols (weight ∝ 1/σ̂, σ̂ = a past-only realised-vol estimate) — the standard cross-sectional construction (Poh/Lim/Zohren; the unravel.finance crypto practitioner reference), which prevents the highest-vol crypto names from dominating the book. The whole book is then scaled to a target portfolio volatility via the existing v3 vol-targeting machinery.

A market-neutral long-short book is the correct construction here because (a) the signal is *relative* — it predicts cross-sectional order, not direction, so a directional book would add un-forecast market beta; (b) it structurally caps single-symbol concentration — no symbol can exceed `1/(tercile size)` of a leg — directly addressing the v3 concentration fragility that `feedback_v3_concentration_is_signal.md` and the 4-failure universe record both flag.

#### 3.4.1 — Rebalance cadence

Rebalance every **8h bar** (the v3 candle cadence) at H=3. A position opened at t targets the 3-bar-forward cross-sectional outcome; with 8h bars the natural holding period is 3 bars (1 day) and the book is refreshed each bar — i.e. overlapping 3-bar holds, ~1/3 of the book turning over per bar. This is more frequent than the Poh/Lim/Zohren monthly equity rebalance, but 8h crypto perps have low per-trade cost (0.1% fee modeled) and the EDA's strongest |IC-IR| is at the 1-day horizon. The Phase-6 backtest must model the fee on every rebalance; Section 7 flags turnover cost as a named failure mode.

### 3.5 — Features: the 14-feature stack, cross-sectionally normalized

The 14-feature `V3_FEATURE_COLUMNS_TOP_N` /059 anchor stack is the feature starting point — UNCHANGED as a column set. But a cross-sectional model must use features that are **comparable across symbols at a timestamp**. Two adjustments, both research-grounded and IS-validated:

1. **Drop `btc_ret_14d` from the cross-sectional feature set** — EDA T6: zero cross-sectional dispersion (identical for every symbol). It carries no cross-sectional information. → 13 features enter the cross-sectional model.
2. **Cross-sectionally normalize each feature** — at each timestamp, replace each feature value with its **cross-sectional rank** (or equivalently a cross-sectional z-score) across the universe. This is the standard cross-sectional-model feature treatment (Poh/Lim/Zohren; Cakici et al.): it removes per-symbol scale and level, so the model learns "is this symbol's RSI high *relative to the universe right now*," which is the cross-sectional question. The T7 composite (Section 2.7) is built on exactly this cross-sectional-rank transform and beats the raw single predictor by 55% — IS evidence the transform adds signal.

The 14-column constant `V3_FEATURE_COLUMNS_TOP_N` is NOT edited (it is reused; the runner pre-flight still asserts `len == 14`). The cross-sectional path applies the drop + normalization at training time.

### 3.6 — Walk-forward, embargo, CPCV for the pooled model

- **Walk-forward**: the existing monthly walk-forward (`walk_forward.py`) — train on the trailing 24 months, test on the next month, advance. `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` look-ahead fix — retained).
- **Embargo / purge**: the pooled cross-sectional model interleaves all 22 symbols' rows. The label's forward window is H = 3 bars. The pooled-CPCV purge gap must remove, on both sides of every test boundary, `(H + 1) × N_symbols = (3 + 1) × 22 = 88` rows so no training label's 3-bar forward window overlaps a test row. **NOTE: this is a DIFFERENT gap from the legacy `REQUIRED_GAP = 66`** (which is `(timeout_candles=21 + 1) × 3` for the per-symbol path's 21-bar triple-barrier). The cross-sectional path's label horizon is H=3, not 21 — so its gap is `(3+1) × 22 = 88`. The Phase-6 build defines a new `XS_REQUIRED_GAP = 88` constant; the legacy `REQUIRED_GAP = 66` governs the per-symbol path the new path supersedes. The QE must NOT conflate the two.
- **CPCV**: `CPCV_N_SPLITS = 10`, `CPCV_N_TEST_SPLITS = 2` → 45 paths, computed on the pooled cross-sectional candle sequence with the `XS_REQUIRED_GAP = 88` purge.

### 3.7 — Risk framework

The v3 7-gate risk stack was designed for the per-symbol directional book. The cross-sectional long-short book is structurally different — many of the gates do not transfer cleanly (a market-neutral book has little BTC-trend beta to filter; a per-symbol OOD gate is moot when the book is the whole cross-section). For iter-v3/088 the cross-sectional path runs **without the legacy 7-gate stack** and relies on three structural risk controls intrinsic to the cross-sectional construction:

1. **Market-neutral construction** — dollar-neutral long-short removes directional market risk by design.
2. **Inverse-vol weighting + portfolio vol-targeting** — caps per-symbol and book-level risk (Section 3.4).
3. **Tercile diversification** — ~7 names per leg; no symbol exceeds `1/7` of a leg. This is the concentration cap, structural rather than a post-hoc rule (cf. `feedback_v3_concentration_is_signal.md`: per-symbol PnL caps are CLOSED — the cross-sectional construction is the orthogonal mechanism: a true denominator-expansion + diversification, not proportional scaling).

Re-introducing v3 gates onto the cross-sectional book is explicitly **deferred to a future iteration** (Section 3.8 / Section 11) — adding gates in /088 would confound the architecture's measurement. This is the honest scoping call: /088 measures the re-architecture clean.

### 3.8 — Phase-6 build scope and staging

This is a substantial build. The QE Phase-6 build, in order:

**Stage A (REQUIRED — /088 must reach this):** the runnable first cross-sectional backtest.
- A1. `XS_UNIVERSE` constant (22 symbols) + `XS_REQUIRED_GAP = 88` + fetch/feature-regen for all 22 (funding + spot caches as the v3 feature builder requires; 21 of 22 parquets already exist post-EDA, only the universe constant is new).
- A2. A cross-sectional labeling function — `label_cross_sectional_rank(panel, H=3)` — producing the {0,1,2} graded relevance label (Section 3.1). New module `src/crypto_trade/strategies/ml/cross_sectional.py`.
- A3. A pooled-panel builder — align all 22 symbols on `open_time`, apply the 60-day burn-in, drop `btc_ret_14d`, cross-sectionally rank-normalize the 13 features, build the `group` array (symbols-per-timestamp).
- A4. A pooled ranking model wrapper — `CrossSectionalRankStrategy` wrapping `LGBMRanker(objective="lambdarank")`, with the monthly walk-forward retrain. Optuna over the LightGBM hyperparameters with the IS rank-IC (or NDCG@k) as the CV objective.
- A5. A cross-sectional backtest path — at each rebalance bar, score the cross-section, form the dollar-neutral tercile long-short book with inverse-vol weights, apply portfolio vol-targeting, accrue PnL net of fees. The current `run_baseline_v3.py` per-symbol `run_backtest` loop is replaced by this path for the cross-sectional run (gated behind a `--cross-sectional` flag or a new runner entry, so the legacy per-symbol path stays intact and the config-accretion check still guards it).
- A6. The IS-only model-objective smoke test (Section 3.2 fallback decision) + the standard v3 report emission (`comparison.csv`, per-symbol attribution, CPCV).

**Stage B (if Stage A reveals it is needed):** the regression-objective fallback (Section 3.2) — only if the `lambdarank` IS smoke test underperforms. This is a contingency, not a planned stage.

**Explicitly deferred (NOT in /088):** re-introducing the v3 7-gate risk stack onto the cross-sectional book; long-only top-quantile variant; crypto-native features (funding/OI) cross-sectionally normalized. These are future-iteration axes (Section 11).

/088 **must reach a runnable first cross-sectional backtest** (Stage A complete). If Phase 6 genuinely cannot land all of Stage A in one pass, the minimum runnable product is A1-A5 with `lambdarank` and A6's report; the IS smoke test (A6) and Stage B can be a documented follow-up — but A1-A5 is the floor and is achievable.

---

## Section 4 — Expected OOS Impact + evaluation + falsifier

### 4.1 — The evaluation: a cross-sectional architecture is NOT directly comparable to the per-symbol baseline

This is critical and the Critic will scrutinise it. iter-v3/088 produces a **cross-sectional long-short book**; the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322) and the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) are **per-symbol directional-book** Sharpes. **The two are NOT the same statistic** — a market-neutral long-short book and a directional per-symbol book have different return distributions, different beta, different turnover. A naive "/088 monthly Sharpe vs /084 monthly Sharpe" comparison is architecturally invalid (it would repeat, in a worse form, the /082-/083 EXPLORATION-vs-CONFIRMATION reference-mismatch error).

**The correct evaluation for iter-v3/088 has two parts:**

**(A) The standing absolute bar.** The mission bar is **top-quant-firm-grade**: the standing v3 merge floors are **IS monthly Sharpe ≥ +1.0 AND OOS monthly Sharpe ≥ +1.0**. iter-v3/088's cross-sectional book IS measured against these absolute floors — a +1.0/+1.0 monthly Sharpe is a +1.0 monthly Sharpe regardless of architecture. This is the bar /088 must clear to be a genuine success, and the EDA's IC evidence (composite t = +14.3) is consistent with a book that can reach it. Beyond +1.0 is the goal.

**(B) The architecture-internal diagnostics.** Because /088 is a re-architecture, its primary read is whether the cross-sectional architecture *behaves as designed*:
- **OOS/IS Sharpe ratio ≥ 0.5** — the researcher-overfitting check. The whole point of the relative label is lower overfit; if OOS/IS < 0.5 the architecture failed its core promise.
- **OOS rank-IC > 0** — does the pooled model's OOS prediction rank actually correlate with the realised forward cross-sectional rank? This is the cleanest architecture-validity signal and is comparable across IS/OOS (a rank-IC is dimensionless).
- **frac_positive_paths (CPCV) ≥ 0.55** and **PBO < 0.40** — the standard v3 multiple-testing gates, computed on the pooled cross-sectional path.
- **No single symbol > 30% of OOS book PnL** — the cross-sectional construction should make this structural; verifying it confirms the construction works.

### 4.2 — The TWO reference anchors (stated for completeness, with the comparability caveat)

- **ANCHOR 1 — the cycle-3 EXPLORATION-MODE-REFERENCE: /084, IS +0.8325 / OOS +0.3322** (3-seed, per-symbol). Stated per the mandatory two-anchor rule. **Comparability caveat (Section 4.1): /088 is a different architecture — this anchor is a per-symbol-book reference and a direct Sharpe delta against it is architecturally invalid. It is recorded as the *incumbent v3 EXPLORATION result* the re-architecture aims to beat in absolute terms, NOT as a like-for-like delta anchor.**
- **ANCHOR 2 — the /059 CONFIRMATION baseline: IS +1.0894 / OOS +0.5791** (10-seed, per-symbol, tag `v0.v3-059`). RESERVED for a future cross-sectional CONFIRMATION; same comparability caveat.

The operative iter-v3/088 evaluation is Section 4.1's absolute bar (A) + architecture diagnostics (B), NOT a delta against either per-symbol anchor.

### 4.3 — Predicted OOS impact

The EDA establishes a real, highly-significant IS cross-sectional signal (composite t = +14.3) and the architecture is purpose-built for OOS robustness (relative label, pooled training, ~30× more rows). Honest prediction: the cross-sectional book reaches a **positive OOS monthly Sharpe with OOS/IS ≥ 0.5 and OOS rank-IC > 0** with good probability; clearing the full +1.0/+1.0 absolute floors on the first re-architecture pass is **plausible but not the expected modal outcome** — a first cross-sectional build typically needs one tuning iteration on the construction (quantile cutoff, vol-target, rebalance cadence) which is a *future* iteration's IS-only work. What /088 must deliver is a **runnable cross-sectional architecture with a positive, generalising OOS signal** — the structural foundation cycle 4+ builds on.

### 4.4 — The LOCKED falsifier band (pre-registered)

Falsifiers are gates, not predictions (`feedback_v3_per_symbol_target_axis_falsifier.md`). Pre-registered, evaluated in Phase 7:

- **F1 — OOS rank-IC ≤ 0**: the pooled model's OOS prediction rank does NOT correlate with the realised forward cross-sectional rank → the cross-sectional signal did not transfer OOS → the re-architecture FAILED its core claim. This is the primary falsifier.
- **F2 — OOS/IS monthly Sharpe ratio < 0.5**: the relative label did NOT deliver the promised overfit reduction → architecture under-delivers.
- **F3 — OOS monthly Sharpe < 0**: the cross-sectional book loses money OOS.
- **F4 — frac_positive_paths < 0.55 OR PBO ≥ 0.40**: the pooled-CPCV multiple-testing gates fail.
- **F5 — a single symbol > 50% of OOS book PnL**: the dollar-neutral tercile construction failed to diversify (a structural-construction failure, distinct from a signal failure).

If F1 fires, the re-architecture is falsified as an edge source for the current cycle (but the architecture and infrastructure are retained — see Section 8). If F2-F5 fire without F1, the signal transferred but the construction needs work (a future-iteration tuning axis).

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. iter-v3/088's risk controls are **structural — intrinsic to the cross-sectional construction** — rather than the per-symbol 7-gate stack:

| Risk | Mitigation | IS-calibrated / a-priori |
|---|---|---|
| Directional market drawdown | Dollar-neutral long-short construction (Section 3.4) — removes market beta by design | a-priori (construction) |
| Single-symbol concentration | Tercile long-short — ~7 names per leg, no symbol > 1/7 of a leg | a-priori (construction); cf. `feedback_v3_concentration_is_signal.md` |
| High-vol-symbol domination | Inverse-vol weighting within each leg + portfolio vol-targeting | a-priori (standard cross-sectional construction) |
| Turnover / fee drag | 0.1% fee modeled on every 8h rebalance; tercile turnover ~1/3-per-bar accepted | IS-modeled in the backtest |
| Listing non-stationarity | 60-day (180-bar) listing burn-in per symbol | a-priori (crypto pitfall convention) |
| Thin-cross-section bars | Require ≥ 6 symbols in the cross-section to form a book at a timestamp | a-priori |
| Label look-ahead | `XS_REQUIRED_GAP = 88` pooled-CPCV purge; walk-forward `train_end = test_start − embargo` | a-priori (formula) |

Simulated historical effect: the EDA's 60-day burn-in and ≥6-symbol minimum are already applied in the IS EDA (Section 2) — the cross-sectional signal (t = −9.5) is measured *with* these controls active, so they do not destroy the signal. The dollar-neutral + inverse-vol + vol-target construction is the standard cross-sectional risk apparatus (Poh/Lim/Zohren) and is not novel.

## Section 6 — Risk Management Design

The cross-sectional book is risk-managed by construction (Section 5). The legacy v3 7-gate stack (vol scaling, ADX, Hurst, z-score OOD, low-vol filter, hit-rate, BTC-trend) is **deferred** — re-introducing it onto a market-neutral cross-sectional book in the same iteration would confound the architecture measurement. A future iteration evaluates which gates transfer (the BTC-trend filter is largely moot for a market-neutral book; a cross-sectional OOD gate on the *book* is a candidate). The /088 cross-sectional path runs with the three structural controls of Section 3.7 only — this is the honest, clean-measurement scoping choice.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

A re-architecture has a wider outcome distribution than an incremental axis. The honest pre-registered distribution:

- **≈35% — the architecture works, positive generalising OOS, OOS/IS ≥ 0.5, OOS rank-IC > 0, but OOS monthly Sharpe lands in [0, +1.0)** (below the absolute floor). The modal outcome: the cross-sectional signal transfers OOS — the EDA's t = +14.3 IS composite says it should — but the *first* cross-sectional build's position construction (tercile cutoff, vol-target, 8h rebalance) is un-tuned, so the realised book Sharpe is positive but sub-floor. This is a SUCCESS for a re-architecture (a runnable, generalising new architecture) and sets up a cycle-4 tuning sequence.
- **≈20% — full success: OOS monthly Sharpe ≥ +1.0 with OOS/IS ≥ 0.5.** The re-architecture clears the absolute bar on the first pass. Possible — the IS signal is strong — but not the modal expectation for a first build.
- **≈25% — F2 fires (OOS/IS < 0.5) without F1**: the cross-sectional signal transfers (OOS rank-IC > 0) but the long-short book still overfits IS — most likely via the position construction (the tercile/vol-target tuned implicitly to IS) or turnover-cost drag eating the OOS spread. The signal is real; the construction needs work.
- **≈15% — F1 fires (OOS rank-IC ≤ 0)**: the cross-sectional signal does NOT transfer OOS. The strongest counter-evidence to the hypothesis. The crypto cross-sectional reversal is a documented, robust effect (Liu-Tsyvinski) so a hard OOS rank-IC reversal is the tail — but the IS reversal could be a 24-month-regime artifact. If F1 fires the architecture is falsified for this cycle.
- **≈5% — implementation/turnover catastrophe**: the 8h rebalance turnover cost overwhelms the +0.24-0.30%/day spread, OOS monthly Sharpe < 0 (F3). The fee is modeled, so this is foreseeable, not a surprise — flagged here so it is not rationalised post-hoc.

The single most-likely outcome is the **≈35% "architecture works, OOS positive and generalising, sub-floor Sharpe"** — and that is named here, honestly, as a SUCCESS for a re-architecture iteration: a runnable cross-sectional architecture with a generalising OOS signal is the structural foundation the situation demands.

---

## Section 8 — Pre-Registered Classification Taxonomy (LOCKED — adapted for a RE-ARCHITECTURE)

The standard EXPLORATION taxonomy (PROMISING/NEGATIVE/INERT/SUSPICIOUS/NULL) was designed for single-axis incremental iterations and does not map cleanly to a re-architecture. The /088 LOCKED taxonomy, adapted, evaluated in disjunctive precedence (first match canonical):

### 8.1 — SUSPICIOUS (evaluated FIRST)

Fires on EITHER:
- **(a)** OOS monthly Sharpe / IS monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature), OR
- **(b)** OOS rank-IC ≥ 2× the IS rank-IC in magnitude (an implausible OOS-better-than-IS signal divergence — the cross-sectional analogue of the per-symbol SUSPICIOUS pattern).

### 8.2 — ARCHITECTURE-FALSIFIED (the re-architecture NEGATIVE)

Fires if **F1 fires — OOS rank-IC ≤ 0** (and NOT SUSPICIOUS). The cross-sectional signal did not transfer OOS; the re-architecture is falsified as an edge source for this cycle. NO-MERGE. The architecture, the `cross_sectional.py` module, the `XS_UNIVERSE`, the pooled-ranking infrastructure are RETAINED as reusable infrastructure (a falsified *edge* with sound *infrastructure* — the established v3 pattern: cf. the basis feed retained after /086).

### 8.3 — ARCHITECTURE-VALIDATED-PROMISING (the re-architecture success)

Fires if (NOT SUSPICIOUS, NOT ARCHITECTURE-FALSIFIED) AND **OOS rank-IC > 0 AND OOS/IS monthly Sharpe ratio ≥ 0.5 AND frac_positive_paths ≥ 0.55 AND OOS monthly Sharpe > 0**. The cross-sectional architecture works and generalises. Sub-case **8.3-FULL**: additionally OOS monthly Sharpe ≥ +1.0 AND IS monthly Sharpe ≥ +1.0 — the re-architecture clears the absolute merge floors and is a CONFIRMATION-bundle candidate. Sub-case **8.3-FOUNDATION**: OOS monthly Sharpe ∈ (0, +1.0) — the architecture is validated and generalising but sub-floor; it advances as the v3 architectural baseline for cycle 4's tuning sequence, not as a /092 merge ingredient.

### 8.4 — ARCHITECTURE-PARTIAL (signal transfers, construction underperforms)

Fires if (NOT SUSPICIOUS, NOT ARCHITECTURE-FALSIFIED, NOT 8.3) AND **OOS rank-IC > 0** but a non-F1 falsifier (F2/F3/F4/F5) fires. The cross-sectional signal transferred but the long-short construction needs work (turnover cost, quantile cutoff, vol-target). The architecture is retained; the next iteration's axis is the construction. NO-MERGE.

### 8.5 — NULL / INCONCLUSIVE

The Phase-6 build did not reach a runnable cross-sectional backtest (only if Stage A genuinely could not be completed — Section 3.8 commits to A1-A5 as the floor). Recorded for completeness; the build scope is committed to avoid this.

**An EXPLORATION cannot update BASELINE_V3.md regardless of classification.** BASELINE_V3.md stays `v0.v3-059`. A re-architecture that lands 8.3-FOUNDATION or 8.3-FULL would, per the cycle plan, motivate a dedicated cross-sectional CONFIRMATION as the next major step.

---

## Section 9 — Library Stack Declaration

- **LightGBM** — `LGBMRanker` with `objective="lambdarank"` (the new ranking model); `LGBMRegressor`/`LGBMClassifier` as the documented fallback. LightGBM is already a v3 dependency.
- **Optuna** — hyperparameter search (existing v3 dependency), CV objective = IS rank-IC / NDCG@k.
- **pandas / numpy** — pooled-panel construction, cross-sectional ranking, label construction.
- No new third-party dependency. The ranking objective is native LightGBM.

## Section 10 — QR Audit Trail

### 10.1 — The orchestrator's lead steer and the QR call

The orchestrator's dispatch LOCKED the **direction** — a cross-sectional relative-value ranking model — as the iter-v3/088 re-architecture axis, per `feedback_v3_bold_research_mandate.md` (SHARPENED). Per `feedback_v3_axis_selection_quant_discipline.md`, the QR owns every *design* decision within that direction, EDA-grounded. The QR's calls in this brief, all IS/research-grounded: the 22-symbol universe (T1 IS screen); H=3 forward horizon (T3 strongest |IS IC-IR|); the `lambdarank` ranking objective (Poh/Lim/Zohren research); the tercile long-short dollar-neutral construction (cross-sectional factor convention + T4); the cross-sectional rank-normalization of 13 features with `btc_ret_14d` dropped (T6 + T7). The cross-sectional-ranking direction was *also* independently the QR's own top recommendation in the /087 closeout's strategic assessment (diary-v3/iteration_v3-087.md Section 8.3(c) PRIMARY) — the orchestrator steer and the QR's prior diagnosis converge.

### 10.2 — Literature-research path (genuine WebSearch/WebFetch, Phases 1-4)

1. **Poh, Lim, Zohren & Roberts (2021), "Building Cross-Sectional Systematic Strategies By Learning to Rank"** — arXiv 2012.07149 / *J. Financial Data Science* 3(2):70, Spring 2021. The canonical methodology paper. Fetched and read in full (the PDF text was extracted directly). Key findings adopted: (a) cross-sectional strategies have a 4-component framework — score calculation, score ranking, security selection (top/bottom decile), portfolio construction (vol-scaled); (b) **regress-then-rank with a pointwise MSE loss is sub-optimal for ranking** — the loss does not consider the *ordering* of returns; (c) **LambdaMART (LightGBM `lambdarank`)** is the strongest learning-to-rank algorithm — it optimises NDCG, a ranking metric, directly; (d) the LTR framework gives **~threefold Sharpe improvement over classical cross-sectional momentum** on US equities; (e) the framework is modular — the momentum predictors can be swapped for any feature set. This paper is the direct template for the iter-v3/088 model (Section 3.2) and label (Section 3.1).
2. **Liu, Tsyvinski & Wu (2022), "Common Risk Factors in Cryptocurrency"** — *Journal of Finance* 77(2):1133-1177 / NBER w25882. Establishes that **three factors — market, size, momentum — capture the cross-section of crypto returns**, and that crypto cross-sectional momentum is regime/horizon-dependent (strong among large coins at weekly horizons, weak/insignificant at sub-weekly). This grounds the EDA's central finding that the *short-horizon* (1-3 bar) cross-sectional signal is a **reversal**, not momentum — Section 2.2.
3. **Cakici, Shahzad, Będowska-Sójka & Zaremba (2024), "Machine Learning and the Cross-Section of Cryptocurrency Returns"** — *International Review of Financial Analysis* 94 / SSRN 4295427. 40 crypto features × 8 ML models. Key findings adopted: ML cross-sectional models generate **substantial economic gains in crypto** (unlike in equities); return predictability comes from **a handful of simple characteristics** (past alpha, illiquidity, momentum) — so a modest 13-feature cross-sectional stack is appropriate, not a 100+ feature set; abnormal crypto returns come from the **long leg** and **persist over time** — relevant to a future long-only variant. (Prior v3 QRs cited Cakici et al. at /083 — the cross-sectional-returns reference the orchestrator dispatch named.)
4. **Practitioner cross-sectional crypto reference** (unravel.finance, "Cross-Sectional Alpha Factors in Crypto") — a practitioner cross-sectional crypto book: top-50-by-market-cap universe, daily rebalance, **equal-weight long top-20% / short bottom-20%, inverse-volatility weighting at the portfolio level**, ~2.0 Sharpe with overfitting controlled by factor diversification + a ~6-factor ensemble cap + established factors. This grounds the iter-v3/088 position construction (Section 3.4: dollar-neutral long-short, inverse-vol weighting) and the survivorship-bias awareness (Section 3.3: a rolling, IS-only universe screen).
5. **LightGBM ranking documentation** — `LGBMRanker`, `objective="lambdarank"`, the `group` parameter (`sum(group) = n_rows`, one query per timestamp), `label_gain` (default handles integer relevance grades ≤ 31). Confirms the ranking objective is native and the {0,1,2} graded-relevance label (Section 3.1) is directly consumable.

The research path: paper 1 supplied the model + label methodology; papers 2-3 supplied the crypto cross-sectional-returns evidence (and the reversal-vs-momentum sign); reference 4 supplied the position construction; reference 5 confirmed the implementation is native LightGBM.

### 10.3 — No-cheating audit

Per `feedback_no_cheating.md` — every design parameter selected on IS data only or a-priori:

- **OOS_CUTOFF_DATE / training_months** — IMMUTABLE, untouched.
- **Universe (22 symbols)** — `T1_universe_screen.csv`: every screened figure (IS rows, IS-window median quote-volume) computed on `open_time < OOS_CUTOFF_MS`. The screen thresholds (≥1,500 rows, ≥$2M liquidity) are a-priori liquidity floors.
- **Forward horizon H=3** — `T3_horizon_rank_ic.csv`: rank-IC computed on IS snapshots only; H selected by strongest |IS IC-IR|. OOS never read. (My EDA's first draft selected by raw IC-IR — a methodology bug, not a cheat; the committed version selects by magnitude. Both versions read only IS data.)
- **Quantile cutoff (tercile)** — a-priori from the cross-sectional factor convention; T4 confirms the tercile spread is positive on IS data — not OOS-tuned.
- **The 13-feature cross-sectional set + `btc_ret_14d` drop** — `T6`: cross-sectional dispersion computed on IS snapshots; `btc_ret_14d` dropped for zero IS dispersion. The T7 composite sign-alignment uses the *same IS* rank-IC. No OOS column is read anywhere in the EDA.
- **Model objective (`lambdarank`)** — set a-priori from the Poh/Lim/Zohren research; the Phase-6 PRIMARY-vs-fallback decision is made on an **IS-only** smoke test (Section 3.2).
- **Position construction (dollar-neutral, inverse-vol, vol-target)** — a-priori from the cross-sectional construction convention.
- The IS window is **never trimmed** — the EDA uses the full IS history from each symbol's listing (after the a-priori 60-day burn-in).
- The QR sees OOS for the first time in Phase 7. Every Section 4 OOS gate is a *pre-registered evaluation gate*, not a tuned parameter.

## Section 11 — Reproducibility Stamp

- **EDA SHA**: `aebd9f3` — `analysis/iteration_v3-088/cross_sectional_signal_eda.py` + T1/T3/T4/T5/T6/T7 CSVs.
- **Setup SHA**: `6de7c44` — ITERATION_LABEL "v3-088"; V3_MODELS 6→3 baseline-restore; REQUIRED_GAP 132→66; config-accretion check + stale 6-symbol comments updated to /059-canonical.
- **Setup test-update SHA**: `22f465d` — 4 universe-pinning tests reverted to the 3-symbol /059 state (test_fracdiff_d05_universal, test_hurst_drift_50_200_universal, test_features_for_symbol, test_cpcv_embargo_assert).
- **Brief SHA**: `e76dbe3` (research brief); this Section-11 backfill in the immediately-following commit.
- **Reports**: `reports-v3/iteration_v3-088/` (Phase 6).
- **Run mode**: EXPLORATION — 3-seed, `--n-trials 35` (the cross-sectional-path runner spec; the QE Phase-6 build defines the cross-sectional run invocation).
- **Future-iteration axes** (deferred from /088, recorded for the cycle plan): (i) re-introduce / re-design the v3 risk gates for the cross-sectional book; (ii) tune the position construction (quantile cutoff, vol-target, rebalance cadence) — IS-only; (iii) cross-sectionally-normalized crypto-native features (funding/OI) — the 7-feed verdict was for the per-symbol architecture; a pooled cross-sectional model with ~100k rows is a genuinely different test; (iv) a long-only top-quantile variant (Cakici et al.: crypto abnormal returns come from the long leg); (v) a dedicated cross-sectional CONFIRMATION if /088 lands 8.3-FOUNDATION or 8.3-FULL.

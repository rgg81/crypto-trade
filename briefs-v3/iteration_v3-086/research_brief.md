# iter-v3/086 — Research Brief — NEW crypto-native data feed: perp-spot BASIS family (cycle-3 EXPLORATION #5)

**Iteration**: iter-v3/086
**Cycle**: 3, EXPLORATION slot #5 of 10
**Branch**: `iteration-v3/086`
**Date**: 2026-05-16
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are IMMUTABLE and untouched. All Phase 1-5 research — literature survey, data acquisition, EDA, feature design — used **IS data only** (`open_time < 2025-03-24`). The QR sees OOS for the first time in Phase 7. The newly-acquired spot klines extend past the cutoff (the walk-forward backtest needs the full series), but the EDA in Section 2 loads only IS rows. No design parameter is selected on any OOS metric (Section 10 audits this explicitly).

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION** (cycle-3 EXPLORATION #5 of 10). **Single-axis**: introduce a NEW crypto-native data feed — the **perp-spot basis** — and append a **3-feature basis family** to `V3_FEATURE_COLUMNS_TOP_N` (14 → 17). EXPLORATION-mode 3-seed, `run_baseline_v3.py --exploration --n-trials 35`. Per `feedback_v3_dsr_mode_artifact.md`, Check-3 DSR/PSR are informational for an EXPLORATION; only per-cell PBO and CPCV `frac_positive_paths` are evaluated against thresholds.

Two MANDATORY non-axis baseline-restore / cleanup actions accompany the setup (they are *not* a second axis — they restore the /059 anchor and fix a stale docstring, per Critic /085 Recs #1/#3): (a) revert `V3_FEATURE_COLUMNS_TOP_N` to the 14-feature /059 anchor (drop the INERT/SUSPICIOUS `funding_regime_momentum_5d`) and add it to the runner pre-flight ABSENT-assertion list; (b) fix the stale `validation_v3.py:594` docstring (`88 4-symbol` → the live `66` 3-symbol).

## Section 1 — Hypothesis

**The perp-spot basis encodes leverage/sentiment crowding that the v3 14-feature OHLCV stack cannot see, and a 3-feature basis family gives the LightGBM a crypto-native signal it currently lacks.**

The basis — `(perp_close − spot_close) / spot_close` — is the canonical sentiment primitive of a perpetual market. A persistently positive basis signals leveraged-long crowding; a negative basis signals leveraged-short positioning. Unlike funding (which settles on an 8h lag and is clamped at Binance's ±floor), the basis reprices **continuously and is unclamped** — it carries a faster, less-saturated crowding signal. The crypto-native literature (AEA 2026 "Perpetual Futures and Basis Risk"; the futures-basis-arbitrage / speculator-demand literature) documents that the basis predicts **mean reversion at extremes**: a crowded-positive basis is a fade setup.

This is a **NEW data feed**, not a feature construction on existing parquets — every prior v3 feature is derived from OHLCV or the funding rate. The basis requires acquiring **spot 8h klines** (a feed v3 has never fetched) and computing the perp-vs-spot premium.

**Why this is NOT the closed funding axis.** The v3 funding axis is a 5-data-point CLOSED verdict (/019/023/024/082/085). The basis is a *different feed*: EDA Section 2.6 measures `corr(basis_z, funding_z)` at only **0.22-0.28** across the 3 symbols — the basis is genuinely distinct from funding (low correlation; economically expected, since funding is the lagged, clamped settlement and the basis is the continuous, unclamped premium). The /085 Critic Rec #4 explicitly named a NEW crypto-native data feed as the highest-value untried axis; this iteration executes that directive.

## Section 2 — IS-Only Numerical Evidence

All tables from the committed EDA `analysis/iteration_v3-086/basis_feed_eda.py` + `basis_directional_probe.py` (EDA SHA backfilled in Section 10), IS-only, current data.

### 2.0 — Data-feed viability: history depth (the binding constraint, VERIFIED)

A new feed is viable ONLY if it covers each symbol's full perp IS window. The v3 IS windows: **BCH perp 2020-01-01** (5727 IS rows), **TRX perp 2020-01-15** (5669 IS rows), **LDO perp 2022-09-22** (2741 IS rows).

| Candidate feed | Source | History depth (VERIFIED) | Viable? |
|---|---|---|---|
| Open Interest | `/futures/data/openInterestHist` API | last ~30 days only (oldest row 2026-04-17; explicit 2021 `startTime` → "parameter invalid") | **NO** |
| Open Interest | `data.binance.vision .../daily/metrics/` archives | BCH/TRX start **~2021-12** (2021-09 → HTTP 404, 2021-12 → HTTP 200) | **NO** — misses ~2 yr of BCH/TRX IS (~62% of rows NaN) |
| Long/short ratio | `/futures/data/globalLongShortAccountRatio` API | last ~30 days only (oldest 2026-04-17) | **NO** |
| **Perp-spot basis** | perp 8h klines (v3 has them) + **spot 8h klines** | spot on `data.binance.vision`: BCH from **2019-11-28**, TRX from **2018-06-11**, LDO from **2022-05-09** — every symbol's spot covers its perp IS window | **YES** |

The basis is the **only candidate feed with adequate IS-window depth.** OI was deferred at /082 for lack of a pipeline; this EDA establishes the *deeper* reason OI cannot be used at all in v3 — its history is structurally too short. The pivot to basis is forced by the data, exactly as the dispatch anticipated.

### 2.1 — T0: coverage / non-degeneracy (the basis feed is clean)

| Symbol | perp IS rows | spot-merge coverage | basis_raw mean (bps) | basis_raw std (bps) | basis_z30 coverage | basis_z30 unique values |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5727 | 1.0000 | −1.97 | 12.89 | 0.9948 | 5280 |
| LDOUSDT | 2741 | 1.0000 | −1.52 | 8.52 | 0.9891 | 2616 |
| TRXUSDT | 5669 | 1.0000 | −1.74 | 9.29 | 0.9947 | 5226 |

Spot-merge coverage is **100%** for all 3 symbols (every IS perp candle matched a spot candle on `open_time`). Basis features cover 98.9-99.9% of IS (the small gap is the leading 30-bar z-score warm-up). The basis is non-degenerate — 5280/2616/5226 distinct z-score values. The feed is real, clean, and computable.

### 2.2 — T1: basis feature → triple-barrier label — Spearman IC (IS-only)

| Symbol | basis_zscore_30 | basis_momentum_3 | basis_extreme_flag |
|---|---:|---:|---:|
| BCHUSDT | +0.0073 | −0.0054 | **+0.0483** |
| LDOUSDT | **−0.0513** | −0.0390 | −0.0135 |
| TRXUSDT | −0.0196 | +0.0128 | −0.0106 |

**Honest reading: the direct basis features carry WEAK univariate IC** — all |IC| ≤ 0.051. The strongest are `basis_extreme_flag` on BCH (+0.048) and `basis_zscore_30` on LDO (−0.051). This is in the same weak range the closed funding features showed. No basis feature has standalone univariate punch.

### 2.3 — T2: orthogonality vs the 14-feature anchor stack (max |Pearson IC|)

| Symbol | basis_zscore_30 (argmax) | basis_momentum_3 (argmax) | basis_extreme_flag (argmax) |
|---|---:|---:|---:|
| BCHUSDT | 0.2497 (vwap_dev_20) | 0.0403 (vwap_dev_20) | 0.3538 (ema_spread_atr_20) |
| LDOUSDT | 0.2086 (vwap_dev_20) | 0.0798 (vwap_dev_20) | 0.4566 (btc_ret_14d) |
| TRXUSDT | 0.3150 (vwap_dev_20) | 0.0915 (vwap_dev_20) | 0.3394 (btc_ret_14d) |

All max |IC| are below the 0.70 hard gate AND the 0.50 strict target — Check 4 passes. But the orthogonality is **uneven**: `basis_momentum_3` is genuinely orthogonal (max |IC| ≤ 0.092 everywhere); `basis_zscore_30` is moderately correlated with `vwap_dev_20` (the perp price-vs-VWAP feature — economically plausible, both touch a price-deviation idea); `basis_extreme_flag` reaches |IC| 0.46 with `btc_ret_14d` on LDO — the highest correlation in the family. The basis family is orthogonal *enough* to pass the gate, but `basis_extreme_flag` is the least independent member.

### 2.4 — T3: incremental-information test — 14 vs 17 features (chronological IS 70/30 split)

| Symbol | n IS | test n | base rate | acc (14) | acc (14 + basis) | Δ |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5627 | 1689 | 0.6442 | 0.6418 | 0.6353 | **−0.0065** |
| LDOUSDT | 2641 | 793 | 0.6570 | 0.5902 | 0.5750 | **−0.0151** |
| TRXUSDT | 5569 | 1671 | 0.5757 | 0.5380 | 0.5332 | **−0.0048** |

**Honest reading: the incremental-information delta is NEGATIVE on all 3 symbols.** Adding the 3 basis features to the 14-anchor stack *reduces* held-out accuracy in this quick-probe. This is the iter-v3/070 colsample-theft signature — features that consume `colsample_bytree` picks without adding signal. This is the single most cautionary EDA result and it is reported plainly: the off-the-shelf direct basis family does not help the model in a fixed-hyperparameter probe.

### 2.5 — PART 2: directional / interaction probes (where the basis DOES carry structure)

**P1 — basis_z → forward raw return Spearman IC.** The crowding-reversal hypothesis (high basis → negative forward return) is **directionally confirmed but weak**: every IC is negative (BCH −0.006/−0.005 at 1/3-bar, LDO −0.031/−0.030, TRX −0.018/−0.025). Only LDO shows even modest reversal magnitude.

**P2 — triple-barrier long-label rate by basis-z extreme bucket — the one genuine signal:**

| Symbol | all IS | basis_z > +1.5 (crowded long) | basis_z < −1.5 (crowded short) | crowded-long − crowded-short spread |
|---|---:|---:|---:|---:|
| BCHUSDT | 0.3544 | 0.3510 (n=416) | 0.3311 (n=453) | +0.020 (negligible) |
| **LDOUSDT** | 0.3124 | **0.2460 (n=187)** | **0.3892 (n=203)** | **−0.143 (genuine)** |
| TRXUSDT | 0.4130 | 0.4125 (n=417) | 0.4113 (n=423) | +0.001 (none) |

On **LDO** the basis-z extreme buckets stratify the label cleanly and in the predicted direction: a crowded-long basis (z > +1.5) drops the long-label rate to 0.246; a crowded-short basis lifts it to 0.389 — a **14.3pp spread**. BCH (~2pp) and TRX (~0pp) show no stratification. The basis carries genuine conditional signal **on LDO only**, in a small-n bucket (187/203 IS trades).

**P3 — basis_regime_momentum** (`regime_momentum_signed_5d × −sign(basis_z)`, the Category-2 fade construction): near-zero IC on all 3 symbols (BCH −0.027, LDO −0.006, TRX +0.025) — the composed fade construction does NOT recover structure. (This is why the axis is the *direct 3-feature family*, not a composed feature — the composed construction is EDA-falsified here, distinguishing /086 from /085.)

### 2.6 — Basis is genuinely distinct from the closed funding axis

`corr(basis_z, funding_z)` over IS: BCH **0.2652**, LDO **0.2216**, TRX **0.2847**. The basis is weakly correlated with funding — it is NOT a funding repackaging. Economically: funding is the lagged, ±-clamped 8h settlement; the basis is the continuous, unclamped premium. The basis is a legitimately distinct crypto-native feed; the closed-funding-axis verdict does not transfer to it.

### 2.7 — The structural context (the v3 fragility this axis sits inside)

BCH carries ~95% of v3 IS PnL (BASELINE_V3.md). LDO is the directionally-weak symbol (OOS WR 25.0%). EDA P2's finding — the basis carries signal **on LDO** — is notable: if the basis helps the LightGBM at all, it most plausibly helps the symbol that currently has the least signal. But this is a hypothesis for the backtest, not a claim; the IS evidence is weak (Section 7 weights it honestly).

## Section 3 — Proposed Changes (and the data-acquisition plan)

### 3.1 The single axis — a NEW perp-spot basis FEATURE FAMILY

`V3_FEATURE_COLUMNS_TOP_N` grows **14 → 17** by appending 3 basis features after the 14 anchors:

| Feature | Construction (all PAST-ONLY — on `basis.shift(1)`) | What it encodes |
|---|---|---|
| `basis_zscore_30` | 30-bar past-only z-score of basis; clipped ±10 | crowding LEVEL — how stretched the perp premium is vs its 10-day baseline |
| `basis_momentum_3` | `basis[t−1] − basis[t−4]` (3-bar change of the lagged basis) | crowding MOMENTUM — premium building / unwinding |
| `basis_extreme_flag` | `sign(basis).shift(1).rolling(9).mean()` | crowding DIRECTION + PERSISTENCE — a mean-zero z-score cannot carry this |

Window choices (30 / 3 / 9) are fixed **a-priori**, NOT swept: 30 = the funding-settlement-cycle convention (`funding_v3.py FUNDING_ZSCORE_WINDOW`, 10 days @ 8h); 3 and 9 = the established /082 funding-family construction (`funding_momentum_3` / `funding_sign_persist_9`). Re-using the proven /082 windows means /086's only genuine novelty is the *feed*, not a parameter sweep.

Nothing else changes — no labeling change, no symbol change, no risk-gate change, no model-architecture change, no seed change. `V3_MODELS` stays BCH/LDO/TRX; `REQUIRED_GAP` stays 66; `PER_CELL_GAP` stays 22; ATR multipliers stay `(2.0, 1.0)`; the 7-gate risk stack is /059-canonical.

### 3.2 The data-acquisition plan — the new feed (this is the heart of /086)

**The feed**: spot 8h klines for BCHUSDT / LDOUSDT / TRXUSDT.

**The source**: `data.binance.vision` monthly spot-kline ZIP archives — `https://data.binance.vision/data/spot/monthly/klines/<SYM>/8h/<SYM>-8h-<YYYY-MM>.zip`. This is the project-canonical bulk source (the same mechanism `src/crypto_trade/bulk.py` uses for perp klines). The `/api/v3/klines` REST API is the fallback for the current (not-yet-archived) month.

**History coverage VERIFIED** (Section 2.0): BCH spot archives from 2019-11-28, TRX from 2018-06-11, LDO from 2022-05-09 — each spot series starts **before** that symbol's perp IS window. The QR fetch (`analysis/iteration_v3-086/fetch_spot_klines.py`) wrote `data/spot/<SYM>/8h.csv`: BCH 7037 rows (2019-11-28→2026-04-30), LDO 4358 rows (2022-05-09→2026-04-30), TRX 8642 rows (2018-06-11→2026-04-30). Spot-merge coverage on the IS perp rows is 100% (Section 2.1).

**The microsecond/millisecond normalisation (LOAD-BEARING)**: Binance spot kline archives switched `open_time`/`close_time` from millisecond (13-digit) to **microsecond (16-digit)** epochs at **2025-01**. The v3 perp CSVs are millisecond. The fetcher normalises every spot timestamp to milliseconds (`val // 1000` when `val ≥ 1e15`) — a microsecond `open_time` would never join a millisecond perp `open_time`. The QE MUST carry this normalisation in the production fetcher.

**Past-only / reporting-lag handling (LOAD-BEARING)**: `perp_close[t]` and `spot_close[t]` both settle at candle `close_time(t)` — so `basis(t)` is knowable only at bar t **CLOSE**, NOT at bar t open. Every basis feature is computed on **`basis.shift(1)`** — bar t's decision uses `basis[t−1]` (the previous fully-closed candle) and earlier ONLY. This is **STRICTER** than the funding convention: funding broadcasts ~5 min before settlement so `funding_rate[t]` is knowable at bar t open, but the basis needs both closes, so it lags one full candle. The EDA's spike-perturbation audit (Section 2, T4) confirmed: perturbing `perp_close` at bar K leaves every basis feature at bars `< K` bit-identical for all 3 symbols.

### 3.3 The QE Phase-6 fetcher build (productionise the QR prototype)

The QR fetch script `analysis/iteration_v3-086/fetch_spot_klines.py` is the PROTOTYPE. The QE productionises it in Phase 6 as a new **`crypto-trade fetch-spot`** CLI subcommand (sibling to the existing `fetch-funding`, `bulk`):

1. **`fetch-spot` subcommand** in `main.py` — `--symbols`, `--interval` (default 8h), `--output-dir` (default `data/spot/`). Iterates `data.binance.vision` monthly spot-kline archives; incremental (skips already-cached months by `open_time`); the current month fills via `/api/v3/klines` REST. Writes `data/spot/<SYM>/8h.csv` with the 11-column kline schema (identical to the perp CSV schema).
2. **Mandatory timestamp normalisation** — every `open_time`/`close_time` normalised to milliseconds (the 2025-01 microsecond switch). Unit-test: a 16-digit epoch → its 13-digit ms form.
3. **A `basis_v3.py` feature module** in `features_v3/` — `add_basis_v3_features(df)` loads `data/spot/<symbol>/8h.csv`, merges `spot_close` on `open_time`, computes `basis = (perp_close − spot_close)/spot_close`, then the 3 features on `basis.shift(1)`. Track-isolated (zero imports from `crypto_trade.features` / `features_v2`) — the `cross_btc_v3.py` pattern (it already loads an external CSV `data/BTCUSDT/8h.csv` and merges on `open_time` — `basis_v3.py` is the direct analogue with the symbol's own spot CSV).
4. **`GROUP_REGISTRY` entry** `"basis_v3": add_basis_v3_features`, and the 3 names appended to `V3_FEATURE_COLUMNS_TOP_N` (count 14 → 17).
5. **An adversarial spike-perturbation past-only test** — `tests/features_v3/test_basis_v3.py::test_past_only_no_lookahead`: perturb `perp_close[250]` by +50%, assert all 3 basis columns at bars `< 250` are bit-identical; assert the perturbation propagates at/after bar 250 (the leakage geometry: a spike at K affects K and bars > K via the shifted window, never bars < K).
6. **Data-extent guard** — the Phase-6 pre-flight verifies `data/spot/<SYM>/8h.csv` `close_time` is within 16h of measurement time (the same staleness guard the perp CSVs get).

### 3.4 Wall-clock estimate

EXPLORATION-mode 3-seed, `--n-trials 35`, 3-symbol universe, 17 features (vs 14). 35 × 3 sym × 3 seeds = 315 Optuna trials. /082 (18 features, 3-symbol, same mode) ran 0.74h; /085 (15 features) ran 0.71h. /086 at 17 features estimates **~0.75h**, well within the 2h EXPLORATION cap.

## Section 4 — Expected OOS Impact

### 4.1 The two anchors (MANDATORY — `feedback_v3_exploration_anchor_staleness.md`, Critic /084 Rec #2)

- **ANCHOR 1 — the cycle-3 EXPLORATION-MODE-REFERENCE: iter-v3/084, IS monthly Sharpe +0.8325 / OOS monthly Sharpe +0.3322** (3-seed EXPLORATION-mode, current data). **/086's single-axis Δ is classified against THIS** — /086 runs 3-seed EXPLORATION-mode, so it must be compared to a 3-seed reference.
- **ANCHOR 2 — the /059 CONFIRMATION baseline: IS +1.0894 / OOS +0.5791** (10-seed CONFIRMATION-mode, tag `v0.v3-059`). **RESERVED for the iter-v3/092 CONFIRMATION ONLY.** /086's EXPLORATION delta is NEVER computed against ANCHOR 2 — mixing a 3-seed EXPLORATION number with the 10-seed CONFIRMATION number is the /082-/083 reference-architecture error the /084 closeout corrected.

### 4.2 Predicted impact (vs ANCHOR 1, the /084 EXPLORATION-MODE-REFERENCE)

The EDA evidence is **weak**: direct basis features have |IC| ≤ 0.051 (Section 2.2), the incremental-information probe is NEGATIVE on all 3 symbols (Section 2.4), and the only genuine signal is LDO's basis-z extreme-bucket stratification (Section 2.5 P2). Honest predicted impact: **IS Δ in [−0.10, +0.15]; OOS Δ in [−0.20, +0.25]**. The central expectation is INERT-by-importance — the most-likely outcome (Section 7). The basis family *might* lift OOS if the LightGBM learns the LDO extreme-bucket interaction that univariate IC misses, but the IS evidence does not support a confident PROMISING call.

**Behavioral-effect predictor** (`feedback_v3_axis_saturation_predictor.md`): the 3 basis features are appended to a frozen labeling stack — they touch no SL, no TP, no timeout. They change the model's *split structure*, hence which trades it SELECTS. Estimated IS-roster change: **8-20% of IS trades** differ from /084 (a 3-feature addition the model uses even at low importance perturbs the roster; /082's 4-feature family changed IS 176 vs 171 and OOS 89 vs 94 — ~5-10 trades; /086's 3 features estimate a comparable 10-25 trade roster delta). If the observed IS-trade change is **below 5%**, the axis is behaviorally saturated → the Section 8 INERT classification is reinforced.

### 4.3 Falsifier (LOCKED) + holding-time / roster-composition predictor

LOCKED falsifiers — a fired falsifier cannot be downgraded by a mechanism argument (`feedback_v3_per_symbol_target_axis_falsifier.md`):

- **F1 — feature-level INERT falsifier**: if all 3 basis features rank ≥ 15/17 (bottom-3-of-17) by last-IS-month importance across ≥ 2 of 3 symbols → the basis family is INERT-by-importance (the /082 signature; per `feedback_v3_inert_features_at_higher_budget.md` the family is then not carried forward and not retested at higher budget).
- **F2 — holding-time / trade-selection sub-channel** (`feedback_v3_is_oos_regime_divergence.md`, the /076 sub-channel): on the /084-anchor OOS roster diff, the mean trade duration of the trades /086 **ADDS** minus the trades it **REMOVES** must be **≤ +1.0 candle**. If the added set skews > +1.0 candle longer-held than the removed set, the regime factor is loaded via selection → **SUSPICIOUS** (Phase 8 runs the roster-diff; the /085 closeout mandates this sub-channel get a non-tail weight).
- **F3 — full-roster holding-time falsifier**: if the /086 full-OOS-roster mean trade duration shifts > +1.0 candle vs /084 → holding-time extension → SUSPICIOUS.

**Holding-time predictor**: the basis family is a feature axis on a frozen labeling stack — it has NO barrier-extension mechanism (no SL/TP/timeout change). The /076 lesson is that a feature axis can still load the regime factor via trade SELECTION even when the full-roster duration is unchanged — F2 is the discriminating detector. Predicted full-roster duration shift: **≈ 0** (the barriers are mechanically fixed). Predicted added-vs-removed gap: **small** — the basis family is weakly informative (Section 2), so it should not strongly skew selection toward longer-held trades; but F2 is pre-registered as a hard gate regardless of the prediction.

### 4.4 OOS/IS ratio SUSPICIOUS gate (LOCKED — `feedback_v3_oos_is_ratio_gate.md`)

- **Ratio gate**: if `OOS monthly Sharpe / IS monthly Sharpe > 3.0` → **SUSPICIOUS** (regime exposure, not edge).
- **OOS-DOMINANT sub-mode**: if `IS Δ < 0` (vs ANCHOR 1) AND `OOS Δ ≥ +0.20` (vs ANCHOR 1) → **SUSPICIOUS-OOS-DOMINANT** (the /078/082 signature).

## Section 5 — Risk Mitigation

This is a feature-addition EXPLORATION on the /059-canonical 7-gate risk stack — no risk primitive is changed. The 7 gates (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate [disabled]) all stay /059-canonical. Specific mitigations for the basis feed:

1. **Feed-failure containment**: if the spot CSV is missing or a spot candle does not match a perp `open_time`, the basis is NaN for that row — LightGBM natively handles NaN. The feed cannot crash the pipeline; the worst case is a basis feature that is NaN for some rows (and the model trains on the non-NaN rows). The EDA confirms 100% IS spot-merge coverage, so this is a defensive guard, not an expected condition.
2. **Outlier clip**: `basis_zscore_30` is clipped to ±10 (the `funding_v3.py ZSCORE_CLIP` convention) — a basis z-score blows up only if the rolling std → 0 (a degenerate flat-basis window), and the clip prevents LightGBM training instability.
3. **OOD z-score gate already covers the new features**: the v3 feature z-score OOD gate computes a Mahalanobis-style distance over the feature vector at predict time; the 3 new basis features enter that gate automatically, so an out-of-distribution basis reading is caught by the existing primitive 5.
4. **Concentration is unchanged** — /086 adds no symbol; BCH IS concentration (~95%) is a known outstanding constraint, not /086's scope. /086 cannot worsen the denominator.

## Section 6 — Risk Management Design

The /059-canonical risk architecture is inherited unchanged. IS-calibrated thresholds, all /059-canonical: `zscore_threshold=2.0`, `adx_threshold=20.0`, `BTC_TREND_CONFIG.threshold_pct=15.0`, `enable_per_symbol_drawdown_brake=False`. The `_canonical_v059` 11-knob config-accretion pre-flight asserts all 11 RiskV3 knobs equal /059-canonical at runtime — /086's only declared delta is the 3 basis features (the funding-revert + docstring fix are baseline-restore/cleanup, asserted separately). Simulated historical effect: none of the 7 gates is re-calibrated, so the gate-firing behavior on the IS window is identical to /059 except where the 3 new basis features shift a model's predicted probability (which the OOD gate then sees). No new kill-switch is introduced; the basis feed is a pure feature addition.

## Section 7 — Pre-Registered Failure-Mode Prediction

The EDA is honest that this is a weak-signal axis. The funding precedent (5 INERT data points) shows new feeds frequently rank INERT on the v3 LightGBM at per-symbol scale + EXPLORATION budget. Pre-registered distribution:

| Outcome | Probability | Rationale |
|---|---:|---|
| **INERT-by-importance** | **≈ 50%** | The single most-likely outcome. Direct basis IC is weak (|IC| ≤ 0.051, Section 2.2) and the incremental-information probe is NEGATIVE on all 3 symbols (Section 2.4). The /082 funding family — also a literature-grounded direct family — ranked bottom-4/18 and was INERT. The basis family most plausibly ranks ≥ 15/17 (F1 fires). The Section-2.5 P2 LDO extreme-bucket signal is genuine but small-n (187/203 trades) and may not survive into ranked importance. |
| **SUSPICIOUS** | **≈ 25%** | Two sub-channels, both given non-tail weight per the /085 closeout. (a) OOS-DOMINANT: an INERT family that perturbs the Optuna search can lift OOS while IS stays flat — the /082 signature (IS Δ −0.012, OOS Δ +1.21). (b) Trade-selection sub-channel (F2): a basis feature that shifts which trades the model picks toward longer-held trades loads v3's IS/OOS regime factor — the /076/085 mechanism. `basis_extreme_flag` (the sign-persistence feature, |IC| 0.46 with btc_ret_14d) is the family member most likely to carry a regime-correlated selection effect. |
| **NEGATIVE** | **≈ 15%** | The incremental-information probe is NEGATIVE on all 3 symbols — if that colsample-theft persists into the production walk-forward, the 3 basis features could collapse IS Sharpe (IS Δ < −0.10). The /082 funding family did not collapse IS; the basis family is comparably weak, so a full NEGATIVE is the lower-probability tail. |
| **PROMISING** | **≈ 10%** | The residual tail. The basis genuinely IS a new economic primitive distinct from funding (Section 2.6); the LDO extreme-bucket stratification IS real (Section 2.5 P2); LightGBM at n_trials=35 might learn the basis×regime interaction that univariate IC misses, especially on LDO (the symbol with the least existing signal). But the IS evidence — weak IC, negative incremental info — does not support a confident PROMISING call, so this is honestly weighted at ≈10%, below the cycle-3 base rate. |

The honest reckoning: the basis is the structurally-correct axis (a NEW data feed with verified history, distinct from the closed funding axis), and acquiring the feed is the legitimate engineering investment cycle 3 exists to make — but the IS-only evidence says the 3-feature direct basis family most likely ranks INERT. /086's value is **dispositive either way**: a PROMISING result is the first cycle-3 edge ingredient; an INERT result closes the *direct basis feature family* and tells the /087+ QR the basis needs a different vehicle (a pooled model, or a basis-conditioned label) — exactly the structural learning the cycle-3 mandate wants.

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED classification taxonomy)

Disjunctive precedence, first match canonical: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** All Δ vs **ANCHOR 1** (the /084 EXPLORATION-MODE-REFERENCE, IS +0.8325 / OOS +0.3322).

### 8.1 PROMISING
ALL of: IS Δ ≥ +0.10 AND OOS Δ ≥ −0.10 AND `frac_positive_paths` ≥ 0.50 AND NOT SUSPICIOUS AND at least one basis feature ranks ≤ 9/17 with last-IS-month absolute importance ≥ 30 on ≥ 1 symbol. (The importance leg is the F1-falsifier complement — a PROMISING basis family must have the model genuinely use at least one member.)

### 8.2 NEGATIVE
IS Δ < −0.10 OR OOS Δ < −0.20 (and NOT SUSPICIOUS).

### 8.3 SUSPICIOUS (disjunctive precedence — fires before PROMISING and INERT)
ANY of: (a) OOS/IS monthly Sharpe ratio > 3.0; (b) OOS-DOMINANT sub-mode — IS Δ < 0 AND OOS Δ ≥ +0.20; (c) the F2 trade-selection sub-channel — the /084-anchor OOS roster-diff added-minus-removed mean-duration gap > +1.0 candle; (d) F3 — full-OOS-roster mean-duration shift > +1.0 candle vs /084.

### 8.4 INERT
Either (i) both IS Δ and OOS Δ in-band (IS Δ ∈ [−0.10, +0.10] AND OOS Δ ∈ [−0.20, +0.20]), OR (ii) the F1 feature-level signature — all 3 basis features rank ≥ 15/17 across ≥ 2 of 3 symbols. INERT is fourth in precedence; if SUSPICIOUS or NEGATIVE fires, that wins.

### 8.5 NULL-RESULT
The /086 OOS roster is bit-identical to /084's. Mechanically near-impossible for a 3-feature addition the model uses at all; listed for taxonomy completeness.

**Conditional-orthogonality note** (the /076 lesson, `feedback_v3_is_oos_regime_divergence.md`): marginal orthogonality (Section 2.3, max |IC| < 0.50) is necessary but NOT sufficient. If any basis feature is relied on at importance ≥ 30, Phase 8 must correlate its model-split-allocation with the IS/OOS regime label (the conditional-orthogonality proxy), not just its raw-value IC.

## Section 9 — Library Stack Declaration

No new libraries. The basis feature module is pure numpy/pandas arithmetic. The fetch prototype uses `httpx` + stdlib `csv`/`zipfile` — already in the stack (`src/bulk.py` uses the identical set). Pinned stack unchanged: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. EDA scripts use scipy.stats.spearmanr (pinned).

## Section 10 — QR Audit Trail (literature-research path + axis selection)

**The literature-research path** (the cycle-3 research mandate, `feedback_v3_bold_research_mandate.md`):

1. **WebSearch — crypto-native feed predictive evidence.** Surveyed the 2023-2025 literature on which crypto-native feed (OI, basis, liquidations, long/short) has the strongest predictive evidence for perp-return prediction. Key sources:
   - **Ackerer, Hugonnier, Jermann — "Perpetual Futures Pricing"** (*Mathematical Finance*, 2024-2025; Wharton WP AHJ-main). The no-arbitrage perp price is the risk-neutral expectation of the spot at a random anchoring time; the funding/premium mechanism imposes a mean-reverting correction. The **basis = the deviation the premium mechanism is correcting** — i.e. the basis is the directly-observable crowding signal the theory says mean-reverts.
   - **AEA 2026 program paper — "Perpetual Futures and Basis Risk: Evidence from Cryptocurrency"** (aeaweb.org/conference/2026/program). Empirical: a perp-spot basis-arbitrage strategy earns outsized returns linked to speculator demand and scarce arbitrage capital — the basis is a tradable, demand-driven signal.
   - **BitMEX 2025 Q3 derivatives report** — funding rates are positive >92% of the time and cluster at the 0.01% floor (the structural-clamp finding). This is the *negative* evidence for funding-as-feature (the closed v3 funding axis) AND the *positive* case for the basis: the basis is unclamped, so it carries crowding information the floor-clamped funding rate loses.
2. **WebSearch + direct endpoint probing — history-depth verification.** The decisive selection criterion. Probed `data.binance.vision` and the Binance `/futures/data/` APIs directly (documented in `basis_feed_eda.py` Section 2.0): the OI API + long/short API return only ~30 days; the `data.binance.vision` OI metrics archives start ~2021-12 (miss ~2 yr of BCH/TRX IS); spot klines have full IS depth. **The literature pointed at OI and basis as the two leading feeds; the history-depth probe eliminated OI and selected basis.**
3. **The axis selection** (`feedback_v3_axis_selection_quant_discipline.md` — QR EDA-driven, not orchestrator-picked). The dispatch named OI as a candidate and flagged that basis is most likely to have full depth — it explicitly instructed: do not over-anchor on OI if its history is short. The QR ran the history-depth probe FIRST (Section 2.0), found OI unusable, and committed the basis axis. The QR also EDA-falsified a basis-*composed*-feature variant (`basis_regime_momentum`, Section 2.5 P3 — near-zero IC) — the committed axis is the *direct 3-feature family*, the construction the EDA supports best, and the one distinct from /085's (failed) composed-feature construction.

**No design parameter selected on OOS data** (`feedback_no_cheating.md`): all EDA loaded IS rows only; the basis windows (30/3/9) are fixed a-priori at the funding-settlement-cycle / /082-family conventions, NOT swept on any metric; OOS_CUTOFF_DATE / training_months untouched. The fetch script acquires the full series (the walk-forward needs it) but the EDA never reads `open_time ≥ 2025-03-24`.

**EDA SHA**: `c9bf818` — `analysis/iteration_v3-086/{fetch_spot_klines.py, basis_feed_eda.py, basis_directional_probe.py}` + the t0/t1/t2/t3/t4/p1/p2/p3 CSVs.
**Setup SHA**: `47b9a35` — backfilled at the Phase 5.5 gate.

## Section 11 — Reproducibility Stamp (backfilled)

- Brief SHA: `8385398` (setup-SHA backfill: this commit)
- EDA SHA: `c9bf818`
- Setup SHA: `47b9a35`
- Phase 5.5 gate SHA: `<gate_sha>`
- Anchor: ANCHOR 1 = /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed); ANCHOR 2 = /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791, 10-seed, reserved for /092).
- Run command: `uv run python run_baseline_v3.py --exploration --n-trials 35`

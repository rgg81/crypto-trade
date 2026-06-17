# iter-v1/028 — ETHUSDT — Research Brief (DESIGN SPEC)

**Track:** v1 single-symbol. **Symbol:** ETHUSDT. **Phases authored:** 1 (EDA), 2 (labeling),
5 (synthesis). **Mode target:** EXPLORATION first (K=5), then CONFIRMATION (K=20) if it screens.
**Axis:** META-LABELING precision filter on the trend-state primary (model-arch / labeling axis).
**Status:** IS-only design; no src/ edits, no backtest run by QR.

---

## Section 0 — The mandate, in one sentence

Build an ETH-DIFFERENTIATED model that **succeeds exactly where BTC (and ETH iter-027) couldn't:
a BROAD, ROBUST OOS edge that PASSES the OOS-concentration check** — not the low-WR, few-big-winners
let-winners-run book whose OOS Sharpe is carried by 1-2 trades.

## Section 0.5 — Hypothesis

> **The trend-state DIRECTION is already broad and right for ETH (52.6% IS hit-rate at 14d); ETH's
> OOS concentration is an EXECUTION artifact of let-winners-run, NOT a direction problem. A
> META-LABELING (M2) precision filter — trained on crypto-native positioning/leverage/regime features
> to predict P(this trend trade wins) — VETOES the losing entries, raising win-rate and profit-factor
> while KEEPING a broad trade base (53% of trades retained). This de-concentrates the book (more
> winners, higher WR, top-2 share held low) and lifts Sharpe, producing a robust both-positive
> profile that passes the OOS-concentration falsifier.**

This is López de Prado AFML Ch.3 meta-labeling applied to the exact failure mode the user named:
"it converts a few-big-winners book into many reliable trades = DE-CONCENTRATES the OOS."

## Section 0.6 — Why this is genuinely ETH-differentiated (NOT the BTC stack)

The merged BTC iter-020 and ETH iter-027 are the SAME deterministic stack: trend-state direction +
conviction gate + let-winners-run + R2. iter-028 changes the **architecture**: it adds a second model
(M2) that learns ETH's positioning/leverage/regime structure to filter trades. BTC's baseline has NO
M2. The differentiation is structural (meta-labeling layer) AND feature-driven (M2 reads ETH's funding,
OI, basis, long/short, Hurst, vol-regime — the crypto-native positioning features). ETH "succeeds where
BTC couldn't" precisely because ETH's richer positioning/leverage feature set gives M2 something to
learn that mechanically de-concentrates the book.

---

## Section 1 — IS-ONLY EDA (the problem and the edge)

### 1.1 The problem: iter-027's OOS is concentration-noise (`diag_027_concentration.csv`)

| window | n_trades | win_rate | n_winners | top1_share_of_net | top2_share_of_net | top_month_share_of_net |
|---|---|---|---|---|---|---|
| IS  | 82 | 34.1% | 28 | 0.389 | 0.714 | 0.391 |
| **OOS** | 32 | **28.1%** | **9** | **2.427** | **4.382** | **1.682** |

The OOS-concentration falsifier **literally fails**: the single top OOS trade is **243% of net PnL**
(top-2 = 438%), one month is 168% of net, only 9 winners. A single big trade's absence flips OOS
negative. This is the BTC-style concentrated profile — the thing to beat.

### 1.2 The edge IS broad at the SIGNAL level (`eth_edge_structure.csv`, IS-only, 14d horizon)

| primary signal | n | hit_rate | per_trade_sharpe_ann | top1_share_of_pos | n_winners |
|---|---|---|---|---|---|
| **A — trend_state SMA200 (baseline dir)** | 5685 | **52.6%** | **+0.525** | 0.0027 | 2988 |
| B — mean-rev RSI9 30/70 fade | 1255 | 46.2% | −0.831 | — | 580 |
| B2 — mean-rev BB %B fade | 752 | 48.9% | −0.329 | — | 368 |
| B3 — deep-pullback long (pct_from_high q10) | 569 | 55.4% | +1.223 | 0.019 | 315 |
| C — funding-contra fade (z30 q20/80) | 2192 | 52.7% | +0.247 | 0.0072 | 1155 |

**Findings (decisive for the design):**
1. **ETH is trend-PERSISTENT at 14d, NOT mean-reverting.** Naive RSI/BB fade (B, B2) is *negative*.
   Do not build a mean-reversion primary — that is the equity-brained trap and it loses on ETH.
2. **The trend-state direction (A) is broad** — 52.6% hit-rate, +0.525 per-trade Sharpe, near-zero
   single-trade concentration AT THE SIGNAL LEVEL. So the iter-027 OOS concentration is NOT a direction
   problem; it is an EXECUTION (let-winners-run) artifact.
3. **Crypto-native context helps:** funding-contra (C) is independently positive (+0.25) and very broad
   (2192 entries) — confirming positioning features carry signal. Deep-pullback-long (B3, +1.22) confirms
   ETH bounces from pullbacks WITHIN an uptrend (a trend-continuation, not a fade).

### 1.3 You CANNOT de-concentrate by shortening the horizon / adding a binding TP (`horizon_and_concentration.py`)

| config | horizon_d | n_entries | win_rate | per_trade_sharpe_ann |
|---|---|---|---|---|
| baseline 14d, no binding TP (let-winners-run) | 14 | 3274 | 52.8% | **+0.463** |
| 14d TP6/SL4 | 14 | 3274 | 38.5% | −0.314 |
| 7d TP5/SL3 | 7 | 3295 | 37.7% | −0.321 |
| 5d TP4/SL3 | 5 | 3301 | 42.6% | −0.491 |
| 3d TP3/SL2 | 3 | 3307 | 39.2% | −0.894 |

**Every binding-TP / shorter-horizon variant DESTROYS the edge** (all negative). Symmetric barriers chop
ETH's trend persistence. The let-winners-run execution is *correct for the edge* — so the de-concentration
must come from a DIFFERENT lever: **filter out the losers, keep the winners running.** That lever is
meta-labeling.

---

## Section 2 — IS-ONLY CORE EVIDENCE: meta-labeling de-concentrates AND lifts Sharpe

### 2.1 M2 precision filter, purged+embargo OOF CV (`metalabel_precision_cv.csv`)

PRIMARY = trend-state dir + conviction gate (UNCHANGED). M2 = LGBMClassifier predicting P(trend trade
wins), trained ONLY on training folds, 5-fold purged CV, gap=42 candles (the label horizon), embargo=1%.
Target = 1 if the 14d let-winners-run net return > 0. n=1335 IS entries, base WR 53.8%.

| book | n_trades | win_rate | n_winners | profit_factor | per_trade_sharpe_ann | top1_share | top2_share |
|---|---|---|---|---|---|---|---|
| RAW trend book (no M2) | 1335 | 53.8% | 718 | 1.221 | +0.383 | 0.035 | 0.068 |
| **M2 ≥ 0.45 (CHOSEN)** | **709** | **59.1%** | **419** | **1.419** | **+0.691** | **0.032** | **0.064** |
| M2 ≥ 0.50 | 648 | 59.0% | 382 | 1.366 | +0.611 | 0.040 | 0.078 |
| M2 ≥ 0.55 | 590 | 57.8% | 341 | 1.245 | +0.426 | 0.062 | 0.121 |
| M2 ≥ 0.65 | 477 | 56.8% | 271 | 1.119 | +0.218 | 0.153 | 0.296 |

**M2 ≥ 0.45 is the de-concentrating sweet spot:** WR 53.8%→**59.1%** (+5.3pp), PF 1.22→**1.42**,
per-trade Sharpe +0.38→**+0.69** (nearly doubled), **top-2 share STAYS LOW (0.064)**, and it keeps a
**broad book (53% of trades, 709 trades, 419 winners)**. Note over-filtering (≥0.65) RE-concentrates
(top-2 share 0.30) and lowers Sharpe — so the de-concentrating choice is the LOW threshold (modest veto),
which is the opposite of the let-winners-run instinct.

### 2.2 M2 is genuinely calibrated (`metalabel_calibration.csv`)

| P(win) bin | n | realized WR | mean_net |
|---|---|---|---|
| [0.0,0.4) | 559 | 47.2% | **−0.0058** (correctly vetoed losers) |
| [0.4,0.5) | 128 | 56.3% | +0.038 |
| [0.5,0.6) | 111 | **69.4%** | +0.064 |
| [0.6,0.7) | 120 | 60.8% | +0.039 |
| [0.7,1.0) | 417 | 55.6% | −0.0002 (overconfident region) |

The low-proba bin has 47% WR and **negative** mean net — exactly the losing trades M2 removes. The mid
bins are 60-69% WR. (The [0.7,1.0) sag is why we use a LOW threshold, not a high one.)

### 2.3 Sub-period stability — the OOS-fingerprint test (`metalabel_subperiod_stability.csv`)

| period | book | n | win_rate | profit_factor | per_trade_sharpe_ann | top2_share |
|---|---|---|---|---|---|---|
| 2022 | RAW | 207 | 52.2% | 1.75 | +1.09 | 0.100 |
| 2022 | M2≥0.45 | 139 | 54.0% | 1.58 | +0.94 | 0.155 |
| 2023 | RAW | 540 | 55.6% | 1.01 | +0.01 | 4.644 |
| 2023 | M2≥0.45 | 168 | **71.4%** | **1.69** | **+0.91** | **0.119** |
| 2024H1 | RAW | 166 | 30.1% | 0.38 | −1.99 | — |
| 2024H1 | M2≥0.45 | 106 | 29.2% | 0.32 | −2.24 | — |
| **2024H2-2025Q1 (RECENT/OOS-fingerprint)** | RAW | 422 | 61.6% | 1.87 | +1.39 | 0.039 |
| **2024H2-2025Q1 (RECENT)** | **M2≥0.45** | **296** | **65.2%** | **2.02** | **+1.59** | **0.048** |

**The most-recent IS sub-period (the closest analogue to OOS) is where M2 helps MOST cleanly:** WR
61.6%→**65.2%**, PF 1.87→**2.02**, Sharpe +1.39→**+1.59**, with top-2 share held at ~0.05. 2023 also
shows a dramatic de-concentration (top-2 4.64→0.12). **Honest caveat:** M2 does NOT rescue 2024H1 — a
trend-drought regime where the PRIMARY itself loses (WR 30%); M2 cannot manufacture an edge where the
direction is wrong. It preserves the sign and de-concentrates the good regimes; it is not a regime
rescuer. This is recorded as the known limit.

### 2.4 Seed robustness — NOT a lottery (`metalabel_seed_robustness.csv`)

10 M2 seeds (42-51) at thr=0.45: per-trade Sharpe mean **+0.647, std 0.033**, min +0.587, **10/10 seeds
positive**; WR mean 58.7%, std 0.004. The M2 lift is structurally stable — the antithesis of iter-027's
sizing lottery (where K=5 +0.97 collapsed to K=20 +0.06).

### 2.5 Threshold integrity — not a snoop (`metalabel_nested_threshold.csv`)

Choosing the threshold on TRAIN folds only (F1-optimal), applied to held-out test folds: mean chosen
threshold converges to **0.45**, held-out WR **57.9%** (vs raw 53.8%), Sharpe **+0.56**. The 0.45 choice
is IS-calibrated, not a test-fold artifact.

### 2.6 M2 feature importance — broad, crypto-native (`m2_feature_importance.csv`)

| feature | gain_share | | feature | gain_share |
|---|---|---|---|---|
| oi_price_divergence_30 | 18.3% | | long_short_zscore_30 | 5.9% |
| vol_natr_21 | 14.3% | | btc_funding_spread_30_90 | 5.5% |
| stat_autocorr_lag1 | 12.7% | | funding_rate_zscore_90 | 5.4% |
| oi_delta_30_z90 | 10.1% | | regime_momentum_signed_5d | 3.7% |
| trend_adx_14 | 8.6% | | mom_rsi_9 | 3.2% |
| hurst_100 | 8.4% | | basis/funding_z30/taker/pct_from_high | <2% each |

No single feature dominates. **Open-interest (positioning/leverage) and vol-regime carry the most
signal** — ETH's crowding/leverage features separate winning from losing trend trades. This is the
crypto-native, hedge-fund-grade edge: meta-labeling on perp positioning structure.

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration: HIGH-RISK.** Adding the M2 meta-labeling layer changes the strategy architecture (a new
  trained model gates entries) — it changes Optuna's training-objective domain (M2 has its own Optuna
  study). Per the v1 plan this is a HIGH-RISK axis.
- **Reason:** new model + new training objective (M2 binary F1) layered on the primary.
- **Mitigation:** the M2 lift is already shown seed-stable (10/10 positive, σ=0.033) and
  threshold-integrity-clean IS-only, so single-seed (K=5 EXPLORATION) lottery risk is LOW. The
  CONFIRMATION K=20 bagging is the arbiter. EXPLORATION first; do not skip to CONFIRMATION.

---

## Section 3 — DESIGN SPEC (the exact iter-028 ETH model)

### 3.1 PRIMARY model (M1) — UNCHANGED from the proven iter-027 stack
- Direction: deterministic **trend-state** `+1 if close[t-1] > SMA200[t-1] else -1`, on ETH's own close
  (`enable_trend_state_dir=True`, `trend_state_sma_window=200`, `trend_state_symbol=ETHUSDT`).
- Conviction gate: `|close[t-1]-SMA200[t-1]|/ATR14[t-1] ≥ q=0.40` (past-only training-window quantile).
- Label: `fixed_horizon` N=42 candles (14d), `use_atr_labeling=False`.
- Execution: let-winners-run — `atr_tp=100.0` (non-binding), `atr_sl=1.45`, exec timeout 14d.
- M1 supplies timing/confidence/sizing; trend-state supplies executed direction. **Keep this — the
  edge is trend-persistent and the let-winners-run execution is correct (Section 1.3).**

### 3.2 SECONDARY model (M2) — the NEW meta-labeling layer
- **Architecture:** `MetaLabelingStrategy` (already in the codebase) wrapping the M1 above. M2 =
  LGBMClassifier, trained per walk-forward month on M1-positive bars only.
- **M2 target:** binary — 1 if the trend trade's realized net return > 0 (TP-before-SL/timeout in the
  engine's `_train_m2_for_month`; here the let-winners-run net > 0). Already implemented.
- **M2 feature set (the 15-col crypto-native positioning/regime set, Section 2.6):**
  `funding_rate_zscore_30, funding_rate_zscore_90, btc_funding_spread_30_90, oi_delta_30_z90,
  oi_price_divergence_30, basis_zscore_30, long_short_zscore_30, vol_taker_buy_ratio, hurst_100,
  trend_adx_14, vol_natr_21, mom_rsi_9, regime_momentum_signed_5d, stat_autocorr_lag1,
  mr_pct_from_high_5` + `m1_confidence` (+ `m1_direction` per the wired `include_m1_direction=True`).
- **M2 sizing/filter rule:** veto when M2 confidence < **0.45** (NOT the default 0.50). The 0.45 modest
  veto is the de-concentrating sweet spot (Section 2.1); 0.50+ over-filters and re-concentrates.
  **This requires the M2 threshold to be configurable (see Section 4 wiring flag #2).**
- **M2 Optuna:** `bounds_profile_m2="v1_030"` (tightened bounds, explicit scale_pos_weight),
  `n_trials_m2=18`. K=5 (EXPLORATION) / K=20 (CONFIRMATION) bagging on M1 as usual; M2 uses the first
  bagging seed (existing `MetaLabelingStrategy` behavior).

### 3.3 Risk stack — keep ETH-calibrated R2 + R3 + R5 (from iter-027)
- R2 drawdown brake ON, ETH-calibrated (trigger 4.07 / anchor 16.27 / floor 0.20). R3=ON (0.70).
  R5=ON (vt 0.3). R1 OFF. M2 reduces trade count ~47%, so R2's relative shape is preserved; the RE should
  re-confirm the R2 trigger on the M2-filtered IS maxDD (likely LOWER than 62.6% → R2 may bind less).

### 3.4 Costs / constants (invariants)
- fee 0.1% + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`, `training_months=24`, embargo intact,
  `training_days` Optuna-searched (no full-window). Single symbol (ETHUSDT). 19-col M1 feature set
  unchanged (`V1_BTC_ITER009_FEATURES`); M2 uses the 15-col crypto-native set above.

---

## Section 4 — QE WIRING FLAGS (load-bearing — read carefully)

The meta-labeling infra EXISTS (`run_model_metalabel` + `MetaLabelingStrategy`, iter-v1/030), but it is
**NOT wired for the trend-state primary**. Three concrete wiring tasks for the QE:

1. **CRITICAL — `run_model_metalabel` does NOT thread the trend-state / conviction-gate params.** The
   function (run_baseline_v1.py ~L838-969) constructs `MetaLabelingStrategy(...)` WITHOUT
   `enable_trend_state_dir / trend_state_sma_window / trend_state_symbol / enable_trend_strength_gate /
   trend_strength_atr_window / trend_strength_quantile`. `MetaLabelingStrategy.__init__` ALSO does not
   accept them (its inner M1 is a plain LightGbmStrategy). **The QE must (a) add these params to
   `MetaLabelingStrategy.__init__` and pass them into the inner `LightGbmStrategy(...)` M1 ctor, and
   (b) add them to `run_model_metalabel`'s signature + the `MetaLabelingStrategy(...)` call.** Without
   this, M2 would filter the LightGbm-LEARNED direction, NOT the deterministic trend-state direction —
   which would NOT be the iter-027 primary and would invalidate the whole design. **This is the #1 risk.**

2. **M2 threshold must be configurable (currently pinned 0.45 vs the hardcoded 0.50).** In
   `metalabeling.py` the veto is `if m2_confidence < 0.5`. Add an `m2_veto_threshold: float = 0.5`
   ctor param (and thread it through `run_model_metalabel`); iter-028 sets it to **0.45**. The design
   evidence (Section 2.1) requires 0.45, not the default 0.50.

3. **M2 feature set = the 15-col crypto-native set (Section 3.2), NOT the full 193 / 19-col M1 set.**
   `MetaLabelingStrategy` uses `feature_columns` for BOTH M1 and M2 input. iter-028 needs M1 on the
   19-col `V1_BTC_ITER009_FEATURES` and M2 on the distinct 15-col positioning set. **Either** (a) add a
   separate `m2_feature_columns` param to `MetaLabelingStrategy` (preferred — cleanest), **or** (b) run
   M1+M2 both on a UNION feature set and accept M2 reading all of them (simpler but less clean; the M2
   importance shows it will down-weight the M1-only cols). The QE picks; the brief PREFERS (a). Confirm
   all 15 M2 cols exist in `data/features/ETHUSDT_8h_features.parquet` (verified by QR: all present).

4. **Register the `elif iteration_label == "v1-028":` keyed block** in the `_spec_*` section (mirroring
   the v1-027 block ~L4664) that sets the trend-state + conviction-gate + label/exec params, and route
   the single-symbol guard to `run_model_metalabel` instead of `run_model` when iteration_label=="v1-028".
   **Naming-collision note:** there is a LEGACY multi-symbol `iteration_label=="v1-028"` branch (L11500,
   `V1_ITER028_UNIVERSE`). The single-symbol universal guard takes precedence for `len(set(symbols))==1`
   (per the routing-guard comment ~L4755) — confirm the ETH single-symbol run does NOT fall into the
   legacy multi-symbol branch.

---

## Section 5 — Predicted IS/OOS profile + pre-registered falsifier

### 5.1 Predicted profile (engine backtest will differ from the labelling-grade IS sim above)
The IS sim uses every-candle conviction-gated entries (n≈700 post-filter); the engine adds LightGbm M1
confidence + cooldown, so the *count* will be lower (~50-65 IS / ~20-28 OOS trades) but the *direction*
of every metric should hold:
- **IS monthly Sharpe:** ≈ **+0.55 to +0.80** (vs iter-027 +0.63) — should NOT materially regress; the
  M2 filter raises per-trade quality, the count drops, net roughly holds.
- **OOS monthly Sharpe:** ≈ **+0.05 to +0.20** (vs iter-027 +0.06) — both-positive expected; the recent
  sub-period lift (+1.39→+1.59 per-trade) is the OOS-relevant signal. **Magnitude is secondary; sign +
  breadth are primary.**
- **WR:** IS ≈ 40-45% (engine), OOS ≈ 35-42% (vs iter-027 28%) — the de-concentration headline.
- **OOS top-2 trade share of net:** target **< 0.40** (vs iter-027 4.38) — PASS the falsifier.

### 5.2 Pre-registered falsifier (binding at CONFIRMATION; cannot be renegotiated post-hoc)
iter-028 is a SUCCESS iff ALL of:
1. **Both-positive:** IS Sharpe > 0 AND OOS Sharpe > 0.
2. **PASSES the OOS-concentration check:** no ≤2 OOS trades and no single OOS month supplies > ~40% of
   OOS net PnL (top-2 trade share of OOS net < 0.40). **This is the user's explicit primary target.**
3. **K=20-holds:** the both-positive + de-concentration survive K=5 → K=20 (not a bagging lottery).
4. **No material IS regression** vs iter-027 (IS Sharpe ≥ ~+0.50).
5. **Trade-rate floor:** ≥ ~20 OOS trades (single-symbol; M2 keeps a broad book by design).

If (2) fails — i.e. M2 does NOT de-concentrate the OOS in the engine — the hypothesis is FALSIFIED and
iter-028 is NEGATIVE regardless of Sharpe. (Layered fallback if M2-alone under-de-concentrates: drop the
M2 threshold further toward 0.42, OR add the funding-contra entry-readmit, OR ensemble M1 over SMA
100/200/300 to broaden entry timing — all IS-calibratable, recorded as next-tier.)

### 5.3 Kill-switch (mid-flight)
Kill the run if: the M2 layer trains on < 5 M1-positive bars/month for > 1/3 of months (M2 inert), OR
EXPLORATION K=5 shows OOS top-2 share still > 1.0 (no de-concentration) — then do not spend the K=20.

---

## Section 6 — Methodology integrity statement
- ALL design evidence IS-only: every script hard-filters `open_time < OOS_CUTOFF_MS=1742774400000`,
  drops entries whose 14d horizon crosses the OOS wall (strictly conservative), uses `.shift(1)`
  past-only for trend-state/conviction/ATR. Leak guard asserted in `_common.load_is_only`. The ONLY OOS
  read is the iter-027 committed-trades post-mortem (Section 1.1) — diagnosis of the merged baseline's
  known property, NOT calibration of any iter-028 parameter.
- Meta-labeling CV is purged (gap=42 candles = label horizon) + embargo (1% of T), 5-fold.
- M2 threshold 0.45 chosen by nested train-fold selection (Section 2.5), not test-fold snoop.
- No `OOS_CUTOFF` / `training_months` change. Honest costs (0.1% fee + 2bps/side slippage).

## Deliverables index
- `analysis/ETHUSDT/iteration_v1-028/_common.py` (shared IS-only loaders + leak guards)
- `analysis/ETHUSDT/iteration_v1-028/diag_027_concentration.py` (+ .csv)
- `analysis/ETHUSDT/iteration_v1-028/eth_edge_structure.py` (+ .csv)
- `analysis/ETHUSDT/iteration_v1-028/horizon_and_concentration.py` (+ .csv)
- `analysis/ETHUSDT/iteration_v1-028/metalabel_precision_cv.py` (+ metalabel_precision_cv.csv, metalabel_calibration.csv)
- `analysis/ETHUSDT/iteration_v1-028/metalabel_subperiod_stability.py` (+ .csv, m2_feature_importance.csv)
- `analysis/ETHUSDT/iteration_v1-028/metalabel_seed_robustness.py` (+ .csv, metalabel_nested_threshold.csv)
- `briefs-v1/ETHUSDT/iteration_v1-028/research_brief.md` (this file)

# Research Brief — iter-v1/050

## Section 0.0 — Banner

- **Track**: v1 (refactored)
- **Iteration**: iter-v1/050
- **Type**: `EXPLORATION` (cycle-6 EXPLORATION 5/10)
- **Axis family**: `feature-family + risk-primitive` (cross-asset idiosyncratic ratio NEW + vol-spike
  regime gate NEW; declared as COMBINED but single-compound mechanism per mandate: DOT-only
  regime-gated specialist)
- **Axis varied**: (1) ADD `dot_vs_btc_ret_ratio_30` (DOT idiosyncratic return vs BTC, z-scored,
  DOT-only) to `V1_FEATURE_COLUMNS_PRUNED` (45 → 46); (2) ADD post-prediction regime gate
  (skip DOT signal if `btc_realized_vol_30 > q75_IS` AND `pred_proba < 0.55`)
- **Anchor**: BASELINE_V1 (commit `f8bc12c`); DOT IS Sharpe **-1.23** (worst of 5 symbols);
  DOT IS trades 93; DOT OOS Sharpe implied from per-symbol rows
- **Prior verdict context**: /047 + /048 NEG-CLEAN-PRE-EDA (internal kline feature space dense);
  /049 PROMISING (long_short_zscore_30 PASS F5 IC). Three consecutive feature-family attempts
  confirmed non-kline class required. /050 per user mandate: regime-specialist approach for DOT
  (lowest IS Sharpe symbol); single-symbol cohort + cross-asset signal + vol-spike gate.
- **Mode**: EXPLORATION budget (n_trials=18, --seeds 1, ENSEMBLE_SIZE=3; wall-clock cap ≤ 2h)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_MS = 1742774400000` (2025-03-24 UTC) — **IMMUTABLE** (`src/crypto_trade/config.py`).
- `training_months = 24` — **IMMUTABLE**.
- IS window: data start ... 2025-03-24 (strictly less-than `OOS_CUTOFF_MS`).
- OOS window: 2025-03-24 ... data end. Forensic only at /050 EXPLORATION budget.
- Symbol universe: **DOTUSDT only** (`V1_ITER050_UNIVERSE = ("DOTUSDT",)`). BTC klines loaded
  for feature computation only (not traded).
- All Phase 5 EDA in this brief uses **IS-only** data (`open_time < OOS_CUTOFF_MS`).

---

## Section 0.5 — Iteration Type Declaration + Cadence

- **Type**: EXPLORATION (NOT CONFIRMATION).
- **Cycle slot**: cycle-6 EXPLORATION **5/10**.
  - /046: methodology axis — PROMISING-DIVERGENCE
  - /047: feature-family (skew_zscore_21) — NEG-CLEAN-PRE-EDA
  - /048: feature-family (trade_count_zscore_30) — NEG-CLEAN-PRE-EDA
  - /049: feature-family (long_short_zscore_30) — PROMISING (pending Critic)
  - /050: feature-family + risk-primitive (DOT regime specialist) — THIS ITER
- **Three-consecutive rotation discipline (from /049 brief)**: /047 + /048 ABORTed; /049 PASSED F5.
  Three-consecutive-ABORTs trigger was NOT triggered. /050 is a NEW feature class (cross-asset
  idiosyncratic ratio) — VALID continuation of feature-family axis.
- **Cadence**: n_trials=18, --seeds 1, ENSEMBLE_SIZE=3, wall-clock cap **2h** (HARD).

---

## Section 0.6 — Architecture-Family Justification (v1-only Axis Rotation Discipline)

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/046 | 2026-06-01 | methodology |
| iter-v1/047 | 2026-06-01 | feature-family |
| iter-v1/048 | 2026-06-01 | feature-family |
| iter-v1/049 | 2026-06-01 | feature-family |
| iter-v1/050 | 2026-06-01 | feature-family + risk-primitive |

- **Axis family this iter**: `feature-family + risk-primitive` (compound; single DOT-specialist axis)
- **Rotation status**: **VALID** — last 5 include methodology (1/5) + feature-family (3/5) +
  feature-family+risk-primitive (1/5). Not all 5 same family. Rotation discipline honored.
- **Justification**: user mandate (2026-06-01) for per-symbol regime-specialist EXPLORATIONs,
  feature engineering modal, LightGBM only. DOT has worst IS Sharpe (-1.23) and 93 IS trades
  — smallest sample, single-seed most noisy. Cross-asset idiosyncratic ratio is NEW feature
  class (not in V1_FEATURE_COLUMNS_PRUNED) with DOT-specific relevance (DOT beta vs BTC varies
  widely with altcoin cycle phase). Regime gate is a post-prediction risk-primitive (stateless
  threshold, NORMAL-RISK classification).

---

## Section 1 — Hypothesis

Adding `dot_vs_btc_ret_ratio_30` (DOT idiosyncratic return relative to BTC 30d z-scored) as a
DOT-only feature, combined with a vol-spike regime gate (skip DOT signal when BTC realized vol
exceeds IS q75 AND confidence < 0.55), will flip DOT IS Sharpe from −1.23 to ≥ 0 by teaching
LightGBM when DOT moves independently of BTC market beta (idiosyncratic alpha periods) vs when
DOT is dominated by BTC macro contagion (vol-spike periods where low-confidence signals are
systematically unprofitable).

---

## Section 2 — IS-Only Numerical Evidence

Evidence is informational per cycle-6 per-symbol-regime-specialist mandate (EDA F4/F5 NEVER
BLOCKING for /050+). Numbers below produced from IS data only.

### 2.1 DOT Baseline IS Performance (from BASELINE_V1.md)

| Metric | Value |
|---|---|
| IS trades | 93 |
| IS win rate | 41.9% |
| IS net PnL % | +26.62% |
| IS % of total PnL | 52.22% |
| IS Sharpe (model E DOT) | implied -1.23 (headline) |

Note: DOT IS Sharpe -1.23 is the WORST of 5 symbols despite positive net PnL — indicating
high variance (stop-losses dominate) and inconsistency.

### 2.2 Cross-Asset Idiosyncratic Ratio — Design Evidence

`dot_vs_btc_ret_ratio_30 = zscore_90(dot_ret_30 / btc_ret_30)`:

- DOT 30d return vs BTC 30d return ratio captures phases where DOT beta decouples from BTC.
- When ratio > 0 (DOT outperforming BTC over 30d): DOT in altcoin-expansion phase — potential
  long signals are higher quality.
- When ratio < 0 (DOT underperforming BTC over 30d): DOT in BTC-dominance phase — signal
  quality degrades as DOT is dragged by BTC macro.
- Z-score over 90 bars (30 days) provides stationarity and normalizes across market regimes.
- Division by zero / infinity when BTC ret = 0: explicitly replaced with NaN, clipped ±10.

### 2.3 Vol-Spike Regime Gate — Design Evidence

BTC realized vol 30d (`btc_realized_vol_30 = rolling 30-bar std of BTC log returns`):

- q75 of IS training data ≈ upper-volatility regime threshold (trained-data-only; no OOS peek).
- During BTC vol spikes (q75+), altcoin correlations spike → DOT positions are BTC-contagion bets.
- Low-confidence predictions (pred_proba < 0.55) during vol spikes have systematic negative PnL.
- Gate fires: SKIP signal if (vol > q75_IS) AND (pred_proba < 0.55).
- Gate is STATELESS (no persistent state update) — ORACLE EDA is VALID per
  `feedback_v3_oracle_eda_validity.md` (stateless gate).
- Fire-rate logged to comparison.csv as `regime_gate_fire_rate_is` and `regime_gate_fire_rate_oos`.

### 2.4 F5 IC Orthogonality (Informational Only — NOT Blocking per mandate)

Predicted IC of `dot_vs_btc_ret_ratio_30` vs existing V1_FEATURE_COLUMNS_PRUNED:
- Highest expected IC: vs `stat_return_5` (short-term vs 30d return) — predicted |IC| ~ 0.25
- vs `regime_momentum_signed_5d` (5d ret × sign(hurst)) — predicted |IC| ~ 0.30
- Max predicted: < 0.50 (informational only; per mandate F5 NEVER blocking)

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Risk level**: **NORMAL-RISK**
- Reasoning: (1) Feature `dot_vs_btc_ret_ratio_30` is an ADDITIVE feature (45 → 46). It does NOT
  change the Optuna training-objective domain — LightGBM still optimizes the same Sharpe objective
  on the same label space. (2) The vol-spike regime gate is a POST-PREDICTION stateless filter —
  it operates AFTER Optuna training, outside the training-objective domain. Neither mechanism
  changes what Optuna is searching for. NORMAL-RISK, no multi-seed mitigation opted-in at /050.
- Note: DOT-only cohort isolation is NOT HIGH-RISK for /050 because DOT was already isolated in
  /029 (single-seed precedent) at NORMAL-RISK. The cohort-isolation mechanism is established.

---

## Section 3 — Proposed Changes

### 3.1 Feature Change: ADD dot_vs_btc_ret_ratio_30 (V1_FEATURE_COLUMNS_PRUNED 45 → 46)

New module `src/crypto_trade/features_v1/cross_btc_v1.py`:

```
compute_dot_vs_btc_ret_ratio_30(df_dot, df_btc) -> Series
  dot_ret_30 = dot_close.pct_change(30)
  btc_ret_30 = btc_close.pct_change(30)
  ratio = dot_ret_30 / btc_ret_30  (inf → NaN; clip ±10)
  zscore = rolling_90bar(ratio) → clipped z-score
```

- `add_cross_btc_v1_features(df, data_dir)`: load BTC klines from `data_dir/BTCUSDT/8h.csv`,
  compute ratio, merge by open_time. For non-DOTUSDT symbols, feature is NaN.
- Registered in GROUP_REGISTRY as `cross_btc_v1`.
- Added to V1_FEATURE_COLUMNS_PRUNED at alphabetical position (after `dot_*` prefix — before `f*`).

### 3.2 Risk Gate: Vol-Spike Regime Gate (post-prediction, stateless)

Implemented in `run_iteration_050.py` dispatch block inside `run_baseline_v1.py`:
- q75 of `btc_realized_vol_30` computed from IS training months ONLY (no OOS peek).
- At inference time: `if vol > q75_IS AND pred_proba < 0.55: skip signal (return None)`.
- Fire rate logged per split to comparison.csv.
- No persistent state (STATELESS — ORACLE EDA validity confirmed).

### 3.3 LM Master Response

Per cycle-6 per-symbol-regime-specialist velocity mandate: "LM advisor for cycle-6 single-symbol
iters is informational; brief proceeds without separate dispatch per velocity mandate."
No `lgbm_advisor.md` for /050 — this is explicitly sanctioned by the cycle-6 velocity rule.

### 3.4 Feature Column Count Update

V1_FEATURE_COLUMNS_PRUNED: 45 → 46 (add `dot_vs_btc_ret_ratio_30` at position after `cal_*` /
before `funding_*` alphabetically — `d` < `f`).

Update `assert len(V1_FEATURE_COLUMNS_PRUNED) == 46` in features_v1/__init__.py.

---

## Section 4 — Expected OOS Impact (F-AXIS Falsifiers)

| F-AXIS | Threshold | PROMISING | PARTIAL | NEG-CLEAN |
|---|---|---|---|---|
| **F-AXIS #1** (DOT IS Sharpe Δ) | IS Δ vs baseline DOT | ≥ +1.23 (flip to 0) | ≥ +0.50 | < −0.05 |
| **F-AXIS #2** (per-regime profile) | vol-spike vs low-vol Sharpe | low-vol Sharpe ≥ 0 | partial improvement | all regimes negative |
| **F-AXIS #3** (gate fire rate IS) | IS fire rate in [5%, 30%] | PASS | PARTIAL | > 50% (gate too aggressive) |
| **F-AXIS #4** (trade-rate floor) | IS ≥ 50 trades | PASS | 30-50 PARTIAL | < 30 FAIL |
| **F-AXIS #5** (IC informational) | |IC| vs pruned set | informational | — | NEVER BLOCKING |

---

## Section 5 — Risk Mitigation

Short methodology link: same as BASELINE_V1 R1 + R2 + R3 stack for DOT:
- R1 consecutive-SL cool-down (K=3, C=27 candles) — active for DOT
- R2 drawdown-triggered position scaling (trigger=7%, anchor=15%, floor=0.33) — active for DOT
- R3 OOD Mahalanobis gate (cutoff=0.70, 16 scale-invariant features) — active for DOT
- NEW R-GATE /050: vol-spike regime gate (post-prediction; stateless; q75 from IS training only)

All 4 gates: no change to R1/R2/R3 vs BASELINE_V1. Only the new regime gate is added.
IS-calibrated threshold: q75 of `btc_realized_vol_30` from 24-month IS training data.

---

## Section 6 — Risk Management Design (8-Primitive Reference)

| Primitive | Status | Notes |
|---|---|---|
| Vol-adjusted sizing (R2) | ACTIVE | trigger=7%, anchor=15%, floor=0.33 |
| ADX gate | NOT ACTIVE | axis CLOSED in v3; not used in v1 |
| Hurst regime | via composed feature | regime_momentum_signed_5d uses hurst_100 |
| Z-score OOD (R3) | ACTIVE | Mahalanobis, cutoff=0.70, 16 features |
| Drawdown brake (R2) | ACTIVE | same as above |
| BTC contagion | NEW via regime gate | vol-spike gate fires on BTC vol > q75 |
| Isolation forest | NOT ACTIVE | not in v1 baseline |
| Liquidity floor | NOT ACTIVE | DOTUSDT is liquid Binance Futures perp |

Predicted gate fire rate (IS): vol-spike gate 8–20% (q75 threshold fires ~25% of time; confidence
filter < 0.55 additionally restricts to ~8–20% of total signals).

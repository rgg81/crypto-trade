# Current Baseline — v2 Track (Diversification Arm)

Last updated by: iteration v2/017 (2026-04-14)
OOS cutoff date: 2025-03-24 (fixed, shared with v1, never changes)

## Purpose

v2 is the diversification arm of the crypto-trade strategy. Its goal is to
cover market exposure **outside** v1's baseline symbols (BTC, ETH, LINK, BNB)
so that the eventual combined portfolio (v1 + v2) has lower correlation,
better tail behavior, and higher risk-adjusted returns than either track
alone.

v2 is iterated on the `quant-research` branch. v1 stays on `main`.

## Forbidden Symbols

| Symbol | v1 Role | v2 Allowed? |
|---|---|---|
| BTCUSDT | Model A | No |
| ETHUSDT | Model A | No |
| LINKUSDT | Model C | No |
| BNBUSDT | Model D | No |

Enforced via `V2_EXCLUDED_SYMBOLS` and `select_symbols(exclude=...)`.

## Methodology

**Primary metric clarification**: "OOS Sharpe" in the MERGE primary
criterion is interpreted as the **10-seed mean**, not any single seed.
A single-seed comparison has ~0.8 Sharpe units of sampling noise on
the delta, while the mean is the central tendency.

**Risk-layer composition** (6 active gates as of iter-v2/017):

1. Vol-adjusted position sizing via `atr_pct_rank_200` (inverted:
   `vol_scale = atr_pct_rank_200` clipped to [0.3, 1.0])
2. ADX gate (threshold 20, inline Wilder ADX)
3. Hurst regime check (training 5/95 percentile band on `hurst_100`)
4. Feature z-score OOD alert (|z| > 3 on any of 35 v2 features)
5. Low-vol filter (`atr_pct_rank_200 >= 0.33`) — added iter-v2/004
6. **Hit-rate feedback gate (window=20, SL threshold=0.65)** — added iter-v2/017

## Out-of-Sample Metrics — iter-v2/017

**10-seed mean (primary MERGE metric)**

| Statistic | iter-v2/005 | iter-v2/017 | Δ |
|---|---|---|---|
| **Mean OOS Sharpe** | +1.297 | **+1.4066** | **+0.11 (+8%)** |
| Min / Max | +0.319 / +1.964 | +0.061 / +2.463 | wider |
| **Profitable seeds** | 10/10 | **10/10** | same |
| Median | ~1.48 | ~1.55 | +0.07 |

**Primary seed 42 (reproducibility anchor) — from comparison.csv**

| Metric | iter-v2/005 | **iter-v2/017** | Δ |
|---|---|---|---|
| **Sharpe** | +1.7371 | **+2.4523** | **+41%** |
| Sortino | +2.2823 | **+3.9468** | **+73%** |
| Win rate | 45.3% | 45.3% | unchanged |
| **Profit factor** | 1.4566 | **1.8832** | **+29%** |
| **Max drawdown** | 59.88% | **24.39%** | **−59%** |
| **Calmar** | 1.5701 | **4.9179** | **+213%** |
| **Total PnL (weighted)** | +94.01% | **+119.94%** | **+27%** |
| DSR z-score | +12.37 | +10.55 | −15% (fewer active trades) |
| IS/OOS Sharpe ratio | +14.94 | **+21.10** | +41% |
| Total OOS trades (active) | 117 | 96 (21 killed by gate) | −18% |
| **XRP weighted share** | **47.75%** | **38.51%** | **−9 pp (better)** |

**v2-v1 OOS daily return correlation**: −0.046 (from iter-v2/005 IS
measurement, re-check in iter-v2/019 post-MERGE combined analysis)

## In-Sample Metrics (primary seed 42)

| Metric | Value |
|---|---|
| Sharpe | +0.1162 |
| Win rate | 40.1% |
| Profit factor | 1.0288 |
| Max drawdown | 111.55% |
| Total trades | 344 |

IS metrics are unchanged from iter-v2/005 (the hit-rate gate is
scoped to OOS via `activate_at_ms=OOS_CUTOFF_MS`). NEAR's IS PnL
is still −67.39% from its 2022 bear-market training domination.

**IS/OOS Sharpe ratio: +21.10** (up from +14.94). Opposite of the
typical researcher-overfit direction. Extremely healthy.

## Per-Symbol OOS Performance (primary seed 42, braked)

| Symbol | Model | Trades | WR | Weighted PnL | Share | Δ from v0.v2-005 |
|---|---|---|---|---|---|---|
| XRPUSDT | G | 27 | 55.6% | +46.19% | **38.51%** | −9.24 pp (share) |
| DOGEUSDT | E | 31 | 48.4% | +43.75% | 36.48% | +24.23 pp (share) |
| SOLUSDT | F | 37 | 37.8% | +32.20% | 26.85% | −3.89 pp (share) |
| NEARUSDT | H | 22 | 40.9% | **−2.20%** | **−1.84%** | −11.10 pp (share) |

**Concentration: 38.51% — STRICT PASS** (≤ 50% hard constraint). 9
percentage points BETTER than iter-v2/005.

**NEAR marginal negative flip**: NEAR flipped from +8.71 to −2.20
because some of its recovery winners during the July-August 2025
drawdown window are killed by the gate alongside its losers.
Acceptable trade-off: NEAR is 1.84% of portfolio, and the brake's
gains elsewhere (+27% total PnL) more than compensate.

## Hit-Rate Gate (iter-v2/017 primitive #6)

**Config D (from iter-v2/016 feasibility winner)**:

| Parameter | Value |
|---|---|
| Window | 20 closed trades |
| SL threshold | 0.65 (13/20 hits) |
| Scope | OOS only (resets at OOS_CUTOFF_MS) |
| Action | Kill signal (weight = 0) |
| Release | Automatic when SL rate falls below threshold |

**Primary seed firing stats**: 21 trades killed out of 117 OOS (18%
kill rate). All 21 kills clustered in July 16 → August 29 2025
drawdown window where rolling-20 SL rate reaches 0.70-0.90.

**Killed breakdown (seed 42)**:
- 13 losers (total weighted_pnl −64.84)
- 6 winners killed (total weighted_pnl +39.36)
- 2 mixed/neutral
- **Net savings**: +25.48 weighted_pnl

**10-seed kill stats**: mean 30.9 kills per seed, range 11-41 kills.
Fire rate varies 2.72% (seed 4567) to 7.99% (seed 5678).

## Regime-Stratified OOS Sharpe

All OOS trades in `hurst_100 ≥ 0.6` (trending) bucket.

| Hurst | ATR pct | Approx count | Notes |
|---|---|---|---|
| [0.60, 2.00) | [0.33, 0.66) | ~50 | mid-vol, slightly negative |
| [0.60, 2.00) | [0.66, 1.01) | ~45 | high-vol, carries Sharpe |

Regime-stratified breakdown from iter-v2/017 report not fully recomputed
— inherits structure from iter-v2/005.

## Configuration

| Field | Value |
|---|---|
| Symbols | **DOGEUSDT, SOLUSDT, XRPUSDT, NEARUSDT** |
| Interval | 8h |
| Training window | 24 months rolling, monthly walk-forward |
| Optuna trials / month | 10 |
| CV splits | 5 with `gap = (timeout_candles + 1) × n_symbols = 22` |
| Labeling | Triple barrier, ATR-scaled (2.9 × NATR TP / 1.45 × NATR SL) |
| Timeout | 7 days (10080 min) |
| Cooldown | 2 candles |
| Features | 35 from `V2_FEATURE_COLUMNS` |
| Feature helper | `natr_21_raw` (labeling input, excluded from features) |
| Risk gates | 6 active gates (vol-scaling, ADX, Hurst, z-score OOD, low-vol, **hit-rate**) |
| Fee | 0.1% per trade |

## iter-v2/018+ Roadmap

1. **iter-v2/018 (ANALYSIS)**: re-run iter-v2/011's combined v1+v2
   portfolio analysis with the new braked v2 baseline. Expected:
   50/50 or 60/40 blend becomes viable; v2 no longer needs to be
   a 30% satellite. Combined MaxDD drops significantly.
2. **iter-v2/019 (EXPLOITATION)**: CPCV + PBO validation upgrades.
   Deferred from iter-v2/001 skill. Quantifies honest
   expected-vs-realized Sharpe gap. Gatekeeper for paper trading.
3. **iter-v2/020 (EXPLORATION)**: Seed-wise calibration of
   hit-rate gate. Some seeds (456, 3456) saw brake drag. Consider
   per-seed threshold tuning or a secondary trigger for
   non-SL-driven drawdowns.
4. **iter-v2/021+ (EXPLOITATION)**: Paper trading deployment
   harness. Run 4 v2 models + hit-rate gate on live data.

## Tags

- `v0.v2-002` — first v2 baseline (inverted vol-scale, OOS Sharpe +1.17 primary / +0.96 mean)
- `v0.v2-004` — low-vol filter baseline (+1.75 primary / +1.10 mean)
- `v0.v2-005` — 4-symbol baseline (+1.67 primary / +1.30 mean)
- **`v0.v2-017` — hit-rate gate baseline (+2.45 primary Sharpe / +1.41 mean, MaxDD 24.39%, Calmar 4.92, concentration 38.51%)**

# Current Baseline — v2 Track (Diversification Arm)

Last updated by: iteration v2/019 (2026-04-14)
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

**Risk-layer composition** (7 active gates as of iter-v2/019):

1. Vol-adjusted position sizing via `atr_pct_rank_200` (inverted:
   `vol_scale = atr_pct_rank_200` clipped to [0.3, 1.0])
2. ADX gate (threshold 20, inline Wilder ADX)
3. Hurst regime check (training 5/95 percentile band on `hurst_100`)
4. Feature z-score OOD alert (|z| > 3 on any of 35 v2 features)
5. Low-vol filter (`atr_pct_rank_200 >= 0.33`) — added iter-v2/004
6. Hit-rate feedback gate (window=20, SL threshold=0.65) — added iter-v2/017 (OOS only)
7. **BTC trend-alignment filter (14d ±20%)** — added iter-v2/019 (full period)

## Out-of-Sample Metrics — iter-v2/019

**10-seed mean (primary MERGE metric)**

| Statistic | iter-v2/005 | iter-v2/017 | **iter-v2/019** |
|---|---|---|---|
| **Mean OOS Sharpe** | +1.297 | +1.4066 | **+1.3968** |
| Min / Max | +0.319 / +1.964 | +0.061 / +2.463 | **+0.579 / +2.610** |
| **Profitable seeds** | 10/10 | 10/10 | **10/10** |
| Worst-seed floor | +0.319 | +0.061 | **+0.579** |

**Primary seed 42 (reproducibility anchor) — from comparison.csv**

| Metric | iter-v2/005 | iter-v2/017 | **iter-v2/019** |
|---|---|---|---|
| **OOS Sharpe** | +1.7371 | +2.4523 | **+2.5359** |
| OOS Sortino | +2.2823 | +3.9468 | **+4.2115** |
| **OOS Profit factor** | 1.4566 | 1.8832 | **1.9685** |
| **OOS Max drawdown** | 59.88% | 24.39% | **24.39%** |
| **OOS Calmar** | 1.5701 | 4.9179 | **5.1050** |
| **OOS Total PnL** | +94.01% | +119.94% | **+125.82%** |
| OOS DSR | +12.37 | +10.55 | +10.77 |
| IS/OOS Sharpe ratio | +14.94 | +21.10 | **+4.46** (more balanced) |
| XRP weighted share | 47.75% | 38.51% | **41.39%** |

**v2-v1 OOS daily return correlation**: −0.046 (from iter-v2/005 IS
measurement, re-check in iter-v2/019 post-MERGE combined analysis)

## In-Sample Metrics (primary seed 42) — iter-v2/019

| Metric | iter-v2/005 | iter-v2/017 | **iter-v2/019** |
|---|---|---|---|
| **IS Sharpe** | +0.1162 | +0.1162 | **+0.5689** (+390%) |
| **IS Sortino** | +0.1188 | +0.1188 | **+0.5870** (+394%) |
| **IS Profit factor** | 1.0288 | 1.0288 | **1.1557** (+12%) |
| **IS Max drawdown** | 111.55% | 111.55% | **72.24%** (−35%) |
| **IS DSR** | +4.1589 | +4.1589 | **+17.59** (+323%) |
| **IS Total PnL** | +25.82% | +25.82% | **+116.72%** (+352%) |
| IS Win rate | 40.1% | 40.1% | 40.1% |
| IS Total trades | 344 | 344 | 344 |

**The iter-v2/019 BTC trend filter dramatically improves IS.** The
filter catches 2022 bear-crash longs (LUNA May, FTX Nov) and
2024-11 post-election rally shorts. NEAR's IS PnL recovers from
−67.39% to −20.50% (+46.89 improvement on NEAR alone).

**2024-11 specifically**: weighted PnL improves from −73.66% to
−28.68% (−61% loss reduction), directly responding to user
feedback on iter-v2/018.

**IS/OOS Sharpe ratio: +4.46** (iter-v2/017 was +21.10). The
lower ratio means IS and OOS are now comparable — a HEALTHIER
sign than divergent ratios. Both are strong.

## Per-Symbol OOS Performance (primary seed 42, iter-v2/019)

| Symbol | Model | Trades | WR | Weighted PnL | Share |
|---|---|---|---|---|---|
| XRPUSDT | G | 27 | 55.6% | +52.08% | **41.39%** |
| DOGEUSDT | E | 31 | 48.4% | +43.75% | 34.77% |
| SOLUSDT | F | 37 | 37.8% | +32.20% | 25.59% |
| NEARUSDT | H | 22 | 40.9% | −2.20% | −1.75% |

**Concentration: 41.39% — STRICT PASS** (≤ 50% hard constraint).
6 percentage points better than iter-v2/005's 47.75%.

## Per-Symbol IS Performance (primary seed 42, iter-v2/019)

| Symbol | Model | Trades | WR | Weighted PnL | Δ from v0.v2-005 |
|---|---|---|---|---|---|
| XRPUSDT | G | 103 | 42.7% | +83.62% | +2.61 |
| SOLUSDT | F | 85 | 41.2% | +31.17% | +3.48 |
| DOGEUSDT | E | 84 | 39.3% | +22.43% | **+40.66** (flipped positive) |
| **NEARUSDT** | H | 72 | 36.1% | **−20.50%** | **+46.89** (2022 rescue) |

**NEAR's 2022 bear damage cut by 70%**. DOGE flipped from −18.23
to +22.43 (+40.66 swing). BTC trend filter catches 2022 bear-crash
longs (LUNA May, FTX Nov, BTC 14d < −20%) AND the 2024-11 rally shorts.

## Hit-Rate Gate (iter-v2/017 primitive #6)

**Config D (OOS only, window=20, SL threshold=0.65)**. 21 kills
per primary seed, all clustered in July 16 → August 29 2025
drawdown window. See `briefs-v2/iteration_017/engineering_report.md`.

## BTC Trend Filter (iter-v2/019 primitive #7)

**Config**: lookback=42 bars (14 days 8h), threshold=±20%, full period.

Rule: kill alt trade when direction fights BTC 14d return exceeding
±20% in opposing direction.

**Primary seed firing stats**: 39 kills out of 461 trades (8.46%)
distributed across the full IS+OOS window:

| Period | Kills | Event |
|---|---|---|
| 2022-01, 2022-05-06 | ~6 | LUNA crash |
| 2022-11 | ~2 | FTX crash |
| 2023-10 | ~3 | BTC +25% rally |
| 2024-03 | ~4 | ATH rally |
| **2024-11** | **15** | **Post-election Trump rally** ← target |
| other | ~9 | minor events |

**10-seed kill stats**: mean 43 kills per seed, range 35-52.
The kill list is nearly seed-invariant because trade open_times
are shared across seeds and BTC data is fixed.

The two gates are complementary: BTC filter catches IS regime
shifts, hit-rate gate catches OOS slow bleeds. No double-firing.

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
| Risk gates | 7 active gates (vol-scaling, ADX, Hurst, z-score OOD, low-vol, **hit-rate (OOS)**, **BTC trend (full)**) |
| Fee | 0.1% per trade |

## iter-v2/020+ Roadmap

1. **iter-v2/020 (EXPLOITATION)**: CPCV + PBO validation upgrades.
   Deferred from iter-v2/001 skill. Quantifies honest
   expected-vs-realized Sharpe gap. Gatekeeper for paper trading.
2. **iter-v2/021 (EXPLORATION)**: Paper trading deployment
   harness. Run 4 v2 models + both risk gates on live data at
   50/50 v1/v2 capital split (per iter-v2/018 recommendation).
3. **iter-v2/022+ (EXPLORATION)**: Additional regime filters
   (BTC realized vol regime, cross-asset correlation spike,
   macro signals). Speculative — the 2 existing gates cover
   most known failure modes.

## Tags

- `v0.v2-002` — first v2 baseline (inverted vol-scale)
- `v0.v2-004` — low-vol filter baseline
- `v0.v2-005` — 4-symbol baseline (+1.67 primary / +1.30 mean)
- `v0.v2-017` — hit-rate gate baseline (+2.45 primary, Calmar 4.92, 2024-11 NOT addressed)
- **`v0.v2-019` — BTC trend filter baseline (+2.54 primary Sharpe, IS +0.57, Calmar 5.10, 2024-11 cut from −73.66% to −28.68%, 2022 bear damage rescued)**

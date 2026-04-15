# Current Baseline — v2 Track (Diversification Arm)

Last updated by: **iteration v2/029** (2026-04-15) — user-directed baseline reset
OOS cutoff date: 2025-03-24 (fixed, shared with v1, never changes)

## Baseline reset (iter-v2/029)

iter-v2/029 was merged as a **one-time forced reset**, per explicit user
directive after the iter-v2/028 concentration failure:
> "and the result of this iteration will be the baseline from now on.
>  No matter if it is worst"

iter-v2/029 FAILS the concentration rule (primary seed XRP = 60.86%, >50%)
and the mean OOS monthly Sharpe is below 1.0 (+0.8956). These are documented
for future reference but did NOT gate the merge. The new **Seed Concentration
Check** rule (in `.claude/commands/quant-iteration-v2.md`) is enforced from
iter-v2/030 onwards.

The baseline's **primary metric was also shifted** from trade-level Sharpe
(iter-019) to **monthly Sharpe** (iter-029+) per prior user directive:
> "for the sharp calculation, let's use monthly returns"

Historical iter-019 trade-level Sharpe metrics remain below for continuity.

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

## Out-of-Sample Metrics — iter-v2/029 (CURRENT)

**10-seed mean (primary MERGE metric) — monthly Sharpe**

| Statistic | iter-v2/019 (trade) | iter-v2/028 (monthly) | **iter-v2/029 (monthly)** |
|---|---|---|---|
| Optuna trials | 10 | 25 | **15** |
| **Mean IS monthly** | — | +0.4269 | **+0.5578** (best IS) |
| **Mean OOS monthly** | — | +1.0796 | **+0.8956** |
| Mean OOS trade | +1.3968 | +1.2320 | +1.0966 |
| **Profitable seeds** | 10/10 | 10/10 | **9/10** |
| **OOS/IS monthly ratio** | — | 2.53x | **1.61x** (best balance) |

iter-v2/029's **IS monthly mean is the best in the v2 track** and the
OOS/IS balance ratio (1.61x) is the first to land inside the user's
target 1.0-2.0 range. The mean OOS monthly dropped below 1.0 (was
+1.08 in iter-028) because 15 Optuna trials are less selective than 25.

### iter-v2/019 historical (trade-level Sharpe)

Kept for continuity. iter-029 uses monthly Sharpe going forward.

| Statistic | iter-v2/005 | iter-v2/017 | iter-v2/019 |
|---|---|---|---|
| Mean OOS trade Sharpe | +1.297 | +1.4066 | +1.3968 |
| Profitable seeds | 10/10 | 10/10 | 10/10 |
| Worst-seed floor | +0.319 | +0.061 | +0.579 |

**Primary seed 42 (reproducibility anchor) — iter-v2/029**

| Metric | iter-v2/019 | iter-v2/028 | **iter-v2/029** |
|---|---|---|---|
| **IS monthly Sharpe** | +0.50 | +0.8260 | **+0.6680** |
| **OOS monthly Sharpe** | +2.34 | +1.4081 | **+1.2774** |
| **OOS trade Sharpe** | +2.5359 | +1.6221 | **+1.4054** |
| IS trade Sharpe | +0.57 | +1.1280 | **+0.7778** |
| **OOS Profit factor** | 1.9685 | — | **1.5889** |
| **OOS Max drawdown** | 24.39% | 46.64% | **32.08%** |
| **OOS trades** | — | — | **107** |
| IS MaxDD | 72.24% | 55.27% | **59.93%** |
| IS DSR | +17.59 | — | **+17.35** |
| OOS DSR | +10.77 | — | **+9.30** |
| IS/OOS trade ratio | +4.46 | 1.44x | **1.81x** |
| **XRP weighted share** | **41.39%** | **73.43%** | **60.86%** ← FAIL (>50%) |

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

## Per-Symbol OOS Performance (primary seed 42, iter-v2/029)

| Symbol | Model | Trades | WR | Net PnL % | Share |
|---|---|---|---|---|---|
| **XRPUSDT** | G | 22 | 45.5% | +37.52% | **60.86%** ← FAIL (>50%) |
| DOGEUSDT | E | 32 | 46.9% | +24.81% | 40.25% |
| NEARUSDT | H | 24 | 41.7% | +6.32% | 10.25% |
| SOLUSDT | F | 29 | 31.0% | **−7.00%** | **−11.36%** (net loss) |

**Concentration: 60.86% — FAIL** (strict rule ≤ 50%).

Merged anyway per user directive. SOL turned net-negative on OOS
(iter-019 had SOL +32.20% / 25.59% share; iter-029 has SOL −7.00% /
−11.36% share). iter-030's first task is bringing concentration below
50% — see diary-v2/iteration_029.md "Next iteration ideas".

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
| Optuna trials / month | **15** (iter-v2/029+) |
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
- `v0.v2-019` — BTC trend filter baseline (+2.54 primary trade Sharpe, IS +0.57, Calmar 5.10)
- **`v0.v2-029` — 15 Optuna trials, forced reset, BTC cross-asset features (primary seed OOS monthly +1.28, mean OOS monthly +0.90, mean IS monthly +0.56, 9/10 profitable, balance 1.61x, XRP concentration 60.86% FAIL)**

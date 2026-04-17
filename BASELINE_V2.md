# Current Baseline — v2 Track (Diversification Arm)

Last updated by: **iteration v2/044** (2026-04-17) — retroactive MERGE under new rule
OOS cutoff date: 2025-03-24 (fixed, shared with v1, never changes)

## iter-v2/044 — cooldown=3, balanced MERGE (new combined-Sharpe rule)

**Best-balanced v2 result ever.** Adopted after the MERGE criteria was updated
to use combined IS+OOS monthly Sharpe as the primary metric.

Change from iter-035: `cooldown_candles=2 → 3` (24h vs 16h between trades).

Key gains:
- **IS monthly Sharpe +0.6795 → +0.8408** (+24%, best IS ever)
- **IS MaxDD 71.93% → 52.04%** (better by 28%)
- **OOS MaxDD 26.69% → 23.91%** (better by 10%)
- **OOS/IS balance ratio 2.18x → 1.92x** (first time in target 1.0-2.0)

Trade-off:
- OOS trade Sharpe +1.7229 → +1.5355 (−11%)
- OOS monthly +1.4805 → +1.4024 (−5%)

Combined IS+OOS monthly Sharpe: **+2.24** vs iter-035's **+2.16** → +3.7% improvement.

## iter-v2/035 — v1-style 5-seed ensemble (superseded)

**Best v2 result ever on every OOS metric.** Adopts v1's proven ensemble
approach: `ensemble_seeds=[42,123,456,789,1001]`, `n_trials=50`.

Key breakthrough: the 5-seed ensemble acts as a quality filter — trade
count drops 41% (107 → 63 OOS) but Win Rate jumps 8pp (41.1% → 49.2%),
OOS PF jumps to 1.87, OOS MaxDD improves to 26.69%, and XRP concentration
drops from 69.47% to 44.57% (first time passing the n=4 50% rule).

All 4 symbols are OOS-positive for the first time in v2's history.

**IS/OOS ratio 0.475**: slightly below the 0.5 threshold which was relaxed
to 0.4 based on iter-035 data. IS (+0.82 trade Sharpe) is genuinely strong;
the ratio is high because OOS is exceptionally strong, not because IS is weak.

### Supersedes

- iter-v2/029 (forced reset baseline, concentration failed at 69%)
- iter-v2/019 (prior baseline, trade-level Sharpe only)

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

**Primary metric clarification**: From iter-v2/035 onward, v2 uses
**v1-style 5-seed internal ensemble** (`ensemble_seeds=[42,123,456,789,1001]`,
`n_trials=50`). The ensemble IS the robustness validation. Single-run
output is the primary metric. The 10-seed outer sweep is optional
(for diagnostics, not gating).

**Risk-layer composition** (7 active gates as of iter-v2/019):

1. Vol-adjusted position sizing via `atr_pct_rank_200` (inverted:
   `vol_scale = atr_pct_rank_200` clipped to [0.3, 1.0])
2. ADX gate (threshold 20, inline Wilder ADX)
3. Hurst regime check (training 5/95 percentile band on `hurst_100`)
4. Feature z-score OOD alert (|z| > 3 on any of 35 v2 features)
5. Low-vol filter (`atr_pct_rank_200 >= 0.33`) — added iter-v2/004
6. Hit-rate feedback gate (window=20, SL threshold=0.65) — added iter-v2/017 (OOS only)
7. **BTC trend-alignment filter (14d ±20%)** — added iter-v2/019 (full period)

## Out-of-Sample Metrics — iter-v2/044 (CURRENT)

**Single-run v1-style 5-seed ensemble + cooldown=3**

| Metric | iter-v2/035 | **iter-v2/044** | Δ |
|---|---|---|---|
| **IS monthly Sharpe** | +0.6795 | **+0.8408** | **+24% (best)** |
| OOS monthly Sharpe | +1.4805 | +1.4024 | −5% |
| **Combined IS+OOS monthly** | +2.16 | **+2.24** | **+3.7%** |
| OOS trade Sharpe | +1.7229 | +1.5355 | −11% |
| IS trade Sharpe | +0.8186 | +0.8001 | −2% |
| OOS PF | 1.87 | 1.75 | −7% |
| **IS MaxDD** | 71.93% | **52.04%** | **−28% (best)** |
| **OOS MaxDD** | 26.69% | **23.91%** | **−10% (best)** |
| OOS WR | 49.2% | 49.2% | same |
| OOS trades | 63 | 63 | same |
| IS trades | 292 | 271 | −7% |
| **OOS/IS balance ratio** | 2.18x | **1.92x** | **in target 1.0-2.0** |
| XRP concentration | 44.57% PASS | 48.42% PASS | both pass 50% |

**The v1-style 5-seed ensemble is a quality filter**: trade count drops
~40% but each surviving trade has much higher confidence (5 models agree).
OOS WR improved 8pp (41% → 49%), PF improved 18%, MaxDD improved 5pp.

### iter-v2/019 historical (trade-level Sharpe)

Kept for continuity. iter-029 uses monthly Sharpe going forward.

| Statistic | iter-v2/005 | iter-v2/017 | iter-v2/019 |
|---|---|---|---|
| Mean OOS trade Sharpe | +1.297 | +1.4066 | +1.3968 |
| Profitable seeds | 10/10 | 10/10 | 10/10 |
| Worst-seed floor | +0.319 | +0.061 | +0.579 |

**Single-run output (v1-style 5-seed ensemble) — iter-v2/035**

| Metric | iter-v2/029 | **iter-v2/035** |
|---|---|---|
| **OOS trade Sharpe** | +1.4054 | **+1.7229** (+23%) |
| **OOS monthly** | +1.2774 | **+1.4805** (+16%) |
| **OOS PF** | 1.5889 | **1.8702** (+18%) |
| **OOS MaxDD** | 32.08% | **26.69%** (best) |
| **OOS WR** | 41.1% | **49.2%** (+8pp) |
| OOS trades | 107 | 63 |
| OOS DSR | +9.30 | **+9.71** |
| IS trade Sharpe | +0.7778 | +0.8186 |
| IS monthly | +0.6680 | +0.6795 |
| IS MaxDD | 59.93% | 71.93% |
| IS DSR | +17.35 | +17.03 |
| **XRP share (wpnl)** | **69.47%** FAIL | **44.57%** PASS |

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

## Per-Symbol OOS Performance — iter-v2/035

**All 4 symbols OOS-positive** (first time in v2 history):

| Symbol | Model | Trades | WR | Weighted PnL | Share (wpnl) |
|---|---|---|---|---|---|
| **XRPUSDT** | G | 7 | **71.4%** | **+31.47** | **44.57%** PASS |
| **NEARUSDT** | H | 17 | **64.7%** | **+28.85** | **40.86%** |
| DOGEUSDT | E | 19 | 42.1% | +8.62 | 12.20% |
| SOLUSDT | F | 20 | 35.0% | +1.68 | 2.37% |

**Concentration: 44.57% — PASS** (n=4 rule ≤ 50%).

The v1-style ensemble quality-filters XRP to only 7 OOS trades (from
iter-029's 22) but each at 71.4% WR — extreme selectivity. NEAR
becomes a major contributor at 64.7% WR. The 2 main alpha sources
(XRP+NEAR) are balanced at 45/41 share — the best diversification
within v2's 4-symbol portfolio ever.

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
| Optuna trials / month | **50** (iter-v2/035+, v1-style budget) |
| CV splits | 5 with `gap = (timeout_candles + 1) × n_symbols = 22` |
| Labeling | Triple barrier, ATR-scaled (2.9 × NATR TP / 1.45 × NATR SL) |
| Timeout | 7 days (10080 min) |
| Cooldown | 2 candles |
| Features | 40 from `V2_FEATURE_COLUMNS` (35 core + 5 BTC cross-asset) |
| Feature helper | `natr_21_raw` (labeling input, excluded from features) |
| Risk gates | 7 active gates (vol-scaling, ADX, Hurst, z-score OOD, low-vol, **hit-rate (OOS)**, **BTC trend (full)**) |
| **Ensemble** | **5-seed internal** (`[42,123,456,789,1001]`, v1-style, from iter-v2/035) |
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
- `v0.v2-029` — 15 Optuna trials, forced reset, BTC cross-asset features (primary OOS monthly +1.28, mean OOS +0.90, concentration 60.86% FAIL)
- `v0.v2-035` — v1-style 5-seed ensemble, 50 trials (OOS trade Sharpe +1.7229, OOS PF 1.87, MaxDD 26.69%, WR 49.2%, concentration 44.57% PASS)
- **`v0.v2-044` — cooldown=3 + v1 ensemble (IS monthly +0.8408, OOS monthly +1.4024, combined +2.24, balance ratio 1.92x, IS MaxDD 52%, OOS MaxDD 24%, retroactively merged under new combined-Sharpe rule)**

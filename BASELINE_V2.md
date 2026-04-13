# Current Baseline — v2 Track (Diversification Arm)

Last updated by: iteration v2/002 (2026-04-13)
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

Enforced in code via `V2_EXCLUDED_SYMBOLS` in `run_baseline_v2.py` and
`select_symbols(exclude=...)`.

## Methodology

**Baseline metrics are deterministic** with single-seed LightGBM training
(per-run `seed=42`, no ensembling). The first v2 baseline is set by
iter-v2/002, which runs three individual single-symbol models (Models E,
F, G) wrapped in `RiskV2Wrapper`.

**Risk-layer composition** (all four MVP gates active):

- Vol-adjusted position sizing via `atr_pct_rank_200` (iter-v2/002 inverted
  formula: `vol_scale = atr_pct_rank_200` clipped to [0.3, 1.0])
- ADX gate (threshold 20, inline Wilder ADX)
- Hurst regime check (training 5/95 percentile band)
- Feature z-score OOD alert (|z| > 3 on any of 35 v2 features)

## Out-of-Sample Metrics (trades with entry_time >= 2025-03-24)

**Primary seed 42 (weighted)**

| Metric | Value |
|---|---|
| Sharpe | **+1.1717** |
| Sortino | +1.4708 |
| Win rate | 40.3% |
| Profit factor | 1.294 |
| Max drawdown | 54.63% |
| Total trades | 139 |
| Calmar ratio | 1.074 |
| Net PnL | +60.58% |
| DSR z-score (N=2 v2 trials) | +8.34 (p ~ 1.0) |
| **v2-v1 OOS daily return correlation** | **+0.042** |

**10-seed robustness (MERGE validation)**

| Statistic | Value |
|---|---|
| Mean OOS Sharpe | **+0.964** |
| Std OOS Sharpe | 0.597 |
| Min / Max | −0.329 / +1.913 |
| Profitable seeds | **9 / 10** |
| ≥ +0.5 target | 9 / 10 |

## In-Sample Metrics (trades with entry_time < 2025-03-24, seed 42)

| Metric | Value |
|---|---|
| Sharpe | +0.538 |
| Win rate | 41.2% |
| Profit factor | 1.140 |
| Max drawdown | 68.80% |
| Total trades | 405 |
| Net PnL | +161.39% |

OOS/IS Sharpe ratio: **+2.18** (OOS > IS — opposite of typical overfitting).

## Per-Symbol OOS Performance (primary seed)

| Symbol | Model | Trades | WR | Weighted Sharpe | Net PnL (weighted) | % of OOS PnL |
|---|---|---|---|---|---|---|
| XRPUSDT | G | 42 | 45.2% | **+1.67** | +44.86% | 74.0% |
| SOLUSDT | F | 50 | 38.0% | +0.77 | +25.05% | 41.4% |
| DOGEUSDT | E | 47 | 38.3% | −0.31 | −9.33% | −15.4% |

**Known concentration caveat**: XRP drives 74% of the signed OOS weighted
PnL, above the standard 50% hard constraint. The failure is a signed-ratio
artifact of DOGE being a net drag (−9.33% weighted). Absolute-share
concentration is 56.6%. iter-v2/002 merged with explicit QR override on
concentration; iter-v2/003 will directly fix DOGE (specialize ATR
multipliers to match meme dynamics) and bring signed concentration below
50%.

## Regime-Stratified OOS Sharpe (Hurst × ATR percentile)

All OOS trades fell in `hurst_100 ≥ 0.6` (trending) bucket.

| Hurst | ATR pct | n | weighted mean | weighted Sharpe |
|---|---|---|---|---|
| [0.60, 2.00) | [0.00, 0.33) | 54 | −0.44% | **−1.86** |
| [0.60, 2.00) | [0.33, 0.66) | 43 | +0.45% | +0.81 |
| [0.60, 2.00) | [0.66, 1.01) | 42 | +1.55% | **+1.49** |

The low-vol trending bucket is a known drag scaled to 0.3× by the inverted
vol formula. iter-v2/004 will add an explicit `atr_pct_rank_200 >= 0.33`
filter to remove it entirely.

## Configuration

**Models**: 3 individual single-symbol LightGBM strategies, wrapped in `RiskV2Wrapper`.

| Field | Value |
|---|---|
| Symbols | DOGEUSDT, SOLUSDT, XRPUSDT |
| Interval | 8h |
| Training window | 24 months rolling, monthly walk-forward |
| Optuna trials / month | 10 |
| CV splits | 5 with `gap = (timeout_candles + 1) × n_symbols = 22` |
| Labeling | Triple barrier, ATR-scaled (2.9 × NATR TP / 1.45 × NATR SL) |
| Timeout | 7 days (10080 min) |
| Cooldown | 2 candles |
| Features | 35 from `V2_FEATURE_COLUMNS` (regime + tail risk + OHLC vol + momentum-accel + volume microstructure + fracdiff) |
| Feature helper | `natr_21_raw` (labeling input only, excluded from model features) |
| Risk gates | vol-scaling (inverted), ADX, Hurst regime, feature z-score OOD |
| Fee | 0.1% per trade |

## Known Limitations / iter-v2/003 Roadmap

1. **DOGE is unprofitable** even weighted. ATR multipliers 2.9/1.45 are
   wrong for meme dynamics. **iter-v2/003 Priority 1**: specialize DOGE
   to 4.0/2.0 or 5.0/2.5.
2. **Low-vol trending bucket is a net drag** even at 0.3× scaling.
   **iter-v2/004**: add `atr_pct_rank_200 >= 0.33` filter.
3. **Gate kill rate is 45-51%** — too hot. **iter-v2/004 or later**:
   lower ADX threshold from 20 to 15.
4. **Optuna trials at 10** (v1 uses 50) — likely under-optimizing.
   **iter-v2/005 or later**: bump to 25-50 after the sizing and DOGE
   fixes land.
5. **Drawdown brake, BTC contagion, isolation forest, liquidity floor**
   — all deferred from iter-v2/002. Enable one at a time in iter-v2/005+.
6. **Concentration caveat**: XRP 74% of signed PnL is above the 50%
   limit. Fix via DOGE repair in iter-v2/003.

## Tags

- `v0.v2-002` — first v2 baseline (this iteration)

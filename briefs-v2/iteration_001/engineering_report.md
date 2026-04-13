# Iteration v2/001 Engineering Report

**Type**: EXPLORATION (new feature set + new universe + new risk layer)
**Role**: QE
**Date**: 2026-04-13
**Branch**: `iteration-v2/001` on `quant-research`
**Decision (from Phase 7)**: **NO-MERGE (EARLY STOP)**

## Run Summary

| Item | Value |
|---|---|
| Models run | 3 (E=DOGEUSDT, F=SOLUSDT, G=XRPUSDT) |
| Architecture | Individual single-symbol LightGBM, 24-month walk-forward |
| Seeds | 1 (seed=42 — first-seed rule triggered early stop) |
| Optuna trials/month | 10 |
| Feature set | 35 features from `features_v2` (V2_FEATURE_COLUMNS) |
| ATR labeling | `natr_21_raw` column, TP=2.9×NATR, SL=1.45×NATR |
| Risk layer | `RiskV2Wrapper` with 4 MVP gates enabled |
| Backtest wall-clock | 242 s (78 + 74 + 90 s per model) |
| Feature gen wall-clock | 78 s for all 28 candidates |
| Output dir | `reports-v2/iteration_v2-001/` |

## Results (first seed, seed=42)

### Aggregate — `comparison.csv`

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---|---|---|
| Sharpe (weighted) | +0.400 | **−0.324** | −0.81 |
| Sortino | +0.505 | −0.372 | −0.74 |
| Max drawdown | 58.78% | 49.82% | 0.85 |
| Win rate | 41.2% | 40.3% | 0.98 |
| Profit factor | 1.09 | **0.934** | 0.86 |
| Total trades | 405 | 139 | 0.34 |
| Calmar | 1.06 | 0.32 | 0.30 |
| Net PnL (weighted) | +62.33% | **−15.91%** | — |

### Unweighted aggregate (critical — see §Diagnosis)

Computed directly from `net_pnl_pct` on the same trades, ignoring the risk
wrapper's `weight_factor` scaling:

| Metric | In-Sample | Out-of-Sample |
|---|---|---|
| Sharpe (raw) | **+1.042** | **+0.479** |
| DSR z-score | +26.35 | +6.73 |
| DSR p-value | ~1.0 | ~1.0 |
| Net PnL (raw) | +161.39% | +39.18% |
| IS/OOS Sharpe ratio | — | **0.460** |

Raw OOS Sharpe is just below the +0.5 success criterion. The weight-scaling
layer is what makes the aggregate weighted Sharpe negative.

### Per-symbol OOS (raw net_pnl_pct)

| Symbol | n | WR | TP rate | SL rate | Raw Sharpe | Raw net PnL | Weighted net PnL |
|---|---|---|---|---|---|---|---|
| DOGEUSDT | 47 | 38.3% | 19% | 60% | **−0.504** | −24.02% | −15.63% |
| SOLUSDT | 50 | 38.0% | 28% | 56% | **+0.491** | +25.65% | +6.37% |
| XRPUSDT | 42 | 45.2% | 26% | 55% | **+0.889** | +37.56% | **−6.65%** (sign flipped) |

### Per-regime OOS (hurst_100 × atr_pct_rank_200, raw net_pnl_pct)

All OOS trades fell in the trending Hurst bucket (`hurst_100 ≥ 0.6`). Split
by ATR percentile:

| Hurst bucket | ATR pct bucket | n | mean | std | Sharpe |
|---|---|---|---|---|---|
| [0.60,2.00) | [0.00,0.33) | 54 | **−1.45%** | 5.77 | **−1.85** |
| [0.60,2.00) | [0.33,0.66) | 43 | +1.01% | 7.05 | +0.94 |
| [0.60,2.00) | [0.66,1.01) | 42 | **+1.77%** | 7.90 | **+1.45** |

All positive edge concentrates in the mid-to-high ATR percentile buckets.
The low-ATR bucket is the entire source of the OOS drag.

### Risk-layer gate statistics (across all 3 models, seed=42)

| Symbol | Signals seen | Killed by z-score | Killed by Hurst | Killed by ADX | Combined kill rate | Mean vol_scale |
|---|---|---|---|---|---|---|
| DOGEUSDT | 2,560 | 286 (11.2%) | 146 (5.7%) | 723 (28.2%) | **45.1%** | 0.620 |
| SOLUSDT | 2,515 | 400 (15.9%) | 193 (7.7%) | 596 (23.7%) | **47.3%** | 0.543 |
| XRPUSDT | 2,532 | 340 (13.4%) | 235 (9.3%) | 709 (28.0%) | **50.7%** | 0.585 |

Combined kill rates are 45-51% — **far above** the 10-30% target band
specified in the research brief §6.2. The model is starved of signal.

## Hard Constraints (iter-v2/001 relaxed criteria)

| Constraint | Threshold | Actual (weighted) | Pass? |
|---|---|---|---|
| OOS Sharpe > +0.5 | +0.5 | **−0.324** | **FAIL** |
| ≥7/10 seeds profitable | ≥7/10 | 0/1 (first-seed stop) | **FAIL** |
| OOS trades ≥ 50 | 50 | 139 | PASS |
| Profit factor > 1.1 | 1.1 | **0.934** | **FAIL** |
| No single symbol > 50% of OOS PnL | — | XRP at 96% / DOGE at −61% | Technically fails (concentrated, one loss-maker, one profit-driver) |
| DSR > −0.5 | −0.5 | **−3.51** (weighted) / +6.73 (raw) | **FAIL on weighted** |
| v2-v1 OOS correlation < 0.80 | < 0.80 | **+0.011** | **PASS (strongly)** |
| IS/OOS Sharpe ratio > 0.5 | 0.5 | −0.81 (weighted) / 0.46 (raw) | **FAIL** |

Primary constraint (OOS Sharpe weighted) fails. First-seed early-stop rule
is triggered (`OOS Sharpe < 0 AND OOS PF < 1.0`). 10-seed validation is
NOT run per the Fail Fast protocol.

## Diagnosis

### 1. The vol-adjusted sizing is sign-inverted for this strategy

The `RiskV2Wrapper` computes `vol_scale = 1 - atr_pct_rank_200` clipped to
`[0.3, 1.0]`. This reduces position size when current ATR is high and
increases it when ATR is low. On paper that's classic vol-targeting.

But this strategy's OOS edge is **entirely in the high-ATR buckets**
(Sharpe +0.94 at `atr_pct_rank ∈ [0.33, 0.66)`, +1.45 at `[0.66, 1.01)`).
The low-ATR bucket is `−1.85` Sharpe. The wrapper therefore:

- Shrinks winning trades (high-ATR) to ~0.3× of their raw size
- Keeps losing trades (low-ATR) at ~1.0× of their raw size

Per-symbol, the effect is severe: XRP's raw sum is +37.56% but the weighted
sum is **−6.65%** — the sign literally flipped. SOL's raw sum is +25.65%
but the weighted sum is +6.37% (75% of the edge destroyed). DOGE is the
only model where the scaling *reduces* a loss, because DOGE's losses skew
to slightly higher-vol bars where `vol_scale` is smaller.

This is not a calibration issue — the sizing direction is fundamentally
wrong for a momentum/trending strategy that wants exposure when volatility
spikes. Either disable vol-scaling or flip the sign to `vol_scale = atr_pct_rank`.

### 2. The gate cascade is over-aggressive

Combined kill rates of 45-51% put the model in signal starvation. Looking
at the breakdown:

- **ADX gate fires 24-28%** — the `adx_threshold=20` is triggered in ~1/4
  of bars. The brief predicted 15-25% based on `<20` fraction for BTC; the
  alts are bouncier.
- **Feature z-score OOD alert fires 11-16%** — this is at the high end
  even though `|z| > 3` is a permissive threshold. Because there are 35
  features, the ANY-one-exceeds rate compounds; an IS window that never
  saw a particular rare combination is easy to trigger on.
- **Hurst regime check fires 6-9%** — on target (≈10% by construction of
  the 5/95 percentile band).

A 50% combined kill rate plus a 60% sizing reduction on the survivors
leaves very little signal for the model to translate into PnL.

### 3. No mean-reverting regime in the OOS window

Every single OOS trade fell in `hurst_100 ≥ 0.6` (trending). The Hurst
regime check, the z-score OOD alert's tail sensitivity, and the ADX gate
are all conditioned on the training window covering a diverse regime mix
— but 2025-03 to 2025-12 OOS turned out to be a monotonically trending
regime for these 3 symbols. The Hurst gate almost never fired.

### 4. DOGE is the weakest of the 3 picks

Even raw (unweighted), DOGE produced OOS Sharpe −0.50. Its 60% SL rate is
the highest of the 3 (SOL 56%, XRP 55%) — it gets stopped out more often.
The meme pick's dynamics (high idiosyncratic vol, pump/dump behavior) are
less well-served by the 2.9×/1.45× ATR barrier ratios, which were inherited
from v1's Model A (BTC+ETH) and never tuned for meme coins.

### 5. Good news hidden in the bad

- **Raw unweighted OOS Sharpe is +0.479** — just below the +0.5 success
  bar. The strategy has real edge underneath the sizing disaster.
- **v2-v1 OOS correlation is +0.011** — effectively zero. The whole reason
  v2 exists (diversification from v1) works perfectly: v2's return stream
  is genuinely orthogonal to v1's BTC+ETH+LINK+BNB portfolio.
- **IS/OOS Sharpe ratio (raw) is 0.46** — close enough to 0.5 that the
  researcher is not obviously overfitting IS, especially at N=1 multiple-
  testing correction.
- **Per-regime OOS Sharpe of +1.45 in the high-vol bucket** — there is a
  clear, exploitable edge in 42 OOS trades. The problem is what to do with
  the 54 trades in the low-vol bucket that lose 1.45% each on average.

## Label Leakage Audit

- CV gap formula: `(timeout_candles + 1) × n_symbols = (10080 / 480 + 1) × 1 = 22` rows
- TimeSeriesSplit with gap=22: verified per the `LightGbmStrategy.optimize` path
- Walk-forward monthly splits: each monthly model trains only on prior-month klines; verified by file timestamp ordering
- Feature isolation audit: `grep -r "from crypto_trade.features " src/crypto_trade/features_v2/` returned empty ✓
- Symbol exclusion audit: `assert set(cfg.symbols).isdisjoint(V2_EXCLUDED_SYMBOLS)` passes for all 3 models ✓

No leakage detected.

## Artifacts

- `reports-v2/iteration_v2-001/comparison.csv`
- `reports-v2/iteration_v2-001/in_sample/{quantstats.html, trades.csv, per_symbol.csv, per_regime.csv, per_regime_v2.csv, daily_pnl.csv, monthly_pnl.csv}`
- `reports-v2/iteration_v2-001/out_of_sample/{..., per_regime_v2.csv}`
- `reports-v2/iteration_v2-001/dsr.json` (DSR on IS/OOS raw and OOS weighted)

## Conclusion

iter-v2/001 ships the full v2 infrastructure (features, risk layer, runner,
reports, DSR, regime-stratified Sharpe). Weighted OOS Sharpe is **−0.32**,
fails the relaxed iter-v2/001 success criteria, and triggers the first-seed
early-stop rule. 10-seed MERGE validation is **not** run.

Decision: **NO-MERGE (EARLY STOP)**. The underlying strategy has real
OOS edge (raw Sharpe +0.48, DSR p≈1, v2-v1 OOS correlation 0.011). The
`RiskV2Wrapper`'s vol-adjusted sizing destroys that edge by
shrinking winning high-vol trades and fully sizing losing low-vol trades.
iter-v2/002 has two concrete, falsifiable corrections (see diary Next
Iteration Ideas).

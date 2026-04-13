# Current Baseline — v2 Track (Diversification Arm)

Last updated by: (not yet merged — awaiting iter-v2/001)
OOS cutoff date: 2025-03-24 (fixed, shared with v1, never changes)

## Purpose

v2 is the diversification arm of the crypto-trade strategy. Its goal is to cover
market exposure **outside** v1's baseline symbols (BTC, ETH, LINK, BNB) so that
the eventual combined portfolio (v1 + v2) has lower correlation, better tail
behavior, and higher risk-adjusted returns than either track alone.

v2 is iterated on the `quant-research` branch. v1 stays on `main`.

## Forbidden Symbols

v2 iterations MUST exclude the following symbols (they belong to v1):

| Symbol | v1 Role | v2 Allowed? |
|---|---|---|
| BTCUSDT | Model A | No |
| ETHUSDT | Model A | No |
| LINKUSDT | Model C | No |
| BNBUSDT | Model D | No |

Enforced in code via the constant `V2_EXCLUDED_SYMBOLS` in `run_baseline_v2.py`
and passed to `select_symbols(exclude=V2_EXCLUDED_SYMBOLS)`.

## Out-of-Sample Metrics

_No metrics yet — first baseline will be written when iter-v2/001 merges._

## In-Sample Metrics

_No metrics yet — first baseline will be written when iter-v2/001 merges._

## Per-Symbol OOS Performance

_No metrics yet._

## Position Sizing

_Will inherit v1's per-symbol vol targeting unless iter-v2/001 changes it:
target_vol=0.3, lookback_days=45, min_scale=0.33, max_scale=2.0._

## Risk Management Layer

v2 wraps each model in a `RiskV2Wrapper` (see `src/crypto_trade/strategies/ml/risk_v2.py`).
MVP gates enabled in iter-v2/001:

- Volatility-adjusted position sizing (scale inversely with ATR percentile)
- ADX gate (kill signal when ADX < threshold)
- Hurst regime check (kill when current Hurst outside training 5/95 percentile)
- Feature z-score OOD alert (kill when any feature |z| > 3 vs training stats)

Deferred to iter-v2/002-003: drawdown brake, BTC contagion circuit breaker,
isolation forest anomaly scoring, liquidity floor.

## Strategy Summary

_Will be written when iter-v2/001 merges. Expected shape: 3 individual models
(E, F, G) on hand-picked diversification symbols, 35 features from the v2
catalog, 10-seed ensemble, 24-month training window, ATR labeling, monthly
walk-forward._

## Notes

This file is the v2 analogue of `BASELINE.md`. It tracks only v2 iterations.
v1's baseline stays in `BASELINE.md` on `main`. The eventual combined-portfolio
runner (not yet created) will load both.

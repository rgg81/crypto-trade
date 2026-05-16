# Engineering Report — iter-v3/036

## Status: READY-FOR-CRITIC

Wall-clock 0.33h (20 min). NEGATIVE — TRX vol_adj_autocorr hurt TRX (+29.24 → +14.08; -15 swing).

## Headline Metrics

| Metric | Value | vs iter-v3/035 anchor (-0.1023/+2.8521) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | -0.2199 | Δ -0.12 |
| OOS monthly Sharpe | +2.3366 | Δ -0.52 |
| Bundle OOS trades | 127 | +4 |
| OOS MaxDD | 35.13% | +6.3pp worse |

## Per-Symbol OOS

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/035 |
|--------|--------------|--------|-----|----------------|
| BCH | +48.73 | 32 | 50.0% | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | bit-identical |
| **TRX** | **+14.08** | 50 | **42.0%** | **-15.16 swing (was +29.24 / 52.2%)** |
| LDO | +3.98 | 20 | 35.0% | bit-identical |

vol_adj_autocorr added MORE TRX trades (50 vs 46) at LOWER WR (42% vs 52%) — same fail mode as iter-v3/026 universal application.

## Verdict: EXPLORATION-NEGATIVE

vol_adj_autocorr is INERT/HARMFUL for v3 architecture both universally (iter-v3/026) and per-symbol (iter-v3/036). Feature is closed.

iter-v3/035 (BCH-only fracdiff) remains the best result. Bundle for iter-v3/039 CONFIRMATION = iter-v3/035 config.

## Recommendations

iter-v3/037: REVERT TRX vol_adj_autocorr + ADD LDO-only cross_asset_divergence_norm.

Rationale:
- LDO uniquely uses btc_ret_14d at rank 6 (BCH/TRX rank 14, ALGO ?) — has BTC-coupling signal
- cross_asset_divergence_norm = (sym_ret_7d - btc_ret_14d) / (vwap_dev_20 + 1e-6) captures relative-strength normalized
- iter-v3/027 universal failure of cross_asset_divergence; per-symbol LDO might work
- LDO at +3.98 OOS has improvement room

Status: READY-FOR-CRITIC.

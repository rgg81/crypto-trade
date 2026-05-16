# iter-v3/014 — ADX threshold (20 → 25) counterfactual synthesis

Per Critic FINAL Recommendation 1 of iter-v3/013 review (SHA `1ee0213`): the SEVENTH EXPLORATION axis is the ADX threshold gate. Currently 20.0 in `RiskV2Config`; this iteration tightens to 25.0 (only allow trades when trend strength is high). ADX threshold is structurally orthogonal to all 5 prior axes (features × 2, labeling × 1, gate-zscore × 1, gate-btc-trend × 1, universe × 1) and NOT subject to mechanical-accretion artifact: changing the ADX gate DOES change behavior at the trade-roster level for all 3 retained symbols (BCH+LDO+TRX inherited from iter-v3/013).

## ADX-bucket distribution at iter-v3/013 trade entry candles

Each iter-v3/013 trade is annotated with the 14-period Wilder ADX at the candle whose `open_time` matches the trade's entry `open_time` (mirroring the runtime `RiskV2Wrapper` ADX lookup). Trades are then bucketed by ADX:
- `<20_GHOST`: would not have entered under the iter-v3/013 gate (should be 0 — sanity check).
- `[20,25)_KILL`: killed by tighter ADX>=25; the new threshold's additional kill set.
- `>=25_KEEP`: survives the tighter threshold.

### IS (iter-v3/013 in_sample, total 209 trades)

| slice   | bucket       |   n_trades |   n_wins |   win_rate_pct |   weighted_pnl_total |   share_of_slice_pct |
|:--------|:-------------|-----------:|---------:|---------------:|---------------------:|---------------------:|
| IS      | >=25_KEEP    |        139 |       58 |          41.73 |              67.304  |                85.42 |
| IS      | [20,25)_KILL |         70 |       26 |          37.14 |              11.4916 |                14.58 |

### OOS (iter-v3/013 out_of_sample, total 85 trades)

| slice   | bucket       |   n_trades |   n_wins |   win_rate_pct |   weighted_pnl_total |   share_of_slice_pct |
|:--------|:-------------|-----------:|---------:|---------------:|---------------------:|---------------------:|
| OOS     | >=25_KEEP    |         55 |       25 |          45.45 |              23.8216 |                38.52 |
| OOS     | [20,25)_KILL |         30 |       15 |          50    |              38.0276 |                61.48 |

## Counterfactual + falsifier

- IS [20,25) kill bucket: **70 trades** (**33.5%** of 209; weighted_pnl_total = **+11.49** removed).
- IS counterfactual_n_trades = 209 − 70 = **139**.
- IS saturation falsifier_threshold = ceil(1.2 × 139) = **167** — if observed iter-v3/014 IS trades > this threshold, the ADX axis did not propagate (per `feedback_axis_saturation_predictor.md`).
- OOS [20,25) kill bucket: **30 trades** (**35.3%** of 85; weighted_pnl_total = **+38.03** removed). Informational under EXPLORATION.
- OOS counterfactual_n_trades = 85 − 30 = **55**.
- OOS saturation falsifier_threshold (informational) = ceil(1.2 × 55) = **66**.

## Direction summary

Tightening ADX from 20 to 25 is a more selective trend filter — only candles with stronger directional movement pass through. The counterfactual estimates the upper bound of additional kills (some [20,25) trades may have been killed upstream by other gates, so the realized iter-v3/014 kill set may be smaller). Whether the IS Sharpe improves depends on the per-trade economics of the killed bucket: if [20,25) trades were systematically losing or noisy, killing them improves Sharpe; if they were a representative sample, killing them merely shrinks the trade roster without improving edge. Brief Section 4 will commit a predicted Sharpe band [+0.50, +1.30] (iter-v3/013's +1.01 ±0.30) and a falsifier on the IS roster size.

# iter-v3/013 — Drop-MKR counterfactual synthesis

Per-symbol-diagnostic counterfactual for the SIXTH EXPLORATION under the v3 cadence discipline. Per `feedback_mkr_threshold_compression.md` (FIRED at iter-v3/012, 5th consecutive MKR OOS-negative trajectory): iter-v3/013 mandatorily varies along the UNIVERSE axis by dropping MKR. This counterfactual estimates the directional effect by removing MKR rows from iter-v3/012's trade roster (286 IS, 101 OOS) and recomputing the weighted-PnL aggregates without re-running Optuna or re-deriving seeds. The realized iter-v3/013 run will diverge from these counterfactual numbers (Optuna re-optimizes on a 3-symbol universe, ensemble seed determinism shifts because n_symbols affects gap/embargo, risk-gate distributions reshape against a 3-symbol portfolio context), but the DIRECTION of the effect is informative.

## IS counterfactual (2022-09-24 → 2025-03-23)

- iter-v3/012 IS roster: 286 trades, 38.46% WR, weighted_pnl_total = 73.42, approx monthly Sharpe = 0.8096.
- IS without MKR: 209 trades (−77 MKR trades dropped), 40.19% WR, weighted_pnl_total = 78.80, approx monthly Sharpe = 1.0088.
- IS counterfactual ΔSharpe = **+0.1992** (drop-MKR isolates a non-MKR portfolio).
- IS top symbol shifts: BCHUSDT (72.82%) → BCHUSDT (67.85%).

## OOS counterfactual (2025-03-24 onwards)

- iter-v3/012 OOS roster: 101 trades, 43.56% WR, weighted_pnl_total = 46.36, approx monthly Sharpe = 1.5914.
- OOS without MKR: 85 trades (−16 MKR trades dropped), 47.06% WR, weighted_pnl_total = 61.85, approx monthly Sharpe = 2.6970.
- OOS counterfactual ΔSharpe = **+1.1056**.
- OOS top symbol shifts: LDOUSDT (87.57%) → LDOUSDT (65.65%).

## Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

- Predicted IS trade count for iter-v3/013: ~209 trades (lower bound; iter-v3/012's 286 minus the 77 MKR rows). Realized may diverge ±20% due to Optuna re-optimization on a 3-symbol universe.
- Predicted OOS trade count: ~85 trades (iter-v3/012's 101 minus the 16 MKR rows).
- Falsifier (axis-saturation failure mode analog to iter-v3/012's trade-roster identity bit-identity): if observed iter-v3/013 IS trade count > 240 (i.e., the MKR drop did not propagate to the trained model's prediction surface), the universe-axis variation did not take effect.

## Direction summary

MKR's iter-v3/012 weighted_pnl contribution was negative in BOTH windows: IS −15.49 weighted_pnl_total (−24% of full IS PnL) at 25.97% WR; OOS −15.49 weighted_pnl_total (a −33.4% drag on OOS PnL) at 25.0% WR. Counterfactually removing MKR is **strictly accretive to weighted_pnl_total** in both windows. The Sharpe deltas may be favorable, neutral, or adverse depending on whether MKR's PnL volatility was contributing to the denominator in a way that offsets its negative numerator contribution — the counterfactual numbers above are the calibration anchor for brief Section 4's predicted band. NO new IS evidence is produced — this is a counterfactual on existing iter-v3/012 trades. The iter-v3/013 backtest is the actual axis test.

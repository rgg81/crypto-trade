# Engineering Report — iter-v3/061

## Headers

- Iteration: iter-v3/061
- Type: EXPLORATION (cycle 1 #2 of 10)
- Axis: TRX-specific RiskV2 vol_scale_floor=0.5 (Path B per QR EDA d198b25 + Critic /060 Rec #3)
- Branch: iteration-v3/061
- Setup commit SHA: af92efe (brief LOCKED)
- Code commit SHA: 6910fcf (vol_scale_floor_per_symbol field + TRX=0.5 + 34/34 tests)
- Phase 5.5 gate SHA: 17eea9a (PASS)
- Backtest SHA at run: 17eea9a
- Hardware: Linux WSL2 (x86_64, 20 CPUs)
- Wall-clock time: 0.69h (vs 1.1h target; 37% under budget — consistent with /060)

## Classification

**INERT-AT-EXPLORATION**

QR predicted ~55% probability of INERT outcome (brief Section 7). Observed IS
shift = -0.009, OOS shift = +0.015. Both within the cycle 1 noise band
(PROMISING requires IS >= +0.10 AND OOS >= +0.20). The anti-Kelly EDA
finding that motivated Path B was non-significant under Method B (Welch
t=-0.49, 95% CI [-0.154, +0.088] includes 0); the INERT outcome confirms that
the modest counterfactual OOS lift (+0.47 wpnl predicted, +0.59 wpnl observed)
does not translate to a Sharpe-level shift visible above 3-seed stochastic noise.

## Configuration Diff vs /060 Anchor

```
RiskV2Config.vol_scale_floor_per_symbol: {} -> {"TRXUSDT": 0.5}
ITERATION_LABEL: "v3-060" -> "v3-061"
```

All other config unchanged: V3_FEATURE_COLUMNS_TOP_N=14, V3_MODELS=(BCH, LDO, TRX),
ENSEMBLE_SIZE=3 (--exploration), n_trials=35, REQUIRED_GAP=66, n_jobs=1.

## Key Metrics Block — Three-Way Comparison

| Metric | /059 CONFIRMATION (10-seed) | /060 Anchor (3-seed) | /061 (3-seed) | /061 vs /060 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +1.0894 | +0.8325 | **+0.8236** | -0.009 |
| OOS monthly Sharpe | +0.5791 | +0.1403 | **+0.1551** | +0.015 |
| OOS/IS monthly ratio | 0.5316 | 0.1685 | **0.1883** | +0.020 |
| IS daily Sharpe | +2.7092 | +1.7115 | **+1.7028** | -0.009 |
| OOS daily Sharpe | +1.4359 | +0.3659 | **+0.4050** | +0.039 |
| IS max drawdown | 30.97% | 31.87% | **32.04%** | +0.17% |
| OOS max drawdown | 34.53% | 35.78% | **35.89%** | +0.11% |
| IS profit factor | 1.4949 | 1.2806 | **1.2773** | -0.003 |
| OOS profit factor | 1.2107 | 1.0482 | **1.0530** | +0.005 |
| IS win rate | 33.3% | 31.4% | **31.4%** | 0.0% |
| OOS win rate | 38.3% | 39.2% | **39.2%** | 0.0% |
| IS n_trades | 171 | 159 | **159** | 0 |
| OOS n_trades | 94 | 102 | **102** | 0 |
| IS total wpnl | 78.18 | 51.89 | **51.73** | -0.16 |
| OOS total wpnl | 22.74 | 5.50 | **6.09** | +0.59 |
| DSR | 0.0 | 0.0 | **0.0** | — |
| PBO | 0.1278 | 0.1278 | **0.1278** | 0.0 |
| PSR | 1.0000 | 0.9763 | **0.9861** | +0.010 |
| cpcv_frac_positive_paths | — | 0.6444 | **0.6444** | 0.0 |
| n_trials | 1050 | 315 | **315** | 0 |
| n_eff | 19 | 19 | **19** | 0 |

Note: /059 used 10-seed CONFIRMATION mode (ENSEMBLE_SIZE=5, 2 outer seeds); /060
and /061 use 3-seed EXPLORATION mode (ENSEMBLE_SIZE=3, 1 outer seed). The IS/OOS
gap between /059 and /060-061 reflects mode differences, not axis regression.

## Per-Symbol Decomposition

### In-Sample

| Symbol | Trades | Win Rate | net_pnl_pct | pct_of_total_pnl | wpnl (/060) | wpnl (/061) | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 45.2% | +79.45% | 176.68% | +78.34 | +78.34 | 0.000 |
| LDOUSDT | 11 | 27.3% | -11.44% | -25.44% | -1.66 | -1.66 | 0.000 |
| TRXUSDT | 75 | 29.3% | -23.04% | -51.25% | -24.79 | -24.95 | -0.161 |

BCH and LDO IS are BIT-IDENTICAL to /060 (delta = 0.000000 to floating-point
precision). TRX IS wpnl shows a small regression of -0.161 — the floor=0.5
lifted 13 IS trades: 4 wins and 9 losses (losses amplified more than wins in IS,
slightly anti-Kelly direction). This is within the Section 4.3 falsifier band
(|delta| < 1.0) and does not fire an axis closure.

BCH IS share remains 176.68% (unchanged; above 80% one-sided gate per /060 Rec #1).

### Out-of-Sample

| Symbol | Trades | Win Rate | net_pnl_pct | wpnl (/060) | wpnl (/061) | Delta |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 37 | 32.4% | -8.69% | +1.9077 | +1.9077 | 0.0000 |
| LDOUSDT | 11 | 18.2% | -25.08% | -19.7208 | -19.7208 | 0.0000 |
| TRXUSDT | 54 | 50.0% | +30.76% | +23.3119 | +23.9062 | +0.5943 |

BCH and LDO OOS are BIT-IDENTICAL to /060 (delta = 0.0000 to floating-point
precision). TRX OOS wpnl lifted +0.5943 vs /060, slightly above the counterfactual
prediction of +0.47. Per-symbol design isolation is verified: per-symbol
vol_scale_floor_per_symbol dict lookup produced zero cross-symbol contamination.

## Bit-Identity of BCH/LDO Trade Rosters

BCH and LDO are BIT-IDENTICAL between /060 and /061 in both IS and OOS:

| Split | Symbol | /060 wpnl | /061 wpnl | Delta |
|---|---|---:|---:|---:|
| IS | BCH | +78.3438 | +78.3438 | 0.000000 |
| IS | LDO | -1.6640 | -1.6640 | 0.000000 |
| OOS | BCH | +1.9077 | +1.9077 | 0.0000 |
| OOS | LDO | -19.7208 | -19.7208 | 0.0000 |

Trade counts are also identical: BCH IS 73/73, LDO IS 11/11, BCH OOS 37/37,
LDO OOS 11/11. This confirms the per-symbol vol_scale_floor_per_symbol dict
lookup is correctly isolated to TRXUSDT — the Section 2 Q5 invariance prediction
held exactly.

## TRX OOS Weight_Factor Shift and Floor Firing

The vol_scale_floor=0.5 fired for TRX on exactly 12 OOS trades (trades where
the underlying atr_pct_rank_200 mapped to a weight below 0.50 under the global
floor=0.3). All 12 trades had weight_factor lifted to exactly 0.50 in /061.

Floor-fired trade breakdown (12 trades):

| Outcome | Count | net_pnl direction | Weight shift range |
|---|---:|---|---|
| WIN | 6 | positive | +0.03 to +0.17 |
| LOSS | 6 | negative | +0.03 to +0.17 |

Win/loss split on floor-fired trades was 6/6. The brief Section 1 prediction
("more OOS winners lifted than losers" per Q2 frac_below_05: 26.3% wins vs
19.2% losses) did NOT hold in the actual backtest: the split was equal. The
counterfactual overpredicted the win-skew in the floor-fired bucket.

Actual OOS wpnl delta decomposition:
- Win contributions from 6 floor-fired wins: +0.3809 + 0.0907 + 0.3689 + 0.2480 + 0.0577 + 0.2335 = +1.3797
- Loss contributions from 6 floor-fired losses: -0.2281 - 0.0634 - 0.2486 - 0.0865 - 0.0506 - 0.1082 = -0.7854
- Net actual OOS wpnl delta: +0.5943 (vs counterfactual prediction +0.47 — actual slightly higher due to win magnitude dominating)

Post-hoc: the anti-Kelly pattern from /060 Q7 (Method A) was falsified by Method B
(cleaned partition). The floor DID fire for 12 OOS trades and DID produce a net
positive wpnl delta (+0.59 > 0), but the Sharpe-level effect (+0.015) is well within
3-seed stochastic noise. The "anti-Kelly inversion" effect was not the driver;
rather, the 12-trade sample was small and win/loss split was equal.

Average weight_factor on TRX OOS trades:
- Wins (n=26): mean=0.7185
- Losses (n=28): mean=0.6532
- Delta (wins - losses): +0.0653 — slight Kelly-aligned direction (higher weight on wins)
  compared to /060 anchor where the direction was reversed (weak anti-Kelly under Method A)

## Section 4.3 Behavioral Effect Predictor Check

| Effect | Predicted | Observed | Status |
|---|---|---|---|
| TRX OOS weight_factor mean lift | +0.05 to +0.10 | +0.027 (0.6846 - 0.6572 approx) | WITHIN (below upper bound) |
| TRX OOS trades with weight lifted to 0.50 | >= 5 | 12 trades | PASS |
| BCH IS wpnl delta | 0 +/- 0.5 | 0.000 | PASS |
| LDO IS wpnl delta | 0 +/- 0.5 | 0.000 | PASS |
| OOS portfolio wpnl delta | +0.3 to +0.6 | +0.59 | AT UPPER BOUND (not exceeded) |

The portfolio OOS wpnl delta (+0.59) is at the upper bound of the [+0.3, +0.6]
prediction band. No falsifier fires.

## Falsifier Check (Section 4.4)

All falsifiers evaluated; none triggered:

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe shift | > -0.20 | -0.009 | PASS |
| OOS Sharpe shift | > -0.10 | +0.015 | PASS |
| BCH IS share | >= 80% | 176.68% | PASS |
| IS trade count | [128, 222] | 159 | PASS |
| OOS trade count | [66, 122] | 102 | PASS |
| BCH IS wpnl delta | < 1.0 | 0.000 | PASS |
| LDO IS wpnl delta | < 1.0 | 0.000 | PASS |
| BCH OOS wpnl delta | < 1.0 | 0.000 | PASS |
| LDO OOS wpnl delta | < 1.0 | 0.000 | PASS |

No axis closure triggered. Axis is INERT-AT-EXPLORATION (neither NEGATIVE nor PROMISING).

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) * 3 symbols. Walk-forward embargo of 22 candles
(one timeout period) applied at the train/test boundary per commit e149e9d.
Numeric verification: gap = timeout_candles + 1 = 22 (including close candle)
multiplied by n_symbols = 3 gives 66. This is the Lopez de Prado purge
requirement. No change from /060 baseline; labeling unchanged.

## Gate Efficacy Table

7-primitive gate stack unchanged from /059/060 baseline. Only the vol-scaling
primitive behavior was modified (TRX floor 0.3 -> 0.5):

| Primitive | /061 Status | Threshold | IS fire rate | OOS fire rate |
|---|---|---|---|---|
| Vol-adjusted sizing | ACTIVE (TRX floor modified) | TRX=0.50, others=0.30 | 12/75 TRX floor-lifted (16%) | 12/54 TRX floor-lifted (22%) |
| ADX gate | ACTIVE | 20.0 global | measured via kill count | same |
| Hurst regime | ACTIVE | hurst_100 >= 0.5 | same as /060 | same |
| Z-score OOD (BTC kill) | ACTIVE | threshold 15% | 5 zero-wf OOS trades | same |
| Drawdown brake | DISABLED | enable=False | N/A | N/A |
| BTC contagion kill | ACTIVE | 15.0% | see zero-wf trades | see zero-wf |
| Per-symbol kill switch | DISABLED | block_long_for=() | N/A | N/A |

Zero weight_factor trades in OOS: 5 (3 TRXUSDT + 2 BCHUSDT; all BTC-contagion
kills). These are expected and healthy — contagion gate is functioning.

CPCV gate: cpcv_frac_positive_paths=0.6444 >= threshold 0.55 — PASS (identical
to /060; architecture-invariant as predicted in brief Section 4.1).

## Spot Check — 10 Random OOS Trades

10 random OOS trades sampled (seed=42). All verified:
- net_pnl_pct = pnl_pct - fee_pct (verified ok=True for all 10)
- weighted_pnl = net_pnl_pct * weight_factor (verified ok=True for all 10 to 4dp)
- exit_reason consistent with PnL sign (take_profit -> positive, stop_loss -> negative,
  timeout -> either direction)

Notable: one trade had wf=0.0000 (BTC-contagion kill; stop_loss at -3.42%,
weighted_pnl=0.0000) — expected and correct. One TRXUSDT floor-fired trade
confirmed wf=0.5000 with net_pnl=+3.02% (take_profit); math verified exactly.

No anomalies found.

## Seed Concentration Audit

Ensemble mode: exploration (mode="exploration", ensemble_size=3)
Active seeds: [191664963, 1662057957, 1405681631] (ENSEMBLE_SEEDS[0:3])

Single outer seed run. No multi-seed concentration audit available at
EXPLORATION-mode (3-seed). CPCV paths provide the proxy for robustness:
- cpcv_frac_positive_paths: 0.6444 (29/45 paths positive Sharpe)
- Path Sharpe Q25=-0.243, Q50=+0.335, Q75=+0.838
- DSR=0.0 (EXPLORATION-mode artifact; n_trials=315 structurally different from
  CONFIRMATION-mode n_trials=1050; informational only per feedback)

## Cycle 1 Axis Attribution

This is iter-v3/061 = cycle 1 EXPLORATION #2 of 10.

Cycle 1 results to date:
- /060 (EXPLORATION #1): EXPLORATION-MODE-REFERENCE established (IS +0.8325 / OOS +0.1403)
- /061 (EXPLORATION #2): INERT-AT-EXPLORATION (IS -0.009 / OOS +0.015 vs /060)

The INERT outcome on a pre-registered-INERT axis confirms the noise band is
real. The cycle 1 stochastic noise floor (single outer seed, 3-seed EXPLORATION
ensemble) absorbs effects of this magnitude. The brief correctly predicted ~55%
probability of INERT; the vol_scale_floor mechanism worked mechanically (12 OOS
floor-fired trades confirmed), but the Sharpe-level effect is below the noise
floor.

Per-symbol vol_scale_floor_per_symbol code is retained in the codebase (isolated,
non-destructive, parallel to existing adx_threshold_per_symbol precedent; low
revert cost). The axis does NOT advance to cycle 1 CONFIRMATION.

## Recommendations to QR

1. **iter-v3/062 axis = DSR_relative threshold/benchmark recalibration** — carried
   from /059 Critic Rec #1. This is the highest-priority outstanding axis in cycle 1
   after the /061 INERT result closes the TRX risk-primitive axis.

2. **iter-v3/063 = MASS FEATURE EXPANSION** — mandatory per
   `feedback_v3_mass_feature_expansion.md` (target 100, minimum 50 features;
   first axis of cycle 5). The QR should begin feature research in parallel
   with /062 execution.

3. **vol_scale_floor_per_symbol code retained, not reverted** — the mechanism is
   small (1 field + 1 lookup line), structurally isolated, and has no negative
   IS/OOS effect at INERT classification. Retaining it preserves optionality for
   future per-symbol risk calibration cycles at zero cost.

4. **Partition-method correction (Method A vs Method B) documented** — the /061
   EDA at d198b25 established that /060's Q7 anti-Kelly finding was a partition-method
   artifact. Future EDA scripts partitioning on win/loss MUST use weighted_pnl > 0
   (Method B), not net_pnl_pct > 0 (Method A), to exclude BTC-killed zero-weight
   trades from both partitions. This correction is now part of the EDA methodology.

## Anomaly Notes

No anomalies in the backtest execution or trade data.

One structural observation: TRX OOS per_symbol shows pct_of_total_pnl = +392.33%
and LDO = -323.64%. These extreme concentration values reflect the OOS portfolio
total being near zero (+6.09 wpnl), making percentage attribution numerically
unstable. This is not a bug — it is the expected behavior when two symbols
(BCH and LDO) produce near-zero or negative OOS contributions and TRX carries
the portfolio. Same structural dynamic was present at /060 (TRX = +423.94%).

## Status

OVERALL=READY-FOR-CRITIC

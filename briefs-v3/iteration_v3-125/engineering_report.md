# Engineering Report — iter-v3/125

## Headers
- Iteration: iter-v3/125
- Branch: iteration-v3/125
- Commit SHA: 85f413bea56c10b02ce7160935622867e0766330
- Hardware: Intel Core i9-12900HK, 58 GiB RAM
- Wall-clock time: ~1.1h (estimated; run.log not present)

## Configuration Diff vs Baseline (/121)

Single axis change — V3_MODELS tuple replacement only:

```
-    ("v3-123-BCH", "BCHUSDT"),
-    ("v3-123-LDO", "LDOUSDT"),
-    ("v3-123-TRX", "TRXUSDT"),
+    ("v3-125-ATOM", "ATOMUSDT"),
+    ("v3-125-RUNE", "RUNEUSDT"),
+    ("v3-125-UNI", "UNIUSDT"),
```

ITERATION_LABEL: "v3-124" → "v3-125". All other parameters bit-identical to /121:
- 14 V3_FEATURE_COLUMNS_TOP_N (unchanged)
- +2/-1 ATR triple-barrier K=21
- 7-gate RiskV2
- no_confirm: enable_no_confirm_exit=True, trigger_atr=0.50, k_candles=4
- REQUIRED_GAP=66 = (21+1)*3
- ENSEMBLE_SIZE=3 (EXPLORATION mode)
- n_trials=35

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.0632 | +0.1104 | 1.747 |
| daily_sharpe | +0.1677 | +0.2135 | 1.273 |
| max_drawdown | 82.97% | 36.76% | 0.443 |
| profit_factor | 1.023 | 1.025 | 1.002 |
| win_rate | 32.2% | 34.2% | 1.061 |
| n_trades | 208 | 79 | 0.380 |
| total_pnl | 8.18 | 2.89 | 0.353 |
| monthly_calmar | 0.099 | 0.079 | 0.797 |
| weighted_pnl_total | 8.18 | 2.89 | 0.353 |
| dsr | 0.000 | — | — |
| pbo | 0.106 | — | — |
| psr | 0.797 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |

vs /121 BASELINE: IS +1.3108 / OOS +0.9682. Delta: IS **−1.248**, OOS **−0.858**.

Per-symbol (IS):

| symbol | n_trades | win_rate | net_pnl_pct | pct_of_total |
|---|---:|---:|---:|---:|
| ATOMUSDT | 68 | 44.1% | +72.48 | +974% |
| UNIUSDT | 61 | 39.3% | −27.70 | −372% |
| RUNEUSDT | 79 | 30.4% | −37.34 | −502% |

Per-symbol (OOS):

| symbol | n_trades | win_rate | net_pnl_pct | pct_of_total |
|---|---:|---:|---:|---:|
| ATOMUSDT | 28 | 42.9% | +22.29 | −2152% |
| RUNEUSDT | 28 | 35.7% | +3.97 | −383% |
| UNIUSDT | 23 | 26.1% | −27.29 | +2635% |

(Concentration percentages invert because aggregate OOS PnL is negative; UNI is the primary drag OOS.)

comparison.csv per-symbol section (weighted_pnl basis):

| symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| ATOMUSDT | +10.40 | 28 | 39.3% | +360% |
| RUNEUSDT | +1.08 | 28 | 35.7% | +38% |
| UNIUSDT | −8.59 | 23 | 26.1% | −298% |

(Denominator sign-flip: total OOS wpnl = +2.89; UNI drags while ATOM carries. Concentration pct not meaningful when total is near-zero.)

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (outer=42 derived inner seeds: 191664963, 1662057957, 1405681631). ENSEMBLE_SIZE=3. n_trials=35. No multi-seed Pareto table at EXPLORATION. frac_positive_paths = 0.467 (FAIL at 0.55 gate). CPCV q25 Sharpe = −1.054 / q50 = −0.137 / q75 = +1.290.

## Label Leakage Audit

REQUIRED_GAP = 66 = (21+1) * 3. Runner line 1183 verifies at startup: `("REQUIRED_GAP", REQUIRED_GAP, 66)`. Verified in runner comments at lines 225-226, 1172, 1178-1183, 1313. No `min(REQUIRED_GAP, n_trades//20)` truncation (iter-v3/001 bug not present). Gap = timeout_candles+1 = 22 per-symbol, cross-symbol multiplier = 3. Correct per Lopez de Prado purge requirement.

## Falsifier Check (Section 8 pre-registration)

- **NEGATIVE-catastrophic trigger** (IS < +0.91 OR OOS < +0.67, Anchor PUBLIC): IS = +0.063 (threshold +0.91 BREACHED by −0.848), OOS = +0.110 (threshold +0.67 BREACHED by −0.560). **Both legs trigger NEGATIVE-catastrophic.**
- Falsifier band (Anchor B ADJUSTED, IS): predicted [+0.76, +1.36]; observed +0.063. Miss by −0.697 below lower bound. Band VIOLATED.
- Falsifier band (Anchor B ADJUSTED, OOS): predicted [+0.65, +1.35]; observed +0.110. Miss by −0.540 below lower bound. Band VIOLATED.
- Trade-roster overlap with /121: 0% by construction (full universe replacement; ATOM/RUNE/UNI vs BCH/LDO/TRX). Engineering integrity PASS per Section 4.4 falsifier.
- IS MaxDD = 82.97% (predicted band [20%, 50%]). Section 6.1 NEGATIVE-catastrophic concentration threshold NOT triggered by MaxDD>50%+Sharpe<0.50 gate (both conditions met), but NEGATIVE-catastrophic already filed on Sharpe grounds.
- Behavioral-effect predictor: 100% trade-roster substitution confirmed (no BCH/LDO/TRX in outputs). Saturation falsifier vacuously satisfied.

## Gate Efficacy Table

7-gate RiskV2 configuration inherited from /121; gate fire rates not separately tabulated at EXPLORATION (regime breakdown shows all trades labelled "unknown" — regime tagging not active). IS 208 trades, OOS 79 trades. Trade rate substantially below /121 baseline (IS 208 vs /121 multi-seed IS equivalent). The lower IS trade count despite 3 comparable-depth symbols suggests the 14-feature stack has poor IS fit on ATOM/RUNE/UNI — consistent with IS MaxDD 82.97%.

## IC Matrix Anomaly Check

High pairwise IC between vwap_dev_20, sym_vs_btc_ret_7d, and regime_momentum_signed_5d: IC(vwap_dev_20, regime_momentum_signed_5d) = 0.814; IC(sym_vs_btc_ret_7d, regime_momentum_signed_5d) = 0.711; IC(sym_vs_btc_ret_7d, vwap_dev_20) = 0.583. This is the same compositional identity noted at iter-v3/025 (regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5) correlates mechanically with vwap_dev_20 and btc_ret_14d terms). These IC values are UNCHANGED from prior iterations — the feature stack is identical; IC matrix is informational baseline for Critic Check 4.

## Anomaly Notes from Trade Spot-Check

10 random OOS rows verified (seed=42 draw): exit_reason values are stop_loss and take_profit — no unexpected exit_reason values. PnL math: stop_loss rows show ~−3% to −6% (consistent with ATR=1.0 SL at 8h holding). take_profit rows show +7% to +11% (consistent with ATR=2.0 TP). weight_factor values range 0.37–0.99 — non-zero, no BTC-kill artifacts. Row integrity: PASS.

Zero-trade months: IS monthly_pnl shows 2 months with 1-2 trades (2022-02: 1 trade, 2022-03: 2 trades) — sparse but not zero. OOS monthly_pnl shows 2026-03 absent (OOS ends 2026-02 based on data). No NaN Sharpe. No NaN PnL. No NaN monthly rows.

## Classification

**NEGATIVE-catastrophic.** Both IS (Δ −1.248) and OOS (Δ −0.858) breach the Section 8 NEGATIVE-catastrophic threshold (IS < +0.91, OOS < +0.67 vs PUBLIC /121 anchor). IS MaxDD 82.97% is extreme — the model extracted near-zero signal IS. This is the 4th consecutive cycle-7 NEGATIVE (after /122 NEGATIVE-INERT, /123 NEGATIVE-catastrophic, /124 NEGATIVE-catastrophic).

Failure mode match: **F3 (Sector cross-contamination / cross-cohort transfer failure)** + elements of F2 (1-symbol carrier: ATOM IS positive +72%, RUNE/UNI both IS negative). The 14-feature stack + /121 calibration were tuned on BCH/LDO/TRX distributions; ATOM/RUNE/UNI have higher per-bar return magnitudes (150-195 bps vs 85-168 bps anchor), different kurtosis structure (lower tail events), and different timeout rates (2.8-4.6% vs 3.8-6.9%). The model's IS Sharpe collapse to +0.06 with MaxDD 83% indicates systematic IS misfitting — not a signal-absence issue but an architecture-distribution mismatch. The feature stack that learned BCH's tail-event structure (high ret_kurt_50/200 importance on BCH at prior iterations) encounters a flatter distribution on RUNE/UNI and misfits. ATOM partially survives (IS +74% PnL, 44% WR) but RUNE (30% WR, −37% PnL IS) and UNI (39% WR, −28% PnL IS) both destroy capital IS, producing the headline IS MaxDD 82.97%.

Axis-CLOSE: V3_MODELS wholesale replacement ATOM/RUNE/UNI CLOSED. Cross-cohort architecture transfer from /121 BCH/LDO/TRX-calibrated stack to new symbol class without re-calibration is FALSIFIED. If any future axis tests a new universe, it must be accompanied by per-symbol feature re-calibration or gate-threshold re-tuning (separate axis per single-axis discipline).

## Status

OVERALL=READY-FOR-CRITIC

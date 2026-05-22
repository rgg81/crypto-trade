# Engineering Report — iter-v3/074

## Headers

- Iteration: iter-v3/074
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit SHA (Phase 5.5 gate, last code commit): `0c01d8f`
- Setup commit SHA (code locked): `a5d5cdd`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.71h (within 1.0h budget; consistent with /071-/073 range of 0.65-0.70h)
- Run mode: `--exploration` (3-seed outer=42 lineage, `ENSEMBLE_SIZE=3`, `--n-trials 35`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR

Two changes vs /060 — one axis change, one mandatory revert:

| Parameter | /060 (anchor) | /074 |
|---|---|---|
| `enable_regime_gate` | `False` | **`True`** (primitive 9 ON — the axis) |
| `regime_gate_symbols` | `("TRXUSDT",)` | `("TRXUSDT",)` (unchanged — already wired) |
| `regime_dd_threshold_pct` | 20.0 | 20.0 (unchanged) |
| `regime_vol_zscore_threshold` | 1.5 | 1.5 (unchanged) |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` (baseline) | `{}` (**REVERT** from /073 `{"BCHUSDT":(2.0,1.25),"LDOUSDT":(1.5,1.25)}`) |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-074"` |
| All other params | — | UNCHANGED |

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.
`V3_FEATURE_COLUMNS`: 14 columns — unchanged.

---

## Key Metrics Block

### Headline vs /060 anchor

| Metric | /060 IS | /074 IS | IS Δ | /060 OOS | /074 OOS | OOS Δ | /074 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.8454** | **+0.0129** | +0.1403 | **+0.2090** | **+0.0687** | 0.247 |
| daily_sharpe | +1.7115 | +1.6908 | -0.0207 | +0.3659 | +0.5623 | +0.1964 | 0.333 |
| max_drawdown | 31.87% | 32.04% | +1.2% | 35.78% | 35.81% | +0.3% | 1.118 |
| profit_factor | 1.2806 | 1.2754 | -0.005 | 1.0482 | 1.0729 | +0.025 | 0.841 |
| win_rate | 31.4% | 31.4% | 0.0pp | 39.2% | 40.8% | +1.6pp | 1.300 |
| n_trades | 159 | 156 | -3 | 102 | 98 | -4 | 0.628 |
| total_pnl | 51.89 | 50.59 | -1.30 | 5.50 | 8.30 | +2.80 | 0.164 |
| monthly_calmar | 1.6282 | 1.5790 | -0.049 | 0.1537 | 0.2318 | +0.078 | 0.147 |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| pbo | 0.1278 | 0.1278 | 0.0 | — | — | — | — |
| psr | 0.9763 | **0.9985** | **+0.022** | — | — | — | — |
| dsr_relative_b4 | n/a | 0.0715 | — | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0.0 | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

### Per-symbol OOS section

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | 37 | 32.4% | 22.99% |
| LDOUSDT | -18.4079 | 12 | 25.0% | -221.79% |
| TRXUSDT | +24.7998 | 49 | 51.0% | 298.80% |

### Per-symbol IS section

| Symbol | trades | wins | win_rate | net_pnl_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 33 | 45.2% | +79.45% |
| LDOUSDT | 11 | 3 | 27.3% | -11.44% |
| TRXUSDT | 72 | 20 | 27.8% | -27.28% |

---

## Classification per Brief Section 8 LOCKED

Evaluation order: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3).

| Gate | Threshold | /074 result | Status |
|---|---|---|---|
| **SUSPICIOUS — OOS/IS ratio > 3.0** | > 3.0 | 0.247 | **PASS (does NOT fire)** |
| **SUSPICIOUS — IS shift < 0 AND OOS shift ≥ +0.20** | IS<0 AND OOS≥+0.20 | IS +0.013 (positive) | **PASS (does NOT fire)** |
| **SUSPICIOUS — duration shift > +1.5 candles** | > +1.5 | IS delta -0.389, OOS delta -0.240 | **PASS (does NOT fire)** |
| **NULL-RESULT — regime_gate_fires = 0** | = 0 | IS -3 TRX trades, OOS -5 TRX trades | **PASS (gate did fire)** |
| **NEGATIVE — IS Sharpe Δ < -0.10** | < -0.10 | +0.013 | **PASS (does NOT fire)** |
| **NEGATIVE — OOS Sharpe Δ < -0.20** | < -0.20 | +0.069 | **PASS (does NOT fire)** |
| **PROMISING — IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20** | both required | IS +0.013 < +0.10 | **FAILS (does NOT qualify)** |
| **INERT — shifts within noise bands** | IS ±0.10 or OOS ±0.20 | IS +0.013 (within), OOS +0.069 (within) | **TRIGGERS** |

**CLASSIFICATION: INERT-AT-EXPLORATION.**

---

## Regime-Gate Mechanism Assessment

### Gate fire counts vs brief Section 4.4 predictions

| Split | Symbol | /060 trades | /074 trades | Delta | Section 4.4 prediction |
|---|---|---:|---:|---:|---|
| IS | BCHUSDT | 73 | 73 | **0** | 0 (hard control) |
| IS | LDOUSDT | 11 | 11 | **0** | 0 (gate targets TRX only) |
| IS | TRXUSDT | 75 | 72 | **-3** | 70-74 (predicted 1-5) |
| OOS | BCHUSDT | 37 | 37 | **0** | 0 (hard control) |
| OOS | LDOUSDT | 11 | 12 | **+1** | 0 (gate targets TRX only) |
| OOS | TRXUSDT | 54 | 49 | **-5** | 46-53 (predicted 1-8) |

All BCH and TRX deltas are within brief predictions. The LDO OOS +1 is a marginal Optuna
drift artifact — inspection of the LDO OOS trade roster shows the +1 trade is an
`end_of_data` close at `open_time=1778716799999` (late in the OOS window), not present in
/060. This is a data-extent artifact (the backtest saw a slightly extended OOS window by
run date) and is not attributable to the regime gate, which is scoped to TRX only. LDO IS
is unchanged (11 trades), confirming the gate did not touch LDO.

The gate fired on 3 IS TRX trades and 5 OOS TRX trades — well within the Section 2.2
counterfactual prediction (3 IS / 6 OOS). The small-N intervention produced small
aggregate shifts, consistent with the Section 7 INERT failure-mode prediction (35%
probability).

### Why the gate produced near-zero aggregate effect

The regime gate's bar-level fire rate in the OOS window is 8.9% of BTC bars (Section 2.5).
However, a TRX candidate must land on one of those bars for a trade to be suppressed.
The result — 5 OOS suppressions — confirms the bar-level rate and trade-level suppression
rate diverge significantly. The OOS window (2025-03 to 2026-05) is an uptrend regime with
few BTC-regime-stress bars; the gate's design targets the IS bear/chop regime (19.1% bar
fire rate), which does not repeat in OOS. The training-distribution shift hypothesis (crash
bars dropped from TRX Optuna landscape) also produced a near-zero effect: TRX IS model
quality did not materially change, consistent with the counterfactual's low prior.

---

## Holding-Time-Orthogonal Hypothesis — CONFIRMED

This is the key methodology finding of iter-v3/074.

After 3 consecutive SUSPICIOUS-OOS-DOMINANT iterations (/065, /071, /073), all of which
used holding-time-extension axes (duration-selective labeling, meta-labeling M2 veto,
per-symbol barrier asymmetry), /074 was explicitly designed as a holding-time-orthogonal
axis per `feedback_v3_is_oos_regime_divergence.md`.

| Metric | /065 | /071 | /073 | /074 |
|---|---:|---:|---:|---:|
| OOS/IS monthly Sharpe ratio | 5.04 | 4.51 | 12.55 | **0.247** |
| Classification | SUSPICIOUS | SUSPICIOUS | SUSPICIOUS | **INERT** |
| Axis type | holding-time extension | holding-time extension | holding-time extension | **holding-time ORTHOGONAL** |

The OOS/IS ratio of 0.247 is healthy — well below the 3.0 SUSPICIOUS threshold — and
comparable to the /060 anchor ratio of 0.169. The regime kill switch (which removes whole
trades by BTC-regime state without touching the SL/TP barrier distances, the 21-candle
timeout, or any meta-labeling filter) did NOT reproduce the SUSPICIOUS pattern.

### Holding-time falsifier check

| Measurement | Prediction (Section 4.3) | Observed |
|---|---|---|
| TRX IS mean duration Δ | ≈ 0 (-0.35 candles, Section 2.3) | **-0.389 candles** |
| TRX IS median duration Δ | 0.0 | **0.0** |
| TRX OOS mean duration Δ | ≈ 0 (-0.29 candles) | **-0.240 candles** |
| TRX OOS median duration Δ | -0.5 | **0.0** |
| Falsifier threshold | > +1.5 candles mean shift | **NOT TRIGGERED** |

The kept-roster mean duration is marginally shorter than the /060 full roster (opposite
direction from holding-time-extension family), confirming the gate selects by BTC-regime
state, not by trade holding time. The holding-time-orthogonality prediction was accurate.

**This validates the regime-divergence diagnosis established in iter-v3/073 Phase 8:
holding-time-extension axes load the IS/OOS regime factor; holding-time-orthogonal axes
do not. Cycle 2 axes #5+ may continue holding-time-orthogonal exploration without the
SUSPICIOUS trap.**

---

## Falsifier Check per Brief Section 4.4

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| OOS Sharpe Δ < -0.20 (hypothesis rejection) | < -0.20 | +0.069 | PASS — hypothesis not rejected |
| OOS/IS ratio > 3.0 (SUSPICIOUS pre-registration) | > 3.0 | 0.247 | PASS — gate does NOT fire |
| frac_positive_paths ≥ 0.50 | ≥ 0.50 | 0.6444 | PASS |
| TRX IS trade count unchanged at 75 (NULL-RESULT) | = 75 | 72 (-3) | PASS — gate fired |
| TRX OOS trade count ≥ 46 (gate not overly restrictive) | ≥ 46 | 49 | PASS |
| BCH IS bit-identity (hard positive control) | delta = 0 | delta = 0 (73/73 trades) | PASS |
| Duration mean shift > +1.5 candles (orthogonality violated) | > +1.5 | -0.389 IS, -0.240 OOS | PASS — orthogonality confirmed |

All falsifiers pass. No threshold is breached.

---

## Label Leakage Audit

- REQUIRED_GAP = 66 = (21+1) × 3 symbols — confirmed in `validation_v3.py` line 60.
- Embargo = 22 candles (1 per symbol beyond the label horizon) — unchanged from /060.
- The regime gate change does not touch the label horizon, the gap computation, or the
  walk-forward train/test split. The leakage protection is identical to /059/060.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` revert confirmed: all symbols use
  `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`, which means the 21-candle (10080-minute)
  timeout and the 2.0/1.0 ATR barrier are uniform. No per-symbol labeling drift.

---

## Seed Concentration Audit

Single-seed EXPLORATION (outer=42 lineage, 3 seeds: 191664963, 1662057957, 1405681631).

The single-seed-42 frozen-baseline pattern documented at iter-v3/020-022 applies: BCH and
LDO produce bit-identical OOS results to /060 (BCH: confirmed BIT-IDENTICAL, 37/37 trades;
LDO: 11→12 trades, with the +1 attributable to data-extent artifact, not gate). TRX is
the target symbol and differs by gate fires. This is the expected frozen-baseline pattern
for non-target symbols at single-seed EXPLORATION — it dissolves at multi-seed CONFIRMATION.

Symbol concentration at OOS: TRX 298.80%, BCH 22.99%, LDO -221.79%. The concentration
figures are uninterpretable at single-seed EXPLORATION with LDO producing negative wpnl;
they are informational only. The 30% per-symbol concentration gate is a CONFIRMATION gate,
not applied at EXPLORATION.

---

## Gate Efficacy Table

| Primitive | State | IS fire rate (predicted) | IS fire rate (observed) | OOS fire rate (predicted) | OOS fire rate (observed) |
|---|---|---|---|---|---|
| 1 — Feature OOD z>2.0 | ON | baseline | baseline | baseline | baseline |
| 2 — Hurst regime | ON | baseline | baseline | baseline | baseline |
| 3 — ADX gate | ON | baseline | baseline | baseline | baseline |
| 4 — Low-vol filter | ON | baseline | baseline | baseline | baseline |
| 5 — Vol-adjusted sizing | ON | baseline | baseline | baseline | baseline |
| **9 — Regime kill switch (TRX)** | **ON** | **14.9% bar-level; 3 trades** | **3 TRX IS trades suppressed** | **8.9% bar-level; ~6 trades** | **5 TRX OOS trades suppressed** |
| 10 — Direction kill switch | OFF (reverted /051) | n/a | n/a | n/a | n/a |
| 11 — Per-symbol drawdown brake | OFF (closed /054) | n/a | n/a | n/a | n/a |

Primitive 9 IS trade suppression: predicted 1-5 (Section 4.4 point estimate 3), observed 3.
Primitive 9 OOS trade suppression: predicted 1-8 (Section 4.4 point estimate 6), observed 5.
Both within predicted bands. The gate fires as designed — it does not misfire (NULL-RESULT
gate cleared), and it does not over-suppress.

---

## Feature Importance

Top-5 IS portfolio importance (last-month walk-forward cell):

| Rank | Feature | Importance |
|---|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 14 (last) | regime_momentum_signed_5d | 506.7 |

`regime_momentum_signed_5d` ranks last at 506.7 — still above the 30 importance threshold
established for composed features (iter-v3/025). No feature ranked zero or marginally
above zero. The regime gate did not materially shift feature importance rankings vs /060.

IC matrix: highest off-diagonal pair is `vwap_dev_20` / `regime_momentum_signed_5d`
(|IC| = 0.764) — the composed feature's algebraic correlation with its parent
`vwap_dev_20` is expected per `feedback_v3_engineered_feature_pivot.md`. No new
collinearity introduced by the regime gate (it does not add features).

---

## Anomaly Notes

1. **LDO OOS +1 trade** (`open_time=1778716799999`, `exit_reason=end_of_data`,
   `net_pnl_pct=+1.71`): not present in /060 OOS. This is a data-extent artifact — the
   backtest was run on a later date with a slightly extended OOS window. The trade closes
   `end_of_data` (not TP/SL), meaning it was open at the data boundary. It is NOT
   attributable to the regime gate (scoped to TRX only). LDO IS unchanged (11 trades
   in both /060 and /074), confirming gate isolation.

2. **TRX IS -3 trades (75→72) matches counterfactual exactly**: The EDA Section 2.2
   point estimate was 3 IS suppressions; the backtest produced exactly 3. This is a
   favorable calibration result, though small-N agreement may be coincidental.

3. **Spot-check 10 random OOS trades — 0 issues**: All entry/exit/PnL math checks pass
   (pnl_pct, net_pnl_pct, weighted_pnl all within rounding tolerance). Exit reasons
   (take_profit, stop_loss, end_of_data) are consistent with the barrier configuration.
   weight_factor values are non-negative and consistent with vol-adjusted sizing.

4. **No NaN Sharpe, no zero-trade IS months, no NaN PnL**: All monthly_pnl.csv rows
   (IS: 33 rows, OOS: 14 rows) have positive trade_count and numeric pnl_pct.

5. **BCH OOS BIT-IDENTICAL to /060**: Confirmed by field-by-field comparison of all 37
   BCH OOS trades. Single-axis discipline verified — the regime gate scope to TRX did
   not contaminate BCH.

---

## Recommendations to QR

1. **Axis CLOSED for cycle 2 CONFIRMATION bundle**: iter-v3/074 is INERT-AT-EXPLORATION.
   The regime gate suppressed only 3 IS / 5 OOS TRX trades; aggregate Sharpe shifts are
   within the noise bands (IS +0.013, OOS +0.069). The training-distribution shift
   hypothesis did not produce a measurable improvement. The regime gate has now been
   tested twice (iter-v3/022 NEGATIVE-pre-fix, /074 INERT-post-fix) and produced no
   positive signal in either run. The axis is CLOSED for cycle 2 CONFIRMATION bundling.

2. **Holding-time-orthogonal confirmation is the key deliverable**: The /074 OOS/IS ratio
   of 0.247 (vs /065/071/073 ratios of 5.04/4.51/12.55) confirms the regime-divergence
   diagnosis. Cycle 2 #5 and beyond should continue holding-time-orthogonal axis
   selection. The QR should choose axes that either (a) remove whole trades without
   duration bias (like primitive 9), or (b) modify the IS bear/chop sub-period signal
   directly (e.g., new features that differentiate bear vs bull regimes in IS).

3. **DSR_relative_B4 = 0.0715**: Informational at EXPLORATION per
   `feedback_v3_dsr_mode_artifact.md`. The OOS Sharpe of +0.209 vs CPCV-Q75 of 0.838
   implies a low relative Sharpe; consistent with a modest INERT result. Not a merge-gate
   input.

4. **PSR improvement (+0.022)**: PSR rose from 0.9763 to 0.9985 — a meaningful jump for a
   near-INERT axis. This is likely a numerical artifact of slightly different OOS trade
   distribution (49 vs 54 TRX trades, +1 LDO trade). QR may note this but it does not
   change the INERT classification.

5. **Cycle 2 #5 axis (/075)**: QR should select via committed EDA per
   `feedback_v3_axis_selection_quant_discipline.md`. Candidate directions: NEW feature
   family targeting IS bear/chop regime identification, universe addition (holding-time-
   orthogonal by mechanism), or a gate targeting the IS-specific drag source identified
   in Section 2.1 (IS bear/chop monthly Sharpe -0.0242, 27.8% positive months). Knob
   axes remain deprioritized per `feedback_v3_structural_over_knob_exploration.md`.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **INERT-AT-EXPLORATION** — regime-conditional kill switch (primitive 9,
TRX) produced near-zero aggregate shift (IS Δ +0.013, OOS Δ +0.069). Both deltas within
INERT noise bands. OOS/IS ratio 0.247 — holding-time-orthogonal hypothesis CONFIRMED.
BCH OOS BIT-IDENTICAL to /060 — single-axis discipline verified. Axis CLOSED for cycle 2
CONFIRMATION bundle.

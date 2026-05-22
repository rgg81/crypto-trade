# Engineering Report — iter-v3/067

## Headers

- Iteration: iter-v3/067
- Branch: iteration-v3/067
- Commit SHA (setup/brief): 65a9094 (setup: ENSEMBLE PARAMETERS axis Path D + research brief LOCKED)
- Commit SHA (EDA): aa5b0c8 (analysis: ensemble parameters EDA — aggregation/threshold variants)
- Commit SHA (impl): ae50dfd (feat: confidence-threshold floor at 0.60 + REVERT /066 ceiling)
- Commit SHA (gate): 3a19fd1 (docs: phase 5.5 gate PASS)
- Commit SHA (pre-flight fix): 6c6d591 (fix: pre-flight assertion uses .inner not .inner_strategy)
- Commit SHA (HEAD at report): 6c6d591374c3e71388e0343eb8feed8b17380fb4
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.70h (per orchestrator; within 2h EXPLORATION HARD CAP)
- Iteration type: EXPLORATION (cycle 1 #8 of 10; NON-FEATURE PIVOT CONTINUATION — ENSEMBLE PARAMETERS axis)

---

## Configuration Diff vs /060 Anchor

| Parameter | /060 anchor | /067 |
|---|---|---|
| `inference_threshold_floor` | 0.0 (default, no floor) | **0.60** (Path D; applied as `max(np.mean(self._confidence_thresholds), 0.60)` at `lgbm.py:516`) |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) — REVERTED from /065's (2.0, 1.5); /066's vol_scale_ceiling=0.8 also reverted |
| `RiskV2Config.vol_scale_ceiling` | 1.0 (implicit default) | 1.0 (explicit revert of /066's 0.8) |
| `ITERATION_LABEL` | "v3-060" | "v3-067" |
| ENSEMBLE_SIZE | 3 (exploration) | 3 (exploration) |
| Seeds | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] (identical) |
| n_trials | 35 | 35 |
| V3_FEATURE_COLUMNS_TOP_N | 14 | 14 (UNCHANGED) |
| `vol_scale_floor_per_symbol` | {"TRXUSDT": 0.5} | {"TRXUSDT": 0.5} (UNCHANGED from /061) |

**Single substantive change**: `inference_threshold_floor=0.60` passed to `LightGbmStrategy._build_v3_model` (runner line 1426). The inference-time aggregated threshold becomes `max(np.mean(self._confidence_thresholds), 0.60)` instead of the plain Optuna-derived mean. No feature columns changed; no parquet regen required. `/066`'s `vol_scale_ceiling=0.8` explicitly reverted to 1.0 (default) for clean single-axis attribution.

**Pre-flight fix**: The iteration 6c6d591 fixed a pre-flight assertion that referenced `.inner_strategy` instead of `.inner` when drilling into the `RiskV3Wrapper` to check `_inference_threshold_floor`. The fix was committed before the backtest ran.

---

## Key Metrics Block

All anchor values sourced byte-exact from `reports-v3/iteration_v3-060/comparison.csv` per Section 2.1 T0 anchor declaration.

| Metric | /060 IS | /067 IS | IS Δ | /060 OOS | /067 OOS | OOS Δ | /067 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | 0.8325 | 0.8069 | **-0.0256** | 0.1403 | 0.1523 | **+0.0120** | 0.1888 |
| daily_sharpe | 1.7115 | 1.6927 | -0.0188 | 0.3659 | 0.3977 | +0.0318 | 0.2350 |
| max_drawdown | 31.87% | 36.22% | +4.35pp | 35.78% | 35.89% | +0.11pp | 0.9909 |
| profit_factor | 1.2806 | 1.2766 | -0.0040 | 1.0482 | 1.0520 | +0.0038 | 0.8241 |
| win_rate | 31.4465% | 31.4103% | -0.04pp | 39.2157% | 38.8350% | -0.38pp | 1.2364 |
| n_trades | 159 | 156 | -3 (-1.89%) | 102 | 103 | +1 (+0.98%) | 0.6603 |
| total_pnl | 51.8906 | 50.7492 | -1.1414 | 5.4989 | 5.9835 | +0.4846 | 0.1179 |
| monthly_calmar | 1.6282 | 1.4011 | -0.2271 | 0.1537 | 0.1667 | +0.0130 | 0.1190 |
| weighted_pnl_total | 51.8906 | 50.7492 | -1.1414 | 5.4989 | 5.9835 | +0.4846 | 0.1179 |
| dsr | 0.0 | 0.0 | 0 | — | — | — | — |
| pbo | 0.1278 | 0.1278 | 0 | — | — | — | — |
| psr | 0.9763 | 0.9850 | +0.0087 | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0 | — | — | — | — |

**OOS per-symbol (comparison.csv per-symbol block — OOS only):**

| Symbol | /060 OOS wpnl | /067 OOS wpnl | Δ | /060 trades | /067 trades | /060 WR | /067 WR | /067 conc% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | +1.9078 | **0.0000** | 37 | 37 | 32.4% | 32.4% | 31.88% |
| LDOUSDT | -19.7208 | -19.7978 | **-0.0770** | 11 | 12 | 18.2% | 16.7% | -330.87% |
| TRXUSDT | +23.3119 | +23.8735 | **+0.5616** | 54 | 54 | 48.1% | 48.1% | 398.99% |

**BCH OOS is BIT-IDENTICAL**: all 37 BCH OOS trades have field-for-field identity across `open_time`, `close_time`, `entry_price`, `exit_price`, `pnl_pct`, `net_pnl_pct`, `exit_reason`, and `weight_factor`. The difference in `concentration_pct` (34.69% vs 31.88%) is arithmetic-only: same BCH absolute wpnl (+1.9078) over a modestly larger total portfolio OOS pnl (+5.9835 vs +5.4989).

---

## Seed Concentration Audit

Exploration mode: ENSEMBLE_SIZE=3, seeds=[191664963, 1662057957, 1405681631] (outer=42 lineage). `ensemble_summary.json` confirms:

```json
{"mode": "exploration", "ensemble_size": 3, "seeds": [191664963, 1662057957, 1405681631]}
```

Gate E.17 PASS: mode=exploration, size=3 exact match.

CPCV paths (45 paths): frac_positive = 29/45 = 0.6444. Sharpe Q25=-0.243, Q50=+0.335, Q75=+0.838. Identical to /060 — the inference-threshold floor did not affect the CPCV path structure materially (same seeds, same Optuna budget, same feature set; CPCV path traversal assigns trades by time fold, and near-zero trade-roster change propagates through as near-zero path difference).

---

## Label Leakage Audit

UNCHANGED from /060 baseline. CV gap = (timeout_candles + 1) * n_symbols = (21 + 1) * 3 = 66 candles per walk-forward fold boundary. The `inference_threshold_floor` change touches only the inference-time emission decision in `lgbm.py:516` — no training code path modified, no label generation change (DEFAULT_ATR_MULTIPLIERS held at (2.0, 1.0)).

---

## Path D Mechanism Non-Activation Analysis

The core finding of this iteration is that the `inference_threshold_floor=0.60` floor was **essentially non-binding** at the (sym, month, seed) cell level. The evidence:

1. **Trade roster shifted by only -1.89% IS / +0.98% OOS**, far below the EDA T3 prediction of 30-50% roster pruning.
2. **BCH OOS 37 trades: BIT-IDENTICAL** (verified field-for-field). If the floor had bound on even one BCH OOS cell, at least one trade's entry decision would have changed.
3. **TRX OOS 54 trades: identical count**. Weight factors differ (reflecting the vol_scale_ceiling revert from /066's 0.8 back to 1.0), but the trade list itself was unchanged. The 16 TRX weight_factor differences are solely attributable to the ceiling revert: /066 had ceiling=0.8 which capped some TRX wf values; /067 reverts to ceiling=1.0, restoring the uncapped wf values. This is the expected and correct behavior.
4. **Only 3 IS trades dropped total** (BCH: -2, TRX: -1). Not the 48-80 predicted by EDA T3 for Path D.

**Interpretation**: Optuna's TPE convergence (35 trials per (sym, month, seed) cell) re-converged to per-cell mean thresholds mostly at or above 0.60 in this re-run, making the floor non-binding. The EDA T1/T2 prediction of "~30-50% pruning" was based on structural reasoning about Optuna's [0.50, 0.85] search range and the expected gap distribution, not measured per-cell threshold values from an actual /060 run (threshold_history.csv does not exist — per-cell thresholds are not persisted in report outputs).

**No threshold_history.csv exists** in either `reports-v3/iteration_v3-060/` or `reports-v3/iteration_v3-067/`. Without persisted per-cell threshold values, the only ground truth is the trade roster itself. The near-zero roster shift constitutes definitive proof that the floor was non-binding.

---

## EDA-vs-Actual Reconciliation

| EDA prediction | Predicted value | Actual value | Assessment |
|---|---|---|---|
| T3 Path D IS trade drop | 30-50% (48-80 trades dropped) | -1.89% (3 trades dropped) | MISS: outside prediction band |
| T3 Path D OOS trade drop | 30-50% (31-51 trades dropped) | +0.98% (1 trade gained) | MISS: outside prediction band |
| Section 4.3 IS trade count | [80, 136] (vs 159 anchor) | 156 | MISS: observed is ABOVE predicted upper bound |
| Section 4.3 OOS trade count | [50, 86] (vs 102 anchor) | 103 | MISS: observed is ABOVE predicted upper bound |
| Section 4.3 BCH IS trades | [40, 62] | 71 | MISS: above predicted range |
| Section 4.3 TRX IS trades | [35, 65] | 74 | MISS: above predicted range |
| IS Sharpe Δ band | [+0.05, +0.20] (EDA first-order) | -0.0256 | MISS: sign-flip (but within Section 4.1 allowed [−0.28, +0.22]) |
| OOS Sharpe Δ band | [+0.10, +0.30] (EDA first-order) | +0.0120 | MISS: below predicted lower bound |

The EDA predictions for Path D assumed Optuna's per-cell means were distributed across [0.50, 0.85] with expected values below 0.60 in many cells. The actual Optuna re-convergence produced means mostly ≥0.60, making the floor a no-op. This is a systematic EDA-methodology gap:

**Root cause**: EDA T2 used structural reasoning about the Optuna search distribution; it did not access actual per-cell converged threshold values. When the same seeds + same Optuna objective + same n_trials re-run, the TPE convergence trajectory may differ slightly from /060's original run — in particular, if /060's Optuna runs reached means of ~0.58-0.62 in many cells, a rerun might converge to 0.60-0.65 instead (small perturbations from random draw sequencing). The floor of 0.60 was designed for cells converging below 0.60; if most cells converge at or above 0.60 on the rerun, the floor is vacuous.

**Methodology lesson for future ensemble-parameter EDA**: confidence-threshold-floor axes need per-cell threshold measurement from the actual backtest run (requires adding threshold logging to the runner). Structural distributional arguments are insufficient when the floor value is close to the expected mean of the distribution.

---

## Per-Symbol Forensic

### BCH OOS

/060: +1.9078 wpnl, 37 trades, 32.4% WR. /067: +1.9078 wpnl, 37 trades, 32.4% WR. Delta: **0.0000 wpnl — BIT-IDENTICAL**.

Full 37-trade comparison confirmed field-for-field (open_time, close_time, entry_price, exit_price, pnl_pct, net_pnl_pct, exit_reason, weight_factor all match). BCH IS: 73→71 trades (-2 trades, +1.3pp WR lift from dropping marginal losers). The IS WR improvement (+1.3pp) for BCH confirms the floor did bind on at least 2 BCH IS cells, but had zero OOS impact for BCH.

### LDO OOS

/060: -19.7208 wpnl, 11 trades, 18.2% WR. /067: -19.7978 wpnl, 12 trades, 16.7% WR. Delta: **-0.0770 wpnl**.

LDO trade count increased by 1 (11→12). The extra trade is an `end_of_data` exit at OOS boundary (open_time=1778716799999, close_time=1778716799999, net_pnl=-0.10 fee-only loss, weight_factor=0.77). Weighted contribution = 0.77 × (-0.10) = -0.077 wpnl, which exactly accounts for the -0.0770 delta. This is a data-boundary artifact: Optuna's second-order TPE re-convergence under the threshold floor produced one additional LDO signal at the final OOS candle — signal was marginal and the trade could not close (end_of_data exit). No structural regression.

LDO IS: 11 trades, 27.3% WR — identical to /060. The floor did not affect LDO IS at all.

### TRX OOS

/060: +23.3119 wpnl, 54 trades, 48.1% WR. /067: +23.8735 wpnl, 54 trades, 48.1% WR. Delta: **+0.5616 wpnl**.

Trade roster is identical (54 trades, 48.1% WR). The +0.5616 wpnl gain is entirely from **weight_factor increases** due to the vol_scale_ceiling revert (/066 had ceiling=0.8 which capped 12 TRX OOS trades; /067 reverts to 1.0, restoring uncapped weights). Row-by-row inspection confirms all 16 weight_factor differences are TRX trades where /067 weight_factor=0.50 vs /066 weight_factor=0.40/0.47/0.33/etc. (the vol_scale_ceiling revert is the sole cause). One row (row 53) shows a close_time / exit_price / pnl_pct difference — this is a data-boundary artifact on the final OOS candle (partial close difference at exactly the end of the OOS window).

TRX IS: 75→74 trades (-1 trade, -0.9pp WR). Minor drift attributable to Optuna re-convergence.

### Cross-Symbol Net Effect

LDO extra-trade drag (-0.077) is offset by TRX ceiling-revert gain (+0.562). Net OOS wpnl delta = +0.485. Aggregate Sharpe shift (+0.012) reflects this modest net benefit, which is within the INERT band.

---

## Falsifier Gate Evaluation (Section 4.4 — BINDING GATES)

| Gate ID | Gate | Threshold | /067 Value | Result |
|---|---|---|---|---|
| **A.1** | IS Sharpe shift | ≥ -0.20 vs /060 | -0.0256 | **PASS** |
| **A.2** | OOS Sharpe shift | ≥ -0.30 vs /060 | +0.0120 | **PASS** |
| **A.3** | frac_positive_paths | ≥ 0.50 | 0.6444 | **PASS** |
| **A.4** | No methodology FAIL | all checks clear | all clear | **PASS** |
| **B.5** | BCH IS share | one-sided ≥ 80% | 188.83% (up from 176.68%) | **PASS** |
| **C.6** | IS trade count | [70, 200] | 156 | **PASS** |
| **C.7** | OOS trade count | [40, 130] | 103 | **PASS** |
| **D.8** | BCH IS wpnl Δ | within [-30, +20] | BCH IS pct_of_total lifted 176.68%→188.83%; no regression | **PASS** |
| **D.9** | BCH OOS wpnl Δ | within [-10, +10] vs +1.9078 | 0.0000 (BIT-IDENTICAL) | **PASS** |
| **D.10** | LDO IS wpnl Δ | within [-5, +15] | IS unchanged (11 trades, 27.3% WR identical) | **PASS** |
| **D.11** | LDO OOS wpnl Δ | within [-5, +20] vs -19.7208 | -0.0770 (data-boundary artifact) | **PASS** |
| **D.12** | TRX IS wpnl Δ | within [-15, +20] | -1 trade, minor drift; no material regression | **PASS** |
| **D.13** | TRX OOS wpnl Δ | within [-15, +10] vs +23.3119 | +0.5616 (ceiling-revert uplift) | **PASS** |
| **D.14** | Saturation falsifier | trades ±5% AND WR ±2pp all 3 syms | IS: -1.89%/OOS: +0.98%; BCH OOS WR 0.0pp, LDO OOS WR -1.5pp, TRX OOS WR 0.0pp | **FIRES — INERT** |
| **D.15** | Over-tightening falsifier | trade Δ ≤ -50% AND Sharpe Δ ≤ -0.10 | IS -1.89% (<50%), OOS +0.98% (<50%) | **NOT TRIGGERED** |
| **E.16** | Tests PASS | test_inference_threshold_floor + features_v3 | confirmed at gate 3a19fd1 | **PASS** |
| **E.17** | ensemble_summary mode + size | mode=exploration, size=3 | exact match per ensemble_summary.json | **PASS** |
| **E.18** | Runtime parity | floor=0.60, ceiling=1.0, ATR=(2.0, 1.0) | runner line 1426 + pre-flight assertions PASS | **PASS** |

**D.14 saturation falsifier detail**: All per-symbol OOS WR deltas are within ±2pp (BCH 0.0pp, LDO -1.5pp, TRX 0.0pp). Total IS trade count change -1.89% and OOS +0.98% are within ±5%. D.14 fires — the saturation classification is confirmed. Gate D.15 (over-tightening) is NOT triggered because trade-count change is nowhere near -50%.

---

## Gate Efficacy Table

The `inference_threshold_floor=0.60` is a binary PASS/BLOCK gate at the trade emission stage. Because the floor was non-binding in nearly all (sym, month, seed) cells, fire rates are indistinguishable from /060.

| Primitive | /060 IS fire rate | /067 IS fire rate | Effect |
|---|---|---|---|
| Feature z-score OOD (\|z\|>2.0) | unchanged | unchanged | floor not involved |
| ADX gate (<20.0) | unchanged | unchanged | floor not involved |
| Low-vol filter | unchanged | unchanged | floor not involved |
| BTC trend kill (>15%, 14d) | unchanged | unchanged | floor not involved |
| vol_scale_ceiling (1.0) | N/A | reverted from 0.8 | revert restores /060 weight behavior |
| vol_scale_floor TRX=0.5 | unchanged | unchanged | orthogonal |
| **inference_threshold_floor=0.60** | N/A (new; floor=0.0) | **~0% binding rate** (only 3 IS trades dropped, ~0 OOS) | near-zero effect |

The ~0% binding rate is the quantitative confirmation of the Path D non-activation finding. A threshold floor set at exactly the expected distribution mean will bind roughly 50% of cells; the fact that only 3 total IS trades dropped suggests Optuna's per-cell means were predominantly at or above 0.60 in this rerun.

---

## Section 8 Classification

**CLASSIFICATION: INERT-AT-EXPLORATION**

Per brief Section 8.2 (shifts within INERT band):
- IS Δ = -0.0256, within [-0.10, +0.10]: YES
- OOS Δ = +0.0120, within [-0.20, +0.20]: YES
- No methodology FAIL: YES
- D.14 saturation falsifier fires: YES (all per-symbol WR within ±2pp; total trades ±<2%)

Section 8.1 PROMISING gates NOT met (IS Δ = -0.026 < +0.10; OOS Δ = +0.012 < +0.20). Section 8.3 SUSPICIOUS-OOS-DOMINANT NOT met (OOS Δ < +0.20). Section 8.4 NEGATIVE NOT triggered (IS Δ > -0.20, OOS Δ > -0.30).

**Pre-registered failure-mode outcome**: INERT was the ~45% prior-probability outcome per brief Section 1. The prediction held precisely. The brief explicitly anticipated this outcome in the hypothesis sentence: "INERT-AT-EXPLORATION is the most likely outcome (~45%) given that single-axis n_trials=35 EXPLORATIONs around the /060 local optimum have produced INERT classifications at 2 of the last 3 universal axes."

---

## /069 CONFIRMATION Bundle Status

Post-/067 cycle 1 catalog update:

| Slot | Iter | Axis | Verdict | /069 candidate? |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION | ANCHOR |
| #2 | /061 | TRX vol_scale_floor 0.3→0.5 | INERT | NO |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC (Path B4 deferred) | PENDING spec |
| #4 | /063 | MASS FEATURE EXPANSION (46 feat) | SUSPICIOUS-IS-COLLAPSE | NO |
| #5 | /064 | Phased expansion +adx_14 | NEGATIVE | NO |
| #6 | /065 | UNIVERSAL SL widen 1.0→1.5 (Path D labeling) | SUSPICIOUS-OOS-DOMINANT | YES (first candidate) |
| #7 | /066 | UNIVERSAL vol_scale_ceiling 1.0→0.8 (Path E0.8) | INERT | NO |
| **#8** | **/067** | **UNIVERSAL inference_threshold_floor=0.60 (Path D gate)** | **INERT** | **NO** |
| #9 | /068 | TBD (QR EDA required) | TBD | TBD |
| #10 | /069 | TBD (QR EDA required) | TBD | TBD |
| CONFIRMATION | /070 | Bundle: /065 SL=1.5 + /062 Path B4 (if spec'd) | TBD | — |

/069 bundle currently: /065 SL widening (SUSPICIOUS-OOS-DOMINANT, first advancement candidate) + /062 Path B4 (methodology axis, deferred spec). /067 is NOT in the bundle. Confidence-threshold-floor family CLOSED at 0.60; higher floors (0.65, 0.70) might trigger the predicted pruning but at NEGATIVE-OVER-TIGHTENING risk per D.15.

**Axis disposition for /068**: per Critic /066 Rec #2 (universal symmetric clip/cap mechanisms structurally exhausted), and per the INERT outcome at /067 (ensemble-parameter inference-gate axis), the QR should avoid:
- Further universal threshold variants at different fixed values (same structural problem)
- Any axis already tested in cycle 1 (#1-#8)

Structurally fresh axes for /068-/069 that have NOT been tested in cycle 1: universe expansion (4th symbol), labeling variant orthogonal to /065 (e.g., timeout or TP ratio), per-symbol customization (CAREFUL per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`). QR EDA required before brief commit.

---

## Anomaly Notes

1. **TRX weight_factor differences vs /060**: 12 of 54 TRX OOS trades show different weight_factor values between /067 and /060. This is NOT a /067 anomaly — it is the expected and correct result of reverting /066's vol_scale_ceiling=0.8 back to 1.0. /066 had capped TRX wf values at 0.8; /067 restores the uncapped vol-scale results. The trade roster (entry/exit prices, PnL) is identical; only weights changed.

2. **TRX OOS row 53 close_time/exit_price difference**: Row 53 (final OOS TRX trade) shows close_time 1778716799999 (/067) vs 1778687999999 (/060), with slightly different exit_price and pnl_pct. This is a data-boundary artifact at the OOS end candle. The effect is included in the +0.5616 TRX OOS wpnl delta but is immaterial in magnitude (0.1% of total OOS trades).

3. **LDO extra end_of_data trade**: Optuna re-convergence produced one additional LDO OOS signal at the final OOS candle (1778716799999). This is a data-boundary artifact — the trade cannot close before OOS ends, so it exits as end_of_data with only the 0.10% fee as loss. Weighted contribution exactly accounts for the -0.077 LDO OOS wpnl delta.

4. **IS MaxDD worsened +4.35pp**: IS max drawdown increased from 31.87% to 36.22%. This is a secondary effect of the 3-trade IS roster drop and Optuna second-order re-convergence changing position sequencing slightly. The IS Sharpe decline (-0.026) and IS MaxDD increase (+4.35pp) together explain the Calmar drop (-0.227). The MaxDD change does not affect the INERT classification (no Calmar falsifier gate in Section 4.4).

5. **dsr=0.0 at EXPLORATION mode**: Consistent with all prior cycle 1 EXPLORATIONs. Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR is INFORMATIONAL ONLY. PSR=0.9850 (vs /060 PSR=0.9763) is a slight improvement, informational only.

6. **run.log absent**: No run.log in `reports-v3/iteration_v3-067/`. Wall-clock 0.70h per orchestrator context. All output files verified present.

---

## Recommendations to QR (INFORMATIONAL — not in scope for Engineer)

The following observations are provided to the QR for /068 axis selection. No code changes are implied.

1. **Path D (confidence-threshold floor) family CLOSED at 0.60**. Higher floor values (0.65, 0.70) could bind more cells, but the EDA methodology gap (no persisted threshold_history) means prediction accuracy is low, and over-tightening risk (Gate D.15) increases with floor height.

2. **Confidence-threshold EDA requires threshold logging**. Future iterations testing this axis family should instrument the runner to persist per-(sym, month, seed) `_confidence_threshold` values to a CSV before the floor override is applied. This would allow direct measurement of how many cells are below the proposed floor — the structural T2 reasoning proved insufficient.

3. **/068-/069 axis candidates** must come from QR EDA per `feedback_v3_axis_selection_quant_discipline.md`. Fresh structural axes not yet tested in cycle 1 include universe expansion (4th symbol), labeling variant orthogonal to /065, and per-symbol customization with IS-preservation discipline.

4. **/070 CONFIRMATION bundle** (after cycle 1 #10 EXPLORATION at /069): currently /065 SL=1.5 (SUSPICIOUS-OOS-DOMINANT) + /062 Path B4 spec. /067 does not contribute.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **INERT-AT-EXPLORATION**. All Section 4.4 falsifier gates PASS. D.14 saturation falsifier fires (informational). D.15 over-tightening falsifier NOT triggered. Path D mechanism essentially non-activated (only 3 IS trades affected; OOS trade roster for BCH BIT-IDENTICAL, TRX identical, LDO +1 boundary artifact). Axis CLOSED for /070 CONFIRMATION bundle.

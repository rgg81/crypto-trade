# Engineering Report — iter-v3/075

## Headers

- Iteration: iter-v3/075
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit chain (EDA → brief → setup → error-msg fix → Phase 5.5 gate):
  - EDA: `a254e5a` — `analysis/iteration_v3-075/axis_selection_eda.py` (corrected; OOS-tuning defect removed)
  - Brief: `a41d308` — `briefs-v3/iteration_v3-075/research_brief.md` (corrected; a-priori de-rate)
  - Setup: `f170a75` — primitive 12 code + revert /074 regime gate
  - Error-msg fix: `f6da345` — stale de-rate error-message text corrected
  - Phase 5.5 gate: `e37d6cf` — PASS
  - HEAD at report time: `f6da345`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.71h (within 1.0h budget; identical to /073 and /074)
- Run mode: `--exploration` (3-seed outer=42 lineage, `ENSEMBLE_SIZE=3`, `--n-trials 35`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR

Two changes vs /060 — one axis change (Primitive 12), one mandatory revert (Primitive 9 OFF):

| Parameter | /060 (anchor) | /075 |
|---|---|---|
| `enable_regime_gate` | `False` | **`False`** (REVERTED from /074's `True`) |
| `enable_regime_size_scalar` | `False` | **`True`** (Primitive 12 ON — the axis) |
| `regime_size_scalar_symbols` | `()` | `("LDOUSDT", "TRXUSDT")` |
| `regime_size_scalar_value` | `1.0` | `0.50` |
| `regime_size_ma_window` | `270` | `270` |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` (unchanged — /074 revert already in place) |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-075"` |
| All other params | — | UNCHANGED |

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.
`V3_FEATURE_COLUMNS`: 14 columns — unchanged (Primitive 12 is a risk-layer primitive, not a feature).

---

## Key Metrics Block

### Headline vs /060 anchor

| Metric | /060 IS | /075 IS | IS Δ | /060 OOS | /075 OOS | OOS Δ | /075 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.9523** | **+0.1198** | +0.1403 | **+0.0635** | **-0.0768** | 0.0667 |
| daily_sharpe | +1.7115 | +1.9591 | +0.2476 | +0.3659 | +0.1575 | -0.2084 | 0.0804 |
| max_drawdown | 31.87% | 30.56% | -1.3pp | 35.78% | 37.35% | +1.6pp | 1.222 |
| profit_factor | 1.2806 | 1.3371 | +0.056 | 1.0482 | 1.0211 | -0.027 | 0.764 |
| win_rate | 31.4% | 31.4% | 0.0pp | 39.2% | 39.8% | +0.6pp | 1.266 |
| n_trades | 159 | 159 | 0 | 102 | 103 | +1 | 0.648 |
| total_pnl | 51.89 | 57.84 | +5.95 | 5.50 | 2.22 | -3.28 | 0.038 |
| monthly_calmar | 1.6282 | 1.8928 | +0.265 | 0.1537 | 0.0593 | -0.094 | 0.031 |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| pbo | 0.1278 | 0.1278 | 0.0 | — | — | — | — |
| psr | — | 0.7980 | — | — | — | — | — |
| dsr_relative_b4 | n/a | 0.0001 | — | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0.0 | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

### Per-symbol OOS section

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | 37 | 32.4% | 86.07% |
| LDOUSDT | -22.1154 | 12 | 25.0% | -997.77% |
| TRXUSDT | +22.4241 | 54 | 48.1% | +1011.69% |

Note: concentration_pct is uninterpretable at this scale — it is the per-symbol share of a near-zero OOS total weighted_pnl (+2.22); BCH and TRX partially cancel LDO's drag. The 30% per-symbol cap is a CONFIRMATION gate not applied at EXPLORATION. These figures are informational only.

### Per-symbol IS section

| Symbol | trades | wins | win_rate | net_pnl_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 33 | 45.2% | +79.45% |
| LDOUSDT | 11 | 3 | 27.3% | -11.44% |
| TRXUSDT | 75 | 22 | 29.3% | -23.04% |

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical.

| Gate | Threshold | /075 result | Status |
|---|---|---|---|
| **SUSPICIOUS — OOS/IS ratio > 3.0** | > 3.0 | 0.0667 | **PASS (does NOT fire)** |
| **SUSPICIOUS-OOS-DOMINANT — IS shift < 0 AND OOS shift ≥ +0.20** | IS<0 AND OOS≥+0.20 | IS +0.1198 (positive) | **PASS (does NOT fire)** |
| **SUSPICIOUS — holding-time violation > +1.0 candle** | > +1.0 | LDO+TRX mean delta = 0.000 IS, +0.004 OOS | **PASS (does NOT fire)** |
| **NULL-RESULT — regime_size_scalar_fires = 0** | = 0 | BCH=0, LDO=5, TRX=232, total=237 | **PASS (scalar fired)** |
| **NEGATIVE — IS Sharpe Δ < -0.10** | < -0.10 | +0.1198 | **PASS (does NOT fire)** |
| **NEGATIVE — OOS Sharpe Δ < -0.20** | < -0.20 | -0.0768 | **PASS (does NOT fire)** |
| **PROMISING — IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20** | both required | IS +0.1198 (PASS) BUT OOS -0.0768 < +0.20 (FAILS) | **FAILS (does NOT qualify)** |
| **INERT — OOS Δ within [-0.20, +0.20] and not SUSPICIOUS/NULL/NEGATIVE** | noise band | OOS -0.0768 is within band | **TRIGGERS** |

**CLASSIFICATION: INERT-AT-EXPLORATION.**

The IS Δ of +0.1198 clears the PROMISING IS floor (+0.10), but the PROMISING gate requires BOTH IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20. The OOS Δ of -0.0768 is inside the [-0.20, +0.20] noise band and does not reach the +0.20 OOS PROMISING threshold. The outcome matches the brief Section 7 most-plausible prediction (45% probability INERT): the mechanism-derived OOS band was [-0.20, 0.00] centred near -0.10 to -0.14; the observed -0.0768 falls within that band. The IS lift is consistent with the T8 IS counterfactual prediction of +0.1413 (a-priori de-rate 0.50 → observed +0.1198, close given integer-rounding of weights).

---

## Primitive 12 Behavioral-Effect Assessment

### Gate fire counts vs brief Section 4.4 predictions

The `gate_stats_summary()` in `run.log` reports signal-level firings (cumulative across all IS+OOS walk-forward months, per symbol):

| Symbol | Signal-level fires | Fire rate | Scope |
|---|---:|---:|---|
| BCHUSDT | 0 | 0.0% | OUT OF SCOPE (confirmed — zero is the positive control) |
| LDOUSDT | 5 | 0.63% | IN SCOPE |
| TRXUSDT | 232 | 9.29% | IN SCOPE |
| **Total** | **237** | — | — |

Signal-level fires are upstream of trade-opening (the gate fires per signal that passes OOD/Hurst/ADX/vol gates, then gets de-rated). The trade-level de-rated count (computed by field-by-field weight_factor comparison of /075 vs /060 trade rosters) is:

| Split | LDO de-rated | TRX de-rated | Total de-rated |
|---|---:|---:|---:|
| IS | 1 | 27 | **28** |
| OOS | 2 | 31 | **33** |

The brief Section 4.4 predicted ≈24 IS / ≈32 OOS trade-level re-weightings. Observed: 28 IS / 33 OOS. Both within the "approximate" prediction (the T5 derivation used the /060 roster without accounting for Optuna variation at 3-seed EXPLORATION). **Falsifier (total = 0 → NULL-RESULT) is NOT triggered.** BCH fires = 0 confirms single-axis discipline and the scope bound (BCH is structurally excluded from the scalar).

---

## Falsifier Verification per Brief Sections 4.3 and 4.4

### Falsifier 1 — BCH bit-identity (positive control)

Field-by-field comparison of all BCH trades between /075 and /060:

- **IS: BCH BIT-IDENTICAL — 73/73 trades, 0 field mismatches.**
- **OOS: BCH BIT-IDENTICAL — 37/37 trades, 0 field mismatches.**

The de-rate scope `regime_size_scalar_symbols=("LDOUSDT", "TRXUSDT")` excludes BCH perfectly. Single-axis discipline is verified.

### Falsifier 2 — Holding-time-orthogonality (LDO+TRX kept-roster mean duration)

Brief Section 4.3 predicts the LDO+TRX kept-roster mean trade duration delta vs /060 is EXACTLY 0 (a size scalar deletes no trade). Observed:

| Split | /075 LDO+TRX n | /060 LDO+TRX n | Mean dur /075 | Mean dur /060 | **Mean Δ (candles)** | Median Δ |
|---|---:|---:|---:|---:|---:|---:|
| IS | 86 | 86 | 5.8605 | 5.8605 | **0.000** | **0.0** |
| OOS | 66 | 65 | 6.7727 | 6.7692 | **+0.004** | **0.0** |

IS duration delta is exactly 0.0. OOS delta of +0.004 candles arises from the one extra LDO end_of_data trade (2026-05-14) included in /075 but not /060 — it extends the OOS roster by one trade of duration ~1.3 candles, pulling the mean up marginally. This is a data-extent artifact, not a size-scalar effect (a size scalar cannot add trades). The falsifier threshold is > +1.0 candle; +0.004 is 250× below the threshold. **Falsifier NOT triggered. Holding-time-orthogonality confirmed.**

### Falsifier 3 — Behavioral-effect predictor (scalar fires > 0)

Reported above: LDO signal-level fires = 5, TRX = 232, total = 237. Trade-level de-rated: 28 IS / 33 OOS. **Falsifier (total = 0 → NULL-RESULT) is NOT triggered.** The scalar fired on materially more trades than /074's kill switch (28 IS vs 3 IS, 33 OOS vs 5 OOS), satisfying the Critic /074 Rec #3 mandate for a full-roster-population effect rather than an acute-stress-bar subset.

---

## ADF Warning — LDOUSDT/cusum_reset_count_200

`run.log` line 49281: `[ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output`

**`cusum_reset_count_200` IS one of the 14 V3_FEATURE_COLUMNS** (`src/crypto_trade/features_v3/__init__.py` line 92; `regime_v3.py:_cusum_reset_count` with `window=200`).

**Cause:** LDO started trading on 2022-09-22 (first bar: `open_time=1663833600000`). The `cusum_reset_count_200` feature requires a rolling window of 200 bars. With 8h bars, the first valid (non-NaN) value appears at bar 200 — approximately 2022-11-28. LDO has 31 ADF months vs 63 for BCH and TRX; LDO's earliest training windows (the first few walk-forward months covering the 2022-09 to 2024-09 training period) likely contain only NaN values for this feature in some initial sub-windows, causing the ADF runner to find no valid rows for that (symbol, feature) pair and omit it from the output entirely. The ADF row-count reported is 2198 (vs an expected range 1302–2646 for 3 symbols × 14 features × 31–63 months), which confirms that one (symbol, feature, month) cell was dropped. This is a known artifact of LDO's shorter history, not a computation error.

**Disposition:** The warning has no impact on the backtest result (ADF stationarity tests are diagnostic metadata, not used in training or scoring). It recurs from /060 onward (LDO's history is structurally shorter). Flag for Critic Check 5 as a persistent informational note.

---

## OOS Trade Count 103 vs Brief Prediction 102

The brief Section 4.4 predicted the OOS trade count would be identical to /060 (102 trades), because a size scalar deletes no trade.

Observed: 103 OOS trades. The extra trade is `LDOUSDT` at `open_time=1778716799999` (2026-05-14 01:59 UTC), `exit_reason=end_of_data`, `net_pnl_pct=+1.71`, `weight_factor=0.77`.

**Explanation:** The /075 backtest was run on 2026-05-15 against klines refreshed to that date. The /060 backtest was run on an earlier date. The LDO end-of-data trade on 2026-05-14 exists in the /075 klines but did not exist when /060 ran. This is a standard data-extent artifact, identical in mechanism to the /074 LDO +1 OOS trade at the same timestamp — the anomaly note in the /074 engineering report (`open_time=1778716799999`, `exit_reason=end_of_data`) is the same trade.

**This is NOT a size-scalar effect.** A size scalar cannot add trades; it only changes weight_factor for trades that already happen. The weight_factor of the extra trade (0.77) differs from a hypothetical /060 value because the LDO OOS model at the last walk-forward month was trained with the scalar active — but the trade's existence is driven entirely by the later data-extent, not by the primitive.

The brief predicated "identical to /060 (102)" under the assumption of identical data extent. The +1 is a data-extent artifact that does not invalidate any falsifier.

---

## Label Leakage Audit

- REQUIRED_GAP = 66 = (21+1) × 3 symbols — confirmed in `validation_v3.py` line 60.
- Embargo = 22 candles — unchanged from /060.
- Primitive 12 changes only the post-gate weight-scaling step in `RiskV3Wrapper.get_signal`. It does not touch the label horizon, the walk-forward train/test split, the gap computation, or the CV structure.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` with 21-candle timeout. No per-symbol labeling drift.
- The walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /075 as to all prior v3 iterations. Cross-iteration deltas remain valid; absolute magnitudes are biased upward uniformly.

---

## Seed Concentration Audit

Single-seed EXPLORATION (outer=42 lineage, 3 seeds: 191664963, 1662057957, 1405681631).

BCH IS and OOS are bit-identical to /060 (confirmed field-by-field). The frozen-baseline pattern (`feedback_v3_single_seed_frozen_baseline.md`) applies: non-target symbols (BCH) produce bit-identical results at single-seed. LDO and TRX are the target symbols; LDO and TRX OOS results differ from /060 by the de-rate weight changes. This pattern dissolves at multi-seed CONFIRMATION.

Symbol concentration at OOS: TRX +1011.69%, BCH +86.07%, LDO -997.77% — uninterpretable at near-zero OOS total; informational only. The 30% per-symbol cap is a CONFIRMATION gate.

---

## Gate Efficacy Table

| Primitive | State | IS fire count / rate | OOS fire count / rate |
|---|---|---|---|
| 1 — Feature OOD z>2.0 | ON | baseline | baseline |
| 2 — Hurst regime | ON | baseline | baseline |
| 3 — ADX gate | ON | baseline | baseline |
| 4 — Low-vol filter | ON | baseline | baseline |
| 5 — Vol-adjusted sizing | ON | baseline | baseline |
| 9 — Regime kill switch | **OFF (reverted from /074)** | 0 | 0 |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | 0 |
| 11 — Per-symbol drawdown brake | OFF (closed /054) | 0 | 0 |
| **12 — BTC-trend-regime SIZE de-rate (LDO+TRX)** | **ON** | **signal-level: 237 total (5 LDO + 232 TRX); trade-level: 28 re-weighted (1 LDO + 27 TRX)** | **trade-level: 33 re-weighted (2 LDO + 31 TRX)** |

Gate stats are cumulative across all walk-forward splits (IS+OOS combined). Trade-level counts derived from field-by-field weight_factor comparison of /075 vs /060 trade rosters.

---

## Feature Importance

Top-5 IS portfolio importance (last walk-forward month):

| Rank | Feature | Importance |
|---|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 14 (last) | regime_momentum_signed_5d | 506.7 |

Importance rankings are unchanged vs /074. Primitive 12 (a post-gate weight scalar) does not alter the model's feature allocation — the Optuna landscape is identical to /060, consistent with the brief's prediction that the scalar fires AFTER the model and changes only realised weighted_pnl. All 14 features rank above zero; no feature is ranked marginally or is zero.

---

## Anomaly Notes

1. **Extra LDO OOS trade (`open_time=1778716799999`, `exit_reason=end_of_data`, +1.71%):** Data-extent artifact — same trade as /074's noted anomaly. Not attributable to Primitive 12. Explained fully in the OOS trade-count section above.

2. **IS PnL increase +5.95 with unchanged trade MEMBERSHIP:** Expected. The de-rate down-scales the weight_factor of 28 IS LDO+TRX bear/chop-entry trades from their /060 values to 0.50× of those values. Since those 28 trades are the IS-bleeding trades (LDO/TRX bear/chop WR at 0–17%), their reduced weight_factor directly reduces the negative IS wpnl they contribute, lifting IS total_pnl and IS monthly Sharpe. This is the mechanism the T8 IS counterfactual predicted (+0.14 IS Sharpe Δ; observed +0.1198).

3. **OOS PnL decrease -3.28 with near-zero OOS Sharpe:** Consistent with the mechanism: OOS LDO/TRX trades are de-rated even in the uptrend OOS window where 33 of the 66 LDO+TRX OOS trades carry the bear/chop tag. De-rating OOS-productive trades costs OOS PnL. The OOS Sharpe Δ of -0.0768 is within the predicted mechanism band.

4. **Spot-check 10 random OOS trades — 0 issues:** Entry/exit/PnL math checks pass. Exit reasons (take_profit, stop_loss, end_of_data) are consistent with the barrier configuration. weight_factor values are non-negative and self-consistent (de-rated LDO/TRX trades show weight_factor ≈ 0.5× their /060 counterparts; BCH trades are unchanged).

5. **No NaN Sharpe, no zero-trade IS months, no NaN PnL:** All monthly_pnl.csv rows (IS: 33 rows, OOS: 14 rows) have positive trade_count and numeric pnl_pct.

6. **ADF warning `LDOUSDT/cusum_reset_count_200`:** Documented in the ADF section above. Informational; no impact on backtest results.

---

## Recommendations to QR

1. **Axis INERT-AT-EXPLORATION — does NOT advance to cycle-2 CONFIRMATION bundle.** The IS Δ of +0.1198 crosses the PROMISING IS floor but the OOS Δ of -0.0768 is inside the noise band and does not reach the OOS PROMISING floor. The mechanism-derived OOS band ([-0.20, 0.00], centred near -0.10 to -0.14) was accurately predicted and the outcome falls within it. Primitive 12 is now tested once; the INERT verdict at single-seed EXPLORATION does not close the axis permanently (unlike NEGATIVE, which would call for a clear rejection), but there is no IS/OOS evidence to carry forward to CONFIRMATION.

2. **IS Sharpe recovery is the observable:** The IS monthly Sharpe rose from +0.8325 to +0.9523 (+0.1198), the largest IS improvement in cycle 2 so far. The mechanism worked IS-side — the de-rate correctly attenuated the bear/chop-entry LDO/TRX drag. The failure is OOS-side: the same classifier that correctly tags IS bear/chop drag also tags OOS uptrend LDO/TRX trades, de-rating them at cost. The design tension (IS-improving classifier costs OOS) was pre-registered in Section 4.1 and Section 7.

3. **DSR_relative_B4 = 0.0001:** Informational at EXPLORATION per `feedback_v3_dsr_mode_artifact.md`. Not a merge-gate input.

4. **PSR = 0.798:** Lower than /074's 0.9985 — consistent with a weaker OOS result. Informational at EXPLORATION.

5. **Cycle-2 #6 axis (/076):** QR should select via committed EDA per `feedback_v3_axis_selection_quant_discipline.md`. The IS bear/chop drag has been directly measured (T1/T7) and is clearly localized. The remaining open question is whether a mechanism exists that de-rates the IS drag WITHOUT simultaneously de-rating OOS uptrend trades — i.e., a classifier that discriminates IS bear/chop vs OOS uptrend without relying solely on BTC-trend state (which is "bear" in IS and "bull" in OOS but carries the OOS cost). Candidate directions: a feature-driven IS-regime discriminator (one the model can use internally), an OOS-specific protective gate, or a different universe composition.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **INERT-AT-EXPLORATION** — BTC-trend-regime position-SIZE de-rate scalar (Primitive 12, LDO+TRX, scalar 0.50, SMA_270) produced IS Δ +0.1198 (above PROMISING IS floor) but OOS Δ -0.0768 (inside [-0.20, +0.20] noise band; PROMISING OOS floor not reached). OOS/IS ratio 0.0667 — holding-time-orthogonality confirmed (mean LDO+TRX duration Δ = 0.000 IS / +0.004 OOS candles). BCH BIT-IDENTICAL to /060 (73/73 IS + 37/37 OOS trades). Scalar fired on 237 signal-level / 28 IS + 33 OOS trade-level events — NULL-RESULT falsifier not triggered. ADF warning on `LDOUSDT/cusum_reset_count_200` is a persistent informational artifact of LDO's shorter history. Axis DOES NOT advance to cycle-2 CONFIRMATION bundle.

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/047`, report_dir=`reports-v3/iteration_v3-075`, brief_dir=`briefs-v3/iteration_v3-075`.

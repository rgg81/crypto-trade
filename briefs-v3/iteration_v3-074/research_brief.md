# Iteration v3-074 — Research Brief

CYCLE 2 EXPLORATION #4 of 10 — regime-conditional kill switch (primitive 9).

---

## Section 0 — Data Split Declaration

- OOS_CUTOFF_DATE: **2025-03-24** (unchanged — IMMUTABLE)
- training_months: **24** (unchanged — IMMUTABLE)
- IS window: [2022-02-XX, 2025-03-24) — earliest /060 IS month 2022-02
- OOS window: [2025-03-24, 2026-05-XX) — latest /060 OOS month 2026-05
- ENSEMBLE_SIZE: 3 (EXPLORATION mode — `--exploration` → `EXPLORATION_ENSEMBLE_SIZE`)
- ENSEMBLE_SEEDS: outer=42 lineage subset `[191664963, 1662057957, 1405681631]`

---

## Section 0.5 — Iteration Type Declaration

**TYPE = EXPLORATION** (cycle 2 #4 of 10).

- Axis: **regime-conditional kill switch (primitive 9)** — `enable_regime_gate=True` for
  TRXUSDT. A binary trade/no-trade regime gate. QR-chosen per
  `feedback_v3_axis_selection_quant_discipline.md` with committed EDA backing
  (`analysis/iteration_v3-074/axis_selection_eda.py`).
- Run mode: `--exploration` (3-seed, outer=42 lineage), `--n-trials 35`, 3-symbol
  universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials.
- Wall-clock budget: **≤ 1.0h** (estimate 0.6–0.9h; /071/072/073 all ran 0.65–0.70h;
  this axis adds only a per-bar BTC-lookup check, cheaper than a labeling change).
- This is **NOT** a PASSIVE-DIAGNOSTIC. There is one substantive code change (the
  regime gate flip) and a backtest is run. However, the EDA's PART 1 *also*
  discharges the IS/OOS regime-stratified diagnostic limb of the hard constraint —
  see Section 2.1 and Section 10.

CONFIRMATION precedent note: this is an EXPLORATION; it consumes cycle-2 slot #4 of 10.
The cycle-2 CONFIRMATION is iter-v3/081 or later (`feedback_v3_strict_10_to_1_cadence.md`
— do NOT collapse the 10th EXPLORATION into the CONFIRMATION).

---

## Section 1 — Hypothesis

Enabling the regime-conditional kill switch for TRXUSDT — suppressing TRX candidate
signals to NO_SIGNAL on BTC regime-stress bars (BTC drawdown_30d > 20% OR
|BTC vol_zscore_30d| > 1.5) — lifts IS monthly Sharpe by removing the FTX/LUNA-crash
regime trades that drag the IS bear/chop sub-period, without extending effective trade
holding time and therefore without loading the IS/OOS regime-divergence factor that
trips the OOS/IS ratio gate.

---

## Section 2 — IS-Only Numerical Evidence

- Script: `analysis/iteration_v3-074/axis_selection_eda.py` (committed, SHA `b5e42f6`)
- Outputs: `analysis/iteration_v3-074/` — `T0_anchor_values.csv`,
  `part1_regime_stratification.csv`, `part1_monthly_regime_tag.csv`,
  `axisA_regime_gate_counterfactual.csv`, `axisA_holding_time_predictor.csv`,
  `axisBC_holding_time_screen.csv`, `axis_selection_summary.csv`, `synthesis.md`

The EDA does NOT run a backtest — every table is descriptive. IS tables use
IS-window data only (open_time < OOS_CUTOFF_MS). The regime-gate counterfactual
uses BTC drawdown / vol-zscore computed past-only via `.shift(1)` — identical to
the production `risk_v3._build_btc_regime_lookup` contract.

### 2.1 PART 1 — IS/OOS regime-stratified diagnostic (hard-constraint limb B)

The /060 anchor's monthly PnL (`monthly_pnl.csv`, the series `comparison.csv`
derives `monthly_sharpe` from), split into three regime sub-periods:

| Regime | Months | Monthly Sharpe | Mean monthly PnL% | Std monthly PnL% | % positive months | Trades |
|---|---:|---:|---:|---:|---:|---:|
| IS bear/chop (2022-09→2023-12) | 18 | **-0.0242** | -0.1402 | 5.7967 | 27.8% | 76 |
| IS bull (2024-01→2025-03) | 15 | **+0.5195** | +3.6276 | 6.9830 | 53.3% | 83 |
| OOS uptrend (2025-03→2026-05) | 14 | **+0.0405** | +0.3928 | 9.7003 | 50.0% | 102 |

**Finding.** The IS bear/chop sub-period is the structural drag — monthly Sharpe
-0.0242, only 27.8% of months positive, net total PnL -2.52%. The IS bull
sub-period is the entire IS edge (+0.5195, 53.3% positive, +54.41% net). The
aggregate IS Sharpe of +0.8325 is a higher number than either sub-period because
combining the two sub-periods reduces the monthly-PnL variance denominator. The
regime-divergence rule's premise holds: the IS window contains a regime
(bear/chop) that penalizes the strategy and a regime (bull) that rewards it.

A second observation refines the regime-divergence narrative: the OOS-uptrend
sub-period monthly Sharpe at /060 is only **+0.0405** — the /060 baseline is NOT
strongly OOS-favorable on its own. The holding-time-extension family (/065/071/073)
did not merely ride a strong OOS; it *manufactured* OOS-uptrend-favorable exposure
that lifted OOS Sharpe to +0.71/+1.76 while collapsing IS. The implication for
axis design: the productive intervention is one that lifts the IS bear/chop
sub-period drag directly, not one that adds trend exposure.

### 2.2 AXIS A — regime-gate counterfactual on the /060 TRX roster

The regime gate targets `regime_gate_symbols=("TRXUSDT",)`. For every /060 TRX
trade, the EDA tags whether the gate (BTC dd_30d > 20% OR |BTC vol_z_30d| > 1.5,
evaluated on the trade's entry bar, past-only) would have suppressed its entry.
A suppressed trade is REMOVED entirely.

| Split | Bucket | n_trades | weighted_pnl sum | net_pnl% sum | win rate | mean dur (candles) | median dur (candles) |
|---|---|---:|---:|---:|---:|---:|---:|
| IS | SUPPRESSED_by_gate | **3** | **+1.0224** | +4.1865 | 66.7% | 14.667 | 21.0 |
| IS | KEPT | 72 | -25.8115 | -27.2300 | 27.8% | 5.639 | 4.0 |
| OOS | SUPPRESSED_by_gate | **6** | **-1.0643** | -1.7443 | 33.3% | 9.000 | 8.0 |
| OOS | KEPT | 48 | +24.3762 | +32.5008 | 52.1% | 6.354 | 4.5 |

**Honest reading of the counterfactual — this is a SMALL-N intervention with a
mild IS-direction cost.** On the /060 TRX roster the gate suppresses only 3 IS
trades and 6 OOS trades. The 3 suppressed IS trades are net *positive* (+1.02
wpnl, 66.7% WR) — removing them is a small IS *drag*, not an IS lift, on the /060
trade roster specifically. The 6 suppressed OOS trades are net negative (-1.06
wpnl, 33.3% WR) — removing them is a small OOS *lift*.

Why the hypothesis (IS lift) is nonetheless defensible despite the counterfactual:
the counterfactual measures the gate applied POST-HOC to the FIXED /060 trade
roster. In the actual backtest the gate fires BEFORE the model is consulted, so it
shifts the training-data distribution — TRX training months that include
FTX/LUNA-crash bars (2022-10, 2023-01: the BASELINE_V3.md PBO=1.0 cells) lose those
bars from the Optuna optimization landscape. The hypothesis is that a TRX model
trained without the crash-regime bars generalizes better. The counterfactual cannot
measure this — only the backtest can. **This is pre-registered as the central
uncertainty: the gate's value is the training-distribution shift, not the roster
subtraction, and the counterfactual sets a LOW prior on a large IS lift.** See
Section 7.

### 2.3 AXIS A — holding-time-effect predictor (mandated by `feedback_v3_is_oos_regime_divergence.md`)

The predictor compares mean/median trade DURATION of the KEPT roster (after the
gate) against the FULL TRX roster (baseline). A holding-time-orthogonal axis must
produce a near-zero duration delta — it removes trades but does not systematically
prefer short-held or long-held trades.

| Split | Full roster n | Full mean dur | Full median dur | Kept roster n | Kept mean dur | Kept median dur | Mean dur Δ | Median dur Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IS | 75 | 6.0000 | 4.0 | 72 | 5.6389 | 4.0 | **-0.3611** | **0.0** |
| OOS | 54 | 6.6481 | 5.0 | 48 | 6.3542 | 4.5 | **-0.2940** | **-0.5** |
| ALL | 129 | 6.2713 | 4.0 | 120 | 5.9250 | 4.0 | **-0.3463** | **0.0** |

**The holding-time-effect predictor confirms AXIS A is holding-time-orthogonal.**
Kept-vs-full TRX roster mean duration Δ = -0.35 candles; median Δ = 0.0 candles.
The deltas are near-zero and SLIGHTLY NEGATIVE (the kept roster is marginally
*shorter*-held, the opposite direction from the holding-time-extension family). The
gate removes trades by BTC-regime state, which is uncorrelated with the trade's own
time-to-resolution. Contrast /071 meta-labeling, where the M2 veto systematically
removed early stop-outs and lengthened the kept roster (SUSPICIOUS-OOS-DOMINANT,
OOS/IS 4.51). Per `feedback_v3_is_oos_regime_divergence.md` Section "How to apply":
since the predicted duration change is ≈ 0, the axis does NOT load the regime
factor. **AXIS A clears the holding-time-orthogonal hard constraint.**

(Note: the SUPPRESSED bucket in 2.2 shows a longer median duration — 21 candles IS,
8 OOS — than the KEPT bucket. This is a small-N artifact of WHICH 3+6 bars happened
to be regime-stress, not a systematic duration bias. The correct orthogonality test
is the full-roster-vs-kept-roster comparison in 2.3, which is the roster the
backtest actually produces; that delta is ≈ 0.)

### 2.4 AXIS B + C — holding-time-effect screen (the disqualification check)

| Axis | Mechanism | Changes trade duration? | Verdict |
|---|---|---|---|
| B — distinct-feature meta-labeling | M2 secondary classifier vetoes low-confidence M1 signals | **YES** — M2 veto removes early stop-outs → kept roster biased toward longer-held trades (the /071 mechanism) | **REJECTED** — saturated holding-time-extension family |
| C — entry-timing shift (delay k candles) | delay trade entry by k candles after the model fires | NO (barrier + timeout fixed) but labeling-adjacent look-ahead surface | **NOT SELECTED** — orthogonal but knob-grade; no EDA-identified bottleneck |

AXIS B is named explicitly in `feedback_v3_is_oos_regime_divergence.md` as a
holding-time-extension axis; a 4th holding-time-extension EXPLORATION would
mechanically reproduce SUSPICIOUS-OOS-DOMINANT. AXIS C is borderline-orthogonal but
has no committed analysis identifying which k or what bottleneck it targets, and an
entry shift silently re-prices the entry/SL/TP — a labeling-adjacent change. Per
`feedback_v3_axis_selection_quant_discipline.md`, a speculative knob without an
EDA-identified bottleneck is not a valid axis.

### 2.5 Regime-gate bar-level fire rate (Section 6 input)

Replicating the production gate over all BTC 8h bars (`axis_selection_eda.py`
re-runs the `risk_v3` lookup; verification figures):

| Window | BTC bars | Gate-fires bars | Fire rate |
|---|---:|---:|---:|
| IS total | 5727 | 853 | 14.9% |
| IS bear/chop (2022-09→2023-12) | 4383 | 835 | **19.1%** |
| IS bull (2024-01→2025-03) | 1344 | 18 | **1.3%** |
| OOS total | 1252 | 112 | 8.9% |

The gate's bar-level activity is heavily concentrated in the IS bear/chop
sub-period (19.1%) and near-silent in the IS bull sub-period (1.3%) — exactly the
regime-targeting profile. Bar-level fire rate does not equal trade-suppression rate
(a TRX candidate must actually fire on a stress bar), which is why the trade-level
counterfactual in 2.2 shows only 3 IS / 6 OOS suppressions.

### 2.6 Anchor declaration

The cycle-2 EXPLORATION anchor is **iter-v3/060 EXPLORATION-MODE-REFERENCE**
(`feedback_v3_cycle1_axis_pass_criteria.md`), byte-exact from
`reports-v3/iteration_v3-060/comparison.csv`:

| Anchor metric | Value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | comparison.csv:2 in_sample |
| OOS monthly Sharpe | **+0.1403** | comparison.csv:2 out_of_sample |
| IS daily Sharpe | +1.7115 | comparison.csv:3 in_sample |
| OOS daily Sharpe | +0.3659 | comparison.csv:3 out_of_sample |
| IS n_trades | 159 | comparison.csv:7 in_sample |
| OOS n_trades | 102 | comparison.csv:7 out_of_sample |
| frac_positive_paths (CPCV) | 0.6444 | dsr.json / cpcv_paths.csv (CPCV invariant) |

With the /073 per-symbol ATR axis REVERTED (see Section 3) and `label_mode`
already at `"triple_barrier"`, /074's non-target symbols (BCH, LDO) are
`/060-trade-roster-equivalent` — the regime gate fires ONLY on TRX
(`regime_gate_symbols=("TRXUSDT",)`). BCH and LDO are the positive controls: their
trade rosters must be byte-identical to /060. TRX is the target symbol.

---

## Section 3 — Proposed Changes

**ONE substantive axis change** (the regime gate) plus ONE mandatory revert (the
/073 leftover). Per `feedback_no_cheating.md` anti-drift discipline, the /073
per-symbol ATR axis — SUSPICIOUS-OOS-DOMINANT, closed at catalog level, NOT
advanced — must not silently carry into /074. The revert restores the established
cycle-2 baseline labeling; it is a revert, not a second axis.

- **Symbols:** UNCHANGED — BCH/LDO/TRX. V3_EXCLUDED_SYMBOLS check: none of
  BCH/LDO/TRX is in V3_EXCLUDED_SYMBOLS. PASS.
- **Labeling:** **REVERT** `V3_ATR_MULTIPLIERS_PER_SYMBOL` from `{"BCHUSDT":
  (2.0,1.25), "LDOUSDT": (1.5,1.25)}` (the /073 axis) back to `{}` (empty — all
  symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`). `label_mode` stays
  `"triple_barrier"` (already reverted at /073). Triple-barrier 21-candle (10080-min)
  timeout unchanged.
- **Features:** UNCHANGED — V3_FEATURE_COLUMNS = 14, the /059/060 anchor set. No
  feature added or removed. Cluster-importance check: N/A (no feature change).
- **Risk gates:** **`enable_regime_gate=False` → `True`** in the `RiskV2Config`
  constructed by `_build_v3_model` in `run_baseline_v3.py`. `regime_gate_symbols`,
  `regime_dd_threshold_pct=20.0`, `regime_vol_zscore_threshold=1.5` are ALREADY set
  in the runner (wired at /022) — only the enable flag flips. The gate is the
  6th-of-7 v3 risk primitives turning ON; the other 6 are unchanged.

### 3.1 Setup-commit code changes (enacting the axis)

1. `src/crypto_trade/features_v3/__init__.py` — `V3_ATR_MULTIPLIERS_PER_SYMBOL`
   reverted to `{}` (with a history-comment line).
2. `run_baseline_v3.py` — `enable_regime_gate=True` (one boolean); the stale
   `_expected_atr_per_symbol = {"BCHUSDT": (2.0,1.25), "LDOUSDT": (1.5,1.25)}`
   pre-flight assertion updated to expect `{}`; a NEW pre-flight assertion added
   verifying `enable_regime_gate is True` and `regime_gate_symbols == ("TRXUSDT",)`;
   `ITERATION_LABEL` bumped `"v3-073"` → `"v3-074"`.
3. `tests/` — a regression test added asserting the regime gate is enabled for TRX
   only, the gate is past-only (cannot peek at the current bar), and the
   `V3_ATR_MULTIPLIERS_PER_SYMBOL` revert holds.

ZERO new strategy/model code — `RiskV3Wrapper`, `_build_btc_regime_lookup`,
`_regime_gate_fires` are all already implemented and unit-tested
(`tests/strategies/ml/test_regime_gate.py` per the /022 lineage).

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted bands (cycle-2 axis-PASS criteria, anchored on /060)

- **Predicted IS monthly Sharpe Δ vs /060:** **+0.05** (CI: **[-0.15, +0.30]**).
  The counterfactual (Section 2.2) shows removing 3 net-positive IS TRX trades from
  the /060 roster is a small DRAG; the hypothesised IS lift comes only from the
  training-distribution shift (crash-regime bars dropped from TRX Optuna), which the
  counterfactual cannot measure. The band is wide and centred near zero to reflect
  this genuine uncertainty.
- **Predicted OOS monthly Sharpe Δ vs /060:** **+0.10** (CI: **[-0.10, +0.40]**).
  The counterfactual shows removing 6 net-negative OOS TRX trades is a small lift;
  TRX OOS-window stress bars are 8.9% of OOS bars.
- **Predicted frac_positive_paths:** ≈ 0.6444 ± 0.03 (CPCV is largely
  architecture-invariant; the gate removes a small number of TRX trades).
- **Falsifier:** if OOS monthly Sharpe Δ < -0.20 vs /060 (i.e. OOS Sharpe below
  -0.06), the hypothesis that removing crash-regime TRX trades is OOS-neutral-to-
  positive is rejected — the gate would be destroying OOS-productive TRX trades.

### 4.2 BCH IS sensitivity (mandated by `feedback_v3_cycle1_axis_pass_criteria.md`)

BCH carries the v3 IS edge (95.76% of /059 IS PnL; 176.68% of /060 IS PnL). The
regime gate `regime_gate_symbols=("TRXUSDT",)` fires ONLY on TRX — **BCH IS is
predicted byte-identical to /060** (73 trades, 45.2% WR, +79.45% net_pnl, per
`reports-v3/iteration_v3-060/in_sample/per_symbol.csv`). The gate cannot touch BCH.
This is a hard prediction and a positive control: if BCH IS shifts at all, the
single-axis discipline has been violated.

### 4.3 Holding-time-effect predictor (mandated by `feedback_v3_is_oos_regime_divergence.md`)

**Predicted mean trade duration change: ≈ 0 (Section 2.3 measured -0.35 candles on
the /060 TRX roster; median 0.0). Predicted median trade duration change: 0.**
AXIS A is holding-time-ORTHOGONAL — it removes whole trades by BTC-regime state, a
quantity uncorrelated with a trade's time-to-resolution. The barrier distances
(atr_tp=2.0, atr_sl=1.0), the 21-candle timeout, and the meta-labeling layer are
all unchanged. Per the regime-divergence rule, since the predicted duration change
is ≈ 0, the axis does NOT load the IS/OOS regime factor. **This is the load-bearing
reason AXIS A satisfies the hard constraint** — it is NOT a 4th holding-time-
extension axis.

Falsifier on the holding-time predictor: if the /074 backtest shows the TRX kept
roster mean duration shifts by > +1.5 candles vs the /060 TRX roster, the
orthogonality assumption is violated and the SUSPICIOUS-OOS-DOMINANT risk re-opens
— the Critic should flag it.

### 4.4 Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

Explicit estimate of how many trades change vs /060:

- **TRX IS trades:** /060 has 75 TRX IS trades; predicted /074 ≈ **70–74**
  (gate suppresses ≈ 1–5; counterfactual point estimate 3, but the
  training-distribution shift can change Optuna's TRX model and thus the roster, so
  the band is wider than the literal counterfactual). Falsifier: if TRX IS trade
  count is UNCHANGED at exactly 75, the gate did not fire → NULL-RESULT (the gate
  is mis-wired or no TRX candidate landed on a stress bar).
- **TRX OOS trades:** /060 has 54; predicted /074 ≈ **46–53** (gate suppresses
  ≈ 1–8; counterfactual point estimate 6).
- **BCH IS+OOS trades:** UNCHANGED (73 IS / 37 OOS) — gate targets TRX only.
- **LDO IS+OOS trades:** UNCHANGED (11 IS / 11 OOS) — gate targets TRX only.
- **Aggregate IS trades:** /060 159 → predicted ≈ 154–158.
- **Aggregate OOS trades:** /060 102 → predicted ≈ 94–101.

### 4.5 OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered SUSPICIOUS gate: if the /074 OOS/IS monthly Sharpe ratio > 3.0,
the axis is classified SUSPICIOUS regardless of absolute OOS Sharpe magnitude.**
This gate fires unconditionally per the memory rule. AXIS A is predicted NOT to trip
it — the holding-time-effect predictor (Section 4.3) shows ≈ 0 duration change, so
the IS/OOS regime divergence should not be loaded; predicted OOS/IS ratio ≈ 0.2–1.5
(anchor /060 is 0.169). But the gate is pre-registered and binding: if /074 comes
back with OOS/IS > 3.0, the axis is SUSPICIOUS and does NOT advance, even though the
mechanism analysis predicted otherwise.

---

## Section 5 — Risk Mitigation

This iteration's axis IS itself a risk-mitigation primitive (a regime-conditional
kill switch). The mitigation discussion is therefore about whether the gate is
correctly bounded and what protects against it misfiring.

- **Past-only discipline.** The gate's BTC drawdown_30d and vol_zscore_30d are
  computed via `.shift(1)` so the current bar's BTC close is never used. The gate
  finds the most recent BTC bar with `open_time STRICTLY LESS THAN` the symbol's
  bar `open_time` (`np.searchsorted(..., side="left") - 1`). This is verified by
  the existing adversarial test `test_regime_gate.py` and a new /074 regression
  test re-asserts it. No look-ahead.
- **IS-calibrated thresholds.** `regime_dd_threshold_pct=20.0` is the IS-90th
  percentile of BTC drawdown_30d; `regime_vol_zscore_threshold=1.5` is the IS-95th
  percentile of BTC vol_zscore_30d (calibrated at /022, EDA SHA b728313). These are
  unchanged — /074 does NOT re-tune the thresholds (re-tuning would be a second
  axis). The thresholds were calibrated on IS data only.
- **Simulated historical effect.** Section 2.2 IS the simulated historical effect:
  on the /060 trade roster the gate would have suppressed 3 IS TRX trades
  (+1.02 wpnl) and 6 OOS TRX trades (-1.06 wpnl). Section 2.5 shows the gate fires
  on 19.1% of IS bear/chop BTC bars and 1.3% of IS bull bars — concentrated in the
  crash regime, near-silent in the bull regime, as designed.
- **Scope bound.** `regime_gate_symbols=("TRXUSDT",)` — the gate touches TRX only.
  BCH (the IS-edge carrier) and LDO are untouched. If the gate misfires, the blast
  radius is TRX's trade count, which the OOS-trade falsifier (Section 4.1) and the
  trade-rate floor catch.
- **Failure-stop.** Section 4.1 falsifier: OOS Sharpe Δ < -0.20 → hypothesis
  rejected. Section 4.3 falsifier: TRX kept-roster mean duration shift > +1.5
  candles → orthogonality violated. Section 4.5 falsifier: OOS/IS > 3.0 → SUSPICIOUS.

---

## Section 6 — Risk Management Design

v3 7-primitive risk gate stack. /074 turns primitive 9 (regime-conditional kill
switch) ON for TRX; all other primitives unchanged from the /059/060 baseline.

| # | Primitive | /074 state | Fire-rate prediction |
|---|---|---|---|
| 1 | Feature z-score OOD (z>2.0) | ON, unchanged | baseline |
| 2 | Hurst regime check | ON, unchanged | baseline |
| 3 | ADX gate (ADX>20) | ON, unchanged | baseline |
| 4 | Low-vol filter (bottom-third ATR) | ON, unchanged | baseline |
| 5 | Vol-adjusted sizing (TRX floor 0.5) | ON, unchanged | baseline |
| 8 | Per-symbol PnL cap | OFF (closed /020) | n/a |
| **9** | **Regime-conditional kill switch (TRX)** | **ON (the /074 axis)** | **fires on ≈ 8.9% of TRX OOS candidate bars, ≈ 14.9% of TRX IS candidate bars (Section 2.5 BTC bar-level rate; trade-level suppression ≈ 3 IS / 6 OOS per the /060 counterfactual)** |
| 10 | Direction-asymmetric kill switch | OFF (reverted /051) | n/a |
| 11 | Per-symbol drawdown brake | OFF (closed /054) | n/a |

**Regime coverage analysis.** The regime gate is the v3 stack's only BTC-macro-
conditional primitive. Primitives 1-4 are per-symbol feature/indicator gates;
primitive 5 sizes by per-symbol vol. None of them sees the BTC crash regime. The
gate fills that coverage gap for TRX — the symbol that carried the FTX/LUNA-crash
PBO=1.0 cells (TRX/2022-10, TRX/2023-01; a standing BASELINE_V3.md outstanding
constraint). The gate fire-rate profile (19.1% IS bear/chop bars, 1.3% IS bull
bars, 8.9% OOS bars) confirms it activates in the crash/bear regime and stays
quiet in the bull regime — it is a targeted crash-regime gate, not a blanket
de-risking switch.

**`gate_stats_summary()` reporting.** `RiskV3Wrapper.gate_stats_summary()` already
emits `regime_gate_fires` and `regime_gate_fire_rate` per symbol — the engineering
report Phase 6 will record the actual TRX fire counts and the Critic Phase 7.5 will
cross-check them against this Section's predictions.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure (probability ≈ 35%): INERT.** The counterfactual
(Section 2.2) shows the gate suppresses only 3 IS + 6 OOS TRX trades on the /060
roster — a small-N intervention. If the training-distribution shift (the crash-
regime bars dropped from TRX's Optuna landscape) does not materially change the TRX
model — plausible because TRX's 24-month training windows mostly do not include
2022-10/2023-01, so for most walk-forward cells the gate removes few-to-zero
training bars — then /074 lands within the [-0.10,+0.10] IS noise band and/or the
[-0.20,+0.20] OOS noise band → INERT-AT-EXPLORATION. The metric signature: IS+OOS
Sharpe within the noise bands, TRX trade count down by only 1-5/IS and 1-8/OOS, BCH
and LDO byte-identical to /060.

**Second failure (probability ≈ 25%): NEGATIVE.** The counterfactual shows the 3
suppressed IS trades are net *positive* (+1.02 wpnl, 66.7% WR). If the gate
suppresses net-positive TRX trades in the actual roster more than it suppresses
net-negative ones — i.e. if the BTC-regime-stress signal is anti-correlated with
TRX trade quality rather than correlated — IS Sharpe could fall below the -0.10
NEGATIVE threshold. The metric signature: IS Sharpe Δ < -0.10, TRX IS net_pnl
worse than /060's -23.04%, suppressed-trade WR > kept-trade WR in the engineering
report's gate-stats breakdown.

**Tail failure (probability ≈ 10%): SUSPICIOUS-OOS-DOMINANT.** AXIS A is
holding-time-orthogonal by mechanism (Section 2.3 / 4.3), so this is a tail. It
could occur if the training-distribution shift incidentally produces a TRX model
that holds trades longer (e.g. a model trained without crash bars learns a
lower-turnover regime). The Section 4.3 holding-time falsifier (kept-roster mean
duration shift > +1.5 candles) is the detector; the Section 4.5 OOS/IS > 3.0 gate
is the classifier. If both fire, /074 is SUSPICIOUS and the regime-gate axis is
re-examined as a holding-time-loading axis despite the mechanism prediction.

**What the gates should catch.** The CPCV `frac_positive_paths` and PBO are
largely invariant to a small TRX trade removal — they will not move much. The
discriminating signals are: (a) the IS/OOS Sharpe deltas vs /060; (b) the
`regime_gate_fires` count in `gate_stats_summary()` — if it is 0, the gate
mis-wired (NULL-RESULT); (c) the BCH/LDO byte-identity check (single-axis
discipline); (d) the TRX kept-roster duration vs /060 (holding-time orthogonality).

Process predictions: P1 — wall-clock under the 1.0h budget (≈ 90% confidence;
/071/072/073 all 0.65-0.70h, this axis is cheaper than a labeling change). P2 —
the new pre-flight regime-gate assertion passes on the first Phase 5.5 gate run
(≈ 80%; the /073 setup hit 4 stale assertions, so a stale-assertion BLOCK is a
real ≈ 20% risk — the QE must update the `_expected_atr_per_symbol` assertion in
the same setup commit). P3 — integration runs clean, no runtime error (≈ 90%).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

This is an EXPLORATION; it cannot MERGE. Section 8 LOCKs the axis-classification
taxonomy per `feedback_v3_cycle1_axis_pass_criteria.md` cycle-2 thresholds. The
classifier is evaluated in this DISJUNCTIVE ORDER (SUSPICIOUS first, then NEGATIVE,
then PROMISING, then INERT) — established /071/073 precedence.

**8.1 — PROMISING-AT-EXPLORATION** (all four conjuncts required):
- IS monthly Sharpe Δ ≥ **+0.10** vs /060 (i.e. IS Sharpe ≥ +0.9325), AND
- OOS monthly Sharpe Δ ≥ **+0.20** vs /060 (i.e. OOS Sharpe ≥ +0.3403), AND
- frac_positive_paths ≥ **0.50**, AND
- no Critic methodology FAIL (13 checks + §11 anti-pattern scan).

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR — either gate fails):
- IS monthly Sharpe Δ < **-0.10** vs /060 (IS Sharpe < +0.7325), OR
- OOS monthly Sharpe Δ < **-0.20** vs /060 (OOS Sharpe < -0.0597).

**8.3 — INERT-AT-EXPLORATION:**
- IS monthly Sharpe Δ within **[-0.10, +0.10]** vs /060, OR OOS monthly Sharpe Δ
  within **[-0.20, +0.20]** vs /060 (the noise band), and not SUSPICIOUS.

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes
classification PRECEDENCE over NEGATIVE and INERT when concurrent, per the
/071/073 precedence rule, with NO magnitude qualifier):
- **OOS/IS monthly Sharpe ratio > 3.0** (`feedback_v3_oos_is_ratio_gate.md` —
  fires unconditionally regardless of absolute OOS Sharpe), OR
- **SUSPICIOUS-OOS-DOMINANT sub-mode:** IS shift < 0 AND OOS shift ≥ +0.20, OR
- **holding-time-orthogonality violation:** /074 TRX kept-roster mean duration
  shifts by > +1.5 candles vs the /060 TRX roster (Section 4.3 falsifier) — this
  would mean the axis loaded the regime factor despite the mechanism prediction.

**8.5 — NULL-RESULT:** `regime_gate_fires` total = 0 in `gate_stats_summary()`
(the gate never fired — mis-wired or no TRX candidate landed on a stress bar);
the trade roster is then byte-identical to /060 and the axis produced no effect.

**Evaluation order:** SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) →
PROMISING (8.1) → INERT (8.3). The first matching classification is canonical.

No BASELINE_V3.md update — EXPLORATIONs never update the baseline. A
PROMISING-AT-EXPLORATION outcome carries the axis forward to the cycle-2
CONFIRMATION (iter-v3/081 or later) as a candidate ingredient; it is NOT a MERGE
signal in itself.

---

## Section 9 — Library Stack Declaration

No new library is introduced. The regime gate uses only `numpy` and `pandas`
(already pinned). Versions in effect (per the /059 baseline reproducibility stamp):

- lightgbm: 4.6.0
- optuna: 4.8.0
- numpy: 2.2.6
- pandas: 3.0.0
- scikit-learn: 1.8.0
- scipy: 1.17.0
- statsmodels: 0.14.6 (ADF — Critic Check 5)
- pyarrow: 23.0.1
- mlfinlab / pypbo / fracdiff: not invoked by this axis (the regime gate is
  pure-numpy; CPCV/PBO/PSR reporting is unchanged from /059).

Walk-forward harness: the embargo (22 candles) + REQUIRED_GAP (66) are unchanged —
the regime gate changes neither the label horizon nor the symbol count.

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, the /074 axis was selected by
the QR with committed EDA backing, NOT by an orchestrator ad-hoc pick.

- **EDA SHA:** `b5e42f6` — `analysis/iteration_v3-074/axis_selection_eda.py`
  (dual-purpose: PART 1 regime diagnostic + PART 2 axis selection).
- **Setup commit SHA:** (backfilled after the setup commit).
- **Orchestrator framing:** the orchestrator did not pre-commit an axis. The task
  defined a HARD CONSTRAINT (holding-time-orthogonal OR regime-diagnostic) and
  named candidate families (NEW feature family, regime-conditional kill switch,
  entry-timing axis, model architecture, IS/OOS regime-stratified diagnostic). The
  QR evaluated three concrete candidates (A regime-conditional kill switch, B
  distinct-feature meta-labeling, C entry-timing shift) on IS-only data and chose
  AXIS A.

**How AXIS A satisfies the holding-time-orthogonal-OR-regime-diagnostic hard
constraint — both limbs:**

- **Limb A (holding-time-ORTHOGONAL):** the regime gate is a BINARY kill switch.
  It suppresses a TRX candidate signal to NO_SIGNAL on a BTC-regime-stress bar,
  BEFORE the model is consulted. It removes WHOLE trades; it does not touch the
  SL/TP barrier distances, the 21-candle timeout, or any meta-labeling filter. A
  trade the gate lets through is bit-identical to the baseline trade. The
  holding-time-effect predictor (Section 2.3) confirms this empirically: kept-vs-
  full TRX roster mean duration Δ = -0.35 candles, median Δ = 0.0 — near-zero, and
  SLIGHTLY NEGATIVE (the opposite direction from the holding-time-extension
  family). Per `feedback_v3_is_oos_regime_divergence.md`, an axis with ≈ 0
  predicted duration change does NOT load the IS/OOS regime factor. AXIS A is NOT a
  4th holding-time-extension axis — it clears limb A.
- **Limb B (regime-diagnostic):** the EDA's PART 1 IS a dedicated IS/OOS
  regime-stratified diagnostic — it splits the IS window into a bear/chop
  sub-period (2022-09→2023-12, monthly Sharpe -0.0242) and a bull sub-period
  (2024-01→2025-03, monthly Sharpe +0.5195) and characterizes them against the OOS
  uptrend (+0.0405). This formally measures the regime factor that /065/071/073
  keep loading and identifies the IS bear/chop sub-period as the structural drag.
  So the iteration discharges limb B as a side deliverable regardless of the AXIS A
  backtest outcome.

AXIS A satisfies the hard constraint by BOTH limbs. AXIS B (distinct-feature
meta-labeling) was rejected because meta-labeling filtration is a holding-time-
EXTENSION axis (the saturated family — a 4th such axis would reproduce
SUSPICIOUS-OOS-DOMINANT). AXIS C (entry-timing shift) was not selected because,
while borderline-orthogonal, it is a knob with no EDA-identified bottleneck and a
labeling-adjacent look-ahead surface — `feedback_v3_axis_selection_quant_discipline.md`
forbids speculative knobs without a quantitative basis.

**Re-evaluation justification.** The regime gate was tested once at iter-v3/022
(TRX, NEGATIVE-clean-PARTIALLY-EFFECTIVE). That verdict was produced at the BIASED
pre-walk-forward-fix baseline. Per `feedback_v3_walkforward_lookahead_bug.md`,
pre-fix verdicts are eligible for re-evaluation in the post-fix landscape, and
BASELINE_V3.md's "Dead Ideas" section explicitly marks pre-fix cycle-4 verdicts as
re-evaluation-eligible. /074 is the regime gate's first post-walk-forward-fix
data point under the unified 10-seed-lineage architecture.

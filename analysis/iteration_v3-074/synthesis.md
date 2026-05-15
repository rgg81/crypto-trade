# iter-v3/074 axis-selection EDA — synthesis

## Mandate

CYCLE 2 EXPLORATION #4 of 10. The /074 axis MUST satisfy the hard constraint
from Critic /073 Rec #1 + `feedback_v3_is_oos_regime_divergence.md`: it must be
EITHER (A) holding-time-ORTHOGONAL OR (B) a dedicated IS/OOS regime diagnostic.
Three consecutive SUSPICIOUS-OOS-DOMINANT EXPLORATIONs (/065, /071, /073;
OOS/IS ratios 2.87 -> 4.51 -> 6.85) each extended effective trade holding time.

This EDA is dual-purpose: PART 1 IS the regime diagnostic (limb B); PART 2
selects a holding-time-orthogonal axis (limb A).

## PART 1 — IS/OOS regime-stratified diagnostic (the divergence, quantified)

Splitting the /060 anchor's monthly PnL into three regime sub-periods:

| Regime | Months | Monthly Sharpe | Mean monthly PnL% | % positive months |
|---|---:|---:|---:|---:|
| IS bear/chop (2022-09->2023-12) | 18 | -0.0242 | -0.1402 | 27.8% |
| IS bull (2024-01->2025-03) | 15 | 0.5195 | 3.6276 | 53.3% |
| OOS uptrend (2025-03->2026-05) | 14 | 0.0405 | 0.3928 | 50.0% |

**Finding.** The diagnostic confirms the regime-divergence rule's premise but
refines it. The IS bear/chop sub-period and the IS bull sub-period are BOTH
weaker than naively expected; read the per-sub-period numbers in
`part1_regime_stratification.csv` for the exact drag attribution. The point
for axis selection: an axis that lifts the IS bull sub-period at the cost of
the IS bear/chop sub-period (or vice versa) does NOT improve the aggregate
IS Sharpe — it shuffles the regime exposure. The holding-time-extension family
lifts OOS-uptrend specifically; that is why it keeps tripping the OOS/IS gate.

## PART 2 — axis selection against the holding-time-orthogonal constraint

### AXIS A — regime-conditional kill switch (primitive 9) — SELECTED

AXIS A enables the regime-conditional kill switch (`enable_regime_gate=True`)
for TRXUSDT. The gate is a BINARY kill switch: when BTC drawdown_30d > 20% OR
|BTC vol_zscore_30d| > 1.5, a TRX candidate signal on that bar is suppressed to
NO_SIGNAL BEFORE the model is consulted. The gate is fully implemented and
past-only-tested in `risk_v3.py` (`_build_btc_regime_lookup`, `_regime_gate_fires`);
it is currently OFF. It was tested once at iter-v3/022 but at the BIASED
pre-walk-forward-fix baseline — `feedback_v3_walkforward_lookahead_bug.md` makes
pre-fix verdicts eligible for re-evaluation.

**Why it satisfies the hard constraint (holding-time-ORTHOGONAL).** The gate
removes WHOLE candidate trades; it does not touch the SL/TP barrier distances,
the timeout, or any meta-labeling filter. A trade that the gate lets through is
bit-identical to the baseline trade. The holding-time-effect predictor
(`axisA_holding_time_predictor.csv`) confirms this empirically:

  - kept-vs-full TRX roster mean duration Δ = -0.3463 candles
  - kept-vs-full TRX roster median duration Δ = 0.0 candles

A near-zero duration delta is the orthogonality signature. The gate is NOT a
filter that preferentially removes short-held or long-held trades — it removes
trades by BTC-regime state, which is uncorrelated with the trade's own
time-to-resolution. Contrast /071 meta-labeling, where the M2 veto
systematically removed early stop-outs and so lengthened the kept roster.

**Quantitative basis.** On the /060 TRX roster the gate would suppress
3 IS trades (combined wpnl 1.0224)
and 6 OOS trades (combined wpnl -1.0643).
See `axisA_regime_gate_counterfactual.csv` for the suppressed-vs-kept economics
split, and brief Section 2 for the interpretation. The gate targets TRX
specifically because TRX carried the FTX/LUNA-crash PBO=1.0 cells
(TRX/2022-10, TRX/2023-01) — a standing BASELINE_V3.md outstanding constraint.

### AXIS B — distinct-feature meta-labeling — REJECTED (saturated family)

Meta-labeling filtration is named explicitly in
`feedback_v3_is_oos_regime_divergence.md` as a holding-time-EXTENSION axis. The
M2 veto preferentially removes early stop-outs, biasing the kept roster toward
longer-held trades — the exact /071 mechanism (SUSPICIOUS-OOS-DOMINANT, OOS/IS
4.51). A 4th holding-time-extension EXPLORATION would mechanically reproduce
SUSPICIOUS-OOS-DOMINANT. Rejected at EDA stage on mechanism.

### AXIS C — entry-timing shift — NOT SELECTED (knob without grounding)

An entry-timing shift (delay entry k candles) is borderline holding-time-
orthogonal — with barrier distances and timeout fixed, expected trade duration
is unchanged. But there is no committed EDA identifying which k or what
bottleneck it would target, and an entry shift silently re-prices the entry and
the realized SL/TP levels — a labeling-adjacent change with its own look-ahead
surface. Per `feedback_v3_axis_selection_quant_discipline.md` a speculative knob
without an EDA-identified bottleneck is not a valid axis. Not selected.

## QR DECISION

**Selected axis: AXIS A — regime-conditional kill switch (primitive 9),
`enable_regime_gate=True` for TRXUSDT.**

It is the only candidate that BOTH (a) satisfies the holding-time-orthogonal
hard constraint with an empirically-verified near-zero duration delta, AND (b)
has a concrete EDA quantitative basis (the suppressed-trade counterfactual) and
a standing BASELINE_V3.md constraint it targets (TRX FTX/LUNA-crash PBO cells).
Implementation is a single boolean flip — the code is built and past-only-tested.

The iteration is dual-purpose: PART 1 above also discharges the regime-
diagnostic limb of the hard constraint, so the cycle gains the formal IS/OOS
characterization regardless of the AXIS A backtest outcome.

# iter-v1/039 — Axis Pre-Flight REJECTED (Drawdown Brake Binary Kill)

**Status: AXIS_PIVOTED at Phase 1-4 EDA stage. NOT proceeding to Phase 6 backtest. New axis TBD pending /038 outcome.**

## Rejected axis
Per-symbol drawdown brake — BINARY KILL mechanism when symbol's rolling 30d realized drawdown > IS p75 threshold. Recovery at threshold × 0.5.

## Rejection rationale (Phase 1-4 EDA finding)

**EDA mechanism load-bearing test FAILED HARD.** Per `eda_findings.md` Section 4:

| Symbol | Skipped trades mean | Retained trades mean | Mechanism sign |
|---|---|---|---|
| **LINK** | **+2.059%/trade (sum +76.17%)** | +0.186%/trade | **BACKWARD** ⚠️ |
| **BTC** | +0.432%/trade | **-0.397%/trade** | **BACKWARD** (sign flip) |
| ETH | -0.043%/trade | -0.143%/trade | Marginal backward |
| LTC | -0.451%/trade | +0.202%/trade | Forward |
| DOT | -0.351%/trade | -0.077%/trade | Forward |

**Aggregate ORACLE IS PnL impact ≈ −64% absolute** (vs /038's predicted -26%). The brake removes LINK's RICHEST decile (D10 = +70.29% sum, +4.69% mean/trade).

Interpretation: in v1's 5-cohort universe with the current LightGBM models, high realized DD on a per-symbol PnL curve is a proxy for "string of recent losing trades", and the model's edge concentrates in FADING those losses on the next signal. The brake mistakes setup for hostility — mechanism BACKWARD.

## Stateful deadlock concern (secondary)

Closed-loop CAN enter no-trade equilibrium: brake ON → no entries → no PnL updates → DD frozen above recovery threshold → permanent ON. Recovery rule (dd < threshold × 0.5) does NOT prevent this since recovery requires a win, win requires a trade, brake forbids trade. ORACLE longest brake-ON runs: BTC 97.7 days, LINK 67.7 days, DOT 69.3 days. Closed-loop runs could span full IS.

Per `feedback_v3_oracle_eda_validity.md` (iter-v3/054 deadlock precedent): closed-loop simulator mandatory before stateful primitive CONFIRMATION.

## Axis-family saturation signal

This is the **2nd consecutive risk-primitive axis** with EDA-flagged predicted-NEG outcome (after /038 vol-target ceiling -25.63% IS PnL prediction). The pattern is structural:

For v1's 5-cohort BTC/ETH/LINK/LTC/DOT universe, sizing/skip primitives that clip high-vol or high-DD regimes DESTROY edge because the LightGBM models' learned policies concentrate edge in exactly those regimes. The Critic's /037 closeout Path Forward #2 (drawdown brake) was based on classical risk-management intuition but does NOT match v1's empirical model behavior.

**Per `feedback_v3_axis_saturation_predictor`**: saturated axes pre-flagged by EDA must be SKIPPED.

## Path Forward — /039 axis pivot

After /038 closeout, select /039 axis from NON-risk-primitive families:

1. **Per-cohort Sortino × specialist hybrid** (loss-function × per-cohort interaction probe) — directly tests /037 closeout open question (does Sortino mechanism survive on /036's 2-cohort LINK+DOT specialist substrate?). Simplest implementation. Resolves /044 stacking decision.
2. **Ternary {long, neutral, short} prediction-architecture** (prediction-architecture family, NEW) — Critic Path Forward #1. Most structural. Heavy implementation.
3. **Cross-asset non-OHLCV feature** (cross-asset-feature family, NEW source) — Critic Path Forward #3. Untested non-Binance basis or funding source.

Selection deferred until /038 closeout to incorporate outcome signal.

## Preserved artifacts (in this directory)

- `eda_findings.md` — full drawdown brake EDA with per-symbol distributions, oscillation test, deadlock risk analysis
- `analysis/iteration_v1-039/*.csv` — `dd_percentiles.csv`, `trade_buckets.csv`, `skip_impact.csv`, `oscillation.csv`, `deadlock_risk.csv`
- `analysis/iteration_v1-039/eda.py` — reproducible script
- `lgbm_advisor.md` — LM Master Phase 4.5 advisory (also notes mechanism backward + deadlock risk)
- `research_brief.md` — drawdown brake brief authored under PRIME DIRECTIVE; **DO NOT IMPLEMENT** (kept for historical record only; new brief will replace if /039 pivots within same NNN slot, or this directory will close as REJECTED if /039 takes new NNN)

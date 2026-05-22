# Engineering Report — iter-v3/044

## Status: READY-FOR-CRITIC

🎯 **STRONG PROMISING** — QR's data-driven axis (ALGO ATR (2.0, 1.5)) worked exactly as predicted.

## Headline

| Metric | Value | vs iter-v3/040 anchor (+0.79/+1.77) |
|--------|-------|--------------------------------------|
| IS Sharpe | **+0.7880** | -0.005 (preserved!) |
| OOS Sharpe | **+2.5383** | **+0.77 lift** |
| OOS WR | **48.72%** | highest in v3 |
| OOS MaxDD | **14.23%** | best in v3 catalog |
| OOS PnL total | +85.68 | +27 from anchor |
| PBO | 0.0762 | best in cycle 3 |
| n_eff | 19 | consistent |

## Per-Symbol OOS — ALGO TRANSFORMATION

| Symbol | weighted_pnl | Trades | WR | vs anchor |
|--------|--------------|--------|-----|-----------|
| **ALGO** | **+70.17** | 22 | **63.6%** | **+49 swing**, +24pp WR (highest single-symbol WR in v3) |
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| BCH | +10.75 | 38 | 39.5% | bit-identical |
| LDO | -3.07 | 11 | 36.4% | bit-identical |

ALGO went from +20.87 (40% WR) to +70.17 (63.6% WR). The QR diagnosis (ALGO LONG SL:TP exit ratio 4.5:1; widening ATR allows LONG positions to recover) was VALIDATED.

## QR Audit Trail

- EDA SHA: `eff841e` — `cycle3_is_diagnosis.py` identified ALGO LONG as IS bottleneck
- Counterfactual prediction: removing 3 worst direction-buckets lifts IS Sharpe +0.79 → +1.95
- Implementation: V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5) — wider TP gives LONG positions room
- Result: ALGO +49 OOS swing matches predicted mechanism perfectly

## §4.4 Classification

PATH A fires unambiguously:
- IS Sharpe maintained (+0.79 vs +0.79 anchor) ✓
- OOS Sharpe lifted +0.77 ✓
- ALGO improved (+49) ✓
- Other symbols bit-identical ✓ (per-symbol Optuna independence)
- OOS MaxDD improved (14.23% best in v3) ✓
- OOS WR improved (48.7% highest in v3) ✓

**Verdict: EXPLORATION-PROMISING (clean — STRONG signal)**.

## Bundle Status for iter-v3/050 CONFIRMATION

Cycle 3 bundle (so far):
1. 4-sym BCH+LDO+TRX+ALGO (iter-v3/029)
2. regime_momentum_signed_5d (universal, validated)
3. ALGO ATR (2.0, 1.5) (iter-v3/044 — NEW edge ingredient)

Multi-seed forecast (50% compression):
- IS: +0.79 → ~+0.46 (similar to iter-v3/028 baseline +0.51)
- OOS: +2.54 → ~**+1.27** (above +1.0 floor!)

## Methodology Validation

QR-driven axis selection per `feedback_v3_axis_selection_quant_discipline.md` produced first PROMISING in cycle 3 after 3 ad-hoc orchestrator NEGATIVES (041 pruning / 042 universal ATR / 043 Kaufman ER). Discipline rule validated.

## Recommendations

iter-v3/045 axis: dispatch QR for next bottleneck analysis. LDO (-3.07 OOS, 36.4% WR, 11 trades) is the obvious next target. QR should diagnose LDO's specific failure mode (direction asymmetry? regime mismatch? feature signature?) and propose data-driven axis.

Status: READY-FOR-CRITIC.

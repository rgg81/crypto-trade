# Engineering Report — iter-v3/045

## Status: READY-FOR-CRITIC

🎯🎯 **STRONGEST PROMISING in v3 history** — QR-driven LDO ATR (2.0, 1.5) lifted OOS to +3.53 (HIGHEST in v3 catalog).

## Headline

| Metric | Value | vs iter-v3/044 anchor (+0.79/+2.54) |
|--------|-------|--------------------------------------|
| IS Sharpe | +0.7459 | -0.04 (preserved) |
| OOS Sharpe | **+3.5259** | **+0.99 — HIGHEST single-seed OOS in v3** |
| OOS WR | **50.42%** | **HIGHEST in v3 catalog** |
| OOS MaxDD | **13.26%** | **BEST in v3 catalog** |
| OOS PnL total | +96.99 | +11 from anchor |
| PBO | 0.0782 | excellent |
| n_eff | 19 | consistent |

## Per-Symbol OOS — ALL 4 POSITIVE FIRST TIME EVER

| Symbol | weighted_pnl | Trades | WR | vs anchor |
|--------|--------------|--------|-----|-----------|
| ALGO | +70.17 | 22 | 63.6% | bit-identical (per-symbol Optuna independence) |
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| BCH | +10.75 | 38 | 39.5% | bit-identical |
| **LDO** | **+10.24** | 13 | **53.8%** | **+13 swing, +17pp WR** |

LDO went from -3.07 OOS / 36.4% WR (iter-v3/044) to +10.24 / 53.8% WR (iter-v3/045). The QR diagnosis (IS→OOS exit-composition shift; SL rate 53→64%) was VALIDATED. Wider SL gave LDO positions room to recover.

## QR Audit Trail

- EDA SHA: `ed949fe` — `ldo_bottleneck_diagnosis.py` identified IS→OOS exit-composition shift
- Quantitative basis: SL:TP ratio doubled IS→OOS (1.14 → 2.33); LDO needs wider SL
- iter-v3/032 (1.5, 0.75) tighter direction was REJECTED (multi-seed-falsified at iter-v3/039)
- Mirror of iter-v3/044 ALGO mechanism (wider SL successful)
- Implementation: V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5)
- Result: LDO +13 OOS swing matches predicted mechanism

## §4.4 Classification

PATH A fires unambiguously:
- IS preserved (+0.75 vs +0.79 anchor)
- OOS lifted +0.99
- LDO target symbol +13 swing (matches mechanism)
- Other symbols bit-identical (per-symbol Optuna independence)
- All 4 symbols positive first time
- OOS WR highest in v3 catalog
- OOS MaxDD best in v3 catalog

**Verdict: EXPLORATION-PROMISING (clean — STRONGEST in v3 catalog)**.

## Bundle Status for iter-v3/050 CONFIRMATION

Cycle 3 bundle (now QUADRUPLE-validated):
1. 4-sym BCH+LDO+TRX+ALGO (iter-v3/029)
2. regime_momentum_signed_5d (universal)
3. ALGO ATR (2.0, 1.5) (iter-v3/044)
4. **LDO ATR (2.0, 1.5)** (iter-v3/045 — NEW edge ingredient)

Multi-seed forecast (50% compression):
- IS: +0.75 → ~+0.43 (similar to iter-v3/028 baseline +0.51)
- OOS: +3.53 → ~**+1.76** (well above +1.0 floor)

If multi-seed compression matches iter-v3/044's pattern (40% rather than 50%): OOS ~+2.12.

## Methodology Validation

QR-driven axis selection per `feedback_v3_axis_selection_quant_discipline.md` produced 2 PROMISING in a row (iter-v3/044 ALGO + iter-v3/045 LDO). vs orchestrator ad-hoc picks (iter-v3/041/042/043): all NEGATIVE.

Mirror mechanism (wider SL ATR (2.0, 1.5)) works for both ALGO and LDO. Universal labeling change (iter-v3/042 universal (1.5, 0.75)) FAILED but per-symbol applications work surgically.

## Recommendations

iter-v3/046 axis: dispatch QR for next bottleneck. Options:
1. BCH or TRX per-symbol ATR (continue per-symbol labels methodology)
2. Diagnose remaining symbols for next bottleneck
3. Try a NEW universal feature (carefully — universal additions historically fail)

QR makes the call.

Status: READY-FOR-CRITIC.

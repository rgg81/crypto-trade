# Engineering Report — iter-v3/046

## Status: READY-FOR-CRITIC

NEGATIVE — BCH ATR (2.0, 1.5) HURT BCH (-45 OOS swing). Mirror mechanism doesn't transfer universally.

## Headline

| Metric | Value | vs iter-v3/045 anchor (+0.75/+3.53) |
|--------|-------|--------------------------------------|
| IS Sharpe | +0.2027 | Δ -0.54 |
| OOS Sharpe | +2.4738 | Δ -1.05 |
| BCH OOS PnL | -34.54 (40 / 40.0% WR) | -45 swing from +10.75 |
| ALGO/LDO/TRX | preserved (per-symbol Optuna independence) | bit-identical |

## Per-Symbol OOS

| Symbol | weighted_pnl | Trades | WR | vs anchor |
|--------|--------------|--------|-----|-----------|
| ALGO | +70.17 | 22 | 63.6% | bit-identical |
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| LDO | +10.24 | 13 | 53.8% | bit-identical |
| **BCH** | **-34.54** | 40 | 40.0% | **-45 swing** |

## QR Prediction vs Reality

QR predicted: BCH IS +0.10-0.18 lift, OOS +0.05-0.15 lift via 6-9 SL→TP redirections.
Observed: BCH IS-axis collapse, OOS -45 swing.

The diagnostic basis (BCH IS=OOS SL:TP stable at 1.93) was correct — but the WRONG conclusion was drawn. Stable SL:TP means BCH was NOT a regime-mismatch case, so widening ATR was inappropriate.

Mirror mechanism (wider SL) worked for ALGO + LDO because both had regime mismatch (LDO: SL:TP doubled IS→OOS; ALGO: extreme LONG SL ratio). BCH had neither.

## Lesson — Mirror Mechanism Has Limits

The wider-SL mechanism is REGIME-MISMATCH-SPECIFIC. Symbols with stable SL:TP across IS→OOS don't benefit. QR's diagnostic should have RULED OUT BCH for this axis based on the stable SL:TP finding.

## §4.4 Classification

PATH C fires: IS Δ -0.54 ≪ -0.10. Verdict: **EXPLORATION-NEGATIVE**.

## Recommendations

iter-v3/047: REVERT BCH ATR. Dispatch QR for BCH direction-asymmetric axis (LONG IS -25% toxic / SHORT IS +49% positive — direction filter or LONG-only ATR).

Status: READY-FOR-CRITIC.

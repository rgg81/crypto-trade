# Iteration v2/023 Diary

**Date**: 2026-04-15
**Type**: EXPLORATION (TRXUSDT as NEAR replacement)
**Parent baseline**: iter-v2/019
**Decision**: **NO-MERGE** on 10-seed means (both below 1.0), but STRONG balance signal

## Results

**Primary seed 42** (significantly better):
| Metric | iter-v2/019 (NEAR) | iter-v2/023 (TRX) |
|---|---|---|
| IS monthly Sharpe | +0.50 | **+0.74** (+48%) |
| IS MaxDD | 72.24% | **50.99%** (−29%) |
| IS trade Sharpe | +0.57 | **+0.86** (+51%) |
| IS DSR | +17.59 | **+20.37** |
| OOS monthly Sharpe | +2.34 | +1.79 (−23%) |
| OOS MaxDD | 24.39% | 35.61% (+46%) |
| OOS/IS ratio | 21.1 | **2.64** (much more balanced) |

**10-seed mean**:
| Metric | Value |
|---|---|
| IS monthly Sharpe | **+0.6118** |
| OOS monthly Sharpe | **+0.6996** |
| **Balance ratio** | **1.14x** ← **excellent balance** |
| OOS trade Sharpe | +0.9393 |
| Profitable seeds | 10/10 |

## Assessment

**Win**: balance achieved. Ratio 1.14x is as balanced as possible
(target 1.0-2.0). IS improved from iter-019's primary +0.50 to
mean +0.61. 10/10 profitable.

**Loss**: both means below 1.0. iter-019 had unbalanced but HIGH
primary OOS (+2.34). iter-023 has balanced but LOW means. The
absolute level dropped.

**Seed-variance issue**: primary seed 42 outlier-high (OOS +1.79).
Other seeds: 123 (+0.63), 456 (+0.55), 789 (+0.45), 1001 (+1.07),
1234 (+0.83), 2345 (+0.08), 3456 (+0.19), 4567 (+0.97), 5678 (+0.43).
Mean dragged down by 2345 and 3456 below +0.3.

**Per-symbol contribution** (iter-023 primary):
- XRP: +83.62 IS, +47.12 OOS
- SOL: +31.17 IS, +36.54 OOS
- DOGE: +22.43 IS, +29.81 OOS
- **TRX: +27.54 IS**, −3.44 OOS ← **positive IS contributor!**

TRX's IS contribution is strictly better than NEAR's. The OOS drag
(−3.44) is similar to NEAR's (−2.20). TRX is a NET improvement
on IS without meaningfully hurting OOS.

## Why the 10-seed mean dropped below 1.0

Each seed produces a different Optuna hyperparameter set and thus
a different trade distribution. The risk gates (BTC trend + hit-rate)
were originally tuned on iter-019's seed 42 trades. On different
seeds with different trade timing, the gates fire at different moments
and miss different drawdowns.

**The iter-019 risk gates are not robust across seeds**. Seed 42
gets the full benefit; other seeds get partial benefit.

## Lesson

Sparse strategies (fewer than 50 trades/seed/year) have high
seed-level variance. To reach higher 10-seed mean, need:
1. More trade density (more symbols OR more trades per symbol)
2. More robust per-seed selection (bigger Optuna space)
3. Feature engineering to reduce model output variance

## Next iteration (iter-v2/024)

Try **adding TRX as a 5th symbol** (Model I) while KEEPING NEAR
(Model H). Rationale:
- TRX's IS contribution is +27.54 (strong positive)
- NEAR's IS contribution is −20.50 (negative drag)
- TRX + NEAR together: net +7.04 IS
- iter-019 without TRX: −20.50 IS contribution
- **Net IS improvement expected: +27.54**

More importantly, 5 symbols = more trade density. Instead of 461
trades across 4 symbols, we'd have ~600 trades across 5 symbols.
Higher density reduces per-month variance, which directly lifts
monthly Sharpe.

Concentration check: iter-019 XRP was 41.39%. With 5 symbols,
XRP's share will drop further (~35%). Safe.

## MERGE / NO-MERGE

**NO-MERGE**. 10-seed means below 1.0 threshold. But the balance
signal is strong. iter-v2/024 will build on iter-v2/019 (keep NEAR)
and add TRX as a 5th symbol (not replace).

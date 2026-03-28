# Iteration 069 — Research Brief

**Type**: EXPLOITATION (cooldown parameter optimization)
**Date**: 2026-03-28
**Previous**: Iteration 068 (MERGE — cooldown=2, OOS Sharpe +1.84)

---

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process. The reporting layer splits trade results at `OOS_CUTOFF_DATE`.

---

## Hypothesis

Cooldown=2 was chosen based on EDA analysis (targeting after-SL trades with WR 42%). The optimal value may differ. Test cooldown={1, 3, 4} and compare against baseline cooldown=2.

## Research Analysis

### Category E: Trade Pattern Analysis (from iter 068 EDA)

Baseline (cooldown=0) gap distribution:
- ≤1 candle: 81% of trades
- ≤3 candles: 85% of trades
- >3 candles: 15% of trades

Expected trade reduction per cooldown value:
- cooldown=1: ~7% fewer trades (removes only 0-candle gaps)
- cooldown=2: ~24% fewer (observed in iter 068)
- cooldown=3: ~30-35% fewer
- cooldown=4: ~40% fewer

### Category D: Sensitivity Analysis

This is a classic hyperparameter sweep. The optimal cooldown balances:
- Too low (0-1): allows marginal rapid re-entries
- Too high (4+): misses good trading opportunities
- Sweet spot: reduces loss streak piling while preserving profitable signals

## Proposed Change

### Quick Sweep Protocol

1. Run single-seed (seed=42 only) backtests with cooldown={1, 3, 4}
2. Compare IS and OOS metrics
3. If any value clearly beats cooldown=2, run full ensemble for that value
4. If cooldown=2 remains best, document as NO-MERGE (nothing to change)

### What stays the same
Everything identical to iter 068 except the cooldown value being tested.

### One-variable change
Only `cooldown_candles` varies (1, 3, or 4 vs baseline 2).

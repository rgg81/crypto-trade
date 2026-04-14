# Iteration v2/012 Research Brief

**Type**: EXPLOITATION (drawdown-brake feasibility study)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/012` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation

iter-v2/005's weakest dimension is OOS MaxDD = **59.88%** on seed 42
(45.33% when measured from daily-aggregated returns). Compared to
v1 iter-152's 21.81% MaxDD, v2 is **more than double the drawdown
exposure**. This is the single reason v2 cannot carry more than a
~30% satellite weight in any combined portfolio.

iter-v2/001's skill deferred the **drawdown brake** as Primitive #5.
The brake was not implemented because iter-v2/001 needed to prove
the core 4 MVP gates first. Four iterations later, those 4 gates
are stable and the baseline is seed-robust. The brake is the natural
next risk primitive.

**Pre-registered from iter-v2/001 skill**:
> "5. Drawdown brake | Deferred (iter-v2/002) | Portfolio DD > 5%
> → shrink to 0.5x. > 10% → flatten."

iter-v2/012 implements and validates this primitive.

## Hypothesis

A portfolio-level drawdown brake that **halves trade weight when
running DD > 6%** and **zeros trade weight when running DD > 12%**
will:

1. **Reduce MaxDD meaningfully** (target: 59.88% → <40%)
2. **Preserve Sharpe within noise** (target: keep 10-seed mean > +1.2)
3. **Improve Calmar** (mechanical consequence of #1 and #2)
4. **Fire at tail events**, not on routine drawdowns

The 6%/12% thresholds are slightly tighter than iter-v2/001's
deferred 5%/10% draft. Rationale: v2's per-trade volatility is
roughly 2-3× v1's (higher-vol satellite symbols), so the brake
should fire a touch later in raw % terms. We want the brake to
activate on **regime-scale** events, not normal noise. 6%/12% maps
to roughly a 1-month bad drawdown in v2's profile (where typical
1-month DDs are 3-5%).

## Methodology — feasibility study, not runner rewrite

This iteration does NOT modify `RiskV2Wrapper` yet. Instead, we run
a **post-hoc simulation** on iter-v2/005's existing OOS trade stream
at `reports-v2/iteration_v2-005/out_of_sample/trades.csv`.

### Algorithm (portfolio-level, cross-symbol)

1. Load the iter-v2/005 OOS trades sorted by `open_time` (entry time).
2. Initialize `running_pnl = 0` and `peak_pnl = 0`.
3. For each trade in entry-time order:
   a. Compute `running_dd_pct = (running_pnl - peak_pnl)` (non-positive).
   b. If `|running_dd_pct| ≥ dd_brake_flatten` (12%): new trade's
      effective weight = 0. Trade contributes 0 to running PnL.
   c. Else if `|running_dd_pct| ≥ dd_brake_shrink` (6%): new trade's
      effective weight = 0.5 × original. Trade contributes
      0.5 × weighted_pnl.
   d. Else: trade runs at full weight.
   e. Update `running_pnl += effective_weighted_pnl`,
      `peak_pnl = max(peak_pnl, running_pnl)`.
4. Recompute daily-aggregated Sharpe, MaxDD, PF on the modified
   trade stream.

### Why post-hoc simulation is a valid test

The brake only **gates new positions**; it does not close existing
ones. The original trades' open_time and PnL are independent of
the brake's decision — the brake only affects **weight**. Therefore
the simulation is equivalent to a live brake implementation with
one caveat: it uses `running_pnl` at the trade's **open_time**,
while a live brake would use `running_pnl` at **signal time**
(same candle's close_time of the previous bar). The difference is
≤1 bar (8h) and within the measurement noise of the brake.

If post-hoc simulation shows the brake improves metrics, iter-v2/013
will productionize it in `RiskV2Wrapper` with proper callback hooks.

### Configurations to test

| Config | Shrink threshold | Flatten threshold | Rationale |
|---|---|---|---|
| A | 5% | 10% | iter-v2/001 skill's original draft |
| B | **6%** | **12%** | **Recommended**: slightly tighter, matches v2 vol profile |
| C | 8% | 16% | Looser: only tail events |
| D | 4% | 8% | Aggressive: fires on mild drawdowns too |
| None | ∞ | ∞ | Baseline (iter-v2/005 as-is) |

Running 4 configs on post-hoc trades costs <5 seconds total.

## Pre-registered failure-mode prediction

Most likely failure mode: **the brake either fires too rarely to
matter (no MaxDD improvement) or fires too often and eats into
Sharpe**.

**If brake is too loose (Config C, 8%/16%)**: probably never fires
on iter-v2/005 OOS because running DD stays below 8% on this
seed. No MaxDD improvement.

**If brake is too tight (Config D, 4%/8%)**: fires on routine
drawdowns, shrinks profitable trades, Sharpe drops below +1.0.
MaxDD improves but Calmar regresses because cumulative PnL falls
faster than DD.

**Sweet spot**: Config A or B. Expected outcome for B (6%/12%):
- MaxDD: 59.88% → 35-45% (target <40%)
- Sharpe: 1.67 (seed 42) → 1.4-1.7 range (within noise)
- Calmar: improves 1.5-2x
- Brake fires 5-15 times over OOS (1-3% of trades)

**Decision criteria**:
- **Success (continue to iter-v2/013 productionization)**: at least
  one config achieves MaxDD < 45% AND Sharpe > +1.3
- **Failure (drawdown brake doesn't help on this dataset)**: no
  config passes both criteria. Conclude the brake is not a lever
  for iter-v2/005 and move on.

## Scope

- iter-v2/012 is **feasibility only**: post-hoc simulation on
  iter-v2/005 seed 42 OOS trades
- No `RiskV2Wrapper` changes
- No 10-seed validation (the point-estimate seed 42 OOS is enough
  to decide whether the brake is worth implementing)
- iter-v2/013 will productionize the winning config if feasibility
  passes

## Configuration

One new analysis script: `analyze_drawdown_brake.py`. Reads
iter-v2/005 OOS trades, applies 4 brake configs, reports metrics.

## Success Criteria

Decision depends on Config B (6%/12%) and Config A (5%/10%):
- **Continue**: one of them achieves MaxDD < 45% AND Sharpe > +1.3
- **Stop**: neither passes → close the brake lever for now

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged from iter-v2/005)

- Feature z-score OOD (|z| > 3)
- Hurst regime check (5th/95th IS percentile)
- ADX gate (threshold 20)
- Low-vol filter (atr_pct_rank_200 < 0.33)
- Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)

### 6.2 New gate — drawdown brake (POST-HOC SIMULATION)

- Portfolio-level: computed on the combined 4-symbol trade stream
- Shrink at 6% running DD (recommended config B)
- Flatten at 12% running DD
- Reset peak to max(peak, new_pnl) after each trade
- Fires only when entering new positions; does not close open ones

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary: the
brake either fires too rarely (no impact) or too often (Sharpe
drag). Config B (6%/12%) is the hypothesized sweet spot.

### 6.4 Expected gate firing rates on iter-v2/005 OOS (117 trades)

- Config A (5%/10%): expect 10-25 trade shrinks, 0-5 flattens
- Config B (6%/12%): expect 5-15 trade shrinks, 0-3 flattens
- Config C (8%/16%): expect 0-5 trade shrinks, 0 flattens
- Config D (4%/8%): expect 20-40 trade shrinks, 5-10 flattens

### 6.5 Black-swan replay

The iter-v2/005 OOS period contains two material drawdowns:
1. **2025-07-18 to 2025-08-22**: 5 consecutive bad days (NEAR, XRP)
2. **2025-10-30 onwards**: v2's largest single-day loss (-7.79%)

Both should be detectable via running DD > 6% and should trigger
the brake. If the brake fires during one of these episodes and
reduces cumulative DD, the hypothesis is validated.

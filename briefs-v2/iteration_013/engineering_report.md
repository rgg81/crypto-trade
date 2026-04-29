# Iteration v2/013 Engineering Report

**Type**: EXPLOITATION (productionize drawdown brake)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/013` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, XRP 47.75%)
**Decision**: **NO-MERGE** (concentration strict fail + cross-symbol brake contamination)

## Run Summary

| Item | Value |
|---|---|
| Runner | `run_baseline_v2.py` (ITERATION_LABEL=v2-013) |
| Models | 4 (E=DOGE, F=SOL, G=XRP, H=NEAR) — same as iter-v2/005 |
| Seeds | 10 (full MERGE validation) |
| Optuna trials/model | 10 |
| Wall-clock | ~50 min |
| New code | `apply_portfolio_drawdown_brake()` in `risk_v2.py`, wired into runner |

## 10-seed results

| Seed | Braked Sharpe | Unbraked | Δ | Brake shrink | Brake flatten | Fire rate |
|---|---|---|---|---|---|---|
| 42 | +1.5961 | +1.6708 | −0.075 | 12 | 40 | 11.3% |
| 123 | +1.3861 | +1.2871 | **+0.099** | 17 | 46 | 12.4% |
| 456 | +1.0986 | +1.5602 | −0.462 | 25 | 59 | 15.6% |
| 789 | **−0.1972** | +0.5648 | −0.762 | 29 | 61 | 17.7% |
| 1001 | +1.6577 | +1.9644 | −0.307 | 31 | 35 | 12.6% |
| 1234 | +2.3867 | +1.8895 | **+0.497** | 20 | 48 | 13.6% |
| 2345 | +0.4623 | +0.6852 | −0.223 | 9 | 48 | 12.9% |
| 3456 | +0.3936 | +0.3185 | **+0.075** | 24 | 69 | 18.6% |
| 4567 | +1.3737 | +1.7147 | −0.341 | 16 | 21 | 9.2% |
| 5678 | +1.3007 | +1.3193 | −0.019 | 8 | 60 | 14.7% |
| **Mean** | **+1.1458** | **+1.2976** | **−0.152** | 19.1 | 48.7 | 13.9% |

- **Profitable seeds**: 9/10 (only seed 789 negative)
- **Mean Sharpe drag**: −0.152 (−11.7% from baseline +1.297)
- **Primary seed 42 OOS MaxDD**: **16.41%** (baseline 59.88%, −73%)
- **Primary seed 42 OOS PF**: 1.5671 (baseline 1.457, +7.5%)

## The concentration strict fail

iter-v2/013 primary seed OOS per-symbol breakdown (using WEIGHTED PnL,
the convention from iter-v2/005's MERGE):

| Symbol | Trades | WR | Weighted PnL | Share |
|---|---|---|---|---|
| **XRPUSDT** | 27 | 55.6% | +46.84 | **78.55%** |
| DOGEUSDT | 31 | 48.4% | +26.06 | +43.70% |
| SOLUSDT | 37 | 37.8% | **−0.18** | −0.31% |
| NEARUSDT | 22 | 40.9% | **−13.08** | −21.94% |

**Compared to iter-v2/005 baseline**:

| Symbol | iter-v2/005 wpnl | iter-v2/013 wpnl | Δ |
|---|---|---|---|
| XRPUSDT | +44.89 | +46.84 | +1.95 |
| DOGEUSDT | +11.52 | +26.06 | **+14.54** |
| SOLUSDT | +28.89 | −0.18 | **−29.07** |
| NEARUSDT | +8.71 | −13.08 | **−21.79** |

### Why the concentration collapses

Root cause traced via trade-by-trade diff on DOGE's 31 OOS trades:

Trades 9-19 (11 trades) are the July-August 2025 bear stretch. In
iter-v2/005 they sum to **−21.50 weighted_pnl for DOGE**. In
iter-v2/013 the brake is in FLATTEN state throughout this window
(shadow equity DD ≥ 16%), so all 11 trades are zeroed. Net effect
on DOGE: **saves 21.5 of losses, adds +14.5 to DOGE's total**.

But SOL and NEAR during the SAME flatten window had mostly winning
trades that would have pulled the shadow equity out of drawdown.
The brake zeros those winners too. Net effect on SOL/NEAR:
**−29.07 and −21.79 respectively**.

**The brake's blanket flatten rule affects each symbol differently
based on its behavior during the drawdown window. DOGE's losers got
spared; SOL and NEAR's winners got killed.**

This is a fundamental characteristic of a portfolio-level brake: it
cannot distinguish per-symbol contribution signs at decision time.
The brake sees the portfolio in drawdown and flattens everything,
regardless of whether each symbol is currently winning or losing.

### Concentration by two metrics

| Metric | iter-v2/005 | iter-v2/013 | Rule | Pass? |
|---|---|---|---|---|
| Weighted (pct of wpnl) | XRP 47.75% | **XRP 78.55%** | ≤50% | **FAIL** |
| Unweighted (pct of net_pnl_pct) | XRP 50.42% | XRP 50.42% | ≤50% | FAIL (unchanged) |

The unweighted metric is unchanged (because net_pnl_pct doesn't
depend on weight_factor). The weighted metric blew out from 47.75%
to 78.55%.

iter-v2/005 was MERGED with a 47.75% weighted concentration. The
weighted convention is the one that matters for capital allocation.
iter-v2/013 fails it by 28.55 percentage points.

## Hard-constraint check

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| 10-seed mean OOS Sharpe ≥ +1.1 | +1.1 | +1.1458 | **PASS** |
| ≥ 7/10 seeds profitable | 7 | 9 | **PASS** |
| Primary OOS trades ≥ 50 | 50 | 117 | PASS |
| Primary OOS MaxDD < 25% | 25% | 16.41% | **PASS** |
| All seeds MaxDD < 30% | 30% | (not measured per-seed) | — |
| **Concentration ≤ 50% (weighted)** | **50%** | **78.55%** | **STRICT FAIL** |
| IS/OOS Sharpe ratio > 0 | 0 | 13.98 | PASS |
| DSR > +1.0 | 1.0 | +8.51 | PASS |

**Result**: 6 of 7 measurable constraints pass. The concentration
strict rule is the blocker.

## Pre-registered failure-mode prediction — accurate on variance, missed concentration

Brief §"Pre-registered failure-mode prediction":

> **"Seed variance in brake fire rate. Different seeds have different
> OOS trade distributions. Some seeds may have fewer drawdowns →
> brake fires less, Sharpe drag smaller. More drawdowns → brake
> fires more, Sharpe drag larger, possibly pushing below +1.1."**

**Actual**: Seed variance is exactly as predicted. Fire rates range
9.2% (seed 4567) to 18.6% (seed 3456). Sharpe drag ranges from
+0.497 (seed 1234, brake HELPED) to −0.762 (seed 789, brake HURT).
Seed 789 at −0.20 is the outlier but 10-seed mean stays above
+1.1.

**What the brief missed**: I did not predict that the brake would
rebalance per-symbol contributions in a way that breaks the
concentration rule. The brief focused on Sharpe/MaxDD and treated
concentration as a given. The flatten blanket rule causes
asymmetric per-symbol impact — a real failure mode that wasn't
in the risk map.

## The right brake design — per-symbol, not portfolio

The post-hoc portfolio brake validated in iter-v2/012 looked great
on aggregate metrics but falls apart on per-symbol decomposition.
**A portfolio-level brake cannot avoid cross-symbol contamination
unless it can also selectively choose which symbols to flatten**,
which requires per-trade outcome prediction (impossible).

**Better design**: **per-symbol brake** inside each `RiskV2Wrapper`.

### Per-symbol brake architecture

Each `RiskV2Wrapper` instance (one per model) tracks its OWN running
PnL via an `on_trade_closed` callback from the backtest engine.
When its own compound equity drops below the shrink threshold,
the brake fires FOR THAT MODEL only, attenuating its new trades.
Cross-model DD is ignored.

Pros:
- No cross-symbol contamination. DOGE's brake cannot zero SOL's winners.
- Per-symbol calibration: each symbol's brake thresholds can be tuned
  to its own vol profile.
- In production, matches the mental model of "each strategy manages
  its own risk budget".

Cons:
- Slower DD estimate per model (fewer trades per estimate).
- Does not protect against portfolio-wide regime shifts where ALL
  models bleed simultaneously.

### Wrapping requirements

The backtest engine currently has no `on_trade_closed` hook. Adding
one is backwards-compatible via `hasattr` check. iter-v2/014 would:

1. Add `on_trade_closed(result: TradeResult)` optional method to
   the Strategy Protocol.
2. Modify `run_backtest` to call `strategy.on_trade_closed(result)`
   after each trade closes.
3. `RiskV2Wrapper` implements `on_trade_closed`: updates per-symbol
   shadow equity, recomputes DD state.
4. `RiskV2Wrapper.get_signal` consults the per-symbol brake state
   after the existing gates and before vol scaling.

This is a more substantial change than iter-v2/013's post-hoc
approach but avoids the cross-symbol contamination issue entirely.

## Why 9/10 profitable but still NO-MERGE

iter-v2/013 passes every MERGE criterion EXCEPT concentration:

- 10-seed mean +1.146 > +1.1 threshold
- 9/10 profitable > 7/10 threshold
- Primary seed MaxDD 16.41% << 30% threshold
- DSR +8.51 > +1.0 threshold
- OOS/IS ratio 13.98 > 0

But concentration 78.55% vs 50% strict rule. The concentration rule
exists for a reason — a 78% single-symbol exposure means the portfolio
is essentially long XRP with satellite diversification. That's not
the 4-symbol v2 architecture.

**Declining the merge is the right call.** Compromising the
concentration rule to ship a single improvement would be exactly
the kind of metric-goal-post moving that the "NO CHEATING" section
forbids.

## Label Leakage Audit

No leakage. Gates operate on trade timing and compound equity, not
on future price data.

## Code Quality

- `apply_portfolio_drawdown_brake` is 80 lines, single responsibility,
  type-hinted, unit-tested inline before the run
- `activate_at_ms` parameter correctly scopes the brake to OOS
- `RiskV2Config` unchanged (brake lives in module-level function,
  not wrapper method — post-hoc design)
- `run_baseline_v2.py` bumped to `v2-013`, records both braked and
  unbraked per-seed Sharpes in `seed_summary.json`
- Lint clean, format clean

## Conclusion

iter-v2/013 productionizes iter-v2/012's validated Config C drawdown
brake into `run_baseline_v2.py`. The implementation is correct —
trades pass through scoping, state is self-releasing, 10-seed fail-fast
passes the threshold criteria. BUT:

1. The portfolio-level brake causes cross-symbol contamination:
   SOL and NEAR's winning trades during the July-August 2025
   flatten window get zeroed, while DOGE's losing trades get spared.
2. The resulting concentration is **78.55% XRP** — far above the
   50% strict rule.
3. Per-symbol PnL: XRP +46.84 (unchanged), DOGE +26.06 (improved),
   SOL −0.18 (destroyed), NEAR −13.08 (destroyed).

**Decision**: **NO-MERGE**. The drawdown brake primitive is
conceptually valid but a portfolio-level implementation is the
wrong architecture. iter-v2/014 should implement a **per-symbol
brake** via a new `on_trade_closed` callback on the backtest
engine, so each model's brake fires only on its own DD and
cannot contaminate other models' winners.

**Cherry-pick** research brief + engineering report + diary to
`quant-research`. Branch stays as record. iter-v2/005 remains the
v2 baseline.

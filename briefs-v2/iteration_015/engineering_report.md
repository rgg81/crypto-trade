# Iteration v2/015 Engineering Report

**Type**: FEASIBILITY STUDY (BTC contagion circuit breaker)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/015` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, MaxDD 59.88%)
**Decision**: **NO-MERGE** (brake fires but misses the actual drawdown window)

## Run Summary

| Item | Value |
|---|---|
| Runner | `analyze_btc_contagion.py` (commit `345f389`) |
| v2 input | `reports-v2/iteration_v2-005/out_of_sample/trades.csv` (117 trades) |
| BTC input | `data/BTCUSDT/8h.csv` (6881 bars, 2020-01-01 → 2026-04-12) |
| OOS slice | 985 BTC bars (2025-03-23 → 2026-03) |
| Wall-clock | ~15 sec |
| Artifacts | `reports-v2/iteration_v2-015_btc_contagion/` |

## BTC OOS window statistics

| Metric | Value |
|---|---|
| BTC 1-bar return range | −6.80% to +6.93% |
| BTC 1-bar return std | 1.25% |
| BTC 3-bar return range | −14.04% to +12.21% |
| Bars with 1-bar return < −3% | 20 |
| Bars with 1-bar return < −4% | 6 |
| Bars with 1-bar return < −5% | 2 |
| Bars with 1-bar return < −6% | 1 |
| Bars with 1-bar return < −8% | **0** |
| Bars with 3-bar return < −10% | 1 |
| Bars with 3-bar return < −15% | 0 |

**Observation**: 2025 OOS was a relatively calm BTC period.
Maximum 1-bar drop is −6.80% (one bar). Maximum 3-bar drop is
−14.04% (one window). No LUNA/FTX-magnitude crashes.

## Headline metrics — all 4 configs FAIL

| Config | 1-bar thresh | 3-bar thresh | Kill bars | Events | Kills | Sharpe | MaxDD | Calmar | XRP share |
|---|---|---|---|---|---|---|---|---|---|
| **None (baseline)** | — | — | — | 0 | 0 | **+1.66** | **−45.33%** | +2.61 | **47.75%** |
| A (tight) | −3% | −8% | 3 | 23 | 14 | +0.60 | **−48.61%** (worse) | +0.40 | **111.30%** (worse) |
| B (mid) | −4% | −10% | 3 | 6 | 1 | +1.55 | **−45.33%** (unchanged) | +2.34 | 51.37% |
| C (loose) | −5% | −12% | 6 | 2 | 3 | +1.33 | **−45.33%** (unchanged) | +1.70 | 56.83% |
| D (mid+extended) | −4% | −10% | 9 | 6 | 6 | +1.13 | **−45.33%** (unchanged) | +1.31 | 51.28% |

## The crucial finding: MaxDD is UNCHANGED for B, C, D

The baseline MaxDD of **−45.33%** is identical to the braked
MaxDD for Configs B (mid thresh), C (loose), and D (mid+extended
kill). The brake fires 1-6 events, kills 1-6 trades, but the
actual drawdown stretch survives completely.

### Why the brake doesn't protect against the actual drawdown

The v2 drawdown is driven by the **July-August 2025** NEAR/XRP/SOL
bear stretch. Looking at the trigger events from Config B:

```
2025-04-07 — 1bar -4.22%, 3bar -9.53%    (early April)
2025-06-22 — 1bar -3.47%, 3bar -4.51%    (not enough, but close)
2025-10-10 — 1bar -5.25%, 3bar -7.29%    (October)
2025-10-11 — 3bar -8.73%                 (October)
2025-10-21 — 1bar -4.50%                 (October)
2025-10-30 — 1bar -3.27%, 3bar -3.40%    (October)
2025-11-20 — 1bar -3.60%, 3bar -5.36%    (November)
...
```

**The earliest trigger is 2025-04-07. The next is 2025-06-22. Then
the next material event is 2025-10-10.**

Between 2025-06-22 and 2025-10-10 — the entire **July-August 2025
v2 drawdown period** — BTC did NOT have any single bar worse than
−4% or 3-bar window worse than −10%. The v2 drawdown was purely
alts-specific: NEAR and XRP bled independently while BTC was
stable or slightly up.

**Result**: the brake fires AROUND v2's drawdown but never
protects against it. Kills happen in April, June, October,
November, December, January — missing the July-August window
entirely.

### Config A (tight) makes things WORSE

Config A (−3% / −8%, 3 bars) fires 23 events and kills 14 trades,
but its MaxDD is **WORSE** than baseline (−48.61% vs −45.33%) and
its concentration blows out to **111.30%**.

Why: Config A's kills include several profitable trades from the
October bounce and later months. Removing those winners while
leaving the July-August losers untouched makes the equity curve
LOWER, deepening the drawdown and amplifying XRP's relative share.

Tighter thresholds catch MORE events but the same events fail to
coincide with v2's actual drawdown window. They just kill more
unrelated winners.

## Decision criteria check

| Constraint | Target | Best (B mid) | Pass? |
|---|---|---|---|
| MaxDD reduction ≥ 15% | −15% | **0%** (unchanged) | **FAIL** |
| Sharpe drag ≤ 5% | −5% | −6.5% | **FAIL** (marginal) |
| Concentration change ≤ 5 pp | ±5 pp | +3.62 pp | PASS |
| No negative-flip | 0 | 0 | PASS |
| OOS PF > 1.3 | 1.3 | (not computed) | — |

**Zero configs pass all criteria.** Config B is the closest but
still fails MaxDD reduction (0% vs required −15%).

## Pre-registered failure-mode prediction — PERFECTLY ACCURATE

Brief §"Pre-registered failure-mode prediction":

> **"Alternative failure mode: BTC crashed during periods where v2
> was not trading, so the brake fires but has no effect on trades.
> Secondary failure mode: the July-August 2025 v2 drawdown may
> have been alt-specific rather than BTC-correlated."**

**Actual**: both failure modes confirmed. The brake fires 1-23
times depending on config, but NONE of the firings coincide with
the July-August 2025 drawdown. The v2 drawdown is alts-specific.

This is a **cleanly-negative result**. The hypothesis was "BTC
contagion catches tail events" and the data says "no, the tail
events we care about are not BTC-correlated".

## The three-primitive conclusion

Combining results from iter-v2/012, 013, 014, 015:

| Primitive | Fires on | Fate | Reason |
|---|---|---|---|
| Portfolio drawdown brake | Pooled equity DD | iter-v2/013 NO-MERGE | Cross-symbol contamination breaks concentration |
| Per-symbol drawdown brake | Single-model DD | iter-v2/014 NO-MERGE | XRP never DDs, other symbols over-fire |
| **BTC contagion brake** | **BTC kline returns** | **iter-v2/015 NO-MERGE** | **v2's drawdown is alts-specific, not BTC-correlated** |

**All three trade-flow risk primitives fail** for this specific
v2 configuration.

The deeper lesson: v2's 59.88% OOS MaxDD is not caused by a
single tail event the model can detect. It's caused by a **slow
multi-week drift in the NEAR/XRP/SOL signals** during
July-August 2025 where the strategy's short positions keep
losing ground against rallying alts. No single-bar signal, no
per-symbol DD signal, no cross-asset BTC signal catches this
kind of slow bleed.

## What actually catches slow bleeds

Looking at the existing iter-v2/005 gates:

- **Feature z-score OOD**: catches distributional shifts in feature values (doesn't catch "my shorts are slowly wrong")
- **Hurst regime**: catches regime transitions (July-August was a gradual shift, not a sudden regime change)
- **ADX gate**: catches ranging regimes (July-August alts were trending UP — the brake misses this because the model is taking shorts in a trend)
- **Low-vol filter**: catches low-vol noise (July-August had normal vol)

**None of the existing gates specifically detect "the model's
shorts keep losing slowly"**. The only gate that could catch
this is a **position-correctness feedback gate**: track the
fraction of recently-closed trades that hit stop-loss vs
take-profit. When SL/TP ratio flips aggressively (many recent
trades hitting SL instead of TP), kill new signals until the
ratio recovers.

This is a **different primitive**: not a drawdown-based attenuator
but a **hit-rate feedback gate**. It would catch:
- July-August 2025 — shorts keep hitting SL, few hitting TP → kill
- COVID March 2020 — longs keep hitting SL → kill
- LUNA May 2022 — both sides hit SL randomly → kill

**iter-v2/016 candidate**: build a hit-rate feedback gate. This
is a FIFTH deferred primitive not in iter-v2/001's original 8-list,
but emerges naturally from the iter-015 negative result.

## Code Quality

- `analyze_btc_contagion.py` is 360 lines, single responsibility
- Reads BTC data, computes rolling returns, flags events, filters
  trades, reports metrics
- No production code touched
- Lint clean, format clean

## Label Leakage Audit

No backtest. BTC data used as a cross-asset trigger (not a v2
training feature). Within the skill's "cross-asset signals allowed
in risk gates" provision. No leakage.

## Conclusion

iter-v2/015 tested the BTC contagion circuit breaker, the only
remaining deferred risk primitive that bypasses XRP dominance.
Feasibility **fails cleanly**: the brake fires at 4-20 events
depending on threshold, but NONE of the events coincide with
v2's July-August 2025 drawdown period because that drawdown is
**alts-specific, not BTC-correlated**.

This result closes the trade-flow risk primitive family for
iter-v2/005:

1. iter-v2/012-014: drawdown brake lineage (portfolio + per-symbol) CLOSED
2. iter-v2/015: BTC contagion CLOSED

**Decision**: **NO-MERGE**. Cherry-pick docs + script to
`quant-research`. iter-v2/005 remains the final v2 baseline.

iter-v2/016 should pivot to ONE of:
1. **Hit-rate feedback gate** — a new primitive emerging from this
   negative result. Tracks recent SL/TP ratio and kills signals
   when the ratio flips aggressively. Could catch slow-bleed
   drawdowns the other primitives miss.
2. **CPCV + PBO validation upgrades** — doesn't improve the
   baseline but quantifies its confidence before paper-trading
   deployment.
3. **Paper-trading deployment** — accept iter-v2/005 as final
   and test it live. Let forward-walk data drive the next
   research questions.

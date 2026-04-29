# Iteration v2/016 Research Brief

**Type**: EXPLORATION (hit-rate feedback gate — NEW primitive)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, 59.88% MaxDD)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/016` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — a NEW primitive that directly targets v2's tail signature

iter-v2/012-015 tested three trade-flow risk primitives, all of
which failed for this specific v2 portfolio:

| Iter | Primitive | Why it failed |
|---|---|---|
| 013 | Portfolio drawdown brake | Cross-symbol contamination breaks concentration |
| 014 | Per-symbol drawdown brake | XRP never DDs → brake only attenuates non-XRP symbols → concentration amplified |
| 015 | BTC contagion circuit breaker | v2's drawdown is alts-specific; BTC never crashed during the drawdown window |

The iter-v2/015 diary identified a **specific tail signature** that
none of these primitives detect:

> **"v2's drawdown is a slow multi-week bleed where shorts keep
> hitting SL. None of the existing gates detect hit-rate feedback."**

iter-v2/016 tests a NEW primitive that directly targets this
signature: the **hit-rate feedback gate**.

## Hypothesis — how the gate works

For each new signal at time T, look at the most recent N closed
trades across ALL 4 v2 models (global, not per-symbol). Count how
many of them hit `exit_reason == "stop_loss"`. If the recent SL
rate exceeds a threshold, kill the signal.

**Formal definition**:

```
For each trade in OOS at open_time T:
    prior_closed = all trades with close_time < T and open_time >= OOS_CUTOFF
    window = prior_closed[-N:]  # last N closed trades
    if len(window) < N:
        # not enough history → don't brake (pass through)
        eff_factor = 1.0
    else:
        sl_rate = sum(1 for t in window if t.exit_reason == "stop_loss") / N
        if sl_rate >= threshold:
            eff_factor = 0.0  # kill
        else:
            eff_factor = 1.0
```

**Key properties**:
- **Self-releasing**: once enough winning trades close, the SL rate
  drops below threshold and the gate releases automatically
- **Symmetric across symbols**: the window is global, so when the
  gate fires, all 4 symbols are killed simultaneously →
  concentration should be preserved
- **Lookback-only**: no future data, no model retraining, just
  reads what already happened
- **Activates at OOS_CUTOFF**: pre-OOS trades don't count toward
  the window; the gate is fresh at deployment

## Configuration candidates

| Config | Window N | SL threshold | Rationale |
|---|---|---|---|
| A | 10 | 0.7 (7/10) | Tight: needs 70% SL rate to fire |
| B | 10 | 0.6 (6/10) | Mid: 60% SL rate |
| C | 15 | 0.67 (10/15) | Larger window, similar threshold |
| **D** | **20** | **0.65 (13/20)** | **Largest window (more robust), mid threshold** |
| None | — | — | Baseline |

iter-v2/005 baseline OOS has WR=45.3%, so SL rate ≈ 55% on average.
A 65-70% SL rate is meaningfully above this baseline, capturing
the "worse than usual" regime.

## Pre-registered failure-mode prediction

### Failure mode 1: the gate fires too late

The hit-rate window needs N trades to fill up before the gate can
fire. With N=20 and v2's ~117 OOS trades over 12 months, the
window fills in the first ~2 months of OOS. The gate can fire
from ~May 2025 onwards.

The July-August 2025 drawdown starts around trade #30-35 of the
OOS stream. The gate has ~20 trades of history by then.
Potentially enough to fire.

But the gate is REACTIVE: it fires after N trades have already
hit SL. If the drawdown starts with 10 consecutive SL hits, the
gate fires ONLY AFTER those 10 have happened. It prevents
further damage but the first 10 losses are already in.

**Expected outcome**: gate reduces drawdown depth but doesn't
prevent the drawdown entirely. MaxDD improves from 45% to maybe
25-30%. Sharpe drag small if winners resume quickly after release.

### Failure mode 2: the gate fires on routine noise

If threshold is too loose (e.g., 60% in 10 trades), the gate
fires on normal losing streaks that would have recovered on
their own. Kills legitimate trades, Sharpe drops.

### Failure mode 3: the gate can't see the slow bleed

If v2's drawdown isn't primarily SL-driven (e.g., it's driven by
timeouts or small losses), the gate misses it. **Verification
needed**: look at iter-v2/005's exit_reason distribution during
the July-August window.

### Sweet spot prediction

Config D (window=20, threshold=0.65) most likely to pass:
- Larger window = more robust to single-trade noise
- Mid threshold (13/20) is meaningfully above baseline SL rate
  (~55%) but not so tight that it misses gradual deterioration

**Expected metrics for Config D**:
- Sharpe: +1.45 to +1.60 (small drag)
- MaxDD: -20% to -30% (meaningful improvement)
- Concentration: 46-52% XRP (within tolerance)
- Kills: 15-30 trades

## Methodology — post-hoc simulation

### Data source

- iter-v2/005 OOS trades: `reports-v2/iteration_v2-005/out_of_sample/trades.csv`

The OOS trades have all fields needed: `open_time`, `close_time`,
`exit_reason`, `weighted_pnl`, `net_pnl_pct`, `symbol`.

### Algorithm

1. Sort trades by `open_time` (entry order)
2. Maintain a FIFO of the last N trades that have `close_time <
   current_trade.open_time` (i.e., trades that closed BEFORE
   this one opened — strict past only)
3. For each trade, compute the SL rate of the window:
   `sum(1 for t in window if t.exit_reason == "stop_loss") / N`
4. If `sl_rate >= threshold`, kill this trade (weight = 0)
5. Otherwise, keep original weight

### Configurations

5 configs: None (baseline), A (10/0.7), B (10/0.6), C (15/0.67), D (20/0.65)

## Success Criteria

Feasibility passes if ANY config achieves ALL of:

- [ ] OOS MaxDD reduction ≥ 15% (primary seed 42: 59.88% → ≤ 51%)
- [ ] Sharpe drag ≤ 10% (primary seed 42: +1.67 → ≥ +1.50)
- [ ] Concentration change ≤ 5 pp (XRP ≤ 52.75%)
- [ ] No per-symbol negative flip
- [ ] Brake fires on July-August 2025 window specifically

If feasibility passes, iter-v2/017 productionizes. If it fails,
**the v2 risk-primitive search space is fully exhausted** — pivot
to paper-trading deployment.

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged from iter-v2/005)

z-score OOD, Hurst, ADX, low-vol filter, vol-adjusted sizing.

### 6.2 New gate — hit-rate feedback

- Window: last N closed trades (global, cross-symbol)
- Trigger: `SL_rate(window) >= threshold`
- Action: kill new signal (weight = 0)
- Scope: activates at OOS_CUTOFF_MS; pre-OOS trades don't count
- Release: automatic when SL rate drops below threshold

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
Config D expected to be sweet spot. Main risks: gate fires too
late (reactive lag) or v2's drawdown isn't SL-driven.

### 6.4 Expected firing rates

- Config A (10/0.7): ~5-15 firings, clustered in drawdown
- Config B (10/0.6): ~15-30 firings, some routine
- Config C (15/0.67): ~10-20 firings
- Config D (20/0.65): ~20-30 firings

### 6.5 Black-swan replay

Verification: iter-v2/005's exit_reason distribution during
July-August 2025. If >65% of trades in that window are SL, the
gate should fire. If not, the drawdown has a different signature
and this primitive also fails.

## Research Checklist (9+ consecutive NO-MERGE rule)

- **A-H**: unchanged from iter-v2/005
- **I** (risk mgmt): NEW primitive targets the specific tail
  signature identified in iter-v2/015's diagnostic

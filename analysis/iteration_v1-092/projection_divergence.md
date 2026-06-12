# iter-v1/092 Projection Divergence — Forensic Summary

**Script:** `analysis/iteration_v1-092/projection_divergence.py`
**Run:** `uv run python analysis/iteration_v1-092/projection_divergence.py`

---

## What was projected vs what happened

The pre-registered projection (committed in `rerun_projection.md` BEFORE the corrected backtest) stated:

> IS: 219 -> 162 trades (−57, 26%), IS Sharpe ~+0.81 gain, net wpnl +5.21
> "subtraction is analytically exact (0 overlapping trades, sequential position model)"

The corrected backtest produced:

> IS: 219 -> 179 trades (−40 net, 18.3%), IS Sharpe 0.3783 -> 0.3007 (−0.078 vs /088)

Projection error on IS wpnl delta: **−12.44** (actual −7.23 vs projected +5.21).

---

## Computed Divergence Counts

| Segment | IS | OOS |
|---|---|---|
| Ungated total trades | 219 | 84 |
| Gated total trades | 179 | 75 |
| **Net change** | **−40** | **−9** |
| Projected net change | −57 | −12 |
| Gross removed (gate-suppressed) | **65** | **23** |
| Added (sequential slot replacements) | **25** | **14** |
| Removed trades WR | 0.3077 | 0.3913 |
| Added trades WR | 0.2800 | 0.5000 |
| Removed trades total wpnl | −17.10 | −2.71 |
| Added trades total wpnl | −24.33 | −1.43 |
| Net wpnl change (added − removed) | **−7.23** | **+1.28** |
| Projected net wpnl change | +5.21 | +2.78 |

---

## Root Cause

The projection claimed "analytically exact" because the ungated /088 IS roster has zero concurrent
(overlapping) positions — each XRP trade is fully closed before the next opens. The inference: removing
a BTC_UP entry simply subtracts it from the roster with no side effects.

**This inference is wrong for a sequential position model.**

When the gate suppresses an entry at time T, the position slot is freed. The strategy's walk-forward
loop then evaluates subsequent candles and MAY enter a new position on a candle that was previously
blocked (because the T-position was still open). These sequential replacement trades are REAL — 25 on IS,
14 on OOS.

The IS replacement trades have:
- WR 0.280 — BELOW the gated IS mean WR of 0.447
- total wpnl −24.33 — deeply negative, dominating the −17.10 removed from suppressed entries
- Net IS wpnl change: −7.23 (vs projected +5.21)

**The offline subtraction underestimated the gross removed count (57 projected vs 65 actual)** because
it applied the BTC_UP filter to the ungated roster statically — it did not account for the fact that
some reshuffled positions (freed by BTC_UP suppressions earlier in the walk-forward) would ALSO land
in BTC_UP regimes and be suppressed again, creating a cascade of replacements.

---

## OOS was different (gate modestly helped)

On OOS the replacement trades had WR 0.500 > removed WR 0.391, contributing a net +1.28 wpnl gain
(Sharpe 0.5158 -> 0.5952). The OOS displacement mechanism happened to yield better replacements than
IS. This does NOT override F1 (IS Sharpe failed the floor).

---

## Generalizable Rule

**Never trust offline post-hoc trade-subtraction projections for ENTRY gates in a path-dependent
sequential backtest.** The only valid test of a gate's effect is the backtest itself. The two conditions
required for "subtraction is exact" to hold are:

1. No concurrent positions (satisfied here — sequential single-symbol model)
2. **No position-slot cascades** — i.e., suppressing an entry never frees a slot for a subsequent
   entry. Condition 2 is impossible to satisfy in a sequential model where entries are conditioned
   on the slot being empty.

The pre-registered projection explicitly noted "stochastic multi-seed ensemble" as a source of OOS
divergence but stated IS was "analytically exact." That was the error — condition 2 was not checked.

This finding vindicates the user directive: **the backtest is the proof; no side scripts.**

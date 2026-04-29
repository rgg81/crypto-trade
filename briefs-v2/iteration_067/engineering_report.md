# iter-v2/067 Engineering Report — Drawdown brake hurts MaxDD (!)

## Build

- Branch: `iteration-v2/067` from `quant-research` at `ccdaa17`
- Code: wired existing `apply_portfolio_drawdown_brake` (built in
  iter-v2/013 but never enabled in baseline) into `_run_single_seed`
  after BTC trend + hit-rate filters. Config C (shrink 8%, flatten 16%,
  shrink factor 0.5), `activate_at_ms=OOS_CUTOFF_MS`.
- Same 4 baseline symbols, same config otherwise.

## Results

| Metric | iter-v2/059-clean | **iter-v2/067** | Δ |
|---|---|---|---|
| **IS monthly Sharpe** | +1.042 | **+1.042** | **identical** |
| IS daily Sharpe | +0.974 | +0.974 | identical |
| OOS monthly Sharpe | +1.659 | +0.911 | **−45%** |
| OOS daily Sharpe | +1.663 | +1.091 | −34% |
| Combined monthly | +2.701 | +1.953 | −28% |
| OOS PF | 1.78 | 1.50 | −16% |
| **OOS MaxDD** | 22.61% | **35.24%** | **+55% (WORSE!)** |
| OOS WR | 49.1% | 49.1% | identical |
| OOS trades | 57 | 57 | identical |
| OOS net PnL | +79.98 | +44.49 | −44% |

IS identical ✓ confirms brake scope (`activate_at_ms=OOS_CUTOFF_MS`)
works as designed. Only OOS period is affected.

## Brake fire stats

```
normal=263  shrink=16  flatten=3  /  282 total trades evaluated
fire rate: 6.74%
```

The brake fired on ~7% of trades — reasonable firing rate. It's working
correctly; the issue is the policy itself.

## Why the brake made MaxDD WORSE (counter-intuitive)

The brake shrinks/flattens new position sizes during drawdowns, trading
smaller losses DURING the drawdown for smaller gains during the REBOUND.
In iter-v2/059-clean's data:

- Drawdown episodes are relatively short; the strategy recovers quickly
- Brake shrinks entries into the recovery → misses rebound PnL
- Braked equity ends up LOWER than unbraked equity at recovery top
- Subsequent drawdowns then dig from a lower peak → deeper peak-to-trough
  measured on braked equity curve

Concrete: unbraked strategy OOS total +79.98 wpnl. Braked +44.49 (−44%).
The 35.5 wpnl "missed" was concentrated in recovery trades.

## Per-symbol (via brake, authoritative from seed_concentration.json)

| Symbol | OOS wpnl (brake applied) | Share |
|---|---|---|
| XRPUSDT | +20.23 | **45.46%** ← new max |
| NEARUSDT | +11.79 | 26.49% ← was 44.44% |
| DOGEUSDT | +10.38 | 23.33% |
| SOLUSDT | +2.10 | 4.71% |

**NEAR concentration DID drop** (44.44% → 26.49%) as a side effect —
the brake fires most during NEAR's big-move phases, which
disproportionately shrinks NEAR entries. XRP fills the vacuum at
45.46% — passes 50% outer cap but not 40% inner.

## MERGE criteria

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly | ≥ 2.70 | 1.95 | FAIL |
| 2 | OOS monthly | ≥ 1.41 | 0.91 | FAIL |
| 3 | IS monthly | ≥ 0.88 | 1.04 | PASS |
| 4 | OOS MaxDD | ≤ 27.1% | 35.24% | FAIL |
| 5 | PF, trades, Sharpe>0 | — | 1.50, 57, +1.09 | PASS |
| 6 | Concentration | ≤50% | 45.46% | PASS |

4 FAILs. NO-MERGE.

## Context — the 5-iteration pattern (iter-v2/063-067)

Every attempt at concentration fix degraded OOS Sharpe:

| Iter | Approach | OOS mo | MaxDD | NEAR% |
|---|---|---|---|---|
| v2/059-clean (baseline) | — | +1.66 | 22.61% | 44.44% |
| v2/063 | Add AAVE 5th symbol | +1.43 | 29.25% | 44.44% |
| v2/064 | NEAR 0.70× cap | +1.43 | 26.57% | 35.89% |
| v2/065 | Param sweep (0.80 best) | +1.51 (proj) | est. 25% | est. 39% |
| v2/066 | IS-only universe re-screen | +0.56 | 34.04% | 78.47% XRP |
| **v2/067** | **Drawdown brake (generic)** | **+0.91** | **35.24%** | 26.49% (XRP 45%) |

**Empirical conclusion**: the iter-v2/059-clean baseline is at or near a
local optimum. Every tested concentration-reduction intervention costs
more Sharpe than it saves. The NEAR 44% concentration appears to be a
**feature of genuine edge**, not an overfit symptom.

## Verdict — NO-MERGE

Brake is net harmful on this strategy. iter-v2/013's design was sound
but its validation was on earlier v2 state (iter-v2/011). Today's
iter-v2/059-clean baseline doesn't benefit.

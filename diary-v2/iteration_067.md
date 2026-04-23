# iter-v2/067 Diary

**Date**: 2026-04-23
**Type**: EXPLOITATION (enable existing drawdown-brake infrastructure)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** — brake HURTS MaxDD (+55%) and Sharpe (−45% OOS monthly)

## Summary

Enabled the drawdown brake that was built in iter-v2/013 but never wired
into baseline. Config C (shrink 8%, flatten 16%, shrink 0.5×),
activate at OOS_CUTOFF_MS so IS is untouched.

Result: **counter-intuitive failure**. The brake INCREASED OOS MaxDD
(22.61% → 35.24%) while dropping OOS monthly Sharpe 45% (+1.66 → +0.91).
Brake fired appropriately (~7% of trades) — the issue is the policy,
not the wiring.

## Why the brake failed here

iter-v2/059-clean has short, shallow drawdowns with fast rebounds. The
brake fires on the way DOWN (correct) but stays engaged into the REBOUND,
missing the recovery trades. The result is a LOWER equity peak
post-recovery, which makes the next drawdown (measured from that lower
peak) appear deeper.

Concretely:
- Baseline OOS total +79.98 wpnl
- Braked OOS total +44.49 wpnl (−44%)
- The 35.5 wpnl delta is mostly recovery trades the brake suppressed

## The 5-iteration pattern (iter-v2/063-067) — empirical signal

Every attempt at concentration fix degrades Sharpe:

| Iter | Approach | OOS mo | Concentration (max) |
|---|---|---|---|
| 059-clean | — | +1.66 | NEAR 44.44% |
| 063 | +AAVE 5th sym | +1.43 | NEAR 44.44% (AAVE lost -21) |
| 064 | NEAR 0.70× cap | +1.43 | NEAR 35.89% |
| 065 | sweep → 0.80 cap | +1.51 (projected) | NEAR 39% |
| 066 | IS-only re-screen | +0.56 | XRP 78.47% (disaster) |
| **067** | **drawdown brake** | **+0.91** | **XRP 45.46% (NEAR 26%)** |

**Takeaway**: NEAR's 44% concentration is not a bug, it's a feature of
the symbol's genuine edge in the current regime. Every intervention to
reduce concentration has come at a Sharpe cost of 6-67%. The baseline
iter-v2/059-clean is at a local optimum; further concentration-centric
iterations produce diminishing returns.

## What PASSED here (worth noting)

- **IS is bit-identical** to iter-v2/059-clean. Confirms brake scope is
  correctly set to OOS-only. The infrastructure works; the policy doesn't.
- **NEAR concentration DID drop** (44.44% → 26.49%). The brake
  generically softens the most-active symbol in a drawdown — which
  happens to be NEAR. But XRP filled the vacuum (45.46%).

## MERGE criteria

| # | Criterion | Actual | Pass |
|---|---|---|---|
| 1 | Combined monthly Sharpe ≥ 2.70 | 1.95 | FAIL |
| 2 | OOS monthly Sharpe ≥ 1.41 | 0.91 | FAIL |
| 3 | IS monthly Sharpe ≥ 0.88 | 1.04 | PASS |
| 4 | OOS MaxDD ≤ 27.1% | 35.24% | FAIL |
| 5 | PF, trades, Sharpe>0 | 1.50, 57, +1.09 | PASS |
| 6 | Concentration ≤ 50% | 45.46% XRP | PASS |

3 FAILs. **NO-MERGE**.

## Next Iteration Ideas — iter-v2/068

### Recommendation: pivot from concentration to Sharpe/MaxDD directly

After 5 iterations empirically showing the current baseline's concentration
is near-optimal (it's a feature not a bug), iter-v2/068 should target OOS
Sharpe or MaxDD directly, accepting NEAR's share.

### 1. (primary) z-score OOD threshold sweep  [0.5h each, fast]
Current: 2.5. iter-v2/050 used 3.0 (worse), iter-v2/060 tried 2.25 (failed,
OOS trades <50 min). Try **2.4** (between 2.5 and 2.25) — tighter without
iter-v2/060's collapse. If this moves OOS Sharpe up without hurting
trade count or concentration, it's a simple win.

### 2. Cooldown tweak  [2.5h]
Current: 4 candles (32h). Try 5 (40h). Tighter cooldown historically
improves Sharpe by preventing overtrading.

### 3. Re-examine drawdown brake with GENTLER config
Config A (less aggressive): shrink at 12%, flatten at 25%, shrink 0.7×.
The failure of Config C here suggests iter-v2/059-clean has a different
regime profile than iter-v2/011. Gentler brake might give DD protection
without crushing rebound PnL.

### 4. Step back: full v1+v2 combined portfolio evaluation
We've optimized v2 in isolation for 67 iterations. The ACTUAL deployment
target is v1+v2 combined. Analyze how iter-v2/059-clean combines with v1
iter-152 in a merged portfolio. If the combined Sharpe is strong, the v2
baseline is already doing its job.

**Recommended iter-v2/068**: Option 1 (z-score 2.4). Fast, low-risk
parameter tweak. If it improves OOS without hurting concentration or IS,
it's a clean win. If it fails, move to Option 2.

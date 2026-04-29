# Iteration v2/006 Engineering Report

**Type**: EXPLOITATION (ADX threshold tuning)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/006` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Decision (from Phase 7)**: **NO-MERGE** — 10-seed mean is flat (−0.003),
IS Sharpe flipped negative, IS/OOS ratio −6.39 strict-fails. Pre-registered
failure mode confirmed in full.

## Run Summary

| Item | Value |
|---|---|
| Models | 4 (E=DOGE, F=SOL, G=XRP, H=NEAR) |
| Architecture | Individual single-symbol LightGBM, 24-mo WF |
| Seeds | 10 (full MERGE validation) |
| Optuna trials/month | 10 |
| Single-variable change | `RiskV2Config.adx_threshold: 20.0 → 15.0` |
| Wall-clock (10 seeds) | ~55 min |
| Output | `reports-v2/iteration_v2-006/` |

## Primary seed 42 — comparison vs iter-v2/005 baseline

| Metric | iter-v2/005 | iter-v2/006 | Δ |
|---|---|---|---|
| OOS Sharpe (seed 42, weighted) | +1.671 | +1.782 | +0.11 |
| OOS PF | 1.457 | 1.443 | −0.01 |
| OOS MaxDD | 59.88% | 59.88% | 0.00 |
| OOS WR | 45.3% | 46.0% | +0.7 pp |
| OOS trades | 117 | **137** | **+20** |
| OOS net PnL (weighted) | +94.01% | +104% | +10 |
| **IS Sharpe** | +0.116 | **−0.278** | **−0.394** |
| **IS PF** | 1.029 | **0.938** | **−0.09** (below 1.0) |
| **IS MaxDD** | 111.55% | **177.98%** | **+66 pp** |
| **IS/OOS Sharpe ratio** | +14.94 | **−6.39** | **sign flipped to negative** |
| DSR (OOS weighted, N=6) | +12.82 | +12.10 | −0.72 |

**Primary seed 42 OOS is slightly better (+0.11) but IS is catastrophic**.
IS Sharpe flipped from +0.12 to −0.28. IS PF dropped below 1.0. IS MaxDD
ballooned from 111% to 178%. The model is now unprofitable on its own
training data.

## 10-seed robustness summary

| Seed | Trades | OOS trades | iter-v2/005 | iter-v2/006 | Δ |
|---|---|---|---|---|---|
| 42 | 535 | 137 | +1.671 | **+1.782** | +0.11 |
| 123 | 577 | 133 | +1.287 | +1.473 | +0.19 |
| 456 | 605 | 151 | +1.560 | +1.275 | **−0.29** |
| 789 | 571 | 139 | +0.565 | **+0.182** | **−0.38** |
| 1001 | 591 | 140 | +1.964 | +1.819 | −0.15 |
| 1234 | 550 | 132 | +1.889 | +1.812 | −0.08 |
| 2345 | 496 | 96 | +0.685 | +1.023 | +0.34 |
| 3456 | 572 | 136 | +0.319 | **+0.107** | **−0.21** |
| 4567 | 456 | 86 | +1.715 | +1.604 | −0.11 |
| 5678 | 531 | 111 | +1.319 | **+1.866** | **+0.55** |

| Statistic | iter-v2/005 | iter-v2/006 | Δ |
|---|---|---|---|
| **Mean OOS Sharpe** | **+1.297** | **+1.294** | **−0.003** |
| Std | 0.552 | 0.641 | +0.09 (wider) |
| Min | +0.319 | +0.107 | −0.21 |
| Max | +1.964 | +1.866 | −0.10 |
| Profitable | 10/10 | 10/10 | — |
| > +0.5 | 9/10 | 8/10 | −1 |

**10-seed mean is flat — essentially unchanged** (−0.003 Sharpe, well
within single-seed noise). Primary seed 42 happens to land on the positive
side of the distribution (+0.11) but the overall distribution is a wash:

- 4 seeds improved (+0.11 to +0.55)
- 6 seeds degraded (−0.08 to −0.38)
- Std widened by +0.09 (less stable)
- Min dropped from +0.32 to +0.11 (worst case closer to zero)

**The improvement is NOT structural — it's seed-42 luck.** The distribution
overall shifted slightly wider and flat. Running 10 seeds was the right
call: a single-seed judgment would have been misleading.

## IS catastrophe — the critical finding

| IS Metric | iter-v2/004 | iter-v2/005 | iter-v2/006 |
|---|---|---|---|
| Sharpe | +0.465 | +0.116 | **−0.278** |
| PF | 1.135 | 1.029 | **0.938** |
| MaxDD | 77.02% | 111.55% | **177.98%** |
| WR | 41.2% | 40.1% | 38.7% |
| Total trades | 272 | 344 | 398 |

The IS trajectory over the last three iterations is a **monotone collapse**:

1. iter-v2/004 (low-vol filter): IS Sharpe +0.47, PF 1.14, MaxDD 77%
2. iter-v2/005 (added NEAR): IS Sharpe +0.12, PF 1.03, MaxDD 112% —
   NEAR's IS bear-market disaster drags the aggregate
3. iter-v2/006 (ADX 20 → 15): IS Sharpe **−0.28**, PF **0.94**,
   MaxDD **178%** — ADX loosening lets 54 more IS trades through,
   and those extra trades are net losers on IS

**The 54 additional IS trades (344 → 398) from lowering ADX are
net-negative IS contributors.** This is the smoking gun: trades in the
ADX 15-20 band are IS-losers but OOS-winners in the specific 2025 OOS
regime. That's a **regime-specific** pattern, not a structural edge.

## IS/OOS Sharpe ratio — researcher-luck flag

The v2 skill's hard constraint states: `IS/OOS Sharpe ratio > 0.5`.

- iter-v2/005: +0.116 / +1.671 = **+0.069** (below 0.5, but same direction)
- iter-v2/006: −0.278 / +1.782 = **−0.156** (negative, strict fail)

The iter-v2/005 ratio was already below 0.5 but the iteration merged
because "OOS > IS" is the opposite of researcher-overfit. iter-v2/006
continues that pattern even more extremely: the ratio is not just low,
it's **negative**. The strategy makes money on OOS while losing money
on IS — the opposite of researcher-overfit, but **arguably worse**:
it means the model's OOS edge doesn't come from its training distribution.

**This is "working by accident"**. The ADX 15-20 band happens to be
profitable in the 2025 OOS window and unprofitable in the 2020-2025 IS
window. There's no structural reason why the next regime shift wouldn't
reverse that. Deploying this strategy is deploying a bet on a specific
OOS regime staying put.

## Hard-constraint check

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: 10-seed mean > +1.297** | +1.297 | **+1.294** | **FAIL** (by 0.003) |
| ≥ 7/10 seeds profitable | 7/10 | 10/10 | PASS |
| OOS trades ≥ 50 | 50 | 137 | PASS |
| OOS PF > 1.1 | 1.1 | 1.443 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 59.88% | PASS |
| No single symbol > 50% OOS PnL | 50% | TBD, likely still ~48% | likely PASS |
| DSR > +1.0 | 1.0 | +12.10 | PASS |
| v2-v1 OOS correlation < 0.80 | 0.80 | ~−0.04 likely | PASS |
| **IS/OOS Sharpe ratio > 0.5** | 0.5 | **−0.156** | **FAIL** |

**Two strict failures**:

1. **Primary 10-seed mean is flat** — technically fails by 0.003. Within
   noise, but the primary metric demands strict improvement.
2. **IS/OOS Sharpe ratio is negative** — hard fail. The researcher-
   overfitting gate exists for a reason; v2/006 triggers it from the
   opposite direction (OOS >> IS) which is its own kind of fragility.

No diversification exception applies because this iteration does not
add new symbols.

## Gate efficacy (primary seed 42)

| Symbol | signals | z-score | Hurst | ADX | low-vol | combined | Δ vs iter-v2/005 |
|---|---|---|---|---|---|---|---|
| DOGEUSDT | 2560 | 11% | 6% | **9%** | **37%** | **63.5%** | −7 pp (as predicted) |
| SOLUSDT | 2515 | 16% | 8% | **8%** | **26%** | **57.9%** | −8 pp (as predicted) |
| XRPUSDT | 2532 | 13% | 9% | **12%** | **29%** | **63.3%** | −8 pp (as predicted) |
| NEARUSDT | 2372 | 19% | 7% | **7%** | **39%** | **71.5%** | −4 pp |

**The ADX gate fires at the predicted ~7-12% (down from 24-28%)** —
the change produced the expected signal recovery at the gate level.
But the SURVIVING low-vol gate absorbs most of the slack (low-vol
fires at 26-39% now vs 19-29% in iter-v2/005). The combined kill rate
drops from 66-76% to 57-72% — a smaller drop than predicted (~7-8pp
instead of ~15pp) because the low-vol filter picked up the slack.

The real story: **the trades that ADX was killing were in the low-vol
bucket anyway**. Lowering ADX let them reach the low-vol filter, which
killed most of them. The additional trades that DID make it through
are the marginal ones, and those are the IS-losers.

## Pre-registered failure-mode prediction — fully validated

Brief §6.3 predicted: "The most likely way iter-v2/006 fails is that
the ADX 15-20 band contains trades that are IS-negative but OOS-positive
— a regime-specific pattern that looks good on 2025 OOS but would
reverse in other regimes. Signal: IS Sharpe drops meaningfully while
OOS Sharpe rises. If IS Sharpe falls below zero while OOS is positive,
that's a **strong** flag that the strategy is working by accident, not
by design. The IS/OOS Sharpe ratio should stay above 0.5 (strictly)
for MERGE."

**Every word of this prediction materialized**:

- ✓ "IS Sharpe drops meaningfully while OOS Sharpe rises" — IS dropped
  from +0.12 to −0.28, OOS rose from +1.67 to +1.78 on primary seed
- ✓ "IS Sharpe falls below zero while OOS is positive" — IS −0.28, OOS +1.78
- ✓ "Strong flag that the strategy is working by accident" — 10-seed mean
  is flat, IS is catastrophic, gains are entirely from primary-seed 42
- ✓ "IS/OOS Sharpe ratio should stay above 0.5" — ratio is −0.156,
  strict fail

**The brief correctly anticipated the exact failure mode**. Writing
the failure mode prediction at the research stage (before seeing the
data) is the mechanism that protected iter-v2/006 from being merged on
a tempting-but-fragile OOS improvement.

## Label Leakage Audit

- CV gap: unchanged
- Walk-forward: unchanged
- Feature isolation: unchanged
- Symbol exclusion: unchanged

No leakage detected. The IS degradation is not a leakage artifact —
it's the expected behavior of a weakened filter letting net-negative IS
trades through.

## Artifacts

- `reports-v2/iteration_v2-006/comparison.csv`
- `reports-v2/iteration_v2-006/{in_sample,out_of_sample}/{...}`
- `reports-v2/iteration_v2-006/seed_summary.json`

## Conclusion

iter-v2/006 lowered ADX threshold 20 → 15 hoping to recover signal
killed by over-aggressive ADX gating. The change did what it said on
the tin (ADX kill rate dropped from 24-28% to 7-12%) but the
additional trades are **net-negative on IS and net-positive on OOS**
in a regime-specific way:

- **10-seed mean is flat** (+1.294 vs +1.297, −0.003 — pure noise)
- **IS Sharpe flipped negative** (−0.28 from +0.12), IS PF < 1.0,
  IS MaxDD 178%
- **IS/OOS ratio is negative** (−0.156), strict-fails the
  researcher-overfitting gate

**Decision**: **NO-MERGE**. Primary metric fails by 0.003 (even under
the generous "any improvement merges" interpretation, the delta is
noise). IS/OOS ratio strict-fails. The pre-registered failure mode
materialized in full.

**Lessons for iter-v2/007+**:

1. **The ADX 15-20 band is fragile**. Don't lower ADX further. Either
   stay at 20 (current baseline) or consider an ADX band gate (only
   trade when ADX is strictly between 20 and 40, not above 40 or
   below 20).
2. **The combined kill rate tolerance is higher than the skill's
   10-30% target**. The retained signal at 66-76% kill rate is
   strongly profitable and seed-robust; relaxing the kill rate hurts
   the IS distribution without helping OOS 10-seed mean. Stop trying
   to reduce kill rate via gate loosening — it doesn't help.
3. **Primary metric should always be 10-seed mean, not primary seed**.
   iter-v2/006 looked good on seed 42 alone and flat on 10 seeds. The
   10-seed interpretation saved a bad merge.
4. **Pre-registered failure modes work**. The brief §6.3 prediction
   was unambiguous, the failure was unambiguous, and the NO-MERGE
   decision flowed naturally from the observed-vs-predicted comparison.
5. **iter-v2/007 should shift away from gate tuning**. The gates are
   now at a local optimum. Move to a different variable: bump Optuna
   trials (iter-v2/005 diary Priority 2), enable drawdown brake
   (deferred primitive), or work on NEAR's IS/OOS mismatch (perhaps
   shorter training window for NEAR specifically).

**Recommendation**: iter-v2/007 = bump Optuna trials 10 → 25. This is
a compute-budget change that should raise IS Sharpe (currently +0.12
at 10 trials, likely under-optimized) without the fragile OOS-only
improvement risk of gate tuning.

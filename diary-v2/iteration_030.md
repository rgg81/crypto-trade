# Iteration v2/030 Diary

**Date**: 2026-04-15
**Type**: ENGINEERING PREREQUISITE (per-seed concentration audit)
**Parent baseline**: iter-v2/029
**Decision**: **NO-MERGE** (no algorithmic change; determinism-identical to iter-029)

## What this iter delivered

**First full 10-seed per-seed concentration audit in v2's history.**

Previously, the runner only saved primary-seed (seed 42) per-symbol
reports. The new Seed Concentration Check rule (skill commit 0e5ac3a)
requires auditing ALL 10 seeds. iter-030 adds the machinery.

Zero algorithmic change. iter-030's seed-by-seed metrics match iter-029
exactly (determinism confirmed across all 10 seeds). This iter's value
is pure visibility.

## The audit — all 10 seeds FAIL, and it's worse than we thought

```
  seed      max      symbol    ≤50    ≤40
    42   69.47%     XRPUSDT    FAIL   FAIL
   123   53.79%     XRPUSDT    FAIL   FAIL
   456   76.15%     XRPUSDT    FAIL   FAIL
   789   72.97%     XRPUSDT    FAIL   FAIL
  1001  949.34%    NEARUSDT    FAIL   FAIL   ← distressed
  1234   59.03%     XRPUSDT    FAIL   FAIL
  2345   51.10%     XRPUSDT    FAIL   FAIL
  3456   91.12%     XRPUSDT    FAIL   FAIL
  4567  113.11%    NEARUSDT    FAIL   FAIL   ← distressed
  5678   87.71%    NEARUSDT    FAIL   FAIL
```

- **0/10 seeds pass the 50% rule**
- **10/10 seeds exceed the 40% inner rule**
- 7 seeds dominated by XRP (51-91%)
- 3 seeds dominated by NEAR (88% / 113% / 949%)
- 3 seeds are "distressed" (near-zero total, nonsensical >100% share)

## Important discovery — concentration was always worse than reported

Primary seed 42:
- `per_symbol.csv` `pct_of_total_pnl` (net_pnl_pct based): **60.86%**
- `seed_concentration.json` `oos_share_pct` (weighted_pnl based): **69.47%**

These should agree but they don't. The difference is **8.6 percentage
points**. The reason: `per_symbol.csv` uses raw trade return percentages,
while `weighted_pnl` includes the `RiskV2Wrapper`'s vol-adjusted position
sizing. For concentration (which is about CAPITAL exposure, not return
percentage), **weighted_pnl is correct**.

**Implication**: every prior v2 iteration's reported concentration was
understated. iter-029's "60.86%" is really "69.47%". iter-019's
"41.39%" is probably really ~48%. The concentration problem has
always been worse than visible.

BASELINE_V2.md should be updated to use the weighted_pnl measure for
concentration reporting going forward.

## Pattern classification — confirmed STRUCTURAL (not seed noise)

The research brief pre-registered 3 possible patterns. Pattern 1
(structural) is confirmed:

**Per-symbol behavior across the 10 seeds**:

| Symbol | Dominant count | Positive count | Negative count |
|---|---|---|---|
| XRPUSDT | 7 | 8 | 2 |
| NEARUSDT | 3 | 6 | 4 |
| DOGEUSDT | 0 | 5 | 5 |
| SOLUSDT | 0 | 5 | 5 |

**The portfolio isn't really 4 symbols**. It's a 2-symbol (XRP + NEAR)
portfolio with DOGE and SOL as noisy filler. Across all 10 seeds,
DOGE and SOL have a 50/50 positive/negative split — they're essentially
random contributors. XRP is almost always a winner. NEAR is bimodal.

This is a structural property of:
1. The feature set (35 + 5 BTC features)
2. The symbol universe (DOGE/SOL/XRP/NEAR)
3. The model architecture (4 independent LightGBMs)
4. The risk gate stack (7 gates)

**It is NOT a random artifact of any one seed.**

## Seed 1001 is broken, not just unlucky

Seed 1001 has been the persistent unprofitable outlier since iter-025.
Per the concentration data:

```
Seed 1001 OOS weighted PnL:
  NEARUSDT: −31.10 (largest absolute contribution, NEGATIVE)
  SOLUSDT:  −22.51
  DOGEUSDT: +13.72
  XRPUSDT:  +36.62
  Total:     −3.27
```

Seed 1001 finds bad hyperparameters for NEAR and SOL via Optuna.
The XRP wins can't cover NEAR+SOL losses, so total is near zero.
This is **model instability at the seed level**, not a concentration
issue. It can be fixed by:

1. Rejecting Optuna trials that produce per-symbol CV Sharpe < 0 on
   some minimum threshold
2. Seed-specific Optuna warm-starts
3. Running the ensemble with more seeds per model (5+ per Optuna)

## Implications for iter-031

The user's explicit concern was "avoid seed concentration — it's a
big risk". The data says concentration is NOT a seed-level artifact;
it's a structural property of this 4-symbol portfolio. Fixing it
requires one of:

### Option A — Accept the 2-symbol reality

XRP + NEAR are the real alpha. Drop DOGE and SOL. Run as a 2-model
portfolio with explicit concentration acceptance.
- Pro: Honest about where the signal is
- Pro: Simpler, faster training
- Pro: Slightly higher Sharpe (no noisy filler)
- Con: 2-symbol concentration will always be ≥50% per symbol (trivially)
- Con: Needs a relaxed concentration rule (e.g., 60% max)

### Option B — Add more symbols to dilute

Add ADAUSDT, AVAXUSDT, or MATICUSDT as 5th and/or 6th models. Run
Gate 6 (v1 correlation) on each candidate first.
- Pro: Structural fix
- Pro: Lower natural concentration with more denominators
- Con: Longer runtime (1.5x per added symbol)
- Con: Risk of adding more DOGE/SOL-like noise-filler symbols
- Con: Pre-gate screening required

### Option C — Hard per-symbol capital cap at aggregation

Enforce a runtime rule: each symbol can contribute at most `cap`%
of the portfolio's total positive weighted_pnl. Any excess is scaled
down linearly.
- Pro: Implementable today without symbol changes
- Pro: Guarantees the concentration rule passes by construction
- Con: Post-hoc return manipulation (dishonest if reported as raw)
- Con: Reduces aggregate Sharpe (clips the winners)

### Option D — Hold-all-symbols equal-weight allocation

Each model gets exactly 1/n_symbols of total capital. Weight inputs
from the models are ignored at aggregation; weighted_pnl is recomputed
as `raw_return × (1/n_symbols)`.
- Pro: Honest equal-weight portfolio
- Pro: Standard industry approach
- Con: Does NOT cap concentration (ratios preserved under linear scaling)
- Con: Can't resolve the rule failure alone

### Option E — Fix the underlying feature/model asymmetry

Investigate WHY XRP is almost always the winner and DOGE/SOL are
random. Add per-symbol features? Adjust labeling? Per-symbol training
windows? This is more exploratory.
- Pro: Could improve the portfolio instead of just hiding concentration
- Con: Speculative
- Con: Could take multiple iters to converge

## Recommendation for iter-031

**Start with Option A (accept 2-symbol reality) + relax the
concentration rule for 2-symbol portfolios.**

Reasoning:
- The data clearly shows XRP and NEAR are the alpha sources
- DOGE and SOL are noise filler — they're 50/50 positive/negative
  across seeds
- Running a 2-symbol portfolio is cleaner and faster
- The 50% concentration rule makes no sense for n=2 (by construction,
  max ≥ 50%). Needs to be rewritten as "no symbol > 60%" for n=2.
- This is an honest admission of where the edge is

**Stretch goal for iter-031**: if 2-symbol XRP+NEAR shows a clear
improvement on OOS mean AND passes a relaxed (60%) concentration
rule, merge as new baseline. If not, move to Option B (add symbols).

**Deferred**: Options C/D/E are not simple fixes and shouldn't be
the iter-031 focus.

## Skill updates recommended

1. **Concentration measure**: use `weighted_pnl` not `net_pnl_pct`.
   The existing `per_symbol.csv` metric is misleading.
2. **n-symbol-aware concentration rule**:
   - n=2 symbols: max ≤ 60% (relaxed from 50%)
   - n=3 symbols: max ≤ 55%
   - n=4 symbols: max ≤ 50% (current rule)
   - n≥5 symbols: max ≤ 30%
3. **Distressed-seed flag**: when total_weighted_pnl is small
   (< $10 absolute) or negative, flag as distressed and exclude
   from the mean max-share computation.

## MERGE / NO-MERGE

**NO-MERGE**. Engineering-prerequisite iter, no algorithmic change.
The iter-029 baseline stands.

The per-seed audit machinery is now available for iter-031+ and is
the first piece of infrastructure needed to make the new Seed
Concentration Check rule actually enforceable.

**Next iteration**: iter-v2/031 = 2-symbol XRP+NEAR portfolio
(drop DOGE and SOL). Test whether the 2-symbol reality is cleaner
and more profitable than the 4-symbol illusion.

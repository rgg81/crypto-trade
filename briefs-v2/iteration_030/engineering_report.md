# Iteration v2/030 Engineering Report

**Branch**: `iteration-v2/030`
**Date**: 2026-04-15
**Config**: Identical to iter-v2/029 (4 models, 35+5 features, 15 Optuna trials, 10 seeds)

## Code changes (single commit)

One commit, `5ed5ed9`, added ~58 lines to `run_baseline_v2.py`:

1. `per_seed_concentration: list[dict]` accumulator in the seed loop
2. Per-seed per-symbol weighted-PnL share computation (`sym_pnl`, `sym_share`)
3. SEED CONCENTRATION AUDIT print section after the SEED ROBUSTNESS SUMMARY
4. `seed_concentration.json` saved alongside `seed_summary.json`

**Zero algorithmic change.** The backtest, risk wrapper, feature pipeline,
labeling, and Optuna search are unchanged. iter-030's primary seed 42
matches iter-029 exactly (435 trades, IS +0.6680, OOS +1.2774).

## Determinism validation — all 10 seeds identical to iter-029

| Seed | iter-029 IS | iter-030 IS | iter-029 OOS | iter-030 OOS |
|---|---|---|---|---|
| 42 | +0.6680 | +0.6680 ✓ | +1.2774 | +1.2774 ✓ |
| 123 | +0.3608 | +0.3608 ✓ | +1.5378 | +1.5378 ✓ |
| 456 | +0.4445 | +0.4445 ✓ | +0.5123 | +0.5123 ✓ |
| 789 | +1.0547 | +1.0547 ✓ | +1.1750 | +1.1750 ✓ |
| 1001 | −0.4341 | −0.4341 ✓ | −0.0725 | −0.0725 ✓ |
| 1234 | +0.6674 | +0.6674 ✓ | +0.9947 | +0.9947 ✓ |
| 2345 | +0.5426 | +0.5426 ✓ | +1.4620 | +1.4620 ✓ |
| 3456 | +0.7541 | +0.7541 ✓ | +1.1326 | +1.1326 ✓ |
| 4567 | +1.0467 | +1.0467 ✓ | +0.4169 | +0.4169 ✓ |
| 5678 | +0.4731 | +0.4731 ✓ | +0.5196 | +0.5196 ✓ |

Mean metrics reproduce exactly: IS +0.5578, OOS +0.8956, 9/10 profitable.

## Seed Concentration Audit — first full 10-seed view

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

- Mean per-seed max-share: **162.38%** (distorted by distressed seeds)
- Mean excluding distressed (3 seeds): **~71%** still fails 45% rule
- **Seeds passing ≤50%**: **0/10**
- **Seeds above 40%**: **10/10**
- **Overall seed concentration: FAIL on every seed**

### Distressed seeds explained

Seeds 1001, 4567, 5678 report max-share > 100%. This is a metric
artifact: when total weighted_pnl is small or negative, one symbol's
positive contribution can exceed 100% of the total while another
symbol's negative contribution makes the total small. Seed 1001:

```
NEARUSDT: −31.10
DOGEUSDT: +13.72
SOLUSDT:  −22.51
XRPUSDT:  +36.62
Total:     −3.27    ← small total amplifies the share ratio
```

Even though NEAR is the LARGEST absolute contributor, it's negative.
The share metric (`contrib / total`) becomes nonsensical near zero-total.
These 3 seeds should be flagged as "distressed" (essentially breakeven
portfolios where the winning and losing symbols cancel out).

## Pattern classification — STRUCTURAL

The brief pre-registered 3 possible patterns. **Pattern 1 (structural)
is confirmed**:

- Every seed has a dominant symbol exceeding 50%
- The dominant symbol is NOT random — it's XRP (7 seeds) or NEAR (3 seeds)
- SOL and DOGE are never the dominant symbol; they're middling or losing
- The 3 distressed seeds have SOL or DOGE losing heavily

**Per-symbol behavior across the 10 seeds**:

| Symbol | Dominant count | Positive count | Negative count |
|---|---|---|---|
| XRPUSDT | 7 | 8 | 2 |
| NEARUSDT | 3 | 6 | 4 |
| DOGEUSDT | 0 | 5 | 5 |
| SOLUSDT | 0 | 5 | 5 |

**XRP and NEAR are the real alpha**; DOGE and SOL are filler whose
contribution is noise-dominated. This suggests the portfolio isn't
really 4 symbols — it's a 2-symbol (XRP+NEAR) portfolio with 2
underperforming hedges.

## Concentration metric discrepancy

Primary seed 42:
- per_symbol.csv (`pct_of_total_pnl` from `net_pnl_pct`): XRP **60.86%**
- seed_concentration.json (`weighted_pnl`): XRP **69.47%**

These differ by **8.6 percentage points**. The difference comes from
position weighting. `net_pnl_pct` is the raw trade return percentage;
`weighted_pnl` includes the vol-adjusted position size from
`RiskV2Wrapper`. For concentration, **weighted_pnl is the correct
measure** because it represents actual capital contribution.

**The iter-029 diary's "60.86%" should have been "69.47%"**. The
concentration problem was always worse than the per_symbol.csv
suggested. This is important to document for the baseline tracker.

## Seed 1001 root cause

Seed 1001 is the persistent negative outlier across iters 025-030.
It's the one seed where the strategy doesn't work. Per the per-seed
data, seed 1001 has:
- NEAR: −31.10 (largest loss)
- SOL:  −22.51 (second largest)
- DOGE: +13.72 (mild win)
- XRP:  +36.62 (strong win)

Net −3.27. Seed 1001 fails because the model finds bad hyperparameters
for NEAR and SOL and the XRP wins can't cover them. This is a
**seed-level model instability issue** — not a concentration issue.
A fix here would need seed-specific Optuna constraints or a safety
override that rejects clearly bad hyperparameter sets.

## Assessment vs engineering-prerequisite gates

| Engineering target | Result |
|---|---|
| Runner produces `seed_concentration.json` with 10 entries | ✓ |
| SEED CONCENTRATION AUDIT table prints to stdout | ✓ |
| Audit contains max-share, max-symbol, pass/fail for all 10 seeds | ✓ |
| Primary seed 42 result matches iter-029 exactly | ✓ |
| Mean per-seed max-share is reported | ✓ |
| Determinism across all 10 seeds | ✓ |

**Engineering success: 6/6 targets met.**

## Research targets (non-gating)

| Target | Result |
|---|---|
| Diary contains full per-seed concentration table | ✓ (this report + diary) |
| Diary identifies which of the 3 patterns matches | ✓ (Pattern 1: structural) |
| Diary proposes specific iter-031 fix based on revealed pattern | ✓ (see diary) |

## Runtime

- Total: ~94 minutes (10 seeds × 4 models)
- Identical to iter-029 (expected given determinism)
- No performance regression from the audit code

## Known limitations

1. **Distressed-seed handling**: the max-share metric fails when total
   weighted_pnl is near zero or negative. The audit should flag these
   as "distressed" instead of reporting nonsensical >100% values.
   Proposed fix for iter-031: add a `total_oos_wpnl` field and a
   `distressed` boolean flag.

2. **`per_symbol.csv` discrepancy**: the primary-seed report uses
   `net_pnl_pct` which underreports concentration by ~8pp relative
   to the correct `weighted_pnl` measure. Either fix `per_symbol.csv`
   or document the discrepancy in BASELINE_V2.md.

3. **No fix applied**: iter-030 is pure visibility. The concentration
   is not addressed. That's iter-031's job.

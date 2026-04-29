# iter-v2/066 Engineering Report — IS re-screening → catastrophic failure

## Build

- Branch: `iteration-v2/066` from `quant-research` at `4d6fc31`
- Stage 1 screener: `screen_v2_candidates.py` (IS-only LGBM with 80/20
  split, 5 Optuna trials, single seed, fast triple-barrier labels)
- Stage 1 ranked 24 candidates; fail-fast gate passed (top-5 Sharpe
  6.51 vs current universe's 4.95, +31.5%)
- Stage 2 universe: OP, XRP, TRX, ADA (top 4 by Stage 1 IS Sharpe)
- Fetched fresh data, regenerated v2 features for OP/TRX/ADA (needed
  BTC cross-asset cols from the shared BTC parquet)

## Stage 1 results (all candidates ranked)

```
  symbol   n_signals  is_sharpe_holdout  current
  OPUSDT        1900             8.2648     False   ← pick
 XRPUSDT        3242             6.5870     True    ← pick, kept
 TRXUSDT        2439             6.1786     False   ← pick
 ADAUSDT        3349             5.7640     False   ← pick
 UNIUSDT        2940             5.7519     False
NEARUSDT        2974             5.7180     True    ← dropped, rank 6
DOGEUSDT        3157             5.4314     True    ← dropped, rank 7
ATOMUSDT        3401             5.0014     False
AAVEUSDT        2962             4.9987     False
RUNEUSDT        3141             4.7015     False
 SOLUSDT        3162             2.0695     True    ← dropped, rank 20
```

## Stage 2 results — full walk-forward baseline

| Metric | iter-v2/059-clean | **iter-v2/066** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.042 | +0.779 | **−25%** |
| IS daily Sharpe | +0.974 | +0.819 | −16% |
| **OOS monthly Sharpe** | +1.659 | **+0.555** | **−67%** |
| **OOS daily Sharpe** | +1.663 | +0.731 | **−56%** |
| Combined monthly | +2.701 | +1.334 | −51% |
| OOS PF | 1.781 | 1.275 | −29% |
| OOS MaxDD | 22.61% | **34.04%** | +50% (WORSE) |
| OOS WR | 49.1% | 46.0% | −3.1pp |
| OOS trades | 57 | 63 | +6 |
| OOS net PnL | +79.98 | +26.38 | **−67%** |

Per-symbol OOS (wpnl-based concentration):

| Symbol | OOS trades | OOS wpnl | Share |
|---|---|---|---|
| XRPUSDT | 7 | +26.83 | **78.47%** (WORSE than NEAR baseline) |
| OPUSDT | 7 | +7.26 | 21.23% |
| TRXUSDT | 30 | +0.10 | 0.29% (breakeven) |
| ADAUSDT | 19 | −7.81 | 0% (loss) |

## Root cause — why Stage 1 was misleading

The IS-only screener was a **bad predictor of walk-forward Sharpe**:

1. **Single train/test split ≠ walk-forward**. A single 80/20 IS split
   gives one point estimate. Walk-forward retrains monthly and accumulates
   distributional information. Symbols can have great single-split Sharpe
   but fail when the model must retrain on a rolling 24-month window.

2. **Single seed ≠ 5-seed ensemble**. The production pipeline uses v1-style
   5-seed ensemble. The ensemble averages out per-seed Optuna idiosyncrasies.
   Symbols whose best-Optuna-seed produces a signal (ADA in iter-036 had
   this exact issue) look great in single-seed screening but wash out in
   ensemble averaging. ADA's -7.81 wpnl OOS here matches iter-036 exactly.

3. **Binary classification in screener ≠ production triple-class**. The
   screener predicted "long vs not-long" binary. Production does
   direction-aware (long / short / no-signal). Different class structure
   → different models → different behaviours.

4. **Survivorship ≠ overfit (in this case)**. The current universe
   (DOGE/SOL/XRP/NEAR) was assumed to be overfit because it was chosen
   through 59 iterations. But iter-v2/066 proves the legacy universe is
   actually GOOD under the production methodology — not merely survivor-
   biased. Swapping 3 of 4 symbols out cost 67% of OOS Sharpe.

## Concentration — ironically WORSE

XRP went from 33.55% in baseline to **78.47%** here. Removing NEAR
(44.44%) from the portfolio just let XRP fill the vacuum. This is
classic concentration whack-a-mole: the problem isn't NEAR per se, it's
the portfolio's structural sensitivity to whichever symbol happens to
generate good signals in a given OOS regime.

## Verdict — NO-MERGE (catastrophic failure)

Fails every criterion:

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined monthly Sharpe ≥ baseline +2.70 | ≥ 2.70 | 1.33 | FAIL |
| 2 | Concentration < 50% (n=4 outer cap) | < 50% | 78.47% | FAIL |
| 3 | OOS monthly Sharpe ≥ 0.85 × baseline | ≥ +1.41 | +0.56 | FAIL |
| 4 | IS monthly Sharpe ≥ 0.85 × baseline | ≥ +0.88 | +0.78 | FAIL |
| 5 | PF > 1, trades ≥ 50 | — | 1.28, 63 | PASS |
| 6 | OOS MaxDD ≤ 1.2 × baseline | ≤ 27.1% | 34.04% | FAIL |

5 FAILs. Hard NO-MERGE.

## Lesson for iter-v2/067

**The Stage 1 screener is not fit for purpose.** To properly evaluate
candidates we need either:
- **Full walk-forward Gate 3** (~30min/symbol × 20 candidates = 10h) —
  expensive but reliable
- **5-seed ensemble single-split screener** — partially addresses the
  ensemble issue, still not walk-forward
- **Use existing baseline as anchor**: only REPLACE 1 symbol at a time,
  keeping the other 3 fixed. This is slow (~2.5h per candidate) but lets
  us A/B test each substitution cleanly.

The "principled re-screening" idea is still valid — just needs a better
screener. Stage-1 screener output is INFORMATIONAL only, not MERGE-worthy.

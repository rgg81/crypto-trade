# team-01 IS report — t01-residual-momentum-v1

> **CANONICAL.** Every number below is from `cli.py team-run --team team-01`
> (`out/is_metrics.json` + `out/net_is.csv`), per charter §8. The QE's `strategy.py`
> reproduces the exp-013 reference (`scratch_common.build`) bit-for-bit, so the team-run
> artifact equals the earlier `out/exp-013_results.json` to full float64 precision.

## Headline (IS 2010-01-01 → 2024-06-30, organizer book construction)

| Metric | 1× cost (6 bps/side) | 2× cost |
|---|---|---|
| **Net Sharpe (monthly, √12)** | **+0.455** | **+0.418** |
| Max drawdown | −28.3% | −28.8% |
| Total return | +120.5% | +104.1% |
| Ann. gross turnover | 4.03× | 4.03× |
| Months scored | 174 | 174 |
| Median names long / short | 24 / 24 | 24 / 24 |
| Mean gross / mean net | 1.00 / ≈0 | 1.00 / ≈0 |

Regime scorecard (1×): bull **+0.44**, bear **−0.24**, chop **+0.73**.

## Reading

- **Cost robustness**: 1×→2× degrades Sharpe by only 0.037 — turnover 4×/yr makes the
  book nearly cost-insensitive (unsmoothed variant: +0.368 → +0.160; the EMA is load-bearing).
- **Breadth**: 24/24 median names per side, ~5× the validity floor; book is dollar-neutral
  by construction (net ≈ 1e-17 pre-cap).
- **Mechanism delivered**: vs the raw 12-1 reference (exp-003: +0.485 @1×, bear −1.27),
  the final residual book trades a noise-level headline difference (−0.03) for a
  collapsed bear channel (−0.24) and a stronger chop profile (+0.73 vs +0.69) — the
  pre-registered family thesis, confirmed on IS.
- **Burn-in**: first ~294 trading days are flat (beta 63 + formation 231); those early-2011
  flat months are inside the 174 scored months and dilute the headline slightly. Accepted —
  scoring window is charter-fixed.

## Negative results (reported with equal precision)

- Idiosyncratic-IR-only scaling (family textbook form): +0.409 @1× — kept only as half of
  the blend; plain-sum-only: +0.480 but bear −0.47 (re-imports the crash channel).
- Quantile (top/bottom) books: non-monotone in q (+0.399 at q=0.3, +0.484 at q=0.2) —
  noise-peak signature, rejected for the continuous rank book.
- Formation shorter than 252d: no burn-in recovery (+0.28..+0.30 at form 126) and chop
  turns negative (−0.67) — the 12-month horizon is where the mechanism lives.
- Un-smoothed daily book: turnover 22.5×/yr, Sharpe +0.16 @2× — fails cost robustness.

## Provisional experiment count

13 ledger lines total: reg-001, exp-002 (EDA), exp-003..exp-013 (11 evaluated batches).

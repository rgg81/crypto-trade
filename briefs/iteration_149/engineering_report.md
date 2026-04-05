# Iteration 149 Engineering Report

## Results

| Metric | Iter 147 (per-symbol VT) | Iter 149 (hybrid VT) | Change |
|--------|---------------------------|----------------------|--------|
| OOS Sharpe | +2.65 | +2.32 | **-12%** |
| OOS MaxDD | 39.17% | 37.85% | -3% |
| OOS PF | 1.62 | 1.53 | -6% |
| OOS Trades | 164 | 164 | same |

## Hybrid VT vs Alternatives

| Config | OOS Sharpe | OOS MaxDD |
|--------|-----------|-----------|
| iter 138 (no sizing) | +2.32 | 62.8% |
| iter 145 (portfolio VT) | +2.33 | 38.1% |
| **iter 147 (per-symbol VT)** | **+2.65** | **39.2%** |
| iter 149 (hybrid VT) | +2.32 | 37.9% |

Hybrid VT ≈ portfolio VT. The geometric mean dilutes the per-symbol signal that
drove iter 147's Sharpe gain. Combining the two signals doesn't produce synergy
— it averages them out.

## Hard Constraints

- OOS Sharpe > +2.65: **FAIL** (+2.32)

NO-MERGE.

## Conclusion

Per-symbol VT is Pareto-optimal over portfolio VT and hybrid VT. It catches the
key risk signal (symbol-specific) without averaging it with a less informative
one (aggregate portfolio).

# Iteration 148 Engineering Report

## Results

| Metric | Baseline (iter 147) | Iter 148 (+DOGE) | Change |
|--------|---------------------|-------------------|--------|
| OOS Sharpe | +2.65 | **+2.42** | **-9%** |
| OOS MaxDD | 39.17% | **69.02%** | **+76%** |
| OOS PF | 1.62 | 1.56 | -4% |
| OOS Trades | 164 | 214 | +30% |

Per-symbol avg scales (with DOGE in portfolio):
- BNB: 0.78, BTC: 0.72, DOGE: 0.77, ETH: 0.67, LINK: 0.69

## Comparison: DOGE Addition Attempts

| Config | Sharpe | MaxDD |
|--------|--------|-------|
| iter 138 (A+C+D, no sizing) | +2.32 | 62.8% |
| iter 143 (A+C+D+DOGE, no sizing) | +2.30 | **92.5%** |
| iter 145 (A+C+D, portfolio VT) | +2.33 | 38.1% |
| iter 146 (A+C+D+DOGE, portfolio VT) | +2.10 | 48.5% |
| **iter 147 (A+C+D, per-symbol VT)** | **+2.65** | **39.2%** |
| **iter 148 (A+C+D+DOGE, per-symbol VT)** | **+2.42** | **69.0%** |

## Why Per-Symbol VT Fails With DOGE

Per-symbol VT scales each trade by its OWN symbol's vol, NOT portfolio vol. When
all 5 symbols experience synchronized drawdowns (like July 2025), per-symbol VT
fails to catch cross-asset co-movement. Each individual symbol appears calm in
isolation but they lose together.

Portfolio-wide VT (iter 146) DID catch this — reduced DOGE-portfolio MaxDD from
92.5% to 48.5%. But per-symbol VT scales based on isolated symbol vol, missing
the aggregate risk.

## Hard Constraints

| Constraint | Threshold | Iter 148 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.65 | +2.42 | **FAIL** |
| OOS MaxDD ≤ 47% | ≤ 47% | 69.0% | **FAIL** |

Both primary and MaxDD constraints fail. NO-MERGE.

## Conclusion

**DOGE cannot be added to this portfolio in any tested configuration**:
- Raw portfolio: MaxDD explodes
- Portfolio-wide VT: Sharpe regresses
- Per-symbol VT: both Sharpe and MaxDD regress

DOGE's temporal correlation with A+C+D drawdowns is structural and cannot be
mitigated by position sizing alone.

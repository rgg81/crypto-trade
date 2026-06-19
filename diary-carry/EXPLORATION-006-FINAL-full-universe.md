# carry-iteration EXPLORATION-006 FINAL — cash-and-carry on the FULL universe (279 coins): definitive verdict

Definitive run on the complete spot∩perp∩funding universe (279 coins with ≥1000 candles, from the
full 338-coin spot-listed set). `analysis/cash_carry.py` (robust loader: dedup open_time, skip
unreadable). Supersedes the 49/80-coin previews.

## Result (diversified M=9, thresh=0, ~93 coins, turnover 0.07)
| cost | net IS | net OOS | DD |
|---|---|---|---|
| TAKER 0.07%/side | +1.06 | −3.63 | −22% |
| **MAKER ~0.01%/side** | **+2.21** | **+1.14** | **−5%** |
| ZERO | +2.42 | +2.92 | −5% |

**Spot-liquidity floor (MAKER cost) — the capacity-respecting numbers:**
| floor | net IS | net OOS | DD | coins |
|---|---|---|---|---|
| no floor | +2.21 | **+1.14** | −5% | 93 |
| **$5M spot** | +2.04 | **−0.13** | −7% | 28 |
| **$20M spot** | +2.26 | **−0.09** | −3% | 8 |

funding-leg OOS Sharpe stays huge (+5–8) at every floor; the NET is what matters.

## The honest verdict (this supersedes the optimistic 80-coin preview)
- **The full universe REVEALS the capacity ceiling.** The no-floor OOS +1.14 leans on the ~93
  positive-funding coins INCLUDING small-spot ones. Impose a tradeable spot floor and the coin count
  collapses (93 → 28 → 8) and net OOS goes to **~0 / slightly negative** (−0.13 / −0.09). The
  80-coin preview's +0.42 was an alphabetical-subset artifact.
- **Why:** cash-and-carry net SCALES WITH BREADTH — the per-coin funding income is tiny, so the net
  edge needs many coins to clear the cost + basis-noise floor. Restricting to tradeable liquidity
  leaves too few coins, and the aggregate income drops below that floor → net ~0.
- **The good news that remains:** the DD is TINY (−3 to −7%, vs perp-perp's −37 to −90%) and the
  failure is GENTLE (~0, not deeply negative). The spot leg genuinely hedges. And taker still kills
  it everywhere (−3.63) — maker execution is mandatory.

## VERDICT: cleanest result of the session, but NOT a deployable positive edge at size
Cash-and-carry is the only thing that doesn't blow up — but capacity-respecting (tradeable spot
floor, maker cost) its OOS is **~breakeven**, not positive. The funding income is real and structural,
but it is **not net-capturable as a positive edge at meaningful size** in any form tested
(perp-perp cross-sectional carry OR spot-perp basis). Deploy: NO.

## Session-level conclusion
Across trend, single-coin LightGBM, cross-sectional momentum, pair-momentum, broad perp-perp funding
carry, and spot-perp cash-and-carry — every candidate, under the FULL anti-hype gauntlet (realistic
engine + walk-forward + survivorship-clean universe + capacity floor + realistic cost + alpha-vs-beta),
fails to deliver a clean, capacity-respecting, positive-OOS deployable edge. The methodology stayed
honest throughout (critic-verified leak-free/bias-free); the EDGES are what don't survive. That is the
true, hype-free state of this research program. Remaining honest options are STRUCTURAL/EXECUTION
(maker-rebate market-making, or non-Binance/cross-venue basis) — different infrastructure, a user call.

## Residual rigor (does not change the verdict)
Params here are still hand-picked (M=9, thresh=0). A walk-forward param selection (no bias) can only
do ≤ the best hindsight pick, so it cannot rescue a ~0 capacity-respecting net. Worth running for
completeness, but the capacity ceiling is the binding constraint, independent of M.

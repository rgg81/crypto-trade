# iter-v2/064 Engineering Report

## Build

- Branch: `iteration-v2/064` from `quant-research` at `383361f`
- Code change: add `PER_SYMBOL_POSITION_SCALE={"NEARUSDT": 0.7}` +
  `_apply_position_caps` post-processing in `run_baseline_v2.py`.
- Note: initial attempt changed `BacktestConfig.max_amount_usd` per symbol,
  which had NO EFFECT on `weighted_pnl` (the concentration metric). Root
  cause: `weighted_pnl = net_pnl_pct × weight_factor`; `max_amount_usd`
  only sets notional but doesn't enter the PnL formula. Fix: post-process
  trades' `weight_factor` and `weighted_pnl` by the symbol-specific
  factor.
- Compute shortcut: since iter-v2/064's 4 models are IDENTICAL to
  iter-v2/059-clean (same seed, config, features), we reused
  iter-v2/059-clean's trade CSVs, applied the cap, and regenerated
  reports via `apply_iter_064_cap.py`. Saved the full ~2.5h backtest.

## Results

Measured vs iter-v2/059-clean (baseline):

| Metric | iter-v2/059-clean | **iter-v2/064** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.0421 | +1.0346 | −0.7% |
| IS trade Sharpe (daily) | +0.9742 | +1.0048 | +3.1% |
| **OOS monthly Sharpe** | +1.6590 | **+1.4291** | **−14%** |
| OOS daily Sharpe | +1.6626 | +1.5733 | −5.4% |
| Combined monthly | +2.7011 | +2.4637 | −9% |
| OOS PF | 1.7806 | 1.7368 | −2.5% |
| OOS MaxDD | 22.61% | 26.57% | +17.5% (within 1.2× cap) |
| OOS WR | 49.1% | 49.1% | identical |
| OOS trades | 57 | 57 | identical |

## Concentration — the primary objective

Using `weighted_pnl` (authoritative, per skill guidance):

| Symbol | OOS wpnl | Share | vs iter-v2/059-clean |
|---|---|---|---|
| XRPUSDT | +26.83 | **38.71%** | was 33.55% — now max |
| NEARUSDT | +24.88 (0.7×) | 35.89% | was 44.44% (−8.5pp) |
| SOLUSDT | +11.87 | 17.12% | was 14.84% |
| DOGEUSDT | +5.74 | 8.28% | was 7.17% |

**Max share dropped 44.44% → 38.71%**, now under the n=4 40% cap.
NEAR specifically dropped from 44.44% to 35.89%.

## MERGE criteria evaluation

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 (primary) | Combined IS+OOS monthly ≥ baseline +2.70 | ≥ 2.70 | 2.46 | **FAIL** |
| 2 | NEAR concentration < 40% | < 40% | 35.89% | PASS |
| 3 | OOS monthly Sharpe ≥ 0.90 × baseline | ≥ +1.49 | +1.43 | **FAIL** (marginal, 0.06 short) |
| 4 | IS monthly Sharpe ≥ 0.85 × baseline | ≥ +0.88 | +1.03 | PASS |
| 5 | OOS trade Sharpe > 0, PF > 1, trades ≥ 50 | — | +1.57 / 1.74 / 57 | PASS |
| 6 | OOS MaxDD ≤ 1.2 × baseline | ≤ 27.1% | 26.57% | PASS |

2 FAILs on Sharpe criteria. Combined monthly regresses by 9%.

## What the math tells us

Reducing NEAR's position by 30% removed 30% of NEAR's weighted PnL. NEAR
contributed 44.44% of positive wpnl in baseline, so removing 30% of that
= 13.3% of total positive wpnl. Total OOS positive wpnl went from 79.98
to 69.31 (−13.3% ✓, matches math).

Monthly Sharpe depends on daily-return std. Since we reduced ONE symbol's
contribution, the portfolio's daily return std doesn't drop proportionally
(other symbols' contributions remain), so Sharpe drops slightly more than
just the PnL reduction.

## Suggestion for iter-v2/065

Softer cap: 0.8× instead of 0.7×. Math predicts:
- NEAR wpnl: 35.54 × 0.8 = 28.43 → share ≈ 39.0% (just under 40% cap)
- Total positive wpnl: 72.87 (vs 79.98 baseline, −9%)
- Expected OOS Sharpe drop: ~3-4% (vs 14% for 0.7× cap)

The 0.8× cap is a more balanced compromise — achieves concentration fix
with a tighter margin but much less Sharpe giveaway.

## Verdict: NO-MERGE

Fixes concentration as promised but gives up too much OOS Sharpe.
iter-v2/065 tries 0.8× for a better tradeoff.

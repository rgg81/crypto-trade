# iter-v2/066 Diary

**Date**: 2026-04-23
**Type**: EXPLORATION (generic universe re-screening)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** — catastrophic (OOS monthly −67%, concentration 78% XRP)

## Summary

User challenged the NEAR-specific cap in iter-v2/064-065 as "biased and
overfitting." Agreed — iter-v2/066 replaced it with a generic IS-only
ranking: screen every eligible candidate, pick top-4 by Stage-1 Sharpe,
run baseline.

Stage 1 picked: **OP, XRP, TRX, ADA** (top 4 by IS holdout Sharpe).
Fail-fast gate PASSED (top-5 mean 6.51 vs current 4.95, +31.5%).

Stage 2 result: DISASTER. OOS monthly dropped 67% (+1.66 → +0.56),
concentration WORSE (XRP 78%, NEAR baseline was 44%), MaxDD 34% (+50%).

## The Stage 1 screener was a bad proxy

Single 80/20 IS split with 5 Optuna trials and 1 seed does NOT predict
walk-forward + 5-seed-ensemble Sharpe:

| Reason | Evidence |
|---|---|
| Single split ≠ walk-forward | Symbols retrain monthly in production; a single split overestimates stability |
| Single seed ≠ 5-seed ensemble | Ensemble averaging washes out per-seed idiosyncrasies. ADA's exact iter-036 failure mode replays here (−7.81 wpnl) |
| Binary classes ≠ triple-class | Screener predicted "long vs not-long", production does direction-aware long/short/none |

## Per-symbol OOS breakdown — the counterfactual

| Symbol | Stage-1 rank | Stage-1 Sharpe | Walk-forward reality |
|---|---|---|---|
| OP | #1 | 8.26 | Only 18 trades total (short history) — screener over-scored |
| XRP | #2 | 6.59 | +26.83 wpnl — the only winner, but its share blew up to 78% |
| TRX | #3 | 6.18 | 99 trades but +0.10 wpnl — model finds no edge in ensemble |
| ADA | #4 | 5.76 | −7.81 wpnl in 19 OOS trades — same failure as iter-036 |

**Anti-pattern identified**: IS-only single-seed screening picks symbols
that look predictable because of happy-accident Optuna fits. The
production 5-seed ensemble dilutes away those accidents, leaving no edge.

## What this proves about the current baseline

The user's hypothesis was "DOGE/SOL/XRP/NEAR is overfit because it was
chosen by iteration." iter-v2/066 empirically disproves that: replacing
3/4 of the universe with principled top-of-ranking candidates cost 67%
OOS Sharpe. The legacy universe is actually well-fit to the 5-seed
ensemble system — not merely survivor-biased.

**Revised understanding**: the current universe has real signal. The
concentration issue (NEAR 44%) is a symptom of NEAR having genuine edge,
not a symptom of overfit. Any "principled" replacement needs to
reproduce the ensemble compatibility, which single-split screening
cannot measure.

## MERGE criteria evaluation

| # | Criterion | Actual | Pass |
|---|---|---|---|
| 1 | Combined monthly Sharpe ≥ 2.70 | 1.33 | FAIL |
| 2 | Concentration < 50% | 78.47% (XRP) | FAIL |
| 3 | OOS monthly Sharpe ≥ 1.41 | 0.56 | FAIL |
| 4 | IS monthly Sharpe ≥ 0.88 | 0.78 | FAIL |
| 5 | PF > 1, trades ≥ 50 | 1.28, 63 | PASS |
| 6 | OOS MaxDD ≤ 27.1% | 34.04% | FAIL |

**5 FAILs. Hard NO-MERGE.**

## Next Iteration Ideas — iter-v2/067

### Insight: use walk-forward screening, not single-split

Option A: **Proper Gate 3 with walk-forward + ensemble**
- n_trials=10 (still small), 3-seed ensemble (partial), walk-forward 24mo
- ~5-8 min per candidate × 10 shortlist = 1h compute
- Much better predictor of production performance

Option B: **A/B test 1 symbol at a time**
- Keep 3 legacy symbols, sub in 1 candidate. Run full baseline (~2.5h)
- Repeat for each candidate to test
- Expensive (10 candidates × 2.5h = 25h) but definitive

Option C: **Accept the legacy universe is good, focus elsewhere**
- NEAR concentration at 44.44% passes the 50% outer cap (though fails
  inner 40%). Maybe that's acceptable for now.
- Focus on improving OOS Sharpe or reducing MaxDD instead.

### Recommendation: iter-v2/067 = Option A

Build a better Stage 1 screener: mini walk-forward (last 18 months of IS
only) + 3-seed ensemble + n_trials=10. Gives a more faithful proxy while
keeping compute manageable (~1h total).

If that screener still identifies non-current symbols as top, we have a
legitimate candidate. If it confirms the current universe is top, we
stop trying to re-screen and focus on risk/feature improvements to the
current baseline.

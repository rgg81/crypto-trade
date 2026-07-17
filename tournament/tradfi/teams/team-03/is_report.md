# team-03 IS report — FINAL (canonical team-run)

> STATUS: FINAL. Every number below is sourced from the canonical `cli.py team-run --team
> team-03` artifacts on the frozen IS snapshot: the headline table + regime line come
> verbatim from `out/is_metrics.json`; the sub-period Sharpes are recomputed from the
> canonical net series `out/net_is.csv` with the tournament's own estimator (`core_tradfi
> .msharpe`). The QE's `strategy.py` transcribes the frozen spec (`research_brief.md` §2);
> team-run reproduces `experiments.jsonl` exp-014 to full float precision (Sharpe @1x
> 0.5679092435090428, @2x 0.4390872273186196), confirming the transcription is exact.

Family: `t03-sector-residual-reversal-v1` — stress-gated sector-residual 5d reversal.
Frozen spec: `research_brief.md` §2. Experiments: 13 material (exp-002 … exp-014).

## Headline (canonical team-run, `out/is_metrics.json`)

| Metric | @1x cost | @2x cost |
|---|---|---|
| Net IS Sharpe (monthly-summed, √12) | **0.568** | **0.439** |
| Max drawdown | −0.325 | −0.370 |
| Annualised turnover | 15.5 | 15.5 |
| Median names long / short (active days) | 25 / 23 | — |
| Mean net exposure | +0.032 | — |
| Total return / n months | +202.5% / 174 | — |

Regime Sharpe @1x: bull 0.50 / bear −0.15 / chop 1.17 (from `out/is_metrics.json`).
Sub-periods @1x (recomputed from `out/net_is.csv`): 2010-14: 0.431 · 2015-19: 0.772 ·
2020-24H1: 0.525 · 2015-24H1: 0.631.
Breadth validity floor (median >= 5/side): PASS. Cost robustness: 2x keeps 77% of Sharpe
(0.4391 / 0.5679 = 0.773).

## Negative results (reported with equal precision)

- UNGATED sector-residual reversal is NOT deployable at 6 bps/side in this universe:
  best net @1x = −0.53 (L=5, EMA10, exp-006); gross Sharpe <= 0.40 at every horizon
  L ∈ {1,2,3,5,7,10,15} (exp-002/003).
- Tail-conditioned fading (soft-threshold z_in ∈ {0.5,1.0,1.5}) REDUCES gross edge —
  large dislocations drift (news), they do not revert; z_in >= 1.0 also breaches the
  breadth floor (exp-005).
- Intraday-exhaustion gate (close-location-in-range): negative at all cells (exp-007).
- Vol-standardisation alone, smoothing alone: cannot rescue the ungated book (exp-004/006).
- Level-VIX gate is knife-edged (VIX>24: 0.00 vs VIX>25: +0.50); the rolling-percentile
  gate is smooth across 0.80-0.90 and was chosen for that robustness (exp-008/009).
- Rejected refinements at the final config: inverse-vol sizing (−0.60), sector-demeaned
  weights (−0.07), skip-day (−0.36) (exp-011).

## Interpretation

The registered liquidity-provision premium exists but is state-dependent: it clears the
6 bps/side hurdle only in the top ~15% of VIX states (rolling 252d percentile > 0.85), where
forced flows widen idiosyncratic dislocations and reversion is violent enough to pay. The
final book is flat ~85% of days, trades ~15.5x/yr turnover, and earns primarily in
stress/chop phases (chop +1.17) while staying near-flat through calm bulls — by construction
decorrelated from momentum-family books. Known weakness: mildly negative inside sustained
macro-bear windows (−0.15); the plateau alternative (pure rank transform, +0.62 @1x) was
declined because its bear Sharpe was −0.46 — selection followed the pre-registered rule of
sacrificing headline Sharpe for regime balance.

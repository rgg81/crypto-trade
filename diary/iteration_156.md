# Iteration 156 Diary

**Date**: 2026-04-08
**Type**: EXPLORATION (meta-labeling post-processing)
**Decision**: **NO-MERGE** — IS-best config fails OOS Sharpe constraint

## Summary

Meta-labeling with 8 meta-features (NATR/ADX/RSI for traded symbol, BTC
NATR, direction, hour, rolling-10-WR, days-since-last) trained walk-forward
on iter 138's closed IS trades. Filter threshold grid-searched on IS only.

## Key Findings

### IS-best (walk-forward-valid)

**thresh=0.40**: keeps 459/652 IS trades (70%) and 122/164 OOS trades (74%).
- IS Sharpe: +0.83 (vs baseline +1.33, **-37%**)
- OOS Sharpe: +2.59 (vs baseline +2.83, **-8.3%**)
- OOS MaxDD: 18.03% (vs 21.81%, -17% improvement)
- OOS PF: 1.87 (vs 1.76, +6%)
- OOS Calmar: 5.13

**Primary OOS Sharpe constraint FAILS.** NO-MERGE.

### The seductive OOS-best result

**thresh=0.50**: OOS Sharpe +3.26 (+15% above baseline), OOS MaxDD 8.78%
(-60% vs baseline), OOS PF 2.63 (+49%). But IS Sharpe is +0.71 (terrible),
so IS-best selection would NEVER pick this. Claiming this result would be
**look-ahead bias**.

### Meta + VT are complementary

Meta-filter WITHOUT VT (scale=1 for kept trades) is strictly worse at all
thresholds. VT protects during crash periods, meta-filter drops weaker
trades. Together > either alone.

### The Paradox

Meta-filter HURTS IS Sharpe at every threshold but IMPROVES OOS MaxDD at
every threshold. The meta-model doesn't identify profitable trades within
IS, yet its OOS filter reduces drawdowns uniformly.

**Interpretation**: The meta-model may be learning patterns (e.g., high
NATR + specific hour + direction combinations) that happen to coincide with
the July 2025 crash period, but those patterns don't generalize across the
2020-2025 IS period. This is a classic case where OOS-best looks better
than IS-best due to chance alignment with the specific OOS regime.

## Research Checklist

- **A (Feature Contribution)**: 8 meta-features constructed, walk-forward
  valid. Feature importance not extracted (would require refitting on full
  IS as final analysis step).
- **E (Trade Pattern)**: Primary model produces 652 IS / 164 OOS trades
  with 44.5% IS profitability rate. Meta-model cannot identify which are
  which within IS training regime.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, X, X, X, X, X, E, **E**] (iters 147-156)
Exploration rate: 4/10 = 40% ✓

## Insights for Future Work

1. **The missing feature is `primary_confidence`**. Iter 138's trades.csv
   doesn't store the LightGBM predict_proba output. Re-running iter 138
   with confidence capture would provide the single most valuable meta
   feature (per AFML Ch. 3 literature).

2. **Nested walk-forward for threshold**. Current approach grid-searches
   threshold on the full IS output. A more rigorous approach: use
   walk-forward CV to select threshold month-by-month based on prior
   OOF results.

3. **Meta-model is too shallow**. With only 551 IS training trades (too few
   for walk-forward), LightGBM's signal is noisy. The model needs richer
   features OR a simpler rule (e.g., "avoid trades when BTC NATR > 80th
   percentile").

## Next Iteration Ideas

1. **Re-run iter 138 with primary_confidence captured** → rerun iter 156
   with 9 meta-features (primary_confidence added). This would need a
   new walk-forward run of the primary LightGBM model (~5h compute).

2. **Simple rule-based meta-filter** (no LightGBM meta-model):
   - Drop trades where BTC NATR_21 > 80th percentile (too volatile)
   - Drop trades where traded-symbol ADX < 15 (no trend)
   - Drop trades where hour_of_day is the worst historical hour
   Grid the rule thresholds. Simpler, more interpretable, potentially less
   over-fit.

3. **Confidence-weighted VT** (future, also requires primary_confidence):
   use confidence to MODULATE the VT scale instead of as a binary filter.
   Trade size = primary_confidence × VT_scale.

4. **Accept v0.152 as final for paper trading**. After 12 more iterations
   beyond the "strategy is DONE" call in iter 154, we've confirmed:
   - min_scale parameter exhausted (iters 152, 153)
   - Per-symbol VT parameters exhausted (iter 155)
   - Meta-labeling with 8 features does not beat baseline (iter 156)

   Structural work (primary_confidence capture, entropy/CUSUM features,
   event-driven sampling) requires engine changes and hours of compute
   per test. Paper trading is the more time-valuable next step.

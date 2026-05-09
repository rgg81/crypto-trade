# Engineering Report — iter-v3/040

## Status: READY-FOR-CRITIC

PROMISING-MECHANICAL — REVERT to iter-v3/029 config produces bit-identical results (verified). Cycle 3 anchor established.

## Headline Metrics

| Metric | Value | vs iter-v3/029 target |
|--------|-------|------------------------|
| IS Sharpe | +0.7926 | **bit-identical** |
| OOS Sharpe | +1.7653 | **bit-identical** |
| All 4 per-symbol OOS | identical to iter-v3/029 | **bit-identical** |

Per-symbol Optuna independence confirmed: clearing V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL produces identical Optuna trajectories as iter-v3/029.

## Verdict

**EXPLORATION-PROMISING-MECHANICAL** — strict accretive baseline restore. Cycle 3 anchor for IS-lift work.

## Recommendations

iter-v3/041 axis: feature pruning (drop bottom-3 importance features universally).

Rationale:
- iter-v3/030-038 showed adding features often breaks IS aggregate
- Pruning REDUCES feature count → less Optuna search noise → cleaner IS fit
- Safest first axis for IS-lift cycle 3

EDA: identify bottom-3 importance features from iter-v3/040 portfolio importance (or iter-v3/028 multi-seed which is the canonical baseline).

Status: READY-FOR-CRITIC.

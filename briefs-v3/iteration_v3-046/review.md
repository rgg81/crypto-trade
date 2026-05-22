# Phase 7.5 Critic Review — iter-v3/046

OVERALL: **EXPLORATION-NEGATIVE** — BCH ATR (2.0, 1.5) caused -45 BCH OOS swing. Mirror mechanism doesn't transfer to symbols without regime mismatch.

## Lesson Refined

Wider-SL ATR mechanism is REGIME-MISMATCH-SPECIFIC:
- ALGO had extreme LONG SL ratio 4.5:1 → wider ATR helped (+49 swing)
- LDO had IS→OOS SL:TP shift 1.14→2.33 → wider ATR helped (+13 swing)
- BCH had stable SL:TP 1.93/1.93 → wider ATR HURT (-45 swing)

**Stable SL:TP across IS/OOS = WRONG axis.**

## Memory Rule Recommendation

Add to `feedback_v3_axis_selection_quant_discipline.md` or save new rule: per-symbol ATR widening only applies to symbols with regime mismatch evidence (IS→OOS SL:TP shift > 30% OR extreme direction asymmetry > 4:1). Stable SL:TP rules OUT this axis for that symbol.

## Recommendations

iter-v3/047: REVERT BCH ATR + dispatch QR for BCH direction-asymmetric axis. BCH LONG IS -25% / SHORT IS +49% — direction filter or LONG-only ATR may help.

## Catalog Row

`| iter-v3/046 | 2026-05-09 | Per-symbol ATR for BCH (2.0, 1.5) — QR mirror-mechanism extension | -0.54 (vs iter-v3/045 +0.7459) | +2.4738 (Δ -1.05; BCH -45 swing 39.5%→40.0% WR despite WR similar; PnL collapsed) | EXPLORATION-NEGATIVE | NO — mirror mechanism doesn't apply to symbols with stable SL:TP; iter-v3/047 = revert + BCH direction-asymmetric axis |`

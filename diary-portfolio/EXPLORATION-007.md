# portfolio-iteration EXPLORATION-007 — agent-driven: refresh+guard KEPT, de-lever REJECTED (critic)

**Agent-driven** (user mandate): risk-engineer built + validated; quant-critic reviewed before keeping.
Funding bug fixed (iter-004) + universe refreshed to current. Code: `analysis/portfolio/iter_007_riskctl.py`,
`risk_probe.py`.

## What changed + verdicts
| item | result | verdict |
|---|---|---|
| funding-fix (nearest-match 4h) | removes ~28% inflation | KEEP (critic: clean, 60.8% coverage) |
| data refresh (degenerate tail gone) | OOS +1.08 → **+1.37** | KEEP (critic: legitimate de-biasing, no new leak; 0 OOS candles guarded) |
| min-eligible guard | neutral on current data | KEEP as free leak-safe safety net (insurance) |
| vol-spike de-lever (rv 21/168 >1.5×→0.5) | +0.16 OOS *in iter_007* | **REJECT** |

## The critic catch (why the de-lever is rejected)
iter_007 vol-targets ONCE at the end (raw-stitch); canonical iter_005 vol-targets per-λ then stitches.
The de-lever's +0.16 OOS only appears under the re-ordered accounting; measured as an overlay on the
CANONICAL net it adds **+0.01 OOS — noise** on n=16 months. The lift was a stitch-order artifact, not
edge. Not promoted. (De-lever IS leak-safe and the config is not OOS-maxed — it's simply not accretive.)

## Honest baseline (critic-cleared)
Canonical iter_005 walk-forward λ on funding-fixed + refreshed data: **IS +1.30 / OOS +1.37 / DD −23%**,
positive every year. trend-only +0.73 → carry-tilt +1.37 (the tilt remains a real walk-forward lift).

## Verdict: refresh + funding-fix + guard PROMOTED; de-lever REJECTED. Baseline OOS +1.08→+1.37 (honest).
## Next (agent-driven)
- iter-008: a genuinely orthogonal accretive change (short-term reversal overlay, OR per-coin caps for
  DD), measured on the CANONICAL net (not raw-stitch), critic-reviewed. Robustness-prove any new param.

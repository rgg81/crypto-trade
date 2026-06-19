# portfolio-iteration EXPLORATION-009 — per-coin weight caps (REJECT, premise falsified)

**Agent-driven** (risk-engineer). Built on the canonical iter_005 net (cap=∞ byte-reproduces baseline,
max|Δnet|=0). Clip |w_i| to a cap, renormalize gross, iterate to convergence. Code:
`analysis/portfolio/iter_009_caps.py`.

## Result vs canonical baseline (IS +1.30 / OOS +1.37 / DD −23%)
| cap | IS | OOS | maxDD | effN OOS | top3 \|PnL\| | cells clipped |
|---|---|---|---|---|---|---|
| 0.10 | +1.31 | +1.40 | −23% | 14.6 | 17.2% | ~10% |
| 0.15 | +1.26 | +1.33 | −23% | 13.4 | 17.3% | ~2% |
| 0.20 | +1.29 | +1.37 | −23% | 13.1 | 17.7% | ~0.8% |
| ∞ (base) | +1.30 | +1.37 | −23% | 13.0 | 17.8% | 0% |

## Read — REJECT (premise falsified)
- **The book was never concentrated**: inverse-vol weights already give effective-N ≈ 13, max-|w| ≈
  0.15. Caps ≥0.15 clip <2% of cells (no-ops). The "Pareto-neutral" tags are inertness, not edge.
- **maxDD −23% does NOT budge at any cap** (incl. cap=0.10 which binds ~10%). The DD is NOT driven by
  single-name concentration — it's correlated portfolio-wide trend reversals (already governed by the
  per-λ vol-target). A weight cap cannot fix a DD that isn't a concentration problem.
- cap=0.10 "+0.03 OOS" is λ-selection-path noise (flat IS). The critic's "top-3 = 25.6%" was share of
  gross-POSITIVE PnL over the sample, not live sizing — on total |PnL| it's ~17.8% (already diversified).

## Verdict: REJECT. Baseline unchanged (OOS +1.37). DD lever lives in correlation/regime exposure, not
per-name caps.
## Next: iter-010 — a potentially-REAL lift: magnitude-weighted (z-score/rank) trend & carry signals
instead of mean-SIGN (continuous signals carry more info than sign); OR a correlation/regime gross
overlay for the DD. Canonical net, robustness-proved, critic-gated.

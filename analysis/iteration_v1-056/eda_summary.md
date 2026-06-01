# EDA — iter-v1/056 Bundle Composition (IS-only)

IS-only barrier: `close_time < OOS_CUTOFF_MS = 1742774400000` (2025-03-24)

## Per-Component IS Evidence

| Component | Symbol | Source | IS Sharpe | IS Trades | IS WR% | IS Net PnL% | IS Lift | Weight |
|---|---|---|---|---|---|---|---|---|
| C1-BTC | BTCUSDT | iteration_v1-054 | +0.2614 | 139 | 37.4% | -23.49% | +1.1114 | 0.2 |
| C2-ETH | ETHUSDT | iteration_v1-055 | -0.2082 | 138 | 39.1% | -18.34% | +0.4018 | 0.2 |
| C3-DOT | DOTUSDT | iteration_v1-051 | -0.2355 | 125 | 46.4% | +111.47% | +0.9945 | 0.2 |
| C4-LINK | LINKUSDT | iteration_v1-baseline | +2.2500 | 146 | 45.2% | +72.06% | +0.0000 | 0.2 |
| C5-LTC | LTCUSDT | iteration_v1-baseline | +0.1700 | 124 | 39.5% | +3.27% | +0.0000 | 0.2 |

Hypothetical weighted IS PnL (sum of component IS_PnL × 0.2): **+28.9936%**
(Informational approximation; actual bundle metrics computed by run_iteration_056.py CSV-replay aggregator.)

## Universe Disjointness

**PASS** — all 10 pairwise intersections are empty. Each coin owned by exactly ONE component (brief Section 11.A).

## Weight Sum

**PASS** — sum = 1.00000000 (within 1e-6 of 1.0). EQUAL weights: 5 × 0.2 = 1.0 (brief Section 11.B).

## Weight Derivation Method

Weights are **literal constants** (0.2 each) — not derived from IS Sharpe, IS trade counts, or any OOS metric.  IS-Sharpe-proportional weighting would zero C1-BTC (IS +0.26) and collapse C2-ETH / C3-DOT toward zero, defeating the per-coin specialist hypothesis (brief Section 11.B rationale).

## Per-Regime Tagger Debt

Regime tagger not wired in EXPLORATION runners at /049-/055.  All EXPLORATION trades in 'unknown' regime bucket.  **run_iteration_056.py** wires the tagger at the bundle-aggregation step (brief Section 3.8 Rec 2).  Bundle per-regime Pareto table = primary MERGE gate.

## IS-Only Provenance

All reads in this script use `in_sample/per_symbol.csv` paths only.
No `out_of_sample/` file is opened.  OOS values referenced in 'notes' fields are informational only (per brief Section 8.5 EXPLORATION-budget rule).

# iter-v1/045 — Substrate Proposal Under No-Coin-Overlap Rule

## Decision: Option III (Pure cohort federation)

Investigation: `run_baseline_v186.py` already runs **Model A, C, D, E as independent `run_backtest()` invocations** with separate `BacktestConfig` + `LightGbmStrategy` instances. Trades are concatenated and sorted by `close_time` post-hoc. Therefore Model A (BTC+ETH) and Model D (LTC) are mechanically extractable as standalone components — no new training, no code surgery. Just call `run_model(...)` and skip C+E.

This makes Option III the cleanest substrate.

## Proposed /045 Composition — 3 Components

| Component | Source | Universe | Features | ATR TP/SL | R1 | R2 | R3 | IS trades | IS Sharpe (daily, ann.) | IS sum PnL |
|---|---|---|---|---|---|---|---|---|---|---|
| **C1 = baseline_A** | baseline_v186 Model A | BTC + ETH | BASELINE_FEATURE_COLUMNS (193) | 2.9 / 1.45 | OFF | OFF | ON (70th pct) | 249 | +0.468 | +31.79 |
| **C2 = baseline_D** | baseline_v186 Model D | LTC | BASELINE_FEATURE_COLUMNS (193) | 3.5 / 1.75 | ON (3, 27) | OFF | ON (70th pct) | 119 | +2.099 | +91.52 |
| **C3 = /036** | iter-v1/036 trend-scan | LINK + DOT | /036 trend-scan feature set | per-/036 | per-/036 | OFF | per-/036 | 281 | -0.037 | -4.09 |

OOD/R3 cutoff and Optuna hyperparameter regions are inherited unchanged from each source.

## No-Coin-Overlap Verification

| Coin | C1 baseline_A | C2 baseline_D | C3 /036 | Owner count |
|---|---|---|---|---|
| BTC  | OWN | — | — | **1** |
| ETH  | OWN | — | — | **1** |
| LTC  | — | OWN | — | **1** |
| LINK | — | — | OWN | **1** |
| DOT  | — | — | OWN | **1** |

All 5 coins owned by exactly one component. **Rule satisfied.**

## Weight Derivation — Methodology Decision

Three deterministic IS-only candidates were computed:

| Scheme | C1 (BTC+ETH) | C2 (LTC) | C3 (LINK+DOT) | Notes |
|---|---|---|---|---|
| Equal | 0.333 | 0.333 | 0.333 | No IS dependence; safest under uncertainty |
| IS-daily-Sharpe-proportional | 0.185 | 0.830 | -0.015 | C3 IS Sharpe ≈ 0 ⇒ near-zero weight |
| IS-trade-count-proportional | 0.384 | 0.183 | 0.433 | Capacity-weighted; ignores edge quality |

**Selected: Equal weights (1/3 each).**

Rationale:
1. C3 (/036) was admitted to the bundle because its **OOS Δ vs LINK-in-pool was +1.08**, not because its IS Sharpe is strong (it is ~0). IS-Sharpe-proportional would erase C3, defeating the rule-compliance design that motivated /045.
2. Trade-count-proportional gives C2 (LTC, the highest-edge component on IS) only 0.183 — capacity-weighting penalizes the lowest-trade-count specialist precisely when it is the highest-quality one. Wrong direction.
3. Equal weights minimize researcher-degrees-of-freedom (no IS-derived knob), and lean on the existing OOS-validated baseline weighting convention.

Falsifier: if /045 equal-weighted OOS Sharpe undershoots /044 by >0.50 AND C3 attribution shows negative OOS contribution, the next iteration evaluates replacing C3 with /043 (LINK-only PROMISING +0.59 OOS Δ) — DOT then needs a separate sole-owner; candidate is /029 DOT-only TF. That escalation is not in /045 scope.

## /045 Implementation Plan

**Runner**: `run_iteration_045.py` (new) — modeled on `run_baseline_v186.py` but only invokes the two baseline cohorts that survive the rule.

**Sub-runs (sequential, independent)**:
1. `run_model("A (BTC/ETH)", ("BTCUSDT","ETHUSDT"), 2.9, 1.45, apply_r1=False)` ← identical to baseline_v186 call
2. `run_model("D (LTC + R1)", ("LTCUSDT",), 3.5, 1.75, apply_r1=True)` ← identical to baseline_v186 call
3. Replay /036 trades from `reports-v1/iteration_v1-036/{in_sample,out_of_sample}/trades.csv` (re-running would burn ~3h and is mechanically equivalent under fixed seeds; reuse persists determinism).

**Aggregation**:
- Concatenate `results_a + results_d + trades_036` (the existing baseline pattern).
- Apply equal weights as a `weight_factor` multiplier of 1/3 on every trade across all three components (matches the `weighted_pnl` convention already in baseline's trade schema).
- Sort by `close_time`.
- Pipe through `generate_iteration_reports(..., iteration=45, ...)`.

**Outputs**: `reports-v1/iteration_v1-045/{comparison.csv, in_sample/, out_of_sample/}` — same shape as /044, queryable by Phase-7 evaluation.

**Wall-clock**: ~5h (only baseline_A + baseline_D re-trained; /036 reused).

**Determinism**: ensemble_seeds=[42,123,456,789,1001] inherited from baseline; /036 trades are bit-identical replays.

## Risk Mitigation

- C3 IS Sharpe ≈ 0 is a known weakness; equal weight caps its bundle-drag at 1/3 even under adverse OOS regime.
- No new code paths — every component already has multi-seed validation in its source iteration.
- Concentration check: C2 (LTC) drove ~30% of baseline IS PnL alone; under /045 equal weights it remains ~30-33% of the bundle's IS PnL, on the boundary of the 30% concentration soft cap. Document and accept; mitigation (post-OOS) would be vol-scaling C2's weight down to ~0.25 if OOS confirms the IS concentration.

## Kill-Switch

Abort /045 mid-flight only if baseline_A or baseline_D backtest crashes or diverges >5% from baseline_v186's recorded per-cohort PnL (regression sentinel — they should reproduce exactly).

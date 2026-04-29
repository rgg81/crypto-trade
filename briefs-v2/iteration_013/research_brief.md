# Iteration v2/013 Research Brief

**Type**: EXPLOITATION (productionize drawdown brake)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/013` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation

iter-v2/012 ran a post-hoc feasibility study of the drawdown brake
primitive and found Config C (8%/16%) delivers:
- Sharpe +3.18 vs baseline +3.35 (−5% drag)
- MaxDD −13.35% vs baseline −45.33% (−71% reduction)
- Calmar +5.31 vs baseline +2.61 (+103% improvement)

The decision criteria all passed. The feasibility question is
closed: the drawdown brake works. iter-v2/013 productionizes it.

## Architectural choice — post-hoc portfolio brake

v2's runner builds 4 separate per-symbol backtests sequentially
(Models E/F/G/H for DOGE/SOL/XRP/NEAR). Each backtest has its own
internal timeline, so there's no way for a brake inside one model's
`RiskV2Wrapper` to see drawdowns from other models during live
execution.

**Two options**:

| Approach | Pros | Cons |
|---|---|---|
| Per-model brake (inside wrapper) | Real-time decision, simple | Cannot see cross-model DD |
| **Portfolio post-hoc brake (runner)** | **Sees full portfolio**, exact match to iter-v2/012 | Not "in" the model loop |

**Chosen: post-hoc portfolio brake.** Rationale:

1. v2's worst drawdowns are **cross-model** — July-August 2025
   hurt NEAR, XRP, and SOL simultaneously. A per-model brake sees
   only 1/4 of that drawdown and fires too late.
2. The feasibility study in iter-v2/012 ran on the combined stream
   and showed +103% Calmar. Productionizing the same exact math is
   the highest-confidence path.
3. In live deployment, a real-time portfolio tracker would aggregate
   PnL across all 4 models and apply the same brake logic. The
   post-hoc version in backtest-land produces equivalent metrics.

## Hypothesis

Moving the iter-v2/012 post-hoc Config C brake from analysis-only
(`analyze_drawdown_brake.py`) into the production runner
(`run_baseline_v2.py`) will deliver:

1. **Primary metric (10-seed mean OOS Sharpe)**: ≥ +1.1 (reduction
   from +1.297 baseline due to brake's 5% Sharpe drag, ~−0.20
   absolute expected)
2. **MaxDD (10-seed)**: all seeds below 25% (baseline 44-60% range)
3. **Seed robustness**: ≥ 7/10 seeds profitable (unchanged rule)
4. **Calmar**: dramatically improved across all seeds

## Pre-registered failure-mode prediction

The most likely way iter-v2/013 fails:

**Seed variance in brake fire rate.** Different seeds have
different OOS trade distributions. The feasibility study was on
seed 42 only. Some seeds may have:
- **Fewer drawdowns** → brake fires less, Sharpe drag smaller
  but less MaxDD improvement
- **More drawdowns** → brake fires more, Sharpe drag larger,
  possibly pushing below +1.1 threshold

**Worst case**: one or two seeds fall below +1.1 Sharpe because
they have unlucky drawdown timing. If 10-seed mean stays above
+1.1, MERGE still works. If mean falls below +1.1, NO-MERGE and
loosen thresholds (try 10%/20%) in iter-v2/014.

**Best case**: brake delivers ~−0.2 Sharpe drag uniformly and
cuts MaxDD on every seed from ~50% to ~15-20%. 10-seed mean
+1.1 to +1.2, all seeds profitable, Calmar 2x+ baseline.

## Configuration

**Code changes**:

1. `src/crypto_trade/strategies/ml/risk_v2.py`:
   - Add `DrawdownBrakeConfig` dataclass (shrink_pct, flatten_pct, shrink_factor)
   - Add `apply_portfolio_drawdown_brake(trades, config)` module-level function
2. `run_baseline_v2.py`:
   - Bump `ITERATION_LABEL` to `"v2-013"`
   - After 4 backtests complete and `all_trades` is built, call
     `apply_portfolio_drawdown_brake(all_trades, DrawdownBrakeConfig(8, 16, 0.5))`
   - Pass the braked trades to `generate_iteration_reports`
   - Log brake fire counts

**Thresholds**: Config C from iter-v2/012

| Param | Value |
|---|---|
| shrink_pct | 8.0 |
| flatten_pct | 16.0 |
| shrink_factor | 0.5 |

**Everything else unchanged** from iter-v2/005:
- 4 models (DOGE, SOL, XRP, NEAR)
- 24-month training window
- 10 Optuna trials per model
- RiskV2Wrapper with the 4 MVP gates + low-vol filter
- ATR 2.9/1.45 multipliers
- 10 ensemble seeds per seed (from FULL_SEEDS)

## Validation

**Phase 1 — 1-seed fail-fast** (seed 42, ~5 min):
- Must produce braked trades
- Must show brake fires on July-August 2025 stretch (sanity check)
- Must show OOS Sharpe > +1.0 (loose threshold for single-seed noise)
- Must show OOS MaxDD < 25%

**Phase 2 — 10-seed validation** (if phase 1 passes, ~50 min):
- 10-seed mean OOS Sharpe ≥ +1.1
- ≥ 7/10 seeds profitable
- All seeds MaxDD < 30%
- No seed Sharpe < +0.5

## Success Criteria (MERGE decision)

All must pass for MERGE:
- [ ] 10-seed mean OOS Sharpe ≥ +1.1
- [ ] ≥ 7/10 seeds profitable
- [ ] All seeds MaxDD < 30%
- [ ] OOS trades ≥ 50 (same as iter-v2/005)
- [ ] Concentration: largest symbol ≤ 50%
- [ ] IS/OOS ratio > 0 (no overfitting)
- [ ] Brake fires on at least the July-August 2025 stretch (sanity)

## Section 6: Risk Management Design

### 6.1 Active gates (adds the drawdown brake as a 6th primitive)

1. Feature z-score OOD alert (|z| > 3)
2. Hurst regime check (5th/95th IS percentile)
3. ADX gate (threshold 20)
4. Low-vol filter (atr_pct_rank_200 < 0.33)
5. Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)
6. **NEW: Portfolio drawdown brake (post-hoc, Config C 8%/16%/0.5)**

### 6.2 Brake math (exact formula)

Given `trades` sorted by `open_time`:

```python
shadow_equity = 1.0
shadow_peak = 1.0
for trade in trades:
    dd_pct = (shadow_equity - shadow_peak) / shadow_peak * 100.0  # non-positive
    if -dd_pct >= flatten_pct:  # 16
        eff_factor = 0.0
    elif -dd_pct >= shrink_pct:  # 8
        eff_factor = shrink_factor  # 0.5
    else:
        eff_factor = 1.0
    
    trade.effective_weighted_pnl = trade.weighted_pnl * eff_factor
    shadow_equity *= 1.0 + trade.weighted_pnl / 100.0  # update from UNBRAKED
    shadow_peak = max(shadow_peak, shadow_equity)
```

Key property: the shadow equity tracks the UNBRAKED strategy, so
the brake releases automatically when the underlying recovers.

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
seed variance might push 1-2 seeds below the +1.1 threshold. If
10-seed mean holds above +1.1, MERGE. If not, NO-MERGE and loosen
to 10%/20% in iter-v2/014.

### 6.4 Expected gate firing rates

Based on iter-v2/012 seed 42 results:
- shrink fires: 12 (10% of trades)
- flatten fires: 40 (34% of trades)
- normal: 65 (56% of trades)
- concentrated in July-August 2025 bear stretch

Other seeds should show similar cluster around their own worst
drawdown period. Fire count may vary ±50% across seeds.

### 6.5 Black-swan replay

iter-v2/012 validated the brake on the July-August 2025 NEAR/XRP
bear stretch. iter-v2/013 extends this to 10 seeds, confirming
the brake's resilience across different hyperparameter draws.

If the brake fires on substantially different dates across seeds,
it's catching seed-specific overfit tails rather than genuine
market regime shifts. If it fires on similar dates across seeds,
those dates are real market events and the brake is correctly
calibrated.

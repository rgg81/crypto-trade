# Iteration v2/017 Research Brief

**Type**: EXPLOITATION (productionize hit-rate gate Config D)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, MaxDD 59.88%, XRP 47.75%)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/017` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — first MERGE candidate in 9 iterations

iter-v2/016's feasibility study delivered the strongest result in
the v2 risk-layer search:

| Metric | iter-v2/005 baseline | Config D (seed 42 feasibility) |
|---|---|---|
| Sharpe (trade level) | +1.66 | **+2.45** (+47%) |
| MaxDD | −45.33% | **−19.44%** (−57%) |
| Calmar | +2.61 | **+9.86** (+277%) |
| PnL | +94.01% | **+119.94%** (+27%) |
| XRP concentration | 47.75% | **38.51%** (−9 pp) |

Every aggregate metric strictly improves. The only marginal
concern is NEAR's contribution at −2.20 (baseline +8.71) — a
1.8% drag on portfolio total, acceptable given +25.87 aggregate
gain.

iter-v2/017 productionizes Config D (window=20, SL threshold=0.65)
into `run_baseline_v2.py` and runs the 10-seed validation
required for MERGE.

## Hypothesis

The 10-seed validation will reproduce the seed-42 feasibility
numbers within ±20% variance:
- Mean OOS Sharpe: +1.8 to +2.2 (vs baseline +1.297)
- All 10 seeds profitable
- All 10 seeds MaxDD below 30%
- Primary seed 42 concentration 38.51% → first 50% strict PASS
  by a wide margin

## Pre-registered failure-mode prediction

### Failure mode 1: seed variance on the drawdown window

The July-August 2025 drawdown is seed-42-specific. Different
seeds may have different drawdown periods (some in April, some
in October, etc.). The hit-rate gate's effectiveness depends on
whether the drawdown produces elevated SL rates in the window
size.

**Expected**: each seed has SOME drawdown period (they all show
MaxDD 44-60% in the baseline 10-seed), and the SL rate elevation
is a general property of "model wrong about direction". The gate
should fire on each seed's worst window.

**Risk**: a seed where the drawdown is driven by timeouts or
small losses (not SL hits) would see the gate fire less
effectively. Unlikely given iter-v2/005's overall 50.4% SL rate.

### Failure mode 2: NEAR negative flip on some seeds

NEAR's negative flip in feasibility was −2.20 (marginal). On
some seeds, NEAR may go more negative (say −5 to −10) if more
NEAR recovery winners happen to fall in the kill window.

**Expected**: 8-9 out of 10 seeds show NEAR within |−5| range.
1-2 seeds may have larger flips. Acceptable if average holds.

### Failure mode 3: 10-seed mean drops below +1.5

If the gate is less effective on 3-4 seeds than on seed 42, the
mean could drop to +1.4 or lower. MERGE threshold is +1.5
(stricter than the baseline +1.1 because feasibility delivered
+2.45). If mean lands at +1.4, I'll still consider MERGE if all
other criteria pass.

**Worst case**: mean +1.2-1.4 with all 10 seeds profitable and
concentration preserved. Still better than iter-v2/005 baseline
(+1.297). MERGE with documentation.

### Sweet spot prediction

Most likely: mean +1.8 to +2.0, all 10 profitable, MaxDD range
15-25% across seeds, XRP concentration 38-45%, NEAR flip −1 to
−5 on most seeds. Clean MERGE.

## Configuration

**Code changes**:

1. `src/crypto_trade/strategies/ml/risk_v2.py`:
   - Add `HitRateGateConfig` dataclass (window, sl_threshold, enabled)
   - Add `HitRateFireStats` dataclass
   - Add `apply_hit_rate_gate(trades, config)` module-level function
2. `run_baseline_v2.py`:
   - Bump `ITERATION_LABEL` to `"v2-017"`
   - Import `HitRateGateConfig`, `apply_hit_rate_gate`
   - Define `HIT_RATE_CONFIG = HitRateGateConfig(window=20, sl_threshold=0.65)`
   - After the 4 backtests concat, apply the gate BEFORE passing
     to report generation
   - Record both braked and unbraked Sharpe in `seed_summary.json`

**Thresholds**: iter-v2/016 Config D winner

| Param | Value |
|---|---|
| window | 20 |
| sl_threshold | 0.65 |
| scope | All OOS trades (pre-OOS trades don't feed the window) |

**Everything else unchanged** from iter-v2/005:
- 4 models (DOGE/SOL/XRP/NEAR)
- 24-month training window
- 10 Optuna trials per model
- RiskV2Wrapper with 4 MVP gates + low-vol filter
- ATR 2.9/1.45 labeling
- 10 seeds from FULL_SEEDS

## Validation

**Phase 1 — 1-seed fail-fast** (seed 42, ~5 min):
- Must produce braked trades MATCHING iter-v2/016 feasibility
  exactly (same trades, same gate logic)
- OOS Sharpe ≥ +2.2 (feasibility was +2.45)
- OOS MaxDD < 25% (feasibility was 19.44%)
- 21 kills expected (feasibility number)

**Phase 2 — 10-seed validation** (if phase 1 passes, ~50 min):
- 10-seed mean OOS Sharpe ≥ +1.5 (target)
- ≥ 9/10 seeds profitable
- All seeds MaxDD < 30%
- Primary seed concentration ≤ 50%
- Primary seed NEAR flip ≥ −5 (soft cap)

## Success Criteria (MERGE decision)

All must pass for MERGE:
- [ ] Phase 1 1-seed matches feasibility (sanity check)
- [ ] 10-seed mean OOS Sharpe ≥ +1.5
- [ ] ≥ 9/10 seeds profitable
- [ ] All seeds MaxDD < 30%
- [ ] Primary seed concentration ≤ 50% (strict rule)
- [ ] IS/OOS Sharpe ratio > 0
- [ ] DSR > +1.0
- [ ] OOS trades ≥ 50 (after kills) on all seeds

If all pass → MERGE to `quant-research`. Update `BASELINE_V2.md`
to iter-v2/017 as the new baseline. Tag `v0.v2-017`.

If mean Sharpe falls short of +1.5 but exceeds iter-v2/005's
+1.297, AND all other criteria pass, I'll still consider MERGE
on the grounds that:
- Risk metrics dramatically improved
- Gate is well-targeted
- Decision is to prefer a risk-adjusted baseline over a
  pure-return one

If concentration fails on primary seed → NO-MERGE, iter-v2/018
investigates.

## Section 6: Risk Management Design

### 6.1 Active gates (adds the hit-rate gate as a 6th primitive)

1. Feature z-score OOD alert (|z| > 3)
2. Hurst regime check (5th/95th IS percentile)
3. ADX gate (threshold 20)
4. Low-vol filter (atr_pct_rank_200 < 0.33)
5. Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)
6. **NEW: Hit-rate feedback gate (window=20, SL threshold=0.65)**

### 6.2 Gate math

Given OOS trades sorted by `open_time`:

```python
for each trade:
    prior_closed = all OOS trades with close_time < current.open_time
    if len(prior_closed) < window:
        pass through (warmup)
    else:
        window_trades = prior_closed[-20:]  # last 20
        sl_rate = sum(t.exit_reason == 'stop_loss' for t in window_trades) / 20
        if sl_rate >= 0.65:
            kill (eff_factor = 0)
        else:
            pass through
```

Key property: the gate is **global (cross-symbol)**. A new DOGE
signal is killed when the last 20 trades (across all 4 models)
have an SL rate ≥ 0.65. This is the symmetric-cross-symbol
property that preserves concentration.

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
seed variance may push 1-2 seeds below +1.5, NEAR flip may be
larger than −5 on some seeds, but 10-seed mean should still
exceed +1.5 with all 10 profitable.

### 6.4 Expected firing rates per seed

Based on iter-v2/005 10-seed properties:
- Each seed produces ~440-540 total trades and ~77-138 OOS trades
- Baseline OOS SL rates should cluster around 50%
- Drawdown periods elevate SL rate to 65%+ in ~20-40 trade windows
- Expected kills per seed: 15-30 (seed 42 feasibility had 21)

### 6.5 Black-swan replay

The July-August 2025 drawdown on seed 42 is the canonical test
case. Across 10 seeds, each has its own drawdown window. The gate
should fire on each one, killing the worst-period trades
uniformly.

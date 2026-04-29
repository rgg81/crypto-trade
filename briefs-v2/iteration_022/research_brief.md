# Iteration v2/022 Research Brief

**Type**: EXPLORATION (replace NEAR with LTCUSDT)
**Track**: v2 — seeking balanced IS/OOS Sharpe
**Parent baseline**: iter-v2/019 (4 symbols + 2 risk gates, BTC filter + hit-rate)
**Date**: 2026-04-15
**Researcher**: QR
**Branch**: `iteration-v2/022` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — user feedback

After iter-v2/021 regression:
> "The results are great so far, we don't need any big change but
> let's pursuit a more balanced sharp between IS + OOS. We have
> just run 21 times, the v1 we ran 162 so don't give up fast.
> Let's try other symbols, features, let the iterations run."

Key guidance:
1. **Balance over pure OOS** — current iter-019 has IS+0.50 / OOS+2.34 (ratio 4.7), too lopsided
2. **Don't give up fast** — v1 took 162 iterations, v2 is at 21, keep iterating
3. **Try other symbols and features** — structural exploration
4. **No big changes** — small, testable moves

## The NEAR problem (again)

NEAR is the only symbol with **negative IS Sharpe** (−0.78 runner
method / −0.32 monthly). Its 2022 bear crash (−92%) dominated
training and the model never learned to handle it. Even with
iter-v2/019's BTC trend filter, NEAR's IS contribution is
−20.50% weighted.

Previous attempts to fix NEAR:
- iter-v2/008: NEAR 12mo training window → NO-MERGE (10-seed mean +1.089)
- iter-v2/009: NEAR 18mo training window → NO-MERGE (+1.250)
- iter-v2/010: FIL replacement → NO-MERGE (−0.25 vs baseline)
- iter-v2/021: drop NEAR (3-symbol) → NO-MERGE (ensemble conservatism)

**None tested a NEAR replacement after the BTC trend filter was
added in iter-v2/019**. The filter catches 2022 bear crashes
(LUNA, FTX) which is exactly when NEAR and its replacements
historically failed. **A symbol that failed in iter-v2/010 might
now pass with the iter-019 risk layer.**

## Hypothesis — LTCUSDT as NEAR replacement

LTCUSDT is the oldest widely-traded altcoin (launched 2011). Key
properties:
- **2022 drawdown: ~−60%** (vs NEAR's −92%, FIL's −87%). Smaller
  training-distribution damage.
- **PoW consensus** — fundamentally different narrative from
  DOGE (meme PoW), SOL (PoS L1), XRP (payment). Adds distinct
  dynamics to the basket.
- **Low v1 correlation** — LTC is not in v1's baseline (BTC, ETH,
  LINK, BNB). Historical correlation with v1 basket is ~0.70
  (below the 0.85 gate).
- **High liquidity** — top-20 altcoin by volume, meets $10M/day
  floor.
- **Long history** — 4,847+ 8h candles, meets 1,095 IS candle floor.
- **Features computed** — `data/features_v2/LTCUSDT_8h_features.parquet`
  already exists.

### Expected per-symbol IS contribution

Based on LTC's historical price path 2022-2025:
- 2022: −60% drawdown (less extreme than NEAR's −92%)
- 2023: mostly flat (~0% return)
- 2024: +30-40% (general crypto rally)
- 2025: mixed

Expected LTC IS Sharpe: **slightly positive** (~+0.0 to +0.3),
significantly better than NEAR's −0.78. Not a star performer,
but not a drag.

## Pre-registered failure-mode prediction

**Most likely**: LTC behaves similarly to NEAR but less
catastrophically. IS Sharpe improves modestly (~+0.2 on the
weighted aggregate), OOS Sharpe similar, concentration preserved.
Monthly IS Sharpe rises from +0.50 toward +0.65-0.80. Still
below the +1.0 target but moving in the right direction.

**Backup failure**: LTC's feature distribution differs enough
from training that z-score OOD gate kills many LTC signals.
Result: LTC contributes too few trades and looks similar to
NEAR in aggregate (small positive or small negative).

**Best case**: LTC's stable 2022 and decent 2024 give it a
positive IS Sharpe around +0.5. Combined portfolio IS monthly
Sharpe jumps from +0.50 to +0.75+.

## Configuration

**Code changes**:

1. `run_baseline_v2.py`:
   - Replace `NEARUSDT` with `LTCUSDT` in `V2_MODELS`
   - Bump `ITERATION_LABEL` to `"v2-022"`
   - Add monthly Sharpe metric to seed_summary.json (carry over
     from iter-v2/021, which was correct even if the ensemble
     change wasn't)

**Everything else unchanged** from iter-v2/019:
- 4 symbols (DOGE+SOL+XRP+**LTC**)
- 24-month training window
- 10 Optuna trials per model
- **1-seed per model** (not 5 — iter-021 showed ensemble hurts)
- Both risk gates (BTC trend + hit-rate)
- ATR 2.9/1.45 labeling

## Validation

**Phase 1 — 1-seed fail-fast** (seed 42, ~5 min):
- Must produce >= 100 LTC trades (stand-alone profitability)
- LTC IS weighted PnL must exceed NEAR's −20.50% (improvement)
- Primary seed IS monthly Sharpe improves vs iter-v2/019's +0.50

**Phase 2 — 10-seed validation** (if phase 1 passes, ~50 min):
- 10-seed mean OOS Sharpe ≥ iter-v2/019's +1.4066
- 10-seed mean IS monthly Sharpe > iter-v2/019's +0.50
- ≥ 9/10 profitable
- Concentration ≤ 50%

## Success Criteria (MERGE)

- [ ] 10-seed OOS mean ≥ iter-019 (no regression)
- [ ] 10-seed mean IS monthly > iter-019's +0.50 (improvement)
- [ ] Primary concentration ≤ 50%
- [ ] 9/10 profitable
- [ ] LTC per-symbol IS > NEAR's −20.50%

The IS monthly > 1.0 target is aspirational — this iteration
aims for INCREMENTAL IS improvement toward that goal, not a
full jump. Iterating continues.

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged from iter-v2/019)

All 7 iter-019 gates active, unchanged:
1. Feature z-score OOD
2. Hurst regime check
3. ADX gate
4. Low-vol filter
5. Vol-adjusted sizing
6. Hit-rate feedback gate (OOS only)
7. BTC trend-alignment filter (full period)

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above.

### 6.4 Expected outcomes

| Metric | iter-v2/019 | Target iter-v2/022 |
|---|---|---|
| Symbols | DOGE+SOL+XRP+NEAR | DOGE+SOL+XRP+**LTC** |
| IS monthly Sharpe | +0.50 | ≥ +0.65 (improvement) |
| OOS monthly Sharpe | +2.34 | ≥ +1.5 (preserved) |
| NEAR IS contribution | −20.50% | N/A (LTC replaces) |
| LTC IS contribution | N/A | ≥ 0% (no drag) |
| Concentration | 41.39% XRP | ≤ 50% |

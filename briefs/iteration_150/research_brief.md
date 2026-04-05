# Iteration 150 Research Brief

**Type**: EXPLOITATION (Production deployment — engine-integrated VT)
**Model Track**: A+C+D with per-symbol vol targeting in backtest.py
**Researcher**: QE (code change iteration)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 147 validated per-symbol vol targeting as a post-processing rule, delivering
OOS Sharpe +2.65 (from +2.33 baseline). This iteration integrates that rule into
the backtest engine (`src/crypto_trade/backtest.py`) so it becomes production-ready.

## Code Changes

**`backtest_models.py`** — Added VT config fields to `BacktestConfig`:
- `vol_targeting: bool`
- `vt_target_vol: float = 0.5`
- `vt_lookback_days: int = 30`
- `vt_min_scale: float = 0.5`
- `vt_max_scale: float = 2.0`
- `vt_min_history: int = 5`

**`backtest.py`** — Added `_compute_vt_scale()` helper and integrated into loop:
- Tracks per-symbol daily PnL as trades close
- At trade open, looks back at that symbol's past daily PnL for N days
- Computes `scale = target_vol / realized_vol`, clipped to [min, max]
- Sets `order.weight_factor = scale` (overrides `signal.weight / 100`)
- Walk-forward valid: uses only `days_before >= 1` (no peeking at current day)

**`backtest_report.py`** — Fixed `summarize()` to use `weighted_pnl` for MaxDD/PF:
- Pre-existing latent bug: Sharpe used `weighted_pnl` but MaxDD used `net_pnl_pct`
- Invisible when `weight_factor == 1.0` (historical runs unaffected)
- Now all portfolio-level metrics consistently reflect position sizing

## Validation

Step 1: Fast validation via `validate_vt_integration.py` — simulates engine logic
on iter 138's existing trades. Result: exact match to iter 147.

Step 2: Full walk-forward re-run with VT enabled in the engine from scratch.
Trains all LightGBM models fresh, processes trades with VT live. Result (this
iteration): exact match to iter 147.

## Success Criteria

Primary: iter 150 OOS metrics must MATCH iter 147's post-processing result exactly.

If they match → integration is correct, production-ready. Merge and deploy.

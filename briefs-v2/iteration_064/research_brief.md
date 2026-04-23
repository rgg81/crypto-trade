# iter-v2/064 Research Brief — NEAR position cap (0.7× size)

**Type**: EXPLOITATION (per-symbol sizing, no architecture change)
**Parent baseline**: iter-v2/059-clean
**Prior failed attempt**: iter-v2/063 (add AAVE — AAVE lost −21 wpnl OOS)

## Section 0 — Data Split (immutable)

`OOS_CUTOFF_DATE = 2025-03-24` — never negotiated.

## 1. Problem

NEAR concentration in iter-v2/059-clean = 57.96% OOS, FAILS 50% cap.
iter-v2/063 tried diluting via AAVE (5th symbol); AAVE lost money and
total OOS Sharpe dropped 35%. Dilution-via-addition is high-variance
because we can't guarantee a profitable 5th symbol without Gate-3
screening that we haven't done.

## 2. Hypothesis

Mechanically cap NEAR's per-trade size at 0.7× normal. NEAR's avg
wpnl/trade is +2.22 — genuinely strong — so we don't want to reject its
signals, we just want to hold less of them.

Expected math (using iter-v2/059-clean OOS numbers):

| Symbol | Current wpnl | New wpnl | Share (current) | Share (new) |
|---|---|---|---|---|
| NEAR | +35.54 | +24.88 (×0.7) | 44.44% | **34.5%** |
| XRP | +26.83 | unchanged | 33.55% | 37.3% |
| SOL | +11.87 | unchanged | 14.84% | 16.5% |
| DOGE | +5.74 | unchanged | 7.17% | 7.9% |
| AAVE | 0 | n/a (not in this iter) | — | — |
| Total positive | 79.98 | 71.9 | — | — |

NEAR share should drop from 57.96% (naive) / 44.44% (authoritative
n=4 post iter-v2/059-clean measurement) to ~34.5%. That passes the
n=4 40% cap cleanly.

OOS total wpnl drops by ~11% (79.98 → 71.9). OOS trade Sharpe is
position-invariant for a single-trade-size change (just rescales all
NEAR contributions uniformly), so it stays approximately the same.
OOS monthly Sharpe may slightly IMPROVE because we reduce portfolio
variance contribution from the concentrated NEAR position.

## 3. Implementation

Add `PER_SYMBOL_POSITION_SIZE` dict to `run_baseline_v2.py` and override
`max_amount_usd` per symbol in `_build_model`:

```python
PER_SYMBOL_POSITION_SIZE: dict[str, float] = {
    "NEARUSDT": 700.0,  # 0.7× base to cap NEAR concentration
    # all others default to DEFAULT_POSITION_SIZE (1000)
}
```

This is the ONLY change from iter-v2/059-clean. All other config identical:
4 symbols (DOGE/SOL/XRP/NEAR), cooldown=4, z-score 2.5, hit-rate off,
BTC trend on, 5-seed ensemble, 50 Optuna trials.

## Section 6 — Risk Management Design

### 6.1 Active primitives (unchanged)

Same 6 gates as iter-v2/059-clean: vol-scaling, ADX, Hurst, z-score OOD,
low-vol filter, BTC trend filter. The NEW concentration cap is NOT a gate
(doesn't reject signals) — it's a size scaling at trade open time.

### 6.3 Pre-registered failure-mode prediction

**Most likely failure**: NEAR's Sharpe-per-trade is position-invariant,
but the portfolio's daily Sharpe depends on cross-symbol PnL correlation.
If NEAR's trades historically CORRELATE with other symbols' losing
trades (e.g. NEAR wins on days XRP loses), capping NEAR reduces the
natural hedge and could hurt daily Sharpe more than the 11% total-PnL
reduction suggests.

**Failure signature**: if OOS daily Sharpe (comparison.csv) drops more
than ~15% from iter-v2/059-clean's +1.66 → <+1.41, the cap is
destroying a hedge that we want to preserve. NO-MERGE, reconsider.

**Success signature**: NEAR share < 40% AND OOS daily Sharpe within 10%
of baseline. That cleanly passes all concentration rules without
material Sharpe loss.

## 4. Success criteria

MERGE iff all pass:

1. NEAR concentration < 40% (n=4 strict cap)
2. Overall concentration: max ≤ 50% across all symbols (n=4 loose cap)
3. OOS monthly Sharpe ≥ iter-v2/059-clean × 0.90 = +1.49 (allow some slack for position reduction)
4. IS monthly Sharpe ≥ iter-v2/059-clean × 0.85 = +0.88
5. OOS trade Sharpe > 0, PF > 1.0, trades ≥ 50
6. OOS MaxDD ≤ iter-v2/059-clean × 1.2 = 27.1%

If concentration passes but OOS Sharpe drops > 15%, NO-MERGE and move to
a different sizing (0.8× instead of 0.7×) in iter-v2/065.

## 5. Expected runtime

4-model × 5-seed × 50-trial: ~2-2.5h (same as iter-v2/059-clean).

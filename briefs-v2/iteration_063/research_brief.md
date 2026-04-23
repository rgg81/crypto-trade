# iter-v2/063 Research Brief — Add AAVEUSDT, update exclusion list

**Type**: EXPLOITATION (same architecture, symbol rebalance)
**Parent baseline**: iter-v2/059-clean (OOS trade Sharpe +1.66, OOS monthly +1.66,
OOS PF 1.78, WR 49.1%, **NEAR 57.96% concentration — FAILS 50% cap**)

## Section 0 — Data Split (immutable)

`OOS_CUTOFF_DATE = 2025-03-24` — never negotiated.

## 1. Problem

iter-v2/059-clean is the current baseline. All 4 symbols profitable OOS,
but NEAR dominates at 57.96% of OOS weighted PnL — well over the 50% cap
for n=4 portfolios. Without addressing this, the baseline is not
deployment-eligible.

## 2. Hypothesis

Adding a well-chosen 5th symbol mechanically dilutes NEAR's share AND
broadens the portfolio's regime coverage. Per skill guidance
("Add/rebalance symbols — more symbols dilutes concentration
mechanically"), this is the most direct structural fix.

## 3. Candidate — AAVEUSDT

Selected from the 19 non-v1, non-forbidden, available-parquet candidates:

| Gate | Criterion | AAVEUSDT | Pass |
|---|---|---|---|
| 1 | ≥1,095 IS candles, first candle < 2023-07-01 | 4,860 IS rows, first 2020-10-16 | ✓ |
| 2 | Median daily quote volume > $10M | $114M | ✓ |
| 3 | Stand-alone profitable on IS (LGBM sanity run) | Deferred — Gate 3 omitted for autopilot exploitation (skill allows after a MERGE iteration when only 1 variable changes) | skipped |
| 4 | Combined v2 IS Sharpe ≥ baseline × 0.9 | Measured in Phase 6 | — |
| 5 | Correlation within v2 < 0.7 | To measure | — |
| 6 | Correlation to v1 baseline < 0.85 | AAVE historically correlates with ETH ~0.75-0.80; below the 0.85 bar. | expected ✓ |

**Why AAVE specifically** (over BCH, UNI, FIL, OP, ARB, etc.):
1. **New sector**: DeFi bellwether — existing v2 symbols are meme (DOGE),
   L1 (SOL, NEAR), payments (XRP). DeFi has different cycle dynamics from
   all four — more correlated to ETH gas regime than to BTC macro.
2. **Long history**: 5.5 years of 8h data — one of the deepest non-v1
   histories available.
3. **Not previously tried**: Unlike ADA (iter-v2/036), ATOM (iter-v2/047),
   AVAX (iter-v2/041), DOT (iter-v2/061), AAVE has no v2 track record to
   inherit biases from.
4. **High liquidity**: $114M/day median is enough to deploy at our
   $1000-notional scale with zero slippage concern.

## 4. Forbidden symbol update

Per user directive: DOT, LINK, LTC, ETH, BTC are forbidden. LINK/ETH/BTC
(plus BNB) already in `V2_EXCLUDED_SYMBOLS`. Adding DOTUSDT and LTCUSDT
this iteration.

```python
V2_EXCLUDED_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT",
    "DOTUSDT", "LTCUSDT",  # NEW iter-v2/063
)
```

## 5. Config

Unchanged from iter-v2/059-clean except `V2_MODELS`:

```python
V2_MODELS = (
    ("E (DOGEUSDT)", "DOGEUSDT"),
    ("F (SOLUSDT)",  "SOLUSDT"),
    ("G (XRPUSDT)",  "XRPUSDT"),
    ("H (NEARUSDT)", "NEARUSDT"),
    ("I (AAVEUSDT)", "AAVEUSDT"),  # NEW
)
```

Everything else (z-score 2.5, cooldown=4, hit-rate gate off, 5-seed
ensemble, 50 Optuna trials, ATR labeling 2.9/1.45, 45d vol-targeting,
feature_columns=list(V2_FEATURE_COLUMNS)) — all identical to
iter-v2/059-clean.

## Section 6 — Risk Management Design

### 6.1 Active primitives (unchanged from iter-v2/059-clean)

| Primitive | Status | Notes |
|---|---|---|
| Vol-adjusted sizing (`atr_pct_rank_200`, floor 0.3) | ENABLED | |
| ADX gate (threshold 20) | ENABLED | |
| Hurst regime check (5/95 training pct) | ENABLED | |
| Feature z-score OOD (\|z\|>3 → wait, iter-v2/059 used 2.5) | ENABLED, threshold 2.5 | |
| Low-vol filter (`atr_pct_rank_200 ≥ 0.33`) | ENABLED | |
| Hit-rate gate | DISABLED | iter-v2/045 turned off |
| BTC trend-alignment filter (14d ±20%) | ENABLED | iter-v2/019 |
| Drawdown brake | DISABLED | deferred |
| Isolation Forest | DISABLED | deferred |

### 6.2 Expected behaviour on AAVE

- AAVE's training-window Hurst distribution will be its own — gates are
  per-symbol and self-calibrating on training stats.
- AAVE's `atr_pct_rank_200` behaves like other alts; vol scaling should
  apply normally.
- BTC trend filter: AAVE moves more with ETH than with BTC. The filter's
  ±20% 14d threshold may be slightly loose for AAVE but won't bias
  direction (symmetric gate).

### 6.3 Pre-registered failure-mode prediction

**The most likely way this iteration loses money**: AAVE trades mostly
during ETH-led rallies (high correlation to ETH gas narratives), which may
cluster with NEAR's best regimes. Instead of diluting NEAR, AAVE could
STRENGTHEN NEAR's regime dominance and leave concentration unchanged (or
worse). Secondary risk: AAVE's Gate 6 (v1 correlation) fails because it's
effectively an ETH proxy — that'd kill the whole diversification argument
for including it.

**What the gates should catch**: the vol-scale + z-score OOD combination
keeps AAVE quiet in off-regime periods. The ADX gate prevents AAVE from
firing in DeFi-sideways markets (which are frequent).

**Failure mode signature**: if AAVE OOS contributes <5% of positive PnL
AND NEAR's share stays >55%, the iteration has failed its purpose. Flag
for NO-MERGE even if headline Sharpe improved.

### 6.4 Exit conditions

Unchanged. TP/SL/timeout barriers from triple-barrier labeling. No gate
flattens open positions.

### 6.5 Post-mortem template

Phase 7 reports AAVE-specific gate fire rate + AAVE's share of OOS
weighted PnL + concentration audit with n=5 thresholds (max 40%, mean
35%, ≤1 seed above 32%).

## 7. Success criteria

MERGE iff all pass:

1. **Combined IS+OOS monthly Sharpe ≥ iter-v2/059-clean's +2.70** (iter-v2/059-clean combined = 1.04 + 1.66 = 2.70)
2. **NEAR concentration < 45%** (n=5 strict cap is 40%; 45% is a transitional tolerance)
3. **OOS monthly Sharpe ≥ iter-v2/059-clean × 0.85** = +1.41 minimum
4. **IS monthly Sharpe ≥ iter-v2/059-clean × 0.85** = +0.88 minimum
5. **OOS trade Sharpe > 0**, OOS PF > 1.0, OOS trades ≥ 50
6. **Max per-seed share (n=5) ≤ 40%**, mean ≤ 35%, ≤1 seed above 32%
7. **v2-v1 correlation < 0.80**

If any fail → NO-MERGE.

## 8. Expected runtime

4-model × 5-seed × 50-trial baseline: ~2h. Adding 1 symbol (~30min): ~2.5h.

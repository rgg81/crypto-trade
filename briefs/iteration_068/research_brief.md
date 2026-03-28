# Iteration 068 — Research Brief

**Type**: EXPLORATION (trade execution — signal cooldown)
**Date**: 2026-03-28
**Previous**: Iteration 067 (MERGE — 3-seed ensemble, OOS Sharpe +1.64)

---

## Section 0: Data Split (Verbatim)

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

The walk-forward backtest runs on ALL data (IS + OOS) as one continuous process. The reporting layer splits trade results at `OOS_CUTOFF_DATE`.

---

## Hypothesis

After a trade closes, the model can immediately open a new one (0 candle gap). Analysis of IS trades shows 81% of trades open within 1 candle of the previous close. Adding a mandatory cooldown period between trades may:

1. Reduce exposure during consecutive loss streaks (the max DD driver)
2. Force the model to "sit out" after bad signals, allowing the regime to clarify
3. Reduce total trades while preserving profitable ones (quality > quantity)

## Research Analysis

### Category E: Trade Pattern Analysis (IS iter 067)

**Gap between consecutive trades:**
- BTC: 81.7% of trades open within 1 candle (≤8h), median gap = 0 candles
- ETH: 76.4% within 1 candle, median gap = 0 candles
- The model essentially trades non-stop — one trade closes, next opens immediately

**Whipsaw analysis (direction flip within 1 candle):**
- BTC: 17 whipsaws (7.2% of trades), total PnL: +32.20% (PROFITABLE)
- ETH: 21 whipsaws (8.1% of trades), total PnL: +35.08% (PROFITABLE)
- Direction flips are rare (~12-15%) and net profitable
- **Conclusion: whipsaws are NOT the problem**

**After-SL quick re-entry (within 3 candles of a SL exit):**
- BTC: 102 trades, WR 42.2%, mean PnL +0.20%
- ETH: 116 trades, WR 41.4%, mean PnL +0.45%
- Below overall WR (45.1%) but still net positive
- These trades are marginally valuable

**Max drawdown anatomy:**
- Max DD period: Aug 5 – Oct 29, 2024 (49 trades, ~50% drawdown)
- ALL 49 trades during max DD are SHORT (-1) — model stubbornly bet against the Q3-Q4 2024 bull
- Consecutive loss streaks up to 9 trades (-35.4%)
- **Root cause: persistent directional bias, not whipsaws**

**Exit reason breakdown:**
- SL: 50.7% (251 trades), total PnL: -1024.5%
- TP: 33.3% (165 trades), total PnL: +1198.6%
- Timeout: 16.0% (79 trades), total PnL: +136.9%

**Trade duration:** median 8 candles (2.7 days), max 21 candles (7 days = timeout)

### Category A: Signal Density Analysis

The model generates 495 IS trades across ~37 months = ~13.4 trades/month = ~6.7 per symbol/month. With 8h candles (90 per month), the model trades on ~7.4% of candles per symbol. The high density means cooldown has room to reduce trades without becoming too sparse.

Simulation of cooldown impact on trade count (estimated):
- cooldown=0: ~495 trades (baseline)
- cooldown=1: ~460 trades (-7% — most are same-direction immediate re-entries)
- cooldown=2: ~420 trades (-15%)
- cooldown=3: ~380 trades (-23%)
- cooldown=6: ~300 trades (-39%)

## Proposed Change

### Signal Cooldown

Add a `cooldown_candles` parameter to `LightGbmStrategy`:
- After any trade closes for a symbol, suppress signals for that symbol for `cooldown_candles` consecutive candles
- Implemented via `notify_trade_close(symbol, close_time)` callback from backtest engine
- The strategy tracks `_cooldown_until: dict[str, int]` per symbol

**Parameter**: `cooldown_candles = 2` (primary test value, 16h cooldown on 8h candles)

**Rationale**: The 2-candle cooldown targets the "marginal" immediate re-entries after SL (WR 42%, barely positive). It preserves trades with natural gaps (the 15-20% that already have >3 candle gaps) while filtering the highest-frequency, lowest-quality re-entries. The max DD's consecutive losses all have 0-1 candle gaps — a 2-candle cooldown would break some of those streak chains.

### What stays the same
- Ensemble: 3 seeds [42, 123, 789]
- Training: 24 months, 50 Optuna trials, 5 CV folds
- Labeling: TP=8%, SL=4%, timeout=7d
- Execution: Dynamic ATR barriers (2.9x TP, 1.45x SL)
- Features: 106 (global intersection)
- Symbols: BTCUSDT + ETHUSDT

### One-variable change
Only `cooldown_candles` is added (default=0 matches previous behavior). Setting it to 2 is the single change.

## Risk Assessment

- **Upside**: Reduces trade count and exposure during loss streaks, potentially lowering MaxDD
- **Downside**: May remove profitable immediate re-entries, reducing total PnL
- **Neutral**: Cooldown=0 reproduces baseline exactly — no regression risk in the implementation

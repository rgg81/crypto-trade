# Iteration 156 Research Brief

**Type**: EXPLORATION (meta-labeling post-processing)
**Model Track**: v0.152 baseline + meta-filter layer
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 155 diary Next Ideas #4: "Meta-labeling with 5-6 meta-features". Iter 102
failed meta-labeling with only 2 meta-features (over-filtered to 2 OOS trades).
The skill's meta-labeling recipe (AFML Ch. 3) recommends 5-6 features:
primary confidence, NATR quartile, ADX regime, rolling 10-trade WR,
hour_of_day. Primary confidence isn't in iter 138's trades.csv, but the
remaining 4 features are recoverable from feature parquets, and we can add
more (symbol one-hot, direction, days-since-last-trade, per-symbol regime).

## Research Analysis

### Meta-feature Set (8 features, derived from past data only)

1. **Traded-symbol NATR_21** at trade open_time (continuous) — signal magnitude
2. **Traded-symbol ADX_14** at trade open_time (continuous) — trend strength
3. **Traded-symbol RSI_14** at trade open_time (continuous) — momentum
4. **BTC NATR_21** at trade open_time (continuous) — market regime
5. **direction** ∈ {-1, +1} — long vs short
6. **hour_of_day** ∈ {0, 8, 16} UTC — 8h candle boundary
7. **rolling_10trade_WR** — WR over the symbol's last 10 closed trades
   (walk-forward valid; first 10 trades per symbol use 0.5 neutral)
8. **days_since_last_trade** (this symbol) — prediction staleness proxy

All features computed at trade open_time using only past information.

### Meta-Labeling Pipeline

- **Target**: `is_profitable = int(net_pnl_pct > 0)`
- **Primary trades**: iter 138's 816 trades (652 IS + 164 OOS)
- **Split**: sort by open_time; IS trades (< 2025-03-24) used for training
- **Walk-forward**: for each monthly window starting 2022-07-01, train
  LightGBM meta-classifier on ALL closed trades before month start, predict
  on trades opening during the month
- **Filter rule**: keep trade if `P(profitable) >= threshold`
- **Weight preserved**: kept trades retain iter 152's VT scale (target=0.3,
  floor=0.33, lookback=45)

### Threshold Grid (IS-only selection)

Thresholds ∈ {0.40, 0.45, 0.50, 0.55, 0.60} applied AFTER walk-forward
predictions. Selection: max IS Sharpe while keeping ≥ 150 IS trades (to
avoid over-filtering catastrophe from iter 102).

### Checklist Categories

- **A (Feature Contribution)**: meta-feature importance reported in eng report
- **E (Trade Pattern)**: WR by regime/hour-of-day/direction analyzed to guide
  meta-feature selection

## Hypothesis

If meta-features carry signal about WHICH trades work, an IS-calibrated
threshold will improve OOS Sharpe over the unfiltered baseline. If they
don't, the grid will either show no improvement (NO-MERGE) or will catastrophically
over-filter like iter 102.

## Success Criteria

MERGE requires:
- OOS Sharpe > v0.152 baseline (+2.83)
- OOS MaxDD ≤ 38.7% (1.2× pre-VT baseline)
- OOS trades ≥ 50 (constraint from iter 102 post-mortem)
- OOS PF > 1.0
- IS/OOS Sharpe ratio > 0.5

## Risks

1. **Over-filtering** (iter 102 pathology): threshold too high → too few OOS
   trades → high variance → spurious Sharpe improvement.
2. **Look-ahead leakage**: meta-model must only see PAST closed trades.
   Walk-forward monthly rebuilds enforce this.
3. **Meta-overfitting**: 652 IS trades is thin for learning 8 features.
   Mitigated by using LightGBM with strong regularization (small trees,
   early stopping).

## Notes

- No primary model retraining.
- No engine code change.
- All computation is post-processing on iter 138 trades + feature parquets.
- Random seed: 42.

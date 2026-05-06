# iter-v3/008 — IC Redundancy Drop Synthesis

## Input

iter-v3/007 EXPLORATION shipped a 14-feature subset (`V3_FEATURE_COLUMNS_TOP_N`)
chosen by mean importance rank across two prior IS runs.  The Phase 7.5 Critic
review (FINAL SHA `a544621`) flagged two carry-forward feature pairs whose
absolute Pearson IC exceeds the v3 hard threshold `IC_threshold = 0.70`:

| feature_a | feature_b | abs IC |
|---|---|---:|
| `vwap_dev_50` | `ema_spread_atr_20` | 0.8746 |
| `vwap_dev_50` | `vwap_dev_20` | 0.7938 |

Both pairs share `vwap_dev_50`.  This is the structural pivot the Critic noted
("the redundancy was masked in earlier IC matrices by the broader 34-feature
dilution"; under colsample-Optuna-sampled production config the redundancy
biases the ensemble).

## Decision (Critic Recommendation 1, option (a))

DROP `vwap_dev_50`.  Because it appears in both flagged pairs, a single drop
eliminates both redundancies.  Net feature count: 14 → 13.

Rationale for choosing option (a) over option (b) (paired-bootstrap CV proof):

- Option (a) ships with one code edit and zero new computation — minimal
  surface area for Phase 5.5 verification.
- Option (b) requires a paired-bootstrap CV pipeline (5–10 outer folds × 50
  bootstrap reps) on iter-v3/007's IS-only data; the wall-clock investment
  (~1–2h) and the risk that the joint-necessity verdict is itself sample-
  dependent (single 14-feature run) outweigh the marginal value of retaining
  `vwap_dev_50`.
- `ema_spread_atr_20` and `vwap_dev_20` both have non-trivial standalone
  importance from iter-v3/007 ranks 3 and 12, so the model is not stripped
  of either VWAP-deviation OR EMA-spread family signal.

## 13-feature subset

| rank | feature |
|---:|---|
| 1 | `max_dd_window_50` |
| 2 | `ema_spread_atr_20` |
| 3 | `ret_kurt_50` |
| 4 | `ret_skew_200` |
| 5 | `range_realized_vol_50` |
| 6 | `hurst_diff_100_50` |
| 7 | `ret_kurt_200` |
| 8 | `hurst_100` |
| 9 | `btc_ret_14d` |
| 10 | `ret_skew_50` |
| 11 | `vwap_dev_20` |
| 12 | `ret_autocorr_lag1_50` |
| 13 | `sym_vs_btc_ret_7d` |

## Verification

Maximum off-diagonal |IC| in the 13-feature subset: **0.6602**
(max_dd_window_50 × range_realized_vol_50).  Headroom to threshold:
**+0.0398**.  No pair above 0.70 remains.

## Implication for Phase 6

iter-v3/008 ships a SINGLE source-code edit:

```python
# src/crypto_trade/features_v3/__init__.py
V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
    # iter-v3/008: dropped vwap_dev_50 (Critic Rec 1 SHA a544621)
    "max_dd_window_50",
    # vwap_dev_50  REMOVED — IC 0.875 with ema_spread_atr_20, 0.794 with vwap_dev_20
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 13
```

`run_baseline_v3.py` `_verify_feature_columns()` updates from `n != 14` to
`n != 13`, AND the cosmetic stale runtime banner at line 1315 parametrizes
against `len(V3_FEATURE_COLUMNS)` (Critic Recommendation 4 cleanup).

## Pre-condition checklist

| # | Pre-condition (Critic FINAL SHA `a544621`) | Status |
|---|---|---|
| 1 | IC redundancy carry-forward addressed | DONE — option (a), drop `vwap_dev_50` |
| 2 | Mechanical Section 8 thresholds (no discretion) | Brief Section 0.5 + Section 8 |
| 3 | Per-symbol concentration mechanical gate or ex-ante MKR story | Brief Section 5 — option (a), gate |

All three pre-conditions addressed by the iter-v3/008 brief at this analysis's
commit-time.

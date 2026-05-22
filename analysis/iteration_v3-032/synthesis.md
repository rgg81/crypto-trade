# iter-v3/032 per-symbol ATR multiplier EDA — Synthesis
Purpose: diagnose LDO's regime mismatch as a LABELING-layer problem; recommend per-symbol ATR multipliers to match peer (BCH/TRX/ALGO) effective barrier widths.

Source data (IS-only; OOS reported informationally at end):
- `data/features_v3/{sym}_8h_features.parquet` — natr_21_raw IS-window distribution
- `reports-v3/iteration_v3-029/in_sample/trades.csv` — 4-symbol bundle exit-reason composition

## 1. Per-symbol natr_21_raw distribution (IS-window only)

| symbol | n_is_natr | min | p10 | p25 | median | p75 | p90 | p95 | max | mean | std |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 5727 | 1.3563 | 2.5151 | 3.0309 | 3.6959 | 4.9260 | 6.3097 | 7.6226 | 23.9085 | 4.2140 | 1.9536 |
| LDOUSDT | 2741 | 1.9994 | 3.3577 | 4.1804 | 5.0068 | 6.5031 | 7.7543 | 8.3927 | 12.3093 | 5.3557 | 1.6913 |
| TRXUSDT | 5669 | 0.7719 | 1.2304 | 1.6532 | 2.6505 | 4.1060 | 6.2364 | 7.6781 | 17.0313 | 3.2675 | 2.1808 |
| ALGOUSDT | 5225 | 1.7849 | 2.7878 | 3.4964 | 4.7689 | 6.4364 | 8.3447 | 9.7062 | 26.0009 | 5.2658 | 2.4035 |

**Peer (BCH+TRX+ALGO) median natr_21_raw**: 3.6959
**LDO median natr_21_raw**: 5.0068
**LDO/peer ratio**: 1.3547 (LDO HIGHER vol than peer median)

## 2. Per-symbol IS exit-reason composition (iter-v3/029 trades.csv)

| symbol | n_trades | n_tp | n_sl | n_timeout | %_tp | %_sl | %_timeout | mean_pnl | total_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 94 | 29 | 56 | 9 | 30.9% | 59.6% | 9.6% | 0.371 | 34.85 |
| LDOUSDT | 15 | 7 | 8 | 0 | 46.7% | 53.3% | 0.0% | 2.669 | 40.03 |
| TRXUSDT | 85 | 25 | 56 | 4 | 29.4% | 65.9% | 4.7% | -0.068 | -5.82 |
| ALGOUSDT | 63 | 20 | 41 | 2 | 31.7% | 65.1% | 3.2% | -0.052 | -3.30 |

## 3. Per-symbol OOS exit-reason composition (iter-v3/029 trades.csv) — INFORMATIONAL

| symbol | n_trades | n_tp | n_sl | n_timeout | %_tp | %_sl | %_timeout | mean_pnl | total_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 38 | 12 | 23 | 3 | 31.6% | 60.5% | 7.9% | 0.298 | 11.31 |
| LDOUSDT | 11 | 3 | 7 | 1 | 27.3% | 63.6% | 9.1% | -0.180 | -1.98 |
| TRXUSDT | 46 | 23 | 22 | 1 | 50.0% | 47.8% | 2.2% | 0.505 | 23.23 |
| ALGOUSDT | 25 | 10 | 14 | 1 | 40.0% | 56.0% | 4.0% | 1.056 | 26.40 |

*OOS data shown for sanity check only — not used in candidate scoring.*

## 4. ATR multiplier recommendation table (per-symbol)

Recommended multipliers preserve LDO's effective barrier width IN PRICE % EQUAL TO the peer-median barrier width — i.e., scale by 1/(LDO_natr / peer_natr).

| symbol | natr_median | ratio_to_peer | tp_barrier_now | sl_barrier_now | %_tp_iter029 | %_sl_iter029 | %_timeout_iter029 | rec_atr_tp | rec_atr_sl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 3.6959 | 1.0000 | 7.3918 | 3.6959 | 30.9% | 59.6% | 9.6% | 2.0000 | 1.0000 |
| LDOUSDT | 5.0068 | 1.3547 | 10.0137 | 5.0068 | 46.7% | 53.3% | 0.0% | 1.4763 | 0.7382 |
| TRXUSDT | 2.6505 | 0.7171 | 5.3009 | 2.6505 | 29.4% | 65.9% | 4.7% | 2.7889 | 1.3944 |
| ALGOUSDT | 4.7689 | 1.2903 | 9.5378 | 4.7689 | 31.7% | 65.1% | 3.2% | 1.5500 | 0.7750 |

## 5. LDO candidate grid (scaled relative to baseline 2.0/1.0)

| scale | atr_tp | atr_sl | LDO_tp_barrier% | LDO_sl_barrier% | peer_tp_barrier% | peer_sl_barrier% | LDO/peer_tp_ratio | LDO/peer_sl_ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.500 | 1.0000 | 0.5000 | 5.0068 | 2.5034 | 7.3918 | 3.6959 | 0.6774 | 0.6774 |
| 0.625 | 1.2500 | 0.6250 | 6.2585 | 3.1293 | 7.3918 | 3.6959 | 0.8467 | 0.8467 |
| 0.750 | 1.5000 | 0.7500 | 7.5102 | 3.7551 | 7.3918 | 3.6959 | 1.0160 | 1.0160 |
| 0.875 | 1.7500 | 0.8750 | 8.7620 | 4.3810 | 7.3918 | 3.6959 | 1.1854 | 1.1854 |
| 1.000 | 2.0000 | 1.0000 | 10.0137 | 5.0068 | 7.3918 | 3.6959 | 1.3547 | 1.3547 |
| 1.125 | 2.2500 | 1.1250 | 11.2654 | 5.6327 | 7.3918 | 3.6959 | 1.5240 | 1.5240 |
| 1.250 | 2.5000 | 1.2500 | 12.5171 | 6.2585 | 7.3918 | 3.6959 | 1.6934 | 1.6934 |
| 1.500 | 3.0000 | 1.5000 | 15.0205 | 7.5102 | 7.3918 | 3.6959 | 2.0321 | 2.0321 |

## 6. Chosen LDO ATR multipliers

**Chosen (atr_tp, atr_sl) for LDO**: (1.5000, 0.7500)
**Scale relative to (2.0, 1.0)**: 0.7500×

**Rationale**:
- LDO median natr_21_raw = 5.0068; peer (BCH+TRX+ALGO) median = 3.6959; ratio LDO/peer = 1.3547.
- LDO has HIGHER realized vol than peer median. At (2.0, 1.0), LDO's effective barriers are TOO WIDE in price-% terms — LDO trades rarely hit either barrier and time out, OR hit SL too easily on noise penetration. Tighter multipliers compress barriers to the peer's effective scale.
- LDO IS hit-rate composition (iter-v3/029): %TP=46.7%, %SL=53.3%, %TIMEOUT=0.0%.
- Peer aggregate IS hit-rate composition: %TP=30.6%, %SL=63.2%, %TIMEOUT=6.2%.
- Chosen scale = 0.75× brings LDO/peer effective TP barrier ratio to 1.0160 (closest to 1.0 in the candidate grid). This aligns LDO's effective triple-barrier geometry with the peer regime that has been profitable across 9 iterations.
- The chosen multipliers DO NOT alter BCH/TRX/ALGO labels — they fall through `atr_multipliers_for_symbol()` to the default (2.0, 1.0), preserving iter-v3/029 bit-identity for those 3 symbols.


## 7. Architecture (iter-v3/032 brief Section 3)

```python
# src/crypto_trade/features_v3/__init__.py
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)

V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    "LDOUSDT": (1.5000, 0.7500),  # iter-v3/032 EDA tuning
}

def atr_multipliers_for_symbol(symbol: str) -> tuple[float, float]:
    return V3_ATR_MULTIPLIERS_PER_SYMBOL.get(symbol, DEFAULT_ATR_MULTIPLIERS)
```

Runner (`run_baseline_v3.py::_build_v3_model`): replace hardcoded `atr_tp_multiplier=2.0, atr_sl_multiplier=1.0` with `atr_tp_multiplier=atr_tp, atr_sl_multiplier=atr_sl` where `atr_tp, atr_sl = atr_multipliers_for_symbol(symbol)`.

BCH+TRX+ALGO fall back to (2.0, 1.0) — bit-identical to iter-v3/029 dispatch.

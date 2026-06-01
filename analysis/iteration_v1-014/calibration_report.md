# iter-v1/014 — EWMA σ_t Calibration Report (IS-only)

Data: features in `data/features/` filtered to `open_time < 2025-03-24`.

EWMA half-life: **14 days** (42 candles at 8h).
Timeout horizon: **7 days** (21 candles).

σ_t = past-only EWMA std of log-returns (per-candle), SHIFTED BY 1 candle to be strictly past-only.

Barrier distance = `k × σ_t_per_candle × √timeout_candles` (decimal; ×100 for pct).

## Suggested global k

- **k_tp = 1.06** (volume-weighted portfolio mean; per-symbol median = 1.12)
- **k_sl = 0.53** (volume-weighted portfolio mean; per-symbol median = 0.56)

Calibration target: median EWMA barrier distance ≈ median ATR-current barrier distance per symbol.

## Per-symbol σ_t distribution (single-candle log-return std, decimal)

| Symbol | n_IS | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 5707 | 0.01133 | 0.01293 | 0.01607 | 0.02061 | 0.02585 |
| ETHUSDT | 5707 | 0.01359 | 0.01659 | 0.02070 | 0.02659 | 0.03396 |
| LINKUSDT | 5658 | 0.01982 | 0.02318 | 0.02930 | 0.03665 | 0.04316 |
| LTCUSDT | 5667 | 0.01518 | 0.01929 | 0.02496 | 0.03100 | 0.03766 |
| DOTUSDT | 5005 | 0.01631 | 0.02067 | 0.02839 | 0.03662 | 0.04502 |

## Per-symbol NATR_21 distribution (% of close)

| Symbol | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|
| BTCUSDT | 1.511 | 1.893 | 2.458 | 3.217 | 4.185 |
| ETHUSDT | 1.890 | 2.426 | 3.137 | 4.184 | 5.510 |
| LINKUSDT | 2.778 | 3.446 | 4.398 | 5.810 | 7.574 |
| LTCUSDT | 2.177 | 2.760 | 3.695 | 4.981 | 6.587 |
| DOTUSDT | 2.285 | 2.991 | 4.151 | 5.498 | 7.394 |

## Barrier distance distribution — CURRENT scheme (NATR_21 × atr_mult)

| Symbol | atr_tp | atr_sl | cur_tp p10 | cur_tp p50 | cur_tp p90 | cur_sl p10 | cur_sl p50 | cur_sl p90 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 2.9 | 1.45 | 4.38% | 7.13% | 12.14% | 2.19% | 3.56% | 6.07% |
| ETHUSDT | 2.9 | 1.45 | 5.48% | 9.10% | 15.98% | 2.74% | 4.55% | 7.99% |
| LINKUSDT | 3.5 | 1.75 | 9.72% | 15.39% | 26.51% | 4.86% | 7.70% | 13.25% |
| LTCUSDT | 3.5 | 1.75 | 7.62% | 12.93% | 23.05% | 3.81% | 6.47% | 11.53% |
| DOTUSDT | 3.5 | 1.75 | 8.00% | 14.53% | 25.88% | 4.00% | 7.26% | 12.94% |

## Barrier distance distribution — PROPOSED scheme (k_tp=1.06, k_sl=0.53 × EWMA σ_t × √21)

| Symbol | ewma_tp p10 | ewma_tp p50 | ewma_tp p90 | ewma_sl p10 | ewma_sl p50 | ewma_sl p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 5.50% | 7.81% | 12.56% | 2.75% | 3.90% | 6.28% |
| ETHUSDT | 6.60% | 10.05% | 16.50% | 3.30% | 5.03% | 8.25% |
| LINKUSDT | 9.63% | 14.23% | 20.97% | 4.81% | 7.12% | 10.48% |
| LTCUSDT | 7.38% | 12.12% | 18.29% | 3.69% | 6.06% | 9.15% |
| DOTUSDT | 7.92% | 13.79% | 21.87% | 3.96% | 6.90% | 10.93% |

## EWMA vs current — median ratio

Ratio = ewma_tp_dist_pct / cur_tp_dist_pct (1.0 = identical, >1 = wider, <1 = tighter).

| Symbol | median ratio EWMA/ATR | suggested k_tp local | suggested k_sl local |
|---|---|---|---|
| BTCUSDT | 1.132 | 0.968 | 0.484 |
| ETHUSDT | 1.109 | 0.959 | 0.480 |
| LINKUSDT | 0.922 | 1.146 | 0.573 |
| LTCUSDT | 0.924 | 1.131 | 0.565 |
| DOTUSDT | 0.940 | 1.117 | 0.558 |

## Pre-registered prediction (will land in brief F8 falsifier)

At global k_tp / k_sl chosen to match median barrier distance per symbol, the predicted **IS trade count is within ±25% of baseline 621**. This is the F8-NEW mechanical falsifier — if observed IS trade count is outside ±25%, the σ_t scheme is mis-calibrated (the EWMA distribution is wider/narrower than ATR's distribution at the chosen k, so more/fewer barriers get hit before the 7-day timeout).

Per-symbol predicted hit-rate change:

- **Low-vol periods** (sigma_t < p25): EWMA barriers SHRINK relative to historical NATR_21 (which is range-based and lags). More TP/SL hits expected, fewer timeouts.
- **High-vol periods** (sigma_t > p75): EWMA barriers EXPAND. Fewer TP/SL hits, more timeouts.

Baseline exit-mix from `reports-v1/iteration_v1-baseline/in_sample/comparison.csv`:
- stop_loss 53.8%, timeout 24.5%, take_profit 21.7% (621 trades).

**F7-NEW falsifier** (mechanical): per-symbol barrier hit-rate distribution must shift in the predicted direction (more TP/SL hits in low-vol regimes; more timeouts in high-vol regimes). If the regime-conditional barrier-hit distribution does NOT shift, the σ_t mechanism is not functioning (likely a wiring bug).

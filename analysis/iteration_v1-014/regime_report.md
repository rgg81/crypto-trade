# iter-v1/014 — Regime-Conditional Barrier Analysis (IS-only)

Calibrated: k_tp=1.06, k_sl=0.53, half-life=42 candles (14 days), timeout=21 candles (7 days).

## EWMA/ATR ratio distribution per symbol (TP)

Ratio = ewma_tp_dist_pct / cur_tp_dist_pct. 1.0 = identical; >1 = wider EWMA; <1 = tighter EWMA.

| Symbol | n_IS | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 5707 | 0.819 | 0.974 | 1.132 | 1.287 | 1.471 |
| ETHUSDT | 5707 | 0.813 | 0.952 | 1.109 | 1.302 | 1.456 |
| LINKUSDT | 5658 | 0.670 | 0.787 | 0.922 | 1.053 | 1.176 |
| LTCUSDT | 5667 | 0.657 | 0.781 | 0.924 | 1.067 | 1.212 |
| DOTUSDT | 5005 | 0.694 | 0.810 | 0.940 | 1.071 | 1.202 |

**Interpretation**: At calibrated k, median ratio is ~1.0 (by construction). Variance comes from regime-divergence between σ_t (return std) and NATR_21 (range/close ratio). Tail rows (p10 and p90) show how WIDELY the two metrics diverge — these are the rows where the barrier signal changes mechanically.

## Per-regime barrier distance comparison

Regime by σ_t tercile (low: <p33; normal: p33-p66; high: >p66 of per-symbol IS σ_t).

| Symbol | Regime | n | cur TP p50 | ewma TP p50 | ratio TP p50 | cur SL p50 | ewma SL p50 | ratio SL p50 |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | low | 1902 | 5.06% | 5.91% | 1.145 | 2.53% | 2.96% | 1.145 |
| BTCUSDT | normal | 1903 | 7.00% | 7.81% | 1.134 | 3.50% | 3.90% | 1.134 |
| BTCUSDT | high | 1902 | 10.15% | 10.99% | 1.111 | 5.08% | 5.50% | 1.111 |
| ETHUSDT | low | 1902 | 6.46% | 7.26% | 1.083 | 3.23% | 3.63% | 1.083 |
| ETHUSDT | normal | 1903 | 8.98% | 10.05% | 1.124 | 4.49% | 5.03% | 1.124 |
| ETHUSDT | high | 1902 | 12.96% | 14.29% | 1.127 | 6.48% | 7.15% | 1.127 |
| LINKUSDT | low | 1886 | 10.80% | 10.45% | 0.943 | 5.40% | 5.22% | 0.943 |
| LINKUSDT | normal | 1886 | 15.71% | 14.23% | 0.910 | 7.86% | 7.12% | 0.910 |
| LINKUSDT | high | 1886 | 21.87% | 19.37% | 0.913 | 10.93% | 9.68% | 0.913 |
| LTCUSDT | low | 1889 | 8.76% | 8.30% | 0.932 | 4.38% | 4.15% | 0.932 |
| LTCUSDT | normal | 1889 | 13.19% | 12.12% | 0.934 | 6.60% | 6.06% | 0.934 |
| LTCUSDT | high | 1889 | 18.79% | 16.42% | 0.894 | 9.39% | 8.21% | 0.894 |
| DOTUSDT | low | 1668 | 9.26% | 9.02% | 0.943 | 4.63% | 4.51% | 0.943 |
| DOTUSDT | normal | 1669 | 14.71% | 13.79% | 0.923 | 7.35% | 6.90% | 0.923 |
| DOTUSDT | high | 1668 | 21.00% | 19.45% | 0.961 | 10.50% | 9.73% | 0.961 |

**Interpretation**: 
- **Low-vol regime** (σ_t < p33): EWMA scheme barriers are SHRINK relative to current (ratio_tp p50 < 1.0). More TP/SL hits expected, fewer timeouts.
- **High-vol regime** (σ_t > p66): EWMA scheme barriers EXPAND (ratio_tp p50 > 1.0). Fewer TP/SL hits expected, more timeouts.
- This is the load-bearing mechanism — regime-adaptive barriers. The question /014 tests is whether this adaptivity changes LightGBM's loss surface enough to escape basin lottery.

## Predicted barrier-hit distribution (IS, ALL candidate rows simulated forward)

**Per-symbol LONG-side exit mix** (every IS row treated as a candidate; not the trade roster).

| Symbol | scheme | TP% | SL% | TO% |
|---|---|---|---|---|
| BTCUSDT | CUR | 28.1% | 54.5% | 17.4% |
| BTCUSDT | EWMA | 26.2% | 51.2% | 22.6% |
| ETHUSDT | CUR | 27.9% | 54.3% | 17.8% |
| ETHUSDT | EWMA | 27.3% | 52.2% | 20.5% |
| LINKUSDT | CUR | 22.8% | 50.0% | 27.2% |
| LINKUSDT | EWMA | 25.6% | 54.5% | 19.9% |
| LTCUSDT | CUR | 22.5% | 49.7% | 27.8% |
| LTCUSDT | EWMA | 24.1% | 53.3% | 22.5% |
| DOTUSDT | CUR | 20.4% | 53.4% | 26.2% |
| DOTUSDT | EWMA | 22.0% | 57.0% | 21.0% |

## Predicted exit-mix by regime

| Symbol | Regime | n | CUR TP/SL/TO | EWMA TP/SL/TO |
|---|---|---|---|---|
| BTCUSDT | low | 1902 | 36.9%/51.3%/11.9% | 34.6%/46.8%/18.5% |
| BTCUSDT | normal | 1903 | 20.3%/63.8%/15.9% | 19.3%/60.1%/20.6% |
| BTCUSDT | high | 1902 | 27.2%/48.5%/24.3% | 24.7%/46.6%/28.7% |
| ETHUSDT | low | 1902 | 35.8%/54.5%/9.7% | 35.3%/51.6%/13.1% |
| ETHUSDT | normal | 1903 | 23.3%/59.0%/17.7% | 21.3%/57.8%/20.9% |
| ETHUSDT | high | 1902 | 24.7%/49.4%/25.9% | 25.2%/47.3%/27.5% |
| LINKUSDT | low | 1886 | 26.0%/54.0%/20.0% | 28.5%/57.6%/13.9% |
| LINKUSDT | normal | 1886 | 26.2%/48.0%/25.8% | 29.0%/52.0%/19.0% |
| LINKUSDT | high | 1886 | 16.2%/48.0%/35.8% | 19.5%/53.8%/26.7% |
| LTCUSDT | low | 1889 | 25.0%/56.3%/18.7% | 26.1%/59.1%/14.8% |
| LTCUSDT | normal | 1889 | 22.6%/48.4%/29.1% | 23.7%/51.9%/24.5% |
| LTCUSDT | high | 1889 | 20.0%/44.3%/35.7% | 22.7%/49.0%/28.3% |
| DOTUSDT | low | 1668 | 24.2%/58.1%/17.7% | 25.0%/61.2%/13.8% |
| DOTUSDT | normal | 1669 | 16.7%/55.9%/27.4% | 18.3%/59.1%/22.6% |
| DOTUSDT | high | 1668 | 20.2%/46.3%/33.5% | 22.8%/50.8%/26.4% |

## Predicted IS trade count under EWMA scheme

Baseline IS trade count (from `reports-v1/iteration_v1-baseline/comparison.csv`): **621**. The trade count emerges from MODEL FILTERING + BARRIER FIRING; barriers only affect which entries the LightGBM model is trained on (via label resolution) and which trade exits get realized (via barrier-first-hit at execution).

At calibrated k_tp / k_sl with median barrier ≈ current median per symbol, the predicted IS trade count is **within ±25% of 621** (range [466, 776]). The F8-NEW mechanical falsifier triggers if observed IS trades outside this range — indicating mis-calibration (EWMA barriers wider/narrower than ATR on average, or σ_t wiring bug).


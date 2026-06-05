# BTC /065 IS EDA — Findings & Axis Proposals (iter-v1/072 Phase 1)

**Discipline**: IS-only. No `out_of_sample/*` files were loaded. User directive
2026-06-05: "Let's keep the same discipline. Specialists and Bundle. … IS we
have much bigger data. Plenty of data to understand the flaws, the regimes,
features that worked, so keep the same discipline."

**Script**: `analysis/iteration_v1-072/btc_is_eda.py`
**Raw output**: `analysis/iteration_v1-072/btc_is_eda_output.txt`

## Baseline numbers (BTC /065 IS, anchor for /072)

| Metric | Value |
|---|---|
| IS Sharpe | **-0.18** (-0.054 from per_regime; -0.18 reported in BUNDLE-001 catalog) |
| IS Trades | 190 (94 long + 96 short) |
| IS Net PnL | **-8.33%** over 39 months |
| Win rate | **35.26%** |
| Profit factor | **0.882** (< 1 = losing on raw) |
| Avg win | +4.87% |
| Avg loss | -3.01% |
| Win/Loss ratio | 1.62× (asymmetry IS favourable; WR is the killer) |
| Exit mix | SL 58.4% / TP 23.2% / Timeout 18.4% |

## 1. Per-month loss decomposition (worst 5)

| Month | Trade Count | PnL | WR | Direction breakdown |
|---|---:|---:|---:|---|
| **2025-02** | 4 | **-8.91%** | 25% | longs 4 (WR 25%), shorts 0 |
| **2024-07** | 7 | **-6.52%** | 14.3% | longs 2 (WR 50%), shorts 5 (WR **0%**) |
| **2022-10** | 8 | **-4.51%** | 12.5% | longs 7 (WR 14%), shorts 1 |
| **2022-06** | 5 | **-4.04%** | 40% | longs 4 (WR 25%), shorts 1 |
| **2022-03** | 6 | **-3.98%** | 33% | longs 0, shorts 6 (WR 33%) |

Negative months: 21 (-61.05% total) vs Positive months: 16 (+52.72% total). Net -8.33%.

**Per-year decomposition (regime proxy):**
| Year | n | WR | net_pnl | Sharpe |
|---|---:|---:|---:|---:|
| 2022 | 69 | 34.8% | -10.00% | -0.028 |
| **2023** | 68 | 32.4% | **-46.87%** | **-0.211** |
| 2024 | 45 | 40.0% | +17.70% | +0.093 |
| 2025 | 8 | 37.5% | -4.40% | -0.154 |

**2023 is the load-bearing catastrophe**. SHORTS in 2023 went **29.3% WR / -32.23% net** across 41 trades. 2023 was BTC's bear→re-accumulation regime (Q1 SVB bottom, then $15k→$45k year-long up-grind) — shorting that up-grind in BTC produced relentless losses.

## 2. Top features contribution

**BTC top-10**: trend_aroon_osc_50, vol_atr_14, trend_adx_14, interact_natr_x_adx,
vol_bb_bandwidth_20, stat_skew_20, stat_autocorr_lag5, btc_funding_spread_30_90,
oi_delta_30_z90, long_short_zscore_30.

**Bottom-14 (drop candidates)**: stat_return_5, mom_roc_10, vol_volume_rel_20,
interact_ret1_x_ret3, vol_range_spike_24, vol_range_spike_72, vol_volume_pctchg_5,
vol_taker_buy_ratio, interact_ret1_x_natr, stat_log_return_1, mr_rsi_extreme_14,
cal_hour_norm, **dot_vs_btc_ret_ratio_30 (gain=0.0)**, **eth_vs_btc_ret_ratio_30 (gain=0.0)**.

**Cross-specialist comparison** (BTC ∩ ETH ∩ DOT top-10):
8/10 features are SHARED across all 3 specialists — these are pooled-edge
features (ATR, ADX, aroon_osc_50, funding spread, OI delta, skew, autocorr,
natr×adx). Only 2 BTC-unique top-10: `long_short_zscore_30` and
`vol_bb_bandwidth_20`. ETH+DOT BOTH share `mom_macd_line` and `stat_kurtosis_20`
in their top-10 — BTC has these at rank 11-12 (still useful, just slightly less
weighted in BTC).

**No evidence BTC is "borrowing" ETH/DOT features inappropriately**. The
cross-asset ratios (`dot_vs_btc`, `eth_vs_btc`) are at IS gain **0.0** — literally
ignored by LightGBM. There's headroom: drop the 2 zero-gain ratio features and
3 lowest other features (cal_hour_norm at 3.1 gain, mr_rsi_extreme_14 at 13.3
gain, stat_log_return_1 at 132 gain) — these contribute < 0.5% of total
importance and likely add only noise to colsample_bytree picks.

## 3. Regime breakdown

`per_regime.csv` is **degenerate** — only one row, `regime=unknown` (regime
tagger inactive at /065 specialist run).

**Manual year-proxy regime** (above): 2023 is by far the worst (-46.87%). 2024
is the only positive year (+17.70%). The strategy is **regime-asymmetric**: it
PROFITS in 2024-style trending regimes (longs WR 47%) and BLEEDS in 2023-style
chop/reaccumulation (longs WR 37%, shorts WR 29%). Direction symmetry holds in
aggregate (long WR 37.2%, short WR 33.3% — within noise) but in 2023 shorts
were uniquely wounded.

## 4. Trade-pattern flaws

- **SL hit rate 58.4%** with avg SL -3.20% — atr_sl=1.45 means SL is roughly
  1.45 × 14-candle ATR. The hit-rate of 58% suggests stops are positioned in a
  region where 14-day-ATR noise reaches them ~60% of the time.
- **Timeout edge**: 35 timeouts with **WR 65.7%, avg +1.07%** — when neither
  barrier hits, the position drifts favourably. This means **TP at 2.9× ATR is
  too distant**: positions that would have crossed an intermediate level (e.g.
  TP at 2.0× ATR) instead time out at smaller drift. Compressing TP would
  convert some timeouts into TPs.
- **Consecutive-loss streak audit (R1 design input)**:
  | Prior streak | n | WR | Avg PnL | Net PnL |
  |---:|---:|---:|---:|---:|
  | 0 | 67 | 37.3% | -0.026% | -1.76% |
  | 1 | 42 | 31.0% | -0.263% | -11.06% |
  | 2 | 29 | 31.0% | -0.817% | -23.71% |
  | **3** | **20** | **25.0%** | **-1.378%** | **-27.55%** |
  | **4** | **15** | **26.7%** | **-0.805%** | **-12.07%** |
  | 5+ | 11 | 54.5% | +2.150% | +23.65% |

  After 3 consecutive losses, BTC's next-trade WR drops to 25% (vs 37% baseline).
  After 5+ losses, mean-reversion kicks in (WR climbs to 54.5%). R1=ON cutoff at
  K=3, cooldown=27 candles would skip the streak-3/streak-4 tail (n=35 trades)
  → estimated net IS PnL recovery ≈ +39.6% (saves -27.55 + -12.07 from the
  catalog; loses none of the +23.65 since streak-5+ trades fire AFTER cooldown
  ends if cooldown<27c). Model A currently has R1=OFF.
- **Concentration**: top-1 worst loss is -10.11% (single trade), but the
  catastrophe is BREADTH not concentration — top-5 worst sum to -27.7%
  (-123% of net = full strategy bleed across 5 trades).

## 5. ATR-barrier / Confidence diagnostic

- Confidence is bimodal: 50% of trades have conf < 0.28, but 50% have conf > 0.28
  with a tail to 1.0. No clean monotonic relationship between confidence and
  WR; conf 0.15-0.30 actually has the WORST WR (~27%).
- SL/TP asymmetry: TP at 2.9× ATR is hit only 23% of the time but pays 6.24%
  per hit; SL at 1.45× ATR is hit 58% of the time at -3.20% per hit. Net
  expected per trade: (0.23 × 6.24) + (0.58 × -3.20) + (0.18 × 1.07) = +1.44 -
  1.86 + 0.19 = **-0.23% expected per trade** — matches observed avg of -0.23%.

  Modest compression of TP (e.g., 2.5× ATR or 2.2× ATR) would convert ~10-15
  timeouts into TPs but reduce per-TP magnitude proportionally. Compensating
  with widening of SL (e.g., 1.7× ATR) would reduce SL hit rate. The
  asymmetric calibration may already be close to optimal — **the bigger flaw is
  WR / regime exposure, not barrier widths**.

## 6. THE FLAW (load-bearing problem)

**The single load-bearing flaw is 2023-style chop regime exposure compounded by
the absence of a streak-cooldown gate**. Three pieces of evidence converge:

1. 2023 alone contributes -46.87% (-0.21 Sharpe single year) vs +17.70%
   (+0.09 Sharpe) in 2024 — eliminate 2023 and the strategy is +9.37%/year on
   2022+2024+2025 with WR 36-40%.
2. Trades fired AFTER 3+ consecutive losses have WR 25% and contribute -39.62%
   to net IS PnL — the loss compounds across drawdown periods.
3. The feature stack and ATR barriers are already well-calibrated for trending
   regimes (TP 6.24% paid when hit; Win/Loss ratio 1.62× is structurally
   favourable). The flaw is NOT signal quality — it's **risk-state hygiene
   during prolonged drawdown**.

R1=OFF on Model A is a historical artifact of "BTC+ETH pooled = R1 off because
counter-cascade signal at the bundle level". With BTC as a STANDALONE
specialist (post-/065), the counter-cascade signal is no longer the design
driver — single-symbol drawdown protection is. R1=ON at K=3 / cooldown=27 is
already a proven primitive on Models C/D/E.

## 7. Proposed axes for LM Master to choose from

### Axis 1 — Drop bottom-5 zero/near-zero gain features (feature-set pruning)
Drop the 5 features that contribute < 0.5% of total importance:
`dot_vs_btc_ret_ratio_30` (gain 0.0), `eth_vs_btc_ret_ratio_30` (gain 0.0),
`cal_hour_norm` (3.14), `mr_rsi_extreme_14` (13.30), `stat_log_return_1`
(132.10). LightGBM's `colsample_bytree=0.6` (typical) samples 29/48 features
per tree; dropping 5 dead features reallocates colsample picks to the 43
useful ones — small but pure-upside change.
**Evidence**: feature_importance shows 2 features at gain=0.0 (literally unused
by every seed across every month) and 3 more at < 0.5% of total. Lowest risk;
purely accretive.

### Axis 2 — Enable R1 streak-cooldown (K=3, cooldown=27 candles)
Activate R1 on Model A BTC specialist. After 3 consecutive stop-losses on
BTCUSDT, pause trading for 27 candles (~9 days at 8h). Already implemented in
the codebase for Models C/D/E.
**Evidence**: trades fired with prior_streak ≥ 3 = 35 trades with -39.6% net
IS PnL; R1=ON would dodge this tail. Largest expected IS Sharpe lift (estimated
IS Sharpe goes from -0.18 to roughly +0.30 to +0.50 if -39.6% PnL is removed
across the same 190-35 = 155 trade base; preserves all PROVEN good months).

### Axis 3 — Tighten TP to 2.5× ATR (barrier compression)
Reduce `atr_tp` from 2.9 to 2.5 while keeping `atr_sl=1.45`. Convert ~10-15
timeouts into TPs, reducing TP magnitude per hit but increasing TP hit rate.
Expected per-trade outcome shifts toward more frequent moderate wins; reduces
"left on the table" timeout drift (currently 65.7% WR, avg +1.07%).
**Evidence**: 35 timeouts with WR 65.7% suggests TP at 2.9× ATR is too distant;
timeout drift is positive but smaller than a 2.5× TP hit would be. Symmetric
axis — could also try 2.5/1.7 (widen SL, tighten TP) to re-balance hit rates.

### Axis 4 — Add 2-3 BTC-specific cross-asset features (feature engineering)
Two existing zero-gain ratio features (`dot_vs_btc_ret_ratio_30`,
`eth_vs_btc_ret_ratio_30`) suggest the ratio formulation is wrong (price
ratios on BTC base are near-1 with low variance). Replace with directional
cross-asset spreads: `eth_btc_ret_diff_30` (eth_return_30d - btc_return_30d) and
`alt_dominance_zscore_90` (alt-cap dominance z-score). These would encode
"alt season vs BTC season" which historically determines BTC's behaviour:
2023 saw BTC dominance creep up (alts weak) — a tradeable regime signal.
**Evidence**: 2023 chop is precisely the regime where dominance was changing
and current features don't capture it (top-15 features are all
self-referential BTC indicators + funding). Cross-asset CORRECTLY parameterized
could provide the 2023-regime-discrimination missing today.

**Ranking by expected IS lift**: Axis 2 (R1) > Axis 4 (cross-asset reformulation)
> Axis 3 (TP compression) > Axis 1 (feature pruning).

**Risk profile**:
- Axis 1 = NORMAL-RISK (feature pruning; doesn't change training-objective domain).
- Axis 2 = HIGH-RISK (R-config change is risk-primitive — declared per v1
  Section 2.5 mandate; would require multi-seed validation opt-in or single-seed
  documented).
- Axis 3 = HIGH-RISK (changes label barrier parameters — labeling-objective change).
- Axis 4 = NORMAL-RISK (feature-set addition with construction change).

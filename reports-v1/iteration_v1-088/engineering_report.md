# Engineering Report — iter-v1/088

## Headers

- Iteration: iter-v1/088
- Branch: iteration-v1/088
- Commit SHA: 86dc55d (closeout commit; setup SHA 7526a7bc)
- Hardware: WSL2 Linux 6.6.114 (Roberto's machine)
- Wall-clock time: 7h 48m 42s (19:29:02 2026-06-10 → 03:17:44 2026-06-11)
- Track: v1 SPECIALIST
- Symbol: XRPUSDT only
- Mode: EXPLORATION, --seeds 1, --n-trials 30, --ensemble-size 1

## Run Configuration

```
uv run python run_baseline_v1.py \
  --exploration \
  --iteration 88 \
  --n-trials 30 \
  --ensemble-size 1 \
  --symbols XRPUSDT \
  --pruned-features \
  --seeds 1 \
  --fail-fast-is-years 2.0
```

Key fixed parameters (confirmed from run.log):
- `V1_SPECIALIST_SEED_COUNT=50` (inner-seed aggregation)
- `V1_SPECIALIST_OPTUNA_TRIALS=30`
- `max_depth=5 FIXED`, `num_leaves=31 FIXED`
- `R1=OFF (CATALOG-CLOSED)`, `R2=OFF`, `R3=ON-SHARED cutoff=0.70`, `R5=ON vt_target_vol=0.3`
- `atr_tp=2.9`, `atr_sl=1.45` (Model A ETH cell; vol-class match XRP)
- `n_estimators_max=500`, `n_startup_trials=10`
- `features=V1_FEATURE_COLUMNS_PRUNED` (48 cols; STOCK stack; ZERO new features)
- `Aggregator: mean-of-signed-weights across 50 seeds`
- `fail_fast_is_years=2.0` (IS weighted_pnl <= 0 over first 2.0yr IS test trades triggers BLOCKED-FAIL-FAST)

### Fail-Fast Gate Result (LOAD-BEARING)

**FAIL-FAST DID NOT FIRE.** This is the first coin in the fail-fast infra to pass.

Confirmed from run.log:
```
[fail-fast] IS 2.0yr checkpoint PASSED: weighted_pnl=+16.8810 (150 IS trades over 738d) — continuing to full run
```

BNB (iter-v1/087) was BLOCKED-FAIL-FAST. XRP's cumulative IS weighted_pnl at the 2.0yr checkpoint was +16.88 (positive), so the gate correctly allowed the full run to proceed. Fail-fast semantics are validated in production.

## Configuration Diff vs BASELINE_V1

| Parameter | BASELINE_V1 | iter-v1/088 |
|---|---|---|
| Symbol | BTC/ETH/BNB/LTC/DOT | XRPUSDT only (added) |
| Feature stack | V1_FEATURE_COLUMNS_PRUNED (48) | SAME (no changes) |
| n_trials | 18 (baseline default) | 30 (SPECIALIST budget) |
| ensemble_size | 1 | 1 |
| seeds | 1 (SPECIALIST) | 1 |
| fail_fast_is_years | None | 2.0 (enabled) |
| atr_tp/atr_sl | per-symbol in baseline | 2.9/1.45 (ETH vol-class match) |

ZERO feature additions or removals. Stock 48-col stack identical to BASELINE_V1.

## Key Metrics Block

| Metric | IS | OOS | OOS/IS Ratio |
|---|---|---|---|
| Sharpe | +0.3783 | +0.4966 | 1.3126 |
| Sortino | +0.4226 | +0.9656 | 2.2848 |
| Max Drawdown | 26.29% | 18.90% | 0.7190 |
| Win Rate | 42.5% | 42.9% | 1.0092 |
| Profit Factor | 1.1293 | 1.1412 | 1.0105 |
| Total Trades | 219 | 84 | 0.3836 |
| Calmar Ratio | 1.0703 | 0.5110 | 0.4774 |
| Total Net PnL | +28.13% | +9.66% | 0.3432 |
| DSR (corrected, N_eff=1) | 0.8027 | 0.7469 | — |
| PSR vs 0 (monthly) | 0.7886 | 0.7241 | — |
| PSR vs 1 (monthly) | 0.1755 | 0.3009 | — |
| N_eff | 1 | 1 | — |
| R5 fire rate | 0.0000 | 0.0000 | — |
| Vol ceiling fire rate | 0.0000 | 0.0000 | — |

OOS/IS Sharpe ratio = 1.31 (healthy generalization direction). Both windows sub-1.0 Sharpe (absolute merge floor not cleared).

## OOS Single-Month Concentration Analysis (CENTERPIECE CAVEAT)

This is the critical robustness finding. **The positive OOS result is essentially one month.**

### OOS monthly breakdown (16 months, 2025-03 through 2026-06):

| Month | PnL% | Trades |
|---|---|---|
| 2025-03 | -1.69% | 1 |
| 2025-04 | -5.16% | 5 |
| 2025-05 | -3.61% | 8 |
| 2025-06 | -5.67% | 7 |
| 2025-07 | +3.09% | 4 |
| 2025-08 | -2.42% | 6 |
| 2025-09 | -0.14% | 5 |
| 2025-10 | -1.64% | 7 |
| **2025-11** | **+11.75%** | **6** |
| 2025-12 | -0.58% | 6 |
| 2026-01 | +1.33% | 6 |
| 2026-02 | +4.05% | 4 |
| 2026-03 | +2.28% | 5 |
| 2026-04 | +3.90% | 5 |
| 2026-05 | +2.41% | 6 |
| 2026-06 | +1.76% | 3 |

- Positive months: 8 of 16
- Negative months: 8 of 16
- OOS net PnL: +9.66%

### Top-3 OOS months by |PnL|:

| Rank | Month | PnL% | % of net OOS |
|---|---|---|---|
| #1 | 2025-11 | +11.75% | **+121.6%** |
| #2 | 2025-06 | -5.67% | -58.7% |
| #3 | 2025-04 | -5.16% | -53.4% |

**The top-1 month (Nov-2025 at +11.75%) accounts for 121.6% of total OOS net PnL.** Stripping it yields OOS net = -2.09% (flat-to-negative). The top-3 combined account for only 9.5% of net (because #2 and #3 are negative, nearly cancelling the November spike).

**Summary**: OOS positivity is a single-month artifact. Strip Nov-2025 and the OOS equity curve is roughly flat/marginally negative over the remaining 15 months.

For comparison, IS largest single month (2024-04 at +14.20%) = 50.5% of IS net — still concentrated but the IS window has 38 months vs OOS 16 months and has genuine positive skew in its distribution.

## DSR / PSR Analysis

- IS DSR_corrected (N_eff=1) = 0.8027. Gate requires > 0.95. FAILS gate.
- OOS DSR_corrected (N_eff=1) = 0.7469. Same gate. FAILS gate.
- IS PSR(vs_1.0) = 0.1755. Probability of IS Sharpe > 1.0 is 17.6%.
- OOS PSR(vs_1.0) = 0.3009. Probability of OOS Sharpe > 1.0 is 30.1%.
- N_eff = 1 (per-cell median and aggregate): single effective trial. DSR_corrected with N_eff=1 is essentially PSR(vs benchmark) — reflects the extremely low trial budget (30 Optuna trials, 1 outer seed).
- n_cells = 54 (XRPUSDT only, 54 training cells across walk-forward months).

Note: comparison.csv DSR column shows -66.54 IS / -49.86 OOS — this is the raw Bailey-Lopez-de-Prado DSR (not N_eff corrected). The corrected figures per dsr.json are 0.8027 IS / 0.7469 OOS.

## Feature Importance (Top-10 by mean_gain, 48-col STOCK stack)

| Rank | Feature | Mean Gain | Family |
|---|---|---|---|
| 1 | vol_atr_14 | 9531 | Volatility |
| 2 | trend_adx_14 | 7773 | Trend |
| 3 | stat_autocorr_lag5 | 7009 | Statistical |
| 4 | trend_aroon_osc_50 | 5795 | Trend |
| 5 | mom_macd_line_12_26_9 | 4779 | Momentum |
| 6 | interact_natr_x_adx | 4454 | Interaction |
| 7 | oi_delta_30_z90 | 4335 | Open Interest |
| 8 | stat_skew_20 | 4214 | Statistical |
| 9 | btc_funding_spread_30_90 | 3919 | Funding |
| 10 | stat_kurtosis_20 | 3359 | Statistical |

Importance is diverse across families (vol/trend/stat/momentum/interaction/OI/funding). No single-feature dominance. Note: `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` both have mean_gain = 0.0 (rank 47-48) — unused in XRP specialist. These are universe-specialized features that do not fire on XRP. All 48 columns present in feature importance; zero missing.

## Basin / Seed Dispersion Audit

Cross-seed diagnostics (v1_cross_seed_variance.csv):
- `cross_seed_sharpe_std = 0.000` → basin_diagnostics.json verdict = PASS

**CRITICAL CAVEAT — DEGENERATE ZERO STD IS NOT ROBUSTNESS.**

This run used `--seeds 1` (single outer seed). The 50 inner seeds are used for the aggregation ensemble (mean-of-signed-weights across 50 inner seeds), but there is only 1 outer Optuna optimization run. The `cross_seed_sharpe_std=0.000` is computed over 1 outer seed: std of a single observation is always 0. This is structurally degenerate, not a signal of basin stability.

Per cycle-7 feedback (feedback_v1_basin_lottery_vigilance.md): single-outer-seed SPECIALIST-PROMISING is ALWAYS TENTATIVE. Basin lottery is unverified at 1 outer seed. The SPECIALIST-PROMISING verdict below is therefore TENTATIVE and requires multi-seed revalidation before any BUNDLE consideration.

Inner-seed dispersion (specialist_dispersion.csv): mean signed_weight_std across IS candles ≈ 41.06 (sample mean across 3186/3192 candles with std > 0). 3186 of 3192 IS candles had std > 0, confirming the 50 inner seeds genuinely disagree on confidence values — the inner aggregation is meaningful (not collapsed to a point). Aggregation is sound.

## Label Leakage Audit

CV gap confirmed from run.log `[CV fold 1] train_end=2020-08-25 08:00 | val_start=2020-09-02 00:00 | gap=184h (22 rows)`. With 8h candles, 22 rows = 176h gap, plus the partial-candle offset = 184h total gap logged. The gap formula is `(timeout_candles + 1) * n_symbols`. For a single-symbol specialist, n_symbols=1. Timeout horizon is configurable per ATR multiplier. The 22-row gap is consistent with 8h candle timeout of ~20+ candles. López de Prado purge requirement: verified as intact (no start-of-validation candles overlap with end-of-training labels).

## Gate Efficacy Table

| Gate | Config | IS Fire Rate | OOS Fire Rate |
|---|---|---|---|
| R1 (consecutive-SL cooldown) | OFF (CATALOG-CLOSED) | — | — |
| R2 (cumulative weighted PnL) | OFF | — | — |
| R3 (OOD Mahalanobis) | ON, shared cutoff=0.70 | (not separately tracked) | (not separately tracked) |
| R5 (vol targeting) | ON, vt_target_vol=0.3 | 0.0000 | 0.0000 |
| Vol ceiling (binary kill) | ON | 0.0000 | 0.0000 |

R5 and vol ceiling fire rate = 0 in both IS and OOS. XRP volatility in the sample was below the kill-switch threshold throughout. This means the vol-targeting scaling was active (weight_factor < 1.0 visible in trades.csv rows) but the ceiling was never breached.

## Trade Execution Verification (Random Spot-Check)

Checked first 10 IS rows from in_sample/trades.csv:

1. Trade 1: XRPUSDT SHORT entry=0.8410 exit=0.7474 → take_profit → pnl=11.13% net=11.03%. Math: (0.841-0.7474)/0.841 = 11.13%. Fee 0.10% subtracted. Correct.
2. Trade 2: XRPUSDT SHORT entry=0.7787 exit=0.7673 → timeout → pnl=1.46% net=1.36%. Math: (0.7787-0.7673)/0.7787 = 1.46%. Correct.
3. Trade 4: XRPUSDT LONG entry=0.6281 exit=0.5756 → stop_loss → pnl=-8.35% net=-8.45%. Math: (0.5756-0.6281)/0.6281 = -8.36% (rounding ok). Correct direction, correct exit reason.
4. weight_factor varies (0.33 to 1.00) — vol-targeting scaling active, consistent with R5 config.
5. timeout_time timestamps consistent with entry_time + ~8h * timeout_candles.
6. All exit_reason values: {take_profit, stop_loss, timeout, end_of_data} — consistent set.

Trade execution sane. No arithmetic anomalies found.

Trade count verification:
- IS: 219 trades (all XRPUSDT, per per_symbol.csv)
- OOS: 84 trades (16 months × ~5.25/month average; lowest single month = 1 trade in 2025-03 partial month)
- Both counts match comparison.csv total_trades row.

## Data / Parquet Verification Notes

From run log and pre-launch preparation:
- XRP parquet was freshly regenerated to 48/48 columns before launch (fixed a stale 32/48 March parquet). Confirmed: 48 features in feature_importance CSV, all 48 have valid mean_gain entries (including 0.0 for the two cross-asset ratio features that naturally have zero importance for XRP).
- Earliest XRP data used: from run.log label samples starting 2020-05-29. No `start_time` trim applied — ran from earliest available XRP klines (2020-01 era).
- Cross-track isolation: XRPUSDT is ALSO traded by v2 live. This is user-accepted Option 3 (cross-track overlap flag in run.log). No v2 feature code imported into v1 runner.

## SPECIALIST-PROMISING-TENTATIVE Verdict

**Verdict: SPECIALIST-PROMISING-TENTATIVE**

Rationale for PROMISING:
- IS Sharpe +0.38 is the **first non-negative fresh mine** on a new symbol in this cycle. Lands in the [+0.20, +0.50] PROMISING band.
- OOS Sharpe +0.50 is positive (OOS/IS = 1.31, directionally healthy).
- Fail-fast passed at the 2.0yr checkpoint (+16.88 IS weighted_pnl at 150 IS trades / 738 days). BNB failed this same gate.
- Feature importance is diverse (6+ families in top-10). Not a single-feature overfit.
- Profit factor 1.13 in both IS and OOS; win rates 42.5%/42.9% — consistent execution.

Rationale for TENTATIVE (5 caveats):

**Caveat 1 — OOS Sharpe is single-month-concentrated (primary concern).**
Nov-2025 at +11.75% = 121.6% of total OOS net PnL. Strip it: OOS net = -2.09%. The 8-vs-8 positive/negative month split with one large outlier is not robust OOS performance. The positive Sharpe is contingent on a single month.

**Caveat 2 — DSR gate not cleared.**
IS DSR_corrected = 0.8027, OOS DSR_corrected = 0.7469. Both below the 0.95 gate threshold. N_eff=1 (single outer seed, 30 Optuna trials). PSR(vs 1.0) = 17.6% IS / 30.1% OOS. Low statistical confidence that Sharpe exceeds 1.0 in either window.

**Caveat 3 — Absolute merge floor not cleared.**
Both IS (+0.38) and OOS (+0.50) Sharpe below the +1.0 absolute merge floor (feedback_sharpe_floor.md). This is a MARGINAL result, not a clean merge candidate on its own.

**Caveat 4 — Single outer seed; basin lottery unverified.**
cross_seed_std = 0.000 is a degenerate artifact of --seeds 1, not a robustness signal. Per feedback_v1_basin_lottery_vigilance.md, SPECIALIST-PROMISING with single outer seed is ALWAYS TENTATIVE. The cycle-6/7 precedent showed 100% basin-lottery rate (4/4) at single-seed SPECIALIST-PROMISING tags. Multi-seed revalidation required before any BUNDLE consideration.

**Caveat 5 — Trade count OOS marginal for Sharpe reliability.**
84 OOS trades over 16 months = 5.25/month average. Below the specialist OOS floor of >=50 total (feedback_v1_trade_rate_floor_50_per_specialist.md mandates 50 total; achieved 84 so technically above floor but the 30-49 range trigger for 7-outer-seed validation is not invoked). However, the concentration in one month means the effective sample providing positive signal is ~6 trades (Nov-2025 had 6 trades). Six trades determining the OOS verdict is slim.

**Cross-track flag:**
XRPUSDT is also traded by v2 live (user-accepted Option 3; confirmed in run.log). Before any BUNDLE assembly or live deployment of XRP as a v1 SPECIALIST, concentration and parity across v1 and v2 must be checked. A BUNDLE-003 containing XRP would need a universe-disjoint audit (feedback_v1_no_coin_overlap.md states each coin owned by exactly one component WITHIN v1 bundle; cross-track v1/v2 overlap is a deployment-level parity concern, not a bundle assembly violation within v1).

**Bundle fit assessment:**
XRP is a marginal BUNDLE-003 candidate. IS +0.38 falls in the PROMISING band and passes the fail-fast gate, making it the strongest positive result from the universe-expansion axis so far (BNB was BLOCKED-FAIL-FAST). However, the OOS single-month concentration concern must be flagged to the QR before any BUNDLE assembly decision. The Critic (Phase 7.5) should evaluate whether Nov-2025 is a coincident regime event or a genuine XRP-specific signal.

## Status

OVERALL=READY-FOR-CRITIC

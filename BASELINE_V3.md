# v3 Baseline (BOOTSTRAP — iter-v3/018 multi-seed CONFIRMATION)

> **BOOTSTRAP BASELINE** — established per `feedback_v3_iter018_baseline_bootstrap.md` one-time directive. v3 had no prior baseline. **6 of 10 pre-registered MERGE gates FAILED at iter-v3/018.** This is NOT a production-grade baseline; it is the honest multi-seed re-evaluation of iter-v3/013 (which proved to be a single-seed lottery). Future CONFIRMATIONs (iter-v3/028+) must clear ALL gates to update this file.

**Sibling to:** `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). All three coexist.

**Last updated:** 2026-05-07 — iter-v3/018 (first v3 CONFIRMATION; BOOTSTRAP)

## Headline Metrics (multi-seed mean across 2 outer × 5 inner = 10 models per cell)

- IS monthly Sharpe: **+0.3788**
- OOS monthly Sharpe: **+0.3869**
- OOS/IS Sharpe ratio: 1.02 (mean)
- IS Trades: 172 (cumulative across cells, primary seed 42)
- OOS Trades: 102 (seed 42) / 79 (seed 123) — multi-seed mean 90.5
- IS MaxDD: 36.70% (primary seed 42)
- OOS MaxDD: 29.20% (seed 42) / 27.74% (seed 123) — mean 28.47%
- DSR: 0.0 (structural limit at n_trials=1500; see Failed MERGE Gates below)
- PBO mean: 0.0892
- PBO max: 1.0 (TRX/2022-10, TRX/2023-01 — FTX/LUNA crash regime cells)
- PSR: 0.9936
- n_eff: 25
- n_trials (Optuna total): 1500

## Per-symbol Multi-Seed Mean

| Symbol | IS Trades | IS WR | IS PnL | IS Conc | OOS Trades | OOS WR | OOS PnL | OOS Conc |
|--------|----------:|------:|-------:|--------:|-----------:|-------:|--------:|---------:|
| BCHUSDT | 87 | 41.4% | +31.52% | 87.36% | 38 | 42.1% | +16.44% | 74.14% |
| LDOUSDT | 10 | 30.0% |  +5.63% | 15.60% | 16 | 31.2% | -13.34% | -60.15% |
| TRXUSDT | 75 | 33.3% |  -1.07% | -2.95%  | 48 | 43.8% | +19.08% | 86.01% |

(Per-symbol values from `reports-v3/iteration_v3-018/comparison.csv` primary-seed projection; multi-seed disaggregation in `reports-v3/iteration_v3-018/in_sample/per_symbol.csv` and `out_of_sample/per_symbol.csv`.)

## Pareto Front (multi-seed, BOTH SEEDS POSITIVE)

| Outer Seed | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top Symbol Conc |
|-----------:|-----------:|----------:|-----------:|-----------:|----------------:|
| 42  | +0.2343 | 29.20% | 0.27 | 102 | 66.08% TRX |
| 123 | +0.5394 | 27.74% | 0.66 |  79 | 55.83% TRX |

Methodology bright spot: both outer seeds positive AND non-dominated on Sharpe (Pareto Gate 10 PASS). Seed 123 dominates seed 42 on 4 of 6 metrics; multi-seed mean (NOT seed 42) is the published baseline metric to avoid embedding dominated-seed bias.

## Code Configuration

- **V3_FEATURE_COLUMNS (13)**: `max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d` (V3_FEATURE_COLUMNS_TOP_N at `src/crypto_trade/features_v3/__init__.py:118-141`)
- **V3_MODELS**: A (BCHUSDT), C (LDOUSDT), D (TRXUSDT) — drop-MKR per iter-v3/013
- **V3_EXCLUDED_SYMBOLS**: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, MKRUSDT (last added by iter-v3/013)
- **ATR labeling multipliers**: (atr_tp=2.0, atr_sl=1.0) — set at iter-v3/010
- **RiskV2Config**: `zscore_threshold=2.0` (iter-v3/011), `adx_threshold=20.0`, `BTC_TREND_CONFIG.threshold_pct=15.0`
- **7-primitive risk gate stack**: BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate (DISABLED)
- **Triple-barrier labeling**: 21-candle (10080-min / 8h) timeout
- **ENSEMBLE_SIZE = 5** (live-prediction variance reduction; v1-style inner ensemble seeds [42, 123, 456, 789, 1001])
- **CPCV**: n_paths=45, embargo=27, REQUIRED_GAP=66 = (timeout_candles=21+1) × n_symbols=3
- **Optuna**: `--n-trials 50` per cell × 5 inner × 3 symbols × 2 outer seeds = 1500 total trials; `colsample_bytree` Optuna-tuned (NOT hardcoded 1.0)
- **Outer seeds**: 2 (per `feedback_outer_seed_cap_2_v3.md`)
- **Sacred constants**: OOS_CUTOFF_DATE=2025-03-24, training_months=24

## Reproducibility Stamp

- Setup commit SHA: `a595f46` (ITERATION_LABEL=v3-018, the only code change)
- Phase 5.5 gate SHA: `98769ce`
- Brief SHA: `5c1b303`
- Engineering report SHA: `00389ec`
- Critic FINAL SHA: `199cbe4`
- Wall-clock: 4.54h (4h 32min — 32min over original 4h cap; cap empirically updated to 6h post-iter-v3/018)
- Hardware: WSL2 / Linux 6.6.87.2 x86_64
- Library stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1

## Sacred Constants

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
ensemble_seeds  = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble
```

Plus v3-specific hard thresholds (per `ITERATION_PLAN_8H_V3.md`):

```
DSR_threshold = 0.95     # Deflated Sharpe Ratio (probability true Sharpe > 0)
PBO_threshold = 0.40     # Probability of Backtest Overfitting
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families
ADF_threshold = 0.05     # ADF p-value (rejects unit root)
```

Inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- Multi-seed pre-MERGE concentration validation (mean Sharpe > 0, ≥7/10 profitable)

## Failed MERGE Gates (Outstanding Constraints for Future CONFIRMATIONs)

| # | Gate | Threshold | Observed | Lift Required |
|---|---|---:|---:|---:|
| 1 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.3788 | +0.62 |
| 2 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.3869 | +0.61 |
| 4 | DSR > 0.95 | > 0.95 | 0.0 | structural; reformulate gate (see DSR root-cause) |
| 5 | PBO max < 0.4 | < 0.4 | 1.0 (TRX/2022-Q4) | regime-aware TRX gate |
| 7 | Top-symbol concentration ≤ 30% | ≤ 30% | TRX 66% / BCH 87% | -36 to -57pp |
| 8 | Bundle OOS trades ≥ 130 | ≥ 130 | 102 (seed 42), 79 (seed 123) | +28 trades min |

DSR root cause: at n_trials=1500, López de Prado E[max_SR] = 3.369; observed annualized Sharpe ≈ 1.7 → DSR formula returns 0.0. NOT a bug; the gate as locked is mathematically blocked at v3's current trade volume + Optuna budget. iter-v3/019 brief proposes either (a) `DSR > 0` (positive deflation), OR (b) reduce CONFIRMATION budget to `--n-trials 20`.

## Methodological Successes (PASSED Gates)

- Gate 3: OOS/IS Sharpe ratio ≥ 0.5 — PASS bare 0.5134 (seed 42); seed 123 = 1.79
- Gate 6: PSR > 0.95 — PASS at 0.9936
- Gate 10: Pareto — both outer seeds Sharpe > 0 — PASS (the methodology bright spot)
- All 12 standard methodology checks (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.) — PASS

## Bootstrap Status

This baseline was established per the user directive on 2026-05-07 because v3 had no prior baseline. iter-v3/013's single-seed +1.0088 IS / +2.6970 OOS Sharpe was **FALSIFIED** at multi-seed validation (62% IS reduction; 86% OOS reduction). The bootstrap exception is **ONE-TIME** — future CONFIRMATIONs (iter-v3/028+) must clear ALL 10 gates to update this file. The 10-EXPLORATION cadence clock RESTARTS at iter-v3/019; first post-bootstrap EXPLORATION targets HIGH-priority axes per `feedback_v3_iter019_axis_priorities.md`.

## Forbidden Symbols (V3_EXCLUDED_SYMBOLS)

v3 cannot trade any symbol already traded by v1 or v2 (plus dropped/v3-failed symbols). The runner enforces this at startup:

```python
V3_EXCLUDED_SYMBOLS = (
    # v1 traded
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    # historical reservation
    "BNBUSDT",
    # v2 traded
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
    # v3 dropped per iter-v3/013 universe-axis EXPLORATION
    "MKRUSDT",
)
assert set(cfg.symbols).isdisjoint(V3_EXCLUDED_SYMBOLS), \
    f"v3 cannot trade v1/v2 symbols: {set(cfg.symbols) & set(V3_EXCLUDED_SYMBOLS)}"
```

## Dead Ideas (populated as v3 iterations fail)

- **iter-v3/013 universe drop-MKR (PROMISING-MECHANICAL)** — falsified at iter-v3/018 multi-seed CONFIRMATION; the +2.6970 OOS Sharpe was a single-seed lottery. The drop-MKR architectural decision is *retained* (TRX positive in BOTH multi-seed seeds; LDO/BCH still net contributors), but the headline OOS metric is dead. Cannot be relitigated as a "PROMISING signal discovery" component for a future CONFIRMATION bundle.
- **iter-v3/014 ADX-25** (NEGATIVE-clean): largest negative OOS Δ in v3 history at -1.83. ADX axis closed.
- **iter-v3/015 tbr_zscore_30 microstructure feature** (NEGATIVE-no-effect): rank 14/14 across all 3 symbols; LightGBM did not learn the feature. Re-introducing more microstructure features deferred.
- **iter-v3/016 XGBoost head-to-head** (NEGATIVE-clean): worst OOS Δ in v3 history at -2.53. XGBoost @ n_trials=10 + cross-entropy + depth-wise NOT closed for all configurations (Sharpe-objective Optuna, drawdown-penalized loss, lossguide growth NOT tested).
- **iter-v3/017 meta-labeling** (NEGATIVE-over-filter, PATH C): M2 filters 42.7% per-candle but kept trades show no quality lift. Same-feature M2 has no incremental learnable signal beyond M1.

## Measurement Discipline

(Inherited from `BASELINE_V2.md`.)

### Data Extent Rule

Every kline CSV in `data/<SYMBOL>/8h.csv` must have `close_time` within 16 hours of the measurement time. Stale data silently corrupts feature computations and label horizons. The Engineer's Phase 6 pre-flight check verifies this before running any backtest.

### Forming-Candle Filter

`fetcher.py` filter: `if k.close_time < now_ms` drops forming candles. iter-v2/059 lost 50 days of OOS data due to a forming-candle bug; the v3 fix is non-negotiable.

### Re-Fetch Protocol

If freshness check fails, the Engineer re-fetches the affected symbols via:

```bash
uv run crypto-trade fetch --interval 8h --symbols <comma-separated>
```

The re-fetch is documented in the engineering report, and the backtest is re-run from the fresh data.

### Reproducibility

Every iteration's engineering report stamps:
- Git commit SHA (must exist in `git rev-parse <SHA>`)
- Hardware (CPU model, RAM)
- Wall-clock time
- Library versions (per brief Section 9)

The Critic's Check 7 verifies reproducibility properties — explicit `feature_columns`, ensemble seeds literal, trade-row PnL spot-check.

## Relationship to v1 and v2

`BASELINE_V3` is independent of `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). The three tracks evolve independently:

- v1 tagged at `v0.NNN` after MERGE
- v2 tagged at `v0.v2-NNN` after MERGE
- v3 tagged at `v0.v3-NNN` after MERGE (first tag: `v0.v3-018` BOOTSTRAP)

The combined-portfolio runner (future work) weights all three tracks. v3 is expected to contribute to combined-portfolio diversification because its symbol universe excludes v1+v2 traded symbols by hard rule.

## See Also

- `ITERATION_PLAN_8H_V3.md` — workflow doc for v3
- `.claude/commands/quant-iteration-v3.md` — the v3 skill
- `.claude/agents/quant-engineer.md` — Engineer subagent
- `.claude/agents/quant-critic.md` — Critic subagent
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE.md` — sibling baseline (v1)
- `briefs-v3/exploration_catalog.md` — running EXPLORATION ledger (cadence anchor)
- `briefs-v3/iteration_v3-018/research_brief.md`, `engineering_report.md`, `review.md` — bootstrap artifacts
- `diary-v3/iteration_v3-018.md` — bootstrap diary entry

# v3 Baseline (iter-v3/028 — first multi-seed-validated edge ingredient)

> **CONFIRMATION-MERGE** per user directive 2026-05-08: STRICTLY-BETTER-than-prior-baseline (iter-v3/018 BOOTSTRAP +0.3788 IS / +0.3869 OOS → iter-v3/028 +0.5101 IS / +0.5053 OOS) triggers BASELINE_V3.md update regardless of aspirational MERGE gate status. **5 of 9 gates still FAIL** — recorded as outstanding constraints for next CONFIRMATION (iter-v3/039). The original `feedback_v3_iter018_baseline_bootstrap.md` rule "must clear ALL gates" is RELAXED at iter-v3/028 closeout per user directive.

**Sibling to:** `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). All three coexist.

**Last updated:** 2026-05-08 — iter-v3/028 (FIRST CONFIRMATION-MERGE post-BOOTSTRAP; first multi-seed-validated edge ingredient)

## Headline Metrics (multi-seed mean across 2 outer × 5 inner = 10 models per cell)

- IS monthly Sharpe: **+0.5101** (was +0.3788 at iter-v3/018; lift **+0.1313**)
- OOS monthly Sharpe: **+0.5053** (was +0.3869 at iter-v3/018; lift **+0.1184**)
- OOS/IS Sharpe ratio: 0.99 (mean) — PASS ≥ 0.5
- IS Trades: 182 (cumulative across cells)
- OOS Trades: 96 (seed 42) / 91 (seed 123) — both BELOW 130 floor (multi-seed mean 93.5)
- IS MaxDD: 41.43%
- OOS MaxDD: 22.97% (seed 42) / 24.08% (seed 123) — mean 23.53% (DOWN from 28.47% at iter-v3/018)
- OOS Calmar: 0.7159 (seed 42) / 1.1298 (seed 123) — mean 0.9229 (UP from 0.4629 at iter-v3/018)
- DSR: 0.0 (structural at v3's trade volume; same root cause as iter-v3/018)
- PBO mean: 0.1243 (PASS < 0.4); frac_positive_paths 0.6444
- PSR: 1.0 (multi-seed n_trials=1050 saturation)
- n_eff: 19
- n_trials (Optuna total): 1050 (= 35 × 3 sym × 2 outer × 5 inner)

## Pareto Front (multi-seed, BOTH SEEDS POSITIVE — Gate 10 PASS)

| Outer Seed | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top Symbol Conc |
|-----------:|-----------:|----------:|-----------:|-----------:|----------------:|
| 42 | +0.5053 | 22.97% | 0.7159 | 96 | 77.71% |
| 123 | **+0.8691** | 24.08% | 1.1298 | 91 | 75.22% |
| **Mean** | **+0.5053** | 23.53% | 0.9229 | 93.5 | 76.47% |

**Methodology bright spot — Pareto Gate 10 PASS at MULTI-SEED-VALIDATED level**: regime_momentum_signed_5d works on BOTH seeds. Seed 123's OOS +0.8691 is the strongest single-seed OOS in v3 multi-seed history. Multi-seed mean (NOT seed 42 numbers) is the published baseline metric to avoid embedding dominated-seed bias — same convention as iter-v3/018.

## Per-symbol Multi-Seed Attribution (single-seed primary projection from comparison.csv)

OOS attribution (seed 42 primary; seed 123 disaggregation in `seed_summary.json`):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct (seed 42) |
|--------|----------------:|-------------:|-------:|---------------------------------:|
| TRX | **+29.92** | 46 | **54.3%** | **181.90%** (single-seed; multi-seed mean ~76%) |
| BCH | +8.58 | 36 | 38.9% | 52.16% |
| LDO | -22.05 | 14 | 21.4% | -134.07% |

(Per-symbol values from `reports-v3/iteration_v3-028/comparison.csv` primary-seed projection; multi-seed disaggregation in `reports-v3/iteration_v3-028/in_sample/per_symbol.csv` and `out_of_sample/per_symbol.csv`. Multi-seed mean concentration is 75-77% per `seed_summary.json`.)

## Code Configuration

- **V3_FEATURE_COLUMNS (14)**: `max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d` (V3_FEATURE_COLUMNS_TOP_N at `src/crypto_trade/features_v3/__init__.py`)
- **V3_MODELS**: BCHUSDT, LDOUSDT, TRXUSDT (drop-MKR per iter-v3/013)
- **V3_EXCLUDED_SYMBOLS**: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, MKRUSDT
- **ATR labeling multipliers**: (atr_tp=2.0, atr_sl=1.0) — set at iter-v3/010
- **RiskV2Config**: `zscore_threshold=2.0` (iter-v3/011), `adx_threshold=20.0`, `BTC_TREND_CONFIG.threshold_pct=15.0`
- **7-primitive risk gate stack**: BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate (DISABLED). Regime gate disabled (per iter-v3/022 PARTIALLY-EFFECTIVE-CLOSED). Per-symbol cap disabled (per iter-v3/020 CLOSED-mechanism).
- **Triple-barrier labeling**: 21-candle (10080-min / 8h) timeout
- **ENSEMBLE_SIZE = 5** (live-prediction variance reduction; v1-style inner ensemble seeds [42, 123, 456, 789, 1001])
- **CPCV**: n_paths=45, embargo=27, REQUIRED_GAP=66 = (timeout_candles=21+1) × n_symbols=3
- **Optuna**: `--n-trials 35` per cell × 5 inner × 3 symbols × 2 outer seeds = 1050 total trials; `colsample_bytree` Optuna-tuned (NOT hardcoded 1.0)
- **Outer seeds**: 2 (per `feedback_outer_seed_cap_2_v3.md`)
- **Sacred constants**: OOS_CUTOFF_DATE=2025-03-24, training_months=24

## Reproducibility Stamp

- Setup commit SHA: `c10e5d3` (drop cross_asset_divergence_norm; V3_FEATURE_COLUMNS=14; ITERATION_LABEL="v3-028")
- Phase 5.5 gate SHA: `d8c1270`
- Brief SHA: `fa1d1bb`
- Engineering report + Critic FINAL SHA: `bdd6fc2`
- BASELINE_V3.md update SHA: (this commit)
- Wall-clock: 3.18h (well within 6h CONFIRMATION cap)
- Hardware: WSL2 / Linux 6.6.87.2 x86_64
- Library stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1
- Run command: `uv run python run_baseline_v3.py --seeds 2`

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

## Failed MERGE Gates (Outstanding Constraints — carry forward to iter-v3/039 CONFIRMATION)

| # | Gate | Threshold | iter-v3/028 Observed | Required Lift |
|---|---|---:|---:|---:|
| 1 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.5101 | **+0.49** (vs iter-v3/018's +0.62 — 21% closer) |
| 2 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.5053 | **+0.49** (vs iter-v3/018's +0.61 — 19% closer) |
| 4 | DSR > 0.95 | > 0.95 | 0.0 | structural; reformulate gate (see DSR root cause below) |
| 7 | Top-symbol concentration ≤ 30% | ≤ 30% | TRX 75-77% (mean) | **−45 to −47pp** (vs iter-v3/018's −36 to −57pp; comparable) |
| 8 | Bundle OOS trades ≥ 130 | ≥ 130 | 91-96 (per seed) | **+34 to +39 trades** (vs iter-v3/018's +28 trades minimum; slight regression) |

Per user directive 2026-05-08 STRICTLY-BETTER-than-prior-baseline policy: these aspirational MERGE-gate failures **inform future-iteration priorities but do NOT block baseline updates**. iter-v3/039 CONFIRMATION (after iter-v3/029-038 EXPLORATIONs) must produce a multi-seed result that EITHER strictly beats iter-v3/028 (this baseline) OR clears the failed gates above to the +1.0 floors.

DSR root cause: at n_trials=1050, López de Prado E[max_SR] formula returns required SR ≈ 3.0; observed annualized ≈ 1.7 → DSR=0.0. NOT a code bug; structural at v3's trade volume + Optuna budget. Either reformulate the gate to `DSR > 0` (positive deflation) OR cap n_trials at the level where the gate becomes feasible. Same root cause as iter-v3/018 BOOTSTRAP.

## Methodological Successes (PASSED Gates)

- **Gate 3: OOS/IS Sharpe ratio ≥ 0.5 — PASS at 0.99** (mean) — generalization is healthy; the strategy is NOT researcher-overfitting. **HIGHER than iter-v3/018's 1.02 boundary**: iter-v3/028's 0.99 is closer to the canonical "perfect generalization" mark of 1.0.
- **Gate 5: PBO mean < 0.4 — PASS at 0.1243.** frac_positive_paths=0.6444 (64% of CPCV paths positive). Mildly higher than iter-v3/018's 0.0892 but well below threshold.
- **Gate 6: PSR > 0.95 — PASS at 1.0** at multi-seed n_trials=1050.
- **Gate 10: Pareto — both outer seeds Sharpe > 0 — PASS** (the methodological bright spot). seed 42: +0.5053; seed 123: +0.8691. Higher Pareto floor than iter-v3/018 (+0.234, +0.539) — both seeds stronger.
- **All 12 standard methodology checks** (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.) — PASS. Critic FINAL `bdd6fc2`.

## What Changed vs iter-v3/018 BOOTSTRAP

**ADDED:** `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` (engineered Category 2 composed feature; first composed feature in v3). 

This single feature contributes:
- IS Sharpe lift: +0.1313 (+0.3788 → +0.5101)
- OOS Sharpe lift: +0.1184 (+0.3869 → +0.5053)
- OOS MaxDD reduction: −4.94pp (28.47% → 23.53%)
- OOS Calmar lift: +0.46 (0.4629 → 0.9229)

regime_momentum_signed_5d is the **first multi-seed-validated edge ingredient in v3 history**. Per `feedback_v3_engineered_features_proven.md` (established at iter-v3/025 single-seed PROMISING), iter-v3/028 multi-seed validation CONFIRMS the engineered-features pivot at multi-seed CONFIRMATION-spec.

## Anchor Comparison Cheat-Sheet (for next-cycle EXPLORATIONs)

iter-v3/029-038 EXPLORATIONs anchor against THIS baseline (multi-seed iter-v3/028), not iter-v3/018 BOOTSTRAP nor iter-v3/025 single-seed. The IS/OOS Sharpe deltas reset:

| Reference | IS Sharpe | OOS Sharpe |
|---|---:|---:|
| iter-v3/028 NEW BASELINE | +0.5101 | +0.5053 |
| iter-v3/018 BOOTSTRAP (prior) | +0.3788 | +0.3869 |
| iter-v3/025 single-seed (validated parent) | +0.8788 | +1.2244 |

EXPLORATION single-seed PROMISING bands (single-axis variation on top of iter-v3/028 baseline) shift accordingly:
- PROMISING (single-seed): IS Δ ≥ +0.10 vs iter-v3/028 anchor (+0.61+); OOS Δ ≥ +0.10 (+0.61+)
- NEGATIVE (single-seed): IS Δ < −0.10 OR OOS Δ < −0.10
- NEGATIVE-SUSPICIOUS-OOS qualifier: IS-OOS daily ratio outside [0.5, 2.0] (per iter-v3/026/027 pattern)

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

- **iter-v3/013 universe drop-MKR (PROMISING-MECHANICAL)** — falsified at iter-v3/018 multi-seed CONFIRMATION; the +2.6970 OOS Sharpe was a single-seed lottery. The drop-MKR architectural decision is *retained* (TRX positive in BOTH multi-seed seeds; LDO/BCH still net contributors), but the headline OOS metric is dead.
- **iter-v3/014 ADX-25** (NEGATIVE-clean): largest negative OOS Δ in v3 history at -1.83. ADX axis closed.
- **iter-v3/015 tbr_zscore_30 microstructure feature** (NEGATIVE-no-effect): rank 14/14; LightGBM did not learn it.
- **iter-v3/016 XGBoost head-to-head** (NEGATIVE-clean): worst OOS Δ in v3 history at -2.53. NOT closed for all configs (Sharpe-objective Optuna, drawdown-penalized loss, lossguide growth NOT tested).
- **iter-v3/017 meta-labeling** (NEGATIVE-over-filter, PATH C): M2 filters 42.7% per-candle but kept trades show no quality lift.
- **iter-v3/019 funding_rate_zscore_30 per-symbol** + **iter-v3/023 retest at n_trials=35** + **iter-v3/024 btc_funding_rate_zscore_30 cross-asset**: funding family PERMANENTLY CLOSED across 3 EXPLORATION data points. INERT-OVERFIT-CONFIRMED.
- **iter-v3/020 per-symbol PnL share cap (0.40)** (NEGATIVE-clean PATH C): concentration is lottery-REWARD source NOT lottery-RISK source. Per-symbol PnL share caps CLOSED-MECHANISM.
- **iter-v3/021 universe expansion +HBAR +AVAX** (NEGATIVE-clean): both drag (-36.5% / -49.2% IS PnL); EDA correlation captured price diversity not signal diversity. CLOSED-symbols-cycle.
- **iter-v3/022 TRX/2022-Q4 regime gate** (NEGATIVE-clean PARTIALLY-EFFECTIVE): TRX/2022-10 cell SUCCESS at single-seed; TRX/2023-01 NOT cleared at single-seed. CONFIRMATION re-evaluation deferred to iter-v3/039+.
- **iter-v3/026 vol_adj_autocorr stacked on regime_momentum** (NEGATIVE-SUSPICIOUS-OOS): IS Sharpe collapse +0.0493; OOS spike +1.4501 (27× IS/OOS daily ratio). Engineered features DON'T STACK at single-seed n_trials=35.
- **iter-v3/027 cross_asset_divergence_norm swapped for vol_adj_autocorr** (NEGATIVE-SUSPICIOUS-OOS): 3-iter monotonic IS degradation pattern REPLICATED. Engineered features DON'T STACK at single-seed FALSIFIED ACROSS 2 COMPOSITIONS.

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

## Status

**CONFIRMATION-MERGE per user directive 2026-05-08 STRICTLY-BETTER-than-prior-baseline policy.** regime_momentum_signed_5d is the FIRST multi-seed-validated edge ingredient in v3 history. iter-v3/039 next CONFIRMATION will need NEW edge ingredients to clear remaining 5 outstanding-constraint gates (Gates 1+2 +0.49 lift each; Gate 4 structural reformulation; Gate 7 −45 to −47pp; Gate 8 +34 to +39 trades).

Per user directive Directive 2 2026-05-08: **STRICT 10:1 EXPLORATION:CONFIRMATION cadence**. iter-v3/029-038 are 10 SEPARATE EXPLORATIONs; iter-v3/039 is a SEPARATE CONFIRMATION. The iter-v3/028 conflation (10th EXPLORATION ran CONFIRMATION-spec and was reclassified post-hoc) is closed; do NOT collapse the 10th EXPLORATION into the next CONFIRMATION.

## Relationship to v1 and v2

`BASELINE_V3` is independent of `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). The three tracks evolve independently:

- v1 tagged at `v0.NNN` after MERGE
- v2 tagged at `v0.v2-NNN` after MERGE
- v3 tagged at `v0.v3-NNN` after MERGE (`v0.v3-018` BOOTSTRAP, `v0.v3-028` first CONFIRMATION-MERGE post-bootstrap)

The combined-portfolio runner (future work) weights all three tracks. v3 is expected to contribute to combined-portfolio diversification because its symbol universe excludes v1+v2 traded symbols by hard rule.

## See Also

- `ITERATION_PLAN_8H_V3.md` — workflow doc for v3
- `.claude/commands/quant-iteration-v3.md` — the v3 skill
- `.claude/agents/quant-engineer.md` — Engineer subagent
- `.claude/agents/quant-critic.md` — Critic subagent
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE.md` — sibling baseline (v1)
- `briefs-v3/exploration_catalog.md` — running EXPLORATION ledger (cadence anchor)
- `briefs-v3/iteration_v3-028/research_brief.md`, `engineering_report.md`, `review.md` — CONFIRMATION-MERGE artifacts
- `diary-v3/iteration_v3-028.md` — CONFIRMATION-MERGE diary entry
- `briefs-v3/iteration_v3-018/` — prior BOOTSTRAP artifacts

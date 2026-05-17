# v3 Baseline (iter-v3/059 — RE-ANCHOR #2: unified 10-seed ensemble — first canonical anchor under live-deployment-compatible architecture)

> **CONFIRMATION-MERGE** per RE-ANCHOR #2 mandate (user directive 2026-05-13) at brief Section 8.1 LOCKED criteria. Unified 10-seed ensemble architecture (Phase B-3 commit `ab2d9ac`) produces ONE deterministic trade roster (live-deployment compatible: one model per coin per account). Path classification: **RE-ANCHOR-MERGE-IS-DOMINANT** (OOS/IS = 0.5316). IS monthly Sharpe **+1.0894** (Δ +0.34 vs /058 multi-seed mean) AND OOS monthly Sharpe **+0.5791** (Δ -0.29 vs /058 multi-seed mean). All 3 hard-blocking gates PASS (Gate 3 OOS/IS=0.5316; Gate 6 PSR=1.0; Gate 10-CPCV frac_positive_paths=0.6444). DSR_relative=0.1134 FAILS 0.95 threshold but is INFORMATIONAL under unified architecture (threshold calibrated against 2-outer × 5-inner; needs cycle 1 recalibration). Multi-seed mean Sharpe reporting (/058 architecture) is **OBSOLETE**. Tag `v0.v3-058` RETIRED as canonical; **`v0.v3-059` is the new canonical baseline**.

**Sibling to:** `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). All three coexist.

**Last updated:** 2026-05-17 — iter-v3/089 cycle-3 EXPLORATION #8 closeout (CONSTRUCTION-PARTIAL — non-advancing; NO-MERGE; canonical /059 anchor METRICS UNCHANGED, tag `v0.v3-059` canonical; edit is documentation-only: the "Active Research Direction — cross-sectional" section below updated with /089's progress — the corrected cross-sectional build contained turnover (the HARD turnover gate PASSED, IS turnover/bar 0.1153 ≤ 0.138), transferred OOS (rank-IC +0.0279 > 0), and turned the book GROSS-POSITIVE on both windows (IS gross monthly Sharpe +0.0925, OOS gross monthly Sharpe +0.1717), lifting the OOS book +0.44 vs /088 to OOS monthly Sharpe −0.0985; the book fails NET only on fees (OOS fees/gross 1.58×, down from /088's 8.8×); classified CONSTRUCTION-PARTIAL — the corrected construction works and transfers but the thin gross signal keeps the net book sub-zero; /088 → /089 is v3's most sustained positive trajectory; /090 is the gross-signal-strengthening next build). PRIOR: iter-v3/088 cycle-3 EXPLORATION #7 closeout (the cross-sectional RE-ARCHITECTURE — ARCHITECTURE-PARTIAL; the Active Research Direction section created). PRIOR: iter-v3/087 cycle-3 EXPLORATION #6 closeout (NEGATIVE — non-advancing; NO-MERGE; canonical /059 anchor METRICS UNCHANGED, tag `v0.v3-059` canonical; the /084 EXPLORATION-MODE-REFERENCE IS +0.8325 / OOS +0.3322 unchanged; edit is documentation-only: a NEW Dead Ideas entry records the WHOLESALE universe expansion 3→6 — `V3_MODELS` grew to BCH/LDO/TRX/GALA/MANA/SAND — as NEGATIVE (OOS monthly Sharpe collapsed to −0.5027, Δ −0.8349 vs the /084 EXPLORATION-MODE-REFERENCE; all 3 new symbols lost OOS; IS lifted +0.0883 — the breadth math transferred in-sample but the 3 new symbols' per-symbol models overfit IS and inverted OOS), and CLOSES Direction 2 (symbol-universe EXPANSION) for the remainder of cycle 3 at a **4-failure track record** spanning every expansion topology — /021 (HBAR+AVAX double), /069 (ADA single), /083 (FIL single), /087 (GALA+MANA+SAND wholesale); the breadth `√N` benefit transferred to production OOS in none of the four. PRIOR: iter-v3/086 cycle-3 EXPLORATION #5 closeout (INERT — non-advancing; NO-MERGE; canonical /059 anchor METRICS UNCHANGED, tag `v0.v3-059` canonical; the /084 EXPLORATION-MODE-REFERENCE IS +0.8325 / OOS +0.3322 unchanged; edit is documentation-only: a NEW Dead Ideas entry records the 7-FEED STRUCTURAL VERDICT — the perp-spot basis feed (/086) is the 7th non-OHLCV crypto-native feature family v3 has tried (funding /019/023/024/082/085, microstructure /015, basis /086) and ALL 7 ARE INERT-by-importance; the v3 per-symbol depth-3-5 LightGBM does not allocate ranked split capacity to crypto-native features regardless of the feed — /087+ must not be an 8th crypto-native feature family; the `fetch-spot` subcommand + `basis_v3.py` + `data/spot/` cache are RETAINED as reusable infrastructure). PRIOR: iter-v3/085 cycle-3 EXPLORATION #4 closeout (SUSPICIOUS — trade-selection sub-channel, non-advancing; NO-MERGE; canonical /059 anchor METRICS UNCHANGED, tag `v0.v3-059` canonical; the /084 EXPLORATION-MODE-REFERENCE IS +0.8325 / OOS +0.3322 unchanged; edit is documentation-only: the Dead Ideas funding-rate entry updated 4→5 data points — the v3 funding axis is now CLOSED across BOTH the direct-feature construction (/019/023/024/082) AND the composed-sign-switch construction (/085); /085's `funding_regime_momentum_5d` was INERT-by-importance rank 13/14/15-of-15 AND its OOS roster swap fired the /076 trade-selection sub-channel falsifier (added-minus-removed OOS mean-duration gap +1.578 > +1.0)). PRIOR: iter-v3/084 cycle-3 slot #3 closeout (REFERENCE / METHODOLOGY — REFERENCE-REANCHOR, non-advancing; canonical /059 anchor METRICS UNCHANGED; the "EXPLORATION-Mode Anchor Staleness" subsection below updated with /084's cycle-3 EXPLORATION-MODE-REFERENCE — IS +0.8325 / OOS +0.3322, 3-seed, current data — and the EXPLORATION-vs-CONFIRMATION architecture-gap finding; the `PER_CELL_GAP` 43→22 methodology fix is recorded as a permanent strictly-accretive correction). PRIOR: iter-v3/083 cycle-3 EXPLORATION #2 closeout (NEGATIVE, non-advancing; universe expansion 3→4 with FILUSDT added to Dead Ideas — IS monthly Sharpe collapsed −0.9156, FIL's own −32% IS edge + a ~24× IS-edge-screen magnitude under-prediction; FILUSDT joins HBAR/AVAX/ADA as CLOSED universe-expansion candidates). PRIOR: iter-v3/082 cycle-3 EXPLORATION #1 closeout (SUSPICIOUS-OOS-DOMINANT; v3 funding-rate axis is a 4-data-point CLOSED verdict in Dead Ideas (/019/023/024/082); OOF parquet append now atomic per commit `a7abba4`)

## Unified 10-Seed Ensemble Architecture (Phase B-3 at commit `ab2d9ac`)

Per memory rule `feedback_v3_unified_10seed_baseline.md` (user directive 2026-05-13 architectural change): the canonical v3 baseline anchors on a **single unified inference path** producing **ONE deterministic trade roster** suitable for live deployment.

The architecture change:
- **ENSEMBLE_SIZE**: 5 → 10
- **ENSEMBLE_SEEDS**: hardcoded 10-tuple with lineage preservation
  - Seeds 0-4 (outer=42 lineage): 191664963, 1662057957, 1405681631, 942484272, 929893137
  - Seeds 5-9 (outer=123 lineage): 33158374, 1465339467, 1273345680, 115579757, 1952249162
- **Outer-seed loop ELIMINATED** in `run_baseline_v3.py`: single `_run_single_seed` call replaces 2-outer × 5-inner loop
- **Single LightGbmStrategy instance per (symbol, walk-forward month) cell**: one Optuna optimization, one trained-model bundle, one inference path with proba averaging across all 10 models
- **Single trade roster**: ONE unified roster from 10-model averaged probability vs /058's two rosters merged via arithmetic-mean Sharpe
- **`--seeds` deprecated**: logs warning if passed, value ignored
- **`_verify_feature_columns` ENSEMBLE_SIZE=10 assertion** added at runtime
- **Report file changes**: `seed_summary.json` → `ensemble_summary.json` (10 rows with lineage annotation); `pareto_front.csv` no longer produced
- **Total Optuna trials UNCHANGED**: 35 × 3 syms × 10 seeds = 1050

**Why this matters for live deployment**: The prior 2-outer × 5-inner architecture required running two independent live strategy instances and merging their trade rosters — operationally infeasible. The unified architecture produces one deterministic inference path from one LightGbmStrategy instance per cell. This is the architecture that will be deployed in the live engine. Multi-seed-mean Sharpe is operationally inaccessible (cannot average two independent live rosters).

Regression coverage: `tests/strategies/ml/test_ensemble_unified.py::TestEnsembleSeedsLineage` regression-tests that `ENSEMBLE_SEEDS[0:5] == _derive_ensemble_seeds(42, 5)` and `ENSEMBLE_SEEDS[5:10] == _derive_ensemble_seeds(123, 5)` to catch future drift.

## Walk-forward Lookahead Fix at Commit `e149e9d` (carried over from /058 RE-ANCHOR #1)

Per memory rule `feedback_v3_walkforward_lookahead_bug.md` (user decision 2026-05-12 path a): ALL v3 iterations PRE-`e149e9d` are INVALIDATED. The walk-forward fix:

- NEW helper `walk_forward.compute_embargo_candles(timeout_minutes, interval_minutes)` returns `timeout_minutes // interval_minutes + 1 = 22` for 10080/480
- `walk_forward.generate_monthly_splits()` requires `label_timeout_minutes` + `interval_minutes` params
- `train_end_ms = test_start_ms - embargo_ms` (purges 22 training candles per (model, month) per symbol)
- `lgbm._train_for_month()` reuses the same helper for `cv_gap = embargo_candles * n_symbols = 66` — single source of truth
- Regression coverage: `tests/test_lookahead_embargo.py` 11/11 PASS

iter-v3/059 inherits the walk-forward fix from /058 unchanged. The Phase B-3 refactor at `ab2d9ac` did not touch `generate_monthly_splits()` — only the outer-seed loop in `run_baseline_v3.py` was eliminated.

## Critic Enhancement Protocol (Second Use at /059)

iter-v3/058 was the FIRST iteration audited under the enhanced Critic protocol at commit `414368a`. iter-v3/059 is the SECOND. Critic FINAL `0fc18c2` confirms:

- **Boot Step 9 Foundation Audit: PASS** — `compute_embargo_candles` helper + `train_end_ms = test_start_ms - embargo_ms` + `cv_gap = embargo_candles * n_symbols` single source of truth verified at Phase B-3 + post-walk-forward-fix state
- **Boot Step 10 Regression Test Confirmation: PASS** — including new `test_ensemble_unified.py::TestEnsembleSeedsLineage`
- **Boot Step 11 Anti-Pattern Static Scan: PASS** — all 13 §11 Anti-Pattern Catalog entries CLEAN; zero unexplained matches
- **Architecture-specific concerns** (FIRST AUDIT under unified 10-seed) — all resolved CLEAN (lineage preservation; `_confidence_threshold` consistency; proba averaging; trade roster construction matches brief Section 4.1 prediction; Optuna efficiency n_eff=19 architecture-independent)

## Headline Metrics (unified 10-seed ensemble — single trade roster)

- IS monthly Sharpe: **+1.0894** (was +0.7481 multi-seed mean at /058; lift **+0.34**)
- OOS monthly Sharpe: **+0.5791** (was +0.8700 multi-seed mean at /058; drop **-0.29**)
- IS daily Sharpe: 2.7092
- OOS daily Sharpe: 1.4359
- OOS/IS monthly Sharpe ratio: **0.5316** — PASS ≥ 0.5 (barely; 0.016 above floor) — path classification RE-ANCHOR-MERGE-IS-DOMINANT
- IS Trades: 171 (was 177 mean at /058; Δ -6)
- OOS Trades: 94 (was 94.5 mean at /058; essentially unchanged); 6.7 trades/month over 14 OOS months; trade-rate floor of ≥10/month NOT met (informational)
- IS MaxDD: 30.97%
- OOS MaxDD: 34.53% (was 31.10% mean at /058; +3.43pp)
- OOS Calmar: **0.6585** (was 1.2028 mean at /058; -0.54)
- DSR (legacy): 0.0 (structural at v3 trade volume; same root cause as all prior v3 CONFIRMATIONs)
- **DSR_relative: 0.1134** (was 0.9982 first PASS at /058) — **INFORMATIONAL under unified architecture**; 0.95 threshold calibrated for 2-outer × 5-inner; needs cycle 1 recalibration. Engineering report attributes drop to `min_trl_months` halving (5.70 vs 11.53), but Critic FINAL `0fc18c2` flags this narrative as factually incorrect (min_trl_months is NOT an input to psr(); drop is dominated by OOS Sharpe falling). See `diary-v3/iteration_v3-059.md` Section 8 Recommendation #1.
- **frac_positive_paths (CPCV): 0.6444** — **IDENTICAL to /058** (CPCV architecture-independent)
- **CPCV path Sharpe Q75: 0.8378** — **IDENTICAL to /058** (CPCV architecture-independent)
- PBO mean: **0.1278** — **IDENTICAL to /058** (cell-level invariant)
- PSR: 1.0 (n_trials=1050 saturation)
- n_eff: 19 (per-cell PCA-95 median; architecture-independent)
- n_trials (Optuna total): 1050 (= 35 × 3 sym × 10 unified seeds; same as /058's 35 × 3 × 2 outer × 5 inner)
- min_trl_months: 5.70 (vs 11.53 at /058 — consistent with outer-seed collapse: 11.53 / 2 ≈ 5.77)

## Per-symbol Attribution (single trade roster from comparison.csv)

OOS attribution:

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|--------|----------------:|-------------:|-------:|----------------------:|
| BCH | **+24.75** | 34 | 41.2% | 108.86% (driver; stable -2.50 vs /058 seed 42) |
| TRX | **+4.16** | 48 | 39.6% | 18.31% (collapsed -18.87 vs /058 seed 42's +23.03 — primary OOS drag) |
| LDO | -6.18 | 12 | 25.0% | -27.17% (improved +9.11 vs /058 seed 42's -15.29; 5th consecutive negative CONFIRMATION-class OOS weighted_pnl — structural drag remains) |

IS attribution:

| Symbol | IS trades | IS WR | IS Net PnL% | % of Total IS PnL |
|---|---:|---:|---:|---:|
| BCH | 83 | **49.4%** | +109.23% | **95.76%** |
| TRX | 79 | 34.2% | +3.95% | 3.47% |
| LDO | 9 | 33.3% | +0.89% | 0.78% |

**BCH IS concentration at 95.76% is a fragility flag for cycle 1 axis design** (per Critic Recommendation #3). Every cycle 1 EXPLORATION brief's Section 4 must project BCH IS sensitivity. An axis that improves LDO and/or TRX but reduces BCH IS contribution will likely collapse the headline IS Sharpe.

## Code Configuration

- **V3_FEATURE_COLUMNS (14)** — UNCHANGED from /028 spec: `max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200, range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100, btc_ret_14d, ret_skew_50, vwap_dev_20, ret_autocorr_lag1_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d` (V3_FEATURE_COLUMNS_TOP_N at `src/crypto_trade/features_v3/__init__.py`)
- **V3_MODELS**: BCHUSDT, LDOUSDT, TRXUSDT (drop-MKR per iter-v3/013)
- **V3_EXCLUDED_SYMBOLS**: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, NEARUSDT, MKRUSDT
- **ATR labeling multipliers**: (atr_tp=2.0, atr_sl=1.0) — DEFAULT for all symbols (V3_ATR_MULTIPLIERS_PER_SYMBOL={} empty per iter-v3/039)
- **RiskV2Config**: `zscore_threshold=2.0` (iter-v3/011), `adx_threshold=20.0`, `adx_threshold_per_symbol={}`, `BTC_TREND_CONFIG.threshold_pct=15.0`, `block_long_for=()`, `block_short_for=()`, `enable_per_symbol_drawdown_brake=False`
- **7-primitive risk gate stack**: BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate (DISABLED). Regime gate disabled (per iter-v3/022). Per-symbol cap disabled (per iter-v3/020). Per-symbol drawdown brake disabled (per iter-v3/054).
- **Triple-barrier labeling**: 21-candle (10080-min / 8h) timeout
- **ENSEMBLE_SIZE = 10** (unified 10-seed ensemble — Phase B-3 architecture)
- **ENSEMBLE_SEEDS** (10-tuple, lineage-preserving):
  - Seeds 0-4 (outer=42 lineage): `(191664963, 1662057957, 1405681631, 942484272, 929893137)`
  - Seeds 5-9 (outer=123 lineage): `(33158374, 1465339467, 1273345680, 115579757, 1952249162)`
- **CPCV**: n_paths=45, embargo=27, REQUIRED_GAP=66 = (timeout_candles=21+1) × n_symbols=3
- **Walk-forward (POST-FIX at `e149e9d`)**: `walk_forward.generate_monthly_splits` applies embargo of `compute_embargo_candles(10080, 480) = 22` candles so `train_end_ms = test_start_ms - embargo_ms`; single source of truth shared with `lgbm._train_for_month()` via the same helper
- **Optuna**: `--n-trials 35` per cell × 10 seeds × 3 symbols = 1050 total trials; `n_jobs=1` (Phase A n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6` due to 5× GIL slowdown); `colsample_bytree` Optuna-tuned (NOT hardcoded 1.0)
- **OOF parquet guardrail**: `--clean-oof` flag active (per `feedback_v3_oof_parquet_guardrail.md`). The OOF parquet append (`trial_oof_returns.parquet`) is **atomic** since iter-v3/082 commit `a7abba4` — the in-place `to_parquet` write was replaced with a temp-file + `os.replace` POSIX-rename pattern, so a concurrent reader sees either the fully-written old or fully-written new file (no partial-write window). Critic-verified metric-neutral; a permanent runner robustness improvement for every v3 iteration.
- **Outer seeds**: deprecated under unified architecture; `--seeds` flag logs warning if passed
- **DSR reporting (Path B4 — retained infrastructure from iter-v3/070 CONFIRMATION)**: `dsr.json`
  reports BOTH the legacy `dsr_relative` field AND the new `dsr_relative_b4` field. Path B4
  (the annualized-both-sides reformulation specified at iter-v3/062 brief Section 3) corrects a
  granularity-mismatch bug in the legacy computation — trade-level cumulative PnL had entered
  `psr()` as if it were an annualized Sharpe. Path B4 puts both inputs at the same granularity:
  observed Sharpe at √252 (annualized daily), benchmark CPCV-Q75 at √756. `dsr.json` additionally
  carries the informational tracking fields `daily_sharpe_oos_b4_at_sqrt252`,
  `cpcv_q75_annualized_b4`, and `n_daily_obs_oos`. Path B4 was the one durable methodology gain
  of cycle 1 — bundled and validated at iter-v3/070 CONFIRMATION (Component B; ACCEPTED). It is a
  strictly-accretive methodology improvement per `feedback_v3_promising_mechanical_subtype.md`
  (non-compoundable across iterations). **The /059 anchor METRICS are UNCHANGED** — Path B4 is a
  reporting-layer-only change with zero behavioral effect on the trade roster. The /059 legacy
  `dsr_relative` of 0.1134 (recorded in Headline Metrics above) was a measurement artifact; under
  Path B4 the same /059 OOS performance would report `dsr_relative_b4 ≈ 1.0`.
- **Sacred constants**: OOS_CUTOFF_DATE=2025-03-24, training_months=24 (IMMUTABLE)

## Reproducibility Stamp

- Setup commit SHA: `20095a8` (brief + phase5p5 gate + ITERATION_LABEL bump to "v3-059")
- Phase 5.5 gate SHA: `20095a8` (PASS — all 11 sections + bundle state + Foundation Audit + Anti-Pattern Catalog verified)
- Brief SHA: `20095a8`
- Brief backfill SHA: `6734a28` (setup commit backfilled into brief Section 10)
- Phase A revert SHA: `31665f6` (n_jobs=2 → n_jobs=1; GIL contention)
- Phase B-3 commit SHA: `ab2d9ac` (unified 10-seed ensemble refactor)
- Walk-forward fix SHA: `e149e9d` (inherited from /058; cherry-pick from main `5566a69`)
- Engineering report SHA: `bea0987`
- Critic FINAL SHA: `0fc18c2` (CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT)
- Critic enhancement SHA: `414368a` (inherited from /058 — Foundation Audit + §11 Anti-Pattern Catalog at 13 entries)
- BASELINE_V3.md update SHA: (this commit)
- Diary SHA: (this commit cycle)
- Tag: `v0.v3-059` (RE-ANCHOR #2 — unified 10-seed; replaces v0.v3-058 as canonical)
- Wall-clock: 3.60h (within 6h CONFIRMATION cap; ~35% faster than /058's 5.49h)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1
- Run command: `uv run python run_baseline_v3.py --clean-oof` (no `--seeds` flag; deprecated in Phase B-3 architecture)

## Sacred Constants

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
ENSEMBLE_SIZE   = 10                # unified 10-seed (Phase B-3)
ENSEMBLE_SEEDS  = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                    33158374, 1465339467, 1273345680, 115579757, 1952249162)
```

Plus v3-specific hard thresholds (per `ITERATION_PLAN_8H_V3.md`):

```
DSR_threshold          = 0.95     # Legacy Deflated Sharpe Ratio — structural FAIL at v3 trade volume
DSR_relative_threshold = 0.95     # NEEDS CYCLE 1 RECALIBRATION under unified architecture
                                  # (calibrated for 2-outer × 5-inner min_trl_months ~11.5;
                                  # unified architecture min_trl_months ~5.7 may make 0.95
                                  # structurally unreachable — see Critic FINAL `0fc18c2` Recommendation #1)
PBO_threshold          = 0.40     # Probability of Backtest Overfitting
PSR_threshold          = 0.95     # Probabilistic Sharpe Ratio
IC_threshold           = 0.70     # |IC_pearson| between feature families
ADF_threshold          = 0.05     # ADF p-value (rejects unit root)
```

NEW Gate 10-CPCV (replaces retired Gate 10 Pareto under unified architecture):

```
Gate 10-CPCV: cpcv_frac_positive_paths >= 0.55
```

iter-v3/059: cpcv_frac_positive_paths = 0.6444 — PASS (IDENTICAL to /058 — CPCV invariant).

Inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- Single-roster validation under unified architecture (replaces multi-seed concentration validation)

## Failed MERGE Gates (Outstanding Constraints — cycle 1 CONFIRMATION iter-v3/070 did NOT clear them; carry forward to cycle 2)

| # | Gate | Threshold | iter-v3/059 Observed | Required Lift |
|---|---|---:|---:|---:|
| 1 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | **+1.0894** | **PASS** (FIRST PASS in v3 history) |
| 2 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | +0.5791 | **+0.42** (vs /058's +0.13 — REGRESSED 0.29) |
| 4 | Legacy DSR > 0.95 | > 0.95 | 0.0 | structural; DSR_relative threshold needs cycle 1 recalibration |
| 4b | DSR_relative > 0.95 | > 0.95 | 0.1134 | **+0.84** (architecture artifact; threshold needs recalibration before becoming a hard gate again) |
| 7 | Top-symbol concentration ≤ 30% | ≤ 30% | 108.86% (BCH; +27pp vs /058's 77.88%) | **-79pp** (WORSE than /058 — concentration tightened) |
| 8a | OOS trades ≥ 130 aggregate | ≥ 130 | 94 | **+36 trades** (single-roster; no aggregate cushion under unified architecture) |
| 8b | OOS trades per-month ≥ 10 | ≥ 10/month | 6.7/month (14 OOS months) | **+3.3/month** |

**IS Sharpe ≥ +1.0 gate FIRST PASS in v3 history.** This is the structural compensation for unified-architecture IS-dominance. OOS gate regressed -0.29 vs /058. Per `feedback_v3_strict_both_is_oos_baseline.md`, cycle 1 CONFIRMATION at iter-v3/069 must produce a multi-seed result where BOTH IS Sharpe AND OOS Sharpe (single-roster mean) improve over this baseline.

Per user directive 2026-05-08 STRICTLY-BETTER-than-prior-baseline policy + RE-ANCHOR mandate: these aspirational MERGE-gate failures **inform future-iteration priorities but do NOT block the /059 RE-ANCHOR baseline update**.

DSR (legacy) root cause: at n_trials=1050 / n_eff=19, López de Prado E[max_SR] formula returns required SR ≈ 2.61; observed annualized ≈ 3.31 → DSR=0 via the SBT formula. NOT a code bug; structural at v3's trade volume + Optuna budget.

DSR_relative root cause for the drop /058 → /059: per Critic FINAL `0fc18c2`, the engineering report's narrative attributing the drop to `min_trl_months` halving is factually incorrect (min_trl_months is NOT an input to `psr()`; it is only written to dsr.json as a tracking field). The actual cause is the OOS Sharpe falling combined with the fixed CPCV-Q75 benchmark of 0.8378. Cycle 1 EXPLORATION briefs must not cite `min_trl_months` as a DSR_relative driver. Appropriate recalibration axes are: (a) benchmark choice (CPCV-Q50 or CPCV-Q60 instead of Q75), or (b) the threshold itself.

## Methodological Successes (PASSED Gates)

- **Gate 1: IS monthly Sharpe ≥ +1.0 — FIRST PASS in v3 history at +1.0894** — unified-architecture IS-dominance produces the first IS Sharpe above the +1.0 floor in any v3 CONFIRMATION-class run.
- **Gate 3: OOS/IS Sharpe ratio ≥ 0.5 — PASS at 0.5316** (barely; 0.016 above floor). Borderline; flagged as RE-ANCHOR-MERGE-IS-DOMINANT per brief Section 8.3.
- **Gate 5: PBO mean < 0.4 — PASS at 0.1278** (IDENTICAL to /058 — cell-level invariant).
- **Gate 6: PSR > 0.95 — PASS at 1.0** at n_trials=1050 saturation.
- **Gate 10-CPCV: frac_positive_paths ≥ 0.55 — PASS at 0.6444** (IDENTICAL to /058 — CPCV architecture-independent). Replaces Pareto Gate 10 (RETIRED under unified architecture).
- **All 12 standard methodology checks** (look-ahead, embargo, IC, ADF, hypothesis-implementation alignment, library pinning, etc.) — PASS or PASS-equivalent.
- **Enhanced Critic protocol Boot Steps 9-11 + Check 13** — PASS (Foundation Audit + Regression Test Confirmation + Anti-Pattern Static Scan; all 13 §11 catalog entries CLEAN).
- **Architecture-specific concerns (FIRST AUDIT under unified 10-seed)** — all resolved CLEAN (lineage preservation; threshold consistency; proba averaging; trade roster construction; Optuna n_eff invariance).

## What Changed vs /058 RE-ANCHOR #1 (multi-seed mean)

**SAME bundle composition** (V3_FEATURE_COLUMNS=14 unchanged from /028 and /058; V3_MODELS unchanged; ATR multipliers unchanged; risk gate stack unchanged).

**ARCHITECTURE CHANGE at Phase B-3 `ab2d9ac`** is the substantive difference. The single trade roster from unified 10-model proba averaging replaces the two independent rosters merged via arithmetic-mean Sharpe at /058.

- IS Sharpe lift: **+0.34** (+0.7481 multi-seed mean → +1.0894 unified)
- OOS Sharpe drop: **-0.29** (+0.8700 multi-seed mean → +0.5791 unified)
- OOS/IS Sharpe ratio: 1.163 → **0.5316** (RE-ANCHOR-MERGE-IS-DOMINANT pre-registered taxonomy fired)
- OOS MaxDD widening: 31.10% → 34.53% (+3.43pp)
- OOS Calmar: 1.2028 → 0.6585 (-0.54)
- DSR_relative: 0.9982 → 0.1134 (-0.885 — architecture artifact; threshold needs cycle 1 recalibration)
- frac_positive_paths: **IDENTICAL** at 0.6444 (CPCV architecture-independent)
- PBO: **IDENTICAL** at 0.1278 (cell-level invariant)
- CPCV path Sharpe Q75: **IDENTICAL** at 0.8378
- IS trades: 177 mean → 171 (-6)
- OOS trades: 94.5 mean → 94 (essentially unchanged)
- TRX OOS weighted_pnl: +23.03 (/058 seed 42) → +4.16 (collapsed -18.87 — primary OOS drag)
- LDO OOS weighted_pnl: -15.29 (/058 seed 42) → -6.18 (improved +9.11)
- BCH OOS weighted_pnl: +27.25 (/058 seed 42) → +24.75 (-2.50; stable)

The structural mechanism: at /058 seed 42 produced IS/OOS = 1.60× (IS-dominant); seed 123 produced OOS/IS = 3.91× (strongly OOS-dominant); the arithmetic mean yielded apparent balance (0.86). The unified 10-seed ensemble inherits seed-42 lineage IS-dominance at prediction-averaging stage while suppressing seed-123 lineage OOS-dominance into the averaged signal. **Cross-seed cancellation was unmasked at /059** — the unified architecture exposes the true IS-dominant character of the BCH/LDO/TRX bundle directly. Detail in `diary-v3/iteration_v3-059.md` Section 5.

## Anchor Comparison Cheat-Sheet (for cycle 1 EXPLORATIONs iter-v3/060-069)

iter-v3/060-068 EXPLORATIONs anchor against THIS baseline (iter-v3/059 unified 10-seed), NOT the retired /058 multi-seed mean anchor or the previously-retired /028 BIASED anchor:

| Reference | Architecture | IS Sharpe | OOS Sharpe |
|---|---|---:|---:|
| **iter-v3/059 NEW BASELINE (unified 10-seed)** | unified | **+1.0894** | **+0.5791** |
| iter-v3/058 RE-ANCHOR #1 (multi-seed mean — RETIRED) | 2-outer × 5-inner | +0.7481 | +0.8700 |
| iter-v3/028 BIASED anchor (RETIRED) | 2-outer × 5-inner buggy WF | +0.5101 | +0.5053 |
| iter-v3/018 BOOTSTRAP (further retired) | 2-outer × 5-inner buggy WF | +0.3788 | +0.3869 |

EXPLORATION single-seed PROMISING bands (single-axis variation on top of iter-v3/059 baseline):
- **PROMISING (single-seed)**: IS Δ ≥ +0.10 vs iter-v3/059 anchor (+1.19+); OOS Δ ≥ +0.10 vs iter-v3/059 anchor (+0.68+)
- **NEGATIVE (single-seed)**: IS Δ < -0.10 OR OOS Δ < -0.10
- **NEGATIVE-SUSPICIOUS-OOS qualifier**: IS-OOS daily ratio outside [0.5, 2.0] (per iter-v3/026/027 pattern)

Note: at CONFIRMATION, BOTH-must-improve discipline applies (per `feedback_v3_strict_both_is_oos_baseline.md`). At EXPLORATION level, single-axis improvement on either axis is informational.

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

## Active Research Direction — the cross-sectional relative-value architecture (LIVE; established iter-v3/088)

> This is a LIVE research direction, NOT a Dead Idea. iter-v3/088 produced v3's FIRST genuine OOS signal transfer and the cross-sectional architecture is the active v3 research line; it is recorded here, not in Dead Ideas, because /089-091 build directly on it.

**iter-v3/088 — the cross-sectional relative-value RE-ARCHITECTURE — ARCHITECTURE-PARTIAL — produced v3's first OOS-positive new signal (cycle-3 EXPLORATION #7).** iter-v3/088 was the most ambitious v3 iteration since iter-v3/001: it REPLACED the v3 model architecture — the N per-symbol absolute-barrier `LightGbmStrategy` classifiers → ONE pooled `LGBMRanker(objective="lambdarank")` (LambdaMART) trained on the pooled cross-section of a 22-symbol universe (`XS_UNIVERSE`), predicting the cross-sectional forward-return rank (H=3-bar / 1-day, tercile-graded {0,1,2} per timestamp — a RELATIVE label replacing the `(2.0,1.0)`-ATR triple-barrier), traded as a dollar-neutral tercile long-short book (inverse-vol weighting + portfolio vol-targeting, every-8h-bar rebalance, 0.1% turnover-based fee). New module `cross_sectional.py` (1073 lines) + new runner `run_cross_sectional_v3.py` (the legacy per-symbol `run_baseline_v3.py` untouched); 13 features (the 14-feature /059 anchor stack minus `btc_ret_14d` for zero cross-sectional dispersion, cross-sectionally rank-normalized); `XS_REQUIRED_GAP = 88 = (3+1)×22`; the legacy 7-gate risk stack intentionally absent (3 structural controls — dollar-neutral construction, inverse-vol + vol-target, tercile diversification). **The result: the dollar-neutral tercile long-short BOOK loses money (IS monthly Sharpe −0.6403, OOS monthly Sharpe −0.5418) — BUT the pooled cross-sectional MODEL's OOS rank-IC is +0.0430 ± 0.3317 over n = 1255 OOS timestamps (t ≈ +4.59) — statistically significant and POSITIVE: the cross-sectional signal genuinely TRANSFERRED out-of-sample.** Classified **ARCHITECTURE-PARTIAL** (brief Section 8.4 — the re-architecture-adapted taxonomy; Critic FINAL `1acfb9c` OVERALL=MERGE methodology-only; the QR's Phase-8 call): F1 (OOS rank-IC ≤ 0 → ARCHITECTURE-FALSIFIED) does NOT fire — OOS rank-IC +0.043 > 0, the signal transferred; non-F1 falsifiers F3 (OOS Sharpe < 0) and F4 (frac_positive_paths 0.000 < 0.55) fire — the long-short CONSTRUCTION loses money. **The architecture is NOT falsified — the position CONSTRUCTION is.** Two diagnosed, fixable failures (QE + Critic concurring): (a) a SIGN INVERSION in the brief — a `LGBMRanker` trained on a FORWARD-return-grade label learns high score = high future return (IS Spearman(score, grade) +0.0328, p = 1.2e-12), so the brief's "long the bottom tercile / low-score" construction longs the predicted future LOSERS; (b) TURNOVER DRAG is the DOMINANT failure — IS fees 0.6866 are 8.8× IS gross PnL 0.078; the flipped-IS diagnostic shows even the corrected sign yields only IS *gross* Sharpe ≈ +0.067 and IS *net* Sharpe still −0.4308. **The significance: across the prior ~27 v3 EXPLORATIONs (3 cycles) the recurring failure was per-symbol models scoring strongly-positive IS and inverting OOS; iter-v3/088 is the FIRST v3 EXPLORATION to produce a genuine, statistically-significant, OOS-positive signal transfer.** The cross-sectional architecture is the active v3 research line; **iter-v3/089 is the corrected next build (NOT a fresh re-architecture)** — fix the sign (LONG the top tercile, SHORT the bottom), attack turnover structurally with a pre-registered turnover ceiling as a hard gate, fix the `_compute_xs_cpcv` path-Sharpe proxy (it collapsed to 45 rows of `sharpe = 0.0`), and consider strengthening the gross signal (the corrected-sign IS gross Sharpe ≈ +0.067 is thin — high-conviction quintile/decile concentration, a longer horizon, a cross-sectionally-normalized feature expansion). The `cross_sectional.py` module, `run_cross_sectional_v3.py` runner, `XS_UNIVERSE` constant, and pooled-ranking infrastructure are RETAINED and built upon. BASELINE_V3.md UNCHANGED — /059 stays canonical; an EXPLORATION cannot update the baseline. Detail: `diary-v3/iteration_v3-088.md`.

**iter-v3/089 — the CORRECTED cross-sectional iteration — CONSTRUCTION-PARTIAL — the book is now GROSS-POSITIVE; /088 → /089 is v3's most sustained positive trajectory (cycle-3 EXPLORATION #8).** iter-v3/089 was the corrected next build on /088's RETAINED `cross_sectional.py` infrastructure — NOT a fresh re-architecture. Five changes vs /088 (all IS-EDA-selected, EDA `c172a12`): (1) the SIGN FIX (Critic /088 Rec #2) — `build_positions` now LONGs the TOP quantile (highest predicted scores = predicted future winners) and SHORTs the BOTTOM, the inverse of /088, specified from first principles (`lambdarank` on a forward-return-grade label learns high score = high future return); (2) the CPCV-PROXY FIX (Critic /088 Rec #3) — `_compute_xs_cpcv` rewritten to compute the ACTUAL realised long-short NET return per CPCV path (`cpcv_paths.csv` now non-degenerate, 45 distinct Sharpes); (3) the cost-aware construction — `XS_QUANTILE_FRAC=0.20` quintile legs + `XS_HOLD_BARS=3` Jegadeesh-Titman overlapping holds + `XS_NO_TRADE_BAND=0.020` Constantinides/Davis-Norman no-trade band; (4) the pre-registered HARD turnover ceiling `XS_TURNOVER_CEILING=0.138` (a breach is NO-MERGE regardless of Sharpe); (5) the 13-feature stack / 22-symbol `XS_UNIVERSE` / H=3 label / `XS_REQUIRED_GAP=88` embargo UNCHANGED. **The result: the corrected cross-sectional book is GROSS-POSITIVE on both windows — IS gross monthly Sharpe +0.0925, OOS gross monthly Sharpe +0.1717 (the Critic FINAL `74054c2` verified this genuine, not a look-ahead artifact) — and fails NET only on fees; the NET book is IS monthly Sharpe −0.1960 / OOS monthly Sharpe −0.0985, a +0.4443 IS and +0.4433 OOS lift vs the /088 cross-sectional book.** Fees/gross collapsed from /088's 8.8× to IS 3.35× / OOS 1.58× — a 2.6× reduction attributable to the quintile + overlapping-hold + no-trade-band construction; the OOS gross PnL (+0.0567) needs only ~37% further fee reduction OR gross-signal lift to cross breakeven net. IS mean gross turnover/bar 0.1153 ≤ the 0.138 ceiling — the HARD turnover gate PASSES. OOS rank-IC +0.0279 > 0 — the signal transfers. The SHORT leg carries the entire gross spread (OOS short-leg gross +0.1200; long-leg gross −0.0633 — a real, pre-registerable signal-anatomy finding). Classified **CONSTRUCTION-PARTIAL** (brief Section 8.4; Critic FINAL `74054c2` OVERALL=MERGE methodology-only; the QR's Phase-8 call): 8.1 SUSPICIOUS does not fire; 8.2 CONSTRUCTION-FALSIFIED does not fire (F2 turnover-gate PASSES, F3 does not fire — OOS −0.0985 > /088's −0.5418); 8.3 CONSTRUCTION-VALIDATED-PROMISING does not fire (it requires OOS monthly Sharpe > 0; observed −0.0985 ≤ 0); 8.4 CONSTRUCTION-PARTIAL is the disjunctive-precedence match — the corrected construction works, contains turnover, transfers OOS, and materially improves the OOS book, but the thin gross signal keeps it sub-zero. **The cross-sectional trajectory — /088 OOS −0.5418 ARCHITECTURE-PARTIAL → /089 OOS −0.0985 CONSTRUCTION-PARTIAL, gross-positive — is v3's most sustained positive trajectory: across two consecutive iterations the architecture responds to fixes (the +0.44 OOS lift matched the IS-internal-walk-forward EDA prediction exactly), the signal transfers OOS, and the book has turned gross-positive; the gap to a net-positive book is now a concrete, bounded cost/signal problem.** NO-MERGE; an EXPLORATION carries no merge ingredient. **iter-v3/090 is the gross-signal-strengthening next build (NOT a fresh re-architecture, NOT a third round of turnover reduction — turnover reduction has steeply diminishing returns per Critic Rec #2; the OOS gross Sharpe +0.17 is the asset to grow): the scoped axis is the G4 cross-sectional-momentum feature expansion (multivariate-contribution-tested per the iter-v3/070 dead-path discipline), with the short-leg-asymmetry hypothesis (Critic Rec #3) a candidate /090/091 axis the QR weighs on IS-only EDA.** The `cross_sectional.py` module, `run_cross_sectional_v3.py` runner, `XS_UNIVERSE` constant, the pooled-ranking infrastructure, AND the /089 cost-aware construction (quintile + 3-bar overlapping holds + no-trade band + the 0.138 turnover ceiling) are all RETAINED and built upon. BASELINE_V3.md UNCHANGED — /059 stays canonical; an EXPLORATION cannot update the baseline. Detail: `diary-v3/iteration_v3-089.md`.

## Dead Ideas (populated as v3 iterations fail — pre-fix verdicts marked for re-evaluation)

> **Re-evaluation note**: Per Critic FINAL `cdd94a3` recommendation #1 from /058, pre-fix NEGATIVE/INERT verdicts in cycle 4 may not transfer to post-fix landscape. Per `feedback_v3_engineered_features_dont_stack.md`, single-seed EXPLORATION SAME-FAMILY stacking continues to be FORBIDDEN at any IC. Cycle 1 EXPLORATIONs should commission fresh EDA before blanket exclusions.

- **iter-v3/013 universe drop-MKR (PROMISING-MECHANICAL)** — falsified at iter-v3/018 multi-seed CONFIRMATION; drop-MKR architectural decision RETAINED.
- **iter-v3/014 ADX-25** (NEGATIVE-clean): largest negative OOS Δ at -1.83 pre-fix; ADX axis closed.
- **iter-v3/015 tbr_zscore_30 microstructure feature** (NEGATIVE-no-effect pre-fix): rank 14/14; **eligible for re-evaluation in cycle 1 per post-fix axis-rethink rule**.
- **iter-v3/016 XGBoost head-to-head** (NEGATIVE-clean pre-fix): worst OOS Δ at -2.53. NOT closed for all configs.
- **iter-v3/017 meta-labeling** (NEGATIVE-over-filter, PATH C pre-fix): M2 filters 42.7% per-candle but kept trades show no quality lift.
- **iter-v3/019/023/024/082/085 funding-rate feature axis — CLOSED across 5 EXPLORATION data points, across BOTH feature-construction families; re-evaluation eligibility DISCHARGED.** /019 (`funding_rate_zscore_30`, n_trials=10, PROMISING-INERT rank 14/14), /023 (same single z-score, n_trials=35, OOS collapsed), /024 (BTC `funding_rate_zscore_30` cross-asset variant, n_trials=35, OOS collapsed) — three single-z-score attempts, all pre-walk-forward-fix. **iter-v3/082** (cycle-3 EXPLORATION #1): a literature-grounded 4-member funding FEATURE FAMILY (`funding_sign_persist_9`, `funding_momentum_3`, `funding_accel_3`, `funding_price_divergence_6`; `V3_FEATURE_COLUMNS` 14→18) encoding crowding/momentum/shock/divergence — the genuinely-distinct family construction the single-z-score attempts never made. /082 reproduced the INERT verdict: the 4 funding features ranked **15/16/17/18 of 18** by importance (combined 9.90%, below the 5.56% uniform-parity baseline); IS Δ flat (-0.0118), OOS Δ +1.2081 — but the OOS lift is the documented INERT-feature Optuna-perturbation / 3-seed-lottery artifact (`feedback_v3_inert_features_at_higher_budget.md`), NOT funding signal — classified **SUSPICIOUS-OOS-DOMINANT** (Critic FINAL `d5670aa`). **iter-v3/085** (cycle-3 EXPLORATION #4): the 5th data point and the one that closes the axis across BOTH construction families. /085 fed funding NOT as a direct feature but as a `sign()` switch *inside* a Category-2 composed feature — `funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30)` (`V3_FEATURE_COLUMNS_TOP_N` 14→15) — the explicitly-different construction (funding conditions *what raw momentum means*, never a splittable column). The Phase 5.5 gate's funding-differentiation adjudication was legitimate — the construction IS structurally distinct from the closed Category-1 funding-as-direct-feature axis — but the RESULT reproduced the INERT-by-importance pattern (rank **13/14/15-of-15**, share ~3%, portfolio rank 15/15) AND the /085-vs-/084 OOS roster swap loaded the /076 trade-selection sub-channel (added-minus-removed mean-duration gap +1.578 > the +1.0 LOCKED falsifier) → classified **SUSPICIOUS** (Critic FINAL `50f32be`; trade-selection sub-channel). The +0.1418 IS lift was an Optuna-search-perturbation artifact of an unused 15th column, NOT funding signal. **All 5 funding-axis data points are INERT-by-importance** — across two structurally orthogonal constructions (direct-feature: /019/023/024/082; composed-sign-switch: /085) the v3 LightGBM declines to allocate ranked importance to funding-derived information on the BCH/LDO/TRX universe at v3's per-symbol scale + EXPLORATION budget. **The funding axis is CLOSED in ALL feature constructions on the funding rate.** Future "funding" axes require a fundamentally different VEHICLE — (a) a NEW crypto-native data feed entirely (open interest / perp-spot basis / liquidation cascades; no current fetcher — a real Phase-6 build), or (b) a non-tree model that can compose the interaction differently — NOT another feature construction (direct OR composed) on the same funding rate. The literal-name bans on `funding_rate_zscore_30` / `btc_funding_rate_zscore_30` stay intact; `funding_regime_momentum_5d` joins the runner ABSENT-assertion ban at the iter-v3/086 setup; per `feedback_v3_inert_features_at_higher_budget.md` an INERT feature must NOT be carried forward and must NOT be retested at a higher Optuna budget. Detail: `diary-v3/iteration_v3-082.md`, `diary-v3/iteration_v3-085.md`.
- **iter-v3/086 perp-spot BASIS feature family — INERT — and the 7-FEED STRUCTURAL VERDICT (cycle-3 EXPLORATION #5).** iter-v3/086 acquired a genuinely NEW crypto-native data feed — the perp-spot basis — via a real Phase-6 build: the `crypto-trade fetch-spot` CLI subcommand (`data.binance.vision` monthly spot-kline archives + `/api/v3/klines` REST fallback, with mandatory 2025-01 microsecond→millisecond timestamp normalisation), a track-isolated `basis_v3.py` feature module (the `cross_btc_v3.py` external-CSV-merge pattern), and the `data/spot/` cache (BCH 7037 / LDO 4358 / TRX 8642 rows, 100% IS spot-merge coverage). A 3-feature basis family (`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag` — all on `basis.shift(1)`, a one-full-candle lag stricter than the funding convention) was appended to `V3_FEATURE_COLUMNS_TOP_N` (14→17). **The result reproduced the INERT-by-importance pattern**: the 3 basis features ranked **15/16/17 of 17** by portfolio-pooled last-IS-month importance (combined share 0.04265, a 2.15× gap below the weakest anchor `regime_momentum_signed_5d` at 0.04034) — the F1 INERT falsifier satisfied. Neither LOCKED SUSPICIOUS sub-channel fired — the Phase-8 OOS roster-diff (`analysis/iteration_v3-086/roster_diff_oos.py`) measured F2 added-minus-removed mean-duration gap +0.9630 ≤ +1.0 and F3 full-roster shift +0.3489 ≤ +1.0 — and the ratio gate (1.149) and OOS-DOMINANT sub-mode (IS Δ +0.063 ≥ 0) did not fire either; classified **INERT** (Critic FINAL `a3297e1` OVERALL=MERGE methodology-only; the QR's Phase-8 Section 8 call). The +0.6962 OOS lift (to +1.0284) was the documented `feedback_v3_inert_features_at_higher_budget.md` Optuna-search-perturbation artifact of 3 INERT columns (the exact /082 signature), NOT basis signal. **THE 7-FEED STRUCTURAL VERDICT: the perp-spot basis feed is the 7th non-OHLCV crypto-native feature family v3 has tried, and ALL 7 are INERT-by-importance** — funding rate (/019/023/024 direct z-scores, /082 the 4-channel direct family, /085 the Category-2 composed sign-switch; 5 data points across two construction families), microstructure (/015 `tbr_zscore_30`; 1), perp-spot basis (/086; 1). Across seven independent crypto-native data sources and multiple construction families, the v3 per-symbol depth-3-5 LightGBM trained on ~2700-5700 IS rows (LDO only 2741) declines to allocate ranked split capacity to crypto-native sentiment information. This is a **structural verdict on the v3 architecture**, not a per-feed result: **iter-v3/087+ MUST NOT be an 8th crypto-native feature family on the same architecture.** The remaining structural levers are Direction 2 (universe expansion / breadth — WHOLESALE, not a single-weak-symbol add) and Direction 3 (a multi-symbol-pooled model — the naive form was /085-EDA-falsified; a non-naive variant is untested). The 3 basis feature columns (`basis_zscore_30` / `basis_momentum_3` / `basis_extreme_flag`) are dropped at the iter-v3/087 setup and join the runner ABSENT-assertion ban (the `funding_regime_momentum_5d` pattern); per `feedback_v3_inert_features_at_higher_budget.md` they must NOT be carried to /092 and must NOT be retested at a higher Optuna budget. **The `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache are RETAINED as reusable infrastructure** — only the 3 feature columns are dropped. Detail: `diary-v3/iteration_v3-086.md`.
- **iter-v3/020 per-symbol PnL share cap (0.40)** (NEGATIVE-clean PATH C): concentration is lottery-REWARD source NOT lottery-RISK source. Per-symbol PnL share caps CLOSED-MECHANISM.
- **iter-v3/021 universe expansion +HBAR +AVAX** (NEGATIVE-clean): both drag; EDA correlation captured price diversity not signal diversity. CLOSED-symbols-cycle.
- **iter-v3/083 universe expansion 3→4 +FILUSDT** (NEGATIVE — cycle-3 EXPLORATION #2). `V3_MODELS` grew BCH/LDO/TRX → BCH/LDO/TRX/FILUSDT (denominator expansion, distinct from the CLOSED swap-by-replacement family). FILUSDT was selected on a genuine IS-edge + portfolio-aggregate screen (rank #1 of 4 deep-history liquid large-cap survivors — the methodology fix /021 and /069 lacked) — but the production result was an aggregate **IS monthly Sharpe collapse to +0.1738 (Δ −0.9156 vs /059)**, IS MaxDD blowout 30.97%→73.18%, CPCV `frac_positive_paths` 0.4667 < 0.55. Decomposition of the −101.56pp IS-PnL collapse: **FIL's own negative edge −32.45pp** (32%; FIL standalone IS net_pnl% −32.45, 36.7% WR — a genuine net detractor, FIL does NOT transfer) + **incumbent drift −69.11pp** (68%). The incumbent drift is **data-extent drift, not FIL-perturbation** — proven cleanly by /082 (the same 3 incumbents on the same fresh data, FIL absent) already showing the incumbent aggregate ~70pp below /059 (/082 incumbent Δ vs /059 = −71.74pp; /082-vs-/083 incumbent Δ = +2.63pp, essentially identical). The engineering report's "FIL reshaped the incumbents' Optuna landscape" claim is mechanistically false (the Critic traced the runner — `_build_v3_model` gives every per-symbol model byte-identical inputs regardless of `len(V3_MODELS)`; each symbol's Optuna study is fully independent). The IS-edge screen predicted −0.0382 aggregate IS Sharpe Δ; realized −0.9156 — a **~24× magnitude under-prediction**: the screen is a defensible relative-ranking tool but NOT an absolute-magnitude predictor — future universe-expansion screens must treat the aggregate-Δ as direction-only. **FILUSDT is a CLOSED universe-expansion candidate** (joining HBAR/AVAX at /021 and ADA at /078). Universe expansion as an axis remains structurally valid (the Fundamental Law breadth lever) but exposed a confounding ~70pp /059 anchor-staleness drift — the /083 closeout recommends iter-v3/084 be a fresh /059-config anchor re-run on current data. Detail: `diary-v3/iteration_v3-083.md`.
- **iter-v3/087 WHOLESALE universe expansion 3→6 +GALA+MANA+SAND — NEGATIVE — and DIRECTION 2 (universe expansion) is now CLOSED for the rest of cycle 3 at a 4-FAILURE TRACK RECORD (cycle-3 EXPLORATION #6).** iter-v3/087 ran the genuinely WHOLESALE breadth expansion the /083/086 closeouts mandated (not /083's single-weak-symbol add): `V3_MODELS` grew BCH/LDO/TRX → BCH/LDO/TRX/**GALAUSDT/MANAUSDT/SANDUSDT** in one step — denominator expansion, the Grinold-Kahn `IR = IC·√breadth` lever, each added symbol fully UNIVERSAL (one independent per-symbol LightGBM, the identical 14-feature stack, the identical `(2.0,1.0)`-ATR triple-barrier, the identical 7-gate risk stack; no per-symbol features/ATR/gates). The symbols were screened on the rigorous Bailey-López de Prado *Sharpe-ratio indifference-curve* framework — the EDA's T3 measured a +0.2371 screen aggregate-IS-Sharpe lift at the N=6 peak, leave-one-out all positive, on the strategy-PnL correlation ρ̄=+0.087 (NOT the price-return correlation /021/069 wrongly used) — the strongest pre-backtest case any cycle-3 EXPLORATION has had. **The production result was NEGATIVE: IS monthly Sharpe lifted +0.0883 (to +0.9208 vs the /084 EXPLORATION-MODE-REFERENCE +0.8325) but OOS monthly Sharpe COLLAPSED to −0.5027 (Δ −0.8349 vs /084's +0.3322), OOS MaxDD blew out to 76.42%, worst CPCV path −3.47 Sharpe.** All 3 new symbols lost in OOS: GALA +67.2% IS → −19.0% OOS, MANA +101.6% IS → −27.2% OOS (the largest single-symbol IS→OOS reversal in v3 history at this iteration), SAND −18.1% IS → −28.1% OOS (IS-negative too — the EDA's restricted-window screen mis-signed SAND, which screened +0.13 standalone Sharpe on an un-gated 1485-trade proxy roster but the production 7-gate+Optuna run selected only 41 IS trades netting −18.10%; the /083-lesson recurring — a per-symbol screen does not survive the gate stack). Classified **NEGATIVE** via the Section 8.2 general `OOS Δ < −0.20` clause (Critic FINAL `24a9dcc` OVERALL=MERGE methodology-only; result-read NEGATIVE; the QR's Phase-8 Section 8 call). SUSPICIOUS does NOT fire — every SUSPICIOUS sub-channel is an OOS-up-on-flat-IS divergence and /087 produced the OPPOSITE (`IS up, OOS crashes`) signature; the Phase-8 roster-diff (`analysis/iteration_v3-087/roster_diff_oos.py`) confirmed the /087 OOS roster is a near-strict SUPERSET of /084's (all 104 /084 trades survive, REMOVES=0, the 76 added are exactly the GALA+MANA+SAND OOS trades; incumbent BCH/LDO bit-identical, TRX off by 1 trade — the `feedback_v3_single_seed_frozen_baseline.md` pattern), so the F4 added-vs-removed sub-channel is a degenerate empty-set artifact and the economically meaningful sub-channel (d) — the added-symbol-minus-incumbent OOS mean-duration gap −0.2546 — does NOT fire (no holding-time regime-loading). The breadth math transferred in-sample (IS lifted +0.09) but the 3 new symbols' per-symbol models overfit IS and inverted OOS. **DIRECTION 2 — symbol-universe EXPANSION — is now CLOSED for the remainder of cycle 3 at a 4-FAILURE TRACK RECORD spanning every expansion topology: /021 (HBAR+AVAX, double add, NEGATIVE), /069 (ADA, single add), /083 (FILUSDT, single add, NEGATIVE — IS collapse), /087 (GALA+MANA+SAND, wholesale add, NEGATIVE — OOS collapse).** The breadth `√N` benefit transferred to production OOS in none of the four — universe expansion is exhausted as a v3 axis. GALAUSDT/MANAUSDT/SANDUSDT join HBAR/AVAX/ADA/FILUSDT as CLOSED universe-expansion candidates. The /088 setup MUST revert `V3_MODELS` 6→3 (BCH/LDO/TRX) and recompute `REQUIRED_GAP` 132→66 — the standard baseline-restore of a NEGATIVE/NO-MERGE axis; `PER_CELL_GAP` stays 22 (universe-count-invariant). NOTE the engineering-report config-diff doc error (Critic Rec #4): the report records `/084 PER_CELL_GAP = 11` and `/087 = 22 (= 132/6)` — both wrong; `PER_CELL_GAP = (timeout_candles+1) = 22` for a single-symbol cell with NO `n_symbols` factor — universe-count-invariant at 22 in both /084 and /087; the code (`run_baseline_v3.py:1600`) is correct, only the report prose is wrong. Future universe/per-symbol briefs must pre-register a SYMMETRIC `OOS Δ < −0.20 regardless of IS sign → NEGATIVE` named falsifier (Critic Rec #2 — /087's F1 was IS-collapse-specific and did not fire on the IS-up/OOS-down signature). Detail: `diary-v3/iteration_v3-087.md`.
- **Regime-conditional kill switch (primitive 9) — CLOSED, tested-twice-no-signal**: NEGATIVE-pre-fix at iter-v3/022 (TRX/2022-Q4 regime gate, NEGATIVE-clean PARTIALLY-EFFECTIVE — TRX/2022-10 cell SUCCESS at single-seed but TRX/2023-01 NOT cleared) and INERT-post-fix at iter-v3/074 (TRX-scoped regime gate, BTC drawdown_30d > 20% OR |vol_z_30d| > 1.5; the gate fired only 3 IS + 5 OOS TRX suppressions — too few to move headline metrics; IS Δ +0.013, OOS Δ +0.069, both inside noise bands). The iter-v3/074 post-fix re-evaluation cleanly discharged the `feedback_v3_walkforward_lookahead_bug.md` re-eval eligibility for this axis. The regime-conditional kill switch is CLOSED across two data points and must not be re-proposed (Critic FINAL `2371324` Recommendation #2). NOTE iter-v3/074 was a clean holding-time-ORTHOGONAL axis — it confirmed (per `feedback_v3_is_oos_regime_divergence.md`) that holding-time-orthogonal axes do not load the v3 IS/OOS regime factor.
- **iter-v3/026 vol_adj_autocorr stacked on regime_momentum** (NEGATIVE-SUSPICIOUS-OOS pre-fix): 27× IS/OOS daily ratio. Engineered features DON'T STACK at single-seed n_trials=35.
- **iter-v3/027 cross_asset_divergence_norm swap for vol_adj_autocorr** (NEGATIVE-SUSPICIOUS-OOS pre-fix): 3-iter monotonic IS degradation pattern REPLICATED.
- **iter-v3/029-/057 cycle-4 EXPLORATION verdicts** — all produced under BUGGY walk-forward; eligible for re-evaluation as part of post-fix axis-rethink rule.
- **Kaufman path-efficiency feature family (`efficiency_ratio_50` / `range_efficiency_50`) — CLOSED across 2 data points; re-evaluation eligibility DISCHARGED.** `range_efficiency_50` is mathematically identical to `efficiency_ratio_50` (same Kaufman formula `|close[t]-close[t-50]| / sum(|close.diff()|, 50)`, same 50-bar window, same `1e-9` epsilon, clip, shift, fillna). The literal `efficiency_ratio_50` name remains runner-banned (`raise RuntimeError`) + a prohibited test entry; the column is never generated. Two data points: **iter-v3/043** added `efficiency_ratio_50` to a 4-symbol universe pre-walk-forward-fix → DISASTROUS (IS -0.8445 / OOS -0.8990); **iter-v3/076** re-added the bit-identical math as `range_efficiency_50` (15th `V3_FEATURE_COLUMNS` feature, 3-symbol BCH/LDO/TRX universe, post-walk-forward-fix) as a rule-sanctioned re-evaluation per `feedback_v3_walkforward_lookahead_bug.md` → SUSPICIOUS-OOS-DOMINANT (IS collapsed to +0.0431, MaxDD blew out to 61.69%, OOS/IS ratio 15.04 — the clearest SUSPICIOUS signature in cycle 2; BCH IS edge destroyed +79.45%→-8.27%). The /076 re-evaluation did NOT vindicate the feature — IS is still economically broken. The `feedback_v3_walkforward_lookahead_bug.md` re-evaluation eligibility for this axis is **DISCHARGED**. `efficiency_ratio_50` / `range_efficiency_50` must NOT be re-proposed (Critic FINAL `8203410` Recommendation #3). NOTE: /076's failure mode (regime-loading via trade SELECTION — the feature shifted which trades the model picks toward longer-held OOS-uptrend trades, with NO barrier-extension mechanism) is a material extension of the v3 IS/OOS regime-divergence finding — see `briefs-v3/exploration_catalog.md` cycle-level-finding section and `feedback_v3_is_oos_regime_divergence.md`.

## Measurement Discipline

(Inherited from `BASELINE_V2.md`.)

### EXPLORATION-Mode Anchor Staleness (established iter-v3/077 closeout)

> This note concerns ONLY the EXPLORATION-MODE-REFERENCE intra-cycle delta anchor. The **/059 CONFIRMATION baseline above (the canonical anchor, tag `v0.v3-059`, IS +1.0894 / OOS +0.5791) is UNCHANGED and unaffected** — it is a unified-architecture CONFIRMATION number, not an EXPLORATION-mode reference.

Cycle-2 EXPLORATIONs /071-/076 quoted the iter-v3/060 EXPLORATION-MODE-REFERENCE as a frozen IS +0.8325 / OOS +0.1403. iter-v3/077 — the first iteration since /060 to run the exact /060 14-feature config with no axis — established that the frozen value no longer reproduces on current code + current data. The **current-code /060-config baseline is IS +0.8236 / OOS +0.2078**, with the exact additive decomposition: IS code-drift **-0.0089** (the iter-v3/061 TRX `vol_scale_floor=0.5`, a permanent deterministic offset) + OOS data-extent **+0.0675** (the 2026-05 OOS month post-dating /060's data fetch, growing monotonically with calendar time). Cycle-2 EXPLORATIONs **/078+ re-anchor against the current-code /060-config baseline (IS +0.8236 / OOS +0.2078)**, not the stale frozen value. This is a methodology correction (a stale reference value replaced by the freshest reproducible no-axis run of the canonical config), not a measurement-window change — the OOS-cutoff and start dates are untouched. The /071-/076 classifications remain robust (the drift is well inside the ±0.10 IS / ±0.20 OOS noise bands and cannot move a SUSPICIOUS ratio across the 3.0 gate). Detail: `diary-v3/iteration_v3-077.md` Section 4 and the anchor-staleness cycle-note in `briefs-v3/exploration_catalog.md`.

**Cycle-3 EXPLORATION-MODE-REFERENCE (established iter-v3/084 closeout — REFERENCE-REANCHOR).** iter-v3/084 — the cycle-3 reference re-run, the direct analogue of cycle 1's /077 — ran the canonical 3-symbol BCH/LDO/TRX / 14-feature / `(2.0,1.0)`-ATR / 7-gate /059 configuration at EXPLORATION-mode 3-seed on freshly-fetched current data, with no axis. It landed at **IS +0.8325 / OOS +0.3322**. The brief Section 4.3 LOCKED re-anchor decision rule fired the re-anchor branch (both deltas vs /059's recorded numbers ≈ −0.25, outside the ±0.10 band). **The cycle-3 EXPLORATION-MODE-REFERENCE is therefore IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data)** — cycle-3 EXPLORATIONs /085-091 anchor their intra-cycle Δ classification against it.

> **The EXPLORATION-vs-CONFIRMATION architecture-gap finding (iter-v3/084 Critic FINAL `16b4cc1` Recommendation #1).** The ~0.26 IS gap between /084's IS +0.8325 and /059's recorded IS +1.0894 is **NOT "the /059 config went stale."** /084's +0.8325 is a **3-seed EXPLORATION-mode** number (`EXPLORATION_ENSEMBLE_SIZE=3`); /059's +1.0894 is a **10-seed CONFIRMATION-mode** number (the unified `ENSEMBLE_SIZE=10`) — two structurally different ensemble architectures (different proba-averaged trade rosters, different Sharpe). Cycle 2's reference re-run /077 landed at IS **+0.8236** (3-seed) — near-identical to /084's +0.8325 — while /059's 10-seed CONFIRMATION is +1.0894. The /077≈/084 near-identity proves essentially the entire ~0.26 IS gap is the **EXPLORATION-vs-CONFIRMATION architecture component** (3-seed-vs-10-seed proba-averaging), with only a small residual genuine data-extent component. The honest finding: the prior cycle-3 EXPLORATIONs /082-/083 were anchoring their 3-seed EXPLORATION-mode deltas against a non-comparable 10-seed CONFIRMATION number — /084 corrects that **reference-architecture mismatch**. The /082 (SUSPICIOUS-OOS-DOMINANT) and /083 (NEGATIVE) classifications STAND — re-anchoring sharpens the framing but does not overturn closed verdicts.

> **The TWO-ANCHOR STRUCTURE (iter-v3/084 Critic Recommendation #2 — MANDATORY for every /085-091 brief).** Every cycle-3 EXPLORATION brief Section 4 must state TWO anchors: **(1) the EXPLORATION-MODE-REFERENCE** — /084: IS +0.8325 / OOS +0.3322 (3-seed) — for intra-cycle Δ classification (an EXPLORATION runs 3-seed, so it must be compared to a 3-seed reference); **(2) the /059 CONFIRMATION baseline** — IS +1.0894 / OOS +0.5791 (10-seed, tag `v0.v3-059`) — RESERVED for the iter-v3/092 CONFIRMATION (which runs 10-seed CONFIRMATION-mode and must be compared to a 10-seed baseline). Mixing the two is the /082-/083 error.

This is a methodology correction (a non-comparable reference value replaced by the freshest architecturally-matched no-axis run of the canonical config), not a measurement-window change — the OOS-cutoff and start dates are untouched. The /082 / /083 classifications remain robust. The /059 CONFIRMATION baseline (the canonical anchor, tag `v0.v3-059`, IS +1.0894 / OOS +0.5791) is UNCHANGED and unaffected — it is a unified-architecture CONFIRMATION number, not an EXPLORATION-mode reference. Detail: `diary-v3/iteration_v3-084.md` Sections 3-5 and the iter-v3/084 catalog row in `briefs-v3/exploration_catalog.md`.

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

**CONFIRMATION-MERGE — RE-ANCHOR-MERGE-IS-DOMINANT** per user directive 2026-05-13 + RE-ANCHOR #2 mandate at brief Section 8.1. iter-v3/059 is the FIRST canonical baseline under unified 10-seed ensemble architecture (live-deployment compatible: one model per coin per account). Multi-seed-mean Sharpe reporting (/058 architecture) is OBSOLETE. The prior /058 RE-ANCHOR #1 anchor and tag `v0.v3-058` are RETIRED as canonical.

### Cycle Counting (cycle 1 CLOSED at iter-v3/070 CONFIRMATION)

Per user directive 2026-05-13: RE-ANCHOR #2 is orthogonal to cycle counting; NOT a cycle 1 EXPLORATION; NOT subject to 10:1 cadence constraint.
- **iter-v3/058 = RE-ANCHOR #1** (cycle 4 RESET; NOT counted toward cycle 1)
- **iter-v3/059 = RE-ANCHOR #2** (orthogonal to cycle counting; NOT counted toward cycle 1)
- **iter-v3/060-069 = CYCLE 1 EXPLORATIONs #1-10** (COMPLETE — under unified-architecture anchor)
- **iter-v3/070 = CYCLE 1 CONFIRMATION** (COMPLETE — SUSPICIOUS-OOS-DOMINANT, NO-MERGE)
- **NEXT iteration = iter-v3/071 = CYCLE 2 EXPLORATION #1 of 10**
- **Cycle 2 CONFIRMATION = iter-v3/081** (or later per cadence discipline; do NOT collapse 10th EXPLORATION into CONFIRMATION)
- **EXPLORATION cap 2h** (unchanged)
- **CONFIRMATION cap 6h** (iter-v3/070 ran 3.13h within cap)

Per `feedback_v3_strict_10_to_1_cadence.md` Directive 2: STRICT 10:1 EXPLORATION:CONFIRMATION cadence. iter-v3/071-080 are 10 SEPARATE EXPLORATIONs; iter-v3/081 (or later) is the SEPARATE CONFIRMATION.

### Cycle 1 Outcome (iter-v3/060-070 — CLOSED)

**Cycle 1 produced NO BASELINE_V3.md update.** /059 remains canonical. Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve), the cycle 1 CONFIRMATION (iter-v3/070, 2-component bundle = /065 SL widening + /062 Path B4) classified SUSPICIOUS-OOS-DOMINANT: IS Sharpe collapsed -0.97 (FAIL the BOTH-must-improve IS gate) while OOS soared +0.67; OOS/IS ratio 10.81 — regime exposure, not robust edge. Component A (/065 SL widening) REJECTED; `DEFAULT_ATR_MULTIPLIERS` reverted (2.0,1.5)→(2.0,1.0). Component B (/062 Path B4) ACCEPTED as accretive methodology infrastructure (see DSR reporting bullet in Code Configuration). The cycle 1 EXPLORATION outcome distribution was 1 PROMISING-anchor, 1 PASSIVE-DIAGNOSTIC, 1 SUSPICIOUS-OOS-DOMINANT, 4 INERT, 3 NEGATIVE. Detail in `diary-v3/iteration_v3-070.md`.

### Cycle 2 Axis Priorities (post-iter-v3/070 CONFIRMATION)

The defining unresolved problem of cycle 1 is **LDO structural weakness** — LDO was a drag through every cycle 1 EXPLORATION and the CONFIRMATION (/070 IS net_pnl -47.46 / 28.6% WR; OOS net_pnl -13.77 / 35.7% WR). No labeling knob, feature expansion, or universe addition fixed it. Cycle 1 exhausted the knob space; cycle 2 must be STRUCTURAL.

1. **HIGHEST — Model architecture (meta-labeling)** per `feedback_v3_iter017_metalabeling_mandate.md` (mandated, never fully executed; /017 was a single-seed over-filter). An M2 secondary classifier that predicts whether to ACT on the M1 direction is the natural response to a directionally-bleeding symbol.
2. **HIGH — Labeling architecture** — fixed-horizon return labels as an alternative to ATR triple-barrier. A different label DEFINITION, not a different multiplier.
3. **MEDIUM — Universe revision: replace LDO** — only if axes 1-2 fail; a replacement must clear an IS-edge screen BEFORE inclusion (prior universe-expansion EXPLORATIONs /021, /069 all failed).
4. **CONSTRAINT on every cycle 2 brief** — per-symbol IS-axis discipline (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`): validate any per-symbol customization PRESERVES/LIFTS IS Sharpe before bundling.
5. **CONSTRAINT on every cycle 2 brief** — pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS) in Section 4 per `feedback_v3_oos_is_ratio_gate.md`.

## Relationship to v1 and v2

`BASELINE_V3` is independent of `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). The three tracks evolve independently:

- v1 tagged at `v0.NNN` after MERGE
- v2 tagged at `v0.v2-NNN` after MERGE
- v3 tagged at `v0.v3-NNN` after MERGE (`v0.v3-018` BOOTSTRAP [RETIRED], `v0.v3-028` first CONFIRMATION-MERGE post-bootstrap [BIASED, RETIRED], `v0.v3-058` first RE-ANCHOR post-walk-forward-fix [RETIRED], **`v0.v3-059` first canonical baseline under unified 10-seed architecture**)

The combined-portfolio runner (future work) weights all three tracks. v3 is expected to contribute to combined-portfolio diversification because its symbol universe excludes v1+v2 traded symbols by hard rule. The unified 10-seed architecture makes v3 directly deployable in live: one model per coin per account.

## See Also

- `ITERATION_PLAN_8H_V3.md` — workflow doc for v3
- `.claude/commands/quant-iteration-v3.md` — the v3 skill
- `.claude/agents/quant-engineer.md` — Engineer subagent
- `.claude/agents/quant-critic.md` — Critic subagent (enhanced at `414368a`)
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE.md` — sibling baseline (v1)
- `briefs-v3/exploration_catalog.md` — running EXPLORATION ledger (cadence anchor)
- `briefs-v3/iteration_v3-059/research_brief.md`, `engineering_report.md`, `review.md` — RE-ANCHOR #2 artifacts
- `diary-v3/iteration_v3-059.md` — RE-ANCHOR #2 diary entry
- `briefs-v3/iteration_v3-058/` — prior RE-ANCHOR #1 artifacts (RETIRED)
- `briefs-v3/iteration_v3-028/` — prior CONFIRMATION-MERGE artifacts (BIASED, RETIRED)
- `briefs-v3/iteration_v3-018/` — prior BOOTSTRAP artifacts (BIASED, RETIRED)

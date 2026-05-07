# Iteration v3-018 — Research Brief

**Type**: **CONFIRMATION** — **first true v3 CONFIRMATION** ever (iter-v3/008 aborted at 4h 15min on 2026-05-06; cadence discipline was established AFTER that abort, so iter-v3/008 does not count).
**Track**: v3 (rigor arm) — eighteenth iteration
**Branch**: `iteration-v3/018` (off `iteration-v3/017` head)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # SET BY non-exploration mode (NOT --exploration)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=5)  # 5 inner per outer
outer_seeds      = 2              # set by --seeds 2
n_trials         = 50             # set by --n-trials 50 (default in non-exploration)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0 — full search space
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees multi-seed OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/013-017 briefs / engineering reports / Critic reviews / diaries / `briefs-v3/exploration_catalog.md` / `BASELINE_V3.md` / `feedback_v3_iter018_confirmation_baseline_validation.md` / `feedback_outer_seed_cap_2_v3.md` / `feedback_trade_rate_floor_bundle_level.md` / `feedback_seed_validation.md` / `run_baseline_v3.py` source. **No new IS-only EDA is needed for this CONFIRMATION** because iter-v3/018 validates an EXISTING baseline (iter-v3/013); the prior IS evidence is the iter-v3/013 single-seed run already committed at SHA `e3168f2`. This brief acknowledges the structural difference: EXPLORATION briefs generate fresh IS evidence pre-backtest; this CONFIRMATION inherits and re-tests.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: CONFIRMATION (first true v3 CONFIRMATION ever)
This iteration MAY UPDATE BASELINE_V3.md if all 10 MERGE gates pass.
Wall-clock budget: 4h HARD CAP (CONFIRMATION cadence rule, cannot be renegotiated)
NOT bundle assembly: all 4 PROMISING components ALREADY cumulatively integrated in iter-v3/013 baseline
This is a MULTI-SEED VALIDATION RUN of iter-v3/013 baseline at full CONFIRMATION rigor
Pre-committed: spec is FORCED by feedback_v3_iter018_confirmation_baseline_validation.md (FIRED at iter-v3/017 Critic FINAL SHA `6de26d1`). Cannot be renegotiated post-hoc.
```

**Justification** (from `feedback_v3_iter018_confirmation_baseline_validation.md` and `briefs-v3/exploration_catalog.md` banner): the catalog reached 10/10 EXPLORATIONs at iter-v3/017 with PROMISING-class 4 of 10 (007 features, 010 labeling, 011 zscore, 013 universe) and NEGATIVE-class 6 of 10 (009, 012, 014, 015, 016, 017). All 4 PROMISING components are **already cumulatively integrated in the current iter-v3/013 baseline**: iter-v3/013's `comparison.csv` reflects top-13 V3_FEATURE_COLUMNS + ATR(2.0/1.0) labeling + z-score 2.0 OOD gate + drop-MKR universe (BCH+LDO+TRX). iter-v3/014-017 were all NEGATIVE/NULL (ADX-25, microstructure tbr_zscore_30 INERT, XGBoost worst-OOS-Δ, meta-labeling over-filter). **There is NOTHING NEW TO BUNDLE.** iter-v3/018 = MULTI-SEED VALIDATION RUN of iter-v3/013 baseline at full CONFIRMATION rigor. The spec (`--seeds 2 --n-trials 50`, ENSEMBLE_SIZE=5) is forced by `feedback_v3_iter018_confirmation_baseline_validation.md` and cannot be renegotiated post-hoc.

---

## Section 1 — Hypothesis

iter-v3/013's IS +1.0088 / OOS +2.6970 monthly Sharpe HOLDS under multi-seed cross-validation rigor (5 inner × 2 outer = 10 models per cell, n_trials=50), with all v3 methodology gates passing at non-EXPLORATION thresholds: PBO < 0.4, DSR > 0.95, PSR > 0.95, multi-seed Pareto non-domination, top-symbol concentration ≤ 30%, bundle-level OOS trade count ≥ 130, 10-seed pre-MERGE validation (mean Sharpe > 0, ≥7/10 profitable).

---

## Section 2 — Inherited IS Evidence (no fresh EDA — structural difference from EXPLORATION briefs)

### 2.1 Why no new IS-only analysis script

CONFIRMATION's question is **statistical-validity-of-prior**, not signal-discovery. Per `feedback_qr_uses_is_data.md`, every Phase 5 brief must contain numerical tables produced by a committed analysis script — for CONFIRMATION the "analysis" IS the iter-v3/013 baseline run already committed at SHA `e3168f2`. iter-v3/018's "fresh IS evidence" is the multi-seed re-run itself, generated in Phase 6, not pre-Phase 5. Generating new IS-only analysis pre-backtest would:
- Risk peeking at OOS aggregates from iter-v3/013/017 (already revealed) and using them to calibrate gates that are pre-registered in this brief
- Add no information beyond the iter-v3/013 reports already in `reports-v3/iteration_v3-013/` (committed, reproducible)

**This brief inherits iter-v3/013's IS+OOS metrics as the prior** and pre-registers MERGE/NO-MERGE gates that the multi-seed run must mechanically clear.

### 2.2 Inherited iter-v3/013 baseline (the prior being validated)

**Source**: `reports-v3/iteration_v3-013/comparison.csv` + `dsr.json` (committed at SHA `e3168f2`).

| Metric | iter-v3/013 IS (1-seed) | iter-v3/013 OOS (1-seed) | OOS/IS ratio |
|---|---:|---:|---:|
| **monthly_sharpe** | **+1.0088** | **+2.6970** | 2.6734 |
| daily_sharpe | +2.0171 | +4.5099 | 2.2358 |
| max_drawdown (%) | 20.7707 | 12.4711 | 0.6004 |
| profit_factor | 1.3427 | 1.8108 | 1.3486 |
| win_rate (%) | 34.4498 | 44.7059 | 1.2977 |
| n_trades | 209 | **85** | 0.4067 |
| total_pnl | 78.7956 | 61.8489 | 0.7849 |
| weighted_pnl_total | 78.7956 | 61.8489 | 0.7849 |
| **DSR** | **0.0000** | — | single-seed saturation |
| **PBO** | **0.1075** | — | (cross-cell mean aggregator) |
| **PSR** | **1.0000** | — | single-seed saturation |
| n_trials | 30 | — | (3 symbols × 10 trials/seed × 1 seed = 30) |
| n_effective_trials | 7 | — | (PCA on trial-returns matrix) |

**Per-symbol iter-v3/013 OOS attribution** (`comparison.csv` per_symbol section):

| Symbol | weighted_pnl | n_trades | win_rate (%) | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +17.2073 | 31 | 38.7 | 27.82 |
| **LDOUSDT** | **+40.6020** | **10** | **80.0** | **65.65** |
| TRXUSDT | +4.0396 | 44 | 40.9 | 6.53 |

LDO 65.65% concentration is **above** the 30% per-symbol cap that applies at CONFIRMATION. The iter-v3/013 catalog row pre-committed: "future CONFIRMATION QR must scope ex-LDO basket fragility before bundling." Section 4.2 below predicts how multi-seed averaging may compress LDO concentration; Section 8 specifies the mechanical gate.

iter-v3/017 single-seed (with meta-labeling layer) showed LDO concentration **74.36%** — same lottery flag persisting across architectural variations. This is ADDITIONAL pre-commitment evidence that LDO is concentrated single-seed across two ITERATIONS, NOT just iter-v3/013.

### 2.3 Inherited per-cell PBO + n_eff diagnostics

| Stat | iter-v3/013 single-seed |
|---|---:|
| Cross-cell PBO (mean aggregator) | 0.1075 |
| `pbo_frac_positive_paths` (45 CPCV paths) | 0.6444 |
| `pbo_path_sharpe_q25` | -0.243 |
| `pbo_path_sharpe_q50` | +0.3351 |
| `pbo_path_sharpe_q75` | +0.8378 |
| n_eff (median across cells) | 7 |
| min_trl_months | 69.67 |
| n_high_pbo_cells_99 | **2** (TRX/2025-10, TRX/2025-11; pre-committed max-aggregator usage at CONFIRMATION per iter-v3/013 catalog) |

The cross-cell mean PBO of 0.1075 is **well below** the 0.4 CONFIRMATION threshold. The two TRX/2025-Q4 cells with PBO ≈ 1.00 are pre-committed for max-aggregator scrutiny per `briefs-v3/exploration_catalog.md` iter-v3/013 caveats: future CONFIRMATION QR uses **both** `(1 − mean_pbo)` AND `(1 − max_per_cell_pbo)` aggregators. iter-v3/018 Phase 7 Critic verifies BOTH pass `< 0.4`.

### 2.4 Setup integrity (verified pre-brief at SHA TBD)

```
reports-v3/iteration_v3-013/comparison.csv extant + non-empty   PASS
reports-v3/iteration_v3-013/dsr.json extant + valid JSON         PASS
ITERATION_LABEL currently "v3-017" (will be updated to "v3-018") AS_DOCUMENTED
V3_MODELS at runtime = 3 entries (BCH, LDO, TRX)                 PASS (verified at runner line 108-112)
ENSEMBLE_SIZE constant = 5 in run_baseline_v3.py                  PASS (verified at runner line 86)
_derive_ensemble_seeds(outer_seed, size=5) returns 5 distinct ints PASS (verified at runner line 90-99)
non-exploration code path uses ENSEMBLE_SIZE not 1                PASS (verified at runner line 1371: "ensemble_size_for_run: int = 1 if args.exploration else ENSEMBLE_SIZE")
non-exploration code path uses fast_mode=False (Optuna tunes colsample) PASS (verified at runner line 1372: "fast_mode_for_run: bool = bool(args.exploration)")
default --n-trials = 50                                           PASS (verified at runner line 1324: "default=50")
default --seeds = 1; --seeds 2 invocation produces outer_seeds=2  PASS (verified at runner line 1320 default=1, accepted via int parser)
```

**No code changes needed** to support iter-v3/018's CONFIRMATION-mode invocation. The runner's non-exploration code path already supports the spec out-of-the-box. The only required edits are §3 sub-fixes (cosmetic ITERATION_LABEL bump only).

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX inherited from iter-v3/013)

| Symbol | iter-v3/013 status | iter-v3/018 status |
|---|---|---|
| BCHUSDT | KEEP | **KEEP** |
| LDOUSDT | KEEP | **KEEP** |
| TRXUSDT | KEEP | **KEEP** |

### 3.2 Labeling — UNCHANGED (ATR(2.0/1.0) inherited from iter-v3/010)

| Parameter | iter-v3/013 | iter-v3/018 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap (REQUIRED_GAP) | 66 = (21+1)×3 | **66 (UNCHANGED)** |

### 3.3 Features — UNCHANGED (13 features inherited from iter-v3/009)

`V3_FEATURE_COLUMNS` length = 13. `vwap_dev_50` excluded. `tbr_zscore_30` excluded. The list is identical to iter-v3/013/014/015/016/017 baseline (after iter-v3/015's tbr_zscore_30 reverted).

### 3.4 Risk gates — UNCHANGED (7-primitive stack inherited from iter-v3/012)

| Parameter | iter-v3/013 | iter-v3/018 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | **15.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Multi-seed config — CHANGED (the actual axis of this CONFIRMATION)

| Parameter | iter-v3/013 | iter-v3/018 |
|---|---:|---:|
| Outer seeds | 1 (default) | **2** (per `feedback_outer_seed_cap_2_v3.md`) |
| `ENSEMBLE_SIZE` (inner ensemble) | 1 (forced by --exploration) | **5** (default; non-exploration mode) |
| Models per cell | 1 × 1 = 1 | **2 × 5 = 10** |
| n_trials per cell (Optuna) | 10 (forced by --exploration) | **50** (default; non-exploration mode) |
| `colsample_bytree` Optuna sampling | hardcoded 1.0 | **Optuna-tuned** (per iter-v3/008 colsample A/B research; `fast_mode=False` enables full search space) |
| `--exploration` flag | YES | **NO** (non-exploration mode) |
| ITERATION_LABEL | "v3-017" → "v3-013" baseline metrics | **"v3-018"** |

The multi-seed × full-ensemble × full-Optuna config is the **only axis** varied in iter-v3/018. All other parameters (symbols, labeling, features, gates, risk primitives, walk-forward window, OOS cutoff) are byte-identical to iter-v3/013 baseline.

### 3.6 Sub-fix decomposition — minimal (cosmetic edit + run command)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | Update `ITERATION_LABEL` to `"v3-018"` in `run_baseline_v3.py` line 102 | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-018"' run_baseline_v3.py` exits 0 |
| 2 | Verify `V3_MODELS` is unchanged (3 entries, BCH/LDO/TRX, no MKR) | grep | `python -c "from importlib import import_module; m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 3 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}"` exits 0 |
| 3 | Verify `REQUIRED_GAP == 66` unchanged | grep | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66, REQUIRED_GAP"` exits 0 |
| 4 | Verify `ENSEMBLE_SIZE == 5` constant in non-exploration mode | grep | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert m.ENSEMBLE_SIZE == 5"` exits 0 |
| 5 | Verify `_derive_ensemble_seeds(seed, 5)` returns 5 ints when called with size=5 | unit | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert len(m._derive_ensemble_seeds(42, 5)) == 5"` exits 0 |
| 6 | Verify default `--n-trials == 50` (no --exploration) | grep | `grep -E 'default=50' run_baseline_v3.py` exits 0 |
| 7 | Verify non-exploration code path: `ensemble_size_for_run = ENSEMBLE_SIZE` and `fast_mode_for_run = False` when `args.exploration is False` | grep | `grep -E 'ensemble_size_for_run.*if args.exploration else ENSEMBLE_SIZE' run_baseline_v3.py` exits 0 AND `grep -E 'fast_mode_for_run.*=.*bool\(args.exploration\)' run_baseline_v3.py` exits 0 |
| 8 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 9 | Commit cosmetic ITERATION_LABEL edit | git | `feat(iter-v3/018): ITERATION_LABEL=v3-018 (no other code changes — multi-seed validation of iter-v3/013 baseline)` |
| 10 | Run **without** `--exploration`: `uv run python run_baseline_v3.py --seeds 2 --n-trials 50` | runner | `test -f reports-v3/iteration_v3-018/comparison.csv` |

NO new feature additions. NO labeling change. NO risk-gate change. NO new src/ code. The only required code edit is the cosmetic ITERATION_LABEL bump (sub-fix #1). Sub-fixes #2-7 are pre-flight verifiers, not edits.

### 3.7 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Item | Code path | Verifier |
|---|---|---|---|
| 1 | `V3_FEATURE_COLUMNS` length 13 unchanged | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` exits 0 |
| 2 | `vwap_dev_50` and `tbr_zscore_30` NOT in V3_FEATURE_COLUMNS | features module | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert 'vwap_dev_50' not in V3_FEATURE_COLUMNS and 'tbr_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 |
| 3 | `atr_tp_multiplier=2.0` UNCHANGED | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 4 | `atr_sl_multiplier=1.0` UNCHANGED | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 5 | `zscore_threshold=2.0` UNCHANGED | `run_baseline_v3.py` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 6 | `BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED | `run_baseline_v3.py` line 123 | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 7 | `V3_MODELS` has exactly 3 entries; MKR not present | `run_baseline_v3.py` lines 108-112 | `python -c "from importlib import import_module; m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 3 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}"` exits 0 |
| 8 | `REQUIRED_GAP == 66` | `validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` exits 0 |
| 9 | `ITERATION_LABEL == "v3-018"` | `run_baseline_v3.py` line 102 | `grep -E 'ITERATION_LABEL.*=.*"v3-018"' run_baseline_v3.py` exits 0 |
| 10 | `ENSEMBLE_SIZE == 5` constant in runner | `run_baseline_v3.py` line 86 | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert m.ENSEMBLE_SIZE == 5"` exits 0 |
| 11 | Non-exploration code path: `ensemble_size_for_run = ENSEMBLE_SIZE`, `fast_mode_for_run = False`, n_trials NOT auto-overridden | `run_baseline_v3.py` lines 1371-1375 | `grep -E 'ensemble_size_for_run.*=.*1 if args\.exploration else ENSEMBLE_SIZE' run_baseline_v3.py` exits 0 AND `grep -E 'fast_mode_for_run.*=.*bool\(args\.exploration\)' run_baseline_v3.py` exits 0 |
| 12 | `--seeds 2 --n-trials 50` invocation produces 2 outer seeds × 5 inner = 10 models per cell | runner | grep `Seeds: 2  Optuna trials/model: 50` in `run.log` |
| 13 | `--exploration` flag NOT set in invocation | runner invocation | grep on `run.log` for absence of "exploration" in the activation banner |
| 14 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 15 | Wall-clock < 4h hard cap | engineering report | wall-clock minutes < 240 (target 75–180) |
| 16 | `comparison.csv` produced with multi-seed metrics aggregated | runner | `test -f reports-v3/iteration_v3-018/comparison.csv` AND DSR/PSR/PBO are NOT single-seed-saturation values (DSR > 0.0, PSR < 1.0 expected with multi-seed n_trials=300) |
| 17 | `pareto_front.csv` shows 2 distinct rows (one per outer seed); seeds Sharpes BOTH > 0 (per `feedback_outer_seed_cap_2_v3.md` 2-seed Pareto rule) | reports | `python -c "import pandas as pd; df = pd.read_csv('reports-v3/iteration_v3-018/pareto_front.csv'); assert len(df) >= 2 and (df['monthly_sharpe'] > 0).all()"` exits 0 (or equivalent column name) |
| 18 | Top-symbol concentration ≤ 30% (or explicit exception in §8) | reports | parsing per_symbol section of `comparison.csv` |
| 19 | Bundle-level OOS trade count ≥ 130 | reports | `python -c "import pandas as pd; df = pd.read_csv('reports-v3/iteration_v3-018/comparison.csv'); n = df.loc[df['metric']=='n_trades','out_of_sample'].iloc[0]; assert int(n) >= 130, f'OOS trades < 130 floor: {n}'"` exits 0 |

### 3.8 Inheritance from iter-v3/017

The `iteration-v3/018` branch was branched from `iteration-v3/017` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15`
- `e3168f2 feat(iter-v3/013): drop MKR (4-symbol → 3-symbol BCH+LDO+TRX) + REQUIRED_GAP 88→66`
- `c6ca96e feat(iter-v3/017): MetaLabelingStrategy + default --model lgbm restored + ITERATION_LABEL v3-017`

Critical inheritance verifiers (run before any code edits in Phase 6) — REUSED from iter-v3/013 brief §3.8:
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS and 'tbr_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0
- `grep -E '"BCHUSDT"' run_baseline_v3.py` exits 0 AND `grep -E '"MKRUSDT"' run_baseline_v3.py` exits 1 (MKR removed)
- `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0

### 3.9 Wall-clock estimate

**Two calibration points** for predicting iter-v3/018 wall-clock:

**Calibration A — linear scaling from iter-v3/013 (UPPER bound)**:
- iter-v3/013: 6 min @ (--seeds 1, ENSEMBLE_SIZE=1, n_trials=10, 3 symbols, --exploration mode)
- iter-v3/018 multiplier: 5 (ensemble: 1→5) × 5 (n_trials: 10→50) × 2 (seeds: 1→2) = **50×**
- Predicted: 6 min × 50 = **300 min ≈ 5.0h** — **EXCEEDS 4h cap by 1h**

**Calibration B — proportional scaling from iter-v3/008 (REALISTIC bound)**:
- iter-v3/008: aborted at 4h 15min @ (--seeds 5, ENSEMBLE_SIZE=5, n_trials=50, 4 symbols)
- iter-v3/018 cost ratio vs iter-v3/008: (2/5) seeds × (3/4) symbols = 0.30
- Predicted: 4h 15min × 0.30 = **76 min ≈ 1.27h** — **comfortably within 4h cap**

**Why the divergence**: Calibration A extrapolates from a tiny baseline (6 min) where fixed overhead (CPCV path matrix construction, ADF testing on 2041 cells, IC matrix, DSR/PBO/PSR computation) dominates the linear runtime, so the 50× multiplier double-counts overhead that doesn't scale linearly. Calibration B uses a same-config-class data point at production scale where overhead has stabilized.

**The QR's chosen estimate**: **75–180 min (1.25–3h), comfortably within 4h cap**, leaning toward Calibration B but allowing for ~50% upside variance from real-system noise (Optuna trial-time variance, parquet I/O cache state, n_trials=50 fitting more trees per LightGBM call than n_trials=10). **Recommendation: proceed at full spec (--seeds 2 --n-trials 50). Engineer kills Phase 6 if elapsed > 4h.**

**Contingency planning** (if Calibration A turns out closer to truth):

| Reduction strategy | New spec | Estimated wall-clock | Methodology cost |
|---|---|---:|---|
| (none — full spec) | --seeds 2 --n-trials 50 | 75–300 min | full CONFIRMATION rigor |
| Reduce n_trials 50 → 30 | --seeds 2 --n-trials 30 | 45–180 min | lower Optuna search rigor; n_eff likely drops 7→5; **least bad** if needed |
| Reduce outer seeds 2 → 1 | --seeds 1 --n-trials 50 | 38–150 min | NOT recommended — defeats multi-seed validation, the entire point of CONFIRMATION |
| Accept >4h cap exceedance | (any) | >240 min | NOT allowed per cadence rule |

**The QR's specific recommendation**: do NOT pre-commit to any reduction. Run at full --seeds 2 --n-trials 50. If the Engineer hits 3h elapsed and projection extrapolates beyond 4h, the Engineer kills Phase 6, and iter-v3/018 is re-run with --n-trials 30 in a subsequent iteration (not the same wall-clock window). The kill-switch decision rule is: at t=180 min, if `< 60% of cells have completed Optuna fitting`, kill and re-launch with reduced n_trials.

---

## Section 4 — Expected OOS Impact

### 4.1 CONFIRMATION → headline metrics ARE BLOCK-triggering gates

Per Section 0.5 + `feedback_v3_iter018_confirmation_baseline_validation.md`, iter-v3/018 is a CONFIRMATION iteration with **mechanical merge gates** (Section 8). Critic emits `CONFIRMATION-MERGE`, `CONFIRMATION-NO-MERGE-METHODOLOGY`, `CONFIRMATION-NO-MERGE-FRAGILITY`, or `BLOCK`. Any single MERGE-gate failure = NO-MERGE.

### 4.2 Predicted multi-seed Sharpe bands

| Metric | iter-v3/013 (1-seed) | iter-v3/018 prediction (multi-seed mean) | Falsifier |
|---|---:|---:|---|
| **IS monthly Sharpe** | +1.0088 | **predicted [+0.85, +1.20] with median +1.00** | **OOS<+1.0 OR IS<+0.85 → NO-MERGE on insufficient edge** |
| **OOS monthly Sharpe** | +2.6970 | **predicted [+1.50, +2.40] with median +1.95** | **OOS<+1.0 → NO-MERGE-METHODOLOGY** |
| OOS/IS Sharpe ratio | 2.6734 | predicted [1.5, 2.4] with median 1.95 | < 0.5 → NO-MERGE on overfitting evidence |
| IS trade count | 209 | predicted ~200-260 (modest variance from outer-seed Optuna re-routing) | sub-130 or super-300 unexpected |
| **OOS trade count (BUNDLE)** | 85 | **predicted [130, 200]** (single-seed 85 × ~2× multi-seed = ~170; multi-seed averaging adds trades not subtracts) | **OOS<130 → NO-MERGE on bundle-level trade-rate floor** per `feedback_trade_rate_floor_bundle_level.md` |
| **DSR** | 0.0000 (single-seed saturation) | **predicted [0.85, 0.99]** (multi-seed n_eff > 10 should give meaningful DSR) | DSR<0.95 → NO-MERGE-METHODOLOGY |
| **PBO** (cross-cell mean) | 0.1075 | **predicted [0.05, 0.20]** (multi-seed averaging reduces per-cell PBO variance) | PBO≥0.4 → NO-MERGE-METHODOLOGY |
| PBO (cross-cell **max** aggregator) | 0.99+ on TRX/2025-Q4 | **predicted [0.40, 0.99]** | max-PBO≥0.4 → CRITIC INFORMATIONAL FLAG (per iter-v3/013 catalog) |
| **PSR** | 1.0000 (single-seed saturation) | **predicted [0.95, 1.00]** | PSR<0.95 → NO-MERGE-METHODOLOGY |
| **LDO concentration** | 65.65% | **predicted [25%, 55%]** (multi-seed averaging may compress lottery flag) | concentration > 30% → NO-MERGE-FRAGILITY (or explicit Critic exception) |
| n_eff | 7 | predicted [10, 20] | n_eff < 10 → CRITIC INFORMATIONAL CONCERN |
| Wall-clock | 6 min | predicted 75–180 min | > 240 min (4h) → BLOCK |

The prediction bands are deliberately broad to absorb:
- Multi-seed averaging may either compress IS Sharpe (variance reduction toward true mean) or expand it (if the single-seed +1.01 was noise within an underlying +1.20 distribution)
- LDO 80% WR on 10 trades is consistent with luck within 95% CI [44.4%, 97.5%]; multi-seed averaging tests whether the WR holds under different Optuna trajectories
- DSR computation requires n_eff ≥ 2; with n_trials=300 (3 sym × 50 trials × 2 seeds) and n_eff predicted ≥ 10, DSR formulation is well-defined for the first time in v3

**Median IS prediction +1.00 sits at the iter-v3/013 baseline** because the multi-seed mean of 2 outer seeds is unbiased given identical underlying signal — only variance changes. Lower bound +0.85 allows for unfavorable outer-seed variance; upper bound +1.20 allows for favorable.

### 4.3 Fragility tests (LOAD-BEARING for NO-MERGE-FRAGILITY classification)

**Fragility test F1 — LDO concentration compression**:
- iter-v3/013 single-seed LDO 65.65% concentration; iter-v3/017 single-seed LDO 74.36% concentration
- iter-v3/018 multi-seed prediction: if LDO concentration > 50% under 2-outer-seed mean, this is **fragility evidence** (single-seed lottery flag persists under multi-seed averaging) → NO-MERGE-FRAGILITY classification
- If LDO concentration ≤ 30% (multi-seed mean), CONFIRMATION-MERGE eligible per gate #6

**Fragility test F2 — bundle-level trade rate**:
- iter-v3/013 OOS=85 trades, iter-v3/017 OOS=62 trades — single-seed runs both below 130 floor
- iter-v3/018 multi-seed prediction: ~170 trades (85 × 2 seeds, modulo overlap)
- If bundle OOS trades < 130, **fragility evidence** that the trade-rate floor only clears on optimistic outer seeds → NO-MERGE-FRAGILITY classification

**Fragility test F3 — multi-seed Sharpe variance**:
- Std(IS Sharpe) and Std(OOS Sharpe) across 2 outer seeds
- High inter-seed variance (std > 0.5 IS Sharpe units, std > 1.0 OOS Sharpe units) signals the strategy's edge is seed-luck-dependent
- If both outer seeds have OOS Sharpe > +1.0 AND IS Sharpe > +0.85 AND OOS/IS ≥ 0.5, the strategy is robust under the 2-seed cap (per `feedback_outer_seed_cap_2_v3.md` 2-seed rule)
- If only 1 of 2 outer seeds clears the floor, **fragility evidence** → NO-MERGE-FRAGILITY

### 4.4 CONFIRMATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row + downstream action |
|---|---|---|
| `CONFIRMATION-MERGE` | All 10 MERGE gates §8 pass | Updates BASELINE_V3.md; tags v0.v3-018; cherry-picks docs+feat to quant-research |
| `CONFIRMATION-NO-MERGE-METHODOLOGY` | Any methodology gate fails (DSR, PBO, PSR, OOS Sharpe, IS Sharpe, OOS/IS ratio, trade-rate floor) | Catalog row documents which gate failed; recommends specific methodology fix for next 10-EXPLORATION cycle |
| `CONFIRMATION-NO-MERGE-FRAGILITY` | Concentration > 30% under multi-seed avg, OR trade-rate floor only met on 1 of 2 seeds, OR multi-seed Sharpe variance shows luck-dependence | Catalog row documents fragility pattern; recommends specific EXPLORATION axes (e.g., LDO-specific filter, cooler LDO position-sizing) for next 10-EXPLORATION cycle |
| `BLOCK` | Methodology check FAILED, or wall-clock cap exceeded, or §3.7 reconciliation row fails | Diary documents; iter-v3/019 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`: every merge candidate must include this section with IS-calibrated thresholds and simulated historical effect. For iter-v3/018 the "simulated effect" IS the iter-v3/013 single-seed run already committed; the multi-seed run validates that the historical effect persists under cross-validation.

### 5.1 Cadence-discipline structural safeguards

iter-v3/018 inherits FOUR structural safeguards:

1. **4h wall-clock hard cap** (per CONFIRMATION cadence rule + `feedback_v3_iter018_confirmation_baseline_validation.md`): Engineer kills Phase 6 if elapsed > 4h.
2. **Single-axis variation rule** honored: only multi-seed config CHANGED (--seeds 2 / ENSEMBLE_SIZE=5 / n_trials=50 / `colsample_bytree` Optuna-tunable); features/labeling/risk-gates/universe byte-identical to iter-v3/013.
3. **CONFIRMATION-MERGE updates BASELINE_V3.md** only if ALL 10 MERGE gates clear at non-EXPLORATION thresholds. ANY gate failure = NO-MERGE.
4. **Pre-commitment lock** via `feedback_v3_iter018_confirmation_baseline_validation.md`: spec cannot be renegotiated post-hoc by future Engineer or QR.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-017)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.7). 19 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_MODELS`, `REQUIRED_GAP`, `V3_FEATURE_COLUMNS`, `ENSEMBLE_SIZE`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.
5. **Sub-fix #1 cosmetic-only**: ITERATION_LABEL bump is a one-line edit with negligible regression risk.

### 5.3 Multi-seed-axis specific risks (NEW for iter-v3/018)

1. **Outer-seed determinism**: `_derive_ensemble_seeds(outer_seed, size=5)` uses `np.random.default_rng(outer_seed)`. If user invokes `--seeds 2`, runner iterates `seed in [42, 123]` (the legacy seed list). Section 3.7 row 12 verifies `Seeds: 2` printed in run.log; Section 3.7 row 17 verifies pareto_front.csv has 2 distinct rows.
2. **Inner-ensemble determinism**: 5 inner seeds are derived per outer seed. iter-v3/006 fix already eliminated the pre-iter-v3/006 "all outer seeds got identical inner ensemble" bug (commit 5217490 generation in iter-v3/006). Verifier: pareto_front.csv shows distinct OOS Sharpes across 2 outer seeds (high probability if inner-ensemble derivation is correct).
3. **n_trials=50 budget per cell**: each (symbol, month) cell gets 50 Optuna trials × 5 inner seeds = 250 trials per cell per outer seed. Joint rank should give n_eff ≥ 10. If n_eff < 10 actual, iter-v3/018 informational caveat (DSR formulation marginal).
4. **`colsample_bytree` Optuna-tuned**: per iter-v3/008 colsample A/B research, allowing Optuna to tune `colsample_bytree` is the production-config choice. iter-v3/007/008 EXPLORATION ran `colsample=1.0` hardcoded for fast-iteration determinism; non-exploration mode restores Optuna sampling. Per-seed feature-subsampling may add modest variance but is the production-correct config.

### 5.4 Multi-seed concentration management (LDO carry-forward)

The LDO 65.65% concentration in iter-v3/013 single-seed (and 74.36% in iter-v3/017 single-seed) is **the dominant pre-commit fragility flag**. Per `briefs-v3/exploration_catalog.md` iter-v3/013 + iter-v3/017 caveats:

- Multi-seed averaging may compress LDO concentration (numerator stays similar, denominator may grow if other symbols' Optuna trajectories find better hyperparams under multi-seed)
- OR multi-seed averaging may NOT compress (if LDO 80% WR on 10 trades was true signal, multi-seed averages of 2 outer × 5 inner = 10 models per (sym, month) on LDO would all converge to similar OOS performance and concentration stays high)
- Fragility test F1 (§4.3): LDO concentration > 50% under multi-seed = NO-MERGE-FRAGILITY (the 80% WR is luck-dependent)

The 30% per-symbol cap from `BASELINE_V3.md` "Inherited project-level merge gates" is the binding threshold. Multi-seed compression to ≤ 30% would clear gate #6; persistence > 30% is FRAGILITY evidence regardless of headline Sharpe.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL to iter-v3/013, fire-rate predictions inherited

| # | Primitive | Spec | Fire-rate prediction (IS, multi-seed) | Source |
|---|---|---|---:|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | inherited iter-v3/013 |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | inherited iter-v3/013 |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | inherited iter-v3/013 |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 | ≈ 25–35% killed | inherited iter-v3/013 (z=2.0 from iter-v3/011) |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | inherited iter-v3/013 |
| 6 | Hit-rate feedback | DISABLED | 0% | inherited iter-v3/013 |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed | inherited iter-v3/013 (band=15% from iter-v3/012) |

Combined kill rate target: **80–90%** (same as iter-v3/013). Multi-seed averaging does NOT change any primitive's threshold or fire rate — primitives operate per-(symbol, candle) on past-only data, independent of seed.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction.

### 6.3 Concentration — BINDING gate at CONFIRMATION (NOT informational like EXPLORATION)

iter-v3/013 OOS shows LDO 65.65% concentration; iter-v3/017 OOS shows 74.36%. Both above the 30% per-symbol cap that **applies as a binding gate at CONFIRMATION**. Per Section 8 gate #6, the multi-seed mean LDO concentration must compress to ≤ 30% for CONFIRMATION-MERGE; otherwise NO-MERGE-FRAGILITY classification.

**Explicit-with-justification exception clause**: per BASELINE_V3.md "Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)". v0.186 v1 baseline uses a DOT@38% explicit exception. iter-v3/018 may invoke a similar exception ONLY IF: (a) Critic accepts that LDO 30-50% concentration is structurally unavoidable given 3-symbol universe; (b) bundle-level OOS trades ≥ 130 (gate #8) demonstrates the LDO contribution is statistically significant not lottery; (c) F1 fragility test passes (multi-seed compression demonstrably moves toward 30%, even if not below). All three conditions must be explicit. The QR pre-commits: **NO blanket exception; if multi-seed LDO > 50%, NO-MERGE-FRAGILITY automatic.**

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=10%)**: Multi-seed Sharpe variance is high enough to indicate trade-rate floor not met at bundle level. **Detection signal**: bundle OOS trades < 130 OR std(OOS Sharpe across 2 seeds) > 1.0. **Mitigation**: Section 3.7 row 19 verifier; Section 4.3 fragility test F2 + F3.

**Prediction P2 (process, P=15%)**: LDO concentration does NOT compress under multi-seed averaging (persists > 50%) — the 80% WR on 10 trades was true signal that multi-seed verifies, OR pure path-dependent lottery that multi-seed inherits. **Detection signal**: per_symbol concentration in `comparison.csv` reports LDO > 50%. **Mitigation**: Section 4.3 fragility test F1 → NO-MERGE-FRAGILITY classification with specific recommendation for next-10-EXPLORATION cycle (LDO position-sizing constraint, LDO-specific gate, ex-LDO basket performance).

**Prediction P3 (process, P=15%)**: PBO max-aggregator catches per-cell tails — TRX/2025-Q4 carry-forward at 99% PBO is structurally persistent. **Detection signal**: max(per_cell_pbo) ≥ 0.99 in `per_cell_pbo.csv`. **Mitigation**: pre-commit max-aggregator review per iter-v3/013 catalog caveats; the cross-cell mean PBO < 0.4 gate clears even if max is 0.99. Critic flags max-aggregator informationally but does NOT block on it.

**Prediction P4 (process, P=20%)**: Wall-clock exceeds 4h cap. **Detection signal**: wall-clock minutes > 240 in engineering report. **Mitigation**: Engineer kill switch at t=180 min if projection extrapolates beyond 4h; iter-v3/019 re-runs at reduced --n-trials 30 in subsequent iteration.

**Prediction P5 (process, P=10%)**: 10-seed pre-MERGE concentration validation runs separately after main backtest and shows < 7/10 profitable. **Detection signal**: post-Phase 7 10-seed sanity run produces fewer than 7 of 10 outer-seed Sharpes > 0. **Mitigation**: Per `feedback_seed_validation.md` (legacy v1/v2 rule, retained for v3 final-pre-MERGE check); the 2-seed cap from `feedback_outer_seed_cap_2_v3.md` covers the main run. The 10-seed pre-MERGE check is a SEPARATE validation step that runs only IF the main 2-seed run clears all 10 MERGE gates. iter-v3/018 brief Section 8 gate #9 specifies this as the final gate before MERGE.

**Prediction P6 (methodology, P=15%)**: DSR < 0.95 due to n_eff under-coverage even at n_trials=300. **Detection signal**: dsr.json `dsr` field < 0.95. **Mitigation**: NO-MERGE-METHODOLOGY classification; iter-v3/019 EXPLORATION on richer Optuna search space (more hyperparams or longer trial budget per seed) to lift n_eff.

**Prediction P7 (model, P=35%)**: IS Sharpe in [+0.85, +1.20], OOS Sharpe in [+1.50, +2.40], LDO concentration ≤ 30%, all methodology gates pass → CONFIRMATION-MERGE. The strategy's edge is robust under multi-seed cross-validation. iter-v3/018 ships v0.v3-018; BASELINE_V3.md updates.

**Prediction P8 (model, P=20%)**: IS Sharpe in [+0.85, +1.20] AND OOS Sharpe in [+1.50, +2.40] BUT LDO concentration > 30% (single-seed lottery persists) → CONFIRMATION-NO-MERGE-FRAGILITY. The strategy's headline Sharpe holds but per-symbol concentration is structurally unacceptable; iter-v3/019 EXPLORATION on LDO-specific filter or position-sizing.

**Prediction P9 (model, P=10%)**: IS or OOS Sharpe drops below floors → CONFIRMATION-NO-MERGE-METHODOLOGY. The single-seed iter-v3/013 result was favorable outer-seed luck; multi-seed averaging reveals true Sharpe is lower. iter-v3/019 EXPLORATION pivots to a different axis.

The predictions are Bayesian-calibrated:
- 4 process-level (P1, P3, P4, P6) per iter-v3/003 lesson #3 discipline
- 5 model-level (P5, P7, P8, P9 + the implicit P10 = catastrophic gate failure ≈ 5%)
- Per the iter-v3/008 calibration history (CONFIRMATION-class spec at --seeds 5 aborted at 4h 15min): wall-clock realism is the dominant process risk

**Summary**:
- **CONFIRMATION-MERGE pathway probability ≈ 35%** (P7)
- **CONFIRMATION-NO-MERGE-FRAGILITY probability ≈ 30%** (P2 + P8)
- **CONFIRMATION-NO-MERGE-METHODOLOGY probability ≈ 25%** (P6 + P9)
- **BLOCK probability ≈ 10%** (P4 dominant; P1+P3 contribute)

If any prediction fails to materialize, the iter-v3/018 diary documents the calibration miss.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically. Cannot be renegotiated post-hoc.**

iter-v3/018 is a CONFIRMATION iteration. Critic emits `CONFIRMATION-MERGE`, `CONFIRMATION-NO-MERGE-METHODOLOGY`, `CONFIRMATION-NO-MERGE-FRAGILITY`, or `BLOCK`.

### CONFIRMATION-MERGE iff ALL 10 of the following are true:

| # | Gate | Threshold | Source |
|---|---|---:|---|
| 1 | IS monthly Sharpe ≥ +1.0 | multi-seed mean (2 outer × 5 inner = 10 models per cell, then aggregated) | `feedback_v3_iter018_confirmation_baseline_validation.md` + `feedback_sharpe_floor.md` |
| 2 | OOS monthly Sharpe ≥ +1.0 | multi-seed mean | same |
| 3 | OOS / IS Sharpe ratio ≥ 0.5 | derived from #1 #2 | `BASELINE_V3.md` |
| 4 | DSR > 0.95 | from `dsr.json` (multi-seed n_eff > 10 expected) | `BASELINE_V3.md` |
| 5 | PBO < 0.4 (cross-cell **mean** AND **max** aggregator both pass) | from `per_cell_pbo.csv`; cross-cell mean from dsr.json `pbo` field | `BASELINE_V3.md` + iter-v3/013 catalog max-aggregator pre-commit |
| 6 | PSR > 0.95 | from `dsr.json` | `BASELINE_V3.md` |
| 7 | Top-symbol concentration ≤ 30% (multi-seed mean) OR explicit Critic-accepted exception per §6.3 (3 conditions all met) | from per_symbol section of `comparison.csv` | `BASELINE_V3.md` + §6.3 |
| 8 | **Bundle-level OOS trade count ≥ 130** | from `comparison.csv` | `feedback_trade_rate_floor_bundle_level.md` (v3 supersedes legacy per-iteration rule) |
| 9 | 10-seed pre-MERGE concentration validation: mean Sharpe > 0, ≥ 7/10 profitable | post-Phase 7 separate validation run; per `feedback_seed_validation.md` (legacy retained for v3 final-pre-MERGE) | `feedback_seed_validation.md` |
| 10 | Multi-seed Pareto front non-domination — **2-seed rule per `feedback_outer_seed_cap_2_v3.md`**: BOTH outer seeds Sharpe > 0 (binary, NOT "≥7/10 profitable" since N=2) | from `pareto_front.csv` | `feedback_outer_seed_cap_2_v3.md` |

**ALL 10 gates must pass.** Any single gate failure = NO-MERGE.

### CONFIRMATION-NO-MERGE-METHODOLOGY iff:

- ANY of gates #1, #2, #3, #4, #5, #6, #8 fail (statistical / methodology gates)
- The strategy's headline edge does NOT clear the bar at multi-seed rigor
- Catalog row documents which gate(s) failed; recommends specific methodology fix for next 10-EXPLORATION cycle

### CONFIRMATION-NO-MERGE-FRAGILITY iff:

- Gates #1-#6 + #8 PASS but gate #7 FAILS (concentration > 30% under multi-seed avg, no Critic-accepted exception)
- OR gate #10 FAILS (only 1 of 2 outer seeds Sharpe > 0; 2-seed Pareto rule)
- OR gate #9 FAILS (10-seed pre-MERGE shows fragility; < 7/10 profitable)
- The strategy's headline edge is real but per-symbol or per-seed luck-dependent
- Catalog row documents fragility pattern; recommends specific EXPLORATION axes for next 10-EXPLORATION cycle (e.g., LDO position-sizing, ex-LDO basket research)

### BLOCK (process) iff ANY of:

- §3.7 reconciliation row(s) fail (Phase 5.5 BLOCK or Phase 6 setup defect)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 4h hard cap

### Discretionary judgment

iter-v3/018's MERGE pathway is `CONFIRMATION-MERGE` with explicit gate clearing on all 10 thresholds. **NO QR or Critic discretion can override gate failures.** The "explicit exception" for gate #7 is a CRITIC-level escalation that requires three structural conditions met simultaneously per §6.3; the QR cannot pre-grant the exception in this brief.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 (default --model lgbm restored at iter-v3/017) | n/a |
| `pytest` | (already installed) | MIT | adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |
| `optuna` | (already installed) | MIT | Hyperparameter search (n_trials=50 per cell per inner seed per outer seed) | n/a |

**No new external deps.** Same stack as iter-v3/013-017 (LightGBM only; XGBoost remains opt-in via `--model xgboost`; meta-labeling remains opt-in via `--model metalabeling`). The iteration's NEW code is:
- 1 line edit in `run_baseline_v3.py` (ITERATION_LABEL "v3-017" → "v3-018")
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths
- 0 new pytest test files
- 0 modifications to V3_FEATURE_COLUMNS, RiskV2Config, BTC_TREND_CONFIG, REQUIRED_GAP, V3_MODELS

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation (primary). Cross-cell max-aggregator INFORMATIONAL per iter-v3/013 catalog pre-commit. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-018/engineering_report.md` with:
- Git commit SHAs at backtest time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow|optuna)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- Runtime `V3_MODELS` (3 entries, no MKR)
- Runtime `REQUIRED_GAP` (66)
- Runtime `ENSEMBLE_SIZE` (5; non-exploration mode)
- Runtime `args.seeds == 2`, `args.n_trials == 50`, `args.exploration is False`
- The `comparison.csv` IS / OOS multi-seed monthly Sharpe values
- Multi-seed std(IS Sharpe) and std(OOS Sharpe) across 2 outer seeds (fragility test F3)
- The `pareto_front.csv` 2-row dump (gate #10 verification)
- The `dsr.json` DSR / PBO / PSR / n_eff dump (gates #4, #5, #6)
- Per-symbol concentration breakdown (gate #7)
- Bundle OOS trade count (gate #8)
- The wall-clock minutes total (must be < 240; target 75-180)
- The adversarial test outcome (PASS expected)
- The non-exploration activation banner from `run.log` (no "exploration" in invocation)
- The runner invocation literal (proof of `--seeds 2 --n-trials 50` with NO `--exploration`)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections. Note the structural difference from EXPLORATION briefs in Section 2 (no fresh IS-only EDA — the prior is the iter-v3/013 single-seed run already committed):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=5 / colsample=Optuna-tuned / n_trials=50 / outer_seeds=2 SET BY non-exploration mode + --seeds 2 + --n-trials 50 invocation |
| 0.5 — Iteration Type Declaration | PASS — TYPE: CONFIRMATION declared (FIRST true v3 CONFIRMATION); 4h HARD CAP; "first v3 CONFIRMATION; NOT bundle assembly; multi-seed validation of iter-v3/013 baseline"; CONFIRMATION-MERGE updates BASELINE_V3.md if all 10 gates pass; pre-commitment lock via `feedback_v3_iter018_confirmation_baseline_validation.md` |
| 1 — Hypothesis | PASS — one sentence; testable target multi-seed IS ≥ +1.0 / OOS ≥ +1.0 with all 10 gates |
| 2 — IS-Only Numerical Evidence | PASS — structural difference from EXPLORATION briefs explicitly acknowledged (CONFIRMATION's analysis IS the iter-v3/013 baseline run committed at SHA `e3168f2`); inherited iter-v3/013 metrics tabulated; per-symbol attribution; per-cell PBO + n_eff diagnostics |
| 3 — Proposed Changes | PASS — symbols/labeling/features/risk-gates ALL UNCHANGED; only multi-seed config CHANGED; single-axis discipline preserved (the axis IS multi-seed-validation); 19-row reconciliation table; ENSEMBLE_SIZE/n_trials/colsample verified in runner code |
| 4 — Expected OOS Impact | PASS — predicted multi-seed Sharpe bands [IS +0.85 to +1.20, OOS +1.50 to +2.40]; LDO concentration prediction band [25%, 55%]; bundle OOS trade count prediction [130, 200]; 3 fragility tests F1/F2/F3; CONFIRMATION outcome interpretation table |
| 5 — Risk Mitigation | PASS — 4 cadence-discipline structural safeguards + 5 methodology-pipeline safeguards + 4 multi-seed-axis specific risks + LDO concentration management; per `feedback_risk_mitigation_design.md`, simulated effect IS the iter-v3/013 baseline run |
| 6 — Risk Management Design | PASS — 7-primitive table inherited; gate orthogonality verified for multi-seed (primitives operate per-(symbol, candle), seed-independent); concentration is BINDING gate at CONFIRMATION (NOT informational like EXPLORATION) |
| 7 — Pre-Registered Failure-Mode | PASS — 9 predictions with **4 process-level (P1, P3, P4, P6)**; calibrated MERGE pathway probability ~35%, NO-MERGE-FRAGILITY ~30%, NO-MERGE-METHODOLOGY ~25%, BLOCK ~10% |
| 8 — Pre-Registered MERGE/NO-MERGE Criteria | PASS — 10 MERGE gates + 4 BLOCK conditions + 3 verdict pathways (MERGE / NO-MERGE-METHODOLOGY / NO-MERGE-FRAGILITY); concentration exception requires 3 structural conditions met simultaneously |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/013-017 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.7. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8. Note that gate #5 (PBO < 0.4 cross-cell mean AND max-aggregator both pass) and gate #7 (concentration ≤ 30% multi-seed mean, no exception unless 3 structural conditions met) are CRITICAL CONFIRMATION-specific gates that did NOT apply at EXPLORATION.

**Wall-clock contingency**: at t=180 min Engineer evaluates progress. If projection extrapolates beyond 4h, kill Phase 6 and re-launch in iter-v3/019 with --n-trials 30 (NOT --seeds 1; preserving multi-seed validation is the entire point of CONFIRMATION).

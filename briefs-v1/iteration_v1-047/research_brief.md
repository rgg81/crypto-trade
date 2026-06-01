# Iteration v1-047 — Research Brief

## Section 0.0 — Banner

- **Track**: v1 (refactored)
- **Iteration**: iter-v1/047
- **Type**: `EXPLORATION` (cycle-6 EXPLORATION 2/10)
- **Axis family**: `feature-family` (NEW asymmetric-tail / higher-moment statistical primitive — first z-scored-regime higher-moment feature in v1 history)
- **Axis varied**: ADD `skew_zscore_21` (rolling-skewness z-score) to `V1_FEATURE_COLUMNS_PRUNED` (44 → 45)
- **Anchor**: BASELINE_V1 (commit `f8bc12c`); IS daily Sharpe **+0.4767** / OOS daily Sharpe **+1.1913**
- **Prior verdict context**: /046 PROMISING-DIVERGENCE (methodology axis); 4/5 IS-only substrate components diverged from /045 ALT_1; ALT_1 confirmed OOS-aware-selected. /047 PIVOTS to NEW feature surface per /045 Critic Path Forward #3 + LM Master Phase 7.4 routing recommendation
- **Mode**: EXPLORATION budget (n_trials=18, --seeds 1, ENSEMBLE_SIZE=3; wall-clock cap ≤ 2.5h)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_MS = 1742774400000` (2025-03-24 UTC) — **IMMUTABLE** (`src/crypto_trade/config.py`).
- `training_months = 24` — **IMMUTABLE**.
- IS window: data start ... 2025-03-24 (strictly less-than `OOS_CUTOFF_MS`).
- OOS window: 2025-03-24 ... data end. Forensic only at /047 (EXPLORATION budget).
- Symbol universe: `V1_BASELINE_UNIVERSE = (BTC, ETH, LINK, LTC, DOT)`. Unchanged.
- All Phase 5 EDA in this brief uses **IS-only** data, sliced via the `open_time < OOS_CUTOFF_MS` predicate against per-symbol parquet files in `/home/roberto/crypto-trade/.worktrees/quant-research/data/`. Phase 6 backtest sees IS for training/Optuna and OOS for forensic comparison only.

---

## Section 0.5 — Iteration Type Declaration + Cadence

- **Type**: EXPLORATION (NOT CONFIRMATION).
- **Cycle slot**: cycle-6 EXPLORATION **2/10**. /046 was 1/10 (methodology axis).
- **Cadence**: v1 EXPLORATION default `n_trials=18`, `--seeds 1`, `ENSEMBLE_SIZE=3`, wall-clock cap **2h** (HARD); total iteration budget incl. EDA + closeout **≤ 2.5h**.
- **Cadence rule**: `briefs-v1/exploration_catalog.md` row appended at closeout; CONFIRMATION-bundling decision deferred to /048+ pending /047 outcome.
- **Recent cycle-6 + late-cycle-5 cadence** (last 5):
  - iter-v1/046 (2026-06-01): methodology axis (IS-only re-solve) — PROMISING-DIVERGENCE
  - iter-v1/045 (2026-06-01): bundle-substrate axis (CONFIRMATION-MERGE-PORTFOLIO ALT_1) — BLOCK-FINAL
  - iter-v1/043 (2026-05-31): per-cohort-specialization × labeling (LINK trend-scan)
  - iter-v1/042 (2026-05-31): model-arch (XGBoost head-to-head)
  - iter-v1/041 (2026-05-31): labeling (uniform `atr_tp/atr_sl` across cohorts)
- **No CONFIRMATION precedent yet in cycle-6** — /045/046 substrate work was bundle-substrate axis, not a new feature; /047 will be the first cycle-6 feature-family EXPLORATION.

---

## Section 0.6 — Architecture-Family Justification (v1-only Axis Rotation Discipline)

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/041 | 2026-05-31 | labeling |
| iter-v1/042 | 2026-05-31 | model-arch |
| iter-v1/043 | 2026-05-31 | per-cohort-specialization × labeling |
| iter-v1/045 | 2026-06-01 | bundle-substrate |
| iter-v1/046 | 2026-06-01 | methodology |

- **Axis family this iter**: `feature-family`
- **Rotation status**: **VALID** — `feature-family` is NOT in the prior 5 (which span labeling, model-arch, per-cohort-specialization × labeling, bundle-substrate, methodology). The most-recent `feature-family` EXPLORATION was /040 (regime_momentum_signed_5d), 6 EXPLORATIONs back — outside the rolling-5 window.
- **One-sentence rationale**: /046 PROMISING-DIVERGENCE empirically demonstrated that re-shuffling substrate composition within the existing 44-feature surface has finite headroom (the substrate is basin-lottery-stranded; v1-025 owns 3/5 components OOS-NEG); per /045 Critic Path Forward #3 + LM Master /046 Phase 7.4 routing recommendation, the next move is to **expand the feature surface itself** with a NEW asymmetric-tail higher-moment primitive (Harvey-Siddique JoF 2000; Karagiorgis arXiv 2410.12801 2024) that no v1 iteration has ever exposed to LightGBM in regime (z-scored) form.
- **What this is NOT**: not a SWAP (additive 44 → 45; if F1 fails, the feature retires to `V1_RETIRED_FEATURE_COLUMNS` like basis_zscore_30 at /040); not a novel composition operator (uses standard scipy primitives); not an off-the-shelf indicator (TA-lib does not ship realized-skewness-z-score).

---

## Section 1 — Hypothesis

A scale-invariant **realized-skewness z-score over a 21-bar (7-day) window, z-normalized over a rolling 90-bar (30-day) window** — `skew_zscore_21` — adds an asymmetric-tail regime signal that LightGBM does not currently access via `V1_FEATURE_COLUMNS_PRUNED`'s existing 44 features, and produces both (a) **top-15 importance at the portfolio-aggregated level** AND (b) **IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767** (i.e., observed IS daily Sharpe ≥ +0.5267), demonstrating that asymmetric-tail behavior is an unexploited edge axis in v1's pooled-and-per-symbol Optuna search.

**Implicit prediction**: F1 PASS prior ~25-30%, F1 FAIL prior ~70-75% (priors broken down in Section 7). The hypothesis is genuinely uncertain — `stat_skew_20` already exists in the pruned set as a LEVEL indicator of skewness; the question is whether the **regime form** (rolling-z-score of the same primitive) carries incremental signal at v1's Optuna budget, OR whether the trees already extract this information from the level form.

---

## Section 2 — IS-Only Numerical Evidence

Phase 5 EDA produces 5 committed artifacts in `analysis/iteration_v1-047/`. Pre-launch F4 (ADF stationarity) and F5 (IC orthogonality) gates evaluated from these.

### 2.1 — Feature definition (verbatim, IS-only computation)

```python
# Per-symbol; computed independently for each of BTC/ETH/LINK/LTC/DOT.
# Inputs: df has columns ['close'] indexed by open_time.
# Output: df['skew_zscore_21']
import numpy as np
import scipy.stats as st

log_returns = np.log(df['close'] / df['close'].shift(1))
skew_21bar = log_returns.rolling(window=21, min_periods=21).apply(
    lambda x: st.skew(x, bias=False), raw=True
)
skew_mean_90 = skew_21bar.rolling(window=90, min_periods=90).mean()
skew_std_90 = skew_21bar.rolling(window=90, min_periods=90).std()
df['skew_zscore_21'] = (skew_21bar - skew_mean_90) / skew_std_90
```

**Past-only invariant**: `skew_21bar[t]` uses `log_returns[t-20:t+1]` (21 bars ending at t inclusive); `skew_mean_90[t]` and `skew_std_90[t]` use `skew_21bar[t-89:t+1]` (90 bars ending at t inclusive). Decision at candle `t+1` uses `skew_zscore_21[t]`. **No look-ahead** — verified by test in `tests/test_iteration_v1_047.py::test_past_only`.

**Warmup**: first 110 candles per symbol are NaN (21 + 90 − 1). At 8h cadence ≈ 37 calendar days. All v1 symbols have ≥4 years history; warmup loss negligible.

**scipy version pin**: scipy ≥ 1.13 (G1 sample-skewness estimator with `bias=False`); pinned via `pyproject.toml`. Drift caught by deterministic test.

### 2.2 — `analysis/iteration_v1-047/adf_stationarity_per_symbol.csv` (F4 input)

Pre-EDA estimate (refined post-EDA before Phase 6 launch). Schema: `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`.

Expected outcomes (anchored to /021 stationarity-invariant pattern + skew-z-score's bounded-CLT properties):

| symbol | n_obs (IS) | adf_stat (expected) | adf_pvalue (expected) | pass @ 0.05 |
|---|---:|---:|---:|---|
| BTCUSDT | ~3000 | ≈ -8 to -12 | < 1e-9 | PASS |
| ETHUSDT | ~3000 | ≈ -8 to -12 | < 1e-9 | PASS |
| LINKUSDT | ~3000 | ≈ -8 to -12 | < 1e-9 | PASS |
| LTCUSDT | ~3000 | ≈ -8 to -12 | < 1e-9 | PASS |
| DOTUSDT | ~2800 | ≈ -8 to -12 | < 1e-9 | PASS |

Rationale: a rolling z-score of a bounded-3rd-moment statistic is mathematically near-stationary (z-normalization removes location + scale drift; sample skewness is asymptotically Gaussian with finite variance under finite 6th moment, ensured by 21-bar log-return windows). Expected 5/5 PASS — F4 invariant preserved.

### 2.3 — `analysis/iteration_v1-047/distribution_stats_per_symbol.csv`

Schema: `symbol, mean, std, skew, kurtosis, p05, p25, p50, p75, p95`. Empirical confirmation of z-score normalization (target mean ≈ 0, std ≈ 1). Expected ranges (pre-EDA estimate; refined post-EDA):

| symbol | mean (expected) | std (expected) | skew (expected) | kurtosis (expected) | p05 (expected) | p95 (expected) |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | ≈ 0.00 | ≈ 1.00 | ≈ ±0.2 | ≈ 0.5-3 | ≈ -1.7 | ≈ +1.7 |
| ETHUSDT | ≈ 0.00 | ≈ 1.00 | ≈ ±0.2 | ≈ 0.5-3 | ≈ -1.7 | ≈ +1.7 |
| LINKUSDT | ≈ 0.00 | ≈ 1.00 | ≈ ±0.2 | ≈ 0.5-3 | ≈ -1.7 | ≈ +1.7 |
| LTCUSDT | ≈ 0.00 | ≈ 1.00 | ≈ ±0.2 | ≈ 0.5-3 | ≈ -1.7 | ≈ +1.7 |
| DOTUSDT | ≈ 0.00 | ≈ 1.00 | ≈ ±0.2 | ≈ 0.5-3 | ≈ -1.7 | ≈ +1.7 |

Deviation > 0.1 from mean=0 or > 0.15 from std=1 → INVESTIGATE (z-score normalization is misspecified; possibly the 90-bar window is too short for that symbol's skewness regime persistence). Deviation > 0.2 → ABORT pre-launch.

### 2.4 — `analysis/iteration_v1-047/ic_orthogonality_top5.csv` (F5 input — high-conjecture pairs)

Pre-EDA pairwise Pearson IC (lag-0, pooled across 5 symbols, sample-weighted by per-symbol IS row count). The 5 highest-conjectured-correlation existing features:

| existing feature | family | conjectured \|IC\| | hard \|IC\| ceiling for F5 PASS |
|---|---|---:|---:|
| `stat_skew_20` | statistical (3rd moment, raw form) | 0.30-0.60 | < 0.50 (strict); [0.50, 0.60] → PROMISING-WITH-CORRELATED-PRIMITIVE escalation; ≥ 0.60 → ABORT |
| `stat_kurtosis_20` | statistical (4th moment) | 0.15-0.40 | < 0.50 |
| `vol_atr_14` | volatility (2nd moment) | 0.10-0.30 | < 0.50 |
| `vol_natr_14` | volatility (normalized 2nd moment) | 0.10-0.30 | < 0.50 |
| `vol_bb_bandwidth_20` | volatility (2nd-moment range) | 0.10-0.30 | < 0.50 |

**Critical pair** (Section 3 detail): `stat_skew_20` is the algebraic-sister primitive. The hypothesis pivots on the regime-vs-level distinction; IC > 0.50 against `stat_skew_20` triggers explicit PROMISING-WITH-CORRELATED-PRIMITIVE subtype framing per Section 8.

### 2.5 — `analysis/iteration_v1-047/ic_orthogonality_full_44.csv` (F5 input — full sweep)

44 rows; one per V1_FEATURE_COLUMNS_PRUNED feature. The **max |IC| over all 44 rows** is the F5 gate input.

Expected: max |IC| ∈ [0.30, 0.55] vs `stat_skew_20`; all other pairs |IC| < 0.40.

### 2.6 — Verifier-source IS-window assertion

```python
# All Section 2 EDA scripts include this assertion before any compute:
from crypto_trade.config import OOS_CUTOFF_MS
df_is = df[df['open_time'] < OOS_CUTOFF_MS].copy()
assert df_is['open_time'].max() < OOS_CUTOFF_MS, "IS-window violation"
# Output: scripts pass --is-only and refuse to read out_of_sample/ paths
```

No OOS data touched. Section 9 lists the 5 deliverables verbatim.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration**: **NORMAL-RISK**.

**Reason**: This is a feature-ADDITION iteration. The Optuna training objective (`sharpe`) is UNCHANGED. The training window (24 months) is UNCHANGED. The symbol universe (5-cohort BTC/ETH/LINK/LTC/DOT) is UNCHANGED. The model architecture (4-model LightGBM 5-seed ensemble, A/C/D/E) is UNCHANGED. Only the `feature_columns` argument expands from 44 → 45. The HIGH-RISK criterion (axis changes Optuna's training-objective domain) explicitly enumerates feature-set REPLACEMENT, not feature ADDITION. Feature addition does not change Optuna's objective; it expands its input space by 1 dimension.

**Mitigation (NORMAL-RISK; informational)**: F4 ADF + F5 IC pre-launch gates protect against pathological additions (non-stationary feature OR high-IC duplicate). If F4 or F5 hard-fails pre-launch, the brief is REVISED before Phase 6 dispatch — no backtest runs on a feature that violates the V1_FEATURE_COLUMNS_PRUNED stationarity-or-orthogonality invariants.

**Multi-seed disposition**: single-seed (--seeds 1) per EXPLORATION default. If /047 PROMISING, /048 multi-seed-validates at 10-seed CONFIRMATION budget. If 3+ HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas in a row (the v1 codified escalation), the next HIGH-RISK iteration becomes mandatorily multi-seed. /047 is NORMAL-RISK so this does not apply.

---

## Section 3 — Proposed Changes

### 3.1 — `src/crypto_trade/features_v1/statistical_v1.py` (NEW module)

**New file**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features_v1/statistical_v1.py`

Mirrors the v1 track-isolation pattern established by `composed_v1.py`, `funding_v1.py`, `basis_v1.py`, `open_interest_v1.py`. Houses the rolling-skew z-score computation independently — keeps the composed_v1 module pinned to its current `regime_momentum_signed_5d` semantic.

Exports:

```python
# src/crypto_trade/features_v1/statistical_v1.py

"""v1 statistical higher-moment features — iter-v1/047 (feature-family EXPLORATION cycle-6 2/10).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``skew_zscore_21``: rolling-21bar realized skewness, z-normalized over rolling 90 bars.

Past-only discipline verified by test_iteration_v1_047::test_past_only.
ADF stationarity per-symbol verified by Section 2.2 EDA artifact.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import scipy.stats as st


def compute_skew_zscore_21(
    df: pd.DataFrame, skew_window: int = 21, znorm_window: int = 90
) -> pd.DataFrame:
    """Append ``skew_zscore_21`` to df. Past-only. Returns df with column added."""
    log_returns = np.log(df["close"].astype(float) / df["close"].astype(float).shift(1))
    skew_series = log_returns.rolling(window=skew_window, min_periods=skew_window).apply(
        lambda x: st.skew(x, bias=False), raw=True
    )
    skew_mean = skew_series.rolling(window=znorm_window, min_periods=znorm_window).mean()
    skew_std = skew_series.rolling(window=znorm_window, min_periods=znorm_window).std()
    df["skew_zscore_21"] = (skew_series - skew_mean) / skew_std
    return df


def add_statistical_v1_features(
    df: pd.DataFrame, skew_window: int = 21, znorm_window: int = 90
) -> pd.DataFrame:
    """Registry wrapper. Called by features registry via --groups statistical_v1."""
    return compute_skew_zscore_21(df, skew_window=skew_window, znorm_window=znorm_window)


__all__ = ["compute_skew_zscore_21", "add_statistical_v1_features"]
```

### 3.2 — `src/crypto_trade/features_v1/__init__.py` (modify)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features_v1/__init__.py`

Changes:

1. **ADD** `skew_zscore_21` to `V1_FEATURE_COLUMNS_PRUNED` (alphabetical insertion between `stat_skew_20` and `trend_adx_14`):

```python
# ...
    "stat_log_return_1",
    "stat_return_5",
    "stat_skew_20",
    "skew_zscore_21",  # iter-v1/047: NEW — rolling-skew z-score (regime higher-moment)
    "trend_adx_14",
# ...
```

   Wait — `stat_skew_20` already comes before `skew_zscore_21` alphabetically ONLY if we count "skew" letter-by-letter against "stat". Since the existing block is alphabetically sorted by raw column name, **`skew_zscore_21`** sorts BEFORE `stat_*` (because `'k' < 't'`). Corrected insertion: after `regime_momentum_signed_5d` and before `stat_autocorr_lag5`:

```python
    "regime_momentum_signed_5d",
    "skew_zscore_21",  # iter-v1/047: NEW — rolling-skew z-score (regime higher-moment)
    "stat_autocorr_lag5",
```

2. **UPDATE** the count assertion:

```python
# iter-v1/047: extended 44 → 45 by adding skew_zscore_21 (rolling-skew z-score
#              regime higher-moment; cycle-6 feature-family EXPLORATION 2/10).
assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 45 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)
```

3. **V1_FEATURE_COLUMNS** (193-col superset): UNCHANGED if `skew_zscore_21` is computed into a NEW group (`statistical_v1`) and the parquet writer adds it to the parquet column list automatically. Alternatively, if the v1 superset list is statically defined to mirror live/models.BASELINE_FEATURE_COLUMNS, the new column must be appended there too. **Decision**: keep V1_FEATURE_COLUMNS scoped to the legacy 193-col BASELINE_FEATURE_COLUMNS (re-exported, not redefined here). The new feature lives in the parquet via the registry but is NOT in V1_FEATURE_COLUMNS — only in V1_FEATURE_COLUMNS_PRUNED, which is what the runner pins to `feature_columns=` argument. This preserves backward-compatibility with the 186 historical iterations.

   Optional: extend V1_FEATURE_COLUMNS tuple with `"skew_zscore_21"` if Engineering finds the runner needs it for any superset-driven path. Default disposition: NO change to V1_FEATURE_COLUMNS unless Engineering documents a reason.

4. **V1_OOD_FEATURE_COLUMNS**: UNCHANGED. Adding `skew_zscore_21` to the OOD Mahalanobis gate would be a second axis change in the same iteration — deferred to /048+ if /047 PROMISING.

### 3.3 — `src/crypto_trade/features/__init__.py` (modify; new group registration)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features/__init__.py`

Register the new `statistical_v1` group (mirrors `funding_v1` / `open_interest_v1` / `basis_v1` / `composed_v1` patterns):

```python
# After existing _register calls (lines 207-219):
from crypto_trade.features_v1.statistical_v1 import (  # noqa: E402
    add_statistical_v1_features as _add_statistical_v1_features,
)
_register("statistical_v1", _add_statistical_v1_features)  # iter-v1/047
```

### 3.4 — Feature regen command

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --format parquet \
  --workers 4 \
  --groups statistical_v1
```

This re-computes ONLY the new `skew_zscore_21` column and writes it to each symbol's v1 parquet, merging with existing columns. **Runtime estimate**: < 2 minutes across all 5 symbols (O(N) rolling skew on ~3000 candles per symbol).

If the registry dispatch must touch all features (some workers re-run the full group registry), the full feature regen command is:

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --format parquet \
  --workers 4
```

This re-computes ALL 11 v1 feature groups in ~25-30 min. Engineering chooses the appropriate path; the partial-regen `--groups statistical_v1` path is preferred for /047 to keep the wall-clock budget tight.

### 3.5 — `run_baseline_v186.py` invocation (Phase 6 backtest)

Runner uses the standard v1 EXPLORATION dispatch with explicit feature-column pinning:

```bash
uv run python run_baseline_v186.py \
  --exploration \
  --iteration-label v1-047 \
  --n-trials 18 \
  --seeds 1 \
  --ensemble-size 3 \
  --feature-columns "/home/roberto/crypto-trade/.worktrees/quant-research/analysis/iteration_v1-047/feature_columns.json"
```

Where `feature_columns.json` is a committed JSON file containing the 45-element list = `list(V1_FEATURE_COLUMNS_PRUNED)` after the /047 source change. **Critical**: the runner MUST receive the explicit 45-element list at invocation time. If the runner imports `V1_FEATURE_COLUMNS_PRUNED` directly (current behavior in `run_baseline_v186.py`), the JSON file is redundant — Engineering picks ONE source-of-truth path. Default: rely on the import (the JSON path is the fallback used by other tracks).

Output paths:
- `reports-v1/iteration_v1-047/in_sample/` — IS trades + per-month equity + Optuna trial logs
- `reports-v1/iteration_v1-047/out_of_sample/` — OOS trades + per-month equity
- `reports-v1/iteration_v1-047/comparison.csv` — IS / OOS daily Sharpe / Sortino / MaxDD / WR / PF / trade-count vs BASELINE_V1
- `reports-v1/iteration_v1-047/feature_importance.csv` — `skew_zscore_21` rank per cohort (A/C/D/E) + portfolio-level gain-weighted aggregate
- `reports-v1/iteration_v1-047/run.log` — Optuna trial-by-trial log

### 3.6 — Tests (new file)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/tests/test_iteration_v1_047.py`

Tests required:

```python
"""Tests for iter-v1/047: skew_zscore_21 feature dispatch."""
import numpy as np
import pandas as pd
import pytest
from crypto_trade.features_v1.statistical_v1 import compute_skew_zscore_21
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def test_v1_pruned_has_45_features():
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45
    assert "skew_zscore_21" in V1_FEATURE_COLUMNS_PRUNED


def test_past_only():
    """skew_zscore_21[t] does not use close[t+k] for any k > 0."""
    # Construct df with close[t] linear; perturb close[T] for T at the end;
    # confirm skew_zscore_21[T-1] is UNCHANGED before vs after the perturbation.
    rng = np.random.default_rng(42)
    base = 100 + rng.normal(0, 1, size=300).cumsum()
    df1 = pd.DataFrame({"close": base.copy()})
    df1 = compute_skew_zscore_21(df1)
    df2 = pd.DataFrame({"close": base.copy()})
    df2.loc[df2.index[-1], "close"] = base[-1] * 10  # perturb FINAL bar only
    df2 = compute_skew_zscore_21(df2)
    # All values up to index -2 must be unchanged.
    pd.testing.assert_series_equal(
        df1["skew_zscore_21"].iloc[:-1], df2["skew_zscore_21"].iloc[:-1],
        check_names=False,
    )


def test_warmup_nan():
    """First 110 bars (21 + 90 - 1) are NaN."""
    rng = np.random.default_rng(42)
    base = 100 + rng.normal(0, 1, size=300).cumsum()
    df = compute_skew_zscore_21(pd.DataFrame({"close": base}))
    assert df["skew_zscore_21"].iloc[:109].isna().all()
    assert df["skew_zscore_21"].iloc[110:].notna().any()


def test_zscore_normalization_approximate():
    """Post-warmup mean ≈ 0, std ≈ 1 across long series."""
    rng = np.random.default_rng(42)
    base = 100 + rng.normal(0, 0.02, size=5000).cumsum()
    df = compute_skew_zscore_21(pd.DataFrame({"close": base}))
    post = df["skew_zscore_21"].iloc[110:].dropna()
    assert abs(post.mean()) < 0.2, f"mean drift: {post.mean()}"
    assert 0.7 < post.std() < 1.5, f"std drift: {post.std()}"


def test_track_isolation():
    """Module does not import from features_v2 or features_v3."""
    import inspect
    from crypto_trade.features_v1 import statistical_v1
    src = inspect.getsource(statistical_v1)
    assert "features_v2" not in src
    assert "features_v3" not in src
```

### 3.7 — LM Master Phase 4.5 response map

LM Master pre-design advisory at Phase 4.5 (`briefs-v1/iteration_v1-047/lgbm_advisor.md`) is invoked AFTER this brief draft and BEFORE Phase 5.5 gate. The brief addresses each LM Master recommendation here once issued. Provisional placeholder rows (this brief revision will be updated post-LM-Master):

| LM Master recommendation | Adoption status | Brief reference |
|---|---|---|
| (TBD HP rec #1) | TBD | TBD |
| (TBD HP rec #2) | TBD | TBD |
| (TBD HP rec #3) | TBD | TBD |
| (TBD HP rec #4) | TBD | TBD |
| (TBD feature engineering rec #1) | TBD | TBD |
| (TBD feature engineering rec #2) | TBD | TBD |

**Pre-emptive responses** to anticipated LM Master recommendations:

| Anticipated recommendation | Expected QR response |
|---|---|
| Raise `colsample_bytree` upper bound (e.g., 0.85+) given NEW feature | **ADOPT** if recommended — a 45th feature deserves more sampling probability. Engineering implements via Optuna search-space upper-bound bump. |
| Raise `feature_fraction` upper bound | **ADOPT** if recommended (same reasoning). |
| Tighten `min_data_in_leaf` lower bound for higher-resolution feature use | **MODIFY/DISCUSS** — risks overfit at v1's Optuna budget. Default REJECT unless LM Master provides specific lower bound. |
| Add SHAP cluster check at Phase 6 to confirm `skew_zscore_21` is non-redundant with `stat_skew_20` | **ADOPT** — Engineering report Section 9 includes SHAP pairwise importance dispersion between the two features. |
| Add a 2nd higher-moment feature in same iteration (e.g., realized kurtosis z-score, semi-variance) | **REJECT** — single-feature-at-a-time per v3 `engineered_features_dont_stack` rule extended to v1 by analogy. /048 considers kurtosis-z-score if /047 PROMISING. |
| Replace `stat_skew_20` with `skew_zscore_21` (SWAP not ADD) | **REJECT** — /047 must isolate the ADD effect; SWAP confounds add+drop signal. If F1 PASS + F5 borderline IC, /048 considers head-to-head SWAP. |

Final adoption matrix populated after Phase 4.5 LM Master advisor file commits.

### 3.8 — Wall-clock budget summary

| Phase | Wall-clock | Notes |
|---|---|---|
| Pre-EDA Section 2 deliverables (committed scripts + CSVs) | 10-15 min | scipy rolling skew + ADF + IC on IS-only data |
| Feature regen (`--groups statistical_v1` partial) | < 2 min | O(N) rolling on 5 symbols × ~3000 candles |
| Optuna backtest (4 cohorts × monthly retrain × 18 trials × 1 seed × ENSEMBLE_SIZE=3) | ≤ 2h | EXPLORATION default per v1; +1 feature dim adds ~5% search-space, no trial-count change |
| Reports + comparison.csv + diary + closeout | 15-20 min | standard /034-/046 cadence |
| **Total** | **≤ 2.5h** | Wall-clock cap 2h HARD on backtest phase; total 2.5h HARD |

If backtest exceeds 2h at the 80% wall-clock mark, abort and triage. /047 is EXPLORATION; signal extraction should not exceed EXPLORATION budget.

---

## Section 4 — Pre-Registered Failure-Mode Falsifiers (F-AXIS #1 through #5)

### F-AXIS #1 — Master falsifier (DUAL CONDITION: importance + Sharpe)

**Claim**: `skew_zscore_21` ranks in **TOP-15 of 45** features by mean-gain importance at the portfolio-aggregated level (gain-weighted average across Models A/C/D/E, weighted by per-model IS trade count) AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767 (i.e., observed IS daily Sharpe ≥ +0.5267).

**Why dual gate**:
- **Importance without Sharpe lift** → LightGBM uses the feature mechanically without gaining net signal. This is the iter-v3/019 `funding_rate_zscore_30` PROMISING-INERT failure mode generalized: even when importance rank is high, if IS Sharpe is flat, the feature is informationally redundant with existing features.
- **Sharpe lift without importance** → the lift is attributable to Optuna basin-lottery noise on the existing 44 features, NOT the new feature. The new feature is a passenger; the lift would happen even without it.

The dual gate prevents both false-positive patterns. Lifted directly from v3's `engineered_features_proven` precedent: iter-v3/025 `regime_momentum_signed_5d` produced 51% top importance AND IS +0.50 / OOS +0.84 vs anchor — dual evidence is the standard.

**Status**: MASTER falsifier. F1 PASS → PROMISING (subtype determined by F2/F5). F1 FAIL (either or both conditions fail) → routed to F-AXIS #2 / #3 verdict subtypes.

### F-AXIS #2 — IS Sharpe Δ band (PROMISING-CLEAN vs NEG-INERT vs NEG-CLEAN)

**Claim**: 3-band classification:

| IS daily Sharpe Δ vs BASELINE_V1 (+0.4767) | Verdict subtype |
|---|---|
| ≥ +0.05 | **PROMISING-CLEAN** (if F5 PASS with max \|IC\| < 0.50) OR **PROMISING-WITH-CORRELATED-PRIMITIVE** (if F5 borderline 0.50 ≤ \|IC\| ≤ 0.60 with `stat_skew_20`) |
| -0.05 < Δ < +0.05 | **NEG-INERT** — feature is tied to baseline within noise; informational drop. Inventory ground-truth: asymmetric-tail z-score is reflected enough in `stat_skew_20` already; trees do not gain edge. Retire `skew_zscore_21` to V1_RETIRED_FEATURE_COLUMNS. |
| ≤ -0.05 | **NEG-CLEAN** — feature actively harms IS. v3 `inert_features_at_higher_budget` analogue: a mechanically-correlated INERT feature can ACTIVELY harm OOS by reorganizing the loss surface to non-signal regions. Retire + new feedback rule candidate. |

**Interpretation if FAIL into NEG-INERT**: file `skew_zscore_21` under V1_RETIRED_FEATURE_COLUMNS like basis_zscore_30 was at /040. Document in diary that the regime form of skewness is informationally subsumed by `stat_skew_20` at v1's EXPLORATION Optuna budget.

**Interpretation if FAIL into NEG-CLEAN**: same routing + new feedback rule "rolling-z-score of an existing same-family primitive is NOT additive at v1's 18-trial EXPLORATION budget"; confirmation pending at /048+.

### F-AXIS #3 — OOS Δ (forensic-only; NOT a verdict gate)

**Claim**: OOS daily Sharpe Δ vs BASELINE_V1 (+1.1913) is REPORTED in comparison.csv but is NOT a /047 success criterion. /046 PROMISING-DIVERGENCE established that OOS-aware selection is a leak path; /047 preserves that discipline.

**Status**: Forensic only. **Critic Phase 7.5 CANNOT cite OOS Sharpe Δ < +0.05 as a /047 failure mode.** OOS is logged for /048+ priors and for the eventual CONFIRMATION run.

This mirrors /046's F4 / /045's F4 forensic-only OOS treatment per the IS/OOS divergence regime feedback rule + the 2026-05-31 user directive on relative-regime Pareto-dominance.

### F-AXIS #4 — ADF Stationarity (PRE-LAUNCH gate)

**Claim**: `skew_zscore_21` is stationary across all 5 v1 symbols (BTC/ETH/LINK/LTC/DOT) at the IS-window upper bound — ADF p-value < 0.05 with `regression='c'` (constant trend), `maxlag=10`. Evaluated PRE-LAUNCH from `analysis/iteration_v1-047/adf_stationarity_per_symbol.csv` (Section 2.2).

**Outcomes**:
- 5/5 PASS → V1_FEATURE_COLUMNS_PRUNED stationarity invariant preserved (extends /021 audit's 40/40 → 45/45). Brief notes the property in Section 9. **Proceed to launch.**
- 4/5 PASS → INVESTIGATE the failing symbol. If borderline (p ∈ [0.05, 0.10]), document and proceed with explicit caveat. If hard fail (p > 0.10), redesign the 90-bar window for that symbol OR mask that symbol's `skew_zscore_21` column to NaN (effectively excluding it from training for that symbol).
- ≤ 3/5 PASS → ABORT pre-launch. The 90-bar z-score normalization is inadequate for high-vol regimes; redesign required.

**Rationale**: The pruned-feature stationarity invariant was a hard property of the /021 pruning campaign; all subsequent ADD/DROP/SWAP operations (basis_zscore_30 at /034, regime_momentum_signed_5d at /040, etc.) preserved it. /047 must not break it.

### F-AXIS #5 — IC Orthogonality (PRE-LAUNCH gate)

**Claim**: max absolute pairwise Pearson IC (lag-0, pooled across 5 symbols, sample-weighted) of `skew_zscore_21` vs ALL 44 existing features in V1_FEATURE_COLUMNS_PRUNED is < 0.50. Evaluated PRE-LAUNCH from `analysis/iteration_v1-047/ic_orthogonality_full_44.csv` (Section 2.5).

**Outcomes**:
- max \|IC\| < 0.50 across all 44 features → **ORTHOGONAL OK**. Proceed to launch as PROMISING-CLEAN candidate.
- max \|IC\| ∈ [0.50, 0.60] AND the offending feature is `stat_skew_20` ONLY → **ESCALATE** to PROMISING-WITH-CORRELATED-PRIMITIVE subtype framing in Section 8. Proceed to launch; F1 dual-gate is the disambiguator (a feature can be 0.55 |IC| with `stat_skew_20` AND still rank top-15 AND produce IS Δ ≥ +0.05 — that pattern means the regime form IS extracting incremental signal beyond the level form).
- max \|IC\| ∈ [0.50, 0.60] with ANY OTHER feature → **ESCALATE BLOCK-PENDING-FIX** — investigate why a non-skew feature correlates with the skew-z-score. Likely a computation bug; redesign required.
- max \|IC\| ≥ 0.60 vs ANY feature → **ABORT** pre-launch. The feature is mechanically duplicative; the regime form does not survive orthogonality.

**Rationale**: The /021 pruning campaign retained features with low pairwise IC; preserving that invariant prevents wasted `colsample_bytree` picks. iter-v2/070 lesson: high-IC redundant features steal split-budget from genuinely orthogonal features (the univariate-Spearman trap).

### Falsifier summary table

| F-AXIS | Type | Phase | Gate | Failure routes to |
|---|---|---|---|---|
| F1 | Master (dual) | Phase 7 | Top-15 importance AND IS Δ ≥ +0.05 | F2 subtype routing |
| F2 | IS Sharpe band | Phase 7 | -0.05 < Δ < +0.05 OR Δ ≤ -0.05 | NEG-INERT / NEG-CLEAN retire |
| F3 | OOS (forensic only) | Phase 7 | No gate (informational) | Logged in diary; not a verdict gate |
| F4 | ADF stationarity | Phase 5 (pre-launch) | 5/5 PASS @ p < 0.05 | INVESTIGATE / REDESIGN / ABORT pre-launch |
| F5 | IC orthogonality | Phase 5 (pre-launch) | max \|IC\| < 0.50 | ESCALATE / BLOCK-PENDING-FIX / ABORT pre-launch |

---

## Section 5 — Methodology Integrity

### 5.1 — Look-ahead audit

- Feature definition uses **past-only** rolling windows; verified by `test_iteration_v1_047::test_past_only`.
- Decision at candle `t+1` consumes `skew_zscore_21[t]` (the bar-close value at t, where `skew_21bar[t]` and `skew_mean/std_90[t]` use bars ending at t inclusive).
- No CSV-level peek at OOS data during EDA: `assert df['open_time'].max() < OOS_CUTOFF_MS` in every Section 2 script.

### 5.2 — Embargo / purge

- v1 walk-forward CV `walk_forward.py:113` is `train_end_ms = test_start_ms - embargo_ms` (the fixed-2026-05-12 implementation). /047 inherits this — no change.
- The new feature does NOT introduce a new max-label-horizon parameter. Inherited triple-barrier label parameters (atr_tp / atr_sl per BASELINE_V1) are UNCHANGED. Embargo budget unchanged.

### 5.3 — DSR / PSR / PBO

- EXPLORATION mode: DSR / PSR are STRUCTURAL ARTIFACTS at n_trials=18, --seeds 1 (per v3 `dsr_mode_artifact` rule — EXPLORATION-mode DSR / PSR are INFORMATIONAL ONLY, not MERGE gates). Reported in `comparison.csv` for forensic continuity but NOT cited as edge-significance evidence.
- CONFIRMATION-mode DSR > 0.95 gate evaluation deferred to /048+ if /047 PROMISING.
- PBO via CSCV: standard v1 walk-forward emits PBO; reported informationally. PBO < 0.4 is the MERGE-time gate; EXPLORATION is informational.

### 5.4 — Regime attribution

- Section 10 covers per-regime IS / OOS PnL attribution (bull / bear / chop / vol-spike / recovery / other tagger). Standard v1 `regime_attribution.csv` emission via `run_baseline_v186.py`.

### 5.5 — Reproducibility checksum

- Engineering report emits SHA256 of `feature_columns.json` + `V1_FEATURE_COLUMNS_PRUNED` source-of-truth in `src/crypto_trade/features_v1/__init__.py`. Catalogued in `briefs-v1/exploration_catalog.md` row.

### 5.6 — Hypothesis-implementation alignment (Critic Check 8 equivalent)

- Hypothesis: ADD `skew_zscore_21` to `V1_FEATURE_COLUMNS_PRUNED` (44 → 45).
- Implementation: `git diff main src/crypto_trade/features_v1/__init__.py src/crypto_trade/features_v1/statistical_v1.py src/crypto_trade/features/__init__.py` must show exactly: NEW file `statistical_v1.py` + INSERT one line in V1_FEATURE_COLUMNS_PRUNED + count assertion 44 → 45 + register `statistical_v1` group in features registry.
- No OTHER axis changes (no risk-gate modification, no labeling change, no universe modification, no model architecture change). Critic Phase 6.0 + Phase 7.5 verifies via diff.

### 5.7 — Critic Check 14 (axis-family match-to-diff)

- Declared axis family: `feature-family`.
- Source diff must show: feature addition only (statistical_v1.py + V1_FEATURE_COLUMNS_PRUNED insert + features registry register). No labeling diff, no risk-primitive diff, no universe diff, no model-arch diff.
- Critic Phase 7.5 Check 14 verifies declared family matches actual diff. PASS expected.

---

## Section 6 — Risk Mitigation

### 6.1 — Inherited BASELINE_V1 risk gates (NO CHANGE)

- **R1 (Consecutive-SL Cooldown)**: K=3, C=27 candles. Applies to Models C/D/E. Model A unchanged (disabled per IS analysis showing late-streak BTC+ETH trades have better edge).
- **R2 (Drawdown-triggered Position Scaling)**: Applies only to Model E; floor 0.33, trigger 7% per-model DD.
- **R3 (OOD Mahalanobis Gate)**: 70th-percentile cutoff; 16 scale-invariant features per `V1_OOD_FEATURE_COLUMNS`. **NOT EXTENDED to skew_zscore_21**; that would be a second axis change at the same iteration.

### 6.2 — F4/F5 pre-launch protective gates (R-NEW for /047)

- F4 ADF stationarity gate: PRE-LAUNCH. ≤3/5 PASS → ABORT pre-launch. Protects V1_FEATURE_COLUMNS_PRUNED stationarity invariant.
- F5 IC orthogonality gate: PRE-LAUNCH. max \|IC\| ≥ 0.60 → ABORT pre-launch. Protects feature-surface orthogonality invariant.

### 6.3 — NEG-CLEAN routing if active harm

- F2's NEG-CLEAN band (Δ ≤ -0.05) triggers: (a) retire `skew_zscore_21` to V1_RETIRED_FEATURE_COLUMNS; (b) candidate new feedback rule "rolling-z-score of an existing same-family primitive is NOT additive at v1's 18-trial EXPLORATION budget"; (c) document in diary's `Lessons` section.

### 6.4 — Wall-clock kill switch

- Phase 6 backtest > 2h wall-clock → abort and triage. EXPLORATION budget HARD cap.

### 6.5 — IS-calibrated thresholds with simulated effect

- F1 importance threshold (TOP-15 of 45): calibrated against /045 mean-gain audit, which showed the top-15 current features capture ~70-80% of total information gain. A NEW feature ranking outside top-15 has empirically zero predictive utility at v1's Optuna budget (v3/019 funding_rate_zscore_30 INERT pattern: rank 14/14, contributed <2% gain → catastrophic OOS at higher budget). Simulated effect: if `skew_zscore_21` ranks rank 16+ but IS Δ < +0.05, NEG-INERT routing prevents adding a passenger feature to the pruned set.
- F2 IS Sharpe lift floor (+0.05): calibrated against /034-/043 EXPLORATION verdicts (PROMISING-CLEAN verdicts posted IS Δ in [+0.05, +0.15]; /037 Sortino IS +0.10; /040 regime_momentum_signed_5d IS +0.06). +0.05 is the meaningful-signal-above-noise threshold.

### 6.6 — Concentration cap

- BASELINE_V1 concentration is governed at the per-symbol level by R1 cool-down (after 3 consec SLs); the 30%-of-OOS-PnL cap is a MERGE-time gate, not EXPLORATION. /047 inherits BASELINE_V1's concentration profile unchanged. Top-symbol concentration is reported in `comparison.csv` for forensic continuity.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

### 7.1 Verdict band priors

| Outcome | Prior | Reasoning |
|---|---:|---|
| **PROMISING-CLEAN** (F1 PASS AND F5 PASS strict <0.50) | **20-25%** | Asymmetric tail is a real edge in crypto (Karagiorgis 2024); z-score regime form has not been tested at v1's 8h cadence; the absence of any z-scored higher-moment in V1_FEATURE_COLUMNS_PRUNED is a real surface gap. v1 Optuna 18 trials × 1 seed × ENSEMBLE_SIZE=3 has empirically sufficient effective optimization to engage a NEW feature if information is orthogonal. Anchored to /040 regime_momentum_signed_5d PROMISING-CLEAN with IS Δ +0.06. |
| **PROMISING-WITH-CORRELATED-PRIMITIVE** (F1 PASS but F5 \|IC\| ∈ [0.50, 0.60] with `stat_skew_20`) | **10-15%** | The z-scored regime form is a transform of a primitive that already exists. The dual F1 gate is the disambiguator: if rank ≤ 15 AND IS Δ ≥ +0.05 DESPITE \|IC\| > 0.50, the regime form IS extracting incremental signal beyond the level form. Plausible but less likely than CLEAN. |
| **NEG-INERT** (IS Δ ∈ (-0.05, +0.05); rank may exceed 15) | **30-40%** | Inventory ground-truth update: asymmetric-tail z-score is reflected ENOUGH in `stat_skew_20` that trees do not gain edge. v1 has 13 cycle-5+6 iterations on the 44-feature surface; the additive-feature space may be empirically signal-bounded. v3 cycle-7 NEW-feature-family precedent: 9/9 NEGATIVE — strong negative prior on NEW feature additions late in cycle. |
| **NEG-CLEAN** (IS Δ ≤ -0.05; active OOS-side regression possible) | **15-25%** | v3 `inert_features_at_higher_budget` rule analogue: adding a feature mechanically correlated with an existing feature can DIVERT split-budget AWAY from genuinely orthogonal features. If `skew_zscore_21` is in the \|IC\| 0.4-0.6 range with `stat_skew_20`, the tree's split-finding becomes confused. |
| **BLOCK-PENDING-FIX** (F4/F5 pre-EDA gate fails; OR src/ defect at Critic Phase 7.5) | **5-10%** | F4 pre-EDA catches stationarity defect; F5 catches IC defect. Critic Phase 7.5 may find a defect in dispatch (e.g., NaN handling at 110-bar warmup, parquet integration test failure, track-isolation grep). Single-rerun discipline applies. |

### 7.2 Most plausible failure scenario

**NEG-INERT (30-40% prior)** is the modal failure mode: `stat_skew_20` already exists in the pruned set and may informationally subsume the z-score regime form at v1's Optuna budget. The trees' split-finding can build a level-vs-regime split implicitly via depth-2 paths through `stat_skew_20` itself; adding the explicit z-scored form does not give them new information they couldn't already access combinatorially.

Sub-scenario: `skew_zscore_21` ranks rank 16-25 (mid-table importance) AND IS Sharpe Δ ∈ [0.00, +0.04]. The feature is mechanically being used but is not carrying incremental signal — passenger usage. /047 closeout routes to NEG-INERT and retires the feature.

### 7.3 Expected metric signature

| Metric | PROMISING-CLEAN expected | NEG-INERT expected | NEG-CLEAN expected |
|---|---:|---:|---:|
| Importance rank (portfolio) | ≤ 15 | 16-30 | 30-45 or 1-5 (rank doesn't disambiguate; Sharpe does) |
| IS daily Sharpe (vs +0.4767 baseline) | +0.52 to +0.65 | +0.45 to +0.50 | +0.30 to +0.43 |
| OOS daily Sharpe (forensic) | +1.00 to +1.40 | +1.05 to +1.20 | +0.50 to +1.00 |
| Top-symbol concentration | unchanged from baseline (~32-38%) | unchanged | unchanged |
| Trade count (IS / OOS) | within ±10% of baseline | within ±5% | within ±5% |

The OOS signature is highly noisy; the expected ranges are illustrative. Verdict is determined by IS metrics + F1 importance only (per F3 forensic-only discipline).

---

## Section 8 — Pre-Registered Comparison Criteria

### 8.1 — Verdict subtypes (EXPLORATION verdict band)

EXPLORATION verdict at /047 closeout is one of:

1. **PROMISING-CLEAN** — F1 PASS (top-15 importance AND IS Δ ≥ +0.05); F5 PASS strict (max \|IC\| < 0.50). Feature retained in V1_FEATURE_COLUMNS_PRUNED; /048 considers companion higher-moment features (realized kurtosis z-score, semi-variance) at EXPLORATION budget.
2. **PROMISING-WITH-CORRELATED-PRIMITIVE** — F1 PASS but F5 \|IC\| ∈ [0.50, 0.60] with `stat_skew_20`. Feature retained in V1_FEATURE_COLUMNS_PRUNED; /048 considers head-to-head SWAP test (DROP `stat_skew_20`, KEEP `skew_zscore_21`) as a follow-up EXPLORATION. Multi-seed CONFIRMATION uses SHAP / cluster-MDA at Phase 6 to determine which form to retain pre-CONFIRMATION.
3. **NEG-INERT** — IS Δ ∈ (-0.05, +0.05); feature is informationally tied to existing pruned set. Feature retired to V1_RETIRED_FEATURE_COLUMNS. Diary documents inventory ground-truth update.
4. **NEG-CLEAN** — IS Δ ≤ -0.05; feature actively harms IS. Feature retired + candidate new feedback rule "rolling-z-score of existing same-family primitive is NOT additive at v1's 18-trial EXPLORATION budget"; confirmation pending /048+.
5. **BLOCK-PENDING-FIX** — F4 stationarity fail, F5 hard \|IC\| > 0.60, OR src/ defect at Critic Phase 7.5. Single-rerun discipline: one cycle to address the defect, then verdict can only be PASS or BLOCK-FINAL.

### 8.2 — Comparison vs BASELINE_V1 (the anchor; not vs /045 ALT_1 or /046 IS-only substrate)

| Metric | BASELINE_V1 anchor | /047 PROMISING threshold | /047 NEG threshold |
|---|---:|---:|---:|
| IS daily Sharpe | +0.4767 | ≥ +0.5267 (Δ ≥ +0.05) | -0.05 < Δ < +0.05 → NEG-INERT; ≤ -0.05 → NEG-CLEAN |
| OOS daily Sharpe (forensic) | +1.1913 | reported only; not a gate | reported only; not a gate |
| Top-symbol concentration (OOS) | ~32-38% (DOT-heavy by design) | unchanged | unchanged |
| Trade count (IS / OOS) | per BASELINE_V1 | within ±10% (no sudden trade-count compression) | reported |
| `skew_zscore_21` importance rank (portfolio) | n/a | ≤ 15 (F1) | 16+ → routed to F2 subtype |

**Critical**: comparison is vs BASELINE_V1 ONLY (per the v1 anchor convention). /045 ALT_1 (BLOCK-FINAL) and /046 IS-only substrate (PROMISING-DIVERGENCE OOS −0.876) are NOT comparison anchors at /047 — they are forensic-only context.

---

## Section 9 — Library Stack Declaration

### 9.1 Required code artifacts (committed BEFORE Phase 6 backtest launch)

1. `analysis/iteration_v1-047/skew_zscore_21_definition.py` — verbatim pandas formula committed; minimal unit test confirming the formula matches Section 2.1 verbatim.
2. `analysis/iteration_v1-047/adf_stationarity_per_symbol.csv` — F4 input; 5 rows (BTC/ETH/LINK/LTC/DOT); columns `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`.
3. `analysis/iteration_v1-047/distribution_stats_per_symbol.csv` — 5 rows × 10 cols (`symbol, mean, std, skew, kurtosis, p05, p25, p50, p75, p95`).
4. `analysis/iteration_v1-047/ic_orthogonality_top5.csv` — 5 rows × 3 cols (`feature, ic, n_pair`); high-conjecture pairs only.
5. `analysis/iteration_v1-047/ic_orthogonality_full_44.csv` — 44 rows × 3 cols; full V1_FEATURE_COLUMNS_PRUNED sweep. **max(\|IC\|) from this file is the F5 gate input.**
6. `analysis/iteration_v1-047/F4_F5_gate_outcomes.md` — pass/fail per gate with quoted critical values + decision (proceed / escalate / abort).
7. `analysis/iteration_v1-047/feature_columns.json` — committed JSON list of 45 feature names; pinned in the runner invocation as Section 3.5 documents.

### 9.2 Required engineering artifacts (post-Phase 6 backtest)

8. `reports-v1/iteration_v1-047/comparison.csv` — IS / OOS daily Sharpe / Sortino / MaxDD / WR / PF / trade count vs BASELINE_V1.
9. `reports-v1/iteration_v1-047/feature_importance.csv` — `skew_zscore_21` rank per cohort (A/C/D/E) AND portfolio-level gain-weighted aggregate.
10. `reports-v1/iteration_v1-047/regime_attribution.csv` — per-regime IS/OOS PnL attribution.
11. `reports-v1/iteration_v1-047/integration_smoke_test.md` — confirms (a) `len(V1_FEATURE_COLUMNS_PRUNED) == 45`; (b) runner pins explicit 45-element list; (c) `tests/test_iteration_v1_047.py` passes; (d) track-isolation grep returns empty; (e) `pytest tests/` all passes.

### 9.3 Library / framework pinning

- scipy ≥ 1.13 for `scipy.stats.skew(x, bias=False)` G1 estimator.
- pandas / numpy version inherited from `pyproject.toml` lockfile.
- LightGBM version inherited (no upgrade at /047).
- statsmodels for ADF (`statsmodels.tsa.stattools.adfuller`).

### 9.4 Test path

`/home/roberto/crypto-trade/.worktrees/quant-research/tests/test_iteration_v1_047.py` — Section 3.6 above.

---

## Section 10 — Regime Attribution Plan

### 10.1 Per-regime IS Sharpe table (Phase 6 output)

Per the v1 `regime_attribution.csv` schema. Reported regimes: bull, bear, chop, vol-spike, recovery, other.

| Regime | IS sample (target) | Cand IS Sharpe (target) | Cand IS Trades (target) | Baseline IS Sharpe | IS Δ vs baseline | Comment |
|---|---|---:|---:|---:|---:|---|
| bull | IS | ≥ -0.35 + 0.05 = -0.30 | ~50-65 | -0.35 | ≥ +0.05 (PROMISING IF improves) | Asymmetric tail z-score should ESPECIALLY help in bull regimes — heavy positive-skew tails are signature of bull markets |
| bear | IS | ≥ +0.15 + 0.05 = +0.20 | ~200-230 | +0.15 | ≥ +0.05 | Negative-skew detection in bear regimes — skew_zscore < -2 should fire as a bear-confirmation regime indicator |
| chop | IS | ≥ +0.23 + 0.00 = +0.23 | ~220-240 | +0.23 | ≥ 0 (neutral OK) | Chop regimes have low absolute skewness; z-score should not move signals heavily |
| vol-spike | IS | n/a (tagger limitation) | 0 | n/a | n/a | Regime never tagged at IS — tagger artifact |
| recovery | IS | ≥ +0.28 + 0.05 = +0.33 | ~100-130 | +0.28 | ≥ +0.05 | Recovery regimes mix bear-skew → bull-skew transitions; z-score crossings should fire |
| other | OOS | n/a (most OOS regimes collapse to "other" per /046 finding) | varies | n/a | n/a | Regime tagger OOS-degenerate documented in /046 |

**Critical**: per-regime IS metrics are FORENSIC; the verdict gate is F1 (master) + F2 (band). Per-regime Pareto-relaxed test is the /045 multi-regime convention and applies at CONFIRMATION, not EXPLORATION.

### 10.2 Specialist-mechanism classification (per /041 closeout convention)

Pre-EDA conjecture for /047's specialist mechanism:

- **Type**: hypothesized **type-A IS-strong** (asymmetric-tail signal is most informative for trade-direction selection in IS; OOS transferability uncertain).
- **Risk facet**: **Sharpe-maximizer** (the new feature targets cleaner trade-direction at IS; not a DD-minimizer or Sortino-shaper primary purpose).
- **Regime profile**: hypothesized to most help in **bull + recovery** (positive-skew regime confirmation) and **bear** (negative-skew regime confirmation). Chop / vol-spike unclear.

Updated post-EDA in diary.

### 10.3 Regime attribution emission

`run_baseline_v186.py` emits `regime_attribution.csv` automatically. Engineering report Section 9 references this file's path explicitly.

---

## End of Brief

**Phase 5 author**: QR (Phase 5).
**Date**: 2026-06-01.
**Status**: AUTHORED — awaiting Phase 5.5 gate verification (axis rotation valid, LM Master responses addressed, F4/F5 pre-launch gates pre-registered) + Phase 6.0 Critic pre-flight (axis-family match, track isolation, src/ diff bounded).

**Phase 5.5 gate checklist** (operator):
- [ ] Section 0.6 axis-rotation declared VALID (this brief: YES — `feature-family` not in prior 5)
- [ ] Section 2.5 HIGH-RISK declaration explicit (this brief: NORMAL-RISK + reason)
- [ ] Section 3.7 LM Master responses populated (this brief: AWAITING LM Master Phase 4.5 advisor)
- [ ] Section 4 falsifiers pre-registered with numeric thresholds (this brief: YES — F1-F5)
- [ ] Section 9 deliverables committed BEFORE Phase 6 launch (this brief: 7 pre-Phase-6 artifacts enumerated)
- [ ] Section 5.6 hypothesis-implementation alignment specifiable as a `git diff` (this brief: YES — see Section 5.7)

**Phase 6.0 Critic pre-flight checklist**:
- [ ] Track isolation grep returns empty for both `features_v2` and `features_v3` imports in `src/crypto_trade/features_v1/statistical_v1.py`
- [ ] `tests/test_iteration_v1_047.py` passes locally before backtest launch
- [ ] `V1_FEATURE_COLUMNS_PRUNED` count assertion updated 44 → 45
- [ ] `feature_columns.json` SHA256 matches `list(V1_FEATURE_COLUMNS_PRUNED)` at HEAD
- [ ] F4 ADF artifact 5/5 PASS (or 4/5 with documented investigation; ≤ 3/5 → ABORT pre-launch)
- [ ] F5 IC orthogonality artifact max \|IC\| < 0.60 (and < 0.50 for CLEAN routing)

If any pre-launch gate fails → brief revised before Phase 6 dispatch; no backtest runs on a pathological feature addition.

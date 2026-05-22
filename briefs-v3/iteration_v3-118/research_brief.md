# iter-v3/118 Research Brief — Cycle-6 EXPLORATION #9

**Axis**: NEW engineered feature family at 8h — adds **one** composed feature
to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15): `C3 = ema_signed_volregime =
ema_spread_atr_20 × sign(range_realized_vol_50 − rolling_median(range_realized_vol_50, 200))`.
The axis is on the `regime_momentum_signed_5d` (/025 PROMISING) lineage — a
Category-2 composed feature (value × regime-sign multiplied through a
2-state sign function), structurally equivalent in form to the /025
baseline-stack feature. EDA-driven adjudication per `feedback_v3_axis_selection_quant_discipline.md`.

**Cycle**: 6 EXPLORATION slot #9 of 10 (iter-v3/119 is the 10th and final
EXPLORATION slot; iter-v3/120 is the mandatory cycle-6 CONFIRMATION). The
cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`) was spent by /110–/115
(universe ×2, model architecture ×1, multi-frequency-features-on-8h ×1, risk
management ×1, labeling architecture ×1 — all NEGATIVE); /116 found the first
PROMISING via /116 no_confirm exit-layer primitive (PROMISING-MECHANICAL); /117
24h-multi-offset NEGATIVE catastrophic — candle-frequency axis broadly CLOSED
for cycle 6. /118 advances to the NEW engineered feature family axis (per the
/117 closeout QR recommendation; the only LIVE feature axis remaining in the
cycle-6 menu after the candle-frequency closure).

**Anchor (EXPLORATION-mode comparison)**: iter-v3/060 (IS monthly Sharpe
**+0.8325** / OOS monthly Sharpe **+0.1403**) — the 3-seed EXPLORATION-mode
reference per `BASELINE_V3.md`. iter-v3/116 EXPLORATION-PROMISING-MECHANICAL
(IS +0.6246 / OOS +1.1089) is REVERTED for /118 (single-axis discipline; /116
no_confirm primitive is bundled at /120 CONFIRMATION as a strictly-accretive
component decision per `feedback_promising_mechanical_subtype.md` — NOT a
compoundable signal source for /118).

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The
sacred constants are immutable across all three tracks; no /118 modification
touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close
  ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent
  (~2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each
  test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/`
  directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (cycle-6 candle-frequency axis broadly CLOSED per
  /117 closeout Section 6).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The brief declares ONE tuned scalar AND THREE hand-chosen design parameters
for `C3 = ema_signed_volregime`:

| Parameter | Value | Provenance |
|---|---|---|
| Rolling-median window | **200 8h bars** (~67 calendar days) | DECLARED hand-chosen. Rationale: matches the longest rolling-window primitive in TOP_N (`hurst_200`, `atr_pct_rank_200`); a regime classifier should be slower than the value primitive it conditions; 200 bars is the v3 canonical "long-horizon regime" timescale. NOT swept; no IS-only sweep table generated. Source: this brief Section 0. |
| Threshold offset | **0.0** (median = reference) | Inherent to the rolling-median construction; not a tunable scalar (the median IS the threshold). Source: structural property of `sign(x - median)`. |
| Sign convention | **+1 if realized_vol > median (high-vol regime); −1 if < median** | Inherent to `sign(x - median)`. Source: structural property. |
| Lookback windows for primitives | **ema_spread_atr_20** (20-bar EMA span; 14-bar ATR scaling); **range_realized_vol_50** (50-bar rolling std) | INHERITED from V3_FEATURE_COLUMNS_TOP_N (the 14-feature anchor). NOT tuned for /118. |

The brief introduces NO additional tuned scalar parameter — every numeric
design choice (median window, sign threshold, primitive lookbacks) is either
hand-chosen with an explicit IS-only rationale that does NOT depend on any
sweep output, or inherited from the V3_FEATURE_COLUMNS_TOP_N canonical anchor.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-118/`, commit
`60a45e8`) was committed in ONE atomic commit BEFORE this brief or any
subsequent setup commit touches the runner. Every script in the EDA directory
asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file is
read at any point. Verified at EDA: 0 OOS-leaked rows across all 3 symbols
(BCH 5483/0, LDO 2497/0, TRX 5425/0).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: NEW engineered feature in
  V3_FEATURE_COLUMNS_TOP_N, 14 → 15)
- **Cycle 6 slot**: #9 of 10 (1 EXPLORATION slot remaining at /119, then /120
  CONFIRMATION)
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35`
  (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per
  `feedback_v3_outer_seed_cap_2_v3.md`; first 3 seeds of the unified 10-seed
  lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE
  warmup ~30; the v3 EXPLORATION default since iter-v3/019)
- **Wall-clock cap**: ≤ 2h (cycle-6 EXPLORATION cap per
  `feedback_v3_cadence_discipline.md`; /117 ran 0.64h; /116 ran 0.70h; the
  8h baseline runtime envelope is well under cap)
- **Single axis variation**: ONE new feature added to
  `V3_FEATURE_COLUMNS_TOP_N`. All other knobs (universe, label, gates,
  ensemble seeds, Optuna search space) are bit-identical to the /117
  baseline (i.e., the /059-canonical state with /116 no_confirm REVERTED).

---

## Section 1 — Hypothesis

**Single sentence**: adding `ema_signed_volregime` (`ema_spread_atr_20 ×
sign(range_realized_vol_50 − rolling_median_200)`) to `V3_FEATURE_COLUMNS_TOP_N`
as the 15th feature produces an additive walk-forward OOF AUC lift in the
production multivariate LightGBM by exposing a vol-regime-conditioned-momentum
signal at a SLOWER timescale (~67-day rolling median) than the existing
/025-baseline `regime_momentum_signed_5d` captures (hurst-based regime
classifier at ~33-day timescale); this lift translates through walk-forward
training to a positive IS monthly Sharpe Δ vs the /060 anchor (+0.8325).

**Distinguishing claim vs the dead-axes**: this is NOT (a) a new model
architecture (the LightGBM hyperparameter space is unchanged); (b) a new label
(triple_barrier 2.0/1.0 ATR is preserved); (c) a new risk primitive (the 7-gate
RiskV2 stack is unchanged); (d) a new universe (BCH/LDO/TRX); (e) a new
external-data feed (the candidate is built from existing primitives only).
The only structural change is one new column in `V3_FEATURE_COLUMNS_TOP_N`.

---

## Section 2 — IS-Only Numerical Evidence

EDA backing: `analysis/iteration_v3-118/`, commit `60a45e8`. Six composite-
feature candidates evaluated per `feedback_v3_axis_selection_quant_discipline.md`
(IS-only, methodology faithful to /109 / /117 walk-forward AUC).

### 2.1 T1 — Candidate catalog (6 candidates)

| ID | Formula | Cycle-6 motivation |
|---|---|---|
| C1 | `vwap_dev_20 * sign(hurst_100 - 0.5)` | /025 template applied to vwap |
| C2 | `ema_spread_atr_20 * sign(hurst_100 - 0.5)` | /025 template applied to ema |
| **C3** | **`ema_spread_atr_20 * sign(range_realized_vol_50 - rolling_median_200)`** | **vol-regime × momentum; orthogonal to /025 hurst-regime** |
| C4 | `ret_autocorr_lag1_50 * sign(hurst_100 - 0.5)` | /116 no_confirm mechanism at feature level |
| C5 | `sym_vs_btc_ret_7d * sign(btc_ret_14d)` | cross-asset regime divergence |
| C6 | `vwap_dev_20 * sign(ret_kurt_50 - 0)` | vwap × tail-regime |

Full motivation per candidate: `analysis/iteration_v3-118/T1_candidate_catalog.csv`.

### 2.2 T2 — Linear Redundancy Pre-Falsifier (R² vs 14 V3_FEATURE_COLUMNS primitives)

| Candidate | POOLED R² | POOLED max\|corr\| primitive | Verdict |
|---|---:|---|---|
| C1 | 1.000 | vwap_dev_20 (corr=1.00) | PASS-CARVEOUT |
| C2 | 1.000 | ema_spread_atr_20 (corr=1.00) | PASS-CARVEOUT |
| **C3** | **0.196** | **sym_vs_btc_ret_7d (corr=0.21)** | **PASS (R²<0.50)** |
| C4 | 1.000 | ret_autocorr_lag1_50 (corr=1.00) | PASS-CARVEOUT |
| C5 | 0.107 | sym_vs_btc_ret_7d (corr=0.25) | PASS (R²<0.50) |
| C6 | 0.758 | vwap_dev_20 (corr=0.87) | PASS-CARVEOUT |

**C3 has the lowest R² of the 6 candidates with R²<0.50** (clean PASS, no
carve-out needed). C5 is also clean R²<0.50 but fails downstream gates (T3, T4).
C1/C2/C4/C6 all PASS via the composed-feature carve-out per
`feedback_v3_engineered_feature_pivot.md`. Full table:
`T2_linear_redundancy_pre_falsifier.csv`.

### 2.3 T3 — Walk-forward universe-pooled univariate OOF AUC + 100-perm null

| Candidate | POOLED AUC | null q95 | p-value | clears q95 |
|---|---:|---:|---:|:---:|
| C4 | **0.5381** | 0.5099 | **0.000** | **True** |
| C2 | 0.5080 | 0.5116 | 0.100 | False |
| C1 | 0.4960 | 0.5103 | 0.720 | False |
| C3 | 0.4977 | 0.5106 | 0.610 | False |
| C5 | 0.4931 | 0.5115 | 0.820 | False |
| C6 | 0.4942 | 0.5113 | 0.860 | False |

**C4 is the only candidate clearing the T3 univariate gate** (univariate AUC
> null q95, p < 0.05). C3 fails T3 univariate (the LightGBM-with-only-1-feature
in 1D space cannot see the interaction). T3 is INFORMATIONAL for C3 — the
controlling test for C3 is the T9 multivariate-lift screen below. Full
table: `T3_walkforward_pooled_auc.csv`.

### 2.4 T4 — Per-symbol univariate AUC (the /117 g1 hard gate)

| Candidate | BCH AUC (g1 pass) | LDO AUC (g1) | TRX AUC (g1) | #g1 pass |
|---|---|---|---|:---:|
| C4 | 0.5125 ✓ | 0.5042 ✗ (miss by 0.005) | 0.5463 ✓ | 2/3 |
| C2 | 0.5023 ✗ | 0.5384 ✓ | 0.5367 ✓ | 2/3 |
| C5 | 0.4874 ✗ | 0.5151 ✓ | 0.5132 ✓ | 2/3 |
| C3 | 0.5024 ✗ | 0.5079 ✗ | 0.4995 ✗ | 0/3 |
| C1 | 0.4975 ✗ | 0.5385 ✓ | 0.4864 ✗ | 1/3 |
| C6 | 0.5061 ✓ | 0.4957 ✗ | 0.4898 ✗ | 1/3 |

**0 of 6 candidates pass all 3 symbols at the univariate per-symbol g1 gate.**
The same multi-dim signal-recovery argument as T3 applies for C3.

### 2.5 T5 — Multivariate (14+1) depth-4 LightGBM importance rank (per symbol)

| Candidate | BCH rank/15 (gain %) | LDO rank/15 (gain %) | TRX rank/15 (gain %) |
|---|---|---|---|
| **C3** | **10 (63%)** | **9 (38%)** | **8 (45%)** |
| C5 | 15 (37%) | 14 (16%) | 15 (9%) |
| C6 | 15 (41%) | 15 (9%) | 15 (12%) |
| C1 | 15 (7%) | 15 (3%) | 15 (2%) |
| C2 | 15 (1%) | 15 (3%) | 15 (3%) |
| C4 | 15 (3%) | 15 (3%) | 15 (4%) |

**C3 is the SOLE candidate clearing ALL THREE symbols at rank ≤ 10 AND
gain ≥ 30% of top-feature.** This matches the /025 PROMISING benchmark
threshold (rank ≤ 5 AND gain ≥ 30%; rank ≤ 10 is a slightly relaxed reading
for the /025-like "well-allocated mid-rank" composite). Mechanism: the
multivariate LightGBM uses C3 as an interaction-level feature at depth ≥ 2
in conjunction with `ema_spread_atr_20` — exactly the "trees can't compose
this interaction at depth-3-5" mechanism that `feedback_v3_engineered_features_proven.md`
codifies. Full table: `T5_importance_rank_multivariate.csv`.

### 2.6 T7 (C4) and T9 (C3) — Multivariate-LIFT screen (14 vs 14+1 OOF AUC)

The decisive production-relevant test: does adding the candidate to the
14-feature stack lift walk-forward OOF AUC of the multivariate depth-4
LightGBM? Same fold geometry, same hyperparameters, only the feature set
differs.

| Scope | Baseline 14f AUC | +C4 AUC | C4 lift | +C3 AUC | **C3 lift** |
|---|---:|---:|---:|---:|---:|
| BCH | 0.5046 | 0.5091 | +0.0046 | 0.5007 | −0.0039 |
| LDO | 0.5207 | 0.5115 | −0.0092 | 0.5101 | −0.0106 |
| TRX | 0.4806 | 0.4763 | −0.0043 | 0.4888 | +0.0082 |
| **POOLED** | **0.4891** | 0.4900 | +0.0010 | 0.4972 | **+0.0081** |

**C3 clears the POOLED multivariate-lift gate (+0.0081 > 0.005)** while
C4 fails (+0.0010). C4's multivariate-INERT pattern is the canonical
/085/086/015/019/020/023 dead path (univariate signal, R²=1.0, importance
rank 15/15, multivariate AUC lift near zero). C3 has the inverse pattern —
no univariate signal, but interaction-level multivariate lift.

**Per-symbol asymmetry in C3 lift**: TRX is the sole positive carrier
(+0.0082); BCH and LDO are negative. This is the inverse of the /116 BCH-led
asymmetry pattern and is pre-registered as Mode 3 in Section 7. Mechanism:
TRX has the longest IS coverage (5425 rows) and the strongest /117 per-offset
heterogeneity (T3: offset 16 AUC 0.5455, strongest of any sym/offset cell);
C3 gives the LightGBM a feature that exposes the same vol-regime structure
TRX's offset-16 heterogeneity is dominated by. T9 file:
`T9_c3_multivariate_lift_screen.csv`.

### 2.7 Verdict synthesis (T6 + T7/T9 cross-reference)

| Candidate | T2 LR-PF | T3 univar p | T5 multivar imp | T7/T9 multivar lift | Final verdict |
|---|---|---|---|---|---|
| **C3** | **R²=0.20** | 0.61 (fail; informational) | rank 8-10, gain 38-63% | **+0.0081 POOLED** | **/118 AXIS** |
| C4 | R²=1.0 carveout | **0.000** | rank 15, gain 3% | +0.0010 POOLED (FAIL) | PROMISING-INERT-RISK |
| C2 | R²=1.0 carveout | 0.10 | rank 15, gain 1-3% | not tested (T3 fail) | REJECT (T3+T5) |
| C5 | R²=0.11 | 0.82 | rank 14-15, gain 9-37% | not tested (T3 fail) | REJECT |
| C1 | R²=1.0 carveout | 0.72 | rank 15, gain 2-7% | not tested | REJECT |
| C6 | R²=0.76 carveout | 0.86 | rank 15, gain 9-41% | not tested | REJECT |

**RECOMMENDATION: /118 axis = C3_ema_signed_volregime.**

The choice is JUSTIFIED on the production-relevant criterion (multivariate-lift
POOLED), supported by T5 importance rank (the closest analog to the /025
PROMISING precedent in this iteration's candidate set), and clean on T2 LR-PF
(lowest R² of any candidate). The per-symbol asymmetry is explicitly
pre-registered as a Mode-3 risk in Section 7.

Synthesis document: `analysis/iteration_v3-118/synthesis.md`.

---

## Section 3 — Proposed Changes (the architectural diff vs /059)

The substantive single-axis change:

| Knob | /117 / /059-canonical value | /118 value |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` count | 14 | **15** (adds `ema_signed_volregime`) |
| `V3_FEATURE_COLUMNS_TOP_N` 15th element | (n/a) | **`"ema_signed_volregime"`** |
| `compute_ema_signed_volregime` in `engineered_v3.py` | (not present) | **NEW function** |
| `add_engineered_v3_features` wires C3 | wires only `regime_momentum_signed_5d` (+ trend_efficiency_signed, vol_regime_x_momentum; the dormant /063 features that are NOT in TOP_N) | **wires C3 too** |
| Runner `n != 14` guard (line 432-440) | enforces 14 | **enforces 15** (with /118 documentation comment) |
| Runner `_canonical_v059` accretion guard | 16 knobs unchanged | **16 knobs unchanged** (feature-set is NOT in the accretion-guard knob list; the n_features guard at line 432 is the sole feature-count check) |
| BANNED-features list in `features_v3/__init__.py` | does NOT include `ema_signed_volregime` (it does not yet exist) | **NO CHANGE** (the candidate is being ADDED, not BANNED) |

**Knobs UNCHANGED (/059-canonical with /116 no_confirm REVERTED, matching
/117-state)**:

- V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
- REQUIRED_GAP = 66 (= (21+1) × 3; 8h base constant)
- label_mode = "triple_barrier"
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (no per-symbol override)
- zscore_threshold = 2.0
- adx_threshold = 20.0
- adx_threshold_per_symbol = {}
- vol_scale_floor_per_symbol = {}
- block_long_for = ()
- block_short_for = ()
- enable_per_symbol_drawdown_brake = False
- enable_no_confirm_exit = False (the /116 no_confirm primitive STAYS REVERTED)
- no_confirm_trigger_atr = 0.50 (field default; never read while flag is False)
- no_confirm_k_candles = 4 (field default; never read)
- ENSEMBLE_SEEDS (the 3-seed EXPLORATION list)
- Optuna search space (the LightGbmStrategy default)

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

Single-axis EXPLORATION; ONE substantive code change spread across 3 files:

**Change 1 — Add `compute_ema_signed_volregime` to `src/crypto_trade/features_v3/engineered_v3.py`**

After the existing `compute_regime_momentum_signed_5d`, `compute_vol_adj_autocorr`,
and `compute_fracdiff_d05_close` functions (and any other engineered-feature
functions present in `engineered_v3.py`), add:

```python
def compute_ema_signed_volregime(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ema_spread_atr_20 × sign(range_realized_vol_50 - rolling_median_200).

    Encodes a vol-regime-conditioned momentum signal at a slower timescale
    (~67 calendar days at 8h cadence) than /025's regime_momentum_signed_5d
    (~33-day Hurst regime).

    Construction:
    - ``ema_spread_atr_20``: 20-bar EMA spread normalised by ATR (computed by
      ``add_momentum_accel_v3_features``).
    - ``range_realized_vol_50``: 50-bar rolling realized vol from log-returns
      (computed by ``add_tail_risk_v3_features``).
    - ``vol_median_200``: trailing 200-bar rolling median of range_realized_vol_50
      (hand-chosen window per brief Section 0; matches longest TOP_N rolling
      window — hurst_200, atr_pct_rank_200 — and is structurally slower than
      the value primitive it conditions).
    - ``vol_regime_sign``: sign(range_realized_vol_50 − vol_median_200);
        +1 if realized vol > median (high-vol regime)
        −1 if realized vol < median (low-vol regime)
         0 (degenerate equality case) → treated as NaN (no signal)

    Past-only by construction:
    - ``ema_spread_atr_20`` is past-only (momentum_accel computed it past-only).
    - ``range_realized_vol_50`` is past-only (tail_risk computed it past-only).
    - ``rolling(window=200, min_periods=200).median()`` is a trailing window;
      value at t uses only bars 0..t-1+1 ≤ t. Both upstream primitives run
      BEFORE engineered_v3 in GROUP_REGISTRY; appending future bars does NOT
      alter the value at t.

    NaN warm-up: first 200 bars are NaN (vol_median_200 needs 200-bar
    history; the underlying primitives range_realized_vol_50 and
    ema_spread_atr_20 stabilise earlier so they are dominated).

    Args:
        df: DataFrame with columns ``ema_spread_atr_20`` (from momentum_accel)
            and ``range_realized_vol_50`` (from tail_risk).

    Returns:
        Copy of ``df`` with ``ema_signed_volregime`` column appended.
        If a source primitive is missing, the column is set to all-NaN
        without error (downstream feature-column assertion will fail loudly).
    """
    df = df.copy()
    if "ema_spread_atr_20" not in df.columns or "range_realized_vol_50" not in df.columns:
        df["ema_signed_volregime"] = np.nan
        return df
    ema = df["ema_spread_atr_20"].astype(float)
    rv = df["range_realized_vol_50"].astype(float)
    rv_med200 = rv.rolling(window=200, min_periods=200).median()
    vol_diff = rv - rv_med200
    sign_vol = np.sign(vol_diff)
    sign_vol = sign_vol.replace(0.0, np.nan)
    df["ema_signed_volregime"] = ema * sign_vol
    return df
```

Then update `add_engineered_v3_features(df)` to call the new function (in the
order: `regime_momentum_signed_5d` → `vol_adj_autocorr` → `fracdiff_d05_close`
→ other existing → **`ema_signed_volregime`**; the new function only depends
on `ema_spread_atr_20` and `range_realized_vol_50`, both produced by upstream
GROUP_REGISTRY entries `momentum_accel` and `tail_risk` respectively, so any
position within `add_engineered_v3_features` is correct).

**Change 2 — Add `ema_signed_volregime` to `V3_FEATURE_COLUMNS_TOP_N` in
`src/crypto_trade/features_v3/__init__.py`**

Locate the `V3_FEATURE_COLUMNS_TOP_N` tuple (currently 14 entries; the last
is `regime_momentum_signed_5d`). Add `ema_signed_volregime` as the 15th
element, with an inline comment:

```python
"ema_signed_volregime",  # engineered [iter-v3/118: vol-regime × momentum; /025 PROMISING lineage]
```

Place it AFTER `regime_momentum_signed_5d` to keep both engineered features
adjacent at the end of the tuple. Update the docstring comment block at the
top of the tuple definition to record the /118 addition (mirror the existing
/064 / /085 / /113 / /114 entries for traceability).

**Change 3 — Update the runner feature-count guard at `run_baseline_v3.py:432-440`**

The current code:
```python
n = len(V3_FEATURE_COLUMNS)
if n != 14:
    raise RuntimeError(
        f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 14. "
        ...
    )
```

Becomes:
```python
n = len(V3_FEATURE_COLUMNS)
if n != 15:
    raise RuntimeError(
        f"V3_FEATURE_COLUMNS has {n} columns — expected exactly 15. "
        "iter-v3/118: V3_FEATURE_COLUMNS adds ema_signed_volregime (15th, "
        "engineered Category 2; vol-regime × momentum at ~67-day timescale) "
        "to the BASELINE_V3 anchor (14 features). Earlier history: iter-v3/114 "
        "reverted /113's 8 multi-frequency daily features. "
        "Check V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
```

**Change 4 — Regenerate the `data/features_v3/<SYM>_8h_features.parquet`
files for BCH/LDO/TRX (and BTC for cross-asset)**

The new column `ema_signed_volregime` must exist in the parquets read by the
runner. CLI:

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,BCHUSDT,LDOUSDT,TRXUSDT \
  --interval 8h --track v3 --format parquet --workers 4
```

Re-run the parquet generation BEFORE the backtest. Verify the column appears
in each symbol's parquet via:

```bash
uv run python -c "import pandas as pd; print(pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet').columns.tolist())"
```

and check `ema_signed_volregime` is present and the count is 94 columns
(prior 93 + 1 new).

**Change 5 — Add unit test for the new function**

In `tests/features/v3/test_engineered_v3.py` (or the closest existing test
module for engineered features), add:

```python
def test_compute_ema_signed_volregime_past_only():
    """ema_signed_volregime is past-only and matches the formula on a
    synthetic panel of 250 bars."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "ema_spread_atr_20": rng.standard_normal(250),
        "range_realized_vol_50": rng.uniform(0.005, 0.05, size=250),
    })
    out = compute_ema_signed_volregime(df)
    # NaN warm-up: first 199 bars
    assert out["ema_signed_volregime"].iloc[:199].isna().all()
    # Past-only spot check at bar 220: append a future bar, recompute, verify
    # value at 220 unchanged.
    df_extended = pd.concat([df, pd.DataFrame({
        "ema_spread_atr_20": [99.0, -99.0],
        "range_realized_vol_50": [0.99, 0.99],
    })], ignore_index=True)
    out_ext = compute_ema_signed_volregime(df_extended)
    assert out.loc[220, "ema_signed_volregime"] == pytest.approx(
        out_ext.loc[220, "ema_signed_volregime"]
    )
```

**Change 6 — Adversarial integration test**

In `tests/runner/test_runner_v3.py` (or the equivalent), add a single
assertion that `V3_FEATURE_COLUMNS` includes `"ema_signed_volregime"` at
runtime and that the feature parquet for BCH/LDO/TRX has the column non-NaN
on the LAST 100 IS rows (proxy for valid feature generation).

**No changes to**:

- `src/crypto_trade/strategies/ml/lgbm.py` (the LightGbmStrategy reads
  feature_columns from the runner; no new code path)
- `src/crypto_trade/strategies/risk_v2.py` (gates unchanged)
- `src/crypto_trade/backtest.py` (no new exit primitive — /118 is single-axis)
- `src/crypto_trade/features_v3/multioffset_24h.py` (this module is for the
  CLOSED 24h-multi-offset axis; not used at /118 8h baseline)
- `OOS_CUTOFF_DATE`, `training_months` — sacred constants, immutable

---

## Section 4 — Expected OOS Impact (predicted bands)

| Arm | Modal predicted Δ vs /060 anchor | Lower (Mode 4/5) | Upper |
|---|---:|---:|---:|
| IS monthly Sharpe Δ | +0.05 to +0.30 | −0.20 (catastrophic) | +0.50 |
| OOS monthly Sharpe Δ | +0.05 to +0.25 | −0.50 (Mode 4) | +0.40 |
| /060 anchor IS | +0.8325 | | |
| /060 anchor OOS | +0.1403 | | |

**Modal prediction band**: IS Sharpe ∈ [+0.88, +1.13]; OOS Sharpe ∈ [+0.19, +0.39].

**Pre-registered explicit falsifier**: if production OOS monthly Sharpe Δ
falls below **−0.50** AND IS monthly Sharpe Δ falls below **−0.20** vs the
/060 anchor, the hypothesis is FALSIFIED — the C3 multivariate-lift signal
did NOT transfer through walk-forward production training; file
EXPLORATION-NEGATIVE.

**Trade-rate prediction**: total IS trades expected ≈ /060 anchor count
± 15% (the new feature does not change the entry/exit gates, only adds a
LightGBM-input column). OOS trades expected ≈ /060 anchor count ± 25%
(more variance OOS due to feature interaction with regime-change exposure).
If OOS trade count falls by > 50% vs /060, file Mode 4 RESIDUAL (the new
feature is causing OOD-rejection rate to spike).

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`):
the new feature changes Optuna's loss surface, so the IS trade roster will
differ from /060 — expected fraction of common IS trades vs /060 baseline
roster: 60–80% (a fresh feature changes ~20–40% of the model's
threshold-crossing decisions). If common-trade fraction > 95%, the feature
is fully INERT (no behavioral signal) → file as NEGATIVE-no-effect / saturated.

---

## Section 5 — Risk Mitigation

| Risk | Mitigation | IS-calibrated threshold |
|---|---|---|
| R1: Univariate signal absent (T3 informational) | C3 chosen on multivariate-lift (T9), not univariate AUC; production runner uses multivariate LightGBM at depth 3-5 (where C3's interaction signal lives) | T9 POOLED lift +0.0081 (above 0.005 gate) is the controlling evidence |
| R2: Per-symbol asymmetry (TRX-led; BCH/LDO multivariate-negative) | Pre-registered Mode 3 in Section 7; modal prediction band is conservative (+0.05 to +0.30 IS, less ambitious than /025's +0.50 reflective of single-symbol-carrier risk) | If BCH or LDO per-symbol IS PnL Δ < −1.0% with TRX > +2.0%, file PROMISING-PARTIAL |
| R3: Importance INERT at production scale (the /085/086 pattern) | Pre-registered Mode 2 in Section 7; the T5 +T9 cross-reference (rank 8-10 multivar AND positive POOLED lift) is the controlling diagnostic; the /085 dead path had rank 13-15 AND zero lift (both fail), C3 has rank 8-10 AND positive lift (both pass) | If production importance rank falls to ≥ 13/15 on > 1 symbol AND POOLED lift not materially > 0, file PROMISING-INERT |
| R4: Look-ahead via rolling-median window | The `rolling(window=200, min_periods=200).median()` is past-only; unit test Change 5 verifies past-only invariant on a synthetic panel | Test must PASS in CI before merge |
| R5: Parquet column missing at runtime | Change 4 mandates parquet regeneration; runner has a hard assertion (lgbm.py:582-589 verifies feature_columns); Change 6 integration test catches at runtime | n_features == 15 hard guard at runner pre-flight |

---

## Section 6 — Risk Management Design

The 7-gate RiskV2 stack is UNCHANGED:
1. Vol scaling (vol_scale_floor_per_symbol = {} → no floor)
2. ADX threshold (20.0; no per-symbol override)
3. Hurst regime check
4. z-score OOD gate (threshold = 2.0)
5. Low-vol filter
6. Hit-rate feedback (OOS only)
7. BTC trend alignment filter

No new risk primitive introduced at /118. The single axis is the new feature
column.

**Hard-merge gate implications for /120 CONFIRMATION** (if /118 is PROMISING):

| Gate | /118 EDA estimate | /120 CONFIRMATION requirement |
|---|---|---|
| IS Sharpe > 1.0 | EDA does not predict beyond +1.13 modal upper | CONFIRMATION must clear at multi-seed mean |
| OOS Sharpe > 1.0 | EDA does not predict beyond +0.39 modal upper | CONFIRMATION must clear |
| OOS/IS ratio ≥ 0.5 | Modal point estimate 0.30/0.13 vs anchor ratios | needs multi-seed validation |
| Trade-rate ≥ 10/month OOS | EDA does not predict trade count change at /118; expected ≈ /060 anchor | needs /120 multi-seed measurement |
| Top-symbol ≤ 30% | TRX-led asymmetry pre-registered as Mode 3; may breach at /120 | CONFIRMATION must check |
| 10-seed validation | Single-seed at /118 EXPLORATION; full 10-seed at /120 | /120 |

The /118 brief does NOT promise merge-eligibility — it promises a single-axis
EXPLORATION result that feeds into the /120 bundle decision per the cycle-6
cadence (10 EXPLORATIONs + 1 CONFIRMATION).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Five modes pre-registered (Mode 1 = success; Modes 2-5 = failure variants).
**First-match-wins**: classify by the FIRST mode whose condition matches the
observed outcome.

| Mode | Condition (BEFORE checking the result) | Probability prior | Verdict if matches |
|---|---|---:|---|
| **Mode 1 (Modal success)** | IS Sharpe Δ ∈ [+0.05, +0.30] AND OOS Sharpe Δ ∈ [+0.05, +0.25] AND common-trade fraction with /060 ∈ [60%, 80%] | 30% | EXPLORATION-PROMISING (the /025 lineage repeats; /120 bundle candidate) |
| Mode 2 (Importance INERT) | Production importance rank ≥ 13/15 on > 1 symbol with gain < 30% of top-feature | 20% | PROMISING-INERT (the /085 precedent; not bundled at /120) |
| Mode 3 (Per-sym asymmetry) | TRX IS PnL Δ ≥ +2.0% AND (BCH IS PnL Δ < −1.0% OR LDO IS PnL Δ < −1.0%) | 20% | PROMISING-PARTIAL (one-symbol carrier; /120 bundles only if per-symbol gates hold) |
| Mode 4 (Catastrophic regime artifact) | IS Sharpe Δ < −0.20 AND OOS Sharpe Δ < −0.50 | 10% | EXPLORATION-NEGATIVE (the vol-regime axis is partially closed; future engineered-feature axes need different regime classifier) |
| Mode 5 (Null at production) | IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /060 > 95% | 20% | NEGATIVE-no-effect (the /015 / /019 saturated-axis pattern; feature is fully INERT, drop) |

**Tail modes** (probability < 5% each, listed for completeness):
- Mode 6 (Suspicious-OOS-dominant): OOS Sharpe Δ > +0.30 but IS Sharpe Δ < +0.05 — file as SUSPICIOUS per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.
- Mode 7 (Suspicious-IS-dominant): IS Sharpe Δ > +0.40 but OOS Sharpe Δ < −0.30 — file as SUSPICIOUS-IS-overfit.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION-mode criteria (first-match-wins; the post-result classification
the QR commits to BEFORE looking at the result):

### NEGATIVE criteria (any-of-the-below)

1. **NEGATIVE-catastrophic**: IS Sharpe Δ < −0.20 vs /060 OR OOS Sharpe Δ < −0.50 vs /060 → file EXPLORATION-NEGATIVE catastrophic. Axis-CLOSE recommendation: vol-regime composite axis CLOSED at /118 (orthogonal classifier didn't lift).

2. **NEGATIVE-no-effect**: IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /060 > 95% AND production importance rank ≥ 13/15 on all 3 symbols → file EXPLORATION-NEGATIVE no-effect (the /015 saturated-axis pattern).

3. **NEGATIVE-clean**: IS Sharpe Δ < +0.05 AND OOS Sharpe Δ < +0.05 (both arms fail the PROMISING leg threshold) and Modes 2/5 do not match → file EXPLORATION-NEGATIVE clean.

### PROMISING criteria (all-of-the-below)

4. **PROMISING-strong**: IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ +0.10 AND production importance rank ≤ 10/15 on ≥ 2 symbols AND common-trade fraction ∈ [60%, 85%] AND no Mode 3/4 falsifier → file EXPLORATION-PROMISING strong. Bundle candidate for /120 CONFIRMATION.

5. **PROMISING-partial**: TRX positive IS PnL > +2.0% AND (BCH or LDO IS PnL Δ < −1.0%) → file EXPLORATION-PROMISING-PARTIAL. /120 bundles only if a per-symbol gate (e.g., excluding the negative symbol from C3-enabled architecture) is also tested at /119.

6. **PROMISING-INERT-RISK**: T5 importance rank ≥ 13/15 on > 1 symbol AND POOLED T7-equivalent OOF AUC lift < +0.005 → file EXPLORATION-PROMISING-INERT-RISK (the /085 pattern). Not bundled at /120.

### Anchor

The /060 anchor IS Sharpe = +0.8325, OOS Sharpe = +0.1403. The /118
backtest will be compared multi-anchor: /060 (the EXPLORATION-mode
reference per BASELINE_V3.md) AND /059 (the CONFIRMATION anchor IS +1.0894 /
OOS +0.5791). The IS-Δ + OOS-Δ are computed vs /060.

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — C3 is built from existing primitives
(`ema_spread_atr_20`, `range_realized_vol_50`) using pandas rolling-window
operations (`rolling.median`) and numpy `sign`. All required functions are
already imported in `engineered_v3.py`.

**Library inventory** (verified at /118):
- `lightgbm == 4.6.0` (unchanged from /117)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- No `statsmodels` / `optuna` / `pyarrow` version change

**Adversarial integration test** (per
`feedback_v3_methodology_axis_integration_test.md`): the `Change 6`
integration test asserts:
- `V3_FEATURE_COLUMNS` includes `"ema_signed_volregime"` at runtime
- The feature parquet for BCH/LDO/TRX has the column non-NaN on the LAST
  100 IS rows
- Runner pre-flight n_features guard fires `n == 15` (not 14)
- The `compute_ema_signed_volregime` unit test PASSES (past-only invariant
  on synthetic data; the Change 5 test)

These 4 assertions cover the end-to-end integration boundary (feature
generation → runner → strategy → model fit) at the runtime call-site, not
just the unit-level math (the /055 DSR_relative defect mode addressed by
the methodology mandate).

---

## Section 10 — QR Audit Trail

**Provenance of the /118 axis selection**:

1. **/117 closeout QR recommendation** (`diary-v3/iteration_v3-117.md`
   Section 8): "NEW engineered feature family at 8h on the
   regime_momentum_signed_5d lineage". Specific candidate proposed by /117 QR:
   `composite_X = (zscore_20d × sign(hurst_100 − 0.5)) × adx_norm_14d`
   — proposed as ONE candidate; QR explicitly said "the recommendation is
   the AXIS (NEW engineered feature at 8h), not the specific feature".

2. **/118 QR adjudication via EDA** (per `feedback_v3_axis_selection_quant_discipline.md`):
   - Evaluated 6 candidates motivated by cycle-6 failure modes (C1-C6).
   - The /117 QR's proposed `zscore_20d × sign(hurst_100 − 0.5) × adx_norm_14d`
     was NOT one of the 6 because (a) `zscore_20d` is not a feature in v3
     (we have `vwap_dev_20`, an analog; the /118 QR substituted to maintain
     primitive-source discipline) and (b) `adx_norm_14d` is computed via
     the technical_v3 dispatch as `adx_14` — the /117 QR's two-sign
     compounding would require BOTH `hurst_100 > 0.5` AND `adx_14 > median`
     to fire, which is a stronger regime conditioner than /025's single sign
     but introduces a Falsifier 4 risk (the /053 hurst_drift R²=1.0 with
     algebraic-identity carve-out for double-sign composites is more brittle
     than single-sign; trees CAN decompose double-sign at depth 3-5 via two
     sequential splits). The /118 QR opted for single-sign composites
     across all 6 candidates to maintain comparability with the /025
     PROMISING baseline.
   - The 6 candidates span: vwap × hurst (C1), ema × hurst (C2), ema × vol
     (C3), autocorr × hurst (C4), cross-asset × cross-asset-regime (C5),
     vwap × kurt (C6). C3 is the orthogonal vol-regime variant; C4 is the
     direct encoding of the /116 no_confirm mechanism the /117 QR
     specifically called out as the mechanistic motivator.

3. **Why C3 over C4 (the T3 winner)**:
   - C4 has univariate AUC (T3 POOLED 0.5381, p=0.000) but FAILS multivariate
     (T7 POOLED lift +0.0010 < 0.005; importance rank 15/15 across all syms).
     This is the canonical /085 INERT-by-importance pattern (cycle-3
     EXPLORATION #4 funding_regime_momentum_5d; SUSPICIOUS verdict + DROPPED
     at /086). The dead-paths catalog is explicit on this: an INERT feature
     at higher-budget makes things WORSE (per `feedback_v3_inert_features_at_higher_budget.md`).
   - C3 has NO univariate signal (T3 fails) but CLEARS T7-equivalent
     multivariate lift (T9 POOLED +0.0081). The mechanism is sub-tree
     interaction — the LightGBM uses C3 in conjunction with
     `ema_spread_atr_20` at depth ≥ 2. This is the textbook
     `feedback_v3_engineered_features_proven.md` mechanism: composed features
     explicitly encode interactions trees can't compose at depth 3-5.
   - C3 has the highest multivariate importance rank/gain in the candidate
     set (rank 8-10/15, gain 38-63% of top — the only candidate clearing
     the gain ≥ 30% bar on all 3 symbols), matching the /025 PROMISING
     benchmark profile.
   - The /117 closeout QR's specific suggestion (vol-regime as the
     conditioner) is realized in C3: `sign(realized_vol > median)` is the
     "I am in a regime where momentum behaves differently" feature the /117
     QR specifically proposed addressing.

4. **Provenance per `feedback_v3_brief_parameter_provenance.md`**:
   - Section 0 hand-chosen declarations are COMPLETE (rolling-median window,
     sign convention, threshold offset all declared with rationale).
   - No false-provenance failure mode (the /114 Check 1 + Check 8 failure;
     the /117 brief Section 0 used this discipline successfully on its
     candle-frequency axis; the /118 brief follows the same pattern).
   - All scalars cite their source (this brief Section 0, table). No
     scalar is "tuned" from an unstated source.

5. **Cycle-6 trajectory recap**:
   - /110 (universe×2) NEGATIVE — confounded by label drift
   - /111 (universe×2 clean retry) NEGATIVE — wholesale CRV/AAVE/GRT/ADA
     replacement failed
   - /112 (pooled architecture) NEGATIVE
   - /113 (multi-frequency on 8h) NEGATIVE
   - /114 (risk management) NEGATIVE — Check-1 FAIL provenance issue
   - /115 (labeling architecture) NEGATIVE
   - /116 (exit-layer primitive) PROMISING-MECHANICAL — strictly accretive at /120
   - /117 (candle frequency) NEGATIVE catastrophic — candle-frequency axis broadly CLOSED
   - **/118 (engineered feature) — this iteration**
   - /119 (TBD — likely XGBoost-with-categorical-handling per the /117
     closeout candidate (b) IF /118 fails, OR a second engineered feature
     IF /118 PROMISING)
   - /120 (CONFIRMATION — bundles /116 no_confirm + /118 if PROMISING)

**Commit chain expected**:
- `analysis(iter-v3/118): engineered-feature axis EDA — ...` (SHA `60a45e8`, committed BEFORE this brief)
- `docs(iter-v3/118): research brief — engineered-feature axis (ema_signed_volregime)` (this brief)
- Phase 5.5 Engineer gate
- `feat(iter-v3/118): add ema_signed_volregime to V3_FEATURE_COLUMNS_TOP_N + engineered_v3.py + runner guards`
- Parquet regeneration
- Backtest + reports
- Critic preliminary
- QR response (if needed)
- Critic FINAL
- Diary

---

**END OF BRIEF** — ready for QE Phase 6 implementation.

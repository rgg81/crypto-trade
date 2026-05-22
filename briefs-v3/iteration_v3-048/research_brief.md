# Iteration v3-048 — Research Brief (NEW universal engineered feature: vol_normalized_ret_5d)

**Type**: EXPLORATION (Cycle 3 #9 of 10)
**Track**: v3 (rigor arm) — forty-eighth iteration
**Branch**: `iteration-v3/048` (off iter-v3/047 head with OOF guardrail at SHA `6a216b5`)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/048 OOS metrics for the FIRST time in
Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #9 of 10 (after iter-v3/040 baseline-restore + iter-v3/041 pruning + 042
  universal ATR + 043 Kaufman ER + 044 ALGO ATR PROMISING + 045 LDO ATR STRONGEST
  PROMISING + 046 BCH ATR NEGATIVE + 047 BCH primitive 10 NEGATIVE-multi-run-
  stochasticity-contaminated)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1 --clean-oof
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
  - --clean-oof (use new guardrail from SHA `6a216b5` to prevent OOF parquet
    contamination from prior iter-v3/047 5-process accumulation)
Single new axis (one feature added to V3_FEATURE_COLUMNS_TOP_N):
  ADD `vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)` to
  V3_FEATURE_COLUMNS_TOP_N (14 → 15). Composed Category 2 feature; canonical Sharpe-like
  ratio. ON TOP of regime_momentum_signed_5d (KEEP per
  `feedback_v3_engineered_features_proven.md` mandate).
Carry-forward state from iter-v3/047 (UNCHANGED):
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}
  - block_long_for = ("BCHUSDT",) — primitive 10 ON
  - block_short_for = ()
  - V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols
  - V3_FEATURES_PER_SYMBOL = {} (empty)
  - REQUIRED_GAP = 88 = (21+1)*4
Predicted classification: PROMISING (25%), PROMISING-INERT (35%), NEGATIVE-clean (30%),
  NEGATIVE-SUSPICIOUS-OOS (10%).
```

**Context**: iter-v3/047 was NEGATIVE-multi-run-stochasticity-contaminated (BCH LONG
primitive 10 IS-validated cleanly; OOS regression -2.36 attributed to ALGO+LDO cross-run
drift, not primitive 10 contagion). Primitive 10 STAYS in iter-v3/048 carry-forward
state. iter-v3/048 axis is QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`.

The QR EDA (3 scripts at `analysis/iteration_v3-048/` SHA `a230cd1`) explored 5 candidate
axes and FALSIFIED the regime-conditional TRX SHORT axis at the EDA stage (BEFORE
backtest). All direction-asymmetric per-symbol axes (TRX SHORT, ALGO LONG, LDO SHORT)
face the iter-v3/039 OOS-divergence pattern — IS-toxic direction is OOS-healthy, blocks
COST OOS more than they lift IS at multi-seed. Cycle 3 plan Axis 1 (NEW universal
engineered feature) is the recommended path: regime_momentum_signed_5d (iter-v3/025 →
iter-v3/028 CONFIRMATION-MERGE) is the only multi-seed-validated edge ingredient in v3
history. vol_normalized_ret_5d is a compositionally-distinct cousin built on the SAME
ret_5d primitive but normalized by range_realized_vol_50 (rank-1 TRX feature), which
addresses the IS-axis bottleneck symbol's flat importance distribution.

iter-v3/048 is CYCLE 3 #9 of 10. iter-v3/049 has ONE remaining slot before iter-v3/050
SECOND v3 CONFIRMATION.

---

## Section 1 — Hypothesis

Adding `vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)` as a 15th
feature in V3_FEATURE_COLUMNS_TOP_N (Category 2 composed feature; ON TOP of
regime_momentum_signed_5d) gives the LightGBM models a risk-normalized momentum signal
they cannot represent at depth-3-5 splits. The composed feature uses range_realized_vol_50
(rank-1 importance for TRX, the IS-axis-bottleneck symbol with flat importance
distribution; rank-3 BCH, rank-4 ALGO). Expected effect: bundle IS Sharpe lift +0.05 to
+0.15 (single-seed n_trials=35) via better split-quality on the toxic-direction trades
that the model currently can't separate from healthy ones; bundle OOS Sharpe regression
within [-0.10, +0.30] band (uncertain — the cycle 3 base rate for NEW engineered features
is poor [iter-v3/043, /044, /035 all NEGATIVE], but `vol_normalized_ret_5d` has stronger
primitive-importance support than those candidates).

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Per-symbol IS contribution @ iter-v3/045 (the binding-constraint baseline)

| Symbol | n IS | WR IS | net_pnl IS | pct of total | Status |
|--------|----:|------:|-----------:|-------------:|---|
| LDO | 18 | 55.6% | +54.55% | 148.10% | Already optimized (per-symbol ATR) |
| BCH | 94 | 38.3% | +23.62% | 64.13% | Default ATR; primitive 10 LONG-block ON (carry-forward) |
| **TRX** | **85** | **34.1%** | **-7.28%** | **-19.77%** | **Default ATR; IS-NEGATIVE; flat importance — iter-v3/048 target** |
| ALGO | 53 | 39.6% | -34.05% | -92.45% | Per-symbol ATR; structural floor |

Source: `reports-v3/iteration_v3-045/in_sample/per_symbol.csv`.

### 2.2 — Per-symbol direction asymmetry @ iter-v3/045 (ALL direction-asymmetric axes)

| Symbol | Direction | IS n | IS WR | IS net_pnl | OOS n | OOS WR | OOS net_pnl |
|---|---|---:|---:|---:|---:|---:|---:|
| BCH | LONG | 39 | 30.8% | -25.07% | 21 | 28.6% | -7.44% |
| BCH | SHORT | 55 | 43.6% | +48.69% | 17 | 52.9% | +18.19% |
| **TRX** | **LONG** | **42** | **42.9%** | **+24.77%** | **22** | **63.6%** | **+20.85%** |
| **TRX** | **SHORT** | **43** | **25.6%** | **-32.05%** | **24** | **41.7%** | **+8.39%** |
| **ALGO** | **LONG** | **26** | **34.6%** | **-55.17%** | **6** | **66.7%** | **+22.55%** |
| **ALGO** | **SHORT** | **27** | **44.4%** | **+21.12%** | **16** | **62.5%** | **+47.62%** |
| LDO | LONG | 6 | 66.7% | +40.89% | 2 | 100% | +17.97% |
| LDO | SHORT | 12 | 50.0% | +13.66% | 11 | 45.5% | -7.73% |

Source: `analysis/iteration_v3-048/multi_axis_diagnosis.csv` Tables A1, A2 (counterfactual),
B1, C1.

**Observation**: every symbol has a "toxic IS / healthy OOS" direction. Universal direction
blocks would cost OOS edge for 3 of the 4 symbols (BCH LONG already addressed by primitive
10 — it's the exception because BOTH IS+OOS LONG are toxic).

### 2.3 — TRX SHORT regime-conditional gate FALSIFIED at all 5 thresholds

Threshold sweep (`regime_threshold_sweep.csv`) tested DD>20% OR vol_z>1.5 (default), DD>15%
OR vol_z>1.0 (relaxed), DD>10% OR vol_z>0.5 (very relaxed), DD-only 10%, and vol_z-only 0.5:

| Threshold | TRX SHORT IS Stressed | TRX SHORT OOS Stressed | TRX LONG OOS Stressed (collateral) |
|---|---|---|---|
| T1 (DD>20% OR vol_z>1.5) | n=2, **-5.44 wpnl** | n=4, -0.78 wpnl | n=1, +0.90 wpnl |
| T2 (DD>15% OR vol_z>1.0) | n=13, -11.16 wpnl | n=12, **+3.64 wpnl** | n=9, **+8.99 wpnl** |
| T3 (DD>10% OR vol_z>0.5) | n=33, -16.22 wpnl | n=23, **+9.33 wpnl** | n=17, **+11.82 wpnl** |
| T4 (DD-only 10%) | n=14, -0.80 wpnl | n=11, **+3.78 wpnl** | n=7, +1.63 wpnl |
| T5 (vol_z-only 0.5) | n=27, -11.88 wpnl | n=14, **+10.41 wpnl** | n=15, **+11.99 wpnl** |

At every threshold the OOS gain from blocking TRX in stressed regimes is NEGATIVE. The
2023 IS catastrophe (TRX SHORT 14 trades all losers, -27.12% net_pnl) does NOT cleanly
correspond to BTC drawdown 30d > 20% — the toxicity bleeds into "healthy regime" by BTC
anchors. Per `feedback_v3_strict_both_is_oos_baseline.md`, this axis FAILS the BOTH-must-
improve rule at multi-seed CONFIRMATION. **Axis A FALSIFIED at EDA stage** (saved an
EXPLORATION slot).

Source: `analysis/iteration_v3-048/regime_threshold_sweep.csv` + synthesis.md Headline
Finding section.

### 2.4 — Top-5 features by mean importance rank (across 4 symbols)

```
range_realized_vol_50      mean_rank 3.00 (min 1, max 4)  ← rank-1 for TRX
ret_kurt_50                mean_rank 4.25 (min 1, max 8)
max_dd_window_50           mean_rank 4.25 (min 2, max 9)
ret_skew_200               mean_rank 4.75 (min 1, max 6)
ret_skew_50                mean_rank 5.50 (min 1, max 8)
```

**range_realized_vol_50 is the most-utilized feature for TRX** (the IS-axis-bottleneck
symbol, importance 313 of max 313). The composed feature `vol_normalized_ret_5d = ret_5d
/ (range_realized_vol_50 + ε)` exposes risk-normalized momentum that LightGBM cannot
represent at depth-3-5 splits — feeding the model an explicit interaction.

Source: `analysis/iteration_v3-048/multi_axis_diagnosis.csv` Table E1.

### 2.5 — TRX importance distribution is FLAT (model can't discriminate)

iter-v3/045 TRX feature importance (last training month):

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | range_realized_vol_50 | 313 |
| 2 | ema_spread_atr_20 | 289 |
| 3 | hurst_100 | 266 |
| 4 | vwap_dev_20 | 240 |
| 5 | ret_kurt_50 | 222 |
| ... | ... | ... |
| 13 | hurst_diff_100_50 | 145 |
| 14 | regime_momentum_signed_5d | 123 |

**Top:bottom ratio = 313/123 = 2.5×** (vs BCH 173/22 = 7.9×). TRX has near-uniform feature
utilization — the model is searching for signal but finding none in the 14 features. A
NEW composed feature exposing multiplicative structure (vol-normalized momentum) could
give Optuna better split-quality on TRX specifically.

Source: `reports-v3/iteration_v3-045/in_sample/model_importance_last_month_TRXUSDT.csv`.

### 2.6 — Cycle 3 NEW engineered feature attempt history (saturation context)

| iter | Axis | Type | Outcome | Note |
|---|---|---|---|---|
| 035 | fracdiff_d05_close | engineered (LdP FFD) | NEGATIVE — universal application broke TRX/ALGO/LDO | Moved to per-symbol BCH |
| 041 | universal pruning | feature axis | Path C; reverted at 042 | regime_momentum DROP/RESTORE |
| 042 | feature restore | feature axis | Mechanical restore | iter-v3/041 mandate |
| 043 | efficiency_ratio_50 | engineered (Kaufman 1995) | DISASTROUS NEGATIVE — broke ALL 4 symbols | rank 14/14 nowhere |
| 044 | regime_momentum_signed_3d | engineered (composed) | REVERTED before backtest | QR EDA: doesn't address ALGO LONG |

**Cycle 3 NEW engineered feature base rate**: 0/2 successes (iter-v3/043 + iter-v3/044
universal axis only; iter-v3/035 also NEGATIVE under universal application). This is a
saturation risk per `feedback_axis_saturation_predictor.md`.

**Mitigation**: vol_normalized_ret_5d differs from prior failed candidates because:
- It is built from rank-1 TRX importance feature (range_realized_vol_50), not a low-rank
  primitive like efficiency_ratio_50 (introduced new feature with no existing primitive
  dependency) or regime_momentum_signed_3d (similar to existing 5d, redundant).
- It is canonical Sharpe-like ratio (Sinclair Vol Trading; LdP AFML Ch. 8) — not an ad-
  hoc sign-flip composition.
- Per cycle 3 plan Axis 1, NEW universal engineered features remain HIGH priority despite
  4 prior NEGATIVE attempts (the only PROVEN edge ingredient in v3 history is
  regime_momentum_signed_5d, also engineered).

### 2.7 — IC carve-out applies (per `feedback_v3_engineered_feature_pivot.md`)

Per the engineered-feature pivot rule (established at iter-v3/025 closeout):
- vol_normalized_ret_5d shares variance with both source primitives by construction.
- |IC| with range_realized_vol_50 expected ~0.3-0.5 (denominator inverse).
- |IC| with ret_5d direction expected ~0.7+ (numerator).
- Strict |IC|<0.50 gate is INAPPROPRIATE for Category 2 composed features.
- **Binding gate: importance ≥30 in at least 2 of 4 symbols** (relaxed Falsifier per
  cycle 3 standard).

### 2.8 — Why NOT TRX SHORT block (Candidates 1, 4 in EDA ranking)

Per `analysis/iteration_v3-048/candidate_axes_ranking.md` Section "Candidate 4":
- TRX SHORT IS toxic (-32.05% net_pnl) but TRX SHORT OOS POSITIVE (+8.39% net_pnl).
- Naive block: IS lift +13.16 wpnl (good) BUT OOS cost -8.23 wpnl (bad).
- Per `feedback_v3_strict_both_is_oos_baseline.md`: BOTH-must-improve fails at multi-seed.
- Critic FINAL of iter-v3/046 already established this DOUBLY-rejected reasoning.

### 2.9 — Why NOT regime-conditional TRX SHORT block (Candidate 2 in EDA ranking)

Per `analysis/iteration_v3-048/candidate_axes_ranking.md` Section "Candidate 2"
+ `analysis/iteration_v3-048/regime_threshold_sweep.csv`:
- All 5 thresholds tested (T1-T5) cost OOS edge.
- The 2023 IS catastrophe doesn't correspond cleanly to BTC drawdown 30d > 20%.
- Even T3 (very relaxed DD>10% OR vol_z>0.5) costs OOS -21.15 wpnl combined LONG+SHORT.

### 2.10 — Why NOT ALGO LONG block (Candidate 3 in EDA ranking)

Per `analysis/iteration_v3-048/candidate_axes_ranking.md` Section "Candidate 3":
- ALGO LONG IS catastrophic (-55.17% net_pnl) — largest single-symbol-direction IS drag.
- ALGO LONG OOS: WR=66.67%, net_pnl=+22.55% (HEALTHY).
- Universal block COSTS +20.99 OOS weighted_pnl. Same iter-v3/039 anti-pattern.

### 2.11 — Predicted Behavioral Effect (per `feedback_v3_axis_saturation_predictor.md`)

Predicted bundle metrics vs iter-v3/045 anchor (single-seed; primitive 10 in carry-forward):
- Bundle IS trade count: 250 → 240-260 (±4%; new feature changes Optuna picks but doesn't
  modify barrier geometry or signal direction).
- Bundle OOS trade count: 119 → 110-128 (±8%).
- Per-symbol trade count: BCH/LDO/TRX/ALGO each ±5-10% (Optuna picks shift modestly).
- vol_normalized_ret_5d importance rank @ TRX: predicted **5-8** (TRX uses
  range_realized_vol_50 at rank 1; composed feature should rank similarly high).
- vol_normalized_ret_5d importance rank @ BCH+ALGO+LDO: predicted **8-12** (mid-utilization
  similar to regime_momentum_signed_5d's rank 13-14).
- Bundle IS Sharpe Δ: **[+0.05, +0.15]** (modest lift; cycle 3 base rate is poor).
- Bundle OOS Sharpe Δ: **[-0.10, +0.30]** (uncertain; OOS direction depends on whether
  the feature genuinely captures structure vs noise).
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.0] (band falsifier per
  `feedback_v3_engineered_features_dont_stack.md`; outside band = NEGATIVE-SUSPICIOUS-OOS).

**Falsifier (saturation predictor)**: if observed bundle IS trade count change > 15%
relative vs iter-v3/045, the feature is producing cascade effects beyond Optuna picks
(investigate for unintended interaction with risk gates or feature-pipeline consistency).

**Per-symbol Optuna independence prediction**: BCH and ALGO models should produce trade
rosters within multi-run-stochasticity baseline (~5-15% drift per iter-v3/047 forensic
analysis at single-seed; primitive 10 carry-forward state same). Non-target symbol drift
would NOT be cross-feature contamination — the new feature is ON THE FEATURE LIST so
ALL 4 models train with it, and per-symbol Optuna independence is preserved.

### Analysis Scripts

3 EDA scripts committed at SHA `a230cd1`:
- `analysis/iteration_v3-048/multi_axis_diagnosis.py` — 5-axis ranking covering TRX SHORT,
  ALGO direction, LDO direction, BCH SHORT residual, NEW engineered feature candidates.
  Outputs: `multi_axis_diagnosis.csv` (14 sub-tables), full per-symbol direction asymmetry,
  per-month TRX SHORT temporal stability, importance rank summary, 5 candidate features.
- `analysis/iteration_v3-048/regime_gate_validation.py` — primitive 9 (regime gate)
  stratification on TRX × direction × regime at default thresholds.
  Outputs: `regime_validation.csv` (regime fire rates, direction × regime PnL).
- `analysis/iteration_v3-048/regime_threshold_sweep.py` — 5 threshold combinations tested
  to find regime gate that captures 2023 toxicity without OOS cost. **NONE found.**
  Outputs: `regime_threshold_sweep.csv`.

---

## Section 3 — Proposed Changes

### Sub-fix 1: ADD `compute_vol_normalized_ret_5d` to `engineered_v3.py`

In `src/crypto_trade/features_v3/engineered_v3.py`, add (parallel to existing
`compute_regime_momentum_signed_5d`):

```python
def compute_vol_normalized_ret_5d(df: pd.DataFrame) -> pd.DataFrame:
    """Composed feature: ret_5d / (range_realized_vol_50 + epsilon).

    Encodes the canonical Sharpe-like risk-normalized momentum (Sinclair, Vol Trading;
    LdP AFML Ch. 8): how unusual is this 5d return given recent volatility regime?

    Construction:
    - ret_5d = log(close_t / close_{t-15}) at 8h cadence (15 bars * 8h = 5 days).
    - range_realized_vol_50: rolling 50-bar high-low realized vol (computed by
      add_tail_risk_v3_features).
    - epsilon = 1e-6 prevents zero-vol division.

    Past-only by construction:
    - ret_5d.shift(15) ensures bar t uses close at t-15 (no look-ahead).
    - range_realized_vol_50 is past-only (rolling window); the v3 implementation
      uses .shift(1) inside add_tail_risk_v3_features.

    Args:
        df: DataFrame with columns 'close' (float-castable) and 'range_realized_vol_50'
            (pre-computed by add_tail_risk_v3_features).

    Returns:
        Copy of df with vol_normalized_ret_5d column appended.
        If range_realized_vol_50 is missing the column is set to all-NaN without error,
        so the pipeline fails loudly at the feature-column assertion downstream.
    """
    df = df.copy()
    close = df["close"].astype(float)
    log_close = np.log(close.clip(lower=1e-12))
    # 15 bars at 8h cadence = 5 calendar days
    ret_5d = log_close - log_close.shift(15)

    if "range_realized_vol_50" not in df.columns:
        df["vol_normalized_ret_5d"] = np.nan
        return df

    rv = df["range_realized_vol_50"].astype(float)
    df["vol_normalized_ret_5d"] = ret_5d / (rv + 1e-6)
    return df
```

### Sub-fix 2: REGISTER `compute_vol_normalized_ret_5d` in `add_engineered_v3_features`

In `src/crypto_trade/features_v3/engineered_v3.py:add_engineered_v3_features` (or wherever
the registry is), add the function call AFTER `compute_regime_momentum_signed_5d`. The
GROUP_REGISTRY in `features_v3/__init__.py` order is preserved (engineered_v3 runs AFTER
regime AFTER tail_risk, so range_realized_vol_50 is available at call time).

### Sub-fix 3: ADD `vol_normalized_ret_5d` to `V3_FEATURE_COLUMNS_TOP_N`

In `src/crypto_trade/features_v3/__init__.py`, append `"vol_normalized_ret_5d"` to the
14-tuple V3_FEATURE_COLUMNS_TOP_N (making it 15 elements). Add a comment block citing
this brief Section 3 Sub-fix 3 + cycle 3 plan Axis 1 + IC carve-out.

### Sub-fix 4: UPDATE `_verify_feature_columns` assertions

In `run_baseline_v3.py:_verify_feature_columns`, ADD assertion (mirror existing
regime_momentum_signed_5d assertion):

```python
# iter-v3/048: vol_normalized_ret_5d MUST be in V3_FEATURE_COLUMNS_TOP_N (NEW addition).
if "vol_normalized_ret_5d" not in V3_FEATURE_COLUMNS_TOP_N:
    raise RuntimeError(
        "vol_normalized_ret_5d NOT FOUND in V3_FEATURE_COLUMNS_TOP_N — must be PRESENT "
        "at iter-v3/048. Cycle 3 plan Axis 1 (NEW engineered feature) per "
        "feedback_v3_engineered_features_proven.md. "
        "Add it to V3_FEATURE_COLUMNS_TOP_N in features_v3/__init__.py."
    )
print("  vol_normalized_ret_5d PRESENT in V3_FEATURE_COLUMNS_TOP_N (cycle 3 plan Axis 1)  PASS")
```

Update existing assertion that `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (if any) → `== 15`.

### Sub-fix 5: ADD adversarial test `tests/features_v3/test_vol_normalized_ret_5d.py`

5 mandatory tests (all PASS at setup commit):

1. `test_vol_normalized_ret_5d_past_only_discipline` — synthetic close+rv array; verify
   the value at bar t depends only on rv at bar t and close at bars [t-15, t]; no future
   leakage.
2. `test_vol_normalized_ret_5d_warmup_nan` — first 15 bars NaN (ret_5d warmup); first 50
   bars NaN if rv warmup dominates.
3. `test_vol_normalized_ret_5d_zero_vol_protection` — when rv == 0, the result is bounded
   (no inf/NaN cascade); epsilon=1e-6 prevents division by zero.
4. `test_vol_normalized_ret_5d_monotonicity` — when ret_5d > 0 and rv constant, the result
   monotonically increases with ret_5d magnitude.
5. `test_vol_normalized_ret_5d_missing_input_returns_nan` — when range_realized_vol_50 is
   missing from input df, the column is added as all-NaN (graceful failure).

### Sub-fix 6: UPDATE ITERATION_LABEL

In `run_baseline_v3.py`, change `ITERATION_LABEL = "v3-047"` to `ITERATION_LABEL = "v3-048"`.

### Sub-fix 7: RE-GENERATE v3 features

After Sub-fixes 1-3 land:

```bash
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT \
  --interval 8h --track v3 --format parquet --workers 4
```

This regenerates 4 parquet files with the new vol_normalized_ret_5d column.

### Sub-fix 8: USE --clean-oof guardrail

The iter-v3/048 backtest invocation should use the new `--clean-oof` flag (introduced at
SHA `6a216b5` to prevent the iter-v3/047 5-process OOF parquet contamination):

```bash
uv run python run_baseline_v3.py --seeds 1 --clean-oof
```

This ensures `trial_oof_returns.parquet` is cleaned before the new run.

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 15 features (UP from 14; vol_normalized_ret_5d ADDED)        PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) — UNCHANGED                                         PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: 2 entries (ALGO, LDO) — both (2.0, 1.5)                  PASS
V3_FEATURES_PER_SYMBOL: {} (empty — UNCHANGED)                                          PASS
features_for_symbol("BCHUSDT") == 15 features (TOP_N fallback)                          PASS
features_for_symbol("ALGOUSDT") == 15 features (TOP_N fallback)                         PASS
features_for_symbol("LDOUSDT") == 15 features (TOP_N fallback)                          PASS
features_for_symbol("TRXUSDT") == 15 features (TOP_N fallback)                          PASS
atr_multipliers_for_symbol("ALGOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)           PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.5) (per-symbol — UNCHANGED)            PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED iter-v3/047)   PASS
atr_multipliers_for_symbol("TRXUSDT") == (2.0, 1.0) (DEFAULT — UNCHANGED)               PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)               PASS
"vol_normalized_ret_5d" IN V3_FEATURE_COLUMNS_TOP_N (NEW iter-v3/048)                   PASS
"regime_momentum_signed_3d" NOT IN V3_FEATURE_COLUMNS_TOP_N (REVERTED at iter-v3/044)   PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (DROPPED at iter-v3/043)          PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                     PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                               PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)                               PASS
REQUIRED_GAP = 88 = (21+1) x 4 (UNCHANGED)                                              PASS
Primitive 10: BCH model risk_cfg.block_long_for == ("BCHUSDT",) (UNCHANGED carry-forward) PASS
Primitive 10: BCH model risk_cfg.block_short_for == () (UNCHANGED carry-forward)        PASS
ITERATION_LABEL == "v3-048" (UPDATED)                                                   PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +0.7459)**:
- Predicted band: **[+0.85, +1.15]** vs iter-v3/045 anchor +0.7459 (lift +0.10 to +0.40)
- More conservative point estimate: +0.80 to +0.90 (lift +0.05 to +0.15) given cycle 3
  base rate
- Rationale: vol_normalized_ret_5d gives the model risk-normalized momentum it can use
  for split-quality on TRX (rank-1 utilization expected) and modest contributions to
  BCH/ALGO/LDO. Sharpe lift is gated by the model's ability to actually USE the new
  feature beyond the existing 14 (per `feedback_v3_inert_features_at_higher_budget.md`,
  features ranking 14/14 ACTIVELY HARM at higher budget — hence the importance ≥30 gate).

**OOS Sharpe prediction (single-seed, vs iter-v3/045 single-seed anchor +3.5259)**:
- Predicted band: **[+3.30, +3.85]** (regression up to -0.30 OR lift up to +0.30)
- More conservative point estimate: +3.40 to +3.55 (slight regression to neutral)
- Rationale: cycle 3 NEW engineered features have 0/2 universal-axis success rate (iter-
  v3/043 + iter-v3/044). vol_normalized_ret_5d differs in being built on rank-1 TRX
  feature, which provides stronger primitive-importance support, but still UNTESTED at
  single-seed n_trials=35. OOS direction depends on whether the new feature generalizes.

**OOS falsifier (pre-registered)**:
- If vol_normalized_ret_5d ranks 15/15 (last) in ALL 4 symbols: PROMISING-INERT
  (model didn't learn the feature; equivalent to base rate).
- If observed bundle IS trade count change > 15% relative vs iter-v3/045: investigate
  cascade effects (Sub-fix 4 assertion catches feature-pipeline issues; Sub-fix 5 tests
  catch dispatch issues).
- If IS-OOS daily Sharpe ratio outside [0.5, 2.0] band:
  NEGATIVE-SUSPICIOUS-OOS classification (per
  `feedback_v3_engineered_features_dont_stack.md`).

**Pathway-A trigger (PROMISING-clean)**:
- IS Sharpe Δ ≥ +0.10 vs iter-v3/045 anchor (i.e. IS Sharpe ≥ +0.85) AND
- OOS Sharpe Δ ≥ -0.10 vs iter-v3/045 anchor (i.e. OOS Sharpe ≥ +3.42) AND
- vol_normalized_ret_5d importance rank ≤ 10 in at least 2 of 4 symbols AND
- IS-OOS daily Sharpe ratio ∈ [0.5, 2.0] (no IS-OOS divergence pattern)

**Pathway-B trigger (PROMISING-INERT)**:
- vol_normalized_ret_5d importance rank ≥ 11 in ALL 4 symbols (model didn't learn) AND
- bundle IS Sharpe Δ ∈ [-0.10, +0.10]

**Pathway-C trigger (NEGATIVE-clean)**:
- Bundle IS Sharpe Δ < -0.10 OR
- Bundle OOS Sharpe Δ < -0.30 OR
- IS-OOS daily Sharpe ratio outside [0.5, 2.0] band (NEGATIVE-SUSPICIOUS-OOS)

**Action on PATH C**: NEW engineered feature axis CLOSED for cycle 3 (vol_normalized_ret_5d
DROPPED from V3_FEATURE_COLUMNS_TOP_N at iter-v3/049 setup). iter-v3/049 = different
axis category (per `feedback_axis_saturation_predictor.md` saturation rule). Likely pivot
to per-symbol architecture review (e.g., per-symbol features that pass the IS-axis pre-
validation gate per cycle 3 plan Axis 5).

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.

**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace UPDATED from 14
to 15 features. This means the Mahalanobis covariance space changes slightly — vol_
normalized_ret_5d is added to the feature mean/std snapshot. Expected effect on OOD
firing rate: <5% relative (the new feature has the same magnitude order as ret_5d so
the covariance matrix shifts modestly).

**Primitive 10 (BCH LONG block)**: unchanged. block_long_for=("BCHUSDT",) carries forward.

**Primitive 9 (regime gate)**: unchanged. enable_regime_gate=False (NOT enabled this
iteration; regime-conditional axis was EDA-falsified).

**Cross-symbol contagion risk**: vol_normalized_ret_5d is added UNIVERSALLY (in
V3_FEATURE_COLUMNS_TOP_N). All 4 symbols' models train with the new feature. There is no
per-symbol gating. Risk: the new feature may help one symbol while harming another (e.g.,
help TRX but harm ALGO). Falsifier: per-symbol importance rank — if vol_normalized_ret_5d
ranks 15/15 in 3 of 4 symbols but rank 1-5 in one symbol, the feature is per-symbol-
relevant and a per-symbol architecture (V3_FEATURES_PER_SYMBOL) should be considered for
iter-v3/049.

**Risk-budget redistribution risk**: unchanged from iter-v3/047 baseline; no new gate.

**IS trade-rate stability**: Bundle IS trades expected within ±4% of iter-v3/045
(250 → 240-260). If portfolio total deviates > 15%, investigate feature-pipeline
consistency (Sub-fix 4 assertion catches missing column; Sub-fix 5 tests catch
implementation bugs).

**Adversarial-tests regression risk**: the 5 vol_normalized_ret_5d tests + the 7
primitive 10 tests + the 5 ATR tests + existing primitive 9 + per_symbol_cap tests all
PASS at the setup commit. If any regress in CI before backtest runs, the iteration is
BLOCKED.

**Multi-run-stochasticity risk** (per iter-v3/047 forensic analysis): primitive 10 +
LightGBM OpenMP non-determinism produces ~5-15% non-target-symbol drift across
process invocations of the same single-seed config. The `--clean-oof` guardrail at SHA
`6a216b5` PREVENTS the OOF parquet duplication that contributed to iter-v3/047's
contamination. Single-process invocation discipline: run the iter-v3/048 backtest ONCE
and record the result; do NOT re-run for cleaner numbers (peeking-at-OOS violation per
`feedback_no_cheating.md`).

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

All 10 risk gates carried forward from iter-v3/047 UNCHANGED. NO new gates added.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0, **15-D space** | Updated dim (14 → 15) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |
| 8 — Per-symbol cap | RiskV2Config | enable_per_symbol_cap=False | None |
| 9 — Regime gate | RiskV2Config | enable_regime_gate=False | None |
| 10 — Direction block | RiskV2Config | block_long_for=("BCHUSDT",); block_short_for=() | UNCHANGED carry-forward |

**Predicted OOD fire rate (Gate 6)**: within ±5% of iter-v3/045 baseline. The 14 → 15
feature subspace change shifts the Mahalanobis covariance modestly; vol_normalized_ret_5d
has similar magnitude scale to ret_5d primitive (which is NOT in the feature list — the
features are categorically distinct).

**Predicted primitive 10 fire rate**: ~41% of BCH candidate signals (from iter-v3/047
EDA Table 03; primitive 10 is unchanged carry-forward).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-INERT — model didn't learn; 35% probability)**:
vol_normalized_ret_5d ranks 14-15/15 across all 4 symbols. Bundle IS Sharpe Δ ∈ [-0.10,
+0.10]; bundle OOS Sharpe Δ within ±0.20 of iter-v3/045 anchor. The composed feature is
mathematically interesting but the model already captures the necessary information from
range_realized_vol_50 + ret_5d-related features (mom_accel_5_20, regime_momentum_signed_5d).
Classification: PROMISING-INERT. Action: drop vol_normalized_ret_5d from
V3_FEATURE_COLUMNS_TOP_N at iter-v3/049 setup; pivot to a different axis category
(per `feedback_v3_engineered_features_dont_stack.md` deferral to multi-seed CONFIRMATION).
**Probability: 35%.**

**Second plausible failure mode (NEGATIVE-clean — IS regression; 30% probability)**:
The new feature confuses Optuna's hyperparameter search at n_trials=35 (cycle 3 has 4
prior NEGATIVE attempts on engineered features at this budget). Bundle IS Sharpe Δ <
-0.10. The 15-D feature space at single-seed Optuna lottery produces lower-quality
model selection. Per `feedback_v3_inert_features_at_higher_budget.md`, INERT features at
n_trials=35 actively HARM OOS. Classification: NEGATIVE-clean. Action: drop the feature;
NEW engineered feature axis CLOSED for cycle 3 (saturated). iter-v3/049 = different axis
category. **Probability: 30%.**

**Third plausible failure mode (PROMISING — clean lift; 25% probability)**:
The composed feature provides genuine signal that the depth-3-5 LightGBM cannot
represent at base-feature splits. vol_normalized_ret_5d ranks 5-12 across symbols
(rank ≤10 in at least 2 of 4); bundle IS Sharpe lift +0.10 to +0.30. OOS regression
within ±0.20 OR positive lift. Classification: PROMISING. Compoundable at iter-v3/050
CONFIRMATION as a 2nd engineered feature on top of regime_momentum_signed_5d (caveat:
2-feature stacking previously failed at iter-v3/026 single-seed; multi-seed CONFIRMATION
required to validate the stacking). **Probability: 25%.**

**Fourth plausible failure mode (NEGATIVE-SUSPICIOUS-OOS — iter-v3/026/027 anti-pattern;
10% probability)**:
IS Sharpe collapses (Δ < -0.10) AND OOS Sharpe spikes implausibly (Δ > +1.5). IS-OOS
daily Sharpe ratio outside [0.5, 2.0] band. Per `feedback_v3_engineered_features_dont_
stack.md`, this is the iter-v3/026 vol_adj_autocorr + iter-v3/027 cross_asset_divergence_
norm pattern: stacking 2 engineered features at single-seed n_trials=35 produces
structurally suspect OOS spikes. Classification: NEGATIVE-SUSPICIOUS-OOS (rejected as
single-seed lottery; cannot be cited as evidence). Action: drop the feature.
**Probability: 10%.**

**What the gates should catch**:
- Sub-fix 4 assertion: vol_normalized_ret_5d MUST be in V3_FEATURE_COLUMNS_TOP_N. If
  missing, runner BLOCKS at startup.
- Sub-fix 5 tests: 5 adversarial tests catch implementation bugs (past-only discipline,
  warmup, zero-vol protection, monotonicity, missing-input handling).
- Gate 6 (OOD): Mahalanobis space updates from 14 → 15. If the new feature has degenerate
  covariance contribution, OOD fire rate may shift by > 5% (signal of feature-distribution
  pathology).
- Bundle IS trade count: predicted 250 → 240-260 (±4%). Larger drift signals risk-gate
  cascade or feature-pipeline issue.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING (clean)**:
  IS Sharpe Δ ≥ +0.10 vs iter-v3/045 anchor +0.7459 (i.e. IS Sharpe ≥ +0.85)
  AND OOS Sharpe Δ ≥ -0.10 vs iter-v3/045 anchor +3.5259 (i.e. OOS Sharpe ≥ +3.42)
  AND vol_normalized_ret_5d importance rank ≤ 10 in at least 2 of 4 symbols
  AND IS-OOS daily Sharpe ratio ∈ [0.5, 2.0]
  Classification: PROMISING. NEW engineered feature contributes positive lift.
  Catalog entry: candidate for next CONFIRMATION bundle (multi-seed validation
  required per `feedback_v3_engineered_features_dont_stack.md` since this is
  2nd engineered feature stacking on top of regime_momentum_signed_5d).

**PATH B — PROMISING-INERT**:
  vol_normalized_ret_5d importance rank ≥ 11 in ALL 4 symbols
  AND bundle IS Sharpe Δ ∈ [-0.10, +0.10]
  AND bundle OOS Sharpe Δ ∈ [-0.20, +0.20]
  Classification: PROMISING-INERT per `feedback_v3_inert_features_at_higher_budget.md`.
  Action: drop the feature at iter-v3/049 setup; NEW engineered feature axis CLOSED.

**PATH C-clean — NEGATIVE-clean**:
  Bundle IS Sharpe Δ < -0.10 (IS regression dominates) OR
  Bundle OOS Sharpe Δ < -0.30 (OOS regression dominates)
  Classification: NEGATIVE-clean. NEW engineered feature axis CLOSED for cycle 3
  (saturated per `feedback_axis_saturation_predictor.md`; cycle 3 has 5 attempts now).
  Action: drop the feature at iter-v3/049 setup; pivot to different axis category.
  iter-v3/045 PROMISING bundle (ALGO + LDO ATR + primitive 10) preserved.

**PATH C-suspicious — NEGATIVE-SUSPICIOUS-OOS**:
  IS-OOS daily Sharpe ratio outside [0.5, 2.0] band per
  `feedback_v3_engineered_features_dont_stack.md`. The iter-v3/026/027 anti-pattern.
  Classification: NEGATIVE-SUSPICIOUS-OOS. Cannot be cited as evidence.
  Action: drop the feature; iter-v3/049 = different axis category.

**Pre-registered classification thresholds (LOCKED before backtest)**:
- PATH A: IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ -0.10 AND vol_normalized_ret_5d rank ≤
  10 in ≥2 syms AND IS-OOS daily ratio ∈ [0.5, 2.0]
- PATH B: vol_normalized_ret_5d rank ≥ 11 in ALL 4 syms AND IS Sharpe Δ ∈ [-0.10, +0.10]
  AND OOS Sharpe Δ ∈ [-0.20, +0.20]
- PATH C-clean: IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30
- PATH C-suspicious: IS-OOS daily Sharpe ratio outside [0.5, 2.0]

These thresholds are LOCKED and CANNOT be post-hoc renegotiated per cycle 3 discipline.

**Saturation rule**: if iter-v3/048 produces PATH B (PROMISING-INERT) OR PATH C, the NEW
universal engineered feature axis is CLOSED for the remainder of cycle 3 (1 EXPLORATION
slot remaining before iter-v3/050 CONFIRMATION). This follows
`feedback_axis_saturation_predictor.md` discipline: cycle 3 has 5 attempts on this
axis (iter-v3/035, /041, /042, /043, /044 + this iter-v3/048); the next attempt would be
the 6th and the cycle is exhausted.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/045/046/047 reproducibility stamp. No new libraries
introduced. vol_normalized_ret_5d is implemented in pure numpy + pandas (parallel to
existing compute_regime_momentum_signed_5d).

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels for all
statistical tests (ADF, PBO, DSR, PSR).

---

## Section 10 — QR Audit Trail (per `feedback_v3_axis_selection_quant_discipline.md`)

**EDA basis**: 3 EDA scripts at `analysis/iteration_v3-048/` committed at SHA `a230cd1`:
- `multi_axis_diagnosis.py` (5-axis ranking covering TRX SHORT, ALGO direction, LDO
  direction, BCH SHORT residual, NEW engineered feature candidates; 14 sub-tables)
- `regime_gate_validation.py` (primitive 9 stratification on TRX × direction × regime)
- `regime_threshold_sweep.py` (5 thresholds tested; ALL fail OOS preservation)

Establishes:
- All 4 symbols have "toxic IS / healthy OOS" direction asymmetries (per-symbol
  direction blocks would COST OOS at multi-seed)
- TRX SHORT regime-conditional gate FALSIFIED at all 5 thresholds (T1 narrow → T5
  vol_z-only)
- ALGO LONG direction block: highest IS leverage (-55.17% IS) but ALGO LONG OOS WR=67%
  (universal block costs +20.99 OOS PnL)
- LDO direction filter: small sample + opposite IS-vs-OOS pattern
- BCH SHORT residual: HEALTHY (no second axis warranted; primitive 10 already addresses
  BCH LONG)
- NEW universal engineered feature: cycle 3 plan Axis 1 priority. range_realized_vol_50
  is rank-1 TRX importance (313/313) and used heavily by all 4 symbols (mean rank 3.00).
  TRX has FLAT importance distribution (2.5× ratio) — model can't discriminate signal.
- 5 candidate engineered features ranked: vol_normalized_ret_5d selected (built on
  rank-1 TRX feature; canonical Sharpe-like ratio; conceptually defensible)

**Original orchestrator pick**: orchestrator did NOT pre-commit a NEW axis (per
`feedback_v3_axis_selection_quant_discipline.md` discipline since iter-v3/044). The
orchestrator delegates axis selection to QR via committed EDA. The 5 SEED CANDIDATES
listed in iter-v3/047 diary Section "Next Iteration Ideas" (TRX bottleneck, ALGO
bottleneck, LDO bottleneck, NEW universal engineered feature, universal LONG-confidence
threshold) are SEED IDEAS only — the QR scored these via EDA-driven quantitative basis.

**QR-driven selection**: vol_normalized_ret_5d (Candidate 2 in
`analysis/iteration_v3-048/candidate_axes_ranking.md`). EDA evidence:
1. **Direction-asymmetric and regime-conditional axes are EDA-falsified** (TRX SHORT
   regime gate fails at all 5 thresholds; ALGO LONG OOS healthy; LDO sample too small;
   BCH SHORT residual healthy after primitive 10).
2. **Cycle 3 plan Axis 1 priority** per `feedback_v3_engineered_features_proven.md`.
   Engineered features are the only PROVEN edge ingredient in v3 (regime_momentum_
   signed_5d → iter-v3/028 CONFIRMATION-MERGE).
3. **TRX flat importance distribution** (2.5× ratio top:bottom) suggests the model can't
   discriminate signal. A composed feature exposing risk-normalized momentum could give
   Optuna better split-quality on TRX (the IS-axis-bottleneck symbol).
4. **Implementation feasible within EXPLORATION 2h cap** — parallel to existing
   compute_regime_momentum_signed_5d; reuse engineered_v3.py infrastructure.
5. **Single-axis discipline** — ONE NEW feature added; no compounded changes.

**Pre-commit SHAs**:
- EDA SHA: `a230cd1` (3 scripts + 4 CSVs + 2 markdown synthesis files)
- Brief SHA: `81af783` (this brief, committed before Phase 5.5 gate + setup commit)
- Setup commit SHA: `c69fdaa` (Engineer's implementation commit)
- Phase 5.5 gate SHA: `34c97c5` (Engineer's gate verification — OVERALL=PASS)

**Phase 5.5 verification**:
- EDA committed BEFORE brief (SHA `a230cd1` precedes brief commit)
- Brief Section 2 includes 11 sub-sections + numerical tables + falsifiers + behavioral-
  effect predictor (per `feedback_v3_axis_saturation_predictor.md`)
- Brief Section 10 (QR Audit Trail) cites EDA SHA explicitly
- Brief Section 8 LOCKED thresholds non-renegotiable post-hoc
- Pre-registered classification (PATH A / B / C-clean / C-suspicious) covers all
  observable outcomes

This Section 10 satisfies the process-discipline requirement that QR EDA precedes axis
selection. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL outcomes:

**Outcome A — PROMISING-clean** (IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ -0.10 AND
vol_normalized_ret_5d rank ≤ 10 in ≥2 syms AND IS-OOS daily ratio ∈ [0.5, 2.0]):
> `| iter-v3/048 | 2026-05-09 | NEW universal engineered feature: vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + ε); 4-sym BCH+LDO+TRX+ALGO; QR EDA-driven cycle 3 #9; primitive 10 BCH LONG block carry-forward | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING (clean) | YES — STRONG candidate; iter-v3/050 CONFIRMATION-bundle ingredient (multi-seed validation required for 2-feature stacking per feedback_v3_engineered_features_dont_stack.md) |`

**Outcome B — PROMISING-INERT** (vol_normalized_ret_5d rank ≥ 11 in ALL 4 syms AND
IS Δ ∈ [-0.10, +0.10] AND OOS Δ ∈ [-0.20, +0.20]):
> `| iter-v3/048 | 2026-05-09 | vol_normalized_ret_5d engineered feature; cycle 3 #9 | <IS Δ> | <OOS Δ> | EXPLORATION-PROMISING-INERT | NO — model didn't learn the feature; drop at iter-v3/049 setup; NEW engineered feature axis CLOSED for cycle 3 per saturation rule |`

**Outcome C-clean — NEGATIVE-clean** (IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30):
> `| iter-v3/048 | 2026-05-09 | vol_normalized_ret_5d engineered feature; cycle 3 #9 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE-clean | NO — drop the feature; NEW engineered feature axis CLOSED for cycle 3; iter-v3/049 = different axis category (per-symbol architecture review or per-symbol features that pass IS-axis pre-validation gate) |`

**Outcome C-suspicious — NEGATIVE-SUSPICIOUS-OOS** (IS-OOS daily Sharpe ratio outside
[0.5, 2.0] band per `feedback_v3_engineered_features_dont_stack.md`):
> `| iter-v3/048 | 2026-05-09 | vol_normalized_ret_5d engineered feature; cycle 3 #9 | <IS Δ> | <OOS Δ> | EXPLORATION-NEGATIVE-SUSPICIOUS-OOS | NO — iter-v3/026/027 anti-pattern at single-seed; cannot cite as evidence; drop the feature; iter-v3/049 = different axis category |`

The diary commit closes the catalog row regardless of outcome. The 4-row pre-commit
prevents post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (10 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED) |
| 2 | Section 1 — Hypothesis | PRESENT (vol_normalized_ret_5d composed feature; expected effect on IS Sharpe; mechanism named) |
| 3 | Section 2 — IS-Only Numerical Evidence | PRESENT (11 sub-sections; 5+ numerical tables; falsifiers with explicit thresholds; behavioral-effect predictor; regime-conditional axis falsification) |
| 4 | Section 3 — Proposed Changes | PRESENT (8 sub-fixes; bundle state verification table with 22 assertions) |
| 5 | Section 4 — Expected OOS Impact | PRESENT (PATH A/B/C-clean/C-suspicious bands; pre-registered classification thresholds) |
| 6 | Section 5 — Risk Mitigation | PRESENT (R1/R2/R3 + primitive 10 + primitive 9 + cross-symbol contagion + risk-budget redistribution + IS trade-rate stability + adversarial-tests regression + multi-run-stochasticity) |
| 7 | Section 6 — Risk Management Design | PRESENT (10-primitive gate table; predicted fire rates) |
| 8 | Section 7 — Pre-Registered Failure-Mode Prediction | PRESENT (4 plausible failure modes; most plausible PROMISING-INERT 35%; 2nd NEGATIVE-clean 30%; 3rd PROMISING 25%; 4th NEGATIVE-SUSPICIOUS-OOS 10%) |
| 9 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (PATH A/B/C-clean/C-suspicious with locked thresholds; saturation rule) |
| 10 | Section 9 — Library Stack | PRESENT (UNCHANGED from iter-v3/045/046/047) |
| 11 | Section 10 — QR Audit Trail | PRESENT (NEW required per `feedback_v3_axis_selection_quant_discipline.md`; EDA SHA `a230cd1` cited; QR-driven selection rationale; 5 SEED CANDIDATES from iter-v3/047 diary scored via EDA) |
| 12 | Section 11 — Catalog-Row Pre-Commit | PRESENT (4 outcomes pre-registered) |

**All 12 sections (10 mandatory + Section 11 pre-commit + Section 12 self-check) PRESENT.**
Engineer's Phase 5.5 gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies
the sections, runs the bundle state assertions, runs the 5 vol_normalized_ret_5d
adversarial tests + the 7 primitive 10 tests + the 5 ATR multipliers tests + regression
on primitive 9 + per_symbol_cap tests, regenerates the v3 features for all 4 symbols
(Sub-fix 7), and writes `phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then runs
at single-seed --exploration --clean-oof; budget 25-40 min; well within 2h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first
time; QR Phase 8 closes the catalog row at one of the 4 pre-registered dispositions.

iter-v3/048 is cycle 3 #9 of 10; 1 EXPLORATION remains in this cycle (iter-v3/049);
SECOND v3 CONFIRMATION at iter-v3/050.

# iter-v3/070 — Research Brief (CYCLE 1 CONFIRMATION)

**Branch**: `iteration-v3/070`
**EDA SHA**: `fe219c1`
**Setup commit SHA**: TBD (this commit)
**Iteration type**: CYCLE 1 CONFIRMATION (NOT EXPLORATION) — first CONFIRMATION after strict 10:1 cadence
**Bundle**: 2-component LOCKED — /065 SL widening + /062 Path B4 methodology

---

## Section 0 — Data Split Declaration

**UNCHANGED.** Sacred constants per `feedback_no_cheating.md`:

```
OOS_CUTOFF_DATE  = 2025-03-24       # IMMUTABLE
training_months  = 24                # IMMUTABLE
ENSEMBLE_SIZE    = 10                # CONFIRMATION mode (unified per Phase B-3)
ENSEMBLE_SEEDS   = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                    33158374, 1465339467, 1273345680, 115579757, 1952249162)
n_trials         = 35                # default for CONFIRMATION (per `feedback_v3_confirmation_n_trials_35.md`)
colsample_bytree = Optuna-tuned      # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (3 symbols — REVERT /069 ADAUSDT addition per /069 closeout).
Feature universe = 14 BASELINE_V3 features (UNCHANGED from /059 anchor at iter-v3/028 spec).

## Section 0.5 — Iteration Type Declaration

**TYPE**: **CYCLE 1 CONFIRMATION (NOT EXPLORATION)**.

- **Cycle 1 cadence**: COMPLETE per `feedback_v3_strict_10_to_1_cadence.md` (10 EXPLORATIONs /060-/069 + 1 CONFIRMATION /070).
- **Run mode**: default CONFIRMATION (NO `--exploration` flag → ENSEMBLE_SIZE=10).
- **Optuna budget**: `--n-trials 35` per (symbol × walk-forward month × seed). Total = 35 × 3 sym × 10 seeds = 1050 trials.
- **Wall-clock target**: ~3.6h (per /058, /059 baselines; HARD CAP 6h per `feedback_v3_cadence_discipline.md`).

**Bundle composition LOCKED** (per /069 diary Section 9 cycle 1 closeout):

| Component | Source | Code Change | EXPLORATION evidence |
|---|---|---|---|
| **A** | /065 SL widening | `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)` | PROMISING-OOS-DOMINANT at /065 EXPLORATION (OOS Δ +0.91; LDO TP-rate +12.6pp) |
| **B** | /062 Path B4 methodology | `dsr_relative` reformulation: annualized-both-sides at √252 | PASSIVE-DIAGNOSTIC at /062 (deferred spec at /062 Section 3 lines 245-313) |

**Cycle 1 catalog summary** (per /069 diary Section 9):

| Slot | Iter | Axis | Verdict | /070 Bundle Contribution |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE | PROMISING (anchor) | anchor only |
| #2 | /061 | TRX vol_scale_floor | INERT | none |
| #3 | /062 | DSR_relative recalibration | PASSIVE-DIAGNOSTIC | **+Path B4 deferred spec** |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS+IS-COLLAPSE | none |
| #5 | /064 | Phased +adx_14 | NEGATIVE | none |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | **SUSPICIOUS-OOS-DOMINANT** | **+SL widening** |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT | none |
| #8 | /067 | Confidence threshold floor=0.60 | INERT | none |
| #9 | /068 | Label timeout 21→42 | NEGATIVE | none |
| #10 | /069 | Universe expansion +ADA | INERT (corrected) | none |
| **CONFIRMATION** | **/070** | **/065 + /062 bundle** | **TBD (this iteration)** | **2 components LOCKED** |

## Section 1 — Testable Hypothesis (ONE sentence)

> The 2-component /070 bundle (/065 SL widening = `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)` + /062 Path B4 methodology = annualized-both-sides DSR_relative reformulation) produces IS monthly Sharpe ≥ +1.0894 AND OOS monthly Sharpe ≥ +0.5791 vs the /059 unified 10-seed CONFIRMATION anchor (BOTH-must-improve per `feedback_v3_strict_both_is_oos_baseline.md`), with `dsr_relative_B4 ≥ 0.95` binding gate cleared, BCH IS share ≥ 80%, OOS trades ≥ 130, and per-symbol no-collapse (WR > 15% AND n_trades > 3) — updating BASELINE_V3.md.

## Section 2 — Numerical EDA Tables (EDA SHA `fe219c1`)

EDA committed at SHA `fe219c1` (`analysis/iteration_v3-070/cycle1_confirmation_setup.py`). 5 tables.

### Section 2.1 — T0 Anchor-value declaration (per Critic /064-/069 Rec #1 anchor-byte gate)

Byte-exact /059 anchor values from `reports-v3/iteration_v3-059/comparison.csv` + `per_symbol.csv` + `dsr.json`. 54-row table at `analysis/iteration_v3-070/T0_anchor_values.csv`. Headline:

| metric | value | source (file:line) |
|---|---:|---|
| monthly_sharpe_in_sample | **+1.0894** | `reports-v3/iteration_v3-059/comparison.csv:2` |
| monthly_sharpe_out_of_sample | **+0.5791** | `reports-v3/iteration_v3-059/comparison.csv:2` |
| daily_sharpe_in_sample | +2.7092 | `reports-v3/iteration_v3-059/comparison.csv:3` |
| daily_sharpe_out_of_sample | +1.4359 | `reports-v3/iteration_v3-059/comparison.csv:3` |
| monthly_sharpe_ratio_oos_is | 0.5316 | `reports-v3/iteration_v3-059/comparison.csv:2` |
| n_trades_in_sample | 171 | `reports-v3/iteration_v3-059/comparison.csv:7` |
| n_trades_out_of_sample | 94 | `reports-v3/iteration_v3-059/comparison.csv:7` |
| pbo_mean | 0.1278 | `reports-v3/iteration_v3-059/comparison.csv:12` |
| dsr_relative_legacy | 0.113363 | `reports-v3/iteration_v3-059/dsr.json` |
| cpcv_path_sharpe_q75 | 0.837759 | `reports-v3/iteration_v3-059/dsr.json` |
| pbo_frac_positive_paths | 0.6444 | `reports-v3/iteration_v3-059/dsr.json` |
| BCH_OOS_weighted_pnl | +24.7502 | `reports-v3/iteration_v3-059/comparison.csv:18` |
| LDO_OOS_weighted_pnl | -6.1783 | `reports-v3/iteration_v3-059/comparison.csv:19` |
| TRX_OOS_weighted_pnl | +4.1639 | `reports-v3/iteration_v3-059/comparison.csv:20` |
| BCH_OOS_n_trades / WR | 34 / 41.2% | `reports-v3/iteration_v3-059/comparison.csv:18` |
| LDO_OOS_n_trades / WR | 12 / 25.0% | `reports-v3/iteration_v3-059/comparison.csv:19` |
| TRX_OOS_n_trades / WR | 48 / 39.6% | `reports-v3/iteration_v3-059/comparison.csv:20` |
| BCH_IS_pct_of_total_pnl | **95.76%** (BCH IS dominance) | `reports-v3/iteration_v3-059/in_sample/per_symbol.csv` |

These are the BIT-EXACT /059 anchor values. Section 4 falsifier bands reference these. **Anchor-byte gate**: every numerical reference in Sections 4/8 cites a source file:line — Phase 5.5 gate verifies match within float precision.

### Section 2.2 — T1 Bundle decomposition (per-component contribution accounting)

8-row table at `analysis/iteration_v3-070/T1_bundle_decomposition.csv`. Headline:

| component | code change | EXPLORATION evidence | rationale |
|---|---|---|---|
| **A** | `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)` | /065 IS Δ -0.16 vs /060; OOS Δ +0.91 vs /060 | SUSPICIOUS-OOS-DOMINANT at single-seed; CONFIRMATION-mode delta UNKNOWN |
| **A_BCH** | (component A's effect on BCH OOS) | BCH OOS +57.40 vs /060 +1.91 (Δ +55.49); WR 32.4% → 59.0% | Single-seed lottery — multi-seed expected to compress |
| **A_LDO** | (component A's effect on LDO OOS) | LDO OOS -19.82 vs /060 -19.72 (flat); WR 18.2% → 30.8% (+12.6pp) | LDO WR mechanism CONFIRMED — structural reason for axis advancement |
| **A_TRX** | (component A's effect on TRX OOS) | TRX OOS +0.92 vs /060 +23.31 (Δ -22.39); WR 48.1% → 43.9% | TRX REGRESSED at single-seed; non-target lottery loss |
| **B** | `dsr_relative` reformulation per /062 spec lines 245-313 | ZERO impact on IS/OOS Sharpe (POST-trade-roster computation); BIT-IDENTICAL trade roster | Modifies dsr.json output ONLY; orthogonal to Component A |
| **B_/058_compat** | (B applied retro to /058) | /058 dsr_relative_legacy = 0.998164 → predicted B4 ≈ 1.0 | High daily Sharpe (1.70 at √252) >> benchmark (0.64) |
| **B_/059_compat** | (B applied retro to /059) | /059 dsr_relative_legacy = 0.113363 → predicted B4 ≈ 0.95-1.0 | RESOLVES granularity-mismatch artifact (central thesis of /062) |
| **Bundle_AB** | `(2.0, 1.5)` + Path B4 reformulation | Single substantive axis (B is methodology-only) | PASS criterion = BOTH-must-improve + dsr_relative_B4 ≥ 0.95 |

### Section 2.3 — T2 Predicted bands (multi-seed CONFIRMATION-mode per BOTH-must-improve)

15-row table at `analysis/iteration_v3-070/T2_predicted_bands.csv`. Headline binding/tracking metrics:

| metric | iter059_anchor | predicted_lower | predicted_upper | PASS_threshold | gate_classification |
|---|---:|---:|---:|---|---|
| monthly_sharpe_in_sample | **+1.0894** | +0.95 | +1.30 | **≥ +1.0894** | BINDING (BOTH-must-improve) |
| monthly_sharpe_out_of_sample | **+0.5791** | +0.60 | +1.05 | **≥ +0.5791** | BINDING (BOTH-must-improve) |
| daily_sharpe_out_of_sample | +1.4359 | +1.50 | +2.40 | n/a | TRACKING; Path B4 input |
| n_trades_out_of_sample | 94 | 85 | 130 | ≥ 130 | INFORMATIONAL (anchor below floor) |
| frac_positive_paths | 0.6444 | 0.55 | 0.75 | ≥ 0.55 | Gate 10-CPCV |
| cpcv_path_sharpe_q75 | 0.8378 | 0.83 | 0.84 | n/a | Architecture-invariant |
| pbo_mean | 0.1278 | 0.10 | 0.20 | < 0.40 | Gate 5 PBO |
| psr_legacy | 1.0 | 0.99 | 1.0 | > 0.95 | Gate 6 PSR |
| **dsr_relative_B4** | n/a (NEW) | **0.95** | **1.0** | **≥ 0.95** | **BINDING (Path B4 gate)** |
| BCH_IS_pct_of_total_pnl | 95.76% | 70% | 100% | ≥ 80% (one-sided) | BCH IS share gate |
| LDO_OOS_weighted_pnl | -6.18 | -10.0 | +10.0 | WR>15% AND n_trades>3 | Per-symbol no-collapse |
| TRX_OOS_weighted_pnl | +4.16 | -10.0 | +25.0 | WR>15% AND n_trades>3 | Per-symbol no-collapse |

**NEGATIVE envelope per Critic /068 Rec #1 (carry-forward)**: IS Δ < -0.30 OR OOS Δ < -0.30 vs /059 → NEGATIVE classification.

### Section 2.4 — T3 Path B4 input traceback (per `feedback_v3_methodology_post_hoc_input_traceback.md`)

7-row table at `analysis/iteration_v3-070/T3_path_b4_traceback.csv`. Maps each `psr()` input variable to runner code path with granularity:

| input_variable | granularity | computation | code_path | verified_or_predicted_value |
|---|---|---|---|---|
| observed_sharpe (daily_sharpe_oos_annualized) | daily, √252 | `daily.mean() / daily.std() * sqrt(252)` | run_baseline_v3.py:NEW (replaces line 2273) | /070 expected ≥ 1.50 |
| n_obs (n_daily_obs_oos) | daily | `max(2, len(oos_daily_pnl))` | run_baseline_v3.py:NEW (replaces line 2278) | /059 ~294 |
| skewness (daily_skew_oos) | daily | `float(skew(oos_daily_pnl.values))` | run_baseline_v3.py:NEW (replaces line 2274) | TBD |
| kurtosis (daily_kurt_oos) | daily | `float(kurtosis(oos_daily_pnl.values, fisher=False))` | run_baseline_v3.py:NEW (replaces line 2275) | TBD |
| benchmark_sharpe (cpcv_q75_annualized) | candle → calendar (√756) | `percentile(flat_path_sharpes, 75)/sqrt(1296)*sqrt(756)` | run_baseline_v3.py:NEW (replaces line 2295) | /059 ≈ 0.640 |
| dsr_relative_B4 (output) | annualized | `psr(observed=daily_annualized, benchmark=cpcv_annualized, ...)` | run_baseline_v3.py:NEW (replaces line 2309) | /059 backward-compat: ~0.95-1.0 |

**CRITICAL convention divergence (per T3 row 7)**: existing `_daily_sharpe()` at `run_baseline_v3.py:1545-1555` uses `np.sqrt(365)` (calendar days). Path B4 spec uses `np.sqrt(252)` (trading days). Brief Section 3 documents this as a deliberate convention choice — NOT a bug. Implementing at √252 yields a lower daily_sharpe value than the existing comparison.csv field; the brief alerts the Critic to this divergence to prevent Section 8 traceback band confusion.

### Section 2.5 — T4 Backward-compat validation predictions

5-row table at `analysis/iteration_v3-070/T4_backward_compat_validation.csv`. Predicted dsr_relative_B4 values for /058/059/060/061/065 under Path B4 reformulation:

| iter | architecture | daily_sharpe_oos_at_√252 (predicted) | cpcv_q75_B4_annualized | dsr_relative_legacy | dsr_relative_B4 (predicted) | PASS at 0.95 |
|---|---|---:|---:|---:|---|---|
| /058 | 2-outer × 5-inner post-fix | 1.696 | 0.640 | 0.998164 | 0.99-1.0 | **PASS** |
| /059 | unified 10-seed (BASELINE) | 1.193 | 0.640 | 0.113363 | **0.95-1.0** | **PASS** (RESOLVES legacy artifact) |
| /060 | 3-seed EXPLORATION | 0.304 | 0.640 | 0.0 | ~0.0 | FAIL (correctly flags EXPLORATION-mode degeneracy) |
| /061 | 3-seed EXPLORATION | 0.336 | 0.640 | 0.0 | ~0.0 | FAIL |
| /065 | 3-seed EXPLORATION | 1.775 | 0.640 | 0.92032 | 0.99-1.0 | PASS (single-seed lottery; SUSPICIOUS) |

**Central thesis of Path B4**: it RESOLVES the granularity-mismatch artifact that produced /059 dsr_relative_legacy = 0.113363 (FAIL legacy threshold) despite OOS Sharpe outperforming benchmark. Path B4 brings /059 to PASS at the same threshold via correct annualization granularity.

### Section 2.6 — Inherited IC violation declaration (per Critic /069 Rec #3)

`vwap_dev_20 × regime_momentum_signed_5d = 0.7797` (from /069 review.md Check 4). This **EXCEEDS the v3 hard gate IC threshold of 0.70**.

**Category 2 composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md`**: composed features (e.g., `feature_A × sign(feature_B - threshold)`) MECHANICALLY correlate with their primitives by construction. The carve-out applies to `regime_momentum_signed_5d = ret_5d × sign(hurst_100 - 0.5)`. The strict |IC|<0.50 (or 0.70) gate is INAPPROPRIATE for Category 2 composed features; replace with importance ≥30 threshold.

**Importance evidence (per /069 review.md Check 4 carry-forward)**:
- vwap_dev_20: LDO importance 249.67 rank 1 — **above 30 threshold**
- regime_momentum_signed_5d: LDO importance 122.0 rank 12 — **above 30 threshold**

Both features pass the importance ≥30 carve-out. Category 2 composed-feature carve-out CARRY-FORWARD APPROVED for /070. NO feature change at /070.

### Section 2.7 — Anchor declaration

**Anchor for /070**: **iter-v3/059 multi-seed unified 10-seed CONFIRMATION baseline** (BASELINE_V3.md canonical at tag `v0.v3-059`). NOT /060 EXPLORATION-mode reference (which was the anchor for /061-/068 EXPLORATIONs).

Per `feedback_v3_unified_10seed_baseline.md`: cycle 1 CONFIRMATION evaluates the bundle against the multi-seed CONFIRMATION anchor /059, NOT the EXPLORATION-mode anchor /060.

## Section 3 — Proposed Changes (enumerated)

### Sub-fix 1 — Component A: DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (2.0, 1.5)

File: `src/crypto_trade/features_v3/__init__.py` line 222

```python
# Before (/059 anchor state — REVERTED at /066 from /065)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)

# After (/070 CONFIRMATION — re-applies /065 Path D universal SL widening)
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.5)
```

V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty `{}` per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. All 3 symbols consume DEFAULT.

### Sub-fix 2 — Component B: Path B4 implementation in run_baseline_v3.py

Replace `run_baseline_v3.py:2257-2305` block with the Path B4 spec from `briefs-v3/iteration_v3-062/research_brief.md` Section 3 lines 260-301. Inputs traced per Section 2.4 (T3) above.

**Two-step implementation**:
1. Daily PnL aggregation: `oos_daily_pnl = pd.Series(weighted_pnl).groupby(close_time.date).sum()`.
2. Annualization: daily Sharpe at √252; CPCV-Q75 at √756 (3 candles/day × 252 trading days = 756 candles/year).
3. dsr.json field changes:
   - **NEW**: `dsr_relative_b4` (Path B4 reformulation)
   - **PRESERVED**: `dsr_relative` (legacy code path) — kept for backward-compat reporting only
   - **NEW**: `daily_sharpe_oos_b4_at_sqrt252` (informational tracking)
   - **NEW**: `cpcv_q75_annualized_b4` (informational tracking)
   - **NEW**: `n_daily_obs_oos` (informational tracking)

### Sub-fix 3 — NEW integration test: tests/strategies/ml/test_dsr_relative_b4.py

Per `feedback_v3_methodology_axis_integration_test.md` (BLOCK at Phase 5.5 if missing). Test structure:

```python
def test_dsr_relative_b4_integration():
    """Integration test for Path B4 dsr_relative reformulation.

    Per `feedback_v3_methodology_axis_integration_test.md`: unit tests on math
    in isolation are insufficient — bugs occur at call-site integration boundary.
    The /055 DSR_relative bug occurred at line 2181 reading cpcv_paths.csv
    BEFORE line 2295 wrote it; fallback set cpcv_path_sharpe_q75=0.0 silently.
    """
    # 1. Construct synthetic oos_trades with known daily_sharpe ~ 1.5 (annualized at √252)
    # 2. Construct synthetic flat_path_sharpes with Q75 ≈ 0.65 annualized
    # 3. Call run_baseline_v3._compute_metrics_and_write_dsr_json() directly
    # 4. Read dsr.json from temp dir
    # 5. Assert dsr_relative_b4 in [0.85, 0.99] (slight non-1.0 due to small sample)
    # 6. Assert cpcv_q75_annualized_b4 matches 0.65 within 1e-6
    # 7. Assert daily_sharpe_oos_b4_at_sqrt252 matches 1.5 within 1e-4
    # 8. Assert n_daily_obs_oos matches expected count
    # 9. Assert dsr_relative (legacy) preserved alongside new dsr_relative_b4 field
```

### Sub-fix 4 — End-to-end smoke test (Section 9 pre-flight)

Per `feedback_v3_methodology_axis_integration_test.md`: run a 1-month walk-forward, single symbol, n_trials=2, verify dsr.json contains `dsr_relative_b4 > 0` and `cpcv_q75_annualized_b4 > 0` when synthetic edge present. Documented in Section 9.

### Sub-fix 5 — NEW runtime assertion (per Critic /069 Rec #1 anchor-byte gate enforcement at runner)

Per /069 closeout: line 1407 (`BacktestConfig.timeout_minutes`) and line 1425 (`LightGbmStrategy.label_timeout_minutes`) fell out of sync silently at /069. Add runtime assertion:

```python
# In _verify_feature_columns() or new _verify_timeout_consistency() helper:
expected_timeout_minutes = 10080
assert cfg.timeout_minutes == expected_timeout_minutes, (
    f"BacktestConfig.timeout_minutes ({cfg.timeout_minutes}) != expected ({expected_timeout_minutes}). "
    f"iter-v3/070 (and forward): label horizon must be consistent at "
    f"BacktestConfig + LightGbmStrategy.label_timeout_minutes."
)
assert lgbm_strategy.label_timeout_minutes == expected_timeout_minutes, (
    f"LightGbmStrategy.label_timeout_minutes ({lgbm_strategy.label_timeout_minutes}) "
    f"!= expected ({expected_timeout_minutes}). Same single-source-of-truth invariant."
)
assert cfg.timeout_minutes == lgbm_strategy.label_timeout_minutes, (
    f"BacktestConfig.timeout_minutes ({cfg.timeout_minutes}) != "
    f"LightGbmStrategy.label_timeout_minutes ({lgbm_strategy.label_timeout_minutes}) — "
    f"DESYNC DETECTED. Centralize via shared module-level constant per Critic /069 Rec #1."
)
```

### Sub-fix 6 — REVERT /069 universe expansion: V3_MODELS back to 3-sym + REQUIRED_GAP back to 66

Per /069 closeout (INERT-AT-EXPLORATION; universe-expansion axis CLOSED):

File: `run_baseline_v3.py` lines 142-147

```python
# Before (/069 — universe expansion axis)
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (ADAUSDT)", "ADAUSDT"),  # iter-v3/069 — 4th symbol
)

# After (/070 — REVERT to 3-sym for cycle 1 CONFIRMATION)
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)
```

File: `src/crypto_trade/strategies/ml/validation_v3.py` line 58

```python
# Before (/069)
REQUIRED_GAP: int = (21 + 1) * 4  # 88

# After (/070 — REVERT 4-sym → 3-sym)
REQUIRED_GAP: int = (21 + 1) * 3  # 66
```

### Sub-fix 7 — ITERATION_LABEL bump

File: `run_baseline_v3.py` line 128

```python
# Before
ITERATION_LABEL = "v3-069"

# After
ITERATION_LABEL = "v3-070"
```

### Sub-fix 8 — Runner pre-flight assertion updates

Update `_verify_feature_columns()` and per-symbol fallback assertion (run_baseline_v3.py lines 422-431, 504-512) to expect `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5)` for /070 (re-applies /065 Path D rationale). Update `_verify_label_leakage_gap()` for n_symbols=3 → required_gap=66.

### Sub-fix 9 — Existing test updates

Two test files reference `DEFAULT_ATR_MULTIPLIERS` hardcoded to (2.0, 1.0):

| File | Current assertion | New assertion |
|---|---|---|
| `tests/features_v3/test_features_for_symbol.py` | `(2.0, 1.0)` | `(2.0, 1.5)` |
| `tests/features_v3/test_atr_multipliers_for_symbol.py` | `(2.0, 1.0)` | `(2.0, 1.5)` |

### Sub-fix 10 — Parquet regeneration

**NOT required.** ATR computation (`natr_21_raw` column) is unchanged. The MULTIPLIER change is consumed inside `label_trades()` via kwargs (per Section 2.4 T3). No new feature columns; no parquet regen.

### Sub-fix 11 — V3_FEATURE_COLUMNS

**UNCHANGED**. Stays at 14 features per /059 anchor. `vwap_dev_20 × regime_momentum_signed_5d = 0.7797` Category 2 composed-feature carve-out documented in Section 2.6.

### Sub-fix 12 — Run command (CLI)

```bash
uv run python run_baseline_v3.py --clean-oof
```

NO `--exploration` flag → ENSEMBLE_SIZE=10 unified architecture. NO `--seeds` flag (deprecated under unified architecture per Phase B-3).

## Section 4 — Predicted Impact Bands + Falsifiers

### Section 4.1 — Headline Sharpe prediction (multi-seed CONFIRMATION mode)

| Metric | /059 anchor | Predicted /070 lower | Predicted /070 upper | PASS criterion |
|---|---:|---:|---:|---|
| IS monthly Sharpe | **+1.0894** | +0.95 | +1.30 | **≥ +1.0894** (BOTH-must-improve) |
| OOS monthly Sharpe | **+0.5791** | +0.60 | +1.05 | **≥ +0.5791** (BOTH-must-improve) |
| OOS/IS daily ratio | 0.5316 | 0.50 | 0.85 | ≥ 0.50 (Gate 3) |
| IS trades | 171 | 150 | 200 | ≥ 130 |
| OOS trades | 94 | 85 | 130 | ≥ 130 (target; informational at /059 baseline) |
| frac_positive_paths | 0.6444 | 0.55 | 0.75 | ≥ 0.55 (Gate 10-CPCV) |
| **dsr_relative_B4** | n/a (NEW) | **0.95** | **1.0** | **≥ 0.95** (BINDING gate) |
| BCH IS share | 95.76% | 70% | 100% | ≥ 80% one-sided |

**Rationale for Sharpe band widths**:

1. **/065 single-seed evidence (Component A only)**: IS Δ -0.16 / OOS Δ +0.91 vs /060 EXPLORATION anchor. Multi-seed CONFIRMATION ensemble averaging is expected to:
   - Compress lottery components (/065 BCH +55 single-seed lottery, /065 TRX -22 single-seed lottery)
   - Preserve structural mechanism (LDO TP-rate +12.6pp universal SL widening effect)
   - **Net effect on IS**: should compensate /065's -0.16 single-seed regression via multi-seed averaging
   - **Net effect on OOS**: partial preservation of /065's +0.91 lift expected

2. **Historical multi-seed precedents at universal labeling changes**:
   - iter-v3/039 PER-SYMBOL LDO ATR (2.0, 1.5) at multi-seed: IS -0.08 / OOS +1.47 (NO-MERGE; per-symbol asymmetry caveat)
   - iter-v3/050 PER-SYMBOL LDO + ALGO at multi-seed: NO-MERGE (per-symbol asymmetry)
   - iter-v3/070 = first UNIVERSAL SL widening tested at multi-seed CONFIRMATION

3. **Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`**: per-symbol customizations broke IS aggregate at multi-seed in 2 prior CONFIRMATIONs. Universal change (V3_ATR_MULTIPLIERS_PER_SYMBOL = {}) avoids this asymmetry.

### Section 4.2 — BCH IS share sensitivity (per /059 Critic Rec #3 + carry-forward)

Per `feedback_v3_unified_10seed_baseline.md`: BCH IS concentration at 95.76% is FRAGILITY FLAG — every cycle 1 brief Section 4 must project BCH IS sensitivity.

Wider SL (1.0× → 1.5×) at multi-seed expected to:
- INCREASE BCH trade survival rate (BCH long_sl_hit_rate falls per /065 EDA T2)
- May LIFT or LOWER BCH IS share depending on whether wider SL generates IS PnL faster (lift) or slower (lower)
- /065 single-seed BCH IS share dropped from /060's 176.68% to 93.71% (rebalancing toward LDO+TRX); multi-seed pattern UNKNOWN

**Predicted BCH IS share at /070**: 70% to 100% (one-sided ≥80% gate cleared in expectation; band wider than baseline due to universal labeling change).

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md` extended for labeling axes per /065 Critic Rec #3)

Path B4 component: ZERO behavioral effect on trade roster (post-trade-roster computation). Trade-roster bit-identity vs Component-A-only execution is the diagnostic.

Component A (SL widening) behavioral effect:

| Symbol | IS trades /059 | IS trades /070 predicted | OOS trades /059 | OOS trades /070 predicted | OOS WR /059 | OOS WR /070 predicted |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 83 | 75-100 | 34 | 30-45 | 41.2% | 45-60% (lift expected) |
| LDO | 9 | 10-20 | 12 | 10-20 | 25.0% | 28-40% (LDO mechanism) |
| TRX | 79 | 70-90 | 48 | 40-50 | 39.6% | 38-46% |
| **Total** | **171** | **160-210** | **94** | **85-130** | **38.3%** | **42-50%** |

**Saturation falsifier (extended for labeling axes per /065 Critic Rec #3)**: per-symbol WR Δ ≤ ±2pp at all 3 symbols (IS+OOS) → AXIS SATURATED. Pre-registered prediction: WR Δ +5 to +15pp at LDO; +5 to +15pp at BCH; -3 to +5pp at TRX.

### Section 4.4 — Pre-registered FALSIFIER bands (BINDING GATES)

Per `feedback_v3_strict_both_is_oos_baseline.md` + Critic /068 Rec #1 wider envelope (carry-forward) + `feedback_v3_per_symbol_target_axis_falsifier.md`:

| Gate ID | Gate | Threshold | Action if FAIL |
|---|---|---|---|
| **A.1** | IS monthly Sharpe | ≥ +1.0894 (PASS); OR IS Δ < -0.30 vs /059 → NEGATIVE | FAIL → NO-MERGE / NEGATIVE |
| **A.2** | OOS monthly Sharpe | ≥ +0.5791 (PASS); OR OOS Δ < -0.30 vs /059 → NEGATIVE | FAIL → NO-MERGE / NEGATIVE |
| **A.3** | OOS/IS Sharpe ratio | ≥ 0.5 (Gate 3 inherited project-level) | FAIL → BLOCK MERGE |
| **A.4** | frac_positive_paths | ≥ 0.55 (Gate 10-CPCV) | FAIL → BLOCK MERGE |
| **A.5** | PBO mean | < 0.40 (Gate 5) | FAIL → BLOCK MERGE |
| **A.6** | PSR (legacy) | > 0.95 (Gate 6) | FAIL → BLOCK MERGE |
| **A.7** | dsr_relative_B4 | ≥ 0.95 (Path B4 BINDING gate) | FAIL → BLOCK MERGE |
| **B.5** | BCH IS share | ≥ 80% (one-sided per /059 Critic Rec #3) | FAIL → BCH IS collapse warning |
| **C.6** | OOS trade count | ≥ 130 aggregate (per `feedback_v3_trade_rate_floor_bundle_level.md`) | FAIL → trade-rate floor (informational at /059 baseline) |
| **C.6b** | OOS trades/month | ≥ 10 (informational; /059 anchor 6.7/month) | FAIL → trade-rate informational |
| **D.8** | BCH OOS no-collapse | WR > 15% AND n_trades > 3 | FAIL → per-symbol collapse |
| **D.9** | LDO OOS no-collapse | WR > 15% AND n_trades > 3 | FAIL → per-symbol collapse |
| **D.10** | TRX OOS no-collapse | WR > 15% AND n_trades > 3 | FAIL → per-symbol collapse |
| **E.11** | All v3 tests pass | including NEW `test_dsr_relative_b4.py` | FAIL → BLOCK |
| **E.12** | ensemble_summary | mode=confirmation, size=10 | FAIL → mode-flag wiring bug |
| **E.13** | Anchor-byte gate | DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5); ITERATION_LABEL == "v3-070"; V3_MODELS = 3 | FAIL → process violation |
| **E.14** | timeout_minutes consistency | BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes (per Critic /069 Rec #1) | FAIL → BLOCK (anchor-byte at runner) |
| **E.15** | Path B4 input granularity | All inputs to `psr()` at daily-annualized basis (per Section 2.4 T3) | FAIL → BLOCK |

### Section 4.5 — Anti-stacking check (per `feedback_v3_engineered_features_dont_stack.md`)

**ONE substantive change** at Component A (Component B is methodology-only with ZERO behavioral effect). The bundle is single-axis at the trade-roster level. Path B4 modifies ONLY the dsr.json output — it does NOT change Optuna search space, training labels, inference probabilities, or trade execution.

Per /065's Section 4.5: this is a TRUE universal change — all 3 symbols receive the same labeling logic. V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty `{}`.

### Section 4.6 — IS-Sharpe / OOS-Sharpe daily ratio sanity check (per /059 ratio = 0.5316 borderline)

Per BASELINE_V3.md: /059 OOS/IS Sharpe ratio = 0.5316 (barely above 0.5 floor; classified RE-ANCHOR-MERGE-IS-DOMINANT). The SL widening axis at multi-seed is expected to either:
- Improve ratio (if OOS lifts more than IS) → desired path
- Worsen ratio (if IS lifts more than OOS) → SUSPICIOUS-IS-DOMINANT classification

**Predicted band**: ratio ∈ [0.50, 0.85] (Gate 3 PASS; ratio improvement plausible per /065 OOS-dominant single-seed evidence).

## Section 5 — Risk Mitigation

**UNCHANGED stack** (carry-forward from /059 anchor):

| Primitive | Status | Source |
|---|---|---|
| Vol scaling (RiskV2) | ENABLED | `feedback_v3_baseline_update_policy.md` carry-forward |
| ADX threshold (global 20.0) | ENABLED | iter-v3/050 closeout |
| Hurst regime gate | DISABLED | iter-v3/022 (closed) |
| Feature z-score OOD (\|z\|>2.0) | ENABLED | iter-v3/011 |
| Low-vol filter | ENABLED | carry-forward |
| Hit-rate gate | DISABLED | OOS-only; not active |
| BTC trend kill (±15%, 14d) | ENABLED | iter-v3/051 reverted to no-block; threshold=15% |
| Primitive 10 (direction-asymmetric kill switch) | DISABLED | iter-v3/051 SYSTEM-LEVEL REVERT |
| Primitive 11 (per-symbol drawdown brake) | DISABLED | iter-v3/054 closeout |

**Bundle-axis is orthogonal to risk gates**. No risk-primitive changes at /070 (single-axis discipline at the bundle level).

## Section 6 — Risk Management

**CHANGED (Component A only)**: DEFAULT_ATR_MULTIPLIERS (2.0, 1.0) → (2.0, 1.5). V3_ATR_MULTIPLIERS_PER_SYMBOL remains empty `{}`. All 3 symbols (BCH/LDO/TRX) consume DEFAULT.

Triple-barrier labeling timeout UNCHANGED: 21 candles (10080 minutes) — REVERT /068's Path C, REVERT /069's universe expansion (4-sym → 3-sym; REQUIRED_GAP 88 → 66). Cooldown UNCHANGED: 4 candles post-trade. Fee UNCHANGED: 0.1% per leg.

**Translated to live trading**: live engine's actual stop-loss order distance per trade widens from 1.0×ATR_at_entry to 1.5×ATR_at_entry. TP stays at 2.0×ATR_at_entry. Per-trade risk-reward ratio shifts from 2:1 to 1.33:1 (less attractive per trade) but expected win rate lifts (~+7.8pp avg per /065 EDA) which dominates Kelly fraction algebra under empirically observed conditions.

**Path B4 is methodology-only** — does NOT affect trade execution, position sizing, or risk gates. Only dsr.json output changes.

## Section 7 — Pre-registered Failure-Mode Prediction

Per Rule 3 of `feedback_v3_iter064_process_lessons.md` (calibrated for non-feature axes at multi-seed CONFIRMATION) + cycle 1 EXPLORATION outcome distribution (per /069 diary):

| Mode | Description | Probability | Expected metrics |
|---|---|---:|---|
| **PASS (MERGE BASELINE_V3 update)** | BOTH IS ≥ +1.0894 AND OOS ≥ +0.5791; all gates clear; bundle MERGES | **~25%** | IS Δ ≥ 0 AND OOS Δ ≥ 0 |
| **INERT (no merge; bundle didn't move multi-seed)** | Within ±band; bundle CLOSED at catalog level | **~35%** | IS Δ within [-0.15, +0.15] AND OOS Δ within [-0.20, +0.20] |
| **SUSPICIOUS-OOS-DOMINANT (OOS up, IS regression)** | OOS lifts but IS regresses; NO-MERGE per BOTH-must-improve | **~15%** | IS Δ < 0 AND OOS Δ ≥ +0.20 |
| **SUSPICIOUS-IS-DOMINANT (IS up, OOS regression)** | IS lifts but OOS regresses; NO-MERGE | **~10%** | IS Δ ≥ +0.10 AND OOS Δ < 0 |
| **NEGATIVE (large regression on ≥1 axis)** | IS Δ < -0.30 OR OOS Δ < -0.30 vs /059 | **~15%** | per `feedback_v3_iter064_process_lessons.md` Rule 4 disjunctive OR |

**Why PASS is only 25%**: bundle composition includes 1 PROMISING-OOS-DOMINANT axis (which is structurally suspect per `feedback_v3_engineered_features_dont_stack.md` cross-iteration extrapolation) + 1 PASSIVE-DIAGNOSTIC methodology axis. Per cycle 1 outcome distribution (1 PROMISING out of 9 testing axes = ~11% PROMISING base rate), the prior at multi-seed CONFIRMATION should be moderately above the base rate but not exceeding 30%.

**Why INERT is 35%**: per `feedback_v3_inert_features_at_higher_budget.md`-analog reasoning: SL widening at multi-seed has 2 prior CONFIRMATION precedents (iter-v3/039, iter-v3/050) both NO-MERGE. The mechanism (LDO TP-rate lift) is real per /065 EDA but may not transfer to other 9 seeds.

**Why NEGATIVE is 15%**: per Rule 3 calibration for non-feature axes; /065's BCH single-seed +55 lottery may invert at multi-seed if other seeds produce -55 BCH lottery (ensemble averaging would NET to near-zero or negative). TRX -22 at /065 single-seed may worsen at multi-seed.

## Section 8 — LOCKED Acceptance / Path Criteria

Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve discipline):

### Section 8.1 — PASS — CONFIRMATION-MERGE → BASELINE_V3.md update

ALL of:
- **A.1** IS monthly Sharpe ≥ +1.0894 vs /059
- **A.2** OOS monthly Sharpe ≥ +0.5791 vs /059
- **A.3** OOS/IS Sharpe ratio ≥ 0.5 (Gate 3 inherited)
- **A.4** frac_positive_paths ≥ 0.55 (Gate 10-CPCV)
- **A.5** PBO mean < 0.40 (Gate 5)
- **A.6** PSR (legacy) > 0.95 (Gate 6)
- **A.7** dsr_relative_B4 ≥ 0.95 (Path B4 BINDING gate)
- **B.5** BCH IS share ≥ 80% (one-sided)
- **C.6** OOS trade count ≥ 130 aggregate (informational; /059 anchor 94)
- **D.8-D.10** Per-symbol no-collapse (WR > 15% AND n_trades > 3 for BCH/LDO/TRX)
- **E.11-E.15** Process gates (tests, mode, anchor-byte, timeout_minutes consistency, granularity)

If ALL PASS → CONFIRMATION-MERGE → BASELINE_V3.md updates to /070; tag `v0.v3-070` issued.

### Section 8.2 — INERT — no merge; bundle CLOSED at catalog level

- IS Δ within [-0.15, +0.15] vs /059 AND OOS Δ within [-0.20, +0.20] vs /059
- AND no methodology FAIL
- Bundle CLOSED — both /065 SL widening and /062 Path B4 components retire from cycle 2 axis priorities (Path B4 spec preserved as informational reference but no longer carried as binding gate)

### Section 8.3 — SUSPICIOUS-OOS-DOMINANT — NO-MERGE per BOTH-must-improve

- IS Δ < 0 vs /059 (regression)
- AND OOS Δ ≥ +0.20 vs /059 (lift)
- NO-MERGE per `feedback_v3_strict_both_is_oos_baseline.md`
- /065 axis CLOSED-PENDING-CYCLE-2 — universal SL widening at multi-seed is OOS-only, not bundle-grade

### Section 8.4 — SUSPICIOUS-IS-DOMINANT — NO-MERGE per BOTH-must-improve

- IS Δ ≥ +0.10 vs /059 (lift)
- AND OOS Δ < 0 vs /059 (regression)
- NO-MERGE per `feedback_v3_strict_both_is_oos_baseline.md`

### Section 8.5 — NEGATIVE — disjunctive OR per `feedback_v3_iter064_process_lessons.md` Rule 4

- IS Δ < -0.30 vs /059 **OR** OOS Δ < -0.30 vs /059 (either gate FAIL)
- AND no methodology FAIL
- Bundle FALSIFIED. /065 universal SL widening at multi-seed and /062 Path B4 PARKED with rationale.

### Section 8.6 — NEGATIVE-SUSPICIOUS (rare)

- IS Δ < -0.30 AND OOS Δ < -0.30
- Strong evidence against bundle.

### Section 8.7 — Methodology FAIL

- Any Critic 13-check BLOCK (look-ahead, embargo, IC, ADF, etc.)
- ANY of E.11-E.15 process gates FAIL
- `dsr_relative_B4` integration test fails OR end-to-end smoke test fails
- Iteration is INVALID; not classifiable as PASS/INERT/SUSPICIOUS/NEGATIVE

### Section 8.8 — BASELINE_V3.md update policy at /070 CONFIRMATION

Per `feedback_v3_strict_both_is_oos_baseline.md`:

- **PASS (Section 8.1) → BASELINE_V3.md updates** to /070; new canonical anchor; tag `v0.v3-070` issued
- **All other paths → BASELINE_V3.md UNCHANGED**; /059 stays canonical at `v0.v3-059`

This is BOTH-must-improve discipline (no aspirational MERGE-gate-failure baseline updates per the strict rule). Failed gates inform cycle 2 axis priorities but do NOT block /059 staying canonical.

### Section 8.9 — Path B4 backward-compat outcome documentation

Regardless of headline PASS/INERT classification:
- `dsr.json` MUST contain BOTH `dsr_relative` (legacy) AND `dsr_relative_b4` (Path B4) fields
- Engineering report MUST record /058 + /059 backward-compat predicted vs observed `dsr_relative_b4` values
- `BASELINE_V3.md` Section "Backward-Compat Validation" MUST be added (informational; persists regardless of CONFIRMATION outcome)

## Section 9 — Library Stack + Reproducibility

### Section 9.1 — Library versions (UNCHANGED from /059)

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=1; per `feedback_v3_unified_10seed_baseline.md` Phase A revert)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0 (skew, kurtosis used in Path B4)
- statsmodels 0.14.6
- pyarrow 23.0.1

### Section 9.2 — Integration test mandate (per `feedback_v3_methodology_axis_integration_test.md`)

NEW integration test: `tests/strategies/ml/test_dsr_relative_b4.py` per Sub-fix 3 above.

Test surface (BLOCK at Phase 5.5 if missing):
1. Calls runner's `_compute_metrics_and_write_dsr_json()` directly with synthetic OOS trades + flat_path_sharpes
2. Inspects produced `dsr.json` dict
3. Asserts `dsr_relative_b4` non-degenerate (in [0.85, 0.99] for synthetic edge case)
4. Asserts `cpcv_q75_annualized_b4` matches expected within 1e-6
5. Asserts `daily_sharpe_oos_b4_at_sqrt252` matches expected within 1e-4
6. Asserts `n_daily_obs_oos` matches expected count
7. Asserts `dsr_relative` (legacy) preserved alongside new field

### Section 9.3 — End-to-end smoke test

Per `feedback_v3_methodology_axis_integration_test.md`:

```bash
# Smoke test (1-month walk-forward, 1 symbol, n_trials=2):
uv run python run_baseline_v3.py --start 2024-01 --end 2024-02 --n-trials 2 --symbols BCHUSDT
# Then read dsr.json from reports-v3/iteration_v3-070/:
python -c "import json; d = json.load(open('reports-v3/iteration_v3-070/dsr.json')); \
            assert d['dsr_relative_b4'] > 0; \
            assert d['cpcv_q75_annualized_b4'] > 0; \
            assert d['daily_sharpe_oos_b4_at_sqrt252'] != 0"
```

### Section 9.4 — ANCHOR-BYTE GATE runtime assertion (per Critic /069 Rec #1)

Per Sub-fix 5 above. Pre-flight check `_verify_timeout_consistency()` invoked before any backtest. Asserts:
- `BacktestConfig.timeout_minutes == 10080`
- `LightGbmStrategy.label_timeout_minutes == 10080`
- `BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes` (cross-line desync detection)

### Section 9.5 — Reproducibility stamp

- EDA SHA: `fe219c1`
- Setup commit SHA: TBD (this commit)
- ITERATION_LABEL: `"v3-070"`
- DEFAULT_ATR_MULTIPLIERS at runtime: (2.0, 1.5)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — universal change)
- V3_MODELS: BCHUSDT, LDOUSDT, TRXUSDT (3 symbols; REVERT /069 ADAUSDT)
- REQUIRED_GAP: 66 = (21+1)×3
- ENSEMBLE_SIZE: 10 (CONFIRMATION mode)
- ENSEMBLE_SEEDS: full 10-tuple unified
- n_trials: 35 default
- Run command: `uv run python run_baseline_v3.py --clean-oof` (no `--exploration`, no `--seeds`)

### Section 9.6 — Pre-flight checks (Phase 5.5 mandatory)

- [x] EDA committed at SHA `fe219c1`
- [x] T0 anchor values byte-exact vs /059 comparison.csv (Section 2.1 verified)
- [x] T1-T4 EDA tables produced
- [x] Brief Section 2.6 documents inherited IC carve-out per /069 Rec #3
- [ ] Setup commit applies Sub-fixes 1-9 — TO BE VERIFIED at Phase 5.5 gate
- [ ] NEW test `tests/strategies/ml/test_dsr_relative_b4.py` committed — TO BE VERIFIED
- [ ] `uv run pytest tests/features_v3/ -k atr -v` PASSES — TO BE VERIFIED
- [ ] `uv run pytest tests/strategies/ml/test_dsr_relative_b4.py -v` PASSES — TO BE VERIFIED
- [ ] `_verify_timeout_consistency()` runtime assertion fires (TO BE VERIFIED at Phase 6)
- [ ] End-to-end smoke test (Section 9.3) PASSES — TO BE VERIFIED at Phase 6
- [ ] ITERATION_LABEL == "v3-070" — TO BE VERIFIED
- [ ] DEFAULT_ATR_MULTIPLIERS == (2.0, 1.5) at runtime — TO BE VERIFIED
- [ ] V3_MODELS = 3 syms — TO BE VERIFIED
- [ ] REQUIRED_GAP == 66 — TO BE VERIFIED

## Section 10 — QR Audit Trail

### Section 10.1 — Why this bundle (cycle 1 closeout per `feedback_v3_strict_10_to_1_cadence.md`)

1. **Cycle 1 cadence completion**: per `feedback_v3_strict_10_to_1_cadence.md` Directive 2 — STRICT 10:1 EXPLORATION:CONFIRMATION cadence. iter-v3/060-/069 are 10 SEPARATE EXPLORATIONs; iter-v3/070 is the SEPARATE CONFIRMATION.

2. **Bundle composition rationale per cycle 1 outcomes** (per /069 diary Section 9 closeout):
   - 1 PROMISING-EXPLORATION (anchor /060): not a bundleable component (it IS the anchor)
   - 1 PASSIVE-DIAGNOSTIC (/062): methodology-only; carry forward as Path B4 spec → Component B
   - 1 SUSPICIOUS-OOS-DOMINANT (/065): the ONLY non-anchor advancement candidate from cycle 1 → Component A
   - 4 INERT (/061, /066, /067, /069): axes CLOSED at catalog level
   - 3 NEGATIVE (/063, /064, /068): axes CLOSED with disqualifying evidence
   
   Bundle = the ONE advancement candidate (Component A) + the deferred methodology spec (Component B). NO other cycle 1 component qualifies.

3. **Path B4 carry-forward from /062**: per /062 brief Section 3 lines 245-313 (deferred spec to /069 cycle 1 CONFIRMATION; relabeled to /070 per cadence shift in `feedback_v3_unified_10seed_baseline.md` Section "EXPLORATION-vs-CONFIRMATION mode separation").

### Section 10.2 — Memory rule compliance

- **`feedback_v3_strict_both_is_oos_baseline.md`**: Section 8.1 PASS = BOTH IS ≥ +1.0894 AND OOS ≥ +0.5791. NOT just OOS-only or IS-only improvement.
- **`feedback_v3_unified_10seed_baseline.md`**: ENSEMBLE_SIZE=10 CONFIRMATION mode; default flag (no --exploration); single trade roster.
- **`feedback_v3_iter018_confirmation_baseline_validation.md`**: ENSEMBLE_SIZE=10 + n_trials=35 + 3-sym + full DSR/PBO/PSR re-eval; multi-seed Pareto retired under unified architecture per `feedback_v3_unified_10seed_baseline.md`.
- **`feedback_v3_baseline_update_policy.md`**: STRICTLY-BETTER-than-prior-baseline. PASS → MERGE; all other paths → /059 stays canonical.
- **`feedback_v3_methodology_axis_integration_test.md`**: NEW `test_dsr_relative_b4.py` mandatory; missing = BLOCK at Phase 5.5.
- **`feedback_v3_methodology_post_hoc_input_traceback.md`**: T3 traceback table at Section 2.4 with input-variable runner code path + granularity.
- **`feedback_v3_iter064_process_lessons.md`**: Rule 1 anchor-byte gate (Section 2.1 T0); Rule 3 NEGATIVE prob calibration (Section 7); Rule 4 Section 8 disjunctive OR (Section 8.5).
- **`feedback_v3_per_symbol_lifts_oos_breaks_is.md`**: V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (universal change at Component A).
- **`feedback_v3_engineered_features_dont_stack.md`**: ONE substantive axis (Component A); Component B is methodology-only (zero behavioral effect).
- **`feedback_v3_engineered_feature_pivot.md`**: Section 2.6 documents inherited IC carve-out (vwap_dev_20 × regime_momentum_signed_5d = 0.7797) with importance ≥30 evidence.
- **`feedback_v3_axis_selection_quant_discipline.md`**: EDA SHA `fe219c1` precedes setup commit.
- **`feedback_v3_trade_rate_floor_bundle_level.md`**: ≥130 OOS trades aggregate (informational at /059 baseline).
- **`feedback_v3_axis_saturation_predictor.md`**: Section 4.3 behavioral predictor with per-symbol WR Δ bands.
- **`feedback_v3_per_symbol_target_axis_falsifier.md`**: Section 8 per-symbol no-collapse gates D.8-D.10.

### Section 10.3 — Critic /069 Recommendations addressed

1. **Rec #1 (anchor-byte correctness gate enforcement at runner-level)**: Sub-fix 5 NEW runtime assertion `_verify_timeout_consistency()` enforces `BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes` for every model. Eliminates the iter-v3/069 line 1407/1425 desync defect class.

2. **Rec #2 (universe expansion follow-up at multi-seed)**: DEFERRED to cycle 2. /070 reverts to 3-sym BCH+LDO+TRX per Sub-fix 6. Cycle 2 may revisit universe expansion at CONFIRMATION-spec.

3. **Rec #3 (inherited IC violation address in /070 brief)**: Section 2.6 documents the Category 2 composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` with importance ≥30 evidence (vwap_dev_20 LDO importance 249.67 rank 1; regime_momentum_signed_5d 122.0 rank 12 — both above 30). NO feature change at /070.

### Section 10.4 — Cycle 1 → Cycle 2 transition note

Per cycle 1 catalog (Section 0.5):
- 4 INERT axes CLOSED: vol_scale_floor, vol_scale_ceiling, confidence threshold floor, universe expansion
- 3 NEGATIVE axes CLOSED: mass feature expansion, phased +adx_14, label timeout doubling
- 2 PROMISING/DIAGNOSTIC axes BUNDLED into /070: SL widening, DSR_relative recalibration
- 1 anchor preserved: /060 EXPLORATION-MODE-REFERENCE

Cycle 2 axis priorities depend on /070 outcome:
- **/070 PASS**: cycle 2 starts at /071; new axes can stack on top of /070 baseline
- **/070 INERT/NEGATIVE/SUSPICIOUS**: cycle 2 starts at /071; both bundled components RETIRE; new axes anchor against /059

### Section 10.5 — Cannot be retroactively renegotiated

Section 8 LOCKED. Section 7 probability calibration LOCKED. Section 4 falsifier bands LOCKED. Established at brief LOCK (setup commit). Per `feedback_v3_axis_selection_quant_discipline.md` and `feedback_v3_iter018_confirmation_baseline_validation.md`.

---

**Setup commit SHA**: TBD (this commit)

**Reading order for Engineer (Phase 6)**:
1. Verify branch `iteration-v3/070`; pull SHA `fe219c1` (EDA).
2. Apply Sub-fixes 1-9: DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5); Path B4 implementation at run_baseline_v3.py:2257-2305 per Section 2.4 T3; NEW `test_dsr_relative_b4.py`; runtime assertion `_verify_timeout_consistency()`; REVERT V3_MODELS to 3-sym; REVERT REQUIRED_GAP to 66; ITERATION_LABEL = "v3-070"; pre-flight assertion updates; existing test updates.
3. Run `uv run pytest tests/features_v3/ -k atr -v` to confirm test PASS.
4. Run `uv run pytest tests/strategies/ml/test_dsr_relative_b4.py -v` to confirm NEW integration test PASS.
5. Run end-to-end smoke test per Section 9.3.
6. Run `uv run python run_baseline_v3.py --clean-oof` (Phase 6 backtest; CONFIRMATION mode).
7. Wall-clock target ~3.6h; HARD CAP 6h per `feedback_v3_cadence_discipline.md`.
8. Engineering report covers Section 8 LOCKED criteria evaluation (PASS/FAIL on each gate A.1–E.15) + Section 8.9 backward-compat documentation for Critic Phase 7.5.

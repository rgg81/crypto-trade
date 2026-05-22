# Iteration v3-050 — Research Brief (SECOND v3 CONFIRMATION — multi-seed validation of cycle 3 best PROMISING bundle)

**Type**: **CONFIRMATION** — **second true v3 CONFIRMATION** ever (after iter-v3/018 BOOTSTRAP at 2026-05-07 and iter-v3/028 first CONFIRMATION-MERGE post-bootstrap at 2026-05-08).
**Track**: v3 (rigor arm) — fiftieth iteration
**Branch**: `iteration-v3/050` (off `iteration-v3/049` head at SHA `3a3d05b`)
**Date**: 2026-05-10
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # SET BY non-exploration mode (NOT --exploration)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=5)  # 5 inner per outer
outer_seeds      = 2              # set by --seeds 2 (per `feedback_v3_outer_seed_cap_2_v3.md`)
n_trials         = 35             # set by default (per `feedback_v3_confirmation_n_trials_35.md`)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0 — full search space
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

**Sacred constants UNCHANGED.** The QR sees multi-seed OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/044/045/047/049 briefs / engineering reports / Critic reviews / diaries / `briefs-v3/exploration_catalog.md` / `BASELINE_V3.md` / iter-v3/018 brief (template predecessor) / iter-v3/028 brief (immediate-prior CONFIRMATION) / `feedback_v3_iter018_confirmation_baseline_validation.md` / `feedback_v3_outer_seed_cap_2_v3.md` / `feedback_v3_confirmation_n_trials_35.md` / `feedback_v3_strict_10_to_1_cadence.md` / `feedback_v3_strict_both_is_oos_baseline.md` / `feedback_v3_baseline_update_policy.md` / `feedback_v3_per_symbol_lifts_oos_breaks_is.md` / `feedback_trade_rate_floor_bundle_level.md` / `feedback_seed_validation.md` / `run_baseline_v3.py` source. **No new IS-only EDA is needed for this CONFIRMATION** because iter-v3/050 multi-seed-validates an EXISTING bundle (cycle 3 best PROMISING ingredients ALREADY integrated at iter-v3/049 head); the prior IS evidence is the iter-v3/044, /045, /047 single-seed runs already committed (reports-v3/iteration_v3-044, /045, /047). This brief acknowledges the structural difference: EXPLORATION briefs generate fresh IS evidence pre-backtest; this CONFIRMATION inherits and re-tests under multi-seed rigor.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: CONFIRMATION (second true v3 CONFIRMATION ever; SECOND post-iter-v3/028 BASELINE_V3.md)
This iteration MAY UPDATE BASELINE_V3.md if BOTH IS Sharpe AND OOS Sharpe (multi-seed mean) beat iter-v3/028 anchor (+0.5101 IS / +0.5053 OOS) per `feedback_v3_strict_both_is_oos_baseline.md`.
Wall-clock budget: 6h HARD CAP (CONFIRMATION cadence rule per `feedback_v3_cadence_discipline.md`)
NOT bundle assembly: all PROMISING components ALREADY integrated at iter-v3/049 head;
  per-symbol ADX (TRX 21) DROPPED per Critic FINAL `1908d50` recommendation #2 (axis CLOSED).
This is a MULTI-SEED VALIDATION RUN of the cycle 3 best PROMISING bundle at full CONFIRMATION rigor.
Pre-committed: spec is FORCED by `feedback_v3_strict_10_to_1_cadence.md` (cycle 3 reached 10/10 EXPLORATIONs at iter-v3/049). Cannot be renegotiated post-hoc.
```

**Justification** (from `feedback_v3_strict_10_to_1_cadence.md`, `feedback_v3_iter018_confirmation_baseline_validation.md`, `briefs-v3/exploration_catalog.md` cycle 3 banner, and Critic FINAL `1908d50` recommendation #2): cycle 3 reached 10/10 EXPLORATIONs at iter-v3/049 with PROMISING-class 3 of 10 (044 ALGO ATR, 045 LDO ATR, 047 primitive 10) and NEGATIVE-class 7 of 10 (040, 041, 042, 043, 046, 048, 049). Three PROMISING components have empirically survived their PATH-A pre-registration: **per-symbol ATR widening for ALGO+LDO** (mechanism: regime-mismatch-driven SL band alignment) and **primitive 10 BCH LONG block** (mechanism: direction-asymmetric kill switch). iter-v3/049 was NEGATIVE-clean PATH C (per-symbol ADX TRX 21 axis CLOSED for cycle 3). **There is NOTHING NEW TO BUNDLE.** iter-v3/050 = MULTI-SEED VALIDATION RUN of the cycle 3 best PROMISING bundle (iter-v3/049 head minus the per-symbol ADX field) at full CONFIRMATION rigor. The spec (`--seeds 2 --n-trials 35`, ENSEMBLE_SIZE=5) is forced by `feedback_v3_outer_seed_cap_2_v3.md` + `feedback_v3_confirmation_n_trials_35.md` and cannot be renegotiated post-hoc.

Per the STRICT 10:1 EXPLORATION:CONFIRMATION cadence rule (`feedback_v3_strict_10_to_1_cadence.md` established 2026-05-08 at iter-v3/028 closeout): iter-v3/050 is a SEPARATE CONFIRMATION (not collapsing the 10th EXPLORATION into the CONFIRMATION). iter-v3/039 was the first CONFIRMATION under this strict rule (NO MERGE per `feedback_v3_strict_both_is_oos_baseline.md` IS regression); iter-v3/050 is the second.

---

## Section 1 — Hypothesis

The cycle 3 best PROMISING bundle (V3_FEATURE_COLUMNS_TOP_N=14 with regime_momentum_signed_5d, V3_ATR_MULTIPLIERS_PER_SYMBOL={ALGO: (2.0, 1.5), LDO: (2.0, 1.5)}, RiskV2Config.block_long_for=("BCHUSDT",), V3_MODELS=4 BCH+LDO+TRX+ALGO) PRESERVES IS lift AND OOS lift at multi-seed (5 inner × 2 outer = 10 models per cell, n_trials=35), AND beats the iter-v3/028 BASELINE_V3.md anchor on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean), satisfying the BASELINE_V3.md update gate per `feedback_v3_strict_both_is_oos_baseline.md`.

---

## Section 2 — Inherited IS Evidence (no fresh EDA — structural difference from EXPLORATION briefs)

### 2.1 Why no new IS-only analysis script

CONFIRMATION's question is **statistical-validity-of-prior**, not signal-discovery. Per `feedback_qr_uses_is_data.md`, every Phase 5 brief must contain numerical tables produced by a committed analysis script — for CONFIRMATION the "analysis" IS the iter-v3/044, /045, /047 baseline runs already committed (reports-v3/iteration_v3-044, /045, /047). iter-v3/050's "fresh IS evidence" is the multi-seed re-run itself, generated in Phase 6, not pre-Phase 5. Generating new IS-only analysis pre-backtest would:
- Risk peeking at OOS aggregates from iter-v3/044/045/047/049 (already revealed) and using them to calibrate gates that are pre-registered in this brief
- Add no information beyond the existing reports already in `reports-v3/iteration_v3-{044,045,047,049}/` (committed, reproducible)

**This brief inherits the cycle 3 PROMISING evidence as the prior** and pre-registers MERGE/NO-MERGE gates that the multi-seed run must mechanically clear.

### 2.2 Cycle 3 PROMISING bundle lineage (the prior being validated)

**Source**: `briefs-v3/exploration_catalog.md` cycle 3 + Critic FINAL `1908d50` recommendation #2 + 3 single-seed comparison.csv files.

| Iter | Date | Axis | Single-seed IS Sharpe | Single-seed OOS Sharpe | Δ vs prior | Classification | Carry-forward to /050? |
|---|---|---|---:|---:|---:|---|---|
| iter-v3/044 | 2026-05-09 | NEW: per-symbol ATR ALGO (2.0, 1.5) | TBD | TBD | +PROMISING | PROMISING-clean | **YES** (V3_ATR_MULTIPLIERS_PER_SYMBOL ALGO) |
| iter-v3/045 | 2026-05-09 | NEW: per-symbol ATR LDO (2.0, 1.5) | **+0.7459** | **+3.5259** | +PROMISING (strongest) | PROMISING-clean | **YES** (V3_ATR_MULTIPLIERS_PER_SYMBOL LDO) |
| iter-v3/046 | 2026-05-09 | NEW: per-symbol ATR BCH (2.0, 1.5) | -0.54 | -45 PnL | NEGATIVE-clean | NEGATIVE-clean (REVERTED at iter-v3/047 setup) | NO (REVERTED) |
| iter-v3/047 | 2026-05-09 | NEW: primitive 10 BCH LONG block | +0.4872 | +1.1675 | -0.26 IS / -2.36 OOS vs /045 anchor | PROMISING (IS-only validated; OOS noisy single-seed) | **YES** (RiskV2Config.block_long_for=("BCHUSDT",)) |
| iter-v3/048 | 2026-05-09 | NEW: vol_normalized_ret_5d feature | -0.43 | -3.15 | NEGATIVE-clean | NEGATIVE-clean (REVERTED at iter-v3/049 setup) | NO (REVERTED) |
| iter-v3/049 | 2026-05-10 | NEW: per-symbol ADX threshold TRX 21 | -0.32 | -2.50 | NEGATIVE-clean | NEGATIVE-clean (axis CLOSED) | **NO** (per Critic FINAL `1908d50` rec #2) |

**Inherited iter-v3/045 single-seed metrics** (the strongest cycle 3 PROMISING anchor; from `reports-v3/iteration_v3-045/comparison.csv`):

| Metric | iter-v3/045 IS (1-seed) | iter-v3/045 OOS (1-seed) | OOS/IS ratio |
|---|---:|---:|---:|
| **monthly_sharpe** | **+0.7459** | **+3.5259** | 4.7268 |
| daily_sharpe | +1.3115 | +4.2020 | 3.2041 |
| max_drawdown (%) | 66.0621 | 13.2635 | 0.2008 |
| profit_factor | 1.2096 | 1.6760 | 1.3856 |
| win_rate (%) | 34.0000 | 50.4202 | 1.4829 |
| n_trades | 250 | **119** | 0.4760 |
| total_pnl | 75.3958 | 96.9939 | 1.2865 |
| weighted_pnl_total | 75.3958 | 96.9939 | 1.2865 |
| **DSR** | **0.0000** | — | single-seed saturation |
| **PBO** | **0.0782** | — | (cross-cell mean aggregator) |
| **PSR** | **1.0000** | — | single-seed saturation |
| n_trials | 140 | — | (4 symbols × 35 trials/seed × 1 seed = 140) |
| n_effective_trials | 19 | — | (PCA on trial-returns matrix) |

**Inherited iter-v3/047 single-seed metrics** (the primitive 10 carry-forward anchor; from `reports-v3/iteration_v3-047/comparison.csv`):

| Metric | iter-v3/047 IS (1-seed) | iter-v3/047 OOS (1-seed) | Δ vs /045 |
|---|---:|---:|---|
| monthly_sharpe | +0.4872 | +1.1675 | -0.26 IS / -2.36 OOS (single-seed Optuna lottery) |
| n_trades | 201 | 92 | -49 IS / -27 OOS (primitive 10 dropped BCH LONG) |
| weighted_pnl_total | 54.8993 | 46.4331 | -20.50 IS / -50.56 OOS |

iter-v3/047's single-seed OOS regression vs iter-v3/045 is **single-seed Optuna lottery noise** (forensically established at iter-v3/048 via the multi-run-stochasticity correction). The IS-only validation basis for primitive 10 (BCH IS net_pnl +18.68 PnL lift; 0 BCH LONG leakage) holds; OOS validation deferred to multi-seed (this iteration). Per Section 14 of iter-v3/049 brief: "Primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 multi-seed run is the first OOS test of primitive 10 in clean conditions."

**Inherited iter-v3/049 single-seed metrics** (the most recent EXPLORATION; from `reports-v3/iteration_v3-049/comparison.csv` for cross-check on the iter-v3/049-head bundle WITHOUT the per-symbol ADX field):

| Metric | iter-v3/049 IS (1-seed; with ADX TRX 21) | iter-v3/049 OOS (1-seed) | Note |
|---|---:|---:|---|
| monthly_sharpe | +0.4261 | +1.0272 | The ADX TRX 21 field DROPPED at iter-v3/050 setup |
| n_trades | 194 | 92 | Bundle state matches /050 minus ADX field |
| weighted_pnl_total | 46.7626 | 34.9069 | LDO at -19.13 OOS (frozen baseline single-seed lottery flag) |

iter-v3/049's single-seed bundle (minus the per-symbol ADX field) is the closest available approximation of the iter-v3/050 starting state at single-seed. The expected multi-seed iter-v3/050 result is ANCHORED to the iter-v3/045 single-seed strongest PROMISING (+0.7459 IS / +3.5259 OOS) MODULO multi-seed compression (precedent: iter-v3/018 BOOTSTRAP saw ~50% compression from single-seed to multi-seed; iter-v3/039 saw ~49% compression).

### 2.3 Per-symbol iter-v3/045 OOS attribution (the strongest single-seed anchor)

**Source**: `reports-v3/iteration_v3-045/comparison.csv` per_symbol section.

| Symbol | weighted_pnl | n_trades | win_rate (%) | concentration_pct |
|---|---:|---:|---:|---:|
| ALGOUSDT | +53.1203 | 22 | 63.6 | **54.77** |
| BCHUSDT | +11.3076 | 38 | 39.5 | 11.66 |
| LDOUSDT | +9.3354 | 13 | 53.8 | 9.62 |
| TRXUSDT | +23.2307 | 46 | 52.2 | 23.95 |

ALGO 54.77% concentration is **above** the 30% per-symbol cap that applies at CONFIRMATION. The iter-v3/045 catalog row pre-committed: "future CONFIRMATION QR must scope ex-ALGO basket fragility before bundling." Section 4.2 below predicts how multi-seed averaging may compress ALGO concentration; Section 8 specifies the mechanical gate.

iter-v3/047 single-seed (with primitive 10 added) showed ALGO concentration **59.06%** + TRX **64.43%** (different lottery seed) — the lottery-flag pattern persisting across compositional variations. iter-v3/049 single-seed (with ADX TRX 21 and primitive 10) showed ALGO **59.06%** + TRX **64.43%** + LDO **-41.21%** (LDO net negative; frozen baseline carry-over from iter-v3/045 single-seed=42 lottery). This is ADDITIONAL pre-commitment evidence that concentration is a single-seed lottery flag persisting across THREE PROMISING-bundle iterations, NOT just iter-v3/045.

Per `feedback_v3_concentration_is_signal.md` (established at iter-v3/020 closeout): "Concentration in 3-symbol BCH+LDO+TRX universe is lottery-REWARD source NOT lottery-RISK source." This rule extends to the 4-symbol BCH+LDO+TRX+ALGO universe by analogy. Per-symbol caps are CLOSED-mechanism. The CONFIRMATION-MERGE concentration gate (≤30%) applies as published in BASELINE_V3.md aspirational gates, but failure to clear does NOT block the BASELINE_V3.md update gate per `feedback_v3_baseline_update_policy.md` 2026-05-08 directive.

### 2.4 Inherited per-cell PBO + n_eff diagnostics (from iter-v3/049 single-seed)

| Stat | iter-v3/049 single-seed |
|---|---:|
| Cross-cell PBO (mean aggregator) | 0.0939 |
| `pbo_frac_positive_paths` (unknown count) | TBD (from per_cell_pbo.csv) |
| n_eff (median across cells) | 18 |
| n_trials (single-seed; ENSEMBLE_SIZE=5) | 700 = 4 syms × 5 inner × 35 |

The cross-cell mean PBO of 0.0939 is **well below** the 0.4 CONFIRMATION threshold. iter-v3/050 at multi-seed (n_trials=1400 = 4 syms × 5 inner × 35 × 2 outer) is expected to have PBO in similar range [0.05, 0.20] based on iter-v3/028's multi-seed PBO of 0.1243.

### 2.5 Setup integrity (verified pre-brief at SHA TBD)

```
reports-v3/iteration_v3-045/comparison.csv extant + non-empty   PASS (verified)
reports-v3/iteration_v3-047/comparison.csv extant + non-empty   PASS (verified)
reports-v3/iteration_v3-049/comparison.csv extant + non-empty   PASS (verified)
ITERATION_LABEL currently "v3-049" (will be updated to "v3-050") AS_DOCUMENTED
V3_MODELS at runtime = 4 entries (BCH, LDO, TRX, ALGO)            PASS (verified)
ENSEMBLE_SIZE constant = 5 in run_baseline_v3.py                  PASS (verified at runner line 90)
_derive_ensemble_seeds(outer_seed, size=5) returns 5 distinct ints PASS (verified at runner line 94)
non-exploration code path uses ENSEMBLE_SIZE not 1                PASS
non-exploration code path uses fast_mode=False (Optuna tunes colsample) PASS
default --n-trials = 35 (per `feedback_v3_confirmation_n_trials_35.md`) PASS
--seeds 2 invocation produces outer_seeds=2                       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} PASS
RiskV2Config.block_long_for = ("BCHUSDT",), block_short_for = () PASS
RiskV2Config.adx_threshold_per_symbol = {} (DROP per Critic FINAL `1908d50` rec #2) PENDING (sub-fix)
V3_FEATURE_COLUMNS_TOP_N length = 14 (regime_momentum_signed_5d PRESENT, vol_normalized_ret_5d ABSENT) PASS
```

**Minimal code changes needed** to support iter-v3/050's CONFIRMATION-mode invocation. The runner's non-exploration code path already supports the spec out-of-the-box. The required edits are §3 sub-fixes (cosmetic ITERATION_LABEL bump + DROP per-symbol ADX field).

---

## Section 3 — Proposed Changes

**Bundle is LOCKED per Critic FINAL `1908d50` recommendation #2.** All ingredients listed below are inherited from iter-v3/049 head EXCEPT the per-symbol ADX field which is DROPPED per the Critic recommendation.

### 3.1 Symbols — UNCHANGED (4-symbol BCH+LDO+TRX+ALGO inherited from iter-v3/044+)

| Symbol | iter-v3/049 status | iter-v3/050 status |
|---|---|---|
| BCHUSDT | KEEP | **KEEP** |
| LDOUSDT | KEEP | **KEEP** |
| TRXUSDT | KEEP | **KEEP** |
| ALGOUSDT | KEEP | **KEEP** |

### 3.2 Labeling — UNCHANGED (default ATR (2.0, 1.0) + per-symbol overrides ALGO/LDO inherited)

| Parameter | iter-v3/049 | iter-v3/050 |
|---|---:|---:|
| `DEFAULT_ATR_MULTIPLIERS` (BCH, TRX) | (2.0, 1.0) | **(2.0, 1.0) (UNCHANGED)** |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"]` | (2.0, 1.5) | **(2.0, 1.5) (UNCHANGED)** |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"]` | (2.0, 1.5) | **(2.0, 1.5) (UNCHANGED)** |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"]` | NOT PRESENT | NOT PRESENT (UNCHANGED) |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL["TRXUSDT"]` | NOT PRESENT | NOT PRESENT (UNCHANGED) |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap (REQUIRED_GAP) | 88 = (21+1)×4 | **88 (UNCHANGED)** |

### 3.3 Features — UNCHANGED (14 features inherited from iter-v3/049 head)

`V3_FEATURE_COLUMNS_TOP_N` length = 14. `regime_momentum_signed_5d` PRESENT. `vol_normalized_ret_5d` ABSENT (DROPPED at iter-v3/049 setup per iter-v3/048 PATH C-clean closeout). `efficiency_ratio_50` ABSENT. `regime_momentum_signed_3d` ABSENT. The list is identical to iter-v3/049 baseline (after iter-v3/048's vol_normalized_ret_5d reverted).

### 3.4 Risk gates — CHANGED minimally (DROP per-symbol ADX field; all else unchanged)

| Parameter | iter-v3/049 | iter-v3/050 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED)** |
| `RiskV2Config.adx_threshold` (global) | 20.0 | **20.0 (UNCHANGED)** |
| **`RiskV2Config.adx_threshold_per_symbol`** | **{"TRXUSDT": 21.0}** | **{} (EMPTY — DROPPED per Critic FINAL `1908d50` rec #2)** |
| `RiskV2Config.block_long_for` | ("BCHUSDT",) | **("BCHUSDT",) (UNCHANGED — primitive 10 carry-forward)** |
| `RiskV2Config.block_short_for` | () | **() (UNCHANGED)** |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | **15.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Multi-seed config — CHANGED (the actual axis of this CONFIRMATION)

| Parameter | iter-v3/049 | iter-v3/050 |
|---|---:|---:|
| Outer seeds | 1 (EXPLORATION) | **2** (per `feedback_v3_outer_seed_cap_2_v3.md`) |
| `ENSEMBLE_SIZE` (inner ensemble) | 5 (default) | **5** (UNCHANGED — non-exploration mode) |
| Models per cell | 1 × 5 = 5 | **2 × 5 = 10** |
| n_trials per cell (Optuna) | 35 | **35** (UNCHANGED — per `feedback_v3_confirmation_n_trials_35.md`) |
| Total trials | 700 = 4 × 5 × 35 × 1 | **1400 = 4 × 5 × 35 × 2** |
| `colsample_bytree` Optuna sampling | Optuna-tuned | **Optuna-tuned (UNCHANGED)** |
| `--exploration` flag | NO | **NO (UNCHANGED — non-exploration mode)** |
| `--clean-oof` flag | YES | **YES (carry-forward — `feedback` SHA `6a216b5` guardrail)** |
| ITERATION_LABEL | "v3-049" | **"v3-050"** |

The multi-seed config (--seeds 1 → 2; total trials 700 → 1400) is the **only axis** varied in iter-v3/050 BESIDES the per-symbol ADX field DROP and the cosmetic ITERATION_LABEL bump. All other parameters (symbols, labeling, features, gates, risk primitives, walk-forward window, OOS cutoff) are byte-identical to iter-v3/049 baseline minus the per-symbol ADX field.

### 3.6 Sub-fix decomposition — minimal (cosmetic edits + DROP one field + run command)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | Update `ITERATION_LABEL` to `"v3-050"` in `run_baseline_v3.py` line 106 | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-050"' run_baseline_v3.py` exits 0 |
| 2 | DROP `adx_threshold_per_symbol={"TRXUSDT": 21.0}` from `RiskV2Config()` constructor in `_build_v3_model` (replace with `adx_threshold_per_symbol={}` or omit the kwarg entirely) | Configuration change | `grep -E 'adx_threshold_per_symbol=\{"TRXUSDT": 21\.0\}' run_baseline_v3.py` exits 1 (NOT present) |
| 3 | Update `_verify_feature_columns` assertion at lines ~252+ to expect `adx_threshold_per_symbol == {}` (NOT `{"TRXUSDT": 21.0}`) | Assertion update | runner doesn't BLOCK at startup; verifier runs to completion |
| 4 | Verify `V3_MODELS` is unchanged (4 entries, BCH/LDO/TRX/ALGO) | grep | `python -c "from importlib import import_module; m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 4 and {s for _, s in m.V3_MODELS} == {'BCHUSDT', 'LDOUSDT', 'TRXUSDT', 'ALGOUSDT'}"` exits 0 |
| 5 | Verify `REQUIRED_GAP == 88` unchanged | grep | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 88"` exits 0 |
| 6 | Verify `ENSEMBLE_SIZE == 5` constant in non-exploration mode | grep | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert m.ENSEMBLE_SIZE == 5"` exits 0 |
| 7 | Verify `_derive_ensemble_seeds(seed, 5)` returns 5 ints when called with size=5 | unit | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert len(m._derive_ensemble_seeds(42, 5)) == 5"` exits 0 |
| 8 | Verify default `--n-trials == 35` (no --exploration) | grep | `grep -E 'default=35' run_baseline_v3.py` exits 0 |
| 9 | Verify `V3_FEATURE_COLUMNS_TOP_N` length 14 | grep | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert len(V3_FEATURE_COLUMNS_TOP_N) == 14"` exits 0 |
| 10 | Verify `regime_momentum_signed_5d` IS in V3_FEATURE_COLUMNS_TOP_N | grep | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS_TOP_N"` exits 0 |
| 11 | Verify `vol_normalized_ret_5d` is NOT in V3_FEATURE_COLUMNS_TOP_N | grep | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert 'vol_normalized_ret_5d' not in V3_FEATURE_COLUMNS_TOP_N"` exits 0 |
| 12 | Verify `V3_ATR_MULTIPLIERS_PER_SYMBOL == {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}` (2 entries) | grep | `python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {'ALGOUSDT': (2.0, 1.5), 'LDOUSDT': (2.0, 1.5)}"` exits 0 |
| 13 | Verify `block_long_for=("BCHUSDT",)` in runner's RiskV2Config setup | grep | `grep -E 'block_long_for=\("BCHUSDT",\)' run_baseline_v3.py` exits 0 |
| 14 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 (88+/88+ tests) |
| 15 | Commit cosmetic ITERATION_LABEL + adx field DROP | git | `feat(iter-v3/050): ITERATION_LABEL=v3-050 + DROP per-symbol ADX field (multi-seed validation of cycle 3 best PROMISING bundle)` |
| 16 | Run **without** `--exploration`, **with** `--seeds 2`: `uv run python run_baseline_v3.py --seeds 2 --clean-oof` | runner | `test -f reports-v3/iteration_v3-050/comparison.csv` |

NO new feature additions. NO labeling change. NO new risk-gate added (only the per-symbol ADX field DROPPED — reverting to iter-v3/048-equivalent risk-gate state plus primitive 10). NO new src/ code. The required code edits are: cosmetic ITERATION_LABEL bump (sub-fix #1), DROP one kwarg from RiskV2Config (sub-fix #2), update one assertion (sub-fix #3). Sub-fixes #4-13 are pre-flight verifiers, not edits.

### 3.7 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Item | Code path | Verifier |
|---|---|---|---|
| 1 | `V3_FEATURE_COLUMNS_TOP_N` length 14 unchanged | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert len(V3_FEATURE_COLUMNS_TOP_N) == 14"` exits 0 |
| 2 | `regime_momentum_signed_5d` IS in V3_FEATURE_COLUMNS_TOP_N | features module | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS_TOP_N"` exits 0 |
| 3 | `vol_normalized_ret_5d` NOT in V3_FEATURE_COLUMNS_TOP_N | features module | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert 'vol_normalized_ret_5d' not in V3_FEATURE_COLUMNS_TOP_N"` exits 0 |
| 4 | `V3_ATR_MULTIPLIERS_PER_SYMBOL` has exactly 2 entries (ALGO, LDO) | features module | `python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {'ALGOUSDT': (2.0, 1.5), 'LDOUSDT': (2.0, 1.5)}"` exits 0 |
| 5 | `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` UNCHANGED | features module | `python -c "from crypto_trade.features_v3 import DEFAULT_ATR_MULTIPLIERS; assert DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)"` exits 0 |
| 6 | `BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED | `run_baseline_v3.py` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 7 | `V3_MODELS` has exactly 4 entries; MKR not present | `run_baseline_v3.py` lines 108-117 | `python -c "from importlib import import_module; m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 4 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}"` exits 0 |
| 8 | `REQUIRED_GAP == 88` | `validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 88"` exits 0 |
| 9 | `ITERATION_LABEL == "v3-050"` | `run_baseline_v3.py` line 106 | `grep -E 'ITERATION_LABEL.*=.*"v3-050"' run_baseline_v3.py` exits 0 |
| 10 | `ENSEMBLE_SIZE == 5` constant in runner | `run_baseline_v3.py` line 90 | `python -c "import importlib, sys; sys.path.insert(0, '.'); m = importlib.import_module('run_baseline_v3'); assert m.ENSEMBLE_SIZE == 5"` exits 0 |
| 11 | Non-exploration code path: `ensemble_size_for_run = ENSEMBLE_SIZE`, `fast_mode_for_run = False`, n_trials NOT auto-overridden | `run_baseline_v3.py` (around line 1371-1375) | `grep -E 'ensemble_size_for_run.*=.*1 if args\.exploration else ENSEMBLE_SIZE' run_baseline_v3.py` exits 0 AND `grep -E 'fast_mode_for_run.*=.*bool\(args\.exploration\)' run_baseline_v3.py` exits 0 |
| 12 | `--seeds 2 --n-trials 35` invocation (default n_trials=35; --seeds 2 explicit) produces 2 outer seeds × 5 inner = 10 models per cell | runner | grep `Seeds: 2` and `Optuna trials/model: 35` in `run.log` |
| 13 | `--exploration` flag NOT set in invocation | runner invocation | grep on `run.log` for absence of "exploration" in the activation banner |
| 14 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 15 | Wall-clock < 6h hard cap | engineering report | wall-clock minutes < 360 (target 120-240) |
| 16 | `comparison.csv` produced with multi-seed metrics aggregated | runner | `test -f reports-v3/iteration_v3-050/comparison.csv` AND DSR/PSR/PBO are NOT single-seed-saturation values (PBO well-defined; PSR may saturate at 1.0 with multi-seed n_trials=1400) |
| 17 | `pareto_front.csv` shows 2 distinct rows (one per outer seed); BOTH seeds Sharpes > 0 (per `feedback_v3_outer_seed_cap_2_v3.md` 2-seed Pareto rule) | reports | `python -c "import pandas as pd; df = pd.read_csv('reports-v3/iteration_v3-050/pareto_front.csv'); assert len(df) >= 2"` exits 0; multi-seed mean Sharpe > 0 verified separately |
| 18 | Top-symbol concentration (multi-seed mean) ≤ 30% (or explicit exception in §8) | reports | parsing per_symbol section of `comparison.csv` |
| 19 | Bundle-level OOS trade count ≥ 130 | reports | `python -c "import pandas as pd; df = pd.read_csv('reports-v3/iteration_v3-050/comparison.csv'); n = df.loc[df['metric']=='n_trades','out_of_sample'].iloc[0]; assert int(n) >= 130, f'OOS trades < 130 floor: {n}'"` exits 0 |
| 20 | `RiskV2Config.adx_threshold_per_symbol == {}` (DROPPED per Critic FINAL `1908d50` rec #2) | `run_baseline_v3.py` _build_v3_model | grep absence of `adx_threshold_per_symbol={"TRXUSDT": 21.0}` AND positive grep for empty/absent kwarg pattern |
| 21 | `RiskV2Config.block_long_for == ("BCHUSDT",)` UNCHANGED carry-forward | `run_baseline_v3.py` _build_v3_model | `grep -E 'block_long_for=\("BCHUSDT",\)' run_baseline_v3.py` exits 0 |
| 22 | `RiskV2Config.block_short_for == ()` UNCHANGED | `run_baseline_v3.py` _build_v3_model | `grep -E 'block_short_for=\(\)' run_baseline_v3.py` exits 0 |

### 3.8 Inheritance from iter-v3/049

The `iteration-v3/050` branch was branched from `iteration-v3/049` head at SHA `3a3d05b`. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset` (initial top-N pruning)
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)` (default ATR established)
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15`
- `e3168f2 feat(iter-v3/013): drop MKR (4-symbol → 3-symbol BCH+LDO+TRX) + REQUIRED_GAP 88→66` (LATER reverted to 4-sym at iter-v3/030+)
- `b0576df feat(iter-v3/028): regime_momentum_signed_5d ADDED to V3_FEATURE_COLUMNS_TOP_N` (FIRST CONFIRMATION-MERGE; BASELINE_V3.md update)
- iter-v3/030+ commits: 4-symbol restoration + ALGO addition (V3_MODELS = (BCH, LDO, TRX, ALGO); REQUIRED_GAP back to 88)
- `b9f4a9c feat(iter-v3/044): V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5)` (ALGO ATR PROMISING ingredient)
- `aa4a7c4 feat(iter-v3/045): V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5)` (LDO ATR strongest PROMISING ingredient)
- `9b1293d feat(iter-v3/047): primitive 10 (direction-asymmetric kill switch) + BCH LONG block` (primitive 10 PROMISING ingredient)
- `6eeff46 feat(iter-v3/049): per-symbol ADX threshold (TRX 21) + vol_normalized_ret_5d REVERT` (this iteration DROPS the ADX field, KEEPS the vol_normalized_ret_5d revert)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N; assert len(V3_FEATURE_COLUMNS_TOP_N) == 14 and 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS_TOP_N and 'vol_normalized_ret_5d' not in V3_FEATURE_COLUMNS_TOP_N"` exits 0
- `python -c "from crypto_trade.features_v3 import V3_ATR_MULTIPLIERS_PER_SYMBOL; assert V3_ATR_MULTIPLIERS_PER_SYMBOL == {'ALGOUSDT': (2.0, 1.5), 'LDOUSDT': (2.0, 1.5)}"` exits 0
- `grep -E 'block_long_for=\("BCHUSDT",\)' run_baseline_v3.py` exits 0
- `grep -E 'block_short_for=\(\)' run_baseline_v3.py` exits 0
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0
- `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 88"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0

### 3.9 Wall-clock estimate

**Two calibration points** for predicting iter-v3/050 wall-clock:

**Calibration A — direct comparison to iter-v3/028 (REALISTIC bound)**:
- iter-v3/028: 3.18h @ (--seeds 2, ENSEMBLE_SIZE=5, n_trials=35, 3 symbols)
- iter-v3/050 cost ratio vs iter-v3/028: (4/3) symbols = 1.33×
- Predicted: 3.18h × 1.33 = **4.23h** — **comfortably within 6h cap**

**Calibration B — linear scaling from iter-v3/049 (UPPER bound)**:
- iter-v3/049: ~35 min @ (--seeds 1, ENSEMBLE_SIZE=5, n_trials=35, 4 symbols)
- iter-v3/050 multiplier: 2 (seeds: 1→2) = **2×**
- Predicted: 35 min × 2 = **70 min ≈ 1.17h** — **comfortably within 6h cap**

**Why the divergence**: Calibration B from iter-v3/049 underestimates because Optuna's TPE warmup cost is paid once per outer seed, not amortized across symbols. Calibration A from iter-v3/028 includes the same overhead structure but at 3 symbols vs 4. Calibration A is the more reliable estimate at production scale.

**The QR's chosen estimate**: **2-4.5h, comfortably within 6h cap**, leaning toward Calibration A but allowing for ~30% upside variance from real-system noise (Optuna trial-time variance, parquet I/O cache state, NEW symbol per cell adding ~25-33% per-cell cost). **Recommendation: proceed at full spec (--seeds 2 --n-trials 35 --clean-oof). Engineer kills Phase 6 if elapsed > 6h.**

**Contingency planning** (if Calibration A turns out closer to 4.5h+):

| Reduction strategy | New spec | Estimated wall-clock | Methodology cost |
|---|---|---:|---|
| (none — full spec) | --seeds 2 --n-trials 35 | 2-5h | full CONFIRMATION rigor |
| Reduce n_trials 35 → 25 | --seeds 2 --n-trials 25 | 1.5-3.5h | lower Optuna search rigor; n_eff likely drops 18→14; **least bad** if needed |
| Reduce outer seeds 2 → 1 | --seeds 1 --n-trials 35 | 1-2.5h | NOT recommended — defeats multi-seed validation, the entire point of CONFIRMATION |
| Accept >6h cap exceedance | (any) | >360 min | NOT allowed per cadence rule |

**The QR's specific recommendation**: do NOT pre-commit to any reduction. Run at full --seeds 2 --n-trials 35. If the Engineer hits 4.5h elapsed and projection extrapolates beyond 6h, the Engineer kills Phase 6 and iter-v3/050 is re-run at --n-trials 25 in a subsequent iteration. The kill-switch decision rule is: at t=270 min (4.5h), if `< 65% of cells have completed Optuna fitting`, kill and re-launch with reduced n_trials.

---

## Section 4 — Expected OOS Impact

### 4.1 CONFIRMATION → headline metrics ARE BLOCK-triggering gates (modified by `feedback_v3_baseline_update_policy.md`)

Per Section 0.5 + `feedback_v3_iter018_confirmation_baseline_validation.md`, iter-v3/050 is a CONFIRMATION iteration with **mechanical merge gates** (Section 8). Critic emits `CONFIRMATION-MERGE-FULL`, `CONFIRMATION-MERGE-BOOTSTRAP-style` (i.e. STRICTLY-BETTER on BOTH IS+OOS but some aspirational gates fail), `CONFIRMATION-NO-MERGE-revert`, or `BLOCK`.

Per `feedback_v3_baseline_update_policy.md` (2026-05-08 directive, established at iter-v3/028 closeout) AND `feedback_v3_strict_both_is_oos_baseline.md` (2026-05-09 directive, established at iter-v3/039 closeout): **BASELINE_V3.md update gate = BOTH IS Sharpe AND OOS Sharpe (multi-seed mean) MUST beat iter-v3/028 anchor (+0.5101 IS / +0.5053 OOS).** Aspirational MERGE gates (Sharpe ≥ +1.0 floors, DSR > 0.95, top-symbol ≤ 30%, OOS trades ≥ 130, etc.) inform future-iteration priorities but do NOT block baseline updates. Hard-blocking gates retained: Gate 3 (OOS/IS ≥ 0.5), Gate 6 (PSR > 0.95), Gate 10 (Pareto dominance positive both seeds).

### 4.2 Predicted multi-seed Sharpe bands

Anchor: iter-v3/045 single-seed (+0.7459 IS / +3.5259 OOS) — the strongest cycle 3 PROMISING.
Compression precedent (single-seed → multi-seed):
- iter-v3/013 → iter-v3/018: +1.0088 IS / +2.6970 OOS → +0.3788 IS / +0.3869 OOS (62% IS compression / 86% OOS compression)
- iter-v3/025 single-seed → iter-v3/028 multi-seed: +0.8788 IS / +1.2244 OOS → +0.5101 IS / +0.5053 OOS (42% IS compression / 59% OOS compression)
- Mid-point compression rate: ~50% IS / ~70% OOS

| Metric | iter-v3/045 (1-seed) | iter-v3/050 prediction (multi-seed mean) | Falsifier |
|---|---:|---:|---|
| **IS monthly Sharpe** | +0.7459 | **predicted [+0.40, +0.65] with median +0.52** | **OOS<+0.51 OR IS<+0.51 → NO BASELINE UPDATE per `feedback_v3_strict_both_is_oos_baseline.md`** |
| **OOS monthly Sharpe** | +3.5259 | **predicted [+0.55, +1.50] with median +1.00** | **OOS<+0.51 → NO BASELINE UPDATE; OOS<+1.0 → aspirational gate fail (informational)** |
| OOS/IS Sharpe ratio | 4.7268 | predicted [1.2, 2.5] with median 1.8 | < 0.5 → HARD BLOCK on overfitting evidence |
| IS trade count | 250 | predicted [180, 250] (modest variance from outer-seed Optuna re-routing + primitive 10 BCH LONG removal) | sub-100 or super-300 unexpected |
| **OOS trade count (BUNDLE)** | 119 | **predicted [80, 160]** (multi-seed averaging; primitive 10 may suppress OOS BCH LONG further) | **OOS<130 → aspirational gate fail (informational; per `feedback_trade_rate_floor_bundle_level.md` v3 rule)** |
| **DSR** | 0.0000 (single-seed saturation) | **predicted [0.00, 0.05]** (structural per iter-v3/028 root cause: at n_trials=1400, López de Prado E[max_SR] ≈ 3.5; observed annualized ≈ 1.5-2.0) | DSR<0.95 → aspirational gate fail (structural; informational) |
| **PBO** (cross-cell mean) | 0.0782 | **predicted [0.05, 0.20]** (multi-seed averaging reduces per-cell PBO variance) | PBO≥0.4 → HARD BLOCK |
| **PSR** | 1.0000 (single-seed saturation) | **predicted [0.95, 1.00]** | PSR<0.95 → HARD BLOCK |
| **ALGO concentration** | 54.77% | **predicted [25%, 60%]** (multi-seed averaging may compress lottery flag) | concentration > 30% → aspirational gate fail (informational; concentration is signal per `feedback_v3_concentration_is_signal.md`) |
| **TRX concentration** | 23.95% | **predicted [15%, 50%]** | (same as above) |
| **LDO concentration** | 9.62% (positive at /045; -41.21% negative at /049 single-seed) | **predicted [-20%, +20%]** (multi-seed averaging tests LDO single-seed lottery) | concentration > 30% → aspirational gate fail; LDO net-negative is the dominant fragility flag |
| n_eff | 19 | predicted [15, 25] | n_eff < 10 → CRITIC INFORMATIONAL CONCERN |
| Wall-clock | 35 min (1-seed) | predicted 120-270 min | > 360 min (6h) → BLOCK |

The prediction bands are deliberately broad to absorb:
- Multi-seed averaging may either compress IS Sharpe (variance reduction toward true mean) or expand it (if the single-seed +0.7459 was noise within an underlying +0.85 distribution)
- Per-symbol concentration is single-seed lottery flag; multi-seed averaging tests whether the pattern persists across different Optuna trajectories (precedent: iter-v3/028 LDO concentration -134% single-seed projection but multi-seed mean ~75-77% — directionally inverted)
- PSR formulation requires n_eff ≥ 2; with n_trials=1400 (4 sym × 35 trials × 5 inner × 2 outer) and n_eff predicted ≥ 15, PSR formulation is well-defined

**Median IS prediction +0.52 sits at the iter-v3/028 anchor +0.5101** because the multi-seed mean of 2 outer seeds is unbiased given identical underlying signal — only variance changes. The expected lift over iter-v3/028 comes from the cycle 3 PROMISING ingredients (primitive 10 + per-symbol ATR ALGO + per-symbol ATR LDO) that did NOT exist at iter-v3/028. Lower bound +0.40 allows for unfavorable outer-seed variance + per-symbol architecture risk (the iter-v3/039 anti-pattern: per-symbol customizations lifted OOS but BROKE IS aggregate at multi-seed, ratio compression ~50%); upper bound +0.65 allows for favorable.

### 4.3 Single-seed → multi-seed compression precedent

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (2026-05-09 from iter-v3/039 closeout): "Per-symbol features (BCH fracdiff) and per-symbol labels (LDO ATR) lift OOS Sharpe materially (+0.96 at iter-v3/039 multi-seed vs baseline) but break IS aggregate (IS Sharpe collapsed -0.59). The 'suspicious-OOS-divergence' pattern observed at iter-v3/026/027/030/034/036/037 single-seed PERSISTED at multi-seed."

**This is the dominant fragility flag for iter-v3/050.** The cycle 3 PROMISING bundle uses TWO per-symbol customizations (per-symbol ATR for ALGO and LDO) plus ONE per-symbol direction-asymmetric block (primitive 10 BCH LONG). All three are per-symbol architecture variants. The iter-v3/039 anti-pattern would manifest as: multi-seed OOS Sharpe lifts strongly (mid-band +1.00 to +1.50) BUT multi-seed IS Sharpe collapses (mid-band +0.40 to +0.50, with downside risk to +0.30 or below).

Per `feedback_v3_strict_both_is_oos_baseline.md`: this manifestation = NO BASELINE UPDATE (IS Sharpe must also improve). The QR pre-commits to this rule and does NOT pre-grant any exception in this brief.

### 4.4 Fragility tests (LOAD-BEARING for NO-MERGE-FRAGILITY classification)

**Fragility test F1 — per-symbol architecture IS preservation**:
- iter-v3/045 single-seed IS +0.7459; iter-v3/047 single-seed IS +0.4872 (per-symbol ATR + primitive 10 added; -0.26 single-seed lottery)
- iter-v3/050 multi-seed prediction: if multi-seed mean IS Sharpe < +0.51 (iter-v3/028 anchor), the per-symbol architecture is the iter-v3/039 anti-pattern → NO BASELINE UPDATE per `feedback_v3_strict_both_is_oos_baseline.md`
- If multi-seed mean IS Sharpe ∈ [+0.51, +0.65] AND multi-seed mean OOS Sharpe > +0.51, BOOTSTRAP-style baseline update eligible (BOTH improve; aspirational gates may still fail)

**Fragility test F2 — bundle-level trade rate**:
- iter-v3/045 OOS=119 trades (single-seed, no primitive 10); iter-v3/047 OOS=92 trades (single-seed, with primitive 10); iter-v3/049 OOS=92 trades (similar)
- iter-v3/050 multi-seed prediction: ~120-180 trades (multi-seed averaging adds trades not subtracts; primitive 10 reduces BCH LONG OOS contribution)
- If bundle OOS trades < 130, **aspirational gate failure** but NOT a baseline-update blocker per `feedback_v3_baseline_update_policy.md`

**Fragility test F3 — multi-seed Sharpe variance**:
- Std(IS Sharpe) and Std(OOS Sharpe) across 2 outer seeds
- High inter-seed variance (std > 0.5 IS Sharpe units, std > 1.0 OOS Sharpe units) signals the strategy's edge is seed-luck-dependent
- If both outer seeds have OOS Sharpe > 0 AND IS Sharpe > 0, the strategy is robust under the 2-seed cap (per `feedback_v3_outer_seed_cap_2_v3.md` 2-seed Pareto rule = Gate 10)
- If only 1 of 2 outer seeds clears positive on either axis, **HARD BLOCK** (Gate 10 fail per `feedback_v3_outer_seed_cap_2_v3.md`)

**Fragility test F4 — LDO single-seed lottery flag**:
- iter-v3/049 single-seed LDO OOS = -19.13 weighted_pnl (-41.21% concentration); iter-v3/047 = same (frozen baseline carry-over from iter-v3/045)
- iter-v3/050 multi-seed prediction: if LDO OOS weighted_pnl remains < -10 across BOTH outer seeds, the LDO per-symbol ATR (iter-v3/045) is the iter-v3/039 anti-pattern materializing — this is fragility evidence for next-cycle EXPLORATION (potentially LDO removal from V3_MODELS at iter-v3/051+ EXPLORATION cycle), but does NOT block baseline update if BOTH IS+OOS aggregate beat /028 anchor

### 4.5 CONFIRMATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row + downstream action |
|---|---|---|
| `CONFIRMATION-MERGE-FULL` | All 10 MERGE gates §8 pass (incl. aspirational ≥+1.0 Sharpe floors) | Updates BASELINE_V3.md; tags v0.v3-050; cherry-picks docs+feat to quant-research |
| `CONFIRMATION-MERGE-BOOTSTRAP-style` | IS+OOS multi-seed mean BOTH beat /028 anchor BUT some aspirational gates fail (e.g. < +1.0 Sharpe floor; > 30% concentration; < 130 OOS trades) | Updates BASELINE_V3.md per `feedback_v3_baseline_update_policy.md`; tags v0.v3-050; records failed aspirational gates as outstanding constraints for iter-v3/051+ |
| `CONFIRMATION-NO-MERGE-revert` | Either IS multi-seed mean < +0.51 OR OOS multi-seed mean < +0.51 OR Hard-blocking gates (3, 6, 10) fail | iter-v3/049 head remains the new bundle "best EXPLORATION-PROMISING" record; BASELINE_V3.md remains at iter-v3/028; cycle 4 EXPLORATIONs anchor against iter-v3/028 + cycle 3 PROMISING bundle |
| `BLOCK` | Methodology check FAILED, or wall-clock cap exceeded, or §3.7 reconciliation row fails | Diary documents; iter-v3/051 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

Per `feedback_risk_mitigation_design.md`: every merge candidate must include this section with IS-calibrated thresholds and simulated historical effect. For iter-v3/050 the "simulated effect" IS the iter-v3/044/045/047 single-seed runs already committed; the multi-seed run validates that the historical effect persists under cross-validation.

### 5.1 Cadence-discipline structural safeguards

iter-v3/050 inherits FOUR structural safeguards:

1. **6h wall-clock hard cap** (per CONFIRMATION cadence rule per `feedback_v3_cadence_discipline.md` 2026-05-07 update): Engineer kills Phase 6 if elapsed > 6h.
2. **Single-axis variation rule** honored: only multi-seed config CHANGED (--seeds 1 → 2; total trials 700 → 1400), per-symbol ADX field DROPPED per Critic FINAL `1908d50` rec #2; features/labeling/risk-gates (except ADX field DROP)/universe byte-identical to iter-v3/049 head.
3. **CONFIRMATION-MERGE updates BASELINE_V3.md** only if BOTH IS+OOS multi-seed mean Sharpe beat iter-v3/028 anchor (+0.5101 IS / +0.5053 OOS) per `feedback_v3_strict_both_is_oos_baseline.md`. ANY hard-blocking gate failure (Gates 3, 6, 10) = NO MERGE.
4. **Pre-commitment lock** via `feedback_v3_strict_10_to_1_cadence.md` + `feedback_v3_iter018_confirmation_baseline_validation.md`: spec cannot be renegotiated post-hoc by future Engineer or QR.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-049)

1. **Adversarial unit tests** must PASS before backtest (88+/88+ tests; ALL gates including primitive 10's 7 tests + per-symbol ATR's 5 tests + per-symbol ADX's 5 tests + others).
2. **File-artifact reconciliation table** (§3.7). 22 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_MODELS`, `REQUIRED_GAP`, `V3_FEATURE_COLUMNS_TOP_N`, `ENSEMBLE_SIZE`, `V3_ATR_MULTIPLIERS_PER_SYMBOL`, `RiskV2Config.block_long_for/block_short_for`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.
5. **Sub-fix #1, #2 cosmetic-only**: ITERATION_LABEL bump + DROP one kwarg. Negligible regression risk; the per-symbol ADX field has empty-default fallback so omitting it == empty dict.

### 5.3 Multi-seed-axis specific risks (NEW for iter-v3/050)

1. **Outer-seed determinism**: `_derive_ensemble_seeds(outer_seed, size=5)` uses `np.random.default_rng(outer_seed)`. If user invokes `--seeds 2`, runner iterates `seed in [42, 123]` (the legacy seed list). Section 3.7 row 12 verifies `Seeds: 2` printed in run.log; Section 3.7 row 17 verifies pareto_front.csv has 2 distinct rows.
2. **Inner-ensemble determinism**: 5 inner seeds are derived per outer seed. iter-v3/006 fix already eliminated the pre-iter-v3/006 "all outer seeds got identical inner ensemble" bug. Verifier: pareto_front.csv shows distinct OOS Sharpes across 2 outer seeds (high probability if inner-ensemble derivation is correct).
3. **n_trials=35 budget per cell** (per `feedback_v3_confirmation_n_trials_35.md`): each (symbol, month) cell gets 35 Optuna trials × 5 inner seeds = 175 trials per cell per outer seed; 350 total trials per cell at multi-seed. Joint rank should give n_eff ≥ 15 (precedent: iter-v3/049 n_eff=18 at 700 trials; multi-seed at 1400 trials should be similar or higher).
4. **`colsample_bytree` Optuna-tuned**: per iter-v3/008 colsample A/B research, allowing Optuna to tune `colsample_bytree` is the production-config choice. iter-v3/007/008 EXPLORATION ran `colsample=1.0` hardcoded for fast-iteration determinism; non-exploration mode restores Optuna sampling. Per-seed feature-subsampling may add modest variance but is the production-correct config.

### 5.4 Per-symbol architecture concentration management (cycle 3 PROMISING carry-forward)

The cycle 3 PROMISING bundle uses TWO per-symbol customizations (per-symbol ATR for ALGO and LDO) plus ONE per-symbol direction-asymmetric block (primitive 10 BCH LONG). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` (2026-05-09 from iter-v3/039 closeout), the dominant fragility flag is the iter-v3/039 anti-pattern: per-symbol customizations lift OOS Sharpe materially but break IS aggregate at multi-seed (suspicious-OOS-divergence pattern persisted at multi-seed).

**Single-seed concentration evidence (lottery flag carry-forward)**:
- iter-v3/045 single-seed: ALGO 54.77%, TRX 23.95%, BCH 11.66%, LDO 9.62% (LDO POSITIVE)
- iter-v3/047 single-seed: ALGO 59.06%, TRX 64.43%, BCH 17.71%, LDO -41.21% (LDO NEGATIVE — flipped sign)
- iter-v3/049 single-seed: same as iter-v3/047 for ALGO/BCH/LDO (frozen baseline carry-over); TRX shifted to 64.43%

**Multi-seed compression hypothesis** (per `feedback_v3_concentration_is_signal.md`):
- Per-symbol PnL share caps are CLOSED-mechanism (iter-v3/020 closeout)
- Multi-seed averaging may compress per-symbol concentration variance (numerator stays similar, denominator may grow if other symbols' Optuna trajectories find better hyperparams under multi-seed)
- OR multi-seed averaging may NOT compress (if the single-seed lottery is structural)
- Fragility test F4 (§4.4): if LDO OOS weighted_pnl < -10 across BOTH outer seeds, the LDO per-symbol ATR is the iter-v3/039 anti-pattern — fragility evidence for next-cycle EXPLORATION (potentially LDO removal from V3_MODELS), but does NOT block baseline update if BOTH IS+OOS aggregate beat /028 anchor

The 30% per-symbol cap from `BASELINE_V3.md` "Inherited project-level merge gates" is the binding ASPIRATIONAL threshold per `feedback_v3_baseline_update_policy.md`. Multi-seed compression to ≤ 30% would clear the aspirational gate; persistence > 30% is fragility evidence regardless of headline Sharpe BUT does NOT block baseline update.

### 5.5 LDO single-seed lottery flag (specific carry-forward concern)

iter-v3/049 LDO OOS = -19.13 weighted_pnl (frozen baseline carry-over from iter-v3/045 single-seed=42 lottery). Per Critic FINAL `1908d50` recommendation #3: "LDO OOS structural concern requires CONFIRMATION investigation. ... At iter-v3/050 multi-seed CONFIRMATION (seeds 42 + alternative), if LDO remains consistently negative, the QR should consider whether LDO's per-symbol ATR (iter-v3/045) is the iter-v3/039 anti-pattern."

The QR explicitly carries this concern forward to iter-v3/050 Phase 7 evaluation:
- If LDO multi-seed mean OOS weighted_pnl > 0: per-symbol ATR for LDO survives multi-seed validation (PROMISING confirmation)
- If LDO multi-seed mean OOS weighted_pnl < 0 BUT bundle multi-seed mean IS+OOS Sharpe BOTH beat /028 anchor: BASELINE-UPDATE-eligible per `feedback_v3_baseline_update_policy.md`; LDO concern documented for iter-v3/051+ EXPLORATION cycle
- If LDO multi-seed mean OOS weighted_pnl < 0 AND bundle multi-seed mean fails any hard-blocking gate (3, 6, 10) OR fails BOTH-must-improve gate (IS or OOS multi-seed mean < anchor): NO MERGE; iter-v3/051 EXPLORATION on LDO-removal alternatives

---

## Section 6 — Risk Management Design (10-Primitive Gate Table)

### 6.1 10-primitive table — IDENTICAL to iter-v3/049 minus the per-symbol ADX field

All 10 risk gates carried forward from iter-v3/049 minus the per-symbol ADX field DROP. NO new gates added; the existing ADX gate reverts to global-only (no per-symbol asymmetry).

| # | Primitive | Spec | Fire-rate prediction (IS, multi-seed) | Source |
|---|---|---|---:|---|
| 1 | BTC trend | BtcTrendFilterConfig: lookback=42, threshold=15% | ≈ 12-13% killed | inherited iter-v3/012 |
| 2 | Hit rate | HitRateGateConfig: window=20, sl_threshold=0.65 | DISABLED | inherited iter-v3/013 |
| 3 | ADX gate | RiskV2Config: threshold=20.0 (global; **per-symbol DROP per iter-v3/050**) | ≈ 60% of bars pass | inherited iter-v3/013 (per-symbol DROPPED per Critic FINAL `1908d50` rec #2) |
| 4 | Hurst regime | hurst_100 > 0.5 gate; implicit feature | ≈ 90% of bars pass | inherited iter-v3/013 |
| 5 | Drawdown brake | R2 cumulative; per-model PnL tracking | per-model gate | inherited iter-v3/013 |
| 6 | Feature z-score OOD | RiskV2Config: zscore_threshold=2.0 (14-D space) | ≈ 25-35% killed | inherited iter-v3/011 |
| 7 | Liquidity floor | NATR floor: NATR >= 0.5% | symbol-dependent | inherited |
| 8 | Per-symbol cap | RiskV2Config: enable_per_symbol_cap=False | 0% (DISABLED) | iter-v3/020 CLOSED-mechanism |
| 9 | Regime gate | RiskV2Config: enable_regime_gate=False | 0% (DISABLED) | iter-v3/022 PARTIALLY-EFFECTIVE-CLOSED |
| 10 | Direction block (primitive 10) | RiskV2Config: block_long_for=("BCHUSDT",); block_short_for=() | ≈ 41% of BCH candidates blocked | iter-v3/047 PROMISING (IS-only); iter-v3/050 first multi-seed OOS test |

Combined kill rate target: **80–90%** (same as iter-v3/049). Multi-seed averaging does NOT change any primitive's threshold or fire rate — primitives operate per-(symbol, candle) on past-only data, independent of seed.

### 6.2 Regime coverage — UNCHANGED

4-symbol IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction.

### 6.3 Concentration — INFORMATIONAL gate at CONFIRMATION (per `feedback_v3_baseline_update_policy.md`)

iter-v3/045 single-seed shows ALGO 54.77% concentration; iter-v3/047/049 single-seed shows ALGO 59.06% + TRX 64.43%. Per `feedback_v3_baseline_update_policy.md` (2026-05-08 directive): aspirational gates (incl. top-symbol ≤ 30%) inform future-iteration priorities but do NOT block baseline updates.

**No explicit-with-justification exception clause needed at this CONFIRMATION**: per the 2026-05-08 directive, the BASELINE_V3.md update gate is BOTH IS+OOS multi-seed mean MUST beat /028 anchor; concentration > 30% does NOT block. The 30% threshold remains as an outstanding constraint for iter-v3/051+ cycles.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=10%)**: Multi-seed Sharpe variance is high enough to indicate trade-rate floor not met at bundle level. **Detection signal**: bundle OOS trades < 130 OR std(OOS Sharpe across 2 seeds) > 1.0. **Mitigation**: Section 3.7 row 19 verifier; Section 4.4 fragility test F2 + F3.

**Prediction P2 (process, P=20%)**: LDO single-seed negative concentration carries forward to multi-seed (LDO multi-seed mean OOS weighted_pnl < 0). **Detection signal**: per_symbol section of `comparison.csv` reports LDO weighted_pnl < 0 in multi-seed mean. **Mitigation**: Section 4.4 fragility test F4 → if bundle aggregate IS+OOS BOTH beat /028 anchor, BASELINE-UPDATE-eligible with LDO documented as outstanding constraint; if not, NO MERGE with iter-v3/051+ EXPLORATION on LDO-removal alternatives.

**Prediction P3 (process, P=15%)**: PBO max-aggregator catches per-cell tails — TRX/2025-Q4 carry-forward at 99% PBO is structurally persistent (precedent: iter-v3/013 catalog caveat). **Detection signal**: max(per_cell_pbo) ≥ 0.99 in `per_cell_pbo.csv`. **Mitigation**: pre-commit max-aggregator review per iter-v3/013 catalog caveats; the cross-cell mean PBO < 0.4 gate clears even if max is 0.99. Critic flags max-aggregator informationally but does NOT block on it (per iter-v3/028 BOOTSTRAP precedent).

**Prediction P4 (process, P=10%)**: Wall-clock exceeds 6h cap. **Detection signal**: wall-clock minutes > 360 in engineering report. **Mitigation**: Engineer kill switch at t=270 min if projection extrapolates beyond 6h; iter-v3/051 re-runs at reduced --n-trials 25 in subsequent iteration.

**Prediction P5 (process, P=10%)**: 10-seed pre-MERGE concentration validation runs separately after main backtest and shows < 7/10 profitable. **Detection signal**: post-Phase 7 10-seed sanity run produces fewer than 7 of 10 outer-seed Sharpes > 0. **Mitigation**: Per `feedback_seed_validation.md` (legacy v1/v2 rule, retained for v3 final-pre-MERGE check); the 2-seed cap from `feedback_v3_outer_seed_cap_2_v3.md` covers the main run. The 10-seed pre-MERGE check is a SEPARATE validation step that runs only IF the main 2-seed run clears the BOTH-must-improve gate. iter-v3/050 brief Section 8 specifies this as gate #9.

**Prediction P6 (model, P=25%) — DOMINANT FAILURE MODE**: The cycle 3 per-symbol architecture is the iter-v3/039 anti-pattern at multi-seed. Multi-seed OOS Sharpe lifts strongly (band [+1.00, +1.50]) BUT multi-seed IS Sharpe collapses (band [+0.30, +0.50]). Per `feedback_v3_strict_both_is_oos_baseline.md`: NO BASELINE UPDATE because IS regression. Catalog row: `CONFIRMATION-NO-MERGE-revert`. Action: iter-v3/051 EXPLORATION on per-symbol architecture revert OR LDO removal OR alternative composition. **Probability: 25%.**

**Prediction P7 (model, P=20%) — BOOTSTRAP-style success**: IS Sharpe in [+0.51, +0.65], OOS Sharpe in [+0.55, +1.00], some aspirational gates fail (< +1.0 floor; > 30% concentration; < 130 OOS trades) BUT BOTH IS+OOS multi-seed mean beat /028 anchor → CONFIRMATION-MERGE-BOOTSTRAP-style. The strategy's edge holds and is a STRICTLY-BETTER-than-/028 baseline; aspirational gates documented as outstanding constraints. iter-v3/050 ships v0.v3-050; BASELINE_V3.md updates per `feedback_v3_baseline_update_policy.md`. **Probability: 20%.**

**Prediction P8 (model, P=10%) — FULL SUCCESS**: IS Sharpe ≥ +1.0 AND OOS Sharpe ≥ +1.0 AND all aspirational gates pass → CONFIRMATION-MERGE-FULL. The strategy's edge clears all v3 thresholds at multi-seed validation. iter-v3/050 ships v0.v3-050; BASELINE_V3.md updates with FULL gate clearance. **Probability: 10%.**

**Prediction P9 (model, P=15%) — IS+OOS BOTH below /028 anchor**: IS multi-seed mean < +0.51 AND OOS multi-seed mean < +0.51. The cycle 3 PROMISING ingredients did not survive multi-seed validation. Catalog row: `CONFIRMATION-NO-MERGE-revert`. Action: iter-v3/051 EXPLORATION reverts the per-symbol architecture additions AND iter-v3/047 primitive 10. **Probability: 15%.**

**Prediction P10 (model, P=10%) — Hard-blocking gate failure**: Gate 3 (OOS/IS < 0.5) OR Gate 6 (PSR < 0.95) OR Gate 10 (one of two outer seeds Sharpe ≤ 0). Catalog row: `CONFIRMATION-NO-MERGE-revert` with hard-blocking gate documented. **Probability: 10%.**

The predictions are Bayesian-calibrated:
- 4 process-level (P1, P3, P4, P5) per iter-v3/003 lesson #3 discipline
- 6 model-level (P2, P6, P7, P8, P9, P10)
- Per the iter-v3/028 calibration history (CONFIRMATION-class spec at --seeds 2, 3 syms, 3.18h wall-clock): the 4-symbol bundle adds ~33% wall-clock; the per-symbol architecture adds ~25% probability mass to the iter-v3/039 anti-pattern fragility flag

**Summary**:
- **CONFIRMATION-MERGE-FULL probability ≈ 10%** (P8)
- **CONFIRMATION-MERGE-BOOTSTRAP-style probability ≈ 20%** (P7)
- **CONFIRMATION-NO-MERGE-revert probability ≈ 50%** (P6 + P9 + P10)
- **BLOCK probability ≈ 10%** (P4 dominant; P1+P3 contribute)
- **Single-seed lottery flag carryforward (no decision either way) ≈ 10%** (P2 + P5)

Total: 100% allocated; the dominant failure mode (P6 iter-v3/039 anti-pattern) is the most plausible single outcome. A rigorous multi-seed test of the per-symbol cycle 3 PROMISING bundle is overdue.

If any prediction fails to materialize, the iter-v3/050 diary documents the calibration miss.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically. Cannot be renegotiated post-hoc.**

iter-v3/050 is a CONFIRMATION iteration. Critic emits `CONFIRMATION-MERGE-FULL`, `CONFIRMATION-MERGE-BOOTSTRAP-style`, `CONFIRMATION-NO-MERGE-revert`, or `BLOCK`.

### BASELINE_V3.md update gate (LOCKED per `feedback_v3_strict_both_is_oos_baseline.md` 2026-05-09 directive)

**Per the 2026-05-09 directive at iter-v3/039 closeout**: BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean).

**Prior baseline (iter-v3/028 CONFIRMATION-MERGE)**:
- IS monthly Sharpe (multi-seed mean): **+0.5101**
- OOS monthly Sharpe (multi-seed mean): **+0.5053**

**iter-v3/050 BASELINE_V3.md update criteria**:
- `IS multi-seed mean Sharpe > +0.5101` AND
- `OOS multi-seed mean Sharpe > +0.5053`

If BOTH conditions are met, BASELINE_V3.md updates. If EITHER condition fails, NO MERGE per `feedback_v3_strict_both_is_oos_baseline.md`. Cannot be renegotiated.

### CONFIRMATION-MERGE-FULL iff ALL 10 of the following are true:

| # | Gate | Threshold | Source | Block-or-Aspirational |
|---|---|---:|---|---|
| 1 | IS monthly Sharpe ≥ +1.0 | multi-seed mean | `feedback_sharpe_floor.md` | ASPIRATIONAL (per `feedback_v3_baseline_update_policy.md` 2026-05-08) |
| 2 | OOS monthly Sharpe ≥ +1.0 | multi-seed mean | same | ASPIRATIONAL |
| 3 | OOS / IS Sharpe ratio ≥ 0.5 | derived from #1 #2 | `BASELINE_V3.md` | **HARD-BLOCKING** (per `feedback_v3_baseline_update_policy.md`) |
| 4 | DSR > 0.95 | from `dsr.json` (multi-seed n_trials=1400 expected) | `BASELINE_V3.md` | ASPIRATIONAL (structural at v3's trade volume per iter-v3/028 BOOTSTRAP) |
| 5 | PBO < 0.4 (cross-cell **mean** AND **max** aggregator both pass) | from `per_cell_pbo.csv`; cross-cell mean from dsr.json `pbo` field | `BASELINE_V3.md` + iter-v3/013 catalog max-aggregator pre-commit | ASPIRATIONAL (mean only checked) |
| 6 | PSR > 0.95 | from `dsr.json` | `BASELINE_V3.md` | **HARD-BLOCKING** (per `feedback_v3_baseline_update_policy.md`) |
| 7 | Top-symbol concentration ≤ 30% (multi-seed mean) | from per_symbol section of `comparison.csv` | `BASELINE_V3.md` | ASPIRATIONAL (per `feedback_v3_concentration_is_signal.md`: concentration is signal, not risk) |
| 8 | **Bundle-level OOS trade count ≥ 130** | from `comparison.csv` | `feedback_trade_rate_floor_bundle_level.md` (v3 supersedes legacy per-iteration rule) | ASPIRATIONAL |
| 9 | 10-seed pre-MERGE concentration validation: mean Sharpe > 0, ≥ 7/10 profitable | post-Phase 7 separate validation run; per `feedback_seed_validation.md` (legacy retained for v3 final-pre-MERGE) | `feedback_seed_validation.md` | ASPIRATIONAL (only runs if main 2-seed run passes BOTH-must-improve gate) |
| 10 | Multi-seed Pareto front non-domination — **2-seed rule per `feedback_v3_outer_seed_cap_2_v3.md`**: BOTH outer seeds Sharpe > 0 (binary, NOT "≥7/10 profitable" since N=2) | from `pareto_front.csv` | `feedback_v3_outer_seed_cap_2_v3.md` | **HARD-BLOCKING** |

**ALL 10 gates must pass for CONFIRMATION-MERGE-FULL.**

### CONFIRMATION-MERGE-BOOTSTRAP-style iff:

- BOTH IS multi-seed mean Sharpe > +0.5101 AND OOS multi-seed mean Sharpe > +0.5053 (BASELINE_V3.md update gate PASSES)
- AND Hard-blocking gates 3, 6, 10 ALL pass
- AND any subset of aspirational gates (1, 2, 4, 5, 7, 8, 9) fails
- BASELINE_V3.md updates per `feedback_v3_baseline_update_policy.md`; tags v0.v3-050; failed aspirational gates documented as outstanding constraints for iter-v3/051+

### CONFIRMATION-NO-MERGE-revert iff ANY of:

- IS multi-seed mean Sharpe ≤ +0.5101 (BASELINE_V3.md update gate FAILS on IS axis)
- OR OOS multi-seed mean Sharpe ≤ +0.5053 (BASELINE_V3.md update gate FAILS on OOS axis)
- OR Hard-blocking gate 3 fails (OOS/IS < 0.5)
- OR Hard-blocking gate 6 fails (PSR < 0.95)
- OR Hard-blocking gate 10 fails (one of two outer seeds Sharpe ≤ 0)
- iter-v3/049 head remains the new bundle "best EXPLORATION-PROMISING" record
- BASELINE_V3.md remains at iter-v3/028
- Catalog row documents which gate(s) failed; recommends specific revert / fix for next 10-EXPLORATION cycle

### BLOCK (process) iff ANY of:

- §3.7 reconciliation row(s) fail (Phase 5.5 BLOCK or Phase 6 setup defect)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 6h hard cap

### Discretionary judgment

iter-v3/050's MERGE pathway is mechanical: BOTH-must-improve gate determines BASELINE_V3.md update; hard-blocking gates determine MERGE eligibility. **NO QR or Critic discretion can override gate failures.**

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | 2.2.6 | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | 1.17.0 | BSD-3 | Stat tests (PSR formulation) | n/a |
| `statsmodels` | 0.14.6 | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | 1.8.0 | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | 4.6.0 | MIT | M1 only — no M2 (default --model lgbm restored at iter-v3/017) | n/a |
| `pytest` | (already installed) | MIT | adversarial tests | n/a |
| `pandas` | 3.0.0 | BSD-3 | Parquet I/O + analysis script CSV loading | n/a |
| `pyarrow` | 23.0.1 | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |
| `optuna` | 4.8.0 | MIT | Hyperparameter search (n_trials=35 per cell per inner seed per outer seed) | n/a |

**No new external deps.** Same stack as iter-v3/028-049. The iteration's NEW code is:
- 1 line edit in `run_baseline_v3.py` (ITERATION_LABEL "v3-049" → "v3-050")
- 1-2 line edit in `run_baseline_v3.py` (DROP `adx_threshold_per_symbol={"TRXUSDT": 21.0}` from `RiskV2Config()`)
- 1 line edit in `_verify_feature_columns` assertion (expect `adx_threshold_per_symbol == {}` instead of `{"TRXUSDT": 21.0}`)
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths
- 0 new pytest test files (existing 5 per_symbol_adx tests still PASS with empty dict — `test_default_empty_dict_preserves_v3_prior_behavior`)
- 0 modifications to V3_FEATURE_COLUMNS_TOP_N, V3_ATR_MULTIPLIERS_PER_SYMBOL, RiskV2Config (other fields), BTC_TREND_CONFIG, REQUIRED_GAP, V3_MODELS

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation (primary). Cross-cell max-aggregator INFORMATIONAL per iter-v3/013 catalog pre-commit. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-050/engineering_report.md` with:
- Git commit SHAs at backtest time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow|optuna)"`
- The full 14-feature list as actually trained on (sanity check against §3.3)
- Runtime `V3_MODELS` (4 entries, no MKR)
- Runtime `REQUIRED_GAP` (88)
- Runtime `ENSEMBLE_SIZE` (5; non-exploration mode)
- Runtime `args.seeds == 2`, `args.n_trials == 35`, `args.exploration is False`, `args.clean_oof == True`
- Runtime `RiskV2Config.adx_threshold_per_symbol == {}` (DROPPED per Critic FINAL `1908d50` rec #2)
- Runtime `RiskV2Config.block_long_for == ("BCHUSDT",)` (UNCHANGED carry-forward)
- Runtime `V3_ATR_MULTIPLIERS_PER_SYMBOL == {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}` (UNCHANGED carry-forward)
- The `comparison.csv` IS / OOS multi-seed monthly Sharpe values
- Multi-seed std(IS Sharpe) and std(OOS Sharpe) across 2 outer seeds (fragility test F3)
- The `pareto_front.csv` 2-row dump (gate #10 verification)
- The `dsr.json` DSR / PBO / PSR / n_eff dump (gates #4, #5, #6)
- Per-symbol concentration breakdown (gate #7)
- Bundle OOS trade count (gate #8)
- The wall-clock minutes total (must be < 360; target 120-270)
- The adversarial test outcome (PASS expected, 88+/88+ tests)
- The non-exploration activation banner from `run.log` (no "exploration" in invocation)
- The runner invocation literal (proof of `--seeds 2 --clean-oof` with NO `--exploration`)

---

## Section 10 — QR Audit Trail

**This is a CONFIRMATION**, not an EXPLORATION. Per `feedback_v3_axis_selection_quant_discipline.md` (2026-05-09 directive), QR-driven EDA-based axis selection applies to EXPLORATIONs. CONFIRMATIONs validate prior PROMISING bundles with no new axis variation.

**Bundle composition decided per Critic FINAL `1908d50` recommendation #2** (iter-v3/049 review.md, lines 83-91):

> "iter-v3/050 SECOND CONFIRMATION bundle composition (RECOMMENDED):
> - V3_FEATURE_COLUMNS_TOP_N = 14 features (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT per /048 closeout)
> - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (BCH+TRX use default)
> - RiskV2Config.block_long_for = ("BCHUSDT",) — primitive 10 carry-forward (iter-v3/047)
> - RiskV2Config.block_short_for = ()
> - RiskV2Config.adx_threshold_per_symbol = {} (EMPTY — TRX 21 DROPPED per this verdict)
> - Spec: --seeds 2, ENSEMBLE_SIZE=5, n_trials=35
>
> This bundle composition represents the union of all EXPLORATION-PROMISING ingredients in cycle 3 that survived their PATH-A pre-registration. Per-symbol ATR (ALGO+LDO) and primitive 10 (BCH LONG block) are the only edge ingredients. NO NEW axis variation; NO IS-only-validated mechanism (primitive 10 had IS-only evidence at iter-v3/047 but multi-seed validation falls under SECOND CONFIRMATION re-validation)."

**Authority chain**:
- Critic FINAL `1908d50` (iter-v3/049 review.md): bundle composition recommendation
- engineering_report `d8998d9` (iter-v3/049): EDA-corrected primitive 10 validation; frozen-baseline pattern OOS-confirmed
- `feedback_v3_strict_10_to_1_cadence.md` (2026-05-08): iter-v3/050 = SEPARATE CONFIRMATION (not collapsing iter-v3/049 EXPLORATION)
- `feedback_v3_strict_both_is_oos_baseline.md` (2026-05-09): BOTH-must-improve baseline update gate
- `feedback_v3_baseline_update_policy.md` (2026-05-08): aspirational vs hard-blocking gate distinction
- `feedback_v3_outer_seed_cap_2_v3.md`: --seeds 2 cap
- `feedback_v3_confirmation_n_trials_35.md`: --n-trials 35 default

**No QR-EDA-driven axis selection for iter-v3/050.** This is a CONFIRMATION; the bundle is LOCKED per Critic recommendation. The QR's role at iter-v3/050 is:
- Phase 5: produce this brief locking the bundle composition + MERGE gates pre-registration (current task)
- Phase 7: evaluate multi-seed OOS for first time; apply mechanical MERGE gates from Section 8
- Phase 8: write diary with MERGE/NO-MERGE decision and lessons

**Pre-commit SHAs**:
- Authority: Critic FINAL `1908d50` (iter-v3/049 review.md)
- iter-v3/049 head SHA (parent): `3a3d05b`
- Brief SHA: TBD (this commit)
- Setup commit SHA: TBD (Engineer's implementation commit)
- Phase 5.5 gate SHA: TBD (Engineer's gate verification)

**Phase 5.5 verification expectations**:
- Brief Section 2 cites EXISTING analysis from iter-v3/044/045/047 + iter-v3/049 (no new EDA needed since this is CONFIRMATION)
- Brief Section 3 LOCKED bundle composition matches Critic FINAL `1908d50` recommendation #2 verbatim
- Brief Section 8 LOCKED thresholds (BOTH-must-improve + hard-blocking gates) non-renegotiable post-hoc
- Pre-registered classification (CONFIRMATION-MERGE-FULL / BOOTSTRAP-style / NO-MERGE-revert / BLOCK) covers all observable outcomes

This Section 10 satisfies the process-discipline requirement that CONFIRMATION bundle composition is decided by Critic recommendation, not orchestrator ad-hoc. Cannot be retroactively renegotiated.

---

## Section 11 — Catalog-Row Pre-Commit Disposition

The catalog row to be appended at Phase 8 (diary closure) is pre-registered for ALL outcomes.

**Outcome A — CONFIRMATION-MERGE-FULL** (BOTH IS+OOS multi-seed mean Sharpe > /028 anchor AND IS Sharpe ≥ +1.0 AND OOS Sharpe ≥ +1.0 AND Hard-blocking gates 3, 6, 10 PASS AND aspirational gates 4, 5, 7, 8, 9 ALL PASS):
> `| iter-v3/050 | 2026-05-10 | SECOND v3 CONFIRMATION on cycle 3 best PROMISING bundle: V3_FEATURE_COLUMNS_TOP_N=14 (regime_momentum_signed_5d PRESENT; vol_normalized_ret_5d ABSENT); V3_ATR_MULTIPLIERS_PER_SYMBOL={ALGO+LDO (2.0, 1.5)}; primitive 10 BCH LONG block; --seeds 2 + ENSEMBLE_SIZE=5 + n_trials=35 + --clean-oof | <IS Δ vs /028> | <OOS Δ vs /028> | CONFIRMATION-MERGE-FULL | YES — BASELINE_V3.md updates to iter-v3/050; tags v0.v3-050; cherry-picks docs+feat to quant-research; all aspirational gates clear |`

**Outcome B — CONFIRMATION-MERGE-BOOTSTRAP-style** (BOTH IS+OOS multi-seed mean Sharpe > /028 anchor AND Hard-blocking gates 3, 6, 10 PASS BUT some aspirational gates fail):
> `| iter-v3/050 | 2026-05-10 | SECOND v3 CONFIRMATION on cycle 3 best PROMISING bundle | <IS Δ vs /028> | <OOS Δ vs /028> | CONFIRMATION-MERGE-BOOTSTRAP-style | YES — BASELINE_V3.md updates per `feedback_v3_baseline_update_policy.md` (BOTH IS+OOS beat /028 anchor); tags v0.v3-050; <list of failed aspirational gates> documented as outstanding constraints for iter-v3/051+ |`

**Outcome C — CONFIRMATION-NO-MERGE-revert** (IS or OOS multi-seed mean Sharpe ≤ /028 anchor OR Hard-blocking gates 3, 6, 10 FAIL):
> `| iter-v3/050 | 2026-05-10 | SECOND v3 CONFIRMATION on cycle 3 best PROMISING bundle | <IS Δ vs /028> | <OOS Δ vs /028> | CONFIRMATION-NO-MERGE-revert | NO — <list of failed gates>; iter-v3/049 head remains the new bundle "best EXPLORATION-PROMISING" record; BASELINE_V3.md remains at iter-v3/028; cycle 4 EXPLORATIONs (iter-v3/051-060) anchor against iter-v3/028 + cycle 3 PROMISING bundle |`

The diary commit closes the catalog row regardless of outcome. The 3-row pre-commit prevents post-hoc rationalization.

---

## Section 12 — Phase 5.5 Gate Self-Check (12 mandatory sections inventory)

| # | Section | Status |
|---|---|---|
| 1 | Section 0 — Data Split Declaration | PRESENT (sacred constants UNCHANGED; ENSEMBLE_SIZE=5 / colsample=Optuna-tuned / n_trials=35 / outer_seeds=2 SET BY non-exploration mode + --seeds 2 + default --n-trials invocation) |
| 2 | Section 0.5 — Iteration Type Declaration | PRESENT — TYPE: CONFIRMATION declared (SECOND true v3 CONFIRMATION post-/028 BOOTSTRAP); 6h HARD CAP; "cycle 3 best PROMISING bundle; NOT bundle assembly; multi-seed validation"; CONFIRMATION-MERGE updates BASELINE_V3.md if BOTH IS+OOS beat /028 anchor (`feedback_v3_strict_both_is_oos_baseline.md`); pre-commitment lock via `feedback_v3_strict_10_to_1_cadence.md` + `feedback_v3_iter018_confirmation_baseline_validation.md` |
| 3 | Section 1 — Hypothesis | PRESENT (one sentence; testable target multi-seed IS+OOS Sharpe BOTH beat /028 anchor) |
| 4 | Section 2 — IS-Only Numerical Evidence | PRESENT (structural difference from EXPLORATION briefs explicitly acknowledged; CONFIRMATION's analysis IS the iter-v3/044/045/047/049 baseline runs already committed; cycle 3 PROMISING bundle lineage table; iter-v3/045 strongest single-seed metrics; iter-v3/047 primitive 10 metrics; iter-v3/049 most-recent EXPLORATION metrics; per-symbol attribution; per-cell PBO + n_eff diagnostics) |
| 5 | Section 3 — Proposed Changes | PRESENT (symbols/labeling/features/risk-gates ALL UNCHANGED minus per-symbol ADX field DROP; only multi-seed config CHANGED; single-axis discipline preserved (the axis IS multi-seed-validation); 22-row reconciliation table; ENSEMBLE_SIZE/n_trials/colsample verified in runner code) |
| 6 | Section 4 — Expected OOS Impact | PRESENT (predicted multi-seed Sharpe bands [IS +0.40 to +0.65, OOS +0.55 to +1.50]; per-symbol concentration prediction bands; bundle OOS trade count prediction [80, 160]; 4 fragility tests F1/F2/F3/F4; CONFIRMATION outcome interpretation table; iter-v3/039 anti-pattern dominant fragility flag) |
| 7 | Section 5 — Risk Mitigation | PRESENT (4 cadence-discipline structural safeguards + 5 methodology-pipeline safeguards + 4 multi-seed-axis specific risks + per-symbol architecture concentration management + LDO single-seed lottery flag specific carry-forward concern; per `feedback_risk_mitigation_design.md`, simulated effect IS the iter-v3/044/045/047 single-seed runs) |
| 8 | Section 6 — Risk Management Design | PRESENT (10-primitive table inherited; gate orthogonality verified for multi-seed; concentration is INFORMATIONAL gate at CONFIRMATION per `feedback_v3_baseline_update_policy.md`; per-symbol ADX field DROP documented at gate #3) |
| 9 | Section 7 — Pre-Registered Failure-Mode | PRESENT (10 predictions with **4 process-level (P1, P3, P4, P5)**; calibrated CONFIRMATION-MERGE-FULL probability ~10%, CONFIRMATION-MERGE-BOOTSTRAP-style ~20%, CONFIRMATION-NO-MERGE-revert ~50%, BLOCK ~10%; iter-v3/039 anti-pattern as dominant single failure mode at P=25%) |
| 10 | Section 8 — Pre-Registered MERGE/NO-MERGE Criteria | PRESENT (BASELINE_V3.md update gate LOCKED at BOTH IS+OOS multi-seed mean > /028 anchor; 10 MERGE gates with hard-blocking-vs-aspirational distinction; 4 verdict pathways; concentration is informational per `feedback_v3_baseline_update_policy.md`) |
| 11 | Section 9 — Library Stack | PRESENT (no new deps; aggregator strategy unchanged from iter-v3/028-049) |
| 12 | Section 10 — QR Audit Trail | PRESENT (NO QR-EDA-driven axis selection because CONFIRMATION; bundle composition decided per Critic FINAL `1908d50` rec #2; authority chain documented; iter-v3/049 head SHA `3a3d05b` cited as parent) |
| 13 | Section 11 — Catalog-Row Pre-Commit | PRESENT (3 outcomes pre-registered: MERGE-FULL / MERGE-BOOTSTRAP-style / NO-MERGE-revert) |
| 14 | Section 12 — Phase 5.5 Gate Self-Check | PRESENT (this section) |

**All 14 sections (12 mandatory + Section 11 pre-commit + Section 12 self-check) PRESENT.** Engineer's Phase 5.5 gate should PASS this brief.

---

## Section 13 — Status

**READY-FOR-PHASE-5.5** — research brief complete. Engineer reads this brief, verifies the sections, runs the bundle state assertions (incl. `adx_threshold_per_symbol == {}` DROP assertion), runs all adversarial tests (88+/88+ expected to PASS — `test_default_empty_dict_preserves_v3_prior_behavior` continues to validate the empty-default fallback), **does NOT regenerate v3 features** (gate-config-only change with field DROP), and writes `phase5p5_gate.md` with OVERALL=PASS. Phase 6 backtest then runs at `--seeds 2 --clean-oof` (CONFIRMATION-spec; non-exploration mode); budget 120-270 min; well within 6h cap.

After Phase 6 closes, Critic Phase 7.5 review fires; QR Phase 7 evaluates OOS for first time; QR Phase 8 closes the catalog row at one of the 3 pre-registered dispositions.

iter-v3/050 is the SECOND v3 CONFIRMATION (after iter-v3/018 BOOTSTRAP and iter-v3/028 first CONFIRMATION-MERGE post-bootstrap, AND after iter-v3/039 first CONFIRMATION post-/028 NO-MERGE).

---

## Section 14 — Cycle 4 carry-forward note (post-iter-v3/050)

After iter-v3/050 closes (regardless of MERGE outcome), iter-v3/051-060 = cycle 4 of 10 EXPLORATIONs per `feedback_v3_strict_10_to_1_cadence.md`. iter-v3/061 = cycle 4 CONFIRMATION (third v3 CONFIRMATION ever).

**Anchor for cycle 4 EXPLORATIONs**:
- IF iter-v3/050 = MERGE (Outcome A or B): cycle 4 anchors against iter-v3/050 multi-seed bundle (BASELINE_V3.md updated)
- IF iter-v3/050 = NO-MERGE (Outcome C): cycle 4 anchors against iter-v3/028 + cycle 3 PROMISING bundle (or simply iter-v3/049 head if Critic recommends preserving the bundle as "best EXPLORATION-PROMISING" record)

**Outstanding constraints to inform cycle 4 axis priorities** (carried forward from /028 + likely persisting at /050):
- IS Sharpe lift toward +1.0 floor (current ~+0.51; need +0.49 lift)
- OOS Sharpe lift toward +1.0 floor (current ~+0.51 multi-seed at /028; possibly +0.55-1.00 at /050)
- DSR > 0 (currently 0; structural at v3's trade volume — reformulate gate?)
- Top-symbol concentration ≤ 30% (currently 75-77% multi-seed at /028)
- Bundle OOS trades ≥ 130 (currently 91-96 at /028; possibly 80-160 at /050)

**Axis priority recommendations for iter-v3/051**:
- HIGH: NEW feature families (engineered features pivot per `feedback_v3_engineered_features_proven.md`)
- MEDIUM: per-symbol revert tests if iter-v3/050 = NO-MERGE due to per-symbol architecture failure
- LOW: knob axes (saturated)

This Section 14 is INFORMATIONAL and pre-commits ZERO axis selection for cycle 4. The QR at iter-v3/051 has full discretion to choose any cycle 4 axis based on iter-v3/050 outcome + diary lessons.

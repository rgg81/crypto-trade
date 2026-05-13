# Iteration v3-059 — Research Brief (RE-ANCHOR #2: unified 10-seed ensemble)

**Type**: RE-ANCHOR #2 (special category — orthogonal to cycle counting per user directive
2026-05-13; NOT a cycle 1 EXPLORATION; NOT subject to 10:1 cadence constraint)
**Track**: v3 (rigor arm) — fifty-ninth iteration
**Branch**: `iteration-v3/059` (created from `iteration-v3/058` head at SHA `ab2d9ac`;
includes Phase A Optuna n_jobs=2 at `0a3c30e` + Phase B-3 unified 10-seed ensemble at
`ab2d9ac` + walk-forward fix at `e149e9d`)
**Date**: 2026-05-13
**Author**: QR (orchestrator-mandated RE-ANCHOR #2)
**EDA SHA**: N/A — RE-ANCHOR #2 runs the EXACT /028 bundle under new architecture.
No new EDA required.

**MANDATED AXIS** (per user directive 2026-05-13):
This is NOT a new axis. /059 verifies the EXACT /028 BASELINE_V3.md bundle (also used by
/058 RE-ANCHOR #1) under the unified 10-seed ensemble architecture introduced in Phase B-3
(`ab2d9ac`). The prior /058 multi-seed mean IS +0.7481 / OOS +0.8700 was produced under
2-outer × 5-inner architecture. The unified 10-seed architecture (single inference path,
all 10 models averaged per prediction) produces a DIFFERENT trade roster — the re-anchor
is required to establish the canonical baseline for cycle 1+ EXPLORATIONs under the new
architecture.

Per user policy: iter-v3/058 (tag v0.v3-058) remains canonical BASELINE_V3.md until
/059 completes; then BASELINE_V3.md updates to /059 values regardless of direction.

**WHAT CHANGES vs /058**:
1. **ITERATION_LABEL** = "v3-059"
2. **ENSEMBLE_SIZE = 10** (already set at Phase B-3 commit `ab2d9ac`; was 5 at /058 run-time)
3. **Unified 10-seed ensemble**: single LightGbmStrategy inference path averaging across
   all 10 ENSEMBLE_SEEDS (lineage-preserving: first 5 from outer=42, last 5 from outer=123).
   Outer-seed loop ELIMINATED; single unified pass replaces 2-outer × 5-inner loop.
4. **Optuna n_jobs=2** (Phase A commit `0a3c30e`; was n_jobs=1 at /058 run-time)
5. **--seeds deprecated**: `--seeds N` logs warning and is ignored; not passed for /059

**WHAT STAYS UNCHANGED from /028 BASELINE_V3.md and /058**:
- V3_FEATURE_COLUMNS_TOP_N (14): all 14 features identical to /028 spec
- V3_MODELS: (BCHUSDT, LDOUSDT, TRXUSDT)
- V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty)
- DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)
- RiskV2Config: block_long_for=(), adx_threshold_per_symbol={},
  enable_per_symbol_drawdown_brake=False
- REQUIRED_GAP = 66 = (21+1)×3
- CPCV: n_paths=45, embargo=27
- Sacred constants: OOS_CUTOFF_DATE=2025-03-24, training_months=24
- n_trials = 35 per cell
- Walk-forward fix from `e149e9d` (embargo of 22 candles at train/test boundary)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 10             # unified 10-seed (Phase B-3 architecture)
ENSEMBLE_SEEDS   = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                     33158374, 1465339467, 1273345680, 115579757, 1952249162)
n_trials         = 35             # CONFIRMATION default (per feedback_v3_confirmation_n_trials_35.md)
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/059 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: RE-ANCHOR #2 (special category)
  - Orthogonal to cycle counting per user directive 2026-05-13
  - NOT a cycle 1 EXPLORATION (NOT counted toward 10:1 cadence)
  - NOT a competitive CONFIRMATION
  - Purpose: establish canonical BASELINE_V3.md under unified 10-seed architecture

Architecture change being anchored:
  Phase A (commit 0a3c30e): Optuna n_jobs=2 parallelization
  Phase B-3 (commit ab2d9ac): unified 10-seed ensemble (ENSEMBLE_SIZE=10;
    outer-seed loop eliminated; single inference path)
  Walk-forward fix (commit e149e9d): 22-candle embargo at train/test boundary

Wall-clock budget: estimated 3.5-5h (n_jobs=2 provides ~30% speedup vs /058's 5.49h)
Run command: uv run python run_baseline_v3.py --clean-oof
  (--seeds NOT passed; deprecated in Phase B-3 architecture)
```

---

## Section 1 — Hypothesis

**SINGLE HYPOTHESIS**: The /028 bundle (V3_FEATURE_COLUMNS_TOP_N 14 features, V3_MODELS
BCH+LDO+TRX, default ATR (2.0, 1.0), no drawdown brake, no block_long_for, no regime gate)
under the unified 10-seed ensemble architecture (Phase B-3 commit `ab2d9ac`) + Optuna
n_jobs=2 (Phase A commit `0a3c30e`) + post-fix walk-forward (commit `e149e9d`) produces a
NEW unbiased baseline that replaces iter-v3/058 (tag v0.v3-058) as canonical BASELINE_V3.md.

**Mechanism**: The unified 10-seed architecture merges the two outer seeds (42 and 123)
into a single LightGbmStrategy instance with ENSEMBLE_SEEDS = 10 lineage-preserving
seeds. Instead of producing two separate trade rosters (one per outer seed) and then
averaging their Sharpe metrics, the unified architecture produces a SINGLE trade roster
from one inference pass that averages across all 10 models per prediction. This changes
the trade roster — the re-anchor captures the new architecture's actual distribution.

**What this iteration tests**: only the architecture effect on the /028 bundle's
performance. The bundle composition is FIXED (no axis variation).

**What this iteration does NOT test**:
- ANY axis variation (no feature SWAP, no risk primitive change, no labeling change)
- ANY new feature family
- ANY universe change
- ANY labeling change

---

## Section 2 — IS-Only Numerical Evidence

**NO new EDA required.** This is a RE-ANCHOR #2 under architecture change, not signal
discovery. The bundle composition is FIXED at /028 BASELINE_V3.md spec.

### Section 2.1 — Anchor spec citations

| Spec element | Value | Source |
|---|---|---|
| V3_FEATURE_COLUMNS_TOP_N | 14 features (identical to /028) | BASELINE_V3.md §Code Configuration |
| V3_MODELS | (BCHUSDT, LDOUSDT, TRXUSDT) | BASELINE_V3.md §Code Configuration |
| ATR multipliers | (atr_tp=2.0, atr_sl=1.0) default for all symbols | BASELINE_V3.md §Code Configuration |
| ENSEMBLE_SIZE | 10 (unified; Phase B-3) | commit ab2d9ac |
| ENSEMBLE_SEEDS | 10 lineage-preserving values | run_baseline_v3.py lines 97-108 |
| n_trials | 35 per cell (350 total = 35 × 3 sym × 10 seeds) | run_baseline_v3.py |
| CPCV | n_paths=45, embargo=27, REQUIRED_GAP=66 | BASELINE_V3.md §Code Configuration |
| Optuna n_jobs | 2 (Phase A) | commit 0a3c30e |
| Walk-forward fix | embargo=22 candles at train/test boundary | commit e149e9d |

**Note on n_trials total**: Under unified 10-seed architecture, n_trials_total =
35 × 3 sym × 10 seeds = 1050 (SAME as /058's 35 × 3 × 2 outer × 5 inner = 1050).
Total Optuna trials are unchanged; only the inference structure changes.

### Section 2.2 — Prior architecture comparison

| Metric | /058 (2-outer × 5-inner) | /059 prediction |
|---|---:|---|
| IS monthly Sharpe (multi-seed mean) | +0.7481 | +0.55 to +0.85 (could be higher or lower) |
| OOS monthly Sharpe (multi-seed mean) | +0.8700 | +0.65 to +0.95 |
| n_trials total | 1050 | 1050 (unchanged) |
| Trade roster | 2 rosters merged | 1 unified roster |
| Report structure | seed_summary.json + pareto_front.csv | cpcv_paths.csv + dsr.json (no per-seed Pareto) |

### Section 2.3 — Phase commit chain

1. `e149e9d` — walk-forward embargo fix (cherry-pick from main `5566a69`)
2. `0a3c30e` — Optuna n_jobs=2 parallelization (Phase A)
3. `ab2d9ac` — unified 10-seed ensemble architecture (Phase B-3)
4. THIS COMMIT — ITERATION_LABEL="v3-059" + brief + phase5p5 gate

---

## Section 3 — Proposed Changes (Setup Commit Locked)

### Edit 1: `run_baseline_v3.py` — ITERATION_LABEL only

```python
ITERATION_LABEL = "v3-059"
```

All other constants already set correctly by Phase B-3 commit `ab2d9ac`:
- `ENSEMBLE_SIZE: int = 10` (was 5 at /058 run-time)
- `ENSEMBLE_SEEDS: tuple[int, ...]` = 10-value lineage-preserving tuple
- `--seeds` flag deprecated (logs warning, value ignored)
- `_verify_feature_columns` ENSEMBLE_SIZE=10 assertion active
- `n_trials_total = args.n_trials * ENSEMBLE_SIZE * len(active_models)`
  = 35 × 10 × 3 = 1050

### Edit 2: `_verify_feature_columns` docstring — update iter reference to /059

Docstring updated to reference iter-v3/059 (not /058) as the current brief.

### Carry-forward state (all UNCHANGED):
- `V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`
- `RiskV2Config(adx_threshold_per_symbol={}, block_long_for=(), enable_per_symbol_drawdown_brake=False)`
- `REQUIRED_GAP = 66`
- V3_FEATURE_COLUMNS_TOP_N: 14 features (identical to /028)
- Walk-forward fix at `e149e9d` present

---

## Section 4 — Expected OOS Impact

### Section 4.1 — Architecture effect on trade roster

The unified 10-seed architecture changes inference from:

**Old (2-outer × 5-inner)**: Two separate 5-seed LightGbmStrategy instances (outer=42
and outer=123) each produce independent signals. A trade is opened only when their signals
agree (effective intersection of two trade rosters). The reported Sharpe is the arithmetic
mean of the two seeds' individual Sharpe values.

**New (unified 10-seed)**: One LightGbmStrategy instance with 10 seeds produces one
signal by averaging predictions across all 10 models. A trade is opened based on the
unified prediction. The trade roster is DIFFERENT — typically fewer trades if 10-model
consensus is harder to reach, or more trades if averaging reduces variance.

The expected Sharpe could be HIGHER or LOWER than /058's multi-seed mean depending on:
1. Whether consensus averaging reduces signal quality (fewer, lower-quality trades)
2. Whether variance reduction improves trade selection (fewer, higher-quality trades)
3. The specific random effects of the 10 ENSEMBLE_SEEDS on BCH/LDO/TRX hyperparameters

### Section 4.2 — Predicted range

| Metric | /058 observed | /059 predicted band |
|---|---:|---|
| IS monthly Sharpe (single-path) | +0.7481 (mean of 2) | **+0.55 to +0.85** |
| OOS monthly Sharpe (single-path) | +0.8700 (mean of 2) | **+0.65 to +0.95** |
| IS Trades | 173 (seed 42); 177 mean | 150 to 200 |
| OOS Trades | 103/86 (seeds 42/123) | 80 to 120 |
| OOS/IS Sharpe ratio | 1.163 | 0.7 to 1.5 |
| frac_positive_paths | 0.6444 | 0.50 to 0.75 |

**Falsifier**: If either IS or OOS Sharpe < +0.40, this signals an architecture-level
regression requiring investigation before cycle 1 EXPLORATIONs proceed.

### Section 4.3 — Path classifications (pre-committed)

```
RE-ANCHOR-MERGE-CLEAN:           IS > 0 AND OOS > 0 AND OOS/IS in [0.7, 1.5]
RE-ANCHOR-MERGE-OOS-DOMINANT:    OOS > 0 AND OOS/IS > 1.5 (suspicious)
RE-ANCHOR-MERGE-IS-DOMINANT:     IS > 0 AND OOS/IS < 0.7 (suspicious)
RE-ANCHOR-COLLAPSE:              IS <= 0 OR OOS <= 0 (investigate)
```

All paths MANDATE BASELINE_V3.md update per user policy.

---

## Section 5 — Risk Mitigation

Same 7-primitive gate stack as /028 and /058:
1. BTC trend kill (threshold_pct=15.0, lookback=42 bars)
2. Vol scaling (zscore_threshold=2.0)
3. ADX gate (adx_threshold=20.0, adx_threshold_per_symbol={})
4. Hurst regime gate
5. Feature z-score OOD (threshold=2.0)
6. Low-vol filter
7. Hit-rate gate (DISABLED)

Per-symbol drawdown brake: DISABLED (enable_per_symbol_drawdown_brake=False)
Block-long: EMPTY (block_long_for=())

Risk surface is identical to /058. The only change is the ensemble architecture;
no new code paths exercised in the risk stack.

---

## Section 6 — Risk Management Design (UNCHANGED)

8-primitive framework status (all UNCHANGED from /058):

| Primitive | Status | Threshold |
|---|---|---|
| Vol-adjusted sizing | ACTIVE | zscore_threshold=2.0 |
| ADX gate | ACTIVE | 20.0 (global); {} per-symbol |
| Hurst regime | ACTIVE | hurst_100 >= 0.5 |
| Z-score OOD | ACTIVE | zscore_threshold=2.0 |
| Drawdown brake | DISABLED | enable_per_symbol_drawdown_brake=False |
| BTC contagion kill | ACTIVE | threshold_pct=15.0 |
| Per-symbol kill switch | DISABLED | block_long_for=() |
| Hit-rate gate | DISABLED | enabled=False |

No gate threshold changes. No new primitives. Fire-rate predictions are UNCHANGED
from /058 (same bundle, same gate stack).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode** (15-25% probability):
RE-ANCHOR-COLLAPSE — unified 10-seed consensus is too strict; the 10-model average
produces near-zero signal variance, resulting in very few trades and collapsed Sharpe.
Detection: OOS Trades < 60 AND OOS Sharpe < +0.20.

If this fires: investigate ENSEMBLE_SEEDS lineage values for degenerate convergence;
consider whether unified architecture needs a minimum prediction-dispersion threshold
before a trade fires.

**Second most plausible failure mode** (20-30% probability):
RE-ANCHOR-MERGE-IS-DOMINANT — unified ensemble over-regularizes IS but OOS suffers
from reduced trade count (too few OOS opportunities to measure reliable Sharpe).
Detection: IS > 0 AND OOS/IS < 0.7.

**Primary success scenario** (50-60% probability):
RE-ANCHOR-MERGE-CLEAN — architecture change produces moderate Sharpe shift (IS in
[+0.55, +0.85]; OOS in [+0.65, +0.95]) with cleaner IS/OOS ratio (0.7-1.3) due to
reduced inter-seed variance in the unified path.

---

## Section 8 — RE-ANCHOR #2 MERGE Criteria (LOCKED)

### Section 8.1 — Mandatory BASELINE_V3.md update

Per user policy (2026-05-13): BASELINE_V3.md updates with /059 single-Sharpe values
REGARDLESS of metrics direction. The only question is the path classification.

### Section 8.2 — Pareto Gate 10 RETIRED

Pareto Gate 10 (multi-seed: both seeds OOS > 0) is NOT applicable to the unified
10-seed architecture (no separate per-outer-seed Pareto exists). Gate 10 is RETIRED
for /059 and all future iterations under the unified architecture.

### Section 8.3 — NEW Gate 10-CPCV

```
Gate 10-CPCV: cpcv_frac_positive_paths >= 0.55
```

Replaces Gate 10 (Pareto) as the multi-path robustness gate. /058 achieved 0.6444;
threshold of 0.55 is the formal floor for CLEAN classification.

### Section 8.4 — Hard-blocking gates retained

| Gate | Threshold | Notes |
|---|---|---|
| Gate 3: OOS/IS Sharpe ratio | >= 0.5 | Hard-blocking |
| Gate 6: PSR | > 0.95 | Hard-blocking |
| Gate 10-CPCV: frac_positive_paths | >= 0.55 | NEW — replaces Gate 10 Pareto |

### Section 8.5 — Path adjudication (LOCKED pre-run)

```
PRIMARY: BASELINE_V3.md update (MANDATORY)

SECONDARY path (in priority order):
  RE-ANCHOR-MERGE-CLEAN:
    IS > 0 AND OOS > 0 AND OOS/IS in [0.7, 1.5] AND frac_positive_paths >= 0.55
    → "CLEAN": cycle 1 proceeds normally on /059 anchor

  RE-ANCHOR-MERGE-OOS-DOMINANT:
    OOS > 0 AND OOS/IS > 1.5
    → "SUSPICIOUS": QR diagnostic before cycle 1 launch

  RE-ANCHOR-MERGE-IS-DOMINANT:
    IS > 0 AND OOS/IS < 0.7
    → "SUSPICIOUS": QR diagnostic before cycle 1 launch

  RE-ANCHOR-COLLAPSE:
    IS <= 0 OR OOS <= 0
    → "INVESTIGATE": architecture-level regression; hold cycle 1 until resolved
```

---

## Section 9 — Library Stack Declaration

UNCHANGED from /058 + /028:
- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=2 via Phase A `0a3c30e`)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new dependencies. The unified ensemble uses only the existing LightGbmStrategy
`ensemble_seeds_override` parameter path (no new code needed; Phase B-3 refactored
the runner to pass ENSEMBLE_SEEDS directly as a 10-tuple).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, brief Section 10 documents the
research path. For RE-ANCHOR #2, the audit trail documents the orchestrator-mandated
architecture change (no EDA-driven axis choice).

### Stage 1 — Architecture change mandate

User directive 2026-05-13: RE-ANCHOR #2 runs the /028 bundle under unified 10-seed
ensemble (Phase B-3) + Optuna n_jobs=2 (Phase A). iter-v3/058 was produced under
2-outer × 5-inner architecture; the architecture is now unified; the canonical baseline
must reflect the new architecture.

### Stage 2 — Bundle composition unchanged

/059 bundle = /028 BASELINE_V3.md bundle = /058 RE-ANCHOR #1 bundle. No new feature
selection, no axis variation, no risk primitive changes.

### Stage 3 — Commit chain

1. `e149e9d` — walk-forward fix (22-candle embargo at train/test boundary)
2. `0a3c30e` — Optuna n_jobs=2 (Phase A)
3. `ab2d9ac` — unified 10-seed ensemble, ENSEMBLE_SIZE=10, ENSEMBLE_SEEDS 10-tuple,
   --seeds deprecated, outer-seed loop eliminated (Phase B-3)
4. THIS COMMIT — ITERATION_LABEL="v3-059" + research brief + phase5p5 gate

### Stage 4 — Cycle counting

RE-ANCHOR #2 is orthogonal to cycle counting per user directive 2026-05-13. Cycle 1
cadence (10 EXPLORATIONs + 1 CONFIRMATION) is unaffected; it starts after /059
BASELINE_V3.md update. iter-v3/060 = CYCLE 1 EXPLORATION #1 of 10.

### Stage 5 — Setup commit SHA backfill

```
Setup commit SHA: (BACKFILL after setup commit)
Phase 5.5 gate SHA: (BACKFILL after gate commit)
```

---

## Section 11 — Catalog Row Pre-Commit

Pre-committed catalog row template (inserted at `briefs-v3/exploration_catalog.md`
after Phase 8 diary):

```
| RE-ANCHOR #2 | /059 | RE-ANCHOR #2: /028 bundle under unified 10-seed ensemble (Phase B-3) | <IS> | <OOS> | Gate 10-CPCV: <frac_positive_paths> | RE-ANCHOR-MERGE-{CLEAN/OOS-DOM/IS-DOM/COLLAPSE} | BASELINE_V3.md replaced (v0.v3-058 retired) |
```

RE-ANCHOR #2 is NOT counted toward cycle 1 cadence.

---

**END OF BRIEF — Phase 5 complete.**

**Next**: Engineer dispatches Phase 5.5 gate, then Phase 6 backtest launch (detached).
Run command: `uv run python run_baseline_v3.py --clean-oof`
(No --seeds flag; deprecated in Phase B-3 architecture)

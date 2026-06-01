# Research Brief — iter-v1/051

## Section 0.0 — Banner

- **Track**: v1 (refactored)
- **Iteration**: iter-v1/051
- **Type**: `EXPLORATION` (cycle-6 EXPLORATION 6/10; multi-seed re-validation sub-type)
- **Axis family**: `validation` (per-symbol mandate sub-class; multi-seed re-validation — distinct
  from feature-family + risk-primitive of /050)
- **Axis varied**: Drop the inert vol-spike regime gate (0% fire rate in /050); run DOT-only
  cohort with `V1_FEATURE_COLUMNS_PRUNED` (46 cols, unchanged) at `--seeds 4` (outer seeds 42,
  offset5, offset10, offset15) to validate that /050's PROMISING-PARTIAL lift (+1.1162 IS Δ) is
  not a single-seed lottery artifact.
- **Anchor**: iter-v1/050 PROMISING-PARTIAL closeout (IS Δ +1.1162; single seed=42); DOT IS
  Sharpe baseline -1.23 (BASELINE_V1.md `f8bc12c`).
- **Mode**: EXPLORATION budget (n_trials=18, --seeds 4, ENSEMBLE_SIZE=3; wall-clock cap ≤ 2h
  per seed × 4 seeds ≈ total ≤ 8h; EXPLORATION wall-clock applies per-seed, not aggregate)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_MS = 1742774400000` (2025-03-24 UTC) — **IMMUTABLE** (`src/crypto_trade/config.py`).
- `training_months = 24` — **IMMUTABLE**.
- IS window: data start ... 2025-03-24 (strictly less-than `OOS_CUTOFF_MS`).
- OOS window: 2025-03-24 ... data end. Forensic only (not a /051 verdict gate).
- Symbol universe: **DOTUSDT only** (`V1_ITER051_UNIVERSE = ("DOTUSDT",)`). BTC klines loaded
  for cross-asset feature computation only (not traded).
- All Phase 5 EDA uses **IS-only** data (`open_time < OOS_CUTOFF_MS`). Section 2 EDA artifact
  mirrors /050's EDA (same feature; no new feature; artifact authored for completeness).

---

## Section 0.5 — Iteration Type Declaration + Cadence

- **Type**: EXPLORATION (NOT CONFIRMATION). Multi-seed re-validation sub-type: no NEW axis
  variation; repeating /050's exact feature+cohort config at additional outer seeds.
- **Cycle slot**: cycle-6 EXPLORATION **6/10**.
  - /046: methodology axis — PROMISING-DIVERGENCE
  - /047: feature-family (skew_zscore_21) — NEGATIVE
  - /048: feature-family (trade_count_zscore_30) — NEGATIVE
  - /049: feature-family (long_short_zscore_30) — NEGATIVE
  - /050: feature-family + risk-primitive (DOT regime specialist) — PROMISING-PARTIAL
  - /051: validation (multi-seed re-validation of /050) — **THIS ITER**
- **Cadence**: n_trials=18, ENSEMBLE_SIZE=3, --seeds 4. Wall-clock cap ≤ 2h per outer seed
  (EXPLORATION standard); 4 outer seeds run sequentially = up to 8h total. Each outer seed is
  a separate EXPLORATION-budget run.

---

## Section 0.6 — Architecture-Family Justification (v1-only Axis Rotation Discipline)

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/047 | 2026-06-01 | feature-family |
| iter-v1/048 | 2026-06-01 | feature-family |
| iter-v1/049 | 2026-06-01 | feature-family |
| iter-v1/050 | 2026-06-01 | feature-family + risk-primitive |
| iter-v1/051 | 2026-06-01 | validation |

- **Axis family this iter**: `validation` (per-symbol regime-specialist mandate sub-class;
  multi-seed re-validation). The rotation axis is distinct from feature-family, model-arch,
  labeling, universe, or risk-primitive — it is a seed-validation sub-class that does NOT
  change the trained model architecture.
- **Rotation status**: **VALID** — last 5 families include feature-family (3x), feature-family
  + risk-primitive (1x), and validation (1x). Not all 5 same family. Rotation discipline honored.
- **Justification**: /050 PROMISING-PARTIAL mandate from brief Section 3.5 Rec 3 ADOPTED
  CONDITIONAL pre-registration (binding): "if /050 verdict ∈ {PROMISING-SPECIALIST,
  PROMISING-PARTIAL}, /051 OR /054 MUST be multi-seed re-validation." /050 hit PROMISING-PARTIAL.
  /051 fires the mandated multi-seed validation at the next available iteration slot.

---

## Section 1 — Hypothesis

Multi-seed mean DOT IS Sharpe Δ across 4 outer seeds confirms that /050's PROMISING-PARTIAL
lift (+1.1162 IS Δ) is reproducible across seed randomization, not a single-seed lottery
artifact — specifically, that `dot_vs_btc_ret_ratio_30` (importance rank 8/45 at seed=42)
is genuinely learned by the DOT-only LightGBM head regardless of inner ensemble seed draw.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 Prior Evidence (iter-v1/050 IS results — load-bearing anchor)

From `reports-v1/iteration_v1-050/` (committed; IS data only per OOS_CUTOFF discipline):

| Metric | iter-v1/050 (seed=42) | BASELINE_V1 DOT |
|---|---:|---:|
| DOT IS Sharpe | -0.1138 | -1.23 |
| DOT IS Δ | **+1.1162** | — |
| IS trades | 125 | 93 |
| IS win rate | 46.4% | 41.9% |
| IS MaxDD | 21.36% | 64.29% |
| dot_vs_btc_ret_ratio_30 importance rank | 8/45 | N/A |
| Vol-spike regime gate IS fire rate | **0%** (INERT) | N/A |

**Key finding from /050**: the +1.1162 IS Sharpe Δ is entirely feature-attributed (gate 0% fire
rate → gate mechanically INERT). Feature importance rank 8/45 (top-15 PASS) confirms genuine
learning. Single-seed=42 lottery risk (DOT cohort: 93 IS trades / small n_eff per fold) is the
binding concern per LM Master Rec 3.

### 2.2 EDA Artifact

EDA artifact mirrors `analysis/iteration_v1-050/eda.py` (same feature `dot_vs_btc_ret_ratio_30`
— no new feature at /051). Script `analysis/iteration_v1-051/eda.py` authored for gate
completeness; produces the same ADF p-value + IC stats as /050 (informational; IS-only; NOT
blocking per EDA informational rule per `bf2c812`/`a6269df`).

Committed script path: `analysis/iteration_v1-051/eda.py`.

---

## Section 2.5 — HIGH-RISK Axis Declaration

- **Risk level**: **NORMAL-RISK**
- Reasoning: No change to the Optuna training-objective domain. Seed variation (inner ensemble
  seed offset) changes the random state of the inner ensemble members but NOT what Optuna
  optimizes (objective = Sharpe on triple-barrier labels, unchanged). Dropping the inert gate
  (which never fired at 0% IS rate) has no training-objective effect. NORMAL-RISK; no multi-seed
  mitigation beyond what /051 itself is already executing.

---

## Section 3 — Proposed Changes

### 3.1 Drop Vol-Spike Regime Gate (inert post-prediction filter)

The vol-spike regime gate from /050 (skip DOT signal if `btc_realized_vol_30 > q75_IS AND
pred_proba < 0.55`) fired at **0% IS / 0% OOS** — mechanically INERT. The gate logic added
complexity without effect. /051 removes it.

**Implementation**: Add `V1_ITER051_UNIVERSE` dispatch block to `run_baseline_v1.py` with:
- Same DOT-only cohort (`{"DOTUSDT"}`)
- Same `V1_FEATURE_COLUMNS_PRUNED` (46 cols; `dot_vs_btc_ret_ratio_30` included, unchanged)
- Same Model E semantics: R1=ON, R2=ON, R3=ON, atr_tp=3.5, atr_sl=1.75
- Same n_trials=18, ENSEMBLE_SIZE=3
- **NO vol-spike regime gate** (zero gate logic in dispatch block)

### 3.2 Multi-Seed Validation: --seeds 4

Pass `--seeds 4` to `run_baseline_v1.main()`. The framework executes:
- Outer seed 0 (offset=0) → inner seeds [42, 123, 456] → `seed_42/` (canonical; matches /050
  deterministic baseline for sanity check)
- Outer seed 1 (offset=5) → inner seeds [2002, 3003, 4004] → `seed_offset5/`
- Outer seed 2 (offset=10) → inner seeds [5005, 6006, 42] (wraps: offset+size may exceed 10)
  → `seed_offset10/`
- Outer seed 3 (offset=15) → inner seeds from ENSEMBLE_SEEDS[15:18] (if available; framework
  caps at `len(ENSEMBLE_SEEDS)`) → `seed_offset15/`

Note: the framework offsets 5, 10, 15 select different windows of the ENSEMBLE_SEEDS roster
`(42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006)`. The goal is 4 statistically
independent outer-seed draws to measure IS Sharpe Δ variance. The framework handles the
sub-run dispatch and aggregation automatically.

### 3.3 LM Master Response Map (from /050's lgbm_advisor.md Rec 3)

**Rec 3 — Single-seed=42 lottery risk; pre-register multi-seed validation**
**Status: ADOPTED EXECUTION** (Rec 3 ADOPTED CONDITIONAL at /050 brief Section 3.5; /051 is
the execution leg of that conditional adoption.)

LM Master's Rec 3 mandated: "if /050 verdict ∈ {PROMISING-SPECIALIST, PROMISING-PARTIAL},
/051 OR /054 MUST be multi-seed re-validation." /050 hit PROMISING-PARTIAL (IS Δ +1.1162).
/051 is the immediate execution, applying seeds [offset=0,5,10,15] per framework convention.

---

## Section 4 — Expected OOS Impact (F-AXIS Falsifiers)

| F-AXIS | Threshold | Verdict band |
|---|---|---|
| **F1** multi-seed mean IS Δ | ≥ +1.23 → PROMISING-SPECIALIST-CONFIRMED | DOT enters /055 CONFIRMATION roster unconditionally |
| **F1** multi-seed mean IS Δ | +0.50 ≤ mean Δ < +1.23 → PROMISING-PARTIAL-CONFIRMED | DOT roster entry conditional on /055 design |
| **F1** multi-seed mean IS Δ | < +0.50 → LOTTERY-CONFIRMED-NEGATIVE | REVERT: remove `dot_vs_btc_ret_ratio_30` from V1_FEATURE_COLUMNS_PRUNED (46 → 45 cols); DOT NOT in roster |
| **F2** trade-rate floor | mean IS ≥ 50 AND mean OOS ≥ 10 (both must hold) | FAIL → forced downgrade one band |
| **F3** multi-seed stability | max(per-seed IS Δ) - min(per-seed IS Δ) ≤ +1.0 | PASS; else BASIN-LOTTERY |
| **F4** IS MaxDD (regression check) | mean IS MaxDD ≤ 80% | PASS; else REGRESSION-WARNING |
| **F5** seed=42 sanity | /051 seed=42 run IS Sharpe ≈ /050 IS Sharpe within ±0.10 | PASS; divergence > ±0.10 = IMPLEMENTATION-ERROR |

**OOS forensic**: OOS Δ reported informational only per /046 PROMISING-DIVERGENCE discipline.
Not a /051 success criterion. Reported in closeout for pattern recognition.

---

## Section 5 — Risk Mitigation

Same R1+R2+R3 stack as /050 and BASELINE_V1 Model E (DOT):
- R1 consecutive-SL cool-down (K=3, C=27 candles) — active for DOT
- R2 drawdown-triggered position scaling (trigger=7%, anchor=15%, floor=0.33) — active for DOT
- R3 OOD Mahalanobis gate (cutoff=0.70, 16 scale-invariant features) — active for DOT

**Change from /050**: vol-spike regime gate DROPPED (was 0% fire rate / INERT; Section 3.1).
Multi-seed IS Δ mean is the load-bearing statistic; stability check (F3) catches basin-lottery.

---

## Section 6 — Risk Management Design

| Primitive | Status | Notes |
|---|---|---|
| Vol-adjusted sizing (R2) | ACTIVE | trigger=7%, anchor=15%, floor=0.33 |
| ADX gate | NOT ACTIVE | axis CLOSED in v3; not used in v1 |
| Hurst regime | via composed feature | regime_momentum_signed_5d uses hurst_100 in V1_FEATURE_COLUMNS_PRUNED |
| Z-score OOD (R3) | ACTIVE | Mahalanobis, cutoff=0.70, 16 features |
| Drawdown brake (R2) | ACTIVE | same as above |
| BTC contagion | via cross-asset feature | dot_vs_btc_ret_ratio_30 encodes BTC idiosyncratic signal |
| Vol-spike regime gate | **DROPPED** | was 0% fire rate (INERT) at /050; removed to simplify; no IS effect expected |
| Liquidity floor | NOT ACTIVE | DOTUSDT is liquid Binance Futures perp |

Multi-seed mean IS Δ is the load-bearing statistic. No new risk primitives added.

---

## Section 7 — Failure-Mode Prediction

**Modal failure (LOTTERY-CONFIRMED-NEGATIVE, ~35% prior)**: /050's +1.1162 IS Δ was a
favorable basin draw at seed=42. DOT's small cohort (93 BASELINE IS trades → 125 at /050)
means each CV fold has ~7-15 effective signals — a handful of correctly-timed DOT trades at
seed=42 can inflate apparent Sharpe. If the other 3 outer seeds land in unfavorable basins,
the mean IS Δ falls below +0.50 → LOTTERY-CONFIRMED-NEGATIVE → revert feature. This is the
most dangerous outcome because it unwinds the 46-col feature set.

**Second most likely (PROMISING-PARTIAL-CONFIRMED, ~45% prior)**: the feature's information
content is real but moderate. The seed=42 canonical run happens to capture DOT's partial
idiosyncratic-alpha regime in IS particularly well; other seeds see the same partial lift at
lower magnitude. Mean IS Δ lands in [+0.50, +1.23) → confirms PARTIAL, triggers F1-PARTIAL
verdict for /055 design. Feature retained.

**Least likely (PROMISING-SPECIALIST-CONFIRMED, ~10% prior)**: all 4 outer seeds produce
consistent IS Δ ≥ +1.23 lift (DOT flips fully positive across all seeds). Would indicate
`dot_vs_btc_ret_ratio_30` is a robust signal, not basin-specific. Unlikely given DOT's small
cohort and the observed /050 IS Sharpe of -0.1138 (still negative; near but not above zero).

**What gates should catch**: F3 stability (max-min ≤ +1.0) catches BASIN-LOTTERY directly.
F5 sanity (seed=42 ≈ /050 within ±0.10) catches implementation errors.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

All thresholds declared before backtest runs; cannot be post-hoc renegotiated.

### 8.1 Primary Verdict (multi-seed mean IS Δ)

DOT baseline IS Sharpe = **-1.23** (BASELINE_V1.md). Mean IS Δ = mean across all 4 outer seeds
of (per-seed DOT IS Sharpe) minus (-1.23).

| Verdict | Condition |
|---|---|
| **PROMISING-SPECIALIST-CONFIRMED** | mean IS Δ ≥ +1.23 (multi-seed mean DOT IS Sharpe ≥ 0) |
| **PROMISING-PARTIAL-CONFIRMED** | +0.50 ≤ mean IS Δ < +1.23 |
| **LOTTERY-CONFIRMED-NEGATIVE** | mean IS Δ < +0.50 |

### 8.2 Trade-Rate Floor (mandatory gating)

- **PASS**: mean IS trades ≥ 50 AND mean OOS trades ≥ 10.
- **FAIL**: either below floor → downgrade one band (SPECIALIST → PARTIAL; PARTIAL → NEG).

### 8.3 Multi-Seed Stability (BASIN-LOTTERY classification)

- **PASS**: max(per-seed IS Δ) - min(per-seed IS Δ) ≤ +1.0.
- **FAIL → BASIN-LOTTERY**: spread > +1.0 means the feature signal is lottery-dependent;
  even a PARTIAL mean may be overfit to favorable basins. Record in closeout as BASIN-LOTTERY
  sub-classification; downgrade one additional band.

### 8.4 IS MaxDD Regression Check

- **PASS**: mean IS MaxDD ≤ 80%.
- **WARNING**: mean IS MaxDD > 80% flagged as REGRESSION; does not downgrade verdict.

### 8.5 Seed=42 Sanity Check (implementation verification)

- /051 outer-seed=42 run (offset=0) must produce DOT IS Sharpe within ±0.10 of /050's
  IS Sharpe (-0.1138). Divergence > ±0.10 = IMPLEMENTATION-ERROR; abort and investigate
  before recording a verdict.

### 8.6 REVERT Trigger

If verdict = LOTTERY-CONFIRMED-NEGATIVE: revert `dot_vs_btc_ret_ratio_30` from
V1_FEATURE_COLUMNS_PRUNED (46 → 45 cols). DOT NOT added to /055 CONFIRMATION roster.
Revert committed in /051 closeout commit as `feat(iter-v1/051): REVERT feature`.

---

## Section 9 — Library Stack Declaration

No new dependencies vs BASELINE_V1 or /050.

| Component | Version | Source |
|---|---|---|
| Python | 3.13 | system / pyproject.toml |
| lightgbm | existing pin | .venv (from `pyproject.toml`) |
| scipy | existing pin | .venv (compute / stats) |
| pandas | existing pin | .venv (feature merge + rolling) |
| numpy | existing pin | .venv (arithmetic + clipping) |
| stdlib | 3.13 builtin | `csv`, `math`, `datetime` |

No NEW pip / uv adds. No version bumps. No alternative ML frameworks. The multi-seed framework
(--seeds 4) is implemented in `run_baseline_v1.py` (framework/032+) — no new dependencies.

---

## Section 10 — Regime Attribution Plan

Per-seed regime tagging: all 4 outer seeds will produce `per_regime.csv` (all trades tagged
"unknown" — regime tagger not wired in v1). Mean per-seed IS Sharpe is the load-bearing metric.

If regime tagger is available in future iterations, the regime attribution plan is:
- vol-low regime: mean IS Δ per seed
- vol-high regime: mean IS Δ per seed
- Compare to BASELINE_V1 DOT per-regime profile

At /051: regime analysis is informational only. Mean across seeds is the primary statistic.

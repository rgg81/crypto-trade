# iter-v1/015 — Research Brief (FIRST CYCLE-2 CONFIRMATION)

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: **CONFIRMATION** (multi-seed; ENSEMBLE_SIZE=10 inner, n_trials=35, 6h cap)
**Axis**: triple-barrier σ_t source — past-only EWMA at 14-day half-life (k_tp=1.06, k_sl=0.53) — **C1 FIX MANDATORY**: execution-time barriers also dispatched through σ_t × k × √timeout (completes the labeling axis; not a 2nd axis)
**Branch**: `iteration-v1/015` (forked from `iteration-v1/014` HEAD `42aeed0`, tag `v0.v1-014`)

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor

`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)
- UNCHANGED since baseline (all /001 through /014 closed; /001 PROMISING-METHODOLOGY non-compoundable; /002-/014 NEGATIVE)
- **/015 is the FIRST opportunity in cycle-2 to update BASELINE_V1.md per `feedback_v3_baseline_update_policy.md`** (user directive 2026-05-25)

### 0.2 Mode

**CONFIRMATION** (cycle-2 #10 of 10; PRE-COMMITTED BINDING per /013 + /014 closeouts)
- `--confirmation --iteration 15 --pruned-features --n-trials 35`
- ENSEMBLE_SIZE = 10 (canonical v1 CONFIRMATION inner seeds; `[42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]`)
- `--label-sigma-source ewma14d --label-sigma-k-tp 1.06 --label-sigma-k-sl 0.53 --label-sigma-halflife-days 14`
- R5-BINARY-KILL DISABLED (axis isolation — labeling is THE axis; R5 family CLOSED at v1 single-seed per /011-/013 catalog)
- **C1 FIX MANDATORY** (NEW from /014 mandate): `lgbm.py:905-915` must dispatch on `self.sigma_source`. When `ewma14d`, both label-time AND execution-time barriers use σ_t × k × √timeout
- **6h wall-clock cap** (CONFIRMATION canonical per `feedback_v3_cadence_discipline.md`)

### 0.2bis Spec Disambiguation — User Directive Notation

User directive at /015 launch: `--seeds 10 --n-trials 35 --ensemble-size 5 --pruned-features --label-sigma-source ewma14d`.

**v1 architecture is single-pass**: no outer seed loop. `--ensemble-size N` selects N inner seeds; there is no `--seeds` flag in `run_baseline_v1.py` (confirmed by argparse audit at `run_baseline_v1.py:734-868`). The v3-style "outer × inner" terminology does not apply to v1.

**Adopted interpretation** (canonical v1 CONFIRMATION per BASELINE_V1.md §"Ensemble seeds (for FUTURE iter-v1/NNN)"): `--confirmation --ensemble-size 10`. This selects the full 10-seed roster `[42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]` in single-pass — the canonical v1 CONFIRMATION inner ensemble.

The user-directive `--ensemble-size 5` line is interpreted as a notational conflict with `--seeds 10`. Per BASELINE_V1.md the canonical CONFIRMATION inner-ensemble is 10 seeds; per /014 LM Master Phase 4.5 §5 the multi-seed CONFIRMATION SE prediction was calibrated at 10 seeds (SE ≈ 0.25). Adopting 10 inner seeds preserves both. **If user wants 5 inner seeds, this can be downgraded with one CLI change (`--ensemble-size 5`) before dispatch — flagged here for review at Phase 5.5 / 6.0.**

### 0.3 Iteration label

`v1-015`

### 0.4 Determinism note

Inner seeds at canonical CONFIRMATION roster `[42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]` (offset=0; full 10-seed window). The `--label-sigma-source ewma14d` flag activates the EWMA σ_t labels AT BOTH label-time AND execution-time (per C1 FIX) — see Section 3.

R5-BINARY-KILL and R5 proportional vol-target are OMITTED (default disabled per runner; axis isolation — /015 tests labeling AT MULTI-SEED, not R5). `ensemble_seeds_offset=0` (default).

### 0.5 Cadence position

**Cycle-2 CONFIRMATION #10 of 10**. FIRST CYCLE-2 CONFIRMATION.

Cycle-2 EXPLORATION precedents (9 of 10; PRE-COMMITTED that /015 occupies the CONFIRMATION slot per /013 + /014 HIGH-RISK mitigation):

| Iteration | Family | Verdict |
|---|---|---|
| iter-v1/006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| iter-v1/007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| iter-v1/008 | methodology | EXPLORATION-PROMISING-METHODOLOGY (non-compoundable; n_eff PCA per-cell median) |
| iter-v1/009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| iter-v1/010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| iter-v1/011 | risk-primitive (binary-kill) | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| iter-v1/012 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) |
| iter-v1/013 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC) |
| iter-v1/014 | **labeling** | EXPLORATION-NEGATIVE (Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM + C1 CONFOUND) |

10:1 cadence discipline satisfied: 9 EXPLORATION precedents in cycle-2 + the HIGH-RISK pre-commit binding declared at /014 fills the 10th CONFIRMATION slot (per `feedback_v3_cadence_discipline.md` plus `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL retraction + /014 mandate). **/015 IS the CONFIRMATION position by HIGH-RISK pre-commit; no separate /015 EXPLORATION needed**.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: **`labeling`** (CONFIRMATION-spec, NOT new family)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/010: `risk-primitive`
  - iter-v1/011: `risk-primitive`
  - iter-v1/012: `methodology-substrate-test`
  - iter-v1/013: `methodology-substrate-test`
  - iter-v1/014: `labeling`
- **Rotation status**: **N/A** — CONFIRMATION is not a NEW EXPLORATION (axis rotation discipline applies to EXPLORATION sequence; CONFIRMATION validates the most recent labeling EXPLORATION at multi-seed). The Axis Rotation Discipline rule fires on EXPLORATION sequences only.
- **One-sentence rationale**: /015 validates the σ_t labeling axis (/014's EXPLORATION-NEGATIVE Cell-5) at multi-seed dissolution with the C1 FIX applied — the experiment is finally well-posed; this is the canonical v1 CONFIRMATION pattern (test the most-promising recent EXPLORATION axis at full statistical rigor).

### 0.7 — CONFIRMATION Bundle Composition (NEW for /015)

What is included from prior EXPLORATIONs in the /015 CONFIRMATION bundle:

| Source | Component | Status |
|---|---|---|
| **iter-v1/001** | methodology layer (PSR × 3 + N_eff-corrected DSR + ADF + IC + dsr.json + cpcv_paths.csv) | **INHERITED** — already in `comparison.csv` schema; non-compoundable per /001 PROMISING-METHODOLOGY subtype but provides the measurement substrate. Validates the OOS Sharpe + DSR + PSR + PBO numbers at /015. |
| **iter-v1/008** | n_eff PCA per-cell median computation | **INHERITED** — provides the F-AXIS-MECHANISM falsifier substrate (n_eff = 19 at /014 single-seed must replicate ≥17 at ≥7/10 seeds in /015). |
| **iter-v1/014** | **σ_t labeling axis (PRIMARY)** — past-only EWMA σ_t at 14-day half-life + k_tp=1.06, k_sl=0.53 + C1 FIX (execution-time barriers ALSO dispatch on σ_t when `sigma_source="ewma14d"`) | **PRIMARY axis under test**. /014 ran with C1 unresolved (label-time σ_t × execution-time NATR); /015 completes the axis with symmetric implementation. |
| /002-/007, /009-/013 | EXPLORATION-NEGATIVE (R5 family, feature-family changes, methodology probes) | **NOT BUNDLED** — all axis-CLOSED at v1 single-seed catalog. |

**/015 is NOT a bundle of multiple edge ingredients** (unlike v3 CONFIRMATIONs that aggregate multiple PROMISING components). v1 cycle-2 produced exactly ONE PROMISING-METHODOLOGY component (/001, non-compoundable as measurement-substrate) and the labeling axis (/014, NEGATIVE single-seed with C1 CONFOUND). /015 = labeling-axis multi-seed-validation with C1 FIX. The bundle is one axis-PLUS-its-completion, not multi-component composition.

---

## Section 1 — Hypothesis

**At v1 CONFIRMATION budget (n_trials=35 + ENSEMBLE_SIZE=10 + V1_FEATURE_COLUMNS_PRUNED + R5 DISABLED + C1 FIX APPLIED), the past-only EWMA σ_t × k labeling axis at 14-day half-life with symmetric label-time AND execution-time dispatch produces a multi-seed mean OOS Sharpe Δ vs BASELINE_V1 within band [-0.30, +0.30] with high confidence and within band [-0.10, +0.20] modal expectation. Per LM Master /014 Phase 7.4 §6 calibration (UPDATED post-/014): 55% NULL / 20% PROMISING / 25% NEGATIVE.**

Three concrete falsifiable claims:

1. **F1-MULTI (OOS Sharpe Δ multi-seed mean)**: modal expectation Δ ∈ [-0.10, +0.20] (NULL/marginal-positive band; 55% probability). PROMISING band Δ ∈ [+0.20, +0.55] (20% probability; triggers BASELINE_V1 update if Pareto + IS both PASS). NEGATIVE band Δ < -0.10 (25% probability; closes labeling axis at multi-seed budget).

2. **F-AXIS-C1 (programmatic axis-completion falsifier)**: execution-time barrier matches label-time within 1e-6 tolerance for all IS candles. Binary PASS/FAIL. If FAIL → BLOCK-PENDING-FIX rerun (single rerun chance per v1 skill discipline); after rerun, verdict can only be PASS or BLOCK-FINAL.

3. **F-AXIS-MECHANISM (multi-seed n_eff replication)**: n_eff_per_cell_median ≥ 17 across at least 7 of 10 outer seeds. If <7/10 → loss-surface diversification was single-seed artifact (unlikely; n_eff bound by label-distribution shape which is seed-independent).

### Why this is the right experiment NOW (cycle-2 CONFIRMATION position)

Three structural reasons:

1. **PRE-COMMITTED BINDING**: per /013 Critic Phase 7.5 Path Forward Option 1 + LM Master /013 Phase 7.4 §6 + /014 brief Section 11 + /014 diary item #7 + /014 Critic Phase 7.5 Rec #1 (C1 fix mandate). The /015 = labeling CONFIRMATION binding regardless of /014 magnitude is the HIGH-RISK pre-commit mitigation; the pre-commit fired correctly at /014's catastrophic basin draw.

2. **EXPERIMENT FINALLY WELL-POSED**: /014 measured a CONFOUNDED experiment (label-time σ_t × execution-time NATR; C1 asymmetry produced LTC windfall + BTC/ETH penalty as per LM Master Phase 7.4 §3). /015 with C1 FIX is the FIRST well-posed test of the σ_t labeling axis at v1 budget.

3. **MULTI-SEED DISSOLVES BASIN LOTTERY**: per `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision and LM Master /014 §6, at v1 single-seed EXPLORATION the basin lottery (±0.80 std) dominates F1/F3 measurement. At 10-seed CONFIRMATION the multi-seed SE is ≈ 0.25 — narrow enough to distinguish edge from noise. /015 is the FIRST CONFIRMATION measurement of labeling at this rigor.

---

## Section 2 — IS-Only Evidence (mostly inherited from /014)

EDA from /014 stands; /015 inherits the calibration computed at `analysis/iteration_v1-014/sigma_calibration.py` and `analysis/iteration_v1-014/regime_barrier_analysis.py` (committed at `cafad3d`). No new EDA needed for /015 because:

1. **σ_t calibration is identical to /014**: k_tp=1.06, k_sl=0.53, halflife=14 days. Numbers unchanged.
2. **C1 FIX changes the EXECUTION-TIME barrier path** — this is a code-side modification, not a calibration change. The σ_t calibration values are reused.
3. **The well-posed experiment** (/015 with C1 FIX) is what tests the labeling axis; the EDA already calibrated the axis.

### 2.1 Reference: /014 EDA recap (numerical tables inherited from /014 brief)

Per-symbol σ_t (decimal log-return std, half-life=42 candles):

| Symbol | n_IS | σ_t p10 | σ_t p25 | σ_t p50 | σ_t p75 | σ_t p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 5707 | 0.00930 | 0.01233 | 0.01607 | 0.02123 | 0.02873 |
| ETHUSDT | 5707 | 0.01163 | 0.01587 | 0.02070 | 0.02710 | 0.03517 |
| LINKUSDT | 5658 | 0.01581 | 0.02184 | 0.02930 | 0.03922 | 0.05082 |
| LTCUSDT | 5667 | 0.01278 | 0.01791 | 0.02496 | 0.03402 | 0.04611 |
| DOTUSDT | 5005 | 0.01521 | 0.02112 | 0.02839 | 0.03762 | 0.04959 |

Calibrated portfolio-mean k values: **k_tp = 1.06, k_sl = 0.53** (per-symbol-median alternative would shift barriers 5-6% tighter for BTC/ETH; ADOPTED unchanged at /015 — axis isolation).

### 2.2 NEW evidence from /014 outcome (informing /015 expectations)

From `reports-v1/iteration_v1-014/comparison.csv`:

| Metric | /014 single-seed | BASELINE_V1 5-seed | Δ |
|---|---|---|---|
| IS Sharpe | -0.6112 | +0.2829 | **-0.8941** (catastrophic) |
| OOS Sharpe | +0.1828 | +0.6637 | **-0.4809** (NEGATIVE band) |
| IS Trades | 598 | 621 | -23 (F8-NEW PASS) |
| OOS Trades | 202 | 189 | +13 |
| **n_eff per-cell median** | **19** | 13 | **+6 (+46% durable mechanism diversification)** |
| F7-NEW per-symbol direction match | 4/5 | — | PARTIAL (ETH deviant via C1) |

**Key inputs for /015 expectations**:
- /014 single-seed catastrophic IS (-0.89 Δ) was C1-amplified (LTC windfall + BTC/ETH penalty pattern). C1 FIX at /015 removes the asymmetric amplification.
- n_eff 13→19 is the DURABLE mechanism finding — independent of basin direction; multi-seed should replicate.
- F7-NEW 4/5 PARTIAL → mechanism 80% functional at single-seed; ETH deviation is C1 signature.

### 2.3 Multi-Seed Variance Estimate (informing F1-MULTI band)

Per LM Master /014 Phase 7.4 §6 + `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision:

- v1 single-seed Sharpe-Δ std ≈ 0.80 (observed empirically across /010-/014 with R5-BINARY-KILL DISABLED comparisons)
- 10-seed mean SE ≈ 0.80 / √10 ≈ 0.25
- **Predicted multi-seed mean F1 (OOS Sharpe Δ vs BASELINE_V1) at /015 with C1 FIX**: modal NULL Δ ∈ [-0.10, +0.20] (NULL band centered on 0; with C1 FIX removed the per-symbol asymmetry, the basin no longer systematically penalizes BTC/ETH on a portfolio level)
- **Tail bands**: PROMISING Δ ∈ [+0.20, +0.55] requires the σ_t labels to capture genuine edge AT MULTI-SEED beyond mechanical confound removal. NEGATIVE Δ < -0.10 means the labeling axis hurts even at multi-seed with C1 FIXED — closes the axis decisively.

### 2.4 Per-Symbol IS+OOS /014 Decomposition (for /015 attribution prior)

From `reports-v1/iteration_v1-014/comparison.csv` per-symbol attribution:

| Symbol | IS net PnL | OOS net PnL | /014 pattern (C1-confounded) |
|---|---|---|---|
| LTC | **+95.51** | **+24.49** | C1 WINDFALL (tighter σ_t labels + wider NATR execution) |
| LINK | -9.79 | +3.87 | mild IS, OOS positive |
| BTC | -24.25 | +5.70 | mild IS C1 PENALTY (wider σ_t labels + tighter NATR execution) |
| DOT | -88.74 | +10.43 | catastrophic IS LOSER (rotates across cycle-2) |
| ETH | -99.73 | -41.18 | largest IS C1 PENALTY (wider σ_t labels + tighter NATR execution) |
| **Portfolio** | -126.99 | +3.31 | OOS net PnL POSITIVE despite Sharpe negative (ETH variance drag) |

**Expected /015 attribution shift** (with C1 FIX):
- LTC: C1 WINDFALL DISAPPEARS — per-symbol IS+OOS likely DOWN from /014 magnitudes
- BTC + ETH: C1 PENALTY REMOVED — per-symbol IS+OOS likely UP from /014 magnitudes
- Portfolio: depends on whether the WINDFALL or PENALTY removal dominates AT MULTI-SEED
- Direction unconstrained — modal NULL because the removals partially cancel

This is a CONFIRMATION attribution prior, not a verdict. The basin lottery is dissolved at multi-seed; the remaining edge or non-edge is what /015 measures.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK** (CONFIRMATION-mode; multi-seed by design — does not carry HIGH-RISK single-seed lottery semantics)
- **Reason**: HIGH-RISK declaration applies to EXPLORATION-mode single-seed-window iterations where the basin draw at single-seed can produce ±0.80 std verdict-class draws. CONFIRMATION at ENSEMBLE_SIZE=10 dissolves the basin lottery by design (SE ≈ 0.25). The HIGH-RISK semantics from `feedback_v1_substrate_basin_lock.md` REFUTED-IN-FULL revision do NOT apply at CONFIRMATION budget.
- **HIGH-RISK pre-commit (from /014) status**: FIRED CORRECTLY at /014's catastrophic basin draw. /015 IS the binding mitigation; this is the mitigation firing, not a new HIGH-RISK declaration.

### Why NORMAL-RISK for /015

Three structural reasons CONFIRMATION is NOT HIGH-RISK:

1. **Multi-seed dissolution**: 10 inner seeds × 35 trials × 5 symbols × 24 months produces statistical resolution at 0.25 OOS Sharpe SE. The single-seed lottery (±0.80) is dissolved by averaging across the seed roster.

2. **C1 FIX completes the axis**: the experimental confound from /014 is removed by definition. /015 measures the well-posed labeling axis, not a confounded one.

3. **BASELINE_V1 update is by user policy, not by HIGH-RISK fallback**: per user directive 2026-05-25 + `feedback_v3_baseline_update_policy.md`, CONFIRMATION updates BASELINE_V1.md if STRICTLY-BETTER on BOTH IS+OOS multi-seed mean AND both Pareto seeds positive. This is a STRUCTURED outcome (defined in Section 7), not an open-ended bet.

---

## Section 3 — Proposed Changes (Implementation Spec)

### 3.1 C1 FIX (PRIMARY MANDATE; completes labeling axis)

**`src/crypto_trade/strategies/ml/lgbm.py` lines 905-915** (currently always uses NATR; needs dispatch on `self.sigma_source`):

CURRENT (`lgbm.py:905-915` per Bash audit):
```python
# Compute dynamic TP/SL from ATR if configured
tp_pct = None
sl_pct = None
if self.atr_tp_multiplier is not None:
    natr = self._month_natr.get(key)
    if natr is not None and natr > 0:
        tp_pct = natr * self.atr_tp_multiplier
        sl_pct = natr * (
            self.atr_sl_multiplier
            if self.atr_sl_multiplier is not None
            else self.atr_tp_multiplier / 2.0
        )
```

REQUIRED at /015 (NEW dispatch path — full QE pseudo-code; final implementation by QE):
```python
# Compute dynamic TP/SL: dispatch on sigma_source.
# - "natr" path: BIT-IDENTICAL to current behavior (backward compatible)
# - "ewma14d" path: σ_t × k_tp/k_sl × √timeout × 100 (C1 FIX — execution-time
#   barriers match label-time scheme; completes the labeling axis per /014
#   Critic Phase 7.5 Rec #1 + LM Master Phase 7.4 §7)
tp_pct = None
sl_pct = None
if self.sigma_source == "ewma14d":
    # C1 FIX: execution-time barriers ALSO use σ_t × k × √timeout
    sigma = self._month_sigma.get(key)  # per-month σ_t cached at training time
    if sigma is not None and sigma > 0 and self.sigma_k_tp is not None and self.sigma_k_sl is not None:
        timeout_candles = self.label_timeout_minutes / (8 * 60)  # 8h candles
        sqrt_timeout = float(np.sqrt(timeout_candles))
        tp_pct = float(sigma * self.sigma_k_tp * sqrt_timeout * 100.0)
        sl_pct = float(sigma * self.sigma_k_sl * sqrt_timeout * 100.0)
elif self.atr_tp_multiplier is not None:
    natr = self._month_natr.get(key)
    if natr is not None and natr > 0:
        tp_pct = natr * self.atr_tp_multiplier
        sl_pct = natr * (
            self.atr_sl_multiplier
            if self.atr_sl_multiplier is not None
            else self.atr_tp_multiplier / 2.0
        )
```

**Companion changes** (QE responsibility per `lgbm.py` modification scope):
1. **`_train_for_month()`** must populate `self._month_sigma` for each `(symbol, open_time)` test-month-first-candle key — mirrors the existing `_month_natr` population at `lgbm.py:740-753`. The σ_t value at the test-month-first-candle is read from the already-computed `self._label_sigma_values` array indexed by master row.
2. **`__init__`** must initialize `self._month_sigma: dict[tuple[str, int], float] = {}` alongside `self._month_natr` (line ~280).
3. **`verbose` log line at line ~922** should display the σ_t-derived TP/SL when `sigma_source="ewma14d"` (informational; does NOT change behavior).

### 3.2 Engineering Report Runner HARD-STOP (4th-strike codification per /014 Critic Rec #2)

**`run_baseline_v1.py:1217-1229`** (currently emits `[WARNING]`; needs hard exit):

CURRENT:
```python
engineering_report_path = report_dir / "engineering_report.md"
if not engineering_report_path.exists():
    print(
        "\n[run_baseline_v1] WARNING: engineering_report.md NOT FOUND at "
        f"{engineering_report_path}\n"
        "  This file is a BLOCKING deliverable for Phase 7.5 dispatch.\n"
        "  Orchestrator MUST create it before invoking the Critic.\n"
        "  Phase 7.5 hard-reject applies: do NOT invoke quant-critic without it."
    )
```

REQUIRED at /015:
```python
engineering_report_path = report_dir / "engineering_report.md"
if not engineering_report_path.exists() and not args.no_engineering_report:
    print(
        f"\n[FATAL] engineering_report.md NOT FOUND at {engineering_report_path}",
        file=sys.stderr,
    )
    print(
        "[FATAL] This file is a BLOCKING deliverable for Phase 7.5 dispatch.\n"
        "[FATAL] Use --no-engineering-report to override (e.g. mid-pipeline orchestration).",
        file=sys.stderr,
    )
    sys.exit(1)
```

**Companion changes**:
1. **`--no-engineering-report`** boolean flag added to argparse (default False; opt-in override for explicit acknowledgment of QE-side defects).
2. Phase 6.0 Critic pre-flight at /015 MUST verify both the code change AND the argparse flag presence before backtest dispatches.

### 3.3 F-AXIS-C1 programmatic falsifier (NEW; required by /014 Critic Rec)

A new programmatic test in `tests/test_lgbm.py` (sibling to existing tests):

```python
def test_sigma_source_ewma14d_execution_barrier_consistency():
    """
    F-AXIS-C1 (CONFIRMATION at /015): When sigma_source="ewma14d", the
    execution-time TP/SL distance computed at predict() MUST match the
    label-time TP/SL distance computed at label_trades() within 1e-6
    tolerance for all IS candles.

    Test: synthesize a 200-row master, train at sigma_source="ewma14d",
    iterate over the test-month roster, verify TP/SL distances at predict()
    match σ_t × k × √timeout × 100 for the test-month-first-candle σ_t.
    """
    # full test body specified in QE Phase 6 deliverables
```

Per `feedback_v3_methodology_axis_integration_test.md`-style mandate: unit test on math AND end-to-end smoke test (single-symbol synthetic; verify trades.csv TP/SL distance equals σ_t × k × √timeout × 100 within float tolerance).

### 3.4 F-AXIS-MECHANISM multi-seed n_eff falsifier (NEW)

No code change required; this is a post-run assertion at Phase 7. The runner already emits `n_effective_trials` per row in `comparison.csv` and `dsr.json` per-seed (verified at /014 dsr.json: BTC=20, ETH=20, LINK=18, LTC=18, DOT=19). At /015 multi-seed, the per-seed dsr.json values are aggregated; the engineering report Section 5 will compute "fraction of 10 outer seeds with n_eff_per_cell_median ≥ 17".

### 3.5 Runner invocation (/015 dispatch)

```bash
uv run python run_baseline_v1.py \
    --confirmation \
    --iteration 15 \
    --pruned-features \
    --n-trials 35 \
    --label-sigma-source ewma14d \
    --label-sigma-k-tp 1.06 \
    --label-sigma-k-sl 0.53 \
    --label-sigma-halflife-days 14
```

`--confirmation` resolves to ENSEMBLE_SIZE=10 + iteration_label=`v1-015` + reports_dir=`reports-v1`. R5-BINARY-KILL and R5 proportional vol-target OMITTED (default disabled). The C1 FIX is invariant at runtime — `lgbm.py:905-915` dispatches on `self.sigma_source="ewma14d"` automatically.

### 3.6 Expected wall-clock budget

Per BASELINE_V1.md §"Wall-clock (5-seed ENSEMBLE)": 7h 0m for 5-seed baseline. At /015 ENSEMBLE_SIZE=10 (2× seeds) + n_trials=35 vs baseline's 50 trials, predicted wall-clock:
- 5-seed baseline at n_trials=50: 7.0h
- Scale to 10-seed: × 2.0 = 14.0h
- Scale n_trials 50→35: × 35/50 = 9.8h
- **/015 predicted wall-clock: ~9.8h**

This EXCEEDS the 6h CONFIRMATION cap from `feedback_v3_cadence_discipline.md`. **FLAG for Phase 5.5 gate**: either (a) reduce n_trials below 35 (against memory `feedback_v3_confirmation_n_trials_35.md`), or (b) reduce ENSEMBLE_SIZE below 10 (against canonical CONFIRMATION spec), or (c) accept extended cap (precedent: iter-v3/018 ran 4.54h after which v3 cap raised to 6h; /015 may need v1 cap update to ~10h).

**Adopted plan**: launch at canonical spec (`--confirmation --ensemble-size 10 --n-trials 35`) and monitor; if approaching 9-10h, do NOT kill (CONFIRMATION integrity > wall-clock budget). Document the wall-clock outcome in engineering report. Update `feedback_v1_cadence_discipline.md` (NEW file at /015 closeout) codifying v1 CONFIRMATION wall-clock cap empirically.

---

## Section 4 — Falsifiers (F1-F8 inherited + F-AXIS-C1 + F-AXIS-MECHANISM + F7-NEW PARTIAL explicit)

Eight falsifiers from /014 + 3 NEW for /015 CONFIRMATION rigor.

### F1-MULTI — OOS Sharpe-Δ multi-seed mean vs BASELINE_V1 (PRIMARY)

- **Condition**: F1-MULTI = (OOS Sharpe iter-v1/015 multi-seed mean) - (OOS Sharpe BASELINE_V1 +0.6637)
- **PROMISING** (CONFIRMATION): Δ ∈ [+0.20, +0.55] AND multi-seed mean OOS Sharpe > BASELINE +0.6637 — triggers BASELINE_V1 update conditional (Section 7)
- **NULL / INERT**: Δ ∈ [-0.10, +0.20] — labeling axis non-distinguishable from baseline at multi-seed; CLOSES the axis with informational value
- **NEGATIVE**: Δ ∈ [-0.55, -0.10] — labeling axis HURTS at multi-seed with C1 FIXED; AXIS DECISIVELY CLOSED
- **NEGATIVE-catastrophic**: Δ < -0.55 — unprecedented; would indicate the axis is structurally toxic at full rigor

### F1-IS — IS Sharpe-Δ multi-seed mean vs BASELINE_V1 (SECONDARY)

- **Condition**: F1-IS = (IS Sharpe iter-v1/015 multi-seed mean) - (IS Sharpe BASELINE_V1 +0.2829)
- **PROMISING**: Δ ∈ [+0.10, +0.50]
- **NULL**: Δ ∈ [-0.10, +0.10]
- **NEGATIVE**: Δ ∈ [-0.50, -0.10]
- **NEGATIVE-catastrophic**: Δ < -0.50

### F2 — Trade count (mechanical sanity)

- **Condition**: |IS_trades - 621| ≤ 0.25 × 621 → IS_trades ∈ [466, 776]
- **PASS**: in band — labels resolve at calibrated barrier widths
- **FAIL-MISCALIBRATION**: outside band — verdict deferred to F-AXIS-C1

### F3 — IS Sharpe-Δ same as F1-IS (renamed; CONFIRMATION primary IS measurement)

(Identical to F1-IS in this CONFIRMATION; F3 retained as legacy label.)

### F4 — DEGENERATE_PREDICTOR detector

- **Condition**: per `validation_v1.detect_degenerate_predictor()` — fire if any model has >99% single-direction prediction OR >95% identical probability output
- **PASS**: no fire
- **FAIL**: fire — verdict immediately NEGATIVE-degenerate

### F5 — PSR (GATING at CONFIRMATION, NOT INFORMATIONAL)

- **Condition**: PSR_monthly_vs_0 ≥ 0.50 both IS and OOS (informational); PSR_monthly_vs_0 > 0.95 (CONFIRMATION GATING per BASELINE_V1.md "Hard Merge Floors")
- **PASS**: PSR > 0.95 both halves
- **FAIL-GATING**: PSR < 0.95 — does NOT block CONFIRMATION but blocks BASELINE_V1 update if all other gates pass

### F6 — OOS roster overlap with BASELINE (informational)

- **Condition**: 100% × (trades_in_BASELINE ∩ trades_in_iter015) / max(trades_in_iter015, 1)
- **Expected band**: [40%, 70%] — labels change AND multi-seed averages produce more diversified rosters
- **Outside band**: informational diagnostic for Phase 7.4 LM Master post-mortem

### F7-NEW-MULTI — Per-symbol exit-mix direction PASS rate across 10 outer seeds (NEW per /014 Critic Rec #3)

- **Condition (per-seed, then aggregated)**: each seed must produce per-symbol exit-mix direction matching predicted (BTC/ETH TO% UP, LINK/LTC/DOT TO% DOWN) for ≥3 of 5 symbols. Aggregate across 10 seeds.
- **PASS**: ≥7 of 10 seeds achieve 3+ per-symbol direction matches
- **PARTIAL**: 4-6 of 10 seeds — mechanism class confirmed but specific per-symbol direction is basin-rotated
- **FAIL**: ≤3 of 10 seeds — mechanism is broken even at multi-seed; F-AXIS-C1 should have caught this; engineering investigation

### F8-NEW-MULTI — IS trade count band per-seed (NEW)

- **Condition**: per-seed IS trade count ∈ [466, 776] across all 10 outer seeds
- **PASS**: 10/10 seeds in band
- **PARTIAL**: 7-9 seeds in band
- **FAIL**: ≤6 seeds in band — calibration is unstable across seeds

### F-AXIS-C1 (NEW; programmatic execution-barrier consistency) — PRIMARY MECHANISM FALSIFIER

- **Condition**: programmatic assertion in `tests/test_lgbm.py::test_sigma_source_ewma14d_execution_barrier_consistency` — execution-time TP/SL distance matches label-time TP/SL distance within 1e-6 tolerance for all IS candles in the test roster
- **PASS**: assertion passes for 100% of test candles
- **FAIL**: assertion fails for any candle → BLOCK-PENDING-FIX (one rerun chance per v1 skill)

### F-AXIS-MECHANISM (NEW; multi-seed n_eff replication) — DURABLE MECHANISM FALSIFIER

- **Condition**: per-seed `n_eff_per_cell_median ≥ 17` across at least 7 of 10 outer seeds. /014 single-seed observed 19; multi-seed should preserve.
- **PASS**: ≥7/10 seeds at n_eff ≥ 17 — mechanism diversification ROBUST at multi-seed
- **PARTIAL**: 4-6 seeds — mechanism partial but lifts from baseline n_eff=13 → /015 mean
- **FAIL**: ≤3 seeds — single-seed n_eff jump was lottery artifact (very unlikely; n_eff bound by label-distribution shape which is seed-independent)

### F7-NEW PARTIAL explicit verdict-class (NEW per /014 Critic Rec #3)

A new verdict-class row in Section 8.1 matrix:
- **Row PARTIAL**: F1×F3 NEGATIVE AND F7-NEW PARTIAL → "CONFIRMATION-NEGATIVE-MECHANISM-80-FUNCTIONAL" — closes the axis with the note that the per-symbol mechanism was 80% functional but the basin-direction was not edge-positive at multi-seed

---

## Section 5 — Predicted Outcomes (LM Master /014 §6 calibration UPDATED)

Per LM Master /014 Phase 7.4 §6 (commit `1f70af3`), multi-seed CONFIRMATION priors at /015 (UPDATED from initial 60/25/15):

| Outcome class | F1-MULTI Δ band | Pre-registered probability |
|---|---|---|
| F1-MULTI PROMISING | [+0.20, +0.55] | **20%** |
| F1-MULTI NULL / INERT | [-0.10, +0.20] | **55%** |
| F1-MULTI NEGATIVE | [-0.55, -0.10] | **25%** |

Concentrated NOT FLAT: at multi-seed dissolution, variance reduction is mechanically guaranteed. The 60/25/15 → 55/20/25 shift between Phase 4.5 and Phase 7.4 reflects /014's NEGATIVE single-seed basin draw + C1 confound being the proximate IS catastrophe explanation. LM Master Phase 7.4 §6 update:
- NEGATIVE bumped +10pp (C1 unresolved at /014 was the IS-catastrophe driver; FIXED at /015 removes the asymmetric amplification but the underlying mechanism remains)
- PROMISING shrunk -5pp (LTC IS+OOS WINNER at /014 was C1 WINDFALL — at multi-seed with C1 FIXED the LTC tail doesn't replicate)
- NULL stayed at 55% (modal outcome — labeling axis dissolves at multi-seed without producing or destroying edge)

### CONFIRMATION verdict matrix (Section 8.1 binding)

Eight outcome cells; the table in Section 8.1 maps observed (F1-MULTI × F1-IS × F-AXIS-C1 × F-AXIS-MECHANISM × Pareto seeds) to verdict.

---

## Section 6 — What Could Falsify the Hypothesis (Pre-Registered Tripwires)

### 6.1 Tripwire: F-AXIS-C1 FAIL

If the programmatic assertion fails (execution-time TP/SL distance does NOT match label-time within 1e-6 tolerance), the C1 FIX is incomplete. Verdict immediately = BLOCK-PENDING-FIX. Single rerun chance: QE fixes the dispatch defect, re-runs the test, re-launches the backtest. After rerun, verdict can be PASS or BLOCK-FINAL only (no recursion per v1 skill).

### 6.2 Tripwire: F-AXIS-MECHANISM FAIL

If n_eff_per_cell_median collapses to baseline 13 at multi-seed (i.e., <7/10 seeds at n_eff ≥ 17), the /014 single-seed n_eff jump was a lottery artifact. This is very unlikely (n_eff bound by label-distribution shape which is seed-independent), but if it fires, the labeling axis is structurally REFUTED at the mechanism layer (the loss surface was NOT diversified by σ_t labels).

### 6.3 Tripwire: F4 DEGENERATE_PREDICTOR FAIL

If any (model, seed, month) cell produces a degenerate predictor at /015, verdict immediately = CONFIRMATION-NEGATIVE-degenerate. Multi-seed at higher ensemble size should reduce degeneracy probability; firing at multi-seed indicates a fundamental data issue.

### 6.4 Tripwire: BASELINE_V1 update conditions not met (NORMAL outcome, not error)

Per Section 7, BASELINE_V1.md updates only on STRICTLY-BETTER on BOTH IS+OOS multi-seed mean AND both Pareto seeds positive. NORMAL outcomes:
- F1-MULTI PROMISING but F1-IS NULL/NEGATIVE → NO BASELINE update (one-sided lift; per-seed instability suspected)
- F1-MULTI PROMISING + F1-IS PROMISING but a Pareto seed has OOS Sharpe < 0 → NO BASELINE update (Gate 10 FAIL; single-seed fragility per `feedback_v3_baseline_update_policy.md`)
- F1-MULTI NULL → NO BASELINE update (default)
- F1-MULTI NEGATIVE → NO BASELINE update (default); labeling axis CLOSED

### 6.5 Tripwire: Wall-clock exceeds 10h

Predicted ~9.8h; cap should be ~10h. If at 9.5h the backtest is still running, monitor closely; if approaching 10h, allow completion (do NOT kill — CONFIRMATION integrity > wall-clock budget per /014 LM Master Phase 7.4 §7). Document outcome; update v1 cadence discipline file.

---

## Section 7 — BASELINE_V1 Update Conditions

Per user directive 2026-05-25 + `feedback_v3_baseline_update_policy.md` (applied to v1 mutatis mutandis), BASELINE_V1.md updates if and ONLY IF ALL of the following hold:

### 7.1 STRICTLY-BETTER trigger (NECESSARY conditions)

1. **Multi-seed mean IS Sharpe (10-seed) > BASELINE_V1 IS Sharpe (+0.2829)**: strict inequality on multi-seed mean.
2. **Multi-seed mean OOS Sharpe (10-seed) > BASELINE_V1 OOS Sharpe (+0.6637)**: strict inequality on multi-seed mean.

### 7.2 Hard-blocking gates (CANNOT be relaxed)

3. **OOS/IS Sharpe ratio ≥ 0.5** (Gate 3) — generalization check
4. **PSR_monthly_vs_0 (OOS) > 0.95** (Gate 6) — multi-seed noise floor check
5. **Both Pareto seeds OOS Sharpe > 0** (Gate 10) — single-seed fragility check

### 7.3 Aspirational gates (record as outstanding constraints; do NOT block)

6. IS Sharpe ≥ +1.0 (Gate 1) — record as outstanding; future-iteration priority
7. OOS Sharpe ≥ +1.0 (Gate 2) — record as outstanding; future-iteration priority
8. DSR > 0.95 (Gate 4) — record as outstanding; gate-reformulation candidate
9. PBO mean+max < 0.4 (Gate 5) — record specific cell if max FAIL
10. Top-symbol concentration ≤ 30% (Gate 7) — record as outstanding
11. Bundle OOS trades ≥ 130 (Gate 8) — record if FAIL

### 7.4 BASELINE_V1 update protocol (if conditions met)

If all of 7.1 + 7.2 hold:
1. Phase 8 diary issues `CONFIRMATION-MERGE` verdict
2. Update `BASELINE_V1.md` headline metrics to multi-seed mean (IS Sharpe, OOS Sharpe, MaxDD, OOS Trades, etc.) AND audit-trail entry citing this iteration as the source
3. Update `BASELINE_V1.md` "Hard Merge Floors" with new anchor values
4. Update `BASELINE_V1.md` "Ensemble seeds (FUTURE iter-v1/NNN)" to reflect any change in canonical CONFIRMATION inner ensemble (if any)
5. Cherry-pick the BASELINE_V1.md update commit to `main` per `feedback_always_document.md`
6. Tag `v0.v1-015` at the BASELINE_V1.md update commit
7. Outstanding constraints carry-forward: list failed aspirational gates with lift required for next CONFIRMATION
8. Update memory file (NEW or EXISTING) codifying the σ_t labeling axis as FIRST EDGE INGREDIENT in v1 catalog

If conditions 7.1 + 7.2 NOT all met → `CONFIRMATION-MERGE-NO-UPDATE` (if PROMISING but doesn't strictly beat) OR `CONFIRMATION-NULL`/`CONFIRMATION-NEGATIVE`. No BASELINE_V1 update.

### 7.5 Verdict-class table for /015 (binding)

| F1-MULTI Δ | F1-IS Δ | Pareto seeds | F-AXIS-C1 | F-AXIS-MECHANISM | Verdict-class | BASELINE update? |
|---|---|---|---|---|---|---|
| ≥ +0.20 | ≥ +0.10 | Both > 0 | PASS | PASS | **CONFIRMATION-MERGE-with-UPDATE** | **YES** (cherry-pick to main + tag v0.v1-015) |
| ≥ +0.20 | ≥ +0.10 | Both > 0 | PASS | PARTIAL | CONFIRMATION-MERGE-with-UPDATE | YES — mechanism partial but multi-seed mean strictly better |
| ≥ +0.20 | ≥ +0.10 | One ≤ 0 | PASS | any | CONFIRMATION-MERGE-NO-UPDATE | NO — Gate 10 fail |
| ≥ +0.20 | < +0.10 | any | any | any | CONFIRMATION-MERGE-NO-UPDATE | NO — IS lift insufficient |
| [-0.10, +0.20] | any | any | PASS | any | **CONFIRMATION-NULL** | NO (default) |
| [-0.55, -0.10] | any | any | PASS | any | **CONFIRMATION-NEGATIVE** | NO (axis CLOSED at multi-seed) |
| < -0.55 | any | any | PASS | any | CONFIRMATION-NEGATIVE-catastrophic | NO |
| any | any | any | FAIL | any | **BLOCK-PENDING-FIX** | NO (single rerun chance) |

Boundary cells handled by Critic Phase 7.5 seed-determinism audit if multi-seed mean is within 0.05 of any threshold.

---

## Section 8 — Verdict Gates (CONFIRMATION-specific)

### 8.1 Verdict matrix (binding; subsumes Section 7.5)

See Section 7.5. The CONFIRMATION-specific verdict classes are:

- **CONFIRMATION-MERGE-with-UPDATE**: STRICTLY-BETTER on BOTH IS+OOS multi-seed mean + both Pareto seeds > 0 + F-AXIS-C1 PASS + F-AXIS-MECHANISM PASS or PARTIAL. **Updates BASELINE_V1.md**.
- **CONFIRMATION-MERGE-NO-UPDATE**: PROMISING on OOS multi-seed but fails to strictly beat baseline on IS OR fails Pareto Gate 10. Documents new infrastructure (C1 FIX + engineering report hard-stop + F-AXIS falsifiers); does NOT update BASELINE_V1.
- **CONFIRMATION-NULL**: multi-seed mean within ±0.05 OOS Δ of baseline. Axis CLOSED at multi-seed; informational.
- **CONFIRMATION-NEGATIVE**: multi-seed mean OOS Δ < -0.05 (more strictly, < -0.10 NEGATIVE band). Axis DECISIVELY CLOSED.
- **BLOCK-PENDING-FIX**: F-AXIS-C1 fails. Single rerun chance; verdict can only be PASS or BLOCK-FINAL after rerun.

### 8.2 Verdict resolution rule

Verdict = first cell that matches observed (F1-MULTI, F1-IS, Pareto seeds, F-AXIS-C1, F-AXIS-MECHANISM). BLOCK-PENDING-FIX overrides all (mechanical failure dominates edge claims).

### 8.3 Hard merge gates evaluation (CONFIRMATION)

For CONFIRMATION-MERGE-with-UPDATE, the following gates are EVALUATED (some hard-block, others informational):

| Gate | Threshold | Hard-block? | Source |
|---|---|---|---|
| 1. IS Sharpe ≥ +1.0 | unlikely to clear at /015 (baseline +0.28) | NO (aspirational; record as outstanding) | BASELINE_V1.md |
| 2. OOS Sharpe ≥ +1.0 | possible at /015 if PROMISING (baseline +0.66; lift +0.34 needed) | NO (aspirational) | BASELINE_V1.md |
| 3. OOS/IS Sharpe ratio ≥ 0.5 | **YES** (generalization) | YES | BASELINE_V1.md |
| 4. DSR > 0.95 | structural at n_trials=35; record outstanding | NO (aspirational) | BASELINE_V1.md |
| 5. PBO mean+max < 0.4 | likely pass at multi-seed | NO (aspirational) | BASELINE_V1.md |
| 6. PSR_monthly_vs_0 (OOS) > 0.95 | **YES** (noise floor) | YES | BASELINE_V1.md |
| 7. Top-symbol concentration ≤ 30% | likely fail (LTC at /014 OOS = 740% of total; denominator effect) | NO (aspirational) | BASELINE_V1.md |
| 8. OOS trades ≥ 130 | likely pass (baseline 189; /014 had 202) | NO (aspirational unless catastrophic drop) | BASELINE_V1.md |
| 9. 10-seed mean Sharpe > 0 | **YES** (foundational at CONFIRMATION) | YES | `feedback_v3_baseline_update_policy.md` |
| 10. Both Pareto seeds OOS Sharpe > 0 | **YES** (single-seed fragility) | YES | `feedback_v3_baseline_update_policy.md` |

Hard-blocking gates (3, 6, 9, 10) MUST PASS to issue CONFIRMATION-MERGE-with-UPDATE. Aspirational gates record outstanding constraints; do NOT block.

---

## Section 9 — Library Stack (mandatory per /009 closeout amendment)

- `numpy>=1.24` — already installed
- `pandas>=2.0` — `ewm(halflife=N, adjust=False).std()` for past-only EWMA σ_t (already installed)
- `pyarrow>=14` — parquet I/O (already installed)
- `lightgbm==4.x` — unchanged (no version pin change at /015)
- `optuna>=3.5` — unchanged
- `statsmodels>=0.14` — ADF for Critic Check 5 (already installed)

No new dependencies. C1 FIX is pure Python logic on existing `_month_natr`-style cache — uses `numpy` + dict access.

---

## Section 10 — Implementation Spec (QE Deliverables)

### 10.1 Source files to modify

1. **`src/crypto_trade/strategies/ml/lgbm.py`**:
   - Add `self._month_sigma: dict[tuple[str, int], float] = {}` initialization in `__init__` (sibling to line ~280 `self._month_natr`)
   - In `_train_for_month()`, populate `self._month_sigma` per (symbol, open_time) using `self._label_sigma_values` at test-month-first-candle index when `sigma_source="ewma14d"`. Mirrors existing `_month_natr` population at lines 740-753.
   - Modify lines 905-915 (verified by Bash audit) to dispatch on `self.sigma_source`:
     - If `"ewma14d"`: `tp_pct = sigma × sigma_k_tp × sqrt(timeout_candles) × 100`; `sl_pct = sigma × sigma_k_sl × sqrt(timeout_candles) × 100`
     - Else (`"natr"`): BIT-IDENTICAL to current path
   - `timeout_candles = self.label_timeout_minutes / (8 * 60)` for 8h interval (parameterize for interval safety)
   - Update verbose log to display sigma-derived TP/SL when applicable

2. **`run_baseline_v1.py`**:
   - Lines 1217-1229: convert `[WARNING]` to `sys.exit(1)` when `engineering_report.md` missing AND `--no-engineering-report` not passed
   - Add `--no-engineering-report` boolean flag to argparse (default False)
   - Print to `sys.stderr` instead of `stdout` for FATAL messages

3. **`tests/test_lgbm.py`**:
   - Add `test_sigma_source_ewma14d_execution_barrier_consistency` — F-AXIS-C1 programmatic falsifier
   - Verify execution-time TP/SL distance equals σ_t × k × √timeout × 100 within 1e-6 tolerance for all test-roster candles

### 10.2 Required artifacts (BLOCKING for Phase 7.5 dispatch — runner HARD-STOP per /014 Rec #2)

QE produces in Phase 6 closeout:

1. `reports-v1/iteration_v1-015/comparison.csv` — same schema as baseline + multi-seed mean across 10 inner seeds
2. `reports-v1/iteration_v1-015/in_sample/` + `out_of_sample/` — full reports
3. `reports-v1/iteration_v1-015/per_symbol.csv` — top-level F7-NEW-MULTI diagnostic per symbol (PER-SEED columns + multi-seed mean)
4. `reports-v1/iteration_v1-015/dsr.json` — per-(symbol, month) n_eff_per_cell_median per outer seed; computes F-AXIS-MECHANISM
5. `reports-v1/iteration_v1-015/cpcv_paths.csv` — CPCV PBO path artifact (inherited from /001 methodology)
6. **`reports-v1/iteration_v1-015/engineering_report.md`** — **BLOCKING (runner HARD-STOP)**. Contents:
   - Wall-clock breakdown per model + per outer seed
   - Per-model σ_t distribution sanity (p10/p50/p90 per seed)
   - Per-symbol exit-mix multi-seed (F7-NEW-MULTI table; 10 columns + mean)
   - F8-NEW-MULTI per-seed trade count
   - **F-AXIS-C1 PASS/FAIL — programmatic assertion result attached**
   - **F-AXIS-MECHANISM PASS/FAIL/PARTIAL — n_eff replication count out of 10**
   - σ_t lookahead audit (already passing per /014 Critic; reconfirm at /015)
   - Multi-seed mean F1-MULTI / F1-IS / F2 / F3 / F4 / F5 / F6 numbers
   - Pareto seeds: which 2 of 10 are Pareto-front; their OOS Sharpe values
   - C1 FIX status disclosure (mandatory per /014 Critic Phase 7.5 Check 8 forward-mandate)
   - BASELINE_V1 update recommendation: YES/NO with explicit Section 7 gate-by-gate evaluation

Runner HARD-STOP at `run_baseline_v1.py:1217-1229` (per Section 3.2) enforces existence of `engineering_report.md` before final exit — Phase 7.5 dispatch is hard-rejected if missing. Critic Phase 6.0 at /015 verifies the runner code change exists BEFORE backtest dispatches.

### 10.3 Test suite additions

- `tests/test_lgbm.py::test_sigma_source_ewma14d_execution_barrier_consistency` (F-AXIS-C1; NEW)
- `tests/test_lgbm.py::test_sigma_source_ewma14d_backward_compat` (sigma_source="natr" → BIT-IDENTICAL; existing at /014)
- `tests/test_lgbm.py::test_sigma_source_ewma14d_past_only` (σ_t at candle t computed from ≤ t-1; existing at /014)
- `tests/test_run_baseline_v1.py::test_engineering_report_hardstop` (NEW for /015): if `engineering_report.md` missing AND `--no-engineering-report` not passed → sys.exit(1); otherwise continues

All 4 tests MUST PASS before Phase 7.5 dispatch.

### 10.4 Wall-clock budget

Predicted ~9.8h per Section 3.6. CONFIRMATION integrity > wall-clock budget; do NOT kill if approaching 6h cap. Document outcome; update v1 cadence discipline at /015 closeout.

---

## Section 11 — Alternates for /016+ Conditional on /015 Outcome

The cycle-2 catalog closes at /015 regardless of outcome (10:1 cadence complete). Cycle-3 begins at /016. Alternative axes for /016 (cycle-3 #1 EXPLORATION):

### Option A (if /015 = CONFIRMATION-MERGE-with-UPDATE)

Cycle-3 first EXPLORATION = labeling sub-axis refinement (e.g., σ_t halflife sweep at {7, 14, 21, 28} days OR k_tp/k_sl re-grid). Test whether labeling axis edge stacks with sister calibrations. CAUTION: per `feedback_v3_engineered_features_dont_stack.md`-style discipline, same-family stacking at single-seed EXPLORATION may not replicate; carry forward to next CONFIRMATION.

### Option B (if /015 = CONFIRMATION-MERGE-NO-UPDATE or CONFIRMATION-NULL or CONFIRMATION-NEGATIVE)

Cycle-3 first EXPLORATION = UNUSED-family axis. Three candidates per /014 Critic Phase 7.5 Path Forward:

1. **Universe expansion to 7-symbol with concentration cap** (`universe` family — UNUSED in cycle-2 since /006). Add BNB + SOL with per-symbol PnL share cap. Denominator expansion attenuates basin-lottery extreme draws. NOT proportional cap (v3/020 closed that for v3 catalog; v1 untested).

2. **XGBoost head-to-head replacement** (`model-arch` family — UNUSED in cycle-2). Depth-wise vs leaf-wise growth may favor different feature interactions. v3/016 closed this for v3 but v1's V1_FEATURE_COLUMNS_PRUNED feature set is different (40 cols vs v3's 14).

3. **Sample weighting by past-realized vol** (NEW `sample-weighting` family — never used in v1). Replace `abs(labeled_pnl)` weighting with weights inversely proportional to past-realized 30-day vol. Attenuates extreme-vol-regime trade influence on IS basin.

Per constructive duty: each from family NOT used in prior 5 EXPLORATIONs.

### Option C (if /015 = BLOCK-PENDING-FIX)

QE fixes the C1 dispatch defect; QR re-launches /015 backtest at same spec. After rerun, verdict can only be PASS or BLOCK-FINAL. NO recursion.

---

## Section 12 — Catalog Closeout Plan + BASELINE_V1 Update Procedure

### 12.1 Catalog entry

At /015 closeout, append a one-line entry to `briefs-v1/exploration_catalog.md` per the schema (TBD: catalog needs a CONFIRMATION-row schema; current schema is EXPLORATION-only). The new CONFIRMATION row should include:

| iter-v1-NNN | YYYY-MM-DD | axis confirmed | axis family | F1-MULTI Δ (OOS multi-seed mean) | F1-IS Δ (multi-seed mean) | F-AXIS-C1 | F-AXIS-MECHANISM | Pareto seeds positive | Verdict | BASELINE update? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iter-v1/015 | 2026-05-25 | labeling σ_t × k EWMA 14d + C1 FIX | labeling (CONFIRMATION) | [observed] | [observed] | PASS/FAIL | PASS/PARTIAL/FAIL | both/one/none | CONFIRMATION-... | YES/NO |

A new "CONFIRMATION Ledger" section may need to be added to `exploration_catalog.md` since the existing ledger is EXPLORATION-only. Defer schema update to Phase 8 closeout when verdict is known.

### 12.2 BASELINE_V1.md update procedure (only if verdict = CONFIRMATION-MERGE-with-UPDATE)

Per Section 7.4:
1. Phase 8 diary issues `CONFIRMATION-MERGE-with-UPDATE` verdict
2. Update `BASELINE_V1.md`:
   - Headline metrics: IS Sharpe, OOS Sharpe, MaxDD, OOS Trades, etc. (multi-seed mean)
   - "Ensemble seeds (for FUTURE iter-v1/NNN per the new skill discipline)": confirm 10-seed CONFIRMATION roster `[42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006]` (no change)
   - "Hard Merge Floors" table: update "Baseline current" column with /015 metrics
   - "Audit Trail" entry citing /015 as the source of baseline ratchet-up
   - Add section "Outstanding Constraints from /015": failed aspirational gates with lift required for next CONFIRMATION
   - Mention σ_t labeling axis as FIRST EDGE INGREDIENT in v1 catalog (mirrors v3/028's regime_momentum_signed_5d as first multi-seed-validated edge ingredient in v3)
3. Cherry-pick the BASELINE_V1.md update commit to `main` per `feedback_always_document.md`
4. Tag `v0.v1-015` at the BASELINE_V1.md update commit
5. New memory file (or update existing): codify σ_t labeling axis as PROVEN edge ingredient at v1 ENSEMBLE_SIZE=10 CONFIRMATION budget
6. Cycle-2 closes; cycle-3 begins at /016

### 12.3 Diary

`diary-v1/iteration_v1-015.md` with verdict + headline metrics + lessons + permanent additions + Path Forward (from Critic Phase 7.5) + BASELINE update SHA (if applicable).

### 12.4 Tag

`v0.v1-015` after Phase 8 closeout. If verdict = CONFIRMATION-MERGE-with-UPDATE, the tag marks the multi-seed-validated baseline ratchet. If other verdict, the tag marks the iteration commit chain (no baseline ratchet).

---

## Section 13 — Phase 5.5 Self-Check

QR self-audits this brief against the v1 skill's Phase 5.5 gate checklist:

| Section requirement | Status | Notes |
|---|---|---|
| 0 — Iteration pre-header (anchor, mode, label, determinism, cadence, axis family) | PRESENT | |
| 0.2bis — Spec disambiguation (user-directive `--seeds 10 --ensemble-size 5` vs v1 architecture) | PRESENT | Adopts `--confirmation --ensemble-size 10`; flags for Phase 5.5 review |
| 0.5 — Cadence position (cycle-2 #10 CONFIRMATION; 9 EXPLORATION precedents) | PRESENT | |
| 0.6 — Architecture-family justification (CONFIRMATION not new EXPLORATION) | PRESENT | Rotation N/A at CONFIRMATION |
| 0.7 — CONFIRMATION bundle composition (NEW) | PRESENT | Inherits /001 methodology + /008 n_eff + /014 σ_t with C1 FIX |
| 1 — Hypothesis (single sentence + 3 falsifiable claims) | PRESENT | LM Master /014 §6 prior 55/20/25 NULL/PROMISING/NEGATIVE |
| 2 — IS-only evidence (inherited from /014; new multi-seed variance estimate) | PRESENT | /014 EDA reused; multi-seed SE ≈ 0.25 |
| 2.5 — HIGH-RISK Axis Declaration | PRESENT | NORMAL-RISK at CONFIRMATION (multi-seed by design) |
| 3 — Proposed Changes (C1 FIX + engineering report HARD-STOP + F-AXIS falsifiers) | PRESENT | 4 src/ changes + 3 test additions |
| 4 — Falsifiers (numerical conditions) | PRESENT | F1-MULTI / F1-IS / F2 / F-AXIS-C1 / F-AXIS-MECHANISM + F7-NEW-MULTI / F8-NEW-MULTI + F7-NEW PARTIAL explicit |
| 5 — Predicted outcomes (per-cell pre-registration UPDATED 55/20/25) | PRESENT | LM Master /014 §6 calibration |
| 6 — What could falsify | PRESENT | 5 tripwires (F-AXIS-C1, F-AXIS-MECHANISM, F4, BASELINE conditions, wall-clock) |
| 7 — BASELINE_V1 update conditions (NEW per user directive) | PRESENT | STRICTLY-BETTER + 3 hard-blocking gates + 6 aspirational |
| 8 — Verdict gates (CONFIRMATION-specific 5 classes) | PRESENT | MERGE-with-UPDATE / MERGE-NO-UPDATE / NULL / NEGATIVE / BLOCK-PENDING-FIX |
| 9 — Library stack | PRESENT | No new deps |
| 10 — Implementation spec for QE (src/ + tests + BLOCKING engineering_report.md) | PRESENT | 3 src/ files; 4 tests; engineering report runner HARD-STOP |
| 11 — Alternates for /016+ | PRESENT | 3 options conditional on /015 outcome |
| 12 — Catalog closeout plan + BASELINE_V1 update procedure | PRESENT | New CONFIRMATION ledger schema |
| 13 — Phase 5.5 self-check | PRESENT | this section |
| Methodology-probe check | PASS | /015 is NOT a methodology probe — completes the labeling axis with C1 FIX |
| LM Master Phase 4.5 placeholder | PRESENT | Brief will be UPDATED post-Phase 4.5 if recommendations diverge from /014 §7 mandates |
| Engineering report BLOCKING declaration | PRESENT | Section 10.2 + runner HARD-STOP per Section 3.2 |
| User directive compliance (BASELINE_V1 update conditions per `feedback_v3_baseline_update_policy.md` adapted to v1) | PRESENT | Section 7 |
| /014 Critic Phase 7.5 Rec adoption (Rec #1 C1 FIX, Rec #2 hard-stop, Rec #3 F7-PARTIAL verdict-class) | PRESENT | All 3 adopted explicitly |
| LM Master /014 Phase 7.4 §7 mandate adoption (5 items) | PRESENT | C1 FIX + F7-NEW-MULTI + F-AXIS-MECHANISM + C1 disclosure + n_trials=35 retained |
| Spec interpretation conflict declared (user `--ensemble-size 5` vs v1 canonical `--ensemble-size 10`) | PRESENT | Section 0.2bis |

Self-check: **PASS**. Brief is complete per v1 skill discipline + /014 forward-mandate carry-forwards + user 2026-05-25 directive on BASELINE_V1 update conditions. Phase 5.5 gate (Engineer) and Phase 6.0 pre-flight (Critic) should both verify against this checklist.

---

## Appendix — Quick-Reference Summary

| Item | Value |
|---|---|
| **Anchor** | BASELINE_V1.md (IS +0.2829 / OOS +0.6637) |
| **Mode** | CONFIRMATION (cycle-2 #10; FIRST cycle-2 CONFIRMATION) |
| **Axis** | labeling (σ_t × k EWMA 14d + C1 FIX) |
| **Spec** | `--confirmation --iteration 15 --pruned-features --n-trials 35 --label-sigma-source ewma14d --label-sigma-k-tp 1.06 --label-sigma-k-sl 0.53 --label-sigma-halflife-days 14` |
| **ENSEMBLE_SIZE** | 10 inner seeds (canonical v1 CONFIRMATION) |
| **Wall-clock cap** | ~10h (v1 CONFIRMATION; predicted 9.8h; do NOT kill at 6h) |
| **C1 FIX** | MANDATORY — `lgbm.py:905-915` dispatch on `self.sigma_source` |
| **Engineering report HARD-STOP** | MANDATORY — `run_baseline_v1.py:1217-1229` `sys.exit(1)` |
| **Predicted outcomes** | 55% NULL / 20% PROMISING / 25% NEGATIVE (LM Master /014 §6) |
| **BASELINE_V1 update conditions** | STRICTLY-BETTER on BOTH IS+OOS multi-seed mean + Gate 3, 6, 9, 10 all PASS |
| **If MERGE-with-UPDATE** | cherry-pick BASELINE_V1.md to main + tag v0.v1-015 + cycle-2 closes |
| **If MERGE-NO-UPDATE / NULL / NEGATIVE** | no BASELINE update; cycle-2 closes; /016 cycle-3 #1 EXPLORATION |
| **If BLOCK-PENDING-FIX** | single rerun chance; PASS or BLOCK-FINAL after rerun |

---

**End of /015 CONFIRMATION brief.** Phase 5.5 gate (Engineer) follows; if PASS, Phase 6.0 (Critic) pre-flight runs; if PASS, QE Phase 6 launches backtest.

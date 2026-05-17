# Phase 5.5 Gate — iter-v3/089

OVERALL: PASS

iter-v3/089 is a CORRECTED-BUILD EXPLORATION on the RETAINED /088 cross-sectional
`LGBMRanker` architecture — two mandatory corrections (Critic /088 Recs #2 and #3)
plus the genuine cost-aware-construction axis.  The brief is complete across all
11 sections (Section 0, 0.5, 1–10, 11), every design parameter is IS-selected or
a-priori from cited research, the Section-3 build spec is precise and already wired
at the /089 setup commit (`bb8c231`), the sign fix is genuinely flipped vs /088,
the CPCV-proxy fix is real, the turnover ceiling is wired as a hard runtime gate,
no /089 parameter is OOS-tuned, ITERATION_LABEL = "v3-089", 36/36 tests PASS, and
ruff is clean.  PASS.

---

## Per-Section Status

- **Section 0 (Data Split)**: PASS — `OOS_CUTOFF_DATE = 2025-03-24` and
  `training_months = 24` declared IMMUTABLE in brief and confirmed in runner
  (`OOS_CUTOFF_MS = 1742774400000`); IS/OOS windows stated in absolute dates.
- **Section 0.5 (Iteration Type)**: PASS — CORRECTED-BUILD EXPLORATION, cycle-3
  slot #8 of 10; explicitly NOT a fresh re-architecture; grounded in /088 closeout
  diary (cross-sectional line is the active v3 research direction).
- **Section 1 (Hypothesis)**: PASS — specific, causal, one-paragraph claim.  The
  /088 model transfers OOS (rank-IC +0.043, t≈4.6); the book lost money to a sign
  inversion + turnover drag; correcting the sign and attacking turnover structurally
  (quintile + overlapping holds + no-trade band) materially reduces the net loss.
  The hypothesis is honest: it pre-states the construction fixes alone do not reach
  a positive IS net Sharpe, and that the gross-signal expansion is deferred to /090.
  Section 1.3 addresses the bold-research mandate (relentless iteration, not
  defeatism).
- **Section 2 (IS-Only Evidence)**: PASS — two committed EDA scripts, both IS-only
  (`open_time < OOS_CUTOFF_MS` filter confirmed in source).
  `analysis/iteration_v3-089/turnover_construction_eda.py` (E1–E6) runs a TRUE
  IS-internal walk-forward of the RETAINED `LGBMRanker` (trains on IS months,
  predicts the next IS month — no OOS row read).
  `analysis/iteration_v3-089/gross_signal_eda.py` (G1–G4) is a model-free
  cross-sectional predictor EDA.  All 11 output CSVs confirmed present.
  Numerical evidence: E1 corrected-sign IS gross Sharpe +0.0485; E2 quintile net
  Sharpe −0.574 vs tercile −0.655; E3 hold=3 cuts turnover 2.2× and IS net Sharpe
  −0.57→−0.42; E4 τ=0.020 IS-best net Sharpe −0.315; E5 combined construction halves
  IS net loss (−0.65→−0.31), turnover 0.325→0.120; E6 the 0.138 ceiling = 0.120 ×
  1.15; G1 quintile the spread sweet spot, decile too thin at N=22.  Category-
  matching absent; every figure is IS-data-derived.
- **Section 3 (Proposed Changes)**: PASS — implementable spec.  See code-readiness
  section below.
- **Section 4 (Expected OOS Impact)**: PASS — dual evaluation (absolute ≥+1.0/+1.0
  floor + architecture-internal diagnostics); /088 cross-sectional book IS −0.6403 /
  OOS −0.5418 as ANCHOR 1; /059 baseline IS +1.0894 / OOS +0.5791 as ANCHOR 2 with
  the comparability caveat.  Five falsifiers F1–F5 pre-registered with numerical
  thresholds; F2 (IS turnover > 0.138) is a HARD MERGE-BLOCKING gate not a
  prediction.  Predicted modal OOS outcome honest: [−0.30, +0.10] monthly Sharpe.
- **Section 5 (Risk Mitigation)**: PASS — overlapping holds + no-trade band +
  turnover ceiling flagged IS-calibrated (EDA E3/E4/E6) with simulated historical
  effect (turnover 0.325→0.120, net Sharpe −0.65→−0.31).  Structural controls
  (dollar-neutral, inverse-vol, quintile, burn-in, embargo) carried from /088.
- **Section 6 (Risk Management Design)**: PASS — legacy 7-gate stack deferred
  (would confound the construction measurement — the same honest scoping /088 made
  and the Critic accepted); /089 risk apparatus is structural construction + two
  new turnover controls.
- **Section 7 (Failure-Mode Prediction)**: PASS — pre-registered probability
  distribution over five named outcomes (≈45% construction-works-but-sub-floor modal;
  ≈20% net-positive-sub-floor; ≈20% F3-fires; ≈10% F2-fires; ≈5% full-success).
  The /088 calibration lesson applied: thin-signal + every-bar rebalance → modal risk
  is NOT a tail.
- **Section 8 (MERGE/NO-MERGE Criteria)**: PASS — five-class LOCKED taxonomy
  (SUSPICIOUS, CONSTRUCTION-FALSIFIED, CONSTRUCTION-VALIDATED-PROMISING with
  FULL/FOUNDATION sub-cases, CONSTRUCTION-PARTIAL, NULL) in disjunctive precedence
  with numerical gates per class.  Turnover ceiling and /088-book OOS Sharpe wired
  into the gates.  States explicitly that an EXPLORATION cannot update BASELINE_V3.md.
- **Section 9 (Library Stack)**: PASS — LightGBM (`LGBMRanker`, `lambdarank`),
  Optuna, pandas/numpy.  No new third-party dependency.
- **Section 10 (QR Audit Trail)**: PASS — Section 10.1 orchestrator scope-steer +
  QR design ownership.  Section 10.2 five literature sources with IDs
  (Poh/Lim/Zohren arXiv 2012.07149; Constantinides 1986 / Davis-Norman 1990;
  Jegadeesh-Titman 1993 + 2023 review; FMPM 2022 + Baldi-Lanfranchi 2024; IRFA
  2024/2025).  Section 10.3 is the no-cheating audit.  Section 10.4 honest senior
  read.
- **Section 11 (Reproducibility Stamp)**: PASS — EDA SHA `c172a12`, brief SHA
  `ac2b487`, setup SHA `bb8c231`; reports path and run mode (EXPLORATION, seed=42,
  --n-trials 35) declared; deferred /090 axis recorded.

---

## Code-Readiness Verification

All checks performed against committed source at HEAD (`a9ba0da`).

### Sign fix — genuinely flipped vs /088

**CONFIRMED.**

`build_positions` at
`src/crypto_trade/strategies/ml/cross_sectional.py` lines 662–663:

```
long_syms = set(sorted_syms[-n_leg:])   # TOP quantile (high score) → LONG
short_syms = set(sorted_syms[:n_leg])   # BOTTOM quantile (low score) → SHORT
```

/088 longed `sorted_syms[:n_leg]` (the LOWEST scores = predicted future losers).
/089 inverts this: `sorted_syms[-n_leg:]` = the HIGHEST scores = predicted future
winners.  The `predict_ranking` docstring (lines ~566–576) and the
`label_cross_sectional_rank` docstring (lines ~181–191) are corrected — the stale
"reversal → SHORT high-score" narrative is replaced with the first-principles
forward-mapping explanation.

The `test_sign_fix_longs_highest_scores` test deterministically verifies the
mapping (ascending scores 0–14; asserts longs are the top-3 indices).

### CPCV-proxy fix — actual long-short net return

**CONFIRMED.**

`_compute_xs_cpcv` in `run_cross_sectional_v3.py` (lines 230–356):

1. Restricts to IS rows (`~results["is_oos"]`).
2. Sums `net_pnl` per `open_time` → one book return per IS timestamp
   (`bar_ret = is_res.groupby("open_time")["net_pnl"].sum()`).
3. For each CPCV path's test fold, computes Sharpe + max-DD on the actual
   path returns (`bar_ret_arr[test_idx]`).
4. `XS_REQUIRED_GAP = 88` asserted via `expected_gap=XS_REQUIRED_GAP` at
   `combinatorial_purged_cv` call (line 294).

The /088 degenerate proxy (`mean(sub_labels[long_idx]) − mean(sub_labels[short_idx])`)
is eliminated.  `frac_positive_paths` now reflects the fraction of CPCV paths with
positive ACTUAL long-short net-return Sharpe — an informative gate.

### Turnover ceiling — wired as a real runtime gate

**CONFIRMED.**

In `run_cross_sectional_v3.py` (lines 428–514):

```
is_turnover = compute_turnover_per_bar(results, is_oos=False)
turnover_gate_pass = is_turnover <= XS_TURNOVER_CEILING   # XS_TURNOVER_CEILING = 0.138
```

The gate result is emitted to:
- `comparison.csv`: row `metric = "turnover_ceiling_gate_pass"`,
  `in_sample = float(turnover_gate_pass)` (1.0 = PASS, 0.0 = FAIL),
  `out_of_sample = XS_TURNOVER_CEILING` (the ceiling value for reference).
- `dsr.json`: `"turnover_ceiling_gate_pass": bool(turnover_gate_pass)`.

A FAIL (IS turnover > 0.138) is immediately visible in the Phase-7 report.

### Construction constants — EDA-selected values verified

**CONFIRMED** by `test_iter089_construction_constants`:

- `XS_QUANTILE_FRAC = 0.20` (quintile, EDA E2/G1)
- `XS_HOLD_BARS = 3` (overlapping holds, EDA E3 + Jegadeesh-Titman)
- `XS_NO_TRADE_BAND = 0.020` (EDA E4 IS-best)
- `XS_TURNOVER_CEILING = 0.138` (EDA E6: IS-best turnover 0.120 × 1.15)

All passed explicitly at the runner call site; no auto-discovery.

### ITERATION_LABEL

**CONFIRMED:** `ITERATION_LABEL = "v3-089"` at `run_cross_sectional_v3.py` line 83.

---

## No-Cheating Verification

Every /089 design parameter is IS-selected or a-priori from cited research:

- `OOS_CUTOFF_DATE` / `training_months` — IMMUTABLE, untouched.
- Sign fix — first-principles correction of what `lambdarank` on a forward-return
  grade learns; no data parameter tuned.
- CPCV-proxy fix — methodology correction; no parameter tuned.
- Quintile (0.20) — `E2_quantile_concentration.csv` (IS-internal walk-forward net
  Sharpe) + `G1_horizon_quantile_spread.csv` (IS realised spread Sharpe).  Both
  IS-only; EDA code confirmed `open_time < OOS_CUTOFF_MS` filter.
- Hold = 3 bars — `E3_overlapping_holds.csv` (IS-internal walk-forward); also
  horizon-matched (= `XS_HORIZON`) and the Jegadeesh-Titman convention.
- No-trade band τ = 0.020 — `E4_no_trade_band_scan.csv`: scanned on IS data; τ=0.020
  is the IS-best net Sharpe of the 17-variant grid.  OOS never read.
- Turnover ceiling = 0.138 — `E6_turnover_ceiling.csv`: IS-best /089 construction
  IS turnover/bar (0.120) × 1.15 headroom.  An IS-derived a-priori gate.
- The 13-feature set, 22-symbol universe, H=3 label, `XS_REQUIRED_GAP = 88` —
  UNCHANGED from /088 (all /088-IS-grounded).  The G4 feature expansion is deferred
  to /090.
- The IS-internal walk-forward in `turnover_construction_eda.py` trains on IS months
  and predicts the next IS month — no OOS row read.
- The QR sees OOS for the first time in Phase 7.  Every Section-4 gate is a
  pre-registered evaluation gate, not a tuned parameter.

---

## Test Coverage and Lint

- **`tests/strategies/ml/test_cross_sectional.py` — 36/36 PASS** (confirmed by QE
  independent run; 1.98s wall-clock).
- The 6 new /089 tests: `test_sign_fix_longs_highest_scores`,
  `test_no_trade_band_holds_within_band`, `test_no_trade_band_zero_is_identity`,
  `test_no_trade_band_reduces_turnover`, `test_compute_turnover_per_bar`,
  `test_iter089_construction_constants`.
- The 30 /088 tests still pass — no regression.
- **Ruff** — `All checks passed!` on `cross_sectional.py`,
  `run_cross_sectional_v3.py`, and `test_cross_sectional.py`.
- The QR's reported 1 pre-existing unrelated full-suite failure is in the slow ML
  test suite (not in the cross-sectional or core test suites); the core test suite
  (115 tests) and `test_cross_sectional.py` (36 tests) are clean.  This failure is
  pre-existing and not /089-introduced.

---

## Phase-6 Scope

The Phase-6 step is the backtest run + engineering report.  The code is already wired.
Concretely:

1. Verify data freshness for the 22-symbol `XS_UNIVERSE` (8h parquets in
   `data/features_v3/`); re-fetch/re-regen if any CSV is >16h stale.
2. Run `uv run python run_cross_sectional_v3.py --n-trials 35 --exploration`
   (EXPLORATION mode, seed=42) and capture stdout/stderr to
   `reports-v3/iteration_v3-089/run.log`.
3. Verify outputs: `comparison.csv` (with `turnover_ceiling_gate_pass`),
   `cpcv_paths.csv` (non-degenerate Sharpes), `rank_ic.csv`, `dsr.json`
   (with `turnover_ceiling_gate_pass` bool), per-symbol CSVs.
4. Write and commit the engineering report at
   `briefs-v3/iteration_v3-089/engineering_report.md`.

---

## Gate Decision

OVERALL: **PASS**.  All 11 sections are present and substantive.  The sign fix is
genuinely flipped vs /088 (top-quantile LONG, independently verified).  The
CPCV-proxy fix computes actual long-short net returns (independently verified).
The 0.138 turnover ceiling is wired as a real runtime gate emitted to both
`comparison.csv` and `dsr.json` (independently verified).  No /089 parameter is
OOS-tuned (no-cheating audit clean).  ITERATION_LABEL = "v3-089".  36/36 tests
PASS.  Ruff clean.

Phase 6 may proceed.

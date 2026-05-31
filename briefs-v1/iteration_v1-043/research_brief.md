# iter-v1/043 — Research Brief

**Iteration**: iter-v1/043
**Date**: 2026-05-31
**TYPE**: EXPLORATION (FINAL cycle-5 — 10 of 10)
**Cycle**: 5, EXP 10 of 10
**Branch**: `iteration-v1/043`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

**iter-v1/043 — EXPLORATION cycle-5 #10/10 (FINAL pre-/044 CONFIRMATION)**
- **Axis**: LINK-only trend-scanning specialist — per-cohort isolation
  diagnostic that strips DOT from /036's LINK+DOT 2-cohort substrate to test
  whether LINK alone is load-bearing for the /036 OOS lift.
- **Axis family**: `per-cohort-specialization × labeling` REPEAT-COMBO (each
  family used twice across the prior-5 window — both under the 5+ rotation
  trigger; see §0.6).
- **Load-bearing purpose**: resolves the /044 CONFIRMATION substrate composition
  decision. /036 produced the largest single-seed OOS lift in v1 history
  (+1.7465 portfolio OOS Sharpe) on LINK+DOT. /039 then confirmed
  Sortino-and-trend-scan do NOT compound (HYBRID axis CLOSED). The remaining
  unresolved question for /044 is: of /036's two cohorts, is LINK the
  signal-load-bearing cohort, OR is the LINK+DOT PAIRING the load-bearing
  primitive? /043 answers this with a 1-cohort isolation experiment that
  exactly mirrors /036's labels/features/risk-gates/budget — only `--symbols
  LINKUSDT` differs from /036's invocation.

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION **10 of 10 — CADENCE COMPLETE**. After
  /043 closeout, /044 CONFIRMATION can launch. Prior 9 cycle-5 EXPLORATIONs:
  - /034 NEG-CLEAN LEARNED-NEG (feature-family basis_zscore_30)
  - /035 NEG-CAT-bundle bimodal (labeling trend-scanning 5-cohort)
  - /036 **PROMISING-CLEAN** (per-cohort-specialization LINK+DOT trend-scan;
    OOS Sharpe +1.7465 — single-seed v1 history high)
  - /037 PROMISING-CLEAN (loss-function Sortino 5-cohort)
  - /038 NEG-CATASTROPHIC EDA-vindicated (risk-primitive vol-ceiling)
  - /039 NEG-CATASTROPHIC HYBRID (loss-function × per-cohort —
    universe-dependence empirical proof; HYBRID axis CLOSED)
  - /040 feature-family composed (status: in flight / closing)
  - /041 labeling triple-barrier tighten (status: in flight / closing)
  - /042 model-arch LightGBM → XGBoost (status: in flight / closing)
- **NO kill-switches** (cycle-5 directive).
- **Wall-clock target**: ~15 min modal compute (anchored on /036 ~25 min × 0.5
  cohort-coverage; per-cohort Optuna re-optimization is the dominant cost and
  scales sub-linearly). Conservative band 12-25 min. Report layer ~3 min.
  Modal total ~18 min — well INSIDE skill default 2h cap.

---

## Section 0.6 — Axis-Family Rotation (v1-only) — REPEAT-COMBO JUSTIFICATION

- **Axis family**: `per-cohort-specialization × labeling` **REPEAT-COMBO**
  - `per-cohort-specialization` last used at /036 (3 iters ago at /042 vantage,
    but /040/041/042 have NOT yet been counted into rotation until catalog
    settles; conservative count = 3 iters ago)
  - `labeling` last used at /035 (4 iters ago) AND /041 (1 iter ago — counted
    once /041 closes)
- **Prior 5 EXPLORATION families** (going INTO /043, ordered most-recent → oldest):
  - iter-v1/042: `model-arch` (LightGBM → XGBoost)
  - iter-v1/041: `labeling` (triple-barrier tighten)
  - iter-v1/040: `feature-family` (composed regime_momentum_signed_5d)
  - iter-v1/039: `loss-function × per-cohort-specialization` HYBRID
  - iter-v1/038: `risk-primitive` (vol-ceiling)
- **Same-family counter in prior-5 window**:
  - `per-cohort-specialization`: appears in /039 HYBRID — counter = **1**
  - `labeling`: appears in /041 — counter = **1**
  - Composite REPEAT-COMBO counter: **3 each across full cycle-5 history**
    (per-cohort: /036, /039 HYBRID, /043; labeling: /035, /041, /043).
- **Rotation status**: **VALID (under 5+ saturation trigger)**. The Axis
  Rotation Discipline fires only when the LAST 5 EXPLORATIONs are ALL from
  the SAME family. /043's prior-5 disperses across 5 distinct families
  (model-arch/labeling/feature-family/HYBRID/risk-primitive), so monoculture
  is NOT armed. Per-cohort × labeling REPEAT-COMBO is permitted at counter
  3 each (well below 5+).
- **REPEAT-COMBO JUSTIFICATION (LOAD-BEARING)**:
  1. **/044 substrate-composition diagnostic**: cycle-5 has TWO PROMISING
     anchors — /036 (LINK+DOT trend-scan) at OOS +1.7465 and /037 (Sortino
     5-cohort) at OOS +0.8388. /039 already CLOSED the HYBRID question
     (universe-dependent, non-compoundable). The remaining unresolved
     question is whether /036's LINK+DOT substrate is decomposable into a
     load-bearing single cohort (LINK-only) or whether the PAIRING itself
     is the primitive. Without this answer, /044 cannot rationally select
     between LINK-only CONFIRMATION, LINK+DOT CONFIRMATION, or LINK+DOT
     with documented DOT risk-diversification attribution.
  2. **Direct precedent at /018** (LINK pure-isolation σ_t triple-barrier
     → PROMISING-INERT-FAV at /018 anchor; OOS Sharpe +0.9789, Δ +0.16 vs
     LINK-in-pool). The /018 precedent shows LINK-only IS productive but
     directionally only — the /018 magnitude was SMALL (+0.16). The EDA
     section anchors LINK-only intrinsic at +1.23 from /036's LINK trade
     subset (Section 1.1) — a substantially LARGER reference number than
     /018, which makes /043 a legitimate test of the LINK-only mechanism
     at the /036 substrate generation, NOT a knob-tuning rerun of /018.
  3. **No new src/ code**: dispatch elif + 3 pre-flight asserts + catch-all
     exclusion + tests. The implementation reuses /036's dispatch pattern
     with `--symbols LINKUSDT` restricting universe to 1 cohort. No new
     algorithmic surface area.
- **One-sentence rationale**: /043 is the canonical /044 substrate-composition
  diagnostic that distinguishes "/044-A = LINK-only" (if Δ ≥ 0 vs /036)
  from "/044-A = LINK+DOT pairing load-bearing" (if Δ < 0 vs /036) before
  multi-seed CONFIRMATION budget is committed — without this diagnostic /044
  burns multi-seed compute on a substrate decision that single-seed
  isolation can resolve in ~18 min.

---

## Section 1 — Hypothesis

**H1 (PRIMARY, 3 sentences)**: Running ONLY Model C' (LINK trend-scanning
specialist) with `--symbols LINKUSDT` at /036's exact label-mode + features +
risk-gates + Optuna budget produces an OOS portfolio Sharpe in the band
[+0.83, +1.53] centered on the intrinsic +1.23 anchor (from /036's LINK-only
trade-subset monthly Sharpe reconstruction; EDA §3) — a predicted Δ vs /036
(+1.7465) of −0.51 modal. The mechanism is **regression-toward-intrinsic**:
removing DOT exposes LINK's unbuffered monthly-return distribution (15-month
σ_monthly = 20.41% vs the buffered LINK+DOT portfolio σ) so portfolio σ
RISES while monthly mean PnL stays at LINK's ~7.26% — Sharpe shrinks even
under bit-identical Optuna trajectory. The Δ vs /036 directly arbitrates
the /044 substrate decision: Δ ≥ 0 ⇒ LINK alone is load-bearing (DOT was
diluting), modal Δ ∈ [−0.90, −0.35] ⇒ LINK+DOT pairing is load-bearing
(DOT diversifies risk at portfolio σ level), Δ < −0.90 ⇒ LINK-single
is INSUFFICIENT and the LINK+DOT pairing is the irreducible primitive.

**H1a (mechanism, EDA prior)**: EDA §3 reconstructs the LINK-only monthly
Sharpe from /036's OOS trades.csv (filter `symbol == 'LINKUSDT'`): 52 trades,
55.8% WR, +108.91% net PnL, 15-month monthly Sharpe **+1.2321** (mean +7.26%,
std 20.41%). This is the intrinsic anchor for /043 — same labels, features,
seed, n_trials budget direction; the ONLY axis change between /036's LINK
leg and /043 is that Optuna optimizes the LINK-only objective (no joint
LINK+DOT averaging). Sub-Optuna-trajectory drift is bounded at ±0.30 Sharpe
(/036's joint optimization could have selected a marginally different HP
basin than LINK-alone optimization, but the trend-scanning labels at single
seed=42 produce highly-similar per-cohort Optuna paths per the /036
attribution exercise). Bimodal LINK-only monthly distribution (6 negative
months max −23.54%, 9 positive months max +54.02% in 2025-08) confirms the
tail-risk exposure: removing DOT damping LIFTS portfolio σ structurally
even without trajectory drift.

**H1b (falsifiable)**: If F-AXIS #1 OOS Sharpe Δ vs /036 ≥ 0 (Δ ≥ 0 puts
/043 in the PROMISING-LINK-LOAD-BEARING band) then DOT was diluting /036's
portfolio Sharpe and /044-A pivots to LINK-only specialist (DROP DOT, accept
concentration risk). If Δ ∈ [−0.90, −0.35] (modal band, 55% prior) then
LINK contributes most of the OOS edge AND DOT provides risk-diversification
at the portfolio σ level — /044-A stays /036 LINK+DOT substrate with
documented per-cohort attribution. If Δ < −0.90 then LINK alone is
INSUFFICIENT and the LINK+DOT pairing is irreducible — /044-A multi-seed
LINK+DOT with explicit pairing-mandatory constraint.

---

## Section 1.5 — IS-Only Evidence (cites EDA verbatim)

### Section 1.5.1 — LINK-only monthly Sharpe reconstruction (EDA §2-§3)

From `briefs-v1/iteration_v1-043/eda_findings.md` Section 3 (15-month subset
of /036 OOS LINK trades):

| Quantity | Value | Source |
|---|---|---|
| LINK-only intrinsic OOS monthly Sharpe | **+1.2321** | EDA §3 |
| LINK-only mean monthly PnL | +7.26% | EDA §3 |
| LINK-only σ monthly PnL | 20.41% | EDA §3 |
| LINK OOS trades in /036 | 52 | EDA §3 |
| LINK OOS WR | 55.8% | EDA §3 |
| LINK OOS net PnL | +108.91% | EDA §3 |
| /036 portfolio OOS Sharpe (LINK+DOT) | +1.7465 | reports-v1/iteration_v1-036/comparison.csv |
| Intrinsic Δ vs /036 portfolio | **−0.5144** | EDA §1 derived |
| /018 LINK-only σ_t triple-barrier reference | +0.9789 | reports-v1/iteration_v1-018/comparison.csv |

### Section 1.5.2 — Bimodal LINK-only monthly distribution (EDA §3)

| Month | PnL % | Trades |
|---|---|---|
| 2025-03 | +10.02 | 1 |
| 2025-04 | −23.54 | 4 |
| 2025-05 | −16.07 | 4 |
| 2025-06 | +5.62 | 2 |
| 2025-07 | −11.75 | 5 |
| 2025-08 | **+54.02** | 4 |
| 2025-09 | −0.24 | 4 |
| 2025-10 | +24.51 | 4 |
| 2025-11 | +39.67 | 4 |
| 2025-12 | +3.64 | 3 |
| 2026-01 | −0.12 | 5 |
| 2026-02 | +4.10 | 1 |
| 2026-03 | −7.48 | 3 |
| 2026-04 | +15.67 | 5 |
| 2026-05 | +10.86 | 3 |

Sharpe-dominated by 2025-08 / 2025-11 wins; 2025-Q2 drawdown (−23.54 / −16.07
in consecutive months) is the tail-risk diversified-away by DOT in /036.

### Section 1.5.3 — Anchor correction vs task text

QR task text claimed "/018 LINK-only specialist precedent was PROMISING-CLEAN
at OOS Sharpe +1.46". This is **incorrect** — verified at
`reports-v1/iteration_v1-018/comparison.csv`:
- /018 OOS Sharpe: **+0.9789** (not +1.46)
- /018 Critic verdict: PROMISING-INERT-FAV (+0.16 Δ vs LINK-in-pool)

The /018 precedent supports Scenario A directionally only (Δ +0.16 was
POSITIVE) but at much smaller magnitude than the task text implied. This
lowers Scenario A prior probability from naive ~35-40% to 20% (EDA §4 §5).

---

## Section 2 — F-AXIS #1 — F1 OOS Sharpe Δ vs /036 anchor (+1.7465)

**Anchor**: /036 OOS Sharpe **+1.7465** (substrate baseline; same labels,
features, risk-gates, seed, n_trials, ENSEMBLE_SIZE as /043). NOT
BASELINE_V1's +0.6637 — H1b anchor selection is pre-registered per /039
closeout discipline (Phase 5.5 gate violation if anchor not pre-declared).

| Band | OOS Sharpe Δ vs /036 | OOS absolute | Verdict subtype |
|---|---|---|---|
| Δ ≥ 0 | ≥ +1.7465 | PROMISING-LINK-LOAD-BEARING (DOT was diluting) | EXPLORATION-PROMISING-CLEAN |
| −0.35 ≤ Δ < 0 | +1.40 to +1.75 | PROMISING-MARGINAL — LINK retains most edge | EXPLORATION-PROMISING-INERT-FAV |
| −0.90 ≤ Δ < −0.35 | +0.85 to +1.40 | **PAIRING-PARTIAL MODAL** — LINK is load-bearing signal, DOT diversifies risk | **EXPLORATION-INERT-PROBE-CONCLUSIVE** |
| −1.30 ≤ Δ < −0.90 | +0.45 to +0.85 | LINK-DEPENDS-ON-DOT — pairing irreducible | EXPLORATION-NEGATIVE |
| Δ < −1.30 | < +0.45 | NEG-CAT — single-cohort lottery / Optuna basin collapse | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal band prior (EDA + intrinsic-anchor integrated)**:

| Outcome | Probability | OOS Sharpe band |
|---|---|---|
| PROMISING-CLEAN (Δ ≥ 0) | **20%** | ≥ +1.75 |
| PROMISING-INERT-FAV (Δ ∈ [−0.35, 0)) | 17% | +1.40 to +1.75 |
| **PAIRING-PARTIAL MODAL (Δ ∈ [−0.90, −0.35))** | **38%** | **+0.85 to +1.40** |
| LINK-DEPENDS-ON-DOT (Δ ∈ [−1.30, −0.90)) | 17% | +0.45 to +0.85 |
| NEG-CAT (Δ < −1.30) | 8% | < +0.45 |

**Modal**: PAIRING-PARTIAL [Δ ∈ −0.90, −0.35)] at 38% weight. Combined
PROMISING mass 37% (PROMISING + PROMISING-INERT-FAV); PAIRING-PARTIAL +
LINK-DEPENDS combined NEG-vs-/036 mass 55%; NEG-CAT tail 8%.

**Predicted modal F1 outcome**: OOS bundle Sharpe **~+1.23** (intrinsic
anchor; Δ −0.52 vs /036, inside PAIRING-PARTIAL band).

**F1 modal band**: **[+0.83, +1.53]** (intrinsic ±0.30 Optuna drift envelope).

---

## Section 2.5 — NORMAL-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: composition of two previously-shipped, audited mechanisms with
  NO new src/ code:
  - `--label-mode trend_scanning` shipped at /035 (live in `lgbm.py`,
    `labeling.py`; trend-scanning grid (5, 8, 13, 21)).
  - `--symbols LINKUSDT` is a universe-restriction CLI flag that exercises
    the same dispatch-elif + pre-flight assert pattern proven at /036 and
    /018 (LINK-only previously dispatched at /018).
  - No Optuna search-space bounds change.
  - No new feature, no new labeling module, no new risk primitive.
  - The axis does NOT change Optuna's training-objective DOMAIN (per-row
    weights, per-row labels, per-row gradient inputs are unchanged from
    /036's LINK leg) — only the per-cell training pool composition (LINK
    only vs LINK+DOT) differs.
- **Distinction vs /036 (HIGH-RISK)**: /036 was HIGH-RISK because it
  STACKED two mechanisms (trend-scanning labels + per-cohort isolation
  from 5-cohort baseline). /043 is a 1-mechanism RESTRICTION of /036 (drop
  one of /036's 2 cohorts) — no NEW mechanism is composed.
- **Budget choice**: SINGLE-SEED=42 at v1 EXPLORATION standard
  (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42). Per v1 discipline,
  NORMAL-RISK + single-seed is the default cycle-5 EXPLORATION footing.
- **HIGH-RISK SINGLE-SEED counter**: NORMAL-RISK declaration resets the
  HIGH-RISK counter for this iteration.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (NO new src/ helper modules)

Per the AXIS specification: the LINK-only trend-scanning mechanism reuses
all previously-shipped infrastructure. Only `run_baseline_v1.py` needs a
dispatch elif + catch-all exclusion:

1. **EDIT `run_baseline_v1.py`**:
   - **Define** `V1_ITER043_UNIVERSE: tuple[str, ...] = ("LINKUSDT",)` near
     other `V1_ITERnnn_UNIVERSE` constants (alphabetical neighborhood after
     `V1_ITER042_UNIVERSE` if /042 has shipped, otherwise near
     `V1_ITER036_UNIVERSE`).
   - **Add `iteration_label == "v1-043"` dispatch branch** mirroring /036's
     dispatch structure (~50 lines, but dispatching ONLY Model C' LINK):
     - Pre-flight assert #1: `assert label_mode_arg == "trend_scanning"`
     - Pre-flight assert #2: `assert set(symbols) == set(V1_ITER043_UNIVERSE)`
       (i.e., `set(symbols) == {"LINKUSDT"}`)
     - Pre-flight assert #3: `assert optuna_objective_arg in ("sharpe", None)`
       (defends against /039 Sortino contamination of the substrate-isolation
       experiment; /043 must use the baseline Sharpe objective per /036
       canonical config)
     - Dispatch banner:
       `[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE: model=Model_C_LINK_only, label_mode={label_mode}, trend_scan_grid=(5,8,13,21), ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1, features={len(active_feature_columns)} cols`
     - Dispatch Model C' (LINK only): `run_model("C' (LINK + R1)",
       ("LINKUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, ...)`,
       threading `label_mode=label_mode_arg` into `run_model()`.
     - Combines results: `all_results = results_c043`,
       `_r5_model_results = [results_c043]`,
       `_post_dispatch_fi_strategies = [("Model_C_LINK_trend_scan_only", _strat_c043)]`.
   - **Add `"v1-043"`** to BASELINE catch-all exclusion tuple at line ~3686
     (per `/030 LESSON` `feedback_v1_dispatch_baseline_catchall_exclusion.md`).

2. **CONFIRM no other src/ edits required**:
   - `--label-mode trend_scanning` shipped /035 — live in `lgbm.py`,
     `labeling.py`.
   - Universe restriction via `--symbols` shipped from project inception.
   - Pre-flight assert pattern shipped /036, /037, /038, /039.

### Section 3.2 — Feature regeneration

**NONE.** V1_FEATURE_COLUMNS_PRUNED UNCHANGED (43-44 cols). Trend-scanning
uses only `close` from kline frames. Existing feature parquets for LINK at
`data/features/LINKUSDT_8h_features.parquet` are reused as-is. Feature
regen cost = 0 min.

### Section 3.3 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --symbols LINKUSDT \
  --label-mode trend_scanning \
  --pruned-features \
  --iteration 43 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  > logs/iter_v1_043_backtest.log 2>&1
```

Flag breakdown:
- `--symbols LINKUSDT` restricts universe to V1_ITER043_UNIVERSE (1 cohort).
- `--label-mode trend_scanning` reuses /035 labeling path with grid (5, 8, 13, 21).
- `--pruned-features` activates `V1_FEATURE_COLUMNS_PRUNED` (43-44 cols UNCHANGED).
- `--iteration 43` triggers the v1-043 dispatch branch.
- `--exploration --n-trials 18 --ensemble-size 3 --seeds 1` = v1 EXPLORATION standard.
- `--optuna-objective` flag NOT passed (defaults to `sharpe` per baseline) —
  pre-flight assert #3 catches accidental Sortino contamination.

### Section 3.4 — Symbols + models + config

| Item | Spec |
|---|---|
| Universe | V1_ITER043_UNIVERSE = (LINKUSDT,) — NEW 1-symbol constant |
| Models | Model C' (LINK only, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON). IDENTICAL to /036's LINK leg. Model E DOT, Model A pool, Model D LTC, Model G ETH SKIPPED. |
| Labels | `trend_scanning` with grid (5, 8, 13, 21) — IDENTICAL to /035, /036 |
| Optuna objective | `sharpe` (baseline default) — explicitly NOT Sortino |
| Features | V1_FEATURE_COLUMNS_PRUNED (43-44 cols) UNCHANGED |
| Sample weight | `abs_pnl` (baseline default) |
| Optuna bounds | `v1_pruned` (NOT axis016) |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 fix |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates | R1 ON for C'; R3 ON (cutoff 0.70, 16 features). R2 not applicable (DOT-only). |

### Section 3.5 — Test mandate (8+ tests per `/030 LESSON`)

`tests/test_iteration_v1_043.py` MUST include:

1. `test_v1_043_universe_constant_exists` — `V1_ITER043_UNIVERSE` =
   `("LINKUSDT",)`.
2. `test_v1_043_universe_subset_of_baseline` — LINKUSDT in V1_BASELINE_UNIVERSE.
3. `test_v1_043_dispatch_branch_exists` — `iteration_label == "v1-043"` path
   reachable (existence check via `inspect.getsource(run_baseline_v1)`).
4. `test_v1_043_pre_flight_label_mode_assert` — runner with
   `iteration_label="v1-043"` AND `--label-mode triple_barrier` raises
   AssertionError BEFORE compute (sample-instance test per /030 LESSON).
5. `test_v1_043_pre_flight_universe_assert` — runner with
   `iteration_label="v1-043"` AND `--symbols LINKUSDT,DOTUSDT` raises
   AssertionError BEFORE compute (defends against /036 contamination).
6. `test_v1_043_pre_flight_optuna_objective_assert` — runner with
   `iteration_label="v1-043"` AND `--optuna-objective sortino` raises
   AssertionError BEFORE compute (defends against /039 Sortino contamination).
7. `test_v1_043_in_baseline_catchall_exclusion` — line-~3686 tuple contains
   `"v1-043"` (catch-all guard per /030 LESSON).
8. `test_v1_043_dispatch_banner_emitted` — runner with `iteration_label="v1-043"`,
   `--label-mode trend_scanning`, `--symbols LINKUSDT` prints
   `[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE` banner with all
   required fields.
9. `test_v1_043_label_mode_threaded_to_link_model` —
   `run_model(label_mode="trend_scanning", ..., symbols=("LINKUSDT",))`
   constructs a `LightGbmStrategy` whose `.label_mode == "trend_scanning"`
   (real-instance attr access per /027 LESSON).
10. `test_v1_043_dispatches_only_link_model` — runner with
    `iteration_label="v1-043"` produces exactly 1 model result
    (`Model_C_LINK_trend_scan_only`); NO Model E DOT, NO Model A, NO Model D,
    NO Model G dispatched.

ALL 10 tests must pass at Phase 6 before backtest launch. Existing
`tests/strategies/ml/test_trend_scanning_label_mode.py` + `tests/test_iteration_v1_036.py`
MUST continue to pass.

### Section 3.6 — File changes (anticipated diff sizes)

| File | Change | Approx LOC |
|---|---|---|
| `run_baseline_v1.py` | V1_ITER043_UNIVERSE constant + dispatch branch + exclusion-tuple add | +60 −2 |
| `tests/test_iteration_v1_043.py` | NEW | ~200 |

Total: 2 files, ~260 lines net.

### Section 3.7 — Phase 6 step-sequence

1. Define `V1_ITER043_UNIVERSE: tuple[str, ...] = ("LINKUSDT",)`.
2. Add `iteration_label == "v1-043"` dispatch branch dispatching Model C'
   only, with `label_mode=label_mode_arg` threaded into the `run_model()` call.
3. Add `"v1-043"` to BASELINE catch-all exclusion tuple.
4. Add `tests/test_iteration_v1_043.py` (10 tests; spec in §3.5).
5. Run `uv run pytest tests/test_iteration_v1_043.py
   tests/test_iteration_v1_036.py tests/strategies/ml/test_trend_scanning_label_mode.py
   -v` — ALL must pass.
6. Launch backtest with CLI in §3.3.
7. After backtest: verify `[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE`
   banner; verify trades.csv contains ONLY LINKUSDT rows; verify
   `iteration_label="v1-043"` lines in log present.
8. Read `reports-v1/iteration_v1-043/comparison.csv` for F1 verdict.

---

## Section 4 — F-AXIS #2 through #5 (mechanism falsifiers)

### F-AXIS #2 — Wiring assert (dispatch + label-mode + universe)

**PASS criterion**: Phase 6 backtest log contains:
- `[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE` banner (1 line at dispatch)
- Per-cell `LABEL MODE: trend_scanning` banner ≥ 95% of cells (~100%)
- Per-trial logs show trend_scanning label inputs
- trades.csv contains ONLY LINKUSDT rows (asserted; any other symbol is
  TECHNICAL-FAILURE-SILENT)
- comparison.csv `iteration_label` column = "v1-043"

**FAIL** = silent fallback to BASELINE catch-all OR triple-barrier labels OR
multi-cohort dispatch → BLOCK-PENDING-FIX

### F-AXIS #3 — Per-symbol attribution (vs /036 LINK subset; LOAD-BEARING-LITE)

**PASS criterion**: LINK OOS PnL %, trade count, WR materially match the
LINK leg of /036 (±15pp PnL band acknowledging Optuna re-optimization drift):

| Metric | /036 LINK subset | /043 expected (modal) | Falsifier band |
|---|---|---|---|
| OOS PnL % | +108.91% | [+90%, +130%] modal +110% | < +60% → mechanism REFUTED |
| OOS trades | 52 | [40, 70] modal 50 | < 30 → TECHNICAL-FAILURE-SILENT-FALLBACK |
| OOS WR | 55.8% | [48%, 62%] modal 55% | < 42% → basin lottery |

**FAIL = LINK OOS PnL < +60%**: even at single-cohort Optuna, LINK didn't
retain the /036 lift — implies Optuna selected a degenerate basin OR the
/036 lift was 2-cohort-joint dependent.

### F-AXIS #4 — Bundle OOS Sharpe Δ band (= F1 verdict; pasted from §2 for completeness)

Conditional on F-AXIS #2 PASS and F-AXIS #3 not catastrophic, F1 verdict matrix
(§2 table) applies. Modal: PAIRING-PARTIAL [Δ ∈ −0.90, −0.35)] → OOS Sharpe
~+1.23 absolute.

### F-AXIS #5 — Trade-roster Jaccard vs /036 LINK subset (diagnostic)

**Expected band [50%, 90%]** — single-cohort Optuna at LINK alone should
recover MOST of /036's LINK trade roster (the labels/features/seed are
bit-identical; only the per-cell training pool composition changes —
removing DOT from Pool-A-equivalent / per-cohort cell does not relocate the
LINK trading basin unless Optuna explores wildly different HP regions).

- **PASS** (modal): Jaccard ∈ [50%, 90%] → LINK roster largely preserved;
  attribution clean.
- **FAIL = > 95% overlap** → TECHNICAL-FAILURE-SILENT-NO-OP (bit-identical
  to /036's LINK leg — no re-optimization happened) → BLOCK-PENDING-FIX.
- **FAIL = < 25% overlap** → BASIN-RELOCATION-ARTIFACT (LINK-only Optuna
  found a fundamentally different basin at single-seed); F1 verdict
  conditioned on basin lottery, /044 routing flagged for multi-seed
  validation.

---

## Section 5 — Configuration

(See §3.4 table above.) All other settings: BASELINE_V1 defaults.

---

## Section 6 — Wall-clock estimate

| Phase | Cost | Anchor |
|---|---|---|
| Data fetch | 0 min | LINK klines on disk |
| Feature regen | 0 min | LINK feature parquet on disk |
| Backtest compute | ~15 min modal | /036 ~25 min × 0.5 cohort-coverage; per-cohort Optuna sub-linear scaling |
| Report layer (DSR/PSR/etc) | ~3 min | standard |
| **Total modal** | **~18 min** | |
| **Conservative band** | 12-25 min | |
| **Hard cap** | 2h (skill default) | |

Honest overrun acceptable; no runtime kill-switch.

**Scaling derivation (5-step)**:
1. **Anchor precedent**: /036 ~25 min compute at 2-cohort EXPLORATION (n_trials=18,
   ENSEMBLE_SIZE=3, 2 syms, 44 cols, trend-scanning labels).
2. **Anchor label count**: /036 IS ~281 / OOS 105 (52 LINK + 53 DOT).
3. **/043 expected label count**: 1/2 = 50% of /036's cohort coverage.
   Expected IS ~120-160, OOS ~40-70.
4. **Scaling factors**: cohort count 0.5×; ENSEMBLE_SIZE 1.0×; n_trials 1.0×;
   outer seed 1.0×; feature count 1.0×. Composite: **0.5-0.6×**.
5. **Projection**: 25 × 0.55 = **~14 min modal**, conservative 12-25 min.

---

## Section 7 — Expected Report Shape

`reports-v1/iteration_v1-043/comparison.csv` will contain row-by-row LINK
metrics. Phase 7 evaluation requires a **3-way comparison table** comparing
/043 vs /036 (substrate baseline) vs BASELINE_V1 (sacred anchor):

| Metric | BASELINE_V1 | /036 LINK subset | /036 portfolio | /043 LINK-only | Δ /043 vs /036 portfolio | Δ /043 vs /036 LINK subset |
|---|---|---|---|---|---|---|
| IS Sharpe | +0.2829 | TBD | TBD | TBD | TBD | TBD |
| OOS Sharpe (portfolio/single) | +0.6637 | +1.2321 (intrinsic) | +1.7465 | TBD | TBD | TBD |
| IS trades | 621 | TBD | 281 | TBD | TBD | TBD |
| OOS trades | 189 | 52 | 105 | TBD | TBD | TBD |
| LINK OOS PnL% | +34.23 | +108.91 | n/a | TBD | n/a | TBD |
| OOS WR | 40.2% | 55.8% | TBD | TBD | TBD | TBD |
| OOS Max DD | 40.94% | n/a | TBD | TBD | TBD | n/a |
| OOS PSR_vs_1 | 0.079 | n/a | TBD | TBD | TBD | n/a |
| Jaccard vs /036 LINK roster | n/a | 1.000 | n/a | TBD | n/a | TBD |

Plus: per-month OOS PnL distribution (compare to EDA §3 LINK-only monthly
table for direct intrinsic-anchor validation), Optuna best_params per training
month (sanity vs /036), feature-importance top-5 (sanity vs /036).

---

## Section 8 — Path Forward Predictions (/044 routing — EXPLICIT decision tree)

Per Critic constructive-Path-Forward discipline + /044 substrate composition
decision binding on /043:

```
IF /043 OOS Sharpe ≥ +1.75 (Δ ≥ 0 vs /036 portfolio):
    → Scenario A confirmed (PROMISING-LINK-LOAD-BEARING)
    → /044-A CONFIRMATION = LINK-ONLY specialist (multi-seed)
       Spec: --symbols LINKUSDT --label-mode trend_scanning
             --pruned-features --seeds 2 --n-trials 35 --ensemble-size 5
    → DOT DROPPED from substrate; concentration risk noted in Phase 7 diary
    → /044-B = /037 multi-seed Sortino 5-cohort as SEPARATE CONFIRMATION
      (per /039 closeout LOCK)

ELIF /043 OOS Sharpe ∈ [+1.40, +1.75) (Δ ∈ [−0.35, 0) vs /036):
    → Scenario A-marginal (PROMISING-INERT-FAV)
    → /044-A CONFIRMATION = LINK+DOT pairing multi-seed
       Spec: --symbols LINKUSDT,DOTUSDT --label-mode trend_scanning
             --pruned-features --seeds 2 --n-trials 35 --ensemble-size 5
    → DOT retained as risk-diversifier; LINK leg's intrinsic Sharpe near-equal
      to portfolio Sharpe means DOT-diversification benefit is < 0.35 — bundle
      decision can go either way at multi-seed; default to /036's substrate
    → Phase 7 diary records "/043 single-cohort isolation showed LINK retains
      most of the /036 lift; DOT diversification benefit measured at <0.35;
      bundle stayed at /036 substrate for /044-A multi-seed"

ELIF /043 OOS Sharpe ∈ [+0.85, +1.40) (Δ ∈ [−0.90, −0.35) vs /036, MODAL):
    → Scenario B confirmed (PAIRING-PARTIAL)
    → /044-A CONFIRMATION = /036 LINK+DOT pairing multi-seed
       Spec: --symbols LINKUSDT,DOTUSDT --label-mode trend_scanning
             --pruned-features --seeds 2 --n-trials 35 --ensemble-size 5
    → Phase 7 diary records LINK contributes most of the OOS edge but DOT
      provides 0.35-0.90 Sharpe via risk-diversification at portfolio σ level
    → /044-B = /037 multi-seed Sortino 5-cohort SEPARATE

ELIF /043 OOS Sharpe ∈ [+0.45, +0.85) (Δ ∈ [−1.30, −0.90) vs /036):
    → Scenario C confirmed (LINK-DEPENDS-ON-DOT)
    → /044-A CONFIRMATION = /036 LINK+DOT pairing multi-seed with
      "PAIRING-MANDATORY" attribution note
    → Pairing is irreducible primitive at v1; /044-A diary documents this
      as a substrate constraint

ELSE (Δ < −1.30, /043 OOS Sharpe < +0.45):
    → Scenario D confirmed (NEG-CAT — single-cohort lottery or basin collapse)
    → /044-A CONFIRMATION = /036 LINK+DOT pairing multi-seed (forced)
    → /045 EXPLORATION = LINK-only multi-seed=2 validation to disambiguate
      lottery vs basin collapse
    → Per-cohort-specialization × labeling REPEAT-COMBO axis-family
      saturation note for cycle-6 planning
```

**Cross-cutting**: regardless of /043 outcome, /044-B (separate Sortino
5-cohort CONFIRMATION) is LOCKED per /039 closeout — /043 does NOT alter
that commitment. /043's role is binding ONLY on /044-A substrate composition.

---

## Section 9 — Behavioral-effect predictor

Per `feedback_axis_saturation_predictor.md`: predict observable behavioral
effects with falsifier triggers.

**Predicted IS trade count**: range [120, 180], modal **~150** (anchor /036
IS ~281 / 2 cohort-coverage = ~140, with Optuna re-optimization ±15%).

**Predicted OOS trade count**: range [40, 70], modal **~52** (anchor /036
LINK subset 52 OOS trades; same labels/features/seed produce highly-similar
trade-emission rate at single-cohort Optuna).

**Predicted LINK OOS PnL %**: range [+90%, +130%], modal **+110%** (anchor
/036 LINK subset +108.91%; minor drift from Optuna re-optimization).

**Predicted LINK OOS WR**: range [48%, 62%], modal **55%** (anchor /036
LINK subset 55.8%).

**Predicted bundle OOS Sharpe Δ vs /036**: range [−0.90, +0.30], modal
**−0.52** (intrinsic anchor +1.23 vs /036 +1.7465). MODAL inside
PAIRING-PARTIAL band.

**Predicted F-AXIS #5 Jaccard vs /036 LINK subset**: range [50%, 90%],
modal **70%** (single-cohort Optuna re-optimization rotates ~30% of trades
from joint optimization; the rest are bit-identical).

**Predicted OOS Max DD**: range [25%, 50%], modal **~35%** (LINK-only
σ_monthly = 20.41% unbuffered by DOT; structurally HIGHER DD than /036
portfolio).

**Falsifier triggers**:
1. IS trades < 80 OR OOS trades < 30 → TECHNICAL-FAILURE-SILENT-FALLBACK
   → BLOCK-PENDING-FIX.
2. F-AXIS #5 Jaccard > 95% → TECHNICAL-FAILURE-SILENT-NO-OP (no
   re-optimization happened) → BLOCK-PENDING-FIX.
3. F-AXIS #5 Jaccard < 25% → BASIN-RELOCATION-ARTIFACT (LINK-only Optuna
   landed in fundamentally different basin); F1 verdict conditioned on
   basin lottery — /044 routing decision flagged for multi-seed at /045+.
4. F-AXIS #2 wiring fails (banner missing OR triple-barrier labels OR
   non-LINK trades) → BLOCK-PENDING-FIX.
5. LINK OOS PnL < +60% (vs /036 LINK subset +108.91%) → mechanism REFUTED;
   reclassify even if F1 marginally in band.

**Mechanism failure scenario (PREDICTED FAILURE MODE)**: the most plausible
failure mode is that /043 produces an OOS Sharpe in the PAIRING-PARTIAL band
(+0.85, +1.40) at modal +1.23 — confirming the EDA-derived intrinsic anchor
and demonstrating that DOT's contribution to /036 was risk-diversification
at the portfolio σ level (not signal addition). This is the EXPECTED outcome
(38% prior) — it is the modal verdict, NOT a failure of the experiment but
a CONCLUSIVE answer to the /044 substrate decision in favor of LINK+DOT
pairing. The "failure" framing applies only if Scenario D fires (Δ < −1.30,
8% tail) — single-cohort Optuna basin collapse at single-seed=42 — in which
case /045 multi-seed=2 LINK-only validation disambiguates lottery vs
true-LINK-insufficiency.

---

## Section 10 — Anti-Cheating Self-Check

- [x] EDA reads IS-only (`reports-v1/iteration_v1-036/in_sample/trades.csv`
      for LINK-leg reconstruction reference; the /036 OOS trades.csv consumed
      ONLY as a REFERENCE POINT for the intrinsic anchor — already-measured
      values from /036's Phase 7 evaluation, NOT new OOS measurements
      derived during /043's Phase 1-5).
- [x] No parameter tuning on OOS data — all /043 config (n_trials=18,
      ENSEMBLE_SIZE=3, seed=42, label_mode=trend_scanning) are v1 EXPLORATION
      standard defaults inherited from /036.
- [x] OOS_CUTOFF_DATE = 2025-03-24 SACRED — unchanged.
- [x] training_months = 24 SACRED — unchanged.
- [x] IS window NOT trimmed; full 2020-01 → 2025-03-23 used at backtest.
- [x] No new EDA scripts beyond `analysis/iteration_v1-043/eda.py` (Phase 1
      deliverable, IS-and-already-published-OOS-as-reference per file path).
- [x] Hypothesis falsifiers F1-F5 pre-registered above Phase 6 dispatch.
- [x] H1b /036-anchor selection pre-registered per /039 closeout
      Phase 5.5 gate discipline.
- [x] Anchor correction documented (task-text "+1.46 /018 LINK" refuted;
      actual /018 OOS Sharpe +0.9789).

---

## Section 11 — LM Master Response Map (Phase 4.5)

**Status**: LM Master Phase 4.5 advisor (`briefs-v1/iteration_v1-043/lgbm_advisor.md`)
has NOT been emitted at the time of brief authoring (file not present in
`briefs-v1/iteration_v1-043/`). Per v1 LM Master discipline, when the
advisor is delayed/absent, the QR brief must EXPLICITLY note the absence
and proceed using EDA + prior LM Master directional guidance from adjacent
iterations (here: /036 LM Master, /039 LM Master, /042 LM Master) as the
substitute prior.

**Substitute prior synthesis (from adjacent LM Master files)**:

| # | Adjacent-LM-Master signal | /043 brief response |
|---|---|---|
| 1 | /036 LM Master: "Per-cohort isolation on trend-scan substrate at single-seed n_trials=18 is search-density-adequate (n_eff ~12-15 per cohort) and basin-migration risk is MITIGATED by Jaccard diagnostic." | **ADOPTED** at F-AXIS #5 (Jaccard vs /036 LINK subset; expected [50%, 90%]). |
| 2 | /039 LM Master: "Anchor on /036 substrate Sharpe (NOT BASELINE_V1) when /036 is the direct substrate baseline; failure to pre-register anchor is a Phase 5.5 gate violation." | **ADOPTED** at §2 F-AXIS #1 (anchor explicitly +1.7465 /036 portfolio; pre-registered per H1b in §1). |
| 3 | /042 LM Master (model-arch family): "EDA-derived intrinsic anchor (subset Sharpe reconstruction) is the authoritative prior for restriction experiments, superseding any prior-iteration distributional priors." | **ADOPTED** — modal +1.23 intrinsic anchor from EDA §3 is the load-bearing prior at §2 (38% MODAL on PAIRING-PARTIAL band). |
| 4 | General LM Master pattern: single-cohort isolation experiments at n_trials=18 / ENSEMBLE_SIZE=3 / single-seed=42 are search-adequate when the substrate baseline (/036 here) was itself measured at the same config. | **ADOPTED** at §3.4 — config IDENTICAL to /036's per-cohort cell; no axis to enlarge. |
| 5 | LM Master discipline: pre-flight assert HIGH-RISK contamination (e.g., accidental Sortino flag, accidental triple-barrier flag, accidental multi-cohort flag). | **ADOPTED** at §3.1 — 3 pre-flight asserts (label-mode, universe set-equality, optuna-objective). |

If `briefs-v1/iteration_v1-043/lgbm_advisor.md` is emitted before Phase 6
dispatch, this Section 11 will be **APPENDED** with a per-recommendation
response map. The Phase 5.5 gate may BLOCK if the advisor's emitted
recommendations conflict materially with the brief's structure; in that
case a QR follow-up amendment is required before Phase 6.

---

## Section 11.5 — Pre-Registered Failure-Mode Prediction

**Most plausible failure scenario at single-seed=42 EXPLORATION budget**:
single-cohort LINK Optuna re-optimization at n_trials=18 / ENSEMBLE_SIZE=3
lands in a basin near-identical to /036's LINK-leg basin (F-AXIS #5 Jaccard
modal 70%) — Optuna re-explores the same HP region because labels, features,
seed, and gradient direction are bit-identical to /036's LINK cell. The
resulting OOS Sharpe equals the EDA-derived intrinsic anchor +1.23 ±0.30
(F1 modal +1.23, Δ vs /036 portfolio = −0.52, inside PAIRING-PARTIAL MODAL
band [−0.90, −0.35)). This is the EXPECTED outcome and represents a
CONCLUSIVE diagnostic — not a failure of the experiment but a clean
resolution of the /044 substrate question.

**Gates that should catch genuine failure**:
- F-AXIS #2 wiring assert: silent fallback to BASELINE catch-all OR
  multi-cohort dispatch → BLOCK-PENDING-FIX.
- F-AXIS #5 Jaccard < 25%: basin-relocation-artifact → /044 routing flagged
  for multi-seed validation at /045+.
- F-AXIS #5 Jaccard > 95%: silent-no-op (no re-optimization) →
  BLOCK-PENDING-FIX.
- F-AXIS #3 LINK OOS PnL < +60%: mechanism REFUTED — single-cohort Optuna
  selected degenerate basin OR /036 lift was 2-cohort-joint dependent
  (the latter would be a structural finding documented at /044 routing).

**Failure metrics signature for Scenario D (8% tail)**: IS Sharpe < 0, OOS
Sharpe < +0.45, OOS Max DD > 50%, LINK OOS PnL < +30%, F-AXIS #5 Jaccard
< 25%. /045 multi-seed=2 LINK-only validation disambiguates lottery vs
true insufficiency.

---

## Section 11.6 — Locked Numerical MERGE/NO-MERGE Thresholds (/044 routing)

EXPLORATION at single-seed = NO direct MERGE. MERGE eligibility requires
/044 multi-seed CONFIRMATION. Pre-registered numerical thresholds for
/043 routing to /044 substrate selection:

| /043 outcome (OOS Sharpe absolute) | OOS Sharpe Δ vs /036 (+1.7465) | /044-A spec |
|---|---|---|
| **≥ +1.75** | **Δ ≥ 0** PROMISING-LINK-LOAD-BEARING | /044-A = LINK-ONLY multi-seed (`--symbols LINKUSDT --label-mode trend_scanning --pruned-features --seeds 2 --n-trials 35 --ensemble-size 5`); DOT DROPPED; concentration cap exception with explicit Phase 7 justification |
| **+1.40 to +1.75** | **Δ ∈ [−0.35, 0)** PROMISING-INERT-FAV | /044-A = LINK+DOT pairing multi-seed (same spec, `--symbols LINKUSDT,DOTUSDT`); LINK is the load-bearing leg; DOT diversification benefit < 0.35 measured at /043 |
| **+0.85 to +1.40** | **Δ ∈ [−0.90, −0.35) MODAL** PAIRING-PARTIAL | /044-A = LINK+DOT pairing multi-seed (same spec); diary documents LINK contributes most of OOS edge, DOT provides 0.35-0.90 Sharpe via portfolio-σ diversification |
| **+0.45 to +0.85** | **Δ ∈ [−1.30, −0.90)** LINK-DEPENDS-ON-DOT | /044-A = LINK+DOT pairing multi-seed with PAIRING-MANDATORY constraint; pairing is irreducible primitive |
| **< +0.45** | **Δ < −1.30** NEG-CAT (8% tail) | /044-A = LINK+DOT pairing multi-seed forced; /045 EXPLORATION = LINK-only multi-seed=2 disambiguation |

**ABSOLUTE MERGE GATES** (apply at /044 CONFIRMATION ONLY, not /043):
IS Sharpe > 1.0 AND OOS Sharpe > 1.0 AND OOS/IS ratio ≥ 0.5 AND OOS
trades ≥ 130 AND DSR > 0.95 AND PBO < 0.40 AND PSR > 0.95 AND top-symbol
concentration ≤ 30% of OOS PnL. /043 EXPLORATION does NOT evaluate against
these.

**Cross-cutting LOCK** (from /039 closeout): regardless of /043 outcome,
/044-B = /037 multi-seed Sortino 5-cohort SEPARATE CONFIRMATION is LOCKED.
/043 binds /044-A substrate composition only.

---

## Section 11.7 — Library Stack Declaration

NO external ML-finance libraries used in this iteration. Standard stack only:
- **LightGBM** (existing project dependency, no version change)
- **Optuna** (existing, no version change)
- **NumPy / Pandas / Polars** (existing, no version change)

NOT used in /043: mlfinlab, mlfinpy, pypbo, fracdiff, financial-machine-learning,
statsmodels (beyond existing ADF test usage), XGBoost (/042 axis, deliberately
isolated from /043).

The trend-scanning labeling implementation at
`src/crypto_trade/strategies/ml/labeling.py:_trend_scan_label` (shipped at
/035) uses only NumPy primitives (np.polyfit, np.std, masked-array slicing).
No new library dependency.

---

## Section 12 — Phase 5.5 Dispatch Readiness Checklist

- [x] Brief Section 0.0 banner declares EXPLORATION cycle-5 #10/10 FINAL.
- [x] Brief Section 0.5 cadence position: 10/10 — CADENCE COMPLETE pre-/044.
- [x] Brief Section 0.6 REPEAT-COMBO JUSTIFIED with substrate-composition
      diagnostic rationale + /044 routing implication.
- [x] Brief Section 1 hypothesis: 3-sentence (H1) + mechanism (H1a) +
      falsifier (H1b) + /036-anchor pre-registered.
- [x] Brief Section 2 F-AXIS #1 verdict matrix with band probabilities +
      modal prediction + /036-anchor explicit (NOT BASELINE_V1).
- [x] Brief Section 2.5 NORMAL-RISK declared with mechanism rationale +
      SINGLE-SEED budget choice justified.
- [x] Brief Section 3 implementation: NO new src/ helper modules; dispatch
      elif + 3 pre-flight asserts + catch-all exclusion + 10 tests.
- [x] Brief Section 3.3 CLI invocation: `--symbols LINKUSDT --label-mode
      trend_scanning --pruned-features --iteration 43 --exploration --n-trials
      18 --ensemble-size 3 --seeds 1`.
- [x] Brief Section 4 F-AXIS #2-#5 falsifiers (wiring, per-symbol PnL/trade,
      bundle Sharpe, Jaccard).
- [x] Brief Section 5 + 6 configuration + wall-clock estimate (~18 min modal).
- [x] Brief Section 7 expected report shape: 3-way comparison /043 vs /036
      LINK-subset vs /036 portfolio vs BASELINE_V1.
- [x] Brief Section 8 path-forward predictions with EXPLICIT /044 routing
      decision tree per outcome quadrant.
- [x] Brief Section 9 behavioral-effect predictor with falsifier triggers.
- [x] Brief Section 10 anti-cheating self-check (incl. /018 anchor correction).
- [x] Brief Section 11 LM Master Response Map — advisor absence DOCUMENTED;
      substitute prior synthesis from adjacent LM Master files.
- [x] Brief Section 11.5 Pre-Registered Failure-Mode Prediction.
- [x] Brief Section 11.6 Locked Numerical MERGE/NO-MERGE Thresholds with
      explicit /044 substrate routing per outcome band.
- [x] Brief Section 11.7 Library Stack Declaration.
- [x] `/030 LESSON`: `"v1-043"` added to baseline catch-all exclusion tuple
      planned in §3.1.

Ready for Phase 5.5 gate review.

---

**END OF BRIEF**

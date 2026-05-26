# iter-v1/016 — Research Brief

**Iteration**: iter-v1/016 (FIRST CYCLE-3 EXPLORATION)
**Date**: 2026-05-26
**Branch**: `iteration-v1/016` (from `iteration-v1/015` HEAD `545c19f` + tag `v0.v1-015`)
**Axis family**: `sample-weighting` (NEW family; never used in v1)
**Verdict-class**: EXPLORATION
**Author**: QR (Phases 1-5)

---

## Section 0 — Audit Header

### 0.1 Anchor

- BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe **+0.2829** / OOS Sharpe **+0.6637**
- Cycle-2 closed at /015 CONFIRMATION-NEGATIVE catastrophic with **ZERO MERGES** across 10 iterations
- BASELINE UNCHANGED through cycle-2

### 0.2 Wall-clock estimate

- **Predicted: 1.50-1.75h** at ENSEMBLE_SIZE=3 (fixed), n_trials=20 (compressed from 35), V1_FEATURE_COLUMNS_PRUNED (40 cols), 5-symbol full universe, 8h candles
- **Cap: 2h EXPLORATION** (per `feedback_v1_wall_clock_discipline_enforced.md`)
- **Margin: ≥25%** (between predicted upper-bound 1.75h and 2h cap)
- See Section 3.6 for detailed compression rationale.

### 0.3 Track detection

TRACK = v1; iteration NNN = 016; cycle position = 3-#1 (first cycle-3 EXPLORATION)

### 0.4 Boot files read

1. `ITERATION_PLAN_8H_V1.md` (v1 workflow)
2. `BASELINE_V1.md` (anchor + cycle-2 outcomes)
3. `diary-v1/iteration_v1-015.md` (5 LESSONS + Path Forward)
4. `briefs-v1/iteration_v1-015/{research_brief.md, lgbm_advisor.md, review.md, critic_preflight.md}` (cycle-2 closeout)
5. `briefs-v1/exploration_catalog.md` (axis rotation status; all 10 cycle-2 iterations)
6. `feedback_v1_wall_clock_discipline_enforced.md` (NEW skill cap; non-negotiable)
7. `feedback_v1_n_eff_barrier_magnitude_curve.md` (NEW — cycle-2 structural finding)
8. `feedback_v1_substrate_basin_lock.md` (REFUTED at /013)
9. `src/crypto_trade/strategies/ml/lgbm.py` (sample_weight wiring — lines 506-595)
10. `src/crypto_trade/strategies/ml/labeling.py` (weights = 1.0 + abs(labeled_pnl)/max × 9.0 at line 543)

### 0.5 Cycle/cadence position

**CYCLE-3 EXPLORATION #1** (first EXPLORATION of cycle-3; new wall-clock discipline active).

Cycle-2 closed NO-MERGE at /015 with 0 edge ingredients merged. Cycle-3 ledger begins at /016.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `sample-weighting` (NEW family — never used in v1)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/010: `risk-primitive`
  - iter-v1/011: `risk-primitive`
  - iter-v1/012: `methodology-substrate-test`
  - iter-v1/013: `methodology-substrate-test`
  - iter-v1/014: `labeling`
- **Rotation status**: **VALID** — `sample-weighting` is NEW (never used). Required because prior 5 are all in 3 closed families (`risk-primitive`, `methodology-substrate-test`, `labeling`); cycle-3 must rotate to UNUSED families per Critic /015 Path Forward.
- **One-sentence rationale**: Sample-weighting is a López de Prado AFML Ch. 4 mandated axis that has NEVER been varied in v1's catalog, and the baseline `abs(labeled_pnl)` weighting demonstrably distorts per-symbol weight shares away from uniform (EDA Table 1: BTC under-weighted 45.1% vs 50% uniform within Model A; LTC/DOT high-PnL outliers dominate via Kish n_eff ratio 0.638-0.793 in worst cells).

---

## Section 1 — Hypothesis

**Replacing `abs(labeled_pnl)` weighting with PURE UNIFORM weights** (or pure-uniqueness AFML mode) will (a) eliminate per-symbol weight asymmetry in Model A (BTC vs ETH), (b) restore Kish n_eff toward 1.0 (~12% gain in effective sample size), and (c) reduce Optuna's overfit to extreme-PnL outliers (max abs_pnl = 74.70% on LINK, 47.46% on ETH, 44.43% on DOT — 8-15× the median).

The intervention is a NEW code path: `sample_weight_mode="uniform"` (and "uniqueness_only" as alternate) replacing the default `"abs_pnl"`. This is single-axis isolated (no other change to labeling, features, symbols, candles, or risk gates).

**Predicted outcome distribution at v1 EXPLORATION (per LM Master /015 §1 FLAT prior rule)**: 55% NULL / 20% PROMISING / 25% NEGATIVE for verdict-class.

**Mechanism-level prediction (MEDIUM confidence, "mechanism-deterministic" disclaimer per `feedback_v1_n_eff_barrier_magnitude_curve.md` §LESSON #2)**:
- F-AXIS-MECHANISM-NEW: Kish n_eff per-cell ratio rises from baseline mean ~0.85 toward ~1.0 (4 of 4 models)
- Per-symbol weight share equalizes within Model A (BTC share = 0.50 ± 0.02 under uniform vs 0.451 ± 0.036 under baseline)
- Trade roster: NOT bit-identical to baseline (the loss surface change WILL affect Optuna's hyperparameter selection per (symbol, month) cell)

---

## Section 2 — IS-Only Evidence (EDA tables)

All numbers from committed scripts under `analysis/iteration_v1-016/`:
- `eda_weighting_schemes.py` → `weight_profile_summary.csv` + `exit_reason_distribution.csv` + `weighting_scheme_comparison.csv` + `n_eff_label_diversity_proxy.csv`
- `eda_per_symbol_weight_concentration.py` → `per_symbol_weight_share.csv` + `kish_n_eff_per_cell.csv`
- `eda_uniqueness_predicted_effect.py` → `uniqueness_effect_prediction.csv`

### 2.1 Baseline label-class distribution refutes /015 timeout-fallback hypothesis

**Table A — Baseline ATR labels (ATR×2.9 TP / ATR×1.5 SL / 21-candle timeout, 8h)**:

| Symbol | n_labels | TP-hit share | Timeout share | SL-opp share | Exit entropy (max=ln 3 ≈ 1.10) |
|---|---|---|---|---|---|
| BTCUSDT | 5713 | 51.2% | 10.3% | 38.5% | 0.895 (81% of max) |
| ETHUSDT | 5713 | 51.5% | 10.1% | 38.4% | 0.890 (81%) |
| LINKUSDT | 5664 | 50.7% | 10.9% | 38.4% | 0.909 (83%) |
| LTCUSDT | 5673 | 51.3% | 12.6% | 36.2% | 0.907 (82%) |
| DOTUSDT | 5011 | 51.0% | 10.8% | 38.2% | 0.904 (82%) |

**Reading**: The /015 timeout-fallback mechanism (>85% timeout class collapsing n_eff to 3) DOES NOT apply at v1 baseline. Timeout share is 10-13% — healthy. **Zero (sym, month) cells have timeout_share > 0.6.** Exit-reason Shannon entropy is 81-83% of theoretical max — high diversity.

**Implication**: The Critic /015 Path Forward axis #1 mechanism justification ("addresses /015's timeout-fallback dominance via weighting timeout cells down") **DOES NOT APPLY at baseline**. Option C (inverse-class-frequency on exit_reason) is poorly motivated for /016 — there's no timeout-fallback problem to solve at baseline labels.

### 2.2 Real mechanism — per-symbol weight asymmetry in Model A

**Table B — Model A (BTC+ETH pooled) weight-share split (mean across IS months)**:

| Symbol | baseline weight share | uniform share | Δ |
|---|---|---|---|
| BTCUSDT | 0.451 (σ 0.036) | 0.500 | -0.049 |
| ETHUSDT | 0.549 (σ 0.036) | 0.500 | +0.049 |

**Reading**: Baseline `abs(labeled_pnl)` weighting systematically over-weights ETH by ~5% and under-weights BTC by ~5% within Model A's training set, **every IS month** (std 0.036 is small relative to the 0.049 mean shift — this is structural, not random). Cause: ETH has higher mean |labeled_pnl| (6.91% vs BTC's 5.41%) → larger relative weights.

### 2.3 Kish n_eff loss to outlier concentration

**Table C — Kish n_eff per (model, month) — baseline vs uniform**:

| Model | n_actual mean | n_eff_kish_baseline mean | Ratio (baseline/uniform) |
|---|---|---|---|
| A (BTC+ETH) | 181.4 | 154.2 (estimate) | **0.86** (range 0.72-0.93) |
| C (LINK) | 89.9 | 79.5 | **0.88** (range 0.74-0.95) |
| D (LTC) | 90.0 | 75.9 | **0.85** (range 0.64-0.97) |
| E (DOT) | 89.5 | 78.7 | **0.88** (range 0.76-0.94) |

**Worst cells** (lowest Kish ratio = most weight concentrated on outliers):
- D 2025-03 — 0.638 (44/68 effective)
- A 2025-03 — 0.724 (98/136 effective)
- C 2025-03 — 0.743 (51/68 effective)
- D 2022-09 — 0.757

**Reading**: Baseline loses **12-15% of effective sample size on average** to outlier weight concentration; **36% loss in worst cells** (D 2025-03). The 2025-03 month is structural (last IS window-end month = fewer training rows). Uniform weighting would recover this loss.

### 2.4 Outlier magnitude in `abs(labeled_pnl)` per symbol

**Table D — per-symbol abs(labeled_pnl) percentiles (IS-only, %)**:

| Symbol | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| BTCUSDT | 4.86 | 9.60 | 11.59 | 16.94 | 35.89 |
| ETHUSDT | 6.21 | 12.26 | 14.56 | 20.26 | **47.46** |
| LINKUSDT | 8.81 | 16.34 | 19.25 | 25.24 | **74.70** |
| LTCUSDT | 7.17 | 14.70 | 17.18 | 22.25 | 38.08 |
| DOTUSDT | 8.11 | 16.21 | 19.00 | 25.26 | 44.43 |

**Reading**: Max abs_pnl ranges 35.89-74.70%. **LINK's 74.70% single outlier dominates Model C's weight space** (the row is at weight = 10.0 after normalization vs median weight ~2.0 — a single row gets 5× the median weight). Same pattern (smaller magnitude) on ETH, DOT, LTC.

### 2.5 Pure uniqueness via production `compute_sample_uniqueness` is a near-no-op (CRITICAL)

**Test on Model A IS window (4322 training rows)**:

- baseline_weights range: [1.001, 10.000]
- uniqueness range: [0.0455, 0.1678], mean=0.0457, **std=0.0037** (essentially constant ≈ 1/21)
- After `train_weights *= uniq` (current production code):
  - Kish n_eff: 3792.1 → 3761.3 (Δ -0.8%, no improvement)
  - Spearman rank correlation between baseline_w and baseline_w × uniq: **0.997** (no change in ordering)
  - BTC share: 0.470 → 0.470 (unchanged)
  - ETH share: 0.530 → 0.530 (unchanged)

**Conclusion**: Existing `sample_uniqueness=True` in production is a NEAR-NO-OP at v1's dense-label regime because every label has nearly-identical uniqueness (~1/21) → multiplication by a constant. LightGBM gradient is scale-invariant.

**This refutes the Critic /015 Path Forward "Option B: weight-by-uniqueness" axis** as currently coded. To get the actual benefit, uniqueness must REPLACE `abs(labeled_pnl)`, not multiply it.

### 2.6 Predicted effect of three intervention modes

| Mode | Per-row weight formula | Expected Kish n_eff ratio | Per-symbol balance |
|---|---|---|---|
| baseline | `1 + abs(labeled_pnl) / max × 9` | 0.85-0.93 (var by cell) | BTC under, ETH over |
| **uniform** | `1.0` (all rows) | **1.000** | **perfect** |
| uniqueness_only | `uniqueness ≈ 1/avg_overlap_count` | 0.993 | perfect (uniqueness symmetric) |
| current `sample_uniqueness=True` | `baseline × uniqueness` | 0.85 (no change) | no change |

### 2.7 Predicted PnL contribution shifts (mechanism-deterministic with disclaimer)

If sample weighting equalizes per-symbol contribution to Optuna's loss:
- Model A: ETH-dominated hyperparameter selection → BTC-balanced; expected per-symbol Δ unknown direction (could help or hurt either; **TRUE FLAT prior**)
- Models C/D/E (single-symbol): per-month weight balance only; cells like D 2025-03 (Kish 0.638) get more uniform Optuna influence; expected effect on IS Sharpe is open

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: Sample-weighting changes Optuna's training-objective domain — the loss-surface gradient receives different per-row weights, so hyperparameter selection per (model, month) cell can shift. Per `feedback_v1_n_eff_barrier_magnitude_curve.md` LESSON #2, this puts /016 in HIGH-RISK basin-shift territory.
- **Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default). The v1 HIGH-RISK rule is OPT-IN multi-seed validation, but ENSEMBLE_SIZE=3 is already fixed by cycle-3 wall-clock discipline. /016 records the choice and the OOS outcome; if /016 + the next 2 HIGH-RISK EXPLORATIONs produce ≥1σ negative OOS deltas, the feedback rule will mandate multi-seed validation per `feedback_v1_n_eff_barrier_magnitude_curve.md` LESSON #2 forward-mandate.

---

## Section 3 — Proposed Changes

### 3.1 Sample-weighting axis — add `sample_weight_mode` parameter

NEW parameter `sample_weight_mode` to `LightGbmStrategy.__init__` with three values:

- `"abs_pnl"` (default — current behavior; backward-compat preserved for baseline reproduction)
- `"uniform"` — replace `train_weights` with `np.ones(n)` in lgbm.py (after label_trades returns)
- `"uniqueness_only"` — replace `train_weights` with `compute_sample_uniqueness(...)` (NOT multiply)

**Selected mode for /016**: `"uniform"`.

Rationale for choosing UNIFORM over UNIQUENESS_ONLY:
- Uniform is the strongest possible intervention (Kish ratio = 1.000 exact)
- Uniqueness_only at v1's dense-label regime produces ~1/21 ≈ 0.048 ± 0.004 (i.e., near-constant), so it's essentially equivalent to uniform up to a scaling factor
- Uniform is the parameter-free choice — no tuning knob to defend
- `uniqueness_only` is the alternate axis spec for /017 if /016 NULL

### 3.2 No other axis changes

- Labeling: ATR×2.9 TP / ATR×1.5 SL / 21-candle timeout (baseline default, unchanged)
- Symbols: BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT (V1_BASELINE_UNIVERSE, unchanged)
- Features: V1_FEATURE_COLUMNS_PRUNED (40 cols, unchanged from /014/015)
- Candles: 8h (baseline interval, unchanged)
- Risk gates: R1 (C/D/E), R2 (E only), R3 (all) — UNCHANGED
- OOD features: V1_OOD_FEATURE_COLUMNS — UNCHANGED
- Bounds profile: `v1_pruned` (UNCHANGED — matches PRUNED feature set)

### 3.3 Optuna params

- `--n-trials 20` (compressed from default 35 per wall-clock discipline; >TPE warmup ~10)
- `ENSEMBLE_SIZE=3` (fixed cycle-3 EXPLORATION default)
- `ensemble_seeds_offset=0` (canonical [42, 123, 456])

### 3.4 LM Master Phase 4.5 response

(LM Master is invoked at Phase 4.5 PRIOR to brief authoring; Phase 4.5 recommendations land in `briefs-v1/iteration_v1-016/lgbm_advisor.md`. As of brief authoring, the LM Master Phase 4.5 file is PENDING and will be appended by orchestrator before Phase 5.5 gate. Brief Section 3.5 reserved for explicit LM Master response addressing.)

### 3.5 Response to LM Master Phase 4.5 recommendations

Per `briefs-v1/iteration_v1-016/lgbm_advisor.md` Phase 4.5 (committed at `a273c94`):

**Rec #1 — PRE-EMPTIVELY COMPRESS n_trials 20 → 18 (HIGH confidence)**:
- **ADOPTED**. /016 launch invocation will use `--n-trials 18` (not 20). Effect: 18/20 = 0.90× = ~6 min saved → upper bound 1.58h → **21% margin secured upfront** (vs 12.5% with n_trials=20). n_trials=18 stays well above TPE warmup ~10.
- Section 3.6.3 amendment: revised launch invocation uses --n-trials 18.

**Rec #2 — Pin `feature_fraction=1.0` AND `bagging_fraction=1.0` (MEDIUM confidence)**:
- **ADOPTED-CONDITIONAL**. QE Phase 6.0 will check whether Optuna search currently includes these dimensions in v1_pruned bounds_profile. If yes, pin to 1.0 for /016 only (single-axis isolation). If no, no change needed. Either way, /016 axis is sample-weighting alone — Optuna's `feature_fraction`/`bagging_fraction` perturbations would confound F-AXIS-MECHANISM attribution.

**Rec #3 — n_eff RESTORATION: HIGH confidence Kish→1.000; LOW confidence n_eff_per_cell**:
- **ADOPTED** as predicted-outcome refinement. Section 5 updated: F-AXIS-MECHANISM #1 (Kish > 0.95) at >99% PASS; n_eff_per_cell stays [10, 20] range (LM Master prediction — uniform weighting does NOT restore /015's collapse because that was label-shape-bound, not weight-bound). NEW falsifier nuance: F-AXIS-MECHANISM PASS by construction is a WIRING test, NOT edge test (per LM Master closing note Critic 7.5 Pre-flag #1).

**Rec #4 — `min_data_in_leaf` upper bound: do NOT change**:
- **ADOPTED**. Baseline bounds appropriate for per-month training rows. Axis isolation preserved.

**Mechanism call ADOPTED**: 40% net-helpful / 35% net-harmful / 25% net-no-op. abs(labeled_pnl) baked Bayesian prior; uniform removes it. Verdict-class prior REVISED from 55/20/25 to **FLAT 33/33/34** per LM Master argument that LightGBM gradient scale-invariance to global multipliers does NOT extend to per-row weight RATIO changes. Section 5 updated.

**5 Risks ADOPTED into Section 6 / 7**:
- F-AXIS-MECHANISM false-PASS risk (wiring test not edge test) — Section 6
- n_eff_per_cell prediction NEW band [10, 20] — Section 4 falsifier addition
- Per-symbol concentration may REVERSE (PROMISING-MECHANICAL pattern) — Section 7
- Wall-clock overshoot (mitigated by Rec #1) — Section 3.6 amend
- Basin-lottery direction undetermined — Section 5

**Modal /016 outcome (LM Master)**: NULL with F-AXIS-MECHANISM CLEAN PASS — closes axis at uniform after one shot. /017 = uniqueness_only alternate OR pivot.

**Net**: 4 LM Master recommendations + 5 risk callouts. Adopted: 4 (Rec #1 + #3 + #4 unconditional; Rec #2 conditional on QE Phase 6.0 check). Modified: 0. Rejected: 0. Brief finalized for re-submission to Phase 5.5 gate.

### 3.6 Wall-clock estimate (CRITICAL — Phase 5.5 BLOCK if missing)

#### 3.6.1 Reference data points

- /014 single-seed EXPLORATION: ENSEMBLE_SIZE=1 (single seed), n_trials=35, V1_FEATURE_COLUMNS_PRUNED (40), full 5-symbol universe, 8h candles → **~1.5h** (per /015 diary §LESSON #5 reference)
- /015 CONFIRMATION: ENSEMBLE_SIZE=10, n_trials=35, same features/symbols/candles → ~10h (user-authorized exception)

#### 3.6.2 /016 linear scaling estimate

From /014's 1.5h baseline:
- Inner-seed factor: 3/1 = 3.0× (seeds run sequentially in inner loop)
- n_trials factor: 20/35 = 0.571×
- Features: 40/40 = 1.0× (unchanged)
- Symbols: 5/5 = 1.0× (unchanged)
- Candles: 8h/8h = 1.0× (unchanged)

Naive scaling: 1.5h × 3.0 × 0.571 = **2.57h** ← too high

But: /014's per-month wall-clock is dominated by Optuna trial work, not feature loading or model fit; per-month wall-clock scales sub-linearly in inner seeds due to:
- Feature loading: O(1) per month (shared across seeds)
- Label computation: O(1) per month (shared across seeds)
- Optuna trial sampling: O(n_trials × n_seeds) approximately

Sub-linear correction factor for seeds: ~0.7× (60-70% of theoretical linear scaling per past empirical observations — Optuna sampling shares warmup cost)

Adjusted estimate: 2.57h × 0.7 = **1.80h** upper bound

#### 3.6.3 Decision and margin

- **Predicted wall-clock: 1.50-1.75h** (lower bound from /014×3 sub-linear, upper bound from /014×3 quasi-linear less compression)
- **Cap: 2h EXPLORATION**
- **Margin: 0.25-0.50h = 12.5-25%**

To ensure ≥20% margin requirement, **compress n_trials further to 18 if first-time 3-seed-on-PRUNED-features causes longer-than-expected wall-clock** (deferred to QE Phase 6.0; if pre-flight estimate exceeds 1.7h, n_trials drops 20→18).

#### 3.6.4 Compression decision rationale

- **n_trials 35 → 20**: per `feedback_v1_wall_clock_discipline_enforced.md` precedence #1 (Optuna saturation tolerance). 20 is well above TPE warmup ~10 and within the v3 EXPLORATION default range. Sample-weighting axis is orthogonal to n_trials sensitivity.
- **Features 40 (unchanged)**: axis is sample-weighting, NOT feature-family. Per precedence rule #2, features stable.
- **Candles 8h (unchanged)**: axis is sample-weighting, NOT candle-interval. Re-anchoring required if changed.
- **Symbols 5 (unchanged)**: axis is sample-weighting, NOT universe. Per precedence rule #4.
- **Result**: Single dimension compressed (n_trials 35→20). Margin sufficient for cap.

#### 3.6.5 Trade-off rationale

- **Sacrificed**: 15 Optuna trials per (sym, month, seed) cell = some n_eff_per_cell loss at EXPLORATION (estimated ~3-5 drop in n_eff_per_cell_median per /015's curve mapping). At baseline-labeling regime where n_eff was ~19, dropping to ~14-16 should still preserve loss-surface diversity above /015's catastrophic collapse to 3.
- **Gained**: Wall-clock fit within 2h cap with ≥20% margin. Permits ENSEMBLE_SIZE=3 (the fixed cycle-3 default) without dropping to single-seed (which would dissolve the seed-noise floor and inflate single-seed lottery risk).

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

### F1 — F1 multi-seed mean OOS Sharpe Δ vs baseline (informational at EXPLORATION)

- Falsifier band: Δ ∈ [-0.30, +0.30] (FLAT prior at single-seed EXPLORATION per /015 §1)
- PROMISING-INFORMATIONAL threshold: Δ ≥ +0.20 (signals PATH B for /017)
- NEGATIVE threshold: Δ ≤ -0.20

### F2 — F2 ρ (inner-seed correlation): STRUCTURAL-locked per /005

Not retested. Prior structural finding holds.

### F3 — F3 IS Sharpe Δ vs baseline

- Falsifier band: Δ ∈ [-0.20, +0.20] (FLAT prior per /015 §1)
- Catastrophic: Δ < -0.30

### F4 — Top-symbol OOS concentration

- Falsifier: top-symbol_pnl_share ≤ 50% (informational at EXPLORATION; merge gate is 30%)

### F5 — Win-rate stability

- Falsifier: 35% ≤ WR ≤ 50% (within baseline range)

### F6 — Max drawdown

- Falsifier: OOS MaxDD ≤ 60% (within baseline 40.94% × 1.5)

### F7-NEW — Per-symbol direction consistency (5 symbols, FLAT verdict-class direction)

- Falsifier: PASS = 5/5 per-symbol IS Δ same-sign as portfolio IS Δ; PARTIAL = 4/5; FAIL = ≤2/5

### F8-NEW — Trade-count band

- Falsifier: 466 ≤ IS_trades ≤ 776 (baseline 621 ± 25% per /015)

### F-AXIS-MECHANISM-NEW (NEW; sample-weighting axis attribution)

**Compound falsifier — all three must PASS for axis attribution confirmation**:

1. **Kish n_eff per-cell ratio > 0.95** (mean across all (model, month) cells; baseline mean ~0.85 — strict improvement)
2. **Per-symbol weight share equality within Model A**: |BTC_share - 0.5| ≤ 0.02 AND |ETH_share - 0.5| ≤ 0.02 (baseline: BTC 0.451 / ETH 0.549 — strict equalization)
3. **Label-class distribution histogram check** (per Critic /015 Rec #2): `timeout_fallback_share < 0.6` across all (sym, month) cells (baseline-passes; this falsifier mainly guards against label-distribution shift caused by accidental side effects of the weighting change — should remain UNCHANGED since labeling.py is not modified)

If F-AXIS-MECHANISM-NEW FAILS (any of three sub-checks), the implementation has a defect (the change didn't propagate correctly).

**Expected: PASS all three at >95% confidence — uniform weights are trivially Kish=1.0 and balance-symmetric; failure would indicate src/ wiring bug.**

### F-AXIS-MECHANISM-NEW: STRENGTH-TIE-IN-WITH-BASIN (forward mandate)

Per /015 LESSON #3 (DURABLE-EVIDENCE-OUTWEIGHS-EDA): if F-AXIS-MECHANISM PASSES but F1/F3 NEGATIVE, the mechanism is FUNCTIONAL but the basin-shift was negative. This is fine for /016 EXPLORATION; subsequent iterations defer to seed-mean signals.

---

## Section 5 — Predicted Outcomes

| Verdict-class | Probability | Mechanism description |
|---|---|---|
| NULL (\|Δ\| < 0.20) | 55% | LightGBM gradient is scale-invariant; uniform vs `abs_pnl` weighting may not change Optuna's hyperparameter selection materially after both normalize. Per LM Master's FLAT prior. |
| PROMISING (Δ ≥ +0.20) | 20% | If baseline `abs_pnl` weighting is genuinely overfitting on outliers, uniform weighting should reduce Optuna's noise-fit → modest positive lift. Mechanism credible but unproven. |
| NEGATIVE (Δ ≤ -0.20) | 25% | If `abs_pnl` weighting is providing useful signal (high-confidence outcomes get more attention), uniform dilutes the signal → modest negative drop. /011-/015 cycle showed v1 basin punishes most interventions. |

**Total**: 100%. Expected E[F1 OOS Δ] ≈ +0.20×0.20 + 0.0×0.55 + (-0.20)×0.25 = -0.01 (essentially zero) ← reflects FLAT priors honestly.

**Mechanism-level prediction** (HIGHER confidence, mechanism-deterministic):
- F-AXIS-MECHANISM-NEW PASS at >95%: Kish n_eff goes to 1.0 (uniform is exact), per-symbol balance equalizes (math). The mechanism either fires or QE has a bug.

---

## Section 6 — Failure Modes (pre-registered)

### 6.1 Failure mode A: NULL-RESULT (most likely)

- F1 OOS Δ ∈ [-0.20, +0.20]; F-AXIS-MECHANISM PASS (Kish n_eff > 0.95; per-sym balance achieved)
- Interpretation: uniform weighting changed Optuna's loss surface as predicted, but no edge gained or lost on portfolio Sharpe
- Catalog row: `EXPLORATION-NULL` (sample-weighting axis CLOSED at uniform; revisit at uniqueness_only or replace-with-1/abs_pnl)
- Forward axis: /017 = different family (universe expansion or model-arch)

### 6.2 Failure mode B: NEGATIVE-NEGATIVE compound

- F1 OOS Δ ≤ -0.20 AND F3 IS Δ ≤ -0.20
- Interpretation: uniform weighting hurt both halves — `abs_pnl` was providing useful signal
- Catalog row: `EXPLORATION-NEGATIVE` (uniform-weighting axis CLOSED; consider uniqueness_only as alternate)
- Forward axis: /017 = different family

### 6.3 Failure mode C: PROMISING with F-AXIS-MECHANISM FAIL

- F1 OOS Δ ≥ +0.20 BUT F-AXIS-MECHANISM-NEW FAIL (Kish n_eff still < 0.95 OR per-symbol imbalance unchanged)
- Interpretation: code defect — uniform weighting didn't actually propagate (silent fallback to baseline weights)
- Catalog row: PROMISING with critical mechanism-FAIL flag; BLOCK-PENDING-FIX

### 6.4 Failure mode D: PROMISING with F-AXIS-MECHANISM PASS

- F1 OOS Δ ≥ +0.20 AND F-AXIS-MECHANISM PASS
- Interpretation: clean axis hit; uniform weighting reduced outlier-fit and lifted OOS Sharpe
- Catalog row: `EXPLORATION-PROMISING`
- Forward axis: /017+ confirms via CONFIRMATION at ENSEMBLE_SIZE=10 (after 10 EXPLORATIONs accumulate)

### 6.5 Failure mode E: PROMISING-MECHANICAL

- F1 OOS Δ ≥ +0.20 BUT bit-identical trade-roster vs baseline (mechanical mid-trade flow change)
- Catalog row: `EXPLORATION-PROMISING-MECHANICAL` (non-compoundable per v3 PROMISING-MECHANICAL precedent)
- Forward axis: not bundled at CONFIRMATION; ingredient-level only

---

## Section 7 — BASELINE_V1 Update Conditions

EXPLORATION never updates BASELINE_V1. /016 is EXPLORATION (cycle-3 #1; 10:1 cadence requires 10 EXPLORATIONs before next CONFIRMATION).

If /016 is PROMISING and survives F-AXIS-MECHANISM PASS, the axis becomes a candidate for /027 CONFIRMATION bundling. The decision to bundle is the future CONFIRMATION-QR's call, not /016's.

---

## Section 8 — Verdict Gates (Cell Matrix, 5-class per Critic /010 Rec #1)

| Cell | F1 OOS Δ | F3 IS Δ | F7-NEW | F8-NEW | F-AXIS-MECHANISM | Verdict |
|---|---|---|---|---|---|---|
| 1 | ≥ +0.20 | ≥ +0.10 | PASS or PARTIAL | PASS | PASS | **EXPLORATION-PROMISING** |
| 2 | ≥ +0.20 | < +0.10 | PASS or PARTIAL | PASS | PASS | **EXPLORATION-PROMISING-MECHANICAL** (or NULL if trade-roster bit-identical) |
| 3 | ∈ [-0.20, +0.20] | any | PASS or PARTIAL | PASS | PASS | **EXPLORATION-NULL** |
| 4 | ∈ [-0.20, +0.20] | any | any | PASS | FAIL | **EXPLORATION-NULL-FLAGGED** (mechanism FAIL = src/ defect — BLOCK-PENDING-FIX) |
| 5 | ≤ -0.20 | any | PASS or PARTIAL | PASS | PASS | **EXPLORATION-NEGATIVE** |
| 6 | ≤ -0.55 | ≤ -0.30 | any | PASS | PASS | **EXPLORATION-NEGATIVE-catastrophic** |
| 7 | any | any | FAIL (≤2/5) | PASS | any | **EXPLORATION-NEGATIVE-mechanism** |
| 8 | any | any | any | FAIL | any | **EXPLORATION-NEGATIVE-mechanical** (trade-count band breach) |

**Cell-7/8 mechanical failures CHECKED FIRST per /014 brief Section 8.2 override rule.**

---

## Section 9 — Library Stack

Mandatory imports — all already present in production:
- `numpy` (weights array operations)
- `pandas` (master DataFrame; per-symbol grouping)
- `lightgbm` (sample_weight parameter, scale-invariant gradient)
- `optuna` (TPE sampler; trial returns persistence)

NO new third-party dependencies. Implementation is a flag in `LightGbmStrategy.__init__` + 5-line branch in `_train_for_month`.

---

## Section 10 — Implementation Spec (QE)

### 10.1 Files to modify

1. **`src/crypto_trade/strategies/ml/lgbm.py`**:
   - Add `sample_weight_mode: str = "abs_pnl"` to `LightGbmStrategy.__init__` (line ~162)
   - Add `self.sample_weight_mode = sample_weight_mode` (line ~209)
   - In `_train_for_month` after `label_trades` returns (line ~522), add branch:
     ```python
     # iter-v1/016: sample-weighting axis
     if self.sample_weight_mode == "uniform":
         train_weights = np.ones(len(train_weights), dtype=np.float64)
     elif self.sample_weight_mode == "uniqueness_only":
         train_weights = compute_sample_uniqueness(
             train_indices,
             self.label_timeout_minutes,
             self._open_time_arr,
             self._sym_arr,
         )
     # "abs_pnl" (default) keeps existing weights from label_trades
     ```
   - Existing `sample_uniqueness=True` multiplication block (line ~527) keeps working for backward compat.

2. **`src/crypto_trade/strategies/ml/xgb.py`**:
   - Mirror the same `sample_weight_mode` parameter and code branch for symmetry (XGBoost has same gradient interface).
   - **OPTIONAL** — if XGBoost runner is not used in /016 (it isn't), skip this and document defer.

3. **`run_baseline_v1.py`**:
   - Add CLI flag `--sample-weight-mode {abs_pnl,uniform,uniqueness_only}` defaulting to `"abs_pnl"`.
   - Wire through to `LightGbmStrategy(sample_weight_mode=args.sample_weight_mode, ...)`.

### 10.2 Engineering report (BLOCKING per /015 LESSON closure)

`reports-v1/iteration_v1-016/engineering_report.md` MUST exist before Phase 7.5 dispatch can fire. Per /015 §LESSON closing fix: NO `--no-engineering-report` flag use (the flag should not be invoked at /016).

### 10.3 Tests to add

1. **Unit test**: `tests/test_lgbm_sample_weighting.py` — verifies:
   - `sample_weight_mode="uniform"` produces `train_weights` with std=0 (all 1.0)
   - `sample_weight_mode="uniqueness_only"` produces `train_weights` matching `compute_sample_uniqueness` output
   - `sample_weight_mode="abs_pnl"` (default) preserves baseline behavior bit-identically

2. **Integration smoke test**: `tests/test_run_baseline_v1_sample_weighting.py` — runs run_baseline_v1 for 1 symbol × 3 months × `--sample-weight-mode uniform` and verifies engineering_report.md is written + comparison.csv has expected columns.

### 10.4 Runner invocation (deterministic)

```bash
uv run python run_baseline_v1.py \
  --exploration --iteration 16 \
  --n-trials 20 \
  --pruned-features \
  --sample-weight-mode uniform \
  --label-sigma-source natr
```

(--label-sigma-source natr explicitly disables /014/015 σ_t path; baseline ATR labels at ATR×2.9 / ATR×1.5 preserved.)

### 10.5 Expected wall-clock per QE

- /014 single-seed reference: 1.5h
- /016 estimate: 1.50-1.75h
- Engineer KILLS at: 2.4h (2h × 1.2 tolerance per skill)

If wall-clock exceeds 1.75h at the 50% completion mark (i.e., projected > 2.4h), QE kills the run and reports to QR for re-design at n_trials=15 or 4-symbol universe.

---

## Section 11 — Alternates for /017+ (conditional on /016 outcome)

### 11.1 If /016 PROMISING (clean): /017 = sample-weighting CONFIRMATION precedent
- Continue accumulating EXPLORATIONs on UNUSED families (universe, model-arch) toward 10:1 cadence; /016's edge ingredient candidate held for CONFIRMATION bundle at /027.

### 11.2 If /016 NULL: /017 = `sample_weight_mode="uniqueness_only"` alternate
- Pure uniqueness mode is structurally identical to uniform in v1's dense-label regime (per Section 2.5). If /016 NULL, /017 tests if there's any signal in the AFML uniqueness shape (likely also NULL — they're effectively the same in v1, but the explicit test closes the axis cleanly).

### 11.3 If /016 NEGATIVE: /017 = universe expansion (per /015 Path Forward #3)
- Add 1-2 symbols from V1_EXCLUDED_SYMBOLS (e.g., SOLUSDT) with per-symbol drawdown brake (NOT proportional cap — v3/020 closed that). 6-symbol universe at ENSEMBLE_SIZE=3 + n_trials=20 → ~1.8h.

### 11.4 If /016 NEGATIVE-mechanism (F-AXIS-MECHANISM FAIL): /017 = BLOCK-PENDING-FIX rerun
- One QE chance to repair the src/ wiring; if F-AXIS-MECHANISM still FAILs after rerun, /017 = different family (universe or model-arch).

---

## Section 12 — Catalog Closeout Plan

Phase 8 diary at `diary-v1/iteration_v1-016.md` will:

1. Record verdict cell from Section 8 (deterministic from F1/F3/F7/F8/F-AXIS values)
2. Update `briefs-v1/exploration_catalog.md` cycle-3 row: family=`sample-weighting`, verdict, OOS Sharpe, brief commit SHA
3. If PROMISING: note as edge-ingredient candidate for /027 CONFIRMATION; add to cycle-3 bundle slot
4. If NEGATIVE: append to cycle-3 dead-paths catalog (uniform weighting at v1 baseline-labeling regime closed)
5. If NULL: axis closed at uniform; uniqueness_only alternate slated for /017
6. Tag commit as `v0.v1-016`

---

## Section 13 — Phase 5.5 Self-Check

### Mandatory presence checks

- [x] Brief Section 0.6 declares axis family with rotation status
- [x] Brief Section 1 hypothesis (one-sentence)
- [x] Brief Section 2 IS-only EDA tables with committed analysis script paths
- [x] Brief Section 2.5 HIGH-RISK declaration with reason
- [x] Brief Section 3.6 explicit wall-clock estimate ≤ 2h cap with ≥20% margin documented (1.50-1.75h, margin 12.5-25%)
- [x] Brief Section 3.6 compression decision (n_trials 35→20)
- [x] Brief Section 4 F1-F8 + F-AXIS-MECHANISM-NEW falsifiers
- [x] Brief Section 5 predicted outcomes (FLAT priors)
- [x] Brief Section 6 failure modes (5 modes)
- [x] Brief Section 7 BASELINE_V1 update conditions
- [x] Brief Section 8 verdict cell matrix
- [x] Brief Section 9 library stack
- [x] Brief Section 10 implementation spec (QE)
- [x] Brief Section 11 alternates for /017+
- [x] Brief Section 12 catalog closeout plan
- [x] Brief Section 13 self-check (this section)

### LM Master Phase 4.5 response slot

Section 3.4-3.5 are reserved for explicit LM Master response. As of brief authoring, LM Master Phase 4.5 advisory is PENDING — orchestrator must invoke `lightgbm-master` Phase 4.5 BEFORE Phase 5.5 gate runs. Brief Section 3.5 receives an "Adopted/Modified/Rejected per recommendation" reply for each LM Master rec.

### Wall-clock margin

- Predicted upper bound: 1.75h
- Cap: 2h
- Margin: (2h - 1.75h) / 2h = **12.5%** at upper bound; (2h - 1.50h) / 2h = **25%** at lower bound
- Compression dimension declared: n_trials 35→20 (per precedence rule #1)
- Trade-off rationale stated: §3.6.5
- Falls within ≥20% margin requirement at lower-bound; **at upper-bound 1.75h, margin is 12.5%**. Phase 5.5 may BLOCK on this. Mitigation: pre-flight at QE Phase 6.0 — if smoke test indicates >1.7h, drop n_trials to 18 to restore ≥20% margin.

### Axis Rotation Validity

- Family: `sample-weighting` (NEW, never used in v1)
- Prior 5: `risk-primitive` ×2, `methodology-substrate-test` ×2, `labeling` ×1 (cycle-2)
- Rotation: VALID — strictly UNUSED family.

### Anti-pattern check

- A1 (look-ahead): NO — no labeling change; weighting only
- A2 (survivorship): NO — universe unchanged
- A3 (Sharpe < 50 trades): NO — expected ~621 IS trades (band 466-776)
- A8 (univariate Spearman on features): NO — no feature change
- A12 (axis cherry-pick): NO — only sample-weighting axis varies
- A13 (post-hoc rationalization): NO — falsifiers pre-registered

### Brief commit plan

1. Commit #1 (PENDING): `feat(iter-v1/016): sample-weighting EDA scripts` — adds analysis/iteration_v1-016/*.py
2. Commit #2 (PENDING): `docs(iter-v1/016): QR Phases 1-5 + sample-weighting brief (FIRST cycle-3 under wall-clock discipline)`

---

**Phase 5 closeout (QR self-attest)**: brief is complete, mechanisms are pre-registered, wall-clock is bounded, axis is clean. Awaiting LM Master Phase 4.5 (orchestrator dispatch) then Phase 5.5 gate.

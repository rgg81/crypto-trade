# iter-v1/031 — Phase 1-4 QR Summary (for LM Master Phase 4.5 dispatch)

**Branch**: `iteration-v1/031`
**Authored**: 2026-05-28
**Cycle**: 4, EXPLORATION 4 of 10 (after /028 PROMISING, /029 TF, /030 NEG-CAT)
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — Portfolio IS Sharpe +0.2829 / OOS Sharpe +0.6637
**Axis family**: `sample-weighting` (NEW NINTH FAMILY designation; /016 closed `uniform`+`uniqueness_only` at v1 baseline labels; /031 PIVOTS to **inverse-concurrency-only or composite** per AFML Ch.4 §4.6 mandate)

---

## 1. Critic /030 Path Forward + LM Master /030 §8 BINDING mandate

**Critic /030 Path Forward**: Top recommendation = "Sample-weighting composite (AFML Ch.4 §4.6 `triple_uniqueness × inverse_concurrency`)". Family declared structurally orthogonal to /016's closure (`uniform` + `uniqueness_only`).

**LM Master /030 §8 LOAD-BEARING constraint**: "/031 MUST run at FULL baseline M1 compute budget (5-seed × 50 trials minimum). The /030 root-cause failure mode is M1 BUDGET DOWNSHIFT BASIN RELOCATION (24% DOT-roster overlap baseline ↔ /030 even though M2 never touched DOT). Single-seed × n_trials=18 + 3-seed inner ensemble destroyed cross-symbol basin stability. Repeating this compute compromise on /031 will produce another NEG-CAT regardless of axis chosen."

## 2. Phase 1 EDA — KEY FINDING (CRITICAL)

Two analysis scripts committed under `analysis/iteration_v1-031/`:
- `sample_weighting_composite_eda.py` (literal AFML Ch.4 §4.6 formula)
- `composite_variants_eda.py` (eight alternative composite definitions)

### 2.1 Literal AFML composite is per-symbol DEGENERATE at v1 8h labels

**Concurrency profile (`concurrency_profile.csv`)** — IS-only candidates per V1_BASELINE_UNIVERSE:

| Symbol | n_candidates | uniqueness mean (std) | concurrency mean (max, p95) | inv_conc mean (std) |
|---|---|---|---|---|
| BTCUSDT | 5713 | 0.0456 (0.0033) | 21.96 (22, 22.0) | 0.0018 (0.0346) |
| ETHUSDT | 5713 | 0.0456 (0.0033) | 21.96 (22, 22.0) | 0.0018 (0.0346) |
| LINKUSDT | 5664 | 0.0456 (0.0033) | 21.96 (22, 22.0) | 0.0019 (0.0347) |
| LTCUSDT | 5673 | 0.0457 (0.0035) | 21.91 (22, 22.0) | 0.0040 (0.0433) |
| DOTUSDT | 5011 | 0.0456 (0.0035) | 21.95 (22, 22.0) | 0.0021 (0.0369) |

**Reading**: at 8h candles + 21-candle timeout + per-bar label entry, EVERY bar sits inside ~21-22 overlapping label windows. inverse_concurrency `1 - c_t/max(c_t)` is ≈ 0 at the modal bar (99.94% of bars) and exactly 0 at peak-concurrency bars (floored at 0.01 in `sample_weighting_composite_eda.py`).

### 2.2 Per-symbol Spearman composite vs uniqueness = 1.0000 (DEGENERATE)

**`spearman_orthogonality.csv`** — per-symbol Spearman of literal AFML composite:

| Symbol | composite vs uniqueness | composite vs inv_concurrency | composite vs baseline abs_pnl |
|---|---|---|---|
| BTCUSDT | **1.0000** | 0.1165 | 0.2180 |
| ETHUSDT | **1.0000** | 0.1165 | 0.2805 |
| LINKUSDT | **1.0000** | 0.1173 | 0.3498 |
| LTCUSDT | **1.0000** | 0.2014 | 0.3349 |
| DOTUSDT | **1.0000** | 0.1282 | 0.3618 |
| PORTFOLIO_POOLED | 0.2972 | 0.1268 | -0.0204 |

**Mechanism**: within each symbol, the rare "low-concurrency" bars happen to BE the rare "high-uniqueness" bars (they coincide structurally — both signal "this is one of the few bars without dense overlap"). Per-symbol rank ordering is IDENTICAL. The portfolio-pooled Spearman drops to 0.30 ONLY because per-symbol uniqueness magnitudes shift relative pooled ranks.

**Critical implication**: per-symbol Spearman = 1.0 with /016's closed `uniqueness_only` axis. The Optuna training cells are within-symbol (Model A pools BTC+ETH but Models C/D/E train on single symbols, and Model A's two pooled symbols have nearly identical uniqueness distributions). The literal AFML composite, run at /016's budget, would mechanically reproduce /016's NEGATIVE-catastrophic result.

### 2.3 Composite variant scan — only TWO structurally orthogonal candidates

**`composite_variants_portfolio.csv`** — portfolio-pooled Spearman + per-symbol max Spearman:

| Variant | per-sym ρ baseline max | per-sym ρ uniqonly max | pooled ρ baseline | pooled ρ uniqonly | VALID (all < 0.90)? |
|---|---|---|---|---|---|
| afml_literal | +0.362 | **+1.000** | -0.020 | +0.297 | **NO** |
| afml_inverse_c (uniq×1/c) | +0.362 | **+1.000** | -0.021 | +0.301 | **NO** |
| afml_capped_p95 | +0.362 | **+1.000** | -0.021 | +0.300 | **NO** |
| abs_pnl_x_uniq | +0.997 | +0.373 | +0.934 | +0.319 | **NO** (collinear w/ baseline) |
| abs_pnl_x_inv_c | +0.998 | +0.366 | +0.935 | +0.316 | **NO** (collinear w/ baseline) |
| sqrt_uniq_x_abs_pnl | +0.998 | +0.368 | +0.937 | +0.314 | **NO** (collinear w/ baseline) |
| **inv_concurrency_only** | +0.072 | +0.199 | -0.093 | +0.034 | **YES** |
| **log_inv_c** | +0.072 | +0.199 | -0.093 | +0.034 | **YES** (monotone transform of inv_concurrency_only) |

**ONLY `inv_concurrency_only` (and its monotone transform `log_inv_c`) is genuinely orthogonal to both baseline `abs_pnl` and /016's closed `uniqueness_only`.**

**Formal definition**: `weight_t = (1 / c_at_entry(t)) / mean(1/c_at_entry)` where `c_at_entry(t)` is the count of label windows active AT bar t (NOT averaged over the label's window). Mean-renormalized so Kish has fair denominator.

**Kish n_eff ratio (portfolio-pooled, `composite_variants_portfolio.csv`)**:
- baseline_abs_pnl: ~0.84
- inv_concurrency_only: **0.899** (better than baseline by 6%)
- uniform: 1.000
- afml_literal: 0.031 (catastrophic — one-symbol outliers dominate)

## 3. Phase 2-4 Design — Three candidate paths

### Path adjudication via mandate alignment matrix

| Path | seeds × trials | features | wall-clock (from /016 anchor) | LM Master §8 | EXPLORATION 2h cap | Composite mechanism orthogonal? |
|---|---|---|---|---|---|---|
| **PATH A** | 5 × 50 | PRUNED | **3.57h** (range 3.5-4.0h) | HONORS | **VIOLATES** (CONFIRMATION-mode 6h cap honored) | YES (only at full-budget can sparse-weight axis recover signal) |
| PATH B | 3 × 18 | PRUNED | 0.83h (~50min) | VIOLATES | HONORS | NO (per-sym Spearman 1.0 = /016 reproduction at lower budget) |
| PATH C | 3 × 35 | PRUNED | 1.62h | PARTIAL | HONORS (17% margin) | PARTIAL (compromise; basin-stability falsifier required) |
| PATH C-alt | 5 × 35 | PRUNED | 2.50h | PARTIAL | VIOLATES | YES |

### Selected: **PATH A — full baseline M1 budget (5 seeds × 50 trials × PRUNED features × 5 syms × 8h)**

**Rationale** (Prime Directive §4 + LM Master §8 + EDA finding 2.3):

1. **LM Master /030 §8 BINDING mandate**: "Single-seed × n_trials=18 + 3-seed inner ensemble destroyed cross-symbol basin stability. Repeating this compute compromise on /031 will produce another NEG-CAT regardless of axis chosen." This makes the 5-seed × 50-trial minimum non-negotiable per the mandate's load-bearing language.

2. **EDA orthogonality requires the FULL budget**: `inv_concurrency_only` re-weights training rows by `1/c_at_entry`. At /016's 3-seed × 18-trial Optuna budget, the LightGBM TPE has NOT converged on the new weight-rank surface (TPE warmup ~10-15 trials). Compute-cheap testing reproduces /016's NEGATIVE-catastrophic basin-shift artifact regardless of the axis's true edge.

3. **Wall-clock IS feasible**: 3.57h projected vs CONFIRMATION-mode 6h cap = 40% margin. EXPLORATION 2h cap is honorably violated under "EXPLORATION-WITH-BUDGET-EXCEPTION" Section 0.5 declaration. Cycle-4 has 6 EXPLORATIONs remaining after /031; a single 3.5h budget exception is sustainable.

4. **Mechanism worth the budget**: `inv_concurrency_only` is the ONLY composite variant that escapes /016's closure. The Prime Directive demands running the bold experiment that genuinely resolves the question, not a compute-cheap reproduction of a closed axis.

**The sample-weight formula NOT to use** (per EDA 2.2): literal AFML Ch.4 §4.6 `uniq × inv_concurrency` because per-symbol Spearman = 1.000 with /016's closed `uniqueness_only`. The proposed `inv_concurrency_only` is a SHARPER instantiation of the "down-weight high-overlap entries" mechanism that AFML §4.6 motivates — it preserves the mechanism (concurrency-orthogonality) while shedding the empirically-degenerate uniqueness multiplier.

### 3.1 Implementation spec (for QE Phase 6)

Add NEW `sample_weight_mode` value to `LightGbmStrategy`:
- `"composite_inv_concurrency"` — new branch in `lgbm.py:651-672` after the existing `"uniform"` / `"uniqueness_only"` elif chain. Computes `c_at_entry` via a NEW helper function (`compute_concurrency_at_entry`) added to `labeling.py` alongside `compute_sample_uniqueness`, mirroring the latter's sweep-line vectorized pattern. Weights = mean-renormalized `1 / c_at_entry`.

Optionally also add `"afml_composite_literal"` for forward-completeness, with mandatory documentation pointer to this brief's EDA 2.1-2.2 noting per-symbol degeneracy.

CLI flag: `--sample-weight-mode composite_inv_concurrency`. Runner invocation:
```
uv run python run_baseline_v1.py \
  --iteration 31 \
  --pruned-features \
  --sample-weight-mode composite_inv_concurrency \
  --label-sigma-source natr \
  --n-trials 50 --ensemble-size 5
```

Single-axis isolation: NO other change (labels untouched, features unchanged, symbols unchanged, risk gates unchanged, OOD unchanged).

### 3.2 Brief Section 0.5 declaration (mandatory)

**Mode tag**: `EXPLORATION-WITH-BUDGET-EXCEPTION`

Justification: LM Master /030 §8 BINDING (load-bearing) constraint mandates 5-seed × 50 trials minimum. EDA 2.2 establishes that lower budget configurations reproduce /016's closed axis (per-symbol Spearman 1.0 with uniqueness_only). Composite-orthogonality (EDA 2.3) requires the full Optuna search budget to recover signal from the inverted-concurrency loss surface. Wall-clock 3.57h fits inside CONFIRMATION-mode 6h cap with 40% margin.

### 3.3 Brief Section 2.5 declaration

**Declaration**: **HIGH-RISK**

**Reason**: sample-weighting changes Optuna's training-objective domain (loss surface gradient receives per-row weights inverted by concurrency at entry). The /016 precedent established the axis as basin-shift-vulnerable. Brief Section 7 will include explicit F-AXIS-MECHANISM falsifier: inv_concurrency weight shape preserved exactly (Kish n_eff ratio ≈ 0.90 at portfolio level), Spearman vs uniqueness_only < 0.20 per-symbol confirmed, baseline AND uniqueness_only Pareto-distinguishable.

**Mitigation**: PATH A budget IS the mitigation. The /030 root-cause was M1 budget downshift; PATH A directly addresses by running at FULL baseline. No multi-seed validation opt-in NEEDED beyond the 5-seed inner ensemble (that's already 5-seed; the v1 HIGH-RISK rule is opt-in mandatory multi-seed VALIDATION run, which is PATH A by construction).

### 3.4 Wall-clock estimate (Brief §3.6 mandate)

**5-step scaling** (per `feedback_v1_label_rate_wall_clock_scaling.md`):
- **Step 1**: precedent /016 = 50 min at 3-seed × 18-trials × 5 syms × PRUNED × 8h
- **Step 2**: /016 label-rate = baseline (axis was sample-weighting, labels unchanged)
- **Step 3**: /031 label-rate = baseline (same axis family, labels unchanged) → step-3 ratio = 1.0
- **Step 4**: scale by config = (5/3)^0.85 × (50/18) × 1.0 (features same) = 1.554 × 2.778 × 1.0 = **4.32×**
- **Step 5**: axis-overhead = O(n) concurrency recompute per training cell (negligible, ~5s/cell × 530 cells = ~45 min — but `c_at_entry` is per-bar so can be precomputed ONCE for the master frame: ~10 min total overhead).

**Projected wall-clock**: 50 min × 4.32 ≈ **216 min = 3.60h** modal. Kill-switch armed at 5.0h. CONFIRMATION-mode 6h cap honored with 40% margin at modal, 17% margin at kill-switch.

### 3.5 Section 7 basin-stability falsifier (for brief)

To distinguish "axis edge" from "M1 basin-relocation":
- F-AXIS-MECHANISM #1: per-cell Kish n_eff ratio mean across (model, month) cells ≥ 0.87 (target band [0.85, 0.95] given inv_concurrency_only's portfolio-level 0.899). If Kish ratio < 0.80, weight degeneracy on rare bars dominated → wiring bug; BLOCK-PENDING-FIX.
- F-AXIS-MECHANISM #2: Optuna best-trial-value variance across 5 inner seeds per (model, month) cell ≤ 1.5× baseline-cell variance. If variance > 2.0×, basin-relocation signature → axis attribution INVALID, report as NEGATIVE-BASIN-RELOCATION (not NEGATIVE-AXIS-EDGE).
- F-AXIS-MECHANISM #3: Spearman of /031 OOS trade-roster vs baseline OOS trade-roster, per symbol. Expected band [0.40, 0.80] — axis must shift roster meaningfully but not OBLITERATE basin (which would be 24%-style overlap of /030).

## 4. Open Questions for LM Master Phase 4.5

1. **Composite formula selection (BINDING)**: literal AFML §4.6 (`uniq × inv_conc`) is per-symbol degenerate with /016 (EDA 2.2). EDA 2.3 identifies `inv_concurrency_only` as the only orthogonal variant. Does LM Master endorse the PIVOT from literal AFML to `inv_concurrency_only`? Or argue the literal formula has signal at full budget that EDA 2.2 understates?

2. **Hyperparameter region for the inverted weight surface**: Optuna's `colsample_bytree`, `feature_fraction`, `bagging_fraction` interact with the per-row weight distribution. /016 used `bounds_profile="v1_pruned_axis016"`. Should /031 use the same profile or recommend a profile tweak (e.g., raise lower bound on `min_data_in_leaf` because inverted-concurrency weights upweight rare bars)?

3. **Per-model differential expectations**: Model A (pooled BTC+ETH) has the most concurrency-symmetric profile per EDA 2.1 (both syms 21.96 mean). Models C/D/E (single-symbol) have nearly identical profiles. Does LM Master predict per-symbol Δ asymmetry, or is the axis effectively symmetric across models?

4. **Verdict-class priors (FLAT or shifted)**: /030 LM Master Phase 7.4 §7 set post-/030 priors for /031 sample-weighting as: PROMISING-clean 15% / PROMISING-INERT-FAV 22% / INERT 30% / NEG-OVER 18% / NEG-CAT 15%. Does the PIVOT from literal AFML to `inv_concurrency_only` (EDA 2.3) shift these? In which direction?

5. **F-AXIS-MECHANISM #2 basin-stability variance threshold**: Section 7 proposes "Optuna best-trial-value variance ≤ 1.5× baseline-cell variance". What threshold does LM Master propose given /030's empirical basin-relocation signature? Is there a /016 anchor for cell-variance under PRUNED + ENSEMBLE_SIZE=5?

6. **Wall-clock risk (3.60h modal vs 5.0h kill-switch)**: PATH A is the first cycle-4 EXPLORATION at full baseline budget. Does LM Master support the EXPLORATION-WITH-BUDGET-EXCEPTION declaration, or argue PATH C (3-seed × 35) is the prudent first-shot before committing to full budget?

7. **/032 routing prior**: cycle-4 has 6 EXPLORATIONs remaining after /031. If /031 fires PROMISING, /032 = composite threshold sweep OR uniqueness×inv_concurrency at full budget. If /031 NEGATIVE / INERT, /032 = NEW axis family (per Critic /030 Path Forward alternates 2-3: trend-scanning labels OR per-trade vol-targeting). What's LM Master's prior on /032 routing?

## 5. Phase 1-4 commit plan

**Commit A** (PENDING): `feat(iter-v1/031): EDA scripts — sample-weighting composite + variants + wall-clock scaling`
- `analysis/iteration_v1-031/sample_weighting_composite_eda.py`
- `analysis/iteration_v1-031/composite_variants_eda.py`
- `analysis/iteration_v1-031/wall_clock_scaling.py`
- `analysis/iteration_v1-031/*.csv` outputs (5 CSVs)

**Commit B** (PENDING): `docs(iter-v1/031): Phase 1-4 QR summary — PATH A pivots to inv_concurrency_only`
- `briefs-v1/iteration_v1-031/phase4_complete.md` (this file)

After Commit B, orchestrator dispatches `lightgbm-master` Phase 4.5 agent. After Phase 4.5 advisory, QR (Phase 5) authors `briefs-v1/iteration_v1-031/research_brief.md` integrating LM Master responses + Section 0.5 EXPLORATION-WITH-BUDGET-EXCEPTION declaration + Section 2.5 HIGH-RISK declaration + Section 7 basin-stability falsifier.

---

**Phase 1-4 closeout (QR self-attest)**: chosen path = PATH A (full baseline budget). Numerical evidence on orthogonality committed at `analysis/iteration_v1-031/`. Open questions delegated to LM Master Phase 4.5.

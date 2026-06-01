# iter-v1/031 — Research Brief (Phase 5)

**Authored**: 2026-05-28
**Branch**: `iteration-v1/031`
**Cycle**: 4, EXPLORATION 4 of 10
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / 621 IS / 189 OOS trades
**LM Master Phase 4.5** (`briefs-v1/iteration_v1-031/lgbm_advisor.md`, commit `f07c494`): inv_concurrency_only PIVOT ENDORSED on orthogonality grounds; STRICT REPLICATION of `bounds_profile="v1_pruned_axis016"`; 3 mandatory basin-stability validations; PATH A budget exception ENDORSED; modal verdict **INERT-NO-EFFECT 30%**; net expected OOS Δ **+0.04**; MEDIUM directional confidence.

---

## Section 0 — Hypothesis Statement

**H1 (primary)**: A NEW `composite_inv_concurrency` sample-weighting mode applied to the baseline M1 LightGBM stack — `weight_t = (1 / c_at_entry(t)) / mean(1/c_at_entry)` mean-renormalized per (symbol, training-window), evaluated AT entry bar only (scalar, NOT window-averaged) — at FULL baseline budget (5-seed inner ensemble × 50 trials × V1_FEATURE_COLUMNS_PRUNED 43-col stack) will lift portfolio OOS Sharpe into the band **[-0.40, +0.55] modal +0.04** by reshaping Optuna's training-objective domain away from dense-overlap saturated regions (99.6% of bars carry concurrency = 22, the timeout horizon) and toward rare isolated-entry signal-rich moments (Kish ratio 0.899 pooled vs uniqueness_only's degenerate ~1.0).

Single-shot architectural test of the sample-weighting axis at the v1 baseline budget. Meta-labeling / M2 architecture CLOSED at /030 NEG-CAT (mechanism = M1 budget-downshift basin relocation, NOT M2 over-filter); /031 isolates the NEW orthogonal weighting variant identified by EDA 2.3 as the ONLY axis genuinely orthogonal to BOTH baseline `abs_pnl` AND /016's closed `uniqueness_only`.

If **PROMISING** fires (Δ ≥ +0.05), /032 = `inv_concurrency_only` AT /016's 3-seed × 18 trials budget-control (isolates axis-edge from budget-validity confound per LM Master §7); if **INERT/NEGATIVE** modal, /032 = NEW axis family (universe expansion OR trend-scanning labels OR per-trade vol-targeting) per LM Master §7 routing PRE-COMMIT.

### 0.1 Cycle position

Cycle-4 EXPLORATION **4 of 10** (cycle-4 started at /028 post-/027 TF closeout). Precedents:
- /028 — per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) → **PROMISING** +0.598 OOS Δ
- /029 — per-cohort-specialization-DOT-v2 (symmetric BTC gate ±8%) → **EXPLORATION-TECHNICAL-FAILURE** (wall-clock cap breach at 2h)
- /030 — meta-labeling (M2 binary per-model A/C/D; E DROPPED) → **NEGATIVE-CATASTROPHIC** F1 OOS Δ -0.81
- /031 = THIS — `composite_inv_concurrency` sample-weighting at FULL baseline M1 budget

6 EXPLORATIONs remain after /031; earliest CONFIRMATION at /037 (10 EXPLORATION precedents accumulate /028 forward).

### 0.2 LM Master Phase 4.5 coordination slot

LM Master (`f07c494`) returned BINDING analysis with THREE LOAD-BEARING calls:

1. **The pivot from literal AFML §4.6 `uniq × inv_conc` to `inv_concurrency_only` is LEGITIMATE and structurally orthogonal to /016's `uniqueness_only` closure** (§1) — three load-bearing distinctions: (a) distributional std 0.33 vs 0.003 (100× wider); (b) Kish ratio 0.899 vs ~1.0 (real down-weighting visible); (c) pooled Spearman composite vs uniqueness_only 0.034 (between-symbol weight ratio is the load-bearing freedom for pooled Model A).

2. **STRICT REPLICATION of `bounds_profile="v1_pruned_axis016"`** for attribution cleanliness (§2) — DO NOT modify hyperparameter bounds. The 6-tweak alternative (tighten num_leaves 63→47, raise min_child_samples 20→30 floor, tighten learning_rate 0.10→0.07 ceiling, etc.) is exploitation-oriented and defensible BUT muddies orthogonality attribution.

3. **3 mandatory basin-stability validations** at the 5-seed inner ensemble (§3) — Validation 1 cross-seed Optuna best-trial Sharpe std/mean ≤ 0.25 PASS; Validation 2 per-cell best-param Spearman ≥ 0.50 across 5 seeds; Validation 3 trade-roster overlap baseline ↔ /031 OOS per symbol within [35%, 75%]. Distinguishes "axis edge" from "M1 basin-relocation" per /030 root-cause precedent.

**Attribution ambiguity flag** (LM Master §1 closing): PATH A at 5-seed × 50 trials CONFOUNDS axis orthogonality with budget control. /031 cannot independently confirm BOTH in a single iteration. If /031 fires PROMISING or INERT-FAV, /032 = budget-control (3-seed × 18 trials replicate at axis-edge isolation). LM Master §7 routing PRE-COMMIT codifies this.

**QR ADOPTS all 9 of 9 LM Master adjudications**. Full Response Map in Section 3.4.

### 0.3 EDA finding (Phase 1 numerical evidence)

From `analysis/iteration_v1-031/composite_variants_portfolio.csv` (committed `0cff4b8`):

| Variant | per-sym ρ baseline max | per-sym ρ uniqonly max | pooled ρ baseline | pooled ρ uniqonly | VALID (all < 0.90)? |
|---|---|---|---|---|---|
| afml_literal (uniq × inv_conc) | +0.362 | **+1.000** | -0.020 | +0.297 | **NO** |
| abs_pnl_x_uniq | +0.997 | +0.373 | +0.934 | +0.319 | **NO** (collinear baseline) |
| **inv_concurrency_only** | **+0.072** | **+0.199** | **-0.093** | **+0.034** | **YES** |
| log_inv_c | +0.072 | +0.199 | -0.093 | +0.034 | **YES** (monotone transform) |

**Reading**: `inv_concurrency_only` is THE ONLY composite variant genuinely orthogonal to BOTH baseline `abs_pnl` AND /016's closed `uniqueness_only`. AFML literal at v1 8h labels is per-symbol DEGENERATE (per-symbol Spearman = 1.000 with /016 closure — mechanically reproduces /016's NEG-CAT result at any budget).

### 0.4 Cycle-4 cadence ledger summary

Cycle-4 EXPLORATIONs to date: /028 PROMISING (+0.598), /029 TF (wall-clock), /030 NEG-CAT (-0.81), /031 = THIS. 6 EXPLORATIONs remaining; CONFIRMATION earliest at /037.

### 0.5 EXPLORATION-WITH-BUDGET-EXCEPTION declaration (MANDATORY)

**Mode tag**: **EXPLORATION-WITH-BUDGET-EXCEPTION** at 6h CONFIRMATION-mode wall-clock cap.

**Justification**: LM Master /030 §8 LOAD-BEARING constraint (codified pre-/031 dispatch): "Single-seed × n_trials=18 + 3-seed inner ensemble destroyed cross-symbol basin stability. Repeating this compute compromise on /031 will produce another NEG-CAT regardless of axis chosen." Sample-weighting at /016 EXPLORATION budget at 3-seed × 18 trials WAS the configuration that produced cycle-3 NEG-CAT closure on `uniqueness_only`; reproducing the configuration on `inv_concurrency_only` (orthogonality notwithstanding) risks reproducing the basin-shift artifact.

PATH A at 5-seed × 50 trials × PRUNED features = projected 3.6h modal wall-clock per `analysis/iteration_v1-031/wall_clock_scaling.py` (Step 4 scaling factor 4.32× from /016 anchor: `(5/3)^0.85 × (50/18) × 1.0`). HONORS LM Master /030 §8 mandate; VIOLATES EXPLORATION 2h soft cap; INSIDE CONFIRMATION-mode 6h hard cap with 40% margin at modal, 17% margin at kill-switch (5.0h).

**LM Master §8 ENDORSEMENT** (verbatim): "ENDORSE QR PATH A. The /030 §8 mandate is BINDING and the budget exception is CORRECT. The 2h cap is a SOFT discipline; the /030 §8 mandate is a HARDER constraint. The /030 §8 supersedes the 2h cap specifically when an axis is sensitive to M1 basin stability AT the v1 EXPLORATION budget. Sample-weighting is precisely such an axis."

Wall-clock kill-switch armed at 5.0h (LM Master §8 protocol).

### 0.6 Axis Family Declaration + Rotation Discipline (v1 mandatory)

**This iter's family**: `sample-weighting` (NINTH family in v1; previously closed at /016 for `uniform` + `uniqueness_only`; **REVIVED via the orthogonal `inv_concurrency_only` pivot per LM Master §1**). The /016 closure does NOT extend per LM Master's three load-bearing distinctions (distributional shape, Kish behavior, per-symbol vs pooled disagreement).

**Prior 5 EXPLORATIONs** (excluding /026 sanity slot + /027 CONFIRMATION-TF which are exempt per skill Rule 4):

| iter | axis family | verdict |
|---|---|---|
| /024 | model-arch (regime-conditional sub-models) | NEG-clean |
| /025 | feature-family (OI delta z-score) | LEARNED-NEG-CAT |
| /028 | per-cohort-specialization-LTC-v2 (atr_sl=1.0 LABEL-shift) | PROMISING +0.598 |
| /029 | per-cohort-specialization-DOT-v2 (symmetric BTC gate) | TECHNICAL-FAILURE |
| /030 | meta-labeling (M2 binary per-model A/C/D) | NEG-CATASTROPHIC -0.81 |

**Rotation status**: **VALID** (categorically). The prior 5 disperse across **3 distinct families** (feature-family/1, per-cohort-specialization/2, model-arch/1, meta-labeling/1). Not same-family-5-of-5 monoculture. Additionally, `sample-weighting` was last attempted at /016 (cycle-3); since /016 there have been ≥15 EXPLORATIONs in OTHER families — the axis family is NOT being re-attempted in monoculture defiance.

**Rotation rationale**: `sample-weighting` is structurally orthogonal to the prior 5. Specifically: (a) NOT model-arch — LightGbm architecture unchanged; (b) NOT feature-family — V1_FEATURE_COLUMNS_PRUNED 43 cols UNCHANGED; (c) NOT per-cohort — universe and per-model dispatch UNCHANGED; (d) NOT meta-labeling — no second-stage classifier added; (e) NOT labeling — triple-barrier σ_t / atr_tp / atr_sl UNCHANGED. Per LM Master §1: the mechanism modifies LightGBM's loss-surface gradient via per-row weight inversion at training-row dispatch level. Mechanism class: "Optuna training-objective domain reshape via per-row weighting".

---

## Section 1 — Sample-weighting composite EDA (IS-only numerical evidence)

All numbers cite committed CSVs at `analysis/iteration_v1-031/`. Scripts: `sample_weighting_composite_eda.py` (literal AFML), `composite_variants_eda.py` (8 alternatives) — both committed `0cff4b8`.

### 1.1 Concurrency at entry distribution (`concurrency_profile.csv`)

IS-only candidates per V1_BASELINE_UNIVERSE:

| Symbol | n_candidates | uniqueness mean (std) | concurrency mean (max, p95) | inv_conc mean (std) |
|---|---|---|---|---|
| BTCUSDT | 5713 | 0.0456 (0.0033) | **21.96 (22, 22.0)** | 0.00184 (0.0346) |
| ETHUSDT | 5713 | 0.0456 (0.0033) | **21.96 (22, 22.0)** | 0.00184 (0.0346) |
| LINKUSDT | 5664 | 0.0456 (0.0033) | **21.96 (22, 22.0)** | 0.00185 (0.0347) |
| LTCUSDT | 5673 | 0.0457 (0.0035) | **21.91 (22, 22.0)** | 0.00397 (0.0433) |
| DOTUSDT | 5011 | 0.0456 (0.0035) | **21.95 (22, 22.0)** | 0.00210 (0.0369) |

**Reading**: at 8h candles + 21-candle timeout + per-bar label entry, EVERY bar sits inside ~21-22 overlapping label windows. **99.63% of BTC/ETH/LINK bars and 99.58% of DOT/LTC bars sit at concurrency = 22 (max-saturated)**. The remaining 0.4% of bars (concurrency < 22) carry rare-isolation signal — these are the bars that `inv_concurrency_only` up-weights in LightGBM training.

### 1.2 Distributional std (100× wider than /016 uniqueness_only)

From `composite_variants_portfolio.csv` row `inv_concurrency_only`:
- **pooled std = 0.3344** (100× larger than /016 `uniqueness_only` per-symbol std ≈ 0.0033)
- pooled min = 0.987 (mean-normalized lower bound around the saturated bars)
- pooled max = 21.77 (mean-normalized upper bound at the rare concurrency=2 outlier bar)
- 0.30% of bars carry weight > 1.5; 0% carry weight < 0.5

**Mechanism evidence**: LightGBM's `sample_weight` parameter scales gradient contributions linearly. A weight std of 0.33 (pooled) vs 0.003 (uniqueness_only) means the loss-surface gradient on rare isolated bars contributes ≈100× more to the per-iteration TPE-objective gradient at /031 than at /016. The mechanism is mathematically alive at /031 in a way it is NOT at /016 (where uniqueness_only collapses to a uniform constant per LM Master §1 Distinction 1).

### 1.3 Spearman orthogonality matrix (`spearman_orthogonality.csv`)

Per-symbol AND portfolio-pooled Spearman ρ:

| Symbol | composite vs uniqueness | composite vs inv_concurrency | composite vs baseline abs_pnl |
|---|---|---|---|
| BTCUSDT | 0.9999 | 0.117 | 0.218 |
| ETHUSDT | 0.9999 | 0.117 | 0.281 |
| LINKUSDT | 0.9999 | 0.117 | 0.350 |
| LTCUSDT | 0.9999 | 0.201 | 0.335 |
| DOTUSDT | 0.9999 | 0.128 | 0.362 |
| **PORTFOLIO_POOLED** | **0.297** | **0.127** | **-0.020** |

From `composite_variants_portfolio.csv` row `inv_concurrency_only` (the PIVOTED variant proposed at /031):
- **pooled vs baseline abs_pnl**: **-0.093** (orthogonal; near-zero)
- **pooled vs uniqueness_only**: **+0.034** (orthogonal; far from /016 closure)
- per-symbol vs baseline abs_pnl max: +0.072 (orthogonal at the per-symbol level too)
- per-symbol vs uniqueness_only max: +0.199 (well below 0.90 orthogonality floor)

**Reading**: `inv_concurrency_only` is the ONLY variant in EDA 2.3 (`composite_variants_portfolio.csv`) that passes BOTH per-symbol AND pooled orthogonality gates. The reshape is BETWEEN symbols (each symbol's `c_at_entry` has different shape relative to the others, even though within-symbol the modal concurrency value is identical 22) — this between-symbol weight ratio is the LOAD-BEARING freedom Optuna can exploit on pooled Model A (BTC+ETH).

### 1.4 Kish n_eff ratio (`composite_variants_portfolio.csv`)

| Mode | Pooled Kish n_eff | Pooled Kish ratio |
|---|---|---|
| `uniform` | 27774 | 1.000 (by construction) |
| **`baseline_abs_pnl`** | 23332 | **0.840** |
| `uniqueness_only` (from /016 closure) | 27772 | ≈ 1.0 (degenerate, uniform-equivalent at 99.6% of bars) |
| **`inv_concurrency_only`** | 24980 | **0.899** |
| `afml_literal` | 858 | 0.031 (catastrophic — one-symbol outliers dominate) |

**Reading**: `inv_concurrency_only` Kish 0.899 sits BETWEEN uniform 1.0 and baseline_abs_pnl 0.84. Real down-weighting visible per LM Master §1 Distinction 2 ("mechanism is alive, not vacuous"). The reshape is mild (6% better than baseline at maintaining effective sample size) — NOT degenerate like afml_literal where 8% of pooled samples dominate via concurrency=2 outliers.

### 1.5 Per-month Kish profile (`per_month_kish.csv`)

Extremes that LM Master §4 NEG-CAT tail anchors on:

| Symbol | Month | Composite Kish ratio | Note |
|---|---|---|---|
| BTCUSDT | 2020-01 | **0.147** | Lowest at /031 — early BTC cycle, thin trade roster |
| ETHUSDT | 2020-01 | **0.147** | Same month, twin profile (pooled Model A symmetry) |
| DOTUSDT | 2020-09 | 0.207 | DOT genesis era |
| LTCUSDT | 2020-01 | 0.209 | |
| LTCUSDT | 2022-03 | 0.225 | LUNA / 3AC crisis |

**0.06% of (symbol, month) cells carry Kish ratio < 0.30**. Per LM Master §4 NEG-CAT tail (12%): "Extreme weight spikes at LTC (Kish ratio 0.036)... could nuke a single training month." The 2020-01 BTC/ETH 0.147 floor is the most concrete NEG-CAT signature; if Optuna at 5-seed × 50-trials gets bumped into a basin during this single month and the basin happens to overfit IS to the heavy-weight rare bars in that month, the OOS catastrophe propagates symmetrically across A_BTC + A_ETH. Probability assessment via LM Master §4: 12% NEG-CAT tail conditional on this signature.

### 1.6 Weight distribution per-symbol (`weight_distribution.csv`)

Composite (=inv_concurrency_only with mean-renormalization) percentile profile per symbol:

| Symbol | p25_norm | p50_norm | p75_norm | p95_norm | max_norm | frac > 0.9 |
|---|---|---|---|---|---|---|
| BTCUSDT | 0.752 | 0.752 | 0.752 | 0.752 | **264.98** | 0.56% |
| ETHUSDT | 0.752 | 0.752 | 0.752 | 0.752 | 264.98 | 0.56% |
| LINKUSDT | 0.751 | 0.751 | 0.751 | 0.751 | 264.41 | 0.56% |
| LTCUSDT | 0.632 | 0.632 | 0.632 | 0.632 | 222.51 | 1.32% |
| DOTUSDT | 0.727 | 0.727 | 0.727 | 0.727 | 256.09 | 0.62% |

**Reading**: 99% of bars sit at the per-symbol "modal" weight (0.63 to 0.75), corresponding to concurrency = 22 (max-saturated). The 0.4-1.3% of bars carrying weight > 0.9 (and a much smaller subset reaching 264x the mean) constitute the rare-isolation signal. **LightGBM at 5-seed × 50-trials × PRUNED has the search-space to either learn from these rare-high-weight bars OR over-fit to them, depending on Optuna basin selection.** Per LM Master §4: combined PROMISING tail 40% > combined NEG tail 30% — net expected OOS Δ +0.04.

---

## Section 1.5 — /016 PRIOR (MANDATORY per Brief structure)

**Reference**: `briefs-v1/iteration_v1-016/research_brief.md` + `diary-v1/iteration_v1-016.md` (v1 EXPLORATION, NEGATIVE-catastrophic clean).

**/016 setup**: Sample-weighting axis, three modes tested: `uniform`, `uniqueness_only` (= window-averaged `mean(1/c_t)` over each candidate's full 21-bar label window), `afml_composite_literal_alpha=1.0`. Budget = 3-seed × 18 trials × PRUNED features × 5 syms × 8h. **Result**: NEGATIVE-catastrophic clean — `uniform` and `uniqueness_only` rank-identical to baseline-`abs_pnl` (per-symbol Spearman ρ = 0.997, mechanism vacuous).

**Sample-weighting axis closure at /016**: cycle-3 closed `uniform` AND `uniqueness_only` as "mechanism degenerate at v1 8h labels — modal concurrency=22 saturates inverse-uniqueness to a constant".

**Why /031 ≠ /016 (per LM Master §1 three load-bearing distinctions)**:

1. **Distributional shape**: /016 `uniqueness_only` was window-AVERAGED (each candidate's weight = mean of `1/c_t` over its FULL 21-bar label window) → per-symbol weight std ≈ 0.0033 (degenerate). /031 `inv_concurrency_only` is SCALAR per-candidate `1/c_at_entry(t)` evaluated AT entry bar only → per-symbol weight std ≈ 0.33 — **100× wider weight dispersion** (LM Master §1 Distinction 1).

2. **Kish behavior**: /016 `uniqueness_only` Kish ≈ 1.0 (uniform-equivalent — the literal AFML reduces to constant at 99.9% of bars under v1's saturated concurrency). /031 `inv_concurrency_only` Kish 0.899 pooled — REAL down-weighting visible. Mechanism is alive, not vacuous (LM Master §1 Distinction 2).

3. **Per-symbol vs portfolio-pooled disagreement**: /016 closed at uniform-equivalent (per-symbol Spearman 0.997 with uniform). /031 per-symbol Spearman composite vs uniqueness = 0.9999 (rank-identical within symbol) BUT pooled = 0.297 — the inv_concurrency mechanism reshapes BETWEEN-symbol weight magnitudes via per-symbol concurrency distribution shifts. Pooled Spearman vs uniqueness_only is **0.034** — totally distinct ordering. Within-symbol ranking is NOT the relevant axis for LightGBM TPE on pooled Model A (BTC+ETH), where the BETWEEN-symbol weight ratio is the load-bearing freedom (LM Master §1 Distinction 3).

**Section 1.5 prior calibration** (mandatory acknowledgment): The /016 closure is a CONDITIONAL closure — it closed `uniform` + `uniqueness_only` at v1 8h labels. The orthogonal variant `inv_concurrency_only` was NOT tested at /016 (it was identified in EDA 2.3 as a downstream pivot from the literal AFML closure). Per LM Master §1 Verdict: "PIVOT LEGITIMATE. Single-axis discipline INTACT. /016 closure does NOT extend." But per LM Master §6 calibration: 1/1 NEG-CAT prior at this axis family (`feedback_v1_abs_pnl_weighting_structural.md` warns abs_pnl is structural to v1's edge). MEDIUM directional confidence — the orthogonal pivot is mathematically justified but the axis-family base rate is unfavorable.

**Differences /031 vs /016**:
1. Budget: 5-seed × 50 trials (/031) vs 3-seed × 18 trials (/016) — 4.32× compute
2. Weight definition: scalar per-bar `1/c_at_entry(t)` (/031) vs window-averaged `mean(1/c_t)` over 21-bar label window (/016)
3. Distributional spread: 100× wider weight std (Section 1.2 evidence)
4. Mechanism activity: Kish 0.899 (alive) vs Kish ~1.0 (vacuous)
5. Single-axis isolation: BIT-IDENTICAL labels, features, universe, risk gates, hyperparameter bounds (`v1_pruned_axis016` STRICT REPLICATION) — the ONLY axis change is `sample_weight_mode`

---

## Section 2 — Falsifier pre-registration (per LM Master §5)

All falsifier bands are LM Master §5 verbatim with QR ADOPTING all 5 F-AXIS items.

### F-AXIS #1 — Sample weights actually applied (wiring binary check)

**Expected behavior**: `run.log` must contain `[sample_weight_mode=composite_inv_concurrency]` print for every Optuna trial dispatch on every (model, month) cell. Expected cell count = 53 months × 5 models (A_BTC, A_ETH, C, D, E) = **265 cells** (Model E participates because the axis is the M1 weight mode at training-row level — Model E receives weights too; /030's Model E EXCLUSION was M2-specific and does NOT apply at /031).

**PASS criterion**: ≥ **95% of (model, month) cells** emit the weight-mode print.

**FAIL criteria**:
- < 80% of cells emit print → silent fallback to baseline weights → wiring bug; **BLOCK-PENDING-FIX** (per LM Master §5 verbatim)
- < 95% but > 80% → INFO-level only; continue
- Print emits but `sample_weight=None` in LightGBM trial → wiring bug; **BLOCK-PENDING-FIX**

### F-AXIS #2 — Trade count band

- **IS predicted [560, 690] modal 621** (baseline 621; sample-weighting reshapes trial parameters but does not silently change M1 prediction roster from labels)
- **OOS predicted [165, 215] modal 190** (baseline 189)

**CRITICAL THRESHOLD**: **OOS trades < 150 → caps verdict at TECHNICAL-FAILURE-SILENT-FALLBACK** (LM Master §5 + Section 7.1; the axis cannot silently zero-out the M1 prediction roster — that would indicate wiring bug or silent baseline fallback)

### F-AXIS #3 — Weight-reach-LightGBM proof (cross-seed best-param Spearman)

**LM Master §5**: "More tractable proxy than weighted-training-loss log parsing: per (Model A, month) cell, compute Spearman of Optuna best `learning_rate` choices across 5 seeds. If Spearman vs baseline best-params > 0.90, axis is silently no-op."

**PASS criterion**: median across (Model A, month) cells of Spearman(best-trial `learning_rate`, baseline best-trial `learning_rate`) **< 0.90** (axis is meaningfully changing Optuna's basin choice)

**FAIL criterion**: median Spearman > 0.95 → axis is silently no-op → BLOCK-PENDING-FIX

### F-AXIS #4 — n_eff per (model, month) cell

**Predicted band**: median n_eff per cell ∈ **[14, 22]** at 5-seed × 50 trials × PRUNED-43.

**FAIL criteria**:
- median n_eff per cell **< 8** → loss surface collapse → axis attribution INVALID → reclassify as NEGATIVE-BASIN-COLLAPSE
- median n_eff per cell **> 30** → axis amplifying loss-surface diversity unexpectedly → INFO-level only; continue (potentially positive signal)

### F-AXIS #5 — OOS TP-exit count LOAD-BEARING (transferred from /028 + /030)

- Post-/031 OOS TP-exit count ≥ **15** (baseline OOS TP ≈ 40; the axis should retain ≥40% of TP-class trades)
- **Model D OOS TP count ≥ 3 LOAD-BEARING** (baseline D OOS TP ≈ 7; LTC-long catastrophe lesson from /028 + /030)

**FAIL criterion**: OOS TP < 15 OR Model D OOS TP < 3 → caps verdict at PROMISING-INERT regardless of headline F1 Δ.

### F-AXIS-MECHANISM compound (5 sub-checks)

1. F-AXIS-M #1 = F-AXIS #1 (binary wiring assertion, 265 expected cells)
2. F-AXIS-M #2 = F-AXIS #2 (trade-count band; OOS < 150 → silent fallback)
3. F-AXIS-M #3 = F-AXIS #3 (cross-seed best-param Spearman)
4. F-AXIS-M #4 = F-AXIS #4 (n_eff per cell)
5. F-AXIS-M #5 = F-AXIS #5 (OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING)

All sub-checks pre-registered. F-AXIS-M #1, #2, #5 are verdict-capping.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1 mandatory)

**Declaration**: **HIGH-RISK**.

**Reason** (per `feedback_axis_saturation_predictor.md` and `feedback_v1_high_risk_declaration_discipline.md`): sample-weighting **reshapes Optuna's training-objective domain**. LightGBM's loss-surface gradient receives per-row weights inverted by concurrency at entry; the gradient surface that TPE Optuna navigates IS modified. The /016 precedent established that the axis is basin-shift-vulnerable. The /030 root-cause was M1 budget downshift basin relocation — sample-weighting is the OTHER mechanism class that can produce basin relocation (loss-surface reshape via weight inversion).

**Mitigation** (LM Master §3 3 basin-stability validations MANDATORY, NOT opt-in):
1. Validation 1 (Section 2.6 below): cross-seed Optuna best-trial Sharpe std/mean ≤ 0.25 PASS
2. Validation 2: per-cell best-param Spearman across 5 seeds ≥ 0.50 PASS
3. Validation 3: trade-roster overlap baseline ↔ /031 OOS per symbol within [35%, 75%]

**NOT a CONFIRMATION** (single-seed=42 outer; 5-seed inner ensemble per LM Master §8 mandate). EXPLORATION-WITH-BUDGET-EXCEPTION framing per Section 0.5 — the 5-seed × 50-trials is the INNER ensemble configuration (mirror of /016 EXPLORATION pattern at higher trials) needed to validate axis-edge AT the v1 EXPLORATION envelope. /032 budget-control at 3-seed × 18 trials per LM Master §7 routing PRE-COMMIT is the budget-isolation iteration if /031 fires PROMISING.

**v1 HIGH-RISK rule per feedback memory**: multi-seed validation opt-in MANDATORY. PATH A IS the multi-seed validation (5-seed inner). Single-outer-seed risk acknowledged; basin-stability Validation 1 (Section 2.6) is the cross-seed measurement that catches single-outer-seed basin lottery.

**Pre-commit-to-CONFIRMATION tripwire**: NOT armed at /031. If /031 fires PROMISING (Δ ≥ +0.05), /037-CONFIRMATION composition does NOT auto-include sample-weighting bundle — /032 (budget-control) must validate axis-edge first per LM Master §1 closing attribution ambiguity flag.

---

## Section 2.6 — Basin-stability validations (per LM Master §3 MANDATORY)

The /030 root cause was 3-seed basin instability at 18-trial Optuna budget. 5-seed × 50-trials at baseline is the budget-control. THREE concrete cross-seed validations are MANDATORY (not opt-in) per LM Master §3.

### Validation #1 — Cross-seed Optuna best-trial Sharpe variance

**Computation**: For each (model, month) cell, parse `run.log` for `Trial X finished with value SR` events; identify the BEST trial per inner-seed (5 seeds total per cell). Compute median across the 5 inner seeds' best-trial Sharpes. Then compute per-cell `std(best_sharpe_across_5_seeds) / mean(best_sharpe_across_5_seeds)`. Median this CV across all 265 cells (53 months × 5 models).

**PASS threshold**: median(std/mean across cells) ≤ **0.25**.

**FAIL threshold**: median(std/mean across cells) > **0.40** → 5-seed is itself in a basin-lottery regime → axis-attribution INVALID → reclassify as **NEGATIVE-BASIN-RELOCATION** (NOT NEGATIVE-AXIS-EDGE).

**Intermediate (between 0.25 and 0.40)**: INFO-level only; basin stability not catastrophic but not clean; report directionally in Section 4 verdict matrix.

### Validation #2 — Per-cell best-param Spearman across seeds

**Computation**: For each (model, month) cell, extract the best-trial hyperparameter vector `[num_leaves, learning_rate, min_child_samples]` for each of 5 inner seeds. Compute the Spearman correlation of best-trial hyperparameter vectors across the 5 seeds (10 pairs per cell). Median across 265 cells.

**PASS threshold**: median Spearman ≥ **0.50** (seeds agree on basin location → axis effect attributable to weight reshape, not seed lottery)

**FAIL threshold**: median Spearman < **0.30** → seeds disagree on basin → axis effect cannot be attributed → reclassify as NEGATIVE-BASIN-RELOCATION.

### Validation #3 — Trade-roster overlap baseline ↔ /031 OOS per symbol

**Computation**: Compute per-symbol OOS trade-roster overlap (Jaccard or set intersection / union) between baseline `v0.v1-baseline-corrected` (189 OOS trades, recorded in `reports-v1/iteration_v1-baseline/out_of_sample/trades.csv`) and /031 OOS trades.

**PASS band**: per-symbol overlap ∈ **[35%, 75%]** (axis materially reshapes roster, but not OBLITERATING basin).

**FAIL criteria**:
- per-symbol overlap < **25%** for ANY symbol → basin relocation (NEG-CAT mechanism mirror of /030 24% DOT overlap) → reclassify as NEGATIVE-BASIN-RELOCATION
- per-symbol overlap > **80%** for ALL symbols → axis not biting → reclassify as INERT-NO-EFFECT (weight reshape didn't reach Optuna's basin choice)

### Validation timing

All 3 validations executed at Phase 7 (evaluation) per `briefs-v1/iteration_v1-031/research_brief.md` Section 4 verdict matrix. Inputs: `run.log` (Validations 1+2) + `reports-v1/iteration_v1-031/out_of_sample/trades.csv` + `reports-v1/iteration_v1-baseline/out_of_sample/trades.csv` (Validation 3).

**Forensic log emission requirement**: QE Phase 6 implementation MUST log per (model, month) cell:
- Each inner-seed's best-trial Sharpe (5 values)
- Each inner-seed's best-trial hyperparameters (`num_leaves`, `learning_rate`, `min_child_samples`)
- Validation 1 + 2 are NOT computable without these logs.

---

## Section 3 — Implementation Spec

### 3.1 Universe + features

- **`V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")`** — **UNCHANGED 5 symbols**
- **M1 feature set**: `V1_FEATURE_COLUMNS_PRUNED` (43 cols) — **FROZEN UNCHANGED** from /028/030
- **Cross-asset features**: existing v1 baseline cross-asset infrastructure unchanged

### 3.2 Labels (M1 — UNCHANGED from baseline)

M1 retains baseline labeling exactly as `v0.v1-baseline-corrected`:
- **Triple-barrier σ_t**: EWMA 14d on past-only returns (per-model baseline)
- **`atr_tp_multiplier = 2.9` (Model A) / 3.5 (C, D, E)** UNCHANGED
- **`atr_sl_multiplier = 1.45` (Model A) / 1.75 (C, D, E)** UNCHANGED
- **`label_timeout = 21 bars`** (7 days at 8h) UNCHANGED
- **Embargo at walk-forward boundary**: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED (post-/058 FIX preserved)

### 3.3 Sample-weighting mode (NEW — THE ONLY AXIS CHANGE)

**New CLI flag**: `--sample-weight-mode composite_inv_concurrency`

**Weight formula** (mean-renormalized per (symbol, training_window)):

```
For each (symbol, training_window):
  For each bar t in training_window:
    c_at_entry(t) = count of label windows ACTIVE at bar t (same-symbol only)
                  = number of bars t' ≤ t such that bar t' has a label window
                    [t', t' + label_timeout_minutes] that contains t
  raw_weight_t = 1 / c_at_entry(t)
  weight_t = raw_weight_t / mean(raw_weight_t over training_window for this symbol)
  # Mean-renormalized per (symbol, training_window) so each symbol contributes
  # the same total weight to the pooled training row dispatch on Model A
```

**Property**: per-symbol weight sum = N (training window size), preserving relative pool contribution; the only thing that changes is the BAR-LEVEL gradient contribution distribution.

**Implementation path**: extend `src/crypto_trade/strategies/ml/labeling.py` OR create new `src/crypto_trade/strategies/ml/sample_weighting.py` (QE Phase 6 choice; prefer new module for axis isolation).

**Compute cost** (per LM Master §8 Step 5): O(n) sweep-line per training cell to compute `c_at_entry`. ~5-10 sec per cell × 265 cells ≈ 22-44 min ADDITIONAL but `c_at_entry` is per-bar and can be precomputed ONCE for the master frame across all training windows → ~10 min total overhead. Negligible vs the 3.6h modal wall-clock.

**DO NOT modify abs_pnl baseline path**: the `composite_inv_concurrency` mode is a NEW branch in `LightGbmStrategy._compute_sample_weights` (or equivalent) after the existing `uniform` / `uniqueness_only` / `abs_pnl` chain. The baseline path (`abs_pnl`) is UNCHANGED — only fires under the NEW mode flag.

**Look-ahead audit** (mandatory per `feedback_no_cheating.md`): `c_at_entry(t)` uses ONLY label windows opened at bars t' ≤ t. The label window for bar t' starts at bar t' itself (entry) and extends forward; for `c_at_entry(t)` we count windows where t' ≤ t ≤ t' + label_timeout. This is BY CONSTRUCTION past-only — no future bars contribute to the weight at bar t. **Mandatory unit test in Section 10.3.**

### 3.4 LM Master Phase 4.5 Response Map (MANDATORY — address each §1-§9)

#### §1 Mechanism Pivot Adjudication: PIVOT ENDORSEMENT

**ADOPTED**. Brief Section 0 H1, Section 1.5 distinction-3 narrative, Section 3.3 weight formula all anchor on `inv_concurrency_only` per the orthogonality grounds. The literal AFML `uniq × inv_conc` is REJECTED per EDA 2.1-2.2 degeneracy.

#### §2 Hyperparameter Region Recommendation: STRICT REPLICATION

**ADOPTED**. `bounds_profile="v1_pruned_axis016"` STRICT REPLICATION at /031. The 6-tweak exploitation-oriented alternative (tighten num_leaves 63→47, raise min_child_samples 20→30 floor, etc.) is REJECTED for attribution cleanliness per LM Master §2 closing: "QR picks; both are defensible. STRICT-REPLICATION is methodologically cleaner."

#### §3 Basin-Stability Validation: 3 validations MANDATORY

**ADOPTED VERBATIM**. Section 2.6 mandates all 3 (Validation 1 cross-seed Sharpe std/mean ≤ 0.25; Validation 2 per-cell best-param Spearman ≥ 0.50; Validation 3 trade-roster overlap ∈ [35%, 75%]). Forensic log emission requirements specified.

#### §4 Mechanism Recommendation + Prior Probability Table: ADOPT

**ADOPTED VERBATIM**:

| Verdict cell | Probability | OOS Δ band | Rationale |
|---|---|---|---|
| **PROMISING-clean** (Δ ≥ +0.20) | **17%** | [+0.20, +0.55] modal +0.32 | Real signal IF inv_concurrency reshapes Optuna's weight surface AND rare-bar up-weighting captures structural concurrency-decorrelation moments |
| **PROMISING-INERT-FAV** (Δ +0.05 to +0.20) | **23%** | [+0.05, +0.20] modal +0.12 | Modal-positive cell. Reshape is real (Kish 0.899) but lift is mechanical not signal-discovery |
| **INERT-NO-EFFECT** (Δ ∈ [-0.10, +0.10]) | **30%** | [-0.10, +0.10] modal -0.02 | **MODAL.** TPE at 5-seed × 50 trials washes out modest weight dispersion. 99% of bars at saturated concurrency dominate; 1% rare bars don't move loss surface enough |
| **NEGATIVE-OVER-FILTER** (Δ -0.40 to -0.10) | **18%** | [-0.40, -0.10] modal -0.20 | Up-weighting rare bars over-fits to noise on those bars; Optuna picks hyperparameters that misgeneralize |
| **NEGATIVE-CATASTROPHIC** (Δ ≤ -0.40) | **12%** | [-0.80, -0.40] modal -0.55 | Tail. 0.06% extreme weight spikes at LTC (Kish 0.036) + BTC/ETH 2020-01 0.147 could nuke training month |

**Modal cell**: **INERT-NO-EFFECT 30%**. Combined PROMISING tail 40% > combined NEG tail 30%. **Net expected OOS Δ: +0.04**.

#### §5 Falsifier Pre-Registration: F-AXIS #1-#5 VERBATIM

**ADOPTED VERBATIM** (Section 2 above). All 5 F-AXIS items carried into brief Section 2; F-AXIS #5 OOS TP ≥ 15 + Model D OOS TP ≥ 3 LOAD-BEARING transferred from /028/030.

#### §6 Track-Record Commentary: MEDIUM confidence ACKNOWLEDGED

**ACKNOWLEDGED**. LM Master methodology 8/8 perfect; directional 4/10 = 40%; for sample-weighting MEDIUM confidence (EDA is dense; budget controlled; mechanism mathematically simple; but axis-family has 1/1 NEG-CAT prior at v1). QR acknowledges uncertainty in Section 0.5 prior recalibration acceptance.

#### §7 Routing Recommendation /032: ADOPT PRE-COMMIT

**ADOPTED PRE-COMMIT**:
- **/031 PROMISING-clean (17%)** → **/032 = `inv_concurrency_only` at 3-seed × 18 trials (BUDGET-CONTROL)** per LM Master §7 explicit — isolates axis-edge from budget-validity confound
- **/031 PROMISING-INERT-FAV (23%)** → /032 = `inv_concurrency_only` stacking with NEW second axis
- **/031 INERT (30% modal)** → /032 = **NEW axis family** (universe expansion / trend-scanning labels / per-trade vol-targeting per LM Master §7)
- **/031 NEG-OVER (18%)** → /032 = NEW axis family; sample-weighting CLOSED at v1
- **/031 NEG-CAT (12%)** → /032 = closure-reconciliation + NEW axis family; sample-weighting PERMANENTLY CLOSED for v1

NO third sample-weighting variant attempted per LM Master §7 strong prior.

#### §8 Wall-Clock + Budget Exception Adjudication: PATH A ENDORSED

**ADOPTED**. PATH A (5-seed × 50 trials × PRUNED × 5 syms × 8h) at 3.6h modal wall-clock. EXPLORATION-WITH-BUDGET-EXCEPTION declared (Section 0.5). 6h CONFIRMATION-mode hard cap. Kill-switch armed at 5.0h. No CONFIRMATION-spec ENSEMBLE_SIZE escalation needed (5-seed inner IS the configuration, NOT 10).

**Wall-clock risk mitigations adopted from LM Master §8**:
1. Pre-mortem checkpoint at month 10 via run.log monitor: if projected total > 5h at month 10, ABORT and document.
2. QR/QE will NOT compress n_trials to 35 mid-run as wall-clock saving measure (Section 3.5 LOCKS n_trials = 50).

#### §9 Seven adjudication questions

- **Q1 Composite formula**: ENDORSE pivot to `inv_concurrency_only`. ADOPTED (Section 3.3 formula).
- **Q2 Hyperparameter region**: KEEP `bounds_profile="v1_pruned_axis016"` STRICT. ADOPTED (Section 3.5 config).
- **Q3 Per-model differential**: BROADLY SYMMETRIC. ADOPTED INFORMATIONAL. All 5 symbols have concurrency mean 21.91-21.96 — nearly identical. Per-model OOS Δ within ± 0.15 of portfolio Δ expected.
- **Q4 Verdict priors**: SHIFTED. Modal INERT-NO-EFFECT 30% / PROMISING combined 40% / NEG combined 30%. ADOPTED (Section 3.4 §4 table).
- **Q5 Basin-stability variance threshold**: median(std/mean across cells) ≤ 0.25 PASS; > 0.40 FAIL. ADOPTED VERBATIM (Section 2.6 Validation 1).
- **Q6 Wall-clock risk**: SUPPORT EXPLORATION-WITH-BUDGET-EXCEPTION declaration. ADOPTED (Section 0.5).
- **Q7 /032 routing prior**: Strongest prior on **/032 = NEW axis family (universe expansion to SOLUSDT 6th symbol)** at modal INERT outcome. ADOPTED PRE-COMMIT (Section 3.4 §7).

### 3.5 Configuration

- **ENSEMBLE_SIZE = 5** (inner ensemble per LM Master §8 + /030 §8 mandate; **NOT 3, NOT 10**)
- **n_trials = 50** (per LM Master §8 + /030 §8 mandate; **NOT 18, NOT 35**)
- **Outer seed = 42** (single outer seed; EXPLORATION-WITH-BUDGET-EXCEPTION framing per Section 0.5; multi-outer-seed is /037 CONFIRMATION territory not /031 territory)
- **Sample weighting (M1) = `composite_inv_concurrency`** (THE AXIS CHANGE)
- **Bar interval = 8h** UNCHANGED
- **Bounds profile = `v1_pruned_axis016`** STRICT REPLICATION (per LM Master §2 ADOPTED — NOT modified)
- **Risk layers**: R1 per-model baseline (A=OFF, C/D/E=ON); R2 OFF per-model (cycle-2 baseline); R3 ON (project-wide always-on, 70th pctl Mahalanobis OOD on 16 scale-invariant features)
- **Wall-clock HARD CAP = 6h** (CONFIRMATION-mode hard cap per Section 0.5 EXPLORATION-WITH-BUDGET-EXCEPTION)
- **Kill-switch ARMED at > 5.0h** (LM Master §8 protocol)

### 3.6 Wall-clock estimate (5-step label-rate scaling per `feedback_v1_label_rate_wall_clock_scaling.md`)

1. **Precedent iteration**: /016 sample-weighting at ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED + 5-sym + 8h = **~50 min observed**. /031's M1 label-roster is BIT-IDENTICAL to baseline (labels untouched).

2. **Precedent label rate**: /016 = baseline labels. Sample-weighting axis at /016 was tested at baseline labels.

3. **/031 label rate**: SAME (M1 UNCHANGED). Sample-weighting axis at /031 uses baseline labels. Step-3 ratio = **1.0**.

4. **Config scaling factor**: `(5/3)^0.85 × (50/18) × 1.0` = **1.554 × 2.778 × 1.0 = 4.32×**

5. **Axis-specific overhead** (Section 3.3 compute cost): `c_at_entry` precompute is O(n) sweep-line, ~10 min total overhead.

**Total estimate**: 50 min × 4.32 ≈ **216 min = 3.60h modal**. **Kill-switch armed at 5.0h** (38% margin). **Hard cap 6h CONFIRMATION-mode** (40% modal margin; 17% kill-switch margin).

**Cross-check via baseline anchor** (per `wall_clock_scaling.py:scale_from_baseline`): 5-seed × 50 trials × 193-feature baseline = 7h total; PRUNED ~= 0.85× = 5.95h. Diverges from /016 anchor (3.60h) — the /016 anchor is 5-symbol PRUNED and most relevant; the baseline anchor includes additional per-leg dispatch overhead absent at /031 (which is pooled Model A + 3 single-symbol models, same dispatch as /016).

**Configuration locks**: ENSEMBLE_SIZE=5, n_trials=50 LOCKED for the entire run; NO mid-run compression for wall-clock savings per LM Master §8 mandate.

### 3.7 Code changes (src/ — keep minimal)

- **NEW** `src/crypto_trade/strategies/ml/sample_weighting.py` (recommended) OR extension to `labeling.py`:
  - `compute_concurrency_at_entry(symbol_df, label_timeout_bars) → np.ndarray` (per-symbol sweep-line)
  - `compute_composite_inv_concurrency_weights(symbol_df, label_timeout_bars) → np.ndarray` (mean-renormalized)
  - Unit tests at `tests/strategies/ml/test_sample_weighting.py` (per Section 10.3)
- `src/crypto_trade/strategies/ml/lgbm.py`: add `composite_inv_concurrency` branch in the existing `sample_weight_mode` dispatcher (alongside `uniform` / `uniqueness_only` / `abs_pnl`)
- `run_baseline_v1.py`: add `--sample-weight-mode` CLI flag (default = baseline `abs_pnl`); wire to `LightGbmStrategy.__init__`; per LM Master §8 print `[sample_weight_mode=<mode>]` for every Optuna trial dispatch (F-AXIS #1 wiring proof)
- `run_baseline_v1.py` **line 2704 BASELINE catch-all exclusion tuple**: MUST add `v1-031` (per `feedback_v1_dispatch_baseline_catchall_exclusion.md` /030 LESSON — silent baseline fallback at /030 BACKTEST #1 wasted 51 min)

### 3.8 Axis Family Declaration (Critic Check 14 verification path)

- **Axis family**: `sample-weighting` (NINTH family in v1 history; previously closed at /016 for `uniform` + `uniqueness_only`; REVIVED via orthogonal `inv_concurrency_only` pivot per LM Master §1)
- **Justification for revival** (per LM Master §1):
  - NOT a `feature-family` axis — V1_FEATURE_COLUMNS_PRUNED UNCHANGED at M1 layer
  - NOT a `model-arch` axis — LightGbm architecture per Model A/C/D/E UNCHANGED
  - NOT a `labeling` axis — triple-barrier σ_t / atr_tp / atr_sl UNCHANGED
  - NOT a `per-cohort-specialization` axis — universe and per-model dispatch UNCHANGED
  - NOT a `risk-primitive` axis — R1/R2/R3 UNCHANGED
  - **Same family as /016, BUT with /016's three closure-relevant distinctions disentangled** per LM Master §1 (distributional std 100× wider, Kish ratio 0.899 vs ~1.0, pooled vs per-symbol disagreement); the conditional closure at /016 does NOT extend to the orthogonal `inv_concurrency_only` variant
- **Rotation status**: VALID (prior 5 disperse across 3 distinct families; /016 closure is >15 EXPLORATIONs in the past; the family is NOT being re-attempted in monoculture)

---

## Section 4 — Verdict Matrix (F1 OOS Δ band per LM Master §4 ADOPTED)

Pre-committed verdict cells with explicit OOS Δ bands per LM Master §4 + Section 2 falsifier override hierarchy:

| OOS Δ band | Verdict cell | Prior probability (LM Master §4 ADOPTED) | Mechanism interpretation |
|---|---|---|---|
| Δ ≥ +0.20 | **PROMISING-CLEAN** | **17%** | inv_concurrency reshape captures rare-bar structural moments; modal +0.32 |
| Δ ∈ [+0.05, +0.20) | **PROMISING-INERT-FAV** | **23%** | Reshape mechanical (Kish 0.899) but lift small; modal +0.12 |
| Δ ∈ [-0.10, +0.05) | **INERT-NO-EFFECT (MODAL)** | **30%** | TPE at 5×50 washes weight dispersion; modal -0.02 |
| Δ ∈ [-0.40, -0.10) | **NEGATIVE-OVER-FILTER** | **18%** | Up-weighting rare bars over-fits to noise; modal -0.20 |
| Δ < -0.40 | **NEGATIVE-CATASTROPHIC** | **12%** | Extreme weight spikes nuke training month; modal -0.55 |
| SUM | | **100%** | |

**Modal verdict**: **INERT-NO-EFFECT 30%** with OOS Δ band centered -0.02. Combined PROMISING tail 40%; combined NEG tail 30%. Net expected OOS Δ **+0.04**.

**F-AXIS overrides** (verdict-capping per LM Master §5):
- F-AXIS #1 wiring < 80% cell print rate → **TECHNICAL-FAILURE-SILENT-FALLBACK** regardless of F1
- F-AXIS #2 OOS trades < 150 → **TECHNICAL-FAILURE-SILENT-FALLBACK** regardless of F1
- F-AXIS #3 cross-seed best-param Spearman > 0.95 → **TECHNICAL-FAILURE-SILENT-NO-OP** regardless of F1
- F-AXIS #5 OOS TP-exit count < 15 OR Model D OOS TP < 3 → **PROMISING-INERT** cap regardless of F1
- Validation 1 std/mean > 0.40 → reclassify NEG-* as **NEG-BASIN-RELOCATION** (not NEG-AXIS-EDGE)
- Validation 2 median Spearman < 0.30 → reclassify NEG-* as **NEG-BASIN-RELOCATION**
- Validation 3 trade-roster overlap < 25% any symbol → reclassify NEG-* as **NEG-BASIN-RELOCATION**
- Validation 3 trade-roster overlap > 80% all symbols → reclassify as **INERT-NO-EFFECT** (axis not biting)

**Pre-committed CONFIRMATION composition implications** (per LM Master §7 PRE-COMMIT):
- /031 PROMISING-CLEAN → /032 = `inv_concurrency_only` at 3-seed × 18 trials BUDGET-CONTROL; /037-CONFIRMATION may add weight axis as SEPARATE bundle component
- /031 PROMISING-INERT-FAV → /032 = inv_concurrency_only stacking with NEW axis; /037 DEFERS bundle decision
- /031 INERT-NO-EFFECT (modal) → /032 = NEW axis family (universe expansion / trend-scanning / per-trade vol-targeting)
- /031 NEG-OVER → /032 = NEW axis family; sample-weighting CLOSED at v1
- /031 NEG-CAT → /032 = closure-reconciliation + NEW axis family; sample-weighting PERMANENTLY CLOSED at v1

---

## Section 5 — Risk Mitigation

### R1 (consecutive-SL cooldown) — per-model baseline ON for C/D/E; OFF for A

UNCHANGED from baseline. 15-day cooldown after 2 consecutive stop-losses (C/D/E). Model A pooled BTC+ETH disables R1 per baseline. Expected ~5-10% trade-blocking across IS+OOS, complementary to weighting axis (R1 fires at trade-stream level; weighting reshapes training-row level — orthogonal).

### R2 (drawdown brake) — OFF per-model

UNCHANGED. Per cycle-2 baseline.

### R3 (Mahalanobis OOD) — ON

UNCHANGED. Project-wide always-on; 70th percentile cutoff on 16 scale-invariant features. Expected ~2-5% trade-skip rate. Orthogonal to weighting axis.

### Basin-stability monitoring (Section 2.6 Validations 1-3 + F-AXIS #3 cross-seed)

The 3 mandated Section 2.6 validations + F-AXIS #3 cross-seed best-param Spearman ARE the risk-mitigation layer specific to the HIGH-RISK declaration. F-AXIS #1 + #2 catch silent fallback (wiring); Validations 1-3 catch basin relocation (loss-surface reshape gone wrong); F-AXIS #5 catches over-filter on Model D LTC-long catastrophe regime.

### Wall-clock kill-switch

5.0h ARMED (LM Master §8); 6h CONFIRMATION-mode hard cap.

### F-AXIS forensic log emission requirement (QE Phase 6)

Per cell logs (53 months × 5 models = 265 cells):
- 5 inner-seed best-trial Sharpes
- 5 inner-seed best-trial hyperparameters (num_leaves, learning_rate, min_child_samples)
- `[sample_weight_mode=composite_inv_concurrency]` print per Optuna trial dispatch

Forensic forensic-log path: `data/v1_iter_v1-031_optuna_trials.parquet` (NEW; per-trial-per-cell with seed-id + Sharpe + best-params columns).

---

## Section 6 — Risk Management Design

Structured 4-row gate-stack table (mirror /030 §6 structure to avoid /029-initial-brief Phase 5.5 BLOCK pattern):

| Gate | State | IS fire-rate (pred) | OOS fire-rate (pred) | Regime coverage | Gate-attribution estimate |
|---|---|---|---|---|---|
| **R1 cooldown** (per-model A=OFF, C/D/E=ON) | ON for C/D/E | ~5-10% of trades blocked | ~5-10% of trades blocked | All (micro-cascade prevention) | +0.05-0.10 OOS Sharpe (baseline component) |
| **R2 weighted DD scaling** | **OFF per-model** | n/a (cycle-2 baseline) | n/a | n/a | n/a (baseline disabled) |
| **R3 Mahalanobis OOD** (16 scale-invariant features, 70th pctl cutoff) | ON | ~2-5% blocked | ~3-5% blocked | OOD regimes | +0.02-0.05 OOS Sharpe (project-wide) |
| **inv_concurrency_only weight (NEW)** (mean-renormalized per (symbol, training-window); F-AXIS #1 wiring proof at 95% cell-print rate) | ON for A/C/D/E (M1 weight) | **100% rows reweighted** | **100% rows reweighted** | All training rows (per-bar gradient contribution shift) | **+0.04 net OOS modal** (LM Master §4 net expected); band [-0.40, +0.55] |

### 6.1 Regime coverage narrative

- **inv_concurrency_only weight (NEW, LOAD-BEARING)** targets the rare-isolation bars (concurrency < 22 = 0.4% of bars per Section 1.1, carrying up to weight 264.98 at extremes) by up-weighting their gradient contribution at training-row dispatch. LightGBM's Optuna TPE then explores hyperparameter regions where the loss surface includes these rare-bar signals; if the rare bars are structurally informative (PROMISING tail), the OOS lift propagates. If the rare bars are noise (NEG tail), Optuna over-fits IS to noise.
- **R3 (Mahalanobis OOD)** catches off-distribution months at feature-space distance level. Orthogonal to weight axis.
- **R1 (cooldown)** prevents micro-streak cascades. Orthogonal.
- **R2 (DD brake)** explicitly OFF.

### 6.2 IS-calibrated gate-effect attribution

From `composite_variants_portfolio.csv` row `inv_concurrency_only` + `per_month_kish.csv` extremes:
- **Pooled Kish ratio 0.899** (6% better than baseline 0.84) = real but mild down-weighting
- **0.06% of cells carry Kish < 0.30** (BTC/ETH 2020-01 = 0.147; LTC 2022-03 = 0.225) — NEG-CAT tail signature carriers
- **Pooled Spearman vs baseline = -0.093** = mechanism orthogonal to existing weighting dimension
- LM Master §4 net expected OOS Δ **+0.04** with modal INERT 30% / combined PROMISING tail 40% / combined NEG tail 30%

This IS-calibrated effect demonstrates the gate has mathematically alive mechanism (Kish 0.899 alive vs /016 ~1.0 vacuous) and orthogonal direction (pooled ρ -0.093 vs baseline) but MILD magnitude — modal INERT is the most-likely Phase 7 outcome.

### 6.3 Verdict-capping reminders (forensic monitoring at Phase 7)

- F-AXIS #1 wiring cell-print rate < 80% → TECHNICAL-FAILURE-SILENT-FALLBACK
- F-AXIS #2 OOS trades < 150 → TECHNICAL-FAILURE-SILENT-FALLBACK
- F-AXIS #3 cross-seed best-param Spearman > 0.95 → TECHNICAL-FAILURE-SILENT-NO-OP
- F-AXIS #5 OOS TP < 15 → PROMISING-INERT cap
- F-AXIS #5 Model D OOS TP < 3 → PROMISING-INERT cap (LOAD-BEARING; LTC-long catastrophe)
- Validation 1 std/mean > 0.40 → reclassify NEG as NEG-BASIN-RELOCATION
- Validation 2 median Spearman < 0.30 → reclassify NEG as NEG-BASIN-RELOCATION
- Validation 3 trade-roster overlap < 25% any symbol → reclassify NEG as NEG-BASIN-RELOCATION

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Three forward-looking failure modes with metric signatures pre-registered for Phase 8 diary verification.

### 7.1 WIRING SILENT FALLBACK (most likely failure mode)

The NEW `--sample-weight-mode composite_inv_concurrency` flag is parsed but the weight computation is NOT actually applied to LightGBM's `sample_weight` parameter. Possible causes:
- Flag plumbed to `LightGbmStrategy.__init__` but downstream `_compute_sample_weights` falls back to `abs_pnl`
- Weight vector computed but never passed to LightGBM trial dispatch
- Per-cell training row dispatcher silently drops the per-row weight column

**Metric signature** (Phase 8 diary verification):
- F-AXIS #1: < 95% of cells emit `[sample_weight_mode=composite_inv_concurrency]` print → silent fallback
- F-AXIS #3: cross-seed best-param Spearman > 0.95 vs baseline → axis silently no-op
- F1: OOS trade-roster BIT-IDENTICAL to baseline → wiring bug confirmed
- Verdict cell: TECHNICAL-FAILURE-SILENT-FALLBACK (no F1 verdict; BLOCK-PENDING-FIX redispatch)

**Critic Phase 6.0 pre-flight check requirement**: Per `feedback_v1_dispatch_baseline_catchall_exclusion.md` /030 LESSON — verify run_baseline_v1.py line 2704 includes "v1-031" in BASELINE catch-all exclusion tuple. Verify `[iter-v1/031]` dispatch banner fires at startup.

### 7.2 BASIN-RELOCATION /030 MIRROR (second-most-likely)

Even at 5-seed × 50-trials, the axis reshapes loss surface enough to relocate Optuna's basin. The weight reshape pushes TPE into a basin region that fits IS noise on rare-up-weighted bars; the basin does NOT generalize OOS. This is mechanistically distinct from /030 (which was M1 budget downshift basin relocation) but produces similar verdict.

**Metric signature**:
- Validation 1: median(std/mean across cells) > 0.40 → 5-seed in basin lottery
- Validation 2: median Spearman across 5 seeds < 0.30 → seeds disagree on basin location
- Validation 3: trade-roster overlap baseline ↔ /031 OOS per symbol < 25% on any symbol → basin relocation signature
- F1: OOS Δ ∈ [-0.40, -0.10] OR < -0.40
- Verdict cell: **NEG-BASIN-RELOCATION** (reclassified from NEG-OVER-FILTER or NEG-CAT per Validations override) — axis attribution INVALID

### 7.3 ABS_PNL STRUCTURAL EDGE DISPLACEMENT (third-most-likely; NEG-CAT signature)

Per `feedback_v1_abs_pnl_weighting_structural.md`: "abs_pnl weighting is structural to v1's edge. Replacing it without preserving the structural function risks NEG-CAT." `composite_inv_concurrency` REPLACES `abs_pnl` (Section 3.5 sample weighting = composite_inv_concurrency, NOT abs_pnl). If the abs_pnl down-weighting of small-pnl trades is structurally load-bearing for the v1 LightGBM training surface, removing it (replacing with inv_concurrency-only re-weighting) destroys edge regardless of basin stability.

**Metric signature**:
- F1: OOS Δ < -0.40 (NEG-CAT)
- Validation 1 + 2 PASS (seeds agree, basin stable) — NOT a basin-relocation artifact
- Validation 3 trade-roster overlap ∈ [35%, 75%] PASS — axis biting; reshape reaching Optuna
- BUT per-trade Sharpe OOS collapses uniformly across symbols
- Verdict cell: NEG-CATASTROPHIC (clean — NOT reclassified to NEG-BASIN-RELOCATION because Validations pass; this is genuine axis-edge negative finding)

This failure mode is the highest-stakes one: it would close `sample-weighting` PERMANENTLY at v1 (LM Master §7 PRE-COMMIT) and would be the second documented NEG-CAT in v1 axis-family precedents (after /030 meta-labeling NEG-CAT). 12% prior probability per LM Master §4.

---

## Section 8 — Verdict Cell Determination Table

Pre-commit to verdict cells with explicit (F1, F2, F3, F5, Validations 1-3) tuples (mirror /030 + /029 8+ row format):

| Row | Condition | Verdict cell |
|---|---|---|
| 1 | F-AXIS #1 cell-print rate < 80% OR F-AXIS #2 OOS < 150 OR F-AXIS #3 cross-seed Spearman > 0.95 | **TECHNICAL-FAILURE-SILENT-*** (no verdict; BLOCK-PENDING-FIX redispatch) |
| 2 | F-AXIS #1 PASS AND F-AXIS #5 OOS TP < 15 | **PROMISING-INERT** (F5 cap; over-filter on TP class) |
| 3 | F-AXIS #1 PASS AND F-AXIS #5 Model D OOS TP < 3 | **PROMISING-INERT** (F5 Model D cap; LTC-long catastrophe pre-vet) |
| 4 | F-AXIS #1 PASS AND Validation 1 std/mean > 0.40 (NEG band) | **NEG-BASIN-RELOCATION** (reclassified from NEG-OVER or NEG-CAT) |
| 5 | F-AXIS #1 PASS AND Validation 2 median Spearman < 0.30 (NEG band) | **NEG-BASIN-RELOCATION** (Validation 2 trigger) |
| 6 | F-AXIS #1 PASS AND Validation 3 overlap < 25% any symbol (NEG band) | **NEG-BASIN-RELOCATION** (Validation 3 trigger) |
| 7 | F-AXIS #1 PASS AND Validation 3 overlap > 80% all symbols | **INERT-NO-EFFECT-AXIS-NOT-BITING** |
| 8 | F1 Δ ≥ +0.20 AND F-AXIS #1-#5 PASS AND Validations 1-3 PASS | **PROMISING-CLEAN** (modal +0.32; /032 = budget-control) |
| 9 | F1 Δ ∈ [+0.05, +0.20) AND F-AXIS #1-#5 PASS AND Validations 1-3 PASS | **PROMISING-INERT-FAV** (modal +0.12; /032 = stack w/ NEW axis) |
| 10 | F1 Δ ∈ [-0.10, +0.05) AND F-AXIS #1-#5 PASS AND Validations 1-3 PASS | **INERT-NO-EFFECT** (modal -0.02; /032 = NEW axis family) |
| 11 | F1 Δ ∈ [-0.40, -0.10) AND F-AXIS #1-#5 PASS AND Validations 1-3 PASS | **NEG-OVER-FILTER** (modal -0.20; sample-weighting CLOSED at v1) |
| 12 | F1 Δ < -0.40 AND F-AXIS #1-#5 PASS AND Validations 1-3 PASS | **NEG-CATASTROPHIC** (modal -0.55; sample-weighting PERMANENTLY CLOSED at v1) |

**Explicit tuple-determination examples** (per LM Master §5 verdict capping logic):

| Tuple (F1, F2, F3, F5, V1, V2, V3) | Verdict |
|---|---|
| (+0.32, OOS=190, cs-ρ=0.7, TP=18, D-TP=4, V1=0.20, V2=0.55, V3=55%) | Row 8 PROMISING-CLEAN |
| (+0.12, OOS=185, cs-ρ=0.7, TP=20, D-TP=4, V1=0.22, V2=0.50, V3=60%) | Row 9 PROMISING-INERT-FAV |
| (-0.02, OOS=189, cs-ρ=0.7, TP=22, D-TP=5, V1=0.18, V2=0.55, V3=70%) | Row 10 INERT-NO-EFFECT (MODAL) |
| (-0.20, OOS=180, cs-ρ=0.7, TP=18, D-TP=4, V1=0.20, V2=0.55, V3=50%) | Row 11 NEG-OVER-FILTER |
| (-0.55, OOS=175, cs-ρ=0.7, TP=17, D-TP=3, V1=0.20, V2=0.55, V3=40%) | Row 12 NEG-CATASTROPHIC |
| (-0.25, OOS=180, cs-ρ=0.7, TP=18, D-TP=4, V1=**0.45**, V2=0.55, V3=50%) | Row 4 NEG-BASIN-RELOCATION (V1 override) |
| (-0.15, OOS=180, cs-ρ=0.7, TP=18, D-TP=4, V1=0.20, V2=0.55, V3=**22%**) | Row 6 NEG-BASIN-RELOCATION (V3 override) |
| (+0.40, OOS=180, cs-ρ=0.7, TP=20, D-TP=**2**, V1=0.20, V2=0.55, V3=55%) | Row 3 PROMISING-INERT (F5 Model D cap regardless of F1 +0.40) |
| (+0.10, OOS=130, cs-ρ=0.7, TP=17, D-TP=4, V1=0.20, V2=0.55, V3=60%) | Row 1 TECHNICAL-FAILURE-SILENT-FALLBACK (F-AXIS #2 OOS < 150 cap) |
| (+0.05, OOS=189, cs-ρ=**0.97**, TP=22, D-TP=5, V1=0.18, V2=0.55, V3=85%) | Row 1 TECHNICAL-FAILURE-SILENT-NO-OP (F-AXIS #3 cap) OR Row 7 INERT-AXIS-NOT-BITING (V3 cap) — F-AXIS #3 cap binds first |

**Modal expectation per LM Master §4**: Row 10 **INERT-NO-EFFECT** at 30% modal weight; combined PROMISING (Rows 8+9) 40%; combined NEG (Rows 4+5+6+11+12) 30%.

---

## Section 9 — Library Stack Declaration

Verified via `uv run python -c "import lightgbm, optuna, numpy, pandas, statsmodels; print(...)"` at brief authoring time:

```
lightgbm:    4.6.0       (LOAD-BEARING — M1 LightGbm w/ sample_weight at training-row level)
optuna:      4.8.0       (LOAD-BEARING — n_trials=50 single outer seed=42; 5 inner seeds)
numpy:       2.2.6       (LOAD-BEARING — trade-roster + per-bar weight vector arithmetic)
pandas:      3.0.0       (LOAD-BEARING — CSV/parquet I/O + per-symbol weight groupby)
statsmodels: 0.14.6      (NOT INVOKED at /031 — no new feature ADF stationarity checks)
mlfinlab:    NOT INSTALLED (no AFML-library invocations; in-tree implementations)
mlfinpy:     NOT INSTALLED (no AFML-library invocations)
fracdiff:    NOT INSTALLED (no new features at /031)
pypbo:       N/A (EXPLORATION single-outer-seed; PBO is CONFIRMATION-mode informational only)
```

### 9.1 Invocation status for /031

- **lightgbm** (4.6.0): LOAD-BEARING. M1 = baseline LightGbm strategy with `v1_pruned_axis016` bounds + NEW `sample_weight=composite_inv_concurrency` passed at training-row level. The `sample_weight` parameter is the only LightGBM API surface change at /031.
- **optuna** (4.8.0): LOAD-BEARING. M1 n_trials=50 single-outer-seed=42 search; 5 inner ensemble seeds.
- **numpy / pandas**: LOAD-BEARING. New per-symbol per-bar `c_at_entry` vector computation; per-symbol mean-renormalization groupby.
- **statsmodels**: NOT INVOKED at /031.
- **mlfinlab / mlfinpy**: NOT INSTALLED. /031 does NOT invoke either — the `compute_concurrency_at_entry` + `compute_composite_inv_concurrency_weights` helpers are in-tree implementations at `src/crypto_trade/strategies/ml/sample_weighting.py` (NEW at /031) OR extension to `labeling.py`.
- **pypbo**: N/A. PBO is CONFIRMATION-mode informational; at single-outer-seed EXPLORATION it is not invoked.
- **fracdiff**: NOT INSTALLED. /031 has zero new features.

### 9.2 NEW module path + version

- **NEW**: `src/crypto_trade/strategies/ml/sample_weighting.py` (recommended path; QE Phase 6 may alternatively extend `labeling.py`)
  - `compute_concurrency_at_entry(symbol_df, label_timeout_bars) → np.ndarray` (per-symbol sweep-line)
  - `compute_composite_inv_concurrency_weights(symbol_df, label_timeout_bars) → np.ndarray` (mean-renormalized)
- Modified: `src/crypto_trade/strategies/ml/lgbm.py` — new branch in `sample_weight_mode` dispatcher
- Modified: `run_baseline_v1.py` — new CLI flag `--sample-weight-mode` + line 2704 BASELINE catch-all exclusion tuple addition

### 9.3 No version bumps required at /031

No new library dependency. No version bumps. `uv.lock` UNCHANGED.

---

## Section 10 — Reproducibility, Symbol Exclusion, Test Suite Mandate

### 10.1 Reproducibility

- **HEAD commit (post-Phase 5.5 dispatch)**: TBD at Phase 5.5 PASS commit (current pre-brief HEAD = `f07c494`)
- **Outer seed**: 42 (single outer seed)
- **Inner ensemble seeds**: 5 (per LM Master §8 + /030 §8 mandate)
- **n_trials**: 50 (per LM Master §8 + /030 §8 mandate)
- **Sample weighting**: `composite_inv_concurrency` (the axis change)
- **Bounds profile**: `v1_pruned_axis016` (STRICT REPLICATION per LM Master §2 ADOPTED)
- **Feature columns**: `list(V1_FEATURE_COLUMNS_PRUNED)` (43 cols; explicit per `feedback_explicit_feature_columns.md`)
- **Universe**: `V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)` UNCHANGED
- **OOS_CUTOFF_DATE = 2025-03-24** (UNCHANGED; sacred constant)
- **training_months = 24** (UNCHANGED; sacred constant)
- **Embargo**: `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNCHANGED
- **`oof_persist_path`**: `data/v1_iter_v1-031_oof.parquet`
- **`params_persist_path`**: `data/v1_iter_v1-031_optuna_best_params.parquet`
- **`optuna_trials_log_path`**: `data/v1_iter_v1-031_optuna_trials.parquet` (NEW — per-trial-per-cell-per-inner-seed log for Validation 1+2)
- **`feature_importance_path`**: `feature_importance_<MODEL>_<SYMBOL>.csv` (PER LM Master + cycle-3 pattern)
- **Reports directory**: `reports-v1/iteration_v1-031/`

### 10.2 Symbol Exclusion

**`V1_EXCLUDED_SYMBOLS` unchanged.** No symbols added or removed from V1_BASELINE_UNIVERSE.

### 10.3 Test Suite Mandate (per `feedback_v1_defensive_check_must_be_tested.md` + `feedback_v1_dispatch_baseline_catchall_exclusion.md`)

For QE Phase 6 implementation. **10+ tests required**.

#### 10.3.1 Required regression tests at `tests/test_lookahead_embargo.py` (4 mandated)

- Walk-forward `train_end_ms < test_start_ms` invariant
- `embargo_ms` positive and applied to BOTH leading and trailing test boundary
- Triple-barrier σ_t uses past-only EWMA (no labeling-window contamination)
- **NEW**: `compute_concurrency_at_entry` uses ONLY label windows opened at bars t' ≤ t (no future-bar contamination of weight at bar t)

#### 10.3.2 New tests at `tests/test_iteration_v1_031.py` (10+ required, listed below)

1. `test_v1_iter031_cli_flag_parsing`: `--sample-weight-mode composite_inv_concurrency` is parsed and propagated to `LightGbmStrategy.__init__` correctly (not silently dropped)
2. `test_v1_iter031_weight_formula_correctness`: `compute_composite_inv_concurrency_weights` produces output matching the expected formula `(1 / c_at_entry) / mean(1 / c_at_entry)` per (symbol, training_window). Verify against the `analysis/iteration_v1-031/composite_variants_eda.py` expected output for a small synthetic training window.
3. `test_v1_iter031_per_symbol_mean_normalization`: Each symbol's weights sum to N (training window size) after mean-renormalization. Per-symbol mean(weights) = 1.0 ± 1e-9.
4. `test_v1_iter031_weight_wiring_to_lightgbm`: Verify the per-row weight column is passed to LightGBM's `sample_weight` parameter at trial dispatch (not silently dropped). Mock LightGBM training and assert `sample_weight` kwarg received the computed weights.
5. `test_v1_iter031_baseline_catchall_exclusion`: Verify `v1-031` added to `run_baseline_v1.py:2704` BASELINE catch-all exclusion tuple (per /030 LESSON — silent fallback at /030 BACKTEST #1 wasted 51 min)
6. `test_v1_iter031_dispatch_banner`: Verify `[iter-v1/031]` startup banner fires at `run_baseline_v1.py` entry (per /030 LESSON — banner is the first-line evidence dispatch hit the intended branch)
7. `test_v1_iter031_f_axis_1_wiring_print`: Verify the per-trial `[sample_weight_mode=composite_inv_concurrency]` print emits at every Optuna trial dispatch (F-AXIS #1 mechanism). Test via mock + log capture.
8. `test_v1_iter031_reproducibility_deterministic_weights`: Two runs with seed=42 + identical input data produce IDENTICAL weight vectors (`compute_composite_inv_concurrency_weights` is deterministic). Hash-compare arrays.
9. `test_v1_iter031_lookahead_concurrency`: `compute_concurrency_at_entry(t)` counts only label windows opened at bars t' ≤ t (no future-bar leakage). Test on synthetic data with explicit past-only verification.
10. `test_v1_iter031_pruned_bounds_strict_replication`: Verify `bounds_profile="v1_pruned_axis016"` is the active bounds profile at all Optuna trial dispatches; no modifications to ranges (per LM Master §2 STRICT REPLICATION).
11. `test_v1_iter031_outer_seed_42_inner_5_n_trials_50`: Verify config locks at outer_seed=42, ENSEMBLE_SIZE=5, n_trials=50 (per LM Master §8 + Section 3.5 LOCKED)

#### 10.3.3 ANY new hard-assert MUST include sample-instance unit test (the /027 lesson)

Per `feedback_v1_defensive_check_must_be_tested.md`: every hard-assert added to src/ MUST have a corresponding test that instantiates the real Pydantic or dataclass object and verifies the assert path. This includes any new asserts in `sample_weighting.py` or modifications to `lgbm.py`'s `_compute_sample_weights` dispatcher.

#### 10.3.4 NO HARD-ASSERT that would crash on legitimate config-fallback paths

The dispatcher must support graceful fallback to `abs_pnl` if `sample_weight_mode` is None or unset; the NEW `composite_inv_concurrency` mode is OPT-IN only. The runner MUST NOT hard-assert mode != None; the default (None / unset) should preserve baseline `abs_pnl` behavior (BIT-IDENTICAL to baseline / cycle-3).

---

## Path Forward (LM Master + QR convergence)

Cycle-4 EXPLORATION 4/10 — 6 EXPLORATIONs remain after /031. **/032 routing PRE-COMMIT** per LM Master §7:

- **/031 PROMISING-CLEAN (17%; Δ ≥ +0.20)** → **/032 = `inv_concurrency_only` at 3-seed × 18 trials BUDGET-CONTROL** (isolates axis-edge from budget-validity confound per LM Master §1 attribution ambiguity); /037-CONFIRMATION composition MAY include sample-weighting as SEPARATE bundle component pending /032 PASS
- **/031 PROMISING-INERT-FAV (23%; Δ ∈ [+0.05, +0.20))** → /032 = `inv_concurrency_only` stacking with NEW second axis (e.g., trend-scanning labels); /037-CONFIRMATION DEFERS sample-weighting bundle decision
- **/031 INERT-NO-EFFECT (30% MODAL; Δ ∈ [-0.10, +0.05))** → **/032 = NEW axis family** (LM Master §7 STRONG prior: universe expansion to SOLUSDT 6th symbol; alternatives: trend-scanning labels OR per-trade vol-targeting); sample-weighting CLOSED at v1 with `inv_concurrency_only` orthogonal pivot tested
- **/031 NEG-OVER-FILTER (18%; Δ ∈ [-0.40, -0.10))** → /032 = NEW axis family; sample-weighting CLOSED at v1
- **/031 NEG-CATASTROPHIC (12%; Δ < -0.40)** → /032 = closure-reconciliation + NEW axis family; sample-weighting PERMANENTLY CLOSED at v1 (mirror /030 meta-labeling NEG-CAT closure pattern)
- **/031 TECHNICAL-FAILURE (any Row 1 verdict)** → BLOCK-PENDING-FIX redispatch /031 (single ONE-CHANCE rerun allowed per v1 BLOCK-PENDING-FIX discipline); /032 routing deferred until /031 produces valid F1 verdict

If /031 PROMISING fires AND /032 BUDGET-CONTROL also PROMISES, /037-CONFIRMATION target composition:
1. Pool A baseline (BTC+ETH) with `composite_inv_concurrency` weight
2. LINK /018 specialist (+0.80 OOS Δ)
3. ETH-gate /019 specialist (+0.50 OOS Δ)
4. LTC-atr_sl /028 specialist (+0.598 OOS Δ)
5. (Optional) `composite_inv_concurrency` as SEPARATE axis bundle if /032 confirms axis-edge

If /031 INERT or NEG, /037-CONFIRMATION stays at 3-specialist (LINK + ETH-gate + LTC) + Pool A baseline.

**Attribution ambiguity acknowledgment** (LM Master §1 closing): PATH A confounds axis orthogonality with budget control. /031 alone cannot independently confirm BOTH in a single iteration. /032 budget-control resolves the confound IF /031 fires PROMISING. /032 = NEW axis family if /031 fires INERT/NEG (axis CLOSED; no need to isolate budget vs axis confound on a closed axis).

---

## Brief authoring complete.

**Authoring sign-off**: Quant Researcher; Phase 5 brief authored 2026-05-28; ready for Phase 5.5 gate dispatch.

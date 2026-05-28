# iter-v1/030 — Phase 4 Complete (Pre-LM Master)

**Date**: 2026-05-28
**Phase**: 1-4 complete; Phase 4.5 LM Master dispatch pending
**Cycle**: 4, EXPLORATION iteration 3/10
**Anchor**: BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe +0.2829, OOS Sharpe +0.6637

---

## Chosen axis family: **META-LABELING (López de Prado AFML Ch. 3)**

NEW family — UNUSED in v1 across cycles 1, 2, 3.
Per LM Master /029 §7 routing: cohort-coverage axis CLOSED at /029; /030 = NEW UNUSED family at single-seed EXPLORATION budget. Meta-labeling satisfies this mandate.

---

## Phase 1 — Axis-candidate EDA (5 candidates evaluated)

Script: `analysis/iteration_v1-030/axis_candidate_eda.py` (committed).

Summary CSV: `analysis/iteration_v1-030/axis_candidate_summary.csv`.

| # | Candidate | Family | Primary signal | Potential | Wall-clock risk | Verdict |
|---|---|---|---|---|---|---|
| 1 | sample-weighting | sample-weighting (NEW) | mean_concurrency=8.98 (H=9), avg_uniqueness=0.112 | STRONG | LOW (existing infra) | **CLOSED at /016** (NEG-CAT -1.6690; uniform inheritance closure of uniqueness_only at Spearman 0.997) — DEAD-PATHS CATALOG |
| 2 | meta-labeling | meta-labeling (NEW) | top-3 worst (sym,dir) cells = 37.0% IS losses; oracle veto lifts IS PnL +77.87% / OOS +58.55% | **STRONG** | **MODERATE** (existing infra: `src/crypto_trade/strategies/ml/metalabeling.py`) | **CHOSEN** |
| 3 | trend-scanning labels | labeling (NEW sub-type) | timeout_share=24.5%, timeout WR=74.3% | MODERATE | HIGH (label-rate scaling risk per /029 TF) | REJECTED (HIGH wall-clock risk + labeling axis already CLOSED at /014/015) |
| 4 | fractional differentiation | feature-family (NEW kernel) | avg ADF p-value = 0.0000 on pruned features | WEAK | MODERATE | REJECTED (`V1_FEATURE_COLUMNS_PRUNED` pre-selected for ADF stationarity α=0.05; AND Pool-A LEARNED-NEG rule disqualifies NEW Pool A features at single-seed) |
| 5 | DOT salvage at 3/18 | per-cohort (REPEAT) | projected wall-clock 185 min (cap 120 min) | INFEASIBLE | HIGH | REJECTED — wall-clock infeasible + cohort-coverage CLOSED per LM Master /029 §7 |

### Why candidates 1, 3, 4, 5 fail

**Candidate 1 (sample-weighting) — CLOSED at /016**: iter-v1/016 tested `sample_weight_mode="uniform"` → OOS Sharpe -1.0053 (Δ -1.6690 NEG-CAT-extreme); IS Sharpe -0.3055 (Δ -0.5884 below floor). The /016 diary explicitly states: "sample-weighting axis CLOSED at v1 baseline-labels; closes by inheritance on `uniqueness_only` per QR EDA Spearman 0.997 with uniform." The `abs(labeled_pnl)` weighting is STRUCTURAL to v1's edge — replacing it (uniform or uniqueness_only) DESTROYS the edge. Cannot retest.

**Candidate 3 (trend-scanning)**: Modifying labels = label-rate scaling per `feedback_v1_label_rate_wall_clock_scaling.md`. Trend-scanning's adaptive barrier produces UNKNOWN label-count distribution per cohort × month. Wall-clock risk at v1 EXPLORATION 2h cap is HIGH. Additionally, labeling axis is in cycle-2's dead-paths catalog (/014 + /015 catastrophic basin lottery; /015 PERMANENTLY CLOSED at portfolio-median magnitude 7.82%).

**Candidate 4 (fracdiff)**: Average ADF p-value on V1_FEATURE_COLUMNS_PRUNED features = 0.0000 (all 4 sampled families stationary). Pruned set was pre-selected for stationarity at α=0.05 — there is no "non-stationary feature memory to preserve." AND `feedback_v1_pool_a_new_feature_lneg.md` structurally disqualifies NEW Pool-A features at single-seed n_trials=18.

**Candidate 5 (DOT-salvage)**: 5-step wall-clock scaling computation:
1. Precedent: /029 DOT @ 10/35 = 7204s at month 6/53 = 11.3% walk-forward = projected 17.7h full
2. Precedent label count: 4342 per training window
3. /030 label count: SAME 4342 (no label change)
4. Compute fraction: (3 × 18) / (10 × 35) = 54/350 = 0.154
5. /030 projected: 17.7h × 0.154 = **2.72h** — **BREACHES 2h cap** even at minimum-budget; not 90-min-feasible

### Numerical evidence for meta-labeling (Candidate 2) — chosen

Script: `analysis/iteration_v1-030/meta_labeling_potential.py` (committed).

**Cell identifiability** (10 (sym, direction) cells, baseline IS):
- 3 worst cells (BTCUSDT-short, ETHUSDT-short, LINKUSDT-short) carry **31.9% of IS trades** and **-77.87% of IS PnL**.
- Oracle veto of worst-3 cells lifts IS net PnL from +50.98% → **+128.85%** (+77.87 pp).
- Oracle veto on OOS lifts net PnL from +24.87% → **+83.42%** (+58.55 pp).
- Per-model: Model A's worst cell (BTC-short) carries -32.65% of A's contribution; Model D's worst cell (LTC-long) carries -10.82% IS but **-45.44% OOS** (catastrophic). M2 on Model D is highest-leverage application.

**Time stability check** (IS H1 vs IS H2 vs OOS worst-cell overlap):
- IS H1 worst-3: {BTC-short, LTC-short, BTC-long}
- IS H2 worst-3: {ETH-short, BTC-short, ETH-long}
- Overlap top-3: 1/3 (BTC-short persists). Top-5 overlap: 3/5.
- **Stability assessment: MODERATE** — pattern shifts but BTC-short loss is persistent. M2 must learn from features, not just (sym, direction) — non-trivial.

**Per-model decomposition (IS/OOS)**:
| Model | Symbols | IS WR | IS PnL | OOS WR | OOS PnL | Worst cell IS | Worst-cell OOS |
|---|---|---|---|---|---|---|---|
| **A** | BTC+ETH (pooled) | 36.4% | -50.98% | 42.0% | +35.93% | BTC-short -0.55/tr | ETH-short -0.51/tr |
| **C** | LINK | 45.2% | +72.06% | 50.0% | +34.23% | LINK-short -0.32/tr | LINK-long +0.36/tr |
| **D** | LTC | 39.5% | +3.27% | 29.4% | -47.25% | LTC-long -0.15/tr | LTC-long -2.39/tr |
| **E** | DOT | 41.9% | +26.62% | 39.1% | +1.96% | DOT-short +0.03/tr | DOT-long -0.08/tr |

**Why meta-labeling wins**:
1. **STRUCTURAL FIT**: M2 is a NEW filtering layer ORTHOGONAL to M1 — it does NOT add features to Pool Model A, so `feedback_v1_pool_a_new_feature_lneg.md` does NOT apply.
2. **EXISTING INFRA**: `src/crypto_trade/strategies/ml/metalabeling.py` (added at iter-v3/017). Wall-clock-friendly — M2 trains on M1-positive bars only.
3. **EMPIRICAL SIGNAL STRONG**: 37% IS losses concentrate in identifiable top-3 cells. Oracle veto lift OOS +58.55%.
4. **UNUSED FAMILY in v1**: rotation status VALID.
5. **MODERATE stability**: forces M2 to use features, not just (sym, direction) memorization. AFML Ch.3 textbook.

---

## Phase 2 — Labeling Decisions (UNCHANGED)

**Triple-barrier UNCHANGED** — M1 retains baseline labeling exactly as v0.186:
- atr_tp_multiplier = (Model A=3.5, C=3.5, D=3.5, E=3.5)
- atr_sl_multiplier = (Model A=1.75, C=1.75, D=1.75, E=1.75)
- 21-bar timeout (7 days at 8h)
- σ_t source: NATR (per Model-specific baseline)
- Walk-forward embargo at fixed `walk_forward.py:113`

**M2 labels**: derived ex-post per AFML Ch.3 inside the training window only.
For each M1-positive training bar with label `y ∈ {-1, +1}`:
- M2 label = 1 if M1's direction matched and the trade reached TP barrier before SL/timeout
- M2 label = 0 if SL hit OR timeout fallback
- M2 labels NEVER consume future candles outside the training window (look-ahead audited per metalabeling.py:23-29 module docstring).

**Sample weighting**: M1 keeps `sample_weight_mode="abs_pnl"` (baseline, structural). M2 has NO sample weighting (binary log-loss objective).

---

## Phase 3 — Symbol Selection / Universe (UNCHANGED)

**Universe: `V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)`** — UNCHANGED 5 symbols.

Per-model dispatch UNCHANGED:
- Model A (pooled): BTC + ETH
- Model C: LINK
- Model D: LTC
- Model E: DOT

**Why universe unchanged**: meta-labeling is a SECOND-STAGE filter; universe expansion (UNUSED since /017 universe family closure) is a SEPARATE axis. Bundling them would entangle two interventions.

---

## Phase 4 — Feature Design

**M1 features: `V1_FEATURE_COLUMNS_PRUNED` (43 cols)** — UNCHANGED from /028.

**M2 features (NEW)**: 43 (M1 features) + 1 (M1 confidence proba) + 1 (M1 direction) = **45 columns** per M2 sample.

NEW M2 architecture detail (v1-specific decision):
- Each of 4 models (A, C, D, E) gets ITS OWN M2 classifier (4 M2 total).
- Each M2 is trained per-month-rolling, parallel to M1's monthly retrain.
- M2 confidence threshold PINNED at 0.5 (single-axis discipline; not tuned).
- M2 Optuna budget: **n_trials_m2 = 10** (less than M1's 18 because M2 trains on sparse M1-positive subset).
- M2 ensemble: **single LGBMClassifier per (model, month)** (no inner-ensembling for M2 — keep simple).

Active feature columns pinned to `list(V1_FEATURE_COLUMNS_PRUNED)` at the `MetaLabelingStrategy._m1` call site (mandatory per `feedback_explicit_feature_columns.md`).

### Phase 4 — Design summary for LM Master Phase 4.5 dispatch

| Dimension | Value | Rationale |
|---|---|---|
| **Axis family** | **meta-labeling** (NEW; UNUSED in v1) | LM Master /029 §7 routing: NEW UNUSED family |
| **Mechanism** | Two-stage: M1 (LightGbm direction) + M2 (LGBMClassifier binary post-filter) | López de Prado AFML Ch. 3 textbook architecture |
| **Cohort** | V1_BASELINE_UNIVERSE (BTC, ETH, LINK, LTC, DOT) UNCHANGED | Universe expansion is a separate axis |
| **M1 architecture** | UNCHANGED 4 models (A pooled BTC+ETH, C LINK, D LTC, E DOT) | Single-axis discipline; M2 is the only NEW layer |
| **M2 architecture** | 4 separate LGBMClassifier binary (one per model) | Per-model M2 aligns with per-model M1 dispatch |
| **M2 features** | V1_FEATURE_COLUMNS_PRUNED (43) + m1_confidence + m1_direction = 45 | M2 gets M1's prediction as extra feature (AFML Ch.3 §3.5) |
| **M2 threshold** | 0.5 (PINNED) | Single-axis; not a tunable knob |
| **`atr_tp/sl_multiplier`** | UNCHANGED (M1 baseline) | M1 untouched |
| **Risk gates** | UNCHANGED (R1 A=OFF, C/D/E=ON; R2 E only; R3 ALL) | Risk gates orthogonal to M2 |
| **Feature set** | V1_FEATURE_COLUMNS_PRUNED (43 cols) | UNCHANGED |
| **Labels** | Triple-barrier σ_t NATR | UNCHANGED |
| **Timeout** | 21 bars (7 days at 8h) | UNCHANGED |
| **Optuna M1** | n_trials=18, ENSEMBLE_SIZE=3 | v1 EXPLORATION standard |
| **Optuna M2** | n_trials=10, single classifier (no ensemble) | M2 sparse subset; lower budget |
| **Seed** | 42 (single-seed) | v1 EXPLORATION standard |
| **Wall-clock cap** | 2h HARD | v1 EXPLORATION cadence discipline |

### Wall-clock estimate (5-step scaling per `feedback_v1_label_rate_wall_clock_scaling.md`)

1. **Precedent iteration**: /016 sample-weighting @ ENSEMBLE_SIZE=3 + n_trials=18 = ~50 min observed (5-symbol, 8h, V1_FEATURE_COLUMNS_PRUNED).
2. **Precedent M1 label count per training window**: ~621 baseline trades / 25 months ≈ 25 trades/month/symbol × 5 sym × 24-month rolling = 3000 M1-positive bars/window. (NOT label COUNT; baseline trades = MODEL FIRES which is smaller. The full label-set is each candle in training window.)
3. **/030 M1 label count**: SAME (M1 is BIT-IDENTICAL to baseline). Wall-clock for M1 dispatch = ~50 min.
4. **M2 cost**: 4 models × 53 months × 10 trials × ~50 M1-positive bars/cell training cost ≈ 106k M2 trial-fits. At ~5ms/trial = ~530s ≈ 9 min.
5. **Sanity check**: 50 + 9 = **~59 min total**, well under 2h cap and under 90-min target. **FEASIBLE.**

Cross-check via v3/017 precedent: v3/017 meta-labeling at 3-symbol BCH/LDO/TRX + V3_FEATURE_COLUMNS_TOP_N + n_trials_m2 = 10 ran in ~35 min total (M1 + M2). v1 has 5 symbols + 43 features vs v3's 3 + 14 → wall-clock multiplier ~1.6× = ~56 min. Both estimates converge on ~60 min.

### NEW v1 verdict cell expected

If M2 fires PROMISING: NEW v1 "meta-labeling-veto-PROMISING" subtype (analog to v3 "PROMISING-MECHANICAL"). Likely NON-COMPOUNDABLE as bundled CONFIRMATION edge ingredient unless paired with per-cohort specialists.

If M2 fires INERT: meta-labeling-axis-CLOSED for v1; PATH FORWARD = new feature family or per-symbol specialist re-attempt.

If M2 fires NEGATIVE: catastrophic over-filter (v3/017 precedent: M2 vetoed too many trades while not improving per-trade quality); axis closure.

---

## Pre-Phase-4.5 Questions for LM Master

1. **M2 features 43 + 1 m1_confidence + 1 m1_direction = 45 (v1 spec)** — should LM Master recommend including additional per-bar context features (e.g., R3 OOD score, BTC-trend bucket flag from /019 ETH gate)? Or keep M2 spec at AFML Ch.3 minimal (only M1 features + M1 confidence)?

2. **M2 per-model (4 separate classifiers) vs M2 unified (1 classifier on all M1-positive bars across models)** — per-model M2 has higher VC-dim risk (4 separate fits on smaller subsets) but matches per-model M1 architecture. Unified M2 has 1 classifier on ~621 bars total but may not capture per-model loss patterns. Mechanism evidence for which to prefer?

3. **n_trials_m2 = 10 vs higher** — M2 trains on sparse M1-positive subset. Is 10 enough for Optuna TPE warmup, or should LM Master recommend escalating to n_trials_m2=20-30?

4. **Time-stability gap (IS H1/H2 top-3 worst-cell overlap = 1/3)** — meta-labeling potential is STRONG via cells but H1/H2 stability is only MODERATE. Should LM Master recommend a SECONDARY falsifier ("M2 OOS veto-pattern overlap with M2 IS veto-pattern") to detect regime instability? What threshold?

5. **F-AXIS pre-registration** — what predicted bands does LM Master recommend for:
   - F-AXIS #1 (architecture): M2 trained AND fired (binary; M2 must produce > 0 vetoes)
   - F-AXIS #2 (M2 veto rate): 15-50% expected band (v3/017 fired 42.7%); cap floor at 10% (too low = over-permissive M2)
   - F-AXIS #3 (M2 retained-trade quality lift): OOS retained-trade per-trade Sharpe ≥ baseline OOS per-trade Sharpe (binary)
   - F-AXIS #4 (n_eff_per_cell): expected band at ENSEMBLE_SIZE=3 / n_trials=18 (M1 unchanged)
   - F-AXIS #5 (per-model M2 differential): which model's M2 has highest predicted lift (D LTC modal expected per OOS LTC catastrophe)?

6. **Verdict-class priors** — given the STRONG signal + MODERATE stability + UNUSED family + existing infrastructure, what tail-probability split does LM Master recommend across:
   - PROMISING (M2 reduces OOS losses while preserving OOS PnL ≥ baseline) — ?%
   - PROMISING-MECHANICAL (M2 fires correctly but no edge lift; per-trade economics flat) — ?%
   - INERT (M2 vetoes < 10% of trades or doesn't fire) — ?%
   - NEG-clean (M2 over-filters; OOS PnL drops by 5-30%; v3/017 precedent) — ?%
   - NEG-CAT (catastrophic M2 over-filter; OOS PnL drops by > 30%) — ?%

7. **Bundle-composition implications** — if /030 fires PROMISING, would meta-labeling be a /027-retry bundle ingredient (alongside LINK +0.80 + ETH+gate +0.50 + LTC+atr_sl=1.0)? Or NON-COMPOUNDABLE per the v3 PROMISING-MECHANICAL classification?

8. **Critic Phase 6.0 implementation risk** — what defensive checks should LM Master mandate at runner level (analogous to /027's `r.model_name` hard-assert) to prevent a /027-style TECHNICAL FAILURE at the M2 dispatch step? Specifically: assert M2 trained for each (model, month) cell with > 0 M1-positive bars, OR assert M2 fired AT LEAST ONCE per OOS month if M1 fired.

---

## Path Forward (Phase 4.5 dispatch)

Orchestrator dispatches LightGBM Master agent for Phase 4.5 advisory. LM Master reads:
- BASELINE_V1.md (current v1 baseline + per-model attribution)
- This file (`phase4_complete.md`)
- `analysis/iteration_v1-030/axis_candidate_summary.csv` (5 candidates)
- `analysis/iteration_v1-030/meta_labeling_*.csv` (deep-dive on chosen axis)
- `briefs-v1/iteration_v1-029/lgbm_advisor.md` (Phase 4.5 + Phase 7.4; §7 routing for /030)
- `diary-v1/iteration_v1-016.md` (sample-weighting CLOSED — informs candidate-1 rejection logic)
- `src/crypto_trade/strategies/ml/metalabeling.py` (existing M2 infra reference)
- v3/017 diary (`diary-v3/iteration_v3-017.md`) for the only meta-labeling precedent (NEG-clean over-filter)
- Last 3 v1 diaries (/025, /027, /029-TF — /028 not yet written but per LM Master /029 §7)

LM Master returns `briefs-v1/iteration_v1-030/lgbm_advisor.md` (Phase 4.5 section).
QR resumes Phase 5 (brief authoring), referencing LM Master Section 3 to address each recommendation (Adopted / Modified / Rejected).

---

## Artifact paths (committed)

```
analysis/iteration_v1-030/
├── axis_candidate_eda.py             [script — Phase 1 EDA, 5 candidates]
├── axis_candidate_summary.csv        [headline summary table]
├── candidate_1_sample_weighting.csv  [Candidate 1 numerics — REJECTED dead-paths]
├── candidate_2_meta_labeling.csv     [Candidate 2 numerics — CHOSEN]
├── candidate_3_trend_scanning.csv    [Candidate 3 numerics — REJECTED HIGH risk]
├── candidate_3_trend_scanning_per_symbol.csv
├── candidate_4_fracdiff.csv          [Candidate 4 numerics — REJECTED WEAK signal]
├── candidate_5_dot_salvage_walltime.csv [Candidate 5 numerics — REJECTED INFEASIBLE]
├── meta_labeling_potential.py        [script — Phase 1.5 deep-dive on chosen axis]
├── meta_labeling_cells.csv           [per (sym, direction) cell stats IS + OOS]
├── meta_labeling_veto_lift.csv       [hypothetical oracle veto cumulative lift]
├── meta_labeling_stability.csv       [H1/H2 worst-cell overlap]
├── meta_labeling_per_model.csv       [per-model A/C/D/E loss breakdown]
└── meta_labeling_summary.csv         [headline summary]

briefs-v1/iteration_v1-030/
└── phase4_complete.md                [THIS FILE]
```

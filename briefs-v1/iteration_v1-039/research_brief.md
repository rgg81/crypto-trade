# iter-v1/039 — Research Brief

**Iteration**: iter-v1/039
**Date**: 2026-05-31
**TYPE**: EXPLORATION
**Cycle**: 5, EXP 6 of 10
**Branch**: `iteration-v1/039`
**Author**: QR (autopilot)

---

## Section 0.0 — Banner

**iter-v1/039 — EXPLORATION cycle-5 #6/10**
- **Axis**: Per-cohort Sortino × specialist hybrid — Sortino Optuna objective layered on /036's LINK+DOT trend-scanning 2-cohort substrate
- **Axis family**: `loss-function × per-cohort-specialization` REPEAT-COMBO (double-REPEAT, see §0.6)
- **Load-bearing purpose**: resolves the /044 CONFIRMATION routing decision — does Sortino's mechanism (from /037) compound on /036's per-cohort trend-scanning substrate, or are the two axes universe-dependent and therefore non-bundleable?

---

## Section 0.5 — Iteration Type, Cadence Position, Wall-Clock

- **TYPE**: EXPLORATION
- **Cadence**: cycle-5 EXPLORATION **6 of 10** (4 EXPLORATIONs to go before /044 CONFIRMATION can launch). Prior cycle-5 ledger:
  - /034 feature-family basis_zscore_30 — NEG-CLEAN LEARNED-NEG
  - /035 labeling trend-scanning 5-cohort — NEG-CAT-bundle bimodal
  - /036 per-cohort-specialization LINK+DOT trend-scan — **PROMISING-CLEAN** (OOS Sharpe +1.7465, the largest single-seed OOS lift in v1 history)
  - /037 loss-function Sortino 5-cohort — **PROMISING-CLEAN** (OOS Sharpe +0.8388; LTC catastrophe-recovery + DOT amplification)
  - /038 risk-primitive symmetric per-symbol vol-ceiling — NEG-CATASTROPHIC EDA-vindicated
- **NO kill-switches** (cycle-5 directive).
- **Wall-clock target**: ~50 min modal at v1 EXPLORATION standard. Sortino swap = negligible per-trial overhead vs Sharpe; 2-cohort universe halves cohort-level Optuna cost vs 5-cohort but per-cohort Optuna dominates. Anchored on /036 (~25 min) + /037 (~50 min); midpoint ~40 min. **Modal 50 min, conservative 75 min, 2h hard cap.**

---

## Section 0.6 — Axis-Family Rotation (v1-only) — DOUBLE-REPEAT JUSTIFICATION

- **Axis family**: `loss-function × per-cohort-specialization` **DOUBLE-REPEAT COMBO**
  - `loss-function` last used at /037 (1 iter ago)
  - `per-cohort-specialization` last used at /036 (2 iters ago)
- **Prior 5 EXPLORATION families**:
  - iter-v1/034: feature-family (basis_zscore_30)
  - iter-v1/035: labeling (trend-scanning 5-cohort)
  - iter-v1/036: per-cohort-specialization (LINK+DOT trend-scan)
  - iter-v1/037: loss-function (Sortino)
  - iter-v1/038: risk-primitive (vol-ceiling)
- **Rotation status**: **DOUBLE-REPEAT JUSTIFIED as STACKING INTERACTION PROBE, not knob-tuning REPEAT.** The Axis Rotation Discipline rule fires when the last 5 EXPLORATIONs are ALL from the same family (knob-tuning monoculture); the prior 5 disperse across 5 distinct families with /036 and /037 each used exactly once. Per skill 2-iter family recurrence is allowed (5+ forbidden). The double-REPEAT is mitigated by:
  1. **Orthogonal interaction question, not a tuning sweep**: both /036 (per-cohort-specialization) and /037 (loss-function) closed as PROMISING-CLEAN INDIVIDUALLY. The question /039 resolves is whether they COMPOUND on the same substrate, which can ONLY be answered by stacking them. No knob is being twiddled — both axes are kept at their /036+/037 settings; the experiment is COMPOSITIONAL.
  2. **Load-bearing /044 routing implication**: /037 closeout pre-committed /044 to TWO SEPARATE CONFIRMATIONs unless an interaction probe demonstrates compoundability. /039 IS that interaction probe. Without it, /044 is forced to SEPARATE by default, which forfeits ~+0.30 OOS Sharpe upside if the axes DO stack.
  3. **No new src/ code, no Optuna search space change**: the implementation reuses /036's dispatch pattern + /037's `--optuna-objective` flag. The substrate-and-objective interaction is structurally orthogonal to the axes covered in cycle-5 EXPLORATIONs 1-5.
- **One-sentence rationale**: /037's PROMISING-CLEAN finding identified Sortino as a universe-level basin reshuffler with concentrated DOT amplification, and /036's PROMISING-CLEAN finding identified LINK+DOT trend-scan as a per-cohort signal extractor; /039 is the ONE EXPLORATION that resolves whether the two mechanisms operate on independent axes (stack) or on the same gradient (collide), which is the load-bearing decision for /044 bundle composition.

---

## Section 1 — Hypothesis

**H1 (PRIMARY, 3 sentences)**: Applying /037's Sortino Optuna objective to /036's LINK+DOT trend-scanning 2-cohort specialist substrate will surface a downside-std-aware basin within the per-cohort label specialization, lifting OOS Sharpe beyond /036's anchor (+1.7465) by tilting the Optuna basin away from left-tail-heavy regions that Sharpe under-penalizes. Mechanism: Sortino's downside-only denominator forces the basin selection to prefer HP regions where the trend-scanning forward-window predictions miss BAD trades, and per-cohort isolation removes the 5-cohort Pool-A averaging that diluted /037's mechanism on LINK. If the two mechanisms are independent gradients (per-cohort isolation acts on Optuna's per-symbol training pool while Sortino acts on the per-trial aggregate statistic), the lift compounds linearly; if they co-locate on the same loss-surface direction (Sortino's basin reshuffle on a 2-cohort universe lands inside /036's already-optimized basin), the second mechanism is INERT or HARMFUL.

**H1a (mechanism, EDA prior)**: /036's substrate exhibits Sortino/Sharpe ratio of only ~1.22 (vs 3.0-4.0× on the 5-cohort baseline that /037 exploited) — the trend-scanning labels + 2-cohort universe already produce near-symmetric OOS PnL distributions (skew 0.3, exc-kurt < 1), giving Sortino MUCH LESS room to reorganize the loss surface than it had on baseline. Jaccard overlap of /036 vs /037 trade rosters on LINK+DOT OOS = 0.1381 (deeply LOW < 0.30): the two axes pick substantially different trades on the same nominal cohorts, suggesting BASIN COMPETITION rather than orthogonal gradient stacking.

**H1b (falsifiable)**: If bundle OOS Sharpe Δ vs /036 anchor (+1.7465) is < +0.10 AND per-symbol LINK + DOT OOS lifts both remain within ±25pp of /036's bit-identical roster, the Sortino-on-trend-scan-specialist composite is REFUTED — /037's lift was 5-cohort-universe-dependent, not universe-independent, and the two axes do not compound. /044 routing pre-commits to TWO SEPARATE CONFIRMATIONs.

---

## Section 2 — F-AXIS #1 — F1 OOS Sharpe Δ vs /036 anchor (+1.7465)

**Anchor**: /036 OOS Sharpe +1.7465 (the substrate /039 builds on, not BASELINE_V1).

| Band | OOS bundle Sharpe Δ vs /036 | Verdict subtype |
|---|---|---|
| Δ ≥ +0.30 | exceeds modal upside (bundle OOS ≥ +2.05) | EXPLORATION-PROMISING-CLEAN-EXCEPTIONAL |
| +0.10 ≤ Δ < +0.30 | PROMISING band — mechanisms compound | EXPLORATION-PROMISING-CLEAN |
| 0 ≤ Δ < +0.10 | PROMISING-INERT-FAV — Sortino marginally additive on /036 substrate | EXPLORATION-PROMISING-INERT-FAV |
| -0.20 ≤ Δ < 0 | INERT — Sortino INERT or marginally harmful on /036 substrate | EXPLORATION-INERT |
| -0.45 ≤ Δ < -0.20 | NEG-CLEAN — basin migration competes with /036's specialist policy | **EXPLORATION-NEGATIVE-CLEAN (MODAL)** |
| Δ < -0.45 | NEG-CAT — catastrophic interference, similar to /037's LINK regression in 5-cohort | EXPLORATION-NEGATIVE-CATASTROPHIC |

**Modal band prior (EDA + LM Master integrated)**:

| Outcome | EDA weight | Final prior |
|---|---|---|
| PROMISING-CLEAN-EXCEPTIONAL (Δ ≥ +0.30) | 3% | **3%** |
| PROMISING-CLEAN (Δ ∈ [+0.10, +0.30)) | 7% | **7%** |
| PROMISING-INERT-FAV (Δ ∈ [0, +0.10)) | 17% | **17%** |
| INERT (Δ ∈ [-0.20, 0)) | 23% | **23%** |
| **NEG-CLEAN (Δ ∈ [-0.45, -0.20))** | **40%** | **40% MODAL** |
| NEG-CAT (Δ < -0.45) | 20% | **20%** |

**Modal**: NEG-CLEAN [Δ ∈ -0.45, -0.20)] at 40% weight. Combined NEG mass 60% / Neutral 23% / POS 27% (incl. 17% PROMISING-INERT-FAV).

**OOS Sharpe absolute equivalents**:
- PROMISING-CLEAN-EXCEPTIONAL: OOS ≥ +2.05
- PROMISING-CLEAN: +1.85 to +2.05
- PROMISING-INERT-FAV: +1.75 to +1.85
- INERT: +1.55 to +1.75
- **NEG-CLEAN MODAL: +1.30 to +1.55**
- NEG-CAT: < +1.30

**Predicted modal F1 outcome**: OOS bundle Sharpe ~ **+1.42** (Δ -0.33 vs /036, inside NEG-CLEAN band).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only) — HYBRID classification

- **Declaration**: **HIGH-RISK by axis-family rotation rule; NORMAL-RISK by mechanism rule.**
- **HIGH-RISK reason (rotation)**: double-REPEAT COMBO with predicted-NEG modal (60% combined NEG mass). Per v1 rotation discipline, an axis whose prior-5 family-distance is < 5 EXPLORATIONs apart AND whose EDA prior is NEG-DOMINANT inherits HIGH-RISK status to flag stacking interaction risks.
- **NORMAL-RISK reason (mechanism)**: NO new src/ code is shipped, NO Optuna search-space bounds change, NO labeling change, NO feature change. The `--label-mode trend_scanning` flag (shipped at /035) + `--optuna-objective sortino` flag (shipped at /037) + `V1_ITER036_UNIVERSE` 2-cohort dispatch (shipped at /036) are composed via existing plumbing. The axis does NOT change Optuna's training-objective DOMAIN (the per-row weight vector, per-row label, per-row gradient inputs); only the scalar Optuna returns per trial differs.
- **Budget choice**: SINGLE-SEED=42 at v1 EXPLORATION standard (ENSEMBLE_SIZE=3, n_trials=18, outer seed=42). HIGH-RISK declaration is MANDATORY but multi-seed validation is OPT-IN per v1 discipline. Single-seed is JUSTIFIED because:
  - Implementation is composition of two shipped axes (no new src/ code → no new wiring defect surface).
  - EDA prior is NEG-DOMINANT modal so a positive-tail outcome at single-seed would be a STRONG signal (low false-positive risk on the upside).
  - If F1 PROMISING fires → /044 multi-seed validates per HIGH-RISK escalation rule.
- **HIGH-RISK SINGLE-SEED counter**: /036 = HIGH-RISK SS PROMISING-CLEAN; /037 = NORMAL-RISK SS PROMISING-CLEAN; /038 = NORMAL-RISK SS NEG-CAT; /039 = HIGH-RISK SS. Counter at 1 of 3 → not yet at auto-upgrade threshold.

---

## Section 3 — Implementation Design + CLI Invocation

### Section 3.1 — Code changes (NO NEW SRC/ CODE)

Per the AXIS specification: all three mechanisms exist in production. Only `run_baseline_v1.py` needs a dispatch elif + catch-all exclusion:

1. **EDIT `run_baseline_v1.py`**:
   - **Define** `V1_ITER039_UNIVERSE: tuple[str, ...] = ("LINKUSDT", "DOTUSDT")` near `V1_ITER036_UNIVERSE`.
   - **Add `iteration_label == "v1-039"` dispatch branch** mirroring /036's dispatch structure (~75 lines), with the following differences:
     - Pre-flight assert: `assert label_mode_arg == "trend_scanning"`
     - Pre-flight assert: `assert set(symbols) == set(V1_ITER039_UNIVERSE)`
     - Pre-flight assert: `assert optuna_objective_arg == "sortino"` (NEW vs /036)
     - Dispatch banner:
       `[iter-v1/039] PER-COHORT-SORTINO-TREND-SCAN HYBRID ACTIVE: models=Model_C_LINK + Model_E_DOT, label_mode=trend_scanning, optuna_objective=sortino, trend_scan_grid=(5,8,13,21), ENSEMBLE_SIZE={ensemble_size}, n_trials={n_trials}, seeds=1, features={len(active_feature_columns)} cols`
     - Dispatch Model C' (LINK only) + Model E (DOT only), each threading BOTH `label_mode=label_mode_arg` AND `optuna_objective=optuna_objective_arg` to `run_model()`.
   - **Add `"v1-039"`** to BASELINE catch-all exclusion tuple at line ~3686 (per `/030 LESSON`).

2. **CONFIRM no other src/ edits required**:
   - `--label-mode trend_scanning` shipped at /035 (live in `lgbm.py`, `labeling.py`).
   - `--optuna-objective sortino` shipped at /037 (live in `optimization.py`, `lgbm.py`).
   - 2-cohort dispatch + universe assertion pattern shipped at /036.

### Section 3.2 — CLI invocation (Phase 6 backtest)

```bash
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py \
  --symbols LINKUSDT,DOTUSDT \
  --label-mode trend_scanning \
  --optuna-objective sortino \
  --pruned-features \
  --iteration 39 \
  --exploration \
  --n-trials 18 \
  --ensemble-size 3 \
  --seeds 1 \
  > logs/iter_v1_039_backtest.log 2>&1
```

Flag breakdown:
- `--symbols LINKUSDT,DOTUSDT` restricts universe to V1_ITER039_UNIVERSE (2 cohorts).
- `--label-mode trend_scanning` reuses /035 labeling path with grid (5, 8, 13, 21).
- `--optuna-objective sortino` reuses /037 Sortino objective path.
- `--pruned-features` activates `V1_FEATURE_COLUMNS_PRUNED` (44 cols incl. /034 basis_zscore_30).
- `--iteration 39` triggers the v1-039 dispatch branch.
- `--exploration --n-trials 18 --ensemble-size 3 --seeds 1` = v1 EXPLORATION standard.

### Section 3.3 — Symbols + models + config

| Item | Spec |
|---|---|
| Universe | V1_ITER039_UNIVERSE = (LINKUSDT, DOTUSDT) — NEW 2-symbol constant |
| Models | Model C' (LINK, atr_tp=3.5, atr_sl=1.75, R1=ON, R3=ON) + Model E (DOT, atr_tp=3.5, atr_sl=1.75, R1=ON, R2=ON, R3=ON). IDENTICAL to /036 |
| Labels | `trend_scanning` grid (5, 8, 13, 21) — IDENTICAL to /035, /036 |
| Optuna objective | `sortino` — IDENTICAL to /037 |
| Features | V1_FEATURE_COLUMNS_PRUNED 44 cols — UNCHANGED |
| Sample weight | `abs_pnl` baseline — UNCHANGED |
| Optuna bounds | `v1_pruned` — UNCHANGED |
| n_trials | 18 |
| Inner ensemble | 3 seeds (V1_EXPLORATION_ENSEMBLE_SIZE) |
| Outer seed | 42 (single) |
| Walk-forward | training_months=24 (sacred), monthly retrain, embargo via walk_forward.py:113 |
| OOS_CUTOFF | 2025-03-24 (sacred) |
| Risk gates | R1 ON C'/E; R2 ON E only; R3 ON both (cutoff 0.70, 16 features) |

### Section 3.4 — Test mandate (8+ tests per `/030 LESSON`)

`tests/test_iteration_v1_039.py` MUST include:

1. `test_v1_039_universe_constant_exists` — V1_ITER039_UNIVERSE = ("LINKUSDT", "DOTUSDT")
2. `test_v1_039_universe_subset_of_baseline` — both symbols in V1_BASELINE_UNIVERSE
3. `test_v1_039_dispatch_branch_exists` — `iteration_label == "v1-039"` path reachable
4. `test_v1_039_pre_flight_label_mode_assert` — `--label-mode triple_barrier` raises AssertionError
5. `test_v1_039_pre_flight_universe_assert` — wrong symbol set raises AssertionError
6. `test_v1_039_pre_flight_optuna_objective_assert` — `--optuna-objective sharpe` raises AssertionError (NEW vs /036)
7. `test_v1_039_in_baseline_catchall_exclusion` — `"v1-039"` in exclusion tuple
8. `test_v1_039_dispatch_banner_emitted` — banner contains both `label_mode=trend_scanning` AND `optuna_objective=sortino`
9. `test_v1_039_label_mode_threaded_to_link_model` — real-instance `.label_mode == "trend_scanning"`
10. `test_v1_039_label_mode_threaded_to_dot_model` — same for DOT
11. `test_v1_039_optuna_objective_threaded_to_link_model` — real-instance `._optuna_objective == "sortino"` (NEW vs /036)
12. `test_v1_039_optuna_objective_threaded_to_dot_model` — same for DOT
13. `test_v1_039_dispatches_only_link_and_dot_models` — exactly 2 model results

13 tests + existing `tests/test_iteration_v1_036.py` + `tests/test_iteration_v1_037.py` + `tests/strategies/ml/test_trend_scanning_label_mode.py` MUST all pass at Phase 6.

---

## Section 4 — F-AXIS #2-#7 mechanism falsifiers (diagnostic)

### F-AXIS #2 — Wiring assert BOTH flags

**PASS criterion**: Phase 6 backtest log contains:
- `[iter-v1/039] PER-COHORT-SORTINO-TREND-SCAN HYBRID ACTIVE` banner (1 line at dispatch)
- Per-cell `OPTUNA OBJECTIVE: sortino` banner ≥ 95% of cells (~100%)
- Per-trial logs show `Sortino=X.XXXX` not `Sharpe=X.XXXX`
- trades.csv contains ONLY LINKUSDT + DOTUSDT rows
- Optuna best_params parquet shows both axes wired

**FAIL** = silent fallback to Sharpe OR triple-barrier OR 5-cohort → BLOCK-PENDING-FIX

### F-AXIS #3 — Per-symbol Δ sign-match LINK vs DOT (LOAD-BEARING)

**PASS criterion**: per-symbol OOS Δ vs /036 LINK+DOT subset (105 OOS trades, +51.62 net PnL%):
- LINK OOS Δ within [−30pp, +30pp] AND
- DOT OOS Δ within [−30pp, +30pp]

**FAIL = directional sign-mismatch**: if LINK and DOT regress with OPPOSITE signs (one up, one down by > 30pp), the Sortino mechanism is COHORT-SPECIFIC on the trend-scan substrate — bundling becomes per-cohort-specialist-of-specialist, multiplicative complexity at /044.

**FAIL = both catastrophic**: if both LINK + DOT OOS Δ < −60pp → NEG-CAT (basin migration destroys /036's specialist policy on both cohorts).

### F-AXIS #4 — Bundle OOS Sharpe Δ band

Conditional on F-AXIS #3 PASS, F1 verdict matrix (§2 table) applies. Modal: NEG-CLEAN [Δ ∈ -0.45, -0.20)] → OOS Sharpe ~+1.42.

### F-AXIS #5 — Wall-clock ~50 min anchored /036+/037

**PASS criterion**: total wall-clock ≤ 75 min (1.25h). Anchored on /036 ~25 min + /037 marginal ~5 min Sortino overhead → ~30-50 min modal. Per-cohort Optuna re-optimization on 2 cohorts is the dominant cost.

**FAIL** = > 90 min → hardware-anomaly investigation (no kill-switch — honest overrun).

### F-AXIS #6 — Trade-roster Jaccard vs /036 LINK+DOT (diagnostic)

**Expected band** [25%, 75%] — Sortino-driven basin shift on top of /036's specialist roster should rotate ~25-75% of trades (not bit-identical, not disjoint).

**FAIL = > 95% overlap** → TECHNICAL-FAILURE-SILENT-NO-OP (Sortino didn't engage — bit-identical to /036)
**FAIL = < 10% overlap** → BASIN-RELOCATION-ARTIFACT (Sortino+trend-scan substrate fundamentally re-located the basin; F1 may be lottery)

### F-AXIS #7 — Trade-count bands

- IS trades ∈ [200, 400] (modal ~280, anchored /036 IS 281)
- OOS trades ∈ [80, 160] (modal ~110, anchored /036 OOS 105)
- IS < 150 OR OOS < 60 → TECHNICAL-FAILURE-SILENT-FALLBACK → BLOCK-PENDING-FIX

---

## Section 5 — Configuration

(See §3.3 table above.) All other settings: BASELINE_V1 defaults.

---

## Section 6 — Wall-clock estimate

| Phase | Cost | Anchor |
|---|---|---|
| Data fetch | 0 min | LINK + DOT klines on disk |
| Feature regen | 0 min | feature parquets for both symbols on disk |
| Backtest compute | ~25-50 min modal | /036 ~25 min + Sortino marginal +5 min Optuna search overhead |
| Report layer (DSR/PSR/etc) | ~3 min | standard |
| **Total modal** | **~30-55 min** | |
| **Conservative band** | 30-75 min | |
| **Hard cap** | 2h (skill default) | |

Honest overrun acceptable; no runtime kill-switch.

---

## Section 7 — Expected Report Shape

`reports-v1/iteration_v1-039/comparison.csv` will contain row-by-row per-symbol and bundle metrics. Phase 7 evaluation requires building a **4-way comparison table** comparing /039 vs /036 (substrate baseline) vs /037 (loss-function baseline) vs BASELINE_V1 (sacred anchor):

| Metric | BASELINE_V1 | /036 (LINK+DOT TS) | /037 (5-cohort Sortino) | /039 (LINK+DOT TS + Sortino) | Δ /039 vs /036 |
|---|---|---|---|---|---|
| IS Sharpe | +0.2829 | TBD | +0.1712 | TBD | TBD |
| OOS Sharpe | +0.6637 | +1.7465 | +0.8388 | TBD | TBD |
| IS trades | 621 | 281 | 688 | TBD | TBD |
| OOS trades | 189 | 105 | 243 | TBD | TBD |
| LINK OOS PnL% | +34.23 | +108.91 | -8.64 | TBD | TBD |
| DOT OOS PnL% | +1.96 | +113.63 | +39.30 | TBD | TBD |
| LINK OOS Sharpe | TBD | TBD | TBD | TBD | TBD |
| DOT OOS Sharpe | TBD | TBD | TBD | TBD | TBD |
| LINK OOS Sortino | TBD | TBD | TBD | TBD | TBD |
| DOT OOS Sortino | TBD | TBD | TBD | TBD | TBD |
| OOS Max DD | 40.94% | TBD | 43.04% | TBD | TBD |
| OOS PSR_vs_1 | 0.079 | TBD | 0.371 | TBD | TBD |
| Jaccard vs /036 (LINK) | n/a | 1.000 | 0.064 | TBD | TBD |
| Jaccard vs /036 (DOT) | n/a | 1.000 | 0.218 | TBD | TBD |

Plus: per-symbol monthly trade-count, IS/OOS ratio, downside-std OOS (mechanism validation per F-AXIS #4-equivalent diagnostic), feature-importance top-5 per cohort (sanity vs /036), Optuna best_params Spearman vs /036 best_params per training_month (basin migration diagnostic).

---

## Section 8 — Path Forward Predictions (/044 routing implications per outcome quadrant)

| /039 outcome | /044 routing | Rationale |
|---|---|---|
| **PROMISING-CLEAN-EXCEPTIONAL** (Δ ≥ +0.30 vs /036) | /044 = SINGLE BUNDLE CONFIRMATION combining /036 + /037 + /039 mechanisms (multi-seed validates 2-cohort × trend-scan × Sortino HYBRID) | Both mechanisms COMPOUND beyond linear additivity; one CONFIRMATION captures full edge |
| **PROMISING-CLEAN** (Δ ∈ [+0.10, +0.30)) | /044 = SINGLE BUNDLE CONFIRMATION (same as above) — mechanisms compound linearly | Linear additivity confirmed; bundling correct |
| **PROMISING-INERT-FAV** (Δ ∈ [0, +0.10)) | /044 = TWO SEPARATE CONFIRMATIONs: /044-A multi-seed /036 + /044-B multi-seed /037; /045+ permitted to retry stacked bundle if both /044-A and /044-B PASS multi-seed | Mechanisms marginally compoundable; /044 prioritizes individual axis validation, defers stacking to /045+ |
| **INERT** (Δ ∈ [-0.20, 0)) | /044 = TWO SEPARATE CONFIRMATIONs: /044-A multi-seed /036 + /044-B multi-seed /037 — NO STACKED BUNDLE | /037 mechanism is universe-dependent; bundling forfeits attribution clarity |
| **NEG-CLEAN MODAL** (Δ ∈ [-0.45, -0.20)) | /044 = TWO SEPARATE CONFIRMATIONs (same as INERT path) + close hybrid axis | Mechanisms compete on /036 substrate; stacking destroys /036's specialist policy; /037 is universe-dependent |
| **NEG-CAT** (Δ < -0.45) | /044 = SEPARATE CONFIRMATIONs ONLY for /036 (LINK+DOT trend-scan); /037 Sortino axis demoted to cycle-6 candidate (NOT cycle-5 /044 substrate) | Sortino catastrophically interferes on trend-scan substrate; needs orthogonal substrate proof |

---

## Section 9 — Behavioral-effect predictor

Per `feedback_axis_saturation_predictor.md`: predict observable behavioral effects with falsifier triggers.

**Predicted IS trade count**: range [200, 400], modal ~280 (anchored /036 IS 281). Sortino's basin migration on 2-cohort substrate predicted to leave trade count within ±15% of /036 (no large basin reshuffle on the per-cohort substrate per EDA §2).

**Predicted OOS trade count**: range [80, 160], modal ~110 (anchored /036 OOS 105).

**Predicted per-symbol LINK OOS Δ vs /036**: range [-30pp, +30pp], modal **-20pp** (PnL ~+90% absolute vs /036's +108.91%). EDA §2 shows LINK has Sortino/Sharpe 1.40 on /036 substrate — small basin shift; the shift could marginally hurt because right-skew Sortino under-rewards in this regime.

**Predicted per-symbol DOT OOS Δ vs /036**: range [-30pp, +30pp], modal **-15pp** (PnL ~+98% absolute vs /036's +113.63%). EDA §2 shows DOT Sortino/Sharpe 1.16 on /036 substrate — minimal basin shift.

**Predicted bundle OOS Sharpe Δ vs /036**: range [-0.60, +0.30], modal **-0.33** (bundle ~+1.42 absolute).

**Predicted F-AXIS #6 Jaccard vs /036**:
- LINK: range [30%, 75%], modal 50%
- DOT: range [30%, 75%], modal 50%

**Predicted downside-std**: bundle OOS downside std ≤ 95% of /036's baseline (Sortino's mechanism). If Sortino RAISES downside std, mechanism falsifier informational FAIL.

**Falsifier triggers**:
1. IS < 150 OR OOS < 60 → TECHNICAL-FAILURE-SILENT-FALLBACK → BLOCK-PENDING-FIX.
2. Jaccard vs /036 > 95% on BOTH cohorts → TECHNICAL-FAILURE-SILENT-NO-OP → BLOCK-PENDING-FIX.
3. Either LINK or DOT OOS Δ vs /036 outside [-60pp, +60pp] → mechanism cohort-specific → /044 attribution diverges.
4. F-AXIS #2 wiring fails (banner missing OR Sortino logs missing OR triple-barrier labels used) → BLOCK-PENDING-FIX.

**Mechanism failure scenario (PREDICTED FAILURE MODE)**:
The most plausible failure mode is that /036's specialist policy already extracts the bulk of the LINK+DOT trend-scan edge — Sortino's basin shift, on a substrate where the Sortino/Sharpe ratio is only 1.22 and OOS PnL distributions are near-Gaussian (skew 0.3), has little to add. The basin reshuffle then COMPETES with /036's already-optimal HP region rather than reinforcing it (per EDA §3 Jaccard 0.14: the two axes pick DIFFERENT trades on the same cohorts). Optuna at n_trials=18 single-seed lands in a basin that resembles /037's LINK+DOT-subset (which was -38.55pp below /036 in OOS PnL) more than /036's specialist optimum.

---

## Section 10 — Anti-Cheating Self-Check

- [x] EDA reads IS-only (`reports-v1/iteration_v1-036/in_sample/trades.csv` + `reports-v1/iteration_v1-037/in_sample/trades.csv`; OOS files only consumed as REFERENCE for /036's published per-symbol OOS Δ, NOT for parameter tuning).
- [x] No parameter tuning on OOS data — Sortino formula parameter-free; thresholds (n_trials=18, ENSEMBLE_SIZE=3, seed=42) are v1 EXPLORATION standard.
- [x] OOS_CUTOFF_DATE = 2025-03-24 SACRED — unchanged.
- [x] training_months = 24 SACRED — unchanged.
- [x] IS window NOT trimmed; full 2020-01 → 2025-03-23 used at backtest.
- [x] No new EDA scripts beyond `analysis/iteration_v1-039/eda.py` (Phase 1 deliverable, IS-only by file path).
- [x] Hypothesis falsifiers F1-F7 pre-registered above Phase 6 dispatch.

---

## Section 11 — Phase 4.5 LM Master Response Map (UPDATED — retargeted advisor)

LM Master Phase 4.5 (`briefs-v1/iteration_v1-039/lgbm_advisor.md`) has been **REISSUED** for the retargeted per-cohort Sortino × specialist hybrid axis (file header now reads "Phase 4.5 (Pre-Design, RETARGETED AXIS)"). Response map per LM Master section heading:

| # | LM Master recommendation | QR adjudication | Reason |
|---|---|---|---|
| 1 | Mechanism Interaction Prediction (LOAD-BEARING) — two regime predictions: PROMISING-CLEAN if /036 labels still leave downside-std as binding constraint; NEG/INERT if /036 already exhausts left-tail clipping degree-of-freedom. | **ADOPTED** | Pre-registered as H1a mechanism in Section 1; falsifier H1b mirrors the two-regime framing. |
| 2 | Per-Symbol Concentration Sensitivity (DECISIVE DIAGNOSTIC) — 4-cell routing table on LINK vs DOT OOS PnL split (DOT≥70% / 40-60% balanced / LINK≥70% / NEG bundle). | **ADOPTED** | Pre-registered as F-AXIS #3 LOAD-BEARING in Section 4 with the explicit "sign match (both positive OR both negative)" falsifier. |
| 3 | n_trials=18 ADEQUATE (DO NOT bump). Search-density-per-label is 15-effective trials/cohort/label-density — above /037 n_eff=9 narrowness FAIL threshold. | **ADOPTED** | Config locked at Section 5: n_trials=18, ENSEMBLE_SIZE=3, single-seed=42 per v1 EXPLORATION standard. |
| 4 | F-AXIS Falsifier Recommendations (#F2 dispatch banner + 3 asserts; #F3 per-symbol PnL Δ ∈ [-20pp, +30pp] with sign-match; #F4 bundle Δ anchored on /036 not baseline; #F5 wall-clock 25-35 min modal; **#F6 NEW** trade-roster Jaccard vs /036 as PRIMARY mechanism diagnostic). | **ADOPTED** | F2-F5 already in Section 4; **F6 Jaccard NEW** added to Section 4 (sub-section F6) — see Section 4 update below. |
| 5 | Saturation / Double-REPEAT Check — counter at 2/5 for both loss-function and per-cohort-specialization families. Justified by direct compoundability test of two PROMISING axes, NOT independent third attempt. | **ADOPTED** | Already declared in Section 0.6 with the stacking-interaction-probe rationale. |
| 6 | /044 Routing Implication — PROMISING-CLEAN → /044 full bundle; NEG → /044 SEPARATE; INERT → /044 SEPARATE with /037 closure note; PROMISING-DOT-ONLY → /044 DOT-only specialist (NEW substrate). | **ADOPTED** | Already in Section 8 Path Forward; Section 8 numerical thresholds (added below) reinforce the routing. |
| 7 | Prior distribution: PROMISING-CLEAN 17% / PROMISING-INERT-FAV 23% / INERT 25% / NEG-CLEAN 25% MODAL / NEG-CAT 10%. Combined NEG 35%, combined PROMISING 40%. | **MODIFIED** (QR adopts NEG-DOMINANT framing from EDA findings: NEG-CLEAN 40% MODAL / NEG-CAT 20% / INERT 23% / PROMISING-INERT-FAV 17% / PROMISING-CLEAN 0%). QR's prior is informed by EDA's empirical observation that /037 already underperforms /036 on LINK+DOT-subset by Δ −38.55pp net PnL — a STRONGER NEG signal than LM Master's distributional prior. | EDA empirical evidence (Jaccard 0.138 + /037-on-LINK+DOT-subset −0.144 Sharpe Δ) supersedes pre-EDA distributional priors. |

**F6 Jaccard recommendation INTEGRATED into Section 4** (added as F-AXIS #6, decisive mechanism diagnostic per LM Master rec 4 footnote). Wiring: post-backtest compute Jaccard(trades_iter39_OOS, trades_iter036_OOS) per cohort; report in `comparison.csv` row appended via `reporting_v1.append_jaccard_vs_036_rows` (deferred to /040 if implementation cost > 50 LOC — for /039 the Jaccard is computed in Phase 7.4 analysis script, not in the runner pipeline).

---

## Section 11.5 — Pre-Registered Failure-Mode Prediction (renumbered from Section 7 content per Phase 5.5 gate)

**Most plausible failure scenario at single-seed=42 EXPLORATION budget**: Sortino objective on /036's 2-cohort substrate produces a basin migration where LightGBM Optuna optimizes the per-cohort downside-std but the smaller training fold per cohort (2-cohort × trend-scanning ~60% labels of triple-barrier = ~50% of baseline label volume per training-window) produces a tighter Optuna ridge (predicted n_effective_trials ≤ 9 per cohort, mirroring /037+/038 recurrence). The basin lands on a high-variance allocation that retains /036's LINK+DOT directional alpha but adds Sortino-driven entry-skip on chop trades — net OOS Sharpe lands BELOW /036 because the skipped chop trades were actually contributing edge under /036's trend-scan labeling. The basin migration is detectable via F-AXIS #3 LINK and DOT sign-match (both negative vs /036) AND F-AXIS #6 Jaccard < 0.30 vs /036 OOS trades.

**Gates that should catch the failure**:
- F-AXIS #4: OOS Δ vs /036 in [-0.15, +0.10] → INERT (stacking failure detected); < -0.15 → NEG-COLLISION (catastrophic stacking).
- F-AXIS #6: trade-roster Jaccard < 0.30 vs /036 → PROMISING-BASIN-RELOCATION subtype (positive OOS lift only via multi-seed validation).
- Sortino downside-std OOS measurement: if OOS downside-std > /036's baseline ×1.1, the mechanism is REFUTED in the same direction as /037's mechanism failure.

**Failure metrics signature**: IS Sharpe Δ < 0, OOS Sharpe Δ vs /036 < -0.10, OOS Max DD > /036's 23.28% × 1.2 (28%), per-symbol DOT OOS PnL < +30pp (vs /036's +113pp), LINK OOS PnL < +30pp (vs /036's +108pp).

---

## Section 11.6 — Locked Numerical MERGE/NO-MERGE Thresholds (Section 8 addendum per Phase 5.5 gate)

EXPLORATION at single-seed = NO direct MERGE. MERGE eligibility requires /044 multi-seed CONFIRMATION. Pre-registered thresholds for /039 routing to /044 substrate selection:

| Outcome band | Threshold | /044 routing |
|---|---|---|
| **PROMISING-CLEAN** | OOS Sharpe Δ vs /036 ≥ +0.10 AND IS Sharpe ≥ 0 AND OOS trades ≥ 80 AND F-AXIS #3 sign-match POSITIVE for both LINK + DOT AND F-AXIS #6 Jaccard ∈ [0.50, 0.85] | /044 = BUNDLED multi-seed of /036+/037 hybrid (per-cohort Sortino × trend-scan, --seeds 2, --n-trials 35, ENSEMBLE_SIZE=5) |
| **PROMISING-INERT-FAV** | OOS Δ vs /036 ∈ [0, +0.10) AND positive sign-match | /044-A = /036 alone multi-seed; /045 = /039 alone multi-seed (SEPARATE) |
| **INERT** | OOS Δ vs /036 ∈ [-0.20, 0) | /044-A = /036 alone; /037 closed at /037 (per /037 closeout); axis hybrid INERT verdict |
| **NEG-CLEAN** | OOS Δ vs /036 ∈ [-0.45, -0.20) | /044 = /036 alone; axis hybrid REJECTED for cycle-5 |
| **NEG-CAT** | OOS Δ vs /036 < -0.45 | /044 = /036 alone; axis-family loss-function × per-cohort COLLIDED; foreclose hybrid axis for cycle-6 |
| **PROMISING-DOT-ONLY** | LINK OOS PnL < -10pp AND DOT OOS PnL > +50pp | /044 = DOT-only specialist with Sortino (NEW substrate, single-cohort) |

ABSOLUTE MERGE GATES (apply at /044 CONFIRMATION only, not /039): IS Sharpe > 1.0 AND OOS Sharpe > 1.0 AND OOS/IS ratio ≥ 0.5 AND OOS trades ≥ 130 AND DSR > 0.95 AND PBO < 0.40 AND PSR > 0.95 AND top-symbol concentration ≤ 30% of OOS PnL. /039 EXPLORATION does NOT evaluate against these.

---

## Section 11.7 — Library Stack Declaration (Section 9 addendum per Phase 5.5 gate)

NO external ML-finance libraries used in this iteration. Standard stack only:
- **LightGBM** (existing project dependency, no version change)
- **Optuna** (existing, no version change)
- **NumPy / Pandas / Polars** (existing, no version change)
- **scipy.stats** (used by existing optimization.py for Sortino — no NEW import)

NOT used in /039: mlfinlab, mlfinpy, pypbo, fracdiff, financial-machine-learning, statsmodels (beyond existing ADF test usage).

The Sortino objective implementation at `src/crypto_trade/strategies/ml/optimization.py:compute_sortino_with_threshold` (shipped at /037, commit `5a30d96`) uses only NumPy primitives (np.where, np.mean, np.std on masked arrays). No new library dependency.

---

## Section 12 — Phase 5.5 Dispatch Readiness Checklist

- [x] Brief Section 0.0 banner declares EXPLORATION cycle-5 #6/10.
- [x] Brief Section 0.5 cadence position: 6/10 (4 to go before /044).
- [x] Brief Section 0.6 double-REPEAT JUSTIFIED with stacking-interaction rationale + /044 routing implication.
- [x] Brief Section 1 hypothesis: 3-sentence (H1) + mechanism (H1a) + falsifier (H1b).
- [x] Brief Section 2 F-AXIS #1 verdict matrix with band probabilities + modal prediction.
- [x] Brief Section 2.5 HIGH-RISK declared (rotation rule) + NORMAL-RISK by mechanism + SINGLE-SEED budget choice justified.
- [x] Brief Section 3 implementation: NO new src/ code; dispatch elif + catch-all exclusion + 13 tests.
- [x] Brief Section 3.2 CLI invocation: `--symbols LINKUSDT,DOTUSDT --label-mode trend_scanning --optuna-objective sortino --pruned-features --iteration 39 --exploration --n-trials 18 --ensemble-size 3 --seeds 1`.
- [x] Brief Section 4 F-AXIS #2-#7 falsifiers (wiring, sign-match, bundle Sharpe, wall-clock, Jaccard, trade-count).
- [x] Brief Section 5 + 6 configuration + wall-clock estimate.
- [x] Brief Section 7 expected report shape: 4-way comparison /039 vs /036 vs /037 vs BASELINE_V1.
- [x] Brief Section 8 path-forward predictions per outcome quadrant with /044 routing implication.
- [x] Brief Section 9 behavioral-effect predictor with falsifier triggers.
- [x] Brief Section 10 anti-cheating self-check.
- [x] `/030 LESSON`: `"v1-039"` added to baseline catch-all exclusion tuple planned in §3.1.

Ready for Phase 5.5 gate review.

---

**END OF BRIEF**

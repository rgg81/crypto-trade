# iter-v3/071 — Research Brief

**Cycle 2 EXPLORATION #1 of 10. Axis: META-LABELING (structural). Path A.**

---

## Section 0 — Data Split Declaration

- **IS window**: data start → `OOS_CUTOFF_DATE` (2025-03-24). IMMUTABLE.
- **OOS window**: `OOS_CUTOFF_DATE` → data end. The QR does not see OOS results until Phase 7.
- **training_months**: 24. IMMUTABLE.
- **Walk-forward**: `generate_monthly_splits` applies `compute_embargo_candles(10080, 480) = 22` candles; `train_end_ms = test_start_ms - embargo_ms`.
- **Universe**: BCH, LDO, TRX (V3_MODELS unchanged; REQUIRED_GAP = 66 = (21+1) × 3).
- **Sacred constants**: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — UNCHANGED.

> **Walk-forward lookahead bug carry-over.** Per `feedback_v3_walkforward_lookahead_bug.md`, the v3 worktree carries the pre-main-`5566a69` walk-forward state. BASELINE_V3.md states the /059 anchor inherits the fix at `e149e9d` (`train_end_ms = test_start_ms - embargo_ms`); /060 EXPLORATION-mode reference is post-fix. iter-v3/071 inherits the same post-fix state — no walk-forward change. Absolute Sharpe values across all v3 iterations remain bias-comparable (same embargo); deltas vs /060 are the load-bearing quantity.

## Section 0.5 — Iteration Type Declaration

- **TYPE**: EXPLORATION — cycle 2 #1 of 10 (iter-v3/071–080 = cycle 2 EXPLORATIONs; iter-v3/081 or later = cycle 2 CONFIRMATION).
- **Axis category**: STRUCTURAL — **model architecture (meta-labeling)**. Category 2 per `feedback_v3_structural_over_knob_exploration.md` (NEW model arch). This is the HIGHEST cycle-2 priority per `feedback_v3_iter017_metalabeling_mandate.md` and the iter-v3/070 Phase 8 closeout (Section 10 priority #1).
- **Run mode**: `--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3` (ENSEMBLE_SEEDS[0:3], outer=42 lineage subset), `--n-trials 35`. Per `feedback_v3_unified_10seed_baseline.md` EXPLORATION/CONFIRMATION mode separation.
- **Run command**: `uv run python run_baseline_v3.py --exploration --model metalabeling --clean-oof`
- **Anchor**: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403). Confirmed valid — see Section 2.10.
- **Wall-clock target**: meta-labeling adds an M2 Optuna study per (symbol, walk-forward month). /017 ran ~30 min at single-seed `--n-trials 10`. At 3-seed `--n-trials 35`, M1 cost ≈ 3 × the /060 EXPLORATION M1 cost; M2 adds a parallel per-cell Optuna study of comparable per-study size. **Estimated wall-clock: 1.5–2.2h.** This **may exceed the 1.1h EXPLORATION nominal and could touch the 2h cap.** Flagged. If the Engineer's pre-flight timing projection exceeds 2h, the Engineer must report this and the orchestrator decides whether to proceed or reduce `--n-trials` to 25 (which stays above the TPE warmup saturation ~30 only marginally — a 25-trial fallback would itself be a deviation requiring a note).

## Section 1 — Testable Hypothesis (ONE sentence)

Replacing the M1-only `LightGbmStrategy` with `MetaLabelingStrategy` (M1 direction model + M2 binary precision classifier per López de Prado AFML Ch. 3, M2 vetoing M1 signals whose M2-confidence < 0.5) lifts both IS and OOS monthly Sharpe ≥ +0.10 vs the /060 EXPLORATION anchor by filtering low-quality M1 signals — primarily the LDO directional bleed.

## Section 2 — Numerical EDA Tables

EDA committed at SHA `4f32ec5` (`analysis/iteration_v3-071/metalabeling_eda.py` + 7 output files). All tables computed on the /060 EXPLORATION-mode trade roster, IS-anchored.

### Section 2.1 — T0 Anchor-value declaration (Rule 1 compliance)

Per `feedback_v3_iter064_process_lessons.md` Rule 1, every anchor value is byte-exact from `reports-v3/iteration_v3-060/comparison.csv`.

| Metric | /060 value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | `comparison.csv:2` |
| OOS monthly Sharpe | **+0.1403** | `comparison.csv:2` |
| OOS/IS monthly Sharpe ratio | 0.1685 | derived |
| IS n_trades | 159 | `comparison.csv:7` |
| OOS n_trades | 102 | `comparison.csv:7` |
| IS profit_factor | 1.2806 | `comparison.csv:5` |
| OOS profit_factor | 1.0482 | `comparison.csv:5` |
| IS win_rate | 31.4465% | `comparison.csv:6` |
| OOS win_rate | 39.2157% | `comparison.csv:6` |

/060 per-symbol (from `comparison.csv:18-20`): BCH OOS wpnl +1.9078 (37 trades, 32.4% WR); LDO OOS wpnl **-19.7208** (11 trades, 18.2% WR); TRX OOS wpnl +23.3119 (54 trades, 48.1% WR). **LDO is the dominant OOS drag** — the symbol meta-labeling targets.

### Section 2.2 — T1 M1 signal quality (the M2 training target distribution)

The M2 binary label (per `metalabeling.py:480-488`) is 1 if the M1-predicted direction produced `net_pnl > 0`, else 0. T1 is the M2 target's IS prior.

| Symbol | IS trades | TP | SL | timeout | TP-hit rate | M2 pos rate (net_pnl>0) |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 73 | 27 | 40 | 6 | 36.99% | 45.21% |
| LDO | 11 | 3 | 8 | 0 | 27.27% | 27.27% |
| TRX | 75 | 19 | 53 | 3 | 25.33% | 29.33% |
| **PORTFOLIO** | **159** | **49** | **101** | **9** | **30.82%** | **36.48%** |

M1 emits a directional signal that resolves TP only ~31% of the time. **63.5% of M1's trades close net-negative.** This is the population M2 must filter — if M2 could perfectly separate the 36.5% winners from the 63.5% losers, it would transform a profit-factor-1.28 strategy into a high-precision one. T1 confirms there IS a large loser population for M2 to target; the open question (T3) is whether M2 has the *information* to separate them.

### Section 2.3 — T2 M1-confidence-vs-outcome separability (weak proxy)

The /060 roster does not persist M1's `predict_proba`. The only confidence-correlated quantity in the roster is `weight_factor` (RiskV3Wrapper vol-scaling × gate output) — a WEAK proxy. T2 splits IS trades at the per-symbol median `weight_factor`.

| Symbol | n (nonzero wt) | median wt | WR high-weight | WR low-weight |
|---|---:|---:|---:|---:|
| BCH | 60 | 0.705 | 60.0% | 40.0% |
| LDO | 10 | 0.685 | 40.0% | 20.0% |
| TRX | 63 | 0.790 | 25.0% | 29.0% |
| **PORTFOLIO** | **133** | **0.740** | **41.2%** | **33.9%** |

Higher-weight trades win more often on BCH (+20pp) and LDO (+20pp) but NOT TRX (-4pp). Portfolio +7.3pp. This is a weak, mixed signal — `weight_factor` is not M1 confidence, so this only rules in "a confidence-correlated quantity has *some* directionality" for 2 of 3 symbols. It is NOT a basis for Path B (M1-proba gating); the decisive test is T3.

### Section 2.4 — T3 same-feature M2 separability (DECISIVE for Path)

This is the load-bearing table. The iter-v3/017 PATH C failure (diary lesson #4, caveat #4) identified the mechanism: `MetaLabelingStrategy`'s M2 receives M1's OWN 14 features + M1's confidence (`metalabeling.py:265`). A same-feature M2 can only learn what M1's features already encode. T3 asks directly: on M1-fired bars, do M1's 14 features separate TP-hit (`net_pnl > 0`) from non-TP? We compute, per symbol, the univariate rank-AUC of each feature and report best/mean `|AUC - 0.5|`.

| Symbol | M1-fired bars | TP-hits | best \|AUC-0.5\| | mean \|AUC-0.5\| | Verdict |
|---|---:|---:|---:|---:|---|
| BCH | 73 | 33 | 0.1038 | 0.0406 | NEAR-ZERO-SIGNAL |
| LDO | 11 | 3 | — | — | **INSUFFICIENT** |
| TRX | 75 | 22 | 0.2144 | 0.0768 | RESIDUAL-SIGNAL |
| **PORTFOLIO** | **159** | **58** | **0.1222** | **0.0577** | **RESIDUAL-SIGNAL** |

Interpretation (decision rule pre-registered in the EDA script):
- **Portfolio best 0.1222 > 0.12 → RESIDUAL-SIGNAL.** There is *some* residual TP/non-TP structure in M1's own features. This clears the Path-D-defer bar — Path A is justified.
- **But the margin is thin and the mean is near-zero (0.0577).** 13 of 14 features carry essentially no winner/loser discrimination. Only TRX has a genuinely discriminating feature (0.2144). BCH — the dominant IS contributor — is NEAR-ZERO (0.1038, below threshold).
- **LDO — the target symbol — is INSUFFICIENT.** 11 trades, 3 TP-hits — too few to compute a stable AUC and far too few for M2 to *learn* anything LDO-specific.

T3 is the honest evidence that this is a borderline axis. It clears Path A but it pre-signals the /017 PATH C outcome as the most likely result (Section 7).

### Section 2.5 — T4 per-symbol M2 viability

M2 (`_train_m2_binary`, `metalabeling.py:67-80`) requires ≥10 M1-positive samples and both classes present. In the runner M2 trains **per walk-forward month** on a 24-month window — so per-cell M2 training sets are far thinner than the full-IS counts.

| Symbol | M1-fired full-IS | M2-pos | M2-neg | both classes | ~samples/month | per-month viable | flag |
|---|---:|---:|---:|---:|---:|:--:|---|
| BCH | 73 | 33 | 40 | yes | 2.81 | no | THIN-PER-MONTH |
| LDO | 11 | 3 | 8 | yes | 0.42 | no | **THIN-PER-MONTH** |
| TRX | 75 | 22 | 53 | yes | 2.88 | no | THIN-PER-MONTH |
| **PORTFOLIO** | **159** | **58** | **101** | **yes** | **6.12** | **no** | THIN-PER-MONTH |

All three symbols have THIN per-month M2 cells. **LDO at 0.42 M1-fired-bars/month is the critical limitation:** across a 24-month training window LDO accumulates ~10 M1-fired bars total. `metalabeling.py:445` skips M2 when M1-positive bars < 5. **M2 will very likely be inactive on most LDO month-cells**, meaning M1's LDO signal passes through unfiltered — the exact symbol the axis is supposed to fix is the symbol M2 can least act on. This is pre-registered as a failure mode in Section 7. (Note: `metalabeling.py` counts M1-*positive* bars at the M1 confidence threshold, which is a superset of M1-*fired* trades after risk gates — so the per-month M2 training set is somewhat larger than the trade-derived 0.42/month, but LDO remains by far the thinnest.)

### Section 2.6 — T5 trade-count reduction prediction

Meta-labeling REDUCES trade count (M2 vetoes some M1 signals). The /017 reference: M2 vetoed 42.7% of per-candle predictions → IS 209→159 (-24%), OOS 85→62 (-27%). T5 applies trade-level reduction scenarios to the /060 roster.

| Scenario | trade-level reduction | IS before→after | OOS before→after | OOS trades/month | trade-rate floor |
|---|---:|---:|---:|---:|---|
| optimistic | 15% | 159→135 | 102→87 | 6.21 | **BELOW-FLOOR** |
| /017-empirical | 25% | 159→119 | 102→76 | 5.43 | **BELOW-FLOOR** |
| pessimistic | 43% | 159→91 | 102→58 | 4.14 | **BELOW-FLOOR** |

**The trade-rate floor (≥10 OOS trades/month) is ALREADY breached at the /060 anchor: 102 OOS trades / 14 months = 7.29/month.** This is documented in BASELINE_V3.md (the /059 anchor itself is at 6.7/month — informational, not a hard EXPLORATION blocker). Meta-labeling can only reduce this further. **Under every M2-veto scenario the OOS trade rate falls further below the floor.** Section 8.5 pre-registers this: the trade-rate floor is treated as an informational metric for this EXPLORATION (consistent with how BASELINE_V3.md treats the /059 anchor's 6.7/month), NOT a hard fail — but if M2 over-filters to the pessimistic 43% the engineering report must flag the OOS sample as too thin for a reliable Sharpe.

### Section 2.7 — T6 predicted impact

Synthesised from T1–T5 and the /017 precedent (the only prior meta-labeling data point):

- **IS monthly Sharpe**: most-likely outcome is a SMALL regression or flat. /017 produced IS Δ -0.48 vs its /013 anchor. The mechanism (T3): a same-feature M2 strips signal alongside noise. The /071 difference vs /017: 3-seed ensemble (vs single-seed) + n_trials 35 (vs 10) + the unified-architecture /060 anchor. Ensemble averaging *may* dampen the single-seed M2 lottery, but does not give M2 new information. Predicted IS Δ band: **[-0.45, +0.15]**, median **-0.15**.
- **OOS monthly Sharpe**: /017 OOS was informational (62 trades). Predicted OOS Δ band: **[-0.30, +0.25]**, median **-0.02**. OOS is dominated by the LDO M2-inactivity problem (T4) — M2 likely cannot touch LDO, so the LDO drag persists.
- **Trade count**: IS 159 → ~119–135 (15–25% reduction); OOS 102 → ~76–87.
- **Per-symbol**: BCH — M2 NEAR-ZERO-signal, expect modest filtering with no quality lift. TRX — M2 has the best residual signal (0.2144), the symbol most likely to see a genuine precision lift. LDO — M2 likely inactive (T4), drag persists.

The honest synthesis: **T3 clears Path A but pre-signals PATH C (over-filter, no quality lift) as the dominant outcome.** This is a legitimate cycle-2 #1 EXPLORATION — the structural axis is mandated, the /017 result was on a retired anchor under different architecture, and a same-feature M2 re-test at the unified /060 anchor is the correct first cycle-2 data point. But the brief does not over-promise.

### Section 2.10 — EXPLORATION anchor confirmation

The cycle-2 EXPLORATION anchor is **iter-v3/060 EXPLORATION-MODE-REFERENCE: IS +0.8325 / OOS +0.1403** (`comparison.csv:2`). Confirmed valid:
- /060 is the unified-architecture 3-seed EXPLORATION-mode reference (per `feedback_v3_cycle1_axis_pass_criteria.md`).
- The codebase post-iter-v3/070 closeout reverted `DEFAULT_ATR_MULTIPLIERS` (2.0,1.5)→(2.0,1.0) (commit `8bdf392`) and Path B4 is reporting-layer-only (zero trade-roster effect). The 14-feature set, the 3-symbol universe, and the risk-gate stack are all at the /060 state.
- Therefore the current codebase, run in EXPLORATION mode with `--model lgbm`, is **/060-trade-roster-equivalent**. /060 is the valid cycle-2 EXPLORATION anchor. (BASELINE_V3.md still tags `v0.v3-059` as the canonical CONFIRMATION-mode baseline; /060 is the parallel EXPLORATION-mode reference, not a replacement.)

## Section 3 — Spec (LOCKED — single-axis variation)

**ONE substantive change:** replace the M1-only `LightGbmStrategy` with `MetaLabelingStrategy` (M1 + M2) via the existing `--model metalabeling` CLI route.

`MetaLabelingStrategy` **already exists** at `src/crypto_trade/strategies/ml/metalabeling.py` (added at iter-v3/017, 560 lines, 11 unit tests at `tests/strategies/ml/test_metalabeling.py`). The runner **already wires it**: `run_baseline_v3.py:1487-1492` routes `--model metalabeling` to `MetaLabelingStrategy(**common_kwargs)`; `run_baseline_v3.py:2029-2038` registers the `--model` choice; `_build_v3_model` / `_write_feature_importance` already handle the M1-unwrap (`run_baseline_v3.py:1796-1823`).

**Therefore this axis requires ZERO new strategy/model code.** The single change is the run invocation: `--model metalabeling`. The brief's "code edits" are limited to:

1. **`ITERATION_LABEL`**: `"v3-070"` → `"v3-071"` (`run_baseline_v3.py:128`). Cosmetic; required so reports land in `reports-v3/iteration_v3-071/`.
2. **No other code change.** `--model metalabeling` is the axis. `DEFAULT_ATR_MULTIPLIERS` stays (2.0,1.0); the 14-feature set, universe, and risk gates are UNCHANGED — single-axis discipline.

M2 configuration (inherited from the existing `MetaLabelingStrategy`, NOT changed by this iteration — preserving single-axis discipline):
- M2 = `LGBMClassifier`, binary objective, `is_unbalance=True`, trained per (symbol, walk-forward month) on M1-positive bars.
- M2 input = M1's 14 V3 features + M1's `predict_proba` confidence = 15-dim vector (`metalabeling.py:265`).
- M2 confidence threshold = **0.5 PINNED** (`metalabeling.py:328`) — Bayes-optimal default, NOT tuned. Pinning is load-bearing for single-axis discipline.
- M2 Optuna budget = same `--n-trials` as M1 (35 in EXPLORATION mode), `n_eff` per `_m2_objective` F1 maximisation.
- M2 label = 1 if M1-predicted direction's `net_pnl > 0` (`metalabeling.py:488`). Per the /017 caveat #3, this conflates "TP-first-hit" with "timeout-positive-walk." **This iteration KEEPS the existing `pnl > 0` label** — changing it to strict-TP-first would be a SECOND axis. The /017 verdict was robust to either label definition; the conflation is documented and non-blocking. (A strict-TP-first M2 label is a candidate for a *future* meta-labeling EXPLORATION, not this one.)

**Why same-feature M2 despite the /017 PATH C lesson.** The /017 diary lesson #4 recommends DIFFERENT M2 features (funding, OI, regime indicators M1 doesn't use). That is the *correct* long-run fix — but it is a TWO-axis change (new model architecture + new feature family) and violates single-axis discipline. Cycle 2 #1 isolates the structural model-architecture axis: does meta-labeling-as-a-mechanism help at the unified /060 anchor? T3 shows portfolio residual signal clears the 0.12 bar, so the same-feature M2 re-test is a legitimate (if conservative) first data point. If iter-v3/071 confirms PATH C again, a *subsequent* cycle-2 EXPLORATION can test M2 with distinct features — but that decision belongs to a future brief with its own EDA, not this one.

## Section 4 — Falsifier Bands (LOCKED — predicted intervals)

Anchor: /060 (IS +0.8325 / OOS +0.1403). Cycle-2 axis-PASS criteria per `feedback_v3_cycle1_axis_pass_criteria.md` carried into cycle 2 (the /070 closeout did not alter the EXPLORATION thresholds; the BASELINE_V3.md cycle-2 priorities section references the same PASS discipline).

> **Threshold note.** `feedback_v3_cycle1_axis_pass_criteria.md` states PROMISING-AT-EXPLORATION = (IS Δ ≥ +0.10 vs /060) **AND** (OOS Δ ≥ **+0.20** vs /060). The orchestrator prompt's Section 4 instruction states "IS shift ≥ +0.10 AND OOS shift ≥ +0.10." **This brief uses the memory-rule value (OOS Δ ≥ +0.20)** as the binding PROMISING threshold — the memory rule is the LOCKED, non-renegotiable artifact and cannot be loosened by a prompt. Section 4.1 and Section 8.1 both use +0.20. (The prompt's +0.10 is recorded here as a discrepancy; the stricter memory-rule value governs.)

### Section 4.1 — PROMISING-AT-EXPLORATION bands (IF /071 advances to cycle-2 CONFIRMATION)

- IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10 vs /060) **AND**
- OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20 vs /060) **AND**
- `frac_positive_paths` ≥ 0.50 (relaxed EXPLORATION threshold) **AND**
- no methodology FAIL (Critic 13 checks + §11 anti-pattern scan).

Predicted probability PROMISING fires: **15%** (Section 7).

### Section 4.2 — NEGATIVE bands (closes axis at catalog level)

- IS Δ < **-0.10** vs /060 (IS < +0.7325) **OR**
- OOS Δ < **-0.20** vs /060 (OOS < -0.0597).

Predicted probability NEGATIVE fires: **35%** (Section 7; per `feedback_v3_iter064_process_lessons.md` Rule 3, NEGATIVE for a structural model-arch axis is weighted ≥25%; /017 is a direct NEGATIVE precedent so 35%).

### Section 4.3 — INERT-AT-EXPLORATION zone

- IS Δ within **[-0.10, +0.10]** vs /060 **OR** OOS Δ within **[-0.20, +0.20]** vs /060 (noise band).

This is the **PATH C zone** for meta-labeling: M2 demonstrably active (veto rate measurable) but the headline Sharpe sits in the noise band — exactly the /017 pattern. Predicted probability INERT/PATH-C fires: **40%** (Section 7) — the dominant predicted outcome.

### Section 4.4 — SUSPICIOUS sub-mode + OOS/IS ratio gate (pre-registered per `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered OOS/IS ratio gate (MANDATORY per `feedback_v3_oos_is_ratio_gate.md`):** if the iteration's **OOS/IS monthly Sharpe ratio > 3.0**, classification is **SUSPICIOUS** regardless of absolute OOS Sharpe magnitude. A ratio above ~3.0 is the regime-exposure signature unmasked at /065/070 (and /026/027). The gate fires *in addition to* the Section 4.2/8.3 NEGATIVE bands.

SUSPICIOUS-OOS-DOMINANT sub-mode (per /065 precedent): IS Δ < 0 (regression) AND OOS Δ ≥ +0.20 (lift) → the axis is regime-exposed, not robust. For meta-labeling this would mean M2 filters in a way that helps the trending OOS window but not the chop/bear IS window.

Predicted probability SUSPICIOUS fires: **10%** (Section 7). Meta-labeling is a *precision filter* — it does not change direction, so the regime-bet mechanism is weaker than SL widening; but M2 trained on an IS window could still over-fit a regime.

### Section 4.5 — Saturation falsifier (per `feedback_axis_saturation_predictor.md`)

Behavioral-effect predictor — explicit estimate of how many IS trades change:

- **Predicted IS trade-count change**: 159 → 119–135 (a **15–25% reduction**, i.e. 24–40 fewer IS trades). M2 must veto a non-trivial fraction of M1 signals.
- **Saturation falsifier FIRES** (axis is mechanically inert) **if**: IS trade count ≥ 155 (i.e. < 4 trades vetoed) AND the per-symbol IS counts are within ±3 of /060's BCH 73 / LDO 11 / TRX 75. That would mean M2 is effectively passing every M1 signal — the meta-labeling layer is not engaging. If the saturation falsifier fires, the classification is **NULL-RESULT** (M2-inactive), distinct from PATH C (M2-active-but-no-lift).
- The engineering report MUST report the M2 per-candle veto rate (as /017 did: 42.7%). A veto rate < 5% with IS count ≥ 155 → NULL-RESULT. A veto rate ≥ 15% with headline Sharpe in the noise band → PATH C.

### Section 4.6 — Per-symbol Δ saturation falsifier

Per-symbol IS-trade-count shift expectation: BCH -10 to -20, TRX -10 to -20, LDO **-2 to 0** (M2 likely inactive on LDO per T4 — LDO's IS count is expected to barely move). If LDO's IS count shifts by > 5 trades, that is unexpected (M2 found enough LDO month-cells to train) and the engineering report must note it. If BOTH BCH and TRX shift by < 5 trades, the saturation falsifier (4.5) is corroborated.

### Section 4.7 — BCH IS concentration sensitivity (per Critic /059 Rec #3 + BASELINE_V3.md audit)

The /059 baseline has BCH at 95.76% of IS PnL — a fragility flag every cycle-2 brief must address. /060's IS BCH share is high (BCH IS net PnL dominates at 3-seed). Meta-labeling risk: M2's NEAR-ZERO-signal verdict on BCH (T3 = 0.1038) means M2 filters BCH essentially at random — a random ~15-20% cut of BCH's 73 IS trades could remove BCH winners and *increase* concentration fragility or collapse the BCH IS contribution. **Pre-registered BCH sensitivity check**: if BCH IS net PnL falls > 30% vs /060 while LDO/TRX are flat, the headline IS Sharpe will likely collapse (the /063/064 pattern). The engineering report must report BCH IS net PnL explicitly.

## Section 5 — Cross-Axis Orthogonality

iter-v3/071 varies exactly ONE axis: model architecture (`LightGbmStrategy` → `MetaLabelingStrategy`). Everything else is held at the /060 state:

| Dimension | /060 state | iter-v3/071 | Changed? |
|---|---|---|:--:|
| Model architecture | LightGbmStrategy (M1 only) | MetaLabelingStrategy (M1 + M2) | **YES — the axis** |
| Feature set | 14 V3_FEATURE_COLUMNS | 14 V3_FEATURE_COLUMNS (M2 reuses them) | no |
| Universe | BCH, LDO, TRX | BCH, LDO, TRX | no |
| ATR multipliers | (2.0, 1.0) | (2.0, 1.0) | no |
| Triple-barrier timeout | 10080 min (21 candles) | 10080 min | no |
| Risk gate stack | 7-primitive (z-score 2.0, ADX 20, etc.) | unchanged | no |
| TRX vol_scale_floor | 0.5 (per-symbol, /061) | unchanged | no |
| Ensemble | EXPLORATION 3-seed | EXPLORATION 3-seed | no |
| n_trials | 35 | 35 (M1 and M2 each) | no |
| M2 threshold | n/a | 0.5 PINNED (not a tunable axis this iter) | n/a |

The M2 threshold (0.5), the M2 feature set (= M1's 14 + confidence), and the M2 label definition (`pnl > 0`) are all INHERITED from the existing `MetaLabelingStrategy` and explicitly NOT varied — pinning them preserves single-axis discipline. A future meta-labeling EXPLORATION could vary one of them; this iteration does not.

## Section 6 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. iter-v3/071 is an EXPLORATION (not a merge candidate) but the section is included for completeness.

- **R1–R3 / 7-primitive gate stack**: UNCHANGED. The RiskV3Wrapper wraps `MetaLabelingStrategy` transparently — `MetaLabelingStrategy` exposes the same `compute_features` / `get_signal` / `skip` interface as `LightGbmStrategy` (`metalabeling.py:279-345`), so all 7 risk primitives (BTC trend kill, vol scaling, ADX, Hurst, z-score OOD, low-vol filter, hit-rate) operate identically on M2-passed signals.
- **Meta-labeling AS a risk primitive.** Conceptually M2 is itself a precision/risk filter — it vetoes low-confidence M1 directional calls. The axis is *adding* a risk-management layer (López de Prado's framing: ML's edge is filtering, not forecasting). The risk this introduces is **over-filtering** (M2 vetoes too many signals — the /017 PATH C outcome), mitigated only by the 0.5 threshold pinning being a conservative (not aggressive) cutpoint.
- **Look-ahead audit (non-negotiable).** `MetaLabelingStrategy._train_m2_for_month` (`metalabeling.py:351-534`) trains M2 EXCLUSIVELY on `M1._split_map[month_str].train_*` window data; M2 labels are derived from `label_trades` on the same training indices (`metalabeling.py:462-471`). No test-window candle is observed. The /017 Critic Check 1 verified this PASS. The walk-forward embargo (REQUIRED_GAP=66) is inherited unchanged — M2 introduces no new label-leakage path.
- **Trade-rate-floor risk** (T5): M2 filtering pushes OOS trades below the 10/month floor. Mitigation: the floor is treated as informational for this EXPLORATION (Section 8.5), consistent with the /059 anchor itself being at 6.7/month. If M2 over-filters to the pessimistic 43%, the engineering report flags the OOS Sharpe as thin-sample.

## Section 7 — Failure-Mode Probability Calibration

Per `feedback_v3_iter064_process_lessons.md` Rule 3 (NEGATIVE ≥25% for structural axes) and the /017 direct precedent:

| Outcome | Probability | Rationale |
|---|---:|---|
| **PATH C / INERT** (M2 active, headline in noise band, no quality lift) | **40%** | The /017 outcome reproduced. T3 mean \|AUC-0.5\|=0.0577 (near-zero) — same-feature M2 strips signal alongside noise. The dominant predicted outcome. |
| **NEGATIVE** (IS Δ < -0.10 OR OOS Δ < -0.20) | **35%** | /017 produced IS Δ -0.48 vs its anchor. M2 over-filtering removes M1 winners. Per Rule 3, structural-axis NEGATIVE weighted ≥25%; the /017 precedent pushes it to 35%. |
| **PROMISING** (IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20) | **15%** | Possible if the 3-seed ensemble dampens the single-seed M2 lottery enough that M2's marginal residual signal (T3 portfolio 0.1222) produces a genuine precision lift — most plausibly via TRX (T3 0.2144). Capped at 15% — same-feature M2 has no new information. |
| **SUSPICIOUS** (OOS/IS ratio > 3.0, or SUSPICIOUS-OOS-DOMINANT) | **10%** | M2 trained on the IS window could regime-overfit; precision-filter mechanism makes this weaker than SL-widening's regime bet. |

**Process predictions:**
- P1 — wall-clock 1.5–2.2h, may touch the 2h cap (Section 0.5). Probability it exceeds 2h: ~30%.
- P2 — M2 inactive on most LDO month-cells (T4: 0.42 M1-fired-bars/month); LDO IS trade count barely moves. Probability ≥ 70%.
- P3 — `MetaLabelingStrategy` integration runs clean (it has 11 unit tests + ran successfully at /017). Probability of integration failure: ~10%.

**Pre-registered most-likely outcome: PATH C / INERT (40%).** The brief does not predict success. The value of the iteration is a clean cycle-2 data point on whether meta-labeling-as-a-mechanism helps at the unified /060 anchor — and, if PATH C reproduces, a quantitatively-grounded mandate for a *future* meta-labeling EXPLORATION with DIFFERENT M2 features.

## Section 8 — LOCKED PASS/FAIL Criteria

Anchor: /060 (IS +0.8325 / OOS +0.1403). All thresholds LOCKED at brief setup; cannot be post-hoc renegotiated.

### Section 8.1 — Conjunctive-AND PROMISING-AT-EXPLORATION threshold

**PROMISING-AT-EXPLORATION** ⟺ ALL of:
- IS monthly Sharpe ≥ **+0.9325** (Δ ≥ +0.10 vs /060), AND
- OOS monthly Sharpe ≥ **+0.3403** (Δ ≥ +0.20 vs /060), AND
- `frac_positive_paths` ≥ 0.50, AND
- no Critic methodology FAIL.

→ axis carries forward to cycle-2 CONFIRMATION (iter-v3/081 or later), re-validated against /059's CONFIRMATION baseline at 10-seed mode.

### Section 8.2 — NEGATIVE-CLOSE threshold (DISJUNCTIVE OR)

**NEGATIVE** ⟺ EITHER:
- IS Δ < **-0.10** vs /060 (IS < +0.7325), **OR**
- OOS Δ < **-0.20** vs /060 (OOS < -0.0597).

A single-gate fail is sufficient (disjunctive OR — per `feedback_v3_iter064_process_lessons.md` Rule 4). → meta-labeling-as-same-feature axis CLOSED at catalog level; a future meta-labeling EXPLORATION would require DIFFERENT M2 features.

### Section 8.3 — INERT-AT-EXPLORATION zone (PATH C)

**INERT-AT-EXPLORATION** ⟺ IS Δ ∈ [-0.10, +0.10] vs /060 **OR** OOS Δ ∈ [-0.20, +0.20] vs /060 (and not NEGATIVE).
- **PATH C sub-flavor** (NEGATIVE-over-filter-quality-residual, per the /017-established taxonomy): INERT zone AND M2 per-candle veto rate ≥ 15% AND kept-trade per-trade economics (profit factor, WR) NOT above the /060 M1-only baseline. M2 demonstrably active but no quality lift.
- **NULL-RESULT sub-flavor**: INERT zone AND M2 per-candle veto rate < 5% AND IS trade count ≥ 155 (saturation falsifier 4.5 fired). M2 effectively inactive.

→ axis does NOT advance to cycle-2 CONFIRMATION.

### Section 8.4 — Disjunctive SUSPICIOUS gate (OOS/IS ratio — MANDATORY pre-registration)

**SUSPICIOUS** ⟺ EITHER:
- **OOS/IS monthly Sharpe ratio > 3.0** (pre-registered per `feedback_v3_oos_is_ratio_gate.md` — fires regardless of absolute OOS Sharpe), **OR**
- SUSPICIOUS-OOS-DOMINANT: IS Δ < 0 vs /060 AND OOS Δ ≥ +0.20 vs /060.

→ axis NOT eligible to advance to a CONFIRMATION bundle as an edge ingredient; re-examinable only with a structural mechanism hypothesis.

**Classification precedence**: SUSPICIOUS (8.4) takes precedence over NEGATIVE (8.2) when both fire (the ratio diagnostic identifies the *mechanism*). NEGATIVE takes precedence over INERT. PROMISING requires 8.1 to fire with no SUSPICIOUS/NEGATIVE.

### Section 8.5 — Trade-rate-floor safety net

Per `feedback_v3_trade_rate_floor.md` and `feedback_v3_trade_rate_floor_bundle_level.md`: the ≥10 OOS trades/month floor applies at CONFIRMATION-bundle level for v3, not per EXPLORATION row. For this EXPLORATION the OOS trade rate is **informational** (the /060 anchor is already at 7.29/month and the /059 canonical baseline at 6.7/month — both below the floor, both accepted as informational). **However**: if the OOS trade count falls below **52** (≈ 50% of /060's 102, the pessimistic-scenario floor), the engineering report MUST flag the OOS Sharpe as thin-sample and the Critic treats the OOS metric as low-confidence.

## Section 9 — Library Stack

No new external dependency. `MetaLabelingStrategy`'s M2 reuses `lightgbm.LGBMClassifier` (binary objective) — already pinned. The Optuna M2 study reuses the pinned `optuna`.

Pinned library stack (per BASELINE_V3.md Reproducibility Stamp): lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.

**Integration test status.** Per `feedback_v3_methodology_axis_integration_test.md`, the end-to-end smoke-test mandate applies to methodology-only axes that ADD computed fields to report files (dsr.json, comparison.csv). **Meta-labeling is a MODEL ARCHITECTURE change, not a methodology-only axis** — the rule explicitly carves out "Model architecture changes (caught by Hypothesis-Implementation alignment + result-verification)" as NOT subject to the integration-test mandate. Meta-labeling adds NO new computed fields to any report file; it changes the trade roster (M2 vetoes signals) and the existing comparison.csv/dsr.json schema is unchanged. Therefore **no NEW integration test is required.**

Existing coverage (sufficient):
- 11 unit tests at `tests/strategies/ml/test_metalabeling.py` (constructor, feature-column validation, M2 feature count, M2 binary label generation, M2-inactive NO_SIGNAL path, fast-mode propagation, distinctness from `LightGbmStrategy`).
- The `--model metalabeling` runner route ran end-to-end successfully at iter-v3/017.

**Phase 6 pre-flight check (Engineer):** verify the run log emits the `[M2]` training/veto lines (`metalabeling.py:383,441,503,534`) for the BCH and TRX month-cells — confirming M2 actually trains and engages. If `[M2]` lines are absent for BCH/TRX, M2 is not training and the run is a NULL-RESULT wiring failure, not a clean EXPLORATION. (LDO `[M2]` lines are expected to be sparse/absent per T4 — that is the predicted P2, not a wiring failure.) The engineering report must include the M2 per-candle veto rate (per /017 precedent: 2,976/6,965 = 42.7%).

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, every EXPLORATION axis is QR-selected with committed EDA backing.

- **Cycle / slot**: cycle 2 EXPLORATION #1 of 10 (iter-v3/071). First EXPLORATION after the cycle-1 CONFIRMATION (iter-v3/070, SUSPICIOUS-OOS-DOMINANT NO-MERGE).
- **Axis origin**: META-LABELING is a MANDATED axis, not an orchestrator ad-hoc pick. The mandate originates in `feedback_v3_iter017_metalabeling_mandate.md` (meta-labeling per López de Prado AFML Ch. 3, deferred from iter-v3/017's single-seed over-filter) and was re-affirmed as cycle-2 priority #1 at the iter-v3/070 Phase 8 closeout (`diary-v3/iteration_v3-070.md` Section 10: "HIGHEST — Model architecture (meta-labeling) ... the natural structural response to a directionally-bleeding symbol"). The cycle-1 closeout established that LDO structural weakness is the defining unresolved problem and cycle 2 must be STRUCTURAL — meta-labeling is the locked structural axis. No orchestrator pick was superseded; no Section-10 supersession entry is needed.
- **EDA SHA**: `4f32ec5` — `analysis/iteration_v3-071/metalabeling_eda.py` + 7 outputs (T0–T5 + synthesis.md).
- **Path selection — Path A** (full meta-labeling via the existing `--model metalabeling`):
  - **Path A chosen because**: T3 portfolio best `|AUC-0.5|` = 0.1222 > 0.12 → there is residual TP/non-TP structure in M1's own features that a same-feature M2 tree could exploit; this clears the Path-D-defer bar. AND `MetaLabelingStrategy` is already implemented, wired (`run_baseline_v3.py:1487-1492`), and tested (11 unit tests, ran at /017) — Path A is a **zero-new-strategy-code structural axis**, the minimal-risk way to execute the mandated meta-labeling axis at cycle-2 #1.
  - **Path B (M1-proba gating) rejected**: not true meta-labeling (no M2 model); the cycle-2 mandate is explicitly a STRUCTURAL axis (`feedback_v3_iter017_metalabeling_mandate.md` + `feedback_v3_structural_over_knob_exploration.md`). A higher M1-proba threshold is a knob, not a structure.
  - **Path C (pooled M2 across symbols) rejected**: pooling dilutes the LDO-specific precision the axis targets; per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, per-symbol model structure is the v3 norm. (Note: the `MetaLabelingStrategy` already trains M2 per symbol-month — Path A *is* the per-symbol architecture.)
  - **Path D (PASSIVE-DIAGNOSTIC defer) rejected**: T3 portfolio AUC clears the 0.12 residual-signal bar. Path D would be justified only if best `|AUC-0.5|` < 0.12 (M1's features carry zero residual signal). The portfolio number clears it — narrowly, but it clears. Deferring would be over-conservative given the axis is structurally mandated and /017 was on a retired anchor under a different (single-seed, buggy-walk-forward) architecture.
- **Honest framing**: T3 also shows the margin is thin (mean `|AUC-0.5|`=0.0577 near-zero; BCH NEAR-ZERO; LDO INSUFFICIENT). The brief pre-registers PATH C / INERT (40%) as the dominant predicted outcome and NEGATIVE (35%) as the second. This is a conservative cycle-2 #1 EXPLORATION: it executes the mandated structural axis with the existing same-feature M2, produces a clean unified-architecture data point, and — if PATH C reproduces — gives a quantitatively-grounded mandate for a future meta-labeling EXPLORATION with DIFFERENT M2 features (the /017 lesson-#4 fix). The same-feature M2 re-test must be done first to isolate the model-architecture axis from a feature-family axis (single-axis discipline).
- **Setup commit SHA**: `7303113` (this brief + ITERATION_LABEL bump to "v3-071").

---

**Brief LOCKED.** EDA SHA `4f32ec5`. Setup commit SHA `7303113`.

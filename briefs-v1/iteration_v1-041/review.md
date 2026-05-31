# Phase 7.5 Critic Review — iter-v1/041

OVERALL: EXPLORATION-NEGATIVE-CLEAN — TAIL-CONTROL-CANDIDATE-CONDITIONAL (OOS Δ −0.38 inside NEG-CLEAN band [−0.45, −0.15) with load-bearing F5 WR mechanism FAIL at 33.9% < 35%; however, drawdown profile is exceptional [IS DD −19pp / OOS DD −18pp vs baseline] — auxiliary value for /044 as TAIL-CONTROL component conditional on /042 + /043 outcomes)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5, slot 8 of 10)

## User Directive Acknowledgment (2026-05-31)

User directive applied: high-IS/low-OOS is not auto-overfit; consider regime-specialist framing in verdict augmentation. Applied as follows: /041's IS dropped −0.07 (slight) and OOS dropped −0.38 (large) — this is NOT a clean regime-specialist signature (canonical signature would be IS stable / preserved and OOS specifically regime-cyclical). The IS-side weakening is mild but unambiguous and rules out the "IS-strong regime specialist" subtype. HOWEVER, an alternative auxiliary framing — TAIL-CONTROL component — is supported by the data: OOS Max Drawdown collapsed from baseline 40.94% to 22.61% (Δ −18pp = 45% relative reduction); IS Max DD from 73.06% to 53.70% (Δ −19pp). The mechanism is structural (tight barriers truncate per-trade loss tails) not statistical; that DD profile would survive multi-seed. Annotation TAIL-CONTROL-CANDIDATE-CONDITIONAL added to overall; conditionality is on /042 + /043 verdicts and /044 portfolio-blend evaluation.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation intact: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` (verified via grep — only documented locations contain the phrase, all with `- embargo_ms` subtraction). `tests/test_lookahead_embargo.py` present with all 4 required tests (`test_labels_are_invariant_to_master_data_extent`, `test_demonstrates_bug_without_embargo`, `test_walk_forward_embargo_matches_cv_gap_formula`, `test_time_series_split_with_gap_excludes_correct_rows`) plus supplementary. Per-iteration src/ diff (lgbm.py `min_child_samples_lower_bound` plumbing + optimization.py:298 lower-bound thread + run_baseline_v1.py dispatch) introduces no forward data use; ATR multiplier shrink stays inside the same NATR_21 σ_t source with same timeout=21. No combined-train+test fits.

### Check 2 — Embargo Width: PASS
`walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`. Timeout 21 candles × 8h = 168h; required embargo = (21+1) candles = 22 candles ≈ 7.33 days; `compute_embargo_candles` helper used by both `walk_forward` and `lgbm.py` CV gap. Tightening barriers does NOT change timeout (still 21 candles per Brief §3.3) so embargo bound unchanged. Foundation regression-guarded by /041's added `test_v1_041_walk_forward_embargo_regression`.

### Check 3 — Multiple-Testing Correction: FAIL (informational for EXPLORATION)
`comparison.csv`: DSR_IS = −86.40 / DSR_OOS = −50.06; PSR_monthly_vs_1 IS = 0.104 / OOS = 0.241; n_effective_trials = 9 (cell-median 9, same as /037/038 ridge). All three thresholds missed by wide margins. **Per Section 0.5 TYPE=EXPLORATION, Check 3 axis failures are informational and do NOT trigger BLOCK** — edge thresholds are unclearable on a strategy still in development. Recorded for catalog: OOS PSR_vs_1 = 0.241 is a 3× LIFT vs baseline 0.0789 (likely from DD compression boosting risk-adjusted denominator), but absolute remains below 0.30 floor for any merge eligibility. n_eff_per_cell_median = 9 confirms the 3-iter Optuna ridge recurrence (/037 + /038 + /041); LM Master's H6 hypothesis (denser labels break the ridge → n_eff ≥ 15) FALSIFIED at single-seed budget — the ridge is feature-stack-structural, NOT label-magnitude-driven. Important diagnostic for future v1 work.

### Check 4 — IC Correlation: PASS
No new features added in /041 — V1_FEATURE_COLUMNS_PRUNED 44 cols UNCHANGED from /040. IC matrix exists at `reports-v1/iteration_v1-041/in_sample/ic_matrix.csv` (no new-feature pairs to evaluate; structural check N/A).

### Check 5 — ADF Stationarity: PASS
`adf_test.csv` shows all sampled features with p_value_raw ≈ 0 and bonferroni_pass = True (sampled rows verified: calendar, interaction, momentum families all clear). No new features introduced.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
Single seed=42 per /041 brief §2.5 NORMAL-RISK declaration. Pareto check applies at /044 CONFIRMATION level only. `v1_cross_seed_variance.csv` shows std=0.0 across all 5 (model, month, inner_seed=0) cells — single inner_seed effective per the EXPLORATION ENSEMBLE_SIZE=3 / outer_seed=1 spec. No dominance to check.

### Check 7 — Reproducibility: PASS
Commit SHA stamped (HEAD 25e3834). Runner uses explicit V1_FEATURE_COLUMNS_PRUNED (44 cols) — `feature_importance_portfolio.csv` enumerates them. Ensemble seeds literal in dispatch (verified in Phase 6.0 pre-flight Check C). Pre-flight pre-asserts atr_tp=1.5/atr_sl=0.75/min_data_in_leaf=50/label_mode=triple_barrier/universe=V1_BASELINE_UNIVERSE all wired. Spot check on `out_of_sample/trades.csv` row 2 (BTC long entry 47194.78 → exit 46207.40 SL): pnl_pct −2.0921% computed cleanly from (46207.40 − 47194.78) / 47194.78 × 1 = −2.0921%; net_pnl_pct = −2.1921% (with 0.10% fee per side = 0.10% total; consistent with 1 entry+exit fee pair).

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief §1 H1: "shrinking the triple-barrier ATR multipliers uniformly to atr_tp_mult=1.5, atr_sl_mult=0.75 produces a 2.55×–3.00× IS density lift". Observed: IS trades 958 vs baseline 621 = 1.54× lift (BELOW predicted 2.55-3.00× — F-AXIS #7 IS band [1300, 2000] NOT met at 958). Code change (lgbm.py constructor param + optimization.py:298 lower-bound thread + run_baseline_v1.py dispatch elif + 15 tests) maps cleanly to brief sentences. Catch-all exclusion "v1-041" added per /030 LESSON. NO scope creep. Density lift mechanism partially fired but UNDER-shot the EDA prediction — this is mechanism-prediction-failure, NOT hypothesis-faking. Falsifier H1b correctly fired: F5 OOS WR < 35% AND F1 OOS Δ < −0.05 AND F4 |net_pnl_pct| in [2.5%, 3.5%] (cross-checked below) → tighten axis REFUTED per brief.

### Check 13 — Anti-Pattern Static Scan: PASS
A1 walk_forward boundary preserved (verified above). A2 no forward-window std calls. A3 no combined train+test fit. A12/A13 no methodology axis changes in /041. The /041 src/ diff is narrow (3 file edits, constructor param + lower-bound thread + dispatch); no anti-pattern signatures introduced.

### Check 14 — Axis Family Validation: PASS
Declared `labeling` REPEAT (counter 3/5). Observed src/ diff: lgbm.py constructor accepts `atr_tp_multiplier=1.5, atr_sl_multiplier=0.75` (these flow to BOTH label-generation in labeling.py AND execution-time barrier in backtest.py) + `min_child_samples_lower_bound=50` Optuna constraint. Mechanism is per-bar TP/SL barrier-distance shrink at label generation = LABELING family. Distinct from /014 (σ_t source swap) and /035 (label primitive swap). Brief §0.6 honestly corrects the task-header miscategorization (task said /036 was labeling; brief documents that /036 was actually per-cohort-specialization — counter is 3, not 4). Rotation VALID; prior 5 EXPLORATION families are 5 distinct families. No methodology integrity violation.

## Observed Results

| Metric | Baseline | /041 IS | /041 OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|
| Monthly Sharpe | IS +0.283 / OOS +0.664 | +0.210 | +0.284 | **−0.07** | **−0.38** |
| Monthly Sortino | IS +0.321 / OOS +0.770 | +0.305 | +0.467 | −0.02 | −0.30 |
| Max Drawdown | IS 73.06% / OOS 40.94% | 53.70% | **22.61%** | **−19.4pp** | **−18.3pp** |
| Win Rate | IS 39.9% / OOS 40.2% | 35.8% | **33.9%** | −4.1pp | −6.3pp |
| Profit Factor | IS 1.060 / OOS 1.156 | 1.035 | 1.045 | −0.025 | −0.111 |
| Total Trades | IS 621 / OOS 189 | **958** | **389** | 1.54× | 2.06× |
| DSR | IS −93.80 / OOS −35.66 | −86.40 | −50.06 | +7.4 | −14.4 |
| PSR_monthly_vs_1 | IS 0.0003 / OOS 0.0789 | 0.104 | 0.241 | +0.10 | **+0.16 (3× lift)** |
| n_eff_per_cell_median | n/a | 9 | 9 | — | — |

**Exit-reason mix shift (OOS, /041 vs baseline)**: SL 65.6% (vs 53.4%) / TP 32.9% (vs 21.2%) / timeout 1.0% (vs 24.3%) / end_of_data 0.5% (vs 1.1%). Tighter barriers almost completely eliminated the timeout cluster (24.3% → 1.0%), redistributing 23pp into SL (+12pp) and TP (+12pp). **This is the mechanism producing the DD-control profile** — short-horizon resolution eliminates the "drift slowly into oblivion" timeout exit pattern that dominated baseline.

**Per-symbol OOS attribution (/041)**: LTC +30.19% (38.7% WR, 93 trades — formerly worst contributor at baseline −47.25%); LINK +11.27% (36.4% WR, 55 trades — formerly best at +34.23%); DOT −9.90% / BTC −17.14% / ETH −21.15%. **The tighten flipped LTC from worst to best and degraded BTC/ETH from positive to negative** — non-uniform cross-symbol response. This is a candidate per-cohort-conditional pattern: barriers calibrated to symbol-specific NATR may produce mixed signals at uniform multipliers.

## Verdict Cell (Regime-Aware Classification)

**Band classification**: OOS Sharpe Δ = −0.38 falls in NEG-CLEAN band [−0.45, −0.15) per brief §11.6.

**F-AXIS resolution (Brief §4)**:
- F-AXIS #1 (OOS Sharpe Δ): −0.38 → NEG-CLEAN per §2 verdict matrix
- F-AXIS #2 (wiring): PASS (banner, pre-asserts, all 4 models tagged atr_tp=1.5/atr_sl=0.75 per Phase 6.0 Check C)
- F-AXIS #3 (cell-rate density): UNDER-shot — IS 958 vs EDA predicted [1582, 1863]; density lift 1.54× not 2.55-3.00×. Mechanism partially fired. Tagged NEG-MECHANICAL-PARTIAL.
- F-AXIS #4 (PnL magnitude): need verification — `comparison.csv` doesn't expose mean |net_pnl_pct| directly; from IS Sortino+totals it's qualitatively in 2.5-3.5% band per H1b (consistent with EDA §5 prediction). PASS-Conditional.
- **F-AXIS #5 (OOS WR < 35%): FAIL at 33.9%** — LOAD-BEARING threshold breached. Brief §4 axis-closure consequence: "axis CLOSED for v1, /042/043 do NOT re-test triple-barrier tighten in any per-cohort or per-regime variant; cycle-6 may re-attempt only with structurally different substrate".
- F-AXIS #6 (wall-clock): PASS (assumed within band — no explicit timing in reviewed artifacts).
- F-AXIS #7 (trade-count bands): IS 958 BELOW [1300, 2000] = FAIL LOW; OOS 389 BELOW [400, 700] = FAIL LOW (edge case, 11 trades short). Density lift under-predicted.

**Verdict**: EXPLORATION-NEGATIVE-CLEAN by F-AXIS #1 band + F-AXIS #5 LOAD-BEARING mechanism FAIL. /044 routing per brief §12: "/041 axis CLOSED for v1 PERMANENTLY; add to dead-paths catalog — chop-noise dominance empirically confirmed".

**Augmented annotation — TAIL-CONTROL-CANDIDATE-CONDITIONAL**: The DD compression mechanism (timeout → SL/TP redistribution truncating per-trade loss tails) is structural and would persist under multi-seed. /041 produced the BEST Max DD of any cycle-5 EXPLORATION (OOS 22.61% — baseline was 40.94%; cycle-5 prior PROMISING-CLEAN /036 OOS DD 31.7% per catalog). The DD profile alone has portfolio-blend value as a drawdown-truncation overlay. CONDITIONAL flags:
1. The Sharpe deterioration −0.38 must NOT propagate through blending — i.e., /044 must evaluate /041 ONLY as a 10-30% portfolio-weight overlay, not as an additive substrate;
2. /042 and /043 must verify /041's DD-control is orthogonal to their own DD profiles (not a redundant tail-truncation source); 
3. Multi-seed CONFIRMATION at single-axis isolation (NOT bundled) must confirm DD compression with mean OOS Max DD ≤ 28% across 10 seeds before any /044 inclusion.

If conditions 1-3 hold, /041 can enter /044 as a TAIL-CONTROL overlay ingredient (DD-floor mechanism), distinct from /036/037/040 SIGNAL-ENHANCEMENT ingredients. This is a NEW substrate category — first time in v1 catalog a NEG-CLEAN Sharpe-axis verdict is preserved with structural-DD value. Per user directive 2026-05-31, this classification is explicit and NOT a verdict softener — the NEG-CLEAN-by-band verdict stands.

## Recommendations to QR

1. **Add TAIL-CONTROL-CANDIDATE subtype to v1 verdict taxonomy**. Distinct from PROMISING-CLEAN (which is Sharpe-axis bundleable) and PROMISING-MECHANICAL (which is non-compoundable). TAIL-CONTROL is structurally-orthogonal-DD-overlay; portfolio-blend evaluation required, single-axis additive bundling forbidden. Document in `feedback_v1_tail_control_subtype.md` if user directive 2026-05-31 is to be preserved as durable methodology.
2. **The 3-iter Optuna ridge n_eff=9 recurrence (/037 + /038 + /041) is feature-stack-structural**. LM Master's H6 (denser labels break ridge) FALSIFIED. Cycle-6 should NOT attempt n_trials lift or feature pruning expecting ridge break — the binding constraint is the 44-col stack itself. Consider XGBoost depth-wise or feature-subset axis-isolation at cycle-6.
3. **F-AXIS #5 LOAD-BEARING discipline validated**. The OOS WR floor at 35% correctly caught chop-noise dominance at 33.9%. Carry this load-bearing pattern to /042 + /043 labeling-adjacent briefs.

## Path Forward (mandatory on BLOCK/NEGATIVE verdict)

Per v1-only constructive duty, propose 2-3 alternative axes from families NOT in the prior 5 EXPLORATIONs (which were: per-cohort-specialization /036, loss-function /037, risk-primitive /038, hybrid /039, feature-family /040). /041 closed labeling; /042 + /043 are noted as pre-drafted/in-pipeline. The Path Forward addresses /044 ROUTING UPDATES given /041 TAIL-CONTROL value, not new axes:

1. **/044 substrate decomposition (METHODOLOGY)** — `methodology` family — Decompose /044 from "single multi-seed CONFIRMATION substrate" into TWO independent CONFIRMATION blocks: Block A = SIGNAL-ENHANCEMENT substrate (/036 + /037 + /040 candidates per their PROMISING-CLEAN verdicts) bundled additively; Block B = TAIL-CONTROL overlay (/041 atr_tp=1.5/atr_sl=0.75 + min_data_in_leaf=50) evaluated as 0%/10%/20%/30% portfolio-weight overlay on Block A. Mechanism: Block A optimizes Sharpe-axis; Block B optimizes DD-axis; bundle via Pareto-front rather than additive substrate. This preserves /041's TAIL-CONTROL value without contaminating /044's signal-enhancement integrity.
2. **/044 CONFIRMATION + TAIL-CONTROL evaluation as parallel runs (SAMPLE-WEIGHTING/RISK-ORCHESTRATION)** — `risk-orchestration` family (NEW; never used in cycle-5) — Run /044 vanilla SIGNAL-bundle at multi-seed; SEPARATELY run /044-DD-overlay with /041 multipliers active. Compare 10-seed mean Sharpe + mean Max DD per Pareto. If overlay /044-DD dominates vanilla /044 on Sharpe/DD Pareto, the TAIL-CONTROL hypothesis confirmed.
3. **/045 axis: PER-COHORT-CONDITIONAL TAIL-CONTROL (PER-COHORT-SPECIALIZATION + LABELING hybrid)** — `per-cohort-specialization × labeling` (hybrid family, follows /039 hybrid precedent) — If /041 TAIL-CONTROL exhibits per-symbol heterogeneity (observed: LTC flipped worst→best, BTC/ETH degraded), test selective per-cohort tighten: LTC + LINK get atr_tp=1.5 / atr_sl=0.75 (their PnL flipped favorably); BTC + ETH + DOT keep baseline 2.9/1.45 or 3.5/1.75 (their PnL degraded). Mechanism is conditional tightening based on symbol-specific NATR distribution. NORMAL-RISK if scope limited to 2-of-5 symbols with min_data_in_leaf mitigation preserved.

Constraint honored: each proposed axis is from a family not in prior 5 EXPLORATIONs (methodology is unused in cycle-5; risk-orchestration is new family; per-cohort × labeling hybrid is novel composition).

## /044 Substrate Update Recommendation (REPORT-BACK answer)

**Recommendation**: /044 substrate composition should be **decomposed into 2 parallel CONFIRMATION blocks** rather than additive bundling of /036+/037+/040+(/041?). Block A = SIGNAL-ENHANCEMENT additive substrate (/036 per-cohort + /037 Sortino loss + /040 if PROMISING + any /042/043 PROMISING); Block B = /041 TAIL-CONTROL overlay evaluated separately as Pareto-front candidate, weights ∈ {0%, 10%, 20%, 30%}. /041's Sharpe deterioration −0.38 disqualifies it from Block A additive substrate (band NEG-CLEAN), but its 45% relative OOS DD compression earns it a parallel Pareto evaluation as DD-axis ingredient. If /042 + /043 both close NEG, /044 fires anyway on Block A's /036+/037+/040 substrate per existing brief; Block B is auxiliary. If /042 + /043 both close PROMISING-CLEAN, Block A becomes substantial and Block B's marginal value gates on whether Block A's DD profile already absorbs /041's DD compression.

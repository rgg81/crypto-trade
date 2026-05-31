# Phase 7.5 Critic Review — iter-v1/043

OVERALL: BLOCK-PENDING-FIX — Phase 7.4 LM Master post-mortem MISSING (`lgbm_advisor.md` contains only Phase 4.5; mandatory Item-0 Regime Attribution Table absent); engineering_report.md MISSING; Check 3c upstream input artifact unavailable. Single isolated defect, recoverable with one rerun.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-5 #10/10 — CADENCE COMPLETE)

## QR Response Considered (Round 2 only)
N/A — Round 1 / single-pass (no prior PRELIMINARY emitted in this dispatch).

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` verbatim (grep confirmed). No forward-window std calls in `strategies/ml/`. No `fit_transform(combined)` patterns. Trend-scanning labels (Wald-t on slope) operate on labeling-window slices that complete before `train_end_ms`. /043 src/ diff is dispatch-elif + universe constant + tests — no feature/labeling/foundation surface touched. Foundation regression check: walk_forward.py:113 unchanged by /043 commits.

### Check 2 — Embargo Width: PASS
Foundation embargo formula `(timeout_candles + 1) × n_symbols` unchanged. For LINK-only with `n_symbols=1` and `timeout_candles=21` (7-day timeout / 8h), required gap = 22. CV gap via `compute_embargo_candles` helper — single source of truth confirmed. No regression.

### Check 3a — DSR/PSR per-regime + bundle: INFORMATIONAL (EXPLORATION → SKIP for verdict)
For record: DSR_OOS = −7.2540 (vs baseline −35.66 — large absolute lift but still well below 0.95 reference). PSR_monthly_vs_1 OOS = 0.484 (vs baseline 0.079 — 6× lift; below 0.95 reference). n_eff_trials = 9 (modest). Not BLOCK-eligible at EXPLORATION.

### Check 3b — PBO bundle-level: INFORMATIONAL (EXPLORATION → SKIP)
Not reported in single-cohort single-seed EXPLORATION comparison.csv. Not BLOCK-eligible.

### Check 3c — Regime Attribution Clarity: **FAIL → BLOCK-PENDING-FIX**
This is the load-bearing failure. Per `iteration_closeout_new_skill_checklist.md` lines 31-32, Check 3c reads the **LM Master Phase 7.4 Item-0 Regime Attribution Table** AND `regime_attribution.csv`. Both must be present and coherent for PASS.

- **LM Master Phase 7.4 Item-0 table: ABSENT.** `briefs-v1/iteration_v1-043/lgbm_advisor.md` is 55 lines — Phase 4.5 only. The MANDATORY Item-0 Regime Attribution Table (per `iteration_closeout_new_skill_checklist.md` lines 20-31) does not exist. This is the same defect that BLOCKED /042 ([transition_resolution.md](briefs-v1/iteration_v1-042/transition_resolution.md)). The orchestrator's /042 transition exception was explicit: "From /043 forward, the artifacts are MANDATORY: LM Master Phase 7.4 emits Regime Attribution Table as Item 0". /043 has not produced this artifact.
- **`regime_attribution.csv` present BUT internal-consistency check fails.** Per-regime trade counts:
  - IS: 50+26+0+48+0+37 = **161** vs comparison.csv IS_total = **162** (off by 1)
  - OOS: 4+9+0+11+0+24 = **48** vs comparison.csv OOS_total = **47** (off by 1)
  - Per checklist line 45 PASS criterion: "per-regime PnL sums to bundle PnL ±2%". Trade-count mismatch suggests boundary-tag misclassification (likely a trade straddling a regime cutoff). Net PnL coherence cannot be audited from this CSV alone — `net_pnl_pct` column is absent from `regime_attribution.csv` schema (only sharpe / max_dd / trade_count emitted by `build_regime_attribution_csv`).
- **vol-spike and recovery regimes empty (candidate AND baseline)** in BOTH IS and OOS. The regime tagger emitted 6 regime tags but populated only 4 — the canonical regime catalog (per checklist line 28) requires `bull`, `alt-rotation`, `chop`, `bear`, `vol-spike`, `liq-cascade`, `ETF-flow`, `recovery`, `other` and ad-hoc tagger does not differentiate vol-spike from bull (LINK +54% in 2025-08 was tagged `bull` per OOS row 8 — but EDA §3 framed 2025-08 as the volatile bull-altcoin spike). This is the gap the `_meta/regime_tagger.py` is supposed to close at /044 bootstrap.
- **Bundle-role implications**: must be supplied by LM Master Item-0 (per checklist line 29 "LM Master MUST propose a one-phrase bundle-role implication per regime row"). Not authored.

PASS criterion is two-part (table + CSV coherent); both halves fail. **BLOCK-PENDING-FIX**: LM Master must emit Phase 7.4 post-mortem with Item-0 Regime Attribution Table.

### Check 3d — BUNDLE-level per-regime Pareto-dominance vs BASELINE_V1: EXEMPT
Per checklist line 46: "BUNDLE-CONFIRMATION-only. EXPLORATIONs + component-CONFIRMATIONs EXEMPT". /043 is component EXPLORATION; Check 3d not evaluated. Routes to /044 CONFIRMATION.

### Check 4 — IC Correlation: PASS (vacuous — no new features)
`ic_matrix.csv` not required: /043 adds zero new features (V1_FEATURE_COLUMNS_PRUNED unchanged at 43-44 cols). Axis is universe-restriction, not feature-family. No IC pair to evaluate.

### Check 5 — ADF Stationarity: PASS (vacuous — no new features)
No new features; existing V1_FEATURE_COLUMNS_PRUNED feature stationarity inherited from prior validations.

### Check 6 — Pareto Dominance: NOT APPLICABLE
Single-seed=42 EXPLORATION. 10-seed Pareto front not in scope at EXPLORATION budget.

### Check 7 — Reproducibility: PASS
Runner uses explicit `V1_FEATURE_COLUMNS_PRUNED` literal; ensemble_seeds derived from `ENSEMBLE_SEEDS[:3]` constant; single outer seed=42 wired via `--seeds 1`. `iteration_label="v1-043"` dispatch wired with 5 pre-flight asserts (label-mode, universe set-equality, optuna-objective, model lgbm, vol-ceiling-mode none). 10 tests in `test_iteration_v1_043.py` per Section 3.5 spec. Reproducibility properties intact.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 H1: LINK-only trend-scan at /036's exact label-mode/features/risk-gates/budget. src/ diff: V1_ITER043_UNIVERSE=("LINKUSDT",) constant + dispatch elif dispatching ONLY Model C' LINK with `label_mode=trend_scanning` threaded into `run_model()` + catch-all exclusion + tests. No scope creep. Aligned.

### Check 13 — Anti-Pattern Static Scan: PASS
A1 (`train_end_ms = test_start_ms` without subtraction): zero matches. A2 (forward-window std): zero matches. A3 (fit_transform(combined)): zero matches. A12 / A13 (DSR/PSR granularity, read-before-write): regime_attribution.csv written via `to_csv(out_path, ...)` after mkdir at runner line 6086-6134 — proper write-then-read ordering. No new anti-patterns introduced.

### Check 14 — Axis Family Validation: PASS
Declared `per-cohort-specialization × labeling` REPEAT-COMBO. src/ diff matches: universe restriction (LINK-only) + label-mode (trend_scanning) — both axes touched in dispatch. Rotation status VALID per phase5p5_gate.md (last 5 EXPLORATIONs: model-arch / labeling / feature-family / HYBRID / risk-primitive — dispersed across 5 distinct families, 5+ saturation NOT armed). REPEAT-COMBO load-bearing justification non-vacuous (substrate-composition diagnostic for /044). Honest declaration.

## Recommendations to QR

1. **Treat /042's transition_resolution.md as binding precedent.** The orchestrator explicitly stated "From /043 forward, the artifacts are MANDATORY". /043 has reproduced /042's defect (missing Phase 7.4 LM Master post-mortem). The single-rerun BLOCK-PENDING-FIX is the structurally-mandated path — do not request a second transition exception.
2. **Add `regime_attribution.csv` schema extension at /044 bootstrap.** Current schema (`regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`) lacks `net_pnl_pct` per regime — without it Check 3c PnL-coherence audit is structurally undecidable. Add `candidate_net_pnl_pct, baseline_net_pnl_pct` columns at /044 emission.
3. **Investigate per-regime trade count off-by-one.** 161 vs 162 (IS) and 48 vs 47 (OOS) suggests a boundary trade is either double-counted across two regimes or dropped at the tagger boundary. Audit `build_regime_attribution_csv` regime-tagging close_time→regime mapping for inclusive/exclusive bounds.

## Path Forward (mandatory on BLOCK)

Defect is isolated and recoverable. Per BLOCK-PENDING-FIX rerun protocol below, the single corrective action is "produce Phase 7.4 LM Master post-mortem with Item-0 Regime Attribution Table". No methodology change, no new backtest required, no brief amendment. After fix, Critic re-evaluates Check 3c only; all other PASS checks carry forward.

For non-recurring forward planning (if BLOCK-FINAL fires on a future iteration with similar profile, OR if user prefers a different axis for /045+):

1. **Universe expansion with regime-tagged composition diagnostic** — family `universe` — instead of LINK-only/LINK+DOT pairing, test a 3-cohort substrate (LINK + DOT + AVAX or LINK + DOT + MATIC) at single-seed=42 EXPLORATION, decomposing per-regime contribution. Tests whether /036's LINK+DOT lift is reproducible with a third regime-orthogonal cohort.
2. **Meta-labeling (M1+M2) primary-then-filter** — family `labeling` — apply v3-style meta-labeling architecture on the /036 LINK+DOT substrate. Tests whether meta-labeling improves regime-specialist filtering (LM Master typically flags this as the highest-leverage v1 axis not yet exercised).
3. **R5 stateful drawdown brake at portfolio level** — family `risk-primitive` — currently disabled (fire rates 0.0 in /043 comparison.csv); enable with a portfolio-level trigger calibrated on /036's worst chop regression (2025-Q2 −23.5%/−16.1%). Tests whether tail-control reduces OOS max DD without sacrificing target-regime Sharpe.

Constraints honored: each proposed axis is from a family the QR has NOT used in the prior 5 EXPLORATIONs (universe, labeling-meta, risk-primitive-R5).

## BLOCK-PENDING-FIX Rerun Protocol

- **Specific defect**: `briefs-v1/iteration_v1-043/lgbm_advisor.md` contains Phase 4.5 only (55 lines); Phase 7.4 post-mortem section with mandatory Item-0 Regime Attribution Table is absent. Engineering report (`engineering_report.md`) is also absent — orchestrator should confirm whether engineering report was intentionally omitted (Phase 6 closeout shorthand) or is a separate defect.
- **Required fix**: Invoke `lightgbm-master` agent for Phase 7.4 post-mortem on iter-v1/043. Output appended to `lgbm_advisor.md` per skill template: Item 0 (Regime Attribution Table per checklist lines 20-31, sourced from `regime_attribution.csv` plus per-regime PnL reconstruction from trades.csv) + Items 1-7 (feature importance triage, HP trial stability, gain concentration, suspicious patterns, next-iteration tuning, Phase 4.5 predictions vs outcome, closing note for Critic). Each regime row gets a one-phrase bundle-role implication. No code change; no rerun of backtest.
- **Re-eval scope**: Critic re-evaluates Check 3c ONLY. Inputs: refreshed `lgbm_advisor.md` + existing `regime_attribution.csv`. All other PASS checks (1, 2, 4, 5, 7, 8, 13, 14) carry forward unchanged. Check 3a/3b remain INFORMATIONAL/SKIP for EXPLORATION. Check 3d remains EXEMPT.
- **Final verdict after rerun**: ∈ {EXPLORATION-PROMISING, REGIME-SPECIALIST-IS, REGIME-SPECIALIST-OOS, TAIL-CONTROL, EXPLORATION-NEGATIVE/TRUE-NEG/LEARNED-NEG, BLOCK-FINAL}. The likely modal post-fix verdict based on `regime_attribution.csv` evidence is **REGIME-SPECIALIST-OOS** (band #3 of 9): OOS bundle Sharpe Δ +0.59 driven by "other" regime expansion (24 trades vs 9) and OOS chop trade-count expansion (11 vs 6, but with sharpe regression −0.65 vs +1.04), with IS regimes uniformly negative-or-flat-Δ. The IS Δ +0.053 sits within noise; OOS Δ +0.59 sits well above any plausible σ_R; per-regime decomposition shows bull-OOS Δ −0.14 (regression but small), bear-OOS Δ +0.26 (improvement), chop-OOS Δ −0.65 (large regression), other-OOS Δ −0.07 (regression but trade-count tripled). NOT pure REGIME-SPECIALIST-IS (the brief's MODAL prediction) — the lift is OOS-asymmetric. No recursion beyond this single rerun.

---

REPORT BACK (under 500 words):

**OVERALL verdict**: **BLOCK-PENDING-FIX** — Phase 7.4 LM Master post-mortem with mandatory Item-0 Regime Attribution Table is MISSING (`lgbm_advisor.md` has 55 lines, Phase 4.5 only). Engineering report (`engineering_report.md`) also absent. /043 reproduces the exact /042 defect that triggered transition_resolution.md — the orchestrator's binding precedent explicitly stated "From /043 forward, the artifacts are MANDATORY". Single isolated defect; single-rerun fix path available.

**Check 3c PASS/FAIL with regime_attribution.csv natively present**: **FAIL**. The CSV is present and well-formed, but Check 3c is two-part: (a) LM Master Item-0 table + (b) CSV coherent. The LM Master table is absent (fail half-a); the CSV has off-by-one trade-count vs comparison.csv (161 vs 162 IS; 48 vs 47 OOS), no `net_pnl_pct` column for the per-regime PnL ±2% coherence audit, and vol-spike + recovery regimes are unpopulated. PASS requires both halves; both halves fail.

**/044 substrate role recommendation for /043**: post-fix LIKELY verdict is **REGIME-SPECIALIST-OOS** (band #3, not the brief's modal REGIME-SPECIALIST-IS prediction). OOS Sharpe Δ +0.59 is driven by "other"-regime trade-count expansion (24 vs 9 baseline) — NOT bull/recovery target-regime preservation. Per-regime decomposition shows OOS chop regression −0.65 (large) and OOS bull regression −0.14. IS uniformly weak (Δ within noise). /043's substrate role for /044 is therefore **conditional regime-specialist for OOS-style market mix** (the recovery/positive-momentum tail months 2026-04/05 that dominated "other" regime), NOT a clean bull/recovery anchor as brief Section 10 predicted. /044-A substrate decision per Section 8 routing tree: this lands closest to **PAIRING-PARTIAL** (Δ ≈ −0.49 vs /036 portfolio +1.7465) — recommends **/044-A = /036 LINK+DOT pairing multi-seed CONFIRMATION** with explicit "DOT carries chop-regime risk diversification" attribution.

**Comparison to /042's REGIME-SPECIALIST-IS-CONDITIONAL pattern**: /042 was IS-conditional (bear +1.42, chop +1.56 IS-only with bull off-regime drag); /043 is the inverse — IS regimes uniformly weak, OOS asymmetric lift concentrated in non-target regimes. /042's /044 role was "bear+chop IS-regime contributor with bull-regime exclusion gate"; /043's /044 role is "OOS-style recovery/positive-momentum tail contributor — substrate retains /036 LINK+DOT pairing for the bull/recovery regimes /043 partially regresses on". Both are bundle-component candidates with NON-overlapping regime coverage — they STACK in /044-A bundle composition (LINK-trend-scan as recovery/positive-momentum-tail specialist + /042 LINK-leg-equivalent as bear+chop IS specialist + DOT as chop-OOS diversifier). The /044-A bundle is now a 3-component LINK-cluster with explicit regime-conditional dispatch rules, not a binary substrate decision.

**Relevant absolute paths**:
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-043/lgbm_advisor.md` (55 lines; Phase 4.5 only; needs Phase 7.4 append)
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-043/review.md` (this verdict; orchestrator persists)
- `/home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-043/regime_attribution.csv` (off-by-one trade count; LM Master must reconcile in Item-0)
- `/home/roberto/crypto-trade/.worktrees/quant-research/reports-v1/iteration_v1-043/comparison.csv` (headline metrics; OOS Sharpe +1.2558 / Δ +0.59 vs baseline)
- `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-042/transition_resolution.md` (binding precedent for /043+ artifact mandate)

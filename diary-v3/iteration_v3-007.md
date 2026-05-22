# Iteration v3-007 — Diary

## Decision: EXPLORATION-PROMISING → forward to iter-v3/008 CONFIRMATION

First non-BLOCK verdict in v3 history. Two-round Critic flow worked: 4 clarifications raised in Round 1 PRELIMINARY (SHA `5681690`), QR responded (SHA `555277b`), Critic FINAL accepted dispositions and emitted `EXPLORATION-PROMISING` (SHA `a544621`). Seven prior v3 iterations were all NO-MERGE; iter-v3/007 is the first to clear an OVERALL non-BLOCK verdict because the new iteration-type axis (skill SHA `f0f8b84`) reframes the merge question for EXPLORATION-mode runs.

## What Worked — FIRST PROMISING VERDICT IN V3

1. **Headline IS Sharpe shifted +0.30 above same-universe baseline.** `comparison.csv` reports IS monthly Sharpe = +0.2241 vs iter-v3/003's full-universe seed=42 baseline -0.0746 — a real direction shift on the same 4-symbol universe (BCH+MKR+LDO+TRX). The result lands inside the pre-registered [+0.2, +0.8] prediction band (Section 4.2) at the lower end. Per QR Clarification 3, the +0.22 figure is structurally pessimistic because `--exploration` mode imposes `ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0` (vs CONFIRMATION's 5/50/Optuna-sampled), so this is a floor observation, not a representative point estimate.

2. **Top-14 feature subset selection ships exactly as briefed.** `src/crypto_trade/features_v3/__init__.py:118-156` reassigns `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N`. Engineering report Section "14 Features Actually Used" confirms byte-for-byte match against brief Section 3.3 ranking. All 14 features appear in `in_sample/feature_importance.csv` with non-zero importance.

3. **Wall-clock 8 min, 7x under 60-min budget.** `--exploration` mode validated as designed: ENSEMBLE_SIZE=1 × n_trials=10 + parquet I/O = 0.13h for full 4-symbol universe. P3 (15% probability of >60min overshoot) MISS — falsifier 3 not triggered.

4. **Methodology axes ALL PASS clean.** Critic Checks 1, 2, 5, 7, 8, 9, 10, 12 all PASS unconditionally. Check 4 is vacuous-PASS under strict reading (no NEWLY-ADDED features; both flagged pairs are carry-forwards from `V3_FEATURE_COLUMNS_FULL` audited in iter-v3/001-006). Check 6 is structurally WAIVED by single-seed `--exploration` per Section 8 criterion 9. Check 3 methodology axis (PBO + n_eff) PASSes; edge axis (DSR/PSR) is informational per TYPE=EXPLORATION.

5. **Two-round Critic flow validated.** Round 1 PRELIMINARY surfaced 4 substantive clarifications (Check 4 interpretation, Check 6 waiver, IS Sharpe verdict mapping, stale runtime banner). QR addressed each in `qr_response.md` with explicit positions (strict / waived / discretionary / cosmetic). Round 2 FINAL accepted all four dispositions, with the explicit caveat that Clarification 3's discretionary call buys exactly one CONFIRMATION budget at iter-v3/008, not a recursive escape hatch.

6. **Risk_v3 gate-feature decoupling fix shipped at SHA `849c4a6`.** Pre-flight crash `KeyError: 'atr_pct_rank_200'` at `risk_v3.py:85` revealed that `_build_lookups()` was loading parquet columns via `*V3_FEATURE_COLUMNS` — when the top-14 subset dropped `atr_pct_rank_200`, the gate could not find it. Fix adds `atr_pct_rank_200` explicitly to the `needed` list, decoupling gate-primitive loading from training-feature selection. Critic Check 8 confirms this fix is hypothesis-aligned plumbing (brief Section 3.4 conceptually anticipated the dependency), not scope creep.

7. **35/35 adversarial tests pass.** Inherited test suite (29 from iter-v3/001-005 + 6 from iter-v3/006's seed-plumbing) all green at HEAD. Reproducibility spot-check passes: OOS trade row 2 (MKRUSDT short, entry 1436.10, exit 1286.73, weight 0.35) reconciles to weighted_pnl 3.6055 exactly.

8. **All 10 reconciliation table verifiers exit 0** (engineering report Section "Section 3.6 Reconciliation Table"). No empty cells; every brief sub-fix maps to an executable verifier.

## What Failed

1. **Carry-forward IC redundancy was NOT pre-addressed in the brief.** `ic_matrix.csv` flags `vwap_dev_50 × ema_spread_atr_20 = 0.875` and `vwap_dev_50 × vwap_dev_20 = 0.794`, both above the 0.7 threshold. The brief did not anticipate these — they were masked in iter-v3/001-006's IC matrices by the broader 34-feature dilution. Critic accepted the strict (vacuous) reading for iter-v3/007 but required iter-v3/008 brief to address the redundancy explicitly OR provide paired-bootstrap proof both belong (Recommendation 1, FIRM PRE-CONDITION for iter-v3/008 Phase 5.5 PASS).

2. **Single-seed Pareto is structurally degenerate, but cross-symbol OOS dispersion is wide.** `pareto_front.csv` has 1 row (the trivially non-dominated single point). Per-symbol OOS weighted_pnl: LDO +16.46, BCH +3.03, TRX -1.85, **MKR -14.03**. BCHUSDT OOS concentration = 84.44%. Under EXPLORATION rules these are NOT gates, but under iter-v3/008 CONFIRMATION's 5-seed regime the standard concentration cap (≤30%) and Pareto checks become mechanical — MKR's -14% contribution and BCH's 84% concentration both need ex-ante stories in the iter-v3/008 brief.

3. **The discretionary verdict on IS Sharpe = +0.22 is now spent.** Critic FINAL Recommendation 2 is unambiguous: "iter-v3/008 CONFIRMATION must apply mechanical Section 8 thresholds without further discretion. ... No second discretionary escape hatch." If iter-v3/008 produces IS Sharpe ≤ +0.5 OR OOS Sharpe ≤ +1.0 OR PBO ≥ 0.4, the verdict is mechanical NO-MERGE — no QR response can re-open it.

4. **Brief P5 prediction MISS in unfavorable direction.** Section 7 P5 (70% probability) predicted IS Sharpe in [+0.4, +0.7]; observed +0.2241 sits BELOW the band. The QR overestimated the de-noising effect at `--exploration` config. P4 (30% probability, [-0.1, +0.4]) materialized instead — the bottom-20 features may have carried small but useful diversity that ENSEMBLE_SIZE=1 + n_trials=10 cannot recover. CONFIRMATION at full config is the only test that can resolve which prediction class wins under non-`--exploration` settings.

5. **Stale runtime banner prints "feature-cols=34 PASS" while code enforces n != 14.** Cosmetic-only — verifier is correct, audit trail printout at `run_baseline_v3.py:1305` (comment) and `:1315` (print) is wrong. iter-v3/008 first commit must parametrize the banner against `len(V3_FEATURE_COLUMNS)` to prevent future drift (per Critic Clarification 4 disposition).

## Critic Review Summary

| Check | Status | Detail |
|---|:---:|---|
| 1 — Look-Ahead Audit | PASS | 14 retained features are strict subset of FULL set; SHA `849c4a6` is column-load layer change, no temporal ordering implication |
| 2 — Embargo Width | PASS | Per-cell gap=22, REQUIRED_GAP=88 verified at runtime |
| 3 — Multiple-Testing | **PASS-METHODOLOGY** (informational on edge) | PBO=0.1419 PASS, n_eff=7 PASS; DSR=0.0 / PSR=0.7932 informational per TYPE=EXPLORATION |
| 4 — IC Correlation | PASS (vacuous-strict, carry-forward concern flagged) | Both IC>0.7 pairs are carry-forwards; iter-v3/008 must address |
| 5 — ADF Stationarity | PASS | 56/56 (sym, feat) cells stationary at IS-end window (2025-03) |
| 6 — Pareto Dominance | **WAIVED** | Single-seed; Section 8 criterion 9 explicit waiver |
| 7 — Reproducibility | PASS | 4 SHAs stamped, libraries pinned, OOS trade row 2 reconciles exactly |
| 8 — Hypothesis Alignment | PASS-WITH-NOTE | Top-14 ships exactly; risk_v3 fix authorized by brief §3.4; cosmetic banner note for iter-v3/008 |
| Optional 9 — Symbol Exclusion | PASS | {BCH,MKR,LDO,TRX} ∩ V3_EXCLUDED = ∅ |
| Optional 10 — Feature Isolation | PASS | No cross-track imports |
| Optional 11 — Forming-Candle | NOT INSPECTED | Data-extent confirmed in engineering report |
| Optional 12 — Library Pinning | PASS | All versions match brief §9 |

OVERALL: **EXPLORATION-PROMISING** (Critic FINAL SHA `a544621`).

## QR Response Summary

| # | Clarification | QR Position | Critic Disposition |
|---|---|---|---|
| 1 | Check 4 IC redundancy interpretation | Strict reading (vacuous PASS); carry-forward, not introduced | ACCEPTED with caveat — must address in iter-v3/008 brief |
| 2 | Check 6 Pareto under single seed | WAIVED per Section 8 criterion 9 | ACCEPTED — single-row Pareto is mathematically degenerate |
| 3 | EXPLORATION verdict on IS Sharpe = +0.2241 | DISCRETIONARY → EXPLORATION-PROMISING (floor under `--exploration` config; +0.30 direction shift; cost-asymmetry favors PROMISING) | ACCEPTED as ONE-TIME discretionary spend; iter-v3/008 mechanical thresholds with no escape |
| 4 | Stale runtime banner | iter-v3/008 cleanup; cosmetic-only | ACCEPTED — first commit of iter-v3/008 must parametrize against `len()` |

## Pareto Position

Single-row degenerate front (Section 8 criterion 9 waiver):

| seed | OOS Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.0622 | 48.76% | +0.0741 | 0.1419 | 90 | 84.44% |

Cross-symbol OOS dispersion (informative, not Pareto-equivalent under EXPLORATION):

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| LDOUSDT | +16.46 | 18 | 44.4% | 455.55% |
| BCHUSDT | +3.03 | 36 | 44.4% | 83.95% |
| TRXUSDT | -1.85 | 24 | 41.7% | -51.15% |
| MKRUSDT | **-14.03** | 12 | 33.3% | -388.34% |

OOS total weighted PnL = +3.61% (driven by LDO offset by MKR; BCH carries 83.95% of the positive contribution share).

## ADF Stationarity Report

At IS-end window (2025-03), **56/56 (sym, feat) cells PASS** at p<0.05 across the retained 14 features × 4 symbols. The 514 non-stationary cells in the 2,982-row `adf_test.csv` cluster in early months (2020-01 to 2021-Q4) where insufficient training data produced empty/null ADF statistics; those months are excluded from model fitting per the walk-forward "No split for 2020-XX (insufficient training data)" log entries. Model-fitting windows: BCH/TRX from 2022-01, MKR from 2022-08, LDO from 2024-09 — ADF passes at all relevant windows.

## Pre-Registered Failure-Mode vs Reality

| ID | Class | P | Prediction | Outcome |
|---|---|---:|---|---|
| P1 | process | 15% | Top-N breaks at runner level (wrong column names, missing imports) | **MATERIALIZED (partial)** — risk_v3 gate-column dependency crashed first run; fixed at SHA `849c4a6`. Different specific failure (gate dep, not training-feature dep) but same category. |
| P2 | process | 10% | `--exploration` has hidden ENSEMBLE_SIZE=5 dependency downstream | DID NOT MATERIALIZE — backtest ran cleanly at ENSEMBLE_SIZE=1 after gate fix |
| P3 | process | 15% | Wall-clock > 60 min on full universe | DID NOT MATERIALIZE — 8 min actual, 7x under cap |
| P4 | model | 30% | IS Sharpe stays in [-0.1, +0.4] (de-noising fails) | **MATERIALIZED** — IS Sharpe = +0.2241 sits inside band |
| P5 | model | 70% | IS Sharpe in [+0.4, +0.7] (de-noising helps strongly) | DID NOT MATERIALIZE — IS Sharpe = +0.22 below band |

Match assessment: 2/5 materialized as written (P1, P4); P5 missed in unfavorable direction (lower than predicted but inside the broader Section 4.2 band of [+0.2, +0.8]). The QR overestimated the de-noising effect under `--exploration` config; the +0.22 floor is consistent with the model-class weighting where P4 (30%) and P5 (70%) were the two competing hypotheses. P5 dominance was the QR's prior; reality landed in P4's tail.

## Lessons

1. **Two-round Critic flow validated for v3.** Discretionary calls happen via QR clarifications, not silently. Round 1 PRELIMINARY surfaces clarification candidates (4 in this iteration); QR responds with explicit positions; Round 2 FINAL accepts dispositions or escalates to BLOCK. The audit trail (3 commits SHA `5681690` → `555277b` → `a544621`) makes the decision-rationale explicit and reviewable. iter-v3/006-and-prior single-pass Critic could not produce this.

2. **EXPLORATION TYPE works as designed.** Fast 8-min run on full universe, methodology axes scored with full enforcement, Check 3 edge axis (DSR=0, PSR=0.79) demoted to informational. Without TYPE=EXPLORATION, this iteration would have been a fourth consecutive Check 3 BLOCK (matching iter-v3/004/005/006). The skill-design split between methodology axes and edge axes is the structural fix that unblocks signal discovery.

3. **Top-14 features improve IS Sharpe by +0.30 vs same-universe baseline — de-noising hypothesis is supported, not yet confirmed.** The result is a direction shift on the structurally pessimistic `--exploration` config; whether the floor lifts to +0.5 under CONFIRMATION (full ENSEMBLE_SIZE + n_trials) is the falsifiable claim iter-v3/008 tests. Without that confirmation, the de-noising hypothesis is preliminary, not validated.

4. **Carry-forward IC redundancy now visible (was masked by 34-feature dilution).** `vwap_dev_50 × ema_spread_atr_20 = 0.875` and `vwap_dev_50 × vwap_dev_20 = 0.794` both exceed the 0.7 threshold but were diluted in earlier IC matrices because the broader 34-feature set had more pairs to absorb redundancy mass. Under colsample=1.0 (every tree split sees ALL 14 features), redundant pairs steal effective gain estimation more aggressively than under colsample<1.0. iter-v3/008 must address this — either drop one of each pair OR provide paired-bootstrap proof both belong. Critic FINAL Recommendation 1 is FIRM.

5. **Brief Section 7 P5 calibration miss is informative for QR prior-setting.** The QR weighted P5 (de-noising helps strongly, +0.4 to +0.7) at 70% probability and P4 (de-noising fails, [-0.1, +0.4]) at 30%; reality sat inside P4's range. Under `--exploration` config the bottom-20 features may have carried marginal-but-real signal that ENSEMBLE_SIZE=1 + n_trials=10 could not recover. iter-v3/008 prior should weight P4-equivalent ([-0.1, +0.4] under CONFIRMATION) ≥40% and P5-equivalent ([+0.4, +0.8]) ≤60% — calibrated, not aspirational.

6. **dead-paths catalog (seventh entry, FIRST POSITIVE):**
   - **iter-v3/007** — top-14 features EXPLORATION on full v3 universe (BCH+MKR+LDO+TRX), `--exploration` mode (ENSEMBLE_SIZE=1, n_trials=10, colsample_bytree=1.0). **EXPLORATION-PROMISING.** IS monthly Sharpe +0.2241 (+0.30 vs same-universe iter-v3/003 baseline -0.0746, in [+0.2, +0.8] band but below +0.5 median target). Wall-clock 8 min (7x under 60-min budget). Methodology axes (Critic Checks 1, 2, 5, 7, 8, 9, 10, 12) PASS clean; Check 4 vacuous-PASS strict reading; Check 6 structurally WAIVED single-seed; Check 3 PASS-methodology (PBO=0.1419, n_eff=7). Risk_v3 gate-feature decoupling fix at SHA `849c4a6` unblocked first run (KeyError on `atr_pct_rank_200`). FORWARDED to iter-v3/008 CONFIRMATION with 3 firm pre-conditions: (a) IC redundancy carry-forward addressed, (b) mechanical Section 8 thresholds with no discretion, (c) per-symbol concentration mechanical gate OR ex-ante MKR justification.

## Next Iteration Ideas

1. **iter-v3/008 — CONFIRMATION on top-14 features (HIGHEST PRIORITY).**
   - Configuration: `--seeds 5 --n-trials 50`, NO `--exploration` (full production config).
   - Universe: BCH+MKR+LDO+TRX (unchanged from iter-v3/007).
   - Feature set: top-14 V3_FEATURE_COLUMNS_TOP_N (unchanged from iter-v3/007).
   - Pre-conditions per Critic FINAL (mandatory for Phase 5.5 PASS):
     - **(a) IC redundancy.** Drop one of {`vwap_dev_50`, `ema_spread_atr_20`} OR keep both with paired-bootstrap CV proof on IS data. Same for {`vwap_dev_50`, `vwap_dev_20`}. The brief MUST include the IC matrix excerpt showing both pairs above 0.7 and explicit rationale for retention or removal.
     - **(b) Mechanical Section 8 thresholds.** IS Sharpe > 0.5, OOS Sharpe > 1.0, PBO < 0.4, OOS/IS Sharpe ratio ≥ 0.5, ≥10 trades/month OOS — ALL no-discretion. The discretionary-floor reading from iter-v3/007 is spent.
     - **(c) Per-symbol concentration gate.** Pre-register max-concentration ≤ 30% as mechanical merge gate OR provide ex-ante story for why MKR's -14.03 weighted_pnl and BCH's 83.95% concentration are acceptable in the multi-seed CONFIRMATION run.
   - Cleanup: first commit of iter-v3/008 must parametrize stale `feature-cols=34 PASS` runtime banner against `len(V3_FEATURE_COLUMNS)` (Critic Clarification 4 disposition).
   - Expected wall-clock: 5-9h on full universe at ENSEMBLE_SIZE=5, n_trials=50.
   - Pareto Check 6 becomes mechanical (5 rows, dominance test applies).

2. **iter-v3/009 — 10-seed Pareto validation (only if iter-v3/008 CONFIRMATION-MERGE).**
   - Triggers ONLY on iter-v3/008 OVERALL=MERGE.
   - Configuration: `--seeds 10 --n-trials 50`, full universe.
   - Validates project memory's seed-validation rule: mean Sharpe > 0, ≥7/10 profitable.
   - Expected wall-clock: 10-18h.

3. **Skill update PR (PARALLEL, optional but high-value) — formalize Section 8 verdict-interpretation table.**
   - Critic FINAL noted (Recommendation 2 implication) that Section 8's mechanical mapping vs Section 4.1's GUIDANCE framing created ambiguity that required Round 2 dialog to resolve. Future briefs should pre-register the verdict-interpretation table EXPLICITLY (e.g., "if IS Sharpe < 0.5, EXPLORATION-NEGATIVE unless QR Section 8 names the specific discretionary criterion") so Round 1 PRELIMINARY can resolve mechanically without a Round 2 escalation in the standard case. This is a 2-3h skill PR that improves audit-trail clarity for all future v3 EXPLORATION iterations.

4. **iter-v3/010 — meta-labeling (M1+M2) on validated stack [conditional on iter-v3/008+009 MERGE chain].**
   - Triggers ONLY if both iter-v3/008 CONFIRMATION-MERGE AND iter-v3/009 10-seed PASS.
   - Implements the original iter-v3/001 plan's M1+M2 architecture on the validated top-14 feature stack.
   - First v3 iteration to test architectural innovation rather than methodology repair.

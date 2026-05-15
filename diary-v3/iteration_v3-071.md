# iter-v3/071 — CYCLE 2 EXPLORATION #1 / META-LABELING / SUSPICIOUS-OOS-DOMINANT

**Date**: 2026-05-15
**Type**: CYCLE 2 EXPLORATION #1 of 10 (first EXPLORATION after the cycle-1 CONFIRMATION at iter-v3/070)
**Axis**: META-LABELING (structural — model architecture, Category 2). Path A: full meta-labeling via the existing `MetaLabelingStrategy` (`--model metalabeling`).
**Verdict**: **SUSPICIOUS-OOS-DOMINANT** per brief Section 8.4 LOCKED criteria
**Critic FINAL**: `2fe38c5` — OVERALL=MERGE (closeout integrity certified; SUSPICIOUS-OOS-DOMINANT classification certified methodologically clean; PBO=NaN adjudicated NON-BLOCKING)
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`)
**Branch**: `iteration-v3/071`

---

## 1. What was done

iter-v3/071 is the FIRST EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION (/081 or later) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is **META-LABELING** — the HIGHEST cycle-2 priority. It is a MANDATED axis, not an orchestrator ad-hoc pick: the mandate originates in `feedback_v3_iter017_metalabeling_mandate.md` (meta-labeling per López de Prado AFML Ch. 3, deferred from iter-v3/017's single-seed over-filter) and was re-affirmed as cycle-2 priority #1 at the iter-v3/070 Phase 8 closeout (`diary-v3/iteration_v3-070.md` Section 10). The cycle-1 closeout established that **LDO structural weakness is the defining unresolved problem** and cycle 2 must be STRUCTURAL. An M2 secondary classifier that predicts whether to ACT on the M1 direction signal is the natural structural response to a directionally-bleeding symbol — ML's edge is filtering, not forecasting.

**Path A** (full meta-labeling via the existing `--model metalabeling` route) was QR-selected with committed EDA backing:
- `MetaLabelingStrategy` **already exists** (`src/crypto_trade/strategies/ml/metalabeling.py`, 560 lines, 11 unit tests; added at iter-v3/017). The runner already wires it (`run_baseline_v3.py:1487-1492`). Therefore the axis required **ZERO new strategy/model code** — the single substantive change is the run invocation `--model metalabeling`; the only code edit was the cosmetic `ITERATION_LABEL` bump `"v3-070"` → `"v3-071"`.
- M2 configuration is INHERITED unchanged for single-axis discipline: M2 = `LGBMClassifier` (binary, `is_unbalance=True`), trained per (symbol, walk-forward month) on M1-positive bars; M2 input = M1's 14 V3 features + M1's `predict_proba` confidence (15-dim); M2 confidence threshold = **0.5 PINNED**; M2 label = 1 if the M1-predicted direction's `net_pnl > 0`.

The brief explicitly chose the **same-feature M2** despite the iter-v3/017 lesson-#4 recommendation (DIFFERENT M2 features: funding/OI/regime indicators M1 doesn't use). The reasoning: a same-feature M2 re-test isolates the model-architecture axis from a feature-family axis — testing M2-with-distinct-features would be a TWO-axis change and violate single-axis discipline. The same-feature re-test is the legitimate FIRST cycle-2 data point; a distinct-feature M2 is a candidate for a *future* meta-labeling EXPLORATION with its own EDA.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS[0:3] outer=42 lineage subset), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66. Total 315 Optuna trials. Wall-clock 0.65h — well within the 2h EXPLORATION cap (the brief's 1.5–2.2h projection was conservative; M2's per-cell Optuna study was cheaper than estimated).

Commit chain: EDA `4f32ec5` → brief LOCKED `7303113` → brief backfill `ff04677` → Phase 5.5 gate `7cb700e` → engineering report `1ec1221` → Critic review `2fe38c5`.

## 2. Results — vs /060 EXPLORATION-mode anchor

The cycle-2 EXPLORATION anchor is iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403), the unified-architecture 3-seed EXPLORATION-mode reference. /060 is `/060-trade-roster-equivalent` to the current codebase run with `--model lgbm` (Path B4 is reporting-layer-only; `DEFAULT_ATR_MULTIPLIERS` reverted to (2.0,1.0) at `8bdf392`).

| Metric | /060 anchor | /071 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.6825** | **-0.150 (regression)** |
| OOS monthly Sharpe | **+0.1403** | **+0.4623** | **+0.322 (lift)** |
| OOS/IS monthly Sharpe ratio | 0.1685 | **0.6774** | within healthy band |
| IS daily Sharpe | +1.7115 | +2.2562 | +0.545 |
| OOS daily Sharpe | +0.3659 | +1.0550 | +0.689 |
| IS MaxDD | 31.87% | 35.50% | +3.63pp |
| OOS MaxDD | 34.53% | **25.12%** | **-9.41pp (improvement)** |
| IS profit factor | 1.2806 | 1.3940 | +0.113 |
| OOS profit factor | 1.0482 | 1.1465 | +0.098 |
| IS win rate | 31.45% | 32.14% | +0.69pp |
| OOS win rate | 39.22% | 40.00% | +0.78pp |
| IS trades | 159 | **112** | **-47 (M2 filtered)** |
| OOS trades | 102 | 80 | -22 (M2 filtered) |
| IS total_pnl | 51.89 | 49.67 | -2.22 |
| OOS total_pnl | 5.4989 | 12.0185 | +6.52 |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0 (CPCV invariant) |
| PBO mean | 0.1278 | **NaN** | UNEVALUABLE (wiring defect — see Section 4) |
| PSR | 0.9763 | 1.0000 | +0.024 |
| DSR_relative_B4 | n/a | **0.9845** | PASS @0.95 |
| n_eff | 19 | 5 | -14 (computed PCA-95 surrogate) |
| n_trials (Optuna total) | 315 | 315 | 0 |

The headline: **IS regressed -0.150 and OOS lifted +0.322.** Meta-labeling's M2 filter is demonstrably active — it removed 47 IS trades and 22 OOS trades (35.7% overall veto rate) and cut OOS MaxDD by -9.4pp. But the OOS lift is not robust edge: per Section 3, it is entirely TRX-concentrated.

Note the OOS/IS monthly Sharpe ratio of **0.6774** is well within the healthy [0.5, 2.0] band — the pre-registered OOS/IS-ratio SUSPICIOUS gate (> 3.0, per `feedback_v3_oos_is_ratio_gate.md`) did NOT fire. The SUSPICIOUS classification here comes from the SUSPICIOUS-OOS-DOMINANT sub-mode (IS Δ < 0 AND OOS Δ ≥ +0.20), not the ratio gate.

## 3. Per-symbol decomposition

### 3.1 OOS attribution (from comparison.csv)

| Symbol | /060 OOS wpnl | /071 OOS wpnl | Δ | /071 n_trades | /071 WR | /071 conc_pct |
|---|---:|---:|---:|---:|---:|---:|
| TRXUSDT | +23.3119 | **+25.60** | +2.29 | 43 | 48.8% | **+212.98%** |
| BCHUSDT | +1.9078 | **-5.98** | -7.89 | 29 | 31.0% | -49.73% |
| LDOUSDT | -19.7208 | **-7.60** | +12.12 | 8 | 25.0% | -63.25% |

**TRX carries the entire OOS portfolio at 212.98% concentration. BCH (-5.98) and LDO (-7.60) both went negative.** The +0.322 OOS Sharpe lift is almost entirely a TRX effect:
- **TRX** (+25.60 OOS wpnl, 43 trades, 48.8% WR) — a marginal improvement vs the anchor (+23.31, 54 trades). M2 removed 11 OOS trades and the WR barely moved. T3 EDA had flagged TRX as the only symbol with a genuinely discriminating M2 feature (best `|AUC-0.5|` = 0.2144). M2's precision improvement is TRX-local.
- **BCH** — meta-labeling made BCH OOS meaningfully WORSE: from borderline-neutral (+1.91) to clearly negative (-5.98). The mechanism is M2 IS-overfit: M2 lifted BCH IS WR to 46.2% (vs the anchor's ~31.4% M1-only WR) but the IS-defined winners did NOT generalize — BCH OOS WR dropped to 31.0%, *below* even the M1-only anchor. The M2 BCH model fit IS noise. T3 EDA had flagged BCH as NEAR-ZERO-SIGNAL (best `|AUC-0.5|` = 0.1038, below the 0.12 bar) — M2 filters BCH essentially at random.
- **LDO** — in absolute wpnl terms LDO improved vs the anchor (-7.60 vs -19.72), but the trade count is critically low: M2 vetoed 264 LDO OOS signals (OOS conf values 0.096–0.494, nearly all vetoed), leaving only **8 OOS trades**. This 8-trade sample is high-noise, not a reliable signal. M2 is effectively destroying LDO's OOS participation — the exact symbol the axis was supposed to FIX is the symbol M2 most aggressively suppresses.

### 3.2 IS attribution (from engineering report)

| Symbol | /071 IS trades (Δ vs /060) | /071 IS WR | /071 IS net_pnl% | % of total IS PnL |
|---|---:|---:|---:|---:|
| BCHUSDT | 52 (-21) | 46.2% | +75.03 | +151.51% |
| LDOUSDT | 7 (-4) | 28.6% | -2.50 | -5.05% |
| TRXUSDT | 53 (-22) | 30.2% | **-23.01** | -46.47% |

The IS regression mechanism: M2's IS filter made **TRX IS net_pnl NEGATIVE** (-23.01, from removing 22 trades while leaving the directional bleed). BCH still carries IS alone (+75.03, 151.51% of total). The IS aggregate Sharpe falls because M2 stripped signal alongside noise on TRX — the same-feature-M2 mechanism the iter-v3/017 PATH C result identified and T3 EDA pre-signalled (portfolio mean `|AUC-0.5|` = 0.0577, near-zero; 13 of 14 features carry essentially no winner/loser discrimination).

### 3.3 M2 veto-rate analysis

M2 is demonstrably active — the saturation falsifier (brief §4.5: IS count ≥ 155 → NULL-RESULT) did NOT fire (IS count = 112):

- **IS veto rate**: 1,254 vetoes / ~3,177 M2-evaluated bars = **39.5%**
- **Overall (IS+OOS) veto rate**: 1,953 vetoes / 5,467 = **35.7%**
- Reference (iter-v3/017): 42.7% — same order of magnitude, slightly lower here.
- Per-symbol veto activity: BCH 679 IS / 170 OOS vetoes; TRX 510 IS / 265 OOS vetoes; LDO 65 IS / 264 OOS vetoes.

Per-symbol IS trade-count shift (brief §4.6 monitoring): BCH -21, TRX -22 (both at the edge of the expected -10 to -20 band), LDO -4 (**exceeds** the predicted "0 to -2" — M2 found enough of the 6-month post-listing LDO window to train and vetoed 65 IS bars; brief §4.6 required this to be noted: NOTED).

The conclusion from the veto analysis: M2 is **WORKING AS DESIGNED** as a take/skip filter — it is materially filtering trades and it did cut OOS MaxDD. But "working as designed" is not "working well." The selection quality is symbol-asymmetric: a TRX-specific pattern learned IS, a BCH IS-noise overfit, and LDO suppressed to near-zero participation.

## 4. Critic verdict summary

**OVERALL = MERGE** (Critic FINAL `2fe38c5`). The "MERGE" verdict certifies the iteration's closeout integrity ONLY — per the Critic's own framing it explicitly does NOT imply a baseline update: "iteration iter-v3/071 does NOT advance to cycle-2 CONFIRMATION and does NOT update BASELINE_V3.md — /059 stays canonical."

All 8 per-checks PASS — zero BLOCK:
- **Checks 1, 2, 4, 5, 6, 7, 8** — PASS (look-ahead audit, embargo width, IC correlation, ADF stationarity, Gate 10-CPCV, reproducibility, hypothesis-implementation alignment).
- **Check 3** — PBO=NaN UNEVALUABLE (informational at EXPLORATION; non-blocking) / DSR_relative_B4=0.9845 PASS / PSR=1.0 PASS.
- **Foundation Audit (Boot Steps 9-11)** — PASS: walk-forward lookahead fix INTACT (`walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`; `compute_embargo_candles(10080,480)=22`); §11 Anti-Pattern Static Scan CLEAN; the lone code change is the cosmetic `ITERATION_LABEL` bump.

**Look-ahead audit certified clean.** M2 trains on `train_indices` bounded by `split.train_end_ms` — the SAME embargoed window M1 uses; M2's binary label comes from `label_trades()` on training indices only; the last-bar triple-barrier scan terminates at `train_end_ms + 21 candles < test_start_ms` (embargo of 22 correctly sized). M2 introduces NO new label-leakage path.

**PBO=NaN adjudicated NON-BLOCKING — a one-line runner WIRING DEFECT, not a structural impossibility.** The engineering report's root-cause hypothesis (the OOF-writing hook "sits in the LightGbmStrategy base path and is not triggered in the MetaLabelingStrategy path") is **factually incorrect**. The Critic traced the actual cause: the OOF-writing hook is in `optimization.py` (`optimize_and_train`), invoked by `lgbm.py:493` whenever `oof_persist_path` is non-None; `MetaLabelingStrategy`'s M1 IS a `LightGbmStrategy` and `__init__` forwards `oof_persist_path` to it correctly when given it. The parquet is absent purely because `run_baseline_v3.py:1492` constructs `MetaLabelingStrategy(**common_kwargs)` with `common_kwargs` **OMITTING** `oof_persist_path` — the `lgbm` and `xgboost` branches (lines ~1500 / ~1494) both pass it explicitly; the `metalabeling` branch is the lone omission. One-line fixable gap. PBO=NaN does NOT invalidate the verdict because the brief Section 8.1 LOCKED PROMISING criteria lists exactly 4 conjuncts (IS ≥ +0.9325, OOS ≥ +0.3403, frac_positive_paths ≥ 0.50, no Critic methodology FAIL) — PBO is in NONE of them, in no Section-4 falsifier band, and is INFORMATIONAL at EXPLORATION mode per the `feedback_v3_dsr_mode_artifact.md` carve-out. **Caveat — adjudicated forward: at CONFIRMATION mode PBO < 0.4 is a binding Gate 5; an unevaluable PBO=NaN would force a Critic BLOCK. The wiring defect MUST be fixed before any `--model metalabeling` CONFIRMATION.**

**Classification precedence certified.** Both NEGATIVE (§8.2: IS Δ < -0.10, i.e. IS < +0.7325; observed +0.6825 trips it) and SUSPICIOUS-OOS-DOMINANT (§8.4: IS Δ < 0 AND OOS Δ ≥ +0.20; observed -0.150 & +0.322 satisfy both) fire concurrently. Brief §8.4's LOCKED precedence rule — "SUSPICIOUS takes precedence over NEGATIVE when both fire" — has no magnitude qualifier. **SUSPICIOUS-OOS-DOMINANT is the canonical outcome; NEGATIVE is superseded** (not a concurrent close).

**Two forensic inaccuracies in the engineering report flagged (non-verdict-altering)**: (i) `n_eff=5` is a computed SURROGATE (`n_effective_trials()` PCA-95), NOT a "hardcoded sentinel" as the report states; (ii) the report's Label Leakage Audit asserts the v3 walk-forward bug "is still present in this worktree" — FALSE; `walk_forward.py:113` reads the FIXED state `train_end_ms = test_start_ms - embargo_ms`. Both are carried to QR as engineering-report-template corrections (Section 8).

## 5. PATH classification — SUSPICIOUS-OOS-DOMINANT

Per brief Section 8.4 LOCKED criteria (SUSPICIOUS-OOS-DOMINANT sub-mode):
- IS Δ < 0 vs /060 (regression): **IS Δ = -0.150** — satisfied.
- OOS Δ ≥ +0.20 vs /060 (lift): **OOS Δ = +0.322** — satisfied.

→ **SUSPICIOUS-OOS-DOMINANT**. Per the §8.4 precedence rule, this takes classification precedence over the concurrently-firing NEGATIVE (§8.2) verdict. The pre-registered OOS/IS-ratio SUSPICIOUS gate (> 3.0) did NOT fire — the ratio is 0.6774, healthy. The SUSPICIOUS label here is the OOS-DOMINANT sub-mode specifically: a same-feature M2 filters in a way that lifts the trending-OOS-window Sharpe but regresses the chop/bear-IS-window Sharpe.

**The mechanism is NOT a code bug to fix; it is a falsified edge hypothesis.** The OOS axis genuinely lifts — but the lift is 212.98%-concentrated in TRX while BCH (-5.98) and LDO (-7.60) both go negative. As the engineering report frames it: "TRX-local precision, not a cross-symbol quality signal." Meta-labeling did not resolve the LDO directional bleed — it suppressed LDO to 8 OOS trades.

This is the SAME pattern the cycle-1 CONFIRMATION (iter-v3/070) produced (also SUSPICIOUS-OOS-DOMINANT) — but the /071 mechanism is different from /070's: /070 was SL-widening regime exposure (IS collapse -0.97, OOS/IS ratio 10.81); /071 is M2 symbol-asymmetric selection (modest IS regression -0.150, OOS/IS ratio 0.68 healthy, OOS lift TRX-concentrated). Same classification family, distinct mechanisms.

## 6. Hypothesis check

The brief Section 1 hypothesis: "Replacing the M1-only `LightGbmStrategy` with `MetaLabelingStrategy` lifts BOTH IS and OOS monthly Sharpe ≥ +0.10 vs the /060 anchor by filtering low-quality M1 signals — primarily the LDO directional bleed."

**The hypothesis was honestly FALSIFIED on the IS axis.** IS Δ = -0.150 < the +0.10 PROMISING threshold (and below the -0.10 NEGATIVE threshold). The "primarily the LDO directional bleed" sub-claim also failed: M2 did not fix LDO, it suppressed LDO to 8 OOS trades.

**Hypothesis-vs-outcome — the QR was honest and the brief did not over-promise.** The brief's Section 7 Failure-Mode Probability Calibration pre-registered:
- **PATH C / INERT (40%)** — pre-registered as the *dominant* predicted outcome (the iter-v3/017 result reproduced; same-feature M2 strips signal alongside noise).
- **NEGATIVE (35%)** — the second-most-likely.
- **PROMISING (15%)**.
- **SUSPICIOUS (10%)** — the tail.

**The observed outcome — SUSPICIOUS-OOS-DOMINANT — is the 10% tail path.** The QR correctly did NOT predict it as most-likely; a low-probability outcome correctly weighted low. The brief's honest framing held: the T3 EDA (portfolio best `|AUC-0.5|` = 0.1222, narrowly above the 0.12 bar; mean 0.0577 near-zero) pre-signalled a borderline axis, and the brief explicitly stated "the brief does not predict success." The decisive lesson: **a same-feature M2 (M1's own 14 features + confidence) does NOT deliver a clean PROMISING lift** at the unified /060 anchor — it reproduces the suspicious pattern with TRX-concentrated OOS. This is a clean, quantitatively-grounded data point.

Process predictions: P1 (wall-clock may touch 2h cap, ~30%) — did NOT fire; 0.65h, well under cap. P2 (M2 nearly inactive on LDO, ≥70%) — partially fired; M2 DID train on LDO's 6-month post-listing window (65 IS vetoes, LDO IS shift -4 exceeded the predicted -2 to 0), but the brief's LDO concern was directionally correct — M2 over-suppressed LDO to 8 OOS trades. P3 (integration runs clean, ~10% failure) — held; clean integration.

## 7. BASELINE_V3.md status — UNCHANGED

**BASELINE_V3.md is UNCHANGED. /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`).**

iter-v3/071 is an EXPLORATION, not a CONFIRMATION. EXPLORATIONs never update BASELINE_V3.md — only a CONFIRMATION-MERGE does (per `feedback_v3_baseline_update_policy.md` and `feedback_v3_strict_both_is_oos_baseline.md`). The SUSPICIOUS-OOS-DOMINANT classification additionally means the axis does NOT advance to the cycle-2 CONFIRMATION bundle as an edge ingredient.

No new git tag is issued.

## 8. Critic Recommendations carried forward

Five recommendations from Critic FINAL `2fe38c5`:

1. **Fix the `--model metalabeling` OOF wiring defect before ANY meta-labeling CONFIRMATION.** `run_baseline_v3.py:1492` must pass `oof_persist_path` into `MetaLabelingStrategy(**common_kwargs)` — exactly as the `lgbm`/`xgboost` branches do. One-line gap. Until fixed, every `--model metalabeling` run produces PBO=NaN; at CONFIRMATION an unevaluable PBO would force a Critic BLOCK (PBO < 0.4 is a binding Gate 5). New memory rule `feedback_v3_metalabeling_oof_wiring.md` created at this closeout to make the fix mandatory before any meta-labeling CONFIRMATION. The self-contradictory comment at `run_baseline_v3.py:1490-1491` should be fixed in the same change.

2. **Correct two forensic inaccuracies in the engineering-report template**: (a) `n_eff=5` is a computed PCA-95 surrogate (`n_effective_trials()`), NOT a hardcoded sentinel; (b) the PBO=NaN root-cause narrative ("OOF hook in LightGbmStrategy base path not triggered in MetaLabelingStrategy path") is false — the hook runs inside `MetaLabelingStrategy`'s M1; the cause is the omitted constructor argument (see Rec #1).

3. **Reconcile the engineering report's Label Leakage Audit with the verified code.** The report states the walk-forward bug "is still present in this worktree" — FALSE. `walk_forward.py:113` reads `train_end_ms = test_start_ms - embargo_ms` (the FIXED state). Future engineering reports must not assert a bug the live code and the brief both contradict. (NOTE: this conflicts with `feedback_v3_walkforward_lookahead_bug.md`, which states the v3 worktree still carries the bug. The Critic verified the FIXED state at `walk_forward.py:113`; the /059 baseline also documents the fix inherited at `e149e9d`. The engineering-report template should align with the verified code state.)

4. **A future meta-labeling EXPLORATION must use DISTINCT M2 features.** iter-v3/071 is a clean unified-anchor data point that same-feature M2 (M1's 14 features + confidence) does NOT deliver a PROMISING lift — it reproduces the SUSPICIOUS-OOS-DOMINANT pattern with TRX-concentrated OOS. This is the iter-v3/017 lesson-#4 fix that /071 intentionally deferred for single-axis discipline. A second meta-labeling EXPLORATION should pre-register an M2 feature set M1 does NOT use (funding, OI, basis, regime) with its own EDA + the trade-rate consequence for any downstream CONFIRMATION bundle. **This is a follow-up — not necessarily the immediate cycle-2 #2 axis** (see Section 9).

5. **Carry forward the open iter-v3/070 Rec #2 (Category-2 IC carve-out).** `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` remains in the inherited /059 baseline. Cycle 2 should either (a) restrict the Category-2 IC carve-out to feature-vs-own-primitive pairs only, or (b) explicitly grandfather inherited baseline correlations and apply the IC gate only to NEWLY-added features.

## 9. Next Iteration Ideas — cycle 2 #2 (iter-v3/072)

iter-v3/072 is cycle 2 EXPLORATION #2 of 10. It anchors against /060 (EXPLORATION-mode reference; unchanged) and the QR commissions EDA per `feedback_v3_axis_selection_quant_discipline.md` before any setup commit. The same-feature meta-labeling axis is now exhausted for this cycle.

Per the BASELINE_V3.md cycle-2 axis priorities and the iter-v3/070 Phase 8 closeout, candidate axes for /072 (QR EDA selects):

1. **Distinct-feature meta-labeling (Critic Rec #4).** A SECOND meta-labeling EXPLORATION with an M2 feature set M1 does NOT use (funding rate, OI, basis, regime indicators). This is the iter-v3/017 lesson-#4 fix. /071 proved same-feature M2 fails; a distinct-feature M2 is the natural next probe of the meta-labeling axis. Caveat: it must carry its own EDA establishing the distinct features have winner/loser discrimination M1's 14 features lack, AND pre-register the trade-rate consequence (meta-labeling structurally reduces trade count — /071 over-filtered OOS to 5.71 trades/month; any downstream CONFIRMATION bundling meta-labeling would breach the 130-trade aggregate OOS floor). This is a follow-up to /071, NOT necessarily #2 — the QR EDA decides whether the meta-labeling axis warrants a second consecutive EXPLORATION or whether to pivot.

2. **HIGH — Alternative labeling architecture.** Fixed-horizon return labels as an alternative to the ATR triple-barrier. Cycle 1 proved the ATR-multiplier knob is a dead end (both /065 widening and /042 tightening failed). A different label DEFINITION — not a different multiplier — is the open structural question. This is the HIGH cycle-2 priority per BASELINE_V3.md after meta-labeling.

3. **MEDIUM — Universe revision: replace LDO.** /071 reinforced that LDO is the structurally weakest symbol — meta-labeling could not rescue it, it suppressed LDO to 8 OOS trades. If alternative labeling also fails to rescue LDO, the honest move is to replace LDO with an IS-validated-edge symbol. Caveat: prior universe-expansion EXPLORATIONs (/021 HBAR+AVAX, /069 ADA) all failed — a replacement must clear an IS-edge screen BEFORE inclusion, not just a feature-space-distance screen.

**Constraints binding every cycle-2 brief:**
- **Per-symbol IS-axis discipline** (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`): validate any per-symbol customization PRESERVES or LIFTS IS Sharpe before bundling. /071 reinforces this — its OOS-only lift with IS regression is not bundle-grade.
- **Pre-register the OOS/IS ratio bound** (`feedback_v3_oos_is_ratio_gate.md`): every cycle-2 EXPLORATION brief Section 4 must pre-register "OOS/IS Sharpe ratio > 3.0 → SUSPICIOUS."
- **If /072 runs `--model metalabeling` at any point, the OOF wiring defect (`run_baseline_v3.py:1492`) is informational at EXPLORATION but BLOCKING at CONFIRMATION** (`feedback_v3_metalabeling_oof_wiring.md`).

What cycle 2 should NOT do: more ATR-multiplier knobs, more single-feature additions chosen by univariate rank, more universe additions chosen by feature-space distance alone, more gate-threshold tuning. Cycle 1 exhausted the knob space; cycle 2 must stay structural.

---

**Diary commit SHA**: TBD (this commit)
**Critic FINAL SHA**: `2fe38c5`
**Engineering report SHA**: `1ec1221`
**Brief LOCKED SHA**: `7303113`
**EDA SHA**: `4f32ec5`
**Phase 5.5 gate SHA**: `7cb700e`
**Reports**: `reports-v3/iteration_v3-071/`

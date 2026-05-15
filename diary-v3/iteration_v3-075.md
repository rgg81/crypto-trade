# iter-v3/075 — Cycle 2 #5 EXPLORATION / BTC-trend-regime position-SIZE de-rate (primitive 12, LDO+TRX-scoped) / INERT-AT-EXPLORATION

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #5 of 10; NEW RISK PRIMITIVE axis — holding-time-ORTHOGONAL by design)
**Axis**: primitive 12 — a BTC-trend-regime position-SIZE de-rate scalar. When BTC is in a bear/chop trend state (`close[t-1] < SMA_270(close)[t-1]`), the position WEIGHT of LDO/TRX trades is multiplied by 0.50; BCH and bull-regime trades are unchanged. `enable_regime_size_scalar=True`, `regime_size_scalar_symbols=("LDOUSDT","TRXUSDT")`, de-rate `0.50`, MA window `270`.
**Verdict**: EXPLORATION-MERGE per Critic FINAL `2211927` — OVERALL=MERGE; **INERT-AT-EXPLORATION classification certified clean**, AND the OOS-tuning remediation adjudicated COMPLETE (closeout-integrity / methodology certification, NOT an advancement)
**Classification**: **INERT-AT-EXPLORATION** per brief Section 8 LOCKED disjunctive gate (IS Δ +0.1198 clears the +0.10 PROMISING IS floor; OOS Δ -0.0768 fails the +0.20 PROMISING OOS floor and sits inside the [-0.20,+0.20] noise band; SUSPICIOUS does not fire; the scalar fired 237 signal-level times so NULL-RESULT is excluded)
**Advancement**: does NOT advance to the cycle-2 CONFIRMATION bundle — Primitive 12 traded IS for OOS roughly 1:1; it did not produce a co-directional lift
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`). **No new tag issued.**
**Branch**: `iteration-v3/075`

---

## 1. What was done

iter-v3/075 is the FIFTH EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is **primitive 12 — a BTC-trend-regime position-SIZE de-rate scalar**, a NEW RISK PRIMITIVE axis. It was chosen to satisfy the Critic /074 hard constraint (Rec #3): cycle-2 #5 must target the IS bear/chop drag directly with a **holding-time-orthogonal mechanism that acts on the FULL roster** — not a stress-bar subset like the /074 kill switch (which touched only 3 IS / 5 OOS trades, too few to lift the drag). A position-SIZE scalar scales exposure, not duration, and re-weights EVERY bear/chop-regime trade on the kept roster — addressing the "too few trades" failure mode directly.

The mechanism: at each LDO/TRX trade entry, the production code classifies the BTC trend state from the prior bar — `close[t-1] < SMA_270(close)[t-1]` → bear/chop. In the bear/chop state, the trade's position WEIGHT is multiplied by 0.50. BCH is excluded by scope (`regime_size_scalar_symbols=("LDOUSDT","TRXUSDT")`), and bull-regime trades pass through at full weight. The hypothesis (brief Section 7) was that down-weighting LDO/TRX exposure in the IS bear/chop drag-period would lift the IS aggregate without an equal OOS cost.

A mandatory secondary edit reverted /074's leftover: the regime-conditional kill switch (primitive 9) was reverted OFF — `enable_regime_gate=False`, `regime_gate_symbols=()` — restoring the established cycle-2 baseline risk-gate stack. This is a revert, not a second varied axis. The /073 leftover (`V3_ATR_MULTIPLIERS_PER_SYMBOL`) was already at `{}` from the /074 closeout and stays there; `DEFAULT_ATR_MULTIPLIERS=(2.0,1.0)` for all symbols.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS outer=42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Anchor for EXPLORATION-mode comparison: iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403).

Commit chain: first EDA `9a04f6f` (DEFECTIVE — see Section 4) → corrected EDA `a254e5a` → corrected brief `a41d308` → setup `f170a75` → error-fix `f6da345` → Phase 5.5 gate `e37d6cf` (PASS) → engineering report `80bbb59` → Critic review `2211927` → stale-comment fix `7c5c7a3`.

## 2. Results — vs /060 EXPLORATION-mode anchor

| Metric | /060 anchor | /075 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.9523** | **+0.1198** (clears the +0.10 PROMISING IS floor) |
| OOS monthly Sharpe | **+0.1403** | **+0.0635** | **-0.0768** (inside the [-0.20,+0.20] noise band; fails the +0.20 PROMISING OOS floor) |
| OOS/IS monthly Sharpe ratio | — | **0.0667** | healthy — no regime-divergence; ≪ 3.0 SUSPICIOUS gate |
| frac_positive_paths (CPCV) | 0.6444 | 0.644 | PASS @ 0.55 |
| PBO mean | 0.1278 | 0.1278 | 0 (post-gate weight scalar — Optuna landscape untouched) |
| DSR (legacy) | — | 0.0 | informational FAIL (EXPLORATION-mode artifact) |
| PSR | — | 0.798 | informational (EXPLORATION-mode) |
| DSR_relative_B4 | — | ~0.0001 (5.3e-05) | informational FAIL (EXPLORATION-mode artifact) |
| IS n_trades | 159 | 159 | 0 |
| OOS n_trades | 102 | 103 | +1 (verified data-extent artifact) |
| n_trials (Optuna total) | 315 | 315 | 0 |
| n_eff | 19 | 19 | 0 |

The headline: **IS lifted +0.1198 and OOS cost -0.0768.** The IS shift clears the +0.10 PROMISING IS floor; the OOS shift fails the +0.20 PROMISING OOS floor and sits inside the [-0.20,+0.20] noise band (above the -0.20 NEGATIVE floor). The OOS/IS monthly Sharpe ratio of **0.0667** is healthy — far below the >3.0 SUSPICIOUS gate; there is no regime-divergence signature. DSR=0.0 / PSR=0.798 / DSR_relative_B4≈0.0001 FAIL their 0.95 thresholds but are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` — the EXPLORATION-mode `n_trials=315` regime is not comparable to CONFIRMATION-mode `n_trials=1050`, and these edge axes do not trigger a BLOCK for an EXPLORATION iteration. PBO=0.1278 — the one Check-3 axis meaningful at any mode — PASSES, bit-identical to /060 (a post-gate weight scalar leaves the Optuna landscape and CPCV path construction untouched).

The defining feature of /075 is **the IS-up/OOS-down tension** (Section 5). The de-rate trades IS for OOS roughly 1:1 — it cannot lift the IS drag without an OOS cost.

### 2.1 Per-symbol OOS decomposition (from `reports-v3/iteration_v3-075/comparison.csv`)

| Symbol | /075 OOS wpnl | /075 OOS n_trades | Note |
|---|---:|---:|---|
| BCHUSDT | **+1.9078** | 37 | **BIT-IDENTICAL to /060** — de-rate scoped to LDO+TRX; QE verified 73/73 IS + 37/37 OOS field-by-field byte-identical |
| LDOUSDT | **-22.12** | 12 | de-rated in bear/chop; structural LDO weakness persists |
| TRXUSDT | **+22.42** | 54 | de-rated in bear/chop; the symbol carrying the OOS roster |

BCH bit-identity is the positive control: the scalar `regime_size_scalar_symbols=("LDOUSDT","TRXUSDT")` cannot touch BCH, and the QE confirmed BCH 73/73 IS + 37/37 OOS trades field-by-field identical to /060 (Critic Check 7 independently verified `weight_factor` and `weighted_pnl` byte-identity on the BCH rows). Single-axis discipline is verified.

## 3. The IS-up/OOS-down structural tension — the key scientific finding

This is the scientific deliverable of the iteration and the central design problem handed to cycle-2 #6 (/076).

Primitive 12 lifted IS (+0.1198) but cost OOS (-0.0768). **This is structural, not noise.** The mechanism:

- A BTC-trend classifier that de-rates the IS bear/chop drag **necessarily also de-rates OOS-uptrend LDO/TRX trades.** v3's IS window (2022-09 → 2025-03) is bear/chop-heavy; v3's OOS window (2025-03 → 2026-05) is a persistent BCH/LDO/TRX uptrend. The SAME "bear/chop" classifier tag that suppresses IS-bleeding trades also suppresses some OOS-rewarding trades — because the OOS window, while net-uptrend, still contains bars where `close[t-1] < SMA_270`, and the scalar fires on them.
- The de-rate therefore **trades IS for OOS roughly 1:1.** The +0.1198 IS lift and the -0.0768 OOS cost are two sides of one re-weighting; there is no co-directional gain.

Critically, this is NOT the holding-time-extension regime-divergence failure mode of /065/071/073. Those axes lengthened trade duration, loading the IS/OOS regime factor — OOS soared, IS collapsed, the OOS/IS ratio inflated. Primitive 12 is the OPPOSITE — it is holding-time-ORTHOGONAL by construction (a size scalar deletes no trade — see falsifier 2). The OOS/IS ratio of 0.0667 confirms no regime-divergence, and the kept-roster duration delta is ~0. The IS-up/OOS-down tension here is a different structural property: a post-gate **macro BTC-trend classifier** whose sign is regime-correlated with the IS/OOS split. The axis is well-behaved (no SUSPICIOUS, healthy OOS/IS ratio, holding-time-orthogonal) — it simply cannot lift the IS drag without an OOS cost, because the discriminator it uses is the very regime axis that flips sign between IS and OOS.

**Consequence for cycle-2 #6 (/076):** a post-gate macro BTC-trend classifier de-rating the IS drag is OOS-costly *by construction*. /076 must pre-register (committed IS-only analysis) whether a mechanism exists that discriminates IS bear/chop from OOS uptrend WITHOUT a feature whose sign is regime-correlated that way — e.g. a feature-internal IS-regime discriminator the *model* can learn, rather than a post-gate macro classifier (Critic Rec #3 — Section 9).

## 4. The OOS-tuning defect + correction — the process story

This iteration had a notable process story that the diary records transparently as a process lesson.

### 4.1 The defect

The QR's first EDA pass (committed at `9a04f6f`) selected the de-rate scalar by an **OOS-tuning rule**. The EDA's `T3`/`T8` tables computed a per-candidate OOS counterfactual (`oos_delta`) for each candidate de-rate value, and `main()` filtered candidates on `oos_delta >= -0.20` and ranked the survivors by `oos_delta`. That is **tuning a design parameter on OOS data** — a direct violation of the `feedback_no_cheating.md` no-cheating rule and of Rung 1 / Rung 5 of the evidence ladder (the QR must not peek at OOS during the design phase; even a single OOS-conditional filter contaminates the iteration). Compounding the defect, the first brief text claimed the de-rate was selected "IS-only" — the committed code directly contradicted the brief's own prose.

### 4.2 The catch

The orchestrator caught the defect **PRE-GATE** — before the Phase 5.5 gate, before any backtest. The QR was sent back to redo Phase 1-2.

### 4.3 The correction

The correction was made transparently across the EDA and brief (corrected EDA `a254e5a`, corrected brief `a41d308`):

- The de-rate value `0.50` became an **a-priori, data-free default** — a hardcoded literal with a documented structural rationale ("halve position size in an adverse BTC regime"). It is not the output of any `sort_values`, `filter`, `argmax`, or threshold operation, on IS or OOS data.
- `T3`/`T8` became **IS-only** — every `oos_delta` / `oos_monthly_sharpe` / `oos_is_ratio` column was removed; the tables now compute only `is_monthly_sharpe` and `is_delta` per candidate. A repository-wide grep for OOS columns in the corrected EDA source returns zero.
- The two other surviving design choices were audited and confirmed never contaminated: the MA window (270) via T2's `is_discrimination_pp` (an IS-only bear-vs-bull flag-rate spread); the scope (LDO+TRX) via T7's `bearchop_is_genuine_drag` (the sign of IS bear/chop-entry wpnl, IS-only).
- Brief Sections 2.4 / 4 / 7 were rewritten mechanism-derived (not OOS-counterfactual-derived); Section 10.0 disclosed the correction in full.

### 4.4 The Critic adjudication — remediation COMPLETE

The Critic independently audited the corrected EDA `axis_selection_eda.py` and adjudicated the remediation **COMPLETE** (review.md `2211927`). The load-bearing judgment: does the QR's prior exposure to the defective first-pass OOS counterfactual retroactively taint the a-priori `0.50`? The Critic ruled NO — a round-number "half size" cut is about as un-tunable as a parameter gets, the T8 IS lift is monotone in aggressiveness (so the only IS-fittable optimum is the boundary value 0.25, which the QR explicitly rejected fitting to), and the `0.50` is data-free by construction. Prior knowledge of an OOS counterfactual cannot overfit a parameter selected by a structural interpretability rule that ignores both IS and OOS magnitudes.

### 4.5 The process lesson

Two process items carry forward (Section 9 Critic Recs #1, #2):

1. The correction sweep must cover **all textual references** — code comments included, not only error-message strings. A stale code comment at `risk_v2.py:182-183` retained the pre-correction "T8 — largest IS lift clearing the floors" phrasing; it was missed by the same sweep that correctly fixed `run_baseline_v3.py:609`. It was fixed post-hoc by the orchestrator at `7c5c7a3`.
2. The no-OOS-tuning rule must be **codified** — every future EDA script must select each design parameter (de-rate, MA window, scope, threshold) via a function whose inputs are demonstrably IS-only or a-priori, and the EDA docstring must state, per parameter, the exact selection function and its input columns. The corrected /075 EDA already does this (its per-parameter "How the three design parameters are chosen" block); the Critic recommends making that block a mandatory EDA section.

The defect was caught and fully remediated before any data was generated, and the corrected design was independently certified clean. But it should not have happened — the QR's own design discipline, not the orchestrator's pre-gate review, should be the first line of defense against OOS-tuning.

## 5. Three falsifiers — all PASS

The brief pre-registered three falsifiers; all three PASS.

1. **BCH bit-identity (positive control).** The de-rate scope `("LDOUSDT","TRXUSDT")` excludes BCH. Predicted: BCH IS + OOS trade rosters byte-identical to /060. **Observed: BCH IS 73/73 + OOS 37/37 trades byte-identical to /060** — QE verified field-by-field, Critic Check 7 independently confirmed `weight_factor` and `weighted_pnl` byte-identity on the BCH rows. Single-axis discipline verified — the de-rate cannot touch BCH.

2. **Holding-time predictor.** Primitive 12 is a size scalar — it re-weights trades, it deletes none. Predicted: kept-roster mean trade duration delta ≈ 0; falsifier at +1.0 candles. **Observed: LDO+TRX kept-roster mean trade duration Δ = 0.000 IS / +0.004 OOS candles** — the +0.004 is entirely the one extra data-extent trade (Section 6); 250× below the +1.0 falsifier. Holding-time-orthogonality CONFIRMED — a size scalar deletes no trade, consistent with the /074 finding that holding-time-orthogonal axes do not load the regime factor.

3. **Behavioral-effect predictor.** The brief Section 4.4 pre-registered ≈24 IS / ≈32 OOS LDO+TRX trades de-rated (trade-level), with a behavioral-effect falsifier. **Observed: 28 IS / 33 OOS LDO+TRX trades de-rated (trade-level); signal-level `regime_size_scalar_fires` = 237 (BCH 0 — positive control, LDO 5, TRX 232).** The observed 28 IS / 33 OOS is within the "approximate" band of the ≈24/≈32 prediction (the T5 derivation used the static /060 roster without 3-seed Optuna variation), and is materially larger than /074's 3-IS/5-OOS suppression — the brief's mandate (a materially larger trade-population effect than /074) is satisfied. The scalar fired (237 signal-level), so NULL-RESULT is excluded.

## 6. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `2211927`. The MERGE verdict certifies (a) the INERT-AT-EXPLORATION classification clean and (b) the OOS-tuning remediation COMPLETE. It is a closeout-integrity / methodology certification, NOT an advancement — /075 does NOT advance to the cycle-2 CONFIRMATION bundle.

- **13/13 Checks PASS or informational.** DSR=0.0 / PSR=0.798 / DSR_relative_B4≈0.0001 — Check 3 edge axes informational-FAIL at EXPLORATION per `feedback_v3_dsr_mode_artifact.md` (not BLOCK-triggering); PBO=0.1278 PASS (bit-identical to /060); frac_positive_paths=0.644 ≥ 0.55 PASS; IC matrix 14×14 structurally identical to /060 (Primitive 12 adds no feature); ADF 2198 rows, all 14 frozen anchor features pass.
- **The OOS-tuning remediation adjudicated COMPLETE** — independent audit of the corrected EDA confirmed `chosen_derate = 0.50` is a hardcoded a-priori literal, no `oos_delta`/`oos_monthly_sharpe`/`oos_is_ratio` anywhere in the corrected EDA source, the MA-window and scope choices both IS-only (Section 4.4).
- **Foundation Audit CLEAN.** Walk-forward embargo intact (`train_end_ms = test_start_ms - embargo_ms`; `compute_embargo_candles(10080,480)=22`; `REQUIRED_GAP=66`). The BTC-trend classification is past-only on two surfaces: `_build_btc_trend_lookup` applies `close.shift(1)` BEFORE the `rolling(270)` mean (bar t's classification sees only `close[t-1 .. t-270]`); `_regime_size_scalar` selects the trade-time BTC bar via `np.searchsorted(..., side="left") - 1` (strict `< t` past-only contract). No look-ahead.
- **§11 Anti-Pattern Static Scan CLEAN** — no `start_time` trimming, no OOS-window manipulation. The de-rate fires AFTER the model and AFTER labeling (post-gate weight step) — it cannot leak into trade selection or the Optuna landscape, which is why PBO / frac_positive_paths / feature-importance are bit-identical to /060.
- **Single-axis discipline confirmed** — the brief declares exactly two changes (Primitive 12 ON; Primitive 9 regime gate reverted OFF); both verified in source. No scope creep: `enable_per_symbol_cap=False`, `block_long_for=()`/`block_short_for=()`, `enable_per_symbol_drawdown_brake=False`, `V3_ATR_MULTIPLIERS_PER_SYMBOL={}`.
- **One non-blocking documentation-hygiene defect** — the stale `risk_v2.py:182-183` code comment; fixed post-hoc by the orchestrator at `7c5c7a3` (Section 4.5).

## 7. PATH classification — INERT-AT-EXPLORATION

**INERT-AT-EXPLORATION** per brief Section 8 LOCKED disjunctive gate. The gate evaluation order is SUSPICIOUS → NEGATIVE → PROMISING → INERT/NULL-RESULT:

1. **SUSPICIOUS — ruled out.** OOS/IS monthly Sharpe ratio = 0.0667 ≪ 3.0 (the ratio gate does not fire). The OOS-DOMINANT sub-mode requires OOS shift ≥ +0.20 AND IS shift < +0.10 — observed OOS shift -0.0768 fails the first clause. The SUSPICIOUS-OOS-DOMINANT path cannot fire because the IS shift is POSITIVE (+0.1198) — there is no IS collapse to flag.
2. **NEGATIVE — ruled out.** Neither shift is below its NEGATIVE threshold (IS -0.10 / OOS -0.20): IS Δ +0.1198 is positive; OOS Δ -0.0768 is above the -0.20 floor.
3. **PROMISING — ruled out.** PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20. IS Δ +0.1198 clears the IS floor, BUT OOS Δ -0.0768 fails the +0.20 OOS floor — it sits inside the [-0.20,+0.20] noise band. Per `feedback_v3_strict_both_is_oos_baseline.md`, BOTH axes must clear; the strong-IS-only result does NOT rescue PROMISING.
4. **NULL-RESULT — ruled out.** The scalar fired 237 times at signal level (28 IS / 33 OOS trade-level re-weightings). NULL-RESULT requires zero firings.
5. **→ INERT-AT-EXPLORATION.** The remaining classification: the axis fired, IS cleared its PROMISING floor but OOS did not, and SUSPICIOUS does not fire. The mechanism of the INERT outcome is the IS-up/OOS-down tension (Section 3) — the de-rate traded IS for OOS roughly 1:1, so the OOS axis landed inside the noise band rather than clearing the +0.20 PROMISING floor co-directionally with IS.

INERT-AT-EXPLORATION iterations do not advance to CONFIRMATION and do not update BASELINE_V3.md.

## 8. Hypothesis check — pre-registered INERT mode fired

The QR brief Section 7 pre-registered **INERT-AT-EXPLORATION at probability ≈45%** as the most plausible outcome, with an explicit mechanism: a BTC-trend de-rate scoped to LDO+TRX would re-weight a moderate trade population in both windows, and because the IS/OOS regimes flip sign on the same BTC-trend axis the de-rate uses, the IS lift and the OOS cost would roughly cancel — landing the OOS axis inside the noise band even if IS cleared its floor.

**Observed: the INERT signature fired exactly.** IS Δ +0.1198 (cleared the +0.10 PROMISING IS floor); OOS Δ -0.0768 (inside the [-0.20,+0.20] noise band, below the +0.20 PROMISING OOS floor); 28 IS / 33 OOS trade-level re-weightings (within the pre-registered ≈24/≈32 band); BCH byte-identical to /060. The QR calibration was accurate on both the mechanism (the IS-up/OOS-down 1:1 trade-off) and the outcome (INERT). The ≈45%-probability mode is what happened.

## 9. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). An INERT-AT-EXPLORATION iteration does not advance to CONFIRMATION and does not update BASELINE_V3.md: the de-rate did not produce a co-directional IS+OOS lift, and `feedback_v3_strict_both_is_oos_baseline.md` requires BOTH axes to improve. **No new tag issued.** No BASELINE_V3.md edit at this closeout — Primitive 12 (BTC-trend-regime position-SIZE de-rate) is a single-data-point INERT result, not a closed-across-multiple-data-points axis, so it is not added to "Dead Ideas" (it remains catalogued in the EXPLORATION ledger only).

## 10. Critic Recommendations carried forward

1. **The stale code comment is fixed; the correction-sweep lesson stands.** `risk_v2.py:182-183` retained pre-correction "T8 — largest IS lift" phrasing; fixed post-hoc by the orchestrator at `7c5c7a3`. The lesson: when a methodology correction is applied, the correction sweep must grep the FULL repo for the stale phrasing — code comments included, not only error-message strings.

2. **Codify the no-OOS-tuning rule as a mandatory EDA section.** Every future EDA script must select each design parameter (de-rate, MA window, scope, threshold) via a function whose inputs are demonstrably IS-only or a-priori; the EDA docstring must state, per parameter, the exact selection function and its input columns. The corrected /075 EDA's "How the three design parameters are chosen" block is the template — make it mandatory.

3. **Cycle-2 #6 (/076) must break, not repeat, the IS-up/OOS-down tension.** Primitive 12 demonstrated that a post-gate macro BTC-trend classifier de-rating the IS drag is OOS-costly by construction — the discriminator's sign is regime-correlated with the IS/OOS split. /076 should pre-register (committed IS-only analysis) whether a mechanism exists that discriminates IS bear/chop from OOS uptrend WITHOUT a feature whose sign is regime-correlated that way — e.g. a feature-internal IS-regime discriminator the *model* can learn, rather than a post-gate macro classifier. Cycle 2 is 0/5 clean PROMISING; the next axis should be chosen to break the pattern.

## 11. Next Iteration Ideas

### Cycle 2 progress — 5/10 EXPLORATIONs done

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | **INERT-AT-EXPLORATION** |
| #6 | /076 | TBD per QR EDA — see candidates below | — |
| #7-#10 | /077-/080 | TBD | — |

**Cycle 2 is halfway done and has produced NO clean PROMISING (0/5).** The pattern across the five iterations:
- /071/073 — holding-time-EXTENSION axes loaded the IS/OOS regime factor (SUSPICIOUS-OOS-DOMINANT: OOS soars, IS collapses).
- /072 — fixed-horizon labeling decoupled label from execution (NEGATIVE).
- /074 — a holding-time-orthogonal kill switch touched too few trades (3 IS / 5 OOS) to lift the IS drag (INERT).
- /075 — a holding-time-orthogonal, full-roster size de-rate touched a materially larger trade population (28 IS / 33 OOS) but a post-gate macro BTC-trend classifier trades IS for OOS roughly 1:1 (INERT).

The defining unresolved problem remains the **IS bear/chop drag** (the /074 brief EDA PART 1 localized it: IS bear/chop monthly Sharpe −0.0242, 27.8% positive months) and the standing **LDO structural weakness** (LDO OOS -22.12 at /075). Cycle 2 has now ruled out: holding-time-extension axes (regime-divergence trap), narrow stress-bar kill switches (too few trades), and post-gate macro-regime size scalars (IS/OOS sign-correlated by construction).

### iter-v3/076 (cycle 2 #6) axis candidates — seeding only

Per Critic Rec #3, /076 should be chosen to **break the IS-up/OOS-down tension** that /075 demonstrated is structural to post-gate macro BTC-trend classifiers. The /076 actual axis is QR-EDA-driven and will be selected fresh in Phase 1-2 of /076 with a committed `analysis/iteration_v3-076/*.py` EDA script (`feedback_v3_axis_selection_quant_discipline.md`); the brief Section 2 must contain EDA-derived numerical tables. The candidates below seed the QR EDA only:

1. **A feature-internal IS-regime discriminator the MODEL learns (Critic Rec #3 — HIGHEST).** Rather than a post-gate macro classifier (whose sign is regime-correlated with the IS/OOS split — exactly the /075 trap), add a feature the model can use to discriminate WITHIN-regime: a feature that is informative in IS bear/chop without being a monotone proxy for the IS-vs-OOS regime axis. The /076 EDA must pre-register (committed IS-only analysis) whether such a mechanism exists — a feature whose IS bear/chop predictive value does NOT come from a sign that flips between IS and OOS. Candidate constructions: a within-regime momentum-quality feature, a realized-vol-conditioned signal-strength feature, or a microstructure feature whose IS-bear informativeness is orthogonal to the BTC-trend sign. Must clear the engineered-feature falsifiers (importance ≥30 per `feedback_v3_engineered_feature_pivot.md`) and be tested ALONE — SAME-FAMILY single-seed stacking is forbidden per `feedback_v3_engineered_features_dont_stack.md`.

2. **A meta-labeling M2 that filters on signal quality, not direction-and-regime.** /071's meta-labeling was a holding-time-EXTENSION axis (the M2 veto removed early stop-outs, lengthening the kept roster — SUSPICIOUS). A meta-labeling variant whose M2 filters on a non-duration-correlated quality signal — and is verified holding-time-orthogonal at brief stage — would address LDO's directional bleed without re-triggering the regime-divergence trap. This is the HIGHEST cycle-2 axis priority per BASELINE_V3.md cycle-2 axis priorities (meta-labeling as the structural response to a directionally-bleeding symbol), but it must be re-scoped to avoid the /071 holding-time-extension failure.

3. **A dedicated IS bear/chop sub-period attribution axis.** Extend the /074 brief EDA PART 1 limb into a full regime-stratified attribution: which symbols and which feature families carry vs drag the IS bear/chop −0.0242 monthly Sharpe, and — critically — whether ANY candidate change lifts IS bear/chop performance WITHOUT the OOS-uptrend cost that /075 demonstrated is mechanically tied to BTC-trend-correlated discriminators. This would directly characterize whether the IS-up/OOS-down tension is escapable at all, or whether the cycle-2 agenda should pivot to a universe-revision axis (replace LDO).

**Hard constraints on /076** (carried from prior closeouts):
- Holding-time-orthogonal — the brief Section 2 must include the holding-time-effect predictor (`feedback_v3_is_oos_regime_divergence.md`); any axis that lengthens mean/median trade duration loads the regime factor and must be rejected at brief stage.
- Pre-register the OOS/IS Sharpe ratio bound (>3.0 → SUSPICIOUS) in Section 4 per `feedback_v3_oos_is_ratio_gate.md`, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio definition.
- Pre-register a behavioral-effect predictor with a falsifier (`feedback_v3_axis_saturation_predictor.md`).
- Per-symbol IS-axis discipline (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) if the candidate is per-symbol.
- **NEW (Critic Rec #2):** the /076 EDA must select every design parameter via a function whose inputs are demonstrably IS-only or a-priori, and the EDA docstring must state, per parameter, the exact selection function and its input columns — a mandatory EDA section.
- **NEW (Critic Rec #3):** the /076 EDA must pre-register a committed IS-only analysis of whether the chosen mechanism discriminates IS bear/chop from OOS uptrend WITHOUT a feature whose sign is regime-correlated that way — chosen to break, not repeat, the IS-up/OOS-down tension.

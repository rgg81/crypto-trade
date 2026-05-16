# iter-v3/081 — CYCLE 2 CONFIRMATION / CONFIRMED (/059 re-validated) / NO-MERGE — CYCLE 2 COMPLETE

**Date**: 2026-05-16
**Type**: CYCLE 2 CONFIRMATION (the SEPARATE CONFIRMATION after the strict 10:1 cadence; cycle 2 = EXPLORATIONs /071-/080, then 1 SEPARATE CONFIRMATION /081 — the 10th EXPLORATION was NOT collapsed into the CONFIRMATION)
**Bundle**: NONE — cycle 2 produced 0 clean PROMISING across all 10 EXPLORATIONs. /081 is a multi-seed RE-VALIDATION of the canonical /059 configuration, analogous to cycle 1's /070 CONFIRMATION (also NO-MERGE).
**Verdict**: **CONFIRMED — NO-MERGE** per `feedback_v3_strict_both_is_oos_baseline.md`. /081 re-validates /059 within the LOCKED ±0.20 tolerance on BOTH axes; cycle 2 produced no edge ingredient, so there is nothing to merge.
**Critic FINAL**: `f8c8474` — OVERALL=MERGE (the CONFIRMED classification, the baseline-integrity finding, and the 11-gate readout all CERTIFIED clean; "MERGE" certifies closeout integrity, NOT a baseline update)
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`). **No new tag issued.**
**Branch**: `iteration-v3/081`

---

## 1. What was done

iter-v3/081 is the cycle-2 CONFIRMATION of v3 — the SEPARATE CONFIRMATION run after the strict 10:1 cadence (`feedback_v3_strict_10_to_1_cadence.md`). Cycle 2 ran 10 SEPARATE EXPLORATIONs (/071-/080); the 10th (/080) was a separate single-seed PASSIVE-DIAGNOSTIC, NOT collapsed into /081.

**/081 is a RE-VALIDATION, not an edge-bundle CONFIRMATION.** A standard CONFIRMATION bundles the cycle's PROMISING EXPLORATION findings. **Cycle 2 produced zero clean PROMISING across all 10 EXPLORATIONs** — there is no edge ingredient to bundle. This is the exact situation cycle 1 hit at /070 (cycle 1 also produced no bundle-able edge; its 2-component bundle of the only non-anchor candidates was SUSPICIOUS-OOS-DOMINANT NO-MERGE — `project_v3_cycle1_outcome.md`). Per the /080 diary Section 11 and the /080 Critic Recommendation #1, /081 executes a `--seeds 2` unified 10-seed CONFIRMATION-mode run of the canonical /059 configuration to confirm `BASELINE_V3.md`'s IS +1.0894 / OOS +0.5791 still reproduces under the current code state.

**The /081 setup made exactly 3 substantive sub-fixes** (`run_baseline_v3.py`), all certified by the Critic's Hypothesis-Implementation Alignment check:

| Sub-fix | Code change | Site |
|---|---|---|
| 1 | `vol_scale_floor_per_symbol={}` — revert the illegitimate iter-v3/061 TRX vol-floor accretion (Section 4) | `run_baseline_v3.py:1729` |
| 2 | `expected_floor_dict={}` pre-flight assertion — raises `ValueError` if the floor re-creeps in | `run_baseline_v3.py:808` |
| 3 | `ITERATION_LABEL = "v3-081"` | `run_baseline_v3.py:131` |

Nothing else behavior-affecting is touched — no feature added, no labeling change, no selection-gate change, no model-architecture change, no universe change (`V3_MODELS` stays BCH/LDO/TRX), no seed change, no Optuna change.

Run mode: DEFAULT CONFIRMATION (`ENSEMBLE_SIZE=10` unified architecture per `feedback_v3_unified_10seed_baseline.md`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), `REQUIRED_GAP = 66 = (21+1)×3`, embargo 22. Total Optuna trials = 35 × 3 sym × 10 seeds = 1050 (identical to /059). `ensemble_summary.json` confirms `"mode": "confirmation"`, `"ensemble_size": 10`, 5 outer=42-lineage + 5 outer=123-lineage seeds.

Commit chain: EDA `be0ccf5` / ruff-clean `f9ddea5` → research brief `944dddf` / backfill `d544e65` → setup `5d42c4a` → Phase 5.5 gate `75248b3` (PASS) → engineering report `9f013f8` → Critic review `f8c8474`.

## 2. Results — vs the BASELINE_V3.md /059 anchor

| Metric | BASELINE_V3.md /059 anchor | /081 actual | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+1.0894** | **+1.0894** | **0.0000 (exact)** |
| OOS monthly Sharpe | **+0.5791** | **+0.5999** | **+0.0208** |
| OOS/IS monthly Sharpe ratio | 0.5316 | **0.5507** | healthy (IS-dominant) |
| IS n_trades | 171 | 171 | **0 (bit-identical roster)** |
| OOS n_trades | 94 | 94 | **0** |
| PBO mean | — | **0.1278** | PASS (< 0.40) |
| PSR | — | **1.0000** | PASS (> 0.95) |
| DSR_relative_B4 | — | **1.0000** | PASS (> 0.95) |
| frac_positive_paths (CPCV) | — | **0.6444** | PASS (> 0.55) |
| Legacy DSR | — | 0.0 | documented structural SBT artifact at n_trials=1050 / n_eff=19 |

**The headline.** The IS monthly Sharpe is **exactly 0.0000 Δ** — a 4-decimal match against the /059 anchor. The IS window is fixed at [data-start, 2025-03-24) by `OOS_CUTOFF_DATE`, so it has no data-extent channel; the only IS-drift source is Optuna TPE run-to-run stochasticity. An exact 4-decimal match on a stochastic 1050-trial TPE run is the strongest possible evidence that the /081 config is bit-identical to /059's config — a single drifted `weight_factor` on any of the 171 IS trades would have moved the Sharpe off +1.0894. The IS roster is genuinely 171 trades (BCH 83 + LDO 9 + TRX 79), matching `per_symbol.csv`, the engineering report, and BASELINE_V3.md /059.

The OOS monthly Sharpe lifted +0.0208 — well inside the LOCKED ±0.20 band. The QE root-caused it to a single trade: the trade that closed `end_of_data` at /059's data boundary now resolves `take_profit` (`TRXUSDT, open_time=1778572799999, weight_factor=0.5000`) with ~1.5 more OOS candles of data extent — a monotonic calendar effect, the identical mechanism the /077-/080 Critics certified benign. The OOS roster is otherwise 94 trades, 0 key diffs / 0 `weight_factor` diffs vs /059.

## 3. PATH classification — CONFIRMED (gate evaluation)

Per the brief Section 8.1 LOCKED re-validation logic — /059 is CONFIRMED if /081 reproduces it within ±0.20 monthly Sharpe on BOTH axes:

- **IS axis (G.1)**: IS Δ = **0.0000**, inside the LOCKED ±0.20 band. **PASS.**
- **OOS axis (G.2)**: OOS Δ = **+0.0208**, inside the LOCKED ±0.20 band. **PASS.**
- **No MERGE path**: cycle 2 produced 0 clean PROMISING across 10 EXPLORATIONs — there is no edge ingredient to bundle. The CONFIRMED outcome → BASELINE_V3.md UNCHANGED, /059 canonical at tag `v0.v3-059`, no new tag.

**All 11 pre-registered gates PASS:**

| Gate | Threshold | /081 observed | Status |
|---|---|---:|---|
| G.1 IS re-validation | within ±0.20 of /059 | Δ 0.0000 | PASS |
| G.2 OOS re-validation | within ±0.20 of /059 | Δ +0.0208 | PASS |
| G.3 OOS/IS ratio | ≥ 0.50 | 0.5507 | PASS |
| G.4 PBO | < 0.40 | 0.1278 | PASS |
| G.5 PSR | > 0.95 | 1.0000 | PASS |
| G.6 DSR_relative_B4 | > 0.95 | 1.0000 | PASS |
| G.7 OOS/IS ratio (SUSPICIOUS bound) | ≤ 3.0 | 0.5507 | PASS (not-SUSPICIOUS) |
| G.8 frac_positive_paths | > 0.55 | 0.6444 | PASS |
| G.9 walk-forward embargo | gap = 66, embargo = 22 | confirmed at runtime | PASS |
| G.10 Pareto | retired under unified 10-seed → Gate-10-CPCV | frac_positive_paths 0.6444 | PASS-equivalent |
| G.11 reproducibility / commit chain | fully stamped | EDA→brief→setup→gate chain stamped | PASS |

For the record: /059's OOS +0.60 does not clear the aspirational OOS > +1.0 merge floor, and OOS trades 94 < 130 — but /059 is the BASELINE being re-validated, not a merge candidate; these aspirational shortfalls inform cycle-3 priorities without blocking the CONFIRMED classification. **/081 is NO-MERGE because cycle 2 produced no edge — which is the correct outcome, not a gate failure.** The legacy DSR=0.0 is the documented structural López de Prado SBT artifact at n_trials=1050 / n_eff=19 (the required E[max_SR] ~2.61 exceeds the observed annualized Sharpe); `DSR_relative_B4` is the operative CONFIRMATION DSR gate and it PASSES at 1.0000.

## 4. The baseline-integrity finding — the /061 illegitimate accretion + the /081 revert

The load-bearing methodology event of /081 is the discovery and revert of an illegitimate config accretion.

**The finding.** The /081 EDA (`analysis/iteration_v3-081/baseline_integrity_audit.py`, SHA `be0ccf5`) ran a git-archaeology measurement-integrity audit — a diff of every behavior-affecting config knob between the /059 setup commit `20095a8` and current HEAD. **Exactly ONE illegitimate accretion was found**: `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` was present at HEAD but ABSENT at /059's `20095a8` (zero references). Every other behavior-affecting axis tested in cycles 1-2 (`DEFAULT_ATR_MULTIPLIERS`, `V3_ATR_MULTIPLIERS_PER_SYMBOL`, `V3_MODELS`, `label_mode`, `label_timeout_minutes`, `inference_threshold_floor`, the gated-off primitives) was explicitly reverted at its EXPLORATION/CONFIRMATION closeout — the `feedback_no_cheating.md` anti-drift discipline was correctly applied everywhere except this one line.

**The /061 vol-floor provenance — why it is illegitimate:**

- The TRX `vol_scale_floor` was introduced at **iter-v3/061** — a cycle-1 EXPLORATION (#2 of 10), `feat` commit `6910fcf`.
- iter-v3/061 was **INERT-AT-EXPLORATION** — IS Δ −0.009 / OOS Δ +0.015 vs the /060 anchor, inside the noise band; it was never even PROMISING.
- It was **never tagged** — `git tag -l v0.v3-*` returns only `{018, 028, 058, 059}`; there is no `v0.v3-061`.
- It was **never carried by a CONFIRMATION-MERGE** — cycle 1's only CONFIRMATION (/070) was SUSPICIOUS-OOS-DOMINANT NO-MERGE, and its bundle was `{/065 SL widening, /062 Path B4}` — the /061 floor was NOT a bundle component.
- The /061 closeout reverted the *intent* but not the *runner config line*: it kept the `RiskV2Config` field + lookup (the harmless mechanism) and silently left the `_build_v3_model` config line `{"TRXUSDT": 0.5}` active. EXPLORATIONs /062-/080 each varied one OTHER axis and never touched the floor line — **so it rode forward 19 iterations undetected.**

The binding rule is `feedback_v3_cadence_discipline.md` rule 5: only a CONFIRMATION-MERGE updates the canonical config. An EXPLORATION axis that was only INERT, never tagged, and never carried by a CONFIRMATION-MERGE persisting in the active runner config IS illegitimate accretion — exactly the drift class `feedback_no_cheating.md` exists to prevent.

**The revert.** The /081 setup `5d42c4a` reverted it — `vol_scale_floor_per_symbol={}` at `run_baseline_v3.py:1729`, plus a consistent pre-flight assertion (`expected_floor_dict={}` at line 808) that raises `ValueError` if the floor re-creeps in. `run.log` confirms the assertion fired green at startup.

**The revert is corroborated at runtime — independent proof beyond the IS exact match.** The Critic inspected the OOS TRX trades: **eight carry `weight_factor` below 0.5** (0.33, 0.34, 0.36, 0.37, 0.38, 0.40, 0.45, 0.47); the IS TRX roster likewise carries 12+ trades with `weight_factor` in [0.35, 0.48]. If the iter-v3/061 `{"TRXUSDT": 0.5}` floor were still active, NO TRX trade could carry `weight_factor < 0.5` — the floor clips every vol-scaled value up to 0.5. The presence of sub-0.5 TRX weights on both splits is direct runtime proof the revert took effect and TRX is now on the global `0.3` floor. The IS exact-reproduction (+1.0894 = /059) is the corroborating evidence — /059 also had no floor, so reverting restored the genuine config.

**Material corollary.** Cycle 1's /070 CONFIRMATION ran with the floor active — so /070's numbers were on a config that was NOT pristine /059. This has **no bearing on BASELINE_V3.md's integrity**: /070 was NO-MERGE, it never updated the baseline, and BASELINE_V3.md anchors /059 (setup commit `20095a8`, pre-/061, zero references to the floor). The baseline was never contaminated; only an intra-cycle measurement that did not feed it was. **/081 is genuinely the first CONFIRMATION-class run since /059 itself to measure the pristine /059 canonical config.**

## 5. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `f8c8474` (`briefs-v3/iteration_v3-081/review.md`). A single-round FINAL review — the 13 checks, the Foundation Audit, the §11 anti-pattern scan, and the three special adjudications all resolved unambiguously against the artifacts; zero clarifications were required from the QR. The "MERGE" verdict certifies the iteration's closeout integrity — it explicitly does NOT imply a baseline update.

- **All 8 Checks PASS or PASS-equivalent.** Check 1 (look-ahead) — /081 adds zero new features; the only code change is the vol-floor revert, a position-SIZE config knob consulting no future data; the 22-candle walk-forward embargo intact and confirmed at runtime via the `gap=184h (22 rows)` CV-fold logs. Check 2 (embargo) — `timeout_candles = 21`, `REQUIRED_GAP = (21+1)×3 = 66`, `compute_embargo_candles(10080, 480) = 22`. Check 3 (multiple-testing — BINDING for this CONFIRMATION) — PBO 0.1278 < 0.40, PSR 1.0000 > 0.95, DSR_relative_B4 1.0000 > 0.95 (the Path-B4 arithmetic independently verified: `cpcv_q75_annualized_b4 = 0.837759 × √(756/1296) = 0.6398`), frac_positive_paths 0.6444 > 0.55. Check 4 (IC) — no new feature family; the 14-feature stack byte-identical to /059. Check 5 (ADF) — `adf_test.csv` 2198 rows; at `2025-03` (the last training month before OOS_CUTOFF) all 14 features for all 3 symbols stationary. Check 6 (Pareto) — `pareto_front.csv` correctly ABSENT (Gate-10-Pareto retired under the unified 10-seed architecture, replaced by Gate-10-CPCV which passes at 0.6444). Check 7 (reproducibility) — commit chain fully stamped, `ensemble_summary.json` carries the literal 10-tuple seeds with lineage, OOS PnL spot-check reconciles. Check 8 (hypothesis-implementation alignment) — the brief declares exactly 3 substantive sub-fixes; all three present at the cited lines; no scope creep.
- **Foundation Audit (Boot Steps 9-11) PASS** — walk-forward embargo intact (`walk_forward.py:113` `train_end_ms = test_start_ms − embargo_ms`); `ITERATION_LABEL = "v3-081"`; `V3_MODELS` = BCH/LDO/TRX; `vol_scale_floor_per_symbol={}` + pre-flight assertion; `efficiency_ratio_50`/`range_efficiency_50` ban intact; `ENSEMBLE_SIZE=10` CONFIRMATION mode; sacred constants immutable (`OOS_CUTOFF_DATE="2025-03-24"`, `TRAINING_MONTHS=24`); feature isolation clean.
- **§11 Anti-Pattern Static Scan CLEAN** — no `feature_columns=None`, no `min(REQUIRED_GAP, ...)`, no `start_time` manipulation, no silent universe survivorship, no cross-track import; `run.log` zero WARNING/ERROR/Traceback lines.
- **Three Critic Adjudications**: #1 the CONFIRMED classification CERTIFIED — the IS roster independently verified at 171 trades, an exact 4-decimal IS match is the strongest possible evidence of a bit-identical config, the OOS one-trade root-cause independently verified (zero `end_of_data` rows in the /081 OOS roster). #2 the baseline-integrity finding CERTIFIED — every load-bearing claim of the /061 vol-floor audit verified independently, including the runtime proof (8 sub-0.5 OOS TRX weights, impossible under the old floor); the revert is a correct, legitimate measurement-integrity correction directly analogous to the /070-closeout revert of the rejected /065 SL widening. #3 the 11-gate readout for a CONFIRMATION CERTIFIED — every gate verified against `dsr.json` / `run.log`; no gate FAIL; the legacy DSR=0.0 confirmed a documented structural SBT artifact, not a defect.

## 6. BASELINE_V3.md status — UNCHANGED

**BASELINE_V3.md is UNCHANGED. /059 stays canonical (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791; tag `v0.v3-059`).**

Per `feedback_v3_strict_both_is_oos_baseline.md`: a CONFIRMATION updates BASELINE_V3.md ONLY when it beats the prior baseline on BOTH IS and OOS Sharpe with a bundled edge ingredient. /081 is a re-validation — it carries no edge ingredient and does not improve either axis (IS Δ 0.0000, OOS Δ +0.0208 a data-extent artifact). **No new git tag is issued.** This mirrors cycle 1's /070 NO-MERGE re-validation exactly.

`V3_MODELS` stays BCH/LDO/TRX; `vol_scale_floor_per_symbol={}` is now permanently reverted in the runner — cycle 3 inherits the pristine /059 config, not the /061-accreted one. The BASELINE_V3.md anchor METRICS do not change; a "Last updated" annotation records the /081 CONFIRMATION re-validation and the /061-vol-floor revert.

## 7. CYCLE 2 OUTCOME RECKONING — 10 EXPLORATIONs, 0 clean PROMISING

iter-v3/081 CLOSES CYCLE 2. The full cycle-2 record:

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | INERT-AT-EXPLORATION |
| #6 | /076 | NEW FEATURE (`range_efficiency_50`, Kaufman path efficiency) | SUSPICIOUS-OOS-DOMINANT |
| #7 | /077 | PASSIVE-DIAGNOSTIC (`conditional_orthogonality.csv` + `range_efficiency_50` revert) | INERT-AT-EXPLORATION |
| #8 | /078 | UNIVERSE REVISION (replace LDOUSDT with ADAUSDT) | SUSPICIOUS-OOS-DOMINANT |
| #9 | /079 | NEW RISK PRIMITIVE (conviction-weighted per-trade sizing, primitive 13) | NULL-RESULT (behavioral saturation) |
| #10 | /080 | PASSIVE-DIAGNOSTIC (persist per-trade `confidence` + `confidence_distribution.csv`) | NULL-RESULT (bit-identical roster) |
| **CONF** | **/081** | **/059-baseline multi-seed RE-VALIDATION (+ /061-vol-floor revert)** | **CONFIRMED — NO-MERGE** |

**Cycle 2 EXPLORATION record, explicitly: 10/10 done, 0 clean PROMISING** — 4 SUSPICIOUS-OOS-DOMINANT (/071, /073, /076, /078), 1 NEGATIVE (/072), 3 INERT (/074, /075, /077), 2 NULL-RESULT (/079, /080); /077 + /080 were the two PASSIVE-DIAGNOSTICs.

Cycle 2 produced load-bearing methodology corrections — the /077 anchor-staleness finding, the /077 bull-month reframing (the IS drag is in the bull months: IS_BULL Sharpe +0.4100 / 33% positive vs IS_BEAR_CHOP +1.2909 / 47% positive), the /078 universe-swap-as-third-regime-vector finding, the /079 threshold-coupled-axis behavioral-saturation finding, the /080 persisted-`confidence` instrument, and now the /081 baseline-integrity finding. **But it produced ZERO edge ingredients.** Together with cycle 1's identical /070 NO-MERGE re-validation outcome, this is dispositive evidence that the conservative axis families — gate-threshold knobs, risk primitives, single-symbol swaps, labeling tweaks, instrumentation — are EXHAUSTED against the narrow 3-symbol BCH/LDO/TRX universe. Cycle 2 closes with the v3 baseline structurally identical to /059, plus the durable Path B4 methodology infrastructure from cycle 1 and the /080 confidence instrument — and a config that is now pristine after the /081 revert.

## 8. Critic Recommendations carried to cycle 3

Three recommendations from Critic FINAL `f8c8474` — items for the cycle-3 EXPLORATION agenda, not fixes:

1. **Cycle 3 must be the bold structural pivot.** Cycle 2's 0/10-clean-PROMISING record (and cycle 1's identical /070 NO-MERGE outcome) is dispositive evidence that the conservative axis families are exhausted against the narrow 3-symbol universe. Per `feedback_v3_mass_feature_expansion.md` and `feedback_v3_bold_research_mandate.md`, the first cycle-3 EXPLORATION should elevate the feature universe (literature-grade crypto-native families: funding-rate regimes, OI dynamics, basis/premium, liquidation cascades, on-chain flow) AND/OR expand the symbol universe — denominator expansion is the structural fix for the standing BCH IS-PnL concentration fragility.

2. **The three standing constraints carried into cycle 3 are real and unresolved.** (a) **LDO directional weakness** — OOS WR 25.0%, well below the 50% baseline for a triple-barrier classifier; a drag through every cycle-1 and cycle-2 iteration. (b) **BCH IS-PnL / OOS concentration** — BCH dominates ~77% of IS wpnl, so a positive-edge change to any non-BCH symbol washes against BCH's dominance of the aggregate (the /078 finding). (c) **OOS Sharpe +0.60 is +0.42 short of the aspirational +1.0 floor.** Cycle-3 axis design should target these directly, not orthogonally.

3. **Audit for residual config accretion before the next CONFIRMATION.** The /061 vol-floor riding 19 iterations undetected is a process near-miss that the /081 baseline-integrity audit caught only because /081 happened to be a re-validation. Recommend a generalized "config == last-CONFIRMATION-MERGE config" pre-flight diff so future accretion is caught at runtime, not by archaeology.

## 9. Next — Cycle 3

**Cycle 2 is COMPLETE.** Cycle 3 = iter-v3/082-/091 (10 EXPLORATIONs) + /092 CONFIRMATION, per the strict 10:1 cadence (`feedback_v3_strict_10_to_1_cadence.md`).

Cycle 3 is authored as a **step-change in ambition** per `feedback_v3_bold_research_mandate.md` (user directive 2026-05-16) and `feedback_v3_mass_feature_expansion.md`. The conservative axis families cycle 2 exhausted are CLOSED for cycle 3. The cycle-3 plan — `briefs-v3/cycle3_plan.md` (authored at this closeout) — sets three priority directions: (1) NEW crypto-native feature families researched from quant-finance literature; (2) aggressive symbol-universe expansion (v3 has been locked to BCH/LDO/TRX for ALL of cycles 1-2; dozens of liquid symbols are available); (3) NEW model architectures / multi-symbol-pooled models. Every cycle-3 QR MUST do genuine WebSearch/WebFetch literature research in Phases 1-4 — not just EDA on the existing 3-symbol parquets. iter-v3/082 anchors against /081's CONFIRMED /059 numbers (the freshly re-validated canonical baseline).

---

**Diary commit SHA**: TBD (this commit)
**Critic FINAL SHA**: `f8c8474`
**Engineering report SHA**: `9f013f8`
**Brief LOCKED SHA**: `944dddf` (backfill `d544e65`)
**Setup SHA**: `5d42c4a`
**Phase 5.5 gate SHA**: `75248b3`
**Reports**: `reports-v3/iteration_v3-081/`

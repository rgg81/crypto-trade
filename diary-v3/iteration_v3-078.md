# iter-v3/078 — Cycle 2 #8 EXPLORATION / UNIVERSE REVISION (replace LDOUSDT with ADAUSDT) / SUSPICIOUS-OOS-DOMINANT

**Date**: 2026-05-16
**Type**: EXPLORATION (cycle 2 #8 of 10; single-axis — universe revision, `V3_MODELS` LDOUSDT→ADAUSDT)
**Axis**: replace `LDOUSDT` with `ADAUSDT` in `V3_MODELS` — the v3 universe goes BCH/LDO/TRX → BCH/ADA/TRX. The 14-feature stack, ATR labeling `(2.0, 1.0)`, the 7-primitive risk-gate stack, `ENSEMBLE_SEEDS`, and the Optuna search are all UNCHANGED. The QR EDA-exhausted the NEW-feature (T3/T4) and meta-labeling-M2 (T5) candidates first, then selected the universe swap; EDA T6 argued LDO is the in-universe symbol whose drag is not regime-split-correlated, and T7 (the IS-edge screen) selected ADA as the swap target (+1.17 IS-Sharpe over LDO). EXPLORATION mode.
**Verdict**: EXPLORATION-MERGE per Critic FINAL `75f4d42` — OVERALL=MERGE; **SUSPICIOUS-OOS-DOMINANT classification CERTIFIED clean**. A closeout-integrity certification, NOT an advancement: a SUSPICIOUS-OOS-DOMINANT axis never advances to the CONFIRMATION bundle.
**Classification**: **SUSPICIOUS-OOS-DOMINANT** per brief Section 8.4 — the OOS/IS ratio gate did NOT fire (0.8404 < 3.0), but the **OOS-DOMINANT sub-mode FIRED**: IS shift -0.0035 < 0 AND OOS shift +0.4814 ≥ +0.20. PROMISING (8.1) fails independently — it requires IS shift ≥ +0.10, observed -0.0035. SUSPICIOUS takes disjunctive precedence with no magnitude qualifier.
**Advancement**: does NOT advance to the cycle-2 CONFIRMATION bundle. A SUSPICIOUS-OOS-DOMINANT axis produces no edge ingredient — the OOS lift is uncorroborated by IS, the defining SUSPICIOUS signature. **LDOUSDT is RETAINED**; the universe-revision axis is CLOSED for cycle 2.
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`). **No new tag issued.** No BASELINE_V3.md edit at this closeout.
**Branch**: `iteration-v3/078`

---

## 1. What was done

iter-v3/078 is the EIGHTH EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION (/081 or later) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is a **single-axis universe revision**: `V3_MODELS` changes the third symbol from `LDOUSDT` to `ADAUSDT`. The universe goes from BCH/LDO/TRX to BCH/ADA/TRX. Nothing else is touched — the 14-feature stack, the ATR labeling `(2.0, 1.0)`, the 7-primitive risk-gate stack, `ENSEMBLE_SEEDS`, and the Optuna search are all unchanged at their /060 configuration. `REQUIRED_GAP = 66 = (21+1)×3` is unchanged (the universe count stays 3).

The QR's Phase 1-2 EDA, per `feedback_v3_axis_selection_quant_discipline.md`, was the basis for the axis selection. The EDA first EXHAUSTED two prior-priority candidates:
- **T3/T4 — a NEW bull-month entry-discrimination feature** (the /077 reframing-finding priority). REJECTED — the candidate failed the conditional-orthogonality screen against the /077 `conditional_orthogonality.csv` map.
- **T5 — a re-scoped meta-labeling M2** (BASELINE_V3.md cycle-2 priority #1). REJECTED — the per-trade entry-discrimination signal is near-random (max |AUC−0.5| = 0.064 on ALL_IS, 0.066 on bull months — essentially identical to the near-zero wall the /071 meta-labeling EDA hit, and /071 went SUSPICIOUS-OOS-DOMINANT). The bull-month overextension signal is real at the monthly-aggregate / regime-stratum level but the per-trade discrimination is near-random — an M2 built on these features filters at near-random and reproduces /071.

Having exhausted the feature and M2 candidates, the QR selected the universe-revision axis (BASELINE_V3.md cycle-2 priority #3). EDA T6 — the escapability bound — argued LDOUSDT is the one in-universe symbol whose drag is NOT regime-split-correlated (LDO bull-SHORT weak in BOTH the IS window, −1.16, AND the OOS window, −12.58), so removing LDO should lift IS without re-triggering the IS-up/OOS-down regime tension. EDA T7 — an IS-only walk-forward IS-edge screen — selected ADAUSDT as the swap target, screening ADA at +0.617 IS-Sharpe vs LDO's −0.550 (a +1.17 IS-edge margin). EDA T8 — the holding-time predictor — estimated the added(ADA)-vs-removed(LDO) label-implied mean-duration gap at +0.38 candles, comfortably inside the >+1.0-candle sub-channel falsifier.

The brief Section 4.1 PREDICTED an IS lift of +0.13 to +0.33 (central +0.20) with OOS roughly flat (−0.27 to +0.13). The brief Section 4.2 set the explicit falsifier: IS Δ < +0.10 → hypothesis falsified.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/ADA/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Anchor for the EXPLORATION-mode comparison: the **re-anchored current-code /060-config baseline IS +0.8236 / OOS +0.2078** (established by /077; NOT the stale frozen /060 +0.8325/+0.1403 — per the iter-v3/077 closeout anchor-staleness cycle-note).

Commit chain: EDA `e48ebad` → research brief `7be5323` (SHA-backfill `ba35f66`) → setup `0648504` → Phase 5.5 gate `9b475b4` (PASS) → engineering report `ceffd1d` → Critic review `75f4d42`.

## 2. Results — vs the re-anchored current-code /060-config baseline (IS +0.8236 / OOS +0.2078)

| Metric | re-anchored baseline | /078 actual | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8236** | **+0.8201** | **-0.0035** |
| OOS monthly Sharpe | **+0.2078** | **+0.6892** | **+0.4814** |
| OOS/IS monthly Sharpe ratio | — | **0.8404** | — |
| IS n_trades | ~159 | 222 | **+63** |
| OOS n_trades | ~103 | 109 | **+6** |
| PBO mean | 0.1278 | 0.1277 | ~0 |
| frac_positive_paths (CPCV) | 0.644 | 0.733 | **+0.089** |
| DSR (legacy) | — | 0.0 | informational (EXPLORATION-mode artifact) |
| PSR | — | 1.0000 | informational (EXPLORATION-mode) |
| DSR_relative_B4 | — | 0.9999 | informational (EXPLORATION-mode artifact) |
| n_trials (Optuna total) | 315 | 315 | 0 |
| n_eff | 19 | 19 | 0 |

**Per-symbol OOS attribution:**

| Symbol | OOS weighted_pnl | OOS n_trades | OOS win_rate | OOS concentration |
|---|---:|---:|---:|---:|
| ADAUSDT | +0.4230 | 18 | 27.8% | 1.56% |
| BCHUSDT | +1.9078 | 37 | 32.4% | 7.05% |
| TRXUSDT | +24.7184 | 54 | 48.1% | 91.38% |

**Per-symbol IS attribution:** BCH 73 trades / 45.2% WR / +78.34 wpnl; ADA 74 trades / 40.5% WR / +21.85 wpnl; TRX 75 trades / 29.3% WR / −24.95 wpnl. (Anchor /077 IS: BCH 73/45.2%/+78.34, LDO 11/27.3%/−11.44 net_pnl, TRX 75/29.3%/−24.95.)

**The headline.** IS slipped trivially (−0.0035, essentially flat). OOS lifted sharply (+0.4814, from +0.2078 to +0.6892). The OOS/IS ratio is a healthy 0.8404. **BCH OOS (+1.9078 / 37 trades) and TRX OOS (+24.7184 / 54 trades) are BIT-IDENTICAL to /077** — the universe swap of the third symbol did not leak into the independent BCH/TRX per-symbol models. LDO's −18.41 OOS weighted_pnl drag was replaced by ADA's +0.4230. DSR=0.0 / DSR_relative_B4=0.9999 are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` (EXPLORATION-mode `n_trials=315` is not comparable to CONFIRMATION-mode `n_trials=1050`). PBO=0.1277 — the one Check-3 axis meaningful at any mode — PASSES.

## 3. PATH classification — SUSPICIOUS-OOS-DOMINANT

The gate evaluation order per the brief Section 8 LOCKED disjunctive taxonomy is SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT; first match is canonical. Anchor = re-anchored IS +0.8236 / OOS +0.2078.

1. **SUSPICIOUS — FIRES.** Two independent grounds, evaluated:
   - **Ratio gate (8.4)**: OOS/IS monthly Sharpe ratio = +0.6892 / +0.8201 = **0.8404** < 3.0 — does NOT fire.
   - **OOS-DOMINANT sub-mode (8.4)**: requires IS shift < 0 AND OOS shift ≥ +0.20. IS shift = 0.8201 − 0.8236 = **−0.0035** < 0 is TRUE; OOS shift = 0.6892 − 0.2078 = **+0.4814** ≥ +0.20 is TRUE — **FIRES**. The sub-mode is a separate, independent SUSPICIOUS ground with no magnitude qualifier. The healthy ratio (0.84) means only that the ratio gate is absent; the sub-mode is the firing trigger.
2. **NULL-RESULT — ruled out.** NULL-RESULT (8.5) requires the trade roster bit-identical to /060. A universe swap fully replaces the LDO sub-roster with the ADA sub-roster — mechanically impossible; the /078 IS/OOS rosters contain 74/18 ADA trades absent from /060. Listed in the brief only for taxonomy completeness.
3. **NEGATIVE — ruled out.** NEGATIVE (8.2) requires IS Δ < −0.10 OR OOS Δ < −0.20. IS Δ −0.0035 > −0.10; OOS Δ +0.4814 > −0.20. Neither floor breached.
4. **PROMISING — ruled out, and fails independently.** PROMISING (8.1) requires IS shift ≥ +0.10 AND OOS shift ≥ +0.20 AND `frac_positive_paths` ≥ 0.50 AND not SUSPICIOUS. The IS gate fails on its own terms — IS shift −0.0035 < +0.10 — irrespective of SUSPICIOUS precedence. The eye-catching OOS +0.4814 cannot rescue PROMISING; it does not clear the independent IS gate.
5. **INERT — does not apply.** INERT (8.3) requires both shifts in-band AND not SUSPICIOUS; SUSPICIOUS fires, so INERT is blocked.

**→ SUSPICIOUS-OOS-DOMINANT.** This is the first canonical match in disjunctive order. SUSPICIOUS-OOS-DOMINANT axes never advance to the CONFIRMATION; they produce no edge ingredient — the OOS lift is uncorroborated by IS. **NO-MERGE. LDOUSDT is RETAINED. The universe-revision axis is CLOSED for cycle 2. BASELINE_V3.md is UNCHANGED (/059 canonical, tag `v0.v3-059`).**

## 4. The falsified hypothesis — ADA did not lift the IS aggregate

The brief Section 1 hypothesis: replace LDOUSDT with ADAUSDT to lift the IS aggregate monthly Sharpe without re-triggering the IS-up/OOS-down regime tension. Section 4.1 predicted IS Δ +0.13 to +0.33 (central +0.20). Section 4.2 set the explicit falsifier: **IS Δ < +0.10 → hypothesis falsified.**

**Observed IS Δ = −0.0035. The falsifier fired.**

The mechanism is precise, and it is NOT a wiring defect:

- **ADA DID trade actively.** ADA produced 74 IS trades vs LDO's 11 — well within the brief Section 4.3 predicted 50–90 range. The swap raised the trade rate as predicted; ADA is not an under-trader like LDO.
- **ADA's IS contribution IS positive.** ADA contributed +21.85 IS weighted_pnl with a 40.5% IS win rate. LDO contributed −1.66 IS weighted_pnl. ADA lifted the IS *total* PnL by roughly 45% (the IS monthly mean PnL rose +1.57 → +2.09, a +33% lift).
- **But the IS *Sharpe* stayed flat — because ADA's variance contribution matched its mean contribution.** The IS monthly std rose +6.59 → +8.83 (+34%) in lockstep with the +33% mean lift. A Sharpe is mean ÷ std; when both the numerator and denominator rise by the same proportion, the ratio is unchanged. The aggregate IS Sharpe moved −0.0035 — flat, not lifted.
- **BCH dominates the IS aggregate and absorbed ADA's contribution as added variance.** BCH contributed +78.34 of the +75.24 IS total weighted_pnl — ~76.9% of the IS aggregate (the /059 baseline figure is 95.76%; the swap-induced roster shifts the share). The portfolio monthly Sharpe is dominated by BCH's monthly PnL distribution. ADA's 74-trade participation entered the aggregate as a denominator driver, not only a numerator driver — so a symbol with a genuine positive standalone IS edge still produced zero aggregate IS-Sharpe lift.

**The T7 IS-edge screen did NOT transfer.** T7 screened ADA at +0.617 IS Sharpe vs LDO −0.550 — a +1.17 margin — on a coarse single-seed fixed-parameter proxy. That screen measures the per-symbol model *in isolation*. The production 3-seed walk-forward measures the portfolio monthly Sharpe across BCH+ADA+TRX, where BCH dominance pins the aggregate. The T7 screen correctly predicted ADA's positive *symbol-level* IS edge; it did not — and structurally could not — predict the portfolio-aggregate variance impact that kept the aggregate Sharpe flat. This is the key lesson for future universe-revision evidence: an IS-edge screen measures per-symbol Sharpe; it does not predict portfolio-aggregate Sharpe lift under incumbent (BCH) dominance.

## 5. The doubly-corroborated regime divergence — the +2.23-candle holding-time falsifier

**This is the key finding of the iteration.** /078's SUSPICIOUS-OOS-DOMINANT verdict is corroborated by a SECOND, independent falsifier — the added-vs-removed holding-time sub-channel — and that corroboration identifies the actual mechanism behind the OOS +0.48 lift.

**The brief Section 4.4 prediction and falsifier.** Per `feedback_v3_is_oos_regime_divergence.md` and Critic /076 Rec #2, the brief pre-registered an added(ADA)-vs-removed(LDO) roster-composition mean-duration sub-channel. T8 — the holding-time predictor — estimated the gap at **+0.38 candles** (ADA label-implied 6.42 vs LDO 6.04). The pre-registered falsifier: **added-vs-removed gap > +1.0 candle → the swap loads the IS/OOS regime factor via selection.**

**The production gap is +2.23 candles — the falsifier FIRED.** The actual production added-vs-removed mean-duration gap is **+2.226 candles** (ADA IS mean duration ~7.135 candles vs LDO IS mean 4.909) — 6× the T8 prediction of +0.38. The Critic independently recomputed it from the trade CSVs (duration = `(close_time − open_time) / 28,800,000` ms per 8h candle):
- **ADA IS timeout trades**: 5 ADAUSDT IS rows resolve `exit_reason = timeout`, each at exactly 21.0 candles (`close − open = 604,800,001 ms`).
- **LDO IS profile**: 11 LDOUSDT IS rows, **ZERO** with `exit_reason = timeout`; LDO IS durations {20, 4, 2, 1, 1, 2, 7, 3, 2, 4, 8} → mean = 54/11 = **4.909 candles**.
- **Production gap = 7.135 − 4.909 = +2.226 ≈ +2.23 candles** vs the T8 label-implied +0.378 — the Section 4.4 sub-channel falsifier (threshold +1.0 candle) **FIRES**. Even excluding the 5 timeout trades, the non-timeout gap (6.13 − 4.91 = +1.22) still clears +1.0.

**The mechanism.** Per `feedback_v3_is_oos_regime_divergence.md`, v3's IS window (2022-09 → 2025-03) is a mixed bear/recovery/bull/chop regime that PENALIZES longer-held trades, and the OOS window (2025-03 → 2026-05) is a persistent BCH/LDO/TRX uptrend that REWARDS longer-held trades. ADA's roster is systematically +2.23 candles longer-held than LDO's was — driven by the 5 ADA IS timeout trades at 21.0 candles that LDO never incurred. So /078's OOS +0.48 lift is the **holding-time-extension regime-divergence mechanism (the /076 trade-selection sub-channel c) arriving via the universe swap** — the swap replaced an entire symbol's model with another symbol's model whose roster is duration-loaded. This is the SAME structural factor as /065/071/073/076, reached by a new vector.

**SUSPICIOUS is therefore DOUBLY corroborated:**
1. The OOS-DOMINANT sub-mode fires (IS shift < 0 AND OOS shift ≥ +0.20).
2. The added-vs-removed holding-time channel falsifier fires (+2.23 > +1.0).

The OOS lift is confirmed **uncorroborated regime-luck, not robust edge.** This is reinforced by the per-symbol OOS attribution: **ADA's own OOS is weak** — 18 trades, 27.8% win rate, `net_pnl_pct` −14.56%, `weighted_pnl` only +0.4230. The aggregate OOS lift to +0.6892 is dominated by the elimination of LDO's −18.41 OOS `weighted_pnl` drag plus ADA's longer-held trades catching regime-luck in the OOS uptrend — NOT by ADA producing edge. BCH (+1.9078) and TRX (+24.7184) are bit-frozen; the entire delta is the LDO→ADA slot.

## 6. The EDA T6 escapability premise was INCOMPLETE — a recorded diagnostic lesson

EDA T6 — the escapability bound — was the load-bearing axis justification. It argued LDOUSDT is the one in-universe symbol whose drag is NOT regime-split-correlated (LDO bull-SHORT weak in BOTH windows: IS −1.16 AND OOS −12.58), so removing LDO lifts IS without the IS-up/OOS-down tension. /078 falsified the *conclusion* — the OOS lifted, the IS did not, and the holding-time falsifier fired.

**T6's reasoning about LDO was NOT wrong.** T6's claim concerned the *removed* symbol's regime-cleanliness, and removing LDO did indeed not re-trigger the tension *through LDO*. The defect: **T6 reasoned exclusively about the REMOVED symbol — the regime-loading came from the ADDED symbol.** ADA's longer-held roster (the +2.23-candle channel, the 5 ADA IS timeout trades) loaded the regime factor. T8 was the QR's attempt to bound the added-symbol channel — but T8's label-implied first-touch simulation used **screen-grade fixed barrier parameters** and predicted +0.38 candles, missing the production +2.23 by 6×, because the production walk-forward uses **Optuna-tuned timeout parameters** that produced 5 ADA timeout trades the fixed-parameter screen could not foresee.

This is a **recorded diagnostic lesson, not a methodology failure.** The QR's brief Section 7 honestly caveated exactly this gap: *"T6 is evidence that the removal is regime-clean; it is not a proof about the added symbol."* The /076 Critic had already flagged the same gap. The QR did pre-register the added-vs-removed sub-channel falsifier (Section 4.4) — it just used a screen-grade parameterization to populate the prediction. The lesson for future universe-revision axes: an added-symbol holding-time falsifier must be computed under the production Optuna-tuned parameterization (or with an explicit duration-distribution band wide enough to admit the timeout-trade tail) — a screen-grade fixed-parameter proxy is structurally biased low and gives false holding-time-orthogonality reassurance.

## 7. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `75f4d42`. A single-round full review; the verdict is FINAL. The MERGE verdict CERTIFIES the SUSPICIOUS-OOS-DOMINANT classification clean and the diagnostic lessons sound. It is a closeout-integrity certification, NOT an advancement — a SUSPICIOUS-OOS-DOMINANT axis never advances to the CONFIRMATION bundle.

- **All 8 Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — the load-bearing concern, the T7 IS-edge screen that selected ADA, was traced end-to-end: `is_months` are built strictly as months with `start_time < OOS_CUTOFF_MS`, the training window terminates at an embargo-22-purged boundary, the monthly-PnL Sharpe is computed on that IS-only series; the screen never reads a bar at or past `OOS_CUTOFF_MS` for any candidate, ADA included; `build_btc_monthly_regime` applies `.shift(1)` before the rolling SMA-270. Check 2 (embargo) PASS — `walk_forward.py:113` carries the `e149e9d` fix (`train_end_ms = test_start_ms - embargo_ms`), `compute_embargo_candles = 22`, REQUIRED_GAP = 66. Check 3 (DSR/PSR/PBO) PASS-equivalent — PBO=0.1277 PASS, DSR/DSR_relative_B4 informational at EXPLORATION; `frac_positive_paths = 0.733` clears the 0.55 gate. Check 4 (IC) PASS — no feature family added or removed; the 14-feature anchor stack is unchanged, so Check 4 has nothing to flag. Check 5 (ADF) PASS — 82.7% of per-month cells stationary; non-stationary rows concentrate in thin early-history months. Check 6 (Pareto) PASS — Gate 10-Pareto retired under the unified architecture; `frac_positive_paths = 0.733` PASS. Check 7 (reproducibility) PASS — explicit 14-element `feature_columns` list, ensemble seeds literal, PnL spot-checks recompute on both directions; **BCH/TRX OOS bit-stability independently verified** (BCH +1.9078/37, TRX +24.7184/54 bit-identical to /077). Check 8 (hypothesis-implementation alignment) PASS — exactly one code change (`V3_MODELS` LDOUSDT→ADAUSDT) plus the `ITERATION_LABEL` bump and pre-flight assertion-site updates; no scope creep. A falsified hypothesis with a faithful implementation is a clean negative data point, not a Check-8 failure.
- **Foundation Audit (Boot Steps 9-11) CLEAN** — `ITERATION_LABEL = "v3-078"`, `V3_MODELS` = BCH/ADA/TRX (LDO removed, ADA added, 3-symbol universe preserved), walk-forward embargo fix intact, `efficiency_ratio_50`/`range_efficiency_50` ban intact at six runner sites, `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` asserted, sacred constants `OOS_CUTOFF_DATE = "2025-03-24"` / `TRAINING_MONTHS = 24` confirmed.
- **§11 Anti-Pattern Static Scan CLEAN** — the six remaining `LDOUSDT` references in `run_baseline_v3.py` are all comments (line 1582's stale `# LDOUSDT returns (1.5, 0.75)` has zero behavioral effect — `V3_ATR_MULTIPLIERS_PER_SYMBOL` is empty); the pre-flight smoke loops iterate `("BCHUSDT", "ADAUSDT", "TRXUSDT")`; `feature_columns` is an explicit list, never None; no `start_time` manipulation, no OOS-cutoff drift, no hardcoded-Sharpe injection, no cross-track import.
- **Check 9 (Symbol Exclusion) PASS** — `V3_EXCLUDED_SYMBOLS` (11 symbols: BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR, MKR) does NOT contain ADAUSDT — the swap-in is legal. LDOUSDT is not in the set either — LDO is removed from `V3_MODELS` only, still an allowed symbol.
- **Three Critic Adjudications**: #1 SUSPICIOUS-OOS-DOMINANT CERTIFIED (the sub-mode fires on its independent ground; PROMISING fails its own +0.10 IS gate); #2 the +2.23-candle holding-time falsifier VERIFIED — SUSPICIOUS DOUBLY CORROBORATED (recomputed from the trade CSVs: 5 ADA IS timeouts at 21.0 candles, LDO zero timeouts, gap +2.226); #3 the T6 escapability premise RECORDED as INCOMPLETE, not wrong (correct about LDO, silent about ADA's production behavior; the QR's honest Section 7 caveat means the verdict is not charged as a methodology failure).

## 8. Hypothesis check — the QR pre-registered SUSPICIOUS at ≈43%; it FIRED, and the calibration was sound

The brief Section 7 pre-registered three plausible failure modes — INERT-AT-EXPLORATION (BCH dominance absorbs the ADA lift), SUSPICIOUS-OOS-DOMINANT (ADA's OOS blind spot), and NEGATIVE (the screen proxy does not transfer) — and **floored the SUSPICIOUS probability at the running cycle-2 base rate of ≈ 43%** (3 SUSPICIOUS-OOS-DOMINANT of the first 7 EXPLORATIONs: /071, /073, /076) per Critic /076 Rec #3.

**SUSPICIOUS-OOS-DOMINANT fired — the pre-registered weight was vindicated.** This is the correct calibration outcome, and it is worth recording precisely *why*:

- The QR did **not** float SUSPICIOUS below the base rate. The brief explicitly reasoned: a universe swap is not a bit-identical roster (the /077 PASSIVE-DIAGNOSTIC's sub-base-rate justification does not apply), and ADA's OOS behaviour is genuinely unknown — there is no conditional-orthogonality *proof* that ADA cannot load the regime factor, only the T6 argument that LDO (the *removed* symbol) is regime-clean. The QR wrote, verbatim: *"T6 is evidence that the removal is regime-clean; it is not a proof about the added symbol."*
- That honest hedge is exactly what the /076 calibration discipline rule demanded — Section 7 SUSPICIOUS must be floored near the running cycle base rate unless a *conditional*-orthogonality proof justifies deviating below it. The QR had no such proof for the *added* symbol, held SUSPICIOUS at ≈43%, and the outcome fired. This is the opposite of the /076 calibration miss (where the brief weighted SUSPICIOUS at ≈3% on a marginal-orthogonality narrative and was falsified).
- The QR's *central* estimate leaned INERT/PROMISING (the IS-edge screen was strong) — and that central estimate was wrong (the result is SUSPICIOUS-OOS-DOMINANT). But the pre-registered *failure-mode weight* was correctly floored, the predicted sub-mode signature ("IS Δ < 0, OOS Δ ≥ +0.20") matched the observed outcome exactly, and the brief carried the Section 7 honest caveat that made the verdict a recorded diagnostic lesson rather than a methodology failure.

**Verdict on the calibration: sound.** The Section 7 ≈43% floor was respected, the sub-mode signature was correctly pre-registered, and the honest "not a proof about the added symbol" caveat was the load-bearing hedge. The cycle-2 SUSPICIOUS base rate is now **4 of 8** (50%) — /071, /073, /076, /078.

## 9. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). A SUSPICIOUS-OOS-DOMINANT EXPLORATION produces no edge ingredient, does not advance to the CONFIRMATION, and an EXPLORATION cannot update the baseline regardless. **No new tag issued. No BASELINE_V3.md edit at this closeout.**

**LDOUSDT is RETAINED.** The universe-revision axis is CLOSED for cycle 2. At /079's setup, `V3_MODELS` reverts from BCH/ADA/TRX back to **BCH/LDO/TRX** (the /060 anchor universe). This is noted for the /079 setup; no code is edited at this closeout.

## 10. Critic Recommendations carried forward

For the cycle-2 CONFIRMATION (iter-v3/081) and future universe-revision axes. This iteration's verdict is final; a SUSPICIOUS-OOS-DOMINANT axis does not advance.

1. **Universe-revision axes need a production-parameterized added-symbol holding-time band.** The T8 label-implied +0.38-candle prediction missed the production +2.23 by 6× because it used screen-grade fixed barrier/Optuna parameters. Any future swap-target screen must either run the duration estimate under the production Optuna-tuned timeout regime or pre-register a duration-distribution band wide enough to admit the timeout-trade tail — a screen-grade fixed-parameter proxy is structurally biased low and gives false holding-time-orthogonality reassurance.

2. **An IS-edge screen measures per-symbol Sharpe, not portfolio-aggregate Sharpe lift under BCH dominance.** T7 correctly screened ADA at +0.617 per-symbol IS Sharpe, but the production 3-seed walk-forward aggregate is dominated by BCH (~77% of IS `weighted_pnl`); ADA's added IS variance (+34% monthly std) matched its added mean (+33%), pinning the aggregate IS Sharpe flat. Future swap evidence must include a portfolio-aggregate IS-Sharpe sensitivity projection conditioned on the incumbent symbol's IS share — not only the candidate's standalone IS edge. This is the BCH-IS-concentration fragility flag from the /059 baseline, now empirically confirmed for a universe swap.

3. **The cycle-2 CONFIRMATION (iter-v3/081) cannot bundle the LDO→ADA swap as an edge ingredient.** /078 is the FOURTH cycle-2 SUSPICIOUS-OOS-DOMINANT data point (after /071, /073, /076). Per `feedback_v3_strict_both_is_oos_baseline.md`, the CONFIRMATION's BOTH-must-improve gate would reject the swap on the flat IS regardless, and the doubly-corroborated regime-luck OOS lift is non-compoundable. **Cycle 2 has now exhausted feature (T3), meta-labeling M2 (T5), AND universe-revision axes against the LDO structural-weakness problem.** The CONFIRMATION brief should treat LDO drag as a standing unresolved constraint, and cycle-3 axis priorities should pivot away from all three exhausted categories.

## 11. Next Iteration Ideas

### Cycle 2 progress — 8/10 EXPLORATIONs done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | INERT-AT-EXPLORATION |
| #6 | /076 | NEW FEATURE (`range_efficiency_50`, Kaufman path efficiency) | SUSPICIOUS-OOS-DOMINANT |
| #7 | /077 | PASSIVE-DIAGNOSTIC (`conditional_orthogonality.csv` + `range_efficiency_50` revert) | INERT-AT-EXPLORATION |
| #8 | /078 | UNIVERSE REVISION (replace LDOUSDT with ADAUSDT) | **SUSPICIOUS-OOS-DOMINANT** |
| #9-#10 | /079-/080 | TBD per QR EDA — see candidates below | — |

**Honest reckoning.** Cycle 2 is 8/10 done and has produced **0 clean PROMISING** — 4 SUSPICIOUS-OOS-DOMINANT (/071, /073, /076, /078), 1 NEGATIVE (/072), 3 INERT (/074, /075, /077). The cycle has produced two load-bearing methodology corrections (the /077 anchor-staleness finding, the /077 reframing finding) and one extended cycle-level finding (/078 — a universe swap is a fourth vector for the IS/OOS holding-time regime-loading factor) — but zero edge ingredients.

**The Critic verdict is explicit: feature (T3), meta-labeling M2 (T5), AND universe-revision axes are all exhausted against the LDO structural-weakness problem.** The standing structural problems are unchanged: LDO directional weakness (LDO has dragged every cycle-1 and cycle-2 iteration), the bull-month entry-discrimination drag (localized by /077 EDA T1: IS_BULL Sharpe +0.4100 / 33% positive vs IS_BEAR_CHOP +1.2909 / 47% positive), and now the empirically-confirmed BCH IS-concentration fragility (a positive-edge swap-in symbol washes against BCH's ~77% IS-PnL dominance).

### iter-v3/079 (cycle 2 #9) axis candidates — seeding only

Per `feedback_v3_axis_selection_quant_discipline.md`, the /079 actual axis is QR-EDA-driven and will be selected fresh in /079 Phase 1-2 with a committed `analysis/iteration_v3-079/*.py` EDA script; the brief Section 2 must contain EDA-derived numerical tables. The candidates below seed the QR EDA only. Per `feedback_v3_structural_over_knob_exploration.md`, the QR should favor a structural axis (NEW model arch > NEW labeling > NEW risk primitive) over a knob axis — and per the /078 Critic, must avoid the three exhausted categories (feature, M2, universe revision).

1. **A NEW model-architecture axis targeting the BCH IS-concentration fragility (HIGHEST — directly motivated by the /078 Critic Rec #2).** /078 empirically confirmed that BCH's ~77% IS-PnL dominance pins the aggregate IS Sharpe — a positive-edge change to any other symbol washes out. The structural fix is not another symbol or feature; it is an architecture that prevents one symbol from dominating the aggregate Sharpe. Candidates: (a) a per-symbol-variance-normalized aggregation in the portfolio Sharpe computation (each symbol's monthly PnL contribution scaled to unit variance before aggregation — a risk-parity-style weighting); (b) inverse-volatility position sizing across the three symbols so BCH's larger PnL swings are down-weighted. NOTE: any sizing change must be screened for the holding-time channel — a sizing change does not lengthen duration (a size scalar deletes no trade, per the /075 finding), so this is structurally holding-time-orthogonal, but the brief Section 2 must still pre-register the holding-time predictor per `feedback_v3_is_oos_regime_divergence.md`. This is a category-2 (NEW model arch) structural axis, not a knob.

2. **A NEW labeling-architecture axis the QR has not yet exhausted (SECOND).** /072 tested fixed-horizon-21 labeling (NEGATIVE) and /071 tested meta-labeling (SUSPICIOUS). A labeling axis the cycle has NOT touched: a trend-scanning / first-significant-move label (López de Prado AFML, the trend-scanning method), or a volatility-adjusted barrier where the TP/SL are set per-symbol from a *past-only* realized-vol estimate rather than a global ATR multiplier. The binding constraint: the brief Section 2 must pre-register the holding-time predictor AND demonstrate the labeling change does not extend mean/median duration (a barrier-rebalancing-toward-TP labeling change loads the regime factor per /073 — it must be rejected at brief stage if it does).

3. **A holding-time-orthogonal, selection-orthogonal NEW risk primitive (THIRD — lower priority).** /074 (regime-conditional kill switch) and /075 (BTC-trend position-SIZE de-rate) were both INERT — too few trades affected, or IS traded for OOS ~1:1. A primitive that has NOT been tried: a per-trade conviction-weighted sizing primitive driven by the M1 model's *prediction-margin* (not a macro BTC classifier — the /075 trap was a post-gate macro classifier). Lower priority because the risk-primitive axis has produced two consecutive INERT results in cycle 2.

**The /081 CONFIRMATION — what it will validate.** Cycle 2 has produced **zero edge ingredients** through 8 EXPLORATIONs. There is no PROMISING component to bundle. By direct analogy to cycle 1's /070 CONFIRMATION — which was a NO-MERGE re-validation of the /059 baseline because cycle 1's EXPLORATIONs produced no bundle-able edge — **the /081 CONFIRMATION is, on current evidence, a /059-baseline multi-seed re-validation**: a `--seeds 2` run of the canonical /059 configuration to confirm BASELINE_V3.md's IS +1.0894 / OOS +0.5791 still reproduces under the current code state (with the /077 anchor-staleness decomposition annotated). If /079 or /080 produce a clean PROMISING in the two remaining slots, that component bundles into /081; if both go SUSPICIOUS/INERT/NEGATIVE, /081 is the re-validation. The cycle-2 CONFIRMATION brief should be written to handle either branch, and should treat the LDO structural-weakness problem as a standing unresolved constraint carried into cycle 3 — with cycle-3 priorities pivoting away from the three exhausted categories (feature, M2, universe revision) toward the BCH IS-concentration / portfolio-aggregation architecture problem that /078 surfaced.

**Hard constraints on /079** (carried from prior closeouts + the /078 Critic):
- **Anchor against the re-anchored current-code /060-config baseline (IS +0.8236 / OOS +0.2078)**, NOT the frozen /060 +0.8325/+0.1403; the /079 brief Section 0 must state this explicitly with the −0.0089/+0.0675 decomposition annotated (per the /077 anchor-staleness cycle-note).
- `V3_MODELS` reverts to **BCH/LDO/TRX** at /079's setup (LDO retained; the universe-revision axis is closed).
- Holding-time-orthogonal — the brief Section 2 must include the holding-time-effect predictor (`feedback_v3_is_oos_regime_divergence.md`) WITH the added-vs-removed roster-composition mean-duration sub-channel; for a universe-touching axis, the sub-channel band must be computed under production Optuna-tuned parameters, not a screen-grade proxy (Critic /078 Rec #1).
- Pre-register the OOS/IS Sharpe ratio bound (>3.0 → SUSPICIOUS) AND the OOS-DOMINANT sub-mode (IS shift < 0 AND OOS shift ≥ +0.20) in Section 4/8 per `feedback_v3_oos_is_ratio_gate.md`, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio definition.
- Pre-register a behavioral-effect predictor with a falsifier (`feedback_v3_axis_saturation_predictor.md`).
- The Section 7 SUSPICIOUS probability must be floored near the running cycle-2 base rate (now 4/8 = 50%) unless the brief presents a proof strong enough to justify deviating below it (Critic /076 Rec #3).
- If the axis is a NEW feature, screen it against the /077 `conditional_orthogonality.csv` map — a near-zero MARGINAL correlation is necessary but NOT sufficient; the CONDITIONAL (model-split-allocation) correlation is the binding test. (But per the /078 Critic, the NEW-feature axis is exhausted for the LDO problem — prefer a structural axis.)
- The Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`), the regime-conditional kill switch (primitive 9), and the LDO→ADA universe swap are all CLOSED — do not re-propose any of them.

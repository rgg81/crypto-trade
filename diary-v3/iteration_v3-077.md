# iter-v3/077 — Cycle 2 #7 EXPLORATION / PASSIVE-DIAGNOSTIC (`conditional_orthogonality.csv` instrumentation + /076 `range_efficiency_50` revert) / INERT-AT-EXPLORATION

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #7 of 10; PASSIVE-DIAGNOSTIC — report-instrumentation-only axis, plus the mandatory revert of /076's 15th feature back to the /060 14-feature anchor)
**Axis**: a new `_write_conditional_orthogonality()` report function emitting `conditional_orthogonality.csv` — the Critic /076 Rec #1 instrument (correlates each baseline feature's per-IS-month model-split gain-importance share against the BTC-regime label). Mandatory secondary edit: REVERT /076's `range_efficiency_50` — `V3_FEATURE_COLUMNS` 15 → 14, restoring the /060 anchor stack. No model, labeling, risk-gate, seed, or Optuna change.
**Verdict**: EXPLORATION-MERGE per Critic FINAL `46e9fe9` — OVERALL=MERGE; **INERT-AT-EXPLORATION classification certified clean**. A closeout-integrity / methodology certification, NOT an advancement.
**Classification**: **INERT-AT-EXPLORATION** per brief Section 8.3 — both shifts inside the noise bands (IS Δ -0.0089 ∈ ±0.10; OOS Δ +0.0675 ∈ ±0.20), the roster is NOT bit-identical to /060 (the brief's predicted NULL-RESULT did not hold), and SUSPICIOUS does not fire (OOS/IS ratio 0.2523 ≪ 3.0; OOS-DOMINANT sub-mode does not fire — OOS shift +0.0675 < +0.20).
**Advancement**: does NOT advance to the cycle-2 CONFIRMATION bundle — a PASSIVE-DIAGNOSTIC produces no edge ingredient. The `conditional_orthogonality.csv` instrumentation lands as accretive tooling for /078-/080.
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`). **No new tag issued.** One BASELINE_V3.md edit at this closeout: a note in Measurement Discipline that the /060 EXPLORATION-MODE-REFERENCE anchor is STALE and that cycle-2 EXPLORATIONs /078+ re-anchor against /077's current-code /060-config baseline.
**Branch**: `iteration-v3/077`

---

## 1. What was done

iter-v3/077 is the SEVENTH EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION (/081 or later) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is a **PASSIVE-DIAGNOSTIC**: a new runner function `_write_conditional_orthogonality()` that emits `conditional_orthogonality.csv`. The function is pure post-backtest report emission — it runs after `run_backtest()` returns, reads the already-trained `model_pairs` gain-importances plus a committed EDA CSV (`T3_conditional_orthogonality.csv`, EDA SHA `313d3c0`), writes one CSV, and touches no model, feature, labeling, risk-gate, Optuna, or seed code path. The CSV is the Critic /076 Rec #1 instrument — the /076 closeout established that *marginal* regime-orthogonality of a feature does not bound the model's *conditional* use of it, and called for a conditional-orthogonality map; /077 builds that map.

The axis carries a **mandatory secondary edit**: /076's `range_efficiency_50` (the Kaufman path-efficiency 15th feature, SUSPICIOUS-OOS-DOMINANT, axis CLOSED) was reverted — `V3_FEATURE_COLUMNS` count 15 → 14, back to the established /060 anchor stack. This is a revert, not a second varied axis. The `efficiency_ratio_50` literal-name ban stays intact.

The brief Section 4.1 **PREDICTED the trade roster would be bit-identical to /060** — same 14-feature stack, same labeling, same risk gates, same `ENSEMBLE_SEEDS`, same Optuna search → deterministically identical trained models → an identical roster. The intended classification was NULL-RESULT (bit-identical roster, zero metric movement). The brief's Section 8.3 also pre-registered the contingency: if a benign non-determinism perturbs the roster without moving the metrics, the classification is INERT-AT-EXPLORATION (Section 7's ≈4% tail).

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS outer=42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Anchor for EXPLORATION-mode comparison: iter-v3/060 EXPLORATION-MODE-REFERENCE (frozen value IS +0.8325 / OOS +0.1403 — see Section 4 for why this anchor is now STALE).

Commit chain: EDA `313d3c0` → research brief `77d0b62` (Section 10 SHA-backfill `e12cf99`) → setup `30cda98` → Phase 5.5 gate `caed50d` (PASS) → stale-ADF-check removal `20c65cd` (orchestrator code fix — Critic Rec #3 other half) → engineering report `21ab2e5` → Critic review `46e9fe9`.

## 2. Results — vs /060 EXPLORATION-mode anchor (the FROZEN anchor)

| Metric | /060 frozen anchor | /077 actual | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.8236** | **-0.0089** |
| OOS monthly Sharpe | **+0.1403** | **+0.2078** | **+0.0675** |
| OOS/IS monthly Sharpe ratio | 0.1685 | **0.2523** | — |
| IS n_trades | 159 | 159 | **0** |
| OOS n_trades | 102 | 103 | **+1** |
| PBO mean | 0.1278 | 0.1278 | **0** |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0 |
| DSR (legacy) | — | 0.0 | informational FAIL (EXPLORATION-mode artifact) |
| PSR | — | 0.9987 | informational (EXPLORATION-mode) |
| DSR_relative_B4 | — | 0.0512 | informational FAIL (EXPLORATION-mode artifact) |
| n_trials (Optuna total) | 315 | 315 | 0 |
| n_eff | 19 | 19 | 0 |

The headline: **the metrics moved trivially.** IS slipped -0.0089, OOS lifted +0.0675, both deep inside the INERT noise bands (±0.10 IS / ±0.20 OOS). The IS `(symbol, open_time)` trade roster is **bit-identical to /060** — 159 = 159 keys, 0 added, 0 removed. The OOS roster has +1 trade. PBO and `frac_positive_paths` are bit-identical to /060 — the CPCV path-return proxy is weight-factor-independent, so a bit-identical-key roster produces a bit-identical CPCV.

DSR=0.0 / DSR_relative_B4=0.0512 are **informational at EXPLORATION** per `feedback_v3_dsr_mode_artifact.md` — EXPLORATION-mode `n_trials=315` is not comparable to CONFIRMATION-mode `n_trials=1050`, and these edge axes do not trigger a BLOCK for an EXPLORATION. PBO=0.1278 — the one Check-3 axis meaningful at any mode — PASSES.

## 3. The bit-identity prediction was falsified — benignly, and fully root-caused

The brief Section 4.1 over-claimed: it asserted the bit-identity prediction was "not a confidence interval — it is an algebraic identity." That claim was wrong. The roster perturbed slightly. But the perturbation is fully explained, with zero residual, and is entirely external to /077's config change. The Critic independently diffed `reports-v3/iteration_v3-077/` against `reports-v3/iteration_v3-060/` and confirmed every claim below.

**(A) The IS roster IS bit-identical on keys.** The IS `(symbol, open_time)` key set is bit-identical to /060 — 159 = 159, 0 added, 0 removed. `in_sample/per_symbol.csv` trade counts are byte-identical (BCH 73, LDO 11, TRX 75). The brief's *qualitative* claim — "/077 selects the same trades as /060" — is correct. The *quantitative* "algebraic identity" framing is what failed.

**(B) The IS divergence: 13 TRX `weight_factor` values floored at 0.5.** 13 TRX IS rows differ from /060 — and only in `weight_factor`, every floored value landing at exactly 0.5 (e.g. TRX `1646467199999`: wf 0.42 → 0.50; `1659513599999`: wf 0.36 → 0.50). Non-floored TRX rows and all BCH/LDO rows are bit-identical. **Root cause: `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}`** — introduced at **iter-v3/061**, sixteen iterations after /060, with an in-code provenance comment (`run_baseline_v3.py:1689-1693`, dated to /061 per QR EDA SHA `d198b25`). This is genuine 16-iteration code accretion, external to /077's setup. It moves 13 IS TRX trades (4 wins, 9 losses) → net IS weighted_pnl -0.1616 → IS monthly Sharpe -0.0089.

**(C) The OOS +1 trade is the data-extent artifact.** /060's last OOS trade is TRX `1778572799999` resolving `end_of_data` (pnl +0.21); /077 has the SAME key resolving as `take_profit` (pnl +1.83) — the live data now extends past where /060's CSV ended. Plus one additional `(LDOUSDT, 1778716799999)` `end_of_data` trade absent from /060. This is the identical data-extent pattern certified by the /074 and /075 Critics (LDO end_of_data ~2026-05-14).

**Verdict on the miss (Critic Rec #2): a process defect, not a BLOCK.** The brief asserted algebraic certainty over a config it had not git-verified frozen since /060. But the SAME brief, Section 8.3, pre-registered this exact outcome shape as a LOCKED classification gate, the disjunctive evaluation resolved cleanly to INERT, and the QE root-caused the perturbation to two fully-explained benign causes (full wpnl reconciliation: A +1.3129 + B +0.8119 + C +0.5943 = +2.7191 OOS; IS -0.1616 from the TRX floor). A BLOCK is reserved for a wiring defect, a look-ahead, or an un-pre-registered failure mode — none present. The corrective: future bit-identity predictions must be backed by a git-diff of every behavior-affecting config (`RiskV2Config`, ATR multipliers, vol-scale floors/ceilings, seeds) between the anchor commit and HEAD, not by the assumption that "no axis change" implies "no roster change."

## 4. The /060 anchor staleness finding — the load-bearing methodology result

This is the iteration's principal deliverable.

**/077 is the first iteration since /060 to run the exact /060 14-feature config with no axis.** /071-/076 each varied a single axis on top of the /060 stack; /077 reverts /076's feature and adds only a report-emission function — so /077's backtest IS the /060 configuration, run on current code and current data. **It does not reproduce the frozen /060 anchor.**

| Anchor | IS monthly Sharpe | OOS monthly Sharpe |
|---|---:|---:|
| /060 FROZEN (EXPLORATION-MODE-REFERENCE, used by /071-/076) | +0.8325 | +0.1403 |
| **/060-config CURRENT-CODE (established by /077)** | **+0.8236** | **+0.2078** |

The two differ. The decomposition is exact and additive:

- **IS code-drift component: -0.0089.** Entirely the iter-v3/061 TRX `vol_scale_floor=0.5` acting on 13 IS TRX trades (Section 3B). This is a **permanent, deterministic** code-state difference, not noise. It does not grow or shrink — it is a fixed offset that any /060-config run on post-/061 code will carry.
- **OOS data-extent component: +0.0675.** Dominated by the 2026-05 OOS month that post-dates /060's data fetch (Section 3C). Data extent grows **monotonically** with calendar time — every later iteration sees slightly more OOS data than /060 did.

The current-code /060-config OOS of ≈ +0.21 is independently corroborated: the /074 diary reports /074's OOS at +0.2090, and /074/075 both landed near +0.21 on the 14-feature stack. The frozen +0.1403 OOS has been stale for several iterations.

**Why /071-/076 classifications are robust, not invalidated (Critic-verified).** /071-/076 all computed deltas against the frozen +0.8325/+0.1403. The drift is small relative to the classification bands: the IS code-drift (-0.0089) is an order of magnitude inside the INERT IS noise band (±0.10); the OOS data-extent drift (+0.0675) is well inside the ±0.20 OOS band. /071/073/076 were classified SUSPICIOUS by the OOS/IS *ratio* gate (4.51 / 6.85 / 15.04) — a ±0.07 OOS shift cannot move a ratio across the 3.0 boundary for those magnitudes. /074/075 were INERT by noise-band shifts that already absorbed the same drift. **No cycle-2 classification flips under the staleness.**

**Why the cycle-2 CONFIRMATION is unaffected.** The CONFIRMATION (iter-v3/081+) MERGE gates anchor on `BASELINE_V3.md` /059 — the canonical unified-architecture numbers, tag `v0.v3-059`. The /060 EXPLORATION-MODE-REFERENCE is an intra-cycle delta anchor only and never feeds the CONFIRMATION gate.

**The re-anchoring decision for /078+ (Critic Rec #1 — formally adopted here).** Cycle-2 EXPLORATIONs **/078, /079, /080 anchor against the current-code /060-config baseline established by /077 — IS +0.8236 / OOS +0.2078** — NOT the frozen /060 +0.8325/+0.1403. The -0.0089 (code-drift) / +0.0675 (data-extent) decomposition is recorded. **This is a methodology correction — a stale anchor replaced by the freshest reproducible no-axis run of the canonical config — not cheating.** It does not shift the OOS-cutoff, does not trim a start date, and does not change the measurement window; it corrects the *reference value* against which intra-cycle deltas are reported. Per-iteration data-extent drift from /077 onward is small (iterations run days apart), so /078-/080 deltas against the /077 anchor will be cleaner than /071-/076's deltas against /060 were. The classification noise bands (±0.10 IS / ±0.20 OOS) remain interpretable under the corrected anchor.

## 5. The reframing finding — the "IS bear/chop drag" was mis-localized

The EDA delivered a second load-bearing finding. EDA test T1 (`T1_regime_stratification.csv`) stratifies /060's IS monthly PnL by a **per-calendar-month BTC-regime label** — a month is BULL if ≥50% of BTC 8h bars have `close[t-1] > SMA_270[t-1]` (`build_btc_monthly_regime`, with `.shift(1)` before the rolling SMA — past-only).

| IS stratum (per-month BTC-regime) | Monthly Sharpe | Months | % positive |
|---|---:|---:|---:|
| IS_BEAR_CHOP | **+1.2909** | 15 | 47% |
| IS_BULL | **+0.4100** | 18 | 33% |

**The IS drag is in the BULL months, not bear/chop.** /074, /075, and /076 all targeted "the IS bear/chop drag" — but they used the *strategy's own endogenous trade-level regime tag*, a label conditioned on where the strategy chose to trade and how those trades resolved (partially circular when used to stratify performance). The per-calendar-month BTC-trend label is **exogenous to the strategy** — computed purely from BTCUSDT OHLCV — and the Critic certified it methodologically superior for exactly that reason. The two labels disagree, and the exogenous one is the correct instrument.

**Conclusion: three cycle-2 iterations (/074, /075, the /076 framing) optimized against the wrong stratum.** The structural IS drag is the bull months, where the strategy under-trades the tape. The EDA T6 escapability synthesis sharpens the diagnosis: win/loss duration ratio 2.08, 64% stop-loss exits, bull-month WR 32.7% vs bear/chop WR 43.6% — the IS problem is a **directional-quality / entry-discrimination** problem in bull regimes, not a holding-time or position-sizing problem in bear/chop.

## 6. The conditional-orthogonality deliverable

The PASSIVE-DIAGNOSTIC axis produced `conditional_orthogonality.csv` — the Critic /076 Rec #1 instrument, now built and available for /078-/080. The CSV is a hybrid: PART A is the runner's last-walk-forward-month gain-importance share per feature (a degenerate single-point map — `lgbm._train_for_month` clears `self._models` each month, so only the final month survives to report time; correctly labeled supplementary); PART B is the full per-IS-month map copied verbatim from the committed EDA `T3_conditional_orthogonality.csv`. The Critic verified PART B byte-matches the EDA file.

**The map: 4 of 14 baseline features are conditionally regime-loaded.** Each feature's per-month gain-importance SHARE was correlated against the BULL=1 indicator over IS-window months. Above the a-priori 0.35 ceiling:

| Feature | max \|corr\| with BTC-regime label |
|---|---:|
| `btc_ret_14d` | 0.4803 |
| `hurst_diff_100_50` | 0.4416 |
| `max_dd_window_50` | 0.4339 |
| `range_realized_vol_50` | 0.3704 |

`regime_momentum_signed_5d` — the one validated cycle-1 edge ingredient — is clean at 0.2092. Any NEW feature proposed in /078-/080 must be screened against this map: a feature whose conditional model-split allocation correlates with the regime label is a /076-style regime-loading risk even if its marginal value distribution is orthogonal.

## 7. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `46e9fe9`. A single-round full review; the verdict is FINAL. The MERGE verdict certifies the INERT-AT-EXPLORATION classification clean and the diagnostic deliverables (conditional-orthogonality map, reframing finding, anchor-staleness finding) sound. It is a closeout-integrity / methodology certification, NOT an advancement — a PASSIVE-DIAGNOSTIC produces no edge ingredient.

- **All 8 Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — `_write_conditional_orthogonality` is post-backtest report emission and cannot introduce look-ahead; the EDA's per-month importance training is embargo-22-disciplined with the unformed-label tail dropped; `build_btc_monthly_regime` applies `.shift(1)` before the rolling SMA-270. Check 2 (embargo) PASS — REQUIRED_GAP=66, embargo=22, walk-forward fix intact; no leakage surface added by a report-emission axis. Check 3 (DSR/PSR/PBO) PASS-equivalent — PBO=0.1278 PASS, DSR/DSR_relative_B4 informational. Check 4 (IC) PASS — /077 adds no new feature family, so the new-vs-existing IC gate is not triggered; the 14×14 `ic_matrix.csv` has no `range_efficiency_50` column (correctly reverted). Check 5 (ADF) PASS-equivalent — 82.0% stationary, non-stationary rows dominated by warmup months. Check 6 (Pareto) PASS-equivalent — `pareto_front.csv` RETIRED under unified architecture; `frac_positive_paths=0.6444` PASS. Check 7 (reproducibility) PASS — explicit 14-element `feature_columns` literal guarded by a `RuntimeError`, ensemble seeds literal, PnL spot-checks recompute. Check 8 (hypothesis-implementation alignment) PASS — exactly two changes (the report function + the `range_efficiency_50` revert), nothing else; no scope creep.
- **Foundation Audit (Boot Steps 9-11) CLEAN** — walk-forward embargo intact (`walk_forward.py:113` is `train_end_ms = test_start_ms - embargo_ms`); `ITERATION_LABEL="v3-077"`; 14-feature stack asserted; `efficiency_ratio_50` literal-name ban retained; `regime_momentum_signed_5d` asserted present; sacred constants untouched.
- **§11 Anti-Pattern Static Scan CLEAN** — no `start_time` manipulation, no OOS-cutoff drift, no hardcoded-Sharpe injection, no `feature_columns=None`/auto-discovery, no cross-track import (the three `features_v3/` grep matches are docstring/comment lines, not `import` statements).
- **The brief's algebraic-identity over-claim is documented as a process-level recommendation (Critic Rec #2), not a BLOCK** — the brief's own Section 8.3 pre-registered the exact INERT outcome, the QE root-caused the perturbation with zero residual, and the classifier fired correctly.

## 8. PATH classification — INERT-AT-EXPLORATION

**INERT-AT-EXPLORATION** per brief Section 8.3. The gate evaluation order is SUSPICIOUS → NULL-RESULT → NEGATIVE → PROMISING → INERT; first match is canonical.

1. **SUSPICIOUS — ruled out.** The ratio gate does not fire: OOS/IS monthly Sharpe ratio = +0.2078 / +0.8236 = **0.2523** ≪ 3.0. The OOS-dominant sub-mode does not fire: it requires IS shift < 0 AND OOS shift ≥ +0.20 — IS shift -0.0089 is negative, but OOS shift +0.0675 < +0.20. Neither ground satisfied.
2. **NULL-RESULT — ruled out.** NULL-RESULT (brief Section 8.2) requires the trade roster bit-identical to /060. The IS *key* roster IS bit-identical (159=159, 0/0), but 13 TRX IS `weight_factor` values differ and the OOS roster has +1 trade — so the roster is NOT bit-identical. The brief's predicted NULL-RESULT does not hold.
3. **NEGATIVE — ruled out.** NEGATIVE requires IS Δ < -0.10 OR OOS Δ < -0.10. IS Δ -0.0089 ∈ ±0.10; OOS Δ +0.0675 is positive. Neither floor breached.
4. **PROMISING — ruled out.** PROMISING requires IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20. IS Δ -0.0089 fails the IS floor; OOS Δ +0.0675 fails the OOS floor. A PASSIVE-DIAGNOSTIC has no edge mechanism — PROMISING was never in scope.
5. **INERT-AT-EXPLORATION — FIRES.** Both shifts within the noise bands (IS Δ -0.0089 ∈ [-0.10,+0.10]; OOS Δ +0.0675 ∈ [-0.20,+0.20]), the roster is NOT bit-identical to /060, and SUSPICIOUS does not fire. This is the precise contingency the brief Section 8.3 pre-registered as the ≈4% benign-perturbation tail.

**→ INERT-AT-EXPLORATION.** INERT iterations do not advance to CONFIRMATION and do not update BASELINE_V3.md. The `conditional_orthogonality.csv` instrumentation lands as accretive report tooling — a strictly-accretive methodology component per `feedback_v3_promising_mechanical_subtype.md`, non-compoundable across iterations as an edge ingredient.

## 9. Hypothesis check — the brief predicted a NULL-RESULT bit-identity; partially right

The brief Section 4.1 predicted the /077 trade roster would be **bit-identical to /060**, classifying NULL-RESULT — on the reasoning that reverting /076's feature and adding only a report-emission function leaves the byte-identical /060 configuration, which deterministically reproduces /060's models and roster.

**The prediction was partially right and partially wrong.**

- **Right — the iteration WAS zero-axis-effect.** /077's own config change (the report function + the feature revert) produced exactly zero behavioral effect: the IS `(symbol, open_time)` key roster is bit-identical to /060 (159=159, 0/0), and the metrics moved trivially (-0.0089 IS / +0.0675 OOS, deep inside the noise bands). The PASSIVE-DIAGNOSTIC was passive, as designed.
- **Wrong — the bit-identity *point prediction* failed.** The roster is not byte-identical: 13 TRX IS `weight_factor` values floored at 0.5, +1 OOS trade. The brief Section 4.1 over-claimed "algebraic identity." The cause was NOT /077's config — it was the iter-v3/061 TRX `vol_scale_floor` (16 iterations of code accretion) plus calendar data-extent growth. The brief reasoned about its own change correctly; it failed to account for the codebase having drifted since the anchor.

The classification machinery absorbed the miss cleanly: the brief's Section 8.3 had pre-registered exactly this INERT contingency, and the disjunctive gate resolved to it. The honest summary: the iteration's *substantive* prediction (zero axis effect) held; the *measurement* prediction (byte-identical roster) failed because the anchor itself had gone stale — which is the iteration's principal finding (Section 4).

## 10. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). A PASSIVE-DIAGNOSTIC INERT EXPLORATION produces no edge ingredient, does not advance to CONFIRMATION, and an EXPLORATION cannot update the baseline regardless. **No new tag issued.**

**One BASELINE_V3.md edit at this closeout:** a note added to the Measurement Discipline section recording that the /060 EXPLORATION-MODE-REFERENCE anchor is STALE — the current-code /060-config baseline is **IS +0.8236 / OOS +0.2078** (frozen anchor was +0.8325 / +0.1403), with the -0.0089 code-drift / +0.0675 data-extent decomposition — and that cycle-2 EXPLORATIONs /078+ re-anchor accordingly. The /059 CONFIRMATION baseline (the canonical anchor, tag `v0.v3-059`) is UNCHANGED and unaffected — it is a unified-architecture CONFIRMATION number, not an EXPLORATION-mode reference. The baseline metrics, anchor, and tag are unchanged; the Measurement Discipline note is the only edit.

## 11. Critic Recommendations carried forward

For FUTURE cycle-2 EXPLORATIONs (/078+). This iteration's verdict is final; a PASSIVE-DIAGNOSTIC does not advance.

1. **Re-anchor /078+ explicitly — ADOPTED (Section 4).** The /060 frozen anchor (IS +0.8325 / OOS +0.1403) does not reproduce on current code+data. /077 establishes the current-code /060-config baseline at **IS +0.8236 / OOS +0.2078**. The /078 brief Section 0 MUST state which anchor it uses and stop treating the frozen +0.1403 OOS as reproducible. /078-/080 anchor against /077's current-code numbers with the -0.0089 (code-drift) / +0.0675 (data-extent) decomposition annotated.

2. **Stop asserting "algebraic identity" for roster predictions unless the entire behavior-affecting config is git-verified frozen since the anchor.** /077's brief Section 4.1 claimed bit-identity as "an algebraic identity" while the codebase had silently accreted the /061 TRX `vol_scale_floor` since /060. A bit-identity prediction must be backed by a git-diff of every behavior-affecting config (`RiskV2Config`, ATR multipliers, vol-scale floors/ceilings, seeds) between the anchor commit and HEAD. A pre-registered benign-perturbation tail (which the brief did have, Section 8.3) is the correct hedge; the over-confident point-estimate framing is the defect.

3. **Fix the same-name-different-denominator inconsistency in EDA summary CSVs.** The /077 EDA `axis_selection_summary.csv` reports IS-window *calendar* months (63) under the same `IS_bull_months` key that `T1_regime_stratification.csv` uses for trade-active months (33) — both numbers are individually correct for their respective denominators, but the shared key is ambiguous; disambiguate the labels. (The other half of Critic Rec #3 — removing the stale hardcoded `LDOUSDT/cusum_reset_count_200` ADF secondary-falsifier check — the orchestrator already completed at commit `20c65cd`.)

## 12. Next Iteration Ideas

### Cycle 2 progress — 7/10 EXPLORATIONs done

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2 take/skip) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon-21) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | NEW RISK PRIMITIVE (regime-conditional kill switch, primitive 9) | INERT-AT-EXPLORATION |
| #5 | /075 | NEW RISK PRIMITIVE (BTC-trend-regime position-SIZE de-rate, primitive 12) | INERT-AT-EXPLORATION |
| #6 | /076 | NEW FEATURE (`range_efficiency_50`, Kaufman path efficiency) | SUSPICIOUS-OOS-DOMINANT |
| #7 | /077 | PASSIVE-DIAGNOSTIC (`conditional_orthogonality.csv` + `range_efficiency_50` revert) | **INERT-AT-EXPLORATION** |
| #8-#10 | /078-/080 | TBD per QR EDA — see candidates below | — |

**Cycle 2 is 7/10 done and has produced 0 clean PROMISING** — 2 SUSPICIOUS-OOS-DOMINANT (/071, /073, /076 — three), 1 NEGATIVE, 3 INERT (/074, /075, /077). Honest reckoning:

- **The cycle has now produced two load-bearing methodology corrections in addition to zero edge.** (a) The anchor-staleness finding (/077 Section 4) — the EXPLORATION reference drifts via code accretion + data-extent growth. (b) The reframing finding (/077 Section 5) — the IS drag is in the BULL months, exogenously measured, and /074-/076 all optimized against the wrong stratum. These corrections re-direct /078-/080; they do not produce an edge ingredient.
- **Three failure channels remain mapped** (carried from /076): (a) holding-time-EXTENSION axes load the regime factor via barrier mechanics; (b) post-gate macro BTC-trend classifiers trade IS for OOS ~1:1; (c) a feature can load the regime factor via trade SELECTION. The conditional-orthogonality map (/077 Section 6) is now the screening tool for channel (c).
- The standing structural problems are unchanged: **LDO directional weakness** (LDO has dragged every cycle-1 and cycle-2 iteration) and the **bull-month entry-discrimination drag** newly localized by EDA T1.

### iter-v3/078 (cycle 2 #8) axis candidates — seeding only

Per `feedback_v3_axis_selection_quant_discipline.md`, the /078 actual axis is QR-EDA-driven and will be selected fresh in /078 Phase 1-2 with a committed `analysis/iteration_v3-078/*.py` EDA script; the brief Section 2 must contain EDA-derived numerical tables. The candidates below seed the QR EDA only:

1. **A bull-month entry-discrimination feature axis (HIGHEST — directly motivated by the /077 reframing finding).** EDA T1 localized the IS drag in the BULL months (IS_BULL Sharpe +0.4100, 33% positive vs IS_BEAR_CHOP +1.2909, 47% positive) and EDA T6 diagnosed it as directional quality (bull-month WR 32.7%, 64% stop-loss exits). A NEW feature that improves *entry discrimination in bull regimes* — separating bull-month continuation from bull-month chop the strategy currently mis-trades — targets the actual structural drag. The /078 EDA MUST screen any candidate against the /077 `conditional_orthogonality.csv` map: a feature whose conditional model-split allocation correlates >0.35 with the BTC-regime label is a /076-style regime-loading risk. The feature must also be tested ALONE (`feedback_v3_engineered_features_dont_stack.md`), clear the engineered-feature importance ≥30 falsifier if composed (`feedback_v3_engineered_feature_pivot.md`), and pre-register the added-vs-removed roster-composition mean-duration sub-channel (Critic /076 Rec #2).

2. **A re-scoped meta-labeling M2 verified BOTH holding-time-orthogonal AND conditionally-orthogonal (BASELINE_V3.md cycle-2 priority #1).** Still the highest-ranked structural axis in BASELINE_V3.md cycle-2 priorities and still never cleanly executed (/071's meta-labeling failed as a holding-time-EXTENSION axis). An M2 whose quality signal is verified at brief stage to NOT lengthen mean/median trade duration AND to NOT produce regime-correlated trade selection (the /076 channel) would address LDO's directional bleed. The brief must pre-register BOTH the holding-time predictor (with the roster-composition sub-channel) AND a conditional-orthogonality test against the /077 map.

3. **A universe-revision axis (replace LDO) — BASELINE_V3.md cycle-2 priority #3.** If the cycle's remaining EXPLORATIONs cannot lift the bull-month drag with a feature or M2, the LDO structural weakness becomes the binding constraint. A replacement must clear an IS-edge screen BEFORE inclusion (prior universe-expansion EXPLORATIONs /021, /069 all failed). Lower priority than #1-#2 — only if a feature/M2 axis is exhausted.

**Hard constraints on /078** (carried from prior closeouts):
- **Anchor against /077's current-code /060-config baseline (IS +0.8236 / OOS +0.2078)**, NOT the frozen /060 +0.8325/+0.1403; the /078 brief Section 0 must state this explicitly with the -0.0089/+0.0675 decomposition annotated (Critic /077 Rec #1).
- Holding-time-orthogonal — the brief Section 2 must include the holding-time-effect predictor (`feedback_v3_is_oos_regime_divergence.md`) WITH the added-vs-removed roster-composition mean-duration sub-channel (Critic /076 Rec #2).
- Pre-register the OOS/IS Sharpe ratio bound (>3.0 → SUSPICIOUS) in Section 4 per `feedback_v3_oos_is_ratio_gate.md`, using the canonical within-iteration `comparison.csv` `monthly_sharpe` ratio definition.
- Pre-register a behavioral-effect predictor with a falsifier (`feedback_v3_axis_saturation_predictor.md`).
- Per-symbol IS-axis discipline (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) if the candidate is per-symbol.
- If the axis is a NEW feature, screen it against the /077 `conditional_orthogonality.csv` map — a near-zero MARGINAL correlation is necessary but NOT sufficient; the CONDITIONAL (model-split-allocation) correlation is the binding test (Critic /076 Rec #1).
- The Section 7 SUSPICIOUS probability must be floored near the running cycle-2 base rate unless the brief presents a conditional-orthogonality proof strong enough to justify deviating below it (Critic /076 Rec #3).
- The Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`) is CLOSED across two data points — do not re-propose it.
- The regime-conditional kill switch (primitive 9) is CLOSED across two data points — do not re-propose it.

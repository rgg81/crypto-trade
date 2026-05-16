# iter-v3/070 — CYCLE 1 CONFIRMATION / SUSPICIOUS-OOS-DOMINANT / NO-MERGE

**Date**: 2026-05-15
**Type**: CYCLE 1 CONFIRMATION (first CONFIRMATION after strict 10:1 cadence; 2-component bundle)
**Bundle**: /065 SL widening (`DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)`) + /062 Path B4 methodology (annualized-both-sides `dsr_relative` reformulation)
**Verdict**: **SUSPICIOUS-OOS-DOMINANT — NO-MERGE** per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve)
**Critic FINAL**: `2991781` — OVERALL=CONFIRMATION-MERGE (verdict certified clean; the NO-MERGE classification is methodologically correct)
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`)
**Branch**: `iteration-v3/070`

---

## 1. What was done

iter-v3/070 is the FIRST CONFIRMATION of v3 cycle 1 (post-RE-ANCHOR #2). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 1 ran 10 SEPARATE EXPLORATIONs (/060-/069) followed by 1 SEPARATE CONFIRMATION (/070) — the 10th EXPLORATION was NOT collapsed into the CONFIRMATION.

The /070 bundle was LOCKED at /069 closeout (diary Section 9) with exactly 2 components:

| Component | Source | Code change | EXPLORATION evidence |
|---|---|---|---|
| **A** | /065 SL widening | `DEFAULT_ATR_MULTIPLIERS` (2.0, 1.0) → (2.0, 1.5) | SUSPICIOUS-OOS-DOMINANT at /065 single-seed (IS Δ -0.16 / OOS Δ +0.91 vs /060) |
| **B** | /062 Path B4 methodology | `dsr_relative` reformulation: annualized-both-sides at √252 / √756 | PASSIVE-DIAGNOSTIC at /062 (deferred spec at /062 brief Section 3) |

Component A is the ONLY non-anchor advancement candidate cycle 1 produced. Component B is methodology-only — it modifies `dsr.json` output and has ZERO behavioral effect on the trade roster (POST-trade-roster computation). The bundle is single-axis at the trade-roster level.

Run mode: unified 10-seed ensemble (ENSEMBLE_SIZE=10), CONFIRMATION default, `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX — REVERT /069 ADA addition; REQUIRED_GAP back to 66). Total 1050 Optuna trials. Wall-clock 3.13h within the 6h CONFIRMATION cap.

Commit chain: brief LOCKED `aee5378` → EDA `fe219c1` → implementation `aab9347` → Phase 5.5 gate `2d733b1` → engineering report `e9a80d3` → Critic review `2991781`.

The /070 setup also addressed Critic /069 Rec #1 (anchor-byte gate enforcement at runner-level): a new `_verify_timeout_consistency()` pre-flight assertion enforces `BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes == 10080`, closing the line-1407/1425 desync defect class that fired at /069.

## 2. Results — vs /059 anchor

| Metric | /059 anchor | /070 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+1.0894** | **+0.1160** | **-0.9734 (collapse)** |
| OOS monthly Sharpe | **+0.5791** | **+1.2533** | **+0.6742 (soar)** |
| OOS/IS monthly Sharpe ratio | 0.5316 | **10.8090** | structurally suspect |
| IS daily Sharpe | +2.7092 | +0.3281 | -2.3811 |
| OOS daily Sharpe | +1.4359 | +2.7233 | +1.2874 |
| IS MaxDD | 30.97% | **46.51%** | **+15.54pp** |
| OOS MaxDD | 34.53% | 36.31% | +1.78pp |
| IS profit factor | 1.49 | **1.05** | -0.44 (break-even) |
| OOS profit factor | 1.21 | 1.41 | +0.20 |
| IS win rate | 33.33% | 35.76% | +2.43pp |
| OOS win rate | 38.30% | **54.02%** | +15.72pp |
| IS trades | 171 | 151 | -20 |
| OOS trades | 94 | 87 | -7 |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0 (CPCV invariant) |
| PBO mean | 0.1278 | 0.1068 | -0.0210 |
| PSR (legacy) | 1.0 | 1.0 | 0 |
| DSR_relative (legacy) | 0.1134 | **0.9999** | **+0.8865 (Path B4 fix working)** |
| **DSR_relative_B4** | n/a (NEW) | **1.0000** | PASS @0.95 |
| daily_sharpe_oos_b4_at_√252 | n/a | 2.2772 | informational |
| cpcv_q75_annualized_b4 | n/a | 0.6398 | informational |
| n_daily_obs_oos | n/a | 79 | informational |

The headline is unambiguous: **IS collapsed by -0.97 and OOS soared by +0.67.** The OOS/IS monthly Sharpe ratio of 10.81 is far outside any healthy strategy band (a robust strategy produces a ratio in roughly [0.5, 2.0]). This is the structural signature of regime exposure, not robust edge.

## 3. Per-symbol decomposition (OOS, from comparison.csv)

| Symbol | /059 OOS wpnl | /070 OOS wpnl | Δ | /070 n_trades | /070 WR | /070 conc_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +24.75 | **+49.89** | +25.14 | 34 | **61.8%** | **101.17%** |
| LDOUSDT | -6.18 | **-13.77** | -7.59 | 14 | 35.7% | -27.92% |
| TRXUSDT | +4.16 | +13.19 | +9.03 | 39 | 53.8% | 26.75% |

OOS BCH carries the entire portfolio (101.17% concentration). LDO (-13.77) is a persistent drag — worse than the /059 anchor (-6.18). TRX (+13.19) is a positive net contributor. The OOS picture LOOKS healthy on aggregate Sharpe but is structurally one BCH-favorable regime window.

IS per-symbol forensic (from engineering report — the decisive evidence):
- **BCH IS**: 72 trades, 58.3% WR, net_pnl +84.09 (+1.17%/trade) — BCH still carries IS alone.
- **TRX IS**: 65 trades, 35.4% WR, net_pnl -23.91 (-0.37%/trade) — directional bleed; wider 1.5×ATR SL makes each loss deeper.
- **LDO IS**: 14 trades, 28.6% WR, net_pnl **-47.46** (-3.39%/trade) — severe IS collapse; wider SL amplifies LDO's well-documented IS weakness.

The mechanism: wider SL (1.0×→1.5×ATR) lets losing trades ride losses ~50% longer before stopping. In the IS window (2022 bear + 2023-24 chop/recovery), this translates directly to deeper per-trade losses, a 46.51% IS MaxDD (catastrophic for a Sharpe +0.12 strategy), and the IS collapse. In the trending OOS window (Apr 2025–May 2026), the same wider SL lets BCH winners run without truncation, producing the OOS WR +15.7pp lift and OOS Sharpe soar. **Wider SL is a directional bet on a trending regime, not a robust edge.**

## 4. Critic verdict summary

**OVERALL = CONFIRMATION-MERGE** (Critic FINAL `2991781`). The "MERGE" verdict certifies the iteration's closeout integrity — it explicitly does NOT imply a baseline update. Per the Critic's own framing: "the SUSPICIOUS-OOS-DOMINANT NO-MERGE classification is methodologically clean. The iteration correctly does NOT update BASELINE_V3.md."

13 checks all PASS or WARN — zero BLOCK:
- **Checks 1, 2, 3, 5, 6, 7, 8** — PASS (look-ahead, embargo, multiple-testing/DSR-B4, ADF, Gate 10-CPCV, reproducibility, hypothesis-implementation alignment).
- **Check 4 (IC)** — WARN: `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` exceeds the 0.70 gate. Does NOT escalate to FAIL because both features are inherited UNCHANGED from /059's 14-feature set — /070 makes ZERO feature change. The Critic flags the Category 2 carve-out wording as imprecise (regime_momentum's primitives are ret_5d + hurst_100, NOT vwap_dev_20) — carried to cycle 2 as a process recommendation.
- **Foundation Audit (Boot Steps 9-11)** — PASS: walk-forward lookahead fix INTACT; `_verify_timeout_consistency()` implemented + invoked; §11 Anti-Pattern Static Scan CLEAN.

**Component decomposition certified CLEAN.** The Critic verified the Path B4 block (run_baseline_v3.py:2386-2464) contains zero `braked` mutation, zero `label_trades()` call, zero Optuna invocation — provably reporting-layer-only. The entire IS collapse is 100% attributable to Component A (SL widening). The 10.81 OOS/IS ratio is regime asymmetry, not leakage (embargo gap=66 asserted; OOS distributed across 14 months with no single carrying month).

**Path B4 DSR_relative_B4 = 1.0 certified clean (not degenerate).** Forensic: `sr_hat = 2.277246 - 0.639849 = 1.637`; benchmark annualization independently verified (`0.837759 / √1296 × √756 = 0.639849`); `z ≈ 9.5 → cdf ≈ 1.0` via the live `psr()` path (not a fallback branch).

## 5. PATH classification — SUSPICIOUS-OOS-DOMINANT

Per brief Section 8.3 LOCKED criteria:
- IS Δ < 0 vs /059 (regression): **IS Δ = -0.9734** — satisfied (and far beyond).
- OOS Δ ≥ +0.20 vs /059 (lift): **OOS Δ = +0.6742** — satisfied.

→ **SUSPICIOUS-OOS-DOMINANT**. The IS Δ of -0.9734 also crosses the NEGATIVE envelope (IS Δ < -0.30 per Critic /068 Rec #1 carry-forward). Per the engineering report and Critic, "SUSPICIOUS-OOS-DOMINANT" takes classification precedence because the extreme OOS/IS ratio (10.81) is the more specific diagnostic — it identifies the mechanism (regime asymmetry), not just the magnitude.

This is NOT a NEGATIVE classification despite the IS Δ crossing the NEGATIVE threshold: the OOS axis genuinely lifts. The bundle is not "broken" — it is regime-exposed. The distinction matters for cycle 2: SL widening is not a code bug to fix; it is a falsified edge hypothesis to retire.

The /065 single-seed EXPLORATION already showed this exact IS-collapse + OOS-soar pattern (IS Δ -0.16 / OOS Δ +0.91). It was classified SUSPICIOUS-OOS-DOMINANT at /065 and advanced to CONFIRMATION precisely to test whether multi-seed averaging would compress the lottery or expose the regime bet. **It exposed the regime bet.** The pattern persisted and amplified at multi-seed — the IS regression went from -0.16 (single-seed) to -0.97 (10-seed). The CONFIRMATION did its job.

## 6. Bundle component adjudication

### Component A — /065 SL widening: **REJECTED**

The IS-collapse + OOS-soar pattern that appeared at /065 single-seed EXPLORATION PERSISTED and AMPLIFIED at multi-seed CONFIRMATION. IS Sharpe collapsed -0.97; IS MaxDD deteriorated +15.5pp to a catastrophic 46.51%; IS profit factor fell to break-even 1.05. A one-month IS Sharpe of +0.12 with PF 1.05 and MaxDD 46.51% is statistically indistinguishable from random at any reasonable confidence level.

Wider SL (1.0→1.5×ATR) is **regime exposure, not robust edge**. It is a directional bet that the live regime will be trending (OOS-like) rather than chop/bear (IS-like). The `/065 SL-widening` edge candidate FAILS CONFIRMATION validation. **Component A is rejected.** The code change (`DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5)`) is REVERTED to (2.0, 1.0) — see Section 7 and the revert commit.

### Component B — /062 Path B4 methodology: **ACCEPTED as infrastructure**

Path B4 corrects a genuine measurement bug. The legacy `dsr_relative` computation mixed granularities — trade-level cumulative PnL entered `psr()` as if it were an annualized Sharpe, producing systematically low DSR values regardless of true OOS performance. /059's legacy DSR of 0.1134 was a measurement artifact, not a signal about edge.

Path B4 puts both inputs at the same granularity (annualized): observed Sharpe at √252 (annualized daily), benchmark CPCV-Q75 at √756. Validation:
- `dsr_relative_B4 = 1.0000` (PASS at 0.95).
- Legacy `dsr_relative` jumped 0.1134 → 0.9999 — the granularity-mismatch fix working exactly as the /062 thesis predicted.
- Backward-compat: /059 predicted B4 ≈ 0.95-1.0 → observed legacy 0.9999 / B4 1.0000 — RESOLVES the artifact as predicted.

**Important caveat**: `dsr_relative_B4 = 1.0` is measuring the SUSPECT strategy's OOS performance. A high relative DSR on a strategy with IS Sharpe +0.12 is NOT evidence of robustness — it is evidence the OOS window happened to favor BCH. The measurement tool works correctly; the strategy it measures does not. DSR_relative_B4 is an OOS-only relative metric — it makes NO IS claim, and it cannot rescue a bundle that fails the BOTH-must-improve IS gate.

Path B4 is classified per `feedback_v3_promising_mechanical_subtype.md` as a strictly-accretive methodology improvement — non-compoundable across iterations, but **retained as infrastructure**. The runner now produces `dsr.json` with `dsr_relative_b4`, `daily_sharpe_oos_b4_at_sqrt252`, `cpcv_q75_annualized_b4`, and `n_daily_obs_oos`; the legacy `dsr_relative` field is PRESERVED alongside. **Component B is accepted and NOT reverted.** This is the one durable gain of cycle 1.

## 7. BASELINE_V3.md status — UNCHANGED

**BASELINE_V3.md is UNCHANGED. /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`).**

Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve discipline): a CONFIRMATION updates BASELINE_V3.md ONLY when it beats the prior baseline on BOTH IS Sharpe AND OOS Sharpe. /070's IS gate FAILS by -0.9734. OOS-only improvement with IS regression = NO-MERGE — exactly the iter-v3/039 precedent (IS -0.08 / OOS +1.47 → NO-MERGE).

No new git tag is issued.

The BASELINE_V3.md "Code Configuration" section is updated (separate commit) to document that **Path B4 methodology is now retained infrastructure** — `dsr.json` reports both legacy `dsr_relative` and the new `dsr_relative_b4`. The anchor METRICS do not change.

`DEFAULT_ATR_MULTIPLIERS` is REVERTED to (2.0, 1.0) — the canonical /059 baseline value — in a separate commit. Leaving (2.0, 1.5) in the codebase would mean cycle 2 silently inherits a CONFIRMATION-rejected axis, violating `feedback_no_cheating.md` ("improve the strategy, not the measurement window") and the Critic /069 anti-drift discipline. BASELINE_V3.md documents the canonical labeling multipliers as `(atr_tp=2.0, atr_sl=1.0)`; the code now matches.

## 8. CYCLE 1 FINAL OUTCOME

| Slot | Iter | Axis | Verdict | /070 Bundle Contribution |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE | PROMISING (anchor) | anchor only |
| #2 | /061 | TRX vol_scale_floor | INERT | none |
| #3 | /062 | DSR_relative recalibration (Path C passive) | PASSIVE-DIAGNOSTIC | **Path B4 deferred spec → ACCEPTED** |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS+IS-COLLAPSE | none |
| #5 | /064 | Phased +adx_14 | NEGATIVE | none |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | SUSPICIOUS-OOS-DOMINANT | **SL widening → REJECTED** |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT | none |
| #8 | /067 | Confidence threshold floor=0.60 | INERT | none |
| #9 | /068 | Label timeout 21→42 | NEGATIVE | none |
| #10 | /069 | Universe expansion +ADA | INERT (corrected) | none |
| **CONF** | **/070** | **/065 SL widening + /062 Path B4** | **SUSPICIOUS-OOS-DOMINANT, NO-MERGE** | A REJECTED; B RETAINED |

**Cycle 1 (iter-v3/060-070) produced NO BASELINE_V3.md update.** /059 remains the canonical anchor. The cycle 1 outcome distribution was:
- 1 PROMISING-EXPLORATION (the /060 anchor — not a bundleable component)
- 1 PASSIVE-DIAGNOSTIC (/062 — methodology axis → Path B4)
- 1 SUSPICIOUS-OOS-DOMINANT (/065 — the only advancement candidate → REJECTED at CONFIRMATION)
- 4 INERT (/061, /066, /067, /069 — axes closed)
- 3 NEGATIVE (/063, /064, /068 — axes closed with disqualifying evidence)

**The one durable gain of cycle 1 is Path B4** — a strictly-accretive methodology fix that corrected the `dsr_relative` granularity-mismatch artifact. It is not an edge ingredient; it is infrastructure. No new signal, no new feature, no new symbol, and no risk primitive from cycle 1 reaches the bundle-grade bar. Cycle 1 closes with the v3 baseline structurally identical to the /059 RE-ANCHOR #2 anchor, plus correct DSR reporting.

This is an honest null result for the edge axis. Mass feature expansion (/063) failed. SL widening (/065→/070) failed. The 8 knob/universe/timeout axes were INERT or NEGATIVE. LDO structural weakness — the dominant per-symbol drag — was not resolved by any cycle 1 axis.

## 9. Critic Recommendations carried to cycle 2

Three process recommendations from Critic FINAL `2991781`:

1. **Fix two stale docstrings before cycle 2** — `features_v3/__init__.py:205-219` calls V3_FEATURE_COLUMNS a "15-feature set" (actual: 14, since adx_14 was removed at /064); `validation_v3.py:589` docstring says "Default gap = 88" (actual: REQUIRED_GAP=66). Documentation rot — inert today, but exactly the desync class Critic /069 Rec #1 targets. (Note: the `features_v3/__init__.py` docstring is corrected as part of the DEFAULT_ATR revert commit since that file is already being touched; `validation_v3.py` is carried to cycle 2.)

2. **Tighten the Category 2 IC carve-out wording** — `feedback_v3_engineered_feature_pivot.md` justifies the carve-out as "composed features correlate with their primitives." The `vwap_dev_20 × regime_momentum_signed_5d = 0.7642` pair is NOT feature-vs-own-primitive (regime_momentum's primitives are ret_5d + hurst_100). Cycle 2 should either (a) restrict the carve-out to feature-vs-own-primitive pairs only, or (b) explicitly grandfather inherited baseline correlations and apply the IC gate only to NEWLY-added features.

3. **Adopt an OOS/IS ratio bound as a pre-registered gate** — the engineering report Rec #5 proposes rejecting any iteration with OOS/IS Sharpe ratio > 3.0 regardless of absolute OOS Sharpe magnitude. This pattern fired at single-seed /065, amplified at /070 CONFIRMATION, and previously appeared at /026 and /027. It is a recurring structural red flag. Cycle 2 EXPLORATION briefs must pre-register the ratio bound in Section 4 as a supplemental SUSPICIOUS classifier. Memory rule `feedback_v3_oos_is_ratio_gate.md` created at this closeout to make the pre-registration mandatory.

## 10. Cycle 2 axis priorities

Cycle 2 starts at iter-v3/071 (EXPLORATION #1 of the next 10) and anchors against /059 (unchanged baseline). The /065 SL widening and the 7 other INERT/NEGATIVE cycle 1 axes are CLOSED.

**The defining unresolved problem of cycle 1 is LDO structural weakness.** LDO was a drag through every cycle 1 EXPLORATION and the CONFIRMATION: /070 IS net_pnl -47.46 (28.6% WR), OOS net_pnl -13.77 (35.7% WR). LDO is the symbol that breaks the IS aggregate. No labeling knob, no feature expansion, no universe addition fixed it.

Recommended cycle 2 axis priorities (QR to commission EDA per `feedback_v3_axis_selection_quant_discipline.md` before any setup commit):

1. **HIGHEST — Model architecture (meta-labeling).** Per the original v3 mandate (`feedback_v3_iter017_metalabeling_mandate.md`), meta-labeling (López de Prado AFML Ch. 3) was MANDATED but never fully executed — /017's attempt was a single-seed EXPLORATION that over-filtered (PATH C). An M2 secondary classifier that predicts whether to ACT on the M1 direction signal is the natural structural response to a symbol (LDO) whose directional model bleeds. ML's edge is filtering, not forecasting. This is a structural axis (category 2 per `feedback_v3_structural_over_knob_exploration.md`), not a knob.

2. **HIGH — Labeling architecture.** Fixed-horizon return labels as an alternative to ATR triple-barrier. Cycle 1 proved the ATR-multiplier knob is a dead end (both /065 widening and /042 tightening failed). A different label DEFINITION — not a different multiplier — is the open question. This is also a structural axis.

3. **MEDIUM — Universe revision: replace LDO.** If meta-labeling and alternative labeling both fail to rescue LDO, the honest move is to replace LDO with a symbol that has IS-validated edge. Caveat: prior universe-expansion EXPLORATIONs (/021 HBAR+AVAX, /069 ADA) all failed — a replacement must clear an IS-edge screen BEFORE inclusion, not just a feature-space-distance screen.

4. **CONSTRAINT on every cycle 2 brief — per-symbol IS-axis discipline.** Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: validate that any per-symbol customization PRESERVES or LIFTS IS Sharpe before including it in a bundle. /070 reinforces this — OOS-only improvement is not bundle-grade.

5. **CONSTRAINT — pre-register the OOS/IS ratio bound** (per Section 9 Rec #3 and `feedback_v3_oos_is_ratio_gate.md`): every cycle 2 EXPLORATION brief Section 4 must pre-register "OOS/IS Sharpe ratio > 3.0 → SUSPICIOUS classification" as a supplemental gate.

What cycle 2 should NOT do: more ATR-multiplier knobs, more single-feature additions chosen by univariate rank, more universe additions chosen by feature-space distance alone, more gate-threshold tuning. Cycle 1 exhausted the knob space. Cycle 2 must be structural — model architecture or labeling architecture.

---

**Diary commit SHA**: TBD (this commit)
**Critic FINAL SHA**: `2991781`
**Engineering report SHA**: `e9a80d3`
**Brief LOCKED SHA**: `aee5378`
**Reports**: `reports-v3/iteration_v3-070/`

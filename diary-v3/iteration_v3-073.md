# iter-v3/073 — Cycle 2 #3 EXPLORATION / Per-symbol triple-barrier asymmetry / SUSPICIOUS-OOS-DOMINANT

**Date**: 2026-05-15
**Type**: EXPLORATION (cycle 2 #3 of 10; PER-SYMBOL LABELING axis)
**Axis**: per-symbol ATR triple-barrier asymmetry — `V3_ATR_MULTIPLIERS_PER_SYMBOL` re-populated for BCH/LDO (TRX falls back to global default)
**Verdict**: EXPLORATION-MERGE per Critic FINAL `c05c95e` — OVERALL=MERGE; SUSPICIOUS-OOS-DOMINANT classification certified clean (closeout integrity, single-axis discipline, no look-ahead)
**Classification**: **SUSPICIOUS-OOS-DOMINANT** per brief Section 8.4 LOCKED disjunctive gate (OOS/IS monthly Sharpe ratio 6.85 > 3.0)
**Advancement**: does NOT auto-advance to cycle 2 CONFIRMATION — the axis is regime-exposed and closed at catalog level
**BASELINE_V3.md**: **UNCHANGED** — /059 stays canonical (IS +1.0894 / OOS +0.5791; tag `v0.v3-059`)
**Branch**: `iteration-v3/073`

---

## 1. What was done

iter-v3/073 is the THIRD EXPLORATION of v3 cycle 2 (post-cycle-1-CONFIRMATION at iter-v3/070). Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 2 runs 10 SEPARATE EXPLORATIONs (/071-/080) followed by 1 SEPARATE CONFIRMATION — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The axis is **per-symbol triple-barrier asymmetry** — a per-symbol LABELING axis, QR-selected with committed EDA backing (`feedback_v3_axis_selection_quant_discipline.md`). The single varied axis is `V3_ATR_MULTIPLIERS_PER_SYMBOL` (the per-symbol ATR triple-barrier multiplier dict). The QR EDA (`b004bc9`) ran a per-symbol (tp, sl) grid sweep and a per-symbol barrier-hit profile, and recommended:

```python
V3_ATR_MULTIPLIERS_PER_SYMBOL = {
    "BCHUSDT": (2.0, 1.25),   # barrier-balance recalibration (was global (2.0, 1.0))
    "LDOUSDT": (1.5, 1.25),   # SL-saturation correction (was global (2.0, 1.0))
    # TRXUSDT omitted — falls back to DEFAULT_ATR_MULTIPLIERS (2.0, 1.0); EDA keep-decision.
}
```

The EDA basis: LDO's global-default triple-barrier label was **69% SL-saturated** (the label predominantly resolves at the SL barrier rather than TP or timeout). The (1.5, 1.25) cell shortens LDO's TP arm and widens its SL arm, raising LDO's label `exec_consistency` from 0.65 to 0.90 in IS. BCH's chosen cell `(2.0, 1.25)` rebalances its barrier-hit profile toward TP. TRX was an explicit EDA keep-decision — its global default was already balanced, so it was deliberately omitted and falls back to `DEFAULT_ATR_MULTIPLIERS (2.0, 1.0)`.

A mandatory secondary edit was the **revert of the /072 leftover**: the runner was on `label_mode="fixed_horizon"` (the iter-v3/072 NEGATIVE axis). It was reverted to `label_mode="triple_barrier"`. The per-symbol ATR multipliers ONLY take effect under the triple-barrier label path, so this revert is necessary both for the axis to fire AND to restore the /060 anchor labeling rule. This is a revert, not a second varied axis — it returns the runner to the established cycle-2 baseline labeling.

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, ENSEMBLE_SEEDS outer=42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna trials. Wall-clock 0.70h — within the brief's 0.6-1.0h estimate and well under the 2h EXPLORATION cap.

The Phase 5.5 gate first BLOCKED (`da92d0d`): 4 stale pre-flight assertions (per-symbol ATR count, per-symbol ATR loop, `label_mode` expected `"fixed_horizon"`, and the existing `test_atr_multipliers_for_symbol.py` asserting the pre-/073 default). All 4 were resolved at `d5d53a0`; Phase 6 proceeded from `d5d53a0` as the implementation commit.

Commit chain: EDA `b004bc9` → brief LOCKED `b859dab` → Phase 5.5 gate (BLOCK) `da92d0d` → gate fix `d5d53a0` → engineering report `f1071a9` → Critic review `c05c95e`.

## 2. Results — vs /060 EXPLORATION-mode anchor

The cycle-2 EXPLORATION anchor is iter-v3/060 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.1403), the unified-architecture 3-seed EXPLORATION-mode reference that /071 and /072 also anchored against. With the /072 `label_mode` reverted to `triple_barrier`, /073 is `/060-trade-roster-equivalent` for its non-axis symbol (TRX — see Section 3).

| Metric | /060 anchor | /073 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.2779** | **-0.5546 (regression)** |
| OOS monthly Sharpe | **+0.1403** | **+1.9025** | **+1.7622 (lift)** |
| OOS/IS monthly Sharpe ratio | 0.169 | **6.847** | most extreme in v3 history |
| IS daily Sharpe | +1.7115 | +0.6080 | -1.1035 |
| OOS daily Sharpe | +0.3659 | +3.8067 | +3.4408 |
| IS profit factor | 1.2806 | 1.0891 | -0.191 (barely break-even IS) |
| OOS profit factor | 1.0482 | 1.5912 | +0.509 |
| IS win rate | 31.45% | 34.09% | +2.64pp |
| OOS win rate | 39.22% | 49.06% | +9.84pp |
| IS MaxDD | 30.97% | 29.07% | -1.90pp |
| OOS MaxDD | 34.53% | **15.79%** | **-18.74pp (improvement)** |
| IS n_trades | 159 | 176 | +17 |
| OOS n_trades | 102 | 106 | +4 |
| IS total_pnl | — | +20.52 | — |
| OOS total_pnl | — | +64.93 | — |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0 (architecture-invariant) |
| DSR_relative_B4 | n/a | 1.0000 | PASS @0.95 (OOS-only) |
| PBO mean | 0.1278 | 0.1541 | +0.026 (still PASS) |
| PSR | 0.9763 | 1.0000 | +0.024 |
| n_eff | 19 | 19 | 0 |
| n_trials (Optuna total) | 315 | 315 | 0 |

The headline: **IS regressed -0.5546 and OOS lifted +1.7622.** The OOS/IS monthly Sharpe ratio of **6.847** is the most extreme of any v3 EXPLORATION or CONFIRMATION iteration. The OOS picture is uniformly strong on its own terms — OOS Sharpe +1.90, OOS MaxDD cut by 18.7pp, OOS WR up nearly 10pp, OOS PF 1.59 — but the IS collapse to a near-break-even +0.2779 (IS PF 1.09) is the defining feature. The two windows tell opposite stories. Per Section 6, this divergence is the regime-exposure signature, not robust edge.

## 3. Per-symbol decomposition

### 3.1 OOS attribution (from `reports-v3/iteration_v3-073/comparison.csv`)

| Symbol | /073 OOS wpnl | /073 OOS n_trades | /073 OOS WR | /073 OOS conc_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | **+21.99** | 37 | 48.6% | 33.86% |
| LDOUSDT | **+18.23** | 15 | 53.3% | 28.07% |
| TRXUSDT | **+24.72** | 54 | 48.1% | 38.07% |

**All three symbols are OOS-positive — the FIRST time this has occurred across cycle 1 AND cycle 2.** OOS wpnl total 64.93 (cross-check: 21.99 + 18.23 + 24.72 = 64.93, PASS). Concentration is well-distributed (33.9% / 28.1% / 38.1%), the most balanced 3-symbol OOS split in v3 history. On a naive read, this is the strongest-looking OOS result v3 has produced.

### 3.2 IS decomposition (the contradiction)

| Symbol | /060 IS trades | /073 IS trades | /060 IS WR | /073 IS WR | /060 IS net_pnl | /073 IS net_pnl | Δ net_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | 73 | 83 | 45.2% | 50.6% | +79.45% | +74.97% | -4.5pp |
| LDO | 11 | 18 | 27.3% | 44.4% | -11.44% | -9.997% | **+1.4pp** |
| TRX | 75 | 75 | 29.3% | 29.3% | -23.04% | -23.04% | 0pp (frozen) |

Key controls:
- **TRX IS is BYTE-IDENTICAL between /060 and /073** (75 trades, 29.3% WR, -23.04% net_pnl). TRX uses the unchanged `DEFAULT_ATR_MULTIPLIERS (2.0, 1.0)` — this is the positive control confirming the axis is wired correctly and the per-symbol ATR dict change for BCH/LDO did not contaminate the TRX trade roster. Single-axis discipline is verified.
- **LDO IS genuinely improved** — WR +17.1pp (27.3%→44.4%), IS net_pnl +1.4pp (-11.44%→-9.997%). The EDA's IS-only prediction (correcting the 69% SL-saturation pathology) is borne out in IS. The aggregate IS collapse is NOT a hidden LDO failure.

**The contradiction (Critic Q2):** LDO IS improved by **+1.4pp net_pnl**, yet LDO's OOS wpnl swung by **+43pp** (from -25.08 at /060 to +18.23 at /073). A +1.4pp IS improvement cannot underwrite a +43pp OOS swing. The EDA itself is decisive on this: LDO's `directional_spread` is NEGATIVE across all 9 grid cells — the axis "corrects the barrier pathology, it does NOT manufacture a positive LDO label spread." The disproportionate +1.4pp-IS / +43pp-OOS split is the regime-exposure fingerprint. LDO's OOS-positive result is dominantly regime exposure, not a genuine LDO edge.

The IS Sharpe collapse (-0.55) is not a single-symbol catastrophe (unlike /072, where LDO OOS -32.49 dominated). It reflects the IS monthly PnL volatility structure: IS PF fell to 1.09 because the wider SL on BCH+LDO lets losses run deeper in the adverse IS regime even when trade count and WR rise. The 2024-Q1 monthly cluster (Jan +29.05, Feb -2.40, Mar -7.28, Apr -11.92) remains the dominant IS volatility driver.

## 4. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `c05c95e`. The MERGE verdict certifies the SUSPICIOUS-OOS-DOMINANT classification clean — it is a closeout-integrity / methodology certification, NOT an advancement to CONFIRMATION.

- **13/13 Checks PASS or informational.** DSR=0.0 structural at v3 trade volume (informational at EXPLORATION); PBO=0.1541 PASS; PSR=1.0 PASS; frac_positive_paths=0.6444 ≥ 0.55 PASS.
- **Foundation Audit CLEAN.** Walk-forward fix intact, 22-candle embargo strictly covers the 21-candle label horizon, ATR is past-inclusive EWMA, `label_mode` revert verified, per-symbol ATR threading verified. No look-ahead.
- **§11 Anti-Pattern Scan CLEAN.**
- **Single-axis discipline confirmed** — TRX IS byte-identical to /060 is the positive control.

Adversarial questions resolved:
- **Q1 — /073 distinct from /065's rejected universal SL widening?** Mechanically /073 IS in the SL-widening family (BCH/LDO SL 1.0→1.25). The QR does NOT hide this — brief Section 4.4 pre-registered the SUSPICIOUS gate BECAUSE the axis is SL-widening; Section 7 weighted NEGATIVE 35% citing /065 precedent. The QR called the failure mode before the run, the run produced it, the gate fired. Honest-disclosure posture certified. The /070 CONFIRMATION precedent is the controlling evidence against advancing /073.
- **Q2 — LDO OOS-positive: genuine edge or regime exposure?** Dominantly regime exposure (see Section 3.2). LDO IS genuinely improved (+1.4pp), but the +43pp OOS swing is disproportionate; LDO `directional_spread` is NEGATIVE across all cells. Does NOT survive as edge evidence.
- **Q3 — the 3-consecutive SUSPICIOUS pattern a structural regime signal?** YES — the most important finding of the iteration (see Section 6).
- **Q4 — OOS/IS 6.85 + OOS Sharpe +1.90 a leakage artifact?** NO. Foundation Audit clean, embargo arithmetic proven, TRX byte-identical IS = positive control. OOS +1.90 is a GENUINE property of the wider-SL config on a trending OOS window (PSR=1.0, DSR_relative_B4=1.0 confirm the OOS Sharpe is statistically real). The SUSPICIOUS classification is orthogonal — it flags the IS/OOS DIVERGENCE as regime exposure, not the OOS number as fabricated.

## 5. PATH classification — SUSPICIOUS-OOS-DOMINANT

**SUSPICIOUS-OOS-DOMINANT** per brief Section 8.4 LOCKED disjunctive gate. The classifier fires on two independent grounds:

1. **OOS/IS ratio gate** — OOS/IS monthly Sharpe ratio = **6.847 > 3.0** → SUSPICIOUS fires unconditionally per `feedback_v3_oos_is_ratio_gate.md`, regardless of absolute OOS Sharpe magnitude.
2. **OOS-DOMINANT sub-mode** — OOS shift ≥ +0.20 (observed +1.7622) AND IS shift < +0.10 (observed -0.5546).

**SUSPICIOUS supersedes NEGATIVE.** The IS Δ of **-0.5546** independently fires the Section 8.2 NEGATIVE gate (IS shift < -0.10). When both classifications fire concurrently, SUSPICIOUS takes classification precedence per the established /071 precedent — there is **no magnitude qualifier**; the precedence is unconditional. Brief Section 8.4 LOCKED the disjunctive evaluation order: SUSPICIOUS first, then NEGATIVE, then PROMISING, then INERT. Both classifications converge on the same disposition — **the per-symbol SL-widening axis is closed at catalog level and does NOT advance to cycle 2 CONFIRMATION** — but the diary records the SUSPICIOUS label as canonical per the precedence rule (Critic Rec #3).

PROMISING is ruled out: the pre-registered conjunctive PROMISING condition required IS ≥ +0.9325 AND OOS ≥ +0.3403; observed IS = +0.2779 fails the IS gate. The strong OOS does not rescue PROMISING — `feedback_v3_strict_both_is_oos_baseline.md` requires BOTH axes, and the regime-exposed IS collapse is exactly the failure that rule was written to catch.

## 6. THE KEY FINDING — 3-consecutive SUSPICIOUS-OOS-DOMINANT regime-divergence signal

This is the cycle-level finding of iter-v3/073, exceeding any per-iteration verdict (Critic Q3, the most important finding of the iteration).

**Three consecutive cycle-1+2 iterations have classified SUSPICIOUS-OOS-DOMINANT with monotonically escalating OOS/IS Sharpe ratios:**

| Iter | Axis | IS Δ | OOS Δ | OOS/IS ratio | Disposition |
|---|---|---:|---:|---:|---|
| /065 | Universal SL widening (2.0,1.0)→(2.0,1.5) | -0.28 | +0.71 | **2.87** (below 3.0 gate) | SUSPICIOUS-OOS-DOMINANT sub-mode; rejected |
| /071 | Meta-labeling (M2 take/skip filter) | -0.12 | +0.63 | **4.51** | SUSPICIOUS-OOS-DOMINANT; fails ratio gate |
| **/073** | **Per-symbol triple-barrier asymmetry (BCH/LDO SL→1.25)** | **-0.55** | **+1.76** | **6.85** | **SUSPICIOUS-OOS-DOMINANT; most extreme ratio in v3 history** |

(For completeness: /070, the CONFIRMATION of the /065 bundle, saw the IS collapse AMPLIFY to -0.97 at multi-seed — the frozen-baseline artifact dissolved and the underlying IS weakness became fully visible. The /065→/070 trajectory is the controlling precedent for what /073's multi-seed CONFIRMATION would do.)

**All three axes share ONE mechanism: each EXTENDS EFFECTIVE TRADE HOLDING TIME.**
- /065 — a wider SL lets trades ride longer before stopping out.
- /071 — meta-labeling filters to fewer, higher-confidence trades that are held longer (the M2 veto removes the early stop-outs).
- /073 — per-symbol barrier rebalancing widens the BCH/LDO SL arm (1.0→1.25) and, for LDO, shortens the TP arm — both push trades toward longer survival before resolution.

**Why the mechanism loads a regime factor.** v3's IS window (2022-09 → 2025-03) spans the 2022 bear market, 2023 chop, the 2024 bull, and the 2024-Q4/2025-Q1 deceleration — a mixed regime that **penalizes longer-held trades** (in bear/chop, a trade held longer simply bleeds longer). v3's OOS window (2025-03 → 2026-05) is a persistent BCH/LDO/TRX uptrend that **rewards longer-held trades** (in a trend, riding longer captures more of the move). Any holding-time-extension axis therefore mechanically loads this IS/OOS regime difference: OOS Sharpe soars, IS Sharpe collapses, the OOS/IS ratio inflates. Three independent axes — touching the SL barrier, the labeling architecture, and per-symbol barrier asymmetry respectively — all produced the same signature with escalating leverage. This is structural to v3's data split, not a property of any one axis.

**Consequence for the cycle agenda.** The holding-time-extension axis family is a SATURATED axis family. It will reproduce SUSPICIOUS-OOS-DOMINANT a fourth time if re-tried. The finding is codified in `feedback_v3_is_oos_regime_divergence.md` (created at this closeout) and pre-registered in `briefs-v3/exploration_catalog.md` so it constrains the remaining cycle 2 agenda and is not re-discovered a fourth time (Critic Rec #2).

## 7. BASELINE_V3.md status

**UNCHANGED** — /059 stays canonical at `v0.v3-059` (IS +1.0894 / OOS +0.5791). A SUSPICIOUS-OOS-DOMINANT EXPLORATION does not update BASELINE_V3.md: it does not advance to CONFIRMATION, and `feedback_v3_strict_both_is_oos_baseline.md` requires BOTH IS and OOS to improve (the IS collapse to +0.2779 fails this on its own). **No new tag issued.**

## 8. Critic Recommendations carried forward

1. **Cycle 2 #4 (/074) must NOT be another holding-time-extension axis.** Three consecutive SUSPICIOUS-OOS-DOMINANT (/065, /071, /073) with escalating ratios is a saturated signal — any axis lengthening effective holding time (wider SL, meta-labeling filtration, per-symbol barrier rebalancing, timeout extension) loads the v3 IS/OOS regime factor and trips the ratio gate. Per `feedback_v3_axis_saturation_predictor.md`, this family is saturated. /074's QR EDA must select a **holding-time-orthogonal axis** OR a **dedicated IS/OOS regime-diagnostic axis** (regime-stratified IS sub-period analysis: how does a candidate perform in the IS bull 2024-01→2025-03 vs the IS bear/chop 2022-09→2023-12?).

2. **The 3-consecutive-SUSPICIOUS pattern warrants a pre-registered entry in `briefs-v3/exploration_catalog.md` AND a memory rule** — not just a diary line. The finding (v3's IS and OOS regimes are structurally divergent; holding-time-extension axes mechanically exploit this) is cycle-level and must constrain the remaining cycle 2 agenda. Codified at this closeout as `feedback_v3_is_oos_regime_divergence.md`.

3. **QR Phase 8 diary should record the SUSPICIOUS-precedence-over-NEGATIVE application explicitly.** IS Δ -0.5546 independently fires the Section 8.2 NEGATIVE gate; SUSPICIOUS supersedes per the /071 precedent (no magnitude qualifier). Both classifications converge on "do not advance." Recorded in Section 5 above.

## 9. Next Iteration Ideas

Cycle 2 progress: 3/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /071 | META-LABELING (same-feature M2) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /072 | ALTERNATIVE LABELING (fixed-horizon) | NEGATIVE |
| #3 | /073 | PER-SYMBOL LABELING (per-symbol triple-barrier asymmetry) | SUSPICIOUS-OOS-DOMINANT |
| #4 | /074 | TBD per QR EDA — **HARD CONSTRAINT: holding-time-orthogonal OR regime-diagnostic** | — |

**The labeling-architecture axis family is now substantially explored and substantially exhausted within cycle 2.** Three of three labeling-family axes have failed to produce a clean PROMISING:
- Same-feature meta-labeling — SUSPICIOUS-OOS-DOMINANT (holding-time extension).
- Fixed-horizon labeling — NEGATIVE (label-execution decoupled).
- Per-symbol triple-barrier asymmetry — SUSPICIOUS-OOS-DOMINANT (holding-time extension).

**iter-v3/074 axis — HARD CONSTRAINT (Critic Rec #1):** /074 must NOT be a holding-time-extension axis. The QR EDA must select from:

1. **A holding-time-orthogonal axis.** Candidates that do NOT change mean/median trade duration:
   - NEW feature families that do not touch the labeling/exit machinery — funding-rate features (8h cadence is funding-aligned; retest at n_trials=35), open-interest delta features, cross-exchange basis, BTC-dominance regime features. The mass-feature-expansion mandate (`feedback_v3_mass_feature_expansion.md`, cycle 5) is the longer-horizon version of this; a single NEW feature family at cycle 2 is the structural-axis option here.
   - The TRX/2022-Q4 regime gate (a binary regime-conditional kill switch — orthogonal to holding time per `feedback_v3_concentration_is_signal.md`; addresses a standing BASELINE_V3.md constraint).
2. **A dedicated IS/OOS regime-diagnostic axis.** Regime-stratified IS sub-period analysis — split the IS window into bull (2024-01→2025-03) and bear/chop (2022-09→2023-12) sub-periods and measure how the current baseline and any candidate change perform in each. This would directly characterize the regime factor that /065/071/073 keep loading, and would tell the cycle whether ANY axis can lift IS bear/chop performance without the OOS-bull-only inflation.

Per `feedback_v3_axis_selection_quant_discipline.md`, the /074 axis selection MUST be made by the QR with an EDA-driven quantitative basis (committed `analysis/iteration_v3-074/*.py` before the brief), and the brief Section 2 must contain EDA-derived numerical tables. Per `feedback_v3_is_oos_regime_divergence.md` (created at this closeout), the /074 brief Section 2 must additionally include a **holding-time-effect predictor**: an explicit statement of whether the proposed axis changes mean/median trade duration. If it does, it loads the regime factor and will reproduce SUSPICIOUS-OOS-DOMINANT — and must be rejected at brief stage.

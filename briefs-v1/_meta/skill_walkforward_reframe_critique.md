# v1 Skill — Walk-Forward Semantics & Regime-Ensemble Reframe Critique

**Date**: 2026-05-31
**Trigger**: User directive 2026-05-31 (load-bearing) — IS/OOS in this framework is NOT a classical train/test split; it is a researcher-discipline boundary inside a monthly walk-forward pipeline. The end goal is a regime-ensemble bundle where component models can each specialize in their own regime — an IS-strong / OOS-modest model is a *regime contributor*, not an "overfit reject".
**Skill file under review**: `/home/roberto/crypto-trade/.worktrees/quant-research/.claude/commands/quant-iteration-v1.md` (1343 lines)
**Author**: Quant Research consultant (Opus 4.7)

---

## Executive Summary

The v1 skill is structurally rigorous but **semantically miscalibrated** for the framework it actually implements. Across at least a dozen load-bearing locations, IS/OOS is treated as the López de Prado / equities-style train→test bisection. The actual mechanic is:

- **Walk-forward**: every month the model retrains on the past 24 months and predicts the next month. Both IS and OOS undergo the *same* walk-forward.
- **Embargo** (`walk_forward.py:113` — `train_end_ms = test_start_ms - embargo_ms`) prevents label leakage at *every* fold boundary — IS-internal AND OOS-internal.
- **IS/OOS is a researcher-discipline boundary**, not a leakage-prevention split. Its purpose is to keep the QR honest during design (Phases 1–5) — NOT to prevent the model from cheating.

This misframing has produced a verdict logic that **systematically kills regime specialists**. A model with IS Sharpe +2.5 / OOS Sharpe +0.3 might be a perfect bull-regime contributor — the IS spans 5 multi-regime years (2020-2025) and the OOS is a single ~7-month regime (2025-03 → 2025-10). Demanding `OOS/IS ≥ 0.5` rejects exactly the kind of regime-specific edge that, when bundled with complementary specialists, would produce a regime-free unified model.

The reframe required:

1. **Mission statement**: v1 builds a *bundle* of regime specialists. Individual models do not need to be universal.
2. **Walk-forward semantics**: state explicitly at the top that BOTH IS and OOS run the same train-predict mechanic; OOS is a researcher-honesty zone.
3. **Verdict bands**: add `REGIME-SPECIALIST-IS`, `REGIME-SPECIALIST-OOS`, `TAIL-CONTROL`, `UNIVERSAL` cells alongside the existing PROMISING/NEGATIVE.
4. **Gates**: relax `OOS/IS ≥ 0.5` as a hard merge gate for component candidates; retain it only for *universal-model* CONFIRMATIONs. Add regime-attribution analysis as the load-bearing signal for component candidates.
5. **CONFIRMATION semantics**: a CONFIRMATION is *bundle assembly*, not single-model validation. Components contribute regime coverage; the bundle's composite OOS is what matters.

---

## Section A — Walk-Forward Semantics Misframing

### A.1 — `quant-iteration-v1.md:141-160` — "THE MOST IMPORTANT RULE: IS/OOS Data Split"

**Current text** (lines 141-160):

> ## THE MOST IMPORTANT RULE: IS/OOS Data Split
> ```
> OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
> training_months = 24             ← FIXED. NEVER CHANGES.
> ```
> This split exists to prevent **researcher overfitting** — not model leakage. The walk-forward / CPCV backtest already prevents model-level leakage by training only on past data each month, with embargo.

**Diagnosis**: This section is the ONLY place where the correct framing is stated — but it is buried, partial, and contradicted by surrounding sections. Critically, it asserts the right principle ("not model leakage") but then continues with `comparison.csv` `ratio` and `OOS/IS Sharpe ≥ 0.5` as a load-bearing gate, which only makes sense under the *classical* (and incorrect) framing.

**Severity**: HIGH — the most important section is internally inconsistent.

### A.2 — `quant-iteration-v1.md:65-67` — Sacred constants block

**Current text** (lines 65-67):

> - Walk-forward backtest runs on full data; reports split at `OOS_CUTOFF_DATE`
> - Forming candles must be dropped (`fetcher.py:if k.close_time < now_ms`)
> - **Walk-forward train_end_ms = test_start_ms - embargo_ms** (the iter-v3/058 fix; cannot regress)

**Diagnosis**: The mechanic IS stated ("Walk-forward backtest runs on full data; reports split at OOS_CUTOFF_DATE") but it does NOT explain that this means IS and OOS both undergo the *same* monthly train-predict cycle. A new agent reads this and infers "the IS is the training data, the OOS is the test data".

**Severity**: MEDIUM — correct but underexplained.

### A.3 — `quant-iteration-v1.md:151-156` — "What the split means" block

**Current text**:

> - The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during Phases 1–5 (design).
> - The **walk-forward / CPCV backtest runs on ALL data** (IS + OOS) as one continuous process. No artificial wall at the model level. The backtest rolls through OOS exactly as it would in live trading.

**Diagnosis**: Lines 151-154 are correct. Line 158 (the `OOS/IS Sharpe ≥ 0.5` gate) contradicts them by treating the gap as a generalization signal — when, under correct walk-forward semantics, the gap is regime-driven, not generalization-driven.

**Severity**: HIGH — adjacent correct and incorrect framing on the same page.

### A.4 — `quant-iteration-v1.md:10` — Mission opening

**Current text**:

> Then at iter-v3/058 we discovered a serious walk-forward look-ahead bug: `train_end_ms = test_start_ms` with no embargo, allowing training labels to scan forward into the test window. The fix landed at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`).

**Diagnosis**: This is correct, but the framing of "test window" is loaded. In walk-forward, every month has a "test window" — there is no single test window. The embargo applies *every month*, IS and OOS alike. A reader inferring "training labels scanned into the OOS test window" misses the point that the bug affected every month boundary.

**Severity**: LOW — directionally correct.

---

## Section B — "Overfit" Misclassification Rules

### B.1 — `quant-iteration-v1.md:158` — `OOS / IS Sharpe ≥ 0.5` floor

**Current text** (line 158):

> The IS/OOS gap in `comparison.csv` tells you whether the researcher's design choices generalize beyond the data they could see. Hard floor: `OOS_Sharpe / IS_Sharpe ≥ 0.5` per project memory.

**Diagnosis**: This is the single most damaging line in the skill. Under the regime-ensemble framing:
- IS = ~5 years × ~6 regimes (2020 bull, 2021 alt-season, 2022 bear, 2023 chop, 2024 ETF-recovery, 2025-Q1 chop)
- OOS = ~7 months × 1-2 regimes (2025-03 → 2025-10)
- An IS Sharpe of +2.5 averaged over 6 regimes against an OOS Sharpe of +0.5 in a regime the model wasn't strong in is **not overfitting** — it's regime mismatch. The model may be a perfect regime-X specialist for which 2025-03-onward doesn't contain regime-X.

A bundle of 6 regime specialists with averaged OOS/IS = 0.30 each could produce a bundle OOS/IS = 0.95 — by construction.

**Severity**: CRITICAL — this gate auto-rejects regime specialists by design.

### B.2 — `quant-iteration-v1.md:817-820` — EXPLORATION verdict cells

**Current text** (lines 815-820):

> | `EXPLORATION-PROMISING` | ≥ +0.05 | Single-seed lift, no confound flagged | Log to catalog, candidate for CONFIRMATION bundle |
> | `EXPLORATION-NEGATIVE` | < 0 OR < +0.05 | No signal | Log to catalog as dead-end; next EXPLORATION |

**Diagnosis**: The verdict is keyed on `OOS Sharpe Δ` only. A model that is +2.0 IS Sharpe Δ but -0.10 OOS Sharpe Δ is auto-NEGATIVE. But that model might be the *exact* regime contributor the bundle needs for periods absent from OOS. The verdict logic has no way to express "regime specialist found — bundle dependent".

**Severity**: HIGH — closes off entire axis of regime exploration.

### B.3 — Implicit "overfit" framing across the skill

The word "overfit" / "overfitting" appears in lines 12, 23, 137, 148, 200, 1338-onward. In every occurrence except line 148 (the correct framing of "researcher overfitting" vs model leakage), the framing treats IS strength + OOS weakness as evidence of overfit. Under walk-forward, this is **structurally false**:
- The model retrains every month — it cannot "overfit" the entire IS in the way a single-fit model overfits training data
- It CAN overfit each month's training window — but the embargo + 24-month rolling re-fit is the structural defense
- IS strength is evidence the strategy works in the regimes IS contains. OOS weakness is evidence the regime mix changed.

**Severity**: HIGH — pervasive miscalibration.

### B.4 — `quant-iteration-v1.md:1330` — Key reminder

**Current text**:

> PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.

**Diagnosis**: PBO/DSR/PSR are well-defined under walk-forward and CPCV — they DO measure something legitimate (selection bias across N trials, deflated Sharpe under multiple testing). These should be retained. The issue is NOT these gates; it is the `OOS/IS ≥ 0.5` ratio (line 158) and the simple `OOS Sharpe Δ` verdict logic (line 815-820).

**Severity**: NONE — this gate is correct.

---

## Section C — Merge Gates That Reject Regime Specialists

### C.1 — `quant-iteration-v1.md:255` — "OOS / IS Sharpe ratio ≥ 0.5"

**Current text** (line 255):

> - OOS / IS Sharpe ratio ≥ 0.5

Listed alongside `IS Sharpe > 1.0`, `OOS Sharpe > 1.0`, `≥10 trades/month OOS`, etc. as inherited project-level merge gates.

**Diagnosis**: Same as B.1. This is a *universal-model* gate — it makes sense if you are evaluating a single model that claims to be regime-free. It does NOT make sense for evaluating a regime-specialist component candidate for bundle inclusion.

**Severity**: CRITICAL.

### C.2 — `quant-iteration-v1.md:825-829` — CONFIRMATION verdict gates

**Current text** (lines 824-829):

> | `CONFIRMATION-MERGE` | All gates PASS; DSR > 0.95; PBO < 0.4; PSR > 0.95; Sharpe floors met | Update BASELINE_V1.md; tag commit |

**Diagnosis**: "Sharpe floors met" cross-references line 254-255 (`IS Sharpe > 1.0 AND OOS Sharpe > 1.0 AND OOS/IS ≥ 0.5`). For a *bundle* CONFIRMATION (assembled from N regime specialists), the bundle-level OOS Sharpe is what should clear the floor. For a *component* CONFIRMATION, the component's regime-attributed Sharpe is the right metric, not OOS Sharpe vs IS Sharpe ratio.

**Severity**: HIGH.

### C.3 — `quant-iteration-v1.md:524` — EXPLORATION verdict bands

**Current text**:

> Critic emits `EXPLORATION-PROMISING` (signal found, candidate for CONFIRMATION inclusion) or `EXPLORATION-NEGATIVE` (no signal, recorded in catalog).

**Diagnosis**: Binary verdict on a multi-dimensional outcome. A model can be:
- IS-PROMISING + OOS-MATCHING → universal contributor (the unicorn)
- IS-PROMISING + OOS-FLAT → bull-regime contributor (if IS bull-leaning)
- IS-FLAT + OOS-PROMISING → bear-regime contributor (if OOS bear-leaning)
- IS-PROMISING + OOS-NEGATIVE → regime-shift sensitive; potentially still useful if the rejected OOS regime is covered by another component
- IS-FLAT + OOS-FLAT → genuinely dead

The current 2-band logic collapses these into PROMISING/NEGATIVE.

**Severity**: HIGH.

### C.4 — `quant-iteration-v1.md:1170` — Diary Critic Review Summary

**Current text** (line 1166):

> - Check 3 (DSR/PBO/PSR): PASS / FAIL

**Diagnosis**: Check 3 lumps three independent metrics. Worse, the gate is BINARY. A model that fails DSR at single-seed EXPLORATION (low n_trials → low E[max_SR]) is automatically NEGATIVE even if it shows clear regime-specialist signal in regime-attributed analysis.

**Severity**: MEDIUM.

---

## Section D — Missing Concepts

### D.1 — Missing: Walk-Forward Semantics Statement at Top

The skill should open (after the Mission section) with an explicit **"How the Backtest Works"** section that says, verbatim:

> Every month, the model is retrained on the past 24 months of klines and predicts the next month. The walk-forward harness (`walk_forward.py`) carries an embargo: `train_end_ms = test_start_ms - embargo_ms` (the iter-v3/058 fix). Both IS (pre-2025-03-24) and OOS (post-2025-03-24) undergo this SAME train-predict cycle. The IS/OOS boundary is NOT a leakage boundary — it is a researcher-honesty boundary. The QR sees only IS during design (Phases 1-5); OOS is revealed in Phase 7. The walk-forward and embargo are the leakage defense.

### D.2 — Missing: Regime-Ensemble Goal as Core Mission

The Mission (lines 8-26) talks about rigor, López de Prado, no p-hacking — all correct, but never mentions that the END GOAL is a *bundle* of complementary regime specialists. Add:

> **The bundle is the product.** Individual EXPLORATIONs identify regime specialists (a model that works in bull, a model that works in chop, a model that controls tail in bear). CONFIRMATIONs *combine* specialists into a bundle whose composite OOS is regime-balanced. A model is not evaluated as a standalone universal predictor — it is evaluated as a contributor to a regime portfolio. An IS-strong / OOS-weak model is a regime specialist when its IS strength was in regimes absent from OOS.

### D.3 — Missing: How to Evaluate a Model as a Regime Contributor

Currently the skill has no methodology for:
- **Regime tagging** of IS and OOS windows (bull / chop / bear / tail / liquidation-cascade / vol-spike)
- **Per-regime attribution** of model PnL (within-regime Sharpe, within-regime drawdown)
- **Bundle composition score** (does adding this specialist to the existing bundle improve regime coverage?)
- **Regime gap analysis** (which regimes does the current bundle UNDER-cover, and what specialist would fill that gap?)

This is the load-bearing missing infrastructure. Without it, the REGIME-SPECIALIST verdict bands have no measurable basis.

### D.4 — Missing: CONFIRMATION as Portfolio Composition

Currently the skill describes CONFIRMATION as: "bundle of best EXPLORATIONS" (line 297) and "Section 3 lists which features/symbols/labels are imported from which prior EXPLORATION" (line 297). This treats CONFIRMATION as a *feature/data merge*, not as a *portfolio composition*.

The reframe: a CONFIRMATION is the act of *combining N component models* (each from prior EXPLORATIONs) into a unified prediction (via stacking, ensembling, regime-conditional dispatch, or whatever the cohort allows). The CONFIRMATION's "best" criterion is bundle-level OOS Sharpe — and individual components can have OOS Sharpe < IS Sharpe / 2 and still contribute if they fill a regime gap.

### D.5 — Missing: Verdict Band Augmentation

The current 2-band EXPLORATION verdict (PROMISING / NEGATIVE) needs to become a 5-band verdict:

| Band | IS Sharpe Δ | OOS Sharpe Δ | Bundle role |
|---|---|---|---|
| `REGIME-SPECIALIST-IS` | ≥ +0.10 | ≤ +0.05 | Specialist for regimes present in IS, absent from OOS; bundle-candidate if attribution shows clean regime-locked strength |
| `REGIME-SPECIALIST-OOS` | ≤ +0.05 | ≥ +0.10 | Specialist for OOS regimes; bundle-candidate if OOS regimes are reasonably represented historically |
| `TAIL-CONTROL` | any | any | Drawdown-reducing component (e.g., regime-conditional kill switch); evaluated on max_drawdown / OOS_min_month_pnl, not Sharpe |
| `UNIVERSAL` | ≥ +0.05 | ≥ +0.05 | Generalizes across IS and OOS regimes; rare, bundle-anchor candidate |
| `EXPLORATION-NEGATIVE` | ≤ 0 IS | ≤ 0 OOS | Genuinely dead; logged to dead-paths catalog |

### D.6 — Missing: IS as Research-Data-Only Statement

Currently the QR's IS-only access during Phases 1-5 is stated (line 152) but the *purpose* is mis-stated. The skill should add:

> **IS is the QR's research data.** It is what you read, analyze, EDA over, design briefs against. It is NOT the model's training data — every month's model has its OWN training window (the past 24 months) carved fresh from the rolling walk-forward. When the QR talks about "the model trained on IS", that is shorthand for "the cumulative behavior of the walk-forward within the IS window". The model retrains 60+ times across IS (one per IS month). It is not a single fit.

---

## Section E — Specific Edit Proposals

Below: CURRENT text and PROPOSED text for each load-bearing fix. Line numbers reference `quant-iteration-v1.md` at the state of 2026-05-31.

### Edit 1 — Replace the "THE MOST IMPORTANT RULE" section header + body

**CURRENT (lines 141-160)**:

```markdown
## THE MOST IMPORTANT RULE: IS/OOS Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
training_months = 24             ← FIXED. NEVER CHANGES.
```

This split exists to prevent **researcher overfitting** — not model leakage. The walk-forward / CPCV backtest already prevents model-level leakage by training only on past data each month, with embargo.

### What the split means

- The **Quant Researcher** uses ONLY IS data (before 2025-03-24) during Phases 1–5 (design). This prevents the researcher from unconsciously tuning features, labeling, or parameters to fit recent patterns.
- The **walk-forward / CPCV backtest runs on ALL data** (IS + OOS) as one continuous process. No artificial wall at the model level. The backtest rolls through OOS exactly as it would in live trading.
- The **LightGBM Master** in Phase 4.5 uses only IS data, prior diaries, and prior iteration reports. NO OOS access.
- The **reporting layer** splits trade results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` report directories plus a `comparison.csv` with OOS/IS ratios.
- The **Quant Researcher** sees OOS results for the FIRST time in Phase 7 (evaluation).

The IS/OOS gap in `comparison.csv` tells you whether the researcher's design choices generalize beyond the data they could see. Hard floor: `OOS_Sharpe / IS_Sharpe ≥ 0.5` per project memory.

This constant lives in `src/crypto_trade/config.py`.
```

**PROPOSED**:

```markdown
## THE MOST IMPORTANT RULE: Walk-Forward, IS/OOS, and the Regime Bundle

### How the backtest actually works

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
training_months = 24             ← FIXED. NEVER CHANGES.
```

**This is a WALK-FORWARD framework — not a classical train/test split.**

Every month, for every (model, symbol) cell, the system:
1. Trains a fresh LightGBM on the past `training_months=24` months of klines + features
2. Predicts the upcoming month's signals
3. Trades those signals via the backtest's order manager + risk gates
4. Moves the window forward one month and repeats

The walk-forward harness (`walk_forward.py:113`) carries the embargo: `train_end_ms = test_start_ms - embargo_ms`. This embargo is applied at EVERY month boundary — IS-internal AND OOS-internal. It is the structural defense against label leakage from triple-barrier label horizons spilling into the next training fold.

**Both IS (pre-2025-03-24) and OOS (post-2025-03-24) undergo the SAME monthly train-predict cycle.** OOS is not a held-out test window in the classical sense; it is a held-out *researcher-honesty* window.

### What the IS/OOS split actually means

- **IS = the QR's research data.** It is what you read, analyze, EDA over, design briefs against. It is NOT a single training set. Each IS month's prediction comes from a model that was trained on the 24 months PRIOR to that month — fresh refit per month.
- **OOS = the researcher-honesty zone.** The QR may NOT look at OOS during Phases 1-5. The point is to prevent the QR from unconsciously tuning features, labeling, or parameters to fit recent patterns the QR has seen.
- **The walk-forward + embargo prevents MODEL leakage.** The IS/OOS boundary prevents RESEARCHER leakage. Two different defenses, two different failure modes.
- **Reports split at `OOS_CUTOFF_DATE`** into `in_sample/` and `out_of_sample/` for accounting clarity, not because the model crosses any wall there.
- **The QR sees OOS results for the FIRST time in Phase 7.**

### The end goal: a regime-ensemble bundle

v1's mission is **NOT to build a single universal model.** It is to build a *bundle* of complementary models, each contributing edge in different market regimes (bull, chop, bear, vol-spike, liquidation-cascade, ETF-flow, etc.). The bundle's composite OOS — averaged across regime contributors — is what trades live.

This has critical verdict implications:

- **An IS-strong / OOS-modest model is NOT inherently overfit.** IS spans ~5 years and ~6 regimes; OOS spans ~7 months and 1-2 regimes. A model that crushed bull-2020 + alt-2021 + chop-2023 (all in IS) but only matched the bull-recovery of 2025-Q2-Q3 (OOS) is a *regime specialist* — a bundle candidate.
- **`OOS/IS Sharpe ≥ 0.5` is a UNIVERSAL-MODEL gate, NOT a bundle-component gate.** It is retained for full-bundle CONFIRMATIONs (where you ARE claiming a unified regime-free predictor). It is RELAXED for individual EXPLORATION component candidates — replaced by regime-attribution analysis.
- **The right verdict for a component candidate is multi-band**, not binary PROMISING/NEGATIVE. See §"Verdict Cells" below.

### The IS/OOS gap — what it tells you

| Pattern | Interpretation |
|---|---|
| IS Sharpe strong + OOS Sharpe strong + both regimes match | UNIVERSAL contributor (rare, anchor candidate) |
| IS Sharpe strong + OOS Sharpe weak BUT regime mix differs | REGIME-SPECIALIST-IS — bundle-candidate if attribution shows clean within-regime edge |
| IS Sharpe weak + OOS Sharpe strong | REGIME-SPECIALIST-OOS — bundle-candidate if OOS regime is historically common |
| IS Sharpe weak + OOS Sharpe weak | EXPLORATION-NEGATIVE — dead-paths catalog |
| Drawdown reduced without Sharpe lift | TAIL-CONTROL — evaluated on regime tail metrics, not Sharpe |

The IS-OOS gap is a *regime-mix signal*, not a generalization signal. To distinguish regime mismatch from researcher overfit, run regime-attributed PnL analysis on both IS and OOS — if within-regime Sharpes match, it's regime mix; if within-regime Sharpes don't match, the QR may have unconsciously snooped.

This constant lives in `src/crypto_trade/config.py`.
```

### Edit 2 — Update Mission to state the bundle goal

**CURRENT (line 22)**:

```
v1 is now the **rigor + creator-role-augmented track**, parallel to v2 (diversification arm) and v3 (rigor-only arm). All three coexist.
```

**PROPOSED — append after line 22**:

```
**The bundle is the product.** v1's mission is to build a *regime-ensemble bundle* — N complementary models where each is strong in some regime, and the composite is regime-balanced. Individual EXPLORATIONs are *component candidates* — a model that crushes bull regimes but flat-lines in chop is a bull specialist, not an overfit reject. CONFIRMATIONs are *bundle assemblies* — combining components (via stacking, ensembling, regime-conditional dispatch) and validating the composite OOS. Edge is measured at the bundle level; rigor is measured per-component (no look-ahead, embargo applied, etc.).

We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly — sometimes with a bull specialist, sometimes with a chop specialist, sometimes with a tail-control gate. The bundle is regime-free; the components are not, by design.
```

### Edit 3 — Update inherited project-level merge gates

**CURRENT (lines 252-260)**:

```markdown
Plus inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

**Any single gate failure = NO-MERGE.** This is by design — gates prevent weird trade-offs ("OOS Sharpe is 2.5 but only 8 trades" is not acceptable).
```

**PROPOSED**:

```markdown
Plus inherited project-level merge gates — applied differently to **component candidates** vs **bundle CONFIRMATIONs**:

#### Bundle-level (full-stack CONFIRMATION-MERGE gates)

The bundle as a whole must clear:

- Bundle OOS monthly Sharpe > 1.0
- Bundle OOS / IS Sharpe ratio ≥ 0.5 (the bundle, not any single component)
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable
- DSR > 0.95, PBO < 0.4, PSR > 0.95

#### Component-level (EXPLORATION-PROMISING evaluation)

A component candidate is evaluated on:

- Within-regime Sharpe (NOT OOS/IS ratio) — at least one tagged regime with Sharpe > 1.0 and within-regime trade count ≥ 30
- Regime-attribution clarity — the component's PnL should concentrate in specific tagged regimes, not be scattered noise
- Bundle composition lift — adding this component to the current bundle (by stacking/dispatch simulation on IS) should improve at least one regime's bundle-attributed Sharpe by ≥ 0.10
- No look-ahead / embargo correct / standard methodology floors (these are NOT relaxed)

**A component can be EXPLORATION-PROMISING even with OOS/IS < 0.5 if regime attribution explains the gap.** The bundle CONFIRMATION is where the OOS/IS ratio is enforced — at the bundle level.

**Any methodology gate failure = NO-MERGE.** This is by design — gates prevent fake edge. Regime mismatch is NOT a methodology failure; researcher overfit IS.
```

### Edit 4 — Update EXPLORATION verdict cells

**CURRENT (lines 812-820)**:

```markdown
### EXPLORATION verdict cells

| Verdict | OOS Sharpe Δ | Condition | Next step |
|---|---|---|---|
| `EXPLORATION-PROMISING` | ≥ +0.05 | Single-seed lift, no confound flagged | Log to catalog, candidate for CONFIRMATION bundle |
| `EXPLORATION-NEGATIVE` | < 0 OR < +0.05 | No signal | Log to catalog as dead-end; next EXPLORATION |
| `NEGATIVE-no-effect` | main Δ ≈ 0 (within ±0.10 of baseline) | Axis had no effect; saturated or under-powered | Log to catalog; try higher n_trials or different axis |
```

**PROPOSED**:

```markdown
### EXPLORATION verdict cells (REGIME-AWARE)

| Verdict | IS Sharpe Δ | OOS Sharpe Δ | Regime attribution | Next step |
|---|---|---|---|---|
| `UNIVERSAL` | ≥ +0.05 | ≥ +0.05 | Lift broadly distributed across regimes | Anchor candidate for next CONFIRMATION |
| `REGIME-SPECIALIST-IS` | ≥ +0.10 | ≤ +0.05 (and ≥ -0.20) | Lift concentrated in IS-only regimes (e.g., bull-2021, chop-2023) | Bundle candidate for regimes absent from OOS |
| `REGIME-SPECIALIST-OOS` | ≤ +0.05 (and ≥ -0.20) | ≥ +0.10 | Lift concentrated in OOS regimes | Bundle candidate if OOS regime is recurring historically |
| `TAIL-CONTROL` | any | any | Reduces max_drawdown / OOS_min_month_pnl by ≥ 20% | Bundle candidate as risk overlay (evaluated on tail metrics, not Sharpe) |
| `EXPLORATION-PROMISING` | ≥ +0.05 | ≥ +0.05 | Lift present but not yet regime-attributed | Log to catalog; next EXPLORATION or CONFIRMATION inclusion |
| `EXPLORATION-NEGATIVE` | ≤ 0 OR catastrophic OOS | — | No signal in any regime | Dead-paths catalog |
| `NEGATIVE-no-effect` | within ±0.10 of baseline | within ±0.10 | Axis had no effect; saturated or under-powered | Catalog; try higher n_trials or pivot axis |
| `LEARNED-NEG` | OOS catastrophic + clear regime explanation | — | Lost a regime the QR thought it would capture | Dead-paths + regime-tag the failure mechanism |

**Regime attribution is the load-bearing signal**, not OOS Sharpe Δ alone. A regime-attribution table is part of Phase 7.4 LM Master post-mortem output (new mandatory section).

Note: iterations CAN and SHOULD produce different configurations from the baseline (different features, labeling, weights, etc.) — this is the purpose of optimization. Different trades vs baseline is EXPECTED. The comparison metric is regime-attributed component PnL vs the existing bundle's regime coverage — NOT OOS Sharpe / PnL / drawdown vs the BASELINE_V1 anchor in isolation.
```

### Edit 5 — Add new mandatory brief section (Section 10 — Regime Attribution Plan)

**PROPOSED — insert after Section 9 (line ~1134)**:

```markdown
## Section 10 — Regime Attribution Plan (NEW v1, regime-ensemble mandate)

State explicitly:

- **Target regime(s)**: which regime(s) this iteration is hypothesized to specialize in (bull / alt-rotation / chop / bear / vol-spike / liquidation-cascade / ETF-flow / etc.)
- **Why this regime**: 1-2 sentences of mechanism (e.g., "momentum features should produce lift in trending regimes; this iter adds 5-day ret_signed × hurst_100 to formalize trend-strength")
- **Off-regime expectation**: what we expect this iteration to do in OFF-target regimes (flat? small loss? we don't know?)
- **Bundle role**: candidate for {anchor / bull-specialist / chop-specialist / bear-specialist / tail-control / universal}
- **Composition simulation**: if PROMISING in target regime, how would this component combine with the existing bundle? (stacking? regime-conditional dispatch? ensemble averaging?)
- **Falsifier (regime-aware)**: "if target-regime IS Sharpe < X, hypothesis is rejected" — NOT "if OOS Sharpe < X" (because OOS may not contain target regime)
```

### Edit 6 — Replace Critic Check 3 wording

**CURRENT (line 1166)**:

```
- Check 3 (DSR/PBO/PSR): PASS / FAIL
```

**PROPOSED**:

```
- Check 3a (DSR/PSR — methodology gate): PASS / FAIL (CONFIRMATION-only; EXPLORATION skips)
- Check 3b (PBO — selection-bias gate): PASS / FAIL (CONFIRMATION-only)
- Check 3c (Regime attribution clarity — component-candidate gate): PASS / WARN / FAIL (EXPLORATION + CONFIRMATION)
- Check 3d (Bundle-level OOS/IS ≥ 0.5): PASS / FAIL (BUNDLE-CONFIRMATION-only; component EXPLORATIONs are exempt)
```

### Edit 7 — Add regime-attribution mandate to LM Master Phase 7.4 deliverable

**CURRENT (lines 707-719)**:

```markdown
Phase 7.4 section appended to `lgbm_advisor.md`. ~500-1000 words covering:

1. **Feature importance triage**: top performers, dead weight (rank 14/14 candidates), unstable features
2. **Hyperparameter trial stability**: best-trial loss std/mean across months, which params jumped wildly, which converged tightly
3. **Gain concentration audit**: top-3 feature cumulative gain%
4. **Suspicious patterns**: anything ML-suspicious the Critic might miss in their 8-check pass
5. **Next-iteration tuning recommendations** (3-5 items): specific changes, mechanisms, risks
6. **What this iteration confirms / refutes about prior LM Master advisory**: honest accounting of Phase 4.5 predictions vs actual outcomes
7. **Closing note for Critic**: flags evidence the Critic should look at (NOT directing the verdict)
```

**PROPOSED — add as new item 0 (FIRST)**:

```markdown
0. **Regime attribution table (MANDATORY NEW)**: tag IS months and OOS months into regime buckets (bull / chop / bear / vol-spike / liq-cascade / ETF-flow / other) using a canonical regime tagger (e.g., BTC 90-day return + 30-day realized vol quantiles). Compute per-regime Sharpe, trade count, max drawdown, weighted PnL for this iteration AND for BASELINE_V1. Emit:

| Regime | IS months | OOS months | This iter IS Sharpe | This iter OOS Sharpe | Baseline IS Sharpe | Baseline OOS Sharpe | Bundle role implication |
|---|---|---|---|---|---|---|---|
| bull | 14 | 3 | +2.10 | +1.45 | +1.20 | +0.80 | UNIVERSAL contributor |
| chop | 18 | 4 | +0.30 | -0.20 | +0.85 | +0.40 | Off-regime; do not select for chop bundle role |
| ... | ... | ... | ... | ... | ... | ... | ... |

The LM Master proposes the bundle role implication explicitly. The Critic Check 3c reads this table.
```

### Edit 8 — Add bundle-composition section to CONFIRMATION brief

**PROPOSED — add as new Section 11 in the brief schema (after Section 10 in Edit 5)**:

```markdown
## Section 11 — Bundle Composition (CONFIRMATION-only)

For CONFIRMATION iterations, declare:

- **Components included** (from prior EXPLORATIONs):
  - iter-v1/NNN-a: <regime role> — <one-sentence summary>
  - iter-v1/NNN-b: <regime role> — <one-sentence summary>
  - ...
- **Composition method**: stacking / ensembling / regime-conditional dispatch / weighted average / other (specify)
- **Regime coverage table**: list every tagged regime; which component(s) cover it; bundle-attributed Sharpe per regime
- **Bundle-level OOS/IS prediction**: explicit prediction of the composite OOS/IS ratio (this IS the gate for CONFIRMATION-MERGE)
- **Component substitution test**: for each component, predict what the bundle's OOS Sharpe would be WITHOUT that component (sensitivity check — if a component contributes < +0.05 to bundle OOS Sharpe, justify its inclusion or drop it)
```

### Edit 9 — Update Key Reminders

**CURRENT (lines 1322-1342)** — final summary section.

**PROPOSED — add at top of the reminders**:

```markdown
- **The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense.** Both IS and OOS undergo the SAME monthly train-predict cycle. The model retrains every month with embargo. IS/OOS is NOT a train/test bisection.
- **The bundle is the product.** Individual EXPLORATIONs identify regime specialists; CONFIRMATIONs assemble bundles. An IS-strong / OOS-modest model is a regime-specialist candidate, NOT an overfit reject — pending regime-attribution analysis.
- **Regime attribution is the load-bearing signal for component candidates.** OOS Sharpe Δ alone is insufficient. Within-regime Sharpe + regime coverage gap analysis are required.
- **OOS/IS ≥ 0.5 is a BUNDLE-level gate**, not a component-level gate. Component EXPLORATIONs are evaluated on regime-attributed within-regime metrics. Bundle CONFIRMATIONs are evaluated on composite OOS/IS.
```

---

## Closing Note

The v1 skill encodes substantial rigor — CPCV, DSR, PBO, PSR, ADF, IC, meta-labeling, embargo, axis rotation, multi-role separation. None of that rigor is wrong. The wrongness is *philosophical* — the skill treats the framework as a single-model train/test pipeline (the equities/López de Prado default) when it actually implements a walk-forward regime-ensemble pipeline.

The fix is **not to remove rigor — it is to redirect rigor to the correct level of analysis**. The methodology gates (no look-ahead, embargo, DSR/PSR/PBO) belong to *components AND bundles*. The generalization gates (`OOS/IS ≥ 0.5`, "overfit means IS-strong + OOS-weak") belong to *bundles only*. Components are evaluated on regime contribution.

Edit 1 alone (the rewritten "THE MOST IMPORTANT RULE" section) is the highest-leverage fix; Edits 3, 4, 5, 7 are the structural reframe; Edits 2, 6, 8, 9 are supporting.

After these edits, the skill encodes: "build regime specialists, combine them into a regime-balanced bundle, validate the bundle on OOS — and DO NOT reject a regime specialist for being weak in regimes it was never meant to capture."

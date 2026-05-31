# v1 Skill — Line-Level CURRENT → PROPOSED Diff

**Target file:** `/home/roberto/crypto-trade/.worktrees/quant-research/.claude/commands/quant-iteration-v1.md` (1343 lines, state at 2026-05-31)
**Companion:** `skill_v1_walkforward_reframe_proposal.md` (rationale)
**Apply order:** EDIT-1 first (highest leverage), then 2–10 in numbered order.

---

## EDIT-1 — Replace "THE MOST IMPORTANT RULE" section (lines 141–160)

### CURRENT (lines 141–160)

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

### PROPOSED

```markdown
## Walk-Forward Semantics — CRITICAL READ

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
training_months = 24             ← FIXED. NEVER CHANGES.
```

**This is a WALK-FORWARD framework — not a classical train/test split.**

Every calendar month, for every `(model, symbol)` cell, the system:
1. Trains a fresh LightGBM on the past `training_months = 24` months of klines + features
2. Predicts the upcoming month's signals
3. Trades them through the risk gates
4. Slides the window forward by one month and repeats

The walk-forward harness (`walk_forward.py:113`) carries the embargo: `train_end_ms = test_start_ms - embargo_ms`. The embargo is applied at EVERY month boundary — IS-internal AND OOS-internal. It is the structural defense against label-horizon leakage.

**Both IS (pre-2025-03-24) and OOS (post-2025-03-24) undergo the SAME monthly train-predict cycle.** OOS is NOT a held-out test set in the classical sense.

### What the IS/OOS split actually means

- **IS = the researcher's research data.** It is what the QR reads, analyzes, EDAs, designs against. It is NOT a single training set — each IS month's prediction comes from a model retrained on the prior 24 months. The walk-forward refits ~60+ times across IS.
- **OOS = the researcher-honesty window.** QR may NOT look at OOS during Phases 1–5. Purpose: prevent the QR from unconsciously tuning features/labels/params to fit recent patterns the QR has seen.
- **The walk-forward + embargo prevents MODEL leakage.** The IS/OOS boundary prevents RESEARCHER leakage. Two different defenses, two different failure modes.
- **Reports split at `OOS_CUTOFF_DATE`** into `in_sample/` and `out_of_sample/` for accounting clarity — the model crosses no wall there.
- **QR sees OOS results for the FIRST time in Phase 7.**

### The end goal — a regime-ensemble bundle

v1's mission is **NOT to build a single universal model.** It is to build a *bundle* of complementary models, each strong in different market regimes (bull, alt-rotation, chop, bear, vol-spike, liquidation-cascade, ETF-flow, etc.). The bundle's composite OOS — averaged across regime contributors — is what trades live.

Critical verdict implications:

- **An IS-strong / OOS-modest model is NOT inherently overfit.** IS spans ~5 years and ~6 regimes; OOS spans ~7 months and 1–2 regimes. A model that crushed bull-2020 + alt-2021 + chop-2023 (all IS) but only matched the recovery of 2025-Q2-Q3 (OOS) is a **regime specialist** — a bundle candidate.
- **`OOS/IS Sharpe ≥ 0.5` is a UNIVERSAL-MODEL / BUNDLE-level gate, NOT a component-EXPLORATION gate.** It is retained for full-bundle CONFIRMATIONs (where you ARE claiming a unified regime-free predictor). It is RELAXED for individual EXPLORATION component candidates — replaced by regime-attribution analysis (Phase 7.4 LM Master mandatory Regime Attribution Table; Phase 7.5 Critic Check 3c).

### The IS/OOS gap — what it tells you

| Pattern | Interpretation |
|---|---|
| IS strong + OOS strong, both regimes match | UNIVERSAL contributor (rare; anchor candidate) |
| IS strong + OOS weak, regime mix differs | REGIME-SPECIALIST-IS — bundle candidate if attribution shows clean within-regime edge |
| IS weak + OOS strong | REGIME-SPECIALIST-OOS — bundle candidate if OOS regime historically recurring |
| IS weak + OOS weak | TRUE-NEG — dead-paths catalog |
| Drawdown reduced without Sharpe lift | TAIL-CONTROL — evaluated on regime tail metrics, not Sharpe |
| Look-ahead bias detected (gap=0, embargo violated) | WALK-FORWARD-LEAKAGE — BLOCK; methodology integrity failure |

The IS-OOS gap is a *regime-mix signal*, not a generalization signal. To distinguish regime mismatch from true researcher overfit, run regime-attributed PnL analysis on both IS and OOS — if within-regime Sharpes match, it's regime mix; if within-regime Sharpes don't match, the QR may have snooped.

**The single most load-bearing sentence in this skill:**

> **The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense; the bundle is the product.**

These constants live in `src/crypto_trade/config.py`.
```

---

## EDIT-2 — Append regime-ensemble mission to Mission section (after line 22)

### CURRENT (line 22)

```markdown
v1 is now the **rigor + creator-role-augmented track**, parallel to v2 (diversification arm) and v3 (rigor-only arm). All three coexist.
```

### PROPOSED — append IMMEDIATELY AFTER line 22

```markdown

**The bundle is the product.** v1's mission is to build a *regime-ensemble bundle* — N complementary models where each is strong in some regime, and the composite is regime-balanced. Individual EXPLORATIONs are *component candidates* — a model that crushes bull regimes but flat-lines in chop is a bull specialist, not an overfit reject. CONFIRMATIONs are *bundle assemblies* — combining components (via stacking, ensembling, regime-conditional dispatch) and validating the composite OOS. Edge is measured at the bundle level; rigor is measured per-component (no look-ahead, embargo applied, etc.).

We do not predict the future. We identify moments when the distribution of forward returns is skewed in our favor, and we bet accordingly — sometimes with a bull specialist, sometimes with a chop specialist, sometimes with a tail-control gate. The bundle is regime-free; the components are not, by design.
```

---

## EDIT-3 — Split inherited merge gates by scope (lines 251–260)

### CURRENT (lines 251–260)

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

### PROPOSED

```markdown
Plus inherited project-level merge gates — applied DIFFERENTLY to **component EXPLORATIONs** vs **bundle CONFIRMATIONs**:

### Bundle-level (full-stack CONFIRMATION-MERGE gates)

The bundle as a whole must clear:

- Bundle IS monthly Sharpe > 1.0
- Bundle OOS monthly Sharpe > 1.0
- Bundle OOS / IS Sharpe ratio ≥ 0.5 (the bundle, NOT any single component)
- ≥10 trades/month OOS, ≥130 OOS total trades (bundle aggregate)
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable
- DSR > 0.95, PBO < 0.4, PSR > 0.95

### Component-level (EXPLORATION-PROMISING evaluation)

A component candidate is evaluated on:

- Within-regime Sharpe (NOT OOS/IS ratio) — at least one tagged regime with Sharpe > 1.0 and within-regime trade count ≥ 30
- Regime-attribution clarity — the component's PnL should concentrate in specific tagged regimes, not be scattered noise
- Bundle composition lift — adding this component to the current bundle (by stacking / dispatch simulation on IS) should improve at least one regime's bundle-attributed Sharpe by ≥ 0.10
- Methodology floors NOT relaxed: no look-ahead, embargo applied, gap correct, no OOS tuning

**A component can be `REGIME-SPECIALIST-IS` with OOS/IS < 0.5 IF regime attribution explains the gap.** The bundle CONFIRMATION enforces OOS/IS at the bundle level.

**Any METHODOLOGY-gate failure = NO-MERGE.** Regime mismatch is NOT a methodology failure; researcher overfit IS. Use the WALK-FORWARD-LEAKAGE verdict cell for actual leakage.
```

---

## EDIT-4 — Replace EXPLORATION verdict cells with 7-band regime-aware version (lines 808–820)

### CURRENT (lines 808–820)

```markdown
## Verdict Cells

All verdict cells used in v1. Established through iteration history; new cells added as methodology evolves.

### EXPLORATION verdict cells

| Verdict | OOS Sharpe Δ | Condition | Next step |
|---|---|---|---|
| `EXPLORATION-PROMISING` | ≥ +0.05 | Single-seed lift, no confound flagged | Log to catalog, candidate for CONFIRMATION bundle |
| `EXPLORATION-NEGATIVE` | < 0 OR < +0.05 | No signal | Log to catalog as dead-end; next EXPLORATION |
| `NEGATIVE-no-effect` | main Δ ≈ 0 (within ±0.10 of baseline) | Axis had no effect; saturated or under-powered | Log to catalog; try higher n_trials or different axis |
```

### PROPOSED

```markdown
## Regime-Aware Verdict Classification

All verdict cells used in v1. The classification recognizes that under walk-forward semantics, the IS-OOS Sharpe gap is **primarily a regime-mix signal**, not a generalization signal. A 7-band classifier replaces the legacy binary PROMISING/NEGATIVE.

### EXPLORATION verdict cells (REGIME-AWARE)

| Verdict | IS Sharpe Δ | OOS Sharpe Δ | Regime attribution | Bundle role | Next step |
|---|---|---|---|---|---|
| `UNIVERSAL` | ≥ +0.05 | ≥ +0.05 | broad across regimes | Anchor candidate | Promote to next CONFIRMATION |
| `REGIME-SPECIALIST-IS` | ≥ +0.10 | ≤ +0.05 (and ≥ −0.20) | concentrated in IS-only regimes | Bundle candidate for IS-only regimes | **PRESERVE for /044+ bundle** — log to catalog with regime tag |
| `REGIME-SPECIALIST-OOS` | ≤ +0.05 (and ≥ −0.20) | ≥ +0.10 | concentrated in OOS regimes | Bundle candidate (OOS-recurring regimes) | **PRESERVE for /044+ bundle** — log with regime tag |
| `TAIL-CONTROL` | any | any | reduces max_dd / OOS_min_month_pnl by ≥ 20% | Risk overlay | **PRESERVE for /044+ bundle** — evaluated on tail metrics, not Sharpe |
| `EXPLORATION-PROMISING` | ≥ +0.05 | ≥ +0.05 | lift present, not yet regime-attributed | TBD — pending attribution | Log to catalog; next EXP or CONFIRMATION inclusion |
| `TRUE-NEG` / `EXPLORATION-NEGATIVE` | ≤ 0 IS | ≤ 0 OOS | no regime gives lift; mechanism falsified | None | Dead-paths catalog |
| `NEGATIVE-no-effect` | within ±0.10 baseline | within ±0.10 | axis had no effect; saturated or under-powered | None | Catalog; try higher n_trials or pivot axis |
| `LEARNED-NEG` | mixed | OOS catastrophic | lost a regime QR expected to capture | None | Dead-paths + regime-tag the failure mechanism |
| `WALK-FORWARD-LEAKAGE` | n/a | n/a | actual leakage detected (gap=0, look-ahead, embargo violated) | None | **BLOCK** — methodology integrity failure |

**Regime attribution is the load-bearing signal**, not OOS Sharpe Δ alone. The regime-attribution table is a MANDATORY Phase 7.4 LM Master output. The Critic Check 3c reads this table.

**Distinguishing REGIME-SPECIALIST from OVERFIT:**

| Signature | Verdict |
|---|---|
| IS lift via importance-INERT basin lottery, OOS catastrophic, mechanism falsified at importance/wiring layer | OVERFIT-BY-MECHANISM-FAILURE — `TRUE-NEG` / `LEARNED-NEG` |
| IS lift mechanically attributable to a load-bearing feature, OOS weakness explained by regime mismatch | `REGIME-SPECIALIST-IS` — PRESERVE |

Note: iterations CAN and SHOULD produce different configurations from the baseline. Different trades vs baseline is EXPECTED. The comparison metric is regime-attributed component PnL vs the existing bundle's regime coverage — NOT OOS Sharpe vs BASELINE_V1 in isolation.
```

---

## EDIT-5 — Add CONFIRMATION portfolio-pathway verdict (lines 822–829)

### CURRENT (lines 822–829)

```markdown
### CONFIRMATION verdict cells

| Verdict | Condition | Next step |
|---|---|---|
| `CONFIRMATION-MERGE` | All gates PASS; DSR > 0.95; PBO < 0.4; PSR > 0.95; Sharpe floors met | Update BASELINE_V1.md; tag commit |
| `CONFIRMATION-BLOCK` | ≥1 gate fails; Critic verdict non-MERGE | No baseline update; iterate on failed gates |
| `BLOCK-PENDING-FIX` | One specific isolable defect; NOT multi-defect | QE one-shot fix + re-run; next verdict is PASS or BLOCK-FINAL |
| `BLOCK-FINAL` | Irrecoverable (multi-defect OR methodology issue OR second BLOCK after BLOCK-PENDING-FIX) | NO-MERGE; next iter fresh brief |
```

### PROPOSED

```markdown
### CONFIRMATION verdict cells

A CONFIRMATION can be EITHER a single-axis validation OR a **multi-component PORTFOLIO assembly**. The /044 substrate is now the canonical portfolio-CONFIRMATION pathway.

| Verdict | Condition | Next step |
|---|---|---|
| `CONFIRMATION-MERGE` (single-axis) | One axis validated multi-seed; all bundle-level gates PASS (DSR > 0.95; PBO < 0.4; PSR > 0.95; bundle Sharpe floors; bundle OOS/IS ≥ 0.5) | Update BASELINE_V1.md; tag commit |
| `CONFIRMATION-MERGE-PORTFOLIO` (multi-component) | N components combined; bundle-level gates PASS at composite; component substitution test PASS (every component contributes ≥ +0.05 bundle OOS Sharpe OR fills a unique regime); regime coverage table shows ≥3 distinct regimes covered | Update BASELINE_V1.md as new bundle stack; tag commit |
| `CONFIRMATION-BLOCK` | ≥1 BUNDLE-level gate fails; Critic verdict non-MERGE | No baseline update; iterate on failed gates |
| `BLOCK-PENDING-FIX` | One specific isolable defect; NOT multi-defect | QE one-shot fix + re-run; next verdict is PASS or BLOCK-FINAL |
| `BLOCK-FINAL` | Irrecoverable (multi-defect OR methodology issue OR second BLOCK after BLOCK-PENDING-FIX OR `WALK-FORWARD-LEAKAGE`) | NO-MERGE; next iter fresh brief |

### Portfolio Composition Rules (`CONFIRMATION-MERGE-PORTFOLIO` only)

1. **Weights:** components combined via stacking, regime-conditional dispatch, or weighted ensemble. Weights must be DETERMINISTIC (no in-sample tuning of weights on OOS).
2. **Regime coverage:** the bundle must cover ≥ 3 distinct tagged regimes. A component that duplicates another's regime coverage requires a Sharpe lift ≥ 0.30 over the substitute to remain in the bundle.
3. **Correlation diversification:** pairwise OOS daily-return correlation between components ≤ 0.70 (LOWER preferred). Cite per-pair correlations in brief Section 11.
4. **Component substitution test:** for every component, predict bundle OOS Sharpe WITHOUT that component. A component contributing < +0.05 bundle OOS Sharpe AND failing to fill a unique regime must be justified or dropped.
5. **At least one anchor:** the bundle must contain ≥ 1 component that, on its own, clears the standalone IS Sharpe > 1.0 + OOS Sharpe > 0.5 floor. Pure-specialist bundles (no anchor) are speculative and require an explicit user-directive exception.
6. **Bundle gates** (DSR, PBO, PSR, OOS/IS ≥ 0.5, ≥10 trades/month OOS, top-symbol ≤ 30%) all evaluated at the BUNDLE level — not per component.
```

---

## EDIT-6 — Add Section 10 (Regime Attribution Plan) to brief schema (after line 1133)

### CURRENT (lines 1128–1134, end of Section 9)

```markdown
## Section 9 — Library Stack Declaration
- mlfinlab: 1.4 (or mlfinpy <version> if fallback)
- pypbo: <version>
- fracdiff: <version>
- statsmodels: <version> (for ADF)
<note any fallback rationale>
```
```

### PROPOSED — insert IMMEDIATELY AFTER the Section 9 block (still inside the brief schema fence)

```markdown

## Section 10 — Regime Attribution Plan (NEW v1, regime-ensemble mandate)

- **Target regime(s):** which regime(s) this iteration is hypothesized to specialize in (bull / alt-rotation / chop / bear / vol-spike / liquidation-cascade / ETF-flow / other)
- **Why this regime:** 1–2 sentences of mechanism
- **Off-regime expectation:** what we expect this iter to do in OFF-target regimes (flat? small loss? don't know?)
- **Bundle role:** candidate for {anchor / bull-specialist / chop-specialist / bear-specialist / tail-control / universal}
- **Composition simulation:** if PROMISING in target regime, how would this component combine with the existing bundle? (stacking? regime-conditional dispatch? ensemble averaging?)
- **Falsifier (regime-aware):** "if target-regime IS Sharpe < X, hypothesis is rejected" — NOT "if OOS Sharpe < X" alone (OOS may not contain target regime)

## Section 11 — Bundle Composition (CONFIRMATION-only)

For CONFIRMATION iterations of TYPE = `CONFIRMATION-PORTFOLIO`, declare:

- **Components included** (from prior EXPLORATIONs):
  - iter-v1/NNN-a: <regime role> — <one-sentence summary>
  - iter-v1/NNN-b: <regime role> — <one-sentence summary>
- **Composition method:** stacking / ensembling / regime-conditional dispatch / weighted average / other (specify)
- **Regime coverage table:** every tagged regime; which component(s) cover it; bundle-attributed Sharpe per regime
- **Pairwise OOS correlation table:** all component pairs; reject bundle if any pair > 0.70
- **Component substitution test:** for each component, predict bundle OOS Sharpe WITHOUT that component
- **Bundle-level OOS/IS prediction:** explicit prediction of the composite OOS/IS ratio (this IS the bundle gate)
```

Also: update the section-count references — Phase 5.5 gate now verifies **13 mandatory sections** (0, 0.5, 0.6, 1, 2, 2.5, 3, 4, 5, 6, 7, 8, 9 + 10 + 11 if CONFIRMATION-PORTFOLIO).

---

## EDIT-7 — Split Critic Check 3 (line 1165)

### CURRENT (lines 1163–1172)

```markdown
- Check 1 (Look-Ahead): PASS
- Check 2 (Embargo): PASS
- Check 3 (DSR/PBO/PSR): PASS / FAIL
- Check 4 (IC): PASS / FAIL
- Check 5 (ADF): PASS / FAIL
- Check 6 (Pareto): PASS / WARN
- Check 7 (Reproducibility): PASS / FAIL
- Check 8 (Hypothesis-Implementation Alignment): PASS / FAIL
- Check 14 (Axis Family Validation): PASS / FAIL (v1-only)
- OVERALL: CONFIRMATION-MERGE | EXPLORATION-PROMISING | EXPLORATION-NEGATIVE | BLOCK-PENDING-FIX → final | BLOCK-FINAL
```

### PROPOSED

```markdown
- Check 1 (Look-Ahead): PASS / FAIL  (FAIL → WALK-FORWARD-LEAKAGE → BLOCK-FINAL)
- Check 2 (Embargo): PASS / FAIL  (FAIL → WALK-FORWARD-LEAKAGE → BLOCK-FINAL)
- Check 3a (DSR/PSR — methodology gate): PASS / FAIL  (CONFIRMATION-only; EXPLORATION skips)
- Check 3b (PBO — selection-bias gate): PASS / FAIL  (CONFIRMATION-only)
- Check 3c (Regime attribution clarity — component-candidate gate): PASS / WARN / FAIL  (EXPLORATION + CONFIRMATION)
- Check 3d (BUNDLE-level OOS/IS ≥ 0.5): PASS / FAIL  (BUNDLE-CONFIRMATION-only; component EXPLORATIONs EXEMPT)
- Check 4 (IC): PASS / FAIL
- Check 5 (ADF): PASS / FAIL
- Check 6 (Pareto): PASS / WARN
- Check 7 (Reproducibility): PASS / FAIL
- Check 8 (Hypothesis-Implementation Alignment): PASS / FAIL
- Check 14 (Axis Family Validation): PASS / FAIL (v1-only)
- OVERALL: UNIVERSAL | REGIME-SPECIALIST-IS | REGIME-SPECIALIST-OOS | TAIL-CONTROL | EXPLORATION-PROMISING | EXPLORATION-NEGATIVE / TRUE-NEG | LEARNED-NEG | NEGATIVE-no-effect | CONFIRMATION-MERGE | CONFIRMATION-MERGE-PORTFOLIO | BLOCK-PENDING-FIX → final | BLOCK-FINAL | WALK-FORWARD-LEAKAGE
```

---

## EDIT-8 — Add Phase 7.4 Regime Attribution Table mandate (lines 707–719)

### CURRENT (lines 707–719) — Phase 7.4 deliverable list

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

### PROPOSED — prepend item 0 (FIRST), renumber existing 1–7 to 1–7 (unchanged)

```markdown
Phase 7.4 section appended to `lgbm_advisor.md`. ~600-1200 words covering:

0. **Regime Attribution Table (MANDATORY — NEW 2026-05-31)**: tag IS months and OOS months into regime buckets (bull / alt-rotation / chop / bear / vol-spike / liq-cascade / ETF-flow / other) using a canonical regime tagger (BTC 90-day return + 30-day realized vol quantiles, OR an explicitly documented alternative). For BOTH this iteration AND BASELINE_V1, compute per-regime Sharpe, trade count, max drawdown, weighted PnL. Emit a markdown table:

   | Regime | IS months | OOS months | This iter IS Sharpe | This iter OOS Sharpe | Baseline IS Sharpe | Baseline OOS Sharpe | Bundle role implication |
   |---|---|---|---|---|---|---|---|
   | bull | 14 | 3 | +2.10 | +1.45 | +1.20 | +0.80 | UNIVERSAL contributor |
   | chop | 18 | 4 | +0.30 | −0.20 | +0.85 | +0.40 | Off-regime; do not select for chop bundle role |
   | ... | ... | ... | ... | ... | ... | ... | ... |

   LM Master proposes the bundle-role implication explicitly for each regime row. The Critic Check 3c reads this table.

1. **Feature importance triage**: top performers, dead weight (rank 14/14 candidates), unstable features
2. **Hyperparameter trial stability**: best-trial loss std/mean across months, which params jumped wildly, which converged tightly
3. **Gain concentration audit**: top-3 feature cumulative gain%
4. **Suspicious patterns**: anything ML-suspicious the Critic might miss in their 8-check pass
5. **Next-iteration tuning recommendations** (3-5 items): specific changes, mechanisms, risks
6. **What this iteration confirms / refutes about prior LM Master advisory**: honest accounting of Phase 4.5 predictions vs actual outcomes
7. **Closing note for Critic**: flags evidence the Critic should look at (NOT directing the verdict)
```

---

## EDIT-9 — Phase 5.5 gate adds Section 10 + falsifier-regime-aware check

### CURRENT (lines 583–598) — gate per-section block

(Existing 11-section list.)

### PROPOSED — add THREE lines

```markdown
- Section 10 (Regime Attribution Plan): PASS / MISSING / INVALID
- (CONFIRMATION-PORTFOLIO only) Section 11 (Bundle Composition): PASS / MISSING / INVALID
- Section 4 falsifier is REGIME-AWARE (cites target-regime IS Sharpe, not OOS-only): PASS / FAIL
```

---

## EDIT-10 — Closeout language replacements + key reminders (lines 1322–1342)

### CURRENT (lines 1322–1342) — Key Reminders list

(Existing reminders unchanged.)

### PROPOSED — PREPEND the following 5 reminders at the top of the list (before line 1324)

```markdown
- **The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense; the bundle is the product.** Both IS and OOS undergo the SAME monthly train-predict cycle with embargo. IS/OOS is NOT a classical train/test bisection.
- **The bundle is the product.** Individual EXPLORATIONs identify regime specialists; CONFIRMATIONs assemble bundles. An IS-strong / OOS-modest model is a `REGIME-SPECIALIST-IS` candidate, NOT an "overfit reject" — pending regime-attribution analysis.
- **Replace "OVERFIT" with "IS-REGIME-SPECIALIST candidate"** in every Phase 7.5 closeout where: (a) IS Δ ≥ +0.10, (b) OOS Δ ∈ [−0.20, +0.05], (c) regime attribution shows clean within-regime edge, (d) mechanism is NOT importance-INERT (load-bearing feature/risk-primitive). True overfit (importance-INERT basin lottery + OOS catastrophic + mechanism falsified) remains `LEARNED-NEG`.
- **Regime attribution is the load-bearing signal for component candidates.** OOS Sharpe Δ alone is insufficient. Within-regime Sharpe + regime coverage gap analysis are required, produced by LM Master Phase 7.4 Regime Attribution Table.
- **`OOS/IS ≥ 0.5` is a BUNDLE-level gate**, NOT a component-EXPLORATION gate. Component EXPLORATIONs use regime-attributed within-regime metrics. Bundle CONFIRMATIONs use composite OOS/IS.
```

---

## Sentinel — verify after applying

Run `grep -nE "OOS_Sharpe / IS_Sharpe ≥ 0.5" /home/roberto/crypto-trade/.worktrees/quant-research/.claude/commands/quant-iteration-v1.md` after applying — every remaining match MUST be inside a bundle-level context (Edit-3 "Bundle-level" block or Edit-7 "Check 3d BUNDLE-CONFIRMATION-only"). Any match in a component-EXPLORATION context is a missed edit.

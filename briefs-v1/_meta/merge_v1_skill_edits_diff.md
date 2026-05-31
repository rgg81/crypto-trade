# v1 Skill Edits — Relative-Regime-Pareto Framework

**Date:** 2026-05-31
**Target file:** `.claude/commands/quant-iteration-v1.md`
**Source proposal:** `briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md`
**Source audit:** `briefs-v1/_meta/merge_criteria_audit.md`
**Status:** Ready for direct Edit-tool application.

Each edit below quotes the verbatim CURRENT text and the verbatim PROPOSED replacement. Edits are independent and may be applied in any order (no overlapping anchors).

---

## EDIT-1 — Bundle-level CONFIRMATION-MERGE gates → per-regime Pareto-dominance

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 291–301 (approximately)

**CURRENT** (verbatim):

```
### Bundle-level (full-stack CONFIRMATION-MERGE gates)

The bundle as a whole must clear:

- Bundle IS monthly Sharpe > 1.0
- Bundle OOS monthly Sharpe > 1.0
- Bundle OOS / IS Sharpe ratio ≥ 0.5 (the bundle, NOT any single component)
- ≥10 trades/month OOS, ≥130 OOS total trades (bundle aggregate)
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable
- DSR > 0.95, PBO < 0.4, PSR > 0.95
```

**PROPOSED**:

```
### Bundle-level (full-stack CONFIRMATION-MERGE criteria — RELATIVE REGIME PARETO)

The bundle as a whole must clear, by reference to the current BASELINE_V1 anchor:

- **Per-regime Pareto-better-or-equal** vs baseline on every tagged regime R present
  in IS or OOS: `sharpe_R(candidate) ≥ sharpe_R(baseline) − σ_R` AND
  `max_dd_R(candidate) ≤ max_dd_R(baseline) + σ_dd_R` AND
  `trade_count_R(candidate) ≥ 0.5 × trade_count_R(baseline)` (rare-regime carve-out
  per §B.5 of `briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md`).
- **At least one regime STRICTLY better** (`sharpe_R > baseline_sharpe_R + σ_R` OR
  `max_dd_R < baseline_max_dd_R − σ_dd_R`).
- **Methodology integrity intact** (no look-ahead, embargo applied, gap correct,
  no OOS tuning, reproducibility checksum match) — see Section "Methodology Gates
  (HARD; PRESERVED)" below.
- **10-seed validation: per-regime mean Sharpe_R(candidate) ≥ per-regime mean
  Sharpe_R(baseline)** AND seed-distribution dominance ratio ≥ 0.5 (at least 5
  of 10 candidate-seed within-regime Sharpes beat the baseline's median seed
  within-regime Sharpe).

`σ_R` and `σ_dd_R` are baseline-seed-noise tolerances (one σ across the
baseline's 10-seed within-regime Sharpe / max_dd distribution) — computed once
at baseline commit and stored in `briefs-v1/_meta/baseline_seed_regime_matrix.csv`.
NO absolute Sharpe / DSR / PBO / PSR floors at the bundle level. DSR / PBO / PSR
are reported per-regime and bundle-level as INFORMATIONAL (see "Statistical-
Significance Metrics" section below).
```

**Rationale:** This is the central refactor — replaces every absolute floor with a Pareto-better-or-equal-per-regime predicate scaled to the baseline's own seed noise. Implements proposal §A + §B + §F.

---

## EDIT-2 — Component-level EXPLORATION-PROMISING evaluation → baseline-relative

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 303–310 (approximately)

**CURRENT** (verbatim):

```
### Component-level (EXPLORATION-PROMISING evaluation)

A component candidate is evaluated on:

- Within-regime Sharpe (NOT OOS/IS ratio) — at least one tagged regime with Sharpe > 1.0 and within-regime trade count ≥ 30
- Regime-attribution clarity — the component's PnL should concentrate in specific tagged regimes, not be scattered noise
- Bundle composition lift — adding this component to the current bundle (by stacking / dispatch simulation on IS) should improve at least one regime's bundle-attributed Sharpe by ≥ 0.10
- Methodology floors NOT relaxed: no look-ahead, embargo applied, gap correct, no OOS tuning
```

**PROPOSED**:

```
### Component-level (EXPLORATION-PROMISING evaluation — BASELINE-RELATIVE)

A component candidate is evaluated by reference to the current BASELINE_V1 anchor:

- **Within-regime Sharpe Δ vs baseline** — at least one tagged regime where
  `sharpe_R(candidate) > sharpe_R(baseline) + σ_R` (materially positive vs
  baseline's own seed noise on that regime).
- **No regime regression > 1σ_R** — on every other tagged regime,
  `sharpe_R(candidate) ≥ sharpe_R(baseline) − σ_R`. A regime that materially
  REGRESSES makes the candidate a TRADED-EDGE candidate, not a clean PROMISING.
- **Regime-attribution clarity** — the component's PnL concentrates in specific
  tagged regimes; not scattered noise. LM Master Phase 7.4 Regime Attribution
  Table is the artifact.
- **Bundle composition lift (qualitative)** — adding the component to the current
  bundle (by stacking / dispatch simulation on IS) should improve at least one
  regime's bundle-attributed Sharpe materially (≥ 1σ_R on that regime).
- **Methodology floors NOT relaxed** — no look-ahead, embargo applied, gap correct,
  no OOS tuning. These remain HARD per §C of the proposal.
```

**Rationale:** Replaces `Sharpe > 1.0`, `trade ≥ 30`, `lift ≥ 0.10` (absolute) with σ-multiples-vs-baseline (relative). Keeps the qualitative attribution clarity bullet.

---

## EDIT-3 — Portfolio Composition Rules → relax correlation + regime-coverage hard numbers

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 916–924 (approximately)

**CURRENT** (verbatim):

```
### Portfolio Composition Rules (`CONFIRMATION-MERGE-PORTFOLIO` only)

1. **Weights:** components combined via stacking, regime-conditional dispatch, or weighted ensemble. Weights must be DETERMINISTIC (no in-sample tuning of weights on OOS).
2. **Regime coverage:** the bundle must cover ≥ 3 distinct tagged regimes. A component that duplicates another's regime coverage requires a Sharpe lift ≥ 0.30 over the substitute to remain in the bundle.
3. **Correlation diversification:** pairwise OOS daily-return correlation between components ≤ 0.70 (LOWER preferred). Cite per-pair correlations in brief Section 11.
4. **Component substitution test:** for every component, predict bundle OOS Sharpe WITHOUT that component. A component contributing < +0.05 bundle OOS Sharpe AND failing to fill a unique regime must be justified or dropped.
5. **At least one anchor:** the bundle must contain ≥ 1 component that, on its own, clears the standalone IS Sharpe > 1.0 + OOS Sharpe > 0.5 floor. Pure-specialist bundles (no anchor) are speculative and require an explicit user-directive exception.
6. **Bundle gates** (DSR, PBO, PSR, OOS/IS ≥ 0.5, ≥10 trades/month OOS, top-symbol ≤ 30%) all evaluated at the BUNDLE level — not per component.
```

**PROPOSED**:

```
### Portfolio Composition Rules (`CONFIRMATION-MERGE-PORTFOLIO` only)

1. **Weights:** components combined via stacking, regime-conditional dispatch, or
   weighted ensemble. Weights must be DETERMINISTIC (no in-sample tuning of
   weights on OOS). UNCHANGED.
2. **Regime coverage:** the bundle must cover EVERY tagged regime that the
   current BASELINE_V1 covers, Pareto-better-or-equal per §B of the proposal.
   No absolute "≥ 3 regimes" floor. A component that duplicates another's
   regime coverage stays in the bundle if it contributes a materially positive
   within-regime lift (≥ 1σ_R) on its target regime; otherwise dropped at the
   substitution test.
3. **Correlation diversification:** LOWER pairwise OOS daily-return correlation
   between components is PREFERRED but NOT BLOCKING. Cite per-pair correlations
   in brief Section 11; if any pair > 0.70, the diary must include a one-paragraph
   "correlation justification" explaining why the duplicate-axis exposure is
   acceptable (e.g., one component is regime-specialist, the other anchor). NO
   AUTO-BLOCK on correlation.
4. **Component substitution test:** for every component, predict bundle within-
   regime metrics WITHOUT that component. A component that fails to Pareto-
   improve the bundle on at least one tagged regime (vs baseline) AND fails to
   fill a regime the bundle would otherwise lose (vs baseline coverage) must be
   justified or dropped.
5. **At least one anchor:** the bundle must contain ≥ 1 component that, on its
   own, performs Pareto-better-or-equal to the BASELINE_V1 anchor on the regime
   the baseline covers best. Pure-specialist bundles (no anchor) require an
   explicit user-directive exception. NO absolute IS Sharpe > 1.0 / OOS Sharpe
   > 0.5 floor.
6. **Bundle MERGE evaluation** lives in the "Bundle-level (full-stack
   CONFIRMATION-MERGE criteria — RELATIVE REGIME PARETO)" section above. DSR /
   PBO / PSR / OOS/IS ratio / trade-count / concentration are reported but
   INFORMATIONAL; per-regime Pareto-dominance is the gate.
```

**Rationale:** Replaces every absolute number (3 regimes, 0.30 lift, 0.70 correlation, 0.05 lift, 1.0 / 0.5 floors) with baseline-Pareto or qualitative criteria. Implements proposal §H rows H6, H7.

---

## EDIT-4 — Sacred Constants thresholds → annotate as INFORMATIONAL anchors

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 279–287 (approximately)

**CURRENT** (verbatim):

```
Plus the v1 hard thresholds (mirroring v3):

```
DSR_threshold = 0.95     # Deflated Sharpe Ratio
PBO_threshold = 0.40     # Probability of Backtest Overfitting (LOWER is better)
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families (LOWER is better)
ADF_threshold = 0.05     # ADF p-value (LOWER is better — rejects unit root)
```
```

**PROPOSED**:

```
Plus the v1 statistical-significance INFORMATIONAL anchors (relative-Pareto framework — 2026-05-31):

```
# INFORMATIONAL ONLY for component EXPLORATIONs.
# ADVISORY (diary-flagging) for bundle CONFIRMATIONs.
# NOT hard MERGE gates under the Relative-Regime-Pareto framework.
DSR_baseline_anchor = <read from briefs-v1/_meta/baseline_metric_anchors.csv>
PBO_baseline_anchor = <read from briefs-v1/_meta/baseline_metric_anchors.csv>
PSR_baseline_anchor = <read from briefs-v1/_meta/baseline_metric_anchors.csv>
IC_threshold  = 0.70     # |IC_pearson| feature-family redundancy heuristic — advisory
ADF_threshold = 0.05     # ADF stationarity heuristic — advisory
```

**The MERGE gate is per-regime Pareto-dominance vs the current baseline**
(§B of `briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md`).
DSR / PBO / PSR are reported per-regime AND bundle-level; the diary calls out
any material regression vs the baseline anchor (`DSR < baseline_DSR`,
`PBO > baseline_PBO + 0.10`, `PSR < baseline_PSR`) but these do NOT auto-block.
Methodology integrity gates remain HARD — see "Methodology Gates (HARD;
PRESERVED)" section.
```

**Rationale:** Demotes the absolute DSR/PBO/PSR thresholds to baseline-relative reporting anchors. Codifies proposal §D INFORMATIONAL role. Implements H1 + H4.

---

## EDIT-5 — Verdict cells — CONFIRMATION-MERGE conditions

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 908–911 (approximately)

**CURRENT** (verbatim):

```
| Verdict | Condition | Next step |
|---|---|---|
| `CONFIRMATION-MERGE` (single-axis) | One axis validated multi-seed; all bundle-level gates PASS (DSR > 0.95; PBO < 0.4; PSR > 0.95; bundle Sharpe floors; bundle OOS/IS ≥ 0.5) | Update BASELINE_V1.md; tag commit |
| `CONFIRMATION-MERGE-PORTFOLIO` (multi-component) | N components combined; bundle-level gates PASS at composite; component substitution test PASS (every component contributes ≥ +0.05 bundle OOS Sharpe OR fills a unique regime); regime coverage table shows ≥3 distinct regimes covered | Update BASELINE_V1.md as new bundle stack; tag commit |
```

**PROPOSED**:

```
| Verdict | Condition | Next step |
|---|---|---|
| `CONFIRMATION-MERGE` (single-axis) | One axis validated multi-seed; bundle is Pareto-better-or-equal to current baseline on every tagged regime AND strictly better on ≥1 regime; methodology integrity intact (no look-ahead, embargo, gap, reproducibility) | Update BASELINE_V1.md; tag commit |
| `CONFIRMATION-MERGE-PORTFOLIO` (multi-component) | N components combined; the COMPOSITE bundle is Pareto-better-or-equal to current baseline on every tagged regime AND strictly better on ≥1 regime; component substitution test PASS (every component is justified by regime-specialist role OR Pareto-positive marginal within-regime contribution); methodology integrity intact | Update BASELINE_V1.md as new bundle stack; tag commit |
```

**Rationale:** Replaces inlined absolute thresholds in verdict cells with per-regime Pareto-dominance conditions. Implements H5 + H6.

---

## EDIT-6 — Phase 5.5 Brief Section 8 → Pre-Registered Baseline-Comparison Criteria

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 589–590 (skill description) AND lines 1220–1221 (brief schema)

### Edit 6a — Skill description (line 590)

**CURRENT** (verbatim):

```
- **Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria.** Locked numerical thresholds before backtest. Example: "MERGE iff `OOS_monthly_Sharpe ≥ +1.8` AND `PBO < 0.4` AND `PSR > 0.95` AND no symbol > 35% of OOS wpnl".
```

**PROPOSED**:

```
- **Section 8 — Pre-Registered Per-Regime Baseline-Comparison Criteria.** Locked per-regime comparison plan vs current BASELINE_V1, BEFORE backtest. Format: "MERGE iff for every tagged regime R, `sharpe_R(candidate) ≥ sharpe_R(baseline) − σ_R` AND `max_dd_R(candidate) ≤ max_dd_R(baseline) + σ_dd_R`; AND on at least one regime R*, `sharpe_R*(candidate) > sharpe_R*(baseline) + σ_R*`." Diary auto-populates the per-regime comparison table from `regime_attribution.csv`. NO absolute Sharpe / DSR / PBO / PSR floors.
```

### Edit 6b — Brief schema (lines 1220–1221)

**CURRENT** (verbatim):

```
## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria
<locked numerical thresholds before backtest. Example: "MERGE iff OOS_monthly_Sharpe ≥ +1.8 AND PBO < 0.4 AND PSR > 0.95 AND no symbol > 35% of OOS wpnl">
```

**PROPOSED**:

```
## Section 8 — Pre-Registered Per-Regime Baseline-Comparison Criteria
<locked per-regime comparison plan vs current BASELINE_V1, BEFORE backtest.>

- **Regimes to evaluate** (from briefs-v1/_meta/regime_catalog.md): bull, alt-rotation, chop, bear, vol-spike, liquidation-cascade, ETF-flow, recovery (or subset present in IS/OOS).
- **Per-regime Pareto criteria** (read baseline numbers from briefs-v1/_meta/baseline_seed_regime_matrix.csv):
  - For every regime R present: `sharpe_R(candidate) ≥ sharpe_R(baseline) − σ_R` AND `max_dd_R(candidate) ≤ max_dd_R(baseline) + σ_dd_R` AND `trade_count_R(candidate) ≥ 0.5 × trade_count_R(baseline)`.
  - On at least one regime R*: `sharpe_R*(candidate) > sharpe_R*(baseline) + σ_R*` OR `max_dd_R*(candidate) < max_dd_R*(baseline) − σ_dd_R*`.
- **DSR / PBO / PSR**: reported per-regime + bundle-level; flagged in diary if materially regressed vs baseline anchor, but NOT a MERGE gate.
- **Methodology integrity gates** (HARD, BLOCKING): no look-ahead, embargo applied, gap correct, reproducibility checksum match.
```

**Rationale:** Reframes Section 8 from absolute-thresholds pre-registration to per-regime comparison-plan pre-registration. Implements H9 fully.

---

## EDIT-7 — Critic Check 3d wording → per-regime baseline comparison

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** line 1284 (in Phase 8 diary template)

**CURRENT** (verbatim):

```
- Check 3d (BUNDLE-level OOS/IS ≥ 0.5): PASS / FAIL  (BUNDLE-CONFIRMATION-only; component EXPLORATIONs EXEMPT)
```

**PROPOSED**:

```
- Check 3d (BUNDLE-level per-regime Pareto-dominance vs BASELINE_V1: candidate ≥ baseline within σ on EVERY tagged regime AND strictly better on ≥1 regime): PASS / FAIL  (BUNDLE-CONFIRMATION-only; component EXPLORATIONs EXEMPT — they use within-regime Δ vs baseline per Check 3c)
```

**Rationale:** Replaces the `OOS/IS ≥ 0.5` absolute gate (an aggregate metric that hides regime-mix effects) with the per-regime Pareto-dominance check. Implements H10.

---

## EDIT-8 — Mandatory Statistical-Significance Reporting → per-regime + bundle, informational

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** lines 952–958 (approximately)

**CURRENT** (verbatim):

```
### Hard Thresholds

- **DSR > 0.95** — required for MERGE
- **PBO < 0.4** — required for MERGE (LOWER is better)
- **PSR > 0.95** — required for MERGE

**Any single threshold failure = automatic NO-MERGE.** Critic enforces this in Check 3.
```

**PROPOSED**:

```
### Reported Statistical-Significance Metrics (INFORMATIONAL, NOT gating)

- **DSR (Deflated Sharpe Ratio)** — reported per-regime AND bundle-level. The
  diary records `DSR(candidate)` vs `DSR(baseline)`. If `DSR(candidate) <
  DSR(baseline)` on bundle OR on any tagged regime, the diary includes a
  "DSR-regression justification" paragraph. NOT a MERGE gate.
- **PBO (Probability of Backtest Overfitting)** — reported bundle-level. Diary
  flags any `PBO(candidate) > PBO(baseline) + 0.10`. NOT a MERGE gate.
- **PSR (Probabilistic Sharpe Ratio)** — reported per-regime. Diary acknowledges
  `PSR(candidate) < PSR(baseline)` on any regime. NOT a MERGE gate.

**The MERGE gate is per-regime Pareto-dominance vs baseline** (Critic Check 3d).
DSR / PBO / PSR are decision-support, not pass/fail predicates. A candidate that
ties baseline on every regime but has slightly worse DSR is an Optuna-trajectory
noise artifact, NOT an edge regression — the relative-Pareto framework treats
it accordingly.

**Methodology-integrity gates remain HARD and BLOCKING** (no look-ahead, embargo
applied, gap correct, reproducibility checksum match — see "Methodology Gates
(HARD; PRESERVED)" section). These are the only absolute gates.
```

**Rationale:** Demotes DSR/PBO/PSR to informational reporting and explicitly states methodology integrity remains the only HARD gate. Implements H4 fully.

---

## EDIT-9 — Add new section "Merge Principle — Relative Regime Pareto-Dominance" after Walk-Forward Semantics

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** Insert after line 199 (end of Walk-Forward Semantics section, before "## Four Roles") — i.e., after the line `These constants live in `src/crypto_trade/config.py`.`

**CURRENT** (verbatim — anchor for insertion):

```
These constants live in `src/crypto_trade/config.py`.

---

## Four Roles
```

**PROPOSED** (insert new section between these two anchors):

```
These constants live in `src/crypto_trade/config.py`.

---

## Merge Principle — Relative Regime Pareto-Dominance (2026-05-31)

**MERGE-PRINCIPLE (canonical, one sentence):**

> A candidate bundle becomes the new BASELINE_V1 if and only if, under every
> tagged regime, the candidate is Pareto-better-or-equal to the current baseline
> on the bundle metric vector (within one baseline-seed-σ tolerance), AND strictly
> better in at least one regime, AND methodology integrity is intact.

Three load-bearing words:

- **Pareto.** No regime is allowed to regress materially (> 1σ_R below baseline).
  Cross-regime trade-offs ("we lost chop, but gained bull") are NOT acceptable.
  The candidate must DOMINATE the baseline on the per-regime surface — not
  re-shuffle edge.
- **Regime.** Comparison is always within-regime (bull / alt-rotation / chop /
  bear / vol-spike / liquidation-cascade / ETF-flow / recovery / …). Aggregated
  OOS-Sharpe-vs-OOS-Sharpe hides regime-mix effects when IS regime mix differs
  from OOS regime mix.
- **Relative.** No absolute Sharpe / DSR / PBO / PSR floors. Every edge metric is
  compared against the corresponding metric on the current baseline, with
  tolerance scaled to the baseline's own seed-to-seed noise on that regime.
  Numbers remain only where they enforce methodology integrity.

Three corollaries:

1. **The bundle is the product.** Components are evaluated as bundle contributors;
   MERGE evaluation lives at the bundle level.
2. **OOS is one regime realization, not a generalization oracle.** A candidate
   that ties baseline on every IS-tagged regime AND ties baseline on the OOS-
   tagged regime is a MERGE candidate even if headline OOS Sharpe is unchanged.
3. **Statistical-significance metrics inform; they do not gate.** DSR / PBO /
   PSR are reported per-regime AND bundle-level. They do NOT auto-trigger BLOCK.

Methodology-integrity gates (look-ahead, embargo, gap, reproducibility, OOS-tuning,
feature-column-pinning, forming-candle-drop, survivorship handling) remain HARD
and BLOCKING. The "no specific numbers" directive applies to EDGE metrics, NOT
INTEGRITY metrics. Full enumeration in §C of
`briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md`.

Operational artifacts (one-time + per-iteration):
- `briefs-v1/_meta/baseline_metric_anchors.csv` — bundle-level DSR/PBO/PSR/Sharpe/MaxDD for current BASELINE_V1.
- `briefs-v1/_meta/baseline_seed_regime_matrix.csv` — per-regime per-seed Sharpe / max_dd / trade_count for the current baseline (10 seeds × N regimes). Used to compute σ_R and σ_dd_R tolerance bands.
- `briefs-v1/_meta/regime_catalog.md` — canonical regime tag definitions.
- `reports-v1/iteration_v1-NNN/regime_attribution.csv` — per-iteration deliverable; schema: `regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`.

Each MERGE updates the baseline anchor files; the next candidate must clear the
new bar. By design (Pareto monotonicity): the framework has no upper edge
ceiling.

---

## Four Roles
```

**Rationale:** Adds the canonical statement of the new principle near the top of the skill (after Walk-Forward Semantics) so every reader sees it before encountering the verdict mechanics. Implements proposal §A.

---

## EDIT-10 — Key Reminders → add Pareto principle, remove auto-block on PBO/DSR/PSR

**File:** `.claude/commands/quant-iteration-v1.md`
**Location:** line 1454 (in Key Reminders list)

**CURRENT** (verbatim):

```
- PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.
```

**PROPOSED**:

```
- **MERGE Principle: per-regime Pareto-dominance vs current BASELINE_V1.** Candidate must Pareto-better-or-equal baseline on EVERY tagged regime (within σ_R tolerance) AND strictly better on ≥1 regime. No absolute Sharpe / DSR / PBO / PSR floors — these are reported INFORMATIONAL per-regime and bundle-level, diary-flagged on material regression, but NOT auto-blocking. Methodology-integrity gates (look-ahead, embargo, gap, reproducibility) remain HARD. See "Merge Principle — Relative Regime Pareto-Dominance" section.
```

**Rationale:** Updates the most-easily-scanned summary line to reflect the new principle and explicitly retracts the auto-block on DSR/PBO/PSR. Implements H12 + reinforces the new principle from EDIT-9.

---

## Application Order

The 10 edits are independent. Recommended order (least-to-most disruptive for reviewer scanning):

1. EDIT-9 (insert new section) — establishes the principle anchor.
2. EDIT-4 (Sacred Constants annotation) — informational anchors at the top.
3. EDIT-1 (Bundle-level gates) — the core relative-Pareto refactor.
4. EDIT-2 (Component-level gates) — relative-Pareto at component layer.
5. EDIT-3 (Portfolio Composition Rules) — softens rules 2/3/4/5.
6. EDIT-5 (Verdict cells) — propagates to verdict table.
7. EDIT-8 (Statistical-Significance Reporting) — demotes to informational.
8. EDIT-6 (Phase 5.5 Brief Section 8) — pre-registration template change.
9. EDIT-7 (Critic Check 3d) — diary template line.
10. EDIT-10 (Key Reminders) — summary line update.

After all 10 edits, the skill is internally consistent with the Relative-Regime-Pareto framework. The companion artifacts (`baseline_metric_anchors.csv`, `baseline_seed_regime_matrix.csv`, `regime_catalog.md`) must exist before the first iteration runs under the new framework — listed as prerequisites in EDIT-9.

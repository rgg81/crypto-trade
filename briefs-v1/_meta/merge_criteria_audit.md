# Merge Criteria Audit — v1 Skill (`quant-iteration-v1.md`)

**Date:** 2026-05-31
**User directive:** "I want to review to be more flexible, and to always compare with the current baseline. A new baseline is taken if the bundle model performs better under all regimes. We don't need specific numbers."
**Scope:** identify every place in `.claude/commands/quant-iteration-v1.md` where a HARD numerical threshold is used as a merge gate, vs places that already do relative-to-baseline comparison.

---

## 1. HARD-NUMBER gates to RELAX

### H1. Sacred Constants — hard numerical thresholds block (Lines 279–287)

**Text verbatim:**
```
DSR_threshold = 0.95     # Deflated Sharpe Ratio
PBO_threshold = 0.40     # Probability of Backtest Overfitting (LOWER is better)
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families (LOWER is better)
ADF_threshold = 0.05     # ADF p-value (LOWER is better — rejects unit root)
```

**Why hard-number:** Codified as global module-level constants intended for direct gate comparison without reference to the baseline's own DSR/PBO/PSR/IC/ADF measurements. The new directive would replace this with "DSR/PBO/PSR/IC/ADF must be no worse than baseline by more than X%" or just "DSR must compare favorably to baseline DSR".

---

### H2. Bundle-level CONFIRMATION-MERGE gates (Lines 291–301)

**Text verbatim:**
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

**Why hard-number:** Every gate is an absolute threshold (`>1.0`, `≥0.5`, `≥130`, `≤30%`, etc.). No reference to the BASELINE_V1 anchor's own measurements. Under the new directive, the gate should read "bundle metrics no worse than baseline metrics on each regime" — not absolute Sharpe floors. The 1.0 Sharpe floor in particular is inherited from project memory (`feedback_sharpe_floor.md`) but the directive explicitly relaxes "specific numbers".

---

### H3. Component-level EXPLORATION-PROMISING gates (Lines 303–310)

**Text verbatim:**
```
### Component-level (EXPLORATION-PROMISING evaluation)

A component candidate is evaluated on:

- Within-regime Sharpe (NOT OOS/IS ratio) — at least one tagged regime with Sharpe > 1.0 and within-regime trade count ≥ 30
- Regime-attribution clarity — the component's PnL should concentrate in specific tagged regimes, not be scattered noise
- Bundle composition lift — adding this component to the current bundle (by stacking / dispatch simulation on IS) should improve at least one regime's bundle-attributed Sharpe by ≥ 0.10
- Methodology floors NOT relaxed: no look-ahead, embargo applied, gap correct, no OOS tuning
```

**Why hard-number:** `Sharpe > 1.0`, `trade count ≥ 30`, `≥ 0.10` Sharpe lift — all absolute thresholds. The directive wants "comparison with current baseline" — the right form is "within-regime Sharpe ≥ baseline's within-regime Sharpe (on that regime)" and "bundle lift ≥ 0 vs baseline bundle on at least one regime".

---

### H4. Mandatory Statistical-Significance Reporting — Hard Thresholds block (Lines 952–958)

**Text verbatim:**
```
### Hard Thresholds

- **DSR > 0.95** — required for MERGE
- **PBO < 0.4** — required for MERGE (LOWER is better)
- **PSR > 0.95** — required for MERGE

**Any single threshold failure = automatic NO-MERGE.** Critic enforces this in Check 3.
```

**Why hard-number:** Section is literally titled "Hard Thresholds" with absolute pass/fail gates and "automatic NO-MERGE" enforcement. Critic Check 3 wires these directly into the verdict. Under the new directive, these become "DSR/PBO/PSR no worse than baseline by more than X%" or "Critic notes if DSR/PBO/PSR diverge materially from baseline; not an auto-block".

---

### H5. CONFIRMATION verdict table — CONFIRMATION-MERGE (single-axis) row (Lines 908–910)

**Text verbatim:**
```
| `CONFIRMATION-MERGE` (single-axis) | One axis validated multi-seed; all bundle-level gates PASS (DSR > 0.95; PBO < 0.4; PSR > 0.95; bundle Sharpe floors; bundle OOS/IS ≥ 0.5) | Update BASELINE_V1.md; tag commit |
```

**Why hard-number:** Verdict cell directly inlines `DSR > 0.95; PBO < 0.4; PSR > 0.95; bundle Sharpe floors; bundle OOS/IS ≥ 0.5` as conditions for issuing the MERGE verdict. No mention of comparison to baseline DSR/PBO/PSR. Under the new directive: "CONFIRMATION-MERGE iff the bundle is at least as good as the current baseline across all tagged regimes".

---

### H6. CONFIRMATION-MERGE-PORTFOLIO row (Line 911)

**Text verbatim:**
```
| `CONFIRMATION-MERGE-PORTFOLIO` (multi-component) | N components combined; bundle-level gates PASS at composite; component substitution test PASS (every component contributes ≥ +0.05 bundle OOS Sharpe OR fills a unique regime); regime coverage table shows ≥3 distinct regimes covered | Update BASELINE_V1.md as new bundle stack; tag commit |
```

**Why hard-number:** `≥ +0.05 bundle OOS Sharpe`, `≥3 distinct regimes` — absolute increments. The directive's "better under all regimes" framing suggests: component must improve at least one regime over baseline without degrading any regime.

---

### H7. Portfolio Composition Rules — numerical gates (Lines 916–924)

**Text verbatim:**
```
1. **Weights:** components combined via stacking, regime-conditional dispatch, or weighted ensemble. Weights must be DETERMINISTIC (no in-sample tuning of weights on OOS).
2. **Regime coverage:** the bundle must cover ≥ 3 distinct tagged regimes. A component that duplicates another's regime coverage requires a Sharpe lift ≥ 0.30 over the substitute to remain in the bundle.
3. **Correlation diversification:** pairwise OOS daily-return correlation between components ≤ 0.70 (LOWER preferred). Cite per-pair correlations in brief Section 11.
4. **Component substitution test:** for every component, predict bundle OOS Sharpe WITHOUT that component. A component contributing < +0.05 bundle OOS Sharpe AND failing to fill a unique regime must be justified or dropped.
5. **At least one anchor:** the bundle must contain ≥ 1 component that, on its own, clears the standalone IS Sharpe > 1.0 + OOS Sharpe > 0.5 floor. Pure-specialist bundles (no anchor) are speculative and require an explicit user-directive exception.
6. **Bundle gates** (DSR, PBO, PSR, OOS/IS ≥ 0.5, ≥10 trades/month OOS, top-symbol ≤ 30%) all evaluated at the BUNDLE level — not per component.
```

**Why hard-number:** `≥ 3 distinct tagged regimes`, `Sharpe lift ≥ 0.30`, correlation `≤ 0.70`, `< +0.05`, `IS Sharpe > 1.0`, `OOS Sharpe > 0.5`, all the rule-6 floors. Rules 2/4/5 are pure absolute numbers. Under the new directive: rule 5 should be "standalone metrics no worse than baseline anchor"; rule 2/4 should be expressed as "must not degrade existing regime coverage".

---

### H8. Shared sacred constants in tracks comparison table (Lines 65–67)

**Text verbatim:**
```
- Hard merge floor: IS Sharpe > 1.0 AND OOS Sharpe > 1.0
- ≥10 trades/month OOS, ≥130 OOS total
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
```

**Why hard-number:** Listed as "shared (sacred across all three tracks)" — absolute Sharpe floors + trade count + concentration. Same numbers re-appear in H2 (bundle-level). The new directive does not allow these as absolute floors; baseline-relative comparison should replace the IS>1 and OOS>1 floors.

---

### H9. Phase 5.5 Gate Section 8 — Pre-Registered Numerical Criteria (Lines 589–590, 1219–1221)

**Text verbatim (skill description, line 590):**
```
- **Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria.** Locked numerical thresholds before backtest. Example: "MERGE iff `OOS_monthly_Sharpe ≥ +1.8` AND `PBO < 0.4` AND `PSR > 0.95` AND no symbol > 35% of OOS wpnl".
```

**Text verbatim (brief schema, lines 1220–1221):**
```
## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria
<locked numerical thresholds before backtest. Example: "MERGE iff OOS_monthly_Sharpe ≥ +1.8 AND PBO < 0.4 AND PSR > 0.95 AND no symbol > 35% of OOS wpnl">
```

**Why hard-number:** The section's purpose is literally to pre-register hard-number criteria. The example uses `OOS_monthly_Sharpe ≥ +1.8` etc. The new directive eliminates "specific numbers", so Section 8 should be replaced with "Pre-Registered Baseline-Comparison Criteria" — pre-register the regime cells to compare and the comparison direction, not specific Sharpe floors.

---

### H10. Walk-Forward Semantics — OOS/IS ≥ 0.5 gate (Line 179)

**Text verbatim:**
```
- **`OOS/IS Sharpe ≥ 0.5` is a UNIVERSAL-MODEL / BUNDLE-level gate, NOT a component-EXPLORATION gate.** It is retained for full-bundle CONFIRMATIONs (where you ARE claiming a unified regime-free predictor). It is RELAXED for individual EXPLORATION component candidates — replaced by regime-attribution analysis (Phase 7.4 LM Master mandatory Regime Attribution Table; Phase 7.5 Critic Check 3c).
```

**Why hard-number:** Defines OOS/IS ≥ 0.5 as a hard gate at the bundle/CONFIRMATION level. The new directive's "better than baseline under all regimes" reframes this: the bundle's per-regime OOS metrics must dominate baseline's per-regime OOS metrics — generalization is then measured at the regime level, not via a single 0.5 ratio.

---

### H11. EXPLORATION verdict cells — numerical Δ thresholds (Lines 881–891)

**Text verbatim (selected rows):**
```
| `UNIVERSAL` | ≥ +0.05 | ≥ +0.05 | broad across regimes | Anchor candidate | Promote to next CONFIRMATION |
| `REGIME-SPECIALIST-IS` | ≥ +0.10 | ≤ +0.05 (and ≥ −0.20) | concentrated in IS-only regimes | Bundle candidate for IS-only regimes | **PRESERVE for /044+ bundle** — log to catalog with regime tag |
| `REGIME-SPECIALIST-OOS` | ≤ +0.05 (and ≥ −0.20) | ≥ +0.10 | concentrated in OOS regimes | Bundle candidate (OOS-recurring regimes) | **PRESERVE for /044+ bundle** — log with regime tag |
| `TAIL-CONTROL` | any | any | reduces max_dd / OOS_min_month_pnl by ≥ 20% | Risk overlay | **PRESERVE for /044+ bundle** — evaluated on tail metrics, not Sharpe |
| `EXPLORATION-PROMISING` | ≥ +0.05 | ≥ +0.05 | lift present, not yet regime-attributed | TBD — pending attribution | Log to catalog; next EXP or CONFIRMATION inclusion |
| `NEGATIVE-no-effect` | within ±0.10 baseline | within ±0.10 | axis had no effect; saturated or under-powered | None | Catalog; try higher n_trials or pivot axis |
```

**Why hard-number:** This table IS relative to baseline (the Δ is "vs baseline") — that's good. But the magnitudes (`≥ +0.05`, `≥ +0.10`, `≥ −0.20`, `≥ 20%`, `±0.10`) are hard-coded boundaries. The directive's "no specific numbers" suggests these magnitudes should be expressed qualitatively ("materially positive", "neutral", "materially negative") OR scaled to baseline noise (σ-multiples vs the baseline's own seed-to-seed Sharpe variance).

**Note:** This table is HALF-aligned — it uses Δ vs baseline (good) but with hard absolute magnitudes (bad). Soften the magnitudes, keep the Δ-vs-baseline framing.

---

### H12. Key Reminders — PBO/DSR/PSR auto-block restatement (Line 1454)

**Text verbatim:**
```
- PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.
```

**Why hard-number:** Restated in the Key Reminders footer as a definitional rule. Same H1/H4 numbers, restated for emphasis. Same relaxation applies.

---

### H13. Cadence wall-clock numbers (Lines 345–347; 600, 605; 1173)

**Text verbatim (line 345–347):**
```
1. **EXPLORATION wall-clock target: 2h.** Brief MUST design to fit (single-axis variation, single-cohort preferred). If a brief estimates > 2h, Phase 6.0 Critic FLAGS as advisory — but the runtime is NOT auto-killed.

2. **CONFIRMATION wall-clock target: 8h.** Default `--confirmation --n-trials 35` + ENSEMBLE_SIZE=10. Brief Section 3.6 must show 5-step scaling. Critic Phase 6.0 FLAGS if estimate > 8h but no auto-kill. NO "CONFIRMATION-EXCEPTION" framing needed — design to fit; if it overruns, accept and learn.
```

**Why hard-number:** 2h / 8h targets used as Phase 5.5 BLOCK criterion (line 341: "if wall-clock estimate is wildly unreasonable (>3× target cap)"). NOT a merge gate per se — it's a cadence/compute gate, NOT a metric gate. **OUT OF SCOPE for the directive's "compare to baseline" reframe** — leave as-is.

---

### H14. "Insist on symbols" + concentration cap restated (Lines 67, 299, 924)

**Text verbatim (line 67):**
```
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception with justification)
```

**Why hard-number:** `30%` is an absolute cap. Used in 3 places (lines 67, 299, 924). Under the new directive: "top-symbol concentration must not be materially worse than baseline's top-symbol concentration". The "explicit exception" carve-out already softens this — extend that softening into the canonical rule.

---

### Summary of H1–H14

| Gate | Location (line refs) | Hard number | Status under new directive |
|---|---|---|---|
| H1 | 282–287 | DSR>0.95, PBO<0.4, PSR>0.95, IC<0.70, ADF<0.05 | Relax — compare to baseline |
| H2 | 291–301 | Bundle Sharpe>1.0 + OOS/IS≥0.5 + 130 trades + 30% conc + DSR/PBO/PSR | Relax — baseline-relative |
| H3 | 303–310 | Within-regime Sharpe>1.0, trade count≥30, lift≥0.10 | Relax — baseline-relative |
| H4 | 952–958 | DSR>0.95, PBO<0.4, PSR>0.95 + auto-NO-MERGE | Relax — comparative |
| H5 | 908–910 | DSR/PBO/PSR/Sharpe floors in verdict cell | Relax — replace with "no worse than baseline" |
| H6 | 911 | ≥+0.05 bundle lift, ≥3 regimes | Relax — "better in at least one regime, no worse in any" |
| H7 | 916–924 | ≥3 regimes, Sharpe lift≥0.30, corr≤0.70, <+0.05, IS>1.0, OOS>0.5, 30% conc | Relax — baseline-relative |
| H8 | 65–67 | IS>1.0, OOS>1.0, ≥130 OOS, 30% conc | Relax — baseline-relative |
| H9 | 590, 1220–1221 | Section 8 hard-number criteria | Relax — Section 8 reframed as baseline-comparison criteria |
| H10 | 179 | OOS/IS ≥ 0.5 at bundle | Reframe — per-regime baseline comparison |
| H11 | 881–891 | Verdict table Δ-magnitudes (+0.05, +0.10, ±0.10, 20%) | Soften magnitudes — keep Δ-vs-baseline framing |
| H12 | 1454 | Key Reminders restating PBO/DSR/PSR auto-block | Relax — consistent with H1/H4 |
| H13 | 345–347 | 2h/8h cadence | OUT OF SCOPE — compute, not metric |
| H14 | 67, 299, 924 | 30% top-symbol concentration | Relax — baseline-relative |

---

## 2. RELATIVE-COMPARISON sections to PRESERVE

These already implement the "compare to current baseline" principle the new directive endorses. PRESERVE and possibly strengthen.

### P1. Regime-Aware Verdict Classification table (Lines 881–891)

**Why already aligned (in framing, not magnitudes):** Every column except "Verdict" and "Bundle role" is expressed as a Δ relative to baseline (`IS Sharpe Δ`, `OOS Sharpe Δ`). The framing "compared to baseline" is exactly what the directive wants. PRESERVE the framing; relax the absolute magnitudes per H11.

---

### P2. Phase 7.4 LM Master Regime Attribution Table (Lines 768–774)

**Text verbatim (excerpt):**
```
| Regime | IS months | OOS months | This iter IS Sharpe | This iter OOS Sharpe | Baseline IS Sharpe | Baseline OOS Sharpe | Bundle role implication |
|---|---|---|---|---|---|---|---|
| bull | 14 | 3 | +2.10 | +1.45 | +1.20 | +0.80 | UNIVERSAL contributor |
| chop | 18 | 4 | +0.30 | −0.20 | +0.85 | +0.40 | Off-regime; do not select for chop bundle role |
```

**Why already aligned:** Side-by-side per-regime comparison of `This iter` vs `Baseline`. This IS the regime-by-regime comparison the directive wants. The "Bundle role implication" column codifies the qualitative judgment. PRESERVE entirely — this is the model template for the rest of the refactor.

---

### P3. Critic Scope statement — "comparison metric vs BASELINE_V1 anchor" (Lines 254–255)

**Text verbatim:**
```
**The comparison metric is always OOS Sharpe / PnL / drawdown vs the BASELINE_V1 anchor**, not trade-roster similarity. Basin migration concern belongs in the LM Master post-mortem as informational context; it is NOT a Critic gate criterion.
```

**Why already aligned:** Explicitly anchors the comparison to BASELINE_V1. PRESERVE; arguably the canonical statement of the new directive's principle, already in the skill. The phrase "vs the BASELINE_V1 anchor" should be propagated into H2/H3/H4/H5 to relax those.

---

### P4. Distinguishing REGIME-SPECIALIST from OVERFIT table (Lines 897–900)

**Text verbatim:**
```
| Signature | Verdict |
|---|---|
| IS lift via importance-INERT basin lottery, OOS catastrophic, mechanism falsified at importance/wiring layer | OVERFIT-BY-MECHANISM-FAILURE — `TRUE-NEG` / `LEARNED-NEG` |
| IS lift mechanically attributable to a load-bearing feature, OOS weakness explained by regime mismatch | `REGIME-SPECIALIST-IS` — PRESERVE |
```

**Why already aligned:** Qualitative comparison signatures (mechanism/regime attribution) rather than hard numbers. PRESERVE.

---

### P5. Walk-Forward Semantics — IS/OOS gap interpretation table (Lines 184–191)

**Text verbatim:**
```
| Pattern | Interpretation |
|---|---|
| IS strong + OOS strong, both regimes match | UNIVERSAL contributor (rare; anchor candidate) |
| IS strong + OOS weak, regime mix differs | REGIME-SPECIALIST-IS — bundle candidate if attribution shows clean within-regime edge |
| IS weak + OOS strong | REGIME-SPECIALIST-OOS — bundle candidate if OOS regime historically recurring |
| IS weak + OOS weak | TRUE-NEG — dead-paths catalog |
| Drawdown reduced without Sharpe lift | TAIL-CONTROL — evaluated on regime tail metrics, not Sharpe |
| Look-ahead bias detected (gap=0, embargo violated) | WALK-FORWARD-LEAKAGE — BLOCK; methodology integrity failure |
```

**Why already aligned:** Qualitative ("strong/weak/match/differs") not numerical. Already pattern-matched against baseline implicitly. PRESERVE; arguably the model template alongside P1/P2.

---

### P6. Catalog Schema (Lines 361–365)

**Text verbatim:**
```
| iter-v1-NNN | YYYY-MM-DD | axis varied | axis family | IS Sharpe Δ | OOS Sharpe (informational) | verdict | confirmation candidate? |
```

**Why already aligned:** `IS Sharpe Δ` column is a delta vs baseline. PRESERVE; possibly enrich with per-regime Δ columns if the new bundle methodology lands.

---

### P7. Phase 8 Diary template — "comparison vs baseline" line (Line 1268)

**Text verbatim:**
```
## What Worked
<numerical results; OOS metrics; per-symbol attribution; comparison vs baseline>
```

**Why already aligned:** "comparison vs baseline" already in the diary template. PRESERVE; strengthen by mandating per-regime comparison rather than headline-only.

---

### P8. Pre-Registered Failure-Mode vs Reality (Lines 1302–1305)

**Text verbatim:**
```
## Pre-Registered Failure-Mode vs Reality
<from brief Section 7: "predicted failure was X via Y mechanism">
<actual: "iteration failed via PBO threshold, mechanism was Z">
<match? yes/partial/no — explain>
```

**Why already aligned:** Qualitative pre-registration vs reality check. Mentions PBO as example but the framework itself is qualitative. PRESERVE.

---

### Summary of P1–P8

| Section | Location (line refs) | Why aligned |
|---|---|---|
| P1 | 881–891 | Verdict table uses Δ-vs-baseline columns (magnitudes need softening per H11) |
| P2 | 768–774 | Regime Attribution Table — side-by-side iter vs baseline per regime |
| P3 | 254–255 | Critic scope: "comparison metric vs BASELINE_V1 anchor" |
| P4 | 897–900 | REGIME-SPECIALIST vs OVERFIT table — qualitative |
| P5 | 184–191 | IS/OOS gap interpretation table — qualitative pattern-match |
| P6 | 361–365 | Catalog schema — IS Sharpe Δ column |
| P7 | 1268 | Diary template — "comparison vs baseline" line |
| P8 | 1302–1305 | Pre-registered failure-mode vs reality — qualitative |

---

## Distribution

- **Hard-number gates (H1–H14):** 14 distinct sites, with H2/H4/H5/H7/H8/H10/H12 forming a tightly coupled cluster around DSR>0.95 / PBO<0.4 / PSR>0.95 / Sharpe>1.0 / OOS/IS≥0.5 / 30% concentration — those 7 sites contain the same 5-6 hard numbers restated across the skill.
- **Relative-comparison sections (P1–P8):** 8 sites, with P1/P2/P5 forming the qualitative regime-attribution core that the refactor should expand into.
- **Skill totals (load-bearing for the merge decision):** approximately 14 hard-number gate sites vs 8 baseline-relative sites — roughly 63% hard, 37% relative. The directive moves the proportion to 100% relative.

---

## Recommended next step (not in scope of this audit)

Replace the H-cluster (H1, H2, H4, H5, H8, H10, H12) with a single "Baseline-Comparison Merge Criteria" section, anchored on P2's Regime Attribution Table template. Bundle-level verdicts become: "bundle is at least as good as baseline in every tagged regime, and strictly better in at least one regime" — no absolute Sharpe / DSR / PBO / PSR floors. Retain methodology-integrity gates (no look-ahead, embargo, gap correct, no OOS tuning) as the only absolute gates; relax all metric gates to baseline-relative.

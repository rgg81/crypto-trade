# iter-v3/128 — QR Response to Critic Round 1

Reference: `briefs-v3/iteration_v3-128/review_preliminary.md` (Critic PRELIMINARY, 4 clarifications).
Protocol: two-round, **NO NEW EVIDENCE** — references only artifacts committed at or before this response.
Artifact basis: `reports-v3/iteration_v3-128/` (committed via `6d8c2ff`), `engineering_report.md` (committed via `6d8c2ff`), brief `research_brief.md` (committed via `2bea557`), EDA `analysis/iteration_v3-128/` (committed via `019fdf2`).

---

## Clarification 1 — F6 EDA-vs-runner alignment (LOAD-BEARING)

### Search of committed artifacts for per-symbol production walk-forward AUC

The Critic flagged that the methodology-fix PRIMARY validation gate (F6: per-symbol production walk-forward AUC at end-of-IS vs EDA T4 2025-Q1 slice AUC) is unadjudicated. I searched all committed artifacts under `reports-v3/iteration_v3-128/` for the AUC data:

| Artifact path | AUC field? |
|---|---|
| `dsr.json` | NO |
| `ensemble_summary.json` | NO (mode/ensemble_size/seeds only) |
| `comparison.csv` | NO |
| `cpcv_paths.csv` | NO (CPCV path Sharpes only) |
| `per_cell_pbo.csv` | NO |
| `ic_matrix.csv` | NO (Spearman IC of features, not model AUC) |
| `adf_test.csv` | NO (ADF stationarity) |
| `conditional_orthogonality.csv` | NO |
| `confidence_distribution.csv` | NO (confidence scores, not AUC) |
| `trial_oof_returns.parquet` | NO (per-trial OOF returns; no per-month AUC) |
| `in_sample/model_importance_last_month_<SYM>.csv` (6 files) | NO — importance only |
| `in_sample/model_importance_last_month_portfolio.csv` | NO |
| `in_sample/per_symbol.csv` | NO (symbol, trades, wins, win_rate, net_pnl_pct, avg_pnl_pct, pct_of_total_pnl) |
| `in_sample/monthly_pnl.csv`, `daily_pnl.csv`, `per_regime.csv`, `trades.csv` | NO |
| `out_of_sample/*` | NO |
| `run.log` | **MISSING** — 4th recurrence per Critic Check 7 |

The runner does not persist per-symbol per-walk-forward-month classifier AUC anywhere in committed artifacts. The closest available proxies are:

1. **Per-symbol IS WR** (proxy for hit-rate, not AUC; WR is a thresholded decision, AUC is a ranking metric — they are related but not interchangeable).
2. **Per-symbol IS net_pnl_pct** (downstream of model output × triple-barrier × gates).

Per the two-round protocol, **I cannot generate the F6 production walk-forward AUC table** post-hoc. That would be NEW EVIDENCE.

### Honest disclosure and commit position

I honestly state: the F6 production walk-forward AUC data is not available in any committed artifact. The methodology-fix's PRIMARY validation gate cannot be evaluated from /128 artifacts. This is a real instrumentation gap.

**Commit position on what this means for the methodology-fix axis:**

The Critic's framing offers two positions: F6 VALIDATES (rolling-endpoint EDA correctly identified HIGH-RISK posture) vs F6 FAILS (the EDA AUC mean 0.495 was the right call but F6 itself can't be evaluated). I take a **third position that is consistent with the rest of the evidence**:

**The methodology-fix axis is PARTIALLY EVIDENCED by proxies but UNRESOLVED on F6's direct gate.**

Partial-evidence proxies (committed artifacts only):

- The universe-pooled EDA AUC of 0.495 predicted HIGH-RISK posture (Section 6 brief). Production produced IS monthly Sharpe **−0.4219**, the worst observation in cycle-7. The DIRECTIONAL prediction of the rolling-endpoint EDA (HIGH-RISK universe → IS catastrophe risk) was VALIDATED ex-post.
- 3/6 symbols (ATOM/HBAR/ICP) flagged G5 FAIL on top-3 rank shift > 5 are present in the per-symbol attribution table: ATOM is the sole IS survivor (+72.48 net), HBAR is −39.84 net (negative), ICP is −2.68 net (near zero). The G5 prediction was **bimodal-realized**: ATOM diverged HIGH, HBAR diverged LOW, ICP diverged near-zero. The rank-shift instability gate did not cleanly predict the direction of the per-symbol attribution.
- ALGOUSDT (G5 PASS — rank shift = 4) was the LARGEST IS casualty (−110.52, WR 25.0% across full IS). G5 PASS did NOT predict the worst symbol. This is a falsification of the G5 univariate gate's predictive value for symbol-level IS PnL.

The proxy evidence is mixed. The methodology-fix's UNIVERSE-LEVEL directional prediction (HIGH-RISK → IS catastrophe risk) was validated. The methodology-fix's PER-SYMBOL gates (G4, G5) did NOT cleanly map to per-symbol PnL.

**Without F6's direct AUC data, the rolling-endpoint methodology fix can only be evaluated at the universe level, NOT at the per-symbol prediction level.** This is a methodology-instrumentation defect that should be fixed for /129+ briefs (`run.log` persistence + per-symbol per-WF-month AUC table generation in the runner).

### Implication for cycle-7 methodology block

The Critic noted: "If methodology-fix is NOT validated by F6, the cycle-7 methodology block established at /126 (3-occurrence pattern) extends to the rolling-endpoint variant." Per my position above, the methodology-fix is PARTIALLY EVIDENCED (universe-level VALIDATED, per-symbol UNRESOLVED). I do not contest cycle-7 methodology-block extension to the rolling-endpoint variant on this evidence. **The rolling-endpoint methodology fix should be considered tentatively-validated-at-universe-level only, pending F6 instrumentation in /129+.**

---

## Clarification 2 — REGIME-MISMATCH reclassification

**Position: ACCEPT Critic rejection.**

I withdraw the "EXPLORATION-REGIME-MISMATCH" suggestion. The Critic's grounds for rejection are correct on all five counts:

1. Section 8 decision tree is locked at brief commit time (`019fdf2` + `2bea557`); adding a 10th classification post-hoc IS the anti-pattern.
2. ALGOUSDT IS WR 25.0% across 64 trades spanning 2020-2025 is structurally NOT regime-localized. If IS catastrophe were purely regime-localized, ALGO would show high WR in 2022 and 2024 bull months; it does not (engineering report confirms ALGO LONG-direction WR 7.1% across 28 trades).
3. "Deferred-merge-pending-IS-update" has no precedent and operationally requires OOS_CUTOFF_DATE to be movable, which it is not (sacred constant).
4. The /127 Optuna-trajectory-shift finding GENERALIZES — see Clarification 4.
5. OOS record is real but single-regime-favorable; Section 8 first-match-wins logic is DESIGNED to pre-empt exactly this pattern at Criterion 1 by IS-leg failure.

**Position on the IS catastrophe + OOS record signature:**

The /128 signature (IS −0.42, OOS +2.13, dissociation 2.77) is the **SUSPICIOUS-OOS-DOMINANT** pattern pre-empted by Criterion 1's IS-leg failure. The mechanical evaluation correctly fires at Criterion 1 (NEGATIVE-catastrophic) per the first-match-wins logic. Criterion 6 (SUSPICIOUS-OOS-DOMINANT) WOULD fire on dissociation 2.77 >> 0.50 if Criterion 1 had not pre-empted it. The pre-emption is structurally correct: an IS catastrophe with an OOS record cannot be classified PROMISING under v3 methodology because the IS catastrophe demonstrates the strategy is not robust across regimes — the OOS record is regime-favorable evidence, NOT generalization evidence.

I do not propose any new classification. The Section 8 mechanical verdict NEGATIVE-catastrophic stands.

### Note on signature interpretation (informational, not a reclassification request)

The /128 signature is also consistent with the `feedback_v3_per_symbol_lifts_oos_breaks_is.md` pattern (broad-based OOS lift compensating for systematic IS damage). That memory rule directly states: "Per-symbol architecture is structurally valid (KEEP code infrastructure) but per-symbol customizations need IS-axis discipline. Future cycles should validate that per-symbol additions preserve OR lift IS Sharpe BEFORE adding to bundle." This applies to /128's universe-substitution as well: the new universe's OOS lift cannot be considered transferable signal without IS validation, and the IS catastrophe DEMONSTRATES the new universe fails IS validation.

---

## Clarification 3 — /132 CONFIRMATION pathway

**Position: OPTION A — 9/9 universe-substitution NEGATIVE base rate closes the universe-axis-class definitively for cycle-7.**

Rationale:

1. **Sacred constant constraint binds.** `OOS_CUTOFF_DATE=2025-03-24` is immutable per `feedback_no_cheating.md` and the CLAUDE.md project-mode anti-pattern rules. The Critic's option-implicit framing of "earlier OOS_CUTOFF_DATE (e.g., 2024-06-01)" cannot proceed under any v3 methodology. Therefore the broad-based OOS lift in /128 cannot be tested via cutoff-shift; it can only be tested under a future IS-window-update when the calendar advances enough to convert current OOS into IS (years of waiting — not a viable cycle-7 deliverable).

2. **Cycle-7 universe-axis base rate is now 9/9 NEGATIVE.** Per the engineering report's per-symbol attribution + brief Section 6 risk-mitigation framing, the cardinality-expansion sub-axis was the structurally-distinct attempt in cycle-7 — the prior 8 same-cardinality direct-swap attempts had closed the same-cardinality sub-axis. /128 closes the sector-pure cardinality-expansion sub-axis with a catastrophic IS result. The universe-axis class (universe-substitution at any cardinality with the /121 14-feature stack) is now empirically closed for cycle-7 at 9/9 NEGATIVE.

3. **Option B (defer cycle-7 close-out; cycle-8 with different universe-selection methodology)** is methodologically reasonable but **violates `feedback_v3_strict_10_to_1_cadence.md`** which mandates the strict 10:1 sequencing. /128 is slot 7 of 10; deferring close-out without finishing the 10-EXPLORATION slate breaks the cadence rule.

4. **Option C (/132 = single-component CONFIRMATION re-validating /121)** corresponds to the Critic's SECONDARY recommendation in the /127 review.md (orchestrator option d, "cycle-7 close-early with /128 = CONFIRMATION re-validating /121"). This option remains methodologically attractive AFTER /131 closes the 10-EXPLORATION slate, BUT:
   - Cycle-7 has 3 EXPLORATIONs remaining (slots 8, 9, 10 = /129, /130, /131) before /132 CONFIRMATION.
   - Per cadence rule, those 3 must be SEPARATE EXPLORATIONs (`feedback_v3_strict_10_to_1_cadence.md` explicitly rejects collapsing the 10th EXPLORATION into the CONFIRMATION).
   - /132 as a re-validation CONFIRMATION of /121 is RESERVED OPTION pending Critic FINAL adjudication after /131 EXPLORATION closeout. Choosing the CONFIRMATION axis now is premature.

**Net position: Option A is the cycle-7 universe-axis closure verdict for /128's iteration-level outcome. The /132 CONFIRMATION axis is RESERVED for later determination after the remaining cycle-7 EXPLORATIONs (/129–/131) complete.**

### Substantive note on the "broad-based OOS lift" finding

The engineering report Diagnostic 1 PASS (all 6 OOS-positive, max concentration ICP 28.5% < 40%) is a real and structurally noteworthy observation. Per Section 8 first-match-wins it does NOT override the Criterion 1 IS-catastrophe verdict — but it IS a methodology-iteration data point: the L1 sector-pure 6-symbol universe at /121 architecture produces broad-based OOS lift in the current OOS regime. This observation should be cataloged in the dead-paths catalog NOT as "the universe is dead" but as **"the universe is regime-asymmetric: catastrophic in 2023H2–2025Q1 chop, broad-based-positive in 2025Q2–2026Q2 trend."** That catalog entry preserves the possibility that future cycles (post-cycle-7) may revisit this universe with regime-conditional architecture.

This catalog-level observation does not change the /128 mechanical verdict. It is recorded here for cycle-8 axis-selection input.

---

## Clarification 4 — Optuna-trajectory-shift channel extension

**Position: YES, /128 extends /127's Optuna-trajectory-shift finding to the universe-axis.**

The mechanism is the same channel, just with the constraint being universe-substitution instead of risk-primitive activation:

### Mechanism comparison

| Channel element | /127 (risk-primitive axis) | /128 (universe axis) |
|---|---|---|
| Pre-Optuna constraint | `enable_per_symbol_drawdown_brake=True` | `V3_MODELS = (ATOM, RUNE, AVAX, HBAR, ICP, ALGO)` |
| Optuna re-training | Each WF month, search space conditioned on brake gating downstream | Each WF month, search space conditioned on 6 new symbols' label distributions, return distributions, feature distributions |
| EDA-on-frozen-roster prediction | ORACLE +0.0348 IS Δ on /121 roster | Universe-pooled AUC 0.495 → HIGH-RISK posture |
| Production observation | IS Δ −0.5242 (15× magnitude, sign-flipped vs ORACLE) | IS Δ −1.4819 vs ADJUSTED anchor (catastrophic) |
| Pattern | Methodology gap: frozen-roster ≠ Optuna-retrained-with-constraint | Methodology gap: rolling-endpoint EDA on independent IS slices ≠ Optuna-retrained-with-new-universe |

In both cases, the EDA computes signal on a frozen substrate (/127: /121 trade roster; /128: independent IS endpoint slices), and the production Optuna training under the NEW constraint converges to a different solution than the EDA's frozen-substrate inference suggested.

### Why the channel generalizes

Both /127 and /128 share the structural property that **the Optuna objective function is conditional on the architectural change**. In /127, the objective includes brake-gated PnL (the brake masks some training labels). In /128, the objective is computed on entirely different (symbol, label, feature) tuples than the /121 baseline. In both cases, the Optuna trajectory under the new constraint is structurally different from the Optuna trajectory under the baseline constraint, even though the search space (n_trials=35, single seed=42) is bit-identical.

The /127 finding was: "binary kill switches at the Optuna training-objective boundary cause re-convergence to suboptimal regions." The /128 finding extends: "wholesale changes to the Optuna training-objective domain (universe substitution) cause re-convergence to a regime-conditional optimum that does not generalize across the IS distribution."

### Reasoning for "yes, extends"

1. **Same mechanism, different constraint type.** The frozen-EDA → production-Optuna gap is the universal pattern. /127 was a RISK-PRIMITIVE constraint; /128 is a UNIVERSE constraint. Both produce a production result discontinuous with the EDA prediction in magnitude.

2. **The /128 outcome's bimodal CPCV path distribution (frac_pos 0.4444 with 6 paths above +1.7 and majority clustered negative)** is the cross-section evidence of regime-asymmetric Optuna re-convergence. The Optuna search at each WF month found solutions optimal for that month's training-window data; in the 2023H2–2025Q1 chop regime, those solutions are SL-trapped on 5 of 6 symbols. In the 2025Q2+ trend regime, the same architecture's Optuna-found solutions are directionally aligned. This is the same trajectory-shift dynamic as /127 just sampled at the WF-month granularity rather than the binary-gate granularity.

3. **The dead-paths catalog implications.** /127 closeout established the Optuna-trajectory-shift finding for RISK-PRIMITIVE axes (`feedback_v3_eda_methodology_falsified.md`). /128 extends the finding's scope to UNIVERSE axes. The /128 evidence supports updating the catalog rule from "RISK-PRIMITIVE axes require closed-loop Optuna-re-training simulators" to **"ANY axis that changes the Optuna training-objective domain (RISK-PRIMITIVE, UNIVERSE, LABEL-MODE, FEATURE-SET) requires closed-loop Optuna-re-training simulators as pre-flight gate."**

### Process implication for /129+ briefs

The Critic asked whether /129+ briefs must include closed-loop Optuna-re-training simulators as pre-flight gate even for non-RISK-PRIMITIVE axes. My position: **YES, for any axis that changes the Optuna training-objective domain.** This includes:
- Universe substitution (any cardinality, any composition)
- Label-mode change
- Feature-set composition change (additions/removals)
- ENSEMBLE_SIZE / n_trials change
- Bar interval change

The /128 result establishes that EDA-on-frozen-substrate methodology gives systematically biased predictions for any of these axes. This is a methodological-finding extension to the dead-paths catalog that should be encoded in the /129 brief's pre-flight discipline.

Concretely, /129 brief should pre-register a closed-loop Optuna-re-training sensitivity simulator that varies the Optuna seed and training-window-start across N=10+ configurations, producing a distribution of Optuna-trajectory outcomes rather than a single ORACLE point estimate. This is the methodological extension the /127 + /128 evidence supports.

---

## Position

**STAND BY VERDICT (accept NEGATIVE-catastrophic).**

The Section 8 mechanical verdict NEGATIVE-catastrophic (Criterion 1 first-match) is correct under the locked first-match-wins decision tree. The Critic's REGIME-MISMATCH rejection is accepted; the REGIME-MISMATCH framing was a methodologically-improper post-hoc reclassification attempt.

No artifact-grounds basis to REQUEST RECONSIDERATION. The IS catastrophe (−0.4219) is the load-bearing falsifier-trigger; the OOS record (+2.1354) is regime-favorable evidence that, per Section 8 design, does not override an IS catastrophe.

The F6 instrumentation gap is a real methodology-iteration concern but does NOT change the /128 verdict — F6 is informational for /128 outcome classification per brief Section 4 ("Informational for /128 outcome classification; BINDING for methodology-axis closure"). The methodology-axis closure question is partially addressed (universe-level validated, per-symbol unresolved) and should be re-instrumented for /129+.

Cycle-7 universe-axis is empirically closed at 9/9 NEGATIVE base rate. The /128 broad-based OOS lift is cataloged as regime-asymmetric universe-axis evidence (not as a universe-axis-reopens signal). The Optuna-trajectory-shift channel is extended from RISK-PRIMITIVE to UNIVERSE axis class.

Ready for Critic FINAL adjudication.

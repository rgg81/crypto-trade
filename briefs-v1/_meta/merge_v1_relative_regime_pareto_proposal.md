# RELATIVE-REGIME-PARETO Merge Framework Proposal — v1

**Date:** 2026-05-31
**Status:** PROPOSAL pending user adoption
**Anchor directive (verbatim):**
> "I want to review to be more flexible, and to always compare with the current baseline. This should be always a comparison. The objective is clear: a new baseline is taken if the bundle model performs better under all regimes. We don't need specific numbers, but this is the general idea."

**Supersedes (if adopted):** Hard-number gate cluster H1, H2, H4, H5, H6, H7, H8, H10, H11 (magnitudes), H12, H14 from `merge_criteria_audit.md`.
**Preserves:** Methodology-integrity gates (look-ahead, embargo, walk-forward gap, reproducibility) — these are integrity, not edge, and remain HARD.
**Inputs:** `merge_criteria_audit.md`, `regime_ensemble_methodology.md`, `quant-iteration-v1.md` (current skill).

---

## Section A — Principle Statement

**MERGE-PRINCIPLE (canonical, one sentence):**
> A candidate bundle becomes the new baseline if and only if, under every tagged regime, the candidate is Pareto-better-or-equal to the current baseline on the bundle metric vector, AND strictly better in at least one regime, AND methodology integrity is intact.

Three load-bearing words:

- **Pareto.** No regime is allowed to regress materially. Cross-regime trade-offs ("we lost chop, but gained bull") are NOT acceptable. The candidate must be a domination of the current baseline on the per-regime surface, not a re-shuffle of edge.
- **Regime.** Comparison is always within-regime (bull / alt-rotation / chop / bear / vol-spike / liquidation-cascade / ETF-flow / recovery / …). Aggregated OOS-Sharpe-vs-OOS-Sharpe is meaningless when the OOS window's regime mix differs from the IS window's regime mix.
- **Relative.** No absolute Sharpe / DSR / PBO / PSR floors. Every metric is compared against the corresponding metric on the current baseline. The directive's "no specific numbers" is taken literally for edge metrics. Numbers remain only where they enforce methodology integrity (gap≥0, embargo>0, reproducibility checksum match).

Three corollaries:

1. **The bundle is the product.** Components are evaluated as bundle contributors. EXPLORATION verdicts already accommodate this (REGIME-SPECIALIST-IS / OOS preserved). MERGE evaluation lives at the bundle level only.
2. **OOS is one regime realization, not a generalization oracle.** A candidate that ties baseline on every IS-tagged regime AND ties baseline on the OOS-tagged regime is a MERGE candidate even if the headline OOS Sharpe number is unchanged — it's an equally-good universal.
3. **Statistical-significance metrics inform; they do not gate.** DSR / PBO / PSR are reported per-regime AND at bundle level. Their values vs baseline are flagged in the diary. They do NOT auto-trigger BLOCK.

---

## Section B — Per-Regime Pareto-Dominance Check (Algorithmic)

### B.1 Regime tags (canonical)

A regime is a labeled month-range derived from the existing `regime_attribution.csv` artifact (Phase 6 deliverable). Tags currently in use:

- `bull` — sustained BTC uptrend, low vol, alt participation
- `alt-rotation` — alts leading BTC, BTC.D falling
- `chop` — sideways, low directional persistence, mean-reverting
- `bear` — sustained BTC downtrend
- `vol-spike` — realized vol > 75th percentile of trailing 90d
- `liquidation-cascade` — daily liquidations > $1B notional cluster
- `recovery` — post-bear retrace
- `ETF-flow` — large persistent net spot ETF inflow/outflow

Each tagged regime has a known month-count in IS and OOS, persisted in the regime catalog (`briefs-v1/_meta/regime_catalog.md` — to be authored alongside this proposal at adoption).

### B.2 Per-regime metric vector

For every tagged regime `R` (present in IS or OOS or both), compute on both BASELINE and CANDIDATE:

```
M(R) = {
  sharpe_R           : within-regime daily-PnL Sharpe (annualized)
  max_dd_R           : within-regime peak-to-trough drawdown
  trade_count_R      : within-regime closed-trade count
  monthly_calmar_R   : sharpe_R / max_dd_R proxy
  hit_rate_R         : within-regime win rate
}
```

### B.3 Pareto-dominance predicate

```
PARETO_BETTER_OR_EQUAL(CANDIDATE, BASELINE, R) :=
    sharpe_R(CANDIDATE)       >= sharpe_R(BASELINE)       - epsilon_sharpe(R)
  AND max_dd_R(CANDIDATE)     <= max_dd_R(BASELINE)       + epsilon_dd(R)
  AND trade_count_R(CANDIDATE) >= 0.5 * trade_count_R(BASELINE)        # RELATIVE trade-count floor

PARETO_STRICTLY_BETTER(CANDIDATE, BASELINE, R) :=
    PARETO_BETTER_OR_EQUAL(CANDIDATE, BASELINE, R)
  AND (sharpe_R(CANDIDATE) > sharpe_R(BASELINE) + epsilon_sharpe(R)
       OR max_dd_R(CANDIDATE) < max_dd_R(BASELINE) - epsilon_dd(R))

MERGE_VERDICT(CANDIDATE, BASELINE) :=
    FOR_ALL R in REGIMES_PRESENT:
        PARETO_BETTER_OR_EQUAL(CANDIDATE, BASELINE, R)
  AND EXISTS R* in REGIMES_PRESENT:
        PARETO_STRICTLY_BETTER(CANDIDATE, BASELINE, R*)
  AND METHODOLOGY_INTEGRITY_PASS(CANDIDATE)
```

### B.4 epsilon definitions (regime-noise-scaled, NOT absolute)

`epsilon_sharpe(R)` and `epsilon_dd(R)` are NOT hard-coded numbers. They are derived from the baseline's own seed-to-seed variance on that regime, computed once when the baseline is committed:

```
epsilon_sharpe(R) = 1.0 * stddev_across_seeds(sharpe_R(BASELINE))
epsilon_dd(R)     = 1.0 * stddev_across_seeds(max_dd_R(BASELINE))
```

Tolerance band = "one baseline-seed-sigma on that regime". If the candidate is within one baseline-noise-σ, it ties the baseline on that regime. This is comparison-relative by construction — there are no absolute Sharpe thresholds anywhere.

### B.5 Rare-regime carve-out

If `trade_count_R(BASELINE) < 10`, the regime is RARE. For rare regimes:

- The trade-count floor (`>= 0.5 * baseline`) is REPLACED with "candidate must produce ≥ 1 trade in regime R if baseline produced ≥ 1".
- The Pareto-dominance check uses **win_rate_R** instead of sharpe_R (small-sample-robust).
- A rare regime cannot block MERGE on its own; it can only flag for the diary.

### B.6 Edge-case: regime present in CANDIDATE but not BASELINE

If a regime appears in OOS for the first time (e.g., a 2026 ETF-flow regime that wasn't in 2020–2025 IS), the candidate has no baseline-regime metric to compare against. Resolution:

- Candidate is evaluated on within-regime trade hygiene only (no look-ahead, no concentration > 50% of regime PnL on one symbol).
- Diary records the new regime as a baseline-extension event; future iterations have a baseline-regime-metric to compare against.

---

## Section C — Methodology Gates (HARD; PRESERVED)

These are integrity gates, NOT edge gates. They remain absolute and BLOCKing because they detect arithmetic / data-handling bugs that produce fake edge. The directive's "no specific numbers" does NOT apply to integrity.

| Gate | Where | What it checks | Why HARD |
|---|---|---|---|
| **C1 — No look-ahead** | Critic Check 1 | Every feature computable from data with timestamp < t for every t; `.shift(1)` on rolling stats; past-only σ_t in triple-barrier | Look-ahead manufactures Sharpe out of thin air. Bias is not regime-attributable. |
| **C2 — Embargo intact** | Critic Check 2 | `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`; embargo δ ≈ 1% of T; gap symmetric both sides of test boundary | Embargo violation = train-on-test leakage. Equally invalid in IS and OOS. |
| **C3 — Walk-forward gap correct** | Critic Check 1+2 combined | `gap = max(label_horizon × n_symbols × bars_per_horizon)` between train and test in every fold | Sub-gap leakage corrupts every per-regime metric. |
| **C4 — Reproducibility checksum** | Critic Check 7 | Re-running the runner with the same seed produces bit-identical trades CSV | Non-reproducible runs are non-falsifiable. |
| **C5 — No OOS tuning** | Phase 5.5 gate + diary audit | No Phase 1–5 artifact references OOS data | Researcher overfitting; OOS becomes a tuning set. |
| **C6 — Feature column pinning** | Phase 6 QE | `feature_columns=list(V1_FEATURE_COLUMNS)` passed explicitly to LightGbmStrategy | `colsample_bytree` samples by position; unpinned columns produce silent model drift. |
| **C7 — Forming-candle drop** | Phase 6 QE | `fetcher.py` filter: `k.close_time < now_ms` | Predicting on incomplete candle = look-ahead. |
| **C8 — Survivorship handling** | Phase 6 QE | Delisted symbols included with NaN post-delist; no post-hoc universe filter | Survivorship inflates Sharpe ~4× on a naïve top-N rebalance. |

**Verdict:** Any C1–C8 violation = `BLOCK-FINAL` regardless of per-regime Pareto outcome. Methodology trumps edge.

---

## Section D — Statistical-Significance Metrics (INFORMATIONAL)

DSR, PBO, PSR remain MANDATORY-TO-COMPUTE (per the comparison.csv schema in skill lines 927–950) but become INFORMATIONAL-not-BLOCKing.

| Metric | Old role | New role |
|---|---|---|
| **DSR (Deflated Sharpe Ratio)** | HARD: < 0.95 = auto-NO-MERGE | INFORMATIONAL: reported per-regime AND bundle-level. If `DSR(CANDIDATE) < DSR(BASELINE)`, diary must include a "DSR-regression justification" paragraph. NOT a BLOCK. |
| **PBO (Probability of Backtest Overfitting)** | HARD: ≥ 0.4 = auto-NO-MERGE | INFORMATIONAL: reported bundle-level. If `PBO(CANDIDATE) > PBO(BASELINE) + 0.10`, flag for next-cycle reconsideration in diary. NOT a BLOCK. |
| **PSR (Probabilistic Sharpe Ratio)** | HARD: < 0.95 = auto-NO-MERGE | INFORMATIONAL: reported per-regime. PSR < baseline PSR in any regime requires diary acknowledgment. NOT a BLOCK. |

**Rationale:** DSR/PBO/PSR are derived from the bundle's per-trial Sharpe distribution. The Pareto-regime check already validates that the candidate is at least as good as baseline everywhere — if the candidate ties on every regime but has slightly worse DSR, that's a noise artifact of the Optuna search trajectory, not a real edge regression. Auto-blocking on it killed regime specialists (see /039 reframe history).

**Critic Check 3 reframe:**

- Check 3a: report DSR vs baseline DSR (per-regime AND bundle). Verdict = INFO.
- Check 3b: report PBO vs baseline PBO. Verdict = INFO (flag if Δ > +0.10).
- Check 3c: regime-attribution clarity (UNCHANGED — this was already qualitative).
- Check 3d: per-regime Pareto-dominance — this IS the load-bearing merge gate. Verdict = PASS / BLOCK.

---

## Section E — Trade-Count and Concentration Replacements

### E.1 Trade-count floor — RELATIVE

| Old | New |
|---|---|
| `≥ 130 OOS total trades, ≥ 10 trades/month OOS` | `trade_count_R(CANDIDATE) ≥ 0.5 × trade_count_R(BASELINE)` for every regime R with baseline trade count ≥ 10. Rare regimes (baseline < 10) use the carve-out in §B.5. |

**Rationale:** A bundle that produces half the trades but the same edge per regime is acceptable IF Pareto-dominance holds. The absolute 130 floor was inherited from the σ_SR ≈ √(1/T) noise-floor argument; that argument applies to the **baseline's** trade count, not to the candidate's. The candidate inherits the baseline's statistical power if it does not drop trade count by more than half per regime.

### E.2 Concentration cap — ADVISORY with regime-attribution carve-out

| Old | New |
|---|---|
| `Top symbol ≤ 30% OOS PnL (or explicit exception)` | `top_symbol_share(CANDIDATE) ≤ top_symbol_share(BASELINE) + 10pp` is the auto-PASS lane. If candidate concentration > baseline by ≥10pp, Critic Check 3c (regime-attribution) inspects WHY: if the top symbol is the bundle's specialist for a regime baseline doesn't cover (or covers worse), ACCEPT; otherwise BLOCK. |

**Rationale:** Specialist roles produce concentration by design. /044 substrate plan (BASELINE + /036 + /040 + /037) has /040's DOT-heavy attribution as a regime-specialist contribution; auto-blocking on 30% would kill the bundle. The new rule recognizes concentration as an emergent property of regime-specialist composition.

---

## Section F — Multi-Seed Validation Reframe

| Old | New |
|---|---|
| `10-seed pre-MERGE: mean Sharpe > 0, ≥7/10 profitable` | `10-seed mean Sharpe_R(CANDIDATE) ≥ 10-seed mean Sharpe_R(BASELINE)` for every regime R; AND `seed-distribution dominance ratio ≥ 0.5` (at least 5 of 10 candidate-seed Sharpes per regime beat the baseline's median seed Sharpe on that regime). |

**Rationale:** The mean>0 / 7-of-10 floor was an absolute stability check. The relative version validates that the candidate is at least as seed-stable as the baseline ON THE SAME REGIMES, which is the integrity claim that matters. A baseline with mean Sharpe 1.5 should not be replaced by a candidate with mean Sharpe 0.05 just because both are >0; conversely, a candidate with mean Sharpe 1.4 should not be blocked merely because the absolute floor was 1.5.

**Operational note:** The baseline's per-regime per-seed Sharpe matrix must be persisted at MERGE time as `briefs-v1/_meta/baseline_seed_regime_matrix.csv`. Candidate MERGE evaluation reads this file. Without it, the relative validation cannot run.

---

## Section G — Example Scenarios

### G.1 Candidate beats baseline everywhere

| Regime | Baseline SR | Candidate SR | Pareto? |
|---|---|---|---|
| bull | +1.20 | +1.45 | strictly better |
| chop | +0.40 | +0.60 | strictly better |
| vol-spike | −0.10 | +0.05 | strictly better |
| recovery | +0.85 | +0.90 | better-or-equal (within σ) |

**Verdict:** `CONFIRMATION-MERGE-PORTFOLIO`. All regimes Pareto-better-or-equal; at least one strictly better. Methodology PASS. Concentration flagged INFO if applicable. DSR/PBO/PSR reported.

### G.2 Candidate beats baseline in 3 of 4 regimes; ties the fourth

| Regime | Baseline SR | Candidate SR | Pareto? |
|---|---|---|---|
| bull | +1.20 | +1.55 | strictly better |
| chop | +0.40 | +0.45 | tie (within σ) |
| vol-spike | −0.10 | +0.20 | strictly better |
| recovery | +0.85 | +1.10 | strictly better |

**Verdict:** `CONFIRMATION-MERGE-PORTFOLIO`. All regimes ≥ baseline (chop ties within σ); three regimes strictly better. PASS.

### G.3 Candidate ties baseline on every regime

| Regime | Baseline SR | Candidate SR | Pareto? |
|---|---|---|---|
| bull | +1.20 | +1.22 | tie |
| chop | +0.40 | +0.38 | tie (within σ) |
| vol-spike | −0.10 | −0.08 | tie |
| recovery | +0.85 | +0.83 | tie |

**Verdict:** `CONFIRMATION-NO-MERGE` (NO strict improvement). Document in diary as `EXPLORATION-NEGATIVE-noise-equivalent`. Candidate is not worse; it's just not better. Baseline stands. Catalog the candidate as a potential future component if regime mix shifts.

### G.4 Candidate loses one regime, wins the rest

| Regime | Baseline SR | Candidate SR | Pareto? |
|---|---|---|---|
| bull | +1.20 | +1.80 | strictly better |
| chop | +0.40 | −0.30 | WORSE (Δ = −0.70, > σ band) |
| vol-spike | −0.10 | +0.40 | strictly better |
| recovery | +0.85 | +1.20 | strictly better |

**Verdict:** `CONFIRMATION-BLOCK` (Pareto-dominance fails on chop). Bundle composition is "regime traded" — gained bull/vol-spike/recovery but lost chop. The new framework REJECTS this even though headline OOS Sharpe is up, because the directive's "better under all regimes" is violated.

**Path forward:** The candidate is a `REGIME-SPECIALIST` candidate for bull/vol-spike/recovery. Next CONFIRMATION should add a chop-specialist component to the bundle and re-evaluate the combined stack. The candidate is preserved in the catalog, not discarded.

### G.5 Methodology violation (look-ahead detected)

| Regime | Baseline SR | Candidate SR | Pareto? |
|---|---|---|---|
| bull | +1.20 | +2.50 | strictly better |
| chop | +0.40 | +1.10 | strictly better |
| vol-spike | −0.10 | +0.80 | strictly better |
| recovery | +0.85 | +1.90 | strictly better |

**Critic Check 1:** `analysis/iteration_v1-NNN/feature_xyz.py` computes a rolling z-score without `.shift(1)` — uses bar-close in the bar's own decision.

**Verdict:** `BLOCK-FINAL` (`WALK-FORWARD-LEAKAGE`). Methodology integrity gate C1 fails. Pareto-dominance result is IGNORED because the metrics themselves are corrupt. No baseline update; iteration discarded.

---

## Section H — Edit Map (CURRENT → PROPOSED)

| Tag | Section / Lines | CURRENT (verbatim shortened) | PROPOSED |
|---|---|---|---|
| **H1** | Sacred Constants 282–287 | `DSR_threshold = 0.95; PBO_threshold = 0.40; PSR_threshold = 0.95` as global merge constants | Remove constant declarations as MERGE thresholds. Re-declare as `DSR_baseline_anchor`, `PBO_baseline_anchor`, `PSR_baseline_anchor` — values read from `briefs-v1/_meta/baseline_metric_anchors.csv` at iteration start. Used for diary INFO comparison only. |
| **H2** | Bundle-level gates 291–301 | Bundle Sharpe > 1.0, OOS/IS ≥ 0.5, ≥130 trades, ≤30% conc, DSR/PBO/PSR floors | Replaced wholesale by Section B Pareto-dominance check. New section: "Bundle MERGE evaluation = Pareto-regime check per §B + methodology integrity per §C + INFO metrics per §D". |
| **H3** | Component-level gates 303–310 | Within-regime Sharpe > 1.0, trade ≥30, lift ≥0.10 | "Component candidate evaluated on within-regime Sharpe Δ vs baseline's within-regime Sharpe (positive Δ on target regime; no regression > 1σ on any other regime). Lift magnitude qualitative." |
| **H4** | Hard Thresholds 952–958 | `DSR > 0.95 required; PBO < 0.4 required; PSR > 0.95 required; auto NO-MERGE` | Section renamed "Reported Statistical-Significance Metrics" (informational). Per Section D. Critic Check 3 reframed per §D. |
| **H5** | CONFIRMATION-MERGE (single-axis) verdict cell 910 | "all bundle-level gates PASS (DSR > 0.95; PBO < 0.4; PSR > 0.95; bundle Sharpe floors; bundle OOS/IS ≥ 0.5)" | "Pareto-regime check PASSES per §B; methodology integrity intact per §C" |
| **H6** | CONFIRMATION-MERGE-PORTFOLIO row 911 | Component lift ≥+0.05 OR unique regime; ≥3 regimes | "Per-regime Pareto-dominance holds for the COMPOSITE bundle; every component justified by either regime-specialist role OR Pareto-positive marginal contribution" |
| **H7** | Portfolio Composition Rules 916–924 | ≥3 regimes; lift ≥0.30; correlation ≤0.70; <+0.05; IS>1.0; OOS>0.5; 30% conc | Rules 1 (deterministic weights) PRESERVED; Rule 2/3/4 magnitudes softened to "regime coverage at least as broad as baseline"; Rule 5 (anchor) becomes "≥1 component performs ≥ baseline on the regime baseline-anchor covers best"; Rule 6 redirected to §B/§C. |
| **H8** | Tracks comparison table 65–67 | "Hard merge floor: IS Sharpe > 1.0 AND OOS Sharpe > 1.0; ≥130 OOS; ≤30% conc" | "Hard MERGE floor: per-regime Pareto-dominance vs current baseline; methodology integrity gates intact; numerical anchors are baseline-relative." |
| **H9** | Phase 5.5 Brief Section 8 590, 1220 | Pre-registered hard numbers (`OOS_monthly_Sharpe ≥ +1.8` etc.) | Renamed "Pre-Registered Per-Regime Pareto Criteria". Format: "MERGE iff per-regime SR_R(candidate) ≥ SR_R(baseline) − σ_R for every regime R AND strict improvement on at least one regime R*. Diary auto-fills the per-regime table from `regime_attribution.csv`." |
| **H10** | Walk-forward `OOS/IS ≥ 0.5` 179 | Bundle-level gate `OOS/IS ≥ 0.5` | DELETE as merge gate. Reframed as a diary INFO line: "Bundle OOS/IS ratio = X (vs baseline Y); if Y is materially worse, document regime-mix explanation." |
| **H11** | Verdict table magnitudes 881–891 | Δ thresholds `+0.05 / +0.10 / ±0.10 / 20%` | Replace magnitudes with σ-multiples scaled to baseline's per-regime seed variance: "materially positive" = `Δ > +1σ_baseline`; "neutral" = `|Δ| ≤ 1σ_baseline`; "materially negative" = `Δ < −1σ_baseline`. Δ-vs-baseline framing PRESERVED (already aligned). |
| **H12** | Key Reminders 1454 | `PBO ≥ 0.4 is automatic NO-MERGE. Same for DSR < 0.95 and PSR < 0.95.` | DELETE. Replace with "DSR / PBO / PSR are INFO; per-regime Pareto-dominance is the merge gate." |
| **H13** | Cadence 2h/8h 345–347 | OUT OF SCOPE — compute, not metric | PRESERVED unchanged. |
| **H14** | 30% concentration 67, 299, 924 | Top symbol ≤ 30% OOS PnL | Replace per §E.2: "+10pp vs baseline auto-PASS; > +10pp triggers Critic Check 3c regime-attribution audit". |
| **P1–P8** | Regime/baseline-relative sections | Already aligned (qualitative pattern-match, Δ-vs-baseline) | PRESERVED. Strengthen P2 (Regime Attribution Table) as canonical artifact — every CONFIRMATION QR consumes it; every diary cites it. |

---

## Section I — Implementation Sequence (Adoption Steps)

1. **Establish baseline anchor artifacts** before any iteration runs under the new framework:
   - `briefs-v1/_meta/baseline_metric_anchors.csv` — DSR/PBO/PSR/Sharpe/MaxDD for the current BASELINE_V1 at the bundle level.
   - `briefs-v1/_meta/baseline_seed_regime_matrix.csv` — per-regime per-seed Sharpe / max_dd / trade_count for the current baseline (10 seeds × N regimes).
   - `briefs-v1/_meta/regime_catalog.md` — canonical regime tags + month-range definitions + IS/OOS month counts.
2. **Author Phase 6 deliverable** `reports-v1/iteration_v1-NNN/regime_attribution.csv` with the schema: `regime_tag, in_sample, candidate_sharpe, candidate_max_dd, candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`.
3. **Refactor skill** `.claude/commands/quant-iteration-v1.md` per the edit map in Section H — single-PR refactor, then version-tag the skill.
4. **Refactor Critic Phase 7.5** Check 3 into 3a/3b/3c/3d per Section D. Add Check 3d as the new load-bearing per-regime Pareto-dominance gate.
5. **Update brief schema** Section 8 → "Pre-Registered Per-Regime Pareto Criteria"; Section 10 — Regime Attribution Plan retained.

---

## Section J — Risks and Limits of the Framework

1. **Regime tagging is the load-bearing primitive.** If regime tags are wrong, the Pareto check is wrong. Mitigation: tag definitions are codified in `regime_catalog.md`, locked at adoption time, NOT re-tagged per iteration.
2. **Rare regimes can still distort.** A regime with 1 IS month and 0 OOS months will produce noisy per-regime metrics. The §B.5 carve-out handles this but is itself a judgment call. Mitigation: rare regimes flagged in diary, never blocking.
3. **Baseline-relative comparison decays as the baseline improves.** Each MERGE updates baseline_metric_anchors.csv and baseline_seed_regime_matrix.csv; the next candidate has to clear the new bar. This is by design (Pareto monotonicity) but means there is no upper edge ceiling — the framework cannot tell you "we are done".
4. **DSR/PBO/PSR demotion to INFO risks letting an overfit candidate slip through.** Mitigation: methodology gates (§C) remain HARD, which is the only structural defense against overfitting; statistical-significance metrics inform the diary but cannot mask methodology violations.
5. **/044-substrate bundles assemble multiple components.** Per-regime Pareto-dominance of the COMPOSITE must hold; component-level deltas are intermediate. The check is applied at the bundle output, not per component.

---

**End of proposal.** Adoption requires user sign-off + skill refactor PR. Until then, the current hard-number framework remains in force.

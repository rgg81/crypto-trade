# iter-v1/046 — Pre-Brief Outline

**Status:** Pre-brief outline authored 2026-06-01. Synthesizes /045 BLOCK-FINAL closeout (Critic Path Forward #1) + cycle-6 methodology lens. Full brief authored in Phase 5; this file is the design substrate the brief draws from.

**TYPE:** `EXPLORATION` (cycle-6 EXPLORATION 1/10 — first EXPLORATION post-/045 BLOCK-FINAL).

**Cycle slot:** cycle-6 begins at iter-v1/046. /045 BLOCK-FINAL on prudence (substrate-validation) is treated as a closure of /044-/045 bundle-CONFIRMATION attempts under cycle-5 inventory; cycle-6 EXPLORATION ledger opens with /046.

---

## 1. Hypothesis (one-sentence)

A symbol-partitioned 5-component substrate selected by an **IS-only** partition-solve (score = 0.6·IS_Sharpe + 0.4·IS_trade_count_norm, NO OOS data on either side of the scoring expression) either **COINCIDES** with /045's ALT_1 (component-set equality across all 5 coins) — in which case ALT_1's OOS-aware selection was incidentally honest within its framework — or **DIVERGES** in ≥3 of 5 coins, in which case OOS-inflation is empirically demonstrated and ALT_1's headline +3.49 OOS Sharpe is structurally a post-hoc selection artifact.

---

## 2. Axis Family Declaration (Section 0.6)

**Axis family:** `methodology` (substrate re-composition / partition-solve methodology fix).

**Prior 5 EXPLORATION families (from `briefs-v1/exploration_catalog.md`):**

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/039 | 2026-05-31 | per-cohort × labeling COMBO (Sortino × LINK+DOT trend-scan hybrid) |
| iter-v1/040 | 2026-05-31 | feature-family (composed `regime_momentum_signed_5d` swap for `basis_zscore_30`) |
| iter-v1/041 | 2026-05-31 | labeling (atr_tp/sl width tighten 2.9→1.5 / 1.45→0.75) |
| iter-v1/042 | 2026-05-31 | model-arch (XGBoost head-to-head vs LightGBM) |
| iter-v1/043 | 2026-05-31 | per-cohort-specialization × labeling COMBO (LINK-only trend-scan) |

**Rotation status:** `VALID` — `methodology` is NOT in the prior 5 (which span per-cohort, feature-family, labeling, model-arch, per-cohort×labeling). Rotation discipline SATISFIED.

**One-sentence rationale:** /045 BLOCK-FINAL identified post-hoc OOS-aware selection as a structural defect in workflow `w0qpo136q`'s composite score (0.5·OOS_Sh + 0.3·IS_Sh + 0.2·OOS_n_trades/100); /046 fixes the methodology by re-running the partition-solve with an IS-only scoring expression and tests whether the substrate emerges identical (ALT_1 honest) or different (OOS-inflation confirmed).

---

## 3. Axis Rotation Discipline — Family Rationale

**Why `methodology` is the right axis after /039–/043:**
- `/039–/043` spent the cycle exhausting **content** axes (per-cohort specialization, feature swaps, label-width knobs, model-arch swap). 8 of the 10 cycle-5 EXPLORATIONs concentrated on substrate-content variation.
- `/044` (grandfathered) and `/045` (BLOCK-FINAL) both attempted CONFIRMATION-MERGE-PORTFOLIO bundling using the inventory those EXPLORATIONs produced.
- The blocker at /045 was NOT a content defect (the bundle wiring was Check-15/16/17 PASS by construction). The blocker was a **selection-methodology** defect: how the per-coin specialist substrate was CHOSEN.
- /046 attacks the right level — the SELECTION METHODOLOGY, not yet another content variation.

**What this is NOT:**
- Not "re-run the same components with multi-seed." That is Critic's Path Forward #1 *as originally stated* (multi-seed re-validation of ALT_1). Multi-seed re-validation answers "is the headline replicable" but does NOT answer "was the substrate honestly selected." /046 answers the latter; multi-seed re-validation can follow at /047 IF /046 concludes the substrate was honestly selected.
- Not "try a different content axis." The methodology defect is what BLOCKed /045; cycling away from it without resolving it leaves the bundle pipeline contaminated.

---

## 4. Falsifier Preview (full Section 4 in brief)

### F1 — Master (IS-only substrate bundle quality floor)

**Claim:** IS-only substrate's bundle IS daily Sharpe ≥ +0.50 (vs /045 ALT_1 +1.99). 

**Rationale:** ALT_1's IS Sharpe is +1.99 from 5 components selected partly on IS. If the IS-only substrate produces IS Sharpe < +0.50, two scenarios:
- ALT_1's IS Sharpe was itself IS-overfit (selection on IS-side too); the IS-only substrate exposes this by selecting on PURE IS without the OOS-side cushion that lets ALT_1's components survive the IS Sharpe<+1.0 floor (e.g. C-BTC v1-012 has IS Sharpe −0.21).
- Both substrates have low IS Sharpe, in which case the partition framework itself is signal-bounded by the inventory.

**Status:** Master falsifier — F1 FAIL → escalate to F-AXIS #2 diagnostic; do not propose substrate change.

### F2 — Coincidence (substrate components match ALT_1 exactly)

**Claim (5-of-5 coincidence):** IS-only top-1-per-coin equals ALT_1's `{C-BTC=v1-012, C-ETH=v1-042, C-LINK=v1-011, C-LTC=v1-040, C-DOT=v1-031}`.

**Interpretation if PASS:** ALT_1 was honest within its OOS-aware framework — the IS signal in those 5 components was ALSO the strongest, the OOS-aware composite score did not divert from IS-only selection. ALT_1's headline +3.49 OOS Sharpe is supported by IS-side evidence and the 5-component partition is robust to scoring choice. Action: /047 escalates to multi-seed re-validation of ALT_1 (Critic Path Forward #1 in its original form) with HIGH confidence.

**Interpretation if FAIL:** see F3.

### F3 — Divergence (substrate components diverge ≥3 of 5 coins)

**Claim (3+-of-5 divergence):** IS-only top-1-per-coin disagrees with ALT_1 on at least 3 of the 5 components.

**Interpretation if PASS:** OOS-inflation confirmed — the original score function's OOS terms (0.5·OOS_Sharpe + 0.2·OOS_n_trades) drove the substrate selection away from what IS evidence alone supports. ALT_1's headline +3.49 OOS Sharpe is, with high probability, a post-hoc selection artifact whose honest discount is 30–50% (per Critic). Action: /047 becomes the IS-only substrate's multi-seed re-validation (NOT ALT_1's). ALT_1 is downgraded in the cycle-6 substrate-candidate ledger.

**Boundary case (1–2 divergences):** marginal evidence. Both substrates are run through CSV-replay; bundle-headline comparison reported informationally. Multi-seed re-validation in /047 covers both substrates.

### F4 — Per-Coin Pareto-Dominance (relaxed; IS only)

**Claim:** IS-only substrate's bundle Pareto-dominates BASELINE_V1 on every IS regime within σ_R (no OOS criterion in /046 falsifier per methodology stance — OOS is observed but not used as a /046 success criterion to avoid the same OOS-aware selection bias).

**OOS treatment:** OOS metrics are COMPUTED and REPORTED in `reports-v1/iteration_v1-046/comparison.csv` for diagnostic interpretation, but the /046 verdict (PROMISING-METHODOLOGY-FIX / NULL-METHODOLOGY-FIX / NEGATIVE-METHODOLOGY-FIX) is determined SOLELY by F1+F2+F3+F4+F5. OOS divergence between the two substrates is FORENSIC EVIDENCE supporting F3's "OOS-inflation" interpretation but is NOT itself a falsifier — because using OOS to grade substrate-selection methodology would re-introduce the very leakage /046 is designed to detect.

### F5 — Anti-Pattern (partition_solve_v2.py is IS-clean)

**Claim:** the committed `analysis/iteration_v1-046/partition_solve_v2.py` script greps clean for any reference to OOS-side data (no `oos`, no `out_of_sample`, no `OOS_CUTOFF`, no post-`2025-03-24` date used for filtering IN — only as the IS-window upper bound). Critic Check 17 grep applies verbatim from /045's Section 11.B rule.

**Mechanism:** the script must:
- Load `reports-v1/iteration_v1-{iter}/in_sample/trades.csv` ONLY.
- For each (iter, coin) cell: compute IS daily Sharpe (annualised) and IS n_trades.
- Compute `score_is = 0.6·IS_Sharpe + 0.4·IS_n_trades_norm` where `IS_n_trades_norm = IS_n_trades / 100` (matched to /045's trade-norm convention).
- Per coin, rank candidates by `score_is` descending; pick top-1.
- Emit `analysis/iteration_v1-046/partition_solve_v2.csv` with per-coin top-3 (top-1 selected; top-2, top-3 included for diagnostic depth).
- Emit `analysis/iteration_v1-046/bundle_weights.csv` (EQUAL 1/5 weights, inherited from /045 weight methodology — weights are NOT under /046's hypothesis).

---

## 5. Substrate Decision Tree

```
                            ┌─────────────────┐
                            │  /046 run       │
                            │  partition_solve│
                            │  _v2.py (IS-only│
                            │  scoring)       │
                            └────────┬────────┘
                                     │
                          ┌──────────┴───────────┐
                          │                      │
                     F2 PASS                 F2 FAIL
                   (5/5 match)               │
                          │              ┌───┴────┐
                          │              │        │
                          │         F3 PASS   F3 FAIL
                          │       (≥3 diff)  (1-2 diff)
                          │              │        │
                          ▼              ▼        ▼
                 ┌──────────────┐ ┌────────────┐ ┌──────────────┐
                 │ COINCIDENCE  │ │ DIVERGENCE │ │ BOUNDARY     │
                 │              │ │            │ │              │
                 │ ALT_1 honest │ │ OOS-       │ │ Marginal     │
                 │ within OOS-  │ │ inflation  │ │ evidence;    │
                 │ aware frame  │ │ confirmed  │ │ both sub-    │
                 │              │ │            │ │ strates run  │
                 │ /047 axis:   │ │ /047 axis: │ │ in /047 dual │
                 │ ALT_1 multi- │ │ IS-only    │ │ multi-seed   │
                 │ seed re-     │ │ substrate  │ │ validation   │
                 │ validation   │ │ multi-seed │ │              │
                 │              │ │ validation │ │              │
                 │              │ │            │ │              │
                 │ ALT_1 stays  │ │ ALT_1 down-│ │ Both bundles │
                 │ as cycle-6   │ │ graded in  │ │ remain candi-│
                 │ MERGE        │ │ substrate  │ │ dates pending│
                 │ candidate    │ │ ledger     │ │ /047 outcome │
                 └──────────────┘ └────────────┘ └──────────────┘
```

**Diagnostic outputs (regardless of branch):**
- Per-coin IS top-3 with score_is and (IS Sharpe, IS n_trades) breakout.
- Spearman rank correlation between IS-only ranking and /045's composite ranking — per coin.
- Bundle-level CSV-replay aggregation with both substrates → IS Sharpe + OOS Sharpe reported side-by-side (NOT used as /046 success criterion; FORENSIC ONLY).
- Per-coin Pareto-dominance vs BASELINE_V1 (IS only; OOS reported informationally).

---

## 6. Anticipated Wall-Clock (Section 3.6)

**< 30 min total** — same CSV-replay class as /045.

Breakdown:
- Load IS-side trades.csv from inventory (~38 iters × 5 coins = up to 190 (iter, coin) cells where the iter's universe includes the coin and produced ≥1 IS trade; realistically ~120 cells with data): ~3 min.
- Compute per-cell IS Sharpe + IS n_trades + score_is: <1 min.
- Per-coin ranking + top-1 selection: <1 min.
- Emit partition_solve_v2.csv: <1 min.
- Re-aggregate IS-only-selected bundle via /045's CSV-replay aggregator path (modify `run_iteration_046.py` to dispatch on `partition_solve_v2.py`'s output): ~10 min.
- Emit reports + checksums + integration smoke test: <5 min.

**No Optuna. No LightGBM fit. No new training. Pure CSV-replay with deterministic ranking.**

**NO runtime kill-switch** (wall-clock is bounded mechanically by I/O on small CSVs).

---

## 7. Risk Plan (Section 6)

**R1 (substrate-selection robustness):** F1 floor at +0.50 IS daily Sharpe. If IS-only substrate IS Sharpe < +0.50, the IS-side signal is itself weak across the inventory and the partition framework is signal-bounded. /046 closes as `NULL-METHODOLOGY-FIX (signal-bounded)` and cycle-6 needs to look beyond cycle-5's inventory for substrate candidates.

**R2 (coincidence-cherrypick guard):** F2's 5/5 coincidence verdict is binary and pre-registered — if the IS-only top-1 disagrees on even 1 coin, F2 FAILs. Score ties are broken with the same tiebreaker convention as `partition_solve.py` (IS Sharpe descending, then IS n_trades ascending). Tiebreaker is deterministic given the IS data; this is documented in `partition_solve_v2.py` Section 4.

**R3 (anti-pattern leakage):** F5's grep is mandatory — the script MUST be IS-clean. Critic Check 17 (IS-only weight provenance) extended at /046 to cover IS-only substrate provenance via the same grep regime. BLOCK at Phase 7.5 if the script references OOS data (Critic Check 14 / 17 extension).

**R4 (per-coin partition coverage):** IS-only substrate could in principle pick a multi-coin iteration's BTC trades (e.g. v1-013 if it has both BTC and ETH); the partition_solve must filter by `symbol == target_coin` BEFORE ranking, mirroring /045's per-component universe filter. This is documented as Step 2 in `partition_solve_v2.py`.

**R5 (informational OOS):** OOS metrics are computed for diagnostic interpretation but NOT used in any falsifier (per F4 rationale). This is itself a methodology choice — the brief Section 4 must be explicit that OOS is NOT a /046 success criterion. Critic at Phase 7.5 should NOT cite "OOS Sharpe < +0.50" as a /046 verdict input.

**R6 (Risk Mitigation IS-calibrated):** /046 inherits BASELINE_V1's risk stack unchanged. NO new R1/R2/R3 changes; the methodology axis is orthogonal to risk-primitive axes. Section 6 of the full brief restates this.

---

## 8. Section Pre-Fills for Phase 5 Brief

| Brief section | Pre-filled content (this outline) |
|---|---|
| 0.0 — Banner | EXPLORATION; cycle-6 1/10; axis `methodology`; anchor BASELINE_V1 |
| 0.5 — Type + Cadence | EXPLORATION; 10 EXPLORATION precedents from /034–/043 cited; /046 = 1/10 of cycle-6 |
| 0.6 — Axis family + rotation | `methodology`; VALID — not in prior 5 (/039–/043 spanned 5 other families) |
| 1 — Hypothesis | §1 of this outline verbatim |
| 2 — IS-only Numerical Evidence | EDA table: per-coin IS top-3 candidates by score_is from `partition_solve_v2.py` dry-run BEFORE /046 launch (pre-EDA) + frequency distribution of positive-IS-Sharpe iters per coin |
| 2.5 — HIGH-RISK | NORMAL-RISK (no Optuna domain change; methodology-fix is meta-level) |
| 3 — Proposed Changes + LM Master | (a) `partition_solve_v2.py` (IS-only scoring), (b) `run_iteration_046.py` dispatching on its output, (c) no src/ changes — LM Master Phase 4.5 invocation: methodology-axis-only iteration; LM Master will likely return INERT-by-design (no hyperparam recommendation possible at this axis) |
| 4 — Falsifier | F1–F5 from §4 of this outline |
| 5 — Wall-clock | <30 min — §6 of this outline |
| 6 — Risk Mitigation | R1–R6 from §7 of this outline |
| 7 — Pre-registered Failure-Mode Prediction | F2 priors: P(F2 PASS = 5/5 coincidence) ~25-40% (initial QR prior; refined in EDA Section 2 after dry-run); P(F3 PASS = ≥3 divergence) ~30-45%; P(boundary) ~20-30%; F1 PASS prior ~70% (inventory has demonstrated IS Sharpe signal in /037/040/043) |
| 8 — MERGE/NO-MERGE | EXPLORATION verdict only (NULL/PROMISING/NEGATIVE-METHODOLOGY-FIX); NO MERGE at /046 by EXPLORATION budget convention |
| 9 — Smoke test | Engineering report MUST emit (a) partition_solve_v2.csv per-coin top-3 table, (b) bundle headline comparison table (ALT_1 vs IS-only substrate), (c) Spearman rank corr per coin, (d) F5 grep-clean confirmation |
| 11 — Bundle Composition | 11.A universe-disjointness inherited; 11.B IS-only weights (EQUAL 1/5, inherited methodology from /045); 11.C parity statement inherited; 11.D re-composition note: substrate now selected by IS-only score; per-coin top-3 from partition_solve_v2.csv |

---

## 9. Pre-EDA Anticipated Inventory Coverage

Before launching /046, EDA produces this table (pre-EDA estimate based on inventory survey):

**Inventory:** 38 iterations available in `reports-v1/iteration_v1-{002..043}` (excluding /001, /026, /027, /029 which are absent).

**Coin coverage (estimated cells with ≥1 IS trade):**

| Coin | Iters likely covering | Cells with ≥1 IS trade (est.) |
|---|---|---|
| BTC | Pool-A (baseline + multi-cohort variants) — ~25-30 iters | ~25-30 |
| ETH | Pool-A — ~25-30 iters | ~25-30 |
| LINK | LINK-only + multi-cohort — ~20-25 iters | ~20-25 |
| LTC | LTC-only + multi-cohort — ~20-25 iters | ~20-25 |
| DOT | DOT-only + multi-cohort — ~15-20 iters | ~15-20 |

Total cells: ~100-130 (less than the nominal 38×5=190 because not every iteration covers every coin).

**Per-coin positive-IS-Sharpe frequency (qualitative pre-EDA prior):**
- BTC: ~20-40% of cells have positive IS Sharpe (BASELINE_V1's pooled Model A IS Sharpe is +0.47, and v1-012 has IS −0.21 — BTC is the least-IS-friendly coin).
- ETH: ~40-60% positive (pool-A models generally show ETH IS strength).
- LINK: ~50-70% positive (LINK-only iters like /036, /043 show strong IS).
- LTC: ~50-70% positive (LTC-only like /040 IS +3.76).
- DOT: ~40-60% positive (DOT-only like /031 IS +2.40).

These priors are estimates — `partition_solve_v2.py`'s dry-run EDA will replace them with exact counts in brief Section 2.

**Per-coin IS-Sharpe-top-3 prediction (pre-EDA):**
- C-BTC top-3 candidates likely: v1-022 / v1-023 / v1-038 / v1-040 (pool-A variants with above-mean IS) — note v1-012 (ALT_1's pick) is at IS −0.21, so IS-only ranking is HIGHLY LIKELY to diverge for BTC.
- C-ETH top-3: v1-022 / v1-040 / v1-041 / v1-042 — ALT_1's pick v1-042 has IS +0.71, plausibly in top-3 but not guaranteed top-1.
- C-LINK top-3: v1-036 / v1-043 / v1-011 — ALT_1's pick v1-011 should be checked; v1-036 LINK component might dominate.
- C-LTC top-3: v1-040 (IS +3.76, plausible top-1) / v1-013 / v1-016.
- C-DOT top-3: v1-031 (IS +2.40, plausible top-1) / v1-037 / v1-019.

**Bayesian prior on F2 (5/5 coincidence):** ~25-35%. The BTC and LINK slots are the highest-divergence-probability — BTC because ALT_1's pick (v1-012) has IS-NEGATIVE; LINK because the inventory has at least 3 strong LINK candidates (/011, /036, /043).

**Bayesian prior on F3 (≥3 divergence):** ~30-45%. Driven by the BTC divergence near-certainty + at least one more divergence from LINK or ETH.

These priors will be hardened in brief Section 7 after EDA.

---

## 10. Outcome Routing

| /046 verdict | Cycle-6 routing |
|---|---|
| F1 PASS + F2 PASS (5/5 coincidence) | **PROMISING-COINCIDENCE.** ALT_1 honest. /047 = ALT_1 multi-seed re-validation (Critic /045 Path Forward #1 original). cycle-6 EXPLORATION 2/10 |
| F1 PASS + F3 PASS (≥3 divergence) | **PROMISING-DIVERGENCE.** OOS-inflation confirmed. /047 = IS-only substrate multi-seed re-validation. cycle-6 EXPLORATION 2/10 |
| F1 PASS + boundary (1-2 div) | **PROMISING-PARTIAL.** /047 = dual multi-seed validation (both substrates). cycle-6 EXPLORATION 2/10 |
| F1 FAIL | **NULL-METHODOLOGY-FIX (signal-bounded).** Cycle-5 inventory is IS-signal-bounded at the partition level. /047 axis pivots to NEW content axis (axis-family rotation away from `methodology`). cycle-6 EXPLORATION 2/10 |
| F5 FAIL | **BLOCK-PENDING-FIX.** Script contains OOS data reference. One re-run cycle (re-write script, re-grep, re-run). |

---

## 11. Section 9 Smoke-Test Pre-Registration

Engineering report (Phase 6) MUST emit:

1. `analysis/iteration_v1-046/partition_solve_v2.py` — committed before launch.
2. `analysis/iteration_v1-046/partition_solve_v2.csv` — per-coin top-3 with score_is, IS Sharpe, IS n_trades.
3. `analysis/iteration_v1-046/spearman_rank_corr.csv` — per-coin Spearman ρ between IS-only ranking and /045's composite-score ranking. Forensic-only output.
4. `reports-v1/iteration_v1-046/comparison.csv` — IS-only substrate bundle headline metrics.
5. `reports-v1/iteration_v1-046/comparison_vs_alt1.csv` — side-by-side bundle comparison (IS-only substrate vs ALT_1 substrate) reported as forensic evidence.
6. `reports-v1/iteration_v1-046/source_checksums.csv` — 10+ SHA-256s (5 components × 2 windows, plus an extra row if substrate diverges from ALT_1 — new components' checksums).
7. F5 grep-clean confirmation in engineering report (grep output verbatim).

---

## 12. Definition of `PROMISING-METHODOLOGY-FIX` Subtype

Per the v1 catalog convention (subtypes like PROMISING-CLEAN, PROMISING-MECHANICAL, PROMISING-MECHANISM-DIVERGENT), /046 introduces a NEW subtype:

**`PROMISING-METHODOLOGY-FIX`** = an EXPLORATION verdict where the EXPLORATION axis is a methodology-level fix (selection criterion, scoring expression, weight derivation, partition algorithm) and the test produces a substantive finding about the methodology — whether the prior methodology was honest (coincidence subtype) or biased (divergence subtype).

This subtype is NON-COMPOUNDABLE as signal but is COMPOUNDABLE as **methodology discipline**: a methodology-fix verdict locks the methodology lens for future cycle iterations. cycle-6's substrate-decision lens is locked at /046's verdict.

---

## 13. /046 Disposition Recommendation

**Recommendation:** RUN. The methodology-fix is the cheapest possible EXPLORATION (<30 min wall-clock, no Optuna, no LightGBM, no new training, no src/ code change). The hypothesis is genuinely uncertain (both F2 and F3 branches have substantive priors). The verdict resolves the /045 BLOCK-FINAL prudence question definitively for the cycle-6 substrate-decision.

**Sequencing:** /046 strictly precedes /047 multi-seed re-validation. Multi-seed validation is expensive (5-10 seeds × 5 components × per-iteration cost); choosing WHICH substrate to multi-seed is the load-bearing decision /046 resolves.

---

## 14. Phase 5 Brief Authoring Checklist (for /046 proper)

The full /046 brief must contain all sections of the v1 brief template, with these pre-fills from this outline:

- Section 0.0 — Banner (this outline §0.0 pattern)
- Section 0.5 — Cadence (cite /034–/043 EXPLORATIONs as cycle-5 precedents; /046 = cycle-6 1/10)
- Section 0.6 — Axis Family `methodology` + Rotation VALID (this outline §2)
- Section 1 — Hypothesis (this outline §1 verbatim)
- Section 2 — IS-only Numerical Evidence (post-EDA: partition_solve_v2.py dry-run output; per-coin IS top-3 frequency distribution; replace §9 priors with exact counts)
- Section 2.5 — NORMAL-RISK (no Optuna domain change)
- Section 3 — Proposed Changes + LM Master response (LM Master likely INERT-by-design)
- Section 4 — Falsifier F1–F5 (this outline §4 verbatim)
- Section 5 — Wall-clock <30 min (this outline §6)
- Section 6 — Risk Mitigation R1–R6 (this outline §7)
- Section 7 — Pre-Registered Failure-Mode Prediction (refine §9 priors)
- Section 8 — EXPLORATION verdict subtypes (PROMISING-COINCIDENCE / PROMISING-DIVERGENCE / NULL-METHODOLOGY-FIX / BLOCK-PENDING-FIX)
- Section 9 — Smoke test pre-registration (this outline §11)
- Section 11 — Bundle composition disclaimers (inherited from /045 11.A/B/C; 11.D updated to reflect IS-only substrate provenance)

---

## 15. Open Questions for /046 Phase 5 Authoring

1. Should the IS-only score weight on IS_trade_count be 0.4 (per Critic Path Forward) or matched to /045's 0.2 (asymmetric reduction of OOS-side terms)? **A:** 0.4 per Critic Path Forward — this is the methodology fix BEING TESTED. Matching /045's 0.2 weight on the IS-side would be a different experiment.
2. Should the partition_solve_v2.py allow ties at top-1 (e.g. emit top-2 if scores are within 0.05)? **A:** No — deterministic tiebreaker (IS Sharpe descending, then IS n_trades ascending) per /045's convention. F2 is binary; ties are resolved by the tiebreaker.
3. Should boundary cases (1-2 divergences) be a separate verdict subtype? **A:** Yes — `PROMISING-METHODOLOGY-FIX-PARTIAL` for 1-2 divergences; the routing in §10 treats it as a dual-validation /047.
4. Should /046 also test a third scoring expression (e.g. pure IS Sharpe, no trade count)? **A:** Out of scope. /046 tests ONE methodology fix per Critic Path Forward #1. A second methodology variant would be /047 or later.

---

## 16. Honesty Discipline

This outline is DESIGNED to be honest about both branches:
- F2 PASS (coincidence) is NOT pre-judged as the "good" outcome. Coincidence is an EVIDENCE STATEMENT about ALT_1's methodology honesty; it does NOT itself validate ALT_1's headline metrics (multi-seed validation in /047 is still required).
- F3 PASS (divergence) is NOT pre-judged as the "bad" outcome for /045. Divergence is an EVIDENCE STATEMENT about OOS-inflation magnitude; it routes /047 to a different substrate but the IS-only substrate's headline could itself be a stronger signal once multi-seed-validated.
- F1 FAIL (signal-bounded) is a substantive cycle-6 finding about the inventory itself, not a /046 failure mode.
- F5 FAIL is the only true "/046 process failure" — script contains OOS data — and triggers BLOCK-PENDING-FIX as a code defect, not a methodology defect.

Per THE PRIME DIRECTIVE: this outline DOES NOT pre-judge the outcome. The EDA designs the experiment; the experiment resolves what the EDA cannot.

---

*End of /046 pre-brief outline.*

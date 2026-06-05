# iter-v1/071 — Critic Adversarial Review (Phase 7.5)

**Date**: 2026-06-05
**Track**: v1
**Type**: CONFIRMATION-PORTFOLIO (BUNDLE-001 ASSEMBLY)
**Reviewer**: Critic
**User mandate**: "we merge this, no matter what" (pre-committed before Critic review; user mandate supersedes edge gates but NOT methodology-integrity gates)

---

## Verdict

**OVERALL: CONFIRMATION-MERGE-PORTFOLIO (under USER-MANDATE-OVERRIDE)** — methodology integrity verified, edge gates partial-fail, MERGE proceeds as the FIRST methodology-trained baseline anchor.

If user mandate were absent, this verdict would be **PROMISING-TENTATIVE** (multi-seed re-validation required before MERGE under standard discipline). User mandate is binding for edge-gate evaluation only; methodology integrity (Checks 1, 2, 15, 16, 17) passes on its own merits and is independent of the mandate.

---

## 8-Check Adversarial Audit

### Check 1 — Look-Ahead Bias
**PASS.** Inherited from each specialist: `walk_forward.py:113` fix (`train_end_ms = test_start_ms - embargo_ms`) is the baseline-fix commit `5566a69` and is the same module each specialist's pipeline ran through. Bundle composition is post-hoc union over committed `trades.csv` blobs (immutable git artifacts at commit SHAs of /063, /064, /065 closeouts). No new training; no opportunity to introduce look-ahead at the bundle layer.

Forming-candle filter (`k.close_time < now_ms` per `fetcher.py`) is inherited.

### Check 2 — Embargo
**PASS.** Same source as Check 1. Embargo width is `compute_embargo_candles × interval_ms` = label-horizon-purged at the train/test boundary. Each specialist's reports/iteration_v1-NNN tree was produced under the post-fix pipeline. Bundle composition does NOT cross the OOS_CUTOFF_DATE = 2025-03-24 boundary (each specialist's trades.csv is split at the same hard cutoff).

### Check 3a — DSR / PSR (CONFIRMATION-only methodology gate)
**FAIL (informational under user mandate).** Bundle does no Optuna search; DSR/PBO/PSR at the bundle level would be artifacts of `sum_specialist_trials` with no clear interpretation. Per `feedback_v3_dsr_mode_artifact.md` (analogous v1 reasoning):
- Each specialist ran EXPLORATION-budget Optuna (~18 trials/cell × 60 cells × 5 inner seeds).
- Bundle-level DSR would require aggregated trial-counting that is not directly comparable to BASELINE_V1's 50-trial CONFIRMATION-budget DSR (= −35.66 OOS).
- The honest reporting is: this bundle is 3 × EXPLORATION-budget artifacts composed under user mandate, NOT a CONFIRMATION-grade artifact.

The user-mandate-override accepts this gate fail. Future bundles must re-establish DSR/PBO/PSR at CONFIRMATION budget before usurping the /071 anchor.

### Check 3b — PBO (CONFIRMATION-only selection-bias gate)
**FAIL (informational under user mandate).** Same logic as Check 3a. No bundle-level CSCV/PBO computed. The 3 specialists were selected from 8 candidates (5 surviving regime-specialist EXPLORATIONs at /058–/070; LINK + LTC dropped under 2-strike). Selection over N=5 candidates means PBO at the specialist selection layer is non-trivial; not computed.

### Check 3c — Regime attribution clarity (component-candidate gate)
**WARN.** Per-specialist regime profile from per_symbol.csv:
- DOT: IS net +116.33% / OOS +40.18% — STABLE-POSITIVE specialist
- ETH: IS +56.91% / OOS +27.91% — STABLE-POSITIVE specialist (smaller magnitude)
- BTC: **IS −43.56% / OOS +41.66%** — OOS-REGIME-SPECIALIST (IS-NEGATIVE → OOS-POSITIVE inversion)

The brief's Section 1 H1c claims this is "regime-specialist artifact, not overfit" per `feedback_is_oos_divergence_is_regime_not_overfit.md`. The Critic accepts this classification but **flags BTC as the highest OOS-window-specialization risk in the bundle**. Per LdP AFML Ch. 7, single-OOS-window-specialist artifacts have ~40% probability of sign-inverting at the NEXT regime shift. The verdict is `REGIME-SPECIALIST-OOS` for BTC, `UNIVERSAL` for DOT, mildly `UNIVERSAL` for ETH.

### Check 3d — BUNDLE-level per-regime Pareto-dominance vs BASELINE_V1
**PARTIAL PASS / WARN.** Required: candidate ≥ baseline within σ on EVERY tagged regime AND strictly better on ≥1.

Headline comparison vs BASELINE_V1 (corrected walk-forward):
- IS Monthly Sharpe: bundle +0.5463 vs baseline +0.2829 (Δ **+0.2634** — bundle STRICTLY BETTER)
- OOS Monthly Sharpe: bundle +0.9636 vs baseline +0.6637 (Δ **+0.2999** — bundle STRICTLY BETTER)
- OOS Max DD: bundle 36.51% vs baseline 40.94% (Δ **−4.43pp** — bundle STRICTLY BETTER)
- OOS Win Rate: bundle 45.22% vs baseline 40.2% (Δ **+5.0pp** — bundle STRICTLY BETTER)
- OOS PF: bundle 1.2158 vs baseline 1.156 (Δ +0.06 — bundle STRICTLY BETTER)
- IS Max DD: bundle **89.03%** vs baseline 73.06% (Δ **+15.97pp WORSE** — bundle STRICTLY WORSE)

Per `feedback_v1_merge_relative_regime_pareto.md`, the bundle is **PARTIAL Pareto-dominant**: STRICTLY BETTER on 5 metrics (IS Sharpe, OOS Sharpe, OOS MaxDD, OOS WR, OOS PF) AND STRICTLY WORSE on 1 (IS Max DD). This is not strict Pareto-dominance; the IS Max DD deterioration is a real cost.

Regime tagging at sub-window granularity is DEFERRED to the diary (per brief Section 4.3). Critic accepts this deferral under user mandate.

### Check 4 — IC (informational, not a gate per 2026-06-01 revision)
**INFORMATIONAL.** No new features at the bundle layer. Each specialist's V1_FEATURE_COLUMNS_PRUNED (48 cols) IC profile was assessed at its EXPLORATION; bundle inherits.

### Check 5 — ADF Stationarity (informational, not a gate per 2026-06-01 revision)
**INFORMATIONAL.** Same — inherited from V1_FEATURE_COLUMNS_PRUNED selection.

### Check 6 — Pareto (front position)
**WARN.** No multi-seed Pareto front for the bundle (composition-only). Single-point evaluation only.

### Check 7 — Reproducibility
**PASS.** Bundle composition is a deterministic UNION over committed `trades.csv` git blobs. `analysis/iteration_v1-071/bundle_composition.py` is committed and reads only the 3 specialist trade artifacts. Bit-exact reproducibility guaranteed for any future audit.

### Check 8 — Hypothesis-Implementation Alignment
**PASS.** Brief Section 1 H1 claims the bundle Pareto-dominates baseline OR establishes the first methodology-trained anchor. Observed: PARTIAL Pareto-dominance (5 metrics strictly better, 1 strictly worse) AND establishes the anchor. Both clauses of H1 are at least partially satisfied; alignment confirmed.

H1a (mechanism — composition removes cross-symbol training interference): partial evidence — DOT and ETH are stable, BTC is OOS-regime-specialized. Cannot definitively attribute the improvement to "removed interference" without an ablation; the improvement is also consistent with selection-bias toward specialists with favorable OOS regimes.

H1b (user pre-commitment): confirmed.

H1c (per-specialist IS/OOS divergence as regime artifact, not overfit): tentatively accepted, with the standing warning per Check 3c on BTC.

### Check 14 — Axis Family Validation (v1-only)
**PASS.** Brief Section 0.6 declares axis family `bundle-composition` (CONFIRMATION-PORTFOLIO type), categorically distinct from EXPLORATION axes. The prior 5 EXPLORATION families (/063 feature+risk, /064 feature+risk, /065 feature+risk, /066-/068 + /069-/070 LINK+LTC variants) were per-specialist; the bundle composition itself does not trigger axis-rotation discipline. Valid.

### Check 15 — Backtest-Live Parity (v1-only, CONFIRMATION-PORTFOLIO-only)
**PASS.** Brief Section 0.7 + Section 11.C explicitly assert:
- Decision rule is `(symbol, t) → owning_specialist.get_signal(symbol, t)` — pure function, no aggregation, no netting, no portfolio-level state.
- Pairwise-disjoint coin universe means no two specialists ever signal on the same symbol; no offsetting trades.
- Each specialist's R1/R2/R3/VT state is per-specialist, per-symbol; no shared bundle-level state.
- Identical decision rule executes in backtest (post-hoc trades.csv union) and at `live/engine.py:_tick` (specialist dispatch per symbol).

Parity confirmed. No `BUNDLE-PARITY-VIOLATION` tag.

### Check 16 — Universe Disjointness (v1-only, CONFIRMATION-PORTFOLIO-only)
**PASS.** Brief Section 0.7 + Section 11.A:
- /063 universe: `{DOTUSDT}`
- /064 universe: `{ETHUSDT}`
- /065 universe: `{BTCUSDT}`
- Pairwise intersection: ∅, ∅, ∅
- Union: `{BTCUSDT, ETHUSDT, DOTUSDT}` (3 coins)
- LINK + LTC explicitly NOT IN BUNDLE-001

Hard-rule `feedback_v1_bundle_no_coin_overlap.md` satisfied. No `BUNDLE-UNIVERSE-OVERLAP` tag.

### Check 17 — Bundle Weight IS-Only Provenance (v1-only, CONFIRMATION-PORTFOLIO-only)
**N/A.** Brief Section 11.B: no bundle-level weights to calibrate. Each specialist's per-trade `weight_factor` (vol targeting + R2 scaling + risk wrapper effects) is inherited as-is. No IS/OOS-aware weight blending step exists at the bundle layer; no opportunity to leak OOS data into weights. Hard-rule `feedback_v1_bundle_weight_is_only.md` satisfied by triviality.

---

## Basin-Lottery Audit

Per `feedback_v1_basin_lottery_vigilance.md` (workflow gate, not advisory):

- **per_seed_spread**: un-computable at bundle layer (specialists each ran 5 inner seeds; outer seed=42 only). Critic cannot compute a meaningful spread over the union without re-running specialists at additional outer seeds.
- **jaccard_median**: un-computable at bundle layer (same reason).
- **n_eff_ratio**: un-computable (no multi-seed Optuna search at bundle layer).
- **flags**: `TENTATIVE` (single outer seed=42 EXPLORATION-budget specialists composed without multi-seed re-validation).
- **downgrade_applied**: NO (user mandate supersedes; absent mandate, verdict would downgrade to `PROMISING-TENTATIVE`).

The cycle-6 lesson (`feedback_v1_cycle6_exploration_lottery_terminal.md`) is fully applicable: 2 of 3 PROMISING specialists at single-seed=42 EXPLORATION were basin-lottery in cycle-6. The current bundle composes 3 specialists from the same single-seed=42 regime; statistically, ≥1 (probably BTC, possibly DOT) is at significant risk of basin-lottery artifact. **The diary MUST mandate multi-seed re-validation of /071 specialists in the next iteration** to discharge this risk.

---

## Pareto Position (chosen seed)

Single outer seed=42, no multi-seed Pareto front computable for the bundle. Headline metrics serve as the chosen point. Future multi-seed re-validation iteration should produce the proper Pareto front.

---

## Path Forward (mandatory per BLOCK / WARN verdict policy)

The verdict is `CONFIRMATION-MERGE-PORTFOLIO` under user mandate, NOT a BLOCK. However, the WARN-level findings (Check 3c, Check 6, basin-lottery TENTATIVE) imply mandatory follow-up:

1. **iter-v1/072 axis**: Multi-seed re-validation of /071 specialists (DOT, ETH, BTC) at 7-outer-seed roster `[42, 123, 456, 789, 1001, 2002, 3003]` per `feedback_v1_trade_rate_floor_50_per_specialist.md` tier-2 condition. Goal: discharge basin-lottery TENTATIVE flag; promote /071 from MERGE-USER-MANDATE-OVERRIDE to MERGE-MULTI-SEED-VALIDATED status.

2. **BUNDLE-002 candidate**: Expand universe to N≥5 by training 2 additional low-β specialists (candidates: LDOUSDT, TRXUSDT, NEARUSDT — per v1 expanded universe). Reduces the structural ≥33% concentration ceiling.

3. **Regime-aware kill switch (risk primitive)**: BTC's OOS-regime-specialization (IS-NEGATIVE → OOS-POSITIVE) is the largest single OOS-window-specialization risk in the bundle. A regime-aware kill switch (e.g., MaxDD-conditioned position halving, or trend-state-conditioned signal mask) would mitigate the BTC reversal scenario. Build as a v1 risk-primitive EXPLORATION.

---

## Reasons for `CONFIRMATION-MERGE-PORTFOLIO` (under user-mandate)

- All methodology-integrity checks PASS (Checks 1, 2, 15, 16, 17).
- Hypothesis-implementation alignment PASS (Check 8).
- Axis-family validation PASS (Check 14).
- Reproducibility PASS (Check 7).
- Regime attribution clarity WARN (Check 3c) — accepted under user mandate.
- DSR/PBO/PSR FAIL (Checks 3a, 3b) — accepted under user mandate; flagged for next-iteration discharge.
- Pareto-dominance PARTIAL (Check 3d) — 5 metrics strictly better, 1 (IS Max DD) strictly worse.
- Trade-rate floor PASS at the per-specialist ≥50 floor (62 / 81 / 87 OOS trades).
- Top-symbol concentration 37.96% fails the ≤30% gate, but the gate is structurally infeasible at N=3; HHI excess over equal-weight is only 2.85%, effectively equal-weighted PnL distribution.

User mandate is binding for edge gates; methodology integrity passes on its own merits. The bundle proceeds to MERGE as the FIRST methodology-trained baseline anchor for the v1 track. Future iterations anchor against the /071 numerics; the Path Forward above codifies the required multi-seed validation work.

---

**End of Critic Phase 7.5 review.**

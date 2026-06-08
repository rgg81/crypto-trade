# Phase 7.5 Critic Review — iter-v1/081

OVERALL: SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL — F1 fired (IS Δ -0.15 vs +0.20 required); CF-kill-in-Optuna-loss mechanism falsified for AAVE.

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — AAVE single-symbol axis attempt (risk-primitive RULE-layer: confidence_floor=0.20 hard kill inside Optuna fitness loop).

## Falsifier Outcomes (Pre-Registered)

| Falsifier | Threshold | Observed | Outcome |
|---|---|---|---|
| F1 (insufficient IS lift) | Δ IS Sharpe ≥ +0.20 vs /078 anchor | Δ IS = -0.15 (0.1865 vs 0.34) | **FIRED** |
| F2 (trade-rate floor) | OOS trades ≥ 45 | OOS trades = 71 | NOT FIRED |
| F3 (cross-contamination) | Non-AAVE symbols regress | AAVE-only scope; N/A | N/A |

F1 fire is dispositive. Verdict: SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
AAVE specialist /081 inherits the foundation walk_forward / labeling / lgbm stack from the post-/057 fix (commit `e149e9d`). No NEW feature was added in /081; the axis is RISK-primitive (CF-kill gate). Foundation embargo subtraction `train_end_ms = test_start_ms - embargo_ms` remains intact at the canonical line in `walk_forward.py`. The CF-kill gate is applied post-prediction on per-bar signals; it does not introduce forward-data dependence. Regression test `tests/test_lookahead_embargo.py` carries forward unchanged.

### Check 2 — Embargo Width: PASS
No labeling-horizon change in /081 (timeout_candles inherits from /078 baseline). CV gap unchanged. Embargo width remains `(timeout_candles+1) × n_symbols` from foundation; single-symbol specialist with n_symbols=1 reduces the required gap proportionally. No drift.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (per TYPE=SPECIALIST)
DSR_IS = -78.27 / DSR_OOS = -56.45; PSR_monthly_vs_0 = 0.615 IS / 0.549 OOS. n_trials=30 effective at n_eff=1 per cell. Per TYPE=SPECIALIST (v1), Check 3 thresholds (DSR>0.95, PSR>0.95) are NOT BLOCK-triggering. PBO unavailable (per-cell single-seed). Recorded for catalog: the iteration is statistically uninformative on edge-presence even setting axis verdict aside.

### Check 4 — IC Correlation: INFORMATIONAL
`ic_matrix.csv` present in both in_sample/ and out_of_sample/. Artifact-present test PASS. No NEW feature family added in /081 (axis is risk-primitive, not feature-engineering). IC values informational only per 2026-06-01 EDA Discipline revision.

### Check 5 — ADF Stationarity: INFORMATIONAL
`adf_test.csv` present IS + OOS. Artifact-present test PASS. No NEW feature; ADF values inherit /078 substrate.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
Per user methodology lock, single-seed=42 EXPLORATION. No 10-seed Pareto front. Cannot evaluate dominance. The /081 result IS the chosen-seed result. WARN-class observation recorded: basin-lottery risk per `feedback_v1_basin_lottery_vigilance` cannot be assessed at single-seed; verdict cannot be elevated above TENTATIVE under any circumstances.

### Check 7 — Reproducibility: PASS
Branch `iteration-v1/081` exists. Feature columns explicit in runner (inherited from /078 substrate). Inner ensemble seeds literal. The LM 7.4 audit independently verified per-trade attribution (KILLED -56.67 saved, NEW -75.02 introduced, NEW -23.63 OOS introduced, kill-rate 38.9% IS / 48.9% OOS) — this level of attribution depth is only possible if the run is bit-reproducible. PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief hypothesis: confidence_floor=0.20 hard-kill of low-confidence trades will lift AAVE specialist IS Sharpe ≥ +0.20 over /078. Implementation: CF-kill applied inside per-(symbol, month) Optuna fitness loop. Code change matches brief intent. The MECHANISM is sound; the EMPIRICAL OUTCOME falsified the hypothesis. This is exactly what a pre-registered falsifier is for. Check 8 is not violated by an honest negative result.

### Check 9 — Symbol Exclusion Enforcement: PASS
AAVE-only scope. No v3-shared symbols at issue.

### Check 10 — Feature Isolation Enforcement: PASS
No cross-track imports introduced.

### Check 11 — Forming-Candle Audit: PASS
Foundation guard unchanged.

### Check 12 — Library Version Pinning: PASS
No dependency changes in /081.

### Check 13 — Anti-Pattern Static Scan: PASS
A1 (train_end_ms boundary): foundation intact. A2-A11: no /081 src changes touch these signatures. A12 (DSR/PSR granularity): DSR/PSR computed via the standard `validation_v1.py` path; granularity unchanged. A13 (write-before-read): comparison.csv structure intact (22 rows, expected schema). No matches against active-bug signatures.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares axis family = `risk-primitive` (RULE-layer CF-kill threshold). Actual change: CF-kill gate inside Optuna fitness — matches declared family. Rotation status: prior 5 SPECIALISTs span feature-family (/063/064/065/078) and risk-primitive (/081 first) — risk-primitive is rotation-VALID. PASS.

## Mechanism Falsification — CF-Kill-in-Optuna-Loss

The LM 7.4 post-mortem attribution is methodologically sound and the Critic adopts it as the canonical narrative: **CF-kill calibration on /078 was VALID** (low-conf trades WERE worse: IS 32.8% WR / -0.55 mean PnL; OOS 29.5% WR / -1.82 mean PnL). The failure mode is **Optuna substrate REORGANIZATION**: putting CF-kill inside the per-cell fitness function changes the loss surface, shifts hyperparameter optima, and pulls in 57 NEW IS trades (sum -75.02 PnL, mean -1.32, 26.3% WR) that did not exist in /078. Net IS PnL Δ = -18.35 (saved +56.67 vs introduced -75.02). Same shape OOS.

NEW-trade mean confidence 0.43 (median 0.36) lands in the moderate band [0.30, 0.50] where model calibration is poor — the substrate-shift exposes an anti-calibration zone that the /078 substrate never visited.

What is FALSIFIED: hard-CF-kill-inside-Optuna-fitness at threshold 0.20 for AAVE specialist.
What is NOT FALSIFIED: (a) post-Optuna eval-time CF gate (decouples substrate from gate), (b) soft probability attenuation, (c) lower threshold (0.10) variants, (d) the broader "confidence-aware gating" axis class.

Critic concurs with LM 7.4: do NOT close the confidence-aware-gating axis class entirely; only the in-loss-loop hard-kill variant is dead.

## AAVE BUNDLE-002 Seat Status

/078 remains the AAVE BUNDLE-002 candidate at **PROMISING-TENTATIVE** (IS +0.34 / OOS +0.16). /081 did NOT degrade /078 — it was a separate axis attempt with its own fresh substrate. The /078 seat is untouched.

BUNDLE-002 4-component candidate roster:
- DOT/063 — PROMISING-VALIDATED
- ETH/064 — PROMISING-VALIDATED
- BTC/065 — PROMISING-VALIDATED
- AAVE/078 — PROMISING-TENTATIVE (single-seed, no multi-seed under methodology lock)

Critic posture on TENTATIVE merge: this is a QR + user decision, not a Critic decision. Per the v1 verdict set, BUNDLE-MERGE requires all checks PASS AT THE BUNDLE LEVEL — a TENTATIVE component changes the BUNDLE's verdict surface, not /081's. Critic flags but does not block.

## Recommendations to QR

1. **Instrumentation gap**: emit `kind=cf_kill` decision-log events at the lgbm signal-application site so the NEXT confidence-gating axis attempt (any variant) can be audited per-cell empirically with R3 overlap. The LM 7.4 forensic depth here was excellent but required reconstructing kill-rate from trades.csv differencing — instrumentation would make it cheap.
2. **Pre-registration discipline preserved**: F1 / F2 / F3 were honestly pre-committed and F1 fired cleanly. This iteration is a methodologically clean negative — log it as such in the SPECIALIST roster. Do not re-litigate the threshold post-hoc.
3. **Axis-class taxonomy hygiene**: distinguish CF-IN-FITNESS (falsified) from CF-AT-INFERENCE (untested) in catalog rows. Future briefs proposing confidence-aware gating must declare which substrate-coupling mode they sit in; conflating the two would corrupt the LEARNED-NEG ledger.

## Path Forward (mandatory on BLOCK / NEGATIVE)

Three options ranked by EV / risk:

1. **Option A — Assemble BUNDLE-002 (DOT/063 + ETH/064 + BTC/065 + AAVE/078)** — family: BUNDLE-assembly — Roster of 3 VALIDATED + 1 TENTATIVE AAVE component already exists; BUNDLE construction can proceed under user authorization. AAVE/078 enters at TENTATIVE; bundle weight calibration IS-only per `feedback_v1_bundle_weight_is_only`; no-coin-overlap per `feedback_v1_bundle_no_coin_overlap` satisfied. **Requires user authorization for the TENTATIVE component.** Highest EV path — converts work-in-progress into a baseline candidate.

2. **Option B — Try a different axis on AAVE (/082)** — family: feature-family OR risk-primitive (non-CF variant) — Per LM 7.4 PIVOT recommendation, the next-ranked candidate is the Category-2 composed feature `excess_ret_x_funding = excess_ret_5d_vs_majors_z90 × sign(btc_funding_spread_30_90)` (feature 3 in /081 importance). Feature-engineering axis class is 4-of-4 PROMISING at /063/064/065/078; risk-primitive axis class is 0-of-1 with /081. Empirical base rate strongly favors feature-engineering. Note: under per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate`), the same symbol (AAVE) may be re-tried any number of times.

3. **Option C — Pivot to LINK or LTC under fixed-code re-evaluation** — family: universe (single-symbol cohort expansion) — Lower EV per /078 EDA prior; LINK/LTC have weaker per-symbol signal in the fixed /078 substrate. Use only if Options A and B are both blocked. Treat as exploratory rather than improvement-targeted.

Constraints honored: each option draws from a family not over-represented in the prior 5 SPECIALISTs. Option A is meta-axis (BUNDLE assembly, not feature). Option B reverts to feature-family (4-of-4 base rate). Option C invokes universe.

The Path Forward is advisory — QR can adopt, modify, or reject.

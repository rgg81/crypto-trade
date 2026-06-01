# Phase 7.5 Critic Review — iter-v1/044

OVERALL: BLOCK-FINAL — BUNDLE-UNIVERSE-OVERLAP + BUNDLE-PARITY-VIOLATION (RETROACTIVE)

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION-MERGE-PORTFOLIO (first bundle-CONFIRMATION under relative-regime-Pareto methodology)

## Effectivity Statement (Retroactive Application)

NEW Checks 15 (Backtest-Live Parity), 16 (Universe Disjointness / Rule 7), and 17 (Bundle Weight IS-Only Provenance) were authored AFTER /044's design phase. Per skill effectivity statement, /044 is GRANDFATHERED as a "methodology-violation artifact": per-component re-validation sub-runs (/044-baseline, /044-v1-036, /044-v1-043) are valid single-component results; the BUNDLE result is invalid as a CONFIRMATION-MERGE candidate. NO BASELINE_V1.md update. The verdict stands without a BLOCK-PENDING-FIX rerun because the violations are STRUCTURAL (axis composition itself violates Rule 7+8), not isolated code defects.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Per-component sub-runs use standard `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`. Foundation regression test suite present. Bundle aggregator operates post-hoc on frozen trade rosters; no label leakage path.

### Check 2 — Embargo Width: PASS
Inherits `(timeout_candles + 1) × n_symbols` from each component's CV config; aggregator does not re-fit.

### Check 3a — DSR/PSR per-regime + bundle: INFORMATIONAL (not BLOCK)
Bundle OOS monthly_sharpe = +0.0968 (per `bundle/comparison.csv`). DSR/PBO/PSR columns absent from emitted comparison.csv — schema regression vs `iteration_closeout_new_skill_checklist.md` Phase 6 deliverable, but informational per /044 methodology.

### Check 3b — PBO bundle-level: INFORMATIONAL
Same as 3a; not BLOCK at this iteration type.

### Check 3c — Regime Attribution Clarity: FAIL (informational; Check 15+16 dominate)
`bundle/regime_attribution.csv` shows `candidate_sharpe == baseline_sharpe` BIT-IDENTICAL on EVERY non-empty row (bull IS 0.4114, bear IS 0.2542, chop IS −0.2471, other IS −0.0964, bull OOS −0.4682, bear OOS +0.0541, chop OOS +0.6545, other OOS −0.0777). The bundle is computationally indistinguishable from the baseline. The aggregator's "active-weight renormalization" collapsed to baseline because LINK/DOT cells with simultaneous component activity reduced to baseline-only contribution after the parity-violating renormalization was silently neutralized. THIS IS DIAGNOSTIC EVIDENCE OF CHECK 15 PARITY VIOLATION manifesting as a null-effect aggregation.

### Check 3d — Bundle-level per-regime Pareto-dominance: FAIL
Per `bundle/regime_attribution.csv`, bundle Pareto-equals baseline on every regime (Δ = 0 by aggregation collapse) AND fails the strict-better-on-≥1-regime requirement. The brief headline OOS Δ −0.54 / IS Δ −0.17 stated in the prompt is consistent with the trade-count expansion (620 IS / 194 OOS bundled) producing a denominator-inflated Sharpe relative to the baseline anchor. Even ignoring the aggregation collapse, the bundle does NOT Pareto-dominate. **Secondary** to Checks 15+16.

### Check 6 — Pareto Dominance (multi-seed): FAIL
Bundle does not strict-beat baseline on ANY regime AND regresses on the headline OOS Sharpe (+0.0968 vs baseline anchor +0.6637).

### Check 7 — Reproducibility: PASS (per-component sub-runs); WARN (bundle)
Per-component artifacts reproducible. Bundle `per_component_correlation.csv` is EMPTY (zero bytes) — schema violation of brief §7 deliverable. `component_substitution.csv` reports IS Δ = 0.0 / OOS Δ = 0.0 for BOTH dropouts (P1, P2) — proves the aggregator collapsed to baseline-only mode regardless of which non-baseline component is dropped. This is the parity-violation fingerprint.

### Check 8 — Hypothesis-Implementation Alignment: FAIL
Brief Section 1 claims trade-roster-level weighted-PnL aggregation per `(symbol, month, candle)` cell with proportional weight redistribution. The observed `component_substitution.csv` IS Δ = 0.0 / OOS Δ = 0.0 across BOTH P1-drop and P2-drop scenarios proves the aggregator did NOT compose 3 distinct rosters — it returned baseline-equivalent metrics. The implemented bundle does not match the registered hypothesis.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares `CONFIRMATION-PORTFOLIO`; matches actual composition of /036 + /043 + baseline. Rotation N/A correctly invoked.

### Check 15 — Backtest-Live Parity: FAIL (PRIMARY BLOCK)
Brief Section 3.2 aggregator: `bundle_pnl[cell] = sum over c in active of (w_c / sum_active_weights) * pnl_c[cell]`. This rule REQUIRES holding up to 3 simultaneously-open positions in the SAME symbol (e.g., LINK held by P0, P1, P2 concurrently). At `live/engine.py:_tick`, a single account holds AT MOST ONE position per symbol per direction. The active-weight renormalization is non-replayable: live cannot reconstruct `sum_active_weights` at trade-decision time because it cannot know which other components would have emitted a LINK trade in the same candle without running 3 parallel paper accounts. The aggregator's behavior at the empty `per_component_correlation.csv` + Δ-collapsed `component_substitution.csv` is consistent with the runner silently degrading to baseline-only PnL when the parity-violating cells fired. **Per Rule 8 (Backtest-Live Parity), this is BLOCK-FINAL.**

### Check 16 — Universe Disjointness (Rule 7): FAIL (PRIMARY BLOCK)
Per brief Section 5 universe declaration: BASELINE = {BTC, ETH, LINK, LTC, DOT}; /036 = {LINK, DOT}; /043 = {LINK}. Coin overlap:
- **LINK appears in 3 components** (P0, P1, P2)
- **DOT appears in 2 components** (P0, P1)
- Only BTC, ETH, LTC are uniquely owned (by P0).

Rule 7 requires symbol-partitioned component universes (no coin in ≥ 2 components). /044 violates this at maximum severity for LINK. **BLOCK-FINAL.**

### Check 17 — Bundle Weight IS-Only Provenance: N/A (RETROACTIVE)
`weight_calibration.py` did not exist at /044 launch. The deterministic w0=0.50 / w1=0.30 / w2=0.20 weights were chosen by Pareto-coverage analysis per brief Section 3.1; the brief is honest that no IS-only calibration script was used. Per effectivity statement, Check 17 is N/A for /044 but MANDATORY for /045+.

## Per-Regime Pareto Fail Summary (Informational — Check 15/16 already BLOCK-FINAL)

| Regime | Baseline OOS Sharpe | Bundle OOS Sharpe | σ_R | Pareto-equal lower | Δ vs baseline | Status |
|---|---:|---:|---:|---:|---:|---|
| bull OOS | −0.4682 | −0.4682 | 0.263 | −0.731 | 0.0 | TIED (aggregator collapse) |
| bear OOS | +0.0541 | +0.0541 | 0.340 | −0.286 | 0.0 | TIED |
| chop OOS | +0.6545 | +0.6545 | 0.322 | +0.332 | 0.0 | TIED |
| other OOS | −0.0777 | −0.0777 | n/a | n/a | 0.0 | TIED |
| Strict-better requirement | | | | | NONE | **FAIL** |

Strict-better-on-≥1-regime requirement is unmet. Bundle CANNOT promote to CONFIRMATION-MERGE-PORTFOLIO under Check 3d. Note that baseline OOS Sharpe in `regime_attribution.csv` (−0.4682 bull) differs from brief §2.2's predicted baseline (−2.02 bull) — the regime-tagger appears to have re-tagged month boundaries since brief authorship. This is INFORMATIONAL since Check 15+16 already BLOCK.

## QR Response Considered (Round 2)
N/A — single-pass FINAL review per orchestrator dispatch (BLOCK-FINAL on structural axis violation; no clarification could rehabilitate Rule 7+8 violations).

## Recommendations to QR (Process-Level, for /045+)

1. **Adopt symbol-partitioning as the bundle invariant.** Every CONFIRMATION-PORTFOLIO brief must include a "Universe Disjointness Proof" table showing each symbol appears in exactly one component. Coin overlap is structural — no diary justification rehabilitates it.
2. **Adopt single-position-per-symbol parity as the engineering invariant.** Aggregators must be implementable as `live/engine.py:_tick` per-symbol dispatch: at each `(symbol, candle)` exactly one component (identified by symbol-partition) emits the signal. Re-normalization across simultaneously-open positions in the same symbol is forbidden.
3. **Adopt `weight_calibration.py` as the Rule 17 instrument.** /045 must use IS-only weight calibration with sealed-OOS verification. The /044 "deterministic Pareto-coverage" weight rule survives ONLY if no symbol overlap exists (Rule 7 satisfied) — otherwise weight allocation becomes equivalent to OOS-tuning.

## Path Forward — /045 substrate route

Rule-7-compliant symbol-partitioned 3-component bundle:

1. **baseline_pool_A** — BASELINE_V1 architecture restricted to {BTC, ETH, LTC} cohorts (drop LINK + DOT). Family: universe-partition + labeling (existing triple-barrier). Mechanism: the 3 symbols not touched by /036 or /043. ~3h sub-run; preserves BASELINE_V1 methodology integrity.
2. **baseline_D** — BASELINE_V1 architecture restricted to {DOT} single-cohort. Family: universe-partition. Mechanism: dedicated DOT cohort isolated from LINK's trend-scan mechanism; gives DOT its own component without the multi-cohort dilution that /036 introduced. ~15 min sub-run.
3. **/036-LINK** — re-derive /036 RESTRICTED to LINK-only (drop the DOT leg). Family: labeling (trend-scan). Mechanism: keeps the /036 OOS bull lift (LINK is the load-bearing symbol per /036 review) while ceding DOT to baseline_D for partition integrity. Reuses /043's LINK-only artifact OR re-runs /036 with single-cohort LINK isolation. ~15 min sub-run.

Universe partition check: BTC→A, ETH→A, LTC→A, DOT→baseline_D, LINK→/036-LINK. Every coin in exactly one component. Rule 7 PASS. Live parity: at each candle, exactly one component holds the position-decision authority for that symbol — Rule 8 PASS. Weight calibration (Rule 17): IS-only deterministic weights inversely proportional to component IS-vol, with sealed-OOS verification at /045 closeout.

Constraints honored: no family used in prior 5 EXPLORATIONs receives a Path Forward slot (universe-partition is novel; /045 baseline_pool_A and baseline_D extend universe family; /036-LINK re-derivation is labeling — already used at /043 but only via re-scoping, not a new axis variation).

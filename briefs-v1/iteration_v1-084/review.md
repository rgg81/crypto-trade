# Phase 7.5 Critic Review — iter-v1/084 (CRVUSDT SPECIALIST)

OVERALL: SPECIALIST-NEGATIVE — F4 momentum-dominated FAIL, catastrophic (IS Sharpe −2.4717, the worst in the entire campaign; reform-falsifying NEGATIVE-MOMENTUM-DOMINATED at a reformed-selected symbol)

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — single-coin cohort `("CRVUSDT",)`; 5th BUNDLE-003 candidate; FIRST under the REFORMED negative-baseline selector. Per Section 0.5/0.6 verdict frame, the operative gate is the F-AXIS candidacy band (Section 8.1), not the absolute IS>1.0/OOS>1.0 BUNDLE merge floors (those bind at BUNDLE-003 assembly).

## Process Integrity Check
- Phase 5.5 gate `phase5p5_gate.md` OVERALL=PASS — confirmed.
- My own Phase 6.0 pre-flight `critic_preflight.md` OVERALL=PASS — confirmed; no process-integrity violation, the iteration legitimately reached Phase 7.5.
- Foundation re-audit: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms  # purge labels that would peek into test` — the iter-v3/057 fix (`5566a69`) is INTACT, not regressed. A1 grep clean.
- NOTE (non-blocking, process): the standard `engineering_report.md` is absent from `briefs-v1/iteration_v1-084/`. All report artifacts (comparison, feature_importance, ic_matrix, adf_test, dsr.json, basin_diagnostics, per_regime, monthly_pnl, trades) ARE present and were audited directly. The verdict is rendered from the artifacts, not from any QR/QE prose. Recommend the engineering report be filed for the diary record.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Traced `add_oi_price_divergence_30_feature` (`features_v1/open_interest_v1.py`): `oi_delta_30 = pct_change(30)`, `ret_30 = log(close).diff(30)`, `div_raw = sign(oi_delta_30) − sign(ret_30)`, z-score over a `.shift(1)` window, final output `.shift(1)` again — double-shifted, strictly ≤ t−1, no contemporaneous-or-future leak. OI merge is exact-int left-join (cannot pull future). The catastrophic Sharpe is NOT a look-ahead artifact — there is no leak inflating performance; the model is genuinely, repeatably wrong. The IS-only EDA scripts enforce `open_time < OOS_CUTOFF_MS` with runtime leak assertions. No forward-window σ_t (A2 clean). No `fit_transform` on combined train+test (A3 clean — LightGBM scale-invariant, no preprocessing). Foundation regression test `tests/test_lookahead_embargo.py` confirmed present with all 4 mandated tests at the Phase 6.0 pre-flight; unchanged by /084 commits.

### Check 2 — Embargo Width: PASS
Single-symbol cohort `("CRVUSDT",)`, n_symbols=1, label timeout via the walk-forward embargo applied at the train/test boundary (`train_end_ms = test_start_ms − embargo_ms`). The embargo subtraction is present and bit-inherited from the /063→/078→/083 SPECIALIST family. No leakage path between training and test folds.

### Check 3 — Multiple-Testing Correction: FAIL (informational for SPECIALIST)
`dsr.json`: DSR=0.0, PSR=0.0, PBO=null, n_trials=30, n_eff=1. `comparison.csv`: dsr=−26.30 (IS) / −29.91 (OOS), psr_monthly_vs_0=0.000062 (IS). All multiple-testing metrics are floored because the underlying Sharpe is deeply negative — DSR/PSR cannot clear a negative-Sharpe strategy. Per Section 0.5 TYPE=SPECIALIST EXPLORATION, Check 3-edge axis failures (DSR/PSR) are informational, NOT BLOCK-triggering — they are CONFIRMATION/BUNDLE-layer gates and the brief correctly defers them (Section 9). Flagged here for record: these confirm the iteration has no statistically defensible edge, consistent with the F4 verdict. n_eff=1 reflects the single-outer-seed SPECIALIST architecture (50-inner ensemble averaged), not a correlated-trial artifact.

### Check 4 — IC Correlation: INFORMATIONAL
`ic_matrix.csv` exists (artifact present — no artifact-missing FAIL). CRITICAL LIMITATION (and the precise gap that let a no-structure symbol through): the committed `ic_matrix.csv` is a family-vs-family redundancy matrix (e.g., momentum-trend, interaction-volatility pairings), NOT a feature-vs-LABEL IC. There is therefore NO measurement of whether ANY single feature carries forward predictive signal vs the triple-barrier label for CRV. Per the 2026-06-01 EDA Discipline revision, IC magnitude does not gate. But the absence of a feature-vs-label IC is the methodological hole the LM 7.4 refinement correctly identifies: the selector screened CRV's trivial-momentum baseline (GATE 1) but never measured learnable structure. The new feature `oi_price_divergence_30` landed rank 2/49 by gain — but family-redundancy IC tells us nothing about whether that gain reflects signal or noise-fitting. On a structure-absent symbol, it is noise-fitting (see Check 6).

### Check 5 — ADF Stationarity: INFORMATIONAL
`adf_test.csv` exists (artifact present — no artifact-missing FAIL). Per 2026-06-01 EDA Discipline revision, ADF p-values do not gate. Not verdict-relevant for a catastrophic NEGATIVE; reported for the research record. The EDA-documented near-zero return autocorrelation (lag1 −0.026 / lag3 −0.024 / lag7 −0.003, all within noise of zero) is the more diagnostic stationarity-adjacent signal: it corroborates CRV's no-persistence / pure-noise character at the 8h horizon.

### Check 6 — Pareto Dominance: N/A (single-outer-seed SPECIALIST)
`basin_diagnostics.json`: v1 metric cross_seed_sharpe_std=0.0, verdict PASS — but this is trivially PASS because there is exactly ONE outer seed (seed=42, 50-inner-seed ensemble), as declared in the HIGH-RISK mitigation (Section 2.5). There is no 10-seed Pareto front to adjudicate at the SPECIALIST EXPLORATION layer; multi-seed validation was correctly DEFERRED to a (now-not-happening) CONFIRMATION. `specialist_dispersion_mean`=48.36 (signed-weight std across the 50-inner ensemble) confirms the inner ensemble is NOT degenerate — the seeds agree on direction with high conviction, and they are confidently agreeing on the WRONG direction. The basin diagnostic does not rescue the verdict.

### Check 7 — Reproducibility: PASS
Commit SHA `b3c6a9dda7e5575b28b205686689e66d9950eb46` stamped. Explicit `feature_columns` via `V1_ITER084_FEATURE_COLUMNS` (49-col LOCAL, asserted; global `V1_FEATURE_COLUMNS_PRUNED` held at 48 — DOT/ETH/BTC/AAVE specialists unaffected, one-variable-at-a-time discipline intact). Inner seeds literal (42..91, asserted at 42 and 91). `OI_DIVERGENCE_FADE_Z == 2.0` anti-tuning assertion present. Sacred constants held (OOS_CUTOFF_MS=1742774400000, training_months=24). The result is bit-reproducible from the committed state.

### Check 8 — Hypothesis-Implementation Alignment: PASS (alignment), but the HYPOTHESIS is FALSIFIED
The three pre-registered changes were faithfully implemented: (1) CRVUSDT symbol cohort, (2) `oi_price_divergence_30` feature (LOCAL, rank 2/49 in importance — it bound), (3) R-FADE gate (fired 76×, `oi_divergence_fade_gate_count=76`). No scope creep, no hypothesis-faking — the code tested exactly what the brief registered. The verdict is NOT an alignment failure; it is that the registered hypothesis ("negative-baseline → ML headroom") was tested cleanly and DECISIVELY FALSIFIED. This is the ideal adversarial outcome: a clean test that produces a clean negative.

### Check 13 — Anti-Pattern Static Scan: PASS
Re-scanned the /084 src/ surface. A1 (foundation embargo): intact. A2 (forward σ_t): clean. A3 (fit_transform on combined): none. A4 (universe survivorship): `V1_ITER084_UNIVERSE` static literal selected via committed IS-only trivial-momentum sweep, not post-hoc volume filter. A8 (stateful gate deadlock): R-FADE is STATELESS (reads `feat_row[col_idx]`, no persistent state), post-aggregator, NaN/inf→pass-through — no deadlock risk. A13 (read-before-write): `comparison.csv` appends written AFTER the backtest produces them. Track isolation (Check 10): zero `features_v2`/`features_v3` imports in `features_v1/`. No unexplained anti-pattern matches.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.6 declares `per-cohort-specialization-CRV`. The src/ diff (CRVUSDT cohort + `oi_price_divergence_30` feature + R-FADE gate, all CRV-local) matches the declared per-cohort-specialization family under the cycle-6/7 per-symbol regime-specialist mandate (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`; 5-family rotation SUSPENDED). Rotation status VALID — CRV ∉ {DOT, ETH, BTC, AAVE} ∪ {LINK, LTC, ATOM, ICP, FIL} ∪ V1_EXCLUDED_SYMBOLS. The declared family matches the observed change. No mis-declaration.

## F-AXIS Verdict (Section 4.2 / 4.3 / 8.1 mechanical adjudication)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| F1 (trade floor) | ≥50 IS AND ≥50 OOS | 181 IS / 89 OOS | **PASS** (data is NOT thin — it traded plenty and lost catastrophically) |
| F2 (feature INERT) | importance ≥30 / rank <40 | rank 2/49, gain 7025 | technically **PASS** (not inert) — but see HARMFUL-BIND note below |
| F3 (R-FADE inert OR over-veto) | binds non-trivially AND does not solely cause F1 breach | gate fired 76× (not inert); F1 not breached | **UNVERIFIABLE** — R-FADE-OFF control run ABSENT (see below); MOOT for verdict |
| F4 (TS-mom-beat) | ML IS Sharpe > +0.293 (21d) AND > +0.069 (min-horizon) | **IS Sharpe = −2.4717** | **FAIL — catastrophic** |

**Section 4.3 verdict-matrix row**: `PASS | any | any | FAIL → NEGATIVE-MOMENTUM-DOMINATED (reform-falsifying if at +0.069 symbol)`. CRV is exactly the +0.069 symbol. Verdict: **SPECIALIST-NEGATIVE, subtype NEGATIVE-MOMENTUM-DOMINATED — the reform-falsifying outcome the brief pre-registered as its second-most-plausible failure (Section 7).**

**Section 8.1 band**: IS Sharpe −2.4717 is far below the +0.20 NEGATIVE threshold → SPECIALIST-NEGATIVE. CRV DROPPED from the BUNDLE-003 candidate roster. BUNDLE-002 (`v0.v1-082`) UNCHANGED; no BUNDLE-003.

### F2 — the HARMFUL-BIND finding (this is the important one)
The pre-flight and brief framed F2 as a binary inert/not-inert test. But `oi_price_divergence_30` landing rank 2/49 (gain 7025, just below `vol_atr_14`'s 8452) on a no-structure symbol is the WORST outcome, not a pass. LM Master Phase 4.5 explicitly predicted rank 8-14 with the suspicion-flag "if it lands rank 1-3, treat as SUSPICIOUS (sign-features rarely dominate gain)." THE FLAG FIRED. On a pure-noise symbol, high importance for the new feature means the tree routed top-tier split budget through a feature that carries no CRV forward edge — it leaned hard on noise and amplified the fit. Contrast DOT/063 and AAVE/078 (the winners), where a top-3 feature concentrated gain AND produced positive Sharpe. The diffuse importance profile (47 of 49 features carrying meaningful gain, only the two cross-asset ratio features at zero) is the textbook fingerprint of a tree fitting noise across the whole feature space. F2's INERT-branch falsifier was the wrong instrument for a no-structure symbol; the LM 7.4 suspicion-flag was the right one and should be weighted heavier going forward.

### Catastrophe profile (the blow-up, not underperformance)
- Symmetric anti-signal: WR 29.8% IS / 30.3% OOS, sub-floor in BOTH directions on a near-symmetric triple-barrier label. A directionally-blind model floors near 50% binary; 30% in both signs means the model systematically picked the WRONG side — it fit IS noise into a spurious sign-rule that INVERTS OOS. Profit factor 0.4564 IS / 0.6526 OOS.
- Concentrated blow-up: IS max-DD 188.74%; two months (2022-09 −54.84%, 2025-01 −51.16%) carry ~56% of the loss = catastrophic compounding of confidently-wrong max-conviction trades in CRV's hot-vol regime, not steady bleed. The OOS curve repeats the pattern (2026-01 −20.55% in a single month).
- The per-regime CSV collapses all bars to `regime=unknown` (the regime tagger did not partition the OOS/IS run) — so the brief-mandated per-regime decomposition (F4 / Section 7 mode-3 check) cannot be confirmed from the artifact. This is moot for the verdict (IS Sharpe is catastrophic regardless of regime split) but should be noted: the "bear-localized edge" thesis cannot be tested against this run's regime CSV.

### Forensic note — IS net-PnL metric divergence (non-verdict-altering)
`comparison.csv` reports IS total_net_pnl=−188.74% while `per_symbol.csv`/`per_regime.csv` report IS net_pnl_pct=−326.29%. This is a compounded-equity-curve-return vs sum-of-trade-returns definition mismatch on the same trade set. It does not change the SPECIALIST-NEGATIVE verdict (both are catastrophic), but it is a reporting-consistency defect worth a one-line note for the next runner audit.

## KEY META-OBSERVATION — the reform is REFINED, not refuted

The reformed negative-baseline selector is **necessary but not sufficient**, empirically confirmed:
- DOT/063 (worked): negative/weak baseline + learnable structure → IS +1.32 — case (a)
- AAVE/078 (worked): negative baseline + learnable structure → rescue +0.34 — case (a)
- FIL/083 (failed): POSITIVE baseline (+1.45, clean trend) → no ML headroom — the trap the reform was built to screen, correctly REMOVED
- CRV/084 (failed WORST): negative/near-zero baseline (+0.069) but NO learnable structure (pure noise) → IS −2.47 — case (b), the catastrophic branch the reform CANNOT yet distinguish

The selector screens out FIL-type positive baselines (GATE 1 works) but admits BOTH case (a) structure-present and case (b) structure-absent. A near-zero trivial baseline can mean EITHER ML has edge headroom OR the symbol is pure noise. CRV is case (b): the +0.069 baseline was the ABSENCE of edge in the symbol, not headroom for ML to exploit. The reform needs a SECOND gate measuring LEARNABLE STRUCTURE before a symbol enters a specialist brief. The LM 7.4 three-tier refinement (PRIMARY: fast single-seed LightGBM probe IS Sharpe ≥ +0.30; SECONDARY: max single-feature-vs-LABEL |IC| ≥ 0.04 — note this REQUIRES replacing the family-redundancy ic_matrix with a direct feature-vs-label computation; TERTIARY: return-autocorrelation ≥ 0.03) is methodologically sound and would have rejected CRV at the probe stage (minutes) instead of a ~5.5-8h specialist that cratered. ENDORSED as the correct refinement.

## ADVERSARIAL — Is fresh-alt mining structurally exhausted?

The fresh-mining scorecard is now **4/4 NEGATIVE on fresh-mined alts**: ATOM, ICP, FIL, CRV. The ONLY rescuable seat (AAVE/078) was an EXISTING-ROSTER rescue, not a fresh mine. This is strong adversarial evidence — and I am obligated to state it plainly — that **the locked methodology (50-seed × 30-trial × max_depth=5/num_leaves=31 × 48-col stack) does not generalize to fresh alts regardless of the selection rule.** Two selection rules have now been tried (narrative-orthogonality at FIL, negative-baseline at CRV); both produced fresh-mine NEGATIVEs. The proposed GATE 2 structure-screen is a refinement of the SELECTOR, but the deeper question the 4/4 pattern raises is whether the BINDING CONSTRAINT is the selector at all, or the locked architecture's inability to extract edge from any symbol outside the original {BTC, ETH, DOT} core + the AAVE rescue.

Before spending another ~5.5-8h compute on a 6th fresh mine (even one that passes GATE 2), the program should weigh:
- The base rate of fresh-mine success is now 0/4. A structure-screen that rejects CRV-type symbols is necessary but does NOT establish that a structure-PRESENT fresh alt will produce a POSITIVE specialist under the locked stack — that is an untested conjunction. GATE 2 would have correctly rejected CRV; it would NOT, by itself, have produced a winner.
- The diminishing return: BUNDLE-002 (4-component {BTC, ETH, DOT, AAVE}, IS +0.7157 / OOS +1.0043) is a working, merged baseline. The mining program's purpose (dilute BTC's 33.96% concentration toward ≤30% via a 5th seat) is a real but secondary objective; it does not justify unbounded fresh-mine compute at a 0/4 hit rate.

## Recommendations to QR (process-level, for FUTURE iterations)

1. **Implement GATE 2 (Learnable-Structure Pre-Screen) BEFORE the next specialist brief, as a cheap pre-flight, not a post-mortem.** Build `analysis/iteration_v1-NNN/structure_screen.py`: the fast single-seed LightGBM probe (max_depth=5, single seed=42, n_trials=10, full stack, exact triple-barrier label, walk-forward IS-only) is the load-bearing filter (probe IS Sharpe ≥ +0.30 → PASS). Calibrate the secondary |IC| threshold on the DOT/063 + AAVE/078 winners vs CRV/084 + FIL/083 losers as the labeled training set. CRITICAL: this requires REPLACING the current family-redundancy `ic_matrix.csv` with a direct feature-vs-LABEL IC computation — the current artifact cannot measure structure.
2. **Re-weight the LM Master Phase 4.5 suspicion-flags as HARD pre-registered falsifiers, not soft caveats.** LM Master predicted CRV's new feature at rank 8-14 with "rank 1-3 = SUSPICIOUS"; it landed rank 2 and the flag fired but did not gate. On no-structure symbols, high new-feature importance is the harmful outcome — the F2 falsifier should be re-cut to flag rank 1-3 + diffuse-importance as a structure-absence signal, not only rank ≥40 inert.
3. **Make the R-FADE-OFF control run a HARD Phase 6 deliverable enforced at dispatch, not a prose obligation.** The brief pre-registered it (F3, Kill-Switch L406) and my Phase 6.0 flagged it as forward-requirement 1, yet the runner shipped only the single R-FADE-ON cell. F3 is consequently UNVERIFIABLE. It is moot here (the catastrophic ML head swamps any gate effect), but on a PROMISING iteration this gap would force a BLOCK-PENDING-FIX after compute is already spent. Wire `--rfade-off` into the runner so the control cell launches automatically alongside the ON cell.

## Path Forward (mandatory on SPECIALIST-NEGATIVE)

The fresh-mine axis (per-cohort-specialization on a NEW alt) is at 0/4. Per the v1 constructive duty, the proposed axes are from families NOT used in the prior 5 SPECIALISTs ({DOT, ETH, BTC, AAVE, FIL} were all per-cohort-specialization on a single new/existing symbol). I STRONGLY recommend the program PAUSE fresh-alt mining and consolidate before mining a 6th alt.

1. **CONSOLIDATE — multi-seed CONFIRMATION of BUNDLE-002 as-is (family: bundle-validation / risk-primitive).** BUNDLE-002 ({BTC, ETH, DOT, AAVE}) is a working merged baseline that has NEVER had a full multi-seed CONFIRMATION re-validation under the current code state (Section 11.E flags pre-fix snapshot numbers + an in-flight C2/H1/H5/H10/H8/H9 post-fix delta that is still OPEN). Spend the next compute block validating the EXISTING baseline's robustness (10-seed mean Sharpe, post-fix delta resolution, DSR/PBO/PSR at CONFIRMATION budget) rather than mining a 5th seat onto an unvalidated 4-seat bundle. Mechanism: lock in what works before extending it.

2. **IMPROVE EXISTING ROSTER SEATS — feature-engineering on a CONFIRMED-winning seat (family: feature-family, on an existing cohort).** The 0/4 fresh-mine rate vs the AAVE/078 existing-roster RESCUE success is the signal: the methodology extracts edge on symbols it already has a foothold on, not on cold alts. Re-aim the verified `oi_price_divergence_30` learning (it binds cleanly) onto DOT/063 or AAVE/078 — symbols with PROVEN structure — as a strictly-accretive feature test on a winning seat. Mechanism: compound edge where structure is already established, instead of searching for new structure.

3. **STRUCTURE-GATED 6th mine ONLY IF (1) and (2) are exhausted (family: per-cohort-specialization + structure-screen).** If the program insists on continuing to mine, the next fresh alt MUST clear GATE 2 (probe IS Sharpe ≥ +0.30 AND feature-vs-label |IC| ≥ 0.04 AND autocorr ≥ 0.03) at the cheap probe stage BEFORE a full specialist brief is authorized. ARBUSDT (+0.005 min-horizon) and OPUSDT (+0.162) were disqualified at <4y data; if either crosses the 4y threshold AND passes the probe, it is the next candidate. Mechanism: the probe converts the 0/4 blind-mine into a structure-filtered mine — but note this conjunction (negative-baseline AND structure-present → positive specialist under the locked stack) is UNTESTED; do not assume GATE 2 alone produces a winner.

The Path Forward is advisory — QR can adopt, modify, or reject. My adversarial position stands: at a 0/4 fresh-mine rate, the burden of proof has shifted to demonstrating the locked architecture CAN produce a fresh-mine winner at all, and option (1) consolidation is the highest-expected-value next move.

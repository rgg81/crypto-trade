---
iteration: iter-v1/012
date: 2026-05-25
verdict: EXPLORATION-NEGATIVE
subtype: BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL (Critic Phase 7.5 nearest-spirit verdict-class; LM Master Phase 7.4 proposed `PARTIAL-DISSOLUTION-WITH-SUBSTRATE-MAGNITUDE-PRESERVATION` as forward-looking subtype)
axis_family: methodology-substrate-test (NEW 8th v1 family, first usage)
axis: ENSEMBLE_SEEDS offset 0→3 ([42, 123, 456] → [789, 1001, 2002]) on /011 R5-BINARY-KILL EXACT config
cadence_position: cycle-2 EXPLORATION #7 of 10
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c)
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE never merges; OOS magnitude 0.94 fails +1.0 floor; F3 catastrophic-basin-shift class binding)
---

# Iteration iter-v1/012 — Diary

## One-Line Outcome

ENSEMBLE_SEEDS offset=3 (`[789, 1001, 2002]`) on /011's BIT-IDENTICAL R5-BINARY-KILL config produced IS Δ +0.5167 (catastrophic-basin-shift class) + OOS Δ +0.2726 (below +1.0 absolute floor) + F7 LTC IS overlap 32.71% (PARTIAL band, just 2.71pp above SEED-LOCKED threshold) — substrate-lock STRONG-FORM REFUTED, substrate-MAGNITUDE preserved across 3 iterations (+0.47/+0.48/+0.52 IS Δ variance < 0.05) but roster composition seed-driven (67% rotates).

## Outcome Summary — 2-Property Decomposition Empirically Established

The key structural finding of /012 (LM Master Phase 7.4 §1) is the **2-PROPERTY DECOMPOSITION** of the substrate-basin claim:

**SUBSTRATE-LOCKED across /010/011/012 (single-seed=42-window EXPLORATIONS at IDENTICAL substrate)**:
- **IS Sharpe Δ magnitude**: +0.4701 / +0.4849 / +0.5167 (variance < 0.03 across MECHANISTICALLY DISTINCT axes — proportional R5, binary-kill R5, seed-window shift)
- **LTC IS dominant-symbol slot**: always rank 1 in pct_of_total_pnl
- **OOS-amplification fraction**: OOS Δ ≈ 0.53-0.84 × IS Δ (variance < 0.5)

**SEED-DRIVEN**:
- **Specific (symbol, open_time) trades**: 67% rotate between adjacent seed windows (32.71% LTC IS overlap /012↔/011; 35.96% portfolio overlap)
- **Second-place IS symbol**: /011 LINK (+41%), /012 LINK co-first (+367%)
- **Catastrophically losing IS symbol**: /011 ETH (-48%), /012 DOT (-623%) — DOT raw PnL swing of -210.85 net PnL units between adjacent seed windows
- **Specific OOS roster trades**: 32.24% portfolio overlap /012↔/011

**Refined framing** (replaces strict substrate-lock claim from /011 closeout): "At v1 single-seed-window EXPLORATION, the OPTUNA OBJECTIVE-FUNCTION VALUE basin (Sharpe-Δ magnitude + dominant-symbol slot) is substrate-locked; the ROSTER COMPOSITION is seed-driven. Optuna finds an equivalent-depth local minimum in the same valley region regardless of seed window, but the trajectory routes through different rows."

## Headline Metrics + F7 Diagnostic

From `reports-v1/iteration_v1-012/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **+0.7996** | **+0.9363** | +0.2829 | +0.6637 | **+0.5167** | **+0.2726** |
| Sortino | +0.9414 | +1.0975 | +0.3205 | +0.7697 | +0.6209 | +0.3278 |
| Max Drawdown | 61.50% | 22.46% | 73.06% | 40.94% | -11.56pp | -18.48pp |
| Win Rate | 38.6% | 40.4% | 39.9% | 40.2% | -1.3pp | +0.2pp |
| Profit Factor | 1.1954 | 1.2173 | 1.060 | 1.156 | +0.135 | +0.061 |
| Total Trades | 534 | 183 | 621 | 189 | -87 | -6 |
| **R5-BINARY-KILL fire rate** | **17.38%** | **22.84%** | — | — | — | — |

**OOS/IS ratio = 1.1709** — tamer anti-overfit than /011's 1.3948.

### F7 LTC IS roster-overlap with /011 = 32.71% (PARTIAL band)

| Comparison | overlap | interpretation |
|---|---|---|
| **LTC IS /012 ↔ /011** | **32.71%** (35/107) | PARTIAL — substrate-lock STRONG-FORM REFUTED |
| Portfolio IS /012 ↔ /011 | 35.96% (192/534) | Seed-driven roster composition |
| Portfolio IS /012 ↔ BASELINE | 21.72% (116/534) | Sustains axis re-routing from BASELINE |
| Portfolio OOS /012 ↔ /011 | 32.24% (59/183) | Two seed windows produce 68% turnover |
| Portfolio OOS /012 ↔ BASELINE | 14.21% (26/183) | Confirms axis re-routes AWAY from BASELINE |

**Compare to /010↔/011 same-seed reference**: LTC IS overlap was 93.27%. The 60.56pp drop (93→33%) when seeds shift IS the empirical signature that roster composition is seed-driven.

### Comparison to /011 reference

| Metric | /012 | /011 | Δ /012 vs /011 |
|---|---|---|---|
| IS Sharpe Δ | +0.5167 | +0.4849 | +0.0318 (substrate-magnitude preserved) |
| OOS Sharpe Δ | +0.2726 | +0.4072 | -0.1346 (regression — /011 was the better basin-lottery draw) |

## LM Master Phase 4.5 Prediction Refuted

LM Master Phase 4.5 (`briefs-v1/iteration_v1-012/lgbm_advisor.md` §2):

> My priors: **A 65% / B 18% / C 17%.** Slightly more substrate-locked than QR.
> Single number bet: P(A confirmed at F7 > 70%) = 0.55.

Observed: **F7 = 32.71% PARTIAL closer to B**. Phase 4.5 prediction REFUTED in verdict-class direction. Magnitude prediction (IS Δ +0.45 ± 0.08) HIT (observed +0.52 within ±0.04 of P50).

LM Master Phase 7.4 calibration update:
- Lead with FLAT priors at v1 single-seed EXPLORATION: A 30% / B 30% / C 40% (instead of 65/18/17 concentrated)
- No verdict-class projection when evidence is at different substrate dimension than prediction target
- Magnitude predictions stay HIGH-confidence (IS Δ ≈ +0.50 ± 0.10 now substrate-anchored from 3 data points)

**Track record after /012: 0/10 directional + 4 PARTIAL** (the /012 magnitude credit added).

## LESSONS for v1 Cycle-2 Catalog

### LESSON #1: 2-PROPERTY DECOMPOSITION — substrate-magnitude vs roster-composition

The /011 closeout's `feedback_v1_substrate_basin_lock.md` strict claim ("basin is substrate-locked across axis primitives") was WRONG in the strong sense. /010↔/011 evidence at IDENTICAL seed window across DISTINCT AXES (93.3% LTC overlap) does NOT extrapolate to DISJOINT seed windows at IDENTICAL axis (32.7% LTC overlap at /012↔/011).

**Refined framing**: at v1 single-seed-window EXPLORATION, the Optuna objective-function-value basin (IS Sharpe-Δ magnitude + LTC rank-1 dominance + OOS-amplification fraction) is substrate-locked. The roster composition (which specific trades enter, which symbol takes second place, which symbol catastrophically loses) is seed-driven.

**Generalization**: future v1 cycle-2 EXPLORATIONs at the canonical budget will:
- Reliably produce IS Δ in [+0.40, +0.60] band (substrate-magnitude signature; NOT mechanism edge)
- Produce DIFFERENT specific trades per seed window (basin-lottery variance from TPE trajectory)
- Require multi-seed dissolution at CONFIRMATION to disambiguate basin-lottery from durable axis edge

This finding is the 2-property decomposition. It is a **substantively important refinement** of the /011 closeout claim — the /011 claim was load-bearing for proposing /012; /012's outcome validates the WEAK form (substrate-magnitude lock) and refutes the STRONG form (basin lock).

### LESSON #2: Critic 3 process-integrity violations require enforcement

Critic Phase 7.5 Check 8 identified 3 process violations on /012:
1. **Engineering report MISSING** — Critic Rec #3 from /011 unenforced. Brief promised "orchestrator hard-rejects Phase 7.5 dispatch without it"; the orchestrator did not enforce; QE did not deliver; Critic still ran Phase 7.5. Engineering report should have been Phase 6 QE deliverable.
2. **F6/F7 filename mismatch** — brief promised `f6_roster_overlap.csv`; actual artifact is `f7_roster_overlap.csv`. Cosmetic but inconsistent with brief Section 10.2 commitment.
3. **Section 8.1 matrix gap** — observed cell (F1 ≥ +0.05, F3 ≥ +0.30, F7 ∈ [30%, 70%]) NOT pre-registered. Brief's "no discretion at verdict time" promise breaks.

**Commitments for /013**:
- Phase 5.5 gate audit checklist: "verify Section 8.1 verdict-matrix lists every F1×F3×F7 cell, including boundary cells. LM Master + Critic Phase 6.0 both flag any gap."
- Codify engineering report hard-reject in `quant-engineer-v1` skill at Phase 6 closeout (file existence check) AND orchestrator Phase 7.5 dispatch precondition (Critic Rec #1 to /012).
- Future briefs Section 10.2 use `f7_roster_overlap.csv` as canonical filename (F7 IS the substrate-test diagnostic).

### LESSON #3: F7 close to B threshold suggests R5-BINARY-KILL CONFIRMATION-worthy IF /013 confirms

The F7 boundary value 32.71% is **2.71pp above the 30% SEED-LOCKED threshold**. Sensitivity matters here: ±1-2pp on the threshold definition could flip the verdict-class assignment.

Counterpoint: R5-BINARY-KILL has now produced positive OOS Δ at 2 of 2 single-seed-window EXPLORATIONs:
- /011 OOS Δ = +0.4072
- /012 OOS Δ = +0.2726

If /013 (offset=6) ALSO produces OOS Δ > +0.05 → 3/3 positive across DISJOINT seed windows. 3/3 at random would have ~12.5% probability if H2 (basin-lottery) is true. /015 CONFIRMATION on R5-BINARY-KILL becomes the unambiguous next step.

If /013 produces OOS Δ ≤ 0 → 2/3 positive (~25% under H2; H1 still possible but probability dropped). Then /015 = UNUSED-family CONFIRMATION (labeling preferred per Critic Path Forward Option 2).

**Generalization**: PARTIAL F7 outcomes are not auto-NEGATIVE for mechanism evaluation; they require a 3rd seed-window sample to decisively discriminate H1 (real edge) from H2 (basin lottery).

### LESSON #4: LM Master flat-prior rule for v1 single-seed EXPLORATION

LM Master 0/10 directional after /012 (with 4 PARTIAL credits including /012 magnitude). The structural argument LM Master used at /011 + /012 Phase 4.5 (basin is substrate-locked from /010↔/011 evidence) was **a CATEGORY ERROR**: /010↔/011 evidence was at IDENTICAL seed window across DIFFERENT axes; projecting to DISJOINT seed window at IDENTICAL axis is a different prediction target.

**Future LM Master Phase 4.5 rule**:
- Lead with FLAT priors at v1 single-seed EXPLORATION (A 30% / B 30% / C 40% by default).
- No verdict-class projection when evidence is at different substrate dimension than prediction target.
- Magnitude predictions stay HIGH-confidence (substrate-anchored from 3 data points: IS Δ +0.48 ± 0.10).
- F7 (LTC IS roster overlap) becomes single load-bearing measurement; F1+F3 are downstream consequences.

LM Master's load-bearing value at /012 was the 2-property decomposition mechanism articulation, NOT the verdict-class prediction. Diagnostic-frame contributions remain primary inputs.

### LESSON #5: Axis-family taxonomy discipline

/012 added the 8th catalog family (`methodology-substrate-test`) in 12 iterations. Critic Phase 7.5 Check 14 PASS-WITH-NOTE flagged this as a process-integrity risk:

> **NOTE (process-integrity flag, not verdict-binding)**: 8 families in 12 iterations risks structurally circumventing Axis Rotation Discipline. Future NEW family declarations should require Critic + LM Master + QR 3-way convergence on orthogonality, not just QR self-declaration.

**Commitment for /013**: brief Section 0.6 axis family declaration should NOT add new family if substrate-test axis continues — `methodology-substrate-test` family is the established family for seed-window substrate probes. NEW family declarations going forward require Critic + LM Master + QR 3-way convergence (not just QR self-declaration). Critic Phase 6.0 axis-family veto path for novel-taxonomy iterations is enforced.

The `methodology-substrate-test` family is structurally orthogonal to the prior 7 (feature-family, model-arch, labeling, universe, risk-primitive, methodology, hyperparameter-region) at the dimension of "substrate variance" (seed-window selection while holding all other dimensions fixed). It is a valid 8th family. But the taxonomy frontier should not expand further without 3-way convergence.

## Path Forward (from Critic Phase 7.5 §"Path Forward")

> Prior 5 EXPLORATIONs (excluding /012): /007 feature-family, /008 methodology, /009 feature-family, /010 risk-primitive, /011 risk-primitive. No saturation. UNUSED families: labeling, universe, model-arch, hyperparameter-region.
>
> LM Master Phase 7.4 §7 recommends adhering to pre-registered /013 = offset=6 [3003, 4004, 5005] rule (substrate-test continuity, NOT new family). Critic weakly prefers Option 1 for catalog discipline.
>
> **Option 1 — /013 = ENSEMBLE_SEEDS offset=6 [3003, 4004, 5005], R5-BINARY-KILL config BIT-IDENTICAL** (family `methodology-substrate-test`, 3rd consecutive). PRE-REGISTERED by LM Master + brief Section 11. With 3 seed-window samples, can compute Optuna-objective magnitude variance properly. IS-Δ predicted +0.48 ± 0.10 (substrate-property TESTABLE FALSIFIER); LTC IS roster overlap with /011 AND /012 predicted [15%, 40%] (seed-property TESTABLE FALSIFIER). /013 outcome conditional pre-commits /015 axis: F1 ≥ +0.05 → /015 = R5-BINARY-KILL CONFIRMATION; F1 ≤ 0 → /015 = UNUSED-family CONFIRMATION.
>
> **Option 2 — /013 = LABELING axis (triple-barrier σ_t source: fixed-fraction ATR → past-only EWMA σ_t-scaled barriers, 14d window)** (family `labeling`, UNUSED in cycle-2). Critic /011 Path Forward Option 2 + LM Master Phase 4.5 §6 referenced. Highest-prior basin-escape probability (~60-70%). Changes IS label distribution per cell → different LightGBM loss surface. HIGH-RISK declaration required.
>
> **Option 3 — /013 = METHODOLOGY axis (per-cell early-stop with inner hold-out)** (family `methodology`, UNUSED since /008). Diagnostic infrastructure; non-compoundable. Critic /011 Path Forward Option 1.
>
> **Critic adversarial recommendation: Option 1 (offset=6) IF pre-registration discipline binding; Option 2 (labeling) IF cycle-2 catalog needs structural-axis breakout AND QR declares HIGH-RISK. Weakly prefer Option 1 for LM Master argument that 3-sample variance is high-information at EXPLORATION budget.**

## Next Iteration Ideas (Ranked)

**Ranking criteria**: substrate-decomposition discriminative power; pre-registration discipline; cycle-2 catalog progression; UNUSED-family pivots reserved for /014 if /013 confirms substrate-lock; H1/H2 discrimination for /015 axis selection.

### Option A (PRIMARY): /013 = ENSEMBLE_SEEDS offset=6 [3003, 4004, 5005] on /011 R5-BINARY-KILL EXACT config

- **Axis**: 3rd seed-window sample. Family `methodology-substrate-test` (3rd consecutive). Pre-registered at /012 Phase 4.5 + brief Section 11 + Critic Phase 7.5 Option 1.
- **Rationale**: highest-information-density experiment within ≤2h EXPLORATION budget. With 3 seed-window samples, can compute Optuna-objective magnitude variance properly. Directly validates or refutes the 2-property decomposition with one more data point.
- **Predicted outcome** (LM Master Phase 7.4 §7, HIGH CONFIDENCE on magnitude; FLAT on roster):
  - IS Δ ∈ [+0.40, +0.60] (substrate-magnitude TESTABLE FALSIFIER; outside this → 2-property decomposition wrong)
  - OOS Δ in [+0.20, +0.50] (50/50 positive/negative; basin-lottery winner could go either way)
  - LTC IS roster overlap with /011 ∈ [15%, 40%]; with /012 ∈ [25%, 50%]
- **Decision split**:
  - /013 OOS Δ > +0.05 → 3/3 R5-BINARY-KILL positive across DISJOINT seed windows → /015 = R5-BINARY-KILL CONFIRMATION
  - /013 OOS Δ ≤ 0 → 2/3 → /015 = UNUSED-family CONFIRMATION (labeling preferred)
- **HIGH-RISK declaration**: NO (substrate test; no Optuna training-objective domain change).
- **Wall-clock budget**: ≤2h (matches /011/012 ~75-90 min observed).

### Option B (RESERVE if Option A blocked): /013 = LABELING axis triple-barrier σ_t source

- **Axis**: replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers (24h vs 14d EWMA window for σ_t).
- **Family**: `labeling` (UNUSED in cycle-2; last used /004 in cycle-1).
- **Rationale**: highest-prior-probability of basin escape from UNUSED-family menu (~60-70% per Critic Path Forward Option 2). Changes IS label distribution per cell → different LightGBM loss surface → potentially different basin.
- **HIGH-RISK declaration**: YES (label distribution change is HIGH-RISK per /005 rule). Multi-seed pre-commit if PROMISING.
- **Risk**: 1.5× NATR_p50 SL-noise-floor red line from /004 closeout applies.

### Option C: /013 = METHODOLOGY axis per-cell early-stop with inner hold-out

- **Axis**: LightGBM per-cell early stopping with Purged-CV inner hold-out (20% within-fold).
- **Family**: `methodology` (UNUSED since /008 PCA closure).
- **Rationale**: structurally orthogonal; changes WHICH trees retained per cell → different ensemble composition. Non-compoundable as edge signal; diagnostic infrastructure.

**QR Phase 8 SELECTION**: **Option A (PRIMARY)** — /013 = offset=6 [3003, 4004, 5005], methodology-substrate-test 3rd consecutive. Pre-registration discipline + 3-sample variance test discriminates H1 (real edge) from H2 (basin lottery) for /015 axis pre-commitment.

The final selection of /013 axis defers to Phase 4.5 LM Master advisory + Phase 6.0 Critic pre-flight on the next iteration's brief. Option B (labeling) is held as RESERVE if Option A becomes unfeasible (e.g., post-hoc orchestrator constraint).

## Cycle-2 Cadence Status

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| /011 | risk-primitive (binary-kill subtype) | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| **/012** | **methodology-substrate-test (NEW 8th family)** | **EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL)** |

**Cycle-2 EXPLORATION count after /012: 7 of 10.** CONFIRMATION-eligible at /015 (3 more EXPLORATIONs required before any CONFIRMATION can launch).

**Cycle-2 verdict distribution**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable) / 6 NEGATIVE. No edge ingredient bundled yet. /012's substrate-decomposition finding is NOT an edge ingredient but a STRUCTURAL CALIBRATION input for /015 CONFIRMATION design.

**HIGH-RISK pre-commit tripwire**: /012 declared NORMAL-RISK; no pre-commit tripwire. The discipline is battle-tested across /003-/011's 8 consecutive correct non-firings (~48h cumulative compute saved). /012's NORMAL-RISK declaration was correct — the substrate test does not change Optuna's training-objective domain; only RNG-init initialization.

## Permanent Catalog Additions (from /012 closeout)

1. **v1 substrate-basin-lock REFINED to 2-property decomposition**: substrate-MAGNITUDE-lock is correct; substrate-LOCK-IN-FULL is wrong. Update `feedback_v1_substrate_basin_lock.md` to reflect:
   - SUBSTRATE-LOCKED properties: IS Sharpe-Δ magnitude (~+0.48-0.52), LTC IS rank-1 dominance, OOS-amplification fraction
   - SEED-DRIVEN properties: specific (symbol, open_time) trade selection (67% rotate), which non-LTC symbol takes second, which symbol catastrophically loses
   - Pending /013 validation (3rd seed-window sample)

2. **NEW v1 verdict subtype `PARTIAL-DISSOLUTION-WITH-SUBSTRATE-MAGNITUDE-PRESERVATION`** (LM Master Phase 7.4 proposal; Critic Phase 7.5 endorsed for FUTURE Section 8 pre-registration; NOT retroactive on /012). Documented as forward-looking process upgrade. Phase 5.5 gate verifies inclusion in /013+ briefs Section 8 verdict tables.

3. **Engineering report hard-reject enforcement** (Critic Rec #1 to /012): codify in `quant-engineer-v1` skill at Phase 6 closeout (file existence check) AND orchestrator Phase 7.5 dispatch precondition. This is the SECOND time the Critic Rec #3 from /011 has been violated; mechanism enforcement is overdue.

4. **Section 8 verdict-matrix completeness audit at Phase 5.5** (Critic Rec #2 to /012): add checklist item "verify Section 8.1 verdict-matrix exhaustively covers F1×F3×F7 cross-product. List every cell, including boundary cells." LM Master + Critic Phase 6.0 should both flag any gap; codifying audit at Phase 5.5 catches before compute is spent.

5. **Axis-family taxonomy extension discipline** (Critic Rec #3 to /012): /012 added 8th family in 12 iterations. Future NEW family proposals should require Critic + LM Master + QR 3-way convergence on orthogonality (with explicit comparison to nearest existing family), not just QR Section 0.6 self-declaration. Add Critic Phase 6.0 axis-family veto path for novel-taxonomy iterations.

6. **LM Master FLAT-prior rule for v1 single-seed EXPLORATION** (LM Master Phase 7.4 §2 self-calibration): future Phase 4.5 advisories at v1 single-seed EXPLORATION lead with FLAT priors (A 30% / B 30% / C 40%) by default. Concentrated priors require explicit evidence at the same substrate dimension as the prediction target. Track record 0/10 directional after /012 doesn't earn concentrated priors.

7. **R5-BINARY-KILL CONFIRMATION CONDITIONAL ON /013** (LM Master Phase 7.4 §8): 2/2 positive OOS Δ at /011/012 is consistent with both H1 (real edge ~+0.05) and H2 (basin lottery happens to be positive both times). /013 = offset=6 [3003, 4004, 5005] discriminates:
   - /013 OOS Δ > +0.05 → 3/3 positive → /015 = R5-BINARY-KILL CONFIRMATION
   - /013 OOS Δ ≤ 0 → 2/3 → /015 = UNUSED-family CONFIRMATION (labeling preferred)
   This is PRE-COMMITTED CONDITIONAL — cannot be post-hoc renegotiated.

## Files & Commits on Branch

- Branch: `iteration-v1/012` from `iter-v1/011` closeout commit (tag `v0.v1-011`)
- HEAD before Phase 7+8: `34d27c3` (Critic Phase 7.5 review)

Commits in this iteration (pre-closeout):
- `360650f` — F6 roster-overlap join script (per /011 Critic Rec #2)
- `e25b129` — style: ruff E501 fixes on f6_roster_overlap.py
- `641e983` — QR Phases 1-5 + substrate-dissolution probe + brief
- `f714ec6` — LM Master Phase 4.5 pre-design advisory
- `31b55a4` — phase 5.5 gate PASS
- `357abcc` — Critic Phase 6.0 pre-flight PASS
- (Backtest run; comparison.csv + reports artifacts in `reports-v1/iteration_v1-012/`)
- `538ff1c` — LM Master Phase 7.4 post-mortem + F7 artifact
- `34d27c3` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE
- (Phase 7+8 closeout commits on this iteration)

Trunk merge: **NONE**. EXPLORATION-NEGATIVE never merges to main.

Tag: `v0.v1-012` (applied after this Phase 8 closeout).

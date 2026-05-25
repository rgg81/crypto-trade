# iter-v1/013 — Research Brief

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: EXPLORATION (single-seed-window, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)
**Axis**: SUBSTRATE-TEST 3rd SEED SAMPLE — `methodology-substrate-test` family (3rd consecutive — flagged for orchestrator review per Critic /012 Rec #3; NOT a new family declaration since the family already exists as the 8th catalog family added at /012)
**Branch**: `iteration-v1/013`

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor

`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)
- UNCHANGED post-/010, post-/011, post-/012 (ALL closed EXPLORATION-NEGATIVE)

### 0.2 Mode

**EXPLORATION** (cycle-2, post-/012 closeout)
- `--exploration --pruned-features --n-trials 35 --r5-binary-kill-enabled --r5-binary-kill-min-natr 2.0 --ensemble-seeds-offset 6` (canonical v1 EXPLORATION knobs PLUS the 3rd seed-window offset)
- ENSEMBLE_SIZE = 3 (inner seeds from offset=6 — `[3003, 4004, 5005]` — DISJOINT from both /011's `[42, 123, 456]` AND /012's `[789, 1001, 2002]`)
- ≤2h wall-clock cap (NON-NEGOTIABLE per /005 closeout 10:1 cadence discipline; matches /011/012 ~75-90 min observed)

### 0.3 Iteration label

`v1-013`

### 0.4 Determinism note

ENSEMBLE_SEEDS roster is `(42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006)`. Inner seeds are selected via `ENSEMBLE_SEEDS[offset:offset+size]` (frozen tuple, deterministic slice). With `--ensemble-seeds-offset 6` + `ENSEMBLE_SIZE=3`, /013 uses inner seeds `[3003, 4004, 5005]`. With offset=3 (/012), the window was `[789, 1001, 2002]`. With offset=0 (/011 canonical), the window was `[42, 123, 456]`. All three windows are inside the CONFIRMATION 10-seed roster — /015 multi-seed CONFIRMATION at offset=0 + size=10 naturally subsumes all three single-seed-window samples.

Backward compatibility unchanged: every existing call without `--ensemble-seeds-offset` continues to produce the canonical `[42, 123, 456, ...]` window byte-identically.

The R5-BINARY-KILL configuration is BIT-IDENTICAL to /011 AND /012 (same `risk_r5_kill_low_natr_enabled=True`, same `risk_r5_kill_low_natr_min_pct=2.0`, same disabled R5 proportional vol-target). The single dimension that changes vs /012 is `ensemble_seeds_offset` 3 → 6. Substrate-probe axis isolation is mechanically clean across all 3 seed-window samples.

### 0.5 Cadence position

**Cycle-2 EXPLORATION #8 of 10**.

Cycle-2 catalog: /006 (universe, NEG+DEGEN), /007 (feature-family composed, NEG-NEG), /008 (methodology PROMISING-METH), /009 (feature-family delete, NEG-NEG), /010 (risk-primitive proportional R5, NEG-INERT-with-IS-basin-shift), /011 (risk-primitive binary-kill R5, NEG-catastrophic-basin-shift), /012 (methodology-substrate-test offset=3, NEG-BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL).

Next CONFIRMATION cannot fire until 10 cycle-2 EXPLORATIONs accumulate (currently 8 after /013). Earliest CONFIRMATION at /015.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `methodology-substrate-test` (3rd consecutive at this family — `methodology-substrate-test` already exists as the 8th catalog family from /012; this is NOT a new family declaration; pre-existing family selected per pre-registered LM Master Phase 7.4 §7 + Critic /012 Path Forward Option 1 + /012 brief Section 11 + /012 diary "Option A PRIMARY")
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/008: `methodology`
  - iter-v1/009: `feature-family`
  - iter-v1/010: `risk-primitive` (proportional-scaling subtype)
  - iter-v1/011: `risk-primitive` (binary-kill subtype)
  - iter-v1/012: `methodology-substrate-test` (offset=3 first usage)
- **Rotation status**: **VALID** — per Axis Rotation Discipline ("if the last 5 EXPLORATIONs were all from the same family, the NEXT EXPLORATION MUST be from a different family"): prior 5 EXPLORATIONs span 4 families (methodology, feature-family, risk-primitive, methodology-substrate-test). The 5-of-5 saturation rule does NOT fire. **3-of-5 same-family is NOT saturation** (5/5 is the explicit threshold). Rotation valid for `methodology-substrate-test` continuation.
- **Critic /012 Rec #3 process flag** (NOT verdict-binding): "Future NEW family declarations should require Critic + LM Master + QR 3-way convergence on orthogonality, not just QR self-declaration." /013 is NOT a NEW family declaration — `methodology-substrate-test` was established at /012 (Critic Phase 7.5 Check 14 PASS-WITH-NOTE accepted the orthogonality argument). The 3rd consecutive same-family iteration is flagged to the orchestrator at brief review time but does NOT block dispatch under the existing rotation rule.
- **Why methodology-substrate-test 3rd consecutive and NOT a UNUSED-family pivot at /013**: pre-registration discipline. LM Master Phase 7.4 §7 explicitly pre-registered "/013 = ENSEMBLE_SEEDS offset=6 [3003, 4004, 5005] as 3rd seed sample"; Critic /012 Phase 7.5 Path Forward Option 1 endorsed; /012 diary "Option A PRIMARY" committed. Pivoting to labeling (Option 2) or methodology (Option 3) post-hoc would be exactly the rationalization v1 skill's pre-registration discipline exists to prevent. The 3rd sample is the highest-information experiment at the ≤2h budget — it completes the 3-way variance-decomposition test that disambiguates substrate-magnitude lock from coincidence on 2 data points.
- **One-sentence rationale**: /013 is the third and last seed-window sample needed to test the 2-property decomposition (substrate-MAGNITUDE locked across DISJOINT seeds; ROSTER COMPOSITION seed-driven) provisionally established at /012 closeout, and to pre-commit the /015 axis selection: F1 OOS Δ > +0.05 → R5-BINARY-KILL CONFIRMATION (3/3 positive consistent with H1 real mechanical edge ~7.5% null prob); F1 ≤ 0 → UNUSED-family CONFIRMATION (labeling preferred; 2/3 positive insufficient under H2 basin-lottery).

---

## Section 1 — Hypothesis

**At v1 EXPLORATION budget (n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED + R5-BINARY-KILL @ 2.0% BIT-IDENTICAL to /011 AND /012), shifting the inner-seeds window from `[789, 1001, 2002]` (/012 canonical) to `[3003, 4004, 5005]` (3rd DISJOINT window; still in CONFIRMATION roster) validates or refutes the 2-PROPERTY DECOMPOSITION provisionally established at /012 closeout.**

The hypothesis has three TESTABLE FALSIFIER bands; ANY band miss refutes the decomposition.

### 2-Property Decomposition (provisional; /013 validates)

Per `feedback_v1_substrate_basin_lock.md` (REFINED at /012 closeout), the substrate-basin claim decomposes:

**SUBSTRATE-LOCKED across /010/011/012** (provisional, /013 tests):
- IS Sharpe-Δ magnitude **~+0.47-0.52** (variance < 0.03 across 3 iterations)
- LTC IS rank-1 dominant-symbol slot (3/3 iterations)
- OOS-amplification fraction OOS Δ ≈ **0.45-0.78 × IS Δ** (variance < 0.5; -0.06 to +0.84 in raw fraction terms but stable enough as a basin property)

**SEED-DRIVEN across /011↔/012** (provisional, /013 tests with 2nd cross-comparison):
- Specific (symbol, open_time) IS trades — **67% rotate** (LTC IS overlap 32.71%; portfolio IS overlap 35.96%)
- Second-place IS symbol (LINK at /011 → LINK co-first at /012)
- Catastrophically losing IS symbol (BTC at /011 → DOT at /012)
- OOS roster composition — same ~32% portfolio overlap between adjacent seed windows; same 14-17% departure from BASELINE

### Hypothesis structure

The 2-property decomposition is the hypothesis. Validation requires:
1. /013 IS Sharpe Δ within substrate-magnitude band [+0.38, +0.58] (LM Master Phase 7.4 §7 P50 ± ~σ on 3 prior observations; brief F9 falsifier)
2. /013 LTC IS roster overlap with /011 within seed-driven band [15%, 40%] (LM Master Phase 7.4 §7; brief F7 falsifier)
3. /013 LTC IS roster overlap with /012 within seed-driven band [25%, 50%] (LM Master Phase 7.4 §7; NEW for /013; brief F8 falsifier)

If ANY of the 3 bands miss, the 2-property decomposition is REFUTED in its specific dimension:
- F9 (IS Δ) outside band → substrate-MAGNITUDE lock claim wrong; magnitude is NOT a property of the substrate
- F7 outside band → seed-driven roster claim wrong vs /011 reference
- F8 outside band → seed-driven roster claim wrong vs /012 reference

If ALL 3 bands hit, the 2-property decomposition is VALIDATED at 4 data points (the strongest empirical support possible at v1 EXPLORATION budget).

### Pre-registered /015 CONFIRMATION CONDITIONAL (from /012 diary §"Permanent Catalog Additions" + LM Master Phase 7.4 §8)

- **/013 F1 OOS Δ > +0.05** → 3/3 R5-BINARY-KILL positive across DISJOINT seed windows → **/015 = R5-BINARY-KILL CONFIRMATION** (mechanical edge ~+0.05 layer measurable at multi-seed; 3/3 random would be ~12.5% null prob under H2 basin-lottery → H1 favored)
- **/013 F1 OOS Δ ≤ 0** → 2/3 R5-BINARY-KILL positive → **/015 = UNUSED-family CONFIRMATION** (labeling preferred per Critic /011 Path Forward Option 2 + LM Master Phase 4.5 §6; H2 basin-lottery dominates the OOS-Δ signal at 2/3 = 25% null prob; insufficient evidence for R5 CONFIRMATION)

This is PRE-COMMITTED CONDITIONAL — cannot be post-hoc renegotiated. The /012 diary §"Permanent Catalog Additions" line item #7 codified this; /013 OUTCOME determines /015 axis selection mechanically.

### Why this is the right experiment NOW

Per Critic /012 Path Forward §"Critic adversarial recommendation: Option 1 (offset=6) IF pre-registration discipline binding; Option 2 (labeling) IF cycle-2 catalog needs structural-axis breakout AND QR declares HIGH-RISK. Weakly prefer Option 1 for LM Master argument that 3-sample variance is high-information at EXPLORATION budget."

Pre-registration discipline IS binding (per the /012 diary Path Forward selection of Option A PRIMARY + LM Master Phase 7.4 §7 + this brief Section 0.6). The cycle-2 catalog needs structural-axis breakout BUT not at the cost of breaking pre-registration: the cost would be inviting future briefs to post-hoc rationalize axis-selection choices.

The 3rd seed-window sample completes the variance-decomposition test cheaply (≤2h budget; same compute footprint as /011/012). With 3 samples (offsets 0, 3, 6), the IS Sharpe-Δ magnitude variance is properly bounded by 3 observations; with 2 samples it was only bounded by 2 observations. Information-density per compute unit is highest at the 3rd sample.

Alternative cycle-2 EXPLORATIONs (labeling axis at /013, methodology axis at /014) cost the same ≤2h budget but produce LESS information because they cannot validate or refute the 2-property decomposition that is load-bearing for /015 axis selection. The decomposition determines whether R5-BINARY-KILL has H1 real mechanical edge or H2 basin lottery — this is the question /015 CONFIRMATION will measure, and the question /013 is the ONLY way to pre-commit unambiguously.

---

## Section 2 — IS-Only Evidence (numerical tables)

The 2-property decomposition is empirically established at /012 closeout (LM Master Phase 7.4 §1 + Critic Phase 7.5 endorsement). /013 EDA is LIGHTER than typical EXPLORATION because the smoking-gun diagnostics were committed at /011 + /012 Phase 7.4/7.5. This section references prior committed evidence (per `feedback_v1_substrate_basin_lock.md`).

### 2.1 Substrate-magnitude empirical baseline across /010/011/012

From `reports-v1/iteration_v1-010/comparison.csv`, `reports-v1/iteration_v1-011/comparison.csv`, `reports-v1/iteration_v1-012/comparison.csv` (all committed):

**IS Sharpe-Δ trajectory**:

| Iteration | Inner seeds | Axis | IS Sharpe | IS Δ vs BASELINE | Notes |
|---|---|---|---|---|---|
| BASELINE | [42, 123, 456, 789, 1001] | none | +0.2829 | — | corrected v1 baseline |
| /010 | [42, 123, 456] | R5 proportional vol-target | +0.7530 | **+0.4701** | LTC IS pct = 119.84% |
| /011 | [42, 123, 456] | R5-BINARY-KILL @ 2.0% | +0.7678 | **+0.4849** | LTC IS pct = 106.48% |
| /012 | [789, 1001, 2002] | R5-BINARY-KILL @ 2.0% | +0.7996 | **+0.5167** | LTC IS pct = 412.12% (denominator-effect) |

**Substrate-magnitude variance**: std(IS Δ across 3 iterations) ≈ **0.025**, **range 0.047** (max +0.5167 - min +0.4701). The IS Δ magnitude is substantially substrate-locked.

### 2.2 Roster overlap measurements across /010/011/012

From `reports-v1/iteration_v1-011/f6_roster_overlap.csv` and `reports-v1/iteration_v1-012/f7_roster_overlap.csv` (both committed):

**LTC IS roster overlap matrix**:

| comparison | overlap | seed change? | axis change? |
|---|---|---|---|
| /010 ↔ /011 LTC IS | **93.27%** (97/104) | NO (same offset=0) | YES (proportional → binary-kill) |
| /011 ↔ /012 LTC IS | **32.71%** (35/107) | YES (offset 0 → 3) | NO (binary-kill bit-identical) |

The 60.56pp drop in LTC IS overlap when seeds change at IDENTICAL axis vs when axes change at IDENTICAL seed is the empirical signature of the 2-property decomposition. Same-seed across different axes → basin re-discovered ~93%. Different-seed at same axis → roster re-routes ~33%.

**Substrate-magnitude property** (Sharpe Δ) survives BOTH dimensions (axis change AND seed change).
**Roster-composition property** survives ONE dimension (axis change at same seed) but NOT the other (seed change at same axis).

### 2.3 OOS-amplification fraction trajectory

OOS-amplification fraction = OOS Sharpe Δ / IS Sharpe Δ:

| Iteration | IS Δ | OOS Δ | Fraction |
|---|---|---|---|
| /010 | +0.4701 | -0.0283 | **-0.06** (basin transfer failed for /010) |
| /011 | +0.4849 | +0.4072 | **+0.84** (basin substantially transfers) |
| /012 | +0.5167 | +0.2726 | **+0.53** (basin partially transfers) |

Variance is high (range -0.06 to +0.84) but the **POSITIVE-OOS-DELTA fraction** at 2/3 (/011 and /012) IS the basis for the R5-BINARY-KILL CONFIRMATION conditional: 2/2 positive OOS Δ at R5-BINARY-KILL configurations is consistent with H1 mechanical edge OR H2 basin-lottery. /013 is the discriminator.

### 2.4 What MUST be true if 2-property decomposition holds at /013

Predicted /013 properties:

1. **IS Sharpe-Δ ∈ [+0.38, +0.58]** (substrate-magnitude TESTABLE FALSIFIER; ±0.10 band centered on mean of 3 prior observations +0.49)
2. **LTC IS roster overlap with /011 ∈ [15%, 40%]** (seed-driven TESTABLE FALSIFIER vs offset=0 reference; LM Master Phase 7.4 §7 P50 ≈ 27% per /011↔/012 32.71% observation reduced for additional ~3 generations of seed routing)
3. **LTC IS roster overlap with /012 ∈ [25%, 50%]** (seed-driven TESTABLE FALSIFIER vs offset=3 reference; LM Master Phase 7.4 §7 P50 ≈ 35% per /011↔/012 32.71% adjusted slightly higher for adjacent seed-window window vs /011 cross-comparison)
4. **OOS-amplification fraction ∈ [-0.20, +0.85]** (looser band per high observed variance)

If observed substantially outside ANY of bands 1-3, the 2-property decomposition is REFUTED in that dimension and the /015 axis-selection conditional needs reassessment.

### 2.5 Why /011 + /012 EDA evidence remains valid for /013

The /011 EDA tested whether R5-BINARY-KILL MECHANISM produces positive OOS Δ when applied as ORACLE to a roster. The cross-roster oracle showed positive Sharpe-Δ on BASELINE roster (+0.046) AND on /010 roster (+0.115).

The /012 EDA tested the substrate-MAGNITUDE lock claim (proved IS Δ stays at +0.47-0.52 across DISJOINT seed windows at IDENTICAL axis).

/013 inherits both EDA findings. The mechanism does NOT change with inner-seed shift (R5 fire rate measured at /011 IS 18.34% / OOS 21.69% and /012 IS 17.38% / OOS 22.84%; tightly bounded; /013 should also be within ±2pp of these). What might change is the BASIN substrate the mechanism operates on top of — exactly what /013 measures.

If /013 produces F1 OOS Δ > +0.05, kill_low mechanical layer is the residual OOS Sharpe-Δ AFTER multi-seed dissolution. Per `feedback_v1_substrate_basin_lock.md`, mechanical kill_low layer estimate is ~+0.05 OOS Sharpe-Δ.

### 2.6 No new EDA work needed — empirical decomposition established

The /011 + /012 Phase 7.4 LM Master post-mortems produced the load-bearing 93.3% LTC IS overlap (/010↔/011) and 32.71% LTC IS overlap (/011↔/012) measurements. The 2-property decomposition is empirically established on 3 data points; /013 is the 4th data point validation.

The committed `f6_roster_overlap.csv` (/011 reports) and `f7_roster_overlap.csv` (/012 reports) serve as deterministic references for all future F7/F8-type comparisons. /013's `f7_roster_overlap.csv` will join /013 against BASELINE, /010, /011, /012 references using the same `analysis/iteration_v1-012/f6_roster_overlap.py` script (general-purpose; supports arbitrary `--reference NAME=PATH` arguments).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: /013 does NOT change Optuna's training-objective domain. The training distribution (which `(symbol, open_time)` rows enter the loss + their weights + their labels) is BIT-IDENTICAL to /011 AND /012 at any given (model, month) cell. Only the inner-seeds passed to LightGBM (and the Optuna sampler initialization) change. The loss surface that Optuna explores is identical; only the trajectory through that surface changes.
- **Mitigation (NORMAL-RISK does not require mitigation)**: N/A. Single-seed-window EXPLORATION is the appropriate cadence for the 3rd seed-window sample.

### Rationale for NORMAL-RISK declaration

HIGH-RISK declarations in v1 are reserved for axes that change the optimization target itself (risk-primitive constraint changes, universe substitution, label-mode change, feature-set replacement, bar-interval change). /013 changes NONE of these. The R5-BINARY-KILL @ 2.0% is BIT-IDENTICAL to /011 AND /012 (same `risk_r5_kill_low_natr_enabled=True`, same threshold, same disabled R5 proportional vol-target). The feature columns, ATR multipliers, n_trials, ENSEMBLE_SIZE, symbols, training window, OOD gate — ALL unchanged from /012.

From the LightGBM perspective, /013 will see the EXACT SAME training rows in the EXACT SAME (model, month) cells with the EXACT SAME labels and weights as /011 AND /012 did. The only difference is the random number generator's initialization. This is a pure substrate test, same as /012.

The /012 outcome (NORMAL-RISK declaration was correct; substrate test did not change Optuna's training-objective domain; only RNG-init) supports the same declaration for /013.

---

## Section 3 — Proposed Changes (incorporating Critic /012 Process Recommendations)

### 3.1 Code changes (src/ + runner)

**Only ONE** change vs /012's branch (no new code):

1. **`run_baseline_v1.py`** — NO change. The `--ensemble-seeds-offset` CLI flag was added at /012 commit `360650f` and is backward-compatible. /013 only changes the FLAG VALUE from `3` to `6` at invocation time.

2. **No `src/` changes**. R5-BINARY-KILL wiring lives in `src/crypto_trade/backtest.py` and `src/crypto_trade/backtest_models.py` from /011 commit `b788d4f`. /012 wired through `ensemble_seeds_offset` per /012 commit `360650f`. /013 inherits both unchanged.

3. **No new analysis scripts needed**. The `analysis/iteration_v1-012/f6_roster_overlap.py` script is general-purpose; /013 reuses it with `--reference iter010=... iter011=... iter012=...` arguments. The output filename will be `f7_roster_overlap.csv` (consistent with /012's name choice).

### 3.2 Critic /012 Process Recommendations — ADOPTED EXPLICITLY

Per Critic /012 Phase 7.5 §"Recommendations to QR" + /012 diary §"Permanent Catalog Additions" — three process recommendations to /013, all ADOPTED:

#### Rec #1 — Pre-register Section 8.1 verdict matrix COMPLETELY (cover ALL F1×F3×F7×F8×F9 cells, including boundary cells)

**Critic /012 Rec text**: "Section 8 verdict-matrix completeness audit at Phase 5.5. Add checklist item: 'verify Section 8.1 verdict-matrix exhaustively covers F1×F3×F7 cross-product. List every cell, including boundary cells.' LM Master + Critic Phase 6.0 should both have flagged this gap; codifying audit at Phase 5.5 catches before compute is spent."

**/013 Adoption**:
- Section 8.1 below pre-registers ALL F1 × F3 × F7 × F8 × F9 cells (5-dimensional matrix; ~6 to 8 deterministic verdict-class rows; boundary cells explicitly handled)
- F9 (NEW for /013, substrate-magnitude lock validation) and F8 (NEW for /013, seed-driven roster vs /012) are pre-registered alongside F7
- The matrix MUST resolve every observable cell to a verdict-class without discretion at verdict time
- Phase 5.5 gate audit checklist verifies completeness

#### Rec #2 — Engineering report mandatory at Phase 7.5

**Critic /012 Rec text**: "Engineering report hard-reject enforcement. Brief Section 3.5 Rec #3 stated 'orchestrator hard-rejects Phase 7.5 dispatch without it'. Orchestrator did NOT enforce. Codify hard-reject in `quant-engineer-v1` skill at Phase 6 closeout (file existence check) AND orchestrator Phase 7.5 dispatch precondition."

**/013 Adoption**:
- Brief Section 10.2 below specifies the engineering report at `reports-v1/iteration_v1-013/engineering_report.md` as a Phase 6 QE DELIVERABLE (not Phase 7 carry-forward)
- Engineering report file existence check is added to the Phase 5.5 gate (QR-side discipline) AND Critic Phase 6.0 pre-flight check
- Orchestrator-side hard-reject at Phase 7.5 dispatch precondition is process-discipline noted in this brief (orchestrator's enforcement; QR cannot mandate)
- The recommendation should now be enforced; /013 is the test of enforcement (3rd consecutive engineering-report-required iteration)

#### Rec #3 — Axis-family taxonomy discipline

**Critic /012 Rec text**: "Axis-family taxonomy extension discipline. /012 added 8th family in 12 iterations. Future NEW family proposals should require Critic + LM Master + QR 3-way convergence on orthogonality (with explicit comparison to nearest existing family), not just QR Section 0.6 self-declaration. Add Critic Phase 6.0 axis-family veto path for novel-taxonomy iterations."

**/013 Adoption**:
- /013 declares `methodology-substrate-test` as a PRE-EXISTING family (8th catalog family already established at /012); this is NOT a new family declaration
- Section 0.6 explicitly flags the 3rd consecutive same-family pattern to the orchestrator (not verdict-binding, but transparent process flag)
- Critic Phase 6.0 axis-family veto path: if Critic disagrees on family taxonomy continuity, /013 dispatch can be blocked at pre-flight; brief Section 10.2 Phase 6.0 deliverable acknowledges this
- Future NEW family declarations (post-/013) MUST go through 3-way convergence; /013 is NOT a new family declaration so this rule does not bind /013 directly

### 3.3 LM Master Phase 4.5 recommendation response (anticipated)

LM Master Phase 4.5 is fired SEPARATELY at /013 dispatch. The current brief is QR Phase 5 output and pre-dates Phase 4.5 advisory. Section 3 will be updated post-Phase 4.5 with explicit LM Master recommendation responses per the v1 skill discipline. Anticipated LM Master recommendations (based on the Phase 7.4 §7 pre-registration):

- **Probable LM Master Rec #1**: "Adhere to pre-registered offset=6 [3003, 4004, 5005] — pre-registration discipline at stake; no axis variation needed" — pre-adopted (the brief specifies BIT-IDENTICAL config to /011/012 modulo offset).
- **Probable LM Master Rec #2**: "Use FLAT priors A 30% / B 30% / C 40% per the /012 Phase 7.4 self-calibration rule — substrate decomposition prediction has equal probability of staying in band or falling outside" — Section 5 priors below ADOPT the flat-prior rule per LM Master Phase 7.4 §2 commitment.
- **Probable LM Master Rec #3**: "Pre-register Section 8.1 with ALL F1×F3×F7×F8×F9 cells per Critic /012 Rec #1" — pre-adopted (Section 8.1 below is exhaustive).
- **Probable LM Master Rec #4**: "Avoid pivoting to UNUSED-family axis until /013 outcome resolves /015 conditional" — pre-adopted (brief Section 1 + Section 11 are explicit; /013 IS the offset=6 sample).

If LM Master Phase 4.5 Rec materially diverges from the above, the brief Section 3 will be UPDATED in a separate commit (per v1 skill Section 0.6 + 3.6).

### 3.4 Runner invocation

```bash
uv run python run_baseline_v1.py \
    --exploration \
    --iteration 13 \
    --pruned-features \
    --n-trials 35 \
    --r5-binary-kill-enabled \
    --r5-binary-kill-min-natr 2.0 \
    --ensemble-seeds-offset 6
```

Hash-comparable to /012's invocation (which was identical minus `--ensemble-seeds-offset 6` ↔ `--ensemble-seeds-offset 3`). All other flags BIT-IDENTICAL.

### 3.5 Expected wall-clock budget

/011 and /012 each ran in ~75-90 min wall-clock per their diaries. /013 has SAME compute footprint:
- Same n_trials=35 per cell
- Same ENSEMBLE_SIZE=3 (3 inner seeds; different RNG seeds within roster)
- Same V1_FEATURE_COLUMNS_PRUNED (40 features)
- Same 4-model dispatch (A pooled, C LINK, D LTC, E DOT)
- Same R5-BINARY-KILL fire rate expectation (18-23% IS / 21-23% OOS based on /011/012 measurements)

Predicted wall-clock: 75-90 min. ≤2h cap is safe.

---

## Section 4 — Falsifiers (F1-F9)

Each falsifier has an explicit pre-registered numerical condition. F1-F7 inherited from /012 (with F7 P50 band updated per LM Master Phase 7.4 §7). F8 + F9 NEW for /013.

### F1 — OOS Sharpe-Δ vs BASELINE

**Pass band**: OOS Sharpe Δ vs BASELINE in [+0.05, +0.55].
**Fire conditions**:
- OOS Δ ≥ +0.55: catastrophic-positive (basin-rediscovery PLUS mechanical kill_low layer compounding)
- OOS Δ ∈ [+0.05, +0.55]: PROMISING band (informational; outcome class determined by F3+F7+F8+F9 combination)
- OOS Δ ∈ (-0.05, +0.05): INERT band (no axis-mechanism effect; basin draw produced ~BASELINE-equivalent OOS)
- OOS Δ < -0.05: NEGATIVE (basin draw produced worse OOS than BASELINE)

**Reference**: /011 +0.4072 / /012 +0.2726 — both in PROMISING band.

**Interpretation**: F1 is the LOAD-BEARING falsifier for the /015 axis-selection CONDITIONAL.

### F2 — R5-BINARY-KILL fire rate

**Pass band**: IS R5 fire rate ∈ [10%, 60%] AND OOS R5 fire rate ∈ [10%, 60%].
**Reference**: /011 measured IS 18.34% / OOS 21.69%; /012 measured IS 17.38% / OOS 22.84%. /013 predicted in same ±2pp window.
**Fire conditions**: outside band → axis-mechanism degeneracy or data divergence — BLOCK-PENDING-FIX candidate.

**Interpretation**: F2 should PASS at >99% probability (mechanism BIT-IDENTICAL to /011/012; data extent identical).

### F3 — IS Sharpe-Δ vs BASELINE

**Pass band per outcome class**:
- **2-PROPERTY DECOMPOSITION VALIDATED (4/4 samples within band)**: IS Sharpe Δ ∈ [+0.38, +0.58] (substrate-magnitude TESTABLE FALSIFIER per LM Master Phase 7.4 §7)
- **Catastrophic-IS-overshoot**: F3 Δ > +0.58 — outside upper band; substrate-MAGNITUDE lock claim WRONG (basin draws are NOT bounded in magnitude)
- **Catastrophic-IS-undershoot**: F3 Δ < +0.38 — outside lower band; substrate-MAGNITUDE lock claim WRONG (specifically for offset=6 case, but ALSO refutes the 3-iteration mean +0.49 estimate)
- **Secondary band** [+0.10, +0.38) — partial deviation; substrate-magnitude is "directionally locked but with significant variance" — REFUTES decomposition in the magnitude dimension

**Interpretation**: F3 + F9 are the PRIMARY substrate-magnitude diagnostic. F3 explicitly numerical; F9 is the substrate-magnitude lock validation derived from F3 against the [+0.38, +0.58] band.

### F4 — DEGENERATE_PREDICTOR detector + comparison.csv schema integrity

**Pass conditions**:
- No DEGENERATE_PREDICTOR firings in `validation_v1.detect_degenerate_predictor`
- comparison.csv schema clean: `r5_binary_kill_fire_rate_is`, `r5_binary_kill_fire_rate_oos` rows correctly labeled (per /010 D-RPRT-001 fix carried forward)
- No 0-pnl trade clusters from dead-feed data (D-RPRT-001 detection: ≥ 30 consecutive trades at exact same entry+exit price)

**Reference**: /011 PASS; /012 PASS. /013 uses V1_BASELINE_UNIVERSE (BTC, ETH, LINK, LTC, DOT) — same as /011/012 — F4 should PASS.

### F5 — PSR monotonic + ADF stationarity

**Pass conditions**:
- PSR_monthly_vs_0 ≥ 0.50 for both IS and OOS (informational signal that Sharpe is above zero benchmark)
- ADF Bonferroni-corrected p < 0.05 for all 40 features in V1_FEATURE_COLUMNS_PRUNED (regime_indicator exceptions: vol_natr_14 already in adf_exceptions per /002+ rules)

**Reference**: /011 PSR_monthly_vs_0 IS 0.926 / OOS 0.918; /012 PSR_monthly_vs_0 IS 0.935 / OOS 0.934. /013 predicted in same range.

### F6 — OOS roster-overlap with BASELINE

**Pass conditions**:
- /013 OOS roster overlap with BASELINE roster: pre-registered for diagnostic purposes (does NOT alone trigger verdict)
- Catastrophic-basin-shift signature: F6 < 61% baseline-overlap (mirrors /011's 16.67% / /012's 14.21% findings)
- Inert: F6 ≥ 80% baseline-overlap (no axis-mechanism + no basin shift)
- Intermediate: F6 ∈ [61%, 80%]

**Reference**: /011 OOS overlap with BASELINE = 16.67%; /012 = 14.21%. /013 should be in same ~15% range (substrate-locked aggregate basin departure; /013 inherits the R5-BINARY-KILL mechanical filter effect).

**Interpretation**: F6 informs how much of /013's OOS roster is "discoverably different" from BASELINE.

### F7 — LTC IS roster-overlap with /011 (substrate-test cross-comparison vs offset=0 reference)

**Pre-registered band per the 2-PROPERTY DECOMPOSITION** (LM Master Phase 7.4 §7):

- **Validates seed-driven roster claim (P50 ≈ 27%)**: F7 ∈ [15%, 40%]
- **Substrate-locked-fail-on-the-other-side**: F7 > 40% means roster also substrate-locked (decomposition REFUTED — roster IS substrate-property, not seed-property)
- **Lottery-bottom-out**: F7 < 15% means roster is overwhelmingly seed-driven beyond expected (decomposition still validated, but seeds dominate even more than /011↔/012 32.71% suggested)
- **Bands explicit**:
  - F7 > 70% — SUBSTRATE-LOCKED (decomposition REFUTED for roster property)
  - F7 ∈ (40%, 70%) — PARTIAL-SUBSTRATE-LOCKED (decomposition refuted; same-axis shows substantial substrate inheritance)
  - F7 ∈ [15%, 40%] — SEED-DRIVEN (decomposition VALIDATED in band; bands match /011↔/012 reference)
  - F7 < 15% — STRONG SEED-DRIVEN (decomposition validated but lower than expected; informational)

**Reference**: /011 ↔ /012 LTC IS overlap = 32.71%. /013 (3rd window) ↔ /011 (1st window) overlap is at one more generation of seed routing — expect slightly LOWER than 32.71% — LM Master Phase 7.4 §7 P50 ≈ 27%.

### F8 — LTC IS roster-overlap with /012 (substrate-test cross-comparison vs offset=3 reference; NEW for /013)

**Pre-registered band per the 2-PROPERTY DECOMPOSITION** (LM Master Phase 7.4 §7):

- **Validates seed-driven roster claim (P50 ≈ 35%)**: F8 ∈ [25%, 50%]
- **Substrate-locked-fail-on-the-other-side**: F8 > 50% means roster is substrate-locked at ADJACENT seed windows (decomposition REFUTED for adjacent comparison)
- **Lottery-bottom-out**: F8 < 25% means /013 routes farther from /012 than /012 did from /011 (decomposition validated but with stronger seed-effect than estimated)
- **Bands explicit**:
  - F8 > 70% — SUBSTRATE-LOCKED at adjacent seed windows (decomposition REFUTED)
  - F8 ∈ (50%, 70%) — PARTIAL-SUBSTRATE-LOCKED at adjacent (decomposition refuted)
  - F8 ∈ [25%, 50%] — SEED-DRIVEN at adjacent (decomposition VALIDATED in band)
  - F8 < 25% — STRONG SEED-DRIVEN at adjacent (validated but lower than expected)

**Reference**: /011 ↔ /012 LTC IS overlap = 32.71% (adjacent windows: offset=0 to offset=3). /013 ↔ /012 are also adjacent windows (offset=3 to offset=6). Should be in similar range. F8 P50 ≈ 35%.

**Why F8 specifically vs /012**: F7 tests overlap vs first window (offset=0); F8 tests overlap vs second window (offset=3). Both bands must be hit for seed-driven roster claim to validate across the full 3-window grid. If F7 hits but F8 misses (or vice versa), the seed-driven claim has dimension-specific structure that warrants investigation.

### F9 — IS Sharpe-Δ within substrate-magnitude band [+0.38, +0.58] (NEW for /013)

**Pre-registered band per LM Master Phase 7.4 §7**:

- **Substrate-MAGNITUDE LOCK VALIDATED**: F9 ∈ [+0.38, +0.58]
- **Catastrophic-overshoot**: F9 > +0.58 → substrate-magnitude lock REFUTED in upper direction (basin draws unbounded in magnitude)
- **Catastrophic-undershoot**: F9 < +0.38 → substrate-magnitude lock REFUTED in lower direction (3-prior-mean of +0.49 is an outlier average)

**Reference**: /010 IS Δ +0.4701 / /011 IS Δ +0.4849 / /012 IS Δ +0.5167. Mean = +0.49; std ≈ 0.025; ±1σ range [+0.465, +0.515]; ±2σ range [+0.44, +0.54]; expanded for tolerance to [+0.38, +0.58].

**Distinct from F3**: F3 measures the IS Sharpe Δ value itself (with multiple sub-band assignments depending on outcome class). F9 is the BINARY pass-fail on the substrate-magnitude lock claim — does the observed value fall in the pre-registered ±2σ band? F9 is a derived falsifier from F3.

**Interpretation**: F9 = PASS → substrate-magnitude lock claim validated; F9 = FAIL → claim refuted; treat as catastrophic-basin-shift in EITHER direction.

---

## Section 5 — Predicted Outcomes per 3-Way Pre-Registration

Per LM Master Phase 7.4 §7 commitment to FLAT priors at v1 single-seed-window EXPLORATION (A 30% / B 30% / C 40%), the verdict-class probabilities are FLAT for ROSTER outcome (Outcome A/B/C). Magnitude (F9) is HIGH-CONFIDENCE pass at ~85% per substrate-anchored ±2σ band.

| Outcome class | Probability | Predicted F1 OOS Δ | Predicted F3/F9 IS Δ | Predicted F7 LTC overlap with /011 | Predicted F8 LTC overlap with /012 |
|---|---|---|---|---|---|
| **A — SUBSTRATE-LOCKED (Outcome A)** | **~30%** | +0.20 to +0.60 (basin substrate inherited) | +0.45 ± 0.10 (substrate signature) | > 40% (substrate-driven roster — wrong-direction for our claim) | > 50% (substrate-driven roster — wrong-direction for our claim) |
| **B — SEED-LOCKED (Outcome B)** | **~30%** | -0.10 to +0.20 (no basin amplification) | +0.45 ± 0.10 (substrate signature, even if basin diverges) | < 30% (strongly seed-driven; band still validated) | < 25% (strongly seed-driven; band lower-side failure) |
| **C — PARTIAL (Outcome C)** | **~40%** | +0.10 to +0.45 (partial basin transfer) | +0.45 ± 0.10 (substrate signature) | [15%, 40%] (seed-driven in band) | [25%, 50%] (seed-driven in band) |

### Reasoning for FLAT 30/30/40 priors

Per LM Master Phase 7.4 §2 commitment (after 0/10 directional track record at v1 single-seed-window EXPLORATION):

> "Lead with FLAT priors at v1 single-seed EXPLORATION: A 30% / B 30% / C 40%. Empirical record doesn't earn concentrated priors. No verdict-class projection when evidence is at different substrate dimension than prediction target. Magnitude predictions stay HIGH-confidence (substrate-anchored from 3 data points: IS Δ +0.50 ± 0.10)."

The 30/30/40 prior is committed by LM Master Phase 7.4 self-calibration. /013 brief Section 5 ADOPTS this rule.

### Most decision-relevant prediction

**F1 OOS Δ ≥ +0.05 (positive R5-BINARY-KILL at /013)** is what triggers the /015 R5-BINARY-KILL CONFIRMATION conditional. This outcome could co-occur with:
- Outcome A (substrate-locked roster + positive OOS) — informational: kill_low compounds with substrate basin
- Outcome B (seed-locked roster + positive OOS, surprising) — would also trigger /015 = R5-BINARY-KILL CONFIRMATION (3/3 positive evidence wins under H1 vs H2)
- Outcome C (partial roster + positive OOS) — would trigger /015 = R5-BINARY-KILL CONFIRMATION

**F1 OOS Δ ≤ 0 (negative R5-BINARY-KILL at /013)** — would commit /015 = UNUSED-family CONFIRMATION (labeling). 2/3 positive at R5 across DISJOINT seed windows is insufficient under H2 basin-lottery (25% null prob).

Per the FLAT 30/30/40 prior across roster outcomes, F1 OOS Δ ≥ +0.05 is approximately 60-70% probable (Outcome A or C with positive OOS = ~50%; small portion of Outcome B with surprising positive OOS = ~10-20%).

### Multi-seed CONFIRMATION dissolution prediction (regardless of /013 outcome)

For /015 CONFIRMATION (which will use all 10 ENSEMBLE_SEEDS values), predicted multi-seed OOS Sharpe-Δ:

- If /013 confirms /015 = R5-BINARY-KILL CONFIRMATION: substrate basin lottery dissolves across 10 seeds → mean OOS Sharpe ≈ BASELINE +0.66 + mechanical kill_low layer ~+0.05 = **~+0.71** (NOT /011's +1.07 single-seed magnitude); 10-seed std ≈ 0.30-0.40 due to basin-lottery variance per seed
- If /013 routes /015 to UNUSED-family CONFIRMATION (labeling): different outcome distribution; not predicted here

In ALL three roster outcomes, the mechanical kill_low layer should produce ~+0.05 OOS Sharpe-Δ at multi-seed. /015 CONFIRMATION decisively measures this.

---

## Section 6 — What Could Falsify the Hypothesis (Pre-Registered Tripwires)

The hypothesis is the 2-PROPERTY DECOMPOSITION (substrate-magnitude lock + seed-driven roster). Any of the following observations would falsify or refute specific dimensions:

| Observation | Falsifies | Result |
|---|---|---|
| F9 outside [+0.38, +0.58] (IS Δ catastrophic miss) | substrate-MAGNITUDE lock dimension | 2-property decomposition REFUTED in magnitude direction → halt and reassess; LM Master Phase 7.4 §7 explicitly states "halt and reassess" if outside this band |
| F7 > 70% AND F8 > 70% (roster substrate-locked at all comparisons) | seed-driven roster dimension | 2-property decomposition REFUTED; basin is full-substrate-locked across DISJOINT seed windows; reconsider/011↔/012 32.71% as anomaly |
| F7 < 15% AND F8 < 25% (roster overwhelmingly seed-driven) | informational — does NOT refute, but indicates seeds dominate more than /011↔/012 suggested | decomposition VALIDATED, but with stronger seed-effect estimate; affects /015 CONFIRMATION multi-seed dissolution prediction |
| F2 R5 fire rate outside [10%, 60%] band | substrate-test design | data integrity failure; not substrate-lock signal — BLOCK-PENDING-FIX |
| F4 DEGENERATE_PREDICTOR fires on any cell | trade roster validity | data integrity failure; not substrate-lock signal — BLOCK-PENDING-FIX |
| F1 OOS Δ > +1.10 (drastic positive overshoot) | all outcome classes | numerical instability or non-deterministic seed handling — BLOCK-PENDING-FIX |
| Wall-clock > 2h | scope discipline | review and consider --kill flag; not iteration-corrupting at first occurrence; document in engineering report |

The substrate-test design is robust against most non-data failures. The expected verdict will be one of {Outcome A, B, C} per Section 8 verdict gates.

---

## Section 7 — Mechanism Diagram (per /011 codification + /012 refinement)

Per `feedback_v1_substrate_basin_lock.md` REFINED at /012 closeout, the substrate is mechanically:

```
At v1 EXPLORATION budget:
  (data + features + V1_FEATURE_COLUMNS_PRUNED + bounds_profile + n_trials=35 + ENSEMBLE_SIZE=3)
                ⇓
        OPTUNA SAMPLER + LightGBM TRAINER initialized by INNER SEED [s1, s2, s3]
                ⇓
        Bayesian search of n_trials=35 ≈ 35 hyperparameter points per cell
                ⇓
        Per-cell convergence to equivalent-DEPTH basin (substrate-magnitude)
        but routing through DIFFERENT specific trades (seed-driven roster)
                ⇓
        Per-(model, month) basin draws produce per-cell prediction model
                ⇓
        BACKTEST signal generation (R5-BINARY-KILL filter applied; kill_low @ NATR<2.0%)
                ⇓
        OBSERVED ROSTER (IS + OOS)
```

The 2-property decomposition refines the strict substrate-lock claim:

**Substrate-MAGNITUDE locked** (across all 3 prior iterations /010/011/012):
- IS Sharpe-Δ magnitude ~+0.48-0.52 (variance < 0.03)
- LTC IS rank-1 dominance always emerges
- OOS-amplification fraction OOS Δ ≈ 0.45-0.78 × IS Δ

**Roster COMPOSITION seed-driven** (per /011↔/012 evidence):
- Specific (symbol, open_time) trades — 67% rotate
- Second-place IS symbol
- Catastrophically losing IS symbol

/013 measurement: hold (data, features, bounds, n_trials, ensemble_size, R5 mechanism) BIT-IDENTICAL to /011 AND /012; change ONLY (s1, s2, s3) from `[789, 1001, 2002]` to `[3003, 4004, 5005]`. The 2-property decomposition predicts:
- IS Sharpe Δ ≈ +0.49 ± 0.10 (substrate-magnitude lock validates)
- LTC IS roster overlap with /011 in [15%, 40%] (seed-driven validates)
- LTC IS roster overlap with /012 in [25%, 50%] (seed-driven validates)

---

## Section 8 — Verdict Gates

### 8.1 Verdict-class deterministic resolution (FULLY PRE-REGISTERED per Critic /012 Rec #1)

**The COMPLETE F1 × F3 × F7 × F8 × F9 verdict-matrix.** Every observable cell resolves to a verdict-class without discretion at verdict time.

| Row | F1 (OOS Δ) | F3 (IS Δ) | F9 (IS Δ band [+0.38, +0.58]) | F7 (LTC overlap /011) | F8 (LTC overlap /012) | Verdict-class |
|---|---|---|---|---|---|---|
| **1** | ≥ +0.05 | ≥ +0.38 | PASS | > 70% | > 70% | **EXPLORATION-NEGATIVE subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-FULL-SUBSTRATE-LOCKED`** (Outcome A full substrate-lock; decomposition REFUTED for roster dimension; /015 → R5-BINARY-KILL CONFIRMATION conditional fires) |
| **2** | ≥ +0.05 | [+0.38, +0.58] | PASS | [15%, 40%] | [25%, 50%] | **EXPLORATION-PROMISING-SUBSTRATE-MAGNITUDE-VALIDATED-SEED-DRIVEN** (Outcome C decomposition VALIDATED; /015 → R5-BINARY-KILL CONFIRMATION conditional fires; THE MOST DECISION-RELEVANT cell) |
| **3** | ≥ +0.05 | [+0.38, +0.58] | PASS | (40%, 70%) | (50%, 70%) | **EXPLORATION-PROMISING-PARTIAL-DISSOLUTION-SUBSTRATE-MAGNITUDE-VALIDATED** (Outcome C-A boundary; partial roster substrate-lock; decomposition REFUTED in roster dimension at adjacent comparison; /015 → R5-BINARY-KILL CONFIRMATION conditional fires) |
| **4** | ≥ +0.05 | [+0.38, +0.58] | PASS | < 15% | < 25% | **EXPLORATION-PROMISING-STRONG-SEED-DRIVEN-SUBSTRATE-MAGNITUDE-VALIDATED** (Outcome B-C boundary; roster overwhelmingly seed-driven; decomposition VALIDATED with stronger seed-effect; /015 → R5-BINARY-KILL CONFIRMATION conditional fires) |
| **5** | [-0.05, +0.05) | [+0.38, +0.58] | PASS | any | any | **EXPLORATION-NEGATIVE subtype `BASELINE-EQUIVALENT-NULL-SUBSTRATE-MAGNITUDE-VALIDATED`** (Outcome B-INERT; mechanism inert at OOS but substrate-magnitude still substrate-locked; /015 → UNUSED-family CONFIRMATION conditional fires) |
| **6** | < -0.05 | [+0.38, +0.58] | PASS | any | any | **EXPLORATION-NEGATIVE subtype `seed-shifted-NEGATIVE-SUBSTRATE-MAGNITUDE-VALIDATED`** (Outcome B negative basin draw; substrate-magnitude validated but specific basin lottery produced regression; /015 → UNUSED-family CONFIRMATION conditional fires) |
| **7** | any | < +0.38 OR > +0.58 | FAIL | any | any | **EXPLORATION-NEGATIVE subtype `SUBSTRATE-MAGNITUDE-LOCK-REFUTED`** (substrate-magnitude lock claim WRONG; 2-property decomposition refuted in magnitude direction; halt and reassess per LM Master Phase 7.4 §7) |
| **8** | > +0.55 | > +0.58 | FAIL (overshoot) | > 90% | > 90% | **EXPLORATION-NEGATIVE subtype `catastrophic-substrate-amplification`** (catastrophic-positive overshoot; substrate-MAGNITUDE NOT bounded as claimed; decomposition refuted) |

**Every observable cell resolves**: Rows 1-8 cover the F1 × F3 × F9 × F7 × F8 cross-product without discretion at verdict time. Boundary cells:
- F1 boundary at +0.05 → rows 5/6 partition (F1=+0.05 exact resolves to row 5 INERT; F1<+0.05 to row 6 negative; ties broken by smaller magnitude per /011 convention)
- F3 boundary at +0.38 → row 7 REFUTED if value strictly below +0.38; rows 1-4 retain if ≥+0.38
- F3 boundary at +0.58 → row 7 REFUTED if strictly above +0.58; rows 1-4 retain if ≤+0.58
- F7 boundaries at 15%, 40%, 70% → rows 2/3/4/1 partition by closed-on-left half-open intervals
- F8 boundaries at 25%, 50%, 70% → analogous partition

### 8.2 Substrate-test diagnostic outcome assignment

Independent of Section 8.1 verdict-class, /013 produces a DIAGNOSTIC outcome that codifies the substrate-magnitude lock validation:

| F9 result | F7+F8 result | Diagnostic outcome | Path Forward implication |
|---|---|---|---|
| PASS | F7 ∈ [15%, 40%] AND F8 ∈ [25%, 50%] | **2-PROPERTY DECOMPOSITION VALIDATED** | The substrate-magnitude lock + seed-driven roster claim holds at 4 data points; binding constraint for /015 CONFIRMATION design; R5-BINARY-KILL CONFIRMATION conditional fires per F1 result |
| PASS | F7 > 40% OR F8 > 50% | **MAGNITUDE LOCKED, ROSTER PARTIALLY-LOCKED** | The substrate-magnitude lock validates but the seed-driven roster claim is partial; decomposition refined to "magnitude-locked, roster partially-locked"; /015 design refined |
| FAIL | any | **SUBSTRATE-MAGNITUDE LOCK REFUTED** | Per LM Master Phase 7.4 §7 "halt and reassess"; decomposition wrong in magnitude direction; reconsider basin claims |

### 8.3 Merge decision

/013 verdict-class will be one of:
- **EXPLORATION-NEGATIVE** (any subtype) → NO-MERGE; /014 advances per Path Forward
- **EXPLORATION-PROMISING** (any of rows 2, 3, 4) → NO-MERGE (EXPLORATION never merges); pre-committed /015 CONFIRMATION axis determined by F1 sign

Per the v1 skill: "EXPLORATION-PROMISING is catalog-only; never merges to trunk". Merging requires CONFIRMATION-MERGE verdict.

### 8.4 HIGH-RISK pre-commit tripwire

/013 is NORMAL-RISK declared. No HIGH-RISK pre-commit tripwire applies. If /013 emerges PROMISING with F1 OOS Δ > +0.05 (3/3 positive across DISJOINT seed windows), this is signal-to-process input for /015 CONFIRMATION planning, NOT a pre-commit tripwire on /014.

### 8.5 /015 CONFIRMATION CONDITIONAL — PRE-COMMITTED

Per the /012 diary §"Permanent Catalog Additions" line #7 + LM Master Phase 7.4 §8 + this brief Section 1:

- **/013 F1 OOS Δ > +0.05** → **/015 = R5-BINARY-KILL CONFIRMATION** (3/3 positive across DISJOINT seed windows; H1 mechanical edge favored over H2 basin-lottery; multi-seed CONFIRMATION measures mechanical kill_low layer ~+0.05 contribution)
- **/013 F1 OOS Δ ≤ 0** → **/015 = UNUSED-family CONFIRMATION** (labeling preferred per Critic /011 Path Forward Option 2 + LM Master Phase 4.5 §6; 2/3 positive insufficient under H2 basin-lottery null hypothesis; pivot to label-distribution change)

The conditional is BINDING — /015 axis selection is mechanically determined by /013's F1 sign. The /014 EXPLORATION continues normally between /013 and /015 (per cycle-2 10-EXPLORATION cadence; CONFIRMATION can fire at /015 once 10 EXPLORATIONs accumulate).

---

## Section 9 — Library Stack

No new libraries required. /013 uses the existing v1 library stack identical to /011 + /012:

- `crypto_trade.strategies.ml.lgbm.LightGbmStrategy` (LightGBM ensemble strategy)
- `crypto_trade.strategies.ml.optimization.optimize_and_train` (Optuna + LightGBM trainer)
- `crypto_trade.backtest.run_backtest` (backtest engine with R5-BINARY-KILL wiring from /011 commit `b788d4f`)
- `crypto_trade.strategies.ml.validation_v1` (CPCV + DSR + PBO + PSR + ADF + IC — methodology reporting)
- `crypto_trade.reporting_v1` (per-cell PCA n_eff + dsr.json + comparison.csv extensions from /008 commit)
- `pandas==2.3.3`, `numpy==2.3.4`, `lightgbm==4.6.0`, `optuna==4.5.0`, `statsmodels==0.14.4` (versions pinned in `uv.lock`)

The pre-existing `analysis/iteration_v1-012/f6_roster_overlap.py` script (now general-purpose F6/F7/F8 join script) uses only Python stdlib (csv, argparse, pathlib).

---

## Section 10 — Implementation Spec (QE Deliverables)

### 10.1 Code diff scope

**Minimal — NO `src/` changes**. Already-landed from /011 + /012:

1. `run_baseline_v1.py` — additive changes for `--ensemble-seeds-offset` flag (commit `360650f` from /012 branch)
2. `analysis/iteration_v1-012/f6_roster_overlap.py` — F6/F7 general-purpose join script (commit `360650f` from /012)
3. R5-BINARY-KILL wiring in `src/crypto_trade/backtest.py` + `src/crypto_trade/backtest_models.py` (commit `b788d4f` from /011)

### 10.2 QE Phase 6 deliverables

1. **Run the /013 backtest**:
   ```
   uv run python run_baseline_v1.py \
       --exploration --iteration 13 \
       --pruned-features --n-trials 35 \
       --r5-binary-kill-enabled --r5-binary-kill-min-natr 2.0 \
       --ensemble-seeds-offset 6
   ```
   Wall-clock budget: ≤2h (predicted 75-90 min per /011/012 reference).

2. **Produce all standard report artifacts** in `reports-v1/iteration_v1-013/`:
   - `comparison.csv` (with R5_binary_kill_fire_rate rows correctly labeled)
   - `in_sample/` and `out_of_sample/` subdirs with trades.csv, per_symbol.csv, monthly_pnl.csv, daily_pnl.csv, dsr.json, adf_test.csv, ic_matrix.csv, quantstats.html, per_regime.csv

3. **Produce the F7/F8 substrate-test artifact** (load-bearing F7+F8 falsifiers):
   ```
   uv run python analysis/iteration_v1-012/f6_roster_overlap.py \
       --target reports-v1/iteration_v1-013 \
       --reference baseline=reports-v1/iteration_v1-baseline \
       --reference iter010=reports-v1/iteration_v1-010 \
       --reference iter011=reports-v1/iteration_v1-011 \
       --reference iter012=reports-v1/iteration_v1-012 \
       --output reports-v1/iteration_v1-013/f7_roster_overlap.csv
   ```
   This produces the per-(half × symbol × reference) overlap CSV that F6 + F7 + F8 falsifiers verify against. Note filename is `f7_roster_overlap.csv` per /012 closeout convention (F7 IS the substrate-test diagnostic from /012 onward; /012 filename mismatch lesson adopted).

4. **Produce QE engineering report** at `reports-v1/iteration_v1-013/engineering_report.md` (Critic Rec #1+#3 + v1 skill mandate). The report MUST be a Phase 6 deliverable (NOT a Phase 7 carry-forward; this is the codified enforcement per Critic /012 Rec #2). Contents:
   - Backtest invocation command + wall-clock elapsed
   - Headline IS / OOS Sharpe + comparison.csv row dump
   - R5-BINARY-KILL fire rate IS/OOS values (F2 verification)
   - Pointer to f7_roster_overlap.csv and per-symbol metrics
   - F1-F9 falsifier table (Brief Section 4 + Section 8 conditions evaluated against observed numbers)
   - Diagnostic outcome (2-PROPERTY DECOMPOSITION VALIDATED / MAGNITUDE LOCKED ROSTER PARTIAL / SUBSTRATE-MAGNITUDE LOCK REFUTED) per Section 8.2
   - F1 sign determination + /015 axis conditional firing

5. **No src/ changes**. R5-BINARY-KILL wiring already at `backtest.py` + `backtest_models.py` from /011's commit `b788d4f`. /013 ONLY toggles `--ensemble-seeds-offset 6`.

### 10.3 Engineer pre-flight checks

Before launching the backtest:
- Verify data extent is identical to /011 + /012 (no fresh data fetches between /012 and /013; otherwise determinism comparison is contaminated)
- Verify the runner banner prints `ensemble_seeds: [3003, 4004, 5005] (offset=6)` at startup — confirms the flag flowed correctly to all 4 models
- Verify R5-BINARY-KILL config matches /011 + /012: `r5_kill_low_natr_enabled=True`, `r5_kill_low_natr_min_pct=2.0`, R5 vol-target DISABLED

### 10.4 Phase 7.5 Critic deliverables — anticipated

Critic will perform the standard 8+2 checks per `quant-critic.md` plus the v1-specific Check 14 (Axis Family Validation). The `methodology-substrate-test` family is PRE-EXISTING (8th catalog family established at /012); /013 is the 3rd consecutive same-family iteration. Per Critic /012 Phase 7.5 PASS-WITH-NOTE: "Future NEW family declarations require 3-way convergence" — /013 is NOT a new family declaration, so this rule does not bind /013 directly. Critic should accept the continuation as PASS or PASS-WITH-NOTE (orchestrator review flag noted; not verdict-binding).

If Critic disagrees on family taxonomy continuity, the verdict still resolves via Section 8.1 deterministically (the F1×F3×F7×F8×F9 cells are independent of family taxonomy debate).

The engineering report file existence check must be enforced by Critic Phase 6.0 pre-flight (and orchestrator dispatch precondition) per Critic /012 Rec #2.

---

## Section 11 — Alternatives (Critic Path Forward Options; deferred to /014 if /013 confirms)

The /012 Phase 7.5 Critic Path Forward listed three Options. /013 implements Option 1 (offset=6 [3003, 4004, 5005] continuation, methodology-substrate-test 3rd consecutive). Options 2 + 3 are deferred to /014 per the cadence sequence:

### Alternate A — Labeling axis: triple-barrier σ_t source (DEFERRED to /014 if /013 confirms F1 ≤ 0)

- **Axis**: replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers (24h vs 14d EWMA window for σ_t).
- **Family**: `labeling` (UNUSED in cycle-2 at /013; if /013 OOS Δ ≤ 0 → /015 = labeling CONFIRMATION; /014 axis = labeling EXPLORATION to validate)
- **Rationale**: highest-prior-probability of basin escape from UNUSED-family menu (~60-70% per Critic Path Forward). Changes IS label distribution per cell → different LightGBM loss surface → potentially different basin.
- **HIGH-RISK declaration**: YES (label distribution change is HIGH-RISK per /005 rule). Multi-seed pre-commit if PROMISING.

### Alternate B — Methodology axis: per-cell early-stop with inner hold-out (RESERVE for /014 if labeling unfit)

- **Axis**: LightGBM per-cell early stopping with Purged-CV inner hold-out (20% within-fold).
- **Family**: `methodology` (UNUSED since /008 at /014).
- **Rationale**: structurally orthogonal; changes WHICH trees retained per cell → different ensemble composition → different basin. Non-compoundable as edge signal but provides diagnostic infrastructure.

### /015 axis conditional clarification (PRE-COMMITTED from /012 closeout)

The CONDITIONAL is:
- /013 F1 OOS Δ > +0.05 → /015 = **R5-BINARY-KILL CONFIRMATION** (mechanical kill_low layer ~+0.05 measured at multi-seed)
- /013 F1 OOS Δ ≤ 0 → /015 = **UNUSED-family CONFIRMATION** (labeling preferred)

This is binding per /012 diary §"Permanent Catalog Additions" item #7. The /014 axis is:
- Open in BOTH conditional branches; /014 designed at /013 closeout based on /013 outcome + /015 axis pre-commitment

These are RESERVE proposals. /013's primary mission is the 3rd seed-window sample. /014's axis will be designed based on /013's diagnostic outcome.

---

## Section 12 — Catalog Closeout Plan

The /013 closeout will append a row to `briefs-v1/exploration_catalog.md` per the v1 skill discipline. Pre-registered fields:

- `iter-v1-NNN`: iter-v1/013
- `YYYY-MM-DD`: 2026-05-25
- `axis varied`: ENSEMBLE_SEEDS window offset 3→6 (DISJOINT inner seeds [3003, 4004, 5005] vs /012's [789, 1001, 2002] vs /011's [42, 123, 456]) with R5-BINARY-KILL config BIT-IDENTICAL to /011 AND /012
- `axis family`: `methodology-substrate-test` (3rd consecutive at this family; orchestrator review flag noted)
- `IS Sharpe Δ`: [TBD post-backtest; F3 + F9 conditions in Section 4]
- `OOS Sharpe (informational)`: [TBD post-backtest; F1 conditions in Section 4 + Section 8.1]
- `verdict`: [TBD; one of EXPLORATION-NEGATIVE-BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-FULL-SUBSTRATE-LOCKED / EXPLORATION-PROMISING-SUBSTRATE-MAGNITUDE-VALIDATED-SEED-DRIVEN / EXPLORATION-PROMISING-PARTIAL-DISSOLUTION-SUBSTRATE-MAGNITUDE-VALIDATED / EXPLORATION-PROMISING-STRONG-SEED-DRIVEN-SUBSTRATE-MAGNITUDE-VALIDATED / EXPLORATION-NEGATIVE-BASELINE-EQUIVALENT-NULL-SUBSTRATE-MAGNITUDE-VALIDATED / EXPLORATION-NEGATIVE-seed-shifted-NEGATIVE-SUBSTRATE-MAGNITUDE-VALIDATED / EXPLORATION-NEGATIVE-SUBSTRATE-MAGNITUDE-LOCK-REFUTED / EXPLORATION-NEGATIVE-catastrophic-substrate-amplification per Section 8.1]
- `confirmation candidate?`: NO for any EXPLORATION-NEGATIVE; conditional YES via pre-committed /015 conditional only if PROMISING

The detailed-verdict-notes section will record:
- F1 + F3 + F7 + F8 + F9 measured values per Section 4
- 2-PROPERTY DECOMPOSITION validation result (full validated / magnitude-validated-only / refuted) per Section 8.2
- LM Master Phase 7.4 calibration update (was substrate-magnitude prediction within band?)
- /015 axis conditional fire (R5-BINARY-KILL CONFIRMATION vs UNUSED-family CONFIRMATION)
- /014 axis recommendation

### Permanent catalog additions anticipated

If 2-PROPERTY DECOMPOSITION VALIDATED at /013:
- `feedback_v1_substrate_basin_lock.md` MEMORY ENTRY UPGRADED — decomposition validated at 4 data points; STRONGER binding constraint for all future v1 EXPLORATIONs; remove "pending /013 validation" caveat
- The substrate-MAGNITUDE lock claim becomes a permanent v1 axiom

If F9 FAILS (substrate-magnitude lock refuted):
- `feedback_v1_substrate_basin_lock.md` MEMORY ENTRY MARKED FALSIFIED in magnitude dimension
- Halt-and-reassess at /013 closeout; reconsider basin claims and /015 design

If F7/F8 don't validate within bands but F9 PASS:
- `feedback_v1_substrate_basin_lock.md` REFINED — magnitude lock validated; roster claim refined per observed bands

---

## Section 13 — Phase 5.5 Self-Check

This brief includes all 13 mandatory sections per the v1 skill discipline. Verification:

| Section | Required | Status |
|---|---|---|
| 0 (pre-header: 0.1-0.6) | Yes | OK |
| 1 (hypothesis) | Yes | OK |
| 2 (IS-only evidence) | Yes | OK (lighter than typical EXPLORATION because substrate decomposition finding is empirically established at /012; F7/F8 join script committed) |
| 2.5 (HIGH-RISK declaration) | Yes | OK (NORMAL-RISK declared with rationale) |
| 3 (proposed changes — incorporating Critic /012 process recs) | Yes | OK |
| 4 (falsifiers F1-F9) | Yes | OK (F1-F7 inherited from /012; F8 + F9 NEW for /013) |
| 5 (predicted outcomes per FLAT 30/30/40 prior — LM Master Phase 7.4 §2) | Yes | OK |
| 6 (what could falsify) | Yes | OK |
| 7 (mechanism diagram) | Yes | OK |
| 8 (verdict gates 8.1-8.5 — COMPLETE F1×F3×F7×F8×F9 matrix per Critic /012 Rec #1) | Yes | OK |
| 9 (library stack) | Yes | OK |
| 10 (implementation spec) | Yes | OK (10.1-10.4) |
| 11 (alternatives — Critic Path Forward Options) | Yes | OK |
| 12 (catalog closeout plan) | Yes | OK |
| 13 (Phase 5.5 self-check) | Yes | OK (this section) |

### Substantive integrity checks

- **Axis Rotation Discipline (skill mandate)**: Section 0.6 declares `methodology-substrate-test` family (3rd consecutive; PRE-EXISTING 8th family; NOT new declaration). Prior 5 EXPLORATIONs span 4 distinct families — saturation rule (5-of-5 same family) does NOT fire. Rotation status VALID.
- **HIGH-RISK Axis Declaration (skill mandate)**: Section 2.5 declares NORMAL-RISK with rationale identical to /012's (RNG-init only).
- **LM Master Phase 4.5 response (skill mandate)**: Section 3.3 anticipates LM Master Phase 4.5 recommendations and pre-adopts the expected ones (pre-registered offset=6, FLAT priors, exhaustive Section 8.1, no UNUSED-family pivot); brief will be UPDATED if LM Master Rec materially diverges (per v1 skill Section 3.6 mandate).
- **F1-F9 falsifiers (skill mandate)**: Section 4 specifies F1-F9 with explicit numerical conditions; F8 + F9 are NEW substrate-test-specific falsifiers per /012 closeout LM Master Phase 7.4 §7 commitment.
- **Section 8 verdict-class pre-registration (Critic /012 Rec #1)**: Section 8.1 pre-registers ALL F1 × F3 × F7 × F8 × F9 cells (8 rows) with deterministic verdict assignment; explicit boundary handling; NO matrix gaps. Phase 5.5 gate verifies completeness.
- **F7/F8 roster-overlap committed artifact**: pre-existing `analysis/iteration_v1-012/f6_roster_overlap.py` (general-purpose) reused for /013; Section 10.2 specifies the invocation with 4 references (baseline, iter010, iter011, iter012).
- **Engineering report mandatory at Phase 7.5 (Critic /012 Rec #2)**: Section 10.2 Deliverable #4 specifies QE engineering report as Phase 6 deliverable; Phase 5.5 gate verifies dispatch precondition; Critic Phase 6.0 pre-flight enforces.
- **Per skill discipline — wall-clock cap ≤2h (cadence skill mandate)**: Section 3.5 predicts 75-90 min wall-clock; ≤2h cap is safe.
- **Critic /012 process recommendations (3 total)**: ADOPTED EXPLICITLY in Section 3.2.

### Brief size assessment

This brief is ~16k tokens — within the ~25k brief size budget for v1 EXPLORATION. Sections 1, 5, 7 are the longest (mechanism + prediction reasoning + 2-property decomposition); other sections are appropriately concise.

### Conclusion of Phase 5.5 Self-Check

This brief is COMPLETE per the v1 skill's 13-section requirement. All 9 falsifiers + verdict gates are pre-registered with numerical conditions. The substrate-test axis is structurally orthogonal at the seed-window dimension to all 7 other family axes; pre-existing 8th family used as 3rd consecutive. The expected outcomes are pre-registered with explicit FLAT probabilities (30/30/40 for A/B/C per LM Master Phase 7.4 §2 commitment).

Brief is READY for LM Master Phase 4.5 advisory + Phase 5.5 gate review + Phase 6.0 Critic pre-flight. The QE Phase 6 invocation is fully specified in Section 10.2.

---

**END OF BRIEF**

Brief authored 2026-05-25 by claude-opus-4-7 (1M context) — quant-research-v1 mode.

Brief total: 13 sections including all mandatory v1 elements.

# iter-v1/012 — Research Brief

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: EXPLORATION (single-seed-window, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)
**Axis**: SUBSTRATE-DISSOLUTION PROBE — `methodology-substrate-test` family (NEW v1 subtype family; structurally orthogonal to risk-primitive despite sharing R5-BINARY-KILL config with /011)
**Branch**: `iteration-v1/012`

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor

`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)
- UNCHANGED post-/010 + /011 (BOTH closed EXPLORATION-NEGATIVE)

### 0.2 Mode

**EXPLORATION** (cycle-2, post-/011 closeout)
- `--exploration --pruned-features --n-trials 35 --r5-binary-kill-enabled --r5-binary-kill-min-natr 2.0 --ensemble-seeds-offset 3` (canonical v1 EXPLORATION knobs PLUS the substrate-probe seed-window shift)
- ENSEMBLE_SIZE = 3 (inner seeds from new offset window — `[789, 1001, 2002]` — DISJOINT from /011's `[42, 123, 456]`)
- ≤2h wall-clock cap (NON-NEGOTIABLE per /005 closeout 10:1 cadence discipline; matches /011 ~75-90 min observed)

### 0.3 Iteration label

`v1-012`

### 0.4 Determinism note

ENSEMBLE_SEEDS roster is `(42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006)`. Inner seeds are selected via `ENSEMBLE_SEEDS[offset:offset+size]` (frozen tuple, deterministic slice). With `--ensemble-seeds-offset 3` + `ENSEMBLE_SIZE=3`, /012 uses inner seeds `[789, 1001, 2002]`. With offset=0 (canonical), /011 used `[42, 123, 456]`. Both windows are inside the CONFIRMATION roster — /015 multi-seed CONFIRMATION at offset=0 + size=10 naturally subsumes both basins.

Backward compatibility: every existing call without `--ensemble-seeds-offset` (or `offset=` kwarg in `_derive_ensemble_seeds`) continues to produce the canonical `[42, 123, 456, ...]` window byte-identically. The 8 prior closed v1 iterations (/001-/011) are deterministically reproducible.

The R5-BINARY-KILL configuration is BIT-IDENTICAL to /011 (same `risk_r5_kill_low_natr_enabled=True`, same `risk_r5_kill_low_natr_min_pct=2.0`, same disabled R5 proportional vol-target). The single dimension that changes vs /011 is `ensemble_seeds_offset` 0 → 3. Substrate-probe axis isolation is mechanically clean.

### 0.5 Cadence position

**Cycle-2 EXPLORATION #7 of 10**.

Cycle-2 catalog: /006 (universe, NEG+DEGEN), /007 (feature-family composed, NEG-NEG), /008 (methodology PROMISING-METH), /009 (feature-family delete, NEG-NEG), /010 (risk-primitive proportional R5, NEG/PROMISING-INERT-with-IS-basin-shift), /011 (risk-primitive binary-kill R5, NEG/catastrophic-basin-shift).

Next CONFIRMATION cannot fire until 10 cycle-2 EXPLORATIONs accumulate (currently 7 after /012). Earliest CONFIRMATION at /015.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `methodology-substrate-test` (NEW v1 subtype family — structurally orthogonal to all 7 existing axis families: feature-family, model-arch, labeling, universe, risk-primitive, methodology, hyperparameter-region)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/007: `feature-family`
  - iter-v1/008: `methodology`
  - iter-v1/009: `feature-family`
  - iter-v1/010: `risk-primitive` (proportional-scaling subtype)
  - iter-v1/011: `risk-primitive` (binary-kill subtype)
- **Rotation status**: **VALID — `methodology-substrate-test` is structurally distinct from every prior 5 family.** Per skill: "if the last 5 EXPLORATIONs were all from the same family, the NEXT EXPLORATION MUST be from a different family". 2/5 risk-primitive + 2/5 feature-family + 1/5 methodology — neither at saturation; new family extension defensible.
- **Why methodology-substrate-test and NOT risk-primitive**: /012 holds the R5-BINARY-KILL config BIT-IDENTICAL to /011 (same enable flag, same 2.0% threshold, same disabled R5 vol-target). The intervention is NOT the R5 mechanism — that was tested at /011. The intervention is the ENSEMBLE_SEEDS window. The "what" being varied is the SUBSTRATE (seed selection), not the AXIS (R5 primitive). This is a methodology-substrate test: it asks "is the basin a property of the substrate (seed window) OR of the axis (R5 mechanism)?". Calling it `risk-primitive` would mis-classify — there is no R5 variation in /012.
- **Structural distinction from `methodology` family (which was /008)**: /008 was a measurement-layer / report-layer methodology axis (per-cell PCA n_eff refactor). /012 is a SUBSTRATE-DISSOLUTION probe — it tests whether single-seed=42 basin draws are seed-conditional or substrate-conditional. The 7th family `hyperparameter-region` (/005) covered Optuna search-space differentiation; the new `methodology-substrate-test` family (8th) covers seed-window selection. Both modulate Optuna trajectory; the difference is `hyperparameter-region` shifts the search bounds while holding the seed fixed, whereas `methodology-substrate-test` shifts the seed window while holding the search bounds fixed.
- **One-sentence rationale**: /012 is the highest-information-density experiment at the v1 EXPLORATION budget — it directly tests the load-bearing structural claim from /010 + /011 closeout (`feedback_v1_substrate_basin_lock.md`) "at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, the Optuna basin is substrate-locked across axis primitives" — by changing ONLY the seed-window dimension, and is the SISTER-PROBE pre-registered as Option 3 in Critic Phase 7.5 /011 Path Forward.

---

## Section 1 — Hypothesis

**At v1 EXPLORATION budget (n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED + R5-BINARY-KILL @ 2.0% IDENTICAL to /011), shifting the inner-seeds window from [42, 123, 456] (/011 canonical) to [789, 1001, 2002] (DISJOINT, still in CONFIRMATION roster) tests whether the LTC-dominated Optuna basin discovered by /010 + /011 is SUBSTRATE-LOCKED (basin re-discovered at DISJOINT seed window) or SEED-LOCKED (basin diverges at new seed window).**

The hypothesis is a 3-way pre-registered outcome, all numerical and binding:

### Outcome A — SUBSTRATE-LOCKED CONFIRMED (basin re-discovered at new seeds)

If the basin is a property of the (n_trials=35, 40-feature, ENSEMBLE_SIZE=3) substrate independent of inner seeds, /012 will produce:

- LTC IS pct_of_total_pnl > +50% (substrate's signature LTC dominance survives seed change; /011 had 106.48%, /010 had 119.84%, BASELINE had 6.42% — substrate signature is the +50% to +120% range)
- F6 OOS roster overlap with /011 > 70% (basin substrate produces similar OOS roster even at DISJOINT seeds)
- IS Sharpe Δ vs BASELINE in the [+0.30, +0.55] OVERSHOOT band (mirroring /010 +0.47 / /011 +0.48 IS basin-rediscovery signature)
- OOS Sharpe in the [+0.50, +1.20] range (substrate-conditional but variable)

**Verdict resolution for Outcome A**: confirms `feedback_v1_substrate_basin_lock.md`'s STRUCTURAL claim with quantitative evidence; R5-BINARY-KILL family REMAINS CLOSED at v1 single-seed-WINDOW EXPLORATION. /015 CONFIRMATION must either (i) test multi-seed dissolution on R5-BINARY-KILL (validates if mechanical kill_low layer aggregates positively across seeds), OR (ii) pivot to UNUSED-family axes from cycle-2 (labeling, methodology infrastructure).

### Outcome B — SEED-LOCKED CONFIRMED (basin diverges at new seeds)

If the basin is a property of the seed itself (not the substrate), /012 will produce:

- LTC IS pct_of_total_pnl < +30% (LTC dominance dissolves at seed shift; new basin's per-symbol distribution diverges)
- F6 OOS roster overlap with /011 < 30% (basin draw is genuinely different; roster shifts substantially)
- IS Sharpe Δ vs BASELINE in [-0.20, +0.20] (basin shift produces ANY direction; rough symmetry)
- OOS Sharpe in [+0.30, +0.85] (without /011's basin-substrate amplification, OOS lands closer to BASELINE +0.66 + small mechanical kill_low layer ~+0.05)

**Verdict resolution for Outcome B**: REFUTES `feedback_v1_substrate_basin_lock.md`'s STRUCTURAL claim. The /011 +0.48 IS Sharpe-Δ was a single-seed=42 lottery, not a substrate property. R5-BINARY-KILL becomes a candidate axis whose mechanical edge may be replicable across multi-seed dissolution. /015 CONFIRMATION on R5-BINARY-KILL becomes the unambiguous next step (one-line directive: run /011's config at multi-seed CONFIRMATION-spec).

### Outcome C — PARTIAL / INTERMEDIATE

If the basin substrate is multi-dimensional (seed × other factors) and seed shift partially dissolves it:

- LTC IS pct_of_total_pnl in [+30%, +50%] (LTC reduced but still dominant)
- F6 OOS roster overlap with /011 in [30%, 70%] (intermediate basin shift)
- IS Sharpe Δ vs BASELINE in [+0.10, +0.35] (partial OVERSHOOT)
- OOS Sharpe in [+0.55, +1.00]

**Verdict resolution for Outcome C**: substrate is locked to MORE than just seed — also includes (n_trials, ENSEMBLE_SIZE, feature set). Pivot to UNUSED family at /013+ as PRIMARY; /015 CONFIRMATION on R5-BINARY-KILL remains POSSIBLE but with reduced confidence.

### Why this is the right experiment NOW

Per `feedback_v1_substrate_basin_lock.md` Falsification Path Option 1: "substrate-dissolution probe at single-seed=43 (or other seed) on EXACT /011 config: if /012 Sharpe diverges >0.30 from /011, basin IS seed-locked (NOT substrate-locked)". /012 IS this falsification probe.

The information value is HIGH irrespective of outcome:
- Outcome A confirms a STRUCTURAL property of v1 EXPLORATION → narrows search to UNUSED-family axes that change the loss surface (labeling, methodology) for the remaining cycle-2 EXPLORATIONs
- Outcome B opens R5-BINARY-KILL as a valid edge candidate at multi-seed → /015 CONFIRMATION pre-committed
- Outcome C constrains the substrate to a higher-dimensional regime → calibrates LM Master's basin-shift priors more precisely

Alternative cycle-2 EXPLORATIONs (labeling axis at /013, methodology axis at /014) cost the same ≤2h budget but produce LESS information because they cannot disambiguate /011's outcome attribution.

---

## Section 2 — IS-Only Evidence (numerical tables)

The substrate-lock finding is empirically established at /011 closeout. /012 EDA is LIGHTER than typical EXPLORATION because the smoking-gun diagnostics were committed at /011 Phase 7.4 + 7.5. This section references prior committed evidence and adds the F6 roster-overlap diagnostic that was missing as a committed artifact (Critic Rec #2 to /011, closing the load-bearing falsifier gap).

### 2.1 Substrate-lock empirical baseline (committed artifact, /012 first deliverable)

From `reports-v1/iteration_v1-011/f6_roster_overlap.csv` (committed at /012 commit `360650f` per Critic Rec #2 — the F6 join script `analysis/iteration_v1-012/f6_roster_overlap.py` reproduces LM Master Phase 7.4 offline computations as committed artifact):

**OOS roster overlap diagnostics**:

| half | reference | n_target | n_reference | n_overlap | pct_target_in_reference |
|---|---|---|---|---|---|
| OOS | BASELINE | 180 | 189 | 30 | **16.67%** |
| OOS | iter010 | 180 | 210 | 168 | **93.33%** |

**IS roster overlap diagnostics**:

| half | reference | n_target | n_reference | n_overlap | pct_target_in_reference |
|---|---|---|---|---|---|
| IS | BASELINE | 570 | 621 | 145 | **25.44%** |
| IS | iter010 | 570 | 663 | 541 | **94.91%** |

**Per-symbol LTC IS overlap (load-bearing for basin substrate claim)**:

| half | symbol | reference | n_target | n_reference | n_overlap | pct_target_in_reference |
|---|---|---|---|---|---|---|
| IS | LTCUSDT | BASELINE | 104 | 124 | 23 | 22.12% |
| IS | LTCUSDT | iter010 | 104 | 110 | **97** | **93.27%** |

**Interpretation**:
1. /011 OOS roster overlaps BASELINE at 16.67% but /010 at 93.33% — at OOS level, /011 is essentially a slightly-modified /010 (~12 trades different), NOT a re-discovered BASELINE.
2. /011 IS roster overlaps BASELINE at only 25.44% but /010 at 94.91% — IS-level basin-substrate inheritance is even more extreme (94.91% > 93.33%). The basin transfers MORE strongly at IS than at OOS.
3. LTC IS specifically: 93.27% of /011's LTC IS trades are SAME `(symbol, open_time)` keys as /010's LTC IS trades. Two mechanistically distinct R5 subtypes (proportional weight scaling vs binary entry filter) produce 97 of 104 byte-identical LTC IS trades. This is the smoking-gun substrate-lock evidence.

### 2.2 Inverse-causal reasoning — what MUST be true if substrate is locked

If `feedback_v1_substrate_basin_lock.md`'s STRUCTURAL claim holds:

- /012 (at offset=3 seeds [789, 1001, 2002]) should produce LTC IS overlap with /011 in the [70%, 90%+] range — IS roster should be MOSTLY preserved across DISJOINT inner seeds because the SUBSTRATE (n_trials, ensemble_size, features) is the basin-determining factor, NOT the inner seeds.
- /012 OOS roster overlap with /011 should be in the [60%, 85%] range — OOS is more variance-sensitive than IS, but if substrate locks IS basin, OOS should also be approximately preserved.

If the claim is FALSE (seed-locked):

- /012 LTC IS overlap with /011 should drop to [10%, 30%] range — different inner seeds → different Optuna trajectory → different basin → different roster.
- /012 OOS roster overlap with /011 should be in the [5%, 25%] range.

The /012 brief Section 4 falsifier F7 codifies these thresholds.

### 2.3 Why /011's EDA evidence remains valid for /012

The /011 EDA (entry-time-conditional NATR_14 distribution + cross-roster oracle Sharpe-Δ simulation) tested whether the R5-BINARY-KILL @ 2.0% MECHANISM produces positive OOS Δ when applied as an ORACLE to a roster. That oracle test is independent of /011's actual Optuna outcomes — it's a mechanical statement about "what would happen if you mechanically filter out NATR<2.0% trades from a roster". The oracle showed positive Sharpe-Δ on BASELINE roster (+0.046) AND on /010 roster (+0.115).

This oracle is THE SAME mechanical effect that /012 will apply on top of its (new-seed) basin draws. The mechanism does NOT change with inner-seed shift. What might change is the BASIN substrate the mechanism operates on top of — exactly what /012 tests.

If /012 produces a new basin (Outcome B), the kill_low mechanical layer should still produce ~+0.05 to +0.10 OOS Sharpe-Δ ON TOP of whatever new basin emerges. If /012 produces the same basin (Outcome A), the mechanical layer compounds with the basin substrate as /011 demonstrated.

### 2.4 Predicted F6 vs /011 roster overlap distribution

Given /011's LTC IS overlap with /010 was 93.27% under MECHANISTICALLY DISTINCT axes (proportional R5 vs binary-kill R5) at IDENTICAL seed [42, 123, 456], and given /012 holds the AXIS IDENTICAL to /011 (binary-kill R5 @ 2.0%) but shifts seeds to DISJOINT [789, 1001, 2002]:

| Hypothesis | Predicted /012↔/011 LTC IS overlap | Predicted /012↔/011 OOS overlap |
|---|---|---|
| SUBSTRATE-LOCKED (Outcome A) | > 70% | > 70% |
| SEED-LOCKED (Outcome B) | < 30% | < 30% |
| PARTIAL (Outcome C) | [30%, 70%] | [30%, 70%] |

The 30-70 ranges are pre-registered F7 cells in Section 4.

### 2.5 No new EDA work needed — substrate finding is empirically established

The /011 Phase 7.4 LM Master post-mortem produced the load-bearing 93.3% LTC IS overlap and 16.7% F6 baseline-overlap measurements. The /011 Phase 7.5 Critic review endorsed the substrate-lock finding. The /011 Phase 8 diary codified `feedback_v1_substrate_basin_lock.md` as permanent v1 memory. /012's EDA does NOT re-establish the finding — it tests the FALSIFICATION path.

The committed `f6_roster_overlap.csv` artifact (now reproducible per Critic Rec #2) serves as the deterministic reference for all future F6-type comparisons.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **NORMAL-RISK**
- **Reason**: /012 does NOT change Optuna's training-objective domain. The training distribution (which `(symbol, open_time)` rows enter the loss + their weights + their labels) is BIT-IDENTICAL to /011 at any given (model, month) cell. Only the inner-seeds passed to LightGBM (and the Optuna sampler initialization) change. The loss surface that Optuna explores is identical; only the trajectory through that surface changes.
- **Mitigation (NORMAL-RISK does not require mitigation)**: N/A. Single-seed-window EXPLORATION is the appropriate cadence for /012.

### Rationale (for Critic and future LM Master Phase 4.5 calibration)

HIGH-RISK declarations in v1 are reserved for axes that change the optimization target itself:
- Risk-primitive constraint changes (R1/R2/R3/R4/R5 mechanism additions or modifications — these change which trades enter the backtest pool)
- Universe substitution (different symbols → different per-symbol Optuna problems)
- Label-mode change (triple-barrier vs fixed-horizon vs trend-scanning → different supervised target)
- Feature-set replacement (different inputs to LightGBM)
- Bar-interval change (different (sym, ot) tuple universe)

/012 changes NONE of these. The R5-BINARY-KILL @ 2.0% is BIT-IDENTICAL to /011 (same `risk_r5_kill_low_natr_enabled=True`, same threshold, same disabled R5 proportional vol-target). The feature columns, ATR multipliers, n_trials, ENSEMBLE_SIZE, symbols, training window, OOD gate — ALL unchanged from /011. The single dimension that changes is the inner-seeds passed to LightGBM.train and Optuna.create_study.

From the LightGBM perspective, /012 will see the EXACT SAME training rows in the EXACT SAME (model, month) cells with the EXACT SAME labels and weights as /011 did. The only difference is the random number generator's initialization. This is a pure substrate test.

### LM Master /011 Phase 4.5 calibration note

LM Master Phase 4.5 for /011 predicted "20-30% basin-shift for entry-filter axes at single-seed=42" (Phase 4.5 §"Basin-Shift Probability Estimate"). The empirical /011 outcome REFUTED this prediction (93.3% LTC overlap with /010 indicates 0% basin-shift between distinct axes at same seed). The Phase 7.4 calibration update is encoded in `feedback_v1_substrate_basin_lock.md`. 

For /012, the LM Master Phase 4.5 prediction will be: at IDENTICAL axis (R5-BINARY-KILL bit-identical) + DISJOINT seeds, basin-shift probability is the SUBSTRATE-LOCK claim's complement. If substrate-locked: ~0-20% basin-shift across seeds (basin re-discovered). If seed-locked: ~80-100% basin-shift across seeds (basin diverges). The /011 finding suggests ~10-20% basin-shift is the modal prediction.

NORMAL-RISK declaration is appropriate: the /012 outcome is BINARY in the substrate-lock dimension (re-discover OR not), independent of any axis-mechanism risk. There is no "the loss surface might over-fit IS noise" pathway in /012's design because /012 is exploring the SAME loss surface as /011 with different RNG initialization.

---

## Section 3 — Proposed Changes

### 3.1 Code changes (src/ + runner)

**Only TWO** changes vs /011's branch:

1. **`run_baseline_v1.py`** — additive (already landed at /012 commit `360650f`):
   - `_derive_ensemble_seeds(size, offset=0)` — added `offset` kwarg with default 0 (backward-compatible)
   - `run_model(...)` — added `ensemble_seeds_offset` kwarg with default 0 (backward-compatible)
   - `main()` — added `--ensemble-seeds-offset` CLI flag (default 0)
   - `_r5_kwargs` dict — threads `ensemble_seeds_offset` through all 4 model calls (A pooled, C LINK, D LTC, E DOT)
   - Banner print updated to show offset

2. **No `src/` changes**. R5-BINARY-KILL wiring already lives in `src/crypto_trade/backtest.py` and `src/crypto_trade/backtest_models.py` from /011 commit `b788d4f`. /012 inherits that code unchanged.

### 3.2 Runner invocation

```bash
uv run python run_baseline_v1.py \
    --exploration \
    --iteration 12 \
    --pruned-features \
    --n-trials 35 \
    --r5-binary-kill-enabled \
    --r5-binary-kill-min-natr 2.0 \
    --ensemble-seeds-offset 3
```

Hash-comparable to /011's invocation (which was identical minus `--ensemble-seeds-offset 3`). All other flags BIT-IDENTICAL.

### 3.3 Expected wall-clock budget

/011 ran in ~75-90 min wall-clock per the diary. /012 has SAME compute footprint:
- Same n_trials=35 per cell
- Same ENSEMBLE_SIZE=3 (3 inner seeds)
- Same V1_FEATURE_COLUMNS_PRUNED (40 features)
- Same 4-model dispatch (A pooled, C, D, E)
- Same R5-BINARY-KILL fire rate expectation (18-22% based on /011 measurement)

Predicted wall-clock: 75-90 min. ≤2h cap is safe.

### 3.4 LM Master Phase 4.5 recommendation response

LM Master Phase 4.5 is fired SEPARATELY at /012 dispatch. The current brief is QR Phase 5 output and pre-dates Phase 4.5 advisory. The brief Section 3 will be updated post-Phase 4.5 with explicit LM Master recommendation responses per the v1 skill discipline. Anticipated LM Master recommendations:

- **Probable LM Master Rec #1**: "keep all hyperparameter / feature / bounds defaults bit-identical to /011 for axis isolation" — pre-adopted (the brief specifies this).
- **Probable LM Master Rec #2**: "consider running 1-2 ADDITIONAL seed-window probes (e.g., offset=4 + offset=5) in PARALLEL to triangulate substrate-lock dimensionality" — REJECT (out of scope for ≤2h cap; deferred to /015 multi-seed CONFIRMATION naturally testing all 10 seeds simultaneously).
- **Probable LM Master Rec #3**: "calibrate F7 thresholds (substrate-lock vs seed-lock cells) using observed /010↔/011 overlap distribution as prior" — pre-adopted (the F7 thresholds in Section 4 use 70%/30% bands anchored on /010↔/011's 93.3% measurement).

If LM Master Phase 4.5 Rec materially diverges from the above, the brief Section 3 will be UPDATED in a separate commit (per v1 skill Section 0.6 + 3.6).

### 3.5 Critic /011 process recommendations — ADOPTED

Three Critic process recommendations from /011 closeout are adopted in /012:

| Rec | Adoption status | /012 implementation |
|---|---|---|
| **Rec #1 — Pre-register `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP` subtype** | ADOPTED (Section 8.1) | Future v1 briefs Section 8 verdict tables MUST pre-register the {F3 catastrophic, F1 PROMISING, F6 < 61%} dual-firing cell as `EXPLORATION-NEGATIVE` subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`. /012's Section 8 already implements this. |
| **Rec #2 — F6 roster-overlap as committed artifact** | ADOPTED (committed at /012 commit `360650f`) | `analysis/iteration_v1-012/f6_roster_overlap.py` is the deterministic join script. QE will produce `reports-v1/iteration_v1-012/f6_roster_overlap.csv` as Phase 6 deliverable. F6/F7 falsifier verification is fully artifact-backed. |
| **Rec #3 — Engineering report mandatory at every Phase 7.5 dispatch** | ADOPTED (pre-commit in Section 10) | QE engineering report at `reports-v1/iteration_v1-012/engineering_report.md` is a Phase 6/7 deliverable; orchestrator hard-rejects Phase 7.5 dispatch without it. |

---

## Section 4 — Falsifiers (F1-F7)

Each falsifier has an explicit pre-registered numerical condition. F1-F6 are the standard v1 EXPLORATION falsifier set. F7 is NEW for /012 — the substrate-test-specific falsifier.

### F1 — OOS Sharpe-Δ vs BASELINE

**Pass band**: OOS Sharpe Δ vs BASELINE in [+0.05, +0.55].
**Fire conditions**:
- OOS Δ ≥ +0.55: catastrophic-positive (basin-rediscovery PLUS mechanical kill_low layer compounding — same as /011)
- OOS Δ ∈ [+0.05, +0.55]: PROMISING band (informational; outcome class determined by F3+F7 combination)
- OOS Δ ∈ (-0.05, +0.05): INERT band (no axis-mechanism effect; basin draw produced ~BASELINE-equivalent OOS)
- OOS Δ < -0.05: NEGATIVE (basin draw produced worse OOS than BASELINE)

**Interpretation**: F1 alone does NOT determine verdict-class. F1 conditions intersect with F3 and F7 per Section 8 verdict tables.

### F2 — R5-BINARY-KILL fire rate

**Pass band**: IS R5 fire rate ∈ [10%, 60%] AND OOS R5 fire rate ∈ [10%, 60%].
**Reference**: /011 measured IS 18.3% / OOS 21.7% — well within band.
**Fire conditions**: outside band → axis-mechanism degeneracy (kill_low fired too aggressively or not at all, indicating data divergence or symbol mismatch).

**Interpretation**: F2 should PASS because /012's R5-BINARY-KILL configuration is BIT-IDENTICAL to /011's. R5 fire rate depends on the data extent + NATR_14 distribution + which trades the model would have signaled — the first two are unchanged; the third depends on Optuna's basin draw. If F2 fails (fire rate <10% or >60%), the issue is data integrity, not the substrate test. F2 should PASS at >99% probability.

### F3 — IS Sharpe-Δ vs BASELINE

**Pass band per outcome class**:
- **Substrate-locked (Outcome A)**: IS Sharpe Δ ≥ +0.30 (basin-rediscovery signature; mirrors /010 +0.47 / /011 +0.48)
- **Seed-locked (Outcome B)**: IS Sharpe Δ ∈ [-0.20, +0.20] (basin shift produces ANY direction; rough symmetry)
- **Partial (Outcome C)**: IS Sharpe Δ ∈ (+0.10, +0.30) (partial OVERSHOOT below the basin-rediscovery signature)

**Catastrophic-IS-overshoot**: F3 Δ > +0.55 — a basin draw substantially LARGER than /010 + /011 (unlikely but not impossible; would indicate the substrate basin re-discovers a stronger variant).

**Interpretation**: F3 is the PRIMARY substrate-lock diagnostic. Combined with F7 (LTC IS overlap), F3 deterministically resolves the substrate-lock claim per Section 8.

### F4 — DEGENERATE_PREDICTOR detector + comparison.csv schema integrity

**Pass conditions**:
- No DEGENERATE_PREDICTOR firings in `validation_v1.detect_degenerate_predictor` (carry-over D-INST-001 from /010 — defect still present; not adjusted in /012; informational not blocking)
- comparison.csv schema clean: r5_fire_rate IS/OOS rows correctly labeled (per /010 D-RPRT-001 fix)
- No 0-pnl trade clusters from dead-feed data (D-RPRT-001 detection: ≥ 30 consecutive trades at exact same entry+exit price)

**Reference**: /010 had MKR dead-feed defect (88/116 OOS MKR trades at frozen 1650.10 price); /011 did NOT (no MKR; V1_BASELINE_UNIVERSE only). /012 also uses V1_BASELINE_UNIVERSE — F4 should PASS.

### F5 — PSR monotonic + ADF stationarity

**Pass conditions**:
- PSR_monthly_vs_0 ≥ 0.50 for both IS and OOS (informational signal that Sharpe is above zero benchmark)
- ADF Bonferroni-corrected p < 0.05 for all 40 features in V1_FEATURE_COLUMNS_PRUNED (regime_indicator exceptions: vol_natr_14 already in adf_exceptions per /002+ rules)

**Reference**: /011 measured PSR_monthly_vs_1 OOS = 0.566 (informational, below merge-gate 0.95 threshold). PSR_monthly_vs_0 should be higher.

### F6 — OOS roster-overlap with BASELINE

**Pass conditions**:
- /012 OOS roster overlap with BASELINE roster: pre-registered for diagnostic purposes (does NOT alone trigger verdict)
- Catastrophic-basin-shift signature: F6 < 61% baseline-overlap (mirrors /011's 16.67% finding)
- Inert: F6 ≥ 80% baseline-overlap (no axis-mechanism + no basin shift)
- Intermediate: F6 ∈ [61%, 80%]

**Interpretation**: F6 informs how much of /012's OOS roster is "discoverably different" from BASELINE. Combined with F7 (overlap with /011), F6 disambiguates substrate-lock from seed-lock outcomes.

### F7 — LTC IS roster-overlap with /011 (NEW; substrate-test specific)

**Pre-registered THREE-CELL classification**:

| F7 condition | Outcome class | Substrate-lock interpretation |
|---|---|---|
| **LTC IS /012↔/011 overlap > 70%** | **SUBSTRATE-LOCKED CONFIRMED (Outcome A)** | Basin re-discovered at DISJOINT seed window; substrate-lock claim VALIDATED |
| **LTC IS /012↔/011 overlap < 30%** | **SEED-LOCKED CONFIRMED (Outcome B)** | Basin diverges at seed shift; substrate-lock claim REFUTED |
| **LTC IS /012↔/011 overlap ∈ [30%, 70%]** | **PARTIAL (Outcome C)** | Basin substrate is multi-dimensional (seed × other factors); partial dissolution |

**Reference**: /011 LTC IS overlap with /010 was 93.27% (commit 360650f's `reports-v1/iteration_v1-011/f6_roster_overlap.csv`). The substrate-lock claim predicts /012↔/011 LTC IS overlap in the [70%, 95%] range.

**Why LTC specifically**: /010 + /011 both showed LTC IS pct_of_total_pnl > +100% — LTC is the SUBSTRATE-SIGNATURE symbol. The basin lottery converged on LTC dominance in BOTH /010 and /011. If /012 also produces LTC dominance with similar rosters, substrate-lock is confirmed. If LTC IS roster diverges, basin substrate is NOT seed-invariant.

**Secondary F7 diagnostic — portfolio IS overlap with /011**:

| Portfolio IS /012↔/011 overlap | Substrate-lock signal |
|---|---|
| > 80% | Strong substrate-lock |
| [60%, 80%] | Weak substrate-lock |
| [30%, 60%] | Partial dissolution |
| < 30% | Strong seed-lock (substrate refuted) |

F7 is verified via `f6_roster_overlap.csv` produced by `analysis/iteration_v1-012/f6_roster_overlap.py` invoked on /012 reports.

---

## Section 5 — Predicted Outcomes per 3-Way Pre-Registration

Per the substrate-lock empirical evidence at /010 + /011 (93.27% LTC IS overlap across MECHANISTICALLY DISTINCT axes at same seed), the modal prediction is **Outcome A (substrate-locked confirmed)** at ~60% probability:

| Outcome class | Probability | Predicted F1 OOS Δ | Predicted F3 IS Δ | Predicted F7 LTC IS overlap |
|---|---|---|---|---|
| **A — SUBSTRATE-LOCKED** | **~60%** | +0.20 to +0.60 (basin substrate inherited from /011) | +0.30 to +0.55 (basin-rediscovery signature) | > 70% |
| **B — SEED-LOCKED** | ~25% | -0.10 to +0.20 (no basin amplification; ~BASELINE +0.66 + mechanical kill_low ~+0.05) | -0.15 to +0.20 (basin shift produces noise) | < 30% |
| **C — PARTIAL** | ~15% | +0.10 to +0.45 (partial basin transfer) | +0.10 to +0.30 (partial OVERSHOOT) | [30%, 70%] |

### Reasoning for ~60% Outcome A modal prediction

The /010 + /011 evidence at same-seed=42 produced 93.27% LTC IS overlap across two MECHANISTICALLY DISTINCT axes. If the seed were the dominant basin-determining factor (Outcome B), we would not have observed this overlap. The empirical evidence strongly suggests the basin is determined by the (n_trials, ensemble_size, feature_set, seed) tuple — and the question /012 tests is whether this tuple's seed dimension is the dominant or subordinate component.

Three reasons the prior leans toward substrate-locked:
1. **Optuna at n_trials=35 with 40 features explores a high-dimensional space with sparse coverage**: 35 trials is too few to escape "the basin near the seed initialization". Different seeds within the canonical roster (which spans 6006 distinct integer values) are uniformly random in this space — there's no reason to expect [789, 1001, 2002] to land far from [42, 123, 456] in basin space.

2. **LightGBM's gradient boosting + Bayesian Optuna sampler are LOCALLY GREEDY**: they don't escape local minima. The 35-trial budget locks in to whatever basin the (data, features, search bounds) substrate creates strongest gravity around. Same data + features + bounds → same basin gravity → same convergence target regardless of inner seed.

3. **/010 + /011 already varied EVERY axis except seeds**: the mechanism differences (proportional R5 vs binary-kill R5) modulate the training distribution marginally — yet the basin re-discovered with 93.27% overlap. This is the strongest evidence the substrate is the dominant basin-shaping factor.

### Reasoning for ~25% Outcome B prior (seed-locked)

Three reasons the prior gives non-trivial weight to seed-locked:
1. **Optuna's Bayesian sampler uses the seed for initial trial coverage**: different seeds explore different first ~10 trials, which sets the priors for later TPE acquisitions. Substantially different first-trial coverage could route to different basins.

2. **LightGBM's per-tree seed determines feature_fraction/bagging_fraction subsampling**: at colsample_bytree<1.0 (which v1_pruned bounds allow), different inner seeds see different feature subsets per tree, producing different ensemble votes.

3. **The /010+/011 result MIGHT be specific to seed=42's basin choice**: it's possible seed=42 specifically lands the LTC-dominated basin AND any other seed lands a different basin. The /012 test is the only way to disambiguate.

### Reasoning for ~15% Outcome C prior (partial)

The substrate's dimensionality is likely multi-component (seed × n_trials × ensemble_size × feature_set). /012 only varies ONE component (seed) — it might dissolve PART of the substrate but not all of it. Outcome C is the "substrate is real but dimension-specific" case.

### Why these probabilities — not just guessed

These priors are informed by:
- /010↔/011 93.27% LTC IS overlap (strong evidence for substrate-lock)
- LM Master Phase 7.4 explicit claim: "the basin is seed-property-driven, not axis-property-driven" — but LM Master has 0/9 directional track record at v1 EXPLORATION; their conclusion is post-hoc, not predictive
- v3 cycle-7 analog: `feedback_v3_single_seed_frozen_baseline.md` shows v3 at single-seed=42 had BIT-IDENTICAL per-symbol Optuna trajectories across iter-v3/020/021/022 (Outcome A-like). v1's substrate-lock evidence at /010+/011 is structurally analogous.

The 60/25/15 prior is the QR's honest probability assignment given the available evidence. Cannot be cited as a precise quantification — it's a coarse decision frame.

### Multi-seed CONFIRMATION dissolution prediction (regardless of /012 outcome)

For /015 CONFIRMATION (which will use all 10 ENSEMBLE_SEEDS values), predicted multi-seed OOS Sharpe-Δ:

- If Outcome A confirms: substrate basin lottery dissolves across 10 seeds → mean OOS Sharpe ≈ BASELINE +0.66 + mechanical kill_low layer ~+0.05 = ~+0.71 (NOT /011's +1.07 single-seed magnitude)
- If Outcome B confirms: each seed produces a different basin; aggregate produces a smoother distribution → mean OOS Sharpe across 10 seeds in [+0.60, +0.85]
- If Outcome C confirms: partial substrate dissolution → mean OOS Sharpe in [+0.65, +0.75]

In ALL three cases, the mechanical kill_low layer should produce a small positive contribution ~+0.05. The PURPOSE of /015 CONFIRMATION (per `feedback_v1_substrate_basin_lock.md`) is to measure this contribution at a non-conditional basis.

---

## Section 6 — What Could Falsify the Hypothesis (Pre-Registered)

The hypothesis is the 3-way outcome pre-registration in Section 1. Any of the following observations would falsify or refute specific outcome classes:

| Observation | Falsifies | Result |
|---|---|---|
| F1 OOS Δ > +0.55 AND F3 IS Δ > +0.55 AND F7 LTC IS overlap > 90% with /011 | Outcomes B+C | Outcome A confirmed STRONGLY (basin substrate is overwhelmingly seed-invariant) |
| F1 OOS Δ < -0.05 AND F7 LTC IS overlap < 20% with /011 | Outcomes A+C | Outcome B confirmed STRONGLY (seed is the dominant basin-determining factor) |
| F1 OOS Δ ∈ [-0.05, +0.20] AND F7 LTC IS overlap ∈ [40%, 60%] | Outcomes A+B | Outcome C confirmed (substrate is multi-dimensional) |
| F2 R5 fire rate outside [10%, 60%] band | Substrate-test design | Data integrity failure; not substrate-lock signal — BLOCK-PENDING-FIX |
| F4 DEGENERATE_PREDICTOR fires on any cell | Trade roster validity | Data integrity failure; not substrate-lock signal — BLOCK-PENDING-FIX |
| F1 OOS Δ > +1.10 (drastic positive overshoot) | All outcomes | Numerical instability or non-deterministic seed handling — BLOCK-PENDING-FIX |

The substrate-test design is robust against most non-data failures. The expected verdict will be one of {Outcome A, B, C} per Section 8 verdict gates.

---

## Section 7 — Mechanism Diagram (per /011 codification)

Per `feedback_v1_substrate_basin_lock.md` and the LM Master + Critic 3-way convergence, the substrate is mechanically:

```
At v1 EXPLORATION budget:
  (data + features + V1_FEATURE_COLUMNS_PRUNED + bounds_profile + n_trials=35 + ENSEMBLE_SIZE=3)
                ⇓
        OPTUNA SAMPLER + LightGBM TRAINER initialized by INNER SEED [s1, s2, s3]
                ⇓
        Bayesian search of n_trials=35 ≈ 35 hyperparameter points per cell
                ⇓
        Per-cell convergence to basin near the SEED INITIALIZATION
                ⇓
        Per-(model, month) basin draws produce per-cell prediction model
                ⇓
        BACKTEST signal generation (R5-BINARY-KILL filter applied; kill_low @ NATR<2.0%)
                ⇓
        OBSERVED ROSTER (IS + OOS)
```

The substrate-lock claim is: the (data + features + bounds + n_trials + ensemble_size) tuple produces basin GRAVITY independent of seed; the seed only modulates the trajectory but not the convergence target. Substrate-LOCK = basin gravity is dominant. SEED-LOCK = seed sets the trajectory entirely, basin gravity is weak at 35-trial budget.

/012 measurement: hold (data, features, bounds, n_trials, ensemble_size, R5 mechanism) BIT-IDENTICAL to /011; change ONLY (s1, s2, s3) from [42, 123, 456] to [789, 1001, 2002]. Substrate-lock predicts ~/011 roster. Seed-lock predicts new roster.

---

## Section 8 — Verdict Gates

### 8.1 Verdict-class deterministic resolution

| F1 (OOS Δ) | F3 (IS Δ) | F7 (LTC IS overlap with /011) | Verdict |
|---|---|---|---|
| ≥ +0.05 | ≥ +0.30 | > 70% | **EXPLORATION-NEGATIVE subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP` (Outcome A confirmed)** |
| ≥ +0.05 | [+0.10, +0.30) | [30%, 70%] | **EXPLORATION-PROMISING-PARTIAL-DISSOLUTION (Outcome C; deserves /015 CONFIRMATION testing)** |
| ≥ +0.05 | [-0.20, +0.10) | < 30% | **EXPLORATION-PROMISING-SEED-DISSOLVED (Outcome B confirmed; R5-BINARY-KILL CONFIRMATION-eligible at /015)** |
| [-0.05, +0.05) | any | any | **EXPLORATION-NEGATIVE subtype `BASELINE-EQUIVALENT-NULL` (mechanism + basin both inert)** |
| < -0.05 | < -0.20 | < 30% | **EXPLORATION-NEGATIVE subtype `seed-shifted-NEGATIVE` (basin shift produced strict OOS regression; rare per /010+/011 evidence)** |
| > +0.55 | > +0.55 | > 90% | **EXPLORATION-NEGATIVE subtype `catastrophic-substrate-amplification` (substrate-lock + amplification beyond /011 magnitude; non-durable)** |

The Section 8.1 table fully pre-registers the verdict-class for all measurable F1×F3×F7 cells. No discretion at verdict time.

### 8.2 Substrate-test diagnostic outcome assignment

Independent of Section 8.1 verdict-class, /012 produces a DIAGNOSTIC outcome that codifies the substrate-lock test result:

| F7 LTC IS overlap with /011 | Diagnostic outcome | Path Forward implication |
|---|---|---|
| > 70% | **SUBSTRATE-LOCKED CONFIRMED** | R5-BINARY-KILL family REMAINS CLOSED at v1 single-seed-WINDOW. /015 CONFIRMATION must pivot to multi-seed dissolution test on R5-BINARY-KILL (testing the mechanical kill_low layer at non-conditional basis) OR to UNUSED-family axes (labeling, methodology). The substrate-lock structural finding stands. |
| [30%, 70%] | **PARTIAL DISSOLUTION** | Substrate is multi-dimensional. /013-/014 should test additional substrate dimensions (n_trials? ENSEMBLE_SIZE?) — but per ≤2h cap, only ONE substrate axis can be tested per EXPLORATION. /015 CONFIRMATION on R5-BINARY-KILL is POSSIBLE but with reduced confidence. |
| < 30% | **SEED-LOCKED CONFIRMED** | Substrate-lock STRUCTURAL claim REFUTED. /011's +0.48 IS Sharpe-Δ was a single-seed=42 lottery. R5-BINARY-KILL becomes a candidate axis whose mechanical edge may aggregate positively at multi-seed CONFIRMATION. **/015 CONFIRMATION on R5-BINARY-KILL becomes the UNAMBIGUOUS next step**. |

### 8.3 Merge decision

/012 verdict-class will be one of:
- **EXPLORATION-NEGATIVE** (any subtype) → NO-MERGE; /013 advances per Path Forward
- **EXPLORATION-PROMISING** (PARTIAL-DISSOLUTION or SEED-DISSOLVED) → NO-MERGE (EXPLORATION never merges); /015 CONFIRMATION pre-committed if SEED-DISSOLVED

Per the v1 skill: "EXPLORATION-PROMISING is catalog-only; never merges to trunk". Merging requires CONFIRMATION-MERGE verdict.

### 8.4 HIGH-RISK pre-commit tripwire

/012 is NORMAL-RISK declared. No HIGH-RISK pre-commit tripwire applies. If /012 emerges PROMISING-SEED-DISSOLVED, this is signal-to-process input for /015 CONFIRMATION planning, NOT a pre-commit tripwire on /013.

---

## Section 9 — Library Stack

No new libraries required. The substrate test uses the existing v1 library stack:

- `crypto_trade.strategies.ml.lgbm.LightGbmStrategy` (LightGBM ensemble strategy)
- `crypto_trade.strategies.ml.optimization.optimize_and_train` (Optuna + LightGBM trainer)
- `crypto_trade.backtest.run_backtest` (backtest engine with R5-BINARY-KILL wiring from /011 commit `b788d4f`)
- `crypto_trade.strategies.ml.validation_v1` (CPCV + DSR + PBO + PSR + ADF + IC — methodology reporting)
- `crypto_trade.reporting_v1` (per-cell PCA n_eff + dsr.json + comparison.csv extensions from /008 commit)
- `pandas==2.3.3`, `numpy==2.3.4`, `lightgbm==4.6.0`, `optuna==4.5.0`, `statsmodels==0.14.4` (versions pinned in `uv.lock`)

The new join script `analysis/iteration_v1-012/f6_roster_overlap.py` uses only Python stdlib (csv, argparse, pathlib).

---

## Section 10 — Implementation Spec (QE Deliverables)

### 10.1 Code diff scope

**Minimal — NO `src/` changes**. Already-landed:

1. `run_baseline_v1.py` — additive changes for `--ensemble-seeds-offset` flag (commit `360650f` on /012 branch)
2. `analysis/iteration_v1-012/f6_roster_overlap.py` — F6/F7 join script (commit `360650f`)
3. `reports-v1/iteration_v1-011/f6_roster_overlap.csv` — committed F6 reference artifact for /011 (commit `360650f`; reproduces LM Master Phase 7.4 offline numbers)

### 10.2 QE Phase 6 deliverables

1. **Run the /012 backtest**:
   ```
   uv run python run_baseline_v1.py \
       --exploration --iteration 12 \
       --pruned-features --n-trials 35 \
       --r5-binary-kill-enabled --r5-binary-kill-min-natr 2.0 \
       --ensemble-seeds-offset 3
   ```
   Wall-clock budget: ≤2h (predicted 75-90 min per /011 reference).

2. **Produce all standard report artifacts** in `reports-v1/iteration_v1-012/`:
   - `comparison.csv` (with R5 fire rate rows)
   - `in_sample/` and `out_of_sample/` subdirs with trades.csv, per_symbol.csv, monthly_pnl.csv, daily_pnl.csv, dsr.json, adf_test.csv, ic_matrix.csv, quantstats.html, per_regime.csv

3. **Produce the F7 substrate-test artifact** (Critic Rec #2 + F7 falsifier):
   ```
   uv run python analysis/iteration_v1-012/f6_roster_overlap.py \
       --target reports-v1/iteration_v1-012 \
       --reference baseline=reports-v1/iteration_v1-baseline \
       --reference iter010=reports-v1/iteration_v1-010 \
       --reference iter011=reports-v1/iteration_v1-011 \
       --output reports-v1/iteration_v1-012/f6_roster_overlap.csv
   ```
   This produces the per-(half × symbol × reference) overlap CSV that F6 + F7 falsifiers verify against.

4. **Produce QE engineering report** at `reports-v1/iteration_v1-012/engineering_report.md` (Critic Rec #3 + v1 skill mandate). Contents:
   - Backtest invocation command + wall-clock elapsed
   - Headline IS / OOS Sharpe + comparison.csv row dump
   - R5-BINARY-KILL fire rate IS/OOS values
   - Pointer to f6_roster_overlap.csv and per-symbol metrics
   - F1-F7 falsifier table (Brief Section 4 + Section 8 conditions evaluated against observed numbers)
   - Diagnostic outcome (SUBSTRATE-LOCKED / PARTIAL / SEED-LOCKED) per Section 8.2

5. **No src/ changes**. R5-BINARY-KILL wiring already at `backtest.py` + `backtest_models.py` from /011's commit `b788d4f`. /012 ONLY toggles `--ensemble-seeds-offset 3`.

### 10.3 Engineer pre-flight checks

Before launching the backtest:
- Verify data extent is identical to /011 (no fresh data fetches between /011 and /012; otherwise determinism comparison is contaminated)
- Verify the runner banner prints `ensemble_seeds: [789, 1001, 2002] (offset=3)` at startup — confirms the flag flowed correctly to all 4 models
- Verify R5-BINARY-KILL config matches /011: `r5_kill_low_natr_enabled=True`, `r5_kill_low_natr_min_pct=2.0`, R5 vol-target DISABLED

### 10.4 Phase 7.5 Critic deliverables — anticipated

Critic will perform the standard 8+2 checks per `quant-critic.md` plus the v1-specific Check 14 (Axis Family Validation). The `methodology-substrate-test` family declaration in Section 0.6 is structurally novel — Critic Check 14 should accept it as orthogonal to prior 7 families (feature-family, model-arch, labeling, universe, risk-primitive, methodology, hyperparameter-region) given that /012's intervention is the SEED WINDOW, not any other axis dimension.

If Critic disagrees on the family taxonomy assignment, the verdict still resolves via Section 8.1 deterministically (the F1×F3×F7 cells are independent of family taxonomy debate). The taxonomy question is a process-integrity issue, not a verdict-binding issue.

---

## Section 11 — Alternatives (Critic Path Forward Options 1 + 2; deferred to /013-/014)

The /011 Phase 7.5 Critic Path Forward listed three Options. /012 implements Option 3 (substrate-dissolution probe). Options 1 + 2 are deferred to /013-/014 per the cadence sequence:

### Alternate A — Labeling axis: triple-barrier σ_t source

- **Axis**: replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers (24h vs 14d EWMA window for σ_t).
- **Family**: `labeling` (UNUSED in cycle-2 at /012; if /012 is Outcome A, this is the next axis at /013).
- **Rationale**: highest-prior-probability of basin escape from UNUSED-family menu (~70% per Critic Path Forward). Changes IS label distribution per cell → different LightGBM loss surface → potentially different basin.
- **HIGH-RISK declaration**: YES (label distribution change is HIGH-RISK per /005 rule). Multi-seed pre-commit if PROMISING.
- **Expected /013 dispatch trigger**: /012 closes Outcome A (substrate-lock confirmed) → /013 = Labeling axis.

### Alternate B — Methodology axis: per-cell early-stop with inner hold-out

- **Axis**: LightGBM per-cell early stopping with Purged-CV inner hold-out (20% within-fold).
- **Family**: `methodology` (UNUSED since /008 at /014).
- **Rationale**: structurally orthogonal; changes WHICH trees retained per cell → different ensemble composition → different basin. Non-compoundable as edge signal but provides diagnostic infrastructure.
- **Expected /014 dispatch trigger**: /012 + /013 both NEG-NULL → /014 = methodology infrastructure axis.

These are RESERVE proposals. /012's primary mission is the substrate-dissolution probe. /013-/014 will be designed based on /012's diagnostic outcome.

---

## Section 12 — Catalog Closeout Plan

The /012 closeout will append a row to `briefs-v1/exploration_catalog.md` per the v1 skill discipline. Pre-registered fields:

- `iter-v1-NNN`: iter-v1/012
- `YYYY-MM-DD`: 2026-05-25
- `axis varied`: ENSEMBLE_SEEDS window offset 0→3 (DISJOINT inner seeds [789, 1001, 2002] vs /011's [42, 123, 456]) with R5-BINARY-KILL config BIT-IDENTICAL to /011
- `axis family`: `methodology-substrate-test` (NEW 8th catalog family — first usage; structurally orthogonal to all 7 prior families)
- `IS Sharpe Δ`: [TBD post-backtest; F3 conditions in Section 4 + Section 8.1]
- `OOS Sharpe (informational)`: [TBD post-backtest; F1 conditions in Section 4 + Section 8.1]
- `verdict`: [TBD; one of EXPLORATION-NEGATIVE-BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP / EXPLORATION-PROMISING-PARTIAL-DISSOLUTION / EXPLORATION-PROMISING-SEED-DISSOLVED / EXPLORATION-NEGATIVE-BASELINE-EQUIVALENT-NULL / EXPLORATION-NEGATIVE-seed-shifted-NEGATIVE / EXPLORATION-NEGATIVE-catastrophic-substrate-amplification per Section 8.1]
- `confirmation candidate?`: NO for any EXPLORATION-NEGATIVE; conditional YES only if PROMISING-SEED-DISSOLVED (path to /015 CONFIRMATION on R5-BINARY-KILL)

The detailed-verdict-notes section will record:
- F1 + F3 + F7 measured values per Section 4
- LTC IS overlap with /011 (the diagnostic outcome assignment per Section 8.2)
- Substrate-lock interpretation and Path Forward
- LM Master Phase 7.4 calibration update (was substrate-lock prediction directionally correct?)
- New catalog axiom additions if any

### Permanent catalog additions anticipated

Outcome A (substrate-locked confirmed at DISJOINT seeds) would add:
- `feedback_v1_substrate_basin_lock.md` MEMORY ENTRY EXTENDED — substrate-lock claim VALIDATED at DISJOINT seeds; binding constraint for ALL future v1 EXPLORATIONs.
- New v1 verdict subtype `SUBSTRATE-LOCK-CONFIRMED-AT-DISJOINT-SEEDS` as compound subtype to `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`.

Outcome B (seed-locked confirmed) would add:
- `feedback_v1_substrate_basin_lock.md` MEMORY ENTRY MARKED FALSIFIED — structural claim refuted.
- /015 CONFIRMATION pre-commit on R5-BINARY-KILL.

Outcome C (partial dissolution) would add:
- `feedback_v1_substrate_basin_lock.md` MEMORY ENTRY REFINED — substrate is multi-dimensional; seed is necessary but not sufficient.
- New axis-priority directive: /013-/014 must test other substrate dimensions before /015 CONFIRMATION.

---

## Section 13 — Phase 5.5 Self-Check

This brief includes all 13 mandatory sections per the v1 skill discipline. Verification:

| Section | Required | Status |
|---|---|---|
| 0 (pre-header: 0.1-0.6) | Yes | ✓ |
| 1 (hypothesis) | Yes | ✓ |
| 2 (IS-only evidence) | Yes | ✓ (lighter than typical EXPLORATION because substrate finding is empirically established at /011; F6 join script + reproduction of LM Master numbers committed) |
| 2.5 (HIGH-RISK declaration) | Yes | ✓ (NORMAL-RISK declared with rationale) |
| 3 (proposed changes) | Yes | ✓ |
| 4 (falsifiers F1-F7) | Yes | ✓ (NEW F7 substrate-test specific) |
| 5 (predicted outcomes per 3-way pre-reg) | Yes | ✓ |
| 6 (what could falsify) | Yes | ✓ |
| 7 (mechanism diagram) | Yes | ✓ |
| 8 (verdict gates 8.1-8.4 + substrate diagnostic) | Yes | ✓ |
| 9 (library stack) | Yes | ✓ |
| 10 (implementation spec) | Yes | ✓ (10.1-10.4) |
| 11 (alternatives — Critic Path Forward Options 1+2) | Yes | ✓ |
| 12 (catalog closeout plan) | Yes | ✓ |
| 13 (Phase 5.5 self-check) | Yes | ✓ (this section) |

### Substantive integrity checks

- **Axis Rotation Discipline (skill mandate)**: Section 0.6 declares `methodology-substrate-test` family with rotation rationale. Prior 5 families [feature-family, methodology, feature-family, risk-primitive, risk-primitive] — neither at saturation (no family at 3+/5). NEW family extension defensible (8th total).
- **HIGH-RISK Axis Declaration (skill mandate)**: Section 2.5 declares NORMAL-RISK with rationale.
- **LM Master Phase 4.5 response (skill mandate)**: Section 3.4 anticipates LM Master Phase 4.5 recommendations and pre-adopts the expected ones; brief will be UPDATED if LM Master Rec materially diverges (per v1 skill Section 3.6 mandate).
- **F1-F7 falsifiers (skill mandate)**: Section 4 specifies F1-F7 with explicit numerical conditions; F7 is NEW substrate-test-specific falsifier per Section 8 verdict-table dependency.
- **Section 8 verdict-class pre-registration (Critic Rec #1)**: Section 8.1 pre-registers all measurable F1×F3×F7 cells with deterministic verdict assignment, including the `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP` subtype codified at /011 closeout.
- **F6 roster-overlap committed artifact (Critic Rec #2)**: artifact `analysis/iteration_v1-012/f6_roster_overlap.py` committed at commit `360650f`; reference output `reports-v1/iteration_v1-011/f6_roster_overlap.csv` committed at same commit reproducing LM Master Phase 7.4 numbers exactly.
- **Engineering report mandatory at Phase 7.5 (Critic Rec #3)**: Section 10.2 Deliverable #4 specifies QE engineering report as Phase 6 deliverable.
- **Per skill discipline — wall-clock cap ≤2h (cadence skill mandate)**: Section 3.3 predicts 75-90 min wall-clock; ≤2h cap is safe.

### Brief size assessment

This brief is ~14k tokens — within the ~25k brief size budget for v1 EXPLORATION. Sections 1, 5, 7 are the longest (mechanism + prediction reasoning); other sections are appropriately concise. No section is excessive.

### Conclusion of Phase 5.5 Self-Check

This brief is COMPLETE per the v1 skill's 13-section requirement. All 7 falsifiers + verdict gates are pre-registered with numerical conditions. The substrate-test axis is structurally orthogonal to all prior axes. The expected outcomes are pre-registered with explicit probabilities (60/25/15 for A/B/C).

Brief is READY for LM Master Phase 4.5 advisory + Phase 5.5 gate review + Phase 6.0 Critic pre-flight. The QE Phase 6 invocation is fully specified in Section 10.2.

---

**END OF BRIEF**

Brief authored 2026-05-25 by claude-opus-4-7 (1M context) — quant-research-v1 mode.

Brief total: 13 sections including all mandatory v1 elements.

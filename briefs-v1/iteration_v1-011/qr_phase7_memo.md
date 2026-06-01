# iter-v1/011 — QR Phase 7 Evaluation Memo

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Branch**: `iteration-v1/011`
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md `f8bc12c`) — IS +0.2829 / OOS +0.6637
**Companion**: full engineering report at `reports-v1/iteration_v1-011/engineering_report.md`

---

## Verdict Concurrence

**QR Phase 7 verdict assignment: EXPLORATION-NEGATIVE — catastrophic-basin-shift class.**

I concur with Critic Phase 7.5 OVERALL verdict and with LM Master Phase 7.4 mechanism diagnosis. Three-way convergence reached on:

1. **Pre-registered F3 catastrophic-basin-shift class fires deterministically**: IS Δ +0.4849 > +0.30 brief Section 8 upper threshold; class explicitly carries "axis CLOSED at single-seed" subsuming any F1 reading.
2. **F6 baseline-roster overlap = 16.7% << 61% tripwire**: 44.3pp below the catastrophic-basin-shift indicator; mechanically incompatible with a stateless 21.69%-fire-rate filter ALONE driving the OOS lift.
3. **LTC IS roster /010 ↔ /011 = 93.3%**: smoking-gun evidence that Optuna at v1 single-seed=42 re-discovered the same basin under mechanically distinct axes (/010 proportional weight scaling; /011 binary entry filter). The IS Δ +0.48 is NOT first-order kill_low mechanical effect.

I considered LM Master Phase 7.4's proposal to introduce a NEW v1 verdict subtype `PROMISING-OVERSHOOT-BASIN-INHERITED` for the {F3 catastrophic, F1 PROMISING, F6 < 61%} dual-firing cell — and I agree with Critic's REJECTION of retroactive re-classification on /011 itself. The brief Section 8 pre-registration is binding; the subtype is forward-looking process upgrade (Critic Recommendation #1 to /011 closeout — codified as future v1 brief requirement).

## Mechanism Read

The OOS Sharpe Δ +0.4072 is real-but-non-durable. Decomposition (engineering report §5):

| Mechanism | OOS Sharpe Δ contribution | Confidence |
|---|---|---|
| /010 basin substrate vs BASELINE | -0.03 (already measured at /010 closeout) | HIGH |
| /011 mechanical kill_low cleanup on /010 basin | ~+0.44 (from /010→/011 per-symbol PnL Δ) | MED |
| **/011 vs BASELINE total** | **+0.41** | LOW directional (basin-conditional) |

The entire OOS Δ +0.41 is attributable to the kill_low mechanical layer riding on the /010 basin substrate. NONE of it is attributable to kill_low DISCOVERING a new positive-OOS basin. If /015 multi-seed CONFIRMATION dissolves the LTC-dominated basin (which the structural argument predicts), the mechanical /010→/011 kill_low effect would still apply per-seed but the basin substrate itself would average to BASELINE's level — meaning multi-seed OOS Sharpe would land closer to BASELINE +0.66 + (small mechanical cleanup ~+0.05) ≈ +0.70, NOT /011's +1.07.

The non-durability is supported by the BASELINE-stratum oracle in brief Section 2.3: kill_low oracle ON the BASELINE roster ITSELF showed only +0.046 Sharpe-Δ (vs the /011 observed +0.41) — the 9× ratio is the basin-substrate amplification not the mechanism's portable edge.

## What the Iteration Established

The /010 + /011 pair establishes a NEW structural finding for v1 cycle-2: at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, the Optuna basin is substrate-locked across axis primitives. Two mechanically distinct axes (/010 proportional weight scaling; /011 binary entry filter) re-discovered the same LTC-dominated basin with 93.3% IS roster overlap. The basin is a property of the (seed, search budget, feature set, ensemble size) tuple, NOT of the axis intervention being tested.

This was hypothesized at /010 closeout (LM Master Phase 7.4 calibration update on position-sizing-weight axes); it became a confirmed structural property at /011 with the cross-mechanism roster overlap measurement.

**Implication for v1 cycle-2 EXPLORATIONs going forward**: single-seed Sharpe-Δ cannot anchor an edge claim at this budget. Only multi-seed dissolution at /015 CONFIRMATION can disambiguate basin-lottery from genuine axis edge.

## LM Master Track Record Update

LM Master /011 Phase 7.4 self-assessment: 0/9 directional + 3 PARTIAL. The PARTIAL credits are:
- /002 LTC overfit mechanism diagnosis (Phase 7.4 §4)
- /008 PROMISING-METHODOLOGY subtype prediction
- /011 modal-class taxonomy

The directional Sharpe-Δ track record is 0/9 over /003-/011. The diagnostic-frame contributions (e.g., the 93.3% LTC overlap + 16.7% F6 baseline overlap measurements at /011 Phase 7.4) are load-bearing for Critic verdict and Path Forward. Future Phase 4.5 / Phase 7.4 cycles should weight LM Master's diagnostic-frame outputs heavily and discount the point Sharpe-Δ predictions accordingly.

## Process Defects (Critic Phase 7.5 Recommendations)

Three process-integrity issues surfaced at /011 closeout:

1. **Engineering report missing (Critic Rec #3)**: /010 had one; /011 did not. This memo + the companion engineering report fill the gap. Mandatory at every future Phase 7.5 dispatch.

2. **F6 roster-overlap diagnostic not committed as artifact (Critic Rec #2)**: LM Master computed offline; the trade-roster-join script is not in `analysis/iteration_v1-011/`. Future briefs with F6-style falsifiers must require QE to emit `f6_roster_overlap.csv` (commit-tracked).

3. **F4 DEGENERATE_PREDICTOR detector surface absent (carry-over D-INST-001)**: detector ships in `validation_v1.py` but no per-cell CSV/JSON emitted. Methodology axis at /012 / /013 / /014 should bundle a "validator output bundle" alongside comparison.csv that surfaces all `validation_v1.*` detector outputs as committed artifacts.

## Path Forward (per Critic Phase 7.5)

Three axes proposed for /012:

1. **Labeling axis — triple-barrier σ_t source** (UNUSED family at v1 cycle-2): replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers. ~70% prior probability of basin escape via re-shaped label distribution. Strongest substrate-dissolution probe from UNUSED-family menu.

2. **Methodology axis — per-cell early-stop with inner hold-out** (UNUSED since /008): within-fold early stopping via 20% inner hold-out. Changes WHICH trees retained per cell; substrate-dissolving via tree-selection diversity. Non-compoundable as edge signal but provides diagnostic infrastructure.

3. **Substrate-dissolution PROBE EXPLORATION at /012** (sister-iteration; not new axis): rerun /011's EXACT R5-BINARY-KILL config at single-seed=43. Tests "basin is seed-property-driven, not axis-property-driven" hypothesis directly. ≤2h cap.

QR Phase 7 memo does NOT pre-commit to a specific option. Phase 8 diary's "Next Iteration Ideas" + next iteration's Phase 5 brief make the selection per (LM Master Phase 4.5 + Critic Phase 6.0) sequence.

## Closeout

Verdict assignment is locked. No BLOCK-PENDING-FIX rerun — Critic Phase 7.5 verdict is EXPLORATION-NEGATIVE catastrophic-basin-shift, not BLOCK-PENDING-FIX. /011 closes as EXPLORATION-NEGATIVE; /012 advances per Path Forward.

Tag `v0.v1-011` is applied after the Phase 8 diary + catalog entry commit lands.

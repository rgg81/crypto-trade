# Phase 7.5 Critic Review — iter-v1/011

OVERALL: EXPLORATION-NEGATIVE — F3 catastrophic-basin-shift fires (IS Δ +0.4849 > +0.30 brief Section 8 threshold); basin-inheritance from /010 confirmed (LTC IS roster /010↔/011 = 93.3% per LM Master Phase 7.4; LTC IS pct 119.84% → 106.48% same-basin reading); OOS Δ +0.41 is real but mechanically attributable to deterministic kill_low cleanup layered on /010's already-dominant basin, not a durable axis-attributable edge.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-2 #6 of 10; CONFIRMATION unreachable until /015)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

R5-BINARY-KILL is a STATELESS entry filter reading `vol_natr_14` from the per-symbol feature parquet at `(sym, ot)` where `ot` is the OPEN time of the candle being evaluated (`backtest.py:431`). `vol_natr_14` is computed past-only via pandas_ta rolling NATR (Bonferroni-pass ADF stat -12.04 confirms stationarity). Foundation re-audited: `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`; the 4 mandated regression tests present. No look-ahead found.

### Check 2 — Embargo Width: PASS

`validation_v1.py:REQUIRED_GAP = (21 + 1) × 5 = 110` for v1's 5-symbol universe. Compute helper at `walk_forward.py:38` is single source of truth. Actual gap = required gap.

### Check 3 — Multiple-Testing Correction: FAIL-informational (EXPLORATION-mode artifact, NOT BLOCK-triggering)

`dsr=0.0` (computable; not saturation), `psr=0.566289` OOS / 0.325365 IS (`psr_monthly_vs_1`), `pbo=null`, `n_eff=13`, `n_trials=35`. PSR_monthly_vs_1 OOS=0.566 borderline at face value, but LM Master Phase 7.4 §5 caveat binds: PSR is **conditional on the (seed=42, LTC-dominated basin) draw**; cross-seed uncertainty unpriced. Per the EXPLORATION-mode DSR-artifact rule, Check 3 fires INFORMATIONAL only.

### Check 4 — IC Correlation: PASS-vacuous

No new feature family. `vol_natr_14` is pre-existing baseline feature read for entry-gate logic, not new LightGBM input. ic_matrix.csv max IC across active pairs = 0.146 (interaction × volatility). N/A by construction.

### Check 5 — ADF Stationarity: PASS

All 40 active features Bonferroni-pass on both halves. `vol_natr_14` ADF=-12.04 (R5 input is stationary).

### Check 6 — Pareto Dominance + Per-Symbol Concentration: FAIL-substantive

Per-symbol concentration (`out_of_sample/per_symbol.csv`):

| Symbol | trades | WR | net_pnl_pct | pct_of_total_pnl |
|---|---|---|---|---|
| LINKUSDT | 47 | 55.3% | +84.86 | **+59.24%** |
| BTCUSDT | 17 | 70.6% | +51.28 | **+35.80%** |
| DOTUSDT | 48 | 45.8% | +29.13 | +20.34% |
| ETHUSDT | 36 | 44.4% | -2.90 | -2.02% |
| LTCUSDT | 32 | 43.8% | -19.12 | -13.34% |

**TWO symbols above the 30% per-symbol concentration cap** (LINK 59.24%, BTC 35.80%). LINK incremental +5% vs /010 — basin-inherited not /011-discovered. BTC 17 trades / WR 70.6% (12W/5L) IS the only mechanism-attributable effect (kill_low selectively removed BTC OOS losers per brief Section 2.4 EDA prediction); however 17 trades / ~15 OOS months = 1.1 trades/month — high-leverage on small N.

In-sample (`in_sample/per_symbol.csv`):

| Symbol | trades | WR | net_pnl_pct | **pct_of_total_pnl** |
|---|---|---|---|---|
| LTCUSDT | 104 | 51.0% | +110.58 | **+106.48%** |
| LINKUSDT | 149 | 43.0% | +42.45 | +40.88% |
| DOTUSDT | 116 | 44.8% | +31.01 | +29.86% |
| BTCUSDT | 78 | 38.5% | -30.74 | -29.60% |
| ETHUSDT | 123 | 31.7% | -49.45 | -47.61% |

**LTC IS = 106.48% — sister to /010's 119.84%.** Trajectory baseline 6.42% → /010 119.84% → /011 106.48% confirms LTC IS basin is SAME Optuna substrate re-discovered. LM Master Phase 7.4: LTC IS roster /010↔/011 = 93.3% (97/104), baseline↔/011 = 22%. IS Δ +0.4849 is NOT first-order R5-BINARY-KILL; basin lottery re-discovery.

Check 6 substantive verdict: **FAIL on basin-inheritance + per-symbol concentration cap breach.**

### Check 7 — Reproducibility: FAIL-substantive

Code-level reproducible (`run_baseline_v1.py:918+` explicit kwargs). But three artifact-level defects:

1. **`engineering_report.md` is NOT committed.** Neither `briefs-v1/iteration_v1-011/engineering_report.md` nor `reports-v1/iteration_v1-011/engineering_report.md` exists. /010 had one — /011 does not. The QE's `OVERALL=READY-FOR-CRITIC` deliverable per Phase 7.5 boot sequence Step 2 is missing. **Process integrity violation.**

2. **F6 roster-overlap diagnostic absent from committed reports.** Brief Section 4 F6 declares "OOS roster-overlap with BASELINE < 61% → NEGATIVE-basin-shift" as a load-bearing falsifier. The trade-roster-join script is NOT in `analysis/iteration_v1-011/`. LM Master Phase 7.4 computed F6=16.7% offline as smoking-gun, but the artifact is unfilled.

3. **F4 DEGENERATE_PREDICTOR detector report surface absent.** Detector ships in `validation_v1.py` but no per-cell JSON/CSV emitted.

Cosmetic: `r5_binary_kill_fire_rate_is` / `_oos` rows in comparison.csv are duplicates (both carry identical payload). The metric-name labels which half is primary subject; values correct in column slots per D-RPRT-001 fix. Unconventional schema but not verdict-binding.

Reproducibility verdict: **FAIL** binding on (1).

### Check 8 — Hypothesis-Implementation Alignment: FAIL-substantive

Brief Section 1: kill_low at 2.0% removes ETH/LTC/DOT 2.5-3 loser cluster; predicted OOS Δ +0.05 to +0.12. Code change matches brief spec exactly.

**Brief-vs-mechanism MISMATCH** per LM Master Phase 7.4 SMOKING GUN:

| Property | /010 | /011 |
|---|---|---|
| IS Δ | +0.4701 | +0.4849 |
| LTC IS pct | 119.84% | 106.48% |
| LTC IS roster overlap /010↔/011 | — | **93.3%** |
| F6 baseline-overlap | 17.1% | **16.7%** |
| F6 /010-overlap | — | **93.3%** |
| LINK OOS | +80.92 | +84.86 |
| BTC OOS | +44.88 | +51.28 |
| LTC OOS | -43.52 | -19.12 |
| ETH OOS | -11.36 | -2.90 |
| OOS Δ | -0.0283 | +0.4072 |

LTC IS basin transferred 93.3% from /010 to /011. Hypothesized mechanism partially observable in LTC OOS +24pp / ETH OOS +8pp mechanical recoveries — but DOMINANT mechanism is same Optuna basin as /010 + kill_low downstream cleanup, NOT the brief's "remove loser cluster from training distribution".

Verdict-class resolves DETERMINISTICALLY at brief Section 8:

> **catastrophic-basin-shift (NEW per Critic Rec #1)**: F3: IS Sharpe Δ > +0.30 → Verdict: EXPLORATION-NEGATIVE-catastrophic-IS-overshoot; axis CLOSED at single-seed

/011 IS Δ = +0.4849 > +0.30. Pre-registered class fires. F1 PROMISING does NOT override — catastrophic-basin-shift explicitly carries "axis CLOSED" subsuming F1. The LM Master Phase 7.4 proposed `PROMISING-OVERSHOOT-BASIN-INHERITED` as NEW subtype — process improvement for FUTURE briefs, cannot retroactively re-classify /011.

Per Critic discipline ("when in doubt, FAIL"): EXPLORATION-NEGATIVE catastrophic-basin-shift.

### Check 13 — Anti-Pattern Static Scan: PASS

A1/A2/A3/A7/A8/A9/A10/A12/A13/A14 all PASS. No anti-pattern hits in QE's diff.

### Check 14 — Axis Family Validation: PASS

Brief Section 0.6 declares `risk-primitive` (binary-kill subtype). src/ diff is RULE-layer entry gate — declared family matches. Rotation: 1 of last 5 same family; rotation rule fires at 5/5 only. PASS.

CAVEAT (informational): within-family subtype distinction (binary-kill vs proportional-scaling) is structurally orthogonal at MECHANISM level — but did NOT produce empirical orthogonality. Basin-substrate dominates both subtypes. Future v1 risk-primitive subtypes at single-seed should be considered closed pending /015 multi-seed dissolution.

## QR Response Considered

Single-pass Phase 7.5 (no Round 1/2). Pre-registered gates resolve dual-firing deterministically.

## Recommendations to QR

1. **Pre-register `(F3 catastrophic AND F1 PROMISING)` cell in future briefs Section 8.** LM Master proposed `PROMISING-OVERSHOOT-BASIN-INHERITED` — Critic concurs as NEW v1 subtype. Codify: F3 catastrophic + F1 PROMISING + F6 < 61% = `EXPLORATION-NEGATIVE` subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`. OOS lift real-but-non-durable; binding constraint is multi-seed dissolution at /015.

2. **F6 roster-overlap diagnostic MUST be committed report artifact.** Future briefs with F6-style falsifiers must require QE to produce deterministic `f6_roster_overlap.csv`. Structural equivalent of dsr.json + comparison.csv contract.

3. **Engineering report mandatory at every Phase 7.5 dispatch.** /011's missing report is process integrity violation. Orchestrator should hard-reject any Phase 7.5 without QE report.

## Path Forward (mandatory on EXPLORATION-NEGATIVE)

LM Master Phase 7.4 establishes: at v1 single-seed=42 + n_trials=35 + V1_FEATURE_COLUMNS_PRUNED + ENSEMBLE_SIZE=3, the LTC-dominated Optuna basin re-discovered across axis primitives. Basin is SUBSTRATE-LOCKED, not axis-locked. /012 must probe basin dissolution at SUBSTRATE level.

Prior 5 EXPLORATION families: universe (/006), feature-family (/007 + /009), methodology (/008), risk-primitive (/010); /011 = risk-primitive again. UNUSED families: labeling, model-arch (closed at /003), hyperparameter-region (closed at /005).

3 axes proposed:

1. **Labeling axis — triple-barrier σ_t source** (UNUSED family at v1; Critic /010 Path Forward Option 2 carried forward). Replace fixed-fraction ATR multipliers with past-only EWMA σ_t-scaled barriers. Changes IS label distribution per cell → different LightGBM loss surface → ~70% prior probability of basin escape. Strongest substrate-dissolution probe in UNUSED-family menu.

2. **Methodology axis — per-cell early-stop with inner hold-out** (UNUSED since /008; Critic /010 Path Forward Option 3 carried forward). Within-fold early stopping via 20% inner hold-out. Changes WHICH trees retained per cell → different ensemble composition → different basin. Substrate-dissolving via tree-selection diversity.

3. **Substrate-dissolution PROBE EXPLORATION at /012** (sister-iteration; NOT CONFIRMATION). Rerun /011's EXACT R5-BINARY-KILL config (threshold=2.0) at single-seed=43. Cost: one EXPLORATION cell ≤2h. Tests LM Master Phase 7.4 hypothesis "basin is seed-property-driven, not axis-property-driven" DIRECTLY. If /012 (seed=43) diverges from /011 by >0.30 Sharpe, basin IS seed-locked → /015 multi-seed CONFIRMATION on R5-BINARY-KILL becomes unambiguous next step. If /012 reproduces /011 patterns, the (n_trials=35, 40-feature, ENSEMBLE=3) substrate is binding and basin cannot be unstuck at EXPLORATION budget. Highest-information-density experiment available within EXPLORATION budget.

Constraints: options 1 + 2 are UNUSED-family pure proposals; option 3 is sister-substrate probe (NOT same-axis-mechanism variation as /011).

HIGH-RISK pre-commit "if /011 PROMISING → /012 = multi-seed CONFIRMATION-SPEC" does NOT bind — /011 is EXPLORATION-NEGATIVE, catastrophic-basin-shift class explicitly says "axis CLOSED at single-seed". /015 CONFIRMATION-spec pre-commit on R5-BINARY-KILL voided per brief's own gates. Future risk-primitive substrate dissolution requires either (a) /015 CONFIRMATION on PROMISING axis from /012-/014, OR (b) /012-/014 substrate-dissolution sequence producing non-basin-inherited evidence.

## BLOCK-PENDING-FIX Rerun Protocol

N/A — verdict is EXPLORATION-NEGATIVE catastrophic-basin-shift, not BLOCK-PENDING-FIX. Defects (missing engineering report, missing F6 artifact, missing F4 detector surface) are RECOMMENDATIONS for future iterations, not fix-and-rerun for /011. /011 closed as EXPLORATION-NEGATIVE catastrophic-basin-shift; /012 advances per Path Forward.

# Phase 7.5 Critic Review — iter-v3/061

OVERALL: EXPLORATION-MERGE — INERT-AT-EXPLORATION certified clean; vol_scale_floor_per_symbol code retained; cycle 1 advances to #3 (iter-v3/062 axis = DSR_relative threshold/benchmark recalibration per /059 Rec #1).

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle 1 #2 of 10; FIRST per-symbol risk-primitive customization EXPLORATION in v3 history; Path B per QR EDA `d198b25` + Critic /060 Rec #3)

## QR Response Considered (Round 2 only)

Single-round FINAL review. The 13 standard Checks plus the §11 Anti-Pattern Static Scan plus the EXPLORATION-mode + Path B-specific concerns enumerated in the dispatch resolve unambiguously against the artifacts in `reports-v3/iteration_v3-061/`, the runner state at `17eea9a`, the new test file at `tests/strategies/ml/test_per_symbol_vol_scale_floor.py`, and the brief's pre-registered LOCKED criteria in Section 8 + Section 4.4. The two adversarially-flagged concerns (TRX IS wpnl Δ -0.161 vs Q4 IS counterfactual prediction +0.008; the 6w/6L floor-fired OOS split overpredicted by Q2 frac_below_05 win-skew prediction) are dispositioned in-line with Checks 7 and 8 — both are **predicted-effect counterfactual misses** but do NOT cross any pre-registered failure-mode threshold in Section 4.4. The brief's Q4 counterfactuals were estimates, not gates; the explicit gates (IS Sharpe shift > -0.20, OOS Sharpe shift > -0.10, BCH IS share ≥ 80%, trade-count bands, BCH/LDO |Δ| < 1.0) all PASS.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

Walk-forward fix at `src/crypto_trade/strategies/ml/walk_forward.py:113` intact: `train_end_ms = test_start_ms - embargo_ms` with `embargo_candles = compute_embargo_candles(10080, 480) = 22`. Grep on `train_end_ms\s*=\s*test_start_ms\s*$` returns zero matches — A1 absent. Triple-barrier labeling unchanged. The new code path at `risk_v2.py:608` (per-symbol floor dict lookup) is static-config; no historical-data access introduced.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3 — runtime-asserted. Walk-forward embargo of 22 candles. vol_scale_floor field is post-training-time runtime config; disjoint from embargo plumbing.

### Check 3 — Multiple-Testing Correction: PASS (per brief Section 8.4 EXPLORATION-mode informational)

Hard-blocking gates per brief Section 8.1 + Section 4.4 LOCKED:
- IS Sharpe shift > -0.20 vs /060 → observed Δ -0.009, PASS (cushion +0.19)
- OOS Sharpe shift > -0.10 vs /060 → observed Δ +0.015, PASS (cushion +0.12)
- BCH IS share ≥ 80% one-sided lower → observed 176.68%, PASS
- cpcv_frac_positive_paths ≥ 0.50 → observed 0.6444, PASS

DSR_relative=0.0 / Legacy DSR=0.0 — informational per brief Section 8.4 + `feedback_v3_dsr_mode_artifact.md`. PSR=0.9861 informational.

n_trials accounting verified: 315 = 35 × 3 × 3. n_eff=19 architecture-invariant. PBO=0.1278 identical to /060.

### Check 4 — IC Correlation: PASS (no new features at /061; matrix identical-by-construction to /060)

### Check 5 — ADF Stationarity: PASS (identical-by-construction to /060)

### Check 6 — Pareto Dominance: PASS (Gate 10-CPCV; frac_positive_paths 0.6444 ≥ 0.50 cleared)

ensemble_summary.json: mode=exploration, ensemble_size=3, seeds (191664963, 1662057957, 1405681631), all outer=42 lineage subset.

### Check 7 — Reproducibility: PASS

Commit SHAs verifiable: brief LOCK `af92efe`, code `6910fcf`, Phase 5.5 `17eea9a`. Trade-math spot check on 4 OOS trades — all match CSV to 4dp. **Row 3 TRX SHORT wf=0.5000 (floor-fired)**: weighted = 3.8091 × 0.5 = 1.90455 — matches CSV 1.9046. /060 counterpart had wf=0.4000; floor-fire confirmed at trade row level. BCH OOS rows BIT-IDENTICAL to /060 (verified row-by-row).

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 3 specified 5 substantive edits — all verified at code level:
1. `risk_v2.py:151` — `vol_scale_floor_per_symbol: dict[str, float] = field(default_factory=dict)`. VERIFIED.
2. `risk_v2.py:608-610` — floor lookup + np.clip. VERIFIED. **Floor applied AFTER existing vol-scale formula; INSIDE `_vol_scale`; AFTER all kill-gates in `get_signal`** — trade-selection invariance is mechanical.
3. `run_baseline_v3.py:1489` — `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` in `_build_v3_model`. VERIFIED.
4. `run_baseline_v3.py:745-752` — runtime assertion fires per model-build. VERIFIED. Cannot silently fall through.
5. `tests/strategies/ml/test_per_symbol_vol_scale_floor.py` — 3 tests structurally sound. VERIFIED.
6. ITERATION_LABEL = "v3-061" at line 128. VERIFIED.

No other change. Classification adjudicated: INERT-AT-EXPLORATION is correctly assigned per Section 8.1/8.2.

**Q4 counterfactual miss adjudication**: Brief Q4 IS counterfactual +0.008 wpnl → observed -0.161 (20× miss with sign flip). NOT a methodology violation — Q4 was an estimate not a falsifier; Section 4.4 binding gate (IS Sharpe shift > -0.20) PASSES with cushion +0.19. Section 2.2 IS reading was qualitatively consistent with the observed -0.161 direction. See Recommendation #3 below for process-level discipline.

### Check 9 — Symbol Exclusion: PASS
### Check 10 — Feature Isolation: PASS
### Check 11 — Forming-Candle: PASS (3.2h lag at gate time)
### Check 12 — Library Version: PASS (UNCHANGED from /060)

### Check 13 — Per-symbol vol_scale_floor wiring + behavioral audit: PASS

Five Path B-specific audits per dispatch:

1. **Floor clip applied AFTER existing vol-scale formula** — VERIFIED at risk_v2.py:608-610.
2. **No leakage to non-target symbols** — VERIFIED at three levels (dict `.get(symbol, fallback)` lookup; isolation test; empirical zero-delta BCH+LDO across IS+OOS).
3. **Per-symbol config dict consistently read** — VERIFIED. `_vol_scale` called per-signal; dict on frozen dataclass; `field(default_factory=dict)` produces fresh per-instance dict.
4. **vol_scale_floor_per_symbol code RETAIN** — methodology rationale: backward-compatible default; future cycle 1+ EXPLORATIONs may re-test per-symbol risk-primitive customizations; small structural footprint (1 field + 1 line).
5. **6w/6L floor-fired OOS pattern + Welch t-NON-significant from /060 Q7** — confirms null hypothesis on TRX RiskV2 anti-Kelly. **TRX RiskV2 anti-Kelly axis CLOSED for cycle 1 carry-forward** — no further per-symbol vol_scale_floor intervention warranted at single-EXPLORATION.

## §11 Anti-Pattern Static Scan (A1-A13)

- **A1** (`train_end_ms = test_start_ms` without embargo): zero matches — PASS
- **A2** (Optuna `n_jobs=2` GIL contention): zero matches in `src/crypto_trade/` — Phase A revert at `31665f6` intact — PASS
- **A3** (master-data-extent invariance): walk-forward fix at `e149e9d` inherited — PASS
- **A4** (track isolation): grep clean — PASS
- **A5/A6/A7**: identical to /060 audit — PASS
- **A8** (stateful gate deadlock): per-symbol drawdown brake disabled; Path B is STATELESS (no rolling state) — A8 absent by construction — PASS
- **A9** (ensemble_seeds threading): seeds populated from ENSEMBLE_SEEDS[0:3] — PASS
- **A10** (feature isolation): PASS
- **A11** (V3_EXCLUDED_SYMBOLS audit): runtime assertion fires — PASS
- **A12** (DSR/PSR granularity input mismatch — iter-v3/056 lesson): granularity gap persists at /061 (dsr_relative=0.0 + cpcv_q75=0.838) — flagged informational per brief Section 8.4; iter-v3/062 axis addresses this. PASS at /061.
- **A13** (written-before-read): `cpcv_path_sharpe_q75` from in-memory `flat_path_sharpes`, not disk — PASS.

Path B-specific anti-pattern audit:
- No silent global-shadow on `floor` variable
- No side-channel into trade selection (vol_scale gate is downstream of all kill-gates)
- No interaction with disabled state primitives

## EXPLORATION-mode concerns dispositioned

- Trade-selection invariance VERIFIED at trade-row level
- vol_scale_floor_per_symbol dict default safety VERIFIED
- Runtime assertion teeth VERIFIED
- Test suite coverage 34/34
- DSR_relative=0.0 artifact carried from /060 (not a /061 defect)

## Adversarial Adjudication — Counterfactual Miss vs Falsifier Pass

Brief Section 2.4 Q4 IS counterfactual +0.008 → observed -0.161 wpnl. 20× magnitude miss with sign flip. **Adjudication**: NOT a methodology violation. Q4 was a partition-Method-B-restated counterfactual; not a deterministic claim. Pre-registered Section 4.4 falsifier list does NOT bound TRX IS wpnl Δ explicitly. IS Sharpe shift gate (-0.20 lower) is the binding macro-level gate at -0.009 observed — PASS with cushion +0.19. Process-level Recommendation #3 below codifies the per-symbol Δ band falsifier discipline for future briefs.

## Recommendations to QR

1. **iter-v3/062 axis = DSR_relative threshold/benchmark recalibration** (carried from /059 Critic FINAL `0fc18c2` Rec #1, restated by Engineer Recommendation #1). The dsr_relative=0.0 + cpcv_path_sharpe_q75=0.838 mismatch is now a 3-iteration-stale artifact (/059, /060, /061). Address via either (a) recalibrate DSR_relative threshold from 0.95 → 0.50-0.60 under unified architecture; OR (b) reformulate the input-granularity match (annualize trade-level Sharpe OR de-annualize path Sharpe so both inputs to psr() share scale). Brief Section 8.7 STRUCTURAL row explicitly defers this to /062.

2. **iter-v3/063 mass feature expansion mandate preparation** (per `feedback_v3_mass_feature_expansion.md`; Engineer Rec #2). Begin feature research in parallel with /062 execution; cycle 1 #4 mandate requires V3_FEATURE_COLUMNS_TOP_N from 14 → TARGET 100 (50 minimum). Sources: TA-lib, microstructure, cross-asset (basis, funding), regime-encoding. Critic /060 Rec #2 emphasized that /060 anchor with 2-of-3 symbols IS-negative is fragile; structural feature expansion is the cleanest path to lifting all-symbols-IS-positive multi-seed.

3. **NEW process rule — future per-symbol counterfactual EDA briefs MUST pre-register a target-symbol-axis wpnl Δ falsifier band**. The /061 brief pre-registered BCH/LDO IS+OOS bands at ±1.0 wpnl but did NOT pre-register a TRX IS wpnl band — the Q4 +0.008 estimate became implicit-acceptance. Future briefs should explicitly state e.g. "TRX IS wpnl Δ falsifier band [-1.0, +1.0]" so the Q4-counterfactual-vs-observed gap has a formal gate. Engineer's loose citation of "Section 4.3 falsifier band |delta| < 1.0" (which is the BCH/LDO row, not a TRX IS row) is a process discipline gap. Adding the per-target-symbol-axis band to the per-symbol-EDA template prevents future implicit acceptance.

# Phase 5.5 Gate — iter-v3/118

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24 and training_months=24 explicitly confirmed unchanged. IS/OOS windows named in absolute dates. Parameter provenance table declared for all 4 design parameters (rolling-median window 200 = hand-chosen with rationale; threshold offset = structural; sign convention = structural; primitive lookbacks = inherited). No laundered provenance. EDA temporal fence: all scripts assert `close_time < OOS_CUTOFF_MS = 1742774400000`; 0 OOS-leaked rows across BCH (5483/0), LDO (2497/0), TRX (5425/0) confirmed in EDA commit `60a45e8`.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION declared; cycle-6 slot #9 of 10 stated; /120=CONFIRMATION stated; /116 no_confirm bundle plan at /120 not touched; CLI invocation with `--n-trials 35 --exploration --bar-interval 8h` specified.
- Section 1 (Hypothesis): PASS — Single sentence: adds `ema_signed_volregime` (ema_spread_atr_20 × sign(range_realized_vol_50 − rolling_median_200)) to V3_FEATURE_COLUMNS_TOP_N as 15th feature, expecting positive IS monthly Sharpe Δ via vol-regime-conditioned momentum at slower (~67-day) timescale than /025 baseline's hurst-regime. Mechanism distinguishes it from all prior dead axes.
- Section 2 (IS-Only Evidence): PASS — Committed EDA at SHA `60a45e8` (committed BEFORE brief). 9 result tables (T1–T9 CSVs). 6-candidate screen with cross-verified numbers: T2 R² values confirmed against CSV (C3 POOLED R²=0.1963, max|corr|=0.212 — clean PASS, no carve-out needed); T3 univariate AUC confirmed informational for C3 (p=0.610, gate acknowledged as non-controlling); T5 importance rank confirmed (rank 8-10/15, gain 38-63% all 3 symbols — only candidate clearing 30% gain bar universally); T9 multivariate lift confirmed against CSV (BCH=−0.0039, LDO=−0.0106, TRX=+0.0082, POOLED=+0.0081). POOLED lift gate (>0.005) clears. /060 anchor IS=+0.8325 and OOS=+0.1403 confirmed against `reports-v3/iteration_v3-060/comparison.csv`. Synthesis document present.
- Section 3 (Proposed Changes): PASS — Enumerated table. Single axis: V3_FEATURE_COLUMNS_TOP_N 14→15 (adds `ema_signed_volregime`). All 16 accretion-guard knobs explicitly stated unchanged. `/116 no_confirm REVERTED` state (`enable_no_confirm_exit=False`) confirmed in knob table at line 286.
- Section 3.5 (Code-Change Manifest): PASS with advisory note — Six changes specified: (1) `compute_ema_signed_volregime` function in `engineered_v3.py` with full docstring and implementation; (2) `V3_FEATURE_COLUMNS_TOP_N` 15th element in `features_v3/__init__.py`; (3) runner feature-count guard updated 14→15; (4) parquet regeneration CLI command with verification step; (5) unit test for past-only invariant; (6) adversarial integration test. `add_engineered_v3_features` dispatch update specified. GROUP_REGISTRY note: no new entry needed (C3 dispatched via existing `engineered_v3` entry; correctly handled by specifying the `add_engineered_v3_features` update). `/117 24h-multi-offset REMAINS in code but UNUSED` confirmed ("No changes to multioffset_24h.py"). `/116 no_confirm REVERTED` state preserved — the runner's 3 existing surfaces (model builder line 2006, accretion guard line 1119, pre-flight assertion line 2928) all currently set to `False`; brief does not enumerate the 3 surfaces explicitly but states "STAYS REVERTED" and "enable_no_confirm_exit=False" which is confirmed correct in the current runner. ADVISORY NOTE (not a block): Section 3.5 does not include a Change 6 equivalent for `ITERATION_LABEL="v3-118"` and `MODEL_SPECS` prefix `"v3-118-BCH/LDO/TRX"` (runner currently reads `"v3-117"`). The convention is deterministic (v3-NNN) and does not block implementation, but deviates from /117 brief precedent which specified it explicitly. Phase 6 Engineer: update ITERATION_LABEL at line 131 and MODEL_SPECS at lines 198-200.
- Section 4 (Expected OOS Impact): PASS — Modal band stated (IS Δ ∈ [+0.05,+0.30]; OOS Δ ∈ [+0.05,+0.25]). Explicit falsifier: OOS Δ < −0.50 AND IS Δ < −0.20 → FALSIFIED. Trade-rate prediction (±15% IS, ±25% OOS). Behavioral-effect predictor: common-trade fraction 60-80%; >95% → INERT (saturated-axis pattern). Anchors stated (IS +0.8325, OOS +0.1403).
- Section 5 (Risk Mitigation): PASS — 5 risks with mitigations and IS-calibrated thresholds. R1 (univariate absent) addressed via multivariate-lift controlling criterion. R2 (per-symbol asymmetry) addressed via Mode 3 pre-registration. R3 (importance INERT) addressed via T5+T9 cross-reference diagnostic. R4 (look-ahead) addressed via unit test. R5 (parquet missing) addressed via Change 4 + runner hard assertion. IC gate: C3 R²=0.196 (max|corr|=0.21 POOLED) is below the 0.50 threshold — clean PASS, no carve-out invocation needed. The `feedback_v3_engineered_feature_pivot.md` carve-out (importance ≥ 30) is correctly noted as applying to C1/C2/C4/C6 (algebraic-identity compositions), not to C3.
- Section 6 (Risk Management Design): PASS — 7-gate RiskV2 stack documented as unchanged with all gate parameters specified (vol_scale_floor={}, ADX=20.0, hurst regime, z-score 2.0, low-vol filter, hit-rate feedback, BTC trend). No new primitive. Hard-merge gate table for /120 CONFIRMATION provided.
- Section 7 (Failure-Mode Prediction): PASS — 5 modes pre-registered with probabilities and first-match-wins logic. Mode 1 (success, 30%), Mode 2 (importance INERT, 20%), Mode 3 (PROMISING-PARTIAL TRX-led, 20%) with explicit numerical conditions (TRX IS PnL Δ ≥ +2.0% AND BCH or LDO IS PnL Δ < −1.0%), Mode 4 (catastrophic, 10%), Mode 5 (null, 20%). Mode 3 PROMISING-PARTIAL fully described with modal-outcome description. Two tail modes (Mode 6 suspicious-OOS-dominant, Mode 7 suspicious-IS-dominant). Section 8 criteria reference Section 7 modes consistently.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 6 first-match-wins criteria locked before backtest. 3 NEGATIVE paths (catastrophic, no-effect, clean) and 3 PROMISING paths (strong, partial, INERT-risk) with explicit numerical thresholds. Anchor declared (IS +0.8325, OOS +0.1403 vs /060; secondary anchor /059 IS +1.0894/OOS +0.5791 stated).
- Section 9 (Library Stack): PASS — lightgbm==4.6.0, numpy>=2.0, pandas>=2.2, scikit-learn (EDA only). No new library dependencies. Adversarial integration test specified at Change 6: V3_FEATURE_COLUMNS includes `ema_signed_volregime`; parquet column non-NaN on last 100 IS rows; n_features==15 guard; Change 5 unit test passes. These 4 assertions cover the end-to-end integration boundary.

## Reasons (if BLOCK)

N/A — OVERALL=PASS.

## Advisory Notes (non-blocking, for Phase 6 Engineer)

1. Section 3.5 does not specify `ITERATION_LABEL="v3-118"` and `MODEL_SPECS` prefix `"v3-118-BCH/LDO/TRX"` as a named change. The runner currently reads `ITERATION_LABEL="v3-117"` (line 131) and `MODEL_SPECS = [("v3-117-BCH", ...), ("v3-117-LDO", ...), ("v3-117-TRX", ...)]` (lines 198-200). Phase 6 must update these as part of the standard runner housekeeping (the convention v3-NNN is deterministic). Without this update, reports would be written to `reports-v3/iteration_v3-117/` and model names would carry `/117` prefix — silent output corruption. Update as Change 0 (before any other change).

2. The runner pre-flight assertion at line 2929 reads "for iter-v3/117" in its error string. Phase 6 should update this string to "iter-v3/118" for traceability (no logic change; string update only).

## Verification Checklist

- [x] EDA committed before brief (SHA `60a45e8` < `26dd346`)
- [x] EDA IS-only fence confirmed (OOS_CUTOFF_MS=1742774400000; 0 OOS rows in all 3 symbols)
- [x] T9 CSV numbers match brief (BCH=-0.0039, LDO=-0.0106, TRX=+0.0082, POOLED=+0.0081)
- [x] /060 anchor confirmed from comparison.csv (IS=0.8325, OOS=0.1403)
- [x] Single-axis discipline: only change is 1 new column in V3_FEATURE_COLUMNS_TOP_N
- [x] OOS_CUTOFF_DATE and training_months unchanged
- [x] Sacred 5-seed inner ensemble unchanged (ENSEMBLE_SIZE=3 for EXPLORATION-mode)
- [x] /116 no_confirm REVERTED confirmed in runner (lines 1119, 2006, 2928 all False)
- [x] 24h-multi-offset code present but dormant (--bar-interval defaults 8h)
- [x] Cycle-6 slot count: /110-/117 = 8 preceding EXPLORATIONs confirmed in catalog; /118 = slot 9
- [x] V3_FEATURE_COLUMNS_TOP_N currently 14 features confirmed (engineered_v3 + __init__ checked)
- [x] test_engineered_v3.py test file exists for adding Change 5
- [x] Mode 3 PROMISING-PARTIAL pre-registered with explicit numerical thresholds
- [x] IC gate: C3 max|corr|=0.21 POOLED < 0.50 — no carve-out invocation needed

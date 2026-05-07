# Phase 5.5 Gate — iter-v3/018

OVERALL: PASS

## Iteration Type
TYPE: CONFIRMATION (first true v3 CONFIRMATION)
Runner invocation: `uv run python run_baseline_v3.py --seeds 2 --n-trials 50` (NO --exploration flag)

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` IMMUTABLE; `training_months = 24` IMMUTABLE; `ENSEMBLE_SIZE = 5` confirmed at runner line 86; `colsample_bytree` Optuna-tuned (non-exploration mode); `n_trials = 50` confirmed at runner line 1324 default; outer_seeds=2 via `--seeds 2` CLI
- Section 0.5 (Iteration Type Declaration): PASS — TYPE: CONFIRMATION declared; "first true v3 CONFIRMATION ever"; 4h HARD CAP stated; "NOT bundle assembly; multi-seed validation of iter-v3/013 baseline"; `feedback_v3_iter018_confirmation_baseline_validation.md` referenced as pre-commitment lock; CONFIRMATION-MERGE updates BASELINE_V3.md if all 10 gates pass
- Section 1 (Hypothesis): PASS — single sentence: "iter-v3/013's IS +1.0088 / OOS +2.6970 monthly Sharpe HOLDS under multi-seed cross-validation rigor (5 inner × 2 outer = 10 models per cell, n_trials=50), with all v3 methodology gates passing at non-EXPLORATION thresholds"; testable and specific (11 mechanical gates named)
- Section 2 (IS-Only Evidence): PASS (CONFIRMATION structural difference acknowledged) — brief explicitly documents WHY no new IS-only analysis script is needed for a CONFIRMATION (CONFIRMATION validates prior, not discovers new signal); inherited iter-v3/013 baseline committed at SHA `e3168f2` serves as the prior; metric tables present with per-symbol OOS attribution and per-cell PBO diagnostics; the structural difference is documented and justified
- Section 3 (Proposed Changes): PASS — symbols/labeling/features/risk-gates ALL UNCHANGED per §3.1-3.4 (explicitly stated); multi-seed config is the single changed axis per §3.5; §3.6 sub-fix decomposition enumerates 10 verifiers; §3.7 19-row reconciliation table with executable verifier commands; NO new feature/labeling/gate/universe changes present (CONFIRMATION-only gate satisfied)
- Section 4 (Expected OOS Impact): PASS — predicted multi-seed Sharpe bands [IS +0.85, +1.20] / [OOS +1.50, +2.40]; LDO concentration prediction [25%, 55%]; bundle OOS trade count prediction [130, 200]; DSR/PBO/PSR prediction bands; 3 fragility tests F1/F2/F3; CONFIRMATION outcome interpretation table; explicit falsifiers for each metric band
- Section 5 (Risk Mitigation): PASS — 4 cadence-discipline structural safeguards; 5 methodology-pipeline safeguards; 4 multi-seed-axis specific risks; LDO concentration management with binding gate clarification; per `feedback_risk_mitigation_design.md` simulated effect IS iter-v3/013 baseline already committed
- Section 6 (Risk Management Design): PASS — 7-primitive table present (vol scaling, ADX gate, Hurst regime, z-score OOD, low-vol filter, hit-rate feedback DISABLED, BTC trend alignment); fire-rate predictions per primitive; regime coverage documented; concentration classified as BINDING at CONFIRMATION; concentration exception clause requires 3 structural conditions simultaneously
- Section 7 (Pre-Registered Failure-Mode): PASS — 9 predictions (P1-P9); 4 process-level failures (P1 trade-rate, P3 PBO max-aggregator tails, P4 wall-clock, P6 DSR); 5 model-level (P5 10-seed validation, P7 MERGE pathway, P8 LDO fragility, P9 Sharpe floors missed); calibrated MERGE pathway probability ~35%/~30%/~25%/~10%; each prediction has detection signal and mitigation
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 10 MERGE gates locked pre-backtest; 3 verdict pathways (CONFIRMATION-MERGE / NO-MERGE-METHODOLOGY / NO-MERGE-FRAGILITY); 4 BLOCK conditions; "ALL 10 gates must pass; any single gate failure = NO-MERGE" explicitly stated; no QR or Critic discretion can override gate failures; PBO gate specifies BOTH mean AND max-aggregator must pass
- Section 9 (Library Stack): PASS — all packages listed with versions/licenses; no new external deps; fallback handling for pyarrow; reproducibility stamp requirements enumerated; XGBoost and meta-labeling remain opt-in (not activated for this run)

## CONFIRMATION-Only Gate: No New Axis Variations

PASS — verified. Brief §3.1-3.4 confirm symbols/labeling/features/risk-gates are byte-identical to iter-v3/013. The only changed parameter is the multi-seed configuration (--seeds 2, ENSEMBLE_SIZE=5, n_trials=50, colsample_bytree Optuna-tuned). This is a pure validation run, not a new axis exploration.

## Pre-Flight Verifier Results (run before gate commit)

| Verifier | Command | Result |
|---|---|---|
| V3_FEATURE_COLUMNS length 13 | `from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13` | PASS — 13 cols confirmed |
| vwap_dev_50 absent | same import, assert 'vwap_dev_50' not in | PASS |
| tbr_zscore_30 absent | same import, assert 'tbr_zscore_30' not in | PASS |
| REQUIRED_GAP == 66 | `from validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66` | PASS |
| ENSEMBLE_SIZE == 5 | `import run_baseline_v3; assert ENSEMBLE_SIZE == 5` | PASS |
| _derive_ensemble_seeds(42, 5) returns 5 ints | same import, len check | PASS — [191664963, 1662057957, 1405681631, 942484272, 929893137] |
| V3_MODELS has 3 entries, no MKR | runner import | PASS — (BCH, LDO, TRX) |
| atr_tp_multiplier=2.0 | grep on runner | PASS — line 877 |
| atr_sl_multiplier=1.0 | grep on runner | PASS — line 878 |
| zscore_threshold=2.0 | grep on runner | PASS — line 897 |
| threshold_pct=15.0 | grep on runner | PASS — line 123 |
| default --n-trials == 50 | grep `default=50` | PASS — line 1324 |
| ensemble_size_for_run code path | grep exploration branch | PASS — line 1371 |
| fast_mode_for_run code path | grep bool(args.exploration) | PASS — line 1372 |
| argparse --seeds 2 --n-trials 50 | run --help | PASS — both args accepted |
| Unit tests | `uv run pytest tests/strategies/ml/ -v` | PASS — 57/57 passed |

## Reasons (if BLOCK)
None — OVERALL: PASS. Proceed to Phase 6.

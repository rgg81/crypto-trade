# Phase 5.5 Gate — iter-v3/067

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` confirmed unchanged. IS window named as 24-month walk-forward ending 2025-03-23. OOS window named as 2025-03-24 onward (14 months). Symbol universe = BCHUSDT, LDOUSDT, TRXUSDT (unchanged from /051 SYSTEM-LEVEL REVERT).
- Section 1 (Hypothesis): PASS — ONE sentence. "UNIVERSAL inference-time confidence-threshold TIGHTENING ... produces ≥+0.10 IS Sharpe AND ≥+0.20 OOS Sharpe vs /060 baseline." Specific falsifier bands stated. Includes honest probability distribution (INERT ~45% most likely).
- Section 2 (IS-Only Evidence): PASS — committed script `analysis/iteration_v3-067/ensemble_parameters_eda.py` at EDA SHA `aa5b0c8`. Produces 7 tables (T0-T6) with concrete numbers. T0 anchor values are bit-exact references to `reports-v3/iteration_v3-060/comparison.csv` line numbers. No category-matching.
- Section 3 (Proposed Changes): PASS — 11 enumerated sub-fixes: (1) lgbm.py:507 floor application, (2) `_inference_threshold_floor` constructor param, (3) runner passes 0.60, (4) REVERT vol_scale_ceiling to default 1.0, (5) DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0), (6) ITERATION_LABEL bump, (7) new test file, (8) runtime assertion, (9) no parquet regen needed, (10) ENSEMBLE_SIZE unchanged, (11) V3_FEATURE_COLUMNS_TOP_N unchanged at 14. Scope explicitly excludes per-symbol customizations.
- Section 4 (Expected OOS Impact): PASS — predicted bands with confidence intervals: IS Δ ∈ [-0.28, +0.22], OOS Δ ∈ [-0.34, +0.36]. Explicit falsifiers enumerated as Gates A.1-E.18, including new Path-D-specific Gate D.15 (over-tightening). NEGATIVE probability ≥25% explicitly stated per Rule 3 calibration.
- Section 5 (Risk Mitigation): PASS — 14-row primitive table covering all risk gates (vol scaling, ADX, Hurst, z-score OOD, low-vol, BTC contagion, per-symbol cap, regime-conditional kill, direction-asymmetric kill, drawdown brake, per-symbol vol_scale_floor, vol_scale_ceiling revert). IS-calibrated threshold (0.60) stated with structural rationale. Orthogonality with all other primitives verified.
- Section 6 (Risk Management Design): PASS — all 11+ primitives addressed; single substantive change is `LightGbmStrategy._inference_threshold_floor = 0.60` (GATE modifier). vol_scale_ceiling REVERTED to 1.0 explicitly documented. Live trading translation described.
- Section 7 (Failure-Mode Prediction): PASS — 4-mode probability table (INERT 45%, PROMISING 25%, SUSPICIOUS-OOS-DOMINANT 5%, NEGATIVE 25%). NEGATIVE probability ≥25% per Rule 3. Each mode has expected metrics description. Specific failure scenarios (over-tightening via D.15, BCH dominance regression, Optuna saturation) described in forward-looking paragraphs.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — 6 locked classification paths (PROMISING, INERT, SUSPICIOUS-OOS-DOMINANT, NEGATIVE, NEGATIVE-OVER-TIGHTENING, Methodology FAIL) with explicit numerical thresholds. NEW Gate D.15 over-tightening classifier pre-registered. Disjunctive-OR NEGATIVE per Rule 4. Trade-rate floor pre-committed as INFORMATIONAL at EXPLORATION / BLOCKING at /069 CONFIRMATION.
- Section 9 (Library Stack): PASS — Python 3.13, LightGBM, pandas, pyarrow, statsmodels. Code paths enumerated (lgbm.py:507, lgbm.py __init__, run_baseline_v3.py `_build_v3_model`). Integration test command provided. Reproducibility stamp: EDA SHA `aa5b0c8`, ITERATION_LABEL `v3-067`, `_inference_threshold_floor=0.60`, `vol_scale_ceiling=1.0 (default)`.

## Implementation Verification (Engineer checks)

### Code changes verified

| Check | Result |
|---|---|
| `ITERATION_LABEL = "v3-067"` | PASS — `run_baseline_v3.py:128` |
| `inference_threshold_floor: float = 0.0` in `LightGbmStrategy.__init__` | PASS — `lgbm.py:144` |
| `self._inference_threshold_floor = float(inference_threshold_floor)` stored | PASS — `lgbm.py:188` |
| `max(np.mean(self._confidence_thresholds), self._inference_threshold_floor)` at lgbm.py:515 | PASS |
| `inference_threshold_floor=0.60` passed in `_build_v3_model` (lgbm branch only) | PASS — `run_baseline_v3.py:~1432` |
| `vol_scale_ceiling=0.8` REMOVED from `_build_v3_model` RiskV2Config | PASS — reverted to default 1.0 |
| /066 `vol_scale_ceiling == 0.8` assertion REPLACED by /067 assertion | PASS — new assertion at `run_baseline_v3.py:~691` checks `_inference_threshold_floor == 0.60` AND `vol_scale_ceiling == 1.0` |
| `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` UNCHANGED | PASS — `src/crypto_trade/features_v3/__init__.py:222` |
| `V3_FEATURE_COLUMNS_TOP_N` count = 14 | PASS — runtime verified |

### Section 2 anchor values (Critic /064/065 Rec #1 byte-correctness gate)

All T0 anchor values verified against brief Section 2.1:

| Metric | Brief value | Source cited | Status |
|---|---|---|---|
| BCH OOS weighted_pnl | +1.9078 | comparison.csv:18 | PASS |
| LDO OOS weighted_pnl | -19.7208 | comparison.csv:19 | PASS |
| TRX OOS weighted_pnl | +23.3119 | comparison.csv:20 | PASS |
| OOS n_trades | 102 | comparison.csv:7 | PASS |
| IS monthly_sharpe | +0.8325 | comparison.csv:2 | PASS |
| OOS monthly_sharpe | +0.1403 | comparison.csv:2 | PASS |

### Section 3 enumeration check

5 key sub-fixes enumerated per brief:
1. lgbm.py:507 floor application — PRESENT (Sub-fix 1)
2. `_inference_threshold_floor` constructor parameter — PRESENT (Sub-fix 2)
3. Runner passes 0.60 in `_build_v3_model` — PRESENT (Sub-fix 3)
4. REVERT vol_scale_ceiling to default 1.0 — PRESENT (Sub-fix 4)
5. DEFAULT_ATR_MULTIPLIERS UNCHANGED (2.0, 1.0) — PRESENT (Sub-fix 5)

Additional sub-fixes 6-11 (ITERATION_LABEL, test, assertion, no parquet regen, ensemble unchanged, features unchanged) all PRESENT.

### Section 4 predicted bands with Path D-specific falsifier

- IS Δ band [+0.05, +0.20] per EDA T4 — PRESENT
- OOS Δ band [+0.10, +0.30] per EDA T4 — PRESENT
- Gate D.15 over-tightening falsifier (trade-count Δ ≤ -50% AND Sharpe Δ ≤ -0.10) — PRESENT at Section 4.3 and Section 8.5
- Gate C.7 OOS trade-rate floor flagged INFORMATIONAL at EXPLORATION — PRESENT at Section 4.5

### Section 7 NEGATIVE probability

- NEGATIVE probability = 25% (≥25% per Rule 3) — PASS

### Section 8 LOCKED criteria

- Gate D.15 over-tightening classifier NEW — PRESENT
- Disjunctive-OR NEGATIVE per Rule 4 — PRESENT at Section 8.4
- Trade-rate floor pre-committed INFORMATIONAL/BLOCKING boundary — PRESENT at Section 8.1 + 4.5

### Invariant checks

| Check | Result |
|---|---|
| `OOS_CUTOFF_DATE = 2025-03-24` | PASS — sacred constant unchanged |
| `training_months = 24` | PASS — sacred constant unchanged |
| 5-seed inner ensemble (via `_derive_ensemble_seeds`) | PASS — ENSEMBLE_SIZE=5 unchanged |
| V3_FEATURE_COLUMNS_TOP_N count = 14 | PASS |
| DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) | PASS |
| Track isolation (`from crypto_trade.features ` absent in features_v3/) | PASS (no change to feature pipeline) |
| Linter / formatter | PASS — `uv run ruff check` clean |
| Tests (new 3 + critical adjacent modules) | PASS — 42/44 pass; 2 pre-existing failures unrelated to /067 (test_v3_feature_count.py asserting /064's adx_14 which was reverted; pre-dates /067) |
| Mode-flag wiring (--exploration ENSEMBLE_SIZE=3) | PASS — no change to exploration flag plumbing |
| Data freshness | PASS — no new data required; inference-time gate change only; no parquet regen needed |

## Reasons

No blocking concerns. All 10 sections PASS. Implementation matches brief spec exactly.

## Implementation commit SHA

`ae50dfd` — `feat(iter-v3/067): confidence-threshold floor at 0.60 + REVERT /066 ceiling`

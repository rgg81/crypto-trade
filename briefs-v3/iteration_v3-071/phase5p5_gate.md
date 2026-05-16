# Phase 5.5 Gate — iter-v3/071

OVERALL: PASS

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24 confirmed in runner (lines 81-82). REQUIRED_GAP=66=(21+1)×3 confirmed. Walk-forward lookahead fix inherited from /060 (post-`e149e9d`). IS/OOS windows declared.
- Section 0.5 (Iteration Type): PASS — EXPLORATION, cycle 2 #1 of 10, structural model-arch axis (mandated). Run mode and anchor stated.
- Section 1 (Hypothesis): PASS — One specific, testable sentence: MetaLabelingStrategy (M1+M2, M2 vetoing signals with M2-confidence < 0.5) lifts IS AND OOS monthly Sharpe >= +0.10 vs /060 anchor by filtering low-quality M1 signals (primarily LDO directional bleed).
- Section 2 (IS-Only Evidence): PASS — EDA committed at SHA `4f32ec5` (`analysis/iteration_v3-071/metalabeling_eda.py` + 7 output files). T0 anchor values byte-exact vs /060 comparison.csv (verified: IS +0.8325, OOS +0.1403, OOS n_trades=102, per-symbol BCH/LDO/TRX values all confirmed). T1-T5 tables present with numerical basis. Decision rule pre-registered in EDA script.
- Section 3 (Proposed Changes): PASS — Single-axis change: `--model metalabeling` CLI flag. ZERO new strategy code. ITERATION_LABEL "v3-070" → "v3-071" (line 128 confirmed). M2 configuration (threshold=0.5 PINNED, feature set M1's 14 + confidence, label=pnl>0) all inherited and unchanged. Cross-axis table provided.
- Section 4 (Expected OOS Impact): PASS — Pre-registered bands with probabilities. PROMISING: IS >= +0.9325 AND OOS >= +0.3403 (uses stricter memory-rule OOS +0.20 threshold, correctly overrides prompt's +0.10). NEGATIVE: IS < +0.7325 OR OOS < -0.0597. SUSPICIOUS: OOS/IS ratio > 3.0 (pre-registered per `feedback_v3_oos_is_ratio_gate.md`). Saturation falsifier (S4.5): IS trade count >= 155 AND per-symbol shift < 3 = NULL-RESULT. Per-symbol delta predictor (S4.6): BCH/TRX -10 to -20, LDO -2 to 0. BCH IS concentration sensitivity check pre-registered (S4.7).
- Section 5 (Risk Mitigation): PASS — 7-primitive RiskV3Wrapper gate stack unchanged. M2 framed as precision/risk filter (not a NEW risk primitive — transparent wrap). Look-ahead audit: M2 trains exclusively on train-window data (metalabeling.py:351-534 reviewed). Trade-rate-floor risk acknowledged (T5, all scenarios below 10/month floor — treated informational per BASELINE_V3.md precedent, with <52-trade safety-net flag).
- Section 6 (Risk Management Design): PASS — 7-primitive table present (BTC trend kill, vol scaling, ADX, Hurst, z-score OOD, low-vol filter, hit-rate disabled). Risk primitives operate transparently on M2-passed signals. Over-filtering risk identified and mitigated by 0.5 threshold pinning.
- Section 7 (Failure-Mode Prediction): PASS — PATH C/INERT 40% (dominant), NEGATIVE 35%, PROMISING 15%, SUSPICIOUS 10%. Process predictions P1-P3 (wall-clock, LDO M2 inactivity, integration risk). Pre-registered most-likely outcome PATH C. Honest framing re: T3 thin-margin.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — All classification thresholds pre-registered and locked. Precedence hierarchy stated (SUSPICIOUS > NEGATIVE > INERT > PROMISING). Section 8.5 trade-rate-floor safety net (<52 OOS trades = thin-sample flag). PATH C and NULL-RESULT sub-flavors distinguished.
- Section 9 (Library Stack): PASS — No new external dependency. LGBMClassifier reuses pinned lightgbm 4.6.0. Full pinned stack listed (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1). Integration-test mandate carve-out correctly cited (model-arch change, not methodology-only axis). Existing 11 unit tests sufficient.
- Section 10 (QR Audit Trail): PASS — Axis origin: MANDATED (feedback_v3_iter017_metalabeling_mandate.md + /070 Phase 8 diary Section 10 priority #1). EDA SHA `4f32ec5`. Path selection rationale (A/B/C/D comparison). Honest framing of T3 thin-margin clearing Path A bar.

## Technical Verification Results

### ITERATION_LABEL
run_baseline_v3.py:128 — `ITERATION_LABEL = "v3-071"` CONFIRMED.

### MetaLabelingStrategy wiring
- `--model metalabeling` is a valid choice in argparse (run_baseline_v3.py:2032) CONFIRMED.
- `model_type == "metalabeling"` branch at lines 1487-1492 wires `MetaLabelingStrategy(**common_kwargs)` CONFIRMED.
- `feature_columns=list(features_for_symbol(symbol))` passed explicitly (line 1483) — never None CONFIRMED.
- `_write_feature_importance` M1-unwrap at lines 1818-1823 for MetaLabelingStrategy CONFIRMED.

### Post-/070 codebase state
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)` — CONFIRMED (features_v3/__init__.py:226; revert commit `8bdf392`).
- `V3_FEATURE_COLUMNS_TOP_N` count = **14** — CONFIRMED (uv run: 14 features listed; adx_14 absent per /064 NEGATIVE).
- `V3_MODELS` = (BCHUSDT, LDOUSDT, TRXUSDT) 3 symbols — CONFIRMED (run_baseline_v3.py:141-145).
- `REQUIRED_GAP = 66` — CONFIRMED (validation_v3.REQUIRED_GAP via uv).
- Path B4 reporting infrastructure retained — CONFIRMED (run_baseline_v3.py:1724,2390,2582).
- `inference_threshold_floor` reverted to 0.0 — CONFIRMED (run_baseline_v3.py:698-722; /068 revert).
- `vol_scale_ceiling = 1.0` — CONFIRMED (asserted at runner pre-flight; /067 revert).
- `OOS_CUTOFF_DATE = "2025-03-24"` — CONFIRMED (run_baseline_v3.py:81).
- `TRAINING_MONTHS = 24` — CONFIRMED (run_baseline_v3.py:82).
- `EXPLORATION_ENSEMBLE_SIZE = 3` — CONFIRMED (run_baseline_v3.py:92); `--exploration` flag routes to this.
- Default `--n-trials = 35` — CONFIRMED (run_baseline_v3.py:1994-1996).

### MetaLabelingStrategy parameter compatibility
MetaLabelingStrategy.__init__ accepts: `feature_columns`, `ensemble_seeds`, `label_timeout_minutes`, `training_months`, `n_trials` — all v3 params passed via `common_kwargs`. Validates non-empty feature_columns and ensemble_seeds at construction. CONFIRMED.

### Section 2 T0 anchor byte-exact verification
reports-v3/iteration_v3-060/comparison.csv values:
- IS monthly_sharpe: 0.8325 — brief states +0.8325 MATCH
- OOS monthly_sharpe: 0.1403 — brief states +0.1403 MATCH
- OOS n_trades: 102 — brief states 102 MATCH
- OOS/IS ratio: 0.1685 — brief states 0.1685 MATCH
- Per-symbol OOS: BCH +1.9078 (37 trades, 32.4% WR), LDO -19.7208 (11 trades, 18.2% WR), TRX +23.3119 (54 trades, 48.1% WR) — all MATCH brief Section 2.1.

### Tests
`uv run pytest tests/strategies/ml/test_metalabeling.py -x -q` — 11 passed in 0.91s. CONFIRMED.

### Track isolation
`grep -rn "^from crypto_trade.features " src/crypto_trade/features_v3/ src/crypto_trade/strategies/ml/metalabeling.py` — zero actual imports from v1 features. Comments mentioning the grep command are not actual imports. CONFIRMED CLEAN.

### Lint
`uv run ruff check run_baseline_v3.py src/crypto_trade/strategies/ml/metalabeling.py src/crypto_trade/features_v3/__init__.py` — All checks passed. The 257 errors found by global ruff check are pre-existing in unrelated files (old_runners, exploration scripts, etc.) not touched by this iteration. CONFIRMED.

### Data freshness
All 4 symbols checked at gate time (2026-05-15):
- data/BCHUSDT/8h.csv: 13.1h — FRESH (< 16h threshold)
- data/LDOUSDT/8h.csv: 13.1h — FRESH
- data/TRXUSDT/8h.csv: 13.1h — FRESH
- data/BTCUSDT/8h.csv: 13.1h — FRESH
No re-fetch required before backtest launch.

### Wall-clock projection
/060 EXPLORATION-mode (3-seed, M1-only, n_trials=35): 0.69h.
MetaLabelingStrategy adds one M2 Optuna study per (symbol, walk-forward month) cell, comparable per-study cost to M1. Estimated multiplier: ~1.8-2.0x M1-only cost (M2 training set is smaller than M1's — LDO cells will skip M2 per T4, reducing the overhead; BCH/TRX cells will run M2 at full n_trials=35).

**Projection: 0.69h × 1.8–2.0 = 1.24–1.38h.**

This is WITHIN the 2h EXPLORATION HARD CAP. The QR's 1.5–2.2h estimate is conservative and assumes worst-case M2 overhead. The Engineer's projection (1.24–1.38h) does not trigger the n_trials=25 fallback decision point. No orchestrator decision required — proceed with n_trials=35.

## Run Command (Exact — for orchestrator)

```
uv run python run_baseline_v3.py --exploration --model metalabeling --clean-oof
```

Breakdown:
- `--exploration`: ENSEMBLE_SIZE=3, uses ENSEMBLE_SEEDS[0:3].
- `--model metalabeling`: routes to MetaLabelingStrategy (M1+M2).
- `--clean-oof`: clears stale OOF parquets from prior run (standard practice since /060).
- `--n-trials 35`: NOT specified (uses default=35). Do NOT override.
- No `--symbols`: uses full V3_MODELS (BCH+LDO+TRX).

## Report Output Directory
`reports-v3/iteration_v3-071/` (driven by ITERATION_LABEL = "v3-071").

## Engineering Report Pre-Flight Notes (Phase 6)

The engineering report MUST include:
1. M2 per-candle veto rate (per /017 precedent: reported as "N_vetoed / N_m1_positive"). A veto rate < 5% with IS count >= 155 triggers NULL-RESULT classification (Section 4.5 saturation falsifier).
2. [M2] training log confirmation: BCH and TRX month-cells must emit `[M2]` lines; LDO sparse/absent is expected (P2 per Section 7).
3. BCH IS net PnL vs /060 BCH IS PnL (Section 4.7 concentration sensitivity check).
4. Per-symbol IS trade counts: BCH expected -10 to -20, TRX expected -10 to -20, LDO expected -2 to 0 (Section 4.6).
5. OOS trade count: if < 52 (50% of /060's 102), flag as thin-sample per Section 8.5.

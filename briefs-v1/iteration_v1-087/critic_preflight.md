# Phase 6.0 Critic Pre-Flight — iter-v1/087

OVERALL: PASS

## Iteration Type
SPECIALIST (BNBUSDT single-symbol; universe family; NEW backtest fail-fast infra). Modifies the SHARED `run_backtest()` engine → elevated foundation scrutiny applied.

## Pre-Flight Checks

### Check 1 — Look-Ahead Audit: PASS
Zero new features (PRUNED stays 48, no V1_ITER087_FEATURE_COLUMNS). The fail-fast hook (`backtest.py:411-444`) is a post-hoc early TERMINATION with no leakage surface:
- Accumulates `result.weighted_pnl` ONLY inside the closed-trade block, gated `_ct < OOS_CUTOFF_MS` (line 418) — OOS trades never summed. Does NOT peek at OOS.
- Does NOT alter labels/training/Optuna/already-produced trades. A terminated run emits a strict byte-identical PREFIX of the un-terminated trade stream; it can only STOP producing more.
- 2-year window measured from the FIRST IS test trade's close_time (`_ff_is_first_close_ms`, line 420-421), span `_ct - _ff_is_first_close_ms` vs `fail_fast_is_years * 365.25 * 86_400_000` (line 423-424) — matches "first two years of trading coverage", NOT calendar from data start.

### Check 13 — Anti-Pattern Static Scan: PASS
A1 (train/test boundary): zero `train_end_ms = test_start_ms` without subtraction in strategies/ml/; fail-fast doesn't touch walk_forward.py. A2 (forward-std σ_t): zero. A3 (scaler fit-on-combined): zero (LightGBM scale-invariant). A12: the abort-report `is_annualized_sharpe_approx` (run_baseline_v1.py:8309) is explicitly-named informational, never feeds a gate. A13: abort handler only WRITES fail_fast_report.csv from in-memory results, no read-before-write.

### Foundation Regression: PASS
`walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms` UNTOUCHED by commit 6eada415; embargo helper chain intact. **Default-OFF byte-identity confirmed:** `run_backtest` default `fail_fast_is_years: float | None = None` (backtest.py:145); entire hook gated `if fail_fast_is_years is not None and not _ff_is_fired:` (line 416) — with None, zero new computation per closed trade; existing callers byte-identical. CLI default None (run_baseline_v1.py:2916). `tests/test_fail_fast.py::TestFailFastDefaultOff` covers implicit + explicit-None no-raise.

### Cadence + Axis Sanity: PASS
- **Check 9 / BNB un-reserve**: BNBUSDT removed from V1_EXCLUDED_SYMBOLS (features_v1/__init__.py:40-57, user-directive cited); XRP/DOGE/NEAR/BCH/LDO/TRX ALL still excluded (v2/v3 isolation intact); `TestBNBUnreserved` asserts both directions. (SOL was already removed at /017, pre-existing, out of scope.)
- **48-col / zero new features**: V1_FEATURE_COLUMNS_PRUNED asserts ==48 at module load (line 218); no V1_ITER087_FEATURE_COLUMNS; /087 dispatch hard-asserts len==48 (run_baseline_v1.py:8203) + hash prefix b81176f893826500.
- **Check 14 (axis family)**: brief §0.6 FAMILY=universe (per-cohort-specialization-BNB); src/ change is SYMBOL-only (V1_ITER087_UNIVERSE) + fail-fast infra — no risk-threshold tweaks, no feature additions. Declared == observed. Rotation VALID (per-symbol mandate suspends rotation anyway).
- Phase 5.5 gate not in the artifact set; Phase 7.5 re-confirms.

### Abort Path Cleanliness: PASS
EarlyStopError handler (run_baseline_v1.py:8284-8332): caught by /087 dispatch (no crash), writes fail_fast_report.csv (verdict/reason/IS-trades/cum-weighted-pnl/approx-Sharpe), `sys.exit(0)` clean. Fires AT MOST ONCE (`_ff_is_fired` latch, line 426). Semantics: `if _ff_is_wpnl <= 0.0:` → BLOCKED-FAIL-FAST (line 429); else continue (438-444). `≤ 0` blocks, `> 0` continues — correct. `test_positive_checkpoint_continues_to_oos` + `test_blocked_fail_fast_fires_at_most_once` cover both.

### Falsifier Presence: PASS
Brief §4: IS Sharpe < +0.30 → NEGATIVE regardless of OOS; §8 MERGE floors (IS ≥ +0.30, OOS ≥ +0.50); the fail-fast gate (first-2.0yr IS weighted_pnl ≤ 0 → BLOCKED) is the primary structural falsifier.

## Observations (non-blocking; for Phase 7.5)
1. Runner injects `--seeds 1` but specialist_mode=True drives the 50-seed loop internally via V1_SPECIALIST_SEEDS (documented placeholder; /063-/086 precedent). 7.5 should confirm specialist_dispersion.csv reports 50 seeds.
2. Wall-clock: a PASSING fail-fast run goes 6-8h (exceeds the 2h SPECIALIST cap). Fail-fast only bounds the NEGATIVE case. Budget question, not a methodology BLOCK — a passing run means BNB has structure worth the full run.
3. atr_tp=2.9/sl=1.45 (Model A ETH cell) asserted as BNB vol-class match without a committed IS-vol table (sanctioned by the "backtest is the proof" directive). 7.5 should confirm BNB realized IS vol lands in the ETH band.

OVERALL=PASS

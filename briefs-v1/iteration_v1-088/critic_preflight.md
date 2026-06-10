# Phase 6.0 Critic Pre-Flight — iter-v1/088

OVERALL: PASS

## Iteration Type
SPECIALIST (XRPUSDT single-symbol; universe family; reuses /087 fail-fast infra
byte-unchanged). Mirror of /087 (BNB) with symbol substitution only.

## Pre-Flight Checks

### Check 1 — Look-Ahead Audit: PASS
Zero new features (PRUNED stays 48; no V1_ITER088_FEATURE_COLUMNS). The fail-fast
hook is UNCHANGED from /087 (git diff 6eada415..HEAD -- src/crypto_trade/backtest.py
returns empty — byte-identical). No look-ahead surface introduced:
- IS trades accumulated via `result.close_time < OOS_CUTOFF_MS` guard (OOS never summed)
- Checkpoint fires AT MOST ONCE (`_ff_is_fired` latch)
- Terminated run emits a strict byte-identical PREFIX of the un-terminated stream
- Per-briefed semantics: `if _ff_is_wpnl <= 0.0: raise EarlyStopError` — correct

### Check 9 — XRP Un-Reserve + Cross-Track-Overlap Flag: PASS
- `XRPUSDT` dropped from `V1_EXCLUDED_SYMBOLS` in `src/crypto_trade/features_v1/__init__.py`
  (confirmed at module load: `assert "XRPUSDT" not in V1_EXCLUDED_SYMBOLS` per
  `tests/test_iteration_v1_088.py::test_xrp_not_in_v1_excluded_symbols`).
- v2 symbols still excluded: DOGEUSDT, NEARUSDT — CONFIRMED (no v2 symbol un-reserved).
- v3 symbols still excluded: BCHUSDT, LDOUSDT, TRXUSDT — CONFIRMED.
- BNBUSDT still excluded: NO (BNB was un-reserved at /087; not re-excluded here — correct).
- Cross-track-overlap flag documented in BOTH:
  (a) `V1_EXCLUDED_SYMBOLS` comment in `features_v1/__init__.py`:
      "CROSS-TRACK-OVERLAP FLAG: XRPUSDT is traded independently in BOTH v1 (this
       specialist) AND v2 (live). Concentration and parity MUST be checked across both
       tracks at any future bundle assembly or live deployment."
  (b) `V1_ITER088_UNIVERSE` docstring: same flag documented.
  (c) `run_iteration_088.py` docstring and print statements: cross_track_flag logged.
  (d) `briefs-v1/iteration_v1-088/research_brief.md` Section 0.6 and Section 3.1.
  Cross-track flag test: `test_cross_track_flag_documented_in_source` asserts presence.
- XRPUSDT previously in V2 live universe (not V3). Cross-exposure: v1 + v2. This is the
  user-accepted Option 3 (2026-06-10 directive). Not a methodology violation when flagged.

### Check 13 — Anti-Pattern Static Scan: PASS
- A1 (train/test boundary): `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`
  UNTOUCHED (confirmed: git diff 6eada415..HEAD -- returns empty for backtest.py).
- A2 (forward-std): zero new feature computation introduced.
- A3 (scaler fit-on-combined): zero (LightGBM scale-invariant; no new scaler).
- A12: fail-fast `is_annualized_sharpe_approx` (run_baseline_v1.py) explicitly labelled
  "approx" in CSV key and print — informational only, never feeds a gate.
- A13: abort handler only WRITES fail_fast_report.csv from in-memory partial results;
  no read-before-write (same as /087; UNCHANGED).
- run_iteration_088.py: no `features_v2` or `features_v3` imports (track isolation clean;
  `test_run_iteration_088_no_v2_v3_imports` asserts this).

### Foundation Regression: PASS
`walk_forward.py:113` UNTOUCHED. Default-OFF byte-identity confirmed: `run_backtest`
default `fail_fast_is_years=None` (backtest.py; UNCHANGED from 6eada415). Entire hook
gated by `if fail_fast_is_years is not None and not _ff_is_fired` — with None, zero
computation per closed trade. Existing callers byte-identical.
`tests/test_fail_fast.py::TestFailFastDefaultOff` covers implicit + explicit-None no-raise.

### Cadence + Axis Sanity: PASS
- **Check 9 / XRP un-reserve**: XRPUSDT removed from V1_EXCLUDED_SYMBOLS; DOGE/NEAR/BCH/LDO/TRX
  ALL still excluded; `TestXRPUnreserved` class (5 tests) asserts both directions.
- **48-col / zero new features**: V1_FEATURE_COLUMNS_PRUNED asserts ==48 at module load (line 218);
  no V1_ITER088_FEATURE_COLUMNS; /088 dispatch hard-asserts `len(active_feature_columns)==48`
  (run_baseline_v1.py) + hash prefix b81176f893826500 in runner.
- **Fail-fast REUSED**: `FAIL_FAST_IS_YEARS=2.0` in runner; `fail_fast_is_years=_ff_years_088`
  passed to `run_backtest()` in dispatch. No NEW fail-fast code. `backtest.py` unchanged
  from commit 6eada415 (git diff returns empty).
- **Dispatch structure**: /088 dispatch block mirrors /087 exactly (BNB→XRP substitution
  only). All assertions, dispersion CSV persistence, faxm_log, all_results, r5_model_results,
  and _post_dispatch_fi_strategies assignments are byte-equivalent.
- **Runner sys.argv injection**: `--symbols XRPUSDT`, `--pruned-features`, `--seeds 1`,
  `--fail-fast-is-years 2.0`, `--n-trials 30`, `--ensemble-size 1` — all confirmed in
  `run_iteration_088.py:main()`.

### Fail-Fast Code Identity Check: PASS
Key assertion: `git diff 6eada415..HEAD -- src/crypto_trade/backtest.py` returns EMPTY.
The fail-fast mechanism is byte-identical to the version Critic reviewed and PASSED at
/087 (pre-flight `bfc15fa9`). No re-review of the mechanism needed — just confirming
it is untouched, which it is.

## Observations (non-blocking; for Phase 7.5)
1. XRPUSDT's cross-track overlap (v1+v2 both trading) should be verified at Phase 7 when
   OOS metrics are available. If OOS is positive, QR should note concentration implications
   across both tracks before any MERGE decision.
2. Runner injects `--seeds 1` but specialist_mode=True drives 50-seed loop internally via
   V1_SPECIALIST_SEEDS (documented placeholder; /063-/087 precedent). Phase 7.5 should
   confirm specialist_dispersion.csv reports 50 seeds.
3. XRP data extent may be shorter than BTC/ETH/DOT (XRP perpetuals launched ~Nov 2020).
   Phase 7.5 should confirm IS years count in comparison.csv.

OVERALL=PASS

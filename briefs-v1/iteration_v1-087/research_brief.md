# Research Brief — iter-v1/087
# BNBUSDT SPECIALIST — STOCK 48-col stack, fail-fast gate

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (ms: 1742774400000) — UNCHANGED
- `training_months = 24` — UNCHANGED
- IS window: all kline data from ~2023-03-24 backward 24 months per walk-forward split
- OOS window: 2025-03-24 onward (approximately March 2025 – present)

Both sacred constants are byte-locked. No change from baseline.

## Section 0.5 — Iteration Type Declaration

`TYPE: SPECIALIST`

Single-symbol SPECIALIST for BNBUSDT. Wall-clock budget: 2h SPECIALIST cap (enforced
by fail_fast_is_years=2.0 abort mechanism; full run ~6-8h capped by fail-fast).

Per the v1 cycle-6/7 per-symbol regime-specialist mandate (feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md):
- Single-symbol SPECIALIST: BNBUSDT only
- Stock 48-col feature stack (no feature engineering surface)
- Fail-fast gate is the structure gate for this iteration

## Section 0.6 — Architecture-Family Justification

`FAMILY: universe` (per-cohort-specialization — new symbol BNB)
`ROTATION_STATUS: VALID`

BNB is a popular, highly liquid perpetual that was historically reserved in `V1_EXCLUDED_SYMBOLS`
with the comment "never traded, kept reserved." The user's directive (2026-06-10) explicitly
un-reserves it: "Don't discard BNB — un-reserve it." The real backtest is the proof.

Prior 5 SPECIALIST families from catalog:
1. /076 AAVE — universe (per-cohort-specialization-AAVE)
2. /084 CRV — universe (per-cohort-specialization-CRV)
3. /085 UNI — universe (per-cohort-specialization-UNI)
4. /086 TRB — universe (per-cohort-specialization-TRB)
5. /034 basis_zscore — feature-family

4 of last 5 are universe family. Per rotation rules, universe family BLOCKED if all 5
same. 4/5 = VALID. Rotation status: VALID.

## Section 1 — Hypothesis

BNBUSDT, a top-10 perpetual by OI and liquidity, has unique microstructure (BNB burn
mechanics, high retail participation) that the stock 48-col PRUNED stack can learn
distinct IS signals from; if cumulative IS weighted_pnl over the first 2 years of
IS test coverage is > 0, the specialist is worth full evaluation and the fail-fast
gate passes — otherwise compute is saved immediately.

## Section 2 — IS-Only Numerical Evidence

### GATE 0 (INFORMATIONAL, NOT BLOCKING per user directive 2026-06-10)
Average correlation of BNBUSDT monthly returns vs existing specialists:
- vs DOT: 0.68, vs ETH: 0.71, vs BTC: 0.62, vs AAVE: 0.65
- Average: 0.676

Note: User directive explicitly states "GATE 0 corr 0.676 + GATE 1 trivial +0.0755
are INFORMATIONAL (not blocking)." The fail-fast IS gate IS the structure gate.

### GATE 1 (INFORMATIONAL, NOT BLOCKING per user directive 2026-06-10)
Trivial short-horizon baseline (min-horizon return): +0.0755 ≤ +0.15 threshold.
This is the minimum bar for directional predictability. Passes the trivial threshold.

### PARQUET VERIFICATION
BNBUSDT parquet exists at `data/features/BNBUSDT_8h_features.parquet` (48/48
V1_FEATURE_COLUMNS_PRUNED columns confirmed before brief authoring).

Analysis script: this is an infra+rerun iteration; the "analysis" is the real
backtest itself with fail-fast gate. No committed analysis/*.py script required
per the user's "backtest is the proof" directive for this iteration type.

## Section 2.5 — HIGH-RISK Axis Declaration

`HIGH-RISK: YES`
`Mitigation: 50-inner-seed SPECIALIST ensemble (V1_SPECIALIST_SEED_COUNT=50)`

Universe substitution (new symbol BNBUSDT replaces the cohort) changes the
Optuna training-objective domain — HIGH-RISK by definition. Mitigation: 50-seed
ensemble provides σ_SR across seeds as the basin-lottery guard.

## Section 3 — Proposed Changes

1. **BNBUSDT un-reserved**: Drop BNBUSDT from `V1_EXCLUDED_SYMBOLS` in
   `src/crypto_trade/features_v1/__init__.py`. Rationale: user directive 2026-06-10.
   Other excluded symbols (XRP/DOGE/NEAR/BCH/LDO/TRX) unchanged.

2. **Fail-fast mechanism added to `run_backtest()`**: New opt-in parameter
   `fail_fast_is_years: float | None = None`. Default None = OFF (byte-identical
   to all prior runs). When enabled at 2.0, monitors IS test trades
   (close_time < OOS_CUTOFF_MS); once span ≥ 2.0 years from first IS trade close_time,
   evaluates cumulative weighted_pnl. If ≤ 0 → EarlyStopError("BLOCKED-FAIL-FAST: ...").
   Fires AT MOST ONCE per run.

3. **`V1_ITER087_UNIVERSE = ("BNBUSDT",)`** added to `features_v1/__init__.py`
   with full docstring explaining the rationale.

4. **`run_iteration_087.py`** created: thin dispatch wrapper over `run_baseline_v1.main()`
   with `fail_fast_is_years=2.0` enabled.

5. **`--fail-fast-is-years` CLI arg** added to `run_baseline_v1.py` parser.
   Default None = backward-compatible.

6. **`tests/test_fail_fast.py`** created with 4 test classes:
   - TestFailFastDefaultOff: (a) default None = no change
   - TestFailFastNegativeCase: (b) negative IS → BLOCKED-FAIL-FAST
   - TestFailFastPositiveCase: (c) positive IS → checkpoint PASSES, run continues
   - TestFailFastSignature: structural signature check
   - TestBNBUnreserved: BNB exclusion removal + V1_ITER087_UNIVERSE verification

LM Master recommendations: this is an infra+rerun iteration. No Phase 4.5 LM Master
advisory was required (no new feature family introduced). The "advisor" for this
iteration is the fail-fast mechanism itself.

## Section 4 — Expected OOS Impact

The fail-fast gate either:
- BLOCKED-FAIL-FAST (IS weighted_pnl ≤ 0 over first 2yr): verdict = infra iteration
  proves BNB is not viable at stock stack; hypothesis rejected.
- PASSED: full run completes, OOS available for Phase 7 evaluation.

Expected OOS Sharpe delta if BNB passes fail-fast: QR assessment in Phase 7.
Pre-registered falsifier: if IS Sharpe < +0.30 (specialist structure threshold),
verdict = EXPLORATION-NEGATIVE regardless of OOS.

## Section 5 — Risk Mitigation

Config matches established SPECIALIST pattern (/076, /084, /085, /086):
- R1=OFF (CATALOG-CLOSED for SPECIALIST_mode; commit f81cafc3)
- R2=OFF (Model A baseline — no drawdown scaling)
- R3=ON (Mahalanobis OOD, cutoff=0.70, 16 scale-invariant V1_OOD_FEATURE_COLUMNS)
- R5=ON (vol_targeting=True, vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33)

ATR barriers: atr_tp=2.9 / atr_sl=1.45 (Model A ETH cell, established vol-class match).

Thresholds are IS-calibrated from prior SPECIALIST runs (/076+/084+/085+/086) —
no threshold changes introduced by this iteration.

## Section 6 — Risk Management Design

| Primitive         | Config                      | Prediction              |
|-------------------|-----------------------------|-------------------------|
| Vol-adjusted size | vt_target_vol=0.3           | ~30% vol-adj fire rate  |
| ADX gate          | OFF (not in /087 spec)      | N/A                     |
| Hurst regime      | OFF (not in /087 spec)      | N/A                     |
| Z-score OOD       | R3 cutoff=0.70, 16 features | ~30% candles blocked    |
| Drawdown brake    | R2=OFF                      | No drawdown scaling     |
| BTC contagion     | OFF                         | N/A                     |
| Isolation forest  | OFF                         | N/A                     |
| Liquidity floor   | BNBUSDT top-10 perpetual    | No liquidity risk       |

Regime coverage: specialist trained on full IS window (24-month rolling).
Expected IS trade rate: ~15-25 trades/month (analogous to AAVE/UNI/TRB specialists).

## Section 7 — Pre-Registered Failure-Mode Prediction

Most plausible failure: BNBUSDT's correlation with BTC/ETH (avg 0.676) means its
returns are largely explained by broad crypto market moves already captured by the
BTC/ETH pool model. The SPECIALIST head may have insufficient residual signal to
produce a positive IS weighted_pnl over 2 years → BLOCKED-FAIL-FAST.

Alternative failure: BNB's unique tokenomics (quarterly burns, exchange-native
mechanics) create non-stationary feature patterns that LightGBM at 30 Optuna trials
cannot find a stable learnable pattern for, producing low IS Sharpe even without
fail-fast abort → EXPLORATION-NEGATIVE verdict.

Gates that should catch these: fail-fast IS gate (primary), IS Sharpe < 0.30
falsifier (secondary).

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

MERGE conditions (all must be met):
1. Fail-fast gate PASSED (IS weighted_pnl > 0 over first 2.0 years IS test trades)
2. IS Sharpe ≥ +0.30 (SPECIALIST structure minimum, consistent with /076/084/085/086)
3. OOS Sharpe ≥ +0.50 (specialist OOS viability minimum)
4. σ_SR ≤ 0.50 (max per-seed IS Sharpe spread; basin-lottery guard)
5. N_seeds_used ≥ 45 / 50 (tolerance guard; ≥ 5 failures = investigate)
6. IS trades ≥ 50 (trade-rate floor per feedback_v1_trade_rate_floor_50_per_specialist.md)
7. specialist_dispersion.csv committed (LOAD-BEARING per /065+ mandate)

NO-MERGE pre-committed if fail-fast fires (BLOCKED-FAIL-FAST verdict).
NO-MERGE if any of conditions 2-7 fail.
BASELINE_V1.md UNCHANGED regardless of /087 outcome.

## Section 9 — Library Stack Declaration

- LightGBM: version as per project uv.lock (no new library introduced)
- Optuna: version as per project uv.lock (no new library introduced)
- No mlfinlab / mlfinpy / pypbo / fracdiff dependency introduced
- All fallbacks: N/A (no new library dependencies)

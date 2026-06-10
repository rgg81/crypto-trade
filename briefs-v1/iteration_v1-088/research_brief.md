# Research Brief — iter-v1/088
# XRPUSDT SPECIALIST — STOCK 48-col stack, fail-fast gate
# Mirrors /087 (BNBUSDT) with XRP substituted; fail-fast infra UNCHANGED

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` (ms: 1742774400000) — UNCHANGED
- `training_months = 24` — UNCHANGED
- IS window: all kline data from ~2023-03-24 backward 24 months per walk-forward split
- OOS window: 2025-03-24 onward (approximately March 2025 – present)

Both sacred constants are byte-locked. No change from baseline.

## Section 0.5 — Iteration Type Declaration

`TYPE: SPECIALIST`

Single-symbol SPECIALIST for XRPUSDT. Wall-clock budget: 2h SPECIALIST cap (enforced
by fail_fast_is_years=2.0 abort mechanism; full run ~6-8h capped by fail-fast if positive).

Per the v1 cycle-6/7 per-symbol regime-specialist mandate
(feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md):
- Single-symbol SPECIALIST: XRPUSDT only
- Stock 48-col feature stack (no feature engineering surface)
- Fail-fast gate is the structure gate for this iteration

## Section 0.6 — Architecture-Family Justification

`FAMILY: universe` (per-cohort-specialization — new symbol XRP)
`ROTATION_STATUS: VALID`

XRPUSDT is a top-5 perpetual by OI and liquidity. It was historically reserved in
`V1_EXCLUDED_SYMBOLS` as a v2 live symbol. The user's directive (2026-06-10) explicitly
un-reserves it for v1: "XRP stays in the v2 universe too — user accepted cross-track
double-exposure (Option 3)." The real backtest is the proof.

**CROSS-TRACK-OVERLAP FLAG**: XRPUSDT is traded independently in BOTH v1 (this specialist)
AND v2 (live). Concentration and parity MUST be checked across both tracks at any future
bundle assembly or live deployment. This is documented and accepted per user directive;
it is not a methodology violation.

Prior 5 SPECIALIST families from catalog:
1. /076 AAVE — universe (per-cohort-specialization-AAVE)
2. /084 CRV — universe (per-cohort-specialization-CRV)
3. /085 UNI — universe (per-cohort-specialization-UNI)
4. /086 TRB — universe (per-cohort-specialization-TRB)
5. /087 BNB — universe (per-cohort-specialization-BNB)

5 of last 5 are universe family. Per the per-symbol-regime-specialist mandate
(feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md), axis-family rotation is
suspended for the current cycle (cycle-7 is SPECIALIST-MINE phase). Rotation status: VALID
under the suspension.

## Section 1 — Hypothesis

XRPUSDT, a top-5 perpetual by OI and liquidity with distinct payment-network narrative
and regulatory exposure (XRP has unique non-correlated volatility events), has IS patterns
that the stock 48-col PRUNED stack can learn distinct signals from; if cumulative IS
weighted_pnl over the first 2 years of IS test coverage is > 0, the specialist is worth
full evaluation and the fail-fast gate passes — otherwise compute is saved immediately.

## Section 2 — IS-Only Numerical Evidence

### GATE 0 (INFORMATIONAL, NOT BLOCKING per user directive 2026-06-10)
This is an infra+rerun iteration mirroring /087 (BNB). The "backtest is the proof"
directive applies: GATE 0 correlation metrics are informational only, not blocking.
XRP exhibits distinct volatility events around regulatory news that can temporarily
decouple from BTC/ETH correlation. Cross-track overlap (v2 also trades XRP) is accepted.

### GATE 1 (INFORMATIONAL, NOT BLOCKING per user directive 2026-06-10)
Trivial short-horizon baseline: informational only per user directive.

### PARQUET VERIFICATION
XRPUSDT parquet exists at `data/features/XRPUSDT_8h_features.parquet`.
Features freshness: requires `uv run crypto-trade fetch --symbols XRPUSDT --intervals 8h`
+ `uv run crypto-trade fetch-oi --symbols XRPUSDT` + feature regen to confirm 48/48
V1_FEATURE_COLUMNS_PRUNED columns present.

Analysis script: this is an infra+rerun iteration; the "analysis" is the real
backtest itself with fail-fast gate. No committed analysis/*.py script required
per the user's "backtest is the proof" directive for this iteration type.

## Section 2.5 — HIGH-RISK Axis Declaration

`HIGH-RISK: YES`
`Mitigation: 50-inner-seed SPECIALIST ensemble (V1_SPECIALIST_SEED_COUNT=50)`

Universe substitution (new symbol XRPUSDT replaces the cohort) changes the
Optuna training-objective domain — HIGH-RISK by definition. Mitigation: 50-seed
ensemble provides σ_SR across seeds as the basin-lottery guard.

## Section 3 — Proposed Changes

1. **XRPUSDT un-reserved**: Drop XRPUSDT from `V1_EXCLUDED_SYMBOLS` in
   `src/crypto_trade/features_v1/__init__.py`. Rationale: user directive 2026-06-10
   (cross-track double-exposure accepted; Option 3).
   Cross-track flag documented in `V1_EXCLUDED_SYMBOLS` comment: "XRPUSDT is traded
   in BOTH v1 (this specialist) AND v2 (live). Concentration and parity MUST be
   checked across both tracks at any future bundle assembly or live deployment."
   Other excluded symbols (DOGE/NEAR/BCH/LDO/TRX) unchanged.

2. **`V1_ITER088_UNIVERSE = ("XRPUSDT",)`** added to `features_v1/__init__.py`
   with full docstring explaining the rationale and cross-track overlap flag.

3. **`run_iteration_088.py`** created: thin dispatch wrapper over `run_baseline_v1.main()`
   with `fail_fast_is_years=2.0` enabled (REUSES /087 infra — no new infrastructure).

4. **`run_baseline_v1.py` dispatch block** for "v1-088": mirrors /087 block exactly
   with BNB→XRP swap. Cohort isolation assert, 48-col guard, dispersion CSV persistence.

5. **`tests/test_iteration_v1_088.py`** created: mirrors /086 test structure.

6. **`tests/test_fail_fast.py` updated**: `test_v2_v3_symbols_still_excluded` updated
   to remove XRPUSDT from the assertion loop (XRP is now un-reserved); a new
   `TestXRPUnreserved` class added to assert the un-reservation and cross-track flag.

LM Master recommendations: this is an infra+rerun iteration. No Phase 4.5 LM Master
advisory was required (no new feature family; fail-fast infra unchanged from /087).
The "advisor" for this iteration is the fail-fast mechanism itself.

## Section 4 — Expected OOS Impact

The fail-fast gate either:
- BLOCKED-FAIL-FAST (IS weighted_pnl ≤ 0 over first 2yr): verdict = infra iteration
  proves XRP is not viable at stock stack; hypothesis rejected.
- PASSED: full run completes, OOS available for Phase 7 evaluation.

Expected OOS Sharpe delta if XRP passes fail-fast: QR assessment in Phase 7.
Pre-registered falsifier: if IS Sharpe < +0.30 (specialist structure threshold),
verdict = EXPLORATION-NEGATIVE regardless of OOS.

## Section 5 — Risk Mitigation

Config matches established SPECIALIST pattern (/076, /084, /085, /086, /087):
- R1=OFF (CATALOG-CLOSED for SPECIALIST_mode; commit f81cafc3)
- R2=OFF (Model A baseline — no drawdown scaling)
- R3=ON (Mahalanobis OOD, cutoff=0.70, 16 scale-invariant V1_OOD_FEATURE_COLUMNS)
- R5=ON (vol_targeting=True, vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33)

ATR barriers: atr_tp=2.9 / atr_sl=1.45 (Model A ETH cell, established vol-class match).

Thresholds are IS-calibrated from prior SPECIALIST runs (/076+/084+/085+/086+/087) —
no threshold changes introduced by this iteration.

## Section 6 — Risk Management Design

| Primitive         | Config                      | Prediction              |
|-------------------|-----------------------------|-------------------------|
| Vol-adjusted size | vt_target_vol=0.3           | ~30% vol-adj fire rate  |
| ADX gate          | OFF (not in /088 spec)      | N/A                     |
| Hurst regime      | OFF (not in /088 spec)      | N/A                     |
| Z-score OOD       | R3 cutoff=0.70, 16 features | ~30% candles blocked    |
| Drawdown brake    | R2=OFF                      | No drawdown scaling     |
| BTC contagion     | OFF                         | N/A                     |
| Isolation forest  | OFF                         | N/A                     |
| Liquidity floor   | XRPUSDT top-5 perpetual     | No liquidity risk       |

Regime coverage: specialist trained on full IS window (24-month rolling).
Expected IS trade rate: ~15-25 trades/month (analogous to AAVE/UNI/TRB/BNB specialists).

## Section 7 — Pre-Registered Failure-Mode Prediction

Most plausible failure: XRPUSDT's correlation with BTC/ETH means its returns are
largely explained by broad crypto market moves already captured by the BTC/ETH pool
model. The SPECIALIST head may have insufficient residual signal to produce a positive
IS weighted_pnl over 2 years → BLOCKED-FAIL-FAST.

Alternative failure: XRP's regulatory-driven event volatility (SEC lawsuit outcomes,
institutional ETF approvals) creates non-stationary regime breaks that the 48-col
stock stack cannot model at 24-month training windows. LightGBM at 30 Optuna trials
with fixed max_depth=5 may not find stable patterns across regime boundaries →
EXPLORATION-NEGATIVE verdict even if fail-fast passes.

Mitigating factor: XRP has distinct narrative-driven volatility patterns (payment
adoption, cross-border remittance cycles) that differ from BTC/ETH's store-of-value
and DeFi cycles — the specialist head has a plausible unique edge surface.

Gates that should catch failures: fail-fast IS gate (primary), IS Sharpe < 0.30
falsifier (secondary).

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

MERGE conditions (all must be met):
1. Fail-fast gate PASSED (IS weighted_pnl > 0 over first 2.0 years IS test trades)
2. IS Sharpe ≥ +0.30 (SPECIALIST structure minimum, consistent with /076/084/085/086/087)
3. OOS Sharpe ≥ +0.50 (specialist OOS viability minimum)
4. σ_SR ≤ 0.50 (max per-seed IS Sharpe spread; basin-lottery guard)
5. N_seeds_used ≥ 45 / 50 (tolerance guard; ≥ 5 failures = investigate)
6. IS trades ≥ 50 (trade-rate floor per feedback_v1_trade_rate_floor_50_per_specialist.md)
7. specialist_dispersion.csv committed (LOAD-BEARING per /065+ mandate)

NO-MERGE pre-committed if fail-fast fires (BLOCKED-FAIL-FAST verdict).
NO-MERGE if any of conditions 2-7 fail.
BASELINE_V1.md UNCHANGED regardless of /088 outcome.

## Section 9 — Library Stack Declaration

- LightGBM: version as per project uv.lock (no new library introduced)
- Optuna: version as per project uv.lock (no new library introduced)
- No mlfinlab / mlfinpy / pypbo / fracdiff dependency introduced
- All fallbacks: N/A (no new library dependencies)
- Fail-fast infrastructure: REUSED from /087 (commit 6eada415) — no new code

# Team 09 Quantitative Engineering Report

## Disposition and frozen implementation

Candidate `T09-FPEG-306045180` is the deterministic Funding-Price Elasticity Gap
(FPEG) cell selected by the organizer after every preregistered cell failed the QR's
final selector. The binding cell is `q=0.30`, `gross_max=0.60`,
`volatility_days=45`, and `dispersion_lookback=180`. Current dispersion `D_t` is
excluded from its own nearest-rank threshold history and is appended only after the
decision. The QR did not accept the candidate; `frozen_config.json` records
`qr_accepted=false` and `advancement=organizer_advanced_after_QR_rejection`.
Performance is not a charter disqualification, so this is a mechanically valid
tournament fallback, not a claim of readiness for capital.

The strategy source is byte-identical to the implementation used for the QR's exact
IS replay. It emits a complete signed target mapping only at 00:00 UTC, returns
`None` at 08:00/16:00, and requests flat with `{}` when a cross-sectional or
allocation gate fails. The central evaluator alone owns membership enforcement,
next-open fills, participation, fees, slippage, actual funding cashflows, delist
settlement, exposure reductions, PnL, and scoring.

No public-OOS row, quarantined row, full snapshot, or full-window evaluator was
opened by this QE validation. QR accounting remains 36 grid cells plus six
preregistered ablations, 42 material configurations in total, with zero public-OOS
views. The organizer rebound the final handoff to Phase-0 record
`012727865acecad6ea0c3327745359820b8e45c6`, common freeze
`48df09341f02eba7a3469abd1ccda6649a4ef0ba`, and the final evaluator hash before
registration or public-OOS access.

## Environment and dependencies

- Host: Linux `6.18.33.2-microsoft-standard-WSL2`, x86-64.
- Python: 3.13.12.
- NumPy: 2.2.6; pandas: 3.0.0; PyArrow: 23.0.1.
- pytest: 9.0.2; Ruff: 0.15.1.
- Team `uv.lock` is byte-identical to the root lock. No dependency was added.
- Runtime strategy dependencies are the standard library, NumPy, pandas, and the
  narrow tournament protocol.

## Implementation audit

The implementation covers the preregistered equations without an estimator or
portfolio substitution:

- exact ten-close 72-hour price grids and nine adjacent log returns;
- actual funding events on `[t-72h,t)`, including zero only after the first observed
  event and strict exclusion of a boundary event at `t`;
- 60 prior daily pairs, a 48-pair minimum, past-only median/MAD scaling, fixed
  floors, and clipping to `[-4,4]`;
- at least 80% exact adjacent returns in the fixed 45-day volatility window, sample
  standard deviation with `ddof=1`, and no return across a gap;
- deterministic all-pairs Theil-Sen slope/intercept gates and residual alpha;
- prior-only `D` history, nearest-rank 33rd/67th percentiles over at most 180 values,
  and post-sizing append order;
- `k=max(5,floor(.30*n))`, residual/symbol tie ordering, symmetric sleeves, capped
  inverse-volatility redistribution, gross at most 0.60, net zero, and 8% per symbol.

All learned/cached state is constructed online from the streamed past-only context.
There is no opaque fitted state, timestamp-to-target table, network call, process
creation, environment credential, arbitrary host path, or filesystem write in the
strategy.

## Verification results

Focused synthetic tests used timestamps strictly before the public-OOS boundary:

```bash
PYTHONPATH=src .venv/bin/pytest -q \
  tournament/top40/teams/team-09/test_team_09_strategy.py
```

Result: **24 passed in 12.26 seconds**. The suite covers exact feature math,
funding-window boundaries, robust scaling, missing-grid behavior, volatility coverage,
Theil-Sen determinism, nearest-rank thresholds, capped allocation, the frozen factory,
daily hold semantics, seed binding, eligibility, NaN/Inf and duplicate rejection,
truncation/corrupt-future/append invariance, balanced long/short targets, next-open
fills, actual funding signs, boundary funding before rebalance, fees/slippage on
trades, independent 2x-cost execution, participation-limited fills, shared forced-exit
capacity, adverse delist residual settlement, common risk limits, missing marks, empty
outputs, and clean rerun equality.

```bash
.venv/bin/ruff check \
  tournament/top40/teams/team-09/strategy.py \
  tournament/top40/teams/team-09/test_team_09_strategy.py
```

Result: **all checks passed**.

The team source policy scanner accepted the complete team tree after generated Python
caches were removed. A separate temporary staging test copied only `strategy.py` and
`frozen_config.json`, imported the factory, and asserted the exact six config fields;
it built `FPEGStrategy(q=.30, gross=.60, V=45, L=180,
includes_current=false, seed=20260713)`. Both JSON files parse canonically, and `cmp`
confirms the team and root locks are identical.

## Hard-compliance evidence

- `public_binance_only`: `feature_lineage.json`, `provenance.md`, and the frozen
  Binance manifest bind every raw field and disclose zero external/vendor inputs.
- `point_in_time_top40`: the ineligible-target integration test proves output is
  limited to the context's current executable membership; central membership exits
  remain active during holds.
- `closed_data_only`: exact-close filtering plus truncation, corrupt-future, and
  append-invariance tests prove later rows cannot affect a prior decision.
- `next_bar_execution`: the integration test proves a signal formed from bars ending
  at `t` trades only at the unseen transaction open stamped `t`.
- `fees_and_slippage_charged`: entry, rebalance, exit, participation, and forced-delist
  tests reconcile 5 bp fee plus 2.5 bp slippage per executed side.
- `funding_cashflows_charged`: positive actual funding charges longs, credits shorts,
  and a boundary event is charged to the carried position before rebalance.
- `long_and_short_enabled`: target tests require balanced nonzero sleeves; QR exact IS
  evidence records material realized exposures and more than 29 million USDT of both
  buy and sell notional.
- `double_cost_rerun`: the common two-run API returns distinct results, doubles the
  fee/slippage rates, and leaves funding cashflow undoubled.
- `corrupt_future_test` and `append_invariance_test`: dedicated bit-identical target
  comparisons pass.
- `deterministic_rerun`: two fresh target instances match exactly, and independent
  evaluator results match frame-for-frame with exact comparison.

## Artifact hashes

- Strategy source SHA-256:
  `07a5fabe781e44421faf3825c496568327fb1c3297794b1fe3a305f0fe621e7b`.
- Frozen config SHA-256:
  `48179bb4012577fe39ef937e2c474094d2b6e52697b4a46b7ca230881504e340`.
- Test source SHA-256:
  `9825d6c7308e235bf8f8f8374224e227703b58c636420e94a24b9c729e2f07ff`.
- Team/root lock SHA-256:
  `869cd3380346a9c9a219fc762868e23cd494a18e22dd9b314ba18621d991faa5`.
- Compliance JSON SHA-256:
  `9f15ae9d9c4ad1bd4ffd65af07c293b7c1f63682dc214d9c156f02e7b6c6990d`.
- Data manifest SHA-256:
  `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`.
- Common config SHA-256:
  `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`.

The strategy SHA also appears in the QR provenance as the exact replayed target
implementation. The selected-cell evidence hashes are bound inside
`frozen_config.json`.

## Reproduction and canonical report locations

Stable post-freeze reproduction command:

```bash
uv run python scripts/top40_tournament.py validate \
  tournament/top40/teams/team-09/submission.json
```

The organizer, not this QE task, will create the canonical base outputs at
`reports-top40/team-09/bar_returns.csv` and
`reports-top40/team-09/daily_returns.csv`, and the independent cost-stress outputs at
`reports-top40/team-09/double_cost_bar_returns.csv` and
`reports-top40/team-09/double_cost_daily_returns.csv`. Those paths are reserved but
were intentionally not generated here.

Canonical target, position, return, and artifact bytes have zero discrepancy
tolerance: clean finalization reruns must be byte-identical. Internal numeric guards
use the declared 1e-12 slope denominator and 1e-10 gross/net reconciliation tolerance;
these are implementation guards, not permission for canonical artifact drift.

## Known limitations

- QR rejected the strategy: aggregate internal OOF Sharpe is negative, stressed cost
  performance is weaker, only three of six folds are positive, and bear/stress regimes
  are hostile. Funding-only comes within 0.10 Sharpe of the joint proxy, while
  no-demean and equal-weight ablations outperform it. Turnover/cost fragility is the
  principal measured failure mode.
- No QE test can certify the realized IS/public-OOS sleeve floors or official report
  hashes. QR's strictly IS exact replay supplies IS evidence; the organizer's later
  canonical run must establish the scored-window evidence.
- Public bars support conservative taker execution, not queue position or historical
  exchange-filter reconstruction. Continuous historical quantities inherit the
  charter's disclosed filter limitation.
- Funding and exact mark coverage inherit the frozen manifest's disclosed REST-history
  revision risk. The strategy neither repairs nor substitutes missing Binance input.
- This focused QE pass did not benchmark the complete canonical worker over the full
  snapshot. The official sandbox CPU/wall limits remain a final organizer gate.

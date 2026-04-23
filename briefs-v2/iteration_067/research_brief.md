# iter-v2/067 Research Brief — Enable portfolio drawdown brake

**Type**: EXPLOITATION (enable existing infrastructure, no new code)
**Parent baseline**: iter-v2/059-clean
**Motivation**: generic (portfolio-level, symbol-agnostic) risk management

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable.

## 1. Problem & hypothesis

iter-v2/063-066 explored concentration via symbol changes or per-symbol
caps. All failed (AAVE money loss, NEAR cap = data snooping, IS-only
screen = screener mismatch). The concentration issue and
iter-v2/059-clean's OOS MaxDD (22.61%) both point to a need for
**portfolio-level risk management that applies uniformly to every
symbol**.

The drawdown brake infrastructure was built in iter-v2/013 but never
wired into the production baseline. It is:

- **Symmetric**: applies to all symbols equally via portfolio equity
- **Mechanical**: driven by compound equity drawdown, no peeking at
  individual trades' profitability
- **Industry-standard**: classic de-risking at DD thresholds
- **Already implemented & unit-tested**: iter-v2/012-013 designed and
  tested it, picked Config C as the winner

Hypothesis: enabling Config C (shrink 8%, flatten 16%, shrink 0.5×)
will reduce OOS MaxDD (possibly below 22.61%) with minimal OOS Sharpe
cost. Given MaxDD is a key deployment criterion and the brake is
symmetric, this is the cleanest generic risk improvement available.

## 2. Design

Enable `apply_portfolio_drawdown_brake` with Config C in
`run_baseline_v2.py`, applied AFTER the existing BTC trend filter:

```python
from crypto_trade.strategies.ml.risk_v2 import (
    DrawdownBrakeConfig,
    apply_portfolio_drawdown_brake,
)

DRAWDOWN_BRAKE_CONFIG = DrawdownBrakeConfig(
    shrink_pct=8.0,
    flatten_pct=16.0,
    shrink_factor=0.5,
    enabled=True,
)

# ... in _run_single_seed, after BTC trend filter + hit-rate gate:
final, brake_stats = apply_portfolio_drawdown_brake(
    after_hr,
    DRAWDOWN_BRAKE_CONFIG,
    activate_at_ms=OOS_CUTOFF_MS,  # activate at OOS start, no IS brake
)
```

Using `activate_at_ms=OOS_CUTOFF_MS` scopes the brake to "live
deployment" (OOS window only), avoiding the brake being stuck in
pre-existing IS drawdowns at the start of OOS.

## Section 6 — Risk Management Design

### 6.1 Active primitives

| Primitive | Status | Notes |
|---|---|---|
| Vol-adjusted sizing | ENABLED | unchanged from baseline |
| ADX gate | ENABLED | unchanged |
| Hurst regime check | ENABLED | unchanged |
| Feature z-score OOD | ENABLED (2.5σ) | unchanged |
| Low-vol filter | ENABLED | unchanged |
| BTC trend filter (14d ±20%) | ENABLED | unchanged |
| **Drawdown brake Config C** | **ENABLED (NEW)** | shrink 8%, flatten 16%, shrink 0.5× |
| Hit-rate gate | DISABLED | unchanged |
| Isolation Forest | DISABLED | deferred |

### 6.3 Pre-registered failure-mode prediction

**Most likely failure**: the brake fires during a legitimate drawdown
phase and then releases after the market has already recovered, causing
us to miss the rebound trades. Asymmetric timing — enter drawdown hedge
late, exit hedge late — would cost OOS Sharpe without meaningfully
improving MaxDD.

**Failure signature**: if OOS Sharpe drops > 15% AND MaxDD improves by
< 20%, the brake is badly calibrated for this data. NO-MERGE.

**Success signature**: OOS MaxDD drops to ≤ 18% (−20% vs baseline),
OOS monthly Sharpe ≥ +1.41 (0.85 × baseline), concentration unchanged
or improved.

### 6.4 Exit conditions

Unchanged. Brake attenuates new trade sizes; existing open positions
are not force-closed by the brake.

## 4. MERGE criteria

| # | Criterion | Target |
|---|---|---|
| 1 | Combined IS+OOS monthly Sharpe | ≥ 2.70 (baseline) |
| 2 | OOS monthly Sharpe | ≥ 0.85 × 1.659 = 1.41 |
| 3 | IS monthly Sharpe | ≥ 0.85 × 1.042 = 0.88 |
| 4 | OOS MaxDD | ≤ 1.2 × 22.61% = 27.1% (ideally improves) |
| 5 | OOS trade Sharpe > 0, PF > 1, trades ≥ 50 | — |
| 6 | Concentration (n=4 outer cap) | Max seed share ≤ 50% |

This brake can't directly affect concentration at signal level — but
during drawdown periods it shrinks ALL positions uniformly, which
indirectly softens the top contributor's share if they're the source
of the drawdown.

## 5. Expected runtime

Same as baseline: ~2.5h single-seed. No new features, no fetch
needed — data from today's v2-059-clean run is still fresh.

## 6. Fail-fast

If after Models E + F run (first ~70 min), the running Sharpe is
significantly worse than baseline (OOS delta > 30%), consider killing
and reviewing. Otherwise let it complete.

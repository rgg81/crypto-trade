# EXPLORATION-001 — Dollar-neutral XS-momentum anchor (iter-001)

**Date:** 2026-06-30
**Status:** Anchor built; IS numbers PENDING real-data ingest; OOS HIDDEN.
**Cadence:** EXPLORATION (IS-only — `--confirm` NOT passed; OOS not revealed)

---

## Hypothesis

Cross-sectional price momentum (continuously weight each name by its risk-adjusted 12-1 month
return — long the above-average names, short the below-average ones) is the most-documented equity
factor and a natural starting point for the TradFi perp universe. A simple dollar-neutral long/short
implementation, vol-targeted at ~10–15%, should net a positive IS Sharpe
across ~2018-01 to 2025-03-23 (covering 2020 COVID + 2022 bear; Dukascopy US-stock depth starts ~2018)
without requiring beta or sector neutralization.
This establishes the anchor that every subsequent EXPLORATION beats or improves upon.

---

## Change

**From:** no baseline (track inception).
**To:** dollar-neutral cross-sectional momentum portfolio.

- Universe: `universe_tradfi.py` — Binance `TRADIFI_PERPETUAL` single-company stocks, PIT, exclude sets
  applied.
- Signal: XS-momentum = 12-1 month return (exclude most-recent month, classic Jegadeesh-Titman),
  inverse-vol scaled (`mom / 63d realized vol`).
- Weights: CONTINUOUS, not tercile/discrete buckets. Each name's weight = its inverse-vol-scaled
  momentum minus the cross-sectional mean (`dollar_neutralize(mom/rvol)`), so the book is
  dollar-neutral (Σ weight = 0) by construction. Names with above-average risk-adjusted momentum
  are long, below-average short, sized by magnitude across the full cross-section. Gross-normalized
  → lagged → vol-targeted at ~12% annualized ex-ante (clip at MAX_LEV).
- Execution: signal on CLOSE[t], rebalance at next-open OPEN[t+1]; taker cost ≈ 6 bps/side on weight
  delta; no funding.
- Implementation: `analysis/portfolio/tradfi/iter_001_xsmom.py`.

---

## IS numbers (Sharpe, maxDD, per-regime)

**PENDING** — ingest pipeline not yet run against real Dukascopy data.

| Metric | IS (~2018-01 to 2025-03-23) |
|--------|----------------------|
| Net Sharpe | PENDING |
| Ann. Return (net) | PENDING |
| Max Drawdown | PENDING |
| Turnover (monthly) | PENDING |
| Avg longs / shorts | PENDING |
| Sharpe @ 2× cost | PENDING |

**Per-regime breakdown (PENDING):**

| Regime | Period | Net Sharpe | Max DD |
|--------|---------|------------|--------|
| Bull (2018–2019) | 2018-01 → 2019-12 | PENDING | PENDING |
| COVID crash | 2020-01 → 2020-06 | PENDING | PENDING |
| Recovery bull | 2020-07 → 2021-12 | PENDING | PENDING |
| 2022 bear | 2022-01 → 2022-12 | PENDING | PENDING |
| Post-bear | 2023-01 → 2025-03 | PENDING | PENDING |

---

## Leak-check result

**MANDATORY dual leak-check** (per design spec § 7, rigor point 2):

| Check | Method | Result |
|-------|--------|--------|
| Future-bar leak | Corrupt all inputs from a cutoff forward; confirm past decisions bit-identical | PENDING |
| Same-bar leak | Corrupt current-bar inputs; confirm current decision bit-identical | PENDING |

> Note: same-bar leak is the class the standard future-only test missed in the metals track; both
> checks are MANDATORY from iter-001 and enforced by `tests/test_portfolio_tradfi_foundation.py`.

---

## Critic verdict

**PENDING** — quant-critic review not yet run (awaiting IS numbers from real data ingest).

Expected check list:
- [ ] Future-bar leak PASS
- [ ] Same-bar leak PASS
- [ ] Dollar-neutrality PASS (net weight within tolerance at each rebalance)
- [ ] PIT / survivorship PASS (no name with backfilled pre-listing returns)
- [ ] OOS gate PASS (engine refused to emit OOS stats without `--confirm`)
- [ ] Cost accounting PASS (fee applied on absolute weight-delta, not notional)
- [ ] Significance note (IS Sharpe with n trades / months)
- [ ] Adversarial findings / constructive path forward

**Verdict:** PENDING

---

## Next

Pending real-data ingest and critic PASS:
- If IS Sharpe > 0 and regime-survivable: tag as CANDIDATE ANCHOR, proceed to CONFIRMATION-001.
- CONFIRMATION-001 will pass `--confirm`, reveal OOS, run full gauntlet (benchmarks, turnover stress,
  DSR/significance), and promote to `BASELINE_TRADFI.md` on critic PASS.
- After CONFIRMATION: iter-002 = beta-neutral overlay.
- If IS Sharpe < 0 or regime fragile: diagnose (signal window, vol-target cap, rebalance cost) before
  proceeding; do NOT advance to CONFIRMATION.

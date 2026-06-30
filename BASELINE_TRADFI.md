# BASELINE_TRADFI

**No baseline yet.** iter-001 (dollar-neutral 12-1m XS-momentum anchor) is **NEGATIVE-CONFIRMED**
(IS Sharpe −0.18, trading-day; fails the +0.30 promotable bar) — a trustworthy, leak-free reject, not
a baseline. A baseline is promoted only at the first CONFIRMATION (critic PASS, OOS revealed via
`--confirm`) of a candidate that clears the IS bar first.

---

**Track:** portfolio-tradfi (market-neutral L/S Binance TradFi single-company stock perps)
**Sacred constants:** `OOS_CUTOFF = 2025-03-24`, **trading-day** bars (weekend/holiday padding dropped),
signals past-only, fills next-open. Universe = Binance `TRADIFI_PERPETUAL` single stocks, 39 sourceable.
**Promotion criterion:** clears IS bar (≥+0.30, all-weather) → CONFIRMATION with critic PASS; OOS revealed.

| Field | Value |
|-------|-------|
| Current baseline iteration | None |
| Working best | iter-006 — net **+0.31** IS (clears +0.30 bar; PROMOTE-CANDIDATE, pending Critic + iter-007) |
| IS Sharpe | — (no baseline) |
| OOS Sharpe | — (hidden until a CONFIRMATION) |
| Universe size | 39 (Dukascopy-sourceable of 42 TradFi single-stock perps) |
| Construction | sector-relative multi-horizon momentum + hysteresis band + bear-state crash gate |
| Last updated | 2026-06-30 (iter-006; iter-007 optimizer in flight) |

## EXPLORATION log

- **iter-001** dollar-neutral 12-1m momentum → **NEGATIVE-CONFIRMED** −0.18 (leak-free; surfaced+fixed the
  calendar→trading-day data bug `eef9b524`). Path: sector-relative at the signal layer.
- **iter-002** sector-relative momentum → +0.08 (sign flip, gross +0.26). PROMISING.
- **iter-003** + hysteresis band δ=0.005 → +0.16 (cost-capture, gross +0.29). Working best.
- **iter-004** + 1m reversal sleeve → NEGATIVE (reversal gross-negative; universe momentum-persistent). Rejected.
- **iter-005** multi-horizon {3-1,6-1,12-1}m blend → +0.20 (gross +0.40, all-weather 1/3→2/3; deeper bear −0.90). KEPT.
- **iter-006** momentum-crash brake (bear-state→slow sleeve) → **+0.31 (CLEARS +0.30 bar)**, bull +0.42/bear −0.54/chop +0.26, maxDD −29.9%. PROMOTE-CANDIDATE (pending Critic + iter-007 optimizer comparison). 2022 crash fixed; COVID V-crash residual.

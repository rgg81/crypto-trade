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
| Last EXPLORATION | iter-001 — NEGATIVE-CONFIRMED (IS −0.18, leak-free, real) |
| IS Sharpe | — (no baseline) |
| OOS Sharpe | — (hidden until a CONFIRMATION) |
| Universe size | 39 (Dukascopy-sourceable of 42 TradFi single-stock perps) |
| Neutrality | dollar-neutral tested (NEGATIVE); next = sector-RELATIVE signal (iter-002) |
| Last updated | 2026-06-30 (iter-001 closeout) |

## EXPLORATION log

- **iter-001** (2026-06-30) — dollar-neutral 12-1m cross-sectional momentum. **NEGATIVE-CONFIRMED**
  IS −0.18 (gross −0.04, signal-driven), maxDD −45.2%, regimes bull −0.20 / bear +0.36 / chop −0.62,
  negate −0.10 (no reversal edge), β≈0. Leak PASS (future + same-bar + trading-day filter). Surfaced +
  fixed a calendar→trading-day data-grain bug (`eef9b524`). Critic BLOCK-PENDING-FIX → NEGATIVE-CONFIRMED.
  Path forward: sector-RELATIVE momentum at the signal layer (β/sector *weight* overlays demoted — inert).

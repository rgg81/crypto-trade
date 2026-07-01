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
| Working best | iter-006 on **Yahoo 2010-25** — net **+0.28** IS (bull +0.30/bear −0.24/chop +0.51); with VIX-brake insurance +0.23, bear −0.09 (~flat) = all-weather-ish; ~0.25 Sharpe robust across 5 bears |
| IS Sharpe | — (no baseline) |
| OOS Sharpe | — (hidden until a CONFIRMATION) |
| Universe size | 39 (Dukascopy-sourceable of 42 TradFi single-stock perps) |
| Construction | sector-relative multi-horizon momentum + hysteresis band + bear-state crash gate |
| Data source | **Yahoo Finance** (split+dividend-adjusted total-return, 69 names + ^VIX); Dukascopy DEPRECATED (split-unadjusted bug) |
| Last updated | 2026-07-01 (iter-009 15-yr/5-bear validation; iter-010 beta-neutral in flight) |

## EXPLORATION log

- **iter-001** dollar-neutral 12-1m momentum → **NEGATIVE-CONFIRMED** −0.18 (leak-free; surfaced+fixed the
  calendar→trading-day data bug `eef9b524`). Path: sector-relative at the signal layer.
- **iter-002** sector-relative momentum → +0.08 (sign flip, gross +0.26). PROMISING.
- **iter-003** + hysteresis band δ=0.005 → +0.16 (cost-capture, gross +0.29). Working best.
- **iter-004** + 1m reversal sleeve → NEGATIVE (reversal gross-negative; universe momentum-persistent). Rejected.
- **iter-005** multi-horizon {3-1,6-1,12-1}m blend → +0.20 (gross +0.40, all-weather 1/3→2/3; deeper bear −0.90). KEPT.
- **iter-006** momentum-crash brake (bear-state→slow sleeve) → **+0.31 (CLEARS +0.30 bar)**, bull +0.42/bear −0.54/chop +0.26, maxDD −29.9%. PROMOTE-CANDIDATE. 2022 crash fixed; COVID V-crash residual.
- **iter-007** portfolio-optimization (MVO + weekly) → **REJECT** (best MVO +0.07 vs naive +0.20; gross +0.31<+0.40; naive=MVO w/ identity cov at N≈40). cvxpy dormant. *(Critic then BLOCK-PENDING-FIX iter-006: Dukascopy SPLIT-UNADJUSTED → arc contaminated.)*

## ⚠️ CLEAN-DATA RE-BASELINE (Yahoo, split+dividend-adjusted, 2026-06-30)

The Critic caught that **all Dukascopy numbers above are contaminated by stock-split-unadjustment** (spurious
−75/−95% split returns, esp. AMZN −95% in the load-bearing 2022 window). Migrated to **Yahoo total-return,
69-name universe + ^VIX**, re-ran the arc. CORRECTED numbers (IS-only, OOS HIDDEN):

| iteration | Dukascopy (contaminated) | **Yahoo (clean, of record)** |
|---|---|---|
| iter-001 dollar-neutral mom | −0.18 (NEGATIVE-CONFIRMED) | **+0.23 — VERDICT OVERTURNED** (splits manufactured the negative) |
| iter-002 sector-relative | +0.08 | +0.31 |
| iter-005 multi-horizon | +0.20 | +0.35 |
| iter-006 crash-gate | +0.31 | **+0.43** (bull +0.60 / **bear −1.23** / chop +0.56), 2× cost +0.27 |

The momentum edge was **understated** by bad data; the qualitative arc holds and is stronger. **Binding
problem on clean data = the −1.23 bear** (high-beta recent IPOs whipsaw) → iter-008 = VIX brake + stop-loss.
iter-006's Dukascopy-calibrated KEEP thresholds need re-calibration (don't trust the in-script REJECT).
Guard added: split-artifact regression test (no single-day |ret_fwd| beyond known-split continuity).

### 15-YEAR VALIDATION (iter-009, 2010-2025, N≈5 bears)
Extended IS to 2010 (42 names full history) to fix the N=2-bear gap. **Momentum edge HOLDS: iter-006 +0.28**
(bull +0.30/bear −0.24/chop +0.51); VIX-alone +0.23 (bear **−0.09 ~flat**). Momentum WON 2 of 5 bears
(2011 +0.85, 2015-16 +1.39); the real tail is sharp REVERSAL crashes (COVID, 2018-Q4), not bears. VIX brake
generalizes (fired 5/5, helped 4/5; whiffed moderate-VIX 2018-Q4). Honest downgrade +0.43→+0.28 (2018-25 was
an era-strong momentum window). N=2-bear overfitting concern RESOLVED; numbers came DOWN on more data.
- **iter-008** VIX brake + stop-loss → WASH for promote (de-risk trades strong regimes for bear); VIX-alone =
  near-free crash insurance (bear −1.23→−0.88 @2018 / −0.24→−0.09 @15yr). Ship VIX-alone, don't stack stop.

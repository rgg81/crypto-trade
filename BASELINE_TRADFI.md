# BASELINE_TRADFI

**No baseline yet.** iter-001 (dollar-neutral 12-1m XS-momentum anchor) is **NEGATIVE-CONFIRMED**
(IS Sharpe −0.18, trading-day; fails the +0.30 promotable bar) — a trustworthy, leak-free reject, not
a baseline. A baseline is promoted only at the first CONFIRMATION (critic PASS, OOS revealed via
`--confirm`) of a candidate that clears the IS bar first.

---

**Track:** portfolio-tradfi (market-neutral L/S Binance TradFi single-company stock perps)
**Sacred constants:** `OOS_CUTOFF = 2025-03-24`, **trading-day** bars (weekend/holiday padding dropped),
signals past-only, fills next-open. Universe = Binance `TRADIFI_PERPETUAL` single stocks, 39 sourceable.
**Promotion criterion OF RECORD (USER-RATIFIED 2026-07-01, revised bar):** net IS Sharpe **≥ +0.50 AND controlled net-beta (≤~0.15) AND positive in ≥13/16 years / no catastrophic year** → CONFIRMATION with critic PASS; OOS revealed. **16/16 (positive EVERY calendar year) is documented as STRUCTURALLY UNREACHABLE** on this data: the diversifier factors (value/quality/BAB/low-vol) are dead 2010-25, and positive-every-year would need perfect market timing (long every bull, flat/short every bear, no turning-point whipsaw). The user explicitly approved **13/16 as the working-best target** plus the directional (controlled-beta) relaxation of pure market-neutrality. (The earlier "positive EVERY year / 16-of-16" wording is SUPERSEDED by this ratified bar.)

| Field | Value |
|-------|-------|
| Current baseline iteration | **iter-016 — CONFIRMED** (bear-gated TSMOM; iter-015 cost-robust + worst-month fix) |
| Working best | **iter-013** (mom+LTR+0.25·TSMOM, **VIX brake ON = DEPLOYED config**, Yahoo 2010-25) — net **+0.61** / maxDD **−28%** / bear **−0.20** / **13/16 years** / net-β **+0.12** (85% neutral). ONE pinned config → the VIX-ON IS anchor (the earlier +0.63/−32% figures were the VIX-OFF row mislabeled "+VIX" — corrected). Misses 2010(warm-up)/2018(bear)/2019(whipsaw); not 16/16 (structurally unreachable). **2× cost (12 bps/side) stress: net +0.42 (< +0.50 — the ≥0.5 bar breaks under DOUBLED taker cost; robust only at the 6 bps/side base cost).** |
| IS Sharpe | **+0.73 @1× / +0.58 @2× (2×-cost-ROBUST)** — gross +0.87, β +0.148; worst yr 2019 −11.1%→**−7.6%**, worst mo Jan-19 −10.8%→**−7.6%** |
| OOS Sharpe | +3.02 @1× (held-out; do-no-harm ≡ iter-015 — bear-gate fired 0/319 all-bull days, so bear-protection OOS-UNTESTED; small-N, do NOT extrapolate; anchor ~+0.7) |
| Universe size | 39 (Dukascopy-sourceable of 42 TradFi single-stock perps) |
| Construction | XS-momentum + LT-reversal + bear-GATED TSMOM tilt (off in EW-252d bear) + VIX brake; band δ=0.010; daily |
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

### MULTI-FACTOR PIVOT (iter-011+, bar ≥0.5 + positive every year)
- **iter-011** mom + 0.5·LTR (3y-1y long-term-reversal value-proxy) → **KEPT net +0.33** (11/16 yrs, 12 w/VIX);
  LTR orthogonal (corr +0.01), fixed the 3 momentum-crash years; misses 2017/2019 (low-dispersion). maxDD −49%.
- **SEC-EDGAR PIT fundamentals** BUILT (filing-date-clean, 56/69) but VALUE −0.34 / QUALITY −0.09 = negative-EV
  on the mega-cap-GROWTH 69 (2010-25 value drought); orthogonal but don't rescue the bad years. Need breadth.
- **iter-012 broad-universe test (525 names) — FALSIFIED the multi-factor premise.** Ceiling = FACTOR problem
  NOT universe: BAB −0.42 / low-vol −0.95 / reversal −0.94 / value −0.34 / quality −0.09 = ALL dead on broad
  (2010-25 momentum+growth decade; value/low-vol had a brutal run). SIZE +1.30 = pure SURVIVORSHIP artifact.
  MOM is STRONGER on the 69 (+0.32) than broad (+0.17). Only MOM + LTR are honest edges. **Net 0.5 +
  positive-EVERY-year is NOT achievable for a PURE market-neutral book on this data.**
- **iter-013 controlled directional TSMOM sleeve (λ=0.25, VIX brake ON = DEPLOYED) → net +0.61 (CLEARS ≥0.5),
  maxDD −28%, bear −0.20, 13/16 yrs, β +0.12.** (VIX-ON anchor; the +0.63/−32% VIX-OFF row was mislabeled
  "+VIX" — corrected.) Fixed 2013/2017 melt-ups + 2020; controlled tilt (85% neutral). Sharpe bar MET at 1×
  cost; 2× cost (12 bps/side) → net +0.42 (bar breaks). 16/16 MISSED (3 residual: 2010 warm-up, 2018 net-long
  bear, 2019 TSMOM whipsaw). Next iter-014 = multi-horizon trend for 2019.
- **iter-014 multi-horizon TSMOM → REJECT** (fast 3/6m speeds whipsaw on the 2018 crash+V-recovery; net
  +0.63→+0.51, 13→12/16). Multi-horizon does NOT generalize to the trend sleeve. **CEILING REACHED.**
- **HONEST CEILING = iter-013 (VIX-ON DEPLOYED): net +0.61 (clears ≥0.5), maxDD −28%, bear −0.20, 13/16 years,
  β +0.12 (85% neutral), 15-yr validated, leak-free. 2× cost (12 bps/side) → net +0.42 (< +0.50 bar).** 16/16
  is NOT honestly achievable: the 3 misses are structural — 2010 (data warm-up), 2018
  (net-long bear cost), 2019 (bull year the neutral book misses + TSMOM whipsaw). Positive-EVERY-year would
  require perfect market timing (long every bull, flat/short every bear, no turning-point whipsaw) AND the
  factor diversifiers that would smooth years (value/quality/BAB/low-vol) are dead 2010-25. Exhausted:
  momentum✓ LTR✓ TSMOM✓ VIX✓ | value✗ quality✗ BAB✗ low-vol✗ reversal✗ MVO✗ multi-horizon-trend✗.

# Team-07 research notes — unjournaled exploratory work

Everything in this file was produced by the team's own approximate simulator
(`research/sim2.py`, `research/panel.py`), **not** by the organiser's evaluator. None of it is a
score, none of it consumed a trial, and no number here is cited as a result. It is the record of
how the design was reached, kept so that the certificate's claims about what was tried are
checkable. The approximation mirrors the organiser's shape — unit-gross normalisation,
reduction-only exposure caps, the trailing-90-day common risk unit off a reference pass,
open-to-open returns, funding summed into the holding interval, 7.5 bps per side — and omits the
participation cap, per-event intra-interval funding, and delisting force exits.

`G*` below is the §7.4 ranking score computed on approximate metrics with the
trial-adjusted-confidence term set to zero, so it is comparable across rows here and nowhere else.

## 1. What the funding data says before any book exists

- 20-name point-in-time universe, 4335 8h decisions from 2020-08-17.
- Funding settles 8-hourly for all but two symbols (ORDIUSDT, WIFUSDT at 4h; 0.29% of rows).
- Median funding is exactly 0.000100 per 8h — Binance's interest component. Above it the perpetual
  traded at a premium; at it, it did not. That is why `PREMIUM_BASELINE = 0.0001` is a mechanism
  constant and not a fitted one.
- Mean annualised funding across eligible names +13.3%; 5th percentile −24%, 95th +81%.
- Funding is strongly persistent: cross-sectional rank autocorrelation +0.60 at one boundary,
  +0.45 at six, +0.34 at 21, +0.26 at 63.
- Trailing mean funding predicts forward price return with rank IC ≈ **−0.018** at every lookback
  from 1 to 63 boundaries. Small, stable and signed the same way as the carry: the rich-funding
  names also drift down. So price and funding legs point the same way rather than opposing.

## 2. The decomposition that set the whole design

Equal-weight top-6 carry sleeves, cadence 9, per fold (price / funding / cost):

| fold | price | funding | cost | net |
|---|---:|---:|---:|---:|
| F1 2020-08 → 2021-08 | −0.050 | **+0.058** | −0.015 | −0.006 |
| F2 2021-08 → 2022-08 | +0.050 | **+0.058** | −0.014 | +0.094 |
| F3 2022-08 → 2023-08 | −0.006 | **+0.061** | −0.014 | +0.041 |
| F4 2023-08 → 2024-08 | −0.006 | **+0.035** | −0.015 | +0.015 |

The funding leg is the same number in every regime. The price leg is the entire fold variance.
Everything after this point is an attempt to reduce price-leg variance without touching the
funding leg.

Beta of the price leg to the equal-weight universe: **−0.022**, explaining **0.8%** of its
variance. The noise is idiosyncratic cross-sectional dispersion, not market direction, so
beta-hedging was abandoned immediately.

## 3. Carry-to-risk sizing — the control that mattered

Splitting the cross-section by each name's own realised volatility and forming the carry spread
inside each tercile (forward 9 boundaries, excess over the eligible cross-section):

| own-vol tercile | carry spread forward return | t |
|---|---:|---:|
| low | **+26.6 bps** | +2.51 |
| mid | +5.0 bps | +0.41 |
| high | −5.7 bps | −0.32 |

Acting on it (`w ∝ 1/σ`, ranking on `(f − median f)/σ`) took `G*` from 14–29 to 32–44 across
breadths. This is the single largest improvement in the whole research programme and it is a
shared risk transform, not alpha.

## 4. Six forms of crowding protection, five of which fail

Crowding measured as **premium duration** — the fraction of the last K settlements above
`PREMIUM_BASELINE`. Its cross-sectional rank correlation with the carry signal is **+0.471**:
substantially the same number, which is the mandate's own warning made quantitative.

| form | strength dial | result |
|---|---|---|
| hard veto: drop entrenched names from the short sleeve, backfill with the next-ranked | `crowd_max` 1.01 → 0.70 | `G*` 42.4 → −27.8, monotone harm at every cadence |
| symmetric veto: also drop entrenched-short names from the long sleeve | `crowd_min` 0 → 0.20 | 42.4 → −3.4 |
| aggregate brake: go flat when market-wide premium duration is high | `brake_max` 1.01 → 0.60 | 42.4 → −21.5; drawdown **unchanged** at 16.3% |
| skip the k richest-carry names in the short sleeve | k 0 → 4 | 43.1 → −18.7 |
| skip the k most entrenched names by premium duration | k 0 → 4 | 43.1 → −7.2 |
| carry-adequacy: stand aside when the cross-sectional spread is thin | 0 → 0.02 | book goes flat 97% of the time; realised volatility **3.6%**, which fails the substance gate |
| **weight guard: multiply short weights by `1 − λ · premium_duration`** | λ 0 → 1 | see below |

The weight guard, on the 7-point neighbourhood median, phase-averaged, at four cadences:

| λ | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---:|---:|---:|---:|---:|---:|
| cadence 1 | 28.2 | 28.8 | 29.5 | 30.6 | 32.9 | 30.2 |
| cadence 2 | 36.6 | 37.0 | 37.7 | 38.7 | 39.0 | 34.4 |
| cadence 3 | 38.1 | 38.4 | 38.6 | 38.9 | 39.8 | 35.4 |
| cadence 6 | 37.8 | 38.0 | 38.6 | 39.1 | 40.4 | 35.6 |

Monotone up to λ ≈ 0.8 in all four, then a fall at λ = 1.0 — the exact point at which a
permanently-premium name reaches zero weight and the guard becomes a filter. That is the same
cliff the five failed forms fall off, reached from the other side.

The guard's crowding lookback is flat over 21–90 settlements (`G*` 40.9 / 41.8 / 41.7 / 40.3) and
decays beyond (126: 33.8; 189: 28.4). 63 sits in the middle of the plateau.

## 5. Cadence and phase

7-point neighbourhood median by cadence and rebalance phase offset:

| cadence | phase-by-phase `G*` | mean | sd | one-way turnover |
|---|---|---:|---:|---:|
| 1 | 37.5 | 37.5 | — | 49.3× |
| **2** | **42.6, 42.4** | **42.5** | **0.1** | **39.7×** |
| 3 | 54.3, 32.8, 45.9 | 44.4 | 8.8 | 34.6× |
| 4 | 40.7, 43.5, 46.2, 50.6 | 45.3 | 3.6 | 31.0× |
| 6 | 40.2, 34.1, 41.2, 54.3, 44.5, 42.4 | 42.8 | 6.1 | 26.5× |

Cadences 3 and 6 divide the three-per-day grid, so each phase locks the book to a single UTC
settlement hour, and the spread across phases is large. Cadence 2 does not divide it: both phases
visit all three settlement hours equally, and the phase axis is measured inert (sd 0.1). Cadence 2
was chosen for that reason — a cadence-3 phase-0 book would have scored better in sample and would
have been a settlement-clock bet, which belongs to a different mandate.

## 6. Things tried and rejected, with the reason

- **Continuous rank tilt / soft-threshold weighting** (`w ∝ −sign(u)·max(0,|u|−θ)/σ`). Worse than
  equal-weight sleeves at every θ, and monotonically worse as θ rises: concentrating on the most
  extreme carry names hurts. Together with §4's skip results this says the return to carry is
  *concave* — the extreme names belong in the book at parity weight, neither over-weighted nor
  removed.
- **Averaging the carry signal across lookbacks** (21/63/126 rank blend). Worse at every breadth.
- **Overlapping tranches** (average the last m target books). Lowered Sharpe monotonically.
- **Hysteresis buffer** on sleeve membership. `G*` across buffer widths 0–6: 43.1, 36.7, 26.8,
  35.8, 6.0, 33.3, 31.7 — no plateau, pure noise. Rejected.
- **Realised drawdown brake in `risk_policy.json`.** A single brake at 10%/0.5 raised `G*` from
  42.4 to 52.3, but phase dispersion rose from ±5.0 to ±12.9 and the brake engages in only two
  episodes across the window. Two effective observations is not evidence. Declined; the risk
  policy is flat.
- **A declared volatility target.** Forbidden by amendment A3 and refused by `--check`. Never used.
- **Market vol-spike stand-aside gate.** `G*` 43.1 → 46.6 at a threshold where it binds at 225 of
  4335 boundaries, and falls away at every tighter setting. Within noise; not adopted.

## 7. Known weaknesses of the nominated book

- One-way turnover ≈ 40× annualised against a 25× floor, and gross edge ≈ 33 bps per unit turnover
  against a 40 bps floor. Both are §7.3 performance floors, both are missed, and under amendment
  A4 both cost points rather than admission — neither appears in the §7.4 ranking inputs nor in the
  §8 holdout eligibility list. They are real weaknesses of the book as a deployable object and are
  reported as such. Slowing to cadence 6 clears the gross-edge floor and nearly clears turnover,
  at the cost of re-introducing the settlement-hour phase exposure of §5.
- The book is a 14-name cross-section out of 20, so the exposure caps trim it; the `exposure_caps`
  block in each packet records by how much.
- Two symbols settle 4-hourly, so `CARRY_LOOKBACK = 63` *settlements* spans fewer calendar days
  for them than for the rest. 0.29% of funding rows.

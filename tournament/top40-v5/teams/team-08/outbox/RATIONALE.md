# team-08 — discovery candidate rationale

**Family:** time-series trend. **Cell:** the Tier-1 centre of the preregistered surface —
`W = ALL (8 rungs)`, `T = tanh z`, `N = 30`, with every §7.1 default of `lane/scouting/THESIS.md`
left where it was fixed. This is deliberately the plainest expression of the mandate. It is a
baseline I can diagnose, not a book I have tuned.

No feedback packets exist in `lane/feedback/` yet, so nothing here is informed by any result. Every
choice below traces to the sealed thesis or to the protocol.

---

## 1. The mechanism

Per contract *i*, using only contract *i*'s own past log closes:

1. **Ladder.** Eight log-spaced lookbacks — `{1, 2, 4, 7, 15, 30, 60, 120}` days. On an 8h clock
   these are the declared `{3, 6, 12, 21, 45, 90, 180, 360}` bars.
2. **Standardise.** Rung *L* contributes `z = (log P_t − log P_{t−L}) / (σ_i · √L)`, where `σ_i` is
   an EWMA of squared per-bar log returns with centre of mass 20 days (the MOP form on this clock).
   Dividing by `σ_i·√L` makes rungs commensurable and makes the signal invariant to price level.
3. **Transform and blend.** Each rung maps to a position with `tanh(z)`; the rungs are equally
   weighted. Each rung is a sub-strategy and the blend is a portfolio of sub-strategies, which is
   what makes the per-rung falsifier F-B directly computable.
4. **Volatility scale.** Position size is `signal_i × (1/σ_i)`, capped at 3× the median inverse-vol
   weight. This sets **relative** risk across contracts. It is not volatility targeting.
5. **Constrain.** Normalise to unit gross, clip `|w_i| ≤ 0.099` with redistribution, then bring
   `|net| ≤ 0.245` by shrinking the dominant side.

Why a ladder rather than one horizon: the thesis (§1.1) claims trend in perpetuals is the **sum of
two premia with different clocks**. The slow rungs (15–120d) harvest the classical Moskowitz–Ooi–
Pedersen under-reaction to slowly diffusing information — and crypto has no valuation anchor, so no
one can lean against a move early and the correction arrives late. The fast rungs (1–7d) harvest
something that has no analogue in the CTA literature: a Binance perpetual sits under a maintenance-
margin liquidation engine that emits **market orders in the direction of the move** when levered
positions breach margin. That is a mechanical autocorrelation generator with a timescale of hours to
days. Two mechanisms, two failure modes, one ladder. Multiple lookbacks is the claim, not a hedge
against not knowing the right horizon.

## 2. Who is on the other side

- **The cash-and-carry basis desk — and they are being paid, by me.** Binance's documented funding
  formula reduces at zero premium to +0.01% per 8h interval, longs to shorts, ≈11%/yr, by contract
  design rather than market outcome. A trend book is long-biased in a drifting-up sample, so it pays
  this continuously and pays most when it is winning. This is the one counterparty identifiable from
  exchange documentation rather than by inference, and it is the reason a trend result measured on
  price return alone is measuring something untradeable.
- **Levered retail on the wrong side.** The retail instinct is counter-trend — buy the dip, short the
  top — which supplies liquidity against a developing trend and is then liquidated by it. The
  transfer is executed by the liquidation engine, mechanically.
- **Inventory hedgers.** Miners, treasuries, unlock recipients, market makers laying off spot flow.
  The classical MOP risk-transfer story; it survives the transplant, smaller here than in commodities.
- **Short-horizon liquidity providers**, who are mean-reverting by construction and get run over by
  persistent one-directional taker flow. This is the counterparty at the fast rungs specifically.
- **Conspicuously absent:** any natural value investor. There is no discounted-cash-flow argument
  against a token perpetual. The missing participant is the point.

## 3. What is deliberately not here

Per thesis §5: no cross-sectional ranking or relative strength; no funding or basis signal as alpha
(funding is a cost in P&L, never an input to the Tier-1 signal — `context.funding` is untouched); no
reversal overlay; no order-flow alpha from `trade_count` or `taker_buy_volume`; no per-contract
parameter fitting; and — the commitment that matters most — **no volatility-regime gate, drawdown
control or exposure throttle**. A vol-conditional overlay is volatility targeting in a trend costume,
and Kim/Tse/Wald argue exactly that device produced most of the headline TSMOM result. Allowing it
would make falsifier F-A unfalsifiable by construction.

## 4. Two honest notes on the implementation

**(a) The no-trade band is not implementable, so it is off.** Thesis §7.1 fixed a Tier-1 default of a
0.10 × target no-trade band. `DecisionContext` exposes no positions and the strategy may hold no
state across decisions, so a band cannot be computed. This candidate therefore runs at `D = 0.00`,
which is a declared Tier-2 value. This is a **forced deviation, not a search step**, and I record it
rather than quietly amending the fixed table. It means turnover here is the honest upper end of the
declared surface.

**(b) The net-exposure cap throttles gross in one-sided regimes, and that is not my doing.** Because
`|net| ≤ 0.25` and `gross ≤ 1.0`, an all-one-way book cannot exceed 0.25 gross. When crypto trends
together — which, at ~0.6 average pairwise correlation, is often — my gross exposure collapses
toward 0.25 automatically. I shrink the dominant side rather than shifting all weights by a constant,
because a shift flips the sign of small positions and would let a book-level adjustment override a
per-contract forecast; shrinking never changes any contract's direction and preserves more gross.
I flag this now so that when the packet shows variable gross exposure I do not later mistake a
constraint artefact for a design choice. It is conditioned on directional crowding, never on
volatility, so it does not breach §0.

**(c) The ladder is declared in days and mapped to bars at runtime.** I do not know the mounted bar
spacing from `protocol.py`, only that funding settles every 8h. Hard-coding "360 bars = 120 days"
would silently become 15 days on an hourly dataset. The strategy infers bar spacing from the index's
own median step — relative spacing only, never an absolute date, so it stays calendar-shift
equivariant. If enough contracts cannot support the longest rungs, the ladder is truncated **for
every contract identically**, so no contract ever runs a different construction from its neighbours.

## 5. What would falsify this

From the sealed thesis, unchanged:

- **F-A (primary).** Hold the universe, the inverse-vol weights, the schedule, the gross and the cost
  accounting fixed; replace only the trend signal's sign and magnitude with a long-fraction-matched,
  block-bootstrapped sign-scrambled control. **If the trend-signed book does not beat that control
  distribution at empirical p ≤ 0.10, the mandate has failed** — what I would have is the organizer's
  common risk unit plus an inverse-vol tilt, not time-series trend, and I will say exactly that.
- **F-B (co-primary).** Standalone mean net return of each rung, equally weighted across the universe.
  **If the positive rungs do not form a contiguous block of at least three**, a positive blended book
  is grid-search noise. Trend, if real, has a bandwidth; noise scatters. A fair coin fails this ~58%
  of the time, so it is a real hurdle.
- **F-C (assigned floor).** If no rung produces positive average returns per contract, time-series
  trend does not persist in this universe. Implied by F-B, restated because it is the assigned test.
- **D-1 (diagnostic, not a falsifier).** If the trend book loses to a static always-long book at
  identical inverse-vol weights *but passes F-A*, the reading is "the sign forecast carries
  information, the sample's drift dominated it" — not "the family is refuted." Declared in advance so
  I cannot spin it later.

Secondary predictions I am on record for (§2): funding drag monotone in rung length; short-signal
bars improving relative to long-signal bars net of funding; low mutual correlation between fast and
slow rungs (if all eight correlate above ~0.8 the ladder is decorative and I will say so); effective
independent bets under 5 in a 30-perp book; P&L concentrated in the top few percent of bars; and
**per-contract Sharpe of order 0.2–0.5 — anything materially above 1 on development data should be
read as a bug or a leak, not a discovery.**

## 6. What I expect this baseline to look like, before I see it

Modest gross edge, high whipsaw, meaningful cost share, and a gross exposure that varies with how
one-sided the market is. The failure regime is not a crash; it is a **high-volatility, zero-net-drift
range**, which is doubly bad here because inverse-vol sizing shrinks positions *after* the volatility
arrives. The two metrics I most want from the packet are **turnover** (the no-trade band is off, so
this is the surface's upper bound, and the declared `W` axis — FAST/MID/SLOW/CORE — is the
preregistered lever for it) and **the long/short exposure split**, which tells me how hard the net cap
is binding. Neither is a reason to hill-climb; twelve feedback-driven trials make a development Sharpe
a statement about a search rather than an edge.

If F-A or F-B fails, the stopping rule is already declared: I will not mine the grid for a passing
cell. I will nominate the minimal-change, seed-adjacent configuration and report the failure.

**Trial accounting.** Declared surface: 45 Tier-1 + 36 contingent Tier-2 = 81. This candidate is one
Tier-1 cell.

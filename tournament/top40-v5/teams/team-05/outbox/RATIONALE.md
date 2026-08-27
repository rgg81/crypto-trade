# RATIONALE — team-05, discovery

**Lane:** illiquidity-conditioned short-horizon reversal (cross-sectional mispricing)
**Phase:** discovery. No feedback packets exist yet; nothing in this document is fitted to a result.
**Relation to the sealed thesis:** this is the base configuration of the declared surface, not the
declared default. The one deliberate deviation is stated in §5 rather than left to be discovered.

---

## 1. The book in one line

    weight_i  ∝  (½ − rank(r_i)) · rank(ILLIQ_i) · clip(median σ / σ_i)

Fade the last 8h cross-sectional move, and scale that fade linearly in the name's *ex-ante*
illiquidity percentile. Dollar-neutral, rank-weighted across the full tradable cross-section, unit
gross every bar.

There is one factor and one conditioning variable. That is the point of this phase: I want the first
metric packet to be attributable to a mechanism, not to an interaction between six choices.

## 2. The mechanism, and why the conditioning is the strategy

Short-horizon reversal is not a mispricing being corrected. Following Nagel (2012), a negative past
return is a *noisy observation of the inventory the market-making sector was just forced to absorb*,
and the reversal profit is the rent paid to whoever takes that inventory off their hands. The
discriminant matters: information-driven price impact is permanent and induces no negative serial
correlation (Glosten–Milgrom), so any reversal profit that exists is, by construction, the inventory
channel net of the information channel.

If that is the mechanism, the premium must scale with the shadow cost of inventory to the marginal
liquidity supplier. That cost is unobservable; Amihud illiquidity — absolute return per dollar of
volume — is its observable dual, since it *is* price impact per dollar of flow, i.e. the inverse of
the depth the marginal maker will show. Thin book → same order displaces price further → the maker
ends up holding more inventory relative to their risk budget → they charge more to hold it.

So the tilt term is not a filter bolted onto a reversal signal. It is the mandate written as
arithmetic: **reversal strength is an increasing function of ex-ante illiquidity.** Strip the tilt
and this book is a generic reversal ranker that makes no claim about liquidity provision at all.

The crypto prior justifies the conditioning rather than the raw trade. Bianchi, Babiak & Dickerson
(2022) find the reversal premium at +1.26%/day equal-weighted in low-activity pairs versus
+0.54%/day in high-activity, and — the line that decides this design — value-weighted the liquid
half is an insignificant **−0.19%/day**. The premium lives in the thin half. Meanwhile Liu, Tsyvinski
& Wu (2022) document weekly *continuation* across ~1,800 coins. My thesis is only coherent if these
coexist: momentum in the liquid core, reversal in the illiquid tail, at a shorter horizon. A raw
unconditional reversal book would be betting against the better-established of the two results.

## 3. Who is on the other side

At the 8h bar boundary on Binance USD-M I am the residual liquidity supplier to four populations:

1. **Forcibly liquidated leveraged traders.** The exchange's liquidation engine submits their market
   order. They did not choose to trade, hold no information, and cannot wait for a better price.
   This is the purest liquidity-motivated flow in any liquid market, and it does not exist in the
   equity cross-section the founding literature was built on. Ali, Peng & Shams (2025) name this
   channel directly: forced liquidations trigger cascading price reversals on high-leverage perp
   venues.
2. **Retail momentum takers** chasing the 8h move and paying the taker fee for immediacy.
3. **Delta-neutral and funding-carry desks** rebalancing around the 00/08/16 UTC settlements — i.e.
   non-informational flow clustered exactly at my decision boundary.
4. **Market makers who have already left.** Not my counterparty — the *reason* my counterparty got a
   bad price. When realized vol spikes and their collateral tightens, they widen or pull quotes. The
   illiquidity tilt is my attempt to point the book at the names where that has just happened.

Funding is treated as a cost/credit and **never as a signal**. Funding-as-signal is the carry
family, not mine, and blending it would make the falsifier untestable.

## 4. Construction choices, and what each is defending against

| Choice | Why |
|---|---|
| Rank transforms throughout | Crypto's cross-section is fat-tailed; a raw-return factor would be one outlier per bar. Also makes the book invariant to price scale and to any monotone relabelling. |
| Percentile ranks on (0,1) via `(rank−½)/n` | No name gets an exactly-zero multiplier, so the tilt is continuous rather than a disguised gate. |
| Continuous tilt, not a tercile gate | A gate has a boundary that can be fit to a subsample and would break the organizer's small-perturbation stability check. A continuous confirmation is also the stronger evidence for the mandate. |
| No explicit demeaning step in code | Da, Liu & Schaumburg (2014) show raw reversal is contaminated by across-industry momentum — in crypto, BTC/ETH beta. Cross-sectional demeaning is required, but `rank(r)` ≡ `rank(r − mean r)`, so the rank transform already carries it. Stated because a missing line that *looks* missing is worse than one explained. |
| Full cross-section, no top-N cut | A top-N threshold is a hidden knob. Linear-in-rank weighting already sends near-median names to near-zero weight, which is the same effect without a fitted boundary. |
| `1/σ` balancing, clipped to [0.5, 2.0]× | Cross-sectional risk balancing at **constant gross** — not a volatility target, which the rules reserve to the organizer. Without it the book's risk is owned by whichever illiquid name is currently most volatile. The clip is a stability guard, not an alpha knob. |
| 30-bar median volume floor at the 20th percentile | Declared ex ante. Participation is capped at 0.1% of prior-24h quote volume, so weight on untradable names silently converts into un-filled gross. The floor drops the part of the tail I could not actually harvest anyway. |
| Explicit net/gross/per-symbol clamps | The evaluator enforces them regardless; doing it myself means the book I reason about is the book that trades. |
| No use of `decision_time`, no symbol literals, all windows anchored at the newest row | Satisfies calendar-shift equivariance, symbol pseudonymisation, and future-append invariance by construction rather than by luck. |

Stateless by design: every decision is recomputed from the past-only rows in `context`. No RNG, no
persisted state, no embedded parameters.

## 5. What this is *not* — the one declared deviation

The sealed thesis names a default configuration with `inventory_proxy = return_and_flow` and
`turnover_band = 0.25`. This candidate runs `return` and `0.0`. That is a deviation and I am
recording it rather than quietly shipping it:

- **Taker-flow inventory proxy.** §1.6 of the thesis declares it as a *refinement* to Nagel's noisy
  proxy — and flags that the practitioner evidence on order-flow imbalance in perps runs momentum,
  not reversal, at sub-minute horizons, so the sign may not survive aggregation to 8h. Adding it now
  would mean the first packet cannot separate "reversal conditioned on illiquidity works" from "the
  flow sign survived aggregation". It is a later-phase test with a clean control.
- **No-trade band.** A band compares against the position I am actually holding, which I cannot
  observe and may not persist. Implementing it would mean recomputing my own prior target from
  truncated history — a real technique, but one that adds a second failure surface to a baseline
  whose job is to be diagnosable. It is the first thing I add if costs are the binding constraint.

Both deviations are in the conservative direction: fewer active knobs than preregistered, not more.

## 6. What would falsify this

The mandate's falsifier, restated on what this candidate can actually show:

- **Primary.** If reversal strength does not increase with illiquidity, the premium is not
  compensation for providing liquidity. On the development window that means: if this
  illiquidity-tilted book does not beat an equivalently-constructed *unconditional* reversal book on
  gross Sharpe, the conditioning is doing nothing and the liquidity-provision story is wrong.
  Pre-committed consequence: I do not swap the conditioning variable for one that works, and I do
  not nominate an illiquidity-conditioned book.
- **Sign.** If the panel interaction between past return and illiquidity is non-negative, same
  conclusion. Note the thesis explicitly permits the *unconditional* reversal coefficient to be zero
  or positive — crypto momentum per Liu et al. — while the interaction is negative. That case would
  be the strongest confirmation available, because conditioning would be doing all the work.
- **Tradeability, scored separately on purpose.** The mechanism claim is about gross returns. Whether
  it survives taker execution at 8h is a different question, and conflating them would let a cost
  failure masquerade as a refutation of the economics. Avramov, Chordia & Goyal (2006) is explicit
  that contrarian profits in high-turnover, low-liquidity names are smaller than the transaction
  costs of harvesting them, and my cost scales with the same ILLIQ that generates the premium —
  there is an interior optimum in illiquidity and it may be at zero net of costs.

**The failure mode I expect, named in advance.** Junior (2026) runs a near-identical exercise on
Binance USDT-margined perps and reports a gradient-boosted ranker reaching positive rank-IC
(+0.0243) alongside net Sharpe −2.91 and −95.6% drawdown. Positive IC with deeply negative net
Sharpe is the signature of a turnover-and-cost failure, not a signal failure. If this book's packet
shows edge in the signal and destruction in the P&L — high turnover, poor gross edge per unit
turnover, cost share dominating, death at 3× cost — that is the predicted outcome, and the response
is the buy/hold spread of Novy-Marx & Velikov (2016), not a new signal.

Zero movement from the seed is an acceptable outcome of this lane. A rescued falsifier is not.

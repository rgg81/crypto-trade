# RATIONALE — team-03, discovery baseline

**Candidate:** `lane/outbox/candidate.py` → `build_strategy()` → `DefensiveBetaControlled`
**Thesis of record:** `lane/scouting/THESIS.md` (sealed in phase S; every constant below traces to §4)
**Phase intent:** the mandate in its most direct form. One signal, one hedge, no composite.

---

## 1. What the book is

At every decision, from past-only rows:

1. **Universe.** `context.eligible_symbols` ∩ `context.bars`, seasoned to ≥ 252 bars (84 days).
   If fewer than 10 members clear that, step down through 126 → 63 bars. The ladder is the
   §4.2 step-down contingency, declared before data, and exists so that a short visible window
   or a young universe degrades the book instead of emptying it.
2. **Liquidity screen.** Keep the top 70% by trailing 63-bar median `quote_volume`. This is the
   Novy-Marx–Velikov guard: rank weighting *is* equal weighting, and equal weighting in crypto
   walks straight into the thinnest contracts, where impact eats the whole spread.
3. **Sort variable.** Parkinson high–low realized volatility over 63 bars (21 days). Declared
   estimator (§4.2); 63 bars is the **midpoint** of the declared `{21, 63, 189}` grid, chosen
   because the midpoint is the one value in the grid I cannot be accused of having picked.
4. **Rank weights.** `w_i ∝ (mean_rank − rank_i)`, normalised to gross 1 and net 0 — long the
   low-volatility end, short the high-volatility end, across the whole screened cross-section
   rather than terciles. Frazzini–Pedersen's construction, and the version §4.2 nominates on.
5. **Beta control.** `β̂_i = ρ̂_i · σ̂_i / σ̂_m` from 8h close-to-close log returns — σ over 63
   bars, ρ over 378 bars (126 days), against the **equal-weight index of the seasoned member
   universe** (not of my screened subset: neutrality is defined against membership, per the
   mandate). Shrunk `β = 0.6·β̂ + 0.4`. The spread is short beta by construction, so the book is
   tilted **toward** the index by exactly `λ = −β_p`, which neutralises it.
6. **Budgets.** Per name 5% of gross (§4.2, inside the organizer's 10%), gross 0.98, net ≤ 23%
   of gross. Constraints are applied in an order where each step preserves the previous
   invariant, so nothing later un-does anything earlier.

Then it does that again next bar. There is no state, no schedule, and no reference to
`decision_time`.

## 2. The mechanism, and why it is not the equity story

The canonical BAB mechanism is a leverage *constraint*. **That channel is largely absent here and
the thesis does not rest on it** (§1.1): Binance sells 125x on BTC and caps most alts at ≤ 75x, so
the venue's constraint runs the *wrong way* — a return-hungry trader can lever the low-beta name
more cheaply than the high-beta one. Importing the equity rationale unexamined into a 125x venue
would be the mistake.

The claim instead (§1.2) is that on a perpetual, the compensation for holding the defensive side
is not only an unobservable expected-return wedge — a large part of it is **metered and paid in
cash every eight hours as funding**. Leverage-seeking and lottery-seeking directional demand
concentrates in high-volatility, low-quality contracts; when the perp trades above index, longs
pay shorts. Binance BTC perp funding averaged ~13.7% annualized 2020–2025 against ~3.1% bills,
and BTC is the *most* arbitraged, *lowest*-beta contract on the venue. The interesting object is
the cross-sectional dispersion of that number.

So: **short high-volatility, long low-volatility, beta-neutral to the member index.** The funding
spread is collected by *holding* the position, not by signalling on it. This is why
`funding_tilt` is **off** in this baseline and the candidate never opens `context.funding` — the
funding channel is the reason the trade should pay, not a second signal. Turning it into a signal
is a separate, testable claim (§4.1 knob 5), and it belongs in a later phase where I can attribute
the difference.

**The level of funding is explicitly disclaimed as edge** (§1.2). Funding is positive on average
by construction — the +0.01%/8h interest term and the clamp asymmetry guarantee it. Harvesting the
level is a short-the-market bet wearing a carry costume; it would be caught by the beta control,
it is not what the mandate names, and the common ex-ante risk unit would not reward it. The claim
is strictly about the **cross-sectional** spread per unit of beta, which survives beta-neutrality.

## 3. Who is on the other side

**Paying me:** levered retail directional longs on alt perpetuals — the structural funding payer,
at 20x–100x, with a financing cost dripped out in 8h increments precisely where it is least
salient. Behind them, trend-following systematic books, which are structurally long the
highest-beta names in an uptrend and mechanically add as realized volatility rises.

**Already on my side, and therefore my competition:** delta-neutral basis and cash-and-carry desks
shorting the highest-funding perps against spot. I do not claim nobody does this. I claim the
beta-neutral, cross-sectional, index-relative expression carries a different risk profile from the
delta-neutral carry expression, and that carry capacity binds hardest in the small illiquid
contracts my liquidity screen deliberately removes. Token treasuries and market makers hedging
long spot inventory are also short perps — their presence is a reason the spread does not fully
close, and a reason it should not be expected to be large.

## 4. What falsifies it

The preregistered falsifier (TEAM-BRIEF, THESIS §3):

> If low-volatility members do not outperform high-volatility members on a beta-adjusted basis,
> the defensive premium does not exist here.

**F1 fires** if the beta-neutral low-minus-high spread has annualized Sharpe ≤ 0 on the full
visible window, **or** if its sign is negative in a majority of non-overlapping 90-day blocks.
Condition (b) is the one I expect to bite: a defensive premium that lives in one alt-cycle
drawdown and nowhere else is a single trade, not a premium. **If F1 fires I report a negative
result and nominate the unmodified organizer seed** — I do not re-specify the volatility
estimator, re-cut the sort, re-screen the universe, or hunt a sub-window.

**F2 (mechanism)** fires if the funding component of the spread is ≤ 0. If F2 fires but F1 passes,
I will say in writing that my stated mechanism is wrong and any positive result is an unexplained
regularity, not the thesis I preregistered.

**F3 (junk leg)** is not live in this candidate — `junk_leg` is off — so it cannot be evaluated
here by construction.

**Not a rescue, stated in advance:** faster rebalancing than the declared grid, a different
universe start, excluding named symbols, excluding a named drawdown, a lower cost assumption, or
a signal from a field outside the six I have.

## 5. Deviations from the thesis, declared

Two, both stated rather than buried.

**(a) Rebalance cadence.** §4.1 declares `rebalance ∈ {21, 42}` bars. This candidate reprices
**every decision**. The reason is mechanical, not economic: implementing a holding period without
persistent state requires a rebalance clock derived from the data, and every clock available to me
either keys off `decision_time` (which is what the calendar-shift check exists to catch) or off
bar counts (which silently degenerates to *never trading* if `bars` is delivered as a fixed
window rather than full history). A book that holds flat for the whole window scores as a book
with no edge rather than one that never ran — the exact failure the rules warn about, and not a
failure I am willing to buy on a first trial.

The signal itself is slow — 63-bar Parkinson volatility, 378-bar correlations — so the turnover
is almost entirely drift-rebalancing, not signal churn. Crucially, this deviation runs in the
**costly** direction: it is an upper bound on the book's turnover, so if it clears the cost gates
it clears them with room, and if cost is what kills it, the packet will say so in `cost share` and
`gross edge per unit turnover` rather than leaving me guessing. Adding the declared holding period
is then a *measured* change, not a rescue — and I will read a slower version as confirmation only
if the mechanism is already visible at this cadence.

**(b) Net cap vs. exact beta neutrality.** Full beta neutrality means going net long the index,
and the organizer's `|net| ≤ 0.25` can make it infeasible when cross-sectional beta dispersion is
wide. The candidate takes the largest hedge the budget permits (bisecting λ against a 23% net
budget) and carries the residual short-beta knowingly, rather than being clipped arbitrarily by
the evaluator. Worth noting: the declared 0.6 shrinkage is what usually makes full neutrality
feasible at all — un-shrunk betas push the required tilt past the net wall. That is an argument
for shrinkage I did not anticipate when declaring it, and I am recording it as a consequence, not
as a new result.

## 6. What I expect, and what would surprise me

I expect the book to lose money sharply in alt melt-ups and in broad liquidation cascades, and to
make its return in the drift between them — short convexity, with drawdowns clustered rather than
gradual. The strongest published argument that this mandate is **empty** is Borri–Liu–Tsyvinski–Wu
(2026): market beta has no significant predictive power in the crypto cross-section, and most
equity smart-beta strategies are subsumed by a four-factor model. My only answer is that those
results are about spot, coin-level total returns, and a perpetual's return is price return *minus
funding*. If the price spread is zero **and** the funding spread is zero, I am simply wrong.

The literature also disagrees with itself on the sign of the crypto lottery channel — Grobys &
Junttila (2021) find low-MAX beats high-MAX, Ozdamar–Akdeniz–Sensoy (2021) find the opposite, and
I could not resolve it. That unresolved conflict is why the falsifier is not a formality.

**Diagnostics I will read first in the packet,** in order: (1) the sign and block-stability of the
spread, for F1; (2) cost share and gross edge per unit turnover, which decide whether cadence (§5a)
is the next change; (3) realized net and gross exposure, to confirm the beta tilt is landing where
the construction says it should; (4) effective breadth, to confirm rank weighting is producing a
portfolio and not a two-name bet.

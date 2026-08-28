# RATIONALE — team-01, trial t02

**Candidate:** `lane/outbox/candidate.py` → `build_strategy()` → `SlowFundingCarry`
**Family:** risk-premium harvesting — cross-sectional funding carry with crowding protection
**Preregistered thesis:** `lane/scouting/THESIS.md` (sealed 2026-08-26)
**Direction:** harvest, as committed in F3. Long the most-negative-funding names, short the
most-positive. Not flipped.

---

## 1. Diagnosis: four failed gates, one failure

t01 (the unmodified organiser seed) failed `turnover_ceiling`, `gross_edge_density`,
`cost_share` and `survives_triple_cost`. Those are not four problems. Net return is linear in
the cost multiplier, so the 1x and 3x numbers identify gross and cost separately:

```
net(1x) = G −  C = − 2.87%/yr
net(3x) = G − 3C = −37.13%/yr
------------------------------------------
        C ≈ 17.1%/yr      G ≈ +14.3%/yr
        cost ≈ 5.9 bp per unit of annualised turnover   (17.1% / 289.5)
        gross Sharpe ≈ 14.3 / 10.4 ≈ 1.37
```

Every structural gate that was *not* about cost passed, and passed comfortably:
`breadth_pass_fraction` 1.0, `active_bar_fraction` 1.0, `mean_gross_exposure` 0.96, long/short
exposure share 0.500/0.500, `ruined` false.

So the reading is unambiguous, and it is the opposite of discouraging: **the funding premium is
present in this universe at roughly 1.4 gross Sharpe, and the seed spends all of it and more on
trading.** My mandate's falsifier F1 asks whether sorting on funding produces spread once
crowding is controlled. Nothing here says it does not. What t01 falsifies is a construction, not
a thesis.

The break-even condition at triple cost is arithmetic:

```
G > 3 · c · T   ⟹   T < 1426 bp / (3 × 5.9 bp) ≈ 80 turns/yr
```

The seed runs 289. That is the whole gap.

## 2. What was actually wrong with the design — and it is a design problem

Refinement guidance says a structural gate failure is a design problem, not a parameter problem.
I want to name the design defect precisely, because it is mine and it is in the preregistration:

> **My declared parameter surface (THESIS §4.2) contains no turnover control of any kind.**

Eight knobs — universe size, funding lookback, normalisation, crowding metric, crowding lookback,
overlay strength, leg fraction, tail trim — and not one of them governs how fast the book trades.
`Rebalance: every 8h bar` was declared as fixed, with the note "the data's native resolution; not
a free parameter". That sentence is where the error is. Rebalance frequency is not a free
parameter, but *signal* frequency is, and I conflated them. Declaring an 8h decision cadence
silently declared that the tradable object is the 8h funding print.

It is not. The mechanism I preregistered pays for **holding** the side opposite the crowd: the
funding transfer accrues at every settlement whether or not I trade. The carry leg is, in my own
words, *arithmetic*. Re-ranking the cross-section on the newest print every eight hours converts
a holding premium into a high-frequency ranking exercise and pays 5.9 bp for each round trip of
noise. Two further construction choices amplified it: hard quantile legs, where a name crosses
the boundary at full weight rather than at zero, and a narrow book (effective breadth 12.9) whose
per-name weights are large enough that ordinary rank churn moves real notional.

I am recording this as a falsification of a declared design commitment, not as a tuning outcome.

## 3. What this candidate changes

Four structural changes. None is a swept parameter; each is a different answer to "what is the
tradable object", and the constants are set by the §1 arithmetic rather than by search.

**(a) The signal is the funding regime, not the funding print.** Carry is an exponentially
weighted funding accrual with a ~14-day centre of mass (`CARRY_TAU_H = 336h`), giving a per-bar
innovation weight of `exp(−8/336) → 0.024` against something on the order of 0.3–1.0 for the
seed. Funding is strongly autocorrelated — that is what makes it a premium rather than a
sequence of shocks — so the slow component carries most of the cross-sectional spread and almost
none of the churn.

**(b) The settlement schedule is inferred, not assumed.** Binance settles 8h, 4h or hourly by
symbol and regime, and the published rate carries a `/(8/N)` divisor (THESIS §4.1, citation [3]).
Per symbol the code infers the mean interval from the spacing of that symbol's own settlements
and rescales the accrual to 8 hours. Without this, fast-settling names — exactly the crowded,
cap-pinned ones the thesis is about — are systematically mis-ranked. This was declared as fixed
preprocessing; it is implemented here for the first time.

**(c) Soft thresholds instead of hard legs.** The book is a rank tilt over the whole liquid
cross-section, soft-thresholded within each side so that a name entering the leg enters at **zero**
weight and scales up continuously. Boundary crossings, which are the single largest turnover
source in a quantile-bucket book, become free. Roughly the top and bottom quarter carry the book
(`ACTIVE_FRAC = 0.50`, ≈ the declared `q`), giving ~38 active names and expected effective breadth
near 28 against the seed's 12.9 — more diversification at the same ex-ante risk, which raises
Sharpe and therefore raises gross edge per unit of turnover directly.

**(d) The crowding overlay is made slow enough that it cannot pay for itself in turnover.** Every
input is a slow statistic: C1 is magnitude-weighted funding-sign persistence over the window
(replacing the declared integer run-length, which is schedule-dependent and jumpy — a pure
turnover generator); C2 uses aggressor-share EW half-lives of 21 and 84 bars; C3 is carry rank
minus log-liquidity rank. λ = 0.5 as declared. C3 additionally pushes weight away from large
premia sitting on thin turnover, which is where slippage and the 0.1%-of-volume participation cap
both live — so the overlay is expected to help the cost gates, not just the tail.

Retained from the preregistration unchanged: harvest direction; carry-to-risk normalisation;
dollar-neutrality (exact, by side balancing); beta-neutrality to the equal-weight universe with
shrinkage and a cap on how much of the book the hedge may restructure; top-75 liquidity screen;
listing burn-in; constant gross; **no volatility targeting of any kind** — gross is normalised to
a constant 1.0 and the organizer's risk unit owns the rest.

## 4. Declared-surface extension, stated rather than hidden

THESIS §4.3: *"If, once data is mounted, I find that a knob I did not declare would materially
change the result, the honest move is to report that fact in the nomination and leave it
unsearched."* Invoking that clause now.

| Item | Declared | Here | Status |
|---|---|---|---|
| Funding lookback `L` | {1, 3, 9, 21} bars | ~42-bar centre of mass, EW | **outside the declared grid** |
| Turnover control | *absent from the surface* | soft thresholds + slow overlay inputs | **new layer** |
| C1 functional form | integer run length | magnitude-weighted sign persistence | substituted |
| C2 lookback `K` | {3, 9, 21} | 21 fast / 84 slow reference | fast leg declared; reference leg new |

These were chosen by the cost arithmetic in §1 — pick the slowest signal that still ranks the
cross-section, then verify `T < 80` is implied — **not** by sweeping and keeping a winner. I have
evaluated **two** configurations on visible data (t01, t02). That literal count is what belongs
in the deflated-Sharpe trial number, and I will keep reporting it honestly even as it grows.

## 5. Who is on the other side

Unchanged from the thesis, and worth restating because it is what makes this a premium rather
than a pattern. On the short leg I face the levered directional long — retail and trend-following
demand for convex, custody-free, stablecoin-collateralised upside, whose position size is set by
their margin rather than by their view, and who leaves forcibly in a liquidation cascade. On the
long leg I face the squeezed short inside a cascade. I am not facing an arbitrageur: for the long
tail of alt perps there is no deep, cheaply borrowable spot on the same venue with the same
collateral, so cash-and-carry cannot close the gap and the only way to take the receiving side is
to bear the risk. That is why it stays a risk premium.

The competition on my own side is now institutional and reflexive — Ethena-style synthetic dollars
whose backing *is* this trade, which retreat when funding compresses. That is the crowding the
mandate names, and it is why the overlay re-allocates a constant risk budget away from crowded
carry rather than shrinking gross: §1.5 of the thesis — de-risking by size is mechanically undone
by the common risk unit, so composition is the only protection that survives rescaling.

## 6. What would falsify this

**Structural, on the next packet — these are predictions, not hopes.**

- `annualised_turnover` lands in roughly **35–80**. Below ~30 would mean I over-damped and should
  worry about a turnover floor; above ~110 means the slow kernel did not bind and the churn is
  coming from somewhere I have not identified (most likely the risk-unit rescaling or universe
  entry/exit), which is a new diagnosis rather than a reason to smooth harder.
- `gross_edge_bps_per_turnover` rises from 6.66 to **above ~25**. If turnover falls as predicted
  and density does *not* rise roughly proportionally, then gross edge fell with it — meaning the
  premium lives in the fast component of funding and is not harvestable net of cost at all. That
  is a genuine, and for this mandate close to fatal, result.
- `cost_share_of_positive_gross` falls below 1.0 and `triple_cost_annualised_return` turns
  positive. **A book that only survives at 1x is not a book**, so I am treating the 3x number as
  the gate that matters and the 1x number as decoration.
- `median_effective_breadth` rises to roughly 25–35 and both exposure shares stay near 0.50.

**Mechanism-level.** F1 stands as written: if the crowding-adjusted carry spread has an
information ratio below 0.3 *and* a non-monotone sort, the premium is not harvestable here and I
nominate the seed. Note that t01 does **not** trigger F1 — F1 is a statement about the *spread*,
and t01's implied gross Sharpe near 1.4 says the spread exists.

**Honest limitation.** F2 — the requirement that λ > 0 beat a matched λ = 0 book on both the
1st-percentile bar and maximum drawdown — is **untested**. I have exactly one feedback packet and
it contains no crowding overlay. I am carrying the overlay here on the strength of the mandate and
the preregistration, not on evidence, and I am flagging that rather than implying otherwise. The
matched λ = 0 control is the natural next trial, and if the overlay cannot beat it I discard the
overlay as F2 requires.

**What I expect to be wrong about.** The confident part is the arithmetic in §1: cost per unit
turnover and gross edge are measured, not assumed, and the turnover reduction follows from the
kernel by construction. The uncertain part is how much of `G ≈ 14.3%` survives the slowdown. My
prior is that most of it does, because funding regimes persist for weeks; if instead the spread is
concentrated in the newest print, this design converts a costly edge into no edge, and the honest
conclusion will be that the premium in this universe is real but not transportable through a
5.9 bp cost.

## 7. Contract compliance

Reads only `decision_time`, `bars`, `funding`, `eligible_symbols` from `DecisionContext`; the
cross-sectional panel is aligned on the `open_time` **column**, never the positional index, and
the funding rate column is `funding_rate`. Returns a finite `dict[str, float]` keyed on
`eligible_symbols` — every eligible name is named explicitly, with 0.0 for those out of the book,
so no position is carried by omission — or `None` to hold when the panel is too degenerate to
produce a portfolio. `sum(abs(w)) ≤ 1.0`, `abs(sum(w)) ≈ 0` by exact side balancing, `abs(w) ≤ 0.10`
by clipping. Stateless and a pure function of the context: no persistence across decisions, no
RNG, no network, subprocess or filesystem, no `eval`/`exec`/`getattr`, no embedded data, no
absolute dates, no symbol identity, and every quantity is scale-free — ranks, log returns, ratios
— so magnitude-scale and calendar-shift equivariance and exact replay all hold by construction.
Epoch units are normalised before any age arithmetic, so a millisecond timestamp column cannot
silently filter every funding row away and hold a flat book.

**Not verified by execution.** This phase has no shell, so the code has been checked by reading
only. The failure modes I hardened against explicitly are the ones that raise nothing and score as
a book with no edge: positional-index alignment, the wrong funding column, epoch-unit mismatch,
empty-slice NaN paths, and hash-order nondeterminism in the returned mapping.

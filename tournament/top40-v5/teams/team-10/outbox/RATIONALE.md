# team-10 — taker-flow pressure — refinement candidate

**Mandate:** aggressor imbalance as a signal about who is pressing and where the pressure resolves.
**Preregistered thesis:** `lane/scouting/THESIS.md`, sealed 2026-08-26.
**Evidence in hand:** one packet, `t01`, which is the *unmodified organizer seed* — not my signal.

---

## 1. What t01 actually tells me

t01 is the seed, so it carries no information about whether taker flow predicts anything. What it
does carry is a calibration of the machine I have to survive, and that is worth more than a Sharpe.

**The cost rate is recoverable, and two independent routes agree.**

| route | arithmetic | implied cost per unit turnover |
|---|---|---|
| density × cost share | `2.1509 bps × 3.4869` | **7.500 bps** |
| the 1x/3x pair | `ln(1−0.2400) = −0.2744`; `ln(1−0.6434) = −1.0304`; `Δ = 0.7560` over 2 cost units → `0.3780/yr`; `÷ 502.91` | **7.52 bps** |

Both land on **≈7.5 bps charged per unit of turnover at 1x**. Back out the rest:

- gross return ≈ `−0.2744 + 0.3780 = 0.1036` → **≈10.4%/yr gross** on 10.87% realised vol,
  i.e. a **gross Sharpe of about 0.95**;
- cost bill ≈ `502.91 × 7.5 bps` = **37.7%/yr**.

**The seed did not fail for lack of edge. It failed because it traded 503 times a year.** Every
structural gate passed — breadth 24.7, mean gross 1.0, long share 0.5001 vs short 0.4999, active bar
fraction 1.0. The four gates it failed (`turnover_ceiling`, `gross_edge_density`, `cost_share`,
`survives_triple_cost`) are one failure wearing four names: a cost failure.

**This is a design problem, not a parameter problem,** and the phase guidance is right to insist on
the distinction. Write the gate algebraically. With holding period `H` bars, per-name per-bar signed
return `μ`, and gross pinned near 1:

```
turnover T ≈ 2190 / H          density d ≈ μ·H / 2          cost_share = 7.5 bps / d
```

Triple-cost survival needs `d > 22.5 bps`, i.e. `μ·H > 45 bps`. At a *plausible* per-bar per-name
edge of 2–3 bps — an information coefficient under 1% against ~3% bar volatility — that forces
**H ≈ 15–30 bars**. There is no value of `μ` a real 8h flow signal can attain that rescues a book
rebalancing every bar: at `H = 2` you would need `μ = 22 bps` per bar per name, an IC near 0.075,
which my own tripwire §4.2 says I should read as a bug rather than alpha.

**The cost structure of this tournament structurally forbids a fast book at 8h decisions.** That is
the diagnosis. My thesis anticipated it in tripwire §4.5 — *"if the cost model is not binding … taker
fees of ~0.05% per side dominate any plausible 8h edge"* — and t01 proves the cost model is binding
by a factor of 3.5. The tripwire fires. I act on it.

---

## 2. The mechanism, unchanged

Binance publishes `taker_buy_quote_volume` per kline: the exchange's own ledger of which side crossed
the spread. Every taker buy is matched by a maker sell, so

```
imb_t = (2·taker_buy_quote_t − quote_volume_t) / quote_volume_t
```

is an accounting statement — the intermediary sector absorbed `imb_t · quote_volume_t` of unwanted
inventory in that bar, in the direction it was imposed. Unlike the entire equity order-flow-imbalance
literature, which runs on *estimated* trade signs (tick rule, Lee-Ready, BVC), this measurement
carries no classification-error haircut.

The forward payoff of that shock is a **mixture of two components that resolve in opposite
directions**: an immediacy/inventory premium that reverts (the maker did not want the position and is
paid to carry it), and an adverse-selection component that continues (some aggressor flow is
informed, and informed flow does not revert). The unconditional sign is therefore not a constant.
The whole bet is that the mixing weight is observable from fields this dataset contains:

| conditioner | observable | preset sign — **fixed by mechanism, never estimated** |
|---|---|---|
| `none` | — | follow the flow |
| `absorption` | price response per unit flow | high response → informed → follow; low → absorbed → fade |
| `funding` | trailing funding rate | rich → crowded and financed → fade; cheap → fresh → follow |
| `composition` | `log(quote_volume / trade_count)` | large average trade → metaorder → follow; small → crowd → fade |

The 8h bar boundary *is* the funding clock (00:00/08:00/16:00 UTC), which is why funding is the
natural stock variable for this flow signal rather than an unrelated carry cost.

### Who is on the other side

Mechanically, resting limit orders. Economically: professional market makers and HFT desks earning
spread plus the maker-fee advantage; cash-and-carry basis desks structurally short the perp against
spot, harvesting funding, and therefore the natural absorber of taker buy pressure; delta-hedging
desks whose perp leg is a hedge; and funding-carry funds. The aggressor side skews to leveraged
directional traders — retail and momentum-chasing programs — for whom the perpetual is the cheapest
available leverage and who need filling *now*. Binance taker fees (~5 bps) are strictly worse than
maker fees (~2 bps): **anyone appearing in the taker-buy field revealed a preference for speed over
price.** That revealed preference is the economic content of the signal. When I fade the imbalance I
rent balance sheet to an intermediary sector short of capacity and am paid an immediacy premium; when
I follow it I price information the maker sector cannot fully requote against inside 8h and am paid
an information rent. Both are payments from the same leveraged taker.

---

## 3. What the book does

Per decision, entirely from past-only rows, no state carried across calls:

1. **Panel.** Align every eligible symbol on the `open_time` *column* — never the positional
   `RangeIndex` — into one 460-bar cube of `close`, `quote_volume`, `taker_buy_quote_volume`,
   `trade_count`. A symbol needs 130 bars to be held at all.
2. **Flow.** Both declared normalisations: `ratio` = `imb_t`, and `trailing` = flow over a *strictly
   lagged* EWMA of quote volume, the scale-matched fork that avoids multiplying the signal by inverse
   turnover. Zero-volume bars set the flow to exactly 0, never interpolated.
3. **Accumulate and standardise.** `L ∈ {9, 21}` bars, trailing z over `W ∈ {90, 360}` bars,
   min_periods = full window, winsorised at ±3σ.
4. **Condition.** Multiplicative, no gates or thresholds, all four conditioners at equal weight with
   their preset signs; a conditioner that is unobservable for a symbol-bar simply drops out of that
   average rather than voiding the name.
5. **Ensemble.** Equal weight over all `N × L × W` combinations — 8 of them, each carrying the
   4-conditioner average. **There is no selection step anywhere in this file.**
6. **Residualise.** Pooled trailing cross-sectional OLS of the ensemble on the contemporaneous state:
   accumulated standardised return, single-bar standardised return, and log quote volume — all
   per-timestamp demeaned, all observable at the same instant as the signal, no forward return
   anywhere. This is the team falsifier compiled into the book: what trades is only the part of taker
   imbalance that is *not* a restatement of the bar that produced it.
7. **Low-pass.** Exponential filter, 12-bar half-life over a 48-bar window. This is the turnover
   control and it is the one substantive change from the seed's geometry.
8. **Book.** Cross-sectionally demean, winsorise at ±3σ, scale to gross 1.0, clip |w| ≤ 0.10 with
   renormalisation, net ≈ 0 by construction. Every eligible symbol appears explicitly, at 0.0 if not
   held, so exits are stated rather than inferred.

### Why the filter is a cost response and not a hill-climb

I have **no return feedback on my own signal** — t01 is the organizer's book. The half-life was not
chosen against any Sharpe, IC, or drawdown, because I have observed none. It is solved from the cost
constant recovered in §1 and the filter algebra: cascading an `L`-bar boxcar with an exponential of
half-life `h` gives a per-bar relative position change of ≈7–9%, i.e. **annualised turnover of
roughly 50–90 against the seed's 503**, and that is the range where `cost_share` and triple-cost
survival stop being the binding constraints. The lever was picked by arithmetic on an observable that
is independent of returns. I record it as a **fixed** choice, not a searched knob, so my
deflated-Sharpe trial count stays at the preregistered **128**.

Two deviations from §5.1/§5.2, both declared rather than quietly taken:

- **`L ∈ {1, 3}` dropped.** Not on performance — on the §4.5 tripwire, which fired. A book at that
  speed cannot clear a 7.5 bps/turnover charge at any credible `μ`.
- **`X` (cross-sectional treatment) collapses to level 2.** Time-series-z-only cannot satisfy
  `|net| ≤ 0.25` or the both-sides-used gate as a standalone book; it would be clipped into something
  I did not design. Structural, not a preference.

Everything else holds: preset signs, symmetric buy/sell treatment, one parameter set for the whole
universe, no per-symbol tuning, no volatility targeting (the organizer owns the risk unit), no
thresholds, no stop-losses, and the conditioner forms as written.

Nomination rule §5.4 said: equal-weight every configuration that passes F1/F2/F3. **The feedback
packet reports no IC, no residualised IC, and no sign-stability split, so F1/F2/F3 are not evaluable
with the evidence I have.** The only non-selective reading of my own commitment is therefore to
nominate the *whole* surface at equal weight. Subsetting it on anything else would be the
pick-the-best-backtest step my preregistration exists to delete.

---

## 4. What would falsify this

Stated before the packet, so the next reading is a test and not a search.

**Predicted metrics.** `annualised_turnover` 40–110 (design point ≈65); `mean_gross_exposure` ≈1.0;
`median_effective_breadth` 25–40; long/short exposure share ≈50/50; `active_bar_fraction` ≈1.0.

- **If turnover comes back above ~150**, my filter algebra is wrong. That is a structural fix — more
  low-pass, or a slower accumulation — not a reason to touch the signal.
- **If turnover lands in band but `gross_edge_bps_per_turnover` is below ~5 bps**, the residualised
  flow signal has no per-trade edge at this horizon. That is F1 and F2 failing in substance: taker
  imbalance at 8h is spanned by the price-volume state, exactly as the closest horizon-matched
  published result warns. **I nominate the unmodified seed and report the mandate falsified.** I do
  not flip the sign and re-submit — the signs are preset by mechanism, and a preferred opposite sign
  falsifies the thesis rather than parameterising it.
- **If the book earns at a rate consistent with a sign error** — meaningfully negative net return
  with turnover in band and density materially non-zero — that is the same falsification with the
  opposite arithmetic, and it gets the same answer.
- **If `median_effective_breadth` collapses or one side of the book empties**, it is not a portfolio
  and it is not a marginal candidate.
- **If density looks implausibly good** — residualised performance implying |IC| > 0.10 at 8h on a
  public field — tripwire §4.2 says my first hypothesis is lookahead, and I audit before nominating.

The honest summary of the risk: I have moved the effective holding period to roughly 1–2 weeks
because the cost model leaves no alternative, while the evidence closest to my horizon locates the
taker-imbalance effect at 4–12 hours. The conditioners and the residualisation are the reason to
think something survives the aggregation. If nothing does, the mandate is falsified on visible data,
and retiring to the seed is a result rather than a forfeit.

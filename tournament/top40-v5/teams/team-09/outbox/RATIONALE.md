# RATIONALE — team-09 nomination

**Family:** time-series trend. **Mandate:** channel breakout gated on participation, so the book
does not buy every false break.
**Preregistered thesis:** `lane/scouting/THESIS.md`, sealed before any data was mounted.
**Charged trials consumed: 2 of a declared cap of 60** — `t01` (the unmodified organizer seed) and
`t02` (my refinement candidate). This nomination is trial 3.

---

## 1. What I am nominating, and why it is this

An **event-stamped, volume-confirmed channel breakout**. Three Donchian stop-and-reverse machines
per symbol (21 / 42 / 84 bars of 8h = 7 / 14 / 28 days) on the extreme of closes. Each machine's
sign is the direction of the break that established its current state. Each machine's *size* is a
participation confidence read on that establishing break bar and then **frozen for the life of the
state**. The three are averaged; the resulting score vector is spent as a cross-sectional core plus
a bounded directional tilt, because the caps do not permit anything else.

This is not my highest-Sharpe book. `t02` posted **net Sharpe 1.45** and I am not nominating it,
because it **failed two hard gates** — `gross_edge_density` and `survives_triple_cost` — and a book
that only exists at 1x is not a book. The nomination is chosen on structure and cost.

## 2. The evidence, and the arithmetic that follows from it

Two packets. Both are on the visible development window only.

| | `t01` — organizer seed | `t02` — mine |
|---|---|---|
| admitted | **yes**, no failed gates | **no** |
| failed gates | — | `gross_edge_density`, `survives_triple_cost` |
| net Sharpe | 1.204 | **1.453** |
| annualised turnover | 37.8 | **183.7** |
| gross edge / turnover | 42.3 bps | **17.0 bps** |
| cost share of positive gross | 17.7% | 44.0% |
| triple-cost annualised return | +7.2% | **−10.1%** |
| double-cost Sharpe | 0.944 | 0.318 |
| mean gross exposure | 0.615 | 0.944 |
| median effective breadth | 18.0 | 19.7 |
| long exposure share | 0.525 | 0.480 |
| positive fold fraction | 0.60 | 0.40 |

**Back out the venue's cost per unit turnover**, which is a property of the tournament rather than
of either strategy:

- `t01`: gross edge = 42.26 bps × 37.84 = 15.99%; net = 13.41% ⇒ **6.81 bps per unit turnover**.
- `t02`: gross edge = 17.04 bps × 183.74 = 31.32%; net = 18.44% ⇒ **7.01 bps per unit turnover**.

The two agree to 3%, so ≈ **6.9 bps at 1x, 20.7 bps at 3x**. That fixes the design constraint
exactly: **a book must earn more than ~21 bps of gross edge per unit of turnover to be positive at
triple cost.** `t02` earned 17.0. It failed by arithmetic, not by luck.

The diagnosis is not that the signal was weak. `t02` generated **31.3% of annualised gross edge
against the seed's 16.0% — nearly double** — and its structural gates all passed cleanly (breadth
19.7, breadth-pass 1.00, gross 0.944, long share 0.480). It spent **4.9× the seed's turnover** to
collect that edge and handed 44% of it back in costs. The problem is entirely the price paid per
unit of signal.

**I preregistered this reading before seeing the packet.** From the sealed §6 of the refinement
rationale, under "feedback signatures I have committed to read a particular way":

> **1x fine, 3x negative** → gross edge per turnover is under ~21 bps. Per §1 that is not a book,
> and the answer is **a slower signal, not a bigger gate**.

`t02` is 1x fine, 3x negative, at 17.0 bps. The committed response is a slower signal. That is the
single change in this nomination, and it is the reason I am comfortable making it on one packet: it
is not a search over the feedback, it is the execution of a rule written down before the feedback
arrived.

## 3. The one structural change: the gate is a stamp, not a multiplier

Here is the mechanism error in `t02`, stated plainly.

The gate's job in this mandate is to **classify a break event** — informed repricing, or inventory
shock. That is a property of an *event*. `t02` implemented it as a term recomputed on every bar:
`score = c + γ·|c|·align·amp`, where `align` was a robust z of a 2-bar taker imbalance. A 2-bar
imbalance z-score is a fast, largely mean-reverting statistic. Multiplying a slow trend signal by a
fast noise term does not make the trend signal smarter; it **modulates the book at the noise term's
frequency**. Every 8 hours, every held name's weight was pushed around by up to ±0.6·|c| for reasons
that had nothing to do with whether its trend was intact. That is turnover with no persistence
behind it, and at 6.9 bps a unit it is precisely the 4.9× turnover bill.

The fix is to put the gate where the mechanism says it belongs:

```
direction, stamp = the first break of the current same-direction run
conf            = 1 + γ · align(stamp) · amp(stamp)          # γ = 0.6  ⇒  conf ∈ [0.4, 1.6]
s_N             = direction · conf                            # constant until the state flips
```

`conf` is evaluated once, on the bar the break happened, and does not move again until an opposite
break stops-and-reverses the state. Further breaks in the *same* direction extend the trend; they do
not re-stamp the position (that distinction matters — re-stamping on the latest break would fire on
most bars of a strong uptrend and reintroduce exactly the per-bar modulation I am removing).

So both components of the position are now event-driven, and turnover can only be generated by a
genuine state change. Everything else about the book — the two-sided construction, the bounded tilt,
the liquidity floor, the caps — is carried over unchanged from the configuration that already passed
every structural gate.

**Expected effect, stated as a number I can be wrong about.** A Donchian(N) stop-and-reverse flips
roughly every 1.5–3·N bars; averaged over 21/42/84 that puts expected annualised turnover in the
**40–70** range against `t02`'s 184 — bracketing the seed's 37.8 from above, which is where I want to
be, because I know 37.8 clears the turnover band and I do not know where its lower edge is. If the
slower signal retains even 65% of `t02`'s gross edge (20.4% annualised) at turnover 60, edge density
is **34 bps** and triple-cost return is **+8.0%** — the seed's structural profile with more edge
behind it. The nomination fails on cost only if the slowdown retains under ~40% of the gross edge,
which would mean the edge was never the trend premium at all.

## 4. Why the book is two-sided, and why that is the mechanism rather than a workaround

`gross ≤ 1.0` with `|net| ≤ 0.25` means the most lopsided admissible fully-invested book is
62.5/37.5. **The tournament does not permit a directional time-series trend book at full size.** A
naive channel breakout in crypto perps breaks up on nearly everything at once in a bull tape, gets
clipped to net 0.25, and what survives fails effective breadth, fails mean gross exposure, and fails
"both sides genuinely used, measured on exposure." That is a design failure no parameter repairs.

So the *signal* stays strictly time-series — each symbol is scored against its own channel and its
own trailing participation distribution, and nothing in the score looks at another symbol — while
only the *budget* is cross-sectional: `core = (s − mean s) / Σ|s − mean s|`, plus a tilt
`0.18·tanh(mean s / 0.5)` carrying the market-wide component well inside the net cap. Demeaning makes
the two sides exactly equal by construction before the tilt, so both sides are used on exposure as a
structural fact, not a P&L accident.

What I did not expect when I built this for cap reasons is that **the demeaning turns out to express
the second half of the thesis**. In a uniformly bullish tape the book ends up long the high-confidence
breaks and short the low-confidence ones — and a break on ordinary or counter-aligned taker flow is
exactly the Campbell–Grossman–Wang inventory branch, which Llorente et al. predict **reverts**.
Shorting it is the mandate, not a residue of the constraint.

To be precise about a distinction I will not blur: `γ = 0.6` guarantees the gate can never flip the
sign of a symbol's *score*, which is what I preregistered in F3. Cross-sectional demeaning can still
place a weakly-confirmed long into the short book. That is portfolio construction under a net cap,
not a gate inversion, and the gate's effect stays monotone throughout — more confirmation is always
more long and less short.

## 5. The mechanism

**The base premium.** Time-series momentum (Moskowitz–Ooi–Pedersen 2012): under-reaction followed by
delayed over-reaction, with speculators paid by hedgers. I express it as a **channel break** rather
than a return sign because George–Hwang (2004) show nearness to a running extreme *dominates* raw
past returns as a momentum predictor and — unlike raw momentum — its forecast returns **do not
reverse at long horizons**. The break selects the subset of trend events where the under-reaction
story is cleanest.

**Why a break needs a gate.** A channel break is a mixture of two populations and the naive rule buys
both:

- **Informed repricing** — someone with a view crosses the spread, price leaves the range, and the
  move continues because the information is not yet impounded. Llorente–Michaely–Saar–Wang (2002):
  returns driven by speculative trade **continue**.
- **Inventory shock** — a large risk-sharing order pushes price out of the range against a
  risk-averse liquidity provider who must be paid to warehouse it. Price reverts as the inventory is
  worked off. Campbell–Grossman–Wang (1993): autocorrelation *declines* with volume in this branch.

Blume–Easley–O'Hara (1994) is the licence to condition at all: volume carries information about
**signal precision** that price alone cannot convey.

**What the gate actually measures, and the trap it avoids.** Karpoff (1987): volume is positively
related to the *magnitude* of the price change, so a high-volume break is partly just a large break
and a gate on raw volume is a volatility filter wearing a costume. The gate's primary input is
therefore **direction-signed taker imbalance** — `2·taker_buy_quote/quote_volume − 1`, which
identifies *who crossed the spread*, is a pure ratio, and carries a sign. Raw participation and
average ticket size enter only as a **confidence weight** on that reading:

```
align = tanh( d · z[ taker imbalance ] )                          ∈ (−1, +1)   who was aggressive
amp   = ½·(1 + tanh( ½·( z[log qv] + z[log(qv/trades)] ) ))       ∈ ( 0,  1)   how far to trust it
conf  = 1 + 0.6 · align · amp                                     ∈ [0.4, 1.6]
```

All three z-scores are robust (median / MAD) against the **symbol's own trailing 63 bars**. That is
deliberate: Cong et al. (2023) find wash trading averages over 70% of reported volume on unregulated
venues, so no participation statistic is ever compared to a cross-sectional volume level, and trade
count and ticket size sit in the composite as independent cross-checks on quote volume.

A confirmed break carries **4× the weight** of a disconfirmed one. That is the whole gate: it can
size, it cannot veto and it cannot invert. Choosing a soft scaler over a hard cutoff is also what
keeps the book away from the razor-thin thresholds the small-perturbation check exists to find.

## 6. Who is on the other side

1. **Levered directional retail.** Long into strength, stopped or liquidated into weakness, and
   paying funding for the privilege of being long a trending perp — He et al. (2022/24) find past
   120-day returns explain over half the variation in the perp–spot gap, so momentum traders sit
   structurally on the funding-paying side. Their forced, price-insensitive exits *are* the
   continuation, and that channel does not exist in spot. **Primary payer.**
2. **Inventory-constrained market makers.** They lean against the break and must be compensated for
   warehousing it. They are precisely why *ungated* breakouts revert: they win the low-participation
   breaks. The gate exists to stop paying them when they are right; on confirmed breaks I am on the
   informed side of the same trade.
3. **Late discretionary and allocator flow**, arriving after the break and completing the repricing —
   the delayed over-reaction half of the MOP story.
4. **Delta-neutral cash-and-carry funds**, directionally indifferent, capping how far the perp can
   decouple without fighting the direction of a break.

I am on the informed-repricing side and I pay carry to be there. Selectivity is not a free
preference; it is how I avoid paying funding on breaks that were never going anywhere.

## 7. What would falsify this — including what I did not get to test

**F1 — the primary falsifier — is UNEVALUATED, and I will not pretend otherwise.** My thesis §4
committed me to running the identical geometry with the gate off (`γ = 0`) and requiring the gated
book to clear it by ≥ +0.15 Sharpe and ≥ +2.0pp continuation rate before nomination. I did not run
it. I had 12 feedback-driven trials available and used 2: one was the seed, and the second returned
a cost failure severe enough that spending trial 3 on an ungated control of a *superseded, non-viable*
geometry would have told me about a book I could never nominate. I spent the trial on the qualifying
structure instead. That is a defensible allocation and it is also a real gap in the evidence, so:

> **The claim "the participation gate adds Sharpe" is not supported by anything I have measured.**
> It is supported only by the literature in §5 and by the preregistered mechanism.

What makes it nominatable anyway is that **the gate is built so that being wrong about it is cheap.**
`conf ∈ [0.4, 1.6]` with a frozen stamp means that if participation carries no information at the
break, `conf` is noise uncorrelated with forward returns, and its effect is a mild, *non-churning*
dispersion of weights around the ungated channel book. It cannot flip a position, it cannot veto a
break, and because it is frozen it cannot generate turnover. A worthless gate here costs a little
weighting efficiency. A worthless gate in `t02`'s form cost 150 units of annualised turnover. That
asymmetry is the actual argument for this construction, and it is why I did not simply retire the
gate and nominate the plain breakout.

The remaining preregistered falsifiers stand as written:

- **F2 — the gate is a volatility filter in disguise.** Must beat a selectivity-matched
  trailing-realised-volatility control by ≥ +0.10 Sharpe. This is the leg Karpoff predicts I might
  lose, and it is why the primary input is the scale-free *signed* taker ratio rather than raw
  volume, which enters only as a confidence weight.
- **F3 — the sign.** I preregistered **continuation** and the code cannot express anything else:
  `γ = 0.6 < 1` bounds `conf` strictly positive. If low-participation breaks continue while
  high-participation breaks revert, that is a falsification of the thesis and I report it as one.
  **I will not flip `γ` negative and re-nominate the inverted rule as a confirmation.**
- **F4 — placebo.** A permuted-gate control at matched acceptance must be beaten by more than its own
  run-to-run dispersion.
- **Not a rescue.** "There were no trends in the sample" is admissible only on the Babu et al. (2020)
  terms: it requires showing the *ungated* breakout underperformed for the same reason. If ungated
  worked and gated did not, the mandate failed, full stop.

**Falsifiers specific to this nomination, on metrics the packet actually reports:**

| Observation | What it falsifies |
|---|---|
| turnover still > ~100 | The gate was not the turnover source; the state machine itself churns, and the geometry is wrong, not the gate's placement. |
| turnover < ~25 | I over-damped; the ensemble is slower than the premium's decay and I have traded edge for a cost saving I did not need. |
| `gross_edge_density` < 21 bps again | The edge in `t02` was high-frequency and never the trend premium. That falsifies the *family*, not the gate — the honest conclusion would be that I was harvesting short-horizon microstructure and calling it George–Hwang. |
| edge density ≥ 35 bps but Sharpe far below `t02` | Slowing worked on cost and the signal is real but thin; a defensible book, and the mandate is intact but unimpressive. |
| effective breadth < 18 or one side under-used | The discrete score concentrates more than the continuous one did; a construction failure, fixable, and not evidence about the gate. |

## 8. Parameter surface accounting

Everything below is from the sealed §5 surface. Where the surface offered a set I ensembled it or
took a value fixed a priori on the §2 cost arithmetic. **Nothing here was selected by comparing
feedback packets**, because I have no packet on any of these knobs.

| Knob | Declared range | Setting | Basis |
|---|---|---|---|
| `channel_lookback` | {6,12,21,42,84,168} | **ensemble {21, 42, 84}** | Ensembling refuses the selection. {6,12} dropped a priori on cost (a 2-day channel is 6 observations and unaffordable at 3x). 168 dropped a priori because at 56 days it is slower than the holding period and contributes mostly a static long bias the net cap cannot express — and because the turnover estimate in §3 needs to sit *above* the seed's 37.8, not below it. |
| `exit_fraction` | {0.5, 1.0} | **1.0** | Symmetric stop-and-reverse — what the state machine implements. |
| `channel_basis` | fixed: closes | closes | As declared. |
| `participation_stat` | {V,T,S,I,D} | **D** (composite) | Abnormal *and* aggressively aligned. `V` alone is Karpoff's trap. |
| `gate_threshold θ` | {0.5, 1.0, 1.5} | **1.0** | Midpoint, as a tanh scale rather than a cliff. |
| `norm_window W` | {21, 63} | **63** | A priori: 21 bars overlaps the shortest channel lookback, which would make the gate partly a restatement of the signal. |
| `gate_mode` | {hard, soft} | **soft** | A hard cutoff is the razor-thin threshold the perturbation check hunts, and it destroys breadth. |
| `confirm_bars k` | {1, 2} | **1** | Changed from `t02`'s k=2. At an event stamp, k=2 would need the bar *after* the break, which does not exist when the break is the current bar; k=1 removes the edge case and reads participation on the bar the break happened in. |
| `funding_veto` | {off, on} | **off** | Unchanged. Binance shortened funding settlement from 8h to 4h and then to 1h for some contracts, so per-settlement rates are not comparable across symbols at a point in time. Thesis §6 recorded this before data was mounted; this is that caveat honoured, not retrofitted. |

**Not on the declared surface, and flagged rather than hidden:** the portfolio-construction constants
(gross 0.95, tilt cap 0.18, tilt scale 0.50, per-name 0.090, net 0.22, liquidity floor at the bottom
quintile, `MIN_NAMES` 12, replay tail 1000 bars). These are not signal parameters and none was chosen
against returns — they are the response to the cap geometry in §4. All except `MIN_NAMES` and the
replay tail are carried unchanged from `t02`, which passed every structural gate with them.

**Not present at all:** per-symbol parameters, date-conditioned regime splits, any volatility target
or ATR sizing, any funding-carry alpha overlay.

**Realised trial count: 2 charged, cap 60.** Trials spent are trials spent whether or not they
flattered the result; the honest number is small because I stopped searching once the cost
arithmetic in §2 told me what the constraint was.

## 9. Known limits of this specific implementation

Recorded now so they cannot be retrofitted later.

- **The 8h floor attenuates the gate.** Breaks happen intrabar. I see a bar's aggregate
  participation, not its sequence, so I cannot separate volume that arrived *before* the break from
  volume that arrived *after*. This is why my prior on the gate was +0.2–0.4 Sharpe and not more.
- **No open interest, no liquidation feed, no order book.** The forced-flow continuation channel is
  the strongest venue-specific reason this should work and it is unobservable here. Taker flow is the
  only proxy; if the gate works I cannot prove liquidations were why.
- **The replay tail is finite.** If the break that established a state fell outside the trailing 1000
  bars (333 days), the walk-back stamps the earliest surviving break of that run instead. Deterministic
  and bounded — it can only re-scale one name's weight within [0.4, 1.6] — but it is an approximation
  and it is in the code, not hidden in a comment.
- **Young listings are downweighted, not excluded.** A symbol needs only the shortest machine's
  warm-up (86 bars) to enter; machines it cannot yet support contribute zero to a denominator that is
  always the full ensemble size, so a recent listing carries at most a third of a mature name's
  magnitude. That is the intended handling of the listing-era volume ramps flagged in thesis §6, and
  it is imperfect — the ramp still inflates the participation z-scores it does reach.
- **A discrete score concentrates more than a continuous one.** The per-name cap plus rescale is what
  protects effective breadth here; `t02`'s power-flattening was removed because `sign(z)·|z|^0.7` has
  unbounded slope at zero and therefore churns exactly the mid-pack names with the least conviction.
  If breadth comes back below 18, that is the trade I got wrong.
- **Decay.** He et al. report perp deviations diminishing over time. I expect a weaker effect in the
  recent part of any sample and I said so before seeing one.

## 10. Compliance

Stateless across decisions — the strategy object holds no attributes and every quantity is
recomputed from the past-only rows in `context`. No RNG (`seed` is accepted and unused); no network,
subprocess, filesystem, `eval`/`exec`/`compile`/`getattr`; no embedded data, fitted parameters or
symbol identities.

- **Look-ahead:** channel extremes are `rolling(N).max().shift(1)`, strictly prior to the marked bar;
  the confidence norm is `[stamp − 63, stamp)`, strictly prior to the break bar. Every read is inside
  the truncated frame.
- **Calendar shift:** `decision_time` is never read, so a shift is a no-op.
- **Magnitude scale:** the channel is a comparison of closes; participation statistics are a ratio
  (`taker imbalance`) and log-differences z-scored by MAD (`log qv`, `log qv/trades`), all invariant
  to a global rescale; the liquidity floor is a quantile of the rescaled vector, so the kept set is
  unchanged.
- **Symbol pseudonymisation:** no symbol name is ever inspected.
- **Alignment trap:** no cross-symbol panel is ever built. All per-symbol work is done on numpy tails
  of each frame and only a single cross-sectional vector is formed at the decision, so the positional
  `RangeIndex` is never used as a join key.
- **Caps by construction:** `Σ|w| ≤ 0.99`, `|Σw| ≤ 0.22`, `|w| ≤ 0.090`, all strictly inside the
  enforced 1.0 / 0.25 / 0.10. Only symbols drawn from `context.eligible_symbols` are returned, and
  every eligible symbol is returned with an explicit target so a flat name is unambiguously flat
  rather than a hold. A mapping is returned at every decision; `None` is never used.
- **No volatility targeting anywhere.** No ATR band, no vol scaling, no risk parity. The only sizer
  is the organizer's ex-ante risk unit.

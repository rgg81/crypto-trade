# team-13 — Discovery candidate: inclusion event, crowding state

**Family:** event and state · **Mandate:** universe inclusion and attention — trade weekly
membership entry and exit · **Thesis:** `lane/scouting/THESIS.md` (sealed 2026-08-26)

This is the discovery baseline. It is deliberately the *honest simple* expression of the thesis, not
a clever one: one event definition, one state variable, one sign, one portfolio rule. If it works I
want to know which of those four is doing the work, and if it fails I want to be able to say which
one broke.

---

## 1. The mechanism

The mandate is *event and state*. The book keeps those two jobs strictly separate:

| | job | what it is |
|---|---|---|
| **Event** | chooses *who is in the book* | weekly liquidity-rank transition (entry and exit) |
| **State** | chooses *the sign and the size* | crowdedness of leveraged positioning |

**The event.** A weekly liquidity-ranked universe is a published, forecastable, synchronized demand
schedule (thesis §1.1). When a symbol crosses the inclusion threshold, mechanical buyers must own it
in the same week; when it falls out, mechanical holders must not, and on this venue falling out of a
volume ranking is positively correlated with an actual Binance USD-M delisting with a hard
auto-settlement clock ([C11]). Crucially, entry in crypto is *endogenous to attention*: a symbol
enters because its turnover just surged relative to peers. That makes membership entry a dated,
observable attention shock, which is exactly Barber & Odean's trigger set — abnormal volume plus
extreme recent return ([C3]).

The book reconstructs that transition from bars alone, two ways:

- **Rank crossing.** Percentile rank of trailing-week per-bar notional, minus the same symbol's
  percentile rank over the three weeks before that. Positive = climbing into the universe.
  Negative = falling out of it. This is thesis knob 5(ii) — the self-computed trailing-dollar-volume
  rank-crossing proxy — and it is used at every decision rather than only on the observed
  membership date, because [C7] says a transparent rule pushes the move into the anticipation
  window.
- **Listing recency.** A symbol whose history is short relative to the horizon is a fresh member by
  construction — the purest entrant there is. Its event weight decays linearly to zero over three
  weeks. `RULES.md` states directly that history length varies by symbol; this channel is the one
  membership signal that is *unambiguous* rather than proxied.

Event intensity is `max(|rank change|, recency)`, converted to a percentile rank, then passed
through a smooth top-half gate `((pr − 0.5)·2)²`. Names at the median get zero weight *and* zero
derivative, so nothing sits on a threshold a perturbation could flip.

**The state.** An unconditional "buy the entrant" book is a bet that inclusion has one sign. The
evidence says it does not, and says so most sharply on the venue I trade: after outlier control,
Binance listings delivered roughly **0%** five-day outperformance against ~29% for Coinbase ([C6]),
and Zaremba et al. find crypto reversal is conditional on liquidity — the illiquid majority reverses
while the largest names show momentum ([C4]). So the sign has to come from somewhere else.

It comes from crowding: an equal-weight composite of (i) the trailing-week mean funding rate and
(ii) taker-buy aggressor skew, each standardised cross-sectionally by median/MAD and clipped at ±3.
Funding is the *price of leverage* — a name whose volume surge arrives with the crowd paying to be
long is an attention-driven demand shock that must unwind; a surge arriving with flat or negative
funding and two-sided taker flow is genuine liquidity migration.

**The sign, committed before any data (thesis §1.2, bound by falsifier F4): short the crowded side
of a transition, long the uncrowded side.**

**Why one function covers both legs.** An entrant is an excess-*demand* shock — if the crowd is
levered long, fade it. A leaver is an excess-*supply* shock — forced closers sell, funding turns
negative, so buy it. "Short the crowded side" therefore produces the entrant/leaver mirror *from the
state*, without a hand-flipped sign anywhere in the code. That is a stronger claim than symmetry by
construction, and it is separately falsifiable (§4).

**Why this can survive on perps when it died in equities.** Greenwood & Sammon show the S&P index
effect collapsed from 7.6% to 0.8% ([C1]) — that is the base rate this thesis must beat. Three
things are structurally different here: an alt USD-M perp is the limiting case of Wurgler &
Zhuravskaya's no-close-substitute stock ([C2]), with no ETF, no creation/redemption and no basket
hedge, which is precisely where they predict the residual effect is largest; the short leg has no
borrow constraint, so the deletion leg is not throttled the way it is in equities; and **the
reversal trade and the carry trade are the same trade** — shorting a crowded entrant means
*receiving* funding every 8h ([C10]).

---

## 2. Who is on the other side

- **Leveraged retail directional traders on Binance Futures**, selecting off volume- and
  gainer-ranked tables. Barber & Odean's attention buyers at 10–50× leverage. Primary counterparty
  on the crowded-entrant short.
- **Copy-trading followers**, who synchronize and deepen that flow.
- **Other systematic managers running the same trailing-dollar-volume screen** — every rules-based
  crypto index screens on trailing liquidity ([C12]), so many books add the same name in the same
  window. The crypto Russell reconstitution.
- **Token treasuries and unlock recipients** distributing supply into attention — the natural
  sellers who appear once a name is finally liquid enough to sell into.
- **Forced closers at delisting**, facing scheduled auto-settlement and restricted order types
  ([C11]).

I am selling immediacy to the first three at the moment they most demand it, buying it from the last
two at the moment they least can wait, and being paid funding for the privilege.

**What I am paid for.** Binance caps funding at 0.75 × maintenance margin ratio ([C10]), so my
compensation is bounded while a squeeze is not. This is a negative-skew liquidity-provision trade in
the least-substitutable, highest-idiosyncratic-vol instruments on the venue. Madhavan says the same
thing about Russell reconstitution: supplying immediacy is profitable but undiversified, costly, and
price-risky on unwind ([C7]). That is not a flaw in the thesis — it is the identity of the premium.

---

## 3. Portfolio construction

Scores are `event × (−crowding)`, cross-sectionally demeaned over the selected names (so both sides
are genuinely used *on exposure*, not just on P&L), water-filled to gross 0.98 with no line above
0.08, then net-capped at 0.15. Hard limits are 1.0 / 0.10 / 0.25, so every constraint has headroom.
The 0.08 line cap is below the 0.10 limit specifically to force breadth: the book needs ≥ 13 names
to reach target gross, and with a smooth event gate it typically holds several dozen.

**I do not target volatility anywhere.** Cross-sectional standardisation of funding and taker skew
is *measurement of a cross-section*, not a risk target; the common ex-ante risk unit is the
organizer's and this book does not touch it.

**Deliberate protocol care.** `RULES.md` warns that reading a field that does not exist produces a
flat book that scores as "no edge" rather than "never ran". So: every column access is guarded with
a fallback (`quote_volume` → `close × volume`; `taker_buy_quote_volume` → `taker_buy_volume`); the
funding rate column is `funding_rate`, not `last_funding_rate`; funding history is taken as a per
symbol *tail count* rather than a timestamp filter, so no dtype or absolute-date assumption is made;
and **the bar frequency is inferred from index spacing rather than assumed** — every window here is
expressed in weeks, so a wrong step size would silently mis-scale every lookback. Missing state
values score zero rather than dropping the name.

The book is a pure function of `DecisionContext`. No persistent state, no RNG, no absolute dates, no
symbol literals, no price levels — only ranks, ratios and rates, which is what makes the
pseudonymisation, calendar-shift and magnitude-scale checks pass by construction rather than by luck.

---

## 4. What would falsify this

The thesis falsifiers (§3, sealed) stand. Restated against *this* book:

**F1 — the mandate's falsifier.** *If entrants and leavers show no abnormal return around their
membership change, inclusion carries no attention effect.* Operationally: pooled cumulative
normalized abnormal return over the three weeks strictly after the transition, entrant minus leaver,
clustered by reconstitution week. **Falsified at |t| < 2.0, or if the spread is smaller than a
round-trip cost estimate for these names** — entrants and leavers are by construction the
highest-spread names in the universe, which is why the magnitude clause is there. If F1 fires the
event leg is dead and I will say so; I will not widen the window or add event types until something
clears 2.0.

**F2 — the state claim.** If the high-crowding-minus-low-crowding entrant spread has |t| < 2.0, the
state conditioning failed. I then fall back to the unconditional event, *labelled as such*.

**F3 — the unseasoned-universe rerun.** The mandate demands I prove this rather than die of it, so
the prediction is committed: **the effect should be at least as strong in an unseasoned universe,
not weaker** — it contains more entrants, younger entrants, and more extreme attention shocks.
**Falsified if the pooled F1 t-statistic falls below half its development value, or inverts.** Either
outcome means the seasoned result was a survivorship artifact.

**F4 — sign integrity.** If development data shows the opposite sign, that is a falsification of the
mechanism, not a parameter to flip. Any book trading the inverted sign is post-hoc and will be
reported as such.

**This candidate specifically is falsified if** the event gate does no work — i.e. if replacing
`event` with a constant leaves performance unchanged. That would mean I have written a
funding-carry book with decoration, not an inclusion book, and it is the single most important
diagnostic to run on the returning packet.

---

## 5. Known failure modes, preregistered

1. **Structural-carry contamination.** Cross-sectional funding *level* is persistent; some alts
   always pay. The event gate is what is supposed to prevent this from becoming a carry book, and
   the constant-event ablation above is the test. If it fails, the phase-2 fix is to demean funding
   against each symbol's own trailing history so the signal is a crowding *shock*, not a level.
2. **Momentum crash on the short leg.** [C8]: attention shocks persist 1–2 weeks. Shorting a crowded
   entrant during a genuine bull leg, with capped funding compensation against an uncapped squeeze,
   is the single most likely way this book dies.
3. **Cost.** Entrants and leavers are the thinnest names available. The effect can be entirely real
   and still not clear 3× costs.
4. **Participation truncation.** The leaver leg is low-liquidity by construction; if participation
   caps bite asymmetrically, the book drifts long and the both-sides-used gate suffers. The 10%
   of-median liquidity floor is the only mitigation in this version, and it is a blunt one.
5. **Wash-traded volume.** [C9]: fabricated volume improves rankings, so a rank crossing can be an
   artifact. Diagnostic available in-dataset (quote volume vs `trade_count`); not used here.
6. **Funding-cap saturation.** [C10]: funding pins to its cap in the most crowded names — the
   crowding proxy is censored exactly where the signal should be strongest.
7. **Decay with arriving capital.** [C1] is the base rate. A monotone decline in effect size across
   the sample is the modal outcome for this family and will be reported as a half-sample split, not
   presented as a surprise.
8. **Thin event count.** The effective sample for F1 is the number of reconstitution weeks, not the
   number of symbol-events.

---

## 6. Search accounting

Declared surface: **N = 48** configurations (thesis §4.2). This candidate fixes one point on it:

| knob | value here | grid |
|---|---|---|
| `H` post-event horizon | 3 weeks | 1, 2, 3 |
| `L_z` crowding lookback | 21 bars (1 week) | 21, 63 |
| `θ` crowding threshold | not applicable — continuous score, no cut | 0.5, 1.0 |
| `S` state variable | funding + taker-imbalance composite | funding alone; composite |
| `A` anticipation offset | −21 bars (self-computed rank crossing) | 0; −21 |

Trial 1 is the unmodified organizer seed and is not part of the 48. Deflation will be reported
against the declared 48 regardless of how many I actually evaluate — declaring a surface and then
claiming credit for under-searching it is the same overfitting in a different costume. Nothing
outside the surface will be evaluated without declaring the excess and adding it to N first.

A falsified thesis is a result. Retiring honestly remains available.

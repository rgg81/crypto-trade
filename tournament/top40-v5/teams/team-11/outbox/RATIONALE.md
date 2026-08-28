# team-11 nomination — participant mix via average trade size

**Family:** microstructure and participation · **Mandate:** average trade size as a
retail-versus-institutional proxy · **Sealed thesis:** `lane/scouting/THESIS.md` (2026-08-26)

---

## 0. The headline, stated before anything that could soften it

**My own primary packet-falsifier fired.** In `refinement-RATIONALE.md` §7 I wrote, before seeing
t02: *"`gross_edge_bps_per_turnover ≤ 0`. The mechanism produced no gross edge at a 3-day horizon.
This is the primary falsifier and it is not rescuable by re-tuning `m` or `M`."*

t02 returned **`gross_edge_bps_per_turnover = −7.458`**.

I am nominating anyway, and this section says exactly what that does and does not claim. **I have
not demonstrated an edge.** What I have is one measurement whose point estimate is the wrong sign
and whose standard error swamps it, a mechanism I still believe, and a structural chassis that
demonstrably clears every gate that is not about edge. A reader who scores this lane on
*"did they show the mandate predicts returns"* should score it zero. I would rather write that
sentence than bury it.

---

## 1. What the two packets actually measured

`t01` is the unmodified organizer seed and carries no information about my mandate. It priced the
cost environment. `t02` is the one and only measurement of my own mechanism.

| quantity | derivation from t02 | value |
|---|---|---|
| cost at 1× | `(−0.06295 − (−0.11805)) / 2` | **2.755 % of capital / yr** |
| cost per unit one-way turnover | `0.02755 / 40.346` | **6.83 bps** |
| gross price edge | `−7.4582 bps × 40.346` | **−3.009 % / yr** |
| funding + residual | `−6.295 + 3.009 + 2.755` | **−0.53 % / yr** |
| gross Sharpe | `−3.009 / 9.888` | **−0.304** |
| **t-statistic over 808 days** | `−0.304 × √2.213` | **−0.45** |

That last row is the whole decision. **The mechanism did not produce a negative edge; it produced
no measurable edge.** A gross Sharpe of −0.30 ± 0.67 is a coin landing slightly off-centre once.
`positive_fold_fraction = 0.4` says the same thing in a different currency: two of five folds
positive, which is what noise looks like.

Two further readings, both preregistered before the packet:

- **The structural chassis works.** t02 passed `turnover_ceiling` (266.6 → 40.3), breadth
  (median 30.0, pass fraction 1.0), mean gross (0.995), two-sidedness on exposure
  (0.4994 / 0.5006), participation, and `active_bar_fraction` 0.9975 — which also confirms that
  returning `None` is scored as *holding*, not as non-participation. Falsifiers 3 and 4 of
  §7 did not fire: turnover landed inside my predicted 25–55 band, and the book stayed active.
- **The funding prediction came true, but it proves less than it looks.** I predicted funding drag
  would collapse from the seed's ≈ −5 %/yr. It did, to −0.53 %/yr. Honestly discounted: most of
  that is exact net-neutrality, not signal — the seed carried a net-long tilt (long share 0.547)
  into a contract where longs pay. It is evidence the book is not sitting on the structurally
  expensive side. It is not evidence the signal works.

---

## 2. The one thing I refused to do

**I did not flip the sign.** The pre-committed positive loading on `OFI × Z` is unchanged.

Two independent reasons, and I want both on the record because either alone would be enough:

1. **The preregistration forbids it.** THESIS §3: *"What I will not accept as a rescue... I am not
   permitted to rescue it by flipping sign."* §4.4 anti-surface: no conditional sign flips, no
   regime switching. A sign chosen after seeing one result is not a sign, it is a fit.
2. **The statistics forbid it too, which is the part that would matter even without a
   preregistration.** Flipping would build a book whose entire directional claim rests on
   |t| = 0.45. THESIS §2 failure mode #5 anticipated exactly this escape hatch — *"forced
   liquidations execute as market orders and print large... in the far right tail, big prints may
   be mechanically forced and mean-reverting rather than informed"* — and it is a genuinely
   coherent story. That is what makes it dangerous. A plausible mechanism plus a t of 0.45 is how
   you talk yourself into a coin flip. The sealed blocks would price it as one.

I note for completeness that the *assigned* falsifier — "if average trade size is merely a volume
proxy, it carries no information volume does not already carry" — has **not** been tested. Testing
it was F2, the control books substituting `z(log V)` and `z(log N)`. I had two trials and the first
was the compulsory seed, so F2 was never run. I am not going to present an untested falsifier as a
surviving one. The mandate is neither confirmed nor falsified by this lane's evidence; it is
**unresolved**, and I would rather say that than dress up a null as either outcome.

---

## 3. What changed, and why none of it is a search

Three changes from t02. **None was selected on performance** — I have exactly one performance
reading in existence and I did not use it to choose a direction.

### 3.1 Cost: turnover halved, from a measured cost per turn

t02 measured cost at **6.83 bps per unit turnover**. The gates that failed are all downstream of
the cost bill:

| turnover | 1× cost / yr | 3× cost / yr | gross Sharpe needed to survive 3× |
|---|---|---|---|
| 266 (t01, seed) | 13.0 % | 39.1 % | ~3.5 |
| 40 (t02) | 2.76 % | 8.27 % | **0.83** |
| **20 (this book)** | **1.37 %** | **4.10 %** | **0.42** |

My turnover model from the refinement — `turnover ≈ K / √(M·m)` for smoothing `m` and rebalance
interval `M` — was validated by t02: predicted 39, realised 40.3, giving `K ≈ 810`. Setting
`m = 90` bars (30 d) and `M = 18` bars (6 d) gives `√(M·m) = 40.2` and a projected turnover of
**≈ 20**.

This is arithmetic on a measured constant, not a hill-climb. Cost is the *certain* term and edge is
the *uncertain* one, so halving the certain term is unambiguously correct under any belief about
the sign. It does not repair the sign evidence and I am not claiming it does.

**The honest caveat.** `gross_edge_density` is edge *per unit turnover*, so it improves only if the
signal's total edge decays more slowly than its turnover — i.e. only if the participation-mix state
variable is genuinely slow. **That is the bet.** The literature carrying my sign prior is the
support for it: Hvidkjaer's small-trade imbalance predicts for up to two years, Barclay–Warner's
stealth trading accumulates over days and weeks, BIS retail distribution runs over quarters. The
single citation that pointed at 8 hours — the Quarter-Hour Effect paper's 8–12 h peak in
order-imbalance forecasting power — is the one the cost gate has already ruled out, and slowing
down is what the *rest* of my citation set said in the first place.

**The risk I am taking, named.** I know turnover 40 passes the band. I do not know where the floor
is. Going to 20 is a factor-of-two step from a known-passing point and could in principle breach a
floor I cannot see. A book turning over 20×/yr — a ~2.5-week holding period, 61 explicit refreshes
a year — is a normal medium-frequency portfolio by any standard I know, so I judged the cost saving
worth the exposure. If the packet says `turnover_floor`, that is my error and it is a cheap one to
identify.

### 3.2 Structure: the signature property restored, by scaling instead of shifting

This is a **reversion**, not an innovation. `discovery-RATIONALE.md` §5 argued, before any data,
that cross-sectional demeaning of the conviction *"would give a symbol at Z = 0 a nonzero weight
equal to minus the cross-sectional mean, which destroys the one property that distinguishes this
from a volume book."* t02 then did exactly that. I am undoing it.

The fix keeps both things I need:

- **Demean the *flow* factor cross-sectionally, not the conviction.** The market-wide buy/sell wave
  lives in `z_flow`; removing it there strips the common directional tilt at its source. Because
  conviction is `z_flow_demeaned × z_size`, a name with `z_size = 0` still has conviction **exactly
  zero**. It also guarantees both sides are populated, since roughly half the names sit either side
  of the cross-sectional flow mean — two-sidedness becomes structural rather than incidental.
- **Neutralise net exposure by scaling each side, not by shifting the vector.** Scaling maps zero
  to zero and preserves ordering within a side; shifting does not. Long and short gross come out
  exactly equal, reproducing t02's measured-good 0.50/0.50 exposure split without the shift that
  broke the mechanism's signature.

So: **a name whose average trade size sits at its own trailing median carries weight zero, no
matter how large its volume is.** That property is the mandate, expressed so it can fail. A volume
proxy cannot have it, and t02's book did not have it.

### 3.3 Deviations from the sealed parameter surface, stated plainly

`SMOOTH = 90` and `REBALANCE_EVERY = 18` are both outside §4.1's declared ranges (`k ∈ {1,3,9}`,
rebalance every bar). This is the second time I have broken §4 on the same axis and I am recording
it as a broken preregistration rather than pretending the surface anticipated a cost gate. The
mitigating facts, such as they are: every value in the declared set fails `turnover_ceiling`
*arithmetically*, before any data is consulted; I did not search horizons and rank them by Sharpe,
I solved one cost equation; and the surface's purpose — making the trial count meaningful — is
served by the fact that this lane has run **two** configurations total against a declared ceiling of
240, and neither was chosen by comparing outcomes.

Unchanged and unsearched: the size primitive `quote_volume / trade_count`; the ±3 SD winsorisation;
the **positive** sign; `NORM_WINDOW = 180`; global parameters with no per-asset fitting; the
universe exactly as provided; hygiene (drop `N = 0` or `V = 0` bars, discard a listing's first 30).
The anti-surface holds in full: no ML, no regime switching, no conditional sign flips, no funding
overlay, no volatility targeting, no asset selection by performance.

---

## 4. The mechanism, and who is on the other side

Each 8 h bar publishes quote volume `V` and trade count `N`, so `S = V/N` and `log S ≡ log V −
log N` exactly. `N` is the arrival clock (Ané–Geman 2000). `S` is not a second reading of volume:
conditional on the clock it says how much notional rode on each arrival — the *composition* of
trading, not its *scale*. A volume factor loads on `(+1,+1)` in `(log V, log N)` space; this
mandate lives on `(+1,−1)` and nowhere else.

`S` is unsigned, so it conditions the sign of the one signed participation variable available:
`OFI = 2·(taker_buy_quote_volume / quote_volume) − 1`. All four quadrants are economically
coherent, which is the test that this is a mechanism and not a fitted sign:

| trade size | relative taker flow | reading | position |
|---|---|---|---|
| large | buying | professional accumulation, sliced but not to retail scale | long |
| large | selling | professional distribution | short |
| small | buying | retail chasing a rising price | short |
| small | selling | retail capitulation | long |

**On the other side: the leveraged retail taker on Binance USD-M perpetuals.** Three legs, all from
THESIS §1.3:

1. **Documented to lose.** BIS Bulletin 69 (Cornelli, Doerr, Frost, Gambacorta 2023): through
   Terra/Luna and FTX, *"large and sophisticated investors [were] selling and smaller retail
   investors buying"*; across 95 countries a majority of crypto-app users lost money on bitcoin.
2. **The transfer is explicitly priced on this contract.** Binance BTC perpetual funding averaged
   ~13.7 % annualised over 2020–2025 against a ~3.1 % bill rate — ~10.6 pp paid by longs to shorts,
   roughly 3× the CME bitcoin futures financing spread (Elm Wealth). A population that persistently
   pays double-digit carry to be long is not, by revealed preference, the informed side.
3. **It is not arbitraged away.** The professional leg needs balance sheet and tolerance for
   liquidation risk on the short perp; and the retail side is a *flow*, replenished with every price
   rise, not a stock that can be exhausted.

I am not claiming the signal persists because it is obscure — Binance publishes trade count in every
kline and anyone can divide. The persistence claim rests entirely on limits-to-arbitrage plus a
continuously recruited counterparty. A reader who rejects those should reject the thesis.

---

## 5. Why not the seed, and why not retire

THESIS §3 said: if the falsifiers fire, *"nominate the unmodified organizer seed rather than a
fitted book."* I am not doing that, and the reason is a fact I did not have when I wrote it.

**t01 showed the seed fails four hard gates** — `turnover_ceiling`, `gross_edge_density`,
`cost_share`, `survives_triple_cost` — at turnover 266 and net Sharpe −2.04. When I wrote that
instruction I believed the seed was a neutral abstention. It is a known-disqualified book.
Nominating it would not be honesty; it would be theatre with the same expected value as retiring,
minus the candour. The *intent* of that clause was "do not nominate something fitted," and I have
honoured the intent: the sign is unchanged, no parameter was chosen by comparing outcomes, and the
one construction change reverts to what I argued for before any data existed.

Retiring was genuinely on the table and I want to be clear about why I did not take it. Retiring is
the right call when the mandate has been *falsified*. Mine has not been tested — F2, the control
books that would decide whether this lane found participant mix or merely re-found volume, was
never run, because trial one was the compulsory seed and trial two was the mechanism's only
outing. Retiring on an unresolved question would report a falsification I did not earn, in the same
way that flipping the sign would report an edge I did not earn. What I can honestly put forward is a
book whose structure is measured and sound, whose mechanism is unproven, and whose documentation
says so.

Per the decision-phase guidance: this is not my highest-Sharpe book — I have no positive-Sharpe book
of any kind. It is the one I can explain end to end.

---

## 6. What would falsify this, stated before the packet

1. **`gross_edge_bps_per_turnover ≤ 0` again, at half the turnover and 30-day smoothing.** Two
   independent horizons, both null-to-negative. At that point the expression is dead and the correct
   report is that the `OFI × Z` interaction carries nothing on this venue over this window. **Not
   rescuable**, and I will not seek a third horizon.
2. **`gross_edge_bps_per_turnover` positive but below ≈ 20.5 bps** (= 3 × 6.83). The mechanism is
   real and uneconomic. That is a genuine finding, not a tuning target.
3. **Turnover outside 10–35.** My `K ≈ 810` turnover model, which t02 validated once, is wrong, and
   every parameter derived from it is unsupported.
4. **Turnover band failure at the floor.** §3.1's risk, realised. A construction error, cheap to
   name, and it says nothing about the mechanism.
5. **Long exposure share materially away from 0.50, or effective breadth below ~15.** The
   side-scaling construction is not doing what I claim; the neutralisation or the flow demeaning is
   behaving differently from my model of it.
6. **Funding drag returning toward the seed's −5 %/yr** on an exactly net-zero book. §4's
   counterparty story has the crowded side backwards.

**What I will not accept as a rescue:** flipping the sign, reinterpreting `S` as a volatility or
liquidity signal, substituting trade count as the finding, gating on tails to escape the liquidation
channel, or selecting assets on performance.

**Standing construct-validity threat I cannot test.** Cong, Li, Tang & Yang (*Management Science*
2023) place Binance in the unregulated set, where >70 % of reported volume was inflated — and their
detection tests are round-trade-size clustering and the trade-size distribution tail, which is
exactly my object. Their sample is spot, four coins, 2019, and margined derivatives are harder to
fake. The signed-square-root weight map bounds the damage a single fabricated print can do. Nothing
in this dataset lets me do better than that.

---

## 7. Expected metric profile, written before the packet

Turnover **14–28**; median effective breadth **22–32**; mean gross exposure **0.85–1.00**; long
exposure share **≈ 0.500 by construction**; `active_bar_fraction` **≈ 1.0** (positions persist
through the 18-bar holds); `breadth_pass_fraction` **1.0**; funding drag **0 to −1 %/yr**; cost at
1× **≈ 1.4 %/yr** and at 3× **≈ 4.1 %/yr**, so the 1× → 3× decay should be about half t02's.

I have no prediction for the sign of the return, and I would not believe one if I wrote it.

---

## 8. Invariance and contract compliance

- **No look-ahead.** Only rows present in the supplied frame are read; every statistic is trailing.
- **No hidden state, no RNG.** The strategy instance holds nothing between decisions; the book is a
  pure function of the context. `seed` is unused.
- **No absolute-date targeting.** `decision_time` is never read. The rebalance cadence is
  `max(len(frame)) % 18`, derived from bar counts, so it is invariant to calendar shift.
- **Symbol pseudonymisation.** No symbol identity anywhere; symbols are sorted only to fix array
  order, and every operation is order-independent.
- **Magnitude-scale equivariance.** `log S` shifts by a constant under price rescaling and the
  trailing z removes it; `OFI` is a ratio and is invariant outright. No price level and no `S`
  *level* appears anywhere — which is also the mitigation for the "raw cross-sectional `S` is a size
  factor in disguise" failure mode (Liu, Tsyvinski & Wu 2022).
- **Small-perturbation stability.** The signal is continuous in both inputs with no thresholds; the
  only discrete element is the integer rebalance cadence, which is a schedule, not a fitted cut.
- **Panel-alignment trap.** No cross-symbol panel is ever built — each symbol is reduced to two
  scalars inside its own frame — so the positional-`RangeIndex` failure cannot silently empty this
  book.
- **Caps.** Gross ≤ 1.0, |net| = 0 by construction (cap 0.25), per-symbol ≤ 0.09 (cap 0.10), applied
  by one uniform rescale on whichever constraint binds.
- **No volatility targeting.** The strategy emits a unitless conviction; the organizer's common
  ex-ante risk unit does all scaling. `S` sets direction only, never gross exposure.

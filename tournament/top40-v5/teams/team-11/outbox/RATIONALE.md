# team-11 discovery candidate — participant mix via average trade size

**Family:** microstructure and participation · **Mandate:** average trade size as a
retail-versus-institutional proxy · **Phase:** discovery (baseline, not an elaboration)

This is the preregistered primary expression (THESIS.md §1.5) at the **central setting** of the
declared parameter surface (§4.1). No search has been run against any data. Every number in
`candidate.py` is either the middle value of a declared knob or a constant fixed by
preregistration in §4.3, or an exposure cap owned by the contract. That is deliberate: the
discovery trial is spent buying a baseline I can diagnose, not a book I have tuned.

---

## 1. The mechanism

### The identity that makes this not a volume book

Each 8h bar exposes quote volume `V` and trade count `N`. Average trade size is

```
S = quote_volume / trade_count            (USD notional per print)
log S ≡ log V − log N                     (exact identity)
```

Volume and count are not two noisy readings of one quantity. `N` is a **clock** — the arrival
process of information events (Ané–Geman 2000). `S` is **composition** — conditional on the
clock, how much notional rode on each arrival. In a venue where the marginal small print is a
leveraged retail taker clicking a market order and the marginal large print is a desk, a market
maker or a basis book, `S` reads *who* transacted, not *how much*.

Geometrically: a loading on `(log V, log N)` decomposes into a **scale** direction `(+1,+1)` —
volume-family territory — and a **contrast** direction `(+1,−1)`. This mandate lives, and can
only live, on the contrast direction.

### Why a state variable needs a sign, and where the sign comes from

Average trade size is **unsigned**. Large prints do not say "up." This dataset supplies exactly
one signed flow variable, itself a participation variable, so combining them stays inside the
assigned family rather than borrowing from another:

```
OFI = 2 · (taker_buy_quote_volume / quote_volume) − 1        ∈ [−1, +1]
```

The book is the product, with the sign **pre-committed positive** before any data was mounted:

```
signal = mean_k(OFI) × mean_k(Z),      Z = winsorised trailing z-score of log S
```

- `Z > 0` (unusually large prints) **and** net taker buying → professional accumulation →
  continuation → **long**. (Barclay–Warner 1993 stealth trading; Chakravarty 2001 attributes the
  disproportionate price impact of medium/large prints to institution-initiated trades.)
- `Z < 0` (unusually small prints) **and** net taker buying → retail chasing → transitory →
  **short**. (Hvidkjaer 2008: stocks with intense *buy*-initiated small-trade volume
  underperform those with intense *sell*-initiated small-trade volume, for up to two years.)

**The property that matters:** when average trade size sits at its own trailing median, `Z ≈ 0`
and the position is zero **no matter how large volume is**. A volume proxy cannot have that
property. That is the mechanism expressed so that it can fail.

### Why 8h is the right clock, not a constraint being tolerated

Binance USD-M perpetual funding settles every 8 hours at 00:00 / 08:00 / 16:00 UTC. One bar is
one funding epoch: the participation mix inside the epoch and the price the leveraged side paid
for it are measured on the same grid. Independently, the Quarter-Hour Effect study
(arXiv:2607.09426, Binance USD-M perps) finds the cumulative forecasting power of order
imbalance peaks between **eight and twelve hours** and is much weaker at finer frequencies.

---

## 2. Who is on the other side

**The leveraged retail taker on Binance USD-M perpetuals.** Three facts make that counterparty
structural rather than incidental:

1. **They are documented as the losing side.** BIS Bulletin No 69 (Cornelli, Doerr, Frost,
   Gambacorta 2023): after Terra/Luna and FTX, "large and sophisticated investors [were] selling
   and smaller retail investors buying"; across 95 countries, Aug 2015–Dec 2022, a majority of
   crypto app users lost money on bitcoin.
2. **The transfer is priced explicitly on this exact contract.** Binance BTC perpetual funding
   averaged ~13.7% annualised over 2020–2025 against a ~3.1% T-bill rate — a ~10.6pp structural
   payment from longs to shorts, roughly 3× the CME bitcoin futures financing spread and 7–20×
   traditional bond/equity index futures (Elm Wealth). A population that persistently pays
   double-digit carry to be long is, by revealed preference, not the informed side.
3. **It does not get arbitraged away.** The professional side needs balance sheet and tolerance
   for margin-liquidation risk on the short perp leg, which slows arbitrage; and the retail
   population is a *flow*, replenished with every price rise (BIS), not a stock that can be
   exhausted.

I am **not** claiming the signal persists because it is obscure. Binance publishes `number of
trades` in every kline; anyone can divide. The persistence claim rests entirely on
limits-to-arbitrage plus a continuously recruited counterparty. A reader who rejects those
should reject the thesis.

**What the premium compensates for:** taking the other side of leverage demand and absorbing
inventory when the leveraged side is forced out. The risk is that small prints are sometimes
right — genuine adoption and news shocks do arrive through retail — and that liquidation
cascades produce gap risk against whoever stands on the professional side.

---

## 3. What would falsify this

The mandate's falsifier, stated before any result: *if average trade size is merely a volume
proxy, it carries no information that volume does not already carry.* Made operational in
THESIS.md §3 and repeated here as the standard this candidate is held to.

**F1 — contrast test (primary).** Residualising `log S` on `{log V, log N}` is degenerate by the
identity above and would be a fake test. The honest form is directional: fit
`r_{t+1} = a + b₁·z(log V) + b₂·z(log N)` and decompose `(b₁, b₂)` into scale `(+1,+1)/√2` and
contrast `(+1,−1)/√2`. **The contrast component must reach |t| ≥ 2.0** with errors clustered by
asset and by time. Indistinguishable from pure scale ⇒ falsified.

**F2 — control books.** Same pipeline, same risk unit, substituting the participation variable:
(a) `z(log S)` — the mandate; (b) `z(log V)`; (c) `z(log N)`. **The `S` book must beat both
controls on development Sharpe in ≥2 of 3 sub-periods.** Losing to either control falsifies the
mandate *regardless of the `S` book's absolute performance* — a profitable book that a volume
control also produces is not evidence for this mandate.

**F3 — sign stability.** The pre-committed **positive** loading must hold in both halves of the
development sample and in ≥⅔ of the universe. Working only by flipping sign across periods or
assets means fitted, not economic.

**F4 — permutation gate (non-nomination condition).** Permute `Z` across assets at each
timestamp while holding `z(log V)`, `z(log N)`, `OFI`, funding and returns at their true asset
assignments; 200 draws. This preserves every market-wide, time-of-day and funding-epoch effect
and breaks only the asset-level size↔return link. The nominated configuration must exceed the
90th percentile of that null, or the edge is the flow channel or a calendar artifact.

**What I will not accept as a rescue.** If F1–F3 fail I will not reinterpret `S` as a volatility
or liquidity signal, will not substitute trade count as the finding, will not re-specify the
horizon, and will not flip the sign in the tail. Per RULES.md, retiring honestly is available
and nomination is never required.

---

## 4. Known failure modes, stated before the result

So that none can be discovered later and presented as foresight. Full list in THESIS.md §2; the
four that most plausibly kill *this* candidate:

1. **The literature's standing verdict is against me.** Jones, Kaul & Lipson (1994) found
   average trade size has **no incremental information content beyond the number of trades**.
   That is my assigned falsifier as a published equity result. My bet is that a retail-dominated,
   high-leverage, 24/7 venue with a documented losing counterparty differs from NASDAQ-NMS in
   1994. It may not.
2. **The tape may be partly fabricated.** Cong, Li, Tang & Yang ("Crypto Wash Trading",
   *Management Science* 2023) place Binance in the unregulated set, where >70% of reported volume
   was inflated — and their detection tests are round-trade-size clustering and the trade-size
   distribution tail, i.e. exactly my object. Their sample is spot, four coins, 2019, and
   margined derivatives are harder to fake; but this is the largest construct-validity threat and
   I cannot test it with this data.
3. **Tail inversion via liquidations.** Forced liquidations execute as market orders and print
   large. In the far right tail, big prints may be mechanically forced and mean-reverting — the
   opposite of my sign. This is the single most likely way the pre-committed sign is wrong.
   Winsorisation is fixed at 3 SD and I am not permitted to rescue it by flipping sign in the
   tail.
4. **The interaction may be carried entirely by `OFI`.** If this is really an order-flow momentum
   book with `Z` along for the ride, the mandate has contributed nothing. That is what F4 and the
   A3 ablation exist to detect, and it is why beating the controls in F2 matters more than the
   headline Sharpe.

---

## 5. What is in the code, and what is deliberately not

**Settings — all central values of the declared surface (§4.1):** trailing z-score
normalisation; window `W = 90` bars (30 days); smoothing `k = 3` bars (1 day) on both `Z` and
`OFI`; `Z` built directly from `log S`; **time-series, own-asset only — no cross-sectional
demeaning**.

Cross-sectional demeaning is a declared knob (§4.1 #5) and I did not take it, on purpose: it
would give a symbol at `Z = 0` a nonzero weight equal to minus the cross-sectional mean, which
destroys the one property that distinguishes this from a volume book. Discovery should test the
mechanism's signature, not launder it into a generic ranker.

**Fixed by preregistration (§4.3):** size primitive `quote_volume / trade_count` (base-per-trade
imports the price level); rebalance every bar on the funding grid; clipped-linear position map at
3 SD; **global parameters, no per-asset fitting**; universe exactly as provided, no selection by
me; hygiene — drop bars with `N = 0` or `V = 0`, drop the first 30 bars after an asset's first
observation.

**Scale invariance is structural, not asserted.** `Z` is a within-asset z-score of a log, so
multiplying a symbol's notional by any constant shifts `log S` by a constant that the mean
subtraction removes; `OFI` is a ratio. No price level, no symbol identity, no absolute date and
no `S` *level* appears anywhere — which is also the mitigation for the "raw cross-sectional `S`
is a size factor in disguise" failure mode (Liu, Tsyvinski & Wu 2022 show market/size/momentum
already absorbs ten characteristic-based crypto strategies).

**Book construction.** Conviction is normalised to gross 1.0, clipped to the ±0.10 per-symbol
cap, then the dominant side is scaled until |net| ≤ 0.25. The signal is continuous in both
inputs with no thresholds, so small perturbations move the book smoothly.

**No volatility targeting.** The strategy emits a unitless conviction; the organizer's common
ex-ante risk unit does all scaling. `S` sets *direction* only, never gross exposure. `S` is
contemporaneously correlated with realised volatility, so if this book's PnL is really volatility
timing in disguise, the common risk unit should strip it — I regard that as the correct outcome,
not an obstacle.

---

## 6. What I want to read off the first packet

Named now so the reading is not retrofitted:

1. **Did it run at all?** Non-trivial mean gross exposure and a plausible symbol count. A flat
   book means I misread the context, not that the mechanism failed — those are different results
   and I do not want to confuse them.
2. **Breadth and two-sidedness on exposure.** The time-series form leaves net exposure free, and
   if `OFI` and `Z` are positively correlated within assets the product has a positive mean and
   the book tilts long. If the net cap is binding often, that is a construction fact to fix, not
   a verdict on the mechanism.
3. **Turnover and cost share, including survival at 3× cost.** `k = 3` at every-bar rebalance is
   an untested guess about turnover; the band and gross-edge-per-turnover gates will price it.
4. **Whether anything is left after the controls.** The headline Sharpe is not the result. F2 is.

A falsified thesis is a result, and this candidate is written so that outcome is legible rather
than escapable.

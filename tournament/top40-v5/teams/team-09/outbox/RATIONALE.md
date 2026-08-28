# RATIONALE — team-09, volume-confirmed channel breakout

**Family:** time-series trend. **Mandate:** channel breakout gated on participation.
**Preregistered thesis:** `lane/scouting/THESIS.md` (sealed at scouting).
**Evidence in hand:** one feedback packet, `t01` — the unmodified organizer seed.

---

## 1. What the feedback actually told me, and what it did not

`t01` is the seed, not my design. It was **admitted with no failed gates**:

| | t01 |
|---|---|
| net Sharpe | 1.204 |
| double-cost Sharpe | 0.944 |
| triple-cost annualised return | +7.2% |
| annualised turnover | 37.8 |
| gross edge / turnover | 42.3 bps |
| cost share of positive gross | 17.7% |
| median effective breadth | 18.0 |
| mean gross exposure | 0.615 |
| long / short exposure share | 0.525 / 0.475 |
| risk-unit capped fraction | 0.136 |
| positive fold fraction | 0.60 |

The refinement instruction is to diagnose rather than tune. The honest diagnosis is that
**there is no broken gate to repair** — so tuning would be tuning against a book I did not
design, on a single packet, with eleven trials of hill-climbing left to burn. That is exactly
the search the rules warn makes a development Sharpe a statement about a search rather than an
edge. I have therefore used `t01` for one thing only: to read off the **cost geometry of the
venue**, which is a fact about the tournament rather than about the seed.

Back out the cost: gross edge 42.3 bps × 37.8 turnover ≈ 16.0% gross against 13.4% net, so
**cost ≈ 7 bps per unit of turnover at 1x, ≈ 21 bps at 3x**. That is the number that governs
design. A book needs gross edge per unit turnover comfortably north of ~25 bps to be a book at
3x rather than a book at 1x. Every construction choice below is made against that budget, not
against `t01`'s Sharpe.

The one number I read as a *design* signal is `long_exposure_share = 0.525`. The seed runs a
genuinely two-sided book. Section 2 explains why that is not optional here.

## 2. The structural problem a channel breakout has in this tournament

This is the design problem, and it is the reason the candidate is shaped the way it is.

The caps are `gross ≤ 1.0`, `|net| ≤ 0.25`, `|w| ≤ 0.10`. Together they mean **a fully invested
book cannot be one-sided**: at gross 1.0 the most lopsided admissible book is 62.5/37.5. So the
tournament does not permit a directional time-series trend book at full size. It permits a
*relative* trend book with a bounded directional tilt.

Crypto perps co-move hard. A naive channel breakout therefore breaks up on nearly everything at
once in a bull tape: the raw book is all-long, the evaluator clips it to net 0.25, and what
survives is a small, one-sided position that fails effective breadth, fails mean gross exposure,
and fails "both sides genuinely used, measured on exposure." That is a **design** failure — no
parameter rescues it — and it is the failure mode I built around rather than discovered.

The resolution: keep the *signal* strictly time-series (each symbol is scored against its own
channel and its own trailing participation distribution — nothing in the score looks at another
symbol), and make only the *budget* cross-sectional. The score vector is split into

- a **cross-sectional core** (`score − mean(score)`), which spends the gross budget on relative
  trend strength and is two-sided by construction, and
- a **bounded directional tilt**, `0.18 · tanh(mean(score)/0.5)`, which carries the market-wide
  time-series signal and saturates well inside the net cap.

When everything breaks up together, the book is net long ~0.17 and holds the strongest breaks
against the weakest — not a clipped stub. When the tape is mixed, the tilt goes to zero and the
book is balanced. Long share stays inside roughly 0.40–0.60 by construction, in the same
territory the seed occupied.

## 3. The mechanism

### 3.1 Why a channel, and why continuous

The base premium is time-series momentum (Moskowitz–Ooi–Pedersen 2012): under-reaction followed
by delayed over-reaction, with speculators paid by hedgers. I express it as a channel rather
than a return sign because George–Hwang (2004) show nearness to a running extreme *dominates*
raw past returns as a momentum predictor **and** — unlike raw momentum — its forecast returns do
not reverse at long horizons. That is a structural advantage, not a reparameterisation.

The score is the George–Hwang nearness statistic itself:

```
c_N = (2·price − high_N − low_N) / (high_N − low_N)   ∈ [−1, +1]
```

`+1` means the price sits exactly on the N-bar high — i.e. **`|c| = 1` is the hard break, and the
statistic is its continuous interior.** I use the continuous form deliberately: a hard break
event fires on ~10–15% of names at any decision, which cannot fill a book that has to clear an
effective-breadth gate. `price` is a 3-bar mean of closes and the score is averaged over four
lookbacks (21/42/84/168 bars = 7/14/28/56 days), both of which are turnover control: the channel
edges are maxima over ≥21 bars and move slowly, and a name must break on several horizons at
once to score near ±1. Slower signal, fewer bps spent, which is what §1 says the 3x budget
requires.

### 3.2 Why the gate, and what it measures

A channel break is a **mixture of two populations** and the naive rule buys both:

- **Informed repricing** — someone with a view crosses the spread, and the move continues because
  the information is not yet impounded. Llorente–Michaely–Saar–Wang (2002): returns from
  speculative trade **continue**.
- **Inventory shock** — a large risk-sharing order pushes price out of the range against a
  risk-averse liquidity provider, who is compensated for warehousing it. Price reverts.
  Campbell–Grossman–Wang (1993): autocorrelation *declines* with volume when makers accommodate
  non-informational pressure.

Blume–Easley–O'Hara (1994) is the licence: volume carries information about **signal precision**
that price alone cannot convey. So conditioning on it is rational learning, not folklore.

The trap is Karpoff (1987): volume is positively related to the *magnitude* of the price change,
so a high-volume break is partly just a large break, and a gate on raw volume is a volatility
filter wearing a costume. I therefore make **direction-signed taker imbalance the primary gate
input**, because it identifies *who crossed the spread*, is a pure ratio, and carries a sign.
Raw volume and ticket size enter only as a **confidence weight** on that reading, never as the
reading itself:

```
align = tanh( z[ taker_buy_quote / quote_volume ] )              # who was aggressive
amp   = ½·(1 + tanh( ½·( z[log quote_volume] + z[log(qv/trades)] ) ))   # how much to trust it
score = c + γ·|c|·align·amp,          γ = 0.6
```

Two properties matter. First, the gate term is multiplied by **`|c|`**, so it is largest exactly
at the channel extreme and vanishes mid-range — that is what "breakout *gated on* participation"
means when written continuously. Second, `score = c·(1 + γ·align·amp·sign(c))` is **continuous
through `c = 0`** (the `sign` is cancelled by the `|c|` factor), so there is no razor-thin
threshold for the small-perturbation check to find.

The signs work out as the mechanism requires: an up-channel met by unusually aggressive,
large-ticket buying is amplified toward 1.6×; an up-channel met by aggressive *selling* — price
leaving the range while takers hit bids, the Campbell–Grossman–Wang inventory branch — is
attenuated toward 0.4×. A down-break confirmed by aggressive selling is amplified short.
`γ = 0.6` bounds the modulation so **the gate can never flip the sign of the trend position**;
per F3 I preregistered continuation and I am not building a machine that can silently invert it.

All three z-scores are robust (median/MAD) against the **symbol's own trailing 63-bar
distribution**. That is deliberate per Cong et al. (2023) on wash trading — no participation
statistic is ever compared to a cross-sectional volume *level*, and trade count and ticket size
sit in the composite as independent cross-checks on quote volume.

### 3.3 Who is on the other side

- **Levered directional retail.** Long into strength, liquidated into weakness, paying funding to
  be long a trending perp (He et al. 2022/24: past 120-day returns explain >50% of the perp–spot
  gap). Their forced exits *are* the continuation. Primary payer.
- **Inventory-constrained market makers.** They lean against the break and must be compensated —
  and they are *right* on the low-participation breaks. The gate exists to stop trading against
  them when they are right; on the confirmed breaks I am on the informed side of the same trade.
- **Late discretionary and allocator flow**, which completes the repricing — the delayed
  over-reaction half of the MOP story.
- **Delta-neutral cash-and-carry funds**, directionally indifferent, capping the size of the
  premium without fighting the direction of a break.

I am on the informed-repricing side and I pay carry to be there. Selectivity is not a free
preference; it is how I avoid paying funding on breaks that were never going anywhere.

## 4. Cost and structural arithmetic

Against the ~7 / 14 / 21 bps-per-turnover budget backed out in §1:

- **Turnover** is attacked in three places at once — a 3-bar smoothed price probe, a four-lookback
  ensemble whose channel edges are slow maxima, and a cross-sectional dead-zone (`|z| < 0.2σ →
  weight exactly 0`) that stops mid-pack names churning their sign for zero conviction.
- **Breadth** is protected by demeaning (two-sided by construction) plus a mild flattening
  (`|z|^0.7`) of the weight distribution. Expected effective breadth is comfortably above the 18
  the seed posted; the flattening is insurance against a small eligible universe, where a linear
  weighting could fall through the gate.
- **Both sides on exposure** follows from the demeaning, not from the P&L.
- **Gross** is submitted at 0.95 spread over the whole admissible set, so per-name weights sit far
  below the 0.10 cap and the organizer's ex-ante risk unit can scale in either direction without
  per-symbol clipping distorting the shape.
- **Liquidity floor**: bottom quintile by trailing 126-bar median quote volume is dropped —
  declared as fixed-by-construction in the thesis, and it protects the participation statistics
  from the thinnest, most wash-contaminated names.

I do not target volatility anywhere. There is no ATR band, no vol scaling, no risk parity. The
only sizer is the organizer's.

## 5. Declared surface, and what I chose not to spend

Every knob below comes from the sealed §5 surface. Where the surface offered a set, I either
**ensembled the whole set** or took the value fixed a priori on cost grounds — I did not select
on feedback, because I have no feedback on any of these:

| Knob | Declared range | Setting | Why |
|---|---|---|---|
| `channel_lookback` | {6,12,21,42,84,168} | **ensemble of {21,42,84,168}** | Ensembling refuses the selection rather than making it. 6 and 12 bars dropped a priori on the §1 cost arithmetic, not on results — a 2-day channel is 6 observations and its turnover is unaffordable at 3x. |
| `exit_fraction` | {0.5, 1.0} | **1.0 (symmetric)** | The continuous score exits by decay; the asymmetric variant needs carried state, which is forbidden. |
| `channel_basis` | fixed: closes | closes | As declared. |
| `participation_stat` | {V,T,S,I,D} | **D** (composite) | The declared composite: abnormal **and** aggressively aligned. Karpoff says `V` alone risks being a volatility filter. |
| `gate_threshold θ` | {0.5,1.0,1.5} | **1.0** | Midpoint, as a tanh scale rather than a cliff. |
| `norm_window W` | {21,63} | **63** | A priori: 21 bars overlaps the shortest channel lookback, which would make the gate partly a restatement of the signal. |
| `gate_mode` | {hard, soft} | **soft** | A hard binary gate is exactly the razor-thin threshold the small-perturbation check exists to catch, and it destroys breadth. |
| `confirm_bars k` | {1,2} | **2** | As declared. |
| `funding_veto` | {off, on} | **off** | See below. |

**Funding overlay left off, and why that is a decision rather than an omission.** Binance
shortened funding settlement from 8h to 4h and then to 1h for some contracts, so per-settlement
rates are not comparable across symbols at a point in time — a cross-sectional read is corrupted
by cadence heterogeneity — and the per-symbol trailing normalisation that *would* fix it is a
groupby over a frame that grows to hundreds of thousands of rows, at every one of ~2,400
decisions. I declared `off` as an admissible setting and I am taking it, rather than shipping an
expensive statistic I cannot validate. Thesis §6 already recorded this cadence problem before any
data was mounted; this is that caveat being honoured, not retrofitted.

**Not searched, not present:** per-symbol parameters, date-conditioned regime splits, any
volatility target, any funding-carry alpha overlay.

**Charged trials consumed to date: 1** (`t01`, the seed). This candidate is trial 2. Nothing in
it has been fitted to `t01`; the only quantity taken from that packet is the venue cost per unit
turnover, which is a property of the tournament rather than of any strategy.

The portfolio construction constants (dead-zone 0.2σ, flattening 0.7, gross 0.95, tilt cap 0.18)
are **not** in the declared surface, and I am flagging that rather than hiding it. They are not
signal parameters and they were not chosen against returns: they are the response to the cap
geometry in §2 and to the structural gates, set a priori and left alone. If I later move them, it
is a trial and I will count it as one.

## 6. What would falsify this

Stated so that a bad packet is a result rather than a prompt to tune. Per thesis §4, evaluated
once, on visible development data.

**F1 — the gate adds nothing.** Same geometry, `γ = 0` (pure ungated channel book), must be beaten
by **≥ +0.15 Sharpe** and **≥ +2.0pp** continuation rate. If either leg fails, the gate is
falsified, I nominate the plain ungated breakout, and I report that participation confirmation did
not earn its place.

**F2 — the gate is a volatility filter in disguise.** The gate must beat a selectivity-matched
trailing-realised-volatility control by **≥ +0.10 Sharpe**. This is the leg Karpoff (1987)
predicts I might lose, and it is why the gate's primary input is the scale-free signed taker
ratio rather than raw volume. If F2 fails while F1 passes, I say exactly that instead of
reporting F1 alone.

**F3 — the sign.** I preregistered **continuation**. If low-participation breaks continue while
high-participation breaks revert — Campbell–Grossman–Wang dominating in perps — that is a
falsification of the thesis. I will report it as one. **I will not flip `γ` negative and
re-nominate the inverted rule as a confirmation.**

**F4 — placebo.** A permuted-gate control at the same acceptance rate must be beaten by more than
its own run-to-run dispersion.

### Feedback signatures I have committed to read a particular way

- **Turnover far below the band with breadth intact** → the ensemble and the dead-zone over-damped
  the signal. A design error in my smoothing, correctable.
- **Effective breadth below the seed's 18** → the flattening was insufficient for this universe.
  Structural, and I fix the construction rather than the signal.
- **1x fine, 3x negative** → gross edge per turnover is under ~21 bps. Per §1 that is not a book,
  and the answer is a slower signal, not a bigger gate.
- **Sharpe below the ungated control** → F1. That is the mandate failing, and per thesis §4 I
  report it rather than searching for a friendlier gate statistic.

What would **not** count as a rescue: "there were no trends in the sample." Babu et al. (2020)
makes that testable — it requires showing the *ungated* breakout underperformed for the same
reason. If the ungated book worked and the gated book did not, the mandate failed, full stop.

## 7. Compliance notes

Stateless across decisions; no RNG (`seed` is accepted and unused); no network, subprocess,
filesystem, `eval`/`exec`; no embedded data, fitted parameters or symbol identities. No absolute
dates are read, so calendar shift is a no-op. Every statistic is a ratio of prices, a ratio of
volumes, or a log-difference taken against the symbol's own trailing median, so a global
magnitude rescale leaves the book unchanged. No cross-symbol panel is ever built — all
per-symbol work is done on numpy tails of each frame and only a single cross-sectional vector is
formed at the decision, which sidesteps the `RangeIndex` alignment trap entirely. Submitted books
satisfy `gross ≤ 0.99`, `|net| ≤ 0.22`, `|w| ≤ 0.090`, all inside the enforced caps, and only
symbols drawn from `context.eligible_symbols` are ever returned.

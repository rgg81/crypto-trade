# team-02 — funding convexity · discovery baseline

**Trial role:** discovery baseline, not a nomination.
**Specification:** the preregistered **primary cell** of `lane/scouting/THESIS.md` §4.2, unmodified.
**Deflation accounting:** N = 1. Nothing outside §4.1 has been searched, because nothing has been
searched at all — this candidate was written from the sealed thesis before any feedback existed.

---

## 1. The mechanism

Binance USD-M funding is not a sentiment reading. It is a contract-enforced price, computed from
the *impact* bid/ask against the spot index, so levered demand that pushes the perp away from its
index is transcribed into funding mechanically rather than inferred. That gives the payoff its
shape: **the premium is capped per interval, the deleveraging cascade that makes you pay for it is
not.** Bounded premium, unbounded loss, is the payoff of selling variance. Funding is the only
observable *price of a risk* on this venue; realized volatility is the only observable *cost of
bearing it*. This dataset has no options, so there is no implied variance and no literal VRP. The
spread between those two observables is the closest analog the data supports:

> **VRP analog = funding carry per unit of forecast forward realized variance.**

The mandate's instruction — trade the funding *term structure* against realized volatility — is
what separates *"the premium is high because volatility is high"* (fairly paid) from *"the premium
is high because the book is crowded and about to break"* (about to be unpaid). Funding **level**
cannot tell those apart. Funding **dispersion** can, because the distribution moves before the mean
does: in the peak-leverage regime before the 10 Oct 2025 cascade, average funding was an
unremarkable 7.3% APR while peak prints exceeded 29% APR. A level filter would have called that
"bullish, not crowded."

### How that becomes a book

Per symbol, at every decision, from past-only rows:

| quantity | construction | window |
|---|---|---|
| `carry` | sum of realized funding prints ÷ elapsed days → funding per day | 3 days (`s = 9` intervals) |
| `dispersion` | stdev of funding prints, rescaled by √(prints/day) → per-day scale | 21 days (`l = 63` intervals) |
| `RV` | mean per-bar Garman–Klass variance | 3 days (`v := s`, tied) |

The forward-variance forecast is an **equal-weight geometric blend of the two variance proxies in
cross-sectionally centred logs** (dispersion squared, so both terms are variance-like):

```
log σ̂²ᵢ  ∝  ½·centre(log RVᵢ)  +  ½·centre(log dispersionᵢ²)
signalᵢ   =  − carryᵢ / σ̂²ᵢ ,  then cross-sectionally demeaned and normalised
```

Equal weights are a preregistered choice, not a fitted one — there is no regression coefficient
anywhere in this file. Dispersion enters the **denominator** and only the denominator: §4.4 of the
thesis commits to that placement because it is the one place the convexity term can act without
becoming a volatility target.

**Sign, committed in §1.6 before any data:** `f > 0` means longs pay shorts, so a position of sign
`p` accrues `−p·f`. Rich funding earns a short. The two return components reinforce — funding
accrual pays, and shorting the highest-carry names is also shorting the crowd that crashes.

### What keeps it inside the rules

- **Not a volatility target.** Gross is renormalised to a fixed 0.98 at every rebalance. The book
  carries no gross-exposure timing whatsoever; `1/σ̂²` sets *relative* allocation across symbols
  only. The *level* of `σ̂²` is not even computed — it cancels identically in the demean-and-
  normalise step, which is also why the book is invariant to a rescaling of prices or of the
  variance unit.
- **Relative value, not an outright short.** Funding is positive on average, so an undemeaned
  carry book is a permanent short in a bull tape. The cross-sectional demean is load-bearing, and
  §1.6 flags it as not optional.
- **No state, no dates, no identities.** `target_weights` is a pure function of the context. No
  attribute survives a call, so exact replay is deterministic and there is no look-ahead channel.
  No symbol name, absolute date, or price level is ever compared against a literal.
- **Constraints held with margin:** gross ≤ 0.98, |wᵢ| ≤ 0.099, |net| ≤ 0.05.
- **Frequency-agnostic by construction.** Carry and dispersion are expressed *per day*, not per
  print, so a contract switched to hourly settlement stays comparable with one settling every 8h.
  Bar spacing is inferred from the frames' own index rather than assumed.

---

## 2. Who is on the other side

**Paying the premium:** the levered long. Offshore retail, trend-followers, and onshore-constrained
funds who cannot or will not hold spot with custody and financing. They buy convex upside and
finance it with a funding drip. They pay because their alternative is unavailable or more expensive.

**Receiving it:** basis desks, market makers, and delta-neutral yield vehicles — Ethena and its
peers, roughly $14bn of stablecoin backed by exactly this trade.

**Who is on the other side of *this* book specifically — and this is the whole thesis.** *Not* the
levered long; that side is already well supplied, and I am not claiming the premium. My counterparty
is the **unconditional funding harvester**: the vehicle that collects funding without asking whether
the premium is adequate for the variance it is underwriting. That distinction is forced on me by the
evidence, not chosen for elegance. Unconditional crypto carry ran a Sharpe of 6.45 over Aug 2020 –
May 2025, 4.06 from 2024, and **negative in 2025**. Preregistering "harvest funding" in 2026 would be
preregistering a decayed factor. I am claiming the **conditioning**, and I am claiming it against
someone who is not doing any.

The supporting asymmetry that makes *ratio* the right functional form rather than *level*: the
Bitcoin variance risk premium is **larger in low-volatility regimes and smaller in high-volatility
regimes**. A book that sells more insurance when the raw premium looks high — which is when
volatility is high — leans the wrong way. Sizing on premium *relative to* forecast variance leans
the right way.

---

## 3. What would falsify it

The mandate's falsifier: *if funding dispersion carries no information about forward realized
volatility, there is no convexity to trade.* Thesis §3 sharpens it into two conditions, **both** of
which must pass, and §3.4 pre-commits the consequence of each failure — in every failing branch the
nomination is the **unmodified organizer seed**, not a rescued variant.

**F1 (information).** Pooled panel, HAR baseline in log realized variance, plus log dispersion:
positive β; symbol-clustered Newey–West t ≥ 2.5; incremental OOS R² ≥ +0.005; positive sign in ≥ 2/3
of symbols individually. Specified as **incremental to a realized-variance baseline** on purpose: a
raw correlation between funding dispersion and forward volatility would pass almost automatically
and would mean nothing, because funding is driven by the premium index, which widens mechanically
when price moves. **This is the most likely way the lane dies, and the test is built so it can.**

**F2 (economic).** At the organizer's common risk unit, the dispersion-conditioned book must improve
Sharpe over **the same book with the dispersion term removed** by ≥ 0.15. Information that cannot be
harvested at equal risk is not a mandate.

**Concretely, what this specific candidate would have to show to be wrong:**

- It is **structurally short momentum** — shorting the highest-funding names is shorting the crowd.
  In a sustained trending tape that loses for a long time before it wins, and 2024–25 is exactly
  such a period. Persistent negative drift concentrated in the short leg during trending stretches
  falsifies the harvestable version of this.
- If the ablated twin (RV-only denominator, dispersion deleted) scores **at or above** this book,
  the convexity term is contributing nothing and F2 has fired regardless of what F1 says.
- If funding dispersion is only a noisy re-encoding of trailing realized volatility, `a` and `b`
  in the blend are collinear, the blend degenerates to an RV-only forecast, and the same ablation
  test catches it.

**Known failure modes I am not pretending to have solved.** Funding is capped at ±0.75×MMR / ±2% and
settlement may switch to hourly when the cap binds, so at this resolution I see a capped print
without knowing it was capped — **the dispersion estimator is most attenuated exactly where the
signal should be loudest**, and I have no fix in this dataset. Coarse bars see a cascade's round
trip, not its excursion. And the observation this lane is built on (peak-to-average funding before
Oct 2025) is a practitioner post-mortem on a single event, while the strongest peer-reviewed
evidence on cascade early warning is *negative* — no early-warning variable is event-invariant, and
the Oct-2025 signature inverts when tested on Aug-2024. I preregistered into a literature that leans
against me and would rather say so here than find a reason to have believed otherwise later.

---

## 4. Honest notes on this trial

- **This code has never been executed.** This lane has no shell and no mounted data I can read, so
  the candidate is written to be correct by construction and defensive about the shape of `context`:
  every column is checked for presence, every timestamp column is coerced from datetime64, tz-aware,
  tz-naive *or* integer epochs in s/ms/µs/ns, and bar spacing is inferred with a sanity band rather
  than assumed to be 8h. The first feedback packet is as much a smoke test as a result.
- **The top-level `except` in `target_weights` is a deliberate blind spot, and I am flagging it
  rather than burying it.** It converts a malformed decision into a flat book instead of a crash.
  That is the failure mode RULES warns about — a strategy that never ran looks identical to one with
  no edge. The tell to check first in the packet is **participation and mean gross exposure**: if
  they are at or near zero, this candidate did not run, and the correct response is to fix the
  parsing, not the economics.
- **F1 and F2 are not yet evaluated**, because this trial is what generates the evidence to evaluate
  them on. Per §6.2 they are reported before any *nomination*, and no nomination is being made here.
- **The next trial is the ablation, not a tune.** F2 is defined against the dispersion-deleted twin,
  so measuring it requires running that twin. That is not a new knob and not a widening of the
  surface — it is the control the preregistered falsifier already demands.

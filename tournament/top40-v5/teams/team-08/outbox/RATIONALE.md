# team-08 — slow-ladder per-contract time-series trend

**Family:** time-series trend. **Mandate:** the CTA transplant — per-contract, volatility scaled,
multiple lookbacks. **Phase:** refinement, working from `lane/feedback/t01.json` (the unmodified
organizer seed) and the sealed preregistration in `lane/scouting/THESIS.md`.

---

## 1. What the seed's packet actually says

The seed passed every structural gate and failed exactly three, all of them cost gates.

| passed | value | | failed | value |
|---|---|---|---|---|
| effective breadth | 21.37 (pass fraction 1.0) | | gross edge / turnover | 14.64 bps |
| mean gross exposure | 0.478 | | cost share of gross | 0.512 |
| participation | 1.0 active bars | | triple-cost return | −0.1035 |
| long / short exposure | 50.6 / 49.4 | | | |
| turnover band | 130.5 (inside) | | | |

Two independent routes recover the cost schedule from the packet, and they agree:

- from triple cost: `C = (net − triple)/2 = (0.0905 + 0.1035)/2 = 0.0970` → **7.43 bps** per unit turnover
- from density: `gross = 130.5 × 14.64bps = 0.1910`, `C = gross − net = 0.1005` → **7.70 bps**

So the charge is **≈7.4–7.7 bps per unit turnover at 1×** — essentially the 7.5 bps that THESIS §7.1
fixed as its accounting assumption, which is a useful confirmation that the preregistered cost model
was not naive.

The decisive reframing. Define the *break-even gross Sharpe at triple cost*:

```
S_required = 3 · c · turnover / volatility
```

| | seed (t01) |
|---|---|
| gross Sharpe delivered | 0.1875 / 0.1203 = **1.56** |
| gross Sharpe required at 3× | 3 × 7.43e-4 × 130.5 / 0.1203 = **2.42** |
| shortfall | cleared **64%** of its own bar |

**The seed does not have a weak signal.** A gross Sharpe of 1.56 on a 21-name book is a good trend
signal — it is above what THESIS §P6 predicted from Hurst/Ooi/Pedersen's ~0.4 per-market calibration.
It failed because it set itself a bar of 2.42 by trading at 130× turnover a year. Costs consumed
exactly half its Sharpe (1.56 → 0.78).

This is why the fix cannot be a parameter. `S_required` is linear in turnover, and turnover is set by
the *horizon at which the ladder places its risk*. Nothing else in the design moves it.

---

## 2. Diagnosis: two structural errors, neither of them a knob

### 2.1 My preregistered turnover control is unimplementable under this contract

THESIS §7.1 fixed a no-trade band of `0.10 × target weight`. A band is a **position-space** control:
it compares the target to the position currently held. `DecisionContext` carries exactly five
attributes and none of them is a position, and RULES.md forbids state that persists across decisions.
So the band cannot be written at all.

That is not an inconvenience, it is the governing constraint of the whole design. **Turnover cannot
be filtered out after the target is formed; it has to be designed into the signal.** Every map from
data to weight in `candidate.py` is therefore continuous — `tanh`, a median-based concentration cap,
a proportional net cap that approaches identity at its own boundary — so that the weight *path* is
smooth because the signal is smooth, not because trades are being suppressed. This also means nothing
in the book depends on a threshold crossing, which is what the organizer's small-perturbation
stability check is looking for.

### 2.2 Equal-weighting rungs equalises risk but not cost

Under a random-walk null the per-bar innovation of a rung-*L* z-score is `√(2/L)`. Across the eight
preregistered rungs:

| rung (8h bars) | 3 | 6 | 12 | 21 | 45 | 90 | 180 | 360 |
|---|---|---|---|---|---|---|---|---|
| √(2/L) | .816 | .577 | .408 | .309 | .211 | .149 | .105 | .075 |

The fast four carry **half the ladder's signal weight and 80% of its position innovation**
(2.110 / 2.650). Meanwhile edge per unit turnover scales as **√L**, while per-market Sharpe is roughly
flat in *L* across the 1–12 month band — that flatness is the Moskowitz–Ooi–Pedersen and
Hurst–Ooi–Pedersen result itself, not an assumption I am adding.

So an equal-weighted ladder is mis-specified in cost space by construction: the fast rungs are funded
by the slow rungs' edge and consume it. No transform, no band and no universe size repairs that,
because the defect is in where the ladder puts its trading, not in how the trading is executed.

Restricting to the declared `SLOW(5–8)` window predicts a turnover factor of
`(2.650/8) / (0.540/4) = 2.45×`.

---

## 3. What the candidate does

Per contract, and reading nothing else — no cross-sectional rank, no relative strength, no
market-wide state variable, and (per the §0 commitment I bound myself to before seeing data) **no
volatility gate, no drawdown control, no exposure throttle**:

```
z_L   = (log return over L bars − funding paid over L bars) / (σ · √L)
g     = mean over available rungs of tanh(z_L)
w_raw = g / σ                       # inverse-vol, relative weights only
w     = normalise → concentration cap → net cap
```

| element | value | status |
|---|---|---|
| ladder window `W` | `SLOW(5–8)` = {45, 90, 180, 360} bars ≈ {15, 30, 60, 120}d | declared Tier-1, 1 of 5 |
| transform `T` | `tanh` | declared Tier-1, 1 of 3 |
| breadth `N` | 30 | declared Tier-1, 1 of 3 |
| vol estimator `V` | EWMA of squared bar returns, com 180 (~60d) | declared Tier-2 |
| signal basis `B` | funding-inclusive total return | declared Tier-2 |
| cadence `R` | every bar | declared default |
| concentration cap | 3× median contract weight | fixed, THESIS §7.1 |

Three choices deserve their reasons stated rather than listed.

**The vol estimator is slowed to match the signal.** `σ` enters the weights, so *its* innovation is
turnover carrying no directional information at all. A 20-day vol estimate driving a 15–120 day
signal is a mismatch that generates pure cost. com 180 bars sits at the ladder's centre of gravity.

**Funding is inside the signal, not just the P&L.** THESIS §1.6 is the crypto-specific half of my
thesis: Binance's documented funding formula pays shorts ≈0.01%/8h by default at zero premium, so a
perpetual long carries a structural ≈11%/yr financing headwind that has no analogue anywhere in the
CTA literature. The tradeable return of a long *is* the price return net of funding, so that is what
the trend should be measured on. This is knob `B`, and it is emphatically **not** a carry signal —
funding never generates a position by itself (THESIS §5). It degrades to price-only on any
malformation of the funding frame rather than to an empty book.

**The universe rank uses a 90-day trailing median of quote volume.** A short-window rank makes names
oscillate across the rank-30 boundary and churn full positions in and out for no informational reason
— membership churn is turnover with negative expected edge. A long, robust window makes the
membership edge quiet.

**Why the book cannot silently vanish.** RULES.md warns that a strategy misreading the context
returns nothing and scores as a book with no edge. Because this design is strictly per-contract it
never builds a cross-symbol panel, so the positional-`RangeIndex` trap cannot arise: every read is
positional inside one symbol's frame. Timestamps are used only for the funding window, via epoch
integers that work for tz-aware, tz-naive and non-datetime columns alike, with an 8h fallback.

---

## 4. Who is on the other side

At a 15–120 day horizon the counterparties are, in descending order of how much of the transfer I
think they explain:

1. **Inventory hedgers.** Miners hedging production, treasuries and foundations hedging holdings,
   recipients of token unlocks, market makers laying off spot. They short into strength and buy into
   weakness for reasons unrelated to expected return. This is the classical MOP risk-transfer story
   and it is the counterparty best matched to the slow ladder's clock.
2. **Extrapolative demand arriving late.** Liu & Tsyvinski put crypto return predictability at a 1–8
   week horizon and identify investor attention as the channel. Binance's listing process is itself
   attention-selecting — perps get listed after a narrative catches — so the tradeable cross-section
   is populated with exactly the assets where late extrapolative demand is strongest. Crucially,
   **there is no valuation anchor**: nobody can compute a fair value for a token with no cash flows,
   so the corrective force that kills under-reaction in an equity index has no seat at this table.
3. **The cash-and-carry basis desk.** Long spot, short the perp, structurally short and completely
   indifferent to direction. They are *not* losing this trade — they are being paid by me, in
   funding, by exchange design. This is the one counterparty I can name from documentation rather
   than inference, and §3 now prices it into the signal instead of discovering it in the P&L.

**And one I have deliberately stopped trading against.** THESIS §1.4(d) named short-horizon liquidity
providers — Shen/Urquhart/Wang's channel, the intraday momentum manufactured by the liquidation
engine's forced, price-insensitive, momentum-aligned order flow. I believe that transfer is real. The
seed's packet says it does not clear a 7.4–22.3 bps schedule. Abandoning it is the substance of this
refinement, and §6 is written so that being wrong about it is visible rather than deniable.

---

## 5. Quantified prediction, stated before the packet returns

The redesign cuts the break-even bar by 2.45×: `S_required` falls from **2.42 to ≈0.99**. Since the
seed delivered 1.56, **the slow ladder needs to retain 63% of the seed's gross Sharpe to clear triple
cost.**

| quantity | seed | predicted |
|---|---|---|
| annualised turnover | 130.5 | **45 – 65** |
| gross edge / turnover | 14.64 bps | **26 – 40 bps** (break-even 22.3) |
| cost share of gross | 0.512 | **0.19 – 0.29** |
| triple-cost return | −0.103 | **positive** |
| effective breadth | 21.4 | 18 – 24 |
| long / short exposure | 50.6 / 49.4 | 35/65 – 65/35 (wider than the seed; see §8) |

---

## 6. What would falsify this

### F-R — the refinement falsifier

The claim is that the seed's edge lives at the slow end and is being consumed by fast-rung turnover.
The next packet discriminates three outcomes, and I commit to all three readings now:

- **Turnover falls into 45–65 and density clears ~22 bps.** The diagnosis holds.
- **Turnover falls as predicted but density does not move** — i.e. gross Sharpe fell in proportion to
  turnover. Then **the edge was in the fast rungs**, the √L argument is wrong for this universe, and
  time-series trend in Binance perpetuals is a microstructure effect that does not clear this cost
  schedule at any horizon. That is the family failing the cost gates, not a parameter miss, and per
  the THESIS §6 stopping rule I will report it rather than mine the grid for a passing cell.
- **Turnover does not fall into the predicted range.** Then my model of where the seed's turnover
  comes from is wrong, and the residual is being generated by the vol estimate, universe churn, or
  the organizer's risk-unit rescale — each separable from the next packet.

### F-C — the mandate falsifier, as assigned

> If no lookback horizon produces positive average returns per contract, time-series trend does not
> persist in this universe.

**Not currently breached.** The seed's gross return of 0.187 at a gross Sharpe of 1.56 establishes
that some horizon in the ladder is positive. What is in question is not whether the premium exists
but whether it survives being paid for.

### F-A and F-B — what I could not run, stated plainly

THESIS §6 preregistered F-A (a 1,000-path sign-scrambled block-bootstrap control, to establish that
the *sign forecast* adds something above the organizer's imposed risk unit — the test Kim/Tse/Wald's
critique demands) and F-B (standalone per-rung net returns, requiring a contiguous positive block of
three adjacent rungs).

**I cannot execute either.** This phase returns one aggregate metric packet per trial, not a backtest
harness; there is no way to construct a bootstrap distribution or a per-rung decomposition from it,
and twelve feedback-driven trials cannot substitute. I am recording this as an unmet preregistered
commitment rather than quietly substituting a weaker test that I *can* run and calling it F-A.
Consequently, **if this book makes money I am not entitled to claim it for the trend family** — the
Kim/Tse/Wald alternative (that the result is the imposed risk unit plus an inverse-volatility tilt)
remains open and untested. The §0 no-vol-gate commitment is what keeps that question at least
honest: this book has no volatility-conditional exposure anywhere, so whatever it earns, it does not
earn from disguised volatility timing.

---

## 7. Declared deviations from the sealed parameter surface

THESIS §7.5 requires that moving a fixed default is counted and reported rather than quietly amended.
Five, of which two are forced by the contract:

1. **No-trade band `D` not implemented — forced.** §7.1 fixed 0.10 × target weight. Position-space
   control is impossible here (§2.1). Turnover control moved to signal space.
2. **Tier-2 knobs used without completing Tier 1 — forced.** §7.3 made Tier 2 contingent on F-A/F-B
   passing and on a Tier-1 grid winner; §7.4 fixed the selection rule. No grid can be run (§6). One
   cell was selected by mechanism reasoning instead. This *lowers* the effective trial count well
   below the declared 81 rather than raising it, which helps the deflation argument — but it is a
   departure from the declared selection rule and is recorded as one.
3. **Net-exposure cap at 0.20 added.** Not in §7.1. It is constraint hygiene mirroring the hard
   |net| ≤ 0.25, applied smoothly by me instead of bluntly by the evaluator, which would impose the
   same reduction anyway. It shrinks the dominant side proportionally and approaches the identity at
   its own boundary, so it introduces no jump turnover. Note what it does **not** do — see §8.
4. **Funding drag approximated** by a trailing mean rate per settlement scaled to a per-bar drag,
   rather than an exact per-rung sum. Chosen for robustness; the smoothing is mild and, if anything,
   less noisy than the exact quantity.
5. **Minimum history fixed at 200 bars.** §7.1 said "sufficient history" without a number.

---

## 8. Where this is exposed

- **Effective breadth is my main exposure among the gates I currently pass.** `tanh` weights times an
  inverse-vol spread put my estimate at 18–24 against the seed's 21.4. The mitigating read: a pass
  fraction of 1.0 with a *median* of 21.37 means the threshold sits below the realised *minimum*, so
  it is likely well under 15. The concentration cap at 3× median is what holds the top of the book
  down and is doing real work here, not decoration.
- **Slow trends are market-directional, and the net cap does not rescue the "both sides used" gate.**
  With ~0.6 average pairwise crypto correlation (Man Group), the raw slow book will be one-sided more
  often than the seed's near-perfect 50.6/49.4. It is worth being exact about what the cap buys.
  After it binds, `net = 0.20` and `gross = 0.20 + 2·short_sum`, so the long share is
  `(0.20 + short_sum)/(0.20 + 2·short_sum)`. That tends to 0.5 only when the minority side carries
  real mass: at `short_sum = 0.3` the split is 62/38, and in a cross-section with no shorts at all it
  is 100/0 with gross collapsing to 0.20. So the cap enforces the *net* constraint and nothing more —
  it is not a both-sides-used guarantee, and I am not claiming one. The gate is protected only by the
  cross-section genuinely containing both signs, which the seed's 50.6/49.4 suggests it does over the
  window but does not promise bar by bar. This is the second real exposure after breadth, and both
  are consequences of the same fact: slowing the ladder makes the book more market-directional.
- **A turnover-band floor.** 130.5 was inside the band; 45–65 may not be. If it fails low, that is a
  clean, diagnosable result.
- **THESIS §3.1 remains the honest failure regime:** a high-realised-volatility, zero-net-drift range.
  Slowing the ladder does not defend against chop — it lengthens the period over which chop can bleed.
  Owning a lookback straddle means paying the premium in whipsaw, and that is the trade.
- **THESIS §3.4 is unrepaired and unrepairable.** The CTA result stands on a tripod — small
  per-market Sharpe, made investable by aggregating many weakly-correlated markets. Crypto supplies
  one leg at ~0.6 correlation. A 30-perp book is not 30 bets. No choice available in this lane
  restores that, and the correct expectation for this family here is therefore modest.

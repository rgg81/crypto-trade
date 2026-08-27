# RATIONALE — team-09 discovery candidate

**Mandate:** channel breakout gated on participation, so the book does not buy every false break.
**Family:** time-series trend. **Phase:** discovery — this is the baseline I want to be able to
diagnose, not the best book I can imagine.

---

## 1. What the candidate does

Per symbol, per decision, recomputed from scratch off past-only bars:

1. **Channel.** Mark every bar whose close prints above the prior 42-bar close high (`+1`) or below
   the prior 42-bar close low (`-1`). 42 bars of 8h = 14 days, the mid of my declared grid.
2. **Gate.** At each break, score directional participation
   `D = z(quote_volume) · max(0, d · z(taker_buy_share))`, where both z-scores are robust
   (median / MAD) over the symbol's **own prior 63 bars** and `d` is the break direction. A break is
   *confirmed* when `D ≥ 1.0`.
3. **State.** Position sign = direction of the most recent **confirmed** break. A break in the
   opposite direction **always** closes the position, confirmed or not.
4. **Universe.** Symbols need 107 bars of history and must clear the bottom quintile of the mounted
   universe by trailing 126-bar median quote volume.
5. **Book.** Equal weight inside each side. Net tilt = signal breadth `(n_long − n_short)/n`, clipped
   to ±0.20; the rest of the tilt is neutralised across the two sides. Gross 1.0 pre-cap; the whole
   book is scaled down if any name would exceed 0.10, rather than clipping individual names.

**Asymmetric gating is the whole design.** The gate governs *entries* only. Requiring participation
to exit as well would leave the book long through an unconfirmed collapse — the failure mode the
mandate is supposed to remove, reintroduced through the back door.

## 2. The mechanism

A channel break is a **mixture of two populations** and the naive breakout rule buys both:

- **Informed repricing** — someone with a view crosses the spread, price leaves the range, and the
  move continues because the information is not yet impounded. Llorente–Michaely–Saar–Wang (2002):
  returns driven by speculative trade **continue**.
- **Inventory shock** — a large risk-sharing order pushes price out of the range against a
  risk-averse liquidity provider who must be paid to warehouse it. Price reverts as the inventory is
  worked off. Campbell–Grossman–Wang (1993): autocorrelation *declines* with volume in this branch.

Blume–Easley–O'Hara (1994) is the licence for conditioning at all: volume carries information about
the **precision** of a signal that price alone cannot convey. So the gate's job is not "was there a
lot of volume." Karpoff (1987) established that volume tracks the **magnitude** of the price change,
so a high-volume break is partly just a large break, and gating on raw volume risks re-discovering a
volatility filter under a different name. That is why the score is a **product**: abnormal
participation *and* aggression aligned with the break. `taker_buy_quote_volume` is the field that
makes this answerable — it identifies who crossed the spread. Passive volume is the side being run
over.

I express trend as a **channel break** rather than a return sign because George–Hwang (2004) show
nearness to a running extreme dominates raw past returns as a momentum predictor and, unlike raw
momentum, its forecast returns **do not reverse long-horizon**. The break selects the subset of trend
events where the underreaction story is cleanest.

## 3. Who is on the other side

1. **Levered directional retail** — long into strength, liquidated into weakness, and paying funding
   for the privilege of being long a trending perp. Their forced, price-insensitive exits *are* the
   continuation. This channel does not exist in spot.
2. **Inventory-constrained market makers** — they lean against the break and must be compensated.
   They are precisely why *ungated* breakouts revert: they win the low-participation breaks. The gate
   is an attempt to stop trading against them when they are right.
3. **Late discretionary and allocator flow** — arrives after the break and completes the repricing.

I am on the informed-repricing side and I am paying carry to be there. That cost is why the gate has
to earn its keep: selectivity is not a free preference, it is how I avoid paying funding on breaks
that were never going anywhere.

## 4. Why the book is two-sided

A single-asset-class trend book cannot satisfy `|net| ≤ 0.25` at gross 1.0 while staying one-sided.
Rather than let the engine clamp an all-long book into a small one, I keep the *maximum permitted*
directional tilt — signal breadth clipped to ±0.20 — and neutralise the remainder across sides. When
the universe is genuinely mixed the book is near cross-sectionally neutral; when it is uniform the
book carries the full allowed tilt and the minority side is levered up to balance it. The
scale-the-book-not-the-name cap keeps that balance intact under the 0.10 constraint. Both sides are
therefore used on exposure by construction, at ≥40% of gross each whenever both sides are non-empty.

## 5. What would falsify this

Preregistered in `lane/scouting/THESIS.md` §4, restated here in operational terms.

- **F1 (primary).** Against the **identical geometry with the gate off**, the gated book must clear
  **both** +0.15 Sharpe and +2.0pp continuation rate. Either leg fails ⇒ the gate is falsified and I
  nominate the plain ungated breakout, reporting the mandate as not supported.
- **F2 (redundancy).** Same geometry with a **selectivity-matched trailing-realised-volatility**
  filter admitting the same fraction of breaks. The gate must beat that control by +0.10 Sharpe. This
  is the test I most expect to lose — Karpoff predicts it. If F2 fails while F1 passes, what I found
  is a volatility filter, and I will say so.
- **F3 (sign).** I committed to **continuation** before seeing data. If high-participation breaks
  revert while low-participation breaks continue — the Campbell–Grossman–Wang branch dominating in
  perps — that is a falsification. **I will not flip the sign and re-nominate the inverted rule.**
- **F4 (placebo).** A randomised gate at matched acceptance rate. If the real gate does not beat it
  by more than the placebo's own dispersion, F1 is void.
- **Not a rescue.** "There were no trends in the sample" is only admissible if the *ungated* book
  underperformed for the same reason. If ungated worked and gated did not, the mandate failed.

**Diagnostics I need back to run F1 correctly:** the ungated control is `GATE_THRESHOLD = -inf`, not
`0.0`. Because `D = z_v · max(0, d·z_i)` is exactly zero whenever aggression is counter-aligned,
`θ = 0` rejects only above-normal-alignment / below-normal-volume breaks — it is a third gate, not
the null. The next trial is that control at identical geometry.

## 6. What I deliberately left out at discovery

Every one of these is on the declared surface and none of it is in this candidate: gate statistic
choice beyond the `D` composite, the soft-scaler gate mode, multi-bar confirmation `k`, the exit
fraction `f`, the funding crowding veto, and any gross-shaping that would let the book shrink when
few breaks are confirmed. The gate here expresses itself purely through *which names are in the
book*, never through book size. That is the one thing I most want a clean read on before elaborating.

## 7. Known attenuation, recorded now rather than retrofitted

- **8h bars.** Breaks happen intrabar. I see the bar's aggregate participation, not its sequence, so
  I cannot separate volume that arrived *before* the break from volume that arrived *after*. This is
  a genuine attenuation of the gate and the reason my prior on its contribution is +0.2–0.4 Sharpe
  rather than something heroic.
- **No open interest, no liquidation feed, no book.** The forced-flow continuation channel is real
  but unobservable here; taker flow is the only proxy. If the gate works I cannot prove liquidations
  were why.
- **Volume integrity.** Cong et al. (2023) find wash trading averages >70% of reported volume on
  unregulated venues. Every participation statistic is normalised against the symbol's **own**
  trailing distribution and never against a cross-sectional volume level.
- **Decay.** He et al. report perp deviations diminishing over time; I expect a weaker effect in the
  recent part of any sample and I am saying so before seeing one.

## 8. Contract compliance

Stateless across decisions; no RNG, network, subprocess, filesystem, `eval`/`exec`; no embedded
fitted parameters or data. Scale-invariant (channel uses close comparisons only; participation uses
per-symbol ratios). No absolute dates, no hard-coded symbols, no volatility targeting — the sizing is
breadth and the engine's risk unit, nothing else. `sum|w| ≤ 1.0`, `|sum w| ≤ 0.20`, `|w| ≤ 0.10`
enforced by construction, with a final defensive rescale. Every eligible symbol is returned with an
explicit target so a flat name is unambiguously flat rather than a hold.

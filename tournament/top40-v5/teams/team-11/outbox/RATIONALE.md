# team-11 — participant mix via average trade size (refinement)

**Family:** microstructure and participation.
**Mandate:** average trade size as a retail-versus-institutional proxy.
**Preregistered thesis:** `lane/scouting/THESIS.md`, sealed 2026-08-26.

---

## 1. Diagnosis: what t01 established, and what it did not

`t01` is the unmodified organizer seed, not an expression of my mandate. It carries no information
about whether average trade size predicts returns. It carries a great deal of information about the
cost environment, and that is what I have used it for.

The seed passed every *portfolio* gate — effective breadth 20.8, mean gross 0.72, long/short
exposure 0.547/0.453, active on every bar — and failed exactly four: `turnover_ceiling`,
`gross_edge_density`, `cost_share`, `survives_triple_cost`. Those four are one failure wearing four
labels. The packet prices it exactly:

| quantity | derivation | value |
|---|---|---|
| cost at 1× | `(0.470784 − 0.210326) / 2` | **13.02 % of capital / yr** |
| cost per unit one-way turnover | `0.1302 / 266.56` | **4.885 bps** |
| gross price edge | `−1.1432 bps × 266.56` | **−3.05 % / yr** |
| funding + residual drag | `−21.03 % + 13.02 % + 3.05 %` | **≈ −4.97 % / yr** |

Two consequences follow, and they are the whole of this refinement.

**(a) The triple-cost gate is a statement about edge density, not about turnover level.** Net return
at 3× is positive only if

```
gross_edge_bps_per_turnover  >  3 × 4.885  =  14.65 bps
```

That threshold does not move when turnover moves. What moves is how attainable it is.

**(b) At the seed's turnover it is unattainable by anything.** 266.6 turns × 4.885 bps × 3 =
**39.1 % of capital per year** in cost alone. At the ~11 % annualised volatility the common risk
unit imposes, clearing that requires a gross Sharpe above 3.5. No 8-hour microstructure signal has
ever had one. A book that rebalances 1 095 times a year is not a book with a tuning problem; it is a
book whose decision frequency is not affordable at any parameter setting.

So the refinement is structural. **The holding period, not the signal, was the broken part.**

## 2. The turnover budget, and the horizon it implies

For a conviction smoothed over `m` bars and re-expressed every `M` bars, the per-rebalance change in
the weight vector scales like `sqrt(M/m)` of typical position size, and there are `1095/M`
rebalances per year. With mean gross ≈ 0.72 and the signed-square-root weight map (which halves
relative weight moves), annualised turnover ≈ `788 / sqrt(M · m)`.

| M (hold) | m (smooth) | est. turnover | 3× cost / yr | gross Sharpe needed to break even |
|---|---|---|---|---|
| 1 | 9 | 263 | 38.5 % | ~3.5 — the seed's regime |
| 1 | 45 | 117 | 17.2 % | ~1.6 |
| 9 | 45 | **39** | **5.7 %** | **~0.72** |
| 12 | 45 | 34 | 5.0 % | ~0.63 |
| 18 | 45 | 26 | 3.8 % | ~0.49 |

I chose `M = 9` (3 days, 122 rebalances/yr) and `m = 45` (15 days). It is the fastest point on that
table whose cost bill a plausible cross-sectional edge can actually pay, and it keeps 122 explicit
book refreshes per year rather than retreating to a near-static portfolio. Going slower is cheaper
but buys freshness I do not want to give up, and pushes toward a turnover *floor* whose location I
cannot see.

Estimated landing zone: turnover 25–55, an order of magnitude below the level that broke the
ceiling, and edge density improved by the same factor for any given per-bar edge.

**Turnover is spent, not merely reduced.** Between rebalances the strategy returns `None`, which the
protocol defines as holding current quantities. Returning an explicit mapping every bar would look
identical in weights but would force the evaluator to re-impose constant mix against price drift
(~14 turns/yr) *and* to re-scale the book each time its ex-ante risk unit moved (~30 turns/yr) —
roughly 45 turns of pure cost buying zero information. `None` is the only way to hold without paying
for it.

## 3. The mechanism

Every 8h bar publishes quote volume `V` and trade count `N`. Average trade size is `S = V/N`, and

```
log S  ≡  log V  −  log N          (exact)
```

`N` is the arrival clock (Ané–Geman). `S` is not a second measurement of volume; conditional on the
clock it says how much notional rode on each arrival — the *composition* of trading rather than its
*scale*. A volume factor loads on the `(+1,+1)` direction in `(log V, log N)` space. This mandate
lives on `(+1,−1)` and nowhere else. That is why "is it just volume?" is a geometric question with
an answer rather than a rhetorical one.

`S` is unsigned: large prints do not say "up". Turning it into a direction needs a signed flow
variable, and this dataset supplies exactly one, which is also a participation variable:

```
OFI = 2 · (taker_buy_quote_volume / quote_volume) − 1        ∈ [−1, +1]
```

The traded conviction is the product of the two, each as a within-asset trailing z-score smoothed
over 45 bars and winsorised at ±3 SD:

```
c_i = clip( z_flow_i × z_size_i , ±3 )
```

with the sign pre-committed positive in the sealed thesis. All four quadrants are economically
coherent, which is the test that it is a mechanism and not a fitted sign:

| trade size | taker flow | reading | position |
|---|---|---|---|
| large | buying | professional accumulation, sliced but not retail-sized | long |
| large | selling | professional distribution | short |
| small | buying | retail chasing a rising price | short |
| small | selling | retail capitulation | long |

The property that distinguishes this from any volume book: **when a name's average trade size sits
at its own trailing median, `z_size = 0` and the position is zero no matter how large `V` is.**

## 4. Who is on the other side

The leveraged retail taker on Binance USD-M perpetuals, and the argument that this counterparty is
structurally rather than incidentally present has three legs, all in §1.3 of the sealed thesis:

1. **Documented to lose.** BIS Bulletin 69 (Cornelli, Doerr, Frost, Gambacorta 2023): through
   Terra/Luna and FTX, "large and sophisticated investors [were] selling and smaller retail
   investors buying"; a majority of crypto-app users across 95 countries lost money on bitcoin.
2. **The transfer is explicitly priced on this contract.** Binance BTC perpetual funding averaged
   ~13.7 % annualised over 2020–2025 against a ~3.1 % bill rate — ~10.6 pp paid by longs to shorts,
   roughly 3× the CME bitcoin futures financing spread. A population that persistently pays
   double-digit carry to be long is not, by revealed preference, the informed side.
3. **It is not arbitraged away.** The professional leg requires balance sheet and tolerance for
   liquidation risk on the short perp; and the retail side is a *flow*, replenished with every price
   rise, not a stock that can be exhausted.

The book therefore expects to be systematically short the retail-crowded names — the ones with small
prints and net taker buying — which are the same names that carry high positive funding. **Prediction
worth checking in the next packet: this book's funding contribution should be small or positive, not
the seed's ≈ −5 %/yr.** If a net-zero, mechanism-driven book still bleeds 5 %/yr to funding, the
sign prior has the crowded side backwards. I have not built a funding overlay — that is a different
family and my anti-surface forbids it — but funding is a clean, unfitted read on whether the
counterparty story is right.

## 5. Portfolio construction, and which gate each piece answers

- **`sign(d)·sqrt|d|` on cross-sectionally demeaned conviction** — *effective breadth.* `c` is a
  product of two z-scores: leptokurtic, with a density that diverges at zero. A linear weight map on
  it gives effective breadth ≈ 0.40·N (≈ 16 on a 40-name universe), below the 20.8 the seed
  achieved. The signed square root lifts it to ≈ 0.72·N (≈ 29). The map is monotone and odd, so it
  preserves the ordering *and* the zero — it is portfolio construction, not a re-specified signal.
  It also bounds the damage a single fabricated or wash-traded print can do, which is failure mode
  #2 in the sealed thesis and the one I cannot test with this data.
- **Exact net neutralisation, then gross normalised to 1.0** — *both sides genuinely used, mean gross
  exposure.* Long and short exposure share land at 0.50/0.50 by construction rather than by luck,
  and the market beta that would otherwise fight the common risk unit is removed.
- **`|w| ≤ 0.09`, iterated, with a final bind-whichever-constraint rescale** — the 0.10 cap and the
  0.25 net cap hold with margin under every universe size, including degenerate ones.
- **z-scores within asset, never levels, never raw cross-sectional ranks** — BTC prints are orders of
  magnitude larger than DOGE prints, and average trade size has trended up with institutional
  onboarding. A level or raw-rank sort would be a size factor and a time trend wearing a
  microstructure costume (failure modes #3 and #4). Fixed by preregistration; unchanged here.
- **Cadence counter = `max(len(bars[s])) % 9`** — data-derived, so it is invariant to calendar
  shift, symbol pseudonymisation and magnitude rescaling, and depends on no absolute date.

Invariance checks, deliberately: no `decision_time` is read anywhere; no RNG; no instance state; only
rows present in the frame are read; `log S` shifts by a constant under price rescaling and the
trailing z removes it, while `OFI` is a ratio and is invariant outright; symbols are sorted only to
fix array order, and every statistic used is order-independent. I never build a cross-symbol panel —
each symbol is reduced to one scalar in its own frame — so the `RangeIndex` alignment trap cannot
produce a silently empty book here.

## 6. Deviations from the sealed parameter surface, stated plainly

Three, and I would rather name them than let them read as undeclared search.

1. **Smoothing `k = 45` bars.** The declared surface (§4.1, knob 3) offered `{1, 3, 9}`. 45 is
   outside it. It was not chosen by performance — I have no performance result for this mechanism.
   It is the solution of the turnover-budget equation in §2 given the cost per unit turnover that
   t01 measured. Every other value in the declared set fails `turnover_ceiling` arithmetically,
   before any data is consulted.
2. **Rebalance every 9 bars, not every bar.** §4.3 fixed "rebalance every bar, on the funding grid."
   Same reason, same arithmetic. I am recording this as a broken preregistration rather than
   pretending the surface anticipated a cost gate, because it did not.
3. **Horizon.** §4.4 forbids "re-specification of the forecast horizon after seeing a result." I am
   doing it, and the honest accounting is: the result I saw was the *seed's* structural gate failure,
   not any result about `S`; I did not search horizons and rank them by Sharpe, I read a single
   horizon off a cost constraint; and the literature carrying my sign prior — Hvidkjaer's
   small-trade imbalance predicting returns for *up to two years*, Barclay–Warner stealth trading
   accumulating over days and weeks, BIS retail distribution over quarters — is itself a
   multi-week phenomenon. The 8-hour clock came from one citation (the Quarter-Hour Effect paper's
   8–12h peak in order-imbalance forecasting power), and it is the citation the cost gate has ruled
   out. A reader is entitled to discount this candidate for the deviation. I would rather be
   discounted than quietly rewrite §4.

Unchanged and unsearched: the size primitive `quote_volume / trade_count`; ±3 SD winsorisation;
positive sign on `OFI × Z`; global parameters with no per-asset fitting; the universe exactly as
provided; the hygiene rules (drop `N = 0` or `V = 0` bars, discard a listing's first 30 bars). The
anti-surface holds in full: no ML, no regime switching, no conditional sign flips, no funding
overlay, no volatility targeting, no asset selection by performance.

## 7. What would falsify this

The sealed falsifiers F1–F4 are regression and permutation tests I cannot run in this phase — no
shell, no data mount, no way to fit a pooled panel or draw a null. I am not going to claim I ran
them. What the returned packet can falsify, stated before I see it:

1. **`gross_edge_bps_per_turnover ≤ 0`.** The mechanism produced no gross edge at a 3-day horizon.
   The expression is dead and the horizon deviation in §6.3 bought nothing. This is the primary
   falsifier and it is not rescuable by re-tuning `m` or `M`, which change cost, not sign.
2. **Density positive but below ≈ 14.65 bps.** The mechanism is real but too weak to clear its own
   trading costs at 3×. That is a genuine finding — an uneconomic edge — not a tuning target.
3. **Turnover lands outside 20–70.** My model of how the weight vector moves is wrong, which means
   §2's whole budget calculation is wrong and every parameter derived from it is unsupported.
4. **`active_bar_fraction` collapses toward 0.11 with a participation failure.** Then `None` is
   scored as non-participation rather than as holding, and the fix — preregistered here so it cannot
   later look like a rediscovered result — is to return an explicit mapping every bar whose weights
   are the *passively drifted* block weights, tracked from closes, so the mapping is submitted every
   bar while the trade is still only every 9th. I would spend a trial on that mechanically, with no
   change to the signal.
5. **Funding drag ≈ the seed's −5 %/yr on a net-zero book.** §4's counterparty story has the crowded
   side backwards.

What I will not accept as a rescue: reinterpreting `S` as a volatility or liquidity signal,
substituting trade count as the finding, flipping the sign in the tail to survive the liquidation
channel (failure mode #5), or selecting assets on performance. If the mandate is falsified, the
falsification is the result and the unmodified seed is what I nominate.

**Trial economics, stated up front.** If I am given a further slot, it goes to F2 — the identical
pipeline with `z(log V)` and `z(log N)` substituted for `z(log S)`. That is the control that decides
whether this lane found participant mix or merely re-found volume, and it is worth more than any
parameter I could move.

## 8. Expected metric profile

Written before the packet, so the packet can contradict it: turnover 25–55; median effective breadth
20–30; mean gross exposure 0.6–1.0; long exposure share ≈ 0.50; `active_bar_fraction` ≈ 1.0 (positions
persist through the holds); cost share an order of magnitude below t01's; and the 1× → 3× Sharpe decay
roughly a seventh of the seed's, because the cost bill is roughly a seventh the size.

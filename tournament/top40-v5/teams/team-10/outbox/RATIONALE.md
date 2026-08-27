# team-10 — taker-flow pressure · discovery candidate

**Configuration:** `N = ratio`, `L = 3`, `W = 90`, `C = none`, `X = ts z + cross-sectional demean`.
One cell of the 128-point surface declared in `scouting/THESIS.md` §5.1. Nothing outside that surface
is varied, and nothing inside it has been fitted — there is no data in this lane yet.

---

## 1. What the book is

At every decision boundary, for each eligible symbol with a full standardization window:

1. **Aggressor imbalance per bar.** `imb_t = (2·taker_buy_quote_t − quote_volume_t) / quote_volume_t`,
   in `[−1, +1]`. Bars with no trade contribute `0` (§5.3.8).
2. **Accumulate** over `L = 3` bars — one calendar day.
3. **Standardize** against the trailing `W = 90` bar distribution of that same accumulated series,
   strictly trailing, `min_periods` full. Winsorize at ±3σ (§5.3.3).
4. **Demean across the cross-section** at that timestamp.
5. **Map linearly** into weights: `w ∝ +z̃`, normalized to gross 1.0, per-symbol cap water-filled at
   0.10, residual net trimmed. No thresholds, no gates, no regime switches, no stops.

Rebalance every bar. Symbols without 92 bars of history are excluded — that is the `min_periods` rule,
not a liquidity screen.

## 2. The mechanism

Binance reports the aggressor side per kline. It is not inferred by a tick rule or by bulk volume
classification, so the measurement-error haircut that sits under every equity order-flow-imbalance
result is zero here [C9, C10]. That is the structural reason this lane is worth running at all.

Every taker buy is matched by a maker sell. `imb_t > 0` is therefore an accounting statement, not a
mood reading: **the intermediary sector absorbed `imb_t · quote_volume_t` of unwanted short inventory
during that bar.** The signal is a direct read on an inventory shock imposed on liquidity providers,
in the direction it was imposed.

That shock resolves two ways, and they point opposite (§1.2). Uninformed immediacy demand is paid for
with a price concession that reverts — fade it. Informed flow does not revert, it continues — follow
it. Aggressor imbalance is a mixture of the two, so its unconditional sign is not a constant. The
mandate's phrase "where the pressure resolves" *is* the question of which component dominates.

**This candidate deliberately does not answer that question.** It is the `C = none` corner: the
unconditional signal, sign preset to *follow*, because Kim & Hansen (2026) is the only published
result matched to this venue, this contract family and this horizon, and it finds taker-initiated
imbalance predicting returns with strongest effects at 4–12 hours [C1]. The 8h bar sits at the centre
of that window. The three conditioners that are supposed to resolve the mixture — absorption, funding,
composition — are declared in §5.2 and held back for later phases, because a conditioned book I cannot
diagnose is worth less than an unconditional one I can.

### Why this horizon is not arbitrary

Funding settles at 00:00/08:00/16:00 UTC and the 8h kline is published on the same grid [C8, C9]. The
bar is one full cycle of the market's own inventory-financing mechanism. `L = 3` spans exactly all
three daily settlements, which also means the signal cannot be a single-stamp calendar artifact by
construction — the §4.1 tripwire is closed mechanically rather than by inspection.

### Why cross-sectional demeaning

The mandate is about *relative* pressure — who is being pressed harder than whom. Demeaning also makes
the book two-sided by construction, which is what the exposure-side gates measure, and keeps net
exposure near zero without me touching the organizer's risk unit.

## 3. Who is on the other side

Mechanically, resting limit orders. Economically:

- **Market makers and HFT desks**, earning spread and the maker fee advantage, who warehouse
  uninformed flow and flee informed flow.
- **Cash-and-carry basis desks**, structurally short the perp against spot to harvest funding, and
  therefore the natural absorber of taker buy pressure. He et al. show this sector is balance-sheet
  constrained and that the constraint is common across coins [C7].
- **Delta-hedging desks**, whose perp leg is a hedge and not a view.

The aggressor side skews the other way: leveraged directional traders for whom the perpetual is the
cheapest available leverage and who need to be filled *now*. Binance taker fees (~0.05%) are strictly
worse than maker fees (~0.02%); anyone appearing in the `taker_buy_*` field **chose** to pay a premium
for speed over price. That revealed preference is the economic content of the signal.

When this book follows an aggressor imbalance, it is pricing in information the maker sector also sees
but cannot fully requote against inside an 8h window, and it collects an information rent. Either way
the payment comes from the same leveraged taker.

## 4. What would falsify it

The preregistered falsifier (§3) is an **incremental-information** test, not a Sharpe test, and it is
aimed at the failure mode I consider most likely: taker-buy share and the same bar's return are
near-mechanically linked, so a raw flow signal can be a momentum or reversal signal in a flow costume.

- **F1** — residualized against contemporaneous return, the `L` lagged returns, and contemporaneous
  `log(quote_volume)`: `|IC| < 0.010` or Newey–West `t < 2.5` ⇒ falsified.
- **F2** — if orthogonalizing against that control set destroys more than half the forward information
  (`|IC(s̃)| < 0.50·|IC(s)|`) ⇒ falsified even if F1 passes.
- **F3** — sign of `IC(s̃)` must agree across three contiguous equal slices of the visible window.

I expect **F3 to be the hardest for this particular candidate**, and I am saying so before the packet
arrives. The whole thesis is that the *unconditional* sign is a mixture and only the *conditioned*
signal has a stable sign. A `C = none` book failing F3 is evidence *for* the conditioning programme,
not against the family. A `C = none` book failing **F1** is different — that is the family itself
coming apart, and it is the outcome Kim & Hansen's own two-stage decomposition warns about: by 8–12h
most of what imbalance knows may already be spanned by observable price-volume state [C1].

### Tripwires on a *passing* result

- Residualized `|IC| > 0.10` at 8h on a public field ⇒ my first hypothesis is lookahead, not alpha.
- If returns plus `quote_volume` alone reproduce ≥80% of the IC, the aggressor field is not doing the
  work [C4].
- If dropping the single largest-contributing symbol sinks pooled IC below F1, this is one asset's
  history, not a family.

### Expected magnitude

Small and conditional. The immediacy premium is competed down, not arbitraged away, but this is the
most capacity-constrained, fastest-decaying family there is, and CVD is a retail charting staple. **A
large unconditional edge here is a bug report, not a result.**

## 5. What this candidate is not

- Not vol-targeted. Gross is constant at 1.0 and the organizer's ex-ante risk unit governs.
- No fitted parameters, no embedded data, no persistent state, no RNG, no symbol identity, no date
  literals. The signal is a ratio of a ratio, so it is invariant to price and volume scale.
- Not residualized in-book. Residualization is my *test* (§3), not a declared knob (§5.1); trading a
  residualized signal would be outside the sealed surface.
- Not selected on anything. This is the first candidate of the lane and no result has been observed.

## 6. What the next trial depends on

Strictly the packet, and strictly through the falsifier:

- F1 fails ⇒ report the mandate falsified and nominate the unmodified seed (§3, commitment on failure).
- F1 passes, F3 fails ⇒ exactly the predicted signature. Move to the conditioners `absorption`,
  `funding`, `composition` with signs already preset in §3, and test whether conditioning stabilizes
  the sign.
- F1 and F3 pass ⇒ check F2, then vary `L` and `W` inside the declared grid and check turnover against
  the cost model per §4.5.

Signs are preset by mechanism throughout. If the data prefer the opposite sign, that is a falsification
of this thesis, not a parameter to flip. Trial count for deflation purposes is the declared **128**
regardless of how many cells are charged.

*Citation tags [C1]–[C13] refer to `scouting/THESIS.md` §6.*

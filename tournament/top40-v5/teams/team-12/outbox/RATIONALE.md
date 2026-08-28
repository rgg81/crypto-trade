# team-12 — volume-shock events — nomination

**Nominated:** a dislocation-conditioned book over extreme quote-volume bars. Sealed thesis §4.2
Stage-A cell `{state axis = Axis A × Axis B}`, written continuously, at `L = 30`, direction = the
event-bar return, funding gate off, held over a 10-bar overlapping window.

**One sentence:** on an extreme quote-volume bar, the part of the price move that was *paid for in
impact* — a lot of price, from many small prints, per unit of volume — is inventory pressure and
reverses; the part that was *absorbed* — little price, from few large prints, per unit of volume —
is patient size and does not owe anybody a rebate.

---

## 1. What the evidence actually was, and what it was not

`t01.json` and `t02.json` are byte-identical except for the three characters of the trial ID. I
verified this field by field. That has one unavoidable consequence: **I hold one distinct result,
not two, and I cannot tell whether it belongs to the organizer seed or to my discovery candidate.**

So I have partitioned it, and I want to be explicit about the partition because the whole
nomination rests on it:

**I treat it as structural evidence.** `median_effective_breadth` 2.0, `breadth_pass_fraction`
0.169, `active_bar_fraction` 0.528, `mean_gross_exposure` 0.265, `annualised_turnover` 149.7,
`cost_share_of_positive_gross` 2.49e11. Those describe the *shape* of a book, and the shape is the
same whichever candidate produced it. Six gates failed and every one of them is a shape failure.
`cost_share` at 2.5e11 is not a cost problem — it is arithmetic reporting that positive gross edge
was approximately zero, so costs were an unbounded multiple of it.

**I do not treat it as sign evidence.** `gross_edge_bps_per_turnover` of −7.29 is tempting to read
as "the drift/reversal assignment is backwards, flip it." I decline. A book with a median
effective breadth of **two names**, active on 53% of bars, is not a cross-section; it is a pair of
coin flips repeated 400-odd times. Sharpe −2.16 on that is not a measurement of a cross-sectional
state mechanism, and flipping a sign on it would be fitting to a number I cannot even attribute to
my own code. The sign in this book is the preregistered one, chosen on mechanism, not on that
number.

Two facts I *can* use positively: `turnover_band` and `mean_gross_exposure` are **not** in the
failed list. So ~150×/yr turnover is inside the accepted band, and the gross-exposure floor is at
or below 0.265. Those are the only two calibration points I have and I aimed at them.

## 2. Why I did not nominate the seed

The sealed thesis (§3) pre-commits: *if F1, F2 or F3 fails, nominate the unmodified organizer seed
and do not move.* I am not invoking that clause, and I want the departure on the record rather than
stepped around.

F1 (deflated Sharpe), F2 (sign stability across halves and volatility terciles) and F3
(monotonicity in event size) were **never evaluated**. They require a research surface I do not
have in this phase; I have two JSON packets carrying one result. The clause triggers on
*falsification*, not on *absence of evidence*, and absence of evidence is what I have. Its purpose
was to stop me hill-climbing my way to a number — and there is no number here to climb.

There is also a fact the pre-commitment could not have known when it was sealed: **the seed fails
six hard gates.** Nominating it would not be a principled null; it would be nominating a book
already known to be non-qualifying. Retiring honestly is available and is not the same act as
nominating a broken book. I have chosen instead to keep the preregistered mechanism and repair the
structure, which is the only use the evidence I hold actually supports.

## 3. The mechanism

An extreme quote-volume z-score is a **state marker, not a directional signal.** It marks a bar
whose marginal clearing price was set by flow that had to trade in that bar rather than flow that
chose to: a maintenance-margin breach, a settlement-driven adjustment, or a burst of attention
arrivals. The return that follows is the compensation paid to whoever stood on the other side.

The mandate asks for drift or reversal, whichever the evidence supports. My preregistered answer is
that neither is unconditionally right and the condition is observable in the same bar. Two axes,
both centred on the symbol's own 30-bar history so that neither degenerates into a contract-size
sort:

- **Axis A — absorption.** `log|intrabar return| − log(quote volume)`, an Amihud-style impact
  ratio. How much price did this flow cost per unit of volume, relative to what this symbol
  normally costs?
- **Axis B — composition.** `log(quote volume / trade count)`, average print size. Jones, Kaul &
  Lipson (1994): it is the *occurrence* of transactions, not their size, that generates volatility.
  A shock made of many small prints is a crowd arriving; one made of few large prints is block flow.

Both are centred, then cross-sectionally ranked and averaged into one dislocation state. The
composite reduces to roughly `(log|return| + log trade count)/2 − log(quote volume)`: **a big move,
from many prints, per unit of volume.** That is a plain description of impatient flow tearing
through a thin book, and it is the observable signature of a liquidation cascade.

**The trade.** Direction is the cross-sectionally demeaned event-bar return. Contribution is
`−direction × (0.5 + state) × extremity`. At the dislocated extreme the fade is full; at the median
it is half; at the absorbed extreme it inverts into a mild drift. The `0.5` is a stated prior, not
a fit: I rank the reversal mechanism above the drift mechanism because Campbell–Grossman–Wang and
Cheng et al.'s forced-flow long-skew are venue-specific and quantified, whereas Gervais–Kaniel–
Mingelgrin's visibility channel is a month-horizon equity-retail-recognition effect with the
weakest transfer to an 8h perpetual where everybody already sees everything.

**Extremity is a ramp, not a threshold:** zero below z = 1.0, full at z ≥ 2.5, linear between. This
does three things at once. It honours the mandate — weight rises monotonically with shock size, so
the book's risk is concentrated in genuinely extreme bars. It encodes falsifier F3 structurally
rather than as an after-the-fact check. And it removes the razor edge at a hard `z*`, which is
exactly what the small-perturbation-stability check exists to catch.

## 4. Who is on the other side

**Paying, if the thesis is right:** leveraged directional retail being margin-called — structurally
long-skewed, since Cheng et al. (2021) measure 3.51% of outstanding longs against 1.89% of shorts
liquidated daily on perps at ~60× average leverage, so the forced side is more often a forced
*seller*; and attention-driven entrants arriving in a burst at the top of a move.

**Sitting beside me:** inventory-constrained market makers paid via changing expected returns for
accommodating non-informational pressure (Campbell–Grossman–Wang 1993; Bianchi, Babiak & Dickerson
2022 find precisely this in crypto, concentrated in lower-activity pairs); and basis desks who
supply the leverage and pull the perp back toward spot.

**Explicitly *not* on the other side.** Garfinkel, Hsiao & Hu (2025) find a −0.50%/day
abnormal-volume reversal in crypto **spot** on essentially my exact statistic — and then show it
dies for the 153 coins that gained margin and short availability. That is Miller (1977)
disagreement under short-sale constraints. A perpetual is the maximally shortable instrument, so I
do not claim that channel and I am not entitled to that effect size. Only the inventory /
forced-flow channel survives shortability. That is the whole bet, and it is a smaller one.

## 5. How each failed gate is addressed

The repair is structural and deliberate. I did not tune a signal; I rebuilt a book.

| Failed gate | Cause in the observed book | Change |
|---|---|---|
| `effective_breadth` (2.0) | a hard `z* = 2.0` fires on almost nobody, and weights were clipped to a handful of names | ramp from z = 1.0 over a 10-bar window, so ~80% of the universe carries some weight; signed power transform spreads weight without changing any ordering or sign |
| `breadth_persistence` (0.169) | breadth existed only on burst bars | the 10-bar overlap means the book is populated between shocks, not only during them |
| `participation` (`active_bar_fraction` 0.528) | flat on 47% of bars | the event set is essentially never empty; `None` (hold), not `{}` (liquidate), on the degenerate branch |
| `gross_edge_density` (−7.29 bps) | ~zero gross edge measured on two names | breadth is the fix for the *measurement*; the mechanism is the fix for the *sign*, and I have no evidence on the latter |
| `cost_share` (2.5e11) | denominator ≈ 0 | follows from the above; small weights across many names also cut the bite of the 0.1%-of-volume participation cap |
| `survives_triple_cost` (−36.3%) | 150×/yr turnover against no edge | 10-bar overlap; continuous ranks instead of median splits, so names drift rather than flip sign |

**One bug worth naming, since it is instructive.** The discovery candidate normalised to full gross
and *then* clipped at the per-symbol cap without redistributing. With two names each wanting ~0.50
and capped at 0.0995, realised gross collapsed to ~0.199. Here the cap-and-redistribute loop runs
to a fixed point, so gross is held at 0.98 rather than silently discarded.

**Estimated turnover: 90–215×/yr**, depending on where the organizer's risk unit seats my gross —
which I do not control and deliberately do not fight. The band demonstrably contains 150. This is
my least confident structural number and it is why `HOLD_BARS` sits at 10 rather than at the
declared maximum of 6.

## 6. What would falsify it

- **F1 — multiple testing.** The spread must clear a Deflated Sharpe Ratio > 0.95 against the
  Bailey–López de Prado benchmark at the declared N. Sharpe alone is not evidence here.
- **F2 — sign stability.** The sign must be identical in the first and second half of the visible
  window and in at least 2 of 3 trailing-volatility terciles. A sign that flips across halves is a
  fit, not a premium.
- **F3 — monotone in event size.** The spread at z ≥ 3.0 must be at least as large, and the same
  sign, as at z ≥ 1.0. If the effect does not grow with the shock, whatever I found is riding along
  on those bars rather than caused by them. The extremity ramp builds this in, so a book that earns
  its return from the z ≈ 1.1 names has falsified the mandate even if it is profitable.
- **Specific to this candidate.** If the dislocated and absorbed halves are profitable in the *same*
  direction, the absorption state is doing no work and this is a disguised flat reversal book. And
  if the gates now pass while `gross_edge_bps_per_turnover` stays negative at comparable magnitude,
  that is the first honest sign-evidence I will have held, and it falsifies the reversal tilt rather
  than the structure.

## 7. Trial accounting

Declared surface: **N = 36** (sealed thesis §4). Configurations actually evaluated on data: **2** —
and one of those two I cannot attribute. The hurdle is still computed at the declared N, because
preregistration means paying for the space you declared rather than the space you used.

This candidate departs from the declared surface in four places, all of which I count as overrun
under §4.5. None was chosen from a return:

1. **`HOLD_BARS = 10`**, outside the declared `H ∈ {1,2,3,6}`. Chosen on **cost**, not return: at
   H = 6 my turnover estimate lands 1.5–2× above the only level I know passes, and three of the six
   failed gates are cost gates.
2. **Extremity ramp z ∈ [1.0, 2.5]** replacing a hard `z*` from `{1.5, 2.0, 2.5}`. The ramp spans
   the declared grid; its floor at 1.0 is the overrun, taken for breadth.
3. **Continuous ranks** replacing the declared median splits on both axes, and the
   `REVERSAL_TILT = 0.5` prior.
4. **`FLATTEN = 0.5`**, a signed power on the score. Order- and sign-preserving; taken for effective
   breadth.

By the letter of the overrun rule this is one further configuration evaluated, **N = 37**. By its
spirit the surface widened by four knobs, and the F1 hurdle should be read as harder, not easier,
than the sealed 36-trial benchmark.

## 8. Where I expect this to break

In descending order of likelihood, stated now so a failure reads as a prediction:

1. **The reversal tilt is simply the wrong sign.** I chose it on mechanism ranking with no data
   behind it. If the venue's volume shocks are information arrival rather than forced flow — and
   Zaremba et al. (2021) find the largest, most tradeable coins show daily *momentum*, not reversal
   — then a majors-heavy universe makes the whole book backwards. This is the honest first risk and
   it is not hedged.
2. **`FLATTEN = 0.5` buys breadth with conviction.** It compresses a 30:1 extremity ratio to about
   5.5:1, so real capital sits on low-conviction names. I took the gate over the ranking because
   qualification is a bar on structure and ranking happens on evidence I will never see. If breadth
   passes with room, raising it toward 1.0 is the declared next move.
3. **The risk unit fights this family.** A volume shock is a volatility shock, so a common ex-ante
   volatility unit shrinks my book precisely when my signal fires. I may not target volatility and
   I do not. A broad book has lower ex-ante volatility per unit gross, so I expect the scaler to
   lever this one toward the cap — which raises realised turnover proportionally and is the main
   source of the wide turnover range above.
4. **Turnover overshoots the band ceiling.** If the packet shows `turnover_band` failing where it
   previously passed, the diagnosis is `HOLD_BARS` and nothing else, and the fix is to lengthen it.
5. **Wash trading corrupts the input statistic.** A quote-volume z-score is the statistic most
   exposed to self-trading. Axis B is the declared mitigation and it is present here, and
   rank-based scoring bounds any single outlier's weight — but a name whose volume is inflated
   without a matching trade count still lands somewhere in the book rather than outside it. This
   mitigates; it does not solve.
6. **The premium may be paid faster than 8h.** Kim & Hansen (2026) put the boundary-imbalance peak
   at 8–12h on this exact venue, which is why I think this horizon is survivable — but this dataset
   cannot distinguish "no premium" from "premium paid below 8h resolution," and I accept that
   ambiguity in advance.

## 9. Contract compliance

- `build_strategy()` returns an object exposing `target_weights(context, *, seed)`.
- Reads only `decision_time`, `bars`, `eligible_symbols`. Columns used: `open_time`, `open`,
  `close`, `quote_volume`, and `trade_count` — the last one **optional**, degrading to Axis A alone
  if absent rather than silently producing no book. `funding` and `auxiliary` are untouched.
- Cross-sections are aligned on the `open_time` **column**, never on the positional `RangeIndex`.
  Symbols with unequal history or a skipped bar are matched by timestamp; a symbol not on the grid
  is dropped rather than mis-lagged.
- Rows at or beyond `decision_time` are cut defensively even though the runner already excludes
  them, so future-append and corrupt-future invariance hold by construction.
- Caps held inside the contract: per-symbol 0.0990, gross 0.980, net 0.240. The net adjustment is
  exact and its floor is unreachable, so all three bind simultaneously.
- Returns `None` (hold) only when the panel is too thin to compute anything; otherwise always a
  mapping. Symbols come exclusively from `eligible_symbols`.
- No persistent state, no RNG, no I/O, no `eval`/`exec`/`getattr`, no embedded data, no date or
  symbol literals, no fitted parameters. Deterministic ordering throughout (`sorted`, stable
  argsort), so exact-replay determinism holds.
- Every input is a log difference, a within-symbol z-score, or a cross-sectional rank, so the book
  is invariant under price-magnitude rescaling, calendar shifts, and symbol pseudonymisation.
- Volatility is not targeted anywhere in this file.

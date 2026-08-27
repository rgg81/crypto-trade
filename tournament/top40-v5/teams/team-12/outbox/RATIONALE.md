# team-12 — volume-shock events — discovery candidate

**Thesis cell:** sealed thesis §4.2, Stage A, `{state axis = Axis A only, H = 3}`, at the declared
Stage-A defaults `L = 30`, `z* = 2.0`, direction = sign of event-bar return, funding gate off.
This consumes **1 of the 36 declared trials**. No knob outside §4 was touched.

---

## 1. The mechanism

An extreme quote-volume z-score is **not a directional signal — it is a state marker**. It marks a
bar whose marginal clearing price was set by flow that *had* to trade in that bar: a margin
breach, a settlement-driven adjustment, or a burst of attention arrivals. The return that follows
is the compensation paid to whoever stood on the other side of that flow.

The mandate asks for drift or reversal, "whichever the evidence supports". My preregistered answer
is that **neither is unconditionally right, and the condition is observable in the same bar**:

- **Axis A — absorption.** `|intrabar log return| / quote_volume`, an Amihud-style impact ratio,
  centred on the symbol's own trailing 30-bar median. This asks: *how much price did this flow
  cost per unit of volume, relative to what this symbol normally costs?*
- **Low impact per unit volume** → the shock was absorbed by a deep, two-sided book. Patient
  size traded without moving price. Read as informed accumulation/distribution → **hold in the
  direction of the event bar (drift)**.
- **High impact per unit volume** → the same volume tore through a thin book. Impatient, forced,
  dislocated. The liquidity provider who absorbed it must be paid → **fade the event bar
  (reversal)**.

The centring on each symbol's own history is load-bearing, not cosmetic: the raw ratio `|r|/QV` is
a market-cap sort (BTC's ratio is orders of magnitude below a small alt's), and a market-cap sort
is not the mechanism I am claiming. After centring, Axis A is approximately *normalised volume
shock size minus normalised return size* — which is exactly the Campbell–Grossman–Wang question.

**Book construction.** Events at each of the last 3 closed bars are ranked by Axis A and split at
the cross-sectional median: bottom half drift, top half reversal, the odd middle name dropped so
the split stays balanced. The three cross-sections are summed, giving an overlapping 24h holding
period, then the book is dollar-neutralised and gross-normalised. The holding period is
**recomputed from past-only rows at every decision** rather than carried, so there is no
persistent state; a symbol whose event repeats across bars accumulates conviction up to the
per-symbol cap.

The split is self-balancing in a useful way: in a market-wide selloff nearly every event bar has
`r < 0`, so the drift half goes short and the reversal half goes long, and the net stays near
zero without me imposing it. Both sides are used **by construction on exposure**, not as a
by-product of P&L.

## 2. Who is on the other side

**Paying me (if the thesis is right):**
- Leveraged directional retail being margin-called. Structurally long-skewed — Cheng et al. (2021)
  measure 3.51% of outstanding longs vs 1.89% of shorts liquidated daily on perps, at ~60×
  average leverage. The forced side is more often a forced *seller*.
- Attention-driven entrants arriving in a burst at the top of a move.

**Sitting beside me:**
- Inventory-constrained market makers, paid via changing expected returns for accommodating
  non-informational pressure (Campbell–Grossman–Wang 1993; Bianchi–Babiak–Dickerson 2022 find
  exactly this in crypto, concentrated in lower-activity pairs).
- Cash-and-carry and basis desks who supply leverage and pull the perp back toward spot.

I am trying to occupy the **receiving** seat at the specific moments the paying seat is occupied
and identifiable from volume and price alone.

**Who is *not* on the other side, stated deliberately:** Garfinkel, Hsiao & Hu (2025) find a
−0.50%/day abnormal-volume reversal in crypto **spot** and then show it dies for the 153 coins
that gained margin/short availability. That is Miller (1977) disagreement under short-sale
constraints. A perpetual is the maximally shortable instrument, so I explicitly **do not** claim
that channel here and I am not entitled to their effect size. Only the inventory / forced-flow
channel survives shortability, and that is the whole bet.

## 3. Why this is the discovery baseline and not something cleverer

Everything in the sealed parameter surface that is *not* here — Axis B (volume per trade), the
taker-buy imbalance as a direction source, the funding-crowding gate, other horizons, other
windows — is left out on purpose. This is the smallest object that can express "drift **or**
reversal, decided by evidence" rather than an arbitrary coin flip between the two, and it is small
enough that a single feedback packet is attributable.

Note that the *unconditional* version would be simpler still, and I preregistered that it should
be **null** (§3, F0). Shipping a candidate I already predicted would be flat would waste the trial;
the conditional spread is the honest minimum, not an elaboration.

## 4. What would falsify it

The mandate's falsifier — *if post-shock returns are symmetric around zero, the shock is not an
event worth trading in either direction* — is one I accept but expect to survive by accident
unconditionally, so the sealed thesis sharpens it. Against **this** candidate:

- **F1 (multiple testing).** The spread must clear a Deflated Sharpe Ratio > 0.95 against the
  Bailey–López de Prado benchmark at the declared `N = 36`. Sharpe alone is not evidence here.
- **F2 (sign stability).** The sign must be identical in the first and second half of the visible
  window and in at least 2 of 3 trailing-volatility terciles. A sign that flips across halves is a
  fit, not a premium.
- **F3 (monotone in event size).** The spread at `z ≥ 3.0` must be at least as large, and the same
  sign, as at `z ≥ 1.0`. If the effect does not grow with the shock, whatever I found is riding
  along on those bars, not caused by them.
- **Mechanism-specific, added by this candidate:** if the drift and reversal halves are *both*
  profitable in the same direction, Axis A is not doing the work I claim and the book is a
  disguised momentum or reversal bet.

**Pre-committed consequence:** if F1, F2 or F3 fails, I nominate the unmodified organizer seed and
do not move. Distance from the seed is what the leaderboard reports, so this costs something real.

## 5. Where I expect this to break, before I see a number

Stated now so a failure reads as a prediction, not an excuse. In descending order of likelihood:

1. **Breadth and participation, not signal.** `z* = 2.0` on 30 trailing bars is strict, and volume
   z-scores are strongly cross-sectionally correlated — quiet stretches may fire almost nowhere
   while bursty ones fire everywhere. The 3-bar overlap is my only smoothing. If the packet shows
   a breadth, mean-gross-exposure or participation gate failing rather than a weak Sharpe, the
   diagnosis is the threshold, not the mechanism, and the fix lives in the declared `z*` range.
2. **The risk unit fights the family.** Volume shocks are volatility shocks, so the organizer's
   common ex-ante vol unit shrinks my book precisely when my signal fires. This is structural, I
   may not target volatility, and it may eat the premium on its own. Broad books help (lower
   ex-ante vol per unit gross), which is a second reason breadth matters here.
3. **The universe may be too liquid for the reversal leg.** Zaremba et al. (2021) find the largest,
   most tradeable coins show daily *momentum*, not reversal. If the eligible universe is
   majors-heavy, Axis A may have no usable dispersion and the fade leg simply will not exist.
4. **The premium may be paid faster than 8h.** Inventory unwind in a liquid perp is a
   minutes-to-hours process. Kim & Hansen (2026) put the boundary-imbalance peak at 8–12h on this
   exact venue, which is why I think H = 3 is survivable — but this dataset cannot distinguish
   "no premium" from "premium paid below 8h resolution", and I accept that ambiguity in advance.
5. **Wash trading corrupts the input statistic.** A quote-volume z-score is the single statistic
   most exposed to self-trading. Axis B (volume per trade) is the declared mitigation and it is
   deliberately *not* in this candidate, so this baseline is maximally exposed to it. That is a
   known cost of keeping the discovery version simple.

## 6. Contract compliance

- `build_strategy()` returns an object with `target_weights(context, *, seed)`.
- Reads only `decision_time`, `bars`, `eligible_symbols`; only the columns `open`, `close`,
  `quote_volume`, which `protocol.py` and RULES both list. `funding` and `auxiliary` are untouched
  in this candidate.
- Returns `{}` (flat) when no event cross-section qualifies; never `None`, since the holding period
  is reconstructed rather than carried.
- Caps held inside the contract with headroom: per-symbol 0.0995, gross 0.995, net 0.245.
- No persistent state, no RNG, no I/O, no embedded data, no date or symbol literals, no fitted
  parameters. Rows strictly after `decision_time` are filtered out defensively even though the
  runner already excludes them, so future-append and corrupt-future invariance hold by
  construction. All statistics are ratios or log differences, so the book is unchanged under a
  price-magnitude rescale, a calendar shift, or symbol pseudonymisation.
- Volatility is not targeted anywhere in this file.

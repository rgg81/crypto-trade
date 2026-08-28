# RATIONALE — team-06, cluster relative value

Refinement candidate. Preregistered thesis: `lane/scouting/THESIS.md`. Only evidence: `t01`, the
unmodified organizer seed, on the visible development window.

---

## 1. Diagnosis of t01 — this was a design failure, not a parameter failure

The seed passed every gate that describes the *shape of a portfolio* and failed every gate that
describes the *economics of trading it*.

| passed | value |
|---|---|
| median effective breadth | 12.26 (pass fraction 0.983) |
| mean gross exposure | 0.830 |
| both sides used, on exposure | 52.1% long / 47.9% short |
| active bar fraction | 1.000 |

| failed | value |
|---|---|
| turnover ceiling | 311.9 /yr |
| gross edge density | **−3.37 bps per unit turnover** |
| cost share of positive gross | denominator ≈ 0 → 5.2e11 |
| survival at triple cost | −55.7% annualised |

Two facts do the work.

**(a) The cost per unit turnover is ~6 bps, and that is the binding constraint.** Gross P&L was
−3.37 bps × 311.9 ≈ −10.5%; net was −29.25%. The 18.7% difference over 311.9 units of turnover is
**≈ 6.0 bps of cost per unit of turnover at 1x, ≈ 18 bps at 3x**. That single number determines what
kind of book can exist here: *any* candidate must clear roughly 18–20 bps of gross alpha per unit of
turnover simply to be alive at triple cost, and roughly 12 bps to bring cost share under one half.

At an 8-hour holding period this is arithmetically unreachable. Alpha per unit turnover scales like
`IC · σ_resid · √h / 2`. With 8h idiosyncratic vol of ~1.7% and a generous cross-sectional IC of
0.04, `h = 1` bar yields ~3 bps and `h = 3` bars ~6 bps — under the 1x cost, never mind 3x. No
improvement in signal quality rescues a book rebalanced every 8 hours. **The seed did not lose
because its signal was bad; it would have lost with a good signal.**

**(b) The signal was also consistently wrong, not merely weak.** `positive_fold_fraction = 0.0` —
every fold negative — with gross edge density negative. A zero-edge book gives ≈ 0.5. So whatever
short-horizon construction the seed used was systematically anti-predictive on this window.

I did not respond to (b) by flipping a sign. I do not know the seed's construction, and flipping the
sign of a book that cannot clear its own costs at any sign produces a book that still cannot clear
its costs. My THESIS §1.6 committed me to treating a bare sign flip as weak evidence rather than a
discovery, and §3.4 committed me not to substitute a different mechanism into the same slot. What
(b) *does* license is a narrower and better-supported claim: **the 8h–24h horizon is contaminated**
— it is where informed and liquidation-driven continuation lives, where fills land, and where
§2.9 (Zaremba et al.) actively predicts momentum rather than reversal in exactly the
largest-and-most-tradeable tier a Binance perp universe is concentrated in. So I vacate that horizon
explicitly rather than betting against it.

Both facts point the same way, and that is what makes this a redesign rather than a tune.

---

## 2. What changed, and why each change is structural

### 2.1 The book is refreshed weekly, not every 8 hours

`REBAL_GRID = 21` bars. At each decision the observation window is snapped back to a coarse grid
(`n_drop = ref_len % REBAL_GRID + SKIP_BARS`), so inside a block *the inputs are literally
unchanged* and the target book is identical decision to decision. The book only moves when the grid
advances.

This is the single most important change and it is deliberately not a parameter. A signal-side fix
cannot reach it: even a signal with lag-1 autocorrelation of 0.97 produces `√(2(1−ρ)) ≈ 0.245` of
turnover per 8h decision, i.e. ~268/yr, because the book is renormalised every bar. Turnover at 8h
cadence is set by the *cadence*, not by the smoothness of the signal. Expected turnover under the
new cadence is ~50–80/yr against the seed's 312, and the alpha per unit turnover rises like `√h`.

The grid is derived from **bar counts** (`_reference_length`), never from `decision_time`. A calendar
shift does not change row counts, so the schedule attaches to the same bars — equivariant by
construction, with no absolute-date channel.

I hold by re-submitting the same explicit book rather than returning `None`, so the book stays fully
specified, stays cluster- and market-neutral through membership changes, and cannot silently carry a
stale position. The cost is a small amount of drift-correction turnover, which is already in the
estimate above.

### 2.2 The signal is a spread level, not a recent return

The deviation is now the **cumulative** residual against the cluster, fitted as an
Ornstein–Uhlenbeck process (THESIS §4.3 axis 6, `Z = OU s-score`; Avellaneda–Lee, §2.1):
`X_t = Σ e_t`, AR(1) fit over 90 bars (30 days), `s = (X − m)/σ_eq`. Trades are contrarian in `s`
with a 0.75 dead zone and a ±3 clip.

This matters for three reasons, not one:

1. A spread level is intrinsically slow, so it survives being refreshed weekly. A `H`-bar return
   residual would be mostly stale by the next grid point.
2. It carries the **mean-reversion speed filter** — only names whose cumulative residual actually
   reverted faster than half the fit window (`0 < b < 0.97`, i.e. half-life under ~15 days) are
   traded. That filter is what raises gross edge density directly: it removes names whose residual is
   a random walk, which contribute turnover and no alpha. The 15-day cap is not free-floating; it is
   §2.10's ~14-day cluster-persistence horizon.
3. It is dominated by slow divergences rather than by "what moved yesterday", which is precisely the
   contaminated window from §1(b).

`SKIP_BARS = 3` excludes the most recent day from the signal outright.

### 2.3 The funding tilt is switched on

`FUND_TILT = 0.5` on the cluster-relative mean funding rate over the last 21 settlements, snapped to
the same grid. This was THESIS trial T6; I am spending it here because it is the one component that
**earns without consuming turnover**. Funding is persistent, so it adds essentially nothing to
`Σ|Δw|` while contributing carry and a crowding read — it improves the exact ratio (gross edge per
unit turnover) that three of the four failed gates measure. It is always cluster-relative, never
absolute, so it is not a naked short-vol carry.

### 2.4 The book is more diversified than the seed's

Effective breadth 12.26 against a 0.10 cap means the seed was pinned at the cap on ~12 names. Soft
cap 0.06 plus a linear-in-dead-zoned-`s` weighting should give effective breadth ~20–35. That is
margin on a gate the seed passed at 0.983 rather than 1.0, and it lowers the variance of the very
small number of independent bets a weekly book makes.

---

## 3. Mechanism, and who is on the other side

Unchanged from the thesis, and the redesign sharpens rather than replaces it.

A narrative-level burst of leveraged directional flow — or a margin engine's price-insensitive
liquidation — lands on one contract in a co-moving group rather than on the group. Someone takes the
other side at a concession and lays the inventory off over days. Cluster-demeaning removes both the
market factor (§2.4, Liu–Tsyvinski–Wu: without it "SOL fell 4%" is mostly "crypto fell 4%") and the
narrative factor the group shares, leaving the concession. Note the two mechanisms that predict this
sign are independent: inventory unwind, and lead-lag diffusion within a correlated group — the
laggard-catches-up trade *is* residual reversal.

The counterparties are named in THESIS §1.3 and I have not revised them: leveraged retail picking the
salient member of a group, liquidation and ADL engines, basis/funding-carry desks pressuring a single
perp leg, and cross-sectional momentum programs. What I am paid for is immediacy and adverse
selection (§2.5, §2.6) — and the weekly cadence means I am now renting balance sheet over days, which
is the horizon on which inventory is actually laid off, rather than over hours, which is the horizon
on which the informed trade.

The groups are discovered, not declared: Spearman correlation over 60 days, Marchenko–Pastur
eigenvalue clipping of the noise bulk (§2.2, Laloux et al.), removal of the top market eigenvector,
then average-linkage agglomerative clustering into an MP-adaptive `K` — factor removal first, cluster
second, trade third, per §2.11.

---

## 4. What would falsify this

**F2 remains the primary falsifier and it is still untested.** From THESIS §3.1: at matched gross and
turnover, this book's gross edge per unit turnover must exceed the identical book with `K = 1` (plain
universe-demeaned reversal). If it does not, the clustering is decoration and the mandate is
falsified *even if the book makes money*. I have no market data in this lane and cannot run it; I
have not run it and I am not claiming otherwise. It is the trial I would spend next, and per §3.4 a
`K = 1` book that wins would be reported as a falsification, not shipped.

**F1b degrades honestly rather than silently.** `K` is `1 + (eigenvalues above the MP edge, excluding
the market)`, clamped to [2, 10]. If the correlation matrix carries no structure beyond market beta,
`K` collapses to 2 and the book converges toward a universe-demeaned book — which is F1b firing in
plain sight rather than being hidden by a fixed `K`. I deliberately did not gate trading on a
per-decision structure test: that would be the volatility/dispersion regime switch THESIS §4.5
forbids and RULES.md says no invariance check closes.

**Specific, checkable ways this candidate is wrong:**

- Turnover comes back well outside ~40–90/yr. That would mean my model of what drives turnover here
  (cadence, not signal smoothness) is wrong, and the diagnosis in §1(a) with it.
- Gross edge density is still negative. Then the horizon story in §1(b) is wrong: cluster residuals
  do not revert at 1–3 week horizons either, and cluster relative value has no expression in this
  venue that clears 6 bps a turn. That is a retirement, not a re-tune.
- Gross edge density is positive but under ~12 bps. Then the mechanism may be real but is not worth
  its immediacy cost at any cadence I can reach at 8h resolution.
- Effective breadth collapses toward 10–12. That would mean average linkage is chaining into one
  giant cluster plus singletons, and the "discovered sectors" are one sector.
- It survives 1x but not 3x. Same verdict as the seed. Per the phase guidance, that is not a book.

---

## 5. Declared departures from the preregistration

THESIS §4.4 requires that a knob I want mid-phase be reported as an incomplete preregistration rather
than added silently. Two are:

1. **`REBAL_GRID` (rebalance cadence) and `SKIP_BARS` (recent-bar exclusion) are new.** They are not
   in the §4.3 surface. §4.5 declared that turnover would be controlled by making the *signal* slowly
   varying via `S`, `H`, `z_enter` and never by remembering positions. That declaration was wrong on
   its own arithmetic — no achievable signal autocorrelation gets turnover under the ceiling at 8h
   cadence — so I am controlling cadence instead. It remains stateless: the grid is computed from
   row counts in the streamed data, nothing is remembered between decisions.
2. **`OU_WINDOW = 90` bars is fixed by fiat, not searched.** §4.3 declared the *choice* of the OU
   s-score but never its fit window. I set it to `W/2` and bounded the reversion filter at half of
   it (~15 days) from §2.10's persistence horizon, rather than searching it.

Everything else is inside the declared surface: `W`=180, `q_max`=0.4, `K`=MP-adaptive, `m_min`=5,
`Z`=OU s-score, `S`=1, `z_enter`=0.75, `α`=0.5, `γ`=0, `sign_mode`=contrarian.

**Trial accounting, stated plainly:** this candidate collapses THESIS trials T1, T5 and T6 into one
configuration and does not spend a trial on the T2 (`K = 1`) null. That is a real cost to the
deflation benchmark and it means F2 is unresolved. Given one feedback packet and four failed gates,
I judged that spending this trial on a book that can pass the cost gates at all was the prerequisite
to F2 being a meaningful question — a `K = 1` comparison between two books that both fail triple cost
answers nothing. If this candidate clears the structural gates, T2 is the next and only trial I want.

## 6. Invariance and contract compliance

Stateless (constants only, no attributes mutated); no RNG, `seed` unused; no network, subprocess,
filesystem, `eval`/`exec`/`getattr`; no embedded data, fitted parameters or lookup tables. No symbol
identity — ordering is by liquidity rank, never by name. No price levels — log returns, rank
correlation and ordinal volume screens only, so a magnitude rescale changes nothing. No absolute
dates — the cadence grid is bar counts and the funding window is relative to the panel cutoff. The
panel is built on `open_time` per RULES.md, not on the positional index. Output is a fully specified
book over `eligible_symbols` with `Σ|w| ≤ 0.999`, `|Σw| ≤ 0.15`, `|w| ≤ 0.095`; on any unexpected
shape the strategy returns `None` and holds rather than churning.

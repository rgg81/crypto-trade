# Top-40 V5 tournament charter

Status: pre-activation authority

Tournament: `quant-portfolio-blind-top40-v5`

## 1. Objective and field

Fifteen isolated teams independently design a long/short book over Binance USD-M perpetuals. Each
receives an assigned economic mechanism family and nothing else: no incumbent, no prior result, no
other team's work, and no strategy artifact from any earlier edition of this tournament.

The edition has transparent development research, a sealed confirmation stage, one historical
observation, and a live-forward paper record. There is no forced finalist, no forced winner, and
no lowering of a floor to fill a bracket. An empty field is a valid, tested outcome.

## 2. Evidence windows

| Layer | Interval, UTC | Span | Permitted use |
|---|---|---|---|
| Venue warmup | `[2020-01-01, 2020-08-02)` | 0.58y | formation windows only; never scored, never traded |
| Development — visible | scored window minus sealed and margin | **808 d (2.21y)** | standardized metric packet per trial |
| Development — sealed | 8 × 45 d interleaved blocks | **360 d (0.99y)** | organizer only; carries the generalization bar |
| Development — withheld margin | purge 5 d, embargo 10 d per block | 110 d | scored by nobody |
| Historical observation | `[2024-02-01, 2026-08-01)` | **2.5y** | one atomic release |
| Operational embargo | `[2026-08-01, 2026-09-01)` | 1mo | nothing |
| Live forward | from `2026-09-01` | ≥365 d | paper only, frozen identities |

The scored development window is `[2020-08-02, 2024-02-01)`. Warmup ends there because the seasoned
universe does not hold a workable cross-section earlier: measured over the scored window it never
falls below 24 members, with a median of 40.

**Sealed schedule.** Partition the scored window into consecutive 45-day blocks indexed from zero;
seal block *i* where `i mod 7 ∈ {1, 4}`, taking the first seven; then seal the final 45 days.

`S1 2020-09-16` · `S2 2021-01-29` · `S3 2021-07-28` · `S4 2021-12-10` · `S5 2022-06-08` ·
`S6 2022-10-21` · `S7 2023-04-19` · `S8 2023-12-18` (terminal). Last visible day **2023-12-12**.

Seven interleaved blocks stratify confirmation across every regime the window contains; the
terminal block tests temporal generalization, which interleaving structurally cannot. The explicit
intervals are the authority and are hash-bound at activation; the rule exists so they can be
re-derived and audited.

**Disclosed limit.** Absolute-return autocorrelation persists to lag 21–30, so a team can always
infer a sealed block's *volatility regime* from its neighbours. It cannot infer the *sign*. This is
stated rather than implied away.

**The historical window is candidate-relative only, and not even that for the organizer.** It is
byte-identical to CUP-50 v2's released sealed window, whose full twelve-lane leaderboard is
published, and whose structural findings were known to the organizer while V5 was designed. It
produces the ranking and the desks. **It authorizes nothing.** Capital gates solely on the forward
record.

## 3. Market and execution authority

Only point-in-time members of the frozen, weekly reconstituted seasoned Top-40 native-crypto
universe may be traded. Membership requires **maturity** (90 days of history), **completeness**
(≥95% of expected bars in a 90-day ranking window, counting only bars in which trading occurred),
and **persistence** (liquid Top-60 in ≥8 of the previous 10 weeks). Missing slots are held as cash
and never backfilled. Persistence is armed before the first scored week, so every scored week is
judged under the same rule.

Features use only information available at the decision boundary. Orders execute at the next
executable open. Funding applies to the carried position before rebalance. Base costs are 5 bps
taker plus 2.5 bps slippage per side, with independent 2× and 3× evaluations. Gross ≤ 1.0,
|net| ≤ 0.25, per-symbol ≤ 0.10, participation ≤ 0.1% of prior-24h quote volume.

Three additions to the V4 contract:

- **A bar in which nothing traded is not executable.** It cannot be filled and is not offered to a
  strategy. On such a bar a carried-forward close and a still-moving index mark diverge without
  bound — 25× for LUNA at its delisting, 989× for SXP — and sizing on one while settling at the
  other produces a loss many times equity.
- **Ruin is scored, never raised.** A wiped-out book is liquidated, floored at zero equity, and
  reported with a −100% final bar so every downstream statistic sees it. An evaluator exception
  never consumes a team's trial.
- **A common ex-ante risk unit**, organizer-owned, scales every book to the same ex-ante
  volatility before the exposure caps are re-applied. Teams may not target volatility themselves.
  Every action it takes is reported; it is never a silent rescale.

## 4. Free research within an assigned family

Each lane receives an economic family and an organizer seed — the idea in the least clever form
that could work. The mandate names the family, never a parameter, an implementation or an expected
sign. Convergent independent ideas are allowed; reading another strategy is not.

Every material trial is accepted into an append-only, hash-chained journal before market data are
opened. Failed and abandoned trials consume their slot. Evaluator faults do not.

Before any data is mounted, each lane runs a **networked scouting phase** with no market data, no
repository, no prior-edition artifact and no broker, and produces a preregistered mechanism thesis,
at least three public citations, a falsifier stated on visible development data, and a declared
parameter surface. That last item makes the search space countable, which is what the trial count
in the deflation benchmark is supposed to mean.

## 5. Qualification

Gates are separated by what they can conclude.

**Degeneracy and cost gates are hard at every stage.** A book that is not a portfolio is not a
marginal candidate: effective breadth, mean gross exposure, participation, both sides used measured
on *exposure* rather than P&L, risk-unit attainment, turnover band, gross edge per turnover, cost
share, and survival at 3× cost.

**Performance gates are reported on development and enforced on the sealed blocks.** Twelve
feedback-driven trials make a development Sharpe a statement about a search rather than an edge:
every prior edition's floor set admitted **zero** of the ninety-four measured V4-R9 trials.
Enforcing performance there is precisely how a field ends up empty and a fallback ends up choosing.

**Multiple testing is corrected where it exists, and only there.** A team selects its nominee from
twelve trials on *visible* data. The sealed blocks never saw that search, so holding them out is
already the correction: the sealed estimate of the chosen strategy is unbiased. Deflating it again
by the team's trial count would charge the same search twice, and measurably does — it costs power
at a true Sharpe of 1.0 more than half. Deflation is therefore **reported on development**, where
the nominee was selected on the same data and a Sharpe is a statement about a search, and the
sealed evaluation carries a trial count of **one**.

**Field multiplicity is reported, never gated.** Fifteen teams each submitting their best does
create an upward bias in the field maximum, and the release publishes the expected maximum under
the null beside the leaderboard so a reader can price it. It is not used as a gate: at a 360-day
window a genuinely good book produces p-values around 0.15–0.30, and a false-discovery correction
across fifteen nominees selects roughly half a team. That is V4-R2's failure in a new costume — a
correct-looking correction nobody can pass — and this edition declines to repeat it.

**The bar's operating characteristic is measured before activation and published.** A bar no
plausible strategy clears cannot be activated; nor can one a null population walks through.

> **What each stage can conclude.** The sealed stage is a **screen**: it passes roughly two thirds
> of books with a true Sharpe of 1.0 and roughly a third of books with none, because at 360 days
> the standard error of an annualised Sharpe is about 1.0 and no threshold does better. Its job is
> to stop the 2.5-year window being spent on books that are degenerate, cost-annihilated or
> negative. **Ranking happens on the historical window**, where the standard error is 0.63 — the
> most discriminating evidence this edition has. **Capital is decided on the forward record**,
> which is the only uncontaminated evidence of any kind.
>
> Three independent filters in series, each weak alone. That is the honest shape of the problem;
> a single strong gate at any one stage is not available at these window lengths.

## 6. Selection

Qualification is a **bar, not a rank cut**. Every candidate clearing the development gates is
observed on the sealed blocks; every candidate clearing the sealed bar is observed on the
historical window. There is no top-N cut before those stages and **no fallback promotion, ever**.
`advancing: []` is a supported, tested terminal state with no winner.

Ranking within the bar is by robustness on sealed data — the contiguous block-deletion fifth
percentile — never by worst-fold Sharpe, which rewards inactivity and in V4-R9 promoted a book
running 3.7% mean gross exposure to first place.

Holdout reporting is noise-floor honest. The standard error of a Sharpe over 2.5 years is about
0.63, so every figure carries a confidence interval and candidates whose *paired* difference
interval contains zero are declared **tied**, not ranked.

## 7. The deliverable

The result is the **top three individual candidates and an equal-weight ensemble of those three**,
carried to **four forward paper desks** from 2026-09-01 for at least 365 official days with
exact-replay parity.

Equal weights, not risk-parity: three constituents, nothing to tune. The mandate structure should
make the three economically distinct; the release reports their pairwise correlations, and if two
land in the same family that is a finding rather than something to substitute around.

**The capital decision reads the forward record, never the leaderboard.**

## 8. Organizer contamination

The organizer has seen prior editions' results over the historical window. Safeguards:

- **Numeric provenance.** Every configured number carries exactly one of `inherited`, `structural`,
  `calibrated` or `derived`, with the artifact hash that justifies it. Activation fails if any
  number lacks provenance.
- **A quarantine list** enumerating every fact the organizer knows about the window, with sources.
- **A contamination-free adversarial review** proposing thresholds independently, under the same
  clean-room profile the teams get.
- **Split-half reporting** of every holdout statistic.
- **Four forward desks** as the only uncontaminated evidence.

Inheriting V4-R2's thresholds is not the safe default it appears to be: its full floor set, its core
four, and even the looser V3-extension set each admitted zero of the ninety-four measured trials.
Structural constants are inherited unchanged; performance thresholds are recalibrated and frozen
before any sealed row opens.

## 9. Activation and amendments

Activation is single-shot and must bind this charter, the numerical config with complete provenance,
all fifteen clean-room surfaces, the implementation, the dependency lock, the evaluator, the
snapshot manifest, the whole-grid preflight report, the calibration report, the focused tests, the
mutation ledger, and the adversarial-review record.

After activation, changes require a prospective append-only amendment made before the affected data
are accessed. No amendment may rewrite evidence, restore a consumed observation, reveal partial
sealed or holdout state, lower a qualification floor, or let a changed model inherit earlier
evidence.

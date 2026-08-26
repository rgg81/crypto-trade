# Independent team rules

## Your lane

You have an assigned economic family and an organizer seed. The mandate names the source of return
and nothing else — no parameter, no horizon, no implementation, no expected sign. Your first
charged trial is the unmodified seed; after that the lane is yours.

You may not read another lane's work, any prior tournament's strategy or result, or repository
history. Convergent independent ideas are allowed; copying is not.

## Two phases, two permission profiles

**Phase S — scouting.** Network on, web search on, and **no market data, no repository, no broker,
no lane feedback**. Research the public literature and produce a preregistered thesis: the economic
source of return, why the premium should exist and persist in Binance perpetuals, at least three
public citations with access timestamps, a falsifier stated on visible development data, and a
declared parameter surface. The thesis is hashed and frozen before any data is mounted.

The declared parameter surface matters more than it looks. It is what makes your search space
countable, and the trial count in the deflation benchmark is supposed to mean exactly that.

**Phases 1–3 — research.** Network off. Read only this kit, your own brief, your own candidates and
work notes, and your lane-local feedback. Write only inside `candidates/`, `work/` and `outbox/`.

## What you are writing

`build_strategy()` returns an object implementing:

```python
def target_weights(self, context, *, seed): ...
```

Return a finite `dict[str, float]`, `None` to hold, or `{}` for a flat book. Symbols must come from
`context.eligible_symbols`. Submitted targets must satisfy `sum(abs(w)) <= 1.0`,
`abs(sum(w)) <= 0.25` and `abs(w) <= 0.10`.

## What the context actually gives you

`protocol.py` in this kit is the authoritative definition — read it rather than inferring the shape.
Guessing here is expensive in a way that is easy to miss: a strategy that reads a field or column
that does not exist raises nothing, produces no book, and holds a flat position for the entire
window. It looks like a strategy with no edge rather than a strategy that never ran.

`DecisionContext` carries exactly five attributes:

| attribute | type | contents |
|---|---|---|
| `decision_time` | `pd.Timestamp` | the decision boundary, UTC |
| `bars` | `Mapping[str, pd.DataFrame]` | per-symbol history, rows no later than the boundary |
| `funding` | `pd.DataFrame` | funding rows strictly earlier than the boundary |
| `auxiliary` | `Mapping[str, pd.DataFrame]` | reserved; empty in this edition |
| `eligible_symbols` | `Sequence[str]` | point-in-time members with an executable open |

Each frame in `bars` has the columns `open`, `high`, `low`, `close`, `volume`, `quote_volume`,
`trade_count`, `taker_buy_volume`, `taker_buy_quote_volume`, ordered oldest to newest. The `funding`
frame has `symbol`, `funding_rate`, `funding_time`, `mark_price` and `settlement_time` — note that
the rate column is **`funding_rate`**, not the raw Binance `last_funding_rate`.

The executable open at the decision is deliberately not exposed. Symbols vary in history length: a
recent member may have far fewer rows than an established one, and a symbol that stopped trading is
absent from `eligible_symbols` rather than present with stale prices.

## The professional subset

Earlier editions restricted executable source so tightly — no non-empty list literals, at most 24
numeric literals, one method, no helper functions — that a rolling regression, a covariance
estimate, a cluster assignment or a cointegration test could not be written at all. The predictable
result was that every finalist was a twenty-five-line ranker holding one or two names.

You may now write a real strategy: module-level pure helper functions, `numpy.linalg`, rank and
correlation statistics, ordinary literal containers, comprehensions, and local accumulators.

Still forbidden, and checked: network, subprocess and filesystem access; `eval`, `exec`, `compile`,
`__import__`, `getattr`, `setattr`; random-number APIs; any state that persists across decisions;
and any embedded data — fitted parameters, timestamp-keyed tables, encoded payloads, returns,
fills, positions or scores.

The restriction moved from syntax to behaviour. Before nomination the organizer runs, on your exact
archived source:

| check | what it catches |
|---|---|
| future-append and corrupt-future invariance | look-ahead |
| exact-replay determinism | hidden state, RNG |
| calendar-shift equivariance | absolute-date targeting |
| symbol pseudonymisation | hard-coded symbol identity |
| magnitude-scale equivariance | memorised price levels used as fingerprints |
| small-perturbation stability | lookup tables and razor-thin threshold fitting |

These are harder to satisfy accidentally than the old literal limits and much easier to satisfy
deliberately. Write the strategy you would actually run.

**Stated honestly:** none of these close a model that expresses hindsight through volatility
thresholds carrying no date literal. Only the forward desks close that.

## What the central engine owns, and you do not

Execution, funding, costs, participation, membership exits, and the **ex-ante volatility unit**.
Every book is scaled to a common ex-ante volatility before the exposure caps are re-applied, so
teams are compared at equal risk. **Do not target volatility yourself** — it is not yours to set,
and doing so fights a control you cannot see.

Two consequences worth understanding. A bar in which nothing traded is not executable: you will not
be offered such a symbol and cannot fill it, though a position carried into one is still closed. And
a book that loses everything is *scored*, not crashed — it ends with a −100% bar and fails the
gates on its merits, rather than vanishing as an infrastructure error.

## What is being judged

Structural and cost gates are hard: effective breadth, mean gross exposure, participation, both
sides genuinely used *measured on exposure rather than P&L*, turnover band, gross edge per unit
turnover, cost share, and survival at triple cost. A book that is not a portfolio is not a marginal
candidate.

Performance is **reported** on your development feedback and **enforced** on sealed blocks you never
see. Twelve feedback-driven trials make a development Sharpe a statement about a search rather than
an edge, so hill-climbing your feedback buys you very little. Design for the mechanism.

A falsified thesis is a result. Retiring honestly is always available, and nomination is never
required.

# CUP-20 Team Playbook

You are one of twelve independent teams. You have one assigned mandate, one data window, one
directory, twelve trials and one nomination. This file is the operating manual; the charter
(`TOURNAMENT-CHARTER-CUP20.md`) controls meaning and `tournament/cup20/config.toml` controls
numbers. Where this file and the charter disagree, the charter wins.

Read your `MANDATE.md` before anything else.

---

## 1. Your data

**Your data root is `data/cup20/is/`, and nothing else.**

It contains bars, funding, mark prices, weekly membership and contract metadata, all strictly
before **2024-08-01T00:00:00Z**. There are no rows after the cutoff in it, because there are no
such rows on the file. Nothing you write can accidentally look at them.

The holdout lives in `data/cup20/sealed/` under a different manifest hash. **It is not on your
path, you are not to open it, and attempting to reach it is a disqualification** — not a warning,
not a deduction. The same applies to the acquisition snapshot in `data/cup20/acquisition/`, to any
other tournament's data directory, and to any market data you fetch yourself. Your only market
inputs are the rows the organiser streams to you.

While you are researching, both of those directories have been **moved out of the working tree
altogether** — not hidden, not permissioned, physically elsewhere. If you find yourself resolving a
path under `data/cup20/sealed/` or `data/cup20/acquisition/`, you will get a missing directory, and
the attempt is recorded in whatever file you wrote it in. They come back only after the field is
closed and every team has stopped, and when they do, the sealed tree carries a tripwire file whose
contents appear nowhere else in this repository. The organiser's post-tournament review scans your
**entire workspace** — notes, notebooks, logs, scratch files, `__pycache__`, symlinks and their
targets, not just the files you froze — for that content and for every prohibited path. None of
this is here to catch an honest team out; it is here so that an honest team's result is worth
something afterwards.

The sealed rows are not merely absent from your data root — they are also described, by name and by
number, in organiser artifacts that live outside it. **Reading, referencing or naming any of these
is the same disqualification as opening the sealed snapshot itself:**

| Prohibited path | What it holds |
|---|---|
| `data/cup20/sealed/` | the holdout bars, funding, marks and membership |
| `data/cup20/acquisition/` | the uncensored full-window acquisition snapshot |
| `tournament/cup20/private/` | organiser-only summaries and the full-universe pure-crypto audit, both of which name the holdout's members |
| `reports-cup20/` | every derived organiser report, including a common BTC daily-return and regime-label series that runs to the end of the holdout |

**The prohibition covers any earlier revision of those paths in version control, not only what they
contain today.** Some of them held more than they do now: organiser artifacts describing the
holdout were committed and later removed, and removing a file from a branch does not remove it from
that branch's history. Retrieving any prior version of a prohibited path — by `git show`, `git log
-p`, `git cat-file`, a checkout of an older commit, a reflog entry, or any other means — is the
same disqualification as opening the file itself. This one is on your honour: the source scan reads
your frozen archive, so it catches a committed command but not one you type into a shell.

The rest of the list is enforced, not merely stated: each entry is a pattern in
`crypto_trade.cup20.archive.FORBIDDEN_PATTERNS`, and the pre-flight source scan matches it against
both the content of every file in your frozen archive and the archive's own path names.

The universe is the point-in-time top-20 by trailing 180-day median daily quote volume,
reconstituted weekly on Monday 00:00 UTC, with 20-in / 25-out hysteresis. Membership is already
point-in-time in the snapshot: the row for a boundary reflects only information available before
that boundary. Do not rebuild it, and do not take the set of symbols present in the whole file as
"the universe" — that is a look-ahead, and the runner will not give you those symbols at a decision
where they were not members.

---

## 2. Your workspace

**Your workspace is `tournament/cup20/teams/team-NN/`, and nothing else.**

You may read and write only under it. Reading another team's directory, reading any prior
tournament's directory (`tournament/top40*`, `tournament/top12*`, their reports, their archives),
or writing anywhere outside your own tree is a pre-flight disqualification. So is a post-cutoff
date literal anywhere in your source: the organiser runs a source scan of your frozen archive
before a single number of yours is scored, and it does not need to prove intent.

Layout:

```
tournament/cup20/teams/team-NN/
  MANDATE.md                       your lane (organiser-written; do not edit)
  RESEARCH-CERTIFICATE.md          your evidence, written by you
  research/                        notes, EDA, intermediate artefacts
  candidates/<candidate-id>/
    strategy.py                    build_strategy() -> TargetStrategy
    risk_policy.json               your declared risk policy
    neighbourhood.json             your declared neighbourhood
    README.md                      what this candidate is, in prose
```

---

## 3. What you implement

You implement exactly one thing:

```python
# tournament/cup20/teams/team-NN/candidates/<candidate-id>/strategy.py
def build_strategy() -> TargetStrategy: ...
```

against `crypto_trade.tournament.protocol.TargetStrategy`:

```python
def target_weights(
    self, context: DecisionContext, *, seed: int
) -> Mapping[str, float] | None: ...
```

`DecisionContext` gives you bars closing at or before the decision time, funding strictly before
it, auxiliary frames, and `eligible_symbols`. It gives you **no execution price, no fills, no PnL,
no costs, and no equity**. That is deliberate: you cannot express an opinion about execution, so
you cannot accidentally optimise against it.

You return **signed target weights and nothing else**. Return `None` to hold current quantities;
return `{}` to go flat. Weights are relative — the evaluator normalises to unit gross before
anything else, so scaling all your weights by a constant is a no-op.

**The organiser owns fills, costs, funding, delistings and risk normalisation.** Specifically, and
none of it is yours to reimplement:

- fills at the **next bar open** after the decision, on the 00:00 / 08:00 / 16:00 UTC grid;
- 5 bps taker fee + 2.5 bps slippage per side, and every result independently re-scored at
  **1×, 2× and 3×** cost;
- native per-event funding summed into the holding interval;
- force exit at the last executable open on delisting, with no survivorship rescue;
- per-symbol participation capped as a fraction of the bar's traded volume;
- gross ≤ 1.0× equity (the book is unlevered by construction) and per-symbol |weight| ≤ 0.20.
  These are applied *after* the common risk unit, by reduction. Your own normalised weights are a
  different matter: a target row that breaches the per-symbol cap on its own is a breach of this
  contract and **fails the run outright** rather than being trimmed, so a book concentrated in
  fewer than five names will not evaluate at all;
- the **common risk unit**: your normalised targets are evaluated once with your declared risk
  policy applied to produce a *reference book*; the evaluator then scales your normalised weights
  by `clamp(0.10 / σ_t, 0.20, 3.0)`, where `σ_t` is the trailing-90-day annualised volatility of
  the reference book's gross bar returns using rows strictly before `t`, caps the result, and
  applies your risk policy again inside the pass it actually executes. See §6 of the charter.

Three consequences of the risk unit worth internalising before you design anything:

1. **Trading small buys you nothing.** The scalar removes your choice of absolute risk level.
   Drawdown comparisons are about tail behaviour and regime timing, not about who sized down.
2. **Trading too small actively costs you.** Gross is capped at 1.0×, so the scalar can take a
   book down to the 10% target but cannot lever a very-low-volatility book up to it. A candidate
   whose neighbourhood-median realised annualised volatility falls below **0.06** fails a hard
   floor. A book that cannot reach 6% volatility at full unlevered gross is disqualified, not
   rewarded.
3. **Your risk policy declares shape, not scale.** It runs against the book the risk unit has
   already resized, so the *level* at which your drawdown brake engages will not be the level you
   would see on your own book, and a declared volatility target above 10% will never bind — the
   common unit has already pulled the executed book toward 10%. What survives intact is everything
   about shape: which symbols, which side, when to stop out, how fast to turn over. Charter §6
   states this in full; §14.6 records it as a known limitation rather than a surprise.

Any fitted state must be fitted from the past-only rows streamed through the context during the
run. No pre-staged models, no pre-computed artefacts, no pickles. Machine learning is permitted in
every lane and mandated in none; it faces the identical turnover, cost-density, neighbourhood and
trial-adjustment discipline as everything else.

---

## 4. Your trial budget

**Every material trial is journaled before you look at any number.** The journal
(`tournament/cup20/research-journal.jsonl`) is organiser-owned and append-only; you request an
append, you never write it yourself. Acceptance consumes the trial even if the run crashes or you
abandon it. A material trial is any evaluation whose tuple of (source bytes, config, feature set,
seed, parameters, window, cost model, risk policy) differs from an earlier one.

- **You have twelve.**
- **You need at least eight accepted trials to nominate.** Fewer is not a nomination.
- **The declared neighbourhood sweep is one trial**, however many points it contains.
- **The falsification battery is one trial** (exact sign inversion + gross-edge placebo).

Both batteries are one trial each *because they are declared in full before they run*. That
concession is what makes the certificate affordable, and it stays honest only under the next rule.

---

## 5. Fix the nominee before you declare the neighbourhood

**You fix your nominee first. Then you declare the neighbourhood. Moving the nominee afterwards
voids the sweep** and costs you another trial for a fresh declared sweep.

Your score is **never** the score of your nominated point. Every scored metric is the per-metric
median across the neighbourhood runs. Nominating a best point is nominating the maximum of a noisy
surface, which is upward-biased by construction; a median over a pre-declared plateau is not. The
same rule is applied on the holdout, so the final ranking is a plateau estimate rather than a
spike.

`neighbourhood.json`:

```json
{
  "coordinates": ["formation_bars", "entry_threshold"],
  "nominee":     {"formation_bars": 30, "entry_threshold": 0.50},
  "points": [
    {"formation_bars": 24, "entry_threshold": 0.50},
    {"formation_bars": 36, "entry_threshold": 0.50},
    {"formation_bars": 30, "entry_threshold": 0.40},
    {"formation_bars": 30, "entry_threshold": 0.60},
    {"formation_bars": 24, "entry_threshold": 0.40},
    {"formation_bars": 36, "entry_threshold": 0.60}
  ]
}
```

It must satisfy all of:

- at least `max(7, 2k + 1)` points **including the nominee**, where `k` is the number of material
  parameters;
- **every point distinct** — no duplicates, and no point equal to the nominee. Distinctness is
  judged on the full coordinate vector. A neighbourhood padded with repeated points is a handful
  of samples wearing a costume, and padding one side of the nominee is a direct lever on the
  median;
- for **every** coordinate, at least one point strictly above and one strictly below the nominated
  value, and each of those variations **material**: at least 5% of the nominee's magnitude for that
  coordinate, or any strictly positive absolute change when the nominee is zero. A variation of
  1e-9 is not an exploration of the surface.

### 5.1 The coordinate rule — read this before you write `strategy.py`

**Every neighbourhood coordinate must be a module-level numeric constant in your frozen
`strategy.py`, named identically to the coordinate, and your nominee's declared value must equal
that constant.**

This exists so the nominated point is provably what the frozen code actually does, rather than a
favourable point merely labelled as the nominee. It is stated here, up front, so an honest
submission is never surprised by it.

- **Module-level** means the top level of the module — including inside a module-level `if` or
  `try`. A value assigned inside a function body or a class body **does not count** and will be
  reported as absent.
- The constant must have **exactly one** value. If a coordinate name is assigned two different
  numeric values anywhere at module scope — by reassignment, or across the branches of an `if` or
  `try` — the submission is **rejected as ambiguous**. Verification parses your code and never runs
  it, so it cannot know which branch would execute; a name whose value depends on a branch is
  therefore not a frozen parameter.

Write it plainly:

```python
FORMATION_BARS = 30        # good: module level, one value
ENTRY_THRESHOLD = 0.50     # good

class Strategy:
    FORMATION_BARS = 30    # NOT counted: class body

if USE_FAST:
    FORMATION_BARS = 10    # rejected: second module-scope value for the same name
```

---

## 6. Your research certificate

`RESEARCH-CERTIFICATE.md` must cover, with journal sequence numbers throughout:

- a transparent **baseline** and its **exact sign inversion**;
- **at least three formation horizons**;
- **at least two rebalance / holding horizons**, with the **rebalance phase offset swept** for any
  cadence longer than one bar. Phase is a first-order axis, not a detail: a cadence-3 result that
  was only ever run at one phase offset is a result about that phase, not about that cadence;
- **controls-off, individual-control and combined-control ablations**;
- **long, short and chop role checks**;
- the **declared neighbourhood** and its sweep;
- **every failure and every abandoned attempt**, with its journal sequence number.

The certificate is not a write-up of what worked. It is the complete record, including what did
not.

---

## 7. Nomination discipline

- **A negative candidate is evidence, not a submission.** Do not nominate because your budget ran
  out or your wall-clock ran down. "No nomination, here is why" is a legitimate and respectable
  outcome, and CUP-20 is explicitly prepared to record no winner at all.
- **You may pivot mechanism once**, documented, and only after your original thesis is falsified
  across the full research matrix above. One pivot, not a search over mechanisms.
- Your candidate is scored against conjunctive hard floors — every one, never waived, never
  lowered, never rounded into compliance. A missing or non-finite value fails. Among them: net
  Sharpe ≥ 0.80 at 1× cost and ≥ 0.50 at 2×, maximum drawdown ≤ 0.20, realised volatility ≥ 0.06,
  annualised one-way turnover ≤ 25×, gross edge ≥ 40 bps per unit turnover, cost share of positive
  gross PnL ≤ 30%, ≥ 500 executed trades, ≥ 70% of neighbourhood points positive, and
  trial-adjusted confidence ≥ 0.90. **Every floor names its cost level in §7.3, and a floor that
  names none is evaluated at base (1×) cost.** The §7.4 ranking reads its inputs at 2× instead, so
  drawdown, positive-quarter fraction and turnover are each measured twice, at two levels — the
  floors gate the realistic book, the ranking rewards the one that survives a cost shock.
- The confidence floor is `max(0, min(1, 1 - T * (1 - B)))`, where `T` is your **complete accepted
  trial count**. Every trial you spend raises the bar the same candidate has to clear. Spend them
  on questions, not on variations.
- **An exact sign inversion that clears the core floors disqualifies the candidate.** If flipping
  every sign also works, the apparent edge is a construction artifact, not a mechanism.

---

## 8. Stop conditions

You are done when you have either:

- frozen one candidate — `strategy.py`, `risk_policy.json`, `neighbourhood.json`, `README.md` — plus
  `RESEARCH-CERTIFICATE.md`, with ≥ 8 accepted trials and the nominee fixed before the
  neighbourhood was declared; or
- concluded that your mandate does not support a candidate that clears the floors, and written that
  up with the same evidence standard.

Either way you stop there. You do not evaluate anything on the holdout, you do not compare yourself
to another team, and you do not touch `data/cup20/sealed/`.

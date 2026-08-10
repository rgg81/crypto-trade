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

**"Post-cutoff" means strictly after the cutoff — `2024-08-02` onward.** The cutoff instant itself,
`2024-08-01T00:00:00Z`, is *not* a post-cutoff date and does not trip the scan. It is the first
instant your data excludes, so writing it down says only where your window stops; it is printed in
the charter's window table, in `config.toml` twice over (as `is_end` and as `sealed_start`), and in
section 1 above. The harness also writes it into every packet it hands you — the `window` and
`folds` banner lines of a coaching packet or a sweep report both end at it. **You never need to
redact, strip or work around organiser output to keep your workspace scanning clean.** If a scan
ever flags something the organiser itself wrote into your tree, that is an organiser defect: say so
and stop, rather than editing the evidence.

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
  These are applied **by reduction, never by rejection**, and applied twice: to your own normalised
  book before the reference pass, and again to the executed weights after the common risk unit.
  **Your weights may therefore be trimmed, and the trim is disclosed** — see the note below;
- the **common risk unit**: your normalised targets are evaluated once with your declared risk
  policy applied to produce a *reference book*; the evaluator then scales your normalised weights
  by `clamp(0.10 / σ_t, 0.20, 3.0)`, where `σ_t` is the trailing-90-day annualised volatility of
  the reference book's gross bar returns using rows strictly before `t`, caps the result, and
  applies your risk policy again inside the pass it actually executes. See §6 of the charter.

**Your intended weights may not be your executed weights, and you can check.** A book that
concentrates is legal — plenty of mandates produce one, and a cross-sectional book on a 20-name
universe concentrates whenever its filter is selective. It is not rejected; it is *reduced* until
the caps hold, by one uniform per-boundary scale. Two things follow, and neither is hidden from
you:

- **The reduction is not redistributed.** Four equal names at unit gross is 0.25 each, so the book
  executes at 0.20 each and **0.80 gross** — not renormalised back to 1.0. The trimmed 0.05 is not
  pushed onto the other names, because which names you are in and in what proportion is your
  strategy, not the organiser's to rewrite. Every pairwise ratio in your book survives exactly. A
  book asking 0.90 of one name executes at 0.20 of it: the cap binds, it just binds by reduction.
- **Every run's packet says how far you were trimmed.** `summary.json` carries an `exposure_caps`
  block with one entry per application (`requested`, for your own book; `executed`, for after the
  risk unit), each recording how many boundaries carried a target, how many were reduced, the
  smallest and median reduction, and which cap bound. If `requested.minimum_scale` is 0.22, your
  book ran at roughly a fifth of the concentration you asked for, and the number to reason about is
  that one — not the weights you returned.

Being trimmed is not a penalty in itself, but it is not free either: less gross means less realised
volatility, and the 0.06 volatility floor below applies to a concentrated book exactly as it does
to a diversified one. Charter §14.7 records that as a known limitation rather than a surprise.

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
   would see on your own book. What survives intact is everything about shape: which symbols, which
   side, when to stop out, how fast to turn over. Charter §6 states this in full; §14.6 records it
   as a known limitation rather than a surprise.

   **`volatility_target.enabled` must be `false` (charter §6, amendment A3).** Declaring `true` is
   refused by `--check`, which is free, so it can never cost you a trial — but it is a hard refusal,
   not a warning. The field is banned because it is self-referential: the policy measures the
   volatility of the book it has already scaled, so realised gross and turnover settle at a
   fractional power of the number you declare rather than being pinned to it. A team short of the
   turnover floor could therefore clear it by declaring a smaller target rather than by trading
   less, which is a floor passed by paperwork. **If you are over the turnover floor, fix it in the
   signal** — trade a slower formation, hold longer, rebalance less often, or soften the weights.
   Two teams before you found this interaction; both declined to use it and said so in their
   certificates.

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
- **The declared neighbourhood sweep is one trial**, however many points it contains. Run it with
  `cup20_evaluate.py --neighbourhood` (§5.3), which runs every point for you under that one trial.
  Evaluating your points one at a time as ordinary candidates spends one trial *each*, and there is
  no rule that would give them back.
- **The falsification battery is one trial** (exact sign inversion + gross-edge placebo).

Both batteries are one trial each *because they are declared in full before they run*. That
concession is what makes the certificate affordable, and it stays honest only under the next rule.

**Budget the wall clock too, not only the count.** Measured on the real snapshot: a point is
**490 s**, a seven-point sweep at the default four workers is **1223 s**, and the falsification
battery is about forty minutes. Ten points plus both batteries is most of a working day of compute;
a plan that discovers that on its last afternoon is a plan that nominates nothing.

---

## 5. The two commands

**You never write your own scorer and you never write to the journal.** Two organiser-owned
commands do both, and every number you are entitled to act on comes out of them. Run them from the
repository root.

If twelve teams each built a private scorer, twelve teams would disagree about which cost level
each floor reads, where the fold boundaries fall, and whether the risk unit runs before or after
the exposure caps — and none of those twelve would be the one the organiser scores nominations
with. These two are.

### 5.1 `cup20_trial.py` — record a material trial

```
uv run python scripts/cup20_trial.py \
  --team team-NN --candidate <candidate-id> \
  --purpose "the question this trial answers, in one sentence" \
  --seed <int> --roles long,short \
  [--kind point|neighbourhood|falsification] \
  [--parameter formation_bars=30 --parameter entry_threshold=0.5]
```

It appends one `trial_accepted` record to the hash-chained journal and prints the **sequence
number** — the number your research certificate cites, and the number the evaluator looks for.

What it records is the material tuple: your candidate directory's source digest, the config
digest, your `risk_policy.json` digest, the IS snapshot digest, the seed, the window, the cost
model, your declared parameters, your declared roles and the trial kind. Two runs whose tuples are
equal are one trial; any difference is a new one.

- **`--roles` is a claim you make before the numbers exist.** It is checked against the sides your
  book actually traded (charter §7.3, "roles are observed, not declared"), and you cannot re-declare
  after seeing which sleeve paid — re-declaring is a new material trial.
- **`--kind`** defaults to `point`. Use `neighbourhood` for the declared sweep and `falsification`
  for the battery; each is one trial, and each kind is its own material trial, so a `point` trial
  does not licence a battery.
- **`--kind neighbourhood` validates your `neighbourhood.json` before it appends anything** — every
  §6 rule and the §6.1 coordinate rule against your frozen source, plus a dry run of the
  substitution the sweep will perform on every point. A declaration that could not be swept is
  refused at the append and **costs you nothing**. A trial is spent at acceptance and never
  refunded, so this is the only place it could cost nothing.
- **The thirteenth is refused**, by name and count. There is no override and no extension.

### 5.2 `cup20_evaluate.py` — evaluate a candidate

```
# no market data, no metric, NO TRIAL — run this as often as you like
uv run python scripts/cup20_evaluate.py --team team-NN --candidate <id> --check

# the scored evaluation of ONE point: full in-sample window, 1x / 2x / 3x cost. About eight minutes.
uv run python scripts/cup20_evaluate.py --team team-NN --candidate <id>

# the declared neighbourhood sweep — YOUR ACTUAL SCORE. About twenty-five minutes for seven points.
uv run python scripts/cup20_evaluate.py --team team-NN --candidate <id> --neighbourhood

# the falsification battery: exact sign inversion + gross-edge placebo. About forty minutes.
uv run python scripts/cup20_evaluate.py --team team-NN --candidate <id> --falsification
```

Before it evaluates anything it does two things, in this order, and refuses on either:

1. **the blindness scan**, over your *entire* workspace — notes, notebooks, logs, `__pycache__`,
   symlinks and their targets — for every prohibited path, every post-cutoff date literal and every
   other team's directory. Catching that now costs you an edit. Catching it at nomination costs you
   the tournament. It runs **before any of your code is imported**, in every mode.
2. **the accepted trial**, for *exactly* this candidate state. If your source digest does not match
   the digest recorded in the trial, that is a new material trial and the command says which field
   moved. Journal it and run again. The digest covers your whole candidate directory, so editing
   `neighbourhood.json` after journaling is a new material trial too.

Then it loads `build_strategy()` out of your `strategy.py`, runs the **full in-sample window** with
the frozen `[execution]` and `[risk_unit]` config and your declared `risk_policy.json`, and prints a
coaching packet:

- the **metric vector at 1×, 2× and 3× cost** — every metric, at every level;
- the **four fold Sharpes** at 2×, the level §7.3 floors them at;
- the **gate vector**, one line per hard floor, with the value you achieved, the floor you needed
  and which comparison it was. You are told what you failed *by*, not merely that you failed;
- the **`exposure_caps` trim block**, both applications, so you can see how far your book was
  reduced and which cap bound (charter §4);
- the trial-adjusted confidence, with `B` and `T` shown separately, so the price of another trial
  is visible before you spend it;
- the **indicative ranking score `G`**.

Two things it will never print. It never prints `QUALIFIED` — two gates
(`neighbourhood_positive_fraction` and `sign_inversion_not_profitable`) cannot be decided from a
single point, and they are shown as `----`, not as passes. And the packet is **your nominated
point's own vector, not your score**: §6 scores the per-metric median across your declared
neighbourhood, which is always below the maximum of a noisy surface.

**There is no short-window mode, on purpose.** The window is part of the material tuple, so a
shorter window is a different trial whose number is comparable to nothing — not to your other runs,
not to the floors, not to another team. `--check` is what exists instead, so you never spend a trial
discovering a typo.

**The battery is run by the harness, not by you.** `--falsification` negates every emitted weight
(leaving `None` and `{}` alone, because neither carries a direction) and scores the inversion
through the identical pipeline against the core floors; an inversion that clears them is
disqualifying. It then runs eight placebo books that keep your weight multiset and rebalance
schedule exactly and randomise only *which* eligible symbol receives which weight, scored on **gross**
edge. You cannot accidentally skip a mandatory falsifier, and you cannot implement it differently
from anyone else.

### 5.3 `--neighbourhood` — the sweep, and the only number that is your score

```
uv run python scripts/cup20_evaluate.py --team team-NN --candidate <id> --neighbourhood
```

**This is one trial, however many points your neighbourhood contains** (§4). Journal it as
`--kind neighbourhood` first; the evaluator refuses without it, exactly as it does for a point.

It runs **every declared point including the nominee**, over the full in-sample window, through the
identical pipeline a single-point evaluation uses, and reports the **per-metric median across the
points**. That median is your score. Your nominee's own vector is printed underneath it, beside the
median for every metric, and labelled `DIAGNOSTIC ONLY — This is NOT your score`. Read the median.

What the packet adds that a single point cannot have:

- **`positive_point_fraction`** against the 70% floor — the fraction of points with positive 1×
  annualised return *and* positive 2× Sharpe. `--neighbourhood` is the only mode that can measure
  this gate; a single-point packet shows it as `----`.
- **`B` as the per-point median** of the bootstrap positive fraction, so the trial-adjusted
  confidence is a property of the plateau rather than of the spike.
- **an inertness check on the results** (charter §7.2, amendment A1). No point may reproduce your
  nominee's scored metric vector *exactly*. Declaring a coordinate that varies by the required 5%
  but that your strategy quantises — a fraction you `round()` into a name count is the usual case —
  produces a byte-identical book, and an inert point sitting on the nominee drags the median onto
  the peak the sweep exists to discount. A sweep containing one is **void and costs the trial**, so
  choose coordinates your strategy visibly responds to. This is the one validity check that cannot
  run before the sweep does, because inertness is only knowable from the results. If it fires, the
  error names the offending points.
- **one `strategy.py` digest per point**, so what actually executed is on the record. `--keep-variants`
  keeps the materialised directories if you want to read them.

It still **never prints QUALIFIED**: the sign-inversion falsifier is a separate trial
(`--falsification`), so that one gate stays `----`.

**How a point is made.** Each point is materialised as a **real file**: your frozen `strategy.py`
with exactly the declared coordinate literals rewritten, and everything else — every other
constant, every comment, every line position — byte for byte identical. That is checked, not
assumed, three ways, and any of the three refuses:

1. both files' coordinate literals are blanked out and the remainders must be **byte-identical**;
2. the variant's parsed constant table must equal your source's at every other name;
3. the imported module must have **bound** the point's value — read back out of the executed
   module's namespace before the run starts.

**Your nominee is not rewritten at all.** Its directory is copied verbatim and the copy's digest is
required to equal your candidate's, so the nominee point runs your frozen bytes.

This is why §6.1's coordinate rule exists, and it is now load-bearing rather than advisory: a
coordinate that is not a single-valued module-level numeric literal cannot be rewritten, and the
sweep refuses. Run `--check` — it dry-runs the substitution for every point, free, and tells you
before you spend the trial.

**Every point runs in its own freshly spawned interpreter**, so no point can leave state behind for
the next. `--workers N` (default `min(4, points)`) only changes the wall clock; the answer is
identical at every worker count.

**What it costs.** Measured on the real snapshot with a real seven-point neighbourhood, not
estimated:

| | |
|---|---|
| `--check` (free, no trial, no market data) | **0.4 s** |
| one point on its own (`cup20_evaluate.py`, no flag) | **489.7 s** — about 8 minutes |
| `--neighbourhood`, 7 points, default 4 workers | **1222.8 s** — about 20 minutes |
| `--neighbourhood`, 7 points, `--workers 1` | ≈ 7 × 490 s — about 57 minutes |

Four workers is 2.8× faster than serial, not 4×: the points are memory-bandwidth bound as well as
CPU-bound, so a point that takes 490 s alone takes about 695 s with three others beside it. Raising
`--workers` past 4 buys less than it looks like it should, and on a shared machine it costs the
other eleven teams.

Budget for it. It is one trial, and it is the trial that produces your score.

### 5.4 `risk_policy.json` is required

Your declared risk policy is part of the material tuple, so every candidate carries one from its
first trial. Declaring nothing is a legitimate declaration — write it out explicitly:

```json
{
  "schema_version": 1,
  "policy_id": "team-nn-flat",
  "same_boundary_reentry": true,
  "volatility_target": {
    "enabled": false, "lookback_days": 30, "annualized_target": 0.10,
    "minimum_scale": 0.5, "maximum_scale": 1.0
  },
  "drawdown_brakes": [],
  "position_stop": {"enabled": false, "loss_fraction": 0.5, "cooldown_bars": 0},
  "time_stop": {"enabled": false, "maximum_holding_bars": 10, "cooldown_bars": 0},
  "turnover_limit": {"enabled": false, "maximum_one_way_turnover": 1.0},
  "side_scaling": {"long_scale": 1.0, "short_scale": 1.0}
}
```

Remember §3: the policy declares **shape, not scale**. It runs inside a book the common risk unit
has already resized.

### 5.5 The order, every time

```
1.  write / edit  strategy.py, risk_policy.json
2.  cup20_evaluate.py --check          (free, seconds — do this until it is clean)
3.  cup20_trial.py    ...              (costs one of your twelve; returns a sequence number)
4.  cup20_evaluate.py                  (490 s measured; prints the coaching packet)
5.  read the packet, decide, and write down what you learned — including if it failed
```

Repeat. Then, once your nominee is **fixed** (§6) and your `neighbourhood.json` is written:

```
6.  cup20_evaluate.py --check                    (free — confirms every point can be materialised)
7.  cup20_trial.py --kind neighbourhood ...      (one trial for the whole declared sweep)
8.  cup20_evaluate.py --neighbourhood            (1223 s measured; prints YOUR SCORE)
9.  cup20_trial.py --kind falsification ...      (one trial for the whole battery)
10. cup20_evaluate.py --falsification            (about forty minutes)
```

That is **two** trials for steps 7–10 in total, and about an hour of wall clock. Plan for it.

**Step 3 before step 4 is not a convention, it is enforced**, and so is step 7 before step 8. The
evaluator refuses to run without an accepted trial of the right kind for exactly the candidate state
on disk, which is what makes "journaled before you look at any number" a fact rather than an
aspiration.

**Step 6 before step 7 is free and you should not skip it.** A neighbourhood that fails validation
is refused at the append and costs nothing — but only if you find out at the append. Once a trial is
accepted it is spent, and there is no refund for a declaration you then fixed.

---

## 6. Fix the nominee before you declare the neighbourhood

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
  1e-9 is not an exploration of the surface;
- every coordinate value **finite**. `NaN` slips past every comparison above — every IEEE-754
  comparison with `NaN` is false, so it is neither a duplicate nor a variation — and there is no
  numeric literal to write it into your source as.

Every one of these is checked when you journal the `--kind neighbourhood` trial, and a failure
refuses the append, so an invalid neighbourhood costs you nothing. `--check` checks them for free
as often as you like.

### 6.1 The coordinate rule — read this before you write `strategy.py`

**Every neighbourhood coordinate must be a module-level numeric constant in your frozen
`strategy.py`, named identically to the coordinate, and your nominee's declared value must equal
that constant.**

This exists so the nominated point is provably what the frozen code actually does, rather than a
favourable point merely labelled as the nominee — and it is also **what makes the sweep possible at
all**. §5.3 materialises each point by rewriting exactly those literals in your frozen source. A
coordinate that is not one cannot be rewritten, and the sweep refuses rather than guessing. It is
stated here, up front, so an honest submission is never surprised by it.

- **Module-level** means the top level of the module — including inside a module-level `if` or
  `try`. A value assigned inside a function body or a class body **does not count** and will be
  reported as absent.
- The constant must have **exactly one** value. If a coordinate name is assigned two different
  numeric values anywhere at module scope — by reassignment, or across the branches of an `if` or
  `try` — the submission is **rejected as ambiguous**. Verification parses your code and never runs
  it, so it cannot know which branch would execute; a name whose value depends on a branch is
  therefore not a frozen parameter.
- The value must be a **plain numeric literal on one line**, optionally negated. Not an expression,
  not a computation, not a literal split across lines with a `\` continuation. `LOOKBACK = 30` and
  `SKEW = -1.5` are fine; `LOOKBACK = 15 * 2` is not a literal, and `SKEW = -\`↵`  1.5` cannot be
  rewritten without touching two lines.
- The name must still be **bound after import**. The sweep reads each coordinate back out of the
  imported module before it runs anything, and refuses if the module bound something else or
  nothing at all. A constant assigned only in a module-level branch that did not run is not a
  parameter the frozen code is governed by.

Write it plainly:

```python
FORMATION_BARS = 30        # good: module level, one value, one line
ENTRY_THRESHOLD = 0.50     # good
SKEW = -1.5                # good: a negated literal is still a literal

class Strategy:
    FORMATION_BARS = 30    # NOT counted: class body

if USE_FAST:
    FORMATION_BARS = 10    # rejected: second module-scope value for the same name

WINDOW = 15 * 2            # rejected: an expression, not a literal — the sweep cannot rewrite it
```

**Read the constant, do not re-derive it.** The sweep changes the module-level constant and nothing
else, so anything downstream that reads it — a default argument, a class attribute set from it, a
table computed at import — moves with it. Anything that hard-codes the same number somewhere else
does not, and that copy would stay at the nominee's value at every point of your sweep.

`--check` dry-runs the rewrite for every declared point and tells you, free, before you spend the
trial.

---

## 7. Your research certificate

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

## 8. Nomination discipline

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

## 9. Stop conditions

You are done when you have either:

- frozen one candidate — `strategy.py`, `risk_policy.json`, `neighbourhood.json`, `README.md` — plus
  `RESEARCH-CERTIFICATE.md`, with ≥ 8 accepted trials and the nominee fixed before the
  neighbourhood was declared; or
- concluded that your mandate does not support a candidate that clears the floors, and written that
  up with the same evidence standard.

Either way you stop there. You do not evaluate anything on the holdout, you do not compare yourself
to another team, and you do not touch `data/cup20/sealed/`.

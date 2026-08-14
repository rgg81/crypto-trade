# CUP-20 Tournament Charter

Status: pre-activation authority
Tournament: `cup20`
Machine contract: `tournament/cup20/config.toml`

This charter controls meaning. The config controls numerical policy. Activation MUST fail on
disagreement. Before the first result an activation record hash-binds this charter, the config,
the implementation, the dependency lock, the data authority, the pure-crypto audit and the focused
test output. Later changes require a prospective, append-only amendment made before the affected
data are accessed. Historical evidence is never rewritten.

## 1. Purpose

Find the crypto perpetual-futures strategy that **generalizes best out of sample with the lowest
drawdown**, using a twelve-team blind tournament on a deliberately stable top-20 pure-crypto
universe, a four-year in-sample research window, and a two-year sealed holdout that no team can
physically read.

The tournament produces exactly one winner, and that winner earns a **six-month forward paper
observation** — not capital. The holdout decides the tournament; the forward record is what would
later justify money.

### 1.1 Non-goals

- Maximum absolute return. Return appears only as a floor and inside Calmar.
- Beating buy-and-hold. Irrelevant; the objective is risk-adjusted consistency.
- Producing a winner at any cost. If no candidate clears the frozen floors, CUP-20 records **no
  winner** and no paper desk opens.

## 2. Evidence layers

| Layer | Interval (UTC) | Team access | Purpose |
|---|---|---|---|
| Warm-up | symbol listing → `IS_START` | historical context only, never scored | indicator initialisation |
| **IS research** | `[IS_START, 2024-08-01)` | full artifacts, unlimited inspection, budgeted trials | research laboratory |
| **Sealed holdout** | `[2024-08-01, 2026-08-01)` | none, ever, until top-3 are frozen | one atomic observation |
| **Forward paper** | from freeze date, 6 months | n/a | genuinely unseen deployment test |

`IS_START` is **computed, not chosen**: the first weekly reconstitution boundary at which the
eligible pool contains at least 20 names. It is expected to land near 2020-08 and is frozen into
the data manifest at snapshot build. Defining it mechanically removes an arbitrary organiser
degree of freedom.

### 2.1 Disclosed contamination

The window `[2024-07, 2026-06)` has already served as the revealed holdout in four prior
tournaments in this repository (crypto-cup-01, top40-v3, top40-v4-R1, MN4). CUP-20's holdout
overlaps it almost entirely. This is disclosed rather than hidden, and neutralised structurally,
not by good intentions:

- Team agents are fresh, receive only the IS snapshot, and cannot read prior-tournament
  directories (§5).
- The twelve mechanism mandates (§9) are fixed in the charter **before any team starts**, so the
  organiser cannot steer the field toward mechanisms already known to have worked.
- Advancement is a **frozen numeric formula** evaluated mechanically (§7), not an organiser
  judgement call.
- The charter states plainly that holdout success authorises the paper desk, and only the forward
  record can later authorise capital.

## 3. Universe

**Rule.** At each weekly reconstitution boundary:

1. **Eligibility.** A symbol is eligible only if it is a USDT-quoted, USDT-margined `PERPETUAL`
   contract, passes the fail-closed pure-crypto policy, is not delisted at the boundary, has a
   **complete 180-day trailing history**, and **has a mark price at every decision boundary of the
   membership period it is being admitted to** (see below). The completeness requirement doubles as
   the minimum listing age and is the single rule that removes launch-hype listings.

   The mark-coverage half is not bookkeeping. The evaluator prices every position at the boundary
   mark and refuses to run a boundary at which a member has an executable bar open and no mark, so
   an unmarkable member crashes **every** candidate in the field before any strategy code runs —
   which is what a member with 21 such boundaries did before this clause existed. A symbol the
   evaluator cannot mark is not tradeable, so it is not eligible. The window checked is the
   membership period `[t_i, t_{i+1})` the admission commits to: not the boundary alone (which says
   nothing about the twenty intra-week decisions that follow), and not the 180-day lookback (mark
   history is an archive property, not a listing age — Binance's mark archive begins on one date
   for every symbol at once, so a trailing-mark rule would admit nobody for six months after it and
   move `IS_START`).
2. **Ranking.** Rank eligible symbols by trailing **180-day USDT quote volume**, descending.
3. **Hysteresis.** Incumbents survive while rank ≤ 25. New entrants require rank ≤ 20.
   Deterministic construction: keep incumbents with rank ≤ 25 in rank order, truncated to 20; fill
   any remaining slots from non-incumbents with rank ≤ 20, in rank order.
4. **Size.** Exactly 20 when the eligible pool allows; `min(20, eligible)` otherwise. Because
   `IS_START` is defined as the first ≥20 boundary, this only binds if delistings ever shrink the
   pool. A boundary with fewer than 8 members is not scored.

**Exclusions (fail closed).** Stablecoins, tokenised or direct TradFi, equities, funds, metals,
commodities, indexes, FX, leveraged tokens. Unknown or ambiguous classification is excluded. A
Binance listing is not sufficient evidence of eligibility. A crypto protocol token is not TradFi
merely because of an exchange sector label; the asset-level and contract-level checks are
authoritative.

**Measured stability** (validated on the existing frozen snapshot before adopting the rule):

| Rule | Changes/period | Periods unchanged | Distinct names ever |
|---|---:|---:|---:|
| Naive weekly, ~30d volume, no hysteresis | 1.66 | 40 / 334 | 203 |
| Weekly, 180d volume, no hysteresis | 0.68 | 154 / 327 | 121 |
| **Weekly, complete-180d volume, hysteresis 20/25** | **0.29** | **239 / 309** | **70** |

The three rows above were measured at design time on a weekly-sampled proxy. The authoritative
numbers are the built artifact's own, **stated over the in-sample window** — this document is
team-visible, and how many names the universe holds after the cutoff is a fact about the holdout.
Across the IS window's 207 reconstitutions the adopted rule delivers **0.28 changes per week, 159
of 206 transitions completely unchanged, and 62 distinct names**, with exactly 20 members at every
boundary. That confirms the design-time estimate's direction and magnitude while being measured on
the real thing rather than a proxy. The organiser's full-window figures exist and are recorded in
`tournament/cup20/private/universe-summary.json`, which is not team-visible.

(These are the figures **after** the mark-coverage clause of rule 1. Before it the same rule gave
0.29 changes per week and 63 distinct names, over the same 207 reconstitutions and the same
`IS_START`; adding mark coverage moved 28 membership rows and removed exactly one name, IOTAUSDT,
whose mark history begins after it first qualified.)

The ranking statistic is the **median** daily quote volume over the trailing window, not the mean.
A coin's launch-week volume spike lifts a 180-day mean far more than a 180-day median, so ranking
on the mean admits transient listings into a universe meant to be blue-chip. Re-measured on the
built data over the same IS window, the mean gave 66 distinct names at 0.30 changes per week
against the median's 62 at 0.28: it admitted COMP, ENS, LINA, MANA, OMG, TOMO and WAVES, and passed
over BAND, MKR and SEI. The choice was fixed before any holdout number existed and is not
conditioned on one. It is a validated field of the machine contract, so the config and the
implementation cannot silently disagree about it.

The adopted rule produces memberships that read as a blue-chip crypto index
(BTC/ETH/BNB/XRP/SOL/DOGE/ADA/LINK/LTC/AVAX/DOT/…) and eliminates the transient hype names that
the naive rule admits.

## 4. Execution contract

Owned entirely by the organiser. No team code touches any of it.

- **Decision grid:** 8h boundaries at 00:00 / 08:00 / 16:00 UTC.
- **Fills:** at the **next bar open** after the decision. The execution open is never exposed to
  team code.
- **Costs:** 5 bps taker fee + 2.5 bps slippage, per side. Every result is independently re-scored
  at **1×, 2× and 3×** cost.
- **Funding:** native per-event settlements summed into the holding interval `(open[t], open[t+1]]`.
  Nearest-match funding is explicitly forbidden — it silently drops roughly half the events on
  symbols that settle 4-hourly.
- **Delisting:** force exit at the last executable open. No survivorship rescue.
- **Participation:** per-symbol executed notional capped as a fraction of the bar's traded volume.
- **Caps:** gross ≤ 1.0× equity — the evaluator is unlevered by construction, which is also the
  honest setting for a book headed to a real paper desk; per-symbol |weight| ≤ 0.20 of equity.
  **Applied by reduction, never by rejection**, at **both** ends of the common risk unit: to the
  team's own normalised book before the reference pass, and again to the executed weights after the
  scalar. Once is not enough in either direction — the reference pass evaluates the team's own book
  and would reject a concentrated one before any scalar exists, and the scalar reaches 3.0, so a
  book capped only before it is over the caps again after it. Each application is **one uniform
  per-boundary scale**, so it never redistributes the trimmed weight and never raises exposure:
  four equal names run at 0.20 each and 0.80 gross rather than being renormalised back to 1.0, and
  a book asking 0.90 of one name still executes at 0.20. Every reduction is disclosed per run
  (§6).
- **Solvency:** equity must remain finite and strictly positive; a breach is terminal for the run.

## 5. Blindness — physical custody first, then four checked layers

Blindness has one control that is physical and four that are checks. The difference matters more
than the count, so custody is stated first and separately.

**Layer 0 — quarantine, for the whole research phase.** Before the first team starts, both
`data/cup20/sealed/` and `data/cup20/acquisition/` (the un-truncated superset, which leaks the same
rows) are **moved out of the working tree entirely**, to a location outside the repository. For the
entire period teams are running, there is no path a team process can name that reaches the holdout,
because the bytes are not under any of them. This is the only layer that does not depend on anyone
keeping a promise, and it covers the only window in which a team is in a position to act.

Quarantine writes a committed receipt recording where each tree went, its whole-tree digest, and
the sealed manifest digest the activation record bound. Restoring is refused unless every one of
those still matches, measured **at the quarantine location, before anything moves**, so a holdout
that was altered while out of the tree never re-enters it. Restoring is also refused until the
selection freeze exists: the holdout does not come back while a team could still act on it. Both
events are appended to the hash-chained journal, which is what makes the coverage claim
*reviewable*: `holdout_quarantined` at a lower sequence number than every `trial_accepted`, and
`holdout_restored` above all of them, is evidence that no trial was accepted while the holdout was
reachable — and re-ordering that to look otherwise breaks the chain.

Custody is two claims, not one, and they are checked by different commands. *Absence* — the trees
are not on any path a team can name — is what `verify_quarantine_in_effect` establishes, and it
reads no bytes. *Integrity* — what is sitting in quarantine is still the holdout that left the tree
— is what `verify_quarantine_integrity` establishes, by recomputing both whole-tree bundle digests
against the receipt, re-verifying the whole activation record with the sealed root read at the
quarantine location, and checking the canary token. The research phase runs for months, so the
second is run **periodically during it**, not only at restore: `restore_holdout` performs the same
comparisons, but it runs after the last team has finished, when corruption can only be answered by
voiding the tournament. A check that reports on absence must never be described as reporting on
integrity.

1. **Truncated data root.** Teams receive `data/cup20/is/`, containing bars, funding, membership,
   contract metadata and exchange info **strictly before 2024-08-01**. Not one row at or after the
   cutoff is in it, in any timestamp column of any dataset, and the contract metadata is censored so
   that a symbol delisting after the cutoff is indistinguishable from one still trading. Holdout
   rows live in `data/cup20/sealed/` under a different manifest hash.

   What this layer does **not** claim: outside the quarantine window the holdout rows are not
   physically absent from the machine. Once restored, `data/cup20/sealed/` sits on the same
   filesystem, under the same account, with the same permissions as the in-sample snapshot, and so
   do the acquisition snapshot and the organiser-only artifacts under `tournament/cup20/private/`.
   Nothing at the operating-system level stops a process from opening any of them. What is true is
   narrower and worth stating precisely: those rows are **not in the team's data root**, so no
   ordinary path — a glob of the data directory, a merge, a `read_parquet` of what was handed over —
   can reach them by accident. Deliberate access is what layers 3 and 4 are for: the playbook
   prohibits every organiser-only path by name, and the pre-flight source scan matches those paths
   against both the content and the file names of the frozen archive before a single number is
   scored. Blindness therefore rests on custody **plus** absence-from-the-data-root **plus** the
   prohibition **plus** the scan — not on absence alone.

   The same is true of version control, and for the same reason it is stated rather than claimed
   away: organiser artifacts that described the holdout were committed and later removed, and a
   removal does not erase a branch's history. Rewriting shared history was judged more dangerous
   than the residual exposure, so the prohibition is extended instead — it covers **any earlier
   revision of a prohibited path**, retrieved by any means. The scan reads a team's frozen archive,
   so it catches a committed command but not an interactive one; this layer is honour-bound, and
   saying so is more useful than pretending the bytes are gone.
2. **Narrow protocol.** Teams implement
   `target_weights(context: DecisionContext, *, seed: int) -> Mapping[str, float] | None`.
   `DecisionContext` exposes only bars closing at or before the decision time, funding strictly
   before it, and the eligible symbol list. It exposes **no execution price, no fills, no PnL, no
   costs**. `None` means "hold current quantities"; `{}` means "go flat". Any fitted state must be
   fitted from the past-only rows streamed through the context during the run — no pre-staged
   models, no pre-computed artifacts.
3. **Namespace isolation.** A team may write and read only under
   `tournament/cup20/teams/team-NN/`. Reading another team's directory, any prior-tournament
   directory, or referencing any post-cutoff date literal is a pre-flight disqualification,
   enforced by a source scan of the frozen archive. The same applies to every organiser-only
   surface, each of which is a pattern in `FORBIDDEN_PATTERNS` and a row in the playbook's
   prohibited table: `data/cup20/sealed/`, `data/cup20/acquisition/`,
   `tournament/cup20/private/` and the whole of `reports-cup20/`.

   The pre-flight scan reads the frozen archive, which is the right surface for a gate and the
   wrong one for a review: a team that left its evidence in a research note, a notebook, a log or a
   `.pyc` hands in a clean archive. The integrity review therefore scans each team's **entire
   workspace** — every regular file, no extension allowlist, no directory exclusions, symlinks
   reported both as symlinks and by where they point, and any file too large to read reported
   rather than skipped.
4. **Future-corruption test.** The organiser corrupts every row strictly after each decision
   boundary and asserts byte-identical target weights. Failure is terminal.

**The window custody cannot cover.** Scoring the finalists (phase 3) requires the sealed data to be
present and readable, so two tripwires watch that window instead, and both are weaker than
quarantine:

- A **canary file** inside the sealed tree carries a high-entropy token that exists nowhere else.
  The token turning up in any team artifact is evidence the tree's bytes were read and kept. It
  detects a bulk read that persisted its output; it does **not** detect a targeted read of one
  parquet file, which never touches the canary.
- An **access-time tripwire**. Every sealed file's `atime` is back-dated 48 hours and the armed
  value recorded, so that under `relatime` — which updates `atime` on read only when the stored
  value is older than the file's own modification time or older than 24 hours — the next read is
  always recorded. It does **not** work on a `noatime` mount (the report says so from
  `/proc/mounts` rather than reporting a clean result), it can be bypassed with `O_NOATIME` by the
  file's own owner, it can be reset by anyone who can call `utime`, and it says nothing about who
  read the file or about a copy of the tree read elsewhere.

**Reviewability.** After the tournament, the organiser runs the written procedure in
`tournament/cup20/INTEGRITY-REVIEW.md` before advancing anyone: quarantine bracketed the whole
research phase, every team's workspace scans clean, every nomination's frozen archive scans clean,
every declared neighbourhood coordinate verifies against the frozen source, the journal chains
verify, and the sealed manifest is unchanged from activation. The tournament's claim is not that
cheating was impossible; it is that the record can be checked and says what happened.

## 6. Common risk unit

Each strategy is normalised to a common ex-ante risk level so that drawdown comparisons measure
**tail behaviour and regime timing** rather than who chose to trade smallest.

Scoring one candidate is **two evaluator passes over the same targets**. The first produces a
*reference book*, whose only purpose is to measure volatility and which is never itself scored.
The second produces the *executed book*, on which every floor and every score is computed.

**Pass 1 — the reference book.**

1. Team returns raw target weights. The evaluator normalises them to unit gross
   (`Σ|w| = 1`), preserving relative sizing and net exposure. This is the **requested** book.
2. The requested book is reduced by one uniform per-boundary scale until the §4 caps hold, and the
   result is evaluated once, at base cost, with the team's own declared risk policy applied
   (volatility target, drawdown brakes, position stops, time stops, turnover limits, side scaling).
3. **Common risk unit.** Let `σ_t` be the annualised standard deviation of the reference book's
   **gross** bar returns over the trailing 90 days, using rows strictly before `t`. Gross returns
   are used deliberately: it removes any circularity between the scalar and the costs it induces,
   and volatility is dominated by exposure, not by fees.

   ```
   s_t = clamp(0.10 / σ_t, 0.20, 3.0)          if ≥ 90 bars of history
   s_t = 1.0                                    otherwise
   ```

**Pass 2 — the executed book.**

4. Executed weights = `s_t × reference weights`, then reduced by one uniform per-boundary scale
   until the §4 gross, net and per-symbol caps hold. The caps *reduce*; they never reject a run
   and never lever a book up. The participation cap is applied by the evaluator at fill time.
5. The declared risk policy is applied again inside this pass, against **this** book's state, and
   the result is scored at 1×, 2× and 3× cost. Each cost level is an independent replay, so a
   declared brake responds to the deeper drawdown a cost shock actually produces.

**The policy runs in the pass it governs.** A risk policy is not a scalar on weights, so it cannot
be applied once and then multiplied through. Of the six declarable primitives, three —
position stops, time stops and the turnover limit, together with the cooldown re-entry blocks the
first two arm — are *order-level* decisions over carried quantities: a stop zeroes a position and
vetoes the team's requested delta for that one symbol for N bars, and the turnover limit prorates
partial fills against the distance from the current position. None of the three has any
representation in target-weight space, and the protocol's rebalance instruction is a row-level
Boolean, so there is no weight that means "hold this one symbol while retargeting the others".
The effect is not marginal: on a sparse mandate that rebalances every sixth boundary, **98% of the
policy's own fills land on boundaries that carry no target row at all**. Each pass therefore has
exactly one equity path, one realised-return history and one set of entry prices and holding ages,
and the policy fires off the pass it is in.

**Two consequences, stated rather than hidden.** First, a declared drawdown brake watches the
*executed* book, which the common risk unit has already resized; on a book the risk unit shrinks,
the same declaration engages at materially fewer boundaries than it would on the reference book.
Second, a team's own volatility target is **forbidden outright** (amendment A3):
`volatility_target.enabled` must be `false`, and a candidate declaring `true` is refused by the free
`--check` before it can cost a trial. The field was originally allowed on the reasoning that it was
largely inert — a declared target may only reduce, and the common risk unit has already pulled the
executed book toward 10% annualised. That reasoning was wrong in the direction that matters. The
policy measures the volatility of the book **it has already scaled**, so the loop settles with
realised gross and turnover at a fractional power of the declared target rather than pinned to it,
and a team short of the turnover floor can clear it by declaring a smaller number instead of by
trading less. That is a floor passed by paperwork. Refusing the field is the only remedy that does
not require the organiser to judge intent, and it is what §6's division already implied: teams
own *shape* — which symbols, which side, when to stop out, how fast to turn over — and the common
risk unit owns *scale*. Both consequences follow from the common risk unit being the tournament's
leveller: where a team's declaration and the common unit disagree about size, the common unit wins.

**Why the caps run at both ends, and why they never redistribute.** Step 2 caps the team's own book
and step 4 caps the organiser's. Neither alone is enough: the reference pass evaluates the
requested weights, so a book concentrated in fewer than five names would be rejected there before
`s_t` existed, and `s_t` reaches 3.0, so a book capped only before the scalar is over the caps
again after it. Capping the reference book does not tilt the risk unit, because the risk unit is
scale-invariant — a uniform trim `c` scales the reference book's gross returns by `c`, so `σ_t`
scales by `c` and `s_t = 0.10 / σ_t` by `1/c`. What the cap changes is the *shape* the caps allow,
which is the point of having them.

The trimmed weight is never pushed onto the other names. A four-name equal-weight book runs at 0.20
each and **0.80 gross**, not renormalised back to 1.0: which names a book is in and in what
proportion is the strategy's expressed intent, and scale is not something a team controls in this
tournament anyway — the common risk unit sets it. Redistribution would also be an evasion surface
rather than a courtesy, because it can *raise* a weight above what the team asked for and so let a
team reach a shape it was not allowed to request. One uniform scale cannot: the executed book is
always a positive multiple of the requested one, every pairwise ratio survives, and a book asking
0.90 of a single name still executes at 0.20.

**Trimming is disclosed, not silent.** Every run's packet carries an `exposure_caps` block with one
entry per application (`requested`, `executed`), each recording how many boundaries carried a
target, how many were reduced, the smallest and median reduction, and which of the three caps bound
at each. A team can therefore tell that its intended weights were not its executed ones and by how
much, and the organiser can see how far a candidate was reduced before comparing it with one that
was not. A reduction below roughly 0.5 at the requested stage means the book is being executed at
less than half the concentration it asked for; that is legal, and it is visible.

Both the **normalised** book (official, all floors and scores) and the **raw** book (diagnostic)
are reported for every run.

**Interaction with the unlevered gross cap.** Because gross is capped at 1.0× equity (§4), the
scalar can always take a book *down* to the common target but cannot take a very-low-volatility
book *up* past unit gross — step 4's cap reduces it back to unit gross rather than failing the
run, so such a book is scored and then judged. The same is true, and more sharply, for a
concentrated book: reduction-only caps mean a four-name book is executed at 0.80 gross and a
single-name book at 0.20, so the risk unit has that much less room to reach the 10% target before
the cap stops it. Such a book is scored and then met by exactly the same 0.06 realised-volatility
floor below — it is not rejected for being concentrated, and it is not excused from being small. It would realise less than the 10% target and
collect an unearned drawdown advantage in the one contest this tournament ranks on. Two things
close that hole rather than one: realised annualised volatility is a **disclosed diagnostic on
every run**, and a candidate whose neighbourhood-median realised volatility falls below **0.06**
fails a hard floor (§7.3). A book that cannot reach 6% annualised volatility at full unlevered
gross is not a deployable book, and it is disqualified rather than rewarded for being small.

## 7. Qualification

### 7.1 Material trials and the research journal

Every organiser-recognised evaluation is appended to a per-team, append-only, hash-chained journal
**before** market data are opened. Acceptance consumes the trial even if the run crashes or is
abandoned.

**What the hash chain does and does not guarantee.** It makes accidental corruption, naive
deletion, renumbering, reordering and truncation detectable — each breaks a sequence number, a
parent link or a record digest. It is **not** a defence against an actor with write access to the
journal file who deletes a record and correctly re-chains every record after it: the digest is
keyless SHA-256 over public bytes, so anyone who can edit the file can also recompute the suffix.
Git-committing the journal does not close this either, since an actor who can edit the file in the
working tree can generally also amend local history, and there is a window between an append and
the commit that captures it.

What actually makes the trial count trustworthy is that **the journal is organiser-owned and teams
never write to it** — teams write only under their own directory (§5). The chain is an audit trail
and an accident detector layered on top of that access boundary, not a substitute for it. This is
stated plainly because a tamper-evidence claim that overstates its own strength is worse than none:
it invites reliance the mechanism cannot carry. A material trial is any evaluation whose tuple of (source bytes, config, feature set,
seed, parameters, window, cost model, risk policy) differs from an earlier one.

**Budget: 12 material trials per team. Nomination requires ≥ 8 accepted trials.** No team may
nominate merely because its budget or wall-clock is exhausted. The append is made by
`scripts/cup20_trial.py`, which is the organiser-owned path teams request through; the budget is
enforced at that append rather than at nomination, so the thirteenth is refused by name and count
before any work is done against it, and `scripts/cup20_evaluate.py` refuses to score a candidate
state no accepted trial describes.

**Preregistered batteries count as one trial each** — an improvement over prior seasons, which
charged each neighbourhood point separately and made the certificate unaffordable:

- the **neighbourhood sweep** (§7.2) counts as **one** trial, because it is declared in full before
  it runs and its output is a robustness estimate, never a selection input;
- the **falsification battery** (exact sign inversion + gross-edge placebo) counts as **one** trial,
  for the same reason.

The nominee must be fixed **before** the neighbourhood sweep is declared. Moving the nominee to a
different point afterwards voids the sweep and requires a fresh declared sweep, costing another
trial. This is what keeps the "preregistered sweeps are free" concession honest.

### 7.2 Neighbourhood-median scoring

A team's score is **never** the score of its nominated point.

Each team declares, before evaluation, a parameter neighbourhood containing the nominee plus
additional points such that:

- the neighbourhood has at least `max(7, 2k + 1)` points, where `k` is the number of material
  parameters;
- **every point is distinct** — no duplicates, and no point equal to the nominee. A neighbourhood
  padded with repeated points is a handful of samples wearing a costume, and padding one side of
  the nominee is a direct lever on the median;
- for **every** declared coordinate there is at least one point strictly above and one strictly
  below the nominated value, and each of those variations is **material**: at least 5% of the
  nominee's magnitude for that coordinate, or a strictly positive absolute change when the nominee
  is zero. A variation of 1e-9 is not an exploration of the surface;
- every coordinate maps to an identically named numeric material parameter in the frozen source,
  **and the nominee's declared value equals the value in that frozen source**, so the nominated
  point is what the frozen code actually does rather than a favourable point merely labelled as
  the nominee. Verified by parsing the entrypoint, never by importing it — team code is untrusted
  and is never executed during verification.

The four rules above police the **declaration**, from numbers written down before anything runs.
They are necessary and not sufficient, so one rule polices the **effect**, decided from measurement
after the points have run — the only moment it is knowable:

- **no point may reproduce the nominee's scored metric vector exactly.** A coordinate the strategy
  consumes through a quantiser — `round(n × fraction)` over a twenty-name universe is the case a
  team found and reported rather than used — can satisfy the 5% materiality rule and still produce
  a byte-identical book, because both variations land inside the same quantisation cell. Such an
  axis is worse than uninformative: an inert point sits exactly on the nominee, dragging the
  per-metric median toward the nominee's own value, which is precisely the peak this section exists
  to discount. Three inert coordinates would convert the anti-peak-picking rule into a rubber stamp
  for the peak. A sweep containing an inert point is void; the team re-declares and sweeps again,
  at the cost of another trial, and keeps the diagnostic naming which points were inert.

**Every scored metric is the per-metric median across the neighbourhood's runs.** The nominated
point's own coherent metric vector, and the coherent vector of the median-performing point, are
both reported as diagnostics but neither is the score. The trial-adjusted confidence's bootstrap
term `B` takes the same per-metric median across the points, because it is a property of a run's
own return stream exactly like the metrics beside it; a non-finite value at any point medians to
non-finite, which fails the floor rather than being sorted around.

**The sweep is run by the organiser's own runner** (`scripts/cup20_evaluate.py --neighbourhood`),
against an accepted trial of kind `neighbourhood`, and never by a team's own script. Each point is
materialised as a real file — the frozen entrypoint with exactly the declared coordinate literals
rewritten by byte span, located through the same single AST traversal the coordinate rule above is
verified by — and each is then evaluated in its own freshly spawned interpreter, so no point can
leave process state behind for the next. Three checks stand between a declared point and a scored
one, and each refuses rather than warns: the two files must be byte-identical once their coordinate
literals are blanked out; the variant's parsed constant table must equal the frozen source's at
every non-coordinate name; and the imported module must be observed to have BOUND the point's value
before the run begins. The nominee is not rewritten at all — its directory is copied verbatim and
required to hash to the frozen candidate's — so the nominated point provably runs the frozen bytes.

A declaration that fails any rule in this section is refused **at the journal append**, so a
neighbourhood that could not be swept costs no trial. §7.1 spends a trial at acceptance and never
refunds one, so the append is the only place it can cost nothing.

Rationale: nominating a best point is nominating the maximum of a noisy surface, which is
upward-biased by construction. A median over a pre-declared plateau is not. This is also applied on
the holdout (§8), so the final ranking is a plateau estimate rather than a spike.

### 7.3 Floors

Evaluated on the neighbourhood-median record, common risk unit. Never waived, never lowered, never
rounded into compliance, never averaged away. A missing or non-finite value fails its floor.

**Amendment A4 changed what a failure costs.** Every floor below was conjunctive and hard, so one
miss out of twenty-two discarded a candidate entirely — which is how a book positive in all four
folds, positive on both sleeves and inside every risk limit came to be ranked nowhere at all. The
floors are all still measured and still reported; what they no longer do is veto. In-sample
advancement is decided by the ranking score of §7.4 over every **admissible** candidate.

Two of the checks are exempt from A4 and still disqualify outright, because they are not claims
about how good a book is but about whether its evidence means what the certificate says:

| Integrity check | Why no score can repair it |
|---|---|
| `sign_inversion_not_profitable` | the falsifier reproduces the book, so the result is an artifact of the harness rather than of the stated mechanism — there is nothing here to rank |
| `declared_roles_match_traded_sides` | the certificate claims a sleeve the book never traded, or hides one it did |

An integrity check that was never *measured* is not passed. A sweep cannot decide sign inversion —
that is its own material trial — so a candidate carrying no falsification result is inadmissible
until one exists. The blindness scan, the source scan, the §5.1 coordinate rule, the A1 inertness
rule and the A3 volatility-target ban are hard for the same reason and are unaffected by A4.

**§7.6's holdout stage does not follow A4.** There the floors remain conjunctive and hard. That
stage asks whether a book is good enough to put on a paper desk, not which book is best, and §1.1
keeps "no winner" as a permitted answer.

**Integrity gates** (evaluated before any performance number):

- all authorities present and hash-bound; deterministic under exact replay; journaled before
  disclosure;
- only the frozen IS snapshot, exact point-in-time membership, and pure-crypto-passing contracts
  used;
- causality: future-corruption test passes;
- execution contract applied by the frozen evaluator;
- solvency and completeness: the full scored window completes.

**Cost levels are stated, never inferred.** Every performance floor below names the cost
multiplier it is evaluated at, and none is left unqualified. Where a floor names no multiplier —
and after this amendment none does — the rule is **base (1×) cost**, because 1× is the actual cost
model the tournament trades under, and because the charter already carries dedicated 2× and 3×
Sharpe floors, which is where cost resilience is stressed. `maxDD ≤ 0.20` asks whether the real
book would have been survivable, which is a question about the real book.

§7.4's ranking inputs are read at **2×** instead. Three metrics — maximum drawdown,
positive-quarter fraction and annualised turnover — are consumed by both, so they are computed
**twice, at two different cost levels**, and both values are carried through scoring. That
duplication is deliberate and is not an inconsistency: the floors gate the realistic book, the
ranking rewards the book that survives a cost shock. This rule governs every floor in this
charter, including the holdout eligibility floors of §8, which carry their own cost-level column
for the same reason this section does: so that no gate anywhere is decided by inference.

**Performance floors:**

| Metric | Cost level | Floor |
|---|---|---:|
| Net Sharpe | 1× | ≥ 0.80 |
| Net Sharpe | 2× | ≥ 0.50 |
| Net Sharpe | 3× | > 0 |
| Annualised return | 1× | > 0 |
| Annualised return | 2× | > 0 |
| Maximum drawdown | 1× | ≤ 0.20 |
| Realised annualised volatility | 1× | ≥ 0.06 |
| Positive-quarter fraction | 1× | ≥ 0.50 |
| Folds positive | 2× | ≥ 3 of 4 |
| Worst-fold Sharpe | 2× | ≥ −0.25 |
| Long gross PnL, short gross PnL | 1× | each > 0, for every side the book actually traded |
| Declared roles agree with the sides actually traded | 1× (roles read off the 1× gross PnL) | **required** |
| Annualised one-way turnover | 1× | ≤ 25× equity |
| Gross edge per unit one-way turnover | 1× | ≥ 40 bps |
| Cost share of positive gross PnL | 1× | ≤ 30% |
| Five largest absolute daily returns | 1× | ≤ 35% of total absolute daily return |
| Any single fold's share of positive PnL | 1× | ≤ 60% |
| Executed trades over IS | 1× | ≥ 500 |
| Neighbourhood points with positive return **and** positive 2× Sharpe | 1× return, 2× Sharpe | ≥ 70% |
| Trial-adjusted confidence | cost-free (bootstrapped on 1× daily returns; see below) | ≥ 0.90 |
| Exact sign inversion clears the core floors | each core floor at its own level | **disqualifying** |

**Roles are observed, not declared.** A candidate's roles are derived from which sides its book
**materially** traded — a side whose gross PnL is more than 1e-6 of the book's total gross activity
— and the roles declared in the research certificate are checked against that. Both floors then
apply to the union. Otherwise a long/short book with a losing short sleeve could declare itself
long-only and the short-PnL floor would never be evaluated, which is opting out of a hard floor by
describing yourself differently. Declaring a sleeve that was never traded fails the same check, in
the other direction.

The materiality threshold is relative, not absolute, and it is deliberately far from both mistakes
it could make. Nothing upstream filters dust, so a long-only book that emits one 1e-9 weight at a
single boundary does carry a nanoscale short with a sign-random PnL; without a threshold it would
be disqualified twice over on a rounding artifact. 1e-6 sits four orders of magnitude above the
largest magnitude such dust can reach (floating-point accumulation error across the window, and the
evaluator's own 1e-12 weight tolerance, both land near 1e-10 relative) and four orders below the
smallest sleeve that could move any reported number at the two-decimal precision every ratio floor
is stated in — so there is no real sleeve small enough to hide behind it and nothing to gain by
trying. A non-finite side is always material and is gated, never dismissed as dust.

**Folds.** Four equal 12-month blocks anchored backward from the IS cutoff, so every fold carries
the same noise floor:

| Fold | Interval | Regime character |
|---|---|---|
| F1 | `[IS_START, 2021-08-01)` | 2020 recovery, 2021 bull, May-2021 crash |
| F2 | `[2021-08-01, 2022-08-01)` | second peak, bear onset, LUNA |
| F3 | `[2022-08-01, 2023-08-01)` | FTX, bear trough, early recovery |
| F4 | `[2023-08-01, 2024-08-01)` | 2024 bull |

If `IS_START` exceeds 2020-08-01, F1 absorbs the shortfall and its shorter length is disclosed.

**Trial-adjusted confidence.** **Base-cost (1×)** daily returns, 2000-sample circular block
bootstrap, fixed 10-day blocks. It is computed **once** and is never recomputed per cost level:
the same single value is the §7.3 floor input and the §7.4 ranking term. With `B` the fraction of
bootstrap arithmetic means above zero and `T` the team's complete accepted-trial count at
nomination:

```
confidence = max(0, min(1, 1 - T * (1 - B)))
```

Both the unadjusted `B` and `T` are always disclosed.

**Falsification battery.** The exact sign inversion of the **nominated point** (not the
neighbourhood) is run; if it clears the core performance floors, the candidate is **disqualified** —
the apparent edge is a construction artifact rather than a mechanism. Separately, a shuffled-signal
placebo is scored on **gross** edge, never on net: a net-of-cost placebo null is structurally broken
because any costed random book centres at −cost rather than at zero.

**The core performance floors** are the eight above that are properties of a single run's own
return stream, and therefore mean the same thing for an inverted book as for the book it inverts:
net Sharpe at 1×, 2× and 3×, annualised return at 1× and 2×, maximum drawdown, realised
annualised volatility, and executed trades. Named explicitly because "core" was previously
undefined and the verdict it decides is disqualifying. The remaining floors are excluded, each for
its own reason: the two research-process terms (neighbourhood positivity, trial-adjusted
confidence) are not properties of the run at all; the sign-inversion row itself is the verdict
being computed; the role rows invert by construction, so a long-only candidate's inversion is
short-only and would fail them for a reason that says nothing about artifacts; and the shape rows
(turnover, gross edge per turnover, cost share, five-largest-day share, fold PnL concentration,
fold and quarter positivity) are close to sign-symmetric, so including them would let a candidate
be disqualified because its inversion had the same turnover. The choice is not delicate: an exactly
inverted book carries the negative of the original's gross return, so `annualised return > 0` alone
fails almost every inversion, and what survives the eight is a book whose apparent edge came from
cost, funding or cap asymmetry rather than from direction.

**Both halves are run by the organiser's harness, not self-reported.** The inversion is
mechanically exact — every emitted weight negated, `None` (hold) and `{}` (flat) untouched, since
neither carries a direction — and the placebo preserves the candidate's weight multiset and
rebalance schedule exactly while randomising which eligible symbol receives which weight. A team
implementing either privately could get it wrong in ways nobody can audit, and could skip a
mandatory falsifier by accident; a disqualifying verdict cannot rest on a self-report.

**Metric definitions.** `calmar_2x` = annualised 2×-cost return ÷ the **2×-cost** maximum drawdown
magnitude. `worst_fold_sharpe_2x` / `median_fold_sharpe_2x` = the minimum and median of the four
fold Sharpes at 2× cost; `positive_fold_count` counts the same four 2×-cost fold Sharpes that are
strictly greater than zero. The fold PnL-concentration floor is the maximum, over the four folds,
of each fold's share of **base-cost** positive PnL. `gross edge per unit one-way turnover` = gross
arithmetic PnL ÷ total one-way turnover, expressed in basis points. A trade is one non-zero
executed symbol/boundary fill after evaluator netting; funding alone is not a trade and order
fragmentation cannot inflate the count. Maximum drawdown is a non-negative magnitude. A regime or
fold is positive only when its Sharpe is strictly greater than zero. Zero is not positive.

### 7.4 Ranking score G

Only floor-passers are ranked. All inputs are neighbourhood medians on the common risk unit, and
every metric input is read **at 2× cost** — including `max_drawdown_2x`,
`positive_quarter_fraction_2x` and the turnover tie-break, each of which §7.3 floors at 1×. Those
three are therefore computed twice, at two levels, and the two values are not interchangeable. The
single exception is `trial_adjusted_confidence`, which is cost-free: it is the one value §7.3
defines, not recomputed at 2×. `C(x) = min(1, max(0, x))`.

```
G = 30 * C((worst_fold_sharpe_2x + 0.25) / 1.00)
  + 20 * C((median_fold_sharpe_2x - 0.25) / 0.75)
  + 20 * C((0.20 - max_drawdown_2x) / 0.15)
  + 15 * C(calmar_2x / 1.50)
  +  8 * C((positive_quarter_fraction_2x - 0.50) / 0.375)
  +  7 * C((trial_adjusted_confidence - 0.90) / 0.10)
```

`G` ranges 0–100: **58 points of generalisation, 35 points of drawdown control, 7 of multiplicity
honesty.** It is a ranking score, not an additional veto.

Ties break by: lower 2×-cost maximum drawdown, then higher worst-fold 2× Sharpe, then lower
2×-cost annualised turnover, then lexicographically smaller team id.

**The top three advance.** If fewer than three clear the floors, only the actual qualifiers
advance. Floors are never lowered and no empty slot is backfilled after holdout access.

### 7.5 Freeze

Each team nominates exactly one archive-backed identity: source bytes, dependency lock, config,
risk policy, parameters, seed and declared neighbourhood, all bound by hash. After nomination there
is no repair, withdrawal, substitution or next-ranked replacement. The organiser closes IS at one
journal head and atomically freezes the complete ranked population and the advancing identities
before any holdout access.

An **equal-risk reporting ensemble** across the three finalists is frozen at the same boundary:
capped inverse-IS-volatility weights, full precision, cap algorithm, constituents and
missing-result behaviour all fixed before holdout access. A failed constituent's weight becomes
cash and is never redistributed.

## 8. Holdout championship

Each finalist receives **exactly one observation**, which is a full neighbourhood sweep (7+ runs)
scored by per-metric median exactly as in §7.2. Runs may be serial, but no team-specific result,
progress, error, timing or completion order is disclosed until every observation is terminal.
Interruption after the journaled start marker is a DNF and consumes the observation. There is no
retry, repair, replacement or backfill.

**Winner eligibility** (all must hold, neighbourhood median, common risk unit). §7.3's ruling that
cost levels are stated and never inferred governs here too, so every row names its multiplier and
an otherwise-unqualified **floor** is **base (1×) cost**:

| Condition | Cost level |
|---|---|
| annualised return > 0 | **1×** |
| annualised return > 0 | **2×** |
| Sharpe > 0 | **2×** |
| maximum drawdown ≤ 0.25 | **1×** |
| at least 5 of 8 quarters positive | **1×** |
| the nominated point itself has positive return | **2×** |

The last row guards against a nominee that is an outlier within its own plateau, and is the one
input here that is a single point rather than a neighbourhood median.

The two rows that were previously unqualified — maximum drawdown and the positive-quarter count —
are base cost for the same reason §7.3 gives: they ask whether the **real** book survived the
sealed window, which is a question about the real book, and §8 already stresses cost resilience
separately through its 2× return and 2× Sharpe rows. The quarter condition is a **count**, not the
ratio §7.3 floors, and is read as such: 5 of 8 is 0.625, so a book with exactly four positive
quarters clears §7.3's 0.50 fraction and still fails here.

**Winner** = the eligible candidate with the highest `G` recomputed on holdout metrics, with the
drawdown term rebased to the 0.25 floor (`20 * C((0.25 - maxDD) / 0.20)`) and the fold terms
computed over four 6-month holdout blocks. Same tie-breaks. **If nobody is eligible, CUP-20 has no
winner and no paper desk opens.**

All individual packets, the ensemble packet and the manifest are built and hash-verified privately.
One release authorisation binds the complete bundle before an atomic public rename. There is no
partial publication.

**Noise disclosure.** The standard error of a Sharpe estimate over two years is roughly ±0.7. The
final report states this explicitly and does not present sub-noise gaps between finalists as
meaningful separation.

## 9. The twelve lanes

Assigned, not chosen. In crypto-cup-01, seven of ten teams independently converged on residual
momentum; assignment is the fix. Shared causal transforms and shared risk controls are not a
collision — copying another team's alpha is.

| # | Mandate |
|---|---|
| 01 | Slow per-coin time-series momentum |
| 02 | Breakout / channel-position |
| 03 | Trend-quality-gated momentum (persistence, efficiency ratio, trend strength) |
| 04 | Market-residual cross-sectional momentum |
| 05 | Short-horizon liquidity-shock reversal |
| 06 | Downside-risk / low-volatility selection |
| 07 | Funding carry with crowding-crash protection |
| 08 | Funding and basis term-dynamics reversion |
| 09 | Taker-flow / price-volume pressure |
| 10 | Volatility-regime risk-on / risk-off timing |
| 11 | Calendar and settlement-clock seasonality |
| 12 | Preregistered multi-sleeve ensemble (≥3 orthogonal causal bases, a-priori weights) |

A team may make **one** documented mechanism pivot, and only after its original thesis is falsified
across the full research matrix. A negative candidate is evidence, not a submission.

Machine learning is permitted in any lane and mandated in none. It faces the identical turnover,
cost-density, neighbourhood and trial-adjustment discipline. All agents run on Opus 5.

### 9.1 Research certificate

Required before nomination:

- a transparent baseline and the exact sign inversion;
- at least three formation horizons and two rebalance/holding horizons, with the rebalance **phase
  offset swept** for any cadence longer than one bar (phase is a first-order axis, not a detail);
- controls-off, individual-control and combined-control ablations;
- long, short and chop role checks;
- the declared parameter neighbourhood and its sweep;
- every success, failure, pivot and abandoned attempt, with its journal sequence number.

## 10. Forward paper desk

The winner is frozen byte-identical and runs for **six months** from the freeze date. No parameter,
universe, signal, risk or execution change is permitted during the declared observation; any change
starts a new research lineage with no inherited evidence.

**Parity by construction, not by reimplementation.** The live tick calls the same evaluator entry
point on a growing panel, so the forward book is bit-identical to what a backtest over the same rows
would produce. A parity assertion compares forward weights, returns at 1× and 2× cost, turnover and
funding against a direct backtest and aborts on mismatch. Append-invariance is asserted on every
tick: if history revises, the tick aborts rather than silently re-writing the record. Funding is
taken from production rates, never from a testnet feed.

Forward gates are pre-registered before the desk opens. The frozen ensemble may run alongside.

## 11. Implementation surface

```
TOURNAMENT-CHARTER-CUP20.md          charter (meaning; authoritative on intent)
tournament/cup20/
  config.toml                        machine contract (numbers; authoritative on policy)
  activation-freeze.json             binds charter+config+impl+lock+data+audit+tests
  INTEGRITY-REVIEW.md                the post-tournament procedure, run before anyone advances
  quarantine-receipt.json            where the holdout went, and what it must hash to on return
  quarantine-restore.json            written on restore; its absence means custody still holds
  sealed-access-baseline.json        armed access times for the phase-3 tripwire
  research-journal.jsonl             append-only, hash-chained
  nomination-registry.json
  selection-freeze.json
  teams/team-NN/{MANDATE.md, candidates/<id>/{strategy.py,risk_policy.json,README.md},
                 research/, RESEARCH-CERTIFICATE.md}
  certificates/
  universe-summary.json              team-visible; in-sample facts only
  private/                           ORGANISER-ONLY, gitignored, prohibited to teams
    holdout/                         holdout outputs, pre-release
    universe-summary.json            full-window figures, incl. sealed-side composition
    pure-crypto-audit.json           the universe attestation the activation record binds
reports-cup20/{is/, holdout/, source-archives/sha256/}   ORGANISER-ONLY, gitignored
data/cup20/{is/, sealed/, acquisition/}                  distinct manifests; only is/ is a team input
src/crypto_trade/cup20/
  config.py universe.py snapshot.py engine.py risk_unit.py journal.py quarantine.py
  qualification.py scoring.py scored_metrics.py adjudication.py runner.py report.py paper.py
  trials.py                          the material tuple, the budget, the organiser-owned append
  harness.py                         the ONE scorer teams run; also the falsification battery
  variants.py                        materialise one neighbourhood point out of the frozen source
  sweep.py                           the declared neighbourhood sweep and its per-metric median
scripts/cup20_trial.py               TEAM-FACING: record a material trial before evaluating
scripts/cup20_evaluate.py            TEAM-FACING: evaluate one point, the declared neighbourhood
                                     (--neighbourhood), or the falsification battery
scripts/cup20_readiness.py           reference strategy end to end, before any team is dispatched
scripts/cup20_quarantine.py          quarantine / restore / verify, from the command line
scripts/cup20_integrity_review.py    runs every check in INTEGRITY-REVIEW.md and prints a verdict
tests/cup20/
```

**Reuse.** `crypto_trade.tournament.protocol` (DecisionContext / TargetStrategy) and the
pure-crypto audit module are reused directly. The proven execution core is reused for fills,
funding, delisting and risk-policy application; CUP-20 adds the top-20 universe, the common risk
unit, and its own qualification, scoring and journal layers.

**Validation before any team starts.** A differential test asserts that the CUP-20 evaluator and the
existing proven evaluator agree on a reference strategy over the same rows; the full leak battery
(future corruption, embargo, membership point-in-time, funding attribution, delist force-exit)
passes; the activation record hash-binds charter, config, implementation, dependency lock, data
authority, pure-crypto audit and the test output. Activation fails on any disagreement between
charter and config.

## 12. Phases

| Phase | Content | Gate to exit |
|---|---|---|
| 0 | Charter, config, dual snapshot, universe, evaluator + risk unit, journal, qualification, scoring, tests | activation freeze recorded |
| 0b | **Quarantine**: sealed + acquisition snapshots moved out of the working tree, canary planted, event journalled | receipt committed; `verify_quarantine_integrity` passes (absence **and** the recorded digests, not absence alone), and is re-run periodically through phase 1 |
| 1 | 12 teams research IS in parallel (QR + QE per team), ≥8 trials, certificate, nominate | nomination registry closed at one journal head |
| 2 | Mechanical qualification, falsification DQs, `G` ranking | selection freeze: top-3 + ensemble weights |
| 2b | **Restore**: quarantined trees verified against the activation-bound digests and moved back; access tripwire armed | digests match; restore stamp written |
| 3 | Holdout observations, private build, hash-verified bundle | single release authorisation |
| 4 | Integrity review, comparative Critic review, final report, ensemble report | `INTEGRITY-REVIEW.md` passes; leaderboard published |
| 5 | Six-month paper desk for the winner | forward gates pre-registered, parity asserted |

Quarantine happens **before the first team starts**, and restore happens **only after the selection
freeze exists**. Neither ordering is advisory: `quarantine_holdout` refuses to run twice and
`restore_holdout` refuses to run at all until the selection freeze is on disk.

## 13. Authority and amendments

The config controls numerical policy; the charter controls meaning; activation fails on
disagreement. Every stage transition, counter, hash, gate vector, score and advancement decision is
append-only, reproducible from frozen authorities, and attributable to an organiser event. Changes
after activation require a prospective, append-only amendment recorded **before** the affected data
are accessed. Historical evidence is never rewritten. Silence, missing output and DNF never count
as a valid submission.

### Amendment A1 — 2026-08-08, prospective: the effect half of the §7.2 neighbourhood rule

**Recorded before any team affected by it accessed the tournament data.** Teams 05-12 had not
started; teams 01-04 had finished.

Team 04 reported, and declined to use, a gap in §7.2: the materiality rule polices the *declared*
variation but nothing policed whether that variation moved the *book*. A coordinate the strategy
consumes through a quantiser can vary by the required 5% and produce a byte-identical result, and
because an inert point lands exactly on the nominee it pulls the median onto the peak — scoring
*better* than an honest declaration. The team measured the alternative it passed up as worth about
0.006 of bootstrap fraction against the axes it did declare, and disclosed it instead.

§7.2 now adds: no point may reproduce the nominee's scored metric vector exactly; a sweep
containing one is void.

**Retroactive effect: none, verified rather than assumed.** The three completed sweeps were checked
against the new rule before it was written. Team 04's sweep measured zero inert points directly;
teams 01 and 02 declared only integer bar counts and a threshold, every variation clearing its
quantisation step by a wide margin. No completed result changes.

The amendment can only make nomination harder and cannot advantage any team, which is the sole
class of change this section permits once teams are running.

### Amendment A2 — 2026-08-08, prospective: two structural floor interactions disclosed, no rule changed

Team 04 reported that two floors interact with this window and this universe in ways the charter had
not stated. Both are recorded as §14.9 and §14.10 and **neither floor is changed**. Both candidate
changes would have *loosened* a floor, and teams 01-04 designed against the strict form; loosening
after they froze would advantage the teams that had not yet started. Disclosure is the fair
instrument here, a rule change is not.

### Amendment A3 — 2026-08-08, prospective: a declared volatility target is forbidden (§6)

`volatility_target.enabled` must be `false`. A candidate declaring `true` is refused by the free
`--check`, before it can cost a trial.

The field was admitted on the reasoning that it was largely inert, since a declared target may only
reduce and the common risk unit has already pulled the executed book toward 10% annualised. That
reasoning was wrong in the direction that matters. The policy measures the volatility of the book it
has **already scaled**, so the loop settles with realised gross and turnover at a fractional power of
the declared target rather than pinned to it. A team short of the turnover floor can therefore clear
it by declaring a smaller number instead of by trading less — a floor passed by paperwork. Refusing
the field is the only remedy that does not require the organiser to judge intent, and it is what §6's
division of shape from scale already implied.

**Retroactive effect: one nomination touched, and handled at organiser cost rather than the team's.**
Teams 02, 03 and 04 declared `enabled: false` throughout. Team 01's nominated candidate declares
`enabled: true` at `annualized_target: 0.10` — the same figure as the organiser's own risk unit, with
`maximum_scale: 1.0` so it can only reduce — and its certificate records that the team identified the
lower-target exploit explicitly and **declined to use it**, fixing its turnover overrun by slowing
its ladder instead. Because the rule changed under a team that had already frozen, the tournament
pays for the re-score rather than the team: the frozen nominee is swept again with the target
disabled, at the accepted-trial count the team actually spent, and the result recorded here stands as
its score under this amendment. Nothing is charged to team 01's budget and no trial is consumed.

### Amendment A4 — 2026-08-08: in-sample advancement is ranked, not gated

**Organiser ruling, on the tournament's own objective.** The twenty-two floors of §7.3 were
conjunctive: miss one, and the candidate left the field regardless of everything else. Measured
against real submissions that proved too blunt. Team 04's residual cross-section was positive in all
four folds (worst +0.195), positive on both sleeves, inside every risk and cost limit, and cleared
twenty-one of twenty-two floors — and scored nothing, because trial-adjusted confidence landed at
0.839 against a 0.90 floor that on this window demands a plateau-median Sharpe near 1.13.

Under A4 every floor is still measured, still reported and still recorded verbatim; a miss costs
points rather than the tournament. In-sample advancement is the §7.4 ranking score over every
admissible candidate, and the top three by that score advance. The ranking formula is **unchanged**
— the same 58 points of fold consistency, 35 of drawdown control and 7 of multiplicity honesty,
fixed before any team ran. Nothing in it was re-weighted after results were visible, which is the
one thing that would have made this ruling a way of choosing a winner rather than a way of ranking
one. The confidence term in particular was already graded rather than a cliff.

Exempt, and still disqualifying: `sign_inversion_not_profitable` and
`declared_roles_match_traded_sides` (§7.3), plus the blindness scan, the source scan, the §5.1
coordinate rule, the A1 inertness rule and the A3 volatility-target ban. Those say the evidence is
not what it claims, and no ranking repairs a false claim.

**Not applied to the holdout.** §7.6 keeps conjunctive floors, because that stage asks whether a
book is deployable rather than which book is best, and §1.1 keeps "no winner" available.

**Known consequence, stated rather than discovered later.** The ranking score measures fold
consistency, drawdown, Calmar, positive quarters and multiplicity honesty. It does **not** measure
turnover, cost efficiency, realised volatility or trade count. Those were previously enforced only
as floors, so under A4 a book that churns with thin edge per unit of turnover can rank on in-sample
evidence where it would once have been removed. The floors remain on the record for every candidate,
and the holdout stage still enforces them conjunctively, so such a book cannot win — but it can
occupy one of the three holdout slots.

### Amendment A6 — 2026-08-11: the multiplicity charge counts only chances to pick a winner

`T` in `1 − T·(1−B)` now counts accepted trials of kind `point` and `neighbourhood` only.
`falsification` and a new kind, `ablation`, are exempt. The **budget** is unchanged: twelve trials,
every one of them charged against it whatever its kind.

**Why, measured rather than argued.** §14.10 disclosed that the correction penalised falsification
and ablation exactly as it penalised a parameter search, and predicted teams would find that
backwards. Seven teams in, the effect is on the record: **four of the first seven stopped at the
eight-trial minimum with a third of their budget unspent**, and two more stopped at nine. Further
research made a candidate score worse, so teams stopped researching. That is the opposite of what
this tournament is for, and disclosure alone did not fix it.

A falsification battery is run by the organiser on a nominee, cannot be steered, and is not a chance
to pick anything. An `ablation` is declared a **control before it runs**, and the exemption has a
price: **declaring a candidate an ablation forfeits its eligibility to be nominated.** A team may
explore without charge, but what it explored under that flag cannot become its answer — otherwise
the flag would be a free relabelling of any search, promoted only when it happened to work. Kind is
journaled before the run, so a disappointing search cannot be reclassified afterwards. The refusal
fires in the free pre-flight, before any market data is read.

**Retroactive effect: every completed team gains slightly, none loses, and the order is unchanged.**
Recomputed at the A6 count, confidence rises by between +0.002 and +0.067 across teams 01–07 — most
where a team had run two falsification batteries, which is the case the old rule punished hardest.
The ranking order is identical before and after. Teams 08–12 face the amended rule from the start
and every earlier team's score has been recomputed under it, so the field is scored on one basis.

### Amendment A7 — 2026-08-14, prospective: the holdout ranks rather than gates

**Organiser ruling, and the third in the same direction.** §7.6 and §8 gated the holdout
conjunctively: a finalist missing any one of §8's six winner-eligibility conditions was eliminated,
and §1.1's "no winner" followed if all three missed. A4 had already replaced that logic in-sample.
A7 extends it: §8's conditions are still evaluated, still reported and still travel with every
verdict — a miss now costs points instead of the tournament, and **the highest holdout score wins.**

**Recorded before the sealed window was restored.** No holdout number existed when this was ruled;
the finalists were known, their holdout results were not. That is exactly the condition §13 imposes
on an amendment, and it is the only thing that makes this one admissible rather than a rule written
around a result.

**Three of §8's six conditions the ranking score already prices** — `max_drawdown` directly at 20
points (rebased to the §8 ceiling), `positive_quarter_count` through `positive_quarter_fraction` at
8, and a negative `annualized_return` through Calmar at 15, which A5's decaying tail carries below
zero. **The other four have no term in `G`**: `annualized_return`, `double_cost_annualized_return`,
`double_cost_sharpe` and the nominated point's own 2×-cost return. Left unpriced they would cost
nothing at all, which is precisely the defect A5 was written to close at the other stage. They are
therefore priced by a multiplicative, equal-weighted `holdout_compliance_factor` over those four —
binary, because §8 states no magnitude for any of them and inventing one now, with the three
finalists known, is the discretion this charter exists to remove.

**Integrity is not re-tested at the holdout and does not need to be.** The observation is a
neighbourhood sweep and runs no falsification battery, so there is no integrity verdict to take
there; it was established in-sample, where every finalist passed.

**Stated plainly: this can crown a book that breached a risk floor out of sample.** The organiser
recommended keeping the holdout conjunctive for exactly that reason and was overruled. The
consequence is disclosed here rather than discovered later, and the winner's full §8 condition
vector is published alongside its score, so what was crowned is legible.

## 14. Known limitations, stated up front

1. The holdout window overlaps four prior organiser-level reveals (§2.1). Mitigated structurally,
   not eliminated. The forward paper record, not the holdout, is what could later authorise capital.
2. Two years of holdout gives a Sharpe standard error of roughly ±0.7. The tournament can identify
   a survivor; it cannot finely rank three survivors.
3. `IS_START` near 2020-08 means the COVID-2020 crash falls outside the scored IS window. IS still
   contains May-2021, LUNA, FTX and the full 2022 bear as stress episodes. The alternative — an
   earlier start with a one-to-six-name universe — would have made the early folds meaningless.
4. A 20-name universe has materially less cross-sectional dispersion than 40. Cross-sectional lanes
   must work in thirds rather than quintiles; this is a real handicap for lanes 04, 05 and 06 and is
   accepted deliberately in exchange for universe stability and liquidity.
5. The common risk unit makes drawdowns comparable but means the reported book is not the book a
   team would deploy at its own chosen risk level. Both normalised and raw are reported.
6. Because the common risk unit resizes the book the declared risk policy then governs (§6), a
   team's declared *sizes* — the drawdown level at which its brake engages — do not survive intact
   into the executed book. Its declared *shape* does. This is a deliberate consequence of levelling
   risk before comparing drawdowns, and it is disclosed rather than mitigated: a strategy whose edge
   depends on running at its own chosen scale is not one this tournament can rank. The volatility
   target used to be the other example here; amendment A3 forbids it outright, because the
   interaction was not merely a distortion of a declared size but a way to move turnover without
   trading differently.
7. A concentrated book is evaluated, but it is not evaluated on equal terms, and the reason is
   arithmetic rather than a judgement about concentration. The §4 caps reduce and never
   redistribute, so a four-name equal-weight book executes at 0.80 gross and a single-name book at
   0.20. The common risk unit can lever back up to `s_t = 3.0` and no further, so a concentrated
   book has correspondingly less room to reach the 10% annualised target before the gross cap stops
   it, and a very concentrated one may fail the 0.06 realised-volatility floor (§7.3) on size alone
   while a diversified book with the same per-name conviction clears it. The alternatives were
   worse: rejecting such a book forbids a whole shape of strategy, and redistributing the trimmed
   weight rewrites the strategy and hands teams a way to reach shapes they could not request.
   Disclosed rather than mitigated — the `exposure_caps` block (§6) says exactly how far each
   candidate was reduced, so a floor failure driven by trimming is visible as such and not
   mistaken for a weak signal.
8. Blindness is enforced by the operating system only during quarantine (§5, layer 0). Phase 3
   needs the sealed data readable, and every agent runs as one account, so during that window the
   controls are detection rather than prevention. The residual, precisely: a phase-3 process that
   reads one sealed parquet file directly, keeps nothing, and writes down only a conclusion leaves
   no canary token, and its `atime` evidence is destroyed by anything that resets access times. No
   control in this tournament closes that. What the record can show is narrower and is what §5
   claims: that custody held for the whole research phase, that no workspace or archive carries
   evidence of a read, and that the sealed bytes are the ones activation bound.

   Two controls would close it, and neither is available here. Running each team agent under its
   own operating-system account, with the sealed tree owned by the organiser at mode `0700`, would
   make phase-3 blindness a kernel guarantee rather than a detection problem; it requires the agent
   harness to launch processes as different users, which this repository does not control. A
   kernel read audit (`auditd -w data/cup20/sealed -p r`, or an equivalent `fanotify`/eBPF watch)
   would name the process and the moment of every read rather than inferring one from a timestamp;
   it requires root. An organiser who can arrange either should, and should say so in the record —
   both supersede the tripwires in §5 rather than supplementing them.

9. **The both-sides-gross-positive floor (§7.3) is a standalone-viability test, and on a rising
   window that is a strong requirement, not a neutral one.** A dollar-neutral book's short sleeve is
   gross-positive only if the shorted names fall in *absolute* terms — much stronger than "short the
   relative losers", which is the only thing a cross-sectional book claims to do. Measured on the
   in-sample window, an equal-weight top-20 basket sums to **+1.99** in simple returns over 4335
   bars, so the floor pushes cross-sectional lanes toward a *concentrated* short sleeve: team 04
   measured 48 diversified sleeves, every one gross-negative (best −0.22), and reached positive only
   by narrowing to a fifth of the names. The floor is kept as written — it is the one test that
   separates a market-neutral book from a long book wearing a hedge, and loosening a floor after
   teams have designed against it would advantage the teams that had not yet started. It is stated
   here so lanes 04, 05 and 06 design for it rather than discover it at their eighth trial. The
   interaction is sharper at 20 names than it would be at 40, where a deeper loser tail is reachable
   without concentrating.

10. **The multiplicity adjustment counts every trial, including the ones spent trying to falsify
    your own result.** `1 − T·(1−B)` against a 0.90 floor means a team at the 8-trial minimum needs
    a bootstrap fraction of 0.9875, and one that uses all twelve needs 0.9917. That penalises
    ablations and falsification batteries exactly as it penalises a parameter search, which is
    backwards with respect to what this charter asks for everywhere else. It is kept because the
    alternative — organiser judgement about which trials "count" — is the discretion §2.1 exists to
    remove, and because a team can always choose to run fewer. Teams should budget for it: on this
    window an all-folds-positive book at the minimum trial count still failed this floor, on
    B = 0.977, which is why it is written down here.

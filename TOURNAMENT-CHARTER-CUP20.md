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
   contract, passes the fail-closed pure-crypto policy, is not delisted at the boundary, and has a
   **complete 180-day trailing history**. The completeness requirement doubles as the minimum
   listing age and is the single rule that removes launch-hype listings.
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
Across the IS window's 207 reconstitutions the adopted rule delivers **0.29 changes per week, 159
of 206 transitions completely unchanged, and 63 distinct names**, with exactly 20 members at every
boundary. That confirms the design-time estimate's direction and magnitude while being measured on
the real thing rather than a proxy. The organiser's full-window figures exist and are recorded in
`tournament/cup20/private/universe-summary.json`, which is not team-visible.

The ranking statistic is the **median** daily quote volume over the trailing window, not the mean.
A coin's launch-week volume spike lifts a 180-day mean far more than a 180-day median, so ranking
on the mean admits transient listings into a universe meant to be blue-chip. Re-measured on the
built data over the same IS window, the mean gave 67 distinct names at 0.31 changes per week
against the median's 63 at 0.29: it admitted COMP, ENS, LINA, MANA, OMG, TOMO and WAVES, and passed
over BAND, NEO and SEI. The choice was fixed before any holdout number existed and is not
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
  Applied after the common risk unit.
- **Solvency:** equity must remain finite and strictly positive; a breach is terminal for the run.

## 5. Blindness — four independent layers

1. **Truncated data root.** Teams receive `data/cup20/is/`, containing bars, funding, membership,
   contract metadata and exchange info **strictly before 2024-08-01**. Not one row at or after the
   cutoff is in it, in any timestamp column of any dataset, and the contract metadata is censored so
   that a symbol delisting after the cutoff is indistinguishable from one still trading. Holdout
   rows live in `data/cup20/sealed/` under a different manifest hash.

   What this layer does **not** claim: the holdout rows are not physically absent from the machine.
   As deployed, `data/cup20/sealed/` sits on the same filesystem, under the same account, with the
   same permissions as the in-sample snapshot, and so do the acquisition snapshot and the
   organiser-only artifacts under `tournament/cup20/private/`. Nothing at the operating-system level
   stops a team process from opening any of them. What is true is narrower and worth stating
   precisely: those rows are **not in the team's data root**, so no ordinary path — a glob of the
   data directory, a merge, a `read_parquet` of what was handed over — can reach them by accident.
   Deliberate access is what layers 3 and 4 are for: the playbook prohibits every organiser-only
   path by name, and the pre-flight source scan matches those paths against both the content and the
   file names of the frozen archive before a single number is scored. Blindness therefore rests on
   absence-from-the-data-root **plus** the prohibition **plus** the scan — not on absence alone.

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
4. **Future-corruption test.** The organiser corrupts every row strictly after each decision
   boundary and asserts byte-identical target weights. Failure is terminal.

## 6. Common risk unit

Each strategy is normalised to a common ex-ante risk level so that drawdown comparisons measure
**tail behaviour and regime timing** rather than who chose to trade smallest.

Order of operations at each decision boundary `t`:

1. Team returns raw target weights. The evaluator normalises them to unit gross
   (`Σ|w| = 1`), preserving relative sizing and net exposure.
2. The team's own declared risk policy is applied (volatility target, drawdown brakes, position
   stops, time stops, turnover limits, side scaling), producing the **unscaled book**.
3. **Common risk unit.** Let `σ_t` be the annualised standard deviation of the unscaled book's
   **gross** bar returns over the trailing 90 days, using rows strictly before `t`. Gross returns
   are used deliberately: it removes any circularity between the scalar and the costs it induces,
   and volatility is dominated by exposure, not by fees.

   ```
   s_t = clamp(0.10 / σ_t, 0.20, 3.0)          if ≥ 90 bars of history
   s_t = 1.0                                    otherwise
   ```

4. Executed weights = `s_t × unscaled weights`, then gross, per-symbol and participation caps.

Both the **normalised** book (official, all floors and scores) and the **raw** book (diagnostic)
are reported for every run.

**Interaction with the unlevered gross cap.** Because gross is capped at 1.0× equity (§4), the
scalar can always take a book *down* to the common target but cannot take a very-low-volatility
book *up* past unit gross. Such a book would realise less than the 10% target and collect an
unearned drawdown advantage in the one contest this tournament ranks on. Two things close that
hole rather than one: realised annualised volatility is a **disclosed diagnostic on every run**,
and a candidate whose neighbourhood-median realised volatility falls below **0.06** fails a hard
floor (§7.3). A book that cannot reach 6% annualised volatility at full unlevered gross is not a
deployable book, and it is disqualified rather than rewarded for being small.

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
nominate merely because its budget or wall-clock is exhausted.

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

**Every scored metric is the per-metric median across the neighbourhood's runs.** The nominated
point's own coherent metric vector, and the coherent vector of the median-performing point, are
both reported as diagnostics but neither is the score.

Rationale: nominating a best point is nominating the maximum of a noisy surface, which is
upward-biased by construction. A median over a pre-declared plateau is not. This is also applied on
the holdout (§8), so the final ranking is a plateau estimate rather than a spike.

### 7.3 Hard floors

Conjunctive. Evaluated on the neighbourhood-median record, common risk unit. Never waived, never
lowered, never rounded into compliance, never averaged away. A missing or non-finite value fails.

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
charter, including the holdout eligibility floors of §8.

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

**Winner eligibility** (all must hold, neighbourhood median, common risk unit):

- base and 2×-cost annualised return > 0;
- 2×-cost Sharpe > 0;
- maximum drawdown ≤ 0.25;
- at least 5 of 8 quarters positive;
- the nominated point itself has positive 2×-cost return (guards against a nominee that is an
  outlier within its own plateau).

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
  config.py universe.py snapshot.py engine.py risk_unit.py journal.py
  qualification.py scoring.py scored_metrics.py adjudication.py runner.py report.py paper.py
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
| 1 | 12 teams research IS in parallel (QR + QE per team), ≥8 trials, certificate, nominate | nomination registry closed at one journal head |
| 2 | Mechanical qualification, falsification DQs, `G` ranking | selection freeze: top-3 + ensemble weights |
| 3 | Holdout observations, private build, hash-verified bundle | single release authorisation |
| 4 | Comparative Critic review, final report, ensemble report | leaderboard published |
| 5 | Six-month paper desk for the winner | forward gates pre-registered, parity asserted |

## 13. Authority and amendments

The config controls numerical policy; the charter controls meaning; activation fails on
disagreement. Every stage transition, counter, hash, gate vector, score and advancement decision is
append-only, reproducible from frozen authorities, and attributable to an organiser event. Changes
after activation require a prospective, append-only amendment recorded **before** the affected data
are accessed. Historical evidence is never rewritten. Silence, missing output and DNF never count
as a valid submission.

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

# Independent team rules

Choose a causal economic mechanism independently. No mechanism family, prior strategy, prior
tournament result, or expected outcome is supplied. The only market observations used for
research are delivered by the organizer's official in-sample evaluator after a preregistered
candidate is accepted.

Use the first accepted candidate's `mechanism` text as the stable family label for ordinary
formation, rebalance, risk, inversion, and neighborhood variants. A parented `control-ablation`
or `role-check` may use more descriptive mechanism prose when it names a candidate already
accepted in the current family. This does not change families. A genuine family change must carry
the `mechanism-pivot` tag, may occur at most once, and establishes the new stable family label;
later controls must parent a candidate in that new family. A no-op or second pivot is rejected.

Your process runs in an OS-enforced, deny-by-default filesystem profile. Read only this kit, your
own brief/policy, your own candidates and work notes, and your lane-local feedback. Write only
inside `candidates/`, `work/`, and `outbox/`. Command networking, web/browser tools, plugins,
skills, subagents, other lanes, repository history, organizer code/state, raw data, and every
earlier edition are unavailable. The initial context contains no installed skill catalog or host
skill path. Do not use remembered post-cutoff prices, results, or strategy code. Pre-existing
`.keep` files are organizer-owned frozen directory markers; do not edit or remove them.

Create eight preregistered candidates in the first batch and at most four additional candidates
after lane-local feedback. Cover a transparent baseline, its exact sign inversion, three formation
horizons, two rebalance horizons, three risk/control profiles, long/short role checks, and a
five-point local neighborhood around any prospective nominee. Every accepted request consumes one
of twelve slots, including failures. After all twelve trials, the organizer deterministically
submits the strongest successful candidate under the frozen ordering below. If a score-blind
refinement batch terminates after discovery produced a success, the organizer preserves the
strongest discovery success, records the actual eight accepted trials, and charges the full
twelve-trial selection penalty. This removes any benefit from choosing not to publish a valid
refinement batch after reading discovery feedback. Retirement is permitted only when the lane has
no successful trial. There is no separate team decision model or outbox.

The representative ordering is higher worst-fold 2x-cost Sharpe, then higher median-fold 2x-cost
Sharpe, higher trial-adjusted confidence, higher gross edge per turnover, lower annualized
turnover, and finally the lexicographically smaller candidate identifier. Passing every frozen
gate (including the complete research certificate and field-adjusted confidence) earns the
`fully-qualified` badge. At selection, fully qualified representatives rank first. If fewer than
five earn that badge, the organizer fills the bracket to exactly five with the strongest remaining
successful representatives without changing, concealing, or claiming that they passed a failed
gate. If fewer than five teams produce any successful candidate, selection fails closed.
For the final comparison, the organizer recomputes each successful candidate's trial-adjusted
confidence using twelve charged selection trials as
`max(0, min(1, 1 - 12 * (1 - bootstrap_probability_positive_mean)))`; provisional adjustments
recorded at different earlier trial counts are never compared.

The organizer performs one score-blind admission preflight over the entire batch before accepting
its first request. Before terminal rejection, every lane receives up to three uniform repair
sessions containing only deterministic admission findings; no score, trial outcome, peer state,
or holdout data is opened. A batch that remains invalid after those repairs terminally retires the
lane without consuming a trial. Validate all candidates from `templates/strategy.py` against the
exact call allowlists in `ADMISSION-CHECKER.md` before publishing the outbox. For
`neighborhood_coordinates`, every key must also exist
in `material_parameters` as the same finite non-boolean numeric value. Use an empty object for a
control or role check that is not itself a local-neighborhood point; `neighborhood_id` may be null.

The team process exits before the organizer runs a batch. Put only a schema-valid broker request
in `outbox/`; a later isolated session receives normalized results only under `feedback/`. Never
infer results from elapsed time or host state. Historical holdout data and every field-wide status
remain undisclosed until the organizer's atomic release.

Candidates contain UTF-8 causal source/configuration only. No data, fitted state, timestamp-keyed
signals or targets, returns, fills, positions, scores, encoded lookup payloads, symlinks, hard
links, caches, or generated binaries are allowed. Only Python modules are mounted for execution;
configuration, notes, and attestations are archived as evidence but are not mounted. Material
runtime parameters must therefore be explicit in source. The organizer performs causal source
review and future-append/corrupt-future invariance checks before nomination.

Keep executable source compact and transparent: exactly one `strategy.py`, at most 128 KiB total.
The executable subset is deliberately stateless: `target_weights` cannot read or mutate `self`,
branch on `context.decision_time`, delegate to candidate helper code, use persistent module/class
state or iterators, while loops, bit/packing arithmetic, modulo, powers, literal indexing,
character/ordinal conversion, RNG APIs, executable docstrings, or any list/set/dict/generator
comprehension. It must contain exactly one
direct module-level class method with the exact `target_weights(self, context, *, seed)` signature,
no decorators or defaults, and no other candidate-defined helper function. Non-docstring
operational strings are ASCII, at most 64 characters each, must be one of the frozen API
column/option names, and are limited to 256 characters in aggregate. Nonempty list/tuple/set/dict
literals are forbidden; at most 24 numeric literals and 64 total literal nodes are allowed. Numeric
literals are ordinary non-scientific decimals/integers, bounded by 10,000 and six significant
digits (integers also fit 14 bits). Dynamic code, file/data loaders, opaque numbers, byte payloads, and packed
sequences are rejected. These are hard admission limits, not targets. Put explanations in comments
or inaccessible docstrings and keep material parameters directly readable.

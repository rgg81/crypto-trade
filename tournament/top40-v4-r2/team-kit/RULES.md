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
subagents, other lanes, repository history, organizer code/state, raw data, and every earlier
edition are unavailable. Do not use remembered post-cutoff prices, results, or strategy code.

Create eight preregistered candidates in the first batch and at most four additional candidates
after lane-local feedback. Cover a transparent baseline, its exact sign inversion, three formation
horizons, two rebalance horizons, three risk/control profiles, long/short role checks, and a
five-point local neighborhood around any prospective nominee. Every accepted request consumes one
of twelve slots, including failures. A team may retire honestly; nomination is never required.

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
character/ordinal conversion, RNG APIs, or executable docstrings. It must contain exactly one
direct module-level class method with the exact `target_weights(self, context, *, seed)` signature,
no decorators or defaults, and no other candidate-defined helper function. Non-docstring
operational strings are ASCII, at most 64 characters each, must be one of the frozen API
column/option names, and are limited to 256 characters in aggregate. Nonempty list/tuple/set/dict
literals are forbidden; at most 24 numeric literals and 64 total literal nodes are allowed. Numeric
literals are ordinary non-scientific decimals/integers, bounded by 10,000 and six significant
digits (integers also fit 14 bits). Dynamic code, file/data loaders, opaque numbers, byte payloads, and packed
sequences are rejected. These are hard admission limits, not targets. Put explanations in comments
or inaccessible docstrings and keep material parameters directly readable.

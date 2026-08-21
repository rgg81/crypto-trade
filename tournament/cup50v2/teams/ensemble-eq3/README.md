# ensemble-eq3 — organizer-written, and why it does not pass the team clean-room scan

`scan_research_root` reports `forbidden-import:strategy.py:pathlib` for this bundle. That is
correct and expected, and it is recorded here rather than left to be rediscovered at release.

**The scan governs team submissions.** Its forbidden-call and forbidden-import lists exist to stop
a competing lane reaching outside its sandbox — reading another team's workspace, the sealed
window, or a prior edition's results. Every one of the twelve nominated bundles passes it, and that
was verified before field close.

**This bundle is not a submission.** It is organizer code, committed under `tournament/cup50v2/`,
whose entire function is to instantiate the three eligible finalists from *their* frozen bundles at
*their* frozen centres. Loading three bundles requires reading three paths. A version of this file
that passed the team scan would be a version that could not do its job.

**What constrains it instead:**

- It is bound by name and digest in the activation record, like every other organizer module.
- `finalists.json` names exactly three finalists; `build_strategy()` refuses any other count.
- Each finalist is loaded through the evaluator's own `load_strategy_module` and sized by the
  evaluator's own EWMA covariance recipe — this file adds no data access of its own beyond reading
  its manifest and the three bundles the release already published.
- The desk that runs it re-verifies its digest on every tick, so the bytes cannot change quietly.
- It reads no sealed data, no team workspace, and no prior edition. The three paths it opens are
  all published output of this edition's own release.

**Do not "fix" the scan finding by narrowing the exemption in `isolation.py`.** The scan is applied
to team research roots and is correct as written; weakening it to accommodate one organizer bundle
would weaken it for all twelve lanes, which is the trade this note exists to prevent.

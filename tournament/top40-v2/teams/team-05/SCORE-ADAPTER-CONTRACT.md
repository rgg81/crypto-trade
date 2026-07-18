# Team 05 LDM A5 score-adapter contract

Candidate `team05-ldm-pivot02-core-v1` directly imports
`crypto_trade.tournament.score_adapter_protocol_v5.score_boundary`.

At each scheduled weekly decision, Team 05 finishes every LDM feature transform first: exact
past-closed bar admission, valid cross-sectional quote-volume shares, unsigned range-per-share
impact, disjoint baseline/recent medians, log depth improvement, and centered fractional ranking.
`candidate_score_values` then passes the complete sorted built-in `dict[str,float]` to A5 exactly
once. A scheduled invalid state passes `{}`. An off-schedule boundary returns `None` without calling
A5.

The A5 return must preserve the key set and contain only finite built-in floats in `[-1,1]`.
Malformed output fails flat. Valid returned values—not a hidden copy—drive the score-span gate and
top/bottom selection. Raw depth improvement remains available only for the fixed median separation
check on sleeves selected by returned scores. Equal weighting, gross/net checks, symbol caps, and
organizer-owned risk are all downstream.

The declared diagnostic uses the same Unix-epoch 168-hour schedule as the strategy and a 168-hour
simple executable-open-to-executable-open return label, with fold-end purging. Higher score means
higher expected return. Pooled Pearson correlation must be positive with at least four of six
positive fold correlations and every other gate in `qualification_thresholds.json` passing.

The strict immutable order is: complete LDM materialization, executable-source manifest first add,
independent semantic review first add, score manifest first add, A7 final parent-linked family
registration, final source fingerprint, trial registration, then one official development run.
Amendment 0008 is not part of this candidate's authority.

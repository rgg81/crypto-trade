# Team 06 pivot handoff

Status: source and prospective registration drafts implemented; no test, validator, registration,
diagnostic, evaluator, or lifecycle command was run by the pivot author.

Organizer progress after author handoff: serial formatting, lint, JSON validation, 13 focused
tests, source preflight, independent A5 semantic review, and the A7 family/candidate metadata
rebind passed. Family registration, canonical A5 first-adds, final hashes, trial registration, and
development evaluation remain pending.

## Outcome

The parent `t06-balanced-trend-reversal-v1-base` is preserved as immutable completed negative
evidence and consumed Team 06 material trial 1. Its net Sharpe was `-0.524809872995251`, annualized
return `-0.24452542046360337`, doubled-cost Sharpe `-0.799922357968985`, maximum drawdown
`0.7380842004083039`, and bear/bull/chop Sharpe respectively `-1.4458380733522744`,
`0.0640641950162595`, and `0.9867176235750049`. No parent control or neighbor activates.

The canonical root executable now implements the new family
`t06-relative-rank-acceleration-v1`, candidate
`t06-relative-rank-acceleration-v1-base`. It is a mechanism pivot, not a risk variation:

- per-bar cross-sectional return ranks remove the common crypto direction;
- only changes from prior to recent two-day relative rank are reversed;
- persistent relative-rank level, raw price trend, market-direction mixing, and net tilt are gone;
- the schedule changes from daily to 48 hours to match the causal horizon and reduce churn;
- broad exact-dollar-neutral sleeves replace the parent's directionally tilted construction;
- every evaluator control remains disabled in root `risk_policy.json`.

The detailed causal equation, universe contract, intended regime roles, and noncompensatory
falsifier are in `research_brief.md`. `pivot-01/pivot-registration.template.json` records the
pivot decision; the adjacent family and trial templates are drafts only.

## Required serialized organizer sequence

1. Inspect the Team 06 diff and verify that no organizer journal, result, report, or A7 authority
   file changed.
2. Run formatting/lint, JSON validation, the canonical Team 06 synthetic suite, organizer risk
   validation, source preflight, and a clean import/target smoke test serially. Fix source only if
   evidence requires it; do not register a failing package.
3. Obtain independent static semantic review of the exact final executable set and direct A5
   boundary placement. The author-provided review-shaped file is only a template.
4. Materialize the new family input outside the Team 06 source tree from
   `pivot-01/family-registration.template.json`, replacing only its event timestamp, and run
   `pivot-team team-06` through the active A7 dispatcher. The family append must precede final
   source fingerprinting.
5. After family registration and final source validation, derive the complete executable-source
   manifest at the exact new canonical A5 path. First-add it, obtain and first-add the independent
   semantic review, then hash that review and first-add the 48-hour score manifest. Do not alter a
   historical v1 A5 file.
6. Confirm Team 06's completed A7 execution-authority metadata rebind still names the exact new
   family/candidate. After all three canonical A5 first-adds, recompute the final Team 06 source
   bundle, strategy, config, and no-control risk hashes; no candidate-tree byte may change
   afterward.
7. Materialize the trial input outside the source tree from
   `pivot-01/trial-registration.template.json`, including the exact score-manifest opt-in SHA, and
   register the pivot as material trial 2. Registering any template or placeholder is prohibited.
8. Run the visible-development no-control reference once. The same material run emits 1x and 2x
   cost views. Then reserve/run the non-material A5 score diagnostic.
9. Apply every PnL and score-evidence gate in `trial_plan.json` together. Any failure stops the
   family. A stop, volatility target, drawdown brake, turnover cap, neighbor, or private ticket
   cannot compensate.

The active authority is A7 entrypoint SHA-256
`8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9`, integration-freeze
commit `c8b917ca49306d5200a4e08848e73ff6f5a18bf3`, freeze SHA-256
`6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51`. Its delegated A6
pure-crypto report SHA-256 is
`b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b` with zero violations.

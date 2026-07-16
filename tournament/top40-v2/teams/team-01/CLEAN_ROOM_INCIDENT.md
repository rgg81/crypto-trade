# Clean-room incident: over-broad lifecycle-command search

## Occurrence

- Date: `2026-07-16`.
- Exact wall-clock time: unavailable from the command result; no timestamp is being inferred.
- Relative point in work: after the Team 01 pivot strategy, tests, frozen config, family package,
  lineage, ablations, and parameter-neighborhood files had been drafted; before inspecting the
  shared tournament command parser and before drafting the trial template, command handoff,
  test-evidence placeholder, and QE handoff.
- Working directory:
  `/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v2`.

## Exact command/query

```text
rg -n "family.*register|register.*family|trial.*register|register.*trial|evaluate" tournament/top40-v2 crypto_trade/tournament | head -n 160
```

The intent was to locate the shared public V2 lifecycle command syntax. The query was incorrectly
scoped to the entire `tournament/top40-v2` tree instead of shared public files plus Team 01 only.
The second search root did not exist and emitted this path in an error:

```text
crypto_trade/tournament
```

## Non-Team01 paths visibly displayed

Every non-Team01 path that was visibly named in the returned result is listed below. Repeated
matches to the same path are listed once.

Shared/public paths:

- `tournament/top40-v2/METHODOLOGY-DISTILLATION.md`
- `tournament/top40-v2/PHASE0-POLICY.md`
- `tournament/top40-v2/TEAM-PLAYBOOK.md`

Other-team paths:

- `tournament/top40-v2/teams/team-02/ablations.json`
- `tournament/top40-v2/teams/team-02/development_review_team_02_c3rp_baseline_001.json`
- `tournament/top40-v2/teams/team-02/development_review_team_02_c3rp_baseline_001.md`
- `tournament/top40-v2/teams/team-02/experiments.jsonl`
- `tournament/top40-v2/teams/team-02/families.jsonl`
- `tournament/top40-v2/teams/team-02/pivot-01/ablations.json`
- `tournament/top40-v2/teams/team-02/pivot-02/family-registration.json`
- `tournament/top40-v2/teams/team-02/pivot-02/research_brief.md`
- `tournament/top40-v2/teams/team-02/post_result_decision_team_02_fir_reference_001.json`
- `tournament/top40-v2/teams/team-02/provenance.md`
- `tournament/top40-v2/teams/team-02/QE_REPORT.md`
- `tournament/top40-v2/teams/team-02/research_brief.md`
- `tournament/top40-v2/teams/team-03/families.jsonl`
- `tournament/top40-v2/teams/team-03/pivot-01/provenance.md`
- `tournament/top40-v2/teams/team-03/pivot-01/risk_ablation_plan.json`
- `tournament/top40-v2/teams/team-04/research_brief.md`

The command result reported that its output was truncated. Paths inside the omitted segment were
not displayed and therefore cannot be enumerated as displayed paths. The visible result also
contained a spliced trailing fragment of other-team family content after the truncation marker
without a visible associated path; it is recorded in the content categories below and was not
used.

## Categories of content exposed

Without reproducing other-team content, the visible match excerpts exposed these categories:

- other-team family-ledger metadata, including family identifiers and fragments of theses,
  mechanisms, falsifiers, parameter domains, risk plans, selection rules, and timestamps;
- other-team trial-ledger metadata, including candidate identifiers, registration fields, hashes,
  and fragments of preregistered hypotheses;
- other-team pivot provenance, ablation/risk-plan, research-review, QE, and terminal-decision
  fragments;
- shared public policy, methodology, and playbook lines referring to registration, evaluation,
  pivots, and risk-policy sequencing.

No private-qualifier or final-OOS path was visibly named by the result.

## Edits made before exposure

The following Team 01 edits already existed before the over-broad query:

- `tournament/top40-v2/teams/team-01/strategy.py`
- `tournament/top40-v2/teams/team-01/test_strategy.py`
- `tournament/top40-v2/teams/team-01/frozen_config.json`
- `tournament/top40-v2/teams/team-01/pivot-01/family_registration_t01_regime_conditional_trend_carry_v2.json`
- `tournament/top40-v2/teams/team-01/pivot-01/reference_candidate.json`
- `tournament/top40-v2/teams/team-01/pivot-01/research_brief.md`
- `tournament/top40-v2/teams/team-01/pivot-01/feature_lineage.json`
- `tournament/top40-v2/teams/team-01/pivot-01/ablations.json`
- `tournament/top40-v2/teams/team-01/pivot-01/parameter_neighborhood.json`

Those choices were derived from Team 01's own H14 post-result review and stopped-family artifacts,
plus the task specification supplied by the organizer. They predate the exposure.

## Edits made after exposure and before the stop instruction

After the exposure, the shared `scripts/top40_v2_tournament.py` command definitions were inspected
to obtain lifecycle argument order. The following Team 01 files were then added or changed:

- `tournament/top40-v2/teams/team-01/pivot-01/trial_registration_rctc_pivot_ref_001.template.json`
- `tournament/top40-v2/teams/team-01/pivot-01/provenance.md`
- `tournament/top40-v2/teams/team-01/pivot-01/commands.json`
- `tournament/top40-v2/teams/team-01/test_evidence.json`
- `tournament/top40-v2/teams/team-01/QE_REPORT.md`

Two small later edits changed only a pending tournament-config hash label in the trial template and
expanded the unexecuted hash command in `commands.json`. Team 01-local read-only inspections then
checked the strategy text, pivot file list, and stale identifier references. No tests, strategy
imports, evaluator, lifecycle command, or Git command were run.

## Incorporation assessment

No Team 01 mechanism decision, threshold, parameter, risk rule, falsifier, code branch, test case,
trial allocation, or evidence claim incorporated other-team content from the accidental output.
The strategy, tests, family specification, lineage, ablations, and neighborhood were already
written before exposure. The post-exposure lifecycle command syntax came from the shared command
parser, not from another team's files. The post-exposure handoff documents restated Team 01's own
pre-existing specification and used explicit pending placeholders; they did not copy or adapt an
other-team design or result.

This statement records factual non-incorporation, not an integrity disposition. All current Team 01
changes are being left for organizer review without further pivot editing.

# Team isolation contract

Strategy blindness is part of the experiment.

## A team may read

- `TOURNAMENT-CHARTER-TOP12-V1.md`;
- `tournament/top12-v1/TEAM-API.md`;
- this isolation contract;
- its own `tournament/top12-v1/teams/<team-id>/` lane; and
- standardized evidence returned by the organizer for its own accepted trials.

## A team must not read

- any path beginning `tournament/top40`, `reports-top40`, `diary`, or `briefs`;
- prior strategy, candidate, submission, result, deployment, retrospective, or paper-trading code;
- `tournament/top12-v1/ORCHESTRATOR-MECHANISM-REGISTRY.json`;
- any other Top-12 team lane;
- `reports-top12-v1`, the lifecycle journal, nomination registry, selection freeze, or private OOS;
- git history, diffs, branches, or object contents for the purpose of discovering a strategy; or
- external descriptions of strategies previously tested in this repository.

Repository search is not permission to inspect a forbidden path. If an accidental command exposes
one, stop immediately, do not use the information, and report the exact path to the organizer.

## Communication

A team submits only its own hypothesis, implementation, falsifier, and requested trial. The
organizer returns metrics and diagnostic labels without naming another strategy. The team may ask
about the neutral API or rules, but not whether another team or earlier tournament used an idea.

## Collision and rediscovery

The organizer, not the team, checks current-tournament mechanism collisions. A baseline or pivot
may be refused before market access and reassigned without revealing the conflicting mechanism.
Independent rediscovery of an older strategy is allowed because prior-tournament exclusion is not
the objective; prior-strategy blindness is.

## Breach

Access to a forbidden strategy or result quarantines the team immediately. It receives no further
data. The organizer records an incident and decides whether a fresh identity can restart in an
untouched lane before OOS. A team exposed to sealed OOS data cannot restart.

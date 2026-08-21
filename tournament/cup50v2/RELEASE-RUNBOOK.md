# CUP-50 v2 — from the last observed point to four running desks

The order matters and two steps are irreversible. Written down because the sequence is executed
once, and improvising it at the end of a ten-hour run is how editions acquire incidents.

## 0. Do not run integrity-review while any point is in flight

`integrity_review` calls `recover_interrupted_points`, which turns **every started-without-terminal
point into a permanent zero**. Run during observation it would silently DNF the six points
currently executing.

Wait for `observation complete` in the runner log, and confirm:

```
ls tournament/cup50v2/private/points | wc -l      # must be 208
pgrep -fc 'cup50v2 observe point'                 # must be 0
```

If the run was hard-killed, run `cup50v2 observe restart` **first** (A8) and let the resumable
points finish. Restart before review; review before release.

## 1. Integrity review

```
uv run cup50v2 integrity-review \
  --field tournament/cup50v2/private/field-close.json \
  --signing-key tournament/cup50v2/private/field-signing.key \
  --journal tournament/cup50v2/private/observation.jsonl \
  --private-stage tournament/cup50v2/private/points \
  --output tournament/cup50v2/private/integrity-review.json
```

Refuses on an unresolved organizer pause, on any point without exactly one terminal record, and on
any observed point the field did not freeze.

## 2. Leaderboard

Same inputs, `--output reports-cup50v2/leaderboard.json`. Ranking is eligible before ineligible
before DNF, then by S. The winner is the first `valid and eligible` entry. **Zero eligible is a
legal outcome**: no winner, no desk, edition closes.

## 3. Re-activate — the A13 remedy

The sealed observation ran with a `cli.py` no activation bound, because A12 edited it after
re-activation. Re-activate **now**, before release, so the published result binds the evaluator
that produced it. The charter and any amendment written during the run get bound here too — they
could not be edited during observation without drifting the evaluator.

Preflight may carry forward only what is provably unchanged; re-run the rest. Record which is which
in `preflight/provenance.json`.

## 4. Release

```
uv run cup50v2 release \
  --leaderboard reports-cup50v2/leaderboard.json \
  --integrity-review tournament/cup50v2/private/integrity-review.json \
  --output reports-cup50v2/release.json
```

Atomic. After this the results are public and **no scoring, qualification or execution change is
permitted** — a material defect found later voids the edition into a new version rather than
correcting this one.

## 5. Bind four desks

Winner, runner-up-1, runner-up-2 from the leaderboard's eligible order; `ensemble-eq3` over those
same three.

```
uv run python scripts/cup50v2_activate_paper.py \
  --desk-id winner --team-id <team> --candidate-id <candidate> --launch <first 8h boundary>
```

Then write `tournament/cup50v2/teams/ensemble-eq3/finalists.json` naming exactly those three at
their frozen centres and bundle paths, and activate `ensemble-eq3` the same way.

Write `paper-cup50v2/launch.json` with the launch boundary **last** — the watchdog refuses to start
anything until it exists, so it is the switch that arms the field.

## 6. First tick and the watchdog

```
bash scripts/cup50v2_paper_watchdog.sh
uv run python scripts/cup50v2_paper_healthcheck.py
```

Expect `STATUS OK` with four desks and `capital ACCRUING`. Register the watchdog in the **system**
crontab at `*/15`, not a session cron — a session cron dies on host restart.

## 7. Afterwards

`/cup50v2-monitor` carries the operating rules. The capital rule is read **once**, after 183
official days. Do not compute a provisional winner before then.

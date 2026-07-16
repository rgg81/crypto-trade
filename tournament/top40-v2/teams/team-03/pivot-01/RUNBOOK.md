# Team 03 pivot-01 serialized commands

These commands are organizer instructions only. None was run while implementing the pivot. Run
them sequentially from the repository root; stop at the first failure.

## Validate the frozen source

```bash
uv run ruff check tournament/top40-v2/teams/team-03/strategy.py tournament/top40-v2/teams/team-03/test_strategy.py tournament/top40-v2/teams/team-03/pivot-01/prepare_preregistration.py
uv run ruff format --check tournament/top40-v2/teams/team-03/strategy.py tournament/top40-v2/teams/team-03/test_strategy.py tournament/top40-v2/teams/team-03/pivot-01/prepare_preregistration.py
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tournament/top40-v2/teams/team-03/test_strategy.py
uv run python scripts/top40_v2_tournament_active.py validate-risk-policy tournament/top40-v2/teams/team-03/risk_policy.json
```

Record the real results and file hashes in `pivot-01/test_evidence.json`. Because that edit changes
the source bundle, do it before family registration and make no further unrecorded source edits.

## Serialize and register the child family

Choose a trusted organizer UTC timestamp. The serializer replaces the timestamp in stdout only; it
does not mutate `pivot-01/submission.json`.

```bash
uv run python tournament/top40-v2/teams/team-03/pivot-01/prepare_preregistration.py family --timestamp-utc YYYY-MM-DDTHH:MM:SS.ffffffZ > /tmp/team03-pivot01-family-registration.json
uv run python scripts/top40_v2_tournament_active.py pivot-team team-03 /tmp/team03-pivot01-family-registration.json
uv run python scripts/top40_v2_tournament_active.py research-status
```

Visually confirm the child family ID, parent family ID, pivot mechanism, falsifier, and journal
projection. Family registration changes `families.jsonl`, which participates in the source-bundle
fingerprint.

## Serialize and register the base trial

Only after successful family registration and a final source freeze:

```bash
uv run python tournament/top40-v2/teams/team-03/pivot-01/prepare_preregistration.py trial --timestamp-utc YYYY-MM-DDTHH:MM:SS.ffffffZ > /tmp/team03-pivot01-trial-registration.json
uv run python scripts/top40_v2_tournament_active.py register-trial team-03 /tmp/team03-pivot01-trial-registration.json
uv run python scripts/top40_v2_tournament_active.py research-status
```

## Consume the base only

```bash
uv run python scripts/top40_v2_tournament_active.py run-window development team-03 t03-crsa-base-i3-c1-b30-v21
uv run python scripts/top40_v2_tournament_active.py research-status
```

Do not register or run a neighbor unless the no-control base passes every declared hard,
development, fold, cost, regime, sleeve, activity, and concentration gate. A base failure is Team
03 DNF. The four neighbors require separate registrations and are not authorized by the base
payload.

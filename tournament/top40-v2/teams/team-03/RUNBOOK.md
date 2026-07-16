# Team 03 serialized first-iteration commands

These commands are proposed for the organizer. They were not run while preparing the candidate.
Run them sequentially only after confirming that result-bearing Top-40 V2 operations are open.

```bash
python -m pytest -q tournament/top40-v2/teams/team-03/test_strategy.py
python -m ruff check tournament/top40-v2/teams/team-03/strategy.py tournament/top40-v2/teams/team-03/test_strategy.py tournament/top40-v2/teams/team-03/prepare_preregistration.py
python scripts/top40_v2_amended_tournament.py validate-risk-policy tournament/top40-v2/teams/team-03/risk_policy.json
```

Choose a trusted organizer UTC timestamp for the family record, serialize the exact payload, and
register the family:

```bash
python tournament/top40-v2/teams/team-03/prepare_preregistration.py family --timestamp-utc YYYY-MM-DDTHH:MM:SS.ffffffZ > /tmp/team03-family-registration.json
python scripts/top40_v2_amended_tournament.py register-family team-03 /tmp/team03-family-registration.json
```

Family registration changes `families.jsonl`, which participates in the complete source-bundle
fingerprint. Therefore serialize the trial only after the family command succeeds and after no
further source edit:

```bash
python tournament/top40-v2/teams/team-03/prepare_preregistration.py trial --timestamp-utc YYYY-MM-DDTHH:MM:SS.ffffffZ > /tmp/team03-trial-registration.json
python scripts/top40_v2_amended_tournament.py register-trial team-03 /tmp/team03-trial-registration.json
python scripts/top40_v2_amended_tournament.py research-status team-03
```

Only after visually verifying the serialized registration and journal projection should the
organizer consume the first material configuration:

```bash
python scripts/top40_v2_amended_tournament.py run-window development team-03 t03-rlsa-base-h3-b30-v21-f25
python scripts/top40_v2_amended_tournament.py research-status team-03
```

`run-window development` records a terminal result even when execution fails. Do not rerun or alter
the candidate after registration. Inspect only Team 03's canonical development artifacts before
applying the preregistered falsifier. Parameter neighbors and risk ablations require new material
registrations and are not authorized by the base registration.

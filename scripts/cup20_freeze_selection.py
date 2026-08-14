"""Freeze the three finalists, and everything that identifies them, before the holdout comes back.

This is the artifact ``quarantine.restore_holdout`` refuses to proceed without, and the reason it
refuses is worth stating: the holdout may not return while a team could still change what it
nominated. Once these bytes are on disk the field is closed by evidence rather than by assertion --
each finalist's strategy source, risk policy and declared neighbourhood are pinned by digest, so a
nomination edited after the reveal is detectable rather than merely forbidden.

It also pins what the finalists were selected BY: the in-sample standing of every team, the
amendments in force, the activation record, and the journal's own head digest. A selection freeze
that recorded only the winners would leave no way to show, afterwards, that the ordering was the
one the frozen formula actually produced.

Run from the repository root, with the holdout still quarantined:

    uv run python scripts/cup20_freeze_selection.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from crypto_trade.cup20.config import load_config  # noqa: E402
from crypto_trade.cup20.journal import append_record, read_records, verify_chain  # noqa: E402
from crypto_trade.cup20.trials import (  # noqa: E402
    candidate_source_digest,
    multiplicity_charged_count,
    risk_policy_digest,
)

SCHEMA = "cup20-selection-freeze-v1"
SELECTION_EVENT = "selection_frozen"


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _standings(path: pathlib.Path) -> dict:
    """The last recorded field-closed standing. Read, never recomputed here.

    Recomputing the ranking inside the artifact that freezes it would let this script disagree
    with the journal about who advanced, and the journal is the record.
    """
    for record in reversed(list(read_records(path))):
        if record.get("event_type") == "field_closed":
            return dict(record["payload"])
    raise SystemExit("REFUSED: no field_closed record in the journal; the field is not closed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="tournament/cup20/config.toml")
    parser.add_argument("--out", default="tournament/cup20/selection-freeze.json")
    arguments = parser.parse_args()

    raw = load_config(arguments.config).raw
    journal_path = pathlib.Path(raw["paths"]["research_journal"])
    records = verify_chain(journal_path)
    closed = _standings(journal_path)

    out = pathlib.Path(arguments.out)
    if out.exists():
        raise SystemExit(f"REFUSED: {out} already exists; the selection is already frozen")

    slots = int(raw["selection"]["advancing_slots"])
    ranking = closed["ranking"]
    advancing = [row for row in ranking if row["team"] in closed["advancing_to_holdout"]]
    if len(advancing) != slots:
        raise SystemExit(
            f"REFUSED: the journal names {len(advancing)} advancing teams, contract says {slots}"
        )

    teams_root = pathlib.Path("tournament/cup20/teams")
    finalists = []
    for row in sorted(advancing, key=lambda r: r["rank"]):
        candidate_root = teams_root / row["team"] / "candidates" / row["candidate"]
        if not candidate_root.is_dir():
            raise SystemExit(f"REFUSED: {candidate_root} does not exist")
        finalists.append(
            {
                "rank": row["rank"],
                "team_id": row["team"],
                "candidate_id": row["candidate"],
                "in_sample_G": row["G"],
                "multiplicity_charged_trials": multiplicity_charged_count(
                    journal_path, row["team"]
                ),
                "source_sha256": candidate_source_digest(candidate_root),
                "risk_policy_sha256": risk_policy_digest(candidate_root),
                "neighbourhood_sha256": _digest(candidate_root / "neighbourhood.json"),
                "certificate_sha256": _digest(
                    teams_root / row["team"] / "RESEARCH-CERTIFICATE.md"
                ),
            }
        )

    freeze = {
        "schema_version": SCHEMA,
        "tournament": "cup20",
        "field_closed": True,
        "advancing_slots": slots,
        "finalists": finalists,
        "in_sample_ranking": ranking,
        "amendments_in_force": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"],
        "journal_records_at_freeze": records,
        "journal_head_sha256": _digest(journal_path),
        "activation_freeze_sha256": _digest(
            pathlib.Path("tournament/cup20/activation-freeze.json")
        ),
        "charter_sha256": _digest(pathlib.Path(raw["charter_path"])),
        "holdout_still_quarantined_at_freeze": not pathlib.Path(
            raw["data"]["sealed_root"]
        ).exists(),
    }
    out.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")

    append_record(
        journal_path,
        SELECTION_EVENT,
        {
            "selection_freeze_path": str(out),
            "selection_freeze_sha256": _digest(out),
            "finalists": [
                {k: f[k] for k in ("rank", "team_id", "candidate_id", "in_sample_G")}
                for f in finalists
            ],
            "holdout_still_quarantined": freeze["holdout_still_quarantined_at_freeze"],
        },
    )

    print(f"selection frozen -> {out}")
    for f in finalists:
        print(f"  {f['rank']}. {f['team_id']:8s} {f['candidate_id']:22s} G={f['in_sample_G']:6.2f}")
    print(f"\nholdout still quarantined at freeze: {freeze['holdout_still_quarantined_at_freeze']}")
    print(f"journal now {verify_chain(journal_path)} records")


if __name__ == "__main__":
    main()

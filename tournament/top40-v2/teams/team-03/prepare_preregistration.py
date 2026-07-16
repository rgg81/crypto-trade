"""Serialize Team 03 family/trial inputs without mutating candidate source files."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from crypto_trade.tournament.runner_v2 import source_bundle_fingerprint

TEAM_ID = "team-03"
TEAM_RELATIVE = "tournament/top40-v2/teams/team-03"
CONFIG_RELATIVE = "tournament/top40-v2/config.toml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _root() -> Path:
    return Path(__file__).resolve().parents[4]


def _timestamp(value: str) -> str:
    if not value.endswith("Z") or "T" not in value:
        raise ValueError("timestamp must be an explicit UTC value ending in Z")
    return value


def family_payload(root: Path, timestamp_utc: str) -> dict[str, object]:
    raw = json.loads((root / TEAM_RELATIVE / "submission.json").read_text(encoding="utf-8"))
    payload = copy.deepcopy(raw["family_registration"])
    payload["registered_at_utc"] = _timestamp(timestamp_utc)
    return payload


def trial_payload(root: Path, timestamp_utc: str) -> dict[str, object]:
    raw = json.loads((root / TEAM_RELATIVE / "submission.json").read_text(encoding="utf-8"))
    payload = copy.deepcopy(raw["trial_registration"])
    strategy = root / TEAM_RELATIVE / "strategy.py"
    risk = root / TEAM_RELATIVE / "risk_policy.json"
    source_sha256, _entries = source_bundle_fingerprint(
        root,
        TEAM_ID,
        f"{TEAM_RELATIVE}/strategy.py",
    )
    payload.update(
        {
            "timestamp_utc": _timestamp(timestamp_utc),
            "strategy_sha256": _sha256(strategy),
            "source_bundle_sha256": source_sha256,
            "risk_config_sha256": _sha256(risk),
            "config_sha256": _sha256(root / CONFIG_RELATIVE),
        }
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("family", "trial"))
    parser.add_argument("--timestamp-utc", required=True)
    args = parser.parse_args()
    root = _root()
    payload = (
        family_payload(root, args.timestamp_utc)
        if args.kind == "family"
        else trial_payload(root, args.timestamp_utc)
    )
    print(json.dumps(payload, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

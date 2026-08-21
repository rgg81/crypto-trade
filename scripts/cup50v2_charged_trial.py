#!/usr/bin/env python3
"""Run one charged trial on a team's behalf.

A charged trial reads the organizer's in-sample snapshot, which is never mounted in a team
workspace, so registering and evaluating one is an organizer action a team requests rather than
performs. Every lane in the field hit that boundary and reported it; this is the service.

The organizer's part is mechanical on purpose. It binds what the team declared, runs the
evaluator the activation record froze, and journals the result. It makes no research decision,
and it must not: the parameters, the source and the purpose all come from the team.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGERS = Path("/home/roberto/cup50v2-teams/_ledgers")
SANDBOX_ENV = {"CUP50V2_SANDBOX": "network-none-read-only"}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str]) -> dict:
    result = subprocess.run(
        command, cwd=REPO, capture_output=True, text=True, env={**os.environ, **SANDBOX_ENV}
    )
    if result.returncode != 0:
        raise SystemExit(f"{' '.join(command[:6])}...\n{result.stderr[-3000:]}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--bundle", required=True, help="the team's frozen candidate directory")
    parser.add_argument("--kind", default="official", choices=["official", "neighbourhood"])
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--parameters", help="override centre, for a neighbourhood probe")
    arguments = parser.parse_args(argv)

    bundle = Path(arguments.bundle).resolve()
    strategy = bundle / "strategy.py"
    parameters_path = (
        Path(arguments.parameters) if arguments.parameters else bundle / "parameters.json"
    )
    centre = json.loads(parameters_path.read_text())
    centre = centre.get("centre", centre)

    from crypto_trade.cup50v2.trials import TrialBinding, source_bundle_digest

    binding = TrialBinding(
        team_id=arguments.team_id,
        trial_id=arguments.trial_id,
        kind=arguments.kind,
        promoteable=arguments.kind == "official",
        source_sha256=source_bundle_digest(bundle),
        parameters={str(k): float(v) for k, v in centre.items()},
        risk_policy_sha256=_digest(REPO / "tournament/cup50v2/risk-policy.json"),
        seed=arguments.seed,
        data_sha256=json.loads((REPO / "data/cup50v2/is/manifest.json").read_text())[
            "manifest_sha256"
        ],
        config_sha256=_digest(REPO / "tournament/cup50v2/config.toml"),
        scorer_sha256=_digest(REPO / "src/crypto_trade/cup50v2/scoring.py"),
        purpose=arguments.purpose,
    )
    journal = LEDGERS / f"{arguments.team_id}-trials.jsonl"
    binding_path = LEDGERS / f"{arguments.team_id}-{arguments.trial_id}-binding.json"
    binding_path.write_text(
        json.dumps(
            {
                field: getattr(binding, field)
                for field in (
                    "team_id",
                    "trial_id",
                    "kind",
                    "promoteable",
                    "source_sha256",
                    "parameters",
                    "risk_policy_sha256",
                    "seed",
                    "data_sha256",
                    "config_sha256",
                    "scorer_sha256",
                    "purpose",
                )
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    registered = _run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "crypto_trade.cup50v2.cli",
            "trial",
            "--journal",
            str(journal),
            "--binding",
            str(binding_path),
        ]
    )
    binding_sha256 = registered["payload"]["binding_sha256"]

    output = Path(f"/home/roberto/cup50v2-teams/{arguments.team_id}-results/charged")
    output.mkdir(parents=True, exist_ok=True)
    evaluated = _run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "crypto_trade.cup50v2.cli",
            "evaluate",
            "--strategy",
            str(strategy),
            "--source-bundle",
            str(bundle),
            "--snapshot",
            "data/cup50v2/is",
            "--config",
            "tournament/cup50v2/config.toml",
            "--risk-policy",
            "tournament/cup50v2/risk-policy.json",
            "--unavailability-audit",
            "tournament/cup50v2/is-unavailability.json",
            "--trial-journal",
            str(journal),
            "--team-id",
            arguments.team_id,
            "--trial-id",
            arguments.trial_id,
            "--binding-sha256",
            binding_sha256,
            "--start",
            "2021-03-15T00:00:00Z",
            "--end",
            "2024-02-01T00:00:00Z",
            "--seed",
            str(arguments.seed),
            "--output",
            str(output / arguments.trial_id),
        ]
    )
    print(
        json.dumps(
            {
                "team_id": arguments.team_id,
                "trial_id": arguments.trial_id,
                "kind": arguments.kind,
                "result": evaluated,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

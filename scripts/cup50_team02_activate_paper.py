#!/usr/bin/env python3
"""One-shot hash activation for the corrected CUP-50 winner's paper desk."""

from __future__ import annotations

import subprocess
from pathlib import Path

from crypto_trade.cup50_desk.authority import (
    build_deployment_manifest,
    paper_root,
    repository_root,
    verify_deployment,
)
from crypto_trade.cup50_desk.tick import HISTORICAL_PREFIX


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def activation_artifacts(root: Path) -> list[Path]:
    paths = [
        *sorted((root / "src" / "crypto_trade" / "cup50").glob("*.py")),
        *sorted((root / "src" / "crypto_trade" / "cup50_desk").glob("*.py")),
        root / "src" / "crypto_trade" / "cup20_desk" / "live_data.py",
        root / "src" / "crypto_trade" / "tournament" / "snapshot.py",
        root / "run_cup50_team02_paper.py",
        root / "scripts" / "cup50_team02_activate_paper.py",
        root / "scripts" / "cup50_team02_freeze_prefix.py",
        root / "scripts" / "cup50_team02_paper_healthcheck.py",
        root / "scripts" / "cup50_team02_paper_digest.py",
        root / "scripts" / "cup50_team02_paper_watchdog.sh",
        root / "tests" / "cup50_desk" / "test_team02_paper.py",
        root / "pyproject.toml",
        root / "uv.lock",
        root / "tournament" / "cup50" / "config.toml",
        root / "tournament" / "cup50" / "teams" / "team-02" / "strategy.py",
        root / "tournament" / "cup50" / "nominations" / "team-02.json",
        root / "tournament" / "cup50" / "organizer-recovery-unavailability.json",
        root / "tournament" / "cup50" / "historical-asset-classification.json",
        root
        / "tournament"
        / "cup50"
        / "incidents"
        / "2026-08-17-qualification-policy-correction.json",
        root / "reports-cup50" / "corrected-leaderboard.json",
        paper_root(root) / "authority.json",
        paper_root(root) / "reconstruction.json",
        paper_root(root) / HISTORICAL_PREFIX,
        paper_root(root) / "preflight.json",
        root / "data" / "cup50" / "acquisition-remediated-20260817" / "manifest.json",
        root / "data" / "cup50" / "acquisition-remediated-20260817" / "bars.parquet",
        root / "data" / "cup50" / "acquisition-remediated-20260817" / "contract_metadata.parquet",
    ]
    for snapshot in ("is", "sealed"):
        paths.extend(sorted((root / "data" / "cup50" / snapshot).glob("*")))
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"activation artifact is missing: {missing[0]}")
    return paths


def main() -> int:
    root = repository_root()
    if _git(root, "diff", "--name-only") or _git(root, "diff", "--cached", "--name-only"):
        raise RuntimeError(
            "tracked or staged changes remain; commit the deployment before activation"
        )
    commit = _git(root, "rev-parse", "HEAD")
    record = build_deployment_manifest(
        activation_artifacts(root), root=root, git_commit=commit
    )
    verified = verify_deployment(root)
    if verified != record:
        raise RuntimeError("deployment manifest did not verify immediately after activation")
    print(paper_root(root) / "deployment-manifest.json")
    print(record["manifest_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

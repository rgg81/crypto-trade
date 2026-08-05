"""Result packets, manifests and the single atomic release."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.cup20.metrics import Fold, daily_returns, fold_sharpes, window_metrics
from crypto_trade.cup20.runner import CandidateRun


def build_packet(
    run: CandidateRun,
    *,
    team_id: str,
    candidate_id: str,
    folds: Sequence[Fold],
    identity: Mapping[str, str],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Write per-cost artifacts and return the summary packet."""
    # Checked before anything else touches the filesystem: an empty run.results would otherwise
    # fall through the loop below (which silently does nothing) and only fail several lines later
    # at `run.results[min(run.results)]` with an opaque `ValueError: min() iterable argument is
    # empty` -- after output_dir has already been created. Raising here first keeps the failure
    # message clear and guarantees a doomed call leaves no directory behind at all.
    if len(run.results) == 0:
        raise ValueError(
            "run.results must not be empty: build_packet requires at least one cost level to report"
        )
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}
    cost_levels: dict[str, dict[str, float]] = {}
    for multiplier, result in sorted(run.results.items()):
        metrics = window_metrics(result)
        cost_levels[str(multiplier)] = metrics.as_dict()
        name = "daily_returns" if multiplier == 1 else f"daily_returns_{multiplier}x"
        path = directory / f"{name}.csv"
        daily_returns(result).to_csv(path, header=["daily_return"])
        artifacts[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    base = run.results[min(run.results)]
    packet = {
        "team_id": team_id,
        "candidate_id": candidate_id,
        "identity": dict(identity),
        "cost_levels": cost_levels,
        "fold_sharpes": fold_sharpes(run.results[2] if 2 in run.results else base, folds),
        "risk_scalar_summary": {
            "count": int(run.risk_scalars.size),
            "median": float(run.risk_scalars.median()) if run.risk_scalars.size else 0.0,
            "minimum": float(run.risk_scalars.min()) if run.risk_scalars.size else 0.0,
            "maximum": float(run.risk_scalars.max()) if run.risk_scalars.size else 0.0,
        },
        "artifact_sha256": artifacts,
    }
    # allow_nan=False: a non-finite metric must fail loudly here rather than silently emitting
    # the non-standard "Infinity" token into a hash-chained, publicly released artifact.
    (directory / "summary.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return packet


def write_manifest(packets: Sequence[Mapping[str, Any]], *, path: str | Path) -> str:
    """Write the release manifest and return its digest."""
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(list(packets), indent=2, sort_keys=True, allow_nan=False) + "\n"
    manifest_path.write_text(body)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def atomic_release(staging_root: str | Path, release_root: str | Path) -> None:
    """Publish a fully built bundle in one rename. There is no partial publication."""
    staging = Path(staging_root)
    release = Path(release_root)
    if release.exists():
        raise FileExistsError(f"release path already exists: {release}")
    if not staging.exists():
        raise FileNotFoundError(f"staging path does not exist: {staging}")
    release.parent.mkdir(parents=True, exist_ok=True)
    staging.rename(release)

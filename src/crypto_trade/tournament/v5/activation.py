"""The single-shot freeze that binds everything a result will later be claimed against.

Activation exists so that no part of the edition can be changed after the evidence starts
accumulating without the change being visible. It records a digest of every artifact a claim
depends on -- the charter, the config, the fifteen lane surfaces, the evaluator, the dependency
lock, the snapshot manifest, the whole-grid preflight, the calibration report, the mutation ledger
and the adversarial review -- and refuses to proceed if any of them is missing or unjustified.

Three refusals are worth stating, because each closes a specific way a prior edition went wrong.

**A number without provenance cannot activate.** Every configured value carries exactly one of
``structural``, ``inherited``, ``calibrated`` or ``derived``, with the artifact hash that justifies
it. The organizer has seen this window's results in six prior editions, so "it looked about right"
is not available as a justification; the ledger makes ex-post fitting mechanically visible.

**Placeholder provenance is not provenance.** The config ships with placeholder tags precisely so
it *cannot* activate until the calibration run has produced real ones. A config that activates on
placeholders would be a config nobody ever calibrated.

**The lane surfaces must match the roster.** Briefs are generated from the same data the roster
invariants are checked against, and activation re-verifies that the tree on disk still agrees. A
mandate that drifted from the code is how a prior edition told teams one thing and measured
another.

Validation is idempotent and re-runnable: it recomputes every digest and compares. A freeze that no
longer validates means something under it changed, which is exactly what it exists to detect.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from crypto_trade.tournament.v5 import contract, journal, lanes, seeds

SCHEMA_VERSION = "top40-v5-activation-v1"

# Every artifact a later claim rests on. Missing any of them is a refusal, not a warning.
REQUIRED_ARTIFACTS = (
    "charter",
    "config",
    "snapshot_manifest",
    "snapshot_preflight",
    "calibration_report",
    "dependency_lock",
    "evaluator",
    "mutation_ledger",
    "adversarial_review",
)


class ActivationError(RuntimeError):
    """The edition cannot be activated, or a freeze no longer describes what is on disk."""


def _digest(path: Path) -> str:
    if not path.is_file():
        raise ActivationError(f"required artifact is missing: {path}")
    body = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            body.update(chunk)
    return body.hexdigest()


def _tree_digest(root: Path) -> str:
    """One digest over a directory's relative paths and contents.

    Paths are included, not just contents, so a file renamed or moved between lanes changes the
    digest. Content-only hashing would let a brief be swapped between two lanes unnoticed.
    """

    if not root.is_dir():
        raise ActivationError(f"required directory is missing: {root}")
    body = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            body.update(path.relative_to(root).as_posix().encode("utf-8"))
            body.update(_digest(path).encode("ascii"))
    return body.hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class ActivationFreeze:
    """What was bound, and what it hashed to."""

    schema_version: str
    artifacts: Mapping[str, str]
    lane_surfaces: Mapping[str, str]
    journal_head: str
    numeric_provenance: Mapping[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "artifacts": dict(sorted(self.artifacts.items())),
            "lane_surfaces": dict(sorted(self.lane_surfaces.items())),
            "journal_head": self.journal_head,
            "numeric_provenance": dict(sorted(self.numeric_provenance.items())),
        }

    def sha256(self) -> str:
        payload = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _check_lanes(tournament_root: Path) -> dict[str, str]:
    """Every lane must exist on disk, carry its four files, and match the roster."""

    lanes.assert_lane_invariants()
    seeds.assert_every_lane_has_a_seed([entry.seed for entry in lanes.LANES])

    surfaces: dict[str, str] = {}
    for lane in lanes.LANES:
        lane_root = tournament_root / "teams" / lane.team_id
        brief = lane_root / "TEAM-BRIEF.md"
        if not brief.is_file():
            raise ActivationError(f"{lane.team_id} has no TEAM-BRIEF.md; scaffold the lanes first")
        if brief.read_text(encoding="utf-8") != lane.brief():
            raise ActivationError(
                f"{lane.team_id}'s brief on disk differs from the roster it is generated from; "
                "a mandate that drifted from the code measures something other than what it says"
            )
        for required in ("SCOUTING-BRIEF.md", "RESEARCH-BRIEF.md", "ACCESS-POLICY.json"):
            if not (lane_root / required).is_file():
                raise ActivationError(f"{lane.team_id} is missing {required}")
        surfaces[lane.team_id] = _tree_digest(lane_root)
    return surfaces


def _check_preflight(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    blocking = report.get("blocking_findings")
    if blocking:
        raise ActivationError(
            f"snapshot preflight reports {blocking} blocking finding(s); every decision boundary "
            "must be executable before a lane starts"
        )
    if not report.get("ok"):
        raise ActivationError("snapshot preflight did not pass")


def freeze(
    artifacts: Mapping[str, str | Path],
    *,
    tournament_root: str | Path,
    journal_path: str | Path,
    destination: str | Path,
) -> ActivationFreeze:
    """Bind the edition. Single-shot: refuses to overwrite an existing freeze.

    The ordering is deliberate -- every refusal happens before anything is written, so a rejected
    activation leaves no partial freeze behind for a later run to mistake for a real one.
    """

    root = Path(tournament_root)
    target = Path(destination)
    if target.exists():
        raise ActivationError(
            f"an activation freeze already exists at {target}; activation is single-shot, and "
            "changes after it require a prospective append-only amendment"
        )

    missing = [name for name in REQUIRED_ARTIFACTS if name not in artifacts]
    if missing:
        raise ActivationError(f"activation is missing required artifacts: {missing}")

    loaded = contract.load_config(artifacts["config"])
    contract.assert_no_placeholder_provenance(loaded)
    provenance = contract.validate_provenance(loaded.raw)
    contract.validate_windows(loaded.raw)

    _check_preflight(Path(artifacts["snapshot_preflight"]))
    surfaces = _check_lanes(root)

    frozen = ActivationFreeze(
        schema_version=SCHEMA_VERSION,
        artifacts={name: _digest(Path(path)) for name, path in sorted(artifacts.items())},
        lane_surfaces=surfaces,
        journal_head=journal.head(journal_path),
        numeric_provenance=provenance,
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(frozen.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    journal.append(
        journal_path,
        "tournament_activated",
        {"freeze_sha256": frozen.sha256(), "artifact_count": len(frozen.artifacts)},
    )
    return frozen


def validate(
    artifacts: Mapping[str, str | Path],
    *,
    tournament_root: str | Path,
    freeze_path: str | Path,
) -> list[str]:
    """Recompute every digest and report what no longer matches.

    Returns findings rather than raising on the first one, because when a freeze breaks the useful
    question is *what* changed, and stopping at the first difference hides the rest.
    """

    path = Path(freeze_path)
    if not path.is_file():
        raise ActivationError(f"no activation freeze at {path}")
    recorded = json.loads(path.read_text(encoding="utf-8"))
    if recorded.get("schema_version") != SCHEMA_VERSION:
        raise ActivationError("activation freeze has an unknown schema version")

    findings: list[str] = []
    for name, expected in sorted(recorded["artifacts"].items()):
        if name not in artifacts:
            findings.append(f"{name}: no longer supplied")
            continue
        try:
            observed = _digest(Path(artifacts[name]))
        except ActivationError:
            findings.append(f"{name}: file is missing")
            continue
        if observed != expected:
            findings.append(f"{name}: content changed since activation")

    root = Path(tournament_root)
    for team_id, expected in sorted(recorded["lane_surfaces"].items()):
        lane_root = root / "teams" / team_id
        if not lane_root.is_dir():
            findings.append(f"{team_id}: lane directory is missing")
            continue
        if _tree_digest(lane_root) != expected:
            findings.append(f"{team_id}: lane surface changed since activation")

    return findings


def assert_activated(freeze_path: str | Path) -> ActivationFreeze:
    """Load a freeze, or refuse to proceed without one."""

    path = Path(freeze_path)
    if not path.is_file():
        raise ActivationError(
            f"the edition is not activated (no freeze at {path}); no lane may start"
        )
    recorded = json.loads(path.read_text(encoding="utf-8"))
    return ActivationFreeze(
        schema_version=recorded["schema_version"],
        artifacts=recorded["artifacts"],
        lane_surfaces=recorded["lane_surfaces"],
        journal_head=recorded["journal_head"],
        numeric_provenance=recorded["numeric_provenance"],
    )


def amend(journal_path: str | Path, *, reason: str, affects: Sequence[str]) -> None:
    """Record a prospective amendment.

    Prospective is the whole constraint: an amendment is made *before* the affected data are
    accessed. No amendment may rewrite evidence, restore a consumed observation, reveal partial
    sealed or holdout state, lower a qualification floor, or let a changed model inherit earlier
    evidence -- and because the journal is hash-chained, one made after the fact is visible as such.
    """

    if not reason.strip():
        raise ActivationError("an amendment must state its reason")
    journal.append(
        journal_path, "tournament_activated", {"amendment": reason, "affects": list(affects)}
    )


__all__ = [
    "REQUIRED_ARTIFACTS",
    "SCHEMA_VERSION",
    "ActivationError",
    "ActivationFreeze",
    "amend",
    "assert_activated",
    "freeze",
    "validate",
]

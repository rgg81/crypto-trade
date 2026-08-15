"""Deployment authority for the CUP-20 winner's forward paper desk.

The desk's whole claim is that its forward record is comparable to the holdout result it follows,
and that claim survives only while every input to the comparison is the one that was scored. This
module is the thing that refuses to run when one of them is not.

Six digests are pinned, and each answers a different way the comparison can go quietly wrong:

* ``strategy_sha256`` -- the winner's candidate bundle, digested by the tournament's own
  :func:`crypto_trade.cup20.trials.candidate_source_digest`. The bundle, never ``strategy.py``
  alone: the two definitions have already produced one false tampering alarm between them.
* ``risk_policy_sha256`` and ``neighbourhood_sha256`` -- the other two declared components the
  selection freeze records for the finalist.
* ``config_sha256`` -- the frozen machine contract, loaded through
  :func:`crypto_trade.cup20.config.load_config` so a config that fails its own validation is drift
  rather than something to notarise.
* ``selection_freeze_sha256`` -- the record that names the winner at all.
* ``evaluator_sha256`` -- the bundle digest of ``src/crypto_trade/cup20``. The desk achieves
  backtest/live parity by re-running the tournament's own evaluator over the whole window; if that
  evaluator changes underneath the desk, the forward record stops being comparable to the holdout
  result *silently*. This digest is what makes it loud.

Nothing here writes. ``src/crypto_trade/cup20`` is hash-bound by
``tournament/cup20/activation-freeze.json`` and the desk only ever reads it.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.cup20.archive import bundle_digest
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.trials import candidate_source_digest, risk_policy_digest

TOURNAMENT = "cup20"
WINNER_TEAM_ID = "team-02"
WINNER_CANDIDATE_ID = "channel-position-ls"
NEIGHBOURHOOD_FILENAME = "neighbourhood.json"

SCHEMA_VERSION = "cup20-desk-authority-v1"

AUTHORITY_FIELDS: tuple[str, ...] = (
    "strategy_sha256",
    "risk_policy_sha256",
    "neighbourhood_sha256",
    "config_sha256",
    "selection_freeze_sha256",
    "evaluator_sha256",
)
"""Every pinned digest, in record order. The verification loop is driven from this tuple so a field
cannot be added to :class:`DeskAuthority` without also being compared."""

# The recorded finalist digests, paired with the desk field each one must agree with. This is the
# cross-check that makes the layer worth having: recomputing a digest and comparing it only against
# a value the desk itself captured proves the desk is self-consistent, not that it is running what
# the tournament froze.
_FREEZE_CROSS_CHECKS: tuple[tuple[str, str], ...] = (
    ("source_sha256", "strategy_sha256"),
    ("risk_policy_sha256", "risk_policy_sha256"),
    ("neighbourhood_sha256", "neighbourhood_sha256"),
)

_HEX_DIGITS = frozenset("0123456789abcdef")


class DeploymentChangedError(RuntimeError):
    """Something the winner's forward record depends on is not what was scored."""


def _require_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or not set(value) <= _HEX_DIGITS:
        raise ValueError(f"{label} must be a SHA-256 digest, got {value!r}")
    return value


def _file_digest(path: Path) -> str:
    """SHA-256 of a file's exact bytes. Propagates ``FileNotFoundError``, which names the path."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class DeskAuthority:
    """The six digests the desk refuses to run without."""

    strategy_sha256: str
    risk_policy_sha256: str
    neighbourhood_sha256: str
    config_sha256: str
    selection_freeze_sha256: str
    evaluator_sha256: str

    def __post_init__(self) -> None:
        for field in AUTHORITY_FIELDS:
            _require_digest(getattr(self, field), field)

    def to_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {
            "schema_version": SCHEMA_VERSION,
            "tournament": TOURNAMENT,
            "team_id": WINNER_TEAM_ID,
            "candidate_id": WINNER_CANDIDATE_ID,
        }
        payload.update({field: getattr(self, field) for field in AUTHORITY_FIELDS})
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> DeskAuthority:
        version = payload.get("schema_version")
        if version is not None and version != SCHEMA_VERSION:
            raise ValueError(f"unknown desk-authority schema_version {version!r}")
        missing = [field for field in AUTHORITY_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"desk authority is missing {', '.join(missing)}")
        return cls(**{field: payload[field] for field in AUTHORITY_FIELDS})

    @classmethod
    def from_json(cls, payload: str | bytes) -> DeskAuthority:
        parsed = json.loads(payload)
        if not isinstance(parsed, Mapping):
            raise ValueError("a serialised desk authority must be a JSON object")
        return cls.from_mapping(parsed)


def repository_root() -> Path:
    """The worktree root containing ``src/crypto_trade``."""
    return Path(__file__).resolve().parents[3]


def _base(root: str | Path | None) -> Path:
    return Path(root).resolve() if root is not None else repository_root()


def tournament_root(root: str | Path | None = None) -> Path:
    return _base(root) / "tournament" / TOURNAMENT


def candidate_root(root: str | Path | None = None) -> Path:
    """The frozen winner's candidate directory -- the desk's only strategy implementation."""
    return tournament_root(root) / "teams" / WINNER_TEAM_ID / "candidates" / WINNER_CANDIDATE_ID


def config_path(root: str | Path | None = None) -> Path:
    return tournament_root(root) / "config.toml"


def selection_freeze_path(root: str | Path | None = None) -> Path:
    return tournament_root(root) / "selection-freeze.json"


def activation_freeze_path(root: str | Path | None = None) -> Path:
    return tournament_root(root) / "activation-freeze.json"


def evaluator_root(root: str | Path | None = None) -> Path:
    """The tournament evaluator the desk replays through. Read-only, always."""
    return _base(root) / "src" / "crypto_trade" / TOURNAMENT


def winner_freeze_entry(root: str | Path | None = None) -> Mapping[str, Any]:
    """The selection freeze's record for the winner, or a refusal naming what is wrong with it."""
    path = selection_freeze_path(root)
    payload = json.loads(path.read_text())
    if not isinstance(payload, Mapping):
        raise ValueError(f"selection freeze {path} must be a JSON object")
    finalists = payload.get("finalists")
    if not isinstance(finalists, list):
        raise ValueError(f"selection freeze {path} has no finalists list")
    matches = [
        entry
        for entry in finalists
        if isinstance(entry, Mapping)
        and entry.get("team_id") == WINNER_TEAM_ID
        and entry.get("candidate_id") == WINNER_CANDIDATE_ID
    ]
    if len(matches) != 1:
        raise DeploymentChangedError(
            f"selection-freeze {path} records {len(matches)} entries for "
            f"{WINNER_TEAM_ID}/{WINNER_CANDIDATE_ID}; the desk deploys exactly one winner"
        )
    return matches[0]


def _cross_check_freeze(digests: Mapping[str, str], root: str | Path | None) -> None:
    """Refuse when the winner's bytes on disk and the digests recorded for it disagree.

    This is the whole point of the layer. A desk that recomputes a digest and compares it only
    against its own captured copy would run happily on a candidate directory that no longer holds
    the source the tournament scored.
    """
    entry = winner_freeze_entry(root)
    path = selection_freeze_path(root)
    mismatches = [
        f"{field} {digests[field]} does not match {recorded} "
        f"{entry.get(recorded)!r} recorded for {WINNER_TEAM_ID}/{WINNER_CANDIDATE_ID} "
        f"in selection-freeze {path}"
        for recorded, field in _FREEZE_CROSS_CHECKS
        if entry.get(recorded) != digests[field]
    ]
    if mismatches:
        raise DeploymentChangedError("CUP-20 desk deployment changed: " + "; ".join(mismatches))


def _cross_check_evaluator(evaluator_sha256: str, root: str | Path | None) -> None:
    """Refuse when the evaluator differs from the one the activation freeze bound.

    ``crypto_trade.cup20.activation.verify_activation`` also checks this, but it needs both
    snapshot trees on disk. The desk must be able to fail closed on evaluator drift on a machine
    that carries only the forward data, so the binding is re-read here directly.
    """
    path = activation_freeze_path(root)
    payload = json.loads(path.read_text())
    if not isinstance(payload, Mapping):
        raise ValueError(f"activation freeze {path} must be a JSON object")
    recorded = payload.get("implementation_sha256")
    if recorded != evaluator_sha256:
        raise DeploymentChangedError(
            f"CUP-20 desk deployment changed: evaluator_sha256 {evaluator_sha256} does not match "
            f"implementation_sha256 {recorded!r} bound by activation-freeze {path}"
        )


def current_desk_authority(root: str | Path | None = None) -> DeskAuthority:
    """Recompute all six digests from disk, cross-checked against the tournament's own records.

    Raises :class:`DeploymentChangedError` when the winner's bytes disagree with the selection
    freeze or the evaluator disagrees with the activation freeze, and ``FileNotFoundError`` when
    something the desk depends on is simply absent.
    """
    candidate = candidate_root(root)
    digests = {
        "strategy_sha256": candidate_source_digest(candidate),
        "risk_policy_sha256": risk_policy_digest(candidate),
        "neighbourhood_sha256": _file_digest(candidate / NEIGHBOURHOOD_FILENAME),
        "config_sha256": load_config(config_path(root)).sha256,
        "selection_freeze_sha256": _file_digest(selection_freeze_path(root)),
        "evaluator_sha256": bundle_digest(evaluator_root(root)),
    }
    _cross_check_freeze(digests, root)
    _cross_check_evaluator(digests["evaluator_sha256"], root)
    return DeskAuthority(**digests)


def verify_desk_authority(expected: DeskAuthority, root: str | Path | None = None) -> DeskAuthority:
    """Recompute the authority and refuse unless it is, field for field, the pinned one.

    Returns the recomputed authority so a caller can use it directly rather than re-reading disk.
    """
    if not isinstance(expected, DeskAuthority):
        raise TypeError("expected must be a DeskAuthority")
    actual = current_desk_authority(root)
    mismatches = [
        f"{field} {getattr(actual, field)} != pinned {getattr(expected, field)}"
        for field in AUTHORITY_FIELDS
        if getattr(actual, field) != getattr(expected, field)
    ]
    if mismatches:
        raise DeploymentChangedError("CUP-20 desk deployment changed: " + "; ".join(mismatches))
    return actual

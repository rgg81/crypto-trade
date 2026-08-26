"""The numeric contract for Top-40 V5, and the provenance every number must carry.

The organizer has seen prior editions' results over the window this edition will use as its
historical observation. That makes "why is this number what it is?" the load-bearing question, and
an unanswerable one is indistinguishable from a number fitted after the fact.

So every configured number carries exactly one provenance tag:

``structural``
    Determined by the venue or by arithmetic -- an 8h cadence, 365-day annualisation, a Monday
    reconstitution. Not a judgement call and not fittable.
``inherited:<edition>``
    Copied unchanged from a prior edition's configuration, which must predate that edition's own
    holdout. Safe because it could not have been chosen with knowledge of the outcome.
``calibrated:<artifact>``
    Produced by the pre-activation calibration harness on development-derived paths, with the
    measured operating characteristic committed *before* the threshold was written.
``derived:<artifact>``
    Read off a measured development distribution, with the measurement artifact named.

There is deliberately no ``judgement`` tag. A number nobody can justify from one of those four
sources does not activate, which is the only mechanism here that makes ex-post fitting visible
rather than merely discouraged.
"""

from __future__ import annotations

import dataclasses
import re
import tomllib
from collections.abc import Mapping
from pathlib import Path

STRUCTURAL = "structural"
_TAG = re.compile(r"^(structural|inherited:[a-z0-9.\-]+|calibrated:[a-z0-9]+|derived:[a-z0-9]+)$")

# Sections whose every numeric leaf must be justified. Sections outside this set are identity and
# path declarations, which are not thresholds and cannot be fitted to an outcome.
JUSTIFIED_SECTIONS = ("universe", "execution", "risk_unit", "selection", "statistics", "sealed")


class ContractError(ValueError):
    """Raised when the numeric contract is incomplete, unjustified, or self-inconsistent."""


def _leaves(node: object, prefix: str = "") -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(node, Mapping):
        for key, value in node.items():
            found.extend(_leaves(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            found.extend(_leaves(value, f"{prefix}[{index}]"))
    else:
        found.append((prefix, node))
    return found


def numeric_keys(config: Mapping[str, object]) -> list[str]:
    """Every dotted key in a justified section whose value is a number."""

    keys: list[str] = []
    for section in JUSTIFIED_SECTIONS:
        if section not in config:
            continue
        for key, value in _leaves(config[section], section):
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                keys.append(key)
    return sorted(keys)


def validate_provenance(config: Mapping[str, object]) -> dict[str, str]:
    """Every justified number carries exactly one well-formed tag, and no tag is orphaned."""

    declared = config.get("provenance")
    if not isinstance(declared, Mapping):
        raise ContractError("config is missing its [provenance] table")
    required = set(numeric_keys(config))
    provided = {str(key) for key in declared}

    missing = sorted(required - provided)
    if missing:
        raise ContractError(
            f"{len(missing)} configured number(s) carry no provenance and cannot be activated: "
            f"{missing[:6]}"
        )
    orphaned = sorted(provided - required)
    if orphaned:
        raise ContractError(
            f"provenance declared for keys that are not justified numbers: {orphaned[:6]}"
        )
    malformed = sorted(key for key, tag in declared.items() if not _TAG.match(str(tag)))
    if malformed:
        raise ContractError(f"provenance tags are malformed: {malformed[:6]}")
    return {str(key): str(value) for key, value in declared.items()}


@dataclasses.dataclass(frozen=True, slots=True)
class LoadedConfig:
    path: Path
    raw: Mapping[str, object]
    provenance: Mapping[str, str]

    def tag(self, key: str) -> str:
        try:
            return self.provenance[key]
        except KeyError as error:
            raise ContractError(f"no provenance recorded for {key}") from error

    def counts_by_source(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for tag in self.provenance.values():
            source = tag.split(":", 1)[0]
            counts[source] = counts.get(source, 0) + 1
        return dict(sorted(counts.items()))


def _require(config: Mapping[str, object], path: tuple[str, ...]) -> object:
    node: object = config
    for part in path:
        if not isinstance(node, Mapping) or part not in node:
            raise ContractError(f"config is missing {'.'.join(path)}")
        node = node[part]
    return node


def validate_windows(config: Mapping[str, object]) -> None:
    """Windows must be ordered, non-overlapping and non-empty.

    V4 aborted at its first trial on a timezone mismatch inside a metric slice, after twenty-five
    activation tests had passed without exercising that path. Parsing every declared boundary here
    costs nothing and moves that class of failure to activation.
    """

    import pandas as pd

    splits = _require(config, ("splits",))
    if not isinstance(splits, Mapping):
        raise ContractError("[splits] must be a table")
    ordered = (
        "warmup_start",
        "development_start",
        "historical_start",
        "historical_end_exclusive",
        "forward_paper_start",
    )
    stamps = []
    for name in ordered:
        if name not in splits:
            raise ContractError(f"[splits] is missing {name}")
        try:
            stamp = pd.Timestamp(str(splits[name]))
        except ValueError as error:
            raise ContractError(f"[splits].{name} is not a timestamp") from error
        stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
        stamps.append((name, stamp))
    for (earlier_name, earlier), (later_name, later) in zip(stamps, stamps[1:], strict=False):
        if earlier >= later:
            raise ContractError(f"[splits].{earlier_name} must precede {later_name}")


PLACEHOLDER = "placeholder"


def assert_no_placeholder_provenance(loaded: LoadedConfig) -> None:
    """Activation gate: a threshold whose justification is still a placeholder is not justified.

    The tags are written while the calibration and derivation artifacts are being produced, so a
    half-finished contract is a normal intermediate state. What must never happen is that state
    reaching activation, where a placeholder would read as a completed justification.
    """

    pending = sorted(
        key for key, tag in loaded.provenance.items() if tag.endswith(f":{PLACEHOLDER}")
    )
    if pending:
        raise ContractError(
            f"{len(pending)} threshold(s) still carry placeholder provenance and cannot be "
            f"activated until their artifact is committed: {pending[:6]}"
        )


def load_config(path: str | Path) -> LoadedConfig:
    """Load and fully validate the numeric contract."""

    resolved = Path(path)
    with resolved.open("rb") as handle:
        raw = tomllib.load(handle)
    validate_windows(raw)
    provenance = validate_provenance(raw)
    return LoadedConfig(path=resolved, raw=raw, provenance=provenance)


__all__ = [
    "JUSTIFIED_SECTIONS",
    "PLACEHOLDER",
    "assert_no_placeholder_provenance",
    "STRUCTURAL",
    "ContractError",
    "LoadedConfig",
    "load_config",
    "numeric_keys",
    "validate_provenance",
    "validate_windows",
]

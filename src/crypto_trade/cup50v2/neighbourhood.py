"""Deterministic, pre-observation CUP-50 v2 parameter neighbourhoods."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from crypto_trade.cup50v2.config import ResearchPolicy, active_policy


@dataclasses.dataclass(frozen=True, slots=True)
class Dimension:
    name: str
    kind: str
    natural_scale: float | None = None

    def validate(self, centre: float) -> None:
        if not self.name or not self.name.replace("_", "").isalnum():
            raise ValueError(f"invalid tunable dimension name {self.name!r}")
        if self.kind not in {"positive", "integer", "fraction", "signed"}:
            raise ValueError(f"unknown dimension kind {self.kind!r}")
        if not math.isfinite(centre):
            raise ValueError(f"dimension {self.name} has a non-finite centre")
        if self.kind in {"positive", "integer"} and centre <= 0:
            raise ValueError(f"{self.kind} dimension {self.name} must be positive")
        if self.kind == "integer" and not float(centre).is_integer():
            raise ValueError(f"integer dimension {self.name} has a non-integer centre")
        if self.kind == "fraction" and not 0.0 < centre < 1.0:
            raise ValueError(f"fraction dimension {self.name} must lie strictly in (0, 1)")
        if self.kind == "signed":
            if self.natural_scale is None:
                raise ValueError(
                    f"signed dimension {self.name} needs a preregistered natural scale"
                )
            if not math.isfinite(self.natural_scale) or self.natural_scale <= 0:
                raise ValueError(f"signed dimension {self.name} has an invalid natural scale")


@dataclasses.dataclass(frozen=True, slots=True)
class Neighbourhood:
    centre: Mapping[str, float]
    dimensions: tuple[Dimension, ...]
    points: tuple[Mapping[str, float], ...]
    centre_index: int


def _value(dimension: Dimension, centre: float, step: int, rules: ResearchPolicy) -> float:
    if step == 0:
        return centre
    if dimension.kind == "positive":
        return centre * (rules.neighbourhood_scale_step**step)
    if dimension.kind == "integer":
        raw = centre * (rules.neighbourhood_scale_step**step)
        # Round away from the centre, not toward it; every declared point is a real perturbation.
        return float(math.ceil(raw) if step > 0 else math.floor(raw))
    if dimension.kind == "fraction":
        logit = math.log(centre / (1.0 - centre)) + step * math.log(rules.neighbourhood_logit_step)
        return 1.0 / (1.0 + math.exp(-logit))
    if dimension.kind == "signed":
        assert dimension.natural_scale is not None
        return centre + step * rules.neighbourhood_signed_step * dimension.natural_scale
    raise AssertionError("validated dimension kind became unreachable")


def _point(
    centre: Mapping[str, float],
    dimensions: Sequence[Dimension],
    steps: Mapping[str, int],
    rules: ResearchPolicy,
) -> dict[str, float]:
    result = {str(name): float(value) for name, value in centre.items()}
    for dimension in dimensions:
        result[dimension.name] = _value(
            dimension, float(centre[dimension.name]), int(steps.get(dimension.name, 0)), rules
        )
    return result


def generate_neighbourhood(
    centre: Mapping[str, float],
    dimensions: Sequence[Dimension],
    *,
    policy: ResearchPolicy | None = None,
) -> Neighbourhood:
    """Generate the one charter-permitted local design for ``k`` tunable dimensions."""
    rules = policy if policy is not None else active_policy().research
    dims = tuple(dimensions)
    if len(dims) > rules.maximum_dimensions:
        raise ValueError(f"CUP-50 v2 allows at most {rules.maximum_dimensions} tunable dimensions")
    names = [dimension.name for dimension in dims]
    if len(names) != len(set(names)):
        raise ValueError("duplicate tunable dimensions")
    missing = set(names) - set(centre)
    if missing:
        raise ValueError(f"centre is missing tunable dimensions: {sorted(missing)}")
    for dimension in dims:
        dimension.validate(float(centre[dimension.name]))

    step_vectors: list[dict[str, int]] = []
    if not dims:
        step_vectors.append({})
    elif len(dims) == 1:
        # The point set is j=-3..3, with the centre first so P0 is unambiguous everywhere.
        step_vectors.append({})
        step_vectors.extend({dims[0].name: step} for step in (-3, -2, -1, 1, 2, 3))
    else:
        # Two probes out on each axis, so a multi-dimensional declaration is examined as far from
        # its centre as a one-dimensional one. CUP-50 probed +/-1 only past two dimensions, which
        # made a wider declaration the cheaper way to look robust.
        step_vectors.append({})
        for dimension in dims:
            step_vectors.extend({dimension.name: step} for step in (-2, -1, 1, 2))

    points = tuple(_point(centre, dims, vector, rules) for vector in step_vectors)
    keys = tuple(sorted(str(name) for name in centre))
    vectors = [tuple(point[name] for name in keys) for point in points]
    if len(vectors) != len(set(vectors)):
        raise ValueError("neighbourhood generation produced duplicate numeric points")
    return Neighbourhood(
        centre={str(name): float(value) for name, value in centre.items()},
        dimensions=dims,
        points=points,
        centre_index=0,
    )


def reject_inert_dimensions(
    neighbourhood: Neighbourhood,
    target_stream_digest: Callable[[Mapping[str, float]], str],
    *,
    policy: ResearchPolicy | None = None,
) -> None:
    """Reject a declared dimension whose low and high probes cannot change the target stream."""
    rules = policy if policy is not None else active_policy().research
    centre_digest = target_stream_digest(neighbourhood.centre)
    for dimension in neighbourhood.dimensions:
        low = _point(neighbourhood.centre, neighbourhood.dimensions, {dimension.name: -1}, rules)
        high = _point(neighbourhood.centre, neighbourhood.dimensions, {dimension.name: 1}, rules)
        if (
            target_stream_digest(low) == centre_digest
            and target_stream_digest(high) == centre_digest
        ):
            raise ValueError(f"tunable dimension {dimension.name} is target-stream inert")


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def freeze_nomination(
    path: str | Path,
    *,
    team_id: str,
    candidate_id: str,
    source_bundle_sha256: str,
    neighbourhood: Neighbourhood,
    trial_id: str | None = None,
    is_score: float | None = None,
    is_point_scores: Sequence[float] | None = None,
    is_regime_scores: Mapping[str, float] | None = None,
    falsifiers: Sequence[Mapping[str, object]] | None = None,
) -> Mapping[str, object]:
    """Atomically bind source, every numeric point, and the research-window evidence.

    The in-sample score travels with the nomination because the qualification question has to be
    answerable while the sealed window is still shut. CUP-50 froze a nomination that carried no
    evidence, and so could only ask who qualified after it already knew who had won.
    """
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"nomination is already frozen: {destination}")
    body: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "team_id": team_id,
        "candidate_id": candidate_id,
        "trial_id": trial_id,
        "source_bundle_sha256": source_bundle_sha256,
        "dimensions": [dataclasses.asdict(dimension) for dimension in neighbourhood.dimensions],
        "centre": dict(neighbourhood.centre),
        "centre_index": neighbourhood.centre_index,
        "points": [dict(point) for point in neighbourhood.points],
        "is_score": None if is_score is None else float(is_score),
        "is_point_scores": [] if is_point_scores is None else [float(v) for v in is_point_scores],
        "is_regime_scores": {} if is_regime_scores is None else {
            str(name): float(value) for name, value in is_regime_scores.items()
        },
        "falsifiers": [] if falsifiers is None else [dict(item) for item in falsifiers],
    }
    record = {**body, "freeze_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return record


def verify_nomination(path: str | Path) -> Mapping[str, object]:
    record = json.loads(Path(path).read_text())
    digest = record.pop("freeze_sha256", None)
    if digest != hashlib.sha256(_canonical(record)).hexdigest():
        raise ValueError("nomination freeze digest mismatch")
    return {**record, "freeze_sha256": digest}

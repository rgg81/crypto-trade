"""Pre-declared parameter neighbourhoods and per-metric median scoring.

A nominated point is the maximum of a noisy surface and is upward-biased by construction. The
median of a neighbourhood declared before evaluation is not.
"""

from __future__ import annotations

import dataclasses
import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path


@dataclasses.dataclass(frozen=True, slots=True)
class NeighbourhoodDeclaration:
    nominee: Mapping[str, float]
    points: tuple[Mapping[str, float], ...]
    coordinates: tuple[str, ...]

    def all_points(self) -> tuple[Mapping[str, float], ...]:
        """The nominee first, then every declared neighbourhood point."""
        return (self.nominee, *self.points)

    def validate(self, minimum_points: int = 7) -> None:
        """Reject a neighbourhood that cannot support a robustness claim."""
        if not self.coordinates:
            raise ValueError("a neighbourhood must declare at least one coordinate")
        required = max(minimum_points, 2 * len(self.coordinates) + 1)
        points = self.all_points()
        if len(points) < required:
            raise ValueError(f"neighbourhood needs at least {required} points, got {len(points)}")
        for point in points:
            unknown = set(point) - set(self.coordinates)
            if unknown:
                raise ValueError(
                    f"neighbourhood point declares unknown coordinates: {sorted(unknown)}"
                )
            missing = set(self.coordinates) - set(point)
            if missing:
                raise ValueError(f"neighbourhood point omits coordinates: {sorted(missing)}")
        for coordinate in self.coordinates:
            centre = float(self.nominee[coordinate])
            values = [float(point[coordinate]) for point in self.points]
            if not any(value > centre for value in values):
                raise ValueError(f"coordinate {coordinate} has no upward variation")
            if not any(value < centre for value in values):
                raise ValueError(f"coordinate {coordinate} has no downward variation")


def median_metrics(per_point: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Median of every metric taken independently across the neighbourhood."""
    if not per_point:
        raise ValueError("median_metrics requires at least one point")
    keys = set(per_point[0])
    for point in per_point[1:]:
        if set(point) != keys:
            raise ValueError("every neighbourhood point must report the same metric keys")
    return {
        key: float(statistics.median(float(point[key]) for point in per_point))
        for key in sorted(keys)
    }


def positive_point_fraction(per_point: Sequence[Mapping[str, float]]) -> float:
    """Fraction of points with positive annualised return AND positive 2x-cost Sharpe."""
    if not per_point:
        raise ValueError("positive_point_fraction requires at least one point")
    passing = sum(
        1
        for point in per_point
        if float(point["annualized_return"]) > 0.0 and float(point["double_cost_sharpe"]) > 0.0
    )
    return passing / len(per_point)


def load_declaration(path: str | Path) -> NeighbourhoodDeclaration:
    """Read a frozen neighbourhood declaration from JSON."""
    payload = json.loads(Path(path).read_text())
    declaration = NeighbourhoodDeclaration(
        nominee={str(k): float(v) for k, v in payload["nominee"].items()},
        points=tuple({str(k): float(v) for k, v in point.items()} for point in payload["points"]),
        coordinates=tuple(str(name) for name in payload["coordinates"]),
    )
    declaration.validate()
    return declaration

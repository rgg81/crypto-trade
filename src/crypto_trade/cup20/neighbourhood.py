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
        # Every point must be a genuinely new sample, not padding: compared on the FULL
        # coordinate vector (not any single coordinate), so a point that only repeats one
        # coordinate while varying another still counts as distinct. Without this, a team can
        # declare N copies of whichever value it wants the median to lean toward -- including the
        # nominee itself -- and clear the max(7, 2k+1) floor on cardinality alone while exploring
        # nothing.
        nominee_vector = tuple(float(self.nominee[coordinate]) for coordinate in self.coordinates)
        seen_vectors: list[tuple[float, ...]] = []
        for point in self.points:
            vector = tuple(float(point[coordinate]) for coordinate in self.coordinates)
            if vector == nominee_vector:
                raise ValueError(f"neighbourhood point duplicates the nominee: {dict(point)}")
            if vector in seen_vectors:
                raise ValueError(
                    f"neighbourhood point duplicates another declared point: {dict(point)}"
                )
            seen_vectors.append(vector)
        for coordinate in self.coordinates:
            centre = float(self.nominee[coordinate])
            # A variation must be material, not an epsilon nudge that satisfies the letter of
            # "strictly above/below" while exploring nothing: at least 5% of the nominee's own
            # magnitude, or -- since 5% of exactly zero is zero, which would make the materiality
            # check vacuous -- any nonzero change at all when the nominee is zero.
            threshold = 0.05 * abs(centre) if centre != 0.0 else 0.0
            values = [float(point[coordinate]) for point in self.points]
            if not any(value > centre and abs(value - centre) >= threshold for value in values):
                raise ValueError(f"coordinate {coordinate} has no material upward variation")
            if not any(value < centre and abs(value - centre) >= threshold for value in values):
                raise ValueError(f"coordinate {coordinate} has no material downward variation")


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
    required_keys = {"annualized_return", "double_cost_sharpe"}
    for point in per_point:
        missing = required_keys - set(point)
        if missing:
            raise ValueError(
                f"positive_point_fraction requires {sorted(required_keys)} on every point; "
                f"a point is missing {sorted(missing)}"
            )
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

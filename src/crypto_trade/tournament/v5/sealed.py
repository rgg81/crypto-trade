"""Sealed confirmation blocks carved out of the development window.

The evaluator cannot skip bars: carried positions, funding accrual and forced exits are
path-dependent, so a strategy must run continuously across the whole development window. The
carve is therefore an operation on the *scoring index*, not on the simulation.

One continuous run produces two disjoint metric views:

* the **visible** index, which is the only thing a team's feedback packet may aggregate;
* the **sealed** index, which only the organizer scores, and which carries the generalization bar.

Days inside a block's purge or embargo margin belong to neither view and are scored by nobody.

Block placement is a deterministic function of the window and four integers, so the schedule is
reproducible from the charter alone. It is also written out explicitly into the frozen config and
hash-bound at activation, and :func:`assert_schedule_matches_rule` checks the two agree — the rule
is the reason, the explicit intervals are the authority.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Sequence

import pandas as pd


class SealedPartitionError(ValueError):
    """Raised when a sealed schedule is internally inconsistent or does not fit its window."""


Interval = tuple[pd.Timestamp, pd.Timestamp]


def _utc(value: object, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(str(value)) if not isinstance(value, pd.Timestamp) else value
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    if pd.isna(timestamp):
        raise SealedPartitionError(f"{label} is not a valid timestamp")
    return timestamp.floor("D")


@dataclasses.dataclass(frozen=True, slots=True)
class SealedPartition:
    """A disjoint, exhaustive split of the development daily index."""

    visible: pd.DatetimeIndex
    sealed: pd.DatetimeIndex
    excluded: pd.DatetimeIndex
    blocks: tuple[Interval, ...]

    def __post_init__(self) -> None:
        if len(self.visible.intersection(self.sealed)) or len(
            self.visible.intersection(self.excluded)
        ):
            raise SealedPartitionError("visible index overlaps a withheld index")
        if len(self.sealed.intersection(self.excluded)):
            raise SealedPartitionError("sealed index overlaps the excluded margin")
        if len(self.sealed) == 0:
            raise SealedPartitionError("a sealed partition must contain at least one sealed day")
        if len(self.visible) == 0:
            raise SealedPartitionError("a sealed partition must leave visible days")

    @property
    def total_days(self) -> int:
        return len(self.visible) + len(self.sealed) + len(self.excluded)

    def summary(self) -> dict[str, object]:
        """Disclosure-safe shape of the split. Carries no returns and no per-day membership."""

        return {
            "block_count": len(self.blocks),
            "visible_days": len(self.visible),
            "sealed_days": len(self.sealed),
            "excluded_days": len(self.excluded),
            "total_days": self.total_days,
        }


def sealed_blocks(
    *,
    start: object,
    end_exclusive: object,
    block_days: int,
    stride: int,
    residues: Sequence[int],
    interleaved_count: int,
    terminal_block: bool,
) -> tuple[Interval, ...]:
    """Generate the sealed schedule from the deterministic placement rule.

    Partition ``[start, end_exclusive)`` into consecutive ``block_days`` blocks indexed from zero;
    seal block ``i`` when ``i % stride`` is in ``residues``, taking the first ``interleaved_count``
    such blocks; then, when ``terminal_block`` is set, seal the final ``block_days`` of the window.

    The terminal block tests temporal generalization, which interleaved blocks structurally cannot:
    interleaving stratifies across regimes but is blind to non-stationarity, and the holdout is a
    forward window. The two measure different things and neither substitutes for the other.
    """

    window_start = _utc(start, "start")
    window_end = _utc(end_exclusive, "end_exclusive")
    if window_end <= window_start:
        raise SealedPartitionError("sealed window must be non-empty")
    if block_days < 1 or stride < 1 or interleaved_count < 0:
        raise SealedPartitionError("block_days and stride must be positive")
    if not residues:
        raise SealedPartitionError("at least one residue is required")
    if any(not 0 <= residue < stride for residue in residues):
        raise SealedPartitionError("every residue must lie in [0, stride)")
    if len(set(residues)) != len(residues):
        raise SealedPartitionError("residues must be unique")

    span = int((window_end - window_start).days)
    grid_blocks = span // block_days
    if grid_blocks < 1:
        raise SealedPartitionError("window is shorter than one block")

    selected: list[Interval] = []
    for index in range(grid_blocks):
        if len(selected) >= interleaved_count:
            break
        if index % stride not in set(residues):
            continue
        block_start = window_start + pd.Timedelta(days=index * block_days)
        selected.append((block_start, block_start + pd.Timedelta(days=block_days)))
    if len(selected) < interleaved_count:
        raise SealedPartitionError(
            f"window fits only {len(selected)} of {interleaved_count} interleaved blocks"
        )

    if terminal_block:
        terminal_start = window_end - pd.Timedelta(days=block_days)
        if selected and terminal_start < selected[-1][1]:
            raise SealedPartitionError("terminal block overlaps the last interleaved block")
        selected.append((terminal_start, window_end))

    return tuple(selected)


def _margin_days(
    blocks: Iterable[Interval], *, purge_days: int, embargo_days: int
) -> pd.DatetimeIndex:
    stamps: list[pd.Timestamp] = []
    for block_start, block_end in blocks:
        for offset in range(1, purge_days + 1):
            stamps.append(block_start - pd.Timedelta(days=offset))
        for offset in range(embargo_days):
            stamps.append(block_end + pd.Timedelta(days=offset))
    if not stamps:
        return pd.DatetimeIndex([], tz="UTC")
    return pd.DatetimeIndex(sorted(set(stamps)), tz="UTC")


def partition(
    daily_index: pd.DatetimeIndex,
    blocks: Sequence[Interval],
    *,
    purge_days: int,
    embargo_days: int,
) -> SealedPartition:
    """Split a development daily index into visible, sealed and withheld-margin days.

    ``purge_days`` before each block removes the immediate run-up from the visible view, and
    ``embargo_days`` after it removes the run-out. The embargo is not about autocorrelation: a
    position decided on a block's last bar persists into the following days, so those days'
    P&L is partly a function of sealed-block decisions and belongs to neither view.
    """

    if purge_days < 0 or embargo_days < 0:
        raise SealedPartitionError("purge and embargo widths cannot be negative")
    if daily_index.tz is None:
        raise SealedPartitionError("development index must be timezone-aware UTC")
    index = pd.DatetimeIndex(daily_index).tz_convert("UTC").floor("D").sort_values().unique()
    index = pd.DatetimeIndex(index, tz="UTC")

    ordered = sorted((_utc(a, "block start"), _utc(b, "block end")) for a, b in blocks)
    for (_, previous_end), (next_start, _) in zip(ordered, ordered[1:], strict=False):
        if next_start < previous_end:
            raise SealedPartitionError("sealed blocks overlap")

    sealed_mask = pd.Series(False, index=index)
    for block_start, block_end in ordered:
        sealed_mask |= (index >= block_start) & (index < block_end)

    margin = _margin_days(ordered, purge_days=purge_days, embargo_days=embargo_days)
    margin_mask = pd.Series(index.isin(margin), index=index) & ~sealed_mask

    return SealedPartition(
        visible=index[~(sealed_mask | margin_mask).to_numpy()],
        sealed=index[sealed_mask.to_numpy()],
        excluded=index[margin_mask.to_numpy()],
        blocks=tuple(ordered),
    )


def assert_schedule_matches_rule(
    declared: Sequence[Interval],
    *,
    start: object,
    end_exclusive: object,
    block_days: int,
    stride: int,
    residues: Sequence[int],
    interleaved_count: int,
    terminal_block: bool,
) -> None:
    """Check the frozen explicit schedule is exactly what the charter's rule generates.

    The explicit intervals in the config are the authority — they are hash-bound at activation —
    but an authority nobody can re-derive is an authority nobody can audit. This is the bridge.
    """

    generated = sealed_blocks(
        start=start,
        end_exclusive=end_exclusive,
        block_days=block_days,
        stride=stride,
        residues=residues,
        interleaved_count=interleaved_count,
        terminal_block=terminal_block,
    )
    normalised = tuple((_utc(a, "declared start"), _utc(b, "declared end")) for a, b in declared)
    if normalised != generated:
        raise SealedPartitionError(
            "declared sealed schedule does not match the charter placement rule"
        )


__all__ = [
    "Interval",
    "SealedPartition",
    "SealedPartitionError",
    "assert_schedule_matches_rule",
    "partition",
    "sealed_blocks",
]

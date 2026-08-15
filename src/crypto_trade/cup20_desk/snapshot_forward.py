"""Roll the CUP-20 universe and its snapshot forward past the sealed window.

The desk's parity argument is that it re-runs the tournament's own evaluator over the tournament's
own snapshot, extended. That only holds while the extension is the tournament's own universe rule
still running -- not a forward-desk universe that resembles it. So the ranking statistic, the
complete-lookback eligibility rule, the 20-in/25-out hysteresis and the mark-coverage criterion are
never restated here. :func:`crypto_trade.cup20.universe.build_membership` computes them, and the
three functions that turn raw bars into its inputs (``daily_quote_volume``, ``eligibility``,
``decision_coverage``) are imported from ``scripts/cup20_build_snapshot.py`` -- the script that
built the sealed membership -- rather than rewritten. A second copy of a rule is the defect class
this module exists to avoid: CUP-20 has already been bitten once by a mean-versus-median divergence
between two copies of the ranking statistic.

**Hysteresis is continuous across the seam, and that is the whole of this module's difficulty.**
``build_membership`` starts each run with an empty incumbency, because it is written to build a
universe from nothing. Run naively from the seam, the first forward boundary would treat every
incumbent as a new entrant: a member sitting at rank 23 -- comfortably inside the ``exit_rank`` of
25 that incumbents survive to -- would be dropped for a newcomer at rank 20, and the desk would
trade a universe the tournament would never have held. Nothing about that failure is loud.

Rather than reach into ``build_membership`` (hash-bound, and untouchable), the incumbency is seeded
through the one input that already expresses it: at the seam boundary, and at the seam boundary
alone, the eligibility frame is replaced by "exactly the symbols the record says were members
here". ``build_membership`` then ranks those twenty against each other, admits all twenty, and
carries them into the next boundary as ``previous`` -- which is precisely the state the sealed run
ended in. The replayed seam rows are discarded; only their effect on incumbency is kept.

Seeding it is not the same as proving it, so the replay is checked against the record and
:class:`SeamDiscontinuityError` is raised if it disagrees, and
``tests/cup20_desk/test_snapshot_forward.py`` rebuilds the ENTIRE sealed window this way -- from
the in-sample membership and the wide bar panel -- and asserts it reproduces
``data/cup20/sealed/membership.parquet`` row for row, ranks and trailing volumes included. That
test is the real statement that this path is the tournament's universe rather than something that
looks like it.

**The candidate panel must be wide.** Membership ranks a symbol against every eligible perpetual,
not against the current members, so a boundary computed from member bars alone would rank the top
twenty against each other and admit whatever it liked. The frames the desk caches are therefore the
FULL Binance USD-M cross-section, and they must reach back a complete ``lookback_days`` window
before the first new boundary or that boundary cannot be scored at all. Both failures are refused
rather than absorbed: :class:`UnscoredBoundaryError` names a boundary that emitted nothing.

**The assembled snapshot narrows, the cache does not.** ``build_forward_snapshot`` scopes every
frame to the symbols membership actually holds, and additionally narrows the mark panel to the
period each symbol is a member for -- extended by one boundary, because the evaluator closes a
departing member's position AT the boundary it stops being eligible and demands a mark for a held
symbol there. Narrowing can only ever remove marks no evaluation consults; a mistake in it is a
loud ``missing current mark`` raise from the evaluator, never a changed number.
"""

from __future__ import annotations

import dataclasses
import functools
import importlib.util
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.cup20.config import load_config

# `_slice` and `_write` are the tournament's own snapshot writer: `_slice` sorts, trims and refuses
# a duplicate key, `_write` lays out the five parquet files and the manifest `load_snapshot`
# verifies. Reimplementing either would put a second definition of the snapshot's byte layout next
# to the loader that checks it. Imported, never modified -- `crypto_trade/cup20/` is hash-bound.
from crypto_trade.cup20.snapshot import Snapshot, load_snapshot
from crypto_trade.cup20.snapshot import _slice as canonical_slice
from crypto_trade.cup20.snapshot import _write as write_snapshot_files
from crypto_trade.cup20.universe import (
    build_membership,
    unmarkable_member_boundaries,
    weekly_reconstitution_times,
)
from crypto_trade.cup20_desk.authority import config_path, repository_root
from crypto_trade.cup20_desk.live_data import (
    BARS,
    CONTRACT_METADATA,
    FUNDING,
    MARK_PRICES,
    MEMBERSHIP,
    SNAPSHOT_FRAMES,
    conform_frame,
    empty_frame,
    frame_schema,
)
from crypto_trade.tournament.snapshot import _utc as utc

BUILD_SCRIPT = Path("scripts") / "cup20_build_snapshot.py"
"""The script that built the sealed snapshot. Its ``daily_quote_volume`` / ``eligibility`` /
``decision_coverage`` are the acquisition's own input preparation and are imported from it."""

CACHE_DIRNAME = "cache"
SNAPSHOT_DIRNAME = "snapshot"


class SeamDiscontinuityError(RuntimeError):
    """The forward universe does not continue the recorded one."""


class UnscoredBoundaryError(RuntimeError):
    """A reconstitution boundary emitted no members, so the previous week silently stayed in force.

    Almost always the wide bar panel not reaching a complete lookback window before the boundary:
    with no symbol carrying a full history, nothing is a candidate, and ``build_membership``
    correctly declines to score a universe it cannot form. Silence there would leave stale members
    in place for a week and mark them against prices nobody checked, so it is an error.
    """


class MarkCoverageError(RuntimeError):
    """The assembled snapshot holds a member the evaluator could not mark."""


class SourceConflictError(RuntimeError):
    """Two snapshot sources report different values for the same row."""


# ------------------------------------------------------------------------------------------------
# the tournament's own universe inputs
# ------------------------------------------------------------------------------------------------


@functools.cache
def acquisition_helpers(root: str | Path | None = None) -> ModuleType:
    """Load ``scripts/cup20_build_snapshot.py`` as a module, by path.

    By path rather than by ``import scripts.cup20_build_snapshot`` because that spelling only works
    when the process happens to be running from the repository root, and a desk started from a cron
    entry or a systemd unit is not. The path is derived from this package's own location, which is
    the same anchor :mod:`crypto_trade.cup20_desk.authority` uses.
    """
    path = (Path(root).resolve() if root is not None else repository_root()) / BUILD_SCRIPT
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; the desk reuses its universe-input preparation rather than "
            "keeping a second copy of it"
        )
    spec = importlib.util.spec_from_file_location("cup20_build_snapshot", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclasses.dataclass(frozen=True, slots=True)
class UniversePolicy:
    """The frozen ``[universe]`` contract, as ``build_membership`` takes it."""

    lookback_days: int
    target_size: int
    entry_rank: int
    exit_rank: int
    minimum_scored_members: int
    reconstitution_weekday: int

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> UniversePolicy:
        return cls(
            lookback_days=int(raw["lookback_days"]),
            target_size=int(raw["target_size"]),
            entry_rank=int(raw["entry_rank"]),
            exit_rank=int(raw["exit_rank"]),
            minimum_scored_members=int(raw["minimum_scored_members"]),
            reconstitution_weekday=int(raw["reconstitution_weekday"]),
        )


def tournament_universe_policy(config: str | Path | None = None) -> UniversePolicy:
    """The activated contract's universe policy, validated by ``load_config`` on the way through."""
    return UniversePolicy.from_mapping(load_config(config or config_path()).raw["universe"])


def _policy(universe: UniversePolicy | Mapping[str, Any] | None) -> UniversePolicy:
    if universe is None:
        return tournament_universe_policy()
    if isinstance(universe, UniversePolicy):
        return universe
    return UniversePolicy.from_mapping(universe)


# ------------------------------------------------------------------------------------------------
# rolling the universe forward
# ------------------------------------------------------------------------------------------------


def extend_membership(
    membership: pd.DataFrame,
    *,
    bars: pd.DataFrame,
    mark_prices: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    through: object,
    universe: UniversePolicy | Mapping[str, Any] | None = None,
    root: str | Path | None = None,
) -> pd.DataFrame:
    """Continue the weekly reconstitution past ``membership``, carrying its incumbency forward.

    ``membership`` is the recorded universe -- in production the in-sample and sealed frames
    concatenated. Its final boundary is the seam, and the returned frame is that record unchanged
    plus one row per member at every weekly boundary in ``(seam, through]``.

    ``bars``, ``mark_prices`` and ``contract_metadata`` must be the WIDE cross-section, not the
    members': ranking twenty incumbents against each other would admit whatever it liked. The bar
    panel must also reach a complete ``lookback_days`` before the first new boundary.
    """
    policy = _policy(universe)
    helpers = acquisition_helpers(root)
    recorded = conform_frame(MEMBERSHIP, membership)
    if recorded.empty:
        raise SeamDiscontinuityError("cannot extend an empty membership: there is no incumbency")
    seam = pd.Timestamp(recorded["reconstitution_time"].max())
    horizon = utc(through)
    if horizon < seam:
        raise ValueError(f"through {horizon} precedes the recorded seam {seam}")

    volume = helpers.daily_quote_volume(bars)
    eligible = helpers.eligibility(volume, contract_metadata)
    fillable, markable = helpers.decision_coverage(bars, mark_prices)
    boundaries = weekly_reconstitution_times(
        seam,
        horizon.normalize() + pd.Timedelta(days=1),
        weekday=policy.reconstitution_weekday,
    )
    if not boundaries or boundaries[0] != seam:
        raise SeamDiscontinuityError(
            f"the recorded seam {seam} is not a reconstitution boundary of the weekly schedule; "
            "the forward universe would restart rather than continue"
        )

    members = frozenset(recorded.loc[recorded["reconstitution_time"] == seam, "symbol"])
    built = build_membership(
        volume,
        eligible=_seed_incumbency(eligible, seam, members),
        fillable=fillable,
        markable=markable,
        reconstitution_times=boundaries,
        lookback_days=policy.lookback_days,
        target_size=policy.target_size,
        entry_rank=policy.entry_rank,
        exit_rank=policy.exit_rank,
        minimum_scored_members=policy.minimum_scored_members,
    )
    replayed = frozenset(built.loc[built["reconstitution_time"] == seam, "symbol"])
    if replayed != members:
        raise SeamDiscontinuityError(
            f"replaying the seam {seam} produced {sorted(replayed ^ members)} differently from the "
            "recorded membership, so the incumbency carried into the forward window would be "
            "wrong; the panel probably does not cover every recorded member"
        )

    forward = built.loc[built["reconstitution_time"] > seam]
    unscored = sorted(set(boundaries[1:]) - set(forward["reconstitution_time"]))
    if unscored:
        raise UnscoredBoundaryError(
            f"{len(unscored)} reconstitution boundaries emitted no members, e.g. {unscored[:3]}; "
            f"the bar panel must cover a complete {policy.lookback_days}-day lookback before "
            f"{unscored[0]} and reach every candidate symbol"
        )
    combined = pd.concat([recorded, forward], ignore_index=True)
    schema = frame_schema(MEMBERSHIP)
    return conform_frame(MEMBERSHIP, combined.sort_values(list(schema.order), kind="stable"))


def _seed_incumbency(
    eligibility: pd.DataFrame, seam: pd.Timestamp, members: frozenset[str]
) -> pd.DataFrame:
    """Make exactly ``members`` eligible at the seam, and change nothing at any other boundary.

    ``build_membership`` reads eligibility with "the last row at or before this boundary", and the
    rows are calendar days, so rewriting the seam's own day reaches the seam boundary and nothing
    else -- the next boundary is a week later and reads its own row.

    At the seam the twenty recorded members are then the entire candidate set, so they rank 1..20,
    all clear ``entry_rank``, and all twenty are admitted. Their replayed ranks are meaningless and
    are discarded; ``previous`` is what is being set.
    """
    index = pd.DatetimeIndex(eligibility.index)
    day = seam.normalize()
    if day not in index:
        raise SeamDiscontinuityError(
            f"the eligibility panel has no row for the seam day {day}, so the recorded incumbency "
            "cannot be carried across it"
        )
    values = eligibility.to_numpy(dtype=bool).copy()
    position = int(index.get_loc(day))
    values[position] = eligibility.columns.isin(list(members))
    return pd.DataFrame(values, index=eligibility.index, columns=eligibility.columns)


# ------------------------------------------------------------------------------------------------
# narrowing the mark panel
# ------------------------------------------------------------------------------------------------


def narrow_mark_panel(mark_prices: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    """Keep the marks an evaluation can consult: each symbol's membership period, plus its exit.

    The evaluator reads a mark at exactly two kinds of ``(symbol, decision time)``: one where the
    symbol is eligible, and one where a position in it is still open. The second is what makes this
    the membership period *inclusive of the following boundary* rather than the half-open interval
    the membership rule itself uses -- a member that leaves the universe at ``t`` is closed AT
    ``t``, when it is already ineligible, and ``evaluate_targets`` raises ``missing current mark for
    held symbols`` if that mark is absent. A tidy half-open narrowing removes exactly the mark the
    exit needs.

    Everything else is unreadable by construction: no position can exist in a symbol before it is
    first admitted, and none survives past the boundary that closes it, so a mark outside these
    intervals cannot be looked up by any evaluation of any strategy.
    """
    panel = conform_frame(MARK_PRICES, mark_prices)
    if panel.empty or membership.empty:
        return conform_frame(MARK_PRICES, panel.iloc[0:0])
    grid = membership.pivot(
        index="reconstitution_time", columns="symbol", values="liquidity_rank"
    ).notna()
    boundaries = pd.DatetimeIndex(grid.index)
    times = pd.DatetimeIndex(panel["mark_time"])
    column = grid.columns.get_indexer(panel["symbol"])
    row = boundaries.searchsorted(times, side="right") - 1
    values = grid.to_numpy(dtype=bool)

    held = _member_at(values, row, column)
    carried = _member_at(values, row - 1, column)
    at_boundary = boundaries.get_indexer(times) >= 0
    retained = held | (at_boundary & carried)
    return conform_frame(MARK_PRICES, panel.loc[retained])


def _member_at(values: np.ndarray, row: np.ndarray, column: np.ndarray) -> np.ndarray:
    """``values[row, column]`` with out-of-range coordinates reading False rather than wrapping.

    ``-1`` is a legitimate result of both ``searchsorted`` (a time before the first boundary) and
    ``get_indexer`` (a symbol that is never a member), and numpy would happily read it as the LAST
    row or column -- silently retaining a mark on the strength of somebody else's membership.
    """
    inside = (row >= 0) & (column >= 0)
    result = np.zeros(len(row), dtype=bool)
    result[inside] = values[row[inside], column[inside]]
    return result


# ------------------------------------------------------------------------------------------------
# assembling the forward snapshot
# ------------------------------------------------------------------------------------------------


def build_forward_snapshot(
    root: str | Path,
    through: object,
    *,
    cache_root: str | Path | None = None,
    out_root: str | Path | None = None,
    is_root: str | Path | None = None,
    sealed_root: str | Path | None = None,
    universe: UniversePolicy | Mapping[str, Any] | None = None,
    config: str | Path | None = None,
    repo: str | Path | None = None,
) -> Snapshot:
    """Assemble one snapshot spanning the record and the forward cache, up to ``through``.

    The two recorded snapshots are loaded by the tournament's own ``load_snapshot``, so their
    manifests are verified before a single row is used, and the result is written and then read
    back through the same loader -- the returned :class:`Snapshot` therefore carries a manifest
    digest the desk's healthcheck can bind.

    Warm-up history is kept. The in-sample snapshot ships every bar it holds for a symbol, back to
    its listing rather than to ``IS_START``, because the charter defines warm-up that way and the
    strategies' formation windows read it; truncating to the decision window would quietly shorten
    them. The DECISION grid still starts at ``IS_START``, which is the caller's business.
    """
    paths = _snapshot_roots(config, is_root, sealed_root, repo)
    recorded = [load_snapshot(paths[0]), load_snapshot(paths[1])]
    cache = _read_cache(Path(cache_root) if cache_root else Path(root) / CACHE_DIRNAME)

    wide = {
        name: _stack(
            name,
            [getattr(snapshot, name) for snapshot in recorded] + [cache[name]],
            later_wins=name == CONTRACT_METADATA,
        )
        for name in SNAPSHOT_FRAMES
    }
    membership = extend_membership(
        _stack(MEMBERSHIP, [snapshot.membership for snapshot in recorded]),
        bars=wide[BARS],
        mark_prices=wide[MARK_PRICES],
        contract_metadata=wide[CONTRACT_METADATA],
        through=through,
        universe=universe,
        root=repo,
    )

    members = set(membership["symbol"])
    horizon = utc(through)
    end = horizon + pd.Timedelta(nanoseconds=1)
    frames = {
        BARS: _members_only(wide[BARS], members),
        FUNDING: _members_only(wide[FUNDING], members),
        MARK_PRICES: narrow_mark_panel(_members_only(wide[MARK_PRICES], members), membership),
        MEMBERSHIP: membership,
        CONTRACT_METADATA: _members_only(wide[CONTRACT_METADATA], members),
    }
    sliced = {name: canonical_slice(name, frame, None, end) for name, frame in frames.items()}
    _require_markable_members(sliced, root=repo)

    destination = Path(out_root) if out_root else Path(root) / SNAPSHOT_DIRNAME
    window = (pd.Timestamp(sliced[BARS]["open_time"].min()), horizon)
    write_snapshot_files(sliced, destination, window=window)
    return load_snapshot(destination)


def _snapshot_roots(
    config: str | Path | None,
    is_root: str | Path | None,
    sealed_root: str | Path | None,
    repo: str | Path | None,
) -> tuple[Path, Path]:
    """The recorded snapshot roots, taken from the frozen contract unless overridden."""
    if is_root is not None and sealed_root is not None:
        return Path(is_root), Path(sealed_root)
    base = Path(repo).resolve() if repo is not None else repository_root()
    declared = load_config(config or config_path(repo)).raw["data"]
    return (
        Path(is_root) if is_root is not None else base / str(declared["is_root"]),
        Path(sealed_root) if sealed_root is not None else base / str(declared["sealed_root"]),
    )


def _read_cache(cache_root: Path) -> dict[str, pd.DataFrame]:
    """The desk's own forward frames, or empties before the first tick has written any."""
    return {
        name: conform_frame(name, pd.read_parquet(cache_root / f"{name}.parquet"))
        if (cache_root / f"{name}.parquet").is_file()
        else empty_frame(name)
        for name in SNAPSHOT_FRAMES
    }


def _stack(name: str, frames: Sequence[pd.DataFrame], *, later_wins: bool = False) -> pd.DataFrame:
    """Concatenate sources under one key, refusing a disagreement unless one is declared to win.

    ``later_wins`` is set for ``contract_metadata`` alone, and for a specific reason: the in-sample
    snapshot's copy is deliberately CENSORED -- ``crypto_trade.cup20.snapshot`` scrubs post-cutoff
    delivery dates and archive markers out of it so a team could not read future universe
    composition off it -- so it disagrees with the sealed copy by design, for symbols that delisted
    after the cutoff. That disagreement is a known, intended property of the artifacts rather than
    a source conflict, and the later source is the truthful one. Every other frame is keyed on
    disjoint time windows and must agree exactly.
    """
    schema = frame_schema(name)
    key = list(schema.key)
    populated = [conform_frame(name, frame) for frame in frames if len(frame)]
    if not populated:
        return empty_frame(name)
    stacked = pd.concat(populated, ignore_index=True)
    if later_wins:
        stacked = stacked.drop_duplicates(key, keep="last")
    else:
        stacked = stacked.drop_duplicates()
        clashing = stacked.loc[stacked.duplicated(key, keep=False)]
        if not clashing.empty:
            raise SourceConflictError(
                f"snapshot sources disagree about {name} {schema.key}="
                f"{tuple(clashing.iloc[0][field] for field in key)}; both values are preserved and "
                "nothing was assembled"
            )
    return conform_frame(name, stacked.sort_values(list(schema.order), kind="stable"))


def _members_only(frame: pd.DataFrame, members: set[str]) -> pd.DataFrame:
    return frame.loc[frame["symbol"].isin(members)]


def _require_markable_members(
    frames: Mapping[str, pd.DataFrame], *, root: str | Path | None
) -> None:
    """Re-derive the mark-coverage guarantee on the frames about to be written.

    The post-condition half of the rule, run on the assembled artifact rather than trusted from the
    criterion that produced it -- exactly as ``scripts/cup20_build_snapshot.py`` runs it on the
    sealed membership. It is what makes the narrowing above safe to do at all: if narrowing ever
    removed a mark a member needs, this names the ``(boundary, symbol)`` pairs instead of letting
    the evaluator discover them mid-run.
    """
    helpers = acquisition_helpers(root)
    fillable, markable = helpers.decision_coverage(frames[BARS], frames[MARK_PRICES])
    unmarkable = unmarkable_member_boundaries(
        frames[MEMBERSHIP], fillable=fillable, markable=markable
    )
    if unmarkable:
        raise MarkCoverageError(
            f"the assembled snapshot holds {len(unmarkable)} (boundary, symbol) pairs the "
            f"evaluator cannot mark, e.g. {unmarkable[:5]}"
        )

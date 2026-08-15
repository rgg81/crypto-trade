"""The forward universe is tested against the universe the tournament actually built.

The headline test rebuilds the WHOLE sealed window with :func:`extend_membership` -- starting from
``data/cup20/is/membership.parquet`` and the wide acquisition bar panel, exactly as a forward tick
starts from the record and its own cache -- and asserts it reproduces
``data/cup20/sealed/membership.parquet`` row for row, ranks and trailing volumes included. A
forward path that merely resembles the tournament's universe passes every structural check and
still trades a different book; only reproduction rules that out.

That test needs the WIDE panel (``data/cup20/acquisition``), because a boundary ranks its members
against every eligible perpetual and not against each other. That directory is organiser-only and
gitignored, so the test skips when it is absent -- and the synthetic fixture below carries the
seam, hysteresis, coverage and narrowing cases on its own, so nothing is left unproven when it does.

The synthetic universe is built so the hysteresis question has exactly one right answer: at the
first boundary after the seam, one incumbent sits at rank 23 -- inside the ``exit_rank`` of 25 that
incumbents survive to, outside the ``entry_rank`` of 20 a newcomer needs -- and a non-member sits at
rank 20. Carrying incumbency across the seam retains the incumbent and refuses the newcomer.
Restarting it does the exact opposite, so the two outcomes cannot be confused.
"""

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20.snapshot import _write as write_snapshot_files
from crypto_trade.cup20.snapshot import load_snapshot
from crypto_trade.cup20.universe import unmarkable_member_boundaries
from crypto_trade.cup20_desk import snapshot_forward
from crypto_trade.cup20_desk.live_data import (
    BARS,
    CONTRACT_METADATA,
    FUNDING,
    MARK_PRICES,
    MEMBERSHIP,
    SNAPSHOT_DATASETS,
    conform_frame,
    empty_frame,
)
from crypto_trade.cup20_desk.snapshot_forward import (
    MarkCoverageError,
    SeamDiscontinuityError,
    SourceConflictError,
    UniversePolicy,
    UnscoredBoundaryError,
    _stack,
    build_forward_snapshot,
    extend_membership,
    narrow_mark_panel,
    tournament_universe_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
IS_ROOT = REPO_ROOT / "data" / "cup20" / "is"
SEALED_ROOT = REPO_ROOT / "data" / "cup20" / "sealed"
ACQUISITION_ROOT = REPO_ROOT / "data" / "cup20" / "acquisition"
MODULE_PATH = REPO_ROOT / "src" / "crypto_trade" / "cup20_desk" / "snapshot_forward.py"

IS_END = pd.Timestamp("2024-08-01T00:00:00Z")
SEALED_END = pd.Timestamp("2026-08-01T00:00:00Z")
LAST_RECORDED_BAR = pd.Timestamp("2026-07-31T16:00:00Z")

requires_acquisition = pytest.mark.skipif(
    not (ACQUISITION_ROOT / "bars.parquet").is_file(),
    reason="the wide acquisition panel (organiser-only, gitignored) is not on this machine",
)

# --------------------------------------------------------------------------------------------
# a synthetic universe with one deliberate rank-23 incumbent
# --------------------------------------------------------------------------------------------

POLICY = UniversePolicy(
    lookback_days=10,
    target_size=20,
    entry_rank=20,
    exit_rank=25,
    minimum_scored_members=8,
    reconstitution_weekday=0,
)

SYMBOLS = tuple(f"S{index:02d}USDT" for index in range(30))

# S19 is the incumbent that falls to rank 23 after the seam; S20 is the newcomer that reaches rank
# 20. Every other name keeps a rank that decides nothing.
RANKS = {symbol: index + 1 for index, symbol in enumerate(SYMBOLS[:19])}
RANKS.update({"S20USDT": 20, "S21USDT": 21, "S22USDT": 22, "S19USDT": 23})
RANKS.update({symbol: 24 + index for index, symbol in enumerate(SYMBOLS[23:])})

INCUMBENT = "S19USDT"
NEWCOMER = "S20USDT"
SEAM_MEMBERS = tuple(SYMBOLS[:20])

PANEL_START = pd.Timestamp("2026-01-05T00:00:00Z")
SEAM = PANEL_START + pd.Timedelta(days=28)
THROUGH = SEAM + pd.Timedelta(days=21)
PANEL_END = SEAM + pd.Timedelta(days=28)
BOUNDARIES = tuple(SEAM + pd.Timedelta(days=7 * step) for step in range(1, 4))


def _grid(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="8h", tz="UTC", inclusive="left")


def _bars(times: Sequence[pd.Timestamp], symbols: Sequence[str] = SYMBOLS) -> pd.DataFrame:
    rows = [
        {
            "open_time": time,
            "symbol": symbol,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1.0,
            "close_time": time + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
            # Daily quote volume is the sum of three bars, so ranking follows RANKS exactly.
            "quote_volume": (100 - RANKS[symbol]) * 1_000_000.0 / 3.0,
            "trade_count": 10,
            "taker_buy_volume": 0.5,
            "taker_buy_quote_volume": 50.0,
        }
        for time in times
        for symbol in symbols
    ]
    return conform_frame(BARS, pd.DataFrame(rows))


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return conform_frame(
        MARK_PRICES,
        pd.DataFrame(
            {
                "mark_time": bars["open_time"],
                "symbol": bars["symbol"],
                "mark_price": 100.0,
            }
        ),
    )


def _metadata(symbols: Sequence[str] = SYMBOLS) -> pd.DataFrame:
    return conform_frame(
        CONTRACT_METADATA,
        pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "contract_type": "PERPETUAL",
                    "quote_asset": "USDT",
                    "margin_asset": "USDT",
                    "is_crypto": True,
                    "onboard_date": PANEL_START,
                    "delivery_date": pd.Timestamp("2100-12-25T08:00:00Z"),
                    "underlying_type": "COIN",
                    "metadata_source": "current_exchangeInfo",
                }
                for symbol in symbols
            ]
        ),
    )


def _recorded_membership(members: Sequence[str] = SEAM_MEMBERS) -> pd.DataFrame:
    """One recorded boundary: the seam, holding exactly ``members``.

    A single boundary is enough. Hysteresis reads only the last one, which is precisely why the
    seam is the whole of the problem.
    """
    return conform_frame(
        MEMBERSHIP,
        pd.DataFrame(
            [
                {
                    "reconstitution_time": SEAM,
                    "symbol": symbol,
                    "liquidity_rank": index + 1,
                    "trailing_quote_volume": (100 - index) * 1_000_000.0,
                }
                for index, symbol in enumerate(members)
            ]
        ),
    )


@pytest.fixture
def panel() -> dict[str, pd.DataFrame]:
    bars = _bars(_grid(PANEL_START, PANEL_END))
    return {BARS: bars, MARK_PRICES: _marks(bars), CONTRACT_METADATA: _metadata()}


def _extend(panel: Mapping[str, pd.DataFrame], **overrides: object) -> pd.DataFrame:
    arguments: dict[str, object] = {
        "bars": panel[BARS],
        "mark_prices": panel[MARK_PRICES],
        "contract_metadata": panel[CONTRACT_METADATA],
        "through": THROUGH,
        "universe": POLICY,
    }
    arguments.update(overrides)
    membership = arguments.pop("membership", None)
    return extend_membership(
        _recorded_membership() if membership is None else membership, **arguments
    )


def _members_at(membership: pd.DataFrame, boundary: pd.Timestamp) -> list[str]:
    rows = membership.loc[membership["reconstitution_time"] == boundary]
    return list(rows.sort_values("liquidity_rank")["symbol"])


# --------------------------------------------------------------------------------------------
# the seam
# --------------------------------------------------------------------------------------------


def test_an_incumbent_at_rank_23_across_the_seam_is_retained(panel: dict[str, pd.DataFrame]):
    """The whole reason this module exists.

    ``S19USDT`` ranks 23 at the first boundary after the seam. As an incumbent it survives to
    ``exit_rank`` 25 and keeps its seat; ``S20USDT`` at rank 20 would have taken that seat had the
    forward run started with an empty incumbency. Both halves are asserted, because a run that
    dropped the incumbent AND refused the newcomer would be wrong in a different way.
    """
    membership = _extend(panel)
    members = _members_at(membership, BOUNDARIES[0])
    assert len(members) == POLICY.target_size
    assert INCUMBENT in members
    assert NEWCOMER not in members


def test_incumbency_stays_carried_at_every_later_boundary(panel: dict[str, pd.DataFrame]):
    """The carry is not a one-boundary patch: the seat holds for as long as the rank does."""
    membership = _extend(panel)
    for boundary in BOUNDARIES:
        members = _members_at(membership, boundary)
        assert INCUMBENT in members, boundary
        assert NEWCOMER not in members, boundary


def test_the_recorded_membership_is_returned_unchanged(panel: dict[str, pd.DataFrame]):
    """The extension appends. It never rewrites the record it continues."""
    recorded = _recorded_membership()
    membership = _extend(panel)
    kept = membership.loc[membership["reconstitution_time"] <= SEAM].reset_index(drop=True)
    expected = recorded.sort_values(["reconstitution_time", "symbol"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(kept, expected)


def test_membership_continues_without_a_gap(panel: dict[str, pd.DataFrame]):
    membership = _extend(panel)
    boundaries = sorted(membership["reconstitution_time"].unique())
    assert boundaries == [SEAM, *BOUNDARIES]
    counts = membership.groupby("reconstitution_time").size()
    assert set(counts) == {POLICY.target_size}


def test_the_replayed_seam_rows_are_not_emitted(panel: dict[str, pd.DataFrame]):
    """Replaying the seam sets incumbency; its ranks are an artifact and must not be published."""
    membership = _extend(panel)
    seam_rows = membership.loc[membership["reconstitution_time"] == SEAM]
    assert list(seam_rows["liquidity_rank"]) == list(range(1, 21))
    assert list(seam_rows.sort_values("liquidity_rank")["symbol"]) == list(SEAM_MEMBERS)


def test_the_seam_replay_must_reproduce_the_recorded_membership(panel: dict[str, pd.DataFrame]):
    """A record naming a symbol the panel cannot see is a discontinuity, not something to absorb.

    Seeding incumbency from the record and then never checking that the record could be reproduced
    would let a panel missing one member carry nineteen incumbents forward silently -- and the
    twentieth seat would go to whoever ranked next.
    """
    recorded = _recorded_membership((*SEAM_MEMBERS[:19], "GHOSTUSDT"))
    with pytest.raises(SeamDiscontinuityError, match="GHOSTUSDT"):
        _extend(panel, membership=recorded)


def test_a_seam_off_the_weekly_schedule_is_refused(panel: dict[str, pd.DataFrame]):
    recorded = _recorded_membership()
    recorded["reconstitution_time"] = SEAM + pd.Timedelta(days=1)
    with pytest.raises(SeamDiscontinuityError, match="weekly schedule"):
        _extend(panel, membership=conform_frame(MEMBERSHIP, recorded))


def test_an_empty_record_has_no_incumbency_to_carry(panel: dict[str, pd.DataFrame]):
    with pytest.raises(SeamDiscontinuityError, match="incumbency"):
        _extend(panel, membership=empty_frame(MEMBERSHIP))


def test_a_horizon_before_the_seam_is_refused(panel: dict[str, pd.DataFrame]):
    with pytest.raises(ValueError, match="precedes the recorded seam"):
        _extend(panel, through=SEAM - pd.Timedelta(days=1))


def test_a_horizon_at_the_seam_extends_nothing(panel: dict[str, pd.DataFrame]):
    membership = _extend(panel, through=SEAM)
    assert sorted(membership["reconstitution_time"].unique()) == [SEAM]


# --------------------------------------------------------------------------------------------
# boundaries the panel cannot score
# --------------------------------------------------------------------------------------------


def _with_history_gap(panel: Mapping[str, pd.DataFrame], day: pd.Timestamp) -> dict:
    """Remove one day of bars for all but five symbols, so their lookback stops being complete."""
    bars = panel[BARS]
    doomed = bars["symbol"].isin(SYMBOLS[5:])
    inside = (bars["open_time"] >= day) & (bars["open_time"] < day + pd.Timedelta(days=1))
    kept = conform_frame(BARS, bars.loc[~(doomed & inside)])
    return {**panel, BARS: kept}


def test_a_boundary_that_cannot_be_scored_is_refused(panel: dict[str, pd.DataFrame]):
    """A boundary emitting nothing leaves last week's members in force. That must be loud.

    ``build_membership`` is right to decline -- with fewer than ``minimum_scored_members``
    candidates there is no universe to form -- but silence downstream would leave stale members
    priced against a week nobody checked coverage over.
    """
    damaged = _with_history_gap(panel, SEAM + pd.Timedelta(days=8))
    with pytest.raises(UnscoredBoundaryError, match="emitted no members"):
        _extend(damaged)


def test_a_panel_that_starts_too_late_scores_nothing(panel: dict[str, pd.DataFrame]):
    """The wide panel must reach a complete lookback before the first new boundary."""
    late = {
        name: frame.loc[frame[frame.columns[0]] >= SEAM] if name != CONTRACT_METADATA else frame
        for name, frame in panel.items()
    }
    with pytest.raises((SeamDiscontinuityError, UnscoredBoundaryError)):
        _extend(late)


# --------------------------------------------------------------------------------------------
# mark coverage
# --------------------------------------------------------------------------------------------


UNMARKED = "S05USDT"
UNMARKED_AT = BOUNDARIES[0] + pd.Timedelta(hours=8)


def _without_one_mark(panel: Mapping[str, pd.DataFrame]) -> dict:
    marks = panel[MARK_PRICES]
    hole = (marks["symbol"] == UNMARKED) & (marks["mark_time"] == UNMARKED_AT)
    return {**panel, MARK_PRICES: conform_frame(MARK_PRICES, marks.loc[~hole])}


def test_a_member_the_evaluator_cannot_mark_is_refused(panel: dict[str, pd.DataFrame]):
    """Mark coverage is checked over the membership period, so one missing hour costs the seat."""
    membership = _extend(_without_one_mark(panel))
    members = _members_at(membership, BOUNDARIES[0])
    assert UNMARKED not in members
    assert NEWCOMER in members, "the vacated seat goes to the highest-ranked admissible entrant"
    assert len(members) == POLICY.target_size


def test_the_forward_membership_is_markable_everywhere_it_is_held(panel: dict[str, pd.DataFrame]):
    """The tournament's own post-condition, re-derived on the extended membership."""
    damaged = _without_one_mark(panel)
    membership = _extend(damaged)
    helpers = _acquisition_helpers()
    fillable, markable = helpers.decision_coverage(damaged[BARS], damaged[MARK_PRICES])
    assert unmarkable_member_boundaries(membership, fillable=fillable, markable=markable) == []


def _acquisition_helpers():
    from crypto_trade.cup20_desk.snapshot_forward import acquisition_helpers

    return acquisition_helpers()


# --------------------------------------------------------------------------------------------
# narrowing the mark panel
# --------------------------------------------------------------------------------------------


def test_the_mark_panel_is_narrowed_to_membership(panel: dict[str, pd.DataFrame]):
    membership = _extend(panel)
    narrowed = narrow_mark_panel(panel[MARK_PRICES], membership)
    assert len(narrowed) < len(panel[MARK_PRICES])
    grid = membership.pivot(
        index="reconstitution_time", columns="symbol", values="liquidity_rank"
    ).notna()
    boundaries = pd.DatetimeIndex(grid.index)
    for symbol, time in zip(narrowed["symbol"], narrowed["mark_time"], strict=True):
        position = int(boundaries.searchsorted(time, side="right")) - 1
        assert position >= 0
        held = bool(grid.iloc[position].get(symbol, False))
        exiting = time == boundaries[position] and bool(grid.iloc[position - 1].get(symbol, False))
        assert held or exiting, (symbol, time)


def test_the_narrowed_mark_panel_keeps_the_exit_boundary(panel: dict[str, pd.DataFrame]):
    """A departing member is CLOSED at the boundary it stops being eligible, and needs a mark there.

    ``evaluate_targets`` raises ``missing current mark for held symbols`` on exactly this row. The
    half-open membership period -- the tidy reading, and the wrong one -- removes it.
    """
    damaged = _without_one_mark(panel)
    membership = _extend(damaged)
    assert UNMARKED not in _members_at(membership, BOUNDARIES[0])
    narrowed = narrow_mark_panel(damaged[MARK_PRICES], membership)
    retained = set(zip(narrowed["symbol"], narrowed["mark_time"], strict=True))
    assert (UNMARKED, BOUNDARIES[0]) in retained
    assert (UNMARKED, BOUNDARIES[0] + pd.Timedelta(hours=16)) not in retained


def test_narrowing_never_removes_a_mark_a_member_needs(panel: dict[str, pd.DataFrame]):
    membership = _extend(_without_one_mark(panel))
    damaged = _without_one_mark(panel)
    narrowed = narrow_mark_panel(damaged[MARK_PRICES], membership)
    helpers = _acquisition_helpers()
    fillable, markable = helpers.decision_coverage(damaged[BARS], narrowed)
    assert unmarkable_member_boundaries(membership, fillable=fillable, markable=markable) == []


def test_narrowing_a_panel_with_no_membership_keeps_nothing(panel: dict[str, pd.DataFrame]):
    narrowed = narrow_mark_panel(panel[MARK_PRICES], empty_frame(MEMBERSHIP))
    assert narrowed.empty
    assert tuple(narrowed.columns) == tuple(panel[MARK_PRICES].columns)


# --------------------------------------------------------------------------------------------
# assembling a snapshot
# --------------------------------------------------------------------------------------------


def _write_recorded(root: Path, panel: Mapping[str, pd.DataFrame], until: pd.Timestamp) -> Path:
    """A synthetic recorded snapshot: everything strictly before ``until``."""
    frames = {
        BARS: conform_frame(BARS, panel[BARS].loc[panel[BARS]["open_time"] < until]),
        FUNDING: empty_frame(FUNDING),
        MARK_PRICES: conform_frame(
            MARK_PRICES, panel[MARK_PRICES].loc[panel[MARK_PRICES]["mark_time"] < until]
        ),
        MEMBERSHIP: _recorded_membership(),
        CONTRACT_METADATA: panel[CONTRACT_METADATA],
    }
    write_snapshot_files(frames, root, window=("", until))
    return root


def _write_cache(root: Path, panel: Mapping[str, pd.DataFrame], since: pd.Timestamp) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    bars = conform_frame(BARS, panel[BARS].loc[panel[BARS]["open_time"] >= since])
    marks = conform_frame(
        MARK_PRICES, panel[MARK_PRICES].loc[panel[MARK_PRICES]["mark_time"] >= since]
    )
    bars.to_parquet(root / f"{BARS}.parquet", index=False)
    marks.to_parquet(root / f"{MARK_PRICES}.parquet", index=False)
    return root


@pytest.fixture
def desk(tmp_path: Path, panel: dict[str, pd.DataFrame]) -> dict[str, Path]:
    seam_bar = SEAM + pd.Timedelta(hours=8)
    recorded = _write_recorded(tmp_path / "is", panel, seam_bar)
    empty = tmp_path / "sealed"
    write_snapshot_files(
        {name: empty_frame(name) for name in SNAPSHOT_DATASETS}, empty, window=("", seam_bar)
    )
    _write_cache(tmp_path / "desk" / "cache", panel, seam_bar)
    return {"root": tmp_path / "desk", "is": recorded, "sealed": empty}


def _assemble(desk: Mapping[str, Path], **overrides: object) -> object:
    return build_forward_snapshot(
        desk["root"],
        overrides.pop("through", THROUGH),
        is_root=desk["is"],
        sealed_root=desk["sealed"],
        universe=POLICY,
        **overrides,
    )


def test_the_assembled_snapshot_loads_through_the_tournaments_own_loader(desk: dict[str, Path]):
    snapshot = _assemble(desk)
    reloaded = load_snapshot(desk["root"] / "snapshot")
    assert reloaded.manifest_sha256 == snapshot.manifest_sha256
    for name in SNAPSHOT_DATASETS:
        pd.testing.assert_frame_equal(getattr(reloaded, name), getattr(snapshot, name))


def test_the_assembled_snapshot_spans_the_record_and_the_forward_cache(desk: dict[str, Path]):
    snapshot = _assemble(desk)
    assert snapshot.bars["open_time"].min() == PANEL_START
    assert snapshot.bars["open_time"].max() == THROUGH
    assert sorted(snapshot.membership["reconstitution_time"].unique()) == [SEAM, *BOUNDARIES]


def test_the_assembled_snapshot_holds_only_symbols_membership_holds(desk: dict[str, Path]):
    snapshot = _assemble(desk)
    members = set(snapshot.membership["symbol"])
    assert members < set(SYMBOLS), "the fixture must have non-members to narrow away"
    for name in (BARS, MARK_PRICES, CONTRACT_METADATA):
        assert set(getattr(snapshot, name)["symbol"]) <= members


def test_the_assembled_snapshot_can_mark_every_member_it_holds(desk: dict[str, Path]):
    snapshot = _assemble(desk)
    helpers = _acquisition_helpers()
    fillable, markable = helpers.decision_coverage(snapshot.bars, snapshot.mark_prices)
    assert (
        unmarkable_member_boundaries(snapshot.membership, fillable=fillable, markable=markable)
        == []
    )


def test_an_over_narrowed_mark_panel_is_refused(desk: dict[str, Path], monkeypatch):
    """The post-condition is what makes narrowing safe to do at all, so it is proved to fire.

    Narrowing is the one step in assembly that removes rows the evaluator might want, and its own
    correctness argument cannot be the thing that checks it. A narrowing that took too much is
    injected here; the assembly must refuse to write a snapshot whose members it cannot mark rather
    than let ``evaluate_targets`` discover them mid-run, months in.
    """
    monkeypatch.setattr(
        snapshot_forward, "narrow_mark_panel", lambda marks, membership: marks.iloc[0:0]
    )
    with pytest.raises(MarkCoverageError, match="cannot mark"):
        _assemble(desk)


def test_the_assembled_snapshot_stops_at_the_requested_boundary(desk: dict[str, Path]):
    snapshot = _assemble(desk, through=BOUNDARIES[0])
    assert snapshot.bars["open_time"].max() == BOUNDARIES[0]
    assert sorted(snapshot.membership["reconstitution_time"].unique()) == [SEAM, BOUNDARIES[0]]


def test_sources_that_disagree_about_a_row_are_refused():
    frame = _bars([PANEL_START])
    revised = frame.copy()
    revised.loc[revised.index[0], "close"] = 1.0
    with pytest.raises(SourceConflictError, match="bars"):
        _stack(BARS, [frame, conform_frame(BARS, revised)])


def test_identical_rows_from_two_sources_are_not_a_conflict():
    frame = _bars([PANEL_START])
    stacked = _stack(BARS, [frame, frame])
    pd.testing.assert_frame_equal(stacked, frame)


def test_the_later_source_wins_for_contract_metadata():
    """The in-sample copy is censored, so it disagrees with the sealed one by design."""
    censored = _metadata(("S00USDT",))
    truthful = conform_frame(
        CONTRACT_METADATA, censored.assign(metadata_source="archive_inference")
    )
    stacked = _stack(CONTRACT_METADATA, [censored, truthful], later_wins=True)
    assert list(stacked["metadata_source"]) == ["archive_inference"]


# --------------------------------------------------------------------------------------------
# against the universe the tournament actually built
# --------------------------------------------------------------------------------------------


def _acquisition_panel(since: pd.Timestamp) -> dict[str, pd.DataFrame]:
    bars = pd.read_parquet(ACQUISITION_ROOT / "bars.parquet")
    marks = pd.read_parquet(ACQUISITION_ROOT / "mark_prices.parquet")
    return {
        BARS: bars.loc[(bars["open_time"] >= since) & (bars["open_time"] < SEALED_END)],
        MARK_PRICES: marks.loc[(marks["mark_time"] >= since) & (marks["mark_time"] < SEALED_END)],
        CONTRACT_METADATA: pd.read_parquet(ACQUISITION_ROOT / "contract_metadata.parquet"),
    }


@requires_acquisition
def test_extend_membership_reproduces_the_sealed_window_exactly():
    """The end-to-end proof: the forward path rebuilds the tournament's own sealed universe.

    In-sample membership in, the wide bar panel in, and ``data/cup20/sealed/membership.parquet``
    out -- 104 boundaries, 2080 rows, every liquidity rank and every trailing quote volume. This is
    the same call a forward tick makes, over a window whose right answer is already on disk.
    """
    recorded = pd.read_parquet(IS_ROOT / "membership.parquet")
    sealed = pd.read_parquet(SEALED_ROOT / "membership.parquet")
    policy = tournament_universe_policy()
    seam = pd.Timestamp(recorded["reconstitution_time"].max())
    panel = _acquisition_panel(seam - pd.Timedelta(days=policy.lookback_days))

    extended = extend_membership(
        recorded,
        bars=panel[BARS],
        mark_prices=panel[MARK_PRICES],
        contract_metadata=panel[CONTRACT_METADATA],
        through=pd.Timestamp(sealed["reconstitution_time"].max()),
    )
    forward = extended.loc[extended["reconstitution_time"] >= IS_END].reset_index(drop=True)
    pd.testing.assert_frame_equal(forward, conform_frame(MEMBERSHIP, sealed))


@requires_acquisition
def test_the_reproduction_keeps_the_in_sample_record_untouched():
    recorded = pd.read_parquet(IS_ROOT / "membership.parquet")
    sealed = pd.read_parquet(SEALED_ROOT / "membership.parquet")
    policy = tournament_universe_policy()
    seam = pd.Timestamp(recorded["reconstitution_time"].max())
    panel = _acquisition_panel(seam - pd.Timedelta(days=policy.lookback_days))
    extended = extend_membership(
        recorded,
        bars=panel[BARS],
        mark_prices=panel[MARK_PRICES],
        contract_metadata=panel[CONTRACT_METADATA],
        through=pd.Timestamp(sealed["reconstitution_time"].max()),
    )
    kept = extended.loc[extended["reconstitution_time"] < IS_END].reset_index(drop=True)
    pd.testing.assert_frame_equal(kept, conform_frame(MEMBERSHIP, recorded))


@pytest.fixture
def recorded_desk(tmp_path: Path) -> Path:
    """A desk whose cache carries only the wide contract metadata the split snapshots lack.

    The IS and sealed snapshots scope ``contract_metadata`` to the symbols visible in sample, so
    four of the twenty members at the final sealed boundary have no metadata row in either. A real
    desk fetches its own from ``exchangeInfo`` every tick; here it comes from the acquisition.
    """
    cache = tmp_path / "cache"
    cache.mkdir(parents=True)
    metadata = pd.read_parquet(ACQUISITION_ROOT / "contract_metadata.parquet")
    conform_frame(CONTRACT_METADATA, metadata).to_parquet(
        cache / f"{CONTRACT_METADATA}.parquet", index=False
    )
    return tmp_path


@requires_acquisition
def test_the_recorded_window_assembles_into_one_loadable_snapshot(recorded_desk: Path):
    """Assembly over the real record, with no forward bars yet -- the desk's first tick.

    The membership must come out as the two recorded frames concatenated, unchanged: with no
    boundary past the seam there is nothing to extend, and anything else would mean the assembly
    rewrites what it was given.
    """
    snapshot = build_forward_snapshot(recorded_desk, LAST_RECORDED_BAR)
    recorded = pd.concat(
        [
            pd.read_parquet(IS_ROOT / "membership.parquet"),
            pd.read_parquet(SEALED_ROOT / "membership.parquet"),
        ],
        ignore_index=True,
    )
    pd.testing.assert_frame_equal(
        snapshot.membership, conform_frame(MEMBERSHIP, recorded), check_like=False
    )
    assert snapshot.bars["open_time"].max() == LAST_RECORDED_BAR
    assert set(snapshot.mark_prices["symbol"]) <= set(snapshot.membership["symbol"])


@requires_acquisition
def test_the_real_assembly_keeps_every_mark_a_departing_member_needs(recorded_desk: Path):
    """Over 311 real boundaries and 78 real members, every force-exit still has its mark.

    Narrowing can only remove rows, so the failure mode is an evaluator raise rather than a wrong
    number -- but the raise would land mid-tick, months in. This is the same check
    ``evaluate_targets`` makes for held symbols, made in advance.
    """
    snapshot = build_forward_snapshot(recorded_desk, LAST_RECORDED_BAR)
    grid = snapshot.membership.pivot(
        index="reconstitution_time", columns="symbol", values="liquidity_rank"
    ).notna()
    boundaries = pd.DatetimeIndex(grid.index)
    opens = set(zip(snapshot.bars["symbol"], snapshot.bars["open_time"], strict=True))
    marks = snapshot.mark_prices
    marked = set(zip(marks["symbol"], marks["mark_time"], strict=True))
    unmarked_exits = [
        (boundaries[position], symbol)
        for position in range(1, len(boundaries))
        for symbol in grid.columns[
            grid.iloc[position - 1].to_numpy() & ~grid.iloc[position].to_numpy()
        ]
        if (symbol, boundaries[position]) in opens and (symbol, boundaries[position]) not in marked
    ]
    assert unmarked_exits == []


@requires_acquisition
def test_the_real_assembly_narrows_the_mark_panel(recorded_desk: Path):
    snapshot = build_forward_snapshot(recorded_desk, LAST_RECORDED_BAR)
    recorded = len(pd.read_parquet(IS_ROOT / "mark_prices.parquet")) + len(
        pd.read_parquet(SEALED_ROOT / "mark_prices.parquet")
    )
    assert 0 < len(snapshot.mark_prices) < recorded


# --------------------------------------------------------------------------------------------
# reuse, by inspection
# --------------------------------------------------------------------------------------------


REUSED_RULES = (
    "build_membership",
    "weekly_reconstitution_times",
    "unmarkable_member_boundaries",
    "daily_quote_volume",
    "eligibility",
    "decision_coverage",
)


def test_the_module_defines_no_second_copy_of_a_universe_rule():
    """The instruction this module was written under, made executable.

    CUP-20 has already been bitten by two copies of the ranking statistic disagreeing about mean
    versus median. A function here NAMED after one of the tournament's rules is the shape that
    defect takes, so it is refused by inspection rather than by review.
    """
    tree = ast.parse(MODULE_PATH.read_text())
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    assert defined & set(REUSED_RULES) == set()


def test_the_universe_rules_are_imported_from_the_tournament():
    tree = ast.parse(MODULE_PATH.read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("crypto_trade.cup20")
        for alias in node.names
    }
    assert {"build_membership", "weekly_reconstitution_times", "unmarkable_member_boundaries"} <= (
        imported
    )


def test_the_universe_policy_is_the_frozen_contract():
    policy = tournament_universe_policy()
    assert dataclasses_as_tuple(policy) == (180, 20, 20, 25, 8, 0)


def dataclasses_as_tuple(policy: UniversePolicy) -> tuple[int, ...]:
    return (
        policy.lookback_days,
        policy.target_size,
        policy.entry_rank,
        policy.exit_rank,
        policy.minimum_scored_members,
        policy.reconstitution_weekday,
    )


def test_the_extension_never_reaches_the_network():
    """Paper-only, and offline: the universe is computed from frames the caller supplies."""
    source = MODULE_PATH.read_text()
    for token in ("httpx", "requests", "fapi", "urlopen", "PublicMarketDataClient"):
        assert token not in source, token


def test_activation_freeze_still_verifies(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    verify_activation("tournament/cup20/activation-freeze.json")

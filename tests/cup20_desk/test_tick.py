"""The paper tick, tested against the evaluator it claims to be running.

Two things have to be true for the desk's record to mean anything, and they are tested differently.

**The numbers are the tournament's.** ``test_the_forward_rows_are_the_evaluators_own_rows`` builds
an independent invocation of :func:`crypto_trade.cup20.runner.run_candidate` -- same snapshot, same
grid, same seed, same frozen ``[execution]``/``[risk_unit]`` tables, same declared risk policy --
and asserts the tick's forward rows are that result's rows, column for column and bit for bit. What
that establishes is precise and worth stating plainly: the desk SELECTS and LABELS the evaluator's
output and does not compute any of it. It cannot establish that the evaluator is right, and it is
not a comparison against the sealed holdout observation, which is a different window (the holdout
runs the grid from ``SEALED_START`` on the sealed snapshot alone; the desk runs from ``IS_START``,
so the equity path, the trailing volatility and therefore the risk unit differ by construction).

**The record does not move.** Every tick replays boundaries it has already published, so the second
tick's rows must equal the first's exactly -- that is what makes the append-invariance abort a
signal rather than noise, and it is why the evaluator's terminal row, which force-exits the book at
the window's end, is discarded rather than recorded. The synthetic tests tick three times over a
fixture built so a rebalance boundary, a hold boundary and the phase change all fall where they can
be pointed at; the ``parity``-marked tests do the same thing over the real record, where one
full-window replay costs about seven minutes.

The synthetic universe is 24 perpetuals on a deterministic price surface: enough names for a
20-member universe, enough history for the frozen strategy's 252-bar channel to form, and enough
bar volume that ``max_bar_participation`` never throttles a fill.
"""

import ast
import dataclasses
import hashlib
import json
import math
import re
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.harness import (
    load_candidate_risk_policy,
    load_team_module,
    strategy_from_module,
)
from crypto_trade.cup20.runner import decision_grid, evaluator_config, run_candidate
from crypto_trade.cup20.snapshot import _write as write_snapshot_files
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.cup20.trials import ENTRYPOINT
from crypto_trade.cup20.universe import build_membership, weekly_reconstitution_times
from crypto_trade.cup20_desk import tick as tick_module
from crypto_trade.cup20_desk.authority import (
    AUTHORITY_FIELDS,
    DeploymentChangedError,
    DeskAuthority,
    candidate_root,
    current_desk_authority,
)
from crypto_trade.cup20_desk.live_data import (
    BARS,
    CONTRACT_METADATA,
    FUNDING,
    MARK_PRICES,
    MEMBERSHIP,
    AppendInvarianceError,
    conform_frame,
)
from crypto_trade.cup20_desk.snapshot_forward import acquisition_helpers
from crypto_trade.cup20_desk.tick import (
    BRIDGE,
    FORWARD_RETURN_SCHEMA,
    OFFICIAL,
    DeskPinDriftError,
    TickWindowError,
    first_official_boundary,
    persist_tick,
    run_tick,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "crypto_trade" / "cup20_desk" / "tick.py"
CONFIG_PATH = REPO_ROOT / "tournament" / "cup20" / "config.toml"
IS_ROOT = REPO_ROOT / "data" / "cup20" / "is"
SEALED_ROOT = REPO_ROOT / "data" / "cup20" / "sealed"
ACQUISITION_ROOT = REPO_ROOT / "data" / "cup20" / "acquisition"

requires_acquisition = pytest.mark.skipif(
    not (ACQUISITION_ROOT / "bars.parquet").is_file(),
    reason="the wide acquisition panel (organiser-only, gitignored) is not on this machine",
)

# --------------------------------------------------------------------------------------------
# a synthetic universe the frozen strategy can actually trade
# --------------------------------------------------------------------------------------------

SYMBOLS = tuple(f"S{index:02d}USDT" for index in range(24))
INTERVAL = pd.Timedelta(hours=8)

PANEL_START = pd.Timestamp("2025-04-07T00:00:00Z")
"""A Monday, 294 days before the seam. Three windows have to fit inside it before the first tick:
the universe's 180-day liquidity lookback, the strategy's 252-bar (84-day) channel, and -- the
binding one -- the risk unit's 90-day trailing volatility, which returns a scalar of exactly 1.0
until 270 return rows exist. A book executed at 1.0x sits at exactly the 1.0 gross cap, so the
first adverse drift trips the evaluator's central exposure reduction and every hold boundary
sprouts fills. With the full lookback the scalar settles below 1, gross sits well inside the cap,
and a hold boundary holds -- which is what the real record does at gross 0.30."""

IS_SPLIT = pd.Timestamp("2026-01-05T00:00:00Z")
SEAM = pd.Timestamp("2026-01-26T00:00:00Z")
"""The fixture's stand-in for ``SEALED_END``. Recorded data stops strictly before it, so -- as in
the real record -- the last RECORDED reconstitution (2026-01-19) is a week earlier than the seam."""

LAST_CACHED_BAR = pd.Timestamp("2026-02-09T16:00:00Z")

BRIDGE_TICK = SEAM + INTERVAL
"""2026-01-26 08:00: the desk's first tick. A hold boundary -- the strategy rebalances on Mondays
at 00:00 -- so the rebalance it must mark to market happened eight hours earlier."""

OFFICIAL_TICK = pd.Timestamp("2026-02-02T00:00:00Z")
"""The first Monday strictly after ``BRIDGE_TICK``: official observation opens here, and it is also
a rebalance boundary."""

AFTER_OFFICIAL_TICK = OFFICIAL_TICK + INTERVAL
"""The first tick that can publish an ``official`` return row: the row at ``OFFICIAL_TICK`` is that
tick's terminal row, and terminal rows are discarded until they settle."""


def _steps(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="8h", tz="UTC", inclusive="left")


def _price(symbol: int, step: int) -> float:
    """A deterministic surface with a real trailing range, distinct in phase for every symbol.

    The channel score the frozen strategy ranks on is ``(close - min low) / (max high - min low)``
    over 252 bars, so a flat panel would make every score undefined and the book empty. The phase
    offset per symbol is what makes the ordering -- and therefore the long and short sleeves --
    unambiguous.
    """
    angle = 2.0 * math.pi * (step / 61.0 + symbol / len(SYMBOLS))
    return 100.0 * (1.0 + 0.25 * math.sin(angle) + 0.05 * math.cos(3.0 * angle))


def _bars(times: Sequence[pd.Timestamp]) -> pd.DataFrame:
    origin = int(PANEL_START.value // INTERVAL.value)
    rows = []
    for time in times:
        step = int(time.value // INTERVAL.value) - origin
        for index, symbol in enumerate(SYMBOLS):
            open_price = _price(index, step)
            close_price = _price(index, step + 1)
            rows.append(
                {
                    "open_time": time,
                    "symbol": symbol,
                    "open": open_price,
                    "high": max(open_price, close_price) * 1.005,
                    "low": min(open_price, close_price) * 0.995,
                    "close": close_price,
                    "volume": 1_000.0,
                    "close_time": time + INTERVAL - pd.Timedelta(milliseconds=1),
                    # Ranked on the median of the daily sum, so a constant per symbol fixes the
                    # membership: the twenty highest are the twenty members at every boundary.
                    "quote_volume": (100 - index) * 1_000_000.0,
                    "trade_count": 100,
                    "taker_buy_volume": 500.0,
                    "taker_buy_quote_volume": 50_000.0,
                }
            )
    return conform_frame(BARS, pd.DataFrame(rows))


def _marks(bars: pd.DataFrame) -> pd.DataFrame:
    return conform_frame(
        MARK_PRICES,
        pd.DataFrame(
            {
                "mark_time": bars["open_time"],
                "symbol": bars["symbol"],
                "mark_price": bars["open"],
            }
        ),
    )


def _funding(bars: pd.DataFrame) -> pd.DataFrame:
    return conform_frame(
        FUNDING,
        pd.DataFrame(
            {
                "funding_time": bars["open_time"],
                "symbol": bars["symbol"],
                "funding_rate": 0.0001,
                "mark_price": bars["open"],
                "mark_time": bars["open_time"],
                "settlement_time": bars["open_time"],
                "funding_interval_hours": 8.0,
            }
        ),
    )


def _metadata() -> pd.DataFrame:
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
                for symbol in SYMBOLS
            ]
        ),
    )


def _recorded_membership(bars: pd.DataFrame, marks: pd.DataFrame, metadata: pd.DataFrame):
    """The record's own universe, built by the tournament's ``build_membership``.

    Constructed the way ``scripts/cup20_build_snapshot.py`` constructs the sealed one rather than
    hand-written, so the incumbency the desk carries across the seam is an incumbency the
    tournament's rule actually produced.
    """
    helpers = acquisition_helpers()
    policy = load_config(CONFIG_PATH).raw["universe"]
    volume = helpers.daily_quote_volume(bars)
    fillable, markable = helpers.decision_coverage(bars, marks)
    times = weekly_reconstitution_times(
        PANEL_START, SEAM, weekday=int(policy["reconstitution_weekday"])
    )
    return build_membership(
        volume,
        eligible=helpers.eligibility(volume, metadata),
        fillable=fillable,
        markable=markable,
        reconstitution_times=times,
        lookback_days=int(policy["lookback_days"]),
        target_size=int(policy["target_size"]),
        entry_rank=int(policy["entry_rank"]),
        exit_rank=int(policy["exit_rank"]),
        minimum_scored_members=int(policy["minimum_scored_members"]),
    )


@dataclasses.dataclass(frozen=True)
class Desk:
    """A desk directory plus the keyword arguments that point a tick at its fixture data."""

    root: Path
    is_root: Path
    sealed_root: Path

    @property
    def kwargs(self) -> dict[str, object]:
        return {
            "desk_root": self.root,
            "seam": SEAM,
            "is_root": self.is_root,
            "sealed_root": self.sealed_root,
        }


@pytest.fixture(scope="module")
def panel() -> dict[str, pd.DataFrame]:
    bars = _bars(_steps(PANEL_START, LAST_CACHED_BAR + INTERVAL))
    marks = _marks(bars)
    metadata = _metadata()
    return {
        BARS: bars,
        MARK_PRICES: marks,
        FUNDING: _funding(bars),
        CONTRACT_METADATA: metadata,
        MEMBERSHIP: conform_frame(MEMBERSHIP, _recorded_membership(bars, marks, metadata)),
    }


def _build_desk(root: Path, panel: Mapping[str, pd.DataFrame]) -> Desk:
    """Two recorded snapshots and a forward cache, split exactly as the real ones are."""
    root.mkdir(parents=True, exist_ok=True)
    windows = {
        "is": (PANEL_START, IS_SPLIT),
        "sealed": (IS_SPLIT, SEAM),
    }
    roots = {}
    for name, (start, end) in windows.items():
        frames = {
            frame: _between(panel[frame], frame, start, end)
            for frame in (BARS, FUNDING, MARK_PRICES, MEMBERSHIP)
        }
        frames[CONTRACT_METADATA] = panel[CONTRACT_METADATA]
        destination = root / name
        write_snapshot_files(frames, destination, window=(start, end))
        roots[name] = destination
    cache = root / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    for frame in (BARS, FUNDING, MARK_PRICES):
        forward = _between(panel[frame], frame, SEAM, LAST_CACHED_BAR + INTERVAL)
        forward.to_parquet(cache / f"{frame}.parquet", index=False)
    panel[CONTRACT_METADATA].to_parquet(cache / f"{CONTRACT_METADATA}.parquet", index=False)
    return Desk(root=root, is_root=roots["is"], sealed_root=roots["sealed"])


_TIME_COLUMN = {
    BARS: "open_time",
    FUNDING: "funding_time",
    MARK_PRICES: "mark_time",
    MEMBERSHIP: "reconstitution_time",
}


def _between(frame: pd.DataFrame, name: str, start: pd.Timestamp, end: pd.Timestamp):
    column = _TIME_COLUMN[name]
    inside = (frame[column] >= start) & (frame[column] < end)
    return conform_frame(name, frame.loc[inside])


@pytest.fixture
def desk(tmp_path: Path, panel: dict[str, pd.DataFrame]) -> Desk:
    return _build_desk(tmp_path / "desk", panel)


@pytest.fixture(scope="module")
def bridged(tmp_path_factory, panel: dict[str, pd.DataFrame], authority: DeskAuthority) -> Desk:
    """A desk that has ticked once, built once. Every full-window replay costs real seconds."""
    desk = _build_desk(tmp_path_factory.mktemp("bridged") / "desk", panel)
    _tick_and_persist(desk, BRIDGE_TICK, authority)
    return desk


@pytest.fixture
def forked(tmp_path: Path, bridged: Desk) -> Desk:
    """A private copy of the already-ticked desk, for the tests that damage one."""
    root = tmp_path / "desk"
    shutil.copytree(bridged.root, root)
    return Desk(root=root, is_root=root / "is", sealed_root=root / "sealed")


@pytest.fixture(scope="module")
def authority() -> DeskAuthority:
    return current_desk_authority()


def _tick(desk: Desk, boundary: pd.Timestamp, authority: DeskAuthority, **overrides: object):
    arguments = {**desk.kwargs, "authority": authority}
    arguments.update(overrides)
    return run_tick(boundary, **arguments)


def _tick_and_persist(desk: Desk, boundary: pd.Timestamp, authority: DeskAuthority, **overrides):
    result = _tick(desk, boundary, authority, **overrides)
    persist_tick(result, desk.root)
    return result


@pytest.fixture(scope="module")
def ticked(tmp_path_factory, panel: dict[str, pd.DataFrame], authority: DeskAuthority):
    """One desk carried through three ticks: the bridge, the phase change, and the row after it.

    Module-scoped because each tick is a full-window replay, and the read-only assertions below
    would otherwise pay for it many times over. Every test that MUTATES a desk builds its own.
    """
    desk = _build_desk(tmp_path_factory.mktemp("ticked") / "desk", panel)
    results = [
        _tick_and_persist(desk, boundary, authority)
        for boundary in (BRIDGE_TICK, OFFICIAL_TICK, AFTER_OFFICIAL_TICK)
    ]
    return desk, results


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _integrity(desk: Desk) -> dict:
    return json.loads((desk.root / "integrity.json").read_text())


# --------------------------------------------------------------------------------------------
# phase
# --------------------------------------------------------------------------------------------


def test_the_first_tick_is_a_bridge_tick(ticked):
    desk, results = ticked
    bridge = results[0]
    assert bridge.phase == BRIDGE
    assert not bridge.forward_returns.empty, "the seam row settled before this boundary"
    assert set(bridge.forward_returns["phase"]) == {BRIDGE}
    assert set(bridge.positions["phase"]) == {BRIDGE}


def test_official_observation_opens_the_first_monday_after_the_first_tick(ticked):
    desk, results = ticked
    assert results[0].official_start == OFFICIAL_TICK
    assert results[1].phase == OFFICIAL
    assert results[2].forward_returns.loc[
        results[2].forward_returns["timestamp"] == OFFICIAL_TICK, "phase"
    ].tolist() == [OFFICIAL]


def test_the_bridge_rows_stay_bridge_once_official_observation_opens(ticked):
    desk, results = ticked
    forward = _read_csv(desk.root / "forward_returns.csv")
    labelled = dict(zip(forward["timestamp"], forward["phase"], strict=True))
    for stamp, phase in labelled.items():
        expected = OFFICIAL if pd.Timestamp(stamp) >= OFFICIAL_TICK else BRIDGE
        assert phase == expected, stamp
    assert set(labelled.values()) == {BRIDGE, OFFICIAL}


def test_the_official_start_is_read_back_and_not_recomputed(desk: Desk, authority: DeskAuthority):
    """A phase boundary derived fresh each tick walks forward a week at a time.

    Recomputing at the second tick would put official observation at the Monday after THAT tick,
    silently reclassifying rows the desk has already published as unscored.
    """
    first = _tick_and_persist(desk, BRIDGE_TICK, authority)
    assert first.official_start == OFFICIAL_TICK
    later = _tick_and_persist(desk, AFTER_OFFICIAL_TICK, authority)
    assert later.pinned
    assert later.official_start == OFFICIAL_TICK
    assert first_official_boundary(AFTER_OFFICIAL_TICK) != OFFICIAL_TICK, (
        "the fixture must be able to tell a recomputed boundary from the pinned one"
    )
    assert _integrity(desk)["official_start"] == OFFICIAL_TICK.isoformat()


def test_first_official_boundary_is_strictly_after_its_argument():
    monday = pd.Timestamp("2026-02-02T00:00:00Z")
    assert first_official_boundary(monday) == monday + pd.Timedelta(days=7)
    assert first_official_boundary(monday + pd.Timedelta(hours=8)) == monday + pd.Timedelta(days=7)
    assert first_official_boundary(monday + pd.Timedelta(days=1)) == monday + pd.Timedelta(days=7)


def test_a_desk_whose_integrity_record_lost_its_pins_refuses(
    forked: Desk, authority: DeskAuthority
):
    desk = forked
    path = desk.root / "integrity.json"
    payload = json.loads(path.read_text())
    payload.pop("official_start")
    path.write_text(json.dumps(payload))
    with pytest.raises(DeskPinDriftError, match="official_start"):
        _tick(desk, AFTER_OFFICIAL_TICK, authority)


def test_a_moved_seam_is_refused(forked: Desk, authority: DeskAuthority):
    desk = forked
    with pytest.raises(DeskPinDriftError, match="seam"):
        _tick(desk, AFTER_OFFICIAL_TICK, authority, seam=SEAM - pd.Timedelta(days=7))


def test_a_moved_is_start_is_refused(forked: Desk, authority: DeskAuthority):
    desk = forked
    pinned = pd.Timestamp(_integrity(desk)["is_start"])
    with pytest.raises(DeskPinDriftError, match="is_start"):
        _tick(desk, AFTER_OFFICIAL_TICK, authority, is_start=pinned + pd.Timedelta(days=7))


# --------------------------------------------------------------------------------------------
# what a boundary produces
# --------------------------------------------------------------------------------------------


def test_a_rebalance_boundary_fills(ticked):
    desk, results = ticked
    official = results[1]
    assert official.rebalance
    at_boundary = official.fills.loc[official.fills["timestamp"] == OFFICIAL_TICK]
    assert not at_boundary.empty
    assert set(at_boundary["event_type"]) <= {"trade", "risk_reduction"}
    assert len(official.requested_weights) == 6, "three long, three short"


def test_a_non_rebalance_boundary_produces_no_fills_but_still_marks_to_market(ticked):
    """The strategy returns ``None`` at 2 of every 3 boundaries. Holding is not idling.

    Nothing trades, and the book still earns the bar: the return row carries the exposure it held,
    a price PnL, a funding PnL, and the positions frame is not empty.
    """
    desk, results = ticked
    hold = results[2]
    assert not hold.rebalance
    assert hold.fills.loc[hold.fills["timestamp"] == AFTER_OFFICIAL_TICK].empty
    assert not hold.positions.empty
    # A settled hold boundary, so the row it produced is published rather than still forming.
    # BRIDGE_TICK is 2026-01-26 08:00 -- eight hours after a Monday rebalance, and a hold.
    marked = hold.forward_returns.loc[hold.forward_returns["timestamp"] == BRIDGE_TICK]
    assert len(marked) == 1
    row = marked.iloc[0]
    assert row["turnover"] == 0.0, "nothing traded"
    assert row["gross_exposure"] > 0.0
    assert row["price_pnl"] != 0.0
    assert row["funding_pnl"] != 0.0


def test_the_terminal_return_row_is_not_published(ticked):
    """It covers an interval that has only just opened, and liquidates the book at the edge."""
    desk, results = ticked
    for result in results:
        assert result.forward_returns["timestamp"].max() < result.boundary
    forward = _read_csv(desk.root / "forward_returns.csv")
    assert pd.Timestamp(forward["timestamp"].max()) == AFTER_OFFICIAL_TICK - INTERVAL


def test_no_end_of_window_liquidation_reaches_the_fill_record(ticked):
    desk, results = ticked
    fills = _read_csv(desk.root / "paper_fills.csv")
    assert "terminal" not in set(fills["execution_phase"])
    assert set(fills["phase"]) <= {BRIDGE, OFFICIAL}


def test_a_tick_at_the_seam_publishes_no_settled_rows_yet(desk: Desk, authority: DeskAuthority):
    """The desk's first possible tick: the seam's own row is still forming, so nothing settles.

    An empty forward frame has to survive the whole persistence path -- ledger, CSV, bindings --
    because it is the state every desk starts in, and it is the one shape a happy-path test that
    ticks late never reaches.
    """
    result = _tick_and_persist(desk, SEAM, authority)
    assert result.phase == BRIDGE
    assert result.forward_returns.empty
    assert list(result.forward_returns.columns) == list(FORWARD_RETURN_SCHEMA.columns)
    assert not result.positions.empty, "the seam boundary is a Monday: the book is opened here"
    integrity = _integrity(desk)
    assert integrity["forward_rows"] == 0
    assert integrity["official_rows"] == 0
    assert integrity["artifacts"]["forward_returns"]["rows"] == 0
    assert _read_csv(desk.root / "forward_returns.csv").empty


def test_every_persisted_row_carries_a_phase(ticked):
    desk, _ = ticked
    for name in ("forward_returns.csv", "paper_fills.csv", "current_positions.csv"):
        frame = _read_csv(desk.root / name)
        assert "phase" in frame.columns, name
        assert set(frame["phase"]) <= {BRIDGE, OFFICIAL}, name
        assert frame["phase"].notna().all(), name


def test_the_artifacts_and_their_bindings_are_written(ticked):
    desk, results = ticked
    integrity = _integrity(desk)
    assert integrity["status"] == "PASS"
    assert integrity["paper_only"] is True
    assert integrity["boundary"] == AFTER_OFFICIAL_TICK.isoformat()
    for field in AUTHORITY_FIELDS:
        assert integrity[field] == getattr(results[-1].authority, field)
    for name in ("forward_returns", "paper_fills", "current_positions", "boundary", "latest"):
        binding = integrity["artifacts"][name]
        path = desk.root / binding["path"]
        assert path.is_file()
        assert binding["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    record = desk.root / "boundaries" / "20260202T080000Z.json"
    assert record.is_file()
    assert json.loads(record.read_text()) == json.loads(
        (desk.root / "latest-boundary.json").read_text()
    )


def test_a_boundary_off_the_decision_grid_is_refused(desk: Desk, authority: DeskAuthority):
    with pytest.raises(TickWindowError, match="decision grid"):
        _tick(desk, BRIDGE_TICK + pd.Timedelta(hours=1), authority)


# --------------------------------------------------------------------------------------------
# authority
# --------------------------------------------------------------------------------------------


def _tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _artifacts(root: Path) -> dict[str, str]:
    """The published record, without the reassembled snapshot.

    ``desk_root/snapshot`` is a work product rebuilt on every tick and legitimately grows with the
    window; the CSVs, the ledgers, the boundary records and ``integrity.json`` are the record.
    """
    return {
        path: digest for path, digest in _tree(root).items() if not path.startswith("snapshot/")
    }


@pytest.mark.parametrize("field", AUTHORITY_FIELDS)
def test_an_authority_mismatch_aborts_before_anything_is_written(
    desk: Desk, authority: DeskAuthority, field: str
):
    """Refusal has to happen before the first byte, or a drifted desk publishes anyway."""
    before = _tree(desk.root)
    wrong = dataclasses.replace(authority, **{field: "0" * 64})
    with pytest.raises(DeploymentChangedError, match=field):
        _tick(desk, BRIDGE_TICK, wrong)
    assert _tree(desk.root) == before
    assert not (desk.root / "integrity.json").exists()
    assert not (desk.root / "snapshot").exists()


# --------------------------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------------------------


def test_a_later_tick_reproduces_the_earlier_forward_rows(ticked):
    """The happy path of the determinism check, and the reason it can be an abort.

    Each tick re-runs the whole window, so the second tick recomputes every row the first
    published. They come back identical because each is a function of past-only data -- which is
    exactly what makes a DIFFERENCE worth stopping the desk for.
    """
    desk, results = ticked
    published = results[0].forward_returns
    ledger = conform_frame(
        FORWARD_RETURN_SCHEMA, pd.read_parquet(desk.root / "ledger" / "forward_returns.parquet")
    )
    overlap = ledger.loc[ledger["timestamp"].isin(published["timestamp"])].reset_index(drop=True)
    pd.testing.assert_frame_equal(overlap, published, check_exact=True)
    assert len(ledger) > len(published), "the later ticks appended rows of their own"


def test_ticking_the_same_boundary_twice_changes_nothing(forked: Desk, authority: DeskAuthority):
    desk = forked
    before = _artifacts(desk.root)
    first = _integrity(desk)
    _tick_and_persist(desk, BRIDGE_TICK, authority)
    after = _artifacts(desk.root)
    second = _integrity(desk)
    assert {path: digest for path, digest in after.items() if path != "integrity.json"} == {
        path: digest for path, digest in before.items() if path != "integrity.json"
    }
    # Two fields legitimately move, and both say the same thing: the second tick read the pins the
    # first one wrote, and found every row it recomputed already recorded and unchanged.
    assert first.pop("official_start_pinned") is False
    assert second.pop("official_start_pinned") is True
    assert first.pop("appended")["forward_returns"]["appended"] == 1
    assert second.pop("appended") == {
        "forward_returns": {"appended": 0, "unchanged": 1, "total": 1},
        "paper_fills": {"appended": 0, "unchanged": 11, "total": 11},
    }
    assert first == second


def test_the_determinism_check_fires_when_a_recorded_forward_row_changes(
    forked: Desk, authority: DeskAuthority
):
    """A revised source row is an append-invariance abort, not a rounding difference."""
    desk = forked
    ledger_path = desk.root / "ledger" / "forward_returns.parquet"
    ledger = pd.read_parquet(ledger_path)
    ledger.loc[0, "net_return"] = float(ledger.loc[0, "net_return"]) + 1e-9
    ledger.to_parquet(ledger_path, index=False)
    result = _tick(desk, AFTER_OFFICIAL_TICK, authority)
    revised = _artifacts(desk.root)
    with pytest.raises(AppendInvarianceError, match="net_return"):
        persist_tick(result, desk.root)
    assert _artifacts(desk.root) == revised, "an abort leaves both values and writes nothing"


def test_the_determinism_check_fires_when_a_recorded_fill_changes(
    forked: Desk, authority: DeskAuthority
):
    desk = forked
    ledger_path = desk.root / "ledger" / "paper_fills.parquet"
    ledger = pd.read_parquet(ledger_path)
    ledger.loc[0, "price"] = float(ledger.loc[0, "price"]) * 2.0
    ledger.to_parquet(ledger_path, index=False)
    result = _tick(desk, AFTER_OFFICIAL_TICK, authority)
    with pytest.raises(AppendInvarianceError, match="price"):
        persist_tick(result, desk.root)


def test_a_boundary_record_that_disagrees_with_its_replay_aborts(
    forked: Desk, authority: DeskAuthority
):
    desk = forked
    result = _tick(desk, BRIDGE_TICK, authority)
    record = desk.root / "boundaries" / f"{BRIDGE_TICK.strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = json.loads(record.read_text())
    payload["risk_scalar"] = payload["risk_scalar"] + 1.0
    record.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(DeskPinDriftError, match="APPEND-INVARIANCE"):
        persist_tick(result, desk.root)


# --------------------------------------------------------------------------------------------
# parity: the rows are the tournament evaluator's own
# --------------------------------------------------------------------------------------------


def _reference(snapshot_root: Path, *, boundary: pd.Timestamp, is_start: pd.Timestamp, seed: int):
    """An independent invocation of the tournament's own runner over the same window.

    Built here from the frozen config and the frozen candidate rather than from anything the desk
    returns, so agreement is a statement about the desk and not a tautology about one object.
    """
    snapshot = load_snapshot(snapshot_root)
    raw = load_config(CONFIG_PATH).raw
    evaluator = evaluator_config(raw["execution"])
    root = candidate_root()
    return run_candidate(
        strategy_from_module(load_team_module(root), entry=root / ENTRYPOINT),
        snapshot,
        decision_times=decision_grid(
            is_start,
            boundary + pd.Timedelta(hours=evaluator.interval_hours),
            interval_hours=evaluator.interval_hours,
        ),
        seed=seed,
        config=evaluator,
        risk_unit=raw["risk_unit"],
        cost_multipliers=(1,),
        risk_policy=load_candidate_risk_policy(root),
    )


def _assert_parity(result, run, *, seam: pd.Timestamp) -> None:
    returns = run.results[1].returns
    index = pd.DatetimeIndex(returns.index)
    expected = returns.loc[(index >= seam) & (index < result.boundary)].copy()
    expected.index.name = "timestamp"
    expected = expected.reset_index()
    published = result.forward_returns.drop(columns=["phase"])
    assert list(published.columns) == list(expected.columns)
    pd.testing.assert_frame_equal(
        published, expected[published.columns].reset_index(drop=True), check_exact=True
    )
    events = run.results[1].events
    stamps = pd.to_datetime(events["timestamp"], utc=True)
    fills = events.loc[
        (stamps >= seam)
        & (stamps <= result.boundary)
        & events["event_type"].isin(tick_module.FILL_EVENT_TYPES)
    ]
    published_fills = result.fills
    assert len(published_fills) == len(fills)
    for column in ("quantity", "price", "notional", "fee", "slippage", "cashflow"):
        pd.testing.assert_series_equal(
            published_fills[column].reset_index(drop=True),
            fills[column].astype(float).reset_index(drop=True),
            check_exact=True,
            check_names=False,
        )


def test_the_forward_rows_are_the_evaluators_own_rows(ticked):
    """Every published number is the evaluator's, bit for bit. The desk selects and labels."""
    desk, results = ticked
    result = results[-1]
    run = _reference(
        desk.root / "snapshot",
        boundary=result.boundary,
        is_start=result.pins.is_start,
        seed=tick_module.DESK_SEED,
    )
    _assert_parity(result, run, seam=SEAM)


def test_the_risk_scalar_and_weights_are_the_runners_own(ticked):
    desk, results = ticked
    result = results[1]
    run = _reference(
        desk.root / "snapshot",
        boundary=result.boundary,
        is_start=result.pins.is_start,
        seed=tick_module.DESK_SEED,
    )
    assert result.risk_scalar == float(run.risk_scalars.loc[result.boundary])
    executed = run.scaled_targets.loc[result.boundary].drop(labels=[REBALANCE_INSTRUCTION_COLUMN])
    expected = executed.loc[executed != 0.0].sort_index().astype(float)
    pd.testing.assert_series_equal(
        result.executed_weights, expected, check_exact=True, check_names=False
    )


# --------------------------------------------------------------------------------------------
# parity at scale: the real record
# --------------------------------------------------------------------------------------------

REAL_SEAM = pd.Timestamp("2026-07-27T00:00:00Z")
"""The last recorded reconstitution boundary. Used as the desk's seam so a boundary inside the
sealed window produces forward rows to compare -- the production seam is ``SEALED_END``."""

REAL_BOUNDARY = pd.Timestamp("2026-07-30T00:00:00Z")
REAL_NEXT = pd.Timestamp("2026-07-30T08:00:00Z")


@pytest.fixture(scope="module")
def real_desk(tmp_path_factory) -> Desk:
    """The real IS and sealed snapshots, with the wide contract metadata the splits omit.

    Four of the twenty members at the final sealed boundary have no metadata row in either split
    snapshot; a live desk fetches its own from ``exchangeInfo`` every tick, and here it comes from
    the acquisition.
    """
    root = tmp_path_factory.mktemp("real") / "desk"
    cache = root / "cache"
    cache.mkdir(parents=True)
    metadata = pd.read_parquet(ACQUISITION_ROOT / "contract_metadata.parquet")
    conform_frame(CONTRACT_METADATA, metadata).to_parquet(
        cache / f"{CONTRACT_METADATA}.parquet", index=False
    )
    return Desk(root=root, is_root=IS_ROOT, sealed_root=SEALED_ROOT)


@pytest.mark.parity
@requires_acquisition
def test_the_real_forward_rows_are_the_evaluators_own_rows(
    real_desk: Desk, authority: DeskAuthority
):
    """The same parity statement over the real six-year window, where one replay costs ~7 minutes.

    Also the only test that exercises the production ``is_start`` -- the tournament's own
    ``resolve_is_start`` over the assembled membership, which lands on 2020-08-17.
    """
    result = run_tick(
        REAL_BOUNDARY,
        desk_root=real_desk.root,
        authority=authority,
        seam=REAL_SEAM,
        is_root=IS_ROOT,
        sealed_root=SEALED_ROOT,
    )
    persist_tick(result, real_desk.root)
    assert result.pins.is_start == resolve_is_start(
        load_snapshot(real_desk.root / "snapshot").membership
    )
    run = _reference(
        real_desk.root / "snapshot",
        boundary=REAL_BOUNDARY,
        is_start=result.pins.is_start,
        seed=tick_module.DESK_SEED,
    )
    _assert_parity(result, run, seam=REAL_SEAM)


@pytest.mark.parity
@requires_acquisition
def test_the_real_record_is_stable_when_the_window_extends(
    real_desk: Desk, authority: DeskAuthority
):
    """Tick, tick again eight hours later, and the published rows must be untouched.

    On real data, with real delistings, participation-capped exits and funding. If the terminal
    row were published, or a fill at the boundary were not yet settled, this would abort.
    """
    first = run_tick(
        REAL_BOUNDARY,
        desk_root=real_desk.root,
        authority=authority,
        seam=REAL_SEAM,
        is_root=IS_ROOT,
        sealed_root=SEALED_ROOT,
    )
    persist_tick(first, real_desk.root)
    second = run_tick(
        REAL_NEXT,
        desk_root=real_desk.root,
        authority=authority,
        seam=REAL_SEAM,
        is_root=IS_ROOT,
        sealed_root=SEALED_ROOT,
    )
    persist_tick(second, real_desk.root)
    ledger = conform_frame(
        FORWARD_RETURN_SCHEMA,
        pd.read_parquet(real_desk.root / "ledger" / "forward_returns.parquet"),
    )
    overlap = ledger.loc[ledger["timestamp"].isin(first.forward_returns["timestamp"])]
    pd.testing.assert_frame_equal(
        overlap.reset_index(drop=True), first.forward_returns, check_exact=True
    )
    assert len(ledger) == len(first.forward_returns) + 1


# --------------------------------------------------------------------------------------------
# the design rule, by inspection
# --------------------------------------------------------------------------------------------

ARITHMETIC_OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)

ALLOWED_ARITHMETIC = frozenset(
    {
        # EVERY arithmetic node in tick.py, verbatim and reviewed. Nine are path joins (``/`` on a
        # Path), four build a dtype tuple, two repeat a scalar down a column, and the rest is
        # calendar arithmetic and a header-row subtraction. A price, a fee, a rate, a quantity, a
        # weight or a PnL appearing in this inventory is the defect the module exists to prevent:
        # it would mean execution had been reimplemented here beside the evaluator's copy, and two
        # copies can disagree. Adding one has to be a deliberate edit to this set.
        "('float64',) * 2",
        "('float64',) * 24",
        "('float64',) * 4",
        "('float64',) * 7",
        "(MONDAY - midnight.weekday()) % 7",
        "MONDAY - midnight.weekday()",
        "Path(desk_root) / INTEGRITY_JSON",
        "[boundary] * len(held)",
        "[phase] * len(held)",
        "candidate += pd.Timedelta(days=7)",
        "candidate / ENTRYPOINT",
        "directory / f\"{boundary.strftime('%Y%m%dT%H%M%SZ')}.json\"",
        "json.dumps(payload, indent=2, sort_keys=True) + '\\n'",
        "ledger / f'{FILL_SCHEMA.name}.parquet'",
        "ledger / f'{FORWARD_RETURN_SCHEMA.name}.parquet'",
        "midnight + pd.Timedelta(days=(MONDAY - midnight.weekday()) % 7)",
        "moment + interval",
        "root / BOUNDARIES_DIRNAME",
        "root / CACHE_DIRNAME",
        "root / FILLS_CSV",
        "root / FORWARD_CSV",
        "root / INTEGRITY_JSON",
        "root / LATEST_JSON",
        "root / LEDGER_DIRNAME",
        "root / POSITIONS_CSV",
        "sum((1 for line in path.read_text().splitlines() if line.strip())) - 1",
    }
)

FORBIDDEN_IN_ARITHMETIC = re.compile(
    r"price|fee|slipp|fund|notional|quantity|weight|equity|pnl|return|turnover|scalar|rate"
)
"""Case sensitive, and lowercase on purpose: a reference to one of these quantities is written
``row["price"]`` or ``net_return``, while an ALL-CAPS module constant naming a schema or a file
(``FORWARD_RETURN_SCHEMA``) is not a reference to a number. Matching both would force the guard to
be relaxed the first time it fired on a filename, and a relaxed guard catches nothing."""


def test_the_module_computes_no_fill_fee_slippage_or_funding():
    """The rule this module is built on, made executable rather than left to review.

    Fills, fees, slippage, funding and position sizes are ``run_candidate``'s, and the moment one
    of them is computed here there are two implementations of execution in the desk.
    """
    tree = ast.parse(MODULE_PATH.read_text())
    operations = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp | ast.AugAssign) and isinstance(node.op, ARITHMETIC_OPERATORS)
    ]
    unexpected = sorted(set(operations) - ALLOWED_ARITHMETIC)
    assert unexpected == [], f"new arithmetic in tick.py: {unexpected}"
    for operation in operations:
        assert not FORBIDDEN_IN_ARITHMETIC.search(operation), operation


def test_the_module_reaches_no_network_and_signs_nothing():
    source = MODULE_PATH.read_text()
    for forbidden in ("httpx", "requests", "api_key", "api_secret", "hmac", "place_order"):
        assert forbidden not in source, forbidden


def test_activation_freeze_still_verifies(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    verify_activation("tournament/cup20/activation-freeze.json")

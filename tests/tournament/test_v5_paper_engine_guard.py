"""The desk engine must not re-do work it has already published -- and must not skip work it owes.

This exists because it happened. The watchdog was scheduled every 20 minutes while a tick replays
2.5 years across four desks at ~25 minutes of one core, so the engine ran essentially continuously
-- roughly seventy full replays a day to publish three rows. The engine lock stopped them
corrupting each other and did nothing about the waste, because a lock is the wrong tool for it.

Two things keep it fixed, and both are needed. The cron cadence is now boundary-aligned, and the
engine exits immediately when every desk has already replayed as far as the data allows. The cadence
lives in a crontab nothing here can test; this covers the guard, which is the half that holds even
if the schedule is changed again by someone who has not read the arithmetic.

The guard keys on **replayed_through**, not on the nominal boundary, and the second half of this
file is about why. When the bar has not landed yet the engine clamps: it records boundary B having
replayed only B-8h. A guard keyed on B would call that boundary finished at the first attempt and
make the retry cron entry -- which exists for exactly the too-early case -- exit without looking,
stranding a row for a full 8h. Skipping owed work is a worse failure than the waste this removes,
so it gets more tests than the waste does.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "scripts" / "top40v5_paper_engine.py"


def _engine():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("v5_paper_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["v5_paper_engine"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


NOW = pd.Timestamp("2026-08-29 18:00", tz="UTC")


@pytest.fixture
def paper(tmp_path: Path, monkeypatch):
    """A launched four-desk tree whose snapshot reaches the current boundary."""

    engine = _engine()
    root = tmp_path / "paper"
    snapshot = tmp_path / "snapshot"
    monkeypatch.setattr(engine, "PAPER", root)
    monkeypatch.setattr(engine, "SNAPSHOT", snapshot)

    desks = ["desk-1", "desk-2", "desk-3", "ensemble-eq3"]
    manifest = {d: {"lane": d, "bundle": {}} for d in desks}
    root.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    (root / "deployment-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "launch.json").write_text(
        json.dumps({"official_start": "2026-09-01 00:00:00+00:00"}), encoding="utf-8"
    )
    for desk in desks:
        (root / desk).mkdir()
    _write_bars(snapshot, engine._boundary(NOW))
    return engine, root, desks, snapshot


def _write_bars(snapshot: Path, last_bar: pd.Timestamp) -> None:
    """The four frames a tick loads. Only bars.parquet has to be meaningful -- the guard reads its
    open_time column, and the tests that get past the guard stop at the replay."""

    times = pd.date_range(last_bar - pd.Timedelta(hours=24), last_bar, freq="8h", tz="UTC")
    pd.DataFrame({"open_time": times, "symbol": "BTCUSDT"}).to_parquet(snapshot / "bars.parquet")
    for name in ("funding", "membership", "mark_prices"):
        pd.DataFrame({"symbol": ["BTCUSDT"]}).to_parquet(snapshot / f"{name}.parquet")


def _publish(
    root: Path, desks, boundary: pd.Timestamp, reached: pd.Timestamp | None = None
) -> None:
    for desk in desks:
        (root / desk).mkdir(parents=True, exist_ok=True)
        record = {"boundary": str(boundary)}
        if reached is not None:
            record["replayed_through"] = str(reached)
        (root / desk / "boundary.json").write_text(json.dumps(record), encoding="utf-8")


def _forbid_replay(engine, monkeypatch) -> None:
    """Make the expensive path an error rather than merely slow.

    ``_returns_for`` is the per-desk replay -- the 25 minutes this guard exists to avoid. Asserting
    on ``pd.read_parquet`` would be wrong now, because the guard itself reads one column of one
    parquet to learn how far the data reaches, and that cheap read is what makes it correct.
    """

    def _boom(*args, **kwargs):
        raise AssertionError("the engine replayed a boundary it had already published")

    monkeypatch.setattr(engine, "_returns_for", _boom)


def test_the_engine_does_nothing_when_every_desk_is_current(paper, monkeypatch, capsys):
    """The whole point: no replay is run."""

    engine, root, desks, _ = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks, boundary, reached=boundary)
    _forbid_replay(engine, monkeypatch)

    assert engine.tick(NOW) == 0
    assert "already replayed" in capsys.readouterr().out


def test_the_guard_reads_only_one_column_of_one_parquet(paper, monkeypatch, capsys):
    """The cheap read has to stay cheap, or the guard costs what it saves."""

    engine, root, desks, _ = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks, boundary, reached=boundary)
    _forbid_replay(engine, monkeypatch)

    calls: list[dict] = []
    original = pd.read_parquet

    def _record(path, *args, **kwargs):
        calls.append(kwargs)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", _record)
    assert engine.tick(NOW) == 0
    capsys.readouterr()

    assert len(calls) == 1, f"the guard read {len(calls)} parquets before short-circuiting"
    assert calls[0].get("columns") == ["open_time"]


def test_the_engine_still_runs_when_one_desk_is_behind(paper, monkeypatch):
    """The other direction, so the guard cannot be trivially always-on.

    One desk short must produce a real tick -- otherwise a desk that missed a publication would stay
    missed forever, which is worse than the waste this guard removes.
    """

    engine, root, desks, _ = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks, boundary, reached=boundary)
    stale = boundary - pd.Timedelta(hours=8)
    (root / desks[2] / "boundary.json").write_text(
        json.dumps({"boundary": str(stale), "replayed_through": str(stale)}), encoding="utf-8"
    )

    reached = {"replayed": False}

    def _mark(*args, **kwargs):
        reached["replayed"] = True
        raise RuntimeError("stop here; reaching the replay is the assertion")

    # The engine catches operational exceptions and records FAILED rather than propagating, so
    # the flag is the assertion; pytest.raises would never see this.
    monkeypatch.setattr(engine, "_returns_for", _mark)
    engine.tick(NOW)
    assert reached["replayed"], "a desk behind the boundary must trigger a real tick"


def test_a_desk_that_never_published_triggers_a_tick(paper, monkeypatch):
    """A missing boundary.json is not the same as an up-to-date one."""

    engine, root, desks, _ = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks[:3], boundary, reached=boundary)

    reached = {"replayed": False}

    def _mark(*args, **kwargs):
        reached["replayed"] = True
        raise RuntimeError("stop here")

    # The engine catches operational exceptions and records FAILED rather than propagating, so
    # the flag is the assertion; pytest.raises would never see this.
    monkeypatch.setattr(engine, "_returns_for", _mark)
    engine.tick(NOW)
    assert reached["replayed"]


def test_a_clamped_tick_is_retried_once_the_bar_lands(paper, monkeypatch):
    """The retry hole, which is the reason the guard keys on replayed_through.

    The desks recorded the current boundary while the snapshot was one bar short, so they replayed
    to B-8h. The bar has since arrived. Keying on the nominal boundary would call this done.
    """

    engine, root, desks, snapshot = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks, boundary, reached=boundary - pd.Timedelta(hours=8))
    _write_bars(snapshot, boundary)  # the bar has landed

    reached = {"replayed": False}

    def _mark(*args, **kwargs):
        reached["replayed"] = True
        raise RuntimeError("stop here")

    # The engine catches operational exceptions and records FAILED rather than propagating, so
    # the flag is the assertion; pytest.raises would never see this.
    monkeypatch.setattr(engine, "_returns_for", _mark)
    engine.tick(NOW)
    assert reached["replayed"], (
        "a desk that was clamped short must re-tick once the missing bar arrives; "
        "the guard is keying on the nominal boundary again"
    )


def test_a_still_clamped_tick_does_not_re_replay(paper, monkeypatch, capsys):
    """And the converse, or the retry entry reintroduces the runaway it was built beside.

    Same clamped state, but the bar still has not landed. There is nothing new to replay, so the
    engine must exit rather than redo 2.5 years for a row it cannot yet publish.
    """

    engine, root, desks, snapshot = paper
    boundary = engine._boundary(NOW)
    short = boundary - pd.Timedelta(hours=8)
    _publish(root, desks, boundary, reached=short)
    _write_bars(snapshot, short)  # still behind
    _forbid_replay(engine, monkeypatch)

    assert engine.tick(NOW) == 0
    assert "already replayed" in capsys.readouterr().out


def test_a_record_written_before_replayed_through_existed_is_not_trusted_when_stale(
    paper, monkeypatch
):
    """Backward compatibility must fail safe.

    Records written by the previous engine carry only ``boundary``. Falling back to it is right when
    nothing was clamped, but a stale snapshot makes that fallback claim a replay that never
    happened -- so the desk must re-tick rather than be assumed current.
    """

    engine, root, desks, snapshot = paper
    boundary = engine._boundary(NOW)
    _publish(root, desks, boundary)  # no replayed_through key
    _write_bars(snapshot, boundary - pd.Timedelta(hours=8))

    reached = {"replayed": False}

    def _mark(*args, **kwargs):
        reached["replayed"] = True
        raise RuntimeError("stop here")

    # The engine catches operational exceptions and records FAILED rather than propagating, so
    # the flag is the assertion; pytest.raises would never see this.
    monkeypatch.setattr(engine, "_returns_for", _mark)
    engine.tick(NOW)
    assert reached["replayed"]


def test_the_early_exit_still_records_current_staleness(paper, monkeypatch, capsys):
    """DATA-STALE must be able to fire while the guard is short-circuiting.

    The healthcheck computes DATA-STALE from `paper-top40v5/boundary.json`. The early-exit guard
    returns before the full record is written further down, so a guard that short-circuits every
    tick also freezes `stale_hours` at whatever the last completed replay saw. It read 0.0 through
    40h of a broken append and only LATE caught it -- the class named for persistent staleness
    could not fire during persistent staleness.
    """

    engine, root, desks, snapshot = paper
    boundary = engine._boundary(NOW)
    short = boundary - pd.Timedelta(hours=24)
    _publish(root, desks, boundary, reached=short)
    _write_bars(snapshot, short)  # three boundaries behind
    (root / "boundary.json").write_text(
        json.dumps({"boundary": str(boundary), "stale_hours": 0.0, "generation": "abc"}),
        encoding="utf-8",
    )
    _forbid_replay(engine, monkeypatch)

    assert engine.tick(NOW) == 0
    capsys.readouterr()

    record = json.loads((root / "boundary.json").read_text(encoding="utf-8"))
    assert record["stale_hours"] == 24.0, (
        "the early-exit path left stale_hours at its previous value; DATA-STALE cannot fire"
    )
    assert record["snapshot_last_bar"] == str(short)
    # Whatever only the full tick can compute must survive the cheap refresh.
    assert record["generation"] == "abc"

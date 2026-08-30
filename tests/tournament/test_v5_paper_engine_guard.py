"""The desk engine must not re-do work it has already published.

This exists because it happened. The watchdog was scheduled every 20 minutes while a tick replays
2.5 years across four desks at ~25 minutes of one core, so the engine ran essentially continuously
-- roughly seventy full replays a day to publish three rows. The engine lock stopped them
corrupting each other and did nothing about the waste, because a lock is the wrong tool for it.

Two things keep it fixed, and both are needed. The cron cadence is now boundary-aligned, and the
engine exits immediately when every desk has already published the current boundary. The cadence
lives in a crontab nothing here can test; this covers the guard, which is the half that holds even
if the schedule is changed again by someone who has not read the arithmetic.
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


@pytest.fixture
def paper(tmp_path: Path, monkeypatch):
    """A launched four-desk tree with nothing to do."""

    engine = _engine()
    root = tmp_path / "paper"
    monkeypatch.setattr(engine, "PAPER", root)

    desks = ["desk-1", "desk-2", "desk-3", "ensemble-eq3"]
    manifest = {d: {"lane": d, "bundle": {}} for d in desks}
    root.mkdir(parents=True)
    (root / "deployment-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "launch.json").write_text(
        json.dumps({"official_start": "2026-09-01 00:00:00+00:00"}), encoding="utf-8"
    )
    return engine, root, desks


def _publish(root: Path, desks, boundary: pd.Timestamp) -> None:
    for desk in desks:
        (root / desk).mkdir(parents=True, exist_ok=True)
        (root / desk / "boundary.json").write_text(
            json.dumps({"boundary": str(boundary)}), encoding="utf-8"
        )


def test_the_engine_does_nothing_when_every_desk_has_the_boundary(paper, capsys):
    """The whole point: no snapshot is loaded and no replay is run."""

    engine, root, desks = paper
    now = pd.Timestamp("2026-08-29 18:00", tz="UTC")
    _publish(root, desks, engine._boundary(now))

    # A replay would have to read the snapshot; make that an error rather than merely slow, so the
    # test fails loudly if the guard stops short-circuiting.
    def _forbidden(*args, **kwargs):
        raise AssertionError("the engine loaded market data for an already-published boundary")

    original, pd.read_parquet = pd.read_parquet, _forbidden
    try:
        assert engine.tick(now) == 0
    finally:
        pd.read_parquet = original

    assert "already published" in capsys.readouterr().out


def test_the_engine_still_runs_when_one_desk_is_behind(paper, monkeypatch):
    """The other direction, so the guard cannot be trivially always-on.

    One desk short of the boundary must produce a real tick -- otherwise a desk that missed a
    publication would stay missed forever, which is worse than the waste this guard removes.
    """

    engine, root, desks = paper
    now = pd.Timestamp("2026-08-29 18:00", tz="UTC")
    _publish(root, desks, engine._boundary(now))
    stale = engine._boundary(now) - pd.Timedelta(hours=8)
    (root / desks[2] / "boundary.json").write_text(
        json.dumps({"boundary": str(stale)}), encoding="utf-8"
    )

    reached = {"loaded": False}

    def _mark(*args, **kwargs):
        reached["loaded"] = True
        raise RuntimeError("stop here; reaching the load is the assertion")

    monkeypatch.setattr(pd, "read_parquet", _mark)
    with pytest.raises(RuntimeError):
        engine.tick(now)
    assert reached["loaded"], "a desk behind the boundary must trigger a real tick"


def test_a_desk_that_never_published_triggers_a_tick(paper, monkeypatch):
    """A missing boundary.json is not the same as an up-to-date one."""

    engine, root, desks = paper
    now = pd.Timestamp("2026-08-29 18:00", tz="UTC")
    _publish(root, desks[:3], engine._boundary(now))

    reached = {"loaded": False}

    def _mark(*args, **kwargs):
        reached["loaded"] = True
        raise RuntimeError("stop here")

    monkeypatch.setattr(pd, "read_parquet", _mark)
    with pytest.raises(RuntimeError):
        engine.tick(now)
    assert reached["loaded"]

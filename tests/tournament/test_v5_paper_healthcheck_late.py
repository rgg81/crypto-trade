"""LATE must fire on a stalled desk and stay silent on a current one.

The threshold was `now - published > 8h45m`, which ignores that the engine deliberately publishes
the PREVIOUS closed boundary -- the final one is provisional until a later bar exists. A perfectly
current desk therefore sits between 8h and 16h behind the wall clock, and the check fired on a
healthy field for most of every cycle: it read LATE(9h) minutes after all four published on time.

That matters more than a cosmetic wrong label. It sat directly beside a genuine LATE(40h) from a
crashed append, and a check that cries wolf on a healthy desk is the one nobody reads on the day it
is right.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]


def _healthcheck():  # type: ignore[no-untyped-def]
    path = REPO / "scripts" / "top40v5_paper_healthcheck.py"
    spec = importlib.util.spec_from_file_location("v5_healthcheck", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["v5_healthcheck"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture
def check():  # type: ignore[no-untyped-def]
    return _healthcheck()


def test_the_owed_boundary_matches_the_engine_rule(check):
    """Both must agree on what is owed, or one of them is measuring a different thing."""

    engine_path = REPO / "scripts" / "top40v5_paper_engine.py"
    spec = importlib.util.spec_from_file_location("v5_engine_for_late", engine_path)
    engine = importlib.util.module_from_spec(spec)
    sys.modules["v5_engine_for_late"] = engine
    spec.loader.exec_module(engine)  # type: ignore[union-attr]

    for hour in range(0, 24):
        now = pd.Timestamp("2026-08-31", tz="UTC") + pd.Timedelta(hours=hour, minutes=13)
        assert check._owed_boundary(now) == engine._boundary(now), f"disagree at {now}"


def _late(check, now: pd.Timestamp, published: pd.Timestamp, tmp_path: Path) -> bool:
    """Ask the real classifier, not a local copy of its arithmetic.

    An earlier version of this helper reimplemented the rule and read as a passing guard while a
    mutation to the script left every test green -- a test of a helper is not a test of the path,
    which is the defect class this whole file exists beside.
    """

    root = tmp_path / "desk-1"
    root.mkdir(exist_ok=True)
    (root / "boundary.json").write_text(
        json.dumps({"boundary": str(published), "replayed_through": str(published)}),
        encoding="utf-8",
    )
    check.PAPER = tmp_path
    classes = check._classes("desk-1", {"bundle": {}}, True, now)
    return any(c.startswith("LATE") for c in classes)


def test_a_current_desk_is_never_late_at_any_point_in_the_cycle(check, tmp_path):
    """The false positive. A desk holding the owed boundary is current, all cycle long."""

    for minutes in range(0, 8 * 60, 7):
        now = pd.Timestamp("2026-08-31 00:00", tz="UTC") + pd.Timedelta(minutes=minutes)
        published = check._owed_boundary(now)
        assert not _late(check, now, published, tmp_path), f"healthy desk flagged LATE at {now}"


def test_a_desk_one_boundary_behind_is_late_once_the_grace_elapses(check, tmp_path):
    """The true positive it has to keep catching."""

    now = pd.Timestamp("2026-08-31 09:13", tz="UTC")
    owed = check._owed_boundary(now)
    assert not _late(check, now, owed, tmp_path), "sanity: current is not late"
    assert _late(check, now, owed - check.INTERVAL, tmp_path), "one boundary behind must be LATE"


def test_a_long_stall_is_late_immediately_without_waiting_for_grace(check, tmp_path):
    """The 40h stall, checked at a moment when the grace has NOT yet elapsed.

    A grace-only rule would have stayed silent here, which is the exact window the crashed append
    sat in. Missing more than one boundary is unambiguous and does not wait.
    """

    now = pd.Timestamp("2026-08-31 08:25", tz="UTC")
    owed = check._owed_boundary(now)
    assert now - owed - check.INTERVAL < check.LATE_GRACE, "fixture must be inside the grace window"
    assert _late(check, now, pd.Timestamp("2026-08-29 16:00", tz="UTC"), tmp_path)

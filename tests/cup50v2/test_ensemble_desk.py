"""The equal-risk ensemble desk.

The hedge only works if the three finalists actually contribute equally. Averaging raw books would
weight the ensemble toward whichever finalist runs the largest gross, so each is sized to the
common volatility target first. These tests pin that, and the subtler rule beside it: a finalist
that holds contributes the book it last emitted, because a hold means "no change to my book", not
"I have no book". Treating a hold as flat would quietly de-risk the ensemble every time a member
went quiet.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _member_source(name: str, weights: dict[str, float] | None, holds_after: int = 10**9) -> str:
    return f'''
class _S:
    def __init__(self):
        self.calls = 0

    def target_weights(self, context, *, seed):
        self.calls += 1
        if self.calls > {holds_after}:
            return None
        return {weights!r}


def build_strategy():
    return _S()
'''


def _context(symbols: list[str], bars: int = 400) -> object:
    """context.bars is a mapping symbol -> frame keyed on close_time, per DecisionContextV2.

    The first draft of this fixture built one long concatenated frame, which close_panel silently
    reduces to nothing: it calls context.bars.get(symbol), and on a DataFrame that looks up a
    column, finds none, and returns an empty panel. Every risk scalar then fell back to 1.0 and the
    ensemble averaged raw books. The equalisation assertion below is what caught it -- a weaker
    test would have passed on a fixture that exercised none of this.
    """
    index = pd.date_range("2024-01-01", periods=bars, freq="8h", tz="UTC")
    rng = np.random.default_rng(7)
    history = {}
    for position, symbol in enumerate(symbols):
        steps = rng.normal(0.0, 0.01 + 0.010 * position, size=bars)
        history[symbol] = pd.DataFrame(
            {
                "close_time": index,
                "close": 100.0 * np.exp(np.cumsum(steps)),
            }
        )
    return types.SimpleNamespace(
        bars=history,
        eligible_symbols=tuple(symbols),
        decision_time=index[-1],
    )


def _build(tmp_path: Path, members: list[tuple[str, str]]):
    finalists = []
    for team_id, source in members:
        bundle = tmp_path / team_id
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "strategy.py").write_text(source)
        finalists.append({"team_id": team_id, "centre": {}, "bundle": str(bundle)})
    manifest = {
        "schema_version": 1,
        "finalists": finalists,
        "risk_policy": {
            "risk_window_bars": 270,
            "risk_halflife_bars": 90,
            "risk_minimum_symbol_bars": 30,
            "risk_target": 0.10,
            "risk_minimum_scale": 0.10,
            "risk_maximum_scale": 3.0,
        },
    }
    ensemble_dir = Path("tournament/cup50v2/teams/ensemble-eq3")
    original = (ensemble_dir / "finalists.json").read_text() if (
        ensemble_dir / "finalists.json"
    ).exists() else None
    (ensemble_dir / "finalists.json").write_text(json.dumps(manifest))
    sys.path.insert(0, str(ensemble_dir))
    try:
        spec = importlib.util.spec_from_file_location(
            "ensemble_eq3_under_test", ensemble_dir / "strategy.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.build_strategy()
    finally:
        sys.path.remove(str(ensemble_dir))
        if original is None:
            (ensemble_dir / "finalists.json").unlink()
        else:
            (ensemble_dir / "finalists.json").write_text(original)


def test_a_loud_finalist_does_not_dominate_a_quiet_one(tmp_path: Path) -> None:
    """The property the whole desk rests on."""
    big = _member_source("a", {"AAAUSDT": 0.9, "BBBUSDT": -0.9})
    small = _member_source("b", {"AAAUSDT": 0.02, "BBBUSDT": -0.02})
    same = _member_source("c", {"CCCUSDT": 0.1, "BBBUSDT": -0.1})
    ensemble = _build(tmp_path, [("team-aa", big), ("team-bb", small), ("team-cc", same)])
    context = _context(["AAAUSDT", "BBBUSDT", "CCCUSDT"])

    book = ensemble.target_weights(context, seed=42)
    assert book, "the ensemble must emit when its members do"

    # Each member is sized to the same volatility target before averaging, so a member running 45x
    # the gross of another cannot carry 45x the weight. Without the pre-scaling the ratio of the
    # two members' contributions to AAAUSDT would be 0.9/0.02 = 45.
    scaled = {team: dict(last) for team, last in ensemble._last.items()}
    loud = abs(scaled["team-aa"]["AAAUSDT"])
    quiet = abs(scaled["team-bb"]["AAAUSDT"])
    assert 0.2 < quiet / loud < 5.0, (
        f"pre-scaling failed to equalise: loud={loud:.4f} quiet={quiet:.4f}"
    )


def test_a_holding_finalist_contributes_what_it_last_emitted(tmp_path: Path) -> None:
    steady = _member_source("a", {"AAAUSDT": 0.5})
    quitter = _member_source("b", {"BBBUSDT": 0.5}, holds_after=1)
    third = _member_source("c", {"CCCUSDT": 0.5})
    ensemble = _build(tmp_path, [("team-aa", steady), ("team-bb", quitter), ("team-cc", third)])
    context = _context(["AAAUSDT", "BBBUSDT", "CCCUSDT"])

    first = ensemble.target_weights(context, seed=1)
    assert "BBBUSDT" in first

    second = ensemble.target_weights(context, seed=1)   # team-bb now holds
    assert "BBBUSDT" in second, "a hold must not silently remove that member's book"
    assert second["BBBUSDT"] == pytest.approx(first["BBBUSDT"])


def test_the_ensemble_holds_only_when_every_finalist_holds(tmp_path: Path) -> None:
    members = [
        (f"team-{tag}", _member_source(tag, {"AAAUSDT": 0.5}, holds_after=1))
        for tag in ("aa", "bb", "cc")
    ]
    ensemble = _build(tmp_path, members)
    context = _context(["AAAUSDT", "BBBUSDT"])

    assert ensemble.target_weights(context, seed=1) is not None
    assert ensemble.target_weights(context, seed=1) is None


def test_exactly_three_finalists_are_required(tmp_path: Path) -> None:
    two = [("team-aa", _member_source("a", {"AAAUSDT": 0.5}))] * 2
    with pytest.raises(ValueError, match="exactly three finalists"):
        _build(tmp_path, two)

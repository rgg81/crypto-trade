"""Focused tests for the generic Amendment 0005 score boundary."""

from __future__ import annotations

import sys
import types

import pytest

from crypto_trade.tournament.generic_score_adapter_v5 import (
    GenericScoreBoundaryAdapter,
    ScoreBoundaryError,
)
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary


def _strategy(name: str, body: str) -> object:
    module = types.ModuleType(name)
    module.__dict__["score_boundary"] = score_boundary
    exec(
        f"""
class Strategy:
    def target_weights(self, context=None, *, seed=1):
{body}
""",
        module.__dict__,
    )
    sys.modules[name] = module
    return module.Strategy()


def test_identity_hook_returns_same_dictionary() -> None:
    scores = {"AUSDT": 1.0}
    assert score_boundary(scores) is scores


def test_adapter_captures_once_and_restores_direct_binding() -> None:
    strategy = _strategy(
        "_a5_capture",
        "        scores = {'AUSDT': 1.0, 'BUSDT': 2.0}\n"
        "        score_boundary(scores)\n"
        "        return {'BUSDT': 0.25}",
    )
    adapter = GenericScoreBoundaryAdapter(strategy)
    result = adapter.evaluate(
        lambda: strategy.target_weights(),
        scheduled=True,
        eligible_symbols=("AUSDT", "BUSDT"),
    )
    assert result.scores == {"AUSDT": 1.0, "BUSDT": 2.0}
    assert result.weights == {"BUSDT": 0.25}
    assert strategy.target_weights.__func__.__globals__["score_boundary"] is score_boundary


def test_adapter_rejects_bypass_and_post_boundary_mutation() -> None:
    bypass = _strategy("_a5_bypass", "        return {'AUSDT': 0.25}")
    with pytest.raises(ScoreBoundaryError, match="exactly once"):
        GenericScoreBoundaryAdapter(bypass).evaluate(
            lambda: bypass.target_weights(),
            scheduled=True,
            eligible_symbols=("AUSDT",),
        )
    mutation = _strategy(
        "_a5_mutation",
        "        scores = {'AUSDT': 1.0}\n"
        "        score_boundary(scores)\n"
        "        scores['AUSDT'] = 2.0\n"
        "        return {'AUSDT': 0.25}",
    )
    with pytest.raises(ScoreBoundaryError, match="mutated"):
        GenericScoreBoundaryAdapter(mutation).evaluate(
            lambda: mutation.target_weights(),
            scheduled=True,
            eligible_symbols=("AUSDT",),
        )


def test_adapter_rejects_unscheduled_capture() -> None:
    strategy = _strategy(
        "_a5_unscheduled",
        "        score_boundary({'AUSDT': 1.0})\n        return None",
    )
    with pytest.raises(ScoreBoundaryError, match="outside"):
        GenericScoreBoundaryAdapter(strategy).evaluate(
            lambda: strategy.target_weights(),
            scheduled=False,
            eligible_symbols=("AUSDT",),
        )

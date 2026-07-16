"""Synthetic evaluator-free tests for the organizer score worker boundary."""

from __future__ import annotations

import sys
import types
from collections.abc import Mapping

import pytest

import crypto_trade.tournament._score_worker_v2 as score_worker
from crypto_trade.tournament.score_adapters.team01_rdf_v1 import (
    ADAPTER_ID,
    Team01RdfScoreAdapter,
    build_adapter,
)


def _strategy_module(
    name: str, *, bypass_selector: bool = False
) -> tuple[types.ModuleType, object]:
    module = types.ModuleType(name)
    module.__dict__["BYPASS_SELECTOR"] = bypass_selector
    exec(
        """
REFERENCE_PARAMETERS = object()

def _combine_scores(left, right, *, penalty):
    return left

def _select_signed_tails(scored, *, tail_fraction, minimum_names_per_side):
    return list(scored[:1]), list(scored[-1:])

class ResidualDriftFundingStrategy:
    def __init__(self):
        self._parameters = REFERENCE_PARAMETERS

    def target_weights(self, context, *, seed):
        scored = [("AUSDT", -2.0, 0.5), ("BUSDT", 0.25, 0.75), ("CUSDT", 3.0, 1.0)]
        if not BYPASS_SELECTOR:
            _select_signed_tails(
                scored,
                tail_fraction=0.25,
                minimum_names_per_side=1,
            )
        return {"AUSDT": -0.4, "CUSDT": 0.4}
""",
        module.__dict__,
    )
    sys.modules[name] = module
    return module, module.ResidualDriftFundingStrategy()


def test_adapter_captures_exact_selector_input_and_restores_module() -> None:
    module, strategy = _strategy_module("_score_adapter_capture")
    original = module._select_signed_tails
    adapter = Team01RdfScoreAdapter(strategy)
    result = adapter.evaluate(
        lambda: strategy.target_weights(None, seed=20260801),
        eligible_symbols=("BTCUSDT", "AUSDT", "BUSDT", "CUSDT"),
    )
    assert result.weights == {"AUSDT": -0.4, "CUSDT": 0.4}
    assert [(item.symbol, item.score) for item in result.scores or ()] == [
        ("AUSDT", -2.0),
        ("BUSDT", 0.25),
        ("CUSDT", 3.0),
    ]
    assert module._select_signed_tails is original


def test_adapter_fails_closed_if_nonempty_targets_bypass_score_boundary() -> None:
    module, strategy = _strategy_module("_score_adapter_bypass", bypass_selector=True)
    original = module._select_signed_tails
    adapter = Team01RdfScoreAdapter(strategy)
    with pytest.raises(ValueError, match="without an observed score"):
        adapter.evaluate(
            lambda: strategy.target_weights(None, seed=20260801),
            eligible_symbols=("BTCUSDT", "AUSDT", "BUSDT", "CUSDT"),
        )
    assert module._select_signed_tails is original


def test_adapter_rejects_unknown_adapter_id() -> None:
    _module, strategy = _strategy_module("_score_adapter_identity")
    with pytest.raises(ValueError, match="unsupported"):
        build_adapter("unknown", strategy)


def test_score_worker_decision_returns_weights_and_full_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _module, strategy = _strategy_module("_score_worker_decision")
    historical = types.SimpleNamespace(strategy=strategy)
    state = score_worker._ScoreWorkerState(
        historical=historical,
        adapter=Team01RdfScoreAdapter(strategy),
    )

    def historical_decision(_state: object, _message: Mapping[str, object]):
        return strategy.target_weights(None, seed=20260801)

    monkeypatch.setattr(score_worker.frozen_worker, "_decision", historical_decision)
    weights, scores = score_worker._decision(
        state,
        {
            "type": "decision",
            "decision_time": "2023-06-30T00:00:00+00:00",
            "eligible_symbols": ["BTCUSDT", "AUSDT", "BUSDT", "CUSDT"],
            "bars": {},
            "funding": {},
        },
    )
    assert weights == {"AUSDT": -0.4, "CUSDT": 0.4}
    assert scores == {"AUSDT": -2.0, "BUSDT": 0.25, "CUSDT": 3.0}


def test_worker_initialization_requires_reviewed_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _module, strategy = _strategy_module("_score_worker_init")
    historical = types.SimpleNamespace(strategy=strategy)
    monkeypatch.setattr(
        score_worker.frozen_worker,
        "_initialise",
        lambda *_args, **_kwargs: historical,
    )
    state = score_worker._initialise(
        {"type": "init", "score_adapter_id": ADAPTER_ID},
        bundle=types.SimpleNamespace(),
        entrypoint="strategy.py",
    )
    assert state.historical is historical
    assert isinstance(state.adapter, Team01RdfScoreAdapter)

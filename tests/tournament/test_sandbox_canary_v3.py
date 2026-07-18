"""Real, evaluator-free Phase-0 canary for the V3 worker sandbox."""

from __future__ import annotations

from pathlib import Path

from crypto_trade.tournament import runner_v3, sandbox_canary_v3

ROOT = Path(__file__).resolve().parents[2]


def test_real_v3_sandbox_canary_completes_one_synthetic_round_trip(monkeypatch) -> None:
    def forbidden_market_operation(*_args, **_kwargs):
        raise AssertionError("the sandbox canary must not load or evaluate a market snapshot")

    monkeypatch.setattr(runner_v3, "_load_verified_snapshot", forbidden_market_operation)
    monkeypatch.setattr(
        runner_v3,
        "evaluate_base_and_double_cost",
        forbidden_market_operation,
    )

    result = sandbox_canary_v3.run_sandbox_canary(ROOT)

    assert result.decision_time == sandbox_canary_v3.CANARY_DECISION_TIME.isoformat()
    assert result.symbol == sandbox_canary_v3.CANARY_SYMBOL
    assert result.weight == sandbox_canary_v3.CANARY_WEIGHT
    assert len(result.source_bundle_sha256) == 64

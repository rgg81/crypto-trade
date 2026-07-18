"""Lean synthetic contract tests for the grandfathered Team 07 two-tape port."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_previous_path = list(sys.path)
_previous_modules = {
    name: sys.modules.get(name) for name in ("candidate_variant", "score_adapter_identity")
}
try:
    sys.path.insert(0, str(TEAM_DIR))
    _load_module("candidate_variant", TEAM_DIR / "candidate_variant.py")
    _load_module("score_adapter_identity", TEAM_DIR / "score_adapter_identity.py")
    STRATEGY = _load_module("team07_two_tape_incumbent_strategy", TEAM_DIR / "strategy.py")
finally:
    sys.path[:] = _previous_path
    for _name, _previous in _previous_modules.items():
        if _previous is None:
            sys.modules.pop(_name, None)
        else:
            sys.modules[_name] = _previous

DECISION = pd.Timestamp(0, unit="ns", tz="UTC") + pd.Timedelta(
    hours=STRATEGY.BAR_INTERVAL_HOURS * STRATEGY.REBALANCE_INTERVAL_BARS * 3000
)


def _context(*, include_future: bool = False) -> SimpleNamespace:
    symbol_count = 28
    open_times = pd.date_range(
        end=DECISION - pd.Timedelta(hours=8),
        periods=STRATEGY.HISTORY_RETURN_BARS + 1,
        freq="8h",
    )
    bars: dict[str, pd.DataFrame] = {}
    center = (symbol_count - 1) / 2.0
    for index in range(symbol_count):
        symbol = f"C{index:02d}USDT"
        loading = (index - center) / center
        closes = [100.0 + index]
        for step in range(STRATEGY.HISTORY_RETURN_BARS):
            common = 0.0025 * math.sin(step * 0.71)
            relative = 0.00070 * loading + 0.00012 * math.sin(
                step * 0.19 + index * 0.11
            )
            closes.append(closes[-1] * math.exp(common + relative))
        frame = pd.DataFrame({"open_time": open_times, "close": closes})
        if include_future:
            frame = pd.concat(
                [
                    frame,
                    pd.DataFrame(
                        {"open_time": [DECISION], "close": [closes[-1] * 1000.0]}
                    ),
                ],
                ignore_index=True,
            )
        bars[symbol] = frame
    return SimpleNamespace(
        decision_time=DECISION,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=tuple(sorted(bars)),
    )


def test_team07_factory_protocol_and_seed_contract() -> None:
    assert not inspect.signature(STRATEGY.build_strategy).parameters
    instance = STRATEGY.build_strategy()
    signature = inspect.signature(instance.target_weights)
    assert tuple(signature.parameters) == ("context", "seed")
    assert signature.parameters["seed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert instance.target_weights(_context(), seed=20260718)
    with pytest.raises(ValueError):
        instance.target_weights(_context(), seed=20260801)


def test_team07_is_deterministic_causal_and_within_exposure_limits() -> None:
    clean = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    repeated = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    future_appended = STRATEGY.build_strategy().target_weights(
        _context(include_future=True), seed=20260718
    )
    assert clean is not None and clean
    assert dict(clean) == dict(repeated or {}) == dict(future_appended or {})
    assert math.fsum(abs(value) for value in clean.values()) == pytest.approx(0.36)
    assert abs(math.fsum(clean.values())) <= 1e-12
    assert max(abs(value) for value in clean.values()) <= 0.025 + 1e-12
    assert sum(value > 0.0 for value in clean.values()) >= 8
    assert sum(value < 0.0 for value in clean.values()) >= 8


def test_team07_runtime_sources_have_no_forbidden_imports() -> None:
    forbidden = {"requests", "socket", "subprocess", "urllib", "httpx"}
    imported: set[str] = set()
    for filename in ("strategy.py", "candidate_variant.py", "score_adapter_identity.py"):
        tree = ast.parse((TEAM_DIR / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden)

"""Lean synthetic contract tests for the grandfathered Team 05 CRTR port."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import math
import sys
from collections import OrderedDict
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext

TEAM_DIR = Path(__file__).resolve().parent
START = pd.Timestamp("2020-01-01T00:00:00Z")
DECISION = pd.Timestamp("2020-07-17T00:00:00Z")


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
    STRATEGY = _load_module("team05_crtr_ab_dd_incumbent_strategy", TEAM_DIR / "strategy.py")
finally:
    sys.path[:] = _previous_path
    for _name, _previous in _previous_modules.items():
        if _previous is None:
            sys.modules.pop(_name, None)
        else:
            sys.modules[_name] = _previous


def _bar_frame(index: int, *, include_future: bool = False) -> pd.DataFrame:
    end = DECISION + pd.Timedelta(days=5) if include_future else DECISION - pd.Timedelta(hours=8)
    open_times = pd.date_range(START, end=end, freq="8h")
    centered = index - 9.5
    drift = centered * 0.000018
    closes = [
        100.0
        * math.exp(
            drift * step
            + 0.004 * math.sin(step / (5.0 + index % 4))
            + 0.0015 * math.cos(step / 2.7 + index)
        )
        for step in range(len(open_times))
    ]
    return pd.DataFrame({"open_time": open_times, "close": closes})


def _context(*, include_future: bool = False) -> DecisionContext:
    bars = OrderedDict(
        (f"C{index:02d}USDT", _bar_frame(index, include_future=include_future))
        for index in range(20)
    )
    return DecisionContext(
        decision_time=DECISION,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
        eligible_symbols=tuple(bars),
    )


def test_team05_factory_protocol_and_seed_contract() -> None:
    assert not inspect.signature(STRATEGY.build_strategy).parameters
    instance = STRATEGY.build_strategy()
    signature = inspect.signature(instance.target_weights)
    assert tuple(signature.parameters) == ("context", "seed")
    assert signature.parameters["seed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert instance.target_weights(_context(), seed=20260718)
    with pytest.raises(ValueError):
        instance.target_weights(_context(), seed=20260801)


def test_team05_is_deterministic_causal_and_within_exposure_limits() -> None:
    clean = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    repeated = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    future_appended = STRATEGY.build_strategy().target_weights(
        _context(include_future=True), seed=20260718
    )
    assert clean is not None and clean
    assert dict(clean) == dict(repeated or {}) == dict(future_appended or {})
    assert math.fsum(abs(value) for value in clean.values()) <= 0.6 + 1e-12
    assert abs(math.fsum(clean.values())) <= 0.08 + 1e-12
    assert max(abs(value) for value in clean.values()) <= 0.04 + 1e-12
    assert any(value > 0.0 for value in clean.values())
    assert any(value < 0.0 for value in clean.values())


def test_team05_runtime_sources_have_no_forbidden_imports() -> None:
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

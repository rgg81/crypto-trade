"""Lean synthetic contract tests for the grandfathered Team 09 DRP port."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

TEAM_DIR = Path(__file__).resolve().parent
DECISION = pd.Timestamp("2023-01-02T00:00:00Z")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_previous_path = list(sys.path)
_previous_hook = sys.modules.get("score_adapter_identity")
try:
    sys.path.insert(0, str(TEAM_DIR))
    _load_module("score_adapter_identity", TEAM_DIR / "score_adapter_identity.py")
    STRATEGY = _load_module("team09_drp_incumbent_strategy", TEAM_DIR / "strategy.py")
finally:
    sys.path[:] = _previous_path
    if _previous_hook is None:
        sys.modules.pop("score_adapter_identity", None)
    else:
        sys.modules["score_adapter_identity"] = _previous_hook


def _context(*, mutate_ignored_prefix: bool = False) -> SimpleNamespace:
    symbol_count = 24
    periods = 310
    symbols = tuple(f"C{index:02d}USDT" for index in range(symbol_count))
    times = pd.date_range(end=DECISION - pd.Timedelta(hours=8), periods=periods, freq="8h")
    step = np.arange(periods, dtype=float)
    midpoint = (symbol_count - 1) / 2.0
    common = 0.00055 * np.sin(step / 9.0) + 0.00020 * np.cos(step / 23.0)
    bars: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(symbols):
        relative_drift = 0.00042 * (index - midpoint) / midpoint
        idiosyncratic = 0.00002 * np.sin(step / 17.0 + index * 0.31)
        increments = common + relative_drift + idiosyncratic
        closes = np.exp(math.log(100.0 + index) + np.cumsum(increments))
        if mutate_ignored_prefix:
            closes = closes.copy()
            closes[0] *= 1000.0
        bars[symbol] = pd.DataFrame(
            {"open_time": times, "symbol": symbol, "close": closes}
        )
    return SimpleNamespace(
        decision_time=DECISION,
        eligible_symbols=symbols,
        bars=bars,
        funding=pd.DataFrame(),
        auxiliary={},
    )


def test_team09_factory_protocol_and_seed_contract() -> None:
    assert not inspect.signature(STRATEGY.build_strategy).parameters
    instance = STRATEGY.build_strategy()
    signature = inspect.signature(instance.target_weights)
    assert tuple(signature.parameters) == ("context", "seed")
    assert signature.parameters["seed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert instance.target_weights(_context(), seed=20260718)
    with pytest.raises(ValueError):
        instance.target_weights(_context(), seed=20260801)


def test_team09_is_deterministic_causal_and_within_exposure_limits() -> None:
    clean = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    repeated = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    prefix_changed = STRATEGY.build_strategy().target_weights(
        _context(mutate_ignored_prefix=True), seed=20260718
    )
    assert clean is not None and clean
    assert dict(clean) == dict(repeated or {}) == dict(prefix_changed or {})
    assert math.fsum(abs(value) for value in clean.values()) < 0.2
    assert abs(math.fsum(clean.values())) <= 1e-12
    assert max(abs(value) for value in clean.values()) <= 0.015 + 1e-12
    assert 6 <= sum(value > 0.0 for value in clean.values()) <= 8
    assert 6 <= sum(value < 0.0 for value in clean.values()) <= 8


def test_team09_runtime_sources_have_no_forbidden_imports() -> None:
    forbidden = {"requests", "socket", "subprocess", "urllib", "httpx"}
    imported: set[str] = set()
    for filename in ("strategy.py", "score_adapter_identity.py"):
        tree = ast.parse((TEAM_DIR / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden)

"""Lean synthetic contract tests for the grandfathered Team 04 UTC port."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.tournament.protocol import DecisionContext

TEAM_DIR = Path(__file__).resolve().parent
DECISION = pd.Timestamp("2023-01-05T00:00:00Z")
INTERVAL = pd.Timedelta(hours=8)
SPEC = importlib.util.spec_from_file_location(
    "team04_utc_incumbent_strategy", TEAM_DIR / "strategy.py"
)
assert SPEC is not None and SPEC.loader is not None
STRATEGY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STRATEGY
SPEC.loader.exec_module(STRATEGY)


def _context(*, include_future: bool = False) -> DecisionContext:
    symbols = tuple(f"C{index:02d}USDT" for index in range(40))
    cutoff = DECISION - INTERVAL
    expected = STRATEGY._expected_open_times(
        cutoff, STRATEGY._REFERENCE.history_return_bars
    )
    bars: dict[str, pd.DataFrame] = {}
    funding_rows: list[dict[str, object]] = []
    midpoint = (len(symbols) - 1) / 2.0
    for index, symbol in enumerate(symbols):
        loading = (index - midpoint) / midpoint
        price = 100.0 + index
        rows: list[dict[str, object]] = []
        for step, open_time in enumerate(expected):
            move = 0.001 * loading + (0.0003 + 0.00002 * index) * math.sin(
                0.47 * step + 0.19 * index
            )
            price *= math.exp(move)
            rows.append(
                {
                    "symbol": symbol,
                    "open_time": open_time,
                    "close_time": open_time + INTERVAL,
                    "close": price,
                }
            )
        if include_future:
            rows.append(
                {
                    "symbol": symbol,
                    "open_time": cutoff,
                    "close_time": DECISION,
                    "close": price * 1000.0,
                }
            )
        bars[symbol] = pd.DataFrame(rows)
        rate = -loading * 0.00004
        start = DECISION - pd.Timedelta(days=7)
        for event in range(21):
            funding_rows.append(
                {
                    "funding_time": start + event * INTERVAL,
                    "symbol": symbol,
                    "funding_rate": rate,
                }
            )
    return DecisionContext(
        decision_time=DECISION,
        bars=bars,
        funding=pd.DataFrame(funding_rows),
        auxiliary={},
        eligible_symbols=symbols,
    )


def test_team04_factory_protocol_and_seed_contract() -> None:
    assert not inspect.signature(STRATEGY.build_strategy).parameters
    instance = STRATEGY.build_strategy()
    signature = inspect.signature(instance.target_weights)
    assert tuple(signature.parameters) == ("context", "seed")
    assert signature.parameters["seed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert instance.target_weights(_context(), seed=20260718)
    with pytest.raises(ValueError):
        instance.target_weights(_context(), seed=20260801)


def test_team04_is_deterministic_causal_and_within_exposure_limits() -> None:
    instance = STRATEGY.build_strategy()
    clean = instance.target_weights(_context(), seed=20260718)
    repeated = STRATEGY.build_strategy().target_weights(_context(), seed=20260718)
    future_appended = STRATEGY.build_strategy().target_weights(
        _context(include_future=True), seed=20260718
    )
    assert isinstance(clean, dict) and clean
    assert clean == repeated == future_appended
    assert math.fsum(abs(value) for value in clean.values()) <= 0.6 + 1e-12
    assert abs(math.fsum(clean.values())) <= 1e-12
    assert max(abs(value) for value in clean.values()) <= 0.04 + 1e-12
    assert any(value > 0.0 for value in clean.values())
    assert any(value < 0.0 for value in clean.values())


def test_team04_runtime_sources_have_no_forbidden_imports() -> None:
    forbidden = {"requests", "socket", "subprocess", "urllib", "httpx"}
    imported: set[str] = set()
    tree = ast.parse((TEAM_DIR / "strategy.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint(forbidden)

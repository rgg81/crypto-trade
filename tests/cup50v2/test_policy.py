"""The config is the contract: every tunable must reach behaviour from the file, not a literal.

CUP-50 restated its caps, costs and score weights in ``config.toml``, in a frozen dictionary, and
again as literals inside the scorer and the evaluator, and only the literals were load-bearing.  A
fixture that holds a dimension constant cannot detect a change along it, so each test here *moves*
one number in a throwaway config and requires the observable to move with it.
"""

from __future__ import annotations

import json
import math
import re
import tomllib
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.cup50v2.config import DEFAULT_CONFIG_PATH, active_policy, load_config
from crypto_trade.cup50v2.neighbourhood import Dimension, generate_neighbourhood
from crypto_trade.cup50v2.replay import ExecutionConfig
from crypto_trade.cup50v2.scoring import CellScore, combine_costs, round_half_even, score_cell
from crypto_trade.cup50v2.trials import TrialBinding, register_trial

DIGEST = "a" * 64


def _config(tmp_path: Path, **overrides: object) -> Path:
    """Write the canonical config with a handful of dotted keys replaced."""
    raw = tomllib.loads(DEFAULT_CONFIG_PATH.read_text())
    for dotted, value in overrides.items():
        table, _, key = dotted.rpartition(".")
        target = raw
        for part in table.split("."):
            target = target[part]
        target[key] = value
    lines = []
    for section, body in raw.items():
        if not isinstance(body, dict):
            lines.append(f"{section} = {json.dumps(body)}")
    for section, body in raw.items():
        if isinstance(body, dict):
            lines.append(f"\n[{section}]")
            for key, value in body.items():
                rendered = json.dumps(value)
                key_text = f'"{key}"' if not key.isidentifier() else key
                lines.append(f"{key_text} = {rendered}")
    path = tmp_path / "config.toml"
    path.write_text("\n".join(lines) + "\n")
    return path


def _returns(days: int = 60) -> pd.DataFrame:
    """A path that is non-degenerate along every dimension the cell scores.

    A flat or monotone path silently zeroes the drawdown, utilisation and concentration terms, and a
    fixture that holds those at zero cannot tell a live penalty from a deleted one.  So this path
    draws down, idles for six days in ten, spikes every seventeenth day, and lands mid-range rather
    than saturating the squash.
    """
    index = pd.date_range("2024-02-01T00:00:00Z", periods=days * 3, freq="8h")
    net, gross_exposure = [], []
    for bar in range(days * 3):
        day = bar // 3
        value = 0.004 * math.sin(day / 3.0) + 0.0005
        if day % 17 == 0:
            value *= 6.0
        net.append(value / 3.0)
        gross_exposure.append(0.0 if day % 10 >= 4 else 0.9)
    return pd.DataFrame(
        {"net_return": net, "gross_return": net, "gross_exposure": gross_exposure}, index=index
    )


def test_the_canonical_config_round_trips_through_the_helper(tmp_path: Path) -> None:
    """The rewriter must reproduce the shipped policy, or every test below proves nothing."""
    assert load_config(_config(tmp_path)).policy == active_policy()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("scoring.drawdown_penalty", 2.0),
        ("scoring.underdeployment_penalty", 5.0),
        ("scoring.concentration_penalty", 5.0),
        ("scoring.squash_scale", 1.0),
        ("scoring.volatility_reference", 5.0),
        ("scoring.activity_reference", 1.0),
        ("scoring.activity_exposure_floor", 0.95),
        ("scoring.concentration_threshold", 0.01),
        ("scoring.concentration_top_days", 1),
    ],
)
def test_moving_a_scoring_constant_moves_the_cell(tmp_path: Path, key: str, value: float) -> None:
    window = (pd.Timestamp("2024-02-01T00:00:00Z"), pd.Timestamp("2024-04-01T00:00:00Z"))
    returns = _returns()
    baseline = score_cell(returns, *window)
    # Guard the fixture itself: every penalised term has to be live, or a deleted penalty
    # would pass this test unnoticed.
    assert baseline.drawdown > 0.0 and baseline.volatility > 0.0
    assert 0.0 < baseline.activity < 1.0
    assert 0.0 < baseline.utilization < 1.0
    assert baseline.concentration > 0.25
    assert 0.0 < baseline.q < 100.0
    moved = score_cell(
        returns,
        *window,
        policy=load_config(_config(tmp_path, **{key: value})).policy.scoring,
    )
    assert moved != baseline, key


def test_moving_the_cost_weights_moves_the_cost_aggregate(tmp_path: Path) -> None:
    cells = {
        cost: CellScore(q, 0.0, 0.0, 0.2, 1.0, 1.0, 0.2, 0.0)
        for cost, q in ((1, 90.0), (2, 50.0), (3, 10.0))
    }
    baseline = combine_costs(cells)
    moved = combine_costs(
        cells,
        policy=load_config(
            _config(tmp_path, **{"scoring.cost_weights": [0.5, 0.3, 0.2]})
        ).policy.scoring,
    )
    assert baseline == pytest.approx(0.45 * 90 + 0.35 * 50 + 0.20 * 10)
    assert moved == pytest.approx(0.5 * 90 + 0.3 * 50 + 0.2 * 10)


def test_moving_the_rounding_places_moves_the_rounding(tmp_path: Path) -> None:
    policy = load_config(_config(tmp_path, **{"scoring.rounding_places": 2})).policy.scoring
    assert round_half_even(1.234567) == 1.234567
    assert round_half_even(1.234567, policy=policy) == 1.23


@pytest.mark.parametrize(
    ("key", "field", "value"),
    [
        ("execution.taker_fee_bps_per_side", "taker_fee_bps_per_side", 12.5),
        ("execution.slippage_bps_per_side", "slippage_bps_per_side", 7.5),
        ("execution.max_symbol_exposure", "max_symbol_exposure", 0.35),
        ("execution.max_gross_exposure", "max_gross_exposure", 0.75),
        ("execution.max_bar_participation", "max_bar_participation", 0.005),
        ("execution.initial_equity", "initial_equity", 250_000.0),
        ("risk_unit.target_annualized_volatility", "risk_target", 0.25),
        ("risk_unit.minimum_scale", "risk_minimum_scale", 0.05),
        ("research.strategy_history_days", "strategy_history_days", 365),
    ],
)
def test_moving_an_execution_constant_moves_the_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, field: str, value: float
) -> None:
    """``ExecutionConfig()`` must resolve against the active config, not a literal default."""
    path = _config(tmp_path, **{key: value})
    monkeypatch.setattr(
        "crypto_trade.cup50v2.replay.active_policy", lambda: load_config(path).policy
    )
    assert getattr(ExecutionConfig(), field) == value


def test_moving_the_dimension_ceiling_moves_the_neighbourhood(tmp_path: Path) -> None:
    centre = {name: 10.0 for name in ("a", "b", "c")}
    dimensions = tuple(Dimension(name=name, kind="integer") for name in centre)
    generate_neighbourhood(centre, dimensions)
    tightened = load_config(_config(tmp_path, **{"research.maximum_dimensions": 2})).policy.research
    with pytest.raises(ValueError, match="at most 2 tunable dimensions"):
        generate_neighbourhood(centre, dimensions, policy=tightened)


def test_moving_the_probe_step_moves_the_declared_points(tmp_path: Path) -> None:
    centre = {"lookback_bars": 100.0}
    dimensions = (Dimension(name="lookback_bars", kind="integer"),)
    baseline = generate_neighbourhood(centre, dimensions).points
    widened = load_config(
        _config(tmp_path, **{"research.neighbourhood_scale_step": 2.0})
    ).policy.research
    moved = generate_neighbourhood(centre, dimensions, policy=widened).points
    assert baseline != moved
    assert moved[-1]["lookback_bars"] == 800.0


def test_moving_the_trial_budget_moves_the_ledger_ceiling(tmp_path: Path) -> None:
    journal = tmp_path / "trials.jsonl"
    policy = load_config(_config(tmp_path, **{"research.official_trial_budget": 2})).policy.research

    def binding(index: int) -> TrialBinding:
        return TrialBinding(
            team_id="team-01",
            trial_id=f"t{index}",
            kind="official",
            promoteable=True,
            source_sha256=DIGEST,
            parameters={"lookback_bars": 10.0},
            risk_policy_sha256=DIGEST,
            seed=1,
            data_sha256=DIGEST,
            config_sha256=DIGEST,
            scorer_sha256=DIGEST,
            purpose="budget ceiling",
        )

    register_trial(journal, binding(1), policy=policy)
    register_trial(journal, binding(2), policy=policy)
    with pytest.raises(ValueError, match="exhausted its 2 official trials"):
        register_trial(journal, binding(3), policy=policy)


def test_no_scorer_constant_survives_as_a_literal() -> None:
    """A number that reappears in the source is a number the config can no longer govern."""
    source = Path("src/crypto_trade/cup50v2/scoring.py").read_text()
    banned = (r"0\.85", r"0\.15", r"0\.50 \*", r"\{1: 0\.20", r"\(0\.40, 0\.25")
    for pattern in banned:
        assert not re.search(pattern, source), pattern

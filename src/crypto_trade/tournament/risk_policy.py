"""Strict declarative risk-policy contract for Top-40 V2.

The central evaluator owns portfolio state and execution.  This module deliberately contains no
market-data access and cannot manufacture fills; it only validates frozen policy parameters and
computes deterministic boundary decisions for the evaluator to apply at the next open.
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

_POLICY_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")


@dataclasses.dataclass(frozen=True)
class VolatilityTarget:
    enabled: bool
    lookback_days: int
    annualized_target: float
    minimum_scale: float
    maximum_scale: float


@dataclasses.dataclass(frozen=True)
class DrawdownBrake:
    drawdown: float
    gross_scale: float


@dataclasses.dataclass(frozen=True)
class PositionStop:
    enabled: bool
    loss_fraction: float
    cooldown_bars: int


@dataclasses.dataclass(frozen=True)
class TimeStop:
    enabled: bool
    maximum_holding_bars: int
    cooldown_bars: int


@dataclasses.dataclass(frozen=True)
class TurnoverLimit:
    enabled: bool
    maximum_one_way_turnover: float


@dataclasses.dataclass(frozen=True)
class SideScaling:
    long_scale: float
    short_scale: float


@dataclasses.dataclass(frozen=True)
class RiskPolicy:
    schema_version: int
    policy_id: str
    same_boundary_reentry: bool
    volatility_target: VolatilityTarget
    drawdown_brakes: tuple[DrawdownBrake, ...]
    position_stop: PositionStop
    time_stop: TimeStop
    turnover_limit: TurnoverLimit
    side_scaling: SideScaling

    @property
    def enabled(self) -> bool:
        return bool(
            self.volatility_target.enabled
            or self.drawdown_brakes
            or self.position_stop.enabled
            or self.time_stop.enabled
            or self.turnover_limit.enabled
            or self.side_scaling.long_scale < 1.0
            or self.side_scaling.short_scale < 1.0
        )


@dataclasses.dataclass(frozen=True)
class BoundaryRiskDecision:
    """Pure risk instruction; the evaluator remains responsible for fills and costs."""

    gross_scale: float
    stopped_symbols: tuple[str, ...]
    timed_out_symbols: tuple[str, ...]
    blocked_symbols: tuple[str, ...]
    maximum_one_way_turnover: float | None
    reasons: tuple[str, ...]


def _exact_object(raw: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping) or set(raw) != expected:
        missing = sorted(expected - set(raw)) if isinstance(raw, Mapping) else sorted(expected)
        extra = sorted(set(raw) - expected) if isinstance(raw, Mapping) else []
        raise ValueError(f"{label} has invalid keys; missing={missing}, extra={extra}")
    return raw


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a JSON boolean")
    return value


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def risk_policy_from_dict(raw: Mapping[str, Any]) -> RiskPolicy:
    """Parse a complete frozen policy and reject implicit or ambiguous defaults."""
    root = _exact_object(
        raw,
        {
            "schema_version",
            "policy_id",
            "same_boundary_reentry",
            "volatility_target",
            "drawdown_brakes",
            "position_stop",
            "time_stop",
            "turnover_limit",
            "side_scaling",
        },
        "risk policy",
    )
    if root["schema_version"] != 1:
        raise ValueError("risk policy schema_version must be 1")
    policy_id = root["policy_id"]
    if not isinstance(policy_id, str) or _POLICY_ID.fullmatch(policy_id) is None:
        raise ValueError("policy_id must be lowercase kebab-case and at most 64 characters")

    raw_volatility = _exact_object(
        root["volatility_target"],
        {"enabled", "lookback_days", "annualized_target", "minimum_scale", "maximum_scale"},
        "volatility_target",
    )
    volatility = VolatilityTarget(
        enabled=_boolean(raw_volatility["enabled"], "volatility_target.enabled"),
        lookback_days=_integer(
            raw_volatility["lookback_days"], "volatility_target.lookback_days", minimum=2
        ),
        annualized_target=_finite(
            raw_volatility["annualized_target"], "volatility_target.annualized_target"
        ),
        minimum_scale=_finite(
            raw_volatility["minimum_scale"], "volatility_target.minimum_scale"
        ),
        maximum_scale=_finite(
            raw_volatility["maximum_scale"], "volatility_target.maximum_scale"
        ),
    )
    if volatility.annualized_target <= 0:
        raise ValueError("volatility_target.annualized_target must be positive")
    if not 0 <= volatility.minimum_scale <= volatility.maximum_scale <= 1:
        raise ValueError("volatility target scales must satisfy 0 <= minimum <= maximum <= 1")

    raw_brakes = root["drawdown_brakes"]
    if not isinstance(raw_brakes, Sequence) or isinstance(raw_brakes, (str, bytes)):
        raise ValueError("drawdown_brakes must be a JSON array")
    brakes: list[DrawdownBrake] = []
    for index, raw_brake in enumerate(raw_brakes):
        item = _exact_object(raw_brake, {"drawdown", "gross_scale"}, f"drawdown_brakes[{index}]")
        brake = DrawdownBrake(
            drawdown=_finite(item["drawdown"], f"drawdown_brakes[{index}].drawdown"),
            gross_scale=_finite(
                item["gross_scale"], f"drawdown_brakes[{index}].gross_scale"
            ),
        )
        if not 0 < brake.drawdown < 1 or not 0 <= brake.gross_scale <= 1:
            raise ValueError("drawdown brakes require drawdown in (0,1) and scale in [0,1]")
        brakes.append(brake)
    if any(
        current.drawdown <= previous.drawdown
        or current.gross_scale > previous.gross_scale
        for previous, current in zip(brakes, brakes[1:], strict=False)
    ):
        raise ValueError("drawdown brakes must increase in threshold and not increase gross scale")

    raw_position = _exact_object(
        root["position_stop"],
        {"enabled", "loss_fraction", "cooldown_bars"},
        "position_stop",
    )
    position_stop = PositionStop(
        enabled=_boolean(raw_position["enabled"], "position_stop.enabled"),
        loss_fraction=_finite(raw_position["loss_fraction"], "position_stop.loss_fraction"),
        cooldown_bars=_integer(raw_position["cooldown_bars"], "position_stop.cooldown_bars"),
    )
    if not 0 < position_stop.loss_fraction < 1:
        raise ValueError("position_stop.loss_fraction must be in (0,1)")

    raw_time = _exact_object(
        root["time_stop"],
        {"enabled", "maximum_holding_bars", "cooldown_bars"},
        "time_stop",
    )
    time_stop = TimeStop(
        enabled=_boolean(raw_time["enabled"], "time_stop.enabled"),
        maximum_holding_bars=_integer(
            raw_time["maximum_holding_bars"], "time_stop.maximum_holding_bars", minimum=1
        ),
        cooldown_bars=_integer(raw_time["cooldown_bars"], "time_stop.cooldown_bars"),
    )

    raw_turnover = _exact_object(
        root["turnover_limit"],
        {"enabled", "maximum_one_way_turnover"},
        "turnover_limit",
    )
    turnover = TurnoverLimit(
        enabled=_boolean(raw_turnover["enabled"], "turnover_limit.enabled"),
        maximum_one_way_turnover=_finite(
            raw_turnover["maximum_one_way_turnover"],
            "turnover_limit.maximum_one_way_turnover",
        ),
    )
    if not 0 < turnover.maximum_one_way_turnover <= 2:
        raise ValueError("maximum_one_way_turnover must be in (0,2]")

    raw_scaling = _exact_object(
        root["side_scaling"], {"long_scale", "short_scale"}, "side_scaling"
    )
    side_scaling = SideScaling(
        long_scale=_finite(raw_scaling["long_scale"], "side_scaling.long_scale"),
        short_scale=_finite(raw_scaling["short_scale"], "side_scaling.short_scale"),
    )
    if not 0 <= side_scaling.long_scale <= 1 or not 0 <= side_scaling.short_scale <= 1:
        raise ValueError("side scales must be in [0,1]")

    return RiskPolicy(
        schema_version=1,
        policy_id=policy_id,
        same_boundary_reentry=_boolean(
            root["same_boundary_reentry"], "same_boundary_reentry"
        ),
        volatility_target=volatility,
        drawdown_brakes=tuple(brakes),
        position_stop=position_stop,
        time_stop=time_stop,
        turnover_limit=turnover,
        side_scaling=side_scaling,
    )


def load_risk_policy(path: str | Path) -> RiskPolicy:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid risk policy: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("risk policy root must be a JSON object")
    return risk_policy_from_dict(raw)


def drawdown_gross_scale(policy: RiskPolicy, current_drawdown: float) -> float:
    """Return the most conservative triggered drawdown scale."""
    drawdown = _finite(current_drawdown, "current_drawdown")
    if not 0 <= drawdown <= 1:
        raise ValueError("current_drawdown must be in [0,1]")
    scale = 1.0
    for brake in policy.drawdown_brakes:
        if drawdown >= brake.drawdown:
            scale = min(scale, brake.gross_scale)
    return scale


def volatility_gross_scale(policy: RiskPolicy, annualized_volatility: float | None) -> float:
    """Return a no-leverage volatility scale from past realized volatility."""
    target = policy.volatility_target
    if not target.enabled:
        return 1.0
    if annualized_volatility is None:
        return target.minimum_scale
    volatility = _finite(annualized_volatility, "annualized_volatility")
    if volatility <= 0:
        return target.maximum_scale
    raw_scale = target.annualized_target / volatility
    return min(target.maximum_scale, max(target.minimum_scale, raw_scale))


def boundary_risk_decision(
    policy: RiskPolicy,
    *,
    current_drawdown: float,
    annualized_volatility: float | None,
    position_returns: Mapping[str, float],
    holding_bars: Mapping[str, int],
    cooldown_bars_remaining: Mapping[str, int],
) -> BoundaryRiskDecision:
    """Compute boundary triggers without executing or pricing any order."""
    symbols = set(position_returns) | set(holding_bars) | set(cooldown_bars_remaining)
    stopped: set[str] = set()
    timed_out: set[str] = set()
    blocked = {
        symbol
        for symbol, remaining in cooldown_bars_remaining.items()
        if _integer(remaining, f"cooldown_bars_remaining[{symbol}]") > 0
    }
    for symbol in symbols:
        if policy.position_stop.enabled:
            observed_return = _finite(
                position_returns.get(symbol, 0.0), f"position_return[{symbol}]"
            )
            if observed_return <= -policy.position_stop.loss_fraction:
                stopped.add(symbol)
        if policy.time_stop.enabled:
            age = _integer(holding_bars.get(symbol, 0), f"holding_bars[{symbol}]")
            if age >= policy.time_stop.maximum_holding_bars:
                timed_out.add(symbol)
    if not policy.same_boundary_reentry:
        blocked |= stopped | timed_out
    drawdown_scale = drawdown_gross_scale(policy, current_drawdown)
    volatility_scale = volatility_gross_scale(policy, annualized_volatility)
    reasons: list[str] = []
    if drawdown_scale < 1:
        reasons.append("drawdown_brake")
    if volatility_scale < 1:
        reasons.append("volatility_target")
    if stopped:
        reasons.append("position_stop")
    if timed_out:
        reasons.append("time_stop")
    if blocked:
        reasons.append("cooldown_or_reentry_block")
    return BoundaryRiskDecision(
        gross_scale=min(drawdown_scale, volatility_scale),
        stopped_symbols=tuple(sorted(stopped)),
        timed_out_symbols=tuple(sorted(timed_out)),
        blocked_symbols=tuple(sorted(blocked)),
        maximum_one_way_turnover=(
            policy.turnover_limit.maximum_one_way_turnover
            if policy.turnover_limit.enabled
            else None
        ),
        reasons=tuple(reasons),
    )

"""Continuous causal CUP-50 v2 replay and execution."""

from __future__ import annotations

import dataclasses
import hashlib
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.availability import UnavailabilityWindow, unavailable_symbols
from crypto_trade.cup50v2.common_risk import common_risk_scalars
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2
from crypto_trade.cup50v2.snapshot import Snapshot
from crypto_trade.cup50v2.universe import members_at

REBALANCE_COLUMN = "__cup50v2_rebalance__"
_NOTIONAL_DUST_USD = 1e-9
FORBIDDEN_CONTEXT_COLUMNS = frozenset(
    {
        "fill",
        "fills",
        "cost",
        "costs",
        "fee",
        "fees",
        "slippage",
        "position",
        "positions",
        "quantity",
        "equity",
        "pnl",
        "profit",
        "net_return",
        "mark_price",
    }
)


class StrategyFailureError(RuntimeError):
    """A source, target, or parameter failure attributable to the candidate bundle."""


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutionConfig:
    interval_hours: int = 8
    initial_equity: float = 100_000.0
    taker_fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.5
    max_gross_exposure: float = 1.0
    max_abs_net_exposure: float = 1.0
    max_symbol_exposure: float = 0.20
    max_bar_participation: float = 0.001
    risk_target: float = 0.10
    risk_lookback_days: int = 90
    risk_minimum_scale: float = 0.20
    risk_maximum_scale: float = 3.0
    strategy_history_days: int = 180

    def validate(self) -> None:
        positive = (
            self.interval_hours,
            self.initial_equity,
            self.max_gross_exposure,
            self.max_abs_net_exposure,
            self.max_symbol_exposure,
            self.max_bar_participation,
            self.risk_target,
            self.risk_lookback_days,
            self.risk_minimum_scale,
            self.risk_maximum_scale,
            self.strategy_history_days,
        )
        if not all(math.isfinite(float(value)) and float(value) > 0 for value in positive):
            raise ValueError("execution configuration must contain positive finite values")
        if self.taker_fee_bps_per_side < 0 or self.slippage_bps_per_side < 0:
            raise ValueError("execution costs cannot be negative")
        if self.risk_minimum_scale > self.risk_maximum_scale:
            raise ValueError("risk scalar minimum exceeds maximum")


@dataclasses.dataclass(frozen=True, slots=True)
class ReplayState:
    decision_time: pd.Timestamp
    equity: float
    quantities: Mapping[str, float]


@dataclasses.dataclass(frozen=True, slots=True)
class EvaluationResultV2:
    returns: pd.DataFrame
    events: pd.DataFrame
    final_state: ReplayState


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateReplay:
    raw_targets: pd.DataFrame
    risk_scalars: pd.Series
    calibration: EvaluationResultV2
    costs: Mapping[int, EvaluationResultV2]


def decision_grid(
    start: pd.Timestamp, end: pd.Timestamp, *, interval_hours: int = 8
) -> tuple[pd.Timestamp, ...]:
    first, stop = pd.Timestamp(start), pd.Timestamp(end)
    if first.tzinfo is None or stop.tzinfo is None:
        raise ValueError("decision bounds must be timezone-aware UTC")
    first, stop = first.tz_convert("UTC"), stop.tz_convert("UTC")
    if first >= stop:
        return ()
    return tuple(pd.date_range(first, stop, freq=f"{interval_hours}h", inclusive="left"))


def load_strategy_module(path: str | Path) -> ModuleType:
    source = Path(path)
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"cannot load strategy source {source}")
    module = ModuleType(f"cup50v2_candidate_{hashlib.sha256(source.read_bytes()).hexdigest()[:16]}")
    module.__file__ = str(source)
    code = compile(source.read_bytes(), str(source), "exec", dont_inherit=True)
    exec(code, module.__dict__)
    return module


def strategy_from_module(module: ModuleType) -> TargetStrategyV2:
    factory = getattr(module, "build_strategy", None)
    if not callable(factory):
        raise ValueError("candidate must define callable build_strategy()")
    strategy = factory()
    if not callable(getattr(strategy, "target_weights", None)):
        raise ValueError("build_strategy() did not return a TargetStrategyV2")
    return strategy


def apply_strategy_parameters(strategy: TargetStrategyV2, parameters: Mapping[str, object]) -> None:
    """Apply only declared numeric strategy attributes, preserving integer dimensions."""
    for name, raw_value in parameters.items():
        if not hasattr(strategy, name):
            raise ValueError(f"candidate parameter is not a strategy attribute: {name}")
        current = getattr(strategy, name)
        if isinstance(current, bool) or not isinstance(current, (int, float)):
            raise ValueError(f"candidate parameter is not numeric: {name}")
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError(f"candidate parameter is non-finite: {name}")
        if isinstance(current, int):
            if not value.is_integer():
                raise ValueError(f"integer candidate parameter is fractional: {name}")
            setattr(strategy, name, int(value))
        else:
            setattr(strategy, name, value)


def _normalise_bars(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"open_time", "close_time", "symbol", "open", "close", "quote_volume"}
    missing = required - set(bars)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    result = bars.copy()
    result["open_time"] = pd.to_datetime(result["open_time"], utc=True)
    result["close_time"] = pd.to_datetime(result["close_time"], utc=True)
    if result.duplicated(["open_time", "symbol"]).any():
        raise ValueError("duplicate transaction bars")
    for column in ("open", "close", "quote_volume"):
        result[column] = pd.to_numeric(result[column], errors="raise")
        if not np.isfinite(result[column].to_numpy(dtype=float)).all():
            raise ValueError(f"bars contain non-finite {column}")
    if (result[["open", "close"]] <= 0).any().any() or (result["quote_volume"] < 0).any():
        raise ValueError("bars contain invalid prices or volume")
    return result.sort_values(["open_time", "symbol"], ignore_index=True)


def _normalise_funding(funding: pd.DataFrame) -> pd.DataFrame:
    required = {"funding_time", "symbol", "funding_rate", "mark_price"}
    missing = required - set(funding)
    if missing:
        raise ValueError(f"funding missing columns: {sorted(missing)}")
    columns = sorted(required | ({"settlement_time"} if "settlement_time" in funding else set()))
    result = funding.loc[:, columns].copy()
    result["funding_time"] = pd.to_datetime(result["funding_time"], utc=True)
    if "settlement_time" in result:
        result["settlement_time"] = pd.to_datetime(result["settlement_time"], utc=True)
    else:
        result["settlement_time"] = result["funding_time"].dt.floor("h")
    jitter = result["funding_time"] - result["settlement_time"]
    if (jitter < pd.Timedelta(0)).any() or (jitter >= pd.Timedelta(seconds=1)).any():
        raise ValueError("funding settlement jitter must be in [0, 1 second)")
    for column in ("funding_rate", "mark_price"):
        result[column] = pd.to_numeric(result[column], errors="raise")
        if not np.isfinite(result[column].to_numpy(dtype=float)).all():
            raise ValueError(f"funding contains non-finite {column}")
    if (result["mark_price"] <= 0).any():
        raise ValueError("funding mark prices must be positive")
    if result.duplicated(["funding_time", "symbol"]).any():
        raise ValueError("duplicate funding settlements")
    return result.sort_values(["funding_time", "symbol"], ignore_index=True)


def _normalise_marks(marks: pd.DataFrame) -> pd.DataFrame:
    required = {"mark_time", "symbol", "mark_price"}
    missing = required - set(marks)
    if missing:
        raise ValueError(f"mark prices missing columns: {sorted(missing)}")
    result = marks.loc[:, sorted(required)].copy()
    result["mark_time"] = pd.to_datetime(result["mark_time"], utc=True)
    result["mark_price"] = pd.to_numeric(result["mark_price"], errors="raise")
    if not np.isfinite(result["mark_price"].to_numpy(dtype=float)).all():
        raise ValueError("mark prices are non-finite")
    if (result["mark_price"] <= 0).any() or result.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("invalid or duplicate mark prices")
    return result.sort_values(["mark_time", "symbol"], ignore_index=True)


def _time_slice(
    frame: pd.DataFrame,
    column: str,
    *,
    lower: pd.Timestamp | None = None,
    lower_inclusive: bool = True,
    upper: pd.Timestamp | None = None,
    upper_inclusive: bool = False,
) -> pd.DataFrame:
    """Slice by causal time before numeric validation, making future-value corruption inert."""
    if column not in frame:
        return frame
    times = pd.to_datetime(frame[column], utc=True, errors="raise")
    mask = pd.Series(True, index=frame.index)
    if lower is not None:
        mask &= times.ge(lower) if lower_inclusive else times.gt(lower)
    if upper is not None:
        mask &= times.le(upper) if upper_inclusive else times.lt(upper)
    result = frame.loc[mask].copy()
    result[column] = times.loc[mask]
    return result


def _past_auxiliary(frame: pd.DataFrame, decision: pd.Timestamp) -> pd.DataFrame:
    forbidden = {str(column).lower() for column in frame.columns} & FORBIDDEN_CONTEXT_COLUMNS
    if forbidden:
        raise ValueError(f"auxiliary data exposes organizer-owned fields: {sorted(forbidden)}")
    time_columns = [
        column
        for column in ("time", "timestamp", "event_time", "close_time", "funding_time")
        if column in frame
    ]
    if not time_columns:
        return frame.copy(deep=False)
    if len(time_columns) != 1:
        raise ValueError("auxiliary dataset has an ambiguous causal time column")
    times = pd.to_datetime(frame[time_columns[0]], utc=True)
    return frame.loc[times < decision].copy(deep=False)


def _bar_context_index(
    bars: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DatetimeIndex]]:
    histories: dict[str, pd.DataFrame] = {}
    close_times: dict[str, pd.DatetimeIndex] = {}
    for symbol, group in bars.groupby("symbol", sort=True):
        name = str(symbol)
        history = group.drop(columns=["symbol", "open"], errors="ignore").reset_index(drop=True)
        histories[name] = history
        close_times[name] = pd.DatetimeIndex(history["close_time"])
    return histories, close_times


def _context_bars(
    histories: Mapping[str, pd.DataFrame],
    close_times: Mapping[str, pd.DatetimeIndex],
    decision: pd.Timestamp,
    *,
    eligible_symbols: Sequence[str],
    history_days: int,
) -> dict[str, pd.DataFrame]:
    lower = decision - pd.Timedelta(days=history_days)
    result: dict[str, pd.DataFrame] = {}
    for symbol in eligible_symbols:
        history = histories.get(symbol)
        if history is None:
            continue
        times = close_times[symbol]
        start = int(times.searchsorted(lower, side="left"))
        stop = int(times.searchsorted(decision, side="left"))
        if stop > start:
            # Pandas 3 copy-on-write makes this a mutation-isolated, lazy view.  Deep-copying
            # roughly 50 x 540 rows at every boundary dominated multi-year replay time without
            # adding any isolation.
            result[symbol] = history.iloc[start:stop]
    return result


def _membership_index(
    membership: pd.DataFrame,
) -> tuple[pd.DatetimeIndex, tuple[tuple[str, ...], ...]]:
    frame = membership.copy()
    frame["reconstitution_time"] = pd.to_datetime(frame["reconstitution_time"], utc=True)
    frame = frame.sort_values(
        ["reconstitution_time", "liquidity_rank", "symbol"], ignore_index=True
    )
    boundaries: list[pd.Timestamp] = []
    members: list[tuple[str, ...]] = []
    for boundary, rows in frame.groupby("reconstitution_time", sort=False):
        boundaries.append(pd.Timestamp(boundary))
        members.append(tuple(rows["symbol"].astype(str)))
    return pd.DatetimeIndex(boundaries), tuple(members)


def _indexed_members_at(
    boundaries: pd.DatetimeIndex,
    members: Sequence[tuple[str, ...]],
    decision: pd.Timestamp,
) -> tuple[str, ...]:
    position = int(boundaries.searchsorted(decision, side="right")) - 1
    return members[position] if position >= 0 else ()


def _validate_targets(
    raw: Mapping[str, float] | None, eligible: Sequence[str]
) -> Mapping[str, float] | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("target_weights must return a mapping, {}, or None")
    eligible_set = set(eligible)
    result: dict[str, float] = {}
    for symbol, value in raw.items():
        name, weight = str(symbol), float(value)
        if name not in eligible_set:
            raise ValueError(f"strategy targeted ineligible symbol {name}")
        if not math.isfinite(weight):
            raise ValueError(f"strategy returned non-finite target for {name}")
        result[name] = weight
    return result


def generate_targets(
    strategy: TargetStrategyV2,
    *,
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    auxiliary: Mapping[str, pd.DataFrame],
    membership: pd.DataFrame,
    decision_times: Sequence[pd.Timestamp],
    seed: int,
    unavailability: Sequence[UnavailabilityWindow] = (),
    history_days: int = 180,
) -> pd.DataFrame:
    """Stream one continuous, past-only context through a fresh strategy instance."""
    if history_days < 1:
        raise ValueError("strategy history window must contain at least one complete UTC day")
    decisions = pd.DatetimeIndex(
        [pd.Timestamp(value).tz_convert("UTC") for value in decision_times]
    )
    if decisions.empty:
        return pd.DataFrame(index=decisions, columns=[REBALANCE_COLUMN])
    uses_bars = getattr(strategy, "uses_bars", True)
    uses_funding = getattr(strategy, "uses_funding", True)
    if not isinstance(uses_bars, bool) or not isinstance(uses_funding, bool):
        raise ValueError("strategy input declarations must be booleans")
    if uses_bars:
        bar_frame = _normalise_bars(
            _time_slice(bars, "close_time", upper=decisions.max(), upper_inclusive=False)
        )
        bar_histories, bar_close_times = _bar_context_index(bar_frame)
    else:
        bar_histories, bar_close_times = {}, {}
    if uses_funding:
        funding_frame = _normalise_funding(
            _time_slice(funding, "funding_time", upper=decisions.max(), upper_inclusive=False)
        )
        funding_times = pd.DatetimeIndex(funding_frame["funding_time"])
    else:
        funding_frame = funding.iloc[0:0].drop(columns="mark_price", errors="ignore")
        funding_times = pd.DatetimeIndex([])
    membership_boundaries, membership_members = _membership_index(membership)
    symbols = sorted(set(membership["symbol"].astype(str)))
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        unavailable = set(unavailable_symbols(unavailability, decision))
        eligible = tuple(
            symbol
            for symbol in _indexed_members_at(membership_boundaries, membership_members, decision)
            if symbol not in unavailable
        )
        if uses_funding:
            funding_start = int(
                funding_times.searchsorted(decision - pd.Timedelta(days=history_days), side="left")
            )
            funding_stop = int(funding_times.searchsorted(decision, side="left"))
            past_funding = funding_frame.iloc[funding_start:funding_stop].copy(deep=False)
            past_funding = past_funding.loc[past_funding["symbol"].astype(str).isin(eligible)]
        else:
            past_funding = funding_frame.iloc[0:0].copy(deep=False)
        # Settlement marks price the organizer's cashflow and are never a strategy input.
        past_funding = past_funding.drop(columns="mark_price", errors="ignore")
        context = DecisionContextV2(
            decision_time=decision,
            bars=(
                _context_bars(
                    bar_histories,
                    bar_close_times,
                    decision,
                    eligible_symbols=eligible,
                    history_days=history_days,
                )
                if uses_bars
                else {}
            ),
            funding=past_funding,
            auxiliary={
                str(name): _past_auxiliary(frame, decision) for name, frame in auxiliary.items()
            },
            eligible_symbols=eligible,
        )
        try:
            target = _validate_targets(strategy.target_weights(context, seed=seed), eligible)
        except Exception as error:
            raise StrategyFailureError(
                f"candidate target failed: {type(error).__name__}"
            ) from error
        row: dict[str, Any] = {symbol: np.nan for symbol in symbols}
        row[REBALANCE_COLUMN] = target is not None
        if target is not None:
            row.update({symbol: 0.0 for symbol in symbols})
            row.update(target)
        rows.append(row)
    return pd.DataFrame(rows, index=decisions, columns=[*symbols, REBALANCE_COLUMN])


def cap_target_row(weights: pd.Series, config: ExecutionConfig) -> pd.Series:
    """Uniform reduction for gross, absolute-net, and per-symbol limits."""
    values = weights.astype(float)
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("target row contains non-finite weights")
    magnitudes = (
        (float(values.abs().sum()), config.max_gross_exposure),
        (abs(float(values.sum())), config.max_abs_net_exposure),
        (float(values.abs().max()) if len(values) else 0.0, config.max_symbol_exposure),
    )
    factors = [ceiling / magnitude for magnitude, ceiling in magnitudes if magnitude > ceiling]
    scale = min([1.0, *factors])
    return values * scale


def _within_caps(weights: pd.Series, config: ExecutionConfig, *, tolerance: float = 1e-10) -> bool:
    return (
        float(weights.abs().sum()) <= config.max_gross_exposure + tolerance
        and abs(float(weights.sum())) <= config.max_abs_net_exposure + tolerance
        and (
            not len(weights) or float(weights.abs().max()) <= config.max_symbol_exposure + tolerance
        )
    )


def scale_targets(targets: pd.DataFrame, scalars: pd.Series) -> pd.DataFrame:
    if not targets.index.equals(scalars.index):
        raise ValueError("risk scalars do not align with target decisions")
    result = targets.copy()
    columns = [column for column in result if column != REBALANCE_COLUMN]
    explicit = result[REBALANCE_COLUMN].astype(bool)
    result.loc[explicit, columns] = result.loc[explicit, columns].mul(scalars.loc[explicit], axis=0)
    return result


def require_execution_coverage(
    snapshot: Snapshot,
    decision_times: Sequence[pd.Timestamp],
    *,
    unavailability: Sequence[UnavailabilityWindow] = (),
) -> None:
    """Missing bars/marks fail readiness; they never rewrite weekly membership."""
    bars, marks = _normalise_bars(snapshot.bars), _normalise_marks(snapshot.mark_prices)
    funding = _normalise_funding(snapshot.funding)
    terminal = snapshot.window_end
    funding_times = set(funding["settlement_time"])
    mark_times = set(marks["mark_time"])
    if terminal not in funding_times or terminal not in mark_times:
        raise ValueError("terminal funding and mark boundary is missing")
    bar_symbols_by_time = {
        pd.Timestamp(time): frozenset(group.astype(str))
        for time, group in bars.groupby("open_time", sort=False)["symbol"]
    }
    mark_symbols_by_time = {
        pd.Timestamp(time): frozenset(group.astype(str))
        for time, group in marks.groupby("mark_time", sort=False)["symbol"]
    }
    interval_left = funding["settlement_time"].dt.ceil("8h") - pd.Timedelta(hours=8)
    funding_symbols_by_interval = {
        pd.Timestamp(time): frozenset(funding.loc[index, "symbol"].astype(str))
        for time, index in funding.groupby(interval_left, sort=False).groups.items()
    }
    for window in unavailability:
        prior = window.start - pd.Timedelta(hours=8)
        if window.symbol not in members_at(snapshot.membership, prior):
            raise ValueError(
                f"unavailability audit names a non-member: {window.symbol} at {window.start}"
            )
        prior_rows = bars.loc[
            bars["open_time"].eq(prior) & bars["symbol"].astype(str).eq(window.symbol)
        ]
        if len(prior_rows) != 1 or float(prior_rows.iloc[0]["close"]) != window.settlement_price:
            raise ValueError(
                f"unavailability settlement evidence differs from the preceding close: "
                f"{window.symbol} at {window.start}"
            )
        audited_rows = bars.loc[
            bars["open_time"].ge(window.start)
            & bars["open_time"].lt(window.end)
            & bars["symbol"].astype(str).eq(window.symbol)
        ]
        active_rows = audited_rows["quote_volume"].astype(float).gt(0.0)
        if "trade_count" in audited_rows:
            active_rows |= audited_rows["trade_count"].astype(float).gt(0.0)
        if active_rows.any():
            raise ValueError(
                f"unavailability audit suppresses an active transaction bar: "
                f"{window.symbol} at {audited_rows.loc[active_rows].iloc[0]['open_time']}"
            )
    for raw in decision_times:
        decision = pd.Timestamp(raw).tz_convert("UTC")
        members = set(members_at(snapshot.membership, decision))
        executable = members - set(unavailable_symbols(unavailability, decision))
        bar_symbols = bar_symbols_by_time.get(decision, frozenset())
        mark_symbols = mark_symbols_by_time.get(decision, frozenset())
        missing_bars, missing_marks = executable - bar_symbols, executable - mark_symbols
        if missing_bars or missing_marks:
            raise ValueError(
                f"execution coverage failure at {decision}: bars={sorted(missing_bars)}, "
                f"marks={sorted(missing_marks)}"
            )
        next_time = decision + pd.Timedelta(hours=8)
        funded = funding_symbols_by_interval.get(decision, frozenset())
        unavailable_next = set(unavailable_symbols(unavailability, next_time))
        missing_funding = executable - unavailable_next - funded
        if missing_funding:
            raise ValueError(
                f"funding coverage failure in ({decision}, {next_time}]: {sorted(missing_funding)}"
            )
    terminal_members = set(members_at(snapshot.membership, terminal - pd.Timedelta(nanoseconds=1)))
    terminal_members -= set(unavailable_symbols(unavailability, terminal))
    terminal_marks = set(marks.loc[marks["mark_time"] == terminal, "symbol"].astype(str))
    if terminal_members - terminal_marks:
        raise ValueError(
            f"terminal mark coverage failure: {sorted(terminal_members - terminal_marks)}"
        )


def _evaluate_targets_reference(
    targets: pd.DataFrame,
    *,
    snapshot: Snapshot,
    config: ExecutionConfig = ExecutionConfig(),
    cost_multiplier: float,
    terminal: bool = False,
    initial_state: ReplayState | None = None,
    unavailability: Sequence[UnavailabilityWindow] = (),
) -> EvaluationResultV2:
    """Fill target weights at the transaction open and attribute funding to ``(t, t+8h]``."""
    config.validate()
    if not math.isfinite(cost_multiplier) or cost_multiplier < 0:
        raise ValueError("cost multiplier must be finite and nonnegative")
    decisions = pd.DatetimeIndex(targets.index)
    if decisions.tz is None or not decisions.is_monotonic_increasing or not decisions.is_unique:
        raise ValueError("targets need a unique ascending UTC index")
    if decisions.empty:
        state = initial_state or ReplayState(snapshot.window_start, config.initial_equity, {})
        return EvaluationResultV2(pd.DataFrame(), pd.DataFrame(), state)
    step = pd.Timedelta(hours=config.interval_hours)
    weight_columns = [column for column in targets if column != REBALANCE_COLUMN]
    starts_flat = initial_state is None or not initial_state.quantities
    target_values = targets.loc[:, weight_columns].fillna(0.0)
    if starts_flat and not target_values.ne(0.0).any().any():
        equity = config.initial_equity if initial_state is None else float(initial_state.equity)
        rows = pd.DataFrame(
            {
                "decision_time": decisions,
                "right_boundary": decisions + step,
                "price_return": 0.0,
                "funding_return": 0.0,
                "gross_return": 0.0,
                "fees_slippage": 0.0,
                "net_return": 0.0,
                "turnover": 0.0,
                "gross_exposure": 0.0,
                "equity": equity,
            }
        ).set_index("decision_time")
        return EvaluationResultV2(
            rows,
            pd.DataFrame(),
            ReplayState(decisions[-1] + step, equity, {}),
        )
    first, end = decisions.min(), decisions.max() + step
    bars = _normalise_bars(
        _time_slice(
            snapshot.bars,
            "open_time",
            lower=first,
            upper=end,
            upper_inclusive=True,
        )
    )
    funding_source = snapshot.funding.copy()
    if "settlement_time" not in funding_source:
        funding_source["settlement_time"] = pd.to_datetime(
            funding_source["funding_time"], utc=True, errors="raise"
        ).dt.floor("h")
    funding = _normalise_funding(
        _time_slice(
            funding_source,
            "settlement_time",
            lower=first,
            lower_inclusive=False,
            upper=end,
            upper_inclusive=True,
        )
    )
    marks = _normalise_marks(
        _time_slice(
            snapshot.mark_prices,
            "mark_time",
            lower=first,
            upper=decisions.max(),
            upper_inclusive=True,
        )
    )
    bar_rows = {
        pd.Timestamp(time): group.set_index("symbol")
        for time, group in bars.groupby("open_time", sort=False)
    }
    mark_rows = {
        pd.Timestamp(time): group.set_index("symbol")["mark_price"].astype(float)
        for time, group in marks.groupby("mark_time", sort=False)
    }
    funding_left = funding["settlement_time"].dt.ceil("8h") - pd.Timedelta(hours=8)
    funding_rows = {
        pd.Timestamp(time): funding.loc[index]
        for time, index in funding.groupby(funding_left, sort=False).groups.items()
    }
    membership_boundaries, membership_members = _membership_index(snapshot.membership)
    empty_bar_rows = bars.iloc[0:0].set_index("symbol")
    symbols = sorted(set(bars["symbol"].astype(str)) | set(targets) - {REBALANCE_COLUMN})
    quantities = pd.Series(0.0, index=symbols)
    equity = config.initial_equity
    if initial_state is not None:
        equity = float(initial_state.equity)
        quantities.update(pd.Series(initial_state.quantities, dtype=float))
    return_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for position, decision in enumerate(decisions):
        next_time = decision + step
        weekly_members = set(
            _indexed_members_at(membership_boundaries, membership_members, decision)
        )
        suppressed = set(unavailable_symbols(unavailability, decision))
        eligible = weekly_members - suppressed
        carried_suppressed = set(quantities[quantities.ne(0.0)].index) & suppressed
        if carried_suppressed:
            raise ValueError(
                f"unavailable positions were not settled before {decision}: "
                f"{sorted(carried_suppressed)}"
            )
        current_rows = bar_rows.get(decision, empty_bar_rows)
        required = eligible | set(quantities[quantities.ne(0.0)].index)
        missing = required - set(current_rows.index.astype(str))
        if missing:
            raise ValueError(f"missing transaction bar at {decision}: {sorted(missing)}")
        current_open = current_rows["open"].reindex(symbols).astype(float)
        current_close = current_rows["close"].reindex(symbols).astype(float)
        quote_volume = current_rows["quote_volume"].reindex(symbols).fillna(0.0).astype(float)
        current_mark = mark_rows.get(decision, pd.Series(dtype=float)).reindex(symbols)
        missing_marks = current_mark.reindex(sorted(required)).isna()
        if missing_marks.any():
            names = list(missing_marks[missing_marks].index)
            raise ValueError(f"missing execution marks at {decision}: {names}")

        equity_start = equity
        explicit = bool(targets.at[decision, REBALANCE_COLUMN])
        desired = quantities.copy()
        if explicit:
            row = targets.loc[decision].drop(labels=REBALANCE_COLUMN).reindex(symbols).fillna(0.0)
            row.loc[~row.index.isin(eligible)] = 0.0
            capped = cap_target_row(row, config)
            desired = capped.mul(equity_start).div(current_mark).replace([np.inf, -np.inf], np.nan)
            desired = desired.fillna(0.0)
        # Membership exits are organizer-owned and occur even on a strategy hold.
        desired.loc[~desired.index.isin(eligible)] = 0.0
        requested_quantity = desired - quantities
        requested_notional = requested_quantity.mul(current_open).fillna(0.0)
        capacity = quote_volume * config.max_bar_participation
        strategy_filled = requested_notional.clip(lower=-capacity, upper=capacity)
        fill_quantity = strategy_filled.div(current_open).fillna(0.0)
        quantities = quantities + fill_quantity
        quantities = quantities.where(
            quantities.mul(current_open).abs().fillna(0.0) > _NOTIONAL_DUST_USD, 0.0
        )
        # A carried book can drift over an exposure limit even though its target was valid. Use
        # all participation left after the strategy fill to reduce that drift. If the market's
        # capacity is insufficient, the excess remains a temporary execution shortfall: the
        # strategy cannot see or cause the organizer's fill constraint, so it is not a candidate
        # failure. Every subsequent boundary continues deleveraging toward the capped book.
        marked_weights = quantities.mul(current_mark).fillna(0.0) / equity_start
        capped_marked = cap_target_row(marked_weights, config)
        risk_requested = (capped_marked - marked_weights).mul(equity_start).div(current_mark)
        risk_requested_notional = risk_requested.mul(current_open).fillna(0.0)
        remaining_capacity = (capacity - strategy_filled.abs()).clip(lower=0.0)
        risk_filled = risk_requested_notional.clip(
            lower=-remaining_capacity, upper=remaining_capacity
        )
        quantities = quantities + risk_filled.div(current_open).fillna(0.0)
        quantities = quantities.where(
            quantities.mul(current_open).abs().fillna(0.0) > _NOTIONAL_DUST_USD, 0.0
        )
        filled_notional = strategy_filled + risk_filled
        turnover_usd = float(filled_notional.abs().sum())
        cost_rate = (
            (config.taker_fee_bps_per_side + config.slippage_bps_per_side)
            / 10_000
            * cost_multiplier
        )
        costs_usd = turnover_usd * cost_rate

        last = position == len(decisions) - 1
        next_rows = bar_rows.get(next_time)
        if next_rows is None:
            end_price = current_close
        else:
            end_price = next_rows["open"].reindex(symbols).astype(float)
        unavailable_next = set(unavailable_symbols(unavailability, next_time))
        next_members = set(
            _indexed_members_at(membership_boundaries, membership_members, next_time)
        )
        # Participation-limited positions can survive a weekly roster exit.  If such a former
        # member subsequently reaches its last verified positive-activity bar, it cannot be
        # allowed to turn an organizer execution shortfall into a candidate failure.  Settle it
        # at that bar's close at the following boundary, exactly like a frozen midweek
        # unavailability event.  Current members still require the pre-activation audit above.
        next_active_symbols = (
            set()
            if next_rows is None
            else set(
                next_rows.loc[
                    pd.to_numeric(next_rows["quote_volume"], errors="coerce").gt(0.0)
                ].index.astype(str)
            )
        )
        unavailable_next.update(
            symbol
            for symbol in (set(current_rows.index.astype(str)) - next_members - next_active_symbols)
            if float(current_rows.at[symbol, "quote_volume"]) > 0.0
        )
        for symbol in unavailable_next:
            if symbol in end_price.index:
                end_price.loc[symbol] = current_close.get(symbol, np.nan)
        held = quantities.ne(0.0)
        if end_price.loc[held].isna().any():
            raise ValueError(
                f"missing next executable price at {next_time}: "
                f"{list(end_price.loc[held & end_price.isna()].index)}"
            )
        price_pnl_usd = float((quantities * (end_price - current_open).fillna(0.0)).sum())
        interval_funding = funding_rows.get(decision, funding.iloc[0:0])
        event_quantities = interval_funding["symbol"].map(quantities).fillna(0.0).astype(float)
        funding_pnl_usd = -float(
            (
                event_quantities
                * interval_funding["mark_price"].astype(float)
                * interval_funding["funding_rate"].astype(float)
            ).sum()
        )
        held_quantities = quantities.copy()
        exposure = float(
            (held_quantities.abs() * current_mark.fillna(current_open)).sum() / equity_start
        )
        gross_pnl = price_pnl_usd + funding_pnl_usd
        liquidation_cost = 0.0
        liquidation_notional = 0.0
        availability_symbols = unavailable_next & set(quantities[quantities.ne(0.0)].index)
        if availability_symbols:
            settlement_symbols = sorted(availability_symbols)
            close_notional = quantities.loc[settlement_symbols].mul(
                end_price.loc[settlement_symbols]
            )
            liquidation_notional += float(close_notional.abs().sum())
            liquidation_cost += float(close_notional.abs().sum()) * cost_rate
            for symbol, notional in close_notional.items():
                event_rows.append(
                    {
                        "timestamp": next_time,
                        "symbol": symbol,
                        "event_type": "unavailability_settlement",
                        "notional": -float(notional),
                    }
                )
            quantities.loc[settlement_symbols] = 0.0
        if terminal and last:
            close_notional = quantities.mul(end_price).fillna(0.0)
            close_capacity = (capacity - filled_notional.abs()).clip(lower=0.0)
            if (close_notional.abs() > close_capacity + 1e-9).any():
                raise StrategyFailureError(
                    "terminal liquidation exceeds remaining participation capacity"
                )
            terminal_notional = float(close_notional.abs().sum())
            liquidation_notional += terminal_notional
            liquidation_cost += terminal_notional * cost_rate
            for symbol, notional in close_notional[close_notional.ne(0.0)].items():
                event_rows.append(
                    {
                        "timestamp": next_time,
                        "symbol": symbol,
                        "event_type": "terminal_liquidation",
                        "notional": -float(notional),
                    }
                )
            quantities[:] = 0.0
        total_cost = costs_usd + liquidation_cost
        equity = equity_start + gross_pnl - total_cost
        if not math.isfinite(equity) or equity <= 0:
            raise StrategyFailureError(f"portfolio insolvent at {decision}")

        for symbol, notional in strategy_filled[strategy_filled.ne(0.0)].items():
            event_rows.append(
                {
                    "timestamp": decision,
                    "symbol": symbol,
                    "event_type": "trade",
                    "notional": float(notional),
                }
            )
        for symbol, notional in risk_filled[risk_filled.ne(0.0)].items():
            event_rows.append(
                {
                    "timestamp": decision,
                    "symbol": symbol,
                    "event_type": "risk_reduction",
                    "notional": float(notional),
                }
            )
        for row in interval_funding.itertuples(index=False):
            quantity = float(held_quantities.get(str(row.symbol), 0.0))
            if quantity:
                event_rows.append(
                    {
                        "timestamp": row.settlement_time,
                        "symbol": str(row.symbol),
                        "event_type": "funding",
                        "notional": quantity * float(row.mark_price),
                    }
                )
        return_rows.append(
            {
                "decision_time": decision,
                "right_boundary": next_time,
                "price_return": price_pnl_usd / equity_start,
                "funding_return": funding_pnl_usd / equity_start,
                "gross_return": gross_pnl / equity_start,
                "fees_slippage": total_cost / equity_start,
                "net_return": (gross_pnl - total_cost) / equity_start,
                "turnover": (turnover_usd + liquidation_notional) / equity_start,
                "gross_exposure": exposure,
                "equity": equity,
            }
        )
    returns = (
        pd.DataFrame(return_rows).set_index("decision_time") if return_rows else pd.DataFrame()
    )
    events = pd.DataFrame(event_rows)
    final_time = decisions[-1] + step if len(decisions) else snapshot.window_start
    state = ReplayState(
        decision_time=final_time,
        equity=float(equity),
        quantities={key: float(value) for key, value in quantities[quantities.ne(0.0)].items()},
    )
    return EvaluationResultV2(returns=returns, events=events, final_state=state)


@dataclasses.dataclass(frozen=True, slots=True)
class _PreparedExecution:
    """Immutable array view reused by calibration and every independent cost pass."""

    decisions: pd.DatetimeIndex
    symbols: tuple[str, ...]
    symbol_positions: Mapping[str, int]
    opens: np.ndarray
    closes: np.ndarray
    quote_volumes: np.ndarray
    marks: np.ndarray
    bar_time_exists: np.ndarray
    eligible: np.ndarray
    suppressed: tuple[frozenset[str], ...]
    unavailable_next: tuple[frozenset[str], ...]
    funding_indices: tuple[np.ndarray, ...]
    funding_marks: tuple[np.ndarray, ...]
    funding_rates: tuple[np.ndarray, ...]
    funding_times: tuple[tuple[pd.Timestamp, ...], ...]
    funding_symbols: tuple[tuple[str, ...], ...]


def _matrix(
    frame: pd.DataFrame,
    *,
    time_column: str,
    value_column: str,
    times: pd.DatetimeIndex,
    symbols: Sequence[str],
) -> np.ndarray:
    if frame.empty:
        return np.full((len(times), len(symbols)), np.nan, dtype=float)
    pivot = frame.pivot(index=time_column, columns="symbol", values=value_column)
    return pivot.reindex(index=times, columns=symbols).to_numpy(dtype=float, copy=True)


def _prepare_execution(
    targets: pd.DataFrame,
    *,
    snapshot: Snapshot,
    config: ExecutionConfig,
    unavailability: Sequence[UnavailabilityWindow],
) -> _PreparedExecution:
    decisions = pd.DatetimeIndex(targets.index)
    step = pd.Timedelta(hours=config.interval_hours)
    first, end = decisions.min(), decisions.max() + step
    bars = _normalise_bars(
        _time_slice(
            snapshot.bars,
            "open_time",
            lower=first,
            upper=end,
            upper_inclusive=True,
        )
    )
    funding_source = snapshot.funding.copy()
    if "settlement_time" not in funding_source:
        funding_source["settlement_time"] = pd.to_datetime(
            funding_source["funding_time"], utc=True, errors="raise"
        ).dt.floor("h")
    funding = _normalise_funding(
        _time_slice(
            funding_source,
            "settlement_time",
            lower=first,
            lower_inclusive=False,
            upper=end,
            upper_inclusive=True,
        )
    )
    marks = _normalise_marks(
        _time_slice(
            snapshot.mark_prices,
            "mark_time",
            lower=first,
            upper=decisions.max(),
            upper_inclusive=True,
        )
    )
    symbols = tuple(sorted(set(bars["symbol"].astype(str)) | set(targets) - {REBALANCE_COLUMN}))
    positions = {symbol: index for index, symbol in enumerate(symbols)}
    bar_times = decisions.append(pd.DatetimeIndex([decisions[-1] + step]))
    opens = _matrix(
        bars,
        time_column="open_time",
        value_column="open",
        times=bar_times,
        symbols=symbols,
    )
    closes = _matrix(
        bars,
        time_column="open_time",
        value_column="close",
        times=bar_times,
        symbols=symbols,
    )
    quote_volumes = _matrix(
        bars,
        time_column="open_time",
        value_column="quote_volume",
        times=bar_times,
        symbols=symbols,
    )
    mark_values = _matrix(
        marks,
        time_column="mark_time",
        value_column="mark_price",
        times=decisions,
        symbols=symbols,
    )
    existing_times = frozenset(pd.DatetimeIndex(bars["open_time"]))
    bar_time_exists = np.array([time in existing_times for time in bar_times], dtype=bool)

    membership_boundaries, membership_members = _membership_index(snapshot.membership)
    eligible = np.zeros((len(decisions), len(symbols)), dtype=bool)
    suppressed: list[frozenset[str]] = []
    unavailable_next: list[frozenset[str]] = []
    for row, decision in enumerate(decisions):
        blocked = frozenset(unavailable_symbols(unavailability, decision))
        following = set(unavailable_symbols(unavailability, decision + step))
        suppressed.append(blocked)
        current_members = _indexed_members_at(membership_boundaries, membership_members, decision)
        next_members = set(
            _indexed_members_at(membership_boundaries, membership_members, decision + step)
        )
        inactive_post_exit = (
            np.isfinite(opens[row])
            & (np.nan_to_num(quote_volumes[row], nan=0.0) > 0.0)
            & (np.isnan(opens[row + 1]) | (np.nan_to_num(quote_volumes[row + 1], nan=0.0) <= 0.0))
        )
        following.update(
            symbols[position]
            for position in np.flatnonzero(inactive_post_exit)
            if symbols[position] not in next_members
        )
        unavailable_next.append(frozenset(following))
        for symbol in current_members:
            position = positions.get(symbol)
            if position is not None and symbol not in blocked:
                eligible[row, position] = True

    funding_left = funding["settlement_time"].dt.ceil("8h") - step
    funding_groups = {
        pd.Timestamp(time): np.asarray(index, dtype=int)
        for time, index in funding.groupby(funding_left, sort=False).groups.items()
    }
    funding_indices: list[np.ndarray] = []
    funding_marks: list[np.ndarray] = []
    funding_rates: list[np.ndarray] = []
    funding_times: list[tuple[pd.Timestamp, ...]] = []
    funding_symbols: list[tuple[str, ...]] = []
    for decision in decisions:
        rows = funding_groups.get(decision, np.array([], dtype=int))
        group = funding.loc[rows]
        names = tuple(group["symbol"].astype(str))
        funding_indices.append(np.array([positions[name] for name in names], dtype=int))
        funding_marks.append(group["mark_price"].to_numpy(dtype=float, copy=True))
        funding_rates.append(group["funding_rate"].to_numpy(dtype=float, copy=True))
        funding_times.append(tuple(pd.Timestamp(value) for value in group["settlement_time"]))
        funding_symbols.append(names)
    return _PreparedExecution(
        decisions=decisions,
        symbols=symbols,
        symbol_positions=positions,
        opens=opens,
        closes=closes,
        quote_volumes=quote_volumes,
        marks=mark_values,
        bar_time_exists=bar_time_exists,
        eligible=eligible,
        suppressed=tuple(suppressed),
        unavailable_next=tuple(unavailable_next),
        funding_indices=tuple(funding_indices),
        funding_marks=tuple(funding_marks),
        funding_rates=tuple(funding_rates),
        funding_times=tuple(funding_times),
        funding_symbols=tuple(funding_symbols),
    )


def _cap_array(values: np.ndarray, config: ExecutionConfig) -> np.ndarray:
    absolute = np.abs(values)
    gross = float(absolute.sum())
    net = abs(float(values.sum()))
    symbol = float(absolute.max()) if len(values) else 0.0
    factors = [
        ceiling / magnitude
        for magnitude, ceiling in (
            (gross, config.max_gross_exposure),
            (net, config.max_abs_net_exposure),
            (symbol, config.max_symbol_exposure),
        )
        if magnitude > ceiling
    ]
    return values * min([1.0, *factors])


def _within_array_caps(
    values: np.ndarray, config: ExecutionConfig, *, tolerance: float = 1e-10
) -> bool:
    absolute = np.abs(values)
    return bool(
        float(absolute.sum()) <= config.max_gross_exposure + tolerance
        and abs(float(values.sum())) <= config.max_abs_net_exposure + tolerance
        and (not len(values) or float(absolute.max()) <= config.max_symbol_exposure + tolerance)
    )


def evaluate_targets(
    targets: pd.DataFrame,
    *,
    snapshot: Snapshot,
    config: ExecutionConfig = ExecutionConfig(),
    cost_multiplier: float,
    terminal: bool = False,
    initial_state: ReplayState | None = None,
    unavailability: Sequence[UnavailabilityWindow] = (),
    record_events: bool = True,
    _prepared: _PreparedExecution | None = None,
) -> EvaluationResultV2:
    """Array-backed execution with the same ordered arithmetic as the reference contract."""
    config.validate()
    if not math.isfinite(cost_multiplier) or cost_multiplier < 0:
        raise ValueError("cost_multiplier must be finite and nonnegative")
    decisions = pd.DatetimeIndex(targets.index)
    if decisions.tz is None or not decisions.is_monotonic_increasing or not decisions.is_unique:
        raise ValueError("targets need a unique ascending UTC index")
    if decisions.empty:
        state = initial_state or ReplayState(snapshot.window_start, config.initial_equity, {})
        return EvaluationResultV2(pd.DataFrame(), pd.DataFrame(), state)
    step = pd.Timedelta(hours=config.interval_hours)
    weight_columns = [column for column in targets if column != REBALANCE_COLUMN]
    starts_flat = initial_state is None or not initial_state.quantities
    target_values = targets.loc[:, weight_columns].fillna(0.0)
    if starts_flat and not target_values.ne(0.0).any().any():
        equity = config.initial_equity if initial_state is None else float(initial_state.equity)
        rows = pd.DataFrame(
            {
                "decision_time": decisions,
                "right_boundary": decisions + step,
                "price_return": 0.0,
                "funding_return": 0.0,
                "gross_return": 0.0,
                "fees_slippage": 0.0,
                "net_return": 0.0,
                "turnover": 0.0,
                "gross_exposure": 0.0,
                "equity": equity,
            }
        ).set_index("decision_time")
        return EvaluationResultV2(
            rows, pd.DataFrame(), ReplayState(decisions[-1] + step, equity, {})
        )
    prepared = _prepared or _prepare_execution(
        targets, snapshot=snapshot, config=config, unavailability=unavailability
    )
    if not prepared.decisions.equals(decisions):
        raise ValueError("prepared execution decisions do not align with targets")
    symbols = prepared.symbols
    size = len(symbols)
    quantities = np.zeros(size, dtype=float)
    equity = config.initial_equity
    if initial_state is not None:
        equity = float(initial_state.equity)
        for symbol, quantity in initial_state.quantities.items():
            position = prepared.symbol_positions.get(symbol)
            if position is not None:
                quantities[position] = float(quantity)
    target_matrix = (
        targets.drop(columns=REBALANCE_COLUMN)
        .reindex(columns=symbols)
        .fillna(0.0)
        .to_numpy(dtype=float, copy=True)
    )
    explicit = targets[REBALANCE_COLUMN].to_numpy(dtype=bool, copy=True)
    return_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    cost_rate = (
        (config.taker_fee_bps_per_side + config.slippage_bps_per_side) / 10_000 * cost_multiplier
    )
    for row, decision in enumerate(decisions):
        next_time = decision + step
        eligible = prepared.eligible[row]
        carried_suppressed = [
            symbol
            for symbol in prepared.suppressed[row]
            if symbol in prepared.symbol_positions
            and quantities[prepared.symbol_positions[symbol]] != 0.0
        ]
        if carried_suppressed:
            raise ValueError(
                f"unavailable positions were not settled before {decision}: "
                f"{sorted(carried_suppressed)}"
            )
        current_open = prepared.opens[row]
        current_close = prepared.closes[row]
        quote_volume = np.nan_to_num(prepared.quote_volumes[row], nan=0.0)
        current_mark = prepared.marks[row]
        required = eligible | (quantities != 0.0)
        missing_bars = required & np.isnan(current_open)
        if missing_bars.any():
            raise ValueError(
                f"missing transaction bar at {decision}: "
                f"{[symbols[index] for index in np.flatnonzero(missing_bars)]}"
            )
        missing_marks = required & np.isnan(current_mark)
        if missing_marks.any():
            raise ValueError(
                f"missing execution marks at {decision}: "
                f"{[symbols[index] for index in np.flatnonzero(missing_marks)]}"
            )

        equity_start = equity
        desired = quantities.copy()
        if explicit[row]:
            weights = target_matrix[row].copy()
            weights[~eligible] = 0.0
            capped = _cap_array(weights, config)
            desired = np.divide(
                capped * equity_start,
                current_mark,
                out=np.zeros(size, dtype=float),
                where=np.isfinite(current_mark) & (current_mark != 0.0),
            )
        desired[~eligible] = 0.0
        requested_quantity = desired - quantities
        requested_notional = np.nan_to_num(requested_quantity * current_open, nan=0.0)
        capacity = quote_volume * config.max_bar_participation
        strategy_filled = np.clip(requested_notional, -capacity, capacity)
        fill_quantity = np.divide(
            strategy_filled,
            current_open,
            out=np.zeros(size, dtype=float),
            where=np.isfinite(current_open) & (current_open != 0.0),
        )
        quantities = quantities + fill_quantity
        quantities[
            np.nan_to_num(np.abs(quantities * current_open), nan=0.0) <= _NOTIONAL_DUST_USD
        ] = 0.0
        marked_weights = np.nan_to_num(quantities * current_mark, nan=0.0) / equity_start
        capped_marked = _cap_array(marked_weights, config)
        risk_requested = np.divide(
            (capped_marked - marked_weights) * equity_start,
            current_mark,
            out=np.zeros(size, dtype=float),
            where=np.isfinite(current_mark) & (current_mark != 0.0),
        )
        risk_requested_notional = np.nan_to_num(risk_requested * current_open, nan=0.0)
        remaining_capacity = np.maximum(capacity - np.abs(strategy_filled), 0.0)
        risk_filled = np.clip(risk_requested_notional, -remaining_capacity, remaining_capacity)
        quantities = quantities + np.divide(
            risk_filled,
            current_open,
            out=np.zeros(size, dtype=float),
            where=np.isfinite(current_open) & (current_open != 0.0),
        )
        quantities[
            np.nan_to_num(np.abs(quantities * current_open), nan=0.0) <= _NOTIONAL_DUST_USD
        ] = 0.0
        filled_notional = strategy_filled + risk_filled
        turnover_usd = float(np.abs(filled_notional).sum())
        costs_usd = turnover_usd * cost_rate

        if prepared.bar_time_exists[row + 1]:
            end_price = prepared.opens[row + 1].copy()
        else:
            end_price = current_close.copy()
        for symbol in prepared.unavailable_next[row]:
            position = prepared.symbol_positions.get(symbol)
            if position is not None:
                end_price[position] = current_close[position]
        held = quantities != 0.0
        missing_end = held & np.isnan(end_price)
        if missing_end.any():
            raise ValueError(
                f"missing next executable price at {next_time}: "
                f"{[symbols[index] for index in np.flatnonzero(missing_end)]}"
            )
        price_change = np.nan_to_num(end_price - current_open, nan=0.0)
        price_pnl_usd = float((quantities * price_change).sum())
        funding_index = prepared.funding_indices[row]
        event_quantities = quantities[funding_index]
        funding_pnl_usd = -float(
            (event_quantities * prepared.funding_marks[row] * prepared.funding_rates[row]).sum()
        )
        held_quantities = quantities.copy()
        exposure_marks = np.where(np.isnan(current_mark), current_open, current_mark)
        exposure = float(np.nansum(np.abs(held_quantities) * exposure_marks) / equity_start)
        gross_pnl = price_pnl_usd + funding_pnl_usd
        liquidation_cost = 0.0
        liquidation_notional = 0.0
        settlement_positions = sorted(
            (
                prepared.symbol_positions[symbol]
                for symbol in prepared.unavailable_next[row]
                if symbol in prepared.symbol_positions
                and quantities[prepared.symbol_positions[symbol]] != 0.0
            ),
            key=lambda index: symbols[index],
        )
        if settlement_positions:
            settlement_array = np.asarray(settlement_positions, dtype=int)
            close_notional = quantities[settlement_array] * end_price[settlement_array]
            liquidation_notional += float(np.abs(close_notional).sum())
            liquidation_cost += float(np.abs(close_notional).sum()) * cost_rate
            if record_events:
                for position, notional in zip(settlement_positions, close_notional, strict=True):
                    event_rows.append(
                        {
                            "timestamp": next_time,
                            "symbol": symbols[position],
                            "event_type": "unavailability_settlement",
                            "notional": -float(notional),
                        }
                    )
            quantities[settlement_array] = 0.0
        if terminal and row == len(decisions) - 1:
            close_notional = np.nan_to_num(quantities * end_price, nan=0.0)
            close_capacity = np.maximum(capacity - np.abs(filled_notional), 0.0)
            if (np.abs(close_notional) > close_capacity + 1e-9).any():
                raise StrategyFailureError(
                    "terminal liquidation exceeds remaining participation capacity"
                )
            terminal_notional = float(np.abs(close_notional).sum())
            liquidation_notional += terminal_notional
            liquidation_cost += terminal_notional * cost_rate
            if record_events:
                for position in np.flatnonzero(close_notional != 0.0):
                    event_rows.append(
                        {
                            "timestamp": next_time,
                            "symbol": symbols[position],
                            "event_type": "terminal_liquidation",
                            "notional": -float(close_notional[position]),
                        }
                    )
            quantities[:] = 0.0
        total_cost = costs_usd + liquidation_cost
        equity = equity_start + gross_pnl - total_cost
        if not math.isfinite(equity) or equity <= 0:
            raise StrategyFailureError(f"portfolio insolvent at {decision}")

        if record_events:
            for position in np.flatnonzero(strategy_filled != 0.0):
                event_rows.append(
                    {
                        "timestamp": decision,
                        "symbol": symbols[position],
                        "event_type": "trade",
                        "notional": float(strategy_filled[position]),
                    }
                )
            for position in np.flatnonzero(risk_filled != 0.0):
                event_rows.append(
                    {
                        "timestamp": decision,
                        "symbol": symbols[position],
                        "event_type": "risk_reduction",
                        "notional": float(risk_filled[position]),
                    }
                )
            for offset, position in enumerate(funding_index):
                quantity = float(held_quantities[position])
                if quantity:
                    event_rows.append(
                        {
                            "timestamp": prepared.funding_times[row][offset],
                            "symbol": prepared.funding_symbols[row][offset],
                            "event_type": "funding",
                            "notional": quantity * float(prepared.funding_marks[row][offset]),
                        }
                    )
        return_rows.append(
            {
                "decision_time": decision,
                "right_boundary": next_time,
                "price_return": price_pnl_usd / equity_start,
                "funding_return": funding_pnl_usd / equity_start,
                "gross_return": gross_pnl / equity_start,
                "fees_slippage": total_cost / equity_start,
                "net_return": (gross_pnl - total_cost) / equity_start,
                "turnover": (turnover_usd + liquidation_notional) / equity_start,
                "gross_exposure": exposure,
                "equity": equity,
            }
        )
    returns = pd.DataFrame(return_rows).set_index("decision_time")
    events = pd.DataFrame(event_rows)
    state = ReplayState(
        decision_time=decisions[-1] + step,
        equity=float(equity),
        quantities={
            symbols[index]: float(quantities[index]) for index in np.flatnonzero(quantities != 0.0)
        },
    )
    return EvaluationResultV2(returns=returns, events=events, final_state=state)


def run_candidate(
    strategy: TargetStrategyV2,
    *,
    snapshot: Snapshot,
    start: pd.Timestamp,
    end: pd.Timestamp,
    auxiliary: Mapping[str, pd.DataFrame] | None = None,
    seed: int = 0,
    config: ExecutionConfig = ExecutionConfig(),
    terminal: bool = False,
    unavailability: Sequence[UnavailabilityWindow] = (),
    record_events: bool = True,
) -> CandidateReplay:
    """One target stream, one causal calibration pass, and independent 1x/2x/3x cost runs."""
    decisions = decision_grid(start, end, interval_hours=config.interval_hours)
    raw = generate_targets(
        strategy,
        bars=snapshot.bars,
        funding=snapshot.funding,
        auxiliary=auxiliary or {},
        membership=snapshot.membership,
        decision_times=decisions,
        seed=seed,
        unavailability=unavailability,
        history_days=config.strategy_history_days,
    )
    nonflat = raw.drop(columns=REBALANCE_COLUMN).fillna(0.0).ne(0.0).any().any()
    prepared = (
        _prepare_execution(raw, snapshot=snapshot, config=config, unavailability=unavailability)
        if nonflat
        else None
    )
    calibration = evaluate_targets(
        raw,
        snapshot=snapshot,
        config=config,
        cost_multiplier=0.0,
        terminal=False,
        unavailability=unavailability,
        record_events=False,
        _prepared=prepared,
    )
    gross = calibration.returns["gross_return"]
    scalars = common_risk_scalars(
        gross,
        decisions,
        target_annualized_volatility=config.risk_target,
        lookback_days=config.risk_lookback_days,
        interval_hours=config.interval_hours,
        minimum_scale=config.risk_minimum_scale,
        maximum_scale=config.risk_maximum_scale,
    )
    scaled = scale_targets(raw, scalars)
    results = {
        multiplier: evaluate_targets(
            scaled,
            snapshot=snapshot,
            config=config,
            cost_multiplier=float(multiplier),
            terminal=terminal,
            unavailability=unavailability,
            record_events=record_events,
            _prepared=prepared,
        )
        for multiplier in (1, 2, 3)
    }
    return CandidateReplay(raw, scalars, calibration, results)


def scored_returns(
    result: EvaluationResultV2, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    """Score intervals by their left boundary only, after a continuous replay."""
    first, stop = pd.Timestamp(start).tz_convert("UTC"), pd.Timestamp(end).tz_convert("UTC")
    return result.returns.loc[
        result.returns.index.to_series().ge(first) & result.returns.index.to_series().lt(stop)
    ].copy()

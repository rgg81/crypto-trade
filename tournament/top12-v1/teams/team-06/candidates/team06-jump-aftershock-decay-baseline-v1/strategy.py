"""Deterministic jump-aftershock decay-state baseline for Team 06."""

from dataclasses import dataclass
from math import exp, isfinite, log
from typing import Mapping, Optional

import numpy as np
import pandas as pd


BAR_HOURS = 8
FORMATION_BARS = 90
MIN_CALIBRATION_RETURNS = 30
JUMP_MULTIPLE = 5.0
MIN_ABSOLUTE_JUMP = 0.03
MAX_EVENT_AGE = 6
MIN_FIRST_AFTERSHOCK_FRACTION = 0.03
MAX_FIRST_AFTERSHOCK_FRACTION = 0.65
MAX_OPPOSING_AFTERSHOCK_FRACTION = 0.35
MAX_RENEWED_IMPULSE_FRACTION = 0.80
MAX_AFTERSHOCK_GROWTH_MULTIPLE = 1.25
AFTERSHOCK_HALF_LIFE = 2.0
REBALANCE_HOURS = 24
MAX_GROSS = 0.80
MAX_ABS_NET = 0.20
MAX_SYMBOL = 0.08


@dataclass
class _AftershockState:
    sign: int
    jump_size: float
    jump_threshold: float
    age: int = 0
    first_aftershock: float = 0.0
    cumulative_projected: float = 0.0
    confirmed: bool = False


def _robust_scale(prior_returns: np.ndarray) -> float:
    center = float(np.median(prior_returns))
    mad = float(np.median(np.abs(prior_returns - center)))
    return 1.4826 * mad


def _advance_state(
    state: _AftershockState, next_return: float
) -> Optional[_AftershockState]:
    state.age += 1
    if state.age > MAX_EVENT_AGE:
        return None

    projected = state.sign * next_return
    state.cumulative_projected += projected

    if state.age == 1:
        lower = MIN_FIRST_AFTERSHOCK_FRACTION * state.jump_size
        upper = MAX_FIRST_AFTERSHOCK_FRACTION * state.jump_size
        if projected <= lower or projected >= upper:
            return None
        state.first_aftershock = projected
        state.confirmed = True
        return state

    if projected <= -MAX_OPPOSING_AFTERSHOCK_FRACTION * state.jump_size:
        return None
    if state.cumulative_projected <= 0.0:
        return None
    if projected >= MAX_RENEWED_IMPULSE_FRACTION * state.jump_size:
        return None
    if projected > MAX_AFTERSHOCK_GROWTH_MULTIPLE * state.first_aftershock:
        return None
    return state


def _event_score(completed_closes: np.ndarray) -> float:
    if completed_closes.size < MIN_CALIBRATION_RETURNS + 2:
        return 0.0
    if not np.all(np.isfinite(completed_closes)) or np.any(completed_closes <= 0.0):
        return 0.0

    returns = np.diff(np.log(completed_closes))
    state: Optional[_AftershockState] = None

    for index in range(MIN_CALIBRATION_RETURNS, returns.size):
        start = max(0, index - FORMATION_BARS)
        prior = returns[start:index]
        scale = _robust_scale(prior)
        threshold = max(MIN_ABSOLUTE_JUMP, JUMP_MULTIPLE * scale)
        current = float(returns[index])

        if abs(current) >= threshold:
            state = _AftershockState(
                sign=1 if current > 0.0 else -1,
                jump_size=abs(current),
                jump_threshold=threshold,
            )
        elif state is not None:
            state = _advance_state(state, current)

    if state is None or not state.confirmed or not 1 <= state.age <= MAX_EVENT_AGE:
        return 0.0

    surprise = min(3.0, state.jump_size / state.jump_threshold)
    confirmation = min(
        1.0, state.first_aftershock / (MAX_FIRST_AFTERSHOCK_FRACTION * state.jump_size)
    )
    age_decay = exp(-log(2.0) * state.age / AFTERSHOCK_HALF_LIFE)
    score = state.sign * surprise * confirmation * age_decay
    return float(score) if isfinite(score) else 0.0


def _completed_closes(frame: pd.DataFrame, decision_time: pd.Timestamp) -> np.ndarray:
    required = {"open_time", "close"}
    if frame is None or not required.issubset(frame.columns):
        return np.empty(0, dtype=float)

    open_time = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    complete = open_time.notna() & ((open_time + pd.Timedelta(hours=BAR_HOURS)) <= decision_time)
    clean = pd.DataFrame({"open_time": open_time[complete], "close": close[complete]})
    clean = clean.dropna().sort_values("open_time").drop_duplicates("open_time", keep="last")
    clean = clean.iloc[-(FORMATION_BARS + MAX_EVENT_AGE + 2) :]
    return clean["close"].to_numpy(dtype=float, copy=True)


def _allocate_capped(scores: Mapping[str, float], budget: float) -> dict[str, float]:
    allocation = {symbol: 0.0 for symbol in scores}
    remaining = {symbol: float(value) for symbol, value in scores.items() if value > 0.0}
    residual = float(budget)

    while remaining and residual > 1e-15:
        total_score = sum(remaining.values())
        if total_score <= 0.0:
            break
        proposed = {
            symbol: residual * value / total_score for symbol, value in remaining.items()
        }
        capped = [symbol for symbol, weight in proposed.items() if weight >= MAX_SYMBOL]
        if not capped:
            allocation.update(proposed)
            break
        for symbol in sorted(capped):
            allocation[symbol] = MAX_SYMBOL
            residual -= MAX_SYMBOL
            remaining.pop(symbol)

    return allocation


class JumpAftershockDecayStrategy:
    def __init__(self) -> None:
        self._last_rebalance: Optional[pd.Timestamp] = None

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        if self._last_rebalance is not None:
            elapsed = decision_time - self._last_rebalance
            if elapsed < pd.Timedelta(hours=REBALANCE_HOURS):
                return None
        self._last_rebalance = decision_time

        symbols = sorted(set(context.eligible_symbols))
        signed_scores: dict[str, float] = {}
        for symbol in symbols:
            frame = context.bars.get(symbol)
            closes = _completed_closes(frame, decision_time)
            score = _event_score(closes)
            if isfinite(score) and score != 0.0:
                signed_scores[symbol] = score

        long_scores = {
            symbol: score for symbol, score in signed_scores.items() if score > 0.0
        }
        short_scores = {
            symbol: -score for symbol, score in signed_scores.items() if score < 0.0
        }

        if long_scores and short_scores:
            side_budget = min(
                MAX_GROSS / 2.0,
                MAX_SYMBOL * len(long_scores),
                MAX_SYMBOL * len(short_scores),
            )
            long_weights = _allocate_capped(long_scores, side_budget)
            short_weights = _allocate_capped(short_scores, side_budget)
        elif long_scores:
            side_budget = min(MAX_ABS_NET, MAX_SYMBOL * len(long_scores))
            long_weights = _allocate_capped(long_scores, side_budget)
            short_weights = {}
        elif short_scores:
            side_budget = min(MAX_ABS_NET, MAX_SYMBOL * len(short_scores))
            long_weights = {}
            short_weights = _allocate_capped(short_scores, side_budget)
        else:
            return {}

        targets = {
            symbol: float(long_weights.get(symbol, 0.0) - short_weights.get(symbol, 0.0))
            for symbol in symbols
            if symbol in long_weights or symbol in short_weights
        }
        targets = {
            symbol: weight
            for symbol, weight in targets.items()
            if isfinite(weight) and abs(weight) > 0.0
        }

        gross = sum(abs(weight) for weight in targets.values())
        net = sum(targets.values())
        if gross > MAX_GROSS + 1e-12 or abs(net) > MAX_ABS_NET + 1e-12:
            return {}
        if any(abs(weight) > MAX_SYMBOL + 1e-12 for weight in targets.values()):
            return {}
        return targets


def build_strategy() -> JumpAftershockDecayStrategy:
    return JumpAftershockDecayStrategy()

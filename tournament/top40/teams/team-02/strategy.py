"""Frozen Team-02 Directed Lagged Diffusion Network strategy.

The strategy consumes only the past-only ``DecisionContext`` supplied by the
common tournament worker.  All learned state is rebuilt chronologically in the
worker; this module contains no fitted artifacts or timestamp keyed targets.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy

EXPECTED_SEED = 20260713
LOOKBACK = 540
RIDGE_PENALTY = 20.0
MAX_LEADERS = 3
GAP_REVERSION = 0.5
EDGE_THRESHOLD = 0.015
HYSTERESIS = 0.30

_INTERVAL = pd.Timedelta(hours=8)
_RCOND = 1e-10
_SCALE_FLOOR = 1e-4
_MIN_VALID_ASSETS = 12
_MIN_RETURN_ROWS = max(180, int(np.ceil(0.6 * LOOKBACK)))
_MIN_EDGE_OVERLAP = max(160, int(np.ceil(0.5 * LOOKBACK)))
_MIN_HALF_OVERLAP = 80
_VOLATILITY_BARS = 90
_MIN_VOLATILITY_ROWS = 45
_NUMERIC_FLOOR = 1e-12


@dataclasses.dataclass(frozen=True)
class _FitState:
    symbols: tuple[str, ...]
    alpha: np.ndarray
    beta: np.ndarray
    residual_center: np.ndarray
    residual_scale: np.ndarray
    valid: np.ndarray
    influence: np.ndarray
    confidence: np.ndarray
    linked: np.ndarray
    communities: np.ndarray
    community_count: int


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _cross_sectional_median(values: np.ndarray) -> np.ndarray:
    medians = np.full(values.shape[0], np.nan, dtype=np.float64)
    for row_index, row in enumerate(values):
        finite = row[np.isfinite(row)]
        if finite.size:
            medians[row_index] = float(np.median(finite))
    return medians


def _returns_on_union_grid(
    context: DecisionContext,
    symbols: Sequence[str],
    *,
    end: pd.Timestamp,
    length: int,
) -> np.ndarray:
    """Return exact 8h close-to-close returns on a fixed union grid.

    Rows outside ``end`` are ignored even if a synthetic test deliberately puts
    them in the context.  Duplicate exact closes are treated as unavailable;
    the canonical feed rejects them before strategy execution.
    """

    first_return = end - (length - 1) * _INTERVAL
    close_grid = pd.date_range(
        first_return - _INTERVAL,
        end,
        freq=_INTERVAL,
        tz="UTC",
    )
    prices = np.full((length + 1, len(symbols)), np.nan, dtype=np.float64)

    for column, symbol in enumerate(symbols):
        frame = context.bars.get(symbol)
        if frame is None or frame.empty or not {"open_time", "close"}.issubset(frame.columns):
            continue
        try:
            open_times = pd.DatetimeIndex(frame["open_time"])
            if open_times.tz is None:
                open_times = open_times.tz_localize("UTC")
            else:
                open_times = open_times.tz_convert("UTC")
        except (TypeError, ValueError):
            open_times = pd.DatetimeIndex(
                pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
            )
        open_start = close_grid[0] - _INTERVAL
        open_end = end - _INTERVAL
        if open_times.is_monotonic_increasing:
            start = int(open_times.searchsorted(open_start, side="left"))
            stop = int(open_times.searchsorted(open_end, side="right"))
            selected_times = open_times[start:stop] + _INTERVAL
            selected_close = frame.iloc[start:stop]["close"]
        else:
            in_window = open_times.notna() & (open_times >= open_start) & (open_times <= open_end)
            selected_times = open_times[in_window] + _INTERVAL
            selected_close = frame.loc[np.asarray(in_window), "close"]
        if len(selected_times) == 0:
            continue
        locations = close_grid.get_indexer(selected_times)
        raw_close = pd.to_numeric(selected_close, errors="coerce").to_numpy(
            dtype=np.float64, copy=False
        )
        usable = (locations >= 0) & np.isfinite(raw_close) & (raw_close > 0.0)
        if not bool(np.any(usable)):
            continue
        usable_locations = locations[usable]
        usable_closes = raw_close[usable]
        counts = np.bincount(usable_locations, minlength=length + 1)
        unique = counts[usable_locations] == 1
        prices[usable_locations[unique], column] = usable_closes[unique]

    result = np.full((length, len(symbols)), np.nan, dtype=np.float64)
    valid = (
        np.isfinite(prices[:-1])
        & np.isfinite(prices[1:])
        & (prices[:-1] > 0.0)
        & (prices[1:] > 0.0)
    )
    result[valid] = np.log(prices[1:][valid]) - np.log(prices[:-1][valid])
    return result


def _ridge_coefficients(slopes: np.ndarray, response: np.ndarray) -> np.ndarray | None:
    if response.size == 0:
        return None
    design = np.column_stack((np.ones(response.size, dtype=np.float64), slopes))
    gram = design.T @ design
    penalty = np.zeros(gram.shape[0], dtype=np.float64)
    penalty[1:] = RIDGE_PENALTY
    gram.flat[:: gram.shape[0] + 1] += penalty
    try:
        coefficients = np.linalg.pinv(gram, rcond=_RCOND) @ (design.T @ response)
    except np.linalg.LinAlgError:
        return None
    if not np.isfinite(coefficients).all():
        return None
    return coefficients


def _community_count(linked_count: int) -> int:
    if linked_count <= 14:
        return 2
    if linked_count <= 19:
        return 3
    return 4


def _lexical_farthest(
    embedding: np.ndarray,
    symbols: Sequence[str],
    selected: Sequence[int],
) -> int:
    selected_set = set(selected)
    candidates: list[tuple[float, str, int]] = []
    for index, symbol in enumerate(symbols):
        if index in selected_set:
            continue
        distances = np.linalg.norm(embedding[index] - embedding[np.asarray(selected)], axis=1)
        candidates.append((-float(np.min(distances)), symbol, index))
    return min(candidates)[2]


def _deterministic_kmeans(
    embedding: np.ndarray,
    symbols: Sequence[str],
    cluster_count: int,
) -> np.ndarray | None:
    first = min(range(len(symbols)), key=lambda index: symbols[index])
    selected = [first]
    while len(selected) < cluster_count:
        selected.append(_lexical_farthest(embedding, symbols, selected))
    centers = embedding[np.asarray(selected)].copy()
    previous: np.ndarray | None = None

    for _ in range(50):
        squared = np.sum((embedding[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        if not np.isfinite(squared).all():
            return None
        assignments = np.argmin(squared, axis=1).astype(np.int64)
        counts = np.bincount(assignments, minlength=cluster_count)

        for empty_cluster in range(cluster_count):
            if counts[empty_cluster] != 0:
                continue
            movable = [
                index for index in range(len(symbols)) if counts[int(assignments[index])] > 1
            ]
            if not movable:
                return None
            donor = min(
                movable,
                key=lambda index: (
                    -float(squared[index, int(assignments[index])]),
                    symbols[index],
                ),
            )
            old_cluster = int(assignments[donor])
            assignments[donor] = empty_cluster
            counts[old_cluster] -= 1
            counts[empty_cluster] += 1

        if previous is not None and np.array_equal(assignments, previous):
            return assignments
        previous = assignments.copy()
        for cluster in range(cluster_count):
            centers[cluster] = np.mean(embedding[assignments == cluster], axis=0)
        if not np.isfinite(centers).all():
            return None

    return previous


def _spectral_communities(
    affinity: np.ndarray,
    linked_indices: np.ndarray,
    all_symbols: Sequence[str],
) -> tuple[np.ndarray, int] | None:
    linked_affinity = affinity[np.ix_(linked_indices, linked_indices)]
    degree = np.sum(linked_affinity, axis=1)
    if (
        not np.isfinite(linked_affinity).all()
        or not np.isfinite(degree).all()
        or np.any(degree <= 0.0)
    ):
        return None
    inverse_root = 1.0 / np.sqrt(degree)
    normalized = inverse_root[:, None] * linked_affinity * inverse_root[None, :]
    laplacian = np.eye(len(linked_indices), dtype=np.float64) - normalized
    try:
        _eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    except np.linalg.LinAlgError:
        return None
    cluster_count = _community_count(len(linked_indices))
    embedding = eigenvectors[:, :cluster_count]
    if not np.isfinite(embedding).all():
        return None
    norms = np.linalg.norm(embedding, axis=1)
    if not np.isfinite(norms).all() or np.any(norms <= _NUMERIC_FLOOR):
        return None
    embedding = embedding / norms[:, None]
    linked_symbols = [all_symbols[index] for index in linked_indices]
    assignments = _deterministic_kmeans(embedding, linked_symbols, cluster_count)
    if assignments is None:
        return None
    communities = np.full(len(all_symbols), -1, dtype=np.int64)
    communities[linked_indices] = assignments
    return communities, cluster_count


class DirectedLaggedDiffusionNetwork:
    """Stateful, deterministic implementation of candidate ``t02-dldn-c01``."""

    def __init__(self) -> None:
        self._previous_eligible: tuple[str, ...] | None = None
        self._fit_state: _FitState | None = None
        self._last_weights: dict[str, float] = {}

    def _flat(self) -> dict[str, float]:
        self._last_weights = {}
        return {}

    def _fit(self, context: DecisionContext, symbols: tuple[str, ...]) -> _FitState | None:
        if len(symbols) < _MIN_VALID_ASSETS or len(set(symbols)) != len(symbols):
            return None
        decision_time = _utc_timestamp(context.decision_time)
        returns = _returns_on_union_grid(
            context,
            symbols,
            end=decision_time,
            length=LOOKBACK,
        )
        market = _cross_sectional_median(returns)
        asset_count = len(symbols)
        alpha = np.full(asset_count, np.nan, dtype=np.float64)
        beta = np.full(asset_count, np.nan, dtype=np.float64)
        center = np.full(asset_count, np.nan, dtype=np.float64)
        scale = np.full(asset_count, np.nan, dtype=np.float64)
        valid_assets = np.zeros(asset_count, dtype=bool)
        standardized = np.full_like(returns, np.nan)

        for asset in range(asset_count):
            valid_rows = np.isfinite(returns[:, asset]) & np.isfinite(market)
            if int(np.sum(valid_rows)) < _MIN_RETURN_ROWS:
                continue
            design = np.column_stack(
                (
                    np.ones(int(np.sum(valid_rows)), dtype=np.float64),
                    market[valid_rows],
                )
            )
            try:
                coefficients = np.linalg.pinv(design, rcond=_RCOND) @ returns[valid_rows, asset]
            except np.linalg.LinAlgError:
                continue
            if not np.isfinite(coefficients).all():
                continue
            residual = returns[valid_rows, asset] - design @ coefficients
            residual_center = float(np.median(residual))
            residual_scale = max(
                _SCALE_FLOOR,
                1.4826 * float(np.median(np.abs(residual - residual_center))),
            )
            if not np.isfinite(residual_center) or not np.isfinite(residual_scale):
                continue
            alpha[asset], beta[asset] = coefficients
            center[asset] = residual_center
            scale[asset] = residual_scale
            valid_assets[asset] = True
            standardized[valid_rows, asset] = np.clip(
                (residual - residual_center) / residual_scale,
                -4.0,
                4.0,
            )

        if int(np.sum(valid_assets)) < _MIN_VALID_ASSETS:
            return None

        influence = np.zeros((asset_count, asset_count), dtype=np.float64)
        confidence = np.zeros(asset_count, dtype=np.float64)
        origin_predictors = standardized[:-1]

        for follower in range(asset_count):
            if not valid_assets[follower]:
                continue
            response = standardized[1:, follower]
            response_rows = np.flatnonzero(np.isfinite(response))
            label_count = len(response_rows)
            if label_count < 2:
                continue
            split = label_count // 2
            first_rows = response_rows[:split]
            second_rows = response_rows[split:]
            if len(first_rows) == 0 or len(second_rows) == 0:
                continue
            leader_order = [follower] + [index for index in range(asset_count) if index != follower]
            full_slopes = np.nan_to_num(
                origin_predictors[np.ix_(response_rows, leader_order)],
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            first_slopes = np.nan_to_num(
                origin_predictors[np.ix_(first_rows, leader_order)],
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            second_slopes = np.nan_to_num(
                origin_predictors[np.ix_(second_rows, leader_order)],
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            full_coefficients = _ridge_coefficients(full_slopes, response[response_rows])
            first_coefficients = _ridge_coefficients(first_slopes, response[first_rows])
            second_coefficients = _ridge_coefficients(second_slopes, response[second_rows])
            if (
                full_coefficients is None
                or first_coefficients is None
                or second_coefficients is None
            ):
                continue
            coefficient_position = {
                leader: position + 1 for position, leader in enumerate(leader_order)
            }
            candidates: list[tuple[float, str, int, float]] = []
            for leader in range(asset_count):
                if leader == follower:
                    continue
                full_overlap = int(np.sum(np.isfinite(origin_predictors[response_rows, leader])))
                first_overlap = int(np.sum(np.isfinite(origin_predictors[first_rows, leader])))
                second_overlap = int(np.sum(np.isfinite(origin_predictors[second_rows, leader])))
                if (
                    full_overlap < _MIN_EDGE_OVERLAP
                    or first_overlap < _MIN_HALF_OVERLAP
                    or second_overlap < _MIN_HALF_OVERLAP
                ):
                    continue
                position = coefficient_position[leader]
                full_value = float(full_coefficients[position])
                first_value = float(first_coefficients[position])
                second_value = float(second_coefficients[position])
                if not np.isfinite([full_value, first_value, second_value]).all():
                    continue
                full_sign = float(np.sign(full_value))
                if (
                    full_sign == 0.0
                    or full_sign != float(np.sign(first_value))
                    or full_sign != float(np.sign(second_value))
                    or abs(full_value) < EDGE_THRESHOLD
                ):
                    continue
                reliability = min(abs(first_value), abs(second_value)) / max(
                    abs(first_value), abs(second_value), _NUMERIC_FLOOR
                )
                candidates.append((-abs(full_value), symbols[leader], leader, float(reliability)))

            kept = sorted(candidates)[:MAX_LEADERS]
            if not kept:
                continue
            reliabilities: list[float] = []
            for _rank, _symbol, leader, reliability in kept:
                position = coefficient_position[leader]
                full_value = float(full_coefficients[position])
                influence[follower, leader] = (
                    float(np.sign(full_value))
                    * max(abs(full_value) - EDGE_THRESHOLD, 0.0)
                    * reliability
                )
                reliabilities.append(reliability)
            row_norm = float(np.sum(np.abs(influence[follower])))
            if row_norm > 0.0 and np.isfinite(row_norm):
                influence[follower] /= row_norm
            else:
                influence[follower] = 0.0
            confidence[follower] = float(np.mean(reliabilities)) * min(
                1.0, label_count / (LOOKBACK - 1)
            )

        affinity = np.abs(influence) + np.abs(influence.T)
        np.fill_diagonal(affinity, 0.0)
        degree = np.sum(affinity, axis=1)
        linked = np.isfinite(degree) & (degree > 0.0)
        if int(np.sum(linked)) < _MIN_VALID_ASSETS:
            return None
        linked_indices = np.flatnonzero(linked)
        spectral = _spectral_communities(affinity, linked_indices, symbols)
        if spectral is None:
            return None
        communities, cluster_count = spectral
        return _FitState(
            symbols=symbols,
            alpha=alpha,
            beta=beta,
            residual_center=center,
            residual_scale=scale,
            valid=valid_assets,
            influence=influence,
            confidence=confidence,
            linked=linked,
            communities=communities,
            community_count=cluster_count,
        )

    def _desired_weights(
        self,
        context: DecisionContext,
        state: _FitState,
    ) -> dict[str, float] | None:
        decision_time = _utc_timestamp(context.decision_time)
        returns = _returns_on_union_grid(
            context,
            state.symbols,
            end=decision_time,
            length=_VOLATILITY_BARS,
        )
        market = _cross_sectional_median(returns)
        residuals = np.full_like(returns, np.nan)
        current_z = np.full(len(state.symbols), np.nan, dtype=np.float64)
        sigma = np.full(len(state.symbols), np.nan, dtype=np.float64)

        for asset in range(len(state.symbols)):
            if not state.valid[asset]:
                continue
            valid_rows = np.isfinite(returns[:, asset]) & np.isfinite(market)
            residuals[valid_rows, asset] = (
                returns[valid_rows, asset]
                - state.alpha[asset]
                - state.beta[asset] * market[valid_rows]
            )
            if valid_rows[-1]:
                current_z[asset] = float(
                    np.clip(
                        (residuals[-1, asset] - state.residual_center[asset])
                        / state.residual_scale[asset],
                        -4.0,
                        4.0,
                    )
                )
            finite_residual = residuals[np.isfinite(residuals[:, asset]), asset]
            if len(finite_residual) >= _MIN_VOLATILITY_ROWS:
                sample_std = float(np.std(finite_residual, ddof=1))
                if np.isfinite(sample_std):
                    sigma[asset] = sample_std

        active = state.linked & np.isfinite(current_z) & np.isfinite(sigma)
        active_indices = np.flatnonzero(active)
        if len(active_indices) == 0:
            return None
        sigma_floor = max(
            _SCALE_FLOOR,
            float(np.percentile(sigma[active_indices], 20.0, method="linear")),
        )
        floored_sigma = np.maximum(sigma[active_indices], sigma_floor)
        predictor = np.nan_to_num(current_z, nan=0.0, posinf=0.0, neginf=0.0)
        gap = state.confidence * (state.influence @ predictor - GAP_REVERSION * predictor)
        score = gap[active_indices] / floored_sigma
        if not np.isfinite(score).all():
            return None
        score_median = float(np.median(score))
        score_scale = 1.4826 * float(np.median(np.abs(score - score_median)))
        if not np.isfinite(score_scale) or score_scale <= _NUMERIC_FLOOR:
            return None
        score = np.clip(
            score,
            score_median - 4.0 * score_scale,
            score_median + 4.0 * score_scale,
        )

        community_dummies = np.zeros((len(active_indices), state.community_count), dtype=np.float64)
        active_communities = state.communities[active_indices]
        community_dummies[np.arange(len(active_indices)), active_communities] = 1.0
        beta_demeaned = state.beta[active_indices].copy()
        for community in range(state.community_count):
            members = active_communities == community
            if bool(np.any(members)):
                beta_demeaned[members] -= float(np.mean(beta_demeaned[members]))
        factors = np.column_stack((community_dummies, beta_demeaned))
        try:
            projection = factors @ (
                np.linalg.pinv(factors.T @ factors, rcond=_RCOND) @ (factors.T @ score)
            )
        except np.linalg.LinAlgError:
            return None
        neutral = score - projection
        if not np.isfinite(neutral).all():
            return None
        absolute_sum = float(np.sum(np.abs(neutral)))
        maximum = float(np.max(np.abs(neutral))) if len(neutral) else 0.0
        if (
            not np.isfinite(absolute_sum)
            or not np.isfinite(maximum)
            or absolute_sum <= _NUMERIC_FLOOR
            or maximum <= _NUMERIC_FLOOR
        ):
            return None
        gross = min(0.80, 0.075 * absolute_sum / maximum)
        active_weights = gross * neutral / absolute_sum
        if not np.isfinite(active_weights).all():
            return None
        weights = {symbol: 0.0 for symbol in state.symbols}
        for row, asset in enumerate(active_indices):
            weights[state.symbols[asset]] = float(active_weights[row])
        return weights

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if seed != EXPECTED_SEED:
            raise ValueError(f"strategy seed must be {EXPECTED_SEED}")
        decision_time = _utc_timestamp(context.decision_time)
        symbols = tuple(str(symbol) for symbol in context.eligible_symbols)
        tuple_changed = self._previous_eligible is None or symbols != self._previous_eligible
        monday_refit = decision_time.weekday() == 0 and decision_time == decision_time.normalize()
        refit = tuple_changed or monday_refit
        self._previous_eligible = symbols

        if refit:
            self._fit_state = self._fit(context, symbols)
            if self._fit_state is None:
                return self._flat()
        state = self._fit_state
        if state is None or state.symbols != symbols:
            return self._flat()
        desired = self._desired_weights(context, state)
        if desired is None:
            return self._flat()
        if refit:
            self._last_weights = dict(desired)
            return desired

        distance_symbols = set(desired) | set(self._last_weights)
        distance = float(
            sum(
                abs(desired.get(symbol, 0.0) - self._last_weights.get(symbol, 0.0))
                for symbol in sorted(distance_symbols)
            )
        )
        if distance < HYSTERESIS:
            return None
        self._last_weights = dict(desired)
        return desired


def build_strategy() -> TargetStrategy:
    """Return one fresh frozen strategy instance for the canonical worker."""

    return DirectedLaggedDiffusionNetwork()

"""Deterministic correlation-network centrality rotation for Team 08."""

from typing import Mapping

import numpy as np
import pandas as pd


class CorrelationNetworkCentralityRotation:
    """Rotate between graph-central and graph-peripheral eligible coins."""

    formation_bars = 252
    graph_half_bars = 126
    edge_threshold = 0.55
    topology_change_threshold = 0.05
    maximum_coins_per_side = 5
    maximum_symbol_weight = 0.08

    @staticmethod
    def _utc_timestamp(value) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    @staticmethod
    def _completed_log_returns(frame, decision_time: pd.Timestamp) -> pd.Series:
        required = {"open_time", "close"}
        if frame is None or not required.issubset(frame.columns):
            return pd.Series(dtype=float)

        open_time = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
        close = pd.to_numeric(frame["close"], errors="coerce")
        completed = open_time.notna() & (open_time + pd.Timedelta(hours=8) <= decision_time)
        valid = completed & np.isfinite(close) & (close > 0.0)
        if int(valid.sum()) < 2:
            return pd.Series(dtype=float)

        prices = pd.Series(
            close.loc[valid].to_numpy(dtype=float),
            index=open_time.loc[valid],
            dtype=float,
        )
        prices = prices.groupby(level=0, sort=True).last().sort_index()
        prices = prices.iloc[-(CorrelationNetworkCentralityRotation.formation_bars + 1) :]
        returns = np.log(prices).diff().dropna()
        return returns.replace([np.inf, -np.inf], np.nan).dropna()

    @staticmethod
    def _correlation(values: np.ndarray) -> np.ndarray:
        symbol_count = values.shape[1]
        correlation = np.eye(symbol_count, dtype=float)
        standard_deviation = np.std(values, axis=0, ddof=1)
        usable = np.isfinite(standard_deviation) & (standard_deviation > 1.0e-12)
        usable_indices = np.flatnonzero(usable)
        if usable_indices.size < 2:
            return correlation

        usable_values = values[:, usable_indices]
        usable_correlation = np.corrcoef(usable_values, rowvar=False)
        usable_correlation = np.atleast_2d(usable_correlation)
        usable_correlation = np.nan_to_num(
            usable_correlation, nan=0.0, posinf=0.0, neginf=0.0
        )
        correlation[np.ix_(usable_indices, usable_indices)] = usable_correlation
        np.fill_diagonal(correlation, 1.0)
        return correlation

    def _graph(self, returns: pd.DataFrame) -> np.ndarray:
        correlation = self._correlation(returns.to_numpy(dtype=float))
        adjacency = np.where(
            correlation >= self.edge_threshold,
            correlation - self.edge_threshold,
            0.0,
        )
        np.fill_diagonal(adjacency, 0.0)
        return adjacency

    @staticmethod
    def _largest_component_share(adjacency: np.ndarray) -> float:
        symbol_count = adjacency.shape[0]
        if symbol_count == 0:
            return 0.0

        linked = adjacency > 0.0
        unseen = set(range(symbol_count))
        largest = 0
        while unseen:
            start = min(unseen)
            unseen.remove(start)
            stack = [start]
            component_size = 0
            while stack:
                node = stack.pop()
                component_size += 1
                neighbors = np.flatnonzero(linked[node])
                for neighbor in neighbors:
                    neighbor_int = int(neighbor)
                    if neighbor_int in unseen:
                        unseen.remove(neighbor_int)
                        stack.append(neighbor_int)
            largest = max(largest, component_size)
        return float(largest) / float(symbol_count)

    @classmethod
    def _connectivity(cls, adjacency: np.ndarray) -> float:
        symbol_count = adjacency.shape[0]
        possible_edges = symbol_count * (symbol_count - 1) / 2
        if possible_edges <= 0:
            return 0.0
        observed_edges = float(np.count_nonzero(np.triu(adjacency > 0.0, k=1)))
        edge_density = observed_edges / possible_edges
        component_share = cls._largest_component_share(adjacency)
        return 0.5 * edge_density + 0.5 * component_share

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed
        decision_time = self._utc_timestamp(context.decision_time)
        if not (
            decision_time.weekday() == 0
            and decision_time.hour == 0
            and decision_time.minute == 0
            and decision_time.second == 0
        ):
            return None

        symbols = sorted(set(context.eligible_symbols))
        if len(symbols) < 4:
            return {}

        return_series = {}
        for symbol in symbols:
            series = self._completed_log_returns(context.bars.get(symbol), decision_time)
            if len(series) >= self.formation_bars:
                return_series[symbol] = series

        usable_symbols = sorted(return_series)
        if len(usable_symbols) < 4:
            return {}

        aligned = pd.concat(
            [return_series[symbol].rename(symbol) for symbol in usable_symbols],
            axis=1,
            join="inner",
        ).dropna()
        aligned = aligned.iloc[-self.formation_bars :]
        if len(aligned) < self.formation_bars:
            return {}

        previous = aligned.iloc[: self.graph_half_bars]
        current = aligned.iloc[-self.graph_half_bars :]
        previous_graph = self._graph(previous)
        current_graph = self._graph(current)
        topology_change = self._connectivity(current_graph) - self._connectivity(
            previous_graph
        )
        if abs(topology_change) < self.topology_change_threshold:
            return {}

        centrality = np.sum(current_graph, axis=1)
        central_order = sorted(
            range(len(usable_symbols)),
            key=lambda index: (-float(centrality[index]), usable_symbols[index]),
        )
        peripheral_order = sorted(
            range(len(usable_symbols)),
            key=lambda index: (float(centrality[index]), usable_symbols[index]),
        )
        side_count = min(self.maximum_coins_per_side, len(usable_symbols) // 2)
        central_indices = central_order[:side_count]
        central_set = set(central_indices)
        peripheral_indices = [
            index for index in peripheral_order if index not in central_set
        ][:side_count]
        if len(peripheral_indices) != side_count:
            return {}

        if topology_change < 0.0:
            long_indices, short_indices = central_indices, peripheral_indices
        else:
            long_indices, short_indices = peripheral_indices, central_indices

        symbol_weight = min(
            self.maximum_symbol_weight,
            0.4 / float(side_count),
        )
        weights = {symbol: 0.0 for symbol in symbols}
        for index in long_indices:
            weights[usable_symbols[index]] = float(symbol_weight)
        for index in short_indices:
            weights[usable_symbols[index]] = float(-symbol_weight)
        return weights


def build_strategy():
    return CorrelationNetworkCentralityRotation()

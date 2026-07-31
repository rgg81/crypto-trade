"""Weekly residual-trend consensus baseline for Team 01."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


class ResidualTrendConsensusStrategy:
    """Rank persistent multi-horizon trends after lagged-market residualization."""

    HORIZON_DAYS = (28, 84, 168)
    BARS_PER_DAY = 3
    MIN_OBSERVATION_FRACTION = 0.85
    MIN_MARKET_BREADTH = 6
    RETURN_CLIP = 0.35
    BETA_CLIP = 3.0
    MIN_ABS_HORIZON_T = 0.15
    MIN_POSITIONS_PER_SIDE = 2
    MAX_POSITIONS_PER_SIDE = 3
    TARGET_GROSS = 0.80

    @staticmethod
    def _utc_times(values: pd.Series) -> pd.Series:
        """Convert common timestamp encodings without changing the supplied frame."""
        if pd.api.types.is_numeric_dtype(values):
            numeric = pd.to_numeric(values, errors="coerce")
            finite = numeric[np.isfinite(numeric)]
            if finite.empty:
                return pd.to_datetime(numeric, utc=True, errors="coerce")
            scale = float(finite.abs().median())
            if scale >= 1.0e17:
                unit = "ns"
            elif scale >= 1.0e14:
                unit = "us"
            elif scale >= 1.0e11:
                unit = "ms"
            else:
                unit = "s"
            return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
        return pd.to_datetime(values, utc=True, errors="coerce")

    def _completed_returns(
        self, frame: pd.DataFrame, boundary: pd.Timestamp
    ) -> pd.Series | None:
        if "open_time" not in frame.columns or "close" not in frame.columns:
            return None

        times = self._utc_times(frame["open_time"])
        closes = pd.to_numeric(frame["close"], errors="coerce")
        complete = times.notna() & (times + pd.Timedelta(hours=8) <= boundary)
        valid = complete & np.isfinite(closes) & (closes > 0.0)

        clean = pd.DataFrame(
            {"open_time": times[valid], "close": closes[valid].astype(float)}
        )
        clean = clean.sort_values("open_time", kind="mergesort")
        clean = clean.drop_duplicates(subset="open_time", keep="last")
        if len(clean) < 2:
            return None

        log_close = np.log(clean.set_index("open_time")["close"])
        returns = log_close.diff().replace([np.inf, -np.inf], np.nan).dropna()
        returns = returns.clip(lower=-self.RETURN_CLIP, upper=self.RETURN_CLIP)
        return returns if not returns.empty else None

    @staticmethod
    def _path_quality(values: np.ndarray) -> float:
        """R-squared of cumulative residual return against elapsed bars."""
        path = np.cumsum(values)
        if len(path) < 3 or float(np.std(path, ddof=1)) <= 0.0:
            return 0.0
        elapsed = np.arange(len(path), dtype=float)
        correlation = float(np.corrcoef(elapsed, path)[0, 1])
        if not np.isfinite(correlation):
            return 0.0
        return correlation * correlation

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The construction has no random branch; symbol ties break lexically.

        boundary = pd.Timestamp(context.decision_time)
        if boundary.tzinfo is None:
            boundary = boundary.tz_localize("UTC")
        else:
            boundary = boundary.tz_convert("UTC")

        # The weekly gate limits endogenous turnover and matches membership refreshes.
        if boundary.weekday() != 0 or boundary.hour != 0 or boundary.minute != 0:
            return None

        symbols = sorted(set(context.eligible_symbols))
        series_by_symbol: dict[str, pd.Series] = {}
        for symbol in symbols:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            returns = self._completed_returns(frame, boundary)
            if returns is not None:
                series_by_symbol[symbol] = returns

        if len(series_by_symbol) < self.MIN_MARKET_BREADTH:
            return {}

        panel = pd.concat(series_by_symbol, axis=1).sort_index()
        panel = panel.loc[~panel.index.duplicated(keep="last")]
        breadth = panel.notna().sum(axis=1)
        market_return = panel.mean(axis=1, skipna=True).where(
            breadth >= self.MIN_MARKET_BREADTH
        )
        lagged_market = market_return.shift(1)

        scores: dict[str, float] = {}
        beta_days = max(self.HORIZON_DAYS)
        beta_start = boundary - pd.Timedelta(days=beta_days)
        beta_required = int(
            np.ceil(beta_days * self.BARS_PER_DAY * self.MIN_OBSERVATION_FRACTION)
        )

        for symbol in sorted(series_by_symbol):
            paired = pd.concat(
                [panel[symbol].rename("asset"), lagged_market.rename("market_lag")],
                axis=1,
            ).loc[beta_start:]
            paired = paired.dropna()
            if len(paired) < beta_required:
                continue

            asset = paired["asset"].to_numpy(dtype=float)
            market_lag = paired["market_lag"].to_numpy(dtype=float)
            centered_market = market_lag - float(np.mean(market_lag))
            market_variance = float(np.mean(centered_market * centered_market))
            if not np.isfinite(market_variance) or market_variance <= 1.0e-12:
                continue
            centered_asset = asset - float(np.mean(asset))
            beta = float(np.mean(centered_asset * centered_market) / market_variance)
            beta = float(np.clip(beta, -self.BETA_CLIP, self.BETA_CLIP))

            residual = paired["asset"] - beta * paired["market_lag"]
            horizon_t: list[float] = []
            horizon_quality: list[float] = []
            valid_horizons = True
            for days in self.HORIZON_DAYS:
                start = boundary - pd.Timedelta(days=days)
                values = residual.loc[start:].to_numpy(dtype=float)
                required = int(
                    np.ceil(days * self.BARS_PER_DAY * self.MIN_OBSERVATION_FRACTION)
                )
                if len(values) < required:
                    valid_horizons = False
                    break
                standard_deviation = float(np.std(values, ddof=1))
                if not np.isfinite(standard_deviation) or standard_deviation <= 1.0e-12:
                    valid_horizons = False
                    break
                trend_t = float(np.mean(values) * np.sqrt(len(values)) / standard_deviation)
                if not np.isfinite(trend_t):
                    valid_horizons = False
                    break
                horizon_t.append(trend_t)
                horizon_quality.append(self._path_quality(values))

            if not valid_horizons:
                continue
            signs = np.sign(np.asarray(horizon_t, dtype=float))
            if not np.all(signs == signs[0]):
                continue
            if min(abs(value) for value in horizon_t) < self.MIN_ABS_HORIZON_T:
                continue

            direction = float(signs[0])
            strength = float(np.median(np.abs(horizon_t)))
            quality_multiplier = 0.5 + 0.5 * float(np.mean(horizon_quality))
            scores[symbol] = direction * strength * quality_multiplier

        positive = sorted(
            ((symbol, score) for symbol, score in scores.items() if score > 0.0),
            key=lambda item: (-item[1], item[0]),
        )
        negative = sorted(
            ((symbol, score) for symbol, score in scores.items() if score < 0.0),
            key=lambda item: (item[1], item[0]),
        )
        side_count = min(
            self.MAX_POSITIONS_PER_SIDE, len(positive), len(negative)
        )
        if side_count < self.MIN_POSITIONS_PER_SIDE:
            return {}

        side_weight = (self.TARGET_GROSS / 2.0) / side_count
        targets: dict[str, float] = {}
        for symbol, _ in positive[:side_count]:
            targets[symbol] = float(side_weight)
        for symbol, _ in negative[:side_count]:
            targets[symbol] = float(-side_weight)
        return targets


def build_strategy() -> ResidualTrendConsensusStrategy:
    return ResidualTrendConsensusStrategy()

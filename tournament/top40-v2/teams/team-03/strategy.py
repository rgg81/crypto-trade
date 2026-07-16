"""Deterministic Team 03 residual-liquidity-shock absorption strategy.

The strategy uses only bars closed by the decision boundary and funding rows strictly before it.
It rebalances once per day at 00:00 UTC.  Positive scores identify unusually negative
idiosyncratic shocks with liquidation/crowding evidence (long candidates); negative scores identify
the symmetric crowded upside exhaustion (short candidates).
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

EXPECTED_SEED = 20260801
BTC_SYMBOL = "BTCUSDT"
INTERVAL_HOURS = 8


@dataclasses.dataclass(frozen=True, slots=True)
class Parameters:
    rebalance_hour_utc: int = 0
    shock_horizon_bars: int = 3
    beta_lookback_days: int = 30
    residual_volatility_lookback_days: int = 21
    volume_lookback_days: int = 30
    volume_amplifier: float = 0.35
    funding_recent_days: int = 3
    funding_lookback_days: int = 30
    funding_weight: float = 0.25
    rank_tail_fraction: float = 0.25
    minimum_valid_symbols: int = 20
    minimum_names_per_side: int = 5
    trend_lookback_days: int = 60
    trend_threshold: float = 0.10
    directional_gross_tilt: float = 0.05
    total_gross: float = 0.80
    per_symbol_target_cap: float = 0.08
    residual_variance_floor: float = 1.0e-8
    minimum_funding_events: int = 12

    def validate(self) -> None:
        if self.rebalance_hour_utc not in range(24):
            raise ValueError("rebalance_hour_utc is invalid")
        if self.shock_horizon_bars < 1:
            raise ValueError("shock_horizon_bars must be positive")
        if (
            min(
                self.beta_lookback_days,
                self.residual_volatility_lookback_days,
                self.volume_lookback_days,
                self.funding_recent_days,
                self.funding_lookback_days,
                self.trend_lookback_days,
            )
            < 2
        ):
            raise ValueError("all lookbacks must span at least two days")
        if not 0.0 <= self.volume_amplifier <= 1.0:
            raise ValueError("volume_amplifier must be in [0, 1]")
        if not 0.0 <= self.funding_weight <= 1.0:
            raise ValueError("funding_weight must be in [0, 1]")
        if not 0.05 <= self.rank_tail_fraction <= 0.50:
            raise ValueError("rank_tail_fraction must be in [0.05, 0.50]")
        if self.minimum_valid_symbols < 2 * self.minimum_names_per_side:
            raise ValueError("minimum_valid_symbols cannot underfill both sleeves")
        if not 0.0 <= self.directional_gross_tilt <= 0.125:
            raise ValueError("directional_gross_tilt breaches the net-exposure design")
        if not 0.0 < self.total_gross <= 1.0:
            raise ValueError("total_gross must be in (0, 1]")
        if not 0.0 < self.per_symbol_target_cap <= 0.10:
            raise ValueError("per_symbol_target_cap must be in (0, 0.10]")
        if self.residual_variance_floor <= 0.0:
            raise ValueError("residual_variance_floor must be positive")


DEFAULT_PARAMETERS = Parameters()


@dataclasses.dataclass(frozen=True, slots=True)
class _Signal:
    symbol: str
    score: float


def _past_bars(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    required = {"open_time", "close", "quote_volume"}
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=["close", "quote_volume"])
    result = frame.loc[:, ["open_time", "close", "quote_volume"]].copy()
    result["open_time"] = pd.to_datetime(result["open_time"], utc=True, errors="raise")
    result["close"] = pd.to_numeric(result["close"], errors="raise")
    result["quote_volume"] = pd.to_numeric(result["quote_volume"], errors="raise")
    close_time = result["open_time"] + pd.Timedelta(hours=INTERVAL_HOURS)
    result = result.loc[close_time <= decision_time].sort_values("open_time")
    result = result.drop_duplicates("open_time", keep="last")
    if (
        result.empty
        or not np.isfinite(result[["close", "quote_volume"]].to_numpy()).all()
        or (result["close"] <= 0.0).any()
        or (result["quote_volume"] < 0.0).any()
    ):
        return result.iloc[0:0].copy()
    return result.set_index("open_time")


def _log_returns(frame: pd.DataFrame) -> pd.Series:
    return np.log(frame["close"].astype(float)).diff().dropna()


def _aligned_returns(
    symbol_frame: pd.DataFrame,
    btc_returns: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    joined = pd.concat(
        [_log_returns(symbol_frame).rename("symbol"), btc_returns.rename("btc")],
        axis=1,
        join="inner",
    ).dropna()
    return joined["symbol"], joined["btc"]


def _funding_zscore(
    funding: pd.DataFrame,
    symbol: str,
    parameters: Parameters,
) -> float:
    if funding.empty or not {"symbol", "funding_rate"}.issubset(funding.columns):
        return 0.0
    values = pd.to_numeric(
        funding.loc[funding["symbol"].astype(str).eq(symbol), "funding_rate"],
        errors="coerce",
    ).dropna()
    values = values[np.isfinite(values.to_numpy())]
    lookback = parameters.funding_lookback_days * 3
    recent = parameters.funding_recent_days * 3
    if len(values) < max(parameters.minimum_funding_events, recent + 1):
        return 0.0
    history = values.iloc[-lookback:]
    scale = float(history.std(ddof=1))
    if not math.isfinite(scale) or scale <= 1.0e-12:
        return 0.0
    zscore = float(values.iloc[-recent:].mean() / scale)
    return float(np.clip(zscore, -3.0, 3.0))


def _signal_for_symbol(
    symbol: str,
    frame: pd.DataFrame,
    btc_returns: pd.Series,
    funding: pd.DataFrame,
    parameters: Parameters,
) -> _Signal | None:
    symbol_returns, aligned_btc = _aligned_returns(frame, btc_returns)
    beta_bars = parameters.beta_lookback_days * 3
    volatility_bars = parameters.residual_volatility_lookback_days * 3
    required = max(beta_bars, volatility_bars) + parameters.shock_horizon_bars
    if len(symbol_returns) < required:
        return None
    history_stop = -parameters.shock_horizon_bars
    beta_history_start = -(beta_bars + parameters.shock_horizon_bars)
    beta_sample = pd.concat(
        [
            symbol_returns.iloc[beta_history_start:history_stop],
            aligned_btc.iloc[beta_history_start:history_stop],
        ],
        axis=1,
    ).dropna()
    btc_variance = float(beta_sample.iloc[:, 1].var(ddof=1))
    if not math.isfinite(btc_variance) or btc_variance <= parameters.residual_variance_floor:
        return None
    beta = float(beta_sample.iloc[:, 0].cov(beta_sample.iloc[:, 1]) / btc_variance)
    if not math.isfinite(beta):
        return None
    beta = float(np.clip(beta, -1.0, 3.0))
    residuals = symbol_returns - beta * aligned_btc
    residual_history = residuals.iloc[
        -(volatility_bars + parameters.shock_horizon_bars) : history_stop
    ]
    residual_scale = float(residual_history.std(ddof=1))
    if not math.isfinite(residual_scale) or residual_scale <= parameters.residual_variance_floor:
        return None
    shock = float(residuals.iloc[-parameters.shock_horizon_bars :].sum())
    shock_z = shock / (residual_scale * math.sqrt(parameters.shock_horizon_bars))

    volume = frame["quote_volume"].astype(float)
    rolling_volume = volume.rolling(parameters.shock_horizon_bars).sum().dropna()
    volume_history = rolling_volume.iloc[-parameters.volume_lookback_days * 3 :]
    if len(volume_history) < parameters.volume_lookback_days:
        return None
    baseline_volume = float(volume_history.median())
    if not math.isfinite(baseline_volume) or baseline_volume <= 0.0:
        return None
    volume_surprise = math.log(max(float(rolling_volume.iloc[-1]), 1.0) / baseline_volume)
    volume_multiplier = 1.0 + parameters.volume_amplifier * float(
        np.clip(volume_surprise, 0.0, 2.0)
    )
    funding_z = _funding_zscore(funding, symbol, parameters)
    score = -shock_z * volume_multiplier - parameters.funding_weight * funding_z
    if not math.isfinite(score):
        return None
    return _Signal(symbol=symbol, score=float(score))


def _btc_trend(btc_returns: pd.Series, parameters: Parameters) -> float:
    bars = parameters.trend_lookback_days * 3
    if len(btc_returns) < bars:
        return 0.0
    value = float(btc_returns.iloc[-bars:].sum())
    return math.expm1(value) if math.isfinite(value) else 0.0


def _sleeve_grosses(trend: float, parameters: Parameters) -> tuple[float, float]:
    half = parameters.total_gross / 2.0
    if trend > parameters.trend_threshold:
        return half + parameters.directional_gross_tilt, half - parameters.directional_gross_tilt
    if trend < -parameters.trend_threshold:
        return half - parameters.directional_gross_tilt, half + parameters.directional_gross_tilt
    return half, half


def _equal_sleeve(
    symbols: list[str],
    gross: float,
    *,
    sign: float,
    cap: float,
) -> dict[str, float]:
    if not symbols:
        return {}
    per_name = gross / len(symbols)
    if per_name > cap + 1.0e-12:
        return {}
    return {symbol: sign * per_name for symbol in symbols}


class ResidualLiquidityShockAbsorptionStrategy:
    def __init__(self, parameters: Parameters = DEFAULT_PARAMETERS):
        parameters.validate()
        self.parameters = parameters

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if seed != EXPECTED_SEED:
            raise ValueError("Team 03 strategy received an unexpected seed")
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            raise ValueError("decision_time must be timezone-aware")
        decision_time = decision_time.tz_convert("UTC")
        if decision_time.hour != self.parameters.rebalance_hour_utc:
            return None

        btc_raw = context.bars.get(BTC_SYMBOL)
        if btc_raw is None:
            return {}
        btc_frame = _past_bars(btc_raw, decision_time)
        btc_returns = _log_returns(btc_frame)
        required_btc_bars = (
            max(
                self.parameters.beta_lookback_days,
                self.parameters.residual_volatility_lookback_days,
            )
            * 3
            + self.parameters.shock_horizon_bars
        )
        if len(btc_returns) < required_btc_bars:
            return {}

        signals: list[_Signal] = []
        for symbol in sorted(str(value) for value in context.eligible_symbols):
            if symbol == BTC_SYMBOL:
                continue
            raw_frame = context.bars.get(symbol)
            if raw_frame is None:
                continue
            frame = _past_bars(raw_frame, decision_time)
            signal = _signal_for_symbol(
                symbol,
                frame,
                btc_returns,
                context.funding,
                self.parameters,
            )
            if signal is not None:
                signals.append(signal)
        if len(signals) < self.parameters.minimum_valid_symbols:
            return {}

        tail_count = max(
            self.parameters.minimum_names_per_side,
            int(math.floor(len(signals) * self.parameters.rank_tail_fraction)),
        )
        if 2 * tail_count > len(signals):
            return {}
        ranked = sorted(signals, key=lambda item: (item.score, item.symbol))
        shorts = [item.symbol for item in ranked[:tail_count]]
        longs = [item.symbol for item in reversed(ranked[-tail_count:])]
        if set(longs) & set(shorts):
            raise AssertionError("long and short selections overlap")

        long_gross, short_gross = _sleeve_grosses(
            _btc_trend(btc_returns, self.parameters),
            self.parameters,
        )
        weights = _equal_sleeve(
            longs,
            long_gross,
            sign=1.0,
            cap=self.parameters.per_symbol_target_cap,
        )
        weights.update(
            _equal_sleeve(
                shorts,
                short_gross,
                sign=-1.0,
                cap=self.parameters.per_symbol_target_cap,
            )
        )
        if len(weights) != 2 * tail_count:
            return {}
        gross = math.fsum(abs(value) for value in weights.values())
        net = math.fsum(weights.values())
        if gross > 1.0 + 1.0e-12 or abs(net) > 0.25 + 1.0e-12:
            raise AssertionError("constructed targets violate frozen exposure limits")
        return weights


def build_strategy() -> ResidualLiquidityShockAbsorptionStrategy:
    return ResidualLiquidityShockAbsorptionStrategy()

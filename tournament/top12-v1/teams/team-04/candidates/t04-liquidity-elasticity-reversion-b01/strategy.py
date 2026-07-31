from __future__ import annotations

import numpy as np
import pandas as pd


FORMATION_BARS = 63
OWN_HISTORY_BARS = 270
MINIMUM_HISTORY_OBSERVATIONS = 90
CAPACITY_ANCHOR_MINIMUM_BARS = 126
CAPACITY_RATIO_MINIMUM = 0.05
CAPACITY_RATIO_MAXIMUM = 20.0
ROBUST_Z_CLIP = 4.0
REBALANCE_HOURS = 24
SIDE_GROSS_BUDGET = 0.39
SYMBOL_WEIGHT_CAP = 0.079


def _robust_location_scale(values):
    clean = pd.Series(values, dtype="float64").replace(
        [np.inf, -np.inf], np.nan
    ).dropna()
    if clean.empty:
        return np.nan, np.nan

    location = float(clean.median())
    scale = float((clean - location).abs().median() * 1.4826)
    if not np.isfinite(scale) or scale <= 1.0e-12:
        scale = float(clean.std(ddof=0))
    if not np.isfinite(scale) or scale <= 1.0e-12:
        return location, np.nan
    return location, scale


class LiquidityImpactElasticityReversion:
    def __init__(self):
        self._last_rebalance_time = None

    def target_weights(self, context, *, seed):
        del seed

        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        if self._last_rebalance_time is not None:
            next_allowed = self._last_rebalance_time + pd.Timedelta(
                hours=REBALANCE_HOURS
            )
            if decision_time < next_allowed:
                return None
        self._last_rebalance_time = decision_time

        symbols = sorted(set(context.eligible_symbols))
        flat_book = {symbol: 0.0 for symbol in symbols}
        own_history_z = {}

        for symbol in symbols:
            frame = context.bars.get(symbol)
            if frame is None or frame.empty:
                continue
            required = {"open_time", "close", "quote_volume"}
            if not required.issubset(frame.columns):
                continue

            data = frame.loc[:, ["open_time", "close", "quote_volume"]].copy()
            data["open_time"] = pd.to_datetime(
                data["open_time"], utc=True, errors="coerce"
            )
            data["close"] = pd.to_numeric(data["close"], errors="coerce")
            data["quote_volume"] = pd.to_numeric(
                data["quote_volume"], errors="coerce"
            )
            completed = (
                data["open_time"] + pd.Timedelta(hours=8) <= decision_time
            )
            data = data.loc[completed]
            data = data.dropna(subset=["open_time", "close", "quote_volume"])
            data = data.loc[
                (data["close"] > 0.0) & (data["quote_volume"] > 0.0)
            ]
            data = data.sort_values("open_time")
            data = data.drop_duplicates(subset=["open_time"], keep="last")

            minimum_rows = (
                FORMATION_BARS
                + max(OWN_HISTORY_BARS, CAPACITY_ANCHOR_MINIMUM_BARS)
                + 1
            )
            if len(data) < minimum_rows:
                continue

            log_return = np.log(data["close"]).diff()
            formation_move = log_return.rolling(
                FORMATION_BARS, min_periods=FORMATION_BARS
            ).sum()
            formation_quote_volume = data["quote_volume"].rolling(
                FORMATION_BARS, min_periods=FORMATION_BARS
            ).sum()
            capacity_anchor = data["quote_volume"].shift(1).rolling(
                OWN_HISTORY_BARS,
                min_periods=CAPACITY_ANCHOR_MINIMUM_BARS,
            ).median()
            capacity_ratio = formation_quote_volume / (
                capacity_anchor * float(FORMATION_BARS)
            )
            capacity_ratio = capacity_ratio.clip(
                lower=CAPACITY_RATIO_MINIMUM,
                upper=CAPACITY_RATIO_MAXIMUM,
            )
            signed_elasticity = formation_move / np.sqrt(capacity_ratio)
            signed_elasticity = signed_elasticity.replace(
                [np.inf, -np.inf], np.nan
            )

            current = float(signed_elasticity.iloc[-1])
            history = signed_elasticity.iloc[
                -(OWN_HISTORY_BARS + 1) : -1
            ].dropna()
            if (
                not np.isfinite(current)
                or len(history) < MINIMUM_HISTORY_OBSERVATIONS
            ):
                continue

            location, scale = _robust_location_scale(history)
            if not np.isfinite(location) or not np.isfinite(scale):
                continue
            z_score = (current - location) / scale
            own_history_z[symbol] = float(
                np.clip(z_score, -ROBUST_Z_CLIP, ROBUST_Z_CLIP)
            )

        if len(own_history_z) < 4:
            return flat_book

        own_z = pd.Series(own_history_z, dtype="float64").sort_index()
        cross_location, cross_scale = _robust_location_scale(own_z)
        if not np.isfinite(cross_location) or not np.isfinite(cross_scale):
            return flat_book

        cross_z = ((own_z - cross_location) / cross_scale).clip(
            lower=-ROBUST_Z_CLIP,
            upper=ROBUST_Z_CLIP,
        )
        expensive_move = 0.5 * own_z + 0.5 * cross_z
        reversion_alpha = -expensive_move
        reversion_alpha = reversion_alpha - reversion_alpha.mean()
        reversion_alpha = reversion_alpha.replace(
            [np.inf, -np.inf], np.nan
        ).dropna()

        long_strength = reversion_alpha.clip(lower=0.0)
        short_strength = (-reversion_alpha.clip(upper=0.0))
        if long_strength.sum() <= 0.0 or short_strength.sum() <= 0.0:
            return flat_book

        long_weights = (
            SIDE_GROSS_BUDGET * long_strength / long_strength.sum()
        ).clip(upper=SYMBOL_WEIGHT_CAP)
        short_weights = (
            SIDE_GROSS_BUDGET * short_strength / short_strength.sum()
        ).clip(upper=SYMBOL_WEIGHT_CAP)

        long_gross = float(long_weights.sum())
        short_gross = float(short_weights.sum())
        matched_gross = min(long_gross, short_gross)
        if matched_gross <= 0.0:
            return flat_book
        long_weights = long_weights * (matched_gross / long_gross)
        short_weights = short_weights * (matched_gross / short_gross)

        weights = flat_book
        for symbol in reversion_alpha.index:
            weight = float(long_weights.get(symbol, 0.0))
            weight -= float(short_weights.get(symbol, 0.0))
            if np.isfinite(weight):
                weights[symbol] = weight
        return weights


def build_strategy():
    return LiquidityImpactElasticityReversion()

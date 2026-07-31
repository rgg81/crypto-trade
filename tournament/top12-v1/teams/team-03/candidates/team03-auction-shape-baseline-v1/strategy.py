"""Transparent auction-path-shape-persistence baseline for Team 03."""

import math

import numpy as np
import pandas as pd


class AuctionPathShapePersistence:
    """Rank persistent acceptance and rejection geometry once per UTC day."""

    def target_weights(self, context, *, seed: int) -> dict[str, float] | None:
        # The frozen seed is intentionally not an alpha input; lexical tie-breaking is exact.
        _ = seed

        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        # A stateless calendar gate makes repeated calls deterministic and permits at most
        # one target request per UTC day.
        if decision_time != decision_time.normalize():
            return None

        formation_bars = 12
        minimum_active_states = 3
        raw_scores: dict[str, float] = {}
        raw_magnitudes: dict[str, float] = {}

        eligible_symbols = sorted({str(symbol) for symbol in context.eligible_symbols})
        for symbol in eligible_symbols:
            frame = context.bars.get(symbol)
            if frame is None or len(frame) < formation_bars:
                continue

            required = ("open_time", "open", "high", "low", "close")
            if any(column not in frame.columns for column in required):
                continue

            open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
            completed_mask = (
                open_times.notna()
                & ((open_times + pd.Timedelta(hours=8)) <= decision_time)
            )
            completed = frame.loc[completed_mask, list(required)].copy()
            if len(completed) < formation_bars:
                continue

            completed["_open_time_utc"] = open_times.loc[completed.index]
            completed = (
                completed.sort_values("_open_time_utc")
                .drop_duplicates("_open_time_utc", keep="last")
                .tail(formation_bars)
            )
            if len(completed) < formation_bars:
                continue

            open_price = pd.to_numeric(completed["open"], errors="coerce").to_numpy(float)
            high_price = pd.to_numeric(completed["high"], errors="coerce").to_numpy(float)
            low_price = pd.to_numeric(completed["low"], errors="coerce").to_numpy(float)
            close_price = pd.to_numeric(completed["close"], errors="coerce").to_numpy(float)

            finite = (
                np.isfinite(open_price)
                & np.isfinite(high_price)
                & np.isfinite(low_price)
                & np.isfinite(close_price)
            )
            valid_ohlc = (
                finite
                & (open_price > 0.0)
                & (high_price > low_price)
                & (high_price >= np.maximum(open_price, close_price))
                & (low_price <= np.minimum(open_price, close_price))
            )
            if not bool(np.all(valid_ohlc)):
                continue

            bar_range = high_price - low_price
            body = np.clip((close_price - open_price) / bar_range, -1.0, 1.0)
            close_location = np.clip(
                (2.0 * close_price - high_price - low_price) / bar_range,
                -1.0,
                1.0,
            )
            upper_wick = np.clip(
                (high_price - np.maximum(open_price, close_price)) / bar_range,
                0.0,
                1.0,
            )
            lower_wick = np.clip(
                (np.minimum(open_price, close_price) - low_price) / bar_range,
                0.0,
                1.0,
            )
            wick_asymmetry = lower_wick - upper_wick

            # Acceptance means body displacement is confirmed by a same-side close.
            acceptance_mask = (
                (body * close_location > 0.0)
                & (np.abs(body) >= 0.18)
                & (np.abs(close_location) >= 0.30)
            )
            acceptance_strength = (
                0.5 * np.abs(body) + 0.5 * np.abs(close_location)
            )
            acceptance_state = np.where(
                acceptance_mask,
                np.sign(body) * acceptance_strength,
                0.0,
            )

            # Positive wick asymmetry rejects lows; negative asymmetry rejects highs.
            # The close must finish away from the rejected excursion and the body must
            # remain modest so this state is distinct from acceptance.
            rejection_mask = (
                (np.abs(wick_asymmetry) >= 0.18)
                & (wick_asymmetry * close_location > 0.0)
                & (np.abs(body) <= 0.45)
            )
            rejection_strength = (
                0.6 * np.abs(wick_asymmetry) + 0.4 * np.abs(close_location)
            )
            rejection_state = np.where(
                rejection_mask,
                np.sign(wick_asymmetry) * rejection_strength,
                0.0,
            )

            acceptance_active = acceptance_state != 0.0
            if int(np.count_nonzero(acceptance_active)) >= minimum_active_states:
                active = acceptance_state[acceptance_active]
                acceptance_persistence = abs(float(np.mean(np.sign(active))))
                acceptance_signal = float(np.mean(active)) * acceptance_persistence
            else:
                acceptance_signal = 0.0

            rejection_active = rejection_state != 0.0
            if int(np.count_nonzero(rejection_active)) >= minimum_active_states:
                active = rejection_state[rejection_active]
                rejection_persistence = abs(float(np.mean(np.sign(active))))
                rejection_signal = float(np.mean(active)) * rejection_persistence
            else:
                rejection_signal = 0.0

            composite = 0.6 * acceptance_signal + 0.4 * rejection_signal
            magnitude = float(np.mean(np.abs(close_price / open_price - 1.0)))
            if math.isfinite(composite) and math.isfinite(magnitude):
                raw_scores[symbol] = composite
                raw_magnitudes[symbol] = magnitude

        if len(raw_scores) < 4:
            return {}

        symbols = sorted(raw_scores)
        score_vector = np.asarray([raw_scores[symbol] for symbol in symbols], dtype=float)
        magnitude_vector = np.asarray(
            [raw_magnitudes[symbol] for symbol in symbols],
            dtype=float,
        )

        # Remove level and linear exposure to raw intrabar move magnitude.
        residual = score_vector - float(np.mean(score_vector))
        centered_magnitude = magnitude_vector - float(np.mean(magnitude_vector))
        magnitude_variance = float(np.dot(centered_magnitude, centered_magnitude))
        if magnitude_variance > 1e-18:
            slope = float(np.dot(centered_magnitude, residual)) / magnitude_variance
            residual = residual - slope * centered_magnitude

        if not bool(np.all(np.isfinite(residual))):
            return {}
        if float(np.max(residual) - np.min(residual)) <= 1e-12:
            return {}

        residual_by_symbol = dict(zip(symbols, residual, strict=True))
        ranked = sorted(symbols, key=lambda symbol: (residual_by_symbol[symbol], symbol))
        positions_per_side = min(3, len(ranked) // 2)
        shorts = ranked[:positions_per_side]
        longs = ranked[-positions_per_side:]

        weights = {symbol: -0.08 for symbol in shorts}
        weights.update({symbol: 0.08 for symbol in longs})

        gross = sum(abs(weight) for weight in weights.values())
        net = sum(weights.values())
        if (
            not all(math.isfinite(weight) for weight in weights.values())
            or gross > 0.8 + 1e-12
            or abs(net) > 0.20 + 1e-12
            or any(abs(weight) > 0.08 + 1e-12 for weight in weights.values())
        ):
            return {}
        return weights


def build_strategy():
    """Return a fresh strategy instance."""

    return AuctionPathShapePersistence()

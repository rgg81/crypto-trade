import math

import numpy as np
import pandas as pd


class ReturnSignEntropyStrategy:
    formation_bars = 180
    entropy_window = 18
    entropy_lag = 6
    entropy_threshold = 0.08
    control_window = 12
    minimum_state_observations = 5
    maximum_symbols_per_side = 5
    symbol_weight = 0.08

    @staticmethod
    def _conditional_entropy(signs, end, window):
        start = end - window + 1
        if start < 0:
            return float("nan")

        segment = signs[start : end + 1]
        counts = np.zeros((2, 2), dtype=float)
        for previous, current in zip(segment[:-1], segment[1:]):
            row = 1 if previous > 0 else 0
            column = 1 if current > 0 else 0
            counts[row, column] += 1.0

        total = float(counts.sum())
        if total <= 0.0:
            return float("nan")

        entropy = 0.0
        for row in counts:
            row_total = float(row.sum())
            if row_total <= 0.0:
                continue
            row_entropy = 0.0
            for count in row:
                if count > 0.0:
                    probability = count / row_total
                    row_entropy -= probability * math.log(probability, 2)
            entropy += (row_total / total) * row_entropy
        return float(entropy)

    def _observation(self, returns, signs, index):
        entropy_now = self._conditional_entropy(
            signs, index, self.entropy_window
        )
        entropy_then = self._conditional_entropy(
            signs, index - self.entropy_lag, self.entropy_window
        )
        if not math.isfinite(entropy_now) or not math.isfinite(entropy_then):
            return None

        entropy_change = entropy_now - entropy_then
        if entropy_change >= self.entropy_threshold:
            transition = 1
        elif entropy_change <= -self.entropy_threshold:
            transition = -1
        else:
            transition = 0

        recent_returns = returns[
            index - self.control_window + 1 : index + 1
        ]
        if len(recent_returns) != self.control_window:
            return None

        cumulative_direction = float(np.sum(recent_returns))
        if cumulative_direction > 0.0:
            direction_state = 1
        elif cumulative_direction < 0.0:
            direction_state = -1
        else:
            direction_state = 0

        realized_volatility = float(np.std(recent_returns, ddof=1))
        if not math.isfinite(realized_volatility):
            return None

        sequence_state = (
            int(signs[index - 1]),
            int(signs[index]),
            transition,
        )
        return {
            "sequence_state": sequence_state,
            "transition": transition,
            "entropy_change": entropy_change,
            "entropy_now": entropy_now,
            "direction_state": direction_state,
            "volatility": realized_volatility,
        }

    @staticmethod
    def _smoothed_sign_mean(targets):
        return float(sum(targets)) / float(len(targets) + 2)

    @staticmethod
    def _binary_predictability(sign_mean):
        probability_up = min(1.0, max(0.0, (sign_mean + 1.0) / 2.0))
        entropy = 0.0
        for probability in (probability_up, 1.0 - probability_up):
            if probability > 0.0:
                entropy -= probability * math.log(probability, 2)
        return 1.0 - entropy

    def _score(self, completed):
        closes = pd.to_numeric(completed["close"], errors="coerce")
        closes = closes[np.isfinite(closes) & (closes > 0.0)]
        if len(closes) < self.formation_bars + 1:
            return None

        closes = closes.iloc[-(self.formation_bars + 1) :]
        returns = np.diff(np.log(closes.to_numpy(dtype=float)))
        if len(returns) != self.formation_bars or not np.all(
            np.isfinite(returns)
        ):
            return None

        signs = np.where(returns < 0.0, -1, 1)
        first_index = max(
            self.entropy_window - 1 + self.entropy_lag,
            self.control_window - 1,
            1,
        )
        records = []
        for index in range(first_index, len(signs) - 1):
            observation = self._observation(returns, signs, index)
            if observation is None:
                continue
            observation["target"] = int(signs[index + 1])
            records.append(observation)

        current = self._observation(returns, signs, len(signs) - 1)
        if not records or current is None or current["transition"] == 0:
            return None

        volatility_cut = float(
            np.median([record["volatility"] for record in records])
        )
        current_high_volatility = current["volatility"] > volatility_cut

        state_targets = [
            record["target"]
            for record in records
            if record["sequence_state"] == current["sequence_state"]
        ]
        if len(state_targets) < self.minimum_state_observations:
            return None

        control_targets = [
            record["target"]
            for record in records
            if record["direction_state"] == current["direction_state"]
            and (record["volatility"] > volatility_cut)
            == current_high_volatility
        ]
        if not control_targets:
            return None

        state_mean = self._smoothed_sign_mean(state_targets)
        control_mean = self._smoothed_sign_mean(control_targets)
        incremental_mean = state_mean - control_mean
        sample_shrinkage = len(state_targets) / (
            len(state_targets) + 6.0
        )
        transition_strength = min(
            1.0, abs(current["entropy_change"]) / 0.25
        )
        predictability = self._binary_predictability(state_mean)
        score = (
            incremental_mean
            * sample_shrinkage
            * transition_strength
            * (0.25 + 0.75 * predictability)
        )
        return float(score) if math.isfinite(score) else None

    @staticmethod
    def _completed_bars(frame, decision_time):
        if frame is None or len(frame) == 0 or "open_time" not in frame:
            return None

        open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
        completed_mask = (
            open_times + pd.Timedelta(hours=8) <= decision_time
        )
        completed = frame.loc[completed_mask].copy()
        if len(completed) == 0 or "close" not in completed:
            return None

        completed["_open_time"] = open_times.loc[completed.index]
        completed = completed.sort_values("_open_time")
        completed = completed.drop_duplicates("_open_time", keep="last")
        return completed

    def target_weights(self, context, *, seed):
        _ = int(seed)
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        if (
            decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        scores = {}
        for symbol in sorted(context.eligible_symbols):
            frame = context.bars.get(symbol)
            completed = self._completed_bars(frame, decision_time)
            if completed is None:
                continue
            score = self._score(completed)
            if score is not None and score != 0.0:
                scores[symbol] = score

        longs = sorted(
            (
                (symbol, score)
                for symbol, score in scores.items()
                if score > 0.0
            ),
            key=lambda item: (-item[1], item[0]),
        )
        shorts = sorted(
            (
                (symbol, score)
                for symbol, score in scores.items()
                if score < 0.0
            ),
            key=lambda item: (item[1], item[0]),
        )
        count = min(
            len(longs),
            len(shorts),
            self.maximum_symbols_per_side,
        )
        if count == 0:
            return {}

        weights = {}
        for symbol, _score in longs[:count]:
            weights[symbol] = self.symbol_weight
        for symbol, _score in shorts[:count]:
            weights[symbol] = -self.symbol_weight
        return weights


def build_strategy():
    return ReturnSignEntropyStrategy()

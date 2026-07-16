"""Dormant one-axis neighbor; activate only after the combined full gates pass."""

from strategy import build_parameterized_strategy


def build_strategy():
    return build_parameterized_strategy(slow_lookback_bars=90, selection_fraction=0.20)

from strategy_common import StrategyParameters, strategy


def build_strategy():
    return strategy(StrategyParameters(rebalance_bars=42, rank_buffer_fraction=0.4))

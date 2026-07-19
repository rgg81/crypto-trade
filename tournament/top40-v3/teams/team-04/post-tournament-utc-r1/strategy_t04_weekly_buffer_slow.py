from strategy_common import StrategyParameters, strategy


def build_strategy():
    return strategy(
        StrategyParameters(
            rebalance_bars=21,
            rank_buffer_fraction=0.4,
            slow_weight=0.7,
            fast_weight=0.1,
            funding_weight=0.2,
        )
    )

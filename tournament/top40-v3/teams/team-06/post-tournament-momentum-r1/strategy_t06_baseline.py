from strategy_common import StrategyParameters, strategy


def build_strategy():
    return strategy(
        StrategyParameters(rebalance_days=1, hold_mixed_signal=False, entry_strength=0.0)
    )

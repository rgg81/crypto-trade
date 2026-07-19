from strategy_common import StrategyParameters, strategy


def build_strategy():
    return strategy(
        StrategyParameters(rebalance_days=3, hold_mixed_signal=True, entry_strength=0.25)
    )

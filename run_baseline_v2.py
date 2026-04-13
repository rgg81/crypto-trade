"""Baseline v2 runner — diversification arm.

iter-v2/001 will populate this file with the first v2 portfolio (Models E/F/G,
one symbol each, wrapped in ``RiskV2Wrapper``). Until then, this module exists
only to reserve the filename and declare the exclusion constant so that tooling
and the skill can reference them.

Run from ``.worktrees/quant-research``:

    uv run python run_baseline_v2.py

Expected structure once iter-v2/001 ships:

    from crypto_trade.backtest import run_backtest
    from crypto_trade.backtest_models import BacktestConfig
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
    from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper, RiskV2Config
    from crypto_trade.strategies.ml.universe import select_symbols

    V2_EXCLUDED_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")

    def run_model(name, symbol, atr_tp, atr_sl):
        config = BacktestConfig(...)
        inner = LightGbmStrategy(..., features_dir="data/features_v2", ...)
        strategy = RiskV2Wrapper(inner, RiskV2Config())
        return run_backtest(config, strategy)
"""

from __future__ import annotations

import sys

V2_EXCLUDED_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")
"""Symbols belonging to v1's baseline. v2 runners MUST exclude these."""


def main() -> None:
    print("run_baseline_v2: scaffold stub.")
    print(f"V2_EXCLUDED_SYMBOLS = {V2_EXCLUDED_SYMBOLS}")
    print("iter-v2/001 will populate this runner with the first v2 portfolio.")
    sys.exit(0)


if __name__ == "__main__":
    main()

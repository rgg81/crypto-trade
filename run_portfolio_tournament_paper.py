"""crypto-cup-01 WINNER paper desk — team-02 breakout-channel, 6-month hands-off run.

PAPER ONLY: dry_run=True is hardcoded — this desk NEVER places exchange orders. Each 8h
candle it refreshes the shared kline/funding store, recomputes the tournament book through
the frozen team-02 submission (SHA-rechecked every tick via strategy_tournament), and
persists the held paper book to its OWN DB. PnL is scored offline by
scripts/tournament_paper_pnl.py through the tournament evaluator's exact cost model.

Fully isolated from the incumbent desks: own DB (data/portfolio_tournament_paper.db), own
log, strategy via the engine's `strategy_module` DI seam, rebalance staggered 25 min past
the candle boundary (v1 fires at 0, v2 at +15 min — no refresh contention).

  # single paper tick (smoke):
  PYTHONUNBUFFERED=1 uv run python run_portfolio_tournament_paper.py --once
  # the 6-month desk loop:
  PYTHONUNBUFFERED=1 nohup uv run python run_portfolio_tournament_paper.py \
      > logs/portfolio_tournament_paper.log 2>&1 &
"""

import argparse
import sys

sys.path.insert(0, "src")

from crypto_trade.config import load_settings
from crypto_trade.portfolio import strategy_tournament
from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine


def main() -> None:
    ap = argparse.ArgumentParser(description="crypto-cup-01 winner paper desk (dry-run ONLY)")
    ap.add_argument("--once", action="store_true", help="one refresh+compute tick, then exit")
    args = ap.parse_args()

    cfg = PortfolioConfig(
        equity_usd=10_000.0,
        leverage=1.0,
        data_dir=str(strategy_tournament.DATA_DIR),
        db_path="data/portfolio_tournament_paper.db",
        dry_run=True,  # hardcoded: this desk never trades
        testnet=False,
        min_active_universe=100,
        min_refresh_fraction=0.80,
        rebalance_lag_seconds=1500,  # +25 min stagger (v1: 0, v2: +15 min)
    )
    engine = PortfolioEngine(cfg, load_settings(), strategy_module=strategy_tournament)
    print(
        f"[tournament-paper] winner={strategy_tournament.WINNER_TEAM} "
        f"family={strategy_tournament.WINNER_FAMILY} db={cfg.db_path} "
        f"data={cfg.data_dir} PAPER-ONLY"
    )
    if args.once:
        engine.run_once()
    else:
        engine.run()


if __name__ == "__main__":
    main()

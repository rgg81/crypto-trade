"""Launch the BASELINE_PORTFOLIO_V2 executor on Binance TESTNET — DRY-RUN by default.

Mirrors run_portfolio_testnet.py for the v2 baseline (rank-21-40 dollar-neutral XS-mom 5-way
ensemble + frozen risk layer), FULLY ISOLATED from the live v1 engine (separate DB, separate
strategy module via the engine's `strategy_module` dependency-injection seam).

Sizing: equity $4k, leverage 1x. The v2 deployed book gross is the vol-target scale (~0.3-0.6 after
the TARGET_VOL=0.006 de-lever), so gross notional ~$1.2-2.4k, fitting the ~5k testnet faucet with
ample headroom. At 1x the account PnL ~= the strategy PnL (clean 1:1 reads).

SAFETY: dry-run is the DEFAULT. A bare run NEVER places orders — it does ONE refresh + compute +
log of the rebalance plan (paper book persisted to the v2 DB) and exits the single tick / loops in
paper mode. Real orders require the explicit `--live-testnet` flag AND testnet credentials.

  # dry smoke (no creds, no orders) — points the data dir at pf_data for an instant run:
  PORTFOLIO_V2_DATA_DIR=pf_data uv run python run_portfolio_v2_testnet.py --once

  # real testnet orders (orchestrator only, after verifying parity):
  set -a; source ~/.binance_testnet_env; set +a
  export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com
  PYTHONUNBUFFERED=1 uv run python run_portfolio_v2_testnet.py --live-testnet
"""

import argparse
import os
import sys

sys.path.insert(0, "src")

from crypto_trade.config import load_settings
from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine
from crypto_trade.portfolio_v2 import strategy_v2


def main() -> None:
    ap = argparse.ArgumentParser(
        description="BASELINE_PORTFOLIO_V2 testnet executor (dry-run by default)"
    )
    ap.add_argument(
        "--live-testnet",
        action="store_true",
        help="place REAL orders on the Binance testnet (requires creds). Omitted => DRY-RUN.",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="run a single tick (refresh + compute + log) and exit, instead of the poll loop.",
    )
    args = ap.parse_args()

    dry_run = not args.live_testnet  # default DRY-RUN; --live-testnet flips to real orders

    if not os.environ.get("BINANCE_AUTH_BASE_URL"):
        os.environ["BINANCE_AUTH_BASE_URL"] = "https://testnet.binancefuture.com"

    settings = load_settings()
    if not dry_run and not settings.binance_api_key:
        raise SystemExit(
            "ERROR: --live-testnet requires BINANCE_API_KEY/SECRET (source ~/.binance_testnet_env)"
        )

    cfg = PortfolioConfig(
        equity_usd=4_000.0,  # notional base sized to fit the ~5k testnet faucet at 1x
        leverage=1.0,  # 1x: account PnL ~= strategy PnL (no leverage amplification)
        delta=strategy_v2.DELTA,  # 0.010 hysteresis band (SNAP)
        dry_run=dry_run,
        testnet=True,
        db_path="data/portfolio_v2_testnet.db",  # isolated from the v1 portfolio DB
        poll_interval_seconds=60,
        paper_untradeable=True,  # testnet: names testnet can't fill (OPN/PUMP/...) -> paper, keeping
        # the live book faithful to the strategy target. (Set False for the production cutover.)
        min_refresh_fraction=0.80,  # refuse to rebalance if a 418 rate-limit ban left <80% of the
        # universe refreshed (partial fetch -> broken seasoning -> degenerate book); retries next tick.
        rebalance_lag_seconds=900,  # stagger the rebalance 15min PAST the 8h boundary so v2's kline
        # refresh doesn't collide with the other engines at the boundary (avoids the 418 contention).
    )
    engine = PortfolioEngine(cfg, settings, strategy_module=strategy_v2)
    mode = "DRY-RUN" if dry_run else "TESTNET (REAL ORDERS)"
    print(
        f"[portfolio-v2:{mode}] equity=${cfg.equity_usd} lev={cfg.leverage}x band={cfg.delta} "
        f"db={cfg.db_path} data_dir={strategy_v2.LIVE_DATA_DIR}"
    )
    if args.once:
        engine.run_once(refresh=True)
    else:
        engine.run()


if __name__ == "__main__":
    main()

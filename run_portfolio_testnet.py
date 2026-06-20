"""Launch the baseline-v2 portfolio executor on Binance TESTNET (full 8h poll loop).

Sizing: equity $10k, leverage 3x => gross notional ~$7,020 (0.70 vol-target), margin ~$2,340 at 3x.
Signed calls route to the testnet host (BINANCE_AUTH_BASE_URL); klines stay on production (parity).
Requires BINANCE_API_KEY / BINANCE_API_SECRET (testnet) in the environment.

  set -a; source ~/.binance_testnet_env; set +a
  export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com
  PYTHONUNBUFFERED=1 uv run python run_portfolio_testnet.py
"""

import os
import sys

sys.path.insert(0, "src")

from crypto_trade.config import load_settings
from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine

if not os.environ.get("BINANCE_AUTH_BASE_URL"):
    os.environ["BINANCE_AUTH_BASE_URL"] = "https://testnet.binancefuture.com"

settings = load_settings()
if not settings.binance_api_key:
    raise SystemExit("ERROR: BINANCE_API_KEY/SECRET not set (source ~/.binance_testnet_env)")

cfg = PortfolioConfig(
    equity_usd=10_000.0,
    leverage=3.0,
    dry_run=False,
    testnet=True,
    db_path="data/portfolio_testnet.db",
    poll_interval_seconds=60,
)
PortfolioEngine(cfg, settings).run()

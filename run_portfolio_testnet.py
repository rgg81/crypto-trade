"""Launch the baseline-v2 portfolio executor on Binance TESTNET (full 8h poll loop).

Sizing: equity $4k, leverage 1x => gross notional ~$3.3k (vol-target ~0.83), ~$3.3k margin at 1x,
fitting the ~5k testnet faucet balance with headroom. At 1x the account PnL ~= the strategy PnL
(no leverage amplification), so account DD ~= strategy DD — clean 1:1 reads.
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
    equity_usd=4_000.0,    # notional base sized to fit the ~5k testnet faucet at 1x (gross ~$3.3k)
    leverage=1.0,          # 1x: account PnL ~= strategy PnL (no leverage amplification of DD reads)
    dry_run=False,
    testnet=True,
    db_path="data/portfolio_testnet.db",
    poll_interval_seconds=60,
)
PortfolioEngine(cfg, settings).run()

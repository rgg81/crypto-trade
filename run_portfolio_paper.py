"""Launch the baseline-v1 portfolio strategy in PAPER mode (dry-run, no exchange).

Paper trading = the engine computes the strategy's deployed book every 8h candle and TREATS the
plan as filled (held_w persisted), placing NO orders. Because there is no venue, the book holds the
EXACT strategy target — all ~20 names including coins a real venue can't trade yet (e.g. ALLOUSDT
PENDING_TRADING on testnet) — with zero slippage and no min-notional/-1121 venue rejections. This is
the cleanest "track the strategy forward" run: the paper book == the backtest's deployed book by
construction (parity-verified), and the paper PnL == the strategy's net series extended live.

Klines + funding come from PRODUCTION (the backtest data); only order placement is skipped.
No API credentials are required (dry-run never authenticates / never touches an exchange).

Sizing: equity $10k (the strategy's canonical notional base — matches the backtest + quantstats
reports), leverage 1x (paper PnL ~= strategy PnL, no amplification). Gross ~$8k (vol-target ~0.83).

  PYTHONUNBUFFERED=1 uv run python run_portfolio_paper.py
"""

from crypto_trade.config import load_settings
from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine

settings = load_settings()

cfg = PortfolioConfig(
    equity_usd=10_000.0,   # canonical strategy notional base (matches backtest / quantstats)
    leverage=1.0,
    dry_run=True,          # PAPER: simulate fills, place no orders, hold the exact strategy book
    testnet=False,
    db_path="data/portfolio_paper.db",
    poll_interval_seconds=60,
)
PortfolioEngine(cfg, settings).run()

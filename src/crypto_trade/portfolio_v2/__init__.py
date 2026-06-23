"""portfolio_v2 — live weight engine for the BASELINE_PORTFOLIO_V2 candidate.

Drop-in replacement for `crypto_trade.portfolio.strategy` (the v1 interface the PortfolioEngine
calls). Exposes the SAME public surface so
`PortfolioEngine(strategy_module=portfolio_v2.strategy_v2)` runs the v2 rank-21-40 dollar-neutral
XS-mom 5-way ensemble + frozen risk layer with ZERO engine edits beyond the dependency-injection
seam.

Parity by construction: the live target weights == the backtest's deployed book
(`run_book_from_signal(... risk layer ...)`'s `held_w × scale` last row), verified by
`analysis/portfolio_v2/parity_live_check.py`.
"""

from __future__ import annotations

from . import strategy_v2

__all__ = ["strategy_v2"]

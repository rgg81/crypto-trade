"""Launch the TradFi PAPER-TRADING engine (confirmed iter-016 book, dual P&L).

Runs the deployed iter-016 BEAR-GATED TSMOM book continuously as a paper desk. Signals are parity-
by-construction with the backtest (same ``iter_016.deployed_weights`` on the same Yahoo total-return
history); fills are PAPER (no real orders). Two equity tracks are booked each settled daily bar:

  * PARITY — the Yahoo-TR backtest net compounded (the book of record).
  * LIVE   — the SAME weights scored on Binance single-stock TradFi-perp returns MINUS funding MINUS
             turnover, coverage-aware. ``basis_gap = equity_live − equity_parity`` (Phase-2b −85bp).

PAYP (PayPal) is EXCLUDED from the LIVE tradeable book (Phase-2b perp-venue decoupling) and NOT
re-normalized. Funding is modeled per leg as ``−w·f`` (Binance f>0 ⇒ longs pay).

    PYTHONUNBUFFERED=1 uv run python run_tradfi_paper.py > logs/tradfi_paper.log 2>&1 &

Ctrl-C is safe; state persists in ``data/tradfi_paper.db`` and equity snapshots append to
``data/tradfi_equity.csv``. On first launch the go-forward equity tracks start flat (launch =
current settled bar).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "analysis" / "portfolio" / "tradfi"))

from live_tradfi import TradfiPaperConfig, TradfiPaperEngine  # noqa: E402

if __name__ == "__main__":
    TradfiPaperEngine(TradfiPaperConfig()).run()

"""Launch the metals PAPER-TRADING engine (iter-008 sleeve-aware regime book).

Live signals are BIT-IDENTICAL to the backtest (same functions, same Dukascopy data); fills are
paper (zero slippage, filled at the candle open). No real orders, no Binance testnet.

    PYTHONUNBUFFERED=1 uv run python run_metals_paper.py > logs/metals_paper.log 2>&1 &

First launch seeds the deep Dukascopy history (gold/silver 2005+, pt/pd 2022+) into
`data_live_metals/` for the SMA-450 regime warmup — that initial pull takes a few minutes; every
subsequent tick is an incremental append. Ctrl-C is safe; state persists in `data/metals_paper.db`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "analysis" / "portfolio" / "metals"))

from live_metals import MetalsPaperConfig, MetalsPaperEngine  # noqa: E402

if __name__ == "__main__":
    MetalsPaperEngine(MetalsPaperConfig()).run()

"""Tests for the combined v1+v2 portfolio reporter (Task 12)."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from crypto_trade.live.portfolio_report import (
    CombinedReport,
    ReportInputs,
    build_combined_report,
)


def _toy_trade(
    symbol: str,
    direction: int,
    open_time_ms: int,
    close_time_ms: int,
    weighted_pnl: float,
    net_pnl_pct: float,
) -> dict:
    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": 100.0,
        "exit_price": 100.0 + (net_pnl_pct / 100.0) * 100.0,
        "weight_factor": 1.0,
        "open_time": open_time_ms,
        "close_time": close_time_ms,
        "exit_reason": "take_profit",
        "pnl_pct": net_pnl_pct + 0.1,
        "fee_pct": 0.1,
        "net_pnl_pct": net_pnl_pct,
        "weighted_pnl": weighted_pnl,
    }


def test_combined_report_aggregates_trades():
    DAY = 86_400_000
    v1 = pd.DataFrame(
        [
            _toy_trade("BTCUSDT", 1, 1 * DAY, 2 * DAY, 1.0, 2.0),
            _toy_trade("BTCUSDT", -1, 32 * DAY, 33 * DAY, -0.5, -1.0),
            _toy_trade("BTCUSDT", 1, 60 * DAY, 61 * DAY, 0.7, 1.4),
        ]
    )
    v2 = pd.DataFrame(
        [
            _toy_trade("DOGEUSDT", 1, 5 * DAY, 6 * DAY, 0.5, 1.0),
            _toy_trade("DOGEUSDT", 1, 40 * DAY, 41 * DAY, 0.3, 0.6),
        ]
    )
    rep = build_combined_report(ReportInputs(v1_trades=v1, v2_trades=v2))
    assert isinstance(rep, CombinedReport)
    assert rep.total_trades == 5
    assert rep.v1_trades == 3
    assert rep.v2_trades == 2
    assert math.isclose(rep.combined_weighted_pnl, 2.0, abs_tol=1e-9)
    assert "BTCUSDT" in rep.per_symbol
    assert rep.per_symbol["BTCUSDT"]["trades"] == 3
    assert "DOGEUSDT" in rep.per_symbol
    assert rep.per_track["v1"]["trades"] == 3
    assert rep.per_track["v2"]["trades"] == 2
    # Sharpe and drawdown finite (even if small)
    assert not math.isnan(rep.combined_sharpe_monthly)
    assert not math.isinf(rep.combined_sharpe_monthly)
    assert rep.combined_max_drawdown_pct >= 0.0


def test_combined_report_handles_empty_inputs():
    rep = build_combined_report(
        ReportInputs(v1_trades=pd.DataFrame(), v2_trades=pd.DataFrame())
    )
    assert rep.total_trades == 0
    assert rep.combined_weighted_pnl == 0.0
    assert rep.combined_sharpe_monthly == 0.0
    assert rep.combined_max_drawdown_pct == 0.0
    assert rep.per_symbol == {}


def test_combined_report_html_smoke(tmp_path):
    """HTML output is created and contains both tracks + headline metrics."""
    v1 = pd.DataFrame([_toy_trade("BTCUSDT", 1, 1, 2, 1.0, 2.0)])
    v2 = pd.DataFrame([_toy_trade("DOGEUSDT", 1, 1, 2, 0.5, 1.0)])
    out = tmp_path / "combined.html"
    build_combined_report(ReportInputs(v1_trades=v1, v2_trades=v2), html_out=out)
    assert out.exists()
    body = out.read_text()
    body_lower = body.lower()
    assert "v1" in body_lower
    assert "v2" in body_lower
    assert "combined sharpe" in body_lower
    assert "btcusdt" in body_lower
    assert "dogeusdt" in body_lower


@pytest.mark.skipif(
    not Path("reports/iteration_186/out_of_sample/trades.csv").exists()
    or not Path("reports-v2/iteration_v2-069/out_of_sample/trades.csv").exists(),
    reason="real backtest CSVs not present",
)
def test_combined_report_on_real_backtests(tmp_path):
    """Smoke test against the actual v1+v2 backtest outputs in this repo."""
    v1 = pd.read_csv("reports/iteration_186/out_of_sample/trades.csv")
    v2 = pd.read_csv("reports-v2/iteration_v2-069/out_of_sample/trades.csv")
    rep = build_combined_report(
        ReportInputs(v1_trades=v1, v2_trades=v2),
        html_out=tmp_path / "real_combined.html",
    )
    assert rep.total_trades == len(v1) + len(v2)
    assert rep.combined_sharpe_monthly != 0.0  # both tracks have OOS edge
    assert (tmp_path / "real_combined.html").exists()

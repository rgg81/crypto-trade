import csv

from crypto_trade.live.models import LiveTrade
from crypto_trade.live.trade_logger import TradeLogger, to_trade_result


def _closed_trade() -> LiveTrade:
    return LiveTrade(
        id="t1",
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=60000.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=57600.0,
        take_profit_price=64800.0,
        open_time=1000000,
        timeout_time=99999999,
        signal_time=999000,
        status="closed",
        exit_price=64800.0,
        exit_time=2000000,
        exit_reason="take_profit",
    )


def test_to_trade_result_long_tp():
    trade = _closed_trade()
    result = to_trade_result(trade, fee_pct=0.1)
    assert result is not None
    assert result.symbol == "BTCUSDT"
    assert result.exit_reason == "take_profit"
    # PnL = (64800 - 60000) / 60000 * 100 = 8.0%
    assert abs(result.pnl_pct - 8.0) < 1e-6
    assert abs(result.net_pnl_pct - 7.9) < 1e-6


def test_to_trade_result_short_sl():
    trade = LiveTrade(
        id="t2",
        model_name="C",
        symbol="LINKUSDT",
        direction=-1,
        entry_price=20.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=20.8,
        take_profit_price=18.4,
        open_time=1000000,
        timeout_time=99999999,
        signal_time=999000,
        status="closed",
        exit_price=20.8,
        exit_time=2000000,
        exit_reason="stop_loss",
    )
    result = to_trade_result(trade, fee_pct=0.1)
    assert result is not None
    # Short PnL = (20.0 - 20.8) / 20.0 * 100 = -4.0%
    assert abs(result.pnl_pct - (-4.0)) < 1e-6


def test_csv_output(tmp_path):
    log_path = tmp_path / "trades.csv"
    logger = TradeLogger(log_path, fee_pct=0.1, dry_run=True)

    trade = _closed_trade()
    logger.log_close(trade)

    with open(log_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert row["model_name"] == "A"
    assert row["symbol"] == "BTCUSDT"
    assert row["direction"] == "1"
    assert row["exit_reason"] == "take_profit"
    assert row["dry_run"] == "True"


def test_csv_header_written_once(tmp_path):
    log_path = tmp_path / "trades.csv"
    logger = TradeLogger(log_path, fee_pct=0.1, dry_run=True)

    trade = _closed_trade()
    logger.log_close(trade)
    logger.log_close(trade)

    with open(log_path) as f:
        lines = f.readlines()
    # 1 header + 2 data rows
    assert len(lines) == 3

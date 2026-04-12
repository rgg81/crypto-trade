from pathlib import Path

import numpy as np

from crypto_trade.live.data_pipeline import build_master, detect_new_candle
from crypto_trade.models import Kline
from crypto_trade.storage import write_klines


def _make_kline(open_time: int, close: str = "42000.00") -> Kline:
    return Kline(
        open_time=open_time,
        open="41000.00",
        high="43000.00",
        low="40000.00",
        close=close,
        volume="100.0",
        close_time=open_time + 28799999,
        quote_volume="4200000.0",
        trades=500,
        taker_buy_volume="50.0",
        taker_buy_quote_volume="2100000.0",
    )


def _write_symbol(tmp_path: Path, symbol: str, interval: str, klines: list[Kline]):
    from crypto_trade.storage import csv_path

    path = csv_path(tmp_path, symbol, interval)
    write_klines(path, klines)


class TestBuildMaster:
    def test_single_symbol(self, tmp_path):
        klines = [_make_kline(1000), _make_kline(2000)]
        _write_symbol(tmp_path, "BTCUSDT", "8h", klines)

        master = build_master(["BTCUSDT"], "8h", tmp_path)
        assert len(master) == 2
        assert "symbol" in master.columns
        assert master["symbol"].dtype.name == "category"
        assert list(master["symbol"].unique()) == ["BTCUSDT"]

    def test_multi_symbol_sorted(self, tmp_path):
        _write_symbol(tmp_path, "BTCUSDT", "8h", [_make_kline(1000), _make_kline(3000)])
        _write_symbol(tmp_path, "ETHUSDT", "8h", [_make_kline(1000), _make_kline(3000)])

        master = build_master(["BTCUSDT", "ETHUSDT"], "8h", tmp_path)
        assert len(master) == 4
        # Same open_time rows should be grouped together
        ots = master["open_time"].values
        assert ots[0] == 1000
        assert ots[1] == 1000
        assert ots[2] == 3000
        assert ots[3] == 3000

    def test_schema_matches_backtest(self, tmp_path):
        """Master DF must have exact columns and dtypes that strategies expect."""
        _write_symbol(tmp_path, "BTCUSDT", "8h", [_make_kline(1000)])
        master = build_master(["BTCUSDT"], "8h", tmp_path)

        expected_cols = {
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_volume",
            "taker_buy_quote_volume",
            "symbol",
        }
        assert set(master.columns) == expected_cols
        assert master["open_time"].dtype == np.int64
        assert master["open"].dtype == np.float64
        assert master["close"].dtype == np.float64
        assert master["symbol"].dtype.name == "category"

    def test_empty_when_no_data(self, tmp_path):
        master = build_master(["BTCUSDT"], "8h", tmp_path)
        assert master.empty


class TestDetectNewCandle:
    def test_returns_closed_candle(self):
        """Should return the second-to-last candle (last closed)."""
        import httpx

        kline_1 = _make_kline(1000)
        kline_2 = _make_kline(2000)  # currently forming

        def handler(request):
            data = [
                [
                    k.open_time,
                    k.open,
                    k.high,
                    k.low,
                    k.close,
                    k.volume,
                    k.close_time,
                    k.quote_volume,
                    k.trades,
                    k.taker_buy_volume,
                    k.taker_buy_quote_volume,
                    "0",
                ]
                for k in [kline_1, kline_2]
            ]
            return httpx.Response(200, json=data)

        from crypto_trade.client import BinanceClient

        client = BinanceClient(transport=httpx.MockTransport(handler))
        candle = detect_new_candle(client, "BTCUSDT", "8h", None)
        assert candle is not None
        assert candle.open_time == 1000

    def test_returns_none_when_already_processed(self):
        import httpx

        kline_1 = _make_kline(1000)
        kline_2 = _make_kline(2000)

        def handler(request):
            data = [
                [
                    k.open_time,
                    k.open,
                    k.high,
                    k.low,
                    k.close,
                    k.volume,
                    k.close_time,
                    k.quote_volume,
                    k.trades,
                    k.taker_buy_volume,
                    k.taker_buy_quote_volume,
                    "0",
                ]
                for k in [kline_1, kline_2]
            ]
            return httpx.Response(200, json=data)

        from crypto_trade.client import BinanceClient

        client = BinanceClient(transport=httpx.MockTransport(handler))
        candle = detect_new_candle(client, "BTCUSDT", "8h", 1000)
        assert candle is None

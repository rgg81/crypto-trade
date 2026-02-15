from dataclasses import dataclass


@dataclass(frozen=True)
class Kline:
    """A single candlestick (kline) from Binance Futures."""

    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_volume: str
    trades: int
    taker_buy_volume: str
    taker_buy_quote_volume: str

    CSV_HEADER: tuple[str, ...] = (
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
    )

    @classmethod
    def from_api(cls, raw: list) -> "Kline":
        """Parse a kline from the Binance API response array.

        Binance returns 12 elements per kline; we use the first 11
        (index 11 is an unused "ignore" field).
        """
        return cls(
            open_time=int(raw[0]),
            open=str(raw[1]),
            high=str(raw[2]),
            low=str(raw[3]),
            close=str(raw[4]),
            volume=str(raw[5]),
            close_time=int(raw[6]),
            quote_volume=str(raw[7]),
            trades=int(raw[8]),
            taker_buy_volume=str(raw[9]),
            taker_buy_quote_volume=str(raw[10]),
        )

    @classmethod
    def from_csv_row(cls, row: list[str]) -> "Kline":
        """Parse a kline from a CSV row (list of strings).

        Used to read headerless CSVs from data.binance.vision ZIPs.
        The row has the same 12 columns as the API response.
        """
        return cls(
            open_time=int(row[0]),
            open=row[1],
            high=row[2],
            low=row[3],
            close=row[4],
            volume=row[5],
            close_time=int(row[6]),
            quote_volume=row[7],
            trades=int(row[8]),
            taker_buy_volume=row[9],
            taker_buy_quote_volume=row[10],
        )

    def to_row(self) -> list[str]:
        """Serialize to a list of strings suitable for csv.writer."""
        return [
            str(self.open_time),
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            str(self.close_time),
            self.quote_volume,
            str(self.trades),
            self.taker_buy_volume,
            self.taker_buy_quote_volume,
        ]

import csv
from pathlib import Path

from crypto_trade.models import Kline


def csv_path(data_dir: Path, symbol: str, interval: str) -> Path:
    """Return the CSV file path for a given symbol and interval."""
    return data_dir / symbol / f"{interval}.csv"


def read_last_open_time(path: Path) -> int | None:
    """Read the open_time of the last row in a CSV file.

    Returns None if the file doesn't exist or is empty (header-only).
    """
    if not path.exists():
        return None
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        last_row = None
        for row in reader:
            last_row = row
    if last_row is None:
        return None
    return int(last_row[0])


def write_klines(path: Path, klines: list[Kline], *, append: bool = False) -> int:
    """Write klines to a CSV file.

    When append=True, opens in append mode and skips the header.
    Returns the number of rows written.
    """
    if not klines:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    write_header = not append
    with open(path, mode, newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(Kline.CSV_HEADER)
        for kline in klines:
            writer.writerow(kline.to_row())
    return len(klines)


def read_klines(path: Path) -> list[Kline]:
    """Read all klines from a CSV file."""
    if not path.exists():
        return []
    klines: list[Kline] = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            klines.append(
                Kline(
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
            )
    return klines

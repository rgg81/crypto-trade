"""Symbol universe selection for ML strategies."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from crypto_trade.config import OOS_CUTOFF_MS


def select_symbols(
    data_dir: str | Path = "data",
    features_dir: str | Path = "data/features",
    interval: str = "8h",
    min_is_candles: int = 1095,
    max_start_date: str = "2023-07-01",
    exclude: tuple[str, ...] = (),
) -> list[str]:
    """Return symbols eligible for walk-forward training.

    Selection criteria (from research brief):
    1. Ends with USDT (excludes BUSD, USDC duplicates)
    2. Does not contain "SETTLED" (contract rollovers)
    3. At least *min_is_candles* candles before OOS_CUTOFF_DATE
    4. First candle before *max_start_date*
    5. Symbol is not in *exclude* (v2 track uses this to forbid v1 baseline symbols)
    """
    import pyarrow.parquet as pq

    exclude_set = frozenset(exclude)
    features_path = Path(features_dir)
    max_start_ms = int(
        datetime.strptime(max_start_date, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000
    )

    selected: list[str] = []
    for pf in sorted(features_path.glob(f"*_{interval}_features.parquet")):
        symbol = pf.stem.replace(f"_{interval}_features", "")

        # 1. USDT only
        if not symbol.endswith("USDT"):
            continue
        # 2. No SETTLED
        if "SETTLED" in symbol:
            continue
        # 5. Exclusion list
        if symbol in exclude_set:
            continue

        # Read only open_time column for speed
        table = pq.read_table(pf, columns=["open_time"])
        open_times = table.column("open_time").to_pylist()
        if not open_times:
            continue

        # 3. Minimum IS candles
        is_count = sum(1 for t in open_times if t < OOS_CUTOFF_MS)
        if is_count < min_is_candles:
            continue

        # 4. Start date
        first_time = min(open_times)
        if first_time > max_start_ms:
            continue

        selected.append(symbol)

    return selected

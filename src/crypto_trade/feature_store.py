"""Feature store: CSV-to-Parquet conversion and memory-efficient lookup."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm


def convert_features_to_parquet(
    csv_path: Path,
    parquet_path: Path,
    row_group_size: int = 50_000,
) -> int:
    """Convert a feature CSV to Parquet with zstd compression.

    Returns the total number of rows written.
    """
    writer: pq.ParquetWriter | None = None
    total_rows = 0

    try:
        for chunk in pd.read_csv(csv_path, chunksize=row_group_size):
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(
                    parquet_path, table.schema, compression="zstd"
                )
            writer.write_table(table)
            total_rows += len(chunk)
    finally:
        if writer is not None:
            writer.close()

    return total_rows


def _convert_one(
    csv_path: Path,
    parquet_path: Path,
    row_group_size: int,
    delete_csv: bool,
) -> tuple[str, int]:
    """Convert a single CSV file. Returns (filename, n_rows)."""
    n_rows = convert_features_to_parquet(csv_path, parquet_path, row_group_size)
    if delete_csv and n_rows > 0:
        csv_path.unlink()
    return (csv_path.name, n_rows)


def convert_all_features(
    features_dir: str | Path,
    interval: str,
    workers: int = 4,
    delete_csv: bool = True,
    row_group_size: int = 50_000,
) -> list[tuple[str, int]]:
    """Convert all feature CSVs to Parquet, optionally deleting CSVs.

    Skips files where Parquet already exists and is newer than the CSV.
    Returns list of (filename, n_rows) for converted files.
    """
    features_dir = Path(features_dir)
    pattern = f"*_{interval}_features.csv"
    csv_files = sorted(features_dir.glob(pattern))

    # Filter: skip if parquet exists and is newer
    to_convert: list[tuple[Path, Path]] = []
    for csv_file in csv_files:
        parquet_file = csv_file.with_suffix(".parquet")
        if parquet_file.exists() and parquet_file.stat().st_mtime >= csv_file.stat().st_mtime:
            continue
        to_convert.append((csv_file, parquet_file))

    if not to_convert:
        return []

    results: list[tuple[str, int]] = []

    if workers <= 1:
        for csv_file, parquet_file in tqdm(to_convert, desc="Converting", unit="file"):
            result = _convert_one(csv_file, parquet_file, row_group_size, delete_csv)
            results.append(result)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _convert_one, csv_file, parquet_file, row_group_size, delete_csv
                ): csv_file.name
                for csv_file, parquet_file in to_convert
            }
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Converting", unit="file"
            ):
                results.append(future.result())

    return results


def lookup_features(
    lookups: list[tuple[str, int]],
    features_dir: str | Path,
    interval: str,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Look up specific (symbol, open_time) pairs from Parquet files.

    Args:
        lookups: List of (symbol, open_time_ms) tuples.
        features_dir: Directory containing Parquet feature files.
        interval: Kline interval (e.g. "15m").
        columns: Optional list of columns to read (for column pruning).

    Returns:
        DataFrame with matching rows, sorted by (symbol, open_time).
    """
    features_dir = Path(features_dir)

    # Group by symbol
    by_symbol: dict[str, list[int]] = {}
    for symbol, open_time in lookups:
        by_symbol.setdefault(symbol, []).append(open_time)

    parts: list[pd.DataFrame] = []

    for symbol, timestamps in by_symbol.items():
        parquet_path = features_dir / f"{symbol}_{interval}_features.parquet"
        if not parquet_path.exists():
            continue

        sorted_ts = sorted(set(timestamps))

        # Use pyarrow filters for row group pruning
        read_columns = columns
        if read_columns is not None and "open_time" not in read_columns:
            read_columns = ["open_time", *read_columns]

        table = pq.read_table(
            parquet_path,
            columns=read_columns,
            filters=[("open_time", "in", sorted_ts)],
        )
        df = table.to_pandas()

        if df.empty:
            continue

        df["symbol"] = symbol
        parts.append(df)

    if not parts:
        return pd.DataFrame()

    result = pd.concat(parts, ignore_index=True)
    result = result.sort_values(["symbol", "open_time"]).reset_index(drop=True)
    return result


def load_features_range(
    symbols: list[str],
    features_dir: str | Path,
    interval: str,
    start_ms: int,
    end_ms: int,
    columns: list[str] | None = None,
) -> dict[tuple[str, int], np.ndarray]:
    """Load features for a time range across symbols into a lookup dict.

    Returns {(symbol, open_time): feature_row_array} for fast per-candle lookups.
    Uses range filters on Parquet (much faster than exact timestamp matching for full months).
    """
    features_dir = Path(features_dir)
    result: dict[tuple[str, int], np.ndarray] = {}

    read_columns = columns
    if read_columns is not None:
        read_columns = ["open_time", *[c for c in read_columns if c != "open_time"]]

    for symbol in symbols:
        parquet_path = features_dir / f"{symbol}_{interval}_features.parquet"
        if not parquet_path.exists():
            continue

        table = pq.read_table(
            parquet_path,
            columns=read_columns,
            filters=[("open_time", ">=", start_ms), ("open_time", "<", end_ms)],
        )
        df = table.to_pandas()

        if df.empty:
            continue

        # Extract feature columns (everything except open_time)
        feat_cols = [c for c in df.columns if c != "open_time"]
        feat_values = df[feat_cols].values
        open_times = df["open_time"].values

        for row_idx in range(len(df)):
            key = (symbol, int(open_times[row_idx]))
            result[key] = feat_values[row_idx]

    return result


def write_parquet(
    df: pd.DataFrame,
    path: Path,
    row_group_size: int = 50_000,
) -> None:
    """Write a DataFrame directly to Parquet with zstd compression."""
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression="zstd", row_group_size=row_group_size)

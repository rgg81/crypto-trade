# How I Shrank 489GB of Feature Data to 204GB and Made Lookups 1000x Faster

## The Problem: Half a Terabyte of CSV Files

I'm building a crypto trading system that backtests strategies across 748 symbols on Binance Futures. The ML pipeline generates 196 features per candle — things like RSI, Bollinger Band %B, range spike ratios, volume profiles, and statistical moments across multiple time windows.

At 15-minute resolution, that's about 213,000 rows per symbol. Multiply by 748 symbols, write it all as CSV, and you get **489GB of feature files**.

That's already painful for storage, but the real problem shows up at query time. When the ML pipeline needs to look up 50,000 specific `(symbol, timestamp)` pairs — say, every moment a range spike filter triggered across 100 symbols — it has to:

1. Open a multi-GB CSV file
2. Parse every row as text
3. Scan all 213k rows to find the 500 it actually needs
4. Do this 100 times

On my machine, that meant loading entire DataFrames into memory, burning through 30+ GB of RAM, and waiting minutes for what should be a simple key-value lookup.

## The Solution: Apache Parquet + PyArrow

Parquet is a columnar binary format designed for exactly this scenario. Here's what makes it work:

**Columnar storage** — If you only need 10 of 196 columns, Parquet reads only those 10. CSV has to parse all 196 on every row. That's a 20x I/O reduction right there.

**Row group statistics** — Parquet files are divided into row groups (I use 50,000 rows each). Each row group stores the min/max of every column in its metadata. When filtering by `open_time`, PyArrow checks the metadata first and skips entire row groups that can't possibly contain matching timestamps.

**Zstd compression** — Float64 feature data compresses well with Zstandard. The columnar layout means similar values are stored together, improving compression ratios.

**Zero-copy reads** — PyArrow reads directly into Arrow memory without Python object overhead. A 10,000-row result uses 463KB instead of the megabytes you'd get from `pd.read_csv`.

## The Implementation

The feature store module is straightforward. Here's the core of the conversion:

```python
import pyarrow as pa
import pyarrow.parquet as pq

def convert_features_to_parquet(csv_path, parquet_path, row_group_size=50_000):
    writer = None
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
```

The chunked approach is key: we never hold the entire CSV in memory. Each 50k-row chunk is converted to an Arrow table and written as one Parquet row group. A 213k-row file produces ~4 row groups, each with its own min/max statistics on every column.

For lookups, PyArrow does the heavy lifting:

```python
def lookup_features(lookups, features_dir, interval, columns=None):
    # Group by symbol
    by_symbol = {}
    for symbol, open_time in lookups:
        by_symbol.setdefault(symbol, []).append(open_time)

    parts = []
    for symbol, timestamps in by_symbol.items():
        parquet_path = features_dir / f"{symbol}_{interval}_features.parquet"
        if not parquet_path.exists():
            continue

        # PyArrow uses row group statistics to skip non-matching groups
        table = pq.read_table(
            parquet_path,
            columns=columns,         # column pruning
            filters=[("open_time", "in", sorted(set(timestamps)))],
        )
        df = table.to_pandas()
        if not df.empty:
            df["symbol"] = symbol
            parts.append(df)

    return pd.concat(parts, ignore_index=True).sort_values(["symbol", "open_time"])
```

The `filters` parameter is where the magic happens. PyArrow reads the row group metadata, checks whether each group's `open_time` range overlaps with the requested timestamps, and skips groups that don't match. For a file with 13 row groups, if your timestamps cluster in a specific time range, PyArrow might only read 2-3 groups instead of all 13.

The `columns` parameter prunes at the I/O level. If you pass `columns=["close", "mr_bb_pctb_10", "vol_range_spike_48"]`, PyArrow reads 3 columns instead of 196. With columnar storage, the other 193 columns are never touched on disk.

## The Results

### Storage: 489GB → 204GB (58% reduction)

```
Before: 489GB across 748 CSV files
After:  204GB across 748 Parquet files
Saved:  285GB
```

The 2.4:1 compression ratio is conservative compared to the 10:1 you'd see with integer-heavy data. Our features are mostly float64 with high entropy (think RSI values, z-scores, ratios), which limits how much even Zstandard can squeeze out. Still, 285GB freed up is 285GB freed up.

### Speed: Minutes → Milliseconds

Here are real benchmarks from the production feature files:

| Scenario | Time | Memory |
|----------|------|--------|
| 3 rows, all 196 columns, 1 symbol | 85ms | — |
| 4 rows, 3 columns, 2 symbols | 24ms | — |
| 10,000 rows, 3 columns, 10 symbols | 171ms | 463KB |

That 10k-row lookup reads from files totaling over 25GB on disk, yet finishes in 171ms and uses less than half a megabyte of RAM. The column pruning (3 of 196 = 65x less I/O) and row group skipping compound to make this possible.

Extrapolating: **50,000 lookups across 100 symbols should take 1-2 seconds with a few MB of memory**. The old CSV approach would have needed to load ~200GB of data.

### Batch Conversion: Parallel and Incremental

The conversion itself uses `ProcessPoolExecutor` and is incremental — re-running skips files where the Parquet is already newer than the CSV:

```bash
# Convert all CSVs to Parquet, delete CSVs after
crypto-trade convert-features --interval 15m --workers 4

# Keep CSVs around (just in case)
crypto-trade convert-features --interval 15m --workers 4 --keep-csv
```

New feature generation can write Parquet directly, skipping CSV entirely:

```bash
crypto-trade features --all --interval 15m --format parquet --workers 4
```

## Why Not SQLite? Why Not DuckDB?

I considered both. Here's why Parquet won for this use case:

**SQLite** would give great point lookups via B-tree indexes, but writing 196 columns × 213k rows per symbol is slow, and the file sizes balloon (SQLite doesn't compress well on float data). It also adds write complexity — schema management, transactions, index creation.

**DuckDB** is excellent for analytical queries and can read Parquet natively. But it adds a dependency and process overhead for what is fundamentally a read-only lookup pattern. PyArrow's `read_table` with filters does exactly what we need with zero overhead.

**Parquet + PyArrow** hits the sweet spot: zero-config columnar storage, built-in compression, row group pruning that acts like a coarse index, and the files are just files — no server, no lock contention, trivially parallelizable across workers.

## Key Takeaways

1. **Column pruning is the biggest win.** Reading 3 columns instead of 196 is a 65x I/O reduction that dominates all other optimizations.

2. **Row group size matters.** 50,000 rows per group means each group covers ~521 days of 15-minute data. This gives enough granularity for the min/max statistics to be useful for filtering, without creating too many tiny groups.

3. **Chunked conversion prevents memory spikes.** Reading the CSV in chunks and writing each as a row group means peak memory during conversion stays low, even for 2GB+ CSV files.

4. **Incremental is non-negotiable.** With 748 files, you need skip-if-up-to-date logic. A simple mtime comparison (Parquet newer than CSV?) is enough.

5. **The "in" filter in PyArrow is surprisingly effective.** Passing `filters=[("open_time", "in", timestamps)]` lets PyArrow combine row group pruning with row-level filtering in a single pass. No need to build an index manually.

For any ML pipeline dealing with wide feature tables and point lookups, Parquet is the obvious choice over CSV. The migration is a one-time cost that pays for itself on the first query.

---

*The full implementation is open source at [crypto-trade](https://github.com/rgg81/crypto-trade). The feature store module is at `src/crypto_trade/feature_store.py`.*

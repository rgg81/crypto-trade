import argparse
import sys
from datetime import UTC, datetime

import httpx

from crypto_trade.bulk import BulkProgress, bulk_fetch_all
from crypto_trade.client import BinanceClient
from crypto_trade.config import load_settings
from crypto_trade.discovery import (
    discover_from_data_vision,
    discover_from_exchange_info,
    merge_symbols,
)
from crypto_trade.fetcher import fetch_all, fetch_symbol_interval


def _parse_date(date_str: str) -> int:
    """Parse YYYY-MM-DD to millisecond timestamp."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)


def _print_progress(progress: BulkProgress) -> None:
    """Print bulk download progress to stdout."""
    sym = progress.current_symbol
    interval = progress.current_interval
    month_pct = (
        f"{progress.current_month}/{progress.total_months}" if progress.total_months else "..."
    )
    print(
        f"\r[{progress.current_symbol_index}/{progress.total_symbols}] "
        f"{sym}/{interval} month {month_pct} | "
        f"{progress.total_klines:,} klines | "
        f"{progress.errors} errors",
        end="",
        flush=True,
    )


def main() -> None:
    settings = load_settings()

    parser = argparse.ArgumentParser(prog="crypto-trade", description="Binance Futures tools")
    subparsers = parser.add_subparsers(dest="command")

    # --- fetch subcommand ---
    fetch_parser = subparsers.add_parser("fetch", help="Fetch kline data from Binance Futures")
    fetch_parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated symbols (default: from config)",
    )
    fetch_parser.add_argument(
        "--intervals",
        type=str,
        default=None,
        help="Comma-separated intervals (default: from config)",
    )
    fetch_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date as YYYY-MM-DD (default: fetch all available)",
    )
    fetch_parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all active perpetual symbols from exchange info",
    )

    # --- symbols subcommand ---
    symbols_parser = subparsers.add_parser("symbols", help="List all discovered symbols")
    symbols_parser.add_argument(
        "--source",
        choices=["api", "vision", "both"],
        default="both",
        help="Source for symbol discovery (default: both)",
    )

    # --- bulk subcommand ---
    bulk_parser = subparsers.add_parser(
        "bulk", help="Bulk download kline data from data.binance.vision"
    )
    bulk_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_symbols",
        help="Discover and download all symbols from data.binance.vision",
    )
    bulk_parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated symbols to download",
    )
    bulk_parser.add_argument(
        "--intervals",
        type=str,
        default="1m,5m",
        help="Comma-separated intervals (default: 1m,5m)",
    )
    bulk_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Earliest month as YYYY-MM (default: all available)",
    )
    bulk_parser.add_argument(
        "--api-backfill",
        action="store_true",
        help="After bulk download, use API to fill current incomplete month",
    )

    args = parser.parse_args()

    if args.command is None:
        print(f"crypto-trade started (API key configured: {bool(settings.binance_api_key)})")
        parser.print_help()
        return

    if args.command == "fetch":
        _cmd_fetch(args, settings)
    elif args.command == "symbols":
        _cmd_symbols(args, settings)
    elif args.command == "bulk":
        _cmd_bulk(args, settings)


def _cmd_fetch(args, settings) -> None:
    if getattr(args, "all", False):
        with httpx.Client() as http:
            api_symbols = discover_from_exchange_info(settings.base_url, http)
        symbols = tuple(s.symbol for s in api_symbols)
        print(f"Discovered {len(symbols)} active perpetual symbols")
    else:
        symbols = (
            tuple(s.strip() for s in args.symbols.split(",")) if args.symbols else settings.symbols
        )

    intervals = (
        tuple(i.strip() for i in args.intervals.split(","))
        if args.intervals
        else settings.intervals
    )
    start_time = _parse_date(args.start) if args.start else None

    client = BinanceClient(
        base_url=settings.base_url,
        limit=settings.kline_limit,
        rate_limit_pause=settings.rate_limit_pause,
    )

    print(f"Fetching klines for {len(symbols)} symbols @ {intervals}")
    if start_time:
        print(f"Starting from {args.start}")

    results = fetch_all(client, settings.data_dir, symbols, intervals, start_time)
    for key, count in results.items():
        print(f"  {key}: {count} klines")
    total = sum(results.values())
    print(f"Done — {total} total klines fetched")


def _cmd_symbols(args, settings) -> None:
    source = args.source

    with httpx.Client() as http:
        if source == "api":
            symbols = discover_from_exchange_info(settings.base_url, http)
            for s in symbols:
                print(f"  {s.symbol:20s} {s.status}")
            print(f"\n{len(symbols)} symbols from API")

        elif source == "vision":
            vision_syms = discover_from_data_vision(http)
            for sym in sorted(vision_syms):
                print(f"  {sym}")
            print(f"\n{len(vision_syms)} symbols from data.binance.vision")

        else:  # both
            api_symbols = discover_from_exchange_info(settings.base_url, http)
            vision_syms = discover_from_data_vision(http)
            merged = merge_symbols(api_symbols, vision_syms)
            for s in merged:
                print(f"  {s.symbol:20s} {s.status}")
            print(f"\n{len(merged)} symbols total")


def _cmd_bulk(args, settings) -> None:
    if not args.all_symbols and not args.symbols:
        print("Error: specify --all or --symbols", file=sys.stderr)
        sys.exit(1)

    intervals = [i.strip() for i in args.intervals.split(",")]

    with httpx.Client(timeout=60.0) as http:
        if args.all_symbols:
            print("Discovering symbols from data.binance.vision...")
            symbols = discover_from_data_vision(http)
            print(f"Found {len(symbols)} symbols")
        else:
            symbols = [s.strip() for s in args.symbols.split(",")]

        print(f"Bulk downloading {len(symbols)} symbols @ {intervals}")

        results = bulk_fetch_all(
            http,
            settings.data_vision_base,
            settings.data_dir,
            symbols,
            intervals,
            rate_pause=settings.bulk_rate_pause,
            progress_cb=_print_progress,
        )

    print()  # newline after progress
    total = sum(results.values())
    print(f"Bulk download complete — {total:,} total klines")

    if args.api_backfill:
        print("\nBackfilling current month from API...")
        client = BinanceClient(
            base_url=settings.base_url,
            limit=settings.kline_limit,
            rate_limit_pause=settings.rate_limit_pause,
        )
        backfill_total = 0
        for symbol in symbols:
            for interval in intervals:
                count = fetch_symbol_interval(client, settings.data_dir, symbol, interval)
                if count:
                    print(f"  {symbol}/{interval}: {count} klines backfilled")
                    backfill_total += count
        print(f"API backfill complete — {backfill_total:,} klines")


if __name__ == "__main__":
    main()

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
    is_perpetual_symbol,
    is_stablecoin_pair,
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
        default="1m,8h",
        help="Comma-separated intervals (default: 1m,8h)",
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

    # --- features subcommand ---
    feat_parser = subparsers.add_parser("features", help="Generate feature CSVs for ML pipeline")
    feat_parser.add_argument("--list", action="store_true", help="List available feature groups")
    feat_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_symbols",
        help="Run against all symbols with data for the given interval",
    )
    feat_parser.add_argument(
        "--symbols", type=str, default=None, help="Comma-separated symbols (default: from config)"
    )
    feat_parser.add_argument(
        "--interval", type=str, default="8h", help="Kline interval (default: 8h)"
    )
    feat_parser.add_argument(
        "--groups", type=str, default="all", help="Comma-separated groups or 'all' (default: all)"
    )
    feat_parser.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    feat_parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    feat_parser.add_argument(
        "--output", type=str, default=None, help="Output directory (default: data/features/)"
    )
    feat_parser.add_argument("--workers", type=int, default=1, help="Parallel workers (default: 1)")
    feat_parser.add_argument(
        "--format",
        choices=["csv", "parquet"],
        default="csv",
        help="Output format (default: csv)",
    )

    # --- convert-features subcommand ---
    conv_parser = subparsers.add_parser(
        "convert-features", help="Convert feature CSVs to Parquet (and optionally delete CSVs)"
    )
    conv_parser.add_argument(
        "--interval", type=str, default="8h", help="Kline interval (default: 8h)"
    )
    conv_parser.add_argument("--workers", type=int, default=4, help="Parallel workers (default: 4)")
    conv_parser.add_argument(
        "--keep-csv", action="store_true", help="Keep CSV files after conversion"
    )
    conv_parser.add_argument(
        "--output", type=str, default=None, help="Features directory (default: data/features/)"
    )

    # --- backtest subcommand ---
    bt_parser = subparsers.add_parser("backtest", help="Run strategy backtests")
    bt_parser.add_argument(
        "--strategy", type=str, default=None, help="Strategy name (e.g. momentum, rsi_bb)"
    )
    bt_parser.add_argument("--list", action="store_true", help="List available strategies")
    bt_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_symbols",
        help="Run against all symbols with data for the given interval",
    )
    bt_parser.add_argument(
        "--symbols", type=str, default=None, help="Comma-separated symbols (default: from config)"
    )
    bt_parser.add_argument(
        "--interval", type=str, default="8h", help="Kline interval (default: 8h)"
    )
    bt_parser.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    bt_parser.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    bt_parser.add_argument(
        "--amount", type=float, default=1000.0, help="Max trade amount USD (default: 1000)"
    )
    bt_parser.add_argument(
        "--stop-loss", type=float, default=2.0, help="Stop loss %% (default: 2.0)"
    )
    bt_parser.add_argument(
        "--take-profit", type=float, default=3.0, help="Take profit %% (default: 3.0)"
    )
    bt_parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout in minutes (default: 120)"
    )
    bt_parser.add_argument("--fee", type=float, default=0.1, help="Fee %% (default: 0.1)")
    bt_parser.add_argument(
        "--params", type=str, default=None, help="Strategy params as key=val,key=val"
    )
    spike_group = bt_parser.add_mutually_exclusive_group()
    spike_group.add_argument(
        "--range-spike-filter", action="store_true", help="Wrap strategy with range spike filter"
    )
    spike_group.add_argument(
        "--adaptive-range-spike-filter",
        action="store_true",
        help="Wrap strategy with adaptive (auto-recalibrating) range spike filter",
    )
    bt_parser.add_argument(
        "--volume-filter", action="store_true", help="Wrap strategy with volume filter"
    )
    bt_parser.add_argument(
        "--profile-memory", action="store_true", help="Print tracemalloc memory usage at key stages"
    )
    bt_parser.add_argument(
        "--report",
        nargs="?",
        const="auto",
        default=None,
        help="Generate quantstats HTML tearsheet (optional: output path)",
    )

    # -- live subcommand --
    live_parser = subparsers.add_parser(
        "live", help="Run live trading (baseline v186 — 4-model portfolio: A/C/D/E)"
    )
    live_parser.add_argument(
        "--amount", type=float, default=1000.0, help="Max trade amount USD (default: 1000)"
    )
    live_parser.add_argument(
        "--leverage", type=int, default=1, help="Futures leverage (default: 1)"
    )
    live_parser.add_argument(
        "--poll-interval",
        type=float,
        default=30.0,
        help="Seconds between polls (default: 30)",
    )
    live_parser.add_argument(
        "--feature-groups",
        type=str,
        default="all",
        help="Feature groups to generate (default: all)",
    )
    live_parser.add_argument(
        "--live",
        action="store_true",
        dest="live_mode",
        help="Enable real trading (default: dry-run)",
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
    elif args.command == "backtest":
        _cmd_backtest(args, settings)
    elif args.command == "features":
        _cmd_features(args, settings)
    elif args.command == "convert-features":
        _cmd_convert_features(args, settings)
    elif args.command == "live":
        _cmd_live(args, settings)


def _cmd_fetch(args, settings) -> None:
    if getattr(args, "all", False):
        with httpx.Client() as http:
            api_symbols = discover_from_exchange_info(settings.base_url, http)
        symbols = tuple(s.symbol for s in api_symbols if not is_stablecoin_pair(s.symbol))
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
            symbols = [
                s
                for s in discover_from_data_vision(http)
                if is_perpetual_symbol(s) and not is_stablecoin_pair(s)
            ]
            print(f"Found {len(symbols)} perpetual symbols")
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


def _cmd_backtest(args, settings) -> None:
    from pathlib import Path

    from crypto_trade.backtest import run_backtest
    from crypto_trade.backtest_models import BacktestConfig
    from crypto_trade.backtest_report import aggregate_monthly_trades, summarize
    from crypto_trade.strategies import get_strategy, list_strategies
    from crypto_trade.strategies.filters.adaptive_range_spike_filter import (
        AdaptiveRangeSpikeFilter,
    )
    from crypto_trade.strategies.filters.range_spike_filter import RangeSpikeFilter
    from crypto_trade.strategies.filters.volume_filter import VolumeFilter

    if args.list:
        print("Available strategies:")
        for name in list_strategies():
            print(f"  {name}")
        return

    if not args.strategy:
        print("Error: --strategy required (or use --list)", file=sys.stderr)
        sys.exit(1)

    # Parse strategy params
    params: dict[str, str] | None = None
    if args.params:
        params = {}
        for pair in args.params.split(","):
            k, _, v = pair.partition("=")
            params[k.strip()] = v.strip()

    strategy = get_strategy(args.strategy, params)

    # Wrap with filters
    adaptive_filter = None
    if args.range_spike_filter:
        strategy = RangeSpikeFilter(inner=strategy)
    elif args.adaptive_range_spike_filter:
        adaptive_filter = AdaptiveRangeSpikeFilter(inner=strategy)
        strategy = adaptive_filter
    if args.volume_filter:
        strategy = VolumeFilter(inner=strategy)

    if getattr(args, "all_symbols", False):
        csv_pattern = f"*/{args.interval}.csv"
        found = sorted(Path(settings.data_dir).glob(csv_pattern))
        symbols = tuple(
            p.parent.name
            for p in found
            if is_perpetual_symbol(p.parent.name) and not is_stablecoin_pair(p.parent.name)
        )
        if not symbols:
            print(f"Error: no data files matching {csv_pattern}", file=sys.stderr)
            sys.exit(1)
    else:
        symbols = (
            tuple(s.strip() for s in args.symbols.split(",")) if args.symbols else settings.symbols
        )
    start_time = _parse_date(args.start) if args.start else None
    end_time = _parse_date(args.end) if args.end else None

    config = BacktestConfig(
        symbols=symbols,
        interval=args.interval,
        max_amount_usd=float(args.amount),
        stop_loss_pct=float(args.stop_loss),
        take_profit_pct=float(args.take_profit),
        timeout_minutes=args.timeout,
        fee_pct=float(args.fee),
        data_dir=Path(settings.data_dir),
        start_time=start_time,
        end_time=end_time,
    )

    filters_desc = []
    if args.range_spike_filter:
        filters_desc.append("range_spike")
    elif args.adaptive_range_spike_filter:
        filters_desc.append("adaptive_range_spike")
    if args.volume_filter:
        filters_desc.append("volume")
    filters_str = f" + filters=[{', '.join(filters_desc)}]" if filters_desc else ""

    print(f"Backtesting {args.strategy}{filters_str}")
    print(f"  Symbols: {', '.join(symbols)}")
    print(f"  Interval: {args.interval}")
    print(f"  SL={args.stop_loss}% TP={args.take_profit}% Timeout={args.timeout}m Fee={args.fee}%")
    if start_time:
        print(f"  Start: {args.start}")
    if end_time:
        print(f"  End: {args.end}")

    results = run_backtest(config, strategy, profile_memory=args.profile_memory)
    summary = summarize(results)

    if summary is None:
        print("\nNo trades generated.")
        return

    print(f"\n{'=' * 50}")
    print(f"  Total signals:   {results.total_signals}")
    print(f"  Total trades:    {summary.total_trades}")
    print(f"  Wins:            {summary.wins}")
    print(f"  Losses:          {summary.losses}")
    print(f"  Win rate:        {summary.win_rate_pct:.1f}%")
    print(f"  Avg PnL:         {summary.avg_pnl_pct:.4f}%")
    print(f"  Total net PnL:   {summary.total_net_pnl_pct:.4f}%")
    print(f"  Max drawdown:    {summary.max_drawdown_pct:.4f}%")
    print(f"  Profit factor:   {summary.profit_factor:.4f}")
    print(f"  Best trade:      {summary.best_trade_pct:.4f}%")
    print(f"  Worst trade:     {summary.worst_trade_pct:.4f}%")
    print(f"  Trades/month:    {summary.trades_per_month:.1f}")
    print(f"  Exit reasons:    {summary.exit_reasons}")
    print(f"{'=' * 50}")

    # Monthly breakdown
    monthly = aggregate_monthly_trades(results)
    if monthly:
        print("\n  Trades per month:")
        for month, count in monthly.items():
            print(f"    {month}: {count}")

    # Calibration log
    if adaptive_filter and adaptive_filter._calibration_log:
        print("\n  Calibration log:")
        print(f"    {'Date':>19s}  {'Threshold':>10s}  {'Signals/mo':>10s}  {'Error':>8s}")
        for cal in adaptive_filter._calibration_log:
            dt = datetime.fromtimestamp(cal.calibrated_at / 1000, tz=UTC)
            print(
                f"    {dt:%Y-%m-%d %H:%M}  {cal.threshold:>10.4f}  {cal.signals_per_month:>10.0f}  "
            )

    # HTML tearsheet
    if args.report is not None:
        from crypto_trade.backtest_report import generate_html_report, to_daily_returns_series

        returns = to_daily_returns_series(results, args.start, args.end)
        if returns.empty:
            print("\nNo daily returns to report.")
        else:
            if args.report == "auto":
                date_tag = datetime.now(tz=UTC).strftime("%Y%m%d")
                sym_tag = symbols[0] if len(symbols) == 1 else f"{len(symbols)}syms"
                report_path = f"{args.strategy}_{sym_tag}_{args.interval}_{date_tag}.html"
            else:
                report_path = args.report

            title_parts = [args.strategy]
            if filters_desc:
                title_parts.append(f"[{', '.join(filters_desc)}]")
            title_parts.append(f"{', '.join(symbols)} {args.interval}")
            title = " | ".join(title_parts)

            out = generate_html_report(returns, report_path, title=title)
            print(f"\nReport saved to {out}")


def _cmd_features(args, settings) -> None:
    from pathlib import Path

    from crypto_trade.features import list_groups, run_features

    if args.list:
        print("Available feature groups:")
        for name in list_groups():
            print(f"  {name}")
        return

    if getattr(args, "all_symbols", False):
        csv_pattern = f"*/{args.interval}.csv"
        found = sorted(Path(settings.data_dir).glob(csv_pattern))
        symbols = [
            p.parent.name
            for p in found
            if is_perpetual_symbol(p.parent.name) and not is_stablecoin_pair(p.parent.name)
        ]
        if not symbols:
            print(f"Error: no data files matching {csv_pattern}", file=sys.stderr)
            sys.exit(1)
    else:
        symbols = (
            [s.strip() for s in args.symbols.split(",")] if args.symbols else list(settings.symbols)
        )
    groups_arg = args.groups.strip()
    if groups_arg == "all":
        groups = list_groups()
    else:
        groups = [g.strip() for g in groups_arg.split(",")]
        available = set(list_groups())
        unknown = [g for g in groups if g not in available]
        if unknown:
            print(f"Error: unknown groups: {unknown}. Available: {list_groups()}", file=sys.stderr)
            sys.exit(1)

    start_ms = _parse_date(args.start) if args.start else None
    end_ms = _parse_date(args.end) if args.end else None
    output_dir = args.output or str(Path(settings.data_dir) / "features")

    print(f"Generating features: {', '.join(groups)}")
    print(f"  Symbols: {', '.join(symbols)} | Interval: {args.interval} | Workers: {args.workers}")

    output_format = getattr(args, "format", "csv")
    results = run_features(
        symbols=symbols,
        interval=args.interval,
        data_dir=settings.data_dir,
        groups=groups,
        start_ms=start_ms,
        end_ms=end_ms,
        output_dir=output_dir,
        workers=args.workers,
        output_format=output_format,
    )

    ext = ".parquet" if output_format == "parquet" else ".csv"
    for symbol, n_rows, n_features in results:
        if n_rows > 0:
            print(
                f"  {symbol}: {n_rows:,} rows, {n_features} features "
                f"-> {output_dir}/{symbol}_{args.interval}_features{ext}"
            )
        else:
            print(f"  {symbol}: no data")

    total = sum(1 for _, n, _ in results if n > 0)
    print(f"Done — {total} symbols processed.")


def _cmd_convert_features(args, settings) -> None:
    from pathlib import Path

    from crypto_trade.feature_store import convert_all_features

    features_dir = args.output or str(Path(settings.data_dir) / "features")
    delete_csv = not args.keep_csv

    print(f"Converting feature CSVs to Parquet in {features_dir}")
    print(f"  Interval: {args.interval} | Workers: {args.workers} | Delete CSV: {delete_csv}")

    results = convert_all_features(
        features_dir=features_dir,
        interval=args.interval,
        workers=args.workers,
        delete_csv=delete_csv,
    )

    if not results:
        print("No files to convert (all up-to-date or none found).")
        return

    total_rows = 0
    for filename, n_rows in results:
        print(f"  {filename}: {n_rows:,} rows")
        total_rows += n_rows

    print(f"Done — {len(results)} files converted, {total_rows:,} total rows.")


def _cmd_live(args, settings) -> None:
    from pathlib import Path

    from crypto_trade.live.engine import LiveEngine
    from crypto_trade.live.models import BASELINE_MODELS, LiveConfig

    groups = tuple(g.strip() for g in args.feature_groups.split(","))

    config = LiveConfig(
        models=BASELINE_MODELS,
        interval="8h",
        max_amount_usd=float(args.amount),
        leverage=args.leverage,
        data_dir=Path(settings.data_dir),
        features_dir=Path(settings.data_dir) / "features",
        feature_groups=groups,
        db_path=Path(settings.data_dir) / ("dry_run.db" if not args.live_mode else "live.db"),
        poll_interval_seconds=args.poll_interval,
        dry_run=not args.live_mode,
    )

    engine = LiveEngine(
        config=config,
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret,
        base_url=settings.base_url,
    )
    engine.run()


if __name__ == "__main__":
    main()

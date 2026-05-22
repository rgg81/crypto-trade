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


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argparse parser.

    Exposed so tests can probe CLI flags without invoking ``main()``.
    """
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
    feat_parser.add_argument(
        "--track",
        choices=["v1", "v2", "v3"],
        default="v1",
        help=(
            "Feature catalog: v1=crypto_trade.features (193 baseline features); "
            "v2=crypto_trade.features_v2 (34 v2 features); "
            "v3=crypto_trade.features_v3 (v3 rigor-arm features, parquet only). "
            "When --track v2/v3 and --output is omitted, default output dir is "
            "data/features_v2 or data/features_v3 respectively."
        ),
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
    live_parser.add_argument(
        "--testnet",
        action="store_true",
        help=(
            "Route signed calls (orders, positions, leverage) to the Binance "
            "Futures testnet (https://testnet.binancefuture.com) while keeping "
            "kline fetches on production. Forces live trading; uses "
            "data/testnet.db and data/testnet_trades.csv. Override the testnet "
            "host with BINANCE_AUTH_BASE_URL."
        ),
    )
    live_parser.add_argument(
        "--track",
        choices=["v1", "v2", "v3", "both", "all"],
        default="v1",
        help=(
            "Model preset: v1=BASELINE_MODELS, v2=V2_BASELINE_MODELS, "
            "v3=V3_BASELINE_MODELS (iter-v3/121), both=COMBINED_MODELS (v1+v2), "
            "all=ALL_MODELS (v1+v2+v3) (default: v1)"
        ),
    )
    # -- seed-live-db subcommand --
    seed_parser = subparsers.add_parser(
        "seed-live-db",
        help="Import backtest trade CSVs into the live SQLite DB so R1/R2/VT/cooldown "
        "state is preloaded. `live` resumes from the seeded boundary automatically.",
    )
    seed_parser.add_argument(
        "--db",
        type=str,
        default="data/dry_run.db",
        help=(
            "Target DB (default: data/dry_run.db, matches `live --dry-run` "
            "behavior). For testnet pass data/testnet.db; for live, data/live.db. "
            "The path must match the DB the engine will open at startup "
            "(testnet > dry_run > live, see engine.py)."
        ),
    )
    seed_parser.add_argument(
        "--v1-trades",
        action="append",
        type=str,
        default=None,
        help="v1 backtest trades.csv (can repeat for IS+OOS — pass each path).",
    )
    seed_parser.add_argument(
        "--v2-trades",
        action="append",
        type=str,
        default=None,
        help="v2 backtest trades.csv (can repeat). Zero-weight rows skipped.",
    )
    seed_parser.add_argument(
        "--v3-trades",
        action="append",
        type=str,
        default=None,
        help="v3 backtest trades.csv (can repeat for IS+OOS — iter-v3/121 baseline).",
    )
    seed_parser.add_argument(
        "--track",
        choices=["v1", "v2", "v3", "both", "all"],
        default="both",
        help="Which model preset to use for symbol→model mapping + cooldown_candles "
        "resolution (default: both — covers v1+v2; pass v3 for /121; pass all for "
        "v1+v2+v3 combined).",
    )
    seed_parser.add_argument(
        "--reseed",
        action="store_true",
        help=(
            "Overwrite seeded_through_* boundary keys with this CSV's "
            "data extent, even if existing keys are higher. Default is "
            "monotonic advance (MAX(existing, new))."
        ),
    )

    # -- fetch-funding subcommand (iter-v3/019) --
    ff_parser = subparsers.add_parser(
        "fetch-funding",
        help=(
            "Fetch Binance Futures funding-rate history from /fapi/v1/fundingRate "
            "and cache to data/funding_rates/<SYMBOL>.csv. Incremental — re-running "
            "appends only new entries since last cached timestamp."
        ),
    )
    ff_parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Comma-separated symbols (e.g. BCHUSDT,LDOUSDT,TRXUSDT)",
    )
    ff_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help=(
            "Earliest funding date as YYYY-MM-DD (default: 2019-01-01). "
            "Ignored if cache already exists — incremental fetch resumes from "
            "last cached timestamp."
        ),
    )
    ff_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for funding-rate CSVs (default: data/funding_rates/)",
    )

    # -- fetch-spot subcommand (iter-v3/086) --
    fs_parser = subparsers.add_parser(
        "fetch-spot",
        help=(
            "Fetch Binance SPOT 8h klines from data.binance.vision monthly archives "
            "and cache to data/spot/<SYMBOL>/8h.csv. Incremental — re-running appends "
            "only new candles. Timestamp normalisation: 16-digit microsecond epochs "
            "(Binance spot archives 2025-01+) are converted to milliseconds."
        ),
    )
    fs_parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Comma-separated symbols (e.g. BCHUSDT,LDOUSDT,TRXUSDT)",
    )
    fs_parser.add_argument(
        "--intervals",
        type=str,
        default="8h",
        help="Comma-separated intervals (default: 8h)",
    )
    fs_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for spot-kline CSVs (default: data/spot/)",
    )

    # -- fetch-oi subcommand (iter-v3/093) --
    foi_parser = subparsers.add_parser(
        "fetch-oi",
        help=(
            "Fetch Binance Futures open-interest + long/short metrics from "
            "data.binance.vision daily metrics archives and cache to "
            "data/open_interest/<SYMBOL>/8h.csv. Incremental — re-running "
            "appends only new rows. Schema: sum_open_interest, "
            "sum_open_interest_value, count_toptrader_long_short_ratio, "
            "sum_toptrader_long_short_ratio at 5-min granularity, "
            "resampled to 8h."
        ),
    )
    foi_parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Comma-separated symbols (e.g. BCHUSDT,LDOUSDT,TRXUSDT,BTCUSDT)",
    )
    foi_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for OI CSVs (default: data/open_interest/)",
    )

    # -- portfolio-report subcommand --
    pr_parser = subparsers.add_parser(
        "portfolio-report",
        help="Build combined v1+v2 portfolio tearsheet from two trade CSVs",
    )
    pr_parser.add_argument(
        "--v1-trades",
        type=str,
        required=True,
        help="Path to v1 trades.csv (e.g. reports/iteration_186/out_of_sample/trades.csv)",
    )
    pr_parser.add_argument(
        "--v2-trades",
        type=str,
        required=True,
        help="Path to v2 trades.csv (e.g. reports-v2/iteration_v2-069/out_of_sample/trades.csv)",
    )
    pr_parser.add_argument(
        "--out",
        type=str,
        default="combined_portfolio_report.html",
        help="Output HTML path (default: combined_portfolio_report.html)",
    )

    return parser


def main() -> None:
    settings = load_settings()
    parser = build_parser()
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
    elif args.command == "portfolio-report":
        _cmd_portfolio_report(args, settings)
    elif args.command == "seed-live-db":
        _cmd_seed_live_db(args, settings)
    elif args.command == "fetch-funding":
        _cmd_fetch_funding(args, settings)
    elif args.command == "fetch-spot":
        _cmd_fetch_spot(args, settings)
    elif args.command == "fetch-oi":
        _cmd_fetch_oi(args, settings)


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

    track = getattr(args, "track", "v1")
    if track == "v3":
        from crypto_trade.features_v3 import (
            list_groups as _list_groups,
        )
        from crypto_trade.features_v3 import (
            run_features_v3 as _run_features,
        )

        default_output = str(Path(settings.data_dir) / "features_v3")
    elif track == "v2":
        from crypto_trade.features_v2 import (
            list_groups as _list_groups,
        )
        from crypto_trade.features_v2 import (
            run_features_v2 as _run_features,
        )

        default_output = str(Path(settings.data_dir) / "features_v2")
    else:
        from crypto_trade.features import (
            list_groups as _list_groups,
        )
        from crypto_trade.features import (
            run_features as _run_features,
        )

        default_output = str(Path(settings.data_dir) / "features")

    if args.list:
        print(f"Available {track} feature groups:")
        for name in _list_groups():
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
        groups = _list_groups()
    else:
        groups = [g.strip() for g in groups_arg.split(",")]
        available = set(_list_groups())
        unknown = [g for g in groups if g not in available]
        if unknown:
            print(
                f"Error: unknown {track} groups: {unknown}. Available: {_list_groups()}",
                file=sys.stderr,
            )
            sys.exit(1)

    start_ms = _parse_date(args.start) if args.start else None
    end_ms = _parse_date(args.end) if args.end else None
    output_dir = args.output or default_output

    print(f"Generating {track} features: {', '.join(groups)}")
    print(f"  Symbols: {', '.join(symbols)} | Interval: {args.interval} | Workers: {args.workers}")

    output_format = getattr(args, "format", "csv")
    if track in ("v2", "v3"):
        # v2/v3 feature runners always emit parquet — no groups/output_format kwargs.
        if output_format != "parquet":
            print(
                f"NOTE: --format {output_format} ignored for --track {track} "
                f"({track} features are parquet-only)",
                file=sys.stderr,
            )
        results = _run_features(
            symbols=symbols,
            interval=args.interval,
            data_dir=settings.data_dir,
            output_dir=output_dir,
            start_ms=start_ms,
            end_ms=end_ms,
            workers=args.workers,
        )
    else:
        results = _run_features(
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
    from crypto_trade.live.models import (
        ALL_MODELS,
        BASELINE_MODELS,
        COMBINED_MODELS,
        V2_BASELINE_MODELS,
        V3_BASELINE_MODELS,
        LiveConfig,
    )

    groups = tuple(g.strip() for g in args.feature_groups.split(","))

    track = getattr(args, "track", "v1")
    track_map = {
        "v1": BASELINE_MODELS,
        "v2": V2_BASELINE_MODELS,
        "v3": V3_BASELINE_MODELS,  # iter-v3/121 baseline (BCH/LDO/TRX)
        "both": COMBINED_MODELS,  # v1+v2 (deliberate; backward compat)
        "all": ALL_MODELS,  # v1+v2+v3 (11 models — disjoint universes)
    }
    selected_models = track_map[track]
    print(f"[live] Track: {track} ({len(selected_models)} models)")

    # Testnet routing: --testnet forces live trading and points signed calls
    # at Binance Futures testnet. Klines stay on production for full history.
    # BINANCE_AUTH_BASE_URL (loaded into settings.auth_base_url) overrides the
    # hardcoded testnet host so operators can re-target if Binance changes URL.
    testnet = bool(getattr(args, "testnet", False))
    if testnet:
        if not settings.binance_api_key or not settings.binance_api_secret:
            print(
                "ERROR: --testnet requires BINANCE_API_KEY / BINANCE_API_SECRET. "
                "Generate testnet keys at https://testnet.binancefuture.com.",
                file=sys.stderr,
            )
            sys.exit(2)
        # Testnet IS live trading (just on the test exchange). Promote
        # live_mode=True so LiveConfig(... dry_run=not args.live_mode ...)
        # correctly sets dry_run=False below.
        args.live_mode = True

    # Auth URL resolution: env wins; if --testnet and env unset, hardcode
    # the testnet host. Otherwise pass None so the engine falls back to
    # base_url (preserves pre-testnet single-URL behavior).
    auth_base_url = getattr(settings, "auth_base_url", None)
    if testnet and auth_base_url is None:
        auth_base_url = "https://testnet.binancefuture.com"

    # Surface a loud banner whenever the auth URL differs from base_url, so
    # an .env-set staging URL can never quietly route prod orders to staging.
    if auth_base_url is not None and auth_base_url != settings.base_url:
        print(f"[live] AUTH endpoint OVERRIDE: {auth_base_url}")

    # DB path is the live-mode fallback. The engine overrides this to
    # data/testnet.db when config.testnet is True and to data/dry_run.db
    # when config.dry_run is True (see engine.py). We always pass live.db
    # here so single-source-of-truth lives in the engine.
    db_path = Path(settings.data_dir) / "live.db"

    config = LiveConfig(
        models=selected_models,
        interval="8h",
        max_amount_usd=float(args.amount),
        leverage=args.leverage,
        data_dir=Path(settings.data_dir),
        features_dir=Path(settings.data_dir) / "features",
        feature_groups=groups,
        db_path=db_path,
        poll_interval_seconds=args.poll_interval,
        dry_run=not args.live_mode,
        testnet=testnet,
    )

    engine = LiveEngine(
        config=config,
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret,
        base_url=settings.base_url,
        auth_base_url=auth_base_url,
    )
    engine.run()


def _cmd_portfolio_report(args, settings) -> None:
    """Build a combined v1+v2 portfolio tearsheet from two trade CSVs."""
    from pathlib import Path

    import pandas as pd

    from crypto_trade.live.portfolio_report import (
        ReportInputs,
        build_combined_report,
    )

    v1 = pd.read_csv(args.v1_trades)
    v2 = pd.read_csv(args.v2_trades)
    out_path = Path(args.out)
    rep = build_combined_report(
        ReportInputs(v1_trades=v1, v2_trades=v2),
        html_out=out_path,
    )
    print(
        f"Combined: {rep.total_trades} trades "
        f"(v1: {rep.v1_trades}, v2: {rep.v2_trades}). "
        f"Sharpe(monthly)={rep.combined_sharpe_monthly:.4f}, "
        f"Sharpe(daily)={rep.combined_sharpe_daily:.4f}, "
        f"MaxDD={rep.combined_max_drawdown_pct:.2f}, "
        f"Calmar={rep.combined_calmar:.4f}, "
        f"PnL={rep.combined_weighted_pnl:.2f}"
    )
    print(f"Wrote {out_path}")


def _cmd_seed_live_db(args, settings) -> None:
    """Seed the live DB with backtest trades to preload R1/R2/VT/cooldown state."""
    from pathlib import Path

    from crypto_trade.live.db_seeder import seed_live_db_from_backtest
    from crypto_trade.live.models import (
        ALL_MODELS,
        BASELINE_MODELS,
        COMBINED_MODELS,
        V2_BASELINE_MODELS,
        V3_BASELINE_MODELS,
        LiveConfig,
    )

    track_map = {
        "v1": BASELINE_MODELS,
        "v2": V2_BASELINE_MODELS,
        "v3": V3_BASELINE_MODELS,  # iter-v3/121 baseline (BCH/LDO/TRX)
        "both": COMBINED_MODELS,  # v1+v2 (deliberate; backward compat)
        "all": ALL_MODELS,  # v1+v2+v3 (11 models — disjoint universes)
    }
    selected_models = track_map[args.track]

    cfg = LiveConfig(models=selected_models, data_dir=Path(settings.data_dir))

    v1_paths = [Path(p) for p in (args.v1_trades or [])]
    v2_paths = [Path(p) for p in (args.v2_trades or [])]
    v3_paths = [Path(p) for p in (args.v3_trades or [])]

    if not v1_paths and not v2_paths and not v3_paths:
        print(
            "ERROR: provide at least one --v1-trades / --v2-trades / --v3-trades CSV.",
            file=sys.stderr,
        )
        sys.exit(2)

    db_path = Path(args.db)
    print(f"[seed] Target DB: {db_path}")
    print(f"[seed] Track: {args.track} ({len(selected_models)} models)")
    if v1_paths:
        print(f"[seed] v1 CSVs: {', '.join(str(p) for p in v1_paths)}")
    if v2_paths:
        print(f"[seed] v2 CSVs: {', '.join(str(p) for p in v2_paths)}")
    if v3_paths:
        print(f"[seed] v3 CSVs: {', '.join(str(p) for p in v3_paths)}")
    if args.reseed:
        print("[seed] reseed=True (boundary keys will be overwritten)")

    counts = seed_live_db_from_backtest(
        db_path=db_path,
        v1_trades_csvs=v1_paths,
        v2_trades_csvs=v2_paths,
        live_config=cfg,
        reseed=args.reseed,
        v3_trades_csvs=v3_paths,
    )

    print()
    print("=== Seeding result ===")
    for k, v in counts.items():
        print(f"  {k:30s}: {v}")
    total_inserted = (
        counts["v1_closed"] + counts["v1_open"] + counts["v2_closed"] + counts["v2_open"]
    )
    print(f"  TOTAL inserted               : {total_inserted}")
    print()
    print(
        "Next step: launch `crypto-trade live --track both`. Catch-up resumes from the "
        "seeded boundary (seeded_through_* keys) and produces trades only for candles "
        "after the seeded data."
    )


def _cmd_fetch_funding(args, settings) -> None:
    """Fetch funding-rate history from /fapi/v1/fundingRate and cache locally.

    Iterates over each symbol, fetches incrementally from cache, and writes
    data/funding_rates/<SYMBOL>.csv (schema: funding_time, funding_rate).

    iter-v3/019: supports the NEW funding_rate_zscore_30 feature family.
    """
    import time as _time
    from pathlib import Path

    import httpx as _httpx
    import pandas as _pd

    symbols = [s.strip() for s in args.symbols.split(",")]
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(settings.data_dir) / "funding_rates"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default start: 2019-01-01 00:00:00 UTC in ms
    default_start_ms = 1_546_300_800_000
    if args.start:
        from datetime import UTC, datetime

        dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=UTC)
        default_start_ms = int(dt.timestamp() * 1000)

    funding_endpoint = "/fapi/v1/fundingRate"
    fapi_base = "https://fapi.binance.com"

    total_fetched = 0
    for symbol in symbols:
        cache_path = output_dir / f"{symbol}.csv"
        print(f"\n[fetch-funding] {symbol} → {cache_path}")

        # Load existing cache (incremental)
        cached = _pd.DataFrame(columns=["funding_time", "funding_rate"])
        start_ms = default_start_ms
        if cache_path.exists():
            cached = _pd.read_csv(cache_path)
            if len(cached) > 0:
                start_ms = int(cached["funding_time"].max()) + 1
                resume_ts = _pd.to_datetime(start_ms, unit="ms")
                print(f"  cache hit: {len(cached)} rows, resuming from {resume_ts}")

        rows: list[dict] = []
        current_start = start_ms
        page = 0

        with _httpx.Client(base_url=fapi_base, timeout=30.0) as http:
            while True:
                params = {"symbol": symbol, "limit": 1000, "startTime": current_start}
                r = http.get(funding_endpoint, params=params)
                r.raise_for_status()
                data = r.json()
                if not data:
                    break
                for d in data:
                    rows.append(
                        {
                            "funding_time": int(d["fundingTime"]),
                            "funding_rate": float(d["fundingRate"]),
                        }
                    )
                page += 1
                last_time = int(data[-1]["fundingTime"])
                print(
                    f"  page {page}: {len(data)} rows, last={_pd.to_datetime(last_time, unit='ms')}"
                )
                if len(data) < 1000:
                    break
                current_start = last_time + 1
                _time.sleep(0.25)  # rate limit

        new_df = _pd.DataFrame(rows)
        if len(new_df) == 0 and len(cached) == 0:
            print(f"  WARNING: no data fetched for {symbol}")
            continue

        full = _pd.concat([cached, new_df], ignore_index=True)
        full = (
            full.drop_duplicates(subset=["funding_time"], keep="last")
            .sort_values("funding_time")
            .reset_index(drop=True)
        )
        full.to_csv(cache_path, index=False)
        total_fetched += len(new_df)
        print(f"  saved {len(full)} total rows ({len(new_df)} new) → {cache_path}")

    print(f"\n[fetch-funding] Done — {total_fetched} new rows across {len(symbols)} symbols")


def _cmd_fetch_spot(args, settings) -> None:
    """Fetch Binance SPOT klines from data.binance.vision monthly archives.

    Writes data/spot/<SYMBOL>/<INTERVAL>.csv with the 11-column kline schema
    (identical to the perp CSV schema). Incremental: re-running appends only
    candles not already cached (dedup on open_time).

    Timestamp normalisation (iter-v3/086 Section 3.2 — LOAD-BEARING):
    Binance spot kline archives switched open_time/close_time from millisecond
    (13-digit) to microsecond (16-digit) epochs at 2025-01. This function
    normalises every timestamp to milliseconds so the spot CSVs join cleanly
    with the millisecond perp CSVs on open_time. Without this normalisation a
    microsecond open_time would never match a millisecond perp open_time.

    Source: data.binance.vision/data/spot/monthly/klines/<SYM>/<IV>/<SYM>-<IV>-<YYYY-MM>.zip
    Current month (not yet archived): Binance /api/v3/klines REST API fallback.
    """
    import csv as _csv
    import io as _io
    import time as _time
    import zipfile as _zipfile
    from datetime import UTC, datetime
    from pathlib import Path

    import httpx as _httpx

    spot_archive_tmpl = (
        "https://data.binance.vision/data/spot/monthly/klines/{sym}/{iv}/{sym}-{iv}-{ym}.zip"
    )
    spot_api_base = "https://api.binance.com"
    kline_header = [
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
    ]

    def _to_ms(val: int) -> int:
        """Normalise a Binance epoch value to milliseconds.

        Binance spot archives switched from ms (13-digit) to µs (16-digit) at
        2025-01. Anything >= 1e15 is a microsecond epoch — divide by 1000.
        Unit test: _to_ms(1_735_689_600_000_000) == 1_735_689_600_000.
        """
        return val // 1000 if val >= 1_000_000_000_000_000 else val

    def _month_range(start: str, end: str) -> list[str]:
        sy, sm = (int(x) for x in start.split("-"))
        ey, em = (int(x) for x in end.split("-"))
        out: list[str] = []
        y, m = sy, sm
        while (y, m) <= (ey, em):
            out.append(f"{y:04d}-{m:02d}")
            m += 1
            if m == 13:
                m, y = 1, y + 1
        return out

    def _fetch_month_archive(http: _httpx.Client, sym: str, iv: str, ym: str) -> list[list[str]]:
        """Download one monthly spot ZIP; return 11-col kline rows (ms-normalised)."""
        url = spot_archive_tmpl.format(sym=sym, iv=iv, ym=ym)
        for attempt in range(3):
            try:
                r = http.get(url, timeout=60.0)
                if r.status_code in (403, 404) or not r.content.startswith(b"PK"):
                    return []  # absent archive or NoSuchKey XML
                r.raise_for_status()
                zf = _zipfile.ZipFile(_io.BytesIO(r.content))
                name = zf.namelist()[0]
                rows: list[list[str]] = []
                for line in zf.read(name).decode().splitlines():
                    parts = line.split(",")
                    if parts and parts[0].lstrip("-").isdigit():
                        parts[0] = str(_to_ms(int(parts[0])))
                        parts[6] = str(_to_ms(int(parts[6])))
                        rows.append(parts[:11])
                return rows
            except (_httpx.HTTPError, _zipfile.BadZipFile) as exc:
                if attempt == 2:
                    raise
                print(f"    retry {sym} {ym}: {exc}")
                _time.sleep(2.0 * (attempt + 1))
        return []

    def _fetch_current_month_api(
        http: _httpx.Client, sym: str, iv: str, since_ms: int
    ) -> list[list[str]]:
        """Fill the current (not-yet-archived) month via /api/v3/klines."""
        rows: list[list[str]] = []
        start = since_ms
        while True:
            params = {
                "symbol": sym,
                "interval": iv,
                "startTime": start,
                "limit": 1000,
            }
            r = http.get("/api/v3/klines", params=params)
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            for k in data:
                ot = _to_ms(int(k[0]))
                ct = _to_ms(int(k[6]))
                now_ms = int(datetime.now(UTC).timestamp() * 1000)
                if ct >= now_ms:
                    continue  # forming candle — skip
                rows.append(
                    [
                        str(ot),
                        str(k[1]),
                        str(k[2]),
                        str(k[3]),
                        str(k[4]),
                        str(k[5]),
                        str(ct),
                        str(k[7]),
                        str(k[8]),
                        str(k[9]),
                        str(k[10]),
                    ]
                )
            if len(data) < 1000:
                break
            start = _to_ms(int(data[-1][6])) + 1
            _time.sleep(0.25)
        return rows

    symbols = [s.strip() for s in args.symbols.split(",")]
    intervals = [i.strip() for i in args.intervals.split(",")]
    if args.output_dir:
        output_root = Path(args.output_dir)
    else:
        output_root = Path(settings.data_dir) / "spot"
    output_root.mkdir(parents=True, exist_ok=True)

    # Widen the month range to cover historical spot depth (spot predates perp).
    now_ym = datetime.now(UTC).strftime("%Y-%m")
    months = _month_range("2018-01", now_ym)

    total_new = 0
    with (
        _httpx.Client(timeout=60.0) as bulk_http,
        _httpx.Client(base_url=spot_api_base, timeout=30.0) as api_http,
    ):
        for sym in symbols:
            for iv in intervals:
                out_dir = output_root / sym
                out_dir.mkdir(parents=True, exist_ok=True)
                out_csv = out_dir / f"{iv}.csv"

                # Load existing cache (incremental dedup on open_time).
                seen: set[int] = set()
                existing: list[list[str]] = []
                if out_csv.exists():
                    with out_csv.open() as fh:
                        rd = _csv.reader(fh)
                        next(rd, None)  # skip header
                        for row in rd:
                            if row:
                                existing.append(row)
                                seen.add(int(row[0]))
                    print(f"[fetch-spot] {sym}/{iv}: cache hit — {len(existing)} rows")
                else:
                    print(f"[fetch-spot] {sym}/{iv}: no cache — full fetch")

                new_rows: list[list[str]] = []

                # --- Bulk archive months ---
                for ym in months:
                    rows = _fetch_month_archive(bulk_http, sym, iv, ym)
                    fresh = [r for r in rows if int(r[0]) not in seen]
                    if fresh:
                        new_rows.extend(fresh)
                        seen.update(int(r[0]) for r in fresh)
                    if rows:
                        print(f"  {sym}/{iv} {ym}: {len(rows)} rows ({len(fresh)} new)")
                    _time.sleep(0.05)  # light rate-limit courtesy

                # --- Current month via REST API ---
                last_ms = (
                    max(int(r[0]) for r in (existing + new_rows)) if (existing or new_rows) else 0
                )
                api_rows = _fetch_current_month_api(api_http, sym, iv, last_ms + 1)
                fresh_api = [r for r in api_rows if int(r[0]) not in seen]
                if fresh_api:
                    new_rows.extend(fresh_api)
                    seen.update(int(r[0]) for r in fresh_api)
                    print(f"  {sym}/{iv} API current-month: {len(fresh_api)} new rows")

                combined = existing + new_rows
                combined.sort(key=lambda r: int(r[0]))
                with out_csv.open("w", newline="") as fh:
                    wr = _csv.writer(fh)
                    wr.writerow(kline_header)
                    wr.writerows(combined)

                total_new += len(new_rows)
                if combined:
                    first_ms = int(combined[0][0])
                    last_ms_out = int(combined[-1][0])
                    fd = datetime.fromtimestamp(first_ms / 1000, UTC).date()
                    ld = datetime.fromtimestamp(last_ms_out / 1000, UTC).date()
                    print(
                        f"[fetch-spot] {sym}/{iv}: {len(combined)} total rows "
                        f"({len(new_rows)} new) {fd} → {ld} → {out_csv}"
                    )

    print(f"\n[fetch-spot] Done — {total_new} new rows across {len(symbols)} symbols")


def _cmd_fetch_oi(args, settings) -> None:
    """Fetch Binance Futures open-interest metrics from data.binance.vision daily archives.

    Downloads ``data/futures/um/daily/metrics/<SYM>/<SYM>-metrics-YYYY-MM-DD.zip``
    daily ZIPs (5-min granularity), resamples to 8h, and writes
    ``data/open_interest/<SYM>/8h.csv``.

    Schema of cached 8h CSV (one row per 8h bar, open_time in ms):
        open_time, sum_open_interest, sum_open_interest_value,
        count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
        count_long_short_ratio, sum_taker_long_short_vol_ratio

    Each column is resampled from the 5-min rows of the PREVIOUS fully-closed
    8h period:
        - sum_open_interest / sum_open_interest_value: LAST (snapshot at period close)
        - count_* / sum_*: SUM (accumulate within the 8h window)

    Incremental: re-running appends only new days not already cached.
    Coverage: BTCUSDT from 2020-09-01; LDO/TRX/BCH from listing date.
    """
    import csv as _csv
    import io as _io
    import time as _time
    import zipfile as _zipfile
    from datetime import UTC, date, datetime, timedelta
    from pathlib import Path

    import httpx as _httpx

    oi_archive_tmpl = (
        "https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{ymd}.zip"
    )

    oi_8h_header = [
        "open_time",
        "sum_open_interest",
        "sum_open_interest_value",
        "count_toptrader_long_short_ratio",
        "sum_toptrader_long_short_ratio",
        "count_long_short_ratio",
        "sum_taker_long_short_vol_ratio",
    ]

    # Binance Futures 8h bar boundaries: 00:00, 08:00, 16:00 UTC (ms).
    _8h_ms = 8 * 3_600_000

    def _floor_to_8h(ts_ms: int) -> int:
        """Floor a millisecond timestamp to the containing 8h bar open_time."""
        return (ts_ms // _8h_ms) * _8h_ms

    def _fetch_day_zip(http: _httpx.Client, sym: str, ymd: str) -> list[list[str]] | None:
        """Download one daily metrics ZIP; return raw 5-min rows or None if absent."""
        url = oi_archive_tmpl.format(sym=sym, ymd=ymd)
        for attempt in range(3):
            try:
                r = http.get(url, timeout=60.0)
                if r.status_code in (403, 404):
                    return None  # date not yet archived or symbol has no history
                if not r.content.startswith(b"PK"):
                    return None  # NoSuchKey XML or empty response
                r.raise_for_status()
                zf = _zipfile.ZipFile(_io.BytesIO(r.content))
                name = zf.namelist()[0]
                rows: list[list[str]] = []
                for line in zf.read(name).decode().splitlines():
                    parts = line.split(",")
                    # schema: create_time, symbol, col1, col2, ...
                    # create_time is "YYYY-MM-DD HH:MM:SS" — skip header line
                    if parts and len(parts) >= 8 and parts[0][:4].isdigit() and "-" in parts[0]:
                        rows.append(parts)
                return rows
            except (_httpx.HTTPError, _zipfile.BadZipFile) as exc:
                if attempt == 2:
                    print(f"  [fetch-oi] WARN: failed {sym} {ymd} after 3 attempts: {exc}")
                    return None
                _time.sleep(2.0 * (attempt + 1))
        return None

    def _resample_5min_to_8h(raw_rows: list[list[str]]) -> list[list[str]]:
        """Resample 5-min metric rows to 8h bars.

        Input row schema (from the ZIP, 8 cols):
            create_time (ms), symbol, sum_open_interest, sum_open_interest_value,
            count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
            count_long_short_ratio, sum_taker_long_short_vol_ratio

        Output row schema (oi_8h_header, 7 cols):
            open_time (ms), sum_open_interest (LAST), sum_open_interest_value (LAST),
            count_toptrader_long_short_ratio (SUM), sum_toptrader_long_short_ratio (SUM),
            count_long_short_ratio (SUM), sum_taker_long_short_vol_ratio (SUM)

        Each output row represents the 8h bar STARTING at open_time. The 5-min rows
        assigned to bar T are those with create_time in [T, T + 8h). The bar's OI
        snapshot is the LAST 5-min value in that window (latest OI reading before
        bar close). The flow metrics (count/sum) are accumulated across the window.

        Past-only convention (enforced at the feature level via .shift(1) in
        derivatives_state_v3.py): bar T's cached values are based on the 5-min
        rows of the SAME bar period — no look-ahead because bar T's close_time is
        T + 8h and the runner reads open_time-aligned snapshots that are then
        shifted before feature construction.
        """
        if not raw_rows:
            return []

        # Parse to typed arrays
        # create_time format: "YYYY-MM-DD HH:MM:SS" UTC
        bars: dict[int, dict] = {}
        for parts in raw_rows:
            if len(parts) < 8:
                continue
            try:
                # Parse "YYYY-MM-DD HH:MM:SS" -> ms epoch
                dt = datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
                ts_ms = int(dt.timestamp() * 1000)
            except (ValueError, OverflowError):
                continue
            bar_open = _floor_to_8h(ts_ms)
            if bar_open not in bars:
                bars[bar_open] = {
                    "last_create_time": 0,
                    "sum_oi": 0.0,
                    "sum_oi_val": 0.0,
                    "cnt_top_ls": 0.0,
                    "sum_top_ls": 0.0,
                    "cnt_ls": 0.0,
                    "sum_tv_ls": 0.0,
                }
            b = bars[bar_open]
            # Track the latest 5-min timestamp to get the LAST OI snapshot
            if ts_ms > b["last_create_time"]:
                b["last_create_time"] = ts_ms
                try:
                    b["sum_oi"] = float(parts[2]) if parts[2] else 0.0
                    b["sum_oi_val"] = float(parts[3]) if parts[3] else 0.0
                except (ValueError, IndexError):
                    pass
            # Accumulate flow metrics (SUM)
            try:
                b["cnt_top_ls"] += float(parts[4]) if parts[4] else 0.0
                b["sum_top_ls"] += float(parts[5]) if parts[5] else 0.0
                b["cnt_ls"] += float(parts[6]) if parts[6] else 0.0
                b["sum_tv_ls"] += float(parts[7]) if parts[7] else 0.0
            except (ValueError, IndexError):
                pass

        # Emit sorted 8h rows
        result: list[list[str]] = []
        for bar_open in sorted(bars.keys()):
            b = bars[bar_open]
            result.append(
                [
                    str(bar_open),
                    f"{b['sum_oi']:.6f}",
                    f"{b['sum_oi_val']:.6f}",
                    f"{b['cnt_top_ls']:.6f}",
                    f"{b['sum_top_ls']:.6f}",
                    f"{b['cnt_ls']:.6f}",
                    f"{b['sum_tv_ls']:.6f}",
                ]
            )
        return result

    symbols = [s.strip() for s in args.symbols.split(",")]
    if args.output_dir:
        output_root = Path(args.output_dir)
    else:
        output_root = Path(settings.data_dir) / "open_interest"
    output_root.mkdir(parents=True, exist_ok=True)

    # Date range: 2020-09-01 (earliest OI archive) to yesterday.
    start_date = date(2020, 9, 1)
    end_date = datetime.now(UTC).date() - timedelta(days=1)

    total_new_rows = 0

    with _httpx.Client(timeout=60.0) as http:
        for sym in symbols:
            out_dir = output_root / sym
            out_dir.mkdir(parents=True, exist_ok=True)
            out_csv = out_dir / "8h.csv"

            # Load existing cache — dedup on open_time (ms)
            seen_bar_times: set[int] = set()
            existing_rows: list[list[str]] = []
            if out_csv.exists():
                with out_csv.open() as fh:
                    rd = _csv.reader(fh)
                    next(rd, None)  # skip header
                    for row in rd:
                        if row and row[0].isdigit():
                            existing_rows.append(row)
                            seen_bar_times.add(int(row[0]))
                print(f"[fetch-oi] {sym}: cache hit — {len(existing_rows)} 8h rows")
            else:
                print(f"[fetch-oi] {sym}: no cache — full fetch from {start_date}")

            new_rows: list[list[str]] = []
            cur_date = start_date
            days_fetched = 0

            while cur_date <= end_date:
                ymd = cur_date.strftime("%Y-%m-%d")
                raw = _fetch_day_zip(http, sym, ymd)
                if raw is not None:
                    resampled = _resample_5min_to_8h(raw)
                    fresh = [r for r in resampled if int(r[0]) not in seen_bar_times]
                    if fresh:
                        new_rows.extend(fresh)
                        seen_bar_times.update(int(r[0]) for r in fresh)
                    days_fetched += 1
                    if days_fetched % 100 == 0:
                        print(f"  [fetch-oi] {sym}: fetched {days_fetched} days so far ...")
                _time.sleep(0.05)
                cur_date += timedelta(days=1)

            combined = existing_rows + new_rows
            combined.sort(key=lambda r: int(r[0]))

            with out_csv.open("w", newline="") as fh:
                wr = _csv.writer(fh)
                wr.writerow(oi_8h_header)
                wr.writerows(combined)

            total_new_rows += len(new_rows)
            if combined:
                first_ms = int(combined[0][0])
                last_ms = int(combined[-1][0])
                fd = datetime.fromtimestamp(first_ms / 1000, UTC).date()
                ld = datetime.fromtimestamp(last_ms / 1000, UTC).date()
                print(
                    f"[fetch-oi] {sym}: {len(combined)} 8h rows "
                    f"({len(new_rows)} new) {fd} → {ld} → {out_csv}"
                )
            else:
                print(f"[fetch-oi] {sym}: no data found (symbol may have no OI archive)")

    print(f"\n[fetch-oi] Done — {total_new_rows} new 8h rows across {len(symbols)} symbols")


if __name__ == "__main__":
    main()

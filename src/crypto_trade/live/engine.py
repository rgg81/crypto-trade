"""Live trading engine — orchestrates 3 independent LightGBM models.

Mirrors run_baseline_v152.py: each ModelRunner manages one LightGBM model
with its own symbol set and ATR config. The LiveEngine runs the shared
poll loop, feature pipeline, and order management.
"""

from __future__ import annotations

import datetime
import signal
import time

import numpy as np
import pandas as pd

from crypto_trade.backtest import check_order, compute_vt_scale
from crypto_trade.backtest_models import Signal
from crypto_trade.client import BinanceClient
from crypto_trade.feature_store import lookup_features
from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.data_pipeline import (
    build_master,
    detect_new_candle,
    refresh_features,
    refresh_klines,
)
from crypto_trade.live.models import (
    BASELINE_FEATURE_COLUMNS,
    LiveConfig,
    LiveTrade,
    ModelConfig,
    _new_id,
)
from crypto_trade.live.order_manager import OrderManager, compute_sl_tp, trade_to_order
from crypto_trade.live.reconciler import reconcile
from crypto_trade.live.state_store import StateStore
from crypto_trade.live.trade_logger import TradeLogger, to_trade_result
from crypto_trade.models import Kline
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy, _epoch_ms_to_month

# 8h in milliseconds — used for cooldown computation
_INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
}


def _day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(ms / 1000, tz=datetime.UTC).strftime("%Y-%m-%d")


def _month_start_ms(epoch_ms: int) -> int:
    """Return epoch ms for the 1st of the month containing epoch_ms."""
    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=datetime.UTC)
    first = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(first.timestamp() * 1000)


def _previous_month_start_ms(epoch_ms: int) -> int:
    """Return epoch ms for the 1st of the previous month."""
    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=datetime.UTC)
    first_of_this_month = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Subtract 1 day to land in the previous month, then snap to day=1
    prev = (first_of_this_month - datetime.timedelta(days=1)).replace(day=1)
    return int(prev.timestamp() * 1000)


class ModelRunner:
    """Manages one LightGBM model (e.g., Model A for BTC/ETH)."""

    def __init__(self, model_config: ModelConfig, live_config: LiveConfig) -> None:
        self.model_config = model_config
        self.strategy = LightGbmStrategy(
            training_months=live_config.training_months,
            n_trials=live_config.n_trials,
            cv_splits=live_config.cv_splits,
            label_tp_pct=live_config.take_profit_pct,
            label_sl_pct=live_config.stop_loss_pct,
            label_timeout_minutes=live_config.timeout_minutes,
            fee_pct=live_config.fee_pct,
            features_dir=str(live_config.features_dir),
            seed=42,
            verbose=1,
            atr_tp_multiplier=model_config.atr_tp_multiplier,
            atr_sl_multiplier=model_config.atr_sl_multiplier,
            use_atr_labeling=model_config.use_atr_labeling,
            ensemble_seeds=list(live_config.ensemble_seeds),
            feature_columns=list(BASELINE_FEATURE_COLUMNS),
        )
        self._master: pd.DataFrame | None = None

    def warmup(self, master: pd.DataFrame) -> None:
        """Run compute_features on the master DF and store reference."""
        self._master = master
        self.strategy.compute_features(master)

    def update_master(self, master: pd.DataFrame) -> None:
        """Update master reference without retraining (for same-month ticks)."""
        self._master = master

    def get_signals(self, new_candle_times: dict[str, int]) -> dict[str, Signal]:
        """Get signals for symbols with new candles."""
        signals: dict[str, Signal] = {}
        for symbol in self.model_config.symbols:
            if symbol in new_candle_times:
                signals[symbol] = self.strategy.get_signal(symbol, new_candle_times[symbol])
        return signals

    def get_close_price(self, symbol: str, open_time: int) -> float | None:
        """Look up close price from the master DataFrame for exact parity with backtest."""
        if self._master is None:
            return None
        row = self._master[
            (self._master["symbol"] == symbol) & (self._master["open_time"] == open_time)
        ]
        if row.empty:
            return None
        return float(row["close"].iloc[0])


class LiveEngine:
    """Main live trading engine — polls for new candles and runs 3 models."""

    def __init__(
        self,
        config: LiveConfig,
        api_key: str = "",
        api_secret: str = "",
        base_url: str = "https://fapi.binance.com",
    ) -> None:
        self.config = config
        self._running = True
        self._all_symbols = config.all_symbols
        self._candle_duration_ms = _INTERVAL_MS.get(config.interval, 28_800_000)

        # Use limit=2 for candle polling (only need last closed + currently forming)
        self._read_client = BinanceClient(base_url=base_url, limit=2, rate_limit_pause=0.25)
        self._auth_client: AuthenticatedBinanceClient | None = None
        if not config.dry_run and api_key:
            self._auth_client = AuthenticatedBinanceClient(
                api_key=api_key,
                api_secret=api_secret,
                base_url=base_url,
            )

        db_path = config.db_path
        if config.dry_run:
            db_path = config.data_dir / "dry_run.db"
        self._state = StateStore(db_path)

        self._order_mgr = OrderManager(config, self._state, self._auth_client)

        log_name = "dry_run_trades.csv" if config.dry_run else "live_trades.csv"
        self._logger = TradeLogger(config.data_dir / log_name, config.fee_pct, config.dry_run)

        self._runners = [ModelRunner(mc, config) for mc in config.models]

        # Separate client for kline fetches (higher limit for initial setup)
        self._fetch_client = BinanceClient(base_url=base_url, limit=1500, rate_limit_pause=0.25)

        # Per-symbol daily PnL tracking for vol targeting — same as backtest.py:186
        # symbol -> {YYYY-MM-DD -> sum of net_pnl_pct that closed on that day}
        self._vt_daily_pnl: dict[str, dict[str, float]] = {}

    def run(self) -> None:
        """Main entry point — runs until SIGINT/SIGTERM."""
        self._setup_signal_handlers()
        self._print_banner()
        self._reconcile()
        self._rebuild_vt_history()
        self._initial_setup()
        self._catch_up()

        print(f"[live] Entering poll loop (every {self.config.poll_interval_seconds}s)")
        while self._running:
            try:
                self._tick()
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"[live] tick error: {exc}")
            time.sleep(self.config.poll_interval_seconds)

        self._shutdown()

    def _print_banner(self) -> None:
        mode = "DRY-RUN" if self.config.dry_run else "LIVE"
        print(f"[live] Starting baseline v152 [{mode}]")
        for mc in self.config.models:
            print(
                f"  Model {mc.name}: {', '.join(mc.symbols)} "
                f"(ATR TP={mc.atr_tp_multiplier}, SL={mc.atr_sl_multiplier})"
            )
        print(f"  Interval: {self.config.interval} | Amount: ${self.config.max_amount_usd}")
        print(
            f"  SL={self.config.stop_loss_pct}% TP={self.config.take_profit_pct}% "
            f"Timeout={self.config.timeout_minutes}m"
        )
        if self.config.vol_targeting:
            print(
                f"  VT: target={self.config.vt_target_vol}, "
                f"lookback={self.config.vt_lookback_days}d, "
                f"scale=[{self.config.vt_min_scale}, {self.config.vt_max_scale}]"
            )

    def _setup_signal_handlers(self) -> None:
        def _handle(signum, frame):
            print(f"\n[live] Received signal {signum}, shutting down...")
            self._running = False

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)

    def _reconcile(self) -> None:
        msgs = reconcile(self._state, self._auth_client, self.config.dry_run)
        for m in msgs:
            print(m)

    def _rebuild_vt_history(self) -> None:
        """Rebuild per-symbol daily PnL from closed trades in DB for vol targeting."""
        if not self.config.vol_targeting:
            return
        self._vt_daily_pnl = {}
        for trade in self._state.get_all_trades():
            if trade.status != "closed" or trade.exit_time is None:
                continue
            result = to_trade_result(trade, self.config.fee_pct)
            if result is None:
                continue
            close_date = _day_of(result.close_time)
            sym_daily = self._vt_daily_pnl.setdefault(trade.symbol, {})
            sym_daily[close_date] = sym_daily.get(close_date, 0.0) + result.net_pnl_pct
        n = sum(len(d) for d in self._vt_daily_pnl.values())
        if n > 0:
            print(
                f"[live] Rebuilt VT history: {n} daily PnL entries across "
                f"{len(self._vt_daily_pnl)} symbols"
            )

    def _record_trade_close_for_vt(self, trade: LiveTrade) -> None:
        """Record a closed trade's PnL into the VT daily accumulator."""
        if not self.config.vol_targeting:
            return
        result = to_trade_result(trade, self.config.fee_pct)
        if result is None:
            return
        close_date = _day_of(result.close_time)
        sym_daily = self._vt_daily_pnl.setdefault(trade.symbol, {})
        sym_daily[close_date] = sym_daily.get(close_date, 0.0) + result.net_pnl_pct

    def _set_cooldown(self, model_name: str, symbol: str, close_time: int) -> None:
        """Set cooldown after a trade closes — same as backtest.py:238-242."""
        if self.config.cooldown_candles <= 0:
            return
        cooldown_until = close_time + self.config.cooldown_candles * self._candle_duration_ms
        self._state.set_state(f"cooldown_{model_name}_{symbol}", str(cooldown_until))

    def _handle_trade_close(self, trade: LiveTrade) -> None:
        """Common handler when a trade closes: log, record VT, set cooldown."""
        updated = self._state.get_trade(trade.id)
        if updated is None:
            return
        self._logger.log_close(updated)
        self._record_trade_close_for_vt(updated)
        self._set_cooldown(updated.model_name, updated.symbol, updated.exit_time or 0)

    def _patch_month_features(
        self,
        runner: ModelRunner,
        model_syms: list[str],
        new_candles: dict[str, Kline],
        master: pd.DataFrame,
    ) -> None:
        """Add new candles' features to the strategy's _month_features dict.

        Used on same-month ticks to avoid calling compute_features (which would
        reset the trained model). Also updates the strategy's internal master
        reference so future operations see the latest candle data.
        """
        strategy = runner.strategy
        # Update master reference for any code that might read it
        strategy._master = master
        strategy._sym_arr = master["symbol"].to_numpy(dtype=str)
        strategy._open_time_arr = master["open_time"].values

        if not strategy._selected_cols:
            return  # model not yet trained for this month (shouldn't happen)

        for sym in model_syms:
            ot = new_candles[sym].open_time
            if (sym, ot) in strategy._month_features:
                continue  # already present
            features_df = lookup_features(
                [(sym, ot)],
                strategy.features_dir,
                strategy._interval,
                columns=strategy._selected_cols,
            )
            if features_df.empty:
                print(f"[live] WARNING: no features in Parquet for {sym} at {ot}")
                continue
            feat_row = features_df.iloc[0]
            feat_array = np.array(
                [feat_row[col] for col in strategy._selected_cols], dtype=np.float64
            )
            strategy._month_features[(sym, ot)] = feat_array

            # Also refresh ATR (NATR) if dynamic barriers are enabled
            if strategy.atr_tp_multiplier is not None:
                natr_df = lookup_features(
                    [(sym, ot)],
                    strategy.features_dir,
                    strategy._interval,
                    columns=[strategy.atr_column],
                )
                if not natr_df.empty:
                    strategy._month_natr[(sym, ot)] = float(natr_df.iloc[0][strategy.atr_column])

    def _initial_setup(self) -> None:
        """Fetch latest klines, regenerate features, warmup all models."""
        all_symbols = list(self._all_symbols)
        print(f"[live] Refreshing klines for {', '.join(all_symbols)}...")
        refresh_klines(self._fetch_client, all_symbols, self.config.interval, self.config.data_dir)

        print("[live] Refreshing features...")
        refresh_features(
            all_symbols,
            self.config.interval,
            str(self.config.data_dir),
            str(self.config.features_dir),
            list(self.config.feature_groups),
        )

        for runner in self._runners:
            symbols = list(runner.model_config.symbols)
            master = build_master(symbols, self.config.interval, self.config.data_dir)
            if master.empty:
                print(f"[live] WARNING: No data for Model {runner.model_config.name}")
                continue
            print(f"[live] Warming up Model {runner.model_config.name} ({len(master)} candles)")
            runner.warmup(master)

        if not self.config.dry_run and self._auth_client is not None:
            print("[live] Setting leverage...")
            for symbol in all_symbols:
                try:
                    self._auth_client.set_leverage(symbol, self.config.leverage)
                except Exception as exc:
                    print(f"[live] Failed to set leverage for {symbol}: {exc}")

    def _catch_up(self) -> None:
        """Replay candles from previous month to build trade state before polling.

        We start one month before the current month so any trades still open
        at the start of the current month (e.g. from a late-previous-month
        signal with a multi-day timeout) carry over correctly. Without this,
        the catch-up starts with empty state and may open trades that the
        backtest would have blocked due to an open position.
        """
        print("[live] Catching up on recent candles (prev + current month)...")
        for runner in self._runners:
            self._catch_up_model(runner)

    def _catch_up_model(self, runner: ModelRunner) -> None:
        master = runner._master
        if master is None or master.empty:
            return

        now_ms = int(time.time() * 1000)
        # Start one month earlier to capture carry-over trades
        catch_up_start = _previous_month_start_ms(now_ms)

        sym_arr = master["symbol"].to_numpy(dtype=str)
        open_time_arr = master["open_time"].values
        close_time_arr = master["close_time"].values
        open_arr = master["open"].values
        high_arr = master["high"].values
        low_arr = master["low"].values
        close_arr = master["close"].values

        open_trades: dict[str, LiveTrade] = {}
        cooldown_until: dict[str, int] = {}
        n_signals = 0
        n_trades_opened = 0
        n_trades_closed = 0

        # Find first index at or after the catch-up start
        start_idx = 0
        for i in range(len(master)):
            if int(open_time_arr[i]) >= catch_up_start:
                start_idx = i
                break
        else:
            return  # no candles to catch up

        for i in range(start_idx, len(master)):
            sym = str(sym_arr[i])
            ot = int(open_time_arr[i])
            ct = int(close_time_arr[i])

            if ct > now_ms:
                break

            # Current month: full trade lifecycle (mirrors backtest.py:217-305)

            # (a) Check open trade for SL/TP/timeout
            if sym in open_trades:
                order = trade_to_order(open_trades[sym])
                result = check_order(
                    order,
                    ot,
                    float(open_arr[i]),
                    float(high_arr[i]),
                    float(low_arr[i]),
                    ct,
                    self.config.fee_pct,
                )
                if result is not None:
                    trade = open_trades.pop(sym)
                    trade.status = "closed"
                    trade.exit_price = result.exit_price
                    trade.exit_time = result.close_time
                    trade.exit_reason = result.exit_reason
                    self._state.upsert_trade(trade)
                    self._logger.log_close(trade)
                    self._record_trade_close_for_vt(trade)
                    n_trades_closed += 1
                    # Match backtest.py:239-243 exactly: use result.close_time
                    # (not current candle ct). For timeouts, result.close_time
                    # is the candle's open_time, not close_time — an 8h difference
                    # for 8h candles that shifts the next eligible trade.
                    if self.config.cooldown_candles > 0:
                        cooldown_until[sym] = (
                            result.close_time
                            + self.config.cooldown_candles * self._candle_duration_ms
                        )

            # (b) Get signal
            sig = runner.strategy.get_signal(sym, ot)
            if sig.direction != 0 and sig.weight > 0:
                n_signals += 1
                if sym not in open_trades and ot >= cooldown_until.get(sym, 0):
                    entry_price = float(close_arr[i])

                    vt_scale = 1.0
                    if self.config.vol_targeting:
                        vt_scale = compute_vt_scale(self._vt_daily_pnl, sym, ct, self.config)

                    sl, tp = compute_sl_tp(sig, entry_price, self.config)
                    trade = LiveTrade(
                        model_name=runner.model_config.name,
                        symbol=sym,
                        direction=sig.direction,
                        entry_price=entry_price,
                        amount_usd=vt_scale * self.config.max_amount_usd,
                        weight_factor=vt_scale,
                        stop_loss_price=sl,
                        take_profit_price=tp,
                        open_time=ct,
                        timeout_time=ct + self.config.timeout_minutes * 60 * 1000,
                        signal_time=ot,
                        entry_order_id=f"CATCHUP-{_new_id()[:8]}",
                        sl_order_id=f"CATCHUP-{_new_id()[:8]}",
                        tp_order_id=f"CATCHUP-{_new_id()[:8]}",
                    )
                    self._state.upsert_trade(trade)
                    self._logger.log_open(trade)
                    open_trades[sym] = trade
                    n_trades_opened += 1

        # Persist last processed candle per symbol
        for sym in runner.model_config.symbols:
            sym_mask = sym_arr == sym
            sym_cts = close_time_arr[sym_mask]
            valid = sym_cts[sym_cts <= now_ms]
            if len(valid) > 0:
                last_ot = int(open_time_arr[sym_mask][len(valid) - 1])
                self._state.set_state(f"last_processed_{sym}", str(last_ot))

        # Persist any still-open trades
        for trade in open_trades.values():
            self._state.upsert_trade(trade)

        n_open = len(open_trades)
        print(
            f"[live] Model {runner.model_config.name} catch-up: "
            f"{n_signals} signals, {n_trades_opened} opened, "
            f"{n_trades_closed} closed, {n_open} still open"
        )

    def _tick(self) -> None:
        now_ms = int(time.time() * 1000)

        # 1. Check timeouts
        for trade in self._order_mgr.check_timeouts(now_ms):
            self._handle_trade_close(trade)

        # 2. Check exchange exits (real mode)
        if not self.config.dry_run:
            for trade in self._order_mgr.check_exchange_exits():
                self._handle_trade_close(trade)

        # 3. Detect new candles
        t_detect_start = time.monotonic()
        new_candles: dict[str, Kline] = {}
        for symbol in self._all_symbols:
            last_str = self._state.get_state(f"last_processed_{symbol}")
            last_ot = int(last_str) if last_str else None
            candle = detect_new_candle(self._read_client, symbol, self.config.interval, last_ot)
            if candle is not None:
                new_candles[symbol] = candle
        t_detect = time.monotonic() - t_detect_start

        if not new_candles:
            return

        t_tick_start = time.monotonic()
        print(
            f"[live] New candle(s): {', '.join(new_candles.keys())} "
            f"(detect={t_detect * 1000:.0f}ms)"
        )

        # 3b. Dry-run: check open trades for SL/TP/timeout against new candle OHLC
        if self.config.dry_run:
            for trade in self._state.get_open_trades():
                if trade.symbol not in new_candles:
                    continue
                candle = new_candles[trade.symbol]
                reason = self._order_mgr.check_dry_run_exit(
                    trade,
                    candle.open_time,
                    float(candle.open),
                    float(candle.high),
                    float(candle.low),
                    candle.close_time,
                )
                if reason:
                    updated = self._state.get_trade(trade.id)
                    if updated:
                        self._handle_trade_close(updated)

        # 4. Feature pipeline: fetch klines to CSV, regenerate features
        new_syms = list(new_candles.keys())
        t_fetch_start = time.monotonic()
        refresh_klines(self._fetch_client, new_syms, self.config.interval, self.config.data_dir)
        t_fetch = time.monotonic() - t_fetch_start

        t_feat_start = time.monotonic()
        refresh_features(
            new_syms,
            self.config.interval,
            str(self.config.data_dir),
            str(self.config.features_dir),
            list(self.config.feature_groups),
        )
        t_feat = time.monotonic() - t_feat_start
        print(
            f"[live] Pipeline: fetch_klines={t_fetch * 1000:.0f}ms "
            f"refresh_features={t_feat * 1000:.0f}ms"
        )

        # 5. Run each model
        for runner in self._runners:
            model_syms = [s for s in runner.model_config.symbols if s in new_candles]
            if not model_syms:
                continue

            t_master_start = time.monotonic()
            master = build_master(
                list(runner.model_config.symbols),
                self.config.interval,
                self.config.data_dir,
            )
            t_master = time.monotonic() - t_master_start
            if master.empty:
                continue

            # Only call compute_features (which resets the trained model) when
            # the calendar month actually changes. On same-month ticks, patch
            # the strategy's _month_features with the new candle's features.
            new_candle_month = _epoch_ms_to_month(
                next(iter(new_candles[s].open_time for s in model_syms))
            )
            t_warmup_start = time.monotonic()
            if runner.strategy._current_month != new_candle_month:
                runner.warmup(master)
                t_warmup_label = "compute_features"
            else:
                # Same month — add new candle's features to the dict and refresh
                # master reference. No retraining.
                runner.update_master(master)
                self._patch_month_features(runner, model_syms, new_candles, master)
                t_warmup_label = "patch_features"
            t_warmup = time.monotonic() - t_warmup_start

            candle_times = {s: new_candles[s].open_time for s in model_syms}
            t_signal_start = time.monotonic()
            signals = runner.get_signals(candle_times)
            t_signal = time.monotonic() - t_signal_start
            print(
                f"[live]   Model {runner.model_config.name}: "
                f"build_master={t_master * 1000:.0f}ms "
                f"{t_warmup_label}={t_warmup * 1000:.0f}ms "
                f"get_signal={t_signal * 1000:.0f}ms"
            )

            for symbol, sig in signals.items():
                if sig.direction == 0 or sig.weight <= 0:
                    continue

                open_trades = self._state.get_open_trades(model_name=runner.model_config.name)
                open_syms = {t.symbol for t in open_trades}
                if symbol in open_syms:
                    continue

                cooldown_key = f"cooldown_{runner.model_config.name}_{symbol}"
                cooldown_str = self._state.get_state(cooldown_key)
                if cooldown_str and now_ms < int(cooldown_str):
                    continue

                # FIX 2: entry price from master DataFrame (same source as backtest)
                candle_ot = new_candles[symbol].open_time
                entry_price = runner.get_close_price(symbol, candle_ot)
                if entry_price is None:
                    print(f"[live] WARNING: no close price for {symbol} at {candle_ot}")
                    continue

                # Get close_time from master too for consistency
                row = master[(master["symbol"] == symbol) & (master["open_time"] == candle_ot)]
                candle_close_time = int(row["close_time"].iloc[0])

                # FIX 1: vol targeting — same as backtest.py:293-296
                vt_scale = 1.0
                if self.config.vol_targeting:
                    vt_scale = compute_vt_scale(
                        self._vt_daily_pnl, symbol, candle_close_time, self.config
                    )

                trade = self._order_mgr.open_trade(
                    model_name=runner.model_config.name,
                    symbol=symbol,
                    signal=sig,
                    entry_price=entry_price,
                    candle_close_time=candle_close_time,
                    candle_open_time=candle_ot,
                    weight_factor=vt_scale,
                )
                self._logger.log_open(trade)

                if self.config.dry_run:
                    self._order_mgr.check_dry_run_exit(
                        trade,
                        candle_ot,
                        float(row["open"].iloc[0]),
                        float(row["high"].iloc[0]),
                        float(row["low"].iloc[0]),
                        candle_close_time,
                    )

        # 6. Mark processed
        for symbol, candle in new_candles.items():
            self._state.set_state(f"last_processed_{symbol}", str(candle.open_time))

        t_total = time.monotonic() - t_tick_start
        print(f"[live] Tick complete: total={t_total * 1000:.0f}ms (excl. detect)")

    def _shutdown(self) -> None:
        print("[live] Shutting down... exchange SL/TP orders remain active.")
        self._state.close()
        if self._auth_client:
            self._auth_client.close()

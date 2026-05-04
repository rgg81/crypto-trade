"""Live trading engine — orchestrates 3 independent LightGBM models.

Mirrors run_baseline_v152.py: each ModelRunner manages one LightGBM model
with its own symbol set and ATR config. The LiveEngine runs the shared
poll loop, feature pipeline, and order management.
"""

from __future__ import annotations

import datetime
import signal
import sqlite3
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
    refresh_features_by_track,
    refresh_klines,
)
from crypto_trade.live.models import (
    BASELINE_FEATURE_COLUMNS,
    LiveConfig,
    LiveTrade,
    ModelConfig,
    _new_id,
    is_paper_trade,
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


def _compute_catch_up_start_ms(now_ms: int, lookback_days: int | None) -> int:
    """Return the catch-up start time as epoch ms.

    lookback_days=N (default 90 in LiveConfig) replays the trailing N days,
    long enough to rebuild VT's 45-day rolling window plus buffer.
    lookback_days=None preserves the legacy previous-calendar-month
    behavior — kept as an explicit opt-out for legacy scripts.
    """
    if lookback_days is None:
        return _previous_month_start_ms(now_ms)
    return now_ms - lookback_days * 86_400_000


class ModelRunner:
    """Manages one LightGBM model (e.g., Model A for BTC/ETH)."""

    def __init__(self, model_config: ModelConfig, live_config: LiveConfig) -> None:
        self.model_config = model_config
        # Resolve per-model overrides; fall back to LiveConfig when None.
        self.feature_columns: tuple[str, ...] = (
            model_config.feature_columns
            if model_config.feature_columns is not None
            else BASELINE_FEATURE_COLUMNS
        )
        self.features_dir = (
            model_config.features_dir
            if model_config.features_dir is not None
            else live_config.features_dir
        )
        self.cooldown_candles: int = (
            model_config.cooldown_candles
            if model_config.cooldown_candles is not None
            else live_config.cooldown_candles
        )
        self.vol_targeting: bool = (
            model_config.vol_targeting
            if model_config.vol_targeting is not None
            else live_config.vol_targeting
        )
        self.ensemble_seeds: tuple[int, ...] = (
            model_config.ensemble_seeds
            if model_config.ensemble_seeds is not None
            else live_config.ensemble_seeds
        )
        atr_column_kwarg: dict[str, str] = {}
        if model_config.atr_column is not None:
            atr_column_kwarg["atr_column"] = model_config.atr_column

        inner = LightGbmStrategy(
            training_months=live_config.training_months,
            n_trials=live_config.n_trials,
            cv_splits=live_config.cv_splits,
            label_tp_pct=live_config.take_profit_pct,
            label_sl_pct=live_config.stop_loss_pct,
            label_timeout_minutes=live_config.timeout_minutes,
            fee_pct=live_config.fee_pct,
            features_dir=str(self.features_dir),
            verbose=1,
            atr_tp_multiplier=model_config.atr_tp_multiplier,
            atr_sl_multiplier=model_config.atr_sl_multiplier,
            use_atr_labeling=model_config.use_atr_labeling,
            ensemble_seeds=list(self.ensemble_seeds),
            feature_columns=list(self.feature_columns),
            ood_enabled=model_config.ood_enabled,
            ood_features=(list(model_config.ood_features) if model_config.ood_enabled else None),
            ood_cutoff_pct=model_config.ood_cutoff_pct,
            **atr_column_kwarg,
        )
        # _inner_strategy is the bare LightGbmStrategy regardless of wrapping;
        # self.strategy may be wrapped in RiskV2Wrapper for v2 models.
        self._inner_strategy = inner
        if model_config.risk_wrapper == "v2":
            if model_config.risk_v2_config is None:
                raise ValueError(
                    f"ModelConfig {model_config.name}: risk_wrapper='v2' "
                    "requires risk_v2_config (got None)"
                )
            from crypto_trade.strategies.ml.risk_v2 import RiskV2Wrapper

            self.strategy = RiskV2Wrapper(inner, model_config.risk_v2_config)
        else:
            self.strategy = inner
        self._master: pd.DataFrame | None = None

    @property
    def inner_strategy(self):
        """The underlying LightGbmStrategy regardless of wrapping (used by patcher)."""
        return self._inner_strategy

    @property
    def inner_atr_column(self) -> str:
        """ATR column name on the inner strategy (used by tests + patcher)."""
        return self._inner_strategy.atr_column

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
        auth_base_url: str | None = None,
    ) -> None:
        self.config = config
        self._running = True
        self._all_symbols = config.all_symbols
        self._candle_duration_ms = _INTERVAL_MS.get(config.interval, 28_800_000)

        # auth_base_url splits signed traffic (orders, positions, leverage)
        # away from kline traffic. None ⇒ same host as klines (preserves the
        # pre-testnet single-URL behavior). The testnet flow passes
        # auth_base_url="https://testnet.binancefuture.com" while leaving
        # base_url on production so klines stay on the full-history feed.
        resolved_auth_url = auth_base_url if auth_base_url is not None else base_url

        # Use limit=2 for candle polling. Klines always target base_url
        # (production); testnet kline history is too short / gappy for
        # the 90-day catch-up window.
        self._read_client = BinanceClient(base_url=base_url, limit=2, rate_limit_pause=0.25)
        self._auth_client: AuthenticatedBinanceClient | None = None
        if not config.dry_run and api_key:
            self._auth_client = AuthenticatedBinanceClient(
                api_key=api_key,
                api_secret=api_secret,
                base_url=resolved_auth_url,
            )

        # DB path resolution: testnet > dry_run > config.db_path. Each mode
        # gets its own file so testnet trades never mix with live.db, and
        # dry_run trades never mix with testnet.db.
        if config.testnet:
            db_path = config.data_dir / "testnet.db"
        elif config.dry_run:
            db_path = config.data_dir / "dry_run.db"
        else:
            db_path = config.db_path
        self._state = StateStore(db_path)

        # Per-symbol order constraints from /fapi/v1/exchangeInfo:
        #   - quantityPrecision (decimal places) + LOT_SIZE.stepSize (increment)
        #   - PRICE_FILTER.tickSize (price increment — what Binance actually
        #     validates; pricePrecision alone is insufficient, e.g. NEAR has
        #     pricePrecision=4 but tickSize=0.0010, so 1.3122 is rejected).
        # Without these rounding rules, the API returns 400 Bad Request.
        qty_precision: dict[str, int] = {}
        tick_size: dict[str, float] = {}
        if self._auth_client is not None:
            try:
                info = self._auth_client.get_exchange_info()
                for sym_info in info.get("symbols", []):
                    qty_precision[sym_info["symbol"]] = int(sym_info["quantityPrecision"])
                    for f in sym_info.get("filters", []):
                        if f.get("filterType") == "PRICE_FILTER":
                            tick_size[sym_info["symbol"]] = float(f["tickSize"])
                            break
                print(
                    f"[live] Loaded quantityPrecision + tickSize for "
                    f"{len(qty_precision)} symbols from /fapi/v1/exchangeInfo"
                )
            except Exception as exc:
                print(f"[live] WARNING: could not load exchangeInfo: {exc}")

        self._order_mgr = OrderManager(
            config,
            self._state,
            self._auth_client,
            quantity_precision=qty_precision,
            tick_size=tick_size,
        )

        # Trade-log filename mirrors the DB-path branch above.
        if config.testnet:
            log_name = "testnet_trades.csv"
            decision_log_name = "testnet_decisions.jsonl"
        elif config.dry_run:
            log_name = "dry_run_trades.csv"
            decision_log_name = "dry_run_decisions.jsonl"
        else:
            log_name = "live_trades.csv"
            decision_log_name = "live_decisions.jsonl"
        self._logger = TradeLogger(config.data_dir / log_name, config.fee_pct, config.dry_run)

        from crypto_trade import decision_log

        decision_log.configure(config.data_dir / decision_log_name)

        self._runners = [ModelRunner(mc, config) for mc in config.models]

        # Separate client for kline fetches (higher limit for initial setup)
        self._fetch_client = BinanceClient(base_url=base_url, limit=1500, rate_limit_pause=0.25)

        # Per-symbol daily PnL tracking for vol targeting — same as backtest.py:186
        # symbol -> {YYYY-MM-DD -> sum of net_pnl_pct that closed on that day}
        self._vt_daily_pnl: dict[str, dict[str, float]] = {}

        # Iter 173: R1 consecutive-SL cool-down state (per-symbol).
        # symbol -> current consecutive SL count (reset on non-SL close or when
        # the streak hits K, at which point risk_cooldown_until[symbol] is armed).
        self._sl_streak: dict[str, int] = {}
        # symbol -> earliest open_time at which a new trade may open again.
        self._risk_cooldown_until: dict[str, int] = {}

        # Iter 176: R2 drawdown-triggered position scaling state (per-model).
        # model_name -> cumulative sum of weighted_pnl over that model's closes.
        self._cum_weighted_pnl: dict[str, float] = {mc.name: 0.0 for mc in config.models}
        # model_name -> running peak of cum_weighted_pnl.
        self._peak_weighted_pnl: dict[str, float] = {mc.name: 0.0 for mc in config.models}

        # Map symbol → model_name for R2 updates on trade close.
        self._symbol_to_model: dict[str, str] = {
            s: mc.name for mc in config.models for s in mc.symbols
        }

        # Guard 1: v2 ModelConfigs must not trade v1 baseline symbols.
        from crypto_trade.live.models import V2_EXCLUDED_SYMBOLS as _V2_EXCLUDED

        for mc in config.models:
            if mc.risk_wrapper == "v2":
                overlap = set(mc.symbols) & set(_V2_EXCLUDED)
                if overlap:
                    raise ValueError(
                        f"ModelConfig {mc.name!r}: risk_wrapper='v2' cannot trade "
                        f"V2_EXCLUDED_SYMBOLS {sorted(overlap)}"
                    )

        # Guard 2: symbols must be disjoint across models — R1 and VT state are
        # keyed by symbol alone, so any overlap would silently corrupt state.
        seen_owner: dict[str, str] = {}
        for mc in config.models:
            for s in mc.symbols:
                if s in seen_owner:
                    raise ValueError(
                        f"overlapping symbols across models: {s!r} appears in "
                        f"{seen_owner[s]!r} and {mc.name!r}"
                    )
                seen_owner[s] = mc.name

        # iter-v2/019: BTC trend filter at signal time (v2 only). Loaded once
        # at startup to mirror run_baseline_v2.py's load_btc_klines_for_filter.
        self._btc_filter_cfg: BtcTrendFilterConfig | None = None
        self._btc_filter_times: np.ndarray | None = None
        self._btc_filter_closes: np.ndarray | None = None
        if any(mc.risk_wrapper == "v2" for mc in config.models):
            from crypto_trade.strategies.ml.risk_v2 import (
                BtcTrendFilterConfig,
                load_btc_klines_for_filter,
            )

            self._btc_filter_cfg = BtcTrendFilterConfig()  # iter-v2/069 defaults
            try:
                self._btc_filter_times, self._btc_filter_closes = load_btc_klines_for_filter(
                    csv_path=str(self.config.data_dir / "BTCUSDT" / "8h.csv"),
                )
                print(
                    f"[live] BTC trend filter loaded: {len(self._btc_filter_times)} 8h bars "
                    f"(lookback={self._btc_filter_cfg.lookback_bars}, "
                    f"threshold=±{self._btc_filter_cfg.threshold_pct:.1f}%)"
                )
            except FileNotFoundError:
                print(
                    "[live] WARNING: BTC trend filter requested by v2 model but "
                    f"BTC CSV not found at {self.config.data_dir / 'BTCUSDT' / '8h.csv'}; "
                    "v2 signals will run without the filter."
                )
                self._btc_filter_cfg = None
        # Telemetry: count BTC-killed v2 signals across the engine's lifetime.
        self._btc_killed_count: int = 0

    def _refresh_groups(self, symbols_subset: list[str]) -> list[tuple[tuple[str, ...], Path, str]]:
        """Group ``symbols_subset`` by track (v1/v2) for refresh_features_by_track.

        A symbol's track is determined by its owning runner's risk_wrapper:
        v2-wrapped runners use ``data/features_v2`` (or whatever the runner
        resolved via per-model override), v1 runners use ``data/features``.
        """
        v1_syms: list[str] = []
        v2_syms: list[str] = []
        v1_dir: Path | None = None
        v2_dir: Path | None = None
        for runner in self._runners:
            track = "v2" if runner.model_config.risk_wrapper == "v2" else "v1"
            for s in runner.model_config.symbols:
                if s not in symbols_subset:
                    continue
                if track == "v2":
                    v2_syms.append(s)
                    v2_dir = runner.features_dir
                else:
                    v1_syms.append(s)
                    v1_dir = runner.features_dir
        groups: list[tuple[tuple[str, ...], Path, str]] = []
        if v1_syms and v1_dir is not None:
            groups.append((tuple(v1_syms), v1_dir, "v1"))
        if v2_syms and v2_dir is not None:
            groups.append((tuple(v2_syms), v2_dir, "v2"))
        return groups

    def catch_up_only(self) -> None:
        """Run the same setup pipeline as ``run()`` and exit before the poll loop.

        Used by parity tests to drive the engine deterministically through
        historical data: reconcile open orders, rebuild risk + VT state from
        closed trades in the DB, train the strategies, replay the most recent
        month of candles to populate trade state. Returns once `_catch_up()`
        completes — does NOT call `_tick()` or sleep.
        """
        self._print_banner()
        self._reconcile()
        self._rebuild_vt_history()
        self._rebuild_risk_state()
        self._initial_setup()
        self._catch_up()

    def run(self) -> None:
        """Main entry point — runs until SIGINT/SIGTERM."""
        self._setup_signal_handlers()
        self._print_banner()
        self._reconcile()
        self._rebuild_vt_history()
        self._rebuild_risk_state()
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
        if self.config.testnet:
            mode = "LIVE — TESTNET"
        elif self.config.dry_run:
            mode = "DRY-RUN"
        else:
            mode = "LIVE"
        print(f"[live] Starting baseline v186 [{mode}]")
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

    def _rebuild_risk_state(self) -> None:
        """Rebuild R1/R2 state from closed trades in DB.

        R1: per-symbol consecutive-SL streak + armed cooldown.
        R2: per-model cumulative weighted PnL + running peak.

        Replays closed trades in chronological order exactly like the backtest.
        """
        self._sl_streak = {}
        self._risk_cooldown_until = {}
        self._cum_weighted_pnl = {mc.name: 0.0 for mc in self.config.models}
        self._peak_weighted_pnl = {mc.name: 0.0 for mc in self.config.models}

        # Look up R1 config per symbol (None ⇒ R1 disabled for that symbol).
        r1_config: dict[str, tuple[int, int]] = {}
        r2_models: set[str] = set()
        for mc in self.config.models:
            if mc.risk_consecutive_sl_limit is not None:
                for sym in mc.symbols:
                    r1_config[sym] = (
                        mc.risk_consecutive_sl_limit,
                        mc.risk_consecutive_sl_cooldown_candles,
                    )
            if mc.risk_drawdown_scale_enabled:
                r2_models.add(mc.name)

        closed = [
            t
            for t in self._state.get_all_trades()
            if t.status == "closed" and t.exit_time is not None and t.exit_reason is not None
        ]
        closed.sort(key=lambda t: t.exit_time or 0)

        n_r1_updates = 0
        for trade in closed:
            sym = trade.symbol
            model_name = trade.model_name
            result = to_trade_result(trade, self.config.fee_pct)
            if result is None:
                continue
            # R1 — update streak and cooldown
            if sym in r1_config:
                k_threshold, cooldown_candles = r1_config[sym]
                if result.exit_reason == "stop_loss":
                    self._sl_streak[sym] = self._sl_streak.get(sym, 0) + 1
                    if self._sl_streak[sym] >= k_threshold:
                        self._risk_cooldown_until[sym] = (
                            result.close_time + cooldown_candles * self._candle_duration_ms
                        )
                        self._sl_streak[sym] = 0
                        n_r1_updates += 1
                else:
                    self._sl_streak[sym] = 0
            # R2 — accumulate weighted PnL per model and update peak
            if model_name in r2_models:
                self._cum_weighted_pnl[model_name] = (
                    self._cum_weighted_pnl.get(model_name, 0.0) + result.weighted_pnl
                )
                if self._cum_weighted_pnl[model_name] > self._peak_weighted_pnl.get(
                    model_name, 0.0
                ):
                    self._peak_weighted_pnl[model_name] = self._cum_weighted_pnl[model_name]

        if n_r1_updates > 0 or any(v != 0.0 for v in self._cum_weighted_pnl.values()):
            print(
                f"[live] Rebuilt risk state: {n_r1_updates} R1 cooldowns armed, "
                f"R2 cum PnL by model = "
                f"{ {k: round(v, 2) for k, v in self._cum_weighted_pnl.items()} }"
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

    def _record_trade_close_for_risk(self, trade: LiveTrade) -> None:
        """Update R1 streak / R2 accumulators on a trade close.

        Mirrors backtest.py:263-280 exactly.
        """
        result = to_trade_result(trade, self.config.fee_pct)
        if result is None:
            return

        # Find R1 config for this symbol
        r1_limit: int | None = None
        r1_cooldown_candles = 0
        r2_enabled = False
        for mc in self.config.models:
            if trade.model_name == mc.name:
                r1_limit = mc.risk_consecutive_sl_limit
                r1_cooldown_candles = mc.risk_consecutive_sl_cooldown_candles
                r2_enabled = mc.risk_drawdown_scale_enabled
                break

        sym = trade.symbol
        if r1_limit is not None and self._candle_duration_ms > 0:
            if result.exit_reason == "stop_loss":
                self._sl_streak[sym] = self._sl_streak.get(sym, 0) + 1
                if self._sl_streak[sym] >= r1_limit:
                    self._risk_cooldown_until[sym] = (
                        result.close_time + r1_cooldown_candles * self._candle_duration_ms
                    )
                    self._sl_streak[sym] = 0
            else:
                self._sl_streak[sym] = 0

        if r2_enabled:
            self._cum_weighted_pnl[trade.model_name] = (
                self._cum_weighted_pnl.get(trade.model_name, 0.0) + result.weighted_pnl
            )
            if self._cum_weighted_pnl[trade.model_name] > self._peak_weighted_pnl.get(
                trade.model_name, 0.0
            ):
                self._peak_weighted_pnl[trade.model_name] = self._cum_weighted_pnl[trade.model_name]

    def _r2_scale_for(self, model_name: str) -> float:
        """Compute R2 drawdown scale factor for the given model (1.0 = no scaling).

        Mirrors backtest.py:358-368 exactly.
        """
        mc = next((m for m in self.config.models if m.name == model_name), None)
        if mc is None or not mc.risk_drawdown_scale_enabled:
            return 1.0
        cum = self._cum_weighted_pnl.get(model_name, 0.0)
        peak = self._peak_weighted_pnl.get(model_name, 0.0)
        dd_pct = max(0.0, peak - cum)
        trigger = float(mc.risk_drawdown_trigger_pct)
        anchor = float(mc.risk_drawdown_scale_anchor_pct)
        floor = float(mc.risk_drawdown_scale_floor)
        if dd_pct <= trigger or anchor <= trigger:
            return 1.0
        span = min(1.0, (dd_pct - trigger) / (anchor - trigger))
        return 1.0 - span * (1.0 - floor)

    def _set_cooldown(self, model_name: str, symbol: str, close_time: int) -> None:
        """Set cooldown after a trade closes — same as backtest.py:238-242.

        Uses the OWNING model's cooldown_candles, not LiveConfig's, so v2
        models (cooldown_candles=4) get a different gate than v1 (default 2).
        """
        cooldown_candles = self._cooldown_for(model_name)
        if cooldown_candles <= 0:
            return
        cooldown_until = close_time + cooldown_candles * self._candle_duration_ms
        self._state.set_state(f"cooldown_{model_name}_{symbol}", str(cooldown_until))

    def _cooldown_for(self, model_name: str) -> int:
        """Resolve per-model cooldown_candles via the matching runner; fall back to LiveConfig."""
        for runner in self._runners:
            if runner.model_config.name == model_name:
                return runner.cooldown_candles
        return self.config.cooldown_candles

    def _handle_trade_close(self, trade: LiveTrade) -> None:
        """Common handler when a trade closes: log, record VT, record risk, set cooldown."""
        updated = self._state.get_trade(trade.id)
        if updated is None:
            return
        self._logger.log_close(updated)
        self._record_trade_close_for_vt(updated)
        self._record_trade_close_for_risk(updated)
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
        # Always reach the bare LightGbmStrategy — RiskV2Wrapper (when present)
        # exposes the same Strategy Protocol but doesn't carry the LGBM internals
        # (_month_features, _selected_cols, atr_column, …) that the patcher mutates.
        strategy = runner.inner_strategy
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
        refresh_features_by_track(
            self._refresh_groups(all_symbols),
            interval=self.config.interval,
            data_dir=str(self.config.data_dir),
            feature_groups=tuple(self.config.feature_groups),
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
        catch_up_start = _compute_catch_up_start_ms(now_ms, self.config.catch_up_lookback_days)

        sym_arr = master["symbol"].to_numpy(dtype=str)
        open_time_arr = master["open_time"].values
        close_time_arr = master["close_time"].values
        open_arr = master["open"].values
        high_arr = master["high"].values
        low_arr = master["low"].values
        close_arr = master["close"].values

        # Pre-load paper open trades (SEEDED, CATCHUP-, DRY-, None) for this
        # model so the catch-up loop's open-position guard sees them. Each
        # SEEDED trade carries full intended-exit info (exit_time, exit_price,
        # exit_reason) and is closed deterministically below.
        #
        # Real numeric-ID trades (left over from a prior --live session) are
        # explicitly excluded — they belong to reconciler + poll-loop. Pre-
        # loading them would let catch-up's check_order simulate a fake exit
        # and falsely close DB rows whose Binance positions are still open.
        open_trades: dict[str, LiveTrade] = {}
        for seeded in self._state.get_open_trades(model_name=runner.model_config.name):
            if seeded.symbol not in runner.model_config.symbols:
                continue
            if not is_paper_trade(seeded):
                continue
            open_trades[seeded.symbol] = seeded
        # Pre-load both dicts from engine_state so the seeder's boundary keys
        # and post-trade cooldown keys are honored from the very first candle.
        cooldown_until: dict[str, int] = {}
        seeded_through: dict[str, int] = {}
        for sym in runner.model_config.symbols:
            cd_raw = self._state.get_state(f"cooldown_{runner.model_config.name}_{sym}")
            if cd_raw:
                cooldown_until[sym] = int(cd_raw)
            sb_raw = self._state.get_state(f"seeded_through_{runner.model_config.name}_{sym}")
            if sb_raw:
                seeded_through[sym] = int(sb_raw)
        if seeded_through or cooldown_until:
            print(
                f"[live] Model {runner.model_config.name} catch-up boundary: "
                f"{len(seeded_through)} seeded keys, {len(cooldown_until)} cooldown keys"
            )

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

            # (a) Check open trade for SL/TP/timeout. SEEDED carry-over and
            # CATCHUP-* paper trades both flow through the same check_order
            # path now that the seeder writes real SL/TP/timeout from the
            # backtest CSV. SEEDED trades carry a real open_time which may
            # be inside the catch-up window — skip check_order for candles
            # before that open_time so the trade's SL/TP is not evaluated
            # against ancient candles. Signal evaluation (step b) still
            # runs unconditionally — it has its own seeded_through guard.
            if sym in open_trades and ot >= open_trades[sym].open_time:
                trade = open_trades[sym]
                order = trade_to_order(trade)
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
                    self._record_trade_close_for_risk(trade)
                    n_trades_closed += 1
                    # Match backtest.py:239-243: use result.close_time (not ct).
                    # For timeouts, result.close_time = candle open_time.
                    if runner.cooldown_candles > 0:
                        cooldown_until[sym] = (
                            result.close_time
                            + runner.cooldown_candles * self._candle_duration_ms
                        )

            # (b) Get signal
            sig = runner.strategy.get_signal(sym, ot)
            if sig.direction != 0 and sig.weight > 0:
                n_signals += 1
                if (
                    sym not in open_trades
                    and ot >= cooldown_until.get(sym, 0)
                    and ot >= self._risk_cooldown_until.get(sym, 0)
                    and ot > seeded_through.get(sym, 0)
                ):
                    entry_price = float(close_arr[i])

                    # Per-model VT — v2 sets vol_targeting=False so vt_scale stays 1.0.
                    vt_scale = 1.0
                    if runner.vol_targeting:
                        vt_scale = compute_vt_scale(self._vt_daily_pnl, sym, ct, self.config)
                    # R2 drawdown scaling applied on top of VT
                    vt_scale *= self._r2_scale_for(runner.model_config.name)

                    # Match backtest.py:567-575: when VT is enabled, weight_factor=vt_scale.
                    # When VT is off, weight_factor includes the strategy's signal.weight
                    # (the wrapper's _vol_scale uses this to pass through position sizing).
                    if runner.vol_targeting:
                        weight_factor = vt_scale
                    else:
                        weight_factor = (sig.weight / 100.0) * vt_scale

                    sl, tp = compute_sl_tp(sig, entry_price, self.config)
                    trade = LiveTrade(
                        model_name=runner.model_config.name,
                        symbol=sym,
                        direction=sig.direction,
                        entry_price=entry_price,
                        amount_usd=weight_factor * self.config.max_amount_usd,
                        weight_factor=weight_factor,
                        stop_loss_price=sl,
                        take_profit_price=tp,
                        open_time=ct,
                        timeout_time=ct + self.config.timeout_minutes * 60 * 1000,
                        signal_time=ot,
                        entry_order_id=f"CATCHUP-{_new_id()[:8]}",
                        sl_order_id=f"CATCHUP-{_new_id()[:8]}",
                        tp_order_id=f"CATCHUP-{_new_id()[:8]}",
                    )
                    try:
                        self._state.upsert_trade(trade)
                    except sqlite3.IntegrityError:
                        # Natural-key collision — keep the existing row (e.g. a
                        # SEEDED carry-over or stale CATCHUP-* from a prior run).
                        print(
                            f"[live] catch-up duplicate suppressed: "
                            f"model={runner.model_config.name} sym={sym} ot={ot}"
                        )
                        continue
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

        from crypto_trade import decision_log

        decision_log.log(
            {
                "kind": "tick_start",
                "now_ms": now_ms,
                "new_candles": {sym: c.open_time for sym, c in new_candles.items()},
            }
        )

        t_tick_start = time.monotonic()
        print(
            f"[live] New candle(s): {', '.join(new_candles.keys())} "
            f"(detect={t_detect * 1000:.0f}ms)"
        )

        # 3b. Candle-based exit check for paper trades. Real numeric-ID trades
        # are handled by check_exchange_exits (above) which polls Binance for
        # SL/TP fills. Paper trades (None / SEEDED / CATCHUP- / DRY-) have no
        # Binance counterpart, so we deterministically simulate SL/TP/timeout
        # against the new candle's OHLC — same logic as backtest.check_order.
        # In dry-run mode all trades are paper; in live mode this catches
        # seeded carry-overs and catch-up replay rows that would otherwise
        # only exit via check_timeouts (default 7 days) — a small SL/TP-hit
        # loss could compound until then.
        for trade in self._state.get_open_trades():
            if trade.symbol not in new_candles:
                continue
            if not is_paper_trade(trade):
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
        refresh_features_by_track(
            self._refresh_groups(new_syms),
            interval=self.config.interval,
            data_dir=str(self.config.data_dir),
            feature_groups=tuple(self.config.feature_groups),
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
            # _current_month lives on the inner LightGbmStrategy. v2 runners
            # wrap it in RiskV2Wrapper, so go through the inner_strategy property.
            if runner.inner_strategy._current_month != new_candle_month:
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

            from crypto_trade import decision_log

            for symbol, sig in signals.items():
                candle_ot_for_log = new_candles[symbol].open_time if symbol in new_candles else None
                if sig.direction == 0 or sig.weight <= 0:
                    decision_log.log(
                        {
                            "kind": "tick_decision",
                            "model": runner.model_config.name,
                            "symbol": symbol,
                            "ot": candle_ot_for_log,
                            "sig_direction": sig.direction,
                            "sig_weight": sig.weight,
                            "decision": "skipped:no_signal",
                        }
                    )
                    continue

                open_trades = self._state.get_open_trades(model_name=runner.model_config.name)
                open_syms = {t.symbol for t in open_trades}
                if symbol in open_syms:
                    decision_log.log(
                        {
                            "kind": "tick_decision",
                            "model": runner.model_config.name,
                            "symbol": symbol,
                            "ot": candle_ot_for_log,
                            "sig_direction": sig.direction,
                            "decision": "skipped:position_open",
                        }
                    )
                    continue

                cooldown_key = f"cooldown_{runner.model_config.name}_{symbol}"
                cooldown_str = self._state.get_state(cooldown_key)
                if cooldown_str and now_ms < int(cooldown_str):
                    decision_log.log(
                        {
                            "kind": "tick_decision",
                            "model": runner.model_config.name,
                            "symbol": symbol,
                            "ot": candle_ot_for_log,
                            "sig_direction": sig.direction,
                            "cooldown_until": int(cooldown_str),
                            "decision": "skipped:cooldown",
                        }
                    )
                    continue

                # FIX 2: entry price from master DataFrame (same source as backtest)
                candle_ot = new_candles[symbol].open_time
                # R1 consecutive-SL cool-down gate (iter 173) — keyed on
                # candle open_time to match backtest's gate semantics.
                if candle_ot < self._risk_cooldown_until.get(symbol, 0):
                    decision_log.log(
                        {
                            "kind": "tick_decision",
                            "model": runner.model_config.name,
                            "symbol": symbol,
                            "ot": candle_ot,
                            "sig_direction": sig.direction,
                            "risk_cooldown_until": int(self._risk_cooldown_until.get(symbol, 0)),
                            "decision": "skipped:r1_cooldown",
                        }
                    )
                    continue

                # iter-v2/019: BTC trend filter (v2 models only). Mirrors
                # run_baseline_v2.py's apply_btc_trend_filter post-hoc gate, but
                # at signal time so we never enter a position the backtest would
                # have killed. v1 signals are unaffected.
                if runner.model_config.risk_wrapper == "v2" and self._btc_filter_cfg is not None:
                    from crypto_trade.strategies.ml.risk_v2 import (
                        evaluate_btc_trend_filter_one_signal,
                    )

                    if evaluate_btc_trend_filter_one_signal(
                        self._btc_filter_times,
                        self._btc_filter_closes,
                        candle_ot,
                        sig.direction,
                        self._btc_filter_cfg,
                    ):
                        self._btc_killed_count += 1
                        print(
                            f"[live] BTC trend filter killed v2 signal: "
                            f"model={runner.model_config.name} symbol={symbol} "
                            f"direction={sig.direction} ot={candle_ot}"
                        )
                        decision_log.log(
                            {
                                "kind": "tick_decision",
                                "model": runner.model_config.name,
                                "symbol": symbol,
                                "ot": candle_ot,
                                "sig_direction": sig.direction,
                                "decision": "skipped:btc_trend_filter",
                            }
                        )
                        continue

                entry_price = runner.get_close_price(symbol, candle_ot)
                if entry_price is None:
                    print(f"[live] WARNING: no close price for {symbol} at {candle_ot}")
                    continue

                # Get close_time from master too for consistency
                row = master[(master["symbol"] == symbol) & (master["open_time"] == candle_ot)]
                candle_close_time = int(row["close_time"].iloc[0])

                # Vol targeting — per-model (v2 disables it; v1 keeps the
                # LiveConfig default).
                vt_scale = 1.0
                if runner.vol_targeting:
                    vt_scale = compute_vt_scale(
                        self._vt_daily_pnl, symbol, candle_close_time, self.config
                    )
                # R2 drawdown scaling (iter 176) applied on top of VT
                vt_scale *= self._r2_scale_for(runner.model_config.name)

                # Match backtest.py:567-575: when VT is enabled, weight_factor=vt_scale.
                # When VT is off (v2), include signal.weight/100 so the wrapper's
                # _vol_scale (which adjusts sig.weight) flows into the trade.
                if runner.vol_targeting:
                    weight_factor = vt_scale
                else:
                    weight_factor = (sig.weight / 100.0) * vt_scale

                trade = self._order_mgr.open_trade(
                    model_name=runner.model_config.name,
                    symbol=symbol,
                    signal=sig,
                    entry_price=entry_price,
                    candle_close_time=candle_close_time,
                    candle_open_time=candle_ot,
                    weight_factor=weight_factor,
                )
                self._logger.log_open(trade)
                decision_log.log(
                    {
                        "kind": "tick_decision",
                        "model": runner.model_config.name,
                        "symbol": symbol,
                        "ot": candle_ot,
                        "ct": candle_close_time,
                        "sig_direction": sig.direction,
                        "sig_weight": sig.weight,
                        "entry_price": float(entry_price),
                        "vt_scale": float(vt_scale),
                        "weight_factor": float(weight_factor),
                        "stop_loss_price": float(trade.stop_loss_price),
                        "take_profit_price": float(trade.take_profit_price),
                        "entry_order_id": trade.entry_order_id,
                        "decision": "opened",
                    }
                )

                # Same-candle SL/TP simulation for paper trades only. Real
                # numeric-ID trades from `--live` poll-loop have Binance SL/TP
                # orders placed already; their exits flow through
                # check_exchange_exits.
                if is_paper_trade(trade):
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

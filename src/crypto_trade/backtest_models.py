from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import pandas as pd


class Strategy(Protocol):
    def compute_features(self, master: pd.DataFrame) -> None:
        """Pre-compute features from master DF. Store internally."""
        ...

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        """Return signal for one candle. Reads from stored features."""
        ...

    def skip(self) -> None:
        """Advance internal position without computing a signal.

        Filters call this on the inner strategy when the candle is blocked,
        avoiding unnecessary computation while keeping ``_pos`` synchronized.
        """
        ...


@dataclass(frozen=True)
class Signal:
    direction: int  # 1=buy, -1=sell, 0=do nothing
    weight: int  # 0-100
    tp_pct: float | None = None  # optional dynamic take-profit %
    sl_pct: float | None = None  # optional dynamic stop-loss %
    # iter-v3/080: passive metadata field — M1 directional confidence scalar.
    # max(P(long), P(short)) from the inner-ensemble mean predict_proba.
    # No decision, barrier, gate, or model input ever reads this field.
    confidence: float | None = None


@dataclass(frozen=True)
class BacktestConfig:
    symbols: tuple[str, ...]
    interval: str
    max_amount_usd: float
    stop_loss_pct: float
    take_profit_pct: float
    timeout_minutes: int
    fee_pct: float = 0.1
    data_dir: Path = Path("data")
    start_time: int | None = None  # epoch ms, default=first row
    end_time: int | None = None  # epoch ms, default=last row
    cooldown_candles: int = 0  # candles to wait after a trade closes before re-entering
    # Per-symbol volatility targeting (iter 147): scale each trade by
    # target_vol / realized_vol of that symbol's past daily PnL.
    vol_targeting: bool = False
    vt_target_vol: float = 0.5
    vt_lookback_days: int = 30
    vt_min_scale: float = 0.5
    vt_max_scale: float = 2.0
    vt_min_history: int = 5  # minimum past daily returns required for scaling
    # Risk mitigation R1 (iter 173): consecutive-loss cool-down.
    # After K consecutive stop-loss closes for a symbol, suppress new
    # trades on that symbol for C candles. Defaults disable the filter.
    risk_consecutive_sl_limit: int | None = None  # K; None disables
    risk_consecutive_sl_cooldown_candles: int = 0  # C
    # Risk mitigation R2 (iter 175): drawdown-triggered position scaling.
    # When per-backtest cumulative weighted PnL drops more than
    # risk_drawdown_trigger_pct below its running peak, scale new trade
    # weight_factors by a linear factor between risk_drawdown_scale_floor
    # (at very deep drawdown) and 1.0 (at the trigger). Disabled when
    # risk_drawdown_scale_enabled is False.
    risk_drawdown_scale_enabled: bool = False
    risk_drawdown_trigger_pct: float = 10.0
    risk_drawdown_scale_floor: float = 0.33
    risk_drawdown_scale_anchor_pct: float = 30.0  # full floor reached at this DD
    # iter-v3/116: early-exit-on-no-confirmation exit primitive.
    # When enabled, a trade that has not reached no_confirm_threshold_price
    # (entry +/- trigger_atr * atr_distance in the favorable direction) within
    # the first no_confirm_k_candles candles is closed at candle K's close
    # (exit_reason = "no_confirm"). Default False preserves /059-canonical
    # byte-identical behavior for all prior iterations.
    enable_no_confirm_exit: bool = False
    no_confirm_trigger_atr: float = 0.50
    no_confirm_k_candles: int = 4
    # Risk mitigation R5 (iter-v1/010): per-symbol vol-target ceiling.
    # When enabled, caps weight_factor by min(1.0, risk_r5_vol_target_pct /
    # max(vol_natr_14, 0.01)). vol_natr_14 is read from per-symbol feature
    # parquets at backtest init. Applied AFTER R2 in the vt_scale pipeline.
    # Default disabled — restoring risk_r5_vol_target_enabled=False preserves
    # byte-identical behavior for all iterations through iter-v1/009.
    risk_r5_vol_target_enabled: bool = False
    risk_r5_vol_target_pct: float = 4.0
    # Risk mitigation R5-BINARY-KILL (iter-v1/011): entry-time NATR floor.
    # When enabled, skips entry entirely if vol_natr_14 at signal time is
    # strictly below risk_r5_kill_low_natr_min_pct. This is a state-discontinuous
    # entry filter — structurally orthogonal to /010's proportional-scaling subtype.
    # Evaluated BEFORE cooldown / vt_scale / R2 (pre-confidence-gate).
    # Safety: if NATR is unavailable (NaN / missing lookup key), entry proceeds.
    # Default disabled — preserves byte-identical behavior for all iterations
    # through iter-v1/010.
    risk_r5_kill_low_natr_enabled: bool = False
    risk_r5_kill_low_natr_min_pct: float = 2.0


@dataclass(frozen=True)
class Order:
    symbol: str
    direction: int
    entry_price: float
    amount_usd: float
    weight_factor: float
    stop_loss_price: float
    take_profit_price: float
    open_time: int
    timeout_time: int
    # iter-v3/080: passive metadata — carried from Signal.confidence.
    confidence: float | None = None
    # iter-v3/116: early-exit-on-no-confirmation primitive.
    # no_confirm_arm_time: close_time at end of K-candle observation window
    #   (open_time + no_confirm_k_candles * interval_ms). Zero when flag is off.
    # no_confirm_threshold_price: entry +/- trigger_atr * atr_distance in the
    #   favorable direction. Zero when flag is off. When a candle's high/low
    #   crosses this price before arm_time, the trade is marked confirmed and
    #   proceeds to normal TP/SL/timeout; if it does not cross by arm_time the
    #   trade exits at the candle's close with exit_reason="no_confirm".
    no_confirm_arm_time: int = 0
    no_confirm_threshold_price: float = 0.0


@dataclass(frozen=True)
class TradeResult:
    symbol: str
    direction: int
    entry_price: float
    exit_price: float
    weight_factor: float
    open_time: int
    close_time: int
    exit_reason: str  # "stop_loss" | "take_profit" | "timeout" | "end_of_data" | "no_confirm"
    pnl_pct: float
    fee_pct: float
    net_pnl_pct: float
    weighted_pnl: float
    # Entry-side risk parameters carried through so the live engine can
    # re-evaluate SEEDED open trades (exit_reason='end_of_data') against
    # fresh post-data-extent candles instead of force-closing them at the
    # backtest's last close.
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    timeout_time: int = 0
    # iter-v3/080: passive metadata — M1 directional confidence scalar.
    # Carried from Order.confidence. No decision path reads this field.
    confidence: float | None = None


@dataclass(frozen=True)
class DailyPnL:
    date: str  # "YYYY-MM-DD"
    avg_weighted_pnl: float
    trade_count: int
    trades: tuple[TradeResult, ...]


class BacktestResult(list):
    """List of TradeResult with extra backtest metadata.

    Extends ``list`` so all existing callers (len, indexing, iteration,
    equality) keep working.  The ``total_signals`` attribute records how
    many times the strategy fired (direction != 0, weight > 0), which may
    exceed ``len(self)`` when signals are skipped because an order is
    already open for that symbol.

    iter-v1/010 R5 IS/OOS split counters
    -------------------------------------
    r5_signals_is, r5_fires_is   : signal count and R5 fire count for
                                   candles with open_time < OOS_CUTOFF_MS.
    r5_signals_oos, r5_fires_oos : same for open_time >= OOS_CUTOFF_MS.
    All four default to 0 when R5 is disabled.

    iter-v1/011 R5-BINARY-KILL IS/OOS split counters
    -------------------------------------------------
    r5_kill_signals_is, r5_kill_fires_is   : signal count and binary-kill
                                            fire count for IS half.
    r5_kill_signals_oos, r5_kill_fires_oos : same for OOS half.
    All four default to 0 when R5-BINARY-KILL is disabled.
    """

    def __init__(
        self,
        trades: list[TradeResult],
        total_signals: int = 0,
        *,
        r5_signals_is: int = 0,
        r5_fires_is: int = 0,
        r5_signals_oos: int = 0,
        r5_fires_oos: int = 0,
        r5_kill_signals_is: int = 0,
        r5_kill_fires_is: int = 0,
        r5_kill_signals_oos: int = 0,
        r5_kill_fires_oos: int = 0,
    ):
        super().__init__(trades)
        self.total_signals = total_signals
        self.r5_signals_is = r5_signals_is
        self.r5_fires_is = r5_fires_is
        self.r5_signals_oos = r5_signals_oos
        self.r5_fires_oos = r5_fires_oos
        self.r5_kill_signals_is = r5_kill_signals_is
        self.r5_kill_fires_is = r5_kill_fires_is
        self.r5_kill_signals_oos = r5_kill_signals_oos
        self.r5_kill_fires_oos = r5_kill_fires_oos

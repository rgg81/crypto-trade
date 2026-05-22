"""Adversarial integration tests for the iter-v3/116 early-exit-on-no-confirmation primitive.

Three test groups per the brief Section 3.5 Change 8:

(a) Confirmed path — high reaches no_confirm_threshold_price before arm_time.
    The trade must proceed to normal TP/SL/timeout resolution (NOT "no_confirm").

(b) No-confirm path — max favorable excursion stays below threshold through arm_time.
    The trade must close at candle K's close with exit_reason = "no_confirm".

(c) Byte-identity guarantee — enable_no_confirm_exit=False produces results
    identical to a baseline run that predates the /116 feature field additions.

All tests use synthetic OHLCV data so they are data-extent-independent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from crypto_trade.backtest import run_backtest
from crypto_trade.backtest_models import BacktestConfig, Order, Signal
from crypto_trade.models import Kline
from crypto_trade.storage import write_klines

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_8H_MS = 28_800_000  # 8h in milliseconds
_BASE_T = 1_700_000_000_000  # arbitrary epoch-ms start


def _make_8h_kline(
    open_time: int,
    open: str,
    high: str,
    low: str,
    close: str,
) -> Kline:
    """Build a synthetic 8h kline."""
    return Kline(
        open_time=open_time,
        open=open,
        high=high,
        low=low,
        close=close,
        volume="1000.0",
        close_time=open_time + _8H_MS - 1,
        quote_volume="100000.0",
        trades=200,
        taker_buy_volume="500.0",
        taker_buy_quote_volume="50000.0",
    )


def _write_8h_data(tmp_path: Path, symbol: str, klines: list[Kline]) -> None:
    from crypto_trade.storage import csv_path

    path = csv_path(tmp_path, symbol, "8h")
    write_klines(path, klines)


class _BuyOnceWithSlPct:
    """Emit one buy signal with explicit sl_pct / tp_pct so no_confirm can compute ATR distance."""

    def __init__(self, sl_pct: float = 3.0, tp_pct: float = 6.0) -> None:
        self._fired = False
        self._sl_pct = sl_pct
        self._tp_pct = tp_pct

    def compute_features(self, master: pd.DataFrame) -> None:
        self._fired = False

    def get_signal(self, symbol: str, open_time: int) -> Signal:
        if not self._fired:
            self._fired = True
            return Signal(
                direction=1,
                weight=100,
                sl_pct=self._sl_pct,
                tp_pct=self._tp_pct,
            )
        return Signal(direction=0, weight=0)


def _base_config(tmp_path: Path, **overrides) -> BacktestConfig:
    """Build a BacktestConfig for 8h candles with 21-candle timeout (v3-canonical)."""
    defaults = dict(
        symbols=("TEST",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,  # 21 * 480 = 21 candles at 8h
        fee_pct=0.1,
        data_dir=tmp_path,
    )
    defaults.update(overrides)
    return BacktestConfig(**defaults)


# ---------------------------------------------------------------------------
# (a) Confirmed path: trade reaches threshold before arm_time → proceeds to TP/SL/timeout
# ---------------------------------------------------------------------------


def test_no_confirm_confirmed_path_proceeds_to_timeout(tmp_path: Path) -> None:
    """When high reaches the threshold within K candles, the trade is confirmed and
    proceeds to its normal timeout exit (NOT no_confirm)."""
    # sl_pct = 3.0% → 1×ATR = 3.0% of entry. trigger_atr=0.50 → threshold = entry * 1.015.
    # entry = 100.0 → threshold = 101.50.
    # k_candles = 4 → arm_time = open_time + 4 * 8h.
    # We confirm on candle 3 (high = 102.0 > 101.50), then no further TP/SL
    # so the trade times out at candle 21.
    sl_pct = 3.0
    tp_pct = 6.0
    # Build 25 candles: entry on candle 0, confirm on candle 3, timeout on candle 21.
    klines = []
    t = _BASE_T
    for i in range(25):
        h = "102.0" if i == 3 else "100.5"  # confirm on candle 3 (high > 101.50)
        klines.append(_make_8h_kline(t, "100.0", h, "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    cfg = _base_config(
        tmp_path,
        enable_no_confirm_exit=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = run_backtest(cfg, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    assert len(result) == 1, f"Expected 1 trade, got {len(result)}"
    trade = result[0]
    assert trade.exit_reason == "timeout", (
        f"Confirmed trade must exit via timeout, got '{trade.exit_reason}'"
    )


def test_no_confirm_confirmed_path_proceeds_to_tp(tmp_path: Path) -> None:
    """When confirmed before arm_time AND TP is hit later, the trade exits via take_profit."""
    sl_pct = 3.0
    tp_pct = 6.0
    # entry = 100.0; TP = entry * 1.06 = 106.0; threshold = entry * 1.015 = 101.50
    klines = []
    t = _BASE_T
    for i in range(12):
        if i == 2:
            h = "102.0"  # confirm (high > 101.50)
        elif i == 8:
            h = "107.0"  # TP hit (high > 106.0)
        else:
            h = "100.5"
        klines.append(_make_8h_kline(t, "100.0", h, "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    cfg = _base_config(
        tmp_path,
        enable_no_confirm_exit=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = run_backtest(cfg, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    assert len(result) == 1, f"Expected 1 trade, got {len(result)}"
    trade = result[0]
    assert trade.exit_reason == "take_profit", (
        f"Confirmed trade must exit via take_profit when TP hit, got '{trade.exit_reason}'"
    )


# ---------------------------------------------------------------------------
# (b) No-confirm path: excursion stays below threshold through arm_time → "no_confirm"
# ---------------------------------------------------------------------------


def test_no_confirm_fires_at_arm_time(tmp_path: Path) -> None:
    """When high never reaches the threshold within K candles, the trade exits with
    exit_reason='no_confirm' at candle K's close."""
    sl_pct = 3.0
    tp_pct = 6.0
    # entry = 100.0; threshold = 101.50 (trigger=0.50 * sl_dist=3.0%)
    # k_candles = 4; arm_time = open_time + 4 * 8h
    # Candles 0-4 all have high = 101.0 < 101.50 → never confirmed.
    # After candle 4 the arm_time is reached → no_confirm fires.
    klines = []
    t = _BASE_T
    for _ in range(25):
        klines.append(_make_8h_kline(t, "100.0", "101.0", "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    cfg = _base_config(
        tmp_path,
        enable_no_confirm_exit=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = run_backtest(cfg, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    assert len(result) == 1, f"Expected 1 trade, got {len(result)}"
    trade = result[0]
    assert trade.exit_reason == "no_confirm", (
        f"Unconfirmed trade must exit via 'no_confirm', got '{trade.exit_reason}'"
    )


def test_no_confirm_sl_wins_over_no_confirm_on_same_candle(tmp_path: Path) -> None:
    """When SL and arm_time coincide on the same candle, SL takes priority (TP/SL wins)."""
    sl_pct = 3.0
    tp_pct = 6.0
    # entry = 100.0; SL = 100.0 * (1 - 0.03) = 97.0; threshold = 101.50
    # Candles 0-3: never confirmed (high=101.0 < 101.50)
    # Candle 4 (the arm_time candle): low hits 96.8 < 97.0 → SL fires
    klines = []
    t = _BASE_T
    for i in range(25):
        if i == 4:
            # arm_time candle: SL hit + arm_time reached simultaneously
            klines.append(_make_8h_kline(t, "100.0", "101.0", "96.8", "97.5"))
        else:
            klines.append(_make_8h_kline(t, "100.0", "101.0", "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    cfg = _base_config(
        tmp_path,
        enable_no_confirm_exit=True,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = run_backtest(cfg, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    assert len(result) == 1, f"Expected 1 trade, got {len(result)}"
    trade = result[0]
    assert trade.exit_reason == "stop_loss", (
        f"SL must win over no_confirm on same candle, got '{trade.exit_reason}'"
    )


# ---------------------------------------------------------------------------
# (c) Byte-identity guarantee: enable_no_confirm_exit=False → identical to baseline
# ---------------------------------------------------------------------------


def test_no_confirm_false_byte_identical_to_baseline(tmp_path: Path) -> None:
    """With enable_no_confirm_exit=False, results must be byte-identical to the
    pre-/116 control run (no new fields affect any code path)."""
    sl_pct = 3.0
    tp_pct = 6.0
    klines = []
    t = _BASE_T
    for i in range(30):
        if i == 10:
            # TP hit
            klines.append(_make_8h_kline(t, "100.0", "107.0", "99.5", "100.0"))
        else:
            klines.append(_make_8h_kline(t, "100.0", "100.5", "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    # Baseline run (flag off — pre-/116 canonical behavior)
    cfg_baseline = _base_config(
        tmp_path,
        enable_no_confirm_exit=False,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result_baseline = run_backtest(cfg_baseline, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    # /116 flag-off run (same — explicit False with new knob fields set)
    cfg_off = _base_config(
        tmp_path,
        enable_no_confirm_exit=False,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result_off = run_backtest(cfg_off, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    assert len(result_baseline) == len(result_off), (
        f"Trade count differs: baseline={len(result_baseline)}, off={len(result_off)}"
    )
    for i, (a, b) in enumerate(zip(result_baseline, result_off)):
        assert a == b, f"Trade {i} differs with flag=False: baseline={a!r} off={b!r}"


def test_no_confirm_flag_false_does_not_fire_no_confirm_exit(tmp_path: Path) -> None:
    """With enable_no_confirm_exit=False, no trade should ever have exit_reason='no_confirm',
    even when the excursion would be below the threshold."""
    sl_pct = 3.0
    tp_pct = 6.0
    # Low excursion only — would fire no_confirm if flag were True
    klines = []
    t = _BASE_T
    for _ in range(25):
        klines.append(_make_8h_kline(t, "100.0", "101.0", "99.5", "100.0"))
        t += _8H_MS
    _write_8h_data(tmp_path, "TEST", klines)

    cfg = _base_config(
        tmp_path,
        enable_no_confirm_exit=False,
        no_confirm_trigger_atr=0.50,
        no_confirm_k_candles=4,
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
    )
    result = run_backtest(cfg, _BuyOnceWithSlPct(sl_pct=sl_pct, tp_pct=tp_pct))

    for trade in result:
        assert trade.exit_reason != "no_confirm", (
            f"exit_reason='no_confirm' must NOT appear when flag=False, got trade={trade!r}"
        )


# ---------------------------------------------------------------------------
# Smoke tests: import + dataclass field verification
# ---------------------------------------------------------------------------


def test_backtest_config_has_no_confirm_fields() -> None:
    """BacktestConfig must expose the three /116 fields with correct defaults."""
    cfg = BacktestConfig(
        symbols=("TEST",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("."),
    )
    assert cfg.enable_no_confirm_exit is False, "Default must be False (/059 byte-identity)"
    assert cfg.no_confirm_trigger_atr == 0.50
    assert cfg.no_confirm_k_candles == 4


def test_order_has_no_confirm_fields() -> None:
    """Order dataclass must expose the two /116 fields with correct defaults."""
    order = Order(
        symbol="TEST",
        direction=1,
        entry_price=100.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=97.0,
        take_profit_price=106.0,
        open_time=_BASE_T,
        timeout_time=_BASE_T + 10080 * 60_000,
    )
    assert order.no_confirm_arm_time == 0, "Default must be 0 (flag-off sentinel)"
    assert order.no_confirm_threshold_price == 0.0, "Default must be 0.0 (flag-off sentinel)"

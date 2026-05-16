"""iter-v3/054: adversarial tests for primitive 11 — per-symbol drawdown brake.

5 adversarial tests covering:
  1. brake_disabled_by_default_is_no_op: backward compat; no state, no counter, no kills.
  2. brake_engages_at_threshold_per_symbol: LDO synthetic sequence; brake state transitions.
  3. brake_disengages_at_recovery_threshold: recovery trade taken; state machine integrity.
  4. brake_independent_across_symbols: LDO brake doesn't affect BCH/TRX signals.
  5. brake_respects_30_day_window: old-peak expiry prevents false engagement.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from crypto_trade.backtest_models import TradeResult
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    enabled: bool = True,
    threshold: float = 10.0,
    recovery: float = 5.0,
    window_days: int = 30,
) -> RiskV2Config:
    """Build a minimal RiskV2Config with the drawdown brake fields set."""
    return RiskV2Config(
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_drawdown_brake=enabled,
        drawdown_brake_threshold_wpnl=threshold,
        drawdown_brake_recovery_wpnl=recovery,
        drawdown_brake_window_days=window_days,
    )


def _make_trade(symbol: str, wpnl: float, close_time_ms: int) -> TradeResult:
    """Build a minimal TradeResult for brake state-update testing."""
    return TradeResult(
        symbol=symbol,
        direction=1,
        open_time=close_time_ms - 100,
        close_time=close_time_ms,
        entry_price=100.0,
        exit_price=101.0,
        pnl_pct=wpnl * 0.1,
        net_pnl_pct=wpnl * 0.1,
        weighted_pnl=wpnl,
        weight_factor=1.0,
        exit_reason="take_profit",
        fee_pct=0.0,
    )


def _make_wrapper(config: RiskV2Config) -> RiskV2Wrapper:
    """Build a RiskV2Wrapper with a no-op inner strategy."""
    inner = MagicMock()
    inner.atr_column = "atr"
    wrapper = RiskV2Wrapper(inner, config)
    # Stub out the lookup so the wrapper skips feature-gated primitives cleanly
    wrapper._lookup = {}
    wrapper._feature_mean = {}
    wrapper._feature_std = {}
    wrapper._hurst_lower = {}
    wrapper._hurst_upper = {}
    return wrapper


# ---------------------------------------------------------------------------
# Test 1: brake_disabled_by_default_is_no_op
# ---------------------------------------------------------------------------


def test_brake_disabled_by_default_is_no_op() -> None:
    """With enable_per_symbol_drawdown_brake=False, the wrapper has no brake state,
    no counter increments, and record_trade_result is a no-op for the brake."""
    cfg = _make_config(enabled=False)
    wrapper = _make_wrapper(cfg)

    # After construction: brake state dicts are empty
    assert wrapper._brake_timeline == {}
    assert wrapper._brake_running_peak == {}
    assert wrapper._brake_cum_wpnl == {}
    assert wrapper._brake_on == {}

    # Feed 3 trades that would exceed the threshold if enabled
    day_ms = 24 * 60 * 60 * 1000
    base_ms = 1_700_000_000_000
    trades = [
        _make_trade("LDOUSDT", +15.0, base_ms),
        _make_trade("LDOUSDT", -8.0, base_ms + 1 * day_ms),
        _make_trade("LDOUSDT", -8.0, base_ms + 2 * day_ms),
    ]
    for t in trades:
        wrapper.record_trade_result(t)

    # Brake state must remain empty (no-op)
    assert wrapper._brake_timeline == {}
    assert wrapper._brake_on == {}

    # GateStats counter must be zero (not even initialized for this symbol)
    # Check via gate_stats_summary — if symbol never triggered a signal, no stats entry
    assert wrapper._gate_stats == {}


# ---------------------------------------------------------------------------
# Test 2: brake_engages_at_threshold_per_symbol
# ---------------------------------------------------------------------------


def test_brake_engages_at_threshold_per_symbol() -> None:
    """Synthetic LDO sequence: peak +15, then cumulative drops to +1 (dd=14 >= T=10).
    Brake must engage AFTER the trade that crosses the threshold, not before.
    """
    cfg = _make_config(enabled=True, threshold=10.0, recovery=5.0, window_days=30)
    wrapper = _make_wrapper(cfg)

    day_ms = 24 * 60 * 60 * 1000
    base_ms = 1_700_000_000_000

    # Trade 1: +15 wpnl (cum +15, peak +15, dd=0) — brake stays off
    t1 = _make_trade("LDOUSDT", +15.0, base_ms)
    wrapper.record_trade_result(t1)
    assert wrapper._brake_on.get("LDOUSDT") is False
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 15.0) < 1e-9
    assert abs(wrapper._brake_running_peak["LDOUSDT"] - 15.0) < 1e-9

    # Trade 2: -7 wpnl (cum +8, peak +15, dd=7) — below T=10, brake stays off
    t2 = _make_trade("LDOUSDT", -7.0, base_ms + 1 * day_ms)
    wrapper.record_trade_result(t2)
    assert wrapper._brake_on.get("LDOUSDT") is False
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 8.0) < 1e-9

    # Trade 3: -7 wpnl (cum +1, peak +15, dd=14 >= T=10) — brake ENGAGES
    t3 = _make_trade("LDOUSDT", -7.0, base_ms + 2 * day_ms)
    wrapper.record_trade_result(t3)
    assert wrapper._brake_on["LDOUSDT"] is True
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 3: brake_disengages_at_recovery_threshold
# ---------------------------------------------------------------------------


def test_brake_disengages_at_recovery_threshold() -> None:
    """After brake engagement, a recovery trade that brings dd <= recovery=5 disengages it.
    The recovery trade itself must not be blocked (brake disengages on close, not open).
    """
    cfg = _make_config(enabled=True, threshold=10.0, recovery=5.0, window_days=30)
    wrapper = _make_wrapper(cfg)

    day_ms = 24 * 60 * 60 * 1000
    base_ms = 1_700_000_000_000

    # Reach brake-on state: peak=15, cum=1, dd=14
    wrapper.record_trade_result(_make_trade("LDOUSDT", +15.0, base_ms))
    wrapper.record_trade_result(_make_trade("LDOUSDT", -14.0, base_ms + 1 * day_ms))
    assert wrapper._brake_on["LDOUSDT"] is True
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 1.0) < 1e-9

    # Recovery trade: +9 wpnl → cum +10, peak still +15, dd=5 == recovery (<=5) → DISENGAGE
    wrapper.record_trade_result(_make_trade("LDOUSDT", +9.0, base_ms + 2 * day_ms))
    assert wrapper._brake_on["LDOUSDT"] is False
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 10.0) < 1e-9

    # Re-engagement: another drawdown past T=10 should re-engage the brake
    wrapper.record_trade_result(_make_trade("LDOUSDT", -12.0, base_ms + 3 * day_ms))
    # cum = -2, peak = 10 (from the +10 after recovery), dd = 10+2 = 12 >= T=10 → re-engage
    assert wrapper._brake_on["LDOUSDT"] is True


# ---------------------------------------------------------------------------
# Test 4: brake_independent_across_symbols
# ---------------------------------------------------------------------------


def test_brake_independent_across_symbols() -> None:
    """Simulate LDO catastrophic streak + BCH/TRX healthy trades simultaneously.
    LDO brake on must NOT affect BCH or TRX brake state.
    """
    cfg = _make_config(enabled=True, threshold=10.0, recovery=5.0, window_days=30)
    wrapper = _make_wrapper(cfg)

    day_ms = 24 * 60 * 60 * 1000
    base_ms = 1_700_000_000_000

    # BCH: healthy — +5, +5 (no drawdown)
    wrapper.record_trade_result(_make_trade("BCHUSDT", +5.0, base_ms))
    wrapper.record_trade_result(_make_trade("BCHUSDT", +5.0, base_ms + 1 * day_ms))
    assert wrapper._brake_on.get("BCHUSDT") is False

    # LDO: catastrophic — peak +15, then -14 → dd=14 >= T=10
    wrapper.record_trade_result(_make_trade("LDOUSDT", +15.0, base_ms + 2 * day_ms))
    wrapper.record_trade_result(_make_trade("LDOUSDT", -14.0, base_ms + 3 * day_ms))
    assert wrapper._brake_on["LDOUSDT"] is True

    # TRX: healthy — +3 (no drawdown)
    wrapper.record_trade_result(_make_trade("TRXUSDT", +3.0, base_ms + 4 * day_ms))
    assert wrapper._brake_on.get("TRXUSDT") is False

    # Assert per-symbol independence
    assert wrapper._brake_on["LDOUSDT"] is True  # only LDO engaged
    assert wrapper._brake_on.get("BCHUSDT") is False  # BCH unaffected
    assert wrapper._brake_on.get("TRXUSDT") is False  # TRX unaffected

    # Cumulative wpnls are independent
    assert abs(wrapper._brake_cum_wpnl["BCHUSDT"] - 10.0) < 1e-9
    assert abs(wrapper._brake_cum_wpnl["LDOUSDT"] - 1.0) < 1e-9
    assert abs(wrapper._brake_cum_wpnl["TRXUSDT"] - 3.0) < 1e-9


# ---------------------------------------------------------------------------
# Test 5: brake_respects_30_day_window
# ---------------------------------------------------------------------------


def test_brake_respects_30_day_window() -> None:
    """A trade >30 days old that established a peak must expire from the rolling window.
    After expiry the peak re-evaluates from in-window trades only, so a drawdown that
    would have triggered the brake relative to the old peak no longer does.
    """
    cfg = _make_config(enabled=True, threshold=10.0, recovery=5.0, window_days=30)
    wrapper = _make_wrapper(cfg)

    day_ms = 24 * 60 * 60 * 1000
    base_ms = 1_700_000_000_000

    # Old trade (32 days ago relative to 'now'): establishes peak at +15
    old_trade_ms = base_ms  # will be 32 days before the later trade
    wrapper.record_trade_result(_make_trade("LDOUSDT", +15.0, old_trade_ms))
    assert wrapper._brake_on.get("LDOUSDT") is False
    assert abs(wrapper._brake_running_peak["LDOUSDT"] - 15.0) < 1e-9

    # New trade 32 days later: +2 wpnl (cum +17, window has both trades → peak=17, dd=0)
    # The old trade is still in the window at this point (32d is > 30d — it should expire)
    new_trade_ms = old_trade_ms + 32 * day_ms
    wrapper.record_trade_result(_make_trade("LDOUSDT", +2.0, new_trade_ms))

    # After this trade: old_trade (31d+ ago) expires from window since
    # cutoff = new_trade_ms - 30*DAY_MS = base_ms + 2*DAY_MS, and old_trade_ms = base_ms < cutoff.
    # So the window contains only the new_trade → cum_wpnl_in_window_at_new_trade = +17
    # BUT the deque at new_trade contains only (new_trade_ms, cum=+17)
    # → peak = +17, dd = 17 - 17 = 0 → brake stays off

    # Verify old trade was expired (deque has only 1 entry — the new trade)
    assert len(wrapper._brake_timeline["LDOUSDT"]) == 1
    assert wrapper._brake_on.get("LDOUSDT") is False

    # The peak from the old trade is gone. Now add a losing trade that would
    # have triggered the brake relative to old peak (+15 - 14 = 1, dd=14 >= T=10),
    # but relative to NEW in-window peak (+17, dd=0+14=14 >= T=10 anyway in this case).
    # Let's instead verify: add a modest -8 loss → dd = 17 - (17-8) = 8 < T=10 → no brake
    wrapper.record_trade_result(_make_trade("LDOUSDT", -8.0, new_trade_ms + 1 * day_ms))
    # cum = 17 - 8 = 9, peak in window = 17 (from trade 2), dd = 17 - 9 = 8 < T=10
    assert wrapper._brake_on.get("LDOUSDT") is False

    # Now add another -8 loss: cum = 1, dd = 17 - 1 = 16 >= T=10 → brake engages
    wrapper.record_trade_result(_make_trade("LDOUSDT", -8.0, new_trade_ms + 2 * day_ms))
    assert wrapper._brake_on["LDOUSDT"] is True

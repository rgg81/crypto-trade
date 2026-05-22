"""Adversarial tests for primitive 11 — per-symbol drawdown brake.

iter-v3/054 original 5 adversarial tests:
  1. brake_disabled_by_default_is_no_op: backward compat; no state, no counter, no kills.
  2. brake_engages_at_threshold_per_symbol: LDO synthetic sequence; brake state transitions.
  3. brake_disengages_at_recovery_threshold: recovery trade taken; state machine integrity.
  4. brake_independent_across_symbols: LDO brake doesn't affect BCH/TRX signals.
  5. brake_respects_30_day_window: old-peak expiry prevents false engagement.

iter-v3/127 time-override deadlock-breaker 3 additional adversarial tests:
  6. brake_time_override_fires_after_M_candles: deadlock-impossibility proof integration test.
     Synthetic: 5 BCH losses → brake-ON → 31 candles no-signal → 1 BCH signal → assert
     time-override fires + trade NOT blocked.
  7. brake_time_override_disabled_when_M_zero: M=0 preserves legacy /054 behavior (no override).
  8. brake_time_override_does_not_re_trigger_after_state_recovery: when state-based recovery
     fires BEFORE M elapsed, time-override does not re-trigger on the same engagement.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from crypto_trade.backtest_models import Signal, TradeResult
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    enabled: bool = True,
    threshold: float = 10.0,
    recovery: float = 5.0,
    window_days: int = 30,
    time_override_candles: int = 0,
    candle_interval_minutes: int = 480,
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
        drawdown_brake_time_override_candles=time_override_candles,
        drawdown_brake_candle_interval_minutes=candle_interval_minutes,
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


# ---------------------------------------------------------------------------
# iter-v3/127 Tests 6-8: time-based override deadlock-breaker
# ---------------------------------------------------------------------------

# Use short candle intervals to make ms math easy in tests (1 "candle" = 1 minute)
_TEST_CANDLE_MINUTES = 1
_TEST_CANDLE_MS = _TEST_CANDLE_MINUTES * 60 * 1000


def _make_config_with_override(
    threshold: float = 7.0,
    recovery: float = 6.0,
    window_days: int = 45,
    m_candles: int = 21,
) -> RiskV2Config:
    """Build a minimal RiskV2Config with time-override enabled.

    Uses _TEST_CANDLE_MINUTES (1 minute) as the candle interval so time-override
    ms math is trivial without depending on real 8h timing in test code.
    """
    return RiskV2Config(
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_drawdown_brake=True,
        drawdown_brake_threshold_wpnl=threshold,
        drawdown_brake_recovery_wpnl=recovery,
        drawdown_brake_window_days=window_days,
        drawdown_brake_time_override_candles=m_candles,
        drawdown_brake_candle_interval_minutes=_TEST_CANDLE_MINUTES,
    )


def _make_wrapper_with_override(config: RiskV2Config) -> RiskV2Wrapper:
    """Build a RiskV2Wrapper with override config and a signal-emitting inner mock."""
    inner = MagicMock()
    inner.atr_column = "atr"
    # Inner strategy always emits a LONG signal for any symbol
    inner.get_signal.return_value = Signal(
        direction=1, weight=1, tp_pct=8.0, sl_pct=4.0, confidence=0.9
    )
    wrapper = RiskV2Wrapper(inner, config)
    # Stub out feature-gated lookups (not needed for brake tests)
    wrapper._lookup = {}
    wrapper._feature_mean = {}
    wrapper._feature_std = {}
    wrapper._hurst_lower = {}
    wrapper._hurst_upper = {}
    return wrapper


# ---------------------------------------------------------------------------
# Test 6: brake_time_override_fires_after_M_candles — deadlock-impossibility proof
# ---------------------------------------------------------------------------


def test_brake_time_override_fires_after_m_candles() -> None:
    """Adversarial deadlock-impossibility integration test (iter-v3/127 brief Section 2.3).

    Sequence:
      1. 5 BCH losses to engage the brake (dd ≥ T=7.0).
      2. 31 candles of no signals (simulated by advancing open_time beyond M+10 candles).
      3. 1 BCH signal arrives at open_time >= brake_on_close_time + M * candle_ms.

    Assertions:
      - After the 4th+ loss, brake engages (brake_on[BCH] = True).
      - The signal at step 3 is NOT blocked (brake-OFF via time-override fires).
      - drawdown_brake_time_overrides counter increments.
      - drawdown_brake_fires counter does NOT increment (no kill).
    """
    m_candles = 21  # M=21 candles at _TEST_CANDLE_MINUTES each
    cfg = _make_config_with_override(
        threshold=7.0, recovery=6.0, window_days=45, m_candles=m_candles
    )
    wrapper = _make_wrapper_with_override(cfg)

    base_ms = 1_700_000_000_000
    day_ms = 24 * 60 * 60 * 1000

    # Step 1: 5 BCH losses clustered in a 5-day window (each -5.5 wpnl).
    # Start with +20 initial gain to establish a peak, then 5 losses of -5.5.
    # After initial: cum=+20, peak=+20, dd=0.
    # After 5x-5.5: cum=+20-27.5=-7.5; peak=+20; dd=27.5>=T=7.
    wrapper.record_trade_result(_make_trade("BCHUSDT", +20.0, base_ms))
    assert wrapper._brake_on.get("BCHUSDT") is False

    loss_times = []
    for i in range(5):
        t_ms = base_ms + (i + 1) * day_ms
        wrapper.record_trade_result(_make_trade("BCHUSDT", -5.5, t_ms))
        loss_times.append(t_ms)

    # After 5 losses: brake engages at the 2nd loss (dd=11 >= T=7.0).
    # _brake_on_close_time stores the time of the trade that FIRST crossed T.
    first_engage_time = loss_times[1]  # 3rd trade overall (index 1 of loss_times)
    assert wrapper._brake_on.get("BCHUSDT") is True, "Brake should be ON after 5 losses"
    assert wrapper._brake_on_close_time.get("BCHUSDT") == first_engage_time

    # Step 2: No BCH trades for m_candles+10 candles (21+10=31 buffer).
    # Step 3: BCH signal arrives at open_time = first_engage_time + (m_candles+10)*candle_ms.
    # 31 candles elapsed since first engagement; exceeds M=21 → time-override must fire.
    signal_open_time = first_engage_time + (m_candles + 10) * _TEST_CANDLE_MS

    # Call get_signal: inner returns LONG (+1); time-override should disengage brake; signal passes.
    result_signal = wrapper.get_signal("BCHUSDT", signal_open_time)

    # Assert: brake-OFF via time-override; signal NOT blocked
    assert wrapper._brake_on.get("BCHUSDT") is False, (
        "Time-override must have fired: brake_on[BCHUSDT] should be False "
        "after m_candles+10 elapsed"
    )
    assert result_signal.direction == 1, "Signal must NOT be blocked after time-override fires"

    # Assert: time-override counter incremented; brake_fires did NOT increment
    bch_stats = wrapper._gate_stats.get("BCHUSDT")
    assert bch_stats is not None, "GateStats for BCHUSDT should exist after get_signal"
    assert bch_stats.drawdown_brake_time_overrides == 1, (
        f"Expected 1 time-override fire, got {bch_stats.drawdown_brake_time_overrides}"
    )
    assert bch_stats.drawdown_brake_fires == 0, (
        f"Expected 0 brake kills (override fired before kill check), "
        f"got {bch_stats.drawdown_brake_fires}"
    )

    # The DEADLOCK is broken: the time-override allowed the signal through.
    # This is the /127 deadlock-impossibility proof materialized as a test.


# ---------------------------------------------------------------------------
# Test 7: brake_time_override_disabled_when_M_zero
# ---------------------------------------------------------------------------


def test_brake_time_override_disabled_when_m_zero() -> None:
    """With M=0 (default), the time-override is DISABLED — preserves /054 legacy behavior.

    Scenario: brake engages, then a signal arrives at open_time >> brake_on_close_time.
    With M=0, the time-override must NOT fire; the brake must continue to block signals.
    """
    # M=0 means time_override_candles=0 — legacy behavior
    cfg = _make_config(
        enabled=True,
        threshold=10.0,
        recovery=5.0,
        window_days=30,
        time_override_candles=0,  # DISABLED
        candle_interval_minutes=480,
    )
    wrapper = _make_wrapper_with_override(cfg)

    base_ms = 1_700_000_000_000
    day_ms = 24 * 60 * 60 * 1000

    # Engage the brake: peak +15, then loss of -14 → dd=14 ≥ T=10
    wrapper.record_trade_result(_make_trade("LDOUSDT", +15.0, base_ms))
    wrapper.record_trade_result(_make_trade("LDOUSDT", -14.0, base_ms + 1 * day_ms))
    assert wrapper._brake_on.get("LDOUSDT") is True, "Brake should be ON"

    # Signal arrives 1000 days later — WELL past any real M threshold
    far_future_open_time = base_ms + 1000 * day_ms

    result_signal = wrapper.get_signal("LDOUSDT", far_future_open_time)

    # With M=0, time-override never fires; brake stays ON; signal is BLOCKED
    assert wrapper._brake_on.get("LDOUSDT") is True, (
        "With M=0 (disabled), brake should remain ON regardless of elapsed time"
    )
    assert result_signal.direction == 0, (
        "Signal must be BLOCKED when M=0 (no time-override) and brake is ON"
    )

    ldo_stats = wrapper._gate_stats.get("LDOUSDT")
    assert ldo_stats is not None
    assert ldo_stats.drawdown_brake_time_overrides == 0, "No time-override fires expected when M=0"
    assert ldo_stats.drawdown_brake_fires == 1, (
        "Brake kill counter must increment when signal is blocked"
    )


# ---------------------------------------------------------------------------
# Test 8: brake_time_override_does_not_re_trigger_after_state_recovery
# ---------------------------------------------------------------------------


def test_brake_time_override_does_not_re_trigger_after_state_recovery() -> None:
    """If state-based recovery fires BEFORE M candles elapsed, time-override should not
    fire on the same engagement (mutual exclusivity of brake-OFF mechanisms).

    Sequence:
      1. Engage brake (dd ≥ T).
      2. Recovery trade arrives within M candles (dd ≤ T_R) → state-based brake-OFF.
      3. Next signal arrives after M candles from original brake-ON.
      4. Assert: time-override counter is 0 (state-based recovery fired, not time-override).
      5. Assert: signal passes (brake is OFF from state-recovery, not from time-override).
    """
    m_candles = 21
    cfg = _make_config_with_override(
        threshold=7.0, recovery=6.0, window_days=45, m_candles=m_candles
    )
    wrapper = _make_wrapper_with_override(cfg)

    base_ms = 1_700_000_000_000
    day_ms = 24 * 60 * 60 * 1000

    # Step 1: Engage brake via losses
    # Trade sequence: +20, -14 → cum +6, peak +20, dd = 14 >= T=7.0 → brake ON
    wrapper.record_trade_result(_make_trade("TRXUSDT", +20.0, base_ms))
    wrapper.record_trade_result(_make_trade("TRXUSDT", -14.0, base_ms + 1 * day_ms))
    assert wrapper._brake_on.get("TRXUSDT") is True, "Brake should be ON"
    brake_on_time = base_ms + 1 * day_ms  # close_time of the trade that triggered brake-ON

    # Step 2: Recovery trade arrives WITHIN M candles (5 candles after brake-ON).
    # Recovery trade: +10 wpnl → cum = 6 + 10 = 16, peak = 20, dd = 20 - 16 = 4 ≤ T_R=6.0 → OFF
    recovery_close_time = brake_on_time + 5 * _TEST_CANDLE_MS  # 5 candles after brake-ON
    wrapper.record_trade_result(_make_trade("TRXUSDT", +10.0, recovery_close_time))
    assert wrapper._brake_on.get("TRXUSDT") is False, (
        "State-based recovery should have fired (dd=4 ≤ T_R=6.0)"
    )

    # Step 3: Signal arrives after m_candles+5 candles from brake_on_time (well past M=21)
    signal_open_time = brake_on_time + (m_candles + 5) * _TEST_CANDLE_MS

    result_signal = wrapper.get_signal("TRXUSDT", signal_open_time)

    # Step 4: time-override counter must be 0 (state-based recovery fired first)
    trx_stats = wrapper._gate_stats.get("TRXUSDT")
    assert trx_stats is not None
    assert trx_stats.drawdown_brake_time_overrides == 0, (
        "Time-override must NOT fire when brake was already disengaged by state-based recovery"
    )

    # Step 5: Signal must pass (brake is OFF from state-recovery)
    assert result_signal.direction == 1, "Signal must pass when brake is OFF"
    assert trx_stats.drawdown_brake_fires == 0, "No brake kills expected (brake was OFF)"

"""Adversarial tests for iter-v3/129 — primitive 13: per-symbol drawdown SIZE-SCALING.

Continuous multiplicative dampening at per-symbol rolling drawdown.
Distinct from primitive 11 (per_symbol_drawdown_brake; binary kill at /054/127).

Tests:
  1. scaling_disabled_by_default_is_no_op: backward compat; no state, no counter.
  2. weight_multiplier_at_t_r_is_one: dd <= T_R → multiplier == 1.0 (full size).
  3. weight_multiplier_at_t_max_is_zero: dd >= T_max → multiplier == 0.0 (zero size).
  4. weight_multiplier_interpolation: dd between T_R and T_max → linear interpolation.
  5. weight_factor_multiplied_not_killed: signal weight_factor reduced, not zeroed.
  6. time_override_fires_after_M_candles: zero-multiplier state + M elapsed → 1.0.
  7. scaling_independent_across_symbols: BCH scaling does not affect LDO/TRX.
  8. deadlock_impossibility_adversarial: 1 large loss + 100 tiny gains; consecutive_zeros == 0.
  9. scaling_no_effect_when_brake_reverted: enable_per_symbol_drawdown_brake=False is independent.
 10. validation_rejects_bad_config: T_R >= T_max raises ValueError.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from crypto_trade.backtest_models import Signal, TradeResult
from crypto_trade.strategies.ml.risk_v2 import RiskV2Config, RiskV2Wrapper

# ---------------------------------------------------------------------------
# Constants matching brief Section 2 chosen config
# ---------------------------------------------------------------------------
CHOSEN_T_R = 6.0
CHOSEN_T_MAX = 7.0
CHOSEN_WINDOW_DAYS = 45
CHOSEN_TIME_OVERRIDE = 21
CHOSEN_CANDLE_INTERVAL = 480  # 8h in minutes

MS_PER_CANDLE = CHOSEN_CANDLE_INTERVAL * 60 * 1000
MS_PER_DAY = 24 * 60 * 60 * 1000

BASE_TIME = 1_700_000_000_000  # arbitrary start time in ms


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scaling_config(
    enabled: bool = True,
    t_r: float = CHOSEN_T_R,
    t_max: float = CHOSEN_T_MAX,
    window_days: int = CHOSEN_WINDOW_DAYS,
    time_override_candles: int = CHOSEN_TIME_OVERRIDE,
    candle_interval_minutes: int = CHOSEN_CANDLE_INTERVAL,
) -> RiskV2Config:
    """Build a minimal RiskV2Config with the drawdown scaling fields set."""
    return RiskV2Config(
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_drawdown_brake=False,
        enable_per_symbol_drawdown_scaling=enabled,
        drawdown_scaling_t_r=t_r,
        drawdown_scaling_t_max=t_max,
        drawdown_scaling_window_days=window_days,
        drawdown_scaling_time_override_candles=time_override_candles,
        drawdown_scaling_candle_interval_minutes=candle_interval_minutes,
    )


def _make_trade(symbol: str, wpnl: float, close_time_ms: int) -> TradeResult:
    """Build a minimal TradeResult for scaling state-update testing."""
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
    wrapper._lookup = {}
    wrapper._feature_mean = {}
    wrapper._feature_std = {}
    wrapper._hurst_lower = {}
    wrapper._hurst_upper = {}
    return wrapper


def _make_signal(weight: int = 100, direction: int = 1) -> Signal:
    """Minimal long signal with given weight."""
    return Signal(direction=direction, weight=weight, tp_pct=8.0, sl_pct=4.0)


# ---------------------------------------------------------------------------
# Test 1 — disabled by default is a no-op
# ---------------------------------------------------------------------------


def test_scaling_disabled_by_default_is_no_op():
    """When enable_per_symbol_drawdown_scaling=False, state is untouched, weight unchanged."""
    cfg = RiskV2Config(
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        enable_per_symbol_drawdown_brake=False,
        # enable_per_symbol_drawdown_scaling defaults to False
    )
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    t0 = BASE_TIME
    sig = wrapper.get_signal("BCHUSDT", t0)

    assert sig.weight == 100, "weight unchanged when scaling disabled"
    assert sig.direction == 1
    # No scaling state initialized
    assert "BCHUSDT" not in wrapper._scaling_timeline
    assert "BCHUSDT" not in wrapper._scaling_cum_wpnl


# ---------------------------------------------------------------------------
# Test 2 — multiplier == 1.0 when dd <= T_R (full size)
# ---------------------------------------------------------------------------


def test_weight_multiplier_at_t_r_is_one():
    """When drawdown <= T_R, scaling_multiplier == 1.0 and weight is unchanged."""
    cfg = _make_scaling_config(enabled=True)
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    # Record a trade with positive wpnl — no drawdown
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=10.0, close_time_ms=BASE_TIME))

    # dd = 0 <= T_R=6.0 → full size
    t1 = BASE_TIME + MS_PER_CANDLE
    sig = wrapper.get_signal("BCHUSDT", t1)
    assert sig.weight == 100, f"expected weight=100 (no dampening), got {sig.weight}"
    assert sig.direction == 1


# ---------------------------------------------------------------------------
# Test 3 — multiplier == 0.0 when dd >= T_max (zero size)
# ---------------------------------------------------------------------------


def test_weight_multiplier_at_t_max_is_zero():
    """When drawdown >= T_max, scaling_multiplier == 0.0, signal reduced to weight=1."""
    cfg = _make_scaling_config(
        enabled=True,
        time_override_candles=0,  # disable time-override to isolate zero-multiplier behavior
    )
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    # Build up a large loss: dd = 10.0 >= T_max=7.0
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=5.0, close_time_ms=t0))
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-15.0, close_time_ms=t0 + MS_PER_DAY))

    # dd = peak(5.0) - cum(-10.0) = 15.0 >= T_max=7.0 → multiplier=0.0
    t2 = t0 + 2 * MS_PER_DAY
    sig = wrapper.get_signal("BCHUSDT", t2)
    # weight_factor = max(1, round(100 * 1.0 * 1.0 * 0.0)) = max(1, 0) = 1
    assert sig.weight == 1, f"expected weight=1 (zero multiplier → max(1,0)=1), got {sig.weight}"
    assert sig.direction == 1


# ---------------------------------------------------------------------------
# Test 4 — linear interpolation between T_R and T_max
# ---------------------------------------------------------------------------


def test_weight_multiplier_interpolation():
    """dd == T_R + 0.5*(T_max - T_R) → multiplier == 0.5."""
    # T_R=6.0, T_max=7.0 → midpoint dd=6.5 → multiplier=(7.0-6.5)/(7.0-6.0)=0.5
    cfg = _make_scaling_config(
        enabled=True,
        t_r=6.0,
        t_max=7.0,
        time_override_candles=0,  # disable override
    )
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    # Peak=10.0, then loss of 6.5 → cum=3.5 → dd=10.0-3.5=6.5
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=10.0, close_time_ms=t0))
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-6.5, close_time_ms=t0 + MS_PER_DAY))

    t2 = t0 + 2 * MS_PER_DAY
    sig = wrapper.get_signal("BCHUSDT", t2)
    # multiplier = (7.0 - 6.5) / (7.0 - 6.0) = 0.5
    # weight = max(1, round(100 * 0.5)) = max(1, 50) = 50
    assert sig.weight == 50, f"expected weight=50 (0.5 multiplier), got {sig.weight}"


# ---------------------------------------------------------------------------
# Test 5 — signal weight_factor multiplied, trade NOT killed
# ---------------------------------------------------------------------------


def test_weight_factor_multiplied_not_killed():
    """Partial scaling reduces weight, does NOT return NO_SIGNAL (direction remains 1)."""
    cfg = _make_scaling_config(enabled=True, time_override_candles=0)
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=200, direction=1)
    wrapper.inner.get_signal.return_value = inner_signal

    # Create dd in partial-scaling zone: dd=6.5 → multiplier=0.5
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=10.0, close_time_ms=t0))
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-6.5, close_time_ms=t0 + MS_PER_DAY))

    t2 = t0 + 2 * MS_PER_DAY
    sig = wrapper.get_signal("BCHUSDT", t2)

    # direction must still be 1 (trade not killed, just dampened)
    assert sig.direction == 1, f"direction must be 1 (not killed), got {sig.direction}"
    # weight = max(1, round(200 * 0.5)) = 100
    assert sig.weight == 100, f"expected weight=100, got {sig.weight}"


# ---------------------------------------------------------------------------
# Test 6 — time-override fires after M candles
# ---------------------------------------------------------------------------


def test_time_override_fires_after_m_candles():
    """After M candles elapsed since zero-multiplier, signal returns to full size."""
    m = 5  # small M for test speed
    cfg = _make_scaling_config(
        enabled=True,
        t_r=6.0,
        t_max=7.0,
        time_override_candles=m,
        candle_interval_minutes=480,
    )
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    # Create large loss → dd = 15.0 >= T_max=7.0 → multiplier=0.0
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=5.0, close_time_ms=t0))
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-20.0, close_time_ms=t0 + MS_PER_DAY))

    # Signal at t0 + 2 days — zero-since is recorded
    t_zero_since = t0 + 2 * MS_PER_DAY
    sig_at_zero = wrapper.get_signal("BCHUSDT", t_zero_since)
    assert sig_at_zero.weight == 1, (
        f"expected weight=1 at zero-multiplier, got {sig_at_zero.weight}"
    )
    # zero_since should be set
    assert wrapper._scaling_zero_since.get("BCHUSDT") == t_zero_since

    # Signal at t_zero_since + (M-1) candles — still zero
    t_before_override = t_zero_since + (m - 1) * MS_PER_CANDLE
    sig_before = wrapper.get_signal("BCHUSDT", t_before_override)
    assert sig_before.weight == 1, "still zero before M candles elapsed"

    # Signal at t_zero_since + M candles — time-override fires → full size
    t_at_override = t_zero_since + m * MS_PER_CANDLE
    sig_after = wrapper.get_signal("BCHUSDT", t_at_override)
    assert sig_after.weight == 100, (
        f"expected weight=100 after time-override fires (M={m} candles), got {sig_after.weight}"
    )
    # zero_since should be cleared
    assert wrapper._scaling_zero_since.get("BCHUSDT") is None

    # Verify GateStats counter
    stats = wrapper._gate_stats.get("BCHUSDT")
    assert stats is not None
    assert stats.drawdown_scaling_time_overrides == 1


# ---------------------------------------------------------------------------
# Test 7 — independent across symbols
# ---------------------------------------------------------------------------


def test_scaling_independent_across_symbols():
    """BCH in drawdown zone does not affect LDO or TRX signals."""
    cfg = _make_scaling_config(enabled=True, time_override_candles=0)
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    # Push BCH into zero-multiplier territory
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=5.0, close_time_ms=t0))
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-20.0, close_time_ms=t0 + MS_PER_DAY))

    t2 = t0 + 2 * MS_PER_DAY

    # BCH: zero multiplier
    bch_sig = wrapper.get_signal("BCHUSDT", t2)
    assert bch_sig.weight == 1, f"BCH expected weight=1, got {bch_sig.weight}"

    # LDO: no trades yet → no drawdown → full size
    ldo_sig = wrapper.get_signal("LDOUSDT", t2)
    assert ldo_sig.weight == 100, f"LDO expected weight=100 (unaffected), got {ldo_sig.weight}"

    # TRX: no trades yet → no drawdown → full size
    trx_sig = wrapper.get_signal("TRXUSDT", t2)
    assert trx_sig.weight == 100, f"TRX expected weight=100 (unaffected), got {trx_sig.weight}"


# ---------------------------------------------------------------------------
# Test 8 — deadlock impossibility adversarial test
# ---------------------------------------------------------------------------


def test_deadlock_impossibility_adversarial():
    """1 large loss (-30 wpnl) + 100 tiny positive wpnl trades: consecutive_zeros == 0.

    The continuous form with M=21 time-override should prevent persistent zero-multiplier
    (the T3 deadlock-impossibility test from the EDA; brief Section 2 T3).
    """
    cfg = _make_scaling_config(
        enabled=True,
        t_r=6.0,
        t_max=7.0,
        window_days=45,
        time_override_candles=21,
        candle_interval_minutes=480,
    )
    wrapper = _make_wrapper(cfg)

    inner_signal = _make_signal(weight=100)
    wrapper.inner.get_signal.return_value = inner_signal

    t = BASE_TIME
    # 1 large loss — triggers zero-multiplier if dd >= T_max
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-30.0, close_time_ms=t))
    t += MS_PER_CANDLE

    max_consecutive = 0
    cur_streak = 0

    for i in range(100):
        sig = wrapper.get_signal("BCHUSDT", t)
        if sig.weight == 1:  # zero-multiplier produces max(1, 0) = 1
            cur_streak += 1
            if cur_streak > max_consecutive:
                max_consecutive = cur_streak
        else:
            cur_streak = 0
        # small positive wpnl trade
        wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=0.01, close_time_ms=t + 1))
        t += MS_PER_CANDLE

    # With M=21 time-override: longest streak <= M (override fires after 21 consecutive zeros)
    assert max_consecutive <= 21, (
        f"deadlock impossibility FAIL: max_consecutive_zeros={max_consecutive} > 21 (M=21). "
        f"Time-override should break the zero-multiplier after M=21 candles."
    )


# ---------------------------------------------------------------------------
# Test 9 — brake reverted independent of scaling
# ---------------------------------------------------------------------------


def test_scaling_does_not_activate_brake():
    """enable_per_symbol_drawdown_brake=False means brake state is NOT updated."""
    cfg = _make_scaling_config(enabled=True)
    assert cfg.enable_per_symbol_drawdown_brake is False

    wrapper = _make_wrapper(cfg)
    t0 = BASE_TIME
    wrapper.record_trade_result(_make_trade("BCHUSDT", wpnl=-50.0, close_time_ms=t0))

    # Brake state should remain empty (brake disabled)
    assert "BCHUSDT" not in wrapper._brake_timeline
    assert "BCHUSDT" not in wrapper._brake_on

    # Scaling state should be populated
    assert "BCHUSDT" in wrapper._scaling_timeline


# ---------------------------------------------------------------------------
# Test 10 — validation rejects bad config
# ---------------------------------------------------------------------------


def test_validation_rejects_t_r_gte_t_max():
    """T_R >= T_max raises ValueError (interval is invalid)."""
    import pytest

    with pytest.raises(ValueError, match="0 < T_R"):
        RiskV2Config(
            enable_vol_scaling=False,
            enable_adx_gate=False,
            enable_hurst_check=False,
            enable_zscore_ood=False,
            enable_low_vol_filter=False,
            enable_per_symbol_drawdown_scaling=True,
            drawdown_scaling_t_r=7.0,  # T_R == T_max — invalid
            drawdown_scaling_t_max=7.0,
        )

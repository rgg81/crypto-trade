"""Unit tests for the per-symbol PnL cap (iter-v3/020, RiskV2Wrapper primitive 8).

Adversarial tests per research brief Section 10 (mandatory: basic + past_only).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from crypto_trade.backtest_models import Signal, TradeResult
from crypto_trade.strategies.ml.risk_v2 import GateStats, RiskV2Config, RiskV2Wrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trade(
    symbol: str,
    open_time: int,
    close_time: int,
    weighted_pnl: float,
    direction: int = 1,
) -> TradeResult:
    """Construct a minimal TradeResult for cap-unit-test purposes."""
    return TradeResult(
        symbol=symbol,
        direction=direction,
        entry_price=100.0,
        exit_price=101.0 if direction == 1 else 99.0,
        weight_factor=1.0,
        open_time=open_time,
        close_time=close_time,
        exit_reason="take_profit",
        pnl_pct=weighted_pnl,
        fee_pct=0.0,
        net_pnl_pct=weighted_pnl,
        weighted_pnl=weighted_pnl,
    )


def _make_wrapper(
    cap: float = 0.40,
    window_bars: int = 90,
    enable: bool = True,
) -> RiskV2Wrapper:
    """Build a RiskV2Wrapper with cap enabled and all other gates disabled."""
    inner = MagicMock()
    inner.atr_column = "natr_21_raw"

    # Return a signal with weight=100 from the inner strategy
    inner.get_signal.return_value = Signal(direction=1, weight=100, tp_pct=8.0, sl_pct=4.0)

    cfg = RiskV2Config(
        enable_vol_scaling=False,
        enable_adx_gate=False,
        enable_hurst_check=False,
        enable_zscore_ood=False,
        enable_low_vol_filter=False,
        max_per_symbol_pnl_share=cap,
        max_per_symbol_window_bars=window_bars,
        enable_per_symbol_cap=enable,
    )
    wrapper = RiskV2Wrapper(inner, cfg)
    # Pre-populate the lookup so _row_for returns None (all gates pass trivially)
    # because all kill gates are disabled, the wrapper never touches lookup.
    return wrapper


# ---------------------------------------------------------------------------
# Test 1: cap fires when symbol share > 0.40
# ---------------------------------------------------------------------------


def test_per_symbol_cap_basic() -> None:
    """Symbol A has 5 winning trades; 6th trade should be scaled by cap/share."""
    bar_ms = 28_800_000  # 8h
    wrapper = _make_wrapper(cap=0.40, window_bars=90)

    # Simulate time: bar 0 is t=0; trades close at bars 0-4
    # Symbol A: 5 trades at +10 PnL each → rolling A_pnl = +50, portfolio_pnl = +50 → share = 1.0
    for i in range(5):
        trade = _make_trade(
            symbol="BCHUSDT",
            open_time=i * bar_ms,
            close_time=(i + 1) * bar_ms,
            weighted_pnl=10.0,
        )
        wrapper.record_trade_result(trade)

    # 6th signal at bar 6: A share = 50/50 = 1.0 > 0.40 → scale = 0.40/1.0 = 0.40
    # Inner weight=100, vol_scale disabled → effective weight = max(1, round(100*0.40)) = 40
    sig = wrapper.get_signal("BCHUSDT", 6 * bar_ms)
    assert sig.direction == 1, "Signal direction should be preserved by cap"
    # cap/share = 0.40/1.0 = 0.40 → weight = max(1, round(100 * 0.40)) = 40
    assert sig.weight == 40, f"Expected weight=40 under cap (got {sig.weight})"

    # Verify cap_fires counter incremented
    stats = wrapper._gate_stats.get("BCHUSDT")
    assert stats is not None
    assert stats.cap_fires == 1, f"Expected 1 cap fire, got {stats.cap_fires}"


# ---------------------------------------------------------------------------
# Test 2: cap does NOT fire when share < 0.40
# ---------------------------------------------------------------------------


def test_per_symbol_cap_no_fire_below_threshold() -> None:
    """Symbol A and B share portfolio roughly 60/40; neither exceeds cap alone."""
    bar_ms = 28_800_000
    wrapper = _make_wrapper(cap=0.40, window_bars=90)

    # Symbol A: 2 trades at +10 = 20; Symbol B: 3 trades at +10 = 30 → total 50
    # A share = 20/50 = 0.40 (at boundary, not strictly > 0.40 → should NOT fire)
    for i in range(2):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))
    for i in range(2, 5):
        wrapper.record_trade_result(_make_trade("LDOUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))

    # Signal for BCHUSDT: share = 20/50 = 0.40 (not strictly > 0.40) → scale = 1.0
    sig = wrapper.get_signal("BCHUSDT", 6 * bar_ms)
    assert sig.weight == 100, f"Expected weight=100 (no cap), got {sig.weight}"

    stats = wrapper._gate_stats.get("BCHUSDT")
    assert stats is not None
    assert stats.cap_fires == 0, f"Expected 0 cap fires, got {stats.cap_fires}"


# ---------------------------------------------------------------------------
# Test 3: scaling magnitude (0.5x when share = 0.80 and cap = 0.40)
# ---------------------------------------------------------------------------


def test_per_symbol_cap_scaling_magnitude() -> None:
    """Verify scaling = cap / share = 0.40 / 0.80 = 0.50 when share = 80%."""
    bar_ms = 28_800_000
    wrapper = _make_wrapper(cap=0.40, window_bars=90)

    # Symbol A: 4 trades at +10 = 40; Symbol B: 1 trade at +10 = 10 → total 50
    # A share = 40/50 = 0.80 → scale = 0.40/0.80 = 0.50
    for i in range(4):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))
    wrapper.record_trade_result(_make_trade("LDOUSDT", 4 * bar_ms, 5 * bar_ms, 10.0))

    sig = wrapper.get_signal("BCHUSDT", 6 * bar_ms)
    # scale = 0.40/0.80 = 0.50 → weight = max(1, round(100 * 0.50)) = 50
    assert sig.weight == 50, f"Expected weight=50 (scale=0.5), got {sig.weight}"

    stats = wrapper._gate_stats.get("BCHUSDT")
    assert stats is not None
    assert stats.cap_fires == 1


# ---------------------------------------------------------------------------
# Test 4: past-only — current trade NOT in its own denominator (Critic Check 1)
# ---------------------------------------------------------------------------


def test_per_symbol_cap_past_only() -> None:
    """Rolling window uses STRICTLY past closed trades (close_time < open_time of signal).

    Scenario: 5 trades for Symbol A close at bars 1-5 with +10 each.
    Signal emitted at bar 6. The signal's own future trade (bar 6) is NOT in the window.
    If bar 6's trade were incorrectly included, the denominator would be 60, not 50.
    """
    bar_ms = 28_800_000
    wrapper = _make_wrapper(cap=0.40, window_bars=90)

    # 5 past trades close before bar 6
    for i in range(5):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))
    # Now inject a synthetic Symbol B trade to make total portfolio PnL = 60
    # If only past trades are used: A=50, B=10, total=60, share=50/60=0.833>0.40
    # If the current signal's trade (not yet closed) were included: A=60/70=0.857 (wrong)
    wrapper.record_trade_result(_make_trade("LDOUSDT", 0, 1 * bar_ms, 10.0))

    # Signal at bar 6: A=50, B=10, total=60, share=50/60=0.833
    # scale = 0.40 / 0.833 = 0.48 → weight = max(1, round(100 * 0.48)) = 48
    sig_bar6 = wrapper.get_signal("BCHUSDT", 6 * bar_ms)
    # The cap should reflect ONLY past trades, not any hypothetical future trade
    expected_share = 50.0 / 60.0
    expected_scale = 0.40 / expected_share
    expected_weight = max(1, round(100 * expected_scale))
    assert sig_bar6.weight == expected_weight, (
        f"Past-only violation: expected weight={expected_weight}, got {sig_bar6.weight}. "
        f"If current trade were included, weight would differ (look-ahead bug)."
    )


# ---------------------------------------------------------------------------
# Test 5: disabled by default — weight unchanged (backward compatibility)
# ---------------------------------------------------------------------------


def test_per_symbol_cap_disabled_by_default() -> None:
    """With enable_per_symbol_cap=False, weight_factor is unchanged from inner strategy."""
    wrapper = _make_wrapper(enable=False)
    bar_ms = 28_800_000

    # Feed trades that would trigger the cap if enabled
    for i in range(10):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))

    sig = wrapper.get_signal("BCHUSDT", 11 * bar_ms)
    # Cap disabled → weight = inner strategy's weight = 100 (unscaled)
    assert sig.weight == 100, f"Expected weight=100 with cap disabled, got {sig.weight}"

    # No cap_fires should be recorded
    stats = wrapper._gate_stats.get("BCHUSDT")
    if stats is not None:
        assert stats.cap_fires == 0


# ---------------------------------------------------------------------------
# Test 6: rolling window correctness — old trades expire
# ---------------------------------------------------------------------------


def test_per_symbol_cap_rolling_window() -> None:
    """Trades older than window_bars should be expired from the rolling sum."""
    bar_ms = 28_800_000
    window_bars = 5  # tiny window for test speed
    wrapper = _make_wrapper(cap=0.40, window_bars=window_bars)

    # Trades at bars 0-4 (all in window initially)
    for i in range(5):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, 10.0))
    # Inject Symbol B trades in same window
    wrapper.record_trade_result(_make_trade("LDOUSDT", 0, 1 * bar_ms, 10.0))

    # Signal at bar 10 (5 bars after last BCHUSDT trade → within window)
    # window_start = 10*bar - 5*bar = 5*bar
    # BCHUSDT close_times: bars 1-5 → close_time > window_start (5*bar) only bars 5 (=5*bar)
    # close_time at bar 5 = 5*bar_ms; window_start = 5*bar_ms → close_time >= window_start
    # Per code: expire entries with close_time < window_start_ms
    # window_start_ms = 10 * bar_ms - 5 * bar_ms = 5 * bar_ms
    # Entries with close_time < 5*bar_ms: i=0(ct=1bar), i=1(ct=2bar), i=2(ct=3bar), i=3(ct=4bar)
    # → 4 BCHUSDT entries expire; only i=4 (ct=5bar) remains in window → BCH PnL=10
    # LDOUSDT entry (ct=1bar) expires → LDO PnL=0
    # portfolio_pnl = 10; sym_pnl = 10; share = 1.0 > 0.40 → cap fires

    sig_bar10 = wrapper.get_signal("BCHUSDT", 10 * bar_ms)
    # All BCHUSDT trades except last expired; LDO expired too → share=10/10=1.0 → fires
    assert sig_bar10.weight < 100, (
        f"Expected cap to fire at bar 10 (old trades expired, last BCH remains): "
        f"got weight={sig_bar10.weight}"
    )


# ---------------------------------------------------------------------------
# Test 7: GateStats cap_fires counter exists (import smoke test)
# ---------------------------------------------------------------------------


def test_gate_stats_cap_fires_field() -> None:
    """GateStats dataclass has the cap_fires field (Critic Check 4 verifier)."""
    g = GateStats()
    assert hasattr(g, "cap_fires"), "GateStats missing cap_fires field"
    assert g.cap_fires == 0


# ---------------------------------------------------------------------------
# Test 8: negative-share symbol is never capped (positive-share-only semantics)
# ---------------------------------------------------------------------------


def test_per_symbol_cap_negative_share_not_capped() -> None:
    """A symbol with negative rolling PnL should never be capped (self-limiting drag)."""
    bar_ms = 28_800_000
    wrapper = _make_wrapper(cap=0.40, window_bars=90)

    # Symbol A (BCH): losing trades → negative PnL
    for i in range(5):
        wrapper.record_trade_result(_make_trade("BCHUSDT", i * bar_ms, (i + 1) * bar_ms, -10.0))
    # Symbol B (TRX): winning trades → positive PnL, portfolio total negative
    wrapper.record_trade_result(_make_trade("TRXUSDT", 0, bar_ms, 5.0))

    # BCH has negative PnL → portfolio_pnl = -50 + 5 = -45 → portfolio <= 0 → no cap
    sig_bch = wrapper.get_signal("BCHUSDT", 6 * bar_ms)
    assert sig_bch.weight == 100, (
        f"Negative-share BCH should not be capped (portfolio_pnl<=0); got weight={sig_bch.weight}"
    )
    stats = wrapper._gate_stats.get("BCHUSDT")
    if stats is not None:
        assert stats.cap_fires == 0

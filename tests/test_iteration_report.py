"""Tests for iteration_report.py — SplitMetrics DSR integration."""

from crypto_trade.backtest_models import TradeResult
from crypto_trade.iteration_report import _compute_metrics


def _make_trade(
    close_time_ms: int,
    net_pnl_pct: float,
    open_offset_ms: int = 1_000_000,
) -> TradeResult:
    return TradeResult(
        symbol="BTCUSDT",
        direction=1,
        entry_price=100.0,
        exit_price=100.0 + net_pnl_pct,
        weight_factor=1.0,
        open_time=close_time_ms - open_offset_ms,
        close_time=close_time_ms,
        exit_reason="take_profit",
        pnl_pct=net_pnl_pct,
        fee_pct=0.0,
        net_pnl_pct=net_pnl_pct,
        weighted_pnl=net_pnl_pct,
    )


def _make_trades_sequence(pnls: list[float], start_day: int = 0) -> list[TradeResult]:
    """Create trades spaced 1 day apart starting at 2024-01-01 + start_day."""
    base_ms = 1_704_067_200_000  # 2024-01-01 UTC
    one_day_ms = 86_400_000
    return [_make_trade(base_ms + (start_day + i) * one_day_ms, p) for i, p in enumerate(pnls)]


class TestSplitMetricsDsr:
    def test_split_metrics_has_dsr_field(self):
        # Create trades with mixed winners/losers
        trades = _make_trades_sequence([1.0, -0.5, 2.0, -1.0, 1.5, -0.7, 0.8] * 3)
        m = _compute_metrics(trades)
        assert m is not None
        assert hasattr(m, "dsr")
        assert isinstance(m.dsr, float)

    def test_none_trades_returns_none(self):
        assert _compute_metrics([]) is None

    def test_default_n_trials_gives_raw_tstat(self):
        # At n_trials=1, E[max]=0, so DSR = sharpe / se — a t-statistic
        trades = _make_trades_sequence([1.0, -0.5, 2.0, -1.0, 1.5, -0.7, 0.8] * 3)
        m = _compute_metrics(trades, n_trials=1)
        assert m is not None
        # DSR should be positive for a profitable strategy (sharpe > 0)
        assert m.dsr > 0
        # sharpe / dsr ≈ SE(Sharpe); should be finite
        assert abs(m.dsr) < 100

    def test_large_n_trials_penalizes_dsr(self):
        trades = _make_trades_sequence([1.0, -0.5, 2.0, -1.0, 1.5, -0.7, 0.8] * 3)
        m_n1 = _compute_metrics(trades, n_trials=1)
        m_n100 = _compute_metrics(trades, n_trials=100)
        assert m_n1 is not None and m_n100 is not None
        assert m_n100.dsr < m_n1.dsr  # multi-testing penalty reduces DSR

    def test_sharpe_unchanged_by_n_trials(self):
        # n_trials only affects DSR, not raw Sharpe
        trades = _make_trades_sequence([1.0, -0.5, 2.0, -1.0, 1.5] * 5)
        m_a = _compute_metrics(trades, n_trials=1)
        m_b = _compute_metrics(trades, n_trials=100)
        assert m_a is not None and m_b is not None
        assert m_a.sharpe == m_b.sharpe
        assert m_a.sortino == m_b.sortino
        assert m_a.max_drawdown == m_b.max_drawdown

"""Smoke tests for iter-v1/019: ETH-only + direction-aware BTC-trend gate.

Tests verify:
1. V1_ITER019_UNIVERSE is exactly {"ETHUSDT"} — F-AXIS-MECHANISM #1 precondition.
2. Gate constants match brief Section 3.3 pinned values.
3. ETHUSDT is not in V1_EXCLUDED_SYMBOLS — dispatch guard won't false-positive.
4. assert_v1_universe() accepts {ETHUSDT} — universe check passes.
5. /019 dispatch condition fires correctly (set equality) and does NOT fire for baseline/017/018.
6. BTC-trend filter imports resolve (risk_v2 cross-track import is accessible).
7. Gate constants are frozen: LOOKBACK_BARS=42, THRESHOLD_PCT=8.0, ENABLED=True.
"""

from __future__ import annotations

import pytest

from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS, assert_v1_universe


class TestIter019Universe:
    """V1_ITER019_UNIVERSE must be exactly ("ETHUSDT",)."""

    def test_iter019_universe_is_ethusdt_only(self) -> None:
        from run_baseline_v1 import V1_ITER019_UNIVERSE

        assert set(V1_ITER019_UNIVERSE) == {"ETHUSDT"}

    def test_iter019_universe_tuple_length(self) -> None:
        from run_baseline_v1 import V1_ITER019_UNIVERSE

        assert len(V1_ITER019_UNIVERSE) == 1

    def test_ethusdt_not_excluded(self) -> None:
        """ETHUSDT must not be in V1_EXCLUDED_SYMBOLS — assert_v1_universe guard."""
        assert "ETHUSDT" not in V1_EXCLUDED_SYMBOLS

    def test_assert_v1_universe_accepts_iter019(self) -> None:
        """assert_v1_universe() must accept {ETHUSDT} without raising."""
        from run_baseline_v1 import V1_ITER019_UNIVERSE

        # Should not raise
        assert_v1_universe(V1_ITER019_UNIVERSE)


class TestIter019GateConstants:
    """Gate constants must match brief Section 3.3 pinned values (frozen for /019)."""

    def test_lookback_bars_frozen_at_42(self) -> None:
        from run_baseline_v1 import V1_ITER019_BTC_GATE_LOOKBACK_BARS

        # 42 bars = 14 days at 8h cadence; frozen per LM Master §6.4
        assert V1_ITER019_BTC_GATE_LOOKBACK_BARS == 42

    def test_threshold_pct_frozen_at_8(self) -> None:
        from run_baseline_v1 import V1_ITER019_BTC_GATE_THRESHOLD_PCT

        # +-8% on BTC 14d return; EDA best IS lift (+42.47%); frozen per brief §3.3
        assert V1_ITER019_BTC_GATE_THRESHOLD_PCT == pytest.approx(8.0)

    def test_gate_enabled_by_default(self) -> None:
        from run_baseline_v1 import V1_ITER019_BTC_GATE_ENABLED

        assert V1_ITER019_BTC_GATE_ENABLED is True


class TestIter019DispatchCondition:
    """Dispatch elif condition set(symbols) == set(V1_ITER019_UNIVERSE) fires correctly."""

    def test_iter019_dispatch_fires_for_ethusdt(self) -> None:
        from run_baseline_v1 import V1_ITER019_UNIVERSE

        symbols = ("ETHUSDT",)
        assert set(symbols) == set(V1_ITER019_UNIVERSE)

    def test_iter019_dispatch_does_not_fire_for_baseline(self) -> None:
        from run_baseline_v1 import V1_BASELINE_UNIVERSE, V1_ITER019_UNIVERSE

        assert set(V1_BASELINE_UNIVERSE) != set(V1_ITER019_UNIVERSE)

    def test_iter019_dispatch_does_not_fire_for_iter018(self) -> None:
        from run_baseline_v1 import V1_ITER018_UNIVERSE, V1_ITER019_UNIVERSE

        # LINK-only vs ETH-only — must not collide
        assert set(V1_ITER018_UNIVERSE) != set(V1_ITER019_UNIVERSE)

    def test_iter019_dispatch_does_not_fire_for_iter017(self) -> None:
        from run_baseline_v1 import V1_ITER017_UNIVERSE, V1_ITER019_UNIVERSE

        assert set(V1_ITER017_UNIVERSE) != set(V1_ITER019_UNIVERSE)

    def test_iter019_universe_is_subset_of_baseline(self) -> None:
        """ETHUSDT is in V1_BASELINE_UNIVERSE — parquet will exist for training."""
        from run_baseline_v1 import V1_BASELINE_UNIVERSE, V1_ITER019_UNIVERSE

        assert set(V1_ITER019_UNIVERSE).issubset(set(V1_BASELINE_UNIVERSE))


class TestIter019BtcFilterImport:
    """BTC-trend filter cross-track import must resolve without error."""

    def test_btc_trend_filter_config_importable(self) -> None:
        from crypto_trade.strategies.ml.risk_v2 import BtcTrendFilterConfig

        # Instantiate with iter-v1/019 pinned constants
        cfg = BtcTrendFilterConfig(lookback_bars=42, threshold_pct=8.0, enabled=True)
        assert cfg.lookback_bars == 42
        assert cfg.threshold_pct == pytest.approx(8.0)
        assert cfg.enabled is True

    def test_apply_btc_trend_filter_importable(self) -> None:
        from crypto_trade.strategies.ml.risk_v2 import apply_btc_trend_filter  # noqa: F401

    def test_load_btc_klines_for_filter_importable(self) -> None:
        from crypto_trade.strategies.ml.risk_v2 import load_btc_klines_for_filter  # noqa: F401

    def test_runner_imports_risk_v2_symbols(self) -> None:
        """run_baseline_v1.py module-level import of risk_v2 symbols must resolve."""
        # Importing run_baseline_v1 triggers the import block; if the cross-track
        # import is broken this will raise ImportError.
        import run_baseline_v1

        assert hasattr(run_baseline_v1, "BtcTrendFilterConfig")
        assert hasattr(run_baseline_v1, "apply_btc_trend_filter")
        assert hasattr(run_baseline_v1, "load_btc_klines_for_filter")

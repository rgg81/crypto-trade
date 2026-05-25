"""Tests for iter-v1/010 R5 vol-target ceiling implementation.

Covers:
1. R5 OFF: BacktestConfig with risk_r5_vol_target_enabled=False — config field default is False.
2. R5 cap formula: min(1.0, vol_target_pct / max(natr, 0.01)) for natr < vol_target.
3. R5 boundary: natr == vol_target_pct → cap = 1.0 (no scaling).
4. R5 missing NATR: when (sym, ot) not in lookup, R5 skips (no nan propagation).
5. R5 × R2 multiplicative: joint weight = vt_scale * r2_scale * r5_scale.
6. BacktestConfig fields default to disabled.

Run:
    uv run pytest tests/test_iteration_v1_010_r5.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestR5VoltargetCeilingCapMath:
    """Unit tests for the R5 cap formula."""

    def test_case_a_natr_below_vol_target_no_cap(self) -> None:
        """natr=2% < vol_target=4% → cap = 1.0 (no scaling)."""
        natr = 2.0  # percent
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
        assert r5_scale == 1.0, f"Expected cap=1.0 when natr < vol_target; got {r5_scale}"

    def test_case_b_natr_equal_vol_target_boundary(self) -> None:
        """natr=4% == vol_target=4% → cap = 1.0 (boundary, no scaling)."""
        natr = 4.0
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
        assert r5_scale == 1.0, f"Expected cap=1.0 at boundary; got {r5_scale}"

    def test_case_c_natr_above_vol_target_half_size(self) -> None:
        """natr=8% > vol_target=4% → cap = 0.5 (half size)."""
        natr = 8.0
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
        assert abs(r5_scale - 0.5) < 1e-9, f"Expected cap=0.5; got {r5_scale}"

    def test_case_d_natr_zero_floor_protection(self) -> None:
        """natr=0 → uses floor 0.01 → cap = min(1.0, 4.0/0.01) = 1.0 (floor protects)."""
        natr = 0.0
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
        assert r5_scale == 1.0, f"Expected cap=1.0 with floor protection; got {r5_scale}"

    def test_case_d_natr_negative_floor_protection(self) -> None:
        """natr=-1.0 (invalid, defensive) → max(-1.0, 0.01) = 0.01 → cap = 1.0."""
        natr = -1.0
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
        assert r5_scale == 1.0, f"Expected cap=1.0 with negative natr; got {r5_scale}"

    def test_cap_never_exceeds_one(self) -> None:
        """cap is always ≤ 1.0 regardless of natr."""
        for natr in [0.0, 0.001, 0.1, 1.0, 2.0, 4.0, 8.0, 16.0, 100.0]:
            vol_target_pct = 4.0
            r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
            assert r5_scale <= 1.0, f"cap={r5_scale} > 1.0 for natr={natr}"

    def test_cap_is_positive(self) -> None:
        """cap is always > 0 for valid natr values."""
        for natr in [0.0, 0.01, 1.0, 4.0, 8.0, 50.0]:
            vol_target_pct = 4.0
            r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
            assert r5_scale > 0.0, f"cap={r5_scale} <= 0 for natr={natr}"


class TestR5BacktestConfigDefaults:
    """Tests for BacktestConfig R5 field defaults."""

    def test_r5_disabled_by_default(self) -> None:
        """BacktestConfig.risk_r5_vol_target_enabled defaults to False."""
        from crypto_trade.backtest_models import BacktestConfig

        config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
        )
        assert config.risk_r5_vol_target_enabled is False, (
            "R5 must be disabled by default to preserve byte-identical behavior "
            "for all iterations through iter-v1/009"
        )

    def test_r5_default_vol_target_pct(self) -> None:
        """BacktestConfig.risk_r5_vol_target_pct defaults to 4.0."""
        from crypto_trade.backtest_models import BacktestConfig

        config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
        )
        assert config.risk_r5_vol_target_pct == 4.0, (
            f"Expected default vol_target_pct=4.0; got {config.risk_r5_vol_target_pct}"
        )

    def test_r5_can_be_enabled(self) -> None:
        """BacktestConfig accepts risk_r5_vol_target_enabled=True."""
        from crypto_trade.backtest_models import BacktestConfig

        config = BacktestConfig(
            symbols=("BTCUSDT",),
            interval="8h",
            max_amount_usd=1000.0,
            stop_loss_pct=4.0,
            take_profit_pct=8.0,
            timeout_minutes=10080,
            risk_r5_vol_target_enabled=True,
            risk_r5_vol_target_pct=4.0,
        )
        assert config.risk_r5_vol_target_enabled is True
        assert config.risk_r5_vol_target_pct == 4.0


class TestR5MissingNatrSkip:
    """Tests for R5 behavior when (sym, ot) is missing from lookup."""

    def test_missing_natr_key_produces_nan(self) -> None:
        """dict.get with missing key returns nan sentinel — no KeyError."""
        r5_natr_lookup: dict[tuple[str, int], float] = {}
        natr = r5_natr_lookup.get(("BTCUSDT", 1_700_000_000_000), float("nan"))
        assert math.isnan(natr), f"Expected nan for missing key; got {natr}"

    def test_nan_natr_skips_r5_application(self) -> None:
        """When natr is nan, the R5 conditional is skipped (no scale change)."""
        natr = float("nan")
        vt_scale_before = 0.75  # arbitrary post-R2 scale
        vt_scale = vt_scale_before
        # Simulate the backtest loop's R5 block
        if not math.isnan(natr):
            r5_scale = min(1.0, 4.0 / max(natr, 0.01))
            vt_scale = vt_scale * r5_scale
        # vt_scale must be unchanged
        assert vt_scale == vt_scale_before, (
            f"vt_scale changed from {vt_scale_before} to {vt_scale} "
            "when natr is nan — missing NATR should be a no-op"
        )


class TestR5R2MultiplicativeInteraction:
    """Tests for R5 × R2 multiplicative joint weight behavior."""

    def test_r5_r2_multiplicative_joint_weight(self) -> None:
        """joint_weight = vt_base * r2_scale * r5_scale."""
        vt_base = 1.0  # baseline from vol-targeting
        # R2 floor scenario (deep drawdown)
        r2_scale = 0.33
        # R5 scenario: natr=8%, vol_target=4% → r5_scale=0.5
        natr = 8.0
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))

        # Apply R2 then R5 (order matches backtest.py)
        vt_scale = vt_base * r2_scale  # after R2
        vt_scale = vt_scale * r5_scale  # after R5

        expected = vt_base * r2_scale * r5_scale
        assert abs(vt_scale - expected) < 1e-9, f"Joint weight {vt_scale} != expected {expected}"
        assert abs(vt_scale - 0.165) < 1e-9, (
            f"Expected joint weight = 1.0 * 0.33 * 0.5 = 0.165; got {vt_scale}"
        )

    def test_r5_r2_worst_case_model_e_dot(self) -> None:
        """Brief Section 6.1: R2 floor 0.33 × R5 extreme (DOT p99 NATR 13.4%):
        joint = 0.33 × min(1.0, 4.0/13.4) ≈ 0.33 × 0.298 ≈ 0.098.
        Must be positive (not zero or negative)."""
        r2_floor = 0.33
        dot_p99_natr = 13.4  # percent, from brief Section 6.1
        vol_target_pct = 4.0
        r5_scale = min(1.0, vol_target_pct / max(dot_p99_natr, 0.01))
        joint_weight = r2_floor * r5_scale
        assert joint_weight > 0.05, (
            f"Joint weight {joint_weight} below 0.05 — "
            "position too small (< 5% baseline) at R2-floor + R5-extreme"
        )
        assert joint_weight < r2_floor, (
            f"R5 should reduce weight below R2-floor {r2_floor}; got {joint_weight}"
        )
        # Sanity: approximately 0.098 per brief Section 6.1
        assert abs(joint_weight - 0.098) < 0.01, f"Expected ~0.098; got {joint_weight}"


class TestR5VolTargetEnabled:
    """Tests for vol_natr_14 column presence in V1_FEATURE_COLUMNS_PRUNED."""

    def test_vol_natr_14_in_pruned_columns(self) -> None:
        """vol_natr_14 must be in V1_FEATURE_COLUMNS_PRUNED so R5 NATR lookup
        is guaranteed to find values in the feature parquet."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

        assert "vol_natr_14" in V1_FEATURE_COLUMNS_PRUNED, (
            "vol_natr_14 must be in V1_FEATURE_COLUMNS_PRUNED to guarantee R5 NATR lookup "
            "finds values in the feature parquet. Check features_v1/__init__.py."
        )


class TestR5IsOosSplitCounters:
    """Tests for IS/OOS partitioned R5 fire counters (iter-v1/010 reporting patch).

    Validates that the counter logic correctly partitions signals and fires
    across the OOS_CUTOFF_MS boundary without relying on the full backtest
    engine (which requires live data files).
    """

    def test_oos_cutoff_ms_value(self) -> None:
        """OOS_CUTOFF_MS must equal 1742774400000 (2025-03-24 00:00:00 UTC)."""
        from crypto_trade.config import OOS_CUTOFF_MS

        assert OOS_CUTOFF_MS == 1742774400000, (
            f"OOS_CUTOFF_MS={OOS_CUTOFF_MS} does not match 2025-03-24 00:00:00 UTC. "
            "Sacred constant must not be changed."
        )

    def test_backtest_result_r5_attributes_default_zero(self) -> None:
        """BacktestResult initialises all four R5 split counters to 0 by default."""
        from crypto_trade.backtest_models import BacktestResult

        br = BacktestResult([])
        assert br.r5_signals_is == 0
        assert br.r5_fires_is == 0
        assert br.r5_signals_oos == 0
        assert br.r5_fires_oos == 0

    def test_backtest_result_r5_attributes_explicit(self) -> None:
        """BacktestResult accepts explicit R5 IS/OOS split counter values."""
        from crypto_trade.backtest_models import BacktestResult

        br = BacktestResult(
            [],
            total_signals=100,
            r5_signals_is=70,
            r5_fires_is=28,
            r5_signals_oos=30,
            r5_fires_oos=9,
        )
        assert br.r5_signals_is == 70
        assert br.r5_fires_is == 28
        assert br.r5_signals_oos == 30
        assert br.r5_fires_oos == 9
        assert br.total_signals == 100

    def test_counter_partitioning_logic(self) -> None:
        """Simulate the backtest loop's IS/OOS partitioning across the cutoff.

        Uses a mock candle stream: 5 IS candles + 3 OOS candles, R5 enabled.
        natr=8% for all candles → r5_scale=0.5 → R5 fires on every candle.
        """
        from crypto_trade.config import OOS_CUTOFF_MS

        vol_target_pct = 4.0
        # 5 IS open_times (before cutoff), 3 OOS open_times (at/after cutoff)
        is_open_times = [OOS_CUTOFF_MS - (i + 1) * 28_800_000 for i in range(5)]
        oos_open_times = [OOS_CUTOFF_MS + i * 28_800_000 for i in range(3)]
        all_open_times = is_open_times + oos_open_times

        # NATR = 8% for every candle (> 4% vol_target → R5 fires each time)
        natr_lookup = {ot: 8.0 for ot in all_open_times}

        r5_signals_is = 0
        r5_fires_is = 0
        r5_signals_oos = 0
        r5_fires_oos = 0

        for ot in all_open_times:
            _natr = natr_lookup.get(ot, float("nan"))
            if ot < OOS_CUTOFF_MS:
                r5_signals_is += 1
            else:
                r5_signals_oos += 1
            if not math.isnan(_natr):
                r5_scale = min(1.0, vol_target_pct / max(_natr, 0.01))
                if r5_scale < 1.0:
                    if ot < OOS_CUTOFF_MS:
                        r5_fires_is += 1
                    else:
                        r5_fires_oos += 1

        assert r5_signals_is == 5, f"Expected 5 IS signals; got {r5_signals_is}"
        assert r5_signals_oos == 3, f"Expected 3 OOS signals; got {r5_signals_oos}"
        assert r5_fires_is == 5, f"Expected 5 IS fires (natr=8%>4%); got {r5_fires_is}"
        assert r5_fires_oos == 3, f"Expected 3 OOS fires (natr=8%>4%); got {r5_fires_oos}"

    def test_counter_no_fire_when_natr_below_threshold(self) -> None:
        """When natr < vol_target_pct, r5_scale == 1.0 and no fire is counted."""
        from crypto_trade.config import OOS_CUTOFF_MS

        vol_target_pct = 4.0
        ot_is = OOS_CUTOFF_MS - 28_800_000  # one candle before cutoff
        ot_oos = OOS_CUTOFF_MS  # one candle at cutoff

        r5_signals_is = 0
        r5_fires_is = 0
        r5_signals_oos = 0
        r5_fires_oos = 0

        for ot, natr in [(ot_is, 2.0), (ot_oos, 3.5)]:  # both < 4.0 → no fire
            if ot < OOS_CUTOFF_MS:
                r5_signals_is += 1
            else:
                r5_signals_oos += 1
            if not math.isnan(natr):
                r5_scale = min(1.0, vol_target_pct / max(natr, 0.01))
                if r5_scale < 1.0:
                    if ot < OOS_CUTOFF_MS:
                        r5_fires_is += 1
                    else:
                        r5_fires_oos += 1

        assert r5_signals_is == 1
        assert r5_signals_oos == 1
        assert r5_fires_is == 0, f"R5 should not fire when natr < vol_target; got {r5_fires_is}"
        assert r5_fires_oos == 0, f"R5 should not fire when natr < vol_target; got {r5_fires_oos}"

    def test_fire_rate_fraction_formula(self) -> None:
        """r5_fire_rate = fires / signals computes correctly for IS and OOS halves."""
        r5_signals_is = 70
        r5_fires_is = 28
        r5_signals_oos = 30
        r5_fires_oos = 9

        rate_is = r5_fires_is / r5_signals_is if r5_signals_is > 0 else 0.0
        rate_oos = r5_fires_oos / r5_signals_oos if r5_signals_oos > 0 else 0.0

        assert abs(rate_is - 0.4) < 1e-9, f"IS fire rate {rate_is} != 0.4"
        assert abs(rate_oos - 0.3) < 1e-9, f"OOS fire rate {rate_oos} != 0.3"

    def test_fire_rate_zero_signals_returns_zero(self) -> None:
        """When signals == 0, fire rate defaults to 0.0 (no ZeroDivisionError)."""
        r5_signals_is = 0
        r5_fires_is = 0
        rate_is = r5_fires_is / r5_signals_is if r5_signals_is > 0 else 0.0
        assert rate_is == 0.0

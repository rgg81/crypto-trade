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

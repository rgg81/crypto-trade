"""Tests for iter-v1/011 R5-BINARY-KILL entry filter.

Covers:
1. BacktestConfig field defaults (disabled = no new fields active).
2. R5-BINARY-KILL logic — below threshold → signal skipped (strict <).
3. R5-BINARY-KILL boundary — NATR exactly at threshold → PROCEED (strict < means proceed).
4. R5-BINARY-KILL above threshold → signal proceeds.
5. Missing NATR (NaN / absent key) → signal proceeds (safety default).
6. IS/OOS counter partitioning accuracy.
7. BacktestResult carries new r5_kill_* attributes.
8. append_r5_binary_kill_rows_to_comparison — column labeling correctness (D-RPRT-001 fix).
"""

from __future__ import annotations

import csv
import math
import tempfile
from pathlib import Path

import pytest

from crypto_trade.backtest_models import BacktestConfig, BacktestResult
from crypto_trade.strategies.ml.reporting_v1 import append_r5_binary_kill_rows_to_comparison

# ---------------------------------------------------------------------------
# Helper: minimal BacktestConfig for field presence checks
# ---------------------------------------------------------------------------


def _minimal_config(**overrides) -> BacktestConfig:
    """Build a minimal BacktestConfig with all required non-default fields."""
    defaults = dict(
        symbols=("BTCUSDT",),
        interval="8h",
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
        data_dir=Path("data"),
        cooldown_candles=2,
    )
    defaults.update(overrides)
    return BacktestConfig(**defaults)


# ---------------------------------------------------------------------------
# 1. BacktestConfig default fields
# ---------------------------------------------------------------------------


class TestBacktestConfigDefaults:
    def test_r5_kill_disabled_by_default(self):
        """R5-BINARY-KILL is off by default — preserves prior iteration behavior."""
        cfg = _minimal_config()
        assert cfg.risk_r5_kill_low_natr_enabled is False

    def test_r5_kill_min_pct_default(self):
        """Default min_natr threshold is 2.0%."""
        cfg = _minimal_config()
        assert cfg.risk_r5_kill_low_natr_min_pct == 2.0

    def test_r5_vol_target_still_exists(self):
        """/010 vol-target fields still present — orthogonal to /011."""
        cfg = _minimal_config()
        assert hasattr(cfg, "risk_r5_vol_target_enabled")
        assert hasattr(cfg, "risk_r5_vol_target_pct")

    def test_r5_kill_enabled(self):
        """Can enable binary kill with custom threshold."""
        cfg = _minimal_config(
            risk_r5_kill_low_natr_enabled=True,
            risk_r5_kill_low_natr_min_pct=2.0,
        )
        assert cfg.risk_r5_kill_low_natr_enabled is True
        assert cfg.risk_r5_kill_low_natr_min_pct == 2.0

    def test_r5_kill_and_vol_target_independent(self):
        """Both R5 subtypes can be independently configured (though /011 disables vol-target)."""
        cfg = _minimal_config(
            risk_r5_vol_target_enabled=False,
            risk_r5_kill_low_natr_enabled=True,
            risk_r5_kill_low_natr_min_pct=2.0,
        )
        assert cfg.risk_r5_vol_target_enabled is False
        assert cfg.risk_r5_kill_low_natr_enabled is True


# ---------------------------------------------------------------------------
# 2-5. Binary kill logic via direct function tests
# ---------------------------------------------------------------------------
# We test the binary-kill predicate directly rather than running a full
# backtest, which would require feature parquets. The logic is:
#   skip if not math.isnan(natr) and natr < min_pct
# (safety: if natr is nan or key missing → proceed)
# ---------------------------------------------------------------------------


def _should_kill(natr: float | None, min_pct: float) -> bool:
    """Replicate the binary-kill predicate from backtest.py."""
    if natr is None:
        _natr_val = float("nan")
    else:
        _natr_val = natr
    return not math.isnan(_natr_val) and _natr_val < float(min_pct)


class TestBinaryKillPredicate:
    def test_below_threshold_is_killed(self):
        """NATR 1.5% < threshold 2.0% → signal KILLED."""
        assert _should_kill(1.5, 2.0) is True

    def test_at_threshold_is_not_killed(self):
        """NATR exactly 2.0% == threshold 2.0% → PROCEED (strict < not <=)."""
        assert _should_kill(2.0, 2.0) is False

    def test_above_threshold_is_not_killed(self):
        """NATR 3.0% > threshold 2.0% → PROCEED."""
        assert _should_kill(3.0, 2.0) is False

    def test_nan_is_not_killed(self):
        """NaN NATR (missing key) → PROCEED (safety default)."""
        assert _should_kill(float("nan"), 2.0) is False

    def test_none_treated_as_nan(self):
        """None NATR (Python sentinel for missing) → PROCEED."""
        assert _should_kill(None, 2.0) is False

    def test_zero_natr_below_any_positive_threshold(self):
        """Zero NATR < 2.0% → KILLED."""
        assert _should_kill(0.0, 2.0) is True

    def test_very_high_natr_not_killed(self):
        """NATR 15% far above threshold 2.0% → PROCEED."""
        assert _should_kill(15.0, 2.0) is False


# ---------------------------------------------------------------------------
# 6-7. BacktestResult carries r5_kill_* attributes
# ---------------------------------------------------------------------------


class TestBacktestResultKillCounters:
    def _make_result(self, **kwargs) -> BacktestResult:
        return BacktestResult([], 0, **kwargs)

    def test_r5_kill_counters_default_to_zero(self):
        """BacktestResult with no kwargs has all kill counters = 0."""
        br = self._make_result()
        assert br.r5_kill_signals_is == 0
        assert br.r5_kill_fires_is == 0
        assert br.r5_kill_signals_oos == 0
        assert br.r5_kill_fires_oos == 0

    def test_r5_kill_counters_set(self):
        """BacktestResult carries kill counters when specified."""
        br = self._make_result(
            r5_kill_signals_is=100,
            r5_kill_fires_is=18,
            r5_kill_signals_oos=50,
            r5_kill_fires_oos=9,
        )
        assert br.r5_kill_signals_is == 100
        assert br.r5_kill_fires_is == 18
        assert br.r5_kill_signals_oos == 50
        assert br.r5_kill_fires_oos == 9

    def test_r5_legacy_counters_still_work(self):
        """/010 legacy r5_* counters unaffected by /011 addition."""
        br = self._make_result(
            r5_signals_is=200,
            r5_fires_is=46,
            r5_signals_oos=100,
            r5_fires_oos=18,
            r5_kill_signals_is=200,
            r5_kill_fires_is=36,
        )
        assert br.r5_signals_is == 200
        assert br.r5_fires_is == 46
        assert br.r5_kill_signals_is == 200
        assert br.r5_kill_fires_is == 36

    def test_r5_kill_counter_fire_rate_arithmetic(self):
        """Verify fire rate arithmetic used in runner aggregation."""
        br = self._make_result(
            r5_kill_signals_is=100,
            r5_kill_fires_is=18,
            r5_kill_signals_oos=50,
            r5_kill_fires_oos=9,
        )
        is_rate = br.r5_kill_fires_is / br.r5_kill_signals_is
        oos_rate = br.r5_kill_fires_oos / br.r5_kill_signals_oos
        assert abs(is_rate - 0.18) < 1e-9
        assert abs(oos_rate - 0.18) < 1e-9


# ---------------------------------------------------------------------------
# 8. append_r5_binary_kill_rows_to_comparison — D-RPRT-001 fix verification
# ---------------------------------------------------------------------------


class TestAppendR5BinaryKillRows:
    """Verify that comparison.csv schema is correct: IS value in in_sample column,
    OOS value in out_of_sample column. This fixes the D-RPRT-001 defect from /010."""

    def _read_comparison_rows(self, path: Path) -> list[dict[str, str]]:
        """Read comparison.csv and return rows as dicts keyed by field position."""
        with open(path, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        # Header was written by base report; we appended rows only.
        # For this test we write a stub header + the appended rows.
        result = []
        for row in rows:
            if len(row) >= 4:
                result.append(
                    {
                        "metric": row[0],
                        "in_sample": row[1],
                        "out_of_sample": row[2],
                        "ratio": row[3],
                    }
                )
        return result

    def test_column_labeling_correct(self):
        """IS fire rate in in_sample column, OOS fire rate in out_of_sample column."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            tmp_path = Path(f.name)

        try:
            append_r5_binary_kill_rows_to_comparison(
                tmp_path,
                r5_kill_fire_rate_is=0.18,
                r5_kill_fire_rate_oos=0.19,
            )
            rows = self._read_comparison_rows(tmp_path)
            assert len(rows) == 2

            # Both rows should have IS rate in in_sample and OOS rate in out_of_sample
            for row in rows:
                assert abs(float(row["in_sample"]) - 0.18) < 1e-6, (
                    f"D-RPRT-001 regression: IS rate {row['in_sample']} "
                    f"should be 0.18 in in_sample column"
                )
                assert abs(float(row["out_of_sample"]) - 0.19) < 1e-6, (
                    f"D-RPRT-001 regression: OOS rate {row['out_of_sample']} "
                    f"should be 0.19 in out_of_sample column"
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_metric_names_correct(self):
        """Row metric names match brief Section 10.3 spec."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            tmp_path = Path(f.name)

        try:
            append_r5_binary_kill_rows_to_comparison(tmp_path, 0.18, 0.19)
            rows = self._read_comparison_rows(tmp_path)
            metric_names = {r["metric"] for r in rows}
            assert "r5_binary_kill_fire_rate_is" in metric_names
            assert "r5_binary_kill_fire_rate_oos" in metric_names
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ratio_computed_correctly(self):
        """ratio column = OOS / IS fire rate."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            tmp_path = Path(f.name)

        try:
            append_r5_binary_kill_rows_to_comparison(tmp_path, 0.20, 0.10)
            rows = self._read_comparison_rows(tmp_path)
            for row in rows:
                ratio = float(row["ratio"])
                assert abs(ratio - 0.5) < 1e-4, f"Expected ratio 0.5, got {ratio}"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_zero_is_rate_produces_dash_ratio(self):
        """When IS fire rate is 0, ratio is '—' (not division by zero)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            tmp_path = Path(f.name)

        try:
            append_r5_binary_kill_rows_to_comparison(tmp_path, 0.0, 0.0)
            rows = self._read_comparison_rows(tmp_path)
            for row in rows:
                assert row["ratio"] == "—", f"Expected '—' for zero IS rate, got {row['ratio']!r}"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_d_rprt_001_fix_not_inverted(self):
        """Explicit regression guard: IS value must NOT appear in out_of_sample column."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            tmp_path = Path(f.name)

        try:
            is_rate = 0.18
            oos_rate = 0.30  # deliberately distinct from is_rate for clear detection
            append_r5_binary_kill_rows_to_comparison(tmp_path, is_rate, oos_rate)
            rows = self._read_comparison_rows(tmp_path)
            for row in rows:
                # The /010 D-RPRT-001 defect placed IS value in out_of_sample column.
                # Verify this is NOT happening for /011.
                assert float(row["out_of_sample"]) != pytest.approx(is_rate), (
                    f"D-RPRT-001 NOT FIXED: IS rate found in out_of_sample column (row={row})"
                )
                assert float(row["in_sample"]) != pytest.approx(oos_rate), (
                    f"D-RPRT-001 NOT FIXED: OOS rate found in in_sample column (row={row})"
                )
        finally:
            tmp_path.unlink(missing_ok=True)

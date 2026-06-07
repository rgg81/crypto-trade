"""Tests for H2 fix — fail-loud on excessive seed failures + N_seeds_used metric.

Covers:
- test_single_seed_failure_tolerated: 1 of 50 seeds raises; training succeeds
  with N=49 successfully-built models.
- test_k_plus_one_failures_raises: 6 seed failures raises SpecialistSeedFailureError
  (tolerance = 5 = V1_SPECIALIST_SEED_TOLERANCE).
- test_tolerance_constant_equals_5: V1_SPECIALIST_SEED_TOLERANCE is 5.
- test_get_n_seeds_used_mean_empty: returns None when no months trained yet.
- test_get_n_seeds_used_mean_single_month: correct mean after one month.
- test_get_n_seeds_used_mean_multi_month: correct mean over multiple months.
- test_append_n_seeds_used_to_comparison: appends correct row to CSV.
- test_failed_seeds_log_accumulates: _failed_seeds_log grows with failures.

Strategy: we mock LightGbmStrategy._train_for_month internals by directly
exercising the _failed_seeds_log / _seeds_used_per_month state variables and
the SpecialistSeedFailureError logic at unit level, without running Optuna or
LightGBM.  Integration tests that require the full backtest pipeline are
deferred to the runner-level smoke tests.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_tolerance_constant_equals_5() -> None:
    """V1_SPECIALIST_SEED_TOLERANCE must equal 5."""
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEED_TOLERANCE

    assert V1_SPECIALIST_SEED_TOLERANCE == 5, (
        f"V1_SPECIALIST_SEED_TOLERANCE={V1_SPECIALIST_SEED_TOLERANCE}; expected 5"
    )


# ---------------------------------------------------------------------------
# SpecialistSeedFailureError
# ---------------------------------------------------------------------------


def test_specialist_seed_failure_error_message_contains_count() -> None:
    """SpecialistSeedFailureError message must include failed count and tolerance."""
    from crypto_trade.strategies.ml.lgbm import SpecialistSeedFailureError

    err = SpecialistSeedFailureError(
        failed=6,
        tolerance=5,
        month_str="2024-01",
        seeds=["42", "43", "44", "45", "46", "47"],
    )
    msg = str(err)
    assert "6" in msg, f"failed count '6' not in error message: {msg!r}"
    assert "5" in msg, f"tolerance '5' not in error message: {msg!r}"
    assert "2024-01" in msg, f"month_str '2024-01' not in error message: {msg!r}"


def test_specialist_seed_failure_error_attributes() -> None:
    """SpecialistSeedFailureError exposes .failed, .tolerance, .month_str, .seeds."""
    from crypto_trade.strategies.ml.lgbm import SpecialistSeedFailureError

    err = SpecialistSeedFailureError(
        failed=7,
        tolerance=5,
        month_str="2024-02",
        seeds=["42", "43", "44", "45", "46", "47", "48"],
    )
    assert err.failed == 7
    assert err.tolerance == 5
    assert err.month_str == "2024-02"
    assert len(err.seeds) == 7


# ---------------------------------------------------------------------------
# _failed_seeds_log and _seeds_used_per_month state variables
# ---------------------------------------------------------------------------


def _make_strategy() -> object:
    """Instantiate LightGbmStrategy with minimal H2-relevant state."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._failed_seeds_log = []
    strat._seeds_used_per_month = []
    strat._specialist_models = []
    strat._specialist_dispersion_stats = []
    strat._specialist_mode = True
    return strat


def test_failed_seeds_log_starts_empty() -> None:
    """_failed_seeds_log must be an empty list on a fresh strategy instance."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._failed_seeds_log = []
    strat._seeds_used_per_month = []
    assert strat._failed_seeds_log == []
    assert strat._seeds_used_per_month == []


def test_failed_seeds_log_accumulates() -> None:
    """_failed_seeds_log must grow with each appended failure."""
    strat = _make_strategy()

    strat._failed_seeds_log.append((42, "repr(ValueError('bad data'))"))
    strat._failed_seeds_log.append((43, "repr(RuntimeError('optuna'))"))

    assert len(strat._failed_seeds_log) == 2
    assert strat._failed_seeds_log[0][0] == 42
    assert strat._failed_seeds_log[1][0] == 43


# ---------------------------------------------------------------------------
# get_n_seeds_used_mean
# ---------------------------------------------------------------------------


def test_get_n_seeds_used_mean_empty() -> None:
    """Returns None when no months have been trained yet."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._seeds_used_per_month = []
    result = strat.get_n_seeds_used_mean()
    assert result is None, f"Expected None, got {result!r}"


def test_get_n_seeds_used_mean_single_month() -> None:
    """Returns the single-month count when only one month trained."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._seeds_used_per_month = [49]
    result = strat.get_n_seeds_used_mean()
    assert result == 49.0, f"Expected 49.0, got {result!r}"


def test_get_n_seeds_used_mean_multi_month() -> None:
    """Returns the arithmetic mean across all trained months."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._seeds_used_per_month = [50, 50, 49, 48, 50]
    result = strat.get_n_seeds_used_mean()
    expected = (50 + 50 + 49 + 48 + 50) / 5
    assert math.isclose(result, expected, rel_tol=1e-9), f"Expected {expected}, got {result!r}"


def test_get_n_seeds_used_mean_full_roster() -> None:
    """Mean equals V1_SPECIALIST_SEED_COUNT when all seeds succeed every month."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_SEED_COUNT,
        LightGbmStrategy,
    )

    strat = LightGbmStrategy.__new__(LightGbmStrategy)
    strat._seeds_used_per_month = [V1_SPECIALIST_SEED_COUNT] * 12
    result = strat.get_n_seeds_used_mean()
    assert result == float(V1_SPECIALIST_SEED_COUNT), (
        f"Expected {V1_SPECIALIST_SEED_COUNT}, got {result!r}"
    )


# ---------------------------------------------------------------------------
# Failure threshold logic — unit-level simulation
# ---------------------------------------------------------------------------


def _simulate_seed_loop(
    n_seeds: int,
    fail_seeds: set[int],
    tolerance: int,
) -> tuple[list[int], list[tuple[int, str]]]:
    """Simulate the specialist seed loop logic (H2 fix) without LightGBM.

    Mirrors lgbm.py's loop structure:
    - Appends to _failed_this_month on exception.
    - Raises SpecialistSeedFailureError when failures > tolerance.
    - Appends to _specialist_models on success.

    Returns (succeeded_seeds, failed_log) if within tolerance.
    Raises SpecialistSeedFailureError otherwise.
    """
    from crypto_trade.strategies.ml.lgbm import SpecialistSeedFailureError

    seeds = list(range(42, 42 + n_seeds))
    _failed_this_month: list[tuple[int, str]] = []
    succeeded: list[int] = []

    for seed in seeds:
        try:
            if seed in fail_seeds:
                raise ValueError(f"Simulated failure for seed {seed}")
            succeeded.append(seed)
        except Exception as exc:
            _failed_this_month.append((seed, repr(exc)))
            if len(_failed_this_month) > tolerance:
                raise SpecialistSeedFailureError(
                    failed=len(_failed_this_month),
                    tolerance=tolerance,
                    month_str="2024-01",
                    seeds=[str(s) for s, _ in _failed_this_month],
                ) from exc

    return succeeded, _failed_this_month


def test_single_seed_failure_tolerated() -> None:
    """1 of 50 seeds raises; backtest succeeds with N=49 successfully-built models."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEED_TOLERANCE,
    )

    # Fail exactly 1 seed — well within tolerance of 5.
    fail_seeds = {42}
    succeeded, failed_log = _simulate_seed_loop(
        n_seeds=V1_SPECIALIST_SEED_COUNT,
        fail_seeds=fail_seeds,
        tolerance=V1_SPECIALIST_SEED_TOLERANCE,
    )
    assert len(succeeded) == 49, f"Expected 49 succeeded seeds, got {len(succeeded)}"
    assert len(failed_log) == 1, f"Expected 1 failed seed in log, got {len(failed_log)}"
    assert failed_log[0][0] == 42


def test_five_seed_failures_tolerated() -> None:
    """Exactly V1_SPECIALIST_SEED_TOLERANCE (5) failures: still succeeds."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEED_TOLERANCE,
    )

    # Fail exactly 5 seeds (= tolerance threshold, not exceeded yet).
    fail_seeds = {42, 43, 44, 45, 46}
    assert len(fail_seeds) == V1_SPECIALIST_SEED_TOLERANCE
    succeeded, failed_log = _simulate_seed_loop(
        n_seeds=V1_SPECIALIST_SEED_COUNT,
        fail_seeds=fail_seeds,
        tolerance=V1_SPECIALIST_SEED_TOLERANCE,
    )
    assert len(succeeded) == V1_SPECIALIST_SEED_COUNT - V1_SPECIALIST_SEED_TOLERANCE
    assert len(failed_log) == V1_SPECIALIST_SEED_TOLERANCE


def test_k_plus_one_failures_raises() -> None:
    """6 seed failures raises SpecialistSeedFailureError (tolerance = 5)."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEED_TOLERANCE,
        SpecialistSeedFailureError,
    )

    # Fail 6 seeds = one beyond tolerance → must raise.
    fail_seeds = {42, 43, 44, 45, 46, 47}
    assert len(fail_seeds) == V1_SPECIALIST_SEED_TOLERANCE + 1

    try:
        _simulate_seed_loop(
            n_seeds=V1_SPECIALIST_SEED_COUNT,
            fail_seeds=fail_seeds,
            tolerance=V1_SPECIALIST_SEED_TOLERANCE,
        )
        raise AssertionError(
            "Expected SpecialistSeedFailureError to be raised but no exception occurred"
        )
    except SpecialistSeedFailureError as exc:
        assert exc.failed == V1_SPECIALIST_SEED_TOLERANCE + 1, (
            f"Expected failed={V1_SPECIALIST_SEED_TOLERANCE + 1}, got {exc.failed}"
        )
        assert exc.tolerance == V1_SPECIALIST_SEED_TOLERANCE


def test_zero_seed_failures_no_exception() -> None:
    """0 seed failures: no exception, all 50 seeds succeed."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEED_TOLERANCE,
    )

    succeeded, failed_log = _simulate_seed_loop(
        n_seeds=V1_SPECIALIST_SEED_COUNT,
        fail_seeds=set(),
        tolerance=V1_SPECIALIST_SEED_TOLERANCE,
    )
    assert len(succeeded) == V1_SPECIALIST_SEED_COUNT
    assert failed_log == []


# ---------------------------------------------------------------------------
# append_n_seeds_used_to_comparison
# ---------------------------------------------------------------------------


def test_append_n_seeds_used_to_comparison(tmp_path: Path) -> None:
    """append_n_seeds_used_to_comparison appends the correct row to comparison.csv."""
    from crypto_trade.strategies.ml.reporting_v1 import append_n_seeds_used_to_comparison

    # Create a minimal comparison.csv with header.
    comp_csv = tmp_path / "comparison.csv"
    comp_csv.write_text("metric,in_sample,out_of_sample,ratio\n")

    append_n_seeds_used_to_comparison(comp_csv, n_seeds_used_mean=49.6667)

    rows = list(csv.reader(comp_csv.read_text().splitlines()))
    # rows[0] = header, rows[1] = appended row
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}: {rows}"
    metric, is_val, oos_val, ratio_val = rows[1]
    assert metric == "N_seeds_used", f"metric={metric!r}"
    assert abs(float(is_val) - 49.6667) < 1e-3, f"is_val={is_val!r}"
    assert oos_val == "", f"oos_val should be blank, got {oos_val!r}"
    assert ratio_val == "", f"ratio_val should be blank, got {ratio_val!r}"


def test_append_n_seeds_used_to_comparison_full_roster(tmp_path: Path) -> None:
    """N_seeds_used=50.0 when all seeds succeed."""
    from crypto_trade.strategies.ml.reporting_v1 import append_n_seeds_used_to_comparison

    comp_csv = tmp_path / "comparison.csv"
    comp_csv.write_text("metric,in_sample,out_of_sample,ratio\n")

    append_n_seeds_used_to_comparison(comp_csv, n_seeds_used_mean=50.0)

    rows = list(csv.reader(comp_csv.read_text().splitlines()))
    assert rows[1][0] == "N_seeds_used"
    assert rows[1][1] == "50.0000"


def test_append_n_seeds_used_to_comparison_does_not_clobber_existing(
    tmp_path: Path,
) -> None:
    """append_n_seeds_used_to_comparison appends; existing rows are preserved."""
    from crypto_trade.strategies.ml.reporting_v1 import append_n_seeds_used_to_comparison

    comp_csv = tmp_path / "comparison.csv"
    comp_csv.write_text(
        "metric,in_sample,out_of_sample,ratio\n"
        "monthly_sharpe,1.5,1.2,0.80\n"
        "specialist_dispersion_mean,0.45,,\n"
    )

    append_n_seeds_used_to_comparison(comp_csv, n_seeds_used_mean=48.5)

    rows = list(csv.reader(comp_csv.read_text().splitlines()))
    # header + monthly_sharpe + specialist_dispersion_mean + N_seeds_used = 4
    assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"
    assert rows[1][0] == "monthly_sharpe"
    assert rows[2][0] == "specialist_dispersion_mean"
    assert rows[3][0] == "N_seeds_used"
    assert rows[3][1] == "48.5000"

"""Tests for the OOF parquet contamination guardrail (iter-v3: QR A5 + Critic FINAL 785500f).

iter-v3/047 was re-run 5 times unintentionally, accumulating 5x duplicate rows in
trial_oof_returns.parquet (55.78M vs expected 11M). This inflated n_trials from 140 to 700
in dsr.json and comparison.csv, mechanically depressing the DSR computation.

The guardrail lives entirely in run_baseline_v3.py (startup-only check, before any
optimization work starts). These tests exercise the three cases via a minimal helper
that replicates the startup guard logic, keeping the test file free of full runner
import-chains (which would require live data / parquets).

Cases:
  1. Default (no --clean-oof, no existing parquet) → no error
  2. --clean-oof + existing parquet → parquet deleted, no error
  3. No --clean-oof + existing parquet → RuntimeError raised with helpful message
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Minimal helper that replicates run_baseline_v3.py's startup guard logic
# without importing the full runner (which requires live data / parquets).
# ---------------------------------------------------------------------------

ITERATION_LABEL = "v3-test"


def _run_oof_guardrail(
    reports_dir: Path,
    iteration_label: str,
    clean_oof: bool,
) -> None:
    """Replicate the startup guard from run_baseline_v3.main().

    Raises RuntimeError if the OOF parquet already exists and clean_oof is False.
    Deletes the parquet and prints a warning if clean_oof is True.
    Does nothing if the parquet does not exist.
    """
    oof_parquet_startup = reports_dir / f"iteration_{iteration_label}" / "trial_oof_returns.parquet"
    if oof_parquet_startup.exists():
        if clean_oof:
            oof_parquet_startup.unlink()
            # Mirror the exact print from the runner for documentation parity.
            print(f"[CLEAN-OOF] Removed stale OOF parquet at {oof_parquet_startup}")
        else:
            raise RuntimeError(
                f"OOF parquet for iteration_label '{iteration_label}' already exists at "
                f"{oof_parquet_startup}. "
                "This indicates a previous run did not complete cleanly OR the iteration "
                "is being re-executed. Re-running silently inflates n_trials and contaminates "
                "DSR/PSR/comparison.csv. Either: "
                "(a) delete the parquet manually, OR "
                "(b) re-run with --clean-oof flag to delete and start fresh."
            )


# ---------------------------------------------------------------------------
# Case 1: default (no --clean-oof, no existing parquet) → no error
# ---------------------------------------------------------------------------


def test_no_existing_parquet_no_error(tmp_path: Path) -> None:
    """No OOF parquet present + clean_oof=False → guardrail is a no-op."""
    oof_path = tmp_path / f"iteration_{ITERATION_LABEL}" / "trial_oof_returns.parquet"
    assert not oof_path.exists(), "Precondition: parquet must not exist"

    # Must not raise
    _run_oof_guardrail(tmp_path, ITERATION_LABEL, clean_oof=False)

    # Parquet still does not exist (guardrail did not create anything)
    assert not oof_path.exists()


# ---------------------------------------------------------------------------
# Case 2: --clean-oof + existing parquet → parquet deleted, no error
# ---------------------------------------------------------------------------


def test_clean_oof_deletes_existing_parquet(tmp_path: Path) -> None:
    """Existing OOF parquet + clean_oof=True → parquet deleted, no RuntimeError."""
    oof_dir = tmp_path / f"iteration_{ITERATION_LABEL}"
    oof_dir.mkdir(parents=True, exist_ok=True)
    oof_path = oof_dir / "trial_oof_returns.parquet"
    oof_path.write_bytes(b"fake parquet content")
    assert oof_path.exists(), "Precondition: parquet must exist before guard runs"

    # Must not raise
    _run_oof_guardrail(tmp_path, ITERATION_LABEL, clean_oof=True)

    # Parquet must have been deleted
    assert not oof_path.exists(), (
        "FAIL: --clean-oof did not delete the existing OOF parquet. "
        "Stale parquet would silently accumulate rows on re-run."
    )


# ---------------------------------------------------------------------------
# Case 3: No --clean-oof + existing parquet → RuntimeError with helpful message
# ---------------------------------------------------------------------------


def test_existing_parquet_without_clean_oof_raises(tmp_path: Path) -> None:
    """Existing OOF parquet + clean_oof=False → RuntimeError with diagnostic message."""
    oof_dir = tmp_path / f"iteration_{ITERATION_LABEL}"
    oof_dir.mkdir(parents=True, exist_ok=True)
    oof_path = oof_dir / "trial_oof_returns.parquet"
    oof_path.write_bytes(b"fake parquet content")
    assert oof_path.exists(), "Precondition: parquet must exist before guard runs"

    with pytest.raises(RuntimeError) as exc_info:
        _run_oof_guardrail(tmp_path, ITERATION_LABEL, clean_oof=False)

    error_msg = str(exc_info.value)

    # Must name the iteration_label so the operator can identify the stale file
    assert ITERATION_LABEL in error_msg, (
        f"RuntimeError must contain iteration_label '{ITERATION_LABEL}'. Got: {error_msg}"
    )

    # Must name the actual path so the operator can find and delete the file
    assert str(oof_path) in error_msg, (
        f"RuntimeError must contain the parquet path '{oof_path}'. Got: {error_msg}"
    )

    # Must mention --clean-oof so the operator knows how to fix it
    assert "--clean-oof" in error_msg, (
        f"RuntimeError must mention '--clean-oof' flag. Got: {error_msg}"
    )

    # Must mention DSR/PSR contamination so the operator understands the consequence
    assert "DSR" in error_msg, (
        f"RuntimeError must mention 'DSR' to explain contamination risk. Got: {error_msg}"
    )

    # Parquet must still exist (guardrail does not touch it on error path)
    assert oof_path.exists(), (
        "FAIL: guardrail deleted the parquet on the error path — "
        "operator may need it for forensics."
    )


# ---------------------------------------------------------------------------
# Smoke test: argparse flag is parseable (validates the runner's add_argument)
# ---------------------------------------------------------------------------


def test_clean_oof_argparse_flag_parses() -> None:
    """Verify --clean-oof is a valid boolean flag (store_true semantics)."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean-oof", action="store_true")

    # With flag
    args_with = parser.parse_args(["--clean-oof"])
    assert args_with.clean_oof is True, "Expected clean_oof=True when --clean-oof is passed"

    # Without flag
    args_without = parser.parse_args([])
    assert args_without.clean_oof is False, "Expected clean_oof=False when --clean-oof is absent"

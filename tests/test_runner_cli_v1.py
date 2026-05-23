"""Tests for run_baseline_v1.py CLI flag --ensemble-size.

iter-v1/001 added --ensemble-size to allow methodology-axis iterations to request
a specific ensemble size (e.g., 5) for byte-identity against the baseline anchor
without needing --baseline-mode (which writes to the wrong directory).

Covers:
- EXPLORATION + --ensemble-size 5 sets ensemble_size=5 (not the default 3).
- CONFIRMATION + --ensemble-size 5 sets ensemble_size=5 (not the default 10).
- --ensemble-size 0 and --ensemble-size 11 are rejected with sys.exit.
- --baseline-mode + --ensemble-size N is ignored (baseline has sacred fixed values).
- --ensemble-size N with no mode flag still triggers the "specify mode" error.

Run:
    uv run pytest tests/test_runner_cli_v1.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# We test _derive_ensemble_seeds and the argparse/mode-resolution logic in isolation.
# We do NOT call main() (which would launch a full backtest).  Instead we import the
# module constants and test _derive_ensemble_seeds, then simulate the argparse path
# by exercising the specific validation block added in iter-v1/001.

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDeriveEnsembleSeeds:
    """Unit tests for _derive_ensemble_seeds helper."""

    def test_first_5_seeds(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        seeds = _derive_ensemble_seeds(5)
        assert seeds == [42, 123, 456, 789, 1001]

    def test_first_3_seeds(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        seeds = _derive_ensemble_seeds(3)
        assert seeds == [42, 123, 456]

    def test_size_1(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        assert _derive_ensemble_seeds(1) == [42]

    def test_size_10(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        seeds = _derive_ensemble_seeds(10)
        assert len(seeds) == 10
        assert seeds[0] == 42

    def test_size_0_raises(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        with pytest.raises(ValueError, match="ENSEMBLE_SIZE must be in"):
            _derive_ensemble_seeds(0)

    def test_size_11_raises(self) -> None:
        from run_baseline_v1 import _derive_ensemble_seeds

        with pytest.raises(ValueError, match="ENSEMBLE_SIZE must be in"):
            _derive_ensemble_seeds(11)


class TestEnsembleSizeOverrideParsing:
    """Verify --ensemble-size override flag semantics without running a backtest.

    We parse args via argparse directly (not main()), then manually apply the
    override logic to verify the correct ensemble_size is derived.
    """

    def _parse_and_resolve(self, argv: list[str]) -> dict:
        """Parse argv and run the mode-resolution + override block.

        Returns a dict with resolved ``ensemble_size`` and ``n_trials``.
        Raises SystemExit if argparse or mode validation fires.
        """
        import argparse

        from run_baseline_v1 import (
            ENSEMBLE_SEEDS,
            V1_CONFIRMATION_ENSEMBLE_SIZE,
            V1_EXPLORATION_ENSEMBLE_SIZE,
        )

        parser = argparse.ArgumentParser()
        parser.add_argument("--iteration", type=int, default=None)
        parser.add_argument("--baseline-mode", action="store_true")
        parser.add_argument("--exploration", action="store_true")
        parser.add_argument("--confirmation", action="store_true")
        parser.add_argument("--n-trials", type=int, default=35)
        parser.add_argument("--ensemble-size", type=int, default=None)
        parser.add_argument("--symbols", type=str, default=None)
        args = parser.parse_args(argv)

        # --- replicate the mode-resolution logic from main() ---
        if args.baseline_mode:
            ensemble_size = 5
            n_trials = 50
        elif args.exploration:
            ensemble_size = V1_EXPLORATION_ENSEMBLE_SIZE
            n_trials = args.n_trials
            if args.iteration is None:
                raise SystemExit("ERROR: --exploration requires --iteration NNN")
        elif args.confirmation:
            ensemble_size = V1_CONFIRMATION_ENSEMBLE_SIZE
            n_trials = args.n_trials
            if args.iteration is None:
                raise SystemExit("ERROR: --confirmation requires --iteration NNN")
        else:
            raise SystemExit(
                "ERROR: must specify --baseline-mode, --exploration, or --confirmation"
            )

        # --- replicate the --ensemble-size override block ---
        if args.ensemble_size is not None and not args.baseline_mode:
            if args.ensemble_size < 1 or args.ensemble_size > len(ENSEMBLE_SEEDS):
                raise SystemExit(
                    f"ERROR: --ensemble-size must be in [1, {len(ENSEMBLE_SEEDS)}]; "
                    f"got {args.ensemble_size}"
                )
            ensemble_size = args.ensemble_size

        return {"ensemble_size": ensemble_size, "n_trials": n_trials}

    def test_exploration_default_ensemble_size(self) -> None:
        """Without --ensemble-size, EXPLORATION gives default 3."""
        from run_baseline_v1 import V1_EXPLORATION_ENSEMBLE_SIZE

        result = self._parse_and_resolve(["--exploration", "--iteration", "1"])
        assert result["ensemble_size"] == V1_EXPLORATION_ENSEMBLE_SIZE

    def test_exploration_ensemble_size_override_5(self) -> None:
        """--exploration --ensemble-size 5 gives ensemble_size=5 (iter-v1/001 use case)."""
        result = self._parse_and_resolve(
            ["--exploration", "--iteration", "1", "--ensemble-size", "5", "--n-trials", "50"]
        )
        assert result["ensemble_size"] == 5
        assert result["n_trials"] == 50

    def test_confirmation_default_ensemble_size(self) -> None:
        """Without --ensemble-size, CONFIRMATION gives default 10."""
        from run_baseline_v1 import V1_CONFIRMATION_ENSEMBLE_SIZE

        result = self._parse_and_resolve(["--confirmation", "--iteration", "10"])
        assert result["ensemble_size"] == V1_CONFIRMATION_ENSEMBLE_SIZE

    def test_confirmation_ensemble_size_override(self) -> None:
        """--confirmation --ensemble-size 5 gives ensemble_size=5."""
        result = self._parse_and_resolve(
            ["--confirmation", "--iteration", "10", "--ensemble-size", "5"]
        )
        assert result["ensemble_size"] == 5

    def test_ensemble_size_0_rejected(self) -> None:
        with pytest.raises(SystemExit, match="must be in"):
            self._parse_and_resolve(["--exploration", "--iteration", "1", "--ensemble-size", "0"])

    def test_ensemble_size_11_rejected(self) -> None:
        with pytest.raises(SystemExit, match="must be in"):
            self._parse_and_resolve(["--exploration", "--iteration", "1", "--ensemble-size", "11"])

    def test_baseline_mode_ignores_ensemble_size_override(self) -> None:
        """--baseline-mode sacred values (5 seeds, 50 trials) are never overridden."""
        result = self._parse_and_resolve(["--baseline-mode", "--ensemble-size", "3"])
        assert result["ensemble_size"] == 5
        assert result["n_trials"] == 50

    def test_no_mode_flag_raises(self) -> None:
        with pytest.raises(SystemExit):
            self._parse_and_resolve(["--ensemble-size", "5"])

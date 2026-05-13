"""Regression tests for unified 10-seed ensemble architecture (iter-v3/059).

Three test groups:
  (A) ENSEMBLE_SEEDS lineage — first 5 seeds match _derive_ensemble_seeds(42, 5),
      last 5 match _derive_ensemble_seeds(123, 5).

  (B) ENSEMBLE_SIZE == 10 — module-level constant enforced at pre-flight time.

  (C) --seeds deprecation warning — _run_single_seed signature accepts
      ensemble_seeds_override; importing the runner module does not crash.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

# ---------------------------------------------------------------------------
# Load run_baseline_v3 module from the repo root (not installed as a package)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_runner() -> ModuleType:
    """Import run_baseline_v3 from repo root without executing main()."""
    module_path = str(REPO_ROOT)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    # Re-import to get the current state (handles repeated calls in the same session)
    if "run_baseline_v3" in sys.modules:
        del sys.modules["run_baseline_v3"]
    return importlib.import_module("run_baseline_v3")


# ---------------------------------------------------------------------------
# (A) ENSEMBLE_SEEDS lineage
# ---------------------------------------------------------------------------


class TestEnsembleSeedsLineage:
    """ENSEMBLE_SEEDS must exactly match the two-outer-seed derivation."""

    def test_first_five_match_outer_42(self) -> None:
        """ENSEMBLE_SEEDS[0:5] must equal _derive_ensemble_seeds(42, 5)."""
        runner = _load_runner()
        derived = runner._derive_ensemble_seeds(42, size=5)
        actual = list(runner.ENSEMBLE_SEEDS[:5])
        assert actual == derived, (
            f"ENSEMBLE_SEEDS[0:5] = {actual}\n"
            f"_derive_ensemble_seeds(42, 5) = {derived}\n"
            "Lineage mismatch — hardcoded seeds have drifted from the derivation function."
        )

    def test_last_five_match_outer_123(self) -> None:
        """ENSEMBLE_SEEDS[5:10] must equal _derive_ensemble_seeds(123, 5)."""
        runner = _load_runner()
        derived = runner._derive_ensemble_seeds(123, size=5)
        actual = list(runner.ENSEMBLE_SEEDS[5:])
        assert actual == derived, (
            f"ENSEMBLE_SEEDS[5:10] = {actual}\n"
            f"_derive_ensemble_seeds(123, 5) = {derived}\n"
            "Lineage mismatch — hardcoded seeds have drifted from the derivation function."
        )

    def test_ensemble_seeds_length(self) -> None:
        """ENSEMBLE_SEEDS must have exactly 10 elements."""
        runner = _load_runner()
        assert len(runner.ENSEMBLE_SEEDS) == 10, (
            f"Expected 10 seeds; got {len(runner.ENSEMBLE_SEEDS)}. "
            "ENSEMBLE_SEEDS must contain exactly 10 values (5 from outer=42 + 5 from outer=123)."
        )

    def test_all_seeds_positive_int(self) -> None:
        """All ENSEMBLE_SEEDS values must be positive integers in [0, 2^31-1]."""
        runner = _load_runner()
        for i, s in enumerate(runner.ENSEMBLE_SEEDS):
            assert isinstance(s, int), f"ENSEMBLE_SEEDS[{i}]={s!r} is not an int"
            assert 0 <= s < 2**31, (
                f"ENSEMBLE_SEEDS[{i}]={s} is out of [0, 2^31-1] range. "
                "Seeds must be in the np.random.default_rng integer domain."
            )

    def test_no_duplicate_seeds(self) -> None:
        """ENSEMBLE_SEEDS must have no duplicates (each seed produces a distinct model)."""
        runner = _load_runner()
        seeds = list(runner.ENSEMBLE_SEEDS)
        assert len(seeds) == len(set(seeds)), (
            f"ENSEMBLE_SEEDS contains duplicates: {seeds}. "
            "Duplicate seeds produce identical models, reducing ensemble diversity."
        )


# ---------------------------------------------------------------------------
# (B) ENSEMBLE_SIZE constant
# ---------------------------------------------------------------------------


class TestEnsembleSizeConstant:
    """ENSEMBLE_SIZE must equal 10 for the unified architecture."""

    def test_ensemble_size_is_10(self) -> None:
        """ENSEMBLE_SIZE module constant must be 10."""
        runner = _load_runner()
        assert runner.ENSEMBLE_SIZE == 10, (
            f"ENSEMBLE_SIZE={runner.ENSEMBLE_SIZE}. "
            "iter-v3/059 RE-ANCHOR #2 requires ENSEMBLE_SIZE=10. "
            "The outer-seed loop has been eliminated; the unified 10-seed inner "
            "ensemble is the only valid architecture."
        )

    def test_legacy_seeds_unchanged(self) -> None:
        """LEGACY_ENSEMBLE_SEEDS must remain [42, 123, 456, 789, 1001] for v1/v2 compat."""
        runner = _load_runner()
        assert runner.LEGACY_ENSEMBLE_SEEDS == [42, 123, 456, 789, 1001], (
            f"LEGACY_ENSEMBLE_SEEDS={runner.LEGACY_ENSEMBLE_SEEDS}. "
            "These must remain unchanged for backward compatibility with v1/v2 baselines."
        )


# ---------------------------------------------------------------------------
# (C) _derive_ensemble_seeds default size no longer uses ENSEMBLE_SIZE=10
# ---------------------------------------------------------------------------


class TestDeriveEnsembleSeedsDefault:
    """After the iter-v3/059 change, _derive_ensemble_seeds default size is 5.

    The function was used to derive 5 inner seeds per outer seed (one outer → 5 inner).
    Its default was changed from ENSEMBLE_SIZE (now 10) to 5 to preserve its
    semantic invariant and backward compatibility with test fixtures.
    """

    def test_derive_default_produces_five(self) -> None:
        """Calling _derive_ensemble_seeds with only outer_seed returns 5 seeds."""
        runner = _load_runner()
        seeds = runner._derive_ensemble_seeds(42)
        assert len(seeds) == 5, (
            f"_derive_ensemble_seeds(42) returned {len(seeds)} seeds; expected 5. "
            "The default size is 5 (historical per-outer-seed derivation)."
        )

    def test_derive_explicit_size_respected(self) -> None:
        """Explicit size= parameter is honoured."""
        runner = _load_runner()
        for size in (1, 3, 5, 10):
            seeds = runner._derive_ensemble_seeds(42, size=size)
            assert len(seeds) == size, (
                f"_derive_ensemble_seeds(42, size={size}) returned {len(seeds)} seeds; "
                f"expected {size}."
            )

    def test_derive_deterministic(self) -> None:
        """Same outer_seed and size always produces identical seed list."""
        runner = _load_runner()
        seeds_a = runner._derive_ensemble_seeds(123, size=5)
        seeds_b = runner._derive_ensemble_seeds(123, size=5)
        assert seeds_a == seeds_b, (
            "_derive_ensemble_seeds must be deterministic (same inputs → same output). "
            f"Got {seeds_a} vs {seeds_b}."
        )


# ---------------------------------------------------------------------------
# (D) _run_single_seed signature accepts ensemble_seeds_override
# ---------------------------------------------------------------------------


class TestRunSingleSeedSignature:
    """_run_single_seed must accept ensemble_seeds_override kwarg."""

    def test_signature_has_ensemble_seeds_override(self) -> None:
        """_run_single_seed must have ensemble_seeds_override in its signature."""
        import inspect

        runner = _load_runner()
        sig = inspect.signature(runner._run_single_seed)
        assert "ensemble_seeds_override" in sig.parameters, (
            "_run_single_seed is missing the ensemble_seeds_override parameter. "
            "iter-v3/059 requires this parameter for the unified ensemble call."
        )

    def test_ensemble_seeds_override_default_none(self) -> None:
        """ensemble_seeds_override must default to None for backward compat."""
        import inspect

        runner = _load_runner()
        sig = inspect.signature(runner._run_single_seed)
        param = sig.parameters["ensemble_seeds_override"]
        assert param.default is None, (
            f"ensemble_seeds_override default is {param.default!r}; expected None. "
            "The default must be None so existing EXPLORATION callers (which pass no "
            "override) continue to use _derive_ensemble_seeds(seed, size=1)."
        )


# ---------------------------------------------------------------------------
# (E) cpcv_frac_positive_paths gate in dsr.json
# ---------------------------------------------------------------------------


class TestCpcvGateThreshold:
    """_CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD must equal 0.55."""

    def test_gate_threshold_value(self) -> None:
        """Gate threshold must be exactly 0.55."""
        runner = _load_runner()
        thr = runner._CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD
        assert abs(thr - 0.55) < 1e-9, (
            f"_CPCV_FRAC_POSITIVE_PATHS_GATE_THRESHOLD={thr}; expected 0.55. "
            "This is the formal Gate 10 replacement threshold per iter-v3/059 design."
        )

    def test_write_dsr_json_includes_gate_fields(self, tmp_path: Path) -> None:
        """_write_dsr_json must write cpcv_frac_positive_paths_gate_pass and threshold."""
        import json

        runner = _load_runner()

        # Build a minimal PBOResult-like namedtuple / object.
        # The actual PBOResult is imported from validation_v3.
        from crypto_trade.strategies.ml.validation_v3 import PBOResult

        pbo_result = PBOResult(
            pbo=0.3,
            frac_positive_paths=0.70,
            path_sharpe_quartiles=(0.1, 0.3, 0.5),
            n_splits_evaluated=45,
            note="synthetic test",
        )

        runner._write_dsr_json(
            report_dir=tmp_path,
            dsr_val=0.8,
            pbo_result=pbo_result,
            psr_val=0.75,
            n_trials=1050,
            n_eff=5,
            min_trl_months=12.0,
            dsr_relative=0.65,
            cpcv_path_sharpe_q75=0.4,
        )

        dsr_path = tmp_path / "dsr.json"
        assert dsr_path.exists(), "dsr.json was not written"
        data = json.loads(dsr_path.read_text())

        assert "cpcv_frac_positive_paths_gate_pass" in data, (
            "dsr.json missing 'cpcv_frac_positive_paths_gate_pass' key. "
            "iter-v3/059 requires this gate field."
        )
        assert "cpcv_frac_positive_paths_gate_threshold" in data, (
            "dsr.json missing 'cpcv_frac_positive_paths_gate_threshold' key."
        )
        # frac_pos = 0.70 >= 0.55 → gate PASS
        gate_val = data["cpcv_frac_positive_paths_gate_pass"]
        assert gate_val is True, (
            f"frac_positive_paths=0.70 should produce gate_pass=True; got {gate_val}"
        )
        assert abs(data["cpcv_frac_positive_paths_gate_threshold"] - 0.55) < 1e-9

    def test_write_dsr_json_gate_fail(self, tmp_path: Path) -> None:
        """Gate must be False when frac_positive_paths < 0.55."""
        import json

        runner = _load_runner()

        from crypto_trade.strategies.ml.validation_v3 import PBOResult

        pbo_result = PBOResult(
            pbo=0.5,
            frac_positive_paths=0.40,  # below threshold
            path_sharpe_quartiles=(0.0, 0.1, 0.2),
            n_splits_evaluated=45,
            note="synthetic low-frac test",
        )

        runner._write_dsr_json(
            report_dir=tmp_path,
            dsr_val=0.4,
            pbo_result=pbo_result,
            psr_val=0.5,
            n_trials=350,
            n_eff=3,
            min_trl_months=8.0,
        )

        data = json.loads((tmp_path / "dsr.json").read_text())
        assert data["cpcv_frac_positive_paths_gate_pass"] is False, (
            f"frac_positive_paths=0.40 should produce gate_pass=False; "
            f"got {data['cpcv_frac_positive_paths_gate_pass']}"
        )

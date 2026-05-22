"""Adversarial test for the iter-v3/006 outer-seed → inner-ensemble derivation.

Pre-iter-v3/006 bug: `run_baseline_v3.py:_run_single_seed` always passed the
hardcoded `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` to LightGbmStrategy,
regardless of the outer seed. So `--seeds 10` produced 10 IDENTICAL inner
ensembles → 10 identical pareto rows (iter-v3/005's structural Pareto FAIL).

The fix: `_derive_ensemble_seeds(outer_seed)` produces a distinct deterministic
5-seed list per outer seed via `np.random.default_rng(outer_seed).integers(...)`.

These tests assert the producer-side property that the derivation is:
  (a) deterministic (same outer seed → same inner ensemble across calls)
  (b) distinct (different outer seeds → different inner ensembles)
  (c) compatible with LightGbmStrategy's existing `ensemble_seeds: list[int]` param

A separate Phase 6 backtest will verify the consumer-side property that
distinct inner ensembles produce distinct OOS trade distributions.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_runner():
    """Load run_baseline_v3.py as a module for testing its top-level helpers."""
    runner_path = Path(__file__).resolve().parents[3] / "run_baseline_v3.py"
    spec = importlib.util.spec_from_file_location("_run_baseline_v3_for_test", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load runner from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_derive_returns_correct_size():
    """_derive_ensemble_seeds default returns `size` inner seeds (default size=5).

    Note: at iter-v3/059+ the unified 10-seed architecture deprecated this helper
    in favor of the hardcoded ENSEMBLE_SEEDS 10-tuple. _derive_ensemble_seeds
    remains exposed for backward compat / regression tests but defaults to size=5
    (legacy 2-outer × 5-inner architecture). The 10-seed unified ENSEMBLE_SEEDS
    is constructed by concatenating _derive_ensemble_seeds(42, size=5) +
    _derive_ensemble_seeds(123, size=5) — see ENSEMBLE_SEEDS literal in runner.
    """
    runner = _load_runner()
    seeds = runner._derive_ensemble_seeds(42)
    # Default size is 5 (legacy per-outer-seed inner ensemble count); 10 only
    # via explicit size=10 or the hardcoded ENSEMBLE_SEEDS tuple.
    assert len(seeds) == 5
    assert all(isinstance(s, int) for s in seeds)


def test_derive_is_deterministic():
    """Same outer seed → same inner ensemble across calls (reproducibility)."""
    runner = _load_runner()
    a = runner._derive_ensemble_seeds(42)
    b = runner._derive_ensemble_seeds(42)
    assert a == b, f"derivation not deterministic: {a} vs {b}"


def test_derive_distinct_for_distinct_outer_seeds():
    """Different outer seeds → different inner ensembles (the iter-v3/006 fix's whole point)."""
    runner = _load_runner()
    s_42 = runner._derive_ensemble_seeds(42)
    s_17 = runner._derive_ensemble_seeds(17)
    s_100 = runner._derive_ensemble_seeds(100)
    assert s_42 != s_17, f"outer 42 and 17 produced identical ensembles: {s_42}"
    assert s_42 != s_100, f"outer 42 and 100 produced identical ensembles: {s_42}"
    assert s_17 != s_100, f"outer 17 and 100 produced identical ensembles: {s_17}"


def test_derive_no_collision_within_ensemble():
    """Single outer seed should produce 5 DISTINCT inner seeds (no in-ensemble collision)."""
    runner = _load_runner()
    seeds = runner._derive_ensemble_seeds(42)
    assert len(set(seeds)) == len(seeds), f"in-ensemble collision: {seeds}"


def test_derive_legacy_constant_no_longer_passed():
    """The pre-fix LEGACY_ENSEMBLE_SEEDS must NOT match any derived ensemble.

    This ensures the iter-v3/006 fix actually changed behavior — if any outer
    seed happened to produce the legacy [42, 123, 456, 789, 1001] list by chance,
    we'd silently revert to the iter-v3/005 false-positive Pareto behavior.
    """
    runner = _load_runner()
    legacy = runner.LEGACY_ENSEMBLE_SEEDS
    # Sample 100 outer seeds and assert none reproduce the legacy list.
    for outer in range(100):
        derived = runner._derive_ensemble_seeds(outer)
        assert derived != legacy, (
            f"outer={outer} derived legacy ensemble {legacy} — would silently "
            "reproduce iter-v3/005's identical-pareto bug."
        )


def test_derive_size_parameter_respected():
    runner = _load_runner()
    seeds_3 = runner._derive_ensemble_seeds(42, size=3)
    seeds_10 = runner._derive_ensemble_seeds(42, size=10)
    assert len(seeds_3) == 3
    assert len(seeds_10) == 10
    # First 3 should match because the RNG is seeded identically.
    seeds_5 = runner._derive_ensemble_seeds(42, size=5)
    assert seeds_5[:3] == seeds_3[:3]

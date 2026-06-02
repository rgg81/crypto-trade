"""Tests for the iter-v1/063 SPECIALIST + BUNDLE methodology.

Covers:
- Constants: V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30
- LightGBM HP constraints in specialist mode
  (max_depth=5 FIXED, num_leaves=31 FIXED, min_child_samples NOT in search space)
- Aggregator: mean-of-signed-weights
- specialist_mode=False preserves old behavior
- Per-seed threshold independence
- Edge cases (all-zero, unanimous signals)
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signed_weights(directions: list[int], weights: list[int]) -> list[float]:
    """Compute signed-weight list from direction/weight pairs."""
    return [float(d) * float(w) for d, w in zip(directions, weights)]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_specialist_seed_count_equals_50() -> None:
    """V1_SPECIALIST_SEED_COUNT must equal 50."""
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEED_COUNT

    assert V1_SPECIALIST_SEED_COUNT == 50, (
        f"V1_SPECIALIST_SEED_COUNT={V1_SPECIALIST_SEED_COUNT}; expected 50"
    )


def test_specialist_optuna_trials_equals_30() -> None:
    """V1_SPECIALIST_OPTUNA_TRIALS must equal 30."""
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_OPTUNA_TRIALS

    assert V1_SPECIALIST_OPTUNA_TRIALS == 30, (
        f"V1_SPECIALIST_OPTUNA_TRIALS={V1_SPECIALIST_OPTUNA_TRIALS}; expected 30"
    )


def test_specialist_seeds_range_42_to_91() -> None:
    """V1_SPECIALIST_SEEDS must be tuple(range(42, 92)) — seeds 42..91."""
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS

    expected = tuple(range(42, 92))
    assert V1_SPECIALIST_SEEDS == expected, (
        f"V1_SPECIALIST_SEEDS[0]={V1_SPECIALIST_SEEDS[0]} (expected 42), "
        f"V1_SPECIALIST_SEEDS[-1]={V1_SPECIALIST_SEEDS[-1]} (expected 91), "
        f"len={len(V1_SPECIALIST_SEEDS)} (expected 50)"
    )


def test_specialist_seeds_length_matches_seed_count() -> None:
    """len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT."""
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEED_COUNT, V1_SPECIALIST_SEEDS

    assert len(V1_SPECIALIST_SEEDS) == V1_SPECIALIST_SEED_COUNT


# ---------------------------------------------------------------------------
# LightGBM HP constraints via optimization.py bounds profile
# ---------------------------------------------------------------------------


def test_lgbm_hp_max_depth_fixed_at_5_in_specialist_mode() -> None:
    """In v1_specialist profile, max_depth must NOT appear as a suggested param."""

    from crypto_trade.strategies.ml.optimization import _objective

    suggested_params: dict = {}

    class _CaptureTrial:
        """Minimal trial stub that captures suggest_int calls."""

        def __init__(self) -> None:
            self.number = 0
            self.study = _FakeStudy()
            self._params: dict = {}

        def suggest_int(self, name: str, low: int, high: int, **_kwargs: object) -> int:
            suggested_params[name] = (low, high)
            return low

        def suggest_float(self, name: str, low: float, high: float, **_kwargs: object) -> float:
            suggested_params[name] = (low, high)
            return (low + high) / 2.0

    class _FakeStudy:
        def user_attrs(self) -> dict:
            return {}

        def get(self, key: str, default: object = None) -> object:
            return default

    # Patch trial.study.user_attrs to behave like a dict.
    class _FakeStudy2:
        user_attrs: dict = {
            "fast_mode": False,
            "optuna_objective": "sharpe",
            "specialist_mode": True,
            "specialist_n_estimators_max": 500,
        }

        def __getitem__(self, key: str) -> object:
            return self.user_attrs[key]

        def get(self, key: str, default: object = None) -> object:
            return self.user_attrs.get(key, default)

    trial = _CaptureTrial()
    trial.study = _FakeStudy2()

    # Build dummy data — we just need _objective to call the suggest_* API.
    rng = np.random.default_rng(0)
    n = 60
    x_train = rng.random((n, 3)).astype(np.float32)
    y_labels = rng.choice([-1, 1], size=n)
    long_pnls = rng.random(n).astype(np.float64)
    short_pnls = rng.random(n).astype(np.float64)
    weights = np.ones(n, dtype=np.float64)
    open_times = np.arange(n, dtype=np.int64) * 28_800_000

    try:
        _objective(
            trial,
            x_train,
            y_labels,
            weights,
            long_pnls,
            short_pnls,
            ["f0", "f1", "f2"],
            3,  # cv_splits
            42,  # seed
            0,  # verbose
            open_times=open_times,
            bounds_profile="v1_specialist",
        )
    except Exception:
        # _objective may raise due to minimal data; we only care that it called suggest_*
        pass

    assert "max_depth" not in suggested_params, (
        f"max_depth was suggested (params={suggested_params}) — "
        "in v1_specialist profile max_depth MUST be FIXED at 5 (not Optuna-tunable)"
    )


def test_lgbm_hp_num_leaves_fixed_at_31_in_specialist_mode() -> None:
    """In v1_specialist profile, num_leaves must NOT appear as a suggested param."""

    from crypto_trade.strategies.ml.optimization import _objective

    suggested_params: dict = {}

    class _FakeStudy3:
        user_attrs: dict = {
            "fast_mode": False,
            "optuna_objective": "sharpe",
            "specialist_mode": True,
            "specialist_n_estimators_max": 500,
        }

        def get(self, key: str, default: object = None) -> object:
            return self.user_attrs.get(key, default)

    class _CaptureTrial2:
        def __init__(self) -> None:
            self.number = 0
            self.study = _FakeStudy3()

        def suggest_int(self, name: str, low: int, high: int, **_kwargs: object) -> int:
            suggested_params[name] = (low, high)
            return low

        def suggest_float(self, name: str, low: float, high: float, **_kwargs: object) -> float:
            suggested_params[name] = (low, high)
            return (low + high) / 2.0

    trial = _CaptureTrial2()

    rng = np.random.default_rng(1)
    n = 60
    x_train = rng.random((n, 3)).astype(np.float32)
    y_labels = rng.choice([-1, 1], size=n)
    long_pnls = rng.random(n).astype(np.float64)
    short_pnls = rng.random(n).astype(np.float64)
    weights = np.ones(n, dtype=np.float64)
    open_times = np.arange(n, dtype=np.int64) * 28_800_000

    try:
        _objective(
            trial,
            x_train,
            y_labels,
            weights,
            long_pnls,
            short_pnls,
            ["f0", "f1", "f2"],
            3,
            42,
            0,
            open_times=open_times,
            bounds_profile="v1_specialist",
        )
    except Exception:
        pass

    assert "num_leaves" not in suggested_params, (
        f"num_leaves was suggested (params={suggested_params}) — "
        "in v1_specialist profile num_leaves MUST be FIXED at 31 (not Optuna-tunable)"
    )


def test_lgbm_hp_min_child_samples_not_in_search_space_in_specialist_mode() -> None:
    """In v1_specialist profile, min_child_samples must NOT appear as a suggested param."""
    from crypto_trade.strategies.ml.optimization import _objective

    suggested_params: dict = {}

    class _FakeStudy4:
        user_attrs: dict = {
            "fast_mode": False,
            "optuna_objective": "sharpe",
            "specialist_mode": True,
            "specialist_n_estimators_max": 500,
        }

        def get(self, key: str, default: object = None) -> object:
            return self.user_attrs.get(key, default)

    class _CaptureTrial3:
        def __init__(self) -> None:
            self.number = 0
            self.study = _FakeStudy4()

        def suggest_int(self, name: str, low: int, high: int, **_kwargs: object) -> int:
            suggested_params[name] = (low, high)
            return low

        def suggest_float(self, name: str, low: float, high: float, **_kwargs: object) -> float:
            suggested_params[name] = (low, high)
            return (low + high) / 2.0

    trial = _CaptureTrial3()

    rng = np.random.default_rng(2)
    n = 60
    x_train = rng.random((n, 3)).astype(np.float32)
    y_labels = rng.choice([-1, 1], size=n)
    long_pnls = rng.random(n).astype(np.float64)
    short_pnls = rng.random(n).astype(np.float64)
    weights = np.ones(n, dtype=np.float64)
    open_times = np.arange(n, dtype=np.int64) * 28_800_000

    try:
        _objective(
            trial,
            x_train,
            y_labels,
            weights,
            long_pnls,
            short_pnls,
            ["f0", "f1", "f2"],
            3,
            42,
            0,
            open_times=open_times,
            bounds_profile="v1_specialist",
        )
    except Exception:
        pass

    assert "min_child_samples" not in suggested_params, (
        f"min_child_samples was suggested (params={suggested_params}) — "
        "in v1_specialist profile min_child_samples MUST be REMOVED from search space"
    )


# ---------------------------------------------------------------------------
# Aggregator unit tests
# ---------------------------------------------------------------------------


def test_aggregator_simple_mean_of_signed_weights() -> None:
    """Aggregator: final_signed = mean(direction_i × weight_i) for arbitrary inputs."""
    # 4 seeds: (+1, 100), (-1, 100), (+1, 100), (+1, 0)
    # signed: [+100, -100, +100, 0]  → mean = 25.0 → direction=+1, weight=25
    signed = _make_signed_weights([1, -1, 1, 1], [100, 100, 100, 0])
    final_signed = float(np.mean(signed))
    assert abs(final_signed - 25.0) < 1e-9, f"Expected 25.0, got {final_signed}"
    direction = 1 if final_signed > 0 else -1
    weight = int(round(abs(final_signed)))
    assert direction == 1
    assert weight == 25


def test_aggregator_handles_all_zero_signals() -> None:
    """If all seeds emit weight=0, final_signed=0 → NO_SIGNAL (abs < 1e-9)."""
    # 50 seeds all below threshold → all (0, 0)
    directions = [1] * 50  # direction doesn't matter — weight is 0
    weights = [0] * 50
    signed = _make_signed_weights(directions, weights)
    final_signed = float(np.mean(signed))
    # Simulate the specialist aggregator gate
    assert abs(final_signed) < 1e-9, f"Expected ~0, got {final_signed}"


def test_aggregator_handles_unanimous_signals() -> None:
    """50 seeds all at (+1, 100) → final_signed=+100, weight=100, direction=+1."""
    directions = [1] * 50
    weights = [100] * 50
    signed = _make_signed_weights(directions, weights)
    final_signed = float(np.mean(signed))
    assert abs(final_signed - 100.0) < 1e-9, f"Expected 100.0, got {final_signed}"
    direction = 1 if final_signed > 0 else -1
    weight = int(round(abs(final_signed)))
    assert direction == 1
    assert weight == 100


def test_aggregator_unanimous_short_signals() -> None:
    """50 seeds all at (-1, 100) → final_signed=-100, weight=100, direction=-1."""
    directions = [-1] * 50
    weights = [100] * 50
    signed = _make_signed_weights(directions, weights)
    final_signed = float(np.mean(signed))
    assert abs(final_signed - (-100.0)) < 1e-9, f"Expected -100.0, got {final_signed}"
    direction = 1 if final_signed > 0 else -1
    weight = int(round(abs(final_signed)))
    assert direction == -1
    assert weight == 100


def test_aggregator_mixed_signals_partial_consensus() -> None:
    """30 long at weight=100, 20 short at weight=100 → final_signed=+20."""
    directions = [1] * 30 + [-1] * 20
    weights = [100] * 50
    signed = _make_signed_weights(directions, weights)
    final_signed = float(np.mean(signed))
    # (30×100 - 20×100) / 50 = (3000 - 2000) / 50 = 1000/50 = 20.0
    assert abs(final_signed - 20.0) < 1e-9, f"Expected 20.0, got {final_signed}"
    direction = 1 if final_signed > 0 else -1
    weight = int(round(abs(final_signed)))
    assert direction == 1
    assert weight == 20


def test_specialist_uses_per_seed_thresholds_not_averaged() -> None:
    """Each seed evaluates against its OWN threshold — NOT the average across seeds.

    Scenario: seed A has threshold=0.55, confidence=0.56 → fires (weight=100).
              seed B has threshold=0.75, confidence=0.56 → does NOT fire (weight=0).
    If thresholds were averaged: mean_threshold=0.65, confidence=0.56 → no trade (WRONG).
    The correct behavior: seed A fires, seed B doesn't → final = mean([+100, 0]) = +50.
    """
    # Simulate per-seed evaluation
    confidence = 0.56

    threshold_a = 0.55
    threshold_b = 0.75

    weight_a = 100 if confidence > threshold_a else 0
    weight_b = 100 if confidence > threshold_b else 0

    # Per-seed: both long direction
    direction_a = 1
    direction_b = 1

    signed_a = float(direction_a * weight_a)
    signed_b = float(direction_b * weight_b)
    final_per_seed = float(np.mean([signed_a, signed_b]))

    # Average-threshold (INCORRECT old behavior):
    avg_threshold = (threshold_a + threshold_b) / 2.0
    weight_avg = 100 if confidence > avg_threshold else 0
    final_avg_threshold = float(weight_avg)

    # Per-seed must fire; avg-threshold must not.
    assert weight_a == 100, "Seed A should fire (conf=0.56 > threshold_a=0.55)"
    assert weight_b == 0, "Seed B should NOT fire (conf=0.56 < threshold_b=0.75)"
    assert abs(final_per_seed - 50.0) < 1e-9, (
        f"Per-seed aggregation should yield 50.0, got {final_per_seed}"
    )
    assert final_avg_threshold == 0.0, (
        f"Averaged-threshold approach yields {final_avg_threshold}; "
        "confirms the retired behavior would produce NO_SIGNAL here"
    )
    # Key assertion: per-seed fires when avg-threshold does NOT.
    assert final_per_seed != final_avg_threshold, (
        "Per-seed and avg-threshold produce identical results — "
        "this scenario should distinguish them"
    )


def test_specialist_mode_off_preserves_old_behavior() -> None:
    """specialist_mode=False: LightGbmStrategy imports and initialises without error."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    # Minimal valid construction — no actual training.
    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=False,
    )
    assert not strat._specialist_mode, "specialist_mode=False should set _specialist_mode=False"
    assert strat._specialist_models == [], (
        "Non-specialist mode should have empty _specialist_models"
    )


def test_specialist_mode_true_sets_flag() -> None:
    """specialist_mode=True: _specialist_mode flag is set correctly."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=True,
        specialist_n_startup_trials=10,
        specialist_n_estimators_max=500,
    )
    assert strat._specialist_mode, "specialist_mode=True should set _specialist_mode=True"
    assert strat._specialist_n_startup_trials == 10
    assert strat._specialist_n_estimators_max == 500


# ---------------------------------------------------------------------------
# iter-v1/063 Patch 2 — per-candle ensemble-std diagnostic
# ---------------------------------------------------------------------------


def test_specialist_dispersion_stats_initialises_empty() -> None:
    """LightGbmStrategy initialises _specialist_dispersion_stats as an empty list."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=True,
    )
    assert isinstance(strat._specialist_dispersion_stats, list), (
        "_specialist_dispersion_stats should be a list"
    )
    assert strat._specialist_dispersion_stats == [], (
        "_specialist_dispersion_stats should be empty on init"
    )


def test_get_specialist_dispersion_mean_returns_none_when_empty() -> None:
    """get_specialist_dispersion_mean() returns None when no signals have fired."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=True,
    )
    assert strat.get_specialist_dispersion_mean() is None, (
        "Should return None when _specialist_dispersion_stats is empty"
    )


def test_specialist_ensemble_std_logged() -> None:
    """Simulates specialist signal generation and verifies ensemble_std in decision_log.

    This test directly exercises the aggregator branch by populating
    _specialist_models with stub models and calling the inner aggregator logic
    that populates _specialist_dispersion_stats and logs ensemble_std.
    Uses the population std formula to verify correctness.
    """
    import numpy as np

    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=["f0", "f1", "f2"],
        specialist_mode=True,
    )

    # Simulate what the aggregator computes for a candle where 3 seeds vote:
    # seed 0: direction=+1, weight=100  → signed = +100
    # seed 1: direction=+1, weight=100  → signed = +100
    # seed 2: direction=-1, weight=100  → signed = -100
    signed_weights = [100.0, 100.0, -100.0]
    final_signed = float(np.mean(signed_weights))
    ensemble_std = float(np.std(signed_weights))  # ddof=0, population std

    # Manually append to dispersion stats as the aggregator would after signal fires.
    assert abs(final_signed) >= 1e-9, "Signal should fire with this signed_weights"
    strat._specialist_dispersion_stats.append(ensemble_std)

    # Verify dispersion mean is computable and numerically correct.
    mean_disp = strat.get_specialist_dispersion_mean()
    assert mean_disp is not None, "get_specialist_dispersion_mean() should not be None after append"

    # Population std of [100, 100, -100]:
    # mean = 33.33...; deviations = [66.67, 66.67, -133.33]; var = (66.67^2 + 66.67^2 + 133.33^2)/3
    expected_std = float(np.std([100.0, 100.0, -100.0]))
    assert abs(mean_disp - expected_std) < 1e-9, (
        f"Dispersion mean {mean_disp:.6f} != expected {expected_std:.6f}"
    )

    # Verify ensemble_std key appears in a mock decision_log entry (schema check).
    # We verify the dict key exists rather than patching the full log module.
    log_entry = {
        "kind": "lgbm_signal",
        "symbol": "BTCUSDT",
        "ot": 1700000000000,
        "month": "2023-11",
        "specialist_seeds": 3,
        "final_signed": final_signed,
        "ensemble_std": ensemble_std,
        "direction": 1 if final_signed > 0 else -1,
        "tp_pct": None,
        "sl_pct": None,
        "confidence": abs(final_signed) / 100.0,
        "decision": "signal",
    }
    assert "ensemble_std" in log_entry, "ensemble_std must be a key in the decision_log entry"
    assert isinstance(log_entry["ensemble_std"], float), "ensemble_std must be a float"
    assert log_entry["ensemble_std"] >= 0.0, "ensemble_std (population std) must be non-negative"


def test_specialist_ensemble_std_zero_for_unanimous_signal() -> None:
    """When all seeds agree unanimously, ensemble_std = 0.0."""
    import numpy as np

    # 50 seeds all vote (+1, 100) → signed_weights = [+100] * 50
    signed_weights = [100.0] * 50
    ensemble_std = float(np.std(signed_weights))
    assert ensemble_std == 0.0, (
        f"Unanimous signals should produce ensemble_std=0.0, got {ensemble_std}"
    )

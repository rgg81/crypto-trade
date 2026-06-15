"""Tests for the v1 single-symbol SEED RULE (redesign 2026-06-15).

THE RULE (ratified by the user):
    v1's model = the SPECIALIST bagging ensemble — K independent Optuna studies
    per month (each its own HP search + seed), combined by mean-of-signed-weights.
    K is the ONLY seed number that varies.
      - Inner ensemble (--ensemble-size / ensemble_seeds) = 1, ALWAYS.
      - Outer seeds (--seeds)                            = 1, ALWAYS.
      - EXPLORATION  -> K = 3.   CONFIRMATION -> K = 20.
      - Single-symbol only.

These tests assert the rule WITHOUT running a full backtest:
  (a) EXPLORATION resolves bagging_k=3, CONFIRMATION resolves bagging_k=20.
  (b) the single-symbol specialist dispatch builds a LightGbmStrategy with
      specialist_mode=True, specialist_seed_count==bagging_k, and inner
      ensemble_seeds length == 1.
  (c) --seeds > 1 raises for exploration/confirmation.

Run:
    uv run pytest tests/test_v1_seed_rule.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# (a) Mode -> bagging_k resolution + outer-seed enforcement.
#
# We replicate the exact mode-resolution + seed-assertion logic from main()
# (parsing via argparse directly, NOT calling main(), which would launch a
# full backtest). The replicated block mirrors run_baseline_v1.main().
# ---------------------------------------------------------------------------


def _resolve_mode(argv: list[str]) -> dict:
    """Parse argv and run the mode-resolution + seed-rule block from main().

    Returns a dict with resolved ``bagging_k``, ``ensemble_size`` and ``seeds``.
    Raises SystemExit if argparse or the seed-rule validation fires.
    """
    import argparse

    from run_baseline_v1 import (
        V1_CONFIRMATION_BAGGING_K,
        V1_EXPLORATION_BAGGING_K,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", type=int, default=None)
    parser.add_argument("--baseline-mode", action="store_true")
    parser.add_argument("--exploration", action="store_true")
    parser.add_argument("--confirmation", action="store_true")
    parser.add_argument("--n-trials", type=int, default=35)
    parser.add_argument("--ensemble-size", type=int, default=None)
    parser.add_argument("--bagging-k", type=int, default=None)
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--symbols", type=str, default=None)
    args = parser.parse_args(argv)

    bagging_k: int | None = None
    # --- replicate the mode-resolution logic from main() ---
    if args.baseline_mode:
        ensemble_size = 5
    elif args.exploration:
        bagging_k = V1_EXPLORATION_BAGGING_K
        ensemble_size = 1
        if args.iteration is None:
            raise SystemExit("ERROR: --exploration requires --iteration NNN")
    elif args.confirmation:
        bagging_k = V1_CONFIRMATION_BAGGING_K
        ensemble_size = 1
        if args.iteration is None:
            raise SystemExit("ERROR: --confirmation requires --iteration NNN")
    else:
        raise SystemExit("ERROR: must specify --baseline-mode, --exploration, or --confirmation")

    # --- replicate the outer-seed enforcement from main() ---
    if (args.exploration or args.confirmation) and args.seeds != 1:
        raise SystemExit(f"ERROR: v1 outer seeds are FIXED at 1 (got --seeds {args.seeds}).")

    # --- replicate the --bagging-k override from main() ---
    if (args.exploration or args.confirmation) and args.bagging_k is not None:
        if args.bagging_k < 1:
            raise SystemExit(f"ERROR: --bagging-k must be >= 1; got {args.bagging_k}")
        bagging_k = args.bagging_k

    # --- replicate the --ensemble-size rejection from main() ---
    if args.ensemble_size is not None and (args.exploration or args.confirmation):
        raise SystemExit(
            f"ERROR: --ensemble-size ({args.ensemble_size}) is not supported with "
            "--exploration/--confirmation."
        )

    return {"bagging_k": bagging_k, "ensemble_size": ensemble_size, "seeds": args.seeds}


class TestBaggingKConstants:
    """The bagging-K constants must equal the ratified values."""

    def test_exploration_bagging_k_is_3(self) -> None:
        from run_baseline_v1 import V1_EXPLORATION_BAGGING_K

        assert V1_EXPLORATION_BAGGING_K == 3

    def test_confirmation_bagging_k_is_20(self) -> None:
        from run_baseline_v1 import V1_CONFIRMATION_BAGGING_K

        assert V1_CONFIRMATION_BAGGING_K == 20

    def test_old_ensemble_size_constants_retired(self) -> None:
        """The old (wrong-knob) inner-ensemble constants must be gone."""
        import run_baseline_v1

        assert not hasattr(run_baseline_v1, "V1_EXPLORATION_ENSEMBLE_SIZE"), (
            "V1_EXPLORATION_ENSEMBLE_SIZE was the wrong inner-ensemble knob — must be retired"
        )
        assert not hasattr(run_baseline_v1, "V1_CONFIRMATION_ENSEMBLE_SIZE"), (
            "V1_CONFIRMATION_ENSEMBLE_SIZE was the wrong inner-ensemble knob — must be retired"
        )


class TestModeResolvesBaggingK:
    """(a) EXPLORATION -> K=3, CONFIRMATION -> K=20; inner ensemble always 1."""

    def test_exploration_resolves_bagging_k_3(self) -> None:
        result = _resolve_mode(["--exploration", "--iteration", "900"])
        assert result["bagging_k"] == 3
        assert result["ensemble_size"] == 1, "inner ensemble must be FIXED at 1"
        assert result["seeds"] == 1, "outer seeds must be FIXED at 1"

    def test_confirmation_resolves_bagging_k_20(self) -> None:
        result = _resolve_mode(["--confirmation", "--iteration", "900"])
        assert result["bagging_k"] == 20
        assert result["ensemble_size"] == 1, "inner ensemble must be FIXED at 1"
        assert result["seeds"] == 1, "outer seeds must be FIXED at 1"

    def test_bagging_k_override_for_smoke(self) -> None:
        """--bagging-k 2 overrides the mode default (smoke-test path)."""
        result = _resolve_mode(["--exploration", "--iteration", "900", "--bagging-k", "2"])
        assert result["bagging_k"] == 2
        assert result["ensemble_size"] == 1

    def test_bagging_k_override_zero_rejected(self) -> None:
        with pytest.raises(SystemExit, match="--bagging-k must be >= 1"):
            _resolve_mode(["--exploration", "--iteration", "900", "--bagging-k", "0"])


class TestOuterSeedsFixedAt1:
    """(c) --seeds > 1 raises for exploration/confirmation."""

    def test_exploration_seeds_2_raises(self) -> None:
        with pytest.raises(SystemExit, match="outer seeds are FIXED at 1"):
            _resolve_mode(["--exploration", "--iteration", "900", "--seeds", "2"])

    def test_confirmation_seeds_5_raises(self) -> None:
        with pytest.raises(SystemExit, match="outer seeds are FIXED at 1"):
            _resolve_mode(["--confirmation", "--iteration", "900", "--seeds", "5"])

    def test_exploration_seeds_1_ok(self) -> None:
        result = _resolve_mode(["--exploration", "--iteration", "900", "--seeds", "1"])
        assert result["seeds"] == 1

    def test_ensemble_size_rejected_for_exploration(self) -> None:
        """--ensemble-size is the retired wrong knob — must be rejected."""
        with pytest.raises(SystemExit, match="not supported with"):
            _resolve_mode(["--exploration", "--iteration", "900", "--ensemble-size", "5"])


class TestSpecialistSeedCountWiring:
    """(b) Verify the LightGbmStrategy bagging wiring honors K.

    LightGbmStrategy stores specialist_seed_count and the bagging loop slices
    V1_SPECIALIST_SEEDS to the FIRST K seeds when K > 0, preserving legacy
    full-roster (50) behavior when K == 0.
    """

    def _build_strategy(self, *, specialist_seed_count: int, ensemble_size: int):
        from run_baseline_v1 import V1_FEATURE_COLUMNS

        from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

        # inner ensemble = 1 placeholder seed [42] (mirrors _derive_ensemble_seeds(1))
        ensemble_seeds = [42] if ensemble_size == 1 else list(range(42, 42 + ensemble_size))
        return LightGbmStrategy(
            training_months=24,
            n_trials=2,
            label_tp_pct=5.8,
            label_sl_pct=2.9,
            atr_tp_multiplier=2.9,
            atr_sl_multiplier=1.45,
            use_atr_labeling=True,
            ensemble_seeds=ensemble_seeds,
            feature_columns=list(V1_FEATURE_COLUMNS),
            bounds_profile="v1_specialist",
            specialist_mode=True,
            specialist_seed_count=specialist_seed_count,
        )

    def test_exploration_strategy_specialist_mode(self) -> None:
        strat = self._build_strategy(specialist_seed_count=3, ensemble_size=1)
        assert strat._specialist_mode is True
        assert strat._specialist_seed_count == 3
        assert len(strat.ensemble_seeds) == 1, "inner ensemble seeds length must be 1"
        assert strat.ensemble_seeds == [42], "inner placeholder seed must be [42]"

    def test_confirmation_strategy_specialist_mode(self) -> None:
        strat = self._build_strategy(specialist_seed_count=20, ensemble_size=1)
        assert strat._specialist_mode is True
        assert strat._specialist_seed_count == 20
        assert len(strat.ensemble_seeds) == 1

    def test_bagging_loop_slices_roster_to_k(self) -> None:
        """The bagging loop uses V1_SPECIALIST_SEEDS[:K] when K > 0."""
        from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS

        strat = self._build_strategy(specialist_seed_count=3, ensemble_size=1)
        # Mirror the loop's slicing decision (lgbm.py specialist branch).
        seeds = (
            V1_SPECIALIST_SEEDS[: strat._specialist_seed_count]
            if strat._specialist_seed_count > 0
            else V1_SPECIALIST_SEEDS
        )
        assert list(seeds) == [42, 43, 44], "K=3 must select the first 3 roster seeds"

    def test_k_zero_preserves_legacy_full_roster(self) -> None:
        """specialist_seed_count==0 (legacy default) keeps the full 50-seed roster."""
        from crypto_trade.strategies.ml.lgbm import (
            V1_SPECIALIST_SEED_COUNT,
            V1_SPECIALIST_SEEDS,
        )

        strat = self._build_strategy(specialist_seed_count=0, ensemble_size=1)
        assert strat._specialist_seed_count == 0
        seeds = (
            V1_SPECIALIST_SEEDS[: strat._specialist_seed_count]
            if strat._specialist_seed_count > 0
            else V1_SPECIALIST_SEEDS
        )
        assert len(seeds) == V1_SPECIALIST_SEED_COUNT == 50


class TestRunModelThreadsSpecialistParams:
    """(b) run_model threads specialist params into LightGbmStrategy without a backtest.

    We monkeypatch run_backtest to short-circuit so construction happens but no
    data is touched, then inspect the returned strategy.
    """

    def test_run_model_builds_specialist_strategy(self, monkeypatch) -> None:
        import run_baseline_v1

        captured = {}

        def _fake_run_backtest(config, strategy, **kwargs):
            captured["strategy"] = strategy
            return []

        monkeypatch.setattr(run_baseline_v1, "run_backtest", _fake_run_backtest)

        results, faxm, strat = run_baseline_v1.run_model(
            "Model_A_BTCUSDT_specialist",
            ("BTCUSDT",),
            atr_tp=2.9,
            atr_sl=1.45,
            apply_r1=False,
            apply_r2=False,
            n_trials=2,
            ensemble_size=1,
            feature_columns=list(run_baseline_v1.V1_FEATURE_COLUMNS),
            bounds_profile="v1_specialist",
            specialist_mode=True,
            specialist_seed_count=3,
        )
        assert strat is captured["strategy"]
        assert strat._specialist_mode is True
        assert strat._specialist_seed_count == 3
        assert len(strat.ensemble_seeds) == 1, "inner ensemble must be 1 (placeholder [42])"
        assert strat.ensemble_seeds == [42]
        assert results == []

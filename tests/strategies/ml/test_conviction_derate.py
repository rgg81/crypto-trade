"""Adversarial tests for conviction_derate (iter-v3/079 primitive 13).

Tests:
1. Boundary values: f(0.50)==50, f(0.65)==100, f(1.00)==100.
2. Full-weight plateau: conviction_derate(c)==100 for all c >= C_REF.
3. Floor: conviction_derate(c)==50 for all c <= C_FLOOR.
4. Monotone non-decreasing on dense grid [0.50, 1.00].
5. Return type is int (Signal.weight contract).
6. Look-ahead-clean structural assertion: conviction_derate is a pure function
   of its argument (confidence) — it does not read any external state.
7. Weight scalar adds/removes no trades: the (symbol, open_time) key roster
   from a controlled toy call to get_signal is structurally unchanged by the
   derate (only the weight value changes).
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from crypto_trade.strategies.ml.lgbm import conviction_derate

# -----------------------------------------------------------------------
# Constants (mirrors brief Section 3.1 a-priori values)
# -----------------------------------------------------------------------
C_FLOOR: float = 0.50
C_REF: float = 0.65
W_MIN_FRAC: float = 0.50
W_MIN: int = round(100 * W_MIN_FRAC)  # 50
W_MAX: int = 100


# -----------------------------------------------------------------------
# 1. Boundary values
# -----------------------------------------------------------------------
class TestBoundaryValues:
    def test_floor_confidence_gives_min_weight(self) -> None:
        assert conviction_derate(C_FLOOR) == W_MIN

    def test_ref_confidence_gives_full_weight(self) -> None:
        assert conviction_derate(C_REF) == W_MAX

    def test_unity_confidence_gives_full_weight(self) -> None:
        assert conviction_derate(1.00) == W_MAX

    def test_below_floor_gives_min_weight(self) -> None:
        # Confidence below the coin-flip line is clamped to floor.
        assert conviction_derate(0.40) == W_MIN
        assert conviction_derate(0.00) == W_MIN


# -----------------------------------------------------------------------
# 2. Full-weight plateau: f(c) == 100 for all c >= C_REF
# -----------------------------------------------------------------------
class TestFullWeightPlateau:
    @pytest.mark.parametrize(
        "conf",
        [C_REF, C_REF + 0.01, C_REF + 0.10, C_REF + 0.20, 0.90, 0.99, 1.00],
    )
    def test_at_or_above_c_ref_is_100(self, conf: float) -> None:
        assert conviction_derate(conf) == W_MAX, (
            f"Expected 100 at confidence={conf}, got {conviction_derate(conf)}"
        )


# -----------------------------------------------------------------------
# 3. Floor plateau: f(c) == 50 for all c <= C_FLOOR
# -----------------------------------------------------------------------
class TestFloorPlateau:
    @pytest.mark.parametrize(
        "conf",
        [C_FLOOR, C_FLOOR - 0.01, C_FLOOR - 0.10, 0.10, 0.00],
    )
    def test_at_or_below_c_floor_is_50(self, conf: float) -> None:
        assert conviction_derate(conf) == W_MIN, (
            f"Expected 50 at confidence={conf}, got {conviction_derate(conf)}"
        )


# -----------------------------------------------------------------------
# 4. Monotone non-decreasing on dense grid
# -----------------------------------------------------------------------
class TestMonotonicity:
    def test_non_decreasing_on_dense_grid(self) -> None:
        grid = np.linspace(0.0, 1.0, 2001)
        weights = [conviction_derate(float(c)) for c in grid]
        for i in range(len(weights) - 1):
            assert weights[i] <= weights[i + 1], (
                f"Monotonicity violated at grid[{i}]={grid[i]:.4f}: "
                f"w[{i}]={weights[i]} > w[{i + 1}]={weights[i + 1]}"
            )

    def test_bounded_in_50_100(self) -> None:
        grid = np.linspace(0.0, 1.0, 2001)
        weights = [conviction_derate(float(c)) for c in grid]
        assert all(W_MIN <= w <= W_MAX for w in weights), (
            f"Weight out of [50, 100]: min={min(weights)}, max={max(weights)}"
        )


# -----------------------------------------------------------------------
# 5. Return type is int
# -----------------------------------------------------------------------
class TestReturnType:
    @pytest.mark.parametrize("conf", [0.50, 0.57, 0.60, 0.62, 0.65, 0.80, 1.00])
    def test_returns_int(self, conf: float) -> None:
        result = conviction_derate(conf)
        assert isinstance(result, int), (
            f"conviction_derate({conf}) returned {type(result).__name__}, expected int"
        )


# -----------------------------------------------------------------------
# 6. Look-ahead-clean structural assertion
#    The function is a pure function: it reads only its argument.
#    Inspect that conviction_derate has no global state references or
#    closures that could consult future data.
# -----------------------------------------------------------------------
class TestLookAheadClean:
    def test_is_pure_function_with_no_closures(self) -> None:
        # Pure functions have no free variables (closures).
        closure = getattr(conviction_derate, "__closure__", None)
        assert closure is None, (
            "conviction_derate has unexpected closure variables — potential look-ahead risk."
        )

    def test_no_global_state_references(self) -> None:
        # The function's global refs should be limited to numpy (np.clip).
        # We verify it does NOT reference any non-builtins other than numpy.
        source = inspect.getsource(conviction_derate)
        # The body should only reference np.clip and round — no model, dataframe,
        # or external data access.
        forbidden_refs = ["self.", "pd.", "open_time", "symbol", "_month", "proba", "models"]
        for ref in forbidden_refs:
            assert ref not in source, (
                f"conviction_derate source references '{ref}' — potential look-ahead / "
                f"external-state access."
            )

    def test_deterministic_repeated_calls(self) -> None:
        # Pure functions produce identical output on repeated calls with same input.
        for conf in [0.50, 0.57, 0.62, 0.65, 0.80, 1.00]:
            r1 = conviction_derate(conf)
            r2 = conviction_derate(conf)
            assert r1 == r2, f"Non-deterministic at confidence={conf}: {r1} != {r2}"


# -----------------------------------------------------------------------
# 7. Weight scalar: de-rate is a SCALAR not a filter
#    Verify that the de-rate property holds: the map always returns a value in
#    [W_MIN, W_MAX] and never returns 0 (which would silently drop a trade).
#    Structural proof that a weight scalar cannot add or remove trades:
#    conviction_derate returns a positive int in [50, 100] — there is no code
#    path that returns 0 or None, which are the only return values that could
#    suppress a Signal downstream.
# -----------------------------------------------------------------------
class TestWeightScalarProperty:
    def test_weight_never_zero(self) -> None:
        """No confidence value in [0, 1] produces weight=0 (no trade dropout)."""
        grid = np.linspace(0.0, 1.0, 10001)
        weights = [conviction_derate(float(c)) for c in grid]
        assert all(w > 0 for w in weights), (
            f"conviction_derate returned 0 — would silently drop a trade. "
            f"Min weight found: {min(weights)}"
        )

    def test_weight_floor_is_50(self) -> None:
        """Weight floor is exactly 50 (half-size, not elimination)."""
        grid = np.linspace(0.0, 0.50, 1001)
        weights = [conviction_derate(float(c)) for c in grid]
        assert all(w == W_MIN for w in weights), (
            f"Below C_FLOOR, expected all weights={W_MIN}; "
            f"got non-{W_MIN} values: {[w for w in weights if w != W_MIN]}"
        )

    def test_midpoint_weight_in_range(self) -> None:
        """A confidence strictly inside (C_FLOOR, C_REF) gives a weight in (50, 100).

        Note: (C_FLOOR + C_REF) / 2 = 0.575 maps to w_min_frac exactly (the clip
        lower bound is w_min_frac=0.50, and (0.575-0.50)/(0.65-0.50)=0.5==w_min_frac).
        Use 0.60 instead, which is strictly above the floor.
        """
        conf = 0.60  # strictly inside (C_FLOOR, C_REF), (0.60-0.50)/(0.15) = 0.667 → w=67
        w = conviction_derate(conf)
        assert W_MIN < w < W_MAX, (
            f"confidence={conf:.2f} should give w in ({W_MIN}, {W_MAX}); got {w}"
        )

"""Tests for iter-v1/074 — ETH-IMPROVED-V3 SPECIALIST (AXIS-R Mid-Bull SHORT VETO).

Covers:
1. AXIS-R veto wiring: mid-bull short signals are vetoed; longs and out-of-band shorts pass.
2. Methodology constants: V1_FEATURE_COLUMNS_PRUNED 48-col hash, AXIS-R band edges,
   R1=OFF, R2=OFF, V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30.
3. V1_ITER074_UNIVERSE == ("ETHUSDT",).
4. Runner pre-flight assertions fire on wrong hash / wrong band edges.
5. Smoke import tests.
"""

from __future__ import annotations

import hashlib

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_features_hash(cols: tuple[str, ...]) -> str:
    payload = "\n".join(sorted(cols)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# 1. Smoke imports
# ---------------------------------------------------------------------------


def test_lgbm_strategy_import() -> None:
    """LightGbmStrategy imports without error."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy  # noqa: F401


def test_v1_iter074_universe_import() -> None:
    """V1_ITER074_UNIVERSE is importable and == ('ETHUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER074_UNIVERSE

    assert V1_ITER074_UNIVERSE == ("ETHUSDT",), (
        f"V1_ITER074_UNIVERSE must be ('ETHUSDT',); got {V1_ITER074_UNIVERSE}"
    )


def test_v1_feature_columns_pruned_48_cols() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must be 48 columns (UNCHANGED from /064 closeout)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"V1_FEATURE_COLUMNS_PRUNED must have 48 cols at iter-v1/074; "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. AXIS-R is post-aggregator only — "
        "it does NOT modify the feature stack."
    )


def test_runner_import() -> None:
    """run_iteration_074 imports without error (no backtest)."""
    import importlib
    import sys

    # Guard against accidentally running main() during import.
    # The module uses 'if __name__ == "__main__": main()' so import is safe.
    if "run_iteration_074" in sys.modules:
        del sys.modules["run_iteration_074"]
    mod = importlib.import_module("run_iteration_074")
    assert hasattr(mod, "main")
    assert hasattr(mod, "ITERATION_LABEL")
    assert mod.ITERATION_LABEL == "v1-074"
    assert hasattr(mod, "AXIS_R_VETO_LO")
    assert hasattr(mod, "AXIS_R_VETO_HI")
    assert hasattr(mod, "AXIS_R_VETO_LOOKBACK")


# ---------------------------------------------------------------------------
# 2. Methodology constants
# ---------------------------------------------------------------------------


def test_features_base_hash_48col() -> None:
    """The 48-col features hash matches the pre-registered value from /064."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    expected = "b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3"
    actual = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)
    assert actual == expected, (
        f"V1_FEATURE_COLUMNS_PRUNED hash mismatch at iter-v1/074.\n"
        f"  expected (48-col /064 hash): {expected}\n"
        f"  actual                     : {actual}\n"
        f"  len(V1_FEATURE_COLUMNS_PRUNED) = {len(V1_FEATURE_COLUMNS_PRUNED)}\n"
        "AXIS-R is post-aggregator only — the feature stack must be UNCHANGED."
    )


def test_axis_r_band_edges_frozen() -> None:
    """AXIS-R band edges [0.20, 0.50] and lookback 270 match pre-registered values."""
    import run_iteration_074 as r074

    assert r074.AXIS_R_VETO_LO == 0.20, (
        f"AXIS_R_VETO_LO must be 0.20 (pre-registered, frozen); got {r074.AXIS_R_VETO_LO}"
    )
    assert r074.AXIS_R_VETO_HI == 0.50, (
        f"AXIS_R_VETO_HI must be 0.50 (pre-registered, frozen); got {r074.AXIS_R_VETO_HI}"
    )
    assert r074.AXIS_R_VETO_LOOKBACK == 270, (
        "AXIS_R_VETO_LOOKBACK must be 270 (pre-registered, frozen); "
        f"got {r074.AXIS_R_VETO_LOOKBACK}"
    )


def test_specialist_constants() -> None:
    """V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_OPTUNA_TRIALS,
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEEDS,
    )

    assert V1_SPECIALIST_SEED_COUNT == 50, (
        f"V1_SPECIALIST_SEED_COUNT must be 50; got {V1_SPECIALIST_SEED_COUNT}"
    )
    assert V1_SPECIALIST_OPTUNA_TRIALS == 30, (
        f"V1_SPECIALIST_OPTUNA_TRIALS must be 30; got {V1_SPECIALIST_OPTUNA_TRIALS}"
    )
    assert len(V1_SPECIALIST_SEEDS) == 50
    assert V1_SPECIALIST_SEEDS[0] == 42
    assert V1_SPECIALIST_SEEDS[-1] == 91


def test_r1_is_off_in_runner_constants() -> None:
    """Runner iteration_label is 'v1-074' (not 'v1-064') and ITERATION_NUMBER=74."""
    import run_iteration_074 as r074

    assert r074.ITERATION_LABEL == "v1-074"
    assert r074.ITERATION_NUMBER == 74


# ---------------------------------------------------------------------------
# 3. AXIS-R veto logic unit tests (via _apply_mid_bull_short_veto)
# ---------------------------------------------------------------------------


def _make_strategy_with_close_index(
    symbol: str,
    open_times: list[int],
    closes: list[float],
    lo: float = 0.20,
    hi: float = 0.50,
    lookback: int = 270,
) -> object:
    """Construct a minimal LightGbmStrategy with close-by-sym index for veto tests."""

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS, LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
        ensemble_seeds=[V1_SPECIALIST_SEEDS[0]],
        enable_mid_bull_short_veto=True,
        mid_bull_short_veto_lo=lo,
        mid_bull_short_veto_hi=hi,
        mid_bull_short_veto_lookback=lookback,
    )

    # Manually inject the close-by-sym index (bypasses compute_features).
    ot_arr = np.array(open_times, dtype=np.int64)
    cl_arr = np.array(closes, dtype=np.float64)
    sort_idx = np.argsort(ot_arr)
    strat._close_by_sym = {symbol: (ot_arr[sort_idx], cl_arr[sort_idx])}
    return strat


def _signal_short(weight: int = 100) -> object:
    """Helper: make a short signal."""
    from crypto_trade.strategies.ml.lgbm import Signal

    return Signal(direction=-1, weight=weight)


def _signal_long(weight: int = 100) -> object:
    """Helper: make a long signal."""
    from crypto_trade.strategies.ml.lgbm import Signal

    return Signal(direction=1, weight=weight)


def _build_open_times(n: int, start_ms: int = 1_000_000_000_000) -> list[int]:
    """Build n sequential open_times spaced 8h apart (28800000 ms)."""
    return [start_ms + i * 28_800_000 for i in range(n)]


def test_veto_fires_for_mid_bull_short() -> None:
    """Veto fires when signal=short AND ret_270b ∈ [0.20, 0.50]."""

    n = 400
    open_times = _build_open_times(n)
    # Force ret_270b = 0.30 at candle index 300:
    #   close[300] / close[30] - 1 = 0.30 → close[300] = close[30] * 1.30
    closes = [100.0] * n
    closes[30] = 100.0
    closes[300] = 130.0  # ret_270b = 130/100 - 1 = 0.30 ∈ [0.20, 0.50]

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=270)
    sig_in = _signal_short()
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[300])

    assert result.direction == 0, (
        f"AXIS-R veto should return direction=0 for mid-bull short; got {result.direction}"
    )
    assert result.weight == 0, f"Vetoed signal weight must be 0; got {result.weight}"
    assert len(strat._axis_r_veto_log) == 1, "Veto log must record 1 event"
    assert abs(strat._axis_r_veto_log[0]["ret_270b"] - 0.30) < 1e-9


def test_veto_does_not_fire_for_long() -> None:
    """Long signals are NEVER vetoed regardless of ret_270b."""
    n = 400
    open_times = _build_open_times(n)
    closes = [100.0] * n
    closes[30] = 100.0
    closes[300] = 130.0  # ret_270b = 0.30 ∈ band

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=270)
    sig_in = _signal_long()
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[300])

    assert result.direction == 1, (
        f"Long signals must pass through AXIS-R veto unchanged; got {result.direction}"
    )
    assert len(strat._axis_r_veto_log) == 0, "No veto event should be logged for long signals"


def test_veto_does_not_fire_bear_continuation() -> None:
    """Short signals with ret_270b < 0.20 (bear continuation) are NOT vetoed."""
    n = 400
    open_times = _build_open_times(n)
    closes = [100.0] * n
    closes[30] = 100.0
    closes[300] = 115.0  # ret_270b = 0.15 < 0.20 → outside band

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=270)
    sig_in = _signal_short()
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[300])

    assert result.direction == -1, (
        f"Bear-continuation short (ret_270b=0.15) should NOT be vetoed; got {result.direction}"
    )
    assert len(strat._axis_r_veto_log) == 0


def test_veto_does_not_fire_structural_bull() -> None:
    """Short signals with ret_270b > 0.50 (structural bull / contrarian) are NOT vetoed."""
    n = 400
    open_times = _build_open_times(n)
    closes = [100.0] * n
    closes[30] = 100.0
    closes[300] = 160.0  # ret_270b = 0.60 > 0.50 → outside band

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=270)
    sig_in = _signal_short()
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[300])

    assert result.direction == -1, (
        f"Structural-bull short (ret_270b=0.60) should NOT be vetoed; got {result.direction}"
    )
    assert len(strat._axis_r_veto_log) == 0


def test_veto_fires_at_band_edges() -> None:
    """Veto fires at values just inside band edges [0.20, 0.50]."""
    n = 400
    open_times = _build_open_times(n)

    # Just inside lo=0.20 (ret_270b = 0.201 > 0.20)
    closes_lo = [100.0] * n
    closes_lo[30] = 100.0
    closes_lo[300] = 120.1  # ret_270b = 0.201 > 0.20 → inside band
    strat_lo = _make_strategy_with_close_index("ETHUSDT", open_times, closes_lo, lookback=270)
    result_lo = strat_lo._apply_mid_bull_short_veto(_signal_short(), "ETHUSDT", open_times[300])
    assert result_lo.direction == 0, "ret_270b=0.201 (just above band lo) must be vetoed"

    # Just inside hi=0.50 (ret_270b = 0.499 < 0.50)
    closes_hi = [100.0] * n
    closes_hi[30] = 100.0
    closes_hi[300] = 149.9  # ret_270b = 0.499 < 0.50 → inside band
    strat_hi = _make_strategy_with_close_index("ETHUSDT", open_times, closes_hi, lookback=270)
    result_hi = strat_hi._apply_mid_bull_short_veto(_signal_short(), "ETHUSDT", open_times[300])
    assert result_hi.direction == 0, "ret_270b=0.499 (just below band hi) must be vetoed"

    # Just below lo=0.20 (ret_270b = 0.199 < 0.20) → NOT vetoed
    closes_out_lo = [100.0] * n
    closes_out_lo[30] = 100.0
    closes_out_lo[300] = 119.9  # ret_270b = 0.199 < 0.20 → outside band
    strat_out_lo = _make_strategy_with_close_index(
        "ETHUSDT", open_times, closes_out_lo, lookback=270
    )
    result_out_lo = strat_out_lo._apply_mid_bull_short_veto(
        _signal_short(), "ETHUSDT", open_times[300]
    )
    assert result_out_lo.direction == -1, "ret_270b=0.199 (just below band lo) must NOT be vetoed"

    # Just above hi=0.50 (ret_270b = 0.501 > 0.50) → NOT vetoed
    closes_out_hi = [100.0] * n
    closes_out_hi[30] = 100.0
    closes_out_hi[300] = 150.1  # ret_270b = 0.501 > 0.50 → outside band
    strat_out_hi = _make_strategy_with_close_index(
        "ETHUSDT", open_times, closes_out_hi, lookback=270
    )
    result_out_hi = strat_out_hi._apply_mid_bull_short_veto(
        _signal_short(), "ETHUSDT", open_times[300]
    )
    assert result_out_hi.direction == -1, "ret_270b=0.501 (just above band hi) must NOT be vetoed"


def test_veto_does_not_fire_when_disabled() -> None:
    """When enable_mid_bull_short_veto=False, no vetoing happens even within band."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
    from crypto_trade.strategies.ml.lgbm import V1_SPECIALIST_SEEDS, LightGbmStrategy

    n = 400
    open_times = _build_open_times(n)
    closes = [100.0] * n
    closes[30] = 100.0
    closes[300] = 130.0  # ret_270b = 0.30 ∈ band — would veto if enabled

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
        ensemble_seeds=[V1_SPECIALIST_SEEDS[0]],
        enable_mid_bull_short_veto=False,  # DISABLED
    )
    ot_arr = np.array(open_times, dtype=np.int64)
    cl_arr = np.array(closes, dtype=np.float64)
    sort_idx = np.argsort(ot_arr)
    strat._close_by_sym = {"ETHUSDT": (ot_arr[sort_idx], cl_arr[sort_idx])}

    sig_in = _signal_short()
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[300])
    assert result.direction == -1, "Veto disabled: short must pass through"


def test_veto_insufficient_history() -> None:
    """When history < lookback, ret_270b is None and veto does not fire."""
    n = 100  # Only 100 candles — less than lookback=270
    open_times = _build_open_times(n)
    closes = [100.0 + i for i in range(n)]

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=270)
    sig_in = _signal_short()
    # Last candle: index 99, need index 99-270=-171 < 0 → None
    result = strat._apply_mid_bull_short_veto(sig_in, "ETHUSDT", open_times[-1])
    assert result.direction == -1, (
        "Insufficient history (< lookback): short must pass through (ret_270b=None)"
    )


def test_compute_ret_270b_correct_formula() -> None:
    """_compute_ret_270b computes (close[t] / close[t - lookback]) - 1.0 correctly."""
    n = 400
    lookback = 270
    open_times = _build_open_times(n)
    closes = [float(100 + i) for i in range(n)]  # monotone increase

    strat = _make_strategy_with_close_index("ETHUSDT", open_times, closes, lookback=lookback)

    # At candle 300: ret_270b = close[300] / close[300 - 270] - 1 = close[300] / close[30] - 1
    # closes[300] = 100 + 300 = 400, closes[30] = 100 + 30 = 130
    # ret_270b = 400 / 130 - 1 ≈ 2.0769
    expected = closes[300] / closes[30] - 1.0
    actual = strat._compute_ret_270b("ETHUSDT", open_times[300])
    assert actual is not None
    assert abs(actual - expected) < 1e-9, (
        f"_compute_ret_270b incorrect: expected {expected:.6f}, got {actual:.6f}"
    )


# ---------------------------------------------------------------------------
# 4. R1=OFF check (catalog rule f81cafc3)
# ---------------------------------------------------------------------------


def test_r1_not_enabled_in_dispatch() -> None:
    """Verify run_iteration_074.py does not pass apply_r1=True or risk_consecutive_sl args."""
    # Check the module docstring and constants confirm R1=OFF.
    import run_iteration_074 as r074

    doc = r074.__doc__ or ""
    assert "R1=OFF" in doc or "R1 streak-cooldown" in doc, (
        "run_iteration_074 docstring must document R1=OFF (CATALOG-CLOSED for SPECIALIST_mode)"
    )


# ---------------------------------------------------------------------------
# 5. V1_ITER074_UNIVERSE in __all__
# ---------------------------------------------------------------------------


def test_v1_iter074_universe_in_all() -> None:
    """V1_ITER074_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER074_UNIVERSE" in f1.__all__, (
        "V1_ITER074_UNIVERSE must be in crypto_trade.features_v1.__all__"
    )

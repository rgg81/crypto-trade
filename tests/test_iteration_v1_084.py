"""Tests for iter-v1/084 — CRVUSDT SPECIALIST (oi_price_divergence_30 + R-FADE gate).

Covers:
1. V1_ITER084_UNIVERSE constant: importable, correct symbol, in __all__.
2. run_iteration_084.py: importable, ITERATION_LABEL=="v1-084", ITERATION_NUMBER==84.
3. Methodology constants: 49-col count (CHANGED from 48), V1_SPECIALIST_SEED_COUNT=50,
   V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91, OOS_CUTOFF_MS.
4. oi_price_divergence_30 in V1_FEATURE_COLUMNS_PRUNED at alphabetically correct position.
5. Dispatch presence: "v1-084" appears in run_baseline_v1.py source,
   references V1_ITER084_UNIVERSE, CRVUSDT, and Model_A_CRV_specialist_084.
6. R-FADE gate: enable_oi_divergence_fade_gate parameter present in LightGbmStrategy.
7. R-FADE gate logic unit test: fires when |oi_div| > fade_z AND sign opposes signal.
8. R-FADE gate pass-through: does NOT fire when |oi_div| <= fade_z.
9. R-FADE gate pass-through: does NOT fire when sign agrees.
10. Feature computation: add_oi_price_divergence_30_feature returns correct column.
11. Past-only invariant: oi_price_divergence_30 uses only past OI data.
12. CRVUSDT parquet: has 49 columns from V1_FEATURE_COLUMNS_PRUNED.
13. Track isolation: no features_v2/features_v3 imports in open_interest_v1.py.
14. V1_ITER084_UNIVERSE not in V1_EXCLUDED_SYMBOLS.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

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


def test_v1_iter084_universe_import() -> None:
    """V1_ITER084_UNIVERSE is importable and == ('CRVUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER084_UNIVERSE

    assert V1_ITER084_UNIVERSE == ("CRVUSDT",), (
        f"V1_ITER084_UNIVERSE must be ('CRVUSDT',); got {V1_ITER084_UNIVERSE}"
    )


def test_v1_iter084_universe_in_all() -> None:
    """V1_ITER084_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER084_UNIVERSE" in f1.__all__, (
        "V1_ITER084_UNIVERSE must be in crypto_trade.features_v1.__all__"
    )


def test_runner_import() -> None:
    """run_iteration_084 imports without error and exposes required attrs."""
    import importlib
    import sys

    if "run_iteration_084" in sys.modules:
        del sys.modules["run_iteration_084"]
    mod = importlib.import_module("run_iteration_084")
    assert hasattr(mod, "main")
    assert hasattr(mod, "ITERATION_LABEL")
    assert mod.ITERATION_LABEL == "v1-084"
    assert hasattr(mod, "ITERATION_NUMBER")
    assert mod.ITERATION_NUMBER == 84
    assert hasattr(mod, "OI_DIVERGENCE_FADE_Z")
    assert hasattr(mod, "PRE_FEATURE_PARQUET_HASH_16")
    assert hasattr(mod, "POST_FEATURE_PARQUET_HASH_16")


# ---------------------------------------------------------------------------
# 2. Methodology constants
# ---------------------------------------------------------------------------


def test_v1_feature_columns_pruned_49_cols() -> None:
    """V1_FEATURE_COLUMNS_PRUNED must be 49 columns (48 base + oi_price_divergence_30)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 49, (
        f"V1_FEATURE_COLUMNS_PRUNED must have 49 cols at iter-v1/084; "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "Expected 48 base + oi_price_divergence_30 = 49."
    )


def test_oi_price_divergence_30_in_feature_columns() -> None:
    """oi_price_divergence_30 is in V1_FEATURE_COLUMNS_PRUNED."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert "oi_price_divergence_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "oi_price_divergence_30 must be in V1_FEATURE_COLUMNS_PRUNED at iter-v1/084"
    )


def test_oi_price_divergence_30_position_alphabetical() -> None:
    """oi_price_divergence_30 is between oi_delta_30_z90 and regime_momentum_signed_5d."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    cols = list(V1_FEATURE_COLUMNS_PRUNED)
    idx_div = cols.index("oi_price_divergence_30")
    idx_delta = cols.index("oi_delta_30_z90")
    idx_regime = cols.index("regime_momentum_signed_5d")
    assert idx_delta < idx_div < idx_regime, (
        f"oi_price_divergence_30 (pos {idx_div}) must be between "
        f"oi_delta_30_z90 (pos {idx_delta}) and regime_momentum_signed_5d (pos {idx_regime})"
    )


def test_specialist_constants() -> None:
    """V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, seeds 42..91."""
    from crypto_trade.strategies.ml.lgbm import (
        V1_SPECIALIST_OPTUNA_TRIALS,
        V1_SPECIALIST_SEED_COUNT,
        V1_SPECIALIST_SEEDS,
    )

    assert V1_SPECIALIST_SEED_COUNT == 50
    assert V1_SPECIALIST_OPTUNA_TRIALS == 30
    assert len(V1_SPECIALIST_SEEDS) == 50
    assert V1_SPECIALIST_SEEDS[0] == 42
    assert V1_SPECIALIST_SEEDS[-1] == 91


def test_oos_cutoff_ms_sacred() -> None:
    """OOS_CUTOFF_MS is the sacred 2025-03-24 constant (1742774400000)."""
    from crypto_trade.config import OOS_CUTOFF_MS

    assert OOS_CUTOFF_MS == 1742774400000, (
        f"OOS_CUTOFF_MS must be 1742774400000 (2025-03-24); got {OOS_CUTOFF_MS}"
    )


def test_runner_iteration_label_and_number() -> None:
    """Runner ITERATION_LABEL='v1-084' and ITERATION_NUMBER=84."""
    import run_iteration_084 as r084

    assert r084.ITERATION_LABEL == "v1-084"
    assert r084.ITERATION_NUMBER == 84


def test_runner_fade_z_constant() -> None:
    """OI_DIVERGENCE_FADE_Z is 2.0 (pre-registered IS-calibrated threshold)."""
    import run_iteration_084 as r084

    assert r084.OI_DIVERGENCE_FADE_Z == 2.0, (
        f"OI_DIVERGENCE_FADE_Z must be 2.0 (pre-registered); got {r084.OI_DIVERGENCE_FADE_Z}"
    )


def test_runner_pre_feature_hash() -> None:
    """PRE_FEATURE_PARQUET_HASH_16 matches the known CRVUSDT pre-regen hash."""
    import run_iteration_084 as r084

    assert r084.PRE_FEATURE_PARQUET_HASH_16 == "e0292892e28a0f51", (
        f"PRE_FEATURE_PARQUET_HASH_16 must be 'e0292892e28a0f51'; "
        f"got {r084.PRE_FEATURE_PARQUET_HASH_16!r}"
    )


# ---------------------------------------------------------------------------
# 3. Dispatch presence in run_baseline_v1.py
# ---------------------------------------------------------------------------


def test_dispatch_branch_present_in_runner() -> None:
    """run_baseline_v1.py contains the 'v1-084' dispatch branch."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists(), f"run_baseline_v1.py not found at {runner_path}"
    src = runner_path.read_text(encoding="utf-8")
    assert 'iteration_label == "v1-084"' in src, (
        "run_baseline_v1.py must contain dispatch branch 'elif iteration_label == \"v1-084\"'"
    )
    assert "V1_ITER084_UNIVERSE" in src, (
        "run_baseline_v1.py must reference V1_ITER084_UNIVERSE in the dispatch branch"
    )
    assert "CRVUSDT" in src, (
        "run_baseline_v1.py dispatch branch must wire CRVUSDT as the cohort symbol"
    )
    assert "Model_A_CRV_specialist_084" in src, (
        "run_baseline_v1.py dispatch branch must name the model 'Model_A_CRV_specialist_084'"
    )
    assert "enable_oi_divergence_fade_gate=True" in src, (
        "run_baseline_v1.py dispatch branch must enable R-FADE gate for CRV specialist"
    )


def test_dispatch_import_in_runner() -> None:
    """run_baseline_v1.py imports V1_ITER084_UNIVERSE from features_v1."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER084_UNIVERSE" in src


# ---------------------------------------------------------------------------
# 4. R-FADE gate parameter and logic
# ---------------------------------------------------------------------------


def test_lgbm_strategy_rfade_params_exist() -> None:
    """LightGbmStrategy accepts enable_oi_divergence_fade_gate parameter."""
    import inspect

    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    sig = inspect.signature(LightGbmStrategy.__init__)
    assert "enable_oi_divergence_fade_gate" in sig.parameters, (
        "LightGbmStrategy must accept enable_oi_divergence_fade_gate parameter"
    )
    assert "oi_divergence_fade_z" in sig.parameters, (
        "LightGbmStrategy must accept oi_divergence_fade_z parameter"
    )
    assert "oi_divergence_fade_column" in sig.parameters, (
        "LightGbmStrategy must accept oi_divergence_fade_column parameter"
    )


def _make_minimal_strategy(
    enable_fade: bool = False,
    fade_z: float = 2.0,
    fade_col: str = "oi_price_divergence_30",
):  # type: ignore[return]
    """Create a minimal LightGbmStrategy for gate testing (no training)."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    strat = LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=5,
        label_tp_pct=5.8,
        label_sl_pct=2.9,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        verbose=0,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42],
        feature_columns=(fade_col, "dummy_col"),
        ood_enabled=False,
        enable_oi_divergence_fade_gate=enable_fade,
        oi_divergence_fade_z=fade_z,
        oi_divergence_fade_column=fade_col,
    )
    # Manually set _selected_cols so gate can look up column index
    strat._selected_cols = [fade_col, "dummy_col"]
    return strat


def test_rfade_gate_fires_long_contradicted() -> None:
    """R-FADE fires: LONG signal + oi_div < -fade_z (bearish OI contradicts long)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([-2.5, 0.0])  # oi_price_divergence_30 = -2.5 < -2.0
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 0, "R-FADE must VETO long signal when oi_div=-2.5 < -fade_z=-2.0"
    assert result.weight == 0


def test_rfade_gate_fires_short_contradicted() -> None:
    """R-FADE fires: SHORT signal + oi_div > +fade_z (bullish OI contradicts short)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([2.5, 0.0])  # oi_price_divergence_30 = +2.5 > +2.0
    signal = Signal(direction=-1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 0, "R-FADE must VETO short signal when oi_div=+2.5 > +fade_z=+2.0"
    assert result.weight == 0


def test_rfade_gate_pass_through_below_threshold() -> None:
    """R-FADE does NOT fire when |oi_div| <= fade_z."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([-1.5, 0.0])  # |oi_div| = 1.5 < 2.0
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 1, "R-FADE must NOT fire when |oi_div|=1.5 <= fade_z=2.0"


def test_rfade_gate_pass_through_sign_agrees_long() -> None:
    """R-FADE does NOT fire when oi_div > 0 (bullish OI agrees with long)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([2.5, 0.0])  # oi_div > 0: bullish OI, LONG trade agrees
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 1, "R-FADE must NOT fire when oi_div > 0 and signal is LONG (agree)"


def test_rfade_gate_pass_through_sign_agrees_short() -> None:
    """R-FADE does NOT fire when oi_div < -fade_z but signal is SHORT (agrees)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([-2.5, 0.0])  # oi_div < -2.0: bearish OI, SHORT trade agrees
    signal = Signal(direction=-1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == -1, (
        "R-FADE must NOT fire when oi_div < -fade_z and signal is SHORT (agree)"
    )


def test_rfade_gate_disabled_by_default() -> None:
    """R-FADE gate does NOT fire when enable_oi_divergence_fade_gate=False (default)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=False, fade_z=2.0)
    feat_row = np.array([-3.0, 0.0])  # Would fire if enabled
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 1, "R-FADE must NOT fire when enable_oi_divergence_fade_gate=False"


def test_rfade_gate_nan_passthrough() -> None:
    """R-FADE gate passes through when oi_div is NaN (conservative; cannot evaluate)."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([np.nan, 0.0])
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    result = strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert result.direction == 1, "R-FADE must pass through when oi_div is NaN"


def test_rfade_log_appended_on_fire() -> None:
    """R-FADE log accumulates entries when gate fires."""
    from crypto_trade.backtest_models import Signal

    strat = _make_minimal_strategy(enable_fade=True, fade_z=2.0)
    feat_row = np.array([-2.5, 0.0])
    signal = Signal(direction=1, weight=60, tp_pct=None, sl_pct=None, confidence=0.6)
    assert len(strat._oi_divergence_fade_log) == 0
    strat._apply_oi_divergence_fade_gate(signal, feat_row, "CRVUSDT", 1234567890000)
    assert len(strat._oi_divergence_fade_log) == 1
    entry = strat._oi_divergence_fade_log[0]
    assert entry["oi_div_val"] == pytest.approx(-2.5)
    assert entry["direction_pre_fade"] == 1


# ---------------------------------------------------------------------------
# 5. Feature computation unit tests
# ---------------------------------------------------------------------------


def _make_kline_df(n: int = 250, seed: int = 42, symbol: str = "CRVUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with open_time, close, and symbol columns."""
    rng = np.random.default_rng(seed)
    start_ms = 1_600_000_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": rng.uniform(1, 5, n),
            "high": rng.uniform(1, 5, n),
            "low": rng.uniform(1, 5, n),
            "close": np.abs(rng.uniform(1, 5, n)),
            "volume": rng.uniform(1000, 100000, n),
            "symbol": symbol,
        }
    )


def _make_oi_df(klines: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create OI DataFrame aligned to kline open_times."""
    rng = np.random.default_rng(seed)
    n = len(klines)
    oi_levels = 10000.0 + np.cumsum(rng.normal(0, 50.0, n))
    oi_levels = np.maximum(oi_levels, 1.0)
    return pd.DataFrame(
        {
            "open_time": klines["open_time"].values,
            "sum_open_interest": oi_levels,
        }
    )


def test_add_oi_price_divergence_30_feature_smoke() -> None:
    """add_oi_price_divergence_30_feature returns DataFrame with oi_price_divergence_30 column."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    klines = _make_kline_df(250)
    oi_df = _make_oi_df(klines)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        oi_dir = tmp / "open_interest" / "CRVUSDT"
        oi_dir.mkdir(parents=True)
        oi_df.to_csv(oi_dir / "8h.csv", index=False)

        result = add_oi_price_divergence_30_feature(klines, data_dir=tmp)

    assert "oi_price_divergence_30" in result.columns
    assert len(result) == len(klines)


def test_oi_price_divergence_30_past_only() -> None:
    """oi_price_divergence_30 does not use future values — past-only invariant.

    Mutate one OI bar at position t_target+1 (one bar after target) and verify
    the feature value at t_target is UNCHANGED. If feature at t_target depends on
    t_target+1, this would fail.
    """
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    klines = _make_kline_df(250)
    oi_df_base = _make_oi_df(klines)

    t_target = 180  # well past burn-in (~120 bars)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        oi_dir = tmp / "open_interest" / "CRVUSDT"
        oi_dir.mkdir(parents=True)

        # Baseline run
        oi_df_base.to_csv(oi_dir / "8h.csv", index=False)
        result_base = add_oi_price_divergence_30_feature(klines, data_dir=tmp)
        val_at_target = result_base["oi_price_divergence_30"].iloc[t_target]

        # Mutate bar at t_target + 1 (future relative to t_target)
        oi_df_mutated = oi_df_base.copy()
        oi_df_mutated.loc[t_target + 1, "sum_open_interest"] = 9_999_999.0
        oi_df_mutated.to_csv(oi_dir / "8h.csv", index=False)
        result_mutated = add_oi_price_divergence_30_feature(klines, data_dir=tmp)
        val_at_target_mutated = result_mutated["oi_price_divergence_30"].iloc[t_target]

    assert val_at_target == pytest.approx(val_at_target_mutated, abs=1e-9), (
        f"Past-only invariant VIOLATED: feature at t={t_target} changed "
        f"when future bar t={t_target + 1} was mutated. "
        f"Base={val_at_target:.6f}, Mutated={val_at_target_mutated:.6f}"
    )


def test_oi_price_divergence_30_burnin() -> None:
    """First 120 rows of oi_price_divergence_30 are NaN (30-bar delta + 90-bar z + extra shift)."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    klines = _make_kline_df(250)
    oi_df = _make_oi_df(klines)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        oi_dir = tmp / "open_interest" / "CRVUSDT"
        oi_dir.mkdir(parents=True)
        oi_df.to_csv(oi_dir / "8h.csv", index=False)
        result = add_oi_price_divergence_30_feature(klines, data_dir=tmp)

    # At least the first ~120 rows should be NaN (30 delta + 90 z-score + 1 extra shift = 121)
    feature_vals = result["oi_price_divergence_30"].values
    n_nan_leading = 0
    for v in feature_vals:
        if np.isnan(v):
            n_nan_leading += 1
        else:
            break
    assert n_nan_leading >= 120, (
        f"Expected at least 120 leading NaN rows (burn-in); got {n_nan_leading}"
    )


def test_oi_price_divergence_30_clip() -> None:
    """oi_price_divergence_30 values are clipped to [-10, +10]."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    klines = _make_kline_df(300)
    # Create extreme OI swing to produce large z-score
    oi_df = _make_oi_df(klines)
    # Spike OI massively in the middle to create very large z-score
    oi_df.loc[200:230, "sum_open_interest"] = 1e9

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        oi_dir = tmp / "open_interest" / "CRVUSDT"
        oi_dir.mkdir(parents=True)
        oi_df.to_csv(oi_dir / "8h.csv", index=False)
        result = add_oi_price_divergence_30_feature(klines, data_dir=tmp)

    feature_vals = result["oi_price_divergence_30"].dropna().values
    assert (feature_vals >= -10.0).all(), "oi_price_divergence_30 must be >= -10 (clip floor)"
    assert (feature_vals <= 10.0).all(), "oi_price_divergence_30 must be <= +10 (clip ceiling)"


def test_oi_price_divergence_30_intermediates_not_retained() -> None:
    """Intermediate columns (oi_delta_30, ret_30, div_raw) are NOT in output DataFrame."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    klines = _make_kline_df(250)
    oi_df = _make_oi_df(klines)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        oi_dir = tmp / "open_interest" / "CRVUSDT"
        oi_dir.mkdir(parents=True)
        oi_df.to_csv(oi_dir / "8h.csv", index=False)
        result = add_oi_price_divergence_30_feature(klines, data_dir=tmp)

    assert "oi_delta_30" not in result.columns, "oi_delta_30 must NOT be in output (NON_FEATURE)"
    assert "ret_30" not in result.columns, "ret_30 must NOT be in output (NON_FEATURE)"
    assert "div_raw" not in result.columns, "div_raw must NOT be in output (NON_FEATURE)"


# ---------------------------------------------------------------------------
# 6. CRVUSDT parquet column audit
# ---------------------------------------------------------------------------


def test_crvusdt_parquet_exists() -> None:
    """CRVUSDT feature parquet exists at data/features/CRVUSDT_8h_features.parquet."""
    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "CRVUSDT_8h_features.parquet"
    )
    assert parquet_path.exists(), (
        f"CRVUSDT feature parquet not found at {parquet_path}. "
        "Regenerate with: uv run crypto-trade features --symbols CRVUSDT --interval 8h "
        "--track v1 --format parquet"
    )


def test_crvusdt_parquet_has_oi_price_divergence_30() -> None:
    """CRVUSDT parquet contains oi_price_divergence_30 column (post-regen)."""
    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "CRVUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"CRVUSDT parquet not found at {parquet_path}")
    df = pd.read_parquet(parquet_path, columns=["oi_price_divergence_30"])
    assert "oi_price_divergence_30" in df.columns
    # Should have non-NaN values past burn-in (~120 bars)
    assert df["oi_price_divergence_30"].notna().sum() > 100


def test_crvusdt_parquet_has_all_49_v1_feature_columns() -> None:
    """CRVUSDT parquet contains all 49 V1_FEATURE_COLUMNS_PRUNED columns."""
    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "CRVUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"CRVUSDT parquet not found at {parquet_path}")

    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    df = pd.read_parquet(parquet_path, columns=list(V1_FEATURE_COLUMNS_PRUNED))
    missing = [c for c in V1_FEATURE_COLUMNS_PRUNED if c not in df.columns]
    assert not missing, (
        f"CRVUSDT parquet is missing {len(missing)} of 49 V1_FEATURE_COLUMNS_PRUNED columns:\n"
        + "\n".join(f"  {c}" for c in missing)
    )
    assert len(df.columns) == 49


# ---------------------------------------------------------------------------
# 7. Track isolation
# ---------------------------------------------------------------------------


def test_open_interest_v1_no_v2_imports() -> None:
    """open_interest_v1.py has no features_v2/v3 import statements (track isolation)."""
    module_path = (
        Path(__file__).parent.parent
        / "src"
        / "crypto_trade"
        / "features_v1"
        / "open_interest_v1.py"
    )
    src = module_path.read_text(encoding="utf-8")
    # Check actual import lines only (not docstring comments that may mention them)
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text, (
        "open_interest_v1.py must NOT import from features_v2 (track isolation)"
    )
    assert "from crypto_trade.features_v3" not in import_text, (
        "open_interest_v1.py must NOT import from features_v3 (track isolation)"
    )


# ---------------------------------------------------------------------------
# 8. Symbol eligibility
# ---------------------------------------------------------------------------


def test_crv_not_in_v1_excluded_symbols() -> None:
    """CRVUSDT is NOT in V1_EXCLUDED_SYMBOLS (eligible for v1 universe)."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    assert "CRVUSDT" not in V1_EXCLUDED_SYMBOLS, (
        f"CRVUSDT must NOT be in V1_EXCLUDED_SYMBOLS; current exclusion list: {V1_EXCLUDED_SYMBOLS}"
    )


def test_assert_v1_universe_passes_for_crv() -> None:
    """assert_v1_universe(['CRVUSDT']) must pass (no exclusion violation)."""
    from crypto_trade.features_v1 import assert_v1_universe

    assert_v1_universe(["CRVUSDT"])  # Should not raise

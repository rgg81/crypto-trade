"""Tests for iter-v1/085 — UNIUSDT SPECIALIST (4-feature mean-reversion set).

Covers:
1. V1_ITER085_UNIVERSE constant: importable, correct symbol, in __all__.
2. V1_ITER085_FEATURE_COLUMNS: 52 cols (LOCAL), global PRUNED stays 48.
3. 4 new features present in V1_ITER085_FEATURE_COLUMNS, NOT in global PRUNED.
4. run_iteration_085.py: importable, ITERATION_LABEL=="v1-085", ITERATION_NUMBER==85.
5. Methodology constants: V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30,
   seeds 42..91, OOS_CUTOFF_MS.
6. Feature hash: 52-col hash prefix == c8b8e0a87abb280a.
7. Dispatch presence: "v1-085" appears in run_baseline_v1.py source.
8. rev_extension_z_3: smoke test, past-only, burn-in, clip, sign-flip semantics.
9. vol_state_z_natr_30: smoke test, past-only, burn-in, clip.
10. rev_halflife_50: smoke test, burn-in, clip.
11. rev_vol_gate_signed: smoke test, gate=0 in vol-expansion, gate=1 in compressed-vol.
12. add_composed_v1_085_features: all 4 cols in output.
13. Track isolation: no features_v2/features_v3 imports in new modules.
14. UNIUSDT parquet: has all 52 V1_ITER085_FEATURE_COLUMNS columns.
15. assert_v1_universe passes for UNIUSDT.
"""

from __future__ import annotations

import hashlib
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


def _make_kline_df(n: int = 300, seed: int = 42, symbol: str = "UNIUSDT") -> pd.DataFrame:
    """Create a minimal kline-like DataFrame with OHLCV columns."""
    rng = np.random.default_rng(seed)
    start_ms = 1_600_000_000_000
    interval_ms = 8 * 3600 * 1000
    open_times = [start_ms + i * interval_ms for i in range(n)]
    close_prices = np.abs(rng.uniform(3.0, 10.0, n))
    high = close_prices * rng.uniform(1.001, 1.02, n)
    low = close_prices * rng.uniform(0.98, 0.999, n)
    return pd.DataFrame(
        {
            "open_time": open_times,
            "open": close_prices * rng.uniform(0.999, 1.001, n),
            "high": high,
            "low": low,
            "close": close_prices,
            "volume": rng.uniform(1000, 100000, n),
            "symbol": symbol,
        }
    )


# ---------------------------------------------------------------------------
# 1. Universe and feature columns
# ---------------------------------------------------------------------------


def test_v1_iter085_universe_import() -> None:
    """V1_ITER085_UNIVERSE is importable and == ('UNIUSDT',)."""
    from crypto_trade.features_v1 import V1_ITER085_UNIVERSE

    assert V1_ITER085_UNIVERSE == ("UNIUSDT",), (
        f"V1_ITER085_UNIVERSE must be ('UNIUSDT',); got {V1_ITER085_UNIVERSE}"
    )


def test_v1_iter085_universe_in_all() -> None:
    """V1_ITER085_UNIVERSE is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER085_UNIVERSE" in f1.__all__


def test_v1_iter085_feature_columns_count() -> None:
    """V1_ITER085_FEATURE_COLUMNS must have exactly 52 cols; global PRUNED stays 48."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER085_FEATURE_COLUMNS

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"Global V1_FEATURE_COLUMNS_PRUNED must stay at 48; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
    )
    assert len(V1_ITER085_FEATURE_COLUMNS) == 52, (
        f"V1_ITER085_FEATURE_COLUMNS must have 52 cols; got {len(V1_ITER085_FEATURE_COLUMNS)}"
    )


def test_v1_iter085_feature_columns_in_all() -> None:
    """V1_ITER085_FEATURE_COLUMNS is exported in features_v1.__all__."""
    import crypto_trade.features_v1 as f1

    assert "V1_ITER085_FEATURE_COLUMNS" in f1.__all__


def test_4_new_features_in_iter085_not_in_global_pruned() -> None:
    """All 4 new features in V1_ITER085_FEATURE_COLUMNS but NOT in global PRUNED."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_ITER085_FEATURE_COLUMNS

    expected_new = {
        "rev_extension_z_3",
        "vol_state_z_natr_30",
        "rev_halflife_50",
        "rev_vol_gate_signed",
    }
    for feat in expected_new:
        assert feat in V1_ITER085_FEATURE_COLUMNS, f"{feat} must be in V1_ITER085_FEATURE_COLUMNS"
        assert feat not in V1_FEATURE_COLUMNS_PRUNED, (
            f"{feat} must NOT be in global V1_FEATURE_COLUMNS_PRUNED (LOCAL-ONLY)"
        )


def test_global_pruned_unchanged_at_48() -> None:
    """V1_FEATURE_COLUMNS_PRUNED is exactly 48 (unchanged from /084 baseline)."""
    from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED

    assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
        f"CRITICAL: V1_FEATURE_COLUMNS_PRUNED must be 48 (unchanged); "
        f"got {len(V1_FEATURE_COLUMNS_PRUNED)}. "
        "The /084 lesson: NEVER add iter-specific features to the global PRUNED."
    )


# ---------------------------------------------------------------------------
# 2. Feature hash
# ---------------------------------------------------------------------------


def test_features_hash_52col() -> None:
    """52-col feature hash matches pre-registered c8b8e0a87abb280a."""
    from crypto_trade.features_v1 import V1_ITER085_FEATURE_COLUMNS

    actual_hash = _compute_features_hash(V1_ITER085_FEATURE_COLUMNS)
    assert actual_hash[:16] == "c8b8e0a87abb280a", (
        f"52-col feature hash prefix mismatch. "
        f"Expected: c8b8e0a87abb280a, Got: {actual_hash[:16]}. "
        "V1_ITER085_FEATURE_COLUMNS has changed from the pre-registered set."
    )


# ---------------------------------------------------------------------------
# 3. Runner constants
# ---------------------------------------------------------------------------


def test_runner_import() -> None:
    """run_iteration_085 imports without error and has ITERATION_LABEL='v1-085'."""
    import importlib
    import sys

    if "run_iteration_085" in sys.modules:
        del sys.modules["run_iteration_085"]
    mod = importlib.import_module("run_iteration_085")
    assert hasattr(mod, "main")
    assert mod.ITERATION_LABEL == "v1-085"
    assert mod.ITERATION_NUMBER == 85
    assert hasattr(mod, "FEATURES_BASE_HASH_52COL")
    assert hasattr(mod, "ITER085_NEW_FEATURES")
    assert len(mod.ITER085_NEW_FEATURES) == 4


def test_runner_hash_constant() -> None:
    """FEATURES_BASE_HASH_52COL in runner matches computed hash."""
    import run_iteration_085 as r085

    assert r085.FEATURES_BASE_HASH_52COL == "c8b8e0a87abb280a", (
        f"Runner FEATURES_BASE_HASH_52COL mismatch: {r085.FEATURES_BASE_HASH_52COL!r}"
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
    """OOS_CUTOFF_MS must be 1742774400000 (2025-03-24, unchanged)."""
    from crypto_trade.config import OOS_CUTOFF_MS

    assert OOS_CUTOFF_MS == 1742774400000


# ---------------------------------------------------------------------------
# 4. Dispatch in run_baseline_v1.py
# ---------------------------------------------------------------------------


def test_dispatch_branch_present() -> None:
    """run_baseline_v1.py contains 'v1-085' dispatch with correct model name."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    assert runner_path.exists()
    src = runner_path.read_text(encoding="utf-8")
    assert 'iteration_label == "v1-085"' in src
    assert "V1_ITER085_UNIVERSE" in src
    assert "UNIUSDT" in src
    assert "Model_A_UNI_specialist_085" in src
    assert "V1_ITER085_FEATURE_COLUMNS" in src


def test_dispatch_import_in_runner() -> None:
    """run_baseline_v1.py imports V1_ITER085_FEATURE_COLUMNS and V1_ITER085_UNIVERSE."""
    runner_path = Path(__file__).parent.parent / "run_baseline_v1.py"
    src = runner_path.read_text(encoding="utf-8")
    assert "V1_ITER085_FEATURE_COLUMNS" in src
    assert "V1_ITER085_UNIVERSE" in src


# ---------------------------------------------------------------------------
# 5. rev_extension_z_3 feature tests
# ---------------------------------------------------------------------------


def test_rev_extension_z_3_smoke() -> None:
    """compute_rev_extension_z_3 returns df with rev_extension_z_3 column."""
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3

    df = _make_kline_df(200)
    result = compute_rev_extension_z_3(df)
    assert "rev_extension_z_3" in result.columns
    assert len(result) == len(df)


def test_rev_extension_z_3_past_only() -> None:
    """rev_extension_z_3 does not use future values — past-only invariant."""
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3

    df_base = _make_kline_df(200)
    t_target = 150
    result_base = compute_rev_extension_z_3(df_base)
    val_base = result_base["rev_extension_z_3"].iloc[t_target]

    # Mutate bar at t_target + 1 (future relative to t_target)
    df_mut = df_base.copy()
    df_mut.loc[df_mut.index[t_target + 1], "close"] = 1e6
    result_mut = compute_rev_extension_z_3(df_mut)
    val_mut = result_mut["rev_extension_z_3"].iloc[t_target]

    assert val_base == pytest.approx(val_mut, abs=1e-9), (
        f"Past-only VIOLATED: rev_extension_z_3 at t={t_target} changed "
        f"when future bar t={t_target + 1} was mutated."
    )


def test_rev_extension_z_3_burnin() -> None:
    """First ~53 rows of rev_extension_z_3 are NaN (3+50+1 = 54 burn-in)."""
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3

    df = _make_kline_df(200)
    result = compute_rev_extension_z_3(df)
    feature = result["rev_extension_z_3"].values
    n_nan = 0
    for v in feature:
        if np.isnan(v):
            n_nan += 1
        else:
            break
    assert n_nan >= 50, f"Expected at least 50 leading NaN rows; got {n_nan}"


def test_rev_extension_z_3_clip() -> None:
    """rev_extension_z_3 is clipped to [-5, +5]."""
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3

    df = _make_kline_df(200)
    result = compute_rev_extension_z_3(df)
    vals = result["rev_extension_z_3"].dropna().values
    assert (vals >= -5.0).all() and (vals <= 5.0).all(), (
        "rev_extension_z_3 must be clipped to [-5, +5]"
    )


def test_rev_extension_z_3_sign_flip_semantics() -> None:
    """Sign flip: positive 3-bar extension => negative raw_z => positive rev_extension_z_3.

    When the 3-bar return is ABOVE its rolling mean (positive extension = above average rally),
    raw_z > 0, and the sign-flipped feature rev_extension_z_3 = -raw_z < 0.
    The model should predict a FADE DOWN when this is negative.
    """
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3

    # Construct a scenario with a large positive 3-bar return at a specific bar
    n = 200
    df = _make_kline_df(n)
    df = df.copy()
    # Create a strong upward move over bars 160-163 (large positive 3-bar return at 163)
    df.loc[df.index[160], "close"] = 1.0
    df.loc[df.index[161], "close"] = 1.1
    df.loc[df.index[162], "close"] = 1.2
    df.loc[df.index[163], "close"] = 2.0  # Large rally: +100% in 3 bars

    result = compute_rev_extension_z_3(df)
    # rev_extension_z_3 at bar 163 (computed from bars ≤ 162 via shift(1))
    # This bar sees the rally up to bar 162
    # The feature at bar 164 uses bar 163's shifted value
    val_164 = result["rev_extension_z_3"].iloc[164]
    if not np.isnan(val_164):
        # After strong rally: raw_z should be positive, sign-flipped should be negative
        assert val_164 < 0, f"Expected rev_extension_z_3 < 0 after strong rally; got {val_164:.3f}"


# ---------------------------------------------------------------------------
# 6. vol_state_z_natr_30 feature tests
# ---------------------------------------------------------------------------


def test_vol_state_z_natr_30_smoke() -> None:
    """compute_vol_state_z_natr_30 returns df with vol_state_z_natr_30 column."""
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df = _make_kline_df(250)
    result = compute_vol_state_z_natr_30(df)
    assert "vol_state_z_natr_30" in result.columns
    assert len(result) == len(df)


def test_vol_state_z_natr_30_burnin() -> None:
    """First ~120 rows of vol_state_z_natr_30 are NaN (30+90+1 = 121 burn-in)."""
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df = _make_kline_df(250)
    result = compute_vol_state_z_natr_30(df)
    feature = result["vol_state_z_natr_30"].values
    n_nan = 0
    for v in feature:
        if np.isnan(v):
            n_nan += 1
        else:
            break
    assert n_nan >= 100, f"Expected at least 100 leading NaN rows; got {n_nan}"


def test_vol_state_z_natr_30_past_only() -> None:
    """vol_state_z_natr_30 does not use future values — past-only invariant."""
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df_base = _make_kline_df(250)
    t_target = 200
    result_base = compute_vol_state_z_natr_30(df_base)
    val_base = result_base["vol_state_z_natr_30"].iloc[t_target]

    df_mut = df_base.copy()
    # Set extreme vol at t_target+1 (future bar)
    df_mut.loc[df_mut.index[t_target + 1], "high"] = 1e6
    df_mut.loc[df_mut.index[t_target + 1], "low"] = 0.001
    result_mut = compute_vol_state_z_natr_30(df_mut)
    val_mut = result_mut["vol_state_z_natr_30"].iloc[t_target]

    assert val_base == pytest.approx(val_mut, abs=1e-6), (
        f"Past-only VIOLATED: vol_state_z_natr_30 at t={t_target} changed "
        f"when future bar t={t_target + 1} was mutated."
    )


def test_vol_state_z_natr_30_clip() -> None:
    """vol_state_z_natr_30 is clipped to [-5, +5]."""
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df = _make_kline_df(250)
    result = compute_vol_state_z_natr_30(df)
    vals = result["vol_state_z_natr_30"].dropna().values
    assert (vals >= -5.0).all() and (vals <= 5.0).all()


# ---------------------------------------------------------------------------
# 7. rev_halflife_50 feature tests
# ---------------------------------------------------------------------------


def test_rev_halflife_50_smoke() -> None:
    """compute_rev_halflife_50 returns df with rev_halflife_50 column."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_halflife_50

    df = _make_kline_df(300)
    result = compute_rev_halflife_50(df)
    assert "rev_halflife_50" in result.columns
    assert len(result) == len(df)


def test_rev_halflife_50_burnin() -> None:
    """First ~140 rows of rev_halflife_50 are NaN (50+90+1 = 141 burn-in)."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_halflife_50

    df = _make_kline_df(300)
    result = compute_rev_halflife_50(df)
    feature = result["rev_halflife_50"].values
    n_nan = 0
    for v in feature:
        if np.isnan(v):
            n_nan += 1
        else:
            break
    assert n_nan >= 100, f"Expected at least 100 leading NaN rows; got {n_nan}"


def test_rev_halflife_50_clip() -> None:
    """rev_halflife_50 is clipped to [-5, +5]."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_halflife_50

    df = _make_kline_df(300)
    result = compute_rev_halflife_50(df)
    vals = result["rev_halflife_50"].dropna().values
    assert (vals >= -5.0).all() and (vals <= 5.0).all()


# ---------------------------------------------------------------------------
# 8. rev_vol_gate_signed feature tests
# ---------------------------------------------------------------------------


def test_rev_vol_gate_signed_smoke() -> None:
    """compute_rev_vol_gate_signed returns df with rev_vol_gate_signed column."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_vol_gate_signed
    from crypto_trade.features_v1.mean_reversion_v1 import compute_rev_extension_z_3
    from crypto_trade.features_v1.volatility_v1 import compute_vol_state_z_natr_30

    df = _make_kline_df(250)
    df = compute_rev_extension_z_3(df)
    df = compute_vol_state_z_natr_30(df)
    result = compute_rev_vol_gate_signed(df)
    assert "rev_vol_gate_signed" in result.columns
    assert len(result) == len(df)


def test_rev_vol_gate_signed_gate_off_in_expansion() -> None:
    """rev_vol_gate_signed == 0 when vol_state_z_natr_30 > 1.0 (vol-expansion regime)."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_vol_gate_signed

    # Manually construct df with vol_state_z_natr_30 > 1.0 and known rev_extension_z_3
    n = 100
    df = pd.DataFrame(
        {
            "rev_extension_z_3": np.full(n, 2.0),
            "vol_state_z_natr_30": np.full(n, 1.5),  # > 1.0: gate OFF
        }
    )
    result = compute_rev_vol_gate_signed(df)
    vals = result["rev_vol_gate_signed"].values
    assert np.allclose(vals, 0.0, atol=1e-9), (
        "rev_vol_gate_signed must be 0 when vol_state_z_natr_30 > 1.0"
    )


def test_rev_vol_gate_signed_gate_on_in_compressed() -> None:
    """rev_vol_gate_signed == rev_extension_z_3 when vol_state_z_natr_30 <= 0 (compressed vol)."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_vol_gate_signed

    n = 100
    signal_val = 2.5
    df = pd.DataFrame(
        {
            "rev_extension_z_3": np.full(n, signal_val),
            "vol_state_z_natr_30": np.full(n, -0.5),  # <= 0: gate FULLY ON
        }
    )
    result = compute_rev_vol_gate_signed(df)
    vals = result["rev_vol_gate_signed"].values
    assert np.allclose(vals, signal_val, atol=1e-9), (
        "rev_vol_gate_signed must equal rev_extension_z_3 when vol_state_z_natr_30 <= 0"
    )


def test_rev_vol_gate_signed_missing_input_raises() -> None:
    """compute_rev_vol_gate_signed raises KeyError if input columns missing."""
    from crypto_trade.features_v1.composed_v1 import compute_rev_vol_gate_signed

    df_no_rev = pd.DataFrame({"vol_state_z_natr_30": [0.1, 0.2]})
    with pytest.raises(KeyError, match="rev_extension_z_3"):
        compute_rev_vol_gate_signed(df_no_rev)

    df_no_vol = pd.DataFrame({"rev_extension_z_3": [0.1, 0.2]})
    with pytest.raises(KeyError, match="vol_state_z_natr_30"):
        compute_rev_vol_gate_signed(df_no_vol)


# ---------------------------------------------------------------------------
# 9. add_composed_v1_085_features: all 4 cols present
# ---------------------------------------------------------------------------


def test_add_composed_v1_085_features_all_4_cols() -> None:
    """add_composed_v1_085_features produces all 4 new UNI-specialist feature columns."""
    from crypto_trade.features_v1.composed_v1 import add_composed_v1_085_features

    df = _make_kline_df(300)
    result = add_composed_v1_085_features(df)
    _expected_feats = (
        "rev_extension_z_3",
        "vol_state_z_natr_30",
        "rev_halflife_50",
        "rev_vol_gate_signed",
    )
    for feat in _expected_feats:
        assert feat in result.columns, f"{feat} missing from add_composed_v1_085_features output"


# ---------------------------------------------------------------------------
# 10. Track isolation
# ---------------------------------------------------------------------------


def test_mean_reversion_v1_no_v2_v3_imports() -> None:
    """mean_reversion_v1.py has no features_v2/v3 import statements (track isolation)."""
    module_path = (
        Path(__file__).parent.parent
        / "src"
        / "crypto_trade"
        / "features_v1"
        / "mean_reversion_v1.py"
    )
    src = module_path.read_text(encoding="utf-8")
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text
    assert "from crypto_trade.features_v3" not in import_text


def test_volatility_v1_no_v2_v3_imports() -> None:
    """volatility_v1.py has no features_v2/v3 import statements (track isolation)."""
    module_path = (
        Path(__file__).parent.parent / "src" / "crypto_trade" / "features_v1" / "volatility_v1.py"
    )
    src = module_path.read_text(encoding="utf-8")
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text
    assert "from crypto_trade.features_v3" not in import_text


def test_composed_v1_no_v2_v3_imports() -> None:
    """composed_v1.py has no features_v2/v3 import statements (track isolation)."""
    module_path = (
        Path(__file__).parent.parent / "src" / "crypto_trade" / "features_v1" / "composed_v1.py"
    )
    src = module_path.read_text(encoding="utf-8")
    import_lines = [
        line for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    import_text = "\n".join(import_lines)
    assert "from crypto_trade.features_v2" not in import_text
    assert "from crypto_trade.features_v3" not in import_text


# ---------------------------------------------------------------------------
# 11. UNIUSDT parquet audit
# ---------------------------------------------------------------------------


def test_uniusdt_parquet_has_all_52_feature_columns() -> None:
    """UNIUSDT parquet contains all 52 V1_ITER085_FEATURE_COLUMNS columns."""
    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "UNIUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"UNIUSDT parquet not found at {parquet_path}")

    from crypto_trade.features_v1 import V1_ITER085_FEATURE_COLUMNS

    df = pd.read_parquet(parquet_path, columns=list(V1_ITER085_FEATURE_COLUMNS))
    missing = [c for c in V1_ITER085_FEATURE_COLUMNS if c not in df.columns]
    assert not missing, (
        f"UNIUSDT parquet is missing {len(missing)} of 52 V1_ITER085_FEATURE_COLUMNS:\n"
        + "\n".join(f"  {c}" for c in missing)
    )
    assert len(df.columns) == 52


def test_uniusdt_parquet_new_features_non_nan() -> None:
    """UNIUSDT parquet: 4 new features have non-NaN values past burn-in."""
    parquet_path = (
        Path(__file__).parent.parent / "data" / "features" / "UNIUSDT_8h_features.parquet"
    )
    if not parquet_path.exists():
        pytest.skip(f"UNIUSDT parquet not found at {parquet_path}")

    _new_cols = [
        "rev_extension_z_3",
        "vol_state_z_natr_30",
        "rev_halflife_50",
        "rev_vol_gate_signed",
    ]
    df = pd.read_parquet(parquet_path, columns=_new_cols)
    for col in df.columns:
        assert df[col].notna().sum() > 100, (
            f"{col}: expected >100 non-NaN rows in UNIUSDT parquet; got {df[col].notna().sum()}"
        )


# ---------------------------------------------------------------------------
# 12. Symbol eligibility
# ---------------------------------------------------------------------------


def test_uni_not_in_v1_excluded_symbols() -> None:
    """UNIUSDT is NOT in V1_EXCLUDED_SYMBOLS."""
    from crypto_trade.features_v1 import V1_EXCLUDED_SYMBOLS

    assert "UNIUSDT" not in V1_EXCLUDED_SYMBOLS


def test_assert_v1_universe_passes_for_uni() -> None:
    """assert_v1_universe(['UNIUSDT']) must pass."""
    from crypto_trade.features_v1 import assert_v1_universe

    assert_v1_universe(["UNIUSDT"])

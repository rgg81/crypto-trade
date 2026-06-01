"""Tests for iter-v1/048: trade_count_zscore_30 feature dispatch.

Axis: ADD ``trade_count_zscore_30`` (rolling-30bar z-score of the ``trades`` kline
field, which is Binance's ``number_of_trades``) to V1_FEATURE_COLUMNS_PRUNED (44 → 45).

Module: src/crypto_trade/features_v1/microstructure_v1.py (NEW)

Test plan (≥6 tests):
  1. test_v1_pruned_has_45_features        — column list + count
  2. test_past_only                         — no-lookahead invariant (core discipline)
  3. test_warmup_nan                        — first 29 bars NaN (min_periods=30)
  4. test_zscore_normalization_approximate  — post-warmup mean ≈ 0, std ≈ 1
  5. test_trades_column_read               — module reads ``trades`` (not a wrong alias)
  6. test_track_isolation                   — no v2/v3 imports in module
  7. test_microstructure_v1_in_registry     — group registered in GROUP_REGISTRY (14 groups)
  8. test_parquet_integration               — trade_count_zscore_30 present in v1 parquet
     (skipped if parquets not yet regenerated)
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, microstructure_v1
from crypto_trade.features_v1.microstructure_v1 import compute_trade_count_zscore_30

# ---------------------------------------------------------------------------
# 1. Column list — confirm 44 → 45 extension
# ---------------------------------------------------------------------------


def test_v1_pruned_has_45_features():
    """V1_FEATURE_COLUMNS_PRUNED must have exactly 45 features and include the new one."""
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
        f"Expected 45 pruned features, got {len(V1_FEATURE_COLUMNS_PRUNED)}"
    )
    assert "trade_count_zscore_30" in V1_FEATURE_COLUMNS_PRUNED, (
        "trade_count_zscore_30 must be in V1_FEATURE_COLUMNS_PRUNED"
    )


# ---------------------------------------------------------------------------
# 2. No-lookahead invariant (core discipline check)
# ---------------------------------------------------------------------------


def test_past_only():
    """trade_count_zscore_30[t] does not use trades[t+k] for any k > 0.

    Perturbing only the FINAL bar of the ``trades`` series must NOT change any
    earlier bar of ``trade_count_zscore_30``.
    """
    rng = np.random.default_rng(42)
    base = rng.integers(10_000, 100_000, size=300).astype(float)

    df1 = pd.DataFrame({"trades": base.copy()})
    df1 = compute_trade_count_zscore_30(df1)

    df2 = pd.DataFrame({"trades": base.copy()})
    df2.loc[df2.index[-1], "trades"] = base[-1] * 100  # perturb FINAL bar only
    df2 = compute_trade_count_zscore_30(df2)

    pd.testing.assert_series_equal(
        df1["trade_count_zscore_30"].iloc[:-1],
        df2["trade_count_zscore_30"].iloc[:-1],
        check_names=False,
    )


# ---------------------------------------------------------------------------
# 3. Warmup NaN (min_periods=30)
# ---------------------------------------------------------------------------


def test_warmup_nan():
    """First 29 bars (indices 0-28) are NaN; bar 30 onward has values (min_periods=30)."""
    rng = np.random.default_rng(42)
    base = rng.integers(10_000, 100_000, size=200).astype(float)
    df = compute_trade_count_zscore_30(pd.DataFrame({"trades": base}))

    assert df["trade_count_zscore_30"].iloc[:29].isna().all(), (
        "First 29 bars must be NaN (window=30, min_periods=30)"
    )
    assert df["trade_count_zscore_30"].iloc[30:].notna().any(), (
        "At least one bar beyond index 30 must be non-NaN"
    )


# ---------------------------------------------------------------------------
# 4. Z-score normalization quality (approximate)
# ---------------------------------------------------------------------------


def test_zscore_normalization_approximate():
    """Post-warmup mean ≈ 0 and std ≈ 1 across a long i.i.d. series."""
    rng = np.random.default_rng(42)
    base = rng.integers(10_000, 100_000, size=5_000).astype(float)
    df = compute_trade_count_zscore_30(pd.DataFrame({"trades": base}))
    post = df["trade_count_zscore_30"].iloc[30:].dropna()

    assert abs(post.mean()) < 0.2, f"Mean drift too large: {post.mean():.4f}"
    assert 0.7 < post.std() < 1.5, f"Std drift out of range: {post.std():.4f}"


# ---------------------------------------------------------------------------
# 5. Correct kline column name — ``trades`` (not number_of_trades alias)
# ---------------------------------------------------------------------------


def test_trades_column_read():
    """Module reads the ``trades`` kline column (Binance field 8 = number_of_trades).

    Verifies the source references ``"trades"`` (the actual kline DataFrame column
    name from models.Kline.trades / kline_array).  The Binance documentation calls
    this ``number_of_trades``; the codebase exposes it as ``trades``.
    """
    src = inspect.getsource(microstructure_v1)
    # The module must reference the actual DataFrame column name "trades"
    assert '"trades"' in src or "'trades'" in src, (
        'microstructure_v1 must reference the "trades" kline column'
    )
    # Verify no runtime df["number_of_trades"] key access (would KeyError).
    # The string "number_of_trades" may appear in docstrings/comments — that is fine.
    # We check that compute_trade_count_zscore_30 function body (excluding docstring)
    # uses "trades", not "number_of_trades", as the DataFrame key.
    import ast  # noqa: PLC0415

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "compute_trade_count_zscore_30":
            # Skip the docstring (first statement if it is an Expr/Constant)
            body_stmts = node.body
            if (
                body_stmts
                and isinstance(body_stmts[0], ast.Expr)
                and isinstance(body_stmts[0].value, ast.Constant)
            ):
                body_stmts = body_stmts[1:]
            body_src = "\n".join(ast.unparse(s) for s in body_stmts)
            assert "number_of_trades" not in body_src, (
                "compute_trade_count_zscore_30 must not access df['number_of_trades']; "
                "use df['trades'] (actual kline column name)"
            )
            assert "trades" in body_src, "compute_trade_count_zscore_30 must access df['trades']"
            break


# ---------------------------------------------------------------------------
# 6. Track isolation — no v2/v3 imports
# ---------------------------------------------------------------------------


def test_track_isolation():
    """microstructure_v1 must not import from features_v2 or features_v3.

    Checks actual import statements via AST, not docstring mentions.
    """
    import ast  # noqa: PLC0415

    src = inspect.getsource(microstructure_v1)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "features_v2" not in alias.name, (
                    f"microstructure_v1 imports from features_v2: {alias.name}"
                )
                assert "features_v3" not in alias.name, (
                    f"microstructure_v1 imports from features_v3: {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "features_v2" not in module, (
                f"microstructure_v1 imports from features_v2: {module}"
            )
            assert "features_v3" not in module, (
                f"microstructure_v1 imports from features_v3: {module}"
            )


# ---------------------------------------------------------------------------
# 7. Registry — microstructure_v1 registered, GROUP_REGISTRY now has 14 groups
# ---------------------------------------------------------------------------


def test_microstructure_v1_in_registry():
    """microstructure_v1 must be registered in GROUP_REGISTRY (14 groups post-/048)."""
    from crypto_trade.features import GROUP_REGISTRY  # noqa: PLC0415

    assert "microstructure_v1" in GROUP_REGISTRY, (
        "microstructure_v1 must be registered in GROUP_REGISTRY"
    )
    assert len(GROUP_REGISTRY) == 14, (
        f"GROUP_REGISTRY must have exactly 14 groups post-/048, got {len(GROUP_REGISTRY)}"
    )


# ---------------------------------------------------------------------------
# 8. Parquet integration — trade_count_zscore_30 present after feature regen
# ---------------------------------------------------------------------------

_V1_PARQUET_DIR = Path("data/features")
_SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]


def _column_in_parquets() -> bool:
    """Return True if trade_count_zscore_30 column is present in any v1 parquet."""
    for sym in _SYMBOLS:
        path = _V1_PARQUET_DIR / f"{sym}_8h_features.parquet"
        if not path.exists():
            continue
        try:
            cols = pd.read_parquet(path, columns=[]).columns.tolist()
        except Exception:
            continue
        if "trade_count_zscore_30" in cols:
            return True
    return False


_COLUMN_REGENERATED = _column_in_parquets()


@pytest.mark.skipif(
    not _COLUMN_REGENERATED,
    reason=(
        "trade_count_zscore_30 not yet in v1 parquets — run: "
        "uv run crypto-trade features --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
        "--interval 8h --track v1 --format parquet --workers 4"
    ),
)
def test_parquet_integration():
    """trade_count_zscore_30 must be present in at least one v1 symbol parquet."""
    found_col = False
    for sym in _SYMBOLS:
        path = _V1_PARQUET_DIR / f"{sym}_8h_features.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=None)
        if "trade_count_zscore_30" in df.columns:
            found_col = True
            # Spot-check: post-warmup rows should not be all NaN
            post = df["trade_count_zscore_30"].iloc[30:]
            assert post.notna().any(), (
                f"{sym}: trade_count_zscore_30 post-warmup is all NaN — "
                "check feature pipeline wiring"
            )
            break
    assert found_col, (
        "trade_count_zscore_30 not found in any v1 parquet. "
        "Re-run: uv run crypto-trade features "
        "--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT "
        "--interval 8h --track v1 --format parquet --workers 4"
    )

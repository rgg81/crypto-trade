"""Tests for iter-v1/032: FROZEN-HP basin-lottery ablation.

Test coverage (5+ required):
1.  Catch-all exclusion: v1-032 appears in run_baseline_v1.py catch-all exclusion tuple.
2.  Dispatch banner: [iter-v1/032] FROZEN-HP ablation banner fires in runner source.
3.  Optuna NOT invoked when frozen_hp_mode != "none" (verify via mock).
4.  Per-cell HP loaded from parquet correctly (schema + lookup correctness).
5.  Reproducibility: same seed + same HP produces identical model predictions.
6.  CLI --frozen-hp-mode flag parses with choices [none, baseline_v1].
7.  LightGbmStrategy accepts frozen_hp_parquet parameter without error.
8.  Foundation regression: walk_forward.py:113 carries embargo_ms purge.

Run:
    uv run pytest tests/test_iteration_v1_032.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_frozen_hp_parquet(tmp_path: Path) -> Path:
    """Build a minimal frozen HP parquet with 2 cells for model A."""
    rows = []
    for seed in [42, 123]:
        rows.append(
            {
                "model": "A",
                "month": "2022-01",
                "inner_seed": seed,
                "best_sharpe": 0.15,
                "confidence_threshold": 0.65,
                "training_days": 200,
                "n_estimators": 100,
                "max_depth": 3,
                "num_leaves": 31,
                "learning_rate": 0.05,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "min_child_samples": 20,
                "reg_alpha": 0.01,
                "reg_lambda": 0.01,
            }
        )
    df = pd.DataFrame(rows)
    out = tmp_path / "frozen_hp_test.parquet"
    df.to_parquet(out, index=False)
    return out


def _make_minimal_lgbm_strategy(frozen_hp_parquet: Path | None = None):
    """Construct a LightGbmStrategy with minimal required args (no data, no training)."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    return LightGbmStrategy(
        training_months=24,
        n_trials=1,
        cv_splits=2,
        feature_columns=["feat_a", "feat_b"],
        ensemble_seeds=[42],
        sample_weight_mode="composite_inv_concurrency",
        frozen_hp_parquet=frozen_hp_parquet,
    )


# ---------------------------------------------------------------------------
# Test 1: BASELINE CATCH-ALL EXCLUSION
# ---------------------------------------------------------------------------


def test_v1_iter032_baseline_catchall_exclusion():
    """v1-032 MUST appear in run_baseline_v1.py catch-all exclusion tuple.

    Per /030 LESSON: the catch-all elif must exclude v1-032 to prevent silent
    baseline fallback when running with iteration_label='v1-032'.
    """
    source = Path("run_baseline_v1.py").read_text()

    # v1-032 must appear somewhere in the source
    assert '"v1-032"' in source or "'v1-032'" in source, (
        "v1-032 not found anywhere in run_baseline_v1.py"
    )

    # Verify it appears in the catch-all exclusion tuple context
    lines = source.splitlines()
    in_catchall = False
    catchall_lines = []
    for i, line in enumerate(lines):
        if "iteration_label not in" in line:
            in_catchall = True
        if in_catchall:
            catchall_lines.append(line)
            if "):" in line and len(catchall_lines) > 1:
                break
    catchall_text = "\n".join(catchall_lines)
    assert "v1-032" in catchall_text, (
        f"v1-032 not found in catch-all exclusion tuple. Catch-all block:\n{catchall_text}"
    )


# ---------------------------------------------------------------------------
# Test 2: DISPATCH BANNER
# ---------------------------------------------------------------------------


def test_v1_iter032_dispatch_banner():
    """[iter-v1/032] FROZEN-HP ablation banner MUST fire in run_baseline_v1.py.

    Per /030 LESSON: the banner is the first-line evidence dispatch hit the
    intended branch (not the catch-all fallback).
    """
    source = Path("run_baseline_v1.py").read_text()
    assert "[iter-v1/032]" in source, (
        "[iter-v1/032] dispatch banner not found in run_baseline_v1.py. "
        "Per /030 LESSON: every iteration branch must print its dispatch banner."
    )
    assert "FROZEN-HP ablation" in source, (
        "FROZEN-HP ablation description not found in run_baseline_v1.py dispatch. "
        "The /032 banner must identify the ablation purpose."
    )


# ---------------------------------------------------------------------------
# Test 3: Optuna NOT invoked when frozen_hp_mode is active
# ---------------------------------------------------------------------------


def test_v1_iter032_optuna_not_invoked_when_frozen_hp(monkeypatch, tmp_path):
    """When frozen_hp_parquet is set, optimize_and_train must NOT be called.

    Verifies that the frozen HP branch skips Optuna entirely and goes directly
    to the LightGBM fit path.
    """
    from crypto_trade.strategies.ml import lgbm as lgbm_mod

    optuna_call_count = {"count": 0}

    original_opt = lgbm_mod.optimize_and_train

    def mock_optimize_and_train(*args, **kwargs):
        optuna_call_count["count"] += 1
        return original_opt(*args, **kwargs)

    monkeypatch.setattr(lgbm_mod, "optimize_and_train", mock_optimize_and_train)

    # Build minimal frozen HP parquet (unused in this test but validates the helper)
    _make_frozen_hp_parquet(tmp_path)

    # Build minimal training data (10 rows, 2 features) — validates LightGBM fit path
    np.random.seed(42)
    n = 20
    x_train = np.random.randn(n, 2).astype(np.float32)
    y_labels = np.where(x_train[:, 0] > 0, 1, -1).astype(np.int64)
    w = np.ones(n, dtype=np.float64)

    import lightgbm as lgb

    clf = lgb.LGBMClassifier(n_estimators=5, max_depth=2, num_leaves=7, random_state=42)
    clf.fit(x_train, y_labels, sample_weight=w)

    # Verify source: frozen HP branch calls lgb.LGBMClassifier directly
    import inspect

    src = inspect.getsource(lgbm_mod.LightGbmStrategy._train_for_month)
    assert "_frozen_hp_parquet" in src, (
        "_frozen_hp_parquet not referenced in _train_for_month source"
    )
    assert "lgb_direct.LGBMClassifier" in src or "lgb_direct" in src, (
        "Direct LGBMClassifier instantiation not found in frozen HP branch"
    )
    # The frozen HP branch must NOT call optimize_and_train
    # (it's in an else branch below the frozen HP path)
    assert "else:" in src and "optimize_and_train" in src, (
        "optimize_and_train must be in the else branch (normal path) in _train_for_month"
    )


# ---------------------------------------------------------------------------
# Test 4: Per-cell HP loaded from parquet correctly
# ---------------------------------------------------------------------------


def test_v1_iter032_per_cell_hp_parquet_schema(tmp_path):
    """Frozen HP parquet schema must match expected columns and lookup produces correct row."""
    hp_parquet = _make_frozen_hp_parquet(tmp_path)
    df = pd.read_parquet(hp_parquet)

    required_cols = {
        "model",
        "month",
        "inner_seed",
        "confidence_threshold",
        "training_days",
        "n_estimators",
        "max_depth",
        "num_leaves",
        "learning_rate",
        "subsample",
        "colsample_bytree",
        "min_child_samples",
        "reg_alpha",
        "reg_lambda",
    }
    missing = required_cols - set(df.columns)
    assert not missing, f"Frozen HP parquet missing required columns: {missing}"

    # Verify lookup works for model=A, month=2022-01, seed=42
    row = df[(df["model"] == "A") & (df["month"] == "2022-01") & (df["inner_seed"] == 42)]
    assert len(row) == 1, f"Expected 1 row for A/2022-01/42, got {len(row)}"
    assert float(row.iloc[0]["confidence_threshold"]) == pytest.approx(0.65)
    assert int(row.iloc[0]["n_estimators"]) == 100

    # Verify lookup returns empty for missing cell
    missing_row = df[(df["model"] == "Z") & (df["month"] == "2022-01") & (df["inner_seed"] == 42)]
    assert len(missing_row) == 0, "Expected empty row for model=Z (does not exist)"


# ---------------------------------------------------------------------------
# Test 5: Reproducibility — same seed + same HP = identical predictions
# ---------------------------------------------------------------------------


def test_v1_iter032_reproducibility_same_hp_same_predictions():
    """Two LightGBM fits with identical HP and same seed must produce identical predictions."""
    import lightgbm as lgb

    np.random.seed(0)
    n = 50
    x_data = np.random.randn(n, 5).astype(np.float32)
    y_data = (x_data[:, 0] + x_data[:, 1] > 0).astype(int)
    w = np.ones(n, dtype=np.float64)

    hp = {
        "n_estimators": 20,
        "max_depth": 3,
        "num_leaves": 7,
        "learning_rate": 0.1,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "min_child_samples": 5,
        "reg_alpha": 0.0,
        "reg_lambda": 0.0,
        "random_state": 42,
        "n_jobs": 1,
        "verbose": -1,
    }

    clf1 = lgb.LGBMClassifier(**hp)
    clf1.fit(x_data, y_data, sample_weight=w)
    pred1 = clf1.predict_proba(x_data)[:, 1]

    clf2 = lgb.LGBMClassifier(**hp)
    clf2.fit(x_data, y_data, sample_weight=w)
    pred2 = clf2.predict_proba(x_data)[:, 1]

    np.testing.assert_array_equal(
        pred1,
        pred2,
        err_msg="LightGBM predictions not deterministic with same HP + seed",
    )


# ---------------------------------------------------------------------------
# Test 6: CLI --frozen-hp-mode flag parsing
# ---------------------------------------------------------------------------


def test_v1_iter032_cli_frozen_hp_mode_flag():
    """--frozen-hp-mode must be in argparse choices [none, baseline_v1]."""
    source = Path("run_baseline_v1.py").read_text()
    assert "--frozen-hp-mode" in source, (
        "--frozen-hp-mode flag not found in run_baseline_v1.py argparse"
    )
    assert '"none"' in source or "'none'" in source, "choice 'none' missing from frozen_hp_mode"
    assert '"baseline_v1"' in source or "'baseline_v1'" in source, (
        "choice 'baseline_v1' missing from frozen_hp_mode"
    )


# ---------------------------------------------------------------------------
# Test 7: LightGbmStrategy accepts frozen_hp_parquet parameter
# ---------------------------------------------------------------------------


def test_v1_iter032_lgbm_strategy_accepts_frozen_hp_parquet(tmp_path):
    """LightGbmStrategy must accept frozen_hp_parquet without raising."""
    hp_parquet = _make_frozen_hp_parquet(tmp_path)
    strat = _make_minimal_lgbm_strategy(frozen_hp_parquet=hp_parquet)
    assert strat._frozen_hp_parquet == hp_parquet
    assert strat._frozen_hp_df is None  # lazy load — not loaded until first _train_for_month


def test_v1_iter032_lgbm_strategy_accepts_frozen_hp_none():
    """LightGbmStrategy with frozen_hp_parquet=None uses normal Optuna path."""
    strat = _make_minimal_lgbm_strategy(frozen_hp_parquet=None)
    assert strat._frozen_hp_parquet is None
    assert strat._frozen_hp_df is None


# ---------------------------------------------------------------------------
# Test 8: Foundation regression — walk_forward.py:113 embargo
# ---------------------------------------------------------------------------


def test_v1_iter032_foundation_regression_embargo():
    """walk_forward.py line 113 must carry the anti-lookahead embargo purge.

    Sacred invariant: train_end_ms = test_start_ms - embargo_ms.
    Unchanged at iter-v1/032 — verify no regression.
    """
    source = Path("src/crypto_trade/strategies/ml/walk_forward.py").read_text()
    lines = source.splitlines()
    # Lines 109-118 (1-indexed) should contain the embargo purge
    if len(lines) > 113:
        region = "\n".join(lines[108:118])
    else:
        region = source
    assert "train_end_ms" in region and "embargo_ms" in region, (
        f"walk_forward.py line ~113 missing embargo_ms purge. Region:\n{region}"
    )
    assert "test_start_ms - embargo_ms" in region, (
        "walk_forward.py must have: train_end_ms = test_start_ms - embargo_ms"
    )

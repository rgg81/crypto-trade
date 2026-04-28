"""Test if LightGBM is deterministic given fixed random_state.

Trains the same small LGBM model twice with identical inputs and compares.
"""

from __future__ import annotations

import numpy as np

import lightgbm as lgb


def main() -> None:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(2000, 50))
    y = rng.integers(0, 2, size=2000)

    params = {
        "n_estimators": 200,
        "max_depth": 4,
        "num_leaves": 64,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.7,
        "min_child_samples": 20,
        "reg_alpha": 0.001,
        "reg_lambda": 0.01,
        "random_state": 42,
        "verbosity": -1,
        "objective": "binary",
        "is_unbalance": True,
    }

    # Run 1
    m1 = lgb.LGBMClassifier(**params)
    m1.fit(X, y)
    p1 = m1.predict_proba(X)

    # Run 2 (same inputs, same seed)
    m2 = lgb.LGBMClassifier(**params)
    m2.fit(X, y)
    p2 = m2.predict_proba(X)

    diff = np.abs(p1 - p2)
    print(f"Max abs diff in predictions: {diff.max()}")
    print(f"Mean abs diff in predictions: {diff.mean()}")
    print(f"Predictions identical: {(diff == 0).all()}")

    # Now with deterministic=True
    params_det = {**params, "deterministic": True, "force_col_wise": True, "num_threads": 1}
    m3 = lgb.LGBMClassifier(**params_det)
    m3.fit(X, y)
    p3 = m3.predict_proba(X)

    m4 = lgb.LGBMClassifier(**params_det)
    m4.fit(X, y)
    p4 = m4.predict_proba(X)

    diff_det = np.abs(p3 - p4)
    print(f"\nWith deterministic=True + force_col_wise + num_threads=1:")
    print(f"Max abs diff: {diff_det.max()}")
    print(f"Identical: {(diff_det == 0).all()}")


if __name__ == "__main__":
    main()

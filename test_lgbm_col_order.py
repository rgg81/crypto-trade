"""Test if column ORDER affects LightGBM output.

Same seed, same data, same hyperparams — just reorder columns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import lightgbm as lgb


def main() -> None:
    rng = np.random.default_rng(42)
    n_rows, n_cols = 3000, 50
    X = rng.normal(size=(n_rows, n_cols))
    y = rng.integers(0, 2, size=n_rows)
    cols = [f"f{i:02d}" for i in range(n_cols)]

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

    # Baseline order
    df1 = pd.DataFrame(X, columns=cols)
    m1 = lgb.LGBMClassifier(**params)
    m1.fit(df1, y)
    p1 = m1.predict_proba(df1)

    # Shuffled order (same data, just reordered columns)
    rng2 = np.random.default_rng(7)
    perm = list(range(n_cols))
    rng2.shuffle(perm)
    cols_shuf = [cols[i] for i in perm]
    df2 = df1[cols_shuf].copy()
    m2 = lgb.LGBMClassifier(**params)
    m2.fit(df2, y)
    p2 = m2.predict_proba(df2)

    # Compare predictions (same rows)
    diff = np.abs(p1 - p2)
    print(f"Column order shuffle test:")
    print(f"  Max abs diff: {diff.max():.6f}")
    print(f"  Mean abs diff: {diff.mean():.6f}")
    print(f"  Predictions identical: {(diff == 0).all()}")
    # Binary classification at 0.5 threshold
    pred1 = (p1[:, 1] > 0.5).astype(int)
    pred2 = (p2[:, 1] > 0.5).astype(int)
    print(f"  Label agreement: {(pred1 == pred2).mean() * 100:.2f}%")
    print(f"  Rows where labels differ: {(pred1 != pred2).sum()}/{n_rows}")


if __name__ == "__main__":
    main()

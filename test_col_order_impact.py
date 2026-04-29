"""Test if column order changes predictions on one walk-forward training.

Uses the actual LightGbmStrategy training pipeline with real BTC+ETH data
for one month, comparing predictions between schema-order and alphabetical
column ordering.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# Baseline features (alphabetical)
from run_v1_baseline_core import BASELINE_FEATURE_COLUMNS

from crypto_trade.backtest import _build_master
from crypto_trade.backtest_models import BacktestConfig
from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

SYMBOLS = ("BTCUSDT", "ETHUSDT")
META = {
    "open_time", "open", "high", "low", "close", "close_time",
    "volume", "quote_volume", "trades", "taker_buy_volume",
    "taker_buy_quote_volume", "symbol",
}


def schema_order_features() -> list[str]:
    schema = pq.read_schema("data/features/BTCUSDT_8h_features.parquet")
    return [
        n for n in schema.names
        if n not in META and not n.startswith("ent_") and not n.startswith("cusum_")
    ]


def train_once(feature_columns: list[str], tag: str, master: pd.DataFrame) -> dict:
    """Train on one walk-forward split and predict the test month."""
    strat = LightGbmStrategy(
        training_months=24,
        n_trials=10,  # small for speed
        cv_splits=5,
        label_tp_pct=8.0,
        label_sl_pct=4.0,
        label_timeout_minutes=10080,
        fee_pct=0.1,
        features_dir="data/features",
        seed=42,
        verbose=0,
        atr_tp_multiplier=2.9,
        atr_sl_multiplier=1.45,
        use_atr_labeling=True,
        ensemble_seeds=[42],  # single seed for speed
        feature_columns=feature_columns,
    )
    strat.compute_features(master)
    # Train on split with test month = 2025-06 (mid-OOS, real data)
    target = "2025-06"
    if target not in strat._split_map:
        targets = list(strat._split_map.keys())
        print(f"Available splits: {targets[:5]} ... {targets[-5:]}")
        return {}
    split = strat._split_map[target]
    strat._train_for_month(target)
    # Get predictions on test month
    test_mask = (master["open_time"] >= split.test_start_ms) & (
        master["open_time"] < split.test_end_ms
    )
    test_rows = master[test_mask].reset_index(drop=True)
    if test_rows.empty:
        return {}

    # Load features for test rows
    from crypto_trade.feature_store import lookup_features
    lookups = list(zip(test_rows["symbol"].tolist(), test_rows["open_time"].tolist(), strict=False))
    feat_df = lookup_features(
        lookups=lookups,
        features_dir="data/features",
        interval="8h",
        columns=feature_columns,
    )
    available = [c for c in feature_columns if c in feat_df.columns]
    X = feat_df[available].to_numpy()
    probas = [m.predict_proba(X) for m in strat._models]
    mean_proba = np.mean([p[:, 1] for p in probas], axis=0)
    pred = (mean_proba > 0.5).astype(int)

    return {
        "tag": tag,
        "n_rows": len(test_rows),
        "mean_proba": mean_proba,
        "pred": pred,
    }


def main() -> None:
    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h",
        data_dir=Path("data"),
        max_amount_usd=1000.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        fee_pct=0.1,
    )
    master = _build_master(config)
    schema_order = schema_order_features()
    alpha_order = list(BASELINE_FEATURE_COLUMNS)

    print(f"Schema-order feature count: {len(schema_order)}")
    print(f"Alpha-order feature count: {len(alpha_order)}")
    print(f"Same set: {set(schema_order) == set(alpha_order)}")
    print(f"Positions differ: {sum(1 for a, b in zip(schema_order, alpha_order, strict=False) if a != b)}/193")
    print()

    print("=== Training with SCHEMA order ===")
    r1 = train_once(schema_order, "schema", master)
    print(f"  predicted {r1['n_rows']} test rows")

    print("\n=== Training with ALPHABETICAL order ===")
    r2 = train_once(alpha_order, "alpha", master)
    print(f"  predicted {r2['n_rows']} test rows")

    # Compare
    print("\n=== Comparison ===")
    diff = np.abs(r1["mean_proba"] - r2["mean_proba"])
    print(f"Max |Δ proba|: {diff.max():.6f}")
    print(f"Mean |Δ proba|: {diff.mean():.6f}")
    flip = (r1["pred"] != r2["pred"]).sum()
    print(f"Label flips: {flip}/{len(r1['pred'])} ({100 * flip / len(r1['pred']):.1f}%)")

    # For 0.75 threshold (baseline uses ~0.7-0.85)
    for th in [0.60, 0.70, 0.75, 0.80, 0.85]:
        sig1 = r1["mean_proba"] > th
        sig2 = r2["mean_proba"] > th
        diff_sig = (sig1 != sig2).sum()
        print(f"At threshold {th}: {diff_sig}/{len(sig1)} trades triggered differently")


if __name__ == "__main__":
    main()

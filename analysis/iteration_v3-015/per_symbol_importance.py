"""
iter-v3/015 — Per-symbol feature importance for tbr_zscore_30 disambiguation.

Background (Critic Round 1 Clarification 2):
    The published reports/iteration_v3-015/{in,out}_sample/feature_importance.csv
    is NOT actually aggregated across all 3 symbol models or all walk-forward
    months as the engineering report claimed.  Inspecting `_write_feature_importance`
    at run_baseline_v3.py:1110-1151 reveals the function reads
    `primary_model_pairs[0]` only -- which is BCH (the first entry of V3_MODELS).
    Furthermore `inner._models` is reset at each `_train_for_month` call, so
    the published CSV reflects BCH's final-month inner ensemble only (size=1
    in --exploration mode).

Critic Round 1 Clarification 2 wants per-symbol importance to determine
whether `tbr_zscore_30` is bottom-quartile across **all 3** symbols (which
would tighten Falsifier 4 brief §4.3 verbatim "across all 3 symbols") or
whether at least one symbol's model gives the feature meaningful importance
(in which case the picture shifts).

This script provides a coarse but informative answer: a single one-shot
LightGBM fit per symbol on the FULL IS window using triple-barrier-equivalent
forward-return-sign labels and the same 14 V3_FEATURE_COLUMNS.  It is
NOT a per-month walk-forward replication of the production runner -- it
is a fast directional signal for "does the model find tbr_zscore_30 useful
on this symbol's IS data, given it has access to all 14 features?"

Method:
    For each symbol in (BCH, LDO, TRX):
      1. Load <symbol>_8h_features.parquet
      2. Filter to IS window (open_time < OOS_CUTOFF_MS)
      3. Drop rows with NaN in any of the 14 V3_FEATURE_COLUMNS
      4. Compute label = sign of forward 21-bar (1-week) return -- a coarse
         proxy for the production triple-barrier label.  Direction-only
         (no fees) is fine for importance ranking.
      5. Fit a default-config LightGBM classifier (no Optuna, no CV)
      6. Record feature_importances_ (split-count) and rank tbr_zscore_30
         within the 14-column space.

Output:
    analysis/iteration_v3-015/per_symbol_importance.csv -- columns:
        symbol, feature, importance, rank, total_features

Caveats (stated up front):
    - This is a one-shot fit, NOT walk-forward.  The production runner
      retrains each month with Optuna-tuned hyperparams.  Per-month rank
      may oscillate.
    - Forward-return-sign labels are not the production triple-barrier
      labels; they are a coarse proxy.  If tbr_zscore_30 has e.g. nonlinear
      regime-classifier value at SL/TP boundaries specifically, a sign-of-
      return label would understate its importance.
    - Default LightGBM hyperparams (no Optuna).  The production runner uses
      Optuna-tuned learning_rate, num_leaves, max_depth, min_child_samples,
      reg_alpha, reg_lambda, colsample_bytree.

Despite these caveats, the relative rank of tbr_zscore_30 across the three
symbols is informative for Falsifier 4 disambiguation: if rank is bottom-
quartile in all 3 symbols, Critic's NEGATIVE-no-effect call is reinforced;
if any symbol shows tbr_zscore_30 in the top half, the picture shifts.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# Match the production paths
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS  # noqa: E402

FEATURES_DIR = Path("data/features_v3")
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
OUT_CSV = Path("analysis/iteration_v3-015/per_symbol_importance.csv")

FORWARD_BARS = 21  # 1 week at 8h cadence -- approximate triple-barrier timeout

assert len(V3_FEATURE_COLUMNS) == 14, f"Expected 14 features; got {len(V3_FEATURE_COLUMNS)}"
assert "tbr_zscore_30" in V3_FEATURE_COLUMNS, "tbr_zscore_30 not in V3_FEATURE_COLUMNS"


def load_is_features(symbol: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    needed = ["open_time", "close", *V3_FEATURE_COLUMNS]
    df = pq.read_table(path, columns=needed).to_pandas()
    df = df.sort_values("open_time").reset_index(drop=True)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    return df


def fit_one_symbol(symbol: str) -> list[dict]:
    import lightgbm as lgb  # local import to avoid bringing into top-level toolchain

    df = load_is_features(symbol)
    print(f"[{symbol}] IS rows raw: {len(df)}")

    fwd_ret = df["close"].shift(-FORWARD_BARS) / df["close"] - 1.0
    df = df.assign(fwd_ret=fwd_ret).dropna(subset=["fwd_ret"]).copy()
    df = df.dropna(subset=list(V3_FEATURE_COLUMNS)).copy()
    print(f"[{symbol}] IS rows after dropna: {len(df)}")

    X = df[list(V3_FEATURE_COLUMNS)].values
    y = (df["fwd_ret"] > 0).astype(int).values
    print(f"[{symbol}] long share: {y.mean():.3f} on n={len(y)}")

    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        min_child_samples=20,
        random_state=42,
        verbose=-1,
    )
    model.fit(X, y)

    importances = model.feature_importances_
    pairs = list(zip(V3_FEATURE_COLUMNS, importances, strict=True))
    pairs.sort(key=lambda p: p[1], reverse=True)
    n = len(pairs)
    rows = []
    for rank, (feature, imp) in enumerate(pairs, start=1):
        rows.append(
            {
                "symbol": symbol,
                "feature": feature,
                "importance": int(imp),
                "rank": rank,
                "total_features": n,
            }
        )
    tbr_row = next(r for r in rows if r["feature"] == "tbr_zscore_30")
    print(
        f"[{symbol}] tbr_zscore_30 rank={tbr_row['rank']}/{n} "
        f"importance={tbr_row['importance']}"
    )
    return rows


def main() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    for symbol in SYMBOLS:
        all_rows.extend(fit_one_symbol(symbol))

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["symbol", "feature", "importance", "rank", "total_features"]
        )
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote {OUT_CSV}")

    # Summary table for the QR response
    print("\n=== Summary: tbr_zscore_30 rank per symbol ===")
    for symbol in SYMBOLS:
        rows = [r for r in all_rows if r["symbol"] == symbol]
        tbr = next(r for r in rows if r["feature"] == "tbr_zscore_30")
        bottom_quartile_threshold = int(np.ceil(tbr["total_features"] * 0.75)) + 1
        is_bottom_q = tbr["rank"] >= bottom_quartile_threshold
        print(
            f"  {symbol:>8s}: rank {tbr['rank']:>2d}/{tbr['total_features']} "
            f"importance {tbr['importance']:>4d}  "
            f"bottom_quartile={'YES' if is_bottom_q else 'NO '} "
            f"(threshold rank>={bottom_quartile_threshold})"
        )


if __name__ == "__main__":
    main()

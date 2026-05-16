"""iter-v3/085 — Cycle-3 EXPLORATION #4 EDA, PART 2: can a symbol-identity
feature rescue the pooled model? (the panel-ML standard fix; IS-only).

PART 1 (`pooled_model_cross_symbol_structure.py`) found a NAIVE pool fails: only
7/14 features sign-agree across symbols and the leave-one-symbol-out transfer lift is
NEGATIVE (-0.0188). A naive pool would average BCH's edge against TRX's opposite-signed
feature relationships.

But the standard panel-ML response (Gu/Kelly/Xiu "Empirical Asset Pricing via ML",
NBER w25398; the v1 Model A precedent) is NOT a naive pool — it is a pool WITH an asset-
identity input, so the tree can split on symbol and learn symbol-conditional rules
while still sharing statistical strength across the cross-section. PART 2 tests whether
that fix recovers the structure a naive pool loses.

The test (all IS data — no OOS, no model-design parameter chosen on OOS):
  T1. POOLED + symbol dummy — train ONE LightGBM on all 3 symbols with 14 features
      + a categorical `symbol_id`; evaluate per-symbol on a chronological 70/30 split.
  T2. PER-SYMBOL baseline — the v3 incumbent: 3 separate LightGBMs, each 14 features,
      same chronological 70/30 split.
  T3. POOLED, NO dummy — the naive pool, same 70/30 split (PART-1's leave-one-out
      used a different protocol; T3 re-tests under the SAME split as T1/T2 for a
      clean 3-way comparison).
  Compare per-symbol test accuracy + the symbol_id feature-importance share (if the
  tree never splits on symbol_id, the dummy is inert and the pool reduces to T3).

NO CHEATING:
  - IS data only (open_time < OOS_CUTOFF_DATE 2025-03-24). OOS never loaded.
  - `OOS_CUTOFF_DATE` / `training_months` not read, not modified.
  - The 70/30 split is chronological and WITHIN the IS window — it is an EDA
    generalisation probe, NOT the production walk-forward; no design parameter of
    iter-v3/085 is selected from it on OOS data.

Run:
  export PATH="$HOME/.local/bin:$PATH"
  uv run python analysis/iteration_v3-085/pooled_with_symbol_dummy.py
"""

from __future__ import annotations

import csv
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.strategies.ml.labeling import label_trades

warnings.filterwarnings("ignore")

OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000)
TIMEOUT_MINUTES = 10080
ATR_TP, ATR_SL = 2.0, 1.0
FEE_PCT = 0.1

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA_DIR = Path("data")
FEATURES_DIR = Path("data/features_v3")
OUT_DIR = Path("analysis/iteration_v3-085")

V3_FEATURES = [
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
]

LGB_PARAMS = dict(
    objective="binary", num_leaves=15, max_depth=4, learning_rate=0.05,
    n_estimators=120, min_child_samples=40, subsample=0.8,
    colsample_bytree=0.8, verbose=-1, seed=42,
)


def _load_is(symbol: str) -> pd.DataFrame:
    ohlcv = pd.read_csv(DATA_DIR / symbol / "8h.csv")
    ohlcv = ohlcv[["open_time", "open", "high", "low", "close", "close_time"]].copy()
    ohlcv["symbol"] = symbol
    feats = pq.read_table(
        FEATURES_DIR / f"{symbol}_8h_features.parquet",
        columns=["open_time", "natr_21_raw", *V3_FEATURES],
    ).to_pandas()
    merged = ohlcv.merge(feats, on="open_time", how="inner")
    return merged[merged["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)


def _label(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    close = df["close"].to_numpy(dtype=float)
    natr = df["natr_21_raw"].to_numpy(dtype=float)
    atr_values = close * natr / 100.0
    valid = (
        df[V3_FEATURES].notna().all(axis=1).to_numpy()
        & np.isfinite(atr_values)
        & (atr_values > 0)
    )
    cand = np.where(valid)[0].astype(np.intp)
    labels, _w, _lp, _sp = label_trades(
        df, cand, ATR_TP, ATR_SL, TIMEOUT_MINUTES,
        fee_pct=FEE_PCT, atr_values=atr_values, verbose=0,
        label_mode="triple_barrier",
    )
    full = np.zeros(len(df), dtype=np.int64)
    full[cand] = labels
    return full, valid


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/085 EDA PART 2 — can a symbol-identity feature rescue the pool?")
    print("=" * 78)

    # Build per-symbol IS frames with chronological 70/30 split.
    frames: dict[str, dict] = {}
    for sym in SYMBOLS:
        df = _load_is(sym)
        labels, valid = _label(df)
        d = df.loc[valid].copy()
        d["y"] = (labels[valid] > 0).astype(int)
        d = d.sort_values("open_time").reset_index(drop=True)
        cut = int(len(d) * 0.70)
        frames[sym] = {"train": d.iloc[:cut], "test": d.iloc[cut:]}
        print(
            f"  {sym}: {len(d)} labelable rows -> "
            f"{cut} train / {len(d) - cut} test (chronological)"
        )

    sym_to_id = {s: i for i, s in enumerate(SYMBOLS)}

    # ----- T2: PER-SYMBOL baseline (v3 incumbent architecture) -------------
    print("\n[T2] PER-SYMBOL baseline — 3 separate LightGBMs (the v3 incumbent)")
    t2_acc: dict[str, float] = {}
    for sym in SYMBOLS:
        tr, te = frames[sym]["train"], frames[sym]["test"]
        clf = lgb.LGBMClassifier(**LGB_PARAMS)
        clf.fit(tr[V3_FEATURES].to_numpy(float), tr["y"].to_numpy())
        pred = (clf.predict_proba(te[V3_FEATURES].to_numpy(float))[:, 1] > 0.5).astype(int)
        acc = float((pred == te["y"].to_numpy()).mean())
        t2_acc[sym] = acc
        base = max(te["y"].mean(), 1 - te["y"].mean())
        print(f"  {sym}: per-symbol acc {acc:.4f} (base {base:.4f}, lift {acc - base:+.4f})")

    # ----- T3: POOLED, NO dummy (naive pool) -------------------------------
    print("\n[T3] POOLED, NO symbol dummy — naive pool")
    pool_tr = pd.concat([frames[s]["train"] for s in SYMBOLS], ignore_index=True)
    clf_naive = lgb.LGBMClassifier(**LGB_PARAMS)
    clf_naive.fit(pool_tr[V3_FEATURES].to_numpy(float), pool_tr["y"].to_numpy())
    t3_acc: dict[str, float] = {}
    for sym in SYMBOLS:
        te = frames[sym]["test"]
        pred = (clf_naive.predict_proba(te[V3_FEATURES].to_numpy(float))[:, 1] > 0.5).astype(int)
        acc = float((pred == te["y"].to_numpy()).mean())
        t3_acc[sym] = acc
        print(f"  {sym}: naive-pool acc {acc:.4f}")

    # ----- T1: POOLED + symbol_id categorical ------------------------------
    print("\n[T1] POOLED + symbol_id categorical — the panel-ML standard fix")
    feats_plus = [*V3_FEATURES, "symbol_id"]
    pool_tr2 = pool_tr.copy()
    pool_tr2["symbol_id"] = pool_tr2["symbol"].map(sym_to_id).astype("category")
    clf_pool = lgb.LGBMClassifier(**LGB_PARAMS)
    clf_pool.fit(
        pool_tr2[feats_plus],
        pool_tr2["y"].to_numpy(),
        categorical_feature=["symbol_id"],
    )
    t1_acc: dict[str, float] = {}
    for sym in SYMBOLS:
        te = frames[sym]["test"].copy()
        te["symbol_id"] = pd.Series(
            [sym_to_id[sym]] * len(te), dtype="category"
        ).cat.set_categories(list(range(len(SYMBOLS))))
        pred = (clf_pool.predict_proba(te[feats_plus])[:, 1] > 0.5).astype(int)
        acc = float((pred == te["y"].to_numpy()).mean())
        t1_acc[sym] = acc
        print(f"  {sym}: pooled+dummy acc {acc:.4f}")

    # symbol_id importance share — if ~0, the dummy is inert (pool == T3).
    imp = clf_pool.feature_importances_.astype(float)
    imp_share = imp / max(1.0, imp.sum())
    symid_share = float(imp_share[feats_plus.index("symbol_id")])
    print(
        f"  symbol_id feature-importance share: {symid_share:.4f} "
        f"({'tree splits on symbol — dummy is LIVE' if symid_share > 0.03 else 'tree ignores symbol — dummy INERT'})"
    )

    # ----- 3-way comparison table ------------------------------------------
    print("\n[CMP] Per-symbol test accuracy — 3-way")
    cmp_rows = []
    for sym in SYMBOLS:
        te = frames[sym]["test"]
        base = float(max(te["y"].mean(), 1 - te["y"].mean()))
        row = {
            "symbol": sym,
            "n_test": len(te),
            "base_rate": round(base, 4),
            "acc_per_symbol_T2": round(t2_acc[sym], 4),
            "acc_naive_pool_T3": round(t3_acc[sym], 4),
            "acc_pooled_dummy_T1": round(t1_acc[sym], 4),
            "T1_minus_T2": round(t1_acc[sym] - t2_acc[sym], 4),
        }
        cmp_rows.append(row)
        print(
            f"  {sym}: per-symbol {row['acc_per_symbol_T2']:.4f} | "
            f"naive-pool {row['acc_naive_pool_T3']:.4f} | "
            f"pooled+dummy {row['acc_pooled_dummy_T1']:.4f} | "
            f"T1-T2 {row['T1_minus_T2']:+.4f}"
        )

    mean_t1_minus_t2 = float(np.mean([r["T1_minus_T2"] for r in cmp_rows]))
    n_pool_wins = sum(1 for r in cmp_rows if r["T1_minus_T2"] > 0)
    print(
        f"  MEAN pooled+dummy minus per-symbol: {mean_t1_minus_t2:+.4f} "
        f"({n_pool_wins}/3 symbols where pooled+dummy beats per-symbol)"
    )

    with (OUT_DIR / "part2_pooled_3way.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "symbol", "n_test", "base_rate", "acc_per_symbol_T2",
                "acc_naive_pool_T3", "acc_pooled_dummy_T1", "T1_minus_T2",
            ],
        )
        w.writeheader()
        w.writerows(cmp_rows)
    with (OUT_DIR / "part2_symbol_id_importance.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["feature", "importance_share"])
        for f, s in zip(feats_plus, imp_share):
            w.writerow([f, round(float(s), 4)])

    # ----- Verdict ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("PART 2 VERDICT")
    print("=" * 78)
    print(f"  symbol_id importance share: {symid_share:.4f}")
    print(f"  mean pooled+dummy - per-symbol acc: {mean_t1_minus_t2:+.4f}")
    print(
        f"  pooled+dummy beats per-symbol on {n_pool_wins}/3 symbols"
    )
    salvageable = mean_t1_minus_t2 > 0.0 and n_pool_wins >= 2
    print(
        f"\n  POOLED-MODEL AXIS {'SALVAGEABLE with the symbol_id fix' if salvageable else 'NOT SUPPORTED even with the symbol_id fix'}."
    )
    print(f"\n  CSVs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()

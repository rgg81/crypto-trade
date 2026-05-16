"""iter-v3/085 — Cycle-3 EXPLORATION #4 EDA, PART 3: is a DONOR-AUGMENTED
(selective-pool) model for LDO supported? (IS-only).

PART 1 + PART 2 falsified a FULL pooled model — a naive or symbol-dummy pool breaks
BCH (BCH carries ~96% of v3 IS PnL; its feature->label map is symbol-specific). But
PART 1 also surfaced a genuine asymmetry: LDO has only ~30 months of IS history (2,641
labelable rows) vs BCH/TRX's ~62 months — LDO is DATA-STARVED, and its walk-forward
gets only ~6 testable IS cells.

The targeted version of Direction 3: keep BCH and TRX as the v3-incumbent isolated
per-symbol models (PART 2: pooling HURTS them — BCH -0.0414, TRX's "gain" is regression
of an already-broken model), and train ONLY LDO's model on a DONOR-AUGMENTED set —
LDO's own rows + BCH/TRX donor rows + a `symbol_id` categorical. This captures the one
real pooling benefit (LDO's 5.24x sample-size gain) without the cost (breaking BCH).

PART 3 is the GO/NO-GO test for that axis. It asks ONE question, on IS data only:
  Does a donor-augmented LDO model beat LDO's per-symbol baseline on held-out LDO test
  candles? If YES -> the LDO-donor-augmentation axis is supported. If NO -> Direction 3
  is fully falsified for v3 and the QR must pivot to a different bold axis.

Three LDO configurations, evaluated on the SAME chronological 70/30 LDO IS split:
  C1. LDO per-symbol — train on LDO-train only, 14 features. The v3 incumbent.
  C2. LDO donor-augmented, NO dummy — train on LDO-train + ALL BCH + ALL TRX rows.
  C3. LDO donor-augmented + symbol_id — C2 plus the categorical, predict with
      symbol_id = LDO so the tree applies LDO-conditional splits.
  Also: donor-DOWNWEIGHTED variant (donor rows at 0.3 sample weight) — the standard
  transfer-learning down-weight so donors inform but do not dominate.

NO CHEATING:
  - IS data only (open_time < OOS_CUTOFF_DATE 2025-03-24). OOS never loaded.
  - `OOS_CUTOFF_DATE` / `training_months` not read as a tunable, not modified.
  - The LDO 70/30 split is chronological, WITHIN the IS window — an EDA generalisation
    probe, not the production walk-forward. No iter-v3/085 design parameter is chosen
    on OOS data.

Run:
  export PATH="$HOME/.local/bin:$PATH"
  uv run python analysis/iteration_v3-085/ldo_donor_augmentation.py
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
TARGET = "LDOUSDT"
DONORS = ["BCHUSDT", "TRXUSDT"]
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


def _label_frame(df: pd.DataFrame) -> pd.DataFrame:
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
    d = df.loc[valid].copy()
    d["y"] = (labels > 0).astype(int)
    return d.sort_values("open_time").reset_index(drop=True)


def _acc(clf, x: np.ndarray | pd.DataFrame, y: np.ndarray) -> float:
    pred = (clf.predict_proba(x)[:, 1] > 0.5).astype(int)
    return float((pred == y).mean())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/085 EDA PART 3 — LDO donor-augmented (selective-pool) GO/NO-GO")
    print("=" * 78)

    labeled = {s: _label_frame(_load_is(s)) for s in SYMBOLS}
    for s in SYMBOLS:
        print(f"  {s}: {len(labeled[s])} labelable IS rows")

    sym_to_id = {s: i for i, s in enumerate(SYMBOLS)}

    # LDO chronological 70/30 split — the held-out test is LDO's own later candles.
    ldo = labeled[TARGET]
    cut = int(len(ldo) * 0.70)
    ldo_tr, ldo_te = ldo.iloc[:cut].copy(), ldo.iloc[cut:].copy()
    base = float(max(ldo_te["y"].mean(), 1 - ldo_te["y"].mean()))
    print(
        f"\n  LDO split: {len(ldo_tr)} train / {len(ldo_te)} test  | "
        f"test base rate {base:.4f}"
    )

    x_te = ldo_te[V3_FEATURES].to_numpy(float)
    y_te = ldo_te["y"].to_numpy()
    donor_rows = pd.concat([labeled[d] for d in DONORS], ignore_index=True)
    print(
        f"  donor pool: {len(donor_rows)} BCH+TRX rows "
        f"(LDO-train augmented {len(donor_rows) / max(1, len(ldo_tr)):.2f}x)"
    )

    results = []

    # ----- C1: LDO per-symbol (v3 incumbent) -------------------------------
    c1 = lgb.LGBMClassifier(**LGB_PARAMS)
    c1.fit(ldo_tr[V3_FEATURES].to_numpy(float), ldo_tr["y"].to_numpy())
    a1 = _acc(c1, x_te, y_te)
    results.append(("C1_LDO_per_symbol", a1))
    print(f"\n  [C1] LDO per-symbol            acc {a1:.4f}  (lift {a1 - base:+.4f})")

    # ----- C2: LDO donor-augmented, NO dummy -------------------------------
    aug_tr = pd.concat([ldo_tr, donor_rows], ignore_index=True)
    c2 = lgb.LGBMClassifier(**LGB_PARAMS)
    c2.fit(aug_tr[V3_FEATURES].to_numpy(float), aug_tr["y"].to_numpy())
    a2 = _acc(c2, x_te, y_te)
    results.append(("C2_donor_aug_no_dummy", a2))
    print(f"  [C2] donor-aug, no dummy       acc {a2:.4f}  (lift {a2 - base:+.4f})")

    # ----- C3: LDO donor-augmented + symbol_id -----------------------------
    feats_plus = [*V3_FEATURES, "symbol_id"]
    aug_tr3 = aug_tr.copy()
    aug_tr3["symbol_id"] = aug_tr3["symbol"].map(sym_to_id).astype("category")
    c3 = lgb.LGBMClassifier(**LGB_PARAMS)
    c3.fit(
        aug_tr3[feats_plus], aug_tr3["y"].to_numpy(),
        categorical_feature=["symbol_id"],
    )
    te3 = ldo_te.copy()
    te3["symbol_id"] = pd.Series(
        [sym_to_id[TARGET]] * len(te3), dtype="category"
    ).cat.set_categories(list(range(len(SYMBOLS))))
    a3 = _acc(c3, te3[feats_plus], y_te)
    results.append(("C3_donor_aug_symbol_id", a3))
    print(f"  [C3] donor-aug + symbol_id     acc {a3:.4f}  (lift {a3 - base:+.4f})")

    # ----- C4: donor-DOWNWEIGHTED (transfer-learning down-weight) ----------
    # donors at 0.3 sample weight: they inform the fit but do not dominate it.
    sw = np.concatenate(
        [np.ones(len(ldo_tr)), np.full(len(donor_rows), 0.3)]
    )
    c4 = lgb.LGBMClassifier(**LGB_PARAMS)
    c4.fit(
        aug_tr3[feats_plus], aug_tr3["y"].to_numpy(),
        sample_weight=sw, categorical_feature=["symbol_id"],
    )
    a4 = _acc(c4, te3[feats_plus], y_te)
    results.append(("C4_donor_downweighted_0.3", a4))
    print(f"  [C4] donor-downweighted (0.3)  acc {a4:.4f}  (lift {a4 - base:+.4f})")

    # ----- Verdict ---------------------------------------------------------
    best_donor = max(a2, a3, a4)
    donor_beats_per_symbol = best_donor > a1
    with (OUT_DIR / "part3_ldo_donor.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["config", "ldo_test_accuracy", "lift_over_base"])
        for name, acc in results:
            w.writerow([name, round(acc, 4), round(acc - base, 4)])

    print("\n" + "=" * 78)
    print("PART 3 VERDICT")
    print("=" * 78)
    print(f"  LDO per-symbol baseline (C1):       {a1:.4f}")
    print(f"  best donor-augmented (C2/C3/C4):    {best_donor:.4f}")
    print(f"  donor-aug minus per-symbol:         {best_donor - a1:+.4f}")
    print(
        f"\n  LDO-DONOR-AUGMENTATION AXIS "
        f"{'SUPPORTED' if donor_beats_per_symbol else 'NOT SUPPORTED'} — donor data "
        f"{'lifts' if donor_beats_per_symbol else 'does NOT lift'} the data-starved "
        f"LDO model."
    )
    if not donor_beats_per_symbol:
        print(
            "  => Direction 3 (pooling, in every form tested) is FALSIFIED for v3. "
            "The QR must pivot to a different bold structural axis."
        )
    print(f"\n  CSV written to {OUT_DIR}/part3_ldo_donor.csv")


if __name__ == "__main__":
    main()

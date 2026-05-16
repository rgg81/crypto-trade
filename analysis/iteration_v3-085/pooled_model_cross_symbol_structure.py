"""iter-v3/085 — Cycle-3 EXPLORATION #4 EDA: does the BCH/LDO/TRX cross-section
share LEARNABLE structure? (the multi-symbol-POOLED model axis — Direction 3).

iter-v3/085 is a BOLD STRUCTURAL axis. v3 currently trains fully-isolated PER-SYMBOL
LightGBM models (one for BCH, one for LDO, one for TRX — total per-symbol isolation,
confirmed by the /083 Critic's runner trace). Direction 3 of `briefs-v3/cycle3_plan.md`
is the UNTRIED multi-symbol-POOLED model: ONE model trained on all 3 symbols' candles
combined (a cross-sectional / panel design — the Gu/Kelly/Xiu empirical-asset-pricing-
via-ML methodology, and the v1 Model A precedent which pools BTC+ETH into one model).

This EDA quantitatively answers the question a pooled model rests on:
  Q1. SAMPLE SIZES — what does pooling do to per-fit training-row counts? In particular,
      LDO is history-thin; does pooling rescue it?
  Q2. CROSS-SYMBOL FEATURE-TARGET STRUCTURE — do the 14 features relate to the
      triple-barrier label in the SAME direction across BCH/LDO/TRX? If the IC signs
      agree, a pooled model can learn ONE rule that transfers; if they disagree, pooling
      averages away symbol-specific signal (the pooling bias risk).
  Q3. SCALE-INVARIANCE — pooling requires features on a COMMON scale (the project
      convention — v1 Model A pools BTC+ETH only because the features are scale-free).
      Are the 14 v3 features distribution-comparable across the 3 symbols?
  Q4. POOLED-vs-PER-SYMBOL GENERALISATION — a direct leave-one-symbol-out test on
      IS data: train a quick LightGBM on 2 symbols, predict the held-out 3rd; compare
      to a within-symbol time-split baseline. If cross-symbol transfer beats noise,
      pooling has a real signal-sharing basis.

NO CHEATING:
  - Reads ONLY IS data (open_time < OOS_CUTOFF_DATE 2025-03-24). The OOS slice is
    never loaded, never touched.
  - `OOS_CUTOFF_DATE` and `training_months` are NOT read from, NOT modified.
  - No design parameter for iter-v3/085 is selected on OOS data — this script is
    IS-only by construction; the OOS rows are filtered out before any computation.
  - Triple-barrier labels use the production labeler (`label_trades`) with the
    /059-canonical ATR multipliers (2.0, 1.0) and 21-candle (10080-min) timeout.

Run:
  export PATH="$HOME/.local/bin:$PATH"
  uv run python analysis/iteration_v3-085/pooled_model_cross_symbol_structure.py
"""

from __future__ import annotations

import csv
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr

from crypto_trade.strategies.ml.labeling import label_trades

warnings.filterwarnings("ignore")

# --- Sacred constants — read for filtering only, never mutated ----------------
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000)
TIMEOUT_MINUTES = 10080  # 21 candles at 8h — /059-canonical
ATR_TP, ATR_SL = 2.0, 1.0  # /059-canonical DEFAULT_ATR_MULTIPLIERS
FEE_PCT = 0.1

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA_DIR = Path("data")
FEATURES_DIR = Path("data/features_v3")
OUT_DIR = Path("analysis/iteration_v3-085")

# The /059-canonical 14-feature V3_FEATURE_COLUMNS_TOP_N stack.
V3_FEATURES = [
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
]


def _load_is_symbol(symbol: str) -> pd.DataFrame:
    """Load one symbol's OHLCV + 14 features, IS slice only, ATR-aligned."""
    # OHLCV from the 8h CSV (the file carries a header row). close_time is
    # required by the production labeler (label_trades scans to a deadline).
    ohlcv = pd.read_csv(DATA_DIR / symbol / "8h.csv")
    ohlcv = ohlcv[
        ["open_time", "open", "high", "low", "close", "close_time"]
    ].copy()
    # Binance CSV stores open_time as an integer epoch-ms; ensure int64 dtype so
    # the merge key matches the parquet's int64 open_time.
    ohlcv["open_time"] = ohlcv["open_time"].astype(np.int64)
    for col in ("open", "high", "low", "close"):
        ohlcv[col] = ohlcv[col].astype(float)
    ohlcv["symbol"] = symbol

    # Features + natr_21_raw for ATR labeling, from the v3 features parquet.
    feat_cols = ["open_time", "natr_21_raw", *V3_FEATURES]
    table = pq.read_table(
        FEATURES_DIR / f"{symbol}_8h_features.parquet", columns=feat_cols
    )
    feats = table.to_pandas()

    merged = ohlcv.merge(feats, on="open_time", how="inner")
    # IS slice ONLY — the OOS rows are dropped here, before any computation.
    merged = merged[merged["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    return merged


def _label_is(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Triple-barrier labels for every IS candle with a valid ATR + features.

    Returns (labels in {-1,+1}, valid_mask aligned to df rows).
    """
    master = df.rename(columns={})  # label_trades reads symbol/open_time/OHLC
    close = master["close"].to_numpy(dtype=float)
    natr = master["natr_21_raw"].to_numpy(dtype=float)
    atr_values = close * natr / 100.0  # price-unit ATR (same as lgbm._load_atr)

    feat_ok = master[V3_FEATURES].notna().all(axis=1).to_numpy()
    atr_ok = np.isfinite(atr_values) & (atr_values > 0)
    valid = feat_ok & atr_ok
    cand = np.where(valid)[0].astype(np.intp)

    labels, _w, _lp, _sp = label_trades(
        master,
        cand,
        ATR_TP,
        ATR_SL,
        TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        atr_values=atr_values,
        verbose=0,
        label_mode="triple_barrier",
    )
    full = np.zeros(len(master), dtype=np.int64)
    full[cand] = labels
    return full, valid


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/085 EDA — multi-symbol-POOLED model: cross-symbol structure (IS-only)")
    print("=" * 78)

    per_symbol: dict[str, dict] = {}
    for sym in SYMBOLS:
        df = _load_is_symbol(sym)
        labels, valid = _label_is(df)
        per_symbol[sym] = {"df": df, "labels": labels, "valid": valid}
        print(
            f"  {sym}: {len(df)} IS candles loaded, "
            f"{int(valid.sum())} labelable (valid features + ATR)"
        )

    # ----------------------------------------------------------------------
    # Q1 — SAMPLE SIZES: what pooling does to per-fit training-row counts.
    # ----------------------------------------------------------------------
    print("\n[Q1] Per-symbol IS sample sizes + the pooling multiplier")
    q1_rows = []
    total_labelable = 0
    for sym in SYMBOLS:
        n_valid = int(per_symbol[sym]["valid"].sum())
        total_labelable += n_valid
        lab = per_symbol[sym]["labels"][per_symbol[sym]["valid"]]
        n_long = int((lab == 1).sum())
        n_short = int((lab == -1).sum())
        q1_rows.append(
            {
                "symbol": sym,
                "is_labelable_rows": n_valid,
                "long_share": round(n_long / max(1, len(lab)), 4),
                "short_share": round(n_short / max(1, len(lab)), 4),
            }
        )
    for r in q1_rows:
        # the pooling multiplier: pooled rows / this symbol's own rows.
        r["pooling_row_multiplier"] = round(
            total_labelable / max(1, r["is_labelable_rows"]), 3
        )
        print(
            f"  {r['symbol']}: {r['is_labelable_rows']} own rows -> "
            f"pooled gives {total_labelable} rows "
            f"({r['pooling_row_multiplier']}x) | "
            f"long {r['long_share']:.2%} / short {r['short_share']:.2%}"
        )
    print(f"  POOLED total labelable IS rows: {total_labelable}")

    with (OUT_DIR / "q1_sample_sizes.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "symbol", "is_labelable_rows", "long_share", "short_share",
                "pooling_row_multiplier",
            ],
        )
        w.writeheader()
        w.writerows(q1_rows)

    # ----------------------------------------------------------------------
    # Q2 — CROSS-SYMBOL FEATURE-TARGET STRUCTURE: do the 14 features relate to
    # the label in the SAME direction across symbols? Spearman IC of each
    # feature vs the {-1,+1} label, per symbol. Sign-agreement = transferable.
    # ----------------------------------------------------------------------
    print("\n[Q2] Per-feature IS Spearman IC vs triple-barrier label (sign-agreement)")
    ic_table: dict[str, dict[str, float]] = {f: {} for f in V3_FEATURES}
    for sym in SYMBOLS:
        d = per_symbol[sym]
        mask = d["valid"]
        lab = d["labels"][mask].astype(float)
        for feat in V3_FEATURES:
            x = d["df"].loc[mask, feat].to_numpy(dtype=float)
            if np.std(x) == 0 or np.std(lab) == 0:
                ic_table[feat][sym] = float("nan")
            else:
                rho, _p = spearmanr(x, lab)
                ic_table[feat][sym] = float(rho)

    q2_rows = []
    n_sign_agree = 0
    for feat in V3_FEATURES:
        ics = [ic_table[feat][s] for s in SYMBOLS]
        signs = [np.sign(v) for v in ics if np.isfinite(v) and abs(v) > 0.01]
        agree = len(signs) >= 2 and len(set(signs)) == 1
        if agree:
            n_sign_agree += 1
        q2_rows.append(
            {
                "feature": feat,
                "ic_BCH": round(ic_table[feat]["BCHUSDT"], 4),
                "ic_LDO": round(ic_table[feat]["LDOUSDT"], 4),
                "ic_TRX": round(ic_table[feat]["TRXUSDT"], 4),
                "sign_agreement": "YES" if agree else "no",
                "mean_abs_ic": round(np.nanmean(np.abs(ics)), 4),
            }
        )
        print(
            f"  {feat:28s} BCH {q2_rows[-1]['ic_BCH']:+.3f}  "
            f"LDO {q2_rows[-1]['ic_LDO']:+.3f}  TRX {q2_rows[-1]['ic_TRX']:+.3f}  "
            f"-> {q2_rows[-1]['sign_agreement']}"
        )
    print(
        f"  SIGN-AGREEMENT: {n_sign_agree}/{len(V3_FEATURES)} features point the "
        f"SAME direction across >=2 symbols (|IC|>0.01)"
    )

    with (OUT_DIR / "q2_feature_target_ic.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "feature", "ic_BCH", "ic_LDO", "ic_TRX", "sign_agreement",
                "mean_abs_ic",
            ],
        )
        w.writeheader()
        w.writerows(q2_rows)

    # ----------------------------------------------------------------------
    # Q3 — SCALE-INVARIANCE: pooling needs a common feature scale. Report each
    # feature's per-symbol IS median + IQR; the cross-symbol spread of medians
    # (max-min) relative to the pooled IQR is the scale-mismatch ratio.
    # ----------------------------------------------------------------------
    print("\n[Q3] Feature scale-comparability across symbols (pooling prerequisite)")
    q3_rows = []
    n_scale_ok = 0
    for feat in V3_FEATURES:
        meds, iqrs, pooled_vals = [], [], []
        for sym in SYMBOLS:
            d = per_symbol[sym]
            x = d["df"].loc[d["valid"], feat].to_numpy(dtype=float)
            x = x[np.isfinite(x)]
            meds.append(float(np.median(x)))
            iqrs.append(float(np.percentile(x, 75) - np.percentile(x, 25)))
            pooled_vals.append(x)
        pooled = np.concatenate(pooled_vals)
        pooled_iqr = float(np.percentile(pooled, 75) - np.percentile(pooled, 25))
        median_spread = float(max(meds) - min(meds))
        # mismatch ratio: how far apart the per-symbol medians sit, in pooled-IQR units.
        ratio = median_spread / pooled_iqr if pooled_iqr > 0 else float("inf")
        scale_ok = ratio < 1.0  # medians within one pooled-IQR = comparable
        if scale_ok:
            n_scale_ok += 1
        q3_rows.append(
            {
                "feature": feat,
                "median_BCH": round(meds[0], 4),
                "median_LDO": round(meds[1], 4),
                "median_TRX": round(meds[2], 4),
                "median_spread": round(median_spread, 4),
                "pooled_iqr": round(pooled_iqr, 4),
                "scale_mismatch_ratio": round(ratio, 3),
                "scale_comparable": "YES" if scale_ok else "no",
            }
        )
        print(
            f"  {feat:28s} medians "
            f"[{meds[0]:+.3f},{meds[1]:+.3f},{meds[2]:+.3f}]  "
            f"mismatch {ratio:.2f}  -> {q3_rows[-1]['scale_comparable']}"
        )
    print(
        f"  SCALE-COMPARABLE: {n_scale_ok}/{len(V3_FEATURES)} features have "
        f"per-symbol medians within one pooled-IQR (pooling-safe)"
    )

    with (OUT_DIR / "q3_scale_invariance.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "feature", "median_BCH", "median_LDO", "median_TRX",
                "median_spread", "pooled_iqr", "scale_mismatch_ratio",
                "scale_comparable",
            ],
        )
        w.writeheader()
        w.writerows(q3_rows)

    # ----------------------------------------------------------------------
    # Q4 — POOLED-vs-PER-SYMBOL GENERALISATION: leave-one-symbol-out transfer
    # test on IS data. For each held-out symbol, train a quick LightGBM on the
    # other 2 symbols (cross-symbol transfer) and on a within-symbol time-split
    # baseline; compare label-prediction accuracy. Cross > within-noise means
    # pooling has a real signal-sharing basis. ALL IS data — no OOS.
    # ----------------------------------------------------------------------
    print("\n[Q4] Leave-one-symbol-out transfer test (IS-only, quick LightGBM)")
    q4_rows = []
    lgb_params = dict(
        objective="binary",
        num_leaves=15,
        max_depth=4,
        learning_rate=0.05,
        n_estimators=120,
        min_child_samples=40,
        subsample=0.8,
        colsample_bytree=0.8,
        verbose=-1,
        seed=42,
    )

    def _xy(sym: str) -> tuple[np.ndarray, np.ndarray]:
        d = per_symbol[sym]
        mask = d["valid"]
        x = d["df"].loc[mask, V3_FEATURES].to_numpy(dtype=float)
        # label {-1,+1} -> {0,1} for binary objective.
        y = (d["labels"][mask] > 0).astype(int)
        return x, y

    base_rate_all = []
    for held in SYMBOLS:
        others = [s for s in SYMBOLS if s != held]
        x_tr = np.vstack([_xy(s)[0] for s in others])
        y_tr = np.concatenate([_xy(s)[1] for s in others])
        x_te, y_te = _xy(held)

        # base rate of the held-out symbol (majority-class accuracy).
        base = max(y_te.mean(), 1 - y_te.mean())
        base_rate_all.append(base)

        # cross-symbol transfer: train on the OTHER 2 symbols, predict held-out.
        clf = lgb.LGBMClassifier(**lgb_params)
        clf.fit(x_tr, y_tr)
        pred_cross = (clf.predict_proba(x_te)[:, 1] > 0.5).astype(int)
        acc_cross = float((pred_cross == y_te).mean())

        # within-symbol time-split baseline: first 70% train, last 30% test
        # (chronological — the held-out symbol predicting its own later candles).
        n = len(y_te)
        cut = int(n * 0.70)
        clf_w = lgb.LGBMClassifier(**lgb_params)
        clf_w.fit(x_te[:cut], y_te[:cut])
        pred_within = (clf_w.predict_proba(x_te[cut:])[:, 1] > 0.5).astype(int)
        acc_within = float((pred_within == y_te[cut:]).mean())
        base_within = max(y_te[cut:].mean(), 1 - y_te[cut:].mean())

        transfer_lift = acc_cross - base  # cross-symbol edge over majority class
        q4_rows.append(
            {
                "held_out_symbol": held,
                "train_symbols": "+".join(s.replace("USDT", "") for s in others),
                "n_test_rows": n,
                "base_rate": round(base, 4),
                "acc_cross_symbol": round(acc_cross, 4),
                "cross_transfer_lift": round(transfer_lift, 4),
                "acc_within_symbol": round(acc_within, 4),
                "within_lift": round(acc_within - base_within, 4),
            }
        )
        print(
            f"  hold {held}: cross-symbol acc {acc_cross:.4f} (base {base:.4f}, "
            f"lift {transfer_lift:+.4f}) | within-symbol acc {acc_within:.4f} "
            f"(lift {acc_within - base_within:+.4f})"
        )

    mean_transfer_lift = float(np.mean([r["cross_transfer_lift"] for r in q4_rows]))
    n_positive_transfer = sum(1 for r in q4_rows if r["cross_transfer_lift"] > 0)
    print(
        f"  MEAN cross-symbol transfer lift over base rate: {mean_transfer_lift:+.4f} "
        f"({n_positive_transfer}/3 symbols positive)"
    )

    with (OUT_DIR / "q4_leave_one_symbol_out.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "held_out_symbol", "train_symbols", "n_test_rows", "base_rate",
                "acc_cross_symbol", "cross_transfer_lift", "acc_within_symbol",
                "within_lift",
            ],
        )
        w.writeheader()
        w.writerows(q4_rows)

    # ----------------------------------------------------------------------
    # Verdict synthesis.
    # ----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("VERDICT SYNTHESIS")
    print("=" * 78)
    print(
        f"  Q1 pooling row gain: LDO {q1_rows[1]['pooling_row_multiplier']}x, "
        f"BCH {q1_rows[0]['pooling_row_multiplier']}x, "
        f"TRX {q1_rows[2]['pooling_row_multiplier']}x"
    )
    print(
        f"  Q2 sign-agreement: {n_sign_agree}/{len(V3_FEATURES)} features transfer "
        f"direction across symbols"
    )
    print(
        f"  Q3 scale-comparable: {n_scale_ok}/{len(V3_FEATURES)} features pooling-safe"
    )
    print(
        f"  Q4 mean cross-symbol transfer lift: {mean_transfer_lift:+.4f} "
        f"({n_positive_transfer}/3 positive)"
    )
    pooling_supported = (
        n_sign_agree >= len(V3_FEATURES) * 0.5
        and n_positive_transfer >= 2
        and mean_transfer_lift > 0.0
    )
    print(
        f"\n  POOLED-MODEL AXIS {'SUPPORTED' if pooling_supported else 'NOT SUPPORTED'} "
        f"by IS evidence — cross-symbol structure is "
        f"{'learnable and transferable' if pooling_supported else 'weak/symbol-specific'}."
    )
    print(f"\n  CSVs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()

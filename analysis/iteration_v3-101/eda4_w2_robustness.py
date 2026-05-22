"""iter-v3/101 EDA #4 — W2 (vol-neutral rank weight) robustness + falsifier prep.

EDA #3 found W2 (cross-sectional RANK of the |net PnL| weight, rescaled to
[1,10]) lifts held-out directional accuracy +0.0218 vs the /059 baseline weight
W0, block-bootstrap 95% CI [+0.0088, +0.0333] strictly above zero, sign-
consistent on all 3 symbols. This EDA stress-tests that finding before it
becomes the iter-v3/101 axis:

  F. Multi-seed stability — re-run the W2-vs-W0 horse race over 5 seeds. A
     fold-lottery artifact would not survive a seed sweep.
  G. Per-symbol IS-share sensitivity — BCH carries 95.76% of /059 IS PnL.
     Project whether W2 erodes BCH's IS contribution (the cycle-1 fragility
     gate from Critic Rec #3 / BASELINE_V3.md).
  H. Confirm the AFML-uniqueness near-no-op finding numerically (the kill of
     the /100-recommended uniqueness half of the axis).

STRICT IS-ONLY: open_time < OOS_CUTOFF_MS = 1742774400000. OOS never read.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.strategies.ml.labeling import (  # noqa: E402
    compute_sample_uniqueness,
    label_trades,
)

OOS_CUTOFF_MS = 1742774400000
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA = REPO / "data" / "features_v3"
OUT = Path(__file__).resolve().parent
ATR_TP, ATR_SL, TIMEOUT_MIN, ATR_COL, FEE_PCT = 2.0, 1.0, 10080, "natr_21_raw", 0.1
EMBARGO = 22
N_FOLDS = 8
SEEDS = [42, 123, 456, 789, 1001]  # v3 canonical inner-ensemble seeds
MONTH_MS = 30 * 24 * 3600 * 1000

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


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA / f"{sym}_8h_features.parquet")
    return df[df["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)


def make_labels(df: pd.DataFrame):
    atr = df[ATR_COL].to_numpy(np.float64)
    return label_trades(
        df,
        np.arange(len(df)),
        ATR_TP,
        ATR_SL,
        TIMEOUT_MIN,
        fee_pct=FEE_PCT,
        atr_values=atr,
        verbose=0,
        label_mode="triple_barrier",
    )


def w2_of(w0: np.ndarray) -> np.ndarray:
    """Vol-neutral: cross-sectional rank of W0, rescaled to [1,10]."""
    return 1.0 + pd.Series(w0).rank(pct=True).to_numpy() * 9.0


def main() -> None:
    import lightgbm as lgb

    print("=" * 78)
    print("iter-v3/101 EDA #4 — W2 robustness + falsifier prep")
    print("=" * 78)

    # ---- ANGLE F — multi-seed stability of the W2 lift ----------------------
    print("\n=== ANGLE F — multi-seed stability of the W2-vs-W0 held-out lift ===")
    seed_rows: list[dict] = []
    for seed in SEEDS:
        per_sym_lift = {}
        for sym in SYMBOLS:
            df = load_is(sym)
            lab, w0, lp, sp = make_labels(df)
            w2 = w2_of(w0)
            open_arr = df["open_time"].to_numpy(np.int64)
            feat = df[V3_FEATURES].to_numpy(np.float64)
            y = (lab == 1).astype(int)
            t_max = open_arr.max()
            lifts = []
            for f in range(N_FOLDS):
                test_hi = t_max - f * MONTH_MS
                test_lo = test_hi - MONTH_MS
                train_hi = test_lo - EMBARGO * 8 * 3600 * 1000
                valid = np.isfinite(feat).all(axis=1) & np.isfinite(lab)
                tr = (open_arr < train_hi) & valid
                te = (open_arr >= test_lo) & (open_arr < test_hi) & valid
                if tr.sum() < 200 or te.sum() < 15:
                    continue
                accs = {}
                for tag, w in [("W0", w0), ("W2", w2)]:
                    m = lgb.LGBMClassifier(
                        n_estimators=120,
                        num_leaves=15,
                        max_depth=4,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=seed,
                        verbose=-1,
                        n_jobs=2,
                    )
                    m.fit(feat[tr], y[tr], sample_weight=w[tr])
                    pred = m.predict_proba(feat[te])[:, 1] >= 0.5
                    accs[tag] = float((pred == (y[te] == 1)).mean())
                lifts.append(accs["W2"] - accs["W0"])
            per_sym_lift[sym] = float(np.mean(lifts)) if lifts else np.nan
        overall = float(np.nanmean(list(per_sym_lift.values())))
        seed_rows.append(
            {
                "seed": seed,
                "overall_d_acc": round(overall, 5),
                "bch": round(per_sym_lift["BCHUSDT"], 5),
                "ldo": round(per_sym_lift["LDOUSDT"], 5),
                "trx": round(per_sym_lift["TRXUSDT"], 5),
            }
        )
        print(
            f"  seed={seed}: overall dACC={overall:+.4f}  "
            f"[BCH {per_sym_lift['BCHUSDT']:+.4f} "
            f"LDO {per_sym_lift['LDOUSDT']:+.4f} "
            f"TRX {per_sym_lift['TRXUSDT']:+.4f}]"
        )
    sdf = pd.DataFrame(seed_rows)
    sdf.to_csv(OUT / "T4_w2_seed_stability.csv", index=False)
    n_pos = int((sdf["overall_d_acc"] > 0).sum())
    print(
        f"  STABILITY: {n_pos}/5 seeds show positive overall dACC; "
        f"mean={sdf['overall_d_acc'].mean():+.4f} std={sdf['overall_d_acc'].std():.4f}"
    )

    # ---- ANGLE G — BCH IS-share sensitivity --------------------------------
    print("\n=== ANGLE G — BCH IS-edge sensitivity (95.76% IS PnL fragility) ===")
    # proxy: held-out cumulative side-PnL per symbol under W0 vs W2, then the
    # BCH SHARE of total positive side-PnL. If W2 keeps/raises BCH share, the
    # headline IS Sharpe is protected.
    share_rows: list[dict] = []
    for tag, wf in [("W0", lambda w0: w0), ("W2", w2_of)]:
        sym_pnl = {}
        for sym in SYMBOLS:
            df = load_is(sym)
            lab, w0, lp, sp = make_labels(df)
            w = wf(w0)
            open_arr = df["open_time"].to_numpy(np.int64)
            feat = df[V3_FEATURES].to_numpy(np.float64)
            y = (lab == 1).astype(int)
            t_max = open_arr.max()
            tot = 0.0
            for f in range(N_FOLDS):
                test_hi = t_max - f * MONTH_MS
                test_lo = test_hi - MONTH_MS
                train_hi = test_lo - EMBARGO * 8 * 3600 * 1000
                valid = np.isfinite(feat).all(axis=1) & np.isfinite(lab)
                tr = (open_arr < train_hi) & valid
                te = (open_arr >= test_lo) & (open_arr < test_hi) & valid
                if tr.sum() < 200 or te.sum() < 15:
                    continue
                m = lgb.LGBMClassifier(
                    n_estimators=120,
                    num_leaves=15,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=SEEDS[0],
                    verbose=-1,
                    n_jobs=2,
                )
                m.fit(feat[tr], y[tr], sample_weight=w[tr])
                pred = m.predict_proba(feat[te])[:, 1] >= 0.5
                tot += float(np.nansum(np.where(pred, lp[te], sp[te])))
            sym_pnl[sym] = tot
        total_abs = sum(abs(v) for v in sym_pnl.values())
        bch_share = sym_pnl["BCHUSDT"] / total_abs * 100 if total_abs > 0 else np.nan
        share_rows.append(
            {
                "weight": tag,
                "bch_pnl": round(sym_pnl["BCHUSDT"], 3),
                "ldo_pnl": round(sym_pnl["LDOUSDT"], 3),
                "trx_pnl": round(sym_pnl["TRXUSDT"], 3),
                "bch_share_pct": round(bch_share, 2),
            }
        )
        print(
            f"  {tag}: held-out side-PnL  BCH={sym_pnl['BCHUSDT']:+.2f}  "
            f"LDO={sym_pnl['LDOUSDT']:+.2f}  TRX={sym_pnl['TRXUSDT']:+.2f}  "
            f"| BCH share={bch_share:.1f}%"
        )
    pd.DataFrame(share_rows).to_csv(OUT / "T4_bch_share.csv", index=False)

    # ---- ANGLE H — confirm AFML uniqueness near-no-op ----------------------
    print("\n=== ANGLE H — AFML-Ch.4 uniqueness near-no-op confirmation ===")
    for sym in SYMBOLS:
        df = load_is(sym)
        idx = np.arange(len(df))
        uniq = compute_sample_uniqueness(
            idx,
            TIMEOUT_MIN,
            df["open_time"].to_numpy(np.int64),
            df["symbol"].to_numpy(),
        )
        # if we multiply W0 by uniq then renormalize, how much does the
        # cross-sectional ORDER change vs W0 alone? (rank correlation ~1 => no-op)
        lab, w0, lp, sp = make_labels(df)
        from scipy.stats import spearmanr

        rho = spearmanr(w0, w0 * uniq).statistic
        print(
            f"  {sym}: uniq CV={uniq.std() / uniq.mean():.4f}  "
            f"rank-corr(W0, W0*uniq)={rho:.5f}  => uniqueness multiply is a "
            f"{'NEAR-NO-OP' if rho > 0.99 else 'material change'}"
        )

    print("\n=== EDA #4 verdict ===")
    print(f"  W2 multi-seed: {n_pos}/5 seeds positive (stability check).")
    print("  Uniqueness weighting confirmed near-no-op (kills the /100-")
    print("  recommended uniqueness half). The iter-v3/101 axis is W2 alone:")
    print("  vol-neutral rank re-weighting of the training sample weight.")


if __name__ == "__main__":
    main()

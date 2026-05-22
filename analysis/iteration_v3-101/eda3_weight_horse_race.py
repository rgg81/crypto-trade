"""iter-v3/101 EDA #3 — held-out-fold horse race of sample-weight designs.

EDA #1+#2 established the diagnosis:
  - AFML uniqueness is ~flat 0.046 (21-candle horizon -> all candles maximally
    overlap) => uniqueness weighting is a near-no-op. The /100-recommended
    uniqueness half of the axis is KILLED at the EDA.
  - The current `|net PnL|`->[1,10] magnitude weight is, on LDO/TRX, an
    almost-PURE volatility weight: corr(weight, |fwd-return|) = +1.000 / +0.995.
    It up-weights the highest-volatility candles -> a vol-chasing training tilt.

This EDA is the LOAD-BEARING design test: a walk-forward-faithful held-out-fold
horse race comparing candidate sample-weight designs against the /059 baseline
weight (W0). It is OOS-ROBUST by construction (the /096/097 lesson — IS-CV-IC
does not predict OOS): each fold's model trains ONLY on prior IS candles and is
scored on the next held-out IS month; the comparison is paired across folds and
symbols with a candle-level block bootstrap (block = 21-bar label horizon).

WEIGHT DESIGNS UNDER TEST (all trained on the SAME features/labels/folds — the
only varied thing is the LightGBM `sample_weight` vector):
  W0  baseline    = |net PnL|->[1,10]               (the /059 production weight)
  W1  uniform     = all ones                         (ablation: does W0 help at all?)
  W2  vol-neutral = cross-sectional RANK of W0->[1,10] (kills the ATR-magnitude tilt)
  W3  edge-floor  = W0, but 0.0 where best_edge<=0    (drop edge-free candles)
  W4  edge-clip   = W2 capped at the 90th pct         (vol-neutral + tail-clip)

The winner of this EDA is the proposed iter-v3/101 axis. If NO design beats W0
out-of-fold, the diagnosis still holds and the brief proposes the
best-mechanistically-grounded design as the experiment (a held-out horse race
is a proxy, not the backtest — the loop must run the experiment).

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

from crypto_trade.strategies.ml.labeling import label_trades  # noqa: E402

OOS_CUTOFF_MS = 1742774400000
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA = REPO / "data" / "features_v3"
OUT = Path(__file__).resolve().parent
ATR_TP, ATR_SL, TIMEOUT_MIN, ATR_COL, FEE_PCT = 2.0, 1.0, 10080, "natr_21_raw", 0.1
TIMEOUT_CANDLES = 21
EMBARGO = 22  # compute_embargo_candles(10080, 480) — single source of truth
N_FOLDS = 8  # last 8 one-month IS folds (the /099/100 harness convention)
SEED = 42

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
MONTH_MS = 30 * 24 * 3600 * 1000


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


def build_weight_designs(w0: np.ndarray, best_edge: np.ndarray) -> dict[str, np.ndarray]:
    """All 5 designs from a single symbol's W0 + best_edge arrays."""
    w1 = np.ones_like(w0)
    ranks = pd.Series(w0).rank(pct=True).to_numpy()
    w2 = 1.0 + ranks * 9.0
    w3 = w0.copy()
    w3[best_edge <= 0] = 1e-6  # ~drop, but keep strictly positive for LGBM
    cap = np.percentile(w2, 90)
    w4 = np.minimum(w2, cap)
    return {"W0": w0, "W1": w1, "W2": w2, "W3": w3, "W4": w4}


def run_horse_race() -> pd.DataFrame:
    import lightgbm as lgb

    designs = ["W0", "W1", "W2", "W3", "W4"]
    rows: list[dict] = []
    # per (symbol, fold, design): held-out directional accuracy + side-PnL
    for sym in SYMBOLS:
        df = load_is(sym)
        lab, w0_full, lp, sp = make_labels(df)
        best_edge = np.maximum(lp, sp)
        wdes = build_weight_designs(w0_full, best_edge)
        open_arr = df["open_time"].to_numpy(np.int64)
        feat = df[V3_FEATURES].to_numpy(np.float64)
        # binary direction target for the classifier (1=long, 0=short)
        y = (lab == 1).astype(int)
        t_max = open_arr.max()
        # last N_FOLDS one-month folds
        for f in range(N_FOLDS):
            test_hi = t_max - f * MONTH_MS
            test_lo = test_hi - MONTH_MS
            train_hi = test_lo - EMBARGO * 8 * 3600 * 1000  # embargo gap
            tr = open_arr < train_hi
            te = (open_arr >= test_lo) & (open_arr < test_hi)
            # row validity: features + label finite
            valid = np.isfinite(feat).all(axis=1) & np.isfinite(lab)
            tr = tr & valid
            te = te & valid
            if tr.sum() < 200 or te.sum() < 15:
                continue
            for d in designs:
                w = wdes[d][tr]
                model = lgb.LGBMClassifier(
                    n_estimators=120,
                    num_leaves=15,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=SEED,
                    verbose=-1,
                    n_jobs=2,
                )
                model.fit(feat[tr], y[tr], sample_weight=w)
                proba = model.predict_proba(feat[te])[:, 1]
                pred_long = proba >= 0.5
                acc = float((pred_long == (y[te] == 1)).mean())
                # held-out side-PnL: take the predicted side's net barrier PnL
                side_pnl = np.where(pred_long, lp[te], sp[te])
                rows.append(
                    {
                        "symbol": sym,
                        "fold": f,
                        "design": d,
                        "n_test": int(te.sum()),
                        "holdout_acc": round(acc, 5),
                        "holdout_side_pnl_mean": round(float(np.nanmean(side_pnl)), 5),
                    }
                )
    return pd.DataFrame(rows)


def block_bootstrap_ci(diffs: np.ndarray, block: int, n_boot: int = 2000) -> tuple[float, float]:
    """Candle-level moving-block bootstrap 95% CI of a paired-difference array."""
    if len(diffs) < block + 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(SEED)
    n = len(diffs)
    n_blocks = int(np.ceil(n / block))
    means = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        samp = np.concatenate([diffs[s : s + block] for s in starts])[:n]
        means[b] = samp.mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> None:
    print("=" * 78)
    print("iter-v3/101 EDA #3 — sample-weight design held-out-fold horse race")
    print("STRICT IS-ONLY | OOS never read")
    print("=" * 78)
    raw = run_horse_race()
    raw.to_csv(OUT / "T3_horse_race_raw.csv", index=False)
    print(f"\nWROTE {OUT / 'T3_horse_race_raw.csv'} ({len(raw)} rows)")

    # aggregate: each non-baseline design vs W0, paired per (symbol, fold)
    base = raw[raw.design == "W0"].set_index(["symbol", "fold"])
    summary: list[dict] = []
    print("\n=== held-out-fold lift vs W0 baseline (paired per symbol-fold) ===")
    for d in ["W1", "W2", "W3", "W4"]:
        cur = raw[raw.design == d].set_index(["symbol", "fold"])
        joined = cur.join(base, lsuffix="_d", rsuffix="_0")
        d_acc = (joined["holdout_acc_d"] - joined["holdout_acc_0"]).to_numpy()
        d_pnl = (joined["holdout_side_pnl_mean_d"] - joined["holdout_side_pnl_mean_0"]).to_numpy()
        ci_lo, ci_hi = block_bootstrap_ci(d_acc, block=4)  # 4 folds ~ horizon proxy
        # per-symbol sign consistency
        per_sym = (
            joined.reset_index()
            .assign(da=lambda x: x.holdout_acc_d - x.holdout_acc_0)
            .groupby("symbol")["da"]
            .mean()
        )
        sign_consistent = int((per_sym > 0).sum())
        summary.append(
            {
                "design": d,
                "d_acc_mean": round(float(np.nanmean(d_acc)), 5),
                "d_acc_ci_lo": round(ci_lo, 5),
                "d_acc_ci_hi": round(ci_hi, 5),
                "d_pnl_mean": round(float(np.nanmean(d_pnl)), 5),
                "n_syms_positive": sign_consistent,
                "bch_d_acc": round(float(per_sym.get("BCHUSDT", np.nan)), 5),
                "ldo_d_acc": round(float(per_sym.get("LDOUSDT", np.nan)), 5),
                "trx_d_acc": round(float(per_sym.get("TRXUSDT", np.nan)), 5),
            }
        )
        print(
            f"  {d}: dACC mean={np.nanmean(d_acc):+.4f} CI=[{ci_lo:+.4f},{ci_hi:+.4f}]  "
            f"dPnL mean={np.nanmean(d_pnl):+.4f}  syms+={sign_consistent}/3  "
            f"[BCH {per_sym.get('BCHUSDT', np.nan):+.4f} "
            f"LDO {per_sym.get('LDOUSDT', np.nan):+.4f} "
            f"TRX {per_sym.get('TRXUSDT', np.nan):+.4f}]"
        )
    pd.DataFrame(summary).to_csv(OUT / "T3_horse_race_summary.csv", index=False)
    print(f"\nWROTE {OUT / 'T3_horse_race_summary.csv'}")
    print("\nREAD: a design is a candidate axis if dACC mean > 0 AND sign-")
    print("consistent across >=2 symbols. CI straddling zero => the held-out")
    print("proxy is inconclusive (NOT a kill) — the backtest resolves it.")


if __name__ == "__main__":
    main()

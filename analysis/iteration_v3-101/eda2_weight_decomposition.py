"""iter-v3/101 EDA #2 — what is the v3 magnitude weight actually weighting?

EDA #1 ANGLE B exposed a per-symbol split: on BCH the labeled side wins only
57.7% of the time (a genuine noisy barrier label), but on LDO/TRX it wins
98.5-99.2% with a large mean labeled PnL (+11 / +7). Hypothesis: the current
`|net PnL|`->[1,10] sample weight is dominated by the ATR-scaled TP DISTANCE
(a volatility proxy), not by predictive edge. This EDA decomposes the weight.

Three angles:
  C. weight-vs-volatility correlation: corr(weight, ATR) and corr(weight,
     |fwd-return|). If high, the weight is a vol proxy, not an edge proxy.
  D. weight-vs-directional-difficulty: does a high magnitude weight coincide
     with candles a model finds EASIER to call (a held-out-fold proxy)?
  E. the candidate re-weighting schemes' raw shape — uniqueness (EDA#1 showed
     ~flat 0.046), edge-floor (zero out edge-free), and a volatility-NEUTRAL
     re-weight (rank-based).

STRICT IS-ONLY: open_time < OOS_CUTOFF_MS = 1742774400000.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.strategies.ml.labeling import label_trades  # noqa: E402

OOS_CUTOFF_MS = 1742774400000
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA = REPO / "data" / "features_v3"
OUT = Path(__file__).resolve().parent
ATR_TP, ATR_SL, TIMEOUT_MIN, ATR_COL, FEE_PCT = 2.0, 1.0, 10080, "natr_21_raw", 0.1

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


def main() -> None:
    print("=" * 78)
    print("iter-v3/101 EDA #2 — magnitude-weight decomposition")
    print("=" * 78)
    rows: list[dict] = []

    print("\n=== ANGLE C — is the weight a VOLATILITY proxy or an EDGE proxy? ===")
    for sym in SYMBOLS:
        df = load_is(sym)
        lab, w, lp, sp = make_labels(df)
        atr = df[ATR_COL].to_numpy(np.float64)
        # fwd 21-candle return magnitude
        close = df["close"].to_numpy(np.float64)
        n = len(close)
        fwd = np.full(n, np.nan)
        for i in range(n - 21):
            fwd[i] = abs((close[i + 21] - close[i]) / close[i] * 100.0)
        labeled_pnl = np.where(lab == 1, lp, sp)
        m = ~np.isnan(w) & ~np.isnan(atr) & ~np.isnan(fwd) & ~np.isnan(labeled_pnl)
        # rank-correlations
        r_atr = spearmanr(w[m], atr[m]).statistic
        r_fwd = spearmanr(w[m], fwd[m]).statistic
        # winner = labeled side's barrier PnL > 0 (directional correctness proxy)
        winner = (labeled_pnl[m] > 0).astype(float)
        r_win = spearmanr(w[m], winner).statistic
        rows.append(
            {
                "angle": "C_weight_decomp",
                "symbol": sym,
                "corr_weight_atr": round(float(r_atr), 4),
                "corr_weight_fwdret": round(float(r_fwd), 4),
                "corr_weight_winner": round(float(r_win), 4),
                "labeled_win_rate": round(float(winner.mean()), 4),
            }
        )
        print(
            f"  {sym}: corr(w,ATR)={r_atr:+.3f}  corr(w,|fwdret|)={r_fwd:+.3f}  "
            f"corr(w,winner)={r_win:+.3f}  labeled-win-rate={winner.mean():.3f}"
        )
    print("  READ: corr(w,ATR) high + corr(w,winner) low => the weight is a")
    print("  VOLATILITY proxy. A weight that up-weights volatile candles biases")
    print("  the model toward high-vol regimes, NOT toward edge-bearing candles.")

    print("\n=== ANGLE D — candidate re-weighting schemes (raw shape) ===")
    print("  Three designs, IS-only diagnostic of their dispersion:")
    print("    W0 baseline   = |net PnL| -> [1,10]            (current /059)")
    print("    W1 vol-neutral= cross-sectional RANK of W0      (kills ATR scaling)")
    print("    W2 edge-floor = W0 but 0 where best_edge<=0     (drop edge-free)")
    print("    W3 confidence = W0 * |2*p_calib - 1| proxy via barrier asymmetry")
    for sym in SYMBOLS:
        df = load_is(sym)
        lab, w, lp, sp = make_labels(df)
        be = np.maximum(lp, sp)
        m = ~np.isnan(w)
        w0 = w[m]
        # W1: rank-normalized -> uniform [1,10], removes the ATR-magnitude tilt
        ranks = pd.Series(w0).rank(pct=True).to_numpy()
        w1 = 1.0 + ranks * 9.0
        # W2: edge-floor
        w2 = w0.copy()
        w2[be[m] <= 0] = 0.0
        edge_free_frac = float((be[m] <= 0).mean())
        rows.append(
            {
                "angle": "D_reweight_shape",
                "symbol": sym,
                "W0_cv": round(float(w0.std() / w0.mean()), 3),
                "W1_cv": round(float(w1.std() / w1.mean()), 3),
                "W2_zeroed_frac": round(edge_free_frac, 4),
                "W0_top_decile_mass": round(
                    float(np.sort(w0)[-len(w0) // 10 :].sum() / w0.sum()), 4
                ),
            }
        )
        top_mass = np.sort(w0)[-len(w0) // 10 :].sum() / w0.sum() * 100
        print(
            f"  {sym}: W0-CV={w0.std() / w0.mean():.3f}  "
            f"W1-CV={w1.std() / w1.mean():.3f}  "
            f"W2 zeroes {edge_free_frac * 100:.1f}% of candles  "
            f"W0 top-decile holds {top_mass:.1f}% of weight mass"
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "T2_weight_decomposition.csv", index=False)
    print(f"\nWROTE {OUT / 'T2_weight_decomposition.csv'}")


if __name__ == "__main__":
    main()

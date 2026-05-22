"""iter-v3/106 EDA script 3 — deep characterization of the IS loss structure.

EDA 2 falsified the user's literal hypothesis at the MONTH level: a trailing
Mahalanobis OOD distance does NOT separate loss months from profit months
(AUC 0.559). Neither does BTC drawdown, BTC vol-z, ATR percentile, or Hurst.

This script goes deeper, asking three sharper questions, ALL strictly IS-only
and strictly causal:

  Q1 — Is the loss structure better seen at the TRADE level than the month
       level? Month aggregation can hide a clean trade-level separator. For
       every IS trade, compute the same OOD distance + regime features at the
       trade's ENTRY bar (causal: reference = trailing 24-month window ending
       at entry; the trade's own bar is the test point) and ask whether
       LOSING trades are OOD-distinguishable from WINNING trades.

  Q2 — Do the losses CLUSTER in time? The user's intuition "the model needs to
       stop" is really a statement about a STATEFUL drawdown signal: if losses
       arrive in runs, a trailing-equity drawdown detector (a NEW mechanism vs
       the closed BTC-regime kill switch and the closed per-symbol brake) can
       stop the book during the run. Measure: the run-length distribution of
       consecutive losing trades, and how concentrated the IS drag is inside
       drawdown episodes of the per-symbol trailing equity curve.

  Q3 — Is there a PER-SYMBOL × DIRECTION structure? /047 already found BCH LONG
       is toxic. Re-check on the /059 roster whether the loss months are a
       particular (symbol, direction) cell concentrating — and whether a
       trailing per-(symbol,direction) hit-rate is a cleaner stop signal than
       any regime variable.

The output drives the EDA 4 detector design — we let the data pick the
mechanism rather than forcing the month-level OOD framing that Q-EDA-2 killed.

NO CHEATING — IS-only, causal. The OOD reference window for a trade entering at
time t ends at t (24 months back); t's own bar is scored against a reference
that excludes it. No post-cutoff data is read.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS

OUT_DIR = "analysis/iteration_v3-106"
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
TRAINING_MONTHS = 24
TRADES_CSV = "reports-v3/iteration_v3-059/in_sample/trades.csv"


def load_features(symbol: str) -> pd.DataFrame:
    # NOTE: the /059 trade CSV's `open_time` equals the feature parquet's
    # `close_time` (the entry candle's CLOSE — the bar the model decided on).
    # We index features by close_time so a trade entering at T is matched to
    # the feature row that CLOSED at T. This is causal: the model only ever
    # sees completed candles.
    cols = [
        "open_time",
        "close_time",
        "atr_pct_rank_200",
        "hurst_100",
        "range_realized_vol_50",
        *V3_FEATURE_COLUMNS,
    ]
    cols = list(dict.fromkeys(cols))
    df = pq.read_table(f"data/features_v3/{symbol}_8h_features.parquet", columns=cols).to_pandas()
    return df.sort_values("close_time").reset_index(drop=True)


def trade_entry_mahalanobis(feats: dict[str, pd.DataFrame], df_trades: pd.DataFrame) -> np.ndarray:
    """Per-trade Mahalanobis distance of the ENTRY bar's feature vector vs the
    trailing 24-month per-symbol training window. Causal by construction:
    the trade's `open_time` is the entry candle's close_time; the reference
    window is all feature bars that CLOSED strictly before it."""
    out = np.full(len(df_trades), np.nan)
    fcols = list(V3_FEATURE_COLUMNS)
    for i, (_, tr) in enumerate(df_trades.iterrows()):
        sym = tr["symbol"]
        t = int(tr["open_time"])  # == entry candle close_time
        df = feats[sym]
        entry_dt = pd.to_datetime(t, unit="ms")
        train_start = int((entry_dt - pd.DateOffset(months=TRAINING_MONTHS)).value // 1_000_000)
        ref = df[(df["close_time"] >= train_start) & (df["close_time"] < t)]
        row = df[df["close_time"] == t]
        if len(ref) < 100 or len(row) == 0:
            continue
        X = ref[fcols].to_numpy()
        X = X[~np.isnan(X).any(axis=1)]
        x = row[fcols].to_numpy()[0]
        if len(X) < 100 or np.isnan(x).any():
            continue
        mu = X.mean(axis=0)
        cov = np.cov(X, rowvar=False)
        cov = cov + 1e-6 * np.mean(np.diag(cov)) * np.eye(cov.shape[0])
        try:
            inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            continue
        d = x - mu
        d2 = float(d @ inv @ d)
        out[i] = np.sqrt(d2) if d2 >= 0 else np.nan
    return out


def main() -> None:
    df = pd.read_csv(TRADES_CSV)
    assert (df["open_time"] < OOS_CUTOFF_MS).all(), "IS-only invariant violated"
    df = df.sort_values("open_time").reset_index(drop=True)
    df["is_win"] = df["net_pnl_pct"] > 0
    feats = {s: load_features(s) for s in SYMBOLS}

    print("=" * 84)
    print("iter-v3/106 EDA 3 — DEEP IS LOSS-STRUCTURE CHARACTERIZATION")
    print("=" * 84)

    # ------------------------------------------------------------------
    # Q1 — trade-level OOD: do losing trades have higher entry-bar OOD?
    # ------------------------------------------------------------------
    df["entry_maha"] = trade_entry_mahalanobis(feats, df)
    ok = df["entry_maha"].notna()
    win = df.loc[ok & df["is_win"], "entry_maha"].to_numpy()
    lose = df.loc[ok & ~df["is_win"], "entry_maha"].to_numpy()
    wins_pairs = sum((a > b) + 0.5 * (a == b) for a in lose for b in win)
    auc_trade = wins_pairs / (len(lose) * len(win)) if len(lose) and len(win) else np.nan
    print()
    print("Q1 — TRADE-LEVEL entry-bar Mahalanobis OOD (loser vs winner)")
    print(f"  scored trades        : {ok.sum()} / {len(df)}")
    print(f"  mean OOD, losing     : {lose.mean():.4f}  (n={len(lose)})")
    print(f"  mean OOD, winning    : {win.mean():.4f}  (n={len(win)})")
    print(f"  AUC (loser ranks high): {auc_trade:.3f}   [>0.60 would be usable]")
    # Also: do high-OOD trades have a worse weighted_pnl?
    q = df.loc[ok].copy()
    q["ood_quartile"] = pd.qcut(q["entry_maha"], 4, labels=["Q1_low", "Q2", "Q3", "Q4_high"])
    print("  weighted_pnl by entry-OOD quartile:")
    qt = q.groupby("ood_quartile", observed=True).agg(
        n=("weighted_pnl", "size"),
        wpnl_sum=("weighted_pnl", "sum"),
        wpnl_mean=("weighted_pnl", "mean"),
        win_rate=("is_win", "mean"),
    )
    print(qt.to_string(float_format=lambda x: f"{x:.4f}"))
    qt.to_csv(f"{OUT_DIR}/T4_trade_ood_quartiles.csv")

    # ------------------------------------------------------------------
    # Q2 — temporal clustering: consecutive losing-trade runs + drawdown
    # ------------------------------------------------------------------
    print()
    print("Q2 — TEMPORAL CLUSTERING of losses (portfolio trade stream)")
    seq = (~df["is_win"]).astype(int).to_numpy()  # 1 = loss
    runs, cur = [], 0
    for x in seq:
        if x:
            cur += 1
        else:
            if cur:
                runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    runs = np.array(runs)
    print(f"  losing-run length distribution: max={runs.max()}  mean={runs.mean():.2f}")
    for L in (1, 2, 3, 4, 5):
        print(f"    runs of length >= {L}: {(runs >= L).sum()}")
    # Trailing equity drawdown — the STATEFUL signal a trailing-DD brake would key on.
    df["cum_wpnl"] = df["weighted_pnl"].cumsum()
    df["running_peak"] = df["cum_wpnl"].cummax()
    df["dd_from_peak"] = df["running_peak"] - df["cum_wpnl"]
    print(f"  portfolio trailing-equity max drawdown (wpnl units): {df['dd_from_peak'].max():.2f}")
    # Where does the drag live: trades opened while ALREADY in a drawdown > X
    for thr in (3.0, 5.0, 8.0, 10.0):
        in_dd = df["dd_from_peak"].shift(1).fillna(0.0) >= thr  # past-only: DD known before this trade
        seg = df.loc[in_dd]
        print(
            f"  trades entered while trailing-DD(prev) >= {thr:>4.1f}: "
            f"n={len(seg):>3}  wpnl_sum={seg['weighted_pnl'].sum():+7.2f}  "
            f"win_rate={seg['is_win'].mean() if len(seg) else float('nan'):.3f}"
        )

    # ------------------------------------------------------------------
    # Q3 — per-(symbol, direction) cell + trailing per-cell hit-rate
    # ------------------------------------------------------------------
    print()
    print("Q3 — PER-(SYMBOL, DIRECTION) loss concentration")
    cell = df.groupby(["symbol", "direction"]).agg(
        n=("weighted_pnl", "size"),
        wpnl_sum=("weighted_pnl", "sum"),
        win_rate=("is_win", "mean"),
    )
    print(cell.to_string(float_format=lambda x: f"{x:.4f}"))
    cell.to_csv(f"{OUT_DIR}/T5_symbol_direction_cells.csv")

    # Trailing per-symbol hit-rate state: for each trade, the win-rate of the
    # last K closed trades of THE SAME SYMBOL (causal — only trades with
    # close_time < this trade's open_time). Then ask whether a low trailing
    # hit-rate predicts the next trade losing.
    print()
    print("Q3b — TRAILING per-symbol hit-rate state vs next-trade outcome")
    for K in (3, 5, 8):
        preds, outs = [], []
        for sym in SYMBOLS:
            s = df[df["symbol"] == sym].sort_values("open_time").reset_index(drop=True)
            for i in range(len(s)):
                t_open = s.loc[i, "open_time"]
                prior = s[s["close_time"] < t_open]
                if len(prior) < K:
                    continue
                hr = prior["is_win"].tail(K).mean()
                preds.append(hr)
                outs.append(bool(s.loc[i, "is_win"]))
        preds, outs = np.array(preds), np.array(outs)
        if len(preds) == 0:
            continue
        # AUC: does a LOW trailing hit-rate rank next-losers high? Use (1-hr).
        lo = (1 - preds)[~outs]  # next-trade loser
        hi = (1 - preds)[outs]  # next-trade winner
        auc = (
            sum((a > b) + 0.5 * (a == b) for a in lo for b in hi) / (len(lo) * len(hi))
            if len(lo) and len(hi)
            else np.nan
        )
        # Outcome split at trailing-hit-rate <= 1/K (i.e. <=1 win in last K) vs higher.
        cold = preds <= (1.0 / K + 1e-9)
        print(
            f"  K={K}: scored={len(preds):>3}  "
            f"AUC(low-hr ranks next-loser high)={auc:.3f}  | "
            f"next-trade win-rate when trailing-hr<=1/{K}: "
            f"{outs[cold].mean() if cold.any() else float('nan'):.3f} (n={cold.sum()})  "
            f"vs trailing-hr>1/{K}: {outs[~cold].mean() if (~cold).any() else float('nan'):.3f} "
            f"(n={(~cold).sum()})"
        )

    df[["symbol", "direction", "open_time", "close_time", "net_pnl_pct", "weighted_pnl",
        "is_win", "entry_maha", "cum_wpnl", "dd_from_peak"]].to_csv(
        f"{OUT_DIR}/T6_trade_level_state.csv", index=False
    )
    print()
    print(f"Wrote {OUT_DIR}/T4_trade_ood_quartiles.csv")
    print(f"Wrote {OUT_DIR}/T5_symbol_direction_cells.csv")
    print(f"Wrote {OUT_DIR}/T6_trade_level_state.csv  ({len(df)} rows)")


if __name__ == "__main__":
    main()

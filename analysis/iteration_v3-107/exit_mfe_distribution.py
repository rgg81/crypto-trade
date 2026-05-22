"""iter-v3/107 gating-EDA script 1 — losing-trade MFE distribution.

DECISIVE TEST 1 of 2. NO model retrain.

For every losing trade in the /059-baseline IS roster, walk the 8h OHLCV path
bar-by-bar from entry candle to exit candle and measure the Maximum Favorable
Excursion (MFE) — peak unrealized profit in ATR units — before the trade
reversed to a loss.

Thesis under test: a static 1-ATR stop books a full loss on a trade that ran,
say, +1.8 ATR favorable then reversed. A trailing stop would have captured
that. If losers DO run favorable first, a trailing stop can convert losers
into scratches/wins. If losers go straight to the stop, no exit re-architecture
can help.

ATR-at-entry is recovered from the barrier geometry the runner wrote:
the SL price is placed exactly 1.0 ATR from entry (V3 atr_sl=1.0), so
    atr_entry = |entry_price - stop_loss_price| / 1.0
and the TP is 2.0 ATR away (atr_tp=2.0) — used as a cross-check.

NO CHEATING: IS-only. Every trade asserted open_time < OOS_CUTOFF_MS. The
/059 IS roster (reports-v3/iteration_v3-059/in_sample/trades.csv) is itself
the IS split; the assertion is a belt-and-braces guard. OHLCV bars are read
only up to each trade's own close_time — no post-exit, no post-cutoff data.
"""

from __future__ import annotations

import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — config.py
ATR_SL_MULT = 1.0  # V3 atr_sl — barrier geometry
ATR_TP_MULT = 2.0  # V3 atr_tp — barrier geometry
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
TRADES_CSV = "reports-v3/iteration_v3-059/in_sample/trades.csv"


def load_ohlcv(symbol: str) -> pd.DataFrame:
    df = pd.read_csv(f"data/{symbol}/8h.csv")
    return df[["open_time", "open", "high", "low", "close", "close_time"]].sort_values(
        "open_time"
    ).reset_index(drop=True)


def walk_trade(ohlcv: pd.DataFrame, row: pd.Series) -> dict:
    """Walk the 8h path from entry to exit; return excursions in ATR units.

    MFE  = peak favorable excursion (ATR units), CAUSAL — computed bar-by-bar.
    MAE  = peak adverse excursion (ATR units).
    All measured on the SAME bars the trade was actually open for
    (open_time inclusive .. close_time inclusive).
    """
    entry = float(row["entry_price"])
    sl = float(row["stop_loss_price"])
    direction = int(row["direction"])  # +1 long, -1 short
    atr_entry = abs(entry - sl) / ATR_SL_MULT
    if atr_entry <= 0:
        return {"atr_entry": 0.0, "mfe_atr": 0.0, "mae_atr": 0.0, "n_bars": 0}

    path = ohlcv[
        (ohlcv["open_time"] >= row["open_time"])
        & (ohlcv["open_time"] <= row["close_time"])
    ]
    if path.empty:
        return {"atr_entry": atr_entry, "mfe_atr": 0.0, "mae_atr": 0.0, "n_bars": 0}

    if direction == 1:
        best = (path["high"].max() - entry) / atr_entry  # favorable = up
        worst = (path["low"].min() - entry) / atr_entry  # adverse  = down
        mae = -worst
    else:
        best = (entry - path["low"].min()) / atr_entry  # favorable = down
        worst = (entry - path["high"].max()) / atr_entry  # adverse = up
        mae = -worst

    return {
        "atr_entry": atr_entry,
        "mfe_atr": float(best),
        "mae_atr": float(mae),
        "n_bars": int(len(path)),
    }


def main() -> None:
    trades = pd.read_csv(TRADES_CSV)
    assert (trades["open_time"] < OOS_CUTOFF_MS).all(), "IS-only invariant violated"
    print(f"Loaded {len(trades)} /059 IS trades; IS-only invariant OK")

    ohlcv = {s: load_ohlcv(s) for s in SYMBOLS}
    recs = []
    for _, row in trades.iterrows():
        w = walk_trade(ohlcv[row["symbol"]], row)
        recs.append({
            "symbol": row["symbol"],
            "direction": int(row["direction"]),
            "exit_reason": row["exit_reason"],
            "net_pnl_pct": float(row["net_pnl_pct"]),
            "is_winner": float(row["net_pnl_pct"]) > 0,
            **w,
        })
    df = pd.DataFrame(recs)
    df.to_csv("analysis/iteration_v3-107/T1_per_trade_excursions.csv", index=False)

    losers = df[~df["is_winner"]].copy()
    winners = df[df["is_winner"]].copy()

    # ---- T2: losing-trade MFE distribution -------------------------------
    print("\n=== T2: LOSING-TRADE MFE DISTRIBUTION (peak favorable, ATR units) ===")
    print(f"  N losers = {len(losers)}  (winners = {len(winners)})")
    q = losers["mfe_atr"].quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    print(f"  MFE mean   = {losers['mfe_atr'].mean():.3f} ATR")
    print(f"  MFE median = {losers['mfe_atr'].median():.3f} ATR")
    for p, v in q.items():
        print(f"  MFE p{int(p * 100):02d}    = {v:.3f} ATR")

    # how many losers ran past trailing-stop arm thresholds before reversing
    print("\n  Losers reaching favorable thresholds before booking a loss:")
    rows = []
    for thr in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75):
        n = int((losers["mfe_atr"] >= thr).sum())
        pct = 100.0 * n / len(losers)
        print(f"    MFE >= {thr:.2f} ATR : {n:3d} / {len(losers)}  ({pct:5.1f}%)")
        rows.append({"mfe_threshold_atr": thr, "n_losers": n,
                     "pct_losers": round(pct, 1)})
    pd.DataFrame(rows).to_csv(
        "analysis/iteration_v3-107/T2_loser_mfe_thresholds.csv", index=False
    )

    losers.sort_values("mfe_atr", ascending=False).to_csv(
        "analysis/iteration_v3-107/T2b_loser_mfe_sorted.csv", index=False
    )

    # ---- T3: winners' MFE — to size a non-clipping trailing stop ---------
    print("\n=== T3: WINNER MFE DISTRIBUTION (to avoid clipping winners) ===")
    qw = winners["mfe_atr"].quantile([0.10, 0.25, 0.50])
    print(f"  Winner MFE mean = {winners['mfe_atr'].mean():.3f} ATR")
    for p, v in qw.items():
        print(f"  Winner MFE p{int(p * 100):02d} = {v:.3f} ATR")
    # winners that only briefly dipped — trailing-stop giveback budget
    print(f"  Winner MAE mean = {winners['mae_atr'].mean():.3f} ATR")
    print(f"  Winner MAE p75  = {winners['mae_atr'].quantile(0.75):.3f} ATR")

    # ---- T4: per-symbol loser MFE ---------------------------------------
    print("\n=== T4: PER-SYMBOL LOSER MFE ===")
    per = losers.groupby("symbol").agg(
        n_losers=("mfe_atr", "size"),
        mfe_mean=("mfe_atr", "mean"),
        mfe_median=("mfe_atr", "median"),
        frac_mfe_ge_1=("mfe_atr", lambda s: (s >= 1.0).mean()),
    ).round(3)
    print(per.to_string())
    per.to_csv("analysis/iteration_v3-107/T4_per_symbol_loser_mfe.csv")

    # ---- ATR-geometry cross-check ---------------------------------------
    tp_trades = df[df["exit_reason"] == "take_profit"]
    print("\n=== ATR-geometry cross-check (TP trades should show MFE ~ 2.0) ===")
    print(f"  TP-trade MFE mean = {tp_trades['mfe_atr'].mean():.3f} ATR "
          f"(expected ~{ATR_TP_MULT}); N={len(tp_trades)}")
    sl_trades = df[df["exit_reason"] == "stop_loss"]
    print(f"  SL-trade MAE mean = {sl_trades['mae_atr'].mean():.3f} ATR "
          f"(expected ~{ATR_SL_MULT}); N={len(sl_trades)}")


if __name__ == "__main__":
    main()

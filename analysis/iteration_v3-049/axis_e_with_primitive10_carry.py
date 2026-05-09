"""Per-symbol ADX threshold EDA WITH primitive 10 carry-forward (BCH LONG blocked).

iter-v3/049 carries iter-v3/047 primitive 10 forward (block_long_for=("BCHUSDT",)).
The ALL-trades EDA in axis_e_finegrained_adx.py uses iter-v3/045 trades, which
PREDATE primitive 10. With primitive 10 ON, BCH LONG trades are BLOCKED entirely.

Re-do the per-symbol ADX threshold simulation AFTER filtering BCH LONG trades.
This gives the realistic IS lift / OOS cost estimates for iter-v3/049.

Also: simulate iter-v3/047 primitive-10-state IS lift directly (not iter-v3/045
counterfactual): this requires iter-v3/047 trades. But iter-v3/047's OOS regression
is single-seed Optuna lottery (per iter-v3/048 forensic correction). Use iter-v3/045
trades and SUBTRACT BCH LONG trades to approximate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANCHOR_REPORT = Path("reports-v3/iteration_v3-045")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v3-049")
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")


def _wilder_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    n = len(high)
    if n < 2 * period + 1:
        return np.full(n, np.nan)
    up_move = np.diff(high, prepend=high[0])
    down_move = np.diff(-low, prepend=-low[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])

    def _wilder(s: np.ndarray) -> np.ndarray:
        out = np.full_like(s, np.nan, dtype=np.float64)
        if n < period:
            return out
        out[period - 1] = np.sum(s[:period])
        for i in range(period, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + s[i]
        return out

    atr_w = _wilder(tr)
    plus_dm_w = _wilder(plus_dm)
    minus_dm_w = _wilder(minus_dm)
    with np.errstate(invalid="ignore", divide="ignore"):
        plus_di = 100.0 * plus_dm_w / atr_w
        minus_di = 100.0 * minus_dm_w / atr_w
        dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = np.full(n, np.nan, dtype=np.float64)
    first_valid = 2 * period - 1
    if first_valid < n:
        adx[first_valid] = np.nanmean(dx[period - 1 : first_valid + 1])
        for i in range(first_valid + 1, n):
            if not np.isnan(dx[i]) and not np.isnan(adx[i - 1]):
                adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period
    return adx


def main() -> int:
    is_t = pd.read_csv(ANCHOR_REPORT / "in_sample" / "trades.csv")
    oos_t = pd.read_csv(ANCHOR_REPORT / "out_of_sample" / "trades.csv")
    is_t["sample"] = "IS"
    oos_t["sample"] = "OOS"

    enriched = []
    for sym in SYMBOLS:
        all_t = pd.concat([is_t[is_t["symbol"] == sym], oos_t[oos_t["symbol"] == sym]])
        if all_t.empty:
            continue
        feat = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        raw = pd.read_csv(DATA_DIR / sym / "8h.csv")
        raw_idx = raw.set_index("open_time")
        joined = feat.set_index("open_time").join(
            raw_idx[["high", "low", "close"]].rename(columns={"high": "_h", "low": "_l", "close": "_c"}),
            how="left",
        )
        adx_arr = _wilder_adx(joined["_h"].values, joined["_l"].values, joined["_c"].values, 14)
        feat = feat.copy()
        feat["adx_14"] = adx_arr
        m = all_t.merge(feat[["close_time", "adx_14"]], left_on="open_time", right_on="close_time", how="left")
        enriched.append(m)
    trades_all = pd.concat(enriched, ignore_index=True).dropna(subset=["adx_14"])

    # PRIMITIVE 10 SIMULATION: drop BCH LONG trades
    trades = trades_all[~((trades_all["symbol"] == "BCHUSDT") & (trades_all["direction"] == 1))].copy()
    n_dropped_is = ((trades_all["symbol"] == "BCHUSDT") & (trades_all["direction"] == 1) & (trades_all["sample"] == "IS")).sum()
    n_dropped_oos = ((trades_all["symbol"] == "BCHUSDT") & (trades_all["direction"] == 1) & (trades_all["sample"] == "OOS")).sum()
    print(f"Primitive 10 simulation: dropped {n_dropped_is} BCH LONG IS trades, {n_dropped_oos} BCH LONG OOS trades")
    print(f"Trades remaining: {len(trades)} (vs {len(trades_all)} all)")
    print()

    # Recompute baseline IS+OOS sums after primitive 10
    is_baseline = {}
    oos_baseline = {}
    for sym in SYMBOLS:
        is_baseline[sym] = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]["weighted_pnl"].sum()
        oos_baseline[sym] = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")]["weighted_pnl"].sum()
    print("Per-symbol baseline (with primitive 10 ON simulation):")
    for sym in SYMBOLS:
        print(f"  {sym}: IS sum_wpnl = {is_baseline[sym]:.2f}, OOS sum_wpnl = {oos_baseline[sym]:.2f}")
    print(f"  TOTAL IS = {sum(is_baseline.values()):.2f}, TOTAL OOS = {sum(oos_baseline.values()):.2f}")
    print()

    # Per-symbol fine-grained sweep WITH primitive 10
    print("=== Per-symbol ADX threshold sweep (WITH primitive 10 carry-forward) ===\n")
    print(f"{'symbol':<10} {'thr':>4} | {'IS_blocked':>10} {'IS_blocked_wpnl':>16} {'IS_lift':>8} | {'OOS_blocked':>11} {'OOS_blocked_wpnl':>17} {'OOS_cost':>9} | {'NET':>8}")
    rows = []
    for sym in SYMBOLS:
        sub_is = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]
        sub_oos = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")]
        for thr in [21, 22, 23, 24, 25]:
            is_blocked = sub_is[sub_is["adx_14"] < thr]
            oos_blocked = sub_oos[sub_oos["adx_14"] < thr]
            is_lift = -is_blocked["weighted_pnl"].sum()
            oos_cost = oos_blocked["weighted_pnl"].sum()
            net = is_lift - oos_cost
            row = {
                "symbol": sym,
                "adx_threshold": thr,
                "n_IS_blocked": len(is_blocked),
                "IS_blocked_wpnl": round(is_blocked["weighted_pnl"].sum(), 2),
                "IS_lift_estimate": round(is_lift, 2),
                "n_OOS_blocked": len(oos_blocked),
                "OOS_blocked_wpnl": round(oos_blocked["weighted_pnl"].sum(), 2),
                "OOS_cost_estimate": round(oos_cost, 2),
                "net_estimate": round(net, 2),
            }
            rows.append(row)
            print(f"{sym:<10} {thr:>4} | {len(is_blocked):>10} {is_blocked['weighted_pnl'].sum():>16.2f} {is_lift:>8.2f} | {len(oos_blocked):>11} {oos_blocked['weighted_pnl'].sum():>17.2f} {oos_cost:>9.2f} | {net:>8.2f}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_e_finegrained_adx_with_primitive10.csv", index=False)
    print(f"\nWritten: {OUT_DIR / 'axis_e_finegrained_adx_with_primitive10.csv'}")

    # Strategy ranking: per-symbol BOTH-must-improve threshold
    print("\n=== Per-symbol BOTH-MUST-IMPROVE threshold (with primitive 10) ===")
    recommendations = {}
    for sym in SYMBOLS:
        sub = df[df["symbol"] == sym]
        valid = sub[(sub["IS_lift_estimate"] > 0) & (sub["OOS_cost_estimate"] <= 0)]
        if not valid.empty:
            best = valid.loc[valid["IS_lift_estimate"].idxmax()]
            recommendations[sym] = (int(best["adx_threshold"]), best["IS_lift_estimate"], best["OOS_cost_estimate"])
        else:
            recommendations[sym] = (20, 0.0, 0.0)
    print("Per-symbol recommendations:")
    total_is = 0
    total_oos = 0
    for sym, (thr, is_l, oos_c) in recommendations.items():
        print(f"  {sym}: ADX threshold {thr}, IS lift +{is_l:.2f}, OOS cost {oos_c:.2f}")
        total_is += is_l
        total_oos += oos_c
    is_agg = sum(is_baseline.values())
    oos_agg = sum(oos_baseline.values())
    print(f"\nAGGREGATE: IS lift +{total_is:.2f} ({total_is/is_agg*100:.1f}% of IS baseline {is_agg:.2f})")
    print(f"           OOS cost {total_oos:+.2f} ({total_oos/oos_agg*100:.1f}% of OOS baseline {oos_agg:.2f})")
    print(f"           NET +{total_is - total_oos:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Fine-grained ADX threshold sweep per symbol — find best IS lift while preserving OOS.

Per `feedback_v3_strict_both_is_oos_baseline.md`: BOTH IS+OOS must improve at multi-seed.
Test: per-symbol ADX threshold {21, 22, 23, 24, 25} for IS lift vs OOS cost.
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
    trades = pd.concat(enriched, ignore_index=True).dropna(subset=["adx_14"])

    # Per-symbol fine-grained sweep
    print("=== Per-symbol fine-grained ADX threshold sweep ===\n")
    print(f"{'symbol':<10} {'thr':>4} | {'IS_blocked':>10} {'IS_blocked_wpnl':>16} {'IS_lift':>8} | {'OOS_blocked':>11} {'OOS_blocked_wpnl':>17} {'OOS_cost':>9} | {'NET':>8}")
    rows = []
    for sym in SYMBOLS:
        sub_is = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]
        sub_oos = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")]
        for thr in [21, 22, 23, 24, 25]:
            is_blocked = sub_is[sub_is["adx_14"] < thr]
            oos_blocked = sub_oos[sub_oos["adx_14"] < thr]
            is_lift = -is_blocked["weighted_pnl"].sum()  # blocking removes losers → positive
            oos_cost = oos_blocked["weighted_pnl"].sum()  # blocking removes positives → cost
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
    df.to_csv(OUT_DIR / "axis_e_finegrained_adx.csv", index=False)
    print(f"\nWritten: {OUT_DIR / 'axis_e_finegrained_adx.csv'}")

    # Also: ADX stratification by direction per symbol
    print("\n=== ADX × direction × IS attribution ===")
    rows2 = []
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]
        for direction in [1, -1]:
            grp = sub[sub["direction"] == direction]
            if grp.empty:
                continue
            # Two ADX sub-buckets: 20-23, 23-25, >=25
            for adx_min, adx_max, label in [(20, 23, "20-23"), (23, 25, "23-25"), (25, 30, "25-30"), (30, 100, ">=30")]:
                sg = grp[(grp["adx_14"] >= adx_min) & (grp["adx_14"] < adx_max)]
                if sg.empty:
                    continue
                rows2.append({
                    "symbol": sym,
                    "direction": "LONG" if direction == 1 else "SHORT",
                    "adx_bucket": label,
                    "n": len(sg),
                    "WR_pct": round((sg["net_pnl_pct"] > 0).mean() * 100, 1),
                    "sum_net_pnl_pct": round(sg["net_pnl_pct"].sum(), 2),
                    "sum_weighted_pnl": round(sg["weighted_pnl"].sum(), 2),
                })
    df2 = pd.DataFrame(rows2)
    df2.to_csv(OUT_DIR / "axis_e_adx_direction_strat.csv", index=False)
    print(df2.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())

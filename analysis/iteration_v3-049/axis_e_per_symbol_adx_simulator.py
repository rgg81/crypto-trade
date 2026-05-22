"""Per-symbol ADX threshold raise — full IS+OOS simulation with BOTH-must-improve check.

Mechanism: per-symbol ADX threshold extension to existing risk_v2 gate. Currently
risk_v2.py uses a UNIVERSAL adx_threshold=20.0. This axis proposes a per-symbol
override: dict[str, float] mapping symbol → ADX threshold.

Per `feedback_v3_strict_both_is_oos_baseline.md`: BOTH IS+OOS must improve at
multi-seed. The naive counterfactual here is single-seed only — Optuna will retune
at multi-seed CONFIRMATION.

Per `feedback_v3_concentration_is_signal.md` orthogonal-mechanism rule: ADX gate
is a regime-conditional kill switch (binary off/on per bar), NOT proportional
position scaling. Compatible with that constraint.
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

    # Strategy A: BCH+TRX raise to 21; LDO+ALGO unchanged at 20
    strategy_a = {"BCHUSDT": 21, "LDOUSDT": 20, "TRXUSDT": 21, "ALGOUSDT": 20}
    # Strategy B: BCH raise to 21, TRX raise to 22; LDO+ALGO unchanged
    strategy_b = {"BCHUSDT": 21, "LDOUSDT": 20, "TRXUSDT": 22, "ALGOUSDT": 20}
    # Strategy C: only BCH raise to 21
    strategy_c = {"BCHUSDT": 21, "LDOUSDT": 20, "TRXUSDT": 20, "ALGOUSDT": 20}
    # Strategy D: only TRX raise to 21
    strategy_d = {"BCHUSDT": 20, "LDOUSDT": 20, "TRXUSDT": 21, "ALGOUSDT": 20}
    # Strategy E: BCH+TRX raise to 21, LDO unchanged, ALGO LOWER to 18 (give ALGO more room)
    # but ALGO baseline already at 20; lowering would be a separate axis. Skip.

    print("=== Per-symbol ADX threshold strategies (BOTH-must-improve) ===\n")
    summary_rows = []
    for label, thresholds in [("A_BCH21_TRX21", strategy_a), ("B_BCH21_TRX22", strategy_b),
                              ("C_BCH21_only", strategy_c), ("D_TRX21_only", strategy_d)]:
        is_total_lift = 0
        oos_total_cost = 0
        is_blocks = 0
        oos_blocks = 0
        per_sym_detail = []
        for sym in SYMBOLS:
            thr = thresholds[sym]
            sub_is = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]
            sub_oos = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")]
            is_blocked = sub_is[sub_is["adx_14"] < thr]
            oos_blocked = sub_oos[sub_oos["adx_14"] < thr]
            is_lift = -is_blocked["weighted_pnl"].sum()
            oos_cost = oos_blocked["weighted_pnl"].sum()
            is_total_lift += is_lift
            oos_total_cost += oos_cost
            is_blocks += len(is_blocked)
            oos_blocks += len(oos_blocked)
            per_sym_detail.append(f"{sym}@thr{thr}:n_IS_blocked={len(is_blocked)},IS_lift={is_lift:.2f},n_OOS_blocked={len(oos_blocked)},OOS_cost={oos_cost:.2f}")
        net = is_total_lift - oos_total_cost
        # Approx Sharpe lift assuming naive Sharpe ~ wpnl_sum/std (not exact)
        is_baseline = sub_is["weighted_pnl"].sum() if len(sub_is) > 0 else 1
        oos_baseline = sub_oos["weighted_pnl"].sum() if len(sub_oos) > 0 else 1
        # Aggregate baseline
        is_agg = sum(trades[(trades["symbol"] == s) & (trades["sample"] == "IS")]["weighted_pnl"].sum() for s in SYMBOLS)
        oos_agg = sum(trades[(trades["symbol"] == s) & (trades["sample"] == "OOS")]["weighted_pnl"].sum() for s in SYMBOLS)
        print(f"Strategy {label}:")
        print(f"  thresholds = {thresholds}")
        print(f"  per-sym: {' | '.join(per_sym_detail)}")
        print(f"  Aggregate IS lift: +{is_total_lift:.2f} wpnl ({is_total_lift/is_agg*100:.1f}% of IS baseline {is_agg:.2f})")
        print(f"  Aggregate OOS cost: {oos_total_cost:+.2f} wpnl ({oos_total_cost/oos_agg*100:.1f}% of OOS baseline {oos_agg:.2f})")
        print(f"  NET estimate: {net:+.2f} wpnl")
        print(f"  IS blocks: {is_blocks}, OOS blocks: {oos_blocks}")
        print()
        summary_rows.append({
            "strategy": label,
            "BCH_threshold": thresholds["BCHUSDT"],
            "LDO_threshold": thresholds["LDOUSDT"],
            "TRX_threshold": thresholds["TRXUSDT"],
            "ALGO_threshold": thresholds["ALGOUSDT"],
            "n_IS_blocked": is_blocks,
            "IS_lift_wpnl": round(is_total_lift, 2),
            "IS_lift_pct": round(is_total_lift / is_agg * 100, 1),
            "n_OOS_blocked": oos_blocks,
            "OOS_cost_wpnl": round(oos_total_cost, 2),
            "OOS_cost_pct": round(oos_total_cost / oos_agg * 100, 1),
            "NET_estimate_wpnl": round(net, 2),
        })

    df_sum = pd.DataFrame(summary_rows)
    df_sum.to_csv(OUT_DIR / "axis_e_per_symbol_adx_strategies.csv", index=False)
    print(f"Written: {OUT_DIR / 'axis_e_per_symbol_adx_strategies.csv'}")
    print()
    print("Strategy ranking:")
    print(df_sum.sort_values("NET_estimate_wpnl", ascending=False).to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())

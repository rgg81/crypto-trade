"""Gate threshold robustness + OOS fire-rate projection — iter-v1/019 Phase 1 EDA.

Script 03 chose `I2_threshold_medium_>10%` (kill_large_counter_move) on IS lift
alone. This script checks:

1. **Threshold robustness**: how sensitive is the IS lift to the +-10% threshold?
   Sweep [3%, 5%, 8%, 10%, 12%, 15%, 18%, 20%, 25%] and report IS PnL lift +
   trade-rate. Plateau → robust. Spike → overfit-prone.

2. **OOS fire-rate projection** (sanity ONLY — does NOT influence threshold choice):
   apply each threshold to baseline OOS ETH trades and report what fire rate
   would be, so we can pre-register F8 OOS-trade-count band correctly.

3. **Cross-year IS stability**: split IS into half-windows (2022-2023, 2024-Q1+)
   and verify the chosen threshold's lift sign is stable in BOTH halves.
   If both halves agree → robust. Sign flip → overfit, choose more conservative.

Outputs (committed):
- gate_threshold_sweep.csv : IS + projected OOS at each threshold
- gate_cross_year_stability.csv : IS split-halves lift check
- gate_final_choice.csv : final recommended gate spec for brief Section 3
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports-v1"
OUT = ROOT / "analysis" / "iteration_v1-019"
OUT.mkdir(parents=True, exist_ok=True)

OOS_CUTOFF_MS = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)
IS_HALF_SPLIT_MS = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp() * 1000)


def load_btc_klines() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "BTCUSDT" / "8h.csv")
    df = df.sort_values("open_time").reset_index(drop=True)
    df["ret_14d"] = df["close"] / df["close"].shift(42) - 1.0
    return df


def attach_ret14(trades: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    out = trades.reset_index(drop=True).copy()
    btc_open = btc["open_time"].to_numpy(dtype=np.int64)
    btc_ret14 = btc["ret_14d"].to_numpy(dtype=np.float64)
    ret14_arr = np.empty(len(out), dtype=np.float64)
    for i, ot in enumerate(out["open_time"]):
        idx = int(np.searchsorted(btc_open, int(ot), side="right") - 1)
        if idx < 42 or np.isnan(btc_ret14[idx]):
            ret14_arr[i] = 0.0
        else:
            ret14_arr[i] = float(btc_ret14[idx])
    out["btc_ret14"] = ret14_arr
    return out


def gate_eval(trades: pd.DataFrame, threshold: float) -> dict:
    """Kill ETH longs when BTC_ret14 < -threshold, ETH shorts when BTC_ret14 > +threshold.

    Returns counts + lift.
    """
    kill = (
        ((trades["direction"] == 1) & (trades["btc_ret14"] < -threshold)) |
        ((trades["direction"] == -1) & (trades["btc_ret14"] > threshold))
    )
    baseline_pnl = float(trades["net_pnl_pct"].sum())
    gated_pnl = float(trades[~kill]["net_pnl_pct"].sum())
    return {
        "threshold_pct": float(threshold * 100),
        "n_total": len(trades),
        "n_killed": int(kill.sum()),
        "skip_pct": float(kill.mean() * 100),
        "baseline_pnl_pct": baseline_pnl,
        "gated_pnl_pct": gated_pnl,
        "lift_pct": gated_pnl - baseline_pnl,
    }


def main() -> None:
    btc = load_btc_klines()
    base_is = pd.read_csv(REPORTS / "iteration_v1-baseline" / "in_sample" / "trades.csv")
    base_oos = pd.read_csv(REPORTS / "iteration_v1-baseline" / "out_of_sample" / "trades.csv")
    eth_is = base_is[base_is["symbol"] == "ETHUSDT"].copy()
    eth_oos = base_oos[base_oos["symbol"] == "ETHUSDT"].copy()
    eth_is = attach_ret14(eth_is, btc)
    eth_oos = attach_ret14(eth_oos, btc)

    assert eth_is["open_time"].max() < OOS_CUTOFF_MS
    assert eth_oos["open_time"].min() >= OOS_CUTOFF_MS

    # --- Threshold sweep IS + OOS projection ---
    sweep_rows = []
    for thr in [0.03, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25]:
        is_stat = gate_eval(eth_is, thr)
        oos_stat = gate_eval(eth_oos, thr)
        sweep_rows.append({
            "threshold_pct": thr * 100,
            "is_skip_pct": is_stat["skip_pct"],
            "is_baseline_pnl": is_stat["baseline_pnl_pct"],
            "is_gated_pnl": is_stat["gated_pnl_pct"],
            "is_lift_pct": is_stat["lift_pct"],
            "is_n_killed": is_stat["n_killed"],
            "oos_skip_pct": oos_stat["skip_pct"],
            "oos_baseline_pnl": oos_stat["baseline_pnl_pct"],
            "oos_gated_pnl_PROJECTED": oos_stat["gated_pnl_pct"],
            "oos_lift_pct_PROJECTED": oos_stat["lift_pct"],
            "oos_n_killed": oos_stat["n_killed"],
        })
    sweep = pd.DataFrame(sweep_rows)
    sweep.to_csv(OUT / "gate_threshold_sweep.csv", index=False)
    print("=== Gate threshold sweep (IS lift + OOS projection) ===")
    print(sweep.to_string(index=False))
    print()
    print("NOTE: oos_* columns are PROJECTED — informational only. These come from")
    print("applying the gate as a post-hoc filter to baseline OOS ETH trades.")
    print("The actual /019 backtest will re-run from scratch with the gate; the")
    print("Optuna trajectory and signal generation will differ. The OOS PROJECTION")
    print("only sizes the F8 OOS trade-count band — it MUST NOT influence threshold")
    print("selection (which is on IS-lift only).")
    print()

    # --- Cross-year IS stability check at chosen threshold ---
    # Choose threshold using IS-only criterion: highest IS lift with skip < 25%
    # AND lift sign stable in BOTH IS-halves.
    eth_is_h1 = eth_is[eth_is["open_time"] < IS_HALF_SPLIT_MS].copy()
    eth_is_h2 = eth_is[eth_is["open_time"] >= IS_HALF_SPLIT_MS].copy()

    print(f"IS H1 (pre-2024): {len(eth_is_h1)} trades")
    print(f"IS H2 (2024+):    {len(eth_is_h2)} trades")

    stability_rows = []
    for thr in [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]:
        h1 = gate_eval(eth_is_h1, thr)
        h2 = gate_eval(eth_is_h2, thr)
        stability_rows.append({
            "threshold_pct": thr * 100,
            "h1_baseline_pnl": h1["baseline_pnl_pct"],
            "h1_gated_pnl": h1["gated_pnl_pct"],
            "h1_lift_pct": h1["lift_pct"],
            "h1_skip_pct": h1["skip_pct"],
            "h2_baseline_pnl": h2["baseline_pnl_pct"],
            "h2_gated_pnl": h2["gated_pnl_pct"],
            "h2_lift_pct": h2["lift_pct"],
            "h2_skip_pct": h2["skip_pct"],
            "both_halves_positive": (h1["lift_pct"] > 0) and (h2["lift_pct"] > 0),
        })
    stability = pd.DataFrame(stability_rows)
    stability.to_csv(OUT / "gate_cross_year_stability.csv", index=False)
    print("=== Cross-year IS stability check ===")
    print(stability.to_string(index=False))
    print()

    # Decision: threshold with both halves positive AND highest combined lift
    # AND IS skip <= 25%
    candidates = stability[stability["both_halves_positive"]].copy()
    if len(candidates) == 0:
        print("WARN: no threshold with both halves positive — fall back to highest IS lift")
        chosen_threshold_pct = float(stability.sort_values("h1_lift_pct", ascending=False).iloc[0]["threshold_pct"])
    else:
        # Add IS skip cap
        full_sweep_idx = sweep.set_index("threshold_pct")
        candidates["is_skip_pct"] = candidates["threshold_pct"].map(
            lambda t: float(full_sweep_idx.loc[t, "is_skip_pct"])
        )
        feasible = candidates[candidates["is_skip_pct"] <= 25.0]
        if len(feasible) == 0:
            chosen = candidates.iloc[0]
        else:
            # Highest combined lift among feasible
            feasible = feasible.assign(combined_lift=feasible["h1_lift_pct"] + feasible["h2_lift_pct"])
            chosen = feasible.sort_values("combined_lift", ascending=False).iloc[0]
        chosen_threshold_pct = float(chosen["threshold_pct"])

    print(f"=== Final chosen threshold: ±{chosen_threshold_pct:.0f}% ===")
    final_row = sweep[sweep["threshold_pct"] == chosen_threshold_pct].iloc[0]
    print(final_row.to_string())

    final_df = pd.DataFrame([{
        "indicator": "btc_ret_14d",
        "lookback_bars": 42,
        "lookback_days": 14,
        "threshold_pct": chosen_threshold_pct,
        "rule_long_kill": f"skip ETH long entry when BTC 14d return < -{chosen_threshold_pct:.0f}%",
        "rule_short_kill": f"skip ETH short entry when BTC 14d return > +{chosen_threshold_pct:.0f}%",
        "is_skip_pct": float(final_row["is_skip_pct"]),
        "is_baseline_pnl_pct": float(final_row["is_baseline_pnl"]),
        "is_gated_pnl_pct": float(final_row["is_gated_pnl"]),
        "is_lift_pct": float(final_row["is_lift_pct"]),
        "oos_skip_pct_PROJECTED": float(final_row["oos_skip_pct"]),
        "oos_lift_pct_PROJECTED": float(final_row["oos_lift_pct_PROJECTED"]),
    }])
    final_df.to_csv(OUT / "gate_final_choice.csv", index=False)
    print("\n=== Final gate spec for /019 brief Section 3 ===")
    print(final_df.to_string(index=False))


if __name__ == "__main__":
    main()

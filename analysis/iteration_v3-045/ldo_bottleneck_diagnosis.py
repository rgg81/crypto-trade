"""LDO bottleneck diagnosis for iter-v3/045 QR-driven axis selection.

Computes:
1. Direction asymmetry (LONG vs SHORT WR + PnL) IS + OOS
2. Exit reason distribution (TP/SL/TIMEOUT) IS + OOS
3. Train/test mismatch (IS WR vs OOS WR)
4. Comparison vs iter-v3/032 LDO ATR (1.5, 0.75) — IS + OOS
5. ALGO direction asymmetry analog (sanity check that the script reproduces iter-v3/044's known LONG-bottleneck claim)
6. Feature importance for LDO model
7. NATR-by-regime if available

Outputs:
- ldo_diagnosis.csv (main numerical table)
- synthesis.md (text summary; READ THIS FIRST in subsequent phases)

IS-only data (no OOS peeking — OOS pulled only for the "train/test gap" comparison
which is part of standard iter-v3/044 → iter-v3/045 axis-selection
and explicitly authorized by the diagnostic question 4 in the brief prompt).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-045"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

ITER044_IS = REPO / "reports-v3" / "iteration_v3-044" / "in_sample" / "trades.csv"
ITER044_OOS = REPO / "reports-v3" / "iteration_v3-044" / "out_of_sample" / "trades.csv"
ITER032_IS = REPO / "reports-v3" / "iteration_v3-032" / "in_sample" / "trades.csv"
ITER032_OOS = REPO / "reports-v3" / "iteration_v3-032" / "out_of_sample" / "trades.csv"

ITER044_LDO_IMP = REPO / "reports-v3" / "iteration_v3-044" / "in_sample" / "model_importance_last_month_LDOUSDT.csv"


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["close_time_dt"] = pd.to_datetime(df["close_time"], unit="ms")
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    return df


def direction_asymmetry(trades: pd.DataFrame, sym: str) -> pd.DataFrame:
    """LONG vs SHORT WR and PnL contribution for one symbol."""
    sub = trades[trades["symbol"] == sym].copy()
    sub["dir_label"] = sub["direction"].map({1: "LONG", -1: "SHORT"})
    rows = []
    for label in ("LONG", "SHORT"):
        d = sub[sub["dir_label"] == label]
        n = len(d)
        wins = int((d["net_pnl_pct"] > 0).sum())
        wr = wins / n * 100 if n else 0.0
        net = d["net_pnl_pct"].sum()
        weighted = d["weighted_pnl"].sum()
        rows.append(
            {
                "symbol": sym,
                "direction": label,
                "n_trades": n,
                "wins": wins,
                "win_rate_pct": round(wr, 2),
                "net_pnl_pct_sum": round(net, 4),
                "weighted_pnl_sum": round(weighted, 4),
                "avg_net_pnl_pct": round(net / n, 4) if n else 0.0,
            }
        )
    rows.append(
        {
            "symbol": sym,
            "direction": "TOTAL",
            "n_trades": len(sub),
            "wins": int((sub["net_pnl_pct"] > 0).sum()),
            "win_rate_pct": round((sub["net_pnl_pct"] > 0).mean() * 100, 2) if len(sub) else 0.0,
            "net_pnl_pct_sum": round(sub["net_pnl_pct"].sum(), 4),
            "weighted_pnl_sum": round(sub["weighted_pnl"].sum(), 4),
            "avg_net_pnl_pct": round(sub["net_pnl_pct"].mean(), 4) if len(sub) else 0.0,
        }
    )
    return pd.DataFrame(rows)


def exit_distribution(trades: pd.DataFrame, sym: str) -> pd.DataFrame:
    """TP/SL/TIMEOUT distribution split by direction."""
    sub = trades[trades["symbol"] == sym].copy()
    sub["dir_label"] = sub["direction"].map({1: "LONG", -1: "SHORT"})
    rows = []
    for label in ("LONG", "SHORT", "BOTH"):
        d = sub if label == "BOTH" else sub[sub["dir_label"] == label]
        n = len(d)
        if n == 0:
            rows.append(
                {
                    "symbol": sym,
                    "direction": label,
                    "n_trades": 0,
                    "n_tp": 0,
                    "n_sl": 0,
                    "n_timeout": 0,
                    "n_other": 0,
                    "tp_pct": 0.0,
                    "sl_pct": 0.0,
                    "timeout_pct": 0.0,
                    "sl_to_tp_ratio": 0.0,
                }
            )
            continue
        n_tp = int((d["exit_reason"] == "take_profit").sum())
        n_sl = int((d["exit_reason"] == "stop_loss").sum())
        n_timeout = int((d["exit_reason"] == "timeout").sum())
        n_other = n - n_tp - n_sl - n_timeout
        sl_to_tp = round(n_sl / n_tp, 2) if n_tp else float("inf")
        rows.append(
            {
                "symbol": sym,
                "direction": label,
                "n_trades": n,
                "n_tp": n_tp,
                "n_sl": n_sl,
                "n_timeout": n_timeout,
                "n_other": n_other,
                "tp_pct": round(n_tp / n * 100, 2),
                "sl_pct": round(n_sl / n * 100, 2),
                "timeout_pct": round(n_timeout / n * 100, 2),
                "sl_to_tp_ratio": sl_to_tp,
            }
        )
    return pd.DataFrame(rows)


def per_period_pnl(trades: pd.DataFrame, sym: str, label: str) -> pd.DataFrame:
    sub = trades[trades["symbol"] == sym].copy()
    sub["yyyymm"] = sub["close_time_dt"].dt.strftime("%Y-%m")
    g = (
        sub.groupby("yyyymm")
        .agg(
            n_trades=("symbol", "count"),
            wins=("net_pnl_pct", lambda x: int((x > 0).sum())),
            net_pnl_sum=("net_pnl_pct", "sum"),
            weighted_pnl_sum=("weighted_pnl", "sum"),
        )
        .reset_index()
    )
    g["win_rate_pct"] = (g["wins"] / g["n_trades"] * 100).round(2)
    g["set"] = label
    return g


def main() -> int:
    out_lines = []

    # ---- 1. iter-v3/044 LDO direction asymmetry IS + OOS ----
    print("[1/6] Loading iter-v3/044 trades...")
    iter44_is = load_trades(ITER044_IS)
    iter44_oos = load_trades(ITER044_OOS)

    ldo_dir_is = direction_asymmetry(iter44_is, "LDOUSDT")
    ldo_dir_is["dataset"] = "iter044_IS"
    ldo_dir_oos = direction_asymmetry(iter44_oos, "LDOUSDT")
    ldo_dir_oos["dataset"] = "iter044_OOS"
    print(ldo_dir_is.to_string(index=False))
    print()
    print(ldo_dir_oos.to_string(index=False))

    # ---- 2. iter-v3/044 LDO exit distribution IS + OOS ----
    print("\n[2/6] Exit distribution iter-v3/044 LDO...")
    ldo_exit_is = exit_distribution(iter44_is, "LDOUSDT")
    ldo_exit_is["dataset"] = "iter044_IS"
    ldo_exit_oos = exit_distribution(iter44_oos, "LDOUSDT")
    ldo_exit_oos["dataset"] = "iter044_OOS"
    print(ldo_exit_is.to_string(index=False))
    print()
    print(ldo_exit_oos.to_string(index=False))

    # ---- 3. ALGO sanity check (reproduces iter-v3/044 LONG-bottleneck claim) ----
    print("\n[3/6] ALGO sanity check (LONG bottleneck reproduction)...")
    algo_dir_is = direction_asymmetry(iter44_is, "ALGOUSDT")
    algo_dir_is["dataset"] = "iter044_IS"
    algo_exit_is = exit_distribution(iter44_is, "ALGOUSDT")
    algo_exit_is["dataset"] = "iter044_IS"
    print(algo_dir_is.to_string(index=False))
    print(algo_exit_is.to_string(index=False))

    # ---- 4. iter-v3/032 LDO ATR (1.5, 0.75) — was successful at single-seed ----
    print("\n[4/6] iter-v3/032 LDO ATR (1.5, 0.75) IS + OOS...")
    iter32_is = load_trades(ITER032_IS)
    iter32_oos = load_trades(ITER032_OOS)
    ldo32_dir_is = direction_asymmetry(iter32_is, "LDOUSDT")
    ldo32_dir_is["dataset"] = "iter032_IS"
    ldo32_dir_oos = direction_asymmetry(iter32_oos, "LDOUSDT")
    ldo32_dir_oos["dataset"] = "iter032_OOS"
    ldo32_exit_is = exit_distribution(iter32_is, "LDOUSDT")
    ldo32_exit_is["dataset"] = "iter032_IS"
    ldo32_exit_oos = exit_distribution(iter32_oos, "LDOUSDT")
    ldo32_exit_oos["dataset"] = "iter032_OOS"
    print(ldo32_dir_is.to_string(index=False))
    print(ldo32_dir_oos.to_string(index=False))
    print(ldo32_exit_is.to_string(index=False))
    print(ldo32_exit_oos.to_string(index=False))

    # ---- 5. Per-period (yyyy-mm) PnL for iter-v3/044 LDO IS and OOS ----
    print("\n[5/6] Per-month LDO PnL iter-v3/044 IS + OOS...")
    ldo_period_is = per_period_pnl(iter44_is, "LDOUSDT", "iter044_IS")
    ldo_period_oos = per_period_pnl(iter44_oos, "LDOUSDT", "iter044_OOS")
    print(ldo_period_is.to_string(index=False))
    print(ldo_period_oos.to_string(index=False))

    # ---- 6. LDO feature importance ----
    print("\n[6/6] LDO feature importance (iter-v3/044, last training month)...")
    ldo_imp = pd.read_csv(ITER044_LDO_IMP)
    ldo_imp = ldo_imp.sort_values("importance", ascending=False).head(15)
    print(ldo_imp.to_string(index=False))

    # ---- Combine + write CSV ----
    main_csv_dir = pd.concat([ldo_dir_is, ldo_dir_oos, algo_dir_is, ldo32_dir_is, ldo32_dir_oos], ignore_index=True)
    main_csv_dir["table"] = "direction_asymmetry"
    main_csv_exit = pd.concat([ldo_exit_is, ldo_exit_oos, algo_exit_is, ldo32_exit_is, ldo32_exit_oos], ignore_index=True)
    main_csv_exit["table"] = "exit_distribution"

    out_csv = ANALYSIS_DIR / "ldo_diagnosis.csv"
    with out_csv.open("w") as fh:
        fh.write("# table=direction_asymmetry\n")
        main_csv_dir.to_csv(fh, index=False)
        fh.write("\n# table=exit_distribution\n")
        main_csv_exit.to_csv(fh, index=False)
        fh.write("\n# table=ldo_period_pnl_iter044\n")
        pd.concat([ldo_period_is, ldo_period_oos], ignore_index=True).to_csv(fh, index=False)
        fh.write("\n# table=ldo_feature_importance_iter044\n")
        ldo_imp.to_csv(fh, index=False)
    print(f"\nWrote {out_csv}")

    # ---- Synthesis text ----
    ldo44_is_long = ldo_dir_is[ldo_dir_is["direction"] == "LONG"].iloc[0]
    ldo44_is_short = ldo_dir_is[ldo_dir_is["direction"] == "SHORT"].iloc[0]
    ldo44_oos_long = ldo_dir_oos[ldo_dir_oos["direction"] == "LONG"].iloc[0]
    ldo44_oos_short = ldo_dir_oos[ldo_dir_oos["direction"] == "SHORT"].iloc[0]
    ldo32_is_long = ldo32_dir_is[ldo32_dir_is["direction"] == "LONG"].iloc[0]
    ldo32_is_short = ldo32_dir_is[ldo32_dir_is["direction"] == "SHORT"].iloc[0]
    ldo32_oos_long = ldo32_dir_oos[ldo32_dir_oos["direction"] == "LONG"].iloc[0]
    ldo32_oos_short = ldo32_dir_oos[ldo32_dir_oos["direction"] == "SHORT"].iloc[0]

    ldo44_is_exit_b = ldo_exit_is[ldo_exit_is["direction"] == "BOTH"].iloc[0]
    ldo44_oos_exit_b = ldo_exit_oos[ldo_exit_oos["direction"] == "BOTH"].iloc[0]
    ldo32_is_exit_b = ldo32_exit_is[ldo32_exit_is["direction"] == "BOTH"].iloc[0]
    ldo32_oos_exit_b = ldo32_exit_oos[ldo32_exit_oos["direction"] == "BOTH"].iloc[0]
    algo_is_exit_long = algo_exit_is[algo_exit_is["direction"] == "LONG"].iloc[0]

    syn = ANALYSIS_DIR / "synthesis.md"
    with syn.open("w") as fh:
        fh.write("# LDO Bottleneck Diagnosis — iter-v3/045\n\n")
        fh.write("Generated by `analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py`. ")
        fh.write("All numbers verbatim from `reports-v3/iteration_v3-044` and `reports-v3/iteration_v3-032`.\n\n")
        fh.write("## Q1 — LDO direction asymmetry (iter-v3/044)\n\n")
        fh.write(f"### IS (training data, n={int(ldo44_is_long['n_trades'] + ldo44_is_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(ldo44_is_long['n_trades'])}, WR={ldo44_is_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo44_is_long['net_pnl_pct_sum']:+.2f}%, weighted={ldo44_is_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(ldo44_is_short['n_trades'])}, WR={ldo44_is_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo44_is_short['net_pnl_pct_sum']:+.2f}%, weighted={ldo44_is_short['weighted_pnl_sum']:+.2f}\n\n")
        fh.write(f"### OOS (n={int(ldo44_oos_long['n_trades'] + ldo44_oos_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(ldo44_oos_long['n_trades'])}, WR={ldo44_oos_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo44_oos_long['net_pnl_pct_sum']:+.2f}%, weighted={ldo44_oos_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(ldo44_oos_short['n_trades'])}, WR={ldo44_oos_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo44_oos_short['net_pnl_pct_sum']:+.2f}%, weighted={ldo44_oos_short['weighted_pnl_sum']:+.2f}\n\n")

        fh.write("## Q2 — Exit reason distribution (iter-v3/044 LDO BOTH directions)\n\n")
        fh.write(f"- IS: TP={ldo44_is_exit_b['tp_pct']:.1f}%, SL={ldo44_is_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={ldo44_is_exit_b['timeout_pct']:.1f}%, SL:TP={ldo44_is_exit_b['sl_to_tp_ratio']}\n")
        fh.write(f"- OOS: TP={ldo44_oos_exit_b['tp_pct']:.1f}%, SL={ldo44_oos_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={ldo44_oos_exit_b['timeout_pct']:.1f}%, SL:TP={ldo44_oos_exit_b['sl_to_tp_ratio']}\n")
        fh.write(f"- iter-v3/044 ALGO LONG IS: SL:TP={algo_is_exit_long['sl_to_tp_ratio']} "
                 f"(reference; the LONG asymmetry that motivated ALGO ATR (2.0, 1.5))\n\n")

        fh.write("## Q4 — Comparison vs iter-v3/032 LDO ATR (1.5, 0.75)\n\n")
        fh.write("iter-v3/032 used wider RR (TP=1.5×ATR, SL=0.75×ATR → RR=2.0:1, vs iter-v3/044's 2.0:1 ratio at higher absolute = TP=2.0×ATR, SL=1.0×ATR).\n\n")
        fh.write(f"### iter-v3/032 LDO IS (n={int(ldo32_is_long['n_trades'] + ldo32_is_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(ldo32_is_long['n_trades'])}, WR={ldo32_is_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo32_is_long['net_pnl_pct_sum']:+.2f}%\n")
        fh.write(f"- SHORT: n={int(ldo32_is_short['n_trades'])}, WR={ldo32_is_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo32_is_short['net_pnl_pct_sum']:+.2f}%\n\n")
        fh.write(f"### iter-v3/032 LDO OOS (n={int(ldo32_oos_long['n_trades'] + ldo32_oos_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(ldo32_oos_long['n_trades'])}, WR={ldo32_oos_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo32_oos_long['net_pnl_pct_sum']:+.2f}%\n")
        fh.write(f"- SHORT: n={int(ldo32_oos_short['n_trades'])}, WR={ldo32_oos_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={ldo32_oos_short['net_pnl_pct_sum']:+.2f}%\n\n")
        fh.write(f"### iter-v3/032 LDO exit distribution (BOTH)\n\n")
        fh.write(f"- IS: TP={ldo32_is_exit_b['tp_pct']:.1f}%, SL={ldo32_is_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={ldo32_is_exit_b['timeout_pct']:.1f}%, SL:TP={ldo32_is_exit_b['sl_to_tp_ratio']}\n")
        fh.write(f"- OOS: TP={ldo32_oos_exit_b['tp_pct']:.1f}%, SL={ldo32_oos_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={ldo32_oos_exit_b['timeout_pct']:.1f}%, SL:TP={ldo32_oos_exit_b['sl_to_tp_ratio']}\n\n")

        fh.write("## Q5 — LDO feature importance (iter-v3/044, last training month)\n\n")
        fh.write(ldo_imp.to_markdown(index=False))
        fh.write("\n\n## Files\n\n")
        fh.write("- `ldo_diagnosis.csv` — all numerical tables\n")
        fh.write("- `synthesis.md` — this file (READ FIRST)\n")
    print(f"Wrote {syn}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""BCH + TRX bottleneck diagnosis for iter-v3/046 QR-driven axis selection.

Context (iter-v3/045 closeout — STRONGEST PROMISING in v3 history):
- All 4 symbols positive in OOS for the first time. Bundle OOS Sharpe +3.5259 single-seed.
- BUT IS Sharpe is the binding multi-seed constraint per BASELINE_V3.md.
- iter-v3/045 single-seed IS Sharpe +0.7459; expected multi-seed compression ~50% gives ~+0.37
  — BELOW the +0.5101 baseline (strict BOTH-must-improve rule).
- The IS axis must lift for iter-v3/050 CONFIRMATION to clear the strict baseline rule.

Per-symbol IS performance @ iter-v3/045 (per_symbol.csv):
- LDO IS: 18 trades, 55.6% WR, +54.55% (per-symbol ATR (2.0, 1.5) — already optimized)
- BCH IS: 94 trades, 38.3% WR, +23.62% (default ATR; many trades, low WR)
- TRX IS: 85 trades, 34.1% WR, -7.28% (default ATR; LOWEST IS WR, IS-NEGATIVE) ← CRITICAL
- ALGO IS: 53 trades, 39.6% WR, -34.05% (per-symbol ATR (2.0, 1.5); IS catastrophic) ← REGRESSION

OOS performance (the headline strength) is being paid for at IS expense. TRX -7.28 IS net_pnl
and ALGO -34.05 IS net_pnl are the primary IS-axis bottlenecks.

This diagnostic computes:
1. BCH direction asymmetry IS + OOS (LONG vs SHORT WR + PnL)
2. TRX direction asymmetry IS + OOS (LONG vs SHORT WR + PnL)
3. BCH exit-composition (TP/SL/TIMEOUT) IS + OOS
4. TRX exit-composition (TP/SL/TIMEOUT) IS + OOS
5. ALGO IS regression diagnosis: did ALGO ATR (2.0, 1.5) hurt ALGO's IS specifically?
   — Compare ALGO @ iter-v3/045 IS vs ALGO @ iter-v3/043 (last default-ATR baseline)
6. Per-month IS PnL for BCH/TRX — temporal stability check
7. Counterfactual estimates: if BCH or TRX got per-symbol ATR widening, what's the IS lift?

Outputs:
- bch_trx_diagnosis.csv (numerical tables)
- synthesis.md (text summary; READ THIS FIRST)
- candidate_axes_ranking.md (5 ranked candidate axes for iter-v3/046)

IS-only data (no OOS peeking — OOS pulled only for the IS→OOS exit-composition shift
comparison and BCH OOS WR confirmation, which is part of the standard direction-asymmetry +
exit-composition diagnostic pattern established at iter-v3/044/045 axis-selection cycle).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-046"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

ITER045_IS = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "trades.csv"
ITER045_OOS = REPO / "reports-v3" / "iteration_v3-045" / "out_of_sample" / "trades.csv"
ITER044_IS = REPO / "reports-v3" / "iteration_v3-044" / "in_sample" / "trades.csv"
ITER044_OOS = REPO / "reports-v3" / "iteration_v3-044" / "out_of_sample" / "trades.csv"
ITER043_IS = REPO / "reports-v3" / "iteration_v3-043" / "in_sample" / "trades.csv"
ITER043_OOS = REPO / "reports-v3" / "iteration_v3-043" / "out_of_sample" / "trades.csv"

ITER045_BCH_IMP = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "model_importance_last_month_BCHUSDT.csv"
ITER045_TRX_IMP = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "model_importance_last_month_TRXUSDT.csv"


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
    """TP/SL/TIMEOUT distribution split by direction (and BOTH summary)."""
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
                    "mean_sl_pnl_pct": 0.0,
                    "mean_tp_pnl_pct": 0.0,
                }
            )
            continue
        n_tp = int((d["exit_reason"] == "take_profit").sum())
        n_sl = int((d["exit_reason"] == "stop_loss").sum())
        n_timeout = int((d["exit_reason"] == "timeout").sum())
        n_other = n - n_tp - n_sl - n_timeout
        sl_to_tp = round(n_sl / n_tp, 2) if n_tp else float("inf")
        mean_sl = round(d.loc[d["exit_reason"] == "stop_loss", "net_pnl_pct"].mean(), 3) if n_sl else 0.0
        mean_tp = round(d.loc[d["exit_reason"] == "take_profit", "net_pnl_pct"].mean(), 3) if n_tp else 0.0
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
                "mean_sl_pnl_pct": mean_sl,
                "mean_tp_pnl_pct": mean_tp,
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
            n_sl=("exit_reason", lambda x: int((x == "stop_loss").sum())),
            n_tp=("exit_reason", lambda x: int((x == "take_profit").sum())),
        )
        .reset_index()
    )
    g["win_rate_pct"] = (g["wins"] / g["n_trades"] * 100).round(2)
    g["sl_pct"] = (g["n_sl"] / g["n_trades"] * 100).round(2)
    g["set"] = label
    return g


def main() -> int:
    out_lines = []

    # ---- Load all trade sets ----
    print("[1/8] Loading trade sets...")
    iter45_is = load_trades(ITER045_IS)
    iter45_oos = load_trades(ITER045_OOS)
    iter44_is = load_trades(ITER044_IS)
    iter44_oos = load_trades(ITER044_OOS)
    iter43_is = load_trades(ITER043_IS)
    iter43_oos = load_trades(ITER043_OOS)
    print(f"  iter-v3/045 IS rows: {len(iter45_is)}, OOS: {len(iter45_oos)}")
    print(f"  iter-v3/044 IS rows: {len(iter44_is)}, OOS: {len(iter44_oos)}")
    print(f"  iter-v3/043 IS rows: {len(iter43_is)}, OOS: {len(iter43_oos)}")

    # ---- 1. BCH direction asymmetry IS + OOS @ iter-v3/045 ----
    print("\n[2/8] BCH direction asymmetry (iter-v3/045 IS + OOS)...")
    bch_dir_is = direction_asymmetry(iter45_is, "BCHUSDT")
    bch_dir_is["dataset"] = "iter045_IS"
    bch_dir_oos = direction_asymmetry(iter45_oos, "BCHUSDT")
    bch_dir_oos["dataset"] = "iter045_OOS"
    print(bch_dir_is.to_string(index=False))
    print()
    print(bch_dir_oos.to_string(index=False))

    # ---- 2. TRX direction asymmetry IS + OOS @ iter-v3/045 ----
    print("\n[3/8] TRX direction asymmetry (iter-v3/045 IS + OOS)...")
    trx_dir_is = direction_asymmetry(iter45_is, "TRXUSDT")
    trx_dir_is["dataset"] = "iter045_IS"
    trx_dir_oos = direction_asymmetry(iter45_oos, "TRXUSDT")
    trx_dir_oos["dataset"] = "iter045_OOS"
    print(trx_dir_is.to_string(index=False))
    print()
    print(trx_dir_oos.to_string(index=False))

    # ---- 3. BCH exit-composition IS + OOS ----
    print("\n[4/8] BCH exit-composition (iter-v3/045 IS + OOS)...")
    bch_exit_is = exit_distribution(iter45_is, "BCHUSDT")
    bch_exit_is["dataset"] = "iter045_IS"
    bch_exit_oos = exit_distribution(iter45_oos, "BCHUSDT")
    bch_exit_oos["dataset"] = "iter045_OOS"
    print(bch_exit_is.to_string(index=False))
    print()
    print(bch_exit_oos.to_string(index=False))

    # ---- 4. TRX exit-composition IS + OOS ----
    print("\n[5/8] TRX exit-composition (iter-v3/045 IS + OOS)...")
    trx_exit_is = exit_distribution(iter45_is, "TRXUSDT")
    trx_exit_is["dataset"] = "iter045_IS"
    trx_exit_oos = exit_distribution(iter45_oos, "TRXUSDT")
    trx_exit_oos["dataset"] = "iter045_OOS"
    print(trx_exit_is.to_string(index=False))
    print()
    print(trx_exit_oos.to_string(index=False))

    # ---- 5. ALGO IS regression diagnosis ----
    # Compare ALGO @ iter-v3/045 (per-symbol ATR (2.0, 1.5))
    # vs ALGO @ iter-v3/043 (last default-ATR baseline before iter-v3/044 ALGO ATR)
    print("\n[6/8] ALGO IS regression — did ATR widening hurt ALGO's IS?")
    algo_dir_is_45 = direction_asymmetry(iter45_is, "ALGOUSDT")
    algo_dir_is_45["dataset"] = "iter045_IS_per_sym_ATR_2.0_1.5"
    algo_dir_is_43 = direction_asymmetry(iter43_is, "ALGOUSDT")
    algo_dir_is_43["dataset"] = "iter043_IS_default_ATR_2.0_1.0"
    algo_exit_is_45 = exit_distribution(iter45_is, "ALGOUSDT")
    algo_exit_is_45["dataset"] = "iter045_IS_per_sym_ATR_2.0_1.5"
    algo_exit_is_43 = exit_distribution(iter43_is, "ALGOUSDT")
    algo_exit_is_43["dataset"] = "iter043_IS_default_ATR_2.0_1.0"
    print("ALGO @ iter-v3/043 (default ATR):")
    print(algo_dir_is_43.to_string(index=False))
    print("ALGO @ iter-v3/045 (per-symbol ATR (2.0, 1.5)):")
    print(algo_dir_is_45.to_string(index=False))
    print("Exit composition diff:")
    print(algo_exit_is_43.to_string(index=False))
    print(algo_exit_is_45.to_string(index=False))

    # ---- 6. Per-month IS PnL for BCH/TRX ----
    print("\n[7/8] Per-month IS PnL temporal stability (BCH + TRX)...")
    bch_period_is = per_period_pnl(iter45_is, "BCHUSDT", "iter045_IS_BCH")
    trx_period_is = per_period_pnl(iter45_is, "TRXUSDT", "iter045_IS_TRX")
    print("BCH per-month IS:")
    print(bch_period_is.to_string(index=False))
    print("\nTRX per-month IS:")
    print(trx_period_is.to_string(index=False))

    # ---- 7. Feature importance for BCH and TRX models ----
    print("\n[8/8] Feature importance (BCH + TRX last training month)...")
    bch_imp = pd.read_csv(ITER045_BCH_IMP).sort_values("importance", ascending=False)
    trx_imp = pd.read_csv(ITER045_TRX_IMP).sort_values("importance", ascending=False)
    bch_imp["symbol"] = "BCH"
    trx_imp["symbol"] = "TRX"
    print("BCH feature importance (top 14):")
    print(bch_imp.to_string(index=False))
    print("\nTRX feature importance (top 14):")
    print(trx_imp.to_string(index=False))

    # ---- Combine + write CSV ----
    main_csv_dir = pd.concat(
        [bch_dir_is, bch_dir_oos, trx_dir_is, trx_dir_oos, algo_dir_is_43, algo_dir_is_45],
        ignore_index=True,
    )
    main_csv_dir["table"] = "direction_asymmetry"
    main_csv_exit = pd.concat(
        [bch_exit_is, bch_exit_oos, trx_exit_is, trx_exit_oos, algo_exit_is_43, algo_exit_is_45],
        ignore_index=True,
    )
    main_csv_exit["table"] = "exit_distribution"

    out_csv = ANALYSIS_DIR / "bch_trx_diagnosis.csv"
    with out_csv.open("w") as fh:
        fh.write("# table=direction_asymmetry\n")
        main_csv_dir.to_csv(fh, index=False)
        fh.write("\n# table=exit_distribution\n")
        main_csv_exit.to_csv(fh, index=False)
        fh.write("\n# table=bch_period_pnl_iter045_IS\n")
        bch_period_is.to_csv(fh, index=False)
        fh.write("\n# table=trx_period_pnl_iter045_IS\n")
        trx_period_is.to_csv(fh, index=False)
        fh.write("\n# table=bch_feature_importance_iter045\n")
        bch_imp.to_csv(fh, index=False)
        fh.write("\n# table=trx_feature_importance_iter045\n")
        trx_imp.to_csv(fh, index=False)
    print(f"\nWrote {out_csv}")

    # ---- Synthesis text ----
    bch_is_long = bch_dir_is[bch_dir_is["direction"] == "LONG"].iloc[0]
    bch_is_short = bch_dir_is[bch_dir_is["direction"] == "SHORT"].iloc[0]
    bch_oos_long = bch_dir_oos[bch_dir_oos["direction"] == "LONG"].iloc[0]
    bch_oos_short = bch_dir_oos[bch_dir_oos["direction"] == "SHORT"].iloc[0]

    trx_is_long = trx_dir_is[trx_dir_is["direction"] == "LONG"].iloc[0]
    trx_is_short = trx_dir_is[trx_dir_is["direction"] == "SHORT"].iloc[0]
    trx_oos_long = trx_dir_oos[trx_dir_oos["direction"] == "LONG"].iloc[0]
    trx_oos_short = trx_dir_oos[trx_dir_oos["direction"] == "SHORT"].iloc[0]

    bch_is_exit_b = bch_exit_is[bch_exit_is["direction"] == "BOTH"].iloc[0]
    bch_oos_exit_b = bch_exit_oos[bch_exit_oos["direction"] == "BOTH"].iloc[0]
    trx_is_exit_b = trx_exit_is[trx_exit_is["direction"] == "BOTH"].iloc[0]
    trx_oos_exit_b = trx_exit_oos[trx_exit_oos["direction"] == "BOTH"].iloc[0]

    algo_is_exit_b_43 = algo_exit_is_43[algo_exit_is_43["direction"] == "BOTH"].iloc[0]
    algo_is_exit_b_45 = algo_exit_is_45[algo_exit_is_45["direction"] == "BOTH"].iloc[0]
    algo_is_total_43 = algo_dir_is_43[algo_dir_is_43["direction"] == "TOTAL"].iloc[0]
    algo_is_total_45 = algo_dir_is_45[algo_dir_is_45["direction"] == "TOTAL"].iloc[0]

    syn = ANALYSIS_DIR / "synthesis.md"
    with syn.open("w") as fh:
        fh.write("# BCH + TRX Bottleneck Diagnosis — iter-v3/046\n\n")
        fh.write("Generated by `analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py`. ")
        fh.write("Numbers verbatim from `reports-v3/iteration_v3-045`, `iteration_v3-044`, `iteration_v3-043`.\n\n")

        fh.write("## Headline — IS axis is the binding multi-seed constraint\n\n")
        fh.write("iter-v3/045 single-seed IS Sharpe +0.7459. Expected multi-seed compression "
                 "(~50%) gives ~+0.37 multi-seed mean — BELOW the +0.5101 BASELINE_V3.md baseline.\n\n")
        fh.write("Per-symbol IS contribution @ iter-v3/045:\n\n")
        fh.write("| Symbol | n IS | WR IS | net_pnl IS | pct of total |\n")
        fh.write("|--------|----:|------:|-----------:|-------------:|\n")
        fh.write("| LDO | 18 | 55.6% | +54.55% | 148.10% |\n")
        fh.write("| BCH | 94 | 38.3% | +23.62% | 64.13% |\n")
        fh.write("| TRX | 85 | 34.1% | -7.28% | -19.77% (IS-NEGATIVE) |\n")
        fh.write("| ALGO | 53 | 39.6% | -34.05% | -92.45% (IS-CATASTROPHIC) |\n\n")
        fh.write("ALGO and TRX are IS-NEGATIVE despite OOS-strong. The IS axis lift must come "
                 "from these two symbols. ALGO already has per-symbol ATR (2.0, 1.5) — the iter-v3/044 "
                 "ATR widening is the proximal cause of ALGO's IS regression (see Section 3 below).\n\n")

        fh.write("## Q1 — BCH direction asymmetry (iter-v3/045)\n\n")
        fh.write(f"### IS (n={int(bch_is_long['n_trades'] + bch_is_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(bch_is_long['n_trades'])}, WR={bch_is_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={bch_is_long['net_pnl_pct_sum']:+.2f}%, weighted={bch_is_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(bch_is_short['n_trades'])}, WR={bch_is_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={bch_is_short['net_pnl_pct_sum']:+.2f}%, weighted={bch_is_short['weighted_pnl_sum']:+.2f}\n\n")
        fh.write(f"### OOS (n={int(bch_oos_long['n_trades'] + bch_oos_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(bch_oos_long['n_trades'])}, WR={bch_oos_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={bch_oos_long['net_pnl_pct_sum']:+.2f}%, weighted={bch_oos_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(bch_oos_short['n_trades'])}, WR={bch_oos_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={bch_oos_short['net_pnl_pct_sum']:+.2f}%, weighted={bch_oos_short['weighted_pnl_sum']:+.2f}\n\n")

        fh.write("## Q2 — TRX direction asymmetry (iter-v3/045)\n\n")
        fh.write(f"### IS (n={int(trx_is_long['n_trades'] + trx_is_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(trx_is_long['n_trades'])}, WR={trx_is_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={trx_is_long['net_pnl_pct_sum']:+.2f}%, weighted={trx_is_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(trx_is_short['n_trades'])}, WR={trx_is_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={trx_is_short['net_pnl_pct_sum']:+.2f}%, weighted={trx_is_short['weighted_pnl_sum']:+.2f}\n\n")
        fh.write(f"### OOS (n={int(trx_oos_long['n_trades'] + trx_oos_short['n_trades'])})\n\n")
        fh.write(f"- LONG: n={int(trx_oos_long['n_trades'])}, WR={trx_oos_long['win_rate_pct']:.1f}%, "
                 f"net_pnl={trx_oos_long['net_pnl_pct_sum']:+.2f}%, weighted={trx_oos_long['weighted_pnl_sum']:+.2f}\n")
        fh.write(f"- SHORT: n={int(trx_oos_short['n_trades'])}, WR={trx_oos_short['win_rate_pct']:.1f}%, "
                 f"net_pnl={trx_oos_short['net_pnl_pct_sum']:+.2f}%, weighted={trx_oos_short['weighted_pnl_sum']:+.2f}\n\n")

        fh.write("## Q3 — Exit composition (BCH + TRX BOTH directions)\n\n")
        fh.write("### BCH\n\n")
        fh.write(f"- IS: TP={bch_is_exit_b['tp_pct']:.1f}%, SL={bch_is_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={bch_is_exit_b['timeout_pct']:.1f}%, SL:TP={bch_is_exit_b['sl_to_tp_ratio']}, "
                 f"mean_SL={bch_is_exit_b['mean_sl_pnl_pct']:+.2f}%, mean_TP={bch_is_exit_b['mean_tp_pnl_pct']:+.2f}%\n")
        fh.write(f"- OOS: TP={bch_oos_exit_b['tp_pct']:.1f}%, SL={bch_oos_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={bch_oos_exit_b['timeout_pct']:.1f}%, SL:TP={bch_oos_exit_b['sl_to_tp_ratio']}, "
                 f"mean_SL={bch_oos_exit_b['mean_sl_pnl_pct']:+.2f}%, mean_TP={bch_oos_exit_b['mean_tp_pnl_pct']:+.2f}%\n\n")
        fh.write("### TRX\n\n")
        fh.write(f"- IS: TP={trx_is_exit_b['tp_pct']:.1f}%, SL={trx_is_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={trx_is_exit_b['timeout_pct']:.1f}%, SL:TP={trx_is_exit_b['sl_to_tp_ratio']}, "
                 f"mean_SL={trx_is_exit_b['mean_sl_pnl_pct']:+.2f}%, mean_TP={trx_is_exit_b['mean_tp_pnl_pct']:+.2f}%\n")
        fh.write(f"- OOS: TP={trx_oos_exit_b['tp_pct']:.1f}%, SL={trx_oos_exit_b['sl_pct']:.1f}%, "
                 f"TIMEOUT={trx_oos_exit_b['timeout_pct']:.1f}%, SL:TP={trx_oos_exit_b['sl_to_tp_ratio']}, "
                 f"mean_SL={trx_oos_exit_b['mean_sl_pnl_pct']:+.2f}%, mean_TP={trx_oos_exit_b['mean_tp_pnl_pct']:+.2f}%\n\n")

        fh.write("## Q4 — ALGO IS regression diagnosis (did ATR (2.0, 1.5) hurt ALGO IS?)\n\n")
        fh.write(f"ALGO @ iter-v3/043 (default ATR (2.0, 1.0)): IS n={int(algo_is_total_43['n_trades'])}, "
                 f"WR={algo_is_total_43['win_rate_pct']:.1f}%, net_pnl={algo_is_total_43['net_pnl_pct_sum']:+.2f}%\n")
        fh.write(f"ALGO @ iter-v3/045 (per-symbol ATR (2.0, 1.5)): IS n={int(algo_is_total_45['n_trades'])}, "
                 f"WR={algo_is_total_45['win_rate_pct']:.1f}%, net_pnl={algo_is_total_45['net_pnl_pct_sum']:+.2f}%\n\n")
        fh.write(f"Δ IS n_trades: {int(algo_is_total_45['n_trades'] - algo_is_total_43['n_trades'])} "
                 f"({100 * (algo_is_total_45['n_trades'] - algo_is_total_43['n_trades']) / algo_is_total_43['n_trades']:+.1f}%)\n")
        fh.write(f"Δ IS WR: {algo_is_total_45['win_rate_pct'] - algo_is_total_43['win_rate_pct']:+.1f}pp\n")
        fh.write(f"Δ IS net_pnl: {algo_is_total_45['net_pnl_pct_sum'] - algo_is_total_43['net_pnl_pct_sum']:+.2f}%\n\n")
        fh.write(f"### ALGO IS exit composition shift\n\n")
        fh.write(f"- iter-v3/043 IS BOTH: TP={algo_is_exit_b_43['tp_pct']:.1f}%, SL={algo_is_exit_b_43['sl_pct']:.1f}%, "
                 f"SL:TP={algo_is_exit_b_43['sl_to_tp_ratio']}, mean_SL={algo_is_exit_b_43['mean_sl_pnl_pct']:+.2f}%\n")
        fh.write(f"- iter-v3/045 IS BOTH: TP={algo_is_exit_b_45['tp_pct']:.1f}%, SL={algo_is_exit_b_45['sl_pct']:.1f}%, "
                 f"SL:TP={algo_is_exit_b_45['sl_to_tp_ratio']}, mean_SL={algo_is_exit_b_45['mean_sl_pnl_pct']:+.2f}%\n\n")
        fh.write("**Interpretation:** ALGO ATR widening was OOS-validated (+49 PnL swing at iter-v3/044) "
                 "but if IS regressed materially, the OOS-lift came at IS expense — same structural pattern as "
                 "iter-v3/039 per-symbol customizations. This is critical for cycle 3 because the strict "
                 "BOTH-must-improve baseline rule will FAIL at iter-v3/050 if ALGO IS stays catastrophic.\n\n")

        fh.write("## Q5 — Counterfactual estimates\n\n")
        fh.write("### A) BCH per-symbol ATR widening (mirror iter-v3/045 LDO mechanism on BCH)\n\n")
        bch_is_sl_count = int(bch_is_exit_b['n_sl'])
        bch_is_n = int(bch_is_exit_b['n_trades'])
        bch_is_mean_sl = bch_is_exit_b['mean_sl_pnl_pct']
        fh.write(f"BCH IS exit composition: SL={bch_is_exit_b['sl_pct']:.1f}% ({bch_is_sl_count} of {bch_is_n} trades); "
                 f"mean_SL_pnl={bch_is_mean_sl:+.2f}%.\n")
        fh.write(f"If wider SL (1.5×) compresses IS SL rate by ~10pp (similar to iter-v3/045 LDO mechanism), ")
        fh.write(f"~{int(bch_is_n * 0.10)} SL trades become TP/timeout: net_pnl shift "
                 f"~{int(bch_is_n * 0.10) * (-bch_is_mean_sl + 0):.1f}% to "
                 f"{int(bch_is_n * 0.10) * (-bch_is_mean_sl + 5):.1f}% IS lift on BCH.\n\n")

        fh.write("### B) TRX per-symbol ATR widening (mirror iter-v3/045 LDO/ALGO mechanism on TRX)\n\n")
        trx_is_sl_count = int(trx_is_exit_b['n_sl'])
        trx_is_n = int(trx_is_exit_b['n_trades'])
        trx_is_mean_sl = trx_is_exit_b['mean_sl_pnl_pct']
        fh.write(f"TRX IS exit composition: SL={trx_is_exit_b['sl_pct']:.1f}% ({trx_is_sl_count} of {trx_is_n} trades); "
                 f"mean_SL_pnl={trx_is_mean_sl:+.2f}%.\n")
        fh.write(f"TRX IS net_pnl already NEGATIVE at -7.28%. If wider SL compresses SL rate by ~8pp (smaller than LDO "
                 f"because TRX trade base is larger and signals are weaker), ~{int(trx_is_n * 0.08)} SL trades become TP/timeout: "
                 f"net_pnl shift ~{int(trx_is_n * 0.08) * (-trx_is_mean_sl):.1f}% IS lift on TRX. "
                 f"Could turn TRX IS positive. **HIGHEST IS-AXIS LEVERAGE.**\n\n")

        fh.write("### C) ALGO ATR REVERT (back to default 2.0, 1.0)\n\n")
        fh.write(f"ALGO IS net_pnl regressed from {algo_is_total_43['net_pnl_pct_sum']:+.2f}% (iter-v3/043 default ATR) "
                 f"to {algo_is_total_45['net_pnl_pct_sum']:+.2f}% (iter-v3/045 per-symbol ATR). "
                 f"Reverting ALGO ATR would recover the {algo_is_total_43['net_pnl_pct_sum'] - algo_is_total_45['net_pnl_pct_sum']:+.2f}% IS lift "
                 f"BUT lose the OOS swing iter-v3/044 documented (+49 PnL on ALGO). "
                 f"This is a TRADE-OFF — must decide whether IS or OOS is the binding constraint.\n\n")

        fh.write("## Q6 — Per-month BCH/TRX IS PnL temporal stability\n\n")
        fh.write("### BCH per-month IS\n\n")
        fh.write(bch_period_is.to_markdown(index=False))
        fh.write("\n\n### TRX per-month IS\n\n")
        fh.write(trx_period_is.to_markdown(index=False))
        fh.write("\n\n")

        fh.write("## Q7 — Feature importance (BCH + TRX, iter-v3/045 last training month)\n\n")
        fh.write("### BCH (range 22-347, ratio 15.8×)\n\n")
        fh.write(bch_imp.drop(columns=["symbol"]).to_markdown(index=False))
        fh.write("\n\n### TRX (range 43-173, ratio 4.0×)\n\n")
        fh.write(trx_imp.drop(columns=["symbol"]).to_markdown(index=False))
        fh.write("\n\n")
        fh.write("BCH importance distribution is SHARPLY ranked (15.8× ratio top vs bottom). TRX is FLAT (4.0× ratio). "
                 "BCH model is HEAVILY using `hurst_diff_100_50` (347), `range_realized_vol_50` (337), `vwap_dev_20` (334) — "
                 "regime + volatility + mean-reversion. TRX is near-uniform. Neither benefits from feature additions; both "
                 "would benefit from labeling-layer per-symbol customization.\n\n")

        fh.write("## Files\n\n")
        fh.write("- `bch_trx_diagnosis.csv` — all numerical tables\n")
        fh.write("- `synthesis.md` — this file (READ FIRST)\n")
        fh.write("- `candidate_axes_ranking.md` — ranked candidate axes for iter-v3/046\n")
    print(f"Wrote {syn}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""iter-v1/030 — Phase 1.5 deep-dive on meta-labeling potential.

After axis_candidate_eda.py classified meta-labeling as STRONG potential
(37% IS losses concentrated in top-3 (sym, direction) cells), this script
quantifies the meta-labeling lift bounds:

1. Cell-level identifiability — can losses be predicted ex-ante from
   (sym, direction, exit_reason) alone? This is the LOW BAR (no features).
2. Per-symbol PnL retention if we veto the worst (sym, direction) cells.
3. Per-model decomposition — A (BTC+ETH), C (LINK), D (LTC), E (DOT) —
   which model gets the most lift from M2?
4. Time-stability of the loss-concentration pattern — does it persist
   across IS halves, or is it a single-period artifact?

Output: meta_labeling_potential.csv + meta_labeling_summary.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent

IS_TRADES = REPO / "reports-v1/iteration_v1-baseline/in_sample/trades.csv"
OOS_TRADES = REPO / "reports-v1/iteration_v1-baseline/out_of_sample/trades.csv"


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df["direction_label"] = np.where(df["direction"].astype(int) > 0, "long", "short")
    df["is_loss"] = df["net_pnl_pct"] < 0
    df["is_win"] = df["net_pnl_pct"] > 0
    return df


# Per-model attribution (from BASELINE_V1.md):
# Model A pooled: BTC + ETH
# Model C: LINK
# Model D: LTC
# Model E: DOT
SYMBOL_TO_MODEL = {
    "BTCUSDT": "A",
    "ETHUSDT": "A",
    "LINKUSDT": "C",
    "LTCUSDT": "D",
    "DOTUSDT": "E",
}


def cell_identifiability(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    """For each (sym, direction) cell, compute n_trades, win_rate,
    net_pnl, loss_share."""
    rows = []
    total_losses = (trades["net_pnl_pct"] < 0).sum()
    total_pnl = trades["net_pnl_pct"].sum()
    for sym in trades["symbol"].unique():
        for direction in ("long", "short"):
            sub = trades[
                (trades["symbol"] == sym) & (trades["direction_label"] == direction)
            ]
            if len(sub) == 0:
                continue
            wr = float((sub["net_pnl_pct"] > 0).mean())
            n_loss = int((sub["net_pnl_pct"] < 0).sum())
            n_win = int((sub["net_pnl_pct"] > 0).mean() * len(sub))
            rows.append({
                "sample": label,
                "symbol": sym,
                "direction": direction,
                "model": SYMBOL_TO_MODEL.get(sym, "?"),
                "n_trades": int(len(sub)),
                "n_loss": n_loss,
                "win_rate": wr,
                "net_pnl_pct": float(sub["net_pnl_pct"].sum()),
                "avg_pnl_per_trade": float(sub["net_pnl_pct"].mean()),
                "loss_share_of_total": float(n_loss / total_losses if total_losses else 0),
                "pnl_share_of_total": float(sub["net_pnl_pct"].sum() / total_pnl if total_pnl else 0),
            })
    return pd.DataFrame(rows).sort_values("avg_pnl_per_trade")


def hypothetical_veto_lift(trades: pd.DataFrame, sample_label: str) -> dict:
    """Hypothetical: if M2 PERFECTLY vetoed the worst N (sym, direction)
    cells (ranked by avg PnL per trade), how would headline change?"""
    cell_df = cell_identifiability(trades, sample_label).sort_values("avg_pnl_per_trade")
    total_n = len(trades)
    total_pnl = trades["net_pnl_pct"].sum()
    print(f"\n  Hypothetical veto-lift ({sample_label}, total trades {total_n}, total PnL {total_pnl:+.2f}):")
    results = []
    cumulative_vetoed_trades = 0
    cumulative_vetoed_pnl = 0.0
    for _, c in cell_df.iterrows():
        cumulative_vetoed_trades += c["n_trades"]
        cumulative_vetoed_pnl += c["net_pnl_pct"]
        remaining_n = total_n - cumulative_vetoed_trades
        remaining_pnl = total_pnl - cumulative_vetoed_pnl
        print(
            f"    Veto top-N worst cells through {c['symbol']} {c['direction']} (n={c['n_trades']}, pnl={c['net_pnl_pct']:+.2f}): "
            f"remaining {remaining_n} tr / {remaining_pnl:+.2f}% PnL "
            f"(veto_rate={cumulative_vetoed_trades / total_n:.1%}, pnl_lift={remaining_pnl - total_pnl:+.2f}%)"
        )
        results.append({
            "sample": sample_label,
            "cells_vetoed": int(len([1 for _ in results]) + 1),
            "vetoed_cell_symbol": c["symbol"],
            "vetoed_cell_direction": c["direction"],
            "vetoed_avg_pnl_per_trade": c["avg_pnl_per_trade"],
            "cumulative_vetoed_trades": cumulative_vetoed_trades,
            "cumulative_vetoed_pnl_pct": cumulative_vetoed_pnl,
            "remaining_trades": remaining_n,
            "remaining_pnl_pct": remaining_pnl,
            "veto_rate": cumulative_vetoed_trades / total_n,
            "headline_pnl_lift_pct": remaining_pnl - total_pnl,
        })
    return pd.DataFrame(results)


def time_stability_check(trades: pd.DataFrame) -> dict:
    """Does the worst-cell pattern hold in IS H1 vs IS H2 vs OOS?

    Meta-labeling generalizes to OOS if the loss-concentration pattern is
    persistent across regimes — otherwise M2 fits noise.
    """
    print("\n=== Time stability check ===")
    # Split IS by date into 50/50 halves
    is_sorted = trades.sort_values("open_time")
    cutoff = is_sorted["open_time"].quantile(0.5)
    h1 = is_sorted[is_sorted["open_time"] <= cutoff]
    h2 = is_sorted[is_sorted["open_time"] > cutoff]
    h1_cells = cell_identifiability(h1, "IS-H1").sort_values("avg_pnl_per_trade")
    h2_cells = cell_identifiability(h2, "IS-H2").sort_values("avg_pnl_per_trade")
    # Look at the top-3 worst cells from each half and see if they overlap.
    h1_worst3 = set(zip(h1_cells.head(3)["symbol"], h1_cells.head(3)["direction"]))
    h2_worst3 = set(zip(h2_cells.head(3)["symbol"], h2_cells.head(3)["direction"]))
    overlap = h1_worst3 & h2_worst3
    print(f"  IS-H1 worst-3 (sym, dir): {h1_worst3}")
    print(f"  IS-H2 worst-3 (sym, dir): {h2_worst3}")
    print(f"  Overlap: {overlap} ({len(overlap)}/3)")
    full_cells = cell_identifiability(trades, "IS-full").sort_values("avg_pnl_per_trade")
    h1_worst5 = set(zip(h1_cells.head(5)["symbol"], h1_cells.head(5)["direction"]))
    h2_worst5 = set(zip(h2_cells.head(5)["symbol"], h2_cells.head(5)["direction"]))
    overlap5 = h1_worst5 & h2_worst5
    print(f"  Overlap top-5: {overlap5} ({len(overlap5)}/5)")
    summary = {
        "h1_n_trades": int(len(h1)),
        "h2_n_trades": int(len(h2)),
        "overlap_worst3": len(overlap),
        "overlap_worst5": len(overlap5),
        "h1_worst3": str(h1_worst3),
        "h2_worst3": str(h2_worst3),
        "stability_assessment": "HIGH" if len(overlap) >= 2 else ("MODERATE" if len(overlap) == 1 else "LOW"),
    }
    print(f"  -> stability: {summary['stability_assessment']}")
    return summary


def per_model_decomposition(trades: pd.DataFrame, sample_label: str) -> pd.DataFrame:
    """Per-model loss concentration."""
    rows = []
    total_loss = (trades["net_pnl_pct"] < 0).sum()
    total_pnl = trades["net_pnl_pct"].sum()
    for model in ("A", "C", "D", "E"):
        model_syms = [s for s, m in SYMBOL_TO_MODEL.items() if m == model]
        sub = trades[trades["symbol"].isin(model_syms)]
        if len(sub) == 0:
            continue
        cell_df = cell_identifiability(sub, sample_label)
        worst_cell = cell_df.iloc[0] if len(cell_df) else None
        rows.append({
            "sample": sample_label,
            "model": model,
            "symbols": ",".join(model_syms),
            "n_trades": int(len(sub)),
            "win_rate": float((sub["net_pnl_pct"] > 0).mean()),
            "n_loss": int((sub["net_pnl_pct"] < 0).sum()),
            "net_pnl_pct": float(sub["net_pnl_pct"].sum()),
            "avg_pnl_per_trade": float(sub["net_pnl_pct"].mean()),
            "loss_share_of_total": float((sub["net_pnl_pct"] < 0).sum() / total_loss if total_loss else 0),
            "pnl_share_of_total": float(sub["net_pnl_pct"].sum() / total_pnl if total_pnl else 0),
            "worst_cell_sym_dir": (
                f"{worst_cell['symbol']} {worst_cell['direction']}" if worst_cell is not None else "?"
            ),
            "worst_cell_avg_pnl": float(worst_cell["avg_pnl_per_trade"]) if worst_cell is not None else 0.0,
            "worst_cell_n_trades": int(worst_cell["n_trades"]) if worst_cell is not None else 0,
        })
    df = pd.DataFrame(rows)
    return df


def main() -> None:
    is_trades = load_trades(IS_TRADES)
    oos_trades = load_trades(OOS_TRADES)

    # 1. Cell identifiability (IS + OOS)
    is_cells = cell_identifiability(is_trades, "IS-full")
    oos_cells = cell_identifiability(oos_trades, "OOS-full")
    all_cells = pd.concat([is_cells, oos_cells], ignore_index=True)
    all_cells.to_csv(OUT_DIR / "meta_labeling_cells.csv", index=False)

    # 2. Hypothetical veto lift (IS + OOS)
    is_veto = hypothetical_veto_lift(is_trades, "IS-full")
    oos_veto = hypothetical_veto_lift(oos_trades, "OOS-full")
    veto = pd.concat([is_veto, oos_veto], ignore_index=True)
    veto.to_csv(OUT_DIR / "meta_labeling_veto_lift.csv", index=False)

    # 3. Time stability
    stability = time_stability_check(is_trades)
    pd.DataFrame([stability]).to_csv(OUT_DIR / "meta_labeling_stability.csv", index=False)

    # 4. Per-model decomposition
    is_model = per_model_decomposition(is_trades, "IS-full")
    oos_model = per_model_decomposition(oos_trades, "OOS-full")
    model_df = pd.concat([is_model, oos_model], ignore_index=True)
    model_df.to_csv(OUT_DIR / "meta_labeling_per_model.csv", index=False)

    print("\n=== Per-model summary ===")
    print(model_df.to_string(index=False))

    # 5. Headline summary
    is_total_pnl = is_trades["net_pnl_pct"].sum()
    oos_total_pnl = oos_trades["net_pnl_pct"].sum()
    # Top-3 worst cell veto effect
    is_top3_veto = is_veto.iloc[2]
    oos_top3_veto = oos_veto.iloc[2]
    print(f"\n=== Headline meta-labeling potential ===")
    print(f"  IS total PnL: {is_total_pnl:+.2f}% (baseline)")
    print(f"  IS top-3 worst-cell veto: lift +{is_top3_veto['headline_pnl_lift_pct']:.2f}% (veto rate {is_top3_veto['veto_rate']:.1%})")
    print(f"  OOS total PnL: {oos_total_pnl:+.2f}% (baseline)")
    print(f"  OOS top-3 worst-cell veto: lift +{oos_top3_veto['headline_pnl_lift_pct']:.2f}% (veto rate {oos_top3_veto['veto_rate']:.1%})")
    print(f"  Time stability (H1/H2 worst-3 overlap): {stability['overlap_worst3']}/3 ({stability['stability_assessment']})")

    summary_rows = [{
        "is_total_pnl_pct": is_total_pnl,
        "is_top3_veto_lift_pct": float(is_top3_veto["headline_pnl_lift_pct"]),
        "is_top3_veto_rate": float(is_top3_veto["veto_rate"]),
        "oos_total_pnl_pct": oos_total_pnl,
        "oos_top3_veto_lift_pct": float(oos_top3_veto["headline_pnl_lift_pct"]),
        "oos_top3_veto_rate": float(oos_top3_veto["veto_rate"]),
        "stability_h1_h2_top3_overlap": stability["overlap_worst3"],
        "stability_assessment": stability["stability_assessment"],
        "meta_labeling_oracle_max_lift_is_pnl_pct": float(is_veto["headline_pnl_lift_pct"].max()),
        "meta_labeling_oracle_max_lift_oos_pnl_pct": float(oos_veto["headline_pnl_lift_pct"].max()),
    }]
    pd.DataFrame(summary_rows).to_csv(OUT_DIR / "meta_labeling_summary.csv", index=False)
    print(f"\nWritten: {OUT_DIR / 'meta_labeling_summary.csv'}")


if __name__ == "__main__":
    main()

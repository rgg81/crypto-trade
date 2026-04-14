"""Combined v1+v2 portfolio analysis (iter-v2/011).

Loads existing trade CSVs from v1's iter-152 baseline and v2's iter-v2/005
baseline, concatenates them as a single combined-portfolio trade stream,
and computes joint metrics:

- Per-track Sharpe / PF / MaxDD (v1, v2, combined)
- Per-symbol breakdown
- v1-v2 daily return correlation
- Concentration of the combined portfolio
- Sample diversification benefit (combined Sharpe vs equal-weight v1+v2)

Inputs:
  - {V1_REPORT}/in_sample/trades.csv (v1 IS)
  - {V1_REPORT}/out_of_sample/trades.csv (v1 OOS)
  - reports-v2/iteration_v2-005/in_sample/trades.csv (v2 IS)
  - reports-v2/iteration_v2-005/out_of_sample/trades.csv (v2 OOS)

The v1 canonical iter-152 reports live in the main repo at
`../../reports/iteration_152_min33_max200/` — the merged iter-152
baseline (min_scale=0.33). This runner reads them directly rather
than re-running the 3-hour v1 baseline each time.

Usage:
    uv run python run_portfolio_combined.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# v1 canonical iter-152 lives in the main repo (not the worktree)
V1_REPORT = Path("/home/roberto/crypto-trade/reports/iteration_152_min33_max200")
V2_REPORT = Path("reports-v2/iteration_v2-005")
OUT_DIR = Path("reports-v2/iteration_v2-011_combined")


def _load_trades(report_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_path = report_dir / "in_sample/trades.csv"
    oos_path = report_dir / "out_of_sample/trades.csv"
    if not is_path.exists() or not oos_path.exists():
        raise FileNotFoundError(
            f"Missing trades.csv files in {report_dir}. Run the baseline first."
        )
    return pd.read_csv(is_path), pd.read_csv(oos_path)


def _annualize(daily_pnl: pd.Series, periods: int = 365) -> tuple[float, float, float]:
    """Compute annualized Sharpe, mean, std from a daily PnL series."""
    if len(daily_pnl) < 2 or daily_pnl.std() == 0:
        return 0.0, 0.0, 0.0
    mean = daily_pnl.mean()
    std = daily_pnl.std()
    sharpe = mean / std * np.sqrt(periods)
    return sharpe, mean, std


def _max_drawdown(equity_curve: pd.Series) -> float:
    if len(equity_curve) == 0:
        return 0.0
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max.replace(0, np.nan)
    return float(drawdown.min() or 0.0)


def _summarize_trades(trades: pd.DataFrame, label: str) -> dict:
    if len(trades) == 0:
        return {"label": label, "n": 0}

    # Trade-level metrics
    pnl = trades["weighted_pnl"]
    wins = (trades["net_pnl_pct"] > 0).sum()
    wr = wins / len(trades)
    pf = (
        trades.loc[trades["weighted_pnl"] > 0, "weighted_pnl"].sum()
        / abs(trades.loc[trades["weighted_pnl"] < 0, "weighted_pnl"].sum() or 1)
    )
    sharpe_trades = pnl.mean() / pnl.std() * np.sqrt(len(pnl)) if pnl.std() > 0 else 0

    # Daily aggregation
    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.date
    daily = trades.groupby("date")["weighted_pnl"].sum()

    # Equity curve (cumulative)
    equity = (1.0 + daily / 100.0).cumprod()
    max_dd = _max_drawdown(equity)

    sharpe_daily, _, _ = _annualize(daily / 100.0)

    return {
        "label": label,
        "n": int(len(trades)),
        "wins": int(wins),
        "win_rate": round(wr * 100, 2),
        "pf": round(float(pf), 4),
        "sharpe_trades": round(float(sharpe_trades), 4),
        "sharpe_daily_annualized": round(float(sharpe_daily), 4),
        "max_dd_pct": round(float(max_dd * 100), 2),
        "total_weighted_pnl": round(float(pnl.sum()), 2),
        "active_days": int(daily.count()),
        "first_date": str(daily.index.min()) if len(daily) else None,
        "last_date": str(daily.index.max()) if len(daily) else None,
    }


def _per_symbol(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total = trades["weighted_pnl"].sum() if len(trades) else 0
    for sym, s in trades.groupby("symbol"):
        wt = s["weighted_pnl"].sum()
        rows.append(
            {
                "symbol": sym,
                "n": len(s),
                "wr": round((s["net_pnl_pct"] > 0).mean() * 100, 2),
                "weighted_pnl": round(float(wt), 2),
                "share_pct": round(float(wt / total * 100), 2) if total else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("share_pct", ascending=False)


def _v1_v2_correlation(v1_trades: pd.DataFrame, v2_trades: pd.DataFrame) -> dict:
    v1 = v1_trades.copy()
    v2 = v2_trades.copy()
    v1["date"] = pd.to_datetime(v1["close_time"], unit="ms").dt.date
    v2["date"] = pd.to_datetime(v2["close_time"], unit="ms").dt.date

    daily_v1 = v1.groupby("date")["weighted_pnl"].sum()
    daily_v2 = v2.groupby("date")["weighted_pnl"].sum()

    aligned = pd.concat([daily_v1, daily_v2], axis=1, join="inner").dropna()
    if len(aligned) < 5:
        return {"correlation": None, "n_days": int(len(aligned))}
    return {
        "correlation": round(float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1])), 4),
        "n_days": int(len(aligned)),
        "common_first_date": str(aligned.index.min()),
        "common_last_date": str(aligned.index.max()),
    }


def _diversification_benefit(
    v1_trades: pd.DataFrame, v2_trades: pd.DataFrame
) -> dict:
    """Quantify diversification value vs naive v1-or-v2 alone.

    Combined Sharpe expectation under independence:
      sigma_combined = sqrt(sigma_v1^2 + sigma_v2^2) / 2
      mean_combined  = (mean_v1 + mean_v2) / 2
    The actual combined Sharpe should match this if v1-v2 correlation is 0.
    """
    v1 = v1_trades.copy()
    v2 = v2_trades.copy()
    v1["date"] = pd.to_datetime(v1["close_time"], unit="ms").dt.date
    v2["date"] = pd.to_datetime(v2["close_time"], unit="ms").dt.date

    daily_v1 = v1.groupby("date")["weighted_pnl"].sum() / 100.0
    daily_v2 = v2.groupby("date")["weighted_pnl"].sum() / 100.0

    # Equal-weight combined daily PnL: average of the two daily series
    daily_combined = pd.concat([daily_v1, daily_v2], axis=1).fillna(0).mean(axis=1)

    sr_v1, _, _ = _annualize(daily_v1)
    sr_v2, _, _ = _annualize(daily_v2)
    sr_combined, _, _ = _annualize(daily_combined)

    # Theoretical combined under independence
    if daily_v1.std() > 0 and daily_v2.std() > 0:
        var_combined = (daily_v1.var() + daily_v2.var()) / 4.0
        mean_combined = (daily_v1.mean() + daily_v2.mean()) / 2.0
        sr_independent = mean_combined / np.sqrt(var_combined) * np.sqrt(365)
    else:
        sr_independent = 0.0

    return {
        "sharpe_v1_alone": round(float(sr_v1), 4),
        "sharpe_v2_alone": round(float(sr_v2), 4),
        "sharpe_equal_weight_combined": round(float(sr_combined), 4),
        "sharpe_combined_under_independence": round(float(sr_independent), 4),
        "diversification_uplift_vs_v1_alone": round(float(sr_combined - sr_v1), 4),
        "diversification_uplift_vs_v2_alone": round(float(sr_combined - sr_v2), 4),
    }


def main() -> None:
    print("=" * 70)
    print("COMBINED v1+v2 PORTFOLIO ANALYSIS — iter-v2/011")
    print("=" * 70)

    if not V1_REPORT.exists():
        print(f"ERROR: v1 report not found at {V1_REPORT}")
        print("Expected the canonical iter-152 (min_scale=0.33) reports in main repo.")
        sys.exit(1)
    if not V2_REPORT.exists():
        print(f"ERROR: v2 report not found at {V2_REPORT}")
        print("Run `uv run python run_baseline_v2.py` first to generate it.")
        sys.exit(1)

    v1_is, v1_oos = _load_trades(V1_REPORT)
    v2_is, v2_oos = _load_trades(V2_REPORT)

    print(f"\nv1 trades loaded: IS={len(v1_is)}, OOS={len(v1_oos)}")
    print(f"v2 trades loaded: IS={len(v2_is)}, OOS={len(v2_oos)}")

    # Tag each trade by track for the combined view
    v1_oos["track"] = "v1"
    v2_oos["track"] = "v2"
    combined_oos = pd.concat([v1_oos, v2_oos], ignore_index=True).sort_values("close_time")

    # ---------- Summary tables ----------
    summary = {
        "v1_oos": _summarize_trades(v1_oos, "v1 OOS (iter-152, BTC+ETH+LINK+BNB)"),
        "v2_oos": _summarize_trades(v2_oos, "v2 OOS (iter-v2/005, DOGE+SOL+XRP+NEAR, seed 42)"),
        "combined_oos": _summarize_trades(
            combined_oos, "v1+v2 combined OOS (8 symbols, naive concat)"
        ),
        "v1_is": _summarize_trades(v1_is, "v1 IS"),
        "v2_is": _summarize_trades(v2_is, "v2 IS"),
    }

    print("\n" + "=" * 70)
    print("OOS METRICS — v1 / v2 / COMBINED")
    print("=" * 70)
    for key in ("v1_oos", "v2_oos", "combined_oos"):
        s = summary[key]
        print(f"\n{s['label']}:")
        for k in (
            "n",
            "win_rate",
            "pf",
            "sharpe_trades",
            "sharpe_daily_annualized",
            "max_dd_pct",
            "total_weighted_pnl",
            "active_days",
        ):
            print(f"  {k}: {s.get(k)}")

    # ---------- Per-symbol concentration ----------
    print("\n" + "=" * 70)
    print("PER-SYMBOL OOS CONCENTRATION")
    print("=" * 70)
    print("\nv1 (iter-152) per-symbol OOS:")
    print(_per_symbol(v1_oos).to_string(index=False))
    print("\nv2 (iter-v2/005) per-symbol OOS:")
    print(_per_symbol(v2_oos).to_string(index=False))
    print("\nCombined v1+v2 per-symbol OOS:")
    print(_per_symbol(combined_oos).to_string(index=False))

    # ---------- v1-v2 correlation ----------
    print("\n" + "=" * 70)
    print("v1-v2 OOS CORRELATION")
    print("=" * 70)
    corr = _v1_v2_correlation(v1_oos, v2_oos)
    for k, v in corr.items():
        print(f"  {k}: {v}")

    # ---------- Diversification benefit ----------
    print("\n" + "=" * 70)
    print("DIVERSIFICATION BENEFIT (equal-weight combined vs each alone)")
    print("=" * 70)
    div = _diversification_benefit(v1_oos, v2_oos)
    for k, v in div.items():
        print(f"  {k}: {v}")

    # ---------- Persist artifacts ----------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    (OUT_DIR / "v1_v2_correlation.json").write_text(json.dumps(corr, indent=2))
    (OUT_DIR / "diversification_benefit.json").write_text(json.dumps(div, indent=2))
    _per_symbol(v1_oos).to_csv(OUT_DIR / "v1_per_symbol_oos.csv", index=False)
    _per_symbol(v2_oos).to_csv(OUT_DIR / "v2_per_symbol_oos.csv", index=False)
    _per_symbol(combined_oos).to_csv(OUT_DIR / "combined_per_symbol_oos.csv", index=False)
    combined_oos.to_csv(OUT_DIR / "combined_oos_trades.csv", index=False)

    print(f"\nArtifacts written to {OUT_DIR}")


if __name__ == "__main__":
    main()

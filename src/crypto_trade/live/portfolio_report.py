"""Combined v1+v2 portfolio reporter.

Reads v1 and v2 trade DataFrames (or CSVs via the CLI subcommand
``crypto-trade portfolio-report``) and emits a combined tearsheet:
combined Sharpe (monthly + daily), MaxDD, Calmar, total weighted PnL,
per-symbol concentration, per-track decomposition. When ``html_out`` is
given, also writes a small HTML page suitable for sharing.

Backtests for both tracks already produce the inputs this consumes:
  - reports/iteration_186/out_of_sample/trades.csv          (v1)
  - reports-v2/iteration_v2-069/out_of_sample/trades.csv    (v2)

After Task 11's combined parity test passes, the same inputs can be
sourced from the live engine's dry_run.db via _read_closed_trades_from_db.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ReportInputs:
    v1_trades: pd.DataFrame
    v2_trades: pd.DataFrame


@dataclass
class CombinedReport:
    total_trades: int
    v1_trades: int
    v2_trades: int
    combined_weighted_pnl: float
    combined_sharpe_monthly: float
    combined_sharpe_daily: float
    combined_max_drawdown_pct: float
    combined_calmar: float
    per_symbol: dict[str, dict[str, float]] = field(default_factory=dict)
    per_track: dict[str, dict[str, float]] = field(default_factory=dict)


def _monthly_sharpe(t: pd.DataFrame) -> float:
    if t.empty:
        return 0.0
    months = pd.to_datetime(t["close_time"], unit="ms", utc=True).dt.to_period("M")
    m = t.groupby(months)["weighted_pnl"].sum()
    if len(m) < 2 or m.std() == 0:
        return 0.0
    return float(m.mean() / m.std() * np.sqrt(12))


def _daily_sharpe(t: pd.DataFrame) -> float:
    if t.empty:
        return 0.0
    days = pd.to_datetime(t["close_time"], unit="ms", utc=True).dt.floor("D")
    d = t.groupby(days)["weighted_pnl"].sum()
    if len(d) < 2 or d.std() == 0:
        return 0.0
    return float(d.mean() / d.std() * np.sqrt(365))


def _max_dd(t: pd.DataFrame) -> float:
    if t.empty:
        return 0.0
    s = t.sort_values("close_time")["weighted_pnl"].cumsum()
    return float(abs((s - s.cummax()).min()))


def build_combined_report(
    inputs: ReportInputs, html_out: Path | None = None
) -> CombinedReport:
    """Aggregate v1+v2 trades into a CombinedReport. Optionally write HTML."""
    v1 = inputs.v1_trades
    v2 = inputs.v2_trades
    combined = pd.concat([v1, v2], ignore_index=True) if len(v1) or len(v2) else v1.copy()
    pnl_total = float(combined["weighted_pnl"].sum()) if not combined.empty else 0.0
    max_dd = _max_dd(combined)
    monthly_sr = _monthly_sharpe(combined)
    daily_sr = _daily_sharpe(combined)
    calmar = pnl_total / max_dd if max_dd > 0 else 0.0

    per_symbol: dict[str, dict[str, float]] = {}
    if not combined.empty:
        for sym, group in combined.groupby("symbol"):
            wpnl = float(group["weighted_pnl"].sum())
            per_symbol[sym] = {
                "trades": int(group.shape[0]),
                "weighted_pnl": wpnl,
                "share_pct": (wpnl / pnl_total * 100) if pnl_total else 0.0,
            }

    per_track = {
        "v1": {
            "trades": int(len(v1)),
            "weighted_pnl": float(v1["weighted_pnl"].sum()) if not v1.empty else 0.0,
        },
        "v2": {
            "trades": int(len(v2)),
            "weighted_pnl": float(v2["weighted_pnl"].sum()) if not v2.empty else 0.0,
        },
    }

    rep = CombinedReport(
        total_trades=int(len(combined)),
        v1_trades=int(len(v1)),
        v2_trades=int(len(v2)),
        combined_weighted_pnl=pnl_total,
        combined_sharpe_monthly=monthly_sr,
        combined_sharpe_daily=daily_sr,
        combined_max_drawdown_pct=max_dd,
        combined_calmar=calmar,
        per_symbol=per_symbol,
        per_track=per_track,
    )

    if html_out is not None:
        _emit_html(rep, html_out)

    return rep


def _emit_html(r: CombinedReport, path: Path) -> None:
    sym_rows = "".join(
        f"<tr><td>{s}</td><td>{d['trades']}</td>"
        f"<td>{d['weighted_pnl']:.2f}</td><td>{d['share_pct']:.2f}%</td></tr>"
        for s, d in sorted(r.per_symbol.items(), key=lambda kv: -kv[1]["weighted_pnl"])
    )
    track_rows = "".join(
        f"<tr><td>{name}</td><td>{vals['trades']}</td>"
        f"<td>{vals['weighted_pnl']:.2f}</td></tr>"
        for name, vals in r.per_track.items()
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Combined v1+v2 Portfolio</title>"
        "<style>body{font-family:sans-serif;max-width:880px;margin:2em auto;}"
        "table{border-collapse:collapse;margin:1em 0;}"
        "th,td{border:1px solid #ccc;padding:6px 12px;text-align:right;}"
        "th{background:#f4f4f4;}td:first-child,th:first-child{text-align:left;}"
        "</style></head><body>"
        "<h1>Combined v1+v2 Portfolio</h1>"
        "<h2>Headlines</h2>"
        "<ul>"
        f"<li>Total trades: {r.total_trades} (v1: {r.v1_trades}, v2: {r.v2_trades})</li>"
        f"<li>Combined Sharpe (monthly): {r.combined_sharpe_monthly:.4f}</li>"
        f"<li>Combined Sharpe (daily): {r.combined_sharpe_daily:.4f}</li>"
        f"<li>Combined MaxDD (weighted PnL units): {r.combined_max_drawdown_pct:.2f}</li>"
        f"<li>Combined Calmar: {r.combined_calmar:.4f}</li>"
        f"<li>Combined weighted PnL: {r.combined_weighted_pnl:.2f}</li>"
        "</ul>"
        "<h2>Per Track</h2>"
        "<table><tr><th>Track</th><th>Trades</th><th>Weighted PnL</th></tr>"
        f"{track_rows}</table>"
        "<h2>Per Symbol</h2>"
        "<table><tr><th>Symbol</th><th>Trades</th><th>Weighted PnL</th><th>Share</th></tr>"
        f"{sym_rows}</table>"
        "</body></html>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)

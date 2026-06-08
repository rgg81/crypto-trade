"""
iter-v1/082 — BUNDLE-002 ASSEMBLY composition script.

Reads the 4 specialists' trades.csv files (IS + OOS) for:
  - /063 DOT specialist (48-col V1_FEATURE_COLUMNS_PRUNED; IS +1.32 / OOS +1.36)
  - /064 ETH specialist (48-col V1_FEATURE_COLUMNS_PRUNED; IS +0.24 / OOS +0.52)
  - /065 BTC specialist (48-col V1_FEATURE_COLUMNS_PRUNED; IS +0.07 / OOS -0.20)
  - /078 AAVE specialist (49-col PRUNED + excess_ret_5d_vs_majors_z90;
                          IS +0.34 / OOS +0.16; PROMISING-TENTATIVE)

Writes full bundle output to reports-v1/iteration_v1-082/:
  - in_sample/trades.csv           — composed bundle IS trades, sorted by entry timestamp
  - out_of_sample/trades.csv       — composed bundle OOS trades, sorted by entry timestamp
  - in_sample/daily_pnl.csv        — bundle IS daily PnL (trade close date → sum)
  - in_sample/monthly_pnl.csv      — bundle IS monthly PnL
  - in_sample/per_symbol.csv       — per-coin IS contribution
  - in_sample/per_regime.csv       — per-regime IS contribution (regime tag from trades)
  - out_of_sample/daily_pnl.csv    — bundle OOS daily PnL
  - out_of_sample/monthly_pnl.csv  — bundle OOS monthly PnL
  - out_of_sample/per_symbol.csv   — per-coin OOS contribution
  - out_of_sample/per_regime.csv   — per-regime OOS contribution
  - comparison.csv                 — bundle headline metrics (IS / OOS / ratio)

No model training. No Optuna search. Deterministic composition from immutable
git-tracked trade artifacts.

Pairwise-disjoint universe assertion (HARD per feedback_v1_bundle_no_coin_overlap.md):
  /063 → {DOTUSDT}
  /064 → {ETHUSDT}
  /065 → {BTCUSDT}
  /078 → {AAVEUSDT}
  Intersection of any pair = ∅.

BUNDLE-001 anchor (iter-v1/071): IS +0.55 / OOS +0.96 / 537 IS + 230 OOS trades
  (3-component: DOT/063 + ETH/064 + BTC/065)
BUNDLE-002 adds AAVE/078 as 4th component.

N-aware concentration metric (H3 fix from quant-research merge):
  denominator = max(total_oos_pnl, sum_of_positives)
  prevents concentration > 100% when one specialist posts negative OOS PnL.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
REPORTS = REPO / "reports-v1"

SPECIALISTS = [
    ("063", "DOTUSDT"),
    ("064", "ETHUSDT"),
    ("065", "BTCUSDT"),
    ("078", "AAVEUSDT"),
]

BUNDLE_DIR = REPORTS / "iteration_v1-082"
BUNDLE_IS = BUNDLE_DIR / "in_sample"
BUNDLE_OOS = BUNDLE_DIR / "out_of_sample"

TRADES_COLUMNS = [
    "symbol",
    "direction",
    "entry_price",
    "exit_price",
    "weight_factor",
    "open_time",
    "close_time",
    "exit_reason",
    "pnl_pct",
    "fee_pct",
    "net_pnl_pct",
    "weighted_pnl",
    "stop_loss_price",
    "take_profit_price",
    "timeout_time",
    "confidence",
]


# ---------------------------------------------------------------------------
# Helper: load trades from CSV
# ---------------------------------------------------------------------------
def load_trades(path: Path) -> list[dict]:
    with open(path) as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Helper: verify pairwise-disjoint universe
# ---------------------------------------------------------------------------
def verify_disjoint(window: str) -> None:
    symbol_sets: dict[str, set[str]] = {}
    for spec, expected_sym in SPECIALISTS:
        path = REPORTS / f"iteration_v1-{spec}" / window / "trades.csv"
        trades = load_trades(path)
        syms = {t["symbol"] for t in trades}
        # Each specialist must contain ONLY its declared symbol
        assert syms == {expected_sym}, (
            f"DISJOINT VIOLATION: spec={spec} expected={{{expected_sym}}} got={syms}"
        )
        symbol_sets[spec] = syms

    specs = list(symbol_sets.keys())
    for i in range(len(specs)):
        for j in range(i + 1, len(specs)):
            si, sj = symbol_sets[specs[i]], symbol_sets[specs[j]]
            assert si.isdisjoint(sj), (
                f"DISJOINT VIOLATION: spec {specs[i]} ∩ spec {specs[j]} = {si & sj}"
            )
    print(f"  [PASS] Pairwise-disjoint coin universe verified for window={window}")


# ---------------------------------------------------------------------------
# Helper: portfolio metrics from a list of net_pnl_pct values
# ---------------------------------------------------------------------------
def compute_bundle_metrics(pnl_list: list[float]) -> dict:
    n = len(pnl_list)
    if n == 0:
        return {}

    total_pnl = sum(pnl_list)
    wins = [p for p in pnl_list if p > 0]
    losses = [p for p in pnl_list if p < 0]
    win_rate = len(wins) / n * 100
    gross_w = sum(wins)
    gross_l = sum(-p for p in losses)
    profit_factor = gross_w / gross_l if gross_l > 0 else float("inf")
    avg_pnl = total_pnl / n
    variance = sum((p - avg_pnl) ** 2 for p in pnl_list) / n
    std_pnl = math.sqrt(variance) if variance > 0 else 0.0
    per_trade_sharpe = avg_pnl / std_pnl if std_pnl > 0 else 0.0

    return {
        "n": n,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_pnl": avg_pnl,
        "std_pnl": std_pnl,
        "per_trade_sharpe": per_trade_sharpe,
    }


# ---------------------------------------------------------------------------
# Helper: compute monthly Sharpe from a monthly_pnl list
#
# Monthly Sharpe (annualized) = (mean_monthly_return / std_monthly_return) * sqrt(12)
# This is the standard v1 metric used throughout the project.
# ---------------------------------------------------------------------------
def monthly_sharpe(monthly_returns: list[float]) -> float:
    if len(monthly_returns) < 2:
        return float("nan")
    mean_r = sum(monthly_returns) / len(monthly_returns)
    var_r = sum((r - mean_r) ** 2 for r in monthly_returns) / (len(monthly_returns) - 1)
    std_r = math.sqrt(var_r) if var_r > 0 else 0.0
    if std_r == 0:
        return float("nan")
    return (mean_r / std_r) * math.sqrt(12)


def monthly_sortino(monthly_returns: list[float]) -> float:
    """Sortino using downside deviation (negative returns only), annualized."""
    if len(monthly_returns) < 2:
        return float("nan")
    mean_r = sum(monthly_returns) / len(monthly_returns)
    neg_dev_sq = [(min(r, 0.0)) ** 2 for r in monthly_returns]
    downside_var = sum(neg_dev_sq) / (len(monthly_returns) - 1)
    downside_std = math.sqrt(downside_var) if downside_var > 0 else 0.0
    if downside_std == 0:
        return float("nan")
    return (mean_r / downside_std) * math.sqrt(12)


def max_drawdown_pct(cumulative_pnl: list[float]) -> float:
    """
    Compute max drawdown on the cumulative PnL series (as percentage of peak).

    Returns a positive percentage (e.g. 15.0 means 15% drawdown).
    Cumulative PnL is in percentage points, so equity starts at 100 + 0 = 100.
    """
    if not cumulative_pnl:
        return 0.0
    # Equity curve: start at 100, add percentage returns
    equity = 100.0
    peak = equity
    max_dd = 0.0
    for r in cumulative_pnl:
        equity += r
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def calmar_ratio(annualized_return: float, max_dd: float) -> float:
    if max_dd == 0:
        return float("nan")
    return annualized_return / max_dd


# ---------------------------------------------------------------------------
# Helper: ms timestamp → YYYY-MM-DD
# ---------------------------------------------------------------------------
def ms_to_date(ms_str: str) -> str:
    ts = int(ms_str) // 1000
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


def ms_to_month(ms_str: str) -> str:
    ts = int(ms_str) // 1000
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m")


# ---------------------------------------------------------------------------
# Compose bundle trades for one window
# ---------------------------------------------------------------------------
def compose_trades(window: str) -> list[dict]:
    all_trades: list[dict] = []
    for spec, _sym in SPECIALISTS:
        path = REPORTS / f"iteration_v1-{spec}" / window / "trades.csv"
        trades = load_trades(path)
        all_trades.extend(trades)
    # Sort by open_time (entry timestamp ascending)
    all_trades.sort(key=lambda t: int(t["open_time"]))
    return all_trades


# ---------------------------------------------------------------------------
# Write composed trades CSV
# ---------------------------------------------------------------------------
def write_trades(trades: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=TRADES_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trades)


# ---------------------------------------------------------------------------
# Build daily_pnl.csv from trades (close_time → daily PnL)
# ---------------------------------------------------------------------------
def build_daily_pnl(trades: list[dict]) -> list[dict]:
    daily: dict[str, dict] = {}
    for t in trades:
        date = ms_to_date(t["close_time"])
        if date not in daily:
            daily[date] = {"date": date, "pnl_pct": 0.0, "trade_count": 0}
        daily[date]["pnl_pct"] += float(t["net_pnl_pct"])
        daily[date]["trade_count"] += 1
    return sorted(daily.values(), key=lambda r: r["date"])


def write_daily_pnl(daily_rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "pnl_pct", "trade_count"])
        writer.writeheader()
        writer.writerows(daily_rows)


# ---------------------------------------------------------------------------
# Build monthly_pnl.csv from trades
# ---------------------------------------------------------------------------
def build_monthly_pnl(trades: list[dict]) -> list[dict]:
    monthly: dict[str, dict] = {}
    for t in trades:
        month = ms_to_month(t["close_time"])
        if month not in monthly:
            monthly[month] = {"month": month, "pnl_pct": 0.0, "trade_count": 0}
        monthly[month]["pnl_pct"] += float(t["net_pnl_pct"])
        monthly[month]["trade_count"] += 1
    return sorted(monthly.values(), key=lambda r: r["month"])


def write_monthly_pnl(monthly_rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["month", "pnl_pct", "trade_count"])
        writer.writeheader()
        writer.writerows(monthly_rows)


# ---------------------------------------------------------------------------
# Build per_symbol.csv
# ---------------------------------------------------------------------------
def build_per_symbol(trades: list[dict]) -> list[dict]:
    sym_data: dict[str, dict] = defaultdict(lambda: {"trades": 0, "wins": 0, "net_pnl_pct": 0.0})
    for t in trades:
        sym = t["symbol"]
        net = float(t["net_pnl_pct"])
        sym_data[sym]["trades"] += 1
        sym_data[sym]["wins"] += 1 if net > 0 else 0
        sym_data[sym]["net_pnl_pct"] += net

    total_pnl = sum(d["net_pnl_pct"] for d in sym_data.values())

    rows = []
    for sym, d in sorted(sym_data.items()):
        n = d["trades"]
        wr = d["wins"] / n * 100 if n else 0.0
        avg = d["net_pnl_pct"] / n if n else 0.0
        pct_total = d["net_pnl_pct"] / total_pnl * 100 if total_pnl != 0 else 0.0
        rows.append(
            {
                "symbol": sym,
                "trades": n,
                "wins": d["wins"],
                "win_rate": round(wr, 1),
                "net_pnl_pct": round(d["net_pnl_pct"], 4),
                "avg_pnl_pct": round(avg, 4),
                "pct_of_total_pnl": round(pct_total, 2),
            }
        )
    return rows


def write_per_symbol(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "symbol",
        "trades",
        "wins",
        "win_rate",
        "net_pnl_pct",
        "avg_pnl_pct",
        "pct_of_total_pnl",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Build per_regime.csv from trades
# Regime tag is read from the "regime" column if present; falls back to "N/A".
# ---------------------------------------------------------------------------
def build_per_regime(trades: list[dict]) -> list[dict]:
    regime_data: dict[str, dict] = defaultdict(lambda: {"trades": 0, "wins": 0, "net_pnl_pct": 0.0})
    has_regime = trades and "regime" in trades[0]
    for t in trades:
        regime = t.get("regime", "N/A") if has_regime else "N/A"
        net = float(t["net_pnl_pct"])
        regime_data[regime]["trades"] += 1
        regime_data[regime]["wins"] += 1 if net > 0 else 0
        regime_data[regime]["net_pnl_pct"] += net

    total_pnl = sum(d["net_pnl_pct"] for d in regime_data.values())

    rows = []
    for regime, d in sorted(regime_data.items()):
        n = d["trades"]
        wr = d["wins"] / n * 100 if n else 0.0
        avg = d["net_pnl_pct"] / n if n else 0.0
        pct_total = d["net_pnl_pct"] / total_pnl * 100 if total_pnl != 0 else 0.0
        rows.append(
            {
                "regime": regime,
                "trades": n,
                "wins": d["wins"],
                "win_rate": round(wr, 1),
                "net_pnl_pct": round(d["net_pnl_pct"], 4),
                "avg_pnl_pct": round(avg, 4),
                "pct_of_total_pnl": round(pct_total, 2),
            }
        )
    return rows


def write_per_regime(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "regime",
        "trades",
        "wins",
        "win_rate",
        "net_pnl_pct",
        "avg_pnl_pct",
        "pct_of_total_pnl",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Compute headline metrics for one window
# ---------------------------------------------------------------------------
def compute_headline(trades: list[dict], monthly_rows: list[dict]) -> dict:
    pnl_list = [float(t["net_pnl_pct"]) for t in trades]
    monthly_ret = [r["pnl_pct"] for r in monthly_rows]

    m = compute_bundle_metrics(pnl_list)
    sharpe = monthly_sharpe(monthly_ret)
    sortino = monthly_sortino(monthly_ret)

    # Max drawdown on cumulative PnL (trade-ordered, sorted by close_time)
    trades_by_close = sorted(trades, key=lambda t: int(t["close_time"]))
    pnl_ordered = [float(t["net_pnl_pct"]) for t in trades_by_close]
    mdd = max_drawdown_pct(pnl_ordered)

    # Total net PnL (sum of net_pnl_pct for all trades — portfolio perspective)
    total_pnl = sum(pnl_list)

    # Annualized return: use mean_monthly * 12
    mean_monthly = sum(monthly_ret) / len(monthly_ret) if monthly_ret else 0.0
    ann_return = mean_monthly * 12
    calmar = calmar_ratio(ann_return, mdd)

    return {
        "n_trades": m["n"],
        "total_pnl": total_pnl,
        "win_rate": m["win_rate"],
        "profit_factor": m["profit_factor"],
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown_pct": mdd,
        "calmar": calmar,
    }


# ---------------------------------------------------------------------------
# Write comparison.csv
# ---------------------------------------------------------------------------
def write_comparison(
    is_metrics: dict, oos_metrics: dict, per_sym_oos: list[dict], path: Path
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def ratio(a, b):
        if b == 0 or (isinstance(b, float) and math.isnan(b)):
            return "N/A"
        if isinstance(a, float) and math.isnan(a):
            return "N/A"
        return round(a / b, 4)

    def fmt_pct(v):
        if isinstance(v, float) and math.isnan(v):
            return "nan"
        return f"{v:.2f}%"

    # Top-symbol concentration (OOS) — N-aware (H3 fix).
    # When sign-mixed PnL is present, total_oos_pnl < sum_of_positives because
    # losers partially cancel winners.  Dividing top_sym_pnl by the net total
    # then yields concentration > 100%, which is a meaningless artifact.
    # Fix: denominator = max(total_oos_pnl, sum_of_positives) so that
    # concentration is always <= 100% even when one specialist is negative.
    total_oos_pnl = sum(r["net_pnl_pct"] for r in per_sym_oos)
    sum_of_positives = sum(r["net_pnl_pct"] for r in per_sym_oos if r["net_pnl_pct"] > 0)
    top_sym_pnl = max((r["net_pnl_pct"] for r in per_sym_oos), default=0.0)
    _conc_denom = max(total_oos_pnl, sum_of_positives)
    top_sym_conc = top_sym_pnl / _conc_denom * 100 if _conc_denom != 0 else 0.0

    rows = [
        {
            "metric": "monthly_sharpe",
            "in_sample": round(is_metrics["sharpe"], 4)
            if not math.isnan(is_metrics["sharpe"])
            else "nan",
            "out_of_sample": round(oos_metrics["sharpe"], 4)
            if not math.isnan(oos_metrics["sharpe"])
            else "nan",
            "ratio": ratio(oos_metrics["sharpe"], is_metrics["sharpe"]),
        },
        {
            "metric": "monthly_sortino",
            "in_sample": round(is_metrics["sortino"], 4)
            if not math.isnan(is_metrics["sortino"])
            else "nan",
            "out_of_sample": round(oos_metrics["sortino"], 4)
            if not math.isnan(oos_metrics["sortino"])
            else "nan",
            "ratio": ratio(oos_metrics["sortino"], is_metrics["sortino"]),
        },
        {
            "metric": "max_drawdown",
            "in_sample": fmt_pct(is_metrics["max_drawdown_pct"]),
            "out_of_sample": fmt_pct(oos_metrics["max_drawdown_pct"]),
            "ratio": ratio(oos_metrics["max_drawdown_pct"], is_metrics["max_drawdown_pct"]),
        },
        {
            "metric": "win_rate",
            "in_sample": fmt_pct(is_metrics["win_rate"]),
            "out_of_sample": fmt_pct(oos_metrics["win_rate"]),
            "ratio": ratio(oos_metrics["win_rate"], is_metrics["win_rate"]),
        },
        {
            "metric": "profit_factor",
            "in_sample": round(is_metrics["profit_factor"], 4),
            "out_of_sample": round(oos_metrics["profit_factor"], 4),
            "ratio": ratio(oos_metrics["profit_factor"], is_metrics["profit_factor"]),
        },
        {
            "metric": "total_trades",
            "in_sample": is_metrics["n_trades"],
            "out_of_sample": oos_metrics["n_trades"],
            "ratio": ratio(oos_metrics["n_trades"], is_metrics["n_trades"]),
        },
        {
            "metric": "total_net_pnl",
            "in_sample": round(is_metrics["total_pnl"], 4),
            "out_of_sample": round(oos_metrics["total_pnl"], 4),
            "ratio": ratio(oos_metrics["total_pnl"], is_metrics["total_pnl"]),
        },
        {
            "metric": "calmar_ratio",
            "in_sample": round(is_metrics["calmar"], 4)
            if not (isinstance(is_metrics["calmar"], float) and math.isnan(is_metrics["calmar"]))
            else "nan",
            "out_of_sample": round(oos_metrics["calmar"], 4)
            if not (isinstance(oos_metrics["calmar"], float) and math.isnan(oos_metrics["calmar"]))
            else "nan",
            "ratio": ratio(oos_metrics["calmar"], is_metrics["calmar"]),
        },
        {
            "metric": "top_symbol_concentration_oos_pct",
            "in_sample": "N/A",
            "out_of_sample": round(top_sym_conc, 2),
            "ratio": "N/A",
        },
    ]

    # Per-symbol section
    rows.append(
        {
            "metric": "--- per_symbol (OOS) ---",
            "in_sample": "",
            "out_of_sample": "",
            "ratio": "",
        }
    )
    for r in sorted(per_sym_oos, key=lambda x: -x["net_pnl_pct"]):
        rows.append(
            {
                "metric": f"oos_pnl_{r['symbol']}",
                "in_sample": "N/A",
                "out_of_sample": round(r["net_pnl_pct"], 4),
                "ratio": round(r["pct_of_total_pnl"], 2),
            }
        )

    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "in_sample", "out_of_sample", "ratio"])
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== BUNDLE-002 ASSEMBLY — iter-v1/082 ===")
    print()
    print("Components:")
    print("  /063 DOT  — 48-col V1_FEATURE_COLUMNS_PRUNED (IS +1.32 / OOS +1.36)")
    print("  /064 ETH  — 48-col V1_FEATURE_COLUMNS_PRUNED (IS +0.24 / OOS +0.52)")
    print("  /065 BTC  — 48-col V1_FEATURE_COLUMNS_PRUNED (IS +0.07 / OOS -0.20)")
    print("  /078 AAVE — 49-col PRUNED + excess_ret_5d_vs_majors_z90")
    print("              (IS +0.34 / OOS +0.16; PROMISING-TENTATIVE)")
    print()
    print("Anchor: BUNDLE-001 /071 — IS +0.55 / OOS +0.96 / 537 IS + 230 OOS trades")
    print()

    # Step 1: verify pairwise-disjoint coin universe
    print("[1] Pairwise-disjoint universe check ...")
    verify_disjoint("in_sample")
    verify_disjoint("out_of_sample")
    print()

    # Step 2: compose bundle trades
    print("[2] Composing bundle trades ...")
    is_trades = compose_trades("in_sample")
    oos_trades = compose_trades("out_of_sample")
    print(f"  IS  trades: {len(is_trades)}")
    print(f"  OOS trades: {len(oos_trades)}")
    print()

    # Step 3: write composed trades CSVs
    print("[3] Writing bundle trade files ...")
    write_trades(is_trades, BUNDLE_IS / "trades.csv")
    write_trades(oos_trades, BUNDLE_OOS / "trades.csv")
    print(f"  Wrote: {BUNDLE_IS / 'trades.csv'}")
    print(f"  Wrote: {BUNDLE_OOS / 'trades.csv'}")
    print()

    # Step 4: build + write daily_pnl
    print("[4] Building daily_pnl ...")
    is_daily = build_daily_pnl(is_trades)
    oos_daily = build_daily_pnl(oos_trades)
    write_daily_pnl(is_daily, BUNDLE_IS / "daily_pnl.csv")
    write_daily_pnl(oos_daily, BUNDLE_OOS / "daily_pnl.csv")
    print(f"  IS  daily days: {len(is_daily)}")
    print(f"  OOS daily days: {len(oos_daily)}")
    print()

    # Step 5: build + write monthly_pnl
    print("[5] Building monthly_pnl ...")
    is_monthly = build_monthly_pnl(is_trades)
    oos_monthly = build_monthly_pnl(oos_trades)
    write_monthly_pnl(is_monthly, BUNDLE_IS / "monthly_pnl.csv")
    write_monthly_pnl(oos_monthly, BUNDLE_OOS / "monthly_pnl.csv")
    print(f"  IS  months: {len(is_monthly)}")
    print(f"  OOS months: {len(oos_monthly)}")
    print()

    # Step 6: build + write per_symbol
    print("[6] Building per_symbol ...")
    is_per_sym = build_per_symbol(is_trades)
    oos_per_sym = build_per_symbol(oos_trades)
    write_per_symbol(is_per_sym, BUNDLE_IS / "per_symbol.csv")
    write_per_symbol(oos_per_sym, BUNDLE_OOS / "per_symbol.csv")
    print("  IS  per_symbol:")
    for r in is_per_sym:
        sym_line = (
            f"    {r['symbol']:<12}  trades={r['trades']:>3}"
            f"  net_pnl={r['net_pnl_pct']:>8.4f}%  share={r['pct_of_total_pnl']:>6.2f}%"
        )
        print(sym_line)
    print("  OOS per_symbol:")
    for r in oos_per_sym:
        sym_line = (
            f"    {r['symbol']:<12}  trades={r['trades']:>3}"
            f"  net_pnl={r['net_pnl_pct']:>8.4f}%  share={r['pct_of_total_pnl']:>6.2f}%"
        )
        print(sym_line)
    print()

    # Step 7: build + write per_regime
    print("[7] Building per_regime ...")
    is_per_regime = build_per_regime(is_trades)
    oos_per_regime = build_per_regime(oos_trades)
    write_per_regime(is_per_regime, BUNDLE_IS / "per_regime.csv")
    write_per_regime(oos_per_regime, BUNDLE_OOS / "per_regime.csv")
    print(f"  IS  regime rows: {len(is_per_regime)}")
    print(f"  OOS regime rows: {len(oos_per_regime)}")
    print()

    # Step 8: compute headline metrics
    print("[8] Computing headline metrics ...")
    is_metrics = compute_headline(is_trades, is_monthly)
    oos_metrics = compute_headline(oos_trades, oos_monthly)

    def _fmt(v):
        if isinstance(v, float) and math.isnan(v):
            return "nan"
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)

    print(f"  {'Metric':<30}  {'IS':>10}  {'OOS':>10}")
    print(f"  {'-' * 52}")
    keys = [
        "n_trades",
        "total_pnl",
        "win_rate",
        "profit_factor",
        "sharpe",
        "sortino",
        "max_drawdown_pct",
        "calmar",
    ]
    for key in keys:
        print(f"  {key:<30}  {_fmt(is_metrics[key]):>10}  {_fmt(oos_metrics[key]):>10}")
    print()

    # Step 9: write comparison.csv
    print("[9] Writing comparison.csv ...")
    write_comparison(is_metrics, oos_metrics, oos_per_sym, BUNDLE_DIR / "comparison.csv")
    print(f"  Wrote: {BUNDLE_DIR / 'comparison.csv'}")
    print()

    # Step 10: per-specialist summary cross-check
    print("[10] Per-specialist cross-check (n_trades) ...")
    for spec, sym in SPECIALISTS:
        is_n = sum(1 for t in is_trades if t["symbol"] == sym)
        oos_n = sum(1 for t in oos_trades if t["symbol"] == sym)
        print(f"  spec={spec}  sym={sym:<12}  IS={is_n:>3}  OOS={oos_n:>3}")
    print()

    # Step 11: top-symbol concentration (OOS) — N-aware (H3 fix).
    total_oos_pnl = sum(r["net_pnl_pct"] for r in oos_per_sym)
    _sum_pos = sum(r["net_pnl_pct"] for r in oos_per_sym if r["net_pnl_pct"] > 0)
    top = max(oos_per_sym, key=lambda r: r["net_pnl_pct"])
    _top_denom = max(total_oos_pnl, _sum_pos)
    top_conc = top["net_pnl_pct"] / _top_denom * 100 if _top_denom != 0 else 0.0
    print(f"[11] Top-symbol OOS concentration: {top['symbol']} = {top_conc:.2f}% of OOS PnL")
    print()

    print("=== DONE ===")
    print()
    print("Bundle-002 headline (IS / OOS):")
    print(f"  Monthly Sharpe   : {_fmt(is_metrics['sharpe'])} / {_fmt(oos_metrics['sharpe'])}")
    print(f"  Monthly Sortino  : {_fmt(is_metrics['sortino'])} / {_fmt(oos_metrics['sortino'])}")
    is_mdd = is_metrics["max_drawdown_pct"]
    oos_mdd = oos_metrics["max_drawdown_pct"]
    print(f"  Max Drawdown     : {is_mdd:.2f}% / {oos_mdd:.2f}%")
    print(f"  Calmar Ratio     : {_fmt(is_metrics['calmar'])} / {_fmt(oos_metrics['calmar'])}")
    print(f"  Win Rate         : {is_metrics['win_rate']:.2f}% / {oos_metrics['win_rate']:.2f}%")
    print(
        f"  Profit Factor    : {is_metrics['profit_factor']:.4f}"
        f" / {oos_metrics['profit_factor']:.4f}"
    )
    print(f"  Total Trades     : {is_metrics['n_trades']} / {oos_metrics['n_trades']}")
    print(f"  Total Net PnL    : {is_metrics['total_pnl']:.4f}% / {oos_metrics['total_pnl']:.4f}%")
    print(f"  Top-sym conc OOS : {top_conc:.2f}% ({top['symbol']})")
    print()
    print("vs BUNDLE-001 anchor (/071): IS +0.55 / OOS +0.96 / 537 IS + 230 OOS trades")


if __name__ == "__main__":
    main()

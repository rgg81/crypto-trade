"""Regime decomposition of iter-v1/040 vs BASELINE_V1 IS performance.

Per user directive 2026-05-31: IS-strong / OOS-weak models are NOT necessarily
overfit — they may be REGIME-SPECIALISTS that perform better under specific IS
regimes. Combining models that specialize on different regimes is the goal.

This script:
1. Loads monthly_pnl.csv from iter-v1/040 and iter-v1-baseline (IS side).
2. Per-trade attribution from trades.csv (joined on open_time → year-month).
3. Buckets IS months into named regime cohorts.
4. Computes Sharpe-proxy (mean_monthly_pnl / std_monthly_pnl, NOT annualized for
   small-N regime windows; we want the SIGN + MAGNITUDE comparison, not the
   absolute-Sharpe number).
5. Writes regime_decomposition.csv: year-month × baseline_pnl_pct ×
   v040_pnl_pct × delta × baseline_trades × v040_trades.
6. Prints regime aggregates: total PnL + monthly-Sharpe-proxy + symbol-attribution.

IS-only. OOS_CUTOFF_DATE = 2025-03-24 enforced upstream (monthly_pnl.csv
under in_sample/ is pre-filtered).
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


REPO = Path(__file__).resolve().parents[2]
V040_DIR = REPO / "reports-v1" / "iteration_v1-040" / "in_sample"
BASE_DIR = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample"
OUT_CSV = Path(__file__).parent / "regime_decomposition.csv"

# IS regime cohort definitions (year-month buckets).
# All ranges are IS-side; OOS_CUTOFF_DATE = 2025-03-24 keeps 2025-Q1 IS-only
# for the baseline (the IS window extends through 2024-12 for the standard
# 24-month walk-forward, but monthly_pnl reports all IS months produced).
REGIMES = {
    "2020-bull": [],  # placeholder, see below — IS starts 2022-01 in v1 data
    "2022-bear": [f"2022-{m:02d}" for m in range(1, 13)],
    "2023-Q1Q2-chop": [f"2023-{m:02d}" for m in range(1, 7)],
    "2023-Q3Q4-recovery": [f"2023-{m:02d}" for m in range(7, 13)],
    "2024-Q1Q2-bull": [f"2024-{m:02d}" for m in range(1, 7)],
    "2024-Q3Q4-transition": [f"2024-{m:02d}" for m in range(7, 13)],
    "2025-Q1-IS-tail": ["2025-01", "2025-02", "2025-03"],
}
# Remove placeholder; v1 IS data starts 2022-01 (24-month training window for
# 2024-01 OOS-cutoff → 2022-01 first IS month).
del REGIMES["2020-bull"]


def load_monthly_pnl(path: Path) -> dict[str, tuple[float, int]]:
    """Return {ym: (pnl_pct, trade_count)}."""
    out: dict[str, tuple[float, int]] = {}
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            out[row["month"]] = (float(row["pnl_pct"]), int(row["trade_count"]))
    return out


def load_trades_by_symbol_month(
    path: Path,
) -> dict[tuple[str, str], tuple[float, int]]:
    """Return {(year_month, symbol): (cumulative_net_pnl_pct, trade_count)}."""
    out: dict[tuple[str, str], list[float]] = defaultdict(list)
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # open_time is ms epoch
            open_ms = int(row["open_time"])
            ym = _ms_to_year_month(open_ms)
            sym = row["symbol"]
            net = float(row["net_pnl_pct"])
            out[(ym, sym)].append(net)
    return {k: (sum(v), len(v)) for k, v in out.items()}


def _ms_to_year_month(ms: int) -> str:
    # Avoid pulling pandas. Compute via datetime stdlib.
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return f"{dt.year}-{dt.month:02d}"


def sharpe_proxy(pnls: list[float]) -> float:
    """Mean / std on the monthly series. Not annualized; sign + magnitude only.

    Returns 0.0 if n < 2 or std == 0.
    """
    if len(pnls) < 2:
        return 0.0
    sd = stdev(pnls)
    if sd == 0:
        return 0.0
    return mean(pnls) / sd


def main() -> None:
    v040_monthly = load_monthly_pnl(V040_DIR / "monthly_pnl.csv")
    base_monthly = load_monthly_pnl(BASE_DIR / "monthly_pnl.csv")
    v040_sym = load_trades_by_symbol_month(V040_DIR / "trades.csv")
    base_sym = load_trades_by_symbol_month(BASE_DIR / "trades.csv")

    all_months = sorted(set(v040_monthly) | set(base_monthly))

    # === Per-month CSV ===
    rows: list[dict] = []
    for ym in all_months:
        v_pnl, v_n = v040_monthly.get(ym, (0.0, 0))
        b_pnl, b_n = base_monthly.get(ym, (0.0, 0))
        regime = _classify(ym)
        rows.append(
            {
                "year_month": ym,
                "regime": regime,
                "v040_pnl_pct": round(v_pnl, 4),
                "baseline_pnl_pct": round(b_pnl, 4),
                "delta_pnl_pct": round(v_pnl - b_pnl, 4),
                "v040_trades": v_n,
                "baseline_trades": b_n,
            }
        )
    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} monthly rows to {OUT_CSV}")

    # === Regime aggregates ===
    print("\n=== REGIME AGGREGATES (IS-only) ===\n")
    print(
        f"{'regime':<25} {'months':<7} {'v040_pnl':<10} {'base_pnl':<10} "
        f"{'delta_pnl':<10} {'v040_sharpe':<13} {'base_sharpe':<13} {'verdict':<25}"
    )
    print("-" * 130)
    regime_winners: dict[str, str] = {}
    for regime_name, regime_months in REGIMES.items():
        v_series = [v040_monthly.get(ym, (0.0, 0))[0] for ym in regime_months]
        b_series = [base_monthly.get(ym, (0.0, 0))[0] for ym in regime_months]
        v_total = sum(v_series)
        b_total = sum(b_series)
        v_sh = sharpe_proxy(v_series)
        b_sh = sharpe_proxy(b_series)
        delta_sh = v_sh - b_sh
        if v_total > b_total and delta_sh > 0:
            verdict = "/040 WINS (cleaner)"
        elif v_total > b_total:
            verdict = "/040 WINS PnL (noisier)"
        elif b_total > v_total and delta_sh < 0:
            verdict = "BASELINE WINS"
        else:
            verdict = "tie/marginal"
        regime_winners[regime_name] = verdict
        print(
            f"{regime_name:<25} {len(regime_months):<7} "
            f"{v_total:>+9.2f}  {b_total:>+9.2f}  "
            f"{v_total - b_total:>+9.2f}  "
            f"{v_sh:>+12.4f}  {b_sh:>+12.4f}  {verdict:<25}"
        )

    # === Per-symbol within each regime where /040 wins ===
    print("\n=== PER-SYMBOL ATTRIBUTION WITHIN /040-WINNING REGIMES ===\n")
    for regime_name, verdict in regime_winners.items():
        if not verdict.startswith("/040 WINS"):
            continue
        print(f"\n--- {regime_name} ({verdict}) ---")
        sym_v040 = defaultdict(lambda: [0.0, 0])
        sym_base = defaultdict(lambda: [0.0, 0])
        for ym in REGIMES[regime_name]:
            for sym in ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"):
                if (ym, sym) in v040_sym:
                    p, n = v040_sym[(ym, sym)]
                    sym_v040[sym][0] += p
                    sym_v040[sym][1] += n
                if (ym, sym) in base_sym:
                    p, n = base_sym[(ym, sym)]
                    sym_base[sym][0] += p
                    sym_base[sym][1] += n
        print(f"  {'symbol':<10} {'v040_pnl':>10} {'base_pnl':>10} {'delta':>10} "
              f"{'v040_n':>7} {'base_n':>7}")
        for sym in sorted(sym_v040.keys()):
            vp, vn = sym_v040[sym]
            bp, bn = sym_base[sym]
            print(f"  {sym:<10} {vp:>+10.2f} {bp:>+10.2f} {vp - bp:>+10.2f} "
                  f"{vn:>7} {bn:>7}")

    # === Full-IS aggregates (sanity check vs diary headline) ===
    print("\n=== FULL-IS AGGREGATES (sanity check) ===")
    v040_total = sum(v040_monthly[ym][0] for ym in v040_monthly)
    base_total = sum(base_monthly[ym][0] for ym in base_monthly)
    v040_sh = sharpe_proxy([v040_monthly[ym][0] for ym in sorted(v040_monthly)])
    base_sh = sharpe_proxy([base_monthly[ym][0] for ym in sorted(base_monthly)])
    print(f"  /040  total IS PnL = {v040_total:+.2f}%  monthly-sharpe-proxy = {v040_sh:+.4f}")
    print(f"  base  total IS PnL = {base_total:+.2f}%  monthly-sharpe-proxy = {base_sh:+.4f}")
    print(f"  Δ     PnL = {v040_total - base_total:+.2f}%  Δ sharpe-proxy = "
          f"{v040_sh - base_sh:+.4f}")


def _classify(ym: str) -> str:
    for regime_name, months in REGIMES.items():
        if ym in months:
            return regime_name
    return "uncategorized"


if __name__ == "__main__":
    sys.exit(main())

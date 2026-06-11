"""
iter-v1/089 — LOAD-BEARING bundle-fit gate for XRP/088.

Computes TRADE-LEVEL (daily-aggregated) PnL correlation of the XRP/088
specialist vs each BUNDLE-002 cohort member (DOT, ETH, BTC, AAVE).

Decision (pre-committed):
    avg IS trade-PnL corr < 0.5  -> XRP EARNS BUNDLE-003 SEAT (genuine diversifier)
    avg IS trade-PnL corr >= 0.5 -> DIVERSIFIER-DEGENERATE (no seat)

Trade-stream proxy = per-symbol weighted_pnl aggregated to UTC calendar day
(by close_time). Trades fire at different times so daily aggregation is the
correct alignment for cross-stream correlation. Verified that aggregating
weighted_pnl by close-day exactly reproduces the engine's daily_pnl.csv.

SOURCES (the specialist AS IT FIRES IN THE BUNDLE):
  - Cohort members: BUNDLE-002 assembly run
    reports-v1/iteration_v1-082/{in,out}_of_sample/trades.csv,
    partitioned by symbol. Verified per-symbol IS trade counts match the
    individual specialist runs that compose the bundle:
       DOT  /063 = 149 == /082-DOT  = 149
       ETH  /064 = 198 == /082-ETH  = 198
       BTC  /065 = 190 == /082-BTC  = 190
       AAVE /078 = 157 == /082-AAVE = 157   (/081 had 135 -> NOT the bundled AAVE)
    Using /082 directly removes any ambiguity about which specialist version is
    in the bundle.
  - XRP: reports-v1/iteration_v1-088/{in,out}_of_sample/trades.csv (standalone
    specialist; XRP is not in BUNDLE-002).

IS-ONLY decision; OOS computed for information only. Read-only, no backtest.
"""

import csv
import datetime
from collections import defaultdict

import numpy as np

REPORTS = "reports-v1"
OOS_CUTOFF = datetime.date(2025, 3, 24)  # sacred constant; close-day < cutoff => IS

BUNDLE_RUN = f"{REPORTS}/iteration_v1-082"  # combined per-symbol trades for cohort
XRP_RUN = f"{REPORTS}/iteration_v1-088"

COHORT = ["DOTUSDT", "ETHUSDT", "BTCUSDT", "AAVEUSDT"]
XRP = "XRPUSDT"

SOURCES = {
    "XRPUSDT": (f"{XRP_RUN}/in_sample/trades.csv", f"{XRP_RUN}/out_of_sample/trades.csv"),
    "DOTUSDT": (f"{BUNDLE_RUN}/in_sample/trades.csv", f"{BUNDLE_RUN}/out_of_sample/trades.csv"),
    "ETHUSDT": (f"{BUNDLE_RUN}/in_sample/trades.csv", f"{BUNDLE_RUN}/out_of_sample/trades.csv"),
    "BTCUSDT": (f"{BUNDLE_RUN}/in_sample/trades.csv", f"{BUNDLE_RUN}/out_of_sample/trades.csv"),
    "AAVEUSDT": (f"{BUNDLE_RUN}/in_sample/trades.csv", f"{BUNDLE_RUN}/out_of_sample/trades.csv"),
}


def daily_pnl_by_symbol(path, symbol):
    """Aggregate weighted_pnl to UTC calendar day for one symbol from a trades.csv.

    Returns {date: summed_weighted_pnl}. Partitioning by close-day is what the
    engine's daily_pnl.csv does (verified bit-identical for XRP/088 IS).
    """
    day_pnl = defaultdict(float)
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["symbol"] != symbol:
                continue
            close_day = datetime.datetime.fromtimestamp(
                int(row["close_time"]) / 1000, datetime.UTC
            ).date()
            day_pnl[close_day] += float(row["weighted_pnl"])
    return dict(day_pnl)


def split_window(day_pnl):
    """Split a {date: pnl} dict into (IS, OOS) on the OOS_CUTOFF close-day rule."""
    is_d = {d: v for d, v in day_pnl.items() if d < OOS_CUTOFF}
    oos_d = {d: v for d, v in day_pnl.items() if d >= OOS_CUTOFF}
    return is_d, oos_d


def load_symbol(symbol):
    """Load full {date:pnl} from a symbol's IS + OOS trade files, then re-split.

    The /082 combined trades.csv mixes IS/OOS via the in_sample / out_of_sample
    file separation already, but a few trades close just past the cutoff. We
    pull both files, merge, then re-split on the strict close-day rule so the
    cut is identical for every symbol regardless of file boundary quirks.
    """
    is_path, oos_path = SOURCES[symbol]
    merged = defaultdict(float)
    for path in (is_path, oos_path):
        for d, v in daily_pnl_by_symbol(path, symbol).items():
            merged[d] += v
    return split_window(dict(merged))


def pearson(a, b):
    if len(a) < 2:
        return float("nan")
    sa, sb = np.std(a), np.std(b)
    if sa == 0 or sb == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def aligned_corr(xrp_d, other_d):
    """Inner-join two {date:pnl} dicts on common days; Pearson + common-day count."""
    common = sorted(set(xrp_d) & set(other_d))
    xa = np.array([xrp_d[d] for d in common])
    oa = np.array([other_d[d] for d in common])
    return pearson(xa, oa), len(common)


def equal_weight_cohort(cohort_dicts):
    """EW cohort daily PnL: mean across the cohort members present on each day."""
    all_days = set()
    for d in cohort_dicts.values():
        all_days |= set(d)
    ew = {}
    for day in all_days:
        vals = [d[day] for d in cohort_dicts.values() if day in d]
        ew[day] = float(np.mean(vals))  # mean over members that traded that day
    return ew


def zerofill_corr(xrp_d, other_d, all_days):
    """Correlation over the union of active days, missing day = 0 PnL (flat day).

    A flat (no-trade) day is a real, informative observation for a daily PnL
    stream, so zero-fill gives a denser, less overlap-sensitive estimate than
    the co-trading-day inner join. Robustness companion to aligned_corr.
    """
    xa = np.array([xrp_d.get(d, 0.0) for d in all_days])
    oa = np.array([other_d.get(d, 0.0) for d in all_days])
    return pearson(xa, oa), len(all_days)


def run_window(label, xrp_d, cohort_dicts):
    rows = []
    per_member = {}
    # Union of all active days (XRP + cohort) for the zero-fill robustness pass.
    union_days = set(xrp_d)
    for d in cohort_dicts.values():
        union_days |= set(d)
    union_days = sorted(union_days)
    zf_member = {}
    for sym in COHORT:
        corr, n = aligned_corr(xrp_d, cohort_dicts[sym])
        per_member[sym] = (corr, n)
        zcorr, zn = zerofill_corr(xrp_d, cohort_dicts[sym], union_days)
        zf_member[sym] = (zcorr, zn)
        rows.append(
            {
                "window": label,
                "pair": f"XRP_vs_{sym[:-4]}",
                "pearson_corr": round(corr, 4),
                "common_days": n,
            }
        )
        rows.append(
            {
                "window": f"{label}_zerofill",
                "pair": f"XRP_vs_{sym[:-4]}",
                "pearson_corr": round(zcorr, 4),
                "common_days": zn,
            }
        )
    member_corrs = [per_member[s][0] for s in COHORT]
    avg_pair = float(np.nanmean(member_corrs))
    rows.append(
        {
            "window": label,
            "pair": "AVG_PAIRWISE",
            "pearson_corr": round(avg_pair, 4),
            "common_days": "",
        }
    )
    zf_corrs = [zf_member[s][0] for s in COHORT]
    zf_avg = float(np.nanmean(zf_corrs))
    rows.append(
        {
            "window": f"{label}_zerofill",
            "pair": "AVG_PAIRWISE",
            "pearson_corr": round(zf_avg, 4),
            "common_days": len(union_days),
        }
    )
    ew = equal_weight_cohort(cohort_dicts)
    ew_corr, ew_n = aligned_corr(xrp_d, ew)
    rows.append(
        {
            "window": label,
            "pair": "XRP_vs_EW_COHORT",
            "pearson_corr": round(ew_corr, 4),
            "common_days": ew_n,
        }
    )
    ew_zf_corr, ew_zf_n = zerofill_corr(xrp_d, ew, union_days)
    rows.append(
        {
            "window": f"{label}_zerofill",
            "pair": "XRP_vs_EW_COHORT",
            "pearson_corr": round(ew_zf_corr, 4),
            "common_days": ew_zf_n,
        }
    )
    return rows, avg_pair, per_member, (ew_corr, ew_n), zf_member, zf_avg, (ew_zf_corr, ew_zf_n)


def main():
    # Load all five symbols, split IS/OOS.
    is_dicts, oos_dicts = {}, {}
    for sym in [XRP] + COHORT:
        is_d, oos_d = load_symbol(sym)
        is_dicts[sym] = is_d
        oos_dicts[sym] = oos_d

    xrp_is = is_dicts[XRP]
    xrp_oos = oos_dicts[XRP]
    cohort_is = {s: is_dicts[s] for s in COHORT}
    cohort_oos = {s: oos_dicts[s] for s in COHORT}

    (is_rows, is_avg, is_member, is_ew, is_zf_member, is_zf_avg, is_zf_ew) = run_window(
        "IS", xrp_is, cohort_is
    )
    (oos_rows, oos_avg, oos_member, oos_ew, oos_zf_member, oos_zf_avg, oos_zf_ew) = run_window(
        "OOS", xrp_oos, cohort_oos
    )

    # Write result CSV
    out_csv = "analysis/iteration_v1-089/xrp_bundle_trade_corr.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["window", "pair", "pearson_corr", "common_days"])
        w.writeheader()
        for r in is_rows + oos_rows:
            w.writerow(r)

    # Console report
    def fmt_window(label, member, avg, ew, zf_member, zf_avg, zf_ew):
        print(f"\n=== {label} trade-level daily-PnL correlation: XRP/088 vs BUNDLE-002 ===")
        print(f"{'pair':<16}{'co-trade':>10}{'cmn_days':>10}{'zerofill':>10}{'zf_days':>9}")
        for sym in COHORT:
            c, n = member[sym]
            zc, zn = zf_member[sym]
            print(f"XRP_vs_{sym[:-4]:<9}{c:>10.4f}{n:>10}{zc:>10.4f}{zn:>9}")
        print(f"{'AVG_PAIRWISE':<16}{avg:>10.4f}{'':>10}{zf_avg:>10.4f}")
        print(f"{'XRP_vs_EW':<16}{ew[0]:>10.4f}{ew[1]:>10}{zf_ew[0]:>10.4f}{zf_ew[1]:>9}")

    print("XRP/088 IS daily-PnL points:", len(xrp_is), "| OOS:", len(xrp_oos))
    print("(co-trade = Pearson on co-trading days only; zerofill = flat day = 0 PnL)")
    fmt_window("IS", is_member, is_avg, is_ew, is_zf_member, is_zf_avg, is_zf_ew)
    fmt_window(
        "OOS (informational)", oos_member, oos_avg, oos_ew, oos_zf_member, oos_zf_avg, oos_zf_ew
    )

    print("\n=== VERDICT (IS-only, pre-committed threshold 0.5) ===")
    print(f"avg IS pairwise corr (co-trade) = {is_avg:.4f}")
    print(f"avg IS pairwise corr (zerofill) = {is_zf_avg:.4f}")
    print(f"XRP vs EW-cohort IS (co-trade)  = {is_ew[0]:.4f}")
    print(f"XRP vs EW-cohort IS (zerofill)  = {is_zf_ew[0]:.4f}")
    if is_avg < 0.5:
        print("VERDICT: XRP EARNS BUNDLE-003 SEAT (genuine diversifier)")
    else:
        print("VERDICT: DIVERSIFIER-DEGENERATE (no seat)")
    print(f"\nResult CSV: {out_csv}")


if __name__ == "__main__":
    main()

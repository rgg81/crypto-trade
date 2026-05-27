"""Diagnostic: what's driving the OOS pool×LINK Pearson +0.5260?

Look at:
1. Side-by-side monthly returns for pool and LINK on OOS.
2. Drop each month one at a time and recompute Pearson (jackknife).
3. Identify outlier-driving months.
4. Spearman vs Pearson divergence indicates outlier influence.

This decides YELLOW vs RED. If a single outlier month accounts for the
breach, the underlying diversification is still intact and /027 can proceed
under YELLOW; if Pearson stays > 0.50 after every leave-one-out, the
correlation is structural and we have a real diversification concern.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

REPO_ROOT = Path("/home/roberto/crypto-trade/.worktrees/quant-research")

POOL = REPO_ROOT / "reports-v1" / "iteration_v1-baseline"
LINK = REPO_ROOT / "reports-v1" / "iteration_v1-018"


def read_monthly(path: Path) -> dict[str, tuple[float, int]]:
    out: dict[str, tuple[float, int]] = {}
    with path.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            out[row["month"].strip()] = (float(row["pnl_pct"]), int(row["trade_count"]))
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def main() -> None:
    pool = read_monthly(POOL / "out_of_sample" / "monthly_pnl.csv")
    link = read_monthly(LINK / "out_of_sample" / "monthly_pnl.csv")

    # Overlap months where both are active (>0 trades)
    months = sorted(
        m for m in pool
        if m in link and pool[m][1] > 0 and link[m][1] > 0
    )
    xs = [pool[m][0] for m in months]
    ys = [link[m][0] for m in months]

    print("OOS monthly returns side-by-side (active in both):")
    print(f"  {'month':<10} {'pool':>10} {'LINK':>10}  trades_pool / trades_LINK")
    for m in months:
        print(
            f"  {m:<10} {pool[m][0]:+10.4f} {link[m][0]:+10.4f}  "
            f"{pool[m][1]:>2d} / {link[m][1]:>2d}"
        )

    p_all = pearson(xs, ys)
    print(f"\nFull-window Pearson (n={len(months)}): {p_all:+.4f}")

    print("\nLeave-one-out (LOO) jackknife — drop each month, recompute Pearson:")
    print(f"  {'dropped':<10} {'Pearson':>10}  {'Δ vs full':>10}")
    for i, m in enumerate(months):
        xs_loo = xs[:i] + xs[i + 1:]
        ys_loo = ys[:i] + ys[i + 1:]
        p_loo = pearson(xs_loo, ys_loo)
        delta = p_loo - p_all
        marker = "  ← biggest mover" if False else ""
        print(f"  {m:<10} {p_loo:+10.4f}  {delta:+10.4f}{marker}")

    # Identify the month whose removal causes the largest drop
    diffs: list[tuple[str, float]] = []
    for i, m in enumerate(months):
        xs_loo = xs[:i] + xs[i + 1:]
        ys_loo = ys[:i] + ys[i + 1:]
        p_loo = pearson(xs_loo, ys_loo)
        diffs.append((m, p_loo))

    diffs.sort(key=lambda t: t[1])  # ascending: smallest LOO Pearson first
    print("\nLOO Pearson ranked ascending (lowest correlation when month removed):")
    for m, p in diffs:
        below_threshold = "  ← BELOW 0.50 threshold" if p < 0.50 else ""
        print(f"  drop {m}: Pearson = {p:+.4f}{below_threshold}")

    # Test "drop 2 worst months" — does that bring correlation under 0.50?
    print("\n2-month drop sensitivity:")
    n_below = 0
    n_total = 0
    for i in range(len(months)):
        for j in range(i + 1, len(months)):
            xs_d2 = [v for k, v in enumerate(xs) if k != i and k != j]
            ys_d2 = [v for k, v in enumerate(ys) if k != i and k != j]
            p_d2 = pearson(xs_d2, ys_d2)
            n_total += 1
            if p_d2 < 0.50:
                n_below += 1
    print(
        f"  Out of {n_total} (n choose 2) 2-month-drop combinations, "
        f"{n_below} bring Pearson below 0.50 ({100 * n_below / n_total:.1f}%)."
    )

    # Co-extreme month analysis: identify months where BOTH PnL are large
    # (z-score abs > 1.0) AND same sign. These drive Pearson upward.
    pool_mean = sum(xs) / len(xs)
    link_mean = sum(ys) / len(ys)
    pool_sd = math.sqrt(sum((x - pool_mean) ** 2 for x in xs) / (len(xs) - 1))
    link_sd = math.sqrt(sum((y - link_mean) ** 2 for y in ys) / (len(ys) - 1))

    print("\nCo-extreme months (|z| > 1.0 in BOTH AND same sign — drives Pearson up):")
    print(f"  {'month':<10} {'z_pool':>8} {'z_link':>8}  pool / LINK")
    co_extreme: list[str] = []
    for m, p, ll in zip(months, xs, ys, strict=True):
        z_p = (p - pool_mean) / pool_sd
        z_l = (ll - link_mean) / link_sd
        if abs(z_p) > 1.0 and abs(z_l) > 1.0 and (z_p * z_l > 0):
            co_extreme.append(m)
            print(f"  {m:<10} {z_p:+8.3f} {z_l:+8.3f}  {p:+.3f} / {ll:+.3f}")

    if not co_extreme:
        print("  (none)")

    # Write summary
    with (REPO_ROOT / "analysis" / "iteration_v1-026" / "oos_pool_link_diagnostic.csv").open(
        "w", newline=""
    ) as f:
        wr = csv.writer(f)
        wr.writerow([
            "month", "pool_pnl_pct", "link_pnl_pct", "pool_trades", "link_trades",
            "z_pool", "z_link", "co_extreme_same_sign",
        ])
        for m, p, ll in zip(months, xs, ys, strict=True):
            z_p = (p - pool_mean) / pool_sd
            z_l = (ll - link_mean) / link_sd
            co = (abs(z_p) > 1.0 and abs(z_l) > 1.0 and (z_p * z_l > 0))
            wr.writerow([
                m, f"{p:+.4f}", f"{ll:+.4f}", pool[m][1], link[m][1],
                f"{z_p:+.3f}", f"{z_l:+.3f}", "YES" if co else "NO",
            ])


if __name__ == "__main__":
    main()

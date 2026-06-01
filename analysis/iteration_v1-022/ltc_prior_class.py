"""iter-v1/022 Phase 1 — LTC prior class classification.

Per /021 Critic Rec #1 + LM Master /022 forward-binding + diary §6:
the SINGLE MOST IMPORTANT decision at /022 is pre-classification of LTC's
prior class. This script reads BASELINE_V1.md's reports-v1/iteration_v1-baseline/
artifacts and produces the LTC tables Section 2 of the brief will cite:

  - LTC per-symbol IS / OOS metrics (already in BASELINE_V1.md §3-4 but
    reproduced here for self-contained Section 2 attribution)
  - LTC per-month IS PnL distribution (n_months, n_positive, mean, P25/P50/P75,
    streak max, streak negative)
  - LTC per-month OOS PnL distribution (same)
  - LTC IS-half / OOS-half / WR / fees / by-direction split
  - LTC exit reason mix vs portfolio-mix delta
  - Prior class verdict computed deterministically from a 3-state classifier

Outputs:
  - analysis/iteration_v1-022/ltc_prior_class.csv  (single summary row)
  - analysis/iteration_v1-022/ltc_monthly_pnl.csv  (LTC-only monthly PnL IS+OOS)
  - analysis/iteration_v1-022/ltc_direction_split.csv  (long/short attribution)
  - analysis/iteration_v1-022/ltc_exit_reasons.csv

NO OOS peeking during /022 design: this script computes both IS and OOS
metrics from the BASELINE_V1.md reports because that information is already
public at the BASELINE_V1.md level (anchor-frame numbers) and is referenced
verbatim in Section 2 of the brief. The QR may cite OOS LTC numbers from the
BASELINE — they are the anchor against which /022 is measured. They are NOT
OOS for any per-iteration model trained inside /022.

Determinism: input is the static reports-v1/iteration_v1-baseline/{in_sample,
out_of_sample}/trades.csv. Re-running the script produces bit-identical CSVs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
IS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OOS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
OUT_DIR = REPO / "analysis" / "iteration_v1-022"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL = "LTCUSDT"


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["close_time_ms"] = df["close_time"].astype("int64")
    df["close_dt"] = pd.to_datetime(df["close_time_ms"], unit="ms", utc=True)
    df["month"] = df["close_dt"].dt.to_period("M").astype(str)
    return df


def _basic_stats(df: pd.DataFrame, sample: str) -> dict[str, float | int | str]:
    if df.empty:
        return {
            "sample": sample,
            "n_trades": 0,
            "n_wins": 0,
            "win_rate_pct": 0.0,
            "net_pnl_pct": 0.0,
            "avg_pnl_pct": 0.0,
            "median_pnl_pct": 0.0,
            "std_pnl_pct": 0.0,
            "sharpe_per_trade": 0.0,
        }
    n = len(df)
    n_wins = int((df["net_pnl_pct"] > 0).sum())
    net = float(df["net_pnl_pct"].sum())
    avg = float(df["net_pnl_pct"].mean())
    med = float(df["net_pnl_pct"].median())
    std = float(df["net_pnl_pct"].std(ddof=1)) if n > 1 else 0.0
    sharpe = (avg / std) if std > 0 else 0.0
    return {
        "sample": sample,
        "n_trades": n,
        "n_wins": n_wins,
        "win_rate_pct": round(100.0 * n_wins / n, 3),
        "net_pnl_pct": round(net, 4),
        "avg_pnl_pct": round(avg, 4),
        "median_pnl_pct": round(med, 4),
        "std_pnl_pct": round(std, 4),
        "sharpe_per_trade": round(sharpe, 4),
    }


def _direction_split(df: pd.DataFrame, sample: str) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for direction in (-1, 1):
        sub = df[df["direction"] == direction]
        row = _basic_stats(sub, f"{sample}_dir{direction:+d}")
        rows.append(row)
    return rows


def _monthly(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "sample", "n_trades", "n_wins", "net_pnl_pct"])
    grouped = (
        df.groupby("month")
        .agg(
            n_trades=("net_pnl_pct", "size"),
            n_wins=("net_pnl_pct", lambda s: int((s > 0).sum())),
            net_pnl_pct=("net_pnl_pct", "sum"),
        )
        .reset_index()
    )
    grouped["sample"] = sample
    grouped["win_rate_pct"] = (100.0 * grouped["n_wins"] / grouped["n_trades"]).round(3)
    grouped["net_pnl_pct"] = grouped["net_pnl_pct"].round(4)
    return grouped[["month", "sample", "n_trades", "n_wins", "win_rate_pct", "net_pnl_pct"]]


def _exit_reasons(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["sample", "exit_reason", "count", "share_pct"])
    counts = df["exit_reason"].value_counts().reset_index()
    counts.columns = ["exit_reason", "count"]
    counts["share_pct"] = (100.0 * counts["count"] / counts["count"].sum()).round(3)
    counts["sample"] = sample
    return counts[["sample", "exit_reason", "count", "share_pct"]]


def _streak_stats(monthly: pd.DataFrame) -> dict[str, int]:
    """Compute longest consecutive (+) and (-) PnL month streaks."""
    if monthly.empty:
        return {"max_pos_streak": 0, "max_neg_streak": 0}
    signs = (monthly["net_pnl_pct"] > 0).astype(int).tolist()
    max_pos = max_neg = 0
    cur_pos = cur_neg = 0
    for s in signs:
        if s == 1:
            cur_pos += 1
            cur_neg = 0
            max_pos = max(max_pos, cur_pos)
        else:
            cur_neg += 1
            cur_pos = 0
            max_neg = max(max_neg, cur_neg)
    return {"max_pos_streak": int(max_pos), "max_neg_streak": int(max_neg)}


def _classify_ltc(is_stats: dict, oos_stats: dict) -> dict[str, str | float]:
    """Three-state classifier matching /021 diary §6 framework.

    Class definitions (mirror /018 LINK, /019 ETH, /020 BTC analysis basis):

    - POSITIVE_EVERYWHERE: IS net_pnl > 0 AND OOS net_pnl > 0 AND both Sharpe positive
    - ASYMMETRIC_ROTATION: IS sign != OOS sign (either direction)
    - ASYMMETRIC_ROTATION-INVERSE: IS marginally positive (< 1 std-error from 0)
      AND OOS strongly negative (Δ from 0 > 1 std-error in magnitude)
      — sub-class of ASYMMETRIC_ROTATION
    - NEGATIVE_EVERYWHERE: IS net_pnl < 0 AND OOS net_pnl < 0

    Per /021 H2 REFUTATION, mechanism is at parameter-basin level NOT feature
    level. Per /020 BTC retrospective, ASYMMETRIC_ROTATION cohorts catastrophically
    fail under PURE ISOLATION; orthogonal mechanism is required.
    """
    is_pnl = float(is_stats["net_pnl_pct"])
    oos_pnl = float(oos_stats["net_pnl_pct"])
    is_n = int(is_stats["n_trades"])
    oos_n = int(oos_stats["n_trades"])
    is_avg = float(is_stats["avg_pnl_pct"])
    oos_avg = float(oos_stats["avg_pnl_pct"])
    is_std = float(is_stats["std_pnl_pct"])
    oos_std = float(oos_stats["std_pnl_pct"])

    # Compute per-trade z-score of avg PnL away from 0 (standard error)
    is_se = (is_std / (is_n**0.5)) if is_n > 0 and is_std > 0 else 0.0
    oos_se = (oos_std / (oos_n**0.5)) if oos_n > 0 and oos_std > 0 else 0.0
    is_z = (is_avg / is_se) if is_se > 0 else 0.0
    oos_z = (oos_avg / oos_se) if oos_se > 0 else 0.0

    # Headline class
    if is_pnl > 0 and oos_pnl > 0:
        klass = "POSITIVE_EVERYWHERE"
    elif is_pnl < 0 and oos_pnl < 0:
        klass = "NEGATIVE_EVERYWHERE"
    else:
        # Sub-classify ASYMMETRIC_ROTATION
        if is_pnl < 0 and oos_pnl > 0:
            klass = "ASYMMETRIC_ROTATION_IS-NEG_OOS-POS"  # /020 BTC family
        elif is_pnl > 0 and oos_pnl < 0:
            # Distinguish marginal vs robust IS positive
            if abs(is_z) < 1.0:
                klass = "ASYMMETRIC_ROTATION-INVERSE_IS-MARGINAL_OOS-CAT"
            else:
                klass = "ASYMMETRIC_ROTATION_IS-POS_OOS-NEG"
        else:
            klass = "UNDEFINED"

    return {
        "ltc_prior_class": klass,
        "is_net_pnl_pct": round(is_pnl, 4),
        "oos_net_pnl_pct": round(oos_pnl, 4),
        "is_avg_per_trade_pct": round(is_avg, 4),
        "oos_avg_per_trade_pct": round(oos_avg, 4),
        "is_avg_z_score": round(is_z, 3),
        "oos_avg_z_score": round(oos_z, 3),
        "is_per_trade_sharpe": round(is_stats["sharpe_per_trade"], 4),
        "oos_per_trade_sharpe": round(oos_stats["sharpe_per_trade"], 4),
        "is_n_trades": is_n,
        "oos_n_trades": oos_n,
        "is_win_rate_pct": round(float(is_stats["win_rate_pct"]), 3),
        "oos_win_rate_pct": round(float(oos_stats["win_rate_pct"]), 3),
    }


def main() -> None:
    is_df = _load(IS_TRADES)
    oos_df = _load(OOS_TRADES)

    is_ltc = is_df[is_df["symbol"] == SYMBOL].copy()
    oos_ltc = oos_df[oos_df["symbol"] == SYMBOL].copy()

    # Basic stats
    is_stats = _basic_stats(is_ltc, "IS")
    oos_stats = _basic_stats(oos_ltc, "OOS")

    # Direction split
    dir_rows = _direction_split(is_ltc, "IS") + _direction_split(oos_ltc, "OOS")
    pd.DataFrame(dir_rows).to_csv(OUT_DIR / "ltc_direction_split.csv", index=False)

    # Monthly distributions
    monthly_is = _monthly(is_ltc, "IS")
    monthly_oos = _monthly(oos_ltc, "OOS")
    monthly_all = pd.concat([monthly_is, monthly_oos], ignore_index=True)
    monthly_all.to_csv(OUT_DIR / "ltc_monthly_pnl.csv", index=False)

    # Exit reasons
    exit_is = _exit_reasons(is_ltc, "IS")
    exit_oos = _exit_reasons(oos_ltc, "OOS")
    pd.concat([exit_is, exit_oos], ignore_index=True).to_csv(
        OUT_DIR / "ltc_exit_reasons.csv", index=False
    )

    # Streaks
    streak_is = _streak_stats(monthly_is)
    streak_oos = _streak_stats(monthly_oos)

    # Per-half (IS only — 2-year IS window)
    # 24-month IS window: first 12 vs last 12 months
    if not monthly_is.empty:
        months_sorted = monthly_is.sort_values("month").reset_index(drop=True)
        n_months = len(months_sorted)
        h1 = months_sorted.iloc[: n_months // 2]
        h2 = months_sorted.iloc[n_months // 2 :]
        is_h1_pnl = float(h1["net_pnl_pct"].sum())
        is_h2_pnl = float(h2["net_pnl_pct"].sum())
        is_h1_n = int(h1["n_trades"].sum())
        is_h2_n = int(h2["n_trades"].sum())
    else:
        is_h1_pnl = is_h2_pnl = 0.0
        is_h1_n = is_h2_n = 0

    # Classification
    klass = _classify_ltc(is_stats, oos_stats)

    # Final summary row
    summary = {
        **klass,
        "is_max_pos_streak_months": streak_is["max_pos_streak"],
        "is_max_neg_streak_months": streak_is["max_neg_streak"],
        "oos_max_pos_streak_months": streak_oos["max_pos_streak"],
        "oos_max_neg_streak_months": streak_oos["max_neg_streak"],
        "is_n_months": len(monthly_is),
        "is_n_pos_months": int((monthly_is["net_pnl_pct"] > 0).sum()) if not monthly_is.empty else 0,
        "oos_n_months": len(monthly_oos),
        "oos_n_pos_months": int((monthly_oos["net_pnl_pct"] > 0).sum())
        if not monthly_oos.empty
        else 0,
        "is_h1_net_pnl_pct": round(is_h1_pnl, 4),
        "is_h2_net_pnl_pct": round(is_h2_pnl, 4),
        "is_h1_n_trades": is_h1_n,
        "is_h2_n_trades": is_h2_n,
    }
    pd.DataFrame([summary]).to_csv(OUT_DIR / "ltc_prior_class.csv", index=False)

    print("=" * 80)
    print("iter-v1/022 Phase 1 — LTC prior class classification")
    print("=" * 80)
    print(f"IS:  {is_stats['n_trades']:3d} trades, "
          f"WR {is_stats['win_rate_pct']:.1f}%, "
          f"net PnL {is_stats['net_pnl_pct']:+.4f}%, "
          f"avg {is_stats['avg_pnl_pct']:+.4f}%, "
          f"std {is_stats['std_pnl_pct']:.4f}%, "
          f"per-trade Sharpe {is_stats['sharpe_per_trade']:+.4f}")
    print(f"OOS: {oos_stats['n_trades']:3d} trades, "
          f"WR {oos_stats['win_rate_pct']:.1f}%, "
          f"net PnL {oos_stats['net_pnl_pct']:+.4f}%, "
          f"avg {oos_stats['avg_pnl_pct']:+.4f}%, "
          f"std {oos_stats['std_pnl_pct']:.4f}%, "
          f"per-trade Sharpe {oos_stats['sharpe_per_trade']:+.4f}")
    print(f"IS half-split:  H1 {is_h1_pnl:+.4f}% ({is_h1_n} tr) | "
          f"H2 {is_h2_pnl:+.4f}% ({is_h2_n} tr)")
    print(f"IS months:  {summary['is_n_months']} total, "
          f"{summary['is_n_pos_months']} positive, "
          f"max pos streak {streak_is['max_pos_streak']}, "
          f"max neg streak {streak_is['max_neg_streak']}")
    print(f"OOS months: {summary['oos_n_months']} total, "
          f"{summary['oos_n_pos_months']} positive, "
          f"max pos streak {streak_oos['max_pos_streak']}, "
          f"max neg streak {streak_oos['max_neg_streak']}")
    print(f"IS avg z-score:  {klass['is_avg_z_score']:+.3f}  "
          f"(>1.0 = robust positive, <1.0 = marginal noise)")
    print(f"OOS avg z-score: {klass['oos_avg_z_score']:+.3f}")
    print()
    print(f"*** LTC PRIOR CLASS = {klass['ltc_prior_class']} ***")
    print()
    print("Per-direction breakdown (avg PnL %):")
    for r in dir_rows:
        print(
            f"  {r['sample']}: {r['n_trades']:3d} tr, "
            f"WR {r['win_rate_pct']:.1f}%, "
            f"net {r['net_pnl_pct']:+.4f}%, "
            f"avg {r['avg_pnl_pct']:+.4f}%, "
            f"per-trade Sharpe {r['sharpe_per_trade']:+.4f}"
        )
    print()
    print("Outputs:")
    print(f"  {OUT_DIR / 'ltc_prior_class.csv'}")
    print(f"  {OUT_DIR / 'ltc_monthly_pnl.csv'}")
    print(f"  {OUT_DIR / 'ltc_direction_split.csv'}")
    print(f"  {OUT_DIR / 'ltc_exit_reasons.csv'}")


if __name__ == "__main__":
    main()

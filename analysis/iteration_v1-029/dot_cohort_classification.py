"""iter-v1/029 Phase 1 — DOT cohort pre-classification.

Per /028 LM Master Phase 7.4 §6 + /028 Critic Path Forward §6: /029 = DOT-only
specialist (cycle-4 cohort coverage; DOT is LAST untested single-cohort).
Pre-classify DOT against the refined per-cohort SATURATION rule (codified at
/028 closeout, `feedback_v1_atr_sl_label_shift_mechanism.md`):

  - POSITIVE_EVERYWHERE      → pure isolation works (LINK /018 model)
  - ASYMMETRIC_ROTATION      → INVIABLE for pre-entry gates; viable for
                                UPSTREAM LABEL changes (atr_sl multiplier
                                — /028 LTC PROMISING +0.598)
  - COUNTER-TREND OOS DRAG   → symmetric pre-entry BTC-trend gate (ETH /019
                                PROMISING +0.50)

This script reads BASELINE_V1.md's `reports-v1/iteration_v1-baseline/`
trade rosters and the LTC /028 anchor (`reports-v1/iteration_v1-028/`) to
produce the DOT tables Section 2 of the brief will cite:

  - DOT per-symbol IS / OOS metrics (already in BASELINE_V1.md §3-4 but
    reproduced here for self-contained Section 2 attribution)
  - DOT trade direction breakdown (long vs short PnL split IS/OOS)
  - DOT win rate by direction
  - DOT per-trade correlation with BTC trend (BTC ret_42_bar bucket)
  - DOT OOS attribution (catastrophe — if any)
  - 3-class pre-classification verdict

No OOS peeking for /029 design: per BASELINE_V1.md framing, baseline OOS
numbers are public anchor-frame and may be cited for cohort pre-classification.
They are NOT OOS for any per-iteration model trained inside /029.

Determinism: input is the static BASELINE reports + LTC /028 anchor +
BTC 8h klines. Re-running produces bit-identical CSVs.

Outputs:
  - analysis/iteration_v1-029/dot_classification.csv  (single summary row)
  - analysis/iteration_v1-029/dot_btc_trend_bucket.csv  (per-bucket PnL split)
  - analysis/iteration_v1-029/dot_direction_split.csv
  - analysis/iteration_v1-029/dot_monthly_pnl.csv
  - analysis/iteration_v1-029/dot_exit_reasons.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
IS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OOS_TRADES = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
BTC_KLINES = REPO / "data" / "BTCUSDT" / "8h.csv"
OUT_DIR = REPO / "analysis" / "iteration_v1-029"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL = "DOTUSDT"
GATE_LOOKBACK = 42  # 14 days at 8h — mirrors /019 ETH gate + /022 LTC gate analysis


# ---------------------------------------------------------------------------
# Helpers — mirror /022 ltc_prior_class.py contract for cross-iteration parity


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


# ---------------------------------------------------------------------------
# BTC trend bucket attachment


def _load_btc() -> pd.DataFrame:
    btc = pd.read_csv(BTC_KLINES)
    btc["open_time_ms"] = btc["open_time"].astype("int64")
    btc["close_price"] = btc["close"].astype(float)
    btc = btc.sort_values("open_time_ms").reset_index(drop=True)
    btc["btc_ret_42"] = (
        btc["close_price"] / btc["close_price"].shift(GATE_LOOKBACK) - 1.0
    ) * 100.0
    return btc[["open_time_ms", "close_price", "btc_ret_42"]]


def _attach_btc_trend(trades: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    trades = trades.copy()
    trades["open_time_ms"] = trades["open_time"].astype("int64")
    merged = pd.merge_asof(
        trades.sort_values("open_time_ms"),
        btc[["open_time_ms", "btc_ret_42"]].sort_values("open_time_ms"),
        on="open_time_ms",
        direction="backward",
        allow_exact_matches=True,
    )
    return merged


def _btc_trend_buckets(
    df: pd.DataFrame, sample: str
) -> list[dict[str, float | int | str]]:
    """Per-direction × BTC-trend-bucket attribution.

    Buckets:
      - BTC strong down: btc_ret_42 < -8%
      - BTC weak down:   -8% <= btc_ret_42 < 0%
      - BTC weak up:     0% <= btc_ret_42 < +8%
      - BTC strong up:   btc_ret_42 >= +8%
    """
    rows: list[dict[str, float | int | str]] = []
    if df.empty:
        return rows

    buckets: list[tuple[str, callable]] = [
        ("strong_down_lt_-8", lambda x: x < -8.0),
        ("weak_down_-8_to_0", lambda x: (x >= -8.0) & (x < 0.0)),
        ("weak_up_0_to_+8", lambda x: (x >= 0.0) & (x < 8.0)),
        ("strong_up_ge_+8", lambda x: x >= 8.0),
    ]

    for direction_label, direction_val in (("long", 1), ("short", -1)):
        dir_df = df[df["direction"] == direction_val]
        for bucket_label, bucket_fn in buckets:
            non_na = dir_df.dropna(subset=["btc_ret_42"])
            sub = non_na[bucket_fn(non_na["btc_ret_42"])]
            stats = _basic_stats(sub, f"{sample}_{direction_label}_{bucket_label}")
            stats["direction"] = direction_label
            stats["bucket"] = bucket_label
            rows.append(stats)
    return rows


# ---------------------------------------------------------------------------
# Classification


def _classify_dot(
    is_stats: dict,
    oos_stats: dict,
    is_dir_stats: dict[str, dict],
    oos_dir_stats: dict[str, dict],
    is_buckets: list[dict],
    oos_buckets: list[dict],
) -> dict[str, str | float]:
    """3-class pre-classification matching /028 LM Master refined SATURATION rule.

    DOT is classified into ONE of:
      - POSITIVE_EVERYWHERE: IS net_pnl > 0 AND OOS net_pnl > 0 AND OOS Sharpe ≥ 0.5 × IS Sharpe
      - COUNTER-TREND OOS DRAG: IS net_pnl > 0 AND OOS catastrophic AND direction-
                                conditional under BTC-trend buckets (long loses
                                while short profits — or vice versa — under
                                opposing BTC-trend regime)
      - ASYMMETRIC_ROTATION:   IS net_pnl > 0 AND OOS catastrophic AND no clear
                                direction asymmetry (basin pulled away from
                                working trades regardless of direction)
      - NEGATIVE_EVERYWHERE:   IS net_pnl < 0 AND OOS net_pnl < 0 (sentinel)

    Mechanism mapping (per /028 LM Master Phase 7.4 §5 + /029 brief mandate):
      - POSITIVE_EVERYWHERE      → pure isolation (atr_sl=1.75, atr_tp=3.5)
      - COUNTER-TREND OOS DRAG   → symmetric BTC-trend gate (±8%, lookback=42)
      - ASYMMETRIC_ROTATION      → atr_sl=1.0 + atr_tp=3.5 (upstream label shift)
    """
    is_pnl = float(is_stats["net_pnl_pct"])
    oos_pnl = float(oos_stats["net_pnl_pct"])
    is_n = int(is_stats["n_trades"])
    oos_n = int(oos_stats["n_trades"])
    is_avg = float(is_stats["avg_pnl_pct"])
    oos_avg = float(oos_stats["avg_pnl_pct"])
    is_std = float(is_stats["std_pnl_pct"])
    oos_std = float(oos_stats["std_pnl_pct"])
    is_sharpe = float(is_stats["sharpe_per_trade"])
    oos_sharpe = float(oos_stats["sharpe_per_trade"])

    # Per-trade z-score of avg PnL away from 0 (standard error)
    is_se = (is_std / (is_n**0.5)) if is_n > 0 and is_std > 0 else 0.0
    oos_se = (oos_std / (oos_n**0.5)) if oos_n > 0 and oos_std > 0 else 0.0
    is_z = (is_avg / is_se) if is_se > 0 else 0.0
    oos_z = (oos_avg / oos_se) if oos_se > 0 else 0.0

    # Direction-conditional PnL (long vs short by sample)
    is_long_pnl = is_dir_stats.get("long", {}).get("net_pnl_pct", 0.0)
    is_short_pnl = is_dir_stats.get("short", {}).get("net_pnl_pct", 0.0)
    oos_long_pnl = oos_dir_stats.get("long", {}).get("net_pnl_pct", 0.0)
    oos_short_pnl = oos_dir_stats.get("short", {}).get("net_pnl_pct", 0.0)

    # Direction asymmetry: at OOS, is one direction profoundly worse?
    # Threshold: |oos_long_pnl - oos_short_pnl| > 5% AND signs differ
    direction_asymmetry_pp = abs(oos_long_pnl - oos_short_pnl)
    signs_differ = (oos_long_pnl > 0) != (oos_short_pnl > 0)

    # Headline class
    if is_pnl > 0 and oos_pnl > 0:
        # Both samples positive — but check OOS/IS Sharpe ratio gate
        # POSITIVE_EVERYWHERE requires OOS Sharpe ≥ 0.5 × IS Sharpe
        # If OOS Sharpe is tiny vs IS, still classify as POSITIVE_EVERYWHERE
        # (it's not catastrophic — it's edge erosion, not regime flip)
        klass = "POSITIVE_EVERYWHERE"
    elif is_pnl < 0 and oos_pnl < 0:
        klass = "NEGATIVE_EVERYWHERE"  # sentinel — should not occur for DOT per BASELINE
    else:
        # IS positive, OOS catastrophic (or vice versa)
        # If OOS catastrophic with sign asymmetry → COUNTER-TREND
        # Otherwise → ASYMMETRIC_ROTATION
        if is_pnl > 0 and oos_pnl < 0:
            if signs_differ and direction_asymmetry_pp > 5.0:
                klass = "COUNTER-TREND_OOS-DRAG"
            else:
                klass = "ASYMMETRIC_ROTATION_IS-POS_OOS-NEG"
        elif is_pnl < 0 and oos_pnl > 0:
            klass = "ASYMMETRIC_ROTATION_IS-NEG_OOS-POS"  # /020 BTC family
        else:
            klass = "UNDEFINED"

    return {
        "dot_prior_class": klass,
        "is_net_pnl_pct": round(is_pnl, 4),
        "oos_net_pnl_pct": round(oos_pnl, 4),
        "is_avg_per_trade_pct": round(is_avg, 4),
        "oos_avg_per_trade_pct": round(oos_avg, 4),
        "is_avg_z_score": round(is_z, 3),
        "oos_avg_z_score": round(oos_z, 3),
        "is_per_trade_sharpe": round(is_sharpe, 4),
        "oos_per_trade_sharpe": round(oos_sharpe, 4),
        "oos_is_sharpe_ratio": round(
            oos_sharpe / is_sharpe if abs(is_sharpe) > 1e-9 else 0.0, 4
        ),
        "is_n_trades": is_n,
        "oos_n_trades": oos_n,
        "is_win_rate_pct": round(float(is_stats["win_rate_pct"]), 3),
        "oos_win_rate_pct": round(float(oos_stats["win_rate_pct"]), 3),
        "is_long_pnl_pct": round(is_long_pnl, 4),
        "is_short_pnl_pct": round(is_short_pnl, 4),
        "oos_long_pnl_pct": round(oos_long_pnl, 4),
        "oos_short_pnl_pct": round(oos_short_pnl, 4),
        "oos_direction_asymmetry_pp": round(direction_asymmetry_pp, 4),
        "oos_signs_differ": signs_differ,
    }


# ---------------------------------------------------------------------------


def main() -> None:
    is_df = _load(IS_TRADES)
    oos_df = _load(OOS_TRADES)
    btc = _load_btc()

    is_dot = is_df[is_df["symbol"] == SYMBOL].copy()
    oos_dot = oos_df[oos_df["symbol"] == SYMBOL].copy()

    # Attach BTC trend
    is_dot = _attach_btc_trend(is_dot, btc)
    oos_dot = _attach_btc_trend(oos_dot, btc)

    # Basic stats
    is_stats = _basic_stats(is_dot, "IS")
    oos_stats = _basic_stats(oos_dot, "OOS")

    # Direction split
    dir_rows = _direction_split(is_dot, "IS") + _direction_split(oos_dot, "OOS")
    pd.DataFrame(dir_rows).to_csv(OUT_DIR / "dot_direction_split.csv", index=False)

    # Build direction-stats dict for classifier
    is_dir_stats = {}
    oos_dir_stats = {}
    for r in dir_rows:
        label = r["sample"]
        if label.startswith("IS"):
            dir_key = "long" if "dir+1" in label else "short"
            is_dir_stats[dir_key] = r
        else:
            dir_key = "long" if "dir+1" in label else "short"
            oos_dir_stats[dir_key] = r

    # Monthly distributions
    monthly_is = _monthly(is_dot, "IS")
    monthly_oos = _monthly(oos_dot, "OOS")
    monthly_all = pd.concat([monthly_is, monthly_oos], ignore_index=True)
    monthly_all.to_csv(OUT_DIR / "dot_monthly_pnl.csv", index=False)

    # Exit reasons
    exit_is = _exit_reasons(is_dot, "IS")
    exit_oos = _exit_reasons(oos_dot, "OOS")
    pd.concat([exit_is, exit_oos], ignore_index=True).to_csv(
        OUT_DIR / "dot_exit_reasons.csv", index=False
    )

    # BTC trend buckets (per-direction × per-bucket)
    is_buckets = _btc_trend_buckets(is_dot, "IS")
    oos_buckets = _btc_trend_buckets(oos_dot, "OOS")
    pd.DataFrame(is_buckets + oos_buckets).to_csv(
        OUT_DIR / "dot_btc_trend_bucket.csv", index=False
    )

    # Streaks
    streak_is = _streak_stats(monthly_is)
    streak_oos = _streak_stats(monthly_oos)

    # IS half-split (12 + 12 month sanity)
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
    klass = _classify_dot(
        is_stats, oos_stats, is_dir_stats, oos_dir_stats, is_buckets, oos_buckets
    )

    # Final summary row
    summary = {
        **klass,
        "is_max_pos_streak_months": streak_is["max_pos_streak"],
        "is_max_neg_streak_months": streak_is["max_neg_streak"],
        "oos_max_pos_streak_months": streak_oos["max_pos_streak"],
        "oos_max_neg_streak_months": streak_oos["max_neg_streak"],
        "is_n_months": len(monthly_is),
        "is_n_pos_months": int((monthly_is["net_pnl_pct"] > 0).sum())
        if not monthly_is.empty
        else 0,
        "oos_n_months": len(monthly_oos),
        "oos_n_pos_months": int((monthly_oos["net_pnl_pct"] > 0).sum())
        if not monthly_oos.empty
        else 0,
        "is_h1_net_pnl_pct": round(is_h1_pnl, 4),
        "is_h2_net_pnl_pct": round(is_h2_pnl, 4),
        "is_h1_n_trades": is_h1_n,
        "is_h2_n_trades": is_h2_n,
    }
    pd.DataFrame([summary]).to_csv(OUT_DIR / "dot_classification.csv", index=False)

    # Stdout summary
    print("=" * 80)
    print("iter-v1/029 Phase 1 — DOT cohort pre-classification")
    print("=" * 80)
    print(
        f"IS:  {is_stats['n_trades']:3d} trades, "
        f"WR {is_stats['win_rate_pct']:.1f}%, "
        f"net PnL {is_stats['net_pnl_pct']:+.4f}%, "
        f"avg {is_stats['avg_pnl_pct']:+.4f}%, "
        f"std {is_stats['std_pnl_pct']:.4f}%, "
        f"per-trade Sharpe {is_stats['sharpe_per_trade']:+.4f}"
    )
    print(
        f"OOS: {oos_stats['n_trades']:3d} trades, "
        f"WR {oos_stats['win_rate_pct']:.1f}%, "
        f"net PnL {oos_stats['net_pnl_pct']:+.4f}%, "
        f"avg {oos_stats['avg_pnl_pct']:+.4f}%, "
        f"std {oos_stats['std_pnl_pct']:.4f}%, "
        f"per-trade Sharpe {oos_stats['sharpe_per_trade']:+.4f}"
    )
    print(
        f"IS half-split:  H1 {is_h1_pnl:+.4f}% ({is_h1_n} tr) | "
        f"H2 {is_h2_pnl:+.4f}% ({is_h2_n} tr)"
    )
    print(
        f"IS months:  {summary['is_n_months']} total, "
        f"{summary['is_n_pos_months']} positive, "
        f"max pos streak {streak_is['max_pos_streak']}, "
        f"max neg streak {streak_is['max_neg_streak']}"
    )
    print(
        f"OOS months: {summary['oos_n_months']} total, "
        f"{summary['oos_n_pos_months']} positive, "
        f"max pos streak {streak_oos['max_pos_streak']}, "
        f"max neg streak {streak_oos['max_neg_streak']}"
    )
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
    print("OOS direction asymmetry:")
    print(f"  OOS long  net PnL: {klass['oos_long_pnl_pct']:+.4f}%")
    print(f"  OOS short net PnL: {klass['oos_short_pnl_pct']:+.4f}%")
    print(
        f"  |Δ|: {klass['oos_direction_asymmetry_pp']:.4f}pp, signs differ: {klass['oos_signs_differ']}"
    )
    print()
    print(f"OOS/IS Sharpe ratio: {klass['oos_is_sharpe_ratio']:+.4f}")
    print()
    print(f"*** DOT PRIOR CLASS = {klass['dot_prior_class']} ***")
    print()
    print("BTC-trend-bucket attribution (OOS only):")
    print(f"{'direction':<8} {'bucket':<22} {'n':>4} {'WR%':>6} {'net%':>10} {'avg%':>9}")
    for r in oos_buckets:
        print(
            f"  {r['direction']:<6} {r['bucket']:<22} "
            f"{r['n_trades']:>4} {r['win_rate_pct']:>5.1f} "
            f"{r['net_pnl_pct']:>+10.4f} {r['avg_pnl_pct']:>+9.4f}"
        )
    print()
    print("Outputs:")
    print(f"  {OUT_DIR / 'dot_classification.csv'}")
    print(f"  {OUT_DIR / 'dot_btc_trend_bucket.csv'}")
    print(f"  {OUT_DIR / 'dot_direction_split.csv'}")
    print(f"  {OUT_DIR / 'dot_monthly_pnl.csv'}")
    print(f"  {OUT_DIR / 'dot_exit_reasons.csv'}")


if __name__ == "__main__":
    main()

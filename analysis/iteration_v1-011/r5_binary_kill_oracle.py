"""iter-v1/011 — R5 BINARY KILL switch oracle EDA.

Per /010 closeout 3-way convergence (LM Master Phase 7.4 PRIMARY + Critic Path
Forward #1 + QR Phase 7 memo): the next risk-primitive axis is a STATE-DISCONTINUOUS
binary kill switch — skip entry entirely if NATR_14 > threshold — sister primitive
to /010's proportional scaling that smoothly attenuated.

Mechanism: tests whether the v3/020 "concentration is signal" finding generalizes
to v1 specifically for the high-NATR TAIL vs the proportional middle. Binary
state-discontinuity differs from /010's smooth multiplicative cap; the prediction
is that skipping the worst-vol entries entirely (rather than attenuating them
proportionally) preserves the LINK+BTC OOS edge while removing the catastrophic
high-vol losers.

STATELESS per `feedback_v3_oracle_eda_validity.md` (no persistent state updated
by signal emission; pure entry filter based on a feature already in the feature
parquets). Oracle EDA on prior trade roster is methodologically VALID.

OUTPUTS:

1. Per-symbol IS+OOS NATR_14 distribution at ENTRY time (vs /010's full IS
   distribution across all candles; this is what the BINARY KILL gate sees).
2. Per-symbol entry-time NATR percentiles (p10/p25/p50/p75/p85/p90/p95).
3. Oracle simulation on BOTH:
   - BASELINE roster (5-seed × n_trials=50; the canonical anchor)
   - /010 EXPLORATION roster (3-seed × n_trials=35; apples-to-apples with /011 spec)
4. For each candidate threshold in {5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0}:
   - Skipped trade count (IS + OOS)
   - Portfolio monthly Sharpe Δ vs anchor
   - Per-symbol PnL Δ
   - Identify the OOS Δ "sweet spot" (best OOS Δ candidate)
5. F2 fire rate band check ([10%, 60%] OOS) — calibration mandate.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_BASELINE_UNIVERSE  # noqa: E402

OUT_DIR = Path(__file__).parent
FEATURES_DIR = ROOT / "data" / "features"

# Two roster anchors — we run oracle on both.
BASELINE_TRADES_IS = ROOT / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
BASELINE_TRADES_OOS = (
    ROOT / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
)
V1_010_TRADES_IS = ROOT / "reports-v1" / "iteration_v1-010" / "in_sample" / "trades.csv"
V1_010_TRADES_OOS = ROOT / "reports-v1" / "iteration_v1-010" / "out_of_sample" / "trades.csv"


# ---------------------------------------------------------------------------
# Helper — NATR_14 lookup per symbol (open_time → NATR_14)
# ---------------------------------------------------------------------------


def load_natr_lookup(symbol: str) -> dict[int, float]:
    """Build open_time → vol_natr_14 lookup for *symbol* from feature parquet.

    Trade-CSV open_time uses candle_open_ms - 1 convention; feature parquet
    uses raw candle_open_ms. We normalize via _align_trade_ot at join time.
    """
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path, columns=["open_time", "vol_natr_14"])
    df = df.dropna(subset=["vol_natr_14"])
    return dict(zip(df["open_time"].to_numpy(), df["vol_natr_14"].to_numpy(), strict=True))


def _align_trade_ot(ot: int) -> int:
    return int(ot) + 1


# ---------------------------------------------------------------------------
# Phase 1.1 — Per-symbol ENTRY-TIME NATR_14 distribution
# ---------------------------------------------------------------------------


def entry_time_natr_distribution(
    roster_is: Path, roster_oos: Path, roster_label: str
) -> pd.DataFrame:
    """For each (symbol, half), compute p10/p25/p50/p75/p85/p90/p95/p99 of NATR_14
    AT ENTRY TIME for trades in the given roster.

    Note: /010 EDA computed candle-level NATR_14 distribution (5,012-5,714 candles
    per symbol). /011 EDA computes ENTRY-TIME-CONDITIONAL NATR_14 distribution
    (the subset of candles where the model actually fired a signal). This is the
    distribution the binary kill gate sees in practice.
    """
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    rows = []
    for half_name, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        natrs = [
            natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
        ]
        df["natr_14_at_entry"] = natrs
        df = df.dropna(subset=["natr_14_at_entry"]).copy()

        for sym in V1_BASELINE_UNIVERSE:
            sub = df[df["symbol"] == sym]["natr_14_at_entry"].to_numpy()
            if len(sub) == 0:
                rows.append(
                    {
                        "roster": roster_label,
                        "half": half_name,
                        "symbol": sym,
                        "n_trades": 0,
                        "mean": float("nan"),
                        "p10": float("nan"),
                        "p25": float("nan"),
                        "p50": float("nan"),
                        "p75": float("nan"),
                        "p85": float("nan"),
                        "p90": float("nan"),
                        "p95": float("nan"),
                        "p99": float("nan"),
                    }
                )
                continue
            rows.append(
                {
                    "roster": roster_label,
                    "half": half_name,
                    "symbol": sym,
                    "n_trades": int(len(sub)),
                    "mean": float(np.mean(sub)),
                    "p10": float(np.percentile(sub, 10)),
                    "p25": float(np.percentile(sub, 25)),
                    "p50": float(np.percentile(sub, 50)),
                    "p75": float(np.percentile(sub, 75)),
                    "p85": float(np.percentile(sub, 85)),
                    "p90": float(np.percentile(sub, 90)),
                    "p95": float(np.percentile(sub, 95)),
                    "p99": float(np.percentile(sub, 99)),
                }
            )

        # Portfolio aggregate
        all_natr = df["natr_14_at_entry"].to_numpy()
        rows.append(
            {
                "roster": roster_label,
                "half": half_name,
                "symbol": "PORTFOLIO",
                "n_trades": int(len(all_natr)),
                "mean": float(np.mean(all_natr)),
                "p10": float(np.percentile(all_natr, 10)),
                "p25": float(np.percentile(all_natr, 25)),
                "p50": float(np.percentile(all_natr, 50)),
                "p75": float(np.percentile(all_natr, 75)),
                "p85": float(np.percentile(all_natr, 85)),
                "p90": float(np.percentile(all_natr, 90)),
                "p95": float(np.percentile(all_natr, 95)),
                "p99": float(np.percentile(all_natr, 99)),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Phase 1.2 — Binary kill oracle: at each threshold, skip trades with
# NATR_14 > threshold; recompute portfolio + per-symbol PnL.
# ---------------------------------------------------------------------------


def _binary_kill_per_symbol(
    df: pd.DataFrame, threshold_pct: float, half_label: str, roster_label: str
) -> list[dict]:
    """For one threshold and one half, compute per-symbol + portfolio impact.

    Returns one row per (roster, half, symbol, threshold) including PORTFOLIO.
    """
    out_rows = []
    kept_mask = df["natr_14_at_entry"] <= threshold_pct
    df_kept = df[kept_mask]

    # Per-symbol aggregation
    for sym in V1_BASELINE_UNIVERSE:
        sub_all = df[df["symbol"] == sym]
        sub_kept = df_kept[df_kept["symbol"] == sym]
        n_trades_baseline = int(len(sub_all))
        n_trades_kept = int(len(sub_kept))
        n_skipped = n_trades_baseline - n_trades_kept
        wpnl_baseline = float(sub_all["weighted_pnl"].sum())
        wpnl_kept = float(sub_kept["weighted_pnl"].sum())
        out_rows.append(
            {
                "roster": roster_label,
                "half": half_label,
                "symbol": sym,
                "threshold_pct": threshold_pct,
                "n_trades_baseline": n_trades_baseline,
                "n_trades_kept": n_trades_kept,
                "n_skipped": n_skipped,
                "skip_rate": (n_skipped / n_trades_baseline) if n_trades_baseline > 0 else 0.0,
                "wpnl_baseline": wpnl_baseline,
                "wpnl_kept": wpnl_kept,
                "wpnl_delta": wpnl_kept - wpnl_baseline,
            }
        )

    # Portfolio aggregate
    n_baseline_all = int(len(df))
    n_kept_all = int(len(df_kept))
    n_skipped_all = n_baseline_all - n_kept_all
    wpnl_b = float(df["weighted_pnl"].sum())
    wpnl_k = float(df_kept["weighted_pnl"].sum())
    out_rows.append(
        {
            "roster": roster_label,
            "half": half_label,
            "symbol": "PORTFOLIO",
            "threshold_pct": threshold_pct,
            "n_trades_baseline": n_baseline_all,
            "n_trades_kept": n_kept_all,
            "n_skipped": n_skipped_all,
            "skip_rate": (n_skipped_all / n_baseline_all) if n_baseline_all > 0 else 0.0,
            "wpnl_baseline": wpnl_b,
            "wpnl_kept": wpnl_k,
            "wpnl_delta": wpnl_k - wpnl_b,
        }
    )
    return out_rows


def binary_kill_per_symbol_table(
    roster_is: Path, roster_oos: Path, roster_label: str, thresholds: tuple[float, ...]
) -> pd.DataFrame:
    """Per-symbol skip-rate + PnL Δ at each threshold, for given roster."""
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    all_rows = []
    for half_label, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        natrs = [
            natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
        ]
        df["natr_14_at_entry"] = natrs
        df = df.dropna(subset=["natr_14_at_entry"]).copy()
        for thr in thresholds:
            all_rows.extend(_binary_kill_per_symbol(df, thr, half_label, roster_label))
    return pd.DataFrame(all_rows)


# ---------------------------------------------------------------------------
# Phase 1.3 — Oracle monthly Sharpe Δ (the key calibration table)
# ---------------------------------------------------------------------------


def oracle_sharpe_delta_table(
    roster_is: Path, roster_oos: Path, roster_label: str, thresholds: tuple[float, ...]
) -> pd.DataFrame:
    """Per (half, threshold), compute oracle monthly Sharpe + Δ vs baseline-roster."""
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    rows = []
    for half_label, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        natrs = [
            natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
        ]
        df["natr_14_at_entry"] = natrs
        df = df.dropna(subset=["natr_14_at_entry"]).copy()
        df["close_dt"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
        df["month"] = df["close_dt"].dt.strftime("%Y-%m")

        # Baseline (no kill) — gives the roster's own monthly Sharpe
        monthly_b = df.groupby("month")["weighted_pnl"].sum()
        mean_b = float(monthly_b.mean())
        std_b = float(monthly_b.std(ddof=0))
        sharpe_b = (mean_b / std_b) if std_b > 0 else 0.0

        for thr in thresholds:
            kept_mask = df["natr_14_at_entry"] <= thr
            df_kept = df[kept_mask]
            n_trades_baseline = int(len(df))
            n_kept = int(len(df_kept))
            n_skipped = n_trades_baseline - n_kept
            skip_rate = (n_skipped / n_trades_baseline) if n_trades_baseline > 0 else 0.0

            if n_kept == 0:
                # Degenerate — all trades killed
                rows.append(
                    {
                        "roster": roster_label,
                        "half": half_label,
                        "threshold_pct": thr,
                        "n_trades_baseline": n_trades_baseline,
                        "n_trades_kept": 0,
                        "n_skipped": n_skipped,
                        "skip_rate": skip_rate,
                        "sharpe_baseline": sharpe_b,
                        "sharpe_oracle": 0.0,
                        "sharpe_delta": -sharpe_b,
                        "wpnl_total_baseline": float(df["weighted_pnl"].sum()),
                        "wpnl_total_oracle": 0.0,
                    }
                )
                continue

            monthly_k = df_kept.groupby("month")["weighted_pnl"].sum().reindex(
                monthly_b.index, fill_value=0.0
            )
            mean_k = float(monthly_k.mean())
            std_k = float(monthly_k.std(ddof=0))
            sharpe_k = (mean_k / std_k) if std_k > 0 else 0.0

            rows.append(
                {
                    "roster": roster_label,
                    "half": half_label,
                    "threshold_pct": thr,
                    "n_trades_baseline": n_trades_baseline,
                    "n_trades_kept": n_kept,
                    "n_skipped": n_skipped,
                    "skip_rate": skip_rate,
                    "sharpe_baseline": sharpe_b,
                    "sharpe_oracle": sharpe_k,
                    "sharpe_delta": sharpe_k - sharpe_b,
                    "wpnl_total_baseline": float(df["weighted_pnl"].sum()),
                    "wpnl_total_oracle": float(df_kept["weighted_pnl"].sum()),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Phase 1.4 — Top-N highest-NATR baseline trades (for forensic intuition)
# ---------------------------------------------------------------------------


def top_high_natr_trades(roster_is: Path, roster_oos: Path, roster_label: str) -> pd.DataFrame:
    """Identify the top-20 highest NATR_14 trades per roster — what would be killed first."""
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    all_rows = []
    for half_label, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        natrs = [
            natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
        ]
        df["natr_14_at_entry"] = natrs
        df = df.dropna(subset=["natr_14_at_entry"]).copy()
        df_sorted = df.sort_values("natr_14_at_entry", ascending=False).head(20)
        for _, row in df_sorted.iterrows():
            all_rows.append(
                {
                    "roster": roster_label,
                    "half": half_label,
                    "symbol": row["symbol"],
                    "direction": int(row["direction"]),
                    "open_time": int(row["open_time"]),
                    "exit_reason": row["exit_reason"],
                    "natr_14": float(row["natr_14_at_entry"]),
                    "weight_factor": float(row["weight_factor"]),
                    "net_pnl_pct": float(row["net_pnl_pct"]),
                    "weighted_pnl": float(row["weighted_pnl"]),
                }
            )
    return pd.DataFrame(all_rows)


# ---------------------------------------------------------------------------
# Phase 1.5 — Per-trade exit-reason distribution by NATR bucket
# ---------------------------------------------------------------------------


def exit_reason_by_natr_bucket(
    roster_is: Path, roster_oos: Path, roster_label: str
) -> pd.DataFrame:
    """For each NATR bucket {<3, 3-5, 5-7, >7}, compute exit-reason distribution
    + mean weighted_pnl. Tests whether high-NATR entries are systematically losers."""
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    rows = []
    buckets = [
        ("<3", 0.0, 3.0),
        ("3-5", 3.0, 5.0),
        ("5-7", 5.0, 7.0),
        ("7-9", 7.0, 9.0),
        (">9", 9.0, 999.0),
    ]
    for half_label, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = pd.read_csv(path)
        natrs = [
            natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
        ]
        df["natr_14_at_entry"] = natrs
        df = df.dropna(subset=["natr_14_at_entry"]).copy()
        for label, lo, hi in buckets:
            sub = df[(df["natr_14_at_entry"] > lo) & (df["natr_14_at_entry"] <= hi)]
            n = int(len(sub))
            if n == 0:
                rows.append(
                    {
                        "roster": roster_label,
                        "half": half_label,
                        "natr_bucket": label,
                        "n_trades": 0,
                        "wr": float("nan"),
                        "mean_net_pnl_pct": float("nan"),
                        "sum_weighted_pnl": 0.0,
                        "stop_loss_share": float("nan"),
                        "take_profit_share": float("nan"),
                        "timeout_share": float("nan"),
                    }
                )
                continue
            wins = int((sub["net_pnl_pct"] > 0).sum())
            rows.append(
                {
                    "roster": roster_label,
                    "half": half_label,
                    "natr_bucket": label,
                    "n_trades": n,
                    "wr": wins / n,
                    "mean_net_pnl_pct": float(sub["net_pnl_pct"].mean()),
                    "sum_weighted_pnl": float(sub["weighted_pnl"].sum()),
                    "stop_loss_share": float((sub["exit_reason"] == "stop_loss").mean()),
                    "take_profit_share": float((sub["exit_reason"] == "take_profit").mean()),
                    "timeout_share": float((sub["exit_reason"] == "timeout").mean()),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"# iter-v1/011 — R5 BINARY KILL oracle EDA — {now}")
    print(f"Universe: {V1_BASELINE_UNIVERSE}")
    print(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS}")
    print("")

    thresholds = (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0)

    # Phase 1.1 — entry-time NATR distribution on BOTH rosters
    print("## Phase 1.1 — Per-symbol ENTRY-TIME NATR_14 distribution")
    print("")
    df_dist_baseline = entry_time_natr_distribution(
        BASELINE_TRADES_IS, BASELINE_TRADES_OOS, "baseline"
    )
    df_dist_010 = entry_time_natr_distribution(V1_010_TRADES_IS, V1_010_TRADES_OOS, "v1-010")
    df_dist = pd.concat([df_dist_baseline, df_dist_010], ignore_index=True)
    df_dist.to_csv(OUT_DIR / "entry_time_natr_distribution.csv", index=False)
    print("### BASELINE roster")
    print(df_dist_baseline.to_string(index=False))
    print("")
    print("### /010 EXPLORATION roster")
    print(df_dist_010.to_string(index=False))
    print("")

    # Phase 1.2 — per-symbol skip-rate + PnL Δ
    print("## Phase 1.2 — Per-symbol skip rate + PnL Δ at each threshold (BASELINE roster)")
    df_per_sym_baseline = binary_kill_per_symbol_table(
        BASELINE_TRADES_IS, BASELINE_TRADES_OOS, "baseline", thresholds
    )
    df_per_sym_010 = binary_kill_per_symbol_table(
        V1_010_TRADES_IS, V1_010_TRADES_OOS, "v1-010", thresholds
    )
    df_per_sym = pd.concat([df_per_sym_baseline, df_per_sym_010], ignore_index=True)
    df_per_sym.to_csv(OUT_DIR / "binary_kill_per_symbol_pnl.csv", index=False)
    print(df_per_sym_baseline[df_per_sym_baseline["symbol"] == "PORTFOLIO"].to_string(index=False))
    print("")
    print("## Phase 1.2b — Per-symbol skip rate + PnL Δ at each threshold (/010 roster)")
    print(df_per_sym_010[df_per_sym_010["symbol"] == "PORTFOLIO"].to_string(index=False))
    print("")

    # Phase 1.3 — oracle monthly Sharpe Δ (the key calibration table)
    print("## Phase 1.3 — Oracle monthly Sharpe Δ by threshold (both rosters)")
    df_sharpe_baseline = oracle_sharpe_delta_table(
        BASELINE_TRADES_IS, BASELINE_TRADES_OOS, "baseline", thresholds
    )
    df_sharpe_010 = oracle_sharpe_delta_table(
        V1_010_TRADES_IS, V1_010_TRADES_OOS, "v1-010", thresholds
    )
    df_sharpe = pd.concat([df_sharpe_baseline, df_sharpe_010], ignore_index=True)
    df_sharpe.to_csv(OUT_DIR / "oracle_sharpe_delta.csv", index=False)
    print("### BASELINE roster")
    print(df_sharpe_baseline.to_string(index=False))
    print("")
    print("### /010 EXPLORATION roster")
    print(df_sharpe_010.to_string(index=False))
    print("")

    # Phase 1.4 — top high-NATR trades (forensic intuition)
    print("## Phase 1.4 — Top-20 highest-NATR baseline trades (would be killed at low thresholds)")
    df_top_baseline = top_high_natr_trades(BASELINE_TRADES_IS, BASELINE_TRADES_OOS, "baseline")
    df_top_010 = top_high_natr_trades(V1_010_TRADES_IS, V1_010_TRADES_OOS, "v1-010")
    df_top = pd.concat([df_top_baseline, df_top_010], ignore_index=True)
    df_top.to_csv(OUT_DIR / "top_high_natr_trades.csv", index=False)
    print("### Top 5 by NATR — BASELINE OOS")
    sub = df_top_baseline[df_top_baseline["half"] == "OOS"].head(5)
    print(sub.to_string(index=False))
    print("")

    # Phase 1.5 — exit-reason by NATR bucket
    print("## Phase 1.5 — Exit-reason distribution by NATR bucket")
    df_exits_baseline = exit_reason_by_natr_bucket(
        BASELINE_TRADES_IS, BASELINE_TRADES_OOS, "baseline"
    )
    df_exits_010 = exit_reason_by_natr_bucket(V1_010_TRADES_IS, V1_010_TRADES_OOS, "v1-010")
    df_exits = pd.concat([df_exits_baseline, df_exits_010], ignore_index=True)
    df_exits.to_csv(OUT_DIR / "exit_reason_by_natr_bucket.csv", index=False)
    print("### BASELINE roster")
    print(df_exits_baseline.to_string(index=False))
    print("")
    print("### /010 EXPLORATION roster")
    print(df_exits_010.to_string(index=False))
    print("")

    # Calibration summary — best OOS Δ threshold per roster
    print("## Phase 1.6 — Calibration summary: best OOS Δ threshold + F2 fire rate")
    print("")
    for roster in ("baseline", "v1-010"):
        oos = df_sharpe[(df_sharpe["roster"] == roster) & (df_sharpe["half"] == "OOS")].copy()
        if len(oos) == 0:
            continue
        oos = oos.sort_values("sharpe_delta", ascending=False)
        best = oos.iloc[0]
        print(f"### Roster: {roster}")
        print(
            f"  best OOS Δ = {best['sharpe_delta']:+.4f} at threshold {best['threshold_pct']}% "
            f"(skip rate {best['skip_rate']:.3%}, "
            f"{best['n_skipped']:.0f} of {best['n_trades_baseline']:.0f} OOS trades killed)"
        )
        # F2 band check
        oos_in_band = oos[(oos["skip_rate"] >= 0.10) & (oos["skip_rate"] <= 0.60)]
        if len(oos_in_band) > 0:
            best_in_band = oos_in_band.sort_values("sharpe_delta", ascending=False).iloc[0]
            print(
                f"  best IN-F2-BAND threshold {best_in_band['threshold_pct']}% "
                f"(skip rate {best_in_band['skip_rate']:.3%}, "
                f"OOS Δ {best_in_band['sharpe_delta']:+.4f})"
            )
        else:
            print(f"  NO threshold puts skip rate in F2 band [10%, 60%] for {roster} OOS")
        print("")

    print("Outputs written:")
    for fn in (
        "entry_time_natr_distribution.csv",
        "binary_kill_per_symbol_pnl.csv",
        "oracle_sharpe_delta.csv",
        "top_high_natr_trades.csv",
        "exit_reason_by_natr_bucket.csv",
    ):
        print(f"  {OUT_DIR}/{fn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

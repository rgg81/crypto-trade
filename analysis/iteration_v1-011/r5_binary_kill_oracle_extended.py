"""iter-v1/011 — R5 BINARY KILL EXTENDED EDA.

Phase 1 INITIAL EDA (r5_binary_kill_oracle.py) revealed a critical surprise:
  - At convergent threshold 7%, OOS skip rate is 0.5% (1 trade), F1 OOS Δ = -0.001
  - NO threshold in {5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0} hits F2 fire rate band [10%, 60%] OOS
  - Phase 1.5 exit-reason analysis: high-NATR (5-7%) OOS WR = 77.8% / mean PnL +5.14%
    vs low-NATR (<3%) OOS WR = 31.7% / mean PnL -0.41%
  - High-NATR entries are EMPIRICAL WINNERS not losers; convergent hypothesis INVERTED

The /010 EDA (candle-level NATR distribution) used universe p90 ≈ 6.3% for sizing
the 7% threshold; the model's actual entry-time NATR p90 is 4.30% (OOS) — the
feature space already selects lower-vol moments. Killing the "high-NATR tail"
removes WINNERS because the residual high-NATR entries that survived the
predictor's confidence gating are precisely the high-conviction moves.

This script extends the EDA to:

1. LOW threshold sweep {3.0, 3.5, 4.0, 4.5} — to put skip rate in F2 band [10%, 60%]
   and validate whether killing low-NATR entries (empirical losers) improves Sharpe.
2. INVERTED kill switch: skip entry if NATR_14 < threshold (kill the LOSERS).
3. Per-symbol oracle: are there symbols where the high-vs-low pattern flips?
4. Confidence-conditional analysis: maybe high-NATR is good ONLY when confidence is high.

Outputs:
- low_threshold_high_kill_oracle.csv (skip if NATR > threshold; low values)
- inverted_kill_oracle.csv (skip if NATR < threshold)
- per_symbol_natr_pnl_pattern.csv (per-symbol NATR×PnL pattern)
- confidence_x_natr_table.csv (confidence × NATR bucket cross-tab)
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

BASELINE_TRADES_IS = ROOT / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
BASELINE_TRADES_OOS = (
    ROOT / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
)
V1_010_TRADES_IS = ROOT / "reports-v1" / "iteration_v1-010" / "in_sample" / "trades.csv"
V1_010_TRADES_OOS = ROOT / "reports-v1" / "iteration_v1-010" / "out_of_sample" / "trades.csv"


def load_natr_lookup(symbol: str) -> dict[int, float]:
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path, columns=["open_time", "vol_natr_14"])
    df = df.dropna(subset=["vol_natr_14"])
    return dict(zip(df["open_time"].to_numpy(), df["vol_natr_14"].to_numpy(), strict=True))


def _align_trade_ot(ot: int) -> int:
    return int(ot) + 1


def _load_trades_with_natr(path: Path) -> pd.DataFrame:
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}
    df = pd.read_csv(path)
    natrs = [
        natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
        for sym, ot in zip(df["symbol"], df["open_time"], strict=True)
    ]
    df["natr_14_at_entry"] = natrs
    df = df.dropna(subset=["natr_14_at_entry"]).copy()
    df["close_dt"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df["month"] = df["close_dt"].dt.strftime("%Y-%m")
    return df


def _portfolio_sharpe(df: pd.DataFrame, all_months: pd.Index) -> float:
    monthly = df.groupby("month")["weighted_pnl"].sum().reindex(all_months, fill_value=0.0)
    mean_, std_ = float(monthly.mean()), float(monthly.std(ddof=0))
    return (mean_ / std_) if std_ > 0 else 0.0


def _oracle_table(
    roster_label: str,
    roster_is: Path,
    roster_oos: Path,
    thresholds: tuple[float, ...],
    direction: str,
) -> pd.DataFrame:
    """direction='kill_high' → skip if NATR > threshold (Path A; matches initial EDA).
    direction='kill_low' → skip if NATR < threshold (Path B inverted)."""
    rows = []
    for half_label, path in (("IS", roster_is), ("OOS", roster_oos)):
        if not path.exists():
            continue
        df = _load_trades_with_natr(path)
        all_months = df.groupby("month")["weighted_pnl"].sum().index
        sharpe_b = _portfolio_sharpe(df, all_months)
        for thr in thresholds:
            if direction == "kill_high":
                kept = df[df["natr_14_at_entry"] <= thr]
            elif direction == "kill_low":
                kept = df[df["natr_14_at_entry"] >= thr]
            else:
                raise ValueError(direction)
            n_b, n_k = len(df), len(kept)
            n_s = n_b - n_k
            sharpe_o = _portfolio_sharpe(kept, all_months) if n_k > 0 else 0.0
            rows.append(
                {
                    "roster": roster_label,
                    "half": half_label,
                    "direction": direction,
                    "threshold_pct": thr,
                    "n_trades_baseline": n_b,
                    "n_trades_kept": n_k,
                    "n_skipped": n_s,
                    "skip_rate": (n_s / n_b) if n_b > 0 else 0.0,
                    "sharpe_baseline": sharpe_b,
                    "sharpe_oracle": sharpe_o,
                    "sharpe_delta": sharpe_o - sharpe_b,
                    "wpnl_total_baseline": float(df["weighted_pnl"].sum()),
                    "wpnl_total_oracle": float(kept["weighted_pnl"].sum()) if n_k > 0 else 0.0,
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Path A — LOW-side high-kill threshold sweep (3.0-5.0)
# ---------------------------------------------------------------------------


def path_a_low_threshold_high_kill() -> pd.DataFrame:
    thresholds = (3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0)
    base = _oracle_table("baseline", BASELINE_TRADES_IS, BASELINE_TRADES_OOS, thresholds, "kill_high")
    v010 = _oracle_table("v1-010", V1_010_TRADES_IS, V1_010_TRADES_OOS, thresholds, "kill_high")
    df = pd.concat([base, v010], ignore_index=True)
    df.to_csv(OUT_DIR / "low_threshold_high_kill_oracle.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Path B — INVERTED kill: skip if NATR < threshold (kill the LOSERS)
# ---------------------------------------------------------------------------


def path_b_inverted_low_kill() -> pd.DataFrame:
    thresholds = (2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0)
    base = _oracle_table("baseline", BASELINE_TRADES_IS, BASELINE_TRADES_OOS, thresholds, "kill_low")
    v010 = _oracle_table("v1-010", V1_010_TRADES_IS, V1_010_TRADES_OOS, thresholds, "kill_low")
    df = pd.concat([base, v010], ignore_index=True)
    df.to_csv(OUT_DIR / "inverted_low_kill_oracle.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Per-symbol NATR×PnL pattern (does the inversion hold across symbols?)
# ---------------------------------------------------------------------------


def per_symbol_natr_pnl_pattern() -> pd.DataFrame:
    """Per (roster, half, symbol, natr_bucket), compute n_trades / wr / mean_net_pnl_pct."""
    rows = []
    buckets = [
        ("<2.5", 0.0, 2.5),
        ("2.5-3", 2.5, 3.0),
        ("3-3.5", 3.0, 3.5),
        ("3.5-4", 3.5, 4.0),
        ("4-5", 4.0, 5.0),
        (">5", 5.0, 999.0),
    ]
    for roster_label, paths in (
        ("baseline", (BASELINE_TRADES_IS, BASELINE_TRADES_OOS)),
        ("v1-010", (V1_010_TRADES_IS, V1_010_TRADES_OOS)),
    ):
        for half_label, path in (("IS", paths[0]), ("OOS", paths[1])):
            if not path.exists():
                continue
            df = _load_trades_with_natr(path)
            for sym in V1_BASELINE_UNIVERSE:
                for label, lo, hi in buckets:
                    sub = df[
                        (df["symbol"] == sym)
                        & (df["natr_14_at_entry"] > lo)
                        & (df["natr_14_at_entry"] <= hi)
                    ]
                    n = len(sub)
                    if n == 0:
                        continue
                    wins = int((sub["net_pnl_pct"] > 0).sum())
                    rows.append(
                        {
                            "roster": roster_label,
                            "half": half_label,
                            "symbol": sym,
                            "natr_bucket": label,
                            "n_trades": n,
                            "wr": wins / n,
                            "mean_net_pnl_pct": float(sub["net_pnl_pct"].mean()),
                            "sum_weighted_pnl": float(sub["weighted_pnl"].sum()),
                        }
                    )
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "per_symbol_natr_pnl_pattern.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# Confidence × NATR bucket
# ---------------------------------------------------------------------------


def confidence_x_natr_table() -> pd.DataFrame:
    """Test interaction: is high-NATR good ONLY when confidence is high?
    Confidence buckets: <0.55, 0.55-0.65, 0.65-0.75, >0.75
    NATR buckets: <3, 3-5, >5
    """
    natr_buckets = [("<3", 0.0, 3.0), ("3-5", 3.0, 5.0), (">5", 5.0, 999.0)]
    conf_buckets = [
        ("<0.55", 0.0, 0.55),
        ("0.55-0.65", 0.55, 0.65),
        ("0.65-0.75", 0.65, 0.75),
        (">0.75", 0.75, 1.01),
    ]
    rows = []
    for roster_label, paths in (
        ("baseline", (BASELINE_TRADES_IS, BASELINE_TRADES_OOS)),
        ("v1-010", (V1_010_TRADES_IS, V1_010_TRADES_OOS)),
    ):
        for half_label, path in (("IS", paths[0]), ("OOS", paths[1])):
            if not path.exists():
                continue
            df = _load_trades_with_natr(path)
            for nat_lab, lo, hi in natr_buckets:
                for con_lab, clo, chi in conf_buckets:
                    sub = df[
                        (df["natr_14_at_entry"] > lo)
                        & (df["natr_14_at_entry"] <= hi)
                        & (df["confidence"] > clo)
                        & (df["confidence"] <= chi)
                    ]
                    n = len(sub)
                    if n == 0:
                        continue
                    wins = int((sub["net_pnl_pct"] > 0).sum())
                    rows.append(
                        {
                            "roster": roster_label,
                            "half": half_label,
                            "natr_bucket": nat_lab,
                            "conf_bucket": con_lab,
                            "n_trades": n,
                            "wr": wins / n,
                            "mean_net_pnl_pct": float(sub["net_pnl_pct"].mean()),
                            "sum_weighted_pnl": float(sub["weighted_pnl"].sum()),
                        }
                    )
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "confidence_x_natr_table.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# F2-band-respecting calibration summary
# ---------------------------------------------------------------------------


def calibration_summary(df_a: pd.DataFrame, df_b: pd.DataFrame) -> None:
    """For each (roster, direction), find threshold maximizing OOS Sharpe Δ
    SUBJECT TO skip rate ∈ [10%, 60%] AND skip rate ∈ [5%, 30%] (relaxed band)."""
    print("## Calibration summary — best threshold in F2 band")
    print("")
    for df, name in ((df_a, "kill_high"), (df_b, "kill_low")):
        for roster in ("baseline", "v1-010"):
            oos = df[(df["roster"] == roster) & (df["half"] == "OOS")].copy()
            if len(oos) == 0:
                continue
            in_strict_band = oos[(oos["skip_rate"] >= 0.10) & (oos["skip_rate"] <= 0.60)]
            in_relaxed_band = oos[(oos["skip_rate"] >= 0.05) & (oos["skip_rate"] <= 0.30)]
            print(f"### {name} — {roster}")
            if len(in_strict_band) > 0:
                best = in_strict_band.sort_values("sharpe_delta", ascending=False).iloc[0]
                print(
                    f"  STRICT band [10%, 60%]: best thr {best['threshold_pct']}% "
                    f"skip {best['skip_rate']:.2%} Δ {best['sharpe_delta']:+.4f}"
                )
            else:
                print("  STRICT band [10%, 60%]: NO candidates")
            if len(in_relaxed_band) > 0:
                best_r = in_relaxed_band.sort_values("sharpe_delta", ascending=False).iloc[0]
                print(
                    f"  RELAXED band [5%, 30%]: best thr {best_r['threshold_pct']}% "
                    f"skip {best_r['skip_rate']:.2%} Δ {best_r['sharpe_delta']:+.4f}"
                )
            else:
                print("  RELAXED band [5%, 30%]: NO candidates")
            best_uncon = oos.sort_values("sharpe_delta", ascending=False).iloc[0]
            print(
                f"  UNCONSTRAINED best: thr {best_uncon['threshold_pct']}% "
                f"skip {best_uncon['skip_rate']:.2%} Δ {best_uncon['sharpe_delta']:+.4f}"
            )
            print("")


def main() -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"# iter-v1/011 — Extended R5 BINARY KILL oracle EDA — {now}")
    print(f"Universe: {V1_BASELINE_UNIVERSE}")
    print(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS}")
    print("")

    print("## Path A — LOW-threshold high-kill sweep (kill_high; skip if NATR > thr)")
    df_a = path_a_low_threshold_high_kill()
    print("### BASELINE roster")
    print(df_a[df_a["roster"] == "baseline"].to_string(index=False))
    print("")
    print("### /010 EXPLORATION roster")
    print(df_a[df_a["roster"] == "v1-010"].to_string(index=False))
    print("")

    print("## Path B — INVERTED low-kill sweep (kill_low; skip if NATR < thr)")
    df_b = path_b_inverted_low_kill()
    print("### BASELINE roster")
    print(df_b[df_b["roster"] == "baseline"].to_string(index=False))
    print("")
    print("### /010 EXPLORATION roster")
    print(df_b[df_b["roster"] == "v1-010"].to_string(index=False))
    print("")

    print("## Per-symbol NATR×PnL pattern (does inversion hold per-symbol?)")
    df_sym = per_symbol_natr_pnl_pattern()
    # Print BASELINE OOS only (most interesting for verdict)
    print("### BASELINE OOS per-symbol NATR×PnL")
    print(
        df_sym[
            (df_sym["roster"] == "baseline") & (df_sym["half"] == "OOS")
        ].to_string(index=False)
    )
    print("")

    print("## Confidence × NATR cross-tab")
    df_cx = confidence_x_natr_table()
    print("### BASELINE OOS confidence × NATR")
    print(
        df_cx[(df_cx["roster"] == "baseline") & (df_cx["half"] == "OOS")].to_string(index=False)
    )
    print("")

    calibration_summary(df_a, df_b)

    print("Outputs written:")
    for fn in (
        "low_threshold_high_kill_oracle.csv",
        "inverted_low_kill_oracle.csv",
        "per_symbol_natr_pnl_pattern.csv",
        "confidence_x_natr_table.csv",
    ):
        print(f"  {OUT_DIR}/{fn}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

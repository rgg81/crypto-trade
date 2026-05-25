"""iter-v1/010 — R5 vol-target ceiling calibration.

Per-symbol IS-only NATR distribution analysis + cap fire-rate simulation
for the R5 vol-target ceiling primitive proposed at /010.

R5 design (from /009 closeout + LM Master /009 Phase 7.4 PRIMARY recommendation):

    R5_cap_ratio = min(1.0, vol_target_pct / max(NATR, eps))

Operates AFTER R2 vol-targeting (vt_scale):

    weight_factor = vt_scale * R5_cap_ratio

The brief asks for "NATR_28d". The v1 feature library exposes NATR for
periods (7, 14, 21) only. At 8h cadence, "28d" would mean ~84 candles
(too noisy for cap calibration) or "28 candles" = ~9.3 days. The closest
available column ALREADY in V1_FEATURE_COLUMNS_PRUNED is `vol_natr_14`
(14 candles = 4.67 days = ~1 week). NATR_14 is the canonical "weekly
volatility" reference at 8h cadence, identical to the column the model
itself reads at feature time and identical to what /008 used in its
DEGENERATE_PREDICTOR detector. Using vol_natr_14 keeps R5 calibration
in lock-step with what is already loaded into the predictor pipeline
(no parallel volatility lineage).

The script outputs:

1. Per-symbol IS NATR_14 percentile distribution (p10/p25/p50/p75/p90/p95/p99)
2. Per-symbol fire rate at candidate vol_target_pct values {2.0, 2.5, 3.0, 3.5}
3. Mean cap value when triggered (intensity)
4. Sample-trade simulation: load BASELINE trades (reports-v1/iteration_v1-baseline/),
   join NATR_14 by (symbol, open_time), compute R5 ratio per trade,
   show fire-rate at trade level vs candle level.

Outputs CSV tables to `analysis/iteration_v1-010/` next to this script.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Make src/ importable so we can read the canonical constants
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


# ---------------------------------------------------------------------------
# Phase 1.1 — per-symbol IS NATR_14 distribution
# ---------------------------------------------------------------------------


def load_is_natr(symbol: str) -> pd.DataFrame:
    """Load IS-window (open_time < OOS_CUTOFF_MS) NATR_14 for *symbol*."""
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path, columns=["open_time", "vol_natr_14"])
    df = df.dropna(subset=["vol_natr_14"])
    df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    return df_is


def per_symbol_natr_distribution() -> pd.DataFrame:
    """Compute p10/p25/p50/p75/p90/p95/p99 of IS NATR_14 per symbol."""
    rows = []
    for sym in V1_BASELINE_UNIVERSE:
        df = load_is_natr(sym)
        natr = df["vol_natr_14"].to_numpy()
        rows.append(
            {
                "symbol": sym,
                "n_candles": int(len(natr)),
                "mean": float(np.mean(natr)),
                "p10": float(np.percentile(natr, 10)),
                "p25": float(np.percentile(natr, 25)),
                "p50": float(np.percentile(natr, 50)),
                "p75": float(np.percentile(natr, 75)),
                "p90": float(np.percentile(natr, 90)),
                "p95": float(np.percentile(natr, 95)),
                "p99": float(np.percentile(natr, 99)),
            }
        )
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "per_symbol_is_natr14_distribution.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# Phase 1.2 — candle-level fire-rate simulation at candidate vol_target_pct
# ---------------------------------------------------------------------------


def compute_r5_cap(natr: np.ndarray, vol_target_pct: float, eps: float = 0.01) -> np.ndarray:
    """R5 cap formula: min(1.0, vol_target_pct / max(natr, eps))."""
    denom = np.maximum(natr, eps)
    return np.minimum(1.0, vol_target_pct / denom)


def candle_level_fire_rate(targets: tuple[float, ...] = (2.0, 2.5, 3.0, 3.5)) -> pd.DataFrame:
    """For each (symbol, vol_target_pct), compute fire rate (cap < 1.0)
    and mean cap value when triggered.
    """
    rows = []
    for sym in V1_BASELINE_UNIVERSE:
        df = load_is_natr(sym)
        natr = df["vol_natr_14"].to_numpy()
        for t in targets:
            cap = compute_r5_cap(natr, t)
            fired = cap < 1.0 - 1e-9
            fire_rate = float(np.mean(fired))
            mean_cap_fired = float(np.mean(cap[fired])) if fired.any() else float("nan")
            min_cap = float(np.min(cap))
            rows.append(
                {
                    "symbol": sym,
                    "vol_target_pct": t,
                    "n_candles": int(len(natr)),
                    "fire_rate": fire_rate,
                    "mean_cap_when_fired": mean_cap_fired,
                    "min_cap": min_cap,
                    "mean_cap_all": float(np.mean(cap)),
                }
            )
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "candle_level_fire_rate_by_target.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# Phase 1.3 — trade-level fire-rate (join baseline trades with NATR at entry)
# ---------------------------------------------------------------------------


def load_natr_lookup(symbol: str) -> dict[int, float]:
    """Build open_time → vol_natr_14 lookup for *symbol*.

    Note on open_time convention: trade CSVs use Binance's
    ``open_time = candle_open_ms - 1`` convention (e.g., 1742831999999
    is the trade entered at the 1742832000000 candle close). Feature
    parquets use the raw candle-open ms. We normalize by adding 1 to
    the trade open_time at join time (see ``_align_trade_ot``).
    """
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path, columns=["open_time", "vol_natr_14"])
    df = df.dropna(subset=["vol_natr_14"])
    return dict(zip(df["open_time"].to_numpy(), df["vol_natr_14"].to_numpy(), strict=True))


def _align_trade_ot(ot: int) -> int:
    """Trade-CSV open_time uses ``candle_open_ms - 1``; +1 aligns to parquet."""
    return int(ot) + 1


def trade_level_fire_rate(
    targets: tuple[float, ...] = (2.0, 2.5, 3.0, 3.5),
) -> pd.DataFrame:
    """Simulate R5 cap on the baseline trade roster (5-seed v0.v1-baseline-corrected).

    For each trade in IS + OOS rosters, look up NATR_14 at open_time, compute
    R5 cap, and aggregate fire-rate per (symbol, half, vol_target_pct).
    """
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}

    out_rows = []
    for half_name, path in (
        ("IS", BASELINE_TRADES_IS),
        ("OOS", BASELINE_TRADES_OOS),
    ):
        if not path.exists():
            print(f"Warning: {path} does not exist", file=sys.stderr)
            continue
        df = pd.read_csv(path)
        # Join NATR by (symbol, open_time). Align trade open_time to parquet
        # convention (+1 ms; trade-CSV stores candle_open - 1).
        natrs = []
        for sym, ot in zip(df["symbol"], df["open_time"], strict=True):
            natr = natr_lookups.get(sym, {}).get(_align_trade_ot(ot), float("nan"))
            natrs.append(natr)
        df["natr_14_at_entry"] = natrs
        df_known = df.dropna(subset=["natr_14_at_entry"]).copy()

        for t in targets:
            cap = compute_r5_cap(df_known["natr_14_at_entry"].to_numpy(), t)
            df_known[f"r5_cap_t{t}"] = cap

            # Per-symbol aggregation
            for sym in V1_BASELINE_UNIVERSE:
                sub = df_known[df_known["symbol"] == sym]
                if len(sub) == 0:
                    continue
                sub_cap = sub[f"r5_cap_t{t}"].to_numpy()
                fired = sub_cap < 1.0 - 1e-9
                fire_rate = float(np.mean(fired))
                mean_cap_fired = (
                    float(np.mean(sub_cap[fired])) if fired.any() else float("nan")
                )
                # PnL preserved: weighted_pnl is what would scale by R5 cap
                wpnl_orig = float(sub["weighted_pnl"].sum())
                wpnl_r5 = float((sub["weighted_pnl"] * sub_cap).sum())
                wpnl_delta = wpnl_r5 - wpnl_orig

                out_rows.append(
                    {
                        "half": half_name,
                        "symbol": sym,
                        "vol_target_pct": t,
                        "n_trades": int(len(sub)),
                        "fire_rate": fire_rate,
                        "mean_cap_when_fired": mean_cap_fired,
                        "mean_cap_all": float(np.mean(sub_cap)),
                        "min_cap": float(np.min(sub_cap)),
                        "wpnl_orig": wpnl_orig,
                        "wpnl_r5_simulated": wpnl_r5,
                        "wpnl_delta_pct": wpnl_delta,
                    }
                )

            # Portfolio aggregation (all-symbols)
            cap_all = df_known[f"r5_cap_t{t}"].to_numpy()
            fired_all = cap_all < 1.0 - 1e-9
            wpnl_orig_all = float(df_known["weighted_pnl"].sum())
            wpnl_r5_all = float((df_known["weighted_pnl"] * cap_all).sum())
            out_rows.append(
                {
                    "half": half_name,
                    "symbol": "PORTFOLIO",
                    "vol_target_pct": t,
                    "n_trades": int(len(df_known)),
                    "fire_rate": float(np.mean(fired_all)),
                    "mean_cap_when_fired": (
                        float(np.mean(cap_all[fired_all])) if fired_all.any() else float("nan")
                    ),
                    "mean_cap_all": float(np.mean(cap_all)),
                    "min_cap": float(np.min(cap_all)),
                    "wpnl_orig": wpnl_orig_all,
                    "wpnl_r5_simulated": wpnl_r5_all,
                    "wpnl_delta_pct": wpnl_r5_all - wpnl_orig_all,
                }
            )

    df_out = pd.DataFrame(out_rows)
    df_out.to_csv(OUT_DIR / "trade_level_fire_rate_simulated.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# Phase 1.4 — Sharpe-impact simulation (oracle EDA caveat per /054)
# ---------------------------------------------------------------------------


def simulated_sharpe_delta(
    targets: tuple[float, ...] = (2.0, 2.5, 3.0, 3.5),
) -> pd.DataFrame:
    """Compute monthly-Sharpe deltas under R5 scaling on baseline trade roster.

    PER /054 ORACLE EDA caveat: R5 is STATELESS (cap depends only on
    NATR_14 at open_time, NOT on persistent state updated by signal
    emission). Oracle EDA on prior trade roster is VALID for stateless
    gates. R5 satisfies this.

    BUT: this simulation is informational only. The actual /010 backtest
    runs the strategy with R5 wiring inside the labeling/training loop;
    Optuna will re-optimize against scaled trade rewards. Real OOS may
    diverge from this oracle estimate by ±20% per F2 mechanism risk.
    """
    natr_lookups = {sym: load_natr_lookup(sym) for sym in V1_BASELINE_UNIVERSE}

    rows = []
    for half_name, path in (
        ("IS", BASELINE_TRADES_IS),
        ("OOS", BASELINE_TRADES_OOS),
    ):
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

        # Baseline monthly Sharpe (already in BASELINE_V1.md)
        monthly_orig = df.groupby("month")["weighted_pnl"].sum()
        mean_o = float(monthly_orig.mean())
        std_o = float(monthly_orig.std(ddof=0))
        sharpe_orig = mean_o / std_o if std_o > 0 else 0.0

        for t in targets:
            cap = compute_r5_cap(df["natr_14_at_entry"].to_numpy(), t)
            df["wpnl_r5"] = df["weighted_pnl"].to_numpy() * cap
            monthly_r5 = df.groupby("month")["wpnl_r5"].sum()
            mean_r = float(monthly_r5.mean())
            std_r = float(monthly_r5.std(ddof=0))
            sharpe_r5 = mean_r / std_r if std_r > 0 else 0.0

            rows.append(
                {
                    "half": half_name,
                    "vol_target_pct": t,
                    "n_trades": int(len(df)),
                    "n_months": int(len(monthly_orig)),
                    "monthly_sharpe_baseline": sharpe_orig,
                    "monthly_sharpe_r5_oracle": sharpe_r5,
                    "monthly_sharpe_delta_oracle": sharpe_r5 - sharpe_orig,
                    "wpnl_total_baseline": float(df["weighted_pnl"].sum()),
                    "wpnl_total_r5_oracle": float(df["wpnl_r5"].sum()),
                    "fire_rate": float(np.mean(cap < 1.0 - 1e-9)),
                    "mean_cap_all_trades": float(np.mean(cap)),
                }
            )

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "simulated_sharpe_delta_oracle.csv", index=False)
    return df_out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"# iter-v1/010 R5 vol-target calibration — {now}")
    print(f"Universe: {V1_BASELINE_UNIVERSE}")
    print(f"OOS_CUTOFF_MS: {OOS_CUTOFF_MS}")
    print("")

    print("## Phase 1.1 — Per-symbol IS NATR_14 distribution")
    df1 = per_symbol_natr_distribution()
    print(df1.to_string(index=False))
    print("")

    print("## Phase 1.2 — Candle-level fire rate by vol_target_pct")
    df2 = candle_level_fire_rate()
    print(df2.to_string(index=False))
    print("")

    print("## Phase 1.3 — Trade-level fire rate (baseline roster oracle)")
    df3 = trade_level_fire_rate()
    print(df3.to_string(index=False))
    print("")

    print("## Phase 1.4 — Oracle Sharpe delta simulation")
    df4 = simulated_sharpe_delta()
    print(df4.to_string(index=False))
    print("")

    print("Outputs written to:")
    print(f"  {OUT_DIR}/per_symbol_is_natr14_distribution.csv")
    print(f"  {OUT_DIR}/candle_level_fire_rate_by_target.csv")
    print(f"  {OUT_DIR}/trade_level_fire_rate_simulated.csv")
    print(f"  {OUT_DIR}/simulated_sharpe_delta_oracle.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())

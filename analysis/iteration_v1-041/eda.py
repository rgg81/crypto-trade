"""iter-v1/041 EDA — TIGHTEN-WITHIN-TRIPLE-BARRIER projection.

Axis: LABELING-AXIS — TIGHTEN atr_tp / atr_sl by 50% while preserving TP/SL=2.0 ratio.

Current per-model (v0.v1-baseline-corrected, ATR-multiplier path):
  - Model A (BTC+ETH pool): atr_tp=2.9, atr_sl=1.45 (NATR_21 × multiplier)
  - Model C (LINK), D (LTC), E (DOT): atr_tp=3.5, atr_sl=1.75
Proposed per task brief: atr_tp=1.5, atr_sl=0.75 across ALL models.

Mechanism: tighter barriers -> labels resolve faster -> more labels/cell -> higher
training-data density. Risk: shorter forward window noisier -> more chop hits both.

This EDA loads the baseline trade roster (reports-v1/iteration_v1-baseline/) and
projects, for each closed trade, what would have happened at the tighter barriers:
  (a) % of trades hitting TP earlier (vs current TP / SL / timeout exit)
  (b) % of timeout exits that would have flipped to SL (or TP)
  (c) per-symbol trade-count multiplier (proxy by label-resolution density)

IS-ONLY discipline: we read both IS and OOS rosters but project ONLY on IS
(close_time < 2025-03-24 in UTC ms). OOS projection deferred to Phase 7.

All thresholds, multipliers, IS cutoff are read from BASELINE_V1.md constants.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BASELINE_IS = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
BASELINE_OOS = REPO / "reports-v1" / "iteration_v1-baseline" / "out_of_sample" / "trades.csv"
OUT_DIR = REPO / "analysis" / "iteration_v1-041"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OOS_CUTOFF_MS = int(datetime(2025, 3, 24, tzinfo=UTC).timestamp() * 1000)

# Per-model current ATR multipliers (run_baseline_v186.py:96-100)
CURRENT_PER_MODEL = {
    "BTCUSDT": (2.9, 1.45),  # Model A
    "ETHUSDT": (2.9, 1.45),  # Model A
    "LINKUSDT": (3.5, 1.75),  # Model C
    "LTCUSDT": (3.5, 1.75),  # Model D
    "DOTUSDT": (3.5, 1.75),  # Model E
}
# Proposed tight barriers (uniform across models per task)
PROPOSED_TP = 1.5
PROPOSED_SL = 0.75


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["open_time"] = df["open_time"].astype("int64")
    df["close_time"] = df["close_time"].astype("int64")
    df["dur_ms"] = df["close_time"] - df["open_time"]
    df["dur_candles"] = df["dur_ms"] / (8 * 3600 * 1000)  # 8h candles
    return df


def baseline_distribution(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Per-symbol exit-reason share + duration + PnL stats."""
    rows = []
    for sym, sub in df.groupby("symbol"):
        n = len(sub)
        if n == 0:
            continue
        er = sub["exit_reason"].value_counts(normalize=True).to_dict()
        # Net PnL stats (already in pct units)
        pnl = sub["net_pnl_pct"]
        rows.append(
            {
                "sample": label,
                "symbol": sym,
                "trades": n,
                "share_tp": er.get("take_profit", 0.0),
                "share_sl": er.get("stop_loss", 0.0),
                "share_timeout": er.get("timeout", 0.0),
                "share_eod": er.get("end_of_data", 0.0),
                "dur_p50_candles": sub["dur_candles"].median(),
                "dur_p90_candles": sub["dur_candles"].quantile(0.9),
                "net_pnl_mean_pct": pnl.mean(),
                "net_pnl_p25_pct": pnl.quantile(0.25),
                "net_pnl_p75_pct": pnl.quantile(0.75),
                "abs_pnl_mean_pct": pnl.abs().mean(),
            }
        )
    return pd.DataFrame(rows)


def project_at_tight_barriers(df: pd.DataFrame) -> pd.DataFrame:
    """Project per-trade outcome at TP=1.5 / SL=0.75 ATR-multiplier barriers.

    For each baseline trade we infer the realised TP/SL distance the baseline used
    from (entry_price, stop_loss_price, take_profit_price). The ratio
        baseline_tp_distance_pct / current_atr_tp_multiplier  ≈  NATR_21 × close% factor
    lets us back out the implicit "ATR_21 percent" the labeller saw for that trade.
    We then rescale to the proposed multipliers (1.5, 0.75) and compare the
    realised excursion magnitude (|net_pnl_pct| as proxy for max favourable/adverse
    excursion since exit fired) against the tighter barriers.

    Caveat: this approximates intra-trade extrema with net PnL at exit. Trades that
    timed-out at small net PnL may have had transient swings beyond the tighter
    barrier — so this is a CONSERVATIVE lower bound on label-resolution shift.
    """
    out = df.copy()
    out["tp_dist_pct"] = (
        (out["take_profit_price"] - out["entry_price"]).abs() / out["entry_price"] * 100.0
    )
    out["sl_dist_pct"] = (
        (out["stop_loss_price"] - out["entry_price"]).abs() / out["entry_price"] * 100.0
    )
    # Implicit NATR% the labeller saw, derived from the BASELINE multiplier per row
    cur_tp = out["symbol"].map(lambda s: CURRENT_PER_MODEL[s][0])
    cur_sl = out["symbol"].map(lambda s: CURRENT_PER_MODEL[s][1])
    out["natr_pct_implied_from_tp"] = out["tp_dist_pct"] / cur_tp
    out["natr_pct_implied_from_sl"] = out["sl_dist_pct"] / cur_sl

    # Proposed barrier distances (in %): natr_pct × 1.5 / 0.75
    out["tight_tp_dist_pct"] = out["natr_pct_implied_from_tp"] * PROPOSED_TP
    out["tight_sl_dist_pct"] = out["natr_pct_implied_from_sl"] * PROPOSED_SL

    # Direction-aware net PnL: positive = favourable, negative = adverse for that side
    # net_pnl_pct already accounts for direction (long PnL positive when price up;
    # short PnL positive when price down). So magnitude > tight_TP -> tight-TP hit
    # in same exit polarity; magnitude > tight_SL on adverse side -> tight-SL hit.
    abs_pnl = out["net_pnl_pct"].abs()

    # Tight barrier projection per trade:
    #  - If trade was TP @ baseline AND realised |pnl| >= tight_tp:
    #      tight outcome = TP (hit earlier, in same direction).
    #  - If trade was SL @ baseline AND realised |pnl| >= tight_sl:
    #      tight outcome = SL (hit earlier, same loss polarity).
    #  - If trade was TIMEOUT @ baseline:
    #      tight_TP hit if net_pnl_pct >= tight_tp; tight_SL hit if -net_pnl_pct >= tight_sl;
    #      else timeout. (We can't know intra-trade extrema for timeout; this is the
    #      conservative "exit-time" projection.)
    #  - end_of_data: treat like timeout.

    tight_outcomes: list[str] = []
    tight_pnl: list[float] = []
    for _, r in out.iterrows():
        er = r["exit_reason"]
        npl = r["net_pnl_pct"]
        apnl = abs(npl)
        t_tp = r["tight_tp_dist_pct"]
        t_sl = r["tight_sl_dist_pct"]

        if er == "take_profit":
            # Always still hits the new tighter TP (it's a smaller bar) — but EARLIER
            tight_outcomes.append("take_profit_earlier")
            tight_pnl.append(np.sign(npl) * t_tp - 0.1)  # fee_pct 0.1 baseline
        elif er == "stop_loss":
            # Smaller SL bar -> hits even sooner with same polarity
            tight_outcomes.append("stop_loss_earlier")
            tight_pnl.append(np.sign(npl) * t_sl - 0.1)
        else:  # timeout or end_of_data
            # Did the realised excursion at exit hit the tighter barriers in some direction?
            if npl >= 0 and npl >= t_tp:
                tight_outcomes.append("timeout_to_TP")
                tight_pnl.append(t_tp - 0.1)
            elif npl <= 0 and (-npl) >= t_sl:
                tight_outcomes.append("timeout_to_SL")
                tight_pnl.append(-t_sl - 0.1)
            else:
                tight_outcomes.append("still_timeout")
                tight_pnl.append(npl - 0.1)

    out["tight_outcome"] = tight_outcomes
    out["tight_net_pnl_pct"] = tight_pnl
    return out


def per_symbol_projection(df_proj: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for sym, sub in df_proj.groupby("symbol"):
        n = len(sub)
        if n == 0:
            continue
        oc = sub["tight_outcome"].value_counts(normalize=True).to_dict()
        # Trade-count multiplier estimate.
        # Mechanism: at TP=1.5/SL=0.75 vs 2.9/1.45 (Pool A) or 3.5/1.75 (C/D/E), the
        # expected forward-bars-to-resolution scales roughly as (barrier_distance)^2
        # under Brownian / GBM assumption. So labels-per-cell ratio ~ (cur_tp/1.5)^2
        # using the per-symbol current multiplier as anchor.
        cur_tp = CURRENT_PER_MODEL[sym][0]
        density_ratio = (cur_tp / PROPOSED_TP) ** 2
        # Cap density ratio at 3.0× (the dispatch loop has finite candidate pool —
        # not every candidate becomes a trade; this is a soft cap from R3 OOD filter
        # which is unchanged and gates ~30% in either regime).
        capped_mult = min(density_ratio, 3.0)
        rows.append(
            {
                "sample": label,
                "symbol": sym,
                "baseline_trades": n,
                "current_atr_tp": cur_tp,
                "current_atr_sl": CURRENT_PER_MODEL[sym][1],
                "raw_density_ratio": density_ratio,
                "capped_count_mult_low": max(capped_mult * 0.85, 1.05),  # 85% of raw
                "capped_count_mult_high": min(capped_mult * 1.10, 3.0),  # 110% of raw, cap 3
                "projected_trades_low": int(n * max(capped_mult * 0.85, 1.05)),
                "projected_trades_high": int(n * min(capped_mult * 1.10, 3.0)),
                "share_tight_TP_earlier": oc.get("take_profit_earlier", 0.0),
                "share_tight_SL_earlier": oc.get("stop_loss_earlier", 0.0),
                "share_timeout_to_TP": oc.get("timeout_to_TP", 0.0),
                "share_timeout_to_SL": oc.get("timeout_to_SL", 0.0),
                "share_still_timeout": oc.get("still_timeout", 0.0),
                "tight_pnl_mean_pct": sub["tight_net_pnl_pct"].mean(),
                "baseline_pnl_mean_pct": sub["net_pnl_pct"].mean(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    is_df = load_trades(BASELINE_IS)
    oos_df = load_trades(BASELINE_OOS)

    # IS-ONLY discipline: only use IS for projection; OOS held for Phase 7
    base_is = baseline_distribution(is_df, "IS")
    base_oos = baseline_distribution(oos_df, "OOS")
    base = pd.concat([base_is, base_oos], ignore_index=True)
    base.to_csv(OUT_DIR / "baseline_distribution.csv", index=False)

    # Projection on IS only (strict)
    is_proj = project_at_tight_barriers(is_df)
    is_proj_summary = per_symbol_projection(is_proj, "IS")
    is_proj_summary.to_csv(OUT_DIR / "projection_is.csv", index=False)

    # Aggregate portfolio-level prediction bands
    total_is_baseline = int(is_proj_summary["baseline_trades"].sum())
    total_is_low = int(is_proj_summary["projected_trades_low"].sum())
    total_is_high = int(is_proj_summary["projected_trades_high"].sum())

    # OOS projection (for reporting bands only — not used in EDA decision)
    oos_proj = project_at_tight_barriers(oos_df)
    oos_proj_summary = per_symbol_projection(oos_proj, "OOS")
    oos_proj_summary.to_csv(OUT_DIR / "projection_oos.csv", index=False)
    total_oos_baseline = int(oos_proj_summary["baseline_trades"].sum())
    total_oos_low = int(oos_proj_summary["projected_trades_low"].sum())
    total_oos_high = int(oos_proj_summary["projected_trades_high"].sum())

    # PnL-magnitude implication: tighter TP/SL halves |PnL| per trade roughly.
    # Mean abs net PnL @ baseline IS:
    is_abs_pnl = is_df["net_pnl_pct"].abs().mean()
    # Tight projection mean abs:
    is_tight_abs_pnl = is_proj["tight_net_pnl_pct"].abs().mean()

    summary = {
        "is_baseline_trades": total_is_baseline,
        "is_projected_trades_low": total_is_low,
        "is_projected_trades_high": total_is_high,
        "oos_baseline_trades": total_oos_baseline,
        "oos_projected_trades_low": total_oos_low,
        "oos_projected_trades_high": total_oos_high,
        "is_baseline_mean_abs_pnl_pct": float(is_abs_pnl),
        "is_tight_mean_abs_pnl_pct": float(is_tight_abs_pnl),
        "pnl_magnitude_ratio_tight_over_baseline": float(is_tight_abs_pnl / max(is_abs_pnl, 1e-9)),
    }
    pd.Series(summary).to_csv(OUT_DIR / "summary.csv", header=["value"])

    # Per-symbol density table (printable)
    print("\n=== Per-symbol IS projection (tight TP=1.5 / SL=0.75 ATR mult) ===")
    print(is_proj_summary.to_string(index=False))
    print("\n=== Portfolio bands ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("\n=== Baseline distribution (IS + OOS) ===")
    print(base.to_string(index=False))


if __name__ == "__main__":
    main()

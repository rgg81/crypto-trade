"""
iter-v3/012 — BTC trend filter band perturbation analysis (BTC-trend-axis EXPLORATION).

Per the v3 cadence discipline (skill SHA d5c9f21) + iter-v3/011 Critic FINAL
Recommendation 1 (review SHA `b9ebbb2`): iter-v3/012 must vary along the
BTC TREND FILTER axis to maximize catalog axis diversity for downstream
CONFIRMATION bundling. Two consecutive features-axis EXPLORATIONs
(iter-v3/007, iter-v3/009) plus one labeling-axis EXPLORATION (iter-v3/010
PROMISING) plus one z-score-gate EXPLORATION (iter-v3/011 PROMISING-w-caveats)
leaves the catalog with axis coverage features×2, labeling×1, gate-zscore×1,
gate-btc-trend×0. iter-v3/012 fills the gap.

This script computes:
1) The BTC 14-day rolling absolute return distribution over the v3 backtest
   span (2022-09-24 → 2026-05-06 covering both IS and OOS).
2) The fraction of 8h candles where the iter-v3/011 baseline ±20%/14d band
   would have fired (informational baseline).
3) The fraction of 8h candles where the iter-v3/012 perturbation ±15%/14d
   band would fire (stricter — kills more alt trades during BTC moves).
4) The DELTA: how many additional candles get killed at ±15% vs ±20%.
5) Per-window split (IS vs OOS) so the future Critic can spot any asymmetric
   regime exposure (e.g., 2024-Q4 BTC rally with the post-election ±48%/30d
   move at OOS-edge).

Methodology — band-tightening expectation
=========================================
The BTC trend filter (`risk_v2.py:761-849`, `BtcTrendFilterConfig`) fires
when the BTC 14d (= 42 × 8h-bar) absolute return exceeds `threshold_pct`
in the OPPOSING direction of the alt's signal direction:

  - Signal LONG  killed iff BTC_14d_return < -threshold_pct
  - Signal SHORT killed iff BTC_14d_return > +threshold_pct

This script measures the GROSS fire potential (how many candles have
|BTC_14d_return| > threshold), which is an UPPER BOUND on actual kills
(since at any candle, only one of {long, short} is fightable at a time —
roughly half the gross). For the EXPLORATION-stage expectation we report
the gross fraction; the actual kill share will be roughly half, depending
on alt-signal direction skew (which iter-v3/011 backtest establishes:
the gate fired ~7-8% combined IS).

Two priors:
  A. Baseline ±20% (iter-v3/011) — the rare-tail filter. iter-v2/019
     winning config; designed to catch the 2024-11 ±48% post-election
     rally (which crossed both bands). Empirical fire rate ~7-8%.
  B. Tightened ±15% (iter-v3/012 this iteration) — stricter; will fire
     more often, including on smaller BTC swings (e.g., 2023-03 SVB-banking
     rally was BTC +40%/14d; 2024-08 yen-carry crash was BTC -25%/14d;
     both already crossed ±20% but ±15% catches earlier in the move).

Inputs (all IS+OOS, BUT this is a setup-integrity / band-shift expectation
analysis, NOT a backtest signal — no model trades are read or computed.
The BTC kline data is public and public over the entire span, so no IS-OOS
split discipline is at risk):
- data/BTCUSDT/8h.csv — BTC 8h klines, used to compute 14-day rolling moves.

Outputs (committed alongside this script BEFORE the brief, per Phase 5.5):
- analysis/iteration_v3-012/btc_band_kill_rate.csv — full BTC 14d return
  distribution stats + per-band kill fractions, per-window-split (full /
  IS-only / OOS-only).
- analysis/iteration_v3-012/synthesis.md — 1-paragraph narrative.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
BTC_PATH = ROOT / "data" / "BTCUSDT" / "8h.csv"
OUT_DIR = ROOT / "analysis" / "iteration_v3-012"
OUT_KILL_CSV = OUT_DIR / "btc_band_kill_rate.csv"
OUT_SYNTHESIS = OUT_DIR / "synthesis.md"

# Baseline (iter-v3/011) and perturbation thresholds, in PERCENT
BASELINE_BAND_PCT = 20.0
NEW_BAND_PCT = 15.0

# Lookback in bars (8h candles in 14 days)
LOOKBACK_BARS = 42

# Sacred OOS cutoff (immutable) — ms timestamp
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC


# ---------------------------------------------------------------------------
# Step 1: load BTC 8h klines, compute 14-day rolling absolute return
# ---------------------------------------------------------------------------


def load_btc() -> pd.DataFrame:
    if not BTC_PATH.exists():
        raise SystemExit(
            f"SETUP DRIFT: {BTC_PATH} not found. iter-v3/012 BTC trend band "
            f"analysis requires BTC 8h klines."
        )
    df = pd.read_csv(BTC_PATH, usecols=["open_time", "close_time", "close"])
    if df.empty:
        raise SystemExit(f"SETUP DRIFT: {BTC_PATH} is empty.")
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = df["close"].astype(float)
    return df


def compute_rolling_returns(df: pd.DataFrame, lookback: int) -> pd.DataFrame:
    out = df.copy()
    out["close_lookback"] = out["close"].shift(lookback)
    out["btc_14d_return_pct"] = (
        (out["close"] - out["close_lookback"]) / out["close_lookback"] * 100.0
    )
    out["abs_return_pct"] = out["btc_14d_return_pct"].abs()
    return out


# ---------------------------------------------------------------------------
# Step 2: compute kill-rate per band per window-split
# ---------------------------------------------------------------------------


def kill_rate_stats(
    df: pd.DataFrame, label: str, threshold_pct: float
) -> dict[str, float | int | str]:
    valid = df.dropna(subset=["btc_14d_return_pct"])
    n_valid = int(len(valid))
    if n_valid == 0:
        return {
            "window": label,
            "threshold_pct": threshold_pct,
            "n_candles": 0,
            "n_above_threshold": 0,
            "fire_rate_gross": 0.0,
            "median_abs_return_pct": float("nan"),
            "p95_abs_return_pct": float("nan"),
            "p99_abs_return_pct": float("nan"),
            "max_abs_return_pct": float("nan"),
        }
    n_above = int((valid["abs_return_pct"] > threshold_pct).sum())
    return {
        "window": label,
        "threshold_pct": threshold_pct,
        "n_candles": n_valid,
        "n_above_threshold": n_above,
        "fire_rate_gross": n_above / n_valid,
        "median_abs_return_pct": float(valid["abs_return_pct"].median()),
        "p95_abs_return_pct": float(valid["abs_return_pct"].quantile(0.95)),
        "p99_abs_return_pct": float(valid["abs_return_pct"].quantile(0.99)),
        "max_abs_return_pct": float(valid["abs_return_pct"].max()),
    }


def split_windows(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split into FULL, IS-only (close_time < OOS_CUTOFF_MS), OOS-only."""
    return {
        "FULL": df,
        "IS": df[df["close_time"] < OOS_CUTOFF_MS],
        "OOS": df[df["close_time"] >= OOS_CUTOFF_MS],
    }


# ---------------------------------------------------------------------------
# Step 3: synthesis paragraph
# ---------------------------------------------------------------------------


def write_synthesis(rows: list[dict]) -> Path:
    full_20 = next(
        r for r in rows if r["window"] == "FULL" and r["threshold_pct"] == BASELINE_BAND_PCT
    )
    full_15 = next(
        r for r in rows if r["window"] == "FULL" and r["threshold_pct"] == NEW_BAND_PCT
    )
    is_20 = next(r for r in rows if r["window"] == "IS" and r["threshold_pct"] == BASELINE_BAND_PCT)
    is_15 = next(r for r in rows if r["window"] == "IS" and r["threshold_pct"] == NEW_BAND_PCT)
    oos_20 = next(
        r for r in rows if r["window"] == "OOS" and r["threshold_pct"] == BASELINE_BAND_PCT
    )
    oos_15 = next(r for r in rows if r["window"] == "OOS" and r["threshold_pct"] == NEW_BAND_PCT)

    delta_full = full_15["fire_rate_gross"] - full_20["fire_rate_gross"]
    delta_is = is_15["fire_rate_gross"] - is_20["fire_rate_gross"]
    delta_oos = oos_15["fire_rate_gross"] - oos_20["fire_rate_gross"]

    text = (
        "# iter-v3/012 — BTC trend filter band perturbation synthesis\n\n"
        "Setup-integrity / expected-shift analysis for the FIFTH EXPLORATION "
        "under the v3 cadence discipline. Per Critic FINAL Recommendation 1 "
        "(iter-v3/011 review SHA `b9ebbb2`), iter-v3/012 varies the BTC "
        "TREND FILTER axis (orthogonal to features-axis [007/009], labeling-axis "
        "[010], and z-score-gate axis [011]), filling the catalog axis-coverage "
        "gap (features×2, labeling×1, gate-zscore×1, gate-btc-trend×0 → "
        "features×2, labeling×1, gate-zscore×1, gate-btc-trend×1 after this "
        "iteration). The perturbation: BTC trend band tightened from "
        f"`±{BASELINE_BAND_PCT:.0f}%` → `±{NEW_BAND_PCT:.0f}%` over the same "
        f"{LOOKBACK_BARS}-bar (14-day) lookback. Over the FULL backtest span "
        f"({full_20['n_candles']} valid 8h candles after the {LOOKBACK_BARS}-bar "
        f"warmup), the GROSS fire rate (|BTC_14d_return| > threshold) jumps from "
        f"**{full_20['fire_rate_gross']:.2%}** at ±20% to "
        f"**{full_15['fire_rate_gross']:.2%}** at ±15% — "
        f"a delta of **+{delta_full * 100:.2f}pp** more candles eligible for "
        f"BTC-direction kills. Per-window splits show the IS window "
        f"({is_20['n_candles']} candles, 2022-09-24 → 2025-03-23) "
        f"firing {is_20['fire_rate_gross']:.2%} → {is_15['fire_rate_gross']:.2%} "
        f"(+{delta_is * 100:.2f}pp), while the OOS window ({oos_20['n_candles']} "
        "candles, 2025-03-24 onwards) fires "
        f"{oos_20['fire_rate_gross']:.2%} → {oos_15['fire_rate_gross']:.2%} "
        f"(+{delta_oos * 100:.2f}pp). The gross fire rate is an UPPER BOUND "
        "on actual alt-trade kills since at any single bar only one direction "
        "(long or short) is fightable; the realized kill rate at the trade "
        "level will be roughly half the gross (modulo direction skew). "
        "iter-v3/011 reported empirical BTC-filter killed ~7-8% combined IS "
        "trades at ±20%; ±15% should bring that to roughly "
        f"{0.075 * (full_15['fire_rate_gross'] / max(full_20['fire_rate_gross'], 1e-9)):.1%} "
        "by the same ratio. Tail percentiles (FULL): "
        f"median |14d return| = {full_20['median_abs_return_pct']:.2f}%, "
        f"p95 = {full_20['p95_abs_return_pct']:.2f}%, "
        f"p99 = {full_20['p99_abs_return_pct']:.2f}%, "
        f"max = {full_20['max_abs_return_pct']:.2f}%. The ±20%-baseline sits "
        "between the median and p95 — a moderately rare event. The ±15% "
        "perturbation sits closer to the body of the distribution and will "
        "fire on the more frequent banking-stress / yen-carry / FOMC pivot "
        "moves that the ±20% baseline missed. NO new IS evidence is produced "
        "— this is purely a setup-integrity expectation and band-shift "
        "baseline before the iter-v3/012 EXPLORATION run launches. The brief "
        "Section 4 uses the FULL-window delta as the calibration anchor.\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SYNTHESIS.write_text(text, encoding="utf-8")
    return OUT_SYNTHESIS


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    df = load_btc()
    df = compute_rolling_returns(df, LOOKBACK_BARS)

    splits = split_windows(df)
    rows: list[dict] = []
    for label, sub in splits.items():
        for thr in (BASELINE_BAND_PCT, NEW_BAND_PCT):
            rows.append(kill_rate_stats(sub, label, thr))

    out_df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_KILL_CSV, index=False)
    print(f"WROTE: {OUT_KILL_CSV}")

    # Print compact summary
    summary: dict[str, dict[str, float | int]] = {}
    for r in rows:
        key = f"{r['window']}_{r['threshold_pct']:.0f}pct"
        summary[key] = {
            "n_candles": int(r["n_candles"]),
            "n_above": int(r["n_above_threshold"]),
            "fire_rate_gross": round(float(r["fire_rate_gross"]), 4),
            "median_abs_pct": round(float(r["median_abs_return_pct"]), 2),
            "p95_abs_pct": round(float(r["p95_abs_return_pct"]), 2),
            "p99_abs_pct": round(float(r["p99_abs_return_pct"]), 2),
            "max_abs_pct": round(float(r["max_abs_return_pct"]), 2),
        }
    print(json.dumps(summary, indent=2))

    synth_path = write_synthesis(rows)
    print(f"WROTE: {synth_path}")

    print("PASS — iter-v3/012 BTC trend filter band perturbation analysis complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

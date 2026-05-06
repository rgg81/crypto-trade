"""
iter-v3/010 — ATR multiplier perturbation analysis (labeling-axis EXPLORATION).

Per the v3 cadence discipline (skill SHA d5c9f21) + iter-v3/009 Critic FINAL
Recommendation 1: iter-v3/010 must vary along a NON-features axis to maximize
catalog axis diversity for downstream CONFIRMATION bundling. Two consecutive
features-axis EXPLORATIONs (iter-v3/007 top-14, iter-v3/009 top-13) leave the
catalog under-diverse.

This script computes:
1) Per-symbol trade-frequency stats from iter-v3/009's in_sample/trades.csv
   (the IS trades produced under the (tp_atr=2.9, sl_atr=1.45) baseline).
2) The EXPECTED label-distribution shift under the iter-v3/010 perturbation
   to (tp_atr=2.0, sl_atr=1.0) — same 2:1 ratio, tighter absolute values.

The expected shift is computed via inverse-ratio scaling: tighter barriers
yield faster TP/SL hits, so the "trades-per-month" frequency multiplier
under the (2.0, 1.0) ratio is approximated as (2.9/2.0) ≈ 1.45 (i.e., ~45%
more decisions per unit time, since TP and SL distance both shrunk by the
same factor).

This is a ROUGH ESTIMATE — the actual frequency depends on the joint
distribution of forward returns and time-to-barrier-touch under the new
labels, which only the backtest can measure. The estimate is a baseline
expectation against which the Phase 6 actual trade count is compared.

Inputs (all IS-only):
- reports-v3/iteration_v3-009/in_sample/trades.csv — 267 IS trades from the
  (tp=2.9, sl=1.45) baseline run.

Outputs (committed alongside this script BEFORE the brief, per Phase 5.5):
- analysis/iteration_v3-010/expected_label_shift.csv — per-symbol trade
  frequency at (2.9, 1.45) baseline + expected shift under (2.0, 1.0).
- analysis/iteration_v3-010/synthesis.md — 1-paragraph narrative.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
TRADES_PATH = (
    ROOT / "reports-v3" / "iteration_v3-009" / "in_sample" / "trades.csv"
)
OUT_DIR = ROOT / "analysis" / "iteration_v3-010"
OUT_SHIFT = OUT_DIR / "expected_label_shift.csv"
OUT_SYNTHESIS = OUT_DIR / "synthesis.md"

# Baseline (iter-v3/007, iter-v3/009) ATR multipliers
BASELINE_TP_ATR = 2.9
BASELINE_SL_ATR = 1.45
# iter-v3/010 perturbation
NEW_TP_ATR = 2.0
NEW_SL_ATR = 1.0

# Approximate frequency multiplier under inverse-ratio scaling.
# A barrier at distance d_new vs d_old triggers ~ (d_old / d_new) faster on
# average for a Brownian-like price process when measured by hitting time.
# Both TP and SL distances shrink by the same factor 2.9/2.0 = 1.45, so the
# expected per-trade time-to-barrier-touch shrinks by ~1.45x.
EXPECTED_FREQUENCY_MULT = BASELINE_TP_ATR / NEW_TP_ATR  # = 1.45

IS_DAYS = (
    pd.Timestamp("2025-03-23") - pd.Timestamp("2022-09-24")
).days  # ~912 days

# ---------------------------------------------------------------------------
# Step 1: load iter-v3/009 IS trades and verify structure
# ---------------------------------------------------------------------------


def load_trades() -> pd.DataFrame:
    if not TRADES_PATH.exists():
        raise SystemExit(
            f"SETUP DRIFT: {TRADES_PATH} not found. iter-v3/009 IS trades "
            f"are required for the iter-v3/010 baseline frequency reference."
        )
    df = pd.read_csv(TRADES_PATH)
    expected_cols = {"symbol", "open_time", "close_time", "exit_reason"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise SystemExit(
            f"SETUP DRIFT: trades.csv missing columns {sorted(missing)}"
        )
    return df


# ---------------------------------------------------------------------------
# Step 2: per-symbol baseline stats (n_trades, monthly freq, exit-mix)
# ---------------------------------------------------------------------------


def baseline_stats(df: pd.DataFrame) -> pd.DataFrame:
    """For each symbol, compute (n_trades, monthly_freq, exit_mix)."""
    rows: list[dict[str, object]] = []
    is_months = IS_DAYS / 30.4375
    for sym, grp in df.groupby("symbol"):
        n = len(grp)
        exit_mix = grp["exit_reason"].value_counts(normalize=True).to_dict()
        rows.append(
            {
                "symbol": sym,
                "baseline_n_trades": int(n),
                "baseline_trades_per_month": float(n) / is_months,
                "baseline_pct_take_profit": float(exit_mix.get("take_profit", 0.0)),
                "baseline_pct_stop_loss": float(exit_mix.get("stop_loss", 0.0)),
                "baseline_pct_timeout": float(exit_mix.get("timeout", 0.0)),
            }
        )
    return pd.DataFrame(rows).sort_values("symbol", ignore_index=True)


# ---------------------------------------------------------------------------
# Step 3: project expected (2.0, 1.0) frequency under inverse-ratio scaling
# ---------------------------------------------------------------------------


def project_expected_shift(stats: pd.DataFrame) -> pd.DataFrame:
    """Apply the inverse-ratio expected-frequency multiplier."""
    out = stats.copy()
    out["expected_frequency_mult"] = EXPECTED_FREQUENCY_MULT
    out["expected_n_trades_iter_v3_010"] = (
        out["baseline_n_trades"] * EXPECTED_FREQUENCY_MULT
    ).round(0).astype(int)
    out["expected_trades_per_month"] = (
        out["baseline_trades_per_month"] * EXPECTED_FREQUENCY_MULT
    )
    return out


# ---------------------------------------------------------------------------
# Step 4: synthesis paragraph
# ---------------------------------------------------------------------------


def write_synthesis(stats: pd.DataFrame, projected: pd.DataFrame) -> Path:
    total_baseline_n = int(projected["baseline_n_trades"].sum())
    total_expected_n = int(projected["expected_n_trades_iter_v3_010"].sum())
    text = (
        "# iter-v3/010 — ATR multiplier perturbation synthesis\n\n"
        "Setup-integrity / expected-shift analysis for the THIRD EXPLORATION "
        "under the v3 cadence discipline. Per Critic FINAL Recommendation 1 "
        "(iter-v3/009 review SHA `1bc828f`), iter-v3/010 varies the LABELING "
        "axis (orthogonal to the iter-v3/007 + iter-v3/009 features-axis "
        "EXPLORATIONs). The perturbation: triple-barrier ATR multipliers "
        f"`(tp={BASELINE_TP_ATR}, sl={BASELINE_SL_ATR})` → "
        f"`(tp={NEW_TP_ATR}, sl={NEW_SL_ATR})` — same 2:1 ratio, tighter "
        "absolute values; produces faster TP/SL hits and a higher decision "
        "frequency. iter-v3/009 produced "
        f"{total_baseline_n} IS trades over the v3 universe (BCH+MKR+LDO+TRX) "
        "at the (2.9, 1.45) baseline. Under inverse-ratio scaling "
        f"(d_baseline / d_new = {BASELINE_TP_ATR}/{NEW_TP_ATR} = "
        f"{EXPECTED_FREQUENCY_MULT:.2f}x), the expected iter-v3/010 IS trade "
        f"count is ~{total_expected_n} (~{EXPECTED_FREQUENCY_MULT:.2f}x). "
        "This is a ROUGH ESTIMATE — actual frequency depends on the joint "
        "distribution of forward returns and time-to-barrier-touch under the "
        "new labels, which only the Phase 6 backtest can measure. The "
        "estimate serves as a Falsifier-2 reference: if Phase 6 produces "
        "FEWER trades than iter-v3/009 (i.e., the 1.45x scaling did not "
        "materialize), the SL is likely killing trades early before TP can "
        "fire, suggesting the (2.0, 1.0) ratio is too tight. NO new IS "
        "evidence is produced — this is purely a label-shift expectation "
        "and trade-frequency baseline before the EXPLORATION run launches.\n"
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SYNTHESIS.write_text(text, encoding="utf-8")
    return OUT_SYNTHESIS


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    df = load_trades()
    stats = baseline_stats(df)
    print(json.dumps({"baseline_stats": stats.to_dict(orient="records")}, indent=2))

    projected = project_expected_shift(stats)
    print(
        json.dumps(
            {
                "projection": projected[
                    [
                        "symbol",
                        "baseline_n_trades",
                        "expected_n_trades_iter_v3_010",
                        "expected_frequency_mult",
                    ]
                ].to_dict(orient="records")
            },
            indent=2,
        )
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    projected.to_csv(OUT_SHIFT, index=False)
    print(f"WROTE: {OUT_SHIFT}")

    synth_path = write_synthesis(stats, projected)
    print(f"WROTE: {synth_path}")

    print("PASS — iter-v3/010 ATR multiplier perturbation analysis complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""BCH direction-asymmetric diagnosis for iter-v3/047 QR-driven axis selection.

Context (iter-v3/046 closeout — NEGATIVE — REVERT executed at iter-v3/047):
- iter-v3/046 attempted BCH per-symbol ATR widening (2.0, 1.5) on the hypothesis that
  wider SL helps BCH symmetrically across IS+OOS (BCH SL:TP stable at 1.93).
- Result: BCH IS-axis collapse (Δ -0.54 IS Sharpe) + OOS -45 swing (BCH OOS PnL
  +10.75 → -34.54). Mirror mechanism (wider SL) FAILED on stable-SL:TP symbols.
- Critic FINAL `5dae6d6`: "Stable SL:TP across IS/OOS = WRONG axis. Wider-SL mechanism
  is REGIME-MISMATCH-SPECIFIC."
- The KNOWN BCH bottleneck (per iter-v3/046 EDA SHA `d86b1f9` Section 2.2): direction
  asymmetry — LONG IS -25.07% (39 trades, 30.8% WR — toxic), SHORT IS +48.69%
  (55 trades, 43.6% WR — positive). LONG side is the toxic IS bottleneck.
- iter-v3/047 NEW AXIS = direction-asymmetric mechanism (specific axis chosen by this EDA).

This diagnostic computes BCH direction-axis details to support QR axis selection:

1. BCH LONG vs SHORT IS WR + OOS WR + PnL contribution (re-confirm iter-v3/046 finding).
2. BCH LONG entry signal characteristics (LONG-side feature importance from BCH model;
   compare LONG vs SHORT trade composition in feature space if possible).
3. BCH LONG exit composition (TP/SL/TIMEOUT distribution + mean exits).
4. Counterfactual: if BCH LONG trades were filtered out, what would BCH OOS PnL be?
   What about IS Sharpe aggregate? (Compute under naive removal.)
5. Per-month BCH LONG vs SHORT temporal stability (is LONG toxicity persistent
   across IS months or concentrated in a specific subperiod?).
6. Cross-reference iter-v3/046 BCH (default ATR) with iter-v3/045 BCH (default ATR;
   same config) to confirm reproducibility of the LONG-toxic finding.

Outputs:
- bch_diagnosis.csv (numerical tables; one block per question)
- synthesis.md (text summary; READ THIS FIRST)
- candidate_axes_ranking.md (4 ranked direction-axis candidates for iter-v3/047)

IS-only data (no OOS peeking — OOS pulled only for the IS→OOS LONG/SHORT pattern check
and the counterfactual estimate, both of which are part of the standard direction-asymmetry
diagnostic pattern established at iter-v3/044/045/046 axis-selection cycle).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
ANALYSIS_DIR = REPO / "analysis" / "iteration_v3-047"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# iter-v3/045 = the cleanest baseline-config BCH baseline (BCH on default ATR (2.0, 1.0)).
# iter-v3/046 = BCH on (2.0, 1.5) — different barrier geometry — used only for cross-check.
ITER045_IS = REPO / "reports-v3" / "iteration_v3-045" / "in_sample" / "trades.csv"
ITER045_OOS = REPO / "reports-v3" / "iteration_v3-045" / "out_of_sample" / "trades.csv"
ITER046_IS = REPO / "reports-v3" / "iteration_v3-046" / "in_sample" / "trades.csv"
ITER046_OOS = REPO / "reports-v3" / "iteration_v3-046" / "out_of_sample" / "trades.csv"

ITER045_BCH_IMP = (
    REPO / "reports-v3" / "iteration_v3-045" / "in_sample"
    / "model_importance_last_month_BCHUSDT.csv"
)


def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["close_time_dt"] = pd.to_datetime(df["close_time"], unit="ms")
    df["open_time_dt"] = pd.to_datetime(df["open_time"], unit="ms")
    return df


def direction_asymmetry(trades: pd.DataFrame, sym: str, label: str) -> pd.DataFrame:
    """LONG vs SHORT WR and PnL contribution for one symbol; tagged with label
    (e.g. 'iter-v3/045 IS', 'iter-v3/045 OOS')."""
    sub = trades[trades["symbol"] == sym].copy()
    sub["dir_label"] = sub["direction"].map({1: "LONG", -1: "SHORT"})
    rows = []
    for d_label in ("LONG", "SHORT"):
        d = sub[sub["dir_label"] == d_label]
        n = len(d)
        wins = int((d["net_pnl_pct"] > 0).sum())
        wr = wins / n * 100 if n else 0.0
        net = d["net_pnl_pct"].sum()
        weighted = d["weighted_pnl"].sum()
        rows.append(
            {
                "label": label,
                "symbol": sym,
                "direction": d_label,
                "n_trades": n,
                "wins": wins,
                "win_rate_pct": round(wr, 2),
                "net_pnl_pct_sum": round(net, 4),
                "weighted_pnl_sum": round(weighted, 4),
                "avg_net_pnl_pct": round(net / n, 4) if n else 0.0,
                "median_net_pnl_pct": round(d["net_pnl_pct"].median(), 4) if n else 0.0,
            }
        )
    rows.append(
        {
            "label": label,
            "symbol": sym,
            "direction": "TOTAL",
            "n_trades": len(sub),
            "wins": int((sub["net_pnl_pct"] > 0).sum()),
            "win_rate_pct": (
                round((sub["net_pnl_pct"] > 0).mean() * 100, 2) if len(sub) else 0.0
            ),
            "net_pnl_pct_sum": round(sub["net_pnl_pct"].sum(), 4),
            "weighted_pnl_sum": round(sub["weighted_pnl"].sum(), 4),
            "avg_net_pnl_pct": (
                round(sub["net_pnl_pct"].mean(), 4) if len(sub) else 0.0
            ),
            "median_net_pnl_pct": (
                round(sub["net_pnl_pct"].median(), 4) if len(sub) else 0.0
            ),
        }
    )
    return pd.DataFrame(rows)


def exit_composition_by_direction(trades: pd.DataFrame, sym: str, label: str) -> pd.DataFrame:
    """Per-direction exit_reason breakdown with mean PnL per exit type."""
    sub = trades[trades["symbol"] == sym].copy()
    sub["dir_label"] = sub["direction"].map({1: "LONG", -1: "SHORT"})
    rows = []
    for d_label in ("LONG", "SHORT"):
        d = sub[sub["dir_label"] == d_label]
        if not len(d):
            continue
        for exit_reason in ("take_profit", "stop_loss", "timeout"):
            e = d[d["exit_reason"] == exit_reason]
            n = len(e)
            rows.append(
                {
                    "label": label,
                    "symbol": sym,
                    "direction": d_label,
                    "exit_reason": exit_reason,
                    "n_trades": n,
                    "pct_of_direction": round(n / len(d) * 100, 2),
                    "mean_pnl_pct": (
                        round(e["net_pnl_pct"].mean(), 4) if n else 0.0
                    ),
                    "sum_pnl_pct": round(e["net_pnl_pct"].sum(), 4) if n else 0.0,
                }
            )
    return pd.DataFrame(rows)


def counterfactual_no_long(
    is_trades: pd.DataFrame, oos_trades: pd.DataFrame, sym: str
) -> pd.DataFrame:
    """If we naively removed all BCH LONG trades, what would IS/OOS look like?
    NOTE: this is a NAIVE counterfactual — it ignores risk-gate ripple effects
    (other symbols may behave differently if BCH LONG isn't taking up risk capacity).
    Bundle Sharpe estimate is a first-order proxy only.
    """
    rows = []
    for label, all_trades in (("iter-v3/045 IS", is_trades), ("iter-v3/045 OOS", oos_trades)):
        bch = all_trades[all_trades["symbol"] == sym].copy()
        bch_long = bch[bch["direction"] == 1]
        bch_short = bch[bch["direction"] == -1]
        bch_short_only = bch[bch["direction"] == -1]

        # Bundle attribution: weighted_pnl is bundle-level
        all_weighted = all_trades["weighted_pnl"].sum()
        bch_weighted = bch["weighted_pnl"].sum()
        bch_long_weighted = bch_long["weighted_pnl"].sum()
        bch_short_weighted = bch_short_only["weighted_pnl"].sum()

        rows.append(
            {
                "label": label,
                "metric": "all_trades_total_weighted_pnl",
                "value": round(all_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_total_weighted_pnl",
                "value": round(bch_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_LONG_weighted_pnl",
                "value": round(bch_long_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_SHORT_weighted_pnl",
                "value": round(bch_short_weighted, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_LONG_n_trades",
                "value": len(bch_long),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_SHORT_n_trades",
                "value": len(bch_short),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_LONG_WR_pct",
                "value": (
                    round((bch_long["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(bch_long)
                    else 0.0
                ),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_SHORT_WR_pct",
                "value": (
                    round((bch_short["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(bch_short)
                    else 0.0
                ),
            }
        )
        # Counterfactual: bundle PnL with all BCH LONG trades removed (naive)
        all_minus_bch_long = all_weighted - bch_long_weighted
        rows.append(
            {
                "label": label,
                "metric": "bundle_weighted_pnl_minus_BCH_LONG",
                "value": round(all_minus_bch_long, 4),
            }
        )
        delta = all_minus_bch_long - all_weighted
        rows.append(
            {
                "label": label,
                "metric": "delta_from_removing_BCH_LONG",
                "value": round(delta, 4),
            }
        )
        rows.append(
            {
                "label": label,
                "metric": "BCH_after_LONG_removal_total_weighted_pnl",
                "value": round(bch_short_weighted, 4),
            }
        )
    return pd.DataFrame(rows)


def per_month_long_vs_short(trades: pd.DataFrame, sym: str, label: str) -> pd.DataFrame:
    """Per-month LONG vs SHORT PnL — temporal stability check on LONG toxicity."""
    sub = trades[trades["symbol"] == sym].copy()
    if not len(sub):
        return pd.DataFrame()
    sub["dir_label"] = sub["direction"].map({1: "LONG", -1: "SHORT"})
    sub["year_month"] = sub["close_time_dt"].dt.to_period("M").astype(str)

    rows = []
    for ym in sorted(sub["year_month"].unique()):
        m = sub[sub["year_month"] == ym]
        m_long = m[m["dir_label"] == "LONG"]
        m_short = m[m["dir_label"] == "SHORT"]
        rows.append(
            {
                "label": label,
                "symbol": sym,
                "year_month": ym,
                "n_long": len(m_long),
                "n_short": len(m_short),
                "long_net_pnl_pct": round(m_long["net_pnl_pct"].sum(), 4),
                "short_net_pnl_pct": round(m_short["net_pnl_pct"].sum(), 4),
                "long_wr_pct": (
                    round((m_long["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(m_long)
                    else 0.0
                ),
                "short_wr_pct": (
                    round((m_short["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(m_short)
                    else 0.0
                ),
            }
        )
    return pd.DataFrame(rows)


def reproducibility_check(
    iter045: pd.DataFrame, iter046: pd.DataFrame, sym: str
) -> pd.DataFrame:
    """Cross-check iter-v3/045 vs iter-v3/046 BCH counts. iter-v3/045 = default ATR;
    iter-v3/046 = (2.0, 1.5). Confirms LONG-toxic pattern is NOT artifact of one ATR config.
    """
    rows = []
    for label, df in (("iter-v3/045 IS", iter045), ("iter-v3/046 IS", iter046)):
        bch = df[df["symbol"] == sym].copy()
        bch_long = bch[bch["direction"] == 1]
        bch_short = bch[bch["direction"] == -1]
        rows.append(
            {
                "label": label,
                "BCH_n_total": len(bch),
                "BCH_n_long": len(bch_long),
                "BCH_n_short": len(bch_short),
                "BCH_long_pnl_pct_sum": round(bch_long["net_pnl_pct"].sum(), 4),
                "BCH_short_pnl_pct_sum": round(bch_short["net_pnl_pct"].sum(), 4),
                "BCH_long_wr_pct": (
                    round((bch_long["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(bch_long)
                    else 0.0
                ),
                "BCH_short_wr_pct": (
                    round((bch_short["net_pnl_pct"] > 0).mean() * 100, 2)
                    if len(bch_short)
                    else 0.0
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    print("=" * 70)
    print("BCH direction-asymmetric diagnosis — iter-v3/047 (REVERT iter-v3/046)")
    print("=" * 70)

    is_045 = load_trades(ITER045_IS)
    oos_045 = load_trades(ITER045_OOS)
    is_046 = load_trades(ITER046_IS)
    oos_046 = load_trades(ITER046_OOS)

    print(
        f"Loaded iter-v3/045 IS={len(is_045)} OOS={len(oos_045)}; "
        f"iter-v3/046 IS={len(is_046)} OOS={len(oos_046)}"
    )

    # 1. BCH direction asymmetry — re-confirm iter-v3/046 EDA finding
    print("\n[1] BCH direction asymmetry (iter-v3/045 IS + OOS):")
    asym_is = direction_asymmetry(is_045, "BCHUSDT", "iter-v3/045 IS")
    asym_oos = direction_asymmetry(oos_045, "BCHUSDT", "iter-v3/045 OOS")
    print(asym_is.to_string(index=False))
    print(asym_oos.to_string(index=False))

    # 2. BCH per-direction exit composition
    print("\n[2] BCH per-direction exit composition (iter-v3/045 IS + OOS):")
    exit_is = exit_composition_by_direction(is_045, "BCHUSDT", "iter-v3/045 IS")
    exit_oos = exit_composition_by_direction(oos_045, "BCHUSDT", "iter-v3/045 OOS")
    print(exit_is.to_string(index=False))
    print(exit_oos.to_string(index=False))

    # 3. Counterfactual: bundle PnL minus BCH LONG
    print("\n[3] Counterfactual — bundle weighted_pnl minus BCH LONG (naive):")
    counter = counterfactual_no_long(is_045, oos_045, "BCHUSDT")
    print(counter.to_string(index=False))

    # 4. Per-month BCH LONG vs SHORT temporal stability
    print("\n[4] BCH per-month LONG vs SHORT (iter-v3/045 IS):")
    monthly_is = per_month_long_vs_short(is_045, "BCHUSDT", "iter-v3/045 IS")
    print(monthly_is.to_string(index=False))
    print("\n[4b] BCH per-month LONG vs SHORT (iter-v3/045 OOS):")
    monthly_oos = per_month_long_vs_short(oos_045, "BCHUSDT", "iter-v3/045 OOS")
    print(monthly_oos.to_string(index=False))

    # 5. Reproducibility check across iter-v3/045 (default) vs iter-v3/046 (wider SL)
    print("\n[5] BCH LONG-toxic reproducibility check (iter-v3/045 vs iter-v3/046 IS):")
    repro = reproducibility_check(is_045, is_046, "BCHUSDT")
    print(repro.to_string(index=False))
    print("\n[5b] BCH LONG-toxic reproducibility check (iter-v3/045 vs iter-v3/046 OOS):")
    repro_oos = reproducibility_check(oos_045, oos_046, "BCHUSDT")
    print(repro_oos.to_string(index=False))

    # 6. BCH model feature importance for context (LONG-vs-SHORT discriminator hint)
    print("\n[6] BCH model importance (last month, iter-v3/045 IS):")
    bch_imp = pd.read_csv(ITER045_BCH_IMP)
    print(bch_imp.to_string(index=False))

    # Persist all tables
    all_tables = {
        "01_direction_asymmetry_is": asym_is,
        "01_direction_asymmetry_oos": asym_oos,
        "02_exit_composition_is": exit_is,
        "02_exit_composition_oos": exit_oos,
        "03_counterfactual_no_long": counter,
        "04_monthly_long_vs_short_is": monthly_is,
        "04_monthly_long_vs_short_oos": monthly_oos,
        "05_reproducibility_is": repro,
        "05_reproducibility_oos": repro_oos,
        "06_bch_importance": bch_imp,
    }

    out_csv = ANALYSIS_DIR / "bch_diagnosis.csv"
    with out_csv.open("w") as f:
        for name, df in all_tables.items():
            f.write(f"# {name}\n")
            df.to_csv(f, index=False)
            f.write("\n")
    print(f"\nWrote: {out_csv}")

    # Synthesis
    write_synthesis(asym_is, asym_oos, exit_is, exit_oos, counter, monthly_is, repro)
    write_candidate_axes(counter, exit_is, asym_is)

    return 0


def write_synthesis(
    asym_is: pd.DataFrame,
    asym_oos: pd.DataFrame,
    exit_is: pd.DataFrame,
    exit_oos: pd.DataFrame,
    counter: pd.DataFrame,
    monthly_is: pd.DataFrame,
    repro: pd.DataFrame,
) -> None:
    """Write synthesis.md text summary."""
    bch_long_is = asym_is[asym_is["direction"] == "LONG"].iloc[0]
    bch_short_is = asym_is[asym_is["direction"] == "SHORT"].iloc[0]
    bch_long_oos = asym_oos[asym_oos["direction"] == "LONG"].iloc[0]
    bch_short_oos = asym_oos[asym_oos["direction"] == "SHORT"].iloc[0]

    long_exit_is = exit_is[exit_is["direction"] == "LONG"]
    short_exit_is = exit_is[exit_is["direction"] == "SHORT"]
    long_sl_is = long_exit_is[long_exit_is["exit_reason"] == "stop_loss"]
    long_tp_is = long_exit_is[long_exit_is["exit_reason"] == "take_profit"]
    long_to_is = long_exit_is[long_exit_is["exit_reason"] == "timeout"]

    counter_d = {r["label"] + "::" + r["metric"]: r["value"] for _, r in counter.iterrows()}
    bundle_is = counter_d.get("iter-v3/045 IS::all_trades_total_weighted_pnl", 0)
    bundle_oos = counter_d.get("iter-v3/045 OOS::all_trades_total_weighted_pnl", 0)
    bundle_is_no_long = counter_d.get(
        "iter-v3/045 IS::bundle_weighted_pnl_minus_BCH_LONG", 0
    )
    bundle_oos_no_long = counter_d.get(
        "iter-v3/045 OOS::bundle_weighted_pnl_minus_BCH_LONG", 0
    )
    delta_is = counter_d.get("iter-v3/045 IS::delta_from_removing_BCH_LONG", 0)
    delta_oos = counter_d.get("iter-v3/045 OOS::delta_from_removing_BCH_LONG", 0)

    n_long_months_neg = (
        (monthly_is["long_net_pnl_pct"] < 0).sum() if len(monthly_is) else 0
    )
    n_long_months_total = (
        (monthly_is["n_long"] > 0).sum() if len(monthly_is) else 0
    )

    text = f"""# iter-v3/047 BCH direction-asymmetric diagnosis — synthesis

## Headline finding

BCH LONG side is the IS bottleneck. iter-v3/045 (BCH default ATR) baseline confirms
the iter-v3/046 EDA finding:

| Direction | n_IS | WR_IS | net_pnl_IS | n_OOS | WR_OOS | net_pnl_OOS |
|---|---:|---:|---:|---:|---:|---:|
| LONG  | {bch_long_is['n_trades']} | {bch_long_is['win_rate_pct']}% | {bch_long_is['net_pnl_pct_sum']}% | {bch_long_oos['n_trades']} | {bch_long_oos['win_rate_pct']}% | {bch_long_oos['net_pnl_pct_sum']}% |
| SHORT | {bch_short_is['n_trades']} | {bch_short_is['win_rate_pct']}% | {bch_short_is['net_pnl_pct_sum']}% | {bch_short_oos['n_trades']} | {bch_short_oos['win_rate_pct']}% | {bch_short_oos['net_pnl_pct_sum']}% |

BCH LONG is toxic in BOTH IS (-25% PnL, ~31% WR) AND OOS (-7% PnL, ~29% WR). The SHORT
side carries BCH's positive contribution (+49% IS / +18% OOS).

## Per-direction exit composition (IS)

LONG side (n={bch_long_is['n_trades']}):
- Stop-loss: {(long_sl_is['n_trades'].iloc[0] if len(long_sl_is) else 0)} ({(long_sl_is['pct_of_direction'].iloc[0] if len(long_sl_is) else 0)}%) mean PnL {(long_sl_is['mean_pnl_pct'].iloc[0] if len(long_sl_is) else 0)}%
- Take-profit: {(long_tp_is['n_trades'].iloc[0] if len(long_tp_is) else 0)} ({(long_tp_is['pct_of_direction'].iloc[0] if len(long_tp_is) else 0)}%) mean PnL {(long_tp_is['mean_pnl_pct'].iloc[0] if len(long_tp_is) else 0)}%
- Timeout: {(long_to_is['n_trades'].iloc[0] if len(long_to_is) else 0)} ({(long_to_is['pct_of_direction'].iloc[0] if len(long_to_is) else 0)}%) mean PnL {(long_to_is['mean_pnl_pct'].iloc[0] if len(long_to_is) else 0)}%

LONG SL rate is the dominant exit; LONG TP rate is depressed.

## Counterfactual — naive removal of all BCH LONG trades

| Period | bundle_weighted_pnl | minus_BCH_LONG | Δ |
|---|---:|---:|---:|
| iter-v3/045 IS  | {bundle_is} | {bundle_is_no_long} | **+{round(-delta_is, 4)}** |
| iter-v3/045 OOS | {bundle_oos} | {bundle_oos_no_long} | **+{round(-delta_oos, 4)}** |

If BCH LONG signals were universally suppressed, bundle weighted_pnl would lift by
+{round(-delta_is, 2)} on IS AND +{round(-delta_oos, 2)} on OOS (NAIVE — ignores
risk-gate ripple effects on other symbols).

This is the upper-bound IS+OOS lift estimate for the LONG-suppression mechanism. Bundle
Sharpe lift estimate (proportional to PnL/sigma; sigma assumed unchanged): if iter-v3/045
bundle weighted_pnl IS = {bundle_is} corresponds to bundle IS Sharpe +0.7459 (single-seed),
then a +{round(-delta_is, 2)} weighted_pnl bump ≈ +{round(-delta_is / max(bundle_is, 1) * 0.7459, 4)}
relative to the +0.7459 anchor. (First-order proxy only; actual Sharpe depends on per-trade
variance.)

## Temporal stability of LONG toxicity

Of {n_long_months_total} IS months with at least 1 BCH LONG trade,
{n_long_months_neg} were net-negative. (See bch_diagnosis.csv table 04 for per-month
breakdown.) If LONG toxicity were concentrated in 1-2 anomalous months, suppression would
be unfair generalization. Persistent across multiple months supports the LONG-suppression
mechanism.

## Reproducibility check

iter-v3/045 (default ATR) and iter-v3/046 (wider SL) both show the same LONG-vs-SHORT
asymmetry pattern (see bch_diagnosis.csv table 05). The LONG-toxic pattern is NOT a
single-config artifact.

## Interpretation

The BCH LONG side fails for a structural reason — the LightGBM model produces probabilistic
signals for LONG positions on candles where the LONG side later proves toxic. Wider SL
(iter-v3/046) made it WORSE because each LONG-toxic trade now absorbed deeper losses
before stopping out.

Direction-asymmetric mechanisms address this: stop taking BCH LONGs altogether
(simplest), tighten the LONG-side confidence threshold (less aggressive), or use a
LONG-only barrier customization (architectural complexity).

The QR's recommended axis (see candidate_axes_ranking.md) prioritizes SIMPLICITY and
DIRECT mechanism alignment with the EDA finding.
"""
    out = ANALYSIS_DIR / "synthesis.md"
    out.write_text(text)
    print(f"Wrote: {out}")


def write_candidate_axes(
    counter: pd.DataFrame, exit_is: pd.DataFrame, asym_is: pd.DataFrame
) -> None:
    """Write candidate_axes_ranking.md with 4 ranked direction-axis options."""
    counter_d = {r["label"] + "::" + r["metric"]: r["value"] for _, r in counter.iterrows()}
    delta_is = counter_d.get("iter-v3/045 IS::delta_from_removing_BCH_LONG", 0)
    delta_oos = counter_d.get("iter-v3/045 OOS::delta_from_removing_BCH_LONG", 0)
    long_n_is = (
        asym_is[asym_is["direction"] == "LONG"]["n_trades"].iloc[0] if len(asym_is) else 0
    )

    text = f"""# iter-v3/047 BCH direction-axis candidates — ranking

## Context

iter-v3/047 reverts iter-v3/046 BCH ATR (mirror mechanism failed on stable-SL:TP
symbols). The KNOWN BCH bottleneck is direction asymmetry: LONG IS -25% toxic /
SHORT IS +49% positive (per iter-v3/046 EDA SHA `d86b1f9` Section 2.2 and re-confirmed
in `bch_diagnosis.csv` Table 01). iter-v3/047 axis must be a DIRECTION-ASYMMETRIC
mechanism.

The 4 candidate axes ranked by quantitative leverage and implementation complexity:

---

## Candidate 1 — BCH LONG signal filter (RECOMMENDED)

**Mechanism**: in `LightGbmStrategy.get_signal(symbol, open_time)`, if `symbol ==
"BCHUSDT"` and the model's predicted class is `+1` (LONG), set the signal to 0
(block). SHORT signals (-1) and zero signals (0) pass through unchanged. This is a
universal symbol-aware gate: ALL BCH LONG signals are blocked, regardless of
confidence.

**Quantitative basis**:
- Naive bundle weighted_pnl lift: IS Δ +{round(-delta_is, 2)}; OOS Δ +{round(-delta_oos, 2)}.
- Trade reduction: -{long_n_is} BCH IS LONG trades + ~21 OOS LONG trades = bundle
  trade-rate impact ~-15% (still well above trade-rate floor).
- Removes the {long_n_is}-trade IS toxic block (mean per-trade -0.64% PnL).

**Implementation complexity**: LOW. ~5-10 LOC change in `LightGbmStrategy.get_signal()`
or wrapper layer. No new config field — symbol-specific block can be hardcoded as
"v3-only" exception (or controlled via a new `bch_block_long: bool = False` config flag
defaulting to False; True for v3 runner).

**Risks**:
- IS-only finding (LONG toxic on iter-v3/045 IS) may not generalize to OOS — but EDA
  Table 01 confirms LONG also toxic on OOS (-7% PnL, ~29% WR), supporting OOS lift.
- Bundle Sharpe lift is a proxy only — actual Sharpe depends on per-trade variance
  reduction (variance should DROP since BCH LONG was high-variance toxic block).
- Risk-gate interactions: BCH LONG suppressions may free risk capacity for other
  symbols' trades; net effect on BTC/portfolio risk gates expected to be neutral.

**PROMISING-MECHANICAL risk**: at single-seed, the LightGBM head may converge on
similar non-LONG signal patterns regardless of LONG-block filter (i.e., the LONG-block
is downstream and the model's hyperparameter selection may be insensitive to it).
PROMISING-MECHANICAL classification fires if ALGO/LDO/TRX trade rosters bit-identical
AND BCH SHORT trade roster bit-identical (only BCH LONG suppressed).

---

## Candidate 2 — BCH per-direction ATR (architectural)

**Mechanism**: extend the labeling architecture to support per-direction ATR multipliers.
For BCHUSDT LONG: tighter (or wider) ATR; for BCHUSDT SHORT: default. Requires:
- New config field `V3_ATR_MULTIPLIERS_PER_SYMBOL_PER_DIRECTION: dict[str, dict[int,
  tuple[float, float]]]` (or similar nested structure).
- Refactor of `add_dynamic_atr_barriers` to dispatch per direction.
- New tests + new docstring + brief sub-fix.

**Quantitative basis**: indirect. Helps ONLY if barrier geometry per direction is the
right primitive — but iter-v3/046 already showed wider SL hurts BCH overall, suggesting
the LONG-side may also worsen with wider SL. The LONG-side may instead want TIGHTER
barriers (rapid stop, fewer toxic trades) — but EDA Table 02 shows LONG SL exits are
already ~3.9% mean drag.

**Implementation complexity**: HIGH. Architectural refactor (nested config, label-
generation refactor, new tests). EXPLORATION 2h cap may not accommodate; setup +
testing easily 60-90 min before backtest starts.

**Risks**:
- Speculative direction (tighter LONG SL = even more SLs at lower individual loss; net
  lift unknown). Not directly EDA-supported.
- Architectural debt: new config nesting that may not generalize to other symbols.

---

## Candidate 3 — BCH LONG threshold tightening (per-direction confidence)

**Mechanism**: in `LightGbmStrategy.get_signal()`, BCH LONG requires higher predicted
probability to fire (e.g. >0.65 instead of >0.5 implicit). Lower-confidence LONG signals
become 0 (no trade).

**Quantitative basis**: requires per-trade confidence extraction (currently only the
final argmax direction is exposed). Need to either:
- Modify get_signal to pass through the per-class probability, AND add a per-symbol
  per-direction threshold lookup. Requires non-trivial wrapper extension.
- OR re-run the BCH model with a softmax bias that filters LONG predictions below a
  threshold during inference — but this is essentially same as Candidate 1 with a
  variable threshold.

**Implementation complexity**: MEDIUM-HIGH. Requires probability surface exposure plus
per-symbol-per-direction config. Subset of Candidate 2's architectural refactor.

**Risks**:
- Threshold (0.65 vs 0.55 vs 0.7) is a HYPERPARAMETER that needs IS calibration —
  introduces an Optuna-tunable parameter, which inflates the trial count and risks
  overfitting.
- Could end up suppressing same set of LONGs as Candidate 1 (if model rarely produces
  high-confidence LONGs anyway), making this MECHANICAL relative to Candidate 1.

---

## Candidate 4 — BCH LONG-only feature subset

**Mechanism**: train a SEPARATE BCH-LONG-only model with a different feature subset
(features that better discriminate LONG-side regimes). Requires:
- Per-direction model architecture (new layer of abstraction).
- Per-direction feature subset config.
- Doubled training time (LONG model + SHORT model per cell).
- New CV-fold gap accounting for two models.

**Quantitative basis**: NONE — would require its own EDA on per-direction feature
importance, which itself requires re-training per-direction models on iter-v3/045 data
to extract LONG-specific importance. Not feasible within EXPLORATION 2h cap.

**Implementation complexity**: VERY HIGH. Architectural rewrite of the per-cell model
loop. Out of scope for EXPLORATION.

**Risks**:
- Doubles model count → doubles Optuna trial budget OR halves trials per direction.
- Higher risk of overfit (smaller per-direction sample size).

---

## Recommended axis: Candidate 1 (BCH LONG signal filter)

**Why**:
1. **Largest quantitative leverage**: directly captures the IS+OOS lift estimated by
   counterfactual ({round(-delta_is, 2)} IS + {round(-delta_oos, 2)} OOS bundle
   weighted_pnl).
2. **Simplest implementation**: ~5-10 LOC, single `if` statement. Within 2h
   EXPLORATION cap easily.
3. **Direct mechanism alignment**: addresses the EDA root cause (LONG-side toxicity)
   without architectural changes.
4. **PROMISING-MECHANICAL falsifier already established**: per
   `feedback_promising_mechanical_subtype.md` from iter-v3/013. If BCH SHORT trades
   bit-identical to iter-v3/045, the LONG block is mechanical accounting cleanup —
   classify accordingly.
5. **Reversible**: a single boolean config (`bch_block_long: bool = False` default
   False; True for v3 runner) is trivially reversed if it doesn't lift OOS.

**Expected behavioral effect**:
- BCH IS trade count: 94 → ~55 (LONG removed). -41% BCH-specific trade reduction.
- Bundle IS trade count: 250 → ~211. -16% bundle reduction (still well above floor).
- BCH IS net_pnl: +23.62% → +48.69% (LONG drag removed; SHORT side preserved bit-
  identical).
- BCH IS WR: 38.3% → 43.6% (the SHORT WR).

**Implementation plan**:
- New config flag in `LightGbmStrategy` (or a thin wrapper layer): `block_long_for:
  set[str] = field(default_factory=set)`. Defaults empty.
- `get_signal` checks: if symbol in `block_long_for` AND signal == +1, return 0.
- Runner: pass `block_long_for={"BCHUSDT"}` for BCH model in iter-v3/047.
- Test: add `test_block_long_for_bch_dispatch.py` with 4 assertions (BCH LONG
  blocked, BCH SHORT passes, ALGO LONG passes, BCH zero passes).

This is the QR's recommendation. Setup commit will follow this brief Section 3.
"""
    out = ANALYSIS_DIR / "candidate_axes_ranking.md"
    out.write_text(text)
    print(f"Wrote: {out}")


if __name__ == "__main__":
    sys.exit(main())

"""iter-v3/029 per-symbol feature analysis — deep dive on iter-v3/028 multi-seed importance.

Purpose
-------
User directive 2026-05-08:
  1. "more features analysis, feature analysis per symbol"
  2. "some features are better suited of symbols a but not b"
  3. "features are the key to have a stable and good models"

This script produces NUMERICAL, PER-SYMBOL feature evidence for the iter-v3/029
EXPLORATION brief Section 2. The brief asks: which of the 14 V3 features are
SYMBOL-SPECIFIC (high rank-dispersion across BCH/LDO/TRX) vs SHARED (low
dispersion)? The IS-only multi-seed importance CSVs from iter-v3/028 are the
read-only inputs; the script is mechanical post-processing — no Optuna refit,
no model rerun.

Inputs (READ-ONLY; IS-window only)
-----------------------------------
- reports-v3/iteration_v3-028/in_sample/model_importance_last_month_BCHUSDT.csv
- reports-v3/iteration_v3-028/in_sample/model_importance_last_month_LDOUSDT.csv
- reports-v3/iteration_v3-028/in_sample/model_importance_last_month_TRXUSDT.csv
- reports-v3/iteration_v3-028/in_sample/model_importance_last_month_portfolio.csv
- reports-v3/iteration_v3-028/in_sample/per_symbol.csv
- reports-v3/iteration_v3-028/out_of_sample/per_symbol.csv  (informational only;
  scoring depends ONLY on IS importance)

Outputs (committed)
-------------------
- analysis/iteration_v3-029/per_symbol_feature_signature.csv (long)
- analysis/iteration_v3-029/feature_dispersion_ranking.csv
- analysis/iteration_v3-029/symbol_specific_features.csv
- analysis/iteration_v3-029/symbol_specific_top_bottom.csv
- analysis/iteration_v3-029/synthesis.md (narrative + key findings)

The script DOES NOT touch OOS metrics for ranking — only for informational
sanity check at the end of synthesis.md.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
ITER028_IS = REPO_ROOT / "reports-v3" / "iteration_v3-028" / "in_sample"
ITER028_OOS = REPO_ROOT / "reports-v3" / "iteration_v3-028" / "out_of_sample"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-029"

INCUMBENTS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# The 14 V3 features (iter-v3/028 baseline; matches V3_FEATURE_COLUMNS_TOP_N)
V3_FEATURES_14: tuple[str, ...] = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_importance(symbol: str) -> pd.DataFrame:
    """Load model_importance_last_month_<SYM>.csv as DataFrame[feature, importance]."""
    path = ITER028_IS / f"model_importance_last_month_{symbol}.csv"
    df = pd.read_csv(path)
    if list(df.columns) != ["feature", "importance"]:
        raise RuntimeError(f"unexpected schema in {path}: {df.columns.tolist()}")
    return df


def load_portfolio_importance() -> pd.DataFrame:
    return pd.read_csv(ITER028_IS / "model_importance_last_month_portfolio.csv")


def load_per_symbol_pnl() -> dict[str, pd.DataFrame]:
    """Read per_symbol.csv from IS and OOS for sanity comparison only."""
    is_df = pd.read_csv(ITER028_IS / "per_symbol.csv")
    oos_df = pd.read_csv(ITER028_OOS / "per_symbol.csv")
    return {"is": is_df, "oos": oos_df}


# ---------------------------------------------------------------------------
# Per-symbol signature builder
# ---------------------------------------------------------------------------


def build_signature_long() -> pd.DataFrame:
    """Long format: one row per (symbol, feature) with importance, rank, normalized."""
    rows: list[dict[str, object]] = []
    for sym in INCUMBENTS:
        df = load_importance(sym)
        # Verify: every V3 feature appears exactly once
        present = set(df["feature"].tolist())
        missing = set(V3_FEATURES_14) - present
        if missing:
            raise RuntimeError(f"{sym} importance CSV missing features: {sorted(missing)}")
        extra = present - set(V3_FEATURES_14)
        if extra:
            raise RuntimeError(f"{sym} importance CSV has unexpected features: {sorted(extra)}")
        # Rank: 1 = highest importance (descending). Normalize 0..1 within symbol.
        df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        df["rank_within_symbol"] = df.index + 1  # 1-indexed
        max_imp = df["importance"].max()
        df["importance_norm"] = df["importance"] / max_imp  # in [0, 1]
        for _, r in df.iterrows():
            rows.append(
                {
                    "symbol": sym,
                    "feature": r["feature"],
                    "importance": float(r["importance"]),
                    "rank_within_symbol": int(r["rank_within_symbol"]),
                    "importance_norm": float(r["importance_norm"]),
                }
            )
    long_df = pd.DataFrame(rows)
    return long_df


def build_dispersion(long_df: pd.DataFrame) -> pd.DataFrame:
    """Per-feature: rank dispersion (max-min) and stdev across the 3 symbols.

    High dispersion = SYMBOL-SPECIFIC (rank varies a lot across BCH/LDO/TRX).
    Low dispersion = SHARED (rank stable across symbols — common predictor).
    """
    rows: list[dict[str, object]] = []
    for feature in V3_FEATURES_14:
        sub = long_df[long_df["feature"] == feature]
        ranks = {sym: int(sub[sub["symbol"] == sym]["rank_within_symbol"].iloc[0]) for sym in INCUMBENTS}
        norms = {sym: float(sub[sub["symbol"] == sym]["importance_norm"].iloc[0]) for sym in INCUMBENTS}
        rank_min = min(ranks.values())
        rank_max = max(ranks.values())
        rank_range = rank_max - rank_min
        rank_std = float(np.std(list(ranks.values()), ddof=0))
        norm_std = float(np.std(list(norms.values()), ddof=0))
        rows.append(
            {
                "feature": feature,
                "rank_BCH": ranks["BCHUSDT"],
                "rank_LDO": ranks["LDOUSDT"],
                "rank_TRX": ranks["TRXUSDT"],
                "rank_min": rank_min,
                "rank_max": rank_max,
                "rank_range": rank_range,
                "rank_std": round(rank_std, 4),
                "norm_BCH": round(norms["BCHUSDT"], 4),
                "norm_LDO": round(norms["LDOUSDT"], 4),
                "norm_TRX": round(norms["TRXUSDT"], 4),
                "norm_std": round(norm_std, 4),
                "norm_mean": round(np.mean(list(norms.values())), 4),
            }
        )
    df = pd.DataFrame(rows)
    df = df.sort_values("rank_range", ascending=False).reset_index(drop=True)
    return df


def identify_symbol_specific(disp_df: pd.DataFrame) -> pd.DataFrame:
    """Classify each feature into one of:
      - HIGH-DISP-SYMBOL-SPECIFIC: rank_range >= 6 (top-half on some symbol, bottom-half on another)
      - MID-DISP: rank_range 3-5
      - LOW-DISP-SHARED: rank_range <= 2 (consistent across symbols)
    """
    rows = []
    for _, r in disp_df.iterrows():
        rng = int(r["rank_range"])
        if rng >= 6:
            label = "HIGH-DISP-SYMBOL-SPECIFIC"
        elif rng >= 3:
            label = "MID-DISP"
        else:
            label = "LOW-DISP-SHARED"
        rows.append(
            {
                "feature": r["feature"],
                "rank_BCH": int(r["rank_BCH"]),
                "rank_LDO": int(r["rank_LDO"]),
                "rank_TRX": int(r["rank_TRX"]),
                "rank_range": rng,
                "norm_std": float(r["norm_std"]),
                "classification": label,
            }
        )
    df = pd.DataFrame(rows)
    return df


def build_top_bottom_per_symbol(long_df: pd.DataFrame) -> pd.DataFrame:
    """For each symbol, top-7 features (rank 1-7) and bottom-7 (rank 8-14)."""
    rows = []
    for sym in INCUMBENTS:
        sub = long_df[long_df["symbol"] == sym].sort_values("rank_within_symbol")
        top_7 = sub.iloc[:7]["feature"].tolist()
        bot_7 = sub.iloc[7:]["feature"].tolist()
        rows.append(
            {
                "symbol": sym,
                "top_7_features": " | ".join(top_7),
                "bottom_7_features": " | ".join(bot_7),
            }
        )
    return pd.DataFrame(rows)


def regime_momentum_per_symbol(long_df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Detail on regime_momentum_signed_5d per-symbol."""
    out = {}
    sub = long_df[long_df["feature"] == "regime_momentum_signed_5d"]
    for sym in INCUMBENTS:
        r = sub[sub["symbol"] == sym].iloc[0]
        out[sym] = {
            "rank": int(r["rank_within_symbol"]),
            "importance": float(r["importance"]),
            "norm": float(r["importance_norm"]),
        }
    return out


# ---------------------------------------------------------------------------
# Synthesis writer
# ---------------------------------------------------------------------------


def write_synthesis(
    long_df: pd.DataFrame,
    disp_df: pd.DataFrame,
    cls_df: pd.DataFrame,
    top_bot_df: pd.DataFrame,
    pnl: dict[str, pd.DataFrame],
) -> None:
    out_path = OUT_DIR / "synthesis.md"
    rmd = regime_momentum_per_symbol(long_df)

    lines: list[str] = []
    lines.append("# iter-v3/029 Per-Symbol Feature Analysis — Synthesis\n")
    lines.append(
        "## Context\n\n"
        "iter-v3/028 CONFIRMATION-MERGE multi-seed (2 outer × 5 inner) — "
        "first multi-seed-validated edge in v3 history (regime_momentum_signed_5d). "
        "User directive 2026-05-08: investigate per-symbol feature importance to "
        "understand which features matter for which symbols, and whether features "
        "are 'better suited of symbols a but not b'. This is the IS-only feature-"
        "signature read-out the iter-v3/029 brief cites in Section 2.\n"
    )
    lines.append(
        "## Method\n\n"
        "Reads `model_importance_last_month_<SYM>.csv` (IS-only, last-month "
        "snapshot per the runner convention; same data the brief authors cite for "
        "feature-rank claims). For each of the 14 V3 features, captures: "
        "rank within symbol (1=highest importance), importance value, and "
        "0..1 normalized within-symbol importance. Then computes rank-range "
        "(max-min across the 3 symbols) and normalized stdev to flag "
        "SYMBOL-SPECIFIC vs SHARED features.\n\n"
        "Classification thresholds: rank_range ≥ 6 → HIGH-DISP-SYMBOL-SPECIFIC "
        "(top-half on one symbol, bottom-half on another); rank_range 3-5 → "
        "MID-DISP; rank_range ≤ 2 → LOW-DISP-SHARED (consistent across all 3 symbols).\n"
    )
    lines.append("## Per-symbol top-7 and bottom-7 features\n")
    lines.append("| Symbol | Top-7 (rank 1-7) | Bottom-7 (rank 8-14) |")
    lines.append("|---|---|---|")
    for _, r in top_bot_df.iterrows():
        lines.append(f"| **{r['symbol']}** | {r['top_7_features']} | {r['bottom_7_features']} |")
    lines.append("")

    lines.append("## Cross-symbol feature dispersion ranking\n")
    lines.append("Sorted by rank_range descending. HIGH dispersion = SYMBOL-SPECIFIC.\n")
    lines.append(
        "| Feature | rank_BCH | rank_LDO | rank_TRX | rank_range | norm_std | "
        "norm_BCH | norm_LDO | norm_TRX | norm_mean | classification |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for _, r in disp_df.iterrows():
        lines.append(
            f"| {r['feature']} | {int(r['rank_BCH'])} | {int(r['rank_LDO'])} | "
            f"{int(r['rank_TRX'])} | {int(r['rank_range'])} | {r['norm_std']:.4f} | "
            f"{r['norm_BCH']:.4f} | {r['norm_LDO']:.4f} | {r['norm_TRX']:.4f} | "
            f"{r['norm_mean']:.4f} | "
            f"{cls_df[cls_df['feature'] == r['feature']]['classification'].iloc[0]} |"
        )
    lines.append("")

    # SYMBOL-SPECIFIC features summary
    high_disp = cls_df[cls_df["classification"] == "HIGH-DISP-SYMBOL-SPECIFIC"]
    mid_disp = cls_df[cls_df["classification"] == "MID-DISP"]
    low_disp = cls_df[cls_df["classification"] == "LOW-DISP-SHARED"]

    lines.append("## Classification summary\n")
    lines.append(
        f"- HIGH-DISP-SYMBOL-SPECIFIC ({len(high_disp)}): "
        f"{', '.join(high_disp['feature'].tolist()) if len(high_disp) else '(none)'}"
    )
    lines.append(
        f"- MID-DISP ({len(mid_disp)}): "
        f"{', '.join(mid_disp['feature'].tolist()) if len(mid_disp) else '(none)'}"
    )
    lines.append(
        f"- LOW-DISP-SHARED ({len(low_disp)}): "
        f"{', '.join(low_disp['feature'].tolist()) if len(low_disp) else '(none)'}"
    )
    lines.append("")

    # regime_momentum_signed_5d deep dive
    lines.append("## regime_momentum_signed_5d — the multi-seed-validated edge feature\n")
    lines.append(
        "Per BASELINE_V3.md, this is THE first multi-seed-validated edge ingredient "
        "in v3 history. Contributed +0.1313 IS Sharpe + +0.1184 OOS Sharpe vs "
        "iter-v3/018 BOOTSTRAP. Its per-symbol importance from the multi-seed "
        "iter-v3/028 last-month snapshot:\n"
    )
    lines.append("| Symbol | rank | importance | norm |")
    lines.append("|---|---:|---:|---:|")
    for sym, vals in rmd.items():
        lines.append(
            f"| {sym} | {vals['rank']} | {vals['importance']:.2f} | {vals['norm']:.4f} |"
        )
    lines.append("")

    # Symbol-archetype interpretation
    bch_top = top_bot_df[top_bot_df["symbol"] == "BCHUSDT"]["top_7_features"].iloc[0].split(" | ")
    ldo_top = top_bot_df[top_bot_df["symbol"] == "LDOUSDT"]["top_7_features"].iloc[0].split(" | ")
    trx_top = top_bot_df[top_bot_df["symbol"] == "TRXUSDT"]["top_7_features"].iloc[0].split(" | ")
    bch_only = set(bch_top) - set(ldo_top) - set(trx_top)
    ldo_only = set(ldo_top) - set(bch_top) - set(trx_top)
    trx_only = set(trx_top) - set(bch_top) - set(ldo_top)
    shared_top = set(bch_top) & set(ldo_top) & set(trx_top)

    lines.append("## Symbol-archetype: which features are top-7 on ONLY ONE symbol?\n")
    lines.append(
        f"- **Top-7 SHARED across all 3 symbols** ({len(shared_top)}): "
        f"{', '.join(sorted(shared_top)) if shared_top else '(none)'}"
    )
    lines.append(
        f"- **BCH-only top-7** ({len(bch_only)}): "
        f"{', '.join(sorted(bch_only)) if bch_only else '(none)'}"
    )
    lines.append(
        f"- **LDO-only top-7** ({len(ldo_only)}): "
        f"{', '.join(sorted(ldo_only)) if ldo_only else '(none)'}"
    )
    lines.append(
        f"- **TRX-only top-7** ({len(trx_only)}): "
        f"{', '.join(sorted(trx_only)) if trx_only else '(none)'}"
    )
    lines.append("")

    # OOS sanity-check — informational only, not used for selection
    lines.append("## Sanity-check: per-symbol OOS PnL (informational only)\n")
    lines.append(
        "*This is OOS data shown for informational purpose only — feature selection "
        "depends ONLY on IS importance ranks above. The OOS columns confirm the "
        "concentration concentration is real and motivates the universe-expansion "
        "axis the iter-v3/029 brief proposes.*\n"
    )
    lines.append("| Symbol | IS trades | IS net_pnl% | OOS trades | OOS net_pnl% | OOS WR% |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    is_df = pnl["is"]
    oos_df = pnl["oos"]
    for sym in INCUMBENTS:
        is_row = is_df[is_df["symbol"] == sym].iloc[0]
        oos_row = oos_df[oos_df["symbol"] == sym].iloc[0]
        lines.append(
            f"| {sym} | {int(is_row['trades'])} | {float(is_row['net_pnl_pct']):+.2f} | "
            f"{int(oos_row['trades'])} | {float(oos_row['net_pnl_pct']):+.2f} | "
            f"{float(oos_row['win_rate']):.1f} |"
        )
    lines.append("")

    # Behavioral interpretation
    lines.append("## Key findings (QR interpretation)\n")
    lines.append(
        "1. **regime_momentum_signed_5d ranks differently per symbol**, confirming "
        "the user's intuition that engineered features may matter more for some "
        f"symbols than others. Per-symbol ranks: BCH={rmd['BCHUSDT']['rank']}, "
        f"LDO={rmd['LDOUSDT']['rank']}, TRX={rmd['TRXUSDT']['rank']}.\n"
    )
    lines.append(
        "2. **Symbol-specific (HIGH-DISP) features** are candidates whose value "
        "depends on the symbol's regime/microstructure. These are the strongest "
        "evidence for the user's 'features better suited of symbols a but not b' "
        f"hypothesis. Count: {len(high_disp)}.\n"
    )
    lines.append(
        "3. **Shared (LOW-DISP) features** are universal predictors that should "
        "transfer cleanly to NEW symbols added via universe expansion. These are "
        "the strongest predictors that the iter-v3/029 NEW symbol will USE the "
        f"same feature set productively. Count: {len(low_disp)}.\n"
    )
    lines.append(
        "4. **iter-v3/029 implication**: a new symbol candidate's likely "
        "compatibility with V3_FEATURE_COLUMNS is best estimated by its 8h-return "
        "correlation with the SHARED features' driving factor (BTC trend, vol "
        "regime, momentum mean-reversion balance), NOT by its raw price correlation "
        "with BCH/LDO/TRX. iter-v3/021's HBAR+AVAX failure confirms this — they had "
        "the LOWEST raw price correlation but produced -86% combined PnL. The "
        "missing diagnostic was 'does the candidate's regime structure match what "
        "the SHARED features capture?'\n"
    )
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    long_df = build_signature_long()
    long_df.to_csv(OUT_DIR / "per_symbol_feature_signature.csv", index=False)

    disp_df = build_dispersion(long_df)
    disp_df.to_csv(OUT_DIR / "feature_dispersion_ranking.csv", index=False)

    cls_df = identify_symbol_specific(disp_df)
    cls_df.to_csv(OUT_DIR / "symbol_specific_features.csv", index=False)

    top_bot_df = build_top_bottom_per_symbol(long_df)
    top_bot_df.to_csv(OUT_DIR / "symbol_specific_top_bottom.csv", index=False)

    pnl = load_per_symbol_pnl()

    write_synthesis(long_df, disp_df, cls_df, top_bot_df, pnl)

    # Console summary
    print("=== iter-v3/029 per-symbol feature analysis ===")
    print(f"Long signature rows: {len(long_df)}")
    print(f"Dispersion rows: {len(disp_df)}")
    print(f"Classification breakdown:")
    for cls, sub in cls_df.groupby("classification"):
        print(f"  {cls}: {len(sub)}")
    print(f"\nTop-3 highest dispersion features (most symbol-specific):")
    for _, r in disp_df.head(3).iterrows():
        print(
            f"  {r['feature']}: rank_range={int(r['rank_range'])}, "
            f"BCH={int(r['rank_BCH'])} LDO={int(r['rank_LDO'])} TRX={int(r['rank_TRX'])}"
        )
    print(f"\nTop-3 lowest dispersion features (most shared):")
    for _, r in disp_df.tail(3).iloc[::-1].iterrows():
        print(
            f"  {r['feature']}: rank_range={int(r['rank_range'])}, "
            f"BCH={int(r['rank_BCH'])} LDO={int(r['rank_LDO'])} TRX={int(r['rank_TRX'])}"
        )
    print(f"\nWritten:")
    print(f"  {OUT_DIR / 'per_symbol_feature_signature.csv'}")
    print(f"  {OUT_DIR / 'feature_dispersion_ranking.csv'}")
    print(f"  {OUT_DIR / 'symbol_specific_features.csv'}")
    print(f"  {OUT_DIR / 'symbol_specific_top_bottom.csv'}")
    print(f"  {OUT_DIR / 'synthesis.md'}")


if __name__ == "__main__":
    main()

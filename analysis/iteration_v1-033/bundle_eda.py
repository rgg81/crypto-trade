"""iter-v1/033 — Bundle EDA for CONFIRMATION substrate.

Phase 1 evidence script: cross-correlation between PROMISING specialist
trade rosters from cycle-3 (/018 LINK, /019 ETH+gate) + cycle-4
(/028 LTC+atr_sl=1.0, /031 composite_inv_concurrency wrapper).

KEY ADJUDICATION CARRIED FROM /032 REVIEW:
- /031's +1.04 OOS Sharpe DECOMPOSES into axis +0.21 + basin +0.83 (4x bias)
- The +0.83 basin component is a SINGLE-DRAW lottery, NOT compoundable
- The +0.21 axis-attributable component is the only thing /033 can stack on

QUESTIONS THIS SCRIPT ANSWERS:
1. Specialist trade-roster cross-correlations on OOS PnL series
   - If specialists are orthogonal, bundle OOS Sharpe ≈ sqrt(sum(Sharpe_i^2))
   - Per /026 sanity: bundle OOS Pearson should be < 0.50 for additivity
2. Per-symbol PnL by specialist (which symbols each specialist owns)
3. Monthly PnL series cross-correlation (the only correct co-movement metric)
4. Realistic bundle projection bands at multi-seed CONFIRMATION

Outputs (committed to analysis/iteration_v1-033/):
- specialist_per_symbol_pnl.csv
- specialist_monthly_pnl_oos.csv
- specialist_correlation_matrix.csv
- specialist_correlation_matrix_is.csv
- bundle_sharpe_projection.csv
- README.md (numerical summary)

Read-only: this script does NOT modify any source or production data.
Inputs are exclusively the IS/OOS reports of /018, /019, /028, /031.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports-v1"
OUT_DIR = ROOT / "analysis" / "iteration_v1-033"

# The 4 PROMISING ingredients
INGREDIENTS = {
    "/018": "iteration_v1-018",  # LINK specialist (Model C')
    "/019": "iteration_v1-019",  # ETH + BTC-trend gate (Model G)
    "/028": "iteration_v1-028",  # LTC + atr_sl=1.0 (Model D')
    "/031": "iteration_v1-031",  # composite_inv_concurrency (sample-weighting)
}

BASELINE = "iteration_v1-baseline"


def _read_trades(iter_dir: str, sample: str) -> pd.DataFrame:
    """Read trades.csv for an iteration's IS or OOS slice."""
    fpath = REPORTS / iter_dir / sample / "trades.csv"
    if not fpath.exists():
        return pd.DataFrame()
    df = pd.read_csv(fpath)
    # Add YYYY-MM from open_time (Binance ms epoch)
    df["close_dt"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df["yyyymm"] = df["close_dt"].dt.strftime("%Y-%m")
    # Use weighted_pnl (R2 scaled) as the realized PnL metric
    return df


def _monthly_pnl(df: pd.DataFrame) -> pd.Series:
    """Sum weighted_pnl by YYYY-MM."""
    if df.empty:
        return pd.Series(dtype="float64")
    g = df.groupby("yyyymm")["weighted_pnl"].sum().sort_index()
    return g


def _aggregate_per_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Group by symbol, compute trade count, win rate, mean PnL, total weighted PnL."""
    if df.empty:
        return pd.DataFrame()
    g = df.groupby("symbol").agg(
        trades=("net_pnl_pct", "count"),
        wins=("net_pnl_pct", lambda s: (s > 0).sum()),
        net_weighted_pnl=("weighted_pnl", "sum"),
        avg_net_pnl_pct=("net_pnl_pct", "mean"),
    ).reset_index()
    g["win_rate"] = (g["wins"] / g["trades"]).round(3)
    return g


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, pd.DataFrame] = {}

    # =====================================================================
    # 1) Per-symbol OOS PnL by specialist
    # =====================================================================
    rows = []
    for tag, iter_dir in INGREDIENTS.items():
        for sample in ("in_sample", "out_of_sample"):
            df = _read_trades(iter_dir, sample)
            agg = _aggregate_per_symbol(df)
            agg["specialist"] = tag
            agg["sample"] = sample
            rows.append(agg)
    df_per_symbol = pd.concat(rows, ignore_index=True)
    df_per_symbol = df_per_symbol[
        ["specialist", "sample", "symbol", "trades", "wins", "win_rate",
         "net_weighted_pnl", "avg_net_pnl_pct"]
    ]
    df_per_symbol.to_csv(OUT_DIR / "specialist_per_symbol_pnl.csv", index=False)
    out["per_symbol"] = df_per_symbol

    # =====================================================================
    # 2) Monthly OOS PnL series per specialist
    # =====================================================================
    oos_monthly: dict[str, pd.Series] = {}
    is_monthly: dict[str, pd.Series] = {}
    for tag, iter_dir in INGREDIENTS.items():
        df_oos = _read_trades(iter_dir, "out_of_sample")
        oos_monthly[tag] = _monthly_pnl(df_oos)
        df_is = _read_trades(iter_dir, "in_sample")
        is_monthly[tag] = _monthly_pnl(df_is)

    # Baseline for reference
    df_baseline_oos = _read_trades(BASELINE, "out_of_sample")
    oos_monthly["baseline"] = _monthly_pnl(df_baseline_oos)
    df_baseline_is = _read_trades(BASELINE, "in_sample")
    is_monthly["baseline"] = _monthly_pnl(df_baseline_is)

    oos_df = pd.DataFrame(oos_monthly).fillna(0.0).sort_index()
    is_df = pd.DataFrame(is_monthly).fillna(0.0).sort_index()
    oos_df.to_csv(OUT_DIR / "specialist_monthly_pnl_oos.csv")
    is_df.to_csv(OUT_DIR / "specialist_monthly_pnl_is.csv")
    out["monthly_oos"] = oos_df
    out["monthly_is"] = is_df

    # =====================================================================
    # 3) Cross-correlation matrix on monthly PnL (OOS and IS)
    # =====================================================================
    oos_corr = oos_df.corr(method="pearson").round(4)
    is_corr = is_df.corr(method="pearson").round(4)
    oos_corr.to_csv(OUT_DIR / "specialist_correlation_matrix_oos.csv")
    is_corr.to_csv(OUT_DIR / "specialist_correlation_matrix_is.csv")
    out["corr_oos"] = oos_corr
    out["corr_is"] = is_corr

    # Pairwise correlations (specialist x specialist, excluding baseline)
    specialist_tags = list(INGREDIENTS.keys())
    pairs = []
    for i, a in enumerate(specialist_tags):
        for b in specialist_tags[i + 1:]:
            pairs.append(
                {
                    "pair": f"{a} ↔ {b}",
                    "oos_corr": oos_corr.loc[a, b],
                    "is_corr": is_corr.loc[a, b],
                }
            )
    df_pairs = pd.DataFrame(pairs)
    df_pairs.to_csv(OUT_DIR / "specialist_pairwise_corr.csv", index=False)
    out["pairs"] = df_pairs

    # =====================================================================
    # 4) Bundle projection — additive vs correlated
    # =====================================================================
    # Specialist OOS Sharpe (monthly, single-seed; from comparison.csv headlines).
    # NOTE: /018, /019, /028 single-symbol; /031 is the WRAPPER applied to baseline pool.
    specialist_oos_sharpe = {
        "/018 LINK": 0.9789,
        "/019 ETH+gate": 0.6990,
        "/028 LTC+atr_sl=1.0": 0.3310,
        "/031 inv_concurrency_axis (frozen-HP)": 0.21,  # /032's CLEAN attribution
    }
    # The baseline portfolio OOS Sharpe is +0.6637.
    # Composition logic for the SPECIALIST BUNDLE (Option A):
    #   Replace the LINK slice of baseline with /018 LINK roster.
    #   Replace the ETH slice of baseline (in Model A pool) with /019 Model G.
    #   Replace the LTC slice of baseline (Model D) with /028 LTC+atr_sl=1.0.
    #   Keep BTC (Model A BTC-slice) and DOT (Model E) unchanged.
    # The "additive" projection treats specialists as independent contributors
    # to portfolio Sharpe. With 5 symbols and per-symbol Sharpes s_i:
    #   bundle Sharpe ≈ sqrt(sum(s_i^2)) / sqrt(N_active) if uncorrelated
    # We need PER-SYMBOL Sharpes from baseline (BTC, DOT slices)
    # and specialist Sharpes for replaced symbols.
    # Approximation: use the specialist headlines (single-symbol OOS Sharpe).

    # Per-symbol Sharpes (annualized monthly) computed below from monthly_oos.
    baseline_per_symbol_oos_sharpe = {
        "BTC": None,   # filled from per_symbol attribution below
        "ETH": None,
        "LINK": None,
        "LTC": None,
        "DOT": None,
    }

    # Per-baseline-symbol monthly Sharpe — use the baseline OOS per_symbol.csv
    # net_pnl_pct as a proxy; then compute realistic per-symbol monthly Sharpe
    # using baseline's trades.csv weighted_pnl monthly series per symbol.
    base_oos = _read_trades(BASELINE, "out_of_sample")
    if not base_oos.empty:
        for sym in ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"):
            sym_df = base_oos[base_oos["symbol"] == sym]
            monthly = sym_df.groupby("yyyymm")["weighted_pnl"].sum().sort_index()
            if len(monthly) >= 3 and monthly.std() > 0:
                sharpe = (monthly.mean() / monthly.std()) * math.sqrt(12)
                baseline_per_symbol_oos_sharpe[sym[:-4]] = round(sharpe, 4)
            else:
                baseline_per_symbol_oos_sharpe[sym[:-4]] = float("nan")

    # Save per-symbol baseline OOS Sharpe
    pd.DataFrame(
        [
            {"symbol": k, "baseline_oos_monthly_sharpe": v}
            for k, v in baseline_per_symbol_oos_sharpe.items()
        ]
    ).to_csv(OUT_DIR / "baseline_per_symbol_oos_sharpe.csv", index=False)

    # Specialist replacement table
    replacements = pd.DataFrame(
        [
            {"symbol": "BTC", "model": "A (Pool BTC-slice)",
             "baseline_oos_sharpe": baseline_per_symbol_oos_sharpe["BTC"],
             "specialist_oos_sharpe": baseline_per_symbol_oos_sharpe["BTC"],
             "specialist": "BASELINE (no change)"},
            {"symbol": "ETH", "model": "G (ETH + BTC-trend gate)",
             "baseline_oos_sharpe": baseline_per_symbol_oos_sharpe["ETH"],
             "specialist_oos_sharpe": specialist_oos_sharpe["/019 ETH+gate"],
             "specialist": "/019 ETH+gate"},
            {"symbol": "LINK", "model": "C' (LINK specialist)",
             "baseline_oos_sharpe": baseline_per_symbol_oos_sharpe["LINK"],
             "specialist_oos_sharpe": specialist_oos_sharpe["/018 LINK"],
             "specialist": "/018 LINK"},
            {"symbol": "LTC", "model": "D' (LTC + atr_sl=1.0)",
             "baseline_oos_sharpe": baseline_per_symbol_oos_sharpe["LTC"],
             "specialist_oos_sharpe": specialist_oos_sharpe["/028 LTC+atr_sl=1.0"],
             "specialist": "/028 LTC+atr_sl=1.0"},
            {"symbol": "DOT", "model": "E (DOT baseline)",
             "baseline_oos_sharpe": baseline_per_symbol_oos_sharpe["DOT"],
             "specialist_oos_sharpe": baseline_per_symbol_oos_sharpe["DOT"],
             "specialist": "BASELINE (no change)"},
        ]
    )
    replacements.to_csv(OUT_DIR / "specialist_replacement_table.csv", index=False)
    out["replacements"] = replacements

    # =====================================================================
    # 5) Additive bundle projection (Option A, no /031 wrapper)
    # =====================================================================
    # Naive RMS: sqrt(sum(s_i^2)) / sqrt(5) for portfolio of 5 uncorrelated symbol-Sharpes
    sharpe_vec = [r for r in replacements["specialist_oos_sharpe"] if pd.notna(r)]
    naive_rms = math.sqrt(sum(s ** 2 for s in sharpe_vec) / max(1, len(sharpe_vec)))
    # Realistic (50% diversification benefit relative to fully-additive):
    realistic_sum = sum(sharpe_vec) / len(sharpe_vec)  # weighted avg per-symbol
    realistic_correlated = sum(sharpe_vec) / math.sqrt(len(sharpe_vec))  # half-diversified

    # Apply OOS/IS single-seed lottery deflator from /015 precedent:
    # /015 precedent showed +0.30 OOS DEGRADATION at multi-seed vs single-seed
    # Apply 65% retention to project multi-seed numbers
    multi_seed_deflator = 0.65
    option_a_projection = realistic_correlated * multi_seed_deflator

    # Option B: add /031 axis-only lift (+0.21 from /032 frozen-HP isolation)
    # /031's basin component (+0.83) is NOT compoundable — single-draw artifact
    option_b_projection = option_a_projection + 0.21  # ONLY the clean axis component

    bundle_projection = pd.DataFrame([
        {
            "scenario": "Naive RMS uncorrelated (upper bound)",
            "computation": "sqrt(sum(s_i^2) / n)",
            "value": round(naive_rms, 4),
        },
        {
            "scenario": "Naive average per-symbol (lower bound)",
            "computation": "sum(s_i) / n",
            "value": round(realistic_sum, 4),
        },
        {
            "scenario": "Half-diversified (sum/sqrt(n))",
            "computation": "sum(s_i) / sqrt(n)",
            "value": round(realistic_correlated, 4),
        },
        {
            "scenario": "Option A multi-seed deflated (× 0.65 lottery)",
            "computation": "half-div × 0.65",
            "value": round(option_a_projection, 4),
        },
        {
            "scenario": "Option B (A + /031 axis-only +0.21)",
            "computation": "Option A + 0.21",
            "value": round(option_b_projection, 4),
        },
    ])
    bundle_projection.to_csv(OUT_DIR / "bundle_sharpe_projection.csv", index=False)
    out["projection"] = bundle_projection

    # =====================================================================
    # README — human-readable summary
    # =====================================================================
    lines = []
    lines.append("# iter-v1/033 Bundle EDA — Numerical Highlights\n")
    lines.append("## 1. Per-Symbol Baseline OOS Monthly Sharpe (annualized)\n")
    for sym, v in baseline_per_symbol_oos_sharpe.items():
        lines.append(f"- **{sym}** baseline OOS monthly Sharpe = {v}")
    lines.append("")
    lines.append("## 2. Specialist Pairwise OOS Pearson Correlation (monthly PnL)\n")
    lines.append("| Pair | OOS Pearson | IS Pearson |")
    lines.append("|---|---|---|")
    for _, row in df_pairs.iterrows():
        lines.append(
            f"| {row['pair']} | {row['oos_corr']:+.4f} | {row['is_corr']:+.4f} |"
        )
    lines.append("")
    lines.append("**Interpretation**: bundle additivity requires OOS Pearson < 0.50 across pairs. Any pair exceeding 0.50 contributes correlated-drag to the bundle.\n")

    lines.append("## 3. Specialist Replacement Table (per-symbol OOS Sharpe)\n")
    lines.append("| Symbol | Baseline OOS Sharpe | Specialist | Specialist OOS Sharpe | Δ |")
    lines.append("|---|---|---|---|---|")
    for _, row in replacements.iterrows():
        delta = row["specialist_oos_sharpe"] - row["baseline_oos_sharpe"] if pd.notna(row["baseline_oos_sharpe"]) and pd.notna(row["specialist_oos_sharpe"]) else float("nan")
        lines.append(
            f"| {row['symbol']} | {row['baseline_oos_sharpe']:+.4f} | {row['specialist']} | "
            f"{row['specialist_oos_sharpe']:+.4f} | {delta:+.4f} |"
        )
    lines.append("")
    lines.append("## 4. Bundle Sharpe Projection\n")
    lines.append("| Scenario | Computation | Value |")
    lines.append("|---|---|---|")
    for _, row in bundle_projection.iterrows():
        lines.append(f"| {row['scenario']} | {row['computation']} | {row['value']:+.4f} |")
    lines.append("")
    lines.append("**Key Verdict for /033**: bundle multi-seed mean projected ≈ +{:.2f} (Option A) or +{:.2f} (Option B).".format(
        option_a_projection, option_b_projection
    ))
    lines.append(f"Hard merge floor +1.0 requires Option B with NO basin drift (i.e. axis stack actually compounds). The +0.21 /031 axis-only component is the LOAD-BEARING uncertainty.\n")
    lines.append("## 5. CRITICAL — /032 Frozen-HP Adjudication\n")
    lines.append("- /031 headline +1.04 OOS Δ = **axis +0.21** + **basin +0.83**")
    lines.append("- The +0.83 basin component is SINGLE-DRAW LOTTERY — NOT compoundable at multi-seed")
    lines.append("- Bundle projections use ONLY the **axis +0.21** component (Option B)")
    lines.append("- Option A (without /031) is the conservative baseline — same as Option B - 0.21")

    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")

    # =====================================================================
    # Print summary to stdout
    # =====================================================================
    print(f"\n[bundle_eda] EDA complete. Output dir: {OUT_DIR}")
    print(f"\n--- Pairwise Specialist OOS Correlations ---")
    print(df_pairs.to_string(index=False))
    print(f"\n--- Bundle Sharpe Projection ---")
    print(bundle_projection.to_string(index=False))
    print(f"\n--- Per-Symbol Baseline OOS Sharpe ---")
    for sym, v in baseline_per_symbol_oos_sharpe.items():
        print(f"  {sym}: {v}")


if __name__ == "__main__":
    main()

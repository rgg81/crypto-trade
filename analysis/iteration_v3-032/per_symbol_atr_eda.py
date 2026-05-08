"""iter-v3/032 per-symbol ATR distribution EDA — LDO volatility regime mismatch.

Purpose
-------
iter-v3/030 per-symbol FEATURES for LDO → NEGATIVE.
iter-v3/031 DROP LDO → NEGATIVE (LDO IS-positive +40, removing it killed IS edge).

The diagnosis from the iter-v3/031 Critic FINAL: LDO's issue is REGIME MISMATCH
(different volatility profile), NOT a feature problem and NOT a drag problem.
The (2.0, 1.0) ATR multipliers may not fit LDO's volatility distribution.

iter-v3/032 hypothesis: per-symbol ATR multipliers tuned to LDO's natr_21
distribution lift LDO performance without hurting BCH/TRX/ALGO.

This script extends the per-symbol architecture (V3_FEATURES_PER_SYMBOL from
iter-v3/030) to the LABELING layer (V3_ATR_MULTIPLIERS_PER_SYMBOL).

Inputs (READ-ONLY; IS-window only — pre-OOS-cutoff 2025-03-24)
----------------------------------------------------------------
- data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT,ALGOUSDT}_8h_features.parquet
  (columns used: open_time, close, natr_21_raw)
- reports-v3/iteration_v3-029/in_sample/trades.csv (4-symbol BCH+LDO+TRX+ALGO bundle)
  (columns used: symbol, exit_reason, weighted_pnl, weight_factor)
- reports-v3/iteration_v3-029/out_of_sample/trades.csv (informational only;
  scoring DOES NOT use OOS data)

Outputs (committed alongside this script)
------------------------------------------
- analysis/iteration_v3-032/per_symbol_atr_distribution.csv (long; per-symbol
  natr_21_raw distribution percentiles)
- analysis/iteration_v3-032/per_symbol_label_outcome_pattern.csv (per-symbol
  hit-rate distribution: TP / SL / timeout pattern at iter-v3/029)
- analysis/iteration_v3-032/atr_multiplier_recommendation.csv (LDO vs others
  comparison; chosen LDO multipliers + rationale)
- analysis/iteration_v3-032/synthesis.md (narrative + chosen LDO multipliers)

Methodology
-----------
1. Load IS-window features parquet for each of BCH/LDO/TRX/ALGO. Slice to
   open_time < OOS_CUTOFF_MS = 1742774400000.
2. Compute per-symbol natr_21_raw distribution: median, 25th, 75th, 90th,
   95th percentile + standard deviation.
3. Load IS trades from iter-v3/029 (4-symbol bundle). Compute per-symbol
   exit-reason composition: % take_profit, % stop_loss, % timeout, %
   end_of_data.
4. The relationship between natr_21_raw scaling and exit-reason composition
   reveals whether LDO's (2.0, 1.0) labels are too-tight (excessive timeouts)
   or too-loose (excessive stop_losses) for its volatility regime.
5. Recommend LDO ATR multipliers based on the comparative analysis.

Per López de Prado AFML Ch. 3 — triple-barrier labeling: barrier widths are
tuned to the per-symbol volatility distribution. A (2.0, 1.0) ATR multiplier
applied uniformly across BCH/LDO/TRX/ALGO assumes natr_21_raw is comparable
across symbols, which is the testable hypothesis in this script.

This script DOES NOT touch OOS data for ranking — only for informational
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
FEATURES_DIR = REPO_ROOT / "data" / "features_v3"
ITER029_IS = REPO_ROOT / "reports-v3" / "iteration_v3-029" / "in_sample"
ITER029_OOS = REPO_ROOT / "reports-v3" / "iteration_v3-029" / "out_of_sample"
OUT_DIR = REPO_ROOT / "analysis" / "iteration_v3-032"

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24

ALL_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")
PEER_SYMBOLS = ("BCHUSDT", "TRXUSDT", "ALGOUSDT")  # the well-fitting peers
TARGET_SYMBOL = "LDOUSDT"

CURRENT_ATR_TP = 2.0
CURRENT_ATR_SL = 1.0

OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Per-symbol natr_21_raw distribution (IS-window only)
# ---------------------------------------------------------------------------


def compute_natr_distribution() -> pd.DataFrame:
    """Compute per-symbol natr_21_raw IS-window distribution percentiles."""
    rows: list[dict] = []
    for sym in ALL_SYMBOLS:
        path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(path, columns=["open_time", "close", "natr_21_raw"])
        df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        natr = df_is["natr_21_raw"].dropna()
        rows.append(
            dict(
                symbol=sym,
                n_is_candles=int(len(df_is)),
                n_is_natr_valid=int(len(natr)),
                natr_min=float(natr.min()),
                natr_p10=float(natr.quantile(0.10)),
                natr_p25=float(natr.quantile(0.25)),
                natr_median=float(natr.median()),
                natr_p75=float(natr.quantile(0.75)),
                natr_p90=float(natr.quantile(0.90)),
                natr_p95=float(natr.quantile(0.95)),
                natr_max=float(natr.max()),
                natr_mean=float(natr.mean()),
                natr_std=float(natr.std()),
            )
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. Per-symbol exit-reason composition from iter-v3/029 IS trades
# ---------------------------------------------------------------------------


def load_trades(path: Path) -> pd.DataFrame:
    """Load iteration trades CSV. Tolerates absence (returns empty DataFrame)."""
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def compute_exit_reason_pattern(trades: pd.DataFrame) -> pd.DataFrame:
    """Compute per-symbol exit-reason composition.

    Returns columns: symbol, n_trades, n_tp, n_sl, n_timeout, n_end_of_data,
    pct_tp, pct_sl, pct_timeout, pct_end_of_data, mean_weighted_pnl, total_weighted_pnl.
    """
    if trades.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for sym in ALL_SYMBOLS:
        sub = trades[trades["symbol"] == sym]
        n = len(sub)
        if n == 0:
            rows.append(
                dict(
                    symbol=sym, n_trades=0, n_tp=0, n_sl=0, n_timeout=0,
                    n_end_of_data=0, pct_tp=np.nan, pct_sl=np.nan,
                    pct_timeout=np.nan, pct_end_of_data=np.nan,
                    mean_weighted_pnl=np.nan, total_weighted_pnl=0.0,
                )
            )
            continue

        n_tp = int((sub["exit_reason"] == "take_profit").sum())
        n_sl = int((sub["exit_reason"] == "stop_loss").sum())
        n_timeout = int((sub["exit_reason"] == "timeout").sum())
        n_eod = int((sub["exit_reason"] == "end_of_data").sum())
        rows.append(
            dict(
                symbol=sym,
                n_trades=n,
                n_tp=n_tp,
                n_sl=n_sl,
                n_timeout=n_timeout,
                n_end_of_data=n_eod,
                pct_tp=100.0 * n_tp / n,
                pct_sl=100.0 * n_sl / n,
                pct_timeout=100.0 * n_timeout / n,
                pct_end_of_data=100.0 * n_eod / n,
                mean_weighted_pnl=float(sub["weighted_pnl"].mean()),
                total_weighted_pnl=float(sub["weighted_pnl"].sum()),
            )
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. Build joint per-symbol distribution + label-outcome table
# ---------------------------------------------------------------------------


def build_atr_multiplier_recommendation(
    distribution: pd.DataFrame,
    is_pattern: pd.DataFrame,
) -> pd.DataFrame:
    """Combine natr distribution + exit-reason pattern; recommend LDO ATR multipliers.

    Logic
    -----
    - The barrier in % terms is `natr_21_raw * atr_multiplier`. A symbol with
      LOWER median natr_21_raw produces NARROWER barriers at the same multiplier,
      meaning more trades hit timeout (price doesn't move enough to hit either
      barrier). HIGHER natr → wider barriers → fewer timeouts but higher noise
      penetration risk (stop_loss before take_profit).
    - The PEER reference is the median of BCH+TRX+ALGO natr distribution.
      LDO's deviation from the peer median signals the multiplier adjustment
      direction.
    - Recommended multipliers preserve LDO's effective barrier WIDTH IN PRICE %
      terms equal to the peer-median barrier width. If LDO has natr 80% of the
      peer median, multipliers scale by 1/0.8 = 1.25× to compensate.
    """
    rows: list[dict] = []

    peer_median_natr = float(
        distribution[distribution["symbol"].isin(PEER_SYMBOLS)]["natr_median"].median()
    )

    for sym in ALL_SYMBOLS:
        d_row = distribution[distribution["symbol"] == sym].iloc[0]
        p_row = is_pattern[is_pattern["symbol"] == sym].iloc[0] if not is_pattern.empty else None

        natr_median = float(d_row["natr_median"])
        ratio_to_peer = natr_median / peer_median_natr if peer_median_natr > 0 else 1.0

        # Barrier width in % at current (2.0, 1.0):
        tp_barrier_pct_at_median = natr_median * CURRENT_ATR_TP
        sl_barrier_pct_at_median = natr_median * CURRENT_ATR_SL

        # Effective barrier width recommended multiplier:
        # Goal: LDO's effective barrier width matches peer-median.
        # If LDO natr > peer median, LDO barriers are TOO WIDE at (2.0, 1.0)
        # → tighter multipliers (LDO_mult = base / (LDO_natr / peer_natr)).
        # If LDO natr < peer median, LDO barriers are TOO TIGHT
        # → wider multipliers.
        rec_atr_tp = CURRENT_ATR_TP / ratio_to_peer
        rec_atr_sl = CURRENT_ATR_SL / ratio_to_peer

        rows.append(
            dict(
                symbol=sym,
                natr_median=natr_median,
                ratio_to_peer_median=ratio_to_peer,
                current_tp_barrier_pct=tp_barrier_pct_at_median,
                current_sl_barrier_pct=sl_barrier_pct_at_median,
                # IS hit-rate composition at iter-v3/029
                pct_tp_iter029=float(p_row["pct_tp"]) if p_row is not None else np.nan,
                pct_sl_iter029=float(p_row["pct_sl"]) if p_row is not None else np.nan,
                pct_timeout_iter029=float(p_row["pct_timeout"]) if p_row is not None else np.nan,
                # Recommended multipliers to match peer effective barrier width
                rec_atr_tp=rec_atr_tp,
                rec_atr_sl=rec_atr_sl,
            )
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Tighter / Looser candidate grid
# ---------------------------------------------------------------------------


def build_candidate_grid(distribution: pd.DataFrame) -> pd.DataFrame:
    """Build a candidate (atr_tp, atr_sl) grid for LDO and report effect on
    barrier % at LDO median natr.

    Candidates are scaled relative to (2.0, 1.0) base. Examines:
      0.5×, 0.625×, 0.75×, 0.875×, 1.0×, 1.125×, 1.25×, 1.5× scaling.
    """
    ldo_natr_median = float(
        distribution[distribution["symbol"] == TARGET_SYMBOL]["natr_median"].iloc[0]
    )
    peer_natr_median = float(
        distribution[distribution["symbol"].isin(PEER_SYMBOLS)]["natr_median"].median()
    )
    peer_tp_barrier = peer_natr_median * CURRENT_ATR_TP
    peer_sl_barrier = peer_natr_median * CURRENT_ATR_SL

    scales = (0.5, 0.625, 0.75, 0.875, 1.0, 1.125, 1.25, 1.5)
    rows: list[dict] = []
    for s in scales:
        atr_tp = CURRENT_ATR_TP * s
        atr_sl = CURRENT_ATR_SL * s
        ldo_tp_barrier = ldo_natr_median * atr_tp
        ldo_sl_barrier = ldo_natr_median * atr_sl
        rows.append(
            dict(
                scale=s,
                atr_tp=atr_tp,
                atr_sl=atr_sl,
                ldo_tp_barrier_pct=ldo_tp_barrier,
                ldo_sl_barrier_pct=ldo_sl_barrier,
                peer_tp_barrier_pct=peer_tp_barrier,
                peer_sl_barrier_pct=peer_sl_barrier,
                ldo_to_peer_tp_ratio=ldo_tp_barrier / peer_tp_barrier,
                ldo_to_peer_sl_ratio=ldo_sl_barrier / peer_sl_barrier,
            )
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. Synthesis writer
# ---------------------------------------------------------------------------


def write_synthesis(
    distribution: pd.DataFrame,
    is_pattern: pd.DataFrame,
    oos_pattern: pd.DataFrame,
    recommendation: pd.DataFrame,
    candidate_grid: pd.DataFrame,
    chosen_atr_tp: float,
    chosen_atr_sl: float,
    chosen_scale: float,
    rationale: str,
) -> None:
    out = OUT_DIR / "synthesis.md"
    lines: list[str] = []
    lines.append("# iter-v3/032 per-symbol ATR multiplier EDA — Synthesis\n")
    lines.append(
        "Purpose: diagnose LDO's regime mismatch as a LABELING-layer problem; "
        "recommend per-symbol ATR multipliers to match peer (BCH/TRX/ALGO) "
        "effective barrier widths.\n\n"
    )
    lines.append(
        "Source data (IS-only; OOS reported informationally at end):\n"
        "- `data/features_v3/{sym}_8h_features.parquet` — natr_21_raw IS-window distribution\n"
        "- `reports-v3/iteration_v3-029/in_sample/trades.csv` — 4-symbol bundle exit-reason composition\n\n"
    )

    lines.append("## 1. Per-symbol natr_21_raw distribution (IS-window only)\n\n")
    lines.append(
        "| symbol | n_is_natr | min | p10 | p25 | median | p75 | p90 | p95 | max | mean | std |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    for _, row in distribution.iterrows():
        lines.append(
            f"| {row['symbol']} | {row['n_is_natr_valid']} | "
            f"{row['natr_min']:.4f} | {row['natr_p10']:.4f} | {row['natr_p25']:.4f} | "
            f"{row['natr_median']:.4f} | {row['natr_p75']:.4f} | {row['natr_p90']:.4f} | "
            f"{row['natr_p95']:.4f} | {row['natr_max']:.4f} | "
            f"{row['natr_mean']:.4f} | {row['natr_std']:.4f} |\n"
        )

    peer_med = float(
        distribution[distribution["symbol"].isin(PEER_SYMBOLS)]["natr_median"].median()
    )
    ldo_med = float(distribution[distribution["symbol"] == TARGET_SYMBOL]["natr_median"].iloc[0])
    lines.append(
        f"\n**Peer (BCH+TRX+ALGO) median natr_21_raw**: {peer_med:.4f}\n"
        f"**LDO median natr_21_raw**: {ldo_med:.4f}\n"
        f"**LDO/peer ratio**: {ldo_med / peer_med:.4f} "
        f"({'LDO HIGHER vol' if ldo_med > peer_med else 'LDO LOWER vol'} "
        f"than peer median)\n\n"
    )

    lines.append("## 2. Per-symbol IS exit-reason composition (iter-v3/029 trades.csv)\n\n")
    lines.append(
        "| symbol | n_trades | n_tp | n_sl | n_timeout | %_tp | %_sl | %_timeout | mean_pnl | total_pnl |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    for _, row in is_pattern.iterrows():
        if row["n_trades"] == 0:
            lines.append(
                f"| {row['symbol']} | 0 | — | — | — | — | — | — | — | 0.00 |\n"
            )
            continue
        lines.append(
            f"| {row['symbol']} | {row['n_trades']} | {row['n_tp']} | {row['n_sl']} | "
            f"{row['n_timeout']} | {row['pct_tp']:.1f}% | {row['pct_sl']:.1f}% | "
            f"{row['pct_timeout']:.1f}% | {row['mean_weighted_pnl']:.3f} | "
            f"{row['total_weighted_pnl']:.2f} |\n"
        )

    lines.append("\n## 3. Per-symbol OOS exit-reason composition (iter-v3/029 trades.csv) — INFORMATIONAL\n\n")
    if oos_pattern.empty:
        lines.append("(OOS data not loaded — informational only.)\n\n")
    else:
        lines.append(
            "| symbol | n_trades | n_tp | n_sl | n_timeout | %_tp | %_sl | %_timeout | mean_pnl | total_pnl |\n"
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        )
        for _, row in oos_pattern.iterrows():
            if row["n_trades"] == 0:
                lines.append(
                    f"| {row['symbol']} | 0 | — | — | — | — | — | — | — | 0.00 |\n"
                )
                continue
            lines.append(
                f"| {row['symbol']} | {row['n_trades']} | {row['n_tp']} | {row['n_sl']} | "
                f"{row['n_timeout']} | {row['pct_tp']:.1f}% | {row['pct_sl']:.1f}% | "
                f"{row['pct_timeout']:.1f}% | {row['mean_weighted_pnl']:.3f} | "
                f"{row['total_weighted_pnl']:.2f} |\n"
            )
        lines.append(
            "\n*OOS data shown for sanity check only — not used in candidate scoring.*\n"
        )

    lines.append("\n## 4. ATR multiplier recommendation table (per-symbol)\n\n")
    lines.append(
        "Recommended multipliers preserve LDO's effective barrier width IN PRICE % "
        "EQUAL TO the peer-median barrier width — i.e., scale by 1/(LDO_natr / peer_natr).\n\n"
    )
    lines.append(
        "| symbol | natr_median | ratio_to_peer | tp_barrier_now | sl_barrier_now | "
        "%_tp_iter029 | %_sl_iter029 | %_timeout_iter029 | rec_atr_tp | rec_atr_sl |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    for _, row in recommendation.iterrows():
        lines.append(
            f"| {row['symbol']} | {row['natr_median']:.4f} | "
            f"{row['ratio_to_peer_median']:.4f} | "
            f"{row['current_tp_barrier_pct']:.4f} | {row['current_sl_barrier_pct']:.4f} | "
            f"{row['pct_tp_iter029']:.1f}% | {row['pct_sl_iter029']:.1f}% | "
            f"{row['pct_timeout_iter029']:.1f}% | "
            f"{row['rec_atr_tp']:.4f} | {row['rec_atr_sl']:.4f} |\n"
        )

    lines.append("\n## 5. LDO candidate grid (scaled relative to baseline 2.0/1.0)\n\n")
    lines.append(
        "| scale | atr_tp | atr_sl | LDO_tp_barrier% | LDO_sl_barrier% | "
        "peer_tp_barrier% | peer_sl_barrier% | LDO/peer_tp_ratio | LDO/peer_sl_ratio |\n"
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    for _, row in candidate_grid.iterrows():
        lines.append(
            f"| {row['scale']:.3f} | {row['atr_tp']:.4f} | {row['atr_sl']:.4f} | "
            f"{row['ldo_tp_barrier_pct']:.4f} | {row['ldo_sl_barrier_pct']:.4f} | "
            f"{row['peer_tp_barrier_pct']:.4f} | {row['peer_sl_barrier_pct']:.4f} | "
            f"{row['ldo_to_peer_tp_ratio']:.4f} | {row['ldo_to_peer_sl_ratio']:.4f} |\n"
        )

    lines.append(
        f"\n## 6. Chosen LDO ATR multipliers\n\n"
        f"**Chosen (atr_tp, atr_sl) for LDO**: ({chosen_atr_tp:.4f}, {chosen_atr_sl:.4f})\n"
        f"**Scale relative to (2.0, 1.0)**: {chosen_scale:.4f}×\n\n"
        f"**Rationale**:\n{rationale}\n\n"
    )

    lines.append(
        "## 7. Architecture (iter-v3/032 brief Section 3)\n\n"
        "```python\n"
        "# src/crypto_trade/features_v3/__init__.py\n"
        "DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)\n"
        "\n"
        f"V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {{\n"
        f"    \"LDOUSDT\": ({chosen_atr_tp:.4f}, {chosen_atr_sl:.4f}),  # iter-v3/032 EDA tuning\n"
        f"}}\n"
        "\n"
        "def atr_multipliers_for_symbol(symbol: str) -> tuple[float, float]:\n"
        "    return V3_ATR_MULTIPLIERS_PER_SYMBOL.get(symbol, DEFAULT_ATR_MULTIPLIERS)\n"
        "```\n\n"
        "Runner (`run_baseline_v3.py::_build_v3_model`): replace hardcoded `atr_tp_multiplier=2.0, "
        "atr_sl_multiplier=1.0` with `atr_tp_multiplier=atr_tp, atr_sl_multiplier=atr_sl` where "
        "`atr_tp, atr_sl = atr_multipliers_for_symbol(symbol)`.\n\n"
        "BCH+TRX+ALGO fall back to (2.0, 1.0) — bit-identical to iter-v3/029 dispatch.\n"
    )
    out.write_text("".join(lines))


def main() -> None:
    print(f"[iter-v3/032 EDA] Reading IS-only feature parquets from {FEATURES_DIR}")
    distribution = compute_natr_distribution()
    distribution.to_csv(OUT_DIR / "per_symbol_atr_distribution.csv", index=False)
    print(f"  wrote per_symbol_atr_distribution.csv ({len(distribution)} rows)")

    print(f"[iter-v3/032 EDA] Reading IS trades from {ITER029_IS}")
    is_trades = load_trades(ITER029_IS / "trades.csv")
    is_pattern = compute_exit_reason_pattern(is_trades)
    is_pattern.to_csv(OUT_DIR / "per_symbol_label_outcome_pattern.csv", index=False)
    print(f"  wrote per_symbol_label_outcome_pattern.csv ({len(is_pattern)} rows)")

    print(f"[iter-v3/032 EDA] Reading OOS trades (informational) from {ITER029_OOS}")
    oos_trades = load_trades(ITER029_OOS / "trades.csv")
    oos_pattern = compute_exit_reason_pattern(oos_trades)
    if not oos_pattern.empty:
        oos_pattern.to_csv(OUT_DIR / "per_symbol_label_outcome_pattern_oos.csv", index=False)
        print(f"  wrote per_symbol_label_outcome_pattern_oos.csv ({len(oos_pattern)} rows)")

    recommendation = build_atr_multiplier_recommendation(distribution, is_pattern)
    recommendation.to_csv(OUT_DIR / "atr_multiplier_recommendation.csv", index=False)
    print(f"  wrote atr_multiplier_recommendation.csv ({len(recommendation)} rows)")

    candidate_grid = build_candidate_grid(distribution)
    candidate_grid.to_csv(OUT_DIR / "ldo_candidate_grid.csv", index=False)
    print(f"  wrote ldo_candidate_grid.csv ({len(candidate_grid)} rows)")

    # ---------------------------------------------------------------------
    # Choose LDO ATR multipliers
    # ---------------------------------------------------------------------
    # Strategy: pick the candidate scale that brings LDO's effective barrier
    # ratio closest to 1.0 vs peer (i.e., neutralizes LDO's vol mismatch).
    closest_idx = (candidate_grid["ldo_to_peer_tp_ratio"] - 1.0).abs().idxmin()
    closest_row = candidate_grid.loc[closest_idx]
    chosen_atr_tp = float(closest_row["atr_tp"])
    chosen_atr_sl = float(closest_row["atr_sl"])
    chosen_scale = float(closest_row["scale"])

    ldo_med = float(
        distribution[distribution["symbol"] == TARGET_SYMBOL]["natr_median"].iloc[0]
    )
    peer_med = float(
        distribution[distribution["symbol"].isin(PEER_SYMBOLS)]["natr_median"].median()
    )
    is_pattern_ldo = is_pattern[is_pattern["symbol"] == TARGET_SYMBOL]
    if not is_pattern_ldo.empty and is_pattern_ldo.iloc[0]["n_trades"] > 0:
        ldo_pct_tp = float(is_pattern_ldo.iloc[0]["pct_tp"])
        ldo_pct_sl = float(is_pattern_ldo.iloc[0]["pct_sl"])
        ldo_pct_timeout = float(is_pattern_ldo.iloc[0]["pct_timeout"])
    else:
        ldo_pct_tp = ldo_pct_sl = ldo_pct_timeout = float("nan")

    # Peer aggregate hit-rate composition for comparison
    peer_pattern = is_pattern[is_pattern["symbol"].isin(PEER_SYMBOLS)]
    peer_n_total = peer_pattern["n_trades"].sum() if not peer_pattern.empty else 0
    if peer_n_total > 0:
        peer_pct_tp = 100.0 * peer_pattern["n_tp"].sum() / peer_n_total
        peer_pct_sl = 100.0 * peer_pattern["n_sl"].sum() / peer_n_total
        peer_pct_timeout = 100.0 * peer_pattern["n_timeout"].sum() / peer_n_total
    else:
        peer_pct_tp = peer_pct_sl = peer_pct_timeout = float("nan")

    rationale_parts = []
    rationale_parts.append(
        f"- LDO median natr_21_raw = {ldo_med:.4f}; peer (BCH+TRX+ALGO) median = "
        f"{peer_med:.4f}; ratio LDO/peer = {ldo_med / peer_med:.4f}.\n"
    )
    if ldo_med > peer_med:
        direction = (
            "LDO has HIGHER realized vol than peer median. At (2.0, 1.0), LDO's "
            "effective barriers are TOO WIDE in price-% terms — LDO trades "
            "rarely hit either barrier and time out, OR hit SL too easily on "
            "noise penetration. Tighter multipliers compress barriers to the "
            "peer's effective scale."
        )
    elif ldo_med < peer_med:
        direction = (
            "LDO has LOWER realized vol than peer median. At (2.0, 1.0), LDO's "
            "effective barriers are TOO TIGHT in price-% terms — LDO trades "
            "should produce more take_profit hits but instead hit timeouts due "
            "to insufficient price excursion. Wider multipliers expand barriers "
            "to the peer's effective scale."
        )
    else:
        direction = (
            "LDO natr matches peer median; barrier width is not the issue. "
            "Recommendation defaults to (2.0, 1.0)."
        )
    rationale_parts.append(f"- {direction}\n")
    rationale_parts.append(
        f"- LDO IS hit-rate composition (iter-v3/029): "
        f"%TP={ldo_pct_tp:.1f}%, %SL={ldo_pct_sl:.1f}%, %TIMEOUT={ldo_pct_timeout:.1f}%.\n"
    )
    rationale_parts.append(
        f"- Peer aggregate IS hit-rate composition: "
        f"%TP={peer_pct_tp:.1f}%, %SL={peer_pct_sl:.1f}%, %TIMEOUT={peer_pct_timeout:.1f}%.\n"
    )
    rationale_parts.append(
        f"- Chosen scale = {chosen_scale}× brings LDO/peer effective TP barrier "
        f"ratio to {closest_row['ldo_to_peer_tp_ratio']:.4f} (closest to 1.0 in "
        "the candidate grid). This aligns LDO's effective triple-barrier "
        "geometry with the peer regime that has been profitable across 9 "
        "iterations.\n"
    )
    rationale_parts.append(
        "- The chosen multipliers DO NOT alter BCH/TRX/ALGO labels — they "
        "fall through `atr_multipliers_for_symbol()` to the default (2.0, 1.0), "
        "preserving iter-v3/029 bit-identity for those 3 symbols.\n"
    )
    rationale = "".join(rationale_parts)

    write_synthesis(
        distribution=distribution,
        is_pattern=is_pattern,
        oos_pattern=oos_pattern,
        recommendation=recommendation,
        candidate_grid=candidate_grid,
        chosen_atr_tp=chosen_atr_tp,
        chosen_atr_sl=chosen_atr_sl,
        chosen_scale=chosen_scale,
        rationale=rationale,
    )
    print(
        f"[iter-v3/032 EDA] Chosen LDO ATR multipliers: ({chosen_atr_tp:.4f}, "
        f"{chosen_atr_sl:.4f}); scale={chosen_scale:.4f}×"
    )
    print(f"  wrote synthesis.md")


if __name__ == "__main__":
    main()

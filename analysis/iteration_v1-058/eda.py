"""EDA — iter-v1/058: btc_oi_delta_5_z30 IS-only analysis on BTCUSDT.

Produces (IS data only — never touches OOS):
  1. Distribution statistics: mean, std, p1, p25, p50, p75, p99, min, max.
  2. ADF stationarity test (raw alpha=0.05, constant + no-trend specification).
  3. Pearson IC vs each of the 48 peer features in V1_FEATURE_COLUMNS_PRUNED.
  4. Summary CSV written to analysis/iteration_v1-058/eda_results.csv.

The CSV has one row per metric/peer. Columns: metric, value, pass_fail.
Sections: DIST_STATS, ADF, IC_vs_<feature_name>.

Grep-clean: no OOS data loaded, no OOS cutoff bypassed.

Run:
    cd /home/roberto/crypto-trade/.worktrees/quant-research
    uv run python analysis/iteration_v1-058/eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00 UTC — IS ends here (sacred)
TARGET_FEATURE: str = "btc_oi_delta_5_z30"

# Parquet path (legacy features dir holds the most recent BTC parquet)
PARQUET_PATH = Path("data/features/BTCUSDT_8h_features.parquet")

OUTPUT_CSV = Path("analysis/iteration_v1-058/eda_results.csv")

# Peer features: all V1_FEATURE_COLUMNS_PRUNED except the target itself
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED  # noqa: E402

PEER_FEATURES: list[str] = [f for f in V1_FEATURE_COLUMNS_PRUNED if f != TARGET_FEATURE]
assert len(PEER_FEATURES) == 48, f"Expected 48 peers; got {len(PEER_FEATURES)}"

# IC thresholds (from brief Section 2.5 and prior precedents)
IC_BLOCK_THRESHOLD: float = 0.80  # blocks regardless of feature (sister IC gate)
IC_WARN_THRESHOLD: float = 0.60  # warn-only for non-volume peers
IC_VOL_BLOCK_THRESHOLD: float = 0.60  # hard block for vol_volume_rel_20 (/048 precedent)

# ADF: constant + no-trend (trend-stationary features are acceptable per prior precedents)
ADF_ALPHA: float = 0.05


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_is_parquet() -> pd.DataFrame:
    """Load BTC parquet, restrict to IS window, return IS-only rows."""
    if not PARQUET_PATH.exists():
        raise FileNotFoundError(
            f"Parquet not found: {PARQUET_PATH}\n"
            "Run: uv run crypto-trade features --symbols BTCUSDT --interval 8h "
            "--track v1 --format parquet first."
        )
    df = pd.read_parquet(PARQUET_PATH)
    if "open_time" not in df.columns:
        raise KeyError("Parquet missing 'open_time' column.")
    df = df[df["open_time"] < IS_CUTOFF_MS].copy()
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def adf_test(series: pd.Series) -> dict[str, float | bool]:
    """Run ADF test (constant, no trend). Return stat, p-value, stationary flag."""
    clean = series.dropna()
    from statsmodels.tsa.stattools import adfuller  # type: ignore[import]

    result = adfuller(clean, regression="c", autolag="AIC")
    adf_stat: float = float(result[0])
    p_value: float = float(result[1])
    stationary: bool = p_value < ADF_ALPHA
    return {"adf_stat": adf_stat, "p_value": p_value, "stationary": stationary}


def pearson_ic(a: pd.Series, b: pd.Series) -> float:
    """Pearson IC on pairwise non-NaN rows."""
    mask = a.notna() & b.notna()
    if mask.sum() < 30:
        return float("nan")
    return float(a[mask].corr(b[mask]))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 72)
    print(f"iter-v1/058 EDA — {TARGET_FEATURE} IS-only on BTCUSDT")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Load IS data
    # ------------------------------------------------------------------
    df = load_is_parquet()
    n_total = len(df)
    print(f"\n[Data] IS rows loaded: {n_total}")
    print(f"[Data] IS window: {df['open_time'].iloc[0]} → {df['open_time'].iloc[-1]}")

    if TARGET_FEATURE not in df.columns:
        raise KeyError(
            f"Target feature '{TARGET_FEATURE}' not found in parquet. "
            "Regenerate parquet after the /058 feature addition."
        )

    target = df[TARGET_FEATURE].copy()
    n_valid = target.notna().sum()
    n_nan = target.isna().sum()
    print(f"\n[{TARGET_FEATURE}]")
    print(f"  IS non-NaN rows: {n_valid} / {n_total}")
    print(f"  IS NaN rows    : {n_nan} (burn-in = delta_window=5 + zscore_window=30 = 35 expected)")

    rows: list[dict[str, object]] = []

    # ------------------------------------------------------------------
    # 2. Distribution statistics
    # ------------------------------------------------------------------
    print("\n--- Distribution Statistics ---")
    valid = target.dropna()
    dist = {
        "mean": float(valid.mean()),
        "std": float(valid.std()),
        "min": float(valid.min()),
        "p1": float(np.percentile(valid, 1)),
        "p25": float(np.percentile(valid, 25)),
        "p50": float(np.percentile(valid, 50)),
        "p75": float(np.percentile(valid, 75)),
        "p99": float(np.percentile(valid, 99)),
        "max": float(valid.max()),
        "n_valid": int(n_valid),
        "n_nan": int(n_nan),
    }
    for k, v in dist.items():
        label = f"  {k:10s} = {v:.4f}" if isinstance(v, float) else f"  {k:10s} = {v}"
        print(label)

    p99_abs = max(abs(dist["p1"]), abs(dist["p99"]))
    fat_tail = p99_abs > 4.0
    if fat_tail:
        print(f"  WARNING: |p99_abs| = {p99_abs:.2f} > 4.0 — fat-tail (RF-1 lgbm_advisor)")
    else:
        print(f"  OK: |p99_abs| = {p99_abs:.2f} <= 4.0 (no fat-tail concern)")

    for k, v in dist.items():
        rows.append(
            {
                "section": "DIST_STATS",
                "metric": k,
                "value": v,
                "pass_fail": "INFO",
            }
        )
    rows.append(
        {
            "section": "DIST_STATS",
            "metric": "fat_tail_flag",
            "value": int(fat_tail),
            "pass_fail": "WARN" if fat_tail else "PASS",
        }
    )

    # ------------------------------------------------------------------
    # 3. ADF stationarity test
    # ------------------------------------------------------------------
    print("\n--- ADF Stationarity Test (constant, no trend; alpha=0.05) ---")
    try:
        adf_result = adf_test(target)
        adf_stat = adf_result["adf_stat"]
        adf_p = adf_result["p_value"]
        adf_stationary = adf_result["stationary"]
        print(f"  ADF statistic : {adf_stat:.4f}")
        print(f"  p-value       : {adf_p:.4f}")
        stat_label = "PASS" if adf_stationary else "FAIL — non-stationary"
        print(f"  Stationary    : {adf_stationary} ({stat_label})")
        rows.append(
            {
                "section": "ADF",
                "metric": "adf_stat",
                "value": adf_stat,
                "pass_fail": "INFO",
            }
        )
        rows.append(
            {
                "section": "ADF",
                "metric": "p_value",
                "value": adf_p,
                "pass_fail": "INFO",
            }
        )
        rows.append(
            {
                "section": "ADF",
                "metric": "stationary",
                "value": int(adf_stationary),
                "pass_fail": "PASS" if adf_stationary else "FAIL",
            }
        )
    except ImportError:
        print("  SKIP: statsmodels not installed — ADF skipped")
        _nan = float("nan")
        rows.append({"section": "ADF", "metric": "adf_stat", "value": _nan, "pass_fail": "SKIP"})
        rows.append({"section": "ADF", "metric": "p_value", "value": _nan, "pass_fail": "SKIP"})
        rows.append({"section": "ADF", "metric": "stationary", "value": _nan, "pass_fail": "SKIP"})

    # ------------------------------------------------------------------
    # 4. Pearson IC vs 48 peer features
    # ------------------------------------------------------------------
    print("\n--- Pearson IC vs 48 peer features (IS only) ---")
    print(f"  Block threshold (sister)    : |IC| >= {IC_BLOCK_THRESHOLD}")
    print(f"  Block threshold (vol_vol)   : |IC| >= {IC_VOL_BLOCK_THRESHOLD} [/048 precedent]")
    print(f"  Warn threshold (others)     : |IC| >= {IC_WARN_THRESHOLD}")

    ic_results: list[tuple[str, float, str]] = []
    for peer in PEER_FEATURES:
        if peer not in df.columns:
            ic_val = float("nan")
            status = "SKIP_MISSING"
        else:
            ic_val = pearson_ic(target, df[peer])
            ic_abs = abs(ic_val) if not np.isnan(ic_val) else 0.0
            if peer == "vol_volume_rel_20":
                # /048 precedent: hard block at 0.60
                if ic_abs >= IC_VOL_BLOCK_THRESHOLD:
                    status = "BLOCK_VOL"
                elif ic_abs >= 0.30:
                    status = "WARN"
                else:
                    status = "PASS"
            elif ic_abs >= IC_BLOCK_THRESHOLD:
                status = "BLOCK"
            elif ic_abs >= IC_WARN_THRESHOLD:
                status = "WARN"
            else:
                status = "PASS"
        ic_results.append((peer, ic_val, status))

    # Sort by |IC| descending for printing
    ic_results_sorted = sorted(
        ic_results,
        key=lambda x: abs(x[1]) if not np.isnan(x[1]) else 0.0,
        reverse=True,
    )

    # Top 10 by |IC|
    print("\n  Top-10 by |IC| (descending):")
    for rank, (peer, ic_val, status) in enumerate(ic_results_sorted[:10], start=1):
        flag = f"  [{status}]" if status not in ("PASS", "INFO") else ""
        ic_str = f"{ic_val:+.4f}" if not np.isnan(ic_val) else "  nan"
        print(f"    {rank:2d}. {peer:<35s} IC={ic_str}{flag}")

    # Sister feature special report
    sister = "oi_delta_30_z90"
    sister_ic = next(ic for name, ic, _ in ic_results if name == sister)
    print(f"\n  Sister feature oi_delta_30_z90 IC = {sister_ic:+.4f}")
    if abs(sister_ic) < 0.55:
        print("    PASS: within LM Master estimate |IC| ≈ 0.30-0.55")
    elif abs(sister_ic) < IC_BLOCK_THRESHOLD:
        print(f"    NOTE: |IC| in [0.55, {IC_BLOCK_THRESHOLD}) — moderate overlap; informational")
    else:
        print(f"    BLOCK: |IC| >= {IC_BLOCK_THRESHOLD} — sister-correlation blocks iteration")

    # Block/warn summary
    blocks = [(p, ic, s) for p, ic, s in ic_results if "BLOCK" in s]
    warns = [(p, ic, s) for p, ic, s in ic_results if s == "WARN"]
    if blocks:
        print(f"\n  BLOCKS ({len(blocks)}): {[(p, f'{ic:.4f}') for p, ic, _ in blocks]}")
    else:
        print(f"\n  No IC blocks found (all {len(ic_results)} peers within thresholds).")
    if warns:
        print(f"  Warnings ({len(warns)}): {[(p, f'{ic:.4f}') for p, ic, _ in warns]}")

    # Write IC rows to results
    for rank, (peer, ic_val, status) in enumerate(ic_results_sorted, start=1):
        rows.append(
            {
                "section": "IC_RANK",
                "metric": peer,
                "value": ic_val,
                "pass_fail": status,
            }
        )

    # ------------------------------------------------------------------
    # 5. Write CSV
    # ------------------------------------------------------------------
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame(rows, columns=["section", "metric", "value", "pass_fail"])
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[Output] CSV written: {OUTPUT_CSV} ({len(results_df)} rows)")

    # ------------------------------------------------------------------
    # 6. Final summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("EDA SUMMARY")
    print(f"  IS rows (non-NaN):      {n_valid} / {n_total}")
    _adf_stat_val = adf_result.get("stationary", "N/A") if "adf_result" in dir() else "N/A"
    print(f"  ADF stationary:         {_adf_stat_val}")
    print(f"  Fat-tail flag:          {fat_tail}")
    print(f"  Sister IC (oi_d30_z90): {sister_ic:+.4f}")
    print(f"  IC blocks:              {len(blocks)}")
    print(f"  IC warnings:            {len(warns)}")
    overall = "BLOCK" if blocks else "PASS"
    print(f"  EDA gate:               {overall}")
    print("=" * 72)


if __name__ == "__main__":
    main()

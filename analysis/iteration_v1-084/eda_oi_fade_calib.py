"""iter-v1/084 EDA ADDENDUM — oi_price_divergence_30 distribution + R-FADE fade_z calibration.

Companion to eda_crv_deep.py (which covers mandate items 1-5: trivial-momentum curve,
per-regime, NATR, data-extent, pooled-baseline shape). This script covers items 6-7:

  6. oi_price_divergence_30 feature distribution (IS-only) — the re-aimed /083 OI-family
     signal (rank-7/11 at FIL/083), now applied to CRVUSDT which has the reformed-selector
     NEGATIVE/near-zero trivial baseline (ML headroom). Uses the PRODUCTION past-only
     computation from crypto_trade.features_v1.open_interest_v1.

  7. R-FADE fade_z calibration (IS-only): the gate vetoes an entry when the trade direction
     OPPOSES the OI-divergence sign AND |oi_div| > fade_z. We pre-register fade_z by
     tabulating a per-bar forward-return proxy conditioned on (AGREE vs DISAGREE) x |z|
     buckets. If DISAGREE bars at high |z| have systematically WORSE trade-aligned forward
     returns than AGREE bars, the gate has economic content and the bucket lower-edge
     becomes the pre-registered fade_z. The threshold is FROZEN here BEFORE any OOS read.

Sign convention (MUST match lgbm.py:_apply_oi_divergence_fade_gate, lines 1962-1969):
    oi_div > 0  → sign(OI_delta) > sign(price_ret) → OI building vs price (bullish OI tilt)
    oi_div < 0  → sign(OI_delta) < sign(price_ret) → OI retreating vs price (bearish OI tilt)
    Gate VETOES:  (dir == +1 long  AND oi_div < -fade_z)  -- long contradicted by bearish OI
                  (dir == -1 short AND oi_div > +fade_z)  -- short contradicted by bullish OI
    DISAGREE set := (dir == +1 AND oi_div < 0) OR (dir == -1 AND oi_div > 0).

IS-ONLY DISCIPLINE: every statistic uses only bars with open_time < OOS_CUTOFF_MS.
The OI-divergence feature is computed on the FULL frame so its 120-bar warmup consumes
pre-IS bars (OI cache starts 2021-12-01, ~479 days before IS start) — then sliced to IS.

Usage:
    uv run python analysis/iteration_v1-084/eda_oi_fade_calib.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = int(dt.datetime(2025, 3, 24, tzinfo=dt.UTC).timestamp() * 1000)
IS_START_MS = int(dt.datetime(2023, 3, 24, tzinfo=dt.UTC).timestamp() * 1000)  # OOS_CUTOFF − 24mo
BARS_PER_DAY = 3
FEE = 0.0005
SYMBOL = "CRVUSDT"
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
KLINE_CSV = DATA_DIR / SYMBOL / "8h.csv"
OI_CSV = DATA_DIR / "open_interest" / SYMBOL / "8h.csv"
OUT_CSV = "analysis/iteration_v1-084/eda_oi_fade_calib_results.csv"


def load_full() -> pd.DataFrame:
    df = pd.read_csv(KLINE_CSV)
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        if c in df.columns:
            df[c] = df[c].astype(float)
    df["open_time"] = df["open_time"].astype("int64")
    return df.sort_values("open_time").reset_index(drop=True)


def compute_oi_divergence(df_full: pd.DataFrame) -> pd.Series:
    """Production past-only oi_price_divergence_30 (shift(1) z-score, shift(1) final)."""
    from crypto_trade.features_v1.open_interest_v1 import add_oi_price_divergence_30_feature

    work = df_full.copy()
    work["symbol"] = SYMBOL
    out = add_oi_price_divergence_30_feature(work, data_dir=DATA_DIR)
    return out["oi_price_divergence_30"].reset_index(drop=True)


def main() -> None:
    print("=" * 78)
    print("iter-v1/084 EDA ADDENDUM — oi_price_divergence_30 + R-FADE fade_z (IS-only)")
    print("=" * 78)

    df = load_full()
    # IS-only leak guard
    is_mask = (df["open_time"] >= IS_START_MS) & (df["open_time"] < OOS_CUTOFF_MS)
    assert int((df["open_time"][is_mask] >= OOS_CUTOFF_MS).sum()) == 0, "OOS leak!"

    # OI cache audit
    oi_raw = pd.read_csv(OI_CSV)
    oi_first = int(oi_raw["open_time"].iloc[0])
    print(
        f"\nOI cache: rows={len(oi_raw)} first={oi_first} "
        f"({pd.to_datetime(oi_first, unit='ms', utc=True).date()}) "
        f"covers IS-start({pd.to_datetime(IS_START_MS, unit='ms', utc=True).date()}) "
        f"warmup: {'PASS' if oi_first < IS_START_MS else 'WARN'}"
    )

    # ---- 6. oi_price_divergence_30 distribution -----------------------------
    oi_div = compute_oi_divergence(df)
    oi_div_is = oi_div[is_mask.values].reset_index(drop=True)
    n_is = int(is_mask.sum())
    n_nan = int(oi_div_is.isna().sum())
    print("\n[6] oi_price_divergence_30 FEATURE DISTRIBUTION (IS-only)")
    print(f"    IS rows={n_is}  NaN={n_nan} ({100.0 * n_nan / max(n_is, 1):.2f}%)")
    valid = oi_div_is.dropna()
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    dpct = {f"p{p}": round(float(np.percentile(valid, p)), 4) for p in pcts}
    print(
        f"    mean={valid.mean():+.4f}  std={valid.std(ddof=1):.4f}  "
        f"nonzero={int((valid.abs() > 1e-9).sum())} ({100.0 * (valid.abs() > 1e-9).mean():.1f}%)"
    )
    print(f"    percentiles: {dpct}")
    frac_15 = float((valid.abs() > 1.5).mean())
    frac_20 = float((valid.abs() > 2.0).mean())
    frac_25 = float((valid.abs() > 2.5).mean())
    print(
        f"    |z|>1.5 frac={frac_15:.4f}   |z|>2.0 frac={frac_20:.4f}   |z|>2.5 frac={frac_25:.4f}"
    )
    print("    → gate-eligible bar frac at each candidate fade_z (entries only fire on a")
    print("      subset of these — actual veto rate is far lower).")

    # ---- 7. R-FADE fade_z calibration ---------------------------------------
    # IS-only frame aligned to oi_div_is.
    df_is = df[is_mask.values].reset_index(drop=True)
    close = df_is["close"]
    log_close = np.log(close)
    fwd = log_close.shift(-1) - log_close  # bar t → t+1 log-return
    nb = 21 * BARS_PER_DAY
    pos = np.sign(close / close.shift(nb) - 1.0).fillna(0.0)  # 21d trivial direction proxy

    cal = pd.DataFrame({"pos": pos.values, "oi": oi_div_is.values, "fwd": fwd.values})
    cal = cal[(cal["pos"] != 0) & cal["oi"].notna() & cal["fwd"].notna()].copy()
    cal["trade_fwd"] = cal["pos"] * cal["fwd"]  # signed (long earns +fwd, short −fwd)
    cal["disagree"] = ((cal["pos"] == 1) & (cal["oi"] < 0)) | ((cal["pos"] == -1) & (cal["oi"] > 0))
    cal["abs_z"] = cal["oi"].abs()

    print("\n[7] R-FADE fade_z CALIBRATION (21d-trivial proxy direction, IS-only)")
    print(f"    {'bucket':<10}{'set':<10}{'n':>6}{'mean_trade_fwd_bps':>22}")
    rows = []
    buckets = [
        (0.0, 1.0, "|z|<1.0"),
        (1.0, 1.5, "1.0-1.5"),
        (1.5, 2.0, "1.5-2.0"),
        (2.0, 2.5, "2.0-2.5"),
        (2.5, 1e9, "|z|>=2.5"),
    ]
    for lo, hi, lbl in buckets:
        for dis in (False, True):
            m = (cal["abs_z"] >= lo) & (cal["abs_z"] < hi) & (cal["disagree"] == dis)
            sub = cal[m]
            mean_bps = round(float(sub["trade_fwd"].mean()) * 1e4, 2) if len(sub) else float("nan")
            setname = "DISAGREE" if dis else "AGREE"
            print(f"    {lbl:<10}{setname:<10}{len(sub):>6}{mean_bps:>22}")
            rows.append(
                {"bucket": lbl, "set": setname, "n": int(len(sub)), "mean_trade_fwd_bps": mean_bps}
            )

    res = pd.DataFrame(rows)
    res.to_csv(OUT_CSV, index=False)

    # Pre-registration decision: find lowest |z| bucket where DISAGREE < AGREE by >= 5bps.
    pivot = res.pivot_table(index="bucket", columns="set", values="mean_trade_fwd_bps")
    pivot = pivot.reindex([b[2] for b in buckets])
    print("\n    DISAGREE-minus-AGREE forward-return (bps) by bucket:")
    chosen = None
    for lbl in [b[2] for b in buckets if b[0] >= 1.5]:
        if lbl in pivot.index and {"AGREE", "DISAGREE"}.issubset(pivot.columns):
            d = pivot.loc[lbl, "DISAGREE"]
            a = pivot.loc[lbl, "AGREE"]
            if pd.notna(d) and pd.notna(a):
                gap = d - a
                print(f"      {lbl}: DISAGREE−AGREE = {gap:+.2f} bps")
                if gap <= -5.0 and chosen is None:
                    chosen = lbl
    # Map first qualifying bucket lower-edge to fade_z; default to 2.0 if none qualify.
    edge_map = {"1.5-2.0": 1.5, "2.0-2.5": 2.0, "|z|>=2.5": 2.5}
    fade_z = edge_map.get(chosen, 2.0) if chosen else 2.0
    print(
        f"\n    PRE-REGISTERED fade_z = {fade_z:.1f}  "
        f"(band 1.5-2.5; default 2.0 if no bucket shows >=5bps DISAGREE penalty)"
    )
    print(f"    Results saved to {OUT_CSV}")
    print("=" * 78)


if __name__ == "__main__":
    main()

"""iter-v3/104 — diagnostic deepening: does the on-chain signal survive at
its NATIVE daily resolution, and is there a regime-conditioned sub-signal?

Two follow-up questions the primary EDA (`onchain_is_eda.py`) raises:

  Q1. The on-chain daily metric forward-fills onto the 8h grid — 3 consecutive
      8h bars carry an identical on-chain value. The 8h-grid IC could therefore
      be diluted by the 21-candle (7-day) label window straddling on-chain days
      that all carry the same stale value. Re-test the IC using ONE observation
      per UTC day (the first 8h bar of each day) — the strongest, least-diluted
      possible read of an on-chain → forward-return relationship.

  Q2. A regime feature can be INERT as a flat input yet useful CONDITIONALLY.
      Test whether the sign of `btc_adract_growth_14d_z90` (BTC network demand
      expanding vs contracting) splits forward returns: i.e. is mean fwd_signed
      meaningfully different in the top-tercile vs bottom-tercile of the
      on-chain z-score? This is the last path that could rescue the source as a
      regime gate rather than a raw feature.

IS-ONLY: every row has open_time < OOS_CUTOFF_MS. The post-cutoff OOS is never
read. This is a diagnostic supplement to the primary EDA; same look-ahead
discipline (the on-chain feature carries a +1-day publication lag, built in
`onchain_is_eda.attach_onchain`).

Output: analysis/iteration_v3-104/T7_daily_resolution_and_regime.csv
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from onchain_is_eda import (  # noqa: E402
    FEAT_DIR,
    INCUMBENTS,
    KLINE_DIR,
    OOS_CUTOFF_MS,
    OWN_CHAIN,
    SYMBOLS,
    attach_onchain,
    build_daily_features,
    label_panel,
)

OUT = Path(__file__).resolve().parent


def main() -> int:
    daily_btc = build_daily_features("btc")
    daily_by_asset = {
        "btc": daily_btc,
        "bch": build_daily_features("bch"),
        "trx": build_daily_features("trx"),
    }
    btc_cands = ["btc_adract_growth_14d_z90", "btc_txcnt_growth_14d_z90"]

    rows = []
    for sym in SYMBOLS:
        kl = pd.read_csv(KLINE_DIR / sym / "8h.csv")
        feat = pd.read_parquet(FEAT_DIR / f"{sym}_8h_features.parquet")
        feat_cols = ["open_time"] + [c for c in INCUMBENTS if c in feat.columns]
        kl = kl.merge(feat[feat_cols], on="open_time", how="left")

        feeds = [daily_btc]
        own = OWN_CHAIN[sym]
        if own is not None:
            feeds.append(daily_by_asset[own])
        kl_oc = attach_onchain(kl, feeds)
        lab = label_panel(kl, sym)
        kl_oc = kl_oc.merge(lab[["open_time", "fwd_signed"]], on="open_time", how="left")

        is_panel = kl_oc.loc[kl_oc["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        # Native-daily view: keep the FIRST 8h bar of each UTC day.
        is_panel["_day"] = pd.to_datetime(
            is_panel["open_time"], unit="ms"
        ).dt.normalize()
        daily_view = is_panel.groupby("_day", as_index=False).first()

        sym_cands = list(btc_cands)
        if own is not None:
            sym_cands += [f"{own}_adract_growth_14d_z90",
                          f"{own}_txcnt_growth_14d_z90"]

        for c in sym_cands:
            # Q1 — daily-resolution IC.
            sub = daily_view[[c, "fwd_signed"]].dropna()
            if len(sub) < 80:
                ic_d, p_d = np.nan, np.nan
            else:
                ic_d, p_d = spearmanr(sub[c], sub["fwd_signed"])
            # 8h-grid IC for direct comparison.
            sub8 = is_panel[[c, "fwd_signed"]].dropna()
            ic_8, _ = spearmanr(sub8[c], sub8["fwd_signed"])

            # Q2 — regime split: top vs bottom tercile of the on-chain z-score.
            sub_r = is_panel[[c, "fwd_signed"]].dropna()
            q_lo, q_hi = sub_r[c].quantile([1 / 3, 2 / 3])
            lo = sub_r.loc[sub_r[c] <= q_lo, "fwd_signed"]
            hi = sub_r.loc[sub_r[c] >= q_hi, "fwd_signed"]
            if len(lo) >= 30 and len(hi) >= 30:
                u_p = mannwhitneyu(hi, lo, alternative="two-sided")[1]
                mean_gap = float(hi.mean() - lo.mean())
            else:
                u_p, mean_gap = np.nan, np.nan

            rows.append({
                "symbol": sym,
                "candidate": c,
                "n_daily": len(sub),
                "ic_8h_grid": round(float(ic_8), 5) if ic_8 == ic_8 else np.nan,
                "ic_daily_native": round(float(ic_d), 5) if ic_d == ic_d else np.nan,
                "ic_daily_pvalue": round(float(p_d), 4) if p_d == p_d else np.nan,
                "regime_topbot_mean_gap_pct": (
                    round(mean_gap, 4) if mean_gap == mean_gap else np.nan
                ),
                "regime_split_mw_pvalue": (
                    round(float(u_p), 4) if u_p == u_p else np.nan
                ),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T7_daily_resolution_and_regime.csv", index=False)
    print("=== T7 daily-resolution IC + regime-split diagnostic ===")
    print(df.to_string(index=False))

    n = len(df)
    sig_daily = int((df["ic_daily_pvalue"] < 0.05).sum())
    sig_regime = int((df["regime_split_mw_pvalue"] < 0.05).sum())
    print(
        f"\nSummary: {n} (symbol x candidate) cells. "
        f"daily-IC significant @p<0.05: {sig_daily}/{n}. "
        f"regime-split significant @p<0.05: {sig_regime}/{n}."
    )
    print(
        "Bonferroni note: 10 cells -> family-wise p<0.05 needs per-cell "
        "p<0.005. With both screens that bar is the honest threshold."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

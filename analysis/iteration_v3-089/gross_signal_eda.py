"""iter-v3/089 — Gross-signal strengthening EDA (IS-ONLY).

The companion to turnover_construction_eda.py.  That EDA established the
HONEST verdict: the corrected-sign + quantile + slower-rebalance + no-trade-band
construction CUTS the IS net loss roughly in half (E1 -0.65 -> E5 -0.31) but
does NOT reach a positive IS net Sharpe — because the gross signal is too thin
(corrected-sign IS gross monthly Sharpe is only +0.05 to +0.10).  Per the /088
closeout's honest senior read, the gross signal itself needs strengthening.

This EDA quantifies — ON IS DATA ONLY — which gross-signal lever lifts the
realised long-short spread the most, so /089's brief can decide what /089
carries vs defers to /090.  It does NOT re-train a model (that is the Phase-6
build); it works on the model-free predictor structure, the same way the /088
EDA T3/T4/T7 did, but focused on the GROSS-SPREAD levers:

  G1  HORIZON x QUANTILE grid — the realised top-vs-bottom quantile L-S spread
      and its per-snapshot Sharpe, across forward horizon H in {3,6,9,12} and
      quantile in {tercile, quartile, quintile, decile}.  The /088 EDA picked
      H=3 by strongest |rank-IC|; G1 asks the DIFFERENT question — which
      (H, quantile) maximises the realised SPREAD SHARPE (the economic edge),
      because a longer H also turns over proportionally less.
  G2  SCORE-WEIGHTED vs EQUAL-WEIGHTED legs — within the chosen quantile, does
      weighting each name by its rank-distance from the median (conviction
      weighting) lift the L-S spread vs equal-weighting?  Poh/Lim/Zohren note
      LTR precision concentrates in the tails; conviction weighting exploits it.
  G3  CROSS-SECTIONAL Z-SCORE vs RANK normalisation — the /088 panel uses a
      cross-sectional RANK transform of each feature.  G3 tests whether a
      cross-sectional Z-SCORE transform (which preserves magnitude information
      a rank discards) produces a stronger composite predictor IC.
  G4  FEATURE-SET headroom — the equal-weight composite IC of the /088
      13-feature stack vs a CROSS-SECTIONALLY-EXPANDED candidate set (adding
      cross-sectional momentum / reversal channels at multiple lookbacks that
      the per-symbol architecture's feature set never carried as separate
      cross-sectional predictors).  Quantifies whether a feature expansion is
      a /089 or a /090 lever.

NO-CHEATING: every table is computed on IS rows only (open_time <
OOS_CUTOFF_MS).  The horizon, quantile, weighting and normalisation are
evaluated on IS data; OOS is never read.  Sign-alignment in the composite
uses the SAME IS rank-IC (IS data only).  Outputs are CSVs.

Run: uv run python analysis/iteration_v3-089/gross_signal_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))

OOS_CUTOFF_MS = 1742774400000  # IMMUTABLE — 2025-03-24

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N  # noqa: E402
from crypto_trade.strategies.ml.cross_sectional import XS_UNIVERSE  # noqa: E402

FEATURES_DIR = REPO / "data" / "features_v3"
MIN_XS = 6  # minimum cross-section width
PAST_WIN = 12  # the 12-bar trailing-return predictor (the /088 EDA convention)

# /088 13-feature cross-sectional stack (anchor minus btc_ret_14d).
ANCHOR_13 = [c for c in V3_FEATURE_COLUMNS_TOP_N if c != "btc_ret_14d"]


def _load_is(symbol: str) -> pd.DataFrame | None:
    p = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    df = df[df["open_time"] < OOS_CUTOFF_MS].sort_values("open_time").reset_index(drop=True)
    # 60-day (180-bar) listing burn-in — the /088 convention.
    if len(df) > 180:
        df = df.iloc[180:].reset_index(drop=True)
    return df


def _fwd_ret(close: pd.Series, h: int) -> pd.Series:
    return close.shift(-h) / close - 1.0


def main() -> None:
    print("=" * 74)
    print("iter-v3/089 gross-signal strengthening EDA — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print("=" * 74)

    panels: dict[str, pd.DataFrame] = {}
    for sym in XS_UNIVERSE:
        df = _load_is(sym)
        if df is None or len(df) < 200:
            print(f"  {sym}: SKIP")
            continue
        df = df.set_index("open_time")
        df["past_ret_12"] = df["close"] / df["close"].shift(PAST_WIN) - 1.0
        panels[sym] = df
    print(f"\nLoaded {len(panels)} IS panels.\n")
    all_ts = sorted(set().union(*[set(p.index) for p in panels.values()]))

    # ====================================================================
    # G1 — HORIZON x QUANTILE realised L-S spread Sharpe
    # ====================================================================
    horizons = [3, 6, 9, 12]
    quantiles = [("tercile", 1 / 3), ("quartile", 0.25), ("quintile", 0.20), ("decile", 0.10)]
    for h in horizons:
        for sym, p in panels.items():
            p[f"fwd_{h}"] = _fwd_ret(p["close"], h)
    g1_rows = []
    for h in horizons:
        for qname, qfrac in quantiles:
            spreads: list[float] = []
            for ts in all_ts:
                recs = []
                for sym, p in panels.items():
                    if ts not in p.index:
                        continue
                    r = p.loc[ts]
                    if pd.notna(r["past_ret_12"]) and pd.notna(r[f"fwd_{h}"]):
                        recs.append((float(r["past_ret_12"]), float(r[f"fwd_{h}"])))
                if len(recs) < max(MIN_XS, int(np.ceil(1 / qfrac)) + 1):
                    continue
                recs.sort(key=lambda x: x[0])  # ascending past return
                n = len(recs)
                nq = max(1, int(np.floor(n * qfrac)))
                # reversal book: long recent LOSERS (bottom), short recent WINNERS (top)
                lo = np.mean([r[1] for r in recs[:nq]])
                hi = np.mean([r[1] for r in recs[-nq:]])
                spreads.append(lo - hi)  # reversal: bottom-minus-top
            sa = np.array(spreads)
            # PER-BAR spread Sharpe normalised to a common 1-day basis: a longer
            # horizon spread spans h bars, so divide by sqrt(h) for comparability.
            mean_sp = float(sa.mean()) if len(sa) else float("nan")
            std_sp = float(sa.std(ddof=1)) if len(sa) > 1 else float("nan")
            sharpe = mean_sp / std_sp if std_sp and std_sp > 0 else float("nan")
            sharpe_per_bar = sharpe / np.sqrt(h) if not np.isnan(sharpe) else float("nan")
            g1_rows.append(
                {
                    "fwd_horizon_bars": h,
                    "quantile": qname,
                    "quantile_frac": round(qfrac, 4),
                    "n_snapshots": len(sa),
                    "mean_reversal_spread": round(mean_sp, 6),
                    "spread_sharpe_raw": round(sharpe, 4),
                    "spread_sharpe_per_bar_eq": round(sharpe_per_bar, 4),
                }
            )
    g1 = pd.DataFrame(g1_rows)
    g1.to_csv(OUT / "G1_horizon_quantile_spread.csv", index=False)
    print("G1 — horizon x quantile realised reversal L-S spread:")
    print(g1.to_string(index=False))
    best_g1 = g1.loc[g1["spread_sharpe_per_bar_eq"].abs().idxmax()]
    print(
        f"\n  -> strongest per-bar-equivalent spread Sharpe: H={int(best_g1['fwd_horizon_bars'])}, "
        f"{best_g1['quantile']} (Sharpe/bar {best_g1['spread_sharpe_per_bar_eq']})\n"
    )

    # ====================================================================
    # G2 — SCORE-WEIGHTED vs EQUAL-WEIGHTED legs (at H=3, quintile)
    # ====================================================================
    h_g2 = 3
    for sym, p in panels.items():
        if f"fwd_{h_g2}" not in p.columns:
            p[f"fwd_{h_g2}"] = _fwd_ret(p["close"], h_g2)
    g2_rows = []
    for qname, qfrac in [("quartile", 0.25), ("quintile", 0.20)]:
        eq_spreads, cw_spreads = [], []
        for ts in all_ts:
            recs = []
            for sym, p in panels.items():
                if ts not in p.index:
                    continue
                r = p.loc[ts]
                if pd.notna(r["past_ret_12"]) and pd.notna(r[f"fwd_{h_g2}"]):
                    recs.append((float(r["past_ret_12"]), float(r[f"fwd_{h_g2}"])))
            if len(recs) < max(MIN_XS, int(np.ceil(1 / qfrac)) + 1):
                continue
            recs.sort(key=lambda x: x[0])
            n = len(recs)
            nq = max(1, int(np.floor(n * qfrac)))
            bot = recs[:nq]  # losers -> LONG
            top = recs[-nq:]  # winners -> SHORT
            # equal-weight
            eq = np.mean([r[1] for r in bot]) - np.mean([r[1] for r in top])
            eq_spreads.append(eq)
            # conviction-weight: weight by rank-distance from the universe median.
            # bottom leg: rank 0..nq-1 from the extreme; weight = (nq - i).
            wb = np.array([nq - i for i in range(nq)], dtype=float)
            wb /= wb.sum()
            wt = np.array([nq - i for i in range(nq)], dtype=float)
            wt /= wt.sum()
            cw_long = np.sum(wb * np.array([r[1] for r in bot]))
            cw_short = np.sum(wt * np.array([r[1] for r in top[::-1]]))
            cw_spreads.append(cw_long - cw_short)
        ea, ca = np.array(eq_spreads), np.array(cw_spreads)
        g2_rows.append(
            {
                "quantile": qname,
                "n_snapshots": len(ea),
                "equalweight_spread_sharpe": round(
                    float(ea.mean() / ea.std(ddof=1)) if ea.std(ddof=1) > 0 else float("nan"), 4
                ),
                "convictionweight_spread_sharpe": round(
                    float(ca.mean() / ca.std(ddof=1)) if ca.std(ddof=1) > 0 else float("nan"), 4
                ),
            }
        )
    g2 = pd.DataFrame(g2_rows)
    g2.to_csv(OUT / "G2_score_weighting.csv", index=False)
    print("G2 — equal-weight vs conviction-weight legs (H=3):")
    print(g2.to_string(index=False))
    print()

    # ====================================================================
    # G3 — cross-sectional Z-SCORE vs RANK normalisation of the composite
    # ====================================================================
    h_g3 = 3
    g3_rank_ic, g3_z_ic = [], []
    # per-feature IS rank-IC for sign alignment
    feat_ic: dict[str, float] = {}
    for f in ANCHOR_13:
        ics = []
        for ts in all_ts:
            vals, fwds = [], []
            for sym, p in panels.items():
                if ts not in p.index or f not in p.columns:
                    continue
                r = p.loc[ts]
                if pd.notna(r[f]) and pd.notna(r[f"fwd_{h_g3}"]):
                    vals.append(float(r[f]))
                    fwds.append(float(r[f"fwd_{h_g3}"]))
            if len(vals) < MIN_XS:
                continue
            ic = pd.Series(vals).rank().corr(pd.Series(fwds).rank())
            if pd.notna(ic):
                ics.append(ic)
        feat_ic[f] = float(np.mean(ics)) if ics else 0.0
    sign = {f: (1.0 if feat_ic[f] >= 0 else -1.0) for f in ANCHOR_13}

    for ts in all_ts:
        recs = []
        for sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r[f"fwd_{h_g3}"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in ANCHOR_13):
                continue
            recs.append(r)
        if len(recs) < MIN_XS:
            continue
        fwds = pd.Series([float(r[f"fwd_{h_g3}"]) for r in recs])
        rank_comp = np.zeros(len(recs))
        z_comp = np.zeros(len(recs))
        for f in ANCHOR_13:
            fv = np.array([float(r[f]) for r in recs])
            rank_comp += sign[f] * pd.Series(fv).rank().to_numpy()
            mu, sd = fv.mean(), fv.std()
            z = (fv - mu) / sd if sd > 1e-12 else np.zeros(len(fv))
            z_comp += sign[f] * z
        ic_r = pd.Series(rank_comp).rank().corr(fwds.rank())
        ic_z = pd.Series(z_comp).rank().corr(fwds.rank())
        if pd.notna(ic_r):
            g3_rank_ic.append(float(ic_r))
        if pd.notna(ic_z):
            g3_z_ic.append(float(ic_z))
    ra, za = np.array(g3_rank_ic), np.array(g3_z_ic)
    g3 = pd.DataFrame(
        [
            {
                "normalization": "cross_sectional_rank",
                "n_snapshots": len(ra),
                "mean_rank_ic": round(float(ra.mean()), 5),
                "ic_ir": round(float(ra.mean() / ra.std(ddof=1)) if ra.std(ddof=1) > 0 else 0.0, 4),
            },
            {
                "normalization": "cross_sectional_zscore",
                "n_snapshots": len(za),
                "mean_rank_ic": round(float(za.mean()), 5),
                "ic_ir": round(float(za.mean() / za.std(ddof=1)) if za.std(ddof=1) > 0 else 0.0, 4),
            },
        ]
    )
    g3.to_csv(OUT / "G3_normalization.csv", index=False)
    print("G3 — cross-sectional rank vs z-score normalisation of the 13-feat composite:")
    print(g3.to_string(index=False))
    print()

    # ====================================================================
    # G4 — feature-set headroom: 13-feat composite vs +cross-sectional
    #      momentum/reversal multi-lookback channels
    # ====================================================================
    h_g4 = 3
    # cross-sectional reversal/momentum channels at multiple lookbacks — these
    # are predictors the per-symbol architecture never carried as separate
    # cross-sectional features (it had btc_ret_14d only).  Built from close.
    xs_lookbacks = [3, 6, 12, 24, 48]
    for sym, p in panels.items():
        for lb in xs_lookbacks:
            p[f"xsret_{lb}"] = p["close"] / p["close"].shift(lb) - 1.0
    xs_channels = [f"xsret_{lb}" for lb in xs_lookbacks]
    # IS rank-IC of each new channel for sign alignment
    chan_ic: dict[str, float] = {}
    for f in xs_channels:
        ics = []
        for ts in all_ts:
            vals, fwds = [], []
            for sym, p in panels.items():
                if ts not in p.index:
                    continue
                r = p.loc[ts]
                if pd.notna(r[f]) and pd.notna(r[f"fwd_{h_g4}"]):
                    vals.append(float(r[f]))
                    fwds.append(float(r[f"fwd_{h_g4}"]))
            if len(vals) < MIN_XS:
                continue
            ic = pd.Series(vals).rank().corr(pd.Series(fwds).rank())
            if pd.notna(ic):
                ics.append(ic)
        chan_ic[f] = float(np.mean(ics)) if ics else 0.0
    chan_sign = {f: (1.0 if chan_ic[f] >= 0 else -1.0) for f in xs_channels}

    base_ic, exp_ic = [], []
    for ts in all_ts:
        recs = []
        for sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r[f"fwd_{h_g4}"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in ANCHOR_13):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in xs_channels):
                continue
            recs.append(r)
        if len(recs) < MIN_XS:
            continue
        fwds = pd.Series([float(r[f"fwd_{h_g4}"]) for r in recs])
        base = np.zeros(len(recs))
        for f in ANCHOR_13:
            base += sign[f] * pd.Series([float(r[f]) for r in recs]).rank().to_numpy()
        exp = base.copy()
        for f in xs_channels:
            exp += chan_sign[f] * pd.Series([float(r[f]) for r in recs]).rank().to_numpy()
        ic_b = pd.Series(base).rank().corr(fwds.rank())
        ic_e = pd.Series(exp).rank().corr(fwds.rank())
        if pd.notna(ic_b):
            base_ic.append(float(ic_b))
        if pd.notna(ic_e):
            exp_ic.append(float(ic_e))
    ba, xa = np.array(base_ic), np.array(exp_ic)
    g4 = pd.DataFrame(
        [
            {
                "feature_set": "anchor_13",
                "n_snapshots": len(ba),
                "mean_rank_ic": round(float(ba.mean()), 5),
                "ic_ir": round(float(ba.mean() / ba.std(ddof=1)) if ba.std(ddof=1) > 0 else 0.0, 4),
                "t_stat": round(
                    float(ba.mean() / (ba.std(ddof=1) / np.sqrt(len(ba))))
                    if len(ba) > 1 and ba.std(ddof=1) > 0
                    else 0.0,
                    2,
                ),
            },
            {
                "feature_set": "anchor_13_plus_5xs_momentum_channels",
                "n_snapshots": len(xa),
                "mean_rank_ic": round(float(xa.mean()), 5),
                "ic_ir": round(float(xa.mean() / xa.std(ddof=1)) if xa.std(ddof=1) > 0 else 0.0, 4),
                "t_stat": round(
                    float(xa.mean() / (xa.std(ddof=1) / np.sqrt(len(xa))))
                    if len(xa) > 1 and xa.std(ddof=1) > 0
                    else 0.0,
                    2,
                ),
            },
        ]
    )
    g4.to_csv(OUT / "G4_feature_set_headroom.csv", index=False)
    # the per-channel IC table too
    pd.DataFrame(
        [{"channel": f, "is_rank_ic": round(chan_ic[f], 5)} for f in xs_channels]
    ).to_csv(OUT / "G4_xs_channel_ic.csv", index=False)
    print("G4 — feature-set headroom (13-feat composite vs +5 cross-sectional momentum channels):")
    print(g4.to_string(index=False))
    print("  per-channel IS rank-IC:")
    for f in xs_channels:
        print(f"    {f}: {chan_ic[f]:+.5f}")

    print("\n" + "=" * 74)
    print("EDA SUMMARY — /089 gross-signal levers, IS data only")
    print("=" * 74)
    print(f"  G1 best (H,quantile) by per-bar spread Sharpe: H={int(best_g1['fwd_horizon_bars'])}, "
          f"{best_g1['quantile']}")
    print("  G2 conviction-weight vs equal-weight: see CSV")
    print(f"  G3 rank vs z-score composite IC: "
          f"{g3.iloc[0]['ic_ir']} vs {g3.iloc[1]['ic_ir']}")
    print(f"  G4 13-feat composite IC-IR {g4.iloc[0]['ic_ir']} vs "
          f"expanded {g4.iloc[1]['ic_ir']}")
    print("  ALL tables IS-only. Horizon/quantile/weighting/features evaluated on IS; OOS unread.")
    print("=" * 74)


if __name__ == "__main__":
    sys.exit(main())

"""iter-v3/090 — Gross-signal-strengthening EDA (IS-ONLY).

The cross-sectional book is GROSS-POSITIVE (iter-v3/089: OOS gross monthly
Sharpe +0.1717) and fails NET only on transaction cost (OOS fees/gross 1.58x).
The /089 closeout + Critic Rec #2 mandate /090 as the GROSS-SIGNAL-strengthening
iteration — grow the +0.17 gross Sharpe enough that, net of the (already
cost-disciplined) fees, the book turns net-positive OOS.

The /089 G4 EDA scoped a "cross-sectional momentum feature expansion" but its
candidate channels (`xsret_lb = close/close.shift(lb) - 1`) are PLAIN trailing
returns — already cross-sectionally rank-normalised in the panel exactly like
the existing 13 features.  Their per-channel IS rank-ICs (-0.03..-0.04) are the
SAME magnitude as the existing stack and the composite IC-IR moved only
0.200 -> 0.204 (+2%).  That is the iter-v3/070 dead-path: marginally-correlated
features steal `colsample_bytree` picks without adding signal.

This EDA does the feature expansion PROPERLY.  Two questions, both IS-only:

  A. THE SHORT-LEG-ASYMMETRY DIAGNOSIS (Critic /089 Rec #3).
     /089's per-leg decomposition: the SHORT leg carries the ENTIRE gross
     spread (OOS short-leg gross +0.1200; long-leg gross -0.0633 — the long
     leg LOSES gross despite longing the model's predicted winners).  A1-A3
     quantify, on IS data, whether the cross-sectional signal in this 22-symbol
     altcoin universe is structurally a DOWNSIDE/SHORT predictor: the realised
     per-tercile forward-return profile, the long-leg vs short-leg realised
     gross spread, and whether the composite predictor's IC is carried by the
     bottom of the cross-section.  This SCOPES /090 (feature expansion) vs /091
     (short-tilt construction) and pre-registers the asymmetry falsifier.

  B. THE MULTIVARIATE-CONTRIBUTION FEATURE EXPANSION (the /090 axis candidate).
     B1-B4 test genuinely DIFFERENT cross-sectional feature families — NOT more
     trailing-return ratios.  Each candidate family is tested for its
     INCREMENTAL multivariate contribution: the IS rank-IC and the realised
     gross long-short spread Sharpe of the 13-feature composite WITH vs WITHOUT
     the family added — the iter-v3/070-correct test (not a univariate Spearman
     rank).  The families researched (Liu-Tsyvinski JoF 2022; Cakici et al.
     IRFA 2024; the crypto cross-sectional ML literature):
       B1  cross-sectional IDIOSYNCRATIC VOLATILITY — IVOL is a documented
           negative cross-sectional crypto predictor (low-IVOL coins
           out-perform).  Residual vol after a market-beta regression.
       B2  cross-sectional DOWNSIDE-RISK channels — semi-deviation, max
           drawdown, downside-beta — direct downside predictors that target
           the SHORT leg the A-block shows carries the alpha.
       B3  cross-sectional LIQUIDITY / SIZE — Amihud illiquidity & dollar
           volume; size/liquidity is a canonical cross-sectional factor.
       B4  the FULL multivariate panel — every B1-B3 family that clears the
           per-family incremental gate, stacked, vs the 13-feature anchor.

NO-CHEATING: every table is computed on IS rows ONLY (open_time <
OOS_CUTOFF_MS = 2025-03-24, with the 60-day/180-bar listing burn-in).  Every
candidate family is built from IS data; OOS is never read.  Sign-alignment of
each predictor in a composite uses the IS rank-IC (IS data only).  The
forward-return target is the H=3 cross-sectional forward return — the same
target the /088 label and the /089 G-EDA use.  Outputs are CSVs committed
alongside this script.

Run: uv run python analysis/iteration_v3-090/gross_signal_expansion_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))

# IMMUTABLE — the v3 sacred constant.  IS = strictly before this ms.
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N  # noqa: E402
from crypto_trade.strategies.ml.cross_sectional import XS_UNIVERSE  # noqa: E402

FEATURES_DIR = REPO / "data" / "features_v3"
MIN_XS = 6  # minimum cross-section width to form a snapshot
BURNIN_BARS = 180  # 60-day listing burn-in — the /088 convention
H = 3  # forward horizon in bars — the /088 label horizon

# the /088 13-feature cross-sectional stack (the /059 anchor minus btc_ret_14d).
ANCHOR_13 = [c for c in V3_FEATURE_COLUMNS_TOP_N if c != "btc_ret_14d"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_is(symbol: str) -> pd.DataFrame | None:
    """Load one symbol's IS feature parquet with the 180-bar listing burn-in."""
    p = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    df = df[df["open_time"] < OOS_CUTOFF_MS].sort_values("open_time").reset_index(drop=True)
    if len(df) > BURNIN_BARS:
        df = df.iloc[BURNIN_BARS:].reset_index(drop=True)
    return df


def _xs_ic(values: list[float], fwds: list[float]) -> float:
    """Spearman rank-IC of one cross-section snapshot."""
    if len(values) < MIN_XS:
        return float("nan")
    ic = pd.Series(values).rank().corr(pd.Series(fwds).rank())
    return float(ic) if pd.notna(ic) else float("nan")


# ---------------------------------------------------------------------------
# Cross-sectional candidate feature construction (all past-only, per-symbol)
# ---------------------------------------------------------------------------


def _engineer_candidates(p: pd.DataFrame) -> pd.DataFrame:
    """Add the /090 candidate cross-sectional feature families to one symbol's
    panel.  Every feature is computed from PAST-ONLY data (rolling windows on
    `close`/`high`/`low`/`volume`, all .shift-safe — the value at bar t uses
    only bars <= t).  Cross-sectional rank-normalisation happens later, per
    timestamp, exactly as the /088 panel builder does.
    """
    close = p["close"].astype(float)
    high = p["high"].astype(float)
    low = p["low"].astype(float)
    vol = p["volume"].astype(float)
    ret_1 = close.pct_change()

    # --- B1: idiosyncratic volatility ------------------------------------
    # Residual volatility after removing the symbol's exposure to BTC.
    # btc_ret_3d is in the feature parquet (a market-return proxy); we form a
    # rolling-window beta of the symbol's 1-bar return on the BTC 1-bar return
    # proxy and take the rolling std of the residual.  Window 50 bars.
    btc_ret_1 = (p["btc_ret_3d"].astype(float) + 1.0) ** (1.0 / 3.0) - 1.0  # ~1-bar BTC ret
    win = 50
    cov = ret_1.rolling(win).cov(btc_ret_1)
    var_b = btc_ret_1.rolling(win).var()
    beta = cov / var_b.replace(0.0, np.nan)
    resid = ret_1 - beta * btc_ret_1
    p["cand_ivol_50"] = resid.rolling(win).std()
    # total realised vol of the same window (for the IVOL-vs-totalvol contrast)
    p["cand_totalvol_50"] = ret_1.rolling(win).std()

    # --- B2: downside-risk channels --------------------------------------
    # semi-deviation: rolling std of NEGATIVE returns only (downside dispersion)
    neg = ret_1.where(ret_1 < 0.0, 0.0)
    p["cand_semidev_50"] = neg.rolling(win).std()
    # downside beta: beta estimated on the bars where the BTC proxy was down
    down_mask = btc_ret_1 < 0.0
    r_d = ret_1.where(down_mask)
    b_d = btc_ret_1.where(down_mask)
    cov_d = r_d.rolling(win, min_periods=15).cov(b_d)
    var_d = b_d.rolling(win, min_periods=15).var()
    p["cand_downbeta_50"] = cov_d / var_d.replace(0.0, np.nan)
    # rolling 50-bar max drawdown of the equity curve (depth of the worst run)
    eq = (1.0 + ret_1.fillna(0.0)).cumprod()
    roll_peak = eq.rolling(win, min_periods=10).max()
    dd = eq / roll_peak - 1.0
    p["cand_maxdd_50"] = dd.rolling(win, min_periods=10).min()
    # Sortino-style downside-scaled momentum: 12-bar return / semi-deviation
    p["cand_sortino_mom_12"] = (close / close.shift(12) - 1.0) / p["cand_semidev_50"].replace(
        0.0, np.nan
    )

    # --- B3: liquidity / size --------------------------------------------
    # Amihud illiquidity: mean over 20 bars of |return| / dollar-volume.
    dollar_vol = (close * vol).replace(0.0, np.nan)
    amihud = (ret_1.abs() / dollar_vol).rolling(20).mean()
    p["cand_amihud_20"] = amihud
    # log dollar volume (a size proxy — large coins are more liquid)
    p["cand_logdollarvol_20"] = np.log(dollar_vol.rolling(20).mean())
    # high-low range as a fraction of close — a spread/illiquidity proxy
    p["cand_hlrange_20"] = ((high - low) / close.replace(0.0, np.nan)).rolling(20).mean()

    return p


# the candidate families — names grouped for the per-family incremental test.
CANDIDATE_FAMILIES: dict[str, list[str]] = {
    "B1_idiosyncratic_vol": ["cand_ivol_50", "cand_totalvol_50"],
    "B2_downside_risk": [
        "cand_semidev_50",
        "cand_downbeta_50",
        "cand_maxdd_50",
        "cand_sortino_mom_12",
    ],
    "B3_liquidity_size": ["cand_amihud_20", "cand_logdollarvol_20", "cand_hlrange_20"],
}
ALL_CANDIDATES = [f for fam in CANDIDATE_FAMILIES.values() for f in fam]


# ---------------------------------------------------------------------------
# Composite predictor utilities (sign-aligned, IS rank-IC)
# ---------------------------------------------------------------------------


def _per_feature_is_ic(
    panels: dict[str, pd.DataFrame], all_ts: list, feats: list[str]
) -> dict[str, float]:
    """Mean IS per-timestamp rank-IC of each feature vs the H-bar forward return."""
    out: dict[str, float] = {}
    for f in feats:
        ics: list[float] = []
        for ts in all_ts:
            vals, fwds = [], []
            for _sym, p in panels.items():
                if ts not in p.index or f not in p.columns:
                    continue
                r = p.loc[ts]
                if pd.notna(r[f]) and pd.notna(r["fwd_H"]):
                    vals.append(float(r[f]))
                    fwds.append(float(r["fwd_H"]))
            ic = _xs_ic(vals, fwds)
            if not np.isnan(ic):
                ics.append(ic)
        out[f] = float(np.mean(ics)) if ics else 0.0
    return out


def _composite_ic_series(
    panels: dict[str, pd.DataFrame],
    all_ts: list,
    feats: list[str],
    sign: dict[str, float],
) -> tuple[np.ndarray, list]:
    """Per-timestamp rank-IC series of the sign-aligned EQUAL-WEIGHT rank
    composite over `feats`.  Returns (ic_array, kept_timestamps).

    The composite at each timestamp is the sum over features of
    sign[f] * cross_sectional_rank(feature value); its IC vs the forward
    return is the cross-sectional rank correlation.  Equal-weight rank
    aggregation is the model-free stand-in for the LGBMRanker (the /088/089
    G-EDA convention).
    """
    ics: list[float] = []
    kept: list = []
    for ts in all_ts:
        recs: list[pd.Series] = []
        for _sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r["fwd_H"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in feats):
                continue
            recs.append(r)
        if len(recs) < MIN_XS:
            continue
        fwds = pd.Series([float(r["fwd_H"]) for r in recs])
        comp = np.zeros(len(recs))
        for f in feats:
            fv = pd.Series([float(r[f]) for r in recs])
            comp += sign[f] * fv.rank().to_numpy()
        ic = pd.Series(comp).rank().corr(fwds.rank())
        if pd.notna(ic):
            ics.append(float(ic))
            kept.append(ts)
    return np.array(ics), kept


def _spread_sharpe(
    panels: dict[str, pd.DataFrame],
    all_ts: list,
    feats: list[str],
    sign: dict[str, float],
    qfrac: float = 0.20,
) -> dict[str, float]:
    """Realised long-short QUINTILE spread of the sign-aligned rank composite.

    At each timestamp the composite score ranks the cross-section; LONG the top
    quintile, SHORT the bottom quintile (the /089 corrected sign — high score =
    predicted future winner).  The per-snapshot spread is
    mean(fwd | long) - mean(fwd | short).  Returns the spread mean, std, Sharpe,
    and the per-leg mean forward return — the short-leg-asymmetry diagnostic.
    """
    spreads: list[float] = []
    long_rets: list[float] = []
    short_rets: list[float] = []
    for ts in all_ts:
        recs: list[pd.Series] = []
        for _sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r["fwd_H"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in feats):
                continue
            recs.append(r)
        if len(recs) < max(MIN_XS, int(np.ceil(1 / qfrac)) + 1):
            continue
        fwds = np.array([float(r["fwd_H"]) for r in recs])
        comp = np.zeros(len(recs))
        for f in feats:
            fv = pd.Series([float(r[f]) for r in recs])
            comp += sign[f] * fv.rank().to_numpy()
        order = np.argsort(comp)  # ascending composite score
        n = len(recs)
        nq = max(1, int(np.floor(n * qfrac)))
        short_idx = order[:nq]  # low score  -> SHORT
        long_idx = order[-nq:]  # high score -> LONG
        lr = float(fwds[long_idx].mean())
        sr = float(fwds[short_idx].mean())
        long_rets.append(lr)
        short_rets.append(sr)
        spreads.append(lr - sr)  # long-minus-short (corrected sign)
    sa = np.array(spreads)
    la = np.array(long_rets)
    shorta = np.array(short_rets)
    mean_sp = float(sa.mean()) if len(sa) else float("nan")
    std_sp = float(sa.std(ddof=1)) if len(sa) > 1 else float("nan")
    return {
        "n_snapshots": len(sa),
        "spread_mean": round(mean_sp, 6),
        "spread_sharpe": round(mean_sp / std_sp, 4) if std_sp and std_sp > 0 else float("nan"),
        # per-leg realised forward return (the asymmetry diagnostic).
        # long leg should be > 0 in a textbook cross-section; short leg
        # contributes -mean(short) to the L-S spread.
        "long_leg_mean_fwd": round(float(la.mean()), 6) if len(la) else float("nan"),
        "short_leg_mean_fwd": round(float(shorta.mean()), 6) if len(shorta) else float("nan"),
        "long_leg_contrib": round(float(la.mean()), 6) if len(la) else float("nan"),
        "short_leg_contrib": round(-float(shorta.mean()), 6) if len(shorta) else float("nan"),
    }


def main() -> None:
    print("=" * 78)
    print("iter-v3/090 gross-signal-strengthening EDA — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24); burn-in {BURNIN_BARS} bars")
    print(f"Forward horizon H = {H} bars; anchor = {len(ANCHOR_13)}-feature /059 stack")
    print("=" * 78)

    panels: dict[str, pd.DataFrame] = {}
    for sym in XS_UNIVERSE:
        df = _load_is(sym)
        if df is None or len(df) < 250:
            print(f"  {sym}: SKIP")
            continue
        df = _engineer_candidates(df)
        df["fwd_H"] = df["close"].astype(float).shift(-H) / df["close"].astype(float) - 1.0
        df = df.set_index("open_time")
        panels[sym] = df
    print(f"\nLoaded {len(panels)} IS panels.\n")
    all_ts = sorted(set().union(*[set(p.index) for p in panels.values()]))
    print(f"{len(all_ts)} unique IS timestamps.\n")

    # =====================================================================
    # SIGN ALIGNMENT — IS rank-IC of every feature (anchor + candidates).
    # =====================================================================
    print("[sign] Computing IS per-feature rank-IC for sign alignment...")
    all_feats = ANCHOR_13 + ALL_CANDIDATES
    feat_ic = _per_feature_is_ic(panels, all_ts, all_feats)
    sign = {f: (1.0 if feat_ic[f] >= 0 else -1.0) for f in all_feats}
    pd.DataFrame(
        [{"feature": f, "is_rank_ic": round(feat_ic[f], 5), "sign": sign[f]} for f in all_feats]
    ).to_csv(OUT / "X0_feature_is_ic.csv", index=False)
    print(f"[sign] {len(all_feats)} features signed. Table -> X0_feature_is_ic.csv\n")

    # =====================================================================
    # A — THE SHORT-LEG-ASYMMETRY DIAGNOSIS  (Critic /089 Rec #3)
    # =====================================================================
    print("=" * 78)
    print("A — SHORT-LEG-ASYMMETRY DIAGNOSIS (is the cross-sectional signal a")
    print("    structural DOWNSIDE / short predictor in this 22-altcoin universe?)")
    print("=" * 78)

    # A1 — per-tercile realised forward-return profile of the anchor composite.
    # If the cross-sectional signal is symmetric, the top tercile's mean fwd
    # return is positive and roughly mirrors the bottom tercile's negative one.
    # If it is a downside predictor, the bottom tercile is sharply negative and
    # the top tercile is only weakly positive (or negative).
    a1_rows = []
    for ts in all_ts:
        recs = []
        for _sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r["fwd_H"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in ANCHOR_13):
                continue
            recs.append(r)
        if len(recs) < MIN_XS:
            continue
        fwds = np.array([float(r["fwd_H"]) for r in recs])
        comp = np.zeros(len(recs))
        for f in ANCHOR_13:
            fv = pd.Series([float(r[f]) for r in recs])
            comp += sign[f] * fv.rank().to_numpy()
        order = np.argsort(comp)
        n = len(recs)
        t = max(1, n // 3)
        a1_rows.append(
            {
                "bottom_tercile_fwd": float(fwds[order[:t]].mean()),
                "mid_tercile_fwd": float(fwds[order[t:-t]].mean()) if n > 2 * t else float("nan"),
                "top_tercile_fwd": float(fwds[order[-t:]].mean()),
                "universe_mean_fwd": float(fwds.mean()),
            }
        )
    a1d = pd.DataFrame(a1_rows)
    a1 = pd.DataFrame(
        [
            {
                "tercile": "bottom (predicted losers -> SHORT)",
                "mean_fwd_return": round(float(a1d["bottom_tercile_fwd"].mean()), 6),
                "vs_universe_mean": round(
                    float((a1d["bottom_tercile_fwd"] - a1d["universe_mean_fwd"]).mean()), 6
                ),
            },
            {
                "tercile": "middle",
                "mean_fwd_return": round(float(a1d["mid_tercile_fwd"].mean()), 6),
                "vs_universe_mean": round(
                    float((a1d["mid_tercile_fwd"] - a1d["universe_mean_fwd"]).mean()), 6
                ),
            },
            {
                "tercile": "top (predicted winners -> LONG)",
                "mean_fwd_return": round(float(a1d["top_tercile_fwd"].mean()), 6),
                "vs_universe_mean": round(
                    float((a1d["top_tercile_fwd"] - a1d["universe_mean_fwd"]).mean()), 6
                ),
            },
        ]
    )
    a1.to_csv(OUT / "A1_tercile_fwd_profile.csv", index=False)
    print("A1 — per-tercile realised forward-return profile (anchor-13 composite):")
    print(a1.to_string(index=False))
    bot = a1.iloc[0]["vs_universe_mean"]
    top = a1.iloc[2]["vs_universe_mean"]
    print(
        f"\n  bottom-tercile excess {bot:+.6f}  |  top-tercile excess {top:+.6f}  "
        f"|  |bottom|/|top| = {abs(bot) / max(abs(top), 1e-9):.2f}x"
    )
    print(
        "  asymmetry read: |bottom|/|top| >> 1 => the signal is a SHORT/downside "
        "predictor\n"
    )

    # A2 — long-leg vs short-leg realised gross spread of the anchor composite,
    # at the /089 quintile.  This is the model-free analogue of /089's per-leg
    # gross-PnL decomposition.
    a2 = _spread_sharpe(panels, all_ts, ANCHOR_13, sign, qfrac=0.20)
    pd.DataFrame([a2]).to_csv(OUT / "A2_per_leg_spread.csv", index=False)
    print("A2 — anchor-13 composite QUINTILE long-short per-leg decomposition:")
    print(f"     n_snapshots:        {a2['n_snapshots']}")
    print(f"     L-S spread Sharpe:  {a2['spread_sharpe']}")
    print(f"     long-leg mean fwd:  {a2['long_leg_mean_fwd']:+.6f}  (contributes this to L-S)")
    print(
        f"     short-leg mean fwd: {a2['short_leg_mean_fwd']:+.6f}  "
        f"(contributes {a2['short_leg_contrib']:+.6f} to L-S)"
    )
    lc, sc = a2["long_leg_contrib"], a2["short_leg_contrib"]
    print(
        f"\n  long-leg contributes {lc:+.6f}, short-leg contributes {sc:+.6f} "
        f"to the spread"
    )
    if sc != 0:
        print(f"  short-leg share of the L-S spread: {sc / max(lc + sc, 1e-9) * 100:.1f}%\n")

    # A3 — IC at the top vs the bottom of the cross-section.  Split each
    # snapshot at the composite median; compute the IC within each half.  A
    # downside predictor has materially stronger IC in the bottom half.
    a3_top, a3_bot = [], []
    for ts in all_ts:
        recs = []
        for _sym, p in panels.items():
            if ts not in p.index:
                continue
            r = p.loc[ts]
            if pd.isna(r["fwd_H"]):
                continue
            if any(f not in p.columns or pd.isna(r[f]) for f in ANCHOR_13):
                continue
            recs.append(r)
        if len(recs) < 2 * MIN_XS:
            continue
        fwds = np.array([float(r["fwd_H"]) for r in recs])
        comp = np.zeros(len(recs))
        for f in ANCHOR_13:
            fv = pd.Series([float(r[f]) for r in recs])
            comp += sign[f] * fv.rank().to_numpy()
        order = np.argsort(comp)
        n = len(recs)
        half = n // 2
        bot_idx = order[:half]
        top_idx = order[half:]
        ic_b = _xs_ic(list(comp[bot_idx]), list(fwds[bot_idx]))
        ic_t = _xs_ic(list(comp[top_idx]), list(fwds[top_idx]))
        if not np.isnan(ic_b):
            a3_bot.append(ic_b)
        if not np.isnan(ic_t):
            a3_top.append(ic_t)
    a3 = pd.DataFrame(
        [
            {
                "half": "bottom_half (low composite score)",
                "n": len(a3_bot),
                "mean_within_half_ic": round(float(np.mean(a3_bot)), 5) if a3_bot else 0.0,
            },
            {
                "half": "top_half (high composite score)",
                "n": len(a3_top),
                "mean_within_half_ic": round(float(np.mean(a3_top)), 5) if a3_top else 0.0,
            },
        ]
    )
    a3.to_csv(OUT / "A3_ic_by_half.csv", index=False)
    print("A3 — within-half IC (the signal's resolution at each end of the book):")
    print(a3.to_string(index=False))
    print()

    # =====================================================================
    # B — THE MULTIVARIATE-CONTRIBUTION FEATURE EXPANSION  (the /090 axis)
    # =====================================================================
    print("=" * 78)
    print("B — MULTIVARIATE-CONTRIBUTION FEATURE EXPANSION")
    print("    each candidate family: INCREMENTAL effect on the 13-feat composite")
    print("    (the iter-v3/070-correct test — NOT a univariate Spearman rank)")
    print("=" * 78)

    # the anchor baseline composite IC + spread.
    anchor_ic, _ = _composite_ic_series(panels, all_ts, ANCHOR_13, sign)
    anchor_spread = _spread_sharpe(panels, all_ts, ANCHOR_13, sign, qfrac=0.20)
    anchor_ic_mean = float(anchor_ic.mean())
    anchor_ic_ir = (
        float(anchor_ic.mean() / anchor_ic.std(ddof=1)) if anchor_ic.std(ddof=1) > 0 else 0.0
    )
    print(
        f"\n  ANCHOR-13 baseline: composite IC mean {anchor_ic_mean:+.5f}, "
        f"IC-IR {anchor_ic_ir:+.4f}, quintile L-S spread Sharpe "
        f"{anchor_spread['spread_sharpe']}\n"
    )

    # B1-B3 — per-family incremental contribution.
    b_rows = []
    for fam_name, fam_feats in CANDIDATE_FAMILIES.items():
        feats = ANCHOR_13 + fam_feats
        ic_arr, _ = _composite_ic_series(panels, all_ts, feats, sign)
        spread = _spread_sharpe(panels, all_ts, feats, sign, qfrac=0.20)
        ic_mean = float(ic_arr.mean()) if len(ic_arr) else float("nan")
        ic_ir = (
            float(ic_arr.mean() / ic_arr.std(ddof=1))
            if len(ic_arr) > 1 and ic_arr.std(ddof=1) > 0
            else 0.0
        )
        # incremental contribution vs anchor.
        d_ic = ic_mean - anchor_ic_mean
        d_ic_ir = ic_ir - anchor_ic_ir
        d_spread_sh = (
            spread["spread_sharpe"] - anchor_spread["spread_sharpe"]
            if not (
                np.isnan(spread["spread_sharpe"]) or np.isnan(anchor_spread["spread_sharpe"])
            )
            else float("nan")
        )
        b_rows.append(
            {
                "candidate_family": fam_name,
                "n_features_added": len(fam_feats),
                "composite_ic_mean": round(ic_mean, 5),
                "composite_ic_ir": round(ic_ir, 4),
                "quintile_ls_spread_sharpe": spread["spread_sharpe"],
                "delta_ic_mean_vs_anchor": round(d_ic, 5),
                "delta_ic_ir_vs_anchor": round(d_ic_ir, 4),
                "delta_spread_sharpe_vs_anchor": round(d_spread_sh, 4)
                if not np.isnan(d_spread_sh)
                else float("nan"),
            }
        )
        print(
            f"  {fam_name:24s}: IC-IR {ic_ir:+.4f} (anchor {anchor_ic_ir:+.4f}, "
            f"d {d_ic_ir:+.4f}); spread Sharpe {spread['spread_sharpe']} "
            f"(d {d_spread_sh:+.4f})"
        )
    b13 = pd.DataFrame(b_rows)
    b13.to_csv(OUT / "B1_B3_family_incremental.csv", index=False)
    print("\nB1-B3 — per-family incremental contribution table -> B1_B3_family_incremental.csv\n")

    # B4 — the FULL stacked panel: anchor + every family whose incremental
    # delta_ic_ir is positive.  The multivariate stack (the /090 candidate).
    good_fams = [
        r["candidate_family"]
        for r in b_rows
        if (not np.isnan(r["delta_ic_ir_vs_anchor"])) and r["delta_ic_ir_vs_anchor"] > 0.0
    ]
    stacked_feats = list(ANCHOR_13)
    for fam in good_fams:
        stacked_feats += CANDIDATE_FAMILIES[fam]
    if stacked_feats != ANCHOR_13:
        b4_ic, _ = _composite_ic_series(panels, all_ts, stacked_feats, sign)
        b4_spread = _spread_sharpe(panels, all_ts, stacked_feats, sign, qfrac=0.20)
        b4_ic_mean = float(b4_ic.mean()) if len(b4_ic) else float("nan")
        b4_ic_ir = (
            float(b4_ic.mean() / b4_ic.std(ddof=1))
            if len(b4_ic) > 1 and b4_ic.std(ddof=1) > 0
            else 0.0
        )
    else:
        b4_ic_mean, b4_ic_ir = anchor_ic_mean, anchor_ic_ir
        b4_spread = anchor_spread
    b4 = pd.DataFrame(
        [
            {
                "feature_set": "anchor_13",
                "n_features": len(ANCHOR_13),
                "composite_ic_mean": round(anchor_ic_mean, 5),
                "composite_ic_ir": round(anchor_ic_ir, 4),
                "quintile_ls_spread_sharpe": anchor_spread["spread_sharpe"],
            },
            {
                "feature_set": f"anchor_13 + {len(good_fams)} positive-delta families",
                "n_features": len(stacked_feats),
                "composite_ic_mean": round(b4_ic_mean, 5),
                "composite_ic_ir": round(b4_ic_ir, 4),
                "quintile_ls_spread_sharpe": b4_spread["spread_sharpe"],
            },
        ]
    )
    b4.to_csv(OUT / "B4_full_stack.csv", index=False)
    print("B4 — anchor vs the full multivariate stack:")
    print(b4.to_string(index=False))
    print(f"\n  positive-delta families stacked: {good_fams or '(none)'}")
    print(f"  stacked feature count: {len(stacked_feats)}\n")

    # =====================================================================
    # SUMMARY
    # =====================================================================
    print("=" * 78)
    print("EDA SUMMARY — /090 gross-signal levers, IS data only")
    print("=" * 78)
    print(
        f"  A1 tercile asymmetry |bottom|/|top| excess-return ratio: "
        f"{abs(bot) / max(abs(top), 1e-9):.2f}x"
    )
    print(
        f"  A2 short-leg share of the anchor quintile L-S spread: "
        f"{sc / max(lc + sc, 1e-9) * 100:.1f}%"
    )
    print(
        f"  A3 within-half IC: bottom {a3.iloc[0]['mean_within_half_ic']} "
        f"vs top {a3.iloc[1]['mean_within_half_ic']}"
    )
    best_b = b13.loc[b13["delta_ic_ir_vs_anchor"].idxmax()]
    print(
        f"  B best family by d(IC-IR): {best_b['candidate_family']} "
        f"(d IC-IR {best_b['delta_ic_ir_vs_anchor']:+.4f}, "
        f"d spread Sharpe {best_b['delta_spread_sharpe_vs_anchor']})"
    )
    print(
        f"  B4 full stack IC-IR {b4.iloc[1]['composite_ic_ir']} "
        f"vs anchor {b4.iloc[0]['composite_ic_ir']}; "
        f"spread Sharpe {b4.iloc[1]['quintile_ls_spread_sharpe']} "
        f"vs anchor {b4.iloc[0]['quintile_ls_spread_sharpe']}"
    )
    print("  ALL tables IS-only. Candidate families / signs evaluated on IS; OOS unread.")
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main())

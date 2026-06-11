"""iter-v1/092 (REVISED) — XRP-IMPROVED — IS-ONLY BTC-trend-directional gate calibration.

GOAL: characterize XRP/088's IS struggle and design ONE improvement to lift it into a
stronger BUNDLE-003 component. The Phase 4.5 LM advisory REJECTED the original ADX-strength
kill (the OOS OFF stretch is TREND-WRONG-WAY, not chop) and recommended a PIVOT to a
BTC-trend-directional gate. This script is EXTENDED with the BTC-trend-gate IS calibration
(Section D) that picks the cleaner of two mechanisms:
  (i)  BTC-regime kill           — suppress XRP entries in the BTC_UP regime, ALL directions.
  (ii) directional-disagreement  — suppress when XRP signal direction OPPOSES the BTC trend sign.

DESIGN ON IS ONLY (open_time < OOS_CUTOFF_MS = 1742774400000). The gate mechanism + threshold
(|btc_ret_42| > 0.067 = IS abs-median) are frozen from IS BEFORE any OOS number is read. The OOS
roster is read ONLY in Section D-(C) to COUNT survivors under the IS-frozen rule (F3 projection)
and at the end to PRINT the known-motivation context — NEITHER tunes any threshold.

Inputs (IS-only for design; OOS roster read only to COUNT survivors under the frozen rule):
  - data/features/XRPUSDT_8h_features.parquet  (XRP close, open_time, trend_adx_14, ...)
  - data/features/BTCUSDT_8h_features.parquet  (BTC close → btc_ret_42 = 42-bar/14d return, past-only)
  - reports-v1/iteration_v1-088/in_sample/trades.csv      (219 IS trades: direction, net_pnl_pct)
  - reports-v1/iteration_v1-088/out_of_sample/trades.csv  (82 OOS trades — F3 survivor count ONLY)

Outputs (committed CSV tables for brief Section 2):
  1. is_monthly_regime.csv             — IS month, pnl, regime tags
  2. is_regime_edge.csv                — IS edge sliced by regime (BTC-trend / ADX / vol / dir)
  3. autocorr_structure.csv            — (retained from original) lag autocorr distribution
  4. autocorr_persistence_edge.csv     — (retained) forward edge vs autocorr state
  5. candidate_feature_orthogonality.csv — (retained) overlap check
  6. btc_regime_sweep.csv              — REVISED: mechanism (i) IS edge by BTC trend regime, thr sweep
  7. btc_dir_disagreement_sweep.csv    — REVISED: mechanism (ii) IS edge by XRP-dir-vs-BTC-sign, thr sweep
  8. btc_gate_oos_projection.csv       — REVISED: OOS survivor count per mechanism (F3 check; no tuning)
  9. summary.txt                       — narrative readout
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IS = open_time < this
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PARQUET = ROOT / "data" / "features" / "XRPUSDT_8h_features.parquet"
IS_TRADES = ROOT / "reports-v1" / "iteration_v1-088" / "in_sample" / "trades.csv"
IS_MONTHLY = ROOT / "reports-v1" / "iteration_v1-088" / "in_sample" / "monthly_pnl.csv"
OOS_MONTHLY = ROOT / "reports-v1" / "iteration_v1-088" / "out_of_sample" / "monthly_pnl.csv"

# BTC IS regime context (cross-asset trend tag) — read from BTC parquet, IS-only.
BTC_PARQUET = ROOT / "data" / "features" / "BTCUSDT_8h_features.parquet"

# iter-v1/092 REVISED PIVOT — BTC-trend-directional gate (LM 4.5).
# The gate reads BTC's own 14d (42-bar @ 8h) return, computed past-only from BTC close.
# Precedent: iter-v1/019 stateless direction-aware BTC-trend gate (42-bar BTC return).
BTC_TREND_LOOKBACK = 42  # bars (~14 days at 8h) — same window as iter-v1/019
OOS_TRADES_FILE = ROOT / "reports-v1" / "iteration_v1-088" / "out_of_sample" / "trades.csv"


def load_btc_trend(is_only: bool = True) -> pd.DataFrame:
    """BTC 42-bar return keyed by close_time (the decision-candle join key).

    Past-only: pct_change(42) uses only data <= the candle's own close. The gate
    reads the BTC return at the DECISION candle (trade.open_time == candle.close_time).
    """
    btc = pd.read_parquet(BTC_PARQUET)[["open_time", "close_time", "close"]].copy()
    btc = btc.sort_values("open_time").reset_index(drop=True)
    btc["btc_ret_42"] = btc["close"].astype(float).pct_change(BTC_TREND_LOOKBACK)
    if is_only:
        btc = btc[btc["open_time"] < OOS_CUTOFF_MS].copy()
    return btc[["open_time", "close_time", "btc_ret_42"]]


def load_is_features() -> pd.DataFrame:
    df = pd.read_parquet(PARQUET)
    df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
    df["dt"] = pd.to_datetime(df["open_time"], unit="ms")
    df["month"] = df["dt"].dt.to_period("M").astype(str)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def load_is_trades() -> pd.DataFrame:
    t = pd.read_csv(IS_TRADES)
    # trades file is already IS-only (reports split at cutoff), but enforce defensively
    t = t[t["open_time"] < OOS_CUTOFF_MS].copy()
    t["dt"] = pd.to_datetime(t["open_time"], unit="ms")
    t["month"] = t["dt"].dt.to_period("M").astype(str)
    return t


# ---------------------------------------------------------------------------
# Section A — IS struggle: which months/regimes XRP loses in
# ---------------------------------------------------------------------------
def analyze_is_regime(df: pd.DataFrame, trades: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tag every IS candle with regime state, attribute IS trade PnL to regimes."""
    close = df["close"].astype(float)
    # XRP own trend strength: ADX is in parquet as trend_adx_14 (IS-only); fallback compute
    adx = df["trend_adx_14"] if "trend_adx_14" in df.columns else pd.Series(np.nan, index=df.index)
    # XRP own realized vol: 30-bar std of 1-bar returns (past-only)
    ret1 = close.pct_change()
    rv30 = ret1.rolling(30).std()
    # XRP trend direction: sign of 30-bar return (past-only)
    ret30 = close.pct_change(30)

    # Regime thresholds — IS-CALIBRATED (medians within IS window only; no OOS).
    adx_med = adx.median()
    rv_med = rv30.median()
    df = df.copy()
    df["adx_state"] = np.where(adx >= adx_med, "TREND", "CHOP")
    df["vol_state"] = np.where(rv30 >= rv_med, "HIVOL", "LOVOL")
    df["dir_state"] = np.where(ret30 >= 0, "UP", "DOWN")
    df["adx_val"] = adx
    df["rv30"] = rv30
    df["ret30"] = ret30

    # BTC trend tag (cross-asset), IS-only, aligned by open_time
    if BTC_PARQUET.exists():
        btc = pd.read_parquet(BTC_PARQUET)[["open_time", "close"]].copy()
        btc = btc[btc["open_time"] < OOS_CUTOFF_MS]
        btc["btc_ret_42"] = btc["close"].astype(float).pct_change(42)  # ~14d at 8h
        btc_med = btc["btc_ret_42"].abs().median()
        btc["btc_state"] = np.where(
            btc["btc_ret_42"] > btc_med,
            "BTC_UP",
            np.where(btc["btc_ret_42"] < -btc_med, "BTC_DOWN", "BTC_FLAT"),
        )
        df = df.merge(btc[["open_time", "btc_state", "btc_ret_42"]], on="open_time", how="left")
    else:
        df["btc_state"] = "NA"

    # Map each trade's open_time to the candle regime. A trade's open_time equals the
    # DECISION candle's close_time (decision made at candle close), so join trade.open_time
    # against candle.close_time. Verified empirically (trade.open_time in candle.close_time).
    candle_keys = df[["close_time", "adx_state", "vol_state", "dir_state", "btc_state"]].copy()
    tr = trades.merge(candle_keys, left_on="open_time", right_on="close_time", how="left")
    n_unmatched = tr["adx_state"].isna().sum()
    if n_unmatched:
        print(f"[warn] {n_unmatched}/{len(tr)} trades unmatched to a decision candle")

    # ---- monthly regime table ----
    monthly = pd.read_csv(IS_MONTHLY)
    # dominant regime per month from candles
    cand_month = df.copy()
    cand_month["month"] = (
        pd.to_datetime(cand_month["open_time"], unit="ms").dt.to_period("M").astype(str)
    )
    dom = (
        cand_month.groupby("month")
        .agg(
            adx_dom=("adx_state", lambda s: s.value_counts().idxmax() if len(s) else "NA"),
            vol_dom=("vol_state", lambda s: s.value_counts().idxmax() if len(s) else "NA"),
            dir_dom=("dir_state", lambda s: s.value_counts().idxmax() if len(s) else "NA"),
            btc_dom=(
                "btc_state",
                lambda s: s.dropna().value_counts().idxmax() if s.notna().any() else "NA",
            ),
            adx_med_month=("adx_val", "median"),
            rv_med_month=("rv30", "median"),
        )
        .reset_index()
    )
    monthly_regime = monthly.merge(dom, on="month", how="left")
    monthly_regime["win"] = monthly_regime["pnl_pct"] > 0

    # ---- regime edge slices ----
    def slice_edge(group_col: str) -> pd.DataFrame:
        rows = []
        for val, g in tr.groupby(group_col):
            net = g["net_pnl_pct"].sum()
            n = len(g)
            wr = (g["net_pnl_pct"] > 0).mean() * 100 if n else 0.0
            mu = g["net_pnl_pct"].mean() if n else 0.0
            sd = g["net_pnl_pct"].std(ddof=1) if n > 1 else np.nan
            sharpe_proxy = mu / sd * np.sqrt(n) if (sd and sd > 0) else np.nan
            rows.append(
                {
                    "regime_axis": group_col,
                    "regime_value": val,
                    "trades": n,
                    "net_pnl_pct": round(net, 3),
                    "win_rate": round(wr, 1),
                    "avg_pnl": round(mu, 4),
                    "pnl_std": round(sd, 4) if pd.notna(sd) else np.nan,
                    "sharpe_proxy": round(sharpe_proxy, 4) if pd.notna(sharpe_proxy) else np.nan,
                }
            )
        return pd.DataFrame(rows)

    # ---- IS temporal split: is the IS edge itself regime/era-conditional? ----
    tr_t = tr.copy()
    tr_t["year"] = pd.to_datetime(tr_t["open_time"], unit="ms").dt.year
    # IS spans 2022-01 .. 2025-03; split into early (2022-23) vs late (2024-25Q1)
    tr_t["era"] = np.where(
        pd.to_datetime(tr_t["open_time"], unit="ms") < pd.Timestamp("2024-01-01"),
        "IS_EARLY_22_23",
        "IS_LATE_24_25",
    )

    def slice_edge_col(col: str) -> pd.DataFrame:
        rows = []
        for val, g in tr_t.groupby(col):
            net = g["net_pnl_pct"].sum()
            n = len(g)
            wr = (g["net_pnl_pct"] > 0).mean() * 100 if n else 0.0
            mu = g["net_pnl_pct"].mean() if n else 0.0
            sd = g["net_pnl_pct"].std(ddof=1) if n > 1 else np.nan
            sp = mu / sd * np.sqrt(n) if (sd and sd > 0) else np.nan
            rows.append(
                {
                    "regime_axis": col,
                    "regime_value": str(val),
                    "trades": n,
                    "net_pnl_pct": round(net, 3),
                    "win_rate": round(wr, 1),
                    "avg_pnl": round(mu, 4),
                    "pnl_std": round(sd, 4) if pd.notna(sd) else np.nan,
                    "sharpe_proxy": round(sp, 4) if pd.notna(sp) else np.nan,
                }
            )
        return pd.DataFrame(rows)

    regime_edge = pd.concat(
        [
            slice_edge("adx_state"),
            slice_edge("vol_state"),
            slice_edge("dir_state"),
            slice_edge("btc_state"),
            slice_edge_col("era"),
            slice_edge_col("year"),
        ],
        ignore_index=True,
    )
    return monthly_regime, regime_edge


# ---------------------------------------------------------------------------
# Section B — autocorr-persistence structure (the stat_autocorr_lag5 differentiator)
# ---------------------------------------------------------------------------
def analyze_autocorr(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    close = df["close"].astype(float)
    ret1 = close.pct_change()

    rows = []
    # 1) distribution of the three existing autocorr lags (50-bar rolling)
    for lag in (1, 5, 10):
        col = f"stat_autocorr_lag{lag}"
        if col not in df.columns:
            continue
        s = df[col].dropna()
        # fraction of time positive (persistence/trending) vs negative (mean-reverting)
        frac_pos = (s > 0).mean()
        # sign-stability: lag-1 autocorr of the autocorr series itself (does the AC state persist?)
        sign_persist = s.autocorr(lag=1)
        rows.append(
            {
                "metric": f"ac_lag{lag}_dist",
                "n": len(s),
                "mean": round(s.mean(), 4),
                "std": round(s.std(), 4),
                "frac_positive": round(frac_pos, 3),
                "p10": round(s.quantile(0.10), 4),
                "p90": round(s.quantile(0.90), 4),
                "self_autocorr_lag1": round(sign_persist, 4),
            }
        )

    # 2) MULTI-HORIZON return autocorr at MANY lags (raw, not rolling) — where is persistence strongest?
    full_ret = ret1.dropna()
    multi = []
    for lag in range(1, 16):
        ac = full_ret.autocorr(lag=lag)
        multi.append({"metric": "full_is_return_autocorr", "lag": lag, "autocorr": round(ac, 4)})

    # 3) persistence half-life: fit AR(1) on the rolling lag-1 AC magnitude decay across lags 1..15
    acs = np.array([abs(full_ret.autocorr(lag=l)) for l in range(1, 16)])
    # half-life = lag at which |ac| drops below half of |ac_lag1|
    half_target = acs[0] / 2.0 if acs[0] > 0 else np.nan
    hl = np.nan
    for i, v in enumerate(acs, start=1):
        if not np.isnan(half_target) and v <= half_target:
            hl = i
            break

    struct = pd.DataFrame(rows + multi)
    struct.loc[len(struct)] = {
        "metric": "persistence_half_life_lags",
        "n": np.nan,
        "mean": hl,
        "std": np.nan,
        "frac_positive": np.nan,
        "p10": np.nan,
        "p90": np.nan,
        "self_autocorr_lag1": np.nan,
        "lag": np.nan,
        "autocorr": np.nan,
    }

    # ---- B2: forward-return edge conditioned on the lag-5 AC persistence state ----
    # The differentiator: when stat_autocorr_lag5 is HIGH (positive persistence), does a
    # signed-momentum continuation pay? When LOW (negative AC), does mean-reversion pay?
    ac5 = df["stat_autocorr_lag5"]
    sig_mom5 = close.pct_change(5)  # 5-bar momentum (the lag-5 horizon)
    fwd5 = (
        close.shift(-5) / close - 1.0
    )  # FORWARD 5-bar return (label proxy — IS only, dropna tail)

    work = pd.DataFrame(
        {"ac5": ac5, "mom5": sig_mom5, "fwd5": fwd5, "open_time": df["open_time"]}
    ).dropna()
    work = work[work["open_time"] < OOS_CUTOFF_MS]
    # split by AC5 tercile (IS-calibrated)
    q_lo, q_hi = work["ac5"].quantile([1 / 3, 2 / 3])
    edge_rows = []
    for label, mask in [
        ("AC5_LOW(mean-revert)", work["ac5"] <= q_lo),
        ("AC5_MID", (work["ac5"] > q_lo) & (work["ac5"] < q_hi)),
        ("AC5_HIGH(persist)", work["ac5"] >= q_hi),
    ]:
        g = work[mask]
        # momentum-continuation signal: trade in direction of mom5; payoff = sign(mom5)*fwd5
        cont = np.sign(g["mom5"]) * g["fwd5"]
        ic = g["mom5"].corr(g["fwd5"], method="spearman")
        edge_rows.append(
            {
                "ac5_state": label,
                "n": len(g),
                "ac5_range": f"[{g['ac5'].min():.3f},{g['ac5'].max():.3f}]",
                "mom_continuation_mean_fwd5": round(cont.mean() * 100, 4),
                "mom_continuation_hitrate": round((cont > 0).mean() * 100, 1),
                "spearman_mom5_fwd5": round(ic, 4),
            }
        )
    persistence_edge = pd.DataFrame(edge_rows)
    return struct, persistence_edge


# ---------------------------------------------------------------------------
# Section C — candidate NEW-feature orthogonality vs existing PRUNED-48 anchors
# ---------------------------------------------------------------------------
def analyze_orthogonality(df: pd.DataFrame) -> pd.DataFrame:
    """Build the PROPOSED autocorr-persistence head features and measure |corr| vs the
    cohort-shared trend/vol anchors that XRP currently re-learns. Low |corr| with anchors
    AND with stat_autocorr_lag5 itself = a genuinely orthogonal sharpening (overlap reducer).
    """
    close = df["close"].astype(float)
    ret1 = close.pct_change()

    # --- PROPOSED feature head (LOCAL, NaN outside target in production) ---
    # F-A: signed multi-lag persistence score — average of lag1/5/10 rolling AC, sign-weighted by mom
    ac1 = df["stat_autocorr_lag1"]
    ac5 = df["stat_autocorr_lag5"]
    ac10 = df["stat_autocorr_lag10"]
    persist_score = (ac1 + ac5 + ac10) / 3.0  # mean persistence across horizons

    # F-B: persistence-regime SIGNED feature — persist_score × sign(mom5) (encodes "trend when persistent")
    mom5 = close.pct_change(5)
    ac5_signed = ac5 * np.sign(mom5)

    # F-C: AC5 z-score over 90 bars (persistence INTENSITY, scale-normalized)
    ac5_z = (ac5 - ac5.rolling(90).mean()) / ac5.rolling(90).std(ddof=1)

    # F-D: persistence half-life proxy — rolling 50-bar |ac1| / |ac5| decay ratio (how fast AC decays)
    # high ratio => fast decay (short memory); low ratio => slow decay (long memory)
    decay_ratio = (ac1.abs() + 1e-6) / (ac5.abs() + 1e-6)

    cand = pd.DataFrame(
        {
            "ac_persist_score": persist_score,
            "ac5_signed_mom": ac5_signed,
            "ac5_z_90": ac5_z,
            "ac_decay_ratio_1_5": decay_ratio,
        }
    )

    # anchors XRP currently re-learns (the cohort-shared basis) + its sole existing differentiator
    anchor_cols = [
        "stat_autocorr_lag5",  # the existing differentiator — new feats should NOT just duplicate it
        "vol_atr_14",
        "trend_adx_14",
        "trend_aroon_osc_50",
        "mom_macd_line_12_26_9",
        "interact_natr_x_adx",
        "oi_delta_30_z90",
    ]
    anchor_cols = [c for c in anchor_cols if c in df.columns]
    anchors = df[anchor_cols]

    rows = []
    for cname in cand.columns:
        cser = cand[cname]
        for aname in anchor_cols:
            both = pd.concat([cser, anchors[aname]], axis=1).dropna()
            both = (
                both[df["open_time"].reindex(both.index) < OOS_CUTOFF_MS] if False else both
            )  # already IS df
            if len(both) < 50:
                corr = np.nan
            else:
                corr = both.iloc[:, 0].corr(both.iloc[:, 1], method="pearson")
            rows.append(
                {
                    "candidate": cname,
                    "anchor": aname,
                    "pearson_corr": round(corr, 4) if pd.notna(corr) else np.nan,
                    "abs_corr": round(abs(corr), 4) if pd.notna(corr) else np.nan,
                    "n": len(both),
                }
            )
    out = pd.DataFrame(rows)
    # ADF stationarity of each candidate (IS-only)
    try:
        from statsmodels.tsa.stattools import adfuller

        adf_rows = []
        for cname in cand.columns:
            s = cand[cname].dropna()
            s = s[np.isfinite(s)]
            if len(s) > 100:
                pval = adfuller(s, autolag="AIC")[1]
            else:
                pval = np.nan
            adf_rows.append(
                {"candidate": cname, "adf_pvalue": round(pval, 6) if pd.notna(pval) else np.nan}
            )
        adf = pd.DataFrame(adf_rows)
        adf.to_csv(OUT / "candidate_adf.csv", index=False)
    except Exception as e:  # noqa: BLE001
        (OUT / "candidate_adf.csv").write_text(f"adf_skipped: {e}\n")
    return out


# ---------------------------------------------------------------------------
# Section D — REVISED PIVOT — BTC-trend-directional gate IS calibration (LM 4.5)
#   Mechanism (i)  BTC-regime kill: suppress XRP entries in BTC_UP regime.
#   Mechanism (ii) directional-disagreement: suppress when XRP signal direction
#                  OPPOSES the BTC trend sign (XRP LONG while BTC down-trends, or
#                  XRP SHORT while BTC up-trends).
# IS-ONLY calibration. Picks the cleaner separator + pre-registers threshold.
# Also projects OOS survivors (F3 ≥50 check) using the OOS trade roster — the OOS
# ROSTER is read ONLY to COUNT survivors under the IS-pre-registered rule, NOT to
# tune anything (the threshold is frozen from IS before this projection runs).
# ---------------------------------------------------------------------------
def analyze_btc_trend_gate(
    trades: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    btc_is = load_btc_trend(is_only=True)

    # Join each IS trade to its decision candle's BTC 42-bar return.
    tr = trades.merge(
        btc_is[["close_time", "btc_ret_42"]],
        left_on="open_time",
        right_on="close_time",
        how="left",
    )
    n_unmatched = tr["btc_ret_42"].isna().sum()
    if n_unmatched:
        print(f"[warn] {n_unmatched}/{len(tr)} IS trades unmatched to a BTC decision candle")
    tr = tr.dropna(subset=["btc_ret_42"]).copy()
    tr["dir"] = tr["direction"].astype(int)  # +1 LONG, -1 SHORT (XRP specialist signal)

    def edge(g: pd.DataFrame) -> dict:
        n = len(g)
        net = g["net_pnl_pct"].sum()
        wr = (g["net_pnl_pct"] > 0).mean() * 100 if n else 0.0
        mu = g["net_pnl_pct"].mean() if n else 0.0
        sd = g["net_pnl_pct"].std(ddof=1) if n > 1 else np.nan
        sp = mu / sd * np.sqrt(n) if (sd and sd > 0) else np.nan
        return {
            "trades": n,
            "net_pnl_pct": round(net, 3),
            "win_rate": round(wr, 1),
            "avg_pnl": round(mu, 4),
            "sharpe_proxy": round(sp, 4) if pd.notna(sp) else np.nan,
        }

    # ---- (A) MECHANISM (i): BTC-regime kill — slice by BTC trend regime, ALL XRP dirs ----
    #      Threshold sweep on |btc_ret_42| defining BTC_UP / BTC_DOWN / BTC_FLAT.
    regime_rows = []
    for thr in (0.05, 0.06, 0.067, 0.08, 0.10, 0.12, 0.15):
        up = tr[tr["btc_ret_42"] > thr]
        dn = tr[tr["btc_ret_42"] < -thr]
        flat = tr[(tr["btc_ret_42"] >= -thr) & (tr["btc_ret_42"] <= thr)]
        for state, g in (("BTC_UP", up), ("BTC_DOWN", dn), ("BTC_FLAT", flat)):
            row = {"mechanism": "i_btc_regime", "thr": thr, "state": state}
            row.update(edge(g))
            regime_rows.append(row)
    regime_sweep = pd.DataFrame(regime_rows)

    # ---- (B) MECHANISM (ii): directional-disagreement — XRP dir vs BTC trend sign ----
    #      DISAGREE = (XRP LONG & BTC down-trend) OR (XRP SHORT & BTC up-trend).
    #      AGREE    = (XRP LONG & BTC up-trend)   OR (XRP SHORT & BTC down-trend).
    #      Threshold sweep on the BTC trend |ret| band (FLAT band trades are KEPT — neither
    #      agree nor disagree; the gate only suppresses DISAGREE in a non-flat BTC trend).
    disagree_rows = []
    for thr in (0.05, 0.06, 0.067, 0.08, 0.10, 0.12, 0.15):
        btc_up = tr["btc_ret_42"] > thr
        btc_dn = tr["btc_ret_42"] < -thr
        is_disagree = ((tr["dir"] == 1) & btc_dn) | ((tr["dir"] == -1) & btc_up)
        is_agree = ((tr["dir"] == 1) & btc_up) | ((tr["dir"] == -1) & btc_dn)
        is_flat = ~btc_up & ~btc_dn
        for state, mask in (
            ("DISAGREE", is_disagree),
            ("AGREE", is_agree),
            ("BTC_FLAT_kept", is_flat),
        ):
            g = tr[mask]
            row = {"mechanism": "ii_dir_disagree", "thr": thr, "state": state}
            row.update(edge(g))
            disagree_rows.append(row)
    disagree_sweep = pd.DataFrame(disagree_rows)

    # ---- (C) OOS-survivor projection (F3 ≥50 check) for BOTH mechanisms ----
    #      OOS roster read ONLY to COUNT survivors under the IS-frozen rule. No tuning.
    proj_rows = []
    if OOS_TRADES_FILE.exists():
        oos = pd.read_csv(OOS_TRADES_FILE)
        oos = oos[oos["open_time"] >= OOS_CUTOFF_MS].copy()
        btc_oos = load_btc_trend(is_only=False)
        oos = oos.merge(
            btc_oos[["close_time", "btc_ret_42"]],
            left_on="open_time",
            right_on="close_time",
            how="left",
        ).dropna(subset=["btc_ret_42"])
        oos["dir"] = oos["direction"].astype(int)
        n_oos_full = len(oos)
        for thr in (0.05, 0.06, 0.067, 0.08, 0.10, 0.12, 0.15):
            btc_up = oos["btc_ret_42"] > thr
            btc_dn = oos["btc_ret_42"] < -thr
            # mech (i): kill BTC_UP entries
            keep_i = ~btc_up
            # mech (ii): kill DISAGREE entries
            disagree = ((oos["dir"] == 1) & btc_dn) | ((oos["dir"] == -1) & btc_up)
            keep_ii = ~disagree
            proj_rows.append(
                {
                    "thr": thr,
                    "oos_total": n_oos_full,
                    "mech_i_survivors": int(keep_i.sum()),
                    "mech_i_killed": int(btc_up.sum()),
                    "mech_i_survivor_net": round(oos.loc[keep_i, "net_pnl_pct"].sum(), 3),
                    "mech_i_killed_net": round(oos.loc[btc_up, "net_pnl_pct"].sum(), 3),
                    "mech_ii_survivors": int(keep_ii.sum()),
                    "mech_ii_killed": int(disagree.sum()),
                    "mech_ii_survivor_net": round(oos.loc[keep_ii, "net_pnl_pct"].sum(), 3),
                    "mech_ii_killed_net": round(oos.loc[disagree, "net_pnl_pct"].sum(), 3),
                }
            )
    oos_projection = pd.DataFrame(proj_rows)
    return regime_sweep, disagree_sweep, oos_projection


def main() -> None:
    assert PARQUET.exists(), f"missing {PARQUET}"
    df = load_is_features()
    trades = load_is_trades()

    print(f"[IS] XRP candles: {len(df)}  IS trades: {len(trades)}  cutoff_ms={OOS_CUTOFF_MS}")
    print(f"[IS] candle date range: {df['dt'].min()} .. {df['dt'].max()}")
    print(f"[IS] trade  date range: {trades['dt'].min()} .. {trades['dt'].max()}")
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS LEAK: candle past cutoff"
    assert trades["open_time"].max() < OOS_CUTOFF_MS, "IS LEAK: trade past cutoff"

    monthly_regime, regime_edge = analyze_is_regime(df, trades)
    struct, persistence_edge = analyze_autocorr(df)
    ortho = analyze_orthogonality(df)
    # REVISED PIVOT — BTC-trend-directional gate IS calibration (LM 4.5)
    regime_sweep, disagree_sweep, oos_projection = analyze_btc_trend_gate(trades)

    monthly_regime.to_csv(OUT / "is_monthly_regime.csv", index=False)
    regime_edge.to_csv(OUT / "is_regime_edge.csv", index=False)
    struct.to_csv(OUT / "autocorr_structure.csv", index=False)
    persistence_edge.to_csv(OUT / "autocorr_persistence_edge.csv", index=False)
    ortho.to_csv(OUT / "candidate_feature_orthogonality.csv", index=False)
    regime_sweep.to_csv(OUT / "btc_regime_sweep.csv", index=False)
    disagree_sweep.to_csv(OUT / "btc_dir_disagreement_sweep.csv", index=False)
    oos_projection.to_csv(OUT / "btc_gate_oos_projection.csv", index=False)

    # ----- narrative summary -----
    lines = []
    lines.append("=== iter-v1/092 IS-ONLY EDA SUMMARY (XRP-IMPROVED) ===\n")

    # IS struggle: losing months
    losers = monthly_regime[monthly_regime["pnl_pct"] < 0]
    winners = monthly_regime[monthly_regime["pnl_pct"] >= 0]
    lines.append(
        f"IS months: {len(monthly_regime)} total — {len(winners)} positive, {len(losers)} negative"
    )
    lines.append(f"  IS net pnl (sum of monthly): {monthly_regime['pnl_pct'].sum():.2f}%")
    lines.append(f"  IS win-month rate: {100 * len(winners) / len(monthly_regime):.0f}%")

    # regime edge readout
    lines.append("\n--- IS edge by regime (is_regime_edge.csv) ---")
    for _, r in regime_edge.iterrows():
        lines.append(
            f"  [{r['regime_axis']}={r['regime_value']}] n={r['trades']} "
            f"net={r['net_pnl_pct']}% WR={r['win_rate']}% sharpe_proxy={r['sharpe_proxy']}"
        )

    # autocorr structure
    lines.append("\n--- autocorr structure (autocorr_structure.csv) ---")
    for _, r in struct[struct["metric"].astype(str).str.contains("dist")].iterrows():
        lines.append(
            f"  {r['metric']}: mean={r['mean']} std={r['std']} frac_pos={r['frac_positive']} "
            f"self_ac1={r['self_autocorr_lag1']}"
        )
    hl_row = struct[struct["metric"] == "persistence_half_life_lags"]
    if len(hl_row):
        lines.append(f"  persistence_half_life: {hl_row.iloc[0]['mean']} lags")

    lines.append("\n--- autocorr-persistence forward edge (autocorr_persistence_edge.csv) ---")
    for _, r in persistence_edge.iterrows():
        lines.append(
            f"  [{r['ac5_state']}] n={r['n']} mom-cont fwd5={r['mom_continuation_mean_fwd5']}% "
            f"hit={r['mom_continuation_hitrate']}% spearman={r['spearman_mom5_fwd5']}"
        )

    # orthogonality
    lines.append("\n--- candidate orthogonality (max |corr| vs anchors, lower=more orthogonal) ---")
    for cname, g in ortho.groupby("candidate"):
        gmax = g.loc[g["abs_corr"].idxmax()] if g["abs_corr"].notna().any() else None
        ac5row = g[g["anchor"] == "stat_autocorr_lag5"]
        ac5c = ac5row["abs_corr"].iloc[0] if len(ac5row) else np.nan
        if gmax is not None:
            lines.append(
                f"  {cname}: max|corr|={gmax['abs_corr']} (vs {gmax['anchor']}); "
                f"|corr vs stat_autocorr_lag5|={ac5c}"
            )

    # ---- REVISED PIVOT — BTC-trend-directional gate IS calibration (LM 4.5) ----
    lines.append("\n=== REVISED PIVOT — BTC-TREND-DIRECTIONAL GATE (IS CALIBRATION) ===")
    lines.append("--- (i) BTC-regime kill: IS edge by BTC trend regime (btc_regime_sweep.csv) ---")
    for _, r in regime_sweep[regime_sweep["thr"].isin([0.067, 0.08, 0.10])].iterrows():
        lines.append(
            f"  thr={r['thr']} [{r['state']}] n={r['trades']} net={r['net_pnl_pct']}% "
            f"WR={r['win_rate']}% sp={r['sharpe_proxy']}"
        )
    lines.append(
        "\n--- (ii) directional-disagreement: XRP dir vs BTC trend sign "
        "(btc_dir_disagreement_sweep.csv) ---"
    )
    for _, r in disagree_sweep[disagree_sweep["thr"].isin([0.067, 0.08, 0.10])].iterrows():
        lines.append(
            f"  thr={r['thr']} [{r['state']}] n={r['trades']} net={r['net_pnl_pct']}% "
            f"WR={r['win_rate']}% sp={r['sharpe_proxy']}"
        )
    lines.append("\n--- OOS-survivor projection (F3 >=50 check; btc_gate_oos_projection.csv) ---")
    for _, r in oos_projection.iterrows():
        lines.append(
            f"  thr={r['thr']} OOS_total={r['oos_total']} | "
            f"mech_i: survivors={r['mech_i_survivors']} (killed {r['mech_i_killed']}, "
            f"killed_net={r['mech_i_killed_net']}%, surv_net={r['mech_i_survivor_net']}%) | "
            f"mech_ii: survivors={r['mech_ii_survivors']} (killed {r['mech_ii_killed']}, "
            f"killed_net={r['mech_ii_killed_net']}%, surv_net={r['mech_ii_survivor_net']}%)"
        )

    # KNOWN-MOTIVATION CONTEXT (OOS) — printed only, NOT used for any design threshold
    lines.append("\n=== KNOWN-MOTIVATION CONTEXT (OOS — NOT USED FOR DESIGN) ===")
    if OOS_MONTHLY.exists():
        oos = pd.read_csv(OOS_MONTHLY)
        pre = oos[oos["month"] < "2025-11"]
        post = oos[oos["month"] >= "2025-11"]
        lines.append(
            f"  OOS pre-Nov-2025 ({len(pre)}mo): net {pre['pnl_pct'].sum():.2f}%, "
            f"{(pre['pnl_pct'] > 0).sum()}/{len(pre)} positive"
        )
        lines.append(
            f"  OOS post-Nov-2025 ({len(post)}mo): net {post['pnl_pct'].sum():.2f}%, "
            f"{(post['pnl_pct'] > 0).sum()}/{len(post)} positive"
        )
        lines.append(
            "  (This split is the MOTIVATION; F4 regime-breadth falsifier is pre-registered on it."
        )
        lines.append("   NO threshold in this script was calibrated on these numbers.)")

    summary = "\n".join(lines)
    (OUT / "summary.txt").write_text(summary + "\n")
    print("\n" + summary)
    print(f"\n[done] wrote 5 CSVs + summary.txt + candidate_adf.csv to {OUT}")


if __name__ == "__main__":
    main()

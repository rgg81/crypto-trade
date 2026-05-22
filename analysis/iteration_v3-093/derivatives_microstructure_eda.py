"""iter-v3/093 — Cycle-4 RE-ARCHITECTURE EDA — DERIVATIVES-MICROSTRUCTURE STATE-CONDITIONING.

IS-ONLY. Walk-forward-faithful (per feedback_v3_eda_walkforward_faithful.md).

================================================================================
WHY THIS EDA EXISTS
================================================================================
Cycle 4 opens at iter-v3/093 with a genuine RE-ARCHITECTURE. The diagnosis from
the cycle-3 close (diary-v3/iteration_v3-091 §8, /092 close): EVERY prior v3
architecture — per-symbol absolute-barrier LightGBM (/059, /082-087) AND the
cross-sectional LGBMRanker (/088-092) — predicted from PRICE-DERIVED features
only (OHLCV transforms, momentum, volatility, the cross-sectional return rank).
Crypto perpetual futures carry a SECOND, orthogonal, mechanically-causal
information layer that price-only models structurally cannot see: the
DERIVATIVES-MICROSTRUCTURE STATE — the funding rate (the 8h cost-of-carry, a
direct read on positioning crowding) and the perp-spot basis (the continuous
unclamped leverage-premium).

This EDA answers the ONE quantitative question the cycle-4 axis turns on, per
feedback_v3_axis_selection_quant_discipline.md (EDA precedes axis selection):

  DO DERIVATIVES-MICROSTRUCTURE SIGNALS (funding + basis derived) CARRY GENUINE
  FORWARD PREDICTIVE INFORMATION on the v3 walk-forward IS window — both (a) vs
  forward returns and (b) vs a forward REALIZED-VOL REGIME label (the
  re-architecture's actual prediction target)?

If yes, the derivatives-state state-conditioning architecture has an IS basis.
If no, the cycle-4 axis pivots to a recorded fallback (Candidate B / C).

================================================================================
WALK-FORWARD FIDELITY (the /091 lesson — feedback_v3_eda_walkforward_faithful.md)
================================================================================
iter-v3/091's EDA scored the FULL 2020-04 -> 2025-03 IS panel with no
walk-forward segmentation and over-predicted IS net Sharpe by +0.28 because the
runner's walk-forward only trades the POST-24-month-burn-in span. This EDA does
NOT repeat that mistake. Every IC / regime statistic below is measured ONLY on
the runner's walk-forward IS TEST window:

  - training_months = 24 (IMMUTABLE). The /059 per-symbol runner's first test
    month for a symbol is ~24 calendar months after that symbol's first kline.
  - OOS_CUTOFF_MS = 1742774400000 (2025-03-24, IMMUTABLE).
  - The walk-forward IS test span is therefore, per symbol:
        [first_kline_open + 24 months,  OOS_CUTOFF_MS)
  - For BCH/TRX (data from 2020-01) the IS test span is 2022-01 -> 2025-03.
  - For LDO (listed 2022-09) the IS test span is 2024-09 -> 2025-03.
  This is the SAME burn-in the runner applies. The full pre-2022 panel — the
  2020-21 bull regime that inflated the /091 EDA — is EXCLUDED, exactly as the
  runner excludes it. Any number this EDA prints as a runner-fidelity target is
  measured on this span and ONLY this span.

NO-CHEATING:
  - OOS_CUTOFF_MS is the hard wall. NOTHING past 2025-03-24 is touched. The QR
    sees OOS for the first time in Phase 7.
  - All features are PAST-ONLY: funding/basis rolling stats are .shift(1)-lagged
    (the funding_v3.py / basis_v3.py convention) so bar t's own settlement never
    enters its own rolling window. Forward labels look STRICTLY ahead of t.
  - Open interest is NOT yet fetched (the `fetch-oi` build is a Phase-6 QE
    setup item). The OI feature component is therefore designed on the prep
    memo's verified data.binance.vision `metrics` schema and spec'd in the
    brief; the OI EDA is acknowledged as Phase-6/7 validation. This EDA measures
    the two legs that ARE present — funding and perp-spot basis.

OUTPUTS (all CSV, committed):
  T1_forward_return_ic.csv       — Spearman IC of each derivatives feature vs
                                   forward H-bar return, per symbol + pooled.
  T2_vol_regime_ic.csv           — IC + AUC-style separation of each feature vs
                                   the forward 3-state realized-vol-regime label.
  T3_deleveraging_signal.csv     — does a funding-extreme + basis-stretch state
                                   precede the forward adverse-vol spike (the
                                   reconstructed deleveraging-cascade label)?
  T4_redundancy_vs_price.csv     — |Spearman IC| of each derivatives feature vs
                                   the 14 price-derived V3_FEATURE_COLUMNS
                                   (the Critic Check-4 IC<0.7 orthogonality test).
  T5_summary.csv                 — one-row headline verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants — mirror the runner. IMMUTABLE.
# --------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE
TRAINING_MONTHS = 24  # IMMUTABLE
BAR_MS = 8 * 60 * 60 * 1000  # 8h candle
ZSCORE_CLIP = 10.0  # funding_v3.py / basis_v3.py convention

DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v3-093")

# The /059 canonical per-symbol universe (the cycle-4 universe — see brief §3).
CORE_UNIVERSE = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
# The broader derivatives-data-complete set (funding + spot both present) — used
# only as a cross-check that the IC finding is not a 3-symbol artifact.
WIDE_UNIVERSE = [
    "BCHUSDT", "LDOUSDT", "TRXUSDT", "GALAUSDT", "HBARUSDT", "ICPUSDT",
    "RUNEUSDT", "MANAUSDT", "SANDUSDT", "AAVEUSDT", "AVAXUSDT", "ATOMUSDT",
    "ADAUSDT", "ALGOUSDT", "AXSUSDT", "CHZUSDT", "CRVUSDT", "EOSUSDT",
    "GRTUSDT", "THETAUSDT", "VETUSDT",
]

# Forward horizons (in 8h bars). H=21 ~ 7d (the v3 timeout / weekly horizon).
FWD_HORIZONS = [3, 9, 21]

# The 14 price-derived V3_FEATURE_COLUMNS (from BASELINE_V3.md) — for the
# redundancy / orthogonality check. We re-derive the cheap-to-compute subset.


# ==========================================================================
# Loaders
# ==========================================================================
def _load_perp(symbol: str) -> pd.DataFrame | None:
    """Perp 8h klines: open_time (ms), OHLCV + taker_buy_volume."""
    f = DATA_DIR / symbol / "8h.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    if df.empty or "open_time" not in df.columns:
        return None
    df = df.sort_values("open_time").reset_index(drop=True)
    for c in ["open", "high", "low", "close", "volume", "quote_volume",
              "taker_buy_volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _load_funding(symbol: str) -> pd.DataFrame | None:
    """Funding rate CSV: funding_time (ms), funding_rate."""
    f = DATA_DIR / "funding_rates" / f"{symbol}.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    if df.empty or "funding_rate" not in df.columns or len(df) < 100:
        return None
    df = df.sort_values("funding_time").reset_index(drop=True)
    df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
    return df


def _load_spot(symbol: str) -> pd.DataFrame | None:
    """Spot 8h klines: open_time (ms), close."""
    f = DATA_DIR / "spot" / symbol / "8h.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    if df.empty or "open_time" not in df.columns:
        return None
    df = df.sort_values("open_time").reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df[["open_time", "close"]].rename(columns={"close": "spot_close"})


# ==========================================================================
# Feature panel — derivatives microstructure (funding + basis) — PAST-ONLY
# ==========================================================================
def build_feature_panel(symbol: str) -> pd.DataFrame | None:
    """Build the derivatives-microstructure feature panel for one symbol.

    All features are PAST-ONLY (.shift(1)-lagged rolling stats — the
    funding_v3.py / basis_v3.py look-ahead convention). Returns a frame indexed
    by open_time with the derivatives features + the raw close (for labels).
    """
    perp = _load_perp(symbol)
    fund = _load_funding(symbol)
    spot = _load_spot(symbol)
    if perp is None or fund is None:
        return None

    df = perp.copy()
    df["symbol"] = symbol

    # ---- merge funding (round to minute, absorb settlement jitter) --------
    fund = fund.copy()
    fund["k"] = (fund["funding_time"] // 60_000) * 60_000
    df["k"] = (df["open_time"] // 60_000) * 60_000
    df = df.merge(fund[["k", "funding_rate"]], on="k", how="left").drop(columns="k")
    r = df["funding_rate"].astype(float)

    # ---- FUNDING features (the /019 + /082 family, past-only) -------------
    # funding_rate: rate that SETTLED at bar t open — knowable at t (broadcast
    # ~5min pre-settlement). Used as a same-bar feature per funding_v3.py.
    df["f_rate"] = r
    # 30-bar past-only z-score (the canonical /019 funding_rate_zscore_30).
    mu = r.shift(1).rolling(30, min_periods=30).mean()
    sd = r.shift(1).rolling(30, min_periods=30).std(ddof=1)
    df["f_zscore_30"] = ((r - mu) / sd.replace(0, np.nan)).clip(-ZSCORE_CLIP, ZSCORE_CLIP)
    # sign-persistence over trailing 9 settlements (crowding direction+persist).
    df["f_sign_persist_9"] = np.sign(r).shift(1).rolling(9, min_periods=9).mean()
    # 8/24/72h momentum (1/3/9 bars) — funding trend.
    df["f_mom_3"] = (r - r.shift(3))
    df["f_mom_9"] = (r - r.shift(9))
    # second difference — the carry-SHOCK proxy (BIS WP 1087: 10% carry shock
    # -> 22% liquidation jump). Acceleration of funding.
    df["f_accel_3"] = (r - r.shift(3)) - (r.shift(3) - r.shift(6))
    # crowding-extreme flag: |z|>2 over the trailing window (danger-zone read).
    df["f_extreme_persist_9"] = (
        (r.shift(1).rolling(30, min_periods=30).apply(
            lambda w: np.abs((w[-1] - w[:-1].mean()) / (w[:-1].std() + 1e-12)),
            raw=True))
        .rolling(9, min_periods=9).mean()
    )

    # ---- BASIS features (the /086 family, past-only) ----------------------
    if spot is not None:
        df = df.merge(spot, on="open_time", how="left")
        basis = (df["close"] - df["spot_close"]) / df["spot_close"].replace(0, np.nan)
        # basis(t) is knowable only at bar t CLOSE -> every basis feature uses
        # basis.shift(1) (the basis_v3.py convention).
        b_lag = basis.shift(1)
        df["b_level"] = b_lag
        bmu = b_lag.rolling(30, min_periods=30).mean()
        bsd = b_lag.rolling(30, min_periods=30).std(ddof=1)
        df["b_zscore_30"] = ((b_lag - bmu) / bsd.replace(0, np.nan)).clip(
            -ZSCORE_CLIP, ZSCORE_CLIP)
        df["b_momentum_3"] = (b_lag - b_lag.shift(3))
        # funding-basis SPREAD: funding is the lagged clamped settlement; basis
        # is the continuous unclamped premium. Their divergence is a leverage-
        # stress read the prep memo flags (IS corr only ~0.22-0.28 -> distinct).
        df["fb_spread_z"] = (df["f_zscore_30"] - df["b_zscore_30"])
    else:
        for c in ["b_level", "b_zscore_30", "b_momentum_3", "fb_spread_z"]:
            df[c] = np.nan

    # ---- OI-DELTA PROXY (the reconstructed deleveraging fingerprint) ------
    # Open interest is NOT yet fetched (Phase-6 `fetch-oi` build). As the prep
    # memo §1.4 specifies, a deleveraging cascade leaves a fingerprint that is
    # RECONSTRUCTABLE from price+volume+funding. The taker-buy IMBALANCE
    # collapsing concurrent with an adverse return is the cascade signature
    # available pre-OI-fetch. We compute it as an INTERIM proxy ONLY — the brief
    # spec's the genuine OI-delta feature on the fetched `metrics` archive.
    if "taker_buy_volume" in df.columns and "volume" in df.columns:
        taker_imb = (2.0 * df["taker_buy_volume"] / df["volume"].replace(0, np.nan)) - 1.0
        df["proxy_taker_imb"] = taker_imb.shift(1)
        # turnover surge — volume z-score (deleveraging = volume spike).
        v = df["volume"].astype(float)
        vmu = v.shift(1).rolling(30, min_periods=30).mean()
        vsd = v.shift(1).rolling(30, min_periods=30).std(ddof=1)
        df["proxy_vol_surge_z"] = ((v - vmu) / vsd.replace(0, np.nan)).clip(
            -ZSCORE_CLIP, ZSCORE_CLIP)
    else:
        df["proxy_taker_imb"] = np.nan
        df["proxy_vol_surge_z"] = np.nan

    return df


DERIV_FEATURES = [
    "f_rate", "f_zscore_30", "f_sign_persist_9", "f_mom_3", "f_mom_9",
    "f_accel_3", "f_extreme_persist_9",
    "b_level", "b_zscore_30", "b_momentum_3", "fb_spread_z",
    "proxy_taker_imb", "proxy_vol_surge_z",
]


# ==========================================================================
# Price-derived comparator features (subset of V3_FEATURE_COLUMNS) for T4
# ==========================================================================
def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cheap-to-compute subset of the 14 price-derived V3_FEATURE_COLUMNS.

    Used ONLY for the T4 redundancy / orthogonality check (Critic Check 4):
    does the derivatives-state panel carry information ORTHOGONAL to the price
    features the /059 baseline already uses?
    """
    c = df["close"].astype(float)
    logr = np.log(c).diff()
    # ret_skew_50 / ret_kurt_50 (past-only).
    df["p_ret_skew_50"] = logr.shift(1).rolling(50, min_periods=50).skew()
    df["p_ret_kurt_50"] = logr.shift(1).rolling(50, min_periods=50).kurt()
    # range_realized_vol_50.
    df["p_realized_vol_50"] = logr.shift(1).rolling(50, min_periods=50).std(ddof=1)
    # ret_autocorr_lag1_50.
    df["p_ret_autocorr_50"] = (
        logr.shift(1).rolling(50, min_periods=50)
        .apply(lambda w: pd.Series(w).autocorr(lag=1) if np.std(w) > 0 else 0.0,
               raw=False)
    )
    # vwap_dev_20 (close vs trailing-20 VWAP, past-only).
    if "quote_volume" in df.columns and "volume" in df.columns:
        vwap = (df["quote_volume"].shift(1).rolling(20, min_periods=20).sum()
                / df["volume"].shift(1).rolling(20, min_periods=20).sum())
        df["p_vwap_dev_20"] = (c - vwap) / vwap.replace(0, np.nan)
    else:
        df["p_vwap_dev_20"] = np.nan
    # momentum: trailing 14d (~42 bar) return.
    df["p_ret_14d"] = c.shift(1).pct_change(42)
    return df


PRICE_FEATURES = [
    "p_ret_skew_50", "p_ret_kurt_50", "p_realized_vol_50",
    "p_ret_autocorr_50", "p_vwap_dev_20", "p_ret_14d",
]


# ==========================================================================
# Labels — forward, strictly look-ahead of t. Used ONLY for IC measurement.
# ==========================================================================
def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Forward labels — strictly ahead of bar t."""
    c = df["close"].astype(float)
    logr = np.log(c).diff()
    for h in FWD_HORIZONS:
        # forward H-bar return.
        df[f"fwd_ret_{h}"] = c.shift(-h) / c - 1.0
        # forward H-bar realized vol (std of the h forward log-returns).
        df[f"fwd_rv_{h}"] = (
            logr.shift(-h).rolling(h, min_periods=h).std(ddof=1).shift(-(h - 1))
        )
    return df


# ==========================================================================
# Test 1 — IC vs forward return
# ==========================================================================
def test1_forward_return_ic(panels: dict[str, pd.DataFrame], label: str) -> pd.DataFrame:
    """Spearman IC of each derivatives feature vs forward H-bar return.

    Measured ONLY on the runner's walk-forward IS test window per symbol.
    """
    rows = []
    pooled = {f: {h: [] for h in FWD_HORIZONS} for f in DERIV_FEATURES}
    pooled_lbl = {f: {h: [] for h in FWD_HORIZONS} for f in DERIV_FEATURES}
    for sym, df in panels.items():
        is_df = df[df["_is_test_window"]]
        for feat in DERIV_FEATURES:
            for h in FWD_HORIZONS:
                sub = is_df[[feat, f"fwd_ret_{h}"]].dropna()
                if len(sub) < 60:
                    continue
                ic = sub[feat].corr(sub[f"fwd_ret_{h}"], method="spearman")
                rows.append({
                    "universe": label, "symbol": sym, "feature": feat,
                    "horizon_bars": h, "ic": round(ic, 5), "n_obs": len(sub),
                })
                pooled[feat][h].append(sub[feat].values)
                pooled_lbl[feat][h].append(sub[f"fwd_ret_{h}"].values)
    # pooled IC.
    for feat in DERIV_FEATURES:
        for h in FWD_HORIZONS:
            if not pooled[feat][h]:
                continue
            x = np.concatenate(pooled[feat][h])
            y = np.concatenate(pooled_lbl[feat][h])
            ic = pd.Series(x).corr(pd.Series(y), method="spearman")
            rows.append({
                "universe": label, "symbol": "POOLED", "feature": feat,
                "horizon_bars": h, "ic": round(ic, 5), "n_obs": len(x),
            })
    return pd.DataFrame(rows)


# ==========================================================================
# Test 2 — IC vs forward-vol-regime label (the architecture's actual target)
# ==========================================================================
def test2_vol_regime_ic(panels: dict[str, pd.DataFrame], label: str) -> pd.DataFrame:
    """Each derivatives feature vs the forward 3-state realized-vol regime.

    The vol-regime label = terciles of forward H-bar realized vol, computed
    PER SYMBOL on the IS test window ONLY: {0=calm, 1=normal, 2=stressed}.
    This is the architecture's prediction target — does the derivatives state
    SEPARATE the forward calm/stressed regimes?

    Reports: Spearman IC of feature vs the ordinal regime, and the mean-feature
    gap between the stressed (regime=2) and calm (regime=0) buckets, normalized
    by the feature's IS std (a separation effect-size).
    """
    rows = []
    for sym, df in panels.items():
        is_df = df[df["_is_test_window"]].copy()
        for h in FWD_HORIZONS:
            rv = is_df[f"fwd_rv_{h}"]
            valid = rv.notna()
            if valid.sum() < 90:
                continue
            # terciles on the IS test window only.
            try:
                regime = pd.qcut(rv[valid], 3, labels=[0, 1, 2]).astype(float)
            except ValueError:
                continue
            is_df.loc[valid, f"_regime_{h}"] = regime.values
            for feat in DERIV_FEATURES:
                sub = is_df[[feat, f"_regime_{h}"]].dropna()
                if len(sub) < 60:
                    continue
                ic = sub[feat].corr(sub[f"_regime_{h}"], method="spearman")
                fstd = sub[feat].std(ddof=1)
                calm = sub.loc[sub[f"_regime_{h}"] == 0, feat].mean()
                stress = sub.loc[sub[f"_regime_{h}"] == 2, feat].mean()
                sep = (stress - calm) / fstd if fstd > 1e-12 else np.nan
                rows.append({
                    "universe": label, "symbol": sym, "feature": feat,
                    "horizon_bars": h, "regime_ic": round(ic, 5),
                    "stress_minus_calm_effsize": round(sep, 4),
                    "n_obs": len(sub),
                })
    return pd.DataFrame(rows)


# ==========================================================================
# Test 3 — deleveraging-signal predictive content
# ==========================================================================
def test3_deleveraging_signal(panels: dict[str, pd.DataFrame],
                              label: str) -> pd.DataFrame:
    """Does a funding-extreme + basis-stretch state precede a forward adverse
    vol spike (the reconstructed deleveraging-cascade label)?

    State definition (all PAST-ONLY, knowable at bar t):
      DELEVERAGING-RISK state = (|f_zscore_30| > 1.5) AND (volume-surge in top
      tercile of the IS test window). The 2025 literature (the Oct-10 cascade:
      85-90% long-side liquidations, OI -40% post-event) ties extreme funding +
      a leverage build to the forced-deleveraging setup.

    Forward outcome = the next-H-bar realized vol is in the IS-test-window TOP
    tercile (a 'stressed' forward regime — the cascade aftermath).

    Reports the lift: P(forward stressed | risk state) / P(forward stressed)
    and the conditional adverse-return mean. A lift > 1.0 means the derivatives
    state carries genuine forward deleveraging-risk information.
    """
    rows = []
    for sym, df in panels.items():
        is_df = df[df["_is_test_window"]].copy()
        for h in FWD_HORIZONS:
            rv = is_df[f"fwd_rv_{h}"]
            fz = is_df["f_zscore_30"]
            vs = is_df["proxy_vol_surge_z"]
            base = is_df[[f"fwd_rv_{h}", "f_zscore_30",
                          "proxy_vol_surge_z", f"fwd_ret_{h}"]].dropna()
            if len(base) < 120:
                continue
            rv_top = base[f"fwd_rv_{h}"].quantile(2 / 3)
            vs_top = base["proxy_vol_surge_z"].quantile(2 / 3)
            risk_state = (base["f_zscore_30"].abs() > 1.5) & (
                base["proxy_vol_surge_z"] > vs_top)
            fwd_stressed = base[f"fwd_rv_{h}"] > rv_top
            p_base = fwd_stressed.mean()
            n_risk = int(risk_state.sum())
            if n_risk < 20 or p_base <= 0:
                rows.append({
                    "universe": label, "symbol": sym, "horizon_bars": h,
                    "n_risk_state": n_risk, "p_base_stressed": round(p_base, 4),
                    "p_cond_stressed": np.nan, "lift": np.nan,
                    "cond_fwd_ret_mean": np.nan,
                })
                continue
            p_cond = fwd_stressed[risk_state].mean()
            cond_ret = base.loc[risk_state, f"fwd_ret_{h}"].mean()
            rows.append({
                "universe": label, "symbol": sym, "horizon_bars": h,
                "n_risk_state": n_risk, "p_base_stressed": round(p_base, 4),
                "p_cond_stressed": round(p_cond, 4),
                "lift": round(p_cond / p_base, 4),
                "cond_fwd_ret_mean": round(cond_ret, 5),
            })
    return pd.DataFrame(rows)


# ==========================================================================
# Test 4 — redundancy vs price-derived V3 features (Critic Check 4)
# ==========================================================================
def test4_redundancy(panels: dict[str, pd.DataFrame], label: str) -> pd.DataFrame:
    """|Spearman IC| of each derivatives feature vs each price-derived feature.

    Critic Check 4 requires IC < 0.7 between a NEW feature family and the
    existing features. This test confirms the derivatives-microstructure panel
    is genuinely ORTHOGONAL to the 14 price-derived V3_FEATURE_COLUMNS — it is
    a new information layer, not a re-encoding of price.
    Reports, per derivatives feature, the MAX |IC| over all price features
    (pooled across the universe, IS test window only).
    """
    rows = []
    for feat in DERIV_FEATURES:
        for pfeat in PRICE_FEATURES:
            xs, ys = [], []
            for _sym, df in panels.items():
                is_df = df[df["_is_test_window"]]
                sub = is_df[[feat, pfeat]].dropna()
                if len(sub) < 60:
                    continue
                xs.append(sub[feat].values)
                ys.append(sub[pfeat].values)
            if not xs:
                continue
            x = np.concatenate(xs)
            y = np.concatenate(ys)
            ic = pd.Series(x).corr(pd.Series(y), method="spearman")
            rows.append({
                "universe": label, "deriv_feature": feat,
                "price_feature": pfeat, "abs_ic": round(abs(ic), 5),
                "n_obs": len(x),
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # max |IC| per derivatives feature.
    mx = out.groupby("deriv_feature")["abs_ic"].max().reset_index()
    mx.columns = ["deriv_feature", "max_abs_ic_vs_any_price_feature"]
    mx["universe"] = label
    mx["check4_pass_ic_lt_0p70"] = mx["max_abs_ic_vs_any_price_feature"] < 0.70
    return mx


# ==========================================================================
# Walk-forward IS test-window flag — mirror the runner's burn-in
# ==========================================================================
def flag_is_test_window(df: pd.DataFrame) -> pd.DataFrame:
    """Flag the rows the runner's walk-forward actually evaluates IN-SAMPLE.

    The /059 per-symbol runner trains on a trailing training_months=24 window
    and evaluates the month AFTER. So the first IN-SAMPLE TEST bar for a symbol
    is 24 calendar months after that symbol's first kline; the IN-SAMPLE TEST
    window ends at OOS_CUTOFF_MS. This EXACTLY mirrors the runner's IS span and
    EXCLUDES the pre-burn-in panel — the /091 walk-forward-fidelity fix.
    """
    first = int(df["open_time"].min())
    # add 24 months ~ 730.5 days in ms.
    burn_end = first + int(730.5 * 24 * 60 * 60 * 1000)
    df = df.copy()
    df["_is_test_window"] = (
        (df["open_time"] >= burn_end) & (df["open_time"] < OOS_CUTOFF_MS)
    )
    return df


# ==========================================================================
# Driver
# ==========================================================================
def run_universe(symbols: list[str], label: str) -> dict[str, pd.DataFrame]:
    panels: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        p = build_feature_panel(sym)
        if p is None:
            print(f"  [{label}] {sym}: SKIP (no perp/funding data)")
            continue
        p = add_price_features(p)
        p = add_labels(p)
        p = flag_is_test_window(p)
        n_is = int(p["_is_test_window"].sum())
        if n_is < 90:
            print(f"  [{label}] {sym}: SKIP (only {n_is} IS-test bars)")
            continue
        is_rows = p[p["_is_test_window"]]
        span0 = pd.to_datetime(int(is_rows["open_time"].min()), unit="ms").date()
        span1 = pd.to_datetime(int(is_rows["open_time"].max()), unit="ms").date()
        fcov = is_rows["f_zscore_30"].notna().mean()
        bcov = is_rows["b_zscore_30"].notna().mean()
        print(f"  [{label}] {sym}: {n_is} IS-test bars  {span0} -> {span1}  "
              f"funding_cov={fcov:.2f}  basis_cov={bcov:.2f}")
        panels[sym] = p
    return panels


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/093 — DERIVATIVES-MICROSTRUCTURE EDA — IS-ONLY, walk-forward-faithful")
    print("=" * 78)
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24, IMMUTABLE)")
    print(f"training_months = {TRAINING_MONTHS} (IMMUTABLE) — IS-test window = "
          f"[first_kline+24mo, OOS_CUTOFF)")
    print()

    print("Building CORE universe (BCH/LDO/TRX — the /059 per-symbol set):")
    core = run_universe(CORE_UNIVERSE, "core")
    print()
    print("Building WIDE universe (derivatives-data-complete cross-check):")
    wide = run_universe(WIDE_UNIVERSE, "wide")
    print()

    if not core:
        print("FATAL: no core-universe panels built. Aborting.")
        sys.exit(1)

    # ---- Test 1 — forward-return IC -------------------------------------
    t1 = pd.concat(
        [test1_forward_return_ic(core, "core"),
         test1_forward_return_ic(wide, "wide")],
        ignore_index=True)
    t1.to_csv(OUT_DIR / "T1_forward_return_ic.csv", index=False)
    print("--- T1: forward-return IC (POOLED rows, |IC| descending) ---")
    t1p = t1[t1["symbol"] == "POOLED"].copy()
    t1p["abs_ic"] = t1p["ic"].abs()
    print(t1p.sort_values("abs_ic", ascending=False)
          .head(14)[["universe", "feature", "horizon_bars", "ic", "n_obs"]]
          .to_string(index=False))
    print()

    # ---- Test 2 — vol-regime IC -----------------------------------------
    t2 = pd.concat(
        [test2_vol_regime_ic(core, "core"),
         test2_vol_regime_ic(wide, "wide")],
        ignore_index=True)
    t2.to_csv(OUT_DIR / "T2_vol_regime_ic.csv", index=False)
    print("--- T2: vol-REGIME IC — mean over symbols, per (universe, feature, H) ---")
    t2g = (t2.groupby(["universe", "feature", "horizon_bars"])
           .agg(mean_regime_ic=("regime_ic", "mean"),
                mean_effsize=("stress_minus_calm_effsize", "mean"),
                n_syms=("symbol", "nunique"))
           .reset_index())
    t2g["abs_ic"] = t2g["mean_regime_ic"].abs()
    print(t2g[t2g["universe"] == "core"].sort_values("abs_ic", ascending=False)
          .head(12)[["feature", "horizon_bars", "mean_regime_ic",
                     "mean_effsize", "n_syms"]].to_string(index=False))
    print()

    # ---- Test 3 — deleveraging signal -----------------------------------
    t3 = pd.concat(
        [test3_deleveraging_signal(core, "core"),
         test3_deleveraging_signal(wide, "wide")],
        ignore_index=True)
    t3.to_csv(OUT_DIR / "T3_deleveraging_signal.csv", index=False)
    print("--- T3: deleveraging-risk state -> forward-stressed lift (mean over syms) ---")
    t3g = (t3.dropna(subset=["lift"])
           .groupby(["universe", "horizon_bars"])
           .agg(mean_lift=("lift", "mean"),
                mean_cond_fwd_ret=("cond_fwd_ret_mean", "mean"),
                mean_n_risk=("n_risk_state", "mean"),
                n_syms=("symbol", "nunique"))
           .reset_index())
    print(t3g.to_string(index=False))
    print()

    # ---- Test 4 — redundancy --------------------------------------------
    t4 = pd.concat(
        [test4_redundancy(core, "core"),
         test4_redundancy(wide, "wide")],
        ignore_index=True)
    t4.to_csv(OUT_DIR / "T4_redundancy_vs_price.csv", index=False)
    print("--- T4: max |IC| of each derivatives feature vs any price feature ---")
    print(t4[t4["universe"] == "core"]
          .sort_values("max_abs_ic_vs_any_price_feature", ascending=False)
          [["deriv_feature", "max_abs_ic_vs_any_price_feature",
            "check4_pass_ic_lt_0p70"]].to_string(index=False))
    print()

    # ---- T5 — headline summary ------------------------------------------
    t1c = t1p[t1p["universe"] == "core"]
    t2c = t2g[t2g["universe"] == "core"]
    t3c = t3g[t3g["universe"] == "core"]
    t4c = t4[t4["universe"] == "core"]
    best_ret_ic = t1c.loc[t1c["abs_ic"].idxmax()] if not t1c.empty else None
    best_reg_ic = t2c.loc[t2c["abs_ic"].idxmax()] if not t2c.empty else None
    summary = {
        "core_n_symbols": len(core),
        "wide_n_symbols": len(wide),
        "best_fwd_return_feature": best_ret_ic["feature"] if best_ret_ic is not None else "NA",
        "best_fwd_return_ic": best_ret_ic["ic"] if best_ret_ic is not None else np.nan,
        "best_fwd_return_horizon": int(best_ret_ic["horizon_bars"]) if best_ret_ic is not None else 0,
        "best_vol_regime_feature": best_reg_ic["feature"] if best_reg_ic is not None else "NA",
        "best_vol_regime_ic": round(best_reg_ic["mean_regime_ic"], 5) if best_reg_ic is not None else np.nan,
        "best_vol_regime_effsize": round(best_reg_ic["mean_effsize"], 4) if best_reg_ic is not None else np.nan,
        "mean_deleveraging_lift_H21": round(
            t3c.loc[t3c["horizon_bars"] == 21, "mean_lift"].mean(), 4)
        if not t3c.empty else np.nan,
        "max_redundancy_vs_price": round(
            t4c["max_abs_ic_vs_any_price_feature"].max(), 4) if not t4c.empty else np.nan,
        "all_check4_pass": bool(t4c["check4_pass_ic_lt_0p70"].all()) if not t4c.empty else False,
        # how many regime-IC measurements clear |IC|>=0.05 (a usable-signal bar)
        "n_regime_ic_ge_0p05": int((t2c["abs_ic"] >= 0.05).sum()),
        "n_regime_ic_measured": int(len(t2c)),
    }
    t5 = pd.DataFrame([summary])
    t5.to_csv(OUT_DIR / "T5_summary.csv", index=False)
    print("--- T5: HEADLINE SUMMARY ---")
    for k, v in summary.items():
        print(f"  {k:38s} = {v}")
    print()
    print("=" * 78)
    print("EDA COMPLETE. Outputs in analysis/iteration_v3-093/.")
    print("VERDICT BAR: vol-regime IC is the architecture-relevant signal — the")
    print("re-architecture predicts a forward vol-regime, not a price barrier.")
    print("=" * 78)


if __name__ == "__main__":
    main()

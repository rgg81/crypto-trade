"""ml_v2 — leak-safe cross-sectional LightGBM return predictor for the rank-21-40 mid-cap L/S band.

iter-v2-003 EXPLORATION. Replaces the hand-set trend+carry+xs blend with a fast LightGBM that learns
walk-forward each coin's RELATIVE forward return within the band (cross-sectionally demeaned), then
turns the prediction into a centered within-band rank signal that the engine `run_book_from_signal`
runs through the SAME inverse-vol / gross-norm / lag / band / eligexit / vol-target pipeline.

LEAK-SAFETY (the critical contract, brief §2.3):
  - every FEATURE at candle t uses only data <= t (the panels are built with the SAME past-only
    rolling/shift conventions as engine_v2._signals; cross-sectional features rank within the band
    at t on past-only inputs).
  - the LABEL is a FORWARD return; it appears ONLY in training rows, all strictly < the test month,
    with an embargo GAP so the last train label cannot reach into the test month.
  - predictions for a test month M come from a model trained ONLY on data before M (with the gap).

The leak surface is guarded by tests/test_portfolio_v2.py::test_ml_walkforward_* (window-bound check
+ future-perturbation invariance of the pre-cutoff ML signal).

Public API:
  build_feature_panel(coins, *, rank_lo, rank_hi, season, liq_win) -> (long_df, elig, index, cols)
  walk_forward_predict(long_df, elig, *, ...) -> (pred_panel, importances, covered_months, skipped)
  pred_to_signal(pred_panel, elig) -> signal_panel    # centered within-band rank, dollar-neutral
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import engine_v2 as e2
from . import universe_v2 as uv

# ---- walk-forward / model constants ---------------------------------------------------------
TRAIN_MONTHS = e2.TRAIN_MONTHS  # 24 — same train window as the anchor's λ stitch
GAP_CANDLES = (
    e2.GAP_CANDLES
)  # 3 — embargo so the last train label (t+1) cannot reach the test month
MIN_TRAIN_ROWS = 1000  # below this a month cold-starts (falls back to the anchor signal)
STEP_MS = e2.STEP_MS

# fast model (user directive: ~200 trees, depth <= 6, lr 0.05, 1-3 seeds; no giant search)
N_ESTIMATORS = 200
NUM_LEAVES = 31
MAX_DEPTH = 6
LEARNING_RATE = 0.05
SUBSAMPLE = 0.8
COLSAMPLE = 0.8
MIN_CHILD_SAMPLES = 50
SEEDS = (42, 123, 777)  # 3-seed mean for prediction stability (kept fast)

# feature horizons
TREND_H = (7, 21, 42, 84, 168)
XS_L = (21, 84)
FUND_WIN = e2.M_FUND  # 9
RVOL_WIN = 84
REGIME_WIN = 63  # trailing realized-Sharpe window of the trend anchor net (past-only regime proxy)

# the ordered feature column list (pinned — LightGBM importance is reported against THIS order).
FEATURE_COLUMNS: list[str] = (
    [f"ret_{h}" for h in TREND_H]
    + [f"sgn_ret_{h}" for h in TREND_H]
    + ["accel_21_84", "accel_42_168"]
    + [f"xsrank_{ell}" for ell in XS_L]
    + ["carry_mean9", "fund_level", "sgn_carry9"]
    + ["rvol_84", "mom21_volscaled"]
    + ["rank_rvol84", "rank_carry", "relstrength_84"]
    + ["cohort_trendabs", "cohort_rvol_median", "regime_trend_sharpe"]
)


# ---- anchor trend+carry signal (the cold-start fallback + a baseline) ------------------------
def anchor_signal_panel(
    coins: dict,
    *,
    rank_lo: float,
    rank_hi: float,
    season: int | None,
    liq_win: int = uv.LIQ_WIN,
) -> pd.DataFrame:
    """The deployed anchor's per-candle trend+carry signal numerator, BEFORE /rvol — i.e. the `tc`
    blend at the canonical walk-forward λ is a per-month choice, so for a single fixed cold-start
    fallback we use the SAME (1-λ)·trend + λ·carry form at the LAM_GRID midpoint λ=0.25 (a fixed,
    pre-registered, OOS-blind constant). This is fed to run_book_from_signal so the cold-start
    months are never undefined and the book stays the SAME class of object as the ML months."""
    panel = e2.build_panel(coins, liq_win=liq_win)
    sig = e2._signals(panel)
    lam = 0.25
    tc = (1 - lam) * sig["trend"] + lam * sig["carry"]
    return tc


def _anchor_net_for_regime(
    coins: dict,
    *,
    rank_lo: float,
    rank_hi: float,
    season: int | None,
    liq_win: int,
    slip_bps_fn,
) -> pd.Series:
    """Past-only realized net of the pure-trend (λ=0) book on the band — the regime proxy source.

    We use the λ=0 fixed_lambda_book net so the trailing realized Sharpe is a clean trend-health
    statistic. It is computed once on the FULL sample; the rolling Sharpe is
    then .shift(1)-lagged at use, so it stays strictly past-only candle-by-candle."""
    book = e2.fixed_lambda_book(
        coins,
        lam=0.0,
        rank_lo=rank_lo,
        rank_hi=rank_hi,
        season=season,
        slip_bps_fn=slip_bps_fn,
        liq_win=liq_win,
    )
    return book["net"]


# ---- feature panel (ALL past-only) ----------------------------------------------------------
def build_feature_panel(
    coins: dict,
    *,
    rank_lo: float,
    rank_hi: float,
    season: int | None,
    liq_win: int = uv.LIQ_WIN,
    slip_bps_fn=None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex, list[str]]:
    """Build a tidy long frame (coin, candle, FEATURE_COLUMNS..., label) — every feature knowable at
    close[t]; the label is the FORWARD demeaned return (brief §2.2), tagged for training-only use.

    Returns (long_df, elig, opens_index, cols). `long_df` is indexed by a (candle, coin) MultiIndex,
    restricted to eligible-band rows (the model only ever sees band members). `elig` / `opens_index`
    / `cols` are the engine-grid eligibility + axes for downstream alignment.
    """
    panel = e2.build_panel(coins, liq_win=liq_win)
    close = panel["close"]
    opens = panel["opens"]
    fund = panel["fund"]
    cols = panel["cols"]
    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=opens.index, columns=cols)
        .fillna(False)
    )

    feats: dict[str, pd.DataFrame] = {}

    # --- Trend: ret_h + sign(ret_h), past-only ---
    rets = {}
    for h in TREND_H:
        r = close / close.shift(h) - 1.0
        rets[h] = r
        feats[f"ret_{h}"] = r
        feats[f"sgn_ret_{h}"] = np.sign(r)

    # --- Momentum acceleration ---
    feats["accel_21_84"] = rets[21] - rets[84]
    feats["accel_42_168"] = rets[42] - rets[168]

    # --- XS rank (centered within-band return-rank, past-only) at L in {21,84} ---
    for ell in XS_L:
        xs, _mom = e2._xsmom(close, elig, ell)  # centered in [-0.5,+0.5], 0.0 outside band
        feats[f"xsrank_{ell}"] = xs.where(elig)

    # --- Carry ---
    carry_mean9 = fund.rolling(FUND_WIN).mean()
    feats["carry_mean9"] = carry_mean9
    feats["fund_level"] = fund
    feats["sgn_carry9"] = np.sign(carry_mean9)

    # --- Vol ---
    rvol84 = close.pct_change().rolling(RVOL_WIN).std()
    feats["rvol_84"] = rvol84
    feats["mom21_volscaled"] = rets[21] / rvol84.replace(0.0, np.nan)

    # --- Cross-sectional context within the band (past-only) ---
    feats["rank_rvol84"] = _band_rank(rvol84, elig)
    feats["rank_carry"] = _band_rank(carry_mean9, elig)
    band_med_ret84 = rets[84].where(elig).median(axis=1)
    feats["relstrength_84"] = rets[84].sub(band_med_ret84, axis=0)

    # --- Regime / trend-health (cohort-level, broadcast to every coin) ---
    trend_abs = sum(np.abs(np.sign(close / close.shift(h) - 1.0)) for h in uv.HORIZONS) / len(
        uv.HORIZONS
    )
    cohort_trendabs = trend_abs.where(elig).mean(axis=1)  # band-mean |trend|
    cohort_rvol_median = rvol84.where(elig).median(axis=1)  # band-median rvol
    anchor_net = _anchor_net_for_regime(
        coins,
        rank_lo=rank_lo,
        rank_hi=rank_hi,
        season=season,
        liq_win=liq_win,
        slip_bps_fn=slip_bps_fn,
    )
    # trailing realized Sharpe of the trend anchor net over REGIME_WIN candles, .shift(1) past-only.
    rmean = anchor_net.rolling(REGIME_WIN).mean()
    rstd = anchor_net.rolling(REGIME_WIN).std()
    regime_sharpe = (rmean / rstd.replace(0.0, np.nan)).shift(1).reindex(opens.index)
    cohort_b = pd.DataFrame(
        {
            "cohort_trendabs": cohort_trendabs,
            "cohort_rvol_median": cohort_rvol_median,
            "regime_trend_sharpe": regime_sharpe,
        }
    ).reindex(opens.index)
    for name in ("cohort_trendabs", "cohort_rvol_median", "regime_trend_sharpe"):
        feats[name] = pd.DataFrame(
            np.repeat(cohort_b[name].to_numpy()[:, None], len(cols), axis=1),
            index=opens.index,
            columns=cols,
        )

    # --- Label (FORWARD, demeaned within band, TRAINING-ONLY) ---
    # ret_fwd1[c,t] = open[c,t+2]/open[c,t+1] - 1 : the return the signal at t earns AFTER the
    # engine's .shift(1) lag (signal[t] -> traded weight at t+1 -> open[t+1]->open[t+2] return).
    ret_fwd1 = opens.shift(-2) / opens.shift(-1) - 1.0
    band_mean_fwd = ret_fwd1.where(elig).mean(axis=1)
    label = ret_fwd1.sub(band_mean_fwd, axis=0).where(elig)

    # --- assemble the tidy long frame over eligible-band cells only ---
    long_df = _to_long(feats, label, elig, opens.index, cols)
    return long_df, elig, opens.index, cols


def _band_rank(x: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """Centered within-band rank of `x` (ascending), in [-0.5,+0.5], NaN outside band/where x NaN.

    Same centering as _xsmom: rk=(rank), centered (rk-(n+1)/2)/n over the n RANKED eligible names.
    Kept NaN (not 0-filled) so the model sees a missing cross-sectional context as missing, and the
    band-restriction in _to_long drops un-rankable rows anyway."""
    xr = x.where(elig)
    rk = xr.rank(axis=1)
    n = xr.notna().sum(axis=1)
    centered = rk.sub(n.add(1) / 2.0, axis=0).div(n.replace(0, np.nan), axis=0)
    return centered.where(elig)


def _to_long(
    feats: dict[str, pd.DataFrame],
    label: pd.DataFrame,
    elig: pd.DataFrame,
    index: pd.DatetimeIndex,
    cols: list[str],
) -> pd.DataFrame:
    """Stack the wide feature/label panels into a tidy (candle, coin) MultiIndex frame, restricted
    to eligible-band cells. Feature NaNs are LEFT as NaN (LightGBM handles them); early-life
    coins are removed by the elig mask, not by fill (brief §2.1)."""
    elig_stack = elig.stack()
    keep = elig_stack[elig_stack].index  # (candle, coin) pairs that are in-band
    data = {}
    for name in FEATURE_COLUMNS:
        data[name] = feats[name].reindex(index=index, columns=cols).stack(future_stack=True)
    data["label"] = label.reindex(index=index, columns=cols).stack(future_stack=True)
    long_df = pd.DataFrame(data)
    long_df = long_df.reindex(keep)  # restrict to in-band (candle, coin) cells
    long_df.index = long_df.index.set_names(["candle", "coin"])
    return long_df


# ---- leak-safe walk-forward LightGBM --------------------------------------------------------
def walk_forward_predict(
    long_df: pd.DataFrame,
    elig: pd.DataFrame,
    *,
    min_train_rows: int = MIN_TRAIN_ROWS,
    seeds: tuple[int, ...] = SEEDS,
    verbose: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, list[pd.Period], list[pd.Period]]:
    """Monthly walk-forward LightGBM regression on the tidy band frame. LEAK-SAFE (brief §2.3).

    For each calendar test month M (the SAME month loop semantics as _canonical_book):
      - train rows: candles in [M - TRAIN_MONTHS mo, M - GAP_CANDLES candles), label non-NaN.
        The GAP embargo guarantees the last train label (a t+1 forward return) cannot reach into M.
      - if < min_train_rows train rows -> SKIP M (cold start; the run script falls back to anchor).
      - else fit LGBMRegressor(s) (3-seed mean) on FEATURE_COLUMNS -> label; predict the test-month
        band rows -> pred[c,t].

    Returns (pred_panel, importances, covered_months, skipped_months):
      pred_panel  : wide (candle x coin) DataFrame of raw predictions on covered test-month cells
                    (NaN elsewhere) — fed to pred_to_signal.
      importances : per-month gain importance (rows=months, cols=FEATURE_COLUMNS) for the G4 read.
      covered_months / skipped_months : the month partition (cold-start fraction = skipped / total).
    """
    import lightgbm as lgb

    candles = long_df.index.get_level_values("candle")
    months = pd.PeriodIndex(candles, freq="M").unique().sort_values()

    pred_index = elig.index
    pred_cols = list(elig.columns)
    pred_panel = pd.DataFrame(np.nan, index=pred_index, columns=pred_cols)
    imp_rows: dict[pd.Period, pd.Series] = {}
    covered: list[pd.Period] = []
    skipped: list[pd.Period] = []

    feat_arr = long_df[FEATURE_COLUMNS]
    label_arr = long_df["label"]

    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=GAP_CANDLES * STEP_MS)
        test_hi = (ms + 1).to_timestamp()

        train_mask = (candles >= lo) & (candles < hi) & label_arr.notna().to_numpy()
        test_mask = (candles >= m0) & (candles < test_hi)
        if not test_mask.any():
            continue
        n_train = int(train_mask.sum())
        if n_train < min_train_rows:
            skipped.append(ms)
            if verbose:
                print(f"  {ms}  SKIP (cold start, {n_train} train rows)")
            continue

        x_tr = feat_arr[train_mask]
        y_tr = label_arr[train_mask].to_numpy()
        x_te = feat_arr[test_mask]

        preds = np.zeros(len(x_te))
        gain = np.zeros(len(FEATURE_COLUMNS))
        for sd in seeds:
            model = lgb.LGBMRegressor(
                n_estimators=N_ESTIMATORS,
                num_leaves=NUM_LEAVES,
                max_depth=MAX_DEPTH,
                learning_rate=LEARNING_RATE,
                subsample=SUBSAMPLE,
                subsample_freq=1,
                colsample_bytree=COLSAMPLE,
                min_child_samples=MIN_CHILD_SAMPLES,
                objective="regression_l2",
                random_state=sd,
                n_jobs=-1,
                verbosity=-1,
            )
            model.fit(x_tr, y_tr)
            preds += model.predict(x_te)
            gain += model.booster_.feature_importance(importance_type="gain")
        preds /= len(seeds)
        gain /= len(seeds)

        te_idx = x_te.index  # (candle, coin) pairs
        for (cdl, coin), p in zip(te_idx, preds, strict=True):
            pred_panel.at[cdl, coin] = p
        imp_rows[ms] = pd.Series(gain, index=FEATURE_COLUMNS)
        covered.append(ms)
        if verbose:
            print(f"  {ms}  train={n_train:6d}  test={len(x_te):4d}  pred-done")

    importances = pd.DataFrame(imp_rows).T if imp_rows else pd.DataFrame(columns=FEATURE_COLUMNS)
    return pred_panel, importances, covered, skipped


# ---- prediction -> centered within-band rank signal -----------------------------------------
def pred_to_signal(pred_panel: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """Turn raw predictions into a centered within-band rank signal (brief §2.4): rank pred within
    the eligible band, center (rk-(n+1)/2)/n, .where(elig) — dollar-neutral, SAME scale as _xsmom.

    Coins/candles with no prediction (cold-start months, un-covered cells) stay NaN here; the run
    script overlays the anchor signal on cold-start months BEFORE feeding run_book_from_signal."""
    pr = pred_panel.where(elig)
    rk = pr.rank(axis=1)
    n = pr.notna().sum(axis=1)
    sig = rk.sub(n.add(1) / 2.0, axis=0).div(n.replace(0, np.nan), axis=0).where(elig)
    return sig

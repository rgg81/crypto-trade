"""Cross-sectional relative-value ranking model for iter-v3/091.

Implements the Phase-6 build spec from briefs-v3/iteration_v3-091/research_brief.md
Section 3.

Design:
  - Label: cross-sectional forward-return rank, {0,1,2} graded relevance, H=21 bars.
  - Score (primary — score_mode="model_free"): parameter-free trailing-H-bar return
    close(ts) / close(ts - H*interval) - 1.  No model, no Optuna, no seed.
  - Score (reference — score_mode="trained"): ONE pooled LGBMRanker(lambdarank),
    monthly walk-forward.  Emitted to reference_lgbmranker/ subdirectory.
  - Universe: 22-symbol XS_UNIVERSE of liquid non-v1/v2 Binance-USDT perps.
  - Features: 13 features (14-feature /059 stack minus btc_ret_14d), each
    cross-sectionally rank-normalized.  (Used only by score_mode="trained".)
  - Position: dollar-neutral cross-sectional quintile long-short, inverse-vol
    weighting, portfolio vol-targeting, 0.1% fee.
  - XS_REQUIRED_GAP = 484 = (H+1)*N = (21+1)*22.  (CPCV row-count purge.)

iter-v3/091 axis: the cross-sectional scoring function (trained LGBMRanker
prediction → parameter-free trailing-H-bar return).  The /089 cost-aware
quintile long-short construction is RETAINED verbatim.

iter-v3/091 SETUP items (correctness + instrumentation, NOT edge axes):
  1. Walk-forward embargo bug fix: embargo_ms = (XS_HORIZON+1)*interval_ms
     (was XS_REQUIRED_GAP*interval_ms — over-embargoing by N=22×).
  2. Gross-Sharpe runner artifact: gross_monthly_sharpe emitted to
     comparison.csv and dsr.json via a shared _monthly_sharpe(sub, pnl_col)
     helper (Critic /090 Rec #1).

No-cheating guarantees:
  - OOS_CUTOFF_DATE / training_months are IMMUTABLE (imported from config).
  - Walk-forward trains each month on IS-only past data; train_end_ms =
    test_start_ms - embargo_ms (the e149e9d fix + /091 embargo correction).
  - XS_REQUIRED_GAP=484 is asserted at CPCV call-site via expected_gap.
  - The cross-sectional label's H=21 forward window NEVER overlaps a test row
    because the embargo removes (H+1)*N_symbols = 484 rows at every boundary.
  - Model-free score uses only close(ts) and close(ts-H*interval) (both ≤ ts);
    PnL return is taken strictly after ts via searchsorted(side='right').
"""

from __future__ import annotations

import datetime
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq

from crypto_trade.config import OOS_CUTOFF_MS

# ---------------------------------------------------------------------------
# Universe constants  (Section 3.3)
# ---------------------------------------------------------------------------

#: 22-symbol XS universe — IS-only screen T1 from EDA SHA aebd9f3.
#: Non-v1/v2 symbols.  Order is canonical (reproducibility).
XS_UNIVERSE: tuple[str, ...] = (
    "ADAUSDT",
    "AVAXUSDT",
    "FILUSDT",
    "FTMUSDT",
    "BCHUSDT",
    "GALAUSDT",
    "EOSUSDT",
    "CRVUSDT",
    "AAVEUSDT",
    "SANDUSDT",
    "ATOMUSDT",
    "LDOUSDT",
    "AXSUSDT",
    "TRXUSDT",
    "RUNEUSDT",
    "MANAUSDT",
    "ICPUSDT",
    "ALGOUSDT",
    "GRTUSDT",
    "THETAUSDT",
    "VETUSDT",
    "HBARUSDT",
)

N_XS_SYMBOLS: int = len(XS_UNIVERSE)  # 22

#: H = forward horizon in bars.
#: iter-v3/091: H=21 (~7 days, the literature weekly cross-sectional-momentum
#: horizon).  The model-free book scores each symbol by the trailing-21-bar
#: return; the overlapping J-T hold is horizon-matched at XS_HOLD_BARS=21.
#: EDA M1a: H=21 is inside a smooth [17,25] plateau (IS net [+0.22, +0.32]) —
#: the choice within the plateau is not fragile; H=21 is the a-priori
#: literature anchor (Jegadeesh-Titman 1993 weekly momentum).
XS_HORIZON: int = 21

#: CPCV purge gap for the pooled cross-section (ROW COUNT, not time).
#: Formula: (H + 1) * N_symbols = (21 + 1) * 22 = 484.
#: This is DIFFERENT from the legacy per-symbol REQUIRED_GAP = 66.
#: - Legacy: (timeout_candles=21 + 1) * 3 symbols = 66
#: - Cross-sectional: (H=21 + 1) * 22 symbols = 484
#: The gap removes, on both sides of every test boundary, enough rows so that
#: no training label's H=21 forward window overlaps a test row.
#: NOTE: XS_REQUIRED_GAP is the CPCV row-count purge; the walk-forward TIME
#: embargo is embargo_ms = (XS_HORIZON + 1) * interval_ms — a separate
#: quantity that does NOT multiply by N_symbols (iter-v3/091 Section 3.2).
XS_REQUIRED_GAP: int = (XS_HORIZON + 1) * N_XS_SYMBOLS  # 484

#: Listing burn-in per symbol: 60 days = 180 8h-bars (crypto new-listing
#: non-stationarity pitfall — Section 3.3).
XS_LISTING_BURNIN_BARS: int = 180

#: Minimum symbols in cross-section to form a book at a timestamp (Section 5).
XS_MIN_SYMBOLS_PER_BAR: int = 6

#: btc_ret_14d is dropped from the cross-sectional feature set because it has
#: zero cross-sectional dispersion (identical for every symbol at a given
#: timestamp — EDA T6).  The 14-column V3_FEATURE_COLUMNS_TOP_N constant is
#: NOT edited; this drop happens at training/inference time.
XS_DROP_FEATURES: frozenset[str] = frozenset({"btc_ret_14d"})

# ---------------------------------------------------------------------------
# iter-v3/090 cross-sectional GROSS-SIGNAL feature expansion.
# /089 left the book GROSS-POSITIVE (OOS gross monthly Sharpe +0.1717) but
# net-sub-zero on fees.  /090 strengthens the GROSS SIGNAL by adding two
# DOWNSIDE-RISK cross-sectional features to the ranker.  Both are IS-EDA
# selected (analysis/iteration_v3-090/) — the /090 EDA showed (A3) the
# cross-sectional signal in this 22-altcoin universe resolves 4.1x sharper at
# the loser end of the book (bottom-half within-IC 0.0576 vs top-half 0.0141),
# so DOWNSIDE-RISK features that better rank the short leg are the highest-EV
# gross-signal lever.  B2 downside-risk was the strongest candidate family by
# INCREMENTAL multivariate contribution (d composite IC-IR +0.0306) — the
# iter-v3/070-correct test, not a univariate Spearman.  The two features here
# are the leave-one-out-confirmed ORTHOGONAL subset (C3/C4): the third B2
# candidate (cand_semidev_50) was DROPPED for 0.80 cross-sectional rank
# correlation with the incumbent range_realized_vol_50 (the iter-v3/070
# colsample-dilution risk); the orthogonal pair captures the full realised
# long-short spread improvement.
# ---------------------------------------------------------------------------

#: iter-v3/090 — the two engineered DOWNSIDE-RISK cross-sectional features
#: appended to the ranker's feature set.  Computed per-symbol from OHLCV +
#: btc_ret_3d in `_engineer_xs_downside_features`, then cross-sectionally
#: rank-normalised by `build_cross_sectional_panel` exactly like every other
#: feature.  Names are NOT in V3_FEATURE_COLUMNS_TOP_N (engineered at panel
#: build time, the cross-sectional path only — the legacy per-symbol path is
#: untouched).
XS_DOWNSIDE_FEATURES: tuple[str, ...] = (
    "xs_sortino_mom_12",  # 12-bar return / downside semi-deviation
    "xs_downbeta_50",  # beta vs the BTC proxy on down-market bars only
)

#: iter-v3/090 window constants for the downside-risk features (a-priori,
#: matched to the existing 50-bar v3 feature windows; the EDA used the same).
XS_DOWNSIDE_VOL_WINDOW: int = 50  # rolling window for semi-deviation / down-beta
XS_DOWNSIDE_MOM_LOOKBACK: int = 12  # the Sortino-momentum return lookback

#: Portfolio vol-target: annualised daily volatility target.
#: Standard cross-sectional construction (Poh/Lim/Zohren).
XS_VOL_TARGET: float = 0.10  # 10% annualised

#: Fee per side, modeled on every 8h rebalance.
XS_FEE_PER_SIDE: float = 0.001  # 0.1%

#: Tercile cutoff fraction — the /088 quantile (a-priori from factor convention).
XS_TERCILE_FRAC: float = 1.0 / 3.0

#: Realised-vol lookback for inverse-vol weighting (past-only, in bars).
XS_VOL_LOOKBACK: int = 50

# ---------------------------------------------------------------------------
# iter-v3/089 cost-aware construction constants — all IS-selected or a-priori.
# /088 lost money because of (1) a sign inversion and (2) turnover drag (IS
# fees 8.8x gross PnL).  These constants attack turnover STRUCTURALLY; the
# /089 research brief Section 3 derives each from the committed IS-only EDA
# (analysis/iteration_v3-089/) — never from OOS data.
# ---------------------------------------------------------------------------

#: /089 per-leg QUANTILE fraction — QUINTILE (top/bottom 20%).
#: EDA G1: quintile maximises the realised L-S spread per-bar Sharpe across
#: the 22-symbol universe; decile (10%) is THINNER and weaker (~2 names/leg
#: is too noisy at N=22); tercile dilutes the LTR precision.  Poh/Lim/Zohren
#: (arXiv 2012.07149): an LTR model places assets in the right quantile with
#: greater precision, so a tighter quantile steepens the spread — but not so
#: tight the leg loses diversification.  Quintile = ~4-5 names/leg.
XS_QUANTILE_FRAC: float = 0.20

#: /089 HOLDING PERIOD — overlapping tranches held XS_HOLD_BARS bars.
#: At each bar a NEW tranche sized 1/XS_HOLD_BARS of the book is formed and
#: held XS_HOLD_BARS bars; the book is the sum of the live tranches.  This is
#: the Jegadeesh-Titman (1993) overlapping-portfolio construction; it cuts
#: gross turnover ~XS_HOLD_BARS-fold with negligible signal loss.
#: iter-v3/091: XS_HOLD_BARS=21, horizon-matched to H=21.  At H=21 the
#: overlapping-hold cuts gross turnover ~7× vs the /089 H=3 book; the IS
#: model-free EDA at H=21 shows turnover/bar ≈ 0.0263 — far inside the
#: 0.138 ceiling.
XS_HOLD_BARS: int = 21

#: /089 NO-TRADE BAND — only re-trade a symbol when its target book weight
#: moves more than XS_NO_TRADE_BAND vs the held weight (Constantinides 1986;
#: Davis-Norman 1990 — the optimal no-trade band scales O(eps^1/3) in the
#: proportional cost eps; utility loss is O(eps^2/3), so when costs dominate
#: a wide band is mandatory).  EDA E4 scanned tau on IS data; tau=0.020 was
#: the IS-best net Sharpe of the grid (-0.31).  Selected on IS net Sharpe.
XS_NO_TRADE_BAND: float = 0.020

#: /089 PRE-REGISTERED HARD TURNOVER CEILING — gross turnover per bar.
#: EDA E6: the IS-best construction (quintile + hold=3 + tau=0.020) runs at
#: 0.120 gross turnover/bar; the ceiling is set at x1.15 headroom = 0.138.
#: This is a HARD MERGE-BLOCKING GATE (the /089 brief Section 4): any /089
#: build whose realised mean gross turnover/bar EXCEEDS XS_TURNOVER_CEILING
#: is NO-MERGE — turnover drag cannot be rationalised post-hoc.
XS_TURNOVER_CEILING: float = 0.138


# ---------------------------------------------------------------------------
# A2 — Cross-sectional labeling (Section 3.1)
# ---------------------------------------------------------------------------


def label_cross_sectional_rank(
    panel: pd.DataFrame,
    horizon: int = XS_HORIZON,
) -> pd.Series:
    """Assign {0, 1, 2} graded cross-sectional relevance labels.

    For each (symbol, timestamp t) row:
      1. Forward H-bar return r_fwd(i,t) = close(i,t+H) / close(i,t) - 1.
         Uses the 'close' column.  NaN when close(t+H) is unavailable.
      2. Within each timestamp's cross-section, rank r_fwd ascending →
         discrete relevance grade in {0, 1, 2} by tercile:
           bottom-third → grade 0 (the lowest FORWARD returns — future
             cross-section UNDER-performers)
           middle-third → grade 1
           top-third    → grade 2 (the highest FORWARD returns — future
             cross-section OUT-performers)

    iter-v3/089 SIGN NOTE — the grade is assigned by FORWARD-return rank.  An
    LGBMRanker(lambdarank) trained on this grade learns the FORWARD mapping:
    high predicted score → high grade → high future return.  The /088 brief
    mis-reasoned (it conflated the EDA's PAST-return reversal predictor with
    what the model learns from a FORWARD-return label) and longed the model's
    predicted LOSERS.  The corrected /089 construction (`build_positions`)
    LONGs the top tercile (high score = predicted future winner) and SHORTs
    the bottom tercile.  See the /089 research brief Section 3.1/3.3.

    Look-ahead safety: r_fwd is the LABEL (the prediction target), not a
    feature.  The labeling is look-ahead-correct.  The walk-forward embargo
    (XS_REQUIRED_GAP = 88 rows) at every train/test boundary ensures no
    training label's forward window overlaps a test row.

    Parameters
    ----------
    panel:
        DataFrame with columns ['open_time', 'symbol', 'close'].
        Must be sorted by (open_time, symbol).
    horizon:
        Forward horizon in bars.  Default XS_HORIZON=3.

    Returns
    -------
    pd.Series of dtype Int8 ({0, 1, 2}), same index as panel.
    NaN (pd.NA) for rows where the forward close is unavailable.
    """
    panel = panel.sort_values(["open_time", "symbol"]).copy()

    # Compute close(t+H) for each (symbol, t) using a within-symbol shift.
    panel["_fwd_close"] = panel.groupby("symbol", sort=False)["close"].shift(-horizon)
    panel["_r_fwd"] = panel["_fwd_close"] / panel["close"] - 1.0

    # Assign tercile grade within each timestamp's cross-section.
    # pd.qcut with q=3 assigns labels {0,1,2} by rank.
    def _tercile_grade(group: pd.Series) -> pd.Series:
        n = group.notna().sum()
        if n < XS_MIN_SYMBOLS_PER_BAR:
            # Too few symbols to form a meaningful cross-section — NaN all.
            return pd.Series(pd.NA, index=group.index, dtype="Int8")
        try:
            # duplicates='drop' handles ties robustly; any tied group may
            # produce slightly unequal tercile sizes — accepted.
            grades = pd.qcut(group, q=3, labels=[0, 1, 2], duplicates="drop")
            return grades.astype("Int8")
        except ValueError:
            # Degenerate distribution (all identical returns) → mid grade.
            return pd.Series(1, index=group.index, dtype="Int8").where(group.notna(), other=pd.NA)

    labels = panel.groupby("open_time", sort=False)["_r_fwd"].transform(_tercile_grade)
    return labels


# ---------------------------------------------------------------------------
# iter-v3/090 — downside-risk feature engineering (Section 3)
# ---------------------------------------------------------------------------


def _engineer_xs_downside_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the iter-v3/090 DOWNSIDE-RISK cross-sectional features to one
    symbol's panel — `xs_sortino_mom_12` and `xs_downbeta_50`.

    Both are computed from PAST-ONLY data: rolling windows on `close` and the
    `btc_ret_3d` market-return proxy already in the v3 feature parquet.  Every
    rolling statistic at bar t uses only bars <= t (pandas `.rolling` is
    backward-looking; `.pct_change()` / `.shift()` look back).  The features
    are NOT forward-looking — they are predictors, scored at bar t.  Cross-
    sectional rank-normalisation happens later, per timestamp, in
    `build_cross_sectional_panel`.

    These reproduce `cand_sortino_mom_12` and `cand_downbeta_50` from the
    committed IS-only EDA `analysis/iteration_v3-090/gross_signal_expansion_eda.py`
    (the `_engineer_candidates` function) exactly — the EDA measured the same
    features the /090 build trades on.

    Look-ahead safety: every column read (`close`, `btc_ret_3d`) is a
    historical observation at bar t; every transform is backward-looking.  The
    walk-forward embargo (XS_REQUIRED_GAP) is unchanged and still governs the
    train/test boundary.

    Parameters
    ----------
    df:
        One symbol's feature DataFrame, sorted by open_time, with at least
        the columns ['close', 'btc_ret_3d'].

    Returns
    -------
    The same DataFrame with two columns added: the names in
    XS_DOWNSIDE_FEATURES.
    """
    win = XS_DOWNSIDE_VOL_WINDOW
    lb = XS_DOWNSIDE_MOM_LOOKBACK
    close = df["close"].astype(float)
    ret_1 = close.pct_change()

    # btc_ret_3d is a 3-bar BTC return; convert to a ~1-bar BTC return proxy so
    # the down-beta regression is on a per-bar basis (matches the EDA).
    btc_ret_1 = (df["btc_ret_3d"].astype(float) + 1.0) ** (1.0 / 3.0) - 1.0

    # --- xs_sortino_mom_12: lb-bar return scaled by downside semi-deviation --
    # semi-deviation = rolling std of NEGATIVE returns only (downside dispersion).
    neg = ret_1.where(ret_1 < 0.0, 0.0)
    semidev = neg.rolling(win).std()
    df["xs_sortino_mom_12"] = (close / close.shift(lb) - 1.0) / semidev.replace(0.0, np.nan)

    # --- xs_downbeta_50: beta vs the BTC proxy on DOWN-market bars only ------
    down_mask = btc_ret_1 < 0.0
    r_d = ret_1.where(down_mask)
    b_d = btc_ret_1.where(down_mask)
    cov_d = r_d.rolling(win, min_periods=15).cov(b_d)
    var_d = b_d.rolling(win, min_periods=15).var()
    df["xs_downbeta_50"] = cov_d / var_d.replace(0.0, np.nan)

    return df


# ---------------------------------------------------------------------------
# A3 — Pooled-panel builder (Section 3.5)
# ---------------------------------------------------------------------------


def build_cross_sectional_panel(
    features_dir: str | Path,
    symbols: tuple[str, ...],
    feature_columns: list[str],
    drop_features: frozenset[str] = XS_DROP_FEATURES,
    listing_burnin_bars: int = XS_LISTING_BURNIN_BARS,
    interval: str = "8h",
    expand_downside: bool = False,
) -> pd.DataFrame:
    """Load and align the pooled cross-sectional panel.

    Steps:
      1. Load each symbol's feature parquet (open_time, close, + feature_cols).
      2. iter-v3/090: if `expand_downside`, engineer the two DOWNSIDE-RISK
         cross-sectional features (XS_DOWNSIDE_FEATURES) per symbol BEFORE the
         burn-in (the rolling windows need the pre-burn-in warm-up history).
      3. Apply the 60-day (180-bar) listing burn-in per symbol.
      4. Concatenate all symbols into a pooled panel sorted by (open_time, symbol).
      5. Drop btc_ret_14d (zero cross-sectional dispersion — EDA T6).
      6. Cross-sectionally rank-normalize each remaining feature (and, when
         `expand_downside`, the two downside features) at each timestamp.

    Parameters
    ----------
    features_dir:
        Path to v3 feature parquets (e.g. 'data/features_v3').
    symbols:
        The XS_UNIVERSE tuple or a subset.
    feature_columns:
        V3_FEATURE_COLUMNS_TOP_N list (14 features; btc_ret_14d is in it
        but will be dropped here).
    drop_features:
        Features with zero cross-sectional dispersion to drop.
    listing_burnin_bars:
        Number of leading bars to drop per symbol (60-day burn-in).
    interval:
        Candle interval string (default '8h').
    expand_downside:
        iter-v3/090 — when True, engineer and rank-normalize the two
        DOWNSIDE-RISK cross-sectional features (XS_DOWNSIDE_FEATURES) in
        addition to the base feature set.  When False, the /088/089 13-feature
        behaviour is byte-identical.

    Returns
    -------
    pd.DataFrame with columns:
        ['open_time', 'symbol', 'close'] + [xs-normalized feature cols]
        (13 features when expand_downside is False; 15 when True).
    Sorted by (open_time, symbol).
    """
    features_path = Path(features_dir)
    xs_cols = [c for c in feature_columns if c not in drop_features]
    # iter-v3/090 — the downside-risk features are appended AFTER engineering;
    # they are rank-normalized alongside the base features.
    if expand_downside:
        xs_cols = xs_cols + list(XS_DOWNSIDE_FEATURES)
        # raw columns needed to engineer the downside features (past-only).
        engineer_inputs = ["btc_ret_3d"]
    else:
        engineer_inputs = []

    frames: list[pd.DataFrame] = []
    for sym in symbols:
        pf = features_path / f"{sym}_{interval}_features.parquet"
        if not pf.exists():
            raise FileNotFoundError(f"build_cross_sectional_panel: parquet missing for {sym}: {pf}")
        # Load only the columns we need (base features + close + any raw
        # columns the iter-v3/090 downside engineering reads).
        base_needed = [c for c in feature_columns if c not in drop_features]
        needed = ["open_time", "close"] + base_needed + engineer_inputs
        needed = list(dict.fromkeys(needed))  # dedup, preserve order
        # Parquet schema may have extra cols — read only what we need.
        available = set(pq.read_schema(pf).names)
        missing = [c for c in needed if c not in available]
        if missing:
            raise ValueError(
                f"build_cross_sectional_panel: {sym} parquet missing columns: {missing}"
            )
        df = pq.read_table(pf, columns=needed).to_pandas()
        df["symbol"] = sym

        # iter-v3/090 — engineer the downside-risk features BEFORE the burn-in
        # so the rolling windows have warm-up history; the burn-in then drops
        # exactly the warm-up rows.  No look-ahead: every transform is
        # backward-looking (see `_engineer_xs_downside_features`).
        if expand_downside:
            df = df.sort_values("open_time").reset_index(drop=True)
            df = _engineer_xs_downside_features(df)
            # the raw engineering inputs are no longer needed downstream.
            df = df.drop(columns=[c for c in engineer_inputs if c not in base_needed])

        # Listing burn-in: drop the first `listing_burnin_bars` rows per symbol.
        if len(df) > listing_burnin_bars:
            df = df.iloc[listing_burnin_bars:].copy()
        else:
            # Symbol has fewer rows than the burn-in — skip entirely.
            warnings.warn(
                f"build_cross_sectional_panel: {sym} has only {len(df)} rows "
                f"— fewer than listing_burnin_bars={listing_burnin_bars}; skipped.",
                stacklevel=2,
            )
            continue

        frames.append(df)

    if not frames:
        raise RuntimeError("build_cross_sectional_panel: no symbol data loaded after burn-in.")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["open_time", "symbol"]).reset_index(drop=True)

    # Cross-sectional rank-normalization: at each timestamp, replace each
    # feature value with its cross-sectional rank (0-based, ascending) divided
    # by (n_symbols - 1) → [0, 1].  This is the standard cross-sectional
    # feature treatment (Poh/Lim/Zohren; EDA T7 is built on this transform).
    def _xs_rank_normalize(group: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        n = len(group)
        if n < 2:
            return group
        for col in cols:
            ranked = group[col].rank(method="average", na_option="keep")
            group[col] = (ranked - 1.0) / max(n - 1, 1)
        return group

    panel[xs_cols] = panel.groupby("open_time", sort=False, group_keys=False).apply(
        lambda g: _xs_rank_normalize(g.copy(), xs_cols)[xs_cols]
    )

    return panel


# ---------------------------------------------------------------------------
# A4 — CrossSectionalRankStrategy (Section 3.2 / 3.6)
# ---------------------------------------------------------------------------


class CrossSectionalRankStrategy:
    """Pooled LGBMRanker with monthly walk-forward retrain.

    Wraps LightGBM's native lambdarank objective for cross-sectional ranking.
    One model trained on the pooled cross-section of XS_UNIVERSE symbols.
    Monthly walk-forward: train on trailing 24 months, predict the next month.

    The model is trained on:
      - Panel rows: one (symbol, timestamp) per row.
      - Group: one query per timestamp (number of symbols at that snapshot).
      - Label: {0, 1, 2} graded relevance (label_cross_sectional_rank output).
      - Features: 13 cross-sectionally rank-normalized features.

    Hyperparameters optimised via Optuna with IS rank-IC as the CV objective.
    """

    def __init__(
        self,
        training_months: int = 24,
        n_trials: int = 35,
        feature_columns: list[str] | None = None,
        features_dir: str = "data/features_v3",
        symbols: tuple[str, ...] = XS_UNIVERSE,
        horizon: int = XS_HORIZON,
        seed: int = 42,
        ensemble_seeds: list[int] | None = None,
        verbose: int = 0,
    ) -> None:
        if not feature_columns:
            raise ValueError(
                "feature_columns must be explicitly specified (the 13-feature "
                "cross-sectional list with btc_ret_14d dropped)."
            )
        self.training_months = training_months
        self.n_trials = n_trials
        self.feature_columns = [c for c in feature_columns if c not in XS_DROP_FEATURES]
        self.features_dir = features_dir
        self.symbols = symbols
        self.horizon = horizon
        self.seed = seed
        # iter-v3/092 inner-ensemble support: when ensemble_seeds is provided,
        # _train_for_month trains one LGBMRanker per seed (with its own TPESampler
        # and random_state) and predict() returns the arithmetic mean of all
        # models' score vectors.  When None, behaviour is identical to /091
        # (single model, seed=self.seed).
        self.ensemble_seeds: list[int] = ensemble_seeds if ensemble_seeds is not None else [seed]
        self.verbose = verbose

        self._models: list[lgb.LGBMRanker] = []  # one model per ensemble seed
        # Backward-compat alias: self._model points to first model (or None).
        self._current_month: str | None = None
        self._is_rank_ic: float | None = None  # IS rank-IC from last training

    @property
    def _model(self) -> lgb.LGBMRanker | None:
        """Backward-compat accessor — first trained model (or None)."""
        return self._models[0] if self._models else None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _train_for_month(
        self,
        train_panel: pd.DataFrame,
        train_labels: pd.Series,
    ) -> float:
        """Train/retrain the pooled LGBMRanker on the training panel.

        iter-v3/092 inner-ensemble: trains one LGBMRanker per seed in
        self.ensemble_seeds (default: [self.seed] — single model, /091
        behaviour).  predict() will return the arithmetic mean of all models'
        score vectors.

        Returns the IS out-of-fold rank-IC (for smoke-test / A6 reporting).
        """
        # Build the group array: one query per timestamp.
        group = train_panel.groupby("open_time", sort=True).size().values
        x_train = train_panel[self.feature_columns].values.astype(np.float32)
        y_train = train_labels.values.astype(np.int32)

        # open_time array aligned to the valid training rows (for CV grouping).
        open_times_train = train_panel["open_time"].values

        self._models = []
        for inner_seed in self.ensemble_seeds:

            def _objective(trial: optuna.Trial, _seed: int = inner_seed) -> float:
                params = {
                    "objective": "lambdarank",
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 15, 63),
                    "max_depth": trial.suggest_int("max_depth", 3, 6),
                    "min_child_samples": trial.suggest_int("min_child_samples", 10, 50),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 1.0, log=True),
                    "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 1.0, log=True),
                    "verbose": -1,
                    "random_state": _seed,
                }
                # 5-fold time-series CV with XS_REQUIRED_GAP purge.
                # Pass open_times so CV can split by timestamp (real group arrays).
                return self._cv_rank_ic(x_train, y_train, open_times_train, params)

            sampler = optuna.samplers.TPESampler(seed=inner_seed)
            study = optuna.create_study(direction="maximize", sampler=sampler)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                optuna.logging.set_verbosity(optuna.logging.WARNING)
                study.optimize(_objective, n_trials=self.n_trials, show_progress_bar=False)

            best_params = {
                "objective": "lambdarank",
                "verbose": -1,
                "random_state": inner_seed,
                **study.best_params,
            }
            m = lgb.LGBMRanker(**best_params)
            m.fit(x_train, y_train, group=group)
            self._models.append(m)

        # IS rank-IC: Spearman between ensemble-mean predicted score and
        # forward-return rank (approximated by the label grade) on the training set.
        scores = self._predict_ensemble(x_train)
        ic = float(self._spearman_ic_by_timestamp(train_panel["open_time"].values, scores, y_train))
        self._is_rank_ic = ic
        return ic

    def _predict_ensemble(self, x: np.ndarray) -> np.ndarray:
        """Arithmetic mean of all inner-ensemble models' predict() vectors."""
        if not self._models:
            return np.zeros(len(x))
        preds = np.stack([m.predict(x) for m in self._models], axis=0)
        return preds.mean(axis=0)

    def _cv_rank_ic(
        self,
        x_arr: np.ndarray,
        y: np.ndarray,
        open_times: np.ndarray,
        params: dict,
    ) -> float:
        """5-fold time-series CV on the training panel; returns mean per-timestamp rank-IC.

        Splits by TIMESTAMP (whole cross-sections stay together — no timestamp
        is ever split across train/val).  Builds the real per-timestamp group
        arrays for each fold (no approximate groups).  The XS_REQUIRED_GAP=88
        timestamp-row purge is applied at the fold boundary: all rows whose
        open_time lies within the gap zone are excluded from both train and val.

        The CV objective is the mean per-timestamp Spearman rank-IC across all
        validation timestamps — the same metric used to evaluate the final model.
        """
        unique_ts = np.unique(open_times)
        n_ts = len(unique_ts)
        n_folds = 5
        fold_size = max(1, n_ts // n_folds)
        gap_ts = XS_REQUIRED_GAP  # gap in rows = (H+1)*N; one "gap unit" = one row

        # Convert to per-timestamp indexing.  For each unique timestamp, record
        # the start/end row-index in x_arr (rows are already sorted by open_time).
        ts_to_rows: dict[int, tuple[int, int]] = {}
        ptr = 0
        for ts in unique_ts:
            mask = open_times == ts
            n = int(mask.sum())
            ts_to_rows[int(ts)] = (ptr, ptr + n)
            ptr += n

        ics: list[float] = []
        for k in range(1, n_folds):
            val_ts_start_idx = k * fold_size
            val_ts_end_idx = (k + 1) * fold_size if k < n_folds - 1 else n_ts

            # Gap boundary: exclude the XS_REQUIRED_GAP rows (= gap_ts rows)
            # that straddle the train/val boundary.  One row in the pooled panel
            # corresponds to one (symbol, timestamp) pair; XS_REQUIRED_GAP rows
            # at 22 symbols/bar = 4 full timestamp-steps.  We purge gap_ts
            # timestamp-steps from the end of train (conservative but correct).
            gap_ts_steps = max(1, gap_ts // len(self.symbols))  # timestamp-steps to purge
            train_ts_end_idx = max(0, val_ts_start_idx - gap_ts_steps)

            # Need enough timestamps in each split.
            if train_ts_end_idx < gap_ts_steps or (val_ts_end_idx - val_ts_start_idx) < 1:
                continue

            # Build row index arrays from the timestamp ranges.
            train_ts = unique_ts[:train_ts_end_idx]
            val_ts = unique_ts[val_ts_start_idx:val_ts_end_idx]

            # Collect row slices and group arrays using actual per-timestamp sizes.
            tr_rows_list: list[tuple[int, int]] = [ts_to_rows[int(t)] for t in train_ts]
            val_rows_list: list[tuple[int, int]] = [ts_to_rows[int(t)] for t in val_ts]

            if not tr_rows_list or not val_rows_list:
                continue

            # Build index arrays for fancy-indexing x_arr / y / open_times.
            tr_idx = np.concatenate([np.arange(s, e) for s, e in tr_rows_list])
            val_idx = np.concatenate([np.arange(s, e) for s, e in val_rows_list])

            x_tr = x_arr[tr_idx]
            y_tr = y[tr_idx]
            x_val = x_arr[val_idx]
            y_val = y[val_idx]
            ot_val = open_times[val_idx]

            # Real per-timestamp group arrays (exact symbol counts per bar).
            g_tr = [e - s for s, e in tr_rows_list]
            g_val = [e - s for s, e in val_rows_list]

            if not g_tr or not g_val or sum(g_tr) < 1 or sum(g_val) < 1:
                continue

            try:
                m = lgb.LGBMRanker(**params)
                m.fit(x_tr, y_tr, group=g_tr)
                scores = m.predict(x_val)
                # Per-timestamp rank-IC (cross-sectional IC, not pooled).
                ic = self._spearman_ic_by_timestamp(ot_val, scores, y_val)
                ics.append(ic)
            except Exception:  # noqa: BLE001
                continue

        return float(np.mean(ics)) if ics else -0.5

    @staticmethod
    def _spearman_ic_by_timestamp(
        open_times: np.ndarray,
        scores: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """Mean per-timestamp Spearman rank-IC (IC Information Ratio denominator)."""
        ics: list[float] = []
        for ts in np.unique(open_times):
            mask = open_times == ts
            if mask.sum() < 2:
                continue
            ic = _spearman_ic(scores[mask], labels[mask].astype(float))
            ics.append(ic)
        return float(np.mean(ics)) if ics else 0.0

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_ranking(self, panel: pd.DataFrame) -> np.ndarray:
        """Score each row in the test panel; returns predicted ranking scores.

        Higher score = the model predicts this symbol will RANK HIGHER in the
        cross-section's FORWARD return — i.e. be a top-tercile forward-return
        symbol.  The model is trained by `lambdarank` on the forward-return
        tercile grade from `label_cross_sectional_rank`, so it learns the
        FORWARD mapping directly: high score → high future return.

        iter-v3/089 SIGN FIX — therefore high score = predicted future WINNER:
        `build_positions` LONGs the top tercile (highest scores) and SHORTs
        the bottom tercile (lowest scores).  The /088 docstring's "reversal
        ... higher score → lower forward return → SHORT" reasoning was WRONG
        (the model is not trained on past returns, so there is no reversal for
        it to invert; the /088 IS Spearman(predicted_score, label_grade) =
        +0.033, p=1.2e-12 confirms high score → high grade → high future
        return).  See the /089 research brief Section 3.1/3.3.
        """
        if self._model is None:
            raise RuntimeError(
                "CrossSectionalRankStrategy.predict_ranking: model not trained. "
                "Call _train_for_month first."
            )
        x_pred = panel[self.feature_columns].values.astype(np.float32)
        return self._model.predict(x_pred)


# ---------------------------------------------------------------------------
# A5 — Position construction (Section 3.4)
# ---------------------------------------------------------------------------


def build_positions(
    panel_t: pd.DataFrame,
    scores: np.ndarray,
    hist_returns: pd.DataFrame,
    vol_target: float = XS_VOL_TARGET,
    tercile_frac: float = XS_TERCILE_FRAC,
    min_symbols: int = XS_MIN_SYMBOLS_PER_BAR,
    vol_lookback: int = XS_VOL_LOOKBACK,
) -> dict[str, float]:
    """Construct dollar-neutral quantile long-short positions at timestamp t.

    iter-v3/089 SIGN FIX (Critic /088 Rec #2).
    -------------------------------------------
    The LGBMRanker is trained by `lambdarank` on `label_cross_sectional_rank`
    grades, where grade is assigned by FORWARD-return rank (grade 2 = top-third
    of FUTURE returns).  The model therefore learns the FORWARD mapping —
    high predicted score → high future return.  The /088 build inverted this:
    it longed `sorted_syms[:n_leg]` (the LOWEST scores = predicted future
    LOSERS) and shorted the highest.  /089 corrects the sign.

    Algorithm:
      1. Score each symbol with the ranking model.
      2. LONG the TOP quantile (HIGHEST scores = predicted future WINNERS).
         SHORT the BOTTOM quantile (LOWEST scores = predicted future LOSERS).
      3. Dollar-neutral: equal gross long and gross short notional.
      4. Within each leg, inverse-vol weight (weight ∝ 1/σ̂).
      5. Scale the whole book to XS_VOL_TARGET via portfolio vol-targeting.

    `tercile_frac` is the per-leg quantile fraction (kept named `tercile_frac`
    for call-site compatibility; the /089 runner passes the EDA-selected
    quintile fraction — see the /089 research brief Section 3.3).

    Parameters
    ----------
    panel_t:
        DataFrame slice for the current timestamp — one row per symbol.
        Must have 'symbol' column.
    scores:
        Predicted ranking score, same row order as panel_t.
    hist_returns:
        DataFrame indexed by open_time, columns = symbols.
        Used to compute per-symbol realised vol (past-only).
    vol_target:
        Annual portfolio vol target.
    tercile_frac:
        Fraction of universe for each leg (default 1/3).
    min_symbols:
        Minimum symbols required to form a book (default 6).
    vol_lookback:
        Lookback bars for realised-vol estimate (default 50).

    Returns
    -------
    dict mapping symbol -> signed position fraction.
    Positive = long, negative = short.
    Empty dict if the cross-section is too thin.
    """
    syms = panel_t["symbol"].values
    n = len(syms)
    if n < min_symbols:
        return {}

    # Sort by score ascending.
    order = np.argsort(scores)
    sorted_syms = syms[order]

    # iter-v3/089 SIGN FIX: high score = predicted future WINNER → LONG.
    n_leg = max(1, int(np.floor(n * tercile_frac)))
    long_syms = set(sorted_syms[-n_leg:])  # TOP quantile (high score) → LONG
    short_syms = set(sorted_syms[:n_leg])  # BOTTOM quantile (low score) → SHORT

    # Per-symbol realised vol estimate (past-only).
    vol_map: dict[str, float] = {}
    for sym in syms:
        if sym in hist_returns.columns and len(hist_returns) >= 2:
            ret_series = hist_returns[sym].dropna()
            if len(ret_series) >= 2:
                vol_map[sym] = max(float(ret_series.std()), 1e-8)
            else:
                vol_map[sym] = 1.0
        else:
            vol_map[sym] = 1.0

    # Inverse-vol weights within each leg.
    def _inv_vol_weights(leg_syms: set[str]) -> dict[str, float]:
        inv_vols = {s: 1.0 / vol_map.get(s, 1.0) for s in leg_syms}
        total = sum(inv_vols.values())
        return {s: v / total for s, v in inv_vols.items()}

    long_weights = _inv_vol_weights(long_syms)
    short_weights = _inv_vol_weights(short_syms)

    # Dollar-neutral: long gross = short gross = 1.0 (pre vol-target scaling).
    positions: dict[str, float] = {}
    for sym, w in long_weights.items():
        positions[sym] = +w
    for sym, w in short_weights.items():
        positions[sym] = -w

    # Portfolio vol-targeting: scale book so its realised vol matches vol_target.
    # Annualise 8h-bar vol: sqrt(3 * 365) ≈ 33.1 bars/year.
    bars_per_year = 3.0 * 365.0  # 8h bars
    port_vol = _portfolio_vol(positions, hist_returns)
    annualised_port_vol = port_vol * np.sqrt(bars_per_year)
    if annualised_port_vol > 1e-8:
        scale = vol_target / annualised_port_vol
        positions = {s: w * scale for s, w in positions.items()}

    return positions


def _portfolio_vol(
    positions: dict[str, float],
    hist_returns: pd.DataFrame,
) -> float:
    """Realised portfolio volatility on the trailing vol_lookback bars."""
    syms = list(positions.keys())
    weights = np.array([positions[s] for s in syms])
    if not syms or len(hist_returns) < 2:
        return 0.01  # fallback

    ret_mat = hist_returns[syms].dropna(how="all").values
    if ret_mat.shape[0] < 2:
        return 0.01
    cov = np.cov(ret_mat.T)
    if cov.ndim == 0:
        port_var = float(cov) * weights[0] ** 2
    else:
        port_var = float(weights @ cov @ weights)
    return np.sqrt(max(port_var, 0.0))


def _approximate_group(n_rows: int, n_symbols: int) -> list[int]:
    """Approximate group array when exact per-timestamp counts unavailable.

    Produces group sizes ≈ n_symbols (may differ by 1 for the last group).
    Used inside CV where the panel is not available.
    """
    if n_symbols < 1 or n_rows < 1:
        return [n_rows]
    n_full = n_rows // n_symbols
    remainder = n_rows % n_symbols
    groups = [n_symbols] * n_full
    if remainder:
        groups.append(remainder)
    return groups


def apply_no_trade_band(
    target: dict[str, float],
    held: dict[str, float],
    band: float,
) -> dict[str, float]:
    """iter-v3/089 no-trade band — hold the previous book weight for a symbol
    unless its target weight has moved by more than `band`.

    Constantinides (1986) / Davis-Norman (1990): with a proportional cost the
    optimal policy is a no-trade region; when a holding leaves the region it
    is rebalanced to the (target) boundary.  Here:
      - |target - held| <= band  →  carry the HELD weight (zero turnover fee).
      - |target - held| >  band  →  move to the TARGET weight.

    band = 0  →  rebalance every symbol every bar (the /088 behaviour).

    Returns the post-band book weights (dust below 1e-9 dropped).
    """
    if band <= 0.0:
        return dict(target)
    out: dict[str, float] = {}
    for s in set(target) | set(held):
        t = target.get(s, 0.0)
        h = held.get(s, 0.0)
        out[s] = t if abs(t - h) > band else h
    return {s: v for s, v in out.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------------------
# A5 — Cross-sectional backtest (Section 3.4.1)
# ---------------------------------------------------------------------------


def run_cross_sectional_backtest(
    strategy: CrossSectionalRankStrategy,
    panel: pd.DataFrame,
    labels: pd.Series,
    train_start_ms: int,
    oos_cutoff_ms: int = OOS_CUTOFF_MS,
    fee_per_side: float = XS_FEE_PER_SIDE,
    vol_lookback: int = XS_VOL_LOOKBACK,
    quantile_frac: float = XS_QUANTILE_FRAC,
    hold_bars: int = XS_HOLD_BARS,
    no_trade_band: float = XS_NO_TRADE_BAND,
    score_mode: str = "trained",
) -> pd.DataFrame:
    """Full walk-forward cross-sectional backtest — iter-v3/089 cost-aware.

    Walk-forward cadence (Section 3.6):
      - Train on trailing training_months months (IS-only past data).
      - Embargo (iter-v3/091 CORRECTED): train_end_ms = test_start_ms - embargo_ms,
        where embargo_ms = (XS_HORIZON + 1) * interval_ms.
        Prior to /091 this was XS_REQUIRED_GAP * interval_ms, which over-embargoed
        by N_XS_SYMBOLS = 22× (XS_REQUIRED_GAP is a row count, not a time count).

    iter-v3/091 scoring modes (score_mode parameter):
      - "model_free": parameter-free trailing-H-bar return score,
        score(sym) = close(sym, ts) / close(sym, ts - H*interval) - 1.
        No model is trained; strategy._model stays None.  Deterministic.
      - "trained": pooled LGBMRanker(lambdarank) monthly walk-forward (the
        /088/089/090 mode, retained as reference comparator in /091).

    iter-v3/089 cost-aware construction:
      - QUINTILE legs (quantile_frac=0.20) — EDA G1.
      - OVERLAPPING HOLDS (hold_bars=21 in /091) — Jegadeesh-Titman (1993).
      - NO-TRADE BAND (no_trade_band=0.020) — Constantinides / Davis-Norman.

    Fees: 0.1% per side modeled, turnover-based, charged on the absolute
    change in the BOOK position bar-to-bar.

    Parameters
    ----------
    strategy:
        Untrained CrossSectionalRankStrategy instance.
    panel:
        Full pooled panel (all timestamps including OOS).
        Returned by build_cross_sectional_panel().
    labels:
        Cross-sectional grades from label_cross_sectional_rank().
    train_start_ms:
        Earliest timestamp (ms) to include in training.
    oos_cutoff_ms:
        OOS split point (default OOS_CUTOFF_MS = 1742774400000).
    fee_per_side:
        Fee per side (default 0.001 = 0.1%).
    vol_lookback:
        Trailing bars for per-symbol realised-vol estimate.
    score_mode:
        "trained" (LGBMRanker — default) or "model_free" (trailing-return).

    Returns
    -------
    pd.DataFrame with columns:
        open_time, symbol, position, gross_pnl, fee, net_pnl, is_oos,
        rank_ic, predicted_score, label_grade
    One row per (timestamp, active symbol).
    """
    if score_mode not in ("trained", "model_free"):
        raise ValueError(f"score_mode must be 'trained' or 'model_free', got {score_mode!r}")

    interval_ms = 8 * 3600 * 1000  # 8h in ms
    # iter-v3/091 CORRECTED embargo: (H+1) candle-intervals of wall-clock TIME.
    # XS_REQUIRED_GAP is a row count; it must NOT be multiplied by interval_ms.
    embargo_ms = (XS_HORIZON + 1) * interval_ms

    # Build sorted unique timestamps.
    all_timestamps = np.sort(panel["open_time"].unique())
    training_months = strategy.training_months

    # Build monthly splits using the walk-forward helper.
    # We pass label_timeout_minutes=XS_HORIZON*480 (H bars) so the embargo
    # helper computes embargo_candles = H+1 = 4 ≈ 32h.  But we use
    # embargo_ms directly from XS_REQUIRED_GAP to ensure correctness.
    # generate_monthly_splits is not used here because the cross-sectional
    # path has a different label timeout than the triple-barrier path.
    # Instead we compute month boundaries directly.
    splits = _generate_xs_monthly_splits(
        all_timestamps=all_timestamps,
        training_months=training_months,
        embargo_ms=embargo_ms,
    )

    if not splits:
        raise RuntimeError(
            "run_cross_sectional_backtest: no walk-forward splits produced. "
            "Check that the panel has at least training_months+1 calendar months."
        )

    # Build a wide return matrix for vol estimation (past-only).
    # Returns are close-to-close: ret(t) = close(t) / close(t-1) - 1.
    close_wide = panel.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    ret_wide = close_wide.pct_change()

    # iter-v3/091 — pre-compute trailing-H-bar return matrix for model_free mode.
    # mom_wide[ts, sym] = close(sym, ts) / close(sym, ts - H*interval) - 1.
    # Both close values are ≤ ts (no look-ahead).
    mom_wide: pd.DataFrame | None = None
    if score_mode == "model_free":
        mom_wide = close_wide / close_wide.shift(XS_HORIZON) - 1.0

    results: list[dict] = []
    trained_months: set[str] = set()
    # iter-v3/089 cost-aware construction state:
    #   prev_book   — the previous bar's post-band BOOK weights (for the fee).
    #   tranches    — live overlapping tranches: (retire_bar_index, {sym: w}).
    #                 each tranche is sized 1/hold_bars of a bar's target book
    #                 and retired hold_bars bars after it was formed.
    prev_book: dict[str, float] = {}
    tranches: list[tuple[int, dict[str, float]]] = []
    bar_counter = 0  # global rebalance-bar index across all walk-forward months

    for split in splits:
        train_start_ms_split = split["train_start_ms"]
        train_end_ms_split = split["train_end_ms"]
        test_start_ms_split = split["test_start_ms"]
        test_end_ms_split = split["test_end_ms"]
        test_month = split["test_month"]

        # In model_free mode: skip all training — the score is the trailing
        # H-bar return, which requires no model, no Optuna, no parameters.
        # The training/labeling pass below is only for score_mode="trained".
        if score_mode == "trained":
            # Extract training panel rows.
            train_mask = (panel["open_time"] >= train_start_ms_split) & (
                panel["open_time"] < train_end_ms_split
            )
            train_panel = panel[train_mask].copy()
            train_labels_all = labels[train_mask]

            # Drop rows with NaN labels (forward window unavailable) from training.
            valid_mask = train_labels_all.notna()
            train_panel_valid = train_panel[valid_mask].reset_index(drop=True)
            train_labels_valid = train_labels_all[valid_mask].reset_index(drop=True)

            if len(train_panel_valid) < 100:
                print(
                    f"[xs] skip training for {test_month}: "
                    f"only {len(train_panel_valid)} valid rows."
                )
                continue

            # Retrain when we reach a new test month (lazy monthly retrain).
            if test_month not in trained_months:
                print(
                    f"[xs] === Training for {test_month} (train rows={len(train_panel_valid)}) ==="
                )
                # Ensure group array is consistent: sort by (open_time, symbol).
                train_panel_valid = train_panel_valid.sort_values(
                    ["open_time", "symbol"]
                ).reset_index(drop=True)
                train_labels_valid = train_labels_valid.reindex(train_panel_valid.index)
                ic = strategy._train_for_month(train_panel_valid, train_labels_valid)
                print(f"[xs]   IS rank-IC for {test_month}: {ic:.4f}")
                trained_months.add(test_month)

        # Extract test panel rows.
        test_mask = (panel["open_time"] >= test_start_ms_split) & (
            panel["open_time"] < test_end_ms_split
        )
        test_panel = panel[test_mask].copy()
        test_labels = labels[test_mask]

        if len(test_panel) == 0:
            continue

        # Rebalance at every 8h bar in the test window.
        test_timestamps = np.sort(test_panel["open_time"].unique())
        for ts in test_timestamps:
            ts_mask = test_panel["open_time"] == ts
            panel_t = test_panel[ts_mask].copy().reset_index(drop=True)

            if len(panel_t) < XS_MIN_SYMBOLS_PER_BAR:
                continue

            # --- Scoring: model_free or trained ----------------------------
            if score_mode == "model_free":
                # Parameter-free trailing-H-bar return score.
                # score(sym) = close(sym, ts) / close(sym, ts-H*interval) - 1.
                # mom_wide is pre-computed above; look up the row at ts.
                assert mom_wide is not None
                if ts not in mom_wide.index:
                    scores = np.zeros(len(panel_t))
                else:
                    mom_row = mom_wide.loc[ts]
                    syms_t = panel_t["symbol"].values
                    raw_scores = np.array(
                        [
                            float(mom_row[s])
                            if s in mom_row.index and not pd.isna(mom_row[s])
                            else np.nan
                            for s in syms_t
                        ]
                    )
                    valid_score = ~np.isnan(raw_scores)
                    if valid_score.sum() < XS_MIN_SYMBOLS_PER_BAR:
                        continue  # not enough history for trailing-return score
                    # Drop symbols with no trailing-return score.
                    panel_t = panel_t[valid_score].copy().reset_index(drop=True)
                    scores = raw_scores[valid_score]
            else:
                # score_mode == "trained": use the LGBMRanker ensemble.
                # iter-v3/092: _predict_ensemble returns the arithmetic mean of
                # all inner-ensemble models' score vectors (or zeros if untrained).
                x_t = panel_t[strategy.feature_columns].values.astype(np.float32)
                if strategy._models:
                    scores = strategy._predict_ensemble(x_t)
                else:
                    scores = np.zeros(len(panel_t))

            # Past-only vol estimate: trailing vol_lookback bars ending BEFORE ts.
            hist = ret_wide[ret_wide.index < ts].tail(vol_lookback)
            # The per-bar TARGET book — corrected-sign, QUINTILE, dollar-neutral,
            # inverse-vol, vol-targeted (build_positions; quantile_frac=0.20).
            target = build_positions(panel_t, scores, hist, tercile_frac=quantile_frac)

            if not target:
                continue

            # --- iter-v3/089 OVERLAPPING-HOLD tranche book ------------------
            # A new tranche sized 1/hold_bars of the target is formed each bar
            # and retired hold_bars bars later; the book = sum of live tranches.
            # Jegadeesh-Titman (1993) overlapping-portfolio construction.
            new_tranche = {s: w / hold_bars for s, w in target.items()}
            tranches.append((bar_counter + hold_bars, new_tranche))
            tranches = [(rb, w) for (rb, w) in tranches if rb > bar_counter]
            raw_book: dict[str, float] = {}
            for _, tw in tranches:
                for s, v in tw.items():
                    raw_book[s] = raw_book.get(s, 0.0) + v

            # --- iter-v3/089 NO-TRADE BAND ----------------------------------
            # A symbol is re-traded to its raw_book weight only if that weight
            # moved more than no_trade_band vs the held weight; else it carries.
            book = apply_no_trade_band(raw_book, prev_book, no_trade_band)
            bar_counter += 1

            if not book:
                prev_book = {}
                continue

            # PnL on the BOOK positions: the 1-bar gross return for a book
            # weight held over bar t→t+1 is book_pos * (close(t+1)/close(t) - 1).
            # Build lookup maps for label_grade and predicted_score at this bar.
            # A symbol in the book but NOT in panel_t (carried by the no-trade
            # band from a prior bar) has label_grade=None / pred_score=0.0.
            ts_mask_full = test_panel["open_time"] == ts
            ts_labels_full = test_labels[ts_mask_full]
            ts_panel_full = test_panel[ts_mask_full]
            ts_panel_syms = ts_panel_full["symbol"].values
            ts_label_vals = ts_labels_full.values

            sym_to_grade: dict[str, int | None] = {}
            for sym_val, raw_grade in zip(ts_panel_syms, ts_label_vals):
                try:
                    is_na = raw_grade is None or pd.isna(raw_grade)
                except TypeError:
                    is_na = False
                sym_to_grade[sym_val] = None if is_na else int(raw_grade)

            # Build sym→score map from the (possibly filtered) panel_t.
            sym_to_score: dict[str, float] = {}
            for iloc_idx in range(len(panel_t)):
                sym_to_score[panel_t["symbol"].iloc[iloc_idx]] = float(scores[iloc_idx])

            idx_loc = ret_wide.index.searchsorted(ts, side="right")
            is_oos = ts >= oos_cutoff_ms

            # iterate the UNION of book symbols and previous-book symbols, so a
            # symbol that just exited (book weight → 0) still pays its exit fee.
            for sym in set(book) | set(prev_book):
                pos = book.get(sym, 0.0)
                prev_pos = prev_book.get(sym, 0.0)
                if pos == 0.0 and prev_pos == 0.0:
                    continue
                # 1-bar return for this symbol.
                if sym in ret_wide.columns and idx_loc < len(ret_wide):
                    nr = ret_wide[sym].iloc[idx_loc]
                    next_ret = 0.0 if pd.isna(nr) else float(nr)
                else:
                    next_ret = 0.0

                gross_pnl = pos * next_ret
                # Turnover-based fee on the BOOK-position change bar-to-bar.
                fee = abs(pos - prev_pos) * fee_per_side

                # label_grade: None for carried symbols or NA labels.
                # pred_score: the trailing-return score (model_free) or model
                #   score (trained); 0.0 sentinel for symbols not in panel_t.
                label_grade: int | None = sym_to_grade.get(sym, None)
                pred_score: float = sym_to_score.get(sym, 0.0)

                results.append(
                    {
                        "open_time": ts,
                        "symbol": sym,
                        "position": pos,
                        "gross_pnl": gross_pnl,
                        "fee": fee,
                        "net_pnl": gross_pnl - fee,
                        "is_oos": is_oos,
                        "rank_ic": (strategy._is_rank_ic or 0.0)
                        if score_mode != "model_free"
                        else 0.0,
                        "predicted_score": pred_score,
                        "label_grade": label_grade,
                    }
                )

            # Carry the post-band book as the previous book for the next bar.
            prev_book = dict(book)

    if not results:
        return pd.DataFrame(
            columns=[
                "open_time",
                "symbol",
                "position",
                "gross_pnl",
                "fee",
                "net_pnl",
                "is_oos",
                "rank_ic",
                "predicted_score",
                "label_grade",
            ]
        )

    df = pd.DataFrame(results).sort_values("open_time").reset_index(drop=True)
    # Force label_grade to object dtype so Python None values are preserved
    # as None (not coerced to float nan by pandas when ints are mixed with None).
    # This ensures test assertions `grade is None` hold for NA-label rows.
    # pandas converts mixed int/None columns to float64 (None → nan); we
    # restore: non-nan values back to int, nan back to None.
    if "label_grade" in df.columns:
        col = df["label_grade"]
        valid_mask = col.notna()
        label_obj = np.empty(len(col), dtype=object)
        for i, v in enumerate(col):
            label_obj[i] = int(v) if valid_mask.iloc[i] else None
        df["label_grade"] = label_obj
    return df


# ---------------------------------------------------------------------------
# Monthly split generator for the cross-sectional walk-forward
# ---------------------------------------------------------------------------


def _generate_xs_monthly_splits(
    all_timestamps: np.ndarray,
    training_months: int,
    embargo_ms: int,
) -> list[dict]:
    """Monthly walk-forward splits for the cross-sectional path.

    Mirrors the logic of walk_forward.generate_monthly_splits but uses the
    cross-sectional embargo_ms (from XS_REQUIRED_GAP * interval_ms) instead
    of the triple-barrier timeout.

    train_end_ms = test_start_ms - embargo_ms  (the e149e9d look-ahead fix)
    """
    ts_seconds = all_timestamps / 1000.0
    dates = [datetime.datetime.fromtimestamp(t, tz=datetime.UTC) for t in ts_seconds]
    seen: set[tuple[int, int]] = set()
    months_ordered: list[tuple[int, int]] = []
    for d in dates:
        ym = (d.year, d.month)
        if ym not in seen:
            seen.add(ym)
            months_ordered.append(ym)

    splits: list[dict] = []
    for i in range(training_months, len(months_ordered)):
        test_year, test_month_num = months_ordered[i]
        train_start_year, train_start_month_num = months_ordered[i - training_months]

        train_start_ms = _month_start_ms(train_start_year, train_start_month_num)
        test_start_ms = _month_start_ms(test_year, test_month_num)
        test_end_ms = _month_end_ms(test_year, test_month_num)
        train_end_ms = test_start_ms - embargo_ms

        splits.append(
            {
                "train_start_ms": train_start_ms,
                "train_end_ms": train_end_ms,
                "test_start_ms": test_start_ms,
                "test_end_ms": test_end_ms,
                "test_month": f"{test_year:04d}-{test_month_num:02d}",
            }
        )

    return splits


def _month_start_ms(year: int, month: int) -> int:
    d = datetime.datetime(year, month, 1, tzinfo=datetime.UTC)
    return int(d.timestamp() * 1000)


def _month_end_ms(year: int, month: int) -> int:
    if month == 12:
        d = datetime.datetime(year + 1, 1, 1, tzinfo=datetime.UTC)
    else:
        d = datetime.datetime(year, month + 1, 1, tzinfo=datetime.UTC)
    return int(d.timestamp() * 1000)


# ---------------------------------------------------------------------------
# A6 — Rank-IC + turnover reporting helpers
# ---------------------------------------------------------------------------


def compute_turnover_per_bar(results: pd.DataFrame, is_oos: bool) -> float:
    """iter-v3/089 — mean gross turnover per bar.

    The turnover-based fee is `|pos - prev_pos| * fee_per_side`, so the gross
    turnover at a bar is `sum_fee_at_bar / fee_per_side`.  This returns the
    mean over all bars of the chosen split — the quantity the /089 brief
    pre-registers a HARD CEILING on (XS_TURNOVER_CEILING = 0.138): a build
    whose IS mean gross turnover/bar exceeds the ceiling is NO-MERGE.

    Parameters
    ----------
    results:
        The run_cross_sectional_backtest results DataFrame.
    is_oos:
        False → IS turnover (the gated quantity); True → OOS turnover.

    Returns
    -------
    float — mean gross turnover per bar (0.0 if the split is empty).
    """
    sub = results[results["is_oos"] == is_oos]
    if sub.empty:
        return 0.0
    fee_per_bar = sub.groupby("open_time")["fee"].sum()
    if fee_per_bar.empty:
        return 0.0
    # turnover = fee / fee_per_side; recover fee_per_side from a non-trivial row.
    nonzero = sub[sub["fee"] > 0]
    if nonzero.empty:
        return 0.0
    # fee = |dpos| * fee_per_side  →  the modal fee_per_side is XS_FEE_PER_SIDE.
    fee_per_side = XS_FEE_PER_SIDE
    return float((fee_per_bar / fee_per_side).mean())


def compute_oos_rank_ic(results: pd.DataFrame) -> dict:
    """Compute OOS rank-IC between predicted_score and realised label_grade.

    A positive OOS rank-IC confirms the model's ranking correlates with the
    realised forward cross-sectional rank OOS — the primary falsifier F1.

    Returns dict with keys: mean_rank_ic, std_rank_ic, n_timestamps.
    """
    oos = results[results["is_oos"]].copy()
    if oos.empty:
        return {"mean_rank_ic": 0.0, "std_rank_ic": 0.0, "n_timestamps": 0}

    ics: list[float] = []
    for ts, grp in oos.groupby("open_time"):
        # Drop rows whose label_grade is NA/None — those rows have valid PnL
        # (included in compute_xs_sharpe) but no realised forward rank, so
        # they must not pollute the rank-IC calculation.
        grp_valid = grp[grp["label_grade"].notna()].copy()
        if len(grp_valid) < 2:
            continue
        label_vals = grp_valid["label_grade"].astype(float).values
        # Guard: if any NaN slipped through (e.g. object column with np.nan),
        # drop them to avoid corrupting std() / argsort().
        finite_mask = np.isfinite(label_vals)
        if finite_mask.sum() < 2:
            continue
        score_vals = grp_valid["predicted_score"].values[finite_mask]
        label_vals = label_vals[finite_mask]
        ic = _spearman_ic(score_vals, label_vals)
        ics.append(ic)

    if not ics:
        return {"mean_rank_ic": 0.0, "std_rank_ic": 0.0, "n_timestamps": 0}

    return {
        "mean_rank_ic": float(np.mean(ics)),
        "std_rank_ic": float(np.std(ics)),
        "n_timestamps": len(ics),
    }


def compute_xs_sharpe(results: pd.DataFrame, is_oos: bool) -> float:
    """Compute monthly Sharpe from the cross-sectional results DataFrame.

    Groups net_pnl by calendar month and computes Sharpe over the monthly
    PnL series.
    """
    mask = results["is_oos"] == is_oos
    sub = results[mask].copy()
    if sub.empty:
        return 0.0

    sub["month"] = sub["open_time"].apply(
        lambda t: datetime.datetime.fromtimestamp(t / 1000, tz=datetime.UTC).strftime("%Y-%m")
    )
    monthly = sub.groupby("month")["net_pnl"].sum()
    if len(monthly) < 2:
        return 0.0
    return float(monthly.mean() / monthly.std()) if monthly.std() > 0 else 0.0


# ---------------------------------------------------------------------------
# Utility: Spearman IC
# ---------------------------------------------------------------------------


def _spearman_ic(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation between x and y.

    Returns 0.0 if either array has zero variance (constant array),
    or if n < 2.
    """
    n = len(x)
    if n < 2:
        return 0.0
    # Guard: NaN in inputs corrupts std() and argsort().
    if np.any(np.isnan(x)) or np.any(np.isnan(y)):
        return 0.0
    # Detect degenerate inputs: constant arrays have no rank information.
    if x.std() < 1e-12 or y.std() < 1e-12:
        return 0.0
    # Rank both arrays (argsort of argsort = rank from 0 to n-1).
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    # Pearson on ranks = Spearman.
    mx, my = rx.mean(), ry.mean()
    num = ((rx - mx) * (ry - my)).sum()
    den = np.sqrt(((rx - mx) ** 2).sum() * ((ry - my) ** 2).sum())
    return float(num / den) if den > 1e-12 else 0.0

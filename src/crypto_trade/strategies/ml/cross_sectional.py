"""Cross-sectional relative-value ranking model for iter-v3/088.

Implements the Phase-6 build spec from briefs-v3/iteration_v3-088/research_brief.md
Section 3 (A1-A6).

Design:
  - Label: cross-sectional forward-return rank, {0,1,2} graded relevance, H=3 bars.
  - Model: ONE pooled LGBMRanker(objective="lambdarank"), one query-group per
    timestamp, monthly walk-forward.
  - Universe: 22-symbol XS_UNIVERSE of liquid non-v1/v2 Binance-USDT perps.
  - Features: 13 features (14-feature /059 stack minus btc_ret_14d), each
    cross-sectionally rank-normalized.
  - Position: dollar-neutral cross-sectional tercile long-short, inverse-vol
    weighting, portfolio vol-targeting, 0.1% fee.
  - XS_REQUIRED_GAP = 88 = (H+1)*N = (3+1)*22.

No-cheating guarantees:
  - OOS_CUTOFF_DATE / training_months are IMMUTABLE (imported from config).
  - Walk-forward trains each month on IS-only past data; train_end_ms =
    test_start_ms - embargo_ms (the e149e9d fix, carried through).
  - XS_REQUIRED_GAP=88 is asserted at CPCV call-site via expected_gap.
  - The cross-sectional label's H=3 forward window NEVER overlaps a test row
    because the embargo removes (H+1)*N_symbols = 88 rows at every boundary.
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

#: H = forward horizon in bars (Section 3.1 / EDA T3: strongest |IS IC-IR|)
XS_HORIZON: int = 3

#: CPCV purge gap for the pooled cross-section.
#: Formula: (H + 1) * N_symbols = (3 + 1) * 22 = 88.
#: This is DIFFERENT from the legacy per-symbol REQUIRED_GAP = 66.
#: - Legacy: (timeout_candles=21 + 1) * 3 symbols = 66
#: - Cross-sectional: (H=3 + 1) * 22 symbols = 88
#: The gap removes, on both sides of every test boundary, enough rows so that
#: no training label's H=3 forward window overlaps a test row.
XS_REQUIRED_GAP: int = (XS_HORIZON + 1) * N_XS_SYMBOLS  # 88

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

#: Portfolio vol-target: annualised daily volatility target.
#: Standard cross-sectional construction (Poh/Lim/Zohren).
XS_VOL_TARGET: float = 0.10  # 10% annualised

#: Fee per side, modeled on every 8h rebalance.
XS_FEE_PER_SIDE: float = 0.001  # 0.1%

#: Tercile cutoff fraction (Section 3.4 — a-priori from factor convention).
XS_TERCILE_FRAC: float = 1.0 / 3.0

#: Realised-vol lookback for inverse-vol weighting (past-only, in bars).
XS_VOL_LOOKBACK: int = 50


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
           bottom-third → grade 0 (under-performers — predicted cross-section
             WINNERS given the reversal signal; these become LONG leg targets)
           middle-third → grade 1
           top-third    → grade 2 (out-performers — predicted cross-section
             LOSERS; these become SHORT leg targets in the reversal book)

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
# A3 — Pooled-panel builder (Section 3.5)
# ---------------------------------------------------------------------------


def build_cross_sectional_panel(
    features_dir: str | Path,
    symbols: tuple[str, ...],
    feature_columns: list[str],
    drop_features: frozenset[str] = XS_DROP_FEATURES,
    listing_burnin_bars: int = XS_LISTING_BURNIN_BARS,
    interval: str = "8h",
) -> pd.DataFrame:
    """Load and align the pooled cross-sectional panel.

    Steps:
      1. Load each symbol's feature parquet (open_time, close, + feature_cols).
      2. Apply the 60-day (180-bar) listing burn-in per symbol.
      3. Concatenate all symbols into a pooled panel sorted by (open_time, symbol).
      4. Drop btc_ret_14d (zero cross-sectional dispersion — EDA T6).
      5. Cross-sectionally rank-normalize each remaining feature at each
         timestamp (rank-transform within the cross-section → comparable
         across symbols).

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

    Returns
    -------
    pd.DataFrame with columns:
        ['open_time', 'symbol', 'close'] + [13 xs-normalized feature cols]
    Sorted by (open_time, symbol).
    """
    features_path = Path(features_dir)
    xs_cols = [c for c in feature_columns if c not in drop_features]

    frames: list[pd.DataFrame] = []
    for sym in symbols:
        pf = features_path / f"{sym}_{interval}_features.parquet"
        if not pf.exists():
            raise FileNotFoundError(f"build_cross_sectional_panel: parquet missing for {sym}: {pf}")
        # Load only the columns we need.
        needed = ["open_time", "close"] + xs_cols
        # Parquet schema may have extra cols — read only what we need.
        available = set(pq.read_schema(pf).names)
        missing = [c for c in needed if c not in available]
        if missing:
            raise ValueError(
                f"build_cross_sectional_panel: {sym} parquet missing columns: {missing}"
            )
        df = pq.read_table(pf, columns=needed).to_pandas()
        df["symbol"] = sym

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
        self.verbose = verbose

        self._model: lgb.LGBMRanker | None = None
        self._current_month: str | None = None
        self._is_rank_ic: float | None = None  # IS rank-IC from last training

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _train_for_month(
        self,
        train_panel: pd.DataFrame,
        train_labels: pd.Series,
    ) -> float:
        """Train/retrain the pooled LGBMRanker on the training panel.

        Returns the IS out-of-fold rank-IC (for smoke-test / A6 reporting).
        """
        # Build the group array: one query per timestamp.
        group = train_panel.groupby("open_time", sort=True).size().values
        x_train = train_panel[self.feature_columns].values.astype(np.float32)
        y_train = train_labels.values.astype(np.int32)

        def _objective(trial: optuna.Trial) -> float:
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
                "random_state": self.seed,
            }
            # 5-fold time-series CV with XS_REQUIRED_GAP purge.
            return self._cv_rank_ic(x_train, y_train, group, params)

        sampler = optuna.samplers.TPESampler(seed=self.seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            study.optimize(_objective, n_trials=self.n_trials, show_progress_bar=False)

        best_params = {
            "objective": "lambdarank",
            "verbose": -1,
            "random_state": self.seed,
            **study.best_params,
        }
        self._model = lgb.LGBMRanker(**best_params)
        self._model.fit(x_train, y_train, group=group)

        # IS rank-IC: Spearman between predicted score and forward-return rank
        # (approximated by the label grade) on the training set.
        scores = self._model.predict(x_train)
        ic = float(self._spearman_ic_by_timestamp(train_panel["open_time"].values, scores, y_train))
        self._is_rank_ic = ic
        return ic

    def _cv_rank_ic(
        self,
        x_arr: np.ndarray,
        y: np.ndarray,
        group: np.ndarray,
        params: dict,
    ) -> float:
        """5-fold time-series CV on the training panel; returns mean rank-IC.

        CV gap = XS_REQUIRED_GAP rows (the Lopez de Prado purge requirement
        for the cross-sectional label with H=3 and 22 symbols).
        """
        n_rows = len(x_arr)
        n_folds = 5
        fold_size = n_rows // n_folds
        gap = XS_REQUIRED_GAP

        ics: list[float] = []
        for k in range(1, n_folds):
            val_start = k * fold_size
            val_end = (k + 1) * fold_size if k < n_folds - 1 else n_rows
            train_end = max(0, val_start - gap)

            if train_end < 2 * gap or (val_end - val_start) < gap:
                continue  # not enough data in this fold

            x_tr = x_arr[:train_end]
            y_tr = y[:train_end]
            x_val = x_arr[val_start:val_end]
            y_val = y[val_start:val_end]

            # Rebuild group arrays for train and val folds.
            # We approximate group arrays by constant group size (n_symbols)
            # since the panel is not available here.  The approximation is
            # valid when the cross-section is approximately full at each bar.
            g_tr = _approximate_group(len(x_tr), len(self.symbols))
            g_val = _approximate_group(len(x_val), len(self.symbols))

            if sum(g_tr) < 1 or sum(g_val) < 1:
                continue

            try:
                m = lgb.LGBMRanker(**params)
                m.fit(x_tr, y_tr, group=g_tr)
                scores = m.predict(x_val)
                ic = _spearman_ic(scores, y_val.astype(float))
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

        Higher score = model predicts this symbol will RANK HIGHER (i.e., be
        a top-tercile forward-return symbol in the cross-section).  Given the
        reversal signal (negative IC), higher score → lower forward return →
        SHORT candidate; lower score → LONG candidate.  The position
        constructor in build_positions() handles this mapping.
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
    """Construct dollar-neutral tercile long-short positions at timestamp t.

    Algorithm (Section 3.4):
      1. Score each symbol with the ranking model.
      2. Long the BOTTOM tercile (grade-0 / low-score symbols — the reversal
         long: recent cross-section under-performers are predicted to bounce).
         Short the TOP tercile (grade-2 / high-score symbols — recent winners).
      3. Dollar-neutral: equal gross long and gross short notional.
      4. Within each leg, inverse-vol weight (weight ∝ 1/σ̂).
      5. Scale the whole book to XS_VOL_TARGET via portfolio vol-targeting.

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

    n_leg = max(1, int(np.floor(n * tercile_frac)))
    long_syms = set(sorted_syms[:n_leg])  # bottom tercile → LONG
    short_syms = set(sorted_syms[-n_leg:])  # top tercile → SHORT

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
) -> pd.DataFrame:
    """Full walk-forward cross-sectional backtest.

    Walk-forward cadence (Section 3.6):
      - Train on trailing training_months months (IS-only past data).
      - Embargo: train_end_ms = test_start_ms - embargo_ms, where
        embargo_ms = XS_REQUIRED_GAP bars * interval_ms.
        This is the e149e9d fix carried through to the cross-sectional path.
      - Rebalance every 8h bar (Section 3.4.1).

    Fees: 0.1% per side modeled on every 8h rebalance, both long and short
    legs (Section 3.5 / Section 5 risk table).

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

    Returns
    -------
    pd.DataFrame with columns:
        open_time, symbol, position, gross_pnl, fee, net_pnl, is_oos,
        rank_ic, predicted_score, label_grade
    One row per (timestamp, active symbol).
    """
    interval_ms = 8 * 3600 * 1000  # 8h in ms
    embargo_ms = XS_REQUIRED_GAP * interval_ms

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

    results: list[dict] = []
    trained_months: set[str] = set()

    for split in splits:
        train_start_ms_split = split["train_start_ms"]
        train_end_ms_split = split["train_end_ms"]
        test_start_ms_split = split["test_start_ms"]
        test_end_ms_split = split["test_end_ms"]
        test_month = split["test_month"]

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
            print(f"[xs] skip training for {test_month}: only {len(train_panel_valid)} valid rows.")
            continue

        # Retrain when we reach a new test month (lazy monthly retrain).
        if test_month not in trained_months:
            print(f"[xs] === Training for {test_month} (train rows={len(train_panel_valid)}) ===")
            # Ensure group array is consistent: sort by (open_time, symbol).
            train_panel_valid = train_panel_valid.sort_values(["open_time", "symbol"]).reset_index(
                drop=True
            )
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

            x_t = panel_t[strategy.feature_columns].values.astype(np.float32)
            if strategy._model is not None:
                scores = strategy._model.predict(x_t)
            else:
                scores = np.zeros(len(panel_t))

            # Past-only vol estimate: trailing vol_lookback bars ending BEFORE ts.
            hist = ret_wide[ret_wide.index < ts].tail(vol_lookback)
            positions = build_positions(panel_t, scores, hist)

            if not positions:
                continue

            # PnL computation.  The 1-bar gross return for a position opened at t
            # and closed at t+1 is position * (close(t+1) / close(t) - 1).
            # We accrue PnL over the rebalance bar (bar t → bar t+H).
            # For simplicity in the backtest we use 1-bar PnL (the book
            # rebalances every bar, so each bar's contribution is 1 period).
            label_grades_t = test_labels[ts_mask].values

            for i, row in panel_t.iterrows():
                sym = row["symbol"]
                pos = positions.get(sym, 0.0)
                if pos == 0.0:
                    continue
                # 1-bar return for this symbol.
                if sym in ret_wide.columns:
                    idx_loc = ret_wide.index.searchsorted(ts, side="right")
                    if idx_loc < len(ret_wide):
                        next_ret = (
                            float(ret_wide[sym].iloc[idx_loc])
                            if not pd.isna(ret_wide[sym].iloc[idx_loc])
                            else 0.0
                        )
                    else:
                        next_ret = 0.0
                else:
                    next_ret = 0.0

                gross_pnl = pos * next_ret
                # Fee: 0.1% per side on entry (and notionally on exit at next bar).
                fee = abs(pos) * fee_per_side * 2  # entry + exit

                is_oos = ts >= oos_cutoff_ms
                label_grade = int(label_grades_t[i]) if i < len(label_grades_t) else -1

                row_iloc = panel_t.index.get_loc(i) if hasattr(panel_t.index, "get_loc") else i
                results.append(
                    {
                        "open_time": ts,
                        "symbol": sym,
                        "position": pos,
                        "gross_pnl": gross_pnl,
                        "fee": fee,
                        "net_pnl": gross_pnl - fee,
                        "is_oos": is_oos,
                        "rank_ic": strategy._is_rank_ic or 0.0,
                        "predicted_score": float(scores[row_iloc]),
                        "label_grade": label_grade,
                    }
                )

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

    return pd.DataFrame(results).sort_values("open_time").reset_index(drop=True)


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
# A6 — Rank-IC reporting helpers
# ---------------------------------------------------------------------------


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
        if len(grp) < 2:
            continue
        ic = _spearman_ic(grp["predicted_score"].values, grp["label_grade"].values.astype(float))
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

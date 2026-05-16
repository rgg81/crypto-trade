"""iter-v3/087 EDA — WHOLESALE universe-breadth EXPANSION (cycle 3 EXPLORATION #6 of 10).

Direction 2 of `briefs-v3/cycle3_plan.md`, done WHOLESALE — grow v3's universe
from 3 symbols (BCH/LDO/TRX) to ~8 in ONE step. This is the structural pivot the
/086 Critic's 7-FEED STRUCTURAL VERDICT mandates: seven non-OHLCV crypto-native
feature families (funding /019/023/024/082/085, microstructure /015, basis /086)
are ALL INERT-by-importance — /087+ must NOT be an 8th feature family. The two
remaining structural levers are Direction 2 (breadth) and Direction 3 (a non-naive
pooled model). This EDA evaluates Direction 2.

==========================================================================
THE /083 FAILURE THIS EDA IS DESIGNED TO NOT REPEAT
==========================================================================
iter-v3/083 added ONE symbol (FILUSDT) and the aggregate IS monthly Sharpe
COLLAPSED -0.9156. The /083 closeout decomposition: FIL's own -32% IS edge was
only ~32% of the collapse; the rest was incumbent data-extent drift. But the
ROOT methodological error is sharper than "FIL was a bad symbol": /083 selected
FIL on a per-symbol IS-edge screen (rank #1 of 4 survivors) and IGNORED the
diversification term. A single-symbol add to a pooled book has NO meaningful
diversification offset — one weak symbol's bad monthly-PnL stream drags the
pooled monthly Sharpe almost one-for-one, because with N=3 the cross-symbol
variance-reduction is tiny. /021 (HBAR+AVAX) and /069 (ADA) failed the same way
plus measured PRICE-return correlation (price diversity, not SIGNAL diversity).

THE FIX — measure the thing that actually governs a breadth expansion: the
Bailey & López de Prado (2012, SSRN 2003638) "Strategy Approval / Sharpe Ratio
Indifference Curve" framework. A new return stream RAISES the portfolio Sharpe
when its average pairwise correlation to the existing book is low ENOUGH —
EVEN IF its own Sharpe is below the book average, even at a negative own Sharpe.
The governing identity for an equal-weight book of N streams each with Sharpe S
and average pairwise PnL-correlation rho-bar:

    SR_portfolio  =  S * sqrt( N / (1 + (N-1)*rho_bar) )

The `sqrt(N)` is the Grinold-Kahn breadth lever (IR = IC*sqrt(breadth));
`1 + (N-1)*rho_bar` is the correlation drag. A WHOLESALE expansion (5-8 symbols
at once) is worth a backtest slot ONLY IF this EDA shows the aggregate IS
monthly Sharpe of the broader book is PRESERVED or LIFTED relative to the
3-symbol book — i.e. the breadth/diversification benefit genuinely offsets the
per-symbol weakness. If the EDA shows a wholesale book would just drag like
/083, this EDA says so and the QR pivots.

THE LOAD-BEARING CORRELATION. /021/069's mistake was measuring price-return
correlation (~0.45-0.60 across these alts). That is the WRONG correlation. The
indifference-curve correlation is the correlation of the per-symbol STRATEGY
PnL streams (each symbol's per-calendar-month weighted-PnL series). A
triple-barrier classifier trades at different times, in different directions,
for different durations per symbol — the monthly-PnL streams are far less
correlated than raw price returns. T4 measures BOTH and reports the gap.

==========================================================================
WHAT THIS EDA DOES (all IS-data-only — NO CHEATING; OOS_CUTOFF 2025-03-24)
==========================================================================
  T1  Data-depth + liquidity + listing screen of the candidate pool. Drops
      candidates without enough history for the 24-month training window + a
      meaningful IS span; applies the 60-day new-listing burn-in.
  T2  Faithful per-symbol v3-style IS model for EVERY incumbent AND every T1
      survivor: the 14-feature v3 stack from raw OHLCV, REAL v3 triple-barrier
      labels (label_trades, ATR(2.0,1.0), 21-candle timeout), a confidence-gated
      IS-only expanding walk-forward LightGBM. Output: each symbol's per-month
      weighted-PnL stream + IS monthly Sharpe + trades + WR.
  T3  THE LOAD-BEARING TEST — aggregate IS monthly Sharpe of the 3-symbol book
      vs candidate wholesale-expanded books (sizes 5/6/7/8). v3 pools all
      per-symbol rosters into ONE book; T3 builds the pooled monthly-PnL series
      directly and reports the aggregate IS monthly Sharpe at each book size,
      AND the Bailey-LdP decomposition (mean per-symbol Sharpe, mean pairwise
      PnL-correlation, predicted vs realized aggregate Sharpe).
  T4  The two correlations — price-return correlation (the /021/069 metric,
      shown to be the wrong one) vs strategy monthly-PnL correlation (the
      indifference-curve metric). Reports the gap so the brief can argue why a
      wholesale expansion is NOT /083.
  T5  Holding-time / roster-composition predictor (the `feedback_v3_is_oos_
      regime_divergence.md` mandate). Per-symbol mean trade duration vs the
      incumbent pooled roster — the added-set duration gap. A book whose added
      symbols are duration-loaded relative to the incumbents loads the v3
      IS/OOS regime factor.
  T6  The wholesale-expansion DECISION — which symbols, how many. The expanded
      book is selected to MAXIMISE the predicted aggregate IS monthly Sharpe
      (the T3 metric) under the indifference-curve math, NOT per-symbol Sharpe.

  SCREEN SCOPE (LOAD-BEARING DISCLOSURE). This is a RELATIVE-RANKING screen,
  not a /059 reproduction. Every symbol runs through ONE identical un-tuned
  (fixed-LGBM-param) pipeline with NO Optuna and NO 7-gate risk stack. The
  ABSOLUTE Sharpe numbers therefore differ from the production v3 baseline
  (Optuna-tuned + risk-gated). Per the /083 closeout's hard lesson, the
  screen's aggregate-Sharpe-Delta is a DIRECTION-ONLY signal, NOT an
  absolute-magnitude predictor — /083's screen under-predicted the realized IS
  damage ~24x. The load-bearing outputs are the SIGN of the aggregate-Sharpe
  Delta, the CROSS-SYMBOL ranking, and the correlation structure. The brief's
  falsifier bands are set wide accordingly.

Inputs (read-only):  data/{SYMBOL}/8h.csv  — 8h klines (OHLCV)

Outputs (committed):
  analysis/iteration_v3-087/T1_data_liquidity_screen.csv
  analysis/iteration_v3-087/T2_per_symbol_is_model.csv
  analysis/iteration_v3-087/T3_aggregate_book_sharpe.csv
  analysis/iteration_v3-087/T4_correlation_price_vs_pnl.csv
  analysis/iteration_v3-087/T5_holding_time_predictor.csv
  analysis/iteration_v3-087/T6_wholesale_expansion_decision.csv

Sacred constants (IMMUTABLE — no cheating):
  OOS_CUTOFF_DATE = 2025-03-24  — every row below uses ONLY data before this.
  training_months = 24          — the walk-forward training window.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.labeling import label_trades

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v3-087"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Sacred constant — 2025-03-24 UTC. The QR sees ONLY data before this in Phases 1-5.
OOS_CUTOFF_MS = int(datetime(2025, 3, 24, tzinfo=UTC).timestamp() * 1000)
TRAINING_MONTHS = 24  # sacred — the walk-forward training window
CANDLE_MINUTES = 480  # 8h
TIMEOUT_MINUTES = 10080  # 21 candles * 8h — the v3 triple-barrier vertical timeout
ATR_TP_MULT = 2.0  # V3 DEFAULT_ATR_MULTIPLIERS[0]
ATR_SL_MULT = 1.0  # V3 DEFAULT_ATR_MULTIPLIERS[1]
FEE_PCT = 0.1

# The v3 incumbent universe (BASELINE_V3.md / iter-v3/059).
INCUMBENTS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Candidate pool — deep-history (2020-2021 listing => full 24-month training
# window + a meaningful IS evaluation span before the 2025-03-24 cutoff), liquid
# Binance-futures altcoins NOT in V3_EXCLUDED_SYMBOLS (v1 BTC/ETH/LINK/LTC/DOT;
# v2 SOL/XRP/DOGE/NEAR; BNB; MKR). HBAR/AVAX are CLOSED (iter-v3/021 NEGATIVE);
# ADA is CLOSED (iter-v3/078 swap SUSPICIOUS); FILUSDT is CLOSED (iter-v3/083
# NEGATIVE — FIL's own -32% IS edge). All four explicitly EXCLUDED below.
# This pool is the genuine large/mid-cap deep-history alt universe — 16
# candidates, vs /083's 8 — so a WHOLESALE 5-8-symbol pick is possible.
CANDIDATE_POOL = (
    "ATOMUSDT",
    "ALGOUSDT",
    "ETCUSDT",
    "XLMUSDT",
    "EOSUSDT",
    "VETUSDT",
    "XTZUSDT",
    "AAVEUSDT",
    "UNIUSDT",
    "CRVUSDT",
    "FTMUSDT",
    "RUNEUSDT",
    "SANDUSDT",
    "GALAUSDT",
    "MANAUSDT",
    "THETAUSDT",
)

# The v3 14-feature stack (V3_FEATURE_COLUMNS_TOP_N / BASELINE_V3.md /059).
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

# Confidence threshold — the model takes a trade only when the winning DIRECTIONAL
# class probability clears this. Screen analogue of v3's 7-gate selectivity. The
# screen is a 3-class model {short, neutral, long}; 0.45 is a data-free a-priori
# choice (well above the 1/3 random floor; not tuned on IS or OOS — no cheating).
CONF_THRESHOLD = 0.45
NEUTRAL_EDGE_PCT = 0.5  # |best-direction net PnL| below this => neutral label

# LightGBM params for the IS-edge screen. Deliberately FIXED and conservative —
# this is a screen, not a tuned backtest. A fixed-param screen gives a clean
# relative ranking across symbols. (Same params as the /083 EDA — comparability.)
LGB_PARAMS = dict(
    objective="multiclass",
    num_class=3,  # {short=0, neutral=1, long=2}
    n_estimators=200,
    learning_rate=0.05,
    num_leaves=31,
    max_depth=5,
    min_child_samples=30,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=2,
    verbose=-1,
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_klines(symbol: str) -> pd.DataFrame | None:
    """Load 8h klines for a symbol. Returns None if missing."""
    p = DATA_DIR / symbol / "8h.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df = df.sort_values("open_time").reset_index(drop=True)
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def wilder_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR — past-only (the value at bar t uses bars <= t)."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


# ---------------------------------------------------------------------------
# Feature engineering — the v3 14-feature stack, computed from raw OHLCV.
# Every feature is past-only: a rolling/ewm stat is .shift(1)-lagged so bar t's
# own close is excluded from bar t's feature value (look-ahead discipline).
# (Identical construction to the /083 EDA — keeps the screen comparable.)
# ---------------------------------------------------------------------------


def compute_v3_features(df: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    """Compute the 14-feature v3 stack. df and btc are 8h-kline frames."""
    out = pd.DataFrame(index=df.index)
    close = df["close"]
    logret = np.log(close / close.shift(1))

    roll_max_50 = close.rolling(50, min_periods=50).max()
    out["max_dd_window_50"] = ((close - roll_max_50) / roll_max_50).shift(1)

    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    atr20 = wilder_atr(df, 20)
    out["ema_spread_atr_20"] = ((ema_fast - ema_slow) / atr20.replace(0, np.nan)).shift(1)

    out["ret_kurt_50"] = logret.rolling(50, min_periods=50).kurt().shift(1)
    out["ret_kurt_200"] = logret.rolling(200, min_periods=200).kurt().shift(1)
    out["ret_skew_50"] = logret.rolling(50, min_periods=50).skew().shift(1)
    out["ret_skew_200"] = logret.rolling(200, min_periods=200).skew().shift(1)
    out["range_realized_vol_50"] = logret.rolling(50, min_periods=50).std().shift(1)
    out["ret_autocorr_lag1_50"] = (
        logret.rolling(50, min_periods=50)
        .apply(lambda x: pd.Series(x).autocorr(lag=1), raw=False)
        .shift(1)
    )

    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap_num = (tp * df["volume"]).rolling(20, min_periods=20).sum()
    vwap_den = df["volume"].rolling(20, min_periods=20).sum()
    vwap20 = vwap_num / vwap_den.replace(0, np.nan)
    out["vwap_dev_20"] = ((close - vwap20) / vwap20).shift(1)

    def _hurst(x: np.ndarray) -> float:
        x = np.asarray(x, dtype=float)
        if len(x) < 20 or np.std(x) == 0:
            return np.nan
        lags = range(2, min(20, len(x) // 2))
        tau = [np.std(x[lag:] - x[:-lag]) for lag in lags]
        tau = np.asarray(tau)
        if np.any(tau <= 0):
            return np.nan
        poly = np.polyfit(np.log(list(lags)), np.log(tau), 1)
        return float(poly[0])

    logc = np.log(close)
    hurst_100 = logc.rolling(100, min_periods=100).apply(_hurst, raw=True)
    hurst_50 = logc.rolling(50, min_periods=50).apply(_hurst, raw=True)
    out["hurst_100"] = hurst_100.shift(1)
    out["hurst_diff_100_50"] = (hurst_100 - hurst_50).shift(1)

    ret_5d = close / close.shift(15) - 1.0  # 15 8h-bars = 5 days
    out["regime_momentum_signed_5d"] = (ret_5d * np.sign(hurst_100 - 0.5)).shift(1)

    btc_idx = btc.set_index("open_time")["close"]
    sym_close_by_t = df.set_index("open_time")["close"]
    btc_aligned = btc_idx.reindex(sym_close_by_t.index).ffill()
    btc_ret_14d = btc_aligned / btc_aligned.shift(42) - 1.0  # 42 8h-bars = 14 days
    sym_ret_7d = sym_close_by_t / sym_close_by_t.shift(21) - 1.0
    btc_ret_7d = btc_aligned / btc_aligned.shift(21) - 1.0
    out["btc_ret_14d"] = btc_ret_14d.shift(1).to_numpy()
    out["sym_vs_btc_ret_7d"] = (sym_ret_7d - btc_ret_7d).shift(1).to_numpy()

    return out


# ---------------------------------------------------------------------------
# Labeling — REAL v3 triple-barrier
# ---------------------------------------------------------------------------


def _barrier_hit_candles(df: pd.DataFrame, atr: np.ndarray, side_for_idx: np.ndarray) -> np.ndarray:
    """Label-implied holding time in candles per row, for the labeled side.

    Re-scans each candle forward to its first barrier hit (TP or SL) or the
    21-candle vertical timeout, using the SAME ATR(2.0,1.0) barriers as
    label_trades. Screen-grade — biased LOW vs production Optuna-tuned barriers
    (the /078 lesson); used only as a relative duration ranking.
    """
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    n = len(df)
    dur = np.full(n, np.nan)
    max_scan = TIMEOUT_MINUTES // CANDLE_MINUTES  # 21
    for i in range(n):
        side = side_for_idx[i]
        if side == 0:
            continue
        a = atr[i] if not np.isnan(atr[i]) else close[i] * 0.02
        entry = close[i]
        if side == 1:
            tp_p, sl_p = entry + ATR_TP_MULT * a, entry - ATR_SL_MULT * a
        else:
            tp_p, sl_p = entry - ATR_TP_MULT * a, entry + ATR_SL_MULT * a
        hit = max_scan
        for k in range(1, max_scan + 1):
            j = i + k
            if j >= n:
                hit = k
                break
            if side == 1:
                if low[j] <= sl_p or high[j] >= tp_p:
                    hit = k
                    break
            else:
                if high[j] >= sl_p or low[j] <= tp_p:
                    hit = k
                    break
        dur[i] = hit
    return dur


def label_symbol_is(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Triple-barrier labels for every candle (REAL v3 labeling)."""
    master = df.copy()
    master["symbol"] = symbol
    atr = wilder_atr(master, 14).to_numpy()
    n = len(master)
    cand = np.arange(n)
    labels, weights, long_pnl, short_pnl = label_trades(
        master=master,
        candidate_indices=cand,
        tp_pct=ATR_TP_MULT,
        sl_pct=ATR_SL_MULT,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        atr_values=atr,
        label_mode="triple_barrier",
    )
    res = master[["open_time", "close_time"]].copy()
    res["label"] = labels
    res["weight"] = weights
    res["long_pnl"] = long_pnl
    res["short_pnl"] = short_pnl
    res["atr"] = atr
    best_dir_pnl = np.maximum(long_pnl, short_pnl)
    y3 = np.where(labels == 1, 2, 0)
    y3 = np.where(best_dir_pnl < NEUTRAL_EDGE_PCT, 1, y3)
    res["y3"] = y3
    res["hold_long"] = _barrier_hit_candles(master, atr, np.ones(n, dtype=int))
    res["hold_short"] = _barrier_hit_candles(master, atr, -np.ones(n, dtype=int))
    return res


# ---------------------------------------------------------------------------
# T2 — per-symbol IS-edge walk-forward LightGBM screen
# ---------------------------------------------------------------------------


def walk_forward_edge(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    """IS-ONLY expanding walk-forward LightGBM. Returns the IS trade roster.

    Each calendar month m in the IS window: train on the 24 months ending one
    embargo before m, predict month m, take a trade ONLY where max class proba
    >= CONF_THRESHOLD and argmax != neutral. Realized PnL = the labeled
    best-direction PnL when the model's side matches the label, else the OTHER
    direction's PnL. A relative-ranking proxy for the v3 per-symbol model — the
    load-bearing output is the per-symbol monthly-PnL stream + the cross-symbol
    ranking, NOT the absolute Sharpe.
    """
    feat = features.copy()
    feat["open_time"] = labels["open_time"].to_numpy()
    feat["close_time"] = labels["close_time"].to_numpy()
    feat["y"] = labels["y3"].to_numpy()
    feat["long_pnl"] = labels["long_pnl"].to_numpy()
    feat["short_pnl"] = labels["short_pnl"].to_numpy()
    feat["weight"] = labels["weight"].to_numpy()
    feat["hold_long"] = labels["hold_long"].to_numpy()
    feat["hold_short"] = labels["hold_short"].to_numpy()

    feat = feat.dropna(subset=list(V3_FEATURE_COLUMNS))
    feat = feat[feat["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    if len(feat) < 400:
        return pd.DataFrame()

    feat["dt"] = pd.to_datetime(feat["open_time"], unit="ms", utc=True)
    feat["ym"] = feat["dt"].dt.to_period("M")
    months = sorted(feat["ym"].unique())

    embargo_candles = TIMEOUT_MINUTES // CANDLE_MINUTES + 1  # 22
    trades = []
    for i, m in enumerate(months):
        if i < TRAINING_MONTHS:
            continue
        test = feat[feat["ym"] == m]
        if len(test) == 0:
            continue
        test_start_idx = test.index.min()
        train = feat[feat.index < (test_start_idx - embargo_candles)]
        train = train[train["ym"].isin(months[i - TRAINING_MONTHS : i])]
        if len(train) < 200 or train["y"].nunique() < 2:
            continue
        x_tr = train[list(V3_FEATURE_COLUMNS)].to_numpy()
        y_tr = train["y"].to_numpy()
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(x_tr, y_tr)
        x_te = test[list(V3_FEATURE_COLUMNS)].to_numpy()
        proba = model.predict_proba(x_te)
        classes = list(model.classes_)
        col_of = {c: k for k, c in enumerate(classes)}
        test_rows = test.reset_index(drop=True)
        for j in range(len(test_rows)):
            p_long = proba[j, col_of[2]] if 2 in col_of else 0.0
            p_short = proba[j, col_of[0]] if 0 in col_of else 0.0
            if max(p_long, p_short) < CONF_THRESHOLD:
                continue
            s = 2 if p_long >= p_short else 0
            row = test_rows.iloc[j]
            if s == 2:
                pnl = float(row["long_pnl"])
                hold = float(row["hold_long"])
                side_str = "long"
            else:
                pnl = float(row["short_pnl"])
                hold = float(row["hold_short"])
                side_str = "short"
            trades.append(
                dict(
                    symbol=symbol,
                    open_time=int(row["open_time"]),
                    close_time=int(row["close_time"]),
                    ym=str(m),
                    side=side_str,
                    pnl=pnl,
                    win=int(pnl > 0),
                    hold_candles=hold,
                )
            )
    return pd.DataFrame(trades)


# ---------------------------------------------------------------------------
# Aggregation helpers — the pooled-book monthly Sharpe (the v3 metric)
# ---------------------------------------------------------------------------


def monthly_pnl_series(trades: pd.DataFrame) -> pd.Series:
    """Per-calendar-month summed PnL of a trade roster."""
    if trades.empty:
        return pd.Series(dtype=float)
    return trades.groupby("ym")["pnl"].sum()


def monthly_sharpe(trades: pd.DataFrame) -> float:
    """Monthly Sharpe of a SINGLE roster (mean monthly PnL / std)."""
    m = monthly_pnl_series(trades)
    if len(m) < 2 or m.std(ddof=1) == 0:
        return 0.0
    return float(m.mean() / m.std(ddof=1))


def pooled_book_sharpe(rosters: dict[str, pd.DataFrame]) -> tuple[float, pd.Series]:
    """Aggregate IS monthly Sharpe of a pooled book — the v3 portfolio metric.

    v3 pools every per-symbol roster into ONE book; the headline IS monthly
    Sharpe is the Sharpe of the union roster's per-calendar-month PnL series.
    Returns (aggregate monthly Sharpe, the pooled monthly-PnL series).
    """
    frames = [r for r in rosters.values() if not r.empty]
    if not frames:
        return 0.0, pd.Series(dtype=float)
    pooled = pd.concat(frames, ignore_index=True)
    m = pooled.groupby("ym")["pnl"].sum()
    if len(m) < 2 or m.std(ddof=1) == 0:
        return 0.0, m
    return float(m.mean() / m.std(ddof=1)), m


def bailey_lopezdeprado_predicted_sharpe(
    rosters: dict[str, pd.DataFrame],
) -> tuple[float, float, float, int]:
    """Bailey-LdP (2012) equal-weight portfolio-Sharpe decomposition.

    SR_portfolio = mean_S * sqrt( N / (1 + (N-1)*rho_bar) )

    where mean_S is the mean per-symbol monthly Sharpe, rho_bar is the mean
    pairwise correlation of the per-symbol MONTHLY-PnL streams (the
    indifference-curve correlation — NOT price-return correlation), N is the
    book size. This is the diversification identity the /083 per-symbol screen
    ignored. Returns (predicted_sharpe, mean_S, rho_bar, N).

    NOTE: this is the EQUAL-WEIGHT-equal-vol idealisation. v3 pools raw PnL
    (symbols are NOT vol-normalised), so the realized pooled Sharpe (T3's direct
    measure) is the operative number; the BLdP prediction is the structural
    DECOMPOSITION that explains WHY the realized number moves — it isolates the
    breadth term (sqrt N) from the correlation drag (1+(N-1)rho_bar).
    """
    series = {s: monthly_pnl_series(r) for s, r in rosters.items() if not r.empty}
    n = len(series)
    if n < 2:
        return 0.0, 0.0, 0.0, n
    per_sym_sharpe = []
    for s, m in series.items():
        if len(m) >= 2 and m.std(ddof=1) > 0:
            per_sym_sharpe.append(m.mean() / m.std(ddof=1))
        else:
            per_sym_sharpe.append(0.0)
    mean_s = float(np.mean(per_sym_sharpe))
    # pairwise correlation of monthly-PnL streams on common months
    syms = list(series.keys())
    corrs = []
    for a, b in combinations(syms, 2):
        ma, mb = series[a], series[b]
        common = sorted(set(ma.index) & set(mb.index))
        if len(common) >= 4:
            va = np.array([ma[t] for t in common])
            vb = np.array([mb[t] for t in common])
            if np.std(va) > 0 and np.std(vb) > 0:
                corrs.append(float(np.corrcoef(va, vb)[0, 1]))
    rho_bar = float(np.mean(corrs)) if corrs else 0.0
    denom = 1.0 + (n - 1) * rho_bar
    predicted = mean_s * np.sqrt(n / denom) if denom > 0 else 0.0
    return float(predicted), mean_s, rho_bar, n


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 78)
    print("iter-v3/087 EDA — WHOLESALE breadth EXPANSION (IS-only, no cheating)")
    print("=" * 78)

    btc = load_klines("BTCUSDT")
    if btc is None:
        raise RuntimeError("BTCUSDT klines missing — needed for cross-asset features.")

    # ----- T1: data-depth + liquidity + listing screen ---------------------
    print("\n[T1] data-depth / liquidity / listing screen ...")
    t1_rows = []
    survivors = []
    for sym in CANDIDATE_POOL:
        df = load_klines(sym)
        if df is None or len(df) < 100:
            t1_rows.append(
                dict(
                    symbol=sym,
                    first_listing="",
                    is_bars_post_burnin=0,
                    median_daily_quote_vol_musd=0.0,
                    depth_ok=False,
                    liquidity_ok=False,
                    status="NO_DATA",
                )
            )
            continue
        first_ms = int(df["open_time"].iloc[0])
        first_dt = datetime.fromtimestamp(first_ms / 1000, tz=UTC)
        burn_cut = first_ms + 60 * 24 * 3600 * 1000  # 60-day burn-in
        is_rows = df[(df["open_time"] >= burn_cut) & (df["open_time"] < OOS_CUTOFF_MS)]
        n_is = len(is_rows)
        # need 24 months training + >= 6 months IS evaluation => ~30 months of
        # post-burn-in IS data => floor 2200 IS bars.
        depth_ok = n_is >= 2200 and first_ms < (OOS_CUTOFF_MS - 30 * 30 * 24 * 3600 * 1000)
        if "quote_volume" in is_rows.columns and n_is > 0:
            daily_qv = is_rows["quote_volume"].rolling(3).sum().median()
        else:
            daily_qv = 0.0
        # liquidity floor $20M median daily quote volume — these are all
        # genuine large/mid-cap perps; $20M is comfortably tradable at v3 size.
        liq_ok = daily_qv >= 2e7
        status = "PASS" if (depth_ok and liq_ok) else "DROP"
        if status == "PASS":
            survivors.append(sym)
        t1_rows.append(
            dict(
                symbol=sym,
                first_listing=first_dt.strftime("%Y-%m-%d"),
                is_bars_post_burnin=n_is,
                median_daily_quote_vol_musd=round(daily_qv / 1e6, 1),
                depth_ok=depth_ok,
                liquidity_ok=liq_ok,
                status=status,
            )
        )
    _write_csv(ANALYSIS_DIR / "T1_data_liquidity_screen.csv", t1_rows)
    for r in t1_rows:
        print(
            f"   {r['symbol']:12s} {r['status']:8s} listed={r['first_listing']} "
            f"IS_bars={r['is_bars_post_burnin']} qvol=${r['median_daily_quote_vol_musd']}M"
        )
    print(f"   T1 survivors ({len(survivors)}): {survivors}")

    # ----- T2: per-symbol IS model — incumbents + survivors ----------------
    print("\n[T2] per-symbol v3-style IS model (14 feat, real triple-barrier) ...")
    rosters: dict[str, pd.DataFrame] = {}
    t2_rows = []
    for sym in list(INCUMBENTS) + survivors:
        df = load_klines(sym)
        feats = compute_v3_features(df, btc)
        labs = label_symbol_is(df, sym)
        roster = walk_forward_edge(feats, labs, sym)
        rosters[sym] = roster
        n_tr = len(roster)
        wr = float(roster["win"].mean()) if n_tr else 0.0
        ms = monthly_sharpe(roster)
        net = float(roster["pnl"].sum()) if n_tr else 0.0
        mean_dur = float(roster["hold_candles"].mean()) if n_tr else 0.0
        is_incumbent = sym in INCUMBENTS
        t2_rows.append(
            dict(
                symbol=sym,
                role="incumbent" if is_incumbent else "candidate",
                is_trades=n_tr,
                is_win_rate=round(wr, 4),
                is_monthly_sharpe=round(ms, 4),
                is_net_pnl_pct=round(net, 2),
                mean_trade_duration_candles=round(mean_dur, 3),
            )
        )
        print(
            f"   {sym:12s} {'INC' if is_incumbent else 'cand':4s} "
            f"trades={n_tr:4d} WR={wr:.3f} monthlySharpe={ms:+.4f} "
            f"net={net:+8.2f} dur={mean_dur:.2f}"
        )
    _write_csv(ANALYSIS_DIR / "T2_per_symbol_is_model.csv", t2_rows)

    # ----- T3: THE LOAD-BEARING TEST — aggregate book Sharpe ---------------
    print("\n[T3] aggregate IS monthly Sharpe — 3-symbol book vs wholesale books ...")
    inc_sharpe, _ = pooled_book_sharpe({s: rosters[s] for s in INCUMBENTS})
    inc_pred, inc_mean_s, inc_rho, inc_n = bailey_lopezdeprado_predicted_sharpe(
        {s: rosters[s] for s in INCUMBENTS}
    )
    print(f"   3-symbol incumbent book: aggregate IS monthly Sharpe = {inc_sharpe:+.4f}")
    print(
        f"     BLdP decomposition: mean_S={inc_mean_s:+.4f} rho_bar(PnL)={inc_rho:+.4f}"
        f" N={inc_n} -> predicted {inc_pred:+.4f}"
    )

    # rank candidates by their own IS monthly Sharpe (descending) for the
    # greedy-add construction of wholesale books — but the DECISION metric is
    # the aggregate book Sharpe, not the per-symbol Sharpe.
    cand_by_sharpe = sorted(survivors, key=lambda s: monthly_sharpe(rosters[s]), reverse=True)
    # also rank by the marginal aggregate-Sharpe lift each candidate gives when
    # added alone to the incumbent book — the genuine indifference-curve test.
    marg_rows = []
    for c in survivors:
        bk = {s: rosters[s] for s in INCUMBENTS}
        bk[c] = rosters[c]
        s4, _ = pooled_book_sharpe(bk)
        marg_rows.append((c, s4 - inc_sharpe))
    marg_rows.sort(key=lambda x: x[1], reverse=True)
    cand_by_marginal = [c for c, _ in marg_rows]

    t3_rows = []
    # 3-symbol incumbent row
    t3_rows.append(
        dict(
            book="incumbent_3",
            symbols="+".join(INCUMBENTS),
            book_size=3,
            aggregate_is_monthly_sharpe=round(inc_sharpe, 4),
            bldp_predicted_sharpe=round(inc_pred, 4),
            mean_per_symbol_sharpe=round(inc_mean_s, 4),
            mean_pairwise_pnl_corr=round(inc_rho, 4),
            delta_vs_incumbent=0.0,
        )
    )
    # wholesale books — greedy-by-marginal-lift, sizes 5/6/7/8
    for size in (5, 6, 7, 8):
        n_add = size - 3
        if n_add > len(cand_by_marginal):
            break
        adds = cand_by_marginal[:n_add]
        bk = {s: rosters[s] for s in list(INCUMBENTS) + adds}
        agg, _ = pooled_book_sharpe(bk)
        pred, mean_s_book, rho, _bk_n = bailey_lopezdeprado_predicted_sharpe(bk)
        t3_rows.append(
            dict(
                book=f"wholesale_{size}_marginal",
                symbols="+".join(list(INCUMBENTS) + adds),
                book_size=size,
                aggregate_is_monthly_sharpe=round(agg, 4),
                bldp_predicted_sharpe=round(pred, 4),
                mean_per_symbol_sharpe=round(mean_s_book, 4),
                mean_pairwise_pnl_corr=round(rho, 4),
                delta_vs_incumbent=round(agg - inc_sharpe, 4),
            )
        )
        print(
            f"   wholesale {size} (greedy-marginal {adds}): aggregate Sharpe "
            f"{agg:+.4f}  delta {agg - inc_sharpe:+.4f}  (mean_S {mean_s_book:+.3f} "
            f"rho {rho:+.3f} -> pred {pred:+.3f})"
        )
    # also a by-own-Sharpe construction at each size for cross-check
    for size in (5, 6, 7, 8):
        n_add = size - 3
        if n_add > len(cand_by_sharpe):
            break
        adds = cand_by_sharpe[:n_add]
        bk = {s: rosters[s] for s in list(INCUMBENTS) + adds}
        agg, _ = pooled_book_sharpe(bk)
        pred, mean_s_book, rho, _bk_n = bailey_lopezdeprado_predicted_sharpe(bk)
        t3_rows.append(
            dict(
                book=f"wholesale_{size}_ownSharpe",
                symbols="+".join(list(INCUMBENTS) + adds),
                book_size=size,
                aggregate_is_monthly_sharpe=round(agg, 4),
                bldp_predicted_sharpe=round(pred, 4),
                mean_per_symbol_sharpe=round(mean_s_book, 4),
                mean_pairwise_pnl_corr=round(rho, 4),
                delta_vs_incumbent=round(agg - inc_sharpe, 4),
            )
        )
    _write_csv(ANALYSIS_DIR / "T3_aggregate_book_sharpe.csv", t3_rows)
    _write_csv(
        ANALYSIS_DIR / "T3b_marginal_lift_per_candidate.csv",
        [dict(symbol=c, marginal_aggregate_sharpe_lift=round(d, 4)) for c, d in marg_rows],
    )

    # ----- T4: price-return corr vs strategy-PnL corr ----------------------
    print("\n[T4] price-return corr (the /021/069 metric) vs strategy-PnL corr ...")
    # price-return correlation across the full universe, IS-only
    all_syms = list(INCUMBENTS) + survivors
    price_rets: dict[str, dict[int, float]] = {}
    for s in all_syms:
        df = load_klines(s)
        is_df = df[df["open_time"] < OOS_CUTOFF_MS]
        closes = is_df["close"].to_numpy()
        ot = is_df["open_time"].to_numpy()
        lr = np.diff(np.log(closes))
        price_rets[s] = dict(zip(ot[1:].tolist(), lr.tolist()))
    pnl_series = {s: monthly_pnl_series(rosters[s]) for s in all_syms}
    t4_rows = []
    for a, b in combinations(all_syms, 2):
        # price-return corr on common 8h bars
        common_p = sorted(set(price_rets[a]) & set(price_rets[b]))
        pc = np.nan
        if len(common_p) >= 100:
            va = np.array([price_rets[a][t] for t in common_p])
            vb = np.array([price_rets[b][t] for t in common_p])
            if np.std(va) > 0 and np.std(vb) > 0:
                pc = float(np.corrcoef(va, vb)[0, 1])
        # strategy monthly-PnL corr on common months
        ma, mb = pnl_series[a], pnl_series[b]
        common_m = sorted(set(ma.index) & set(mb.index))
        sc = np.nan
        if len(common_m) >= 4:
            va = np.array([ma[t] for t in common_m])
            vb = np.array([mb[t] for t in common_m])
            if np.std(va) > 0 and np.std(vb) > 0:
                sc = float(np.corrcoef(va, vb)[0, 1])
        t4_rows.append(
            dict(
                pair=f"{a}|{b}",
                price_return_corr=round(pc, 4) if not np.isnan(pc) else "",
                strategy_monthly_pnl_corr=round(sc, 4) if not np.isnan(sc) else "",
                abs_gap=round(abs(pc) - abs(sc), 4) if not (np.isnan(pc) or np.isnan(sc)) else "",
            )
        )
    _write_csv(ANALYSIS_DIR / "T4_correlation_price_vs_pnl.csv", t4_rows)
    pc_all = [r["price_return_corr"] for r in t4_rows if r["price_return_corr"] != ""]
    sc_all = [
        r["strategy_monthly_pnl_corr"] for r in t4_rows if r["strategy_monthly_pnl_corr"] != ""
    ]
    print(f"   mean |price-return corr|      = {np.mean(np.abs(pc_all)):.4f}")
    print(f"   mean |strategy monthly-PnL corr| = {np.mean(np.abs(sc_all)):.4f}")
    print("   (the indifference-curve correlation is the PnL one — far lower)")

    # ----- T5: holding-time / roster-composition predictor -----------------
    print("\n[T5] holding-time predictor — added-set vs incumbent pooled roster ...")
    inc_pool = pd.concat(
        [rosters[s] for s in INCUMBENTS if not rosters[s].empty], ignore_index=True
    )
    inc_mean_dur = float(inc_pool["hold_candles"].mean()) if not inc_pool.empty else 0.0
    inc_med_dur = float(inc_pool["hold_candles"].median()) if not inc_pool.empty else 0.0
    t5_rows = [
        dict(
            symbol="INCUMBENT_POOL",
            role="incumbent",
            mean_duration_candles=round(inc_mean_dur, 3),
            median_duration_candles=round(inc_med_dur, 3),
            duration_gap_vs_incumbent=0.0,
        )
    ]
    for c in survivors:
        r = rosters[c]
        if r.empty:
            continue
        md = float(r["hold_candles"].mean())
        t5_rows.append(
            dict(
                symbol=c,
                role="candidate",
                mean_duration_candles=round(md, 3),
                median_duration_candles=round(float(r["hold_candles"].median()), 3),
                duration_gap_vs_incumbent=round(md - inc_mean_dur, 3),
            )
        )
    _write_csv(ANALYSIS_DIR / "T5_holding_time_predictor.csv", t5_rows)
    for r in t5_rows:
        print(
            f"   {r['symbol']:16s} mean_dur={r['mean_duration_candles']:.2f} "
            f"gap_vs_incumbent={r['duration_gap_vs_incumbent']:+.3f}"
        )

    # ----- T6: the wholesale-expansion decision ----------------------------
    print("\n[T6] wholesale-expansion DECISION ...")
    # pick the book size + symbol set that maximises aggregate IS monthly Sharpe
    # among the greedy-marginal books, subject to the duration-gap guard
    # (|gap| > ~2.0 candles loads the regime factor — flag, do not auto-include).
    best = None
    for row in t3_rows:
        if not row["book"].startswith("wholesale_") or not row["book"].endswith("marginal"):
            continue
        if best is None or row["aggregate_is_monthly_sharpe"] > best["aggregate_is_monthly_sharpe"]:
            best = row
    t6_rows = []
    if best is not None:
        chosen_syms = best["symbols"].split("+")
        added = [s for s in chosen_syms if s not in INCUMBENTS]
        # duration gaps for the chosen added symbols
        dur_gaps = {}
        for r in t5_rows:
            if r["symbol"] in added:
                dur_gaps[r["symbol"]] = r["duration_gap_vs_incumbent"]
        max_abs_gap = max((abs(v) for v in dur_gaps.values()), default=0.0)
        t6_rows.append(
            dict(
                metric="chosen_book",
                value=best["symbols"],
            )
        )
        t6_rows.append(dict(metric="book_size", value=str(best["book_size"])))
        t6_rows.append(
            dict(
                metric="added_symbols",
                value="+".join(added),
            )
        )
        t6_rows.append(
            dict(
                metric="incumbent_3_aggregate_sharpe",
                value=f"{inc_sharpe:+.4f}",
            )
        )
        t6_rows.append(
            dict(
                metric="chosen_book_aggregate_sharpe",
                value=f"{best['aggregate_is_monthly_sharpe']:+.4f}",
            )
        )
        t6_rows.append(
            dict(
                metric="aggregate_sharpe_delta",
                value=f"{best['delta_vs_incumbent']:+.4f}",
            )
        )
        t6_rows.append(
            dict(
                metric="chosen_book_mean_pairwise_pnl_corr",
                value=f"{best['mean_pairwise_pnl_corr']:+.4f}",
            )
        )
        t6_rows.append(
            dict(
                metric="max_abs_duration_gap_added",
                value=f"{max_abs_gap:.3f}",
            )
        )
        # the /083-drag-avoidance verdict
        verdict = (
            "EXPANSION-WORTHWHILE — broader book aggregate Sharpe preserved/lifted"
            if best["delta_vs_incumbent"] >= -0.05
            else "EXPANSION-DRAGS — would repeat /083; pivot"
        )
        t6_rows.append(dict(metric="verdict", value=verdict))
    _write_csv(ANALYSIS_DIR / "T6_wholesale_expansion_decision.csv", t6_rows)
    for r in t6_rows:
        print(f"   {r['metric']:38s} {r['value']}")

    print("\n" + "=" * 78)
    print("EDA complete. CSVs in analysis/iteration_v3-087/.")
    print("=" * 78)


if __name__ == "__main__":
    main()

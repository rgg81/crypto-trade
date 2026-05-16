"""iter-v3/083 EDA — UNIVERSE EXPANSION axis (cycle 3 EXPLORATION #2 of 10).

Direction 2 of `briefs-v3/cycle3_plan.md` — symbol-universe EXPANSION (grow the
denominator 3 -> N, N > 3). This is denominator expansion, the structural fix for
the /082 finding that v3's OOS Sharpe is ~104%-concentrated in BCH on a 3-symbol
universe. It is DISTINCT from the CLOSED swap-by-replacement family (/078).

WHY A NEW EDA (not /021's or /069's correlation screen). The two prior universe
EDAs failed at the SAME place:
  - /021 (HBAR+AVAX): composite score = 0.30*complementarity + 0.30*data_quality
    + 0.25*liquidity + 0.15*trade_rate. It ranked HBAR rank-1 by return-correlation
    diversity — and HBAR was the WORST IS contributor (-36.5% IS wpnl). NEGATIVE.
  - /069 (ADA): added a feature-space proximity term (T3) — still a DISTANCE metric.
    ADA went SUSPICIOUS-OOS-DOMINANT at /078.
Both screens measured PRICE diversity, not SIGNAL diversity. They never asked the
only question that matters: does a v3-style LightGBM model, trained with v3's own
14-feature stack and v3's own triple-barrier labels, produce a positive IS edge on
the candidate — AND does adding it lift the PORTFOLIO-AGGREGATE IS Sharpe under
BCH's ~96% IS dominance? The /078 lesson (memory `feedback_v3_per_symbol_lifts_oos_
breaks_is.md` / `feedback_v3_is_oos_regime_divergence.md`): a per-symbol Sharpe
screen does NOT transfer to portfolio-aggregate lift.

WHAT THIS EDA DOES (all IS-data-only — NO CHEATING):
  T1  Data-depth + liquidity + listing screen. Drops candidates with too little
      history for the 24-month training window + a meaningful IS evaluation span,
      and applies the crypto non-stationarity 60-day new-listing burn-in.
  T2  Genuine per-candidate IS-edge screen. For each surviving candidate, compute
      the v3 14-feature stack from raw OHLCV, label with the REAL v3 triple-barrier
      (label_trades, ATR(2.0, 1.0), 21-candle / 10080-min timeout), and run an
      IS-ONLY expanding walk-forward LightGBM (the same 24-month training window,
      monthly refit). A CONFIDENCE THRESHOLD gates trades — the model takes a
      trade only when max class proba clears CONF_THRESHOLD, the screen analogue
      of the v3 7-gate risk stack's selectivity. Report per-candidate IS monthly
      Sharpe, trade count, WR.
  T3  Portfolio-aggregate IS-Sharpe contribution under BCH dominance. v3 pools the
      per-symbol trade rosters into ONE book. T3 measures: incumbent 3-symbol IS
      monthly Sharpe (BCH+LDO+TRX) vs the 4-symbol IS monthly Sharpe with each
      candidate added. The candidate that LIFTS (or least-harms) the aggregate IS
      Sharpe AND dilutes BCH's trade-count share toward the <=30% gate is the pick.
  T4  Holding-time / roster-composition predictor (the /078 mandate). For the
      chosen candidate, report mean/median trade duration of its IS roster vs the
      incumbent pooled roster — the added-vs-incumbent mean-duration gap. A
      candidate whose roster is duration-loaded relative to the incumbents loads
      the v3 IS/OOS regime factor (memory `feedback_v3_is_oos_regime_divergence.md`).
  T5  Composite ranking + the count-expansion decision (HOW MANY to add, WHICH one).

  IMPORTANT — SCREEN SCOPE. This is a RELATIVE-RANKING screen, not a baseline
  reproduction. It runs every candidate AND the 3 incumbents through one
  identical un-tuned (fixed-LGBM-param) pipeline with NO Optuna and NO 7-gate
  risk stack. The ABSOLUTE Sharpe numbers therefore differ from the production
  v3 baseline (which is Optuna-tuned + risk-gated); only the CROSS-SYMBOL
  ranking and the SIGN/MAGNITUDE of the aggregate-IS-Sharpe DELTA are the
  load-bearing outputs. The incumbent pooled Sharpe computed here is the screen
  baseline the candidate deltas are measured against — internal consistency,
  not a /059 reproduction. BCH wpnl-share figures are unstable (the un-tuned
  pooled incumbent wpnl is near zero); the STABLE concentration proxy is BCH
  trade-count share (always-positive, large denominator) — T3/T5 use that.

Inputs (read-only):
  data/{SYMBOL}/8h.csv        — 8h klines (OHLCV)

Outputs (committed):
  analysis/iteration_v3-083/T1_data_liquidity_screen.csv
  analysis/iteration_v3-083/T2_per_candidate_is_edge.csv
  analysis/iteration_v3-083/T3_portfolio_aggregate_contribution.csv
  analysis/iteration_v3-083/T4_holding_time_predictor.csv
  analysis/iteration_v3-083/T5_composite_ranking.csv

Sacred constants (IMMUTABLE — no cheating):
  OOS_CUTOFF_DATE = 2025-03-24  — every row below uses ONLY data before this.
  training_months = 24          — the walk-forward training window.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
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
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v3-083"
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

# Candidate pool — deep-history (2020 listing => full 24-month training + a
# meaningful IS evaluation span before the 2025-03-24 cutoff), liquid large-cap
# Binance-futures altcoins NOT in V3_EXCLUDED_SYMBOLS (v1 BTC/ETH/LINK/LTC/DOT;
# v2 SOL/XRP/DOGE/NEAR; BNB; MKR). HBAR+AVAX are CLOSED at the catalog level
# (iter-v3/021 NEGATIVE — explicitly excluded here). ADA is CLOSED (iter-v3/078
# swap SUSPICIOUS — explicitly excluded here). The pool below is the
# "ATOM/FIL/ALGO deferred-to-LOW-priority" set from the /021 catalog plus other
# 2020-listed liquid alts that were never screened.
CANDIDATE_POOL = (
    "ATOMUSDT",
    "FILUSDT",
    "ALGOUSDT",
    "VETUSDT",
    "ETCUSDT",
    "XLMUSDT",
    "XTZUSDT",
    "AAVEUSDT",
)

# The v3 14-feature stack (V3_FEATURE_COLUMNS_TOP_N / BASELINE_V3.md).
# This EDA computes them from raw OHLCV so the screen is self-contained and
# faithful to what the v3 LightGBM model actually sees.
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
# class probability clears this. The screen analogue of v3's 7-gate risk stack:
# it turns the screen from a trade-every-candle classifier into a SELECTIVE one,
# so the IS-edge metric reflects high-conviction signal, not noise. The screen
# is a 3-class model {short, neutral, long}; 0.45 is a data-free a-priori choice
# (well above the 1/3 random-multiclass floor; not tuned on IS or OOS — no
# cheating). A candle is labeled NEUTRAL when the better directional barrier
# outcome is below NEUTRAL_EDGE_PCT — a no-clean-edge candle — so the model has
# a genuine third class to abstain into.
CONF_THRESHOLD = 0.45
NEUTRAL_EDGE_PCT = 0.5  # |best-direction net PnL| below this => neutral label

# LightGBM params for the IS-edge screen. Deliberately FIXED and conservative —
# this is a screen, not a tuned backtest. Optuna tuning happens in Phase 6. A
# fixed-param screen gives a clean relative ranking across candidates.
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
# ---------------------------------------------------------------------------


def compute_v3_features(df: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    """Compute the 14-feature v3 stack. df and btc are 8h-kline frames."""
    out = pd.DataFrame(index=df.index)
    close = df["close"]
    logret = np.log(close / close.shift(1))

    # --- price-action / drawdown / vol -------------------------------------
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

    # --- VWAP deviation -----------------------------------------------------
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap_num = (tp * df["volume"]).rolling(20, min_periods=20).sum()
    vwap_den = df["volume"].rolling(20, min_periods=20).sum()
    vwap20 = vwap_num / vwap_den.replace(0, np.nan)
    out["vwap_dev_20"] = ((close - vwap20) / vwap20).shift(1)

    # --- Hurst exponent (rolling, R/S style) --------------------------------
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

    # --- regime momentum (engineered — ret_5d * sign(hurst_100 - 0.5)) ------
    ret_5d = (close / close.shift(15) - 1.0)  # 15 8h-bars = 5 days
    out["regime_momentum_signed_5d"] = (
        ret_5d * np.sign(hurst_100 - 0.5)
    ).shift(1)

    # --- cross-asset (BTC) --------------------------------------------------
    btc_idx = btc.set_index("open_time")["close"]
    sym_close_by_t = df.set_index("open_time")["close"]
    btc_aligned = btc_idx.reindex(sym_close_by_t.index).ffill()
    btc_ret_14d = (btc_aligned / btc_aligned.shift(42) - 1.0)  # 42 8h-bars = 14 days
    sym_ret_7d = (sym_close_by_t / sym_close_by_t.shift(21) - 1.0)
    btc_ret_7d = (btc_aligned / btc_aligned.shift(21) - 1.0)
    out["btc_ret_14d"] = btc_ret_14d.shift(1).to_numpy()
    out["sym_vs_btc_ret_7d"] = (sym_ret_7d - btc_ret_7d).shift(1).to_numpy()

    return out


# ---------------------------------------------------------------------------
# T2 — per-candidate IS-edge walk-forward LightGBM screen
# ---------------------------------------------------------------------------


def _barrier_hit_candles(
    df: pd.DataFrame, atr: np.ndarray, side_for_idx: np.ndarray
) -> np.ndarray:
    """Label-implied holding time in candles per row, for the labeled side.

    Re-scans each candle forward to its first barrier hit (TP or SL) or the
    21-candle vertical timeout, using the SAME ATR(2.0, 1.0) barriers as
    label_trades. `side_for_idx` is +1 (long) / -1 (short) / 0 (no labeled
    side). This exposes the holding time that label_trades computes internally
    (long_step / short_step) but does not return. Screen-grade — memory /078
    documents it is biased LOW vs production Optuna-tuned barriers; flagged in
    the brief.
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
    """Triple-barrier labels for every candle. IS-only frame returned.

    Uses the REAL v3 labeling (label_trades, ATR multipliers, 21-candle timeout).
    """
    master = df.copy()
    master["symbol"] = symbol
    atr = wilder_atr(master, 14).to_numpy()
    n = len(master)
    cand = np.arange(n)
    labels, weights, long_pnl, short_pnl = label_trades(
        master=master,
        candidate_indices=cand,
        tp_pct=ATR_TP_MULT,  # ATR multiplier when atr_values is provided
        sl_pct=ATR_SL_MULT,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        atr_values=atr,
        label_mode="triple_barrier",
    )
    res = master[["open_time", "close_time"]].copy()
    res["label"] = labels  # 1 long, -1 short
    res["weight"] = weights
    res["long_pnl"] = long_pnl
    res["short_pnl"] = short_pnl
    res["atr"] = atr
    res["labeled_pnl"] = np.where(labels == 1, long_pnl, short_pnl)
    # 3-class training label: 2=long, 0=short, 1=neutral (no clean directional
    # edge — the better barrier outcome is below NEUTRAL_EDGE_PCT). best = the
    # larger of the two directional net-PnLs.
    best_dir_pnl = np.maximum(long_pnl, short_pnl)
    y3 = np.where(labels == 1, 2, 0)
    y3 = np.where(best_dir_pnl < NEUTRAL_EDGE_PCT, 1, y3)
    res["y3"] = y3
    # label-implied holding time for BOTH sides (real barrier scan) — the model
    # may pick either, so we precompute long-side and short-side durations.
    res["hold_long"] = _barrier_hit_candles(master, atr, np.ones(n, dtype=int))
    res["hold_short"] = _barrier_hit_candles(master, atr, -np.ones(n, dtype=int))
    return res


def walk_forward_edge(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    """IS-ONLY expanding walk-forward LightGBM. Returns the IS trade roster.

    Each calendar month m in the IS window:
      - train on the 24 months ending one embargo before m,
      - predict month m, take a trade ONLY where max class proba >= CONF_THRESHOLD
        and argmax(proba) != neutral (the screen analogue of v3's risk-gate
        selectivity),
      - realized PnL = the labeled best-direction PnL when the model's side
        matches the label, else the OTHER direction's PnL (a real loss/gain),
      - hold_candles = the label-implied barrier-hit duration for the side the
        MODEL picked.
    This is a relative-ranking proxy for the v3 per-symbol model's IS behaviour
    (un-tuned, un-risk-gated) — load-bearing output is the CROSS-SYMBOL ranking.
    """
    feat = features.copy()
    feat["open_time"] = labels["open_time"].to_numpy()
    feat["close_time"] = labels["close_time"].to_numpy()
    feat["y"] = labels["y3"].to_numpy()  # 0=short, 1=neutral, 2=long
    feat["long_pnl"] = labels["long_pnl"].to_numpy()
    feat["short_pnl"] = labels["short_pnl"].to_numpy()
    feat["weight"] = labels["weight"].to_numpy()
    feat["hold_long"] = labels["hold_long"].to_numpy()
    feat["hold_short"] = labels["hold_short"].to_numpy()

    # restrict to rows with a fully-formed feature vector AND a valid label,
    # and (sacred) ONLY the IS window — train AND predict are IS-only.
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
        if i < TRAINING_MONTHS:  # need 24 months of training history
            continue
        test = feat[feat["ym"] == m]
        if len(test) == 0:
            continue
        # train window: 24 months ending at month m, minus an embargo of
        # `embargo_candles` rows so labels do not leak across the boundary.
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
        classes = list(model.classes_)  # subset of {0, 1, 2}
        col_of = {c: k for k, c in enumerate(classes)}
        test_rows = test.reset_index(drop=True)
        for j in range(len(test_rows)):
            # take the more-probable DIRECTIONAL class (long vs short); gate on
            # its probability clearing CONF_THRESHOLD. A neutral-dominated row,
            # or a low-confidence directional row, is skipped — the screen's
            # selectivity mechanism (v3 7-gate-stack analogue).
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


def monthly_sharpe(trades: pd.DataFrame) -> float:
    """Monthly Sharpe of a trade roster (mean monthly PnL / std, annualized-free).

    v3 reports a 'monthly Sharpe' — the per-calendar-month PnL series Sharpe.
    """
    if trades.empty:
        return 0.0
    m = trades.groupby("ym")["pnl"].sum()
    if len(m) < 2 or m.std(ddof=1) == 0:
        return 0.0
    return float(m.mean() / m.std(ddof=1))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 78)
    print("iter-v3/083 EDA — universe EXPANSION IS-edge screen (IS-only, no cheating)")
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
            t1_rows.append(dict(symbol=sym, status="NO_DATA"))
            continue
        first_ms = int(df["open_time"].iloc[0])
        first_dt = datetime.fromtimestamp(first_ms / 1000, tz=UTC)
        # 60-day new-listing burn-in (crypto non-stationarity pitfall)
        burn_cut = first_ms + 60 * 24 * 3600 * 1000
        is_rows = df[(df["open_time"] >= burn_cut) & (df["open_time"] < OOS_CUTOFF_MS)]
        n_is = len(is_rows)
        # need 24 months training + >= 6 months IS evaluation => ~30 months of
        # post-burn-in IS data => ~30*~91 8h-bars. Floor: 2200 IS bars.
        depth_ok = n_is >= 2200 and first_ms < (
            OOS_CUTOFF_MS - 30 * 30 * 24 * 3600 * 1000
        )
        # liquidity — median IS daily quote volume
        if "quote_volume" in is_rows.columns and n_is > 0:
            daily_qv = is_rows["quote_volume"].rolling(3).sum().median()
        else:
            daily_qv = 0.0
        liq_ok = daily_qv >= 5e7  # >= $50M median daily quote volume
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
        print(f"   {r}")
    print(f"   T1 survivors: {survivors}")

    # ----- incumbent rosters (for T3 aggregate) ----------------------------
    print("\n[building incumbent IS rosters: BCH / LDO / TRX] ...")
    incumbent_rosters: dict[str, pd.DataFrame] = {}
    for sym in INCUMBENTS:
        df = load_klines(sym)
        feats = compute_v3_features(df, btc)
        labs = label_symbol_is(df, sym)
        roster = walk_forward_edge(feats, labs, sym)
        incumbent_rosters[sym] = roster
        print(
            f"   {sym}: IS trades={len(roster)} "
            f"monthly_Sharpe={monthly_sharpe(roster):+.4f}"
        )
    incumbent_pooled = pd.concat(
        [r for r in incumbent_rosters.values() if not r.empty], ignore_index=True
    )
    incumbent_sharpe = monthly_sharpe(incumbent_pooled)
    bch_wpnl = incumbent_rosters["BCHUSDT"]["pnl"].sum()
    inc_total_wpnl = incumbent_pooled["pnl"].sum()
    bch_share_3sym = 100.0 * bch_wpnl / inc_total_wpnl if inc_total_wpnl else float("nan")
    print(
        f"   INCUMBENT 3-sym pooled IS monthly Sharpe = {incumbent_sharpe:+.4f}; "
        f"BCH IS wpnl share = {bch_share_3sym:.1f}%"
    )

    # ----- T2: per-candidate IS-edge screen --------------------------------
    print("\n[T2] per-candidate IS-edge walk-forward LightGBM ...")
    t2_rows = []
    candidate_rosters: dict[str, pd.DataFrame] = {}
    for sym in survivors:
        df = load_klines(sym)
        feats = compute_v3_features(df, btc)
        labs = label_symbol_is(df, sym)
        roster = walk_forward_edge(feats, labs, sym)
        candidate_rosters[sym] = roster
        sh = monthly_sharpe(roster)
        wr = 100.0 * roster["win"].mean() if not roster.empty else 0.0
        n_months = roster["ym"].nunique() if not roster.empty else 0
        t2_rows.append(
            dict(
                symbol=sym,
                is_trades=len(roster),
                is_eval_months=n_months,
                is_trades_per_month=(
                    round(len(roster) / n_months, 2) if n_months else 0.0
                ),
                is_monthly_sharpe=round(sh, 4),
                is_win_rate=round(wr, 1),
                is_total_pnl=round(
                    roster["pnl"].sum() if not roster.empty else 0.0, 2
                ),
            )
        )
        print(f"   {t2_rows[-1]}")
    _write_csv(ANALYSIS_DIR / "T2_per_candidate_is_edge.csv", t2_rows)

    # ----- T3: portfolio-aggregate IS-Sharpe contribution ------------------
    print("\n[T3] portfolio-aggregate IS-Sharpe contribution under BCH dominance ...")
    t3_rows = []
    # BCH trade-count share — a STABLE concentration proxy. The wpnl-share
    # figures are unstable because the un-tuned screen's pooled incumbent wpnl
    # is near zero (BCH wpnl > total => share > 100%). Trade-count share has a
    # always-positive, large denominator => a robust dilution metric. v3's <=30%
    # gate is on OOS PnL share; trade-count share is the EDA-stage stable proxy.
    bch_n_trades = len(incumbent_rosters["BCHUSDT"])
    inc_n_trades = len(incumbent_pooled)
    bch_trade_share_3sym = 100.0 * bch_n_trades / inc_n_trades if inc_n_trades else float("nan")
    for sym in survivors:
        cand_roster = candidate_rosters[sym]
        if cand_roster.empty:
            continue
        pooled4 = pd.concat([incumbent_pooled, cand_roster], ignore_index=True)
        agg4_sharpe = monthly_sharpe(pooled4)
        total4 = pooled4["pnl"].sum()
        bch_wpnl_share4 = 100.0 * bch_wpnl / total4 if total4 else float("nan")
        n4 = len(pooled4)
        bch_trade_share4 = 100.0 * bch_n_trades / n4 if n4 else float("nan")
        cand_trade_share4 = 100.0 * len(cand_roster) / n4 if n4 else float("nan")
        t3_rows.append(
            dict(
                symbol=sym,
                incumbent_3sym_is_sharpe=round(incumbent_sharpe, 4),
                aggregate_4sym_is_sharpe=round(agg4_sharpe, 4),
                is_sharpe_delta=round(agg4_sharpe - incumbent_sharpe, 4),
                bch_wpnl_share_3sym_pct=round(bch_share_3sym, 1),
                bch_wpnl_share_4sym_pct=round(bch_wpnl_share4, 1),
                bch_trade_share_3sym_pct=round(bch_trade_share_3sym, 1),
                bch_trade_share_4sym_pct=round(bch_trade_share4, 1),
                bch_trade_share_dilution_pp=round(
                    bch_trade_share_3sym - bch_trade_share4, 1
                ),
                candidate_trade_share_pct=round(cand_trade_share4, 1),
            )
        )
        print(f"   {t3_rows[-1]}")
    _write_csv(ANALYSIS_DIR / "T3_portfolio_aggregate_contribution.csv", t3_rows)

    # ----- T4: holding-time / roster-composition predictor -----------------
    print("\n[T4] holding-time / roster-composition predictor (label-implied) ...")
    # The /078 mandate: a candidate whose roster is DURATION-LOADED relative to
    # the incumbents loads the v3 IS/OOS regime factor (IS penalizes longer-held
    # trades, OOS rewards them). hold_candles is the real label-implied barrier-
    # hit duration for the side the MODEL picked. Memory /078: a screen-grade
    # label-implied proxy is biased LOW vs the production Optuna-tuned barriers
    # (under-predicts the timeout-trade tail) — flagged here and in the brief.
    t4_rows = []
    inc_dur = incumbent_pooled["hold_candles"].to_numpy()
    inc_dur = inc_dur[~np.isnan(inc_dur)]
    for sym in survivors:
        cand_roster = candidate_rosters[sym]
        if cand_roster.empty:
            continue
        cand_dur = cand_roster["hold_candles"].to_numpy()
        cand_dur = cand_dur[~np.isnan(cand_dur)]
        t4_rows.append(
            dict(
                symbol=sym,
                incumbent_mean_duration_candles=round(float(np.mean(inc_dur)), 3),
                candidate_mean_duration_candles=round(float(np.mean(cand_dur)), 3),
                duration_gap_candles=round(
                    float(np.mean(cand_dur) - np.mean(inc_dur)), 3
                ),
                incumbent_median_duration=round(float(np.median(inc_dur)), 1),
                candidate_median_duration=round(float(np.median(cand_dur)), 1),
                candidate_timeout_trade_pct=round(
                    100.0 * float(np.mean(cand_dur >= 21)), 1
                ),
                incumbent_timeout_trade_pct=round(
                    100.0 * float(np.mean(inc_dur >= 21)), 1
                ),
                note="label-implied proxy; production Optuna-tuned barriers biased it LOW",
            )
        )
        print(f"   {t4_rows[-1]}")
    _write_csv(ANALYSIS_DIR / "T4_holding_time_predictor.csv", t4_rows)

    # ----- T5: composite ranking + count-expansion decision ----------------
    print("\n[T5] composite ranking ...")
    t3_by_sym = {r["symbol"]: r for r in t3_rows}
    t2_by_sym = {r["symbol"]: r for r in t2_rows}
    t4_by_sym = {r["symbol"]: r for r in t4_rows}
    t5_rows = []
    for sym in survivors:
        if sym not in t3_by_sym:
            continue
        t3 = t3_by_sym[sym]
        t2 = t2_by_sym[sym]
        t4 = t4_by_sym[sym]
        # Selection criterion (IS-data-only). The un-tuned screen produces
        # negative absolute Sharpe everywhere (it has no Optuna, no 7-gate risk
        # stack) — so the gates are RELATIVE, ranking candidates against one
        # another and against the incumbent, NOT against the production +1.09
        # baseline. A candidate is preferred when it:
        #   (a) ranks high on standalone IS edge (T2 monthly Sharpe — least-bad),
        #   (b) is the LEAST harmful to the portfolio-aggregate IS Sharpe (T3
        #       delta closest to 0 — the /078 lesson: aggregate, not per-symbol),
        #   (c) dilutes BCH's trade-count share (T3 stable dilution > 0),
        #   (d) meets the >=10 trades/month trade-rate floor in IS,
        #   (e) is NOT duration-loaded vs incumbents (T4 |gap| <= 1.0 candle —
        #       the /078 IS/OOS regime-factor guard).
        # Gate (a)/(b) absolute thresholds are deliberately RELATIVE: edge_rank
        # marks the top-2 by standalone Sharpe; agg_ok marks T3 delta in the
        # least-harmful half. The un-tuned screen cannot give an absolute
        # positive-edge gate honestly — flagged in the brief.
        rate_ok = t2["is_trades_per_month"] >= 10.0
        dur_ok = abs(t4["duration_gap_candles"]) <= 1.0
        dilution_ok = t3["bch_trade_share_dilution_pp"] > 0
        # composite score — aggregate IS-Sharpe delta is the dominant term
        # (the /021/069 lesson: signal contribution, not price diversity);
        # standalone edge is the secondary term; duration penalty if gap > 1.
        score = (
            2.0 * t3["is_sharpe_delta"]
            + 1.0 * t2["is_monthly_sharpe"]
            - 0.5 * max(abs(t4["duration_gap_candles"]) - 1.0, 0.0)
        )
        t5_rows.append(
            dict(
                symbol=sym,
                standalone_is_sharpe=t2["is_monthly_sharpe"],
                aggregate_is_sharpe_delta=t3["is_sharpe_delta"],
                bch_trade_share_dilution_pp=t3["bch_trade_share_dilution_pp"],
                is_trades_per_month=t2["is_trades_per_month"],
                duration_gap_candles=t4["duration_gap_candles"],
                gate_trade_rate=rate_ok,
                gate_duration_clean=dur_ok,
                gate_bch_diluted=dilution_ok,
                composite_score=round(score, 4),
            )
        )
    t5_rows.sort(key=lambda r: r["composite_score"], reverse=True)
    # mark the screen winner — highest composite among rows passing the two
    # hard gates (trade-rate + duration-clean).
    for rank, r in enumerate(t5_rows):
        r["hard_gates_pass"] = bool(r["gate_trade_rate"] and r["gate_duration_clean"])
        r["composite_rank"] = rank + 1
    _write_csv(ANALYSIS_DIR / "T5_composite_ranking.csv", t5_rows)
    print(f"\n   incumbent 3-sym IS monthly Sharpe (screen) = {incumbent_sharpe:+.4f}")
    print(f"   incumbent BCH IS trade-count share = {bch_trade_share_3sym:.1f}%")
    for r in t5_rows:
        print(f"   {r}")
    print("\n" + "=" * 78)
    eligible = [r for r in t5_rows if r["hard_gates_pass"]]
    if eligible:
        top = eligible[0]  # already sorted by composite descending
        print(
            f"SCREEN WINNER: {top['symbol']} — composite={top['composite_score']:+.4f}, "
            f"composite_rank #{top['composite_rank']}, "
            f"standalone_IS_Sharpe={top['standalone_is_sharpe']:+.4f}, "
            f"aggregate_IS_Sharpe_delta={top['aggregate_is_sharpe_delta']:+.4f}, "
            f"duration_gap={top['duration_gap_candles']:+.3f} candles. "
            f"Expansion: 3 -> 4 symbols (1-symbol-at-a-time per the /021 lesson)."
        )
        print(
            "NOTE: the un-tuned screen produces negative ABSOLUTE Sharpe (no "
            "Optuna, no 7-gate stack). The winner is the candidate that ranks "
            "best RELATIVE to peers AND least-harms the aggregate. The QR "
            "adjudicates the final pick in brief Section 2/3."
        )
    else:
        print("No candidate clears both hard gates (trade-rate + duration). "
              "QR adjudicates in brief Section 2/3.")
    print("=" * 78)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    main()

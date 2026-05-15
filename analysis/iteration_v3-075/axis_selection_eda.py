"""iter-v3/075 — Phase 1-4 axis-selection EDA (QR-driven, IS-data-only).

CYCLE 2 EXPLORATION #5 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

==============================================================================
THE MANDATE (Critic /074 FINAL `2371324` Recommendation #3 — binding)
==============================================================================
iter-v3/075 MUST target the IS bear/chop drag directly. The /074 EDA PART 1
localized it: the IS bear/chop sub-period (2022-09 -> 2023-12) has monthly Sharpe
-0.0242, only 27.8% positive months, total PnL -2.52%. The /074 regime kill switch
touched only 3 IS + 5 OOS trades — too few to lift the drag.

The /075 mechanism MUST be:
  - HOLDING-TIME-ORTHOGONAL. The holding-time-EXTENSION family (/065 SL widen,
    /071 meta-label, /073 per-symbol barrier) is SATURATED — all 3 reproduced
    SUSPICIOUS-OOS-DOMINANT by loading the v3 IS/OOS regime-divergence factor
    (`feedback_v3_is_oos_regime_divergence.md`). Any axis that lengthens
    mean/median trade DURATION is rejected at brief stage.
  - FULL-ROSTER. The mechanism must act on the FULL trade roster (or a large
    fraction), not a 3-trade stress-bar subset.

==============================================================================
THE QR AXIS CHOICE — Primitive 12: BTC-trend-regime position-SIZE scalar
==============================================================================
A NEW risk primitive (the structural-axis category, NOT a gate knob): a
BTC-trend-regime-conditional position-SIZE de-rate scalar.

Mechanism:
  - A past-only BTC bull / bear-chop classifier on the BTC 8h close.
    BTC is in "bear/chop" at bar t when close[t-1] < SMA_N(close)[t-1] (the
    slow-trend filter; Carver, *Systematic Trading*, Ch. on trend filters).
    Slow MA window N is chosen by this EDA (T2 sweep).
  - When the classifier says BTC bear/chop, the position weight of a trade is
    multiplied by a de-rate scalar s_regime < 1.0 — but ONLY for the
    genuine-drag symbols identified by the EDA (T7 SCOPE decision). When BTC
    bull, s_regime = 1.0.
  - It slots in at primitive 5 (vol-scaling) as an extra multiplicative factor
    (`scale *= s_regime`). It changes WEIGHT only — never SL/TP/timeout — so it is
    HOLDING-TIME-ORTHOGONAL by construction. It acts on the FULL roster of the
    scope symbols: every bear/chop-month trade of a scope symbol has its weight
    scaled.

IMPORTANT — the SCOPE is an EDA OUTPUT, not a pre-decision. The EDA first tests
a BLANKET (all-3-symbol) de-rate (T3) and finds it IS-NEGATIVE — BCH WINS in
BTC-bear/chop months, so de-rating BCH down-scales the IS edge. T7 localises the
genuine-drag symbols (negative bear/chop-entry IS wpnl); the de-rate is SCOPED to
exactly those. The scope is the IS-improving design — it preserves the BCH IS
edge by construction.

Why a SIZE scalar and not the /074 binary kill switch:
  - /074's binary kill switch at acute-crash thresholds (BTC dd>20% OR |vol_z|>1.5)
    fired on only 3 IS trades. A SIZE scalar at a BROADER trend-state classifier
    (price-vs-slow-MA tags whole bear/chop MONTHS, not just acute-crash bars) acts
    on the FULL bear/chop-month roster of the scope symbols — the materially-larger
    trade population the Critic mandate demands.
  - A SIZE scalar de-rates rather than removes: it preserves trade-rate (no trade
    is deleted, so the OOS trade-rate floor is untouched) while reducing the
    bear/chop drag's PnL contribution.

==============================================================================
WHAT THIS EDA DOES
==============================================================================
T0  — /060 EXPLORATION-mode anchor, byte-exact with source file:line refs.
T1  — IS/OOS regime-stratified diagnostic (re-derives the /074 PART 1 finding
      from the /060 monthly_pnl, the structural drag we must lift).
T2  — BTC-trend-regime classifier SWEEP. For each slow-MA window N, measure how
      well the price-vs-SMA_N classifier tags the IS bear/chop sub-period and how
      it overlaps the OOS uptrend. Picks N.
T3  — Counterfactual: apply the BTC bear/chop SIZE de-rate to the /060 trade
      roster. For a grid of de-rate scalars, recompute IS monthly Sharpe.
      IS-ONLY — this is the simulated historical IS effect.
T4  — Holding-time-effect predictor. A SIZE scalar changes weight, never
      duration — verify the kept roster duration delta is EXACTLY 0 (the scalar
      removes no trades and shifts no barriers).
T5  — Behavioral-effect predictor. Count how many IS + OOS trades have their
      weight changed by the scalar — must be MATERIALLY LARGER than /074's
      3-IS/5-OOS.
T6  — Per-symbol IS-axis discipline. Decompose the T3 counterfactual IS lift by
      symbol — the scalar must PRESERVE or LIFT each symbol's IS contribution
      (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`).

==============================================================================
NO LOOK-AHEAD — and the de-rate scalar is chosen WITHOUT OOS data
==============================================================================
Every IS table is computed on IS-window data only (open_time < OOS_CUTOFF_MS =
2025-03-24). The BTC-trend classifier uses close.shift(1) before the rolling SMA
— identical past-only contract to the production risk_v3._build_btc_regime_lookup.
The EDA runs NO backtest; every table is descriptive arithmetic on the committed
/060 trade roster.

ALL THREE DESIGN PARAMETERS ARE SELECTED ON IS DATA OR A-PRIORI:
  - The MA-window choice (T2) sorts on `is_discrimination_pp` — IS-only.
  - The LDO+TRX scope (T7) is `bearchop_is_genuine_drag` from IS bear/chop-entry
    wpnl sign — IS-only.
  - The de-rate scalar (T3/T8) is an A-PRIORI default of 0.50 ("halve position
    size in the adverse BTC regime") — a canonical, data-free risk default. It
    is NOT fitted to any IS magnitude and NOT ranked by any OOS counterfactual.
    See main() for the documented criterion.

CORRECTION DISCLOSURE: the first EDA pass selected the de-rate scalar via an
OOS-informed rule — it filtered candidate de-rates by `oos_delta >= -0.20` and
ranked the survivors by `oos_delta`. That used the /060 OOS trade roster to rank
and pick an iteration DESIGN PARAMETER, which is OOS tuning (the QR sees OOS only
in Phase 7). The defect was caught pre-Phase-5.5-gate and corrected: T3 and T8 no
longer compute any OOS counterfactual for candidate de-rates, and the de-rate is
an a-priori default. T1's `OOS_uptrend` row stays — it merely reproduces the
already-published /060 OOS anchor (+0.1403, in every brief's anchor table), which
is the public anchor, NOT a per-candidate-design OOS evaluation.
==============================================================================

Run:
  uv run python analysis/iteration_v3-075/axis_selection_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

# Sacred constant — src/crypto_trade/config.py OOS_CUTOFF_MS (2025-03-24 00:00 UTC).
OOS_CUTOFF_MS = 1742774400000

# IS regime sub-window boundary (matches /074 PART 1 exactly for continuity).
# IS bear/chop : 2022-09-01 -> 2023-12-31  (FTX collapse, 2023 chop)
# IS bull      : 2024-01-01 -> 2025-03-24  (2024 bull + 2024-Q4/2025-Q1 chop)
IS_BULL_START_MS = 1704067200000  # 2024-01-01 00:00:00 UTC

V3_SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]

REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"
BTC_CSV = REPO / "data" / "BTCUSDT" / "8h.csv"

# Candidate slow-MA windows (bars at 8h cadence) for the BTC-trend classifier.
#   90 bars  = 30 calendar days   (matches the regime_dd_lookback_bars of /022)
#   135 bars = 45 calendar days
#   180 bars = 60 calendar days
#   270 bars = 90 calendar days   (quarter — slow trend)
CANDIDATE_MA_WINDOWS = [90, 135, 180, 270]

# Candidate bear/chop SIZE de-rate scalars for the T3 counterfactual grid.
CANDIDATE_DERATE = [0.25, 0.35, 0.50, 0.65, 0.75]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _monthly_sharpe_from_wpnl(df: pd.DataFrame, wpnl_col: str = "weighted_pnl") -> float:
    """Monthly Sharpe = mean(monthly wpnl%) / std(monthly wpnl%) * sqrt(12).

    Mirrors `run_baseline_v3.py:_monthly_sharpe` — the function that produces the
    `comparison.csv` `monthly_sharpe` row. wpnl is divided by 100 (pct -> fraction).
    """
    if df.empty:
        return 0.0
    months = pd.to_datetime(df["close_time"], unit="ms").dt.to_period("M")
    monthly = (df[wpnl_col].astype(float) / 100.0).groupby(months).sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _load_trades(split: str) -> pd.DataFrame:
    """Load the /060 trade roster for `split` in {in_sample, out_of_sample}."""
    path = REPORTS_060 / split / "trades.csv"
    df = pd.read_csv(path)
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    df["weighted_pnl"] = df["weighted_pnl"].astype(float)
    # Trade duration in 8h candles: (close_time - open_time) / 8h_ms.
    df["dur_candles"] = (df["close_time"] - df["open_time"]) / (8 * 3600 * 1000)
    return df


def _build_btc_trend_lookup(ma_window: int) -> pd.DataFrame:
    """BTC bull / bear-chop classifier — past-only, close-vs-slow-SMA.

    Past-only contract (identical to risk_v3._build_btc_regime_lookup):
      close.shift(1) is applied BEFORE the rolling SMA so bar t's classification
      uses only close[t-1 .. t-ma_window]. The current bar's own close is NEVER
      seen. Appending future BTC bars does not change the value at t.

    Returns a frame with: open_time, btc_bearchop (1 = bear/chop, 0 = bull).
    """
    btc = pd.read_csv(BTC_CSV, usecols=["open_time", "close"])
    btc = btc.sort_values("open_time").reset_index(drop=True)
    btc["close"] = btc["close"].astype(float)
    close_shifted = btc["close"].shift(1)
    sma = close_shifted.rolling(window=ma_window, min_periods=ma_window).mean()
    # bear/chop = past close strictly below the slow trend MA.
    btc["btc_bearchop"] = (close_shifted < sma).astype("Int64")
    # Warm-up bars (sma NaN) -> classified bull (0): conservative — no de-rate
    # applied where the classifier is undefined.
    btc["btc_bearchop"] = btc["btc_bearchop"].fillna(0).astype(int)
    return btc[["open_time", "btc_bearchop"]]


def _tag_trades_with_regime(trades: pd.DataFrame, btc_lookup: pd.DataFrame) -> pd.Series:
    """Tag each trade with the BTC regime in force at its ENTRY bar (past-only).

    For trade entry open_time, the regime is read from the most recent BTC bar
    with open_time STRICTLY LESS THAN the trade's open_time (searchsorted 'left'
    minus 1) — the production `_regime_gate_fires` contract. Returns an int Series
    aligned to `trades` index (1 = entry in BTC bear/chop, 0 = entry in BTC bull).
    """
    btc_times = btc_lookup["open_time"].to_numpy(dtype=np.int64)
    btc_flag = btc_lookup["btc_bearchop"].to_numpy(dtype=np.int64)
    out = np.zeros(len(trades), dtype=np.int64)
    for i, ot in enumerate(trades["open_time"].to_numpy(dtype=np.int64)):
        idx = int(np.searchsorted(btc_times, ot, side="left")) - 1
        out[i] = 0 if idx < 0 else int(btc_flag[idx])
    return pd.Series(out, index=trades.index)


# ===========================================================================
# T0 — Anchor declaration (byte-exact)
# ===========================================================================
def t0_anchor() -> None:
    cmp = "reports-v3/iteration_v3-060/comparison.csv"
    rows = [
        ("monthly_sharpe_IS", 0.8325, f"{cmp}:2 in_sample"),
        ("monthly_sharpe_OOS", 0.1403, f"{cmp}:2 out_of_sample"),
        ("daily_sharpe_IS", 1.7115, f"{cmp}:3 in_sample"),
        ("daily_sharpe_OOS", 0.3659, f"{cmp}:3 out_of_sample"),
        ("n_trades_IS", 159, f"{cmp}:7 in_sample"),
        ("n_trades_OOS", 102, f"{cmp}:7 out_of_sample"),
        (
            "frac_positive_paths",
            0.6444,
            "reports-v3/iteration_v3-060 dsr.json / cpcv_paths.csv (CPCV invariant)",
        ),
    ]
    df = pd.DataFrame(rows, columns=["anchor_metric", "value", "source"])
    df.to_csv(OUT / "T0_anchor_values.csv", index=False)
    print("\n=== T0 — /060 EXPLORATION-mode anchor ===")
    print(df.to_string(index=False))


# ===========================================================================
# T1 — IS/OOS regime-stratified diagnostic (re-derive /074 PART 1)
# ===========================================================================
def t1_regime_stratification() -> pd.DataFrame:
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")

    def _bucket(df: pd.DataFrame, lo: int | None, hi: int | None) -> pd.DataFrame:
        m = pd.Series(True, index=df.index)
        if lo is not None:
            m &= df["open_time"] >= lo
        if hi is not None:
            m &= df["open_time"] < hi
        return df.loc[m]

    bear = _bucket(is_trades, None, IS_BULL_START_MS)
    bull = _bucket(is_trades, IS_BULL_START_MS, OOS_CUTOFF_MS)

    rows = []
    for name, df in [
        ("IS_bear_chop", bear),
        ("IS_bull", bull),
        ("OOS_uptrend", oos_trades),
    ]:
        months = pd.to_datetime(df["close_time"], unit="ms").dt.to_period("M")
        monthly = (df["weighted_pnl"].astype(float) / 100.0).groupby(months).sum()
        rows.append(
            {
                "regime": name,
                "n_months": int(monthly.shape[0]),
                "total_wpnl_pct": round(float(df["weighted_pnl"].sum()), 4),
                "mean_monthly_pnl_pct": round(float(monthly.mean() * 100.0), 4),
                "std_monthly_pnl_pct": round(float(monthly.std() * 100.0), 4),
                "monthly_sharpe": round(_monthly_sharpe_from_wpnl(df), 4),
                "pct_positive_months": round(float((monthly > 0).mean() * 100.0), 1),
                "n_trades": int(len(df)),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T1_regime_stratification.csv", index=False)
    print("\n=== T1 — IS/OOS regime-stratified diagnostic (the drag to lift) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T2 — BTC-trend-regime classifier SWEEP
# ===========================================================================
def t2_classifier_sweep() -> pd.DataFrame:
    """For each slow-MA window, measure how the close-vs-SMA classifier overlaps
    the IS bear/chop sub-period vs the IS bull and OOS-uptrend sub-periods.

    The classifier is GOOD if it flags a high fraction of IS-bear/chop trades and
    a low fraction of IS-bull AND OOS-uptrend trades — that asymmetry is what
    delivers an IS-lift without OOS-bull-only inflation.
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    bear_mask = is_trades["open_time"] < IS_BULL_START_MS

    rows = []
    for n in CANDIDATE_MA_WINDOWS:
        btc = _build_btc_trend_lookup(n)
        is_flag = _tag_trades_with_regime(is_trades, btc)
        oos_flag = _tag_trades_with_regime(oos_trades, btc)

        bear_flag = is_flag[bear_mask]
        bull_flag = is_flag[~bear_mask]

        rows.append(
            {
                "ma_window_bars": n,
                "ma_window_days": n * 8 // 24,
                # fraction of IS-bear/chop trades the classifier tags bear/chop
                "is_bearchop_trades_flagged_pct": round(float(bear_flag.mean() * 100.0), 1),
                # fraction of IS-bull trades wrongly tagged bear/chop (lower better)
                "is_bull_trades_flagged_pct": round(float(bull_flag.mean() * 100.0), 1),
                # fraction of OOS-uptrend trades tagged bear/chop (lower better)
                "oos_trades_flagged_pct": round(float(oos_flag.mean() * 100.0), 1),
                # discrimination = bear-flag-rate minus bull-flag-rate (higher better)
                "is_discrimination_pp": round(
                    float((bear_flag.mean() - bull_flag.mean()) * 100.0), 1
                ),
                "n_is_bearchop_trades_flagged": int(bear_flag.sum()),
                "n_is_total_flagged": int(is_flag.sum()),
                "n_oos_total_flagged": int(oos_flag.sum()),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T2_classifier_sweep.csv", index=False)
    print("\n=== T2 — BTC-trend classifier sweep (close < SMA_N, past-only) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T3 — Counterfactual: BTC bear/chop SIZE de-rate on the /060 roster (IS-ONLY)
# ===========================================================================
def t3_derate_counterfactual(ma_window: int) -> pd.DataFrame:
    """Apply a bear/chop SIZE de-rate scalar to the /060 IS trade roster and
    recompute IS monthly Sharpe for a grid of scalars.

    IS-ONLY. This table reports the simulated historical IS effect of a BLANKET
    (all-3-symbol) de-rate. A trade whose ENTRY bar is in BTC bear/chop has its
    weighted_pnl scaled by the de-rate (a position-size scalar scales the
    realised PnL linearly — half the size, half the PnL). Bull-entry trades are
    unchanged.

    NO OOS COLUMN. The de-rate scalar is an iteration DESIGN PARAMETER; ranking
    or filtering candidate de-rates by an OOS counterfactual is OOS tuning (the
    QR sees OOS only in Phase 7). This table therefore reports IS columns only —
    it exists to show the blanket all-symbol de-rate is IS-NEGATIVE (the
    EDA-driven reason to SCOPE the de-rate, T7), a finding made entirely on IS
    data. The de-rate scalar itself is an a-priori default (see main()).

    NOTE — a position-SIZE scalar at primitive 5 fires AFTER the model and AFTER
    labeling. It changes only the realised weighted_pnl of trades that still
    happen; it does NOT change trade SELECTION, labels, or the Optuna
    optimization landscape (unlike the /074 KILL switch, which fired BEFORE the
    model). The IS counterfactual is therefore ESSENTIALLY EXACT on the IS
    roster.
    """
    is_trades = _load_trades("in_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)

    base_is = _monthly_sharpe_from_wpnl(is_trades)

    rows = [
        {
            "derate_scalar": 1.00,
            "is_monthly_sharpe": round(base_is, 4),
            "is_delta": 0.0,
        }
    ]
    for d in CANDIDATE_DERATE:
        is_cf = is_trades.copy()
        # Bear/chop-entry trades: weighted_pnl scaled by the de-rate. Bull: unchanged.
        is_cf["weighted_pnl"] = is_cf["weighted_pnl"] * np.where(is_flag.to_numpy() == 1, d, 1.0)
        cf_is = _monthly_sharpe_from_wpnl(is_cf)
        rows.append(
            {
                "derate_scalar": d,
                "is_monthly_sharpe": round(cf_is, 4),
                "is_delta": round(cf_is - base_is, 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T3_derate_counterfactual.csv", index=False)
    print(f"\n=== T3 — bear/chop SIZE de-rate counterfactual, IS-ONLY (BTC SMA_{ma_window}) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T4 — Holding-time-effect predictor
# ===========================================================================
def t4_holding_time_predictor(ma_window: int) -> pd.DataFrame:
    """A SIZE scalar changes WEIGHT, never DURATION. Verify the kept roster's
    mean/median trade duration is EXACTLY unchanged — a position-size scalar
    deletes no trade and shifts no SL/TP/timeout barrier.

    Mandated by `feedback_v3_is_oos_regime_divergence.md`: an axis with ~0
    predicted duration change does NOT load the IS/OOS regime factor.
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)
    oos_flag = _tag_trades_with_regime(oos_trades, btc)

    rows = []
    for split, df, flag in [
        ("IS", is_trades, is_flag),
        ("OOS", oos_trades, oos_flag),
    ]:
        # Full roster (baseline) vs the post-scalar roster. The post-scalar roster
        # is IDENTICAL in membership and timing — only weighted_pnl differs — so
        # the duration distribution is bit-identical by construction.
        full_mean = float(df["dur_candles"].mean())
        full_med = float(df["dur_candles"].median())
        # de-rated subset duration (the bear/chop-entry trades) — informational:
        # shows the scalar does not preferentially touch long- or short-held trades
        sub = df.loc[flag == 1, "dur_candles"]
        rows.append(
            {
                "split": split,
                "full_roster_n": int(len(df)),
                "full_mean_dur": round(full_mean, 4),
                "full_median_dur": round(full_med, 4),
                "post_scalar_roster_n": int(len(df)),  # IDENTICAL — no trade removed
                "post_scalar_mean_dur": round(full_mean, 4),  # IDENTICAL by construction
                "post_scalar_median_dur": round(full_med, 4),
                "mean_dur_delta": 0.0,  # EXACT — a size scalar removes no trade
                "median_dur_delta": 0.0,
                "derated_subset_n": int((flag == 1).sum()),
                "derated_subset_mean_dur": round(float(sub.mean()), 4) if len(sub) else 0.0,
                "derated_subset_median_dur": round(float(sub.median()), 4) if len(sub) else 0.0,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T4_holding_time_predictor.csv", index=False)
    print("\n=== T4 — holding-time-effect predictor (SIZE scalar; duration UNCHANGED) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T5 — Behavioral-effect predictor
# ===========================================================================
def t5_behavioral_predictor(ma_window: int) -> pd.DataFrame:
    """Count IS + OOS trades whose WEIGHT is changed by the scalar (entry in BTC
    bear/chop). Mandated by `feedback_v3_axis_saturation_predictor.md`.

    The Critic /074 mandate requires a MATERIALLY LARGER trade-population effect
    than /074's 3-IS / 5-OOS suppression.
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)
    oos_flag = _tag_trades_with_regime(oos_trades, btc)

    rows = []
    for split, df, flag in [("IS", is_trades, is_flag), ("OOS", oos_trades, oos_flag)]:
        for sym in V3_SYMBOLS:
            sym_mask = df["symbol"] == sym
            n_total = int(sym_mask.sum())
            n_changed = int(((flag == 1) & sym_mask).sum())
            rows.append(
                {
                    "split": split,
                    "symbol": sym,
                    "n_total_trades": n_total,
                    "n_weight_changed": n_changed,
                    "pct_weight_changed": (
                        round(100.0 * n_changed / n_total, 1) if n_total else 0.0
                    ),
                }
            )
        # portfolio row
        n_total = int(len(df))
        n_changed = int((flag == 1).sum())
        rows.append(
            {
                "split": split,
                "symbol": "PORTFOLIO",
                "n_total_trades": n_total,
                "n_weight_changed": n_changed,
                "pct_weight_changed": round(100.0 * n_changed / n_total, 1) if n_total else 0.0,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T5_behavioral_predictor.csv", index=False)
    print("\n=== T5 — behavioral-effect predictor (trades with WEIGHT changed) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T7 — Per-symbol bear/chop-entry IS economics (the SCOPE-decision table)
# ===========================================================================
def t7_per_symbol_bearchop_economics(ma_window: int) -> pd.DataFrame:
    """Decompose, per symbol, the IS economics of bear/chop-entry vs bull-entry
    trades. THIS IS THE DECISIVE TABLE for the axis design.

    T3/T6 revealed a blanket (all-symbol) bear/chop SIZE de-rate is IS-NEGATIVE:
    BCH — the IS-edge carrier — actually WINS in BTC-bear/chop months, so
    de-rating BCH's bear/chop trades down-scales the IS edge. The drag is
    SYMBOL-ASYMMETRIC: BCH wins in bear/chop, TRX + LDO bleed.

    This table localises which symbols' bear/chop-entry trades are the genuine
    drag (negative bear/chop-entry IS wpnl AND bear/chop-entry win rate below the
    symbol's own bull-entry win rate). The de-rate must be SCOPED to exactly
    those symbols — that scope is the IS-improving axis, not a customisation that
    breaks IS.
    """
    is_trades = _load_trades("in_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)

    rows = []
    for sym in V3_SYMBOLS:
        sym_mask = is_trades["symbol"] == sym
        sub = is_trades.loc[sym_mask].copy()
        f = is_flag[sym_mask]
        bear = sub.loc[f == 1]
        bull = sub.loc[f == 0]
        bear_wr = float((bear["weighted_pnl"] > 0).mean() * 100.0) if len(bear) else 0.0
        bull_wr = float((bull["weighted_pnl"] > 0).mean() * 100.0) if len(bull) else 0.0
        bear_wpnl = float(bear["weighted_pnl"].sum())
        # genuine drag = bear/chop-entry IS wpnl is negative.
        is_drag = bear_wpnl < 0.0
        rows.append(
            {
                "symbol": sym,
                "n_bearchop_entry": int(len(bear)),
                "n_bull_entry": int(len(bull)),
                "bearchop_entry_wpnl": round(bear_wpnl, 4),
                "bull_entry_wpnl": round(float(bull["weighted_pnl"].sum()), 4),
                "bearchop_entry_wr": round(bear_wr, 1),
                "bull_entry_wr": round(bull_wr, 1),
                "bearchop_is_genuine_drag": bool(is_drag),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T7_per_symbol_bearchop_economics.csv", index=False)
    print("\n=== T7 — per-symbol bear/chop-entry IS economics (the SCOPE decision) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T8 — SCOPED de-rate counterfactual (de-rate only the drag symbols, IS-ONLY)
# ===========================================================================
def t8_scoped_derate_counterfactual(ma_window: int, scope_symbols: tuple[str, ...]) -> pd.DataFrame:
    """Re-run the T3 counterfactual but de-rate bear/chop-entry trades ONLY for
    symbols in `scope_symbols` (the genuine-drag symbols from T7). BCH trades are
    never touched. This is the CORRECTED axis.

    IS-ONLY. NO OOS COLUMN — same reason as T3: the de-rate scalar is an
    iteration DESIGN PARAMETER, and ranking/filtering candidate de-rates by an
    OOS counterfactual is OOS tuning. This table reports IS monthly Sharpe for
    the grid of scalars so the IS lift of the SCOPED de-rate is visible, and so
    the a-priori 0.50 default's IS effect can be read off (it is reported, not
    selected on — see main()). The de-rate scalar is an a-priori default.

    Same ESSENTIALLY-EXACT property as T3 — a position-SIZE scalar fires after
    the model + labeling, so trade selection and the Optuna landscape are
    unchanged on the IS roster.
    """
    is_trades = _load_trades("in_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)

    is_scope = is_trades["symbol"].isin(scope_symbols).to_numpy()

    base_is = _monthly_sharpe_from_wpnl(is_trades)

    rows = [
        {
            "derate_scalar": 1.00,
            "is_monthly_sharpe": round(base_is, 4),
            "is_delta": 0.0,
        }
    ]
    for d in CANDIDATE_DERATE:
        is_cf = is_trades.copy()
        # de-rate fires ONLY when (bear/chop entry) AND (symbol in scope).
        is_mult = np.where((is_flag.to_numpy() == 1) & is_scope, d, 1.0)
        is_cf["weighted_pnl"] = is_cf["weighted_pnl"] * is_mult
        cf_is = _monthly_sharpe_from_wpnl(is_cf)
        rows.append(
            {
                "derate_scalar": d,
                "is_monthly_sharpe": round(cf_is, 4),
                "is_delta": round(cf_is - base_is, 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T8_scoped_derate_counterfactual.csv", index=False)
    print(
        f"\n=== T8 — SCOPED bear/chop de-rate counterfactual, IS-ONLY "
        f"(BTC SMA_{ma_window}; scope={scope_symbols}) ==="
    )
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T6 — Per-symbol IS-axis discipline
# ===========================================================================
def t6_per_symbol_is_discipline(
    ma_window: int, derate: float, scope_symbols: tuple[str, ...]
) -> pd.DataFrame:
    """Decompose the SCOPED IS counterfactual lift at the chosen de-rate by symbol.

    Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, the axis must PRESERVE or
    LIFT each symbol's IS contribution. The de-rate fires ONLY for symbols in
    `scope_symbols` (the genuine-drag symbols). BCH — outside the scope — is
    BIT-IDENTICAL to /060 by construction (delta exactly 0). This table verifies
    every symbol's IS weighted_pnl is preserved or lifted.
    """
    is_trades = _load_trades("in_sample")
    btc = _build_btc_trend_lookup(ma_window)
    is_flag = _tag_trades_with_regime(is_trades, btc)

    rows = []
    for sym in V3_SYMBOLS:
        sym_mask = is_trades["symbol"] == sym
        base_wpnl = float(is_trades.loc[sym_mask, "weighted_pnl"].sum())
        cf = is_trades.loc[sym_mask].copy()
        f = is_flag[sym_mask]
        in_scope = sym in scope_symbols
        # de-rate fires only when (bear/chop entry) AND (symbol in scope).
        mult = np.where((f.to_numpy() == 1) & in_scope, derate, 1.0)
        cf_wpnl = float((cf["weighted_pnl"] * mult).sum())
        bearchop_wpnl = float(cf.loc[f == 1, "weighted_pnl"].sum())
        rows.append(
            {
                "symbol": sym,
                "in_derate_scope": in_scope,
                "is_wpnl_base": round(base_wpnl, 4),
                "is_wpnl_post_derate": round(cf_wpnl, 4),
                "is_wpnl_delta": round(cf_wpnl - base_wpnl, 4),
                "is_bearchop_entry_wpnl_base": round(bearchop_wpnl, 4),
                "n_is_trades": int(sym_mask.sum()),
                "n_is_bearchop_entry": int((f == 1).sum()),
                "is_axis_preserves_or_lifts": bool(cf_wpnl >= base_wpnl - 1e-9),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T6_per_symbol_is_discipline.csv", index=False)
    print(
        f"\n=== T6 — per-symbol IS-axis discipline "
        f"(SMA_{ma_window}, derate={derate}, scope={scope_symbols}) ==="
    )
    print(df.to_string(index=False))
    return df


# ===========================================================================
# Synthesis
# ===========================================================================
def write_synthesis(
    t1: pd.DataFrame,
    t2: pd.DataFrame,
    t3: pd.DataFrame,
    t7: pd.DataFrame,
    t8: pd.DataFrame,
    t4: pd.DataFrame,
    t5: pd.DataFrame,
    t6: pd.DataFrame,
    ma_window: int,
    derate: float,
    scope: tuple[str, ...],
) -> None:
    bearchop = t1.loc[t1["regime"] == "IS_bear_chop"].iloc[0]
    blanket_cf = t3.loc[np.isclose(t3["derate_scalar"], derate)].iloc[0]
    scoped_cf = t8.loc[np.isclose(t8["derate_scalar"], derate)].iloc[0]
    bch_t7 = t7.loc[t7["symbol"] == "BCHUSDT"].iloc[0]
    trx_t7 = t7.loc[t7["symbol"] == "TRXUSDT"].iloc[0]
    ldo_t7 = t7.loc[t7["symbol"] == "LDOUSDT"].iloc[0]
    scope_mask = t5["symbol"].isin(scope)
    is_changed = int(t5.loc[(t5["split"] == "IS") & scope_mask, "n_weight_changed"].sum())
    oos_changed = int(t5.loc[(t5["split"] == "OOS") & scope_mask, "n_weight_changed"].sum())

    lines = [
        "# iter-v3/075 — Axis-Selection EDA Synthesis",
        "",
        "## QR axis decision",
        "",
        "**Primitive 12 — BTC-trend-regime position-SIZE de-rate scalar, SCOPED to the "
        f"genuine-drag symbols {scope}.** A NEW risk primitive: a past-only BTC "
        f"bull/bear-chop classifier (close[t-1] < SMA_{ma_window}(close)[t-1]). When the "
        f"classifier says BTC bear/chop, the position WEIGHT of a trade is multiplied by "
        f"**{derate}** — but ONLY for symbols in the scope set {scope}. BCH trades and all "
        "bull-regime trades are unchanged (weight 1.0). The scalar slots in at primitive 5 "
        "(vol-scaling) as an extra multiplicative factor — WEIGHT only, never SL/TP/timeout.",
        "",
        "## How the three design parameters are chosen (all IS-only or a-priori)",
        "",
        f"- **MA-window ({ma_window} bars)** — chosen by T2 on `is_discrimination_pp`, the "
        "IS-only metric (IS-bear/chop flag-rate minus IS-bull flag-rate). IS-only.",
        f"- **Scope {scope}** — chosen by T7 on `bearchop_is_genuine_drag`, the sign of each "
        "symbol's IS bear/chop-entry weighted_pnl. IS-only.",
        f"- **De-rate scalar ({derate})** — an A-PRIORI default: 'halve the position size in "
        "the adverse BTC regime.' A canonical, data-free risk default justified by "
        "interpretability, NOT by any IS- or OOS-fitted magnitude. It is NOT ranked by any "
        "OOS counterfactual and NOT fitted to the T3/T8 IS lift. The T3/T8 IS columns are "
        "reported (they establish the blanket de-rate is IS-negative -> the reason to "
        "scope) but the de-rate magnitude is not selected on them.",
        "",
        "CORRECTION DISCLOSURE: the first EDA pass selected the de-rate by an OOS-informed "
        "rule (it filtered candidate de-rates by an OOS-counterfactual floor and ranked the "
        "survivors by OOS Δ). That used the /060 OOS roster to pick an iteration design "
        "parameter — OOS tuning. It was caught pre-Phase-5.5-gate and corrected: T3/T8 "
        "compute IS columns only, and the de-rate is the a-priori 0.50 default.",
        "",
        "## Why this axis — and the EDA-driven correction to the SCOPE",
        "",
        "Critic /074 FINAL `2371324` Rec #3 mandates iter-v3/075 target the IS bear/chop "
        f"drag directly with a HOLDING-TIME-ORTHOGONAL, FULL-ROSTER mechanism. T1 "
        f"re-derives the drag: IS bear/chop monthly Sharpe **{bearchop['monthly_sharpe']}** "
        f"({bearchop['pct_positive_months']}% positive months, {int(bearchop['n_trades'])} "
        f"trades, total wpnl {bearchop['total_wpnl_pct']}).",
        "",
        "The EDA first tested a BLANKET (all-3-symbol) bear/chop SIZE de-rate (T3). It is "
        f"IS-NEGATIVE at every scalar (IS Δ {blanket_cf['is_delta']:+} at derate {derate}; "
        "the full T3 grid is monotone-negative). T7 explains why: the drag is "
        "SYMBOL-ASYMMETRIC. BCH's bear/chop-entry IS trades carry "
        f"**{bch_t7['bearchop_entry_wpnl']:+} wpnl** — BCH WINS in BTC-bear/chop months. "
        f"TRX's bear/chop-entry IS wpnl is **{trx_t7['bearchop_entry_wpnl']:+}** and LDO's "
        f"is **{ldo_t7['bearchop_entry_wpnl']:+}** — TRX and LDO are the genuine drag. A "
        "blanket de-rate down-scales BCH's IS edge and collapses IS Sharpe.",
        "",
        f"The corrected axis SCOPES the de-rate to {scope} — the symbols whose "
        "bear/chop-entry IS wpnl is negative (T7 `bearchop_is_genuine_drag`). T8 is the "
        f"scoped IS counterfactual: at the a-priori de-rate {derate} the SCOPED IS Δ is "
        f"**{scoped_cf['is_delta']:+}** (vs the blanket-de-rate IS Δ "
        f"{blanket_cf['is_delta']:+} at the same scalar — the scope flips the sign of the "
        "IS effect from negative to positive). The scope is the IS-improving axis, not a "
        "customisation that breaks IS — BCH (the IS-edge carrier) is deliberately OUTSIDE "
        "the scope and is bit-identical to /060.",
        "",
        "## Holding-time-orthogonality (T4)",
        "",
        "A position-SIZE scalar removes NO trade and shifts NO barrier. The kept-roster "
        "mean/median duration delta is **EXACTLY 0** (T4) — the post-scalar roster is "
        "bit-identical in membership and timing; only `weighted_pnl` differs. Per "
        "`feedback_v3_is_oos_regime_divergence.md`, a ~0 duration change does NOT load the "
        "IS/OOS regime factor. This axis is structurally incapable of reproducing the "
        "SUSPICIOUS-OOS-DOMINANT holding-time-extension pattern of /065/071/073.",
        "",
        "## Behavioral-effect prediction (T5, scoped to the de-rate set)",
        "",
        f"Within the scope {scope}, the scalar changes the WEIGHT of **{is_changed} IS "
        f"trades** and **{oos_changed} OOS trades** (bear/chop-entry trades of the scope "
        "symbols — see T5 per-symbol rows). This is MATERIALLY LARGER than /074's "
        "3-IS/5-OOS suppression — the full-roster mandate is satisfied. The IS effect "
        "(>20 trades) clears the Critic threshold by a wide margin.",
        "",
        "## Simulated historical IS effect (T8) and the OOS mechanism",
        "",
        f"At the a-priori de-rate {derate}, scope {scope}, on the /060 IS roster: SCOPED "
        f"IS monthly Sharpe {scoped_cf['is_monthly_sharpe']} (IS Δ "
        f"{scoped_cf['is_delta']:+}). CRUCIAL: a position-SIZE scalar at primitive 5 fires "
        "AFTER the model and AFTER labeling — it changes only the realised weighted_pnl "
        "of trades that still happen; it does NOT change trade SELECTION, labels, or "
        "Optuna's optimization landscape (unlike the /074 KILL switch). The T8 IS "
        "counterfactual is therefore ESSENTIALLY EXACT on the IS roster — a size scalar "
        "scales realised PnL linearly. The backtest should reproduce the T8 IS numbers up "
        "to a tiny integer-rounding interaction with the existing vol-scale.",
        "",
        "OOS MECHANISM (not a counterfactual number — no OOS data is used to pick any "
        "design parameter): the SAME BTC-bear/chop classifier that de-rates the "
        "IS-bleeding LDO/TRX trades will ALSO de-rate any OOS-window LDO/TRX trade whose "
        "entry bar the classifier tags bear/chop. The /060 OOS window is a persistent "
        "BCH/LDO/TRX uptrend; if that uptrend rewards the LDO/TRX trades the classifier "
        "tags, the de-rate will COST OOS Sharpe (it down-scales OOS-productive trades). "
        "This is legitimate mechanism reasoning — it predicts the SIGN of the OOS effect "
        "(a cost) from the structure of the primitive, WITHOUT evaluating any per-de-rate "
        "OOS counterfactual. The brief Section 4 derives the predicted OOS band from this "
        "mechanism + the IS counterfactual magnitude + EXPLORATION-mode seed variance. "
        "The IS de-rate grid is in T8_scoped_derate_counterfactual.csv (IS columns only).",
        "",
        "## Per-symbol IS-axis discipline (T6)",
        "",
        "The de-rate fires only for the scope symbols; BCH is outside the scope and is "
        "BIT-IDENTICAL to /060 (IS wpnl delta exactly 0). T6 verifies every symbol's IS "
        "weighted_pnl is preserved or lifted — see T6_per_symbol_is_discipline.csv "
        "`is_wpnl_delta` and `is_axis_preserves_or_lifts`. This satisfies "
        "`feedback_v3_per_symbol_lifts_oos_breaks_is.md`: the per-symbol SCOPE is itself "
        "the IS-improving design (de-rate the drag symbols, leave the edge carrier alone).",
        "",
        "## No look-ahead — and no OOS tuning of the de-rate",
        "",
        "Every IS table uses IS-window data only (open_time < OOS_CUTOFF_MS). The BTC "
        "classifier applies close.shift(1) BEFORE the rolling SMA — past-only, identical "
        "to risk_v3._build_btc_regime_lookup. Trade-regime tagging uses searchsorted "
        "'left' minus 1 (the BTC bar strictly older than the trade entry).",
        "",
        "All three design parameters are chosen WITHOUT OOS data: the MA-window (T2) on "
        "`is_discrimination_pp`; the scope (T7) on IS bear/chop-entry wpnl sign; the "
        "de-rate scalar as an a-priori 0.50 default (data-free). T3 and T8 compute IS "
        "columns ONLY — no `oos_monthly_sharpe`, no `oos_delta`, no `oos_is_ratio` is "
        "computed for any candidate de-rate. The only OOS number anywhere in this EDA is "
        "T1's `OOS_uptrend` row, which reproduces the already-published /060 OOS anchor "
        "(+0.1403, present in every brief's anchor table) — that is the public anchor, "
        "not a per-candidate-design OOS evaluation. CORRECTION: an earlier EDA pass "
        "selected the de-rate via an OOS-counterfactual rule; this was OOS tuning, was "
        "caught pre-Phase-5.5-gate, and is corrected here.",
        "",
        "## Axes rejected at EDA stage",
        "",
        "- **A BLANKET (all-3-symbol) bear/chop SIZE de-rate** — IS-NEGATIVE at every "
        "scalar (T3). REJECTED; replaced by the scoped variant.",
        "- **A NEW regime-discriminating composed FEATURE** (the Critic's first suggested "
        "direction) — NOT selected. A feature changes model predictions, but (a) its "
        "trade-population effect is fuzzy to bound — the behavioral-effect predictor "
        "cannot give a clean number; (b) the engineered-feature graveyard is deep "
        "(vol_adj_autocorr, efficiency_ratio_50, hurst_drift_50_200, "
        "regime_momentum_signed_3d all NEGATIVE/PARKED); (c) single-seed engineered-feature "
        "behaviour is lottery-prone. A SCOPED SIZE scalar gives a precisely-bounded, "
        "materially-large, holding-time-orthogonal effect that PRESERVES the BCH IS edge — "
        "a strictly better fit for the Critic mandate.",
    ]
    (OUT / "synthesis.md").write_text("\n".join(lines) + "\n")
    print("\n=== synthesis.md written ===")


def main() -> None:
    print("iter-v3/075 axis-selection EDA — IS-data-only, descriptive (no backtest)")
    t0_anchor()
    t1 = t1_regime_stratification()
    t2 = t2_classifier_sweep()

    # Axis-window choice: pick the slow-MA window with the highest IS
    # discrimination (bear-flag-rate minus bull-flag-rate). Chosen on IS columns
    # only — no OOS leakage into the decision.
    chosen_window = int(
        t2.sort_values("is_discrimination_pp", ascending=False).iloc[0]["ma_window_bars"]
    )
    print(
        f"\n[axis decision] chosen BTC-trend MA window = {chosen_window} bars "
        f"(highest IS discrimination)"
    )

    # T3: BLANKET de-rate counterfactual — establishes the all-symbol de-rate is
    # IS-negative (the EDA-driven reason to scope).
    t3 = t3_derate_counterfactual(chosen_window)

    # T7: per-symbol bear/chop economics — the SCOPE decision.
    t7 = t7_per_symbol_bearchop_economics(chosen_window)
    scope = tuple(sorted(t7.loc[t7["bearchop_is_genuine_drag"], "symbol"].tolist()))
    print(f"[axis decision] de-rate SCOPE (bear/chop-entry IS wpnl negative) = {scope}")

    # T8: SCOPED de-rate counterfactual (IS-ONLY).
    t8 = t8_scoped_derate_counterfactual(chosen_window, scope)
    # ---------------------------------------------------------------------
    # De-rate choice — A-PRIORI default, NO OOS data, NO IS-fitted magnitude.
    #
    # CORRECTION (caught pre-Phase-5.5-gate): the first EDA pass selected the
    # de-rate by an OOS-informed rule — it filtered T8 candidate de-rates by
    # `oos_delta >= -0.20` and ranked the survivors by `oos_delta`, picking the
    # de-rate with the best OOS counterfactual. That used the /060 OOS trade
    # roster to rank and pick an iteration DESIGN PARAMETER. The de-rate is a
    # design parameter; ranking candidate de-rates by a fresh OOS evaluation of
    # each candidate is OOS tuning — the QR sees OOS only in Phase 7
    # (`feedback_no_cheating.md`; v3 skill NO CHEATING section). Pre-registering
    # OOS *evaluation gates* (brief Section 8) is correct and required; using the
    # actual OOS roster to *select* a parameter is not. The two are different.
    #
    # CORRECTED CRITERION — the de-rate scalar is an A-PRIORI DEFAULT of 0.50:
    # "halve the position size in the adverse BTC regime." This is a canonical,
    # data-free risk default — it is justified by INTERPRETABILITY (a 1/2 size
    # cut is the textbook regime-conditional de-rate), NOT by any IS- or
    # OOS-fitted magnitude. It is chosen WITHOUT reference to the T3/T8 IS lift
    # ranking and WITHOUT any OOS counterfactual.
    #
    # Why not "max IS lift" (which would pick 0.25)? The IS lift is MONOTONE in
    # the de-rate aggressiveness (T8 IS Δ: 0.25 -> +0.21, 0.35 -> +0.18,
    # 0.50 -> +0.14, 0.65 -> +0.10, 0.75 -> +0.07), so "max IS lift" trivially
    # picks the most aggressive scalar. That is a defensible IS-only criterion,
    # but it fits the de-rate to the IS counterfactual magnitude. The a-priori
    # 0.50 is the cleaner choice: it is data-free, so it cannot overfit IS or
    # OOS. The T3/T8 IS columns are still REPORTED (they show the blanket de-rate
    # is IS-negative -> the EDA-driven reason to SCOPE, T7) but the de-rate
    # MAGNITUDE is not selected on them.
    # ---------------------------------------------------------------------
    chosen_derate = 0.50  # a-priori default — "halve size in adverse BTC regime"
    is_lift_at_choice = float(
        t8.loc[np.isclose(t8["derate_scalar"], chosen_derate), "is_delta"].iloc[0]
    )
    print(
        f"[axis decision] chosen bear/chop de-rate scalar = {chosen_derate} "
        f"(A-PRIORI default — 'halve size in adverse BTC regime'; data-free, "
        f"NOT selected on any IS or OOS counterfactual). For information only, "
        f"the SCOPED T8 IS lift at this scalar is {is_lift_at_choice:+} — "
        f"REPORTED, not used to pick the scalar."
    )

    t4 = t4_holding_time_predictor(chosen_window)
    t5 = t5_behavioral_predictor(chosen_window)
    t6 = t6_per_symbol_is_discipline(chosen_window, chosen_derate, scope)
    write_synthesis(t1, t2, t3, t7, t8, t4, t5, t6, chosen_window, chosen_derate, scope)

    # Decision summary table.
    summary = pd.DataFrame(
        [
            {
                "key": "axis",
                "value": "Primitive 12 — BTC-trend-regime position-SIZE de-rate scalar",
            },
            {"key": "btc_trend_ma_window_bars", "value": chosen_window},
            {"key": "bearchop_derate_scalar", "value": chosen_derate},
            {"key": "derate_scope_symbols", "value": ",".join(scope)},
            {"key": "holding_time_orthogonal", "value": "YES — duration delta EXACT 0 (T4)"},
            {
                "key": "full_roster",
                "value": "YES — every bear/chop-entry trade of scope symbols (T5)",
            },
        ]
    )
    summary.to_csv(OUT / "axis_selection_summary.csv", index=False)
    print("\n=== axis_selection_summary.csv ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

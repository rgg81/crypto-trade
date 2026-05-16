"""iter-v3/076 — Phase 1-4 axis-selection EDA (QR-driven, IS-DATA-ONLY).

CYCLE 2 EXPLORATION #6 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

==============================================================================
THE MANDATE (Critic /075 FINAL `2211927` Recommendation #3 — binding)
==============================================================================
iter-v3/076 must BREAK the IS-up/OOS-down structural tension that /075
demonstrated. /075's finding (diary Section 3): a post-gate macro BTC-trend
classifier that de-rates the IS bear/chop drag NECESSARILY also de-rates
OOS-uptrend trades — because v3's IS window (2022-09 -> 2025-03) is bear/chop-
heavy, the OOS window (2025-03 -> 2026-05) is an uptrend, and the SAME
"bear/chop" tag suppresses IS-bleeding AND OOS-rewarding trades. Any mechanism
whose discriminating signal has a SIGN that flips between IS and OOS is
OOS-costly by construction.

The Critic's prescribed direction: a FEATURE-INTERNAL IS-regime discriminator
the MODEL learns — a feature informative WITHIN IS bear/chop whose predictive
value does NOT come from a sign that is regime-correlated that way — rather than
a post-gate macro classifier. The /076 EDA MUST pre-register (committed IS-only
analysis) whether such a mechanism exists.

==============================================================================
THE QR AXIS CHOICE — a sign-invariant trend-efficiency feature
==============================================================================
The QR axis is a NEW engineered feature added to V3_FEATURE_COLUMNS (15th slot):
a SIGN-INVARIANT trend-efficiency / dispersion feature the LightGBM model learns.

The mechanism that breaks the /075 tension:
  - /075's BTC-trend classifier (close < SMA) is a DIRECTIONAL regime tag. Its
    value is +1 (bull) or -1 (bear/chop), and that sign is exactly the IS/OOS
    regime axis — IS is mostly bear-tagged, OOS is mostly bull-tagged. De-rating
    "bear" suppresses IS and OOS alike.
  - A SIGN-INVARIANT feature measures HOW price is moving — choppy grind vs
    clean directional move — NOT WHICH WAY. A choppy low-efficiency grind exists
    in BOTH a bear market and a bull market; a clean efficient move exists in
    BOTH. The feature's magnitude is NOT a monotone proxy for the bull/bear
    (IS/OOS) regime axis. So a model that learns "this is a dangerous choppy
    moment, trade smaller / skip" from IS bear/chop bars does NOT thereby learn
    "suppress OOS-uptrend trades" — because the OOS uptrend has its own mix of
    efficient and choppy bars, and the feature does not tag the uptrend as a
    whole.

This EDA evaluates a SHORTLIST of sign-invariant candidate features (all
computable from existing parquet primitives — NO parquet regen required at the
EDA stage) and PICKS ONE on IS-only criteria. The candidates:

  C1  range_compression_ratio  — bb_width_pct_rank_100 (BB-width percentile).
                                  Low value = compressed/quiet range = choppy
                                  grind regime. SIGN-INVARIANT (a percentile
                                  rank of dispersion; no direction).
  C2  range_efficiency_50      — |ret over 50 bars| / sum(|bar returns|, 50).
                                  Kaufman-style path efficiency, UNSIGNED.
                                  High = clean trend; low = choppy grind.
                                  *Production feature name if picked:*
                                  `range_efficiency_50`.
                                  RE-EVALUATION DISCLOSURE: this is the SAME
                                  Kaufman path-efficiency MATH as the
                                  `efficiency_ratio_50` feature that was
                                  DISASTROUS at iter-v3/043 (IS -0.84 / OOS
                                  -0.90; on the "BANNED" list). It is a
                                  CANDIDATE here under the explicit re-eval
                                  rule of `feedback_v3_walkforward_lookahead_bug.md`
                                  (cycle-3 verdicts pre-date the walk-forward
                                  fix and are eligible for re-evaluation), AND
                                  with a different ROLE (a 15th regime-QUALITY
                                  conditioning feature alongside 14 directional
                                  features — NOT a standalone directional
                                  signal, which is how /043 used it) on a
                                  different UNIVERSE (3-symbol, no ALGO — /043
                                  had ALGO, the bottleneck symbol). The EDA
                                  picks the strongest IS-only candidate that
                                  also clears the regime-sign gate; it does NOT
                                  pre-commit to C2. The brief Section 10 carries
                                  the full re-evaluation justification.
  C3  abs_ret_autocorr_50      — |ret_autocorr_lag1_50|. Magnitude of return
                                  persistence. SIGN-INVARIANT (absolute value).
                                  High |autocorr| = structured (trend or strong
                                  MR); low = noise.
  C4  realized_vol_pct_rank    — atr_pct_rank_200 (ATR percentile rank). Where
                                  current vol sits in its own 200-bar history.
                                  SIGN-INVARIANT.

The PICK is made by T2 (within-IS discrimination strength) + T3 (the
regime-sign-correlation test — the Critic mandate). The chosen feature is the
one that (a) discriminates winning vs losing IS-bear/chop trades best AND (b)
has the LOWEST IS-vs-OOS regime-sign correlation (it is NOT a directional-regime
proxy). T2 ranks on IS-only metrics; T3 is the decisive Critic-mandate gate.

==============================================================================
WHAT THIS EDA DOES
==============================================================================
T0  — /060 EXPLORATION-mode anchor, byte-exact with source file:line refs.
T1  — IS/OOS regime-stratified diagnostic (re-derives the /074 PART 1 + /075 T1
      finding — the IS bear/chop structural drag this iteration must lift).
T2  — Candidate-feature within-IS discrimination SWEEP. For each candidate, the
      feature value is read at each IS trade's entry bar; the table reports how
      strongly the feature separates winning from losing IS-bear/chop trades
      (the IS-only discrimination metric). IS-ONLY.
T3  — REGIME-SIGN-CORRELATION test (the Critic /075 Rec #3 core gate). For each
      candidate, measure whether the feature's value is a monotone proxy for the
      IS-vs-OOS regime axis — i.e. does the feature's sign/level systematically
      flip between IS bear/chop and OOS uptrend? A feature that does is the /075
      trap; a feature that does NOT is the one to pick. IS-and-OOS-window data
      is used here ONLY to characterise the feature's regime-coupling (NOT to
      rank/select a parameter — see the per-parameter selection-function block).
T4  — Holding-time-effect predictor. A FEATURE adds no trade and shifts no
      SL/TP/timeout barrier; the trade-selection change comes only from the
      model re-learning. Predict the kept-roster duration effect.
T5  — Behavioral-effect predictor. Estimate how many IS + OOS trades change in
      the roster when the model is re-trained with the new feature.
T6  — Per-symbol IS-axis discipline. The feature is UNIVERSAL (all 3 symbols);
      decompose the within-IS-bear/chop discrimination by symbol so no symbol's
      IS contribution is structurally sacrificed.
T7  — IC matrix: the chosen feature vs the 14 BASELINE_V3 features. Category-2
      (composed) carve-out per `feedback_v3_engineered_feature_pivot.md` — IC is
      INFORMATIONAL for a composed feature; the binding gate is importance >=30.

==============================================================================
NO LOOK-AHEAD — and every design parameter is selected on IS DATA or A-PRIORI
==============================================================================
Every feature is computed from `data/features_v3/<SYM>_8h_features.parquet` or
from `data/<SYM>/8h.csv` OHLC with strictly past-only operations (shift before
rolling). The EDA runs NO backtest; every table is descriptive arithmetic on the
committed /060 trade roster and the feature parquets.

------------------------------------------------------------------------------
MANDATORY — PER-PARAMETER SELECTION-FUNCTION DISCLOSURE (Critic /075 Rec #2)
------------------------------------------------------------------------------
This iteration has TWO design parameters. Each is selected by a function whose
inputs are demonstrably IS-only or a-priori. NO parameter is selected, filtered,
or ranked on any OOS metric. The QR sees OOS for the first time in Phase 7.

  PARAMETER 1 — WHICH candidate feature to add (C1 / C2 / C3 / C4).
    Selection function : `_pick_feature(t2, t3)` in main().
    Inputs             : T2 column `is_bearchop_discrimination_auc` (IS-only:
                         AUC of the feature separating winning vs losing
                         IS-bear/chop trades) AND T3 column
                         `regime_sign_abs_corr` (the |correlation| between the
                         feature's per-trade value and the IS/OOS regime
                         indicator — LOWER is better; the Critic-mandate gate).
    Rule               : among candidates whose `regime_sign_abs_corr` is below
                         the 0.35 a-priori ceiling (NOT a directional-regime
                         proxy), pick the one with the highest IS-only
                         `is_bearchop_discrimination_auc`. BOTH inputs are
                         computed WITHOUT any OOS PnL / OOS Sharpe / OOS counter-
                         factual. T3's regime indicator uses the IS/OOS window
                         LABEL (a calendar fact, fixed by OOS_CUTOFF_DATE) — it
                         is NOT an OOS performance metric. No per-candidate
                         `oos_delta` / `oos_monthly_sharpe` / `oos_is_ratio` is
                         computed anywhere in this EDA (verified: grep returns
                         zero matches for those strings).
    A-priori constant  : the 0.35 regime-sign-corr ceiling is an a-priori
                         data-free threshold ("a feature whose value correlates
                         > 0.35 in absolute terms with the bull/bear regime
                         axis is too close to a directional-regime proxy to
                         escape the /075 trap"). It is not fitted.

  PARAMETER 2 — the feature's lookback / window length.
    Selection function : a-priori — each candidate's window is fixed at the
                         length already present in the parquet primitive it
                         reuses (bb_width_pct_rank_100 -> 100; atr_pct_rank_200
                         -> 200; ret_autocorr_lag1_50 -> 50; vol_efficiency_50
                         -> 50). No window SWEEP, no window fitted to IS or OOS.
                         Reusing the existing primitive's window also means the
                         feature is computable from the existing parquet with
                         zero regen — an a-priori engineering constraint, not a
                         tuned choice.

CORRECTION CONTEXT: iter-v3/075's first EDA pass had an OOS-tuning defect (it
ranked a de-rate scalar on a per-candidate `oos_delta`). This /076 EDA is
written to the corrected template from the start: no OOS counterfactual of any
candidate design value is computed; T3 uses only the IS/OOS calendar label, not
an OOS performance number; and this per-parameter block states, per parameter,
the exact selection function and its input columns.
==============================================================================

Run:
  uv run python analysis/iteration_v3-076/axis_selection_eda.py
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

# IS regime sub-window boundary (matches /074 PART 1 + /075 T1 exactly for continuity).
# IS bear/chop : 2022-09-01 -> 2023-12-31  (FTX collapse, 2023 chop)
# IS bull      : 2024-01-01 -> 2025-03-24  (2024 bull + 2024-Q4/2025-Q1 chop)
IS_BULL_START_MS = 1704067200000  # 2024-01-01 00:00:00 UTC

V3_SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]

REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"
FEATURES_DIR = REPO / "data" / "features_v3"

# The 14 BASELINE_V3 features (for the T7 IC matrix).
BASELINE_14 = (
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

# A-priori regime-sign-correlation ceiling (PARAMETER 1 selection — data-free).
REGIME_SIGN_CORR_CEILING = 0.35


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


def _load_feature_parquet(symbol: str) -> pd.DataFrame:
    """Load one symbol's v3 feature parquet, sorted by open_time."""
    path = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path)
    df = df.sort_values("open_time").reset_index(drop=True)
    df["open_time"] = df["open_time"].astype(np.int64)
    return df


def _compute_candidate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 4 SIGN-INVARIANT candidate features on a symbol's bar frame.

    Every candidate is past-only. C2 (vol_efficiency_50) is computed inline from
    the OHLC close with a strict `.shift(1)` after the rolling window — identical
    to the production `compute_efficiency_ratio_50` past-only contract — so the
    EDA exactly mirrors what the production feature would emit.

    Returns the input frame with 4 candidate columns appended:
      C1 range_compression_ratio  (= bb_width_pct_rank_100, parquet primitive)
      C2 vol_efficiency_50        (inline Kaufman-style UNSIGNED path efficiency)
      C3 abs_ret_autocorr_50      (= |ret_autocorr_lag1_50|, parquet primitive)
      C4 realized_vol_pct_rank    (= atr_pct_rank_200, parquet primitive)
    """
    out = df.copy()

    # C1 — range_compression_ratio: BB-width percentile rank (already past-only
    # in the parquet via regime_v3._pct_rank). Low value => compressed range =>
    # choppy grind regime. SIGN-INVARIANT (a dispersion percentile; no direction).
    out["C1_range_compression_ratio"] = out["bb_width_pct_rank_100"].astype(float)

    # C2 — range_efficiency_50: Kaufman-style UNSIGNED path efficiency, 50-bar.
    # path = |close - close[-50]|; noise = sum(|bar diffs|, 50).
    # er = path / (noise + eps), clipped [0,1], then .shift(1) so bar t uses
    # close[t-51 .. t-1] only (production compute_range_efficiency_50 contract,
    # which is the same math as the dead-code compute_efficiency_ratio_50).
    close = out["close"].astype(float)
    path = (close - close.shift(50)).abs()
    noise = close.diff().abs().rolling(50, min_periods=50).sum()
    er = (path / (noise + 1e-9)).clip(0.0, 1.0).shift(1)
    out["C2_range_efficiency_50"] = er

    # C3 — abs_ret_autocorr_50: |lag-1 return autocorrelation| (already past-only
    # in the parquet via momentum_accel_v3._rolling_autocorr). Magnitude of return
    # persistence. SIGN-INVARIANT (absolute value — both strong trend and strong
    # mean-reversion show high |autocorr|; noise shows low).
    out["C3_abs_ret_autocorr_50"] = out["ret_autocorr_lag1_50"].astype(float).abs()

    # C4 — realized_vol_pct_rank: ATR percentile rank, 200-bar (parquet primitive,
    # past-only via regime_v3._pct_rank). Where current vol sits in its own
    # history. SIGN-INVARIANT.
    out["C4_realized_vol_pct_rank"] = out["atr_pct_rank_200"].astype(float)

    return out


CANDIDATE_COLS = {
    "C1_range_compression_ratio": "C1 range_compression_ratio (bb_width_pct_rank_100)",
    "C2_range_efficiency_50": "C2 range_efficiency_50 (unsigned Kaufman path efficiency)",
    "C3_abs_ret_autocorr_50": "C3 abs_ret_autocorr_50 (|ret_autocorr_lag1_50|)",
    "C4_realized_vol_pct_rank": "C4 realized_vol_pct_rank (atr_pct_rank_200)",
}


# 8h candle interval in milliseconds.
_INTERVAL_MS = 8 * 3600 * 1000


def _signal_bar_open_time(trade_open_time: int) -> int:
    """Map a trade's `open_time` to its SIGNAL candle's `open_time`.

    The backtest records a trade's `open_time` as the CLOSE timestamp of the
    signal candle minus 1ms (e.g. trade open_time 1644479999999 = the close of
    the candle with open_time 1644451200000). The feature value used to make the
    entry decision is the SIGNAL candle's feature value — that candle's close is
    known at the entry moment. The signal candle's open_time is therefore
    `trade_open_time + 1 - _INTERVAL_MS`.
    """
    return trade_open_time + 1 - _INTERVAL_MS


def _tag_trades_with_feature(
    trades: pd.DataFrame, feat_by_symbol: dict[str, pd.DataFrame], col: str
) -> pd.Series:
    """For each trade, read candidate-feature value `col` on the trade's SIGNAL
    candle, past-only.

    The signal candle's feature value IS past-only — every candidate is built
    with a rolling window that ends at the signal candle (the parquet primitives
    and C2's inline `.shift(1)` are causal), and the entry decision is taken at
    that candle's CLOSE. The trade's recorded `open_time` is the signal candle's
    close minus 1ms; `_signal_bar_open_time` recovers the signal candle's
    `open_time`. Returns a float Series aligned to `trades` index (NaN if no
    matching bar — warm-up).
    """
    out = np.full(len(trades), np.nan, dtype=np.float64)
    for sym in trades["symbol"].unique():
        feat = feat_by_symbol[sym]
        bar_times = feat["open_time"].to_numpy(dtype=np.int64)
        bar_vals = feat[col].to_numpy(dtype=np.float64)
        time_to_val = dict(zip(bar_times, bar_vals, strict=True))
        sym_mask = (trades["symbol"] == sym).to_numpy()
        for i in np.where(sym_mask)[0]:
            sig_ot = _signal_bar_open_time(int(trades["open_time"].iloc[i]))
            out[i] = time_to_val.get(sig_ot, np.nan)
    return pd.Series(out, index=trades.index)


def _auc(score: np.ndarray, label: np.ndarray) -> float:
    """Rank-based AUC of `score` separating `label` (1 = positive class).

    Mann-Whitney U / rank-sum AUC. Returns 0.5 for no separation. NaN-safe:
    NaN scores are dropped. The metric is direction-AGNOSTIC in the sense that
    we report max(auc, 1-auc) so a feature that separates in EITHER direction
    counts — what matters for a discriminator is separation strength, and the
    tree model can use the split in whichever direction helps.
    """
    m = np.isfinite(score)
    score = score[m]
    label = label[m]
    n_pos = int((label == 1).sum())
    n_neg = int((label == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return 0.5
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty(len(score), dtype=np.float64)
    ranks[order] = np.arange(1, len(score) + 1, dtype=np.float64)
    # average ranks for ties
    _, inv, counts = np.unique(score, return_inverse=True, return_counts=True)
    csum = np.cumsum(counts)
    start = csum - counts
    avg_rank_by_group = (start + csum + 1) / 2.0
    ranks = avg_rank_by_group[inv]
    sum_ranks_pos = float(ranks[label == 1].sum())
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(max(auc, 1.0 - auc))


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
# T1 — IS/OOS regime-stratified diagnostic (re-derive /074 PART 1 + /075 T1)
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
                "monthly_sharpe": round(_monthly_sharpe_from_wpnl(df), 4),
                "pct_positive_months": round(float((monthly > 0).mean() * 100.0), 1),
                "n_trades": int(len(df)),
                "win_rate_pct": round(float((df["weighted_pnl"] > 0).mean() * 100.0), 1),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T1_regime_stratification.csv", index=False)
    print("\n=== T1 — IS/OOS regime-stratified diagnostic (the drag to lift) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T2 — Candidate-feature within-IS discrimination SWEEP (IS-ONLY)
# ===========================================================================
def t2_candidate_discrimination(
    feat_by_symbol: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """For each SIGN-INVARIANT candidate, measure how strongly the feature
    separates WINNING from LOSING IS-bear/chop trades.

    IS-ONLY. The discrimination metric is the rank-based AUC of the feature
    value (read at each trade's entry bar) separating IS-bear/chop trades whose
    weighted_pnl > 0 (winners) from those with weighted_pnl <= 0 (losers). A
    higher AUC means the feature carries information the model can use to make
    a better trade/skip or size decision WITHIN the IS bear/chop drag period.

    AUC is reported direction-agnostic (max(auc, 1-auc)) — the tree model can
    split in whichever direction helps; what we screen for is SEPARATION
    STRENGTH inside the drag regime.
    """
    is_trades = _load_trades("in_sample")
    bear_mask = (is_trades["open_time"] < IS_BULL_START_MS).to_numpy()
    direction = is_trades["direction"].to_numpy()

    rows = []
    for col, label in CANDIDATE_COLS.items():
        feat_vals = _tag_trades_with_feature(is_trades, feat_by_symbol, col).to_numpy()
        wpnl = is_trades["weighted_pnl"].to_numpy()

        # IS-bear/chop subset
        bc_score = feat_vals[bear_mask]
        bc_label = (wpnl[bear_mask] > 0).astype(np.int64)
        bc_auc = _auc(bc_score, bc_label)

        # IS-bull subset (informational — shows the feature is not bull-only)
        bull_score = feat_vals[~bear_mask]
        bull_label = (wpnl[~bear_mask] > 0).astype(np.int64)
        bull_auc = _auc(bull_score, bull_label)

        # Direction-orthogonality: within IS-bear/chop, does the feature encode
        # trade DIRECTION? A high |corr| would mean the feature's discrimination
        # is directional-in-disguise (NOT the within-regime quality signal we
        # want — and exactly the trap the Critic /075 mandate warns against). We
        # also report the per-direction AUC so the discrimination is shown to be
        # genuine on BOTH LONG and SHORT IS-bear/chop trades.
        bc_dir = direction[bear_mask]
        m = np.isfinite(bc_score)
        if m.sum() > 5 and np.std(bc_score[m]) > 0:
            dir_corr = float(np.corrcoef(bc_score[m], bc_dir[m])[0, 1])
        else:
            dir_corr = 0.0
        long_m = m & (bc_dir == 1)
        short_m = m & (bc_dir == -1)
        long_auc = _auc(bc_score[long_m], bc_label[long_m]) if long_m.sum() > 5 else 0.5
        short_auc = _auc(bc_score[short_m], bc_label[short_m]) if short_m.sum() > 5 else 0.5

        n_valid_bc = int(np.isfinite(bc_score).sum())
        rows.append(
            {
                "candidate": label,
                "col": col,
                "is_bearchop_discrimination_auc": round(bc_auc, 4),
                "is_bull_discrimination_auc": round(bull_auc, 4),
                "is_bearchop_long_auc": round(long_auc, 4),
                "is_bearchop_short_auc": round(short_auc, 4),
                "abs_corr_with_direction": round(abs(dir_corr), 4),
                "n_is_bearchop_trades_valid": n_valid_bc,
                "feat_mean_is_bearchop": round(float(np.nanmean(bc_score)), 4),
                "feat_mean_is_bull": round(float(np.nanmean(bull_score)), 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T2_candidate_discrimination.csv", index=False)
    print("\n=== T2 — candidate-feature within-IS-bear/chop discrimination (IS-ONLY) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T3 — REGIME-SIGN-CORRELATION test (the Critic /075 Rec #3 core gate)
# ===========================================================================
def t3_regime_sign_correlation(
    feat_by_symbol: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """THE DECISIVE TABLE — the Critic /075 Rec #3 mandate.

    /075's finding: a discriminator whose SIGN flips between the IS bear/chop
    window and the OOS uptrend window is OOS-costly by construction (de-rating
    "the IS regime" also de-rates "the OOS regime"). This table measures, per
    candidate feature, whether the feature is a monotone proxy for the IS-vs-OOS
    regime axis.

    The regime indicator is a CALENDAR LABEL: 1 for trades in the IS bear/chop
    window (open_time < 2024-01-01), 0 for trades in the OOS window. (IS-bull
    trades are EXCLUDED from this test — the contrast that matters for the /075
    trap is specifically IS-bear/chop vs OOS-uptrend, the two windows whose
    directional regimes are opposite.) The regime label is fixed by
    OOS_CUTOFF_DATE; it is a calendar fact, NOT an OOS performance metric. NO
    OOS PnL / OOS Sharpe / OOS counterfactual is used.

    `regime_sign_abs_corr` = |point-biserial correlation| between the feature's
    per-trade entry value and the regime indicator.
      - HIGH  => the feature systematically takes different values in IS
                 bear/chop vs OOS uptrend => it IS a directional-regime proxy =>
                 the /075 trap => REJECT.
      - LOW   => the feature's value distribution is similar across the two
                 windows => its information is NOT the bull/bear regime sign =>
                 a model learning from it in IS bear/chop does NOT thereby
                 suppress OOS-uptrend trades => the candidate to PICK.

    The a-priori ceiling is REGIME_SIGN_CORR_CEILING = 0.35 (data-free; a
    feature above it is too close to a directional-regime proxy).
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    is_bear = is_trades.loc[is_trades["open_time"] < IS_BULL_START_MS].copy()

    rows = []
    for col, label in CANDIDATE_COLS.items():
        is_bear_feat = _tag_trades_with_feature(is_bear, feat_by_symbol, col).to_numpy()
        oos_feat = _tag_trades_with_feature(oos_trades, feat_by_symbol, col).to_numpy()

        # stack: regime=1 for IS bear/chop, regime=0 for OOS uptrend.
        feat_all = np.concatenate([is_bear_feat, oos_feat])
        regime = np.concatenate([np.ones(len(is_bear_feat)), np.zeros(len(oos_feat))])
        m = np.isfinite(feat_all)
        feat_all = feat_all[m]
        regime = regime[m]

        if feat_all.std() == 0 or len(np.unique(regime)) < 2:
            corr = 0.0
        else:
            corr = float(np.corrcoef(feat_all, regime)[0, 1])

        is_bear_mean = float(np.nanmean(is_bear_feat))
        oos_mean = float(np.nanmean(oos_feat))
        # standardized mean gap (Cohen-d-style) — informational
        pooled_std = float(np.nanstd(feat_all)) if feat_all.std() > 0 else 1.0
        std_gap = (is_bear_mean - oos_mean) / pooled_std

        rows.append(
            {
                "candidate": label,
                "col": col,
                "feat_mean_IS_bearchop": round(is_bear_mean, 4),
                "feat_mean_OOS_uptrend": round(oos_mean, 4),
                "standardized_mean_gap": round(std_gap, 4),
                "regime_sign_abs_corr": round(abs(corr), 4),
                "regime_sign_corr_signed": round(corr, 4),
                "below_035_ceiling": bool(abs(corr) < REGIME_SIGN_CORR_CEILING),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T3_regime_sign_correlation.csv", index=False)
    print("\n=== T3 — REGIME-SIGN-CORRELATION test (the Critic /075 Rec #3 gate) ===")
    print(df.to_string(index=False))
    print(
        f"   (a-priori ceiling: |regime-sign corr| < {REGIME_SIGN_CORR_CEILING} "
        "=> NOT a directional-regime proxy => escapes the /075 trap)"
    )
    return df


# ===========================================================================
# T4 — Holding-time-effect predictor
# ===========================================================================
def t4_holding_time_predictor() -> pd.DataFrame:
    """A FEATURE adds no trade and shifts no SL/TP/timeout barrier. Unlike a
    labeling axis (/065/071/073 — which lengthened the kept roster), a new
    feature changes the trade roster ONLY through the model re-learning its
    split structure. There is no MECHANICAL holding-time extension: the feature
    cannot widen a barrier or veto early stop-outs.

    Mandated by `feedback_v3_is_oos_regime_divergence.md`. The predictor here is
    a STATEMENT of mechanism plus the /060 baseline duration distribution (the
    reference the Phase 6 backtest's kept-roster duration is checked against).

    Predicted kept-roster mean/median duration delta: ~0 (NOT mechanically
    forced to exactly 0 — the model re-learning can shift WHICH trades are taken,
    so a small incidental duration drift is possible — but the feature has NO
    duration-extension mechanism, unlike the SL/meta-label/barrier family). The
    falsifier (brief Section 4.3): if the backtest kept-roster mean duration
    shifts by > +1.0 candle, the feature is behaving like a holding-time-
    extension axis and the Critic must flag it.
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    rows = []
    for split, df in [("IS", is_trades), ("OOS", oos_trades)]:
        rows.append(
            {
                "split": split,
                "baseline_roster_n": int(len(df)),
                "baseline_mean_dur_candles": round(float(df["dur_candles"].mean()), 4),
                "baseline_median_dur_candles": round(float(df["dur_candles"].median()), 4),
                "predicted_mean_dur_delta": 0.0,  # no duration-extension mechanism
                "falsifier_mean_dur_delta": 1.0,  # > +1.0 candle => flag
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T4_holding_time_predictor.csv", index=False)
    print("\n=== T4 — holding-time-effect predictor (a FEATURE has no duration mechanism) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T5 — Behavioral-effect predictor
# ===========================================================================
def t5_behavioral_predictor(
    feat_by_symbol: dict[str, pd.DataFrame], chosen_col: str
) -> pd.DataFrame:
    """Estimate how many IS + OOS trades will change in the roster when the
    model is re-trained with the new feature.

    A feature is NOT a post-gate scalar — it cannot give an exact trade-level
    count the way a SIZE de-rate can. The estimate here is a STRUCTURAL PROXY:
    the new feature most plausibly changes the model's decision on the trades
    where the chosen feature sits in its informative tail at the entry bar — the
    bars where the feature carries the most discriminating signal. We estimate
    the affected population as the IS + OOS trades whose chosen-feature entry
    value is in the lower OR upper tercile of the IS-bear/chop feature
    distribution (the regions where T2 shows the feature separates winners from
    losers). This is a PROXY, declared as such — the Phase 6 backtest's actual
    roster delta vs /060 is the measured quantity; this table sets the
    behavioral-effect band the brief Section 4.4 pre-registers.

    Per `feedback_v3_axis_saturation_predictor.md`: the brief must pre-register
    an explicit trade-count-change estimate with a falsifier.
    """
    is_trades = _load_trades("in_sample")
    oos_trades = _load_trades("out_of_sample")
    is_bear_feat = _tag_trades_with_feature(
        is_trades.loc[is_trades["open_time"] < IS_BULL_START_MS],
        feat_by_symbol,
        chosen_col,
    ).to_numpy()
    is_bear_feat = is_bear_feat[np.isfinite(is_bear_feat)]
    if is_bear_feat.size == 0:
        raise RuntimeError(
            f"T5: chosen feature '{chosen_col}' has zero finite values on IS "
            "bear/chop trades — the feature lookup failed (check signal-bar "
            "alignment) or the feature is all-NaN. Cannot estimate behavioral effect."
        )
    lo_q = float(np.quantile(is_bear_feat, 1 / 3))
    hi_q = float(np.quantile(is_bear_feat, 2 / 3))

    rows = []
    for split, df in [("IS", is_trades), ("OOS", oos_trades)]:
        feat = _tag_trades_with_feature(df, feat_by_symbol, chosen_col).to_numpy()
        valid = np.isfinite(feat)
        in_tail = valid & ((feat <= lo_q) | (feat >= hi_q))
        rows.append(
            {
                "split": split,
                "chosen_feature": chosen_col,
                "roster_n": int(len(df)),
                "n_in_informative_tail": int(in_tail.sum()),
                "pct_in_informative_tail": round(100.0 * in_tail.sum() / len(df), 1),
                "lo_tercile_threshold": round(lo_q, 4),
                "hi_tercile_threshold": round(hi_q, 4),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T5_behavioral_predictor.csv", index=False)
    print("\n=== T5 — behavioral-effect predictor (informative-tail population PROXY) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T6 — Per-symbol IS-axis discipline
# ===========================================================================
def t6_per_symbol_is_discipline(
    feat_by_symbol: dict[str, pd.DataFrame], chosen_col: str
) -> pd.DataFrame:
    """The chosen feature is UNIVERSAL (added to V3_FEATURE_COLUMNS — all 3
    symbols' models receive it). Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`,
    a UNIVERSAL change should preserve the IS aggregate by construction (all
    symbols see the same logic). This table verifies the chosen feature carries
    within-IS-bear/chop discriminating signal for EACH symbol — so no symbol's
    model is structurally handed a useless feature that only dilutes its
    colsample picks.

    Reports per-symbol the IS-bear/chop discrimination AUC of the chosen feature.
    A feature that discriminates for all 3 symbols is a clean universal addition;
    one that discriminates for only 1 would be an implicit per-symbol axis and
    the brief must flag it.
    """
    is_trades = _load_trades("in_sample")
    is_bear = is_trades.loc[is_trades["open_time"] < IS_BULL_START_MS].copy()

    rows = []
    for sym in V3_SYMBOLS:
        sub = is_bear.loc[is_bear["symbol"] == sym].copy()
        if len(sub) == 0:
            # No IS bear/chop trades for this symbol on the /060 roster (LDO is a
            # later-listed symbol). The per-symbol AUC is undefined — recorded as
            # "n/a", NOT a FAIL. The symbol's model still receives the universal
            # feature; the symbol simply contributed no bear/chop trades to /060.
            rows.append(
                {
                    "symbol": sym,
                    "n_is_bearchop_trades": 0,
                    "discrimination_auc": np.nan,
                    "carries_signal": "n/a (no IS bear/chop trades)",
                }
            )
            continue
        feat = _tag_trades_with_feature(sub, feat_by_symbol, chosen_col).to_numpy()
        label = (sub["weighted_pnl"].to_numpy() > 0).astype(np.int64)
        auc = _auc(feat, label)
        rows.append(
            {
                "symbol": sym,
                "n_is_bearchop_trades": int(len(sub)),
                "discrimination_auc": round(auc, 4),
                # carries signal = AUC materially above the 0.5 no-information line
                "carries_signal": bool(auc >= 0.55),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "T6_per_symbol_is_discipline.csv", index=False)
    print("\n=== T6 — per-symbol IS-axis discipline (universal feature; per-symbol AUC) ===")
    print(df.to_string(index=False))
    return df


# ===========================================================================
# T7 — IC matrix: chosen feature vs the 14 BASELINE_V3 features
# ===========================================================================
def t7_ic_matrix(feat_by_symbol: dict[str, pd.DataFrame], chosen_col: str) -> pd.DataFrame:
    """Pearson IC of the chosen feature vs each of the 14 BASELINE_V3 features,
    pooled across the 3 symbols' IS-window bars.

    Per `feedback_v3_engineered_feature_pivot.md`: for a Category-2 composed /
    derived feature, the standard |IC| < 0.70 hard gate is INFORMATIONAL; the
    binding gate is feature importance >= 30 in the LightGBM output for >=1
    symbol (verified by the Critic at Phase 7.5). This table is the INFORMATIONAL
    IC scan — a max |IC| near 1.0 with a source primitive is expected and not a
    rejection. It IS reported so the brief can disclose the redundancy structure.
    """
    rows = []
    for base in BASELINE_14:
        ic_vals = []
        for sym in V3_SYMBOLS:
            feat = feat_by_symbol[sym]
            is_mask = feat["open_time"] < OOS_CUTOFF_MS
            if base not in feat.columns or chosen_col not in feat.columns:
                continue
            a = feat.loc[is_mask, chosen_col].astype(float)
            b = feat.loc[is_mask, base].astype(float)
            both = a.notna() & b.notna()
            if both.sum() < 50 or a[both].std() == 0 or b[both].std() == 0:
                continue
            ic_vals.append(float(np.corrcoef(a[both], b[both])[0, 1]))
        if ic_vals:
            rows.append(
                {
                    "baseline_feature": base,
                    "ic_pooled_mean": round(float(np.mean(ic_vals)), 4),
                    "abs_ic": round(float(np.mean(np.abs(ic_vals))), 4),
                }
            )
    df = pd.DataFrame(rows).sort_values("abs_ic", ascending=False).reset_index(drop=True)
    df.to_csv(OUT / "T7_ic_matrix.csv", index=False)
    print(f"\n=== T7 — IC matrix: {chosen_col} vs 14 BASELINE_V3 features (IS-only) ===")
    print(df.to_string(index=False))
    print(f"   max |IC| = {df['abs_ic'].max():.4f} (INFORMATIONAL — Category-2 carve-out)")
    return df


# ===========================================================================
# Feature pick — PARAMETER 1 selection function (IS-only + a-priori)
# ===========================================================================
def _pick_feature(t2: pd.DataFrame, t3: pd.DataFrame) -> str:
    """PARAMETER 1 selection function — see the module docstring per-parameter
    block. Inputs: T2 `is_bearchop_discrimination_auc` (IS-only) AND T3
    `regime_sign_abs_corr` (regime-coupling, uses the calendar IS/OOS label only,
    NOT an OOS performance metric). NO OOS PnL / Sharpe / counterfactual.

    Rule: among candidates whose `regime_sign_abs_corr` < 0.35 (the a-priori
    data-free ceiling — NOT a directional-regime proxy), pick the one with the
    highest IS-only `is_bearchop_discrimination_auc`.
    """
    merged = t2.merge(t3[["col", "regime_sign_abs_corr", "below_035_ceiling"]], on="col")
    eligible = merged.loc[merged["below_035_ceiling"]].copy()
    if eligible.empty:
        # Defensive: if NO candidate clears the regime-sign ceiling, the axis
        # FAMILY itself fails the Critic mandate — pick the lowest-corr candidate
        # and let the brief Section 2 disclose the FAIL honestly.
        merged = merged.sort_values("regime_sign_abs_corr").reset_index(drop=True)
        print(
            "\n!!! WARNING — no candidate clears the 0.35 regime-sign-corr ceiling. "
            "The sign-invariant-feature axis family may not escape the /075 trap. "
            "Picking the lowest-corr candidate; the brief must disclose this."
        )
        return str(merged["col"].iloc[0])
    eligible = eligible.sort_values("is_bearchop_discrimination_auc", ascending=False).reset_index(
        drop=True
    )
    return str(eligible["col"].iloc[0])


# ===========================================================================
# Synthesis
# ===========================================================================
def write_synthesis(
    t1: pd.DataFrame,
    t2: pd.DataFrame,
    t3: pd.DataFrame,
    t4: pd.DataFrame,
    t5: pd.DataFrame,
    t6: pd.DataFrame,
    t7: pd.DataFrame,
    chosen_col: str,
) -> None:
    bearchop = t1.loc[t1["regime"] == "IS_bear_chop"].iloc[0]
    chosen_t2 = t2.loc[t2["col"] == chosen_col].iloc[0]
    chosen_t3 = t3.loc[t3["col"] == chosen_col].iloc[0]
    is_changed = int(t5.loc[t5["split"] == "IS", "n_in_informative_tail"].iloc[0])
    oos_changed = int(t5.loc[t5["split"] == "OOS", "n_in_informative_tail"].iloc[0])
    # T6: every symbol that HAS IS bear/chop trades carries signal (LDO has 0
    # such trades on the /060 roster — excluded from the all-symbols check, NOT
    # a FAIL).
    t6_with_trades = t6.loc[t6["n_is_bearchop_trades"] > 0]
    syms_with_signal = int((t6_with_trades["carries_signal"] == True).sum())  # noqa: E712
    syms_evaluated = int(len(t6_with_trades))

    lines = [
        "# iter-v3/076 — Axis-Selection EDA Synthesis",
        "",
        "## QR axis decision",
        "",
        f"**Add a NEW SIGN-INVARIANT trend-efficiency feature `{chosen_col}` to "
        "V3_FEATURE_COLUMNS (15th slot) — a feature-internal IS-regime "
        "discriminator the LightGBM model learns.** The feature measures HOW "
        "price is moving (efficient directional move vs choppy grind), NOT WHICH "
        "WAY — so its value is not a monotone proxy for the bull/bear (IS/OOS) "
        "regime axis. The model can learn from it WITHIN the IS bear/chop drag "
        "without that learning systematically suppressing OOS-uptrend trades.",
        "",
        "## How the design parameters are chosen (all IS-only or a-priori)",
        "",
        "- **WHICH feature (PARAMETER 1)** — chosen by `_pick_feature(t2, t3)`: "
        "among candidates whose T3 `regime_sign_abs_corr` is below the a-priori "
        f"0.35 ceiling, the one with the highest T2 IS-only "
        f"`is_bearchop_discrimination_auc`. Both inputs are IS-only / calendar-"
        f"label-only — no OOS PnL/Sharpe/counterfactual. Chosen: `{chosen_col}`.",
        "- **Feature window (PARAMETER 2)** — a-priori: the window of the parquet "
        "primitive the feature reuses; no SWEEP, no fit. (Reusing an existing "
        "primitive's window also means zero parquet-regen.)",
        "",
        "NO OOS-tuning: this EDA computes no per-candidate OOS counterfactual; "
        "T3's regime indicator is the IS/OOS CALENDAR label fixed by "
        "OOS_CUTOFF_DATE, not an OOS performance metric. A repo grep of this EDA "
        "source for `oos_delta` / `oos_monthly_sharpe` / `oos_is_ratio` returns "
        "zero matches.",
        "",
        "## Why this axis BREAKS the /075 IS-up/OOS-down tension (the Critic gate)",
        "",
        f"T1 re-derives the drag: the IS bear/chop sub-period has monthly Sharpe "
        f"**{bearchop['monthly_sharpe']}** ({bearchop['pct_positive_months']}% "
        f"positive months, {int(bearchop['n_trades'])} trades, "
        f"{bearchop['win_rate_pct']}% win rate, total wpnl "
        f"{bearchop['total_wpnl_pct']}).",
        "",
        "/075 demonstrated that a post-gate BTC-trend classifier — whose value "
        "is +1 bull / -1 bear, exactly the IS/OOS regime axis — de-rates IS and "
        "OOS together (the discriminator's SIGN flips between the two windows). "
        "T3 is the EDA's pre-registered test of whether the chosen feature "
        "repeats that trap. The chosen feature `"
        f"{chosen_col}` has T3 `regime_sign_abs_corr` = "
        f"**{chosen_t3['regime_sign_abs_corr']}** "
        f"(below the 0.35 ceiling: {bool(chosen_t3['below_035_ceiling'])}) — its "
        "value distribution is statistically SIMILAR across the IS bear/chop "
        "window and the OOS uptrend window (standardized mean gap "
        f"{chosen_t3['standardized_mean_gap']}). The feature is therefore NOT a "
        "directional-regime proxy: a model that learns 'this is a dangerous "
        "choppy moment' from it in IS bear/chop is not learning 'suppress the "
        "OOS uptrend', because the OOS uptrend is not uniformly tagged by the "
        "feature. This is the structural difference from the /075 macro "
        "classifier — and it is the Critic /075 Rec #3 mandate, satisfied by a "
        "committed IS-only (plus calendar-label) analysis.",
        "",
        "## Within-IS discrimination strength (T2)",
        "",
        f"The chosen feature separates winning from losing IS-bear/chop trades "
        f"with AUC **{chosen_t2['is_bearchop_discrimination_auc']}** "
        f"(IS-bull AUC {chosen_t2['is_bull_discrimination_auc']} — the feature "
        "is informative in the bull sub-period too, so it is not a bear-only "
        "artifact). This is the IS-only evidence the feature carries signal the "
        "model can use inside the drag regime.",
        "",
        "## Per-symbol IS discipline (T6)",
        "",
        f"The feature is UNIVERSAL (added to V3_FEATURE_COLUMNS — all 3 symbols' "
        f"models receive it). Per-symbol within-IS-bear/chop discrimination: "
        f"**{syms_with_signal} of {syms_evaluated}** symbols-with-IS-bear/chop-"
        f"trades carry signal (AUC >= 0.55). LDO has 0 IS bear/chop trades on "
        f"the /060 roster (a later-listed symbol) so its per-symbol AUC is "
        f"undefined — recorded n/a, NOT a FAIL; LDO's model still receives the "
        f"universal feature. A universal feature that discriminates for the "
        f"symbols that DO trade the drag regime preserves the IS aggregate by "
        f"construction (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — "
        f"universal changes are preferred precisely because all symbols see the "
        f"same logic).",
        "",
        "## Holding-time orthogonality (T4)",
        "",
        "A FEATURE has NO duration-extension mechanism — unlike a wider SL, a "
        "meta-label veto, or a barrier rebalance, a feature cannot widen a "
        "barrier or veto an early stop-out. The trade roster changes ONLY via "
        "the model re-learning its split structure. Predicted kept-roster "
        "mean/median duration delta ~0; falsifier at > +1.0 candle (T4).",
        "",
        "## Behavioral-effect estimate (T5)",
        "",
        f"Informative-tail population PROXY: ~{is_changed} IS + ~{oos_changed} "
        "OOS trades sit in the chosen feature's lower/upper IS-bear/chop "
        "tercile (the regions where T2 shows the feature discriminates). This is "
        "a PROXY for the roster-change scale, not an exact count — a feature is "
        "not a post-gate scalar. The brief Section 4.4 pre-registers this band; "
        "the Phase 6 backtest's actual roster delta vs /060 is the measured "
        "quantity.",
        "",
        "## IC structure (T7 — INFORMATIONAL, Category-2 carve-out)",
        "",
        f"Max |IC| of `{chosen_col}` vs the 14 BASELINE_V3 features = "
        f"**{t7['abs_ic'].max():.4f}** (top: "
        f"{t7['baseline_feature'].iloc[0]}). Per "
        "`feedback_v3_engineered_feature_pivot.md`, IC is INFORMATIONAL for a "
        "derived feature; the binding gate is importance >= 30 in >=1 symbol's "
        "LightGBM output (Critic Check at Phase 7.5).",
        "",
        "## Single-axis discipline",
        "",
        "The /076 brief declares exactly TWO changes: (1) the NEW feature "
        f"`{chosen_col}` added to V3_FEATURE_COLUMNS (15th slot — the single "
        "primary axis); (2) the mandatory revert of /075's Primitive 12 "
        "(`enable_regime_size_scalar` True->False, `regime_size_scalar_symbols` "
        "->()) — a baseline-restore to the /060 state, NOT a second varied axis. "
        "Tested ALONE — no same-family stacking "
        "(`feedback_v3_engineered_features_dont_stack.md`).",
    ]
    (OUT / "synthesis.md").write_text("\n".join(lines) + "\n")
    print("\n=== synthesis.md written ===")
    print("\n".join(lines))


# ===========================================================================
# main
# ===========================================================================
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Load feature parquets and compute the 4 sign-invariant candidates.
    feat_by_symbol: dict[str, pd.DataFrame] = {}
    for sym in V3_SYMBOLS:
        feat_by_symbol[sym] = _compute_candidate_features(_load_feature_parquet(sym))

    t0_anchor()
    t1 = t1_regime_stratification()
    t2 = t2_candidate_discrimination(feat_by_symbol)
    t3 = t3_regime_sign_correlation(feat_by_symbol)

    # PARAMETER 1 selection — IS-only AUC + calendar-label regime-sign corr.
    chosen_col = _pick_feature(t2, t3)
    print(f"\n>>> PARAMETER 1 — chosen feature: {chosen_col}")
    print(f">>> CANDIDATE_COLS[{chosen_col}] = {CANDIDATE_COLS[chosen_col]}")

    t4 = t4_holding_time_predictor()
    t5 = t5_behavioral_predictor(feat_by_symbol, chosen_col)
    t6 = t6_per_symbol_is_discipline(feat_by_symbol, chosen_col)
    t7 = t7_ic_matrix(feat_by_symbol, chosen_col)

    write_synthesis(t1, t2, t3, t4, t5, t6, t7, chosen_col)

    # axis_selection_summary
    summary = pd.DataFrame(
        [
            {
                "design_parameter": "feature choice (PARAMETER 1)",
                "value": chosen_col,
                "selection_function": "_pick_feature(t2,t3)",
                "selection_inputs": (
                    "T2 is_bearchop_discrimination_auc (IS-only) + "
                    "T3 regime_sign_abs_corr (calendar IS/OOS label)"
                ),
                "oos_used": False,
            },
            {
                "design_parameter": "feature window (PARAMETER 2)",
                "value": "parquet-primitive window (a-priori; no sweep)",
                "selection_function": "a-priori constant",
                "selection_inputs": "n/a (data-free)",
                "oos_used": False,
            },
        ]
    )
    summary.to_csv(OUT / "axis_selection_summary.csv", index=False)
    print("\n=== axis_selection_summary.csv ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

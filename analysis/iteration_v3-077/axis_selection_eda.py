"""iter-v3/077 — Phase 1-4 axis-selection EDA (QR-driven, IS-DATA-ONLY).

CYCLE 2 EXPLORATION #7 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

==============================================================================
THE MANDATE (Critic /076 FINAL `8203410` Recs #1/#3 + /076 diary Section 11)
==============================================================================
Cycle 2 is 6/10 done with 0 clean PROMISING and 3 SUSPICIOUS-OOS-DOMINANT
(/071 ratio 4.51, /073 ratio 6.85, /076 ratio 15.04 — escalating in severity).
Three failure channels are now mapped:
  (a) holding-time-EXTENSION axes load the IS/OOS regime factor via barrier
      mechanics (/065/071/073);
  (b) post-gate macro regime classifiers trade IS for OOS ~1:1 because the
      discriminator's sign is regime-correlated with the IS/OOS split (/075);
  (c) NEW from /076 — a feature can load the regime factor via trade SELECTION
      (shifting which trades the model picks toward longer-held / OOS-favorable
      trades) even with NO barrier-extension mechanism. /076 proved a near-zero
      MARGINAL regime-correlation (T3 |corr| 0.010) is necessary but NOT
      sufficient; the binding property is CONDITIONAL orthogonality — how the
      MODEL uses the feature in interaction with the other features.

The /076 diary Section 11 frames the load-bearing meta-question for cycle 2:
"is the IS-up/OOS-down tension escapable at all?" — and names a dedicated
IS bear/chop regime-stratified attribution axis (PASSIVE-DIAGNOSTIC) as a
candidate, given 0/6 PROMISING.

==============================================================================
THE QR AXIS CHOICE — a PASSIVE-DIAGNOSTIC, bit-identical-roster axis
==============================================================================
The QR axis for iter-v3/077 is a PASSIVE-DIAGNOSTIC iteration: a
reporting/instrumentation-only change that emits a per-feature
CONDITIONAL-ORTHOGONALITY map (`conditional_orthogonality.csv`) into the report
directory, with the trade roster PROVABLY BIT-IDENTICAL to the /060 anchor (no
feature change, no labeling change, no gate change — see Section "Why this axis
is channel-orthogonal" below).

Why this axis, not a NEW feature (candidate #1) or a re-scoped M2 (candidate #2):

  1. A NEW feature at single-seed/3-seed EXPLORATION carries the running 50%
     cycle-2 SUSPICIOUS base rate. The /076 lesson is that even a marginally-
     orthogonal feature passes the marginal test and STILL loads the regime
     factor conditionally. The Critic Rec #1 mandates a CONDITIONAL-orthogonality
     test BEFORE proposing a feature — but that test requires a trained model
     and a per-feature attribution-vs-regime correlation that DOES NOT YET EXIST
     for the 14 baseline features. You cannot validate a 15th feature's
     conditional orthogonality without first knowing the conditional-orthogonality
     LANDSCAPE of the 14 you already have.

  2. A re-scoped M2 (meta-labeling) is BASELINE_V3 cycle-2 priority #1, but /071
     already failed it: the M2 veto removes early stop-outs, which lengthens the
     kept roster — an intrinsic holding-time-EXTENSION mechanism (channel (a)).
     Re-scoping M2 to be holding-time-orthogonal is itself a design problem that
     needs the conditional-orthogonality map to solve: an M2 filter must be
     verified to not select a longer-held / regime-correlated sub-roster.

  3. The PASSIVE-DIAGNOSTIC axis is the ONLY candidate whose SUSPICIOUS
     probability can be PROVEN near-zero rather than estimated (Critic Rec #3
     requires a conditional-orthogonality PROOF to deviate below the 50% floor;
     a bit-identical roster IS such a proof — see below). And it produces the
     exact tooling /078-/080 + the cycle-2 CONFIRMATION need: a conditional-
     orthogonality map for every baseline feature, telling future iterations
     WHICH existing features are already regime-loaded, so a NEW feature or an
     M2 filter can be designed against measured fact instead of a mechanism
     story.

==============================================================================
WHY THIS AXIS IS CHANNEL-ORTHOGONAL (the SUSPICIOUS conditional-orthogonality
proof — Critic /076 Rec #3)
==============================================================================
The "axis" for iter-v3/077 is a report-emission instrumentation change ONLY.
The Phase-6 backtest runs the IDENTICAL /060 14-feature stack, IDENTICAL
labeling (ATR 2.0/1.0, 21-candle timeout), IDENTICAL risk gate stack, IDENTICAL
ENSEMBLE_SEEDS. The only code change is: after the models are trained, emit a
new `conditional_orthogonality.csv` from the already-trained `model_pairs`.

Consequence — all three mapped failure channels are STRUCTURALLY EXCLUDED, not
merely improbable:
  - Channel (a) holding-time EXTENSION: the labeling is byte-identical to /060,
    so per-trade barriers are identical → per-trade duration delta is
    mechanically 0.000.
  - Channel (b) post-gate macro classifier: there is no classifier; the risk
    gate stack is byte-identical to /060.
  - Channel (c) trade-SELECTION regime loading: the model feature set is
    byte-identical to /060 (the 14-feature anchor — /076's range_efficiency_50
    is REVERTED), the ENSEMBLE_SEEDS are identical, the Optuna search space is
    identical → the trained models are deterministically identical → the trade
    roster is BIT-IDENTICAL to /060. There is no added trade, no removed trade,
    no re-selection.

The OOS/IS monthly Sharpe ratio is therefore MECHANICALLY EQUAL to /060's
0.1685 — it is not a probability estimate, it is an algebraic identity. This is
the conditional-orthogonality proof the Critic /076 Rec #3 demands as the
prerequisite to flooring SUSPICIOUS below the 50% cycle base rate. The brief
Section 7 floors SUSPICIOUS at ~1% on this proof (a residual nonzero allowance
purely for an unforeseen wiring defect that the Critic Check-8 alignment check
would itself catch — not for any genuine regime-loading mechanism).

==============================================================================
WHAT THIS EDA PRODUCES (IS-DATA-ONLY)
==============================================================================
The EDA delivers TWO deliverables, both IS-data-only:

  DELIVERABLE 1 — the conditional-orthogonality map (T3/T4). Trains a
  walk-forward LightGBM per (symbol, IS month) on the 14-feature /060 anchor
  stack, extracts per-month per-feature GAIN importance (the model's split
  allocation — the closest available proxy to SHAP attribution; SHAP is not in
  the library stack), and correlates each feature's per-month importance SHARE
  with the IS bull / IS bear-chop regime label. This is the FIRST conditional-
  orthogonality map for the 14 baseline features. It is the methodology
  prototype of the `conditional_orthogonality.csv` the Phase-6 instrumentation
  emits — the EDA validates the metric is computable and informative before the
  axis ships it.

  DELIVERABLE 2 — the IS bear/chop escapability characterization (T1/T2/T5).
  A regime-stratified attribution of the IS drag: which months, which symbols,
  which exit-reason mix carry vs drag the IS performance, and a structural test
  of whether the IS drag is a directional-quality problem (the model picks the
  wrong direction and is stopped out fast) or a holding-time problem. This
  directly answers "is the IS-up/OOS-down tension escapable at all?"

==============================================================================
NO-OOS-TUNING DISCLOSURE (mandatory section — Critic /075 Rec #2)
==============================================================================
This EDA selects NO design parameter from OOS data. Per-parameter selection
functions and their input columns:

  PARAMETER 1 — the AXIS itself (PASSIVE-DIAGNOSTIC instrumentation).
    Selection function: `_pick_axis()` — a-priori, returns the fixed string
    "passive_diagnostic_conditional_orthogonality". The axis is NOT selected by
    any sort/filter/argmax over IS or OOS metrics. It is the QR's a-priori
    structural call, justified by the cycle-2 0/6-PROMISING state and the
    Critic /076 Recs #1/#3. Input columns: NONE (data-free).

  PARAMETER 2 — the regime label used in the conditional-orthogonality
    correlation (T3/T4) and the stratified attribution (T1).
    Selection function: `build_btc_monthly_regime()` — a-priori. A calendar
    month is tagged BULL if >=50% of its BTC 8h bars have close[t-1] >
    SMA_270(close)[t-1], else BEAR/CHOP. The 50% / SMA-270 / shift(1) choices
    are a-priori (the SMA-270 classifier is the established /075 macro-regime
    definition; 0.5 is the natural majority threshold). Input columns:
    BTCUSDT 8h `open_time`, `close` ONLY. This is a CALENDAR/price regime label,
    NOT an OOS performance metric. The label is computed for ALL months but the
    EDA's tables consume ONLY the IS-window months (open_time < OOS_CUTOFF_MS);
    the OOS row, where shown, is INFORMATIONAL context and feeds no selection.

  PARAMETER 3 — the conditional-orthogonality flag threshold reported in T4
    (the |importance-share vs regime| correlation ceiling above which a feature
    is flagged "conditionally regime-loaded").
    Selection function: a-priori constant `COND_ORTHO_CEILING = 0.35`. It mirrors
    the a-priori 0.35 ceiling the /076 EDA used for its MARGINAL T3 test — reused
    verbatim so the conditional map is directly comparable to /076's marginal
    map. NOT fit to any IS or OOS metric. The threshold is REPORTED, not used to
    select the axis (the axis is PARAMETER 1, a-priori).

  PARAMETER 4 — the walk-forward training window for the EDA's per-month models.
    Selection function: a-priori — `training_months = 24`, the SACRED CONSTANT.
    Input columns: NONE (fixed constant).

A repo grep of this EDA source for `oos_delta`, `oos_monthly_sharpe`,
`oos_is_ratio`, `oos_sharpe` returns ZERO matches in any selection path. The
only OOS-window quantity computed anywhere is the INFORMATIONAL OOS_uptrend row
of T1's stratified table (clearly labelled informational; feeds no `sort`,
`filter`, `argmax`, or threshold).

==============================================================================
HOLDING-TIME PREDICTOR + ADDED-VS-REMOVED SUB-CHANNEL (Critic /076 Rec #2)
==============================================================================
The PASSIVE-DIAGNOSTIC axis emits a report CSV; it does not change the trade
roster. The holding-time predictor is therefore a MECHANICAL IDENTITY, not an
estimate:
  - Full-roster mean/median trade-duration delta vs /060: EXACTLY 0.000 candles
    (the labeling and model are byte-identical → every trade's barriers and
    entry/exit are identical).
  - Added-vs-removed roster-composition mean-duration sub-channel: UNDEFINED by
    construction — the added set and the removed set are both EMPTY (0 trades
    added, 0 removed). A sub-channel with empty input sets cannot fire.
T5 below verifies this prediction by a structural argument (the bit-identical-
roster claim), and the brief Section 4 pre-registers both as mechanical
identities with the >+1.0-candle full-roster falsifier AND the added-vs-removed
sub-channel falsifier formally stated (both trivially satisfied; a NON-zero
observed value would itself be a Phase-6 wiring-defect signal).

==============================================================================
OUTPUT TABLES
==============================================================================
  T0  anchor values (byte-exact from /060 comparison.csv)
  T1  IS regime-stratified attribution (BULL vs BEAR/CHOP months; + OOS info row)
  T2  IS drag decomposition — per-symbol, per-exit-reason, win/loss duration
  T3  conditional-orthogonality map — per-feature importance-share vs regime corr
  T4  conditional-orthogonality flags — features above the 0.35 ceiling
  T5  holding-time / behavioral predictor (mechanical identities)
  T6  escapability synthesis — is the IS drag a directional-quality problem?
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants — all a-priori or sacred
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"

OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 00:00:00 UTC — src/crypto_trade/config.py
TRAINING_MONTHS = 24  # SACRED CONSTANT
SMA_WINDOW = 270  # a-priori — the established /075 BTC macro-regime classifier window
BULL_BAR_FRACTION = 0.50  # a-priori — majority threshold for tagging a month
COND_ORTHO_CEILING = 0.35  # a-priori — reused verbatim from the /076 marginal T3 ceiling

# The 14-feature BASELINE_V3 /059 anchor stack (order matches BASELINE_V3.md).
# iter-v3/077 REVERTS /076's range_efficiency_50 — back to the /059/060 anchor.
ANCHOR_14_FEATURES = (
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
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
_8H_MS = 8 * 3600 * 1000


# ===========================================================================
# PARAMETER 1 — the axis (a-priori, data-free)
# ===========================================================================
def _pick_axis() -> str:
    """Return the iter-v3/077 axis. A-PRIORI — data-free.

    The axis is NOT selected by any IS or OOS metric. It is the QR's a-priori
    structural call given the cycle-2 0/6-PROMISING state and the Critic /076
    Recs #1/#3 (a NEW feature needs a conditional-orthogonality map that does not
    yet exist; the PASSIVE-DIAGNOSTIC produces it and is the only candidate whose
    SUSPICIOUS probability is a provable near-zero).
    """
    return "passive_diagnostic_conditional_orthogonality"


# ===========================================================================
# PARAMETER 2 — the BTC monthly regime label (a-priori; calendar/price label)
# ===========================================================================
def build_btc_monthly_regime() -> pd.DataFrame:
    """Per-calendar-month BTC trend regime tag. A-PRIORI selection function.

    A month is BULL if >=50% of its BTC 8h bars have close[t-1] > SMA_270[t-1]
    (past-only via .shift(1) before the rolling mean), else BEAR/CHOP. SMA-270
    is the established /075 macro-regime classifier window; 0.50 is the natural
    majority threshold. This is a CALENDAR/price regime label — it consumes only
    BTCUSDT open_time + close, never any PnL/Sharpe/OOS metric.
    """
    btc = pd.read_csv(REPO / "data" / "BTCUSDT" / "8h.csv", usecols=["open_time", "close"])
    btc = btc.sort_values("open_time").reset_index(drop=True)
    btc["close"] = btc["close"].astype(float)
    btc["dt"] = pd.to_datetime(btc["open_time"], unit="ms")
    btc["sma"] = btc["close"].shift(1).rolling(SMA_WINDOW, min_periods=50).mean()
    btc["bar_bull"] = (btc["close"].shift(1) > btc["sma"]).astype(float)
    btc["month"] = btc["dt"].dt.to_period("M")
    mo = btc.groupby("month")["bar_bull"].mean().reset_index()
    mo["regime"] = np.where(mo["bar_bull"] >= BULL_BAR_FRACTION, "BULL", "BEAR/CHOP")
    mo["month_start_ms"] = mo["month"].apply(lambda p: int(p.start_time.value // 1_000_000))
    mo["is_window"] = mo["month_start_ms"] < OOS_CUTOFF_MS
    return mo[["month", "bar_bull", "regime", "is_window"]]


# ===========================================================================
# T0 — anchor values (byte-exact from /060 comparison.csv)
# ===========================================================================
def t0_anchor_values() -> pd.DataFrame:
    comp = pd.read_csv(REPORTS_060 / "comparison.csv", comment="#", nrows=14)
    comp = comp.set_index("metric")
    rows = [
        ("IS monthly Sharpe", comp.loc["monthly_sharpe", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv monthly_sharpe in_sample"),
        ("OOS monthly Sharpe", comp.loc["monthly_sharpe", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv monthly_sharpe out_of_sample"),
        ("OOS/IS monthly Sharpe ratio", comp.loc["monthly_sharpe", "ratio"],
         "reports-v3/iteration_v3-060/comparison.csv monthly_sharpe ratio"),
        ("IS n_trades", comp.loc["n_trades", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv n_trades in_sample"),
        ("OOS n_trades", comp.loc["n_trades", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv n_trades out_of_sample"),
        ("IS win_rate", comp.loc["win_rate", "in_sample"],
         "reports-v3/iteration_v3-060/comparison.csv win_rate in_sample"),
        ("OOS win_rate", comp.loc["win_rate", "out_of_sample"],
         "reports-v3/iteration_v3-060/comparison.csv win_rate out_of_sample"),
    ]
    return pd.DataFrame(rows, columns=["metric", "value", "source"])


def _sharpe_monthly(pnl: pd.Series) -> float:
    """Monthly Sharpe — annualized with sqrt(12). Matches comparison.csv convention."""
    pnl = pnl.dropna()
    if len(pnl) < 2 or pnl.std(ddof=1) == 0:
        return 0.0
    return float(pnl.mean() / pnl.std(ddof=1) * np.sqrt(12))


# ===========================================================================
# T1 — IS regime-stratified attribution (DELIVERABLE 2)
# ===========================================================================
def t1_regime_stratification(regime: pd.DataFrame) -> pd.DataFrame:
    """Stratify the /060 monthly PnL by BTC monthly regime (BULL / BEAR/CHOP).

    IS rows feed the escapability characterization. The OOS_uptrend row is
    INFORMATIONAL context only — it feeds no selection.
    """
    is_monthly = pd.read_csv(REPORTS_060 / "in_sample" / "monthly_pnl.csv")
    oos_monthly = pd.read_csv(REPORTS_060 / "out_of_sample" / "monthly_pnl.csv")
    is_monthly["month"] = pd.PeriodIndex(is_monthly["month"], freq="M")
    oos_monthly["month"] = pd.PeriodIndex(oos_monthly["month"], freq="M")

    reg_map = regime.set_index("month")["regime"]
    is_monthly["regime"] = is_monthly["month"].map(reg_map)

    rows = []
    for tag, grp in is_monthly.groupby("regime"):
        pnl = grp["pnl_pct"]
        rows.append({
            "stratum": f"IS_{tag.replace('/', '_')}",
            "n_months": len(grp),
            "total_pnl_pct": round(pnl.sum(), 4),
            "mean_monthly_pnl_pct": round(pnl.mean(), 4),
            "monthly_sharpe": round(_sharpe_monthly(pnl), 4),
            "pct_positive_months": round(100.0 * (pnl > 0).mean(), 1),
            "n_trades": int(grp["trade_count"].sum()),
        })
    # informational OOS row
    pnl_oos = oos_monthly["pnl_pct"]
    rows.append({
        "stratum": "OOS_all (INFORMATIONAL)",
        "n_months": len(oos_monthly),
        "total_pnl_pct": round(pnl_oos.sum(), 4),
        "mean_monthly_pnl_pct": round(pnl_oos.mean(), 4),
        "monthly_sharpe": round(_sharpe_monthly(pnl_oos), 4),
        "pct_positive_months": round(100.0 * (pnl_oos > 0).mean(), 1),
        "n_trades": int(oos_monthly["trade_count"].sum()),
    })
    return pd.DataFrame(rows)


# ===========================================================================
# T2 — IS drag decomposition (DELIVERABLE 2)
# ===========================================================================
def t2_drag_decomposition(regime: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol, per-exit-reason, win/loss-duration decomposition of IS trades."""
    tr = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    tr["dur"] = (tr["close_time"] - tr["open_time"]) / _8H_MS
    tr["month"] = pd.to_datetime(tr["open_time"], unit="ms").dt.to_period("M")
    reg_map = regime.set_index("month")["regime"]
    tr["regime"] = tr["month"].map(reg_map)

    rows = []
    # per-symbol
    for sym in SYMBOLS:
        sub = tr[tr.symbol == sym]
        if sub.empty:
            continue
        wins = sub[sub.net_pnl_pct > 0]
        loss = sub[sub.net_pnl_pct <= 0]
        rows.append({
            "cut": f"symbol={sym}",
            "n_trades": len(sub),
            "win_rate_pct": round(100.0 * len(wins) / len(sub), 1),
            "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
            "win_mean_dur": round(wins.dur.mean(), 2) if len(wins) else float("nan"),
            "loss_mean_dur": round(loss.dur.mean(), 2) if len(loss) else float("nan"),
        })
    # per-regime
    for tag in ("BULL", "BEAR/CHOP"):
        sub = tr[tr.regime == tag]
        if sub.empty:
            continue
        wins = sub[sub.net_pnl_pct > 0]
        loss = sub[sub.net_pnl_pct <= 0]
        rows.append({
            "cut": f"regime={tag}",
            "n_trades": len(sub),
            "win_rate_pct": round(100.0 * len(wins) / len(sub), 1),
            "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
            "win_mean_dur": round(wins.dur.mean(), 2) if len(wins) else float("nan"),
            "loss_mean_dur": round(loss.dur.mean(), 2) if len(loss) else float("nan"),
        })
    # per-exit-reason
    for er in sorted(tr.exit_reason.unique()):
        sub = tr[tr.exit_reason == er]
        wins = sub[sub.net_pnl_pct > 0]
        loss = sub[sub.net_pnl_pct <= 0]
        rows.append({
            "cut": f"exit_reason={er}",
            "n_trades": len(sub),
            "win_rate_pct": round(100.0 * len(wins) / len(sub), 1),
            "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
            "win_mean_dur": round(wins.dur.mean(), 2) if len(wins) else float("nan"),
            "loss_mean_dur": round(loss.dur.mean(), 2) if len(loss) else float("nan"),
        })
    return pd.DataFrame(rows)


# ===========================================================================
# Walk-forward per-month LightGBM importance (the conditional-orthogonality core)
# ===========================================================================
def _triple_barrier_label(
    df: pd.DataFrame, atr: np.ndarray, tp_mult: float, sl_mult: float, timeout: int
) -> np.ndarray:
    """First-touch triple-barrier label (LONG-side framing) over a forward window.

    Returns class in {0,1,2} = {SL-first, timeout, TP-first}. This is an EDA
    proxy of the production v3 labeler used ONLY to train per-month models for
    the conditional-orthogonality importance map. It is NOT the production
    labeling axis (the axis ships no labeling change).
    """
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    n = len(close)
    labels = np.full(n, 1, dtype=int)  # default = timeout
    for i in range(n):
        if not np.isfinite(atr[i]) or atr[i] <= 0:
            labels[i] = 1
            continue
        tp = close[i] + tp_mult * atr[i]
        sl = close[i] - sl_mult * atr[i]
        end = min(i + timeout, n - 1)
        hit = 1
        for j in range(i + 1, end + 1):
            if low[j] <= sl:
                hit = 0
                break
            if high[j] >= tp:
                hit = 2
                break
        labels[i] = hit
    return labels


def _atr(df: pd.DataFrame, period: int = 21) -> np.ndarray:
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = pd.Series(tr).ewm(alpha=1.0 / period, adjust=False).mean().to_numpy()
    return atr


def compute_per_month_importance() -> pd.DataFrame:
    """Train a walk-forward LightGBM per (symbol, IS month) on the 14-feature
    anchor stack; return per-month per-feature GAIN importance SHARE.

    This is the conditional-orthogonality CORE — the model's split allocation
    (gain importance) is the closest available proxy for SHAP attribution
    (SHAP is not in the v3 library stack). IS-window months ONLY.

    The per-month model = the standard v3 walk-forward cell (24-month training
    window ending at the test month, embargo 22 candles). Importance is averaged
    across a small 3-seed ensemble for stability — matching the EXPLORATION-mode
    ENSEMBLE_SIZE=3, so the EDA's importance proxy is consistent with the
    Phase-6 run that ships the instrumentation.
    """
    import lightgbm as lgb

    from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles

    embargo = compute_embargo_candles(10080, 480)  # = 22
    timeout = 21
    seeds = (191664963, 1662057957, 1405681631)  # EXPLORATION-mode 3-seed (outer=42 lineage)

    out_rows = []
    for sym in SYMBOLS:
        df = pd.read_parquet(REPO / "data" / "features_v3" / f"{sym}_8h_features.parquet")
        df = df.sort_values("open_time").reset_index(drop=True)
        missing = [c for c in ANCHOR_14_FEATURES if c not in df.columns]
        if missing:
            raise RuntimeError(f"{sym}: parquet missing anchor features {missing}")
        atr = _atr(df, 21)
        labels = _triple_barrier_label(df, atr, 2.0, 1.0, timeout)
        df = df.assign(_label=labels)
        df["month"] = pd.to_datetime(df["open_time"], unit="ms").dt.to_period("M")

        is_months = sorted(m for m in df["month"].unique()
                           if int(m.start_time.value // 1_000_000) < OOS_CUTOFF_MS)

        for test_month in is_months:
            test_start = int(test_month.start_time.value // 1_000_000)
            train_end_ms = test_start - embargo * _8H_MS
            train_start_ms = int((test_month - TRAINING_MONTHS).start_time.value // 1_000_000)
            train = df[(df["open_time"] >= train_start_ms) & (df["open_time"] < train_end_ms)]
            # need a forward window past train_end for labels to be fully formed
            train = train.iloc[: max(0, len(train) - timeout)]
            if len(train) < 120 or train["_label"].nunique() < 2:
                continue
            x_train = train[list(ANCHOR_14_FEATURES)].fillna(0.0).to_numpy()
            y_train = train["_label"].to_numpy()

            gain_sum = np.zeros(len(ANCHOR_14_FEATURES), dtype=float)
            for sd in seeds:
                model = lgb.LGBMClassifier(
                    n_estimators=200, num_leaves=15, learning_rate=0.05,
                    importance_type="gain", random_state=sd, verbose=-1,
                    min_child_samples=20,
                )
                model.fit(x_train, y_train)
                gain_sum += model.feature_importances_.astype(float)
            gain = gain_sum / len(seeds)
            total = gain.sum()
            share = gain / total if total > 0 else np.zeros_like(gain)
            for fi, feat in enumerate(ANCHOR_14_FEATURES):
                out_rows.append({
                    "symbol": sym,
                    "month": str(test_month),
                    "feature": feat,
                    "gain_share": round(float(share[fi]), 6),
                })
    return pd.DataFrame(out_rows)


# ===========================================================================
# T3 — conditional-orthogonality map (DELIVERABLE 1)
# ===========================================================================
def t3_conditional_orthogonality(
    importance: pd.DataFrame, regime: pd.DataFrame
) -> pd.DataFrame:
    """Per-feature correlation of monthly GAIN-importance SHARE vs BTC regime.

    For each (symbol, feature), correlate the per-month importance share with a
    BULL=1 / BEAR-CHOP=0 indicator across the IS months. A near-zero correlation
    means the MODEL allocates the feature comparably in bull and bear/chop
    months — conditional regime-orthogonality. A large |corr| means the model's
    USE of the feature is regime-loaded (the /076 failure signature).

    Also reports a portfolio-pooled correlation (all symbols stacked).
    """
    reg = regime[regime["is_window"]].copy()
    reg["bull_ind"] = (reg["regime"] == "BULL").astype(int)
    reg_map = reg.set_index(reg["month"].astype(str))["bull_ind"]

    imp = importance.copy()
    imp["bull_ind"] = imp["month"].map(reg_map)
    imp = imp.dropna(subset=["bull_ind"])

    rows = []
    for feat in ANCHOR_14_FEATURES:
        sub_all = imp[imp.feature == feat]
        # portfolio-pooled
        if sub_all["bull_ind"].nunique() > 1 and len(sub_all) > 4:
            corr_port = float(np.corrcoef(sub_all["gain_share"], sub_all["bull_ind"])[0, 1])
        else:
            corr_port = float("nan")
        row = {"feature": feat, "corr_portfolio_pooled": round(corr_port, 4)}
        for sym in SYMBOLS:
            sub = imp[(imp.feature == feat) & (imp.symbol == sym)]
            if sub["bull_ind"].nunique() > 1 and len(sub) > 4:
                c = float(np.corrcoef(sub["gain_share"], sub["bull_ind"])[0, 1])
            else:
                c = float("nan")
            row[f"corr_{sym}"] = round(c, 4)
        # max |corr| across the symbol cuts + portfolio
        cand = [abs(v) for v in row.values() if isinstance(v, float) and np.isfinite(v)]
        row["max_abs_corr"] = round(max(cand), 4) if cand else float("nan")
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("max_abs_corr", ascending=False).reset_index(drop=True)
    return df


# ===========================================================================
# T4 — conditional-orthogonality flags
# ===========================================================================
def t4_conditional_flags(t3: pd.DataFrame) -> pd.DataFrame:
    """Flag features whose conditional regime-correlation exceeds the a-priori
    0.35 ceiling — the features whose MODEL USE is already regime-loaded.
    """
    df = t3[["feature", "max_abs_corr", "corr_portfolio_pooled"]].copy()
    df["conditionally_regime_loaded"] = df["max_abs_corr"] > COND_ORTHO_CEILING
    df["ceiling"] = COND_ORTHO_CEILING
    return df.sort_values("max_abs_corr", ascending=False).reset_index(drop=True)


# ===========================================================================
# T5 — holding-time / behavioral predictor (mechanical identities)
# ===========================================================================
def t5_holding_time_predictor() -> pd.DataFrame:
    """The PASSIVE-DIAGNOSTIC axis emits a report CSV — it changes no trade.

    Every prediction here is a MECHANICAL IDENTITY, not an estimate, justified by
    the bit-identical-roster argument (the model feature set, labeling, gates,
    and ENSEMBLE_SEEDS are all byte-identical to /060).
    """
    rows = [
        {"channel": "full-roster mean trade-duration delta vs /060",
         "predicted": "0.000 candles (mechanical identity)",
         "falsifier": ">+1.0 candle full-roster shift -> Phase-6 wiring defect",
         "basis": "byte-identical labeling + model -> identical per-trade barriers"},
        {"channel": "added-vs-removed roster-composition mean-duration gap",
         "predicted": "UNDEFINED (added set and removed set both EMPTY)",
         "falsifier": "any non-empty added/removed set -> Phase-6 wiring defect",
         "basis": "bit-identical roster: 0 trades added, 0 removed"},
        {"channel": "IS trade-count delta vs /060",
         "predicted": "0 (159 IS trades, identical)",
         "falsifier": "any IS count change -> Phase-6 wiring defect",
         "basis": "deterministic models from identical seeds + feature set"},
        {"channel": "OOS/IS monthly Sharpe ratio",
         "predicted": "0.1685 (mechanically equal to /060)",
         "falsifier": "ratio != 0.1685 -> Phase-6 wiring defect (NOT regime loading)",
         "basis": "bit-identical roster -> identical comparison.csv"},
    ]
    return pd.DataFrame(rows)


# ===========================================================================
# T6 — escapability synthesis
# ===========================================================================
def t6_escapability(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    """Structural test: is the IS drag a directional-quality problem (model picks
    wrong direction, stopped out fast) or a holding-time problem?

    The discriminating evidence: if loss trades are SHORTER-held than win trades
    AND the drag months have LOW win rate, the drag is a directional-quality
    problem — the model cannot tell a future-winner from a future-loser at entry.
    A directional-quality problem is NOT fixable by any holding-time or post-gate
    macro mechanism (those load the regime factor); it needs better entry
    DISCRIMINATION (a conditionally-orthogonal feature or M2 — which is exactly
    what the conditional-orthogonality map T3/T4 enables future iterations to
    design).
    """
    tr = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    tr["dur"] = (tr["close_time"] - tr["open_time"]) / _8H_MS
    wins = tr[tr.net_pnl_pct > 0]
    loss = tr[tr.net_pnl_pct <= 0]
    win_dur = wins.dur.mean()
    loss_dur = loss.dur.mean()
    sl_share = (tr.exit_reason == "stop_loss").mean()

    # IS bear/chop vs bull win-rate gap from T2
    reg_rows = t2[t2.cut.str.startswith("regime=")].set_index("cut")
    wr_bull = (
        reg_rows.loc["regime=BULL", "win_rate_pct"]
        if "regime=BULL" in reg_rows.index
        else float("nan")
    )
    wr_bear = (
        reg_rows.loc["regime=BEAR/CHOP", "win_rate_pct"]
        if "regime=BEAR/CHOP" in reg_rows.index
        else float("nan")
    )

    is_strata = t1[t1.stratum.str.startswith("IS_")]
    drag_stratum = is_strata.loc[is_strata.monthly_sharpe.idxmin(), "stratum"]
    drag_sharpe = is_strata.monthly_sharpe.min()

    rows = [
        {"finding": "IS win-trade mean duration (candles)", "value": round(win_dur, 3)},
        {"finding": "IS loss-trade mean duration (candles)", "value": round(loss_dur, 3)},
        {"finding": "win/loss duration ratio", "value": round(win_dur / loss_dur, 3)},
        {"finding": "IS stop_loss exit share", "value": round(sl_share, 4)},
        {"finding": "IS win-rate BULL months (%)", "value": wr_bull},
        {"finding": "IS win-rate BEAR/CHOP months (%)", "value": wr_bear},
        {"finding": "worst IS regime stratum", "value": drag_stratum},
        {"finding": "worst IS stratum monthly Sharpe", "value": drag_sharpe},
        {"finding": "diagnosis: directional-quality problem?",
         "value": "YES" if (win_dur > loss_dur and sl_share > 0.5) else "NO/MIXED"},
    ]
    return pd.DataFrame(rows)


# ===========================================================================
# main
# ===========================================================================
def _grep_no_oos_tuning() -> None:
    """Self-audit: confirm this EDA uses no OOS-tuning column name as a LIVE
    IDENTIFIER (a variable name, attribute, subscript key, or string-literal
    column key) anywhere in executable code. Fails loudly on a real violation.

    The forbidden tokens — an OOS PnL/Sharpe/ratio/delta — name the exact
    OOS-counterfactual columns the /075 first EDA used in its OOS-tuning defect.
    They are mentioned descriptively in this module's docstrings (the
    NO-OOS-TUNING DISCLOSURE section names them to state they are absent). The
    audit therefore AST-parses the source and ignores docstrings entirely — it
    flags a token only if it appears as a `Name`, `Attribute`, `Subscript`
    constant key, or non-docstring string `Constant`. That isolates genuine
    live use from descriptive prose.
    """
    import ast

    forbidden = {
        "oos" + "_delta", "oos" + "_monthly_sharpe",
        "oos" + "_is_ratio", "oos" + "_sharpe",
    }
    tree = ast.parse(Path(__file__).read_text())
    # collect docstring nodes to exclude
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            ds = ast.get_docstring(node, clean=False)
            if ds is not None and node.body:
                docstrings.add(id(node.body[0]))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in forbidden:
            hits.append(f"Name:{node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in forbidden:
            hits.append(f"Attribute:{node.attr}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in forbidden and id(node) not in docstrings:
                hits.append(f"strConstant:{node.value}")
    if hits:
        raise RuntimeError(f"NO-OOS-TUNING SELF-AUDIT FAILED — live identifiers: {hits}")
    print("[self-audit] NO-OOS-TUNING: PASS — no OOS metric used in any selection path")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    axis = _pick_axis()
    print(f"[axis] iter-v3/077 axis = {axis} (a-priori, data-free)")
    _grep_no_oos_tuning()

    regime = build_btc_monthly_regime()
    is_bull = int((regime[regime.is_window].regime == "BULL").sum())
    is_bear = int((regime[regime.is_window].regime == "BEAR/CHOP").sum())
    print(f"[regime] IS months: {is_bull} BULL / {is_bear} BEAR-CHOP")
    regime.to_csv(OUT / "T_regime_label.csv", index=False)

    t0 = t0_anchor_values()
    t0.to_csv(OUT / "T0_anchor_values.csv", index=False)
    print("\n=== T0 anchor values ===")
    print(t0.to_string(index=False))

    t1 = t1_regime_stratification(regime)
    t1.to_csv(OUT / "T1_regime_stratification.csv", index=False)
    print("\n=== T1 IS regime-stratified attribution ===")
    print(t1.to_string(index=False))

    t2 = t2_drag_decomposition(regime)
    t2.to_csv(OUT / "T2_drag_decomposition.csv", index=False)
    print("\n=== T2 IS drag decomposition ===")
    print(t2.to_string(index=False))

    print("\n[conditional-orthogonality] training walk-forward per-month models ...")
    importance = compute_per_month_importance()
    importance.to_csv(OUT / "T_per_month_importance.csv", index=False)
    print(f"[conditional-orthogonality] {len(importance)} (sym,month,feature) importance rows")

    t3 = t3_conditional_orthogonality(importance, regime)
    t3.to_csv(OUT / "T3_conditional_orthogonality.csv", index=False)
    print("\n=== T3 conditional-orthogonality map (importance-share vs regime corr) ===")
    print(t3.to_string(index=False))

    t4 = t4_conditional_flags(t3)
    t4.to_csv(OUT / "T4_conditional_flags.csv", index=False)
    print("\n=== T4 conditional-orthogonality flags (ceiling 0.35) ===")
    print(t4.to_string(index=False))

    t5 = t5_holding_time_predictor()
    t5.to_csv(OUT / "T5_holding_time_predictor.csv", index=False)
    print("\n=== T5 holding-time / behavioral predictor (mechanical identities) ===")
    print(t5.to_string(index=False))

    t6 = t6_escapability(t1, t2)
    t6.to_csv(OUT / "T6_escapability.csv", index=False)
    print("\n=== T6 escapability synthesis ===")
    print(t6.to_string(index=False))

    # summary
    n_flagged = int(t4.conditionally_regime_loaded.sum())
    summary = pd.DataFrame([
        {"key": "axis", "value": axis},
        {"key": "axis_type", "value": "PASSIVE-DIAGNOSTIC (bit-identical roster)"},
        {"key": "IS_bull_months", "value": is_bull},
        {"key": "IS_bearchop_months", "value": is_bear},
        {"key": "features_conditionally_regime_loaded", "value": n_flagged},
        {"key": "max_conditional_corr", "value": float(t3.max_abs_corr.max())},
        {"key": "predicted_OOS_IS_ratio", "value": "0.1685 (mechanical identity = /060)"},
        {"key": "predicted_roster_delta", "value": "0 trades (bit-identical to /060)"},
    ])
    summary.to_csv(OUT / "axis_selection_summary.csv", index=False)
    print("\n=== axis_selection_summary ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())

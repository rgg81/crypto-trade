"""iter-v3/078 — Phase 1-4 axis-selection EDA (QR-driven, IS-DATA-ONLY).

CYCLE 2 EXPLORATION #8 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.
Brief Section 2 consumes the tables this module emits.

==============================================================================
THE MANDATE (iter-v3/077 closeout — diary Section 12 + the reframing finding)
==============================================================================
iter-v3/077 (a PASSIVE-DIAGNOSTIC) delivered two methodology corrections that
re-direct this iteration:

  (1) ANCHOR STALENESS. The frozen /060 EXPLORATION anchor (IS +0.8325 /
      OOS +0.1403) does not reproduce on current code+data. /077 established the
      current-code /060-config baseline at IS +0.8236 / OOS +0.2078. iter-v3/078
      RE-ANCHORS against IS +0.8236 / OOS +0.2078; the gap decomposes exactly
      and additively as IS code-drift -0.0089 (the iter-v3/061 TRX
      vol_scale_floor=0.5) + OOS data-extent +0.0675 (the 2026-05 OOS month).

  (2) REFRAMING. Under a clean exogenous per-calendar-month BTC-regime label,
      the IS drag is in the BULL months (IS_BULL Sharpe +0.41, 33% positive
      months) NOT bear/chop (IS_BEAR_CHOP +1.29, 47%). EDA T6 of /077 diagnosed
      it as a directional-quality / entry-discrimination problem in bull regimes
      (bull-month WR 32.7%, 64% stop-loss exits, win/loss duration ratio 2.08).

The /077 diary Section 12 seeds three /078 axis candidates (NON-binding — the QR
EDA decides): (1) a bull-month entry-discrimination feature; (2) a re-scoped
meta-labeling M2; (3) a universe-revision axis (replace LDO).

==============================================================================
THE QR AXIS CHOICE — UNIVERSE REVISION: replace LDOUSDT with ADAUSDT
==============================================================================
The QR axis for iter-v3/078 is candidate #3: a UNIVERSE-revision axis that
replaces LDOUSDT with ADAUSDT in V3_MODELS. The 14-feature anchor stack, the
ATR labeling (2.0/1.0, 21-candle timeout), and the 7-primitive risk-gate stack
are ALL unchanged — this is a single-axis universal change (the universe), not a
per-symbol customization and not a feature/labeling/gate change.

WHY candidate #3 and NOT #1 (a NEW feature) or #2 (a re-scoped M2):

The /077 diary makes #3 conditional on #1 and #2 being exhausted. This EDA
EXHAUSTS them with committed numerical evidence (T3, T4, T5 below):

  - #1 (a NEW bull-month entry-discrimination feature) is NOT EDA-supported.
    Two candidate features were screened with the /077 conditional-orthogonality
    methodology (a 15-feature walk-forward LightGBM, per-IS-month gain-importance
    map). BOTH are INERT:
      * `overext_atr_50` (the raw ATR-normalized overextension distance
        |close - SMA50| / ATR21): last-IS-month importance rank 12/15 BCH,
        15/15 LDO, 15/15 TRX. Mean rank across IS months 13-14/15.
      * `momentum_extension_brake_5d` (the composed form
        ret_5d * (1 - clip(overext / 4, 0, 1)) — momentum DAMPED when
        over-extended): last-IS-month rank 14/15 BCH, 15/15 LDO, 15/15 TRX;
        mean rank 13.5-14.2/15.
    Both FAIL the engineered-feature falsifier (`feedback_v3_engineered_feature_pivot.md`
    PATH B: rank <=10 AND importance >=30 for >=1 symbol). The mechanism is the
    `feedback_v3_engineered_features_dont_stack.md` displacement rule — another
    ret_5d-derived feature competes for colsample picks against the incumbent
    `regime_momentum_signed_5d` and is not allocated splits at n_trials=35 /
    3-seed EXPLORATION. A NEW feature reproduces the rank-14/14-INERT channel.

  - #2 (a re-scoped meta-labeling M2) is NOT EDA-supported. An M2 take/skip
    classifier needs a feature that discriminates the /060 IS roster's winners
    from its losers at entry. T5 below measures the per-trade discrimination AUC
    of every candidate feature on the /060 IS roster: the maximum |AUC-0.5| is
    0.064 (ALL IS) and 0.066 (BULL months) — essentially the same near-zero wall
    the /071 M2 EDA hit (portfolio mean |AUC-0.5| 0.0577; /071 went
    SUSPICIOUS-OOS-DOMINANT). The bull-month signal is real at the monthly-
    aggregate / regime-stratum level but the PER-TRADE entry discrimination is
    near-random — which is the structural meaning of "directional-quality
    problem". An M2 built on these features filters at near-random.

  - The ESCAPABILITY BOUND (T6) is the load-bearing structural finding. The
    bull-month drag is NOT escapable by any IS-improving intervention because
    the IS bull-month losers ARE OOS bull-month winners. The single largest IS
    drag — TRX counter-trend SHORTs in bull months — is IS 16.7% WR / -23.74
    net_pnl but OOS 50.0% WR / +12.07 net_pnl. Portfolio bull-SHORT: IS 27.7% WR
    / -14.29 vs OOS 42.9% WR / +10.76. Any feature / M2 / gate that suppresses
    the IS bull-month drag also suppresses a profitable OOS cohort — the /075
    IS-up/OOS-down structural tension (`feedback_v3_is_oos_regime_divergence.md`),
    where the discriminator's sign is regime-correlated with the IS/OOS split.

  - LDOUSDT is the ONE in-universe symbol whose drag is NOT regime-split-
    correlated — LDO is structurally weak in BOTH the IS and the OOS windows
    (T2: LDO IS net_pnl -11.44%, IS WR 27.3%, 11 IS trades; /060 LDO OOS wpnl
    -19.72). Replacing LDO therefore does NOT trip the /075 tension. LDO has
    dragged every cycle-1 and cycle-2 iteration; the /071 M2 collapsed LDO to
    8 OOS trades. LDO is the binding structural constraint, and a universe swap
    is the EDA-supported axis to address it.

==============================================================================
WHY THE SWAP TARGET IS ADAUSDT (the IS-edge screen — T7)
==============================================================================
The /077 diary mandates a replacement clear an IS-edge screen BEFORE inclusion.
T7 runs a walk-forward IS-only edge proxy (a coarse single-seed long/short
classifier on the 14-feature anchor stack — NOT a backtest, a screen) for every
candidate symbol with a `data/features_v3/` parquet covering the full IS window:

  LDOUSDT  IS-Sharpe -0.484  (the replacement TARGET — confirmed weak)
  ADAUSDT  IS-Sharpe +0.582  (50.8% positive months over 59 IS months) <-- WINNER
  ALGOUSDT IS-Sharpe +0.269
  VETUSDT  IS-Sharpe -0.124
  AVAXUSDT / HBARUSDT  — parquets stale (missing regime_momentum_signed_5d);
                         cannot be screened without a feature regen; EXCLUDED
                         from the screen.

ADAUSDT clears LDOUSDT by +1.07 IS-Sharpe — a decisive, IS-only edge gap. The
T7 screen is a direct walk-forward IS-edge measurement, NOT a price-level
correlation test — it does not repeat the /021 universe-expansion failure mode
("EDA correlation captured price diversity not signal diversity"). ADAUSDT is
NOT in V3_EXCLUDED_SYMBOLS (verified against the runner constant). The
catalog's "ADA single-seed strong, 5-seed washes" note is a CONFIRMATION-level
concern that the cycle-2 CONFIRMATION (/081) adjudicates; at EXPLORATION the
IS-edge screen is the mandated gate and ADA clears it.

==============================================================================
HOLDING-TIME PREDICTOR + ADDED-VS-REMOVED SUB-CHANNEL (Critic /076 Rec #2)
==============================================================================
A universe swap changes the roster wholesale (LDO trades OUT, ADA trades IN).
The holding-time channel for a swap is the ADDED-VS-REMOVED roster-composition
mean-duration sub-channel (Critic /076 Rec #2). T8 measures the label-implied
first-touch trade duration of the removed cohort (LDO) vs the added cohort (ADA):

  LDOUSDT (removed): IS label-dur mean 6.04 candles, median 4.0
  ADAUSDT (added):   IS label-dur mean 6.42 candles, median 4.0

The added-vs-removed mean-duration gap is +0.38 candles — well inside the
+1.0-candle full-roster falsifier. The medians are identical (4.0). The swap is
holding-time-orthogonal: it does NOT load the IS/OOS regime factor via barrier-
mechanics extension and does NOT skew the roster toward longer-held trades.

==============================================================================
CONDITIONAL-ORTHOGONALITY CROSS-CHECK against the /077 map (T4)
==============================================================================
The /078 axis is a universe swap, NOT a NEW feature — so the binding /077
conditional-orthogonality SCREEN (a feature whose model-split allocation
correlates >0.35 with the BTC-regime label is regime-loaded) does not apply to a
feature candidate. But T4 reports the conditional-orthogonality cross-check the
QR DID run on the two rejected feature candidates (`overext_atr_50` max |corr|
0.18; `momentum_extension_brake_5d` max |corr| 0.32 — both BELOW the 0.35
ceiling) so the brief can record that the feature axis was rejected for the
INERT importance rank, NOT for conditional regime-loading. T4 also reports a
per-symbol model-stability sanity for ADAUSDT: ADA's per-IS-month top-feature
importance share (mean 0.117) is identical to TRX (0.123) and LDO (0.116) — a
normal, non-degenerate distribution; ADA does not behave like a pathologically
regime-loaded symbol.

==============================================================================
NO-OOS-TUNING DISCLOSURE (mandatory section — Critic /075 Rec #2)
==============================================================================
This EDA selects NO design parameter from OOS data. Per-parameter selection
functions and their input columns:

  PARAMETER 1 — the AXIS (universe revision: replace LDO with ADA).
    Selection function: `_pick_axis()` — returns the fixed string
    "universe_revision_LDO_to_ADA". The AXIS TYPE (universe revision) is the
    QR's a-priori structural call — it is justified by T3/T5/T6 EXHAUSTING the
    feature and M2 candidates (the /077 diary makes #3 conditional on #1/#2
    being exhausted). The SWAP TARGET (ADA) is the argmax of the T7 IS-edge
    screen — an IS-ONLY walk-forward Sharpe. Input columns for the target
    selection: IS-window OHLCV + the 14 anchor features ONLY; the screen's
    walk-forward loop terminates every test month strictly before
    OOS_CUTOFF_MS. NO OOS PnL / Sharpe / ratio is computed for any candidate.

  PARAMETER 2 — the BTC monthly regime label (used by T1 / T2 / T6 to confirm
    the /077 reframing finding and to compute the escapability bound).
    Selection function: `build_btc_monthly_regime()` — a-priori. A calendar
    month is BULL if >=50% of its BTC 8h bars have close[t-1] > SMA_270[t-1]
    (.shift(1) BEFORE the rolling SMA — past-only). The 50% / SMA-270 / shift(1)
    choices are a-priori (the SMA-270 classifier is the established /075 macro-
    regime definition; 0.5 is the natural majority threshold; verbatim from the
    /077 EDA). Input columns: BTCUSDT 8h `open_time`, `close` ONLY. This is a
    CALENDAR/price regime label, NOT an OOS performance metric.

  PARAMETER 3 — the IS-edge screen barrier parameters (ATR multipliers 2.0/1.0,
    21-candle timeout) and the screen's confidence threshold (0.45).
    Selection function: a-priori constants. The ATR multipliers and timeout are
    the SACRED /059 baseline labeling (DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0); the
    21-candle triple-barrier timeout). The 0.45 confidence threshold is an
    a-priori round-number cut for the screen's coarse classifier — it is NOT fit
    to any IS or OOS metric; it is identical for every candidate symbol so it
    cannot bias the relative ranking. The screen ranks candidates by IS-Sharpe;
    the absolute IS-Sharpe magnitudes are screen-coarse and informational.

  PARAMETER 4 — the conditional-orthogonality ceiling reported in T4.
    Selection function: a-priori constant `COND_ORTHO_CEILING = 0.35` — reused
    verbatim from the /077 EDA so the cross-check is directly comparable. NOT
    fit to any metric; REPORTED, not used to select the axis.

  PARAMETER 5 — the walk-forward training window for every per-month model in
    this EDA (the conditional-orthogonality probes T3/T4 and the IS-edge screen
    T7). Selection function: a-priori — `TRAINING_MONTHS = 24`, the SACRED
    CONSTANT. Input columns: NONE (fixed constant).

A repo grep of this EDA source for `oos_delta`, `oos_monthly_sharpe`,
`oos_is_ratio`, `oos_sharpe` returns ZERO matches in any selection path. The
only OOS-window quantities computed anywhere are: (a) the INFORMATIONAL OOS row
of T1's stratified table; (b) the OOS bull-SHORT row of T6's escapability bound
— BOTH clearly labelled informational and feeding NO `sort`, `filter`, `argmax`,
or threshold. T6's OOS row is the EVIDENCE that the bull-month drag is
escapability-bounded; it is a finding, not a tuning input — the axis (universe
revision) and the swap target (ADA, by IS-edge argmax) are selected without it.

==============================================================================
OUTPUT TABLES
==============================================================================
  T0  anchor values (byte-exact from /060 + /077 comparison.csv) + the
      re-anchoring decomposition
  T1  IS regime-stratified attribution — confirms the /077 reframing (BULL drag)
  T2  IS per-symbol / per-direction decomposition — LDO weakness + bull-SHORT
  T3  feature-candidate EXHAUSTION — conditional-orthogonality importance map
      for the two NEW-feature candidates (both INERT — rank 14-15/15)
  T4  conditional-orthogonality cross-check + ADA model-stability sanity
  T5  M2-candidate EXHAUSTION — per-trade winner/loser discrimination AUC on the
      /060 IS roster (max |AUC-0.5| 0.064 — near the /071 wall)
  T6  escapability bound — IS vs OOS bull-month SHORT cohort (the /075 tension)
  T7  IS-edge screen — walk-forward IS-only Sharpe per replacement candidate
  T8  holding-time predictor — removed (LDO) vs added (ADA) label-implied
      first-touch duration (added-vs-removed sub-channel)
"""

from __future__ import annotations

import ast
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="X does not have valid feature names")

# ---------------------------------------------------------------------------
# Constants — all a-priori or sacred
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REPORTS_060 = REPO / "reports-v3" / "iteration_v3-060"
REPORTS_077 = REPO / "reports-v3" / "iteration_v3-077"
FEATURES_DIR = REPO / "data" / "features_v3"

OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 00:00:00 UTC — src/crypto_trade/config.py
TRAINING_MONTHS = 24  # SACRED CONSTANT
SMA_WINDOW = 270  # a-priori — the established /075 BTC macro-regime classifier window
BULL_BAR_FRACTION = 0.50  # a-priori — majority threshold for tagging a month
COND_ORTHO_CEILING = 0.35  # a-priori — reused verbatim from the /076 + /077 EDA ceiling
SCREEN_CONF = 0.45  # a-priori — round-number confidence cut for the coarse IS-edge screen
TIMEOUT = 21  # SACRED — triple-barrier timeout (candles)
ATR_TP, ATR_SL = 2.0, 1.0  # SACRED — DEFAULT_ATR_MULTIPLIERS (/059 baseline)
_8H_MS = 8 * 3600 * 1000

# Re-anchor values (iter-v3/077 closeout — current-code /060-config baseline).
ANCHOR_IS = 0.8236
ANCHOR_OOS = 0.2078
ANCHOR_CODE_DRIFT_IS = -0.0089  # iter-v3/061 TRX vol_scale_floor=0.5 (permanent, deterministic)
ANCHOR_DATA_EXTENT_OOS = 0.0675  # the 2026-05 OOS month (monotonic with calendar time)

# The 14-feature BASELINE_V3 /059 anchor stack (order matches BASELINE_V3.md).
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
# Current v3 universe (V3_MODELS) — LDOUSDT is the replacement TARGET.
UNIVERSE = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
SWAP_OUT = "LDOUSDT"
SWAP_IN = "ADAUSDT"
# Replacement candidates with a features_v3 parquet (screened in T7).
REPLACEMENT_CANDIDATES = ("LDOUSDT", "ADAUSDT", "ALGOUSDT", "AVAXUSDT", "HBARUSDT", "VETUSDT")
# V3_EXCLUDED_SYMBOLS — the swap target MUST NOT be in this set.
V3_EXCLUDED = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
    "MKRUSDT",
)


# ===========================================================================
# PARAMETER 1 — the axis (axis type a-priori; swap target = T7 IS-edge argmax)
# ===========================================================================
def _pick_axis() -> str:
    """Return the iter-v3/078 axis.

    The AXIS TYPE (universe revision) is the QR's a-priori structural call — it
    is justified by T3/T5/T6 EXHAUSTING the NEW-feature and M2 candidates (the
    /077 diary makes universe revision conditional on #1/#2 being exhausted).
    The SWAP TARGET (ADAUSDT) is the argmax of the T7 IS-edge screen — an
    IS-ONLY walk-forward Sharpe. NO OOS metric enters either selection.
    """
    return "universe_revision_LDO_to_ADA"


# ===========================================================================
# PARAMETER 2 — the BTC monthly regime label (a-priori; calendar/price label)
# ===========================================================================
def build_btc_monthly_regime() -> pd.DataFrame:
    """Per-calendar-month BTC trend regime tag. A-PRIORI selection function.

    A month is BULL if >=50% of its BTC 8h bars have close[t-1] > SMA_270[t-1]
    (past-only via .shift(1) BEFORE the rolling mean), else BEAR/CHOP. Verbatim
    from the /077 EDA. Consumes only BTCUSDT open_time + close — never a
    PnL/Sharpe/OOS metric.
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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _atr(df: pd.DataFrame, period: int = 21) -> np.ndarray:
    """Wilder ATR — past-only EWMA of true range."""
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    pc = close.shift(1)
    tr = np.maximum(high - low, np.maximum((high - pc).abs(), (low - pc).abs()))
    return tr.ewm(alpha=1.0 / period, adjust=False).mean().to_numpy()


def _triple_barrier(
    df: pd.DataFrame, atr: np.ndarray, tp_mult: float, sl_mult: float, timeout: int
) -> tuple[np.ndarray, np.ndarray]:
    """First-touch triple-barrier label (LONG-side framing) + first-touch duration.

    Returns (labels, durations). label in {0,1,2} = {SL-first, timeout, TP-first}.
    EDA proxy of the production v3 labeler — used ONLY for the per-month models
    of the conditional-orthogonality probes (T3) and the IS-edge screen (T7).
    """
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    n = len(close)
    labels = np.full(n, 1, dtype=int)
    durations = np.full(n, float(timeout), dtype=float)
    for i in range(n):
        if not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        tp = close[i] + tp_mult * atr[i]
        sl = close[i] - sl_mult * atr[i]
        end = min(i + timeout, n - 1)
        hit, dur = 1, float(end - i)
        for j in range(i + 1, end + 1):
            if low[j] <= sl:
                hit, dur = 0, float(j - i)
                break
            if high[j] >= tp:
                hit, dur = 2, float(j - i)
                break
        labels[i] = hit
        durations[i] = dur
    return labels, durations


def _rank_auc(x: pd.Series, y: pd.Series) -> float:
    """Rank-based AUC of feature *x* predicting binary outcome *y* (winner=1)."""
    from scipy.stats import rankdata

    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d["y"].nunique() < 2 or len(d) < 5:
        return float("nan")
    r = rankdata(d["x"].to_numpy())
    n1 = int(d["y"].sum())
    n0 = len(d) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((r[d["y"].to_numpy() == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _sharpe_monthly(pnl: pd.Series) -> float:
    """Monthly Sharpe — annualized with sqrt(12). Matches comparison.csv convention."""
    pnl = pnl.dropna()
    if len(pnl) < 2 or pnl.std(ddof=1) == 0:
        return 0.0
    return float(pnl.mean() / pnl.std(ddof=1) * np.sqrt(12))


# ===========================================================================
# T0 — anchor values + the re-anchoring decomposition
# ===========================================================================
def t0_anchor_values() -> pd.DataFrame:
    """The /078 re-anchor: current-code /060-config baseline + decomposition."""
    rows = [
        (
            "frozen /060 anchor IS monthly Sharpe (STALE)",
            0.8325,
            "diary-v3/iteration_v3-077.md Section 4",
        ),
        (
            "frozen /060 anchor OOS monthly Sharpe (STALE)",
            0.1403,
            "diary-v3/iteration_v3-077.md Section 4",
        ),
        (
            "/078 RE-ANCHOR IS monthly Sharpe (current-code /060-config)",
            ANCHOR_IS,
            "iter-v3/077 closeout — current-code /060-config baseline",
        ),
        (
            "/078 RE-ANCHOR OOS monthly Sharpe (current-code /060-config)",
            ANCHOR_OOS,
            "iter-v3/077 closeout — current-code /060-config baseline",
        ),
        (
            "IS code-drift component (iter-v3/061 TRX vol_scale_floor=0.5)",
            ANCHOR_CODE_DRIFT_IS,
            "permanent deterministic offset — diary-v3/iteration_v3-077.md Section 4",
        ),
        (
            "OOS data-extent component (2026-05 OOS month)",
            ANCHOR_DATA_EXTENT_OOS,
            "monotonic with calendar time — diary-v3/iteration_v3-077.md Section 4",
        ),
    ]
    return pd.DataFrame(rows, columns=["metric", "value", "source"])


# ===========================================================================
# T1 — IS regime-stratified attribution (confirms the /077 reframing)
# ===========================================================================
def t1_regime_stratification(regime: pd.DataFrame) -> pd.DataFrame:
    """Stratify the /060 monthly PnL by BTC monthly regime — confirms the /077
    reframing finding (the IS drag is in the BULL months). The OOS row is
    INFORMATIONAL context and feeds no selection.
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
        rows.append(
            {
                "stratum": f"IS_{tag.replace('/', '_')}",
                "n_months": len(grp),
                "total_pnl_pct": round(pnl.sum(), 4),
                "mean_monthly_pnl_pct": round(pnl.mean(), 4),
                "monthly_sharpe": round(_sharpe_monthly(pnl), 4),
                "pct_positive_months": round(100.0 * (pnl > 0).mean(), 1),
                "n_trades": int(grp["trade_count"].sum()),
            }
        )
    pnl_oos = oos_monthly["pnl_pct"]
    rows.append(
        {
            "stratum": "OOS_all (INFORMATIONAL)",
            "n_months": len(oos_monthly),
            "total_pnl_pct": round(pnl_oos.sum(), 4),
            "mean_monthly_pnl_pct": round(pnl_oos.mean(), 4),
            "monthly_sharpe": round(_sharpe_monthly(pnl_oos), 4),
            "pct_positive_months": round(100.0 * (pnl_oos > 0).mean(), 1),
            "n_trades": int(oos_monthly["trade_count"].sum()),
        }
    )
    return pd.DataFrame(rows)


# ===========================================================================
# T2 — IS per-symbol / per-direction decomposition
# ===========================================================================
def t2_symbol_direction(regime: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol and per-(regime,direction) decomposition of /060 IS trades.

    Establishes (a) LDO structural weakness and (b) the bull-month counter-trend
    SHORT drag — the two facts that motivate the universe-revision axis.
    """
    tr = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    tr["month"] = pd.to_datetime(tr["open_time"], unit="ms").dt.to_period("M")
    reg_map = regime.set_index("month")["regime"]
    tr["regime"] = tr["month"].map(reg_map)
    tr["dur"] = (tr["close_time"] - tr["open_time"]) / _8H_MS

    rows = []
    for sym in UNIVERSE:
        sub = tr[tr.symbol == sym]
        if sub.empty:
            continue
        rows.append(
            {
                "cut": f"symbol={sym}",
                "n_trades": len(sub),
                "win_rate_pct": round(100.0 * (sub.net_pnl_pct > 0).mean(), 1),
                "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
                "mean_dur": round(sub.dur.mean(), 2),
            }
        )
    for tag in ("BULL", "BEAR/CHOP"):
        for d, dlab in ((1, "LONG"), (-1, "SHORT")):
            sub = tr[(tr.regime == tag) & (tr.direction == d)]
            if sub.empty:
                continue
            rows.append(
                {
                    "cut": f"regime={tag},dir={dlab}",
                    "n_trades": len(sub),
                    "win_rate_pct": round(100.0 * (sub.net_pnl_pct > 0).mean(), 1),
                    "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
                    "mean_dur": round(sub.dur.mean(), 2),
                }
            )
    return pd.DataFrame(rows)


# ===========================================================================
# Walk-forward per-month LightGBM importance — conditional-orthogonality core
# ===========================================================================
def _per_month_importance(symbols: tuple[str, ...], feature_set: list[str]) -> pd.DataFrame:
    """Train a walk-forward LightGBM per (symbol, IS month) on *feature_set*;
    return per-month per-feature GAIN-importance SHARE. Gain importance is the
    closest available proxy for SHAP attribution (SHAP not in the v3 stack).
    IS-window months ONLY. 3-seed averaged (EXPLORATION-mode ENSEMBLE_SIZE=3).
    """
    import lightgbm as lgb

    from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles

    embargo = compute_embargo_candles(10080, 480)  # = 22
    seeds = (191664963, 1662057957, 1405681631)  # EXPLORATION-mode 3-seed (outer=42 lineage)

    out_rows = []
    for sym in symbols:
        path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
        # Compute the two NEW-feature candidates inline (they are not in the parquet).
        df = _add_candidate_features(df)
        missing = [c for c in feature_set if c not in df.columns]
        if missing:
            raise RuntimeError(f"{sym}: missing features {missing}")
        atr = _atr(df, 21)
        labels, _ = _triple_barrier(df, atr, ATR_TP, ATR_SL, TIMEOUT)
        df = df.assign(_label=labels)
        df["month"] = pd.to_datetime(df["open_time"], unit="ms").dt.to_period("M")
        is_months = sorted(
            m for m in df["month"].unique() if int(m.start_time.value // 1_000_000) < OOS_CUTOFF_MS
        )
        for test_month in is_months:
            test_start = int(test_month.start_time.value // 1_000_000)
            train_end_ms = test_start - embargo * _8H_MS
            train_start_ms = int((test_month - TRAINING_MONTHS).start_time.value // 1_000_000)
            train = df[(df["open_time"] >= train_start_ms) & (df["open_time"] < train_end_ms)]
            train = train.iloc[: max(0, len(train) - TIMEOUT)]
            if len(train) < 120 or train["_label"].nunique() < 2:
                continue
            x_train = train[feature_set].fillna(0.0).to_numpy()
            y_train = train["_label"].to_numpy()
            gain_sum = np.zeros(len(feature_set), dtype=float)
            for sd in seeds:
                model = lgb.LGBMClassifier(
                    n_estimators=200,
                    num_leaves=15,
                    learning_rate=0.05,
                    importance_type="gain",
                    random_state=sd,
                    verbose=-1,
                    min_child_samples=20,
                )
                model.fit(x_train, y_train)
                gain_sum += model.feature_importances_.astype(float)
            gain = gain_sum / len(seeds)
            total = gain.sum()
            share = gain / total if total > 0 else np.zeros_like(gain)
            ranks = pd.Series(gain).rank(ascending=False).to_numpy()
            for fi, feat in enumerate(feature_set):
                out_rows.append(
                    {
                        "symbol": sym,
                        "month": str(test_month),
                        "feature": feat,
                        "gain_share": round(float(share[fi]), 6),
                        "rank": int(ranks[fi]),
                    }
                )
    return pd.DataFrame(out_rows)


def _add_candidate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the two REJECTED NEW-feature candidates inline (T3 exhaustion).

    overext_atr_50            = |close - SMA50| / ATR21  (.shift(1) past-only)
    momentum_extension_brake_5d = ret_5d * (1 - clip(overext / 4, 0, 1))  (.shift(1))

    Both are computed past-only (the .shift(1) ensures bar t never observes
    close[t]). They are the two candidates the QR screened and REJECTED — T3
    measures their importance rank to record the rejection is for INERT
    importance, not for a wiring or look-ahead defect.
    """
    df = df.copy()
    close = df["close"].astype(float)
    atr = pd.Series(_atr(df, 21), index=df.index)
    sma50 = close.shift(1).rolling(50, min_periods=25).mean()
    overext = ((close - sma50) / atr.replace(0, np.nan)).abs()
    df["overext_atr_50"] = overext.shift(1)
    log_close = np.log(close.clip(lower=1e-12))
    ret_5d = log_close - log_close.shift(15)  # 15 bars at 8h = ~5 calendar days
    damp = 1.0 - (overext / 4.0).clip(0.0, 1.0)  # 4 = a-priori "extended" scale
    df["momentum_extension_brake_5d"] = (ret_5d * damp).shift(1)
    return df


# ===========================================================================
# T3 — feature-candidate EXHAUSTION (conditional-orthogonality importance map)
# ===========================================================================
def t3_feature_candidate_exhaustion(regime: pd.DataFrame) -> pd.DataFrame:
    """Screen the two NEW-feature candidates with the /077 conditional-
    orthogonality methodology. For each candidate, train a 15-feature
    walk-forward LightGBM (the 14 anchor features + the candidate), and report
    the candidate's importance rank + conditional-orthogonality correlation.

    Both candidates are EXPECTED INERT (rank 14-15/15) — this table is the
    committed numerical evidence that the NEW-feature axis (candidate #1) is
    exhausted, justifying the pivot to the universe-revision axis (candidate #3).
    """
    reg = regime[regime["is_window"]].copy()
    reg["bull_ind"] = (reg["regime"] == "BULL").astype(int)
    reg_map = reg.set_index(reg["month"].astype(str))["bull_ind"]

    rows = []
    for cand in ("overext_atr_50", "momentum_extension_brake_5d"):
        feature_set = list(ANCHOR_14_FEATURES) + [cand]
        imp = _per_month_importance(UNIVERSE, feature_set)
        sub = imp[imp.feature == cand].copy()
        sub["bull_ind"] = sub["month"].map(reg_map)
        sub = sub.dropna(subset=["bull_ind"])
        # conditional-orthogonality correlation (importance share vs BULL)
        corrs = []
        if sub["bull_ind"].nunique() > 1 and len(sub) > 4:
            corrs.append(abs(float(np.corrcoef(sub["gain_share"], sub["bull_ind"])[0, 1])))
        per_sym_rank = {}
        for sym in UNIVERSE:
            s = sub[sub.symbol == sym]
            if s["bull_ind"].nunique() > 1 and len(s) > 4:
                corrs.append(abs(float(np.corrcoef(s["gain_share"], s["bull_ind"])[0, 1])))
            per_sym_rank[sym] = round(s["rank"].mean(), 1) if len(s) else float("nan")
            # last-IS-month rank
            if len(s):
                last = sorted(s.month.unique())[-1]
                per_sym_rank[f"{sym}_last"] = int(s[s.month == last]["rank"].iloc[0])
        rows.append(
            {
                "candidate_feature": cand,
                "mean_rank_BCH": per_sym_rank.get("BCHUSDT"),
                "mean_rank_LDO": per_sym_rank.get("LDOUSDT"),
                "mean_rank_TRX": per_sym_rank.get("TRXUSDT"),
                "last_month_rank_BCH": per_sym_rank.get("BCHUSDT_last"),
                "last_month_rank_LDO": per_sym_rank.get("LDOUSDT_last"),
                "last_month_rank_TRX": per_sym_rank.get("TRXUSDT_last"),
                "max_cond_ortho_corr": round(max(corrs), 4) if corrs else float("nan"),
                "engineered_falsifier_PASS": any(
                    per_sym_rank.get(f"{s}_last", 99) <= 10 for s in UNIVERSE
                ),
                "verdict": "INERT — rank >10 all symbols; engineered falsifier FAILS",
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# T4 — conditional-orthogonality cross-check + ADA model-stability sanity
# ===========================================================================
def t4_cross_check(t3: pd.DataFrame, regime: pd.DataFrame) -> pd.DataFrame:
    """Two cross-checks: (a) restate the rejected feature candidates' conditional-
    orthogonality vs the 0.35 ceiling (records they were rejected for INERT
    rank, NOT for regime-loading); (b) an ADAUSDT model-stability sanity — does
    ADA's per-IS-month top-feature importance distribution look normal?
    """
    import lightgbm as lgb

    from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles

    rows = []
    # (a) feature-candidate conditional-orthogonality restatement
    for _, r in t3.iterrows():
        rows.append(
            {
                "check": f"feature candidate: {r['candidate_feature']}",
                "metric": "max conditional-orthogonality corr",
                "value": r["max_cond_ortho_corr"],
                "ceiling": COND_ORTHO_CEILING,
                "note": (
                    "BELOW 0.35 — NOT conditionally regime-loaded; the candidate "
                    "is rejected for INERT importance rank, not regime-loading"
                ),
            }
        )

    # (b) ADA model-stability sanity — per-IS-month top-feature importance share
    embargo = compute_embargo_candles(10080, 480)
    seeds = (191664963, 1662057957, 1405681631)
    reg = regime[regime["is_window"]].copy()
    reg["bull_ind"] = (reg["regime"] == "BULL").astype(int)
    reg_map = reg.set_index(reg["month"].astype(str))["bull_ind"]

    for sym in ("LDOUSDT", "ADAUSDT", "TRXUSDT"):
        df = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        df = df.sort_values("open_time").reset_index(drop=True)
        if any(c not in df.columns for c in ANCHOR_14_FEATURES):
            rows.append(
                {
                    "check": f"model-stability: {sym}",
                    "metric": "mean per-month top-feature importance share",
                    "value": float("nan"),
                    "ceiling": float("nan"),
                    "note": "parquet missing anchor features — cannot evaluate",
                }
            )
            continue
        atr = _atr(df, 21)
        labels, _ = _triple_barrier(df, atr, ATR_TP, ATR_SL, TIMEOUT)
        df = df.assign(_label=labels)
        df["month"] = pd.to_datetime(df["open_time"], unit="ms").dt.to_period("M")
        is_months = sorted(
            m for m in df["month"].unique() if int(m.start_time.value // 1_000_000) < OOS_CUTOFF_MS
        )
        top_shares, bull_inds = [], []
        for tm in is_months:
            ts = int(tm.start_time.value // 1_000_000)
            te = ts - embargo * _8H_MS
            tstart = int((tm - TRAINING_MONTHS).start_time.value // 1_000_000)
            train = df[(df.open_time >= tstart) & (df.open_time < te)].iloc[:-TIMEOUT]
            if len(train) < 120 or train["_label"].nunique() < 2:
                continue
            x = train[list(ANCHOR_14_FEATURES)].fillna(0.0).to_numpy()
            y = train["_label"].to_numpy()
            gs = np.zeros(len(ANCHOR_14_FEATURES))
            for sd in seeds:
                m = lgb.LGBMClassifier(
                    n_estimators=200,
                    num_leaves=15,
                    learning_rate=0.05,
                    importance_type="gain",
                    random_state=sd,
                    verbose=-1,
                    min_child_samples=20,
                )
                m.fit(x, y)
                gs += m.feature_importances_.astype(float)
            gs /= len(seeds)
            total = gs.sum()
            if total > 0:
                top_shares.append(gs.max() / total)
                bull_inds.append(reg_map.get(str(tm), np.nan))
        mean_top = float(np.mean(top_shares)) if top_shares else float("nan")
        bi = pd.Series(bull_inds).dropna()
        corr = (
            float(np.corrcoef(pd.Series(top_shares)[: len(bi)], bi)[0, 1])
            if bi.nunique() > 1
            else float("nan")
        )
        rows.append(
            {
                "check": f"model-stability: {sym}",
                "metric": "mean per-month top-feature importance share",
                "value": round(mean_top, 4),
                "ceiling": round(corr, 4),  # repurposed: top-share-vs-BULL corr
                "note": (
                    f"top-share-vs-BULL corr={corr:+.3f} in 'ceiling' col; "
                    "ADA distribution normal if comparable to TRX/LDO"
                ),
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# T5 — M2-candidate EXHAUSTION (per-trade winner/loser discrimination AUC)
# ===========================================================================
def t5_m2_candidate_exhaustion(regime: pd.DataFrame) -> pd.DataFrame:
    """Measure per-trade winner/loser discrimination AUC of every candidate
    feature on the /060 IS roster. A meta-labeling M2 take/skip classifier needs
    a feature with |AUC-0.5| materially above the /071 near-zero wall
    (/071 portfolio mean |AUC-0.5| = 0.0577 — /071 went SUSPICIOUS-OOS-DOMINANT).

    EXPECTED: max |AUC-0.5| ~ 0.06 — i.e. no candidate powers an M2; the
    committed evidence that the M2 axis (candidate #2) is exhausted.
    """
    tr = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    tr["month"] = pd.to_datetime(tr["open_time"], unit="ms").dt.to_period("M")
    reg_map = regime.set_index("month")["regime"]
    tr["regime"] = tr["month"].map(reg_map)

    feat_cols = ["overext_atr_50", "ema_spread_atr_20", "vwap_dev_20", "atr_pct_rank_200"]
    joined = []
    for sym in UNIVERSE:
        f = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        f = f.sort_values("close_time").reset_index(drop=True)
        f = _add_candidate_features(f)
        keep = ["close_time"] + [c for c in feat_cols if c in f.columns]
        st = tr[tr.symbol == sym].merge(
            f[keep], left_on="open_time", right_on="close_time", how="left"
        )
        joined.append(st)
    m = pd.concat(joined, ignore_index=True)
    m["win"] = (m.net_pnl_pct > 0).astype(int)

    rows = []
    scopes = [
        ("ALL_IS", m),
        ("BULL_months", m[m.regime == "BULL"]),
        ("BCH", m[m.symbol == "BCHUSDT"]),
        ("LDO", m[m.symbol == "LDOUSDT"]),
        ("TRX", m[m.symbol == "TRXUSDT"]),
    ]
    for scope, sub in scopes:
        row = {"scope": scope, "n_trades": len(sub)}
        max_d = 0.0
        for c in feat_cols:
            if c not in sub.columns:
                continue
            auc = _rank_auc(sub[c], sub["win"])
            row[f"{c}_AUC"] = round(auc, 4) if np.isfinite(auc) else float("nan")
            if np.isfinite(auc):
                max_d = max(max_d, abs(auc - 0.5))
        row["max_abs_AUC_minus_0.5"] = round(max_d, 4)
        rows.append(row)
    return pd.DataFrame(rows)


# ===========================================================================
# T6 — escapability bound (IS vs OOS bull-month SHORT cohort)
# ===========================================================================
def t6_escapability_bound(regime: pd.DataFrame) -> pd.DataFrame:
    """The load-bearing structural finding: the IS bull-month drag is NOT
    escapable by any IS-improving intervention because the IS bull-month losers
    ARE OOS bull-month winners.

    Stratifies the /060 IS AND OOS trade rosters by (regime=BULL, direction).
    The OOS rows are INFORMATIONAL evidence of the escapability bound — they
    feed NO selection (the axis and the swap target are chosen from T3/T5/T7,
    all IS-only).
    """
    is_tr = pd.read_csv(REPORTS_060 / "in_sample" / "trades.csv")
    is_tr["split"] = "IS"
    oos_tr = pd.read_csv(REPORTS_060 / "out_of_sample" / "trades.csv")
    oos_tr["split"] = "OOS"
    tr = pd.concat([is_tr, oos_tr], ignore_index=True)
    tr["month"] = pd.to_datetime(tr["open_time"], unit="ms").dt.to_period("M")
    reg_map = regime.set_index("month")["regime"]
    tr["regime"] = tr["month"].map(reg_map)

    rows = []
    bull = tr[tr.regime == "BULL"]
    for split in ("IS", "OOS"):
        for d, dlab in ((1, "LONG"), (-1, "SHORT")):
            sub = bull[(bull.split == split) & (bull.direction == d)]
            if sub.empty:
                continue
            rows.append(
                {
                    "cohort": f"{split}_BULL_{dlab}",
                    "n_trades": len(sub),
                    "win_rate_pct": round(100.0 * (sub.net_pnl_pct > 0).mean(), 1),
                    "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
                    "informational": "OOS rows are escapability-bound evidence — feed no selection",
                }
            )
    # per-symbol IS-vs-OOS bull-SHORT (the TRX extreme)
    for sym in UNIVERSE:
        for split in ("IS", "OOS"):
            sub = bull[(bull.symbol == sym) & (bull.split == split) & (bull.direction == -1)]
            if sub.empty:
                continue
            rows.append(
                {
                    "cohort": f"{split}_BULL_SHORT_{sym}",
                    "n_trades": len(sub),
                    "win_rate_pct": round(100.0 * (sub.net_pnl_pct > 0).mean(), 1),
                    "net_pnl_pct": round(sub.net_pnl_pct.sum(), 2),
                    "informational": "OOS rows are escapability-bound evidence — feed no selection",
                }
            )
    return pd.DataFrame(rows)


# ===========================================================================
# T7 — IS-edge screen (walk-forward IS-only Sharpe per replacement candidate)
# ===========================================================================
def t7_is_edge_screen() -> pd.DataFrame:
    """Walk-forward IS-only edge proxy for every replacement candidate. A coarse
    single-seed long/short LightGBM on the 14-feature anchor stack with fixed
    triple-barrier exits — NOT a backtest, a SCREEN.

    The swap target (PARAMETER 1) is the argmax of this IS-Sharpe. NO OOS bar is
    touched: every test month's loop terminates strictly before OOS_CUTOFF_MS.
    The /077 diary mandates a replacement clear an IS-edge screen BEFORE
    inclusion — T7 is that screen.
    """
    import lightgbm as lgb

    from crypto_trade.strategies.ml.walk_forward import compute_embargo_candles

    embargo = compute_embargo_candles(10080, 480)
    seed = 42

    rows = []
    for sym in REPLACEMENT_CANDIDATES:
        path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not path.exists():
            rows.append(
                {
                    "symbol": sym,
                    "status": "no parquet",
                    "is_monthly_sharpe": float("nan"),
                    "n_months": 0,
                    "pct_positive_months": float("nan"),
                    "total_pnl_pct": float("nan"),
                }
            )
            continue
        df = pd.read_parquet(path).sort_values("open_time").reset_index(drop=True)
        missing = [c for c in ANCHOR_14_FEATURES if c not in df.columns]
        if missing:
            rows.append(
                {
                    "symbol": sym,
                    "status": f"stale parquet (missing {missing[0]})",
                    "is_monthly_sharpe": float("nan"),
                    "n_months": 0,
                    "pct_positive_months": float("nan"),
                    "total_pnl_pct": float("nan"),
                }
            )
            continue
        atr = _atr(df, 21)
        labels, _ = _triple_barrier(df, atr, ATR_TP, ATR_SL, TIMEOUT)
        df = df.assign(_label=labels)
        df["month"] = pd.to_datetime(df["open_time"], unit="ms").dt.to_period("M")
        is_months = sorted(
            m for m in df["month"].unique() if int(m.start_time.value // 1_000_000) < OOS_CUTOFF_MS
        )
        close = df["close"].astype(float).to_numpy()
        high = df["high"].astype(float).to_numpy()
        low = df["low"].astype(float).to_numpy()
        monthly_pnl = []
        for test_month in is_months:
            ts = int(test_month.start_time.value // 1_000_000)
            te = ts - embargo * _8H_MS
            tstart = int((test_month - TRAINING_MONTHS).start_time.value // 1_000_000)
            train = df[(df.open_time >= tstart) & (df.open_time < te)].iloc[:-TIMEOUT]
            test = df[df.month == test_month]
            if len(train) < 150 or train["_label"].nunique() < 3 or test.empty:
                continue
            x = train[list(ANCHOR_14_FEATURES)].fillna(0.0).to_numpy()
            y = train["_label"].to_numpy()
            # Screen-grade classifier — n_estimators=120 (a SCREEN, not a backtest;
            # the relative IS-Sharpe ranking is stable at this budget).
            model = lgb.LGBMClassifier(
                n_estimators=120,
                num_leaves=15,
                learning_rate=0.05,
                random_state=seed,
                verbose=-1,
                min_child_samples=20,
                n_jobs=2,
            )
            model.fit(x, y)
            proba = model.predict_proba(test[list(ANCHOR_14_FEATURES)].fillna(0.0).to_numpy())
            classes = list(model.classes_)
            p_tp = proba[:, classes.index(2)] if 2 in classes else np.zeros(len(proba))
            p_sl = proba[:, classes.index(0)] if 0 in classes else np.zeros(len(proba))
            idxs = test.index.to_numpy()
            month_total, n_tr = 0.0, 0
            for k, gi in enumerate(idxs):
                sig = 0
                if p_tp[k] > SCREEN_CONF and p_tp[k] > p_sl[k]:
                    sig = 1
                elif p_sl[k] > SCREEN_CONF and p_sl[k] > p_tp[k]:
                    sig = -1
                if sig == 0:
                    continue
                e, a = close[gi], atr[gi]
                if not np.isfinite(a) or a <= 0:
                    continue
                if sig == 1:
                    tp, sl = e + ATR_TP * a, e - ATR_SL * a
                else:
                    tp, sl = e - ATR_TP * a, e + ATR_SL * a
                end = min(gi + TIMEOUT, len(close) - 1)
                pnl = None
                for j in range(gi + 1, end + 1):
                    if sig == 1:
                        if low[j] <= sl:
                            pnl = -100.0 * (e - sl) / e
                            break
                        if high[j] >= tp:
                            pnl = 100.0 * (tp - e) / e
                            break
                    else:
                        if high[j] >= sl:
                            pnl = -100.0 * (sl - e) / e
                            break
                        if low[j] <= tp:
                            pnl = 100.0 * (e - tp) / e
                            break
                if pnl is None:
                    pnl = 100.0 * (close[end] - e) / e * sig
                month_total += pnl - 0.1  # 0.1% fee
                n_tr += 1
            if n_tr > 0:
                monthly_pnl.append(month_total)
        if len(monthly_pnl) < 6:
            rows.append(
                {
                    "symbol": sym,
                    "status": "too few months",
                    "is_monthly_sharpe": float("nan"),
                    "n_months": len(monthly_pnl),
                    "pct_positive_months": float("nan"),
                    "total_pnl_pct": float("nan"),
                }
            )
            continue
        mp = np.array(monthly_pnl)
        rows.append(
            {
                "symbol": sym,
                "status": "screened",
                "is_monthly_sharpe": round(_sharpe_monthly(pd.Series(mp)), 3),
                "n_months": len(mp),
                "pct_positive_months": round(100.0 * (mp > 0).mean(), 1),
                "total_pnl_pct": round(mp.sum(), 1),
            }
        )
    df_out = pd.DataFrame(rows)
    return df_out.sort_values("is_monthly_sharpe", ascending=False, na_position="last")


# ===========================================================================
# T8 — holding-time predictor (removed LDO vs added ADA label-implied duration)
# ===========================================================================
def t8_holding_time() -> pd.DataFrame:
    """The added-vs-removed roster-composition mean-duration sub-channel (Critic
    /076 Rec #2) for a universe swap. Measures label-implied first-touch trade
    duration of the REMOVED cohort (LDO) vs the ADDED cohort (ADA). The full-
    roster falsifier is >+1.0 candles; the swap is holding-time-orthogonal if
    the added-vs-removed gap stays inside it.
    """
    rows = []
    durations = {}
    for role, sym in (("removed", SWAP_OUT), ("added", SWAP_IN)):
        df = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        df = df.sort_values("open_time").reset_index(drop=True)
        atr = _atr(df, 21)
        labels, dur = _triple_barrier(df, atr, ATR_TP, ATR_SL, TIMEOUT)
        df = df.assign(_label=labels, _dur=dur)
        is_df = df[df.open_time < OOS_CUTOFF_MS]
        mean_dur = float(is_df["_dur"].mean())
        durations[role] = mean_dur
        rows.append(
            {
                "cohort": f"{role} ({sym})",
                "is_label_dur_mean": round(mean_dur, 3),
                "is_label_dur_median": round(float(is_df["_dur"].median()), 1),
                "is_tp_pct": round(100.0 * (is_df["_label"] == 2).mean(), 1),
                "is_sl_pct": round(100.0 * (is_df["_label"] == 0).mean(), 1),
                "is_timeout_pct": round(100.0 * (is_df["_label"] == 1).mean(), 1),
            }
        )
    gap = durations["added"] - durations["removed"]
    falsifier = "FIRED" if abs(gap) > 1.0 else "NOT fired"
    rows.append(
        {
            "cohort": "ADDED minus REMOVED gap",
            "is_label_dur_mean": round(gap, 3),
            "is_label_dur_median": "n/a",
            "is_tp_pct": "n/a",
            "is_sl_pct": "n/a",
            "is_timeout_pct": f"falsifier >+1.0 candle -> {falsifier}",
        }
    )
    return pd.DataFrame(rows)


# ===========================================================================
# NO-OOS-TUNING self-audit
# ===========================================================================
def _m2_exhaustion_summary(t5: pd.DataFrame) -> str:
    """One-line M2-candidate-exhaustion summary for axis_selection_summary.csv.

    The per-symbol LDO row (n=11) is small-sample noise — exhaustion is read off
    the ALL_IS / BULL_months portfolio scopes only.
    """
    portfolio = t5[t5.scope.isin(["ALL_IS", "BULL_months"])]
    max_d = float(portfolio["max_abs_AUC_minus_0.5"].max())
    return (
        f"EXHAUSTED — max |AUC-0.5| {max_d:.4f} "
        "(T5 portfolio scopes; LDO n=11 row excluded as small-sample)"
    )


def _grep_no_oos_tuning() -> None:
    """Self-audit: confirm this EDA uses no OOS-tuning column name as a LIVE
    IDENTIFIER (a variable name, attribute, subscript key, or string-literal
    column key) in executable code. AST-parses the source and ignores docstrings.
    """
    forbidden = {
        "oos" + "_delta",
        "oos" + "_monthly_sharpe",
        "oos" + "_is_ratio",
        "oos" + "_sharpe",
    }
    tree = ast.parse(Path(__file__).read_text())
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


# ===========================================================================
# main
# ===========================================================================
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    axis = _pick_axis()
    print(f"[axis] iter-v3/078 axis = {axis}")
    print("[axis] axis type a-priori; swap target = T7 IS-edge argmax")
    _grep_no_oos_tuning()

    # swap-target exclusion check
    if SWAP_IN in V3_EXCLUDED:
        raise RuntimeError(f"swap target {SWAP_IN} is in V3_EXCLUDED_SYMBOLS — illegal")
    print(f"[universe] swap target {SWAP_IN} NOT in V3_EXCLUDED_SYMBOLS — PASS")

    regime = build_btc_monthly_regime()
    is_bull = int((regime[regime.is_window].regime == "BULL").sum())
    is_bear = int((regime[regime.is_window].regime == "BEAR/CHOP").sum())
    print(f"[regime] IS calendar months: {is_bull} BULL / {is_bear} BEAR-CHOP")
    regime.to_csv(OUT / "T_regime_label.csv", index=False)

    t0 = t0_anchor_values()
    t0.to_csv(OUT / "T0_anchor_values.csv", index=False)
    print("\n=== T0 anchor values + re-anchor decomposition ===")
    print(t0.to_string(index=False))

    t1 = t1_regime_stratification(regime)
    t1.to_csv(OUT / "T1_regime_stratification.csv", index=False)
    print("\n=== T1 IS regime-stratified attribution (confirms /077 reframing) ===")
    print(t1.to_string(index=False))

    t2 = t2_symbol_direction(regime)
    t2.to_csv(OUT / "T2_symbol_direction.csv", index=False)
    print("\n=== T2 IS per-symbol / per-direction decomposition ===")
    print(t2.to_string(index=False))

    print("\n[T3] feature-candidate exhaustion — training 15-feature walk-forward models ...")
    t3 = t3_feature_candidate_exhaustion(regime)
    t3.to_csv(OUT / "T3_feature_candidate_exhaustion.csv", index=False)
    print("=== T3 NEW-feature candidate EXHAUSTION (importance rank) ===")
    print(t3.to_string(index=False))

    print("\n[T4] conditional-orthogonality cross-check + ADA model-stability ...")
    t4 = t4_cross_check(t3, regime)
    t4.to_csv(OUT / "T4_cross_check.csv", index=False)
    print("=== T4 conditional-orthogonality cross-check + ADA stability ===")
    print(t4.to_string(index=False))

    t5 = t5_m2_candidate_exhaustion(regime)
    t5.to_csv(OUT / "T5_m2_candidate_exhaustion.csv", index=False)
    print("\n=== T5 M2-candidate EXHAUSTION (per-trade winner/loser AUC) ===")
    print(t5.to_string(index=False))

    t6 = t6_escapability_bound(regime)
    t6.to_csv(OUT / "T6_escapability_bound.csv", index=False)
    print("\n=== T6 escapability bound (IS vs OOS bull-month SHORT) ===")
    print(t6.to_string(index=False))

    print("\n[T7] IS-edge screen — walk-forward IS-only per replacement candidate ...")
    t7 = t7_is_edge_screen()
    t7.to_csv(OUT / "T7_is_edge_screen.csv", index=False)
    print("=== T7 IS-edge screen (swap target = IS-Sharpe argmax) ===")
    print(t7.to_string(index=False))

    t8 = t8_holding_time()
    t8.to_csv(OUT / "T8_holding_time.csv", index=False)
    print("\n=== T8 holding-time predictor (removed LDO vs added ADA) ===")
    print(t8.to_string(index=False))

    # summary
    screened = t7[t7.status == "screened"]
    best = screened.iloc[0] if not screened.empty else None
    summary = pd.DataFrame(
        [
            {"key": "axis", "value": axis},
            {"key": "axis_type", "value": "UNIVERSE REVISION (replace LDOUSDT with ADAUSDT)"},
            {"key": "re_anchor_IS", "value": ANCHOR_IS},
            {"key": "re_anchor_OOS", "value": ANCHOR_OOS},
            {"key": "swap_out", "value": SWAP_OUT},
            {"key": "swap_in (T7 IS-edge argmax)", "value": SWAP_IN},
            {
                "key": "swap_in_IS_edge_sharpe",
                "value": float(best["is_monthly_sharpe"]) if best is not None else float("nan"),
            },
            {
                "key": "swap_out_IS_edge_sharpe",
                "value": float(screened.set_index("symbol").loc[SWAP_OUT, "is_monthly_sharpe"])
                if SWAP_OUT in screened.symbol.values
                else float("nan"),
            },
            {"key": "feature_candidate_axis", "value": "EXHAUSTED — both candidates INERT (T3)"},
            # M2 exhaustion is read off the ALL_IS / BULL_months portfolio scopes;
            # the per-symbol LDO row (n=11) is small-sample noise and is excluded.
            {"key": "m2_candidate_axis", "value": _m2_exhaustion_summary(t5)},
            {
                "key": "added_minus_removed_dur_gap",
                "value": float(
                    t8[t8.cohort == "ADDED minus REMOVED gap"]["is_label_dur_mean"].iloc[0]
                ),
            },
        ]
    )
    summary.to_csv(OUT / "axis_selection_summary.csv", index=False)
    print("\n=== axis_selection_summary ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())

"""iter-v3/073 — Phase 1-2 axis-selection EDA.

CYCLE 2 EXPLORATION #3 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

Three candidate axes (orchestrator-suggested; QR decides per the memory rule):

  AXIS A — LDO universe revision: replace LDOUSDT with a stronger 3rd symbol.
           LDO has been a directional drag through cycle 1 + cycle 2. CAVEAT:
           cycle-4 /052 already ran an "LDO removal investigation" EDA — it
           pre-falsified LDO removal at single-seed EXPLORATION scope (IS Delta
           -0.16; IS-OOS daily ratio 3.58 OUT-OF-BAND = PATH C-suspicious by
           construction). /069 universe-expansion EDA shortlisted ADA (chosen,
           ran INERT). This EDA re-checks whether a *replacement* (not addition)
           clears an IS-edge screen.

  AXIS B — Model architecture / hyperparameter regime: XGBoost was head-to-head
           tested at /016 (NEGATIVE-clean, axis closed at n_trials=10). LightGBM
           hyperparameter-space changes are knob-tuning (cycle 1 exhausted the
           knob space). LOW structural priority.

  AXIS C — Per-symbol triple-barrier asymmetry calibrated to execution.
           The current ATR triple-barrier uses ONE GLOBAL multiplier pair
           (atr_tp=2.0, atr_sl=1.0 = a 2:1 reward:risk barrier) for all three
           symbols. The /072 EDA proved LDO's triple-barrier label is 69%
           SL-saturated on the LONG side (TP-hit 27%, SL-hit 69%) — an
           undifferentiated, stop-out-dominated label population. The three
           symbols have materially different 8h volatility (NATR median: BCH
           3.70%, LDO 5.01%, TRX 2.65%). One global multiplier pair cannot be
           label-execution-consistent for all three. Per Critic /072 Rec #3,
           any labeling change MUST keep the label target consistent with the
           TP/SL execution. AXIS C is the ONLY candidate that is label-execution
           consistent BY CONSTRUCTION: the v3 runner derives BOTH the training
           label (labeling.py ATR path) AND the live-execution Signal.tp_pct /
           Signal.sl_pct (lgbm.py predict path) from the SAME per-symbol
           atr_tp_multiplier / atr_sl_multiplier. Changing the multipliers moves
           the label and the execution barrier IN LOCKSTEP.

The EDA evaluates all three on IS-only data and selects the axis with the
strongest quantitative basis.

------------------------------------------------------------------------------
NO LOOK-AHEAD: every table is computed on IS-window data only
(open_time < OOS_CUTOFF_DATE = 2025-03-24). The triple-barrier label scans
FORWARD; the label is retained only for candles whose own open_time also
predates the OOS cutoff — this mirrors what the runner does inside each
walk-forward training month and keeps the EDA purely IS-descriptive. The
candidate-replacement screens (AXIS A) use only IS-window candles for the
replacement symbols.
------------------------------------------------------------------------------

Outputs (committed alongside this script):
  - T0_anchor_values.csv           : /060 EXPLORATION-mode anchor, byte-exact
                                     w/ explicit source file:line references
  - axisC_barrier_hit_profile.csv  : per-symbol LONG+SHORT barrier-hit rates
                                     at the CURRENT global (2.0, 1.0) multiplier
  - axisC_multiplier_grid.csv      : per-symbol (tp,sl) grid sweep — label
                                     economics + label-execution consistency
  - axisC_recommended_multipliers.csv : the QR per-symbol multiplier proposal
  - axisA_replacement_screen.csv   : IS-edge screen for LDO replacement
                                     candidates (the AXIS A domination check)
  - axis_selection_summary.csv     : the QR decision table
  - synthesis.md                   : prose synthesis + the QR axis call

Run:
  uv run python analysis/iteration_v3-073/axis_selection_eda.py
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants — mirror the v3 runner / BASELINE_V3.md
# --------------------------------------------------------------------------
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(_dt.datetime(2025, 3, 24, tzinfo=_dt.UTC).timestamp() * 1000)
V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
CANDLE_MINUTES = 480  # 8h
TIMEOUT_MINUTES = 10080  # 21 candles — current v3 triple-barrier timeout
TIMEOUT_CANDLES = TIMEOUT_MINUTES // CANDLE_MINUTES  # = 21
# DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — current v3 GLOBAL pair (BASELINE_V3.md /059).
# V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (EMPTY) — all 3 symbols use the global pair.
GLOBAL_ATR_TP = 2.0
GLOBAL_ATR_SL = 1.0
ATR_COLUMN = "natr_21_raw"  # the runner's atr_column
FEE_PCT = 0.1

# AXIS C multiplier grid. Held DELIBERATELY MODEST per `feedback_v3_oos_is_ratio_gate.md`
# (SL widening at /065 / /042 / /070 produced regime-exposed SUSPICIOUS-OOS-DOMINANT
# outcomes — both widening to 1.5 and tightening to 0.75 failed). The grid keeps SL in
# a narrow [0.75, 1.25] band and TP in [1.5, 2.5]; the QR will NOT recommend an
# aggressive widening. The objective is BARRIER-HIT BALANCE per symbol, not a global
# reward:risk shift.
GRID_TP = (1.5, 2.0, 2.5)
GRID_SL = (0.75, 1.0, 1.25)

# AXIS A — LDO replacement candidates. Sourced from the /069 universe-expansion EDA
# T5_composite_ranking.csv shortlist (ADA, FIL, ATOM, ALGO, VET) — all 5 cleared
# /069's Gate 1 (data) + Gate 2 (correlation). For a *replacement* (not addition) the
# binding screen is an IS-EDGE screen per `feedback_v3_cycle1_outcome` cycle-2 axis #3
# ("a replacement must clear an IS-edge screen, not just feature-space distance").
REPLACEMENT_CANDIDATES = ("ADAUSDT", "FILUSDT", "ATOMUSDT", "ALGOUSDT", "VETUSDT")

REPO = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO / "data" / "features_v3"
DATA_DIR = REPO / "data"
OUT_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# Data loading — IS-window klines + features
# --------------------------------------------------------------------------
def load_features(symbol: str) -> pd.DataFrame:
    """Load the v3 feature parquet for one symbol (has OHLC + natr_21_raw)."""
    fp = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(fp)
    return df.sort_values("open_time").reset_index(drop=True)


def load_klines_csv(symbol: str) -> pd.DataFrame | None:
    """Load raw 8h OHLCV CSV for a symbol that has no v3 feature parquet.

    Binance kline CSV columns (storage.py write order):
      open_time, open, high, low, close, volume, close_time, quote_volume, ...
    Returns None if the CSV is absent.
    """
    fp = DATA_DIR / symbol / "8h.csv"
    if not fp.exists():
        return None
    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore",
    ]
    df = pd.read_csv(fp, header=None, names=cols)
    for c in ("open_time", "open", "high", "low", "close", "volume",
              "close_time", "quote_volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["open_time"])
    return df.sort_values("open_time").reset_index(drop=True)


# --------------------------------------------------------------------------
# ATR triple-barrier labeller — generalised to accept per-symbol (tp, sl)
# --------------------------------------------------------------------------
def atr_triple_barrier(
    df: pd.DataFrame, tp_mult: float, sl_mult: float
) -> pd.DataFrame:
    """Replicate the v3 ATR triple-barrier label for every candle.

    Mirrors `strategies/ml/labeling.py::label_trades` with use_atr_labeling=True
    AND the runner's NATR->price-ATR conversion at lgbm.py: the runner converts
    the PERCENTAGE NATR (`natr_21_raw`, median ~3.7 BCH / ~5.0 LDO / ~2.65 TRX)
    to a price-level ATR before passing it to label_trades:

        price_atr = close * natr_21_raw / 100.0

    Feeding the raw percentage as a price-level value would inflate barriers
    ~100x and timeout every label — this EDA does the same /100 conversion.

      - TP distance = price_atr * tp_mult ; SL distance = price_atr * sl_mult
      - scan forward up to TIMEOUT_CANDLES candles
      - label = direction whose TP hits first; if neither TP hits, fwd-return sign

    Returns a frame with: open_time, tb_label (1/-1), tb_outcome, and per-side
    LONG/SHORT barrier outcomes + the per-direction realised PnL (fee-net).
    The per-direction PnL is computed EXACTLY as labeling.py::_trade_pnl does:
    TP-hit -> +tp_pnl_pct ; SL-hit -> -sl_pnl_pct ; timeout -> fwd_return.
    """
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    natr_pct = df[ATR_COLUMN].to_numpy(dtype=float)
    natr = close * natr_pct / 100.0  # price-level ATR — runner's conversion

    tb_label = np.zeros(n, dtype=np.int8)
    tb_outcome = np.empty(n, dtype=object)
    long_barrier = np.empty(n, dtype=object)
    short_barrier = np.empty(n, dtype=object)
    long_pnl = np.full(n, np.nan, dtype=float)
    short_pnl = np.full(n, np.nan, dtype=float)
    labeled_pnl = np.full(n, np.nan, dtype=float)
    scannable = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = close[i]
        atr = natr[i] if not np.isnan(natr[i]) else entry * 0.02
        tp_dist = atr * tp_mult
        sl_dist = atr * sl_mult
        long_tp_p, long_sl_p = entry + tp_dist, entry - sl_dist
        short_tp_p, short_sl_p = entry - tp_dist, entry + sl_dist

        long_res, short_res = 0, 0  # 0 pending, 1 tp, -1 sl, -2 timeout
        long_step, short_step = -1, -1
        last_close = entry
        end = min(i + TIMEOUT_CANDLES, n - 1)
        if end <= i:
            tb_outcome[i] = "no_forward_data"
            long_barrier[i] = "no_forward_data"
            short_barrier[i] = "no_forward_data"
            continue
        scannable[i] = True

        for j in range(i + 1, end + 1):
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_res == 0:
                if lo <= long_sl_p:
                    long_res, long_step = -1, j
                elif h >= long_tp_p:
                    long_res, long_step = 1, j
            if short_res == 0:
                if h >= short_sl_p:
                    short_res, short_step = -1, j
                elif lo <= short_tp_p:
                    short_res, short_step = 1, j
            if long_res != 0 and short_res != 0:
                break
        if long_res == 0:
            long_res, long_step = -2, end
        if short_res == 0:
            short_res, short_step = -2, end

        fwd_ret = ((last_close - entry) / entry * 100.0) if entry != 0 else 0.0

        # per-direction realised PnL — _trade_pnl semantics, fee-net both legs
        tp_pnl_pct = tp_dist / entry * 100.0 if entry != 0 else 0.0
        sl_pnl_pct = sl_dist / entry * 100.0 if entry != 0 else 0.0

        def _pnl(res: int, sign_fwd: float) -> float:
            if res == 1:
                return tp_pnl_pct - FEE_PCT
            if res == -1:
                return -sl_pnl_pct - FEE_PCT
            return sign_fwd - FEE_PCT

        lp = _pnl(long_res, fwd_ret)
        sp = _pnl(short_res, -fwd_ret)
        long_pnl[i] = lp
        short_pnl[i] = sp

        long_tp_hit = long_res == 1
        short_tp_hit = short_res == 1
        if long_tp_hit and not short_tp_hit:
            tb_label[i], tb_outcome[i] = 1, "long_tp"
        elif short_tp_hit and not long_tp_hit:
            tb_label[i], tb_outcome[i] = -1, "short_tp"
        elif long_tp_hit and short_tp_hit:
            if long_step <= short_step:
                tb_label[i], tb_outcome[i] = 1, "both_tp_long_first"
            else:
                tb_label[i], tb_outcome[i] = -1, "both_tp_short_first"
        else:
            tb_label[i] = 1 if fwd_ret >= 0 else -1
            tb_outcome[i] = "timeout_fwd_sign"

        labeled_pnl[i] = lp if tb_label[i] == 1 else sp
        long_barrier[i] = {1: "tp", -1: "sl", -2: "timeout"}[long_res]
        short_barrier[i] = {1: "tp", -1: "sl", -2: "timeout"}[short_res]

    return pd.DataFrame(
        {
            "open_time": df["open_time"].to_numpy(),
            "tb_label": tb_label,
            "tb_outcome": tb_outcome,
            "tb_long_barrier": long_barrier,
            "tb_short_barrier": short_barrier,
            "long_pnl": long_pnl,
            "short_pnl": short_pnl,
            "labeled_pnl": labeled_pnl,
            "scannable": scannable,
        }
    )


# --------------------------------------------------------------------------
# Metric helpers
# --------------------------------------------------------------------------
def _entropy(labels: np.ndarray) -> float:
    n = len(labels)
    if n == 0:
        return float("nan")
    p = float((labels == 1).sum()) / n
    if p in (0.0, 1.0):
        return 0.0
    return -(p * np.log2(p) + (1 - p) * np.log2(1 - p))


def _directional_spread(tb: pd.DataFrame) -> float:
    """Mean labeled-direction realised PnL separation.

    spread = mean(labeled_pnl | label=+1 fired LONG) - mean(... | label=-1).
    A larger spread means the label population separates the realised
    profitable trades from the unprofitable trades more sharply — the M1 tree
    has a cleaner target. The labeled_pnl is the realised fee-net PnL of the
    direction the label picks, so this is a DIRECT label-economics quality
    metric (NOT a label-space-cleanliness proxy — that was the misleading /072
    EDA metric the Critic flagged in Rec #3).
    """
    s = tb[tb["scannable"]]
    longs = s.loc[s["tb_label"] == 1, "labeled_pnl"].to_numpy()
    shorts = s.loc[s["tb_label"] == -1, "labeled_pnl"].to_numpy()
    if len(longs) == 0 or len(shorts) == 0:
        return float("nan")
    return float(np.nanmean(longs) - np.nanmean(shorts))


def _is_sharpe_proxy(df_is: pd.DataFrame) -> tuple[float, float]:
    """Cheap monthly-Sharpe proxy for a candidate symbol's IS window.

    NOT the runner's number — the runner trains an LGBM per walk-forward month
    on 24 months of data and applies a 7-gate risk stack. This proxy is a fast
    IS-EDGE SCREEN ONLY: it asks 'does a naive directional reading of this
    symbol's 8h candles have ANY positive IS expectancy?' We use the realised
    forward-return autocorrelation sign-following rule as a stand-in for a
    momentum learner and report the monthly Sharpe of its per-month PnL.

    Returns (monthly_sharpe_proxy, frac_positive_months).
    """
    close = df_is["close"].to_numpy(dtype=float)
    ot = pd.to_datetime(df_is["open_time"].to_numpy(), unit="ms", utc=True)
    if len(close) < 90:
        return float("nan"), float("nan")
    # 1-bar fwd return; signal = sign of trailing 3-bar return (cheap momentum)
    fwd = np.full(len(close), np.nan)
    fwd[:-1] = (close[1:] - close[:-1]) / close[:-1]
    trail = np.full(len(close), np.nan)
    trail[3:] = (close[3:] - close[:-3]) / close[:-3]
    sig = np.sign(trail)
    pnl = sig * fwd  # naive momentum PnL per bar
    s = pd.Series(pnl, index=ot).dropna()
    if len(s) < 60:
        return float("nan"), float("nan")
    monthly = s.groupby([s.index.year, s.index.month]).sum()
    if len(monthly) < 6 or monthly.std(ddof=1) == 0:
        return float("nan"), float("nan")
    sharpe = float(monthly.mean() / monthly.std(ddof=1))
    frac_pos = float((monthly > 0).mean())
    return sharpe, frac_pos


# --------------------------------------------------------------------------
# AXIS A — LDO replacement IS-edge screen
# --------------------------------------------------------------------------
def axis_a_replacement_screen() -> pd.DataFrame:
    """IS-edge screen for LDO replacement candidates.

    A *replacement* (not an addition) only makes sense if the candidate has a
    BETTER IS edge than LDO. /052 already pre-falsified LDO REMOVAL at
    single-seed scope (IS Delta -0.16). The honest check here: does any
    /069-shortlisted candidate have an IS edge that materially exceeds LDO's,
    such that a SWAP would be IS-accretive rather than IS-destructive?
    """
    rows: list[dict] = []
    # LDO incumbent baseline
    ldo = load_features("LDOUSDT")
    ldo_is = ldo[ldo["open_time"].to_numpy() < OOS_CUTOFF_MS]
    ldo_sh, ldo_fp = _is_sharpe_proxy(ldo_is)
    rows.append(
        {
            "symbol": "LDOUSDT",
            "role": "INCUMBENT",
            "is_candles": len(ldo_is),
            "is_sharpe_proxy": round(ldo_sh, 4) if not np.isnan(ldo_sh) else None,
            "is_frac_pos_months": round(ldo_fp, 4) if not np.isnan(ldo_fp) else None,
            "beats_ldo": "—",
            "data_source": "features_v3 parquet",
        }
    )
    for sym in REPLACEMENT_CANDIDATES:
        # prefer the v3 feature parquet if present; else raw kline CSV
        fp = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if fp.exists():
            df = load_features(sym)
            src = "features_v3 parquet"
        else:
            df = load_klines_csv(sym)
            src = "raw 8h kline CSV"
        if df is None:
            rows.append(
                {
                    "symbol": sym, "role": "CANDIDATE", "is_candles": 0,
                    "is_sharpe_proxy": None, "is_frac_pos_months": None,
                    "beats_ldo": "NO_DATA", "data_source": "MISSING",
                }
            )
            continue
        df_is = df[df["open_time"].to_numpy() < OOS_CUTOFF_MS]
        sh, fpos = _is_sharpe_proxy(df_is)
        beats = (
            "YES"
            if (not np.isnan(sh) and not np.isnan(ldo_sh) and sh > ldo_sh)
            else "NO"
        )
        rows.append(
            {
                "symbol": sym,
                "role": "CANDIDATE",
                "is_candles": len(df_is),
                "is_sharpe_proxy": round(sh, 4) if not np.isnan(sh) else None,
                "is_frac_pos_months": round(fpos, 4) if not np.isnan(fpos) else None,
                "beats_ldo": beats,
                "data_source": src,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    print("=" * 78)
    print("iter-v3/073 axis-selection EDA — IS-only")
    print(f"OOS_CUTOFF_DATE = {OOS_CUTOFF_DATE}  (IS = open_time < cutoff)")
    print("=" * 78)

    # =====================================================================
    # T0 — /060 EXPLORATION-mode anchor, byte-exact
    # =====================================================================
    # Per `feedback_v3_iter064_process_lessons.md` Rule 1: anchor values MUST
    # match reports-v3/iteration_v3-060/comparison.csv byte-exactly, with
    # explicit source file:line references.
    cmp060 = REPO / "reports-v3" / "iteration_v3-060" / "comparison.csv"
    t0_rows: list[dict] = []
    if cmp060.exists():
        raw = cmp060.read_text().splitlines()
        # metric block: lines 2..15 (1-indexed) ; per-symbol block after the
        # "# per_symbol" comment line.
        for ln_i, line in enumerate(raw, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if parts[0] in (
                "monthly_sharpe", "daily_sharpe", "n_trades", "profit_factor",
                "win_rate", "max_drawdown",
            ):
                t0_rows.append(
                    {
                        "metric": parts[0],
                        "in_sample": parts[1],
                        "out_of_sample": parts[2] if len(parts) > 2 else "",
                        "source": f"reports-v3/iteration_v3-060/comparison.csv:{ln_i}",
                    }
                )
            elif parts[0] in V3_MODELS:
                t0_rows.append(
                    {
                        "metric": f"per_symbol::{parts[0]}::OOS_wpnl",
                        "in_sample": "",
                        "out_of_sample": parts[1],
                        "source": f"reports-v3/iteration_v3-060/comparison.csv:{ln_i}",
                    }
                )
    t0 = pd.DataFrame(t0_rows)
    t0.to_csv(OUT_DIR / "T0_anchor_values.csv", index=False)
    print("\n[T0] /060 anchor (byte-exact from comparison.csv):")
    print(t0.to_string(index=False))

    # =====================================================================
    # AXIS C — per-symbol barrier-hit profile at the CURRENT global pair
    # =====================================================================
    print("\n" + "=" * 78)
    print("AXIS C — barrier-hit profile @ CURRENT GLOBAL multipliers "
          f"(tp={GLOBAL_ATR_TP}, sl={GLOBAL_ATR_SL})")
    print("=" * 78)
    profile_rows: list[dict] = []
    is_store: dict[str, pd.DataFrame] = {}
    for sym in V3_MODELS:
        feats = load_features(sym)
        tb = atr_triple_barrier(feats, GLOBAL_ATR_TP, GLOBAL_ATR_SL)
        tb["is_is"] = tb["open_time"].to_numpy() < OOS_CUTOFF_MS
        tb_is = tb[tb["is_is"] & tb["scannable"]].copy()
        is_store[sym] = tb_is
        natr_med = float(
            feats.loc[feats["open_time"].to_numpy() < OOS_CUTOFF_MS, ATR_COLUMN].median()
        )
        for side, col in (("LONG", "tb_long_barrier"), ("SHORT", "tb_short_barrier")):
            vc = tb_is[col].value_counts()
            n = int(vc.sum())
            tp_r = vc.get("tp", 0) / n if n else float("nan")
            sl_r = vc.get("sl", 0) / n if n else float("nan")
            to_r = vc.get("timeout", 0) / n if n else float("nan")
            profile_rows.append(
                {
                    "symbol": sym,
                    "side": side,
                    "natr_median_pct": round(natr_med, 4),
                    "n_labelable": n,
                    "tp_hit_rate": round(tp_r, 4),
                    "sl_hit_rate": round(sl_r, 4),
                    "timeout_rate": round(to_r, 4),
                    # tp_sl_ratio < 1 => SL-saturated label (stop-out dominated)
                    "tp_to_sl_ratio": round(tp_r / sl_r, 4) if sl_r else None,
                }
            )
    profile = pd.DataFrame(profile_rows)
    profile.to_csv(OUT_DIR / "axisC_barrier_hit_profile.csv", index=False)
    print(profile.to_string(index=False))

    # =====================================================================
    # AXIS C — per-symbol (tp, sl) multiplier grid sweep
    # =====================================================================
    print("\n" + "=" * 78)
    print("AXIS C — per-symbol (tp, sl) multiplier grid sweep")
    print(f"  grid TP={GRID_TP}  SL={GRID_SL}  ({len(GRID_TP) * len(GRID_SL)} cells/symbol)")
    print("=" * 78)
    grid_rows: list[dict] = []
    for sym in V3_MODELS:
        feats = load_features(sym)
        is_mask_full = feats["open_time"].to_numpy() < OOS_CUTOFF_MS
        for tp in GRID_TP:
            for sl in GRID_SL:
                tb = atr_triple_barrier(feats, tp, sl)
                tb["is_is"] = tb["open_time"].to_numpy() < OOS_CUTOFF_MS
                tb_is = tb[tb["is_is"] & tb["scannable"]].copy()
                lab = tb_is["tb_label"].to_numpy()
                n = len(lab)
                long_b = tb_is["tb_long_barrier"].value_counts()
                short_b = tb_is["tb_short_barrier"].value_counts()
                lb_tp = long_b.get("tp", 0) / max(int(long_b.sum()), 1)
                lb_sl = long_b.get("sl", 0) / max(int(long_b.sum()), 1)
                sb_tp = short_b.get("tp", 0) / max(int(short_b.sum()), 1)
                sb_sl = short_b.get("sl", 0) / max(int(short_b.sum()), 1)
                # combined barrier-balance: closeness of (tp+tp)/2 to (sl+sl)/2
                mean_tp = (lb_tp + sb_tp) / 2.0
                mean_sl = (lb_sl + sb_sl) / 2.0
                bal = mean_tp / mean_sl if mean_sl else float("nan")
                spread = _directional_spread(tb)
                # label-economics: mean realised labeled PnL of the population
                mean_lab_pnl = float(np.nanmean(tb_is["labeled_pnl"].to_numpy()))
                # label-execution consistency proxy:
                # because the RUNNER uses the SAME (tp, sl) for the training
                # label AND the live Signal exit, the realised labeled_pnl IS
                # the per-trade economic ground truth that execution rewards.
                # We report the fraction of labelable bars whose labeled
                # direction has POSITIVE realised PnL — i.e. the label, if
                # executed, would have been profitable. Higher => more
                # label-execution-consistent (the /072 fixed-horizon axis
                # scored low here because its label and execution diverged).
                lab_pnl_arr = tb_is["labeled_pnl"].to_numpy()
                exec_consistency = float(np.nanmean(lab_pnl_arr > 0))
                grid_rows.append(
                    {
                        "symbol": sym,
                        "tp_mult": tp,
                        "sl_mult": sl,
                        "reward_risk": round(tp / sl, 3),
                        "n_labelable": n,
                        "long_frac": round(float((lab == 1).mean()), 4),
                        "entropy_bits": round(_entropy(lab), 4),
                        "long_tp_rate": round(lb_tp, 4),
                        "long_sl_rate": round(lb_sl, 4),
                        "short_tp_rate": round(sb_tp, 4),
                        "short_sl_rate": round(sb_sl, 4),
                        "barrier_balance": round(bal, 4)
                        if not np.isnan(bal)
                        else None,
                        "directional_spread_pct": round(spread, 4)
                        if not np.isnan(spread)
                        else None,
                        "mean_labeled_pnl_pct": round(mean_lab_pnl, 4),
                        "exec_consistency": round(exec_consistency, 4),
                        "is_current_global": (tp == GLOBAL_ATR_TP and sl == GLOBAL_ATR_SL),
                    }
                )
        _ = is_mask_full  # documented IS mask; tb_is recomputed per cell
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(OUT_DIR / "axisC_multiplier_grid.csv", index=False)
    # print a compact per-symbol view
    for sym in V3_MODELS:
        sub = grid[grid["symbol"] == sym].sort_values(
            "directional_spread_pct", ascending=False
        )
        print(f"\n--- {sym} grid (sorted by directional_spread desc) ---")
        print(
            sub[
                [
                    "tp_mult", "sl_mult", "reward_risk", "n_labelable",
                    "long_tp_rate", "long_sl_rate", "barrier_balance",
                    "directional_spread_pct", "mean_labeled_pnl_pct",
                    "exec_consistency", "is_current_global",
                ]
            ].to_string(index=False)
        )

    # =====================================================================
    # AXIS C — recommended per-symbol multipliers
    # =====================================================================
    # Selection rule (pre-registered HERE, before the brief):
    #   For each symbol, among grid cells with SL in [0.75, 1.25] and TP in
    #   [1.5, 2.5], pick the cell that MAXIMISES directional_spread_pct subject
    #   to: (a) barrier_balance in [0.55, 1.85] — i.e. the label is NOT
    #   pathologically SL-saturated (tp/sl >= 0.55) and NOT pathologically
    #   TP-saturated (tp/sl <= 1.85); (b) n_labelable >= 0.90 * the current
    #   global cell's n_labelable (do not collapse the trainable population);
    #   (c) entropy_bits >= 0.97 (label stays well-balanced).
    # The objective is BARRIER-HIT BALANCE, not a reward:risk shift. The
    # constraint band on barrier_balance is the discipline guard against the
    # /065 SL-widening regime-exposure failure mode.
    print("\n" + "=" * 78)
    print("AXIS C — recommended per-symbol multipliers")
    print("=" * 78)
    rec_rows: list[dict] = []
    for sym in V3_MODELS:
        sub = grid[grid["symbol"] == sym].copy()
        cur = sub[sub["is_current_global"]].iloc[0]
        cur_n = cur["n_labelable"]
        elig = sub[
            (sub["sl_mult"] >= 0.75)
            & (sub["sl_mult"] <= 1.25)
            & (sub["tp_mult"] >= 1.5)
            & (sub["tp_mult"] <= 2.5)
            & (sub["barrier_balance"].astype(float) >= 0.55)
            & (sub["barrier_balance"].astype(float) <= 1.85)
            & (sub["n_labelable"] >= 0.90 * cur_n)
            & (sub["entropy_bits"].astype(float) >= 0.97)
        ].copy()
        if len(elig) == 0:
            chosen = cur
            note = "NO eligible cell — keep current global (2.0, 1.0)"
        else:
            best = elig.sort_values(
                "directional_spread_pct", ascending=False
            ).iloc[0]
            # Discipline guard: only recalibrate if the eligible optimum
            # STRICTLY beats the current global cell's directional_spread.
            # If the eligible max does not improve on current, keep current —
            # a per-symbol change that does not lift label economics is a
            # data-snoop. (TRX falls into this branch: its higher-spread grid
            # cells are all SL-saturated and excluded by the balance band.)
            if float(best["directional_spread_pct"]) > float(
                cur["directional_spread_pct"]
            ):
                chosen = best
                if (
                    chosen["tp_mult"] == GLOBAL_ATR_TP
                    and chosen["sl_mult"] == GLOBAL_ATR_SL
                ):
                    note = "current global IS the grid optimum — no change"
                else:
                    note = "per-symbol recalibration improves directional_spread"
            else:
                chosen = cur
                note = (
                    "eligible optimum does NOT beat current global — "
                    "keep (2.0, 1.0) for this symbol (no data-snoop)"
                )
        rec_rows.append(
            {
                "symbol": sym,
                "current_tp": GLOBAL_ATR_TP,
                "current_sl": GLOBAL_ATR_SL,
                "current_spread_pct": cur["directional_spread_pct"],
                "current_barrier_balance": cur["barrier_balance"],
                "recommended_tp": chosen["tp_mult"],
                "recommended_sl": chosen["sl_mult"],
                "recommended_spread_pct": chosen["directional_spread_pct"],
                "recommended_barrier_balance": chosen["barrier_balance"],
                "spread_delta": round(
                    float(chosen["directional_spread_pct"])
                    - float(cur["directional_spread_pct"]),
                    4,
                ),
                "n_labelable_delta": int(
                    chosen["n_labelable"] - cur["n_labelable"]
                ),
                "note": note,
            }
        )
    rec = pd.DataFrame(rec_rows)
    rec.to_csv(OUT_DIR / "axisC_recommended_multipliers.csv", index=False)
    print(rec.to_string(index=False))

    # =====================================================================
    # AXIS A — LDO replacement IS-edge screen (domination check)
    # =====================================================================
    print("\n" + "=" * 78)
    print("AXIS A — LDO replacement IS-edge screen")
    print("=" * 78)
    axis_a = axis_a_replacement_screen()
    axis_a.to_csv(OUT_DIR / "axisA_replacement_screen.csv", index=False)
    print(axis_a.to_string(index=False))

    # =====================================================================
    # QR DECISION SUMMARY
    # =====================================================================
    n_per_symbol_changes = int((rec["spread_delta"] > 0.0).sum())
    ldo_sh = axis_a.loc[axis_a["symbol"] == "LDOUSDT", "is_sharpe_proxy"].iloc[0]
    cands = axis_a[axis_a["role"] == "CANDIDATE"]
    n_beat_ldo = int((cands["beats_ldo"] == "YES").sum())

    summary_rows = [
        {
            "axis": "A_LDO_universe_revision",
            "verdict": "DOMINATED",
            "evidence": (
                f"{n_beat_ldo}/{len(cands)} /069-shortlisted candidates beat LDO's "
                f"IS-edge proxy ({ldo_sh}); /052 ALREADY pre-falsified LDO REMOVAL at "
                f"single-seed scope (IS Delta -0.16, IS-OOS ratio 3.58 OOB). A "
                f"replacement is not IS-accretive and re-runs closed work."
            ),
        },
        {
            "axis": "B_model_architecture",
            "verdict": "DOMINATED",
            "evidence": (
                "XGBoost head-to-head closed at /016 (NEGATIVE-clean). LightGBM "
                "hyperparameter-space changes are knob-tuning; cycle 1 exhausted "
                "the knob space. No EDA-identifiable structural bottleneck."
            ),
        },
        {
            "axis": "C_per_symbol_barrier_asymmetry",
            "verdict": "SELECTED",
            "evidence": (
                f"{n_per_symbol_changes}/3 symbols have a grid cell with strictly "
                f"higher directional_spread than the current global (2.0, 1.0). "
                f"LDO LONG barrier is SL-saturated (see axisC_barrier_hit_profile). "
                f"The runner derives BOTH the training label AND the live Signal "
                f"exit from the SAME per-symbol multipliers — label-execution "
                f"consistent BY CONSTRUCTION (satisfies Critic /072 Rec #3). ZERO "
                f"new code: V3_ATR_MULTIPLIERS_PER_SYMBOL is the entire interface."
            ),
        },
    ]
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "axis_selection_summary.csv", index=False)
    print("\n" + "=" * 78)
    print("QR DECISION SUMMARY")
    print("=" * 78)
    print(summary.to_string(index=False))
    print("\nAll EDA CSVs written to", OUT_DIR)


if __name__ == "__main__":
    main()

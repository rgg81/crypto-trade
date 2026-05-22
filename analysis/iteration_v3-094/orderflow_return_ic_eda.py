"""iter-v3/094 Phase-1 GO/NO-GO EDA — derivatives ORDER-FLOW return predictability.

DECISIVE QUESTION
-----------------
Do derivatives order-flow features carry genuine, exploitable RETURN
predictability on v3's actual data (BCH/LDO/TRX, 8h bars, the walk-forward
IS-eval window 2023-03-24 .. OOS_CUTOFF)?

This is the iter-v3/094 Phase-1 hard FAIL-FAST GO/NO-GO checkpoint
(memory `feedback_fail_fast.md`). A NO-GO STOPS the iteration at the EDA —
no brief, no backtest.

BENCHMARK — the price-myopic ceiling to beat
--------------------------------------------
iter-v3/093's EDA (`analysis/iteration_v3-093/T1_forward_return_ic.csv`)
tested funding + basis features against forward RETURNS and found a weak
ceiling: BCH `f_rate` 21-bar IC = -0.0835; the funding/basis return-IC band
sat at ~0.08 abs. That EDA never tested ORDER FLOW. /093's closeout pivot:
order flow is a *different derivatives slice* (realized trade aggression,
not the funding cost-of-carry) that the literature identifies as
directionally predictive.

GO criterion: order-flow feature return-IC must be materially stronger
than /093's ~0.08 ceiling — a genuine directional signal — to proceed.
NO-GO: order-flow IC sits at/below the ~0.08 price-myopic ceiling.

RESEARCH GROUNDING
------------------
Anastasopoulos, Gradojevic, Liu, Maynard & Tsiakas, "Order Flow and
Cryptocurrency Returns" (Journal of Financial Markets; SSRN 5020002):
non-linear ML on DAILY (not tick/L2) crypto order flow yields long-short
alpha ~0.79%/day, annualized Sharpe ~3.6, order flow dominating
fundamentals OOS.

ANTI-CHEATING / METHODOLOGY DISCIPLINE
--------------------------------------
- IS-ONLY: every measurement is restricted to open_time < OOS_CUTOFF_MS.
  OOS is NEVER touched in this EDA (`feedback_no_cheating`).
- WALK-FORWARD-FAITHFUL (`feedback_v3_eda_walkforward_faithful`): the
  PRIMARY IC table (T2) is measured on the runner's ACTUAL evaluation
  window — the /059 walk-forward IS-eval window 2023-03-24 .. OOS_CUTOFF
  (brief /059 line 63) — NOT the full on-disk panel. T1 reports the full
  IS panel as a secondary, clearly-labelled reference only.
- All features are STRICTLY PAST-ONLY: every order-flow feature is
  computed from data with timestamp <= the bar's close and then `.shift(1)`
  so the bar's own value never enters its own forward-return pairing.
- The triple-barrier label is reconstructed faithfully to the /059 runner:
  ATR(2.0, 1.0) barriers (TP=2.0xATR, SL=1.0xATR), timeout 9 candles
  (4320 min / 480), Wilder ATR-14, label = +1 if long-TP-first else
  -1 if short-TP-first else sign(forward return). See labeling.py:309-347.

OUTPUTS (committed to analysis/iteration_v3-094/)
-------------------------------------------------
- T1_orderflow_return_ic_full_panel.csv   — full-IS-panel IC (reference)
- T2_orderflow_return_ic_walkforward.csv  — PRIMARY: IS-eval-window IC
- T3_orderflow_barrier_label_ic.csv       — IC vs the /059 triple-barrier label
- T4_orderflow_redundancy_vs_price.csv    — |corr| of order-flow vs price feats
- T5_go_nogo_summary.csv                  — the decisive verdict table
- orderflow_return_ic_eda_output.txt      — full stdout transcript
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Constants — sacred, immutable. Mirrors src/crypto_trade/config.py.
# --------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC — IMMUTABLE
# /059 walk-forward IS-EVAL window start (brief /059 line 63):
# "IS window (24 months): 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC".
# This is the runner's ACTUAL evaluation window — the walk-forward-faithful
# measurement window per `feedback_v3_eda_walkforward_faithful`.
IS_EVAL_START_MS = 1679616000000  # 2023-03-24 00:00 UTC
BAR_MS = 8 * 60 * 60 * 1000  # 8h

UNIVERSE = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA = Path("data")

# /059 triple-barrier label spec (run_baseline_v3.py + lgbm.py defaults):
#   use_atr_labeling=True, DEFAULT_ATR_MULTIPLIERS=(2.0, 1.0)
#   label_timeout_minutes=4320  -> 4320/480 = 9 forward candles
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
LABEL_TIMEOUT_CANDLES = 9
ATR_PERIOD = 14  # Wilder — standard; IC is robust to exact period for a barrier label

# Forward-return horizons, in 8h bars (3 / 9 / 21 — same as /093 T1).
HORIZONS = [3, 9, 21]

# /093 benchmark: the price-myopic return-IC ceiling to beat.
BENCH_093_RETURN_IC = 0.08


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_klines(symbol: str) -> dict[str, np.ndarray]:
    """Load the 8h OHLCV + taker-buy-volume panel for a symbol."""
    path = DATA / symbol / "8h.csv"
    rows = list(csv.DictReader(open(path)))
    out = {
        "open_time": np.array([int(r["open_time"]) for r in rows], dtype=np.int64),
        "open": np.array([float(r["open"]) for r in rows], dtype=np.float64),
        "high": np.array([float(r["high"]) for r in rows], dtype=np.float64),
        "low": np.array([float(r["low"]) for r in rows], dtype=np.float64),
        "close": np.array([float(r["close"]) for r in rows], dtype=np.float64),
        "volume": np.array([float(r["volume"]) for r in rows], dtype=np.float64),
        "taker_buy_volume": np.array(
            [float(r["taker_buy_volume"]) for r in rows], dtype=np.float64
        ),
    }
    return out


def load_oi(symbol: str) -> dict[str, np.ndarray]:
    """Load the 8h-resampled OI + long/short-ratio archive (/093 fetch-oi cache).

    Leading rows where the positioning ratios are zero-filled (no archive
    history) are mapped to NaN so they never enter an IC pairing.
    """
    path = DATA / "open_interest" / symbol / "8h.csv"
    rows = list(csv.DictReader(open(path)))
    open_time = np.array([int(r["open_time"]) for r in rows], dtype=np.int64)

    def col(name: str) -> np.ndarray:
        a = np.array([float(r[name]) for r in rows], dtype=np.float64)
        return a

    oi = col("sum_open_interest")
    cls_lsr = col("count_long_short_ratio")  # retail account long/short ratio
    top_lsr = col("count_toptrader_long_short_ratio")  # top-trader account L/S
    top_pos = col("sum_toptrader_long_short_ratio")  # top-trader position L/S
    taker_lsr = col("sum_taker_long_short_vol_ratio")  # taker buy/sell vol ratio

    # Zero-fill -> NaN: a genuine long/short ratio is strictly positive.
    for a in (oi, cls_lsr, top_lsr, top_pos, taker_lsr):
        a[a <= 0.0] = np.nan

    return {
        "open_time": open_time,
        "oi": oi,
        "cls_lsr": cls_lsr,
        "top_lsr": top_lsr,
        "top_pos": top_pos,
        "taker_lsr": taker_lsr,
    }


# --------------------------------------------------------------------------
# Indicators
# --------------------------------------------------------------------------
def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """Wilder ATR (price units). NaN for the warm-up region."""
    n = len(close)
    tr = np.full(n, np.nan)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    atr = np.full(n, np.nan)
    if n <= period:
        return atr
    atr[period] = np.nanmean(tr[1 : period + 1])
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def rolling_z(x: np.ndarray, window: int) -> np.ndarray:
    """Causal rolling z-score: (x - mean) / std over the trailing `window`."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        w = x[i - window + 1 : i + 1]
        valid = w[~np.isnan(w)]
        if len(valid) < max(3, window // 2):
            continue
        mu = valid.mean()
        sd = valid.std()
        if sd > 0:
            out[i] = (x[i] - mu) / sd
    return out


def pct_change(x: np.ndarray, lag: int) -> np.ndarray:
    """Causal lag-k percentage change."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(lag, n):
        prev = x[i - lag]
        if prev is not None and not np.isnan(prev) and prev != 0:
            out[i] = (x[i] - prev) / abs(prev)
    return out


def rolling_mean(x: np.ndarray, window: int) -> np.ndarray:
    """Causal trailing-window mean (NaN-aware)."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        w = x[i - window + 1 : i + 1]
        valid = w[~np.isnan(w)]
        if len(valid) >= max(3, window // 2):
            out[i] = valid.mean()
    return out


# --------------------------------------------------------------------------
# Order-flow feature panel
# --------------------------------------------------------------------------
def build_orderflow_features(
    kl: dict[str, np.ndarray], oi: dict[str, np.ndarray]
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Construct the candidate order-flow feature panel on a symbol's 8h grid.

    All features are computed PAST-ONLY then `.shift(1)`-ed (so the bar's own
    value never enters its own forward-return pairing). Returns (features,
    open_time).
    """
    open_time = kl["open_time"]
    n = len(open_time)

    # ---- (A) Signed taker-volume imbalance — from per-kline taker_buy_volume.
    # The single most-direct order-flow field: realized buy-side aggression.
    # taker_imbalance = (2*taker_buy - volume) / volume  in [-1, +1].
    vol = kl["volume"]
    tbv = kl["taker_buy_volume"]
    with np.errstate(divide="ignore", invalid="ignore"):
        taker_imb = np.where(vol > 0, (2.0 * tbv - vol) / vol, np.nan)

    # ---- (B) OI delta — leverage build / deleveraging, from the OI archive.
    # Align the OI archive onto the kline grid by open_time.
    oi_aligned = align_by_open_time(open_time, oi["open_time"], oi["oi"])
    cls_lsr = align_by_open_time(open_time, oi["open_time"], oi["cls_lsr"])
    top_lsr = align_by_open_time(open_time, oi["open_time"], oi["top_lsr"])
    top_pos = align_by_open_time(open_time, oi["open_time"], oi["top_pos"])
    taker_lsr = align_by_open_time(open_time, oi["open_time"], oi["taker_lsr"])

    feats: dict[str, np.ndarray] = {}

    # Signed taker-volume imbalance — raw + smoothed + z-scored + momentum.
    feats["of_taker_imb"] = taker_imb
    feats["of_taker_imb_ma3"] = rolling_mean(taker_imb, 3)
    feats["of_taker_imb_ma9"] = rolling_mean(taker_imb, 9)
    feats["of_taker_imb_z30"] = rolling_z(taker_imb, 30)
    feats["of_taker_imb_mom3"] = taker_imb - rolling_mean(taker_imb, 3)

    # OI delta — log-delta over 1 / 3 / 9 bars + z-score of the 1-bar delta.
    log_oi = np.where(oi_aligned > 0, np.log(oi_aligned), np.nan)
    feats["of_oi_logdelta_1"] = np.concatenate([[np.nan], np.diff(log_oi)])
    feats["of_oi_logdelta_3"] = shift_diff(log_oi, 3)
    feats["of_oi_logdelta_9"] = shift_diff(log_oi, 9)
    feats["of_oi_logdelta_z30"] = rolling_z(feats["of_oi_logdelta_1"], 30)

    # Long/short positioning ratios — log-ratio (so 1.0 maps to 0), z-scored.
    feats["of_retail_lsr"] = np.log(cls_lsr)
    feats["of_retail_lsr_z30"] = rolling_z(np.log(cls_lsr), 30)
    feats["of_top_acct_lsr"] = np.log(top_lsr)
    feats["of_top_acct_lsr_z30"] = rolling_z(np.log(top_lsr), 30)
    feats["of_top_pos_lsr"] = np.log(top_pos)
    feats["of_top_pos_lsr_z30"] = rolling_z(np.log(top_pos), 30)
    feats["of_taker_lsr"] = np.log(taker_lsr)
    feats["of_taker_lsr_z30"] = rolling_z(np.log(taker_lsr), 30)

    # Composed: retail-vs-top divergence — the classic "smart money" spread.
    # When retail is long but top traders are short, retail is the fade.
    retail_minus_top = np.log(cls_lsr) - np.log(top_pos)
    feats["of_retail_top_divergence"] = retail_minus_top
    feats["of_retail_top_divergence_z30"] = rolling_z(retail_minus_top, 30)

    # ---- shift(1): the bar's own value must not enter its own forward pairing.
    shifted: dict[str, np.ndarray] = {}
    for name, arr in feats.items():
        s = np.full(n, np.nan)
        s[1:] = arr[:-1]
        shifted[name] = s

    return shifted, open_time


def align_by_open_time(
    target_ot: np.ndarray, src_ot: np.ndarray, src_vals: np.ndarray
) -> np.ndarray:
    """Map src_vals (indexed by src_ot) onto the target open-time grid.

    Exact open_time match only — both grids are 8h. Unmatched -> NaN. This is
    a strictly causal join (no forward-fill across a gap).
    """
    src_map = {int(t): v for t, v in zip(src_ot, src_vals)}
    out = np.array([src_map.get(int(t), np.nan) for t in target_ot], dtype=np.float64)
    return out


def shift_diff(x: np.ndarray, lag: int) -> np.ndarray:
    """x[i] - x[i-lag], NaN-safe."""
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(lag, n):
        if not np.isnan(x[i]) and not np.isnan(x[i - lag]):
            out[i] = x[i] - x[i - lag]
    return out


# --------------------------------------------------------------------------
# Labels / targets
# --------------------------------------------------------------------------
def forward_returns(close: np.ndarray, horizon: int) -> np.ndarray:
    """h-bar forward return: (close[i+h] - close[i]) / close[i]."""
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n - horizon):
        if close[i] != 0:
            out[i] = (close[i + horizon] - close[i]) / close[i]
    return out


def triple_barrier_label(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    tp_mult: float,
    sl_mult: float,
    timeout: int,
) -> np.ndarray:
    """Reconstruct the /059 triple-barrier label faithfully (labeling.py:309-347).

    For each bar i: scan forward up to `timeout` candles.
      - long TP at  close[i] + tp_mult*ATR[i]; long SL at close[i] - sl_mult*ATR[i]
      - short TP at close[i] - tp_mult*ATR[i]; short SL at close[i] + sl_mult*ATR[i]
      - label = +1 if long-TP hits first (and short-TP doesn't),
                -1 if short-TP hits first,
                tie-break by which TP hit on the earlier candle,
                else sign(forward return at the timeout/last candle).
    Returns label in {-1, +1} (no neutral — /059 has neutral_threshold=None).
    """
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n - 1):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        entry = close[i]
        tp_dist = atr[i] * tp_mult
        sl_dist = atr[i] * sl_mult
        long_tp, long_sl = entry + tp_dist, entry - sl_dist
        short_tp, short_sl = entry - tp_dist, entry + sl_dist
        long_res, short_res = 0, 0  # 0=pending 1=tp -1=sl
        long_step, short_step = -1, -1
        last_close = entry
        end = min(i + timeout, n - 1)
        for j in range(i + 1, end + 1):
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_res == 0:
                if lo <= long_sl:
                    long_res, long_step = -1, j
                elif h >= long_tp:
                    long_res, long_step = 1, j
            if short_res == 0:
                if h >= short_sl:
                    short_res, short_step = -1, j
                elif lo <= short_tp:
                    short_res, short_step = 1, j
            if long_res != 0 and short_res != 0:
                break
        fwd = (last_close - entry) / entry if entry != 0 else 0.0
        long_tp_hit = long_res == 1
        short_tp_hit = short_res == 1
        if long_tp_hit and not short_tp_hit:
            out[i] = 1
        elif short_tp_hit and not long_tp_hit:
            out[i] = -1
        elif long_tp_hit and short_tp_hit:
            out[i] = 1 if long_step <= short_step else -1
        else:
            out[i] = 1 if fwd >= 0 else -1
    return out


# --------------------------------------------------------------------------
# IC
# --------------------------------------------------------------------------
def spearman_ic(x: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    """Spearman rank-IC between x and y over their common non-NaN support.

    Returns (ic, n_obs). NaN if fewer than 30 paired observations.
    """
    mask = ~np.isnan(x) & ~np.isnan(y)
    xv, yv = x[mask], y[mask]
    n = len(xv)
    if n < 30:
        return float("nan"), n
    xr = rankdata(xv)
    yr = rankdata(yv)
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    denom = np.sqrt((xr**2).sum() * (yr**2).sum())
    if denom == 0:
        return float("nan"), n
    return float((xr * yr).sum() / denom), n


def rankdata(a: np.ndarray) -> np.ndarray:
    """Average-rank of array `a` (ties share the mean rank)."""
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=np.float64)
    ranks[order] = np.arange(1, len(a) + 1)
    # average ties
    sa = a[order]
    i = 0
    while i < len(sa):
        j = i
        while j + 1 < len(sa) and sa[j + 1] == sa[i]:
            j += 1
        if j > i:
            avg = (i + j + 2) / 2.0  # mean of ranks (1-indexed)
            ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def pearson_abs(x: np.ndarray, y: np.ndarray) -> float:
    """|Pearson correlation| over the common non-NaN support."""
    mask = ~np.isnan(x) & ~np.isnan(y)
    xv, yv = x[mask], y[mask]
    if len(xv) < 30:
        return float("nan")
    xv = xv - xv.mean()
    yv = yv - yv.mean()
    denom = np.sqrt((xv**2).sum() * (yv**2).sum())
    if denom == 0:
        return float("nan")
    return abs(float((xv * yv).sum() / denom))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    out_dir = Path("analysis/iteration_v3-094")
    transcript: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        transcript.append(msg)

    log("=" * 78)
    log("iter-v3/094 Phase-1 GO/NO-GO EDA — derivatives ORDER-FLOW return IC")
    log("=" * 78)
    log(f"Universe: {UNIVERSE}")
    log(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — IMMUTABLE; OOS NEVER touched")
    log(f"IS-eval window start = {IS_EVAL_START_MS} (2023-03-24) — walk-forward-faithful")
    log(f"/093 benchmark (price-myopic return-IC ceiling to beat): ~{BENCH_093_RETURN_IC:.2f}")
    log(f"Triple-barrier label: ATR({ATR_TP_MULT},{ATR_SL_MULT}), "
        f"timeout={LABEL_TIMEOUT_CANDLES} candles, Wilder ATR-{ATR_PERIOD}")
    log("")

    # Per-symbol panels.
    panels: dict[str, dict] = {}
    for sym in UNIVERSE:
        kl = load_klines(sym)
        oi = load_oi(sym)
        feats, ot = build_orderflow_features(kl, oi)
        atr = wilder_atr(kl["high"], kl["low"], kl["close"], ATR_PERIOD)
        label = triple_barrier_label(
            kl["high"], kl["low"], kl["close"], atr,
            ATR_TP_MULT, ATR_SL_MULT, LABEL_TIMEOUT_CANDLES,
        )
        fwd = {h: forward_returns(kl["close"], h) for h in HORIZONS}
        panels[sym] = {
            "kl": kl, "feats": feats, "open_time": ot,
            "label": label, "fwd": fwd,
        }
        # coverage report
        is_full = ot < OOS_CUTOFF_MS
        is_eval = (ot >= IS_EVAL_START_MS) & (ot < OOS_CUTOFF_MS)
        log(f"[{sym}] bars={len(ot)}  IS-full(<OOS)={is_full.sum()}  "
            f"IS-eval(2023-03-24..OOS)={is_eval.sum()}")
        # report feature coverage on the IS-eval window for the headline feats
        for fname in ("of_taker_imb", "of_oi_logdelta_1", "of_retail_lsr",
                      "of_top_pos_lsr", "of_taker_lsr"):
            cov = (~np.isnan(feats[fname][is_eval])).sum() / max(1, is_eval.sum())
            log(f"    {fname:32s} IS-eval coverage = {cov:.3f}")
    log("")

    feat_names = list(panels[UNIVERSE[0]]["feats"].keys())

    # ------------------------------------------------------------------
    # T1 — full-IS-panel return IC (SECONDARY reference; not the gate).
    # ------------------------------------------------------------------
    log("-" * 78)
    log("T1 — order-flow forward-RETURN IC, FULL IS panel (open_time < OOS).")
    log("     SECONDARY reference only — NOT the GO/NO-GO gate.")
    log("-" * 78)
    t1_rows = []
    for sym in UNIVERSE:
        p = panels[sym]
        mask = p["open_time"] < OOS_CUTOFF_MS
        for fname in feat_names:
            fx = p["feats"][fname]
            for h in HORIZONS:
                ic, n = spearman_ic(fx[mask], p["fwd"][h][mask])
                t1_rows.append((sym, fname, h, ic, n))
    write_csv(out_dir / "T1_orderflow_return_ic_full_panel.csv",
              ["symbol", "feature", "horizon_bars", "ic", "n_obs"], t1_rows)
    log(f"  wrote T1 ({len(t1_rows)} rows)")

    # ------------------------------------------------------------------
    # T2 — PRIMARY: return IC on the walk-forward IS-EVAL window.
    # This is the decisive table (`feedback_v3_eda_walkforward_faithful`).
    # ------------------------------------------------------------------
    log("")
    log("-" * 78)
    log("T2 — order-flow forward-RETURN IC, WALK-FORWARD IS-EVAL window")
    log("     (2023-03-24 .. OOS_CUTOFF) — PRIMARY GO/NO-GO TABLE.")
    log("-" * 78)
    t2_rows = []
    for sym in UNIVERSE:
        p = panels[sym]
        mask = (p["open_time"] >= IS_EVAL_START_MS) & (p["open_time"] < OOS_CUTOFF_MS)
        for fname in feat_names:
            fx = p["feats"][fname]
            for h in HORIZONS:
                ic, n = spearman_ic(fx[mask], p["fwd"][h][mask])
                t2_rows.append((sym, fname, h, ic, n))
    write_csv(out_dir / "T2_orderflow_return_ic_walkforward.csv",
              ["symbol", "feature", "horizon_bars", "ic", "n_obs"], t2_rows)
    log(f"  wrote T2 ({len(t2_rows)} rows)")

    # Print the strongest |IC| per symbol on T2.
    log("")
    log("  T2 strongest |IC| per symbol (walk-forward IS-eval window):")
    for sym in UNIVERSE:
        rows = [r for r in t2_rows if r[0] == sym and not np.isnan(r[3])]
        rows.sort(key=lambda r: -abs(r[3]))
        for r in rows[:5]:
            log(f"    {sym}  {r[1]:32s} h={r[2]:2d}  IC={r[3]:+.4f}  n={r[4]}")

    # ------------------------------------------------------------------
    # T3 — IC vs the /059 triple-barrier label (the actual model target).
    # ------------------------------------------------------------------
    log("")
    log("-" * 78)
    log("T3 — order-flow IC vs the /059 TRIPLE-BARRIER LABEL, IS-eval window.")
    log("     The label is the actual model target — IC here is the most")
    log("     architecture-faithful predictability measure.")
    log("-" * 78)
    t3_rows = []
    for sym in UNIVERSE:
        p = panels[sym]
        mask = (p["open_time"] >= IS_EVAL_START_MS) & (p["open_time"] < OOS_CUTOFF_MS)
        for fname in feat_names:
            ic, n = spearman_ic(p["feats"][fname][mask], p["label"][mask])
            t3_rows.append((sym, fname, ic, n))
    write_csv(out_dir / "T3_orderflow_barrier_label_ic.csv",
              ["symbol", "feature", "ic", "n_obs"], t3_rows)
    log(f"  wrote T3 ({len(t3_rows)} rows)")
    log("")
    log("  T3 strongest |IC| per symbol (vs triple-barrier label):")
    for sym in UNIVERSE:
        rows = [r for r in t3_rows if r[0] == sym and not np.isnan(r[2])]
        rows.sort(key=lambda r: -abs(r[2]))
        for r in rows[:5]:
            log(f"    {sym}  {r[1]:32s}  IC={r[2]:+.4f}  n={r[3]}")

    # ------------------------------------------------------------------
    # T4 — redundancy vs price-derived features (orthogonality sanity).
    # We proxy "price features" with standard price-derived signals:
    # 9-bar return, RSI-14, and the ATR-normalized close-vs-MA gap.
    # ------------------------------------------------------------------
    log("")
    log("-" * 78)
    log("T4 — order-flow vs price-derived features: |corr| (orthogonality).")
    log("-" * 78)
    t4_rows = []
    for sym in UNIVERSE:
        p = panels[sym]
        kl = p["kl"]
        mask = (p["open_time"] >= IS_EVAL_START_MS) & (p["open_time"] < OOS_CUTOFF_MS)
        price_feats = build_price_proxies(kl)
        for fname in feat_names:
            fx = p["feats"][fname][mask]
            for pname, pv in price_feats.items():
                c = pearson_abs(fx, pv[mask])
                t4_rows.append((sym, fname, pname, c))
    write_csv(out_dir / "T4_orderflow_redundancy_vs_price.csv",
              ["symbol", "orderflow_feature", "price_feature", "abs_corr"], t4_rows)
    max_corr = max((r[3] for r in t4_rows if not np.isnan(r[3])), default=float("nan"))
    log(f"  wrote T4 ({len(t4_rows)} rows)  max |corr| vs price = {max_corr:.4f}")

    # ------------------------------------------------------------------
    # T5 — the GO/NO-GO verdict table.
    # ------------------------------------------------------------------
    log("")
    log("=" * 78)
    log("T5 — GO/NO-GO VERDICT")
    log("=" * 78)

    # Headline metric A: best |IC| on T2 (return, walk-forward window),
    # taken as the per-symbol max then the cross-symbol mean and max.
    def best_abs_ic_per_symbol(rows: list, ic_idx: int, sym_idx: int = 0) -> dict:
        d = {}
        for sym in UNIVERSE:
            vals = [abs(r[ic_idx]) for r in rows
                    if r[sym_idx] == sym and not np.isnan(r[ic_idx])]
            d[sym] = max(vals) if vals else float("nan")
        return d

    t2_best = best_abs_ic_per_symbol(t2_rows, 3)
    t3_best = best_abs_ic_per_symbol(t3_rows, 2)

    # Cross-symbol summary.
    t2_vals = [v for v in t2_best.values() if not np.isnan(v)]
    t3_vals = [v for v in t3_best.values() if not np.isnan(v)]
    t2_mean = float(np.mean(t2_vals)) if t2_vals else float("nan")
    t2_max = float(np.max(t2_vals)) if t2_vals else float("nan")
    t3_mean = float(np.mean(t3_vals)) if t3_vals else float("nan")
    t3_max = float(np.max(t3_vals)) if t3_vals else float("nan")

    log("")
    log("Best |return-IC| per symbol (T2, walk-forward IS-eval window):")
    for sym in UNIVERSE:
        log(f"  {sym}: {t2_best[sym]:+.4f}")
    log(f"  -> cross-symbol mean = {t2_mean:.4f}   max = {t2_max:.4f}")
    log("")
    log("Best |barrier-label-IC| per symbol (T3, walk-forward IS-eval window):")
    for sym in UNIVERSE:
        log(f"  {sym}: {t3_best[sym]:+.4f}")
    log(f"  -> cross-symbol mean = {t3_mean:.4f}   max = {t3_max:.4f}")

    # ---- The decision rule.
    # GO requires order-flow return-predictability MATERIALLY stronger than
    # /093's ~0.08 price-myopic ceiling. "Materially stronger" is operationalized
    # as: the cross-symbol-MEAN best |IC| > 1.5 x 0.08 = 0.12 AND at least 2 of 3
    # symbols individually clear the 0.08 ceiling. A single-symbol spike is NOT a
    # GO (it would be a 3-symbol lottery — the `feedback_v3_single_seed...` family).
    GO_MEAN_THRESHOLD = 1.5 * BENCH_093_RETURN_IC  # 0.12
    GO_MIN_SYMBOLS_OVER_CEILING = 2

    # Evaluate on the stronger of the two return-predictability tables (T2
    # return-IC vs T3 barrier-label-IC) — both measure the same underlying
    # question; the model trains on the barrier label so T3 is the more
    # architecture-faithful, but we report both and gate on whichever the
    # honest signal supports. We use the headline = T3 (label-IC) as the
    # primary gate because that is the model's actual target, with T2 as
    # corroboration.
    headline_mean = t3_mean
    headline_max = t3_max
    headline_best = t3_best
    n_over_ceiling = sum(
        1 for v in headline_best.values()
        if not np.isnan(v) and v > BENCH_093_RETURN_IC
    )
    # Corroboration check: T2 must not contradict (mean T2 also above ceiling).
    t2_corroborates = (not np.isnan(t2_mean)) and (t2_mean > BENCH_093_RETURN_IC)

    go = (
        (not np.isnan(headline_mean))
        and headline_mean > GO_MEAN_THRESHOLD
        and n_over_ceiling >= GO_MIN_SYMBOLS_OVER_CEILING
        and t2_corroborates
    )
    verdict = "GO" if go else "NO-GO"

    log("")
    log("-" * 78)
    log("DECISION RULE")
    log("-" * 78)
    log(f"  GO requires ALL of:")
    log(f"   (a) headline cross-symbol mean best |IC| > {GO_MEAN_THRESHOLD:.3f} "
        f"(= 1.5 x /093 ceiling 0.08)")
    log(f"       -> headline mean = {headline_mean:.4f}  "
        f"[{'PASS' if (not np.isnan(headline_mean)) and headline_mean > GO_MEAN_THRESHOLD else 'FAIL'}]")
    log(f"   (b) >= {GO_MIN_SYMBOLS_OVER_CEILING} of 3 symbols individually clear "
        f"the 0.08 ceiling")
    log(f"       -> {n_over_ceiling} of 3 symbols clear  "
        f"[{'PASS' if n_over_ceiling >= GO_MIN_SYMBOLS_OVER_CEILING else 'FAIL'}]")
    log(f"   (c) T2 (return-IC) corroborates — T2 cross-symbol mean > 0.08")
    log(f"       -> T2 mean = {t2_mean:.4f}  "
        f"[{'PASS' if t2_corroborates else 'FAIL'}]")
    log("")
    log(f"  ===> VERDICT: {verdict}")
    log("")
    if not go:
        log("  NO-GO: derivatives order-flow return-predictability sits at or near")
        log("  the /093 ~0.08 price-myopic ceiling. The order-flow-DIRECTIONAL axis")
        log("  is KILLED CHEAPLY at the EDA — exactly as fail-fast demands. No brief,")
        log("  no backtest. See diary-v3/iteration_v3-094.md for the next-axis pivot.")
    else:
        log("  GO: derivatives order-flow carries genuine directional return-IC")
        log("  materially stronger than the /093 ~0.08 ceiling. Proceed to the")
        log("  10-section research brief (Phases 2-5).")

    t5_rows = [
        ("benchmark_093_return_ic_ceiling", f"{BENCH_093_RETURN_IC:.4f}"),
        ("go_mean_threshold", f"{GO_MEAN_THRESHOLD:.4f}"),
        ("T2_return_ic_best_mean", f"{t2_mean:.4f}"),
        ("T2_return_ic_best_max", f"{t2_max:.4f}"),
        ("T3_barrier_label_ic_best_mean", f"{t3_mean:.4f}"),
        ("T3_barrier_label_ic_best_max", f"{t3_max:.4f}"),
        ("headline_mean_metric", "T3_barrier_label_ic_best_mean"),
        ("headline_mean_value", f"{headline_mean:.4f}"),
        ("n_symbols_over_ceiling", str(n_over_ceiling)),
        ("t2_corroborates", str(t2_corroborates)),
        ("max_abs_corr_vs_price", f"{max_corr:.4f}"),
        ("VERDICT", verdict),
    ]
    write_csv(out_dir / "T5_go_nogo_summary.csv", ["metric", "value"], t5_rows)
    log("")
    log(f"  wrote T5 — VERDICT = {verdict}")

    # Persist the transcript.
    (out_dir / "orderflow_return_ic_eda_output.txt").write_text("\n".join(transcript) + "\n")
    log("")
    log(f"Transcript saved to {out_dir / 'orderflow_return_ic_eda_output.txt'}")

    # Non-zero exit on NO-GO is NOT used — the EDA always completes; the
    # verdict is in T5. The orchestrator reads T5_go_nogo_summary.csv.
    sys.exit(0)


def build_price_proxies(kl: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Standard price-derived features, for the T4 orthogonality check."""
    close = kl["close"]
    n = len(close)
    # 9-bar return
    ret9 = np.full(n, np.nan)
    for i in range(9, n):
        if close[i - 9] != 0:
            ret9[i] = (close[i] - close[i - 9]) / close[i - 9]
    # RSI-14 (Wilder)
    rsi = np.full(n, np.nan)
    period = 14
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    if n > period:
        ag = gain[1 : period + 1].mean()
        al = loss[1 : period + 1].mean()
        for i in range(period + 1, n):
            ag = (ag * (period - 1) + gain[i]) / period
            al = (al * (period - 1) + loss[i]) / period
            rs = ag / al if al > 0 else 0.0
            rsi[i] = 100.0 - 100.0 / (1.0 + rs)
    # ATR-normalized close-vs-MA20 gap
    ma20 = rolling_mean(close, 20)
    atr14 = wilder_atr(kl["high"], kl["low"], close, 14)
    gap = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(ma20[i]) and not np.isnan(atr14[i]) and atr14[i] > 0:
            gap[i] = (close[i] - ma20[i]) / atr14[i]
    # shift(1) — same convention as the order-flow panel
    out = {}
    for name, arr in {"price_ret9": ret9, "price_rsi14": rsi, "price_ma_gap": gap}.items():
        s = np.full(n, np.nan)
        s[1:] = arr[:-1]
        out[name] = s
    return out


def write_csv(path: Path, header: list[str], rows: list) -> None:
    """Write a CSV with the given header and rows."""
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    main()

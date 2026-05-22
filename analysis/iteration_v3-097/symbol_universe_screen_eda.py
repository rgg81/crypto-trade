"""iter-v3/097 — Phase-1 SYMBOL-UNIVERSE RE-SELECTION SCREEN — IS-only EDA.

THE AXIS UNDER TEST
-------------------
v3 has been locked to the BCH/LDO/TRX universe for all of cycles 1-4 (96
iterations).  The /096 GO/NO-GO EDA measured the within-symbol purged-CV
rank-IC of the 14-feature V3_FEATURE_COLUMNS stack vs the /059 triple-barrier
directional label and found:

    BCH within-symbol CV rank-IC = +0.02542   (thin)
    LDO within-symbol CV rank-IC = +0.17793   (genuine signal)
    TRX within-symbol CV rank-IC = +0.02907   (thin)

i.e. /059's OOS +0.58 is essentially carried by LDO alone.  BCH and TRX sit
barely above zero — the 14-feature -> label map on those two symbols is noise.

The user directive (memory feedback_v3_bold_research_mandate.md, 2026-05-18,
verbatim): "Let's keep grinding, focus on different symbols, features, pooled
models vs single models. ... You are free to select whatever symbol you like."
A thin feature->label IC on a symbol means that SYMBOL is wrong for the v3
framing — not that the space is worked.  LDO proves good-signal symbols exist.

So this EDA does the obvious next thing v3 has never done: screen the BROAD
allowed universe for the symbols where the EXISTING 14-feature stack already
carries genuine, IS-stable feature->label signal — LDO-like symbols — and
re-anchor the v3 universe onto them.

THE SCREEN
----------
For every candidate symbol in a wide universe of liquid Binance USDT perps
(the 22-symbol XS_UNIVERSE, which is by construction disjoint with
V3_EXCLUDED_SYMBOLS — the v1/v2 symbols + MKR):

  T2  WITHIN-SYMBOL purged 5-fold CV rank-IC
      Train a LightGBM (the /096 LGB_PARAMS, the v3-representative config) on
      4 of 5 purged folds, predict the held-out fold, measure Spearman rank-IC
      of the prediction vs the realized triple-barrier directional label.
      THIS IS THE HEADLINE — it is the SAME metric the /096 EDA used to
      diagnose BCH/LDO/TRX.  It measures: "does the existing 14-feature stack,
      under the v3 per-symbol architecture, carry genuine multivariate
      feature->label signal on this symbol?"

  T3  SUB-PERIOD IC SIGN-CONSISTENCY
      Split each symbol's post-burn-in IS span into 3 equal sequential thirds.
      In each third, measure the same purged-CV-style rank-IC (a single
      train/predict on a 2/3-vs-1/3 chronological split within the third).
      A genuine-signal symbol has a POSITIVE IC in all 3 thirds (or at worst
      2 of 3, with the third near zero) — i.e. the signal is not a single-
      regime artifact.  A symbol whose IC flips sign across thirds is NOT
      genuine-signal regardless of its full-span T2 number.

  T4  per-feature univariate IC + sign-consistency-across-thirds (diagnostic)
      For the top symbols, report each of the 14 features' univariate rank-IC
      and whether its sign is stable across the 3 thirds — the texture behind
      the headline (which features carry the symbol).

RANKING + SELECTION (pre-registered, decided BEFORE running)
------------------------------------------------------------
  THE HEADLINE METRIC is the T2 within-symbol purged-CV rank-IC — the SAME
  metric the /096 EDA used to diagnose BCH (+0.025) / LDO (+0.178) / TRX
  (+0.029).  The band assignment is on the headline metric:

  GENUINE-SIGNAL  iff  T2 within-symbol CV rank-IC >= +0.060  (clearly above
                       the +0.025 thin-signal floor; the LDO-like range, ~2.4x
                       the BCH/TRX floor).
  THIN-SIGNAL     iff  T2 within-symbol CV rank-IC < +0.040  (BCH/TRX band).
  BORDERLINE      the [+0.040, +0.060) band — reported, not selected as a
                  primary re-anchor symbol.

  T3 (sub-period sign-consistency) is a STABILITY ANNOTATION on the headline,
  NOT a hard band gate.  A v3 symbol's edge is empirically regime-concentrated
  (the /096 IS-dominance finding) — every screened symbol, BCH/LDO/TRX
  included, carries its signal in 1-2 of 3 thirds.  Demoting an unambiguous
  +0.178-IC symbol to BORDERLINE because one third dips negative would
  conflate "regime-concentrated genuine signal" with "thin signal" — they are
  different things.  T3 is reported as `regime_stability` (STABLE = >=2 of 3
  thirds positive AND worst third >= the -0.030 floor; CONCENTRATED otherwise)
  so the brief can pre-register a regime-robustness falsifier WITHOUT it
  collapsing the headline screen.

  The re-anchored v3 universe = the GENUINE-SIGNAL symbols (headline CV-IC
  >= +0.060), ranked by T2 IC.  LDO is kept iff it re-screens GENUINE.
  BCH/TRX are dropped iff they re-screen THIN (the /096 finding, re-confirmed
  here on the full-IS-span purged-CV metric).

NO-CHEATING
-----------
  - OOS_CUTOFF_MS = 1742774400000 (2025-03-24).  EVERY row used here has
    open_time < OOS_CUTOFF_MS.  OOS is NEVER touched.
  - 24-month listing burn-in dropped per symbol (TRAINING_MONTHS=24) — matches
    the runner's per-symbol warmup.  The label is computed on the FULL panel
    so the forward scan can see post-burn-in bars, then rows are restricted to
    [first_kline + 24mo, OOS_CUTOFF_MS).  This is the runner's actual
    walk-forward evaluation span (feedback_v3_eda_walkforward_faithful.md).
  - The triple-barrier label uses the EXACT /059 production params: ATR
    multipliers (TP=2.0, SL=1.0), timeout 10080 min = 21 candles, fee 0.1%,
    label_mode triple_barrier — replicated from
    src/crypto_trade/strategies/ml/labeling.py:label_trades.  The replication
    is byte-identical to the /096 EDA's triple_barrier_label (validated there).
  - The 14-feature stack is V3_FEATURE_COLUMNS_TOP_N (the /059 anchor).
  - Purged 5-fold CV with a 22-candle embargo (EMBARGO_CANDLES = 10080//480+1)
    dropped from BOTH sides of each test fold — no label-window leakage.

This is a Phase-1 screening EDA.  Its CSVs (T1-T5) drive the brief's Section 2
and its pre-registered falsifiers.  It does NOT run a backtest — the backtest
(the re-anchored-universe build) is the Phase-6 deliverable.

T6 (a separate committed companion artifact, T6_seed_robustness.csv) re-runs
the headline within-symbol CV-IC for the top tier under 4 LightGBM seeds
(42, 7, 99, 2024).  It confirms the GENUINE / THIN split is NOT a seed lottery:
LDO/GALA hold +0.171/+0.128 (seed std 0.019/0.016) and clear the +0.040 floor
on ALL 4 seeds, vs BCH/TRX +0.025/+0.028 (std 0.004/0.006) — the headline
ranking is seed-stable.  T6 is produced by the inline snippet documented in
the iter-v3/097 EDA commit message; this module produces T1-T5.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    print("lightgbm not importable", file=sys.stderr)
    raise

# --------------------------------------------------------------------------
# Immutable constants (NO CHEATING)
# --------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080  # 21 candles at 8h
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
EMBARGO_CANDLES = 22  # 10080 // 480 + 1
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-097")

# The candidate universe = the 22-symbol XS_UNIVERSE (already has features on
# disk).  By construction this is DISJOINT with V3_EXCLUDED_SYMBOLS (the v1/v2
# symbols BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/DOGE/NEAR + MKR) — every symbol
# below is a legal v3 candidate.  The disjointness is asserted at runtime.
CANDIDATE_UNIVERSE: tuple[str, ...] = (
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

# V3_EXCLUDED_SYMBOLS — copied from features_v3/__init__.py for the
# disjointness assertion (the EDA is standalone; it does not import src/).
V3_EXCLUDED_SYMBOLS: tuple[str, ...] = (
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

# The /059 canonical 14-feature stack (V3_FEATURE_COLUMNS_TOP_N).
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

# Pre-registered selection thresholds (decided BEFORE running)
GENUINE_IC_MIN = 0.060  # >= +0.060 within-symbol CV IC -> GENUINE-SIGNAL band
THIN_IC_MAX = 0.040  # < +0.040 -> THIN-SIGNAL band (BCH/TRX live here)
SUBPERIOD_NEG_FLOOR = -0.030  # no third may be more negative than this
SUBPERIOD_MIN_POSITIVE = 2  # >= 2 of 3 thirds must be positive

# v3-representative LightGBM config (identical to the /096 GO/NO-GO EDA so the
# screen is comparable to the /096 BCH/LDO/TRX diagnosis).
LGB_PARAMS = dict(
    objective="binary",
    n_estimators=200,
    num_leaves=31,
    max_depth=5,
    learning_rate=0.05,
    min_child_samples=40,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=42,
    verbose=-1,
    n_jobs=2,
)


# ---------------------------------------------------------------------------
# Triple-barrier labeling — byte-faithful replication of labeling.py and the
# /096 EDA's triple_barrier_label (validated against production there).
# ---------------------------------------------------------------------------
def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with added columns tb_label (+1 long / -1 short) and tb_pnl.

    Replicates the /059 production triple-barrier rule for one symbol:
      - ATR distance: TP = 2.0*ATR, SL = 1.0*ATR  (ATR in price units)
      - timeout 21 candles
      - label = side whose TP is hit first; if neither TP, sign of fwd return
    natr_21_raw is NATR-as-percentage -> ATR_price = natr/100 * close.
    """
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
    pnls = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        tp_dist = atr * TP_MULT
        sl_dist = atr * SL_MULT
        long_tp = entry + tp_dist
        long_sl = entry - sl_dist
        short_tp = entry - tp_dist
        short_sl = entry + sl_dist
        deadline = close_time[i] + timeout_ms

        long_result = 0  # 0 pending, 1 tp, -1 sl, -2 timeout
        short_result = 0
        long_step = -1
        short_step = -1
        last_close = entry

        j = i + 1
        while j < n:
            if close_time[j] > deadline:
                if long_result == 0:
                    long_result, long_step = -2, j
                if short_result == 0:
                    short_result, short_step = -2, j
                break
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_result == 0:
                if lo <= long_sl:
                    long_result, long_step = -1, j
                elif h >= long_tp:
                    long_result, long_step = 1, j
            if short_result == 0:
                if h >= short_sl:
                    short_result, short_step = -1, j
                elif lo <= short_tp:
                    short_result, short_step = 1, j
            if long_result != 0 and short_result != 0:
                break
            j += 1
        else:
            if long_result == 0:
                long_result, long_step = -2, n
            if short_result == 0:
                short_result, short_step = -2, n

        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0
        tp_pnl_pct = tp_dist / entry * 100.0
        sl_pnl_pct = sl_dist / entry * 100.0

        def side_pnl(result: int, signed_fwd: float) -> float:
            if result == 1:
                return tp_pnl_pct - FEE_PCT
            if result == -1:
                return -sl_pnl_pct - FEE_PCT
            return signed_fwd - FEE_PCT

        long_pnl = side_pnl(long_result, fwd_ret)
        short_pnl = side_pnl(short_result, -fwd_ret)

        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1

        labels[i] = lab
        pnls[i] = long_pnl if lab == 1 else short_pnl

    out["tb_label"] = labels
    out["tb_pnl"] = pnls
    return out


def load_symbol_is(symbol: str) -> pd.DataFrame | None:
    """Load a symbol's feature parquet, apply the 24-month listing burn-in,
    restrict strictly to open_time < OOS_CUTOFF_MS (IS-only), compute the
    triple-barrier label.  Returns None if the parquet is missing.

    The burn-in + IS cutoff reproduce the runner's per-symbol walk-forward
    evaluation span exactly (feedback_v3_eda_walkforward_faithful.md): the
    runner only trades the post-24-month-warmup bars, and never trades OOS.
    """
    path = DATA_DIR / f"{symbol}_8h_features.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df.sort_values("open_time").reset_index(drop=True)
    first_ms = int(df["open_time"].min())
    burnin_end = first_ms + TRAINING_MONTHS * 30 * 24 * 60 * 60 * 1000
    # Label on the FULL panel so the forward scan sees post-burn-in bars,
    # then keep only [burnin_end, OOS_CUTOFF_MS) — the runner's IS span.
    df = triple_barrier_label(df)
    is_mask = (df["open_time"] >= burnin_end) & (df["open_time"] < OOS_CUTOFF_MS)
    isd = df[is_mask].copy()
    isd["symbol"] = symbol
    return isd.reset_index(drop=True)


def rank_ic(pred: np.ndarray, target: np.ndarray) -> float:
    """Spearman rank-IC between prediction and target. NaN if < 30 samples."""
    if len(pred) < 30:
        return float("nan")
    s1 = pd.Series(pred).rank()
    s2 = pd.Series(target).rank()
    c = s1.corr(s2)
    return float(c) if pd.notna(c) else float("nan")


def purged_kfold_indices(n: int, k: int, embargo: int):
    """Yield (train_idx, test_idx) for a purged k-fold over a single
    time-ordered symbol — embargo rows dropped from BOTH sides of each test
    fold so no training label's 21-bar forward window overlaps a test row."""
    fold_sizes = np.full(k, n // k, dtype=int)
    fold_sizes[: n % k] += 1
    current = 0
    bounds = []
    for fs in fold_sizes:
        bounds.append((current, current + fs))
        current += fs
    for lo, hi in bounds:
        test_idx = np.arange(lo, hi)
        train_mask = np.ones(n, dtype=bool)
        train_mask[max(0, lo - embargo) : min(n, hi + embargo)] = False
        train_idx = np.where(train_mask)[0]
        yield train_idx, test_idx


def within_symbol_cv_ic(d: pd.DataFrame) -> tuple[float, int]:
    """Purged 5-fold CV rank-IC of the 14-feature LightGBM vs tb_label.

    THE HEADLINE METRIC — identical to the /096 EDA's within-symbol benchmark.
    Returns (mean_rank_ic, n_folds_used).
    """
    X = d[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
    y = d["y"].to_numpy(dtype=int)
    tgt = d["tb_label"].to_numpy(dtype=np.float64)  # +1/-1 directional
    fold_ics: list[float] = []
    for tr, te in purged_kfold_indices(len(d), 5, EMBARGO_CANDLES):
        if len(np.unique(y[tr])) < 2 or len(te) < 30:
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(X[tr], y[tr])
        p = model.predict_proba(X[te])[:, 1]
        ic = rank_ic(p, tgt[te])
        if pd.notna(ic):
            fold_ics.append(ic)
    if not fold_ics:
        return float("nan"), 0
    return float(np.nanmean(fold_ics)), len(fold_ics)


def subperiod_ics(d: pd.DataFrame) -> list[float]:
    """Rank-IC of the 14-feature LightGBM in each of 3 equal sequential thirds
    of the symbol's IS span — the sign-consistency / single-regime test.

    Within each third, a chronological 2/3-train -> 1/3-predict split (the
    last 1/3 of the third is the test segment; an embargo gap purges the
    label window).  A genuine-signal symbol scores positive in all 3 thirds.
    """
    n = len(d)
    out: list[float] = []
    bounds = [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]
    for lo, hi in bounds:
        seg = d.iloc[lo:hi].reset_index(drop=True)
        m = len(seg)
        if m < 90:  # need a workable train + >=30-row test
            out.append(float("nan"))
            continue
        cut = (2 * m) // 3
        tr_idx = np.arange(0, max(0, cut - EMBARGO_CANDLES))
        te_idx = np.arange(cut, m)
        Xseg = seg[list(V3_FEATURE_COLUMNS)].to_numpy(dtype=np.float64)
        yseg = seg["y"].to_numpy(dtype=int)
        tgt = seg["tb_label"].to_numpy(dtype=np.float64)
        if len(tr_idx) < 60 or len(te_idx) < 30 or len(np.unique(yseg[tr_idx])) < 2:
            out.append(float("nan"))
            continue
        model = lgb.LGBMClassifier(**LGB_PARAMS)
        model.fit(Xseg[tr_idx], yseg[tr_idx])
        p = model.predict_proba(Xseg[te_idx])[:, 1]
        out.append(rank_ic(p, tgt[te_idx]))
    return out


def regime_stability(sub: list[float]) -> tuple[bool, int, float]:
    """Map a sub-period IC list -> (is_stable, n_thirds_positive, worst_third).

    is_stable: >= 2 of 3 thirds positive AND no third below the -0.030 floor.
    This is a STABILITY ANNOTATION — it does NOT gate the headline band.
    """
    valid_sub = [v for v in sub if pd.notna(v)]
    n_pos = sum(1 for v in valid_sub if v > 0)
    worst = min(valid_sub) if valid_sub else float("nan")
    is_stable = (
        len(valid_sub) >= 2
        and n_pos >= SUBPERIOD_MIN_POSITIVE
        and (pd.isna(worst) or worst >= SUBPERIOD_NEG_FLOOR)
    )
    return is_stable, n_pos, worst


def classify(t2_ic: float) -> str:
    """Map the headline within-symbol CV-IC -> band.

    band in {GENUINE, BORDERLINE, THIN, INSUFFICIENT}.  The band is on the
    HEADLINE metric ONLY (the /096-comparable purged-CV rank-IC) — sub-period
    sign-consistency is a separate annotation, not a band input.
    """
    if pd.isna(t2_ic):
        return "INSUFFICIENT"
    if t2_ic >= GENUINE_IC_MIN:
        return "GENUINE"
    if t2_ic < THIN_IC_MAX:
        return "THIN"
    return "BORDERLINE"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/097 Phase-1 SYMBOL-UNIVERSE RE-SELECTION SCREEN — IS-only EDA")
    print("Headline: within-symbol purged-5-fold-CV rank-IC of the 14-feature")
    print("V3_FEATURE_COLUMNS stack vs the /059 triple-barrier directional label.")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row IS-only.")
    print("=" * 78)

    # ---- disjointness assertion (NO CHEATING — no v1/v2 symbol, no MKR) ----
    overlap = set(CANDIDATE_UNIVERSE) & set(V3_EXCLUDED_SYMBOLS)
    assert not overlap, f"candidate universe overlaps V3_EXCLUDED_SYMBOLS: {sorted(overlap)}"
    print(
        f"\nDisjointness check: {len(CANDIDATE_UNIVERSE)} candidates, "
        f"0 overlap with V3_EXCLUDED_SYMBOLS ({len(V3_EXCLUDED_SYMBOLS)} excluded). PASS."
    )

    # ---- load every candidate's IS panel ----
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    for sym in CANDIDATE_UNIVERSE:
        d = load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet MISSING — skipped")
            continue
        d["y"] = (d["tb_label"] == 1).astype(int)
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["tb_pnl"]).reset_index(drop=True)
        if len(d) < 300:
            print(f"  {sym}: only {len(d)} IS rows post-burn-in — skipped (insufficient)")
            continue
        panels[sym] = d
        t1_rows.append(
            {
                "symbol": sym,
                "is_rows": len(d),
                "is_first": str(pd.to_datetime(d["open_time"].min(), unit="ms").date()),
                "is_last": str(pd.to_datetime(d["open_time"].max(), unit="ms").date()),
                "long_label_frac": round(float(d["y"].mean()), 4),
                "mean_tb_pnl": round(float(d["tb_pnl"].mean()), 4),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_candidate_is_panels.csv", index=False)
    print(f"\nT1 — candidate IS panels (post-24mo-burn-in, IS-only): {len(panels)} screened")
    print(t1.to_string(index=False))

    # ---- T2: within-symbol CV rank-IC (the headline) ----
    print("\nT2 — WITHIN-symbol purged 5-fold CV rank-IC (headline screen):")
    t2_rows = []
    for sym in panels:
        ic, nf = within_symbol_cv_ic(panels[sym])
        t2_rows.append({"symbol": sym, "within_cv_rank_ic": round(ic, 5), "n_folds": nf})
        print(f"  {sym:10s}: within-symbol CV rank-IC = {ic:+.5f}  ({nf} folds)")
    t2 = pd.DataFrame(t2_rows).sort_values(
        "within_cv_rank_ic", ascending=False, na_position="last"
    )
    t2.to_csv(OUT / "T2_within_symbol_cv_ic.csv", index=False)

    # ---- T3: sub-period sign-consistency ----
    print("\nT3 — SUB-PERIOD IC sign-consistency (3 sequential thirds of each IS span):")
    t3_rows = []
    for sym in panels:
        sub = subperiod_ics(panels[sym])
        valid = [v for v in sub if pd.notna(v)]
        n_pos = sum(1 for v in valid if v > 0)
        t3_rows.append(
            {
                "symbol": sym,
                "ic_third_1": round(sub[0], 5) if pd.notna(sub[0]) else np.nan,
                "ic_third_2": round(sub[1], 5) if pd.notna(sub[1]) else np.nan,
                "ic_third_3": round(sub[2], 5) if pd.notna(sub[2]) else np.nan,
                "n_thirds_positive": n_pos,
                "worst_third_ic": round(min(valid), 5) if valid else np.nan,
            }
        )
        print(
            f"  {sym:10s}: thirds = "
            f"[{sub[0]:+.4f}, {sub[1]:+.4f}, {sub[2]:+.4f}]  "
            f"({n_pos}/3 positive)"
        )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_subperiod_sign_consistency.csv", index=False)

    # ---- T5: ranked screen + classification + re-anchored universe ----
    sub_lookup = {r["symbol"]: r for r in t3_rows}
    t5_rows = []
    for _, r in t2.iterrows():
        sym = r["symbol"]
        t2_ic = float(r["within_cv_rank_ic"])
        sr = sub_lookup[sym]
        sub = [sr["ic_third_1"], sr["ic_third_2"], sr["ic_third_3"]]
        band = classify(t2_ic)
        is_stable, n_pos, worst = regime_stability(sub)
        t5_rows.append(
            {
                "symbol": sym,
                "within_cv_rank_ic": round(t2_ic, 5),
                "band": band,
                "ic_vs_thin_floor_ratio": round(t2_ic / 0.025, 2) if pd.notna(t2_ic) else np.nan,
                "n_thirds_positive": n_pos,
                "worst_third_ic": worst,
                "regime_stability": "STABLE" if is_stable else "CONCENTRATED",
            }
        )
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_ranked_screen.csv", index=False)

    print("\n" + "=" * 78)
    print("T5 — RANKED SCREEN (descending within-symbol CV rank-IC)")
    print("=" * 78)
    print(t5.to_string(index=False))

    genuine = t5[t5["band"] == "GENUINE"]["symbol"].tolist()
    borderline = t5[t5["band"] == "BORDERLINE"]["symbol"].tolist()
    thin = t5[t5["band"] == "THIN"]["symbol"].tolist()

    # ---- T4: per-feature univariate IC texture for the GENUINE symbols ----
    diag_syms = genuine if genuine else t5["symbol"].tolist()[:4]
    print(f"\nT4 — per-feature univariate rank-IC (texture for: {', '.join(diag_syms)}):")
    t4_rows = []
    for sym in diag_syms:
        d = panels[sym]
        n = len(d)
        bounds = [(0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)]
        for feat in V3_FEATURE_COLUMNS:
            full_ic = rank_ic(
                d[feat].to_numpy(dtype=np.float64),
                d["tb_label"].to_numpy(dtype=np.float64),
            )
            third_ics = []
            for lo, hi in bounds:
                seg = d.iloc[lo:hi]
                third_ics.append(
                    rank_ic(
                        seg[feat].to_numpy(dtype=np.float64),
                        seg["tb_label"].to_numpy(dtype=np.float64),
                    )
                )
            signs = {np.sign(v) for v in third_ics if pd.notna(v) and v != 0}
            t4_rows.append(
                {
                    "symbol": sym,
                    "feature": feat,
                    "univariate_ic_full": round(full_ic, 5) if pd.notna(full_ic) else np.nan,
                    "ic_third_1": round(third_ics[0], 5) if pd.notna(third_ics[0]) else np.nan,
                    "ic_third_2": round(third_ics[1], 5) if pd.notna(third_ics[1]) else np.nan,
                    "ic_third_3": round(third_ics[2], 5) if pd.notna(third_ics[2]) else np.nan,
                    "sign_consistent_across_thirds": len(signs) <= 1,
                }
            )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_per_feature_ic_texture.csv", index=False)
    print(f"  (written to T4_per_feature_ic_texture.csv — {len(t4)} rows)")

    # ---- verdict ----
    stable_set = set(t5[t5["regime_stability"] == "STABLE"]["symbol"].tolist())
    print("\n" + "=" * 78)
    print("SCREEN VERDICT — re-anchored v3 universe")
    print("=" * 78)
    print(f"  Headline metric = within-symbol purged-5-fold-CV rank-IC (the /096 metric).")
    print(f"  GENUINE-SIGNAL  (CV IC >= +{GENUINE_IC_MIN:.3f}): {genuine}")
    print(f"  BORDERLINE      (CV IC in [+{THIN_IC_MAX:.3f}, +{GENUINE_IC_MIN:.3f})): {borderline}")
    print(f"  THIN-SIGNAL     (CV IC < +{THIN_IC_MAX:.3f}): {thin}")
    print("  ----")
    for legacy in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        row = t5[t5["symbol"] == legacy]
        if not row.empty:
            ic = float(row["within_cv_rank_ic"].iloc[0])
            print(
                f"  legacy {legacy:10s}: CV IC = {ic:+.5f}  band = {row['band'].iloc[0]}"
                f"  ({row['regime_stability'].iloc[0]})"
            )
    print("  ----")
    print("  GENUINE-SIGNAL symbols with regime annotation:")
    for sym in genuine:
        row = t5[t5["symbol"] == sym].iloc[0]
        print(
            f"    {sym:10s}: CV IC {float(row['within_cv_rank_ic']):+.5f}  "
            f"({float(row['ic_vs_thin_floor_ratio']):.1f}x the +0.025 thin floor)  "
            f"{row['regime_stability']}"
        )
    print("  ----")
    print(f"  Proposed re-anchored v3 universe = the GENUINE-SIGNAL symbols: {genuine}")
    print(f"  (regime-STABLE genuine symbols: {sorted(set(genuine) & stable_set)})")
    print("=" * 78)


if __name__ == "__main__":
    main()

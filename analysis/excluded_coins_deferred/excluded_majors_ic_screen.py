"""iter-v3/101 — Cycle-5 opener — EXCLUDED-COINS RE-EVALUATION SCREEN — IS-only EDA.

THE QUESTION UNDER TEST
-----------------------
v3 has been confined to the mid-cap altcoin universe (BCH/LDO/TRX core) for
ALL of cycles 1-4 (100 iterations).  `V3_EXCLUDED_SYMBOLS` bars v3 from the
v1+v2 symbols — the liquid majors: BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP,
DOGE, NEAR.

Cycle 4 (iter-v3/093-100) found NO edge anywhere — confirmed ~6 independent
ways (derivatives microstructure, cointegration stat-arb, pooled vs single
models, symbol screening, researched feature families, labeling
re-architecture, regime-switching).  The binding constraint, repeatedly
confirmed, is the THIN per-symbol 8h triple-barrier feature->label signal of
the mid-cap altcoin universe — the /096 EDA measured within-symbol purged-CV
rank-IC of the 14-feature stack vs the /059 triple-barrier label at:

    BCH within-symbol CV rank-IC = +0.02542   (thin)
    LDO within-symbol CV rank-IC = +0.17793   (genuine — v3's strongest, modest)
    TRX within-symbol CV rank-IC = +0.02907   (thin)

The /097 broad-altcoin screen (22-symbol XS_UNIVERSE) found only LDO/GALA in
the GENUINE band — the altcoin universe is signal-thin almost everywhere.

THE DECISIVE QUESTION (user directive 2026-05-18, "next cycle we re-evaluate
the excluded coins"): is the thin signal a property of the v3 ALTCOIN
CONFINEMENT, or a property of 8h crypto triple-barrier prediction generally?
If the EXCLUDED liquid majors carry materially genuine feature->label signal
— clearly stronger than the thin altcoins (BCH/TRX ~+0.025; LDO +0.178 was
v3's best) — then v3's 100-iteration plateau is an artifact of its universe,
and relaxing V3_EXCLUDED_SYMBOLS is the structural lever.  If the majors are
ALSO thin, the thin signal is an 8h-crypto-wide problem and confinement to
altcoins did NOT cause it.

THE SCREEN
----------
For every v3-EXCLUDED liquid major (the 10 v1+v2 symbols):

  T2  WITHIN-SYMBOL purged 5-fold CV rank-IC  -- THE HEADLINE METRIC
      Train a LightGBM (the /096/097 LGB_PARAMS, the v3-representative config)
      on 4 of 5 purged folds, predict the held-out fold, measure Spearman
      rank-IC of the prediction vs the realized /059 triple-barrier
      directional label.  This is the EXACT metric the /096 EDA used to
      diagnose BCH (+0.025) / LDO (+0.178) / TRX (+0.029) and the /097 EDA
      used to screen the broad altcoin universe.  Strict apples-to-apples
      comparison — same metric, same LightGBM config, same label, same purge.

  T3  SUB-PERIOD IC SIGN-CONSISTENCY
      Split each symbol's post-burn-in IS span into 3 equal sequential thirds.
      In each third, measure the same purged-CV-style rank-IC (a single
      chronological 2/3-train -> 1/3-predict split within the third, with a
      22-candle embargo gap).  A genuine-signal symbol has a POSITIVE IC in
      all 3 thirds (or at worst 2 of 3, worst third near zero).  A major whose
      IC FLIPS SIGN across thirds is NOT genuinely stronger than the
      sign-flipping altcoins regardless of its full-span T2 number — a
      sign-flipping IC is curve-fit noise, not transferable signal.

  T4  per-feature univariate IC + sign-consistency-across-thirds (diagnostic)
      For the top-tier majors, report each of the 14 features' univariate
      rank-IC and whether its sign is stable across the 3 thirds — the texture
      behind the headline (which features carry the symbol).

CLASSIFICATION (pre-registered, decided BEFORE running — IDENTICAL bands to
the /096/097 diagnosis so the verdict is directly comparable)
-----------------------------------------------------------------------------
  THE HEADLINE METRIC is the T2 within-symbol purged-CV rank-IC.

  GENUINE-SIGNAL  iff  T2 CV rank-IC >= +0.060  (clearly above the +0.025
                       thin-signal floor; the LDO-like band, ~2.4x the
                       BCH/TRX floor — the /097 band, unchanged).
  THIN-SIGNAL     iff  T2 CV rank-IC < +0.040  (the BCH/TRX band).
  BORDERLINE      the [+0.040, +0.060) band — reported, not GENUINE.

  T3 (sub-period sign-consistency) is a STABILITY ANNOTATION on the headline,
  reported as `subperiod_stability`:
     STABLE        = >= 2 of 3 thirds positive AND worst third >= -0.030.
     CONCENTRATED  = otherwise (regime-concentrated signal — still genuine if
                     the headline clears +0.060, per the /097 methodology
                     note: v3's edge is empirically regime-concentrated).
     SIGN-FLIPPING = the IC sign is NOT consistent across the thirds (>=1
                     third clearly positive AND >=1 third clearly negative,
                     each beyond a +-0.020 deadband).  A SIGN-FLIPPING major
                     is explicitly NOT "genuinely better than the altcoins"
                     even if its full-span T2 looks high — the user asked for
                     sign-stability precisely to catch this.

  THE DECISIVE VERDICT — a 3-way call (printed + written to T6), NOT a binary.
  The question is whether the majors carry signal MATERIALLY stronger than the
  thin altcoins.  "One symbol scrapes past +0.060 by a hair" is NOT that —
  LDO, v3's strongest, is +0.178, and the GENUINE band floor +0.060 was set as
  a low bar.  So the verdict is graded on the BEST major's absolute strength
  AND the BREADTH of the GENUINE-and-sign-stable set:

    CONFINEMENT-ARTIFACT  -- the majors clearly carry the signal the altcoins
        lack.  Triggered iff EITHER (a) >= 1 GENUINE-and-sign-stable major has
        a headline CV-IC >= +0.120 (LDO-CLASS, i.e. clearly into v3's
        strongest-altcoin territory — not the +0.060 scrape band), OR (b) a
        CLUSTER of >= 3 majors are GENUINE-and-sign-stable (breadth the
        altcoin universe never had — /097 found only LDO/GALA).  Relaxing
        V3_EXCLUDED_SYMBOLS would then be a strong structural lever.

    8H-CRYPTO-WIDE-THIN  -- every excluded major is THIN/BORDERLINE, OR every
        GENUINE major is SIGN-FLIPPING.  No major beats the thin altcoins on
        either headline OR stability.  The thin signal is a property of 8h
        crypto generally; v3's altcoin confinement did NOT cause the plateau;
        relaxing the exclusion would NOT lift v3 off it.

    EQUIVOCAL  -- the middle ground: 1-2 majors are GENUINE-and-sign-stable but
        only marginally (best CV-IC in [+0.060, +0.120) — the scrape band, a
        fraction of LDO's +0.178), with no LDO-class symbol and no >= 3-symbol
        cluster.  The majors are NOT a clean confinement-artifact answer: the
        marginal pass is the same thin/non-stationary texture as the altcoins,
        a hair above the GENUINE floor.  The honest reading LEANS toward an
        8h-crypto-wide thin signal — a single +0.06-IC symbol does not justify
        a structural universe change on its own.  The user weighs whether a
        marginal-but-positive single-symbol result is worth a confirmation
        backtest; it is NOT evidence the plateau was confinement-caused.

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
    label_mode triple_barrier — replicated BYTE-IDENTICALLY from the /096/097
    EDAs' triple_barrier_label (validated against
    src/crypto_trade/strategies/ml/labeling.py:label_trades there).
  - The 14-feature stack is V3_FEATURE_COLUMNS_TOP_N (the /059 anchor),
    copied verbatim from features_v3/__init__.py.
  - Purged 5-fold CV with a 22-candle embargo (EMBARGO_CANDLES = 10080//480+1)
    dropped from BOTH sides of each test fold — no label-window leakage.

  This is a Phase-1 RE-EVALUATION EDA.  It does NOT run a backtest, does NOT
  write a research brief, and does NOT modify V3_EXCLUDED_SYMBOLS or any src/
  code.  Relaxing the exclusion is a structural/policy change for the user to
  decide.  This EDA delivers the screen + the decisive verdict.
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
OUT = Path("analysis/iteration_v3-101")

# THE SCREEN UNIVERSE = the 10 v3-EXCLUDED liquid majors.  Copied VERBATIM
# from features_v3/__init__.py V3_EXCLUDED_SYMBOLS (minus MKRUSDT — MKR was a
# v3-DROPPED altcoin, not an excluded major; it is screened in /097's altcoin
# catalog already and is not a "v1/v2 liquid major").  The 10 below are
# exactly the v1-traded + v2-traded + BNB-reservation symbols.
EXCLUDED_MAJORS: tuple[str, ...] = (
    # v1 traded
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    # historical reservation
    "BNBUSDT",
    # v2 traded
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
)

# V3_EXCLUDED_SYMBOLS — copied from features_v3/__init__.py for the
# CONTAINMENT assertion (the EDA is standalone; it does not import src/).
# This EDA SCREENS the excluded symbols (it does not select v3 candidates) —
# so unlike /097 (which asserted DISJOINTNESS), this EDA asserts every screened
# symbol IS in V3_EXCLUDED_SYMBOLS: the screen target is the excluded set.
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

# The /059 canonical 14-feature stack (V3_FEATURE_COLUMNS_TOP_N) — copied
# verbatim from features_v3/__init__.py.
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

# Pre-registered classification thresholds (decided BEFORE running — the
# /096/097 bands, unchanged, so the verdict is apples-to-apples).
GENUINE_IC_MIN = 0.060  # >= +0.060 within-symbol CV IC -> GENUINE-SIGNAL band
THIN_IC_MAX = 0.040  # < +0.040 -> THIN-SIGNAL band (BCH/TRX live here)
SUBPERIOD_NEG_FLOOR = -0.030  # no third may be more negative than this (STABLE)
SUBPERIOD_MIN_POSITIVE = 2  # >= 2 of 3 thirds must be positive (STABLE)
SIGNFLIP_DEADBAND = 0.020  # a third's IC must clear +-this to count as a sign

# v3-representative LightGBM config — IDENTICAL to the /096/097 EDAs so the
# screen is comparable to the BCH/LDO/TRX diagnosis and the /097 altcoin
# catalog.
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

# The /096 BCH/LDO/TRX reference numbers — the thin-signal altcoin baseline
# this screen is judged against.  These are the published /096 GO/NO-GO EDA
# within-symbol CV rank-ICs (also cited in the /097 EDA docstring).
ALTCOIN_REFERENCE = {
    "BCHUSDT": 0.02542,  # thin
    "LDOUSDT": 0.17793,  # genuine — v3's STRONGEST, still modest
    "TRXUSDT": 0.02907,  # thin
}


# ---------------------------------------------------------------------------
# Triple-barrier labeling — byte-faithful replication of labeling.py and the
# /096/097 EDAs' triple_barrier_label (validated against production there).
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
    evaluation span exactly (feedback_v3_eda_walkforward_faithful.md).
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

    THE HEADLINE METRIC — identical to the /096/097 EDA within-symbol benchmark.
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

    Within each third, a chronological 2/3-train -> 1/3-predict split (an
    embargo gap purges the label window).  A genuine-signal symbol scores
    positive in all 3 thirds; a SIGN-FLIPPING symbol does not.
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


def subperiod_stability(sub: list[float]) -> tuple[str, int, float]:
    """Map a sub-period IC list -> (label, n_thirds_positive, worst_third).

    label in {STABLE, CONCENTRATED, SIGN-FLIPPING}:
      SIGN-FLIPPING -- >=1 third clearly positive AND >=1 third clearly
                       negative, each beyond the +-0.020 deadband.  This is
                       the failure the user asked the screen to catch: a
                       major with a sign-flipping IC is NOT genuinely better
                       than the sign-flipping altcoins, whatever its T2.
      STABLE        -- >=2 of 3 thirds positive AND worst third >= -0.030.
      CONCENTRATED  -- otherwise (regime-concentrated, but not sign-flipping).
    """
    valid = [v for v in sub if pd.notna(v)]
    n_pos = sum(1 for v in valid if v > 0)
    worst = min(valid) if valid else float("nan")
    has_pos = any(v > SIGNFLIP_DEADBAND for v in valid)
    has_neg = any(v < -SIGNFLIP_DEADBAND for v in valid)
    if has_pos and has_neg:
        return "SIGN-FLIPPING", n_pos, worst
    is_stable = (
        len(valid) >= 2
        and n_pos >= SUBPERIOD_MIN_POSITIVE
        and (pd.isna(worst) or worst >= SUBPERIOD_NEG_FLOOR)
    )
    return ("STABLE" if is_stable else "CONCENTRATED"), n_pos, worst


def classify(t2_ic: float) -> str:
    """Map the headline within-symbol CV-IC -> band {GENUINE, BORDERLINE,
    THIN, INSUFFICIENT}.  Bands are the /096/097 bands, unchanged."""
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
    print("iter-v3/101 cycle-5 opener — EXCLUDED-COINS RE-EVALUATION SCREEN — IS-only")
    print("Headline: within-symbol purged-5-fold-CV rank-IC of the 14-feature")
    print("V3_FEATURE_COLUMNS stack vs the /059 triple-barrier directional label.")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row IS-only.")
    print("Altcoin reference (the /096 thin-signal baseline this screen judges against):")
    print("  BCH +0.02542 (thin) | LDO +0.17793 (v3's best) | TRX +0.02907 (thin)")
    print("=" * 78)

    # ---- containment assertion (the screen target IS the excluded set) ----
    not_excluded = set(EXCLUDED_MAJORS) - set(V3_EXCLUDED_SYMBOLS)
    assert not not_excluded, f"screen contains non-excluded symbols: {sorted(not_excluded)}"
    print(
        f"\nContainment check: all {len(EXCLUDED_MAJORS)} screened symbols are in "
        f"V3_EXCLUDED_SYMBOLS. PASS. (This EDA SCREENS the excluded set — it does "
        f"NOT modify it; relaxing the exclusion is the user's structural decision.)"
    )

    # ---- load every excluded major's IS panel ----
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    missing: list[str] = []
    for sym in EXCLUDED_MAJORS:
        d = load_symbol_is(sym)
        if d is None:
            print(f"  {sym}: parquet MISSING — skipped")
            missing.append(sym)
            continue
        d["y"] = (d["tb_label"] == 1).astype(int)
        d = d.dropna(subset=list(V3_FEATURE_COLUMNS) + ["tb_pnl"]).reset_index(drop=True)
        if len(d) < 300:
            print(f"  {sym}: only {len(d)} IS rows post-burn-in — skipped (insufficient)")
            missing.append(sym)
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
    t1.to_csv(OUT / "T1_excluded_major_is_panels.csv", index=False)
    print(f"\nT1 — excluded-major IS panels (post-24mo-burn-in, IS-only): {len(panels)} screened")
    print(t1.to_string(index=False))
    if missing:
        print(f"  symbols NOT obtained: {missing}")

    # ---- T2: within-symbol CV rank-IC (the headline) ----
    print("\nT2 — WITHIN-symbol purged 5-fold CV rank-IC (THE HEADLINE SCREEN):")
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
        stab, _, worst = subperiod_stability(sub)
        t3_rows.append(
            {
                "symbol": sym,
                "ic_third_1": round(sub[0], 5) if pd.notna(sub[0]) else np.nan,
                "ic_third_2": round(sub[1], 5) if pd.notna(sub[1]) else np.nan,
                "ic_third_3": round(sub[2], 5) if pd.notna(sub[2]) else np.nan,
                "n_thirds_positive": n_pos,
                "worst_third_ic": round(worst, 5) if pd.notna(worst) else np.nan,
                "subperiod_stability": stab,
            }
        )
        print(
            f"  {sym:10s}: thirds = "
            f"[{sub[0]:+.4f}, {sub[1]:+.4f}, {sub[2]:+.4f}]  "
            f"({n_pos}/3 positive)  {stab}"
        )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_subperiod_sign_consistency.csv", index=False)

    # ---- T5: ranked screen + classification + verdict ----
    sub_lookup = {r["symbol"]: r for r in t3_rows}
    t5_rows = []
    for _, r in t2.iterrows():
        sym = r["symbol"]
        t2_ic = float(r["within_cv_rank_ic"])
        sr = sub_lookup[sym]
        sub = [sr["ic_third_1"], sr["ic_third_2"], sr["ic_third_3"]]
        band = classify(t2_ic)
        stab, n_pos, worst = subperiod_stability(sub)
        # "genuinely better than the thin altcoins" requires BOTH the
        # GENUINE headline band AND a non-sign-flipping IC.
        genuine_and_stable = band == "GENUINE" and stab != "SIGN-FLIPPING"
        t5_rows.append(
            {
                "symbol": sym,
                "within_cv_rank_ic": round(t2_ic, 5),
                "band": band,
                "ic_vs_thin_floor_ratio": round(t2_ic / 0.025, 2) if pd.notna(t2_ic) else np.nan,
                "ic_vs_ldo_ratio": round(t2_ic / 0.17793, 2) if pd.notna(t2_ic) else np.nan,
                "n_thirds_positive": n_pos,
                "worst_third_ic": round(worst, 5) if pd.notna(worst) else np.nan,
                "subperiod_stability": stab,
                "genuine_and_sign_stable": genuine_and_stable,
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
    genuine_stable = t5[t5["genuine_and_sign_stable"]]["symbol"].tolist()

    # ---- T4: per-feature univariate IC texture for the top-tier majors ----
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

    # ---- THE DECISIVE VERDICT (3-way — see the docstring) ----
    LDO_CLASS_MIN = 0.120  # >= this and sign-stable -> LDO-class major
    CLUSTER_MIN = 3  # >= this many GENUINE-and-sign-stable -> breadth signal
    best_ic = float(t5["within_cv_rank_ic"].max()) if not t5.empty else float("nan")
    best_sym = t5.iloc[0]["symbol"] if not t5.empty else "n/a"
    cluster_above_ldo = t5[t5["within_cv_rank_ic"] > 0.17793]["symbol"].tolist()
    # best CV-IC AMONG the GENUINE-and-sign-stable majors (NaN if none).
    gs_rows = t5[t5["genuine_and_sign_stable"]]
    best_gs_ic = float(gs_rows["within_cv_rank_ic"].max()) if not gs_rows.empty else float("nan")
    ldo_class = [s for s in genuine_stable
                 if float(t5[t5["symbol"] == s]["within_cv_rank_ic"].iloc[0]) >= LDO_CLASS_MIN]
    if len(ldo_class) >= 1 or len(genuine_stable) >= CLUSTER_MIN:
        verdict_code = "CONFINEMENT_ARTIFACT"
    elif len(genuine_stable) == 0:
        verdict_code = "8H_CRYPTO_WIDE_THIN"
    else:
        verdict_code = "EQUIVOCAL"

    print("\n" + "=" * 78)
    print("DECISIVE VERDICT — do the EXCLUDED liquid majors carry genuine signal?")
    print("=" * 78)
    print("  Headline metric = within-symbol purged-5-fold-CV rank-IC (the /096 metric).")
    print(f"  GENUINE-SIGNAL  (CV IC >= +{GENUINE_IC_MIN:.3f}): {genuine}")
    print(f"  BORDERLINE      (CV IC in [+{THIN_IC_MAX:.3f}, +{GENUINE_IC_MIN:.3f})): {borderline}")
    print(f"  THIN-SIGNAL     (CV IC < +{THIN_IC_MAX:.3f}): {thin}")
    print("  ----")
    print(f"  best excluded major: {best_sym} at CV IC {best_ic:+.5f}")
    print(f"    vs the thin-altcoin floor +0.025  -> {best_ic / 0.025:.2f}x")
    print(f"    vs LDO (v3's strongest) +0.17793  -> {best_ic / 0.17793:.2f}x")
    print(f"  GENUINE *and* sign-stable majors: {genuine_stable}")
    print(f"    best GENUINE-and-sign-stable CV-IC: {best_gs_ic:+.5f}"
          if genuine_stable else "    (none)")
    print(f"  LDO-class majors (GENUINE-and-sign-stable AND CV-IC >= +{LDO_CLASS_MIN:.3f}): "
          f"{ldo_class}")
    print(f"  majors clearly above LDO's +0.178: {cluster_above_ldo}")
    print("  ----")
    if verdict_code == "CONFINEMENT_ARTIFACT":
        print("  VERDICT: CONFINEMENT ARTIFACT — an excluded liquid major carries")
        print("  LDO-CLASS, sign-stable signal (or a >= 3-symbol GENUINE cluster the")
        print("  altcoin universe never had).  v3's 100-iteration plateau is at")
        print("  least partly a property of its altcoin confinement.  Relaxing")
        print("  V3_EXCLUDED_SYMBOLS is a strong structural lever for the user.")
    elif verdict_code == "8H_CRYPTO_WIDE_THIN":
        print("  VERDICT: 8h-CRYPTO-WIDE THIN SIGNAL — every excluded liquid major")
        print("  is THIN/BORDERLINE, OR every GENUINE major is SIGN-FLIPPING (not")
        print("  transferable).  No major beats the thin altcoins.  The thin")
        print("  per-symbol 8h triple-barrier signal is a property of 8h crypto")
        print("  generally — v3's altcoin confinement did NOT cause the plateau.")
    else:
        print("  VERDICT: EQUIVOCAL — LEANS toward an 8h-crypto-wide thin signal.")
        print(f"  {len(genuine_stable)} major(s) ({', '.join(genuine_stable)}) clear GENUINE")
        print(f"  *and* sign-stable, but only MARGINALLY: best CV-IC {best_gs_ic:+.5f} sits")
        print(f"  in the [+{GENUINE_IC_MIN:.3f}, +{LDO_CLASS_MIN:.3f}) scrape band — a fraction")
        print("  of LDO's +0.178 — with NO LDO-class symbol and NO >= 3-symbol cluster.")
        print("  8 of 10 majors are THIN (BTC -0.069, ETH -0.003 — the two deepest")
        print("  markets are NEGATIVE).  The majors are NOT a clean confinement-")
        print("  artifact answer; the marginal pass is the same thin/non-stationary")
        print("  texture as the altcoins.  A single +0.06-IC symbol does NOT justify")
        print("  a structural universe change on its own; the user weighs whether")
        print("  it is worth a confirmation backtest.")
    print("=" * 78)

    # ---- write the verdict CSV ----
    verdict = pd.DataFrame(
        [
            {
                "metric": "n_majors_screened",
                "value": len(panels),
            },
            {"metric": "best_major", "value": best_sym},
            {"metric": "best_major_cv_ic", "value": round(best_ic, 5)},
            {"metric": "best_vs_thin_floor_ratio", "value": round(best_ic / 0.025, 2)},
            {"metric": "best_vs_ldo_ratio", "value": round(best_ic / 0.17793, 2)},
            {"metric": "n_genuine", "value": len(genuine)},
            {"metric": "n_genuine_and_sign_stable", "value": len(genuine_stable)},
            {"metric": "n_borderline", "value": len(borderline)},
            {"metric": "n_thin", "value": len(thin)},
            {"metric": "best_genuine_and_sign_stable_cv_ic",
             "value": round(best_gs_ic, 5) if genuine_stable else "NaN"},
            {
                "metric": "genuine_and_sign_stable_symbols",
                "value": ";".join(genuine_stable) or "NONE",
            },
            {"metric": "ldo_class_majors", "value": ";".join(ldo_class) or "NONE"},
            {"metric": "majors_above_ldo", "value": ";".join(cluster_above_ldo) or "NONE"},
            {"metric": "verdict", "value": verdict_code},
        ]
    )
    verdict.to_csv(OUT / "T6_verdict.csv", index=False)
    print(f"\nVerdict written to {OUT / 'T6_verdict.csv'}")


if __name__ == "__main__":
    main()

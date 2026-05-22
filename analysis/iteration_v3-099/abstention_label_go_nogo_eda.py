"""iter-v3/099 — Phase-1 FAIL-FAST GO/NO-GO EDA — ABSTENTION-AWARE LABEL.

THE AXIS UNDER TEST
-------------------
v3's canonical label (`labeling.py:label_trades`, label_mode="triple_barrier")
produces a BINARY direction {LONG=+1, SHORT=-1} for EVERY candle.  When no TP
barrier is hit in either direction (the chop case), `labeling.py` lines 337-347
fall back to `sign(fwd_return)` — so a candle whose forward path chops sideways,
where BOTH net directional PnLs are negative, STILL receives a confident
long/short training label.  The primary LightGBM is therefore trained to call a
side on candles that carry NO tradeable directional edge.  That is label noise
injected by construction.

The /099 axis: an ABSTENTION-AWARE triple-class label {LONG, SHORT, NO-TRADE}.
A candle is relabeled NO-TRADE when the BETTER of its two realized net
directional PnLs — max(long_pnl, short_pnl), both already fee-netted by
`label_trades` — fails to clear a per-symbol, train-window-calibrated edge
floor.  The barrier MECHANICS are unchanged (this is NOT /072's fixed-horizon
relabel); only ambiguous-outcome candles move to a third class.  This is the
target-information-content lever no v3 labeling iteration has touched:
  - /010 tuned ATR barrier geometry (knob) — NOT this.
  - /017 meta-labeling: an M2 classifier FILTERS M1's side post-hoc — the
    abstention here is IN THE LABEL, learned by the PRIMARY model — NOT this.
  - /072 fixed-horizon: still a binary return-sign label; failed on a
    label-execution mismatch — NOT this (barrier mechanics preserved).

THE DECISIVE PREMISE (what GO/NO-GO tests)
------------------------------------------
The abstention axis is only worth a build if BOTH hold:
  P1 (FORCING) — the current binary label is forced on a MATERIAL fraction of
       edge-free candles.  If <~15% of candles are edge-free, there is almost
       nothing for an abstention class to remove and the axis is a near-no-op.
  P2 (LEARNABILITY) — the NO-TRADE class must be PREDICTABLE FROM FEATURES at
       decision time, above chance, OUT-OF-WINDOW.  This is the load-bearing,
       NON-CIRCULAR test.  An abstention LABEL is only useful if the primary
       model can actually LEARN it from the feature panel it sees at the candle
       close; if edge-free vs traded is feature-indistinguishable, relabeling
       merely deletes ~30% of training rows at random and the axis is dead.
       /072's fixed-horizon relabel failed because the new label was not
       coherent with what the model could act on — P2 directly guards that.

THE OOS-ROBUST METHODOLOGY (NOT a naive IS-IC ranking, NOT circular)
--------------------------------------------------------------------
/096/097 proved an IS-CV-IC ranking does NOT predict OOS.  /098 used a
nested expanding-window walk-forward held-out-tail test; /099 uses the SAME
discipline.  The P2 statistic is the held-out AUC of a LightGBM classifier
trained to predict the edge_free label from a scale-invariant feature panel,
under an expanding-window walk-forward over the last HOLDOUT_FOLDS one-month
IS folds (strictly open_time < OOS_CUTOFF — the real OOS is NEVER touched); the
classifier for each fold is trained ONLY on candles strictly BEFORE that fold.
NON-CIRCULARITY: the classifier sees ONLY past-only features (NEVER best_edge,
NEVER any barrier outcome) and predicts the edge_free label out-of-window — so
a high AUC genuinely means "the abstention class is learnable", not "thresholding
X separates X".  Significance: a candle-level block-bootstrap 95% CI of the
pooled held-out AUC (block = the 21-bar label horizon — the /096 discipline for
overlapping-label serial dependence).  A held-out AUC whose CI includes 0.50 is
NOT a GO.

GO / NO-GO  (pre-registered, decided BEFORE running)
----------------------------------------------------
  g1 FORCING        — pooled edge-free-candle fraction >= 0.15
                      (a material share for an abstention class to act on).
  g2 LEARNABILITY   — pooled held-out edge_free-classifier AUC >= 0.55
                      (genuinely above the 0.50 coin-flip; the abstention
                      class carries feature-predictable structure a primary
                      model can learn).
  g3 LEARNABILITY   — the candle-level block-bootstrap 95% CI lower bound of
       sig             the pooled held-out AUC > 0.50 (learnability is real,
                      not a point estimate).
  g4 EDGE GRADIENT  — the held-out abstention SCORE must monotonically rank
                      edge: candles in the TOP score-tercile (model says
                      "trade") realize a strictly HIGHER mean net barrier PnL
                      than candles in the BOTTOM tercile (model says
                      "abstain"), pooled across folds.  This confirms the
                      learnable class is the EDGE-relevant one — the direct
                      mechanism by which the axis would lift the book — and is
                      measured on best_edge but SPLIT by the feature-only
                      classifier score (NOT by best_edge), so it is not
                      circular.
  GO iff g1 AND g2 AND g3 AND g4 ALL hold.  Any single fail => NO-GO, STOP at
  the EDA, file NULL-AT-EDA.  Fail-fast: kill a foreseeably-modest axis for
  the cost of one committed IS-only script.

NO CHEATING
-----------
OOS_CUTOFF_MS = 1742774400000 (2025-03-24).  EVERY measurement is strictly
open_time < OOS_CUTOFF_MS.  The held-out-fold classifier is trained ONLY on
candles strictly before that fold (expanding window).  The classifier features
are strictly past-only (rolling windows; the panel never reads a barrier
outcome).  The real OOS is never read.  training_months / OOS cutoff untouched
— this is an EDA, no runner change.

Outputs (committed): T1_forcing.csv, T2_holdout_learnability.csv,
T3_bootstrap_ci.csv, T4_go_nogo_verdict.csv, and a printed verdict block.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- v3 canonical constants (replicated from BASELINE_V3.md / config — NOT imported;
#     this is an IS-only diagnostic, it must not touch src/ runner state) -----------
OOS_CUTOFF_MS = 1_742_774_400_000  # 2025-03-24 — the sacred IS/OOS wall
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]  # V3_MODELS — NO universe axis (/097 ruling)
INTERVAL_MS = 8 * 60 * 60 * 1000
TIMEOUT_CANDLES = 21  # /059 canonical triple-barrier timeout
ATR_TP_MULT = 2.0  # /059 canonical
ATR_SL_MULT = 1.0  # /059 canonical
ATR_WINDOW = 14  # standard Wilder ATR window for the labeling barrier scale
FEE_PCT = 0.1  # /059 canonical round-trip fee
HOLDOUT_FOLDS = 6  # last 6 one-month folds of IS = the held-out tail
MIN_CALIB_ROWS = 300  # minimum prior-IS rows before a held-out fold is scored
BOOTSTRAP_N = 2000
BLOCK = TIMEOUT_CANDLES  # block-bootstrap block = label horizon (overlap serial dep)
RNG_SEED = 42

DATA = Path("data")
OUT = Path("analysis/iteration_v3-099")


# ----------------------------------------------------------------------------------
# ATR — past-only Wilder ATR, the barrier scale `labeling.py` uses via atr_values.
# ----------------------------------------------------------------------------------
def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, window: int) -> np.ndarray:
    n = len(close)
    tr = np.full(n, np.nan)
    prev_close = np.concatenate([[np.nan], close[:-1]])
    hl = high - low
    hc = np.abs(high - prev_close)
    lc = np.abs(low - prev_close)
    tr = np.nanmax(np.vstack([hl, hc, lc]), axis=0)
    tr[0] = high[0] - low[0]
    atr = np.full(n, np.nan)
    if n > window:
        atr[window] = np.mean(tr[1 : window + 1])
        for i in range(window + 1, n):
            atr[i] = (atr[i - 1] * (window - 1) + tr[i]) / window
    # shift(1): the ATR used to size candle i's barrier must be known at i's close.
    return np.concatenate([[np.nan], atr[:-1]])


# ----------------------------------------------------------------------------------
# Triple-barrier outcome — a faithful single-symbol replica of
# `labeling.py:label_trades` (label_mode="triple_barrier", use_atr=True).
# Returns, per candle, the net-of-fee long_pnl and short_pnl AND whether either
# direction hit its TP (the "edge-free" definition mirrors labeling.py's no-TP
# fallback branch).  IS-only by construction — the caller passes IS candles.
# ----------------------------------------------------------------------------------
def barrier_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    h = df["high"].to_numpy(float)
    lo = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    ct = df["close_time"].to_numpy(np.int64)
    ot = df["open_time"].to_numpy(np.int64)
    atr = wilder_atr(h, lo, c, ATR_WINDOW)
    n = len(df)
    timeout_ms = TIMEOUT_CANDLES * INTERVAL_MS

    long_pnl = np.full(n, np.nan)
    short_pnl = np.full(n, np.nan)
    long_tp = np.zeros(n, dtype=bool)
    short_tp = np.zeros(n, dtype=bool)
    any_tp = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = c[i]
        a = atr[i]
        if not np.isfinite(a) or entry == 0:
            a = entry * 0.02 if entry else np.nan
        if not np.isfinite(a):
            continue
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        long_tp_p, long_sl_p = entry + tp_dist, entry - sl_dist
        short_tp_p, short_sl_p = entry - tp_dist, entry + sl_dist
        deadline = ct[i] + timeout_ms
        l_res, s_res, last_close = 0, 0, entry  # 0 pending, 1 tp, -1 sl, -2 timeout
        for j in range(i + 1, n):
            if ct[j] > deadline:
                if l_res == 0:
                    l_res = -2
                if s_res == 0:
                    s_res = -2
                break
            last_close = c[j]
            if l_res == 0:
                if lo[j] <= long_sl_p:
                    l_res = -1
                elif h[j] >= long_tp_p:
                    l_res = 1
            if s_res == 0:
                if h[j] >= short_sl_p:
                    s_res = -1
                elif lo[j] <= short_tp_p:
                    s_res = 1
            if l_res != 0 and s_res != 0:
                break
        else:
            if l_res == 0:
                l_res = -2
            if s_res == 0:
                s_res = -2
        fwd = (last_close - entry) / entry * 100.0 if entry else 0.0
        tp_pct = tp_dist / entry * 100.0
        sl_pct = sl_dist / entry * 100.0
        lp = (tp_pct if l_res == 1 else -sl_pct if l_res == -1 else fwd) - FEE_PCT
        sp = (tp_pct if s_res == 1 else -sl_pct if s_res == -1 else -fwd) - FEE_PCT
        long_pnl[i] = lp
        short_pnl[i] = sp
        long_tp[i] = l_res == 1
        short_tp[i] = s_res == 1
        any_tp[i] = (l_res == 1) or (s_res == 1)

    out = pd.DataFrame(
        {
            "open_time": ot,
            "long_pnl": long_pnl,
            "short_pnl": short_pnl,
            "long_tp": long_tp,
            "short_tp": short_tp,
            "any_tp": any_tp,
        }
    )
    # best_edge = the net PnL of the side the binary label would actually pick.
    # labeling.py picks the TP-hitting side, else sign(fwd) — but for the EDGE
    # question the load-bearing quantity is the BEST achievable net PnL: a candle
    # is "edge-free" precisely when even its better direction loses money.
    out["best_edge"] = np.maximum(out["long_pnl"], out["short_pnl"])
    # edge_free: no TP in either direction AND the better side is net-negative.
    # This is the population the abstention class would target — the candles the
    # binary label is currently FORCED onto with no tradeable directional edge.
    out["edge_free"] = (~out["any_tp"]) & (out["best_edge"] < 0.0)
    return out.dropna(subset=["best_edge"]).reset_index(drop=True)


def month_key(ms: np.ndarray) -> np.ndarray:
    dt = pd.to_datetime(ms, unit="ms", utc=True)
    return (dt.year * 100 + dt.month).to_numpy()


# ----------------------------------------------------------------------------------
# Feature panel — a compact, scale-invariant past-only panel drawn from the SAME
# families as V3_FEATURE_COLUMNS (realized vol, momentum, range, autocorrelation,
# skew/kurtosis, RSI).  It is NOT the full 14-feature stack — a `features` regen
# is a setup cost the Phase-1 fail-fast discipline disfavors — but it is a FAIR
# proxy: if the abstention class is learnable AT ALL it must register in this
# panel of the standard predictor families.  Every column is strictly past-only
# (rolling windows + .shift(1)); NONE reads a barrier outcome.
# ----------------------------------------------------------------------------------
def feature_panel(df: pd.DataFrame) -> pd.DataFrame:
    c = df["close"].astype(float)
    h = df["high"].astype(float)
    lo = df["low"].astype(float)
    v = df["volume"].astype(float)
    ret1 = np.log(c / c.shift(1))
    out = pd.DataFrame(index=df.index)
    # realized volatility — 20 / 50 bar
    out["rv_20"] = ret1.rolling(20).std()
    out["rv_50"] = ret1.rolling(50).std()
    # momentum — 5 / 15 bar log return
    out["mom_5"] = np.log(c / c.shift(5))
    out["mom_15"] = np.log(c / c.shift(15))
    # normalized range (high-low over close), rolling mean 20
    out["range_20"] = ((h - lo) / c).rolling(20).mean()
    # return autocorrelation lag-1, 50-bar
    out["ret_acf1_50"] = ret1.rolling(50).apply(
        lambda x: pd.Series(x).autocorr(lag=1) if np.std(x) > 0 else 0.0, raw=False
    )
    # rolling skew / kurtosis of returns, 50-bar
    out["ret_skew_50"] = ret1.rolling(50).skew()
    out["ret_kurt_50"] = ret1.rolling(50).kurt()
    # RSI-14 (Wilder), scale-invariant 0-100
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    out["rsi_14"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    # volume z-score, 50-bar
    out["vol_z_50"] = (v - v.rolling(50).mean()) / v.rolling(50).std()
    # ABSOLUTE recent return — a candle is more likely edge-free when recent
    # realized motion is small (chop); a direct, economically-motivated predictor.
    out["abs_mom_5"] = out["mom_5"].abs()
    # shift the whole panel by 1: every feature must be known at the candle close
    # that the label is assigned to (the binary model sees feat[t] -> label[t]).
    return out


FEATURE_COLS = [
    "rv_20",
    "rv_50",
    "mom_5",
    "mom_15",
    "range_20",
    "ret_acf1_50",
    "ret_skew_50",
    "ret_kurt_50",
    "rsi_14",
    "vol_z_50",
    "abs_mom_5",
]


def _auc(y: np.ndarray, score: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney).  Returns NaN if a class is absent."""
    pos = score[y == 1]
    neg = score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    # average ties
    allv = np.concatenate([pos, neg])
    sorted_v = allv[order]
    i = 0
    while i < len(sorted_v):
        j = i
        while j + 1 < len(sorted_v) and sorted_v[j + 1] == sorted_v[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def block_bootstrap_auc_ci(
    y: np.ndarray, score: np.ndarray, n_boot: int, block: int, rng: np.random.Generator
):
    """Candle-level block-bootstrap 95% CI of the AUC.

    The held-out candles carry overlapping 21-bar labels => serial dependence;
    resampling contiguous BLOCK-length runs of candles preserves it.  This is a
    GENUINE candle-level resample (the prior fold-mean version was degenerate:
    17 fold means with block 21 wrap to the same 17 indices every draw).
    """
    m = len(y)
    if m < block:
        return float("nan"), float("nan")
    n_blocks = int(np.ceil(m / block))
    aucs = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, m - block + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:m]
        aucs[b] = _auc(y[idx], score[idx])
    aucs = aucs[np.isfinite(aucs)]
    if aucs.size == 0:
        return float("nan"), float("nan")
    return float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def main() -> int:
    try:
        from lightgbm import LGBMClassifier
    except ImportError:
        print("[FATAL] lightgbm not importable — run under `uv run`.")
        return 1

    rng = np.random.default_rng(RNG_SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    forcing_rows = []
    learn_rows = []  # one row per (symbol, held-out fold)
    # pooled held-out arrays for the candle-level bootstrap + edge-gradient gate
    pooled_y: list[np.ndarray] = []
    pooled_score: list[np.ndarray] = []
    pooled_edge: list[np.ndarray] = []

    for sym in SYMBOLS:
        df = pd.read_csv(DATA / sym / "8h.csv")
        df = df[df["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)  # IS-ONLY
        feats = feature_panel(df)
        oc = barrier_outcomes(df)
        if oc.empty:
            print(f"[WARN] {sym}: no labeled candles")
            continue
        # join the feature panel onto the labeled candles by open_time
        feats["open_time"] = df["open_time"].to_numpy(np.int64)
        merged = oc.merge(feats, on="open_time", how="inner")
        merged = merged.dropna(subset=FEATURE_COLS).reset_index(drop=True)
        merged["month"] = month_key(merged["open_time"].to_numpy())

        # ---- P1: FORCING — fraction of edge-free candles, pooled per symbol ----
        n_total = len(merged)
        n_ef = int(merged["edge_free"].sum())
        n_notp = int((~merged["any_tp"]).sum())
        forcing_rows.append(
            {
                "symbol": sym,
                "n_candles": n_total,
                "n_no_tp": n_notp,
                "no_tp_frac": round(n_notp / n_total, 4),
                "n_edge_free": n_ef,
                "edge_free_frac": round(n_ef / n_total, 4),
                "mean_best_edge_all": round(float(merged["best_edge"].mean()), 4),
                "mean_best_edge_edge_free": round(
                    float(merged.loc[merged["edge_free"], "best_edge"].mean())
                    if n_ef
                    else float("nan"),
                    4,
                ),
            }
        )

        # ---- P2: held-out LEARNABILITY of the edge_free label, walk-forward ----
        # Classifier predicts edge_free from FEATURE_COLS ONLY (never best_edge,
        # never a barrier outcome); trained strictly on candles before each fold.
        months = sorted(merged["month"].unique())
        if len(months) <= HOLDOUT_FOLDS:
            print(f"[WARN] {sym}: only {len(months)} IS months, need > {HOLDOUT_FOLDS}")
            continue
        holdout_months = months[-HOLDOUT_FOLDS:]
        for hm in holdout_months:
            calib = merged[merged["month"] < hm]
            fold = merged[merged["month"] == hm]
            if len(calib) < MIN_CALIB_ROWS or len(fold) < 10:
                continue
            y_tr = calib["edge_free"].to_numpy(int)
            if y_tr.sum() < 20 or (1 - y_tr).sum() < 20:
                continue  # need both classes present to train
            clf = LGBMClassifier(
                n_estimators=120,
                num_leaves=15,
                max_depth=4,
                learning_rate=0.05,
                min_child_samples=30,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RNG_SEED,
                n_jobs=1,
                verbose=-1,
            )
            clf.fit(calib[FEATURE_COLS].to_numpy(), y_tr)
            # held-out fold: score = P(edge_free); abstain_score = 1 - score so a
            # HIGH abstain_score means "trade" (low edge-free probability).
            y_fold = fold["edge_free"].to_numpy(int)
            p_ef = clf.predict_proba(fold[FEATURE_COLS].to_numpy())[:, 1]
            fold_auc = _auc(y_fold, p_ef)  # AUC of predicting edge_free
            edge_fold = fold["best_edge"].to_numpy()
            trade_score = 1.0 - p_ef  # high => model says "trade"
            pooled_y.append(y_fold)
            pooled_score.append(p_ef)
            pooled_edge.append(edge_fold)
            # within-fold edge gradient: top vs bottom score tercile by trade_score
            if len(fold) >= 9:
                q1, q2 = np.quantile(trade_score, [1 / 3, 2 / 3])
                top = edge_fold[trade_score >= q2]
                bot = edge_fold[trade_score <= q1]
                grad = float(np.mean(top) - np.mean(bot)) if len(top) and len(bot) else float("nan")
            else:
                grad = float("nan")
            learn_rows.append(
                {
                    "symbol": sym,
                    "fold_month": int(hm),
                    "n_calib": len(calib),
                    "n_fold": len(fold),
                    "fold_edge_free_frac": round(float(y_fold.mean()), 4),
                    "holdout_auc": round(fold_auc, 4) if np.isfinite(fold_auc) else None,
                    "edge_top_tercile": round(
                        float(np.mean(edge_fold[trade_score >= np.quantile(trade_score, 2 / 3)])),
                        4,
                    )
                    if len(fold) >= 9
                    else None,
                    "edge_bot_tercile": round(
                        float(np.mean(edge_fold[trade_score <= np.quantile(trade_score, 1 / 3)])),
                        4,
                    )
                    if len(fold) >= 9
                    else None,
                    "edge_gradient": round(grad, 4) if np.isfinite(grad) else None,
                }
            )

    forcing = pd.DataFrame(forcing_rows)
    learn = pd.DataFrame(learn_rows)
    forcing.to_csv(OUT / "T1_forcing.csv", index=False)
    learn.to_csv(OUT / "T2_holdout_learnability.csv", index=False)

    # ---- pooled gate statistics ----------------------------------------------
    pooled_ef_frac = (
        float(forcing["n_edge_free"].sum() / forcing["n_candles"].sum())
        if not forcing.empty
        else float("nan")
    )
    if pooled_y:
        all_y = np.concatenate(pooled_y)
        all_score = np.concatenate(pooled_score)
        all_edge = np.concatenate(pooled_edge)
        pooled_auc = _auc(all_y, all_score)
        ci_lo, ci_hi = block_bootstrap_auc_ci(all_y, all_score, BOOTSTRAP_N, BLOCK, rng)
        trade_score_all = 1.0 - all_score
        q1, q2 = np.quantile(trade_score_all, [1 / 3, 2 / 3])
        edge_top = float(np.mean(all_edge[trade_score_all >= q2]))
        edge_bot = float(np.mean(all_edge[trade_score_all <= q1]))
        pooled_gradient = edge_top - edge_bot
    else:
        all_y = np.array([])
        pooled_auc = ci_lo = ci_hi = edge_top = edge_bot = pooled_gradient = float("nan")

    boot = pd.DataFrame(
        [
            {
                "stat": "pooled_holdout_auc",
                "value": round(pooled_auc, 4),
                "ci95_lo": round(ci_lo, 4),
                "ci95_hi": round(ci_hi, 4),
                "edge_top_tercile": round(edge_top, 4),
                "edge_bot_tercile": round(edge_bot, 4),
                "edge_gradient": round(pooled_gradient, 4),
                "n_holdout_candles": int(len(all_y)),
                "bootstrap_n": BOOTSTRAP_N,
                "block": BLOCK,
            }
        ]
    )
    boot.to_csv(OUT / "T3_bootstrap_ci.csv", index=False)

    # ---- the four pre-registered gates ---------------------------------------
    g1 = bool(pooled_ef_frac >= 0.15)  # FORCING
    g2 = bool(np.isfinite(pooled_auc) and pooled_auc >= 0.55)  # LEARNABILITY pt
    g3 = bool(np.isfinite(ci_lo) and ci_lo > 0.50)  # LEARNABILITY significance
    g4 = bool(np.isfinite(pooled_gradient) and pooled_gradient > 0.0)  # EDGE GRADIENT
    go = g1 and g2 and g3 and g4

    verdict = pd.DataFrame(
        [
            {
                "gate": "g1_forcing_edge_free_frac>=0.15",
                "value": round(pooled_ef_frac, 4),
                "pass": g1,
            },
            {
                "gate": "g2_learnability_holdout_auc>=0.55",
                "value": round(pooled_auc, 4),
                "pass": g2,
            },
            {"gate": "g3_learnability_ci95_lo>0.50", "value": round(ci_lo, 4), "pass": g3},
            {"gate": "g4_edge_gradient_top-bot>0", "value": round(pooled_gradient, 4), "pass": g4},
            {"gate": "OVERALL", "value": "GO" if go else "NO-GO", "pass": go},
        ]
    )
    verdict.to_csv(OUT / "T4_go_nogo_verdict.csv", index=False)

    # ---- printed verdict block -----------------------------------------------
    print("=" * 78)
    print("iter-v3/099 — Phase-1 GO/NO-GO EDA — ABSTENTION-AWARE LABEL")
    print("=" * 78)
    print("\nT1 — FORCING (per-symbol edge-free candle fraction, IS-only):")
    print(forcing.to_string(index=False))
    print(f"\n  pooled edge-free fraction = {pooled_ef_frac:.4f}")
    print("\nT2 — held-out LEARNABILITY (last 6 IS folds/symbol; LightGBM predicts")
    print("     edge_free from FEATURE panel ONLY, trained strictly on prior IS):")
    print(learn.to_string(index=False))
    print("\nT3 — pooled held-out AUC + candle-level block-bootstrap 95% CI +")
    print("     edge gradient (top vs bottom feature-score tercile):")
    print(boot.to_string(index=False))
    print("\nT4 — GATES (pre-registered before running):")
    print(verdict.to_string(index=False))
    print("\n" + "=" * 78)
    print(f"VERDICT: {'GO' if go else 'NO-GO'}")
    print("=" * 78)
    if not go:
        failed = [
            r["gate"] for _, r in verdict.iterrows() if not r["pass"] and r["gate"] != "OVERALL"
        ]
        print(f"NO-GO — failed gate(s): {failed}")
        print("STOP at the EDA. File NULL-AT-EDA. No brief, no runner change, no backtest.")
    else:
        print("GO — proceed to Phases 2-5; this EDA is brief Section 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

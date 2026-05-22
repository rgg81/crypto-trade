"""iter-v3/091 — Holding-horizon grid EDA for the cross-sectional book (IS-ONLY).

iter-v3/091 is cycle-3 EXPLORATION slot #10 of 10 — the FINAL cycle-3 EXPLORATION.
The cross-sectional line: /088 stood up a pooled LGBMRanker (OOS net monthly
Sharpe -0.54) -> /089 cost-aware construction (sign fix + quintile + 3-bar
overlapping holds + no-trade band; OOS net -0.10, the book turned GROSS-positive
OOS gross +0.1717) -> /090 downside-risk feature expansion FAILED
(FEATURE-EXPANSION-FALSIFIED; OOS net -0.08; the gross signal did not respond
to feature work). The /090 closeout (diary Section 7) and the /090 Critic both
concluded the open question is now SIGNAL STRENGTH, not construction re-slicing
or more features.

THE /091 AXIS — extend the holding horizon.
  The current cross-sectional hold is XS_HOLD_BARS = 3 = 3 x 8h = ~1 day, and
  the label horizon is XS_HORIZON = 3 (the label ranks the 3-bar-forward
  cross-sectional return). The cross-sectional crypto-momentum literature
  (Han, Kang & Ryu SSRN 4675565; the FXEmpire / Starkiller Capital practitioner
  consensus) is consistent that the cross-sectional momentum signal persists at
  WEEKLY-TO-FORTNIGHTLY horizons and reverses beyond ~2 weeks — the current
  ~1-day hold is BELOW the horizon where the signal lives. Extending the hold
  toward ~7 days attacks both diagnosed failure modes at once: (a) it measures
  the signal where it is strongest and most stable (a signal-STRENGTH lever,
  not a re-slice); (b) it cuts rebalance frequency, collapsing the fee drag
  that is the sole source of the net loss (the /090 closeout established OOS
  fees/gross ~1.58x).

THE LABEL-HORIZON COUPLING — H and XS_HOLD_BARS are ONE axis.
  The cross-sectional label `label_cross_sectional_rank(panel, horizon=H)` ranks
  symbols by the H-bar-forward return. If the HOLD is extended to ~H bars, the
  LABEL horizon must be horizon-matched (train the ranker to predict the H-bar
  forward-return rank, not a 3-bar one — a mismatch trains for the wrong
  horizon). So this EDA scans H, and for EACH H it (1) re-labels with horizon=H,
  (2) trains a fresh ranker on the H-label, (3) runs the IS-internal cost-aware
  backtest with hold_bars=H — H and the hold move together. This is the SINGLE
  coupled "holding horizon" axis. Extending H changes TWO DISTINCT embargo
  quantities: the CPCV flattened-ROW gap XS_REQUIRED_GAP = (H+1)*N (a ROW COUNT;
  H=28 -> (28+1)*22 = 638 rows) AND the walk-forward WALL-CLOCK TIME embargo
  = (H+1)*interval_ms = (H+1) candle-intervals of TIME (NO ×N — that factor is
  the row count, not a time; H=28 -> 29 intervals ~= 9.7 days, NOT 213 days).
  The EDA prints both per H and confirms the 24-month training window survives.
  (Multiplying the wall-clock embargo by N — conflating the row-gap with the
  time-embargo — was the iter-v3/091 Phase-5.5 BLOCK; fixed here.)

WHAT THIS EDA MEASURES — the horizon-grid scan.
  For each horizon H in HORIZON_GRID:
    - build the 22-symbol panel; label with horizon=H.
    - IS-internal monthly walk-forward: train one LGBMRanker per IS test month
      on the H-label, predict the next IS month (NEVER an OOS row).
    - construct the dollar-neutral QUINTILE long-short book (the /089 cost-aware
      construction: corrected sign, inverse-vol, vol-target, 3-bar-style
      OVERLAPPING tranches with hold_bars=H, the /089 no-trade band tau=0.020).
    - measure the IS quintile long-short spread monthly Sharpe — BOTH GROSS and
      NET of the turnover-based fee — on the IDENTICAL per-calendar-month basis
      (one shared `_monthly_sharpe` helper computes both; the /090 BLOCK was a
      gross-vs-net basis inconsistency, so gross and net here are guaranteed
      apples-to-apples).
  Output table: H x {IS gross spread monthly Sharpe, IS net spread monthly
  Sharpe, IS turnover/bar, IS fees/|gross| ratio, IS rank-IC, XS_REQUIRED_GAP}.
  Pre-register the IS-best horizon (by IS NET spread monthly Sharpe — the
  net-of-cost metric is the operative one; the diary asks whether a longer
  horizon beats hold=3 NET of cost).
  Sanity-check the monotonicity: the literature predicts a HUMP (the signal
  builds then reverses) — confirm or refute on IS data.

  This is MODEL-FREE in the sense that it does NOT prejudge the trained model —
  but it DOES train the same LGBMRanker the /091 build will run, per H, exactly
  as the /089 EDA trained the ranker per IS month. (A purely model-free momentum
  proxy is ALSO computed as the M-block cross-check — a trailing-N-bar-return
  rank composite, no LGBMRanker — so the horizon hump can be seen without any
  model in the loop.)

NO-CHEATING:
  - OOS_CUTOFF_MS / training_months are IMMUTABLE. The IS-internal walk-forward
    trains the ranker ONLY on IS months and predicts the NEXT IS month — no OOS
    row is ever read (panel sliced to open_time < OOS_CUTOFF_MS).
  - Every horizon in the grid is scanned; the IS-best is selected on the IS net
    spread monthly Sharpe. No OOS data informs the selection.
  - The QR sees OOS for the first time in Phase 7.

Run: uv run python analysis/iteration_v3-091/holding_horizon_eda.py
"""

from __future__ import annotations

import datetime
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))

# IMMUTABLE — the v3 sacred constant. IS = strictly before this ms.
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC

# Reuse the RETAINED /088/089 cross-sectional infrastructure verbatim — the EDA
# must measure the SAME model the /091 build runs, not a re-implementation.
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N  # noqa: E402
from crypto_trade.strategies.ml.cross_sectional import (  # noqa: E402
    XS_DROP_FEATURES,
    XS_MIN_SYMBOLS_PER_BAR,
    XS_NO_TRADE_BAND,
    XS_QUANTILE_FRAC,
    XS_UNIVERSE,
    XS_VOL_LOOKBACK,
    CrossSectionalRankStrategy,
    _generate_xs_monthly_splits,
    build_cross_sectional_panel,
    label_cross_sectional_rank,
)

FEATURES_DIR = REPO / "data" / "features_v3"
XS_FEATURE_COLUMNS = [c for c in V3_FEATURE_COLUMNS_TOP_N if c not in XS_DROP_FEATURES]
N_XS = len(XS_UNIVERSE)  # 22

# --- the holding-horizon grid -------------------------------------------------
# H is in 8h bars. 3 bars = ~1 day (the /088/089/090 incumbent). The literature
# locates the cross-sectional crypto-momentum signal at WEEKLY-TO-FORTNIGHTLY:
#   7 bars   = ~2.3 days
#   14 bars  = ~4.7 days
#   21 bars  = ~7 days   (one week — the practitioner-consensus rebalance)
#   28 bars  = ~9.3 days
#   35 bars  = ~11.7 days (the upper edge before the literature's ~2-week reversal)
# The grid straddles the incumbent (3) and the literature's predicted hump
# (weekly-to-fortnightly) so the IS data can confirm or refute the hump shape.
HORIZON_GRID: tuple[int, ...] = (3, 7, 14, 21, 28, 35)

# EDA controls — kept light (this is an EDA, not the Phase-6 backtest).
EDA_N_TRIALS = 8  # Optuna trials per IS month (fast; the full build uses 35)
EDA_TRAINING_MONTHS = 24  # the IMMUTABLE training window
BARS_PER_YEAR = 3.0 * 365.0  # 8h bars
FEE_PER_SIDE = 0.001  # 0.1% — the modeled Binance-futures-grade taker cost
SEED = 42


# ---------------------------------------------------------------------------
# Shared monthly-Sharpe helper — the /090-BLOCK fix.
# The /090 OVERALL=BLOCK was caused by gross monthly Sharpe being hand-computed
# on a non-per-month basis while net monthly Sharpe used per-calendar-month
# aggregation. Here ONE function computes BOTH from a PnL column, so gross and
# net are GUARANTEED on the identical per-calendar-month basis.
# ---------------------------------------------------------------------------


def _monthly_sharpe(df: pd.DataFrame, pnl_col: str) -> float:
    """Per-calendar-month Sharpe of a PnL column.

    Buckets each row into its calendar month by `open_time`, sums `pnl_col` per
    month, returns Sharpe = mean/std (sample std, ddof=1), no annualization.
    This is the EXACT method `run_cross_sectional_v3.py::_write_xs_reports`'s
    `_monthly_sharpe` uses for net monthly Sharpe — and the method the
    /090-closeout recompute confirmed reproduces comparison.csv to 1e-14.
    GROSS and NET monthly Sharpe MUST both be computed through this one helper.
    """
    if df.empty:
        return 0.0
    sub = df.copy()
    sub["_month"] = sub["open_time"].apply(
        lambda t: datetime.datetime.fromtimestamp(t / 1000, tz=datetime.UTC).strftime("%Y-%m")
    )
    monthly = sub.groupby("_month")[pnl_col].sum()
    if len(monthly) < 2:
        return 0.0
    return float(monthly.mean() / monthly.std()) if monthly.std() > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# Construction primitives — corrected-sign quintile, inverse-vol, vol-target,
# overlapping tranches, no-trade band (verbatim from the /089 EDA harness;
# the /089 build is the RETAINED construction baseline).
# ---------------------------------------------------------------------------


def _inv_vol_weights(leg_syms: list[str], vol_map: dict[str, float]) -> dict[str, float]:
    """Inverse-vol weights within a leg (the standard cross-sectional construction)."""
    inv = {s: 1.0 / max(vol_map.get(s, 1.0), 1e-8) for s in leg_syms}
    tot = sum(inv.values())
    return {s: v / tot for s, v in inv.items()} if tot > 0 else {}


def _target_positions(
    syms: np.ndarray,
    scores: np.ndarray,
    vol_map: dict[str, float],
    quantile_frac: float,
) -> dict[str, float]:
    """CORRECTED-SIGN dollar-neutral target positions at a timestamp.

    The /089 SIGN FIX: the LGBMRanker is trained on a FORWARD-return tercile
    grade, so high predicted score = predicted future WINNER. LONG the top
    quantile (high score), SHORT the bottom quantile. Dollar-neutral inverse-vol.
    """
    n = len(syms)
    order = np.argsort(scores)  # ascending
    sorted_syms = syms[order]
    n_leg = max(1, int(np.floor(n * quantile_frac)))
    short_syms = list(sorted_syms[:n_leg])  # LOW score  -> predicted losers -> SHORT
    long_syms = list(sorted_syms[-n_leg:])  # HIGH score -> predicted winners -> LONG
    lw = _inv_vol_weights(long_syms, vol_map)
    sw = _inv_vol_weights(short_syms, vol_map)
    pos: dict[str, float] = {}
    for s, w in lw.items():
        pos[s] = +w
    for s, w in sw.items():
        pos[s] = pos.get(s, 0.0) - w
    return pos


def _scale_to_vol_target(
    pos: dict[str, float], hist: pd.DataFrame, vol_target: float = 0.10
) -> dict[str, float]:
    """Portfolio vol-target scaling (mirrors build_positions / _portfolio_vol)."""
    syms = list(pos.keys())
    if not syms or len(hist) < 2:
        return pos
    present = [s for s in syms if s in hist.columns]
    rm = hist[present].dropna(how="all")
    if rm.shape[0] < 2 or rm.shape[1] < 1:
        return pos
    cov = np.cov(rm.values.T)
    wp = np.array([pos[s] for s in present])
    if cov.ndim == 0:
        pv = float(cov) * wp[0] ** 2
    else:
        pv = float(wp @ cov @ wp)
    ann = np.sqrt(max(pv, 0.0)) * np.sqrt(BARS_PER_YEAR)
    if ann > 1e-8:
        sc = vol_target / ann
        return {s: v * sc for s, v in pos.items()}
    return pos


def _apply_no_trade_band(
    target: dict[str, float], prev: dict[str, float], tau: float
) -> dict[str, float]:
    """No-trade band: hold the previous position for a symbol unless the target
    weight moved by more than tau. Constantinides/Davis-Norman no-trade region.
    """
    if tau <= 0.0:
        return dict(target)
    out: dict[str, float] = {}
    for s in set(target) | set(prev):
        t = target.get(s, 0.0)
        p = prev.get(s, 0.0)
        out[s] = t if abs(t - p) > tau else p
    return {s: v for s, v in out.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------------------
# IS-internal cost-aware backtest of one (horizon, hold) construction
# ---------------------------------------------------------------------------


def is_internal_backtest(
    panel_is: pd.DataFrame,
    ret_wide: pd.DataFrame,
    splits: list[dict],
    trained_models: dict[str, CrossSectionalRankStrategy],
    quantile_frac: float,
    hold_bars: int,
    no_trade_band: float,
) -> dict:
    """Run ONE (horizon-matched hold) construction over the IS-internal walk-forward.

    `trained_models` carries the per-IS-month LGBMRanker trained on the
    horizon-H label (the caller trains them). `hold_bars` is set EQUAL to the
    horizon H — the holding-horizon axis couples the label horizon and the hold.

    hold_bars > 1 implements OVERLAPPING tranches: at each bar a NEW tranche
    sized 1/hold_bars of the target is formed and held hold_bars bars then
    retired; the book = sum of the live tranches (Jegadeesh-Titman 1993). This
    cuts gross turnover ~hold_bars-fold. Returns a metrics dict.
    """
    rows: list[dict] = []
    tranches: list[tuple[int, dict[str, float]]] = []
    prev_book: dict[str, float] = {}
    bar_idx = 0

    for split in splits:
        test_month = split["test_month"]
        strat = trained_models.get(test_month)
        if strat is None or strat._model is None:
            continue
        test_mask = (panel_is["open_time"] >= split["test_start_ms"]) & (
            panel_is["open_time"] < split["test_end_ms"]
        )
        test_panel = panel_is[test_mask].copy()
        if test_panel.empty:
            continue

        for ts in np.sort(test_panel["open_time"].unique()):
            ts_mask = test_panel["open_time"] == ts
            panel_t = test_panel[ts_mask].copy().reset_index(drop=True)
            if len(panel_t) < XS_MIN_SYMBOLS_PER_BAR:
                continue
            x_t = panel_t[strat.feature_columns].values.astype(np.float32)
            scores = strat._model.predict(x_t)
            syms = panel_t["symbol"].values

            # past-only realised-vol estimate
            hist = ret_wide[ret_wide.index < ts].tail(XS_VOL_LOOKBACK)
            vol_map = {
                s: (
                    max(float(hist[s].dropna().std()), 1e-8)
                    if s in hist.columns and hist[s].dropna().shape[0] >= 2
                    else 1.0
                )
                for s in syms
            }

            # target book for THIS bar (full-size, dollar-neutral, vol-targeted)
            tgt = _target_positions(syms, scores, vol_map, quantile_frac)
            tgt = _scale_to_vol_target(tgt, hist)

            # ---- overlapping tranches: new tranche = (1/hold) of target ----
            new_tranche = {s: w / hold_bars for s, w in tgt.items()}
            tranches.append((bar_idx + hold_bars, new_tranche))
            tranches = [(rb, w) for (rb, w) in tranches if rb > bar_idx]
            book: dict[str, float] = {}
            for _, w in tranches:
                for s, v in w.items():
                    book[s] = book.get(s, 0.0) + v

            # ---- no-trade band on the realised book vs the previous book ---
            book = _apply_no_trade_band(book, prev_book, no_trade_band)

            # ---- PnL + turnover-based fee --------------------------------
            idx_loc = ret_wide.index.searchsorted(ts, side="right")
            for s in set(book) | set(prev_book):
                pos = book.get(s, 0.0)
                pp = prev_book.get(s, 0.0)
                if pos == 0.0 and pp == 0.0:
                    continue
                if s in ret_wide.columns and idx_loc < len(ret_wide):
                    nr = ret_wide[s].iloc[idx_loc]
                    nr = 0.0 if pd.isna(nr) else float(nr)
                else:
                    nr = 0.0
                fee = abs(pos - pp) * FEE_PER_SIDE
                rows.append(
                    {
                        "open_time": ts,
                        "symbol": s,
                        "position": pos,
                        "gross_pnl": pos * nr,
                        "fee": fee,
                        "net_pnl": pos * nr - fee,
                    }
                )
            prev_book = dict(book)
            bar_idx += 1

    if not rows:
        return {}
    df = pd.DataFrame(rows)
    n_bars = df["open_time"].nunique()
    gross = float(df["gross_pnl"].sum())
    feet = float(df["fee"].sum())
    net = float(df["net_pnl"].sum())
    turn_bar = float(df.groupby("open_time")["fee"].sum().mean()) / FEE_PER_SIDE
    book_bar = float(df["position"].abs().groupby(df["open_time"]).sum().mean())

    # GROSS and NET monthly Sharpe — both through the SHARED helper (the
    # /090-BLOCK fix: identical per-calendar-month basis, guaranteed).
    sg = _monthly_sharpe(df, "gross_pnl")
    sn = _monthly_sharpe(df, "net_pnl")

    psym = df.groupby("symbol")["net_pnl"].sum().abs()
    conc = float(psym.max() / psym.sum() * 100) if psym.sum() > 0 else 0.0

    return {
        "is_bars": n_bars,
        "is_gross_pnl": round(gross, 5),
        "is_fee_total": round(feet, 5),
        "is_net_pnl": round(net, 5),
        "fee_over_abs_gross": round(feet / abs(gross), 3) if abs(gross) > 1e-9 else float("inf"),
        "is_gross_monthly_sharpe": round(sg, 4),
        "is_net_monthly_sharpe": round(sn, 4),
        "mean_turnover_per_bar": round(turn_bar, 4),
        "mean_gross_book_per_bar": round(book_bar, 4),
        "max_symbol_concentration_pct": round(conc, 1),
    }


# ---------------------------------------------------------------------------
# M-block — a fully MODEL-FREE momentum-rank composite, per horizon.
# No LGBMRanker in the loop: rank symbols cross-sectionally by the trailing
# H-bar return, LONG the top quintile / SHORT the bottom quintile, hold H bars
# with overlapping tranches. Confirms the horizon hump is a property of the
# raw cross-sectional momentum signal, not an artifact of the trained model.
# ---------------------------------------------------------------------------


def model_free_horizon_scan(
    panel_is: pd.DataFrame,
    ret_wide: pd.DataFrame,
    horizon: int,
) -> dict:
    """Model-free trailing-H-bar-return cross-sectional momentum book, IS-only.

    The momentum proxy is the trailing H-bar return `close/close.shift(H) - 1`
    (a standard cross-sectional momentum signal — the dominant existing v3
    momentum family is exactly this kind of trailing-return ratio). At each bar
    the cross-section is ranked by the proxy; LONG the top quintile, SHORT the
    bottom quintile; inverse-vol; vol-target; held H bars via overlapping
    tranches; the /089 no-trade band. GROSS and NET monthly Sharpe through the
    shared `_monthly_sharpe` helper.

    No look-ahead: the proxy at bar t uses close(t) and close(t-H) only — both
    <= t. The 1-bar forward return for PnL is strictly after t (searchsorted
    side='right'). This is purely model-free — it never trains anything.
    """
    # wide trailing-H-bar return matrix (the momentum proxy), past-only.
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    mom_wide = close_wide / close_wide.shift(horizon) - 1.0

    timestamps = mom_wide.index.to_numpy()
    rows: list[dict] = []
    tranches: list[tuple[int, dict[str, float]]] = []
    prev_book: dict[str, float] = {}
    bar_idx = 0

    for ts in timestamps:
        mom_t = mom_wide.loc[ts].dropna()
        if len(mom_t) < XS_MIN_SYMBOLS_PER_BAR:
            continue
        syms = mom_t.index.to_numpy()
        scores = mom_t.to_numpy()  # the momentum proxy IS the score

        hist = ret_wide[ret_wide.index < ts].tail(XS_VOL_LOOKBACK)
        vol_map = {
            s: (
                max(float(hist[s].dropna().std()), 1e-8)
                if s in hist.columns and hist[s].dropna().shape[0] >= 2
                else 1.0
            )
            for s in syms
        }

        tgt = _target_positions(syms, scores, vol_map, XS_QUANTILE_FRAC)
        tgt = _scale_to_vol_target(tgt, hist)

        new_tranche = {s: w / horizon for s, w in tgt.items()}
        tranches.append((bar_idx + horizon, new_tranche))
        tranches = [(rb, w) for (rb, w) in tranches if rb > bar_idx]
        book: dict[str, float] = {}
        for _, w in tranches:
            for s, v in w.items():
                book[s] = book.get(s, 0.0) + v
        book = _apply_no_trade_band(book, prev_book, XS_NO_TRADE_BAND)

        idx_loc = ret_wide.index.searchsorted(ts, side="right")
        for s in set(book) | set(prev_book):
            pos = book.get(s, 0.0)
            pp = prev_book.get(s, 0.0)
            if pos == 0.0 and pp == 0.0:
                continue
            if s in ret_wide.columns and idx_loc < len(ret_wide):
                nr = ret_wide[s].iloc[idx_loc]
                nr = 0.0 if pd.isna(nr) else float(nr)
            else:
                nr = 0.0
            fee = abs(pos - pp) * FEE_PER_SIDE
            rows.append(
                {
                    "open_time": ts,
                    "symbol": s,
                    "position": pos,
                    "gross_pnl": pos * nr,
                    "fee": fee,
                    "net_pnl": pos * nr - fee,
                }
            )
        prev_book = dict(book)
        bar_idx += 1

    if not rows:
        return {}
    df = pd.DataFrame(rows)
    gross = float(df["gross_pnl"].sum())
    feet = float(df["fee"].sum())
    turn_bar = float(df.groupby("open_time")["fee"].sum().mean()) / FEE_PER_SIDE
    return {
        "mf_gross_monthly_sharpe": round(_monthly_sharpe(df, "gross_pnl"), 4),
        "mf_net_monthly_sharpe": round(_monthly_sharpe(df, "net_pnl"), 4),
        "mf_turnover_per_bar": round(turn_bar, 4),
        "mf_fee_over_abs_gross": (
            round(feet / abs(gross), 3) if abs(gross) > 1e-9 else float("inf")
        ),
    }


# ---------------------------------------------------------------------------
# Per-horizon: build panel, label at horizon=H, train per-IS-month ranker.
# ---------------------------------------------------------------------------


def train_rankers_for_horizon(
    panel_is: pd.DataFrame,
    horizon: int,
    splits: list[dict],
) -> tuple[dict[str, CrossSectionalRankStrategy], float]:
    """Label the IS panel at horizon=H, train one LGBMRanker per IS test month.

    Returns (trained_models keyed by test_month, mean IS-train rank-IC).
    The label changes with H — this is the LABEL side of the coupled
    holding-horizon axis. The model is trained on the H-bar-forward grade.
    """
    labels_is = label_cross_sectional_rank(panel_is, horizon=horizon)
    trained: dict[str, CrossSectionalRankStrategy] = {}
    is_rank_ics: list[float] = []
    for split in splits:
        tm = split["test_month"]
        train_mask = (panel_is["open_time"] >= split["train_start_ms"]) & (
            panel_is["open_time"] < split["train_end_ms"]
        )
        tp = panel_is[train_mask].copy()
        tl = labels_is[train_mask]
        valid = tl.notna()
        tp_v = tp[valid].sort_values(["open_time", "symbol"]).reset_index(drop=True)
        tl_v = tl[valid].reset_index(drop=True)
        tl_v = tl_v.reindex(tp_v.index)
        if len(tp_v) < 100:
            continue
        strat = CrossSectionalRankStrategy(
            training_months=EDA_TRAINING_MONTHS,
            n_trials=EDA_N_TRIALS,
            feature_columns=XS_FEATURE_COLUMNS,
            features_dir=str(FEATURES_DIR),
            symbols=XS_UNIVERSE,
            horizon=horizon,
            seed=SEED,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ic = strat._train_for_month(tp_v, tl_v)
        trained[tm] = strat
        is_rank_ics.append(ic)
    return trained, (float(np.mean(is_rank_ics)) if is_rank_ics else 0.0)


def main() -> None:
    print("=" * 78)
    print("iter-v3/091 holding-horizon grid EDA — cross-sectional book — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print(f"Universe: {N_XS} symbols (XS_UNIVERSE); horizon grid (8h bars): {HORIZON_GRID}")
    print(f"Model: the RETAINED cross_sectional.py LGBMRanker (lambdarank), {EDA_N_TRIALS} trials")
    print(f"Construction: /089 cost-aware (quintile q={XS_QUANTILE_FRAC}, ")
    print(f"  overlapping holds = horizon-matched, no-trade band tau={XS_NO_TRADE_BAND})")
    print("=" * 78)

    # --- build the pooled panel ONCE (IS rows only); features are H-invariant -
    print("\n[panel] Building pooled cross-sectional panel (IS slice only)...")
    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
    )
    panel_is = panel[panel["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    print(
        f"[panel] IS panel {len(panel_is)} rows, "
        f"{panel_is['open_time'].nunique()} timestamps, {panel_is['symbol'].nunique()} symbols"
    )

    # wide return matrix (IS only) for vol estimation + PnL
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    ret_wide = close_wide.pct_change()

    # IS-internal walk-forward splits. TWO DISTINCT embargo quantities — do NOT
    # conflate them (the Phase-5.5 BLOCK on the first /091 draft was exactly this
    # conflation):
    #   1. The CPCV flattened-(symbol,timestamp)-ROW gap:
    #        XS_REQUIRED_GAP = (H+1) * N_symbols
    #      This is a ROW COUNT — correct for the pooled-panel CPCV, which purges
    #      a count of flattened rows and converts back to timestamps internally
    #      (`cross_sectional.py` line ~625: `gap_ts_steps = gap_ts // N`).
    #   2. The walk-forward WALL-CLOCK time embargo:
    #        embargo_ms = (H+1) * interval_ms
    #      `_generate_xs_monthly_splits` does `train_end_ms = test_start_ms -
    #      embargo_ms` — a TIMESTAMP subtraction. At a timestamp t every symbol's
    #      label uses close(t+H); all symbols require the SAME (H+1) candle-
    #      intervals of TIME clearance. The clearance is INDEPENDENT of N — the
    #      `×N` row-count factor must NOT appear in a wall-clock embargo (that
    #      over-embargoes by N=22×: e.g. at H=28, 213 days instead of ~9.7 days,
    #      stripping ~7 months of training data from every monthly fold). The
    #      CPCV's own `// N` division proves (H+1)×N rows span exactly (H+1)
    #      timestamps. Fixed at the iter-v3/091 Phase-5.5 BLOCK re-work.
    interval_ms = 8 * 3600 * 1000
    all_ts = np.sort(panel_is["open_time"].unique())

    grid_rows: list[dict] = []
    mf_rows: list[dict] = []

    for H in HORIZON_GRID:  # noqa: N806 — H is the canonical horizon symbol
        # CPCV flattened-ROW gap (a row count) — correct as (H+1)*N. Reported
        # in the H1 grid as `xs_required_gap`; consumed by the pooled CPCV.
        required_gap = (H + 1) * N_XS
        # Walk-forward WALL-CLOCK TIME embargo — (H+1) candle-intervals of TIME.
        # NO `×N`: the row-count factor would over-embargo a timestamp quantity
        # by 22×. `_generate_xs_monthly_splits` subtracts this from a ms
        # timestamp (`train_end_ms = test_start_ms - embargo_ms`).
        embargo_ms = (H + 1) * interval_ms
        embargo_days = (H + 1) * 8 / 24
        splits = _generate_xs_monthly_splits(
            all_timestamps=all_ts,
            training_months=EDA_TRAINING_MONTHS,
            embargo_ms=embargo_ms,
        )
        if not splits:
            print(f"\n[H={H}] ERROR: no IS-internal splits — abort this horizon.")
            continue

        print(f"\n{'-' * 78}")
        print(
            f"[H={H}]  hold={H} bars (~{H * 8 / 24:.1f} days)  "
            f"CPCV row-gap=(H+1)*N={required_gap}  "
            f"WF time-embargo=(H+1) intervals={H + 1} (~{embargo_days:.1f} days)  "
            f"IS-internal test months={len(splits)}"
        )

        # --- model-free momentum-rank cross-check (M-block) ------------------
        mf = model_free_horizon_scan(panel_is, ret_wide, horizon=H)
        mf["horizon_bars"] = H
        mf["horizon_days"] = round(H * 8 / 24, 2)
        mf_rows.append(mf)
        print(
            f"[H={H}]  M-block (model-free trailing-{H}-bar momentum rank): "
            f"gross Sharpe {mf.get('mf_gross_monthly_sharpe', 0.0):+.4f}  "
            f"net Sharpe {mf.get('mf_net_monthly_sharpe', 0.0):+.4f}"
        )

        # --- trained LGBMRanker, H-matched label + hold (the operative scan) -
        trained, mean_ic = train_rankers_for_horizon(panel_is, horizon=H, splits=splits)
        print(
            f"[H={H}]  trained {len(trained)} monthly rankers; "
            f"mean IS-train rank-IC {mean_ic:+.4f}"
        )

        r = is_internal_backtest(
            panel_is,
            ret_wide,
            splits,
            trained,
            quantile_frac=XS_QUANTILE_FRAC,
            hold_bars=H,
            no_trade_band=XS_NO_TRADE_BAND,
        )
        if not r:
            print(f"[H={H}]  ERROR: backtest produced no rows.")
            continue
        row = {
            "horizon_bars": H,
            "horizon_days": round(H * 8 / 24, 2),
            "xs_required_gap": required_gap,
            "is_train_rank_ic": round(mean_ic, 4),
            "is_gross_monthly_sharpe": r["is_gross_monthly_sharpe"],
            "is_net_monthly_sharpe": r["is_net_monthly_sharpe"],
            "is_turnover_per_bar": r["mean_turnover_per_bar"],
            "is_fee_over_abs_gross": r["fee_over_abs_gross"],
            "is_gross_pnl": r["is_gross_pnl"],
            "is_net_pnl": r["is_net_pnl"],
            "max_symbol_concentration_pct": r["max_symbol_concentration_pct"],
            "is_bars": r["is_bars"],
        }
        grid_rows.append(row)
        print(
            f"[H={H}]  TRAINED book: gross Sharpe {r['is_gross_monthly_sharpe']:+.4f}  "
            f"net Sharpe {r['is_net_monthly_sharpe']:+.4f}  "
            f"turnover/bar {r['mean_turnover_per_bar']:.4f}  "
            f"fee/|gross| {r['fee_over_abs_gross']}"
        )

    if not grid_rows:
        print("\nERROR: no horizon produced a result. Abort.")
        return

    # --- write the horizon-grid table ------------------------------------
    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(OUT / "H1_horizon_grid.csv", index=False)
    mf_df = pd.DataFrame(mf_rows)
    mf_df.to_csv(OUT / "H2_model_free_horizon_scan.csv", index=False)

    # --- pre-register the IS-best horizon (by IS NET spread monthly Sharpe) -
    # The diary asks whether a longer horizon beats hold=3 NET of cost — so the
    # operative selection metric is the IS NET spread monthly Sharpe.
    best = grid_df.loc[grid_df["is_net_monthly_sharpe"].idxmax()]
    incumbent = grid_df[grid_df["horizon_bars"] == 3]
    incumbent_net = (
        float(incumbent["is_net_monthly_sharpe"].iloc[0]) if not incumbent.empty else float("nan")
    )
    best_H = int(best["horizon_bars"])  # noqa: N806 — canonical horizon symbol
    best_net = float(best["is_net_monthly_sharpe"])
    best_gross = float(best["is_gross_monthly_sharpe"])

    # --- monotonicity / hump sanity-check --------------------------------
    # The literature predicts a HUMP (gross spread builds with H then reverses).
    # Check: is the IS gross spread monthly Sharpe non-monotone with a single
    # interior peak?
    g = grid_df.sort_values("horizon_bars")["is_gross_monthly_sharpe"].to_numpy()
    hs = grid_df.sort_values("horizon_bars")["horizon_bars"].to_numpy()
    peak_idx = int(np.argmax(g))
    is_hump = (0 < peak_idx < len(g) - 1)
    peak_H = int(hs[peak_idx])  # noqa: N806 — canonical horizon symbol

    summary = pd.DataFrame(
        [
            {"metric": "horizon_grid_bars", "value": str(list(HORIZON_GRID))},
            {"metric": "incumbent_horizon_bars", "value": 3},
            {"metric": "incumbent_IS_net_spread_monthly_sharpe", "value": round(incumbent_net, 4)},
            {"metric": "IS_best_horizon_bars", "value": best_H},
            {"metric": "IS_best_horizon_days", "value": round(best_H * 8 / 24, 2)},
            {"metric": "IS_best_net_spread_monthly_sharpe", "value": round(best_net, 4)},
            {"metric": "IS_best_gross_spread_monthly_sharpe", "value": round(best_gross, 4)},
            {
                "metric": "IS_best_net_minus_incumbent_net",
                "value": round(best_net - incumbent_net, 4),
            },
            {"metric": "IS_best_xs_required_gap", "value": int(best["xs_required_gap"])},
            {"metric": "IS_best_turnover_per_bar", "value": float(best["is_turnover_per_bar"])},
            {
                "metric": "IS_best_fee_over_abs_gross",
                "value": float(best["is_fee_over_abs_gross"]),
            },
            {"metric": "gross_spread_peak_horizon_bars", "value": peak_H},
            {
                "metric": "gross_spread_shape_is_interior_hump",
                "value": bool(is_hump),
            },
            {
                "metric": "axis_verdict",
                "value": (
                    "HORIZON-CONFIRMED (a longer horizon beats hold=3 on IS net spread "
                    "monthly Sharpe)"
                    if best_H != 3 and best_net > incumbent_net
                    else "HORIZON-NOT-CONFIRMED (no horizon beats hold=3 net of cost)"
                ),
            },
        ]
    )
    summary.to_csv(OUT / "H3_horizon_summary.csv", index=False)

    # --- print the consolidated summary ----------------------------------
    print("\n" + "=" * 78)
    print("HORIZON-GRID SUMMARY — /091 holding-horizon axis, IS data only")
    print("=" * 78)
    print(
        f"{'H(bars)':>8} {'~days':>7} {'gap':>6} {'IS-IC':>8} "
        f"{'gross-Shrp':>11} {'net-Shrp':>10} {'turn/bar':>9} {'fee/gross':>10}"
    )
    for _, rr in grid_df.sort_values("horizon_bars").iterrows():
        print(
            f"{int(rr['horizon_bars']):>8} {rr['horizon_days']:>7.1f} "
            f"{int(rr['xs_required_gap']):>6} {rr['is_train_rank_ic']:>+8.4f} "
            f"{rr['is_gross_monthly_sharpe']:>+11.4f} {rr['is_net_monthly_sharpe']:>+10.4f} "
            f"{rr['is_turnover_per_bar']:>9.4f} {rr['is_fee_over_abs_gross']:>10.3f}"
        )
    print("-" * 78)
    print("MODEL-FREE cross-check (trailing-H-bar momentum rank, no LGBMRanker):")
    print(f"{'H(bars)':>8} {'~days':>7} {'gross-Shrp':>11} {'net-Shrp':>10}")
    for _, rr in mf_df.sort_values("horizon_bars").iterrows():
        print(
            f"{int(rr['horizon_bars']):>8} {rr['horizon_days']:>7.1f} "
            f"{rr.get('mf_gross_monthly_sharpe', 0.0):>+11.4f} "
            f"{rr.get('mf_net_monthly_sharpe', 0.0):>+10.4f}"
        )
    print("-" * 78)
    print(f"  Incumbent H=3 (~1 day):  IS net spread monthly Sharpe {incumbent_net:+.4f}")
    print(
        f"  IS-BEST horizon: H={best_H} (~{best_H * 8 / 24:.1f} days):  "
        f"IS net spread monthly Sharpe {best_net:+.4f}  "
        f"(gross {best_gross:+.4f})"
    )
    print(
        f"  IS-best vs incumbent (net spread monthly Sharpe delta): "
        f"{best_net - incumbent_net:+.4f}"
    )
    print(
        f"  gross-spread shape: peak at H={peak_H} bars; "
        f"interior hump = {is_hump} "
        f"({'literature-consistent' if is_hump else 'monotone — refutes the hump'})"
    )
    print(f"  IS-best XS_REQUIRED_GAP = (H+1)*N = ({best_H}+1)*{N_XS} = {(best_H + 1) * N_XS}")
    verdict = (
        "HORIZON-CONFIRMED"
        if best_H != 3 and best_net > incumbent_net
        else "HORIZON-NOT-CONFIRMED"
    )
    print(f"  AXIS VERDICT: {verdict}")
    print("  ALL tables IS-only. Walk-forward trains+tests inside IS; no OOS row read.")
    print("  Horizon selected on IS NET spread monthly Sharpe (the net-of-cost metric).")
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main())

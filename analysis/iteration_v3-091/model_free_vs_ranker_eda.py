"""iter-v3/091 — FOCUSED EDA — model-free cross-sectional momentum vs the trained
LGBMRanker, at the literature weekly horizon H=21. IS-ONLY.

WHY THIS EDA EXISTS — the corrected `holding_horizon_eda.py` surfaced a finding
the re-worked horizon-extension brief did not exploit.

  The corrected (embargo-fixed) horizon-grid EDA shows, at H=21 (~7 days — the
  cross-sectional-crypto-momentum literature's weekly horizon):
    H2  model-free trailing-21-bar momentum-rank book: IS net spread monthly
        Sharpe = +0.2964   (H2_model_free_horizon_scan.csv, embargo-independent)
    H1  trained LGBMRanker book (8 Optuna trials/month):  IS net spread monthly
        Sharpe = -0.0125   (H1_horizon_grid.csv, corrected embargo)
  A ~0.31 gap. A PARAMETER-FREE trailing-return quintile long-short DRAMATICALLY
  beats the trained LGBMRanker — IDENTICAL /089 cost-aware construction, cost
  model, and `_monthly_sharpe`; the ONLY difference is the SCORING function.

  Note the flip: at H=3 the LGBMRanker net spread (-0.2917) is close to model-
  free (-0.2143) and the model-free already wins; at H=21 model-free wins
  DECISIVELY. A plausible cause: the /088/089 13-feature stack was built for the
  H=3 label and is horizon-mismatched at H=21 — the ranker fits short-horizon
  features as noise and DEGRADES the clean long-horizon momentum signal.

  The implication: the re-worked /091 axis ("extend the LGBMRanker's holding
  horizon") tests the WRONG thing. The corrected EDA says the LGBMRanker ITSELF
  is the bottleneck. /091 should test whether scoring the cross-section
  MODEL-FREE recovers the signal the LGBMRanker is destroying.

WHAT THIS EDA CONFIRMS (3 stress-tests + 1 diagnosis) — all IS-ONLY.

  M1 — STRESS-TEST the model-free finding. Confirm the model-free cross-sectional
       momentum book at H=21 is genuinely ~+0.30 IS net spread monthly Sharpe and
       ROBUST — not an artifact of the 6-point lookback-grid selection. Two
       robustness checks: (a) a fine horizon sweep H ∈ {17..25} around H=21
       (does +0.30 persist off the grid point?); (b) IS sub-period stability
       (split the IS window into 3 contiguous thirds; is the H=21 book positive
       in each, or carried by one regime?). Runner-fidelity /089 cost-aware
       construction. The model-free book TRAINS NOTHING — embargo-independent.

  M2 — STRESS-TEST the LGBMRanker side. The H1 EDA used 8 Optuna trials/month;
       the runner uses 35. Re-run the trained LGBMRanker at H=21 at the FULL
       35-trial budget. If even at full Optuna budget the LGBMRanker net spread
       < model-free, the model-free-beats-trained finding is ROCK-SOLID. (If 35
       trials CLOSE the gap, the finding is budget-sensitive and the axis call
       changes.)

  M3 — DIAGNOSE WHY. Feature-importance / horizon-appropriateness. Train the
       LGBMRanker on the H=3 label and on the H=21 label; inspect the gain-based
       feature importance of the 13-feature stack at each horizon. Are the
       features horizon-matched to a ~21-bar label, or short-horizon features
       (fast RSI, short-window returns/vol) that become noise at H=21? Also
       report per-feature univariate IS rank-IC vs the H=21 forward-return rank
       — a direct read of whether the stack's features even correlate with the
       long-horizon target.

NO-CHEATING:
  - OOS_CUTOFF_MS / training_months are IMMUTABLE. The IS-internal walk-forward
    trains the ranker ONLY on IS months and predicts the NEXT IS month — no OOS
    row is ever read (panel sliced to open_time < OOS_CUTOFF_MS).
  - The model-free book reads only IS rows; the momentum proxy at bar t uses
    close(t) and close(t-H) only — both <= t. The 1-bar forward PnL return is
    strictly after t (searchsorted side='right').
  - The walk-forward wall-clock embargo is the CORRECTED (H+1)*interval_ms
    (NOT *N) — the Phase-5.5-BLOCK fix; the model-free book is embargo-
    independent regardless.
  - The QR sees OOS for the first time in Phase 7.

Run: uv run python analysis/iteration_v3-091/model_free_vs_ranker_eda.py
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
# must measure the SAME model + construction the /091 build runs.
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
# The /088/089 13-feature base stack (V3_FEATURE_COLUMNS_TOP_N minus btc_ret_14d,
# the XS_DROP_FEATURES drop) — the stack /090's downside features are reverted
# back to. This is the stack the /091 build runs and the stack M3 diagnoses.
XS_FEATURE_COLUMNS = [c for c in V3_FEATURE_COLUMNS_TOP_N if c not in XS_DROP_FEATURES]
N_XS = len(XS_UNIVERSE)  # 22

# --- the pre-registered weekly horizon -----------------------------------------
# H=21 8h-bars = ~7 days — the cross-sectional-crypto-momentum literature's
# weekly rebalance (Starkiller Capital SSRN 4322637; Dobrynskaya SSRN 3913263).
# H_PRIMARY is the operative /091 horizon; H_INCUMBENT is the /088/089/090 hold.
H_PRIMARY = 21
H_INCUMBENT = 3
# M1(a) fine sweep AROUND H=21 — does the model-free +0.30 persist OFF the
# 6-point grid? If H=21 is an artifact of the coarse grid, the neighbours fall
# away; if it is the genuine literature horizon, the plateau is wide and smooth.
H_FINE_SWEEP: tuple[int, ...] = (17, 18, 19, 20, 21, 22, 23, 24, 25)

# EDA controls.
EDA_N_TRIALS_LIGHT = 8  # the H1-EDA trial budget (the "light proxy")
EDA_N_TRIALS_FULL = 35  # the RUNNER's trial budget — the M2 stress-test
EDA_TRAINING_MONTHS = 24  # the IMMUTABLE training window
INTERVAL_MS = 8 * 3600 * 1000
FEE_PER_SIDE = 0.001  # 0.1% — the modeled Binance-futures-grade taker cost
BARS_PER_YEAR = 3.0 * 365.0  # 8h bars
SEED = 42


# ---------------------------------------------------------------------------
# Shared monthly-Sharpe helper — the /090-BLOCK fix. ONE function computes both
# gross and net monthly Sharpe from a PnL column, on the identical per-calendar-
# month basis. This is the EXACT method `run_cross_sectional_v3.py` uses.
# ---------------------------------------------------------------------------


def _monthly_sharpe(df: pd.DataFrame, pnl_col: str) -> float:
    """Per-calendar-month Sharpe of a PnL column (mean/std, ddof=1, no annualization)."""
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
# /089 cost-aware construction primitives — corrected-sign quintile, inverse-vol,
# vol-target, overlapping tranches, no-trade band. Verbatim from the /089 EDA
# harness (and structurally identical to cross_sectional.py::build_positions).
# ---------------------------------------------------------------------------


def _inv_vol_weights(leg_syms: list[str], vol_map: dict[str, float]) -> dict[str, float]:
    """Inverse-vol weights within a leg."""
    inv = {s: 1.0 / max(vol_map.get(s, 1.0), 1e-8) for s in leg_syms}
    tot = sum(inv.values())
    return {s: v / tot for s, v in inv.items()} if tot > 0 else {}


def _target_positions(
    syms: np.ndarray,
    scores: np.ndarray,
    vol_map: dict[str, float],
    quantile_frac: float,
) -> dict[str, float]:
    """CORRECTED-SIGN dollar-neutral target positions: LONG high score, SHORT low."""
    n = len(syms)
    order = np.argsort(scores)  # ascending
    sorted_syms = syms[order]
    n_leg = max(1, int(np.floor(n * quantile_frac)))
    short_syms = list(sorted_syms[:n_leg])  # LOW score  -> SHORT
    long_syms = list(sorted_syms[-n_leg:])  # HIGH score -> LONG
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
    """No-trade band: carry the previous weight unless the target moved by > tau."""
    if tau <= 0.0:
        return dict(target)
    out: dict[str, float] = {}
    for s in set(target) | set(prev):
        t = target.get(s, 0.0)
        p = prev.get(s, 0.0)
        out[s] = t if abs(t - p) > tau else p
    return {s: v for s, v in out.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------------------
# The shared cost-aware book runner — takes a per-bar SCORING CALLBACK.
# This is the structural heart of the EDA: the model-free book and the trained
# book differ ONLY in the scoring callback. Everything downstream — quintile
# legs, inverse-vol, vol-target, overlapping tranches, no-trade band, the
# turnover-based fee, the per-calendar-month Sharpe — is byte-identical.
# ---------------------------------------------------------------------------


def _run_cost_aware_book(
    bars: list[tuple[int, np.ndarray, np.ndarray]],
    ret_wide: pd.DataFrame,
    hold_bars: int,
    quantile_frac: float = XS_QUANTILE_FRAC,
    no_trade_band: float = XS_NO_TRADE_BAND,
) -> pd.DataFrame:
    """Run the /089 cost-aware quintile long-short book over a list of scored bars.

    `bars` is a time-ordered list of (timestamp_ms, symbols, scores) — the
    scoring is done by the caller (model-free OR trained). The /089 construction
    is applied identically: corrected-sign quintile legs, inverse-vol within
    leg, portfolio vol-target, overlapping `hold_bars`-tranches, no-trade band,
    turnover-based fee. Returns a per-(timestamp, symbol) PnL DataFrame.
    """
    rows: list[dict] = []
    tranches: list[tuple[int, dict[str, float]]] = []
    prev_book: dict[str, float] = {}
    bar_idx = 0
    for ts, syms, scores in bars:
        if len(syms) < XS_MIN_SYMBOLS_PER_BAR:
            continue
        hist = ret_wide[ret_wide.index < ts].tail(XS_VOL_LOOKBACK)
        vol_map = {
            s: (
                max(float(hist[s].dropna().std()), 1e-8)
                if s in hist.columns and hist[s].dropna().shape[0] >= 2
                else 1.0
            )
            for s in syms
        }
        tgt = _target_positions(syms, scores, vol_map, quantile_frac)
        tgt = _scale_to_vol_target(tgt, hist)

        # overlapping tranches: new tranche = (1/hold_bars) of target
        new_tranche = {s: w / hold_bars for s, w in tgt.items()}
        tranches.append((bar_idx + hold_bars, new_tranche))
        tranches = [(rb, w) for (rb, w) in tranches if rb > bar_idx]
        book: dict[str, float] = {}
        for _, w in tranches:
            for s, v in w.items():
                book[s] = book.get(s, 0.0) + v
        book = _apply_no_trade_band(book, prev_book, no_trade_band)

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
    return pd.DataFrame(rows)


def _book_metrics(df: pd.DataFrame) -> dict:
    """Summary metrics of a cost-aware book DataFrame."""
    if df.empty:
        return {
            "gross_monthly_sharpe": 0.0,
            "net_monthly_sharpe": 0.0,
            "turnover_per_bar": 0.0,
            "fee_over_abs_gross": float("inf"),
            "is_bars": 0,
            "max_symbol_concentration_pct": 0.0,
        }
    gross = float(df["gross_pnl"].sum())
    feet = float(df["fee"].sum())
    turn_bar = float(df.groupby("open_time")["fee"].sum().mean()) / FEE_PER_SIDE
    psym = df.groupby("symbol")["net_pnl"].sum().abs()
    conc = float(psym.max() / psym.sum() * 100) if psym.sum() > 0 else 0.0
    return {
        "gross_monthly_sharpe": round(_monthly_sharpe(df, "gross_pnl"), 4),
        "net_monthly_sharpe": round(_monthly_sharpe(df, "net_pnl"), 4),
        "turnover_per_bar": round(turn_bar, 4),
        "fee_over_abs_gross": (
            round(feet / abs(gross), 3) if abs(gross) > 1e-9 else float("inf")
        ),
        "is_bars": int(df["open_time"].nunique()),
        "max_symbol_concentration_pct": round(conc, 1),
    }


# ---------------------------------------------------------------------------
# Model-free scoring — the raw trailing-H-bar return as the cross-sectional
# score. NO model trained. This IS the /091 candidate axis.
# ---------------------------------------------------------------------------


def _model_free_bars(
    panel_is: pd.DataFrame, horizon: int
) -> list[tuple[int, np.ndarray, np.ndarray]]:
    """Build the time-ordered (ts, syms, scores) list for the model-free book.

    The score is the trailing-H-bar return `close(t)/close(t-H) - 1` — a
    standard cross-sectional momentum signal. Past-only: close(t), close(t-H)
    both <= t.
    """
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    mom_wide = close_wide / close_wide.shift(horizon) - 1.0
    bars: list[tuple[int, np.ndarray, np.ndarray]] = []
    for ts in mom_wide.index.to_numpy():
        mom_t = mom_wide.loc[ts].dropna()
        if len(mom_t) < XS_MIN_SYMBOLS_PER_BAR:
            continue
        bars.append((int(ts), mom_t.index.to_numpy(), mom_t.to_numpy()))
    return bars


# ---------------------------------------------------------------------------
# Trained-LGBMRanker scoring — IS-internal walk-forward, H-matched label + hold.
# ---------------------------------------------------------------------------


def _train_rankers(
    panel_is: pd.DataFrame,
    horizon: int,
    splits: list[dict],
    n_trials: int,
) -> tuple[dict[str, CrossSectionalRankStrategy], float]:
    """Label IS panel at horizon=H, train one LGBMRanker per IS test month.

    Returns (trained_models keyed by test_month, mean IS-train rank-IC).
    """
    labels_is = label_cross_sectional_rank(panel_is, horizon=horizon)
    trained: dict[str, CrossSectionalRankStrategy] = {}
    ics: list[float] = []
    for split in splits:
        tm = split["test_month"]
        train_mask = (panel_is["open_time"] >= split["train_start_ms"]) & (
            panel_is["open_time"] < split["train_end_ms"]
        )
        tp = panel_is[train_mask].copy()
        tl = labels_is[train_mask]
        valid = tl.notna()
        tp_v = tp[valid].sort_values(["open_time", "symbol"]).reset_index(drop=True)
        tl_v = tl[valid].reset_index(drop=True).reindex(tp_v.index)
        if len(tp_v) < 100:
            continue
        strat = CrossSectionalRankStrategy(
            training_months=EDA_TRAINING_MONTHS,
            n_trials=n_trials,
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
        ics.append(ic)
    return trained, (float(np.mean(ics)) if ics else 0.0)


def _trained_bars(
    panel_is: pd.DataFrame,
    splits: list[dict],
    trained: dict[str, CrossSectionalRankStrategy],
) -> list[tuple[int, np.ndarray, np.ndarray]]:
    """Build the (ts, syms, scores) list from the per-month trained rankers.

    Each test month's bars are scored by THAT month's ranker (the IS-internal
    walk-forward — never an OOS row, never a future-month model).
    """
    bars: list[tuple[int, np.ndarray, np.ndarray]] = []
    for split in splits:
        strat = trained.get(split["test_month"])
        if strat is None or strat._model is None:
            continue
        test_mask = (panel_is["open_time"] >= split["test_start_ms"]) & (
            panel_is["open_time"] < split["test_end_ms"]
        )
        test_panel = panel_is[test_mask].copy()
        if test_panel.empty:
            continue
        for ts in np.sort(test_panel["open_time"].unique()):
            panel_t = test_panel[test_panel["open_time"] == ts].reset_index(drop=True)
            if len(panel_t) < XS_MIN_SYMBOLS_PER_BAR:
                continue
            x_t = panel_t[strat.feature_columns].values.astype(np.float32)
            bars.append(
                (int(ts), panel_t["symbol"].to_numpy(), strat._model.predict(x_t))
            )
    return bars


# ---------------------------------------------------------------------------
# M3 — feature-importance / horizon-appropriateness diagnosis.
# ---------------------------------------------------------------------------


def _univariate_rank_ic(panel_is: pd.DataFrame, horizon: int) -> dict[str, float]:
    """Per-feature univariate IS rank-IC vs the H-bar-forward return rank.

    For each feature, the per-timestamp Spearman correlation between the feature
    value and the realised H-bar-forward cross-sectional return, averaged over
    all IS timestamps. A direct read of whether the stack's features even
    correlate with the long-horizon target.
    """
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    fwd_wide = close_wide.shift(-horizon) / close_wide - 1.0  # H-bar-forward return
    out: dict[str, float] = {}
    for feat in XS_FEATURE_COLUMNS:
        ics: list[float] = []
        for ts in np.sort(panel_is["open_time"].unique()):
            sub = panel_is[panel_is["open_time"] == ts]
            if len(sub) < XS_MIN_SYMBOLS_PER_BAR or ts not in fwd_wide.index:
                continue
            fwd_row = fwd_wide.loc[ts]
            merged = pd.DataFrame(
                {
                    "feat": sub.set_index("symbol")[feat],
                    "fwd": fwd_row,
                }
            ).dropna()
            if len(merged) < XS_MIN_SYMBOLS_PER_BAR:
                continue
            fr = merged["feat"].rank()
            yr = merged["fwd"].rank()
            if fr.std() > 1e-12 and yr.std() > 1e-12:
                ics.append(float(np.corrcoef(fr, yr)[0, 1]))
        out[feat] = float(np.mean(ics)) if ics else 0.0
    return out


def _feature_importance(
    trained: dict[str, CrossSectionalRankStrategy],
) -> dict[str, float]:
    """Mean gain-based feature importance across the per-month trained rankers."""
    cols = XS_FEATURE_COLUMNS
    acc = {c: [] for c in cols}
    for strat in trained.values():
        if strat._model is None:
            continue
        imp = strat._model.feature_importances_  # gain-based by default in LGBM sklearn
        tot = float(imp.sum()) if imp.sum() > 0 else 1.0
        for i, c in enumerate(cols):
            acc[c].append(float(imp[i]) / tot * 100.0)  # percent of total gain
    return {c: (float(np.mean(v)) if v else 0.0) for c, v in acc.items()}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:  # noqa: C901 — a single linear EDA script
    print("=" * 80)
    print("iter-v3/091 FOCUSED EDA — model-free cross-sectional momentum vs the")
    print("trained LGBMRanker at the literature weekly horizon H=21 — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print(f"Universe: {N_XS} symbols; /088/089 13-feature base stack")
    print(f"Construction: /089 cost-aware (quintile q={XS_QUANTILE_FRAC}, ")
    print(f"  overlapping holds = horizon-matched, no-trade band tau={XS_NO_TRADE_BAND})")
    print("=" * 80)

    # --- build the pooled panel ONCE (IS rows only) -------------------------
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
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    ret_wide = close_wide.pct_change()
    all_ts = np.sort(panel_is["open_time"].unique())

    # =======================================================================
    # M1 — STRESS-TEST the model-free finding.
    # =======================================================================
    print("\n" + "-" * 80)
    print("M1 — STRESS-TEST: is the model-free H=21 book genuinely ~+0.30 IS net")
    print("     spread monthly Sharpe and ROBUST (not a 6-point-grid artifact)?")
    print("-" * 80)

    # M1(a) — fine horizon sweep around H=21.
    m1a_rows: list[dict] = []
    for H in H_FINE_SWEEP:  # noqa: N806
        bars = _model_free_bars(panel_is, horizon=H)
        df = _run_cost_aware_book(bars, ret_wide, hold_bars=H)
        m = _book_metrics(df)
        m1a_rows.append(
            {
                "horizon_bars": H,
                "horizon_days": round(H * 8 / 24, 2),
                "mf_gross_monthly_sharpe": m["gross_monthly_sharpe"],
                "mf_net_monthly_sharpe": m["net_monthly_sharpe"],
                "mf_turnover_per_bar": m["turnover_per_bar"],
                "mf_fee_over_abs_gross": m["fee_over_abs_gross"],
            }
        )
        print(
            f"[M1a] H={H:>2} (~{H * 8 / 24:>4.1f}d)  model-free: "
            f"gross {m['gross_monthly_sharpe']:+.4f}  net {m['net_monthly_sharpe']:+.4f}  "
            f"turnover/bar {m['turnover_per_bar']:.4f}"
        )
    m1a_df = pd.DataFrame(m1a_rows)
    m1a_df.to_csv(OUT / "M1a_model_free_fine_sweep.csv", index=False)
    sweep_net = m1a_df["mf_net_monthly_sharpe"].to_numpy()
    sweep_min, sweep_max = float(sweep_net.min()), float(sweep_net.max())
    print(
        f"[M1a] fine-sweep H∈{list(H_FINE_SWEEP)}: net spread Sharpe range "
        f"[{sweep_min:+.4f}, {sweep_max:+.4f}] — "
        f"{'WIDE SMOOTH PLATEAU (robust)' if sweep_min > 0.15 else 'NOT a robust plateau'}"
    )

    # M1(b) — IS sub-period stability of the H=21 model-free book.
    # Split the IS window into 3 contiguous thirds by timestamp; recompute the
    # H=21 model-free book's net monthly Sharpe restricted to each third.
    print()
    bars_h21 = _model_free_bars(panel_is, horizon=H_PRIMARY)
    df_h21_full = _run_cost_aware_book(bars_h21, ret_wide, hold_bars=H_PRIMARY)
    m_h21_full = _book_metrics(df_h21_full)
    thirds = np.array_split(np.sort(df_h21_full["open_time"].unique()), 3)
    m1b_rows: list[dict] = []
    for i, third_ts in enumerate(thirds):
        sub = df_h21_full[df_h21_full["open_time"].isin(third_ts)]
        lo = datetime.datetime.fromtimestamp(
            int(third_ts[0]) / 1000, tz=datetime.UTC
        ).strftime("%Y-%m")
        hi = datetime.datetime.fromtimestamp(
            int(third_ts[-1]) / 1000, tz=datetime.UTC
        ).strftime("%Y-%m")
        sg = _monthly_sharpe(sub, "gross_pnl")
        sn = _monthly_sharpe(sub, "net_pnl")
        m1b_rows.append(
            {
                "sub_period": f"third_{i + 1}",
                "window": f"{lo}..{hi}",
                "mf_gross_monthly_sharpe": round(sg, 4),
                "mf_net_monthly_sharpe": round(sn, 4),
                "n_bars": int(sub["open_time"].nunique()),
            }
        )
        print(
            f"[M1b] H=21 model-free, sub-period {i + 1} ({lo}..{hi}): "
            f"gross {sg:+.4f}  net {sn:+.4f}  ({sub['open_time'].nunique()} bars)"
        )
    m1b_df = pd.DataFrame(m1b_rows)
    m1b_df.to_csv(OUT / "M1b_model_free_subperiod_stability.csv", index=False)
    n_positive_thirds = int((m1b_df["mf_net_monthly_sharpe"] > 0).sum())
    print(
        f"[M1b] H=21 model-free net spread positive in {n_positive_thirds}/3 IS "
        f"sub-periods — {'stable (not one-regime)' if n_positive_thirds >= 2 else 'regime-concentrated'}"
    )

    # =======================================================================
    # M2 — STRESS-TEST the LGBMRanker side: 8 trials vs 35 trials at H=21.
    # =======================================================================
    print("\n" + "-" * 80)
    print("M2 — STRESS-TEST: does the LGBMRanker at the runner's 35 Optuna trials")
    print("     close the gap to model-free at H=21? (H1 EDA used only 8.)")
    print("-" * 80)

    # corrected walk-forward wall-clock embargo — (H+1)*interval_ms, NOT *N.
    embargo_ms_h21 = (H_PRIMARY + 1) * INTERVAL_MS
    splits_h21 = _generate_xs_monthly_splits(
        all_timestamps=all_ts,
        training_months=EDA_TRAINING_MONTHS,
        embargo_ms=embargo_ms_h21,
    )
    print(
        f"[M2] H=21 corrected WF embargo = (21+1)*interval = 22 candles "
        f"(~{22 * 8 / 24:.1f}d); IS-internal test months = {len(splits_h21)}"
    )

    m2_rows: list[dict] = []
    trained_h21_full: dict[str, CrossSectionalRankStrategy] = {}
    for n_trials, tag in ((EDA_N_TRIALS_LIGHT, "8-trial (H1-EDA)"), (EDA_N_TRIALS_FULL, "35-trial (runner)")):
        trained, mean_ic = _train_rankers(panel_is, H_PRIMARY, splits_h21, n_trials=n_trials)
        bars = _trained_bars(panel_is, splits_h21, trained)
        df = _run_cost_aware_book(bars, ret_wide, hold_bars=H_PRIMARY)
        m = _book_metrics(df)
        if n_trials == EDA_N_TRIALS_FULL:
            trained_h21_full = trained  # keep for M3 importance
        m2_rows.append(
            {
                "n_optuna_trials": n_trials,
                "config": tag,
                "trained_lgbmranker_gross_monthly_sharpe": m["gross_monthly_sharpe"],
                "trained_lgbmranker_net_monthly_sharpe": m["net_monthly_sharpe"],
                "mean_is_train_rank_ic": round(mean_ic, 4),
                "turnover_per_bar": m["turnover_per_bar"],
                "n_monthly_models": len(trained),
            }
        )
        print(
            f"[M2] H=21 trained LGBMRanker @ {tag}: "
            f"gross {m['gross_monthly_sharpe']:+.4f}  net {m['net_monthly_sharpe']:+.4f}  "
            f"mean IS-train rank-IC {mean_ic:+.4f}"
        )
    m2_df = pd.DataFrame(m2_rows)
    m2_df.to_csv(OUT / "M2_lgbmranker_trial_budget.csv", index=False)
    trained_net_35 = float(
        m2_df.loc[m2_df["n_optuna_trials"] == EDA_N_TRIALS_FULL, "trained_lgbmranker_net_monthly_sharpe"].iloc[0]
    )
    mf_net_h21 = m_h21_full["net_monthly_sharpe"]
    print(
        f"[M2] VERDICT: model-free H=21 net {mf_net_h21:+.4f}  vs  trained LGBMRanker "
        f"@35-trial net {trained_net_35:+.4f}  — gap {mf_net_h21 - trained_net_35:+.4f}  "
        f"({'model-free wins at FULL budget (finding ROCK-SOLID)' if mf_net_h21 > trained_net_35 else '35 trials CLOSE the gap'})"
    )

    # =======================================================================
    # M3 — DIAGNOSE WHY: feature horizon-appropriateness.
    # =======================================================================
    print("\n" + "-" * 80)
    print("M3 — DIAGNOSE: is the /088/089 13-feature stack horizon-matched to a")
    print("     ~21-bar label, or short-horizon features that become noise at H=21?")
    print("-" * 80)

    # M3(a) — univariate IS rank-IC of each feature vs the H=3 and H=21 forward
    # return rank. A feature whose |rank-IC| collapses from H=3 to H=21 is a
    # short-horizon feature the H=21 ranker cannot use.
    ic_h3 = _univariate_rank_ic(panel_is, horizon=H_INCUMBENT)
    ic_h21 = _univariate_rank_ic(panel_is, horizon=H_PRIMARY)

    # M3(b) — gain-based feature importance of the H=21-label-trained ranker
    # (the 35-trial set from M2). Where does the H=21 ranker spend its gain?
    imp_h21 = _feature_importance(trained_h21_full)

    m3_rows: list[dict] = []
    for feat in XS_FEATURE_COLUMNS:
        m3_rows.append(
            {
                "feature": feat,
                "univariate_rank_ic_H3": round(ic_h3.get(feat, 0.0), 4),
                "univariate_rank_ic_H21": round(ic_h21.get(feat, 0.0), 4),
                "abs_ic_H3_minus_H21": round(
                    abs(ic_h3.get(feat, 0.0)) - abs(ic_h21.get(feat, 0.0)), 4
                ),
                "H21_ranker_gain_importance_pct": round(imp_h21.get(feat, 0.0), 2),
            }
        )
    m3_df = pd.DataFrame(m3_rows).sort_values(
        "H21_ranker_gain_importance_pct", ascending=False
    )
    m3_df.to_csv(OUT / "M3_feature_horizon_appropriateness.csv", index=False)
    print(
        f"{'feature':<28} {'IC@H3':>9} {'IC@H21':>9} {'|IC|H3-H21':>11} {'H21-gain%':>10}"
    )
    for _, rr in m3_df.iterrows():
        print(
            f"{rr['feature']:<28} {rr['univariate_rank_ic_H3']:>+9.4f} "
            f"{rr['univariate_rank_ic_H21']:>+9.4f} {rr['abs_ic_H3_minus_H21']:>+11.4f} "
            f"{rr['H21_ranker_gain_importance_pct']:>10.2f}"
        )
    # how much of the H=21 ranker's gain goes to features that are stronger at
    # H=3 than H=21 (|IC|H3 > |IC|H21) — i.e. horizon-mismatched features.
    mismatched = m3_df[m3_df["abs_ic_H3_minus_H21"] > 0]
    gain_on_mismatched = float(mismatched["H21_ranker_gain_importance_pct"].sum())
    mean_abs_ic_h3 = float(np.mean([abs(v) for v in ic_h3.values()]))
    mean_abs_ic_h21 = float(np.mean([abs(v) for v in ic_h21.values()]))
    print(
        f"\n[M3] mean |univariate rank-IC| of the 13-feature stack: "
        f"H=3 {mean_abs_ic_h3:.4f}  vs  H=21 {mean_abs_ic_h21:.4f}"
    )
    print(
        f"[M3] {len(mismatched)}/{len(m3_df)} features have stronger |IC| at H=3 "
        f"than H=21; the H=21 ranker spends {gain_on_mismatched:.1f}% of its gain on them"
    )

    # =======================================================================
    # CONSOLIDATED SUMMARY.
    # =======================================================================
    summary = pd.DataFrame(
        [
            {"metric": "M1_model_free_H21_net_spread_monthly_sharpe", "value": round(mf_net_h21, 4)},
            {"metric": "M1_model_free_H21_gross_spread_monthly_sharpe", "value": round(m_h21_full["gross_monthly_sharpe"], 4)},
            {"metric": "M1_model_free_H21_turnover_per_bar", "value": m_h21_full["turnover_per_bar"]},
            {"metric": "M1_model_free_H21_max_symbol_concentration_pct", "value": m_h21_full["max_symbol_concentration_pct"]},
            {"metric": "M1a_fine_sweep_net_spread_min", "value": round(sweep_min, 4)},
            {"metric": "M1a_fine_sweep_net_spread_max", "value": round(sweep_max, 4)},
            {"metric": "M1b_subperiods_net_positive", "value": f"{n_positive_thirds}/3"},
            {"metric": "M2_trained_lgbmranker_H21_net_8trial", "value": round(float(m2_df.loc[m2_df['n_optuna_trials'] == EDA_N_TRIALS_LIGHT, 'trained_lgbmranker_net_monthly_sharpe'].iloc[0]), 4)},
            {"metric": "M2_trained_lgbmranker_H21_net_35trial", "value": round(trained_net_35, 4)},
            {"metric": "M2_model_free_minus_trained_35trial_net", "value": round(mf_net_h21 - trained_net_35, 4)},
            {"metric": "M3_mean_abs_univariate_rank_ic_H3", "value": round(mean_abs_ic_h3, 4)},
            {"metric": "M3_mean_abs_univariate_rank_ic_H21", "value": round(mean_abs_ic_h21, 4)},
            {"metric": "M3_H21_ranker_gain_pct_on_horizon_mismatched_features", "value": round(gain_on_mismatched, 1)},
            {
                "metric": "model_free_beats_trained_at_full_budget",
                "value": bool(mf_net_h21 > trained_net_35),
            },
            {
                "metric": "finding_verdict",
                "value": (
                    "CONFIRMED — model-free cross-sectional momentum at H=21 beats the "
                    "trained LGBMRanker at the full 35-trial budget; the LGBMRanker degrades "
                    "a real cross-sectional momentum signal"
                    if mf_net_h21 > trained_net_35
                    else "NOT-CONFIRMED — 35 Optuna trials close the gap to model-free"
                ),
            },
        ]
    )
    summary.to_csv(OUT / "M4_focused_eda_summary.csv", index=False)

    print("\n" + "=" * 80)
    print("FOCUSED EDA SUMMARY — /091 model-free vs trained LGBMRanker — IS data only")
    print("=" * 80)
    print(f"  M1  model-free H=21 cross-sectional momentum book:")
    print(
        f"        IS net spread monthly Sharpe   {mf_net_h21:+.4f}   "
        f"(gross {m_h21_full['gross_monthly_sharpe']:+.4f})"
    )
    print(
        f"        fine sweep H∈[17,25] net range [{sweep_min:+.4f}, {sweep_max:+.4f}]  "
        f"-> {'wide smooth plateau' if sweep_min > 0.15 else 'NOT a plateau'}"
    )
    print(f"        IS sub-period net-positive in {n_positive_thirds}/3 thirds")
    print(f"  M2  trained LGBMRanker H=21:")
    print(
        f"        @ 8 Optuna trials  IS net spread monthly Sharpe "
        f"{float(m2_df.loc[m2_df['n_optuna_trials'] == EDA_N_TRIALS_LIGHT, 'trained_lgbmranker_net_monthly_sharpe'].iloc[0]):+.4f}"
    )
    print(
        f"        @ 35 Optuna trials IS net spread monthly Sharpe {trained_net_35:+.4f}"
    )
    print(
        f"        model-free MINUS trained@35-trial = {mf_net_h21 - trained_net_35:+.4f}"
    )
    print(f"  M3  feature horizon-appropriateness of the 13-feature stack:")
    print(
        f"        mean |univariate rank-IC|: H=3 {mean_abs_ic_h3:.4f}  H=21 {mean_abs_ic_h21:.4f}"
    )
    print(
        f"        {len(mismatched)}/{len(m3_df)} features stronger at H=3; H=21 ranker "
        f"spends {gain_on_mismatched:.1f}% of gain on them"
    )
    print("-" * 80)
    fv = summary.loc[summary["metric"] == "finding_verdict", "value"].iloc[0]
    print(f"  VERDICT: {fv}")
    print("  ALL tables IS-only. Model-free book trains nothing (embargo-independent).")
    print("  Trained LGBMRanker uses the corrected (H+1)*interval_ms walk-forward embargo.")
    print("=" * 80)


if __name__ == "__main__":
    sys.exit(main())

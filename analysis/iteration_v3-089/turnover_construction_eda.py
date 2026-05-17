"""iter-v3/089 — Cost-aware cross-sectional construction EDA (IS-ONLY).

The CORRECTED cross-sectional iteration. iter-v3/088 produced v3's FIRST genuine
OOS signal transfer (OOS rank-IC +0.0430, t~4.6) but the long-short BOOK lost
money (IS -0.64 / OOS -0.54) for two diagnosed reasons:
  (1) SIGN INVERSION — the /088 brief specified LONGing the model's predicted
      LOSERS. The LGBMRanker is trained on a FORWARD-return-grade label, so high
      predicted score = predicted future WINNER. The book must LONG high-score.
  (2) TURNOVER DRAG — IS fees were 8.8x the gross PnL. Every-8h-bar rebalance of
      a tercile (~30% gross book turnover/bar) buries a +0.04-rank-IC signal.

This EDA validates — ON IS DATA ONLY (open_time < OOS_CUTOFF_MS = 2025-03-24) —
the /089 cost-aware construction. It runs a TRUE IS-internal walk-forward of the
cross_sectional.py ranker (NO OOS row is ever read), then measures the
CORRECTED-SIGN net IS monthly Sharpe under each turnover-reduction lever:

  E1  Baseline replication — corrected-sign tercile every-bar book. Confirms the
      flipped-IS gross Sharpe ~ +0.067 figure the /088 engineering report quotes
      and quantifies the cost drag on the IS-internal walk-forward.
  E2  QUANTILE CONCENTRATION — tercile vs quartile vs quintile. Per Poh/Lim/Zohren
      (arXiv 2012.07149) an LTR model places assets in the right quantile with
      greater precision, so a tighter quantile STEEPENS the long-short spread.
      A quintile also turns over LESS gross book/bar. E2 measures both the gross
      signal effect AND the turnover effect of quantile concentration.
  E3  SLOWER REBALANCE / OVERLAPPING HOLDS — hold each tranche H_hold bars,
      rebalance 1/H_hold of the book per bar (the Jegadeesh-Titman 1993
      overlapping-portfolio construction). H_hold in {1,3,6}. Turnover falls
      ~H_hold-fold; the signal is H=3-bar-forward so a 3-bar hold is horizon-matched.
  E4  NO-TRADE BAND — only rebalance a symbol when its target weight moves more
      than a band threshold tau. Per Constantinides (1986) / Davis-Norman (1990)
      the optimal no-trade band scales O(eps^1/3) in the proportional cost eps;
      utility loss is O(eps^2/3). E4 scans tau and reports the turnover/cost
      tradeoff curve — the table that SETS the /089 pre-registered turnover ceiling.
  E5  COMBINED — corrected sign + quintile + 3-bar overlapping hold + the
      best-IS no-trade band. The /089 candidate construction; net IS Sharpe.
  E6  TURNOVER CEILING derivation — from E1-E5, the gross-turnover-per-bar at
      which the IS net Sharpe is maximised; the /089 brief pre-registers a
      ceiling at-or-below this as a HARD MERGE-blocking gate.

NO-CHEATING: the IS-internal walk-forward trains the ranker ONLY on IS months
and predicts on the NEXT IS month — never an OOS row. Every lever parameter
(quantile cutoff, hold length, no-trade band) is SELECTED on the IS net Sharpe
or set a-priori from the cited research. OOS_CUTOFF_MS / training_months are
IMMUTABLE. Outputs are CSVs committed alongside this script.

Run: uv run python analysis/iteration_v3-089/turnover_construction_eda.py
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

# Reuse the RETAINED /088 cross-sectional infrastructure verbatim — the EDA
# must measure the SAME model the /089 build runs, not a re-implementation.
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N  # noqa: E402
from crypto_trade.strategies.ml.cross_sectional import (  # noqa: E402
    XS_DROP_FEATURES,
    XS_HORIZON,
    XS_MIN_SYMBOLS_PER_BAR,
    XS_REQUIRED_GAP,
    XS_UNIVERSE,
    XS_VOL_LOOKBACK,
    CrossSectionalRankStrategy,
    _generate_xs_monthly_splits,
    build_cross_sectional_panel,
    label_cross_sectional_rank,
)

FEATURES_DIR = REPO / "data" / "features_v3"
XS_FEATURE_COLUMNS = [c for c in V3_FEATURE_COLUMNS_TOP_N if c not in XS_DROP_FEATURES]

# EDA controls — kept light (this is an EDA, not the Phase-6 backtest).
EDA_N_TRIALS = 8  # Optuna trials per IS month (fast; the full build uses 35)
EDA_TRAINING_MONTHS = 24  # the IMMUTABLE training window
BARS_PER_YEAR = 3.0 * 365.0  # 8h bars
FEE_PER_SIDE = 0.001  # 0.1% — the modeled Binance-futures-grade taker cost


# ---------------------------------------------------------------------------
# Construction primitives (cost-aware variants of build_positions)
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
    grade, so high predicted score = predicted future WINNER.  Therefore
    LONG the top quantile (high score) and SHORT the bottom quantile.
    This is the inverse of the /088 build (`cross_sectional.py:586-587`
    longed `sorted_syms[:n_leg]`, the LOW scores).

    Returns dollar-neutral inverse-vol target weights (gross long = gross
    short = 1.0, pre vol-target scaling).
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
        pos[s] = pos.get(s, 0.0) - w  # a symbol can't be both legs in disjoint quantiles
    return pos


def _scale_to_vol_target(
    pos: dict[str, float], hist: pd.DataFrame, vol_target: float = 0.10
) -> dict[str, float]:
    """Portfolio vol-target scaling (mirrors build_positions / _portfolio_vol)."""
    syms = list(pos.keys())
    if not syms or len(hist) < 2:
        return pos
    w = np.array([pos[s] for s in syms])
    rm = hist[[s for s in syms if s in hist.columns]].dropna(how="all")
    if rm.shape[0] < 2 or rm.shape[1] < 1:
        return pos
    cov = np.cov(rm.values.T)
    if cov.ndim == 0:
        pv = float(cov) * w[0] ** 2
    else:
        # align w to the columns actually present
        present = [s for s in syms if s in hist.columns]
        wp = np.array([pos[s] for s in present])
        pv = float(wp @ cov @ wp)
    ann = np.sqrt(max(pv, 0.0)) * np.sqrt(BARS_PER_YEAR)
    if ann > 1e-8:
        sc = vol_target / ann
        return {s: v * sc for s, v in pos.items()}
    return pos


def _apply_no_trade_band(
    target: dict[str, float], prev: dict[str, float], tau: float
) -> dict[str, float]:
    """No-trade band: hold the previous position for a symbol unless the
    target weight moved by more than tau.  Constantinides/Davis-Norman:
    when outside the band, rebalance to the (target) boundary.

    tau = 0  -> rebalance every symbol every bar (the /088 behaviour).
    tau > 0  -> only the symbols whose target moved > tau are re-traded;
                the rest carry their previous weight, paying ZERO fee.
    """
    if tau <= 0.0:
        return dict(target)
    out: dict[str, float] = {}
    all_syms = set(target) | set(prev)
    for s in all_syms:
        t = target.get(s, 0.0)
        p = prev.get(s, 0.0)
        out[s] = t if abs(t - p) > tau else p
    # drop dust
    return {s: v for s, v in out.items() if abs(v) > 1e-9}


# ---------------------------------------------------------------------------
# IS-internal cost-aware backtest of one construction variant
# ---------------------------------------------------------------------------


def is_internal_backtest(
    panel_is: pd.DataFrame,
    labels_is: pd.Series,
    ret_wide: pd.DataFrame,
    splits: list[dict],
    trained_models: dict[str, CrossSectionalRankStrategy],
    quantile_frac: float,
    hold_bars: int,
    no_trade_band: float,
    seed: int = 42,
) -> dict:
    """Run ONE construction variant over the IS-internal walk-forward.

    The model for each IS test month is taken from `trained_models` (trained
    ONCE up front, reused across all variants — so E1-E5 differ ONLY in
    construction, never in the model).  Returns a metrics dict.

    hold_bars > 1 implements OVERLAPPING tranches: at each bar a NEW tranche
    is formed sized 1/hold_bars of the book; it is held hold_bars bars then
    retired.  The book = the sum of the live tranches.  This is the
    Jegadeesh-Titman (1993) overlapping-portfolio construction; it cuts
    gross turnover ~hold_bars-fold.
    """
    rows: list[dict] = []
    # live tranches: list of (retire_bar_index, {sym: weight})
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
                s: max(float(hist[s].dropna().std()), 1e-8)
                if s in hist.columns and hist[s].dropna().shape[0] >= 2
                else 1.0
                for s in syms
            }

            # target book for THIS bar (full-size, dollar-neutral, vol-targeted)
            tgt = _target_positions(syms, scores, vol_map, quantile_frac)
            tgt = _scale_to_vol_target(tgt, hist)

            # ---- overlapping tranches: new tranche = (1/hold) of target ----
            new_tranche = {s: w / hold_bars for s, w in tgt.items()}
            tranches.append((bar_idx + hold_bars, new_tranche))
            tranches = [(rb, w) for (rb, w) in tranches if rb > bar_idx]
            # the book = sum of live tranches
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
        return {"variant": None}
    df = pd.DataFrame(rows)
    n_bars = df["open_time"].nunique()
    gross = float(df["gross_pnl"].sum())
    feet = float(df["fee"].sum())
    net = float(df["net_pnl"].sum())
    turn_bar = float(df.groupby("open_time")["fee"].sum().mean()) / FEE_PER_SIDE
    book_bar = float(df["position"].abs().groupby(df["open_time"]).sum().mean())

    # monthly Sharpe (gross and net) — the operative v3 metric
    df["month"] = df["open_time"].apply(
        lambda t: datetime.datetime.fromtimestamp(t / 1000, tz=datetime.UTC).strftime("%Y-%m")
    )
    mg = df.groupby("month")["gross_pnl"].sum()
    mn = df.groupby("month")["net_pnl"].sum()
    sg = float(mg.mean() / mg.std()) if len(mg) > 1 and mg.std() > 0 else 0.0
    sn = float(mn.mean() / mn.std()) if len(mn) > 1 and mn.std() > 0 else 0.0
    # per-symbol concentration
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
        "turnover_frac_of_book": round(turn_bar / book_bar, 3) if book_bar > 1e-9 else 0.0,
        "max_symbol_concentration_pct": round(conc, 1),
    }


def main() -> None:
    print("=" * 74)
    print("iter-v3/089 cost-aware cross-sectional construction EDA — IS-ONLY")
    print(f"IS cutoff: open_time < {OOS_CUTOFF_MS} (2025-03-24)")
    print(f"Model: the RETAINED cross_sectional.py LGBMRanker (lambdarank), {EDA_N_TRIALS} trials")
    print("=" * 74)

    # --- build the pooled panel (IS rows only) ----------------------------
    print("\n[panel] Building pooled cross-sectional panel (IS slice only)...")
    panel = build_cross_sectional_panel(
        features_dir=FEATURES_DIR,
        symbols=XS_UNIVERSE,
        feature_columns=list(V3_FEATURE_COLUMNS_TOP_N),
    )
    panel_is = panel[panel["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    labels = label_cross_sectional_rank(panel, horizon=XS_HORIZON)
    labels_is = labels[panel["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    print(
        f"[panel] IS panel {len(panel_is)} rows, "
        f"{panel_is['open_time'].nunique()} timestamps, {panel_is['symbol'].nunique()} symbols"
    )

    # wide return matrix (IS only) for vol estimation + PnL
    close_wide = panel_is.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="first"
    ).sort_index()
    ret_wide = close_wide.pct_change()

    # IS-internal walk-forward splits — the LAST IS month has no forward label
    # window fully inside IS, so it is naturally excluded; every test month is
    # strictly inside IS.  train_end = test_start - embargo (the e149e9d fix).
    interval_ms = 8 * 3600 * 1000
    embargo_ms = XS_REQUIRED_GAP * interval_ms
    all_ts = np.sort(panel_is["open_time"].unique())
    splits = _generate_xs_monthly_splits(
        all_timestamps=all_ts,
        training_months=EDA_TRAINING_MONTHS,
        embargo_ms=embargo_ms,
    )
    print(
        f"[walk-forward] {len(splits)} IS-internal test months "
        f"(train {EDA_TRAINING_MONTHS}m, embargo {XS_REQUIRED_GAP} rows)"
    )
    if not splits:
        print("ERROR: no IS-internal splits — IS history too short. Abort.")
        return

    # --- train the ranker ONCE per IS test month, reuse across all variants -
    print("\n[train] Training the LGBMRanker per IS test month (reused for E1-E5)...")
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
            horizon=XS_HORIZON,
            seed=42,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ic = strat._train_for_month(tp_v, tl_v)
        trained[tm] = strat
        is_rank_ics.append(ic)
        print(f"  {tm}: trained (train rows={len(tp_v)}, IS rank-IC={ic:+.4f})")
    print(
        f"[train] {len(trained)} monthly models; mean IS train rank-IC "
        f"{np.mean(is_rank_ics):+.4f}"
    )

    # ====================================================================
    # E1 — baseline replication: corrected-sign tercile, every-bar rebalance
    # ====================================================================
    print("\n[E1] Baseline — corrected-sign TERCILE, every-bar rebalance (hold=1, band=0)")
    e1 = is_internal_backtest(
        panel_is, labels_is, ret_wide, splits, trained,
        quantile_frac=1.0 / 3.0, hold_bars=1, no_trade_band=0.0,
    )
    e1["variant"] = "E1_tercile_everybar_corrected_sign"
    for k, v in e1.items():
        print(f"     {k}: {v}")

    # ====================================================================
    # E2 — quantile concentration: tercile vs quartile vs quintile
    # ====================================================================
    print("\n[E2] Quantile concentration — tercile / quartile / quintile (hold=1, band=0)")
    e2_rows = []
    for qname, qfrac in [("tercile", 1 / 3), ("quartile", 0.25), ("quintile", 0.20)]:
        r = is_internal_backtest(
            panel_is, labels_is, ret_wide, splits, trained,
            quantile_frac=qfrac, hold_bars=1, no_trade_band=0.0,
        )
        r["variant"] = f"E2_{qname}"
        r["quantile_frac"] = round(qfrac, 4)
        e2_rows.append(r)
        print(
            f"     {qname:9s}: gross Sharpe {r['is_gross_monthly_sharpe']:+.4f}  "
            f"net Sharpe {r['is_net_monthly_sharpe']:+.4f}  "
            f"turnover/bar {r['mean_turnover_per_bar']:.4f}  "
            f"fee/|gross| {r['fee_over_abs_gross']}"
        )

    # ====================================================================
    # E3 — slower rebalance / overlapping holds: hold in {1,3,6}
    # ====================================================================
    print("\n[E3] Overlapping holds — hold {1,3,6} bars (quintile, band=0)")
    e3_rows = []
    for hb in [1, 3, 6]:
        r = is_internal_backtest(
            panel_is, labels_is, ret_wide, splits, trained,
            quantile_frac=0.20, hold_bars=hb, no_trade_band=0.0,
        )
        r["variant"] = f"E3_quintile_hold{hb}"
        r["hold_bars"] = hb
        e3_rows.append(r)
        print(
            f"     hold={hb}: gross Sharpe {r['is_gross_monthly_sharpe']:+.4f}  "
            f"net Sharpe {r['is_net_monthly_sharpe']:+.4f}  "
            f"turnover/bar {r['mean_turnover_per_bar']:.4f}  "
            f"fee/|gross| {r['fee_over_abs_gross']}"
        )

    # ====================================================================
    # E4 — no-trade band scan: the turnover/cost tradeoff curve
    # ====================================================================
    print("\n[E4] No-trade band scan — quintile, hold=3, band tau in a grid")
    e4_rows = []
    for tau in [0.0, 0.0025, 0.005, 0.0075, 0.010, 0.015, 0.020]:
        r = is_internal_backtest(
            panel_is, labels_is, ret_wide, splits, trained,
            quantile_frac=0.20, hold_bars=3, no_trade_band=tau,
        )
        r["variant"] = f"E4_band_{tau}"
        r["no_trade_band"] = tau
        e4_rows.append(r)
        print(
            f"     tau={tau:.4f}: gross Sharpe {r['is_gross_monthly_sharpe']:+.4f}  "
            f"net Sharpe {r['is_net_monthly_sharpe']:+.4f}  "
            f"turnover/bar {r['mean_turnover_per_bar']:.4f}  "
            f"fee/|gross| {r['fee_over_abs_gross']}"
        )

    # ====================================================================
    # E5 — combined /089 candidate: corrected sign + quintile + hold3 + best band
    # ====================================================================
    best_e4 = max(e4_rows, key=lambda r: r["is_net_monthly_sharpe"])
    best_band = best_e4["no_trade_band"]
    print(
        f"\n[E5] Combined /089 candidate — corrected sign + quintile + hold=3 + "
        f"best-IS band tau={best_band}"
    )
    e5 = is_internal_backtest(
        panel_is, labels_is, ret_wide, splits, trained,
        quantile_frac=0.20, hold_bars=3, no_trade_band=best_band,
    )
    e5["variant"] = "E5_combined_candidate"
    e5["no_trade_band"] = best_band
    for k, v in e5.items():
        print(f"     {k}: {v}")

    # --- write CSVs --------------------------------------------------------
    pd.DataFrame([e1]).to_csv(OUT / "E1_baseline_replication.csv", index=False)
    pd.DataFrame(e2_rows).to_csv(OUT / "E2_quantile_concentration.csv", index=False)
    pd.DataFrame(e3_rows).to_csv(OUT / "E3_overlapping_holds.csv", index=False)
    pd.DataFrame(e4_rows).to_csv(OUT / "E4_no_trade_band_scan.csv", index=False)
    pd.DataFrame([e5]).to_csv(OUT / "E5_combined_candidate.csv", index=False)

    # E6 — turnover ceiling derivation -------------------------------------
    all_variants = [e1, *e2_rows, *e3_rows, *e4_rows, e5]
    vdf = pd.DataFrame(all_variants)
    best_overall = vdf.loc[vdf["is_net_monthly_sharpe"].idxmax()]
    # the turnover ceiling: the turnover/bar of the best-IS-net-Sharpe variant,
    # rounded UP slightly to a clean a-priori gate value.
    best_turn = float(best_overall["mean_turnover_per_bar"])
    ceiling = round(best_turn * 1.15, 3)  # 15% headroom above the IS optimum
    e6 = pd.DataFrame(
        [
            {
                "metric": "best_IS_net_Sharpe_variant",
                "value": best_overall["variant"],
            },
            {
                "metric": "best_IS_net_monthly_sharpe",
                "value": best_overall["is_net_monthly_sharpe"],
            },
            {"metric": "best_variant_turnover_per_bar", "value": round(best_turn, 4)},
            {
                "metric": "best_variant_turnover_frac_of_book",
                "value": best_overall["turnover_frac_of_book"],
            },
            {"metric": "E1_baseline_turnover_per_bar", "value": e1["mean_turnover_per_bar"]},
            {
                "metric": "proposed_turnover_ceiling_per_bar",
                "value": ceiling,
            },
            {
                "metric": "ceiling_rationale",
                "value": (
                    "gross-turnover-per-bar HARD gate = best-IS-variant turnover x1.15 headroom; "
                    "any /089 build whose mean gross turnover/bar EXCEEDS this is NO-MERGE"
                ),
            },
        ]
    )
    e6.to_csv(OUT / "E6_turnover_ceiling.csv", index=False)

    e2q = [r for r in e2_rows if "quintile" in r["variant"]][0]
    e2t = [r for r in e2_rows if "tercile" in r["variant"]][0]
    e3h3 = [r for r in e3_rows if r["hold_bars"] == 3][0]
    e3h1 = [r for r in e3_rows if r["hold_bars"] == 1][0]
    print("\n" + "=" * 74)
    print("EDA SUMMARY — /089 cost-aware construction, IS data only")
    print("=" * 74)
    print(
        f"  E1 baseline (corrected-sign tercile every-bar): "
        f"net Sharpe {e1['is_net_monthly_sharpe']:+.4f}, "
        f"gross Sharpe {e1['is_gross_monthly_sharpe']:+.4f}, "
        f"turnover/bar {e1['mean_turnover_per_bar']:.4f}"
    )
    print(
        f"  E2 quantile: quintile gross Sharpe {e2q['is_gross_monthly_sharpe']:+.4f} "
        f"vs tercile {e2t['is_gross_monthly_sharpe']:+.4f}"
    )
    print(
        f"  E3 hold=3 net Sharpe {e3h3['is_net_monthly_sharpe']:+.4f} "
        f"vs hold=1 {e3h1['is_net_monthly_sharpe']:+.4f}"
    )
    print(
        f"  E4 best no-trade band tau={best_band}, "
        f"net Sharpe {best_e4['is_net_monthly_sharpe']:+.4f}"
    )
    print(
        f"  E5 combined /089 candidate: net Sharpe {e5['is_net_monthly_sharpe']:+.4f}, "
        f"turnover/bar {e5['mean_turnover_per_bar']:.4f}, fee/|gross| {e5['fee_over_abs_gross']}"
    )
    print(f"  E6 PROPOSED TURNOVER CEILING (hard gate): {ceiling} gross turnover/bar")
    print("  ALL tables IS-only. Walk-forward trains+tests inside IS; no OOS row read.")
    print("  Quantile/hold/band selected on IS net Sharpe or a-priori from cited research.")
    print("=" * 74)


if __name__ == "__main__":
    sys.exit(main())

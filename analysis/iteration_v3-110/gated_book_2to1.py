"""iter-v3/110 EDA — the 2:1-barrier-faithful gated-tail book per candidate symbol.

universe_construction.py's T4 ``mean_gated_bet_pnl`` used a SYMMETRIC +/-|edge|
PnL proxy — that is NOT what the v3 backtest produces. The v3 exit is a 2:1 ATR
TP:SL triple-barrier: a clean win pays ~+2 ATR, a clean loss costs ~-1 ATR.
/109's reconciliation (R2) established that under that geometry the mechanical
breakeven win rate is 1/3 — so the right per-symbol "tradeable edge" question
is: does the gated tail's realized 2:1-barrier book clear breakeven?

This script re-resolves each candidate symbol's gated tail using the ACTUAL
triple-barrier ``long_pnl`` / ``short_pnl`` already computed in _shared (the
faithful /059 labeler), so the per-symbol book PnL is barrier-faithful, not a
symmetric proxy. It is, structurally, an IS-only gated backtest of the symbol
as a standalone v3 model — the closest pre-backtest estimate of what Phase 6
will produce per symbol.

It also runs the universe-level checks: the proposed-universe aggregate book,
a leave-one-out, and the breadth comparison vs the incumbent universe.

Outputs:
  T7_gated_book_2to1.csv      — per-symbol barrier-faithful gated-book metrics
  T8_universe_aggregate.csv   — proposed-universe aggregate + leave-one-out

NO CHEATING — every feature row has close_time < OOS_CUTOFF_MS; OOS never read.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb  # noqa: E402

from _shared import (  # noqa: E402
    CANDIDATE_SYMBOLS,
    INCUMBENTS,
    V3_FEATURE_COLUMNS,
    load_labeled_symbol,
    make_walk_forward_folds,
)

OUT = Path(__file__).resolve().parent
SEEDS = (42, 123, 456, 789, 1001)
GATE_PCTILE = 0.30
LGB_PARAMS = dict(
    objective="binary", num_leaves=15, max_depth=4, learning_rate=0.05,
    n_estimators=200, subsample=0.8, colsample_bytree=1.0,
    min_child_samples=20, reg_lambda=1.0, verbosity=-1,
)


def gated_book(sym: str) -> tuple[dict, pd.DataFrame]:
    """Barrier-faithful gated-tail book for one symbol.

    Returns (metrics dict, per-trade frame with close_time + realized barrier
    PnL). The model bets long on high proba, short on low proba; the realized
    PnL is the actual triple-barrier long_pnl / short_pnl from the /059 labeler.
    """
    df = load_labeled_symbol(sym)
    folds = make_walk_forward_folds(df, n_folds=8)
    X_all = df[V3_FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    y_all = (df["label"].to_numpy() > 0).astype(np.int64)
    long_pnl = df["long_pnl"].to_numpy(dtype=np.float64)
    short_pnl = df["short_pnl"].to_numpy(dtype=np.float64)
    ct = df["close_time"].to_numpy(dtype=np.int64)

    trades = []
    for tr_idx, te_idx in folds:
        X_tr, y_tr = X_all[tr_idx], y_all[tr_idx]
        if len(np.unique(y_tr)) < 2:
            continue
        seed_probas = []
        for sd in SEEDS:
            params = dict(LGB_PARAMS)
            params["random_state"] = sd
            m = lgb.LGBMClassifier(**params)
            m.fit(X_tr, y_tr)
            seed_probas.append(m.predict_proba(X_all[te_idx])[:, 1])
        proba = np.mean(seed_probas, axis=0)
        hi = np.quantile(proba, 1.0 - GATE_PCTILE)
        lo = np.quantile(proba, GATE_PCTILE)
        for k, gi in enumerate(te_idx):
            p = proba[k]
            if p >= hi:  # bet long — realized = the actual triple-barrier long PnL
                trades.append({"close_time": ct[gi], "pnl": long_pnl[gi], "side": 1})
            elif p <= lo:  # bet short
                trades.append({"close_time": ct[gi], "pnl": short_pnl[gi], "side": -1})
    tdf = pd.DataFrame(trades)
    if len(tdf) == 0:
        return {"symbol": sym, "n_trades": 0}, tdf

    pnl = tdf["pnl"].to_numpy()
    wins = int(np.sum(pnl > 0))
    n = len(pnl)
    gross_win = float(np.sum(pnl[pnl > 0]))
    gross_loss = float(-np.sum(pnl[pnl < 0]))
    pf = gross_win / gross_loss if gross_loss > 0 else np.nan
    # daily-equivalent Sharpe proxy: per-trade mean / std, annualized at the
    # ~3-trades/day rate is misleading; report the per-trade Sharpe and the
    # monthly aggregate. Keep it simple + comparable across symbols.
    per_trade_sharpe = float(np.mean(pnl) / np.std(pnl)) if np.std(pnl) > 1e-9 else np.nan

    return {
        "symbol": sym,
        "n_trades": n,
        "win_rate": round(wins / n, 4),
        "wr_minus_breakeven": round(wins / n - 1.0 / 3.0, 4),  # 2:1 breakeven=33.3%
        "total_pnl": round(float(np.sum(pnl)), 3),
        "mean_pnl": round(float(np.mean(pnl)), 4),
        "profit_factor": round(pf, 4) if not np.isnan(pf) else np.nan,
        "per_trade_sharpe": round(per_trade_sharpe, 4),
        "is_incumbent": sym in INCUMBENTS,
    }, tdf


def main() -> None:
    rows = []
    trade_frames: dict[str, pd.DataFrame] = {}
    n = len(CANDIDATE_SYMBOLS)
    for i, sym in enumerate(CANDIDATE_SYMBOLS, 1):
        print(f"[{i}/{n}] gated 2:1 book {sym} ...", flush=True)
        m, tdf = gated_book(sym)
        rows.append(m)
        trade_frames[sym] = tdf
        print(
            f"    n={m.get('n_trades')} WR={m.get('win_rate')} "
            f"PF={m.get('profit_factor')} totPnL={m.get('total_pnl')}",
            flush=True,
        )

    t7 = pd.DataFrame(rows).sort_values("total_pnl", ascending=False)
    t7.to_csv(OUT / "T7_gated_book_2to1.csv", index=False)

    # ---- T8 — universe aggregates ------------------------------------------
    # the composite-ranked proposed universe (from T6) + the incumbent set.
    t6 = pd.read_csv(OUT / "T6_universe_recommendation.csv")
    proposed5 = list(t6.head(5)["symbol"])
    proposed6 = list(t6.head(6)["symbol"])

    def agg_book(syms: list[str], name: str) -> dict:
        frames = [trade_frames[s] for s in syms if len(trade_frames[s]) > 0]
        if not frames:
            return {"universe": name, "n_trades": 0}
        allt = pd.concat(frames, ignore_index=True)
        pnl = allt["pnl"].to_numpy()
        wins = int(np.sum(pnl > 0))
        nn = len(pnl)
        gw = float(np.sum(pnl[pnl > 0]))
        gl = float(-np.sum(pnl[pnl < 0]))
        pf = gw / gl if gl > 0 else np.nan
        # monthly Sharpe proxy: bucket trades by close_time month, monthly PnL.
        allt["month"] = pd.to_datetime(allt["close_time"], unit="ms").dt.to_period("M")
        monthly = allt.groupby("month")["pnl"].sum()
        m_sharpe = (
            float(monthly.mean() / monthly.std() * np.sqrt(12))
            if monthly.std() > 1e-9 else np.nan
        )
        return {
            "universe": name,
            "symbols": "+".join(s.replace("USDT", "") for s in syms),
            "n_trades": nn,
            "win_rate": round(wins / nn, 4),
            "total_pnl": round(float(np.sum(pnl)), 3),
            "profit_factor": round(pf, 4) if not np.isnan(pf) else np.nan,
            "monthly_sharpe_proxy": round(m_sharpe, 4) if not np.isnan(m_sharpe) else np.nan,
            "n_months": int(monthly.shape[0]),
        }

    t8_rows = [
        agg_book(list(INCUMBENTS), "incumbent_BCH_LDO_TRX"),
        agg_book(proposed5, "proposed_top5"),
        agg_book(proposed6, "proposed_top6"),
    ]
    # leave-one-out on the proposed top-5
    for drop in proposed5:
        loo = [s for s in proposed5 if s != drop]
        t8_rows.append(agg_book(loo, f"top5_minus_{drop.replace('USDT', '')}"))
    t8 = pd.DataFrame(t8_rows)
    t8.to_csv(OUT / "T8_universe_aggregate.csv", index=False)

    print("\n=== T7 per-symbol 2:1-barrier gated book (sorted by total_pnl) ===")
    print(t7[
        ["symbol", "is_incumbent", "n_trades", "win_rate", "wr_minus_breakeven",
         "total_pnl", "profit_factor", "per_trade_sharpe"]
    ].to_string(index=False))

    print("\n=== T8 universe aggregate book (IS-only, gated, 2:1 barrier) ===")
    print(t8.to_string(index=False))


if __name__ == "__main__":
    main()

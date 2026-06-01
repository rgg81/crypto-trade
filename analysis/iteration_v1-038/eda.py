"""
iter-v1/038 EDA — Per-symbol vol-target ceiling

Mechanism under test: at trade-entry, if symbol's realized vol (rolling 30d
annualized, computed from past 8h log returns) is above its long-run upper
percentile, REDUCE position size proportionally.

This EDA is IS-ONLY (close_time < 2025-03-24 OOS_CUTOFF). It computes:
  1. Per-symbol realized-vol distribution and {5,25,50,75,85,90,95} percentiles
  2. Per-symbol IS trade roster bucketed by trade-entry realized-vol decile
  3. Asymmetry test: PnL above vs below the candidate ceiling (75th, 85th)
  4. Predicted trade-impact (count of trades whose entry RV sits above the ceiling)

OOS_CUTOFF is the project sacred constant 2025-03-24 — used ONLY to slice the
labeling baseline window. We do NOT peek at OOS PnL in this EDA.

Pure pandas + numpy. No model fit. No backtest. No I/O outside this iteration's
directory + read-only access to data/features/ and reports-v1/iteration_v1-baseline/.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Sacred constant — DO NOT change.
OOS_CUTOFF_MS = pd.Timestamp("2025-03-24", tz="UTC").value // 1_000_000

SYMBOLS = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]

# 8h candles, 3 per day, 365 days/yr (crypto 24/7) → 1095 candles/yr.
BARS_PER_YEAR = 365 * 3
ROLL_WINDOW_DAYS = 30
ROLL_WINDOW_BARS = ROLL_WINDOW_DAYS * 3  # 90 8h bars ≈ 30 days

REPO = Path("/home/roberto/crypto-trade/.worktrees/quant-research")
FEATURES_DIR = REPO / "data" / "features"
TRADES_CSV = REPO / "reports-v1" / "iteration_v1-baseline" / "in_sample" / "trades.csv"
OUT_DIR = REPO / "analysis" / "iteration_v1-038"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Percentiles to report on the long-run RV distribution.
PCTS = [5, 25, 50, 75, 85, 90, 95]


def load_rv_panel() -> pd.DataFrame:
    """Per-symbol realized-vol panel from past-only 8h log returns, IS-only."""
    frames = []
    for sym in SYMBOLS:
        f = FEATURES_DIR / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(f, columns=["open_time", "close_time", "close"])
        df = df.sort_values("close_time").reset_index(drop=True)
        df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
        # Past-only log returns: log(close_t / close_{t-1}).
        df["log_ret"] = np.log(df["close"]).diff()
        # Rolling std of past 90 bars, then annualize.
        df["rv_30d_ann"] = (
            df["log_ret"].rolling(ROLL_WINDOW_BARS, min_periods=ROLL_WINDOW_BARS).std()
            * np.sqrt(BARS_PER_YEAR)
        )
        df["symbol"] = sym
        frames.append(df[["symbol", "open_time", "close_time", "close", "log_ret", "rv_30d_ann"]])
    return pd.concat(frames, ignore_index=True)


def per_symbol_percentiles(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sym, g in panel.groupby("symbol"):
        rv = g["rv_30d_ann"].dropna()
        row = {"symbol": sym, "n_bars": int(len(rv)), "mean": rv.mean(), "std": rv.std()}
        for p in PCTS:
            row[f"p{p}"] = rv.quantile(p / 100.0)
        rows.append(row)
    return pd.DataFrame(rows).set_index("symbol")


def load_is_trades() -> pd.DataFrame:
    df = pd.read_csv(TRADES_CSV)
    # Re-confirm IS-only filter (defensive — baseline CSV already split).
    df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
    return df


def merge_trade_rv(trades: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Attach the realized-vol at trade-entry (open_time -> matching panel close_time)."""
    out = []
    for sym, g in trades.groupby("symbol"):
        p = panel[panel["symbol"] == sym][["close_time", "rv_30d_ann"]].copy()
        p = p.sort_values("close_time")
        # Trades' open_time is the END of the entry candle (Binance convention; same
        # ms as close_time in the panel for that bar). We use the bar's RV.
        merged = pd.merge_asof(
            g.sort_values("open_time"),
            p.rename(columns={"close_time": "open_time"}),
            on="open_time",
            direction="backward",
        )
        out.append(merged)
    return pd.concat(out, ignore_index=True)


def decile_table(trades_rv: pd.DataFrame) -> pd.DataFrame:
    """For each symbol, bucket trades into RV deciles based on the SYMBOL's long-run
    RV distribution and report trade count + PnL stats per decile."""
    pcts_for_buckets = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    rows = []
    panel_pcts = trades_rv.groupby("symbol")["rv_30d_ann"]
    for sym, g in trades_rv.groupby("symbol"):
        rv = g["rv_30d_ann"].dropna()
        if rv.empty:
            continue
        # NOTE: bucket edges derived from the PANEL's distribution (long-run), not
        # from the trade-RV subset. We re-pull the panel quantiles here.
        rows.append(_per_symbol_decile_rows(sym, g))
    return pd.concat(rows, ignore_index=True)


def _per_symbol_decile_rows(sym: str, trades_g: pd.DataFrame) -> pd.DataFrame:
    # Use the symbol's panel-derived percentile bin edges (passed via panel ref).
    edges = _panel_edges_cache[sym]
    g = trades_g.dropna(subset=["rv_30d_ann"]).copy()
    g["decile"] = pd.cut(
        g["rv_30d_ann"],
        bins=edges,
        labels=[f"D{i + 1}" for i in range(len(edges) - 1)],
        include_lowest=True,
    )
    out = []
    for dec, sub in g.groupby("decile", observed=True):
        out.append(
            {
                "symbol": sym,
                "decile": str(dec),
                "n_trades": len(sub),
                "wins": int((sub["net_pnl_pct"] > 0).sum()),
                "win_rate": float((sub["net_pnl_pct"] > 0).mean()),
                "mean_net_pnl_pct": sub["net_pnl_pct"].mean(),
                "sum_weighted_pnl": sub["weighted_pnl"].sum(),
                "mean_weighted_pnl": sub["weighted_pnl"].mean(),
            }
        )
    return pd.DataFrame(out)


def asymmetry_test(trades_rv: pd.DataFrame, pct_table: pd.DataFrame) -> pd.DataFrame:
    """For each symbol and each candidate ceiling (75th / 85th), measure PnL above vs below."""
    rows = []
    for sym, g in trades_rv.groupby("symbol"):
        if g["rv_30d_ann"].isna().all():
            continue
        for ceiling_p in [75, 85]:
            thr = pct_table.loc[sym, f"p{ceiling_p}"]
            above = g[g["rv_30d_ann"] > thr]
            below = g[g["rv_30d_ann"] <= thr]
            rows.append(
                {
                    "symbol": sym,
                    "ceiling_pct": ceiling_p,
                    "rv_threshold": thr,
                    "n_above": len(above),
                    "n_below": len(below),
                    "share_above": len(above) / max(len(g), 1),
                    "wr_above": float((above["net_pnl_pct"] > 0).mean()) if len(above) else np.nan,
                    "wr_below": float((below["net_pnl_pct"] > 0).mean()) if len(below) else np.nan,
                    "mean_net_pnl_above": above["net_pnl_pct"].mean() if len(above) else np.nan,
                    "mean_net_pnl_below": below["net_pnl_pct"].mean() if len(below) else np.nan,
                    "sum_weighted_pnl_above": above["weighted_pnl"].sum(),
                    "sum_weighted_pnl_below": below["weighted_pnl"].sum(),
                    "asymmetry_delta_mean": (
                        below["net_pnl_pct"].mean() - above["net_pnl_pct"].mean()
                    ),
                }
            )
    return pd.DataFrame(rows)


def trade_impact_prediction(trades_rv: pd.DataFrame, pct_table: pd.DataFrame) -> pd.DataFrame:
    """If we apply a 0.5x sizing reduction above the ceiling, predict the weighted-PnL
    re-weighting effect on the IS roster (linear approximation, no model retraining)."""
    rows = []
    for sym, g in trades_rv.groupby("symbol"):
        if g["rv_30d_ann"].isna().all():
            continue
        for ceiling_p in [75, 85]:
            thr = pct_table.loc[sym, f"p{ceiling_p}"]
            above_mask = g["rv_30d_ann"] > thr
            # Linear sizing-reduction approximation: trades above ceiling contribute 0.5x.
            current_pnl = g["weighted_pnl"].sum()
            adjusted_pnl = (
                g.loc[~above_mask, "weighted_pnl"].sum()
                + 0.5 * g.loc[above_mask, "weighted_pnl"].sum()
            )
            rows.append(
                {
                    "symbol": sym,
                    "ceiling_pct": ceiling_p,
                    "n_trades_total": len(g),
                    "n_trades_above": int(above_mask.sum()),
                    "share_capped": float(above_mask.mean()),
                    "current_weighted_pnl_sum": current_pnl,
                    "adjusted_weighted_pnl_sum_at_0p5": adjusted_pnl,
                    "delta_pnl_pct": adjusted_pnl - current_pnl,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("Loading per-symbol RV panel (IS-only)...")
    panel = load_rv_panel()
    print(f"  Panel rows: {len(panel)}")
    print(f"  Per-symbol counts: {panel.groupby('symbol').size().to_dict()}")

    pct_table = per_symbol_percentiles(panel)
    pct_table.to_csv(OUT_DIR / "rv_percentiles.csv")
    print("\nPer-symbol RV percentiles (annualized):")
    print(pct_table.round(4).to_string())

    # Stash panel edges per symbol for decile cuts (10 quantile bins).
    global _panel_edges_cache
    _panel_edges_cache = {}
    for sym, g in panel.groupby("symbol"):
        rv = g["rv_30d_ann"].dropna()
        edges = np.quantile(rv, np.linspace(0, 1, 11))
        # Guard against duplicate edges (collapse to unique sorted).
        edges[0] = -np.inf
        edges[-1] = np.inf
        _panel_edges_cache[sym] = list(edges)

    print("\nLoading IS trades...")
    trades = load_is_trades()
    print(f"  IS trades: {len(trades)}")

    trades_rv = merge_trade_rv(trades, panel)
    matched = trades_rv["rv_30d_ann"].notna().sum()
    print(f"  Trades with RV match: {matched} / {len(trades_rv)}")
    trades_rv.to_csv(OUT_DIR / "trades_with_rv.csv", index=False)

    decile_df = decile_table(trades_rv)
    decile_df.to_csv(OUT_DIR / "decile_table.csv", index=False)
    print("\nPer-symbol RV-decile trade roster:")
    print(decile_df.to_string(index=False))

    asym_df = asymmetry_test(trades_rv, pct_table)
    asym_df.to_csv(OUT_DIR / "asymmetry_test.csv", index=False)
    print("\nAsymmetry test (mean PnL above vs below ceiling):")
    print(asym_df.round(4).to_string(index=False))

    impact_df = trade_impact_prediction(trades_rv, pct_table)
    impact_df.to_csv(OUT_DIR / "trade_impact_prediction.csv", index=False)
    print("\nLinear sizing-impact prediction (0.5x above ceiling, no retraining):")
    print(impact_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

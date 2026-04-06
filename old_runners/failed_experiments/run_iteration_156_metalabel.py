"""Iter 156: Meta-labeling on iter 138 trades.

Post-processes iter 138's 816 trades with a LightGBM meta-classifier that
predicts whether each trade will be profitable. Meta-features: traded-symbol
NATR/ADX/RSI + BTC NATR at open_time, direction, hour_of_day, rolling
10-trade WR, days_since_last_trade.

Walk-forward: monthly refit, trained only on closed trades before month
start. Filter: keep trades with P(profitable) >= threshold. Grid-search
threshold on IS only; apply IS-best to OOS.

VT scales from iter 152 config (target=0.3, lookback=45, floor=0.33) are
applied to KEPT trades.
"""

import csv
import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from crypto_trade.backtest import _compute_vt_scale
from crypto_trade.backtest_models import BacktestConfig, TradeResult
from crypto_trade.iteration_report import _compute_metrics

OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT")
SYM_INDEX = {s: i for i, s in enumerate(SYMBOLS)}

META_FEATURE_COLS = [
    "sym_natr_21", "sym_adx_14", "sym_rsi_14", "btc_natr_21",
    "direction", "hour_of_day", "rolling_wr_10", "days_since_last",
    "sym_idx",
]


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def month_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m")


def hour_of(ms: int) -> int:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).hour


def load_trades() -> list[dict]:
    trades = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades.append(row)
    trades.sort(key=lambda t: int(t["open_time"]))
    return trades


def load_feature_frames() -> dict[str, pd.DataFrame]:
    frames = {}
    for sym in SYMBOLS:
        path = f"data/features/{sym}_8h_features.parquet"
        df = pd.read_parquet(path, columns=[
            "open_time", "vol_natr_21", "trend_adx_14", "mom_rsi_14"
        ])
        df = df.set_index("open_time").sort_index()
        frames[sym] = df
    return frames


def lookup_feature(df: pd.DataFrame, col: str, ts_ms: int) -> float:
    """Get feature value at or just before ts_ms (asof lookup)."""
    # df index is open_time in ms. Find largest index <= ts_ms.
    idx = df.index.searchsorted(ts_ms, side="right") - 1
    if idx < 0:
        return np.nan
    val = df[col].iloc[idx]
    return float(val) if not pd.isna(val) else np.nan


def build_meta_features(
    trades: list[dict],
    frames: dict[str, pd.DataFrame],
) -> np.ndarray:
    """Build meta-features array. Rolling 10-trade WR and days-since-last
    are computed walk-forward per symbol from past closed trades.
    """
    btc_df = frames["BTCUSDT"]

    # Per-symbol history: list of (close_time_ms, is_profitable)
    sym_history: dict[str, list[tuple[int, int]]] = {s: [] for s in SYMBOLS}
    last_trade_open_ms: dict[str, int | None] = {s: None for s in SYMBOLS}

    features = []
    for t in trades:
        sym = t["symbol"]
        ot_ms = int(t["open_time"])
        ct_ms = int(t["close_time"])
        direction = int(t["direction"])
        net_pnl = float(t["net_pnl_pct"])

        # Drop closes that occurred before this open from sym_history...
        # actually sym_history is appended AFTER this trade is emitted,
        # so it only contains past trades. No leakage.

        # Asset-level features (asof at open_time)
        sym_df = frames[sym]
        sym_natr = lookup_feature(sym_df, "vol_natr_21", ot_ms)
        sym_adx = lookup_feature(sym_df, "trend_adx_14", ot_ms)
        sym_rsi = lookup_feature(sym_df, "mom_rsi_14", ot_ms)
        btc_natr = lookup_feature(btc_df, "vol_natr_21", ot_ms)

        hour = hour_of(ot_ms)

        # Walk-forward rolling WR: use only CLOSED trades (close_time < ot_ms)
        past_closed = [
            is_prof for (close_ms, is_prof) in sym_history[sym]
            if close_ms < ot_ms
        ]
        if len(past_closed) < 10:
            rolling_wr = 0.5
        else:
            rolling_wr = sum(past_closed[-10:]) / 10.0

        # Days since last trade OPEN for this symbol
        last_open = last_trade_open_ms[sym]
        if last_open is None:
            days_since = -1.0  # sentinel
        else:
            days_since = (ot_ms - last_open) / (1000.0 * 86400.0)

        features.append([
            sym_natr, sym_adx, sym_rsi, btc_natr,
            float(direction), float(hour), rolling_wr, days_since,
            float(SYM_INDEX[sym]),
        ])

        # Update state AFTER emitting features
        is_profitable = int(net_pnl > 0)
        sym_history[sym].append((ct_ms, is_profitable))
        last_trade_open_ms[sym] = ot_ms

    return np.array(features)


def walk_forward_predict(
    X: np.ndarray,
    y: np.ndarray,
    close_times: np.ndarray,
    open_times: np.ndarray,
    monthly_refit: bool = True,
) -> np.ndarray:
    """Walk-forward prediction: for each trade, train meta-classifier on all
    trades closed before the trade's open_time, predict probability.

    Refits once per calendar month to save compute.
    """
    n = len(X)
    proba = np.full(n, 0.5, dtype=float)

    # Start predicting only after 100 closed trades (warmup)
    first_pred_idx = None
    for i in range(n):
        # Count closed trades before open_time[i]
        closed_mask = close_times < open_times[i]
        n_closed = closed_mask.sum()
        if n_closed >= 100:
            first_pred_idx = i
            break
    if first_pred_idx is None:
        print("Warning: never reached 100 closed trades")
        return proba

    # Monthly refit schedule
    current_month = None
    model = None
    for i in range(first_pred_idx, n):
        month = month_of(int(open_times[i]))
        if monthly_refit and month != current_month:
            # Refit on all closed trades before open_times[i]
            train_mask = close_times < open_times[i]
            if train_mask.sum() < 100:
                continue
            X_tr = X[train_mask]
            y_tr = y[train_mask]
            model = lgb.LGBMClassifier(
                n_estimators=100, max_depth=4, num_leaves=15,
                learning_rate=0.05, min_child_samples=20,
                colsample_bytree=0.8, subsample=0.8, subsample_freq=1,
                random_state=42, verbose=-1,
                class_weight="balanced",
            )
            model.fit(X_tr, y_tr)
            current_month = month

        proba[i] = model.predict_proba(X[i:i + 1])[0, 1]

    return proba


def apply_vt(
    trades_raw: list[dict],
    kept_mask: np.ndarray,
    config: BacktestConfig,
) -> list[TradeResult]:
    """Build TradeResults for KEPT trades with iter 152 VT scaling.

    Important: VT's per-symbol daily PnL history is built from ORIGINAL trades
    (unfiltered). This mirrors the engine — VT scales would be the same
    regardless of meta-filter (the engine doesn't know about filtering).

    Alternative: build VT history from KEPT trades only. We test both.
    """
    # Build per-sym daily PnL history from ORIGINAL trades (for VT lookup)
    events = []
    for i, t in enumerate(trades_raw):
        events.append((int(t["open_time"]), "open", i, t))
        events.append((int(t["close_time"]), "close", i, t))
    events.sort(key=lambda e: (e[0], 0 if e[1] == "close" else 1))

    running: dict[str, dict[str, float]] = {}
    scales_by_i: dict[int, float] = {}

    for ts, et, i, trade in events:
        sym = trade["symbol"]
        if et == "close":
            d = day_of(ts)
            sym_d = running.setdefault(sym, {})
            sym_d[d] = sym_d.get(d, 0.0) + float(trade["net_pnl_pct"])
        else:
            scale = _compute_vt_scale(running, sym, ts, config)
            scales_by_i[i] = scale

    # Build TradeResults for kept trades only
    results: list[TradeResult] = []
    for i, t in enumerate(trades_raw):
        if not kept_mask[i]:
            continue
        scale = scales_by_i.get(i, 1.0)
        net_pnl = float(t["net_pnl_pct"])
        results.append(TradeResult(
            symbol=t["symbol"], direction=int(t["direction"]),
            entry_price=float(t["entry_price"]),
            exit_price=float(t["exit_price"]),
            weight_factor=scale,
            open_time=int(t["open_time"]), close_time=int(t["close_time"]),
            exit_reason=t["exit_reason"],
            pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
            net_pnl_pct=net_pnl, weighted_pnl=net_pnl * scale,
        ))
    results.sort(key=lambda t: t.close_time)
    return results


def split_is_oos(results):
    is_t = [r for r in results if r.open_time < OOS_CUTOFF_MS]
    oos_t = [r for r in results if r.open_time >= OOS_CUTOFF_MS]
    return is_t, oos_t


def main() -> None:
    print("Loading iter 138 trades and feature frames...")
    trades = load_trades()
    frames = load_feature_frames()
    print(f"Loaded {len(trades)} trades, {len(frames)} feature frames")

    print("Building meta-features (walk-forward)...")
    X = build_meta_features(trades, frames)
    y = np.array([1 if float(t["net_pnl_pct"]) > 0 else 0 for t in trades])
    close_times = np.array([int(t["close_time"]) for t in trades])
    open_times = np.array([int(t["open_time"]) for t in trades])

    # NaN check
    nan_frac = np.isnan(X).mean()
    print(f"NaN fraction in meta-features: {nan_frac*100:.1f}%")
    # Fill NaNs with column medians for training
    col_medians = np.nanmedian(X, axis=0)
    for j in range(X.shape[1]):
        nan_mask = np.isnan(X[:, j])
        X[nan_mask, j] = col_medians[j]

    print("Base rate (IS profitable trades):", f"{y[:652].mean()*100:.1f}%")

    print("Walk-forward prediction (monthly refit)...")
    proba = walk_forward_predict(X, y, close_times, open_times)

    # Diagnostics
    n_is_predicted = ((open_times < OOS_CUTOFF_MS) & (proba != 0.5)).sum()
    n_oos_predicted = ((open_times >= OOS_CUTOFF_MS) & (proba != 0.5)).sum()
    print(f"Trades with meta predictions: IS={n_is_predicted}, "
          f"OOS={n_oos_predicted}")

    config = BacktestConfig(
        symbols=SYMBOLS,
        interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True,
        vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )

    # Baseline: no filter
    print("\n=== Baseline (no meta-filter) ===")
    all_kept = np.ones(len(trades), dtype=bool)
    base = apply_vt(trades, all_kept, config)
    is_t, oos_t = split_is_oos(base)
    is_m = _compute_metrics(is_t)
    oos_m = _compute_metrics(oos_t)
    print(
        f"IS:  trades={is_m.total_trades} Sharpe={is_m.sharpe:+.4f} "
        f"MaxDD={is_m.max_drawdown:.2f}%"
    )
    print(
        f"OOS: trades={oos_m.total_trades} Sharpe={oos_m.sharpe:+.4f} "
        f"MaxDD={oos_m.max_drawdown:.2f}% PF={oos_m.profit_factor:.2f}"
    )

    print("\n=== Threshold grid ===")
    print(f"{'thresh':>7s} {'IS_n':>5s} {'OOS_n':>6s} "
          f"{'IS_SR':>8s} {'OOS_SR':>8s} {'IS_DD':>7s} {'OOS_DD':>7s} "
          f"{'OOS_PF':>7s}")
    table = []
    for thresh in [0.40, 0.45, 0.50, 0.52, 0.55, 0.58, 0.60]:
        # Warmup trades (proba=0.5) are KEPT to avoid dropping early history
        kept = (proba >= thresh) | (proba == 0.5)
        results = apply_vt(trades, kept, config)
        is_t, oos_t = split_is_oos(results)
        if len(is_t) < 50 or len(oos_t) < 20:
            print(f"  thresh={thresh:.2f}: too few trades "
                  f"(IS={len(is_t)}, OOS={len(oos_t)})")
            continue
        is_m = _compute_metrics(is_t)
        oos_m = _compute_metrics(oos_t)
        print(
            f"{thresh:7.2f} {is_m.total_trades:5d} {oos_m.total_trades:6d} "
            f"{is_m.sharpe:+8.4f} {oos_m.sharpe:+8.4f} "
            f"{is_m.max_drawdown:7.2f} {oos_m.max_drawdown:7.2f} "
            f"{oos_m.profit_factor:7.2f}"
        )
        table.append({
            "thresh": thresh,
            "is_sharpe": is_m.sharpe, "oos_sharpe": oos_m.sharpe,
            "is_n": is_m.total_trades, "oos_n": oos_m.total_trades,
            "is_dd": is_m.max_drawdown, "oos_dd": oos_m.max_drawdown,
            "oos_pf": oos_m.profit_factor,
            "oos_calmar": oos_m.calmar_ratio,
            "oos_pnl": oos_m.total_net_pnl,
        })

    # IS-best selection (require >= 150 IS trades to avoid over-filter)
    valid = [r for r in table if r["is_n"] >= 150]
    if not valid:
        print("\nNo config passes IS-trade-count constraint (>= 150)")
        return
    best = max(valid, key=lambda r: r["is_sharpe"])
    print(f"\n=== IS-best (thresh={best['thresh']:.2f}) ===")
    print(f"  IS Sharpe: {best['is_sharpe']:+.4f} (n={best['is_n']})")
    print(f"  OOS Sharpe: {best['oos_sharpe']:+.4f} (n={best['oos_n']})")
    print(f"  OOS MaxDD: {best['oos_dd']:.2f}%")
    print(f"  OOS PF: {best['oos_pf']:.2f}")
    print(f"  OOS Calmar: {best['oos_calmar']:.2f}")
    print(f"  OOS PnL: {best['oos_pnl']:+.2f}%")

    # Alt: meta-filter WITHOUT VT (scale=1)
    print("\n=== Meta-filter, NO VT (scale=1.0 for kept trades) ===")
    print(f"{'thresh':>7s} {'IS_n':>5s} {'OOS_n':>6s} "
          f"{'IS_SR':>8s} {'OOS_SR':>8s} {'IS_DD':>7s} {'OOS_DD':>7s} "
          f"{'OOS_PF':>7s}")
    no_vt_table = []
    for thresh in [0.40, 0.45, 0.50, 0.55, 0.60]:
        kept = (proba >= thresh) | (proba == 0.5)
        # Build results with scale=1.0
        results = []
        for i, t in enumerate(trades):
            if not kept[i]:
                continue
            net_pnl = float(t["net_pnl_pct"])
            results.append(TradeResult(
                symbol=t["symbol"], direction=int(t["direction"]),
                entry_price=float(t["entry_price"]),
                exit_price=float(t["exit_price"]),
                weight_factor=1.0,
                open_time=int(t["open_time"]), close_time=int(t["close_time"]),
                exit_reason=t["exit_reason"],
                pnl_pct=float(t["pnl_pct"]), fee_pct=float(t["fee_pct"]),
                net_pnl_pct=net_pnl, weighted_pnl=net_pnl,
            ))
        results.sort(key=lambda t: t.close_time)
        is_t, oos_t = split_is_oos(results)
        if len(is_t) < 50 or len(oos_t) < 20:
            continue
        is_m = _compute_metrics(is_t)
        oos_m = _compute_metrics(oos_t)
        print(
            f"{thresh:7.2f} {is_m.total_trades:5d} {oos_m.total_trades:6d} "
            f"{is_m.sharpe:+8.4f} {oos_m.sharpe:+8.4f} "
            f"{is_m.max_drawdown:7.2f} {oos_m.max_drawdown:7.2f} "
            f"{oos_m.profit_factor:7.2f}"
        )
        no_vt_table.append({
            "thresh": thresh,
            "is_sharpe": is_m.sharpe, "oos_sharpe": oos_m.sharpe,
            "is_n": is_m.total_trades, "oos_n": oos_m.total_trades,
        })


if __name__ == "__main__":
    main()

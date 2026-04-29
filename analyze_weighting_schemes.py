"""Test multiple portfolio weighting schemes for v1+v2 combined.

Compares:
1. Equal-coin: 1/8 per symbol (current)
2. Sharpe-weighted: weight by per-symbol OOS trade-Sharpe
3. Risk-parity: weight inversely by per-symbol OOS std(wpnl)
4. Drop-worst: equal-coin but exclude OOS losers (if any)
5. Track-weighted 50/50: 50% v1, 50% v2 (within each, equal-coin)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS


def _load(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p)
    df["open_time"] = pd.to_numeric(df["open_time"])
    df["close_time"] = pd.to_numeric(df["close_time"])
    return df


def _sharpe(w: np.ndarray) -> float:
    if len(w) < 2 or w.std() == 0:
        return 0.0
    return float(w.mean() / w.std() * np.sqrt(len(w)))


def _monthly_sharpe(df: pd.DataFrame) -> float:
    if len(df) < 2:
        return 0.0
    m = pd.to_datetime(df["close_time"], unit="ms").dt.to_period("M")
    mo = df.assign(_m=m).groupby("_m")["weighted_pnl"].sum() / 100.0
    if len(mo) < 2 or mo.std() == 0:
        return 0.0
    return float(mo.mean() / mo.std() * np.sqrt(12))


def _pf(w: np.ndarray) -> float:
    pos = w[w > 0].sum()
    neg = -w[w < 0].sum()
    return float(pos / neg) if neg > 0 else float("inf")


def _eval(df: pd.DataFrame, label: str) -> None:
    is_t = df[df["open_time"] < OOS_CUTOFF_MS]
    oos_t = df[df["open_time"] >= OOS_CUTOFF_MS]
    is_w = is_t["weighted_pnl"].to_numpy()
    oos_w = oos_t["weighted_pnl"].to_numpy()
    print(f"\n{label}")
    print("-" * 55)
    print(
        f"  IS:  trade={_sharpe(is_w):+.3f}  monthly={_monthly_sharpe(is_t):+.3f}  "
        f"trades={len(is_t)}  wpnl={is_w.sum():+.2f}  "
        f"WR={100 * (is_w > 0).mean():.1f}%  PF={_pf(is_w):.3f}"
    )
    print(
        f"  OOS: trade={_sharpe(oos_w):+.3f}  monthly={_monthly_sharpe(oos_t):+.3f}  "
        f"trades={len(oos_t)}  wpnl={oos_w.sum():+.2f}  "
        f"WR={100 * (oos_w > 0).mean():.1f}%  PF={_pf(oos_w):.3f}"
    )


def _compute_per_symbol_stats(trades: pd.DataFrame, window: str) -> dict[str, dict]:
    """Compute per-symbol trade-Sharpe, std, etc. for a given window ('is'/'oos'/'all')."""
    if window == "is":
        df = trades[trades["open_time"] < OOS_CUTOFF_MS]
    elif window == "oos":
        df = trades[trades["open_time"] >= OOS_CUTOFF_MS]
    else:
        df = trades
    stats = {}
    for sym in trades["symbol"].unique():
        sym_w = df[df["symbol"] == sym]["weighted_pnl"].to_numpy()
        if len(sym_w) < 2:
            continue
        stats[sym] = {
            "trade_sharpe": _sharpe(sym_w),
            "std": float(sym_w.std()),
            "mean": float(sym_w.mean()),
            "n": len(sym_w),
        }
    return stats


def main() -> None:
    # Load fresh trades from both baselines
    v1 = pd.concat(
        [
            _load(Path("reports/iteration_152/in_sample/trades.csv")),
            _load(Path("reports/iteration_152/out_of_sample/trades.csv")),
        ],
        ignore_index=True,
    )
    v2 = pd.concat(
        [
            _load(Path("reports-v2/iteration_v2-063-fresh/in_sample/trades.csv")),
            _load(Path("reports-v2/iteration_v2-063-fresh/out_of_sample/trades.csv")),
        ],
        ignore_index=True,
    )
    all_trades = pd.concat([v1, v2], ignore_index=True)

    # IS-based stats (NO lookahead) — used for all weighting schemes below
    is_stats = _compute_per_symbol_stats(all_trades, "is")
    # OOS-based stats (displayed for context, NOT used for weights)
    oos_stats = _compute_per_symbol_stats(all_trades, "oos")

    print("=" * 70)
    print("PORTFOLIO WEIGHTING SCHEMES COMPARISON")
    print("=" * 70)
    print("All weights determined from IS ONLY — no lookahead bias.")

    symbols = sorted(is_stats.keys())

    # 1. Equal-coin
    weights_equal = {s: 1.0 / len(symbols) for s in symbols}

    # 2. IS-Sharpe-weighted (clip negative sharpe to 0)
    sharpes = np.array([max(0.0, is_stats[s]["trade_sharpe"]) for s in symbols])
    sharpe_total = sharpes.sum() if sharpes.sum() > 0 else 1.0
    weights_sharpe = {s: float(sh / sharpe_total) for s, sh in zip(symbols, sharpes)}

    # 3. Risk-parity (inverse IS std)
    stds = np.array([is_stats[s]["std"] for s in symbols])
    inv = 1.0 / stds
    inv_total = inv.sum()
    weights_rp = {s: float(i / inv_total) for s, i in zip(symbols, inv)}

    # 4. Drop-worst: drop symbols with IS trade-Sharpe < 0.8 (stricter)
    thresh = 0.8
    keep = [s for s in symbols if is_stats[s]["trade_sharpe"] >= thresh]
    weights_drop_worst = {s: 1.0 / max(len(keep), 1) for s in keep}

    # 5. Track 50/50: 50% v1 (4 coins → 1/8 each) + 50% v2 (4 coins → 1/8 each)
    v1_syms = {"BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"}
    v2_syms = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}
    weights_5050 = {}
    for s in symbols:
        if s in v1_syms:
            weights_5050[s] = 0.5 / len(v1_syms)
        elif s in v2_syms:
            weights_5050[s] = 0.5 / len(v2_syms)

    print("\nPer-symbol IS stats (used for weighting) + OOS stats (eval only):")
    print(
        f"  {'symbol':<10}  "
        f"{'IS-trades':>9}  {'IS-sharpe':>9}  {'IS-std':>7}  "
        f"{'OOS-trades':>10}  {'OOS-sharpe':>10}"
    )
    for s in symbols:
        ist = is_stats[s]
        ost = oos_stats.get(s, {})
        print(
            f"  {s:<10}  {ist['n']:>9d}  {ist['trade_sharpe']:>+9.3f}  {ist['std']:>7.3f}  "
            f"{ost.get('n', 0):>10d}  {ost.get('trade_sharpe', 0):>+10.3f}"
        )

    print("\nWeights per scheme:")
    print(
        f"  {'symbol':<10}  {'equal':>7}  {'sharpe':>7}  "
        f"{'risk-par':>8}  {'dropW':>7}  {'50/50':>7}"
    )
    for s in symbols:
        print(
            f"  {s:<10}  {weights_equal.get(s, 0):>7.3f}  "
            f"{weights_sharpe.get(s, 0):>7.3f}  "
            f"{weights_rp.get(s, 0):>8.3f}  "
            f"{weights_drop_worst.get(s, 0):>7.3f}  "
            f"{weights_5050.get(s, 0):>7.3f}"
        )

    for name, weights in [
        ("EQUAL-COIN (1/8 each)", weights_equal),
        ("IS-SHARPE-WEIGHTED (per-symbol IS Sharpe)", weights_sharpe),
        ("RISK-PARITY (1/IS-std)", weights_rp),
        (f"DROP-WORST (IS Sharpe < {thresh})", weights_drop_worst),
        ("TRACK 50/50 (50% v1 + 50% v2)", weights_5050),
    ]:
        scaled = all_trades.copy()
        scaled["weighted_pnl"] = scaled.apply(
            lambda r: r["weighted_pnl"] * weights.get(r["symbol"], 0.0), axis=1
        )
        _eval(scaled, name)


if __name__ == "__main__":
    main()

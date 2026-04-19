"""Combine v1 (Models A/C/D) and v2 (Models E/F/G/H) into an equal-coin-weight portfolio.

User's approach: give the same weight to each coin. v1 Model A is pooled on BTC+ETH
(2 coins), so Model A gets 2x weight relative to single-coin models.

Coin counts:
- Model A (v1): BTCUSDT + ETHUSDT = 2 coins
- Model C (v1): LINKUSDT = 1 coin
- Model D (v1): BNBUSDT = 1 coin
- Model E (v2): DOGEUSDT = 1 coin
- Model F (v2): SOLUSDT = 1 coin
- Model G (v2): XRPUSDT = 1 coin
- Model H (v2): NEARUSDT = 1 coin
Total: 8 coins

Per-coin weight: 1/8 = 0.125
Per-model weights:
- Model A: 0.25 (2 coins / 8)
- Models C, D, E, F, G, H: 0.125 each (1 coin / 8)

The `weighted_pnl` column in each trade is already the model's PnL contribution
assuming 100% allocation to that model. To combine at equal-coin weighting, we
scale each trade's weighted_pnl by its model's portfolio weight.

Both v1 and v2 use max_amount_usd=1000 and fee_pct=0.1, so their weighted_pnl
values are directly comparable (both are percentage returns on $1000 notional
per trade).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS

# Model weights per user directive: equal weight per coin
V1_SYMBOLS_A = {"BTCUSDT", "ETHUSDT"}  # Model A (pooled)
V1_SYMBOLS_C = {"LINKUSDT"}
V1_SYMBOLS_D = {"BNBUSDT"}
V2_SYMBOLS = {"DOGEUSDT", "SOLUSDT", "XRPUSDT", "NEARUSDT"}

ALL_COINS = V1_SYMBOLS_A | V1_SYMBOLS_C | V1_SYMBOLS_D | V2_SYMBOLS
PER_COIN_WEIGHT = 1.0 / len(ALL_COINS)  # 1/8 = 0.125


def _per_symbol_weight(symbol: str) -> float:
    """Equal-coin weight. Each coin gets 1/8 of portfolio."""
    if symbol in ALL_COINS:
        return PER_COIN_WEIGHT
    raise ValueError(f"Unexpected symbol: {symbol}")


def _load_trades(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["open_time"] = pd.to_numeric(df["open_time"])
    df["close_time"] = pd.to_numeric(df["close_time"])
    return df


def _sharpe_trade(wpnl: np.ndarray) -> float:
    if len(wpnl) < 2:
        return 0.0
    sd = float(wpnl.std())
    if sd == 0:
        return 0.0
    return float(wpnl.mean() / sd * np.sqrt(len(wpnl)))


def _sharpe_monthly(trades: pd.DataFrame) -> float:
    if len(trades) < 2:
        return 0.0
    months = pd.to_datetime(trades["close_time"], unit="ms").dt.to_period("M")
    monthly = trades.assign(_m=months).groupby("_m")["weighted_pnl"].sum() / 100.0
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _summarize(trades: pd.DataFrame, label: str) -> dict:
    """Compute portfolio metrics on a trade list with pre-scaled weighted_pnl."""
    is_trades = trades[trades["open_time"] < OOS_CUTOFF_MS]
    oos_trades = trades[trades["open_time"] >= OOS_CUTOFF_MS]

    is_wpnl = is_trades["weighted_pnl"].to_numpy(dtype=float)
    oos_wpnl = oos_trades["weighted_pnl"].to_numpy(dtype=float)

    is_total = float(is_wpnl.sum())
    oos_total = float(oos_wpnl.sum())

    # Win rate
    is_wr = float((is_wpnl > 0).mean()) if len(is_wpnl) > 0 else 0.0
    oos_wr = float((oos_wpnl > 0).mean()) if len(oos_wpnl) > 0 else 0.0

    # Profit factor
    def _pf(arr: np.ndarray) -> float:
        pos = arr[arr > 0].sum()
        neg = -arr[arr < 0].sum()
        return float(pos / neg) if neg > 0 else float("inf")

    return {
        "label": label,
        "is_trades": len(is_trades),
        "oos_trades": len(oos_trades),
        "is_total_wpnl": round(is_total, 2),
        "oos_total_wpnl": round(oos_total, 2),
        "is_sharpe_trade": round(_sharpe_trade(is_wpnl), 4),
        "oos_sharpe_trade": round(_sharpe_trade(oos_wpnl), 4),
        "is_sharpe_monthly": round(_sharpe_monthly(is_trades), 4),
        "oos_sharpe_monthly": round(_sharpe_monthly(oos_trades), 4),
        "is_wr": round(is_wr, 4),
        "oos_wr": round(oos_wr, 4),
        "is_pf": round(_pf(is_wpnl), 4) if not np.isinf(_pf(is_wpnl)) else 999.0,
        "oos_pf": round(_pf(oos_wpnl), 4) if not np.isinf(_pf(oos_wpnl)) else 999.0,
    }


def _per_symbol_breakdown(trades: pd.DataFrame, oos_only: bool = True) -> pd.DataFrame:
    """Per-symbol OOS trade count, WR, and total weighted_pnl share."""
    if oos_only:
        trades = trades[trades["open_time"] >= OOS_CUTOFF_MS]
    grp = trades.groupby("symbol").agg(
        trades=("weighted_pnl", "size"),
        wins=("weighted_pnl", lambda s: int((s > 0).sum())),
        wpnl=("weighted_pnl", "sum"),
    )
    grp["wr"] = (grp["wins"] / grp["trades"]).round(4)
    total_positive = float(grp.loc[grp["wpnl"] > 0, "wpnl"].sum())
    grp["share_pct"] = (
        grp["wpnl"].clip(lower=0) / max(total_positive, 1e-9) * 100
    ).round(2)
    return grp.sort_values("wpnl", ascending=False)


def main() -> None:
    # v1 trades from reports/iteration_152/
    v1_is = _load_trades(Path("reports/iteration_152/in_sample/trades.csv"))
    v1_oos = _load_trades(Path("reports/iteration_152/out_of_sample/trades.csv"))
    v1_trades = pd.concat([v1_is, v1_oos], ignore_index=True)

    # v2 trades from reports-v2/iteration_v2-059/
    v2_is = _load_trades(Path("reports-v2/iteration_v2-059/in_sample/trades.csv"))
    v2_oos = _load_trades(Path("reports-v2/iteration_v2-059/out_of_sample/trades.csv"))
    v2_trades = pd.concat([v2_is, v2_oos], ignore_index=True)

    # Scale each trade's weighted_pnl by its coin's portfolio weight (equal per coin)
    v1_trades = v1_trades.copy()
    v2_trades = v2_trades.copy()
    v1_trades["weighted_pnl"] = v1_trades["weighted_pnl"] * v1_trades["symbol"].apply(
        _per_symbol_weight
    )
    v2_trades["weighted_pnl"] = v2_trades["weighted_pnl"] * v2_trades["symbol"].apply(
        _per_symbol_weight
    )

    combined = pd.concat([v1_trades, v2_trades], ignore_index=True)
    combined = combined.sort_values("close_time").reset_index(drop=True)

    # Raw (unscaled) v1 and v2 summaries for reference (we re-load unscaled)
    v1_raw = pd.concat(
        [
            _load_trades(Path("reports/iteration_152/in_sample/trades.csv")),
            _load_trades(Path("reports/iteration_152/out_of_sample/trades.csv")),
        ]
    )
    v2_raw = pd.concat(
        [
            _load_trades(Path("reports-v2/iteration_v2-059/in_sample/trades.csv")),
            _load_trades(Path("reports-v2/iteration_v2-059/out_of_sample/trades.csv")),
        ]
    )

    print("=" * 70)
    print("COMBINED v1 + v2 PORTFOLIO — EQUAL-COIN WEIGHTING")
    print("=" * 70)
    print("8 coins total, 1/8 weight each. Model A (BTC+ETH) gets 0.25 (2 coins).")
    print()

    for df, label in [
        (v1_raw, "v1 raw (100% capital)"),
        (v2_raw, "v2 raw (100% capital)"),
        (combined, "COMBINED (equal-coin)"),
    ]:
        s = _summarize(df, label)
        print(f"\n{s['label']}")
        print("-" * 50)
        print(
            f"  IS:  trade-Sharpe={s['is_sharpe_trade']:+.4f}  "
            f"monthly-Sharpe={s['is_sharpe_monthly']:+.4f}"
        )
        print(
            f"       trades={s['is_trades']}  wpnl={s['is_total_wpnl']:+.2f}  "
            f"WR={s['is_wr'] * 100:.1f}%  PF={s['is_pf']:.3f}"
        )
        print(
            f"  OOS: trade-Sharpe={s['oos_sharpe_trade']:+.4f}  "
            f"monthly-Sharpe={s['oos_sharpe_monthly']:+.4f}"
        )
        print(
            f"       trades={s['oos_trades']}  wpnl={s['oos_total_wpnl']:+.2f}  "
            f"WR={s['oos_wr'] * 100:.1f}%  PF={s['oos_pf']:.3f}"
        )

    print("\n" + "=" * 70)
    print("Combined OOS per-symbol breakdown (after scaling)")
    print("=" * 70)
    print(_per_symbol_breakdown(combined, oos_only=True))

    print("\n" + "=" * 70)
    print("Combined vs individual — OOS monthly Sharpe comparison")
    print("=" * 70)
    v1_oos_sr = _sharpe_monthly(v1_raw[v1_raw["open_time"] >= OOS_CUTOFF_MS])
    v2_oos_sr = _sharpe_monthly(v2_raw[v2_raw["open_time"] >= OOS_CUTOFF_MS])
    combined_oos_sr = _sharpe_monthly(combined[combined["open_time"] >= OOS_CUTOFF_MS])
    print(f"v1 alone OOS monthly Sharpe: {v1_oos_sr:+.4f}")
    print(f"v2 alone OOS monthly Sharpe: {v2_oos_sr:+.4f}")
    print(f"Combined OOS monthly Sharpe: {combined_oos_sr:+.4f}")
    if max(v1_oos_sr, v2_oos_sr) > 0:
        diversification_benefit = combined_oos_sr / max(v1_oos_sr, v2_oos_sr) - 1.0
        print(f"Combined vs best-alone: {diversification_benefit:+.1%}")


if __name__ == "__main__":
    main()

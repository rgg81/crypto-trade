"""Post-hoc drawdown-brake feasibility study (iter-v2/012).

Loads iter-v2/005 OOS trades and simulates a portfolio-level drawdown
brake that halves trade weight when running drawdown exceeds a shrink
threshold and zeroes it when running drawdown exceeds a flatten
threshold.

The brake operates on the combined 4-symbol v2 stream (Models E/F/G/H
= DOGE/SOL/XRP/NEAR). Trades are processed in open_time order. At
each trade, the current running DD is computed from the cumulative
weighted PnL and its running peak. The effective weight is applied
to that trade only — the brake does not close already-open positions.

Usage:
    uv run python analyze_drawdown_brake.py

Configurations tested:
    A — 5% / 10%   (iter-v2/001 draft)
    B — 6% / 12%   (recommended)
    C — 8% / 16%   (looser)
    D — 4% / 8%    (aggressive)
    None           (baseline)

Outputs:
    reports-v2/iteration_v2-012_dd_brake/
      summary.json          per-config headline metrics
      per_config_trades.csv  trade-by-trade brake state
      firing_log.txt        detailed brake firing events
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

V2_REPORT = Path("reports-v2/iteration_v2-005")
OUT_DIR = Path("reports-v2/iteration_v2-012_dd_brake")


@dataclass(frozen=True)
class BrakeConfig:
    name: str
    shrink_pct: float  # running DD threshold above which weight → 0.5x
    flatten_pct: float  # running DD threshold above which weight → 0
    shrink_factor: float = 0.5


CONFIGS: tuple[BrakeConfig, ...] = (
    BrakeConfig("none", shrink_pct=float("inf"), flatten_pct=float("inf")),
    BrakeConfig("A_5_10", shrink_pct=5.0, flatten_pct=10.0),
    BrakeConfig("B_6_12", shrink_pct=6.0, flatten_pct=12.0),
    BrakeConfig("C_8_16", shrink_pct=8.0, flatten_pct=16.0),
    BrakeConfig("D_4_8", shrink_pct=4.0, flatten_pct=8.0),
)


def _apply_brake(trades: pd.DataFrame, cfg: BrakeConfig) -> tuple[pd.DataFrame, list[dict]]:
    """Apply a drawdown brake to a trade stream.

    The brake state is decided from the UNDERLYING strategy's compound
    equity drawdown (not the braked stream), so flattening is
    self-releasing — once the underlying strategy recovers above the
    shrink threshold, new trades flow at full weight again. In
    production this corresponds to tracking a "shadow" portfolio of
    what-the-strategy-would-earn and releasing the brake when that
    shadow recovers.

    Trades are processed in open_time order. Compound equity uses
    ``equity *= (1 + weighted_pnl/100)`` per trade (chained multiply
    on the unbraked stream).
    """
    trades = trades.sort_values("open_time").reset_index(drop=True).copy()

    effective_weight: list[float] = []
    effective_pnl: list[float] = []
    baseline_dd_log: list[float] = []
    brake_state: list[str] = []
    firings: list[dict] = []

    # UNBRAKED (shadow) compound equity — drives brake state
    baseline_equity = 1.0
    baseline_peak = 1.0

    for _, trade in trades.iterrows():
        # Compute baseline DD from peak BEFORE this trade is added
        baseline_dd_pct = (baseline_equity - baseline_peak) / baseline_peak * 100.0

        if -baseline_dd_pct >= cfg.flatten_pct:
            eff_factor = 0.0
            state = "flatten"
        elif -baseline_dd_pct >= cfg.shrink_pct:
            eff_factor = cfg.shrink_factor
            state = "shrink"
        else:
            eff_factor = 1.0
            state = "normal"

        wpnl = float(trade["weighted_pnl"])
        eff_weighted = wpnl * eff_factor

        # Update baseline (unbraked) equity from the REAL trade pnl
        baseline_equity *= 1.0 + wpnl / 100.0
        baseline_peak = max(baseline_peak, baseline_equity)

        effective_weight.append(eff_factor)
        effective_pnl.append(eff_weighted)
        baseline_dd_log.append(baseline_dd_pct)
        brake_state.append(state)

        if state != "normal":
            firings.append(
                {
                    "config": cfg.name,
                    "open_time": int(trade["open_time"]),
                    "symbol": trade["symbol"],
                    "baseline_dd_pct_at_entry": round(float(baseline_dd_pct), 3),
                    "state": state,
                    "original_weighted_pnl": round(wpnl, 3),
                    "effective_weighted_pnl": round(eff_weighted, 3),
                }
            )

    trades["effective_factor"] = effective_weight
    trades["effective_weighted_pnl"] = effective_pnl
    trades["baseline_dd_before_entry"] = baseline_dd_log
    trades["brake_state"] = brake_state
    return trades, firings


def _annualize(daily_pnl: pd.Series, periods: int = 365) -> float:
    if len(daily_pnl) < 2 or daily_pnl.std() == 0:
        return 0.0
    return float(daily_pnl.mean() / daily_pnl.std() * np.sqrt(periods))


def _max_drawdown(equity_curve: pd.Series) -> float:
    if len(equity_curve) == 0:
        return 0.0
    rolling_max = equity_curve.cummax()
    dd = (equity_curve - rolling_max) / rolling_max.replace(0, np.nan)
    return float(dd.min() or 0.0)


def _summarize(trades: pd.DataFrame, pnl_col: str, label: str) -> dict:
    if len(trades) == 0:
        return {"label": label, "n": 0}

    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.date
    daily = trades.groupby("date")[pnl_col].sum()

    # Daily-annualized Sharpe
    sharpe_daily = _annualize(daily / 100.0)
    # Trade-level Sharpe
    pnl = trades[pnl_col]
    sharpe_trades = (
        pnl.mean() / pnl.std() * np.sqrt(len(pnl)) if pnl.std() > 0 else 0.0
    )
    # Equity curve for MaxDD
    equity = (1.0 + daily / 100.0).cumprod()
    max_dd = _max_drawdown(equity)
    # Profit factor on effective PnL
    wins = trades.loc[pnl > 0, pnl_col].sum()
    losses = abs(trades.loc[pnl < 0, pnl_col].sum() or 1)
    pf = float(wins / losses)
    total_pnl = float(pnl.sum())
    # Active trades (brake didn't flatten)
    active = int((trades["effective_factor"] > 0).sum()) if "effective_factor" in trades else len(trades)
    # Calmar = total_return / max_dd
    total_return = float((1.0 + daily / 100.0).prod() - 1.0)
    calmar = float(total_return / abs(max_dd)) if max_dd != 0 else 0.0

    return {
        "label": label,
        "n_signals": int(len(trades)),
        "n_active_trades": active,
        "win_rate": round(float((pnl > 0).mean() * 100), 2),
        "pf": round(pf, 4),
        "sharpe_trades": round(float(sharpe_trades), 4),
        "sharpe_daily_annualized": round(float(sharpe_daily), 4),
        "max_dd_pct": round(float(max_dd * 100), 2),
        "total_pnl_pct": round(total_pnl, 2),
        "calmar": round(calmar, 2),
        "active_days": int(daily.count()),
    }


def main() -> None:
    print("=" * 70)
    print("DRAWDOWN BRAKE FEASIBILITY STUDY — iter-v2/012")
    print("=" * 70)

    oos_path = V2_REPORT / "out_of_sample/trades.csv"
    if not oos_path.exists():
        print(f"ERROR: {oos_path} not found")
        return

    trades = pd.read_csv(oos_path)
    print(f"\nLoaded {len(trades)} OOS trades from {oos_path}")
    print(f"Symbols: {sorted(trades['symbol'].unique().tolist())}")
    print(f"Total baseline weighted PnL: {trades['weighted_pnl'].sum():.2f}%")
    print()

    summaries: dict[str, dict] = {}
    all_firings: list[dict] = []
    per_config_frames: dict[str, pd.DataFrame] = {}

    for cfg in CONFIGS:
        braked, firings = _apply_brake(trades, cfg)
        summary = _summarize(braked, "effective_weighted_pnl", cfg.name)
        summary["config"] = {
            "shrink_pct": cfg.shrink_pct if np.isfinite(cfg.shrink_pct) else None,
            "flatten_pct": cfg.flatten_pct if np.isfinite(cfg.flatten_pct) else None,
            "shrink_factor": cfg.shrink_factor,
        }
        summary["n_shrink_firings"] = int(
            (braked["brake_state"] == "shrink").sum()
        )
        summary["n_flatten_firings"] = int(
            (braked["brake_state"] == "flatten").sum()
        )
        summary["n_normal"] = int((braked["brake_state"] == "normal").sum())
        summaries[cfg.name] = summary
        all_firings.extend(firings)
        per_config_frames[cfg.name] = braked

    # Print headline table
    print("=" * 70)
    print("HEADLINE METRICS (daily-annualized Sharpe, max DD, Calmar)")
    print("=" * 70)
    header = (
        f"{'config':<10} {'shrink':>7} {'flatten':>7} "
        f"{'Sharpe':>8} {'MaxDD%':>8} {'Calmar':>7} {'PnL%':>8} "
        f"{'shrinks':>8} {'flatns':>7} {'normal':>7}"
    )
    print(header)
    print("-" * len(header))
    for name, s in summaries.items():
        cfg = s["config"]
        sh = f"{cfg['shrink_pct']}" if cfg["shrink_pct"] else "—"
        fl = f"{cfg['flatten_pct']}" if cfg["flatten_pct"] else "—"
        print(
            f"{name:<10} {sh:>7} {fl:>7} "
            f"{s['sharpe_daily_annualized']:>+8.4f} "
            f"{s['max_dd_pct']:>+8.2f} "
            f"{s['calmar']:>+7.2f} "
            f"{s['total_pnl_pct']:>+8.2f} "
            f"{s['n_shrink_firings']:>8} "
            f"{s['n_flatten_firings']:>7} "
            f"{s['n_normal']:>7}"
        )

    # Print decision check
    print()
    print("=" * 70)
    print("DECISION CRITERIA: MaxDD < 45% AND Sharpe > +1.3 (daily annualized)")
    print("=" * 70)
    for name, s in summaries.items():
        if name == "none":
            continue
        mdd_ok = abs(s["max_dd_pct"]) < 45.0
        sr_ok = s["sharpe_daily_annualized"] > 1.3
        overall = "PASS" if (mdd_ok and sr_ok) else "FAIL"
        print(
            f"  {name}: MaxDD={s['max_dd_pct']:+.2f}% ({'ok' if mdd_ok else 'BAD'}) "
            f"| Sharpe={s['sharpe_daily_annualized']:+.4f} ({'ok' if sr_ok else 'BAD'}) "
            f"→ {overall}"
        )

    # Print baseline for reference
    print()
    baseline = summaries["none"]
    print(
        f"Baseline (no brake): Sharpe={baseline['sharpe_daily_annualized']:+.4f}, "
        f"MaxDD={baseline['max_dd_pct']:+.2f}%, "
        f"Calmar={baseline['calmar']:+.2f}, "
        f"PnL={baseline['total_pnl_pct']:+.2f}%"
    )

    # Persist artifacts
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summaries, indent=2, default=str))

    # Combined per-config trades
    all_frames = []
    for name, df in per_config_frames.items():
        df = df.copy()
        df["brake_config"] = name
        all_frames.append(df)
    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(OUT_DIR / "per_config_trades.csv", index=False)

    # Firing log — sorted by config then time
    firing_df = pd.DataFrame(all_firings)
    if len(firing_df):
        firing_df["open_date"] = pd.to_datetime(firing_df["open_time"], unit="ms").dt.date
        firing_df = firing_df.sort_values(["config", "open_time"])
        firing_df.to_csv(OUT_DIR / "firing_log.csv", index=False)
        print()
        print("=" * 70)
        print("BRAKE FIRING EVENTS (first 30 across all configs)")
        print("=" * 70)
        print(firing_df.head(30).to_string(index=False))

    print(f"\nArtifacts written to {OUT_DIR}")


if __name__ == "__main__":
    main()

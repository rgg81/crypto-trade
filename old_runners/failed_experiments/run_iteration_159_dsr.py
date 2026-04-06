"""Iter 159: Deflated Sharpe Ratio audit for v0.152 baseline.

Computes DSR accounting for multiple testing across the iteration
history. Per AFML Ch. 14:

  E[max(SR_0)] ~ sqrt(2 ln N) × (1 - γ/(2 ln N)) + γ/sqrt(2 ln N)

where γ = 0.5772 (Euler-Mascheroni) and N is the number of independent
trials. DSR uses the observed OOS Sharpe's skew/kurtosis:

  SE(SR) ~ sqrt((1 - γ_3*SR + (γ_4-1)/4*SR²) / (T-1))

where γ_3 = skewness, γ_4 = kurtosis, T = trade count (or obs count).

DSR = (SR - E[max(SR_0)]) / SE(SR).
DSR > 0 means observed SR beats the expected max under random null.
"""

import csv
import datetime
import math
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.backtest import _compute_vt_scale
from crypto_trade.backtest_models import BacktestConfig, TradeResult
from crypto_trade.iteration_report import to_daily_returns_series

OOS_CUTOFF_MS = int(
    datetime.datetime(2025, 3, 24, tzinfo=datetime.UTC).timestamp() * 1000
)

GAMMA = 0.5772156649015328  # Euler-Mascheroni


def day_of(ms: int) -> str:
    return datetime.datetime.fromtimestamp(
        ms / 1000, tz=datetime.UTC
    ).strftime("%Y-%m-%d")


def expected_max_sharpe(N: int) -> float:
    """E[max(SR_0)] under the null hypothesis of N independent random
    Sharpe ratios with zero mean, unit variance.
    """
    if N <= 1:
        return 0.0
    lnN = math.log(N)
    return math.sqrt(2 * lnN) * (1 - GAMMA / (2 * lnN)) + GAMMA / math.sqrt(2 * lnN)


def deflated_sharpe_ratio(
    observed_sr: float,
    N_trials: int,
    returns: np.ndarray,
) -> tuple[float, float, float]:
    """Compute DSR.

    Returns (DSR, E[max(SR_0)], SE(SR)).
    """
    emax = expected_max_sharpe(N_trials)
    T = len(returns)
    if T < 3:
        return (0.0, emax, 0.0)
    # Compute skew and excess kurtosis
    mean = returns.mean()
    std = returns.std(ddof=1)
    if std <= 0:
        return (0.0, emax, 0.0)
    z = (returns - mean) / std
    skew = float((z ** 3).mean())
    kurt = float((z ** 4).mean())  # raw kurtosis (Pearson's)
    # Standard error of annualized Sharpe
    # SE_SR^2 ≈ (1 - skew*SR + (kurt-1)/4*SR^2) / (T - 1)
    se_sq = (1 - skew * observed_sr + (kurt - 1) / 4 * observed_sr ** 2) / (T - 1)
    if se_sq <= 0:
        return (0.0, emax, 0.0)
    se = math.sqrt(se_sq)
    dsr = (observed_sr - emax) / se
    return (dsr, emax, se)


def load_iter138_apply_vt() -> list[TradeResult]:
    """Load iter 138 trades and apply iter 152 VT config."""
    trades_raw = []
    for sub in ("in_sample", "out_of_sample"):
        with open(f"reports/iteration_138/{sub}/trades.csv") as f:
            for row in csv.DictReader(f):
                trades_raw.append(row)
    trades_raw.sort(key=lambda t: int(t["open_time"]))

    config = BacktestConfig(
        symbols=("BTCUSDT", "ETHUSDT", "LINKUSDT", "BNBUSDT"),
        interval="8h", max_amount_usd=1000.0,
        stop_loss_pct=4.0, take_profit_pct=8.0, timeout_minutes=10080,
        data_dir=Path("data"),
        vol_targeting=True,
        vt_target_vol=0.3, vt_lookback_days=45,
        vt_min_scale=0.33, vt_max_scale=2.0,
    )

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
            scales_by_i[i] = _compute_vt_scale(running, sym, ts, config)

    results = []
    for i, t in enumerate(trades_raw):
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


def main() -> None:
    results = load_iter138_apply_vt()

    is_t = [r for r in results if r.open_time < OOS_CUTOFF_MS]
    oos_t = [r for r in results if r.open_time >= OOS_CUTOFF_MS]

    # IS daily returns
    is_returns = to_daily_returns_series(is_t).to_numpy()
    oos_returns = to_daily_returns_series(oos_t).to_numpy()

    print("=== v0.152 Baseline DSR Audit ===\n")

    # IS Sharpe
    is_mean = is_returns.mean()
    is_std = is_returns.std(ddof=1)
    is_sharpe = is_mean / is_std * math.sqrt(365)
    print(f"IS:  days={len(is_returns)}, mean={is_mean:.4f}%, "
          f"std={is_std:.4f}%, Sharpe={is_sharpe:+.4f}")

    oos_mean = oos_returns.mean()
    oos_std = oos_returns.std(ddof=1)
    oos_sharpe = oos_mean / oos_std * math.sqrt(365)
    print(f"OOS: days={len(oos_returns)}, mean={oos_mean:.4f}%, "
          f"std={oos_std:.4f}%, Sharpe={oos_sharpe:+.4f}")

    # Compute skew/kurt on daily returns (not annualized)
    for label, rets, sr in [("IS", is_returns, is_sharpe),
                              ("OOS", oos_returns, oos_sharpe)]:
        z = (rets - rets.mean()) / rets.std(ddof=1)
        skew = float((z ** 3).mean())
        kurt = float((z ** 4).mean())
        print(f"\n{label} distribution: skew={skew:.3f}, kurt={kurt:.3f}")

    # Scenario 1: N = 20 post-processing iterations (from v0.152 forward)
    # Iterations 153, 155, 156, 157, 158 = 5 iterations post-152.
    # Each tested multiple configs.
    print("\n=== DSR Scenarios ===")

    # Scenario: iter 158's actual 21-config grid (isolated to that iter)
    print("\nScenario 1: Single iteration (iter 158) — 21 configs")
    dsr, emax, se = deflated_sharpe_ratio(oos_sharpe, 21, oos_returns)
    print(f"  N=21: E[max] = {emax:.3f}, SE(SR) = {se:.3f}, DSR = {dsr:+.3f}")

    print("\nScenario 2: Full iteration history — conservative")
    # Iterations 152 onward: 152 (9 configs), 153 (5 configs), 155 (9+5 configs),
    # 156 (7 thresholds × 2 VT modes = 14), 157 (8 rules), 158 (21 configs)
    # Total: 9+5+14+14+8+21 = 71 configs/thresholds tried on similar OOS
    total_configs = 9 + 5 + 14 + 14 + 8 + 21
    dsr, emax, se = deflated_sharpe_ratio(oos_sharpe, total_configs, oos_returns)
    print(f"  N={total_configs}: E[max] = {emax:.3f}, SE(SR) = {se:.3f}, "
          f"DSR = {dsr:+.3f}")

    print("\nScenario 3: Full iteration history — full iteration count (159)")
    dsr, emax, se = deflated_sharpe_ratio(oos_sharpe, 159, oos_returns)
    print(f"  N=159: E[max] = {emax:.3f}, SE(SR) = {se:.3f}, DSR = {dsr:+.3f}")

    print("\n=== Minimum Sharpe Improvement Required ===")
    print("To meaningfully exceed E[max(SR_0)], next iteration must show:")
    for N in [10, 20, 50, 100, 200]:
        emax = expected_max_sharpe(N)
        # Rough SE from OOS
        se = math.sqrt((1 - 0 * oos_sharpe + 2/4 * oos_sharpe**2) / (len(oos_returns) - 1))
        # For DSR = 1 (90% confidence), need SR > emax + se
        min_sr = emax + se
        print(f"  N={N:3d}: E[max]={emax:.3f}, "
              f"min Sharpe for DSR>1: {min_sr:.3f} "
              f"(Δ vs baseline {min_sr - oos_sharpe:+.3f})")

    # Delta-DSR: for iter 158's (25, 33) config
    # OOS Sharpe improved from 2.8286 to 2.8517
    print("\n=== iter 158 (25, 33) ΔDSR ===")
    print(f"  Baseline OOS Sharpe: 2.8286")
    print(f"  iter 158 OOS Sharpe: 2.8517")
    print(f"  Δ Sharpe: +0.0231")
    se_base = math.sqrt((1 - 0 * 2.8286 + 2/4 * 2.8286**2) / 319)
    print(f"  SE(SR) (approx): {se_base:.3f}")
    print(f"  Δ in SE units: {0.0231 / se_base:.3f}")
    print("  (Change is well within 1 SE → not statistically distinguishable)")


if __name__ == "__main__":
    main()

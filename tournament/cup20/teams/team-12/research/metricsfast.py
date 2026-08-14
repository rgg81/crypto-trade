"""Scored-metric vector from fastsim output, mirroring crypto_trade.cup20.scored_metrics."""
from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd

from crypto_trade.cup20.bootstrap import circular_block_bootstrap_positive_fraction
from crypto_trade.cup20.metrics import is_folds
from crypto_trade.cup20.scoring import robustness_score
from crypto_trade.cup20.config import IS_END

from fastsim import daily, max_dd, sharpe, DAYS_PER_YEAR

UNDEFINED_CALMAR = 1_000.0
UNDEFINED_COST_SHARE = 1.0


def window(res: dict, times: pd.DatetimeIndex) -> dict:
    d = daily(res["net_return"], times)
    days = max(len(d), 1)
    years = days / DAYS_PER_YEAR
    growth = float(np.prod(1.0 + d.to_numpy()))
    ann = growth ** (1.0 / years) - 1.0 if growth > 0 else -1.0
    dd = max_dd(d)
    calmar = (UNDEFINED_CALMAR if ann > 0 else 0.0) if dd <= 0 else ann / dd
    naive = pd.DatetimeIndex(d.index).tz_convert("UTC").tz_localize(None)
    q = (1.0 + d).groupby(naive.to_period("Q")).prod() - 1.0
    posq = int((q > 0).sum())
    gross_bar = res["price_pnl"] + res["funding_pnl"]
    tot_turn = float(res["turnover"].sum())
    gt = float(gross_bar.sum())
    pg = float(np.clip(gross_bar, 0, None).sum())
    costs = float(res["fees"].sum() + res["slippage"].sum())
    ad = d.abs()
    return {
        "daily": d,
        "net_sharpe": sharpe(d),
        "annualized_return": ann,
        "annualized_volatility": float(np.std(d.to_numpy(), ddof=1)) * math.sqrt(DAYS_PER_YEAR)
        if len(d) > 1 else 0.0,
        "max_drawdown": dd,
        "calmar": calmar,
        "positive_quarter_fraction": posq / len(q) if len(q) else 0.0,
        "positive_quarter_count": posq,
        "annualized_turnover": tot_turn / years if years > 0 else 0.0,
        "gross_edge_bps_per_turnover": gt / tot_turn * 1e4 if tot_turn > 0 else 0.0,
        "cost_share_of_positive_gross": costs / pg if pg > 0 else UNDEFINED_COST_SHARE,
        "top5_day_share": float(ad.nlargest(5).sum()) / float(ad.sum()) if float(ad.sum()) > 0 else 0.0,
        "long_gross_pnl": float(res["long_price_pnl"].sum() + res["long_funding_pnl"].sum()),
        "short_gross_pnl": float(res["short_price_pnl"].sum() + res["short_funding_pnl"].sum()),
        "trade_count": int(res["trade_count"]),
    }


def scored_vector(run: dict, panel, *, trial_count: int = 2) -> dict:
    times = panel.times
    w1 = window(run["results"][1], times)
    w2 = window(run["results"][2], times)
    w3 = window(run["results"][3], times)
    folds = is_folds(panel.is_start, IS_END)
    d2 = w2["daily"]
    fs = [sharpe(d2[(d2.index >= a) & (d2.index < b)]) for _, a, b in folds]
    d1 = w1["daily"]
    pos1 = d1.clip(lower=0.0)
    tot = float(pos1.sum())
    shares = [float(pos1[(pos1.index >= a) & (pos1.index < b)].sum()) / tot if tot > 0 else 0.0
              for _, a, b in folds]
    try:
        B = circular_block_bootstrap_positive_fraction(d1, samples=2000, block_days=10, seed=20260804)
    except Exception:
        B = float("nan")
    conf = max(0.0, min(1.0, 1.0 - trial_count * (1.0 - B))) if math.isfinite(B) else float("nan")
    scored = {
        "net_sharpe": w1["net_sharpe"],
        "double_cost_sharpe": w2["net_sharpe"],
        "triple_cost_sharpe": w3["net_sharpe"],
        "annualized_return": w1["annualized_return"],
        "double_cost_annualized_return": w2["annualized_return"],
        "max_drawdown": w1["max_drawdown"],
        "annualized_volatility": w1["annualized_volatility"],
        "positive_quarter_fraction": w1["positive_quarter_fraction"],
        "positive_fold_count": float(sum(1 for v in fs if v > 0)),
        "worst_fold_sharpe": float(min(fs)),
        "median_fold_sharpe": float(statistics.median(fs)),
        "calmar": w2["calmar"],
        "annualized_turnover": w1["annualized_turnover"],
        "gross_edge_bps_per_turnover": w1["gross_edge_bps_per_turnover"],
        "cost_share_of_positive_gross": w1["cost_share_of_positive_gross"],
        "top5_day_share": w1["top5_day_share"],
        "max_fold_positive_pnl_share": float(max(shares)),
        "trade_count": float(w1["trade_count"]),
        "long_gross_pnl": w1["long_gross_pnl"],
        "short_gross_pnl": w1["short_gross_pnl"],
        "double_cost_max_drawdown": w2["max_drawdown"],
        "double_cost_positive_quarter_fraction": w2["positive_quarter_fraction"],
        "double_cost_annualized_turnover": w2["annualized_turnover"],
        "fold_sharpes_2x": fs,
        "B": B,
        "trial_adjusted_confidence": conf,
    }
    rank = {
        "worst_fold_sharpe": scored["worst_fold_sharpe"],
        "median_fold_sharpe": scored["median_fold_sharpe"],
        "calmar": scored["calmar"],
        "max_drawdown": scored["double_cost_max_drawdown"],
        "positive_quarter_fraction": scored["double_cost_positive_quarter_fraction"],
        "trial_adjusted_confidence": conf if math.isfinite(conf) else 0.0,
    }
    scored["G"] = robustness_score(rank, drawdown_floor=0.20)
    return scored


def show(scored: dict, label: str = "") -> str:
    return (
        f"{label:28s} G={scored['G']:6.2f} Sh1={scored['net_sharpe']:5.2f} "
        f"Sh2={scored['double_cost_sharpe']:5.2f} Sh3={scored['triple_cost_sharpe']:5.2f} "
        f"DD1={scored['max_drawdown']:.3f} DD2={scored['double_cost_max_drawdown']:.3f} "
        f"vol={scored['annualized_volatility']:.3f} "
        f"folds={['%.2f' % v for v in scored['fold_sharpes_2x']]} "
        f"worst={scored['worst_fold_sharpe']:5.2f} med={scored['median_fold_sharpe']:5.2f} "
        f"cal={scored['calmar']:6.2f} q2={scored['double_cost_positive_quarter_fraction']:.2f} "
        f"trn={scored['annualized_turnover']:5.1f} edge={scored['gross_edge_bps_per_turnover']:6.1f} "
        f"cost%={scored['cost_share_of_positive_gross']:.2f} n={int(scored['trade_count'])} "
        f"L={scored['long_gross_pnl']:+.2f} S={scored['short_gross_pnl']:+.2f} B={scored['B']:.4f}"
    )

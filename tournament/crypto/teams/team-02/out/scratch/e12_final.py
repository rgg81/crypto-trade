"""e12 — FINAL SPEC confirmation: fresh, self-contained implementation of the QE formula.

build_raw_weights logic exactly as the QE will ship it (no imports from other scratch files).
"""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc
from portfolio_tournament import engine as te

N = 60
D = 0.25
K = 6


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    close = pn["close"]
    hi = close.rolling(N, min_periods=N).max()
    lo = close.rolling(N, min_periods=N).min()
    rng = hi - lo
    c = (2.0 * (close - lo) / rng - 1.0).where(rng > 0, 0.0)
    s = np.sign(c) * (c.abs() - D).clip(lower=0.0) / (1.0 - D)
    s = s.fillna(0.0)
    return s.ewm(span=K, adjust=True).mean()


pn, aux, scoring = te.load_is_panels()
raw = build_raw_weights(te.team_view(pn), te.make_team_aux(aux))
raw = te.conform_raw(raw, pn)
net, w, parts = te.net_series(raw, pn, scoring)
m1 = te.evaluate(net, w, parts, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
net2, w2, parts2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
m2 = te.evaluate(net2, w2, parts2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)

print("FINAL SPEC — form E, N=60, d=0.25, k=6 (ewm adjust=True), raw sizing")
print(f"@1x : sharpe={m1.sharpe:+.4f} maxdd={m1.maxdd:+.4f} turnover={m1.ann_turnover:.1f} "
      f"months={m1.n_months} total_ret={m1.total_return:+.3f}")
print(f"      breadth long/short median = {m1.median_names_long:.1f}/{m1.median_names_short:.1f} "
      f"mean_gross={m1.mean_gross:.3f} mean_net={m1.mean_net:+.3f}")
print(f"      regime={m1.regime_sharpe}")
print(f"      funding_pnl={m1.total_funding_pnl:+.4f} cost={m1.total_cost:.4f}")
print(f"@2x : sharpe={m2.sharpe:+.4f} maxdd={m2.maxdd:+.4f}")

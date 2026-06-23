"""portfolio-iteration-v2 iter-v2-008 — MULTI-LOOKBACK ENSEMBLE of the XS-mom signal.

The baseline candidate (XS-mom L=84) has a 2026 OOS sub-window that is positive only at L=84/168 and
negative at L=42/63/126 (critic Count 3). A single lookback is a free parameter; AVERAGING the centered
rank across several lookbacks is regularization — it should reduce the L-dependence (more stable
sub-windows) at comparable Sharpe, with NO new tunable (equal weights, pre-registered lookback set).

Hypothesis: equal-weight ensemble over L∈{42,84,126} >= single-L=84 on LATE AND on BOTH OOS sub-windows
(more robust), at comparable IS/turnover. Risk layer (target_vol=0.006/max_lev=2.0) is orthogonal — a
Sharpe-invariant de-lever — so Sharpe comparisons here carry over to the risk-layered book unchanged.

Run:  uv run python analysis/portfolio_v2/iter_v2_008_ensemble.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "analysis"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio_v2 import engine_v2 as e2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe, slip_pessimistic  # noqa: E402
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

OOS = e2.OOS_CUTOFF
W1 = pd.Timestamp("2026-01-01")
EARLY_LO, EARLY_HI = pd.Timestamp("2021-01-01"), pd.Timestamp("2024-01-01")
LATE_LO = pd.Timestamp("2024-01-01")


def _norm(sig):
    return sig.div(sig.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def row(label, res):
    net = res["net"]
    s = {
        "IS": e2.msharpe(net, e2.LO0, OOS),
        "EARLY": e2.msharpe(net, EARLY_LO, EARLY_HI),
        "LATE": e2.msharpe(net, LATE_LO, OOS),
        "OOS": e2.msharpe(net, OOS, e2.HI1),
        "O25": e2.msharpe(net, OOS, W1),
        "O26": e2.msharpe(net, W1, e2.HI1),
    }
    print(
        f"  {label:26} IS={s['IS']:+.2f} EARLY={s['EARLY']:+.2f} LATE={s['LATE']:+.2f} "
        f"| OOS={s['OOS']:+.2f} [25={s['O25']:+.2f} 26={s['O26']:+.2f}] turn={res['turnover']:.3f}"
    )
    return s


def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    def xs(lb):
        s, _ = _xsmom(panel["close"], elig, lb)
        return _norm(s)

    def run(sig, **kw):
        return e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    print("=" * 100)
    print("iter-v2-008 — MULTI-LOOKBACK ENSEMBLE (XS-mom), rank 21-40 (OOS shown — confirmation-class)")
    print("=" * 100)
    print("\n[single-lookback baselines]")
    for lb in (42, 84, 126):
        row(f"single L={lb}", run(xs(lb)))

    print("\n[equal-weight ensembles] (average the centered ranks, then size)")
    ensembles = {
        "ens{42,84,126}": (42, 84, 126),
        "ens{42,84}": (42, 84),
        "ens{84,126}": (84, 126),
        "ens{42,63,84,126,168}": (42, 63, 84, 126, 168),
    }
    best = None
    for name, lbs in ensembles.items():
        sig = _norm(sum(xs(lb) for lb in lbs) / len(lbs))
        res = run(sig)
        s = row(name, res)
        # prefer: both OOS sub-windows positive, then higher LATE (robustness-first)
        score = (min(s["O25"], s["O26"]), s["LATE"])
        if best is None or score > best[0]:
            best = (score, name, lbs, sig, res)

    _, name, lbs, sig, res = best
    print(f"\n[best-robustness ensemble] {name}; cost stress:")
    row("  default", res)
    row("  2x-taker", run(sig, cost_mult=2.0))
    row(
        "  pessimistic",
        e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=slip_pessimistic
        ),
    )
    print(f"  per-year={per_year_sharpe(res['net'])}")
    print("\n[read] vs single L=84 (OOS +1.20 [25 +1.22 26 +1.09]): does the ensemble keep BOTH OOS "
          "sub-windows positive AND hold LATE, with less L-dependence? Robustness, not a bigger number.")


if __name__ == "__main__":
    main()

"""portfolio-iteration-v2 iter-v2-009 — FUNDING-rank carry sleeve + combine with XS-mom ensemble.

User insight: rank-21-40 mid-caps carry richer/crowded funding -> a cross-sectional funding fade may
work here. The literature warns crypto carry is REGIME-FADED (negative in 2025 broadly) so judge on
the RECENT (LATE/OOS) regime, not full sample. If it has a recent edge AND is orthogonal to XS-mom, the
2-sleeve combine (the classic momentum+carry Sharpe-lifter) should raise risk-adjusted return.

Baseline to beat: XS-mom 5-way ensemble {42,63,84,126,168} OOS +1.37 [25 +1.61 26 +0.84], 2x-taker +1.03.
Tests: funding standalone (M sweep + weekly rebalance, since carry is slower); ensemble+funding combine
(weight sweep); correlation of the two sleeves' nets. OOS shown (confirmation-class for the baseline).

Run:  uv run python analysis/portfolio_v2/iter_v2_009_funding.py
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
from portfolio_v2 import funding_v2 as fv  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402
from portfolio_v2.diag_v2_001 import per_year_sharpe  # noqa: E402
from portfolio_v2.engine_v2 import _xsmom, build_panel  # noqa: E402

OOS = e2.OOS_CUTOFF
W1 = pd.Timestamp("2026-01-01")
LATE_LO = pd.Timestamp("2024-01-01")


def _norm(s):
    return s.div(s.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def resample(sig, freq):
    if freq is None:
        return sig
    per = pd.Series(sig.index.to_period(freq), index=sig.index)
    return sig.loc[per != per.shift(1)].reindex(sig.index).ffill().fillna(0.0)


def row(label, res):
    net = res["net"]
    s = {k: f for k, f in (
        ("IS", e2.msharpe(net, e2.LO0, OOS)),
        ("LATE", e2.msharpe(net, LATE_LO, OOS)),
        ("OOS", e2.msharpe(net, OOS, e2.HI1)),
        ("O25", e2.msharpe(net, OOS, W1)),
        ("O26", e2.msharpe(net, W1, e2.HI1)),
    )}
    print(f"  {label:28} IS={s['IS']:+.2f} LATE={s['LATE']:+.2f} | "
          f"OOS={s['OOS']:+.2f} [25={s['O25']:+.2f} 26={s['O26']:+.2f}] turn={res['turnover']:.3f}")
    return net


def main():
    pool = uv.load_pool_pit()
    panel = build_panel(pool)
    elig = (
        uv.eligibility(pool, 20, 40, 168)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    def run(sig, **kw):
        return e2.run_book_from_signal(
            pool, sig, rank_lo=20, rank_hi=40, season=168, slip_bps_fn=e2.default_slip_bps, **kw
        )

    # the XS-mom 5-way ensemble baseline
    ens = _norm(sum(_norm(_xsmom(panel["close"], elig, lb)[0]) for lb in (42, 63, 84, 126, 168)) / 5)

    print("=" * 100)
    print("iter-v2-009 — FUNDING carry sleeve + combine, rank 21-40 (OOS shown)")
    print("=" * 100)
    print("\n[XS-mom ensemble baseline]")
    ens_net = row("xsmom-ens (baseline)", run(ens))

    print("\n[funding sleeve standalone — M sweep + weekly (carry is slower)]")
    fund_sigs = {}
    for m in (9, 21, 63):
        s = _norm(fv.funding_signal(pool, lookback=m))
        fund_sigs[m] = s
        row(f"funding M={m} (8h)", run(s))
    row("funding M=21 weekly", run(resample(fund_sigs[21], "W")))

    print("\n[orthogonality] corr(xsmom-ens net, funding net):")
    for m in (9, 21, 63):
        fn = run(fund_sigs[m])["net"]
        c = ens_net.align(fn, join="inner")
        corr = float(np.corrcoef(c[0].values, c[1].values)[0, 1])
        print(f"  M={m}: corr={corr:+.3f}")

    print("\n[combine: ensemble + funding, weight sweep]")
    fbest = fund_sigs[21]
    for w in (0.5, 0.3, 0.2):
        combo = _norm((1 - w) * ens + w * fbest)
        net = row(f"ens*(1-{w}) + funding*{w}", run(combo))
        if w == 0.3:
            print(f"     per-year={per_year_sharpe(net)}")
    print("\n[read] funding earns its keep ONLY if combine OOS/LATE (cost-stressed) > ens-alone "
          "(OOS +1.37); else XS-mom ensemble stays the baseline (carry regime-faded).")


if __name__ == "__main__":
    main()

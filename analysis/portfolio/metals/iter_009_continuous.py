"""iter-009 — CONTINUOUS-breadth dispersion gate: leak-free recovery of the bear edge.

THE PROBLEM (found by the live-parity reconcile, not the leak test): iter-008's dispersion regime
weight d_w[t] used the BINARY bear flag b[t] = (breadth ≥ 0.6) computed from candle t's OWN close —
a same-bar look-ahead. De-leaked (b[t-1]) the binary gate is NOISY (flips ~400×), so the one-bar lag
often lands on the wrong side of the 0.6 threshold and the bear edge collapses (bear +0.75→+0.19,
worst-DD −18.7%→−27.5%, WORSE than the plain L2+brake baseline).

THE FIX: scale the dispersion sleeve CONTINUOUSLY by the breadth FRACTION (the DEPTH of the bear),
not a binary gate:  d_w[t] = dw_bull + (dw_bear − dw_bull)·breadth[t-1],  breadth ∈ [0,1].
A continuous signal moves smoothly, so the one-bar de-leak lag barely perturbs it — the bear edge
survives. dw_bear capped at 1.0 (IS-tuned) keeps the tail TIGHTER than L2+brake. Leak-free + bit-
exact live-reproducible (proven by reconcile_metals.py). Mechanism = iter_008.regime_book(gate=...)
+ the frozen `CHAMP9` config; this module is the iter-009 scorecard + pristine-2008 generalization.

IS-ONLY tuned (the dw_bear endpoint chosen on the 2015→2025-03 IS); the 2011-15 bear + the 2008 GFC
crash are STRESS checks, never tuned on.

Run:  uv run python analysis/portfolio/metals/iter_009_continuous.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_007_allweather as aw  # noqa: E402
import iter_008_allweather as a8  # noqa: E402
import universe_metals as um  # noqa: E402

CHAMP9 = a8.CHAMP9  # {win:450, thresh:0.6, a_w:0.5, dw_bull:0.25, dw_bear:1.0, gate:"continuous"}


def scorecard() -> dict[str, dict]:
    """All-weather rows: L2+brake baseline vs iter-008 binary champ vs iter-009 continuous champ."""
    a8.bear.ingest_bear()  # self-heal data_bear/ (gold/silver) — idempotent, bear-blind
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)
    return {
        "L2 + brake (baseline)": a8._profile(
            a8._brake(aw.book_l2(cb)), a8._brake(aw.book_l2(cm))
        ),
        "iter-008 binary champ (dW.25->1.5)": a8._champ_profile(cb, cm),
        "iter-009 CONTINUOUS champ (dW.25->1.0)": a8._champ_profile(
            cb, cm, gate="continuous", dw_bear=1.0
        ),
    }


def pristine_2008() -> dict[str, dict] | None:
    """The FROZEN iter-009 champion on the never-touched 2008 GFC bear (generalization, not fit)."""
    if not (_HERE.parents[2] / "data_bear2008" / "XAUUSDT" / "8h.csv").exists():
        return None
    coins = um.load_metals(_HERE.parents[2] / "data_bear2008")
    net, _ = a8.regime_book(coins, **CHAMP9)
    out: dict[str, dict] = {}
    for lo, hi, lbl in [
        ("2008-03-01", "2009-06-01", "crash+recovery"),
        ("2008-07-01", "2008-12-31", "pure crash"),
    ]:
        s = net[(net.index >= pd.Timestamp(lo)) & (net.index < pd.Timestamp(hi))]
        eq = (1 + s).cumprod()
        out[lbl] = {
            "sharpe": um.msharpe(s, pd.Timestamp(lo), pd.Timestamp(hi)),
            "maxdd": float((eq / eq.cummax() - 1).min()),
            "ret": float(eq.iloc[-1] - 1),
        }
    return out


def main() -> None:
    print("=" * 104)
    print("iter-009 ALL-WEATHER SCORECARD — CONTINUOUS-breadth dispersion gate (leak-free bear)")
    print("=" * 104)
    rows = scorecard()
    for label, r in rows.items():
        print(
            f"  {label:42} BEAR={r['bsr']:+.2f}/{r['bdd'] * 100:5.1f}%  "
            f"IS={r['isr']:+.2f}/{r['idd'] * 100:5.1f}%  BULL={r['usr']:+.2f}  "
            f"worst={r['worst'] * 100:5.1f}%  all3+={r['allp']}"
        )
    p = pristine_2008()
    if p:
        print("\n  PRISTINE 2008 GFC bear (frozen champion, never selected on):")
        for lbl, d in p.items():
            print(
                f"    {lbl:18} Sharpe={d['sharpe']:+.2f}  maxDD={d['maxdd'] * 100:5.1f}%  "
                f"ret={d['ret'] * 100:+.0f}%"
            )


if __name__ == "__main__":
    main()

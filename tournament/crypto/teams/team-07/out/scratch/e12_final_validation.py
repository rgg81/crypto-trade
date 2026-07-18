"""e12: final validation of the frozen spec — subperiods, recent window, estimator robustness."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]

    vt = vslib.cc_vol(pn, 12) / vslib.cc_vol(pn, 84)
    sm = vt.ewm(halflife=72, min_periods=1).mean()
    raw = vslib.rank_signal(sm, elig, sign=+1.0)

    print("=== e12: frozen spec, full IS ===")
    vslib.run(raw, "e12 FROZEN cc 12/84 hl=72")

    print("=== e12: sub-windows (1x) ===")
    for lo, hi in (
        ("2020-01-01", "2022-04-01"),
        ("2022-04-01", "2024-07-01"),
        ("2023-07-01", "2024-07-01"),
    ):
        s = vslib.msharpe_window(raw, lo, hi)
        print(f"  {lo} .. {hi}: msharpe_1x = {s:+.3f}")

    print("=== e12: estimator robustness (pk, same params, report-only) ===")
    vtp = vslib.pk_vol(pn, 12) / vslib.pk_vol(pn, 84)
    smp = vtp.ewm(halflife=72, min_periods=1).mean()
    vslib.run(vslib.rank_signal(smp, elig, sign=+1.0), "e12 pk 12/84 hl=72")


if __name__ == "__main__":
    main()

"""e11: final pre-committed hl extension."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    vt = vslib.cc_vol(pn, 12) / vslib.cc_vol(pn, 84)
    for hl in (108, 144):
        sm = vt.ewm(halflife=hl, min_periods=1).mean()
        vslib.run(vslib.rank_signal(sm, elig, sign=+1.0), f"e11 vt 12/84 hl={hl}")
    vt2 = vslib.cc_vol(pn, 21) / vslib.cc_vol(pn, 84)
    sm2 = vt2.ewm(halflife=72, min_periods=1).mean()
    vslib.run(vslib.rank_signal(sm2, elig, sign=+1.0), f"e11 vt 21/84 hl=72")


if __name__ == "__main__":
    main()

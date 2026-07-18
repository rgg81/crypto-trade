"""e08: extend score-EMA halflife grid; e09: level+expansion composite blend."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]

    print("=== e08: halflife extension ===")
    vt1 = vslib.cc_vol(pn, 12) / vslib.cc_vol(pn, 84)
    for hl in (18, 24, 36):
        sm = vt1.ewm(halflife=hl, min_periods=1).mean()
        vslib.run(vslib.rank_signal(sm, elig, sign=+1.0), f"e08 vt 12/84 hl={hl}")
    vt2 = vslib.cc_vol(pn, 21) / vslib.cc_vol(pn, 126)
    sm2 = vt2.ewm(halflife=18, min_periods=1).mean()
    vslib.run(vslib.rank_signal(sm2, elig, sign=+1.0), f"e08 vt 21/126 hl=18")

    print("=== e09: composite level + expansion (hl=12 baseline; rerun with e08 winner if it moves) ===")
    lvl = vslib.rank_signal(vslib.cc_vol(pn, 84), elig, sign=+1.0)
    exp12 = vslib.rank_signal(vt1.ewm(halflife=12, min_periods=1).mean(), elig, sign=+1.0)
    for a in (0.25, 0.5, 0.75):
        vslib.run(a * lvl + (1.0 - a) * exp12, f"e09 blend a={a} (hl=12)")


if __name__ == "__main__":
    main()

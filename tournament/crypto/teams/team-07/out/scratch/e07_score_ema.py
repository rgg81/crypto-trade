"""e07: per-name EMA on the vt score BEFORE ranking — turnover control for the expansion alpha."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    for s, l in ((12, 84), (21, 126)):
        vt = vslib.cc_vol(pn, s) / vslib.cc_vol(pn, l)
        for hl in (3, 6, 12):
            sm = vt.ewm(halflife=hl, min_periods=1).mean()
            raw = vslib.rank_signal(sm, elig, sign=+1.0)
            vslib.run(raw, f"e07 vt {s}/{l} score-hl={hl}")


if __name__ == "__main__":
    main()

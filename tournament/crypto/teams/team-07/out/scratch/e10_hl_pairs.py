"""e10: hl extension {48,72} + 2D pair robustness at hl {36,48}."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402

GRID = {
    (12, 84): (48, 72),
    (21, 126): (36, 48),
    (12, 126): (36, 48),
    (21, 84): (36, 48),
}


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    for (s, l), hls in GRID.items():
        vt = vslib.cc_vol(pn, s) / vslib.cc_vol(pn, l)
        for hl in hls:
            sm = vt.ewm(halflife=hl, min_periods=1).mean()
            vslib.run(vslib.rank_signal(sm, elig, sign=+1.0), f"e10 vt {s}/{l} hl={hl}")


if __name__ == "__main__":
    main()

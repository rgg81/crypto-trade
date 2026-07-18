"""e06: vol dynamics — expansion ratio vol_short/vol_long, both signs, three (s,l) pairs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402

PAIRS = [(12, 84), (21, 126), (42, 168)]


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    for s, l in PAIRS:
        vt = vslib.cc_vol(pn, s) / vslib.cc_vol(pn, l)
        for sign, name in ((+1.0, "expand"), (-1.0, "compress")):
            raw = vslib.rank_signal(vt, elig, sign=sign)
            vslib.run(raw, f"e06 vt {s}/{l} long-{name}")


if __name__ == "__main__":
    main()

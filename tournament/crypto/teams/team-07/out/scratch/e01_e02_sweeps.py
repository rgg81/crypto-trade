"""e01: close-close vol window sweep; e02: Parkinson window sweep. Base transform, sign=-1
(long low-vol / short high-vol), every-candle emission."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402

WINDOWS = [21, 42, 84, 126, 168]


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    print("=== e01: cc vol sweep ===")
    for w in WINDOWS:
        raw = vslib.rank_signal(vslib.cc_vol(pn, w), elig, sign=-1.0)
        vslib.run(raw, f"e01 cc W={w}")
    print("=== e02: parkinson sweep ===")
    for w in WINDOWS:
        raw = vslib.rank_signal(vslib.pk_vol(pn, w), elig, sign=-1.0)
        vslib.run(raw, f"e02 pk W={w}")


if __name__ == "__main__":
    main()

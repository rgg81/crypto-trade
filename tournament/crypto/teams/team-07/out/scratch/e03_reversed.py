"""e03: H2 reversed-sign sweep — long high-vol / short low-vol, both estimators, full grid."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402

WINDOWS = [21, 42, 84, 126, 168]


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]
    for est, fn in (("cc", vslib.cc_vol), ("pk", vslib.pk_vol)):
        print(f"=== e03: {est} reversed (long high-vol) ===")
        for w in WINDOWS:
            raw = vslib.rank_signal(fn(pn, w), elig, sign=+1.0)
            vslib.run(raw, f"e03 {est} W={w} rev")


if __name__ == "__main__":
    main()

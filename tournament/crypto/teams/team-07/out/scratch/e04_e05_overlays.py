"""e04: EMA smoothing overlay on H2 cc base; e05: weekly-refresh overlay."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vslib  # noqa: E402


def weekly_hold(sig):
    is_refresh = (sig.index.weekday == 0) & (sig.index.hour == 0)
    held = sig.where(is_refresh[:, None] if False else None)  # placeholder
    return held


def main():
    pn, aux, scoring = vslib.panels()
    elig = aux["eligibility"]

    print("=== e04: EMA smoothing (cc reversed) ===")
    for w in (42, 84, 126):
        base = vslib.rank_signal(vslib.cc_vol(pn, w), elig, sign=+1.0)
        for hl in (6, 15, 30):
            sm = base.ewm(halflife=hl, min_periods=1).mean()
            vslib.run(sm, f"e04 cc W={w} hl={hl}")

    print("=== e05: weekly refresh (cc reversed) ===")
    for w in (84, 126):
        base = vslib.rank_signal(vslib.cc_vol(pn, w), elig, sign=+1.0)
        mask = (base.index.weekday == 0) & (base.index.hour == 0)
        held = base.copy()
        held.loc[~mask, :] = float("nan")
        held = held.ffill(limit=21).fillna(0.0)
        vslib.run(held, f"e05 cc W={w} weekly")


if __name__ == "__main__":
    main()

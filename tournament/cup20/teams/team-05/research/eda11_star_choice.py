"""EDA 11 -- choose the nominee and the three declared coordinates, on the plateau not the peak.

Section 7.2 scores the per-metric median of a declared star, so the object to reason about is the
star, not the point. Two rules constrain the choice and both are about honesty rather than score:

  * a coordinate whose downward variation TURNS A CONTROL OFF is not a neighbouring
    parameterisation, it is the ablation. MIN_BREADTH = 1 means "no breadth condition at all", so a
    nominee at MIN_BREADTH = 2 forces the ablation into its own robustness estimate.
  * a coordinate the strategy quantises into inertness voids the sweep (amendment A1). MIN_BREADTH
    is compared with `len(scores) < MIN_BREADTH`, so 1.5 and 2 are the same book: only integer
    variations are legitimate here.

HOLD_BARS is measured too, and reported, so the decision not to declare it is on the record with
its number rather than hidden.

Approximation, not a scorer.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "tournament/cup20/teams/team-05/research")

from eda10_basket_shape import KEYS, simulate  # noqa: E402


def star(nom: dict, coords: dict) -> tuple[dict, dict, int]:
    pts = [simulate(**nom)]
    labels = ["nominee"]
    for name, (lo, hi) in coords.items():
        pts.append(simulate(**{**nom, name: lo}))
        labels.append(f"{name}={lo}")
        pts.append(simulate(**{**nom, name: hi}))
        labels.append(f"{name}={hi}")
    med = {k: float(np.median([p[k] for p in pts])) for k in KEYS}
    pos = sum(1 for p in pts if p["gross%/yr"] > 0 and p["shp_2x"] > 0)
    for lab, p in zip(labels, pts, strict=True):
        print(f"      {lab:<22}" + "".join(f"{p[k]:>10.2f}" for k in
                                           ["shp_2x", "wfold", "mfold", "turn/yr", "bps/turn"]))
    return pts[0], med, pos


SHOW = ["turn/yr", "gross%/yr", "bps/turn", "shp_2x", "wfold", "mfold", "maxDD", "posQ"]
print(f"{'':<26}" + "".join(f"{k:>10}" for k in ["shp_2x", "wfold", "mfold", "turn/yr", "bps/turn"]))

CASES = [
    ("A  nominee br=2, coords {z, ts, br}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=2, basket=5),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "breadth": (1, 3)}),
    ("B  nominee br=3, coords {z, ts, br}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=3, basket=5),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "breadth": (2, 4)}),
    ("C  nominee br=3, coords {z, ts, basket}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=3, basket=5),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "basket": (4, 6)}),
    ("D  nominee br=2, coords {z, ts, basket}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=2, basket=5),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "basket": (4, 6)}),
    ("E  nominee br=3, coords {z, ts, hold}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=3, basket=5),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "hold_bars": (2, 4)}),
    ("F  nominee br=2 basket 8, coords {z, ts, basket}",
     dict(shock_z=-2.0, flow_spike=2.0, breadth=2, basket=8),
     {"shock_z": (-2.25, -1.75), "flow_spike": (1.6, 2.5), "basket": (6, 10)}),
]
for label, nom, coords in CASES:
    print()
    print(label)
    nomr, med, pos = star(nom, coords)
    print(f"   {'NOMINEE':<23}" + "".join(f"{nomr[k]:>11.2f}" for k in SHOW))
    print(f"   {'STAR MEDIAN':<23}" + "".join(f"{med[k]:>11.2f}" for k in SHOW)
          + f"   pos={pos}/7")

"""team-07 scratch runner — overnight-vs-intraday tug-of-war experiments (IS only).

Usage (from worktree root, AFTER the experiment ids are ledgered in experiments.jsonl):
    uv run python tournament/tradfi/teams/team-07/scratch_tugofwar.py e-002 e-003 ...

Data reaches this script ONLY via tournament.engine.load_is_panels(); signals are built from
te.team_view(pn) + aux. pn['ret_fwd'] is never touched in signal construction.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "analysis/portfolio/tradfi")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from neutralize import sector_neutralize  # noqa: E402  (approved substrate module)
from tournament import engine as te  # noqa: E402

OUT = Path("tournament/tradfi/teams/team-07/out")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- experiment configs ------------
# construct: SPREAD | ON | ID_REV      standardize: raw | tstat
# xform: rank | zscore                 weighting: linear | tercile
# ema_halflife: 0 = off                sector_neutral: bool
BASE = dict(
    construct="SPREAD", W=63, standardize="raw", xform="rank", weighting="linear",
    ema_halflife=0, sector_neutral=False,
)

CONFIGS: dict[str, dict] = {
    # batch 1 — locate the edge: three constructs at W=63, plainest settings
    "e-002": dict(BASE, construct="ON"),
    "e-003": dict(BASE, construct="ID_REV"),
    "e-004": dict(BASE, construct="SPREAD"),
    # batch 2 — formation sweep on the ON-persistence construct (batch 1 located the edge there;
    # ON-only IS the registered mechanism — SPREAD/ID were within-family controls)
    "e-005": dict(BASE, construct="ON", W=21),
    "e-006": dict(BASE, construct="ON", W=126),
    "e-007": dict(BASE, construct="ON", W=252),
    # batch 3 — variants at the W=252 plateau center (batch-2 winner)
    "e-008": dict(BASE, construct="ON", W=252, standardize="tstat"),
    "e-009": dict(BASE, construct="ON", W=252, xform="zscore"),
    "e-010": dict(BASE, construct="ON", W=252, weighting="tercile"),
    "e-011": dict(BASE, construct="ON", W=252, sector_neutral=True),
    "e-012": dict(BASE, construct="ON", W=252, ema_halflife=5),
    "e-013": dict(BASE, construct="ON", W=252, skip=21),
    # batch 5 — final spec confirmation (identical to e-012; determinism/reproduction check)
    "e-018": dict(BASE, construct="ON", W=252, ema_halflife=5),
    # batch 4 — smoothing depth + interactions around the champion (ON 252 rank linear ema5)
    "e-014": dict(BASE, construct="ON", W=252, ema_halflife=10),
    "e-015": dict(BASE, construct="ON", W=126, ema_halflife=5),
    "e-016": dict(BASE, construct="ON", W=252, weighting="tercile", ema_halflife=5),
    "e-017": dict(BASE, construct="ON", W=252, xform="zscore", ema_halflife=5),
}


# ---------------------------------------------------------------- signal construction -----------
def build_raw(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    o, c = view["open"], view["close"]
    on = o / c.shift(1) - 1.0          # overnight component (uses ONLY past/current bars)
    iday = c / o - 1.0                 # intraday component
    W = cfg["W"]

    def form(x: pd.DataFrame) -> pd.DataFrame:
        m = x.rolling(W, min_periods=W).mean()
        if cfg["standardize"] == "tstat":
            s = x.rolling(W, min_periods=W).std()
            return m / s.replace(0.0, np.nan)
        return m

    if cfg["construct"] == "ON":
        sig = form(on)
    elif cfg["construct"] == "ID_REV":
        sig = -form(iday)
    else:  # SPREAD
        sig = form(on) - form(iday)

    skip = cfg.get("skip", 0)
    if skip:  # 12-1-style: formation window ends `skip` bars before the decision bar
        sig = sig.shift(skip)

    if cfg["xform"] == "rank":
        r = sig.rank(axis=1, pct=True)
        w = r.sub(r.mean(axis=1), axis=0)
    else:  # zscore, winsorized, re-demeaned
        z = sig.sub(sig.mean(axis=1), axis=0).div(sig.std(axis=1).replace(0.0, np.nan), axis=0)
        z = z.clip(-3.0, 3.0)
        w = z.sub(z.mean(axis=1), axis=0)

    if cfg["weighting"] == "tercile":
        hi = sig.quantile(2.0 / 3.0, axis=1)
        lo = sig.quantile(1.0 / 3.0, axis=1)
        t = pd.DataFrame(np.nan, index=sig.index, columns=sig.columns)
        t = t.mask(sig.ge(hi, axis=0), 1.0).mask(sig.le(lo, axis=0), -1.0)
        t[sig.notna() & t.isna()] = 0.0
        w = t

    if cfg["sector_neutral"]:
        mask = w.isna()
        w = sector_neutralize(w.fillna(0.0), aux["sector_map"])
        w[mask] = 0.0

    h = cfg["ema_halflife"]
    if h:
        w = w.ewm(halflife=h, min_periods=1).mean()

    return w


# ---------------------------------------------------------------- run ---------------------------
def main(exp_ids: list[str]) -> None:
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    for eid in exp_ids:
        cfg = CONFIGS[eid]
        raw = build_raw(view, aux, cfg)
        _, _, m1 = te.run_is(raw, pn)
        _, _, m2 = te.run_is(raw, pn, cost_mult=2.0)
        rec = {"id": eid, "config": cfg, "metrics_1x": m1.to_dict(), "metrics_2x": m2.to_dict()}
        (OUT / f"{eid}.json").write_text(json.dumps(rec, indent=2))
        print(
            f"{eid}: sharpe1x={m1.sharpe:+.3f} sharpe2x={m2.sharpe:+.3f} "
            f"maxdd={m1.maxdd:+.3f} turn={m1.ann_turnover:.1f} "
            f"nL/nS={m1.median_names_long:.0f}/{m1.median_names_short:.0f} "
            f"regime={ {k: round(v, 2) for k, v in m1.regime_sharpe.items()} }"
        )


if __name__ == "__main__":
    main(sys.argv[1:])

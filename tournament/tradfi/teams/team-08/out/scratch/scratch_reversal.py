"""team-08 scratch experiments — own-name short-horizon reversal (family t08-short-horizon-reversal-v1).

QR-only analysis harness. Run from the worktree root:
    uv run python tournament/tradfi/teams/team-08/scratch_reversal.py <expname>

All performance numbers come from tournament.engine.run_is / evaluate (the evaluator).
Results are dumped as JSON under tournament/tradfi/teams/team-08/out/.
No sector_map, no vix, no seed usage — own-name signal only (family fidelity).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402

OUT = Path("tournament/tradfi/teams/team-08/out")
OUT.mkdir(parents=True, exist_ok=True)

VOL_WIN = 63
VOL_MINP = 40


# ------------------------------------------------------------------ signal --------------------
def build_score(
    view: dict,
    *,
    k: int,
    weighting: str = "rank",  # rank | z | zwinsor
    variant: str = "FULL",  # FULL | LAG1 | INTRA
    halflife: float = 0.0,  # EWMA halflife in days; 0 = none
    q: float = 0.5,  # per-tail concentration fraction; 0.5 = full book
    z_max: float = float("inf"),  # exclude |z|>z_max (informational gap gate)
) -> pd.DataFrame:
    close, open_ = view["close"], view["open"]
    ret1 = close / close.shift(1) - 1.0
    sigma = ret1.rolling(VOL_WIN, min_periods=VOL_MINP).std()

    if variant == "FULL":
        r_k = close / close.shift(k) - 1.0
        sig = sigma
    elif variant == "LAG1":
        r_k = (close / close.shift(k) - 1.0).shift(1)
        sig = sigma.shift(1)
    elif variant == "INTRA":
        # drop the t-1 -> t overnight leg: close[t-k] -> close[t-1], then open[t] -> close[t]
        r_k = (close.shift(1) / close.shift(k)) * (close / open_) - 1.0
        sig = sigma
    else:
        raise ValueError(variant)

    z = r_k / (sig * np.sqrt(k))

    # informational-gap gate: refuse to fade extreme standardized moves
    if np.isfinite(z_max):
        gate = z.abs() > z_max
    else:
        gate = pd.DataFrame(False, index=z.index, columns=z.columns)

    if weighting == "rank":
        base = r_k.mask(gate)
        ranks = base.rank(axis=1)
        score = -(ranks.sub(ranks.mean(axis=1), axis=0))
    elif weighting in ("z", "zwinsor"):
        zz = z.mask(gate)
        if weighting == "zwinsor":
            zz = zz.clip(-3.0, 3.0)
        score = -(zz.sub(zz.mean(axis=1), axis=0))
    else:
        raise ValueError(weighting)

    # per-tail concentration on the score itself
    if q < 0.5:
        pct = score.rank(axis=1, pct=True)
        keep = (pct <= q) | (pct >= 1.0 - q)
        score = score.where(keep)

    score = score.fillna(0.0)
    if halflife and halflife > 0:
        score = score.ewm(halflife=halflife, adjust=True).mean()
    return score


# ------------------------------------------------------------------ evaluation ----------------
def eval_config(view, pn, cfg: dict, *, cost_mults=(1.0, 2.0), subperiods=False) -> dict:
    raw = build_score(view, **cfg)
    row: dict = {"cfg": {k: (str(v) if v == float("inf") else v) for k, v in cfg.items()}}
    for cm in cost_mults:
        net, w, m = te.run_is(raw, pn, cost_mult=cm)
        tag = "1x" if cm == 1.0 else f"{cm:g}x"
        row[tag] = m.to_dict()
        if subperiods and cm == 1.0:
            for name, lo, hi in [
                ("2010_2016", "2010-01-01", "2017-01-01"),
                ("2017_2024", "2017-01-01", "2024-07-01"),
            ]:
                ms = te.evaluate(net, w, lo=pd.Timestamp(lo), hi=pd.Timestamp(hi))
                row[f"sub_{name}"] = {
                    "sharpe": ms.sharpe,
                    "maxdd": ms.maxdd,
                    "n_months": ms.n_months,
                }
    return row


def dump(name: str, payload) -> None:
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"wrote {p}")
    for row in payload if isinstance(payload, list) else [payload]:
        c = row["cfg"]
        m1, m2 = row.get("1x", {}), row.get("2x", {})
        print(
            f"  k={c.get('k')} w={c.get('weighting','rank')} var={c.get('variant','FULL')} "
            f"h={c.get('halflife',0)} q={c.get('q',0.5)} zmax={c.get('z_max','inf')} | "
            f"S1x={m1.get('sharpe'):+.3f} S2x={m2.get('sharpe', float('nan')):+.3f} "
            f"dd={m1.get('maxdd'):+.3f} to={m1.get('ann_turnover'):.1f} "
            f"nL={m1.get('median_names_long'):.0f}/nS={m1.get('median_names_short'):.0f}"
        )


# ------------------------------------------------------------------ experiments ---------------
def info(view, pn, aux):
    close = view["close"]
    per_year = close.notna().sum(axis=1).groupby(close.index.year).median()
    print(f"names={close.shape[1]} days={close.shape[0]} span={close.index[0]}..{close.index[-1]}")
    print("median valid names per year:")
    print(per_year.to_string())
    print(f"aux keys: {sorted(aux)} (sector_map/vix/seed UNUSED by design)")


def exp003(view, pn, aux):
    rows = [eval_config(view, pn, {"k": k, "weighting": "rank"}) for k in (1, 2, 3, 4, 5)]
    dump("exp003_lookback_grid", rows)


def exp004(view, pn, aux, k: int):
    rows = [
        eval_config(view, pn, {"k": k, "weighting": w}) for w in ("rank", "z", "zwinsor")
    ]
    dump("exp004_weighting", rows)


def exp005(view, pn, aux, base: dict):
    rows = [
        eval_config(view, pn, {**base, "halflife": h}) for h in (0, 1, 2, 3, 5, 8)
    ]
    dump("exp005_smoothing", rows)


def exp006(view, pn, aux, base: dict):
    rows = [
        eval_config(view, pn, {**base, "variant": v}) for v in ("FULL", "LAG1", "INTRA")
    ]
    dump("exp006_lastday", rows)


def exp007(view, pn, aux, base: dict):
    rows = [eval_config(view, pn, {**base, "q": q}) for q in (0.5, 0.35, 0.25, 0.15)]
    dump("exp007_concentration", rows)


def exp008(view, pn, aux, base: dict):
    rows = [
        eval_config(view, pn, {**base, "z_max": zm}) for zm in (float("inf"), 4.0, 3.0, 2.5)
    ]
    dump("exp008_gate", rows)


def exp009(view, pn, aux):
    rows = []
    for k in (1, 3, 5):
        for h in (2, 3, 5):
            rows.append(
                eval_config(
                    view,
                    pn,
                    {"k": k, "weighting": "rank", "variant": "INTRA", "halflife": h},
                    subperiods=True,
                )
            )
    dump("exp009_joint_cross", rows)
    for row in rows:
        s1, s2 = row.get("sub_2010_2016", {}), row.get("sub_2017_2024", {})
        c = row["cfg"]
        print(
            f"    k={c['k']} h={c['halflife']} sub-period Sharpe: "
            f"2010-16={s1.get('sharpe'):+.3f} 2017-24={s2.get('sharpe'):+.3f}"
        )


def exp010(view, pn, aux):
    rows = [
        eval_config(
            view,
            pn,
            {"k": 1, "weighting": "rank", "variant": "INTRA", "halflife": h},
            subperiods=True,
        )
        for h in (8, 12, 20, 30)
    ]
    dump("exp010_h_boundary", rows)
    for row in rows:
        s1, s2 = row.get("sub_2010_2016", {}), row.get("sub_2017_2024", {})
        c = row["cfg"]
        print(
            f"    h={c['halflife']} sub-period Sharpe: "
            f"2010-16={s1.get('sharpe'):+.3f} 2017-24={s2.get('sharpe'):+.3f}"
        )


def main():
    which = sys.argv[1]
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    if which == "info":
        info(view, pn, aux)
        return
    fns = {"exp003": exp003, "exp009": exp009, "exp010": exp010}
    if which in fns:
        fns[which](view, pn, aux)
        return
    # parameterized experiments read their frozen base config from out/base_cfg.json,
    # written by the QR when the ledger line is appended (pre-registration artifact)
    base = json.loads((OUT / "base_cfg.json").read_text())
    if which == "exp004":
        exp004(view, pn, aux, base["k"])
    elif which == "exp005":
        exp005(view, pn, aux, base)
    elif which == "exp006":
        exp006(view, pn, aux, base)
    elif which == "exp007":
        exp007(view, pn, aux, base)
    elif which == "exp008":
        exp008(view, pn, aux, base)
    else:
        raise SystemExit(f"unknown experiment {which}")


if __name__ == "__main__":
    main()

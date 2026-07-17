"""team-05 scratch explorer — t05-lowvol-bab-v1. IS data only, via the evaluator.

Run from worktree root:
    uv run python tournament/tradfi/teams/team-05/scratch_explore.py <batch.json>

<batch.json> = {"experiments": [{"id": "...", "config": {...}}, ...]}
Results are printed and dumped to tournament/tradfi/teams/team-05/out/scratch/results_<id>.json.
Signals use team_view/aux ONLY — ret_fwd is never touched here.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "analysis/portfolio/tradfi")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import core_tradfi as ct  # noqa: E402
from tournament import engine as te  # noqa: E402

TEAM_DIR = Path("tournament/tradfi/teams/team-05")
OUT_DIR = TEAM_DIR / "out" / "scratch"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ signal construction ---------
def daily_returns(view):
    return view["close"].pct_change(fill_method=None)


def vol_panel(view, L, estimator="std"):
    ret = daily_returns(view)
    mo = max(40, L // 2)
    if estimator == "std":
        return ret.rolling(L, min_periods=mo).std()
    if estimator == "ewma":
        return ret.ewm(halflife=L / 2, min_periods=mo).std()
    raise ValueError(estimator)


def beta_panel(view, L=252, min_obs=120, shrink=0.6):
    ret = daily_returns(view)
    mkt = ret.mean(axis=1)
    cov = ret.rolling(L, min_periods=min_obs).cov(mkt)
    var = mkt.rolling(L, min_periods=min_obs).var()
    b = cov.div(var, axis=0)
    return shrink * b + (1.0 - shrink) * 1.0


def idio_vol_panel(view, L):
    """Rolling std of market-residual returns: ret - shrunk_beta * ew_mkt."""
    ret = daily_returns(view)
    mkt = ret.mean(axis=1)
    b = beta_panel(view)
    resid = ret - b.mul(mkt, axis=0)
    return resid.rolling(L, min_periods=max(40, L // 2)).std()


def sector_rank_linear_weights(key, view, sector_map, min_names=4):
    """Within-sector symmetric rank weights (lowest key long). Sectors with < min_names flat."""
    key = key.where(view["close"].notna())
    out = pd.DataFrame(np.nan, index=key.index, columns=key.columns)
    sectors = {}
    for t in key.columns:
        sectors.setdefault(sector_map.get(t, "Unknown"), []).append(t)
    for _, cols in sectors.items():
        sub = key[cols]
        rank = sub.rank(axis=1, method="average")
        n = sub.notna().sum(axis=1)
        w = rank.rsub((n + 1) / 2.0, axis=0)
        w = w.where(n.ge(min_names), other=np.nan, axis=0)
        out[cols] = w
    return out


def rank_linear_weights(key, view):
    """Symmetric rank weights: lowest key most LONG, highest most SHORT. NaN = flat."""
    key = key.where(view["close"].notna())  # eligibility: sort key AND a close today
    rank = key.rank(axis=1, method="average")
    n = key.notna().sum(axis=1)
    return rank.rsub((n + 1) / 2.0, axis=0)  # (N+1)/2 - rank


def quantile_weights(key, view, q=15):
    key = key.where(view["close"].notna())
    rank = key.rank(axis=1, method="average")
    n = key.notna().sum(axis=1)
    hi_cut = rank.le(q, axis=0)  # q lowest-vol -> long
    lo_cut = rank.ge((n - q + 1), axis=0)  # q highest-vol -> short
    w = pd.DataFrame(0.0, index=key.index, columns=key.columns)
    w = w.mask(hi_cut, 1.0).mask(lo_cut, -1.0)
    return w.where(key.notna())


def bab_balance(raw, beta, floor=0.25):
    """Scale each leg by 1/leg-|w|-weighted-mean-beta (floored). Engine still owns caps."""
    b = beta.reindex(index=raw.index, columns=raw.columns)
    pos = raw.clip(lower=0.0).fillna(0.0)
    neg = (-raw.clip(upper=0.0)).fillna(0.0)
    bb = b.fillna(1.0)
    bp = ((pos * bb).sum(axis=1) / pos.sum(axis=1).replace(0.0, np.nan)).clip(lower=floor)
    bn = ((neg * bb).sum(axis=1) / neg.sum(axis=1).replace(0.0, np.nan)).clip(lower=floor)
    out = raw.clip(lower=0.0).div(bp, axis=0).fillna(0.0) + raw.clip(upper=0.0).div(
        bn, axis=0
    ).fillna(0.0)
    return out.where(raw.notna())


def build_raw(view, cfg, aux=None):
    sort = cfg.get("sort", "vol")
    L = int(cfg.get("L", 120))
    if sort == "vol":
        key = vol_panel(view, L, estimator=cfg.get("estimator", "std"))
    elif sort == "idio_vol":
        key = idio_vol_panel(view, L)
    elif sort == "beta":
        key = beta_panel(view, L=L, min_obs=int(cfg.get("min_obs", 120)),
                         shrink=float(cfg.get("shrink", 0.6)))
    else:
        raise ValueError(sort)
    weighting = cfg.get("weighting", "rank")
    if weighting == "sector_rank":
        raw = sector_rank_linear_weights(key, view, aux["sector_map"],
                                         min_names=int(cfg.get("min_sector_names", 4)))
    elif weighting == "rank":
        raw = rank_linear_weights(key, view)
    else:
        raw = quantile_weights(key, view, q=int(cfg.get("q", 15)))
    if cfg.get("bab_balance", False):
        raw = bab_balance(raw, beta_panel(view), floor=float(cfg.get("beta_floor", 0.25)))
    S = cfg.get("smooth_span")
    if S:
        raw = raw.fillna(0.0).ewm(span=int(S)).mean()
    return raw


# ------------------------------------------------------------------ diagnostics -----------------
def diagnostics(net, view):
    d = {}
    for tag, lo, hi in [
        ("sub_2010_2015", "2010-01-01", "2015-01-01"),
        ("sub_2015_2024H1", "2015-01-01", "2024-07-01"),
        ("meltup_core_2020_2021", "2020-04-01", "2021-02-15"),
    ]:
        d[tag + "_msharpe"] = float(ct.msharpe(net, pd.Timestamp(lo), pd.Timestamp(hi)))
    mkt = daily_returns(view).mean(axis=1)
    a = pd.concat([net.rename("net"), mkt.rename("mkt")], axis=1).dropna()
    if len(a) > 100 and a["mkt"].var() > 0:
        d["beta_of_net_vs_ew_mkt"] = float(a["net"].cov(a["mkt"]) / a["mkt"].var())
    return d


# ------------------------------------------------------------------ main ------------------------
def main():
    batch = json.loads(Path(sys.argv[1]).read_text())
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)
    results = {}
    for exp in batch["experiments"]:
        eid, cfg = exp["id"], exp["config"]
        raw = build_raw(view, cfg, aux)
        net1, w1, m1 = te.run_is(raw, pn)
        net2, w2, m2 = te.run_is(raw, pn, cost_mult=2.0)
        res = {
            "config": cfg,
            "m_1x": m1.to_dict(),
            "m_2x": m2.to_dict(),
            "diag": diagnostics(net1, view),
        }
        results[eid] = res
        print(f"\n===== {eid} {json.dumps(cfg)}")
        print(
            f"  1x: sharpe={m1.sharpe:+.3f} maxdd={m1.maxdd:+.3f} turn={m1.ann_turnover:.1f} "
            f"breadth L/S={m1.median_names_long:.0f}/{m1.median_names_short:.0f} "
            f"net={m1.mean_net:+.3f} gross={m1.mean_gross:.3f}"
        )
        print(f"  2x: sharpe={m2.sharpe:+.3f} maxdd={m2.maxdd:+.3f}")
        print(f"  regimes 1x: { {k: round(v, 3) for k, v in m1.regime_sharpe.items()} }")
        print(f"  diag: { {k: round(v, 4) for k, v in res['diag'].items()} }")
    out = OUT_DIR / f"results_{batch.get('batch_id', 'batch')}.json"
    out.write_text(json.dumps(results, indent=2, sort_keys=True))
    print(f"\n[saved] {out}")


if __name__ == "__main__":
    main()

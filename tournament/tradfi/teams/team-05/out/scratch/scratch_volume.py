"""team-05 scratch explorer — t05-volume-liquidity-anomalies-v1 (menu #6). IS only, evaluator only.

Run from worktree root:
    uv run python tournament/tradfi/teams/team-05/scratch_volume.py <batch.json>

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


# ------------------------------------------------------------------ signals ---------------------
def daily_returns(view):
    return view["close"].pct_change(fill_method=None)


def rel_volume_log(view, W):
    """log(volume / trailing-median volume): own-name abnormal volume. NaN-safe."""
    vol = view["volume"].where(view["volume"] > 0)
    med = vol.rolling(W, min_periods=W // 2).median()
    return np.log(vol / med)


def abnormal_volume_key(view, W, F):
    return rel_volume_log(view, W).rolling(F, min_periods=F).mean()


def amihud_key(view, K):
    """Trailing mean |ret| / dollar-volume (Amihud ILLIQ). Higher = more illiquid."""
    ret = daily_returns(view)
    dollar = (view["close"] * view["volume"]).where(lambda x: x > 0)
    return (ret.abs() / dollar).rolling(K, min_periods=K // 2).mean()


def divergence_key(view, D, W=60):
    """Volume-flow direction vs price path over D days: pct-rank(flow) - pct-rank(D-day ret)."""
    ret = daily_returns(view)
    vol = view["volume"].where(view["volume"] > 0)
    med = vol.rolling(W, min_periods=W // 2).median()
    ratio = vol / med
    flow = (np.sign(ret) * ratio).rolling(D, min_periods=D // 2).sum()
    pmom = view["close"].pct_change(D, fill_method=None)
    both = flow.notna() & pmom.notna()
    return flow.where(both).rank(axis=1, pct=True) - pmom.where(both).rank(axis=1, pct=True)


def rank_weights(key, view, direction=1):
    """Symmetric centered rank weights; direction=+1 -> HIGHEST key most long. NaN = flat."""
    key = key.where(view["close"].notna())
    rank = key.rank(axis=1, method="average")
    n = key.notna().sum(axis=1)
    return direction * rank.sub((n + 1) / 2.0, axis=0)


def tranche(raw, H):
    """Overlapping-portfolio smoothing: H-day rolling mean of daily rank-weight rows."""
    return raw.fillna(0.0).rolling(H, min_periods=1).mean() if H and H > 1 else raw


def build_raw(view, cfg):
    kind = cfg["kind"]
    if kind == "abn_vol":
        key = abnormal_volume_key(view, int(cfg.get("W", 60)), int(cfg.get("F", 5)))
    elif kind == "amihud":
        key = amihud_key(view, int(cfg.get("K", 126)))
        if cfg.get("weighting") == "quantile":
            key = key.where(view["close"].notna())
            rank = key.rank(axis=1, method="average", ascending=False)  # 1 = most illiquid
            n = key.notna().sum(axis=1)
            q = int(cfg.get("q", 15))
            w = pd.DataFrame(0.0, index=key.index, columns=key.columns)
            w = w.mask(rank.le(q, axis=0), 1.0).mask(rank.gt(n.sub(q), axis=0), -1.0)
            return w.where(key.notna())
    elif kind == "divergence":
        key = divergence_key(view, int(cfg.get("D", 20)), int(cfg.get("W", 60)))
    elif kind == "dollar_vol":  # trailing mean dollar volume (use direction=-1 for long-illiquid)
        dollar = (view["close"] * view["volume"]).where(lambda x: x > 0)
        K = int(cfg.get("K", 252))
        key = dollar.rolling(K, min_periods=K // 2).mean()
    elif kind == "blend":  # 50/50 pct-rank average of two configured legs
        a = build_raw(view, cfg["leg_a"])
        b = build_raw(view, cfg["leg_b"])
        return a.rank(axis=1, pct=True).sub(0.5) + b.rank(axis=1, pct=True).sub(0.5)
    else:
        raise ValueError(kind)
    raw = rank_weights(key, view, direction=int(cfg.get("direction", 1)))
    return tranche(raw, int(cfg.get("H", 0)))


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
        raw = build_raw(view, cfg)
        net1, w1, m1 = te.run_is(raw, pn)
        net2, w2, m2 = te.run_is(raw, pn, cost_mult=2.0)
        res = {"config": cfg, "m_1x": m1.to_dict(), "m_2x": m2.to_dict(),
               "diag": diagnostics(net1, view)}
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

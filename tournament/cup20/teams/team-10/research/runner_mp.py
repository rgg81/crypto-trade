"""Parallel driver for the offline simulator.

One worker process per core builds the panel and the regime measures once, then evaluates a
stream of configurations. Every configuration is a plain dict so the whole experiment log is
serialisable and can be re-run.
"""

from __future__ import annotations

import multiprocessing as mp
import warnings
from typing import Any

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

_STATE: dict[str, Any] = {}


def _init() -> None:
    from panel import panel
    from signals import Regime

    p = panel()
    _STATE["p"] = p
    _STATE["R"] = Regime(p)
    _STATE["cache"] = {}


def signal(name: str) -> np.ndarray:
    """Resolve a signal name of the form ``family:args`` against the shared Regime instance."""
    cache = _STATE["cache"]
    if name in cache:
        return cache[name]
    R = _STATE["R"]
    head, _, rest = name.partition(":")
    args = [int(a) if a.isdigit() else a for a in rest.split(",")] if rest else []
    fn = {
        "rv": R.rv,
        "rvbtc": R.rv_btc,
        "park": R.parkinson,
        "term": R.term,
        "rangeratio": R.range_ratio,
        "vr": R.variance_ratio,
        "disp": R.dispersion,
        "dispratio": R.dispersion_ratio,
        "corr": R.avg_correlation,
        "btccorr": R.btc_correlation,
        "btcshare": R.btc_share,
        "semi": R.semivariance_share,
        "vov": R.vol_of_vol,
    }[head]
    out = fn(*args)
    cache[name] = out
    return out


def zsig(name: str, window: int) -> np.ndarray:
    key = f"{name}|z{window}"
    cache = _STATE["cache"]
    if key not in cache:
        cache[key] = _STATE["R"].zscore(signal(name), window)
    return cache[key]


def _run(cfg: dict[str, Any]) -> dict[str, Any]:
    import fastsim as fs
    from book import build_weights

    p = _STATE["p"]
    R = _STATE["R"]
    z = zsig(cfg["sig"], cfg.get("zwin", 360)) * cfg.get("sgn", 1)
    thr_hi = cfg.get("thr_hi", cfg.get("thr", 0.0))
    thr_lo = cfg.get("thr_lo", thr_hi)
    up = cfg.get("up", 1.0)
    down = cfg.get("down", -1.0)
    mid = cfg.get("mid", None)
    state = np.full(len(z), np.nan)
    ok = np.isfinite(z)
    if mid is None:
        state[ok] = np.where(z[ok] > thr_hi, up, down)
    else:
        state[ok] = np.where(z[ok] > thr_hi, up, np.where(z[ok] < thr_lo, down, mid))

    rank = None
    if cfg.get("rank"):
        rname, rwin, rsgn = cfg["rank"]
        base = {
            "rvsym": R.rv_symbol,
            "semisym": R.semivariance_share_symbol,
        }[rname](rwin)
        rank = rsgn * R.zscore(base, cfg.get("rank_z", 360))

    w, reb = build_weights(
        p,
        state,
        rank=rank,
        cadence=cfg.get("cad", 1),
        phase=cfg.get("phase", 0),
        rebalance_on_change=cfg.get("on_change", False),
        warmup=cfg.get("warmup", 380),
    )
    r = fs.simulate(p, w, reb)
    m = dict(r.metrics)
    m["G"] = fs.rank_score(m)
    m["n_rebalance"] = int(reb.sum())
    sf = state[np.isfinite(state)]
    m["n_switch"] = int((np.diff(sf) != 0).sum()) if len(sf) > 1 else 0
    m["frac_long"] = float(np.mean(sf > 0.5)) if len(sf) else np.nan
    m["frac_short"] = float(np.mean(sf < -0.5)) if len(sf) else np.nan
    m["b1x"] = fs.bootstrap_positive_fraction(r.daily[1])
    out = {k: v for k, v in cfg.items() if k != "rank"}
    out["rank"] = str(cfg.get("rank"))
    out.update(m)
    return out


def run_many(configs: list[dict[str, Any]], workers: int = 8) -> pd.DataFrame:
    with mp.Pool(workers, initializer=_init) as pool:
        rows = pool.map(_run, configs, chunksize=4)
    return pd.DataFrame(rows)

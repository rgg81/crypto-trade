"""Parallel offline sweep harness. Nothing here is a tournament number."""

from __future__ import annotations

import itertools
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from book import G, cross_sectional_book, score_book, tranche_book
from flow import Flow, cs_residual, prev_mean, prev_std, prev_sum, rank_rows
from ic import fold_edges
from panel import Panel
from sim import Sim

_S = {}


def init():
    p = Panel()
    f = Flow(p)
    _S["p"] = p
    _S["f"] = f
    _S["sim"] = Sim(p)
    _S["E"] = p.eligible[p.d0 : p.dn]
    _S["fe"] = fold_edges(p.times)
    cut = lambda a: a[p.d0 : p.dn]  # noqa: E731
    E = _S["E"]
    _S["size"] = rank_rows(cut(prev_mean(f.log_ats, 90)), E)
    _S["liq"] = rank_rows(cut(prev_mean(f.log_qv, 90)), E)
    _S["cut"] = cut
    _S["cache"] = {}


def raw_measure(kind: str, w: int, nb: int = 90) -> np.ndarray:
    key = (kind, w, nb)
    if key in _S["cache"]:
        return _S["cache"][key]
    f, cut = _S["f"], _S["cut"]
    if kind == "per":
        pos = np.where(np.isfinite(f.imb), (f.imb > 0).astype(float), np.nan)
        v = cut(prev_mean(pos, w))
    elif kind == "perb":
        pos = np.where(np.isfinite(f.imb_base), (f.imb_base > 0).astype(float), np.nan)
        v = cut(prev_mean(pos, w))
    elif kind == "lvl":
        v = cut(f.netflow(w))
    elif kind == "zfl":
        s = prev_std(f.net_quote, 90)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = cut(np.where(s > 0, prev_mean(f.net_quote, w) / s, np.nan))
    elif kind == "bigp":
        big = f.log_ats - prev_mean(f.log_ats, nb)
        wgt = np.where(np.isfinite(big), np.clip(big, -3, 3), 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            num = prev_sum(np.nan_to_num(f.imb) * wgt * np.nan_to_num(f.qv), w)
            den = prev_sum(f.qv, w)
            v = cut(np.where(den > 0, num / den, np.nan))
    elif kind == "perbig":
        # persistence counted only over bars whose average print was above the symbol's own norm
        big = f.log_ats - prev_mean(f.log_ats, 90)
        sel = np.isfinite(f.imb) & np.isfinite(big) & (big > 0)
        num = prev_sum(np.where(sel & (f.imb > 0), 1.0, 0.0), w)
        den = prev_sum(np.where(sel, 1.0, 0.0), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = cut(np.where(den >= max(3, w // 6), num / den, np.nan))
    elif kind == "persml":
        big = f.log_ats - prev_mean(f.log_ats, 90)
        sel = np.isfinite(f.imb) & np.isfinite(big) & (big <= 0)
        num = prev_sum(np.where(sel & (f.imb > 0), 1.0, 0.0), w)
        den = prev_sum(np.where(sel, 1.0, 0.0), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = cut(np.where(den >= max(3, w // 6), num / den, np.nan))
    elif kind in ("imbeq", "coveq"):
        # Controls for the falsification of the print-size claim. ``imbeq`` is the EQUAL-BAR-WEIGHT
        # mean imbalance -- it removes the dominance of the highest-volume bars without using print
        # size at all. ``coveq`` is the same de-weighting applied to the covariance. If the
        # print-size measures do no better than these, the mechanism is "ignore the biggest bars",
        # not "condition on print size", and the certificate must say so.
        if kind == "imbeq":
            v = cut(prev_mean(f.imb, w))
        else:
            shock = f.log_ats - prev_mean(f.log_ats, 90)
            z = np.where(np.isfinite(shock) & np.isfinite(f.imb), np.clip(shock, -3.0, 3.0), np.nan)
            v = cut(prev_mean(np.where(np.isfinite(z), f.imb * z, np.nan), w))
    elif kind in ("covats", "covqv", "covnt", "covatsn"):
        # Volume-weighted covariance, over the last w bars, between the bar's signed taker
        # imbalance and the bar's print-size / volume / trade-count shock measured against the
        # SAME w bars. Positive = the unusually-large-print bars were buy-led while the
        # unusually-small-print bars were sell-led.
        src = {"covats": f.log_ats, "covatsn": f.log_ats, "covqv": f.log_qv, "covnt": f.log_nt}[kind]
        shock = src - prev_mean(src, w)
        z = np.where(np.isfinite(shock) & np.isfinite(f.imb), np.clip(shock, -3.0, 3.0), np.nan)
        num = prev_sum(np.where(np.isfinite(z), f.imb * z * f.qv, 0.0), w)
        den = prev_sum(np.where(np.isfinite(z), f.qv, 0.0), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = np.where(den > 0, num / den, np.nan)
        if kind == "covatsn":  # scale-free: divide by the window's own shock dispersion
            sd = prev_std(np.where(np.isfinite(z), z, np.nan), w)
            with np.errstate(invalid="ignore", divide="ignore"):
                v = np.where(sd > 0, v / sd, np.nan)
        v = cut(v)
    elif kind == "imbsmlm":
        # IMBSML with the small/large split taken at the WINDOW'S OWN MEDIAN print-size shock
        # rather than at zero. Always defined (half the window qualifies by construction), so the
        # measure never drops a symbol out of the cross-section during a print-size regime shift --
        # which is exactly when the sign-of-shock split goes undefined and is not obviously a
        # moment worth discarding.
        big = f.log_ats - prev_mean(f.log_ats, nb)
        n, m = big.shape
        v = np.full((n, m), np.nan)
        nq, qq = f.net_quote, f.qv
        for i in range(w, n):
            blk = big[i - w : i]
            med = np.nanmedian(blk, axis=0)
            sel = np.isfinite(blk) & np.isfinite(nq[i - w : i]) & (blk <= med)
            den = np.where(sel, qq[i - w : i], 0.0).sum(axis=0)
            num = np.where(sel, nq[i - w : i], 0.0).sum(axis=0)
            with np.errstate(invalid="ignore", divide="ignore"):
                v[i] = np.where(den > 0, num / den, np.nan)
        v = cut(v)
    elif kind in ("imbsml0", "imbbig0"):
        # Same as imbsml/imbbig but with NO minimum-count guard: defined whenever the window holds
        # at least one qualifying bar. Exists to test whether the guard -- and therefore the
        # missing-component policy it triggers -- is doing any of the work.
        big = f.log_ats - prev_mean(f.log_ats, nb)
        sel = np.isfinite(f.imb) & np.isfinite(big) & ((big <= 0) if kind == "imbsml0" else (big > 0))
        num = prev_sum(np.where(sel, f.net_quote, 0.0), w)
        den = prev_sum(np.where(sel, f.qv, 0.0), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = cut(np.where(den > 0, num / np.where(den > 0, den, np.nan), np.nan))
    elif kind in ("imbsml", "imbbig"):
        # Taker imbalance measured ONLY over bars whose average print size was below (imbsml) or
        # above (imbbig) that symbol's own NORM_BARS norm. The mandate's conditioning question in
        # its most direct form: does the same USDT of net taker buying mean the same thing when it
        # arrived in many small prints as when it arrived in few large ones?
        big = f.log_ats - prev_mean(f.log_ats, nb)
        sel = np.isfinite(f.imb) & np.isfinite(big) & ((big <= 0) if kind == "imbsml" else (big > 0))
        num = prev_sum(np.where(sel, f.net_quote, 0.0), w)
        den = prev_sum(np.where(sel, f.qv, 0.0), w)
        cnt = prev_sum(sel.astype(float), w)
        with np.errstate(invalid="ignore", divide="ignore"):
            v = cut(np.where((cnt >= max(4, w // 6)) & (den > 0), num / np.where(den > 0, den, np.nan), np.nan))
    elif kind == "ret":
        v = cut(f.ret_w(w))
    else:
        raise KeyError(kind)
    _S["cache"][key] = v
    return v


def score(kinds, weights, w, purge, nb: int = 90, strict: bool = False):
    E = _S["E"]
    raws = [raw_measure(kind, w, nb) for kind in kinds]
    if strict:
        # Every component must be defined for a symbol to enter the cross-section, and the ranks
        # are then formed over one common valid set -- which is what the frozen strategy does.
        ok = E.copy()
        for r in raws:
            ok &= np.isfinite(r)
        parts = [wt * rank_rows(r, ok) for r, wt in zip(raws, weights, strict=True)]
        z = np.nansum(np.stack(parts), axis=0)
        z = np.where(ok, z, np.nan)
    else:
        parts = [wt * rank_rows(r, E) for r, wt in zip(raws, weights, strict=True)]
        z = np.nansum(np.stack(parts), axis=0)
        z = np.where(np.all(np.stack([~np.isfinite(pp) for pp in parts]), axis=0), np.nan, z)
    base = ok if strict else E
    ctrl = []
    if "ret" in purge:
        ctrl.append(rank_rows(raw_measure("ret", w, nb), base))
    if "size" in purge:
        ctrl.append(rank_rows(_S["cut"](prev_mean(_S["f"].log_ats, nb)), base))
    if "liq" in purge:
        ctrl.append(rank_rows(_S["cut"](prev_mean(_S["f"].log_qv, nb)), base))
    if ctrl:
        z = cs_residual(z, ctrl, base)
    return z


def one(cfg: dict) -> dict:
    S = score(cfg["kinds"], cfg["weights"], cfg["w"], cfg["purge"], cfg.get("nb", 90), cfg.get("strict", False))
    if "hold" in cfg:
        W = tranche_book(
            S, _S["E"], k=cfg["k"], hold=cfg["hold"], weight=cfg.get("weight", "equal")
        )
    else:
        W = cross_sectional_book(
            S,
            _S["E"],
            k=cfg["k"],
            cadence=cfg["cadence"],
            phase=cfg["phase"],
            smooth=cfg.get("smooth", 0.0),
            weight=cfg.get("weight", "equal"),
        )
    r = score_book(_S["sim"], W, _S["fe"], levels=cfg.get("levels", (1, 2, 3)))
    r["G"] = G(r)
    r.update({k: (v if not isinstance(v, (list, tuple)) else "+".join(map(str, v)))
              for k, v in cfg.items() if k not in ("levels",)})
    return r


def run(cfgs, workers=10, out=None):
    with Pool(workers, initializer=init) as pool:
        rows = pool.map(one, cfgs, chunksize=1)
    df = pd.DataFrame(rows)
    if out:
        df.to_csv(out, index=False)
    return df

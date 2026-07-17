"""team-06 scratch engine — sector pairs / cointegration stat-arb (t06-sector-pairs-coint-v1).

Config-driven: evaluates one or more configs against the frozen IS snapshot through the
tournament evaluator ONLY. Run from the worktree root:

    uv run python tournament/tradfi/teams/team-06/scratch_pairs.py census
    uv run python tournament/tradfi/teams/team-06/scratch_pairs.py run '{"tag":"exp-004"}' ...

Every material config passed to `run` must already have its pre-registered line in
experiments.jsonl (ledger discipline lives in the operator workflow, not here).
"""

from __future__ import annotations

import itertools
import json
import math
import sys
import time

sys.path.insert(0, "analysis/portfolio/tradfi")
from tournament import engine as te  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

DEF = dict(
    tag="",
    score="df",  # df | ssd | corr
    w_form=252,
    resel=21,
    n_pairs=20,
    z_mode="frozen",  # frozen | rolling
    w_z=63,
    z_dead=0.5,
    z_max=3.0,
    book="cont",  # cont | band
    z_in=2.0,
    z_out=0.5,
    sizing="equal",  # equal | invvol
    ema_hl=0.0,
    max_per_name=0,  # 0 = unlimited
    z_stop=0.0,  # >0: exit + block when spread diverges to |z| >= z_stop
    t_stop=0,  # >0: exit + block after t_stop days in position
    df_max=None,  # score=="df" only: keep pairs with DF t-stat <= df_max (quality gate)
    beta_lo=0.2,
    beta_hi=5.0,
    min_frac_valid=0.95,
    cost_mult=1.0,
    invert=False,  # DIAGNOSTIC ONLY (continuous book): flip sign to test divergence structure
)


def _df_tstat(e: np.ndarray) -> float:
    """Dickey-Fuller t-stat of rho in de_t = rho*e_{t-1} + eps (no intercept; e ~ OLS residual)."""
    de = np.diff(e)
    lag = e[:-1]
    den = float((lag * lag).sum())
    if den <= 0.0 or len(de) < 20:
        return np.nan
    rho = float((lag * de).sum()) / den
    resid = de - rho * lag
    s2 = float((resid * resid).sum()) / max(len(de) - 1, 1)
    se = math.sqrt(s2 / den)
    return rho / se if se > 0 else np.nan


def _score_pair(yi: np.ndarray, yj: np.ndarray, need: int, cfg: dict):
    """Estimate (beta, alpha, mu, sd, sd_de, score) on the masked formation window, or None."""
    m = np.isfinite(yi) & np.isfinite(yj)
    if int(m.sum()) < need:
        return None
    a = yi[m]
    b = yj[m]
    vb = float(b.var())
    if vb <= 0.0:
        return None
    beta = float(((a - a.mean()) * (b - b.mean())).mean()) / vb
    if not (cfg["beta_lo"] <= beta <= cfg["beta_hi"]):
        return None
    alpha = float(a.mean() - beta * b.mean())
    e = a - alpha - beta * b
    sd = float(e.std(ddof=1))
    if not np.isfinite(sd) or sd <= 1e-10:
        return None
    de = np.diff(e)
    sd_de = float(de.std(ddof=1)) if len(de) > 2 else np.nan
    if cfg["score"] == "df":
        score = _df_tstat(e)
    elif cfg["score"] == "ssd":
        pa = np.exp(a - a[0])
        pb = np.exp(b - b[0])
        score = float(((pa - pb) ** 2).mean())
    elif cfg["score"] == "corr":
        ra = np.diff(a)
        rb = np.diff(b)
        c = float(np.corrcoef(ra, rb)[0, 1]) if len(ra) > 20 else np.nan
        score = -c  # ascending sort => most correlated first
    else:
        raise ValueError(cfg["score"])
    if not np.isfinite(score) or not np.isfinite(sd_de) or sd_de <= 0:
        return None
    return beta, alpha, float(e.mean()), sd, sd_de, score


def build_raw(view: dict, aux: dict, cfg: dict) -> pd.DataFrame:
    cfg = {**DEF, **cfg}
    close = view["close"]
    cols = list(close.columns)
    colpos = {c: k for k, c in enumerate(cols)}
    dates = close.index
    T = len(dates)
    x = np.log(close.astype(float))
    xf = x.ffill(limit=5)  # spread-evaluation prices; >5d gap => NaN => flat
    Xf = xf.to_numpy()
    validn = x.notna().to_numpy()
    vcum = validn.cumsum(axis=0)

    sectors: dict[str, list[str]] = {}
    for tkr, sec in aux["sector_map"].items():
        if tkr in colpos:
            sectors.setdefault(sec, []).append(tkr)

    W = int(cfg["w_form"])
    R = int(cfg["resel"])
    need = math.ceil(cfg["min_frac_valid"] * W)
    sel_pos = list(range(W - 1, T, R))
    raw = np.zeros((T, len(cols)))
    band_state: dict[tuple[str, str], float] = {}

    for k, s in enumerate(sel_pos):
        seg_end = sel_pos[k + 1] if k + 1 < len(sel_pos) else T
        w0 = s - W + 1
        vc = vcum[s] - (vcum[w0 - 1] if w0 > 0 else 0)
        recent = validn[max(0, s - 4): s + 1].any(axis=0)
        ok = (vc >= need) & recent
        ok_names = {c for c in cols if ok[colpos[c]]}

        scored = []
        Xwin = Xf[w0: s + 1]
        for sec_names in sectors.values():
            ns = sorted(n for n in sec_names if n in ok_names)
            for i, j in itertools.combinations(ns, 2):
                r = _score_pair(Xwin[:, colpos[i]], Xwin[:, colpos[j]], need, cfg)
                if r is not None:
                    scored.append((r[5], i, j, r[0], r[1], r[2], r[3], r[4]))
        scored.sort(key=lambda t: t[0])
        if cfg["score"] == "df" and cfg.get("df_max") is not None:
            scored = [t for t in scored if t[0] <= float(cfg["df_max"])]

        selected = []
        name_ct: dict[str, int] = {}
        cap = int(cfg["max_per_name"])
        for sc, i, j, beta, alpha, mu, sd, sd_de in scored:
            if cap > 0 and (name_ct.get(i, 0) >= cap or name_ct.get(j, 0) >= cap):
                continue
            selected.append((i, j, beta, alpha, mu, sd, sd_de))
            name_ct[i] = name_ct.get(i, 0) + 1
            name_ct[j] = name_ct.get(j, 0) + 1
            if len(selected) >= int(cfg["n_pairs"]):
                break

        med_sd_de = float(np.median([p[6] for p in selected])) if selected else np.nan
        new_state: dict[tuple[str, str], float] = {}
        for i, j, beta, alpha, mu, sd, sd_de in selected:
            ci, cj = colpos[i], colpos[j]
            if cfg["z_mode"] == "rolling":
                lo = max(0, s - int(cfg["w_z"]) + 1 - (seg_end - s))
                e_ser = pd.Series(Xf[lo:seg_end, ci] - alpha - beta * Xf[lo:seg_end, cj])
                rm = e_ser.rolling(int(cfg["w_z"]), min_periods=int(cfg["w_z"]))
                zf = ((e_ser - rm.mean()) / rm.std()).to_numpy()
                z = zf[(s - lo): (seg_end - lo)]
            else:
                e = Xf[s:seg_end, ci] - alpha - beta * Xf[s:seg_end, cj]
                z = (e - mu) / sd
            finite = np.isfinite(z)

            if cfg["book"] == "cont":
                zc = np.where(finite, z, 0.0)
                p = -np.clip(zc, -cfg["z_max"], cfg["z_max"])
                p[np.abs(zc) < cfg["z_dead"]] = 0.0
                p[~finite] = 0.0
            else:  # banded, stateful; carries iff identical pair re-selected
                pos, held, blocked = band_state.get((i, j), (0.0, 0, False))
                zstp = float(cfg["z_stop"] or 0.0)
                tstp = int(cfg["t_stop"] or 0)
                p = np.zeros(len(z))
                for t in range(len(z)):
                    if finite[t]:
                        zt = z[t]
                        if pos != 0.0:
                            held += 1
                            if abs(zt) <= cfg["z_out"]:
                                pos, held = 0.0, 0
                            elif zstp > 0 and ((pos < 0 and zt >= zstp) or (pos > 0 and zt <= -zstp)):
                                pos, held, blocked = 0.0, 0, True
                            elif tstp > 0 and held >= tstp:
                                pos, held, blocked = 0.0, 0, True
                        if pos == 0.0:
                            if blocked:
                                if abs(zt) <= cfg["z_out"]:
                                    blocked = False
                            elif zt >= cfg["z_in"]:
                                pos, held = -1.0, 0
                            elif zt <= -cfg["z_in"]:
                                pos, held = 1.0, 0
                    p[t] = pos
                new_state[(i, j)] = (pos, held, blocked)

            u = 1.0 / (1.0 + beta)
            if cfg["sizing"] == "invvol":
                u *= float(np.clip(med_sd_de / sd_de, 0.0, 3.0))
            raw[s:seg_end, ci] += p * u
            raw[s:seg_end, cj] -= p * beta * u
        band_state = new_state

    out = pd.DataFrame(raw, index=dates, columns=cols)
    if cfg.get("invert"):
        out = -out
    if cfg["ema_hl"] and cfg["ema_hl"] > 0:
        out = out.ewm(halflife=float(cfg["ema_hl"]), min_periods=1).mean()
    return out


def _fmt(m) -> dict:
    d = m.to_dict()
    return {
        "sharpe": round(d["sharpe"], 3),
        "maxdd": round(d["maxdd"], 3),
        "ann_turnover": round(d["ann_turnover"], 1),
        "total_return": round(d["total_return"], 3),
        "med_long": d["median_names_long"],
        "med_short": d["median_names_short"],
        "mean_gross": round(d["mean_gross"], 3),
        "mean_net": round(d["mean_net"], 4),
        "regime_sharpe": {k: round(v, 2) for k, v in d["regime_sharpe"].items()},
    }


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "census"
    pn, aux = te.load_is_panels()
    view = te.team_view(pn)

    if mode == "census":
        close = view["close"]
        sec_hist: dict[str, int] = {}
        for t in close.columns:
            sec_hist[aux["sector_map"].get(t, "Unknown")] = (
                sec_hist.get(aux["sector_map"].get(t, "Unknown"), 0) + 1
            )
        first_valid = close.notna().idxmax()
        print(json.dumps({
            "n_names": len(close.columns),
            "n_days": len(close.index),
            "span": [str(close.index[0].date()), str(close.index[-1].date())],
            "sector_hist": dict(sorted(sec_hist.items(), key=lambda kv: -kv[1])),
            "names_by_start_year": pd.Series(
                [d.year for d in first_valid]).value_counts().sort_index().to_dict(),
        }, indent=2))
        # candidate-pair counts at a few positions for W=252
        W, need = 252, math.ceil(0.95 * 252)
        validn = close.notna().to_numpy()
        vcum = validn.cumsum(axis=0)
        cols = list(close.columns)
        colpos = {c: k for k, c in enumerate(cols)}
        for s in [W - 1, len(close) // 3, 2 * len(close) // 3, len(close) - 1]:
            w0 = s - W + 1
            vc = vcum[s] - (vcum[w0 - 1] if w0 > 0 else 0)
            ok = {c for c in cols if vc[colpos[c]] >= need}
            n_pairs = 0
            secs: dict[str, list[str]] = {}
            for tkr, sec in aux["sector_map"].items():
                if tkr in ok:
                    secs.setdefault(sec, []).append(tkr)
            for ns in secs.values():
                n_pairs += len(ns) * (len(ns) - 1) // 2
            print(json.dumps({"pos": s, "date": str(close.index[s].date()),
                              "eligible_names": len(ok), "candidate_pairs": n_pairs}))
        return

    # run mode: each argv[2:] item is a JSON config overlay on DEF
    for arg in sys.argv[2:]:
        cfg = {**DEF, **json.loads(arg)}
        t0 = time.time()
        raw = build_raw(view, aux, cfg)
        net, w, m = te.run_is(raw, pn, cost_mult=float(cfg.get("cost_mult", 1.0)))
        res = {"tag": cfg["tag"], "cfg": {k: v for k, v in cfg.items() if v != DEF.get(k)},
               "metrics": _fmt(m), "wall_s": round(time.time() - t0, 1)}
        print(json.dumps(res))


if __name__ == "__main__":
    main()

"""Offline design sweep -- unlimited, unscored, and journaled nowhere.

Every configuration is a full in-sample two-pass evaluation through ``fastsim``, so the numbers are
directly comparable with each other and (to the residual measured in ``calibrate.py``) with the
organiser's harness. Nothing here is reported as a result.
"""

from __future__ import annotations

import itertools
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "tournament/cup20/teams/team-11/research")
import book as B  # noqa: E402
import fastsim  # noqa: E402
import measures as M  # noqa: E402
import panel as panel_mod  # noqa: E402

IS_START = pd.Timestamp("2020-08-17T00:00:00Z")


def build_controls(p, w):
    el = p.eligible[w]
    qv = np.where(el, p.quote_volume[w], np.nan)
    clr = M.close_log_return(p.close[w])
    absr = np.abs(clr)
    return {
        "size": np.log(np.maximum(M.causal_rolling_sum(qv, 126), 1.0)),
        "vol": np.sqrt(M.causal_rolling_sum(absr**2, 126)),
        "mom": M.causal_rolling_sum(clr, 63),
        "fund": M.causal_rolling_sum(np.abs(np.where(el, p.funding_at_f[w], np.nan)), 126),
    }


def evaluate(p, start_idx, weights_full, reb_full):
    return fastsim.full_evaluate(p, start_idx, weights_full, reb_full)


def summarise(res, label, extra=None):
    m1, m2, m3 = res[1], res[2], res[3]
    row = {
        "config": label,
        "sharpe_1x": m1["sharpe"],
        "sharpe_2x": m2["sharpe"],
        "sharpe_3x": m3["sharpe"],
        "ret_1x": m1["ann_return"],
        "ret_2x": m2["ann_return"],
        "vol_1x": m1["ann_vol"],
        "dd_1x": m1["max_dd"],
        "dd_2x": m2["max_dd"],
        "calmar_2x": m2["calmar"],
        "turnover": m1["ann_turnover"],
        "gross_edge": m1["gross_edge_bps"],
        "cost_share": m1["cost_share"],
        "trades": m1["trades"],
        "long_gross": m1["long_gross"],
        "short_gross": m1["short_gross"],
        "top5": m1["top5_share"],
    }
    if extra:
        row.update(extra)
    return row


def fold_stats(res, times, level=2):
    d = pd.Series(res[level]["daily"], index=pd.DatetimeIndex(res[level]["daily_index"], tz="UTC"))
    bounds = [
        ("F1", "2020-08-17", "2021-08-01"),
        ("F2", "2021-08-01", "2022-08-01"),
        ("F3", "2022-08-01", "2023-08-01"),
        ("F4", "2023-08-01", "2024-08-01"),
    ]
    out = {}
    for name, s, e in bounds:
        x = d[(d.index >= pd.Timestamp(s, tz="UTC")) & (d.index < pd.Timestamp(e, tz="UTC"))]
        v = x.to_numpy()
        out[name] = (
            float(np.mean(v)) / float(np.std(v, ddof=1)) * np.sqrt(365.0)
            if len(v) > 1 and np.std(v, ddof=1) > 0 else 0.0
        )
    out["worst"] = min(out[k] for k in ("F1", "F2", "F3", "F4"))
    out["median_fold"] = float(np.median([out[k] for k in ("F1", "F2", "F3", "F4")]))
    out["npos"] = sum(1 for k in ("F1", "F2", "F3", "F4") if out[k] > 0)
    return out


def main() -> None:
    t0 = time.time()
    p = panel_mod.load()
    w = p.times >= IS_START
    start_idx = int(np.where(p.times == IS_START)[0][0])
    el = p.eligible[w]
    times = p.times[w]
    n = len(times)
    ctrl = build_controls(p, w)

    grid_quantity = ["volume", "volatility"]
    grid_window = [63, 126, 252]
    grid_contrast = ["asia", "us_minus_asia", "euro", "weekend"]
    grid_neutral = ["none", "vol", "all4"]
    grid_scheme = ["rank", "tercile"]
    grid_cadence = [1, 3, 9, 21]

    rows = []
    cache: dict = {}
    for quantity, window, contrast in itertools.product(
        grid_quantity, grid_window, grid_contrast
    ):
        if contrast == "weekend":
            raw = B.weekend_share(p, w, "volume" if quantity == "trades" else quantity, window)
            sign = -1.0
        elif contrast == "asia":
            raw = B.session_share(p, w, quantity, window, [0])
            sign = -1.0
        elif contrast == "euro":
            raw = B.session_share(p, w, quantity, window, [1])
            sign = +1.0
        else:
            raw = B.session_share(p, w, quantity, window, [2]) - B.session_share(
                p, w, quantity, window, [0]
            )
            sign = +1.0
        for neutral in grid_neutral:
            key = (quantity, window, contrast, neutral)
            if neutral == "none":
                sig = M.cross_section_rank(raw, el)
            elif neutral == "vol":
                sig = B.neutralise(raw, [ctrl["vol"]], el)
            elif neutral == "vol_size":
                sig = B.neutralise(raw, [ctrl["vol"], ctrl["size"]], el)
            else:
                sig = B.neutralise(raw, list(ctrl.values()), el)
            cache[key] = sig
            for scheme, cadence in itertools.product(grid_scheme, grid_cadence):
                wts = B.rank_book(sig, el, sign=sign, scheme=scheme)
                reb = B.cadence_mask(n, cadence, 0)
                res = evaluate(p, start_idx, wts, reb)
                label = f"{quantity}|{contrast}|W{window}|{neutral}|{scheme}|c{cadence}"
                extra = {
                    "quantity": quantity, "contrast": contrast, "window": window,
                    "neutral": neutral, "scheme": scheme, "cadence": cadence,
                }
                extra.update(fold_stats(res, times))
                rows.append(summarise(res, label, extra))
        print(f"  {quantity}/{contrast}/W{window} done  ({time.time() - t0:.0f}s, "
              f"{len(rows)} configs)", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv("tournament/cup20/teams/team-11/research/sweep_stage1.csv", index=False)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 200)
    cols = ["config", "sharpe_1x", "sharpe_2x", "vol_1x", "dd_1x", "turnover", "gross_edge",
            "cost_share", "trades", "worst", "median_fold", "npos", "long_gross", "short_gross"]
    print(f"\n{len(out)} configurations, {time.time() - t0:.0f}s")
    print("\n=== top 30 by 2x Sharpe ===")
    print(out.sort_values("sharpe_2x", ascending=False).head(30)[cols].to_string(
        index=False, float_format="%.3f"))
    print("\n=== top 25 by 2x Sharpe among turnover <= 25 ===")
    sel = out[out.turnover <= 25.0]
    print(sel.sort_values("sharpe_2x", ascending=False).head(25)[cols].to_string(
        index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()

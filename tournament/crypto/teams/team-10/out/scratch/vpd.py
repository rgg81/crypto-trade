"""team-10 scratch — volume-price divergence experiment runner.

Scratch-only (out/scratch/ is excluded from the harness scan and the frozen bundle).
Data access exclusively via the evaluator API. Usage:

    uv run python tournament/crypto/teams/team-10/out/scratch/vpd.py <exp_id> [key=val ...]

Prints one JSON blob per config and saves out/scratch/results/<exp_id>.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/roberto/crypto-trade/.worktrees/quant-portfolio-tournament/analysis")
from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)

EPS = 1e-12


# ---------------------------------------------------------------- signals ----------------------
def conf_panel(qv: pd.DataFrame, L: int, B: int) -> pd.DataFrame:
    """log participation ratio: move-window volume vs own pre-move baseline (past-only)."""
    ma_l = qv.rolling(L, min_periods=L).mean()
    ma_b = qv.rolling(B, min_periods=B).mean().shift(L)
    conf = np.log(ma_l.clip(lower=EPS)) - np.log(ma_b.clip(lower=EPS))
    return conf.where((ma_l > 0) & (ma_b > 0))


def cs_rank_centered(x: pd.DataFrame, elig: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank over eligible names, centered to [-1, +1]."""
    r = x.where(elig).rank(axis=1, pct=True)
    return 2.0 * (r - 0.5)


def vpd_signal(
    pn: dict,
    aux: dict,
    *,
    L: int,
    B: int = 90,
    H: int = 3,
    dform: str = "D1",
    soft: float = 0.0,
) -> pd.DataFrame:
    close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]
    ret_l = close / close.shift(L) - 1.0
    C = cs_rank_centered(conf_panel(qv, L, B), elig)
    if soft > 0.0:
        C = C.where(C.abs() >= soft, 0.0)
    if dform == "D1":
        D = np.sign(ret_l)
    elif dform == "D2":
        D = cs_rank_centered(ret_l, elig)
    else:
        raise ValueError(dform)
    S = (D * C).where(elig).fillna(0.0)
    if H > 1:
        S = S.ewm(span=H, adjust=False).mean()
    return S


def vpd_ami_signal(
    pn: dict,
    aux: dict,
    *,
    L: int,
    B: int = 90,
    H: int = 3,
    k: float = 0.0,
) -> pd.DataFrame:
    """Excess-participation form (registered 'Amihud-style divergence' phrasing):
    confirmation = participation rank MINUS |move| rank — volume beyond what the move size
    mechanically implies. k blends fade->underweight: S = D * (C' + k) (k=0 pure divergence)."""
    close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]
    ret_l = close / close.shift(L) - 1.0
    conf = conf_panel(qv, L, B)
    r_conf = conf.where(elig).rank(axis=1, pct=True)
    r_move = ret_l.abs().where(elig).rank(axis=1, pct=True)
    E = r_conf - r_move  # excess participation, [-1, +1]-ish
    C = 2.0 * (E.rank(axis=1, pct=True) - 0.5)  # re-rank to symmetric [-1, +1]
    D = np.sign(ret_l)
    S = (D * (C + k)).where(elig).fillna(0.0)
    if H > 1:
        S = S.ewm(span=H, adjust=False).mean()
    return S


def mean_rank_ic(sig: pd.DataFrame, pn: dict, aux: dict, *, predictive: bool = False) -> dict:
    """Diagnostic: mean per-candle Spearman IC of the signal vs ret_fwd over eligible names.
    Scratch-only (ret_fwd never reaches strategy code).

    predictive=False pairs sig[t] with ret_fwd[t] = open[t]->open[t+1]: CONTEMPORANEOUS
    (that window closes at the signal's info time) — kept only to document the e03/e04 bug.
    predictive=True pairs sig[t] with ret_fwd[t+1] (engine pairing: w=capped.shift(1))."""
    elig = aux["eligibility"]
    s = (sig.shift(1) if predictive else sig).where(elig)
    r = pn["ret_fwd"].where(elig)
    sr = s.rank(axis=1)
    rr = r.rank(axis=1)
    valid = sr.notna() & rr.notna()
    sr = sr.where(valid)
    rr = rr.where(valid)
    sd = sr.sub(sr.mean(axis=1), axis=0)
    rd = rr.sub(rr.mean(axis=1), axis=0)
    num = (sd * rd).sum(axis=1)
    den = np.sqrt((sd**2).sum(axis=1) * (rd**2).sum(axis=1))
    ic = (num / den.replace(0.0, np.nan)).dropna()
    ic = ic[(ic.index >= tc.TRN_IS_START) & (ic.index < tc.TRN_IS_HI)]
    return {
        "mean_ic": round(float(ic.mean()), 5),
        "ic_tstat": round(float(ic.mean() / ic.std() * np.sqrt(len(ic))), 2),
        "n_candles": int(len(ic)),
    }


def price_only_signal(pn: dict, aux: dict, *, L: int, H: int = 3, sign: int = +1) -> pd.DataFrame:
    """MOM_L (sign=+1) / REV_L (sign=-1) yardsticks — same transforms, no volume axis."""
    close, elig = pn["close"], aux["eligibility"]
    ret_l = close / close.shift(L) - 1.0
    S = (sign * cs_rank_centered(ret_l, elig)).where(elig).fillna(0.0)
    if H > 1:
        S = S.ewm(span=H, adjust=False).mean()
    return S


# ---------------------------------------------------------------- evaluation -------------------
def score(raw: pd.DataFrame, pn: dict, scoring: dict, label: str) -> dict:
    raw = te.conform_raw(raw, pn)
    net1, w1, p1 = te.net_series(raw, pn, scoring)
    m1 = te.evaluate(net1, w1, p1, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    net2, w2, p2 = te.net_series(raw, pn, scoring, cost_mult=2.0, slip_mult=2.0)
    m2 = te.evaluate(net2, w2, p2, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
    d1 = m1.to_dict()
    return {
        "label": label,
        "sharpe_1x": round(d1["sharpe"], 4),
        "sharpe_2x": round(m2.to_dict()["sharpe"], 4),
        "maxdd": round(d1["maxdd"], 4),
        "ann_turnover": round(d1["ann_turnover"], 2),
        "breadth_ls": [d1["median_names_long"], d1["median_names_short"]],
        "regimes": {k: round(v, 3) for k, v in d1["regime_sharpe"].items()},
        "mean_gross": round(d1["mean_gross"], 3),
        "mean_net": round(d1["mean_net"], 4),
        "funding_pnl": round(d1["total_funding_pnl"], 4),
        "total_cost": round(d1["total_cost"], 4),
        "total_return": round(d1["total_return"], 4),
    }


# ---------------------------------------------------------------- experiments ------------------
L_GRID = [3, 6, 9, 12, 21]


def main() -> None:
    exp = sys.argv[1]
    kw = dict(kv.split("=") for kv in sys.argv[2:])
    L = int(kw.get("L", 0)) or None
    H = int(kw.get("H", 3))
    B = int(kw.get("B", 90))

    pn, aux, scoring = te.load_is_panels()
    rows: list[dict] = []

    if exp == "e01":  # price-only yardsticks (F2 bars)
        for ell in L_GRID:
            for sgn, name in [(+1, "MOM"), (-1, "REV")]:
                s = price_only_signal(pn, aux, L=ell, H=H, sign=sgn)
                rows.append(score(s, pn, scoring, f"{name}_L{ell}_H{H}"))
    elif exp == "e02":  # core VPD, L grid
        for ell in L_GRID:
            s = vpd_signal(pn, aux, L=ell, B=B, H=H, dform="D1")
            rows.append(score(s, pn, scoring, f"VPD_D1_L{ell}_B{B}_H{H}"))
    elif exp == "e03":  # excess-participation (Amihud) form, L grid + IC diagnostics
        for ell in L_GRID:
            s = vpd_ami_signal(pn, aux, L=ell, B=B, H=H, k=0.0)
            row = score(s, pn, scoring, f"AMI_D1_L{ell}_B{B}_H{H}")
            row["ic"] = mean_rank_ic(s, pn, aux)
            rows.append(row)
        # reference ICs: raw C-form and pure momentum at L=9
        s_c = vpd_signal(pn, aux, L=9, B=B, H=H, dform="D1")
        s_m = price_only_signal(pn, aux, L=9, H=H, sign=+1)
        rows.append({"label": "IC_ref_VPD_D1_L9", "ic": mean_rank_ic(s_c, pn, aux)})
        rows.append({"label": "IC_ref_MOM_L9", "ic": mean_rank_ic(s_m, pn, aux)})
    elif exp == "e03h":  # H scan at plateau L (original e03 plan slot)
        for h in [1, 3, 6, 9]:
            s = vpd_signal(pn, aux, L=L, B=B, H=h, dform="D1")
            rows.append(score(s, pn, scoring, f"VPD_D1_L{L}_B{B}_H{h}"))
    elif exp == "e04":  # EXPLORATORY: flipped-sign forms (registered sign falsified in e02/e03)
        # climax-volume fade / thin-move continuation. Matched MOM yardstick + net-corr vs MOM.
        for ell in L_GRID:
            s_m = price_only_signal(pn, aux, L=ell, H=H, sign=+1)
            raw_m = te.conform_raw(s_m, pn)
            net_m, _, _ = te.net_series(raw_m, pn, scoring)
            for maker, name in [
                (lambda e=ell: -vpd_ami_signal(pn, aux, L=e, B=B, H=H, k=0.0), "flipAMI"),
                (lambda e=ell: -vpd_signal(pn, aux, L=e, B=B, H=H, dform="D1"), "flipC"),
            ]:
                s = maker()
                row = score(s, pn, scoring, f"{name}_D1_L{ell}_B{B}_H{H}")
                raw_s = te.conform_raw(s, pn)
                net_s, _, _ = te.net_series(raw_s, pn, scoring)
                both = pd.concat([net_s, net_m], axis=1).dropna()
                row["corr_with_MOM_net"] = round(float(both.iloc[:, 0].corr(both.iloc[:, 1])), 3)
                row["ic"] = mean_rank_ic(s, pn, aux)
                rows.append(row)
    elif exp == "e04d2":  # D2 variant + matched-H yardsticks at the selected (L, H)
        s = vpd_signal(pn, aux, L=L, B=B, H=H, dform="D2")
        rows.append(score(s, pn, scoring, f"VPD_D2_L{L}_B{B}_H{H}"))
        for sgn, name in [(+1, "MOM"), (-1, "REV")]:
            s = price_only_signal(pn, aux, L=L, H=H, sign=sgn)
            rows.append(score(s, pn, scoring, f"{name}_L{L}_H{H}"))
    elif exp == "e05":  # PREDICTIVE ICs (bug-fixed) + confirmation-weighted momentum (k-blend)
        for ell in [3, 9, 21]:
            close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]
            ret_l = close / close.shift(ell) - 1.0
            C = cs_rank_centered(conf_panel(qv, ell, B), elig)
            M = cs_rank_centered(ret_l, elig)
            for name, s in [
                (f"MOM_L{ell}", M),
                (f"C_raw_L{ell}", C),
                (f"VPD_D1_L{ell}", (np.sign(ret_l) * C)),
                (f"AMI_D1_L{ell}", vpd_ami_signal(pn, aux, L=ell, B=B, H=1)),
            ]:
                s = s.where(elig).fillna(0.0)
                rows.append(
                    {
                        "label": f"predIC_{name}",
                        "ic_pred": mean_rank_ic(s, pn, aux, predictive=True),
                        "ic_cont": mean_rank_ic(s, pn, aux, predictive=False),
                    }
                )
        # confirmation-weighted momentum: S = M * (C + k)/(1 + k), never sign-flips for k>=1
        for ell in [9, 12, 21]:
            close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]
            ret_l = close / close.shift(ell) - 1.0
            C = cs_rank_centered(conf_panel(qv, ell, B), elig)
            M = cs_rank_centered(ret_l, elig)
            for k in [1.0, 2.0]:
                G = (C + k) / (1.0 + k)
                S = (M * G).where(elig).fillna(0.0).ewm(span=H, adjust=False).mean()
                rows.append(score(S, pn, scoring, f"CWMOM_L{ell}_k{k}_B{B}_H{H}"))
    elif exp == "e06":  # CWMOM controls: pure interaction, stale-C placebo, B robustness, paired
        close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]

        def monthly(net: pd.Series) -> pd.Series:
            s = net[(net.index >= tc.TRN_IS_START) & (net.index < tc.TRN_IS_HI)]
            return s.groupby(s.index.to_period("M")).sum()

        def paired(a: pd.DataFrame, b: pd.DataFrame) -> dict:
            na, _, _ = te.net_series(te.conform_raw(a, pn), pn, scoring)
            nb, _, _ = te.net_series(te.conform_raw(b, pn), pn, scoring)
            d = (monthly(na) - monthly(nb)).dropna()
            return {
                "mean_monthly_diff": round(float(d.mean()), 5),
                "t_stat": round(float(d.mean() / d.std() * np.sqrt(len(d))), 2),
                "n_months": int(len(d)),
                "pct_months_better": round(float((d > 0).mean()), 3),
            }

        def cwmom(L_: int, B_: int, k: float, H_: int, c_shift: int = 0) -> pd.DataFrame:
            ret_l = close / close.shift(L_) - 1.0
            C = cs_rank_centered(conf_panel(qv, L_, B_), elig)
            if c_shift:
                C = C.shift(c_shift)
            M = cs_rank_centered(ret_l, elig)
            S = (M * (C + k) / (1.0 + k)).where(elig).fillna(0.0)
            return S.ewm(span=H_, adjust=False).mean() if H_ > 1 else S

        # (a) pure interaction M x C across L
        for ell in [6, 9, 12, 21]:
            ret_l = close / close.shift(ell) - 1.0
            C = cs_rank_centered(conf_panel(qv, ell, B), elig)
            M = cs_rank_centered(ret_l, elig)
            S = (M * C).where(elig).fillna(0.0).ewm(span=H, adjust=False).mean()
            rows.append(score(S, pn, scoring, f"pureMxC_L{ell}_B{B}_H{H}"))
        # (b) stale-confirmation placebo at the strongest cell (L9, k=1)
        rows.append(score(cwmom(9, 90, 1.0, 3, c_shift=21), pn, scoring, "CWMOM_L9_k1_Cstale21"))
        # (c) B robustness at L9 k1
        for b in [60, 120]:
            rows.append(score(cwmom(9, b, 1.0, 3), pn, scoring, f"CWMOM_L9_k1_B{b}_H3"))
        # (d) paired monthly tests vs matched MOM
        for ell in [9, 12]:
            m_sig = price_only_signal(pn, aux, L=ell, H=3, sign=+1)
            rows.append(
                {
                    "label": f"paired_CWMOMk1_vs_MOM_L{ell}",
                    **paired(cwmom(ell, 90, 1.0, 3), m_sig),
                }
            )
    elif exp == "e06soft":  # soft-threshold turnover diagnostic (original slot)
        for soft in [0.0, 0.2, 0.4]:
            s = vpd_signal(pn, aux, L=L, B=B, H=H, dform="D1", soft=soft)
            rows.append(score(s, pn, scoring, f"VPD_D1_L{L}_B{B}_H{H}_soft{soft}"))
    elif exp == "e07":  # CWMOM plateau completion: L6 fill + H scan at L9 (k=1, B=90)
        close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]

        def cwmom(L_: int, H_: int) -> pd.DataFrame:
            ret_l = close / close.shift(L_) - 1.0
            C = cs_rank_centered(conf_panel(qv, L_, 90), elig)
            M = cs_rank_centered(ret_l, elig)
            S = (M * (C + 1.0) / 2.0).where(elig).fillna(0.0)
            return S.ewm(span=H_, adjust=False).mean() if H_ > 1 else S

        rows.append(score(cwmom(6, 3), pn, scoring, "CWMOM_L6_k1_B90_H3"))
        for h in [1, 6, 9]:
            rows.append(score(cwmom(9, h), pn, scoring, f"CWMOM_L9_k1_B90_H{h}"))
    elif exp == "e07f":  # selected config: funding decomposition + no-funding sensitivity
        s = vpd_signal(pn, aux, L=L, B=B, H=H, dform="D1")
        rows.append(score(s, pn, scoring, f"SELECTED_VPD_D1_L{L}_B{B}_H{H}"))
        raw = te.conform_raw(s, pn)
        netf, wf, pf = te.net_series(raw, pn, scoring, apply_funding=False)
        mf = te.evaluate(netf, wf, pf, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
        rows.append({"label": "no_funding_sensitivity", "sharpe_1x": round(mf.sharpe, 4)})
    elif exp == "e08":  # H scan at L12 + final config full detail
        close, qv, elig = pn["close"], pn["quote_volume"], aux["eligibility"]

        def cwmom(L_: int, H_: int) -> pd.DataFrame:
            ret_l = close / close.shift(L_) - 1.0
            C = cs_rank_centered(conf_panel(qv, L_, 90), elig)
            M = cs_rank_centered(ret_l, elig)
            S = (M * (C + 1.0) / 2.0).where(elig).fillna(0.0)
            return S.ewm(span=H_, adjust=False).mean() if H_ > 1 else S

        scans = {}
        for h in [1, 3, 6, 9]:
            r = score(cwmom(12, h), pn, scoring, f"CWMOM_L12_k1_B90_H{h}")
            scans[h] = r["sharpe_1x"]
            rows.append(r)
        hmax = max(scans.values())
        h_sel = min(h for h, sh in scans.items() if sh >= hmax - 0.1)
        rows.append({"label": "H_rule_selection", "H_selected": h_sel, "H_scan": scans})
        s = cwmom(12, h_sel)
        rows.append(score(s, pn, scoring, f"FINAL_CWMOM_L12_k1_B90_H{h_sel}"))
        raw = te.conform_raw(s, pn)
        netf, wf, pf = te.net_series(raw, pn, scoring, apply_funding=False)
        mf = te.evaluate(netf, wf, pf, lo=tc.TRN_IS_START, hi=tc.TRN_IS_HI)
        rows.append({"label": "no_funding_sensitivity", "sharpe_1x": round(mf.sharpe, 4)})
        net1, _, _ = te.net_series(raw, pn, scoring)
        is_net = net1[(net1.index >= tc.TRN_IS_START) & (net1.index < tc.TRN_IS_HI)]
        monthly = is_net.groupby(is_net.index.to_period("M")).sum()
        rows.append(
            {
                "label": "monthly_detail",
                "n_months": int(len(monthly)),
                "pct_positive_months": round(float((monthly > 0).mean()), 3),
                "worst_month": round(float(monthly.min()), 4),
                "best_month": round(float(monthly.max()), 4),
                "monthly": {str(k): round(float(v), 4) for k, v in monthly.items()},
            }
        )
    else:
        raise SystemExit(f"unknown experiment {exp}")

    (OUT / f"{exp}.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

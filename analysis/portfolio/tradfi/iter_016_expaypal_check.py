"""Deploy-consistency check — re-run the CONFIRMED iter-016 book WITHOUT trading PAYP.

The live paper desk EXCLUDES PAYPUSDT (a broken Binance perp: the perp trades ~$14 while PayPal/PYPL
is ~$43, corr 0.19 — a perp-VENUE decoupling, verified at Phase-2b). The confirmed backtest ran on
all 69 SECTOR_MAP names (PAYP's Yahoo data is CORRECT PayPal via the PAYPUSDT->PYPL override, so the
baseline itself is uncontaminated). For deploy honesty the backtest must match the traded 68.
Two ways to "drop PAYP", and they answer DIFFERENT questions:

  (B) DEPLOY-FAITHFUL  — exactly what the live engine does: compute the 69-name book (PAYP stays in
      the XS ranking, the EW-market proxy, and the bear-gate — its data is valid PayPal),
      then ZERO PAYP's final leg (no renormalize; the same vol-target `scale` the 69-name book set).
      Isolates the pure "don't trade PayPal" P&L. THIS is the number that justifies the live desk.
  (A) UNIVERSE-RECOMPUTE — remove PAYP from the universe ENTIRELY, so the ranking / market proxy /
      bear-gate all recompute on 68 names. A stronger robustness stress (composition sensitivity),
      but NOT what the desk does — a broad reshuffle, not the leg's own contribution.

IS-only throughout (every Sharpe is ct.msharpe over LO0..OOS_CUTOFF; OOS stays hidden). A self-check
asserts the no-drop path reproduces the confirmed +0.729 baseline bit-for-bit.

Run: uv run python analysis/portfolio/tradfi/iter_016_expaypal_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_011_mom_ltr as i11  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import iter_016_bear_gated_tsmom as champ  # noqa: E402  — the confirmed baseline
import universe_tradfi as ut  # noqa: E402

EXCLUDE = "PAYPUSDT"
D, F = champ.DELTA, champ.FREQ


def _universe(exclude: set[str]) -> list[str]:
    base = ct._ROOT / "data"
    return sorted(
        p.parent.name
        for p in base.glob("*/1d.csv")
        if p.parent.name in ut.SECTOR_MAP and p.parent.name not in exclude
    )


def _panel(exclude: set[str]) -> dict:
    return ct.panels(ct.load_tradfi(_universe(exclude), None))


def _net0(w: pd.DataFrame, ret_fwd: pd.DataFrame, cost_mult: float) -> pd.Series:
    """Pre-scale leak-safe net for a banded weight panel at cost = cost_mult*COST_SIDE (0/1/2)."""
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * ct.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return pnl - cost


def _metrics_from_w(w: pd.DataFrame, pn: dict, scale: pd.Series, svix: pd.Series, mkt) -> dict:
    """Deployed IS metric bundle for a banded weight panel ``w`` under a GIVEN (69-name) vol-target
    ``scale`` + VIX ``svix`` — zeroing a leg does NOT recompute the desk's scale (matches live)."""
    ret_fwd = pn["ret_fwd"]
    n0, n1, n2 = (_net0(w, ret_fwd, c) for c in (0.0, 1.0, 2.0))
    d1x = (n1 * scale * svix).dropna()
    d2x = (n2 * scale * svix).dropna()
    dg = (n0 * scale * svix).dropna()
    npos, nyr = i11.n_pos_years(d1x)
    return {
        "net1x": ct.msharpe(d1x, ct.LO0, ct.OOS_CUTOFF),
        "net2x": ct.msharpe(d2x, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(dg, ct.LO0, ct.OOS_CUTOFF),
        "beta": i13.net_beta((n1 * scale).dropna(), mkt),  # VIX-off 1x, iter-015 convention
        "nlong": i13.net_long_fraction(w),
        "npos": npos,
        "nyr": nyr,
        "d1x": d1x,
    }


def _deploy_faithful() -> tuple[dict, dict]:
    """(B) 69-name book, PAYP's leg zeroed at fill (no renormalize, 69-name scale kept)."""
    pn = _panel(set())
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)  # 69-name proxy (PAYP still in it — valid PayPal)
    svix = i8.vix_scale(i8.load_vix_close(ret_fwd.index, None)).reindex(ret_fwd.index).fillna(1.0)
    raw = champ.bear_gated_combined_raw(pn)
    w = i15.banded_book_freq(raw, D, F)  # 69-name banded unit-gross book
    scale = ct.vol_target_scale(_net0(w, ret_fwd, 1.0))  # 69-name vol-target scale (kept fixed)

    m_full = _metrics_from_w(w, pn, scale, svix, mkt)  # self-check: must == confirmed baseline
    w_z = w.copy()
    if EXCLUDE in w_z.columns:
        w_z[EXCLUDE] = 0.0  # drop PAYP's leg only (no renormalize) — exactly the live engine
    m_drop = _metrics_from_w(w_z, pn, scale, svix, mkt)
    return m_full, m_drop


def _recompute(exclude: set[str]) -> dict:
    """(A) full recompute on the reduced universe (ranking + market + gate all on 68)."""
    pn = _panel(exclude)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)
    svix = i8.vix_scale(i8.load_vix_close(ret_fwd.index, None))
    return champ.deployed_metrics(champ.bear_gated_combined_raw(pn), ret_fwd, svix, mkt)


def _maxdd_is(d1x: pd.Series) -> float:
    d = ct.is_only(d1x)
    eq = (1.0 + d).cumprod()
    return float((eq / eq.cummax() - 1.0).min()) * 100.0


def _worst(d1x: pd.Series) -> tuple[int, float, str, float]:
    yt = i11.year_table(d1x)
    wy = min(yt, key=lambda y: yt[y][1])
    d = ct.is_only(d1x)
    mo = d.groupby(d.index.to_period("M")).sum()
    wm = mo.idxmin()
    return wy, yt[wy][1], str(wm), float(mo.loc[wm]) * 100.0


def _row(lab: str, m: dict) -> str:
    return (
        f"      {lab:<24} {m['net1x']:>+7.3f} {m['net2x']:>+7.3f} {m['gross']:>+7.3f} "
        f"{m['beta']:>+7.3f} {m['nlong']:>+7.3f} {m['npos']:>4}/{m['nyr']}"
    )


def _drow(lab: str, d: dict) -> str:
    return (
        f"      {lab:<24} {d['net1x']:>+7.3f} {d['net2x']:>+7.3f} {d['gross']:>+7.3f} "
        f"{d['beta']:>+7.3f} {d['nlong']:>+7.3f}"
    )


def main() -> None:
    m_full, m_drop_b = _deploy_faithful()
    m_re_a = _recompute({EXCLUDE})

    print("=" * 96)
    print("iter-016 DEPLOY-CONSISTENCY — confirmed baseline vs NOT trading PAYP (IS-only)")
    print("=" * 96)
    ok = abs(m_full["net1x"] - 0.729) < 5e-3 and abs(m_full["gross"] - 0.875) < 5e-3
    print(f"  self-check (no-drop == confirmed +0.729/+0.875): {'PASS' if ok else 'FAIL'}\n")

    print(
        f"      {'config':<24} {'net@1x':>7} {'net@2x':>7} {'gross':>7} "
        f"{'net-b':>7} {'nlong':>7} {'+yrs':>7}"
    )
    print(_row("69-name (confirmed base)", m_full))
    print(_row("(B) drop PAYP leg [LIVE]", m_drop_b))
    print(_row("(A) recompute on 68", m_re_a))
    keys = ("net1x", "net2x", "gross", "beta", "nlong")
    d_b = {k: m_drop_b[k] - m_full[k] for k in keys}
    d_a = {k: m_re_a[k] - m_full[k] for k in keys}
    print(_drow("delta (B) — DEPLOY #", d_b))
    print(_drow("delta (A) — composition", d_a))

    for lab, m in (("69 base", m_full), ("(B) drop-leg", m_drop_b), ("(A) recompute", m_re_a)):
        wy, wyr, wm, wmr = _worst(m["d1x"])
        print(
            f"\n  {lab:<14} maxDD(IS) {_maxdd_is(m['d1x']):>+6.1f}%   "
            f"worst-yr {wy} {wyr:>+5.1f}%   worst-mo {wm} {wmr:>+6.2f}%"
        )

    y_f, y_b = i11.year_table(m_full["d1x"]), i11.year_table(m_drop_b["d1x"])
    print("\n  PER-YEAR net return% (Sharpe) IS — 69 base -> (B) drop-PAYP-leg [deployed]:")
    for yr in sorted(y_b):
        star = "  <-- differs" if abs(y_f[yr][1] - y_b[yr][1]) > 0.05 else ""
        print(
            f"      {yr}  {y_f[yr][1]:>+6.1f}% ({y_f[yr][0]:>+5.2f}) -> "
            f"{y_b[yr][1]:>+6.1f}% ({y_b[yr][0]:>+5.2f}){star}"
        )

    keep_b = abs(d_b["net1x"]) <= 0.03 and m_drop_b["net1x"] >= 0.50 and m_drop_b["beta"] <= 0.20
    tag = "BENIGN — baseline robust, live universe OK" if keep_b else "MATERIAL — investigate"
    print(
        f"\n  VERDICT (B, the live desk): dropping {EXCLUDE}'s leg is {tag} "
        f"(net@1x {m_full['net1x']:+.3f} -> {m_drop_b['net1x']:+.3f}, d={d_b['net1x']:+.3f}; "
        f"clears >=0.50, beta {m_drop_b['beta']:+.3f})"
    )


if __name__ == "__main__":
    main()

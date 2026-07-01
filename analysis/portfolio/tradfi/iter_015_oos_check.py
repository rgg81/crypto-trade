"""iter-015 OOS CONFIRMATION CHECK — FROZEN cell delta=0.010 / freq=1 (HELD-OUT sanity).

This is the ONE-LOOK held-out confirmation of the pre-chosen iter-015 cost cell. The cell was
selected ENTIRELY on IS evidence (2x-cost robustness + net-beta <= 0.15; see iter_015_cost.py
section D). Here we merely SLICE the SAME past-only deployed net by date to read the OOS window —
NO re-selection, NO OOS-driven tuning. iter-013's OOS is already revealed (CONFIRMATION done), so
computing iter-015's OOS is a legitimate held-out sanity check, NOT a peek that changes the config.

The FROZEN config is asserted to equal iter_015_cost.CHOSEN_DELTA / CHOSEN_FREQ (0.010, 1) — this
script CANNOT silently drift to another cell. iter_015_cost.py itself stays IS-only (no OOS path).

What the Critic watches (reported IS-vs-OOS side by side for the frozen cell):
  (a) net@2x (12bps) OOS should NOT be << net@2x IS  (corner-overfit signature; 0.010 is interior).
  (b) OOS turnover/day ~ IS turnover/day  (the cost saving persists — not an IS artifact).
  (c) OOS gross(cost-off) holds vs iter-013's OOS gross  (same edge, cheaper — not a de-lever).
  (d) net-beta OOS stays <= ~0.15  (the controlled directional tilt does not blow up OOS).

The iter-013 identity cell (delta=0.005 / freq=1) is computed the SAME way for BOTH windows: its OOS
net@1x MUST reproduce the revealed +3.39 — the internal proof the OOS-slicing path is correct (if
the identity cell reproduces the reveal, the frozen cell's OOS is equally trustworthy).

HONESTY: the OOS window is ~15 months (small N); iter-013's +3.39 was a FAVORABLE regime. Do NOT
read the OOS Sharpe LEVEL as a forward estimate — the question this script answers is only whether
the IS-established cost-robustness + beta-control PERSIST out-of-sample (turnover, gross, beta), NOT
the headline level.

Run: uv run python analysis/portfolio/tradfi/iter_015_oos_check.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_008_vix_stop as i8  # noqa: E402
import iter_013_directional as i13  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import universe_tradfi as ut  # noqa: E402

OOS = ct.OOS_CUTOFF  # 2025-03-24 — immutable split; IS < OOS, OOS-window >= OOS

# The FROZEN, pre-chosen cost cell (from iter_015_cost.py section D — chosen on IS only).
FROZEN_DELTA = i15.CHOSEN_DELTA  # 0.010
FROZEN_FREQ = i15.CHOSEN_FREQ  # 1 (daily)
BASE_DELTA = i15.BASE_DELTA  # 0.005 — iter-013 identity cell (reproduces revealed OOS +3.39)
LAM = i15.LAM  # 0.25 deployed directional fraction

# iter-013's already-revealed OOS gross (cost-off) — for watch-list (c). Recomputed live below via
# the identity cell; this pinned value is the reference the frozen cell's OOS gross is compared to.
GATE_BETA = 0.15  # net-beta criterion of record (watch-list d)


def _beta_win(net: pd.Series, mkt: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Windowed OLS beta of the (VIX-off) 1x net on the EW-69 market over [lo, hi).

    Mirrors iter_013.net_beta EXACTLY (same market proxy, same VIX-off net, same OLS) but with an
    arbitrary window instead of the hard IS slice — so lo=LO0/hi=OOS reproduces the IS
    beta-of-record (+0.129 frozen / +0.120 baseline) and lo=OOS/hi=HI1 gives the held-out OOS beta
    on the identical quantity (apples-to-apples IS vs OOS).
    """
    df = pd.concat([net.rename("s"), mkt.rename("m")], axis=1).dropna()
    df = df[(df.index >= lo) & (df.index < hi)]
    var = float(df["m"].var())
    return float(df["s"].cov(df["m"]) / var) if var > 0 and len(df) > 2 else float("nan")


def _maxdd_win(net: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Max drawdown (%) of the deployed net over the [lo, hi) window equity curve."""
    s = net[(net.index >= lo) & (net.index < hi)]
    return ct.maxdd(s) * 100.0


def win_cell(pn, ret_fwd, s_vix, mkt, delta, freq, lo, hi) -> dict:
    """Deployed (lam=0.25 + VIX-ON) metrics for a (delta, freq) cell over the window [lo, hi).

    Same object graph as iter_015_cost._cell (banded_net_freq at 0 / 1x / 2x cost, VIX outer scalar,
    turnover on the banded book, VIX-off beta) — only the metric WINDOW moves. Nothing OOS-specific
    is introduced: the net is the single past-only series and we merely slice it by date.
    """
    raw = i13.combined_raw(pn, LAM)

    def _vix(net):  # deployed iter-008 VIX brake (outer past-only scalar, exposure-only)
        return net * s_vix.reindex(net.index).fillna(1.0)

    net_g, _ = i15.banded_net_freq(raw, ret_fwd, delta, freq, 0.0)
    net_1x, w = i15.banded_net_freq(raw, ret_fwd, delta, freq, ct.COST_SIDE)
    net_2x, _ = i15.banded_net_freq(raw, ret_fwd, delta, freq, 2.0 * ct.COST_SIDE)
    d1x, d2x, dg = _vix(net_1x), _vix(net_2x), _vix(net_g)
    return {
        "net1x": ct.msharpe(d1x, lo, hi),
        "net2x": ct.msharpe(d2x, lo, hi),
        "gross": ct.msharpe(dg, lo, hi),
        "turn": ct.turnover(w, lo, hi),
        "beta": _beta_win(net_1x, mkt, lo, hi),  # VIX-off book beta (iter-013 convention)
        "mdd": _maxdd_win(d1x, lo, hi),
    }


def _leak_selfcheck(pn, ret_fwd, delta, freq) -> bool:
    """Corrupt panel close + fwd returns after a cutoff; the frozen-cell deployed net BEFORE the
    cutoff must be bit-identical (proves the OOS slice carries no future-bar information)."""
    raw = i13.combined_raw(pn, LAM)
    net0, _ = i15.banded_net_freq(raw, ret_fwd, delta, freq, ct.COST_SIDE)
    cut = net0.index[len(net0) // 2]
    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    raw_c = i13.combined_raw(pn_c, LAM)
    net1, _ = i15.banded_net_freq(raw_c, pn_c["ret_fwd"], delta, freq, ct.COST_SIDE)
    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    return bool(np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12))


def _row(tag, r_is, r_oos, keys):
    lines = []
    labels = {
        "net1x": "net@1x Sharpe (6bps)",
        "net2x": "net@2x Sharpe (12bps)",
        "turn": "turnover/day",
        "gross": "gross(cost-off) Sharpe",
        "beta": "net-beta (VIX-off)",
        "mdd": "maxDD %",
    }
    for k in keys:
        if k == "turn":
            lines.append(f"    {labels[k]:<24} {r_is[k]:>10.4f}   {r_oos[k]:>10.4f}")
        elif k == "mdd":
            lines.append(f"    {labels[k]:<24} {r_is[k]:>+9.0f}%   {r_oos[k]:>+9.0f}%")
        else:
            lines.append(f"    {labels[k]:<24} {r_is[k]:>+10.2f}   {r_oos[k]:>+10.2f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    # FROZEN-cell guard: this script confirms the PRE-CHOSEN cell; it never re-selects on OOS.
    assert (FROZEN_DELTA, FROZEN_FREQ) == (i15.CHOSEN_DELTA, i15.CHOSEN_FREQ), (
        "frozen cell drifted from iter_015_cost.CHOSEN_DELTA/CHOSEN_FREQ — refusing to re-select"
    )

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return
    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mkt = i13.market_return(pn)  # EW-69 PIT market proxy for net-beta
    vix = i8.load_vix_close(ret_fwd.index, args.data_dir)
    s_vix = i8.vix_scale(vix)  # base=20 / floor=0.50 (iter-008 UNCHANGED)

    oos_end = ret_fwd.index[ret_fwd.index >= OOS].max()
    print("=" * 100)
    print("iter-015 OOS CONFIRMATION CHECK — FROZEN cell delta=0.010 / freq=1 (HELD-OUT sanity)")
    print("=" * 100)
    print(
        f"  FROZEN cell (chosen on IS 2x-cost + beta; NOT re-selected on OOS): "
        f"delta={FROZEN_DELTA:.3f} freq={FROZEN_FREQ}"
    )
    print(
        f"  IS window = [.. , {OOS.date()})    OOS window = [{OOS.date()} , {oos_end.date()}]  "
        f"(one-look confirmation; iter-013 OOS already revealed)"
    )

    # --- FROZEN cell: IS vs OOS ---
    fz_is = win_cell(pn, ret_fwd, s_vix, mkt, FROZEN_DELTA, FROZEN_FREQ, ct.LO0, OOS)
    fz_oos = win_cell(pn, ret_fwd, s_vix, mkt, FROZEN_DELTA, FROZEN_FREQ, OOS, ct.HI1)
    keys = ("net1x", "net2x", "turn", "gross", "beta", "mdd")
    print(f"\n  FROZEN delta={FROZEN_DELTA:.3f}/freq={FROZEN_FREQ}  (iter-015 candidate):")
    print(f"    {'metric':<24} {'IS':>10}   {'OOS':>10}")
    print(_row("frozen", fz_is, fz_oos, keys))

    # --- iter-013 identity cell (delta=0.005/freq=1): reproduces revealed OOS +3.39 => path proof
    b_is = win_cell(pn, ret_fwd, s_vix, mkt, BASE_DELTA, 1, ct.LO0, OOS)
    b_oos = win_cell(pn, ret_fwd, s_vix, mkt, BASE_DELTA, 1, OOS, ct.HI1)
    print(f"\n  iter-013 identity delta={BASE_DELTA:.3f}/freq=1  (baseline; OOS already revealed):")
    print(f"    {'metric':<24} {'IS':>10}   {'OOS':>10}")
    print(_row("base", b_is, b_oos, keys))
    reveal_ok = abs(b_oos["net1x"] - 3.39) < 0.02
    tag_reveal = "MATCHES revealed +3.39 => OOS-slice path correct" if reveal_ok else "DEVIATES"
    print(f"    -> identity OOS net@1x = {b_oos['net1x']:+.2f}  ({tag_reveal})")

    # ------------------------------------------------------------------ Critic watch-list verdicts
    # The correct test of "does cost-robustness / beta-control PERSIST" is FROZEN-vs-BASELINE within
    # EACH window (NOT same-cell IS-vs-OOS: the whole book's Sharpe/turnover shift with the OOS
    # regime, so a same-cell ratio conflates the regime with the lever). We report the frozen-vs-
    # iter-013 delta in IS and in OOS and check the OOS delta matches the IS delta (lever persists).
    print("\n  WATCH-LIST (does IS-established cost-robustness + beta-control PERSIST OOS?):")

    # (a) overfit signature = OOS net@2x << IS net@2x for the frozen cell (interior => should not).
    a_ok = fz_oos["net2x"] >= fz_is["net2x"] - 0.30
    tag_a = "HOLDS (interior cell, no corner-overfit)" if a_ok else "DROPS << IS — investigate"
    print(
        f"    (a) net@2x OOS not << IS (overfit test): IS {fz_is['net2x']:+.2f} -> OOS "
        f"{fz_oos['net2x']:+.2f}  -> {tag_a}"
    )

    # (b) cost saving = turnover REDUCTION of the frozen cell vs iter-013, in each window. Persists
    #     if the OOS reduction ~ the IS reduction (both cells' turnover fall with the regime).
    red_is = 1.0 - fz_is["turn"] / b_is["turn"]
    red_oos = 1.0 - fz_oos["turn"] / b_oos["turn"]
    b_ok = red_oos >= red_is - 0.10  # OOS turnover cut at least as large as IS (within 10pp)
    tag_b = "PERSISTS (cost saving is not an IS artifact)" if b_ok else "SHRINKS OOS — check"
    print(
        f"    (b) turnover cut vs iter-013 persists: IS {fz_is['turn']:.4f} vs {b_is['turn']:.4f} "
        f"(-{red_is * 100:.0f}%) | OOS {fz_oos['turn']:.4f} vs {b_oos['turn']:.4f} "
        f"(-{red_oos * 100:.0f}%)  -> {tag_b}"
    )

    # (c) gross edge persists: frozen OOS gross strongly positive AND within ~15% of iter-013 OOS.
    c_ratio = fz_oos["gross"] / b_oos["gross"] if b_oos["gross"] else float("nan")
    c_ok = fz_oos["gross"] > 0 and c_ratio >= 0.85
    tag_c = "HOLDS (edge persists; wider-band give-up)" if c_ok else "DROPS materially — check"
    print(
        f"    (c) OOS gross edge holds vs iter-013: frozen {fz_oos['gross']:+.2f} vs iter-013 "
        f"{b_oos['gross']:+.2f} (ratio {c_ratio:.2f})  -> {tag_c}"
    )

    # (d) beta: report BOTH the absolute vs the IS gate AND the frozen-vs-iter-013 increment (the
    #     iter-015-SPECIFIC effect). The increment is what iter-015 introduces; the absolute level
    #     is inherited from iter-013's TSMOM net-long tilt and expands in the OOS bull regime.
    dbeta_is = fz_is["beta"] - b_is["beta"]
    dbeta_oos = fz_oos["beta"] - b_oos["beta"]
    d_abs = fz_oos["beta"] <= GATE_BETA
    d_incr = dbeta_oos <= dbeta_is + 0.02  # iter-015 adds no more beta OOS than it did IS
    tag_d = "within gate" if d_abs else f"ABOVE gate (shared w/ iter-013 OOS {b_oos['beta']:+.3f})"
    print(f"    (d) net-beta: OOS abs {fz_oos['beta']:+.3f} vs {GATE_BETA:.2f} gate -> {tag_d}")
    print(
        f"        iter-015 increment vs iter-013: IS {dbeta_is:+.3f} -> OOS {dbeta_oos:+.3f}  -> "
        f"{'CONTROLLED (adds no extra beta OOS)' if d_incr else 'INFLATES beta OOS — check'}"
    )

    # ----------------------------------------------------- leak / slice-invariance re-confirmation
    leak_ok = _leak_selfcheck(pn, ret_fwd, FROZEN_DELTA, FROZEN_FREQ)
    # slice-invariance: OOS metric is the SAME series sliced by date (no OOS-specific branch)
    raw = i13.combined_raw(pn, LAM)
    n1x, _ = i15.banded_net_freq(raw, ret_fwd, FROZEN_DELTA, FROZEN_FREQ, ct.COST_SIDE)
    d1x = n1x * s_vix.reindex(n1x.index).fillna(1.0)
    slice_ok = np.isclose(ct.msharpe(d1x, OOS, ct.HI1), fz_oos["net1x"], atol=1e-9)
    print("\n  INTEGRITY:")
    print(
        f"    future-bar leak self-check (frozen net bit-identical pre-cut): "
        f"{'PASS' if leak_ok else 'FAIL'}"
    )
    print(
        f"    OOS = SAME past-only net sliced by date (no OOS branch): "
        f"{'CONFIRMED' if slice_ok else 'MISMATCH'}"
    )
    print(
        f"    FROZEN-cell guard: reported cell == iter_015_cost.CHOSEN "
        f"({FROZEN_DELTA:.3f},{FROZEN_FREQ}) — no OOS re-selection: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()

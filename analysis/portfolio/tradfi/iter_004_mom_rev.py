"""iter-004 — add a within-sector SHORT-TERM REVERSAL sleeve to the momentum book.

ONE change vs iter-003: add a SECOND signal sleeve (within-sector ~1-month reversal), combine it
with the iter-002 within-sector momentum sleeve into a single raw book, then run that combined book
through the EXACT iter-003 hysteresis band (delta=0.005) + leak-safe net_from_raw. The band, the
cost model, the vol-target and the OOS-hidden accounting are all UNCHANGED — only the signal that
feeds the band is now two sleeves instead of one.

Why reversal: short-term (1-month) reversal is the classic complement to 12-1m momentum. Momentum
buys recent winners; reversal buys recent losers. The two factors are near-orthogonal and reversal
tends to earn in CHOP — exactly the iter-003 book's weakest regime (chop -0.10). The hope is the
combined book is MORE all-weather (positive in >=2 of 3 regimes) without losing the bull edge.

The two sector-neutralized sleeves (each per-sector-demeaned -> dollar-neutral by construction):

    mom_raw = sector_neutralize( (close.shift(21)/close.shift(252) - 1) / rvol63, MAP )   # iter-002
    rev_raw = sector_neutralize( -(close/close.shift(21) - 1)          / rvol63, MAP )     # NEW

`mom_raw` is reused BYTE-FOR-BYTE from iter-002 (`i2.sector_rel_raw`) so the mom-only standalone
reproduces iter-003 (+0.16) exactly. `rev_raw` NEGATES the recent within-sector return (long recent
losers / short recent winners), inverse-vol scaled by the SAME trailing-63 realized vol, then
per-sector demeaned. Both are past-only (shift(21)/shift(252) + a trailing rvol) — no forward leak.

Two NON-TUNABLE combiners are tested (report both; pick the IS-robust one; never OOS-tuned):

  (a) EQUAL-WEIGHT      : raw = 0.5*mom_n + 0.5*rev_n  (each sleeve gross-normed to unit gross first
                          so neither sleeve dominates by sheer scale), then band.
  (b) INVERSE-VOL PARITY: raw = w_mom*mom_n + w_rev*rev_n, with w_i,t = (1/rv_i,t)/Σ(1/rv_j,t) and
                          rv_i,t = sleeve_net_i.rolling(VOL_WIN).std().shift(1) (PAST-ONLY trailing
                          realized net-return vol of each standalone sleeve). The leak-safe combiner
                          is ported from metals iter_014_riskparity: a higher-vol sleeve gets a
                          SMALLER weight; the weights are a risk-determined simplex, no free knob.

Both combined panels stay sector-neutral (a linear combo of per-sector-zero-sum panels is itself
per-sector-zero-sum), so the book is dollar-neutral before the band. After the band the same tiny
renorm drift as iter-003 appears (reported as the sector-neutrality residual).

OOS stays HIDDEN (perf_line reveal_oos=False) unless --confirm (CONFIRMATION only). Everything is
IS-only. The combined banded build is covered by a future-bar leak test for BOTH combiners.
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
import iter_002_sector_rel as i2  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

# Inverse-vol parity uses the SAME trailing-vol window the rest of the core uses (3m realized).
RP_VOL_WIN = ct.VOL_WIN  # 63 trading days (~3m); the ONE structural knob, == iter-002 rvol window
CHOSEN_DELTA = i3.CHOSEN_DELTA  # 0.005, inherited from iter-003 UNCHANGED


def mom_raw(pn) -> pd.DataFrame:
    """iter-002 within-sector 12m-1m momentum sleeve, reused byte-for-byte (mom-only==iter-003)."""
    return i2.sector_rel_raw(pn)


def rev_raw(pn) -> pd.DataFrame:
    """Within-sector SHORT-TERM (1-month) reversal sleeve, inverse-vol scaled, sector-neutralized.

    rev = sector_neutralize( -(close/close.shift(21) - 1) / rvol63, SECTOR_MAP ). The NEGATED recent
    1-month return makes recent within-sector LOSERS long / recent WINNERS short. rvol63 is the same
    trailing-63 realized vol the momentum sleeve uses (close.pct_change().rolling(63).std()) — all
    past, no forward leak. Per-sector demeaning forces each sector net-zero (singletons -> 0).
    """
    close = pn["close"]
    rev = -(close / close.shift(21) - 1.0)  # negated 1-month return, all past
    rvol = close.pct_change().rolling(ct.VOL_WIN).std()
    raw = rev / rvol
    return nz.sector_neutralize(raw, ut.SECTOR_MAP)


def _gross_norm(raw: pd.DataFrame) -> pd.DataFrame:
    """Gross-normalize each row to unit gross (Σ|w|=1), or 0 on warm-up/empty rows. Leak-free."""
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(gross, axis=0).fillna(0.0)


def _sleeve_net_pre(raw: pd.DataFrame, ret_fwd: pd.DataFrame) -> pd.Series:
    """Leak-safe standalone sleeve net BEFORE the portfolio vol-target (for inverse-vol weighting).

    gross-normalize -> .shift(1) lag -> Σ w·ret_fwd − taker cost on |Δw|. This is net_from_raw minus
    the vol_target wrapper: the portfolio vol-target is applied ONCE to the COMBINED book, so the
    sleeve-level vol used for inverse-vol weighting must be measured on the raw (un-vol-targeted)
    sleeve return — else both sleeves get normalized to the same target vol and inverse-vol parity
    collapses to a trivial ~50/50. Strictly past-only: w is .shift(1)-lagged onto ret_fwd.
    """
    w = _gross_norm(raw).shift(1)
    pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
    cost = ct.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return (pnl - cost).dropna()


def invvol_weights(
    mraw: pd.DataFrame, rraw: pd.DataFrame, ret_fwd: pd.DataFrame, vol_win: int = RP_VOL_WIN
) -> tuple[pd.Series, pd.Series]:
    """Past-only inverse-vol sleeve weights (w_mom, w_rev), each a per-date scalar summing to 1.

    rv_i,t = sleeve_net_i.rolling(vol_win).std().shift(1) (PAST-ONLY — the .shift(1) keeps the
    weight applied at bar t using only vol estimated through t−1). w_i,t = (1/rv_i,t)/Σ_j(1/rv_j,t).
    Aligned to the union index; warm-up rows (any rv NaN) yield NaN weights -> the combiner zeroes
    that row.
    """
    m_net = _sleeve_net_pre(mraw, ret_fwd)
    r_net = _sleeve_net_pre(rraw, ret_fwd)
    idx = m_net.index.union(r_net.index)
    rv_m = m_net.reindex(idx).rolling(vol_win).std().shift(1)
    rv_r = r_net.reindex(idx).rolling(vol_win).std().shift(1)
    inv_m = 1.0 / rv_m.replace(0.0, np.nan)
    inv_r = 1.0 / rv_r.replace(0.0, np.nan)
    denom = inv_m + inv_r  # NaN if either sleeve's vol is not yet estimable
    return inv_m / denom, inv_r / denom


def combine_equal(mraw: pd.DataFrame, rraw: pd.DataFrame) -> pd.DataFrame:
    """(a) EQUAL-WEIGHT: 0.5*mom_n + 0.5*rev_n, each sleeve gross-normed to unit gross first."""
    return 0.5 * _gross_norm(mraw) + 0.5 * _gross_norm(rraw)


def combine_invvol(
    mraw: pd.DataFrame, rraw: pd.DataFrame, ret_fwd: pd.DataFrame, vol_win: int = RP_VOL_WIN
) -> pd.DataFrame:
    """(b) INVERSE-VOL PARITY: w_mom*mom_n + w_rev*rev_n with past-only inverse-vol weights."""
    w_mom, w_rev = invvol_weights(mraw, rraw, ret_fwd, vol_win)
    mom_n = _gross_norm(mraw)
    rev_n = _gross_norm(rraw)
    idx = mom_n.index.union(rev_n.index)
    combined = (
        mom_n.reindex(idx)
        .mul(w_mom, axis=0)
        .add(rev_n.reindex(idx).mul(w_rev, axis=0), fill_value=0.0)
    )
    return combined.fillna(0.0)  # warm-up rows (NaN weights) -> zero book


def _report_build(label, raw, ret_fwd, delta, base_turn, *, reveal_oos=False):
    """Print the standard IS-only line for a banded build + return its (net, w, metrics) bundle."""
    net, w = i3.banded_net(raw, ret_fwd, delta)
    gnet, _ = i3.banded_net(raw, ret_fwd, delta, cost_on=False)
    sh_net = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    sh_gross = ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF)
    turn = ct.turnover(w, ct.LO0, ct.OOS_CUTOFF)
    reg = ct.regime_sharpe(ct.is_only(net))
    n_pos = sum(1 for v in reg.values() if v > 0)
    tpc = "" if base_turn is None else f"  (turn {(turn / base_turn - 1) * 100:+.0f}% vs mom-only)"
    print(ct.perf_line(label, net, reveal_oos=reveal_oos))
    print(
        f"      gross={sh_gross:+.2f} net={sh_net:+.2f} drag={sh_gross - sh_net:+.2f}  "
        f"turn/day={turn:.4f}{tpc}"
    )
    print(
        f"      regimes(IS): bull={reg['bull']:+.2f} bear={reg['bear']:+.2f} "
        f"chop={reg['chop']:+.2f}  ({n_pos}/3 positive)"
    )
    return {
        "net": net,
        "w": w,
        "sh_net": sh_net,
        "sh_gross": sh_gross,
        "turn": turn,
        "reg": reg,
        "n_pos": n_pos,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", type=float, default=CHOSEN_DELTA, help="hysteresis band (iter-003)")
    ap.add_argument("--confirm", action="store_true", help="reveal OOS (CONFIRMATION only)")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    d = args.delta

    base = Path(args.data_dir) if args.data_dir else ct._ROOT / "data"
    syms = sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)
    coins = ct.load_tradfi(syms, args.data_dir)
    if not coins:
        print("No ingested tradfi data found. Run ingest_dukascopy_stocks.py first.")
        return

    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]
    mraw = mom_raw(pn)
    rraw = rev_raw(pn)

    print("=" * 96)
    print("iter-004 — within-sector REVERSAL sleeve + momentum, iter-003 hysteresis band (IS-only)")
    print("=" * 96)
    print(
        f"  band delta={d:.3f} (iter-003 UNCHANGED); inverse-vol window={RP_VOL_WIN} (== rvol63)\n"
    )

    # --- IDENTITY: mom-only banded must reproduce iter-003 (+0.16) bit-for-bit ---
    net_mom_band, _ = i3.banded_net(mraw, ret_fwd, d)
    net_i3, _ = i3.banded_net(i2.sector_rel_raw(pn), ret_fwd, d)
    ident = bool(np.allclose(net_mom_band.to_numpy(), net_i3.to_numpy()))
    print(f"  IDENTITY mom-only banded == iter-003: {'PASS' if ident else 'FAIL'}\n")

    # --- (1) STANDALONE sleeves (each through the SAME iter-003 band) ---
    print(f"  --- STANDALONE sleeves (each banded delta={d:.3f}) ---")
    mom = _report_build("mom-only (=iter-003)", mraw, ret_fwd, d, None, reveal_oos=args.confirm)
    base_turn = mom["turn"]
    rev = _report_build("rev-only", rraw, ret_fwd, d, base_turn, reveal_oos=args.confirm)

    # mom<->rev standalone net-return correlation (IS) — low/negative = good diversification
    mom_is = ct.is_only(mom["net"])
    rev_is = ct.is_only(rev["net"])
    common = mom_is.index.intersection(rev_is.index)
    corr = float(np.corrcoef(mom_is.loc[common], rev_is.loc[common])[0, 1])
    print(
        f"\n  mom<->rev standalone net-return correlation (IS): {corr:+.2f}  (<=0 = diversifying)"
    )

    # --- (2) COMBINERS (a) equal-weight and (b) inverse-vol parity ---
    print(f"\n  --- COMBINERS (mom + rev, banded delta={d:.3f}) ---")
    raw_eq = combine_equal(mraw, rraw)
    raw_iv = combine_invvol(mraw, rraw, ret_fwd, RP_VOL_WIN)
    comb_a = _report_build(
        "(a) equal-weight", raw_eq, ret_fwd, d, base_turn, reveal_oos=args.confirm
    )
    comb_b = _report_build(
        "(b) inv-vol parity", raw_iv, ret_fwd, d, base_turn, reveal_oos=args.confirm
    )

    # inverse-vol weight timeline (IS): is the split sensible / not a corner?
    w_mom, _ = invvol_weights(mraw, rraw, ret_fwd, RP_VOL_WIN)
    w_mom_is = w_mom[w_mom.index < ct.OOS_CUTOFF].dropna()
    print(
        f"      inv-vol sleeve weight (IS mean): w_mom={w_mom_is.mean():.2f} "
        f"w_rev={1 - w_mom_is.mean():.2f}  range w_mom=[{w_mom_is.min():.2f},{w_mom_is.max():.2f}]"
    )

    # --- (3) PICK the IS-robust combiner: prefer all-weather (more positive regimes), then Sharpe
    # Pure IS selection — NEVER OOS-tuned. Tie-break order: (n_positive_regimes, IS net Sharpe).
    pick_a = (comb_a["n_pos"], round(comb_a["sh_net"], 4))
    pick_b = (comb_b["n_pos"], round(comb_b["sh_net"], 4))
    chosen, tag = (
        (comb_a, "(a) equal-weight") if pick_a >= pick_b else (comb_b, "(b) inv-vol parity")
    )
    print(f"\n  --- CHOSEN combiner: {tag} (IS-robust: regimes-positive, then Sharpe) ---")
    print(ct.perf_line(f"CHOSEN {tag}", chosen["net"], reveal_oos=args.confirm))
    reg = chosen["reg"]
    print(
        f"      net={chosen['sh_net']:+.2f} gross={chosen['sh_gross']:+.2f} "
        f"maxDD={ct.maxdd(ct.is_only(chosen['net'])) * 100:.1f}%  turn/day={chosen['turn']:.4f}"
    )
    print(
        f"      regimes(IS): bull={reg['bull']:+.2f} bear={reg['bear']:+.2f} "
        f"chop={reg['chop']:+.2f}  ({chosen['n_pos']}/3 positive)"
    )
    print(f"      sector-neutrality residual (IS active): {i3._sector_residual(chosen['w']):.1e}")
    print(
        f"\n  vs iter-003 (mom-only net +0.16):  d_net={chosen['sh_net'] - mom['sh_net']:+.2f}  "
        f"d_chop={reg['chop'] - mom['reg']['chop']:+.2f}  "
        f"d_bear={reg['bear'] - mom['reg']['bear']:+.2f}"
    )

    promotable = chosen["sh_net"] >= 0.30
    all_weather = chosen["n_pos"] >= 2
    print(
        f"\n  bar: promotable(>=+0.30)={'YES' if promotable else 'NO'}  "
        f"all-weather(>=2/3 regimes)={'YES' if all_weather else 'NO'}"
    )


if __name__ == "__main__":
    main()

"""iter-010 — BETA-NEUTRAL OVERLAY on the iter-006 signal (IS-only, 2010-2025).

Tests the iter-007 ORTHOGONAL finding on the robust 15-year data. The iter-007 MVO probe found a
HARD beta-neutral constraint transformed CHOP (+0.26 -> +1.05 daily) but WRECKED bear — on 2018-only
data, inside the mean-variance context. Here we ask the same question on the NAIVE iter-006 book on
the full 2010-2025 IS window: does removing the book's net market-beta exposure lift chop / overall
Sharpe, and does making the neutralization regime-CONDITIONAL (skip it in the bear state, where the
iter-006 crash gate already handles risk) avoid the bear damage iter-007 saw?

=========================================================================================
THE ONE CHANGE — a beta-neutral projection on the raw weight book, pre-band
=========================================================================================
iter-006's raw book is beta-neutralized BEFORE the iter-003 hysteresis band. Everything downstream —
the band (delta=0.005), banded_net's vol-target / taker-cost model, the OOS-hidden accounting — is
UNCHANGED. Only the raw weight vector that feeds the band is projected off the market-beta vector.

    ret[t,i]   = close.pct_change()                         # daily returns (past-priced)
    mkt[t]     = ret.mean(axis=1)                           # EQUAL-WEIGHT universe return
    beta[t,i]  = rolling_beta(ret, mkt, win=63)[t,i].shift(1)   # past-only, LAGGED before use
    raw6       = i6.crash_braked_raw(pn)                    # the iter-006 signal (UNCHANGED)
    raw_bn     = beta_neutralize(raw6, beta) = raw6 - (Σ w·β / Σ β²)·β   # net market-beta -> 0

`beta_neutralize` projects the weight vector off the beta vector per row (a least-squares hedge of
the single market factor), so Σ_i (w_i - k·β_i)·β_i == 0 — the book carries ZERO net market beta.
The betas are `.shift(1)`-lagged and NaN-filled to 0 (a name with no beta yet is simply UN-hedged,
never dropped), so the transform is strictly past-only.

=========================================================================================
THREE PRE-REGISTERED VARIANTS (NOT swept, NOT max-net picked)
=========================================================================================
  1. UNCONDITIONAL : raw = beta_neutralize(raw6, beta)            (neutralize EVERY bar)
  2. CONDITIONAL   : raw = g*raw6 + (1-g)*raw_bn                  (skip in the bear state g=1)
  3. PARTIAL 0.5x  : raw = 0.5*raw6 + 0.5*raw_bn                  (remove HALF the net beta)

g[t] = i6.bear_state(close) is the EXISTING past-only 252d EW-return<0 bear gate from iter-006 — the
SAME gate the crash brake already fires on. The conditional book runs the iter-006 crash-gated book
UNCHANGED in the bear (where the fast->slow sleeve rotation already de-risks) and beta-neutralizes
it only in bull+chop. No new gate window / threshold is introduced; g is reused verbatim.

=========================================================================================
PRE-REGISTERED IDENTITIES
=========================================================================================
  * beta_neutralize(raw6, beta=0) == raw6  -> banded net reproduces iter-006 bit-for-bit.
  * CONDITIONAL with g == all-ONES  == iter-006 (never neutralize -> pure crash-gated book).
  * CONDITIONAL with g == all-ZEROS == UNCONDITIONAL (always neutralize).
  * PARTIAL frac=0.0 == iter-006 ; frac=1.0 == UNCONDITIONAL.

=========================================================================================
LEAK SAFETY (HARD rule)
=========================================================================================
  * beta uses returns strictly before the decision bar (rolling_beta is past-only, then .shift(1));
    a warm-up / absent-name NaN beta is filled to 0 (un-hedged), never a forward read.
  * the conditional gate g is the existing past-only bear-state (close[t]/close[t-1] + 252d trend).
  * the transformed raw book feeds the strictly-causal iter-003 band, which applies the single
    .shift(1) execution lag. net[t] reads only held[t-1] -> future-bar leak-safe.
  * verified by the in-script future-bar self-check (corrupt panel + forward returns after a cutoff
    -> beta-neutral net before it is bit-identical) and test_iter010_betaneutral_future_bar_no_leak.

OOS stays HIDDEN — every metric is IS-only (< OOS_CUTOFF 2025-03-24); no OOS number is computed or
printed without --confirm (CONFIRMATION only). Do NOT tune the beta window / partial fraction here.

Run: uv run python analysis/portfolio/tradfi/iter_010_betaneutral.py
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
import iter_003_hysteresis as i3  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

BETA_WIN = 63  # market-beta window (== neutralize.rolling_beta default / iter-005 rvol / iter-007)
PARTIAL_FRAC = 0.5  # variant 3: remove HALF the net beta (convex blend iter-006 <-> unconditional)
CHOSEN_DELTA = i6.CHOSEN_DELTA  # 0.005, inherited from iter-003 UNCHANGED


def market_return(close: pd.DataFrame) -> pd.Series:
    """Past-only EQUAL-WEIGHT universe daily return = cross-sectional mean of close.pct_change().

    close[t]/close[t-1] only (no forward read); the same EW proxy iter-006's bear gate + iter-007's
    residual sleeve use. NaN names are skipped by the row-mean (ragged PIT membership).
    """
    return close.pct_change().mean(axis=1)


def book_betas(pn: dict[str, pd.DataFrame], win: int = BETA_WIN) -> pd.DataFrame:
    """Past-only rolling betas of each name to the EW-market, LAGGED (.shift(1)), NaN-filled to 0.

    A name whose trailing window is not yet full (or absent) gets beta 0 -> it is left UN-hedged by
    beta_neutralize (never dropped). The .shift(1) makes beta[t] read only returns strictly < t.
    """
    ret = pn["close"].pct_change()
    mkt = market_return(pn["close"])
    return nz.rolling_beta(ret, mkt, win).shift(1).fillna(0.0)


def unconditional_raw(raw6: pd.DataFrame, betas: pd.DataFrame) -> pd.DataFrame:
    """Variant 1 — beta-neutralize the iter-006 book on EVERY bar (removes all net market beta)."""
    return nz.beta_neutralize(raw6, betas)


def conditional_raw(raw6: pd.DataFrame, raw_bn: pd.DataFrame, g: pd.Series) -> pd.DataFrame:
    """Variant 2 — g*raw6 + (1-g)*raw_bn: iter-006 book in the bear (g=1), beta-neutral elsewhere.

    A row-wise convex blend of two past-only books gated by the existing past-only bear-state -> the
    combined book stays past-only. g=1 (bear) keeps the crash-gated book; g=0 (bull/chop) hedges it.
    """
    g = g.reindex(raw6.index).fillna(0.0)
    return raw6.mul(g, axis=0).add(raw_bn.mul(1.0 - g, axis=0), fill_value=0.0)


def partial_raw(
    raw6: pd.DataFrame, raw_bn: pd.DataFrame, frac: float = PARTIAL_FRAC
) -> pd.DataFrame:
    """Variant 3 — (1-frac)*raw6 + frac*raw_bn: remove `frac` of the net beta (frac=0.5 -> half)."""
    return raw6.mul(1.0 - frac).add(raw_bn.mul(frac), fill_value=0.0)


def net_beta_series(raw: pd.DataFrame, betas: pd.DataFrame) -> pd.Series:
    """Per-bar net market beta of the GROSS-NORMALIZED raw book: Σ_i (w_i / Σ|w|) · β_i.

    Gross-normalized so the exposure is comparable across builds (unit-gross book). This is the
    structural market-beta the book carries at decision time (same betas fed into beta_neutralize).
    """
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0)
    b = betas.reindex_like(raw).fillna(0.0)
    return (w * b).sum(axis=1)


def _metrics(net: pd.Series, w: pd.DataFrame, raw: pd.DataFrame, ret_fwd, delta) -> dict:
    """IS-only (net, gross, turn, maxDD, regimes, n_pos) bundle for a banded build."""
    gnet, _ = i3.banded_net(raw, ret_fwd, delta, cost_on=False)
    reg = ct.regime_sharpe(ct.is_only(net))
    return {
        "net": ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF),
        "gross": ct.msharpe(gnet, ct.LO0, ct.OOS_CUTOFF),
        "turn": ct.turnover(w, ct.LO0, ct.OOS_CUTOFF),
        "mdd": ct.maxdd(ct.is_only(net)) * 100,
        "reg": reg,
        "n_pos": sum(1 for v in reg.values() if v > 0),
    }


def _line(
    label: str, m: dict, base_turn: float | None, *, net_series=None, reveal_oos=False
) -> str:
    tpc = "" if base_turn is None else f" ({(m['turn'] / base_turn - 1) * 100:+.0f}%)"
    head = (
        ct.perf_line(label, net_series, reveal_oos=reveal_oos)
        if net_series is not None
        else f"  {label:22}"
    )
    r = m["reg"]
    return (
        f"{head}\n"
        f"      gross={m['gross']:+.2f} net={m['net']:+.2f}  maxDD={m['mdd']:.0f}%  "
        f"turn/day={m['turn']:.4f}{tpc}\n"
        f"      regimes(IS): bull={r['bull']:+.2f} bear={r['bear']:+.2f} "
        f"chop={r['chop']:+.2f}  ({m['n_pos']}/3 positive)"
    )


def _beta_summary(net_beta_is: pd.Series) -> str:
    """Mean signed + mean |net beta| over IS active bars (the market exposure the book carries)."""
    s = net_beta_is.replace(0.0, np.nan).dropna()
    if s.empty:
        return "mean=+0.000 |mean|=0.000"
    return f"mean={s.mean():+.3f} |mean|={s.abs().mean():.3f}"


def _leak_selfcheck(pn, ret_fwd, delta) -> bool:
    """Corrupt panel + forward returns AFTER a cutoff; the UNCONDITIONAL beta-neutral net before it
    must not move (the strongest build — betas + book both rebuilt from the corrupted panel)."""
    raw6 = i6.crash_braked_raw(pn)
    betas = book_betas(pn)
    net0, w0 = i3.banded_net(unconditional_raw(raw6, betas), ret_fwd, delta)
    cut = net0.index[len(net0) // 2]

    pn_c = {k: v.copy() for k, v in pn.items()}
    pn_c["close"].loc[pn_c["close"].index >= cut] *= -7.0
    pn_c["ret_fwd"].loc[pn_c["ret_fwd"].index >= cut] += 5.0
    raw6_c = i6.crash_braked_raw(pn_c)
    betas_c = book_betas(pn_c)
    net1, w1 = i3.banded_net(unconditional_raw(raw6_c, betas_c), pn_c["ret_fwd"], delta)

    common = net0.index.intersection(net1.index)
    common = common[common < cut]
    ok_net = np.allclose(net0.loc[common].to_numpy(), net1.loc[common].to_numpy(), atol=1e-12)
    ok_w = np.allclose(
        w0[w0.index < cut].fillna(0.0).to_numpy(),
        w1[w1.index < cut].fillna(0.0).to_numpy(),
        atol=1e-12,
    )
    return bool(ok_net and ok_w)


def main() -> None:
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
        print("No ingested tradfi data found. Run ingest_yahoo.py first.")
        return

    pn = ct.panels(coins)
    ret_fwd = pn["ret_fwd"]

    raw6 = i6.crash_braked_raw(pn)  # the iter-006 signal — UNCHANGED
    betas = book_betas(pn)  # past-only, lagged, NaN->0
    g = i6.bear_state(pn["close"])  # existing past-only bear-state

    raw_bn = unconditional_raw(raw6, betas)
    raw_cond = conditional_raw(raw6, raw_bn, g)
    raw_half = partial_raw(raw6, raw_bn, PARTIAL_FRAC)

    print("=" * 100)
    print("iter-010 — BETA-NEUTRAL OVERLAY on iter-006 (2010-2025 IS, OOS HIDDEN)")
    print("=" * 100)
    print(
        f"  beta: rolling_beta(ret, EW-univ, win={BETA_WIN}).shift(1);  "
        f"beta_neutralize removes net Σ w·β;  band delta={d:.3f} (iter-003 UNCHANGED)\n"
    )

    # --- PRE-REGISTERED IDENTITIES ---
    net_id, _ = i3.banded_net(
        nz.beta_neutralize(raw6, betas * 0.0), ret_fwd, d
    )  # beta=0 -> unchanged
    net_i6, _ = i3.banded_net(raw6, ret_fwd, d)
    id_zero = bool(np.allclose(net_id.to_numpy(), net_i6.to_numpy(), atol=1e-12))
    ones = pd.Series(1.0, index=pn["close"].index)
    zeros = pd.Series(0.0, index=pn["close"].index)
    net_cond1, _ = i3.banded_net(conditional_raw(raw6, raw_bn, ones), ret_fwd, d)  # g=1 -> iter-006
    net_cond0, _ = i3.banded_net(conditional_raw(raw6, raw_bn, zeros), ret_fwd, d)  # g=0 -> uncond
    net_uncond_chk, _ = i3.banded_net(raw_bn, ret_fwd, d)
    id_cond1 = bool(np.allclose(net_cond1.to_numpy(), net_i6.to_numpy(), atol=1e-12))
    id_cond0 = bool(np.allclose(net_cond0.to_numpy(), net_uncond_chk.to_numpy(), atol=1e-12))
    print(
        f"  IDENTITY beta=0 == iter-006: {'PASS' if id_zero else 'FAIL'}   "
        f"cond(g=1) == iter-006: {'PASS' if id_cond1 else 'FAIL'}   "
        f"cond(g=0) == unconditional: {'PASS' if id_cond0 else 'FAIL'}"
    )

    # --- the four builds (iter-006 baseline + 3 variants) ---
    net6, w6 = i3.banded_net(raw6, ret_fwd, d)
    net_un, w_un = i3.banded_net(raw_bn, ret_fwd, d)
    net_cd, w_cd = i3.banded_net(raw_cond, ret_fwd, d)
    net_hf, w_hf = i3.banded_net(raw_half, ret_fwd, d)

    m6 = _metrics(net6, w6, raw6, ret_fwd, d)
    m_un = _metrics(net_un, w_un, raw_bn, ret_fwd, d)
    m_cd = _metrics(net_cd, w_cd, raw_cond, ret_fwd, d)
    m_hf = _metrics(net_hf, w_hf, raw_half, ret_fwd, d)
    bt = m6["turn"]

    print("\n  --- IS effect (iter-006 baseline vs the 3 pre-registered beta-neutral variants) ---")
    print(_line("iter-006 (baseline)", m6, None, net_series=net6, reveal_oos=args.confirm))
    print("      ^ working best: net +0.28 bull +0.30 bear -0.24 chop +0.51 maxDD -29%")
    print(_line("1. UNCONDITIONAL", m_un, bt, net_series=net_un, reveal_oos=args.confirm))
    print(_line("2. CONDITIONAL (non-bear)", m_cd, bt, net_series=net_cd, reveal_oos=args.confirm))
    print(
        _line(
            f"3. PARTIAL {PARTIAL_FRAC:.1f}x", m_hf, bt, net_series=net_hf, reveal_oos=args.confirm
        )
    )

    # --- realized net market-beta before/after (the requested diagnostic; should -> 0) ---
    nb6 = ct.is_only(net_beta_series(raw6, betas))
    nb_un = ct.is_only(net_beta_series(raw_bn, betas))
    nb_cd = ct.is_only(net_beta_series(raw_cond, betas))
    nb_hf = ct.is_only(net_beta_series(raw_half, betas))
    print("\n  realized net market-beta of the gross-normalized book (IS active bars):")
    print(f"    iter-006 (before)        : {_beta_summary(nb6)}")
    print(f"    1. UNCONDITIONAL (after)  : {_beta_summary(nb_un)}")
    print(f"    2. CONDITIONAL (after)    : {_beta_summary(nb_cd)}  (bear bars keep iter-006 beta)")
    print(f"    3. PARTIAL {PARTIAL_FRAC:.1f}x (after)     : {_beta_summary(nb_hf)}")

    # --- deltas vs iter-006 (the headline question) ---
    print("\n  --- Δ vs iter-006 (net / bull / bear / chop) ---")
    for lab, m in (("1. UNCOND ", m_un), ("2. COND   ", m_cd), ("3. PARTIAL", m_hf)):
        r, r6 = m["reg"], m6["reg"]
        print(
            f"    {lab}: dnet={m['net'] - m6['net']:+.2f}  dbull={r['bull'] - r6['bull']:+.2f}  "
            f"dbear={r['bear'] - r6['bear']:+.2f}  dchop={r['chop'] - r6['chop']:+.2f}"
        )

    # --- sector-neutrality note (beta-neutral projection is NOT sector-structured -> it drifts) ---
    print(
        f"\n  sector-neutrality residual (IS active): iter-006={i3._sector_residual(w6):.1e}  "
        f"uncond={i3._sector_residual(w_un):.1e}  cond={i3._sector_residual(w_cd):.1e}  "
        f"(beta-projection is not per-sector-structured; it induces a sector drift)"
    )

    # --- LEAK self-check (UNCONDITIONAL, panel + forward returns corrupted post-cutoff) ---
    print(
        f"\n  future-bar leak self-check (beta-neutral net+weights bit-identical pre-cut): "
        f"{'PASS' if _leak_selfcheck(pn, ret_fwd, d) else 'FAIL'}"
    )

    # --- PRE-REGISTERED VERDICTS (report whatever the fixed variants give; NOT tuned) ---
    r_un, r_cd, r6 = m_un["reg"], m_cd["reg"], m6["reg"]
    # Q1: does UNCONDITIONAL beta-neutral lift chop / overall on 15-yr (the iter-007 hypothesis)?
    chop_lift = r_un["chop"] > r6["chop"] + 1e-9
    net_lift = m_un["net"] > m6["net"] + 1e-9
    bear_hurt = r_un["bear"] < r6["bear"] - 1e-9
    print("\n  Q1 (UNCONDITIONAL, the iter-007 hypothesis on 15-yr data):")
    print(
        f"    chop {r6['chop']:+.2f}->{r_un['chop']:+.2f} ({'LIFT' if chop_lift else 'flat'})  "
        f"net {m6['net']:+.2f}->{m_un['net']:+.2f} ({'LIFT' if net_lift else 'flat'})  "
        f"bear {r6['bear']:+.2f}->{r_un['bear']:+.2f} ({'HURT' if bear_hurt else 'ok'})"
    )
    # Q2: does the CONDITIONAL version keep the chop lift WITHOUT wrecking bear?
    cond_keeps_chop = r_cd["chop"] >= r6["chop"] - 0.05  # chop preserved-or-lifted
    cond_bear_ok = r_cd["bear"] >= r6["bear"] - 0.10  # bear NOT wrecked (within tolerance)
    cond_net_ok = m_cd["net"] >= m6["net"] - 0.02  # net not washed
    keep_cond = cond_keeps_chop and cond_bear_ok and cond_net_ok
    print("\n  Q2 (CONDITIONAL — chop lift WITHOUT bear damage?):")
    print(
        f"    chop_preserved(>=+0.46)={'Y' if cond_keeps_chop else 'N'} "
        f"({r6['chop']:+.2f}->{r_cd['chop']:+.2f})  "
        f"bear_not_wrecked(>=-0.34)={'Y' if cond_bear_ok else 'N'} "
        f"({r6['bear']:+.2f}->{r_cd['bear']:+.2f})  "
        f"net_not_washed(>=+0.26)={'Y' if cond_net_ok else 'N'} "
        f"({m6['net']:+.2f}->{m_cd['net']:+.2f})"
    )
    print(f"  VERDICT (conditional): {'KEEP' if keep_cond else 'REJECT'}")
    print(
        "  read: the beta-neutral projection removes the book's net market beta (-> ~0); whether "
        "that lift survives 2010-2025 and the bear is the pre-registered test above."
    )


if __name__ == "__main__":
    main()

"""iter-012 BROAD PROBE — do the factors that DIED on the 69 mega-cap-growth names WORK on a broad
US universe, and how much is realizable within the tradeable 69? (IS-only 2010-2025, OOS HIDDEN).

THE PIVOTAL TEST of the multi-factor pivot. On the 69 Binance-tradeable names (homogeneous mega-cap
GROWTH) the cross-sectional value/quality/BAB/low-vol/size factors are signal-negative: no cheap
tail, no small tail, no genuine low-beta tail. The QR's hypothesis is that UNIVERSE BREADTH
resurrects them. This probe measures it on ~500 S&P 500 names ingested to data_broad/ by
ingest_yahoo_broad.py, then asks how much of any broad-universe edge survives when the tradeable
cross-section is restricted to the 69.

Six PRICE-ONLY, past-only, sector-neutral factors (each a cross-sectional z-score -> per-sector
demean -> the same leak-safe net_from_raw vol-target + 6bps taker cost as the momentum stack):
  * MOM 12-1m   :  (close[t-21]/close[t-252]-1)/rvol      LONG winners
  * LTR 3y-1y   : -(close[t-252]/close[t-756]-1)/rvol     LONG multi-year losers (value proxy)
  * BAB low-beta: -rolling_beta(252d, mkt).shift(1)       LONG low-beta / SHORT high (Frazzini-P)
  * LOW-VOL     : -rvol_63                                LONG low realized-vol
  * SIZE        : -log(mean_63(close*volume))             LONG small (dollar-vol proxy for mcap)
  * ST-REV 1m   : -(close[t]/close[t-21]-1)/rvol          LONG 1-month losers

Then: (A) standalone IS Sharpe + per-year sign + pairwise corr; (B) an inverse-vol (risk-parity)
multi-factor combine of the POSITIVE-EV, low-correlated factors -> net Sharpe + per-year X/16 +
per-regime + maxDD; (C) the HYBRID deployable-69 — the same construction on the tradeable-69
sub-panel — to size how much of the broad edge is capturable.

>>> SURVIVORSHIP CAVEAT <<<  data_broad/ is CURRENT S&P 500 membership (Wikipedia), NOT PIT.
Backtesting on today's members INFLATES results (delisted failures are absent). This is a FIRST-PASS
diversity test (is there enough cross-sectional spread for the factors to fire at all?), NOT a
deployable backtest. If the factors work, a PIT-membership rebuild is the follow-up.

LEAK SAFETY: every characteristic is built from PAST prices only (close.shift(>=21) for
mom/ltr/rev; betas .shift(1); rvol/dollar-vol are trailing windows ending at t); the combined raw
feeds net_from_raw / the strictly-causal band (single .shift(1) execution lag). OOS is HIDDEN —
every number is on the IS slice (< 2025-03-24); no OOS is computed. This is a PROBE, not a promote.

Run:  uv run python analysis/portfolio/tradfi/iter_012_broad.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_003_hysteresis as i3  # noqa: E402
import neutralize as nz  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DATA_BROAD = _ROOT / "data_broad"
DELTA = i3.CHOSEN_DELTA  # 0.005 hysteresis band for the combined book (standalone factors unbanded)
BETA_WIN = 252  # 1-year rolling beta window (Frazzini-Pedersen use ~1yr daily)
DVOL_WIN = 63  # dollar-volume averaging window for the size proxy
DECORR_MAX = 0.70  # greedy de-correlation cutoff for the "positive-EV, low-correlated" selection
FACTORS = ("MOM_12_1", "LTR_3y1y", "BAB_lowbeta", "LOWVOL", "SIZE", "STREV_1m")
_YAHOO_OVERRIDES = {"BRKBUSDT": "BRK-B", "PAYPUSDT": "PYPL"}


def binance_to_broad(sym: str) -> str:
    """Tradeable-69 Binance ticker -> its broad/Yahoo ticker (AAPLUSDT->AAPL, BRKBUSDT->BRK-B)."""
    return _YAHOO_OVERRIDES.get(sym, ut.stem(sym))


# ---------------------------------------------------------------- data loading -----------------
def load_broad() -> tuple[dict, dict[str, str]]:
    """Load every data_broad/<TICKER>/1d.csv + the cached GICS sector map. Raises if empty."""
    sect_path = DATA_BROAD / "_sectors.json"
    if not sect_path.exists():
        raise SystemExit("data_broad/_sectors.json missing — run ingest_yahoo_broad.py first.")
    sectors = json.loads(sect_path.read_text())
    syms = sorted(p.parent.name for p in DATA_BROAD.glob("*/1d.csv"))
    coins = ct.load_tradfi(syms, DATA_BROAD)
    if not coins:
        raise SystemExit("no data_broad CSVs found — run ingest_yahoo_broad.py first.")
    return coins, sectors


def _volume_panel(coins: dict, index: pd.DatetimeIndex, cols: list[str]) -> pd.DataFrame:
    """Aligned float volume panel on the close-panel datetime index (for the dollar-vol proxy)."""
    v = pd.DataFrame({s: coins[s]["volume"] for s in cols}).astype(float).sort_index()
    v.index = pd.to_datetime(v.index, unit="ms")
    return v.reindex(index)


# ---------------------------------------------------------------- factor signals ---------------
def _rvol(close: pd.DataFrame) -> pd.DataFrame:
    """Trailing-63 realized vol of daily returns (past-only), the shared inverse-vol scaler."""
    return close.pct_change().rolling(ct.VOL_WIN).std()


def _xs_z(x: pd.DataFrame, winsor: float = 3.0) -> pd.DataFrame:
    """Row-wise cross-sectional z-score (NaN-skipping mean/std), winsorized at +/-winsor.

    Past-only: x is built from past prices; the z-score is a pure cross-sectional standardization of
    the present row. inf (e.g. rvol==0) is nulled first so it can't drive the mean/std; names with a
    NaN characteristic (warm-up / ragged IPO) stay NaN -> 0 weight.
    """
    x = x.replace([np.inf, -np.inf], np.nan)
    mu = x.mean(axis=1)
    sd = x.std(axis=1).replace(0, np.nan)
    return x.sub(mu, axis=0).div(sd, axis=0).clip(-winsor, winsor)


def make_panel(coins: dict, cols: list[str]) -> dict[str, pd.DataFrame]:
    """core_tradfi.panels for the sub-universe `cols`, plus an aligned volume panel (for SIZE)."""
    pn = ct.panels({c: coins[c] for c in cols})
    pn["volume"] = _volume_panel(coins, pn["close"].index, cols)
    return pn


def build_signals(pn: dict, sectors: dict[str, str], cols: list[str]) -> dict[str, pd.DataFrame]:
    """The six sector-neutral factor signals on the sub-universe `cols` (leak-safe, past-only).

    market proxy = equal-weight mean daily return ACROSS `cols` (so BAB betas are relative to the
    same universe being traded). Each characteristic is z-scored cross-sectionally then per-sector
    demeaned via neutralize.sector_neutralize (dollar- + sector-neutral by construction). Every
    input is a backward window on pn['close'/'volume']; betas are .shift(1) before use.
    """
    close = pn["close"]
    rvol = _rvol(close)
    rets = close.pct_change()
    mkt = rets.mean(axis=1)  # broad-market proxy over the sub-universe
    beta = nz.rolling_beta(rets, mkt, BETA_WIN).shift(1)  # .shift(1): betas used to size bar t+1
    dvol = (close * pn["volume"]).rolling(DVOL_WIN).mean()

    chars = {
        "MOM_12_1": (close.shift(21) / close.shift(252) - 1.0) / rvol,
        "LTR_3y1y": -(close.shift(252) / close.shift(756) - 1.0) / rvol,
        "BAB_lowbeta": -beta,
        "LOWVOL": -rvol,
        "SIZE": -np.log(dvol.where(dvol > 0)),
        "STREV_1m": -(close / close.shift(21) - 1.0) / rvol,
    }
    smap = {c: sectors.get(c, "__" + c) for c in cols}
    return {name: nz.sector_neutralize(_xs_z(x), smap) for name, x in chars.items()}


# ---------------------------------------------------------------- IS-only metrics ---------------
def _gn(raw: pd.DataFrame) -> pd.DataFrame:
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


def standalone_net(sig: pd.DataFrame, ret_fwd: pd.DataFrame) -> pd.Series:
    """Unbanded standalone net (the task's `net_from_raw` path) for a single factor signal."""
    net, _ = ct.net_from_raw(sig, ret_fwd)
    return net


def year_table(net: pd.Series) -> dict[int, tuple[float, float]]:
    net = ct.is_only(net)
    out: dict[int, tuple[float, float]] = {}
    for yr, g in net.groupby(net.index.year):
        m = g.groupby(g.index.to_period("M")).sum()
        sh = float(m.mean() / m.std() * np.sqrt(12)) if len(m) > 1 and m.std() > 0 else float("nan")
        out[int(yr)] = (sh, float((np.prod(1.0 + g) - 1.0) * 100))
    return out


def n_pos_years(net: pd.Series) -> tuple[int, int]:
    yt = year_table(net)
    return sum(1 for sh, _ in yt.values() if sh > 0), len(yt)


def _monthly(net: pd.Series) -> pd.Series:
    net = ct.is_only(net)
    return net.groupby(net.index.to_period("M")).sum()


def corr(a: pd.Series, b: pd.Series) -> float:
    ma, mb = _monthly(a), _monthly(b)
    idx = ma.index.intersection(mb.index)
    if len(idx) < 3:
        return float("nan")
    return float(np.corrcoef(ma.loc[idx], mb.loc[idx])[0, 1])


def _is_vol(net: pd.Series) -> float:
    """IS monthly-return std (the inverse-vol weight denominator)."""
    m = _monthly(net)
    return float(m.std()) if len(m) > 1 and m.std() > 0 else float("nan")


def select_positive_lowcorr(nets: dict[str, pd.Series]) -> list[str]:
    """Greedy pick: positive-EV factors, best-Sharpe-first, skipping any with |corr|>=DECORR_MAX
    to an already-selected factor (the 'positive-EV, low-correlated' book)."""
    pos = [n for n in nets if ct.msharpe(nets[n], ct.LO0, ct.OOS_CUTOFF) > 0]
    pos.sort(key=lambda n: ct.msharpe(nets[n], ct.LO0, ct.OOS_CUTOFF), reverse=True)
    keep: list[str] = []
    for n in pos:
        if all(abs(corr(nets[n], nets[k])) < DECORR_MAX for k in keep):
            keep.append(n)
    return keep


def invvol_signal_book(
    signals: dict[str, pd.DataFrame], nets: dict[str, pd.Series], members: list[str]
) -> pd.DataFrame:
    """Inverse-IS-vol weighted blend of the gross-normed member signals (equal risk budget)."""
    inv = {m: 1.0 / _is_vol(nets[m]) for m in members}
    tot = sum(inv.values())
    acc = None
    for m in members:
        contrib = _gn(signals[m]) * (inv[m] / tot)
        acc = contrib if acc is None else acc.add(contrib, fill_value=0.0)
    return acc


def report_book(label: str, net: pd.Series) -> dict:
    npos, nyr = n_pos_years(net)
    reg = ct.regime_sharpe(ct.is_only(net))
    sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
    mdd = ct.maxdd(ct.is_only(net)) * 100
    print(
        f"    {label:26} net={sh:+.2f}  +yrs={npos:>2}/{nyr}  maxDD={mdd:5.0f}%  "
        f"bull/bear/chop={reg['bull']:+.2f}/{reg['bear']:+.2f}/{reg['chop']:+.2f}"
    )
    return {"sharpe": sh, "npos": npos, "nyr": nyr, "maxdd": mdd, "reg": reg}


# ---------------------------------------------------------------- main --------------------------
def main() -> None:
    coins, sectors = load_broad()
    broad_cols = sorted(coins)
    n_sectors = len(set(sectors.get(c, "?") for c in broad_cols))
    print("=" * 100)
    print(
        "iter-012 BROAD PROBE — factors on ~500 S&P names vs the 69 (IS-only 2010-2025, OOS HIDDEN)"
    )
    print("=" * 100)
    print(f"  broad universe: {len(broad_cols)} names across {n_sectors} GICS sectors")
    print(
        "  *** SURVIVORSHIP CAVEAT: current S&P 500 membership, NOT point-in-time (inflates). ***\n"
    )

    pn = make_panel(coins, broad_cols)
    signals = build_signals(pn, sectors, broad_cols)
    ret_fwd = pn["ret_fwd"]
    nets = {name: standalone_net(sig, ret_fwd) for name, sig in signals.items()}

    # ---- (A) standalone factor scorecard ----
    print("(A) STANDALONE factors on BROAD (net_from_raw, 15% vol-target + 6bps) — IS net Sharpe:")
    print(f"    {'factor':14} {'net':>6} {'+yrs':>7}   per-year sign (2010->2025)")
    for name in FACTORS:
        net = nets[name]
        sh = ct.msharpe(net, ct.LO0, ct.OOS_CUTOFF)
        npos, nyr = n_pos_years(net)
        yt = year_table(net)
        signs = "".join("+" if yt[y][0] > 0 else "-" for y in sorted(yt))
        print(f"    {name:14} {sh:>+6.2f} {npos:>4}/{nyr}   {signs}")

    # ---- pairwise correlation matrix (monthly IS net) ----
    print("\n    pairwise monthly-net corr (IS):")
    print("    " + " " * 12 + " ".join(f"{n[:7]:>7}" for n in FACTORS))
    for a in FACTORS:
        row = " ".join(f"{corr(nets[a], nets[b]):>+7.2f}" for b in FACTORS)
        print(f"    {a:>12} {row}")

    # ---- (B) multi-factor combine (inverse-vol / risk-parity) ----
    members = select_positive_lowcorr(nets)
    print(
        f"\n(B) MULTI-FACTOR combine on BROAD (inverse-vol risk-parity, band delta={DELTA}, "
        f"vol-targeted):"
    )
    print(
        "    positive-EV & low-corr selection: " + ", ".join(members) + f"  ({len(members)} of 6)"
    )
    pos_ev = [n for n in FACTORS if ct.msharpe(nets[n], ct.LO0, ct.OOS_CUTOFF) > 0]

    combos = {
        "SELECTED (pos-EV,low-corr)": members,
        "ALL positive-EV": pos_ev,
    }
    combo_nets: dict[str, pd.Series] = {}
    for label, mem in combos.items():
        if not mem:
            continue
        book = invvol_signal_book(signals, nets, mem)
        net, _ = i3.banded_net(book, ret_fwd, DELTA)
        combo_nets[label] = net
        report_book(label, net)

    # return-level risk-parity cross-check (portfolio of standalone factor return streams)
    inv = {m: 1.0 / _is_vol(nets[m]) for m in members}
    tot = sum(inv.values())
    rp_ret = sum((nets[m] * (inv[m] / tot)).reindex(ret_fwd.index).fillna(0.0) for m in members)
    report_book("  (return-level RP check)", ct.vol_target(rp_ret.loc[rp_ret.ne(0).cummax()]))

    headline = combo_nets.get("SELECTED (pos-EV,low-corr)")
    if headline is not None:
        npos, nyr = n_pos_years(headline)
        sh = ct.msharpe(headline, ct.LO0, ct.OOS_CUTOFF)
        print("\n    PER-YEAR net Sharpe (BROAD SELECTED combo, IS 2010-2025):")
        yt = year_table(headline)
        for yr in sorted(yt):
            mark = "" if yt[yr][0] > 0 else "   <- NEGATIVE"
            print(f"      {yr}: Sharpe={yt[yr][0]:>+6.2f}  ret={yt[yr][1]:>+6.1f}%{mark}")
        reach = sh >= 0.5 and npos == nyr
        print(
            f"\n    >>> BROAD SELECTED: net={sh:+.2f}, positive-years={npos}/{nyr}  "
            f"-> reaches (net>=0.5 AND positive-ALL-years)? {'YES' if reach else 'NO'} "
            "(survivorship-caveated)"
        )

    # ---- (C) hybrid deployable-69 ----
    the69 = [binance_to_broad(s) for s in ut.SECTOR_MAP]
    cov69 = sorted(t for t in the69 if t in coins)
    print(
        f"\n(C) HYBRID deployable-69 — same construction on the tradeable-69 sub-panel "
        f"({len(cov69)}/{len(the69)} of the 69 present in data_broad):"
    )
    pn69 = make_panel(coins, cov69)
    sig69 = build_signals(pn69, sectors, cov69)
    ret69 = pn69["ret_fwd"]
    nets69 = {name: standalone_net(sig, ret69) for name, sig in sig69.items()}
    print("    standalone factor net Sharpe on the 69 sub-panel:")
    for name in FACTORS:
        sh = ct.msharpe(nets69[name], ct.LO0, ct.OOS_CUTOFF)
        npos, nyr = n_pos_years(nets69[name])
        print(f"      {name:14} net={sh:>+6.2f}  +yrs={npos}/{nyr}")

    # Deployable book variant 1: SAME selected factor set, inverse-vol on the 69 sub-panel vols.
    mem69 = [m for m in members if m in sig69]
    book69 = invvol_signal_book(sig69, nets69, mem69)
    net69, _ = i3.banded_net(book69, ret69, DELTA)
    print(
        f"\n    deployable-69 combo (factors={mem69}, inverse-vol on 69 sub-panel, "
        f"band delta={DELTA}):"
    )
    r69 = report_book("deployable-69 SELECTED", net69)
    yt69 = year_table(net69)
    signs69 = "".join("+" if yt69[y][0] > 0 else "-" for y in sorted(yt69))
    print(f"      per-year sign: {signs69}")

    # ---- leak self-check: corrupt the panel's close/volume (signal inputs) + ret_fwd AFTER a cut;
    # the IS combo net must be bit-identical pre-cut. Mirrors iter-011: `open` is left intact so the
    # pre-cut ret_fwd (open[t+1]/open[t]) is unchanged; only genuinely-future info is corrupted. ---
    cut = headline.index[len(headline) // 2] if headline is not None else ret_fwd.index[-100]
    pn_c = {k: v.copy() for k, v in pn.items()}
    m = pn_c["close"].index >= cut
    pn_c["close"].loc[m] *= -7.0
    pn_c["volume"].loc[m] *= 3.0
    pn_c["ret_fwd"].loc[m] += 5.0
    sig_c = build_signals(pn_c, sectors, broad_cols)
    book_c = invvol_signal_book(sig_c, {mm: nets[mm] for mm in members}, members)
    net_c, _ = i3.banded_net(book_c, pn_c["ret_fwd"], DELTA)
    common = headline.index.intersection(net_c.index)
    common = common[common < cut]
    ok = np.allclose(headline.loc[common].to_numpy(), net_c.loc[common].to_numpy(), atol=1e-10)
    resid = i3._sector_residual(i3.banded_book(invvol_signal_book(signals, nets, members), DELTA))
    print(
        f"\n  future-bar leak self-check (BROAD combo net bit-identical pre-cut): "
        f"{'PASS' if ok else 'FAIL'}"
    )
    print(f"  sector-neutrality residual (IS active, max |sector$|/gross): {resid:.1e}")

    # ---- machine-readable summary for the diary ----
    print(
        "\nSUMMARY_JSON "
        + json.dumps(
            {
                "n_broad": len(broad_cols),
                "n_sectors": n_sectors,
                "standalone_broad": {
                    n: round(ct.msharpe(nets[n], ct.LO0, ct.OOS_CUTOFF), 3) for n in FACTORS
                },
                "selected": members,
                "broad_combo": {
                    k: {"sharpe": round(ct.msharpe(v, ct.LO0, ct.OOS_CUTOFF), 3), **n_pos_dict(v)}
                    for k, v in combo_nets.items()
                },
                "hybrid69": {
                    "sharpe": round(r69["sharpe"], 3),
                    "npos": r69["npos"],
                    "nyr": r69["nyr"],
                },
                "n_cov69": len(cov69),
                "leak_ok": bool(ok),
            }
        )
    )


def n_pos_dict(net: pd.Series) -> dict:
    npos, nyr = n_pos_years(net)
    return {"npos": npos, "nyr": nyr}


if __name__ == "__main__":
    main()

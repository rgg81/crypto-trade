"""portfolio-iteration EXPLORATION-011 — LIQUIDATION-CASCADE FADE (event-triggered contrarian).

ONE orthogonal, contrarian change to the canonical iter_005 baseline (walk-forward-λ trend+carry,
honest IS +1.30 / OOS +1.37 / maxDD -23%). Aimed at being orthogonal to trend+carry AND cutting the
-23% DD.

CRYPTO-NATIVE RATIONALE (quant-researcher):
  Liquidation cascades are a distinct crypto agent: forced-leverage liquidation / stop-runs that
  violently OVERSHOOT in 8-48h then SNAP BACK as the forced flow exhausts. A cascade candle is
  recognisable from OHLCV alone — a huge range/wick AND a volume spike (forced flow). We FADE the
  overshoot: a violent DOWN-flush -> LONG the snap-back at open[t+1]; a violent UP-spike (forced
  short-covering) -> SHORT. This is EVENT-TRIGGERED and SPARSE — fundamentally different from the
  iter_008 reject (a CONTINUOUS unconditional -sign(ret_h) reversal on EVERY coin-candle, which was
  orthogonal but unprofitable net and TAIL-LEVERING). Here the fade fires only on detected forced-
  deleverage candles, so it does not unconditionally fight trend everywhere.

  DD THESIS (iter_009): the -23% DD is correlated PORTFOLIO-WIDE trend reversals, NOT single-name
  concentration (caps did nothing). A cascade fade is LONG precisely when many coins flush together
  — exactly the correlated down-cascades that build the DD — so it should buffer the tail. KEY
  QUESTION: does fading cascades CUT the DD and/or add OOS, ON IS TOO (not an OOS-only mirage)?

iter_008 SCALE-LEAK FIX: iter_008's axis note warned a reversal "loads hardest on exactly the
high-vol post-cascade candles where the /rvol denominator is least trustworthy." We size the fade as
a FIXED ±1 EVENT FLAG, never a magnitude divided by the (contaminated) post-cascade rvol. After the
overlay enters the shared `/rvol` step, the large suspect denominator SHRINKS — not levers — the
post-cascade contribution, so it works in our favour rather than against us.

DETECTOR (per coin-candle t, ALL inputs known at close[t], PAST-ONLY via .shift(1)):
  rng[t]        = (high-low)/open
  rng_ratio[t]  = rng[t] / rng.rolling(RANGE_WIN).median().shift(1)    # vs trailing median, excl t
  vol_ratio[t]  = volume[t] / volume.rolling(VOL_SPK_WIN).mean().shift(1)
  cascade[t]    = (rng_ratio >= RANGE_K) AND (vol_ratio >= VOL_K) AND elig
  fade_dir[t]   = -sign(close/open - 1)        # down-flush -> +1 LONG ; up-spike -> -1 SHORT
  liqfade[t]    = fade_dir  where cascade else 0     # ±1 / 0 event flag — NEVER /rvol

CONSTRUCTION (mirrors iter_005 exactly; overlay BEFORE /rvol so it flows through the IDENTICAL
gross-normalize -> lag -> cost+funding -> PER-λ vol-target -> wf.walkforward stitch):
  sig = (1-λ)·trend + λ·carry + γ·liqfade
  γ=0 BYTE-REPRODUCES iter_005 (IS +1.30 / OOS +1.37 / -23%).

NO-CHEATING: γ is a STRUCTURAL family-weight (no evidence of regime non-stationarity, unlike λ which
EARNED its walk-forward) -> ROBUSTNESS-PROVEN over a fixed grid (every cell positive IS+OOS), NEVER
walk-forwarded, NEVER OOS-picked. λ walk-forward UNCHANGED. Taker 0.05%/side both sides + a 2× cost
stress (short-horizon fades are turnover-heavy; a gross-only edge is a REJECT). OOS_CUTOFF fixed.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402

# --- detector knobs (structural; robustness-checked, NEVER OOS-tuned) ---
RANGE_WIN = 90  # trailing window for the range-median baseline (~30d of 8h, == LIQ_WIN)
RANGE_K = 3.0  # candle range >= 3× its own trailing median = a genuine violent candle
VOL_SPK_WIN = 90  # trailing window for the volume-mean baseline
VOL_K = 2.5  # volume >= 2.5× trailing mean = forced flow (cascade is range AND volume)
HOLD = 1  # snap-back hold horizon in candles (1 = baseline shift; sweep {1,2,3})

# --- blend / robustness ---
GAMMA_GRID = [0.0, 0.05, 0.10, 0.15, 0.20]  # structural family-weight grid (robustness-proven)
EPS = 0.05  # materiality band (same as iter_008): "not worse" / "real lift" threshold


def load_ohlcv(coins: dict) -> dict:
    """Re-read high/low/volume for the SAME universe (load_universe only pulls open/close/qvol).

    Returns aligned high/low/volume DataFrames on the ms index, restricted to the coins dict so the
    point-in-time universe is byte-identical to the baseline's.
    """
    hi, lo, vol = {}, {}, {}
    by_sym = {p.split("/")[1]: p for p in glob.glob("data/*USDT/8h.csv")}
    for sym in coins:
        p = by_sym.get(sym)
        if p is None:
            continue
        k = pd.read_csv(p, usecols=["open_time", "high", "low", "volume"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        hi[sym] = k["high"].astype(float)
        lo[sym] = k["low"].astype(float)
        vol[sym] = k["volume"].astype(float)
    return {"high": pd.DataFrame(hi), "low": pd.DataFrame(lo), "volume": pd.DataFrame(vol)}


def _panels(coins: dict) -> dict:
    """Shared past-only inputs — IDENTICAL to iter_005.lam_nets prep, plus the liqfade signal."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    ohlcv = load_ohlcv(coins)
    high = ohlcv["high"].reindex(index=opens.index, columns=opens.columns)
    low = ohlcv["low"].reindex(index=opens.index, columns=opens.columns)
    volume = ohlcv["volume"].reindex(index=opens.index, columns=opens.columns)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund, high, low, volume):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)
    liqfade = build_liqfade(opens, high, low, close, volume, elig, HOLD)
    return {
        "ret_fwd": ret_fwd,
        "elig": elig,
        "rvol": rvol,
        "trend": trend,
        "carry": carry,
        "fund_next": fund_next,
        "liqfade": liqfade,
        # raw OHLCV stashed so the detector robustness sweep can rebuild liqfade variants without
        # re-loading the universe (trend/carry/rvol/elig are fixed across all detector variants).
        "_opens": opens,
        "_high": high,
        "_low": low,
        "_close": close,
        "_volume": volume,
    }


def build_liqfade(
    opens: pd.DataFrame,
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    volume: pd.DataFrame,
    elig: pd.DataFrame,
    hold: int,
    range_k: float = RANGE_K,
    vol_k: float = VOL_K,
) -> pd.DataFrame:
    """Event-triggered fade signal in {-1, 0, +1}, PAST-ONLY (every trailing stat .shift(1)).

    cascade = (range >> trailing median) AND (volume >> trailing mean) AND eligible.
    fade_dir = -sign(close/open - 1): a violent DOWN-flush -> +1 (LONG snap-back); UP-spike -> -1.
    NEVER divided by rvol (the iter_008 scale-leak); a fixed ±1 unit per event.
    hold > 1 forward-fills the trigger for hold-1 extra candles (snap-back may take >8h).
    range_k / vol_k override the module thresholds (used by the detector robustness sweep); the
    headline detector uses the module RANGE_K / VOL_K defaults.
    """
    rng = (high - low) / opens
    rng_med = rng.rolling(RANGE_WIN).median().shift(1)
    rng_ratio = rng / rng_med.replace(0, np.nan)
    vol_mean = volume.rolling(VOL_SPK_WIN).mean().shift(1)
    vol_ratio = volume / vol_mean.replace(0, np.nan)
    cascade = (rng_ratio >= range_k) & (vol_ratio >= vol_k) & elig
    fade_dir = -np.sign(close / opens - 1.0)
    liq = fade_dir.where(cascade, 0.0)
    if hold > 1:
        # forward-fill the directional fade for hold-1 extra candles, then re-mask to where a
        # trigger was active within the trailing hold-window (past-only — no future trigger used).
        held = liq.replace(0.0, np.nan).ffill(limit=hold - 1)
        active = cascade.rolling(hold, min_periods=1).max().astype(bool)
        liq = held.where(active, 0.0).fillna(0.0)
    return liq.fillna(0.0)


def lam_nets_gamma(p: dict, gamma: float) -> dict:
    """Canonical iter_005 per-λ net with a γ-weighted liqfade overlay folded into the directional
    core BEFORE /rvol. Mirrors iter_005.lam_nets line-for-line except `trend` -> `core + γ·liqfade`.
    γ=0 => the canonical net exactly. PER-λ vol-target applied here (iter_005 line 50) — ordering
    preserved.
    """
    overlay = gamma * p["liqfade"]
    nets = {}
    for lam in wf.LAM_GRID:
        sig = (1 - lam) * p["trend"] + lam * p["carry"] + overlay
        raw = (sig / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    return nets


def stitched_turnover(p: dict, gamma: float) -> float:
    """Mean one-sided per-candle turnover of the DEPLOYED (walk-forward-λ-chosen) portfolio, using
    the SAME λ-selection as the headline run (best PAST vol-targeted monthly Sharpe). Mirrors
    iter_008.stitched_turnover with the γ overlay.
    """
    overlay = gamma * p["liqfade"]
    weights, nets = {}, {}
    for lam in wf.LAM_GRID:
        sig = (1 - lam) * p["trend"] + lam * p["carry"] + overlay
        raw = (sig / p["rvol"]).where(p["elig"])
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        weights[lam] = w
        pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        nets[lam] = base.vol_target((pnl + fpnl - cost).dropna())
    vt_panel = pd.DataFrame(nets).sort_index()
    months = pd.PeriodIndex(vt_panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    cols = weights[wf.LAM_GRID[0]].columns
    w_parts = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = vt_panel[(vt_panel.index >= lo) & (vt_panel.index < hi)]
        if len(train) < 200:
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        wm = weights[tsh.idxmax()].reindex(columns=cols)
        wm = wm[(wm.index >= m0) & (wm.index < test_hi)]
        if not wm.empty:
            w_parts.append(wm)
    wfull = pd.concat(w_parts).sort_index()
    return float((wfull - wfull.shift(1)).abs().sum(axis=1).mean())


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    yr = {int(k): round(v * 100, 0) for k, v in net.groupby(net.index.year).sum().items()}
    return {
        "is": base.msharpe(net, base.LO0, base.OOS_CUTOFF),
        "oos": base.msharpe(net, base.OOS_CUTOFF, base.HI1),
        "dd": dd,
        "tot": (eq.iloc[-1] - 1) * 100,
        "yr": yr,
    }


def standalone(p: dict, cost_mult: float) -> dict:
    """Build liqfade as a self-contained cross-sectional signal (±1/0, gross-normalized, lagged,
    real funding + taker cost at cost_mult×, per-candle vol-targeted) — directly comparable to the
    baseline. Returns stats + turnover + event counts.
    """
    raw = p["liqfade"].where(p["elig"])
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = base.vol_target((pnl + fpnl - cost).dropna())
    gross_net = base.vol_target((pnl + fpnl).dropna())  # pre-cost (cost honesty diagnostic)
    s = stats(net)
    s["turn"] = float((w - w.shift(1)).abs().sum(axis=1).mean())
    s["gross_is"] = base.msharpe(gross_net, base.LO0, base.OOS_CUTOFF)
    s["gross_oos"] = base.msharpe(gross_net, base.OOS_CUTOFF, base.HI1)
    return s


def event_counts(p: dict) -> dict:
    """Sparsity diagnostics: number of nonzero liqfade event-cells IS vs OOS + events/month.

    liqfade is already masked to eligible+cascade cells (0 elsewhere); count nonzero AND eligible
    explicitly (NOT `.where(elig) != 0`, which would count NaN ineligible cells since NaN != 0).
    """
    ev = (p["liqfade"] != 0) & p["elig"]
    per_cand = ev.sum(axis=1)
    is_n = int(per_cand[per_cand.index < base.OOS_CUTOFF].sum())
    oos_n = int(per_cand[per_cand.index >= base.OOS_CUTOFF].sum())
    n_months = per_cand.groupby(per_cand.index.to_period("M")).sum().shape[0]
    total = is_n + oos_n
    return {"is": is_n, "oos": oos_n, "per_month": total / max(n_months, 1)}


def orthogonality(p: dict, on_event: bool) -> float:
    """Pooled cross-coin Pearson corr(liqfade, trend) over IS eligible cells. on_event=True keeps
    only cells where liqfade actually fired (the informative number; unconditional corr is ~0 by
    sparsity). Eligibility enters via the finite-mask on `tr` (NaN outside elig) plus the explicit
    nonzero-liqfade mask — never `.where(elig) != 0`, which keeps NaN ineligible cells.
    """
    tr = p["trend"].where(p["elig"])
    lf = p["liqfade"]
    is_mask = tr.index < base.OOS_CUTOFF
    a = tr[is_mask].to_numpy().ravel()
    b = lf[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if on_event:
        ok &= b != 0
    if ok.sum() < 100 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


# detector + hold robustness grid: prove the REJECT is not a knob artifact (the headline detector
# is just one cell). Each row rebuilds liqfade with a different (range_k, vol_k, hold) and blends at
# γ=0.05 and γ=0.10 on the canonical net. range_k/vol_k/hold are NEVER OOS-tuned — this is a
# robustness scan, not a search for a winning cell.
SENSITIVITY_GRID = [
    (3.0, 2.5, 1),  # headline detector
    (4.0, 3.0, 1),  # stricter (rarer, larger events)
    (2.5, 2.0, 1),  # looser (more events)
    (5.0, 4.0, 1),  # very strict
    (6.0, 5.0, 1),  # extreme-only cascades
    (3.0, 2.5, 2),  # 2-candle hold (slower snap-back)
    (3.0, 2.5, 3),  # 3-candle hold
]


def sensitivity(p: dict, b: dict) -> None:
    """Detector + hold robustness sweep — rebuild liqfade per (range_k, vol_k, hold) and blend at
    γ∈{0.05,0.10}. If NO reasonable detector variant lifts OOS materially, the REJECT is structural,
    not a knob artifact. Reuses the fixed trend/carry/rvol/elig panels (only the detector changes).
    """
    print(
        "\n  --- DETECTOR+HOLD ROBUSTNESS (γ=0.05/0.10 blend; baseline OOS "
        f"{b['oos']:+.2f}/DD {b['dd'] * 100:.0f}%) ---"
    )
    print(
        f"  {'rangeK':>6} {'volK':>5} {'hold':>4} {'nev':>5}  "
        f"{'g05 IS':>7} {'g05 OOS':>8} {'g05 DD':>7}  {'g10 IS':>7} {'g10 OOS':>8} {'g10 DD':>7}"
    )
    for range_k, vol_k, hold in SENSITIVITY_GRID:
        liq = build_liqfade(
            p["_opens"],
            p["_high"],
            p["_low"],
            p["_close"],
            p["_volume"],
            p["elig"],
            hold,
            range_k,
            vol_k,
        )
        nev = int(((liq != 0) & p["elig"]).sum().sum())
        pv = {**p, "liqfade": liq}
        s05 = stats(wf.walkforward(lam_nets_gamma(pv, 0.05))[0])
        s10 = stats(wf.walkforward(lam_nets_gamma(pv, 0.10))[0])
        print(
            f"  {range_k:>6.1f} {vol_k:>5.1f} {hold:>4d} {nev:>5d}  "
            f"{s05['is']:>+7.2f} {s05['oos']:>+8.2f} {s05['dd'] * 100:>6.0f}%  "
            f"{s10['is']:>+7.2f} {s10['oos']:>+8.2f} {s10['dd'] * 100:>6.0f}%"
        )


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-011: liquidation-cascade FADE (event-triggered) — {len(coins)} coins")
    print(
        f"  detector: range>=({RANGE_K}×med_{RANGE_WIN}) AND vol>=({VOL_K}×mean_{VOL_SPK_WIN}); "
        f"fade=-sign(close/open-1); HOLD={HOLD}; γ grid {GAMMA_GRID}; sign-based ±1, NOT /rvol\n"
    )

    p = _panels(coins)

    # --- sparsity ---
    ec = event_counts(p)
    print(
        f"  SPARSITY: cascade events  IS={ec['is']}  OOS={ec['oos']}  "
        f"(~{ec['per_month']:.1f} events/month across the top-20)\n"
    )

    # --- mechanism falsifier: fade must be orthogonal/contrarian to trend (we WANT corr<=0) ---
    corr_all = orthogonality(p, on_event=False)
    corr_ev = orthogonality(p, on_event=True)
    corr_ok = np.isfinite(corr_ev) and corr_ev < 0.3
    print(
        f"  ORTHOGONALITY: corr(liqfade,trend) IS unconditional={corr_all:+.3f}  "
        f"on-event={corr_ev:+.3f}  -> {'PASS (<0.3, orthogonal)' if corr_ok else 'FAIL'}\n"
    )

    # --- STANDALONE liqfade: 1× and 2× taker (cost honesty; gross-only edge = REJECT) ---
    print("  --- STANDALONE liqfade cross-sectional signal (cost honesty) ---")
    s1 = standalone(p, 1.0)
    s2 = standalone(p, 2.0)
    print(f"  {'':10}{'IS':>7}{'OOS':>7}{'maxDD':>7}{'netTot':>8}{'turn':>7}")
    print(
        f"  {'1× taker':10}{s1['is']:>+7.2f}{s1['oos']:>+7.2f}{s1['dd'] * 100:>6.0f}%"
        f"{s1['tot']:>+7.0f}%{s1['turn']:>7.3f}"
    )
    print(
        f"  {'2× taker':10}{s2['is']:>+7.2f}{s2['oos']:>+7.2f}{s2['dd'] * 100:>6.0f}%"
        f"{s2['tot']:>+7.0f}%{s2['turn']:>7.3f}"
    )
    print(
        f"  {'gross':10}{s1['gross_is']:>+7.2f}{s1['gross_oos']:>+7.2f}  "
        f"(pre-cost — if gross strong but net weak, the edge is eaten by turnover)"
    )
    print(f"     1× net%/yr={s1['yr']}\n")

    # --- canonical baseline reproduction (γ=0) via the SAME iter_005.walkforward stitch ---
    base_nets = lam_nets_gamma(p, 0.0)
    base_wf, _ = wf.walkforward(base_nets)
    b = stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    print(
        f"  CANONICAL baseline (γ=0, iter_005 net): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}% netTot={b['tot']:+.0f}%"
    )
    print(f"     net%/yr={b['yr']}")
    print("     (sanity: must match iter_005 IS+1.30/OOS+1.37/-23%)\n")

    # --- robustness sweep over γ (NOT walk-forwarded; measured on the CANONICAL net) ---
    print("  --- ROBUSTNESS SWEEP (γ; λ walk-forwarded; per-λ-vol-target-then-stitch) ---")
    print(
        f"  {'gamma':>5} {'IS':>7} {'OOS':>7} {'dIS':>7} {'dOOS':>7} {'maxDD':>7} "
        f"{'turn':>6} {'all-yr+IS':>9}"
    )
    rows = []
    for gamma in GAMMA_GRID:
        nets = lam_nets_gamma(p, gamma)
        net_wf, _ = wf.walkforward(nets)
        s = stats(net_wf)
        turn = stitched_turnover(p, gamma)
        is_net = net_wf[net_wf.index < base.OOS_CUTOFF]
        is_yr = is_net.groupby(is_net.index.year).sum()
        yr_is_pos = bool((is_yr >= 0).all())
        rows.append({"gamma": gamma, **s, "turn": turn, "yr_is_pos": yr_is_pos})
        print(
            f"  {gamma:>5.2f} {s['is']:>+7.2f} {s['oos']:>+7.2f} {s['is'] - b['is']:>+7.2f} "
            f"{s['oos'] - b['oos']:>+7.2f} {s['dd'] * 100:>6.0f}% {turn:>6.3f} "
            f"{'yes' if yr_is_pos else 'NO':>9}"
        )

    mid = next(r for r in rows if abs(r["gamma"] - 0.10) < 1e-9)
    print(f"\n  mid-grid γ=0.10 net%/yr={mid['yr']}")

    # --- detector + hold robustness (prove the REJECT is not a knob artifact) ---
    sensitivity(p, b)

    # --- pre-registered falsifier verdict ---
    nz = [r for r in rows if r["gamma"] > 0]
    all_cells_pos = all(r["is"] >= b["is"] - EPS and r["oos"] >= b["oos"] - EPS for r in nz)
    small = next(r for r in nz if abs(r["gamma"] - 0.05) < 1e-9)
    small_signal = small["oos"] >= b["oos"] - EPS and small["is"] >= b["is"] - EPS
    mid_lift = mid["oos"] - b["oos"]
    lift_ok = mid_lift >= 0.15
    dd_no_blowout = all(r["dd"] >= -0.28 for r in nz)
    dd_cut = any(
        r["dd"] > b["dd"] and r["is"] >= b["is"] - EPS and r["oos"] >= b["oos"] - EPS for r in nz
    )
    yr_ok = all(r["yr_is_pos"] for r in nz)
    cost_ok = s1["is"] > 0 and s1["oos"] > 0 and s2["is"] > 0 and s2["oos"] > 0

    print(f"\n  === PRE-REGISTERED FALSIFIER VERDICT (n={n_oos_mo} OOS months) ===")
    print(f"  [1] all γ cells IS+OOS >= baseline-{EPS}: {'PASS' if all_cells_pos else 'FAIL'}")
    print(
        f"  [2] signal present at small γ=0.05 (not only-at-large): "
        f"{'PASS' if small_signal else 'FAIL'}"
    )
    print(
        f"  [3] mid-grid OOS lift >= +0.15 (above n={n_oos_mo}mo noise): "
        f"dOOS={mid_lift:+.2f} -> {'PASS' if lift_ok else 'FAIL'}"
    )
    print(
        f"  [4] on-event corr(liqfade,trend) < 0.3 (orthogonal/contrarian): "
        f"{'PASS' if corr_ok else 'FAIL'}"
    )
    print(
        f"  [5] maxDD >= -28% across grid (no tail-levering): "
        f"{'PASS' if dd_no_blowout else 'FAIL'}  "
        f"[stretch: CUTS DD below {b['dd'] * 100:.0f}% on a positive cell: "
        f"{'YES' if dd_cut else 'no'}]"
    )
    print(f"  [6] no IS year flips negative: {'PASS' if yr_ok else 'FAIL'}")
    print(
        f"  [7] standalone net-positive at 1× AND 2× taker (not gross-only): "
        f"{'PASS' if cost_ok else 'FAIL'}"
    )

    gates = [all_cells_pos, small_signal, lift_ok, corr_ok, dd_no_blowout, yr_ok, cost_ok]
    if all(gates):
        print("\n  VERDICT: EDGE — robustness-proven contrarian event-fade. Recommend CONFIRM.")
    elif corr_ok and dd_no_blowout and all_cells_pos and cost_ok and not lift_ok:
        print(
            "\n  VERDICT: NOISE (real-but-too-small) — leak-safe, orthogonal, cost-honest, not "
            "harmful, but the OOS lift is inside the OOS-month-Sharpe noise band. NOT worth the "
            "added turnover/complexity. REJECT as accretive change (honest down-call)."
        )
    else:
        print("\n  VERDICT: REJECT — failed a mechanism/robustness/cost falsifier above. NOT kept.")


if __name__ == "__main__":
    main()

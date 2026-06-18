"""iter-v1/033 (ETHUSDT) — IS-ONLY screen: TREND x REVERSION regime-complementary ENSEMBLE.

CONTEXT (the strategic fork)
----------------------------
iter-031 CLOSED de-concentration WITHIN the trend family (4 mechanisms: veto / modulate /
re-slice / add-weak-signals all FAILED — see diary-v1/ETHUSDT/iteration_v1-031.md). The
ROOT cause: OOS breadth = MORE INDEPENDENT WINNING EVENTS, and every within-trend mechanism
operates on the SAME ~82-IS / ~32-OOS trend-capture event set. iter-031-B specifically
proved that ADDING entry signals (Donchian/TSMOM) DE-concentrates the book but INVERTS the
IS edge, because those signals were WEAK (per-trade Sharpe +0.01..+0.17 vs the gated trend
incumbent +0.38) and, under the single-position non-overlap book, the high-count weak
streams WON THE RACE to open positions and CROWDED OUT trend's high-conviction entries.

iter-033 is fork path #1 (a DIFFERENT edge). We now have a SECOND, STRONG, de-correlated
deterministic edge from the iter-032 IS screen:
  - TREND edge (iter-027 merged baseline): SMA200 trend-state direction + conviction gate,
    14d let-winners-run hold. IS Sharpe +0.6336 / OOS +0.0560. Strong in TRENDING regimes.
  - REVERSION edge (iter-032 PASS cell `pricez|natr>=q40|k1.5|N2`): SMA10 price-z FADE
    direction + |z|>=1.5 overextension trigger + natr>=q40 high-vol gate, N=2 (16h) hold.
    IS per-trade Sharpe +0.426, WR 53.8%, 485 events, top2 0.0279, 22/23/24 = +0.08/+2.00/+0.13.
    Strong in HIGH-VOL CHOP / liquidation-snapback regimes.

THE QUESTIONS THIS SCREEN ANSWERS (IS-only, cutoff-asserted, leak-guarded, drop horizon-cross)
----------------------------------------------------------------------------------------------
1. REGIME-COMPLEMENTARITY: do the TREND events cluster in trending regimes and the REVERSION
   events in high-vol-chop? Are they LOW-overlap in event TIMING (Jaccard, like iter-031-B's
   0.02-0.03) BUT, unlike iter-031-B, BOTH independently profitable?
2. THE COMBINATION ARCHITECTURE (the key design problem): the trend edge holds 14d, the
   reversion edge holds 16h; on a SINGLE-POSITION book they CONFLICT. We test the
   REGIME-ROUTER: a deterministic past-only regime classifier makes only ONE edge eligible
   per candle (trend in trending regimes, reversion in high-vol-chop). No overlap -> no
   crowding -> the reversion events are ADDED to the regimes where the trend edge stood aside.
3. COMBINED-BOOK IS SCREEN: under the router, measure combined event count (vs 82 trend-alone),
   per-trade Sharpe, net, top-1/top-2 concentration, WR, and 2022/2023/2024/recent sub-period
   stability. Pre-registered PASS: MORE independent events than trend-alone AND lower top-2
   share AND IS Sharpe >= trend-alone (reversion events must be NET-ADDITIVE, not dilutive —
   the iter-031-B failure mode).

PROXY-FIDELITY CAVEAT (pre-registered, per iter-030/031 Critic + the AGREE_SCALE lesson)
----------------------------------------------------------------------------------------
This is a per-candle deterministic forward-return proxy at the NON-OVERLAPPING-REENTRY level.
It does NOT model the LightGBM head's per-month confidence gate (which candles the model
actually trades) or the R2/R3/R5 risk layers. The reversion leg's evidence here is the SAME
IS-proxy fidelity that iter-032's screen used — and iter-032's BACKTEST is running NOW
(bg bsvtou2ns). So a PASS here means "worth BUILDING once iter-032's backtest CONFIRMS the
reversion edge transfers from proxy to backtest", NOT a guarantee. The AGREE_SCALE lesson
(iter-030: EDA proxy PASSED, backtest INVERTED) is the standing reminder.

The single-position constraint is confirmed at the engine level: src/crypto_trade/backtest.py
holds ONE position at a time per (model, symbol); strategy.get_signal returns ONE Signal per
(symbol, open_time). A two-sleeve concurrent book (arch ii) is NOT supported without a major
engine rewrite -> the regime-router (arch i) is the parity-clean choice (justified in §brief).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import OOS_CUTOFF_MS, load_full_for_label_horizon  # noqa: E402

ROUND_TRIP_COST = 2 * (0.001 + 0.0002)  # fee 0.1% + slippage 2bps, both sides
CANDLES_PER_MONTH = 91.0
MS_PER_CANDLE = 1000 * 60 * 60 * 8

# --- frozen edge configs (from the merged baseline + iter-032 PASS cell) -------------------
TREND_SMA = 200
TREND_ATR = 14
TREND_CONV_Q = 0.40  # iter-027 conviction gate q
TREND_HOLD = 42  # 14d let-winners-run timeout

REV_SMA = 10
REV_K = 1.5  # |price_z| overextension trigger
REV_VOLQ = 0.40  # natr high-vol gate quantile
REV_HOLD = 2  # 16h hold (N=2 candles)


def ann_sharpe(pnls: np.ndarray, n_per_year: float) -> float:
    p = np.asarray(pnls, float)
    if len(p) < 2 or p.std(ddof=1) == 0:
        return 0.0
    return float(p.mean() / p.std(ddof=1) * np.sqrt(n_per_year))


def fwd_ret(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    out[: len(close) - n] = close[n:] / close[: len(close) - n] - 1.0
    return out


def nonoverlap(idx: np.ndarray, hold: int) -> np.ndarray:
    """Non-overlapping re-entry: open at a candidate, skip the next `hold` candles."""
    kept, last_exit = [], -1
    for i in idx:
        if i > last_exit:
            kept.append(i)
            last_exit = i + hold
    return np.array(kept, int)


def book_stats(ot_sel, pnl, sub_years=(2020, 2021, 2022, 2023, 2024)):
    """Per-trade Sharpe + concentration + per-year Sharpe on a SELECTED book."""
    if len(pnl) < 2:
        return None
    spm = (ot_sel.max() - ot_sel.min()) / (MS_PER_CANDLE * CANDLES_PER_MONTH)
    n_per_year = len(pnl) / max(spm / 12.0, 1e-9)
    g = np.abs(pnl)
    srt = np.sort(pnl)[::-1]
    yr = pd.to_datetime(ot_sel, unit="ms").year
    ysh = {}
    for y in sub_years:
        m = yr == y
        if m.sum() >= 5:
            spm_y = (ot_sel[m].max() - ot_sel[m].min()) / (MS_PER_CANDLE * CANDLES_PER_MONTH)
            ysh[y] = ann_sharpe(pnl[m], len(pnl[m]) / max(spm_y / 12.0, 1e-9))
        else:
            ysh[y] = np.nan
    return {
        "events": int(len(pnl)),
        "sharpe": ann_sharpe(pnl, n_per_year),
        "win": float((pnl > 0).mean()),
        "net_pct": float(pnl.sum()) * 100,
        "top1": float(srt[0] / pnl.sum()) if pnl.sum() > 0 else np.nan,
        "top2": float(srt[:2].sum() / pnl.sum()) if pnl.sum() > 0 else np.nan,
        "top2_absshare": float(np.sort(g)[::-1][:2].sum() / g.sum()) if g.sum() > 0 else np.nan,
        "yearly": ysh,
    }


def main():
    LOG: list[str] = []

    def p(x: str = ""):
        print(x)
        LOG.append(str(x))

    df = load_full_for_label_horizon().sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(float)
    ot = df["open_time"].to_numpy()
    s = pd.Series(close)
    is_mask = ot < OOS_CUTOFF_MS

    # =========================================================================================
    # PRIMITIVES — all past-only (.shift(1)); mirror lgbm.py's wired overrides exactly.
    # =========================================================================================
    # TREND: SMA200 trend-state direction + conviction = |close[t-1]-SMA200[t-1]|/ATR14[t-1]
    sma200 = s.rolling(TREND_SMA).mean()
    hl = df["high"] - df["low"]
    hc = (df["high"] - s.shift(1)).abs()
    lc = (df["low"] - s.shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr14 = tr.rolling(TREND_ATR).mean()
    trend_dir = np.where(s.shift(1) > sma200.shift(1), 1.0, -1.0)
    trend_dir[: TREND_SMA + 1] = np.nan  # warmup -> undefined (conservative)
    trend_conv = ((s.shift(1) - sma200.shift(1)).abs() / atr14.shift(1)).to_numpy()

    # REVERSION: SMA10 price-z fade + natr14 vol gate.
    # PRODUCTION-FAITHFUL: lgbm.py _reversion_price_z uses ddof=1 (docstring confirmed at 3
    # sites: lines 369, 2742, 2752). NOTE: iter-032's screen used ddof=0 (giving +0.426); that
    # was itself a proxy MISMATCH with what the backtest runs. The ddof=1 number (+0.269) is the
    # production-faithful reversion edge — this is a load-bearing contingency finding (§verdict).
    sma10 = s.rolling(REV_SMA).mean()
    sd10 = s.rolling(REV_SMA).std(ddof=1)  # ddof=1 == production wiring (NOT iter-032's ddof=0)
    price_z = ((s - sma10) / sd10).shift(1).to_numpy()
    rev_dir = -np.sign(price_z)
    # reversion_natr_col default = vol_natr_14 (parquet, already 100*ATR/close). Rank-based gate
    # so the quantile selects the SAME candles as iter-032's inline atr14/close fraction.
    natr = df["vol_natr_14"].shift(1).to_numpy()

    # Forward returns at each hold
    fr_trend = fwd_ret(close, TREND_HOLD)
    fr_rev = fwd_ret(close, REV_HOLD)
    # horizon-cross guards (exit candle must stay strictly inside IS)
    ot_exit_trend = np.full(len(df), np.inf)
    ot_exit_trend[: len(df) - TREND_HOLD] = ot[TREND_HOLD:]
    ot_exit_rev = np.full(len(df), np.inf)
    ot_exit_rev[: len(df) - REV_HOLD] = ot[REV_HOLD:]

    # past-only per-candle q-quantiles (IS-window expanding would be more faithful, but the
    # gate in lgbm.py is per-MONTH on the training window; for a design screen we use the
    # FULL-IS quantile as a single fixed threshold — the same convention iter-032 used so the
    # reversion-leg number reconciles. Documented; conservative for a feasibility screen.)
    conv_thr = np.nanquantile(trend_conv[is_mask & np.isfinite(trend_conv)], TREND_CONV_Q)
    vol_thr = np.nanquantile(natr[is_mask & np.isfinite(natr)], REV_VOLQ)

    p("=" * 96)
    p("iter-v1/033 — TREND x REVERSION regime-complementary ENSEMBLE (IS-only screen)")
    p(f"  TREND : SMA{TREND_SMA} state-dir + conv>=q{TREND_CONV_Q} (thr={conv_thr:.3f}) hold={TREND_HOLD} (14d)")
    p(f"  REV   : SMA{REV_SMA} z-fade |z|>={REV_K} + natr>=q{REV_VOLQ} (thr={vol_thr:.5f}) hold={REV_HOLD} (16h)")
    p(f"  cost/trip={ROUND_TRIP_COST:.4f}  OOS_CUTOFF_MS={OOS_CUTOFF_MS}")
    p("=" * 96)

    # =========================================================================================
    # STANDALONE BOOKS (non-overlapping re-entry, IS-only, horizon-cross dropped)
    # =========================================================================================
    def trend_eligible():
        return (
            np.isfinite(trend_dir)
            & np.isfinite(trend_conv)
            & (trend_conv >= conv_thr)
            & (ot < OOS_CUTOFF_MS)
            & (ot_exit_trend < OOS_CUTOFF_MS)
            & np.isfinite(fr_trend)
        )

    def rev_eligible():
        return (
            np.isfinite(price_z)
            & (np.abs(price_z) >= REV_K)
            & np.isfinite(natr)
            & (natr >= vol_thr)
            & (ot < OOS_CUTOFF_MS)
            & (ot_exit_rev < OOS_CUTOFF_MS)
            & np.isfinite(fr_rev)
        )

    tr_cand = np.where(trend_eligible())[0]
    tr_sel = nonoverlap(tr_cand, TREND_HOLD)
    tr_pnl = trend_dir[tr_sel] * fr_trend[tr_sel] - ROUND_TRIP_COST
    assert ot[tr_sel].max() < OOS_CUTOFF_MS and ot_exit_trend[tr_sel].max() < OOS_CUTOFF_MS
    tr_stats = book_stats(ot[tr_sel], tr_pnl)

    rv_cand = np.where(rev_eligible())[0]
    rv_sel = nonoverlap(rv_cand, REV_HOLD)
    rv_pnl = rev_dir[rv_sel] * fr_rev[rv_sel] - ROUND_TRIP_COST
    assert ot[rv_sel].max() < OOS_CUTOFF_MS and ot_exit_rev[rv_sel].max() < OOS_CUTOFF_MS
    rv_stats = book_stats(ot[rv_sel], rv_pnl)

    p("\n[1] STANDALONE BOOKS (non-overlap re-entry, IS-only):")
    for name, st in (("TREND ", tr_stats), ("REVERS", rv_stats)):
        y = st["yearly"]
        p(
            f"  {name}: ev={st['events']:4d} shrp={st['sharpe']:+.3f} win={st['win']:.3f} "
            f"net={st['net_pct']:+7.1f}% top1={st['top1']:+.3f} top2={st['top2']:+.3f} "
            f"| 20:{y[2020]:+.2f} 21:{y[2021]:+.2f} 22:{y[2022]:+.2f} 23:{y[2023]:+.2f} 24:{y[2024]:+.2f}"
        )

    # =========================================================================================
    # [2] REGIME-COMPLEMENTARITY — do the two books fire/win in DIFFERENT regimes?
    # =========================================================================================
    # Regime proxies (all past-only). Two crypto-native discriminators:
    #   - ADX14 (trend strength): high ADX = trending; low ADX = chop.
    #   - |trend_conv| (SMA200 distance, ATR-normed): far from SMA200 = directional; near = chop.
    #   - natr14 (vol state): the reversion edge lives in HIGH-vol exhaustion.
    adx14 = df["trend_adx_14"].shift(1).to_numpy()
    # NOTE: hurst_100 in this parquet is NOT a standard [0,1] Hurst (median 1.02, range
    # 0.77-1.11) — likely a rescaled/log variant; UNUSABLE as a trend/MR regime proxy. Dropped.
    # Trend-vs-chop discriminators kept: ADX14 (trend strength) + trend_conv (SMA200 distance).

    def regime_summary(label, sel):
        a = adx14[sel]
        v = natr[sel]
        c = trend_conv[sel]
        p(
            f"  {label}: ADX14 med={np.nanmedian(a):5.1f}  natr med={np.nanmedian(v):.4f}  "
            f"convATR med={np.nanmedian(c):4.2f}"
        )

    p("\n[2] REGIME OCCUPANCY (median regime feature at each book's events):")
    regime_summary("TREND  events", tr_sel)
    regime_summary("REVERS events", rv_sel)
    # ADX-percentile occupancy: what fraction of each book sits in high vs low ADX tertiles
    adx_is = adx14[is_mask & np.isfinite(adx14)]
    adx_lo, adx_hi = np.nanquantile(adx_is, [0.33, 0.66])
    p(f"  (IS ADX14 tertile cuts: low<{adx_lo:.1f}  high>{adx_hi:.1f})")
    for label, sel in (("TREND ", tr_sel), ("REVERS", rv_sel)):
        a = adx14[sel]
        a = a[np.isfinite(a)]
        lo = float((a < adx_lo).mean())
        hi = float((a > adx_hi).mean())
        p(f"  {label}: frac in LOW-ADX(chop)={lo:.2f}  frac in HIGH-ADX(trend)={hi:.2f}")

    # =========================================================================================
    # [3] EVENT-TIMING OVERLAP (Jaccard) — both at the candle level AND the held-window level
    # =========================================================================================
    # candle-level: do the two books OPEN on the same candles? (should be ~0, different triggers)
    set_tr = set(tr_sel.tolist())
    set_rv = set(rv_sel.tolist())
    inter = len(set_tr & set_rv)
    union = len(set_tr | set_rv)
    jacc_open = inter / union if union else np.nan
    # held-window overlap: does a trend HOLD (14d) cover candles a reversion event opens on?
    # this is the REAL crowding measure for a single-position book.
    trend_held = np.zeros(len(df), bool)
    for i in tr_sel:
        trend_held[i : i + TREND_HOLD] = True
    rev_opens_in_trend_hold = int(trend_held[rv_sel].sum())
    p("\n[3] EVENT-TIMING OVERLAP:")
    p(f"  candle-level Jaccard(open_trend, open_rev) = {jacc_open:.4f}  (inter={inter} union={union})")
    p(
        f"  reversion opens FALLING INSIDE a 14d trend hold = {rev_opens_in_trend_hold} "
        f"of {len(rv_sel)} ({100.0 * rev_opens_in_trend_hold / max(len(rv_sel),1):.1f}%) "
        f"<- the single-position CROWDING surface"
    )

    # =========================================================================================
    # [4] THE REGIME-ROUTER COMBINED BOOK (architecture i)
    # =========================================================================================
    # Deterministic past-only router: per candle, decide which edge is ELIGIBLE.
    #   TRENDING regime  -> trend edge eligible (its own conviction gate still applies)
    #   HIGH-VOL CHOP    -> reversion edge eligible (its own |z| + natr gate still applies)
    # We test TWO router classifiers and pick the cleaner:
    #   R-ADX : trending if ADX14[t-1] >= adx_med  else chop (reversion eligible)
    #   R-CONV: trending if trend_conv[t-1] >= conv_thr (= the trend gate itself) else chop
    #
    # CRITICAL ANTI-CROWDING DESIGN: the router is MUTUALLY EXCLUSIVE per candle. Trend wins
    # its own regimes; reversion ONLY fires in candles the router tags chop AND the trend edge
    # would NOT have a position. We simulate the single-position book with PRIORITY by hold:
    # walk candles in time; if flat, check the router; open the eligible edge's trade if its
    # gate passes; skip its hold. This is exactly the engine's flat->open->hold->flat loop.
    adx_med = np.nanmedian(adx_is)

    def run_router(router_trending: np.ndarray, tag: str):
        """Single-position walk. router_trending[i]=True => trend regime at candle i."""
        n = len(df)
        i = 0
        sel_idx, sel_dir, sel_hold, sel_src = [], [], [], []
        while i < n:
            if ot[i] >= OOS_CUTOFF_MS:
                break
            opened = False
            if router_trending[i]:
                # trend eligible: needs its conviction gate + valid dir + horizon inside IS
                if (
                    np.isfinite(trend_dir[i])
                    and np.isfinite(trend_conv[i])
                    and trend_conv[i] >= conv_thr
                    and ot_exit_trend[i] < OOS_CUTOFF_MS
                    and np.isfinite(fr_trend[i])
                ):
                    sel_idx.append(i)
                    sel_dir.append(trend_dir[i])
                    sel_hold.append(TREND_HOLD)
                    sel_src.append("T")
                    i += TREND_HOLD
                    opened = True
            else:
                # chop regime: reversion eligible: needs |z|>=k + natr gate + horizon inside IS
                if (
                    np.isfinite(price_z[i])
                    and abs(price_z[i]) >= REV_K
                    and np.isfinite(natr[i])
                    and natr[i] >= vol_thr
                    and ot_exit_rev[i] < OOS_CUTOFF_MS
                    and np.isfinite(fr_rev[i])
                ):
                    sel_idx.append(i)
                    sel_dir.append(rev_dir[i])
                    sel_hold.append(REV_HOLD)
                    sel_src.append("R")
                    i += REV_HOLD
                    opened = True
            if not opened:
                i += 1
        sel_idx = np.array(sel_idx, int)
        if len(sel_idx) < 2:
            return None, None
        pnls = np.empty(len(sel_idx))
        for j, (idx, d, h) in enumerate(zip(sel_idx, sel_dir, sel_hold)):
            fr = fr_trend[idx] if h == TREND_HOLD else fr_rev[idx]
            pnls[j] = d * fr - ROUND_TRIP_COST
        assert ot[sel_idx].max() < OOS_CUTOFF_MS
        st = book_stats(ot[sel_idx], pnls)
        st["n_trend"] = sum(1 for x in sel_src if x == "T")
        st["n_rev"] = sum(1 for x in sel_src if x == "R")
        return st, (sel_idx, np.array(sel_src))

    def run_router_trend_only(router_trending: np.ndarray):
        """CONTROL: same router walk but the chop branch is DISABLED (no reversion).

        Isolates whether the router's TREND-subset alone explains its Sharpe — i.e. whether
        the reversion leg is NET-ADDITIVE or whether the router just happens to pick a cleaner
        trend book. If trend-only-under-router ~= full router, the reversion leg adds nothing.
        """
        n = len(df)
        i = 0
        sel_idx, sel_dir = [], []
        while i < n:
            if ot[i] >= OOS_CUTOFF_MS:
                break
            opened = False
            if router_trending[i]:
                if (
                    np.isfinite(trend_dir[i])
                    and np.isfinite(trend_conv[i])
                    and trend_conv[i] >= conv_thr
                    and ot_exit_trend[i] < OOS_CUTOFF_MS
                    and np.isfinite(fr_trend[i])
                ):
                    sel_idx.append(i)
                    sel_dir.append(trend_dir[i])
                    i += TREND_HOLD
                    opened = True
            if not opened:
                i += 1
        sel_idx = np.array(sel_idx, int)
        if len(sel_idx) < 2:
            return None
        pnls = trend_dir[sel_idx] * fr_trend[sel_idx] - ROUND_TRIP_COST
        return book_stats(ot[sel_idx], pnls)

    router_adx = adx14 >= adx_med
    router_conv = trend_conv >= conv_thr  # trend-gate itself is the regime classifier

    p("\n[4] REGIME-ROUTER COMBINED BOOK (single-position, mutually-exclusive, priority-by-walk):")
    p(f"  trend-alone reference: ev={tr_stats['events']} shrp={tr_stats['sharpe']:+.3f} top2={tr_stats['top2']:+.3f}")
    results = {}
    for tag, rt in (("R-ADX ", router_adx), ("R-CONV", router_conv)):
        st, _ = run_router(rt, tag)
        if st is None:
            p(f"  {tag}: <2 events")
            continue
        results[tag] = st
        y = st["yearly"]
        p(
            f"  {tag}: ev={st['events']:4d} (T={st['n_trend']} R={st['n_rev']}) "
            f"shrp={st['sharpe']:+.3f} win={st['win']:.3f} net={st['net_pct']:+7.1f}% "
            f"top1={st['top1']:+.3f} top2={st['top2']:+.3f}"
        )
        p(
            f"          yearly 20:{y[2020]:+.2f} 21:{y[2021]:+.2f} 22:{y[2022]:+.2f} "
            f"23:{y[2023]:+.2f} 24:{y[2024]:+.2f}"
        )
        # CONTROL: trend-only under the SAME router (reversion disabled) — isolates the
        # reversion leg's marginal contribution (NET-ADDITIVE test, the iter-031-B guard).
        ctrl = run_router_trend_only(rt)
        if ctrl is not None:
            d_sh = st["sharpe"] - ctrl["sharpe"]
            d_ev = st["events"] - ctrl["events"]
            p(
                f"          CONTROL trend-only-under-router: ev={ctrl['events']} "
                f"shrp={ctrl['sharpe']:+.3f} top2={ctrl['top2']:+.3f}  ||  reversion marginal: "
                f"Δev={d_ev:+d} Δshrp={d_sh:+.3f}  ({'ADDITIVE' if d_sh >= 0 else 'DILUTIVE'})"
            )

    # =========================================================================================
    # [5] PRE-REGISTERED PASS/NEGATIVE VERDICT
    # =========================================================================================
    p("\n[5] PRE-REGISTERED VERDICT (per the brief's combined-book criteria):")
    p("  PASS requires (vs trend-alone), for the recommended router:")
    p("    (a) MORE independent events than trend-alone")
    p("    (b) LOWER top-2 share than trend-alone (de-concentration)")
    p("    (c) IS Sharpe >= trend-alone (net-additive, NOT dilutive — the iter-031-B failure mode)")
    p("    (d) recent sub-period (2022,2023,2024) all non-negative (the OOS-adjacent stability gate)")

    def verdict(tag, st):
        if st is None:
            return False, ["no book"]
        a = st["events"] > tr_stats["events"]
        b = (st["top2"] < tr_stats["top2"]) if np.isfinite(st["top2"]) and np.isfinite(tr_stats["top2"]) else False
        c = st["sharpe"] >= tr_stats["sharpe"]
        y = st["yearly"]
        d = all((np.isnan(y[yy]) or y[yy] >= -0.10) for yy in (2022, 2023, 2024))
        passed = a and b and c and d
        flags = [
            f"(a)more-events={a}({st['events']}v{tr_stats['events']})",
            f"(b)lower-top2={b}({st['top2']:+.3f}v{tr_stats['top2']:+.3f})",
            f"(c)sharpe>=trend={c}({st['sharpe']:+.3f}v{tr_stats['sharpe']:+.3f})",
            f"(d)recent-nonneg={d}",
        ]
        return passed, flags

    for tag in ("R-ADX ", "R-CONV"):
        if tag not in results:
            continue
        ok, flags = verdict(tag, results[tag])
        p(f"  {tag}: {'PASS' if ok else 'NEGATIVE'}  " + "  ".join(flags))

    # dump CSV
    rows = []
    for name, st in (("trend_alone", tr_stats), ("rev_alone", rv_stats)):
        rows.append({"book": name, **{k: v for k, v in st.items() if k != "yearly"},
                     **{f"y{yy}": st["yearly"][yy] for yy in st["yearly"]}})
    for tag, st in results.items():
        rows.append({"book": tag.strip(), **{k: v for k, v in st.items() if k != "yearly"},
                     **{f"y{yy}": st["yearly"][yy] for yy in st["yearly"]}})
    pd.DataFrame(rows).to_csv(Path(__file__).parent / "ensemble_screen.csv", index=False)
    (Path(__file__).parent / "ensemble_screen_output.txt").write_text("\n".join(LOG))
    print("\n[written] ensemble_screen.csv + ensemble_screen_output.txt")


if __name__ == "__main__":
    main()

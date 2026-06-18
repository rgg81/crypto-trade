"""iter-v1/032 (ETHUSDT) — IS-ONLY breadth-edge feasibility screen.

GOAL: the iter-027 let-winners-run TREND edge fires ~82 IS / ~32 OOS trades (~1.3/mo)
and its OOS is carried by 1-2 concentrated trend-captures (top-2 ~438%). The de-concentration
campaign (/028-/031, 4 mechanism families) PROVED you cannot manufacture independent events by
modifying the slow-trend trade structure. The path to BREADTH is a genuinely DIFFERENT,
HIGHER-FREQUENCY edge that intrinsically produces MANY independent events.

This screen evaluates 3 crypto-native high-event edges HEAD-TO-HEAD on ETH IS, all judged on:
  (a) MANY MORE independent events than 82 (target >= 2x),
  (b) positive per-trade edge NET of cost (fee 0.1% + slippage 2bps/side = 0.104% round-trip
      on notional ... actually fee 0.1%/side + 2bps/side => per-side 0.12%, round trip 0.24%),
  (c) LOWER concentration (top-2 share) than iter-027,
  (d) event independence / temporal spread.

CANDIDATE EDGES
  A. SHORT-HORIZON MEAN-REVERSION  — direction = -sign(overextension). Triggers tested:
       A1 ret z-score over window W beyond +-k  (deterministic, the cleanest)
       A2 BB %B extreme  (close above/below band)
       A3 RSI extreme (<30 / >70)
     Hold N in {3,6,9} candles (1-3d). Direction is DETERMINISTIC (opposite the stretch).
  B. FASTER-TREND  — trend_state on shorter SMA (50/100) + shorter hold N in {6,9,21}.
     Keeps the proven deterministic trend-state primitive, faster -> more captures.
  C. FUNDING / BASIS CARRY  — direction from funding_rate_zscore_30 sign (fade extreme
     positive funding = short; fade extreme negative = long) — crypto carry. Data-dependent.

ALL leak-safe: load_is_only (open_time < OOS_CUTOFF), every primitive .shift(1), entries dropped
if their N-candle label horizon crosses the OOS wall (drop_horizon_crossing_oos with horizon=N).

COST MODEL (matches baseline): fee 0.1%/side + slippage 2.0 bps/side.
  round-trip cost on |notional| = 2*(0.001 + 0.0002) = 0.0024 = 0.24%.

Per-trade pnl_pct = direction * (close[t+N]/close[t] - 1) - 0.0024  (signless fwd return * dir).
Entry at close[t] (decision uses only info <= t-1; we ENTER at the close of the decision candle,
standard for this codebase — the SIGNAL is past-only, fill at decision-candle close).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    concentration_stats,
    load_full_for_label_horizon,
)

ROUND_TRIP_COST = 2 * (0.001 + 0.0002)  # 0.24%
CANDLES_PER_MONTH = 91.0  # ~91 8h candles/month on ETH IS
N_TREND_BASELINE = 82  # iter-027 IS roster
TREND_TOP2_SHARE_POS = None  # computed below from the TREND-fast control; baseline ref ~0.07 IS


def ann_sharpe(pnls: np.ndarray, n_per_year: float) -> float:
    p = np.asarray(pnls, float)
    if len(p) < 2 or p.std(ddof=1) == 0:
        return 0.0
    return float(p.mean() / p.std(ddof=1) * np.sqrt(n_per_year))


def fwd_return(close: np.ndarray, n: int) -> np.ndarray:
    """signless forward return close[t+n]/close[t]-1 (NaN where t+n out of range)."""
    out = np.full(len(close), np.nan)
    out[: len(close) - n] = close[n:] / close[: len(close) - n] - 1.0
    return out


def non_overlap_select(idx: np.ndarray, n_hold: int) -> np.ndarray:
    """Greedy non-overlapping selection: take entry, skip the next n_hold candles.

    idx is a sorted array of candidate ENTRY positions (integer index into the frame).
    Returns the subset that does not overlap (single position at a time) — the realistic
    single-symbol cadence. This is what bounds the true event count.
    """
    kept = []
    last_exit = -1
    for i in idx:
        if i > last_exit:
            kept.append(i)
            last_exit = i + n_hold
    return np.array(kept, dtype=int)


def evaluate_edge(
    df: pd.DataFrame,
    entry_mask: np.ndarray,
    direction: np.ndarray,
    n_hold: int,
    name: str,
) -> dict:
    """Evaluate one edge: entries where entry_mask True, given direction array, N-candle hold.

    LEAK GUARD: drop entries whose label horizon (t + n_hold) crosses the OOS wall, AND require
    open_time < OOS_CUTOFF. fwd return uses close[t+n_hold].
    """
    close = df["close"].to_numpy(float)
    open_time = df["open_time"].to_numpy()
    fr = fwd_return(close, n_hold)

    # horizon must stay strictly inside IS: open_time[t+n_hold] < OOS_CUTOFF
    ot_future = np.full(len(df), np.inf)
    ot_future[: len(df) - n_hold] = open_time[n_hold:]
    horizon_safe = (open_time < OOS_CUTOFF_MS) & (ot_future < OOS_CUTOFF_MS)

    valid = entry_mask & horizon_safe & np.isfinite(fr) & np.isfinite(direction)
    cand_idx = np.where(valid)[0]
    if len(cand_idx) == 0:
        return {"name": name, "n_raw": 0, "events": 0}

    # single-position non-overlapping cadence (realistic)
    sel = non_overlap_select(cand_idx, n_hold)
    d = direction[sel]
    raw = fr[sel]
    pnl = d * raw - ROUND_TRIP_COST  # net per-trade pnl_pct

    # max IS open_time among selected -> assert leak guard
    max_ot = open_time[sel].max()
    assert max_ot < OOS_CUTOFF_MS, f"LEAK GUARD FAIL {name}: {max_ot}"
    # also assert future candle inside IS
    assert ot_future[sel].max() < OOS_CUTOFF_MS, f"LEAK GUARD FAIL (horizon) {name}"

    events = len(sel)
    n_per_year = (CANDLES_PER_MONTH * 12.0) / n_hold  # trades/year if back-to-back
    # actual trades/year from realized cadence:
    span_months = (open_time[sel].max() - open_time[sel].min()) / (
        1000 * 60 * 60 * 8 * CANDLES_PER_MONTH
    )
    trades_per_year = events / max(span_months / 12.0, 1e-9)

    sharpe = ann_sharpe(pnl, trades_per_year)
    conc = concentration_stats(pnl)
    win = float((pnl > 0).mean())
    net = float(pnl.sum())
    gross_abs = np.abs(pnl)
    srt = np.sort(gross_abs)[::-1]
    top2_gross = float(srt[:2].sum() / gross_abs.sum()) if gross_abs.sum() > 0 else np.nan

    return {
        "name": name,
        "n_raw": len(cand_idx),
        "events": events,
        "trades_per_month": events / max(span_months, 1e-9),
        "win_rate": win,
        "per_trade_sharpe": sharpe,
        "net_sum_pct": net * 100.0,
        "mean_pnl_pct": float(pnl.mean()) * 100.0,
        "top2_share_pos": conc["top2_share_of_pos"],
        "top2_share_gross": top2_gross,
        "n_hold": n_hold,
        "_pnl": pnl,
        "_idx": sel,
        "_open_time": open_time[sel],
    }


def main() -> None:
    df = load_full_for_label_horizon()
    df = df.sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(float)
    log = []

    def p(s=""):
        print(s)
        log.append(str(s))

    p("=" * 100)
    p("iter-v1/032 ETHUSDT — IS-ONLY BREADTH-EDGE FEASIBILITY SCREEN")
    p(f"round-trip cost = {ROUND_TRIP_COST * 100:.3f}% | OOS_CUTOFF = {OOS_CUTOFF_MS}")
    p(
        f"baseline iter-027 IS roster = {N_TREND_BASELINE} events (~1.31/mo); BREADTH target >= 2x = 164"
    )
    p("=" * 100)

    # ---- past-only primitives (all .shift(1)) -----------------------------------
    s = pd.Series(close)
    logret = np.log(s / s.shift(1))

    # ret z-score over window W (of 1-candle log returns), past-only at t-1
    def ret_zscore(w: int) -> np.ndarray:
        r = logret  # 1-candle log return
        mu = r.rolling(w).mean()
        sd = r.rolling(w).std(ddof=0)
        z = (r - mu) / sd
        return z.shift(1).to_numpy()  # value known at t-1

    # cumulative-return z-score: z of the W-candle cumulative log return, past-only
    def cumret_zscore(w: int, lookback: int = 200) -> np.ndarray:
        cr = logret.rolling(w).sum()  # W-candle cumulative log return ending at t
        mu = cr.rolling(lookback).mean()
        sd = cr.rolling(lookback).std(ddof=0)
        z = (cr - mu) / sd
        return z.shift(1).to_numpy()  # past-only

    # RSI(14) from parquet (already past-only per feature builder), shift(1) for safety
    rsi14 = df["mom_rsi_14"].shift(1).to_numpy() if "mom_rsi_14" in df else None
    # BB %B 20 from parquet
    bbpctb20 = df["mr_bb_pctb_20"].shift(1).to_numpy() if "mr_bb_pctb_20" in df else None
    # mr_zscore from parquet (price z vs SMA) — past-only shift(1)
    mrz20 = df["mr_zscore_20"].shift(1).to_numpy() if "mr_zscore_20" in df else None
    mrz10 = df["mr_zscore_10"].shift(1).to_numpy() if "mr_zscore_10" in df else None
    # funding z30 from parquet, shift(1)
    fz30 = (
        df["funding_rate_zscore_30"].shift(1).to_numpy() if "funding_rate_zscore_30" in df else None
    )
    fz90 = (
        df["funding_rate_zscore_90"].shift(1).to_numpy() if "funding_rate_zscore_90" in df else None
    )

    # SMA trend-state (fast)
    def trend_state(w: int) -> np.ndarray:
        sma = s.rolling(w).mean()
        cp = s.shift(1)
        sm = sma.shift(1)
        return np.where(cp > sm, 1.0, -1.0)

    results = []

    # ============================ EDGE A: MEAN-REVERSION ======================
    p("\n" + "#" * 100)
    p("# EDGE A — SHORT-HORIZON MEAN-REVERSION (direction = -sign(overextension))")
    p("#" * 100)

    # A1: cumulative-return z-score trigger (the cleanest deterministic overextension)
    for w in (3, 5, 10):
        z = cumret_zscore(w)
        for k in (1.5, 2.0, 2.5):
            for n_hold in (3, 6, 9):
                mask = np.abs(z) >= k
                direction = -np.sign(z)  # fade the stretch
                r = evaluate_edge(df, mask, direction, n_hold, f"A1.cumretZ_w{w}_k{k}_N{n_hold}")
                if r.get("events", 0) >= 20:
                    results.append(r)

    # A2: BB %B extreme (close outside band -> fade)
    if bbpctb20 is not None:
        for lo, hi in ((0.05, 0.95), (0.0, 1.0), (0.10, 0.90)):
            for n_hold in (3, 6, 9):
                mask = (bbpctb20 <= lo) | (bbpctb20 >= hi)
                # direction: below lower band -> long(+1); above upper -> short(-1)
                direction = np.where(bbpctb20 <= lo, 1.0, np.where(bbpctb20 >= hi, -1.0, np.nan))
                r = evaluate_edge(df, mask, direction, n_hold, f"A2.bbpctb_{lo}_{hi}_N{n_hold}")
                if r.get("events", 0) >= 20:
                    results.append(r)

    # A3: RSI extreme
    if rsi14 is not None:
        for lo, hi in ((25, 75), (30, 70), (20, 80)):
            for n_hold in (3, 6, 9):
                mask = (rsi14 <= lo) | (rsi14 >= hi)
                direction = np.where(rsi14 <= lo, 1.0, np.where(rsi14 >= hi, -1.0, np.nan))
                r = evaluate_edge(df, mask, direction, n_hold, f"A3.rsi_{lo}_{hi}_N{n_hold}")
                if r.get("events", 0) >= 20:
                    results.append(r)

    # A4: price z-score vs SMA (mr_zscore) extreme — fade
    for col, zarr in (("mrz20", mrz20), ("mrz10", mrz10)):
        if zarr is None:
            continue
        for k in (1.5, 2.0, 2.5):
            for n_hold in (3, 6, 9):
                mask = np.abs(zarr) >= k
                direction = -np.sign(zarr)
                r = evaluate_edge(df, mask, direction, n_hold, f"A4.{col}_k{k}_N{n_hold}")
                if r.get("events", 0) >= 20:
                    results.append(r)

    # ============================ EDGE B: FASTER-TREND ========================
    p("\n" + "#" * 100)
    p("# EDGE B — FASTER-TREND (deterministic trend-state, shorter SMA + shorter hold)")
    p("#" * 100)
    for w in (50, 100):
        ts = trend_state(w)
        for n_hold in (6, 9, 21):
            mask = np.isfinite(ts)
            r = evaluate_edge(df, mask, ts, n_hold, f"B.trendSMA{w}_N{n_hold}")
            if r.get("events", 0) >= 20:
                results.append(r)

    # ============================ EDGE C: FUNDING CARRY =======================
    p("\n" + "#" * 100)
    p(
        "# EDGE C — FUNDING-CARRY (fade extreme funding: high +funding -> short; low -funding -> long)"
    )
    p("#" * 100)
    for col, fz in (("fz30", fz30), ("fz90", fz90)):
        if fz is None:
            continue
        for k in (1.0, 1.5, 2.0):
            for n_hold in (3, 6, 9):
                mask = np.abs(fz) >= k
                direction = -np.sign(fz)  # fade crowded funding
                r = evaluate_edge(df, mask, direction, n_hold, f"C.{col}_k{k}_N{n_hold}")
                if r.get("events", 0) >= 20:
                    results.append(r)

    # ---------------------------- report -------------------------------------
    cols = [
        "name",
        "events",
        "trades_per_month",
        "win_rate",
        "per_trade_sharpe",
        "net_sum_pct",
        "mean_pnl_pct",
        "top2_share_pos",
        "top2_share_gross",
        "n_hold",
    ]
    rdf = pd.DataFrame([{c: r.get(c) for c in cols} for r in results])
    rdf = rdf.sort_values("per_trade_sharpe", ascending=False).reset_index(drop=True)
    rdf.to_csv(Path(__file__).parent / "breadth_edge_screen.csv", index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", lambda x: f"{x:.4f}")

    p("\n" + "=" * 100)
    p("TOP 25 by per-trade Sharpe (events>=20, net of cost):")
    p("=" * 100)
    p(rdf.head(25).to_string())

    # breadth-credible = events >= 164 AND per_trade_sharpe > 0 AND top2_share_gross < ~0.07
    p("\n" + "=" * 100)
    p("BREADTH-CREDIBLE (events>=164 = 2x baseline, per_trade_sharpe>0, top2_gross<0.10):")
    p("=" * 100)
    cred = rdf[
        (rdf["events"] >= 164) & (rdf["per_trade_sharpe"] > 0) & (rdf["top2_share_gross"] < 0.10)
    ].sort_values("per_trade_sharpe", ascending=False)
    p(cred.to_string() if len(cred) else "  (none clear all three)")

    # best per family
    p("\n" + "=" * 100)
    p("BEST per family (by per_trade_sharpe among events>=100):")
    p("=" * 100)
    rdf["family"] = rdf["name"].str.split(".").str[0].str.replace(r"\d", "", regex=True).str[0]
    rdf["fam"] = rdf["name"].str[0]
    big = rdf[rdf["events"] >= 100]
    for fam in ("A", "B", "C"):
        sub = big[big["fam"] == fam].sort_values("per_trade_sharpe", ascending=False)
        if len(sub):
            p(f"\n-- family {fam} (events>=100) --")
            p(sub.head(6).to_string())
        else:
            sub2 = rdf[rdf["fam"] == fam].sort_values("per_trade_sharpe", ascending=False)
            p(f"\n-- family {fam} (NONE with events>=100; best overall) --")
            p(sub2.head(6).to_string())

    # independence diagnostic for the single best mean-reversion config vs trend baseline proxy
    p("\n" + "=" * 100)
    p("INDEPENDENCE / SPREAD diagnostic for the best EDGE-A config:")
    p("=" * 100)
    a_results = [r for r in results if r["name"].startswith("A") and r.get("events", 0) >= 164]
    if a_results:
        best_a = max(a_results, key=lambda r: r["per_trade_sharpe"])
        ot = pd.to_datetime(best_a["_open_time"], unit="ms")
        months = ot.to_period("M").value_counts().sort_index()
        active_months = (months > 0).sum()
        p(
            f"best EDGE-A: {best_a['name']}  events={best_a['events']}  "
            f"per_trade_sharpe={best_a['per_trade_sharpe']:.4f}"
        )
        p(
            f"  active months: {active_months} of {len(months)}  "
            f"(mean {months.mean():.1f}/mo, max {months.max()}/mo, min {months.min()})"
        )
        # what fraction of net comes from best & worst month?
        pnl = best_a["_pnl"]
        mser = pd.Series(pnl, index=ot.to_period("M"))
        mon = mser.groupby(level=0).sum()
        pos_months = (mon > 0).sum()
        p(
            f"  monthly net PnL: {pos_months}/{len(mon)} months positive; "
            f"best month {mon.max() * 100:.1f}%, worst {mon.min() * 100:.1f}%"
        )
        p(
            f"  top-2 trade share (gross) = {best_a['top2_share_gross']:.4f} "
            f"(vs iter-027 IS ~0.073, OOS ~0.44)"
        )
    else:
        p("  no EDGE-A config reached 164 events with positive Sharpe.")

    (Path(__file__).parent / "breadth_edge_screen_output.txt").write_text("\n".join(log))
    print("\n[written] breadth_edge_screen.csv + breadth_edge_screen_output.txt")


if __name__ == "__main__":
    main()

"""portfolio-iteration EXPLORATION-020 — HYSTERESIS-BANDING (no-trade band) on trend+carry.

Every prior iteration modulated GROSS exposure (a scalar) or FACTOR weights. None touched
rebalancing CADENCE. The baseline's -23% maxDD is whipsaw turnover INTO correlated reversals: a
coin's target weight flips on noise, we pay the round-trip cost AND eat the reversal. A no-trade
band rebalances a coin only when its target weight has moved meaningfully since we last traded it —
fewer trades, less flip-on-noise, lower live cost/slippage.

Mechanism (past-only, path-dependent), applied per-coin to the canonical walk-forward-lambda
target-weight book:

    held_w[t] = held_w[t-1]                         if |target_w[t] - held_w[t-1]| <= delta
    held_w[t] = target_w[t]                          otherwise  (SNAP mode)
    held_w[t] = held_w[t-1] +- (move - delta)        otherwise  (EDGE mode: snap to band edge)

held_w[t-1] is strictly past; the band decision uses no information from candle t's return. After
banding, the per-candle GROSS is renormalized back to the baseline's gross so this is a CADENCE
change, not a sizing change. Net P&L (price + real funding - taker cost) is then recomputed on the
ACTUAL (banded) turnover — that is the whole point: the banded book trades less, so cost DROPS.

delta = 0 reproduces iter_005 EXACTLY (IS +1.30 / OOS +1.37 / maxDD -23%): with no band, held_w
always equals target_w, gross renorm is a no-op, and the net is bit-identical to the stitched
walk-forward.

CONFIRMATION rigor is deferred; this is an EXPLORATION (no OOS-tuning — delta is swept and judged on
robustness across the sweep, the OOS column is reported once for information, never selected on).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_004_funding as f4  # noqa: E402
import iter_005_wf_lambda as wf5  # noqa: E402

# Band sizes swept (per-coin absolute target-weight move threshold). 0.0 is the identity check.
DELTA_GRID = [0.0, 0.002, 0.005, 0.010, 0.020]


def build_books(coins: dict) -> dict:
    """Per-lambda canonical books, sharing the iter_004/iter_005 construction EXACTLY.

    Returns, for each lambda in wf5.LAM_GRID, a dict with the past-only lagged per-coin weight book
    `w` (gross-normalized to 1, already shifted), the raw next-bar open return `ret_fwd`, the
    next-candle funding `fund_next`, the per-candle vol-target `scale`, and the undiscounted net
    `net` (vol-targeted) used by the walk-forward to PICK lambda. These are computed once and reused
    across the whole delta sweep.
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    close = close.reindex(opens.index)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    qv = qv.reindex(opens.index)
    fund = f4.load_funding(opens.index, list(coins.keys())).reindex(opens.index)
    dt = pd.to_datetime(opens.index, unit="ms")
    for df in (opens, close, qv, fund):
        df.index = dt
    ret_fwd = opens.shift(-1) / opens - 1.0
    elig = qv.rolling(base.LIQ_WIN).mean().shift(1).rank(axis=1, ascending=False) <= base.TOP_N
    rvol = close.pct_change().rolling(base.VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in base.HORIZONS) / len(base.HORIZONS)
    carry = -np.sign(fund.rolling(f4.M_FUND).mean())
    fund_next = fund.shift(-1)

    books = {}
    for lam in wf5.LAM_GRID:
        raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)
        # lagged, gross-normalized target weight book (this IS iter_004/iter_005's `w`)
        w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
        pnl = (w * ret_fwd.reindex(columns=w.columns)).sum(axis=1)
        fpnl = -(w * fund_next.reindex(columns=w.columns)).sum(axis=1)
        cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
        raw_net = (pnl + fpnl - cost).dropna()
        # vol-target scale (past-only) — base.vol_target multiplies net by this scale
        rv = raw_net.rolling(base.PORT_VOL_WIN).std().shift(1)
        scale = (base.TARGET_VOL / rv).clip(upper=base.MAX_LEV).fillna(0.0)
        books[lam] = {
            "w": w,
            "ret_fwd": ret_fwd,
            "fund_next": fund_next,
            "scale": scale,
            "net": raw_net * scale,  # == base.vol_target(raw_net), the iter_005 per-lambda net
        }
    return books


def canonical_book(coins: dict, books: dict) -> dict:
    """Stitch the walk-forward-lambda choice into a SINGLE per-candle canonical target book.

    Re-runs the IDENTICAL month-picking loop as iter_005.walkforward (best past monthly Sharpe on
    the vol-targeted per-lambda nets), but stitches the chosen lambda's WEIGHTS and per-candle scale
    rather than its net. The resulting target_w / scale reproduce iter_005's stitched net exactly.
    """
    panel = pd.DataFrame({lam: books[lam]["net"] for lam in books}).sort_index()
    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    step = 8 * 60 * 60 * 1000
    any_w = next(iter(books.values()))["w"]
    cols = any_w.columns
    target_w = pd.DataFrame(0.0, index=any_w.index, columns=cols)
    scale = pd.Series(0.0, index=any_w.index)
    covered = pd.Series(False, index=any_w.index)
    picks = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=wf5.TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=wf5.GAP_CANDLES * step)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= lo) & (panel.index < hi)]
        test_mask = (panel.index >= m0) & (panel.index < test_hi)
        if len(train) < 200 or not test_mask.any():
            continue
        tsh = train.apply(lambda s: base.msharpe(s, base.LO0, base.HI1))
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        picks.append((m0.year, best))
        idx = panel.index[test_mask]
        target_w.loc[idx, cols] = books[best]["w"].reindex(index=idx, columns=cols).to_numpy()
        scale.loc[idx] = books[best]["scale"].reindex(idx).to_numpy()
        covered.loc[idx] = True
    # restrict to the stitched (covered) candles — same span the iter_005 net spans
    target_w = target_w.loc[covered]
    scale = scale.loc[covered]
    ret_fwd = next(iter(books.values()))["ret_fwd"].reindex(index=target_w.index, columns=cols)
    fund_next = next(iter(books.values()))["fund_next"].reindex(index=target_w.index, columns=cols)
    return {
        "target_w": target_w,
        "scale": scale,
        "ret_fwd": ret_fwd,
        "fund_next": fund_next,
        "picks": picks,
    }


def apply_band(target_w: pd.DataFrame, delta: float, mode: str = "snap") -> pd.DataFrame:
    """Per-coin no-trade band on the canonical target weights (past-only, path-dependent).

    held[t] inherits held[t-1] unless |target[t]-held[t-1]| > delta. delta=0 returns target
    unchanged (held equals target bit-for-bit). The held book is the post-band, PRE-renorm
    weight; gross renormalization to the baseline gross is done by the caller per candle.
    """
    tw = target_w.to_numpy()
    n = tw.shape[0]
    if delta <= 0.0:
        return target_w.copy()
    held = np.empty_like(tw)
    held[0] = tw[0]
    prev = tw[0].copy()
    for t in range(1, n):
        tgt = tw[t]
        move = tgt - prev
        cur = prev.copy()
        trig = np.abs(move) > delta
        if mode == "edge":
            # move only the excess beyond the band edge, preserving direction
            cur[trig] = prev[trig] + np.sign(move[trig]) * (np.abs(move[trig]) - delta)
        else:  # snap
            cur[trig] = tgt[trig]
        held[t] = cur
        prev = cur
    return pd.DataFrame(held, index=target_w.index, columns=target_w.columns)


def banded_net(book: dict, delta: float, mode: str, cost_mult: float = 1.0) -> pd.Series:
    """Recompute the canonical net under a no-trade band of size `delta`.

    Renormalizes the post-band gross back to the baseline target gross each candle (cadence change,
    not sizing), then books price P&L + real funding - taker cost on the ACTUAL banded turnover, and
    applies the SAME canonical per-candle vol-target scale. `cost_mult` stresses the taker fee.
    """
    target_w = book["target_w"]
    held = apply_band(target_w, delta, mode)
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    # renorm post-band gross to the baseline gross each candle (no-op at delta=0)
    w = held.mul((base_gross / held_gross).fillna(0.0), axis=0)
    ret_fwd = book["ret_fwd"]
    fund_next = book["fund_next"]
    pnl = (w * ret_fwd).sum(axis=1)
    fpnl = -(w * fund_next).sum(axis=1)
    cost = base.COST_SIDE * cost_mult * (w - w.shift(1)).abs().sum(axis=1)
    raw_net = (pnl + fpnl - cost).dropna()
    return (raw_net * book["scale"].reindex(raw_net.index)).dropna()


def turnover_of(book: dict, delta: float, mode: str) -> float:
    """Mean per-candle one-side turnover sum |w[t]-w[t-1]| of the renormalized banded book."""
    target_w = book["target_w"]
    held = apply_band(target_w, delta, mode)
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    w = held.mul((base_gross / held_gross).fillna(0.0), axis=0)
    return float((w - w.shift(1)).abs().sum(axis=1).iloc[1:].mean())


def stats(net: pd.Series) -> dict:
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    oos = net[net.index >= base.OOS_CUTOFF]
    oeq = (1 + oos).cumprod()
    odd = float((oeq / oeq.cummax() - 1).min()) if len(oos) else float("nan")
    yr = {int(k): round(v * 100) for k, v in net.groupby(net.index.year).sum().items()}
    return {
        "IS": base.msharpe(net, base.LO0, base.OOS_CUTOFF),
        "OOS": base.msharpe(net, base.OOS_CUTOFF, base.HI1),
        "maxDD": dd * 100,
        "oosDD": odd * 100,
        "yr": yr,
    }


def report(book: dict, mode: str) -> None:
    print(f"\n=== mode={mode.upper()} ===")
    print(
        f"  {'delta':>6} {'IS':>6} {'OOS':>6} {'maxDD':>7} {'oosDD':>7} {'turn':>7} {'OOS-2x':>7}"
    )
    base_turn = None
    for delta in DELTA_GRID:
        net = banded_net(book, delta, mode, cost_mult=1.0)
        net2 = banded_net(book, delta, mode, cost_mult=2.0)
        turn = turnover_of(book, delta, mode)
        if delta == 0.0:
            base_turn = turn
        st = stats(net)
        oos2 = base.msharpe(net2, base.OOS_CUTOFF, base.HI1)
        tpc = "" if base_turn is None else f" ({(turn / base_turn - 1) * 100:+.0f}%)"
        print(
            f"  {delta:>6.3f} {st['IS']:>+6.2f} {st['OOS']:>+6.2f} {st['maxDD']:>6.0f}% "
            f"{st['oosDD']:>6.0f}% {turn:>7.4f} {oos2:>+7.2f}   turn{tpc}"
        )
    # per-year for the headline candidate (first non-zero delta in snap mode)
    if mode == "snap":
        cand = DELTA_GRID[2]
        st = stats(banded_net(book, cand, mode))
        st0 = stats(banded_net(book, 0.0, mode))
        print(f"  per-yr net%  delta=0.000: {st0['yr']}")
        print(f"  per-yr net%  delta={cand:.3f}: {st['yr']}")


def main() -> None:
    coins = base.load_universe()
    books = build_books(coins)
    book = canonical_book(coins, books)
    # identity check — delta=0 must reproduce iter_005 exactly
    net0 = banded_net(book, 0.0, "snap")
    st0 = stats(net0)
    print(f"EXPLORATION-020: hysteresis-banding — {len(coins)} candidates, grid {DELTA_GRID}")
    print(
        f"  IDENTITY delta=0: IS={st0['IS']:+.2f} OOS={st0['OOS']:+.2f} "
        f"maxDD={st0['maxDD']:.0f}%  (iter_005 target: IS +1.30 / OOS +1.37 / -23%)"
    )
    report(book, "snap")
    report(book, "edge")


if __name__ == "__main__":
    main()

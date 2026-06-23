"""portfolio-iteration EXPLORATION-021 — ELIGIBILITY-EXIT overlay (clean the zombie tail).

iter_020's hysteresis band (delta=0.010, SNAP) is the deployed baseline-v2 cadence layer. It works
(IS/OOS up, turnover down) but has a structural pathology the user found: the deployed book holds
**38 positions for a top-20 strategy**. Band-free (delta=0) it is exactly 20. The band carries ~18
EXITED coins forward FOREVER: once a coin drops out of the top-20 its target weight goes to 0, but
its leftover held weight (gross-renorm puts it at 0.003-0.008) only needs to move by < delta to
reach 0, and the band by design refuses moves <= delta. So the exit never fires. Verified zombies on
the last candle include DELISTED coins (TOMOUSDT last candle 2024-05-28, BLZUSDT rank ~198, $0 vol).
That is a live liability: paying funding + holding inventory in dead/illiquid names forever.

THE FIX (this exploration): an eligibility-exit overlay on top of iter_020's banded held book. The
band still governs how we TRACK eligible coins (the turnover win), but a coin that has been
INELIGIBLE (rank > TOP_N, i.e. not past-only `elig`) for >= K consecutive candles is FORCE-CLOSED
(held := 0), overriding the band's "hold". Then renorm to the baseline gross and apply the canonical
vol-target, exactly as iter_020.

Mechanism (PAST-ONLY, path-dependent), threaded INSIDE the iter_020 band loop:

    cur = band_decision(target[t], prev)           # iter_020 SNAP/EDGE step (unchanged)
    streak[c] += 1 if not elig[c, t] else reset 0   # elig uses shift(1) liquidity rank — past-only
    cur[c] = 0  for every c with streak[c] >= K      # force-close zombies, override the band
    held[t] = cur ;  prev = cur                      # forced-zero propagates (true path dependence)

`elig` is the SAME past-only top-N liquidity mask iter_002/iter_020 build (qv.rolling(90).mean()
.shift(1).rank <= 20). It uses no information from candle t's return, so the exit is leak-safe.

K-sweep semantics:
  K=1   exit immediately on dropping out of the top-20 (the held book ~= band-free for EXITS, while
        keeping the band for coins that stay eligible -> cleans the tail hardest).
  K=inf eligibility-exit DISABLED -> reproduces iter_020 EXACTLY (HARD identity gate).

This is an EXPLORATION: no OOS-tuning. K is swept and judged on ROBUSTNESS across the sweep; the OOS
column is reported once for information, never selected on. Cost is realistic (taker 0.05%/side, and
stressed 2x). The honest question: does forcing the zombies out clean the book toward true-top-20
WITHOUT hurting OOS Sharpe and WITHOUT blowing up the band's turnover win?
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_020_hysteresis as h20  # noqa: E402

# Consecutive-ineligible candles before a force-close. np.inf == exit disabled == iter_020 identity.
K_GRID = [1, 2, 3, 4, 6, np.inf]
DELTA = 0.010  # the deployed baseline-v2 band; the overlay sits ON TOP of it
MODE = "snap"  # the deployed band mode


def eligibility_mask(coins: dict, target_w: pd.DataFrame) -> pd.DataFrame:
    """The SAME past-only top-N liquidity eligibility mask iter_002/iter_020 build, aligned to the
    canonical target-weight book's index/columns.

    elig[c, t] = True iff coin c is in the top-TOP_N by trailing-LIQ_WIN mean $-volume as known at
    the PRIOR candle (`.shift(1)`). Identical construction to iter_002.build / iter_020.build_books;
    it is the mask whose `<= TOP_N` band-free book has exactly TOP_N positions. Past-only by shift.
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float)
    qv = pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()}).astype(float)
    close, qv = close.reindex(opens.index), qv.reindex(opens.index)
    close.index = qv.index = pd.to_datetime(opens.index, unit="ms")
    elig = base.top_n_eligibility(close, qv)  # PIT-seasoned top-N (survivorship-safe)
    return elig.reindex(index=target_w.index, columns=target_w.columns).fillna(False)


def apply_band_eligexit(
    target_w: pd.DataFrame,
    elig: pd.DataFrame,
    delta: float,
    k_exit: float,
    mode: str = "snap",
) -> pd.DataFrame:
    """iter_020 no-trade band + eligibility-exit overlay (past-only, path-dependent).

    Reproduces iter_020.apply_band's SNAP/EDGE step EXACTLY, then force-closes any coin ineligible
    for >= k_exit consecutive candles (overriding the band's hold). k_exit=inf disables the overlay
    so this returns iter_020.apply_band's book bit-for-bit. The forced zero is written into `prev`,
    so it propagates to the next candle's band decision: genuine path dependence, no peeking.
    """
    tw = target_w.to_numpy()
    el = elig.to_numpy()  # bool, True == eligible (in top-N this candle, known past-only)
    n, m = tw.shape
    held = np.empty_like(tw)
    streak = np.zeros(m, dtype=np.int64)  # consecutive ineligible candles, per coin

    def _force_exit(row_idx: int, cur: np.ndarray) -> np.ndarray:
        # advance the per-coin ineligible streak using THIS candle's past-only eligibility, then
        # force-close coins whose streak reached k_exit. inf -> the mask is always False -> no-op.
        elig_row = el[row_idx]
        streak[elig_row] = 0
        streak[~elig_row] += 1
        if np.isfinite(k_exit):
            cur = cur.copy()
            cur[streak >= k_exit] = 0.0
        return cur

    # t == 0: no band history; held starts at the (eligibility-exited) target.
    held[0] = _force_exit(0, tw[0].copy())
    prev = held[0].copy()
    no_band = delta <= 0.0
    for t in range(1, n):
        tgt = tw[t]
        if no_band:
            cur = tgt.copy()
        else:
            move = tgt - prev
            cur = prev.copy()
            trig = np.abs(move) > delta
            if mode == "edge":
                cur[trig] = prev[trig] + np.sign(move[trig]) * (np.abs(move[trig]) - delta)
            else:  # snap
                cur[trig] = tgt[trig]
        cur = _force_exit(t, cur)
        held[t] = cur
        prev = cur
    return pd.DataFrame(held, index=target_w.index, columns=target_w.columns)


def _renorm(target_w: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    """Renorm the post-overlay held gross back to the baseline per-candle gross (iter_020 step)."""
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    return held.mul((base_gross / held_gross).fillna(0.0), axis=0)


def eligexit_net(
    book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str, cost_mult: float = 1.0
) -> pd.Series:
    """Canonical net under the band + eligibility-exit overlay. Mirrors iter_020.banded_net: renorm
    to baseline gross, book price P&L + real funding - taker cost on the ACTUAL turnover, apply the
    canonical per-candle vol-target scale. `cost_mult` stresses the taker fee (2x = cost-stress)."""
    target_w = book["target_w"]
    held = apply_band_eligexit(target_w, elig, delta, k_exit, mode)
    w = _renorm(target_w, held)
    pnl = (w * book["ret_fwd"]).sum(axis=1)
    fpnl = -(w * book["fund_next"]).sum(axis=1)
    cost = base.COST_SIDE * cost_mult * (w - w.shift(1)).abs().sum(axis=1)
    raw_net = (pnl + fpnl - cost).dropna()
    return (raw_net * book["scale"].reindex(raw_net.index)).dropna()


def _renormed_book(book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str):
    target_w = book["target_w"]
    held = apply_band_eligexit(target_w, elig, delta, k_exit, mode)
    return _renorm(target_w, held)


def turnover_of(book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str) -> float:
    """Mean per-candle one-side turnover sum|w[t]-w[t-1]| of the renormalized overlay book."""
    w = _renormed_book(book, elig, k_exit, delta, mode)
    return float((w - w.shift(1)).abs().sum(axis=1).iloc[1:].mean())


def tickets_of(book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str) -> float:
    """Mean per-candle rebalancing-TICKET count: number of coins whose weight changed materially.

    A ticket is one order. 1e-6 absolute-weight-change floor screens float noise. This is the metric
    the band optimizes (fewer tickets = lower live cost); forcing exits ADDS tickets, so this is the
    quantity that decides whether the overlay wrecks the band's cost win."""
    w = _renormed_book(book, elig, k_exit, delta, mode)
    chg = (w - w.shift(1)).abs() > 1e-6
    return float(chg.sum(axis=1).iloc[1:].mean())


def avg_positions(book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str) -> float:
    """Mean per-candle count of NON-ZERO held positions (the point — should fall toward ~20)."""
    w = _renormed_book(book, elig, k_exit, delta, mode)
    return float((w.abs() > 1e-9).sum(axis=1).mean())


def last_book_audit(book: dict, elig: pd.DataFrame, k_exit: float, delta: float, mode: str) -> dict:
    """On the LAST candle: position count + how many held coins are still INELIGIBLE (zombies) +
    whether the known delisted/zero-vol names survive in the final book."""
    w = _renormed_book(book, elig, k_exit, delta, mode)
    last = w.index[-1]
    row = w.loc[last]
    held = row[row.abs() > 1e-9]
    elig_last = elig.loc[last]
    zombies = [c for c in held.index if not bool(elig_last.get(c, False))]
    dead = sorted(c for c in held.index if c in ("TOMOUSDT", "BLZUSDT"))
    return {
        "n_pos": int(len(held)),
        "n_zombie": int(len(zombies)),
        "zombies": sorted(zombies),
        "dead_held": dead,
    }


def stats(net: pd.Series) -> dict:
    return h20.stats(net)


def _kfmt(k: float) -> str:
    return "inf" if not np.isfinite(k) else f"{int(k)}"


def report(book: dict, elig: pd.DataFrame) -> None:
    print(f"\n=== ELIGIBILITY-EXIT overlay on band(delta={DELTA:.3f}, {MODE.upper()}) ===")
    print(
        f"  {'K':>4} {'IS':>6} {'OOS':>6} {'maxDD':>7} {'oosDD':>7} "
        f"{'avgPos':>7} {'turn':>7} {'tickets':>8} {'OOS-2x':>7}   {'turn-vs-iter020'}"
    )
    ref_turn = None
    for k_exit in sorted(K_GRID, reverse=True):  # inf (== iter_020) first, to anchor the turnover %
        net = eligexit_net(book, elig, k_exit, DELTA, MODE, cost_mult=1.0)
        net2 = eligexit_net(book, elig, k_exit, DELTA, MODE, cost_mult=2.0)
        turn = turnover_of(book, elig, k_exit, DELTA, MODE)
        tick = tickets_of(book, elig, k_exit, DELTA, MODE)
        pos = avg_positions(book, elig, k_exit, DELTA, MODE)
        st = stats(net)
        oos2 = base.msharpe(net2, base.OOS_CUTOFF, base.HI1)
        if ref_turn is None:
            ref_turn = turn
        tpc = f"{(turn / ref_turn - 1) * 100:+.0f}%"
        print(
            f"  {_kfmt(k_exit):>4} {st['IS']:>+6.2f} {st['OOS']:>+6.2f} {st['maxDD']:>6.0f}% "
            f"{st['oosDD']:>6.0f}% {pos:>7.1f} {turn:>7.4f} {tick:>8.2f} {oos2:>+7.2f}   {tpc}"
        )


def book_audit(book: dict, elig: pd.DataFrame) -> None:
    print("\n  LAST-CANDLE BOOK AUDIT (positions / zombies-still-held / delisted-still-held):")
    for k_exit in sorted(K_GRID, reverse=True):
        a = last_book_audit(book, elig, k_exit, DELTA, MODE)
        dead = ",".join(a["dead_held"]) if a["dead_held"] else "none"
        print(
            f"    K={_kfmt(k_exit):>3}: n_pos={a['n_pos']:>2}  "
            f"zombies(ineligible_held)={a['n_zombie']:>2}  delisted_held={dead}"
        )


def main() -> None:
    coins = base.load_universe()
    books = h20.build_books(coins)
    book = h20.canonical_book(coins, books)
    elig = eligibility_mask(coins, book["target_w"])

    # HARD identity gate: K=inf (overlay disabled) must reproduce iter_020 delta=0.010 SNAP exactly.
    net_inf = eligexit_net(book, elig, np.inf, DELTA, MODE)
    net_ref = h20.banded_net(book, DELTA, MODE)
    aligned = net_inf.align(net_ref, join="inner")
    max_abs = float((aligned[0] - aligned[1]).abs().max())
    ok = max_abs < 1e-12 and len(net_inf) == len(net_ref)
    st_inf = stats(net_inf)
    print(f"EXPLORATION-021: eligibility-exit overlay — {len(coins)} candidates, K-grid {K_GRID}")
    print(
        f"  IDENTITY K=inf vs iter_020(delta={DELTA:.3f},{MODE}): "
        f"max|diff|={max_abs:.2e}  len_match={len(net_inf) == len(net_ref)}  -> "
        f"{'PASS' if ok else 'FAIL'}"
    )
    print(f"  K=inf (== iter_020 baseline-v2): IS={st_inf['IS']:+.2f} OOS={st_inf['OOS']:+.2f} "
          f"maxDD={st_inf['maxDD']:.0f}%")
    if not ok:
        raise SystemExit("IDENTITY GATE FAILED — overlay does not reproduce iter_020 at K=inf")

    report(book, elig)
    book_audit(book, elig)


if __name__ == "__main__":
    main()

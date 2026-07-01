"""Live-parity RECONCILE — prove the tradfi paper bridge reproduces the backtest BIT-FOR-BIT.

The live bridge (`live_weights_tradfi.deployed_target_weights`) recomputes the iter-016 deployed
weight book from FULL history each call. This harness replays that at chosen ``as_of`` dates: at
each ``as_of`` it truncates the history to ``≤ as_of`` (what the desk sees when ``as_of`` has just
completed) and recomputes the deployed book — then asserts the last row == the full-history
backtest book's row for ``as_of``, BIT-EXACT. Because every signal is causal (``close.shift`` /
``rolling`` / ``.shift(1)`` lag, the EW-252d bear gate, past-only vol-target + VIX scalars), the
truncated recompute MUST equal the full-history book → no look-ahead, no drift, no ragged-panel or
gate-phase artifact.

The ``as_of`` set is stress-picked to hit the failure phases metals surfaced: a mid-history date, a
month boundary, the LATEST bar (forming-adjacent), a BEAR-GATE-FIRING day (lam_eff=0 sleeve flip), a
BAND-HOLD day (hysteresis no-trade), plus a dense sweep over the last N complete bars.

Part (2) quantifies the LIVE FORMING-BAR proxy gap (informational): the desk trading the NEXT
(forming) bar uses open ≈ prior close (the actual next open isn't known yet), so the forming target
vs the backtest's realised next-bar weight differ only by that vol-target-scale / band re-snap gap.

Run:  uv run python analysis/portfolio/tradfi/reconcile_tradfi.py [--n 40] [--data <dir>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import iter_006_crashbrake as i6  # noqa: E402
import iter_015_cost as i15  # noqa: E402
import iter_016_bear_gated_tsmom as champ  # noqa: E402
import live_weights_tradfi as lw  # noqa: E402

BIT_TOL = 1e-10  # bit-exact (truncated recompute == full-history book)
PROXY_TOL = 5e-2  # live forming-bar proxy gap (open ≈ prior close on the vol-target scale term)


def _truncate(coins: dict[str, pd.DataFrame], cutoff_ms: int) -> dict[str, pd.DataFrame]:
    return {s: d[d.index <= cutoff_ms] for s, d in coins.items() if len(d[d.index <= cutoff_ms])}


def _recompute_row(
    coins: dict[str, pd.DataFrame], as_of_ms: int, cols
) -> tuple[pd.Series, pd.Timestamp]:
    """Truncate to ``≤ as_of``; return the deployed book's LAST row (the live-bridge recompute)."""
    trunc = _truncate(coins, as_of_ms)
    _, deployed = champ.deployed_weights(ct.panels(trunc))
    return deployed.iloc[-1].reindex(cols).fillna(0.0), deployed.index[-1]


def _append_forming(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Append one SYNTHETIC forming bar per name (O=H=L=C=last close, +1 trading day) — the live
    forming-bar proxy (the just-opened bar whose true open isn't known yet)."""
    out: dict[str, pd.DataFrame] = {}
    for s, d in coins.items():
        if not len(d):
            continue
        last_ms = int(d.index[-1])
        nxt = last_ms + 86_400_000  # +1 day in ms
        c = float(d["close"].iloc[-1])
        row = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 0.0}, index=[nxt])
        out[s] = pd.concat([d, row])
    return out


def _pick_as_of_dates(
    coins: dict[str, pd.DataFrame], full_deployed: pd.DataFrame
) -> dict[str, pd.Timestamp]:
    """Stress-pick the phase-diverse ``as_of`` set (bear-gate-firing + band-hold + boundaries)."""
    pn = ct.panels(coins)
    idx = full_deployed.index
    gross = full_deployed.abs().sum(axis=1)
    live = idx[gross.values > 1e-9]

    # bear-gate-firing day: g=1 (EW-252d bear-state) AND book live — the sleeve flips to neutral.
    g = i6.bear_state(pn["close"], champ.GATE_LOOKBACK).reindex(idx).fillna(0.0)
    fired = idx[(g.values > 0.5) & (gross.values > 1e-9)]

    # band-hold day: the pre-scale banded book did NOT re-snap (Σ|Δw| ~ 0) while holding a position.
    raw = champ.bear_gated_combined_raw(pn)
    w = i15.banded_book_freq(raw, champ.DELTA, champ.FREQ)
    dturn = (w - w.shift(1)).abs().sum(axis=1)
    wgross = w.abs().sum(axis=1)
    hold = w.index[(dturn.values < 1e-9) & (wgross.values > 1e-9)]

    picks: dict[str, pd.Timestamp] = {}
    picks["mid_history"] = live[len(live) // 2]
    # month boundary: first live bar of a mid-history month
    mb = [t for t in live if t.day <= 3]
    picks["month_boundary"] = mb[len(mb) // 2] if mb else live[len(live) // 3]
    picks["latest_bar"] = live[-1]
    if len(fired):
        picks["bear_gate_firing"] = fired[len(fired) * 3 // 4]  # a deep-in-2022 firing day
    if len(hold):
        picks["band_hold"] = hold[len(hold) // 2]
    return picks


def reconcile(data_dir: str | None, n: int) -> int:
    coins = ct.load_tradfi(lw._universe(data_dir), data_dir)
    full_net, full = champ.deployed_weights(ct.panels(coins), data_dir=data_dir)
    cols = full.columns
    idx = full.index
    print(
        f"RECONCILE  data={data_dir or '<default>'}  names={len(cols)}  bars={len(full)}  "
        f"span={idx[0].date()}..{idx[-1].date()}"
    )

    # ---- named phase-diverse as_of dates + dense recent sweep ----
    named = _pick_as_of_dates(coins, full)
    sweep = list(
        idx[-(n + 1) : -1]
    )  # last n COMPLETE bars (exclude the very last = forming-adjacent)

    print("\n(1) BIT-EXACT  truncated-recompute[as_of]  ==  full-history book[as_of]:")
    worst_named = 0.0
    for tag, ts in named.items():
        as_of_ms = int(ts.value // 1_000_000)
        rec, bar = _recompute_row(coins, as_of_ms, cols)
        assert bar == ts, f"{tag}: truncated last bar {bar} != as_of {ts}"
        ref = full.loc[ts].reindex(cols).fillna(0.0)
        d = float((rec - ref).abs().max())
        worst_named = max(worst_named, d)
        # ALSO exercise the PUBLIC bridge end-to-end (disk load + dict packaging).
        api = lw.deployed_target_weights(ts, data_dir)
        api.pop("_meta")
        da = max((abs(api.get(c, 0.0) - float(ref[c])) for c in cols), default=0.0)
        gg = float(ref.abs().sum())
        print(
            f"    {tag:18} as_of={ts.date()}  gross={gg:5.2f}  "
            f"max|Δw|(recompute)={d:.2e}  max|Δw|(public API)={da:.2e}  "
            f"{'OK' if max(d, da) <= BIT_TOL else 'FAIL'}"
        )

    worst_sweep, sweep_fail = 0.0, 0
    for ts in sweep:
        as_of_ms = int(ts.value // 1_000_000)
        rec, bar = _recompute_row(coins, as_of_ms, cols)
        ref = full.loc[ts].reindex(cols).fillna(0.0)
        d = float((rec - ref).abs().max())
        worst_sweep = max(worst_sweep, d)
        sweep_fail += int(d > BIT_TOL)
    print(
        f"    dense sweep (last {len(sweep)} bars): worst max|Δw| = {worst_sweep:.2e}  "
        f"({'PASS' if sweep_fail == 0 else f'FAIL ({sweep_fail} bars)'}, tol {BIT_TOL:.0e})"
    )

    worst_bit = max(worst_named, worst_sweep)
    bit_ok = worst_bit <= BIT_TOL
    print(
        f"    -> BIT-EXACT overall: worst max|Δw| = {worst_bit:.2e}  "
        f"({'PASS' if bit_ok else 'FAIL'}, tol {BIT_TOL:.0e})"
    )

    # ---- (2) LIVE FORMING-BAR proxy gap (informational; open ≈ prior close) ----
    print("\n(2) LIVE forming-bar proxy gap (informational — open ≈ prior close):")
    worst_proxy = 0.0
    for ts in sweep[-10:]:
        pos = idx.get_loc(ts)
        if pos + 1 >= len(idx):
            continue
        nxt = idx[pos + 1]  # the bar the forming proxy targets
        as_of_ms = int(ts.value // 1_000_000)
        forming = _append_forming(_truncate(coins, as_of_ms))
        _, dep_f = champ.deployed_weights(ct.panels(forming))
        # forming last row targets the appended (proxy) bar; compare to the REALISED next-bar book.
        live_tgt = dep_f.iloc[-1].reindex(cols).fillna(0.0)
        ref_next = full.loc[nxt].reindex(cols).fillna(0.0)
        worst_proxy = max(worst_proxy, float((live_tgt - ref_next).abs().max()))
    print(
        f"    worst |Δw| forming-vs-realised (last 10 bars) = {worst_proxy:.2e}  "
        f"({'OK' if worst_proxy < PROXY_TOL else 'WIDE'}, tol {PROXY_TOL:.0e})"
    )

    verdict = (
        "OK — live bridge reproduces the iter-016 backtest deployed book bit-for-bit"
        if bit_ok
        else "DRIFT"
    )
    print(f"\nPARITY: {verdict}")
    return 0 if bit_ok else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--data", dest="data_dir", default=None)
    args = ap.parse_args()
    raise SystemExit(reconcile(args.data_dir, args.n))


if __name__ == "__main__":
    main()

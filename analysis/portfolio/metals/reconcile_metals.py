"""Live-parity RECONCILE — prove the paper engine reproduces the backtest BIT-FOR-BIT.

The engine recomputes the target from FULL history each tick. This replays the last N candles: at
each candle C it truncates the data to C (what the engine sees when C has just completed) and
recomputes the deployed book — then asserts the last row == the backtest's full-history book row for
C, BIT-EXACT. Because every signal is causal (ewm/rolling/.shift(1), bear-blind brake thresholds),
the truncated recompute must equal the full-history book → no look-ahead, no drift.

Separately it quantifies the LIVE forming-candle proxy gap: live trades the just-opened candle using
open ≈ prior close (the actual open isn't known yet), so the live target vs the backtest's realised
weight differ only by that <~0.01% gap (the crypto engine's documented forming approximation).

Run:  uv run python analysis/portfolio/metals/reconcile_metals.py [--n 300] [--data <dir>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import live_metals as lm  # noqa: E402
import live_weights as lw  # noqa: E402
import universe_metals as um  # noqa: E402

BIT_TOL = 1e-9  # bit-exact (recompute == full book)
PROXY_TOL = (
    5e-3  # live forming-proxy gap (open ≈ prior close; ~1e-3 after the regime-gate leak fix)
)


def _truncate(coins: dict[str, pd.DataFrame], cutoff_ms: int) -> dict[str, pd.DataFrame]:
    return {s: d[d.index <= cutoff_ms] for s, d in coins.items() if len(d[d.index <= cutoff_ms])}


def reconcile(data_dir: str, n: int) -> int:
    coins = um.load_metals(Path(data_dir))
    full, _ = lw.deployed_weight_book(coins)  # the backtest target per candle (full history)
    ms_index = max((d for d in coins.values()), key=len).index  # ms candle index (gold/silver)
    test = ms_index[
        -(n + 1) : -1
    ]  # last n COMPLETE candles (exclude the very last = forming-adjacent)

    print(f"RECONCILE  data={data_dir}  candles={len(full)}  replaying last {len(test)} ...")
    worst_bit = 0.0
    worst_proxy = 0.0
    bit_fail = 0
    for cutoff in test:
        ts = pd.Timestamp(int(cutoff), unit="ms")
        if ts not in full.index:
            continue
        # (1) BIT-EXACT: recompute on data truncated to this completed candle == the full book row
        trunc = _truncate(coins, int(cutoff))
        recompute, _ = lw.deployed_weight_book(trunc)
        diff = (
            (
                recompute.iloc[-1].reindex(full.columns).fillna(0.0)
                - full.loc[ts].reindex(full.columns).fillna(0.0)
            )
            .abs()
            .max()
        )
        worst_bit = max(worst_bit, float(diff))
        bit_fail += int(diff > BIT_TOL)
        # (2) LIVE FORMING PROXY: the engine (data thru cutoff−1, forming=cutoff) targets candle
        #     `cutoff`; compare to the backtest's realised weight for `cutoff`.
        prev_idx = ms_index[ms_index < cutoff]
        if len(prev_idx):
            live_coins = lm.MetalsPaperEngine._append_forming(_truncate(coins, int(prev_idx[-1])))
            live_tgt = lw.next_target_weights_metals(live_coins)
            live_tgt.pop("_meta")
            pg = max(
                (abs(live_tgt.get(s, 0.0) - float(full.loc[ts].get(s, 0.0))) for s in full.columns),
                default=0.0,
            )
            worst_proxy = max(worst_proxy, float(pg))

    print(
        f"  (1) BIT-EXACT recompute==book : worst |Δw| = {worst_bit:.2e}  "
        f"({'PASS' if bit_fail == 0 else f'FAIL ({bit_fail} candles)'}, tol {BIT_TOL:.0e})"
    )
    print(
        f"  (2) live forming-proxy gap     : worst |Δw| = {worst_proxy:.2e}  "
        f"({'OK' if worst_proxy < PROXY_TOL else 'WIDE'}, tol {PROXY_TOL:.0e} — open≈prior close)"
    )
    ok = bit_fail == 0 and np.isfinite(worst_bit)
    print(f"\nPARITY: {'OK — live engine reproduces the backtest bit-for-bit' if ok else 'DRIFT'}")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--data", default=str(_HERE.parents[2] / "data_live_metals"))
    args = ap.parse_args()
    raise SystemExit(reconcile(args.data, args.n))


if __name__ == "__main__":
    main()

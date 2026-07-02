"""Live parity bridge — the DEPLOYED iter-016 target weight book for the tradfi desk.

Thin adapter over the confirmed baseline (iter-016 BEAR-GATED TSMOM). The live paper engine and the
reconcile harness call ONLY these functions, so re-pointing the champion is a one-line change here.

PARITY IS BY CONSTRUCTION. This bridge does NOT re-implement the strategy — it calls the SAME
backtest deployed-weights code (`iter_016.deployed_weights`, which is itself decomposed from the
backtest net) on the on-disk history sliced to ``≤ as_of``. Because every signal is causal
(``close.shift`` / ``rolling`` / ``.shift(1)`` lag, the EW-252d bear gate, the past-only vol-target
and VIX scalars), the truncated recompute's ``as_of`` row equals the full-history backtest book's
``as_of`` row bit-for-bit — no incremental state that could drift. `reconcile_tradfi.py` proves it.

Recompute-from-full-history (the metals pattern): each call rebuilds the whole book from scratch and
returns the last row. There is no stored position state to diverge from the backtest.

PERP-VS-UNDERLYING BASIS — SOLVED (splice step 2). This bridge now loads the SPLICED book of record
(``splice_loader.load_tradfi_spliced``): Yahoo deep history return-chain-spliced to each name's
Binance perp from its point-in-time inception, resampled onto the Yahoo trading-day calendar. So the
signal + parity book are computed on the SAME instrument the desk executes (perp for the recent
2026 tail, Yahoo for the pre-inception history). IS is BIT-IDENTICAL to pure Yahoo by construction
(the entire in-sample window precedes every perp inception, so ``spliced == Yahoo`` for all IS bars;
proven in ``splice_verify.py`` / ``tests/test_tradfi_splice.py``) — the confirmed iter-016 IS cannot
move. Only the recent tail switches to the traded perp, collapsing the parity-vs-live BASIS to just
funding + quantization. Residual funding carry (~−0.7%/yr net on the L/S book) stays a budget item.

Run:  uv run python analysis/portfolio/tradfi/live_weights_tradfi.py [--as-of YYYY-MM-DD]
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
import iter_016_bear_gated_tsmom as champ  # noqa: E402  — the confirmed tradfi baseline
import splice_loader as sl  # noqa: E402  — Yahoo->perp SPLICED loader (the EXECUTED instrument)
import universe_tradfi as ut  # noqa: E402


def _universe(data_dir: str | None) -> list[str]:
    """The deployed universe = every ingested ``<SYM>/1d.csv`` that is in the sector map (69 names).

    Same membership resolution the backtest ``main`` uses, so the live book spans the exact panel.
    """
    base = Path(data_dir) if data_dir else ct._ROOT / "data"
    return sorted(p.parent.name for p in base.glob("*/1d.csv") if p.parent.name in ut.SECTOR_MAP)


def _truncate(coins: dict[str, pd.DataFrame], cutoff_ms: int) -> dict[str, pd.DataFrame]:
    """Slice every per-name frame to open_time ``≤ cutoff_ms`` (past-only, drops empties)."""
    return {s: d[d.index <= cutoff_ms] for s, d in coins.items() if len(d[d.index <= cutoff_ms])}


def deployed_book(
    data_dir: str | None = None, live_data_dir: str | None = None
) -> tuple[pd.Series, pd.DataFrame]:
    """Full-history ``(net, deployed_w)`` of the iter-016 baseline on the SPLICED book of record.

    Loads via ``splice_loader.load_tradfi_spliced`` (Yahoo deep history return-chain-spliced to each
    name's Binance perp from PIT inception), so the parity net + weight book are computed on the
    instrument the desk executes. IS bit-identical to pure Yahoo by construction (entire IS <
    earliest inception); only the recent 2026 tail switches to the traded perp. ``live_data_dir``
    overrides the perp store (default ``data_live_tradfi``)."""
    coins = sl.load_tradfi_spliced(_universe(data_dir), data_dir, live_data_dir)
    pn = ct.panels(coins)
    return champ.deployed_weights(pn, data_dir=data_dir)


def deployed_target_weights(
    as_of: str | pd.Timestamp,
    data_dir: str | None = None,
    tol: float = 1e-12,
    live_data_dir: str | None = None,
) -> dict[str, float]:
    """The iter-016 DEPLOYED target weight book the desk should hold as of ``as_of``.

    Recompute-from-full-history sliced to ``≤ as_of``: the last row of the truncated deployed book
    is the position held during bar ``as_of`` (band + vol-target + VIX + bear-gate applied), which
    is bit-identical to the full-backtest ``deployed_w.loc[as_of]`` (every input is past-only).

    ``as_of`` is snapped to the last on-disk trading bar ``≤ as_of``. Returns ``{ticker: weight}``
    for the names carrying a non-negligible position, plus a ``_meta`` entry (gross / net-dollar /
    as_of / scaled-flag). Weights are the vol-target-scaled DEPLOYED magnitudes (``Σ|w| ≈
    scale·s_vix``, NOT unit gross) — the real book in underlying-weight space (see header TODO).
    """
    as_of_ts = pd.Timestamp(as_of)
    as_of_ms = int(as_of_ts.value // 1_000_000)  # ns -> ms
    coins = _truncate(
        sl.load_tradfi_spliced(_universe(data_dir), data_dir, live_data_dir), as_of_ms
    )
    if not coins:
        raise ValueError(f"no tradfi data ≤ {as_of_ts.date()}")
    pn = ct.panels(coins)
    _, deployed = champ.deployed_weights(pn, data_dir=data_dir)
    row = deployed.iloc[-1]
    bar = deployed.index[-1]
    out = {t: float(w) for t, w in row.items() if abs(float(w)) > tol}
    out["_meta"] = {
        "as_of": bar,
        "gross": float(row.abs().sum()),
        "net_dollar": float(row.sum()),
        "n_names": len(out),
        "scaled": True,  # DEPLOYED = post band+vol-target+VIX (not pre-scale unit gross)
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=None, help="YYYY-MM-DD (default: latest on-disk bar)")
    ap.add_argument("--data", dest="data_dir", default=None)
    args = ap.parse_args()

    if args.as_of is None:
        net, deployed = deployed_book(args.data_dir)
        as_of = deployed.index[-1]
    else:
        as_of = pd.Timestamp(args.as_of)
    tgt = deployed_target_weights(as_of, args.data_dir)
    meta = tgt.pop("_meta")
    top = sorted(tgt.items(), key=lambda kv: -abs(kv[1]))[:12]
    print(
        f"iter-016 DEPLOYED target weights  as_of={meta['as_of'].date()}  (SPLICED book of record)"
    )
    print(
        f"  gross Σ|w| = {meta['gross']:.3f} (vol-target-scaled)   "
        f"net-dollar Σw = {meta['net_dollar']:+.3f} (bear-gated β-tilt)   names = {meta['n_names']}"
    )
    print("  top |w|:")
    for t, w in top:
        print(f"    {t:12} {w:+.4f}")
    print("  NOTE: SPLICED book — recent tail on the traded perp; IS bit-identical to Yahoo.")


if __name__ == "__main__":
    main()

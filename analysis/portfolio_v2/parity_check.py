"""Parity gate (SLOW, full universe) — the linchpin.

Proves engine_v2.run_book in v1-compat mode reproduces the deployed v1 book (iter_021 eligibility
-exit K=2, baseline-v3) bit-for-bit BEFORE any v2 correction is judged. If this fails, the
consolidated port is not a faithful reimplementation and no later comparison is trustworthy.

Independent reference path (exactly as the v1 baseline is built):
    iter_020.build_books(coins) -> iter_020.canonical_book(coins, books)
      -> iter_021.eligibility_mask(coins, target_w) -> iter_021.eligexit_net(book, elig, K=2, ...)

Candidate path:
    engine_v2.run_book(coins, rank_lo=0, rank_hi=20, season=None, slip_bps_fn=None) -> ['net']

Both read the SAME survivorship-inflated v1-compat pool from pf_data/. The v1 reference modules
hardcode `data/...` paths; since they are read-only we redirect their I/O to pf_data/ HERE (in this
script only) via a glob shim + a funding-loader shim — no edit to any analysis/portfolio/ file.

PASS iff inner-aligned max|Δ| < 1e-9 AND equal length. Prints IS/OOS for both. May take minutes.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
os.chdir(_ROOT)  # so pf_data/... and (shimmed) data/... resolve from the worktree root
sys.path.insert(0, str(_ROOT / "analysis"))
sys.path.insert(0, str(_ROOT / "analysis" / "portfolio"))

from portfolio_v2 import engine_v2  # noqa: E402
from portfolio_v2 import universe_v2 as uv  # noqa: E402

THRESH = 1e-9


def _install_pf_data_shims() -> None:
    """Redirect the read-only v1 reference modules' hardcoded `data/` I/O to `pf_data/`.

    Two shims, both local to this process:
      1. glob.glob — iter_002.load_universe globs `data/*USDT/8h.csv`; rewrite the prefix.
      2. iter_004.load_funding — reads `data/funding_rates/<SYM>.csv`; replace with a pf_data
         version whose math (nearest-match within 4h, sign, dedup) is IDENTICAL to the original.
    """
    import iter_002_top20  # noqa: F401  (ensures the module is importable before patching)
    import iter_004_funding as f4

    _orig_glob = glob.glob

    def _patched_glob(pattern, *a, **k):
        if isinstance(pattern, str) and pattern.startswith("data/"):
            pattern = "pf_" + pattern
        return _orig_glob(pattern, *a, **k)

    glob.glob = _patched_glob

    def _patched_load_funding(index_ms, syms) -> pd.DataFrame:
        cols = {}
        for s in syms:
            p = f"pf_data/funding_rates/{s}.csv"
            if not os.path.exists(p):
                cols[s] = pd.Series(0.0, index=index_ms)
                continue
            f = pd.read_csv(p).drop_duplicates(subset="funding_time", keep="last")
            f = f.set_index("funding_time")["funding_rate"].astype(float).sort_index()
            cols[s] = f.reindex(index_ms, method="nearest", tolerance=14_400_000).fillna(0.0)
        return pd.DataFrame(cols)

    f4.load_funding = _patched_load_funding


def _reference_net(coins: dict) -> tuple[pd.Series, list]:
    """iter_021 eligibility-exit K=2 net on the v1-compat pool (the deployed baseline-v3 book)."""
    import iter_020_hysteresis as h20
    import iter_021_eligexit as ee

    books = h20.build_books(coins)
    book = h20.canonical_book(coins, books)
    elig = ee.eligibility_mask(coins, book["target_w"])
    net = ee.eligexit_net(book, elig, k_exit=2, delta=ee.DELTA, mode=ee.MODE)
    return net, book["picks"]


def main() -> int:
    _install_pf_data_shims()

    # Same survivorship-inflated v1-compat pool for both paths.
    coins = uv.load_pool_v1compat()
    print(f"PARITY: v1-compat pool from pf_data/ — {len(coins)} candidates")

    # Reference: the deployed v1 book.
    print("  computing iter_021 K=2 reference net ...", flush=True)
    ref_net, ref_picks = _reference_net(coins)

    # Candidate: the consolidated engine in v1-compat mode (slip=0, season=None, band (0,20]).
    print("  computing engine_v2.run_book(v1-compat) ...", flush=True)
    out = engine_v2.run_book(
        coins,
        rank_lo=0,
        rank_hi=20,
        season=None,
        slip_bps_fn=None,  # -> zero_slip -> pure taker cost (v1)
        delta=engine_v2.DELTA,
        k_exit=engine_v2.K_EXIT,
        mode=engine_v2.MODE,
    )
    cand_net = out["net"]

    # Inner-align and compare.
    a, b = ref_net.align(cand_net, join="inner")
    max_abs = float((a - b).abs().max())
    len_match = len(ref_net) == len(cand_net) == len(a)
    ok = (max_abs < THRESH) and len_match

    ref_is = engine_v2.msharpe(ref_net, engine_v2.LO0, engine_v2.OOS_CUTOFF)
    ref_oos = engine_v2.msharpe(ref_net, engine_v2.OOS_CUTOFF, engine_v2.HI1)
    cand_is = out["IS"]
    cand_oos = out["OOS"]

    ref_picks_s = f"{ref_picks[:6]}{' ...' if len(ref_picks) > 6 else ''}"
    cand_picks_s = f"{out['picks'][:6]}{' ...' if len(out['picks']) > 6 else ''}"
    print()
    print(
        f"  ref  (iter_021 K=2)     : len={len(ref_net):5d}  IS={ref_is:+.4f}  OOS={ref_oos:+.4f}"
    )
    print(
        f"  cand (engine_v2 compat) : len={len(cand_net):5d}  "
        f"IS={cand_is:+.4f}  OOS={cand_oos:+.4f}"
    )
    print(f"  inner-aligned len={len(a)}  max|Δ|={max_abs:.3e}  len_match={len_match}")
    print(f"  ref λ-picks (year,λ)    : {ref_picks_s}")
    print(f"  cand λ-picks (year,λ)   : {cand_picks_s}")
    print()
    print(
        f"  PARITY {'PASS' if ok else 'FAIL'}  (max|Δ|={max_abs:.3e} < {THRESH:.0e}: "
        f"{max_abs < THRESH}; len_match: {len_match})"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

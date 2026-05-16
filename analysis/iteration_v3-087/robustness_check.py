"""iter-v3/087 EDA robustness check — leave-one-out + per-month decomposition.

Verifies the T3/T6 wholesale-6 lift is NOT a single-month artifact and is robust
to dropping any one symbol. IS-only — no cheating. Imports the main EDA module's
faithful per-symbol model.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "wbe_eda", Path(__file__).resolve().parent / "wholesale_breadth_expansion_eda.py"
)
_EDA = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_EDA)


def main() -> None:
    btc = _EDA.load_klines("BTCUSDT")
    syms6 = ["BCHUSDT", "LDOUSDT", "TRXUSDT", "GALAUSDT", "MANAUSDT", "SANDUSDT"]
    rosters = {}
    for s in syms6:
        df = _EDA.load_klines(s)
        feats = _EDA.compute_v3_features(df, btc)
        labs = _EDA.label_symbol_is(df, s)
        rosters[s] = _EDA.walk_forward_edge(feats, labs, s)

    inc3 = {s: rosters[s] for s in ["BCHUSDT", "LDOUSDT", "TRXUSDT"]}
    agg3, ser3 = _EDA.pooled_book_sharpe(inc3)
    agg6, ser6 = _EDA.pooled_book_sharpe(rosters)
    print(f"incumbent-3 aggregate IS monthly Sharpe: {agg3:+.4f}  (n_months={len(ser3)})")
    print(f"wholesale-6  aggregate IS monthly Sharpe: {agg6:+.4f}  (n_months={len(ser6)})")

    print("\nLEAVE-ONE-OUT robustness on the size-6 book:")
    for drop in syms6:
        bk = {s: rosters[s] for s in syms6 if s != drop}
        a, _ = _EDA.pooled_book_sharpe(bk)
        print(f"  drop {drop:10s} -> {len(bk)}-symbol aggregate Sharpe {a:+.4f}")

    common = sorted(set(ser3.index) & set(ser6.index))
    beats = sum(1 for t in common if ser6[t] > ser3[t])
    print(f"\nper-month: 6-book monthly PnL > 3-book in {beats}/{len(common)} common months")
    print(f"  6-book mean monthly PnL {ser6.mean():+.2f}  std {ser6.std(ddof=1):.2f}")
    print(f"  3-book mean monthly PnL {ser3.mean():+.2f}  std {ser3.std(ddof=1):.2f}")

    counts = {s: len(rosters[s]) for s in syms6}
    tot = sum(counts.values())
    print("\nIS trade-count share (denominator-expansion concentration check):")
    for s in syms6:
        print(f"  {s:10s} {counts[s]:5d} trades  {100 * counts[s] / tot:5.1f}%")
    print(f"  BCH share in 3-book: {100 * counts['BCHUSDT'] / sum(counts[s] for s in inc3):.1f}%")


if __name__ == "__main__":
    main()

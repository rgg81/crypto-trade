"""BACKWARD out-of-sample BEAR test — the frozen L2 baseline on the 2011–2015 metals bear.

The CONFIRMATION OOS (2025–26) was a benign metals BULL, so it could not test the book's #1
vulnerability: the long-biased anchor in a metals DOWNTURN. Our IS starts 2015-01; Dukascopy has
gold/silver back to ~2003. The 2011–2015 bear (gold $1920 Sep-2011 → $1050 Dec-2015, −45%; silver
−70%; the April-2013 crash) is a SEVERE metals bear the book has NEVER SEEN — a genuine backward
out-of-sample test.

DISCIPLINE: the L2 baseline is FROZEN (EMA84/189, FLOOR 0.5, dispersion α=0.5, vol-target ~15%/≤5×).
ONE shot, NO tuning on the result. Platinum/palladium have no pre-2022 data → this is the
deep-history GOLD/SILVER core of the baseline (which is what L2 reduces to before 2022 anyway).

EXPECTATION (do not misread): a long-biased book LOSES in a metals bear by design (the anchor never
shorts — iter-001 proved shorting metals loses). The test is whether the drawdown is BOUNDED /
survivable and whether the dollar-neutral gold-vs-silver dispersion overlay CUSHIONS it (silver fell
harder than gold, so long-gold/short-silver should profit in this bear).

Run:  uv run python analysis/portfolio/metals/bear_test_2011.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import ingest_dukascopy as ing  # noqa: E402
import iter_001_trend as it  # noqa: E402
import iter_002_mn_overlay as ov  # noqa: E402
import universe_metals as um  # noqa: E402

BEAR_DIR = _HERE.parents[2] / "data_bear"  # generated, gitignored-style (not committed)
BEAR_INSTRUMENTS = {"XAUUSDT": "xauusd", "XAGUSDT": "xagusd"}  # gold/silver only (deep history)
INGEST_START = "2010-06-01"  # warmup margin before 2011 (EMA189 + vol-target need ~270 candles)
INGEST_END = "2015-04-01"  # through the IS boundary (2015-03-24)
IS_CUTOFF = pd.Timestamp("2015-03-24")  # everything BEFORE this is UNSEEN by the baseline


def ingest_bear() -> None:
    """Pull gold/silver 2010-06→2015-04 into data_bear/ (idempotent — skips if already present)."""
    for ticker, inst in BEAR_INSTRUMENTS.items():
        out = ing.csv_path(BEAR_DIR, ticker, "8h")
        if out.exists():
            print(f"  {ticker}: cached {out}")
            continue
        print(f"  {ticker} ← dukascopy {inst} {INGEST_START}..{INGEST_END} ...", flush=True)
        with tempfile.TemporaryDirectory(prefix="bear_") as tmp:
            h1 = ing.fetch_h1(inst, INGEST_START, INGEST_END, tmp)
            ing.write_klines(out, ing.to_klines(ing.resample_8h(h1)), append=False)


def _stats(net: pd.Series, lo: pd.Timestamp, hi: pd.Timestamp) -> tuple[float, float, float, int]:
    """Monthly Sharpe, maxDD, total net%, n candles over [lo, hi)."""
    s = net[(net.index >= lo) & (net.index < hi)]
    if len(s) < 2:
        return float("nan"), float("nan"), float("nan"), len(s)
    eq = (1 + s).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return um.msharpe(s, lo, hi), dd, float(eq.iloc[-1] - 1), len(s)


def _bh_gold_total(close: pd.DataFrame, lo: pd.Timestamp, hi: pd.Timestamp) -> float:
    """Buy-and-hold gold total return over [lo, hi) — the bear magnitude (context only)."""
    g = close["XAUUSDT"][(close.index >= lo) & (close.index < hi)].dropna()
    return float(g.iloc[-1] / g.iloc[0] - 1) if len(g) > 1 else float("nan")


def main() -> None:
    print("=" * 88)
    print("BACKWARD OOS BEAR TEST — frozen L2 baseline on the 2011–2015 metals bear (gold/silver)")
    print("=" * 88)
    ingest_bear()

    coins = um.load_metals(BEAR_DIR)
    pan = um.panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    print(
        f"\n  universe: {tuple(coins)}  candles: {len(close)}  "
        f"span: {close.index[0].date()} .. {close.index[-1].date()}"
    )

    # FROZEN books (identical construction to confirm_metals L1/L2; only the universe is 2-metal)
    gn = ov.gross_norm
    anchor_raw = it.build_raw(coins)
    disp_raw = ov.mn_dispersion_raw(close)
    net_anchor, _ = um.net_from_raw(gn(anchor_raw), ret_fwd)  # L1 anchor alone
    net_l2, _ = um.net_from_raw(gn(anchor_raw) + 0.5 * gn(disp_raw), ret_fwd)  # L2 BASELINE
    net_disp, _ = um.net_from_raw(gn(disp_raw), ret_fwd)  # dispersion alone (the offset)

    windows = [
        ("FULL unseen pre-IS  2011-01 → 2015-03", pd.Timestamp("2011-01-01"), IS_CUTOFF),
        ("PURE bear (peak→IS) 2011-09 → 2015-03", pd.Timestamp("2011-09-01"), IS_CUTOFF),
        (
            "2013 CRASH year     2013-01 → 2013-12",
            pd.Timestamp("2013-01-01"),
            pd.Timestamp("2014-01-01"),
        ),
    ]
    print(f"\n  {'window':40} {'book':14} {'Sharpe':>7} {'maxDD':>8} {'net%':>8}  goldB&H%")
    print("  " + "-" * 86)
    for label, lo, hi in windows:
        bh = _bh_gold_total(close, lo, hi)
        for name, net in (
            ("L1 anchor", net_anchor),
            ("L2 baseline", net_l2),
            ("dispersion", net_disp),
        ):
            sr, dd, tot, _ = _stats(net, lo, hi)
            tag = f"{bh * 100:+6.0f}%" if name == "L1 anchor" else ""
            print(
                f"  {label if name == 'L1 anchor' else '':40} {name:14} "
                f"{sr:>+7.2f} {dd * 100:>7.1f}% {tot * 100:>+7.0f}%  {tag}"
            )
        print()

    # Per-year net% across the unseen bear
    print("  Per-year net% (UNSEEN; 2015 partial → IS cutoff):")
    print(f"  {'year':>6} {'L1_anchor':>10} {'L2_base':>10} {'disp':>8} {'goldB&H':>9}")
    yrs = sorted({d.year for d in close.index if d < IS_CUTOFF and d.year >= 2011})
    for y in yrs:
        lo, hi = pd.Timestamp(f"{y}-01-01"), min(pd.Timestamp(f"{y + 1}-01-01"), IS_CUTOFF)
        a = _stats(net_anchor, lo, hi)[2]
        b = _stats(net_l2, lo, hi)[2]
        d = _stats(net_disp, lo, hi)[2]
        bh = _bh_gold_total(close, lo, hi)
        print(f"  {y:>6} {a * 100:>+9.0f}% {b * 100:>+9.0f}% {d * 100:>+7.0f}% {bh * 100:>+8.0f}%")

    print("\n  READ (one-shot, no tuning): L1 = directional damage; L2 = with dispersion cushion;")
    print(
        "  dispersion = the standalone offset (long-gold/short-silver in a silver-led-down bear)."
    )


if __name__ == "__main__":
    main()

"""Leak-safe Yahoo -> Binance-perp SPLICED tradfi BACKTEST loader.

The confirmed iter-016 book is priced/validated on Yahoo total-return daily bars
(``data/<SYM>/1d.csv``, US trading-day calendar, ~252/yr, full history 2010-2026). The live desk
FILLS on Binance single-stock ``TRADIFI_PERPETUAL`` perps (``data_live_tradfi/<SYM>/1d.csv``, 24/7
calendar-daily incl. weekend bars). Because signal (Yahoo) and execution (perp) use DIFFERENT series
for the same recent day, they diverge (a ~179 bps single-day parity/live gap).

``load_tradfi_spliced`` returns the SAME output shape as ``core_tradfi.load_tradfi`` — a
``{ticker: OHLCV DataFrame indexed by open_time ms}`` dict — but each name's OHLC is the leak-safe
SPLICE: the RECENT period uses the perp (the instrument actually traded), Yahoo only for the deep
history the perp lacks.

======================================================================================= THE SPLICE
1. Load the Yahoo frame via ``ct.load_tradfi`` (trading-day, full history) and the raw 24/7 perp
   frame from ``data_live_tradfi/<SYM>/1d.csv``.
2. TRADING-DAY-ALIGN the perp: inner-join the perp onto the Yahoo trading-day ``open_time`` index —
   keep only perp bars whose ``open_time`` is a Yahoo trading day. Weekend/holiday perp bars are
   DROPPED; their price move folds into the adjacent trading-day return (a Fri->Mon return spans the
   dropped Sat+Sun perp bars). Result: the perp on the SAME ~252/yr trading-day grid as Yahoo — no
   calendar-day-vs-trading-day density contamination.
3. BOUNDARY ``d`` = the FIRST trading-day ``open_time`` where the aligned perp exists (each name's
   point-in-time perp inception). A name with no perp / <2 aligned perp bars is returned as the pure
   Yahoo frame (no splice).
4. RETURN-CHAIN RE-BASE (no level jump, no leak), per OHLC field ``x`` in {open, high, low, close}::
       spliced_x[t] = yahoo_x[t]                              for t <  d
       spliced_x[d] = yahoo_x[d]                              (anchor: exact, |Δ| == 0)
       spliced_x[t] = yahoo_x[d] * perp_x[t] / perp_x[d]      for t >  d
   Each field is anchored on its OWN d-value ``yahoo_x[d]/perp_x[d]`` (both read AT d, past-only),
   so the first spliced return at d+1 is ``perp[d+1]/perp[d]`` — a PURE perp return; the Yahoo level
   never enters a perp return. The return INTO d stays pure-Yahoo (open[d]/open[d-1] with both legs
   Yahoo), so there is no Yahoo->perp level jump at the boundary. ``ct.panels`` builds ``ret_fwd``
   from ``open`` and the iter-016 signals read ``close``; both series carry the property above.

LEAK SAFETY: everything is a function of data at or before each timestamp. The re-base anchor is
``yahoo_x[d]`` and ``perp_x[d]`` (both at d, past-only). Truncating every input frame to
``<= as_of`` and re-splicing reproduces the full panel's ``<= as_of`` rows bit-for-bit (see
``splice_verify.py`` / the tests). Because every live perp inception is deep in 2026 (far
past the immutable ``OOS_CUTOFF = 2025-03-24``), the ENTIRE in-sample window is ``< d`` for every
name — so the spliced IS is BIT-IDENTICAL to pure ``ct.load_tradfi`` and the confirmed IS baseline
cannot have moved. The splice only alters the recent (2026) OOS tail, on the traded instrument.

===================================================================== MID-SERIES SPLIT DETECTION
Binance single-stock perps do not always split-adjust in lockstep with the underlying (found via
CRWDUSDT, 2026-07-02: perp closed the day at ~1/4 its open, a real 4:1 split the RAW perp feed never
rebased — Yahoo, loaded ``auto_adjust=True``, already handles it cleanly). Left alone, that single
un-adjusted bar reads as a ~-75% one-day crash and permanently mis-scales every spliced price after
it (the single boundary-anchor multiplier no longer matches the post-split share count).

Detection compares perp's day-over-day return against Yahoo's SAME-DAY (already split-adjusted)
return on the aligned trading-day grid — a real split shows a huge one-day divergence there since
Yahoo tracks the true price throughout; ordinary basis/tracking noise between perp and Yahoo is a
few bps, never remotely close. But a raw divergence alone is NOT sufficient: ~10 names in this
universe show a single-day divergence >15% that reverts the very next day (a transient data blip,
confirmed by checking the perp/Yahoo ratio before vs. after — CRWD's ratio is a stable ~4.0x for
weeks, snaps to ~1.0x, and STAYS there; the blips return to ~1.0x within a day). Only a PERSISTENT
ratio shift (checked against a forward window) is treated as a real split and re-based; a one-day
reversion is left untouched — see ``_detect_split_points``.

CAVEAT (a deliberate, bounded exception to "past-only"): confirming persistence needs a few
FORWARD trading days of data, so a split within the last ``SPLIT_CONFIRM_WINDOW`` bars may not yet
be detected — the correction lands within that window, once enough data exists to distinguish it
from a one-day blip. This is a data-quality revision (identical in spirit to Yahoo's own
``auto_adjust=True`` retroactively rescaling history when a split posts), not a lookahead into any
tradeable signal: by the time a day flips from "unconfirmed" to "confirmed split", it is already
days in the past and irrelevant to what any current decision would have used as inputs.

Run:  uv run python analysis/portfolio/tradfi/splice_loader.py [--sym TSLAUSDT]
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
import perp_map_tradfi as pm  # noqa: E402

LIVE_DIR = ct._ROOT / "data_live_tradfi"
_OHLC = ("open", "high", "low", "close")
_PERP_USECOLS = ["open_time", "open", "high", "low", "close", "volume"]

# Mid-series split detection (see module docstring "MID-SERIES SPLIT DETECTION").
SPLIT_DIVERGE_THRESHOLD = 0.15  # single-day |perp_ret - yahoo_ret| to flag a CANDIDATE split day
SPLIT_CONFIRM_WINDOW = 3  # trading days each side used to confirm the ratio shift PERSISTS
SPLIT_PERSIST_THRESHOLD = 0.15  # required |after/before - 1| on the perp/yahoo ratio to confirm


def _detect_split_points(
    yahoo: pd.DataFrame,
    aligned: pd.DataFrame,
    diverge_threshold: float = SPLIT_DIVERGE_THRESHOLD,
    window: int = SPLIT_CONFIRM_WINDOW,
    persist_threshold: float = SPLIT_PERSIST_THRESHOLD,
) -> list[int]:
    """Sorted list of ``open_time`` (ms) where the perp feed has an un-adjusted split that Yahoo
    (already split-adjusted) does not show — a PERSISTENT perp/Yahoo ratio shift, not a one-day
    blip. ``aligned`` is the perp frame already restricted to Yahoo's trading-day index."""
    if len(aligned) < 2 * window + 1:
        return []
    yahoo_c = yahoo["close"].reindex(aligned.index)
    perp_ret = aligned["close"].pct_change()
    yahoo_ret = yahoo_c.pct_change()
    diverge = (perp_ret - yahoo_ret).abs()
    ratio = aligned["close"] / yahoo_c

    out: list[int] = []
    candidates = diverge[diverge > diverge_threshold].index
    for i, t in enumerate(aligned.index):
        if t not in candidates:
            continue
        if i < window or i + window >= len(aligned):
            continue  # can't confirm persistence yet — near an edge of the loaded data
        before = float(ratio.iloc[i - window : i].median())
        after = float(ratio.iloc[i + 1 : i + 1 + window].median())
        if before <= 0 or not (after == after) or not (before == before):  # NaN-safe
            continue
        if abs(after / before - 1.0) > persist_threshold:
            out.append(int(t))
    return out


def load_perp_frame(perp_sym: str, live_dir: Path = LIVE_DIR) -> pd.DataFrame | None:
    """Raw 24/7 perp daily OHLCV frame indexed by ``open_time`` (ms), or ``None`` if absent."""
    p = live_dir / perp_sym / "1d.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, usecols=_PERP_USECOLS)
    df = df.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    return df.astype(float)


def splice_one(yahoo: pd.DataFrame, perp: pd.DataFrame | None) -> tuple[pd.DataFrame, int | None]:
    """Return ``(spliced_frame, d)`` for one name — the leak-safe Yahoo/perp OHLC splice.

    ``spliced_frame`` shares the Yahoo trading-day index; OHLC on ``t >= d`` is the perp re-based to
    the Yahoo level at the boundary ``d`` (each field on its own past-only anchor there). ``d`` is
    the perp-inception ``open_time`` (ms), or ``None`` when there is no valid perp overlap (< 2
    aligned bars) — in which case the pure Yahoo frame is returned unchanged.

    Any CONFIRMED mid-series split in the raw perp feed (see module docstring) gets an additional
    anchor at its own breakpoint, so the un-adjusted split never reads as a fake return and every
    post-split level matches Yahoo's true (split-adjusted) price, not a stale pre-split scale.
    """
    if perp is None:
        return yahoo.copy(), None
    # trading-day-align: keep only perp bars whose open_time is a Yahoo trading day (inner join).
    common = perp.index.intersection(yahoo.index)
    aligned = perp.loc[common].sort_index()
    if len(aligned) < 2:
        return yahoo.copy(), None
    d = int(aligned.index.min())  # PIT perp inception on the trading-day grid
    splits = [t for t in _detect_split_points(yahoo, aligned) if t > d]
    breakpoints = sorted({d, *splits})
    out = yahoo.copy()
    for field in _OHLC:
        rebased = pd.Series(index=aligned.index, dtype=float)
        for i, bp in enumerate(breakpoints):
            seg_end = breakpoints[i + 1] if i + 1 < len(breakpoints) else None
            mask = aligned.index >= bp
            if seg_end is not None:
                mask = mask & (aligned.index < seg_end)
            seg = aligned.index[mask]
            if len(seg) == 0:
                continue
            # At d (inception) each field anchors independently — the whole bar is the first
            # REAL trading bar, no intra-bar contamination. At a mid-series split the split day's
            # OWN bar can straddle the transition (open/high still pre-split, low/close already
            # post-split — see CRWD 2026-07-02), so every field anchors off 'close' alone, the
            # one field confirmed clean by end-of-day (the split day itself is still forced exact
            # to Yahoo below, so this anchor only matters for days AFTER the split).
            anchor_field = field if bp == d else "close"
            anchor = float(yahoo.at[bp, anchor_field]) / float(aligned.at[bp, anchor_field])
            rebased.loc[seg] = anchor * aligned.loc[seg, field]
        rebased.loc[d] = float(yahoo.at[d, field])  # anchor EXACT at d (|Δ| == 0, no float drift)
        for bp in splits:
            rebased.loc[bp] = float(yahoo.at[bp, field])  # exact at each confirmed split too
        out.loc[aligned.index, field] = rebased
    if "volume" in aligned.columns:  # traded-instrument volume on spliced bars (unused downstream)
        out["volume"] = out["volume"].astype(float)  # Yahoo volume is int64; perp is float
        out.loc[aligned.index, "volume"] = aligned["volume"]
    return out, d


def load_tradfi_spliced(
    universe, data_dir: str | None = None, live_data_dir: str | None = None
) -> dict[str, pd.DataFrame]:
    """Yahoo->perp spliced ``{ticker: OHLCV DataFrame}`` — drop-in for ``ct.load_tradfi``.

    Each name's OHLC uses the trading-day-aligned, level-re-based perp wherever it exists (recent
    2026 tail) and pure Yahoo for the deep history. Leak-safe and IS-bit-identical by construction
    (see module docstring). ``live_data_dir`` overrides the perp store (default data_live_tradfi).
    """
    yahoo_coins = ct.load_tradfi(universe, data_dir)
    live_dir = Path(live_data_dir) if live_data_dir is not None else LIVE_DIR
    out: dict[str, pd.DataFrame] = {}
    for sym, ydf in yahoo_coins.items():
        perp_sym = pm.PERP_SYMBOL_MAP.get(sym, sym)  # stem==perp symbol here; identity fallback
        perp = load_perp_frame(perp_sym, live_dir)
        spliced, _d = splice_one(ydf, perp)
        out[sym] = spliced
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sym", default="TSLAUSDT", help="inspect one name's splice boundary")
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()

    ydf = ct.load_tradfi([args.sym], args.data_dir).get(args.sym)
    if ydf is None:
        print(f"{args.sym}: no Yahoo frame")
        return
    perp = load_perp_frame(pm.PERP_SYMBOL_MAP.get(args.sym, args.sym))
    spliced, d = splice_one(ydf, perp)
    if d is None:
        print(f"{args.sym}: no perp overlap — pure Yahoo (no splice)")
        return
    dts = pd.to_datetime(spliced.index, unit="ms")
    n_perp = int((spliced.index >= d).sum())
    d_dt = pd.to_datetime(d, unit="ms").date()
    anchor_dev = abs(spliced.at[d, "close"] - ydf.at[d, "close"])
    print(f"{args.sym}: boundary d = {d_dt}  ({n_perp} spliced perp bars, {len(spliced)} total)")
    print(f"  span {dts.min().date()} -> {dts.max().date()}   OOS_CUTOFF = {ct.OOS_CUTOFF.date()}")
    print(f"  spliced_close[d] == yahoo_close[d] : |Δ| = {anchor_dev:.3e}")


if __name__ == "__main__":
    main()

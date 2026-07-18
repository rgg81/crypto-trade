"""Weekly PIT top-40 universe — organizer-owned, computed on the FULL crypto pool.

The eligibility mask is TOURNAMENT DATA, not team code: it is computed here on the full
(~500-symbol) pool, shipped inside the frozen snapshot (``data_is/_universe/eligibility.csv``,
manifest-hashed), and applied by the organizer engine. Teams receive it read-only in ``aux``.
Recomputing a rank on the truncated snapshot pool would diverge from full-pool truth (a coin
ranked 45 full-pool can rank ≤40 among the snapshot's symbols), hence ship-not-recompute.

Semantics (all past-only):
  liq[t]  = qv.rolling(DVOL_WIN=21, min_periods=DVOL_MIN_PERIODS=18).mean().shift(1)
            — trailing 7-day mean 8h quote-volume, known strictly before candle t.
            min_periods=18 tolerates a short mid-life exchange outage; a NEW listing is
            additionally age-gated (>= DVOL_WIN candles of history) so a coin cannot rank
            off a partial first week.
  refresh = Monday 00:00 UTC candles. rank = liq row-rank descending; top-40 wins.
  mask[t] = the list in force during candle t (last refresh at or before open[t]); False
            before the first refresh. A coin dropping out at a refresh is force-closed by
            the engine at the NEXT candle open (≤8h after the refresh — the weekly floor).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from portfolio_tournament import constants as tc  # noqa: E402


def pool_symbols(src: Path) -> list[str]:
    """The full crypto pool: every ``<SYM>/8h.csv`` passing the pure-crypto filter, sorted."""
    return sorted(
        p.parent.name for p in Path(src).glob("*/8h.csv") if tc.crypto_pool_symbol(p.parent.name)
    )


def load_qv_panel(src: Path, symbols: list[str] | None = None) -> pd.DataFrame:
    """Quote-volume panel (ms open_time index × symbols) on the aligned full 8h grid."""
    src = Path(src)
    if symbols is None:
        symbols = pool_symbols(src)
    cols: dict[str, pd.Series] = {}
    for sym in symbols:
        k = pd.read_csv(src / sym / "8h.csv", usecols=["open_time", "quote_volume"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        cols[sym] = k["quote_volume"].astype(float)
    qv = pd.DataFrame(cols)
    lo = max(int(qv.index.min()), int(tc.TRN_IS_START.value // 1_000_000))
    grid = pd.RangeIndex(lo, int(qv.index.max()) + tc.STEP_MS, tc.STEP_MS)
    return qv.reindex(pd.Index(grid, name="open_time"))


def weekly_topn_mask(qv: pd.DataFrame, *, top_n: int = tc.TOP_N) -> pd.DataFrame:
    """Bool eligibility panel on the qv grid: the weekly top-``top_n`` list in force per candle."""
    liq = qv.rolling(tc.DVOL_WIN, min_periods=tc.DVOL_MIN_PERIODS).mean().shift(1)
    age = qv.notna().cumsum().shift(1)  # candles of history strictly before t
    liq = liq.where(age >= tc.DVOL_WIN)  # new listings need a FULL ranking window first
    dt = pd.to_datetime(qv.index, unit="ms")
    refresh = (dt.weekday == tc.REFRESH_WEEKDAY) & (dt.hour == 0)
    rank = liq.loc[refresh].rank(axis=1, ascending=False, method="min")
    mask = (rank <= top_n).reindex(qv.index).ffill().fillna(False).astype(bool)
    return mask


def membership_spans(mask: pd.DataFrame) -> dict[str, dict]:
    """Per symbol ever in the mask: {sym: {first_ms, last_ms, n_candles}} of True cells."""
    out: dict[str, dict] = {}
    for sym in mask.columns:
        col = mask[sym]
        if not col.any():
            continue
        idx = col[col].index
        out[sym] = {
            "first_ms": int(idx.min()),
            "last_ms": int(idx.max()),
            "n_candles": int(col.sum()),
        }
    return out


def build(src: Path = tc.MAIN_DATA_DIR, build_dir: Path = tc.BUILD_DIR) -> dict:
    """Compute the full-pool mask + unions; persist to ``BUILD_DIR``. Returns a summary."""
    src = Path(src)
    symbols = pool_symbols(src)
    qv = load_qv_panel(src, symbols)
    mask = weekly_topn_mask(qv)

    is_mask = mask[mask.index <= tc.IS_END_MS]
    hold_hi_ms = int(tc.TRN_HOLD_HI.value // 1_000_000)
    full_mask = mask[mask.index < hold_hi_ms]
    union_is = sorted(c for c in mask.columns if is_mask[c].any())
    union_full = sorted(c for c in mask.columns if full_mask[c].any())

    build_dir.mkdir(parents=True, exist_ok=True)
    mask.astype(int).to_csv(build_dir / "eligibility_full.csv")
    spans = membership_spans(full_mask)
    (build_dir / "union_is.json").write_text(json.dumps(union_is, indent=0) + "\n")
    (build_dir / "union_full.json").write_text(json.dumps(union_full, indent=0) + "\n")
    (build_dir / "membership_spans.json").write_text(
        json.dumps(spans, indent=2, sort_keys=True) + "\n"
    )

    dt = pd.to_datetime(full_mask.index, unit="ms")
    per_year = {int(y): int(full_mask[dt.year == y].any().sum()) for y in sorted(set(dt.year))}
    summary = {
        "pool": len(symbols),
        "union_is": len(union_is),
        "union_full": len(union_full),
        "per_year_distinct_members": per_year,
        "grid_lo_ms": int(mask.index.min()),
        "grid_hi_ms": int(mask.index.max()),
    }
    (build_dir / "pool_meta.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else tc.MAIN_DATA_DIR
    print(json.dumps(build(src), indent=2))

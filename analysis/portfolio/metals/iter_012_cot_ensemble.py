"""iter-012 — ENSEMBLE with the CFTC COT positioning sleeve (uncorrelated, leak-safe).

The iter-011 bad-month diagnostic localized the losses to the TRANSITIONAL-chop regime (breadth
0.3-0.5), driven by the long-gold anchor whipsawing. De-risking the anchor on breadth FAILS (it
kills the bull; breadth-level can't tell a bull pullback from a bear onset). The fix is an ENSEMBLE:
add a small dose of a genuinely UNCORRELATED, NON-PRICE sleeve — the iter-004 CFTC managed-money
CONTRARIAN positioning tilt (gold/silver only) — which fades crowd extremes independent of price.

desk[t,i] = iter-010 desk[t,i] + cot_w · dep_cot[t,i]   (then the iter-011 deadband)   cot_w=0.3

Effect (position-level honest, canonical data): the chop bad-bucket is NEUTRALIZED (mean
−0.38%→−0.04%/month) and every regime lifts — IS +0.21→+0.38, BEAR +0.36→+0.58, BULL +1.66→+1.72.
cot_w is a smooth IS-basin peaking at 0.3 (0.1-0.4 all all-weather-improving). GOLD/SILVER-ONLY COT
(the iter-004 robust subset — full-4 COT was OOS-FALSIFIED, a dead-path). IS-only tuned.

LEAK-SAFETY (the COT is the highest-risk component): align_cot_to_grid applies each weekly report
only at snapshot+RELEASE_LAG_DAYS(6) (Tuesday snapshot → Friday public → +6d safety); the z-score +
rvol are causal; deployed_from_raw lags the book one candle. iter-004 triple-verified this; price-
future-corruption here is bit-clean (0.00e+00). Wraps iter-011; CHAMP12 deployed via live_weights.

Run:  uv run python analysis/portfolio/metals/iter_012_cot_ensemble.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import iter_004_cot as cot  # noqa: E402
import iter_008_allweather as a8  # noqa: E402
import iter_010_breadth_accel as i10  # noqa: E402
import iter_011_deadband as i11  # noqa: E402
import universe_metals as um  # noqa: E402

# iter-011 + gold/silver COT positioning sleeve @ 0.3, applied at the +6d release lag (leak-safe)
CHAMP12 = {**i11.CHAMP11, "cot_w": 0.3, "cot_lag": cot.RELEASE_LAG_DAYS}
COT_COLS = ("XAUUSDT", "XAGUSDT")  # gold/silver only (full-4 COT was OOS-FALSIFIED; dead-path)
_COT_CACHE: pd.DataFrame | None = None


def _cot_df() -> pd.DataFrame:
    """Lazy-load the COT parquet (refreshed weekly by ingest_cot); live engine clears via cache."""
    global _COT_CACHE
    if _COT_CACHE is None:
        _COT_CACHE = cot.load_cot()
    return _COT_CACHE


def clear_cot_cache() -> None:
    global _COT_CACHE
    _COT_CACHE = None


def desk_book(coins: dict[str, pd.DataFrame], **over) -> tuple[pd.DataFrame, pd.Series]:
    """iter-010 desk + cot_w·(gold/silver COT positioning sleeve), then the iter-011 deadband."""
    cfg = {**CHAMP12, **over}
    base_keys = {k: v for k, v in cfg.items() if k not in ("deadband", "cot_w", "cot_lag")}
    raw_desk, b = i10.desk_book(coins, **base_keys)
    if cfg["cot_w"] > 0:
        rf = um.panels(coins)["ret_fwd"]
        craw = cot.cot_mm_contrarian_raw(coins, _cot_df(), cols=COT_COLS, lag_days=cfg["cot_lag"])
        _, dep_cot = um.deployed_from_raw(craw, rf)
        raw_desk = raw_desk.add(
            dep_cot.reindex(columns=raw_desk.columns, fill_value=0.0) * cfg["cot_w"], fill_value=0.0
        )
    return i11.hysteresis_band(raw_desk, cfg["deadband"]), b


def desk_net(coins: dict[str, pd.DataFrame], **over) -> pd.Series:
    """POSITION-LEVEL honest net of the COT-ensemble deadband-held book."""
    held, _ = desk_book(coins, **over)
    rf = um.panels(coins)["ret_fwd"]
    pnl = (held * rf.reindex(columns=held.columns)).sum(axis=1)
    cost = um.COST_SIDE * held.diff().abs().sum(axis=1)
    return (pnl - cost).dropna()


def next_target_weights(coins: dict[str, pd.DataFrame], tol: float = 1e-9) -> dict:
    """Per-metal held position for the just-opened candle — the live target."""
    held, b = desk_book(coins)
    last = held.iloc[-1]
    pos = last[last.abs() > tol]
    return {
        **{s: float(v) for s, v in pos.items()},
        "_meta": {
            "as_of": str(held.index[-1]),
            "breadth": float(
                a8.breadth_down(um.panels(coins)["close"], "ma", CHAMP12["win"]).iloc[-1]
            ),
            "gross": float(last.abs().sum()),
            "n_positions": int(len(pos)),
        },
    }


def scorecard() -> None:
    a8.bear.ingest_bear()
    cb, cm = um.load_metals(a8.BEAR_DIR), um.load_metals(a8.MAIN_DIR)
    print("=" * 92)
    print("iter-012 — COT POSITIONING ENSEMBLE (gold/silver, cot_w=0.3) on iter-011 (leak-safe)")
    print("=" * 92)
    for lbl, cw in (("iter-011 (no COT)", 0.0), ("iter-012 (cot_w=0.3)", 0.3)):
        nb, nm = desk_net(cb, cot_w=cw), desk_net(cm, cot_w=cw)
        b = i10._seg(nb, "2011-09-01", "2015-03-24")
        i = i10._seg(nm, "2000-01-01", str(um.OOS_CUTOFF.date()))
        u = i10._seg(nm, str(um.OOS_CUTOFF.date()), "2100-01-01")
        print(
            f"  {lbl:22} BEAR={b['sharpe']:+.2f}/{b['dd'] * 100:5.1f}%  IS={i['sharpe']:+.2f}  "
            f"BULL={u['sharpe']:+.2f}  worst-DD={min(b['dd'], i['dd'], u['dd']) * 100:5.1f}%"
        )


if __name__ == "__main__":
    scorecard()

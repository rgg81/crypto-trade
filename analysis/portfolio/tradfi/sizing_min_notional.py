"""Position-sizing feasibility — can the iter-016 deployed book be traded at a $10k budget?

The live desk holds the vol-target-scaled DEPLOYED weight book (gross Σ|w| ≈ scale·s_vix ≈ 0.7 now)
across 68 Binance TradFi perps (ex-PAYP). At a small equity each leg's dollar notional shrinks, and
Binance USDⓈ-M perps enforce two OFFICIAL filters (fetched live from exchangeInfo, not assumed):

  * MIN_NOTIONAL  — a leg's price*qty must be >= `notional` USDT (all 69 TradFi perps: 5 USDT).
  * LOT_SIZE      — qty is a multiple of `stepSize`, >= `minQty` (all 69: step 0.01, minQty 0.01).

Consequence: a leg is UNTRADEABLE if |w|*equity < max(5, 0.01*price) (below min-notional or one
lot). And every tradeable leg is QUANTIZED to 0.01*price of notional — a granularity 10x coarser at
$10k than $100k and worst on high-priced perps (0.01*$500 = $5/step on BRKB vs $0.14 on a $14 name).
This script quantizes the ACTUAL current deployed book to the live filters at several equity levels
and measures: dropped legs, gross realized vs target, dollar-neutrality drift, and the weight-space
tracking error (implementation shortfall) — $10k vs $100k — plus the min equity for a clean book.

Run: uv run python analysis/portfolio/tradfi/sizing_min_notional.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import core_tradfi as ct  # noqa: E402
import live_weights_tradfi as lw  # noqa: E402  — the deployed target-weight bridge
import universe_tradfi as ut  # noqa: E402

FAPI = "https://fapi.binance.com/fapi/v1/exchangeInfo"
LIVE_EXCLUDED = {"PAYPUSDT"}  # broken perp (Phase-2b) — the live desk drops it
EQUITIES = (10_000.0, 25_000.0, 100_000.0)


def _filters() -> dict[str, dict]:
    """{symbol: {min_notional, step, min_qty}} for the TradFi perps, from LIVE exchangeInfo."""
    info = httpx.get(FAPI, timeout=30.0).json()
    out: dict[str, dict] = {}
    for s in info["symbols"]:
        sym = s["symbol"]
        if s.get("contractType") != "TRADIFI_PERPETUAL" or sym not in ut.SECTOR_MAP:
            continue
        f = {x["filterType"]: x for x in s["filters"]}
        out[sym] = {
            "min_notional": float(f["MIN_NOTIONAL"]["notional"]),
            "step": float(f["LOT_SIZE"]["stepSize"]),
            "min_qty": float(f["LOT_SIZE"]["minQty"]),
        }
    return out


def _price(sym: str) -> float | None:
    """Latest close: prefer the Binance perp mark (data_live_tradfi), fall back to the Yahoo bar."""
    for d in ("data_live_tradfi", "data"):
        base = ct._ROOT / d / sym / "1d.csv"
        if base.exists():
            df = pd.read_csv(base)
            if len(df):
                return float(df["close"].iloc[-1])
    return None


def _quantize(w: float, price: float, filt: dict, equity: float) -> tuple[float, bool]:
    """Round a target weight to a tradeable (realized_weight, tradeable?) under the perp filters."""
    target_notional = abs(w) * equity
    step, min_qty, min_notional = filt["step"], filt["min_qty"], filt["min_notional"]
    qty = round(target_notional / price / step) * step  # nearest whole lot
    if qty < min_qty or qty * price < min_notional:
        return 0.0, False  # below one lot or below min-notional -> cannot place this leg
    realized_notional = qty * price
    return (realized_notional / equity) * (1.0 if w > 0 else -1.0), True


def main() -> None:
    filt = _filters()
    tgt = lw.deployed_target_weights(pd.Timestamp("now"))  # latest on-disk bar
    meta = tgt.pop("_meta")
    book = {s: w for s, w in tgt.items() if s not in LIVE_EXCLUDED}
    prices = {s: _price(s) for s in book}
    missing = [s for s, p in prices.items() if not p]
    book = {s: w for s, w in book.items() if prices.get(s)}

    print("=" * 98)
    print("iter-016 SIZING FEASIBILITY vs Binance official perp minimums (MIN_NOTIONAL / LOT_SIZE)")
    print("=" * 98)
    mn = {f["min_notional"] for f in filt.values()}
    st = {f["step"] for f in filt.values()}
    print(f"  official filters (live): MIN_NOTIONAL={mn} USDT, LOT_SIZE step={st} units")
    print(
        f"  deployed book as_of {meta['as_of'].date()}: {len(book)} legs "
        f"(ex-PAYP), gross Σ|w|={meta['gross']:.3f}, net Σw={meta['net_dollar']:+.3f}"
        + (f"  [no price for {missing}]" if missing else "")
    )
    gross_t = sum(abs(w) for w in book.values())
    net_t = sum(book.values())

    print(
        f"\n  {'equity':>9} {'trade':>6} {'drop':>5} {'grossT':>7} {'grossR':>7} "
        f"{'netT':>7} {'netR':>7} {'wTE':>7} {'maxLegErr':>10}"
    )
    for eq in EQUITIES:
        n_tr = n_dr = 0
        gross_r = net_r = te = 0.0
        max_rel = ("", 0.0)
        for s, w in book.items():
            rw, ok = _quantize(w, prices[s], filt[s], eq)
            if ok:
                n_tr += 1
            else:
                n_dr += 1
            gross_r += abs(rw)
            net_r += rw
            te += abs(rw - w)
            rel = abs(rw - w) / abs(w) if w else 0.0
            if rel > max_rel[1]:
                max_rel = (s, rel)
        print(
            f"  ${eq:>8,.0f} {n_tr:>6} {n_dr:>5} {gross_t:>7.3f} {gross_r:>7.3f} "
            f"{net_t:>+7.3f} {net_r:>+7.3f} {te:>7.3f} {max_rel[0]:>6}{max_rel[1] * 100:>4.0f}%"
        )

    # min equity so every MATERIAL leg clears its floor max(min_notional, one lot at price).
    # exclude immaterial near-band legs (|w| < 10bps) — a ~0-weight leg divides to a meaningless
    # huge number and is economically nothing to skip. Report at a few materiality thresholds.
    for thr in (0.0005, 0.0010, 0.0020):
        mat = {s: w for s, w in book.items() if abs(w) >= thr}
        need = {
            s: max(filt[s]["min_notional"], filt[s]["step"] * prices[s]) / abs(w)
            for s, w in mat.items()
        }
        b = max(need, key=need.get)
        me = max(need.values())
        print(
            f"\n  legs |w| >= {thr * 100:.2f}% ({len(mat)}): min equity all-tradeable = ${me:,.0f}"
            f"  (binder {b} w={mat[b]:+.4f})"
        )
    # gross share of the legs DROPPED at $10k (the economic cost of the min-notional floor)
    dropped = [(s, w) for s, w in book.items() if not _quantize(w, prices[s], filt[s], 10_000.0)[1]]
    dg = sum(abs(w) for _, w in dropped)
    print(
        f"\n  at $10k: {len(dropped)} legs drop {sorted(s for s, _ in dropped)} "
        f"= {dg:.4f} of {gross_t:.3f} gross ({dg / gross_t * 100:.2f}% of book)"
    )
    # smallest legs (the ones that drop first at low equity)
    small = sorted(book.items(), key=lambda kv: abs(kv[1]))[:6]
    print("  smallest legs (drop first):  " + "  ".join(
        f"{s} |w|={abs(w):.4f}=${abs(w) * 10_000:,.0f}@10k" for s, w in small
    ))
    # highest-priced legs (worst quantization granularity)
    hi = sorted(book.items(), key=lambda kv: -prices[kv[0]])[:6]
    print("  highest-priced (coarsest step): " + "  ".join(
        f"{s} ${prices[s]:,.0f}(step ${0.01 * prices[s]:.2f})" for s, w in hi
    ))


if __name__ == "__main__":
    main()

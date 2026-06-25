"""metals-portfolio EXPLORATION-001 — long-biased TREND ANCHOR (the foundation iteration).

The first metals iteration: a long-only trend-following book on the 4 precious-metal perps
(gold / silver / platinum / palladium). Each metal always carries a base-load long FLOOR and a
trend overlay that ADDS exposure when a confirmed uptrend is in force (fast EMA > slow EMA) and
cuts back to the FLOOR otherwise. It NEVER shorts — metals are a structurally long, store-of-value
universe, so the anchor expresses "always own some, lean in when the trend is up".

Mechanics (leak-safe, mirrors iter_002_top20.build):
  - Signal decided on close[t] (EMA cross is causal — only past closes), sized inverse-vol.
  - `net_from_raw` gross-normalises, `.shift(1)`-lags the weight book (so expo[t] from close[t]
    is deployed at open[t+1]), charges taker cost on |Δw| turnover, and vol-targets the portfolio.
  - Ragged starts (platinum/palladium from 2022) handled point-in-time via `elig = close.notna()`
    → a metal carries 0 weight until it has price history. No forward-fill, no fabrication.

This module is IN-SAMPLE-ONLY in its reporting. OOS (>= OOS_CUTOFF) is HIDDEN and never printed;
it is revealed only at a future CONFIRMATION. `msharpe(net, LO0, OOS_CUTOFF)` is the IS Sharpe.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from universe_metals import (
    LO0,
    OOS_CUTOFF,
    VOL_WIN,
    load_metals,
    maxdd,
    msharpe,
    net_from_raw,
    panels,
    turnover,
)

# ── Center config (the registered candidate) ─────────────────────────────────────────────
EMA_FAST = 84  # 28d trend filter in 8h candles
EMA_SLOW = 189  # 63d trend filter in 8h candles
FLOOR = 0.5  # base-load long exposure (always own at least half a unit when eligible)

# ── Robustness sweep grid (reporting only — NOT for cell selection) ──────────────────────
SWEEP_FAST = (63, 84)
SWEEP_SLOW = (168, 189, 210)
SWEEP_FLOOR = (0.25, 0.5, 0.75)


def build_raw(
    coins: dict[str, pd.DataFrame],
    ema_fast: int = EMA_FAST,
    ema_slow: int = EMA_SLOW,
    floor: float = FLOOR,
) -> pd.DataFrame:
    """Pre-`net_from_raw` SIGNED RAW weight book for the long-biased trend anchor.

    Returns the inverse-vol-sized `(expo / rvol).where(elig, 0.0)` panel — the exact input the
    anchor hands to `net_from_raw`. Exposed so an overlay (iter-002) can combine at the RAW-weight
    level (parity-correct: ONE `net_from_raw` over the summed book, no post-trade netting).

    Per metal: exposure ∈ {floor, 1.0} — `floor` always, stepped up to 1.0 while fast EMA > slow
    EMA (confirmed uptrend). NEVER shorts: `expo` and therefore `raw` are non-negative everywhere.

    Look-ahead audit: `ewm(...).mean()` is causal (only past+present closes). `up`/`expo` at t use
    close[t]; the downstream `net_from_raw` lags `raw` by one candle, so expo[t] is filled at
    open[t+1] (decided at close[t], traded next open) — no future information enters the decision.
    `rvol` and `elig` are likewise past/present-only.
    """
    pan = panels(coins)
    close = pan["close"]
    elig = close.notna()  # PIT eligibility — a metal carries weight only once it has price history
    rvol = close.pct_change().rolling(VOL_WIN).std()  # 28d realized vol for inverse-vol sizing
    ef = close.ewm(span=ema_fast, adjust=False).mean()
    es = close.ewm(span=ema_slow, adjust=False).mean()
    up = (ef > es).astype(float)  # 1.0 in a confirmed uptrend, else 0.0
    expo = floor + (1.0 - floor) * up  # in {floor, 1.0}, long-only — never negative
    return (expo / rvol).where(elig, 0.0)  # inverse-vol sized; 0 where the metal has no history


def build(
    coins: dict[str, pd.DataFrame],
    ema_fast: int = EMA_FAST,
    ema_slow: int = EMA_SLOW,
    floor: float = FLOOR,
) -> tuple[pd.Series, pd.DataFrame]:
    """Long-biased trend anchor → (vol-targeted net return, deployed weight book).

    Thin wrapper: `build_raw` produces the signed raw book; the leak-safe `net_from_raw` core
    (gross-norm → .shift(1) lag → cost → vol-target) turns it into a vol-targeted net return and
    the deployed weight book. Bit-identical to the pre-refactor inline path.
    """
    ret_fwd = panels(coins)["ret_fwd"]
    raw = build_raw(coins, ema_fast, ema_slow, floor)
    return net_from_raw(raw, ret_fwd)


def _year_breakdown_is(net: pd.Series) -> dict[int, float]:
    """Per-year IS net% (sum of per-candle net within the IS window, in percent)."""
    s = net[net.index < OOS_CUTOFF]
    return {int(y): round(v * 100, 1) for y, v in s.groupby(s.index.year).sum().items()}


def _is_line(label: str, net: pd.Series, w: pd.DataFrame) -> None:
    """IS-only one-liner: Sharpe / maxDD / netTot% / turnover-per-candle."""
    eq = (1 + net).cumprod()
    sr = msharpe(net, LO0, OOS_CUTOFF)
    dd = maxdd(net) * 100
    tot = (eq.iloc[-1] - 1) * 100
    tnov = turnover(w, LO0, OOS_CUTOFF)
    print(
        f"  {label:24} IS_Sharpe={sr:+.2f}  maxDD={dd:6.1f}%  "
        f"netTot={tot:+5.0f}%  turnover/candle={tnov:.4f}"
    )


def main() -> None:
    coins = load_metals()
    print(f"EXPLORATION-001: long-biased TREND ANCHOR — {len(coins)} metals {tuple(coins)}")
    print("  (IN-SAMPLE ONLY — OOS is hidden until CONFIRMATION)\n")

    # ── 1. Center config ────────────────────────────────────────────────────────────────
    print(f"[1] CENTER config  EMA{EMA_FAST}/{EMA_SLOW}  FLOOR={FLOOR}")
    net_c, w_c = build(coins, EMA_FAST, EMA_SLOW, FLOOR)
    _is_line("center", net_c, w_c)
    yr = _year_breakdown_is(net_c)
    print(f"      IS net%/yr = {yr}\n")

    # ── 2. Reference: always-long inverse-vol (FLOOR=1.0 → no trend overlay) ─────────────
    print("[2] REFERENCE  always-long inverse-vol (FLOOR=1.0, no trend filter) — the bar to beat")
    net_r, w_r = build(coins, EMA_FAST, EMA_SLOW, 1.0)
    _is_line("always-long", net_r, w_r)
    print()

    # ── 3. Robustness sweep (REPORT ALL CELLS — no best-cell selection) ──────────────────
    print(
        f"[3] ROBUSTNESS sweep  FAST{list(SWEEP_FAST)} × SLOW{list(SWEEP_SLOW)} × "
        f"FLOOR{list(SWEEP_FLOOR)}  ({len(SWEEP_FAST) * len(SWEEP_SLOW) * len(SWEEP_FLOOR)} cells)"
    )
    sweep_sr: list[float] = []
    for f in SWEEP_FAST:
        for s in SWEEP_SLOW:
            cells = []
            for fl in SWEEP_FLOOR:
                net_s, _ = build(coins, f, s, fl)
                sr = msharpe(net_s, LO0, OOS_CUTOFF)
                sweep_sr.append(sr)
                cells.append(f"FLOOR{fl}={sr:+.2f}")
            print(f"  EMA{f:>3}/{s:<3}  " + "  ".join(cells))
    arr = np.array(sweep_sr, dtype=float)
    n = len(arr)
    pos = float((arr > 0).mean() * 100)
    strong = float((arr > 0.20).mean() * 100)
    print(
        f"  summary: {n} cells  |  >0: {pos:.0f}%  |  >+0.20: {strong:.0f}%  |  "
        f"min={np.nanmin(arr):+.2f}  median={np.nanmedian(arr):+.2f}  max={np.nanmax(arr):+.2f}\n"
    )

    # ── 4. Drop-gold variant (center config, ex-XAUUSDT) ────────────────────────────────
    print("[4] DROP-GOLD  center config excluding XAUUSDT (gold-led but not gold-only)")
    coins_ng = {k: v for k, v in coins.items() if k != "XAUUSDT"}
    net_ng, w_ng = build(coins_ng, EMA_FAST, EMA_SLOW, FLOOR)
    _is_line("drop-gold", net_ng, w_ng)


if __name__ == "__main__":
    main()

"""metals-portfolio EXPLORATION-002 — MARKET-NEUTRAL dispersion OVERLAY on the trend anchor.

The anchor (iter-001) is a structurally long, gold-led trend book — it earns when metals trend up
and bleeds in the metals bear/chop years (2015 / 2018 / 2021 / 2023). This iteration adds a
DOLLAR-NEUTRAL dispersion overlay whose return stream is (by construction) decorrelated from — even
negatively correlated to — the anchor, so the combination earns in the anchor's bad years without
demanding metals go up.

The MN signal is a gold-DEFENSIVE dispersion: LONG gold (+1 unit), SHORT the other metals equally
(−1/(#present) each), then DEMEANED cross-sectionally so the deployed book is EXACTLY dollar-neutral
(Σ weight = 0 every bar). It expresses "when metals disperse, gold is the store-of-value anchor and
the industrials (silver / platinum / palladium) are the cyclical risk leg". Inverse-vol sized so the
two legs carry comparable risk.

Combination is PARITY-CORRECT: each arm's RAW book is gross-normalised, summed at the raw-weight
level with a mixing weight ALPHA, then a SINGLE `net_from_raw` does the lag / cost / vol-target. No
post-trade netting, no double-counting of cost — identical accounting to running one strategy whose
raw book is the blended book.

IN-SAMPLE-ONLY reporting. OOS (>= OOS_CUTOFF) is HIDDEN and never printed.
"""

from __future__ import annotations

import iter_001_trend as it  # noqa: E402  (anchor; build_raw is the parity-correct raw book)
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
ALPHA = 0.5  # mixing weight of the MN overlay on top of the (gross-normed) anchor book
MN_VOL_WIN = VOL_WIN  # 84 (28d) realized-vol window for the overlay's inverse-vol sizing
GOLD = "XAUUSDT"  # the store-of-value leg of the dispersion

# ── Robustness sweep grid (reporting only — NOT for cell selection) ──────────────────────
SWEEP_ALPHA = (0.25, 0.5, 0.75, 1.0)
SWEEP_VOL_WIN = (42, 63, 84, 126)


def mn_dispersion_raw(close: pd.DataFrame, vol_win: int = MN_VOL_WIN) -> pd.DataFrame:
    """Dollar-neutral gold-defensive dispersion → SIGNED raw weight book (pre-`net_from_raw`).

    LONG gold (+1), SHORT each other present metal equally (−1/#present), inverse-vol sized, then
    DEMEANED cross-sectionally so the deployed book is EXACTLY dollar-neutral (Σ weight = 0).

    Leak-safe: `rvol` and `elig` use only past/present closes; the downstream `net_from_raw` lags
    the whole book by one candle, so a signal decided at close[t] is deployed at open[t+1].
    """
    rvol = close.pct_change().rolling(vol_win).std()
    elig = close.notna()
    others = [c for c in close.columns if c != GOLD]
    sig = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    sig[GOLD] = elig[GOLD].astype(float) * 1.0
    pres = elig[others].sum(axis=1).replace(0, np.nan)  # #present industrial legs each bar
    for c in others:
        sig[c] = (-1.0 / pres).where(elig[c], 0.0)
    raw = (sig / rvol).where(elig & rvol.notna(), 0.0)
    raw = raw.sub(raw.mean(axis=1), axis=0)  # demean cross-section → exact dollar-neutrality
    return raw.fillna(0.0)


def gross_norm(raw: pd.DataFrame) -> pd.DataFrame:
    """Gross-normalise a raw book to unit gross (Σ|w| = 1) per bar; 0 where the book is flat."""
    g = raw.abs().sum(axis=1).replace(0, np.nan)
    return raw.div(g, axis=0).fillna(0.0)


def build_combined(
    coins: dict[str, pd.DataFrame],
    alpha: float = ALPHA,
    vol_win: int = MN_VOL_WIN,
) -> tuple[pd.Series, pd.DataFrame]:
    """Parity-correct: gross-norm(anchor) + alpha·gross-norm(MN) → ONE `net_from_raw`."""
    pan = panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    raw_combined = gross_norm(it.build_raw(coins)) + alpha * gross_norm(
        mn_dispersion_raw(close, vol_win)
    )
    return net_from_raw(raw_combined, ret_fwd)


def build_overlay(
    coins: dict[str, pd.DataFrame],
    vol_win: int = MN_VOL_WIN,
) -> tuple[pd.Series, pd.DataFrame]:
    """Standalone MN overlay → (vol-targeted net, deployed book) via the leak-safe core."""
    pan = panels(coins)
    return net_from_raw(mn_dispersion_raw(pan["close"], vol_win), pan["ret_fwd"])


# ── reporting helpers (IS-only) ──────────────────────────────────────────────────────────
def _is_monthly(net: pd.Series) -> pd.Series:
    """Monthly-summed net series over the IN-SAMPLE window only."""
    s = net[net.index < OOS_CUTOFF]
    return s.groupby(s.index.to_period("M")).sum()


def _year_breakdown_is(net: pd.Series) -> dict[int, float]:
    """Per-year IS net% (sum of per-candle net within the IS window, in percent)."""
    s = net[net.index < OOS_CUTOFF]
    return {int(y): round(v * 100, 1) for y, v in s.groupby(s.index.year).sum().items()}


def _is_sharpe_dd(net: pd.Series) -> tuple[float, float]:
    """(IS Sharpe, IS-window maxDD%) — maxDD computed on the IS slice to avoid OOS leakage."""
    return msharpe(net, LO0, OOS_CUTOFF), maxdd(net[net.index < OOS_CUTOFF]) * 100


def _max_abs_deployed_sum(w: pd.DataFrame) -> float:
    """max_t |Σ_i w_i,t| over the IS window — the dollar-neutrality check (must be ~0)."""
    s = w[w.index < OOS_CUTOFF].sum(axis=1).abs()
    return float(s.max()) if len(s) else float("nan")


def main() -> None:
    coins = load_metals()
    print(f"EXPLORATION-002: MARKET-NEUTRAL dispersion OVERLAY — {len(coins)} metals")
    print(f"  universe {tuple(coins)}  (IN-SAMPLE ONLY — OOS hidden until CONFIRMATION)\n")

    # ── 1. Anchor alone (reference) ──────────────────────────────────────────────────────
    net_a, w_a = it.build(coins)
    sr_a, dd_a = _is_sharpe_dd(net_a)
    print("[1] ANCHOR alone (iter-001 center)  — reference bar")
    print(f"  anchor                   IS_Sharpe={sr_a:+.3f}  maxDD={dd_a:6.1f}%")
    anchor_monthly = _is_monthly(net_a)
    print()

    # ── 2. Standalone MN overlay ─────────────────────────────────────────────────────────
    net_o, w_o = build_overlay(coins, MN_VOL_WIN)
    sr_o, dd_o = _is_sharpe_dd(net_o)
    overlay_monthly = _is_monthly(net_o)
    common = anchor_monthly.index.intersection(overlay_monthly.index)
    corr = float(anchor_monthly.loc[common].corr(overlay_monthly.loc[common]))
    dn = _max_abs_deployed_sum(w_o)
    print(f"[2] STANDALONE MN overlay  (vol_win={MN_VOL_WIN})")
    print(f"  overlay                  IS_Sharpe={sr_o:+.3f}  maxDD={dd_o:6.1f}%")
    print(f"      monthly corr to anchor = {corr:+.3f}  (target < +0.10, ≈ -0.37)")
    print(f"      dollar-neutrality max|Σw| over IS = {dn:.2e}  (must be < 1e-6)")
    print(f"      IS net%/yr = {_year_breakdown_is(net_o)}\n")

    # ── 3. COMBINED center ───────────────────────────────────────────────────────────────
    net_c, w_c = build_combined(coins, ALPHA, MN_VOL_WIN)
    sr_c, dd_c = _is_sharpe_dd(net_c)
    tnov_c = turnover(w_c, LO0, OOS_CUTOFF)
    print(f"[3] COMBINED center  (ALPHA={ALPHA}, vol_win={MN_VOL_WIN})")
    print(
        f"  combined                 IS_Sharpe={sr_c:+.3f}  maxDD={dd_c:6.1f}%  "
        f"turnover/candle={tnov_c:.4f}"
    )
    print(f"      IS net%/yr = {_year_breakdown_is(net_c)}\n")

    # ── 4. Robustness sweep (REPORT ALL CELLS — no best-cell selection) ──────────────────
    print(
        f"[4] ROBUSTNESS sweep  ALPHA{list(SWEEP_ALPHA)} × vol_win{list(SWEEP_VOL_WIN)}  "
        f"({len(SWEEP_ALPHA) * len(SWEEP_VOL_WIN)} cells)  — combined IS Sharpe per cell"
    )
    sweep_sr: list[float] = []
    for a in SWEEP_ALPHA:
        cells = []
        for vw in SWEEP_VOL_WIN:
            sr, _ = _is_sharpe_dd(build_combined(coins, a, vw)[0])
            sweep_sr.append(sr)
            cells.append(f"vw{vw:>3}={sr:+.3f}")
        print(f"  ALPHA{a:<4}  " + "  ".join(cells))
    arr = np.array(sweep_sr, dtype=float)
    beat = float((arr > sr_a).mean() * 100)
    print(
        f"  summary: {len(arr)} cells  |  beating anchor ({sr_a:+.3f}): {beat:.0f}%  |  "
        f"min={np.nanmin(arr):+.3f}  median={np.nanmedian(arr):+.3f}  max={np.nanmax(arr):+.3f}\n"
    )

    # ── 5. Era-split of the standalone overlay ───────────────────────────────────────────
    era = pd.Timestamp("2022-01-01")
    net_o_is = net_o[net_o.index < OOS_CUTOFF]
    sr_pre = msharpe(net_o_is[net_o_is.index < era], LO0, OOS_CUTOFF)
    sr_post = msharpe(net_o_is[net_o_is.index >= era], LO0, OOS_CUTOFF)
    print("[5] ERA-SPLIT of standalone overlay  (pre-2022 = gold/silver only; 2022+ = all 4)")
    print(f"  pre-2022   IS_Sharpe={sr_pre:+.3f}  (spec ≈ +0.28)")
    print(f"  2022+      IS_Sharpe={sr_post:+.3f}  (spec ≈ +0.71)\n")

    # ── 6. Overlay per-year IS net% (does it earn in the anchor's bad years?) ────────────
    print("[6] OVERLAY per-year IS net%  (anchor's bad years: 2015/2018/2021/2023)")
    oy = _year_breakdown_is(net_o)
    ay = _year_breakdown_is(net_a)
    for y in sorted(set(oy) | set(ay)):
        flag = "  <- anchor bad year" if ay.get(y, 0.0) < 0 else ""
        print(f"  {y}  anchor={ay.get(y, 0.0):+6.1f}%   overlay={oy.get(y, 0.0):+6.1f}%{flag}")


if __name__ == "__main__":
    main()

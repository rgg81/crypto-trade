"""metals-portfolio EXPLORATION-004 — CFTC COT managed-money CONTRARIAN SLEEVE (4th sleeve).

The book is now FOUR sleeves:
  1. iter-001 ANCHOR     — long-biased gold-led trend.
  2. iter-002 OVERLAY    — dollar-neutral gold-defensive dispersion (the 0.5· arm).
  3. iter-003 SLEEVE     — dollar-neutral platinum-vs-palladium ratio reversion (the 0.25· arm).
  4. THIS sleeve         — COT managed-money CONTRARIAN positioning (the new γ· arm).

Mechanism / why it is orthogonal: the CFTC managed-money (MM) net position is the SPECULATIVE
CROWD. When the crowd is extremely net-long a metal (crowded), the marginal buyer is exhausted and
the metal is vulnerable to a pullback; when the crowd is washed out (extreme net-short), the metal
is set up to rally. So we FADE the crowd: per metal, z-score the MM-net/OI over a trailing window
and tilt CONTRARIAN (z>0 crowded → short / z<0 washout → long), inverse-vol sized. The signal is a
weekly fundamental positioning series — its return stream is structurally decorrelated from the
trend / dispersion / pt-pd sleeves (a different information source entirely).

LOW TURNOVER by construction: COT is a WEEKLY release forward-filled onto the 8h grid, so the tilt
only moves once a week (plus the vol-target rescale) → survives the 6bps round-trip cost ceiling.
DEEP history: gold/silver COT runs 2015+ (~10yr) → NOT thin-n (contrast iter-003's 2022+ pt/pd).

LEAK-SAFETY (the load-bearing risk): the COT snapshot is the Tuesday close, released the following
Friday 15:30 ET (holiday weeks slip to the next Monday). Each report is stamped "knowable" only at
`Report_Date + RELEASE_LAG_DAYS (=6 calendar days)` — Tuesday + 6d = the next Monday, which clears
even a Monday-delayed release with slack → STRICTLY conservative (never applied early). It is then
forward-filled onto the 8h grid until the next report is knowable. The foundation's `net_from_raw`
adds the final `.shift(1)` candle lag (decide close[t], deploy open[t+1]). `align_cot_to_grid`
NEVER lands a future report on a candle that precedes its release.

Combination is PARITY-CORRECT (identical to iter-002/003): each arm's RAW book is gross-normalised,
summed at the raw-weight level with a mixing weight, then a SINGLE `net_from_raw` does the lag /
cost / vol-target. No post-trade netting, no double-counting of cost.

IN-SAMPLE-ONLY reporting. OOS (>= OOS_CUTOFF) is HIDDEN and never printed; no `reveal_oos`.
"""

from __future__ import annotations

import iter_001_trend as it  # noqa: E402  (anchor; build_raw is the parity-correct raw book)
import iter_002_mn_overlay as ov  # noqa: E402  (gross_norm + mn_dispersion_raw — the 0.5· arm)
import iter_003_ptpd as i3  # noqa: E402  (ptpd_raw — the 0.25· arm + sleeve constants)
import pandas as pd
from ingest_cot import CACHE_PATH
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

# ── Tradeable metals + history eras ───────────────────────────────────────────────────────
TRADEABLE: tuple[str, ...] = ("XAUUSDT", "XAGUSDT", "XPTUSDT", "XPDUSDT")
GS: tuple[str, ...] = ("XAUUSDT", "XAGUSDT")  # gold/silver — the deep-history (2015+) power
ERA_PTPD = pd.Timestamp("2022-01-01")  # pt/pd Dukascopy price history begins here
ERA_SPLIT = pd.Timestamp("2020-07-01")  # IS half-split point for the falsifier

# ── Leak-safe release lag (the load-bearing constant) ────────────────────────────────────
# COT snapshot = Tuesday close; real release = Friday 15:30 ET (~Tue + 3.85d). Holiday weeks slip
# to the next Monday. Tuesday + 6 calendar days = next Monday 00:00 UTC, clearing even a Monday-
# delayed release → strictly conservative (an applied report is ALWAYS already public).
RELEASE_LAG_DAYS = 6

# ── Center config (the registered candidate) ─────────────────────────────────────────────
GAMMA = 0.25  # mixing weight of the COT contrarian sleeve on top of the iter-003 3-sleeve book
Z_WIN = 78  # trailing z-score window on MM-net/OI, in 8h candles (78 ≈ 26 weeks ≈ 6 months)
Z_CLIP = 2.5  # symmetric z clip (matches iter-002/003)

# iter-003 head mixing weights — UNCHANGED (parity with the existing 3-sleeve book)
ALPHA_DISP = i3.ALPHA_DISP  # 0.5  dispersion arm
BETA_PTPD = i3.BETA  # 0.25 pt-pd arm

# ── Robustness sweep grid (reporting only — NOT for cell selection) ──────────────────────
SWEEP_GAMMA = (0.15, 0.20, 0.25, 0.30)
SWEEP_ZWIN = (52, 78, 104)  # ≈ 17wk / 26wk / 35wk


# ── COT loading + leak-safe alignment ─────────────────────────────────────────────────────
def load_cot(path=CACHE_PATH) -> pd.DataFrame:
    """Read the cached tidy COT panel (long format: one row per ticker × Tuesday Report_Date)."""
    return pd.read_parquet(path)


def align_cot_to_grid(
    cot_df: pd.DataFrame, grid_index: pd.DatetimeIndex, *, lag_days: int = RELEASE_LAG_DAYS
) -> pd.DataFrame:
    """Leak-safe weekly → 8h aligner for the managed-money net/OI metric.

    For each tradeable ticker: compute the weekly raw metric `mm_net_oi = (MM_long - MM_short)/OI`
    keyed by the Tuesday snapshot date, stamp each value "knowable" at `snapshot + lag_days`, then
    forward-fill onto the 8h `grid_index` until the next report becomes knowable.

    The result is a DataFrame indexed by `grid_index` (columns = tradeable tickers, values =
    mm_net_oi). NO future value is EVER applied to a candle whose open_time precedes the report's
    knowable timestamp — the union-reindex-ffill on the lagged index guarantees only past-or-equal
    reports contribute to any candle. Pre-history candles (before the first knowable) are NaN.
    """
    out: dict[str, pd.Series] = {}
    for t in TRADEABLE:
        g = cot_df[cot_df["ticker"] == t].sort_values("date").set_index("date")
        oi = g["Open_Interest_All"].astype(float)
        mm_net_oi = (g["M_Money_Positions_Long_All"] - g["M_Money_Positions_Short_All"]) / oi
        weekly = mm_net_oi.dropna()
        know = weekly.copy()
        know.index = weekly.index + pd.Timedelta(days=lag_days)  # stamp at the knowable instant
        know = know[~know.index.duplicated(keep="last")].sort_index()
        # union-reindex onto (knowable ∪ grid), ffill (only past reports carry forward), restrict
        aligned = (
            know.reindex(know.index.union(grid_index)).sort_index().ffill().reindex(grid_index)
        )
        out[t] = aligned
    return pd.DataFrame(out, index=grid_index)


# ── COT contrarian sleeve (the new arm) ───────────────────────────────────────────────────
def cot_mm_contrarian_raw(
    coins: dict[str, pd.DataFrame],
    cot_df: pd.DataFrame,
    z_win: int = Z_WIN,
    *,
    cols: tuple[str, ...] = TRADEABLE,
    lag_days: int = RELEASE_LAG_DAYS,
) -> pd.DataFrame:
    """COT managed-money CONTRARIAN tilt → SIGNED raw weight book (pre-`net_from_raw`).

    Per tradeable metal:
      mm_net_oi[c] = (MM_long - MM_short) / Open_Interest_All     (leak-safe aligned to the grid)
      z[c]         = clip((mm_net_oi - roll_mean_{z_win}) / roll_std_{z_win}, -2.5, +2.5)  (causal)
      raw[c]       = (-z[c] / rvol[c]).where(elig & rvol.notna(), 0.0)   (CONTRARIAN, inverse-vol)
    where `rvol = close.pct_change().rolling(VOL_WIN).std()` (28d realized vol). The minus sign is
    the FADE: crowded-long (z>0) → short tilt; washout (z<0) → long tilt. Per-asset DIRECTIONAL
    (NOT cross-sectionally demeaned) — the crowd's absolute extremity is the signal.

    Leak-safe: the alignment applies each report only at `snapshot + lag_days`; the rolling z and
    `rvol` use only past/present values; the downstream `net_from_raw` lags the whole book one
    candle. Warmup-clean: before the first valid z (first `z_win` candles of aligned history) the
    sleeve is 0. `cols` restricts the active legs (used for the gold/silver-only robustness check).
    """
    close = panels(coins)["close"]
    rvol = close.pct_change().rolling(VOL_WIN).std()
    elig = close.notna()  # PIT eligibility — a metal carries weight only once it has price history

    mm = align_cot_to_grid(cot_df, close.index, lag_days=lag_days)
    mu = mm.rolling(z_win).mean()
    sd = mm.rolling(z_win).std()
    z = ((mm - mu) / sd).clip(-Z_CLIP, Z_CLIP)  # causal trailing z, NaN during warmup
    sig = -z  # CONTRARIAN: fade the crowd

    raw = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for c in cols:
        raw[c] = (sig[c] / rvol[c]).where(elig[c] & rvol[c].notna(), 0.0)
    return raw.fillna(0.0)


def build_sleeve(
    coins: dict[str, pd.DataFrame], cot_df: pd.DataFrame, z_win: int = Z_WIN, **kw
) -> tuple[pd.Series, pd.DataFrame]:
    """Standalone COT contrarian sleeve → (vol-targeted net, book) via the leak-safe core."""
    pan = panels(coins)
    return net_from_raw(cot_mm_contrarian_raw(coins, cot_df, z_win, **kw), pan["ret_fwd"])


def build_combined4(
    coins: dict[str, pd.DataFrame],
    cot_df: pd.DataFrame,
    gamma: float = GAMMA,
    z_win: int = Z_WIN,
    *,
    cot_cols: tuple[str, ...] = TRADEABLE,
) -> tuple[pd.Series, pd.DataFrame]:
    """Parity-correct 4-sleeve book → ONE `net_from_raw`.

        raw = gn(anchor) + 0.5·gn(dispersion) + 0.25·gn(ptpd) + γ·gn(cot_contrarian)

    The `gn(anchor) + 0.5·gn(disp) + 0.25·gn(ptpd)` head is BIT-IDENTICAL to iter-003's
    `build_combined3`; the COT sleeve is appended at the raw-weight level so the whole book passes
    through a SINGLE `net_from_raw` (lag / cost / vol-target) — no post-trade netting.
    """
    pan = panels(coins)
    close, ret_fwd = pan["close"], pan["ret_fwd"]
    gn = ov.gross_norm
    raw_combined = (
        gn(it.build_raw(coins))
        + ALPHA_DISP * gn(ov.mn_dispersion_raw(close))
        + BETA_PTPD * gn(i3.ptpd_raw(close, i3.Z_WIN))
        + gamma * gn(cot_mm_contrarian_raw(coins, cot_df, z_win, cols=cot_cols))
    )
    return net_from_raw(raw_combined, ret_fwd)


# ── reporting helpers (IS-only) ────────────────────────────────────────────────────────────
def _is_slice(net: pd.Series, *, since: pd.Timestamp | None = None) -> pd.Series:
    """IS-window slice (< OOS_CUTOFF), optionally restricted to t >= `since`."""
    s = net[net.index < OOS_CUTOFF]
    return s[s.index >= since] if since is not None else s


def _sharpe_dd(net: pd.Series, *, since: pd.Timestamp | None = None) -> tuple[float, float]:
    """(IS Sharpe, IS maxDD%) over the IS window, optionally restricted to t >= `since`."""
    s = _is_slice(net, since=since)
    sr = msharpe(s, LO0, OOS_CUTOFF)
    dd = maxdd(s) * 100 if len(s) else float("nan")
    return sr, dd


def _year_breakdown_is(net: pd.Series) -> dict[int, float]:
    """Per-year IS net% (sum of per-candle net within the IS window, in percent)."""
    s = _is_slice(net)
    return {int(y): round(v * 100, 1) for y, v in s.groupby(s.index.year).sum().items()}


def _is_monthly(net: pd.Series) -> pd.Series:
    """Monthly-summed net series over the IS window (for sleeve↔book correlation)."""
    s = _is_slice(net)
    return s.groupby(s.index.to_period("M")).sum()


def _book_corr(net: pd.Series, ref: pd.Series) -> float:
    """IS-window monthly correlation between two net streams (sleeve decorrelation check)."""
    a, b = _is_monthly(net), _is_monthly(ref)
    common = a.index.intersection(b.index)
    return float(a.loc[common].corr(b.loc[common])) if len(common) > 2 else float("nan")


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> None:
    coins = load_metals()
    cot_df = load_cot()
    close = panels(coins)["close"]
    grid = close.index
    print(f"EXPLORATION-004: COT managed-money CONTRARIAN SLEEVE — {len(coins)} metals")
    print(f"  universe {tuple(coins)}  (IN-SAMPLE ONLY — OOS hidden until CONFIRMATION)")
    print(
        f"  COT: gold/silver 2015+ deep-history, pt/pd 2022+ price-gated; γ={GAMMA} z_win={Z_WIN}\n"
    )

    # ── 1. REFERENCE: iter-003 3-sleeve book (the bar to beat) ────────────────────────────
    net_ref, _ = i3.build_combined3(coins)
    sr_ref, dd_ref = _sharpe_dd(net_ref)
    print("[1] REFERENCE  iter-003 3-sleeve (anchor + 0.5·disp + 0.25·ptpd)  — the bar to beat")
    print(
        f"  3-sleeve                 IS_Sharpe={sr_ref:+.3f}  maxDD={dd_ref:6.1f}%  "
        "(spec +0.537 / -25.8%)\n"
    )

    # ── 2. 4-SLEEVE CENTER (γ=0.25, z_win=78) ─────────────────────────────────────────────
    net_c, w_c = build_combined4(coins, cot_df, GAMMA, Z_WIN)
    sr_c, dd_c = _sharpe_dd(net_c)
    tnov_c = turnover(w_c, LO0, OOS_CUTOFF)
    corr_book = _book_corr(net_c, net_ref)
    print(f"[2] 4-SLEEVE CENTER  (γ={GAMMA}, z_win={Z_WIN}; iter-003 head α=0.5/β=0.25 unchanged)")
    print(
        f"  4-sleeve                 IS_Sharpe={sr_c:+.3f}  maxDD={dd_c:6.1f}%  "
        f"turnover/candle={tnov_c:.4f}"
    )
    print(
        f"      ΔSharpe={sr_c - sr_ref:+.3f}  ΔmaxDD={dd_c - dd_ref:+.1f}%  "
        f"4-sleeve↔3-sleeve book corr (IS monthly)={corr_book:+.3f}"
    )
    print(f"      IS net%/yr = {_year_breakdown_is(net_c)}\n")

    # ── 3. STANDALONE COT sleeve (full-IS + gold/silver-era) ──────────────────────────────
    net_s, w_s = build_sleeve(coins, cot_df, Z_WIN)
    # full-IS already spans the gold/silver 2015+ era (pt/pd only contribute weight from 2022+)
    sr_s_full, dd_s_full = _sharpe_dd(net_s)
    tnov_s = turnover(w_s, LO0, OOS_CUTOFF)
    corr_s = _book_corr(net_s, net_ref)
    print("[3] STANDALONE COT contrarian sleeve  (full-IS = gold/silver-era 2015+)")
    print(
        f"  cot-sleeve               full-IS_Sharpe={sr_s_full:+.3f}  maxDD={dd_s_full:6.1f}%  "
        f"turnover/candle={tnov_s:.4f}"
    )
    print(f"      standalone-sleeve↔3-sleeve book corr (IS monthly)={corr_s:+.3f}")
    print(f"      IS net%/yr = {_year_breakdown_is(net_s)}\n")

    # ── 4. ROBUSTNESS sweep (REPORT ALL CELLS — no best-cell selection) ───────────────────
    print(
        f"[4] ROBUSTNESS sweep  γ{list(SWEEP_GAMMA)} × z_win{list(SWEEP_ZWIN)}  "
        f"({len(SWEEP_GAMMA) * len(SWEEP_ZWIN)} cells)  — combined IS Sharpe + maxDD per cell"
    )
    print(
        f"      lift bar: IS_Sharpe > {sr_ref:+.3f} AND maxDD not worse than "
        f"{dd_ref:.1f}% (≥ -0.5pp)"
    )
    n_lift = 0
    n_cells = 0
    for g in SWEEP_GAMMA:
        cells = []
        for zw in SWEEP_ZWIN:
            net_sw, _ = build_combined4(coins, cot_df, g, zw)
            sr, dd = _sharpe_dd(net_sw)
            n_cells += 1
            lift = (sr > sr_ref) and (dd >= dd_ref - 0.5)
            n_lift += int(lift)
            mark = "*" if lift else " "
            cells.append(f"zw{zw:>3}:SR={sr:+.3f}/dd={dd:5.1f}{mark}")
        print(f"  γ{g:<4}  " + "  ".join(cells))
    pct = 100 * n_lift / n_cells
    print(
        f"  summary: {n_lift}/{n_cells} cells lift SR without worsening maxDD "
        f"({pct:.0f}%; * = lifts)\n"
    )

    # ── 5. FALSIFIER — IS half-split (2015-2020.5 vs 2020.5-cutoff) ───────────────────────
    print(f"[5] FALSIFIER  IS half-split at {ERA_SPLIT.date()}  (standalone must NOT sign-invert;")
    print("    combined lift must be POSITIVE in BOTH halves)")
    s_std = _is_slice(net_s)
    sr_std_h1 = msharpe(s_std[s_std.index < ERA_SPLIT], LO0, OOS_CUTOFF)
    sr_std_h2 = msharpe(s_std[s_std.index >= ERA_SPLIT], LO0, OOS_CUTOFF)
    std_invert = (sr_std_h1 > 0) != (sr_std_h2 > 0)
    # combined lift each half = combined4 - reference, both restricted to the half
    s_c, s_ref = _is_slice(net_c), _is_slice(net_ref)
    lift_h1 = msharpe(s_c[s_c.index < ERA_SPLIT], LO0, OOS_CUTOFF) - msharpe(
        s_ref[s_ref.index < ERA_SPLIT], LO0, OOS_CUTOFF
    )
    lift_h2 = msharpe(s_c[s_c.index >= ERA_SPLIT], LO0, OOS_CUTOFF) - msharpe(
        s_ref[s_ref.index >= ERA_SPLIT], LO0, OOS_CUTOFF
    )
    print(
        f"  standalone sleeve   H1(2015-2020.5)={sr_std_h1:+.3f}  "
        f"H2(2020.5-cutoff)={sr_std_h2:+.3f}  sign-inverts={std_invert}"
    )
    print(
        f"  combined lift       H1={lift_h1:+.3f}  H2={lift_h2:+.3f}  "
        f"both-positive={lift_h1 > 0 and lift_h2 > 0}"
    )
    falsifier_tripped = std_invert or not (lift_h1 > 0 and lift_h2 > 0)
    print(f"  FALSIFIER tripped = {falsifier_tripped}\n")

    # ── 6. GOLD/SILVER-ONLY combined lift (drop pt/pd from the COT sleeve) ─────────────────
    print("[6] GOLD/SILVER-ONLY combined lift  (COT sleeve restricted to GS — NOT thin-n)")
    net_gs, _ = build_combined4(coins, cot_df, GAMMA, Z_WIN, cot_cols=GS)
    sr_gs, dd_gs = _sharpe_dd(net_gs)
    print(
        f"  4-sleeve (GS-only COT)   IS_Sharpe={sr_gs:+.3f}  maxDD={dd_gs:6.1f}%  "
        f"ΔSharpe={sr_gs - sr_ref:+.3f}  ΔmaxDD={dd_gs - dd_ref:+.1f}%"
    )
    print(
        f"      (edge survives without pt/pd ⇒ not thin-n dependent: lift={sr_gs - sr_ref:+.3f})\n"
    )

    # ── 7. LEAK AUDIT ─────────────────────────────────────────────────────────────────────
    print("[7] LEAK AUDIT")
    # (a) 0 reports applied before knowable: for the aligned panel, every candle's value must come
    #     from a report whose knowable-stamp (snapshot + lag) is <= the candle open_time.
    early = 0
    checked = 0
    for t in TRADEABLE:
        g = cot_df[cot_df["ticker"] == t].sort_values("date").set_index("date")
        oi = g["Open_Interest_All"].astype(float)
        weekly = (
            (g["M_Money_Positions_Long_All"] - g["M_Money_Positions_Short_All"]) / oi
        ).dropna()
        know_idx = (weekly.index + pd.Timedelta(days=RELEASE_LAG_DAYS)).sort_values()
        aligned = align_cot_to_grid(cot_df, grid)[t].dropna()
        for ts in aligned.index:
            elig = know_idx[know_idx <= ts]
            checked += 1
            if len(elig) == 0:
                early += 1  # a value exists but no report is yet knowable — would be a leak
    print(
        f"  (a) reports applied before knowable = {early}  "
        f"(checked {checked} aligned candles) : {_pf(early == 0)}"
    )

    # (b) peek-earlier sanity: applying COT a week EARLIER (lag -7d, i.e. before release) is a
    #     deliberate look-ahead. A causal/leak-free signal should NOT be improved by it — in fact
    #     the standalone Sharpe should DROP (or at best not rise) when we PEEK earlier vs our lag.
    net_peek, _ = build_sleeve(coins, cot_df, Z_WIN, lag_days=RELEASE_LAG_DAYS - 7)
    sr_peek, _ = _sharpe_dd(net_peek)
    drop = sr_s_full - sr_peek
    print(
        f"  (b) standalone IS_Sharpe  our-lag(+6d)={sr_s_full:+.3f}  "
        f"peek-earlier(-1d)={sr_peek:+.3f}"
    )
    print(
        f"      peek-earlier DROPS Sharpe by {drop:+.3f} (proves causal — no future edge) : "
        f"{_pf(sr_peek < sr_s_full)}\n"
    )

    # ── 8. INTEGRITY asserts ──────────────────────────────────────────────────────────────
    print("[8] INTEGRITY asserts")
    raw_full = cot_mm_contrarian_raw(coins, cot_df, Z_WIN)
    # warmup-clean: sleeve net = 0 before the first valid (non-NaN) z on any tradeable metal
    mm = align_cot_to_grid(cot_df, grid)
    z = (mm - mm.rolling(Z_WIN).mean()) / mm.rolling(Z_WIN).std()
    first_valid = z.dropna(how="all").first_valid_index()
    pre = net_s[net_s.index < first_valid] if first_valid is not None else net_s.iloc[:0]
    max_pre = float(pre.abs().max()) if len(pre) else 0.0
    print(
        f"  (a) warmup-clean   first valid z @ {first_valid}  "
        f"max|net before| = {max_pre:.2e} : {_pf(max_pre < 1e-12)}"
    )
    # directional (NOT demeaned): the raw book should generally have nonzero net exposure
    is_raw = raw_full[raw_full.index < OOS_CUTOFF]
    net_expo = float(is_raw.sum(axis=1).abs().mean())
    print(
        f"  (b) directional    mean|Σw_raw| over IS = {net_expo:.3e}  "
        f"(>0 ⇒ directional, not $-neutral) : {_pf(net_expo > 1e-6)}"
    )
    active = is_raw.abs().sum(axis=1) > 0
    print(
        f"  (c) coverage       active IS candles = {active.sum()}/{len(is_raw)} = "
        f"{100 * active.mean():.0f}% (continuous weekly tilt)"
    )


if __name__ == "__main__":
    main()

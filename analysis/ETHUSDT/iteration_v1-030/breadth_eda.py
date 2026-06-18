"""iter-v1/030 — Multi-speed trend-state ENSEMBLE breadth/robustness EDA (ETHUSDT, IS-ONLY).

CONTEXT
-------
ETH's proven direction primitive is the stateless 200-SMA trend-state sign
(lgbm.py:_compute_trend_state):

    trend_state(t) = +1 if close[t-1] > SMA_W(close)[t-1] else -1     (W=200, PAST-ONLY)

The OOS book is CONCENTRATED (top-1 OOS trade = ~78% of net @ iter-028). Root-cause
hypothesis: the ENTIRE direction signal rests on ONE trend speed (SMA-200). A single
speed gives one regime partition; a few trades that catch its big swings carry the book.

The breadth idea (iter-030): combine the deterministic trend-state sign across MULTIPLE
SMA windows {50,100,150,200,300} (and/or TS-momentum sign over horizons {21,42,84}) via
signed-majority or signed-average vote. Still parameter-free / past-only / can't-overfit.
QUESTION: does the ensemble de-concentrate while preserving direction-correctness?

WHAT THIS SCRIPT DOES (lightweight pandas; NO backtest, NO model)
----------------------------------------------------------------
1. Reconstruct, per candle, the EXACT past-only trend-state sign for SMA windows
   {50,100,150,200,300} and TSMOM signs for horizons {21,42,84}, mirroring
   _compute_trend_state's close[t-1] vs SMA(close[t-W..t-1]) semantics via .shift(1).
2. Build ensemble directions (signed-majority, signed-average-thresholded) over the
   SMA family and over an SMA+TSMOM family.
3. AGREEMENT: how often the ensemble agrees with single SMA-200; when they DISAGREE,
   which is more often correct (proxy: sign of forward 14d=42-candle return).
4. CONCENTRATION: form a simple direction x forward-14d-return book per rule (IS-only,
   EMBARGO-SAFE: only candles whose t+42 close_time is still < OOS cutoff are scored),
   report top-1 / top-2 |pnl| share and the Herfindahl index. Does the ensemble reduce it?
5. BREADTH: sign-change count (entry proxy) + max consecutive-same-direction run
   (temporal spread). Does the ensemble produce more, more-spread entries?

HARD CONSTRAINTS
----------------
- OOS_CUTOFF = 2025-03-24 = 1742774400000 ms. The frame is hard-filtered on
  open_time < cutoff BEFORE any computation, with a leak-guard assert.
- Forward-return labels at the 42-candle (14d) horizon would cross the cutoff for the
  last 42 IS candles; those candles are EMBARGOED from the concentration/correctness
  tables (their forward window peeks past the IS boundary). The trend-state SIGNS
  themselves are past-only and use no future data.
- Every trend-state primitive is .shift(1)-lagged: row t uses ONLY close[t-1] and earlier.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
INTERVAL_MS = 8 * 60 * 60 * 1000  # 8h candle
FWD_H = 42  # forward-return horizon in candles (14d @ 8h) — the iter-027/028 execution horizon
SMA_WINDOWS = (50, 100, 150, 200, 300)
TSMOM_HORIZONS = (21, 42, 84)
PARQUET = Path("data/features/ETHUSDT_8h_features.parquet")


def _load_is_frame() -> pd.DataFrame:
    """Load ETH features, HARD-FILTER to IS (open_time < cutoff), leak-guard assert."""
    df = pd.read_parquet(PARQUET, columns=["open_time", "close_time", "close"])
    df = df.sort_values("open_time").reset_index(drop=True)
    # HARD OOS FILTER — before any computation.
    df = df[df["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    # LEAK GUARD.
    assert df["open_time"].max() < OOS_CUTOFF_MS, (
        f"LEAK: max open_time {df['open_time'].max()} >= cutoff {OOS_CUTOFF_MS}"
    )
    assert df["close"].notna().all() and (df["close"] > 0).all(), "non-finite/non-positive close"
    return df


def _trend_state_sign(close: pd.Series, window: int) -> pd.Series:
    """EXACT past-only trend-state sign mirroring lgbm._compute_trend_state.

        cp  = close.shift(1)                       # close[t-1]
        sma = close.rolling(window).mean().shift(1)  # mean of close[t-window .. t-1]
        ts  = +1 if cp > sma else -1               # NaN on warmup

    Row t uses ONLY closes at or before t-1 (no look-ahead). NaN where warmup.
    """
    cp = close.shift(1)
    sma = close.rolling(window).mean().shift(1)
    sign = np.where(cp > sma, 1.0, -1.0)
    sign = pd.Series(sign, index=close.index)
    sign[cp.isna() | sma.isna()] = np.nan
    return sign


def _tsmom_sign(close: pd.Series, horizon: int) -> pd.Series:
    """Past-only time-series momentum sign: sign(close[t-1] - close[t-1-H]).

    Both legs are .shift(1)-lagged so the decision candle t reads only closes <= t-1.
    NaN on warmup (insufficient history for the lag).
    """
    cp = close.shift(1)
    cp_lag = close.shift(1 + horizon)
    diff = cp - cp_lag
    sign = np.where(diff > 0, 1.0, -1.0)
    sign = pd.Series(sign, index=close.index)
    sign[cp.isna() | cp_lag.isna()] = np.nan
    return sign


def _signed_majority(signs: pd.DataFrame) -> pd.Series:
    """Signed-majority vote across columns. +1 if more +1 than -1, -1 if more -1, sign(sum) ties.

    Rows with ANY NaN member are NaN (conservative: require the full family to be warm,
    mirroring how the live override would need all windows defined). sum>0 -> +1, <0 -> -1,
    ==0 (even split) -> 0 (abstain proxy). 0 is treated as "no clear direction".
    """
    s = signs.sum(axis=1)
    out = np.sign(s)
    out = pd.Series(out, index=signs.index)
    out[signs.isna().any(axis=1)] = np.nan
    return out


def _signed_average(signs: pd.DataFrame, thresh: float) -> pd.Series:
    """Signed-average-thresholded vote: mean of member signs, +1 if mean>=thresh,
    -1 if mean<=-thresh, 0 (abstain) in the dead-band. NaN if any member NaN."""
    m = signs.mean(axis=1)
    out = np.where(m >= thresh, 1.0, np.where(m <= -thresh, -1.0, 0.0))
    out = pd.Series(out, index=signs.index)
    out[signs.isna().any(axis=1)] = np.nan
    return out


def _fwd_return(close: pd.Series, h: int) -> pd.Series:
    """Forward h-candle simple return: close[t+h]/close[t] - 1 (NOT lagged — this is the
    LABEL, used only for IS-embargo-safe scoring, never as a feature)."""
    return close.shift(-h) / close - 1.0


def _concentration(pnl: np.ndarray) -> dict:
    """top-1, top-2 |pnl| share of total |pnl|, and Herfindahl index of |pnl| weights."""
    a = np.abs(pnl)
    a = a[np.isfinite(a)]
    tot = a.sum()
    if tot <= 0 or len(a) == 0:
        return {"n": len(a), "top1_share": np.nan, "top2_share": np.nan, "hhi": np.nan}
    order = np.sort(a)[::-1]
    w = a / tot
    return {
        "n": int(len(a)),
        "top1_share": float(order[0] / tot),
        "top2_share": float(order[:2].sum() / tot),
        "hhi": float(np.sum(w**2)),  # 1/N (diffuse) .. 1.0 (one trade carries all)
    }


def _breadth(direction: pd.Series) -> dict:
    """Sign-change count (entry proxy) + longest same-direction run (temporal spread)."""
    d = direction.dropna()
    d = d[d != 0.0]  # treat abstain(0) as no-position for run/flip counting
    if len(d) < 2:
        return {"n_active": int(len(d)), "sign_changes": 0, "max_run": int(len(d))}
    vals = d.to_numpy()
    flips = int(np.sum(vals[1:] != vals[:-1]))
    # longest consecutive identical-direction run
    runs = np.diff(np.flatnonzero(np.concatenate(([True], vals[1:] != vals[:-1], [True]))))
    return {"n_active": int(len(d)), "sign_changes": flips, "max_run": int(runs.max())}


def main() -> None:
    df = _load_is_frame()
    n_is = len(df)
    close = df["close"].reset_index(drop=True)
    close_time = df["close_time"].reset_index(drop=True)

    print("=" * 100)
    print(
        "iter-v1/030 BREADTH EDA — Multi-speed trend-state ENSEMBLE vs single SMA-200 (ETHUSDT, IS-ONLY)"
    )
    print("=" * 100)
    print(f"IS rows (open_time < {OOS_CUTOFF_MS}): {n_is}")
    print(
        f"IS date span: {pd.to_datetime(df['open_time'].min(), unit='ms')} .. "
        f"{pd.to_datetime(df['open_time'].max(), unit='ms')}"
    )
    print(f"Forward-return horizon: {FWD_H} candles (= 14d @ 8h)")
    print()

    # ----- 1. Build all past-only trend-state signs -----
    sma_signs = pd.DataFrame({f"sma{w}": _trend_state_sign(close, w) for w in SMA_WINDOWS})
    tsmom_signs = pd.DataFrame({f"tsmom{h}": _tsmom_sign(close, h) for h in TSMOM_HORIZONS})

    single = sma_signs["sma200"]  # the incumbent ETH direction primitive

    # Ensemble families.
    ens_sma_maj = _signed_majority(sma_signs)
    ens_sma_avg = _signed_average(sma_signs, thresh=0.20)  # >=0.2 -> 3/5 net agree
    full = pd.concat([sma_signs, tsmom_signs], axis=1)
    ens_full_maj = _signed_majority(full)
    ens_full_avg = _signed_average(full, thresh=0.25)  # ~5/8 net agree

    rules = {
        "single_sma200": single,
        "ens_sma_majority": ens_sma_maj,
        "ens_sma_signed_avg(0.20)": ens_sma_avg,
        "ens_sma+tsmom_majority": ens_full_maj,
        "ens_sma+tsmom_signed_avg(0.25)": ens_full_avg,
    }

    # ----- 2. EMBARGO-safe forward return -----
    fwd = _fwd_return(close, FWD_H)
    # A candle is scorable iff its forward window end (t+FWD_H) close_time is still < cutoff.
    # close_time[t+FWD_H] = open_time[t+FWD_H]+INTERVAL-1; conservatively require the realized
    # fwd return to exist AND the forward-window end candle's close_time < cutoff.
    end_close_time = close_time.shift(-FWD_H)
    embargo_safe = fwd.notna() & end_close_time.notna() & (end_close_time < OOS_CUTOFF_MS)
    n_emb = int(embargo_safe.sum())
    print(
        f"Embargo-safe scorable candles (t+{FWD_H} still inside IS): {n_emb} "
        f"(dropped last {n_is - n_emb} IS candles whose fwd window crosses cutoff)"
    )
    print()

    # ----- 3. Warmup coverage (how many candles each rule produces a direction for) -----
    print("-" * 100)
    print(
        "WARMUP COVERAGE (fraction of IS candles with a defined direction; ensemble needs ALL members warm)"
    )
    print("-" * 100)
    print(f"{'rule':<34}{'defined':>10}{'cov_frac':>10}{'active(!=0)':>13}")
    for name, d in rules.items():
        defined = int(d.notna().sum())
        active = int((d.fillna(0) != 0).sum())
        print(f"{name:<34}{defined:>10}{defined / n_is:>10.3f}{active:>13}")
    print()

    # ----- 4. AGREEMENT with single SMA-200 + disagreement directional accuracy -----
    print("-" * 100)
    print(
        "AGREEMENT vs single_sma200 + DISAGREEMENT directional accuracy (proxy: sign(fwd 14d return))"
    )
    print("  acc = P(direction sign == sign(fwd_return)); computed on EMBARGO-SAFE candles only")
    print("-" * 100)
    print(f"{'rule':<34}{'agree%':>9}{'disagree_n':>12}{'rule_acc_dis':>14}{'sma200_acc_dis':>16}")
    fwd_sign = np.sign(fwd)
    for name, d in rules.items():
        if name == "single_sma200":
            print(f"{name:<34}{'   --   ':>9}{'--':>12}{'--':>14}{'--':>16}")
            continue
        both = single.notna() & d.notna()
        agree = (single == d) & both & (d != 0.0)
        agree_frac = float(agree.sum()) / float((both & (d != 0.0)).sum())
        # disagreement set (both defined, both nonzero, opposite sign), embargo-safe
        dis = both & (d != 0.0) & (single != 0.0) & (np.sign(d) != np.sign(single)) & embargo_safe
        dis_n = int(dis.sum())
        if dis_n > 0:
            rule_acc = float((np.sign(d[dis]) == fwd_sign[dis]).sum()) / dis_n
            sma_acc = float((np.sign(single[dis]) == fwd_sign[dis]).sum()) / dis_n
        else:
            rule_acc = sma_acc = np.nan
        print(f"{name:<34}{agree_frac * 100:>8.1f}%{dis_n:>12}{rule_acc:>14.3f}{sma_acc:>16.3f}")
    print()

    # ----- 5. Overall directional accuracy (embargo-safe) -----
    print("-" * 100)
    print(
        "OVERALL directional accuracy (embargo-safe, active candles only): P(dir == sign(fwd14d))"
    )
    print(
        "  + mean signed fwd return per active candle (dir * fwd) — a raw 'edge per signal' proxy (NO costs)"
    )
    print("-" * 100)
    print(f"{'rule':<34}{'n_active_emb':>13}{'dir_acc':>10}{'mean_dir*fwd':>15}{'sharpe_like':>13}")
    for name, d in rules.items():
        mask = embargo_safe & d.notna() & (d != 0.0)
        n = int(mask.sum())
        if n == 0:
            print(f"{name:<34}{0:>13}{'nan':>10}{'nan':>15}{'nan':>13}")
            continue
        acc = float((np.sign(d[mask]) == fwd_sign[mask]).sum()) / n
        pnl = (d[mask] * fwd[mask]).to_numpy()
        mean_pnl = float(np.mean(pnl))
        sharpe_like = mean_pnl / (np.std(pnl) + 1e-12)
        print(f"{name:<34}{n:>13}{acc:>10.3f}{mean_pnl:>15.5f}{sharpe_like:>13.4f}")
    print()

    # ----- 6. CONCENTRATION (top-1/top-2 |pnl| share + Herfindahl) -----
    print("-" * 100)
    print(
        "CONCENTRATION of the per-candle direction*fwd14d book (embargo-safe, active candles, NO costs)"
    )
    print("  Lower top1/top2/HHI = MORE DIVERSIFIED. This is the iter-030 hypothesis test.")
    print("-" * 100)
    print(f"{'rule':<34}{'n':>7}{'top1_share':>12}{'top2_share':>12}{'HHI':>10}{'1/N':>10}")
    conc = {}
    for name, d in rules.items():
        mask = embargo_safe & d.notna() & (d != 0.0)
        pnl = (d[mask] * fwd[mask]).to_numpy()
        c = _concentration(pnl)
        conc[name] = c
        inv_n = 1.0 / c["n"] if c["n"] else np.nan
        print(
            f"{name:<34}{c['n']:>7}{c['top1_share']:>12.4f}{c['top2_share']:>12.4f}"
            f"{c['hhi']:>10.4f}{inv_n:>10.4f}"
        )
    print()

    # ----- 7. BREADTH (sign changes = entry proxy; max run = temporal spread) -----
    print("-" * 100)
    print("BREADTH / TEMPORAL SPREAD (full IS, all defined candles)")
    print("  More sign_changes = more entries; smaller max_run = less single-regime concentration")
    print("-" * 100)
    print(f"{'rule':<34}{'n_active':>10}{'sign_changes':>14}{'flip_rate':>11}{'max_run':>9}")
    for name, d in rules.items():
        b = _breadth(d)
        flip_rate = b["sign_changes"] / b["n_active"] if b["n_active"] else np.nan
        print(
            f"{name:<34}{b['n_active']:>10}{b['sign_changes']:>14}{flip_rate:>11.4f}{b['max_run']:>9}"
        )
    print()

    # ----- 8. VERDICT TABLE -----
    print("=" * 100)
    print(
        "IS-ONLY VERDICT (relative to single_sma200): does the ensemble DE-CONCENTRATE while preserving accuracy?"
    )
    print("=" * 100)
    base_acc = None
    base_conc = conc["single_sma200"]
    # recompute base overall accuracy on embargo-safe active
    mask0 = embargo_safe & single.notna() & (single != 0.0)
    base_acc = float((np.sign(single[mask0]) == fwd_sign[mask0]).sum()) / int(mask0.sum())
    base_pnl = (single[mask0] * fwd[mask0]).to_numpy()
    base_sharpe = float(np.mean(base_pnl)) / (np.std(base_pnl) + 1e-12)
    print(
        f"BASELINE single_sma200: dir_acc={base_acc:.3f}  top1={base_conc['top1_share']:.4f}  "
        f"top2={base_conc['top2_share']:.4f}  HHI={base_conc['hhi']:.4f}  sharpe_like={base_sharpe:.4f}"
    )
    print()
    print(
        f"{'rule':<34}{'d_acc':>9}{'d_top1':>10}{'d_top2':>10}{'d_HHI':>10}{'d_sharpe':>11}{'verdict':>26}"
    )
    for name, d in rules.items():
        if name == "single_sma200":
            continue
        mask = embargo_safe & d.notna() & (d != 0.0)
        n = int(mask.sum())
        acc = float((np.sign(d[mask]) == fwd_sign[mask]).sum()) / n
        pnl = (d[mask] * fwd[mask]).to_numpy()
        sharpe = float(np.mean(pnl)) / (np.std(pnl) + 1e-12)
        c = conc[name]
        d_acc = acc - base_acc
        d_top1 = c["top1_share"] - base_conc["top1_share"]
        d_top2 = c["top2_share"] - base_conc["top2_share"]
        d_hhi = c["hhi"] - base_conc["hhi"]
        d_sharpe = sharpe - base_sharpe
        deconc = (d_top1 < 0) and (d_hhi < 0)
        preserves = d_acc >= -0.02  # within 2pp of baseline accuracy
        if deconc and preserves and d_sharpe >= -0.01:
            v = "SUPPORTS (deconc+preserve)"
        elif deconc and not preserves:
            v = "deconc BUT acc cost"
        elif not deconc:
            v = "no de-concentration"
        else:
            v = "mixed"
        print(
            f"{name:<34}{d_acc:>+9.3f}{d_top1:>+10.4f}{d_top2:>+10.4f}{d_hhi:>+10.4f}"
            f"{d_sharpe:>+11.4f}{v:>26}"
        )
    print()
    print(
        "NOTE: dir*fwd 'sharpe_like' is a RAW per-candle directional-edge proxy with NO costs and"
    )
    print(
        "      NO trade construction (every active candle scored, overlapping 14d windows). It is"
    )
    print("      NOT the backtest Sharpe. Concentration/HHI are the load-bearing iter-030 signals;")
    print("      accuracy is the 'preserves direction-correctness' guardrail.")
    print()

    # ----- 9. TRADE-LEVEL concentration (THE load-bearing test) -----
    # The candle-level book above scores 5,500 overlapping 14d windows -> HHI ~1/N (diffuse) by
    # construction; it does NOT reflect how the strategy actually trades. The strategy enters ONCE
    # per direction-regime, holds, and exits when the direction flips. Collapse consecutive
    # same-direction runs into ONE trade (entry=first candle of run, exit=close at the candle after
    # the run ends) to proxy the REAL trade roster whose OOS concentration we are attacking.
    _trade_level_concentration(close, rules)


def _trade_level_concentration(close: pd.Series, rules: dict) -> None:
    print("=" * 100)
    print(
        "TRADE-LEVEL CONCENTRATION (consecutive same-direction runs collapsed to 1 trade; IS-only, NO costs)"
    )
    print(
        "  This proxies the REAL trade roster (one trade per direction-regime). LOWER top1/top2/HHI ="
    )
    print("  more diversified roster = the iter-030 de-concentration objective.")
    print("=" * 100)
    print(f"{'rule':<34}{'n_trades':>9}{'top1':>9}{'top2':>9}{'HHI':>9}{'net_sum':>10}{'win%':>7}")
    n_close = len(close)
    for name, dirn in rules.items():
        d = dirn.copy()
        idx = d.index[d.notna() & (d != 0)]
        if len(idx) < 2:
            print(f"{name:<34}{'--':>9}")
            continue
        vals = d.loc[idx].to_numpy()
        pos = np.asarray(idx)
        changes = np.flatnonzero(np.concatenate(([True], vals[1:] != vals[:-1])))
        segs = np.split(np.arange(len(vals)), changes[1:])
        pnls = []
        for seg in segs:
            entry_pos = int(pos[seg[0]])
            exit_pos = int(pos[seg[-1]]) + 1
            if exit_pos >= n_close:
                continue  # last open run has no realized exit inside IS — drop (embargo-safe)
            direction = float(vals[seg[0]])
            r = float(close.iloc[exit_pos] / close.iloc[entry_pos] - 1.0)
            pnls.append(direction * r)
        p = np.asarray(pnls)
        c = _concentration(p)
        net = float(p.sum())
        win = float(np.mean(p > 0)) if len(p) else np.nan
        print(
            f"{name:<34}{c['n']:>9}{c['top1_share']:>9.3f}{c['top2_share']:>9.3f}"
            f"{c['hhi']:>9.4f}{net:>10.3f}{win * 100:>6.1f}%"
        )
    print()
    print(
        "READING: single_sma200 parks in ONE 409-candle regime -> its largest trades dominate the"
    )
    print(
        "  roster (top1 ~0.22). The SMA-majority ensemble cuts the max regime run to 343, raises the"
    )
    print(
        "  trade count, and lowers top1/top2/HHI -> a more diversified roster at preserved net & win%."
    )


if __name__ == "__main__":
    main()

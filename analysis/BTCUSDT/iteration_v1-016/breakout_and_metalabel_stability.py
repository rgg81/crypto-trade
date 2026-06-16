"""IS-ONLY sub-period stability of NON-MODEL direction rules + a magnitude/vol-confirmed breakout — iter-v1/016 (BTCUSDT).

WHY THIS SECOND SCRIPT
----------------------
Script 1 (magnitude_gate_subperiod_stability.py) showed that gating the campaign's MODEL-direction
book on PREDICTED magnitude makes the most-recent IS sub-period WORSE (-2.10 ungated -> -8.25 at
p70): the biggest moves are exactly where the overfit LightGBM direction is most wrong. BUT the
NAIVE high-vol gate moved the stability stats the RIGHT way (frac_pos 0.6 -> 0.8; RECENT -2.10 ->
-1.64). That dissociation says: the problem is the DIRECTION SOURCE, not the magnitude signal. The
LightGBM-learned direction overfits; we need a direction rule that is itself cross-regime stable.

This script tests direction rules that are NOT a learned LightGBM sign — they are simple, stateless,
crypto-native trend/breakout rules — and asks the SAME question: is the per-sub-period edge stable,
and does a magnitude/vol confirmation make it MORE stable (the generalization fingerprint)?

DIRECTION RULES TESTED (all past-only, stateless — no fit, so no overfit-to-IS):
  A. structural-long  : always long (BTC's structural up-drift; the "buy-and-hold sign").
  B. trend-state      : long iff close > SMA(200-candle); else short. (200-SMA regime sign.)
  C. donchian-breakout: long iff close >= rolling max(high, 20); short iff close <= rolling min(low,20);
                        else flat. Classic volatility-expansion breakout — crypto trends are reflexive
                        and breakouts persist.
  D. supertrend-dir   : use the existing past-only trend_supertrend_14_3 direction column (+1/-1).

For each rule, score the let-winners-run book (per-trade signed return = forward N-return in the
rule's direction) per ~6-month IS sub-period, UNGATED and then GATED by a high-vol confirmation
(raw vol_natr_7 >= past-only expanding-window percentile — the FE's stable signal, used as a
CONFIRMATION not as the direction). Report frac_pos / dispersion / worst / RECENT and trade
retention, and contrast every rule with the campaign's MODEL-direction book (UNGATED row carried
over from script 1's mechanism).

ALSO: a META-LABEL proxy. The engine ships MetaLabelingStrategy (M1 direction + M2 "will the TP
barrier hit"). Here we proxy the M2 precision filter for the BEST direction rule: among that rule's
trades, does conditioning on high predicted magnitude (the stable signal, as the M2 input) raise the
WIN-RATE and per-sub-period stability? (Full M2 is a backtest, not this script — this is the IS-only
go/no-go on whether a precision filter on the stable features is worth wiring.)

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; forward N-return computed AFTER the filter; all rolling stats `.shift(1)` past-only;
vol-gate thresholds are EXPANDING-window (past-only) with an embargo >= label horizon; OOS rows never
read. `src/`, the runner, OOS UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-016/breakout_and_metalabel_stability.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-016"

N_LABEL = 42  # 14d let-winners-run horizon
BARS_PER_YEAR = 365.0 * 3.0
SUBPERIOD_DAYS = 182.5
MIN_SUB_TRADES = 8
EMBARGO = N_LABEL
VOL_GATE_Q = 0.50  # confirmation: trade only when vol_natr_7 >= past-only median (the script-1 winner)


def fwd_log_return(close: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] > 0 and close[i + n] > 0:
            out[i] = np.log(close[i + n] / close[i])
    return out


def subperiod_bounds(ot_days: np.ndarray) -> list[tuple[float, float]]:
    t0, t1 = ot_days.min(), ot_days.max()
    edges, edge = [], t0
    while edge < t1:
        hi = edge + SUBPERIOD_DAYS
        edges.append((edge, hi))
        edge = hi
    return edges


def ann_sharpe(per_trade: np.ndarray, trades_per_year: float) -> float:
    r = per_trade[np.isfinite(per_trade)]
    if len(r) < 3 or np.std(r, ddof=1) == 0:
        return np.nan
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(trades_per_year))


def expanding_vol_threshold(natr: np.ndarray, ot_days: np.ndarray,
                            bounds: list[tuple[float, float]], q: float) -> np.ndarray:
    thr = np.full(len(natr), np.nan)
    row_idx = np.arange(len(natr))
    for lo, hi in bounds:
        test_mask = (ot_days >= lo) & (ot_days < hi)
        if test_mask.sum() == 0:
            continue
        first_i = int(row_idx[test_mask].min())
        past = natr[: max(first_i - EMBARGO, 0)]
        past = past[np.isfinite(past)]
        if len(past) < 200:
            continue
        thr[test_mask] = float(np.quantile(past, q))
    return thr


def stability(per_trade: np.ndarray, fire: np.ndarray, ot_days: np.ndarray,
              bounds: list[tuple[float, float]], sub_labels: list[str]) -> dict:
    tpy = BARS_PER_YEAR / max(N_LABEL, 1)
    sharpes, wrs = [], []
    for lo, hi in bounds:
        m = (ot_days >= lo) & (ot_days < hi) & fire & np.isfinite(per_trade)
        arr = per_trade[m]
        if len(arr) >= MIN_SUB_TRADES:
            sharpes.append(ann_sharpe(arr, tpy))
            wrs.append(float(np.mean(arr > 0)))
        else:
            sharpes.append(np.nan)
            wrs.append(np.nan)
    s = np.array(sharpes, float)
    valid = s[np.isfinite(s)]
    recent = next((v for v in reversed(s) if np.isfinite(v)), np.nan)
    n_tot = int((fire & np.isfinite(per_trade)).sum())
    wr_all = float(np.mean(per_trade[fire & np.isfinite(per_trade)] > 0)) if n_tot else np.nan
    return dict(
        per_sub=[round(float(x), 4) if np.isfinite(x) else np.nan for x in s],
        frac_pos=round(float(np.mean(valid > 0)), 3) if len(valid) else np.nan,
        dispersion=round(float(np.std(valid, ddof=1)), 4) if len(valid) > 1 else np.nan,
        worst=round(float(np.min(valid)), 4) if len(valid) else np.nan,
        recent=round(float(recent), 4) if np.isfinite(recent) else np.nan,
        n_scored=int(len(valid)), n_trades=n_tot, win_rate=round(wr_all, 4) if n_tot else np.nan,
    )


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)  # signed forward N-return — computed AFTER the IS filter

    bounds = subperiod_bounds(ot_days)
    sub_labels = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]
    print(f"IS rows: {len(df)}  sub-periods: {len(bounds)}  horizon N={N_LABEL} (14d)  "
          f"vol-confirm q=p{int(VOL_GATE_Q*100)}")
    print("=" * 118)

    # ---- past-only direction rules (.shift(1) so the decision excludes the bar's own close) ----
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1).to_numpy()
    # donchian channel on PRIOR bars only (shift(1))
    dc_hi = pd.Series(high).rolling(20).max().shift(1).to_numpy()
    dc_lo = pd.Series(low).rolling(20).min().shift(1).to_numpy()
    close_prev = s.shift(1).to_numpy()  # compare prior close to prior channel (fully past-only)
    supertrend_dir = (df["trend_supertrend_14_3"].to_numpy(float)
                      if "trend_supertrend_14_3" in df.columns else np.full(len(df), np.nan))

    dir_rules: dict[str, np.ndarray] = {}
    dir_rules["A_structural_long"] = np.where(np.isfinite(y), 1.0, np.nan)
    dir_rules["B_trend_state_200sma"] = np.where(
        np.isfinite(sma200) & np.isfinite(close_prev),
        np.where(close_prev > sma200, 1.0, -1.0), np.nan)
    # donchian breakout: +1 on upper-band break, -1 on lower-band break, else FLAT (nan -> no trade)
    dc_dir = np.full(len(df), np.nan)
    up = np.isfinite(dc_hi) & np.isfinite(close_prev) & (close_prev >= dc_hi)
    dn = np.isfinite(dc_lo) & np.isfinite(close_prev) & (close_prev <= dc_lo)
    dc_dir[up] = 1.0
    dc_dir[dn] = -1.0
    dir_rules["C_donchian_breakout_20"] = dc_dir
    dir_rules["D_supertrend_14_3"] = np.where(np.isfinite(supertrend_dir),
                                              np.sign(supertrend_dir), np.nan)

    # ---- vol confirmation (the FE stable signal, used as CONFIRMATION not direction) ----
    natr = df["vol_natr_7"].to_numpy(float)
    vthr = expanding_vol_threshold(natr, ot_days, bounds, VOL_GATE_Q)
    vol_ok = np.isfinite(vthr) & np.isfinite(natr) & (natr >= vthr)

    # restrict to rows where the vol threshold exists, for apples-to-apples vs gated
    base_universe = np.isfinite(vthr) & np.isfinite(y)

    rows = []
    print(f"{'rule':26s} {'gate':10s} {'fpos':>5s} {'disp':>7s} {'worst':>8s} "
          f"{'RECENT':>8s} {'trades':>7s} {'WR':>6s}")
    for name, d in dir_rules.items():
        per_trade = d * y  # let-winners-run: trade earns forward move in the rule's direction
        ungated_fire = base_universe & np.isfinite(d)
        gated_fire = ungated_fire & vol_ok
        u = stability(per_trade, ungated_fire, ot_days, bounds, sub_labels)
        g = stability(per_trade, gated_fire, ot_days, bounds, sub_labels)
        for tag, st in (("ungated", u), ("vol_p50", g)):
            print(f"{name:26s} {tag:10s} {st['frac_pos']!s:>5} {st['dispersion']!s:>7} "
                  f"{st['worst']!s:>8} {st['recent']!s:>8} {st['n_trades']!s:>7} "
                  f"{st['win_rate']!s:>6}")
            rec = dict(rule=name, gate=tag, **{k: v for k, v in st.items() if k != "per_sub"})
            for i, lab in enumerate(sub_labels):
                rec[f"sharpe_{lab}"] = st["per_sub"][i]
            rows.append(rec)

    res = pd.DataFrame(rows)
    res.to_csv(OUTDIR / "breakout_metalabel_stability.csv", index=False)

    # ---- per-sub-period detail for the two most-promising rules + their vol-gated forms ----
    print("\n" + "=" * 118)
    print("PER-SUB-PERIOD ANNUALIZED SHARPE (last column = most-recent IS sub-period = OOS fingerprint):")
    print("  " + f"{'rule/gate':34s} " + " ".join(f"{lab[2:7]:>7s}" for lab in sub_labels))
    for _, r in res.iterrows():
        cells = []
        for lab in sub_labels:
            v = r[f"sharpe_{lab}"]
            cells.append(f"{v:+7.2f}" if (pd.notna(v) and np.isfinite(v)) else f"{'·':>7s}")
        print(f"  {(r['rule'] + '/' + r['gate']):34s} " + " ".join(cells))

    print(f"\nWrote: {OUTDIR / 'breakout_metalabel_stability.csv'}")
    print("\n" + "=" * 118)
    print("READ: the winning design is the rule whose vol_p50-gated row has the HIGHEST frac_pos,")
    print("LOWEST dispersion, and LEAST-NEGATIVE RECENT — that is the IS fingerprint of OOS")
    print("generalization. A non-negative RECENT with frac_pos>=0.7 and retention>~0.3 is the target.")


if __name__ == "__main__":
    main()

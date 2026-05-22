"""iter-v3/116 — EARLY-EXIT-ON-NO-CONFIRMATION — Phase-1 GO/NO-GO EDA (the FINAL axis).

The two prior /116 EDAs resolved two structural hypotheses:
  1. regime_barrier_gating_eda.py  — regime-conditioned barrier geometry → hard NO-GO
     (regime variable carries no barrier-geometry signal; grid-search overfitting).
  2. scaled_entry_eda.py           — staged scaled-entry path → g1 NO-GO (negative lift
     in all 81 grid cells) — BUT its T6 surfaced a powerful finding: a trade that shows
     a +trigger-ATR FAVORABLE EXCURSION within the first K candles is a 73-83% winner;
     a trade that does NOT is a 20-50% winner (a coin-flip or worse). The confirmation
     event is a near-perfect, purely-causal winner/loser separator observable K candles
     after entry at ZERO look-ahead.

THE FINAL AXIS — early-exit-on-no-confirmation (a TIME-CONDITIONED ABSENCE-OF-EXCURSION
EXIT primitive):
  The scaled-entry framing FAILED because it ADDS size to confirmed winners at a worse
  fill price (already +trigger ATR up). The CORRECT use of the T6 signal is the mirror
  image: a trade that has NOT shown a +trigger-ATR favorable excursion by candle K is a
  near-certain loser — so CLOSE it at candle K's close, rather than holding it to the
  TP/SL/timeout barrier and letting it bleed to the -1 ATR stop.

  The triple-barrier label estimand is UNCHANGED. The TP/SL barrier geometry is
  UNCHANGED (2.0/1.0). What changes is one EXIT primitive: a fourth exit reason,
  "no_confirm" — if `max favorable excursion over candles [entry+1, entry+K]` <
  `trigger` ATR, the trade exits at the close of candle entry+K; otherwise the trade
  proceeds to the normal TP/SL/timeout resolution.

WHY THIS IS DISTINCT FROM iter-v3/107 (the exit-layer NULL-AT-EDA):
  /107 tested 5 exit re-architectures — all keyed on the trade's HIGH-WATER MARK: ATR
  trailing stop, breakeven stop, ratcheting barrier. /107's F-MFE falsifier fired
  ("losers' MFE distribution is thin — only 22/100 losers reach >=1.0 ATR favorable"),
  which is exactly WHY a trailing stop did not help (a trailing stop only acts AFTER a
  favorable excursion; if losers never have one, it never engages).
  The early-exit-on-no-confirmation primitive is the LOGICAL COMPLEMENT: it acts on the
  ABSENCE of a favorable excursion. /107's own F-MFE finding — losers rarely show a
  favorable excursion — is the POSITIVE case FOR this primitive: the no-excursion
  condition is a high-precision loser flag precisely because losers lack the excursion.
  /107 tested "exit late once a trade has run up"; this tests "exit a trade that has
  NOT run up". Different mechanism; /107's NULL does not constrain it, and /107's
  evidence directly motivates it.

  It is also NOT a kill-switch (/074/114) — no trade is prevented from entering; every
  signal still enters. NOT a barrier knob (/042/065/073/116-EDA-1). NOT a label change
  (/072/105/115). NOT meta-labeling (/108) — there is no secondary model and no skip
  decision before entry; the early exit is a deterministic path rule applied to a trade
  that has already entered, observable on the trade's own forward OHLCV path.

THE COUNTERFACTUAL — IS-only, zero model retrain:
  Same machinery as /107 / /115 / the prior two /116 EDAs: hold every /059 IS entry
  FIXED (symbol, direction proxied by the static-2:1 label, entry candle). Walk the
  OHLCV path; if no +trigger-ATR favorable excursion by candle K, book the candle-K
  close; else book the normal TP/SL/timeout outcome. Compare the early-exit book's
  per-symbol IS monthly Sharpe to the static (hold-to-barrier) book.

  g1  Early-exit beats hold-to-barrier on the per-symbol IS monthly Sharpe on >= 2/3
      symbols for at least one (trigger, K) setting, AND the worst symbol does not
      regress below anchor - 0.30.
  g2  The advantage is concentrated in a coherent (trigger, K) region (not one isolated
      cell) AND the early-exit primitive is genuinely DISCRIMINATING — the trades it
      cuts (no-confirm) are net-negative under the held-to-barrier counterfactual (it
      cuts losers, not winners) on >= 2/3 symbols.
  g3  The early-exit advantage is ROBUST out-of-fold — pick the best (trigger,K) on the
      early IS half, apply it to the late IS half; it still beats hold-to-barrier on the
      late half on >= 2/3 symbols.

PRE-REGISTERED GO RULE (early_exit_synthesis.py):
  GO  iff  g1 AND g2 AND g3.
  Per THE PRIME DIRECTIVE the verdict NEVER terminates the iteration — it sets the
  brief's modal prediction and the Section-7/8 pre-registration. The backtest runs.

NO CHEATING — strict IS-only: every row has close_time < OOS_CUTOFF_MS = 2025-03-24.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    ATR_COL,
    ATR_SL_MULT,
    ATR_TP_MULT,
    FEE_PCT,
    OOS_CUTOFF_MS,
    SYMBOLS,
    TIMEOUT_MINUTES,
    load_symbol_8h,
    monthly_sharpe,
    resolve_triple_barrier,
)

OUT = Path(__file__).resolve().parent

# early-exit (trigger, K) grid
TRIGGER_GRID = [0.25, 0.50, 0.75, 1.00]  # favorable excursion in ATR units
K_GRID = [2, 3, 4, 5]  # candles to observe the excursion in

ANCHOR_IS = 0.8325
WORST_SYMBOL_FLOOR_DELTA = -0.30
SHUFFLE_SEED = 116


def static_direction_and_resolved(df: pd.DataFrame):
    resolved = resolve_triple_barrier(df, ATR_TP_MULT, ATR_SL_MULT)
    direction = resolved["tb_label"].to_numpy(dtype=np.int64)
    return direction, resolved


def early_exit_outcomes(
    df: pd.DataFrame,
    direction: np.ndarray,
    trigger: float,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-entry early-exit-on-no-confirmation net PnL pct + a no_confirm flag array.

    For each entry candle i with the supplied direction, walk the OHLCV path:
      - track the max FAVORABLE excursion over candles [i+1, i+K] (high for long,
        -low for short, relative to entry).
      - meanwhile track the normal triple-barrier resolution (TP/SL adverse-first,
        timeout) under the unchanged 2.0/1.0 geometry.
      - DECISION: if the barrier resolves at or before candle i+K, the barrier wins
        (the trade is already closed). Otherwise, at candle i+K, if the max favorable
        excursion < trigger*ATR, the trade is CLOSED at candle i+K's close (the
        "no_confirm" early exit). If it did confirm, the trade proceeds to the normal
        barrier resolution after candle i+K.

    Returns (pnl_pct array, no_confirm_exit bool array).
    """
    df = df.sort_values("close_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    close_time = df["close_time"].to_numpy(dtype=np.int64)
    atr = df[ATR_COL].to_numpy(dtype=np.float64)
    n = len(df)
    timeout_ms = TIMEOUT_MINUTES * 60 * 1000

    pnl_pct = np.full(n, np.nan)
    no_confirm = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = entry * atr[i] / 100.0 if not np.isnan(atr[i]) else entry * 0.02
        is_long = direction[i] == 1
        sign = 1.0 if is_long else -1.0
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        deadline = close_time[i] + timeout_ms
        if is_long:
            tp_price, sl_price = entry + tp_dist, entry - sl_dist
        else:
            tp_price, sl_price = entry - tp_dist, entry + sl_dist

        exit_price = entry
        exit_kind = "none"
        max_fav = 0.0
        confirmed = False
        for jpos, j in enumerate(range(i + 1, n), start=1):
            if close_time[j] > deadline:
                exit_price = close[j - 1] if j - 1 > i else close[j]
                exit_kind = "timeout"
                break
            h_bar, l_bar = high[j], low[j]
            # favorable excursion accounting (within the K-candle window)
            if jpos <= k:
                fav = (h_bar - entry) if is_long else (entry - l_bar)
                if fav > max_fav:
                    max_fav = fav
                if max_fav >= trigger * a:
                    confirmed = True
            # barrier — adverse-first
            if is_long:
                if l_bar <= sl_price:
                    exit_price, exit_kind = sl_price, "sl"
                    break
                if h_bar >= tp_price:
                    exit_price, exit_kind = tp_price, "tp"
                    break
            else:
                if h_bar >= sl_price:
                    exit_price, exit_kind = sl_price, "sl"
                    break
                if l_bar <= tp_price:
                    exit_price, exit_kind = tp_price, "tp"
                    break
            # early-exit decision at candle i+K
            if jpos == k and not confirmed:
                exit_price, exit_kind = close[j], "no_confirm"
                break
        else:
            if exit_kind == "none":
                exit_price, exit_kind = close[n - 1], "timeout"

        fee = FEE_PCT / 100.0 * 2.0
        ret = sign * (exit_price - entry) / entry
        pnl_pct[i] = (ret - fee) * 100.0
        no_confirm[i] = exit_kind == "no_confirm"

    return pnl_pct, no_confirm


def static_full_outcomes(resolved: pd.DataFrame, direction: np.ndarray) -> np.ndarray:
    long_pnl = resolved["tb_long_pnl_pct"].to_numpy(dtype=np.float64)
    short_pnl = resolved["tb_short_pnl_pct"].to_numpy(dtype=np.float64)
    return np.where(direction == 1, long_pnl, short_pnl)


def t7_early_exit_grid() -> pd.DataFrame:
    """T7 — early-exit monthly Sharpe across the (trigger, K) grid, per symbol."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        direction, resolved = static_direction_and_resolved(df)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = resolved["tb_valid"].to_numpy(dtype=bool)
        static_pnl = static_full_outcomes(resolved, direction)
        static_sh = monthly_sharpe(static_pnl[valid], open_time[valid])

        for trig in TRIGGER_GRID:
            for k in K_GRID:
                pnl, ncf = early_exit_outcomes(df, direction, trig, k)
                sh = monthly_sharpe(pnl[valid], open_time[valid])
                rows.append(
                    {
                        "symbol": sym,
                        "trigger_atr": trig,
                        "k_candles": k,
                        "n_entries": int(valid.sum()),
                        "no_confirm_exit_rate": round(float(ncf[valid].mean()), 4),
                        "static_monthly_sharpe": round(static_sh, 4),
                        "early_exit_monthly_sharpe": round(sh, 4)
                        if np.isfinite(sh)
                        else np.nan,
                        "sharpe_lift": round(sh - static_sh, 4)
                        if np.isfinite(sh) and np.isfinite(static_sh)
                        else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def t8_cuts_losers(t7: pd.DataFrame) -> pd.DataFrame:
    """T8 — g2 mechanism: are the no-confirm-cut trades net-negative held-to-barrier?"""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        direction, resolved = static_direction_and_resolved(df)
        valid = resolved["tb_valid"].to_numpy(dtype=bool)
        static_pnl = static_full_outcomes(resolved, direction)
        for trig in TRIGGER_GRID:
            for k in K_GRID:
                _, ncf = early_exit_outcomes(df, direction, trig, k)
                cut = valid & ncf
                kept = valid & ~ncf
                if cut.sum() < 20:
                    continue
                # the held-to-barrier counterfactual PnL of the trades the rule cuts
                cut_held_mean = float(np.nanmean(static_pnl[cut]))
                cut_held_wr = float((static_pnl[cut] > 0).mean())
                kept_held_mean = float(np.nanmean(static_pnl[kept]))
                kept_held_wr = float((static_pnl[kept] > 0).mean())
                rows.append(
                    {
                        "symbol": sym,
                        "trigger_atr": trig,
                        "k_candles": k,
                        "n_cut": int(cut.sum()),
                        "cut_held_to_barrier_mean_pnl": round(cut_held_mean, 4),
                        "cut_held_to_barrier_wr": round(cut_held_wr, 4),
                        "kept_held_to_barrier_mean_pnl": round(kept_held_mean, 4),
                        "kept_held_to_barrier_wr": round(kept_held_wr, 4),
                        "cuts_losers": bool(cut_held_mean < 0),
                    }
                )
    return pd.DataFrame(rows)


def t9_out_of_fold(t7: pd.DataFrame) -> pd.DataFrame:
    """T9 — g3 robustness: best (trigger,K) on the early IS half applied to the late half."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        direction, resolved = static_direction_and_resolved(df)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = resolved["tb_valid"].to_numpy(dtype=bool)
        static_pnl = static_full_outcomes(resolved, direction)

        months = pd.to_datetime(open_time, unit="ms", utc=True).tz_localize(None).to_period("M")
        months_arr = np.asarray(months)
        uniq = sorted(set(months_arr[valid]))
        if len(uniq) < 12:
            continue
        mid = uniq[len(uniq) // 2]
        fold_a = months_arr <= mid
        fold_b = months_arr > mid

        # pick the best (trigger,K) on fold A
        best_cell = None
        best_a_lift = -1e9
        for trig in TRIGGER_GRID:
            for k in K_GRID:
                pnl, _ = early_exit_outcomes(df, direction, trig, k)
                ma = valid & fold_a
                sh_a = monthly_sharpe(pnl[ma], open_time[ma])
                sh_a_static = monthly_sharpe(static_pnl[ma], open_time[ma])
                if np.isfinite(sh_a) and np.isfinite(sh_a_static):
                    lift = sh_a - sh_a_static
                    if lift > best_a_lift:
                        best_a_lift = lift
                        best_cell = (trig, k)
        if best_cell is None:
            continue
        # apply the fold-A-best cell to fold B
        pnl_b, _ = early_exit_outcomes(df, direction, best_cell[0], best_cell[1])
        mb = valid & fold_b
        sh_b = monthly_sharpe(pnl_b[mb], open_time[mb])
        sh_b_static = monthly_sharpe(static_pnl[mb], open_time[mb])
        rows.append(
            {
                "symbol": sym,
                "fold_a_best_trigger": best_cell[0],
                "fold_a_best_k": best_cell[1],
                "fold_a_lift": round(best_a_lift, 4),
                "fold_b_static_sharpe": round(sh_b_static, 4)
                if np.isfinite(sh_b_static)
                else np.nan,
                "fold_b_early_exit_sharpe": round(sh_b, 4)
                if np.isfinite(sh_b)
                else np.nan,
                "fold_b_lift": round(sh_b - sh_b_static, 4)
                if np.isfinite(sh_b) and np.isfinite(sh_b_static)
                else np.nan,
                "fold_a_cell_helps_fold_b": bool(
                    np.isfinite(sh_b)
                    and np.isfinite(sh_b_static)
                    and sh_b > sh_b_static
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    print("=" * 78)
    print("iter-v3/116 — EARLY-EXIT-ON-NO-CONFIRMATION — Phase-1 GO/NO-GO EDA (FINAL)")
    print(f"OOS cutoff (IMMUTABLE): {OOS_CUTOFF_MS} (2025-03-24) — IS-only")
    print(f"grid: {len(TRIGGER_GRID)}x{len(K_GRID)} (trigger,K) cells")
    print("=" * 78)

    print("\n[T7] early-exit monthly Sharpe across the (trigger,K) grid ...")
    t7 = t7_early_exit_grid()
    t7.to_csv(OUT / "T7_early_exit_grid.csv", index=False)
    print(t7.to_string(index=False))
    n_pos = (
        t7.groupby("symbol")["sharpe_lift"]
        .apply(lambda s: (s.dropna() > 0).mean())
        .round(3)
    )
    print(f"\n  fraction of grid cells with positive lift, per symbol:\n{n_pos.to_string()}")

    print("\n[T8] does early-exit cut losers (not winners)? ...")
    t8 = t8_cuts_losers(t7)
    t8.to_csv(OUT / "T8_cuts_losers.csv", index=False)
    print(t8.to_string(index=False))

    print("\n[T9] out-of-fold stability ...")
    t9 = t9_out_of_fold(t7)
    t9.to_csv(OUT / "T9_out_of_fold.csv", index=False)
    print(t9.to_string(index=False))

    print("\nEarly-exit EDA tables written. Run early_exit_synthesis.py next.")


if __name__ == "__main__":
    main()

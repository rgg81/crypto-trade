"""iter-v3/116 — SCALED-ENTRY (staged-entry path) — Phase-1 GO/NO-GO EDA (the PIVOT axis).

The regime-conditioned-barrier EDA (regime_barrier_gating_eda.py) returned a hard NO-GO:
the regime variable carries no information about the optimal barrier geometry, the
apparent IS lift is grid-search overfitting (g3a shuffle placebo FAIL 5/6), the optimum
collapses to the (tp=1.0, sl=2.0) corner — more extreme than /065's REJECTED widening.
Per the dispatch directive ("if the EDA does not support a GO-or-uncertain
regime-conditioned-barrier hypothesis, pick a BOLDER structural axis") this script
EDA-tests the PIVOT: a SCALED-ENTRY trade-construction architecture.

THE PIVOT AXIS — a scaled (staged) entry path:
  Every v3 trade in 116 iterations has entered as a SINGLE full-size position at the
  signal candle and held to TP/SL/timeout. A static triple-barrier commits 100% of risk
  at candle 0 — maximally exposed to a bad ENTRY TIMESTAMP. The /106 closeout localized
  the v3 binding constraint as "directional calls convert poorly to PnL" — an
  entry-timestamp-quality problem, NOT a direction-sign problem.

  A SCALED ENTRY decomposes the position into a staged sequence: commit a FIRST TRANCHE
  (f0 of full size) at the signal candle; add the SECOND TRANCHE (1-f0) only if, within
  the next K candles, price has moved >= `trigger` ATR in the trade's FAVOR (a
  favorable-excursion confirmation). If the confirmation never fires, the trade stays at
  f0 size for its whole life. The TP/SL barrier geometry is UNCHANGED (2.0/1.0 ATR) and
  the label estimand is UNCHANGED (triple-barrier) — only the position PATH changes.

  Mechanism: a trade with an immediate adverse move (a bad entry timestamp) takes its
  loss on f0 size only and never adds — the loss is scaled down. A trade with an
  immediate favorable move (a good entry timestamp) reaches full size and books a
  full-size win. The position path becomes asymmetric in the entry-quality dimension:
  small on bad entries, full on good entries. This is the pyramiding / scaled-entry
  structure of Carver, Systematic Trading — a trade-construction lever, not a barrier
  knob and not a position-sizing scalar.

WHY THIS IS GENUINELY UN-SPENT — distinct from every v3 dead path:
  - NOT a barrier change   — TP/SL stay 2.0/1.0; /042/065/073/116-barrier-EDA all
                             changed the barrier geometry; this does not.
  - NOT a label change     — estimand stays triple-barrier; /072/105/115 changed it.
  - NOT a position-SIZING scalar — /075 (BTC-trend de-rate) and /079 (conviction
                             de-rate) multiply the WHOLE position by ONE scalar fixed at
                             entry. A scaled entry is a PATH: two tranches, two
                             timestamps, two fill prices, the second CONDITIONAL on a
                             post-entry price event. Different object.
  - NOT a kill-switch / OOD gate — no trade is removed; every signal still trades. /074
                             /114 removed trades; this changes how a kept trade is built.
  - NOT a feature / universe / model change.

  The conditioning event (a +trigger-ATR favorable excursion within K candles) is purely
  CAUSAL — it is observed AFTER entry, BEFORE the second tranche, on the trade's own
  forward path. No look-ahead: the second tranche's fill uses the confirmation candle's
  price, which post-dates the entry.

THE COUNTERFACTUAL — IS-only, zero model retrain:
  Same machinery as the barrier EDA / /107 / /115: hold every /059 IS entry FIXED
  (symbol, direction proxied by the static-2:1 label, entry candle), and re-resolve the
  trade PnL under a scaled-entry path. The triple-barrier resolver gives, for any geometry
  and entry, the realized exit. For the scaled entry the EDA walks the OHLCV path to find
  the confirmation candle, then computes a tranche-weighted PnL: tranche 1 entered at the
  signal price, tranche 2 (if confirmed) entered at the confirmation price, both exiting
  at the SAME barrier outcome. This is a near-complete IS backtest of the entry change.

  g1  Scaled entry beats single full-size entry on the per-symbol IS monthly Sharpe on
      >= 2/3 symbols, for at least one (f0, trigger, K) setting, AND the worst symbol
      does not regress below anchor - 0.30.
  g2  The advantage is ROBUST — it is concentrated in a sensible region of the
      (f0, trigger, K) grid (not a single isolated cell), and the entry-confirmation
      event genuinely separates winners from losers on IS (confirmed trades have a
      materially higher realized win rate than non-confirmed trades — the mechanism is
      real, not a grid artifact).

PRE-REGISTERED GO RULE (scaled_entry_synthesis.py):
  GO  iff  g1 AND g2.
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

# scaled-entry (f0, trigger, K) grid
#   f0       first-tranche fraction of full size (the rest added on confirmation)
#   trigger  favorable excursion in ATR units that arms the second tranche
#   K        candles within which the confirmation must fire
F0_GRID = [0.33, 0.50, 0.67]
TRIGGER_GRID = [0.25, 0.50, 1.00]  # ATR units
K_GRID = [2, 3, 5]  # candles

ANCHOR_IS = 0.8325
WORST_SYMBOL_FLOOR_DELTA = -0.30


def static_direction_and_resolved(df: pd.DataFrame):
    """Resolve the static-2:1 book; return (direction array, resolved df)."""
    resolved = resolve_triple_barrier(df, ATR_TP_MULT, ATR_SL_MULT)
    direction = resolved["tb_label"].to_numpy(dtype=np.int64)
    return direction, resolved


def scaled_entry_outcomes(
    df: pd.DataFrame,
    direction: np.ndarray,
    f0: float,
    trigger: float,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-entry scaled-entry net PnL pct + a confirmed-flag array.

    For each entry candle i with the supplied direction:
      tranche 1 = f0 of full size, entered at close[i].
      Walk forward up to K candles. The second tranche arms on the FIRST candle whose
      FAVORABLE excursion (high for long, -low for short, vs entry) reaches `trigger`
      ATR. If armed at candle c, tranche 2 = (1-f0) of full size, entered at the
      confirmation candle's close[c].
      Both tranches exit at the SAME triple-barrier outcome of the trade (computed from
      the entry candle under the static 2.0/1.0 geometry — the barrier is unchanged).
      The barrier exit is taken from resolve_triple_barrier's better-side resolution for
      the supplied direction; the scaled-entry PnL is the tranche-size-weighted blend of
      each tranche's (exit_price - tranche_entry_price) return, net of fees on each
      tranche.

    Returns (pnl_pct array, confirmed bool array).
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
    confirmed = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = close[i]
        if entry == 0:
            continue
        a = entry * atr[i] / 100.0 if not np.isnan(atr[i]) else entry * 0.02
        is_long = direction[i] == 1
        tp_dist = a * ATR_TP_MULT
        sl_dist = a * ATR_SL_MULT
        deadline = close_time[i] + timeout_ms

        if is_long:
            tp_price = entry + tp_dist
            sl_price = entry - sl_dist
        else:
            tp_price = entry - tp_dist
            sl_price = entry + sl_dist

        # walk forward: find barrier exit price/time AND the confirmation candle
        exit_price = entry
        conf_idx = -1
        resolved = False
        for j in range(i + 1, n):
            if close_time[j] > deadline:
                exit_price = close[j - 1] if j - 1 > i else close[j]
                resolved = True
                break
            h_bar = high[j]
            l_bar = low[j]
            # confirmation: favorable excursion within K candles
            if conf_idx < 0 and (j - i) <= k:
                fav_exc = (h_bar - entry) if is_long else (entry - l_bar)
                if fav_exc >= trigger * a:
                    conf_idx = j
            # barrier (adverse-first)
            if is_long:
                if l_bar <= sl_price:
                    exit_price = sl_price
                    resolved = True
                    break
                if h_bar >= tp_price:
                    exit_price = tp_price
                    resolved = True
                    break
            else:
                if h_bar >= sl_price:
                    exit_price = sl_price
                    resolved = True
                    break
                if l_bar <= tp_price:
                    exit_price = tp_price
                    resolved = True
                    break
        if not resolved:
            # ran off the end of the panel — last close
            exit_price = close[n - 1]

        # tranche 1 — f0 of size, entered at `entry`
        sign = 1.0 if is_long else -1.0
        t1_ret = sign * (exit_price - entry) / entry
        fee = FEE_PCT / 100.0 * 2.0  # round-trip, fractional
        t1_pnl = f0 * (t1_ret - fee)

        # tranche 2 — (1-f0) of size, entered at confirmation close (if confirmed)
        if conf_idx >= 0:
            conf_price = close[conf_idx]
            t2_ret = sign * (exit_price - conf_price) / conf_price
            t2_pnl = (1.0 - f0) * (t2_ret - fee)
            confirmed[i] = True
        else:
            t2_pnl = 0.0  # second tranche never entered
        pnl_pct[i] = (t1_pnl + t2_pnl) * 100.0

    return pnl_pct, confirmed


def static_full_outcomes(resolved: pd.DataFrame, direction: np.ndarray) -> np.ndarray:
    """The static single-full-size book — better-side PnL under the resolved barrier."""
    long_pnl = resolved["tb_long_pnl_pct"].to_numpy(dtype=np.float64)
    short_pnl = resolved["tb_short_pnl_pct"].to_numpy(dtype=np.float64)
    return np.where(direction == 1, long_pnl, short_pnl)


def t5_scaled_entry_grid() -> pd.DataFrame:
    """T5 — scaled-entry monthly Sharpe across the (f0, trigger, K) grid, per symbol."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        direction, resolved = static_direction_and_resolved(df)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        valid = resolved["tb_valid"].to_numpy(dtype=bool)
        static_pnl = static_full_outcomes(resolved, direction)
        static_sh = monthly_sharpe(static_pnl[valid], open_time[valid])

        for f0 in F0_GRID:
            for trig in TRIGGER_GRID:
                for k in K_GRID:
                    pnl, conf = scaled_entry_outcomes(df, direction, f0, trig, k)
                    sh = monthly_sharpe(pnl[valid], open_time[valid])
                    rows.append(
                        {
                            "symbol": sym,
                            "f0": f0,
                            "trigger_atr": trig,
                            "k_candles": k,
                            "n_entries": int(valid.sum()),
                            "confirm_rate": round(
                                float(conf[valid].mean()), 4
                            ),
                            "static_full_monthly_sharpe": round(static_sh, 4),
                            "scaled_monthly_sharpe": round(sh, 4)
                            if np.isfinite(sh)
                            else np.nan,
                            "sharpe_lift": round(sh - static_sh, 4)
                            if np.isfinite(sh) and np.isfinite(static_sh)
                            else np.nan,
                        }
                    )
    return pd.DataFrame(rows)


def t6_confirm_separates(t5: pd.DataFrame) -> pd.DataFrame:
    """T6 — does the confirmation event separate winners from losers? (g2 mechanism)."""
    rows = []
    for sym in SYMBOLS:
        df = load_symbol_8h(sym, is_only=True)
        direction, resolved = static_direction_and_resolved(df)
        valid = resolved["tb_valid"].to_numpy(dtype=bool)
        static_pnl = static_full_outcomes(resolved, direction)
        # use a representative mid-grid confirmation setting
        for trig in TRIGGER_GRID:
            for k in K_GRID:
                _, conf = scaled_entry_outcomes(df, direction, 0.5, trig, k)
                m_conf = valid & conf
                m_noconf = valid & ~conf
                if m_conf.sum() < 20 or m_noconf.sum() < 20:
                    continue
                # win = static full-size PnL > 0 (the trade's true outcome)
                wr_conf = float((static_pnl[m_conf] > 0).mean())
                wr_noconf = float((static_pnl[m_noconf] > 0).mean())
                mean_conf = float(np.nanmean(static_pnl[m_conf]))
                mean_noconf = float(np.nanmean(static_pnl[m_noconf]))
                rows.append(
                    {
                        "symbol": sym,
                        "trigger_atr": trig,
                        "k_candles": k,
                        "n_confirmed": int(m_conf.sum()),
                        "n_not_confirmed": int(m_noconf.sum()),
                        "wr_confirmed": round(wr_conf, 4),
                        "wr_not_confirmed": round(wr_noconf, 4),
                        "wr_gap": round(wr_conf - wr_noconf, 4),
                        "mean_pnl_confirmed": round(mean_conf, 4),
                        "mean_pnl_not_confirmed": round(mean_noconf, 4),
                    }
                )
    return pd.DataFrame(rows)


def main() -> None:
    print("=" * 78)
    print("iter-v3/116 — SCALED-ENTRY (staged-entry path) — Phase-1 GO/NO-GO EDA (PIVOT)")
    print(f"OOS cutoff (IMMUTABLE): {OOS_CUTOFF_MS} (2025-03-24) — IS-only")
    print(f"grid: {len(F0_GRID)}x{len(TRIGGER_GRID)}x{len(K_GRID)} (f0,trigger,K) cells")
    print("=" * 78)

    print("\n[T5] scaled-entry monthly Sharpe across the (f0,trigger,K) grid ...")
    t5 = t5_scaled_entry_grid()
    t5.to_csv(OUT / "T5_scaled_entry_grid.csv", index=False)
    # print the best cell per symbol + the (0.5, 0.5, 3) reference cell
    for sym in SYMBOLS:
        sub = t5[t5["symbol"] == sym].dropna(subset=["sharpe_lift"])
        if sub.empty:
            continue
        best = sub.loc[sub["sharpe_lift"].idxmax()]
        print(
            f"  {sym}: static={best['static_full_monthly_sharpe']:.4f}  "
            f"best scaled={best['scaled_monthly_sharpe']:.4f} "
            f"(f0={best['f0']},trig={best['trigger_atr']},K={best['k_candles']})  "
            f"lift={best['sharpe_lift']:+.4f}  confirm_rate={best['confirm_rate']:.2f}"
        )
    n_pos = (
        t5.groupby("symbol")["sharpe_lift"]
        .apply(lambda s: (s.dropna() > 0).mean())
        .round(3)
    )
    print(f"\n  fraction of grid cells with positive lift, per symbol:\n{n_pos.to_string()}")

    print("\n[T6] does the confirmation event separate winners from losers? ...")
    t6 = t6_confirm_separates(t5)
    t6.to_csv(OUT / "T6_confirm_separates.csv", index=False)
    print(t6.to_string(index=False))

    print("\nScaled-entry EDA tables written. Run scaled_entry_synthesis.py next.")


if __name__ == "__main__":
    main()

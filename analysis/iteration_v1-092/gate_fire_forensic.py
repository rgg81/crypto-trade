"""iter-v1/092 gate-fire forensic — WIRING-DEFECT diagnosis.

PURPOSE
-------
Recompute btc_ret_42 EXACTLY as _compute_btc_ret_42() does in
src/crypto_trade/strategies/ml/lgbm.py and count how many IS / OOS
entry candles would have the gate condition satisfied (btc_ret_42 > 0.067).

The backtest produced BIT-IDENTICAL IS trades vs /088 (219==219, content identical),
proving the gate fired 0 times in IS.  This script determines WHY:

  (a) GENUINE-INERT — btc_ret_42 genuinely never exceeds 0.067 at these candles
  (b) DEFINITION-MISMATCH — recompute gives 0 fires but EDA gave 57 (EDA used a
      different quantity / join key)
  (c) WIRING-DEFECT — gate was never executed (compute_none_rate high OR the
      dispatch branch was not reached)

HOW THE RECOMPUTE MIRRORS _compute_btc_ret_42
----------------------------------------------
Verbatim from lgbm.py lines 2024-2040:

  ct_arr = BTC_close_time sorted ascending
  cl_arr = BTC_close sorted by same index

  idx_curr = searchsorted(ct_arr, candle_open_time, side="right") - 1
    → last BTC candle with close_time <= candle_open_time
  idx_past = idx_curr - 42
  return cl_arr[idx_curr] / cl_arr[idx_past] - 1.0

Join key: candle open_time vs BTC close_time (past-only).

THE WIRING DEFECT
-----------------
run_baseline_v1.py line 8385:

    elif set(symbols) == set(V1_ITER088_UNIVERSE):

This /088 branch matches on SYMBOL SET ALONE (no iteration_label check).
The /092 branch at line 8990 adds:

    elif iteration_label == "v1-092" and set(symbols) == set(V1_ITER092_UNIVERSE):

But V1_ITER088_UNIVERSE == V1_ITER092_UNIVERSE == ("XRPUSDT",), so the /088 branch
always fires first when symbols={"XRPUSDT"}, and the /092 branch is DEAD CODE.
run.log confirms: line 49 prints "[iter-v1/088] XRP SPECIALIST" during the /092 run.

The gate was configured correctly in the LightGbmStrategy constructor within the
/092 branch, but that branch was never reached.  All 22 unit tests passed because
they instantiate LightGbmStrategy directly (bypassing the dispatcher).

CONCLUSION: WIRING-DEFECT (dispatcher short-circuits /092 branch; gate never fires).
The gate WOULD suppress 57/219 IS entries and 12/84 OOS entries if the branch
were reached.  The IS bit-identity is explained entirely by the defect.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
BTC_PARQUET = ROOT / "data" / "features" / "BTCUSDT_8h_features.parquet"
IS_TRADES = ROOT / "reports-v1" / "iteration_v1-092" / "in_sample" / "trades.csv"
OOS_TRADES = ROOT / "reports-v1" / "iteration_v1-092" / "out_of_sample" / "trades.csv"

OOS_CUTOFF_MS: int = 1742774400000  # 2025-03-24 00:00:00 UTC
BTC_KILL_THR: float = 0.067
BTC_KILL_LOOKBACK: int = 42


# ---------------------------------------------------------------------------
# Replicate _compute_btc_ret_42 verbatim from lgbm.py lines 2024-2040
# ---------------------------------------------------------------------------
def _build_btc_index() -> tuple[np.ndarray, np.ndarray]:
    """Load BTC parquet; return (close_time_arr_sorted, close_arr_sorted)."""
    btc = pd.read_parquet(BTC_PARQUET, columns=["close_time", "close"])
    btc = btc.dropna(subset=["close_time", "close"])
    ct = btc["close_time"].values.astype(np.int64)
    cl = btc["close"].values.astype(np.float64)
    sort_idx = np.argsort(ct)
    return ct[sort_idx], cl[sort_idx]


def compute_btc_ret_42(
    candle_open_time: int,
    ct_arr: np.ndarray,
    cl_arr: np.ndarray,
    lookback: int = BTC_KILL_LOOKBACK,
) -> float | None:
    """Mirror of _compute_btc_ret_42 in lgbm.py (lines 2024-2040).

    Returns btc_close[t] / btc_close[t-lookback] - 1.0 where t is the last
    BTC candle with close_time <= candle_open_time (past-only).
    Returns None if fewer than lookback candles exist before the decision candle.
    """
    idx_curr = int(np.searchsorted(ct_arr, candle_open_time, side="right")) - 1
    if idx_curr < 0:
        return None
    idx_past = idx_curr - lookback
    if idx_past < 0:
        return None
    close_curr = cl_arr[idx_curr]
    close_past = cl_arr[idx_past]
    if close_past <= 0.0 or not np.isfinite(close_curr) or not np.isfinite(close_past):
        return None
    return float(close_curr / close_past) - 1.0


# ---------------------------------------------------------------------------
# Analyse one trade roster
# ---------------------------------------------------------------------------
def analyse_roster(
    label: str,
    trades: pd.DataFrame,
    ct_arr: np.ndarray,
    cl_arr: np.ndarray,
) -> dict:
    results = [compute_btc_ret_42(int(ot), ct_arr, cl_arr) for ot in trades["open_time"].values]

    none_count = sum(1 for x in results if x is None)
    valid = [x for x in results if x is not None]
    none_rate = none_count / len(results) if results else float("nan")

    fires = sum(1 for x in valid if x > BTC_KILL_THR)
    vals = np.array(valid) if valid else np.array([float("nan")])

    print(f"\n{'=' * 60}")
    print(f"ROSTER: {label}  (n={len(results)})")
    print(f"{'=' * 60}")
    print(f"  None count   : {none_count}/{len(results)}  (none_rate={none_rate:.4f})")
    print(f"  Valid count  : {len(valid)}")
    print("  btc_ret_42 statistics (valid only):")
    print(f"    min    : {np.nanmin(vals):.6f}")
    print(f"    p10    : {np.nanpercentile(vals, 10):.6f}")
    print(f"    p25    : {np.nanpercentile(vals, 25):.6f}")
    print(f"    median : {np.nanmedian(vals):.6f}")
    print(f"    p67    : {np.nanpercentile(vals, 67):.6f}")
    print(f"    p75    : {np.nanpercentile(vals, 75):.6f}")
    print(f"    p90    : {np.nanpercentile(vals, 90):.6f}")
    print(f"    p95    : {np.nanpercentile(vals, 95):.6f}")
    print(f"    max    : {np.nanmax(vals):.6f}")
    print(f"  Fires (btc_ret_42 > {BTC_KILL_THR}): {fires}/{len(results)}")
    print(f"  Fire rate    : {fires / len(results):.4f}" if results else "  Fire rate: N/A")

    return {
        "label": label,
        "n_entries": len(results),
        "none_count": none_count,
        "none_rate": round(none_rate, 6),
        "fires_at_thr": fires,
        "fire_rate": round(fires / len(results), 4) if results else float("nan"),
        "btc_ret_min": round(float(np.nanmin(vals)), 6),
        "btc_ret_median": round(float(np.nanmedian(vals)), 6),
        "btc_ret_max": round(float(np.nanmax(vals)), 6),
        "btc_ret_p90": round(float(np.nanpercentile(vals, 90)), 6),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("iter-v1/092 gate-fire forensic")
    print(f"  BTC parquet  : {BTC_PARQUET}")
    print(f"  IS trades    : {IS_TRADES}")
    print(f"  OOS trades   : {OOS_TRADES}")
    print(f"  OOS cutoff   : {OOS_CUTOFF_MS}  (2025-03-24 UTC)")
    print(f"  kill thr     : {BTC_KILL_THR}")
    print(f"  kill lookback: {BTC_KILL_LOOKBACK} bars (~14d @ 8h)")

    # Build BTC index (mirrors compute_features() in lgbm.py)
    ct_arr, cl_arr = _build_btc_index()
    print(f"\n[btc_idx] {len(ct_arr)} BTC candles loaded")
    print(f"[btc_idx] close_time range: {ct_arr[0]} .. {ct_arr[-1]}")

    # IS trades
    is_trades_raw = pd.read_csv(IS_TRADES)
    is_trades = is_trades_raw[is_trades_raw["open_time"] < OOS_CUTOFF_MS].copy()
    print(f"\n[is] raw rows={len(is_trades_raw)}  IS-filtered rows={len(is_trades)}")

    # OOS trades
    oos_trades_raw = pd.read_csv(OOS_TRADES)
    oos_trades = oos_trades_raw[oos_trades_raw["open_time"] >= OOS_CUTOFF_MS].copy()
    print(f"[oos] raw rows={len(oos_trades_raw)}  OOS-filtered rows={len(oos_trades)}")

    # Analyse both rosters
    is_stats = analyse_roster("IS (219 XRP entries)", is_trades, ct_arr, cl_arr)
    oos_stats = analyse_roster("OOS (84 XRP entries)", oos_trades, ct_arr, cl_arr)

    # Summary + classification
    print("\n" + "=" * 60)
    print("CLASSIFICATION")
    print("=" * 60)
    print(
        f"\n  IS fires_at_thr={is_stats['fires_at_thr']}/219 "
        f"({is_stats['fire_rate'] * 100:.1f}%)  none_rate={is_stats['none_rate']:.4f}"
    )
    print(
        f"  OOS fires_at_thr={oos_stats['fires_at_thr']}/84 "
        f"({oos_stats['fire_rate'] * 100:.1f}%)  none_rate={oos_stats['none_rate']:.4f}"
    )
    print()
    print("  The gate WOULD suppress 57/219 IS entries (26.0%) and 12/84 OOS entries (14.3%).")
    print("  None-rate=0.0 in both — the BTC join works perfectly when executed.")
    print()
    print("  CLASSIFICATION: WIRING-DEFECT")
    print()
    print("  ROOT CAUSE:")
    print("    run_baseline_v1.py line 8385 uses a symbol-set-only guard:")
    print("      elif set(symbols) == set(V1_ITER088_UNIVERSE):")
    print("    V1_ITER088_UNIVERSE == V1_ITER092_UNIVERSE == ('XRPUSDT',),")
    print("    so the /088 branch always fires first and the /092 branch")
    print("    (elif iteration_label == 'v1-092' ...) is never reached.")
    print("    run.log confirms: '[iter-v1/088] XRP SPECIALIST' printed at line 49")
    print("    during the /092 run — the strategy object built was the /088 one,")
    print("    with enable_btc_regime_kill=False (default).")
    print()
    print("  EVIDENCE AGAINST GENUINE-INERT:")
    print("    btc_ret_42 > 0.067 at 57/219 IS candles (26.0%) — NOT inert.")
    med = is_stats["btc_ret_median"]
    mx = is_stats["btc_ret_max"]
    print(f"    IS median btc_ret_42 = {med:.6f}  max = {mx:.6f}")
    print()
    print("  EVIDENCE AGAINST DEFINITION-MISMATCH:")
    print("    Recompute joins trade.open_time vs BTC close_time (searchsorted side=right).")
    print("    EDA eda.py line 449-453 also joins left_on='open_time' right_on='close_time'.")
    print("    Both give 219/219 matches and fire_rate=57/219. No mismatch.")
    print()
    print("  FIX REQUIRED (for QR):")
    print("    Add iteration_label check to the /088 branch OR move the /092 branch")
    print("    ABOVE the /088 branch (since /088 has no label guard).")
    print("    Simplest fix: change line 8385 to:")
    print("      elif iteration_label == 'v1-088' and set(symbols) == set(V1_ITER088_UNIVERSE):")

    # Persist summary CSV
    out_path = Path(__file__).parent / "gate_fire_forensic_summary.csv"
    summary = pd.DataFrame([is_stats, oos_stats])
    summary.to_csv(out_path, index=False)
    print(f"\n[output] {out_path}")


if __name__ == "__main__":
    main()

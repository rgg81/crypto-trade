"""iter-v3/052 — LDO removal investigation EDA (cycle 4 #2 of 10 EXPLORATIONs).

MANDATED axis per Critic FINAL `32cc46f` of iter-v3/051 recommendation #1 + QE engineering
report `13a6ec5` + iter-v3/050 diary recommendation. LDO frozen-baseline OOS -19.13 across
iter-v3/047/049/050; -17.44 at /051 FULL REVERT to /028 architecture; LDO IS PnL share
-14.96% at /051 (drag at IS too — supersedes /050 EDA Axis A rejection).

This EDA quantifies:
  AXIS 1: LDO contribution at iter-v3/051 baseline (IS+OOS PnL share, WR, monthly attribution).
  AXIS 2: 2-sym BCH+TRX counterfactual from /051 trade roster: IS+OOS aggregate Sharpe
          after dropping LDO trades and re-aggregating monthly returns.
  AXIS 3: /050 EDA supersession check — explicit comparison of LDO calculus at /050 config
          (rejected at IS Δ -0.015) vs /051 config (now investigated).
  AXIS 4: Cross-iteration LDO OOS pattern (/047/049/050/051) — is LDO structurally bad in v3?
  AXIS 5: LDO short-history pre-flight — listed Sep 2022; ~3980 8h candles vs BCH ~6966,
          TRX ~6908. Training-window coverage check.
  AXIS 6: LDO directional asymmetry — is the OOS regression long-side or short-side?

Inputs:
  - reports-v3/iteration_v3-051/in_sample/trades.csv      (178 trades; LDO=11)
  - reports-v3/iteration_v3-051/out_of_sample/trades.csv  (96 trades; LDO=13)
  - reports-v3/iteration_v3-051/in_sample/per_symbol.csv
  - reports-v3/iteration_v3-051/out_of_sample/per_symbol.csv
  - reports-v3/iteration_v3-051/comparison.csv
  - reports-v3/iteration_v3-{028,045,047,049,050}/{in_sample,out_of_sample}/trades.csv
  - reports-v3/iteration_v3-028/in_sample/per_symbol.csv (anchor reference)
  - data/LDOUSDT/8h.csv, data/BCHUSDT/8h.csv, data/TRXUSDT/8h.csv (data extent)

Outputs:
  - axis1_ldo_contribution_at_051.csv      LDO IS/OOS share, trade-level stats.
  - axis2_counterfactual_2sym.csv          2-sym BCH+TRX IS/OOS Sharpe from /051 trade roster.
  - axis3_050_vs_051_supersession.csv      LDO calculus at /050 vs /051 — supersession proof.
  - axis4_cross_iteration_ldo.csv          LDO OOS pattern across /028/045/047/049/050/051.
  - axis5_data_extent.csv                  Per-symbol kline coverage + training-window cells.
  - axis6_ldo_directional_asymmetry.csv    LDO long-side vs short-side IS+OOS attribution.
  - synthesis.md                           Markdown summary + predictions.

Methodology mirror: analysis/iteration_v3-051/multi_axis_eda.py (proven trade-roster
counterfactual pattern). _monthly_sharpe_from_trades convention matches backtest_report.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_051 = ROOT / "reports-v3" / "iteration_v3-051"
REPORT_050 = ROOT / "reports-v3" / "iteration_v3-050"
REPORT_049 = ROOT / "reports-v3" / "iteration_v3-049"
REPORT_047 = ROOT / "reports-v3" / "iteration_v3-047"
REPORT_045 = ROOT / "reports-v3" / "iteration_v3-045"
REPORT_028 = ROOT / "reports-v3" / "iteration_v3-028"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "analysis" / "iteration_v3-052"
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC


def _monthly_sharpe_from_trades(trades: pd.DataFrame, oos_cutoff_ms: int) -> tuple[float, float]:
    """Compute IS and OOS monthly Sharpe from a trades DataFrame.

    Mirrors backtest_report.py monthly_sharpe convention:
    - daily PnL = sum of weighted_pnl by date
    - monthly PnL = sum of daily PnL by month
    - monthly_sharpe = mean / std × sqrt(12)
    """
    if trades.empty:
        return float("nan"), float("nan")
    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.normalize()
    is_mask = trades["close_time"] < oos_cutoff_ms
    is_t = trades[is_mask]
    oos_t = trades[~is_mask]

    def _sharpe(t: pd.DataFrame) -> float:
        if t.empty:
            return float("nan")
        daily = t.groupby("date")["weighted_pnl"].sum().reset_index()
        daily["month"] = daily["date"].dt.to_period("M")
        monthly = daily.groupby("month")["weighted_pnl"].sum()
        if len(monthly) < 2 or monthly.std(ddof=1) == 0:
            return float("nan")
        return float(monthly.mean() / monthly.std(ddof=1) * np.sqrt(12))

    return _sharpe(is_t), _sharpe(oos_t)


def _daily_sharpe_from_trades(trades: pd.DataFrame, oos_cutoff_ms: int) -> tuple[float, float]:
    """Compute IS and OOS daily Sharpe (annualized) for IS-OOS-daily-ratio falsifier check."""
    if trades.empty:
        return float("nan"), float("nan")
    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.normalize()
    is_mask = trades["close_time"] < oos_cutoff_ms
    is_t = trades[is_mask]
    oos_t = trades[~is_mask]

    def _sharpe(t: pd.DataFrame) -> float:
        if t.empty:
            return float("nan")
        daily = t.groupby("date")["weighted_pnl"].sum()
        if len(daily) < 2 or daily.std(ddof=1) == 0:
            return float("nan")
        return float(daily.mean() / daily.std(ddof=1) * np.sqrt(252))

    return _sharpe(is_t), _sharpe(oos_t)


def _load_trades(report_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load IS+OOS trades. Drop weight_factor=0 rows (BTC-killed/primitive-blocked)."""
    is_t = pd.read_csv(report_dir / "in_sample" / "trades.csv")
    oos_t = pd.read_csv(report_dir / "out_of_sample" / "trades.csv")
    is_t = is_t[is_t["weight_factor"] > 0.0].copy()
    oos_t = oos_t[oos_t["weight_factor"] > 0.0].copy()
    return is_t, oos_t


def _trade_count_count_zero(report_dir: Path) -> tuple[int, int]:
    """Count of weight_factor=0 trades (BTC-killed). Diagnostic only."""
    is_full = pd.read_csv(report_dir / "in_sample" / "trades.csv")
    oos_full = pd.read_csv(report_dir / "out_of_sample" / "trades.csv")
    return int((is_full["weight_factor"] == 0.0).sum()), int((oos_full["weight_factor"] == 0.0).sum())


# ============================================================
# AXIS 1: LDO contribution at iter-v3/051 baseline
# ============================================================


def axis1_ldo_contribution_at_051() -> pd.DataFrame:
    """Quantify LDO PnL share, WR, exit-reason breakdown at iter-v3/051 baseline."""
    print("=" * 70)
    print("[axis 1] LDO contribution at iter-v3/051 baseline")
    print("=" * 70)
    is_t, oos_t = _load_trades(REPORT_051)
    rows = []
    for window, t in [("IS", is_t), ("OOS", oos_t)]:
        ldo = t[t["symbol"] == "LDOUSDT"]
        total = t["weighted_pnl"].sum()
        ldo_wpnl = ldo["weighted_pnl"].sum()
        share = float(ldo_wpnl / total * 100.0) if total != 0.0 else float("nan")
        wr = float((ldo["weighted_pnl"] > 0).mean() * 100.0) if not ldo.empty else float("nan")
        long_n = int((ldo["direction"] == 1).sum())
        short_n = int((ldo["direction"] == -1).sum())
        long_wpnl = float(ldo.loc[ldo["direction"] == 1, "weighted_pnl"].sum())
        short_wpnl = float(ldo.loc[ldo["direction"] == -1, "weighted_pnl"].sum())
        sl_n = int((ldo["exit_reason"] == "stop_loss").sum())
        tp_n = int((ldo["exit_reason"] == "take_profit").sum())
        to_n = int((ldo["exit_reason"] == "timeout").sum())
        eo_n = int((ldo["exit_reason"] == "end_of_data").sum())
        avg_wpnl = float(ldo["weighted_pnl"].mean()) if not ldo.empty else float("nan")
        rows.append({
            "window": window,
            "ldo_trades": int(len(ldo)),
            "ldo_long_n": long_n,
            "ldo_short_n": short_n,
            "ldo_long_wpnl": round(long_wpnl, 4),
            "ldo_short_wpnl": round(short_wpnl, 4),
            "ldo_wpnl_total": round(float(ldo_wpnl), 4),
            "ldo_avg_wpnl_per_trade": round(avg_wpnl, 4),
            "ldo_wr_pct": round(wr, 2),
            "ldo_sl_n": sl_n,
            "ldo_tp_n": tp_n,
            "ldo_timeout_n": to_n,
            "ldo_eod_n": eo_n,
            "bundle_total_wpnl": round(float(total), 4),
            "ldo_pnl_share_pct": round(share, 2),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis1_ldo_contribution_at_051.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 2: 2-sym BCH+TRX counterfactual from /051 trade roster
# ============================================================


def axis2_counterfactual_2sym() -> pd.DataFrame:
    """Drop LDO trades from /051 roster and re-compute IS+OOS aggregate Sharpe.

    Caveat: this is a LOWER BOUND of the multi-seed CONFIRMATION effect because
    Optuna would re-tune on a 2-symbol universe and SHIFT trade rosters, not just
    drop LDO trades. But the counterfactual proves whether LDO drag DOMINATES the
    aggregate metrics (i.e., a clean 2-sym lift > +0.05 IS at single-seed roster
    counterfactual = highly likely PROMISING at multi-seed CONFIRMATION).
    """
    print("=" * 70)
    print("[axis 2] 2-sym BCH+TRX counterfactual from /051 trade roster")
    print("=" * 70)
    is_t, oos_t = _load_trades(REPORT_051)
    is_no_ldo = is_t[is_t["symbol"] != "LDOUSDT"]
    oos_no_ldo = oos_t[oos_t["symbol"] != "LDOUSDT"]

    # Combined (IS+OOS) Sharpe by window
    is_sh_with, oos_sh_with = _monthly_sharpe_from_trades(
        pd.concat([is_t, oos_t], ignore_index=True), OOS_CUTOFF_MS
    )
    is_sh_no, oos_sh_no = _monthly_sharpe_from_trades(
        pd.concat([is_no_ldo, oos_no_ldo], ignore_index=True), OOS_CUTOFF_MS
    )

    # Daily Sharpe (for IS-OOS ratio diagnostics)
    is_dsh_with, oos_dsh_with = _daily_sharpe_from_trades(
        pd.concat([is_t, oos_t], ignore_index=True), OOS_CUTOFF_MS
    )
    is_dsh_no, oos_dsh_no = _daily_sharpe_from_trades(
        pd.concat([is_no_ldo, oos_no_ldo], ignore_index=True), OOS_CUTOFF_MS
    )

    # Per-symbol after LDO removal
    is_bch_wpnl = float(is_no_ldo.loc[is_no_ldo["symbol"] == "BCHUSDT", "weighted_pnl"].sum())
    is_trx_wpnl = float(is_no_ldo.loc[is_no_ldo["symbol"] == "TRXUSDT", "weighted_pnl"].sum())
    oos_bch_wpnl = float(oos_no_ldo.loc[oos_no_ldo["symbol"] == "BCHUSDT", "weighted_pnl"].sum())
    oos_trx_wpnl = float(oos_no_ldo.loc[oos_no_ldo["symbol"] == "TRXUSDT", "weighted_pnl"].sum())

    # Concentration after LDO removal (top-symbol share)
    is_total_no = is_bch_wpnl + is_trx_wpnl
    oos_total_no = oos_bch_wpnl + oos_trx_wpnl
    is_top_conc_no = max(abs(is_bch_wpnl), abs(is_trx_wpnl)) / abs(is_total_no) * 100.0 if is_total_no != 0 else float("nan")
    oos_top_conc_no = max(abs(oos_bch_wpnl), abs(oos_trx_wpnl)) / abs(oos_total_no) * 100.0 if oos_total_no != 0 else float("nan")

    rows = [
        {
            "scenario": "3-sym /051 actual (BCH+LDO+TRX)",
            "is_trades": int(len(is_t)),
            "oos_trades": int(len(oos_t)),
            "is_monthly_sharpe": round(is_sh_with, 4),
            "oos_monthly_sharpe": round(oos_sh_with, 4),
            "is_daily_sharpe": round(is_dsh_with, 4),
            "oos_daily_sharpe": round(oos_dsh_with, 4),
            "is_oos_daily_ratio": round(oos_dsh_with / is_dsh_with, 4) if is_dsh_with > 0 else float("nan"),
            "is_total_wpnl": round(float(is_t["weighted_pnl"].sum()), 4),
            "oos_total_wpnl": round(float(oos_t["weighted_pnl"].sum()), 4),
            "is_bch_wpnl": round(float(is_t.loc[is_t["symbol"] == "BCHUSDT", "weighted_pnl"].sum()), 4),
            "is_trx_wpnl": round(float(is_t.loc[is_t["symbol"] == "TRXUSDT", "weighted_pnl"].sum()), 4),
            "is_ldo_wpnl": round(float(is_t.loc[is_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum()), 4),
            "oos_bch_wpnl": round(float(oos_t.loc[oos_t["symbol"] == "BCHUSDT", "weighted_pnl"].sum()), 4),
            "oos_trx_wpnl": round(float(oos_t.loc[oos_t["symbol"] == "TRXUSDT", "weighted_pnl"].sum()), 4),
            "oos_ldo_wpnl": round(float(oos_t.loc[oos_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum()), 4),
            "is_top_conc_pct": float("nan"),
            "oos_top_conc_pct": float("nan"),
        },
        {
            "scenario": "2-sym counterfactual (drop LDO)",
            "is_trades": int(len(is_no_ldo)),
            "oos_trades": int(len(oos_no_ldo)),
            "is_monthly_sharpe": round(is_sh_no, 4),
            "oos_monthly_sharpe": round(oos_sh_no, 4),
            "is_daily_sharpe": round(is_dsh_no, 4),
            "oos_daily_sharpe": round(oos_dsh_no, 4),
            "is_oos_daily_ratio": round(oos_dsh_no / is_dsh_no, 4) if is_dsh_no > 0 else float("nan"),
            "is_total_wpnl": round(is_total_no, 4),
            "oos_total_wpnl": round(oos_total_no, 4),
            "is_bch_wpnl": round(is_bch_wpnl, 4),
            "is_trx_wpnl": round(is_trx_wpnl, 4),
            "is_ldo_wpnl": 0.0,
            "oos_bch_wpnl": round(oos_bch_wpnl, 4),
            "oos_trx_wpnl": round(oos_trx_wpnl, 4),
            "oos_ldo_wpnl": 0.0,
            "is_top_conc_pct": round(is_top_conc_no, 2),
            "oos_top_conc_pct": round(oos_top_conc_no, 2),
        },
        {
            "scenario": "DELTA (no_LDO - with_LDO)",
            "is_trades": int(len(is_no_ldo)) - int(len(is_t)),
            "oos_trades": int(len(oos_no_ldo)) - int(len(oos_t)),
            "is_monthly_sharpe": round(is_sh_no - is_sh_with, 4),
            "oos_monthly_sharpe": round(oos_sh_no - oos_sh_with, 4),
            "is_daily_sharpe": round(is_dsh_no - is_dsh_with, 4),
            "oos_daily_sharpe": round(oos_dsh_no - oos_dsh_with, 4),
            "is_oos_daily_ratio": float("nan"),
            "is_total_wpnl": round(is_total_no - float(is_t["weighted_pnl"].sum()), 4),
            "oos_total_wpnl": round(oos_total_no - float(oos_t["weighted_pnl"].sum()), 4),
            "is_bch_wpnl": 0.0,
            "is_trx_wpnl": 0.0,
            "is_ldo_wpnl": -round(float(is_t.loc[is_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum()), 4),
            "oos_bch_wpnl": 0.0,
            "oos_trx_wpnl": 0.0,
            "oos_ldo_wpnl": -round(float(oos_t.loc[oos_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum()), 4),
            "is_top_conc_pct": float("nan"),
            "oos_top_conc_pct": float("nan"),
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis2_counterfactual_2sym.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 3: /050 EDA vs /051 supersession check
# ============================================================


def axis3_050_vs_051_supersession() -> pd.DataFrame:
    """Explicit comparison of LDO calculus at /050 config vs /051 config.

    The iter-v3/051 EDA rejected LDO removal on the basis of /050 trade-roster
    IS Δ -0.015 (near-zero IS contribution). The /051 result SUPERSEDES this
    because LDO IS PnL share at the /028-reverted /051 config is -14.96% — a
    clear drag, not near-zero.

    This axis documents the supersession explicitly.
    """
    print("=" * 70)
    print("[axis 3] /050 EDA vs /051 supersession check")
    print("=" * 70)
    rows = []

    # /050 EDA-stage rejection (from analysis/iteration_v3-051/axis_a_ldo_attribution.csv)
    # iter-v3/050 seed=42: LDO IS wpnl +0.85, IS Sharpe Δ +0.0075 (no removal), OOS Sharpe Δ +0.8492 (removed)
    for label, report, comment in [
        ("/050 EDA rejection basis (4-sym + per-sym ATR + primitive 10)",
         REPORT_050,
         "REJECTED: LDO IS contribution +0.85 wpnl near-zero; IS Δ if remove = -0.015 (not improving)"),
        ("/051 NEW evidence (3-sym /028 architecture; default ATR; no primitive 10)",
         REPORT_051,
         "INVESTIGATE: LDO IS PnL share -14.96%; IS Δ if remove = AXIS 2 result (this script)"),
    ]:
        is_t, oos_t = _load_trades(report)
        ldo_is = is_t[is_t["symbol"] == "LDOUSDT"]
        ldo_oos = oos_t[oos_t["symbol"] == "LDOUSDT"]
        is_total = float(is_t["weighted_pnl"].sum())
        oos_total = float(oos_t["weighted_pnl"].sum())
        ldo_is_wpnl = float(ldo_is["weighted_pnl"].sum())
        ldo_oos_wpnl = float(ldo_oos["weighted_pnl"].sum())
        ldo_is_share = ldo_is_wpnl / is_total * 100.0 if is_total != 0 else float("nan")
        ldo_oos_share = ldo_oos_wpnl / oos_total * 100.0 if oos_total != 0 else float("nan")

        # Bundle Sharpe with/without LDO
        is_sh_with, oos_sh_with = _monthly_sharpe_from_trades(
            pd.concat([is_t, oos_t], ignore_index=True), OOS_CUTOFF_MS
        )
        is_no = is_t[is_t["symbol"] != "LDOUSDT"]
        oos_no = oos_t[oos_t["symbol"] != "LDOUSDT"]
        is_sh_no, oos_sh_no = _monthly_sharpe_from_trades(
            pd.concat([is_no, oos_no], ignore_index=True), OOS_CUTOFF_MS
        )

        rows.append({
            "config": label,
            "comment": comment,
            "ldo_is_trades": int(len(ldo_is)),
            "ldo_oos_trades": int(len(ldo_oos)),
            "ldo_is_wr_pct": round(float((ldo_is["weighted_pnl"] > 0).mean() * 100.0) if not ldo_is.empty else float("nan"), 2),
            "ldo_oos_wr_pct": round(float((ldo_oos["weighted_pnl"] > 0).mean() * 100.0) if not ldo_oos.empty else float("nan"), 2),
            "ldo_is_wpnl": round(ldo_is_wpnl, 4),
            "ldo_oos_wpnl": round(ldo_oos_wpnl, 4),
            "ldo_is_share_pct": round(ldo_is_share, 2),
            "ldo_oos_share_pct": round(ldo_oos_share, 2),
            "is_sharpe_with_ldo": round(is_sh_with, 4),
            "is_sharpe_no_ldo": round(is_sh_no, 4),
            "is_sharpe_delta": round(is_sh_no - is_sh_with, 4),
            "oos_sharpe_with_ldo": round(oos_sh_with, 4),
            "oos_sharpe_no_ldo": round(oos_sh_no, 4),
            "oos_sharpe_delta": round(oos_sh_no - oos_sh_with, 4),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis3_050_vs_051_supersession.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 4: Cross-iteration LDO OOS pattern
# ============================================================


def axis4_cross_iteration_ldo() -> pd.DataFrame:
    """LDO OOS pattern across /028/045/047/049/050/051.

    Frozen-baseline pattern: -19.13 OOS wpnl bit-identical at seed 42 across
    /047/049/050. The /051 FULL REVERT to /028 architecture produced -17.44
    OOS — close to the frozen value, with different config layers stripped.

    This axis prints the cross-iteration LDO pattern to demonstrate that LDO
    is structurally bad in v3 architecture independent of customization layer.
    """
    print("=" * 70)
    print("[axis 4] Cross-iteration LDO OOS pattern")
    print("=" * 70)
    rows = []
    for label, report, config in [
        ("iter-v3/028 (3-sym /028 baseline; multi-seed mean)",
         REPORT_028, "3-sym BCH+LDO+TRX; default ATR; no primitive 10; multi-seed"),
        ("iter-v3/045 (4-sym + per-sym ATR; single-seed PROMISING anchor)",
         REPORT_045, "4-sym BCH+LDO+TRX+ALGO; per-sym ATR (LDO 2.0/1.5); no primitive 10"),
        ("iter-v3/047 (4-sym + per-sym ATR + primitive 10; single-seed)",
         REPORT_047, "4-sym; per-sym ATR; primitive 10 = BCH LONG block"),
        ("iter-v3/049 (4-sym + per-sym ATR + primitive 10 + ADX retune; single-seed)",
         REPORT_049, "4-sym; per-sym ATR; primitive 10; ADX retune"),
        ("iter-v3/050 seed=42 (CONFIRMATION; same head as /049)",
         REPORT_050, "Same head as /049; CONFIRMATION-NO-MERGE-revert"),
        ("iter-v3/051 (3-sym FULL REVERT; single-seed EXPLORATION)",
         REPORT_051, "3-sym BCH+LDO+TRX; default ATR; no primitive 10; +fracdiff_d05_close"),
    ]:
        is_t, oos_t = _load_trades(report)
        ldo_is = is_t[is_t["symbol"] == "LDOUSDT"]
        ldo_oos = oos_t[oos_t["symbol"] == "LDOUSDT"]
        rows.append({
            "iteration": label,
            "config": config,
            "ldo_is_trades": int(len(ldo_is)),
            "ldo_oos_trades": int(len(ldo_oos)),
            "ldo_is_wpnl": round(float(ldo_is["weighted_pnl"].sum()), 4),
            "ldo_oos_wpnl": round(float(ldo_oos["weighted_pnl"].sum()), 4),
            "ldo_is_wr_pct": round(float((ldo_is["weighted_pnl"] > 0).mean() * 100.0) if not ldo_is.empty else float("nan"), 2),
            "ldo_oos_wr_pct": round(float((ldo_oos["weighted_pnl"] > 0).mean() * 100.0) if not ldo_oos.empty else float("nan"), 2),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis4_cross_iteration_ldo.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 5: LDO short-history pre-flight check
# ============================================================


def axis5_data_extent() -> pd.DataFrame:
    """Per-symbol kline data extent.

    LDO is a relatively new asset (listed Sep 2022 = ~3980 8h candles vs
    BCH ~6966 / TRX ~6908 — LDO has ~43% less training data). This is
    one structural reason LDO could underperform: fewer training-window
    cells produce noisier per-cell models.
    """
    print("=" * 70)
    print("[axis 5] Per-symbol kline data extent")
    print("=" * 70)
    rows = []
    for sym in ("BCHUSDT", "LDOUSDT", "TRXUSDT"):
        csv = DATA_DIR / sym / "8h.csv"
        df_k = pd.read_csv(csv)
        n_candles = int(len(df_k))
        first_t = int(df_k["open_time"].iloc[0])
        last_t = int(df_k["open_time"].iloc[-1])
        # Convert to UTC dates
        first_date = pd.to_datetime(first_t, unit="ms").strftime("%Y-%m-%d")
        last_date = pd.to_datetime(last_t, unit="ms").strftime("%Y-%m-%d")
        # IS candles (before OOS_CUTOFF_MS) vs OOS candles
        is_candles = int((df_k["close_time"] < OOS_CUTOFF_MS).sum())
        oos_candles = int((df_k["close_time"] >= OOS_CUTOFF_MS).sum())
        rows.append({
            "symbol": sym,
            "n_candles_total": n_candles,
            "first_open": first_date,
            "last_open": last_date,
            "is_candles": is_candles,
            "oos_candles": oos_candles,
            "is_months_approx": round(is_candles * 8 / 24 / 30.4, 1),
            "oos_months_approx": round(oos_candles * 8 / 24 / 30.4, 1),
            "deficit_vs_bch": "n/a" if sym == "BCHUSDT" else f"{round((1 - n_candles / 6966) * 100, 1)}% less",
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis5_data_extent.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 6: LDO directional asymmetry
# ============================================================


def axis6_ldo_directional_asymmetry() -> pd.DataFrame:
    """LDO long-side vs short-side IS+OOS PnL attribution.

    Is the LDO drag concentrated in one direction? If so, a direction-asymmetric
    fix (like primitive 10) MIGHT save LDO without removing it. The /051 result
    needs to be examined: 11 of 13 OOS trades are shorts, with most being SLs.
    A short-only loss pattern in a rising-LDO environment is consistent with
    "model learns to short LDO when it should have been long" (signal flip).

    This axis classifies LDO trades by direction and exit-reason to determine
    the failure mode.
    """
    print("=" * 70)
    print("[axis 6] LDO directional asymmetry at /051 baseline")
    print("=" * 70)
    is_t, oos_t = _load_trades(REPORT_051)
    rows = []
    for window, t in [("IS", is_t), ("OOS", oos_t)]:
        ldo = t[t["symbol"] == "LDOUSDT"].copy()
        for direction, dir_label in [(1, "LONG"), (-1, "SHORT")]:
            sub = ldo[ldo["direction"] == direction]
            if sub.empty:
                rows.append({
                    "window": window,
                    "direction": dir_label,
                    "n_trades": 0,
                    "n_wins": 0,
                    "win_rate_pct": float("nan"),
                    "wpnl_total": 0.0,
                    "avg_wpnl_per_trade": float("nan"),
                    "n_sl": 0, "n_tp": 0, "n_timeout": 0, "n_eod": 0,
                })
                continue
            wins = int((sub["weighted_pnl"] > 0).sum())
            rows.append({
                "window": window,
                "direction": dir_label,
                "n_trades": int(len(sub)),
                "n_wins": wins,
                "win_rate_pct": round(wins / len(sub) * 100.0, 2),
                "wpnl_total": round(float(sub["weighted_pnl"].sum()), 4),
                "avg_wpnl_per_trade": round(float(sub["weighted_pnl"].mean()), 4),
                "n_sl": int((sub["exit_reason"] == "stop_loss").sum()),
                "n_tp": int((sub["exit_reason"] == "take_profit").sum()),
                "n_timeout": int((sub["exit_reason"] == "timeout").sum()),
                "n_eod": int((sub["exit_reason"] == "end_of_data").sum()),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis6_ldo_directional_asymmetry.csv", index=False)
    print(df.to_string(index=False))
    return df


# ============================================================
# AXIS 7: Monthly LDO PnL (extra: temporal pattern)
# ============================================================


def axis7_ldo_monthly_pnl() -> pd.DataFrame:
    """Monthly LDO PnL across IS+OOS to detect regime-specific failure."""
    print("=" * 70)
    print("[axis 7] LDO monthly PnL temporal pattern")
    print("=" * 70)
    is_t, oos_t = _load_trades(REPORT_051)
    all_t = pd.concat([is_t, oos_t], ignore_index=True)
    ldo = all_t[all_t["symbol"] == "LDOUSDT"].copy()
    if ldo.empty:
        return pd.DataFrame()
    ldo["date"] = pd.to_datetime(ldo["close_time"], unit="ms").dt.normalize()
    ldo["month"] = ldo["date"].dt.to_period("M").astype(str)
    ldo["window"] = np.where(ldo["close_time"] < OOS_CUTOFF_MS, "IS", "OOS")
    monthly = ldo.groupby(["month", "window"]).agg(
        n_trades=("weighted_pnl", "count"),
        wpnl=("weighted_pnl", "sum"),
        wins=("weighted_pnl", lambda s: int((s > 0).sum())),
    ).reset_index()
    monthly["wr_pct"] = (monthly["wins"] / monthly["n_trades"] * 100.0).round(2)
    monthly["wpnl"] = monthly["wpnl"].round(4)
    monthly.to_csv(OUT_DIR / "axis7_ldo_monthly_pnl.csv", index=False)
    print(monthly.to_string(index=False))
    return monthly


# ============================================================
# Main
# ============================================================


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    a1 = axis1_ldo_contribution_at_051()
    print()
    a2 = axis2_counterfactual_2sym()
    print()
    a3 = axis3_050_vs_051_supersession()
    print()
    a4 = axis4_cross_iteration_ldo()
    print()
    a5 = axis5_data_extent()
    print()
    a6 = axis6_ldo_directional_asymmetry()
    print()
    a7 = axis7_ldo_monthly_pnl()
    print()

    # Headline summary (printed to stdout for easy capture into synthesis.md)
    print("=" * 70)
    print("[HEADLINE SUMMARY] iter-v3/052 LDO removal investigation")
    print("=" * 70)
    print(f"AXIS 1: LDO IS PnL share = {a1.loc[a1['window'] == 'IS', 'ldo_pnl_share_pct'].iloc[0]:.2f}%")
    print(f"         LDO OOS PnL share = {a1.loc[a1['window'] == 'OOS', 'ldo_pnl_share_pct'].iloc[0]:.2f}%")
    print(f"AXIS 2: 2-sym counterfactual IS Sharpe Δ = {a2.loc[a2['scenario'] == 'DELTA (no_LDO - with_LDO)', 'is_monthly_sharpe'].iloc[0]:+.4f}")
    print(f"         2-sym counterfactual OOS Sharpe Δ = {a2.loc[a2['scenario'] == 'DELTA (no_LDO - with_LDO)', 'oos_monthly_sharpe'].iloc[0]:+.4f}")
    print(f"         2-sym counterfactual top-symbol concentration: IS {a2.loc[a2['scenario'] == '2-sym counterfactual (drop LDO)', 'is_top_conc_pct'].iloc[0]:.2f}% / OOS {a2.loc[a2['scenario'] == '2-sym counterfactual (drop LDO)', 'oos_top_conc_pct'].iloc[0]:.2f}%")
    print(f"AXIS 3: /050 EDA rejection IS Δ = {a3.loc[a3['config'].str.startswith('/050'), 'is_sharpe_delta'].iloc[0]:+.4f} (near-zero)")
    print(f"         /051 NEW evidence IS Δ = {a3.loc[a3['config'].str.startswith('/051'), 'is_sharpe_delta'].iloc[0]:+.4f}")
    print(f"AXIS 5: LDO data extent {a5.loc[a5['symbol'] == 'LDOUSDT', 'n_candles_total'].iloc[0]} candles vs BCH {a5.loc[a5['symbol'] == 'BCHUSDT', 'n_candles_total'].iloc[0]}")
    print(f"AXIS 6: LDO OOS LONG: {a6.loc[(a6['window'] == 'OOS') & (a6['direction'] == 'LONG'), 'n_trades'].iloc[0]}, SHORT: {a6.loc[(a6['window'] == 'OOS') & (a6['direction'] == 'SHORT'), 'n_trades'].iloc[0]}")
    print()


if __name__ == "__main__":
    main()

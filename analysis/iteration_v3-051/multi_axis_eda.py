"""iter-v3/051 — multi-axis EDA for cycle 4 #1 of 10 EXPLORATIONs.

Per `feedback_v3_axis_selection_quant_discipline.md` (established 2026-05-09 at iter-v3/044):
QR must do EDA-driven axis selection BEFORE brief write. Orchestrator suggested 4 candidate
axes (per Critic FINAL `b6339c5` of iter-v3/050 recommendations #2 + #3 + #5):

  (a) LDO removal investigation (LDO -19.13 frozen baseline at seed 42 across /047/049/050)
  (b) Per-symbol customization REVERT (4 sub-axes b1, b2, b3, b4)
  (c) NEW universal engineered features (fracdiff_d05_close universal, hurst_drift_50_200,
      regime_momentum_signed_3d retest at universal scope)
  (d) 3-symbol universe restoration WITHOUT ALGO (test if regime_momentum recovers from
      rank 14/14 to top-rank in 3-symbol BCH+LDO+TRX universe)

Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` SYSTEM-LEVEL CONFIRMED across 2 cycles:
the cycle 4 starting hypothesis must NOT bundle further per-symbol customizations. The
candidates above are ALL structural REVERTs or universal additions / universe restorations.

Inputs:
  - reports-v3/iteration_v3-050/  (current head; 4-sym + per-sym ATR + primitive 10; multi-seed)
  - reports-v3/iteration_v3-049/  (4-sym + per-sym ATR + primitive 10 single-seed)
  - reports-v3/iteration_v3-045/  (4-sym + per-sym ATR; single-seed PROMISING anchor)
  - reports-v3/iteration_v3-028/  (BASELINE_V3.md; 3-sym BCH+LDO+TRX; multi-seed +0.5101 IS)
  - reports-v3/iteration_v3-047/  (4-sym + per-sym ATR + primitive 10 first single-seed)
  - data/features_v3/<SYMBOL>_8h.parquet  (for IC analysis on candidate features)

Outputs:
  - axis_a_ldo_attribution.csv      (LDO IS/OOS PnL across 5 iterations + IS Sharpe contribution)
  - axis_b_subaxis_ranking.csv      (b1, b2, b3, b4 IS Sharpe counterfactuals from /050 trade roster)
  - axis_c_eng_feature_screening.csv (3-5 candidate features: |IC| + ADF + per-symbol description)
  - axis_d_3sym_restoration.csv     (3-sym restoration counterfactual using /050 trade roster)
  - synthesis.md                    (markdown ranking)
  - candidate_axes_ranking.md       (final selected axis + 4 candidates ranked)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_050 = ROOT / "reports-v3" / "iteration_v3-050"
REPORT_049 = ROOT / "reports-v3" / "iteration_v3-049"
REPORT_047 = ROOT / "reports-v3" / "iteration_v3-047"
REPORT_045 = ROOT / "reports-v3" / "iteration_v3-045"
REPORT_028 = ROOT / "reports-v3" / "iteration_v3-028"
FEATURES_DIR = ROOT / "data" / "features_v3"
OUT_DIR = ROOT / "analysis" / "iteration_v3-051"
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")

# Existing 14-feature stack at iter-v3/028 baseline (carry-forward through /050).
EXISTING_14 = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

# ---------- Helpers ----------


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


def _load_trades(report_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load IS+OOS trades. Drop weight_factor=0 rows (BTC-killed/primitive-blocked)."""
    is_t = pd.read_csv(report_dir / "in_sample" / "trades.csv")
    oos_t = pd.read_csv(report_dir / "out_of_sample" / "trades.csv")
    is_t = is_t[is_t["weight_factor"] > 0.0].copy()
    oos_t = oos_t[oos_t["weight_factor"] > 0.0].copy()
    return is_t, oos_t


def _per_sym_sharpe(trades: pd.DataFrame, syms: tuple[str, ...]) -> dict[str, float]:
    """Per-symbol monthly Sharpe contribution (treat each symbol as standalone)."""
    out = {}
    for s in syms:
        t = trades[trades["symbol"] == s]
        if t.empty:
            out[s] = float("nan")
            continue
        t = t.copy()
        t["date"] = pd.to_datetime(t["close_time"], unit="ms").dt.normalize()
        daily = t.groupby("date")["weighted_pnl"].sum().reset_index()
        daily["month"] = daily["date"].dt.to_period("M")
        monthly = daily.groupby("month")["weighted_pnl"].sum()
        if len(monthly) < 2 or monthly.std(ddof=1) == 0:
            out[s] = float("nan")
        else:
            out[s] = float(monthly.mean() / monthly.std(ddof=1) * np.sqrt(12))
    return out


# ---------- Axis A — LDO removal investigation ----------


def axis_a_ldo_attribution() -> pd.DataFrame:
    """Cross-iteration LDO IS/OOS attribution table.

    Tests: would removing LDO from V3_MODELS produce a stronger CONFIRMATION at iter-v3/061?

    Method: for each of 5 reference iterations, compute IS+OOS PnL and IS Sharpe contribution
    of LDO. Then compute counterfactual IS Sharpe and OOS Sharpe with LDO REMOVED (drop all
    LDO trades from daily PnL series).
    """
    print("[axis_a] LDO removal investigation")
    rows = []
    for label, report in [
        ("iter-v3/028 (3-sym baseline; no per-sym ATR)", REPORT_028),
        ("iter-v3/045 (4-sym + per-sym ATR; PROMISING anchor)", REPORT_045),
        ("iter-v3/047 (4-sym + per-sym ATR + primitive 10)", REPORT_047),
        ("iter-v3/049 (4-sym + per-sym ATR + primitive 10 + ADX retune)", REPORT_049),
        ("iter-v3/050 seed=42 (CONFIRMATION; same head as /049)", REPORT_050),
    ]:
        is_t, oos_t = _load_trades(report)
        n_is_ldo = int((is_t["symbol"] == "LDOUSDT").sum())
        n_oos_ldo = int((oos_t["symbol"] == "LDOUSDT").sum())
        is_ldo_pnl = float(is_t.loc[is_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum())
        oos_ldo_pnl = float(oos_t.loc[oos_t["symbol"] == "LDOUSDT", "weighted_pnl"].sum())
        is_ldo_wr = (
            float((is_t.loc[is_t["symbol"] == "LDOUSDT", "weighted_pnl"] > 0).mean()) * 100.0
            if n_is_ldo > 0 else float("nan")
        )
        oos_ldo_wr = (
            float((oos_t.loc[oos_t["symbol"] == "LDOUSDT", "weighted_pnl"] > 0).mean()) * 100.0
            if n_oos_ldo > 0 else float("nan")
        )

        # Bundle Sharpe (with LDO)
        is_sh_with, oos_sh_with = _monthly_sharpe_from_trades(
            pd.concat([is_t, oos_t], ignore_index=True), OOS_CUTOFF_MS
        )

        # Counterfactual: drop all LDO trades from daily PnL aggregation
        is_no_ldo = is_t[is_t["symbol"] != "LDOUSDT"]
        oos_no_ldo = oos_t[oos_t["symbol"] != "LDOUSDT"]
        is_sh_no, oos_sh_no = _monthly_sharpe_from_trades(
            pd.concat([is_no_ldo, oos_no_ldo], ignore_index=True), OOS_CUTOFF_MS
        )

        rows.append({
            "iteration": label,
            "n_is_ldo": n_is_ldo,
            "n_oos_ldo": n_oos_ldo,
            "is_ldo_pnl": round(is_ldo_pnl, 4),
            "oos_ldo_pnl": round(oos_ldo_pnl, 4),
            "is_ldo_wr": round(is_ldo_wr, 2),
            "oos_ldo_wr": round(oos_ldo_wr, 2),
            "is_sharpe_with_ldo": round(is_sh_with, 4),
            "is_sharpe_no_ldo": round(is_sh_no, 4),
            "is_sharpe_delta_no_ldo": round(is_sh_no - is_sh_with, 4),
            "oos_sharpe_with_ldo": round(oos_sh_with, 4),
            "oos_sharpe_no_ldo": round(oos_sh_no, 4),
            "oos_sharpe_delta_no_ldo": round(oos_sh_no - oos_sh_with, 4),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_a_ldo_attribution.csv", index=False)
    print(df.to_string(index=False))
    return df


# ---------- Axis B — Per-symbol customization REVERT (4 sub-axes) ----------


def axis_b_subaxis_ranking() -> pd.DataFrame:
    """4-axis ranking: which sub-piece of the iter-v3/050 bundle drags IS most?

    Sub-axes:
      b1 = LDO removal alone (drop LDO; keep ALGO ATR, primitive 10)
      b2 = per-symbol ATR ALGO+LDO REVERT alone (keep V3_MODELS=4 syms, keep primitive 10)
      b3 = primitive 10 BCH LONG block REVERT alone (keep V3_MODELS=4 syms, keep per-sym ATR)
      b4 = full per-symbol REVERT (drop everything; restore iter-v3/028 architecture exactly)

    NOTE: b2/b3/b4 cannot be precisely simulated from iter-v3/050 trade roster alone — the
    Optuna re-tune cost path is not modelable. The COUNTERFACTUAL we compute here is "what
    IS Sharpe results from the iter-v3/050 trade roster with these bundle ingredients
    REMOVED?" That answer represents a LOWER BOUND on the true Optuna-retune effect because
    Optuna retunes will SHIFT trade rosters, not just drop trades.

    For b1 (LDO removal): can be precisely computed from the trade roster — drop LDO trades
    from the daily PnL aggregation.

    For b2 (per-sym ATR REVERT): trade rosters from iter-v3/045 (which has ALGO+LDO ATR)
    differ from those in iter-v3/050 by Optuna re-tune; using the iter-v3/050 roster as
    proxy for "what would happen if ATR REVERTed" is approximate. We use the iter-v3/028
    baseline as a sample observation of what IS Sharpe looks like at default ATR + 3-sym
    universe.

    For b3 (primitive 10 REVERT): use iter-v3/045 as the proxy (4-sym + per-sym ATR; no
    primitive 10).

    For b4 (full REVERT): use iter-v3/028 baseline as the gold-standard observation.
    """
    print("\n[axis_b] 4-axis ranking: which sub-axis revert lifts IS most?")
    rows = []

    # ----- Axis b0 — current head (iter-v3/050 seed 42 primary projection) -----
    is_t_050, oos_t_050 = _load_trades(REPORT_050)
    is_sh_050, oos_sh_050 = _monthly_sharpe_from_trades(
        pd.concat([is_t_050, oos_t_050], ignore_index=True), OOS_CUTOFF_MS
    )
    n_trades_is_050 = int(is_t_050["weight_factor"].count())
    n_trades_oos_050 = int(oos_t_050["weight_factor"].count())
    rows.append({
        "axis": "b0 — current head (iter-v3/050 seed 42)",
        "is_trades": n_trades_is_050,
        "oos_trades": n_trades_oos_050,
        "is_sharpe": round(is_sh_050, 4),
        "oos_sharpe": round(oos_sh_050, 4),
        "is_delta_vs_028": round(is_sh_050 - 0.5101, 4),
        "oos_delta_vs_028": round(oos_sh_050 - 0.5053, 4),
        "method": "primary projection from /050 (seed 42; bundle assembly: 4-sym + per-sym ATR + primitive 10)",
    })

    # ----- Axis b1 — LDO removal alone -----
    # Drop LDO trades from /050 roster; keep ALGO ATR + primitive 10
    is_b1 = is_t_050[is_t_050["symbol"] != "LDOUSDT"]
    oos_b1 = oos_t_050[oos_t_050["symbol"] != "LDOUSDT"]
    is_sh_b1, oos_sh_b1 = _monthly_sharpe_from_trades(
        pd.concat([is_b1, oos_b1], ignore_index=True), OOS_CUTOFF_MS
    )
    rows.append({
        "axis": "b1 — LDO removal alone (drop LDO; keep ALGO ATR + primitive 10)",
        "is_trades": int(is_b1["weight_factor"].count()),
        "oos_trades": int(oos_b1["weight_factor"].count()),
        "is_sharpe": round(is_sh_b1, 4),
        "oos_sharpe": round(oos_sh_b1, 4),
        "is_delta_vs_028": round(is_sh_b1 - 0.5101, 4),
        "oos_delta_vs_028": round(oos_sh_b1 - 0.5053, 4),
        "method": "PRECISE: drop LDO rows from /050 daily PnL; no Optuna re-tune assumed for non-LDO syms",
    })

    # ----- Axis b2 — per-sym ATR REVERT alone -----
    # No precise simulation possible. Use iter-v3/047 → iter-v3/045 (where /045 was per-sym ATR
    # ON, /047 added primitive 10). But what we want is "/050 with primitive 10 ON but per-sym
    # ATR REVERTed". The closest empirical evidence is the /028 baseline (no per-sym ATR, 3-sym
    # universe). However that's not a fair counterfactual because /028 is 3-sym not 4-sym.
    #
    # Use a hybrid simulator: take /028 BCH+LDO+TRX trades as "default ATR observed Sharpe"
    # then subtract the iter-v3/050 per-symbol ATR effect on the ALGO+LDO subset.
    is_t_028, oos_t_028 = _load_trades(REPORT_028)
    is_sh_028, oos_sh_028 = _monthly_sharpe_from_trades(
        pd.concat([is_t_028, oos_t_028], ignore_index=True), OOS_CUTOFF_MS
    )
    rows.append({
        "axis": "b2 — per-symbol ATR ALGO+LDO REVERT alone (keep 4-sym + primitive 10) [APPROX]",
        "is_trades": -1,  # not precisely simulable
        "oos_trades": -1,
        "is_sharpe": float("nan"),
        "oos_sharpe": float("nan"),
        "is_delta_vs_028": float("nan"),
        "oos_delta_vs_028": float("nan"),
        "method": "NOT PRECISELY SIMULABLE: requires Optuna re-tune. Empirical proxy below.",
    })

    # ----- Axis b3 — primitive 10 REVERT alone -----
    # Use iter-v3/045 as proxy: same 4-sym + per-sym ATR, but no primitive 10.
    is_t_045, oos_t_045 = _load_trades(REPORT_045)
    is_sh_045, oos_sh_045 = _monthly_sharpe_from_trades(
        pd.concat([is_t_045, oos_t_045], ignore_index=True), OOS_CUTOFF_MS
    )
    n_trades_is_045 = int(is_t_045["weight_factor"].count())
    n_trades_oos_045 = int(oos_t_045["weight_factor"].count())
    rows.append({
        "axis": "b3 — primitive 10 REVERT alone (keep 4-sym + per-sym ATR) [PROXY=iter-v3/045]",
        "is_trades": n_trades_is_045,
        "oos_trades": n_trades_oos_045,
        "is_sharpe": round(is_sh_045, 4),
        "oos_sharpe": round(oos_sh_045, 4),
        "is_delta_vs_028": round(is_sh_045 - 0.5101, 4),
        "oos_delta_vs_028": round(oos_sh_045 - 0.5053, 4),
        "method": "PROXY: iter-v3/045 single-seed (4-sym + per-sym ATR; no primitive 10) — different Optuna seed/path",
    })

    # ----- Axis b4 — full per-symbol REVERT -----
    # iter-v3/028 baseline IS the answer: 3-sym BCH+LDO+TRX universe, no per-sym ATR, no
    # primitive 10. This is the MULTI-SEED reference (+0.5101 IS / +0.5053 OOS).
    n_trades_is_028 = int(is_t_028["weight_factor"].count())
    n_trades_oos_028 = int(oos_t_028["weight_factor"].count())
    rows.append({
        "axis": "b4 — full per-symbol REVERT to iter-v3/028 architecture [GOLD STANDARD]",
        "is_trades": n_trades_is_028,
        "oos_trades": n_trades_oos_028,
        "is_sharpe": round(is_sh_028, 4),
        "oos_sharpe": round(oos_sh_028, 4),
        "is_delta_vs_028": 0.0,
        "oos_delta_vs_028": 0.0,
        "method": "GOLD STANDARD: iter-v3/028 multi-seed BASELINE (+0.5101 IS / +0.5053 OOS); not a counterfactual but the actual baseline state",
    })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_b_subaxis_ranking.csv", index=False)
    print(df.to_string(index=False))
    return df


# ---------- Axis C — NEW universal engineered feature screening ----------


def _try_load_features(symbol: str) -> pd.DataFrame | None:
    """Load symbol's features parquet if available."""
    p = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)


def axis_c_eng_feature_screening() -> pd.DataFrame:
    """Screen 3-5 NEW universal engineered feature candidates for cycle 4.

    For each candidate, compute:
    - max |IC_pearson| with existing 14 features (carve-out for Category 2 composed features
      per `feedback_v3_engineered_feature_pivot.md`)
    - Per-symbol presence in feature parquets (must compute or be computable from primitives)
    - ADF stationarity check (sample 1000 random IS rows)

    Candidates per Critic FINAL `b6339c5` recommendation #5 (axis #1 HIGH-priority):
      c1 = fracdiff_d05_close_universal — already computed in features parquets but
           dropped from V3_FEATURE_COLUMNS_TOP_N at /035 (BCH-only via per-sym dict).
           Cycle 4 retest at universal scope (4 symbols).
      c2 = hurst_drift_50_200 — composed: hurst_100 - hurst_200 (signal-strength delta).
           NOT yet implemented; this candidate would require new feature code.
      c3 = regime_momentum_signed_3d — composed: ret_3d × sign(hurst_100 - 0.5).
           Already computed in features parquets (orthogonal time-scale variant).
      c4 = vwap_dev_zscore_30 — composed: zscore of vwap_dev_20 over 30 bars.
           NOT yet implemented; new feature code required.
      c5 = sym_vs_btc_corr_30d — rolling Pearson(sym_ret_8h, btc_ret_8h, window=90 bars).
           NOT yet implemented; new feature code required.

    Strategy: focus on c1 (universal-scope retest) and c3 (regime_momentum_signed_3d retest)
    since they require NO new feature code (parquets already have them or can be computed
    from existing primitives). c2/c4/c5 deferred (would require feature regeneration which
    delays EXPLORATION beyond 2h cap).
    """
    print("\n[axis_c] NEW universal engineered feature screening")

    df_btc = _try_load_features("BTCUSDT")
    rows = []
    candidates = [
        ("fracdiff_d05_close", "Category 2 composed (LdP AFML Ch. 5 FFD; existing in parquets — re-add at universal scope after BCH-only drop at /035)"),
        ("candle_efficiency_20", "Category 1 indicator: |close-open|/range; trend-strength regime signal (orthogonal to ema_spread_atr_20)"),
        ("fracdiff_logclose_dstat", "Category 1 indicator: ADF d-stat for FFD log-price; stationarity quality score"),
        ("fracdiff_logvolume_dstat", "Category 1 indicator: ADF d-stat for FFD log-volume; volume-stationarity score"),
        ("cross_asset_divergence_norm", "Category 2 composed (already-tested, dropped at /027 due to NEGATIVE-SUSPICIOUS-OOS at single-seed); included as comparison-baseline"),
    ]

    for cand, desc in candidates:
        print(f"\n  candidate: {cand}")
        per_sym_max_ic_with_existing: dict[str, float] = {}
        per_sym_avg_value: dict[str, float] = {}
        per_sym_present: dict[str, bool] = {}
        for sym in SYMBOLS:
            df = _try_load_features(sym)
            if df is None or cand not in df.columns:
                per_sym_present[sym] = False
                per_sym_max_ic_with_existing[sym] = float("nan")
                per_sym_avg_value[sym] = float("nan")
                continue
            per_sym_present[sym] = True

            # Restrict to IS window
            df_is = df[df["close_time"] < OOS_CUTOFF_MS].copy()
            df_is = df_is.dropna(subset=[cand])
            if len(df_is) < 100:
                per_sym_max_ic_with_existing[sym] = float("nan")
                per_sym_avg_value[sym] = float("nan")
                continue
            per_sym_avg_value[sym] = float(df_is[cand].mean())
            ics = []
            for f in EXISTING_14:
                if f not in df_is.columns:
                    continue
                v1 = df_is[cand].values
                v2 = df_is[f].values
                mask = ~(np.isnan(v1) | np.isnan(v2))
                if mask.sum() < 100:
                    continue
                ics.append(abs(np.corrcoef(v1[mask], v2[mask])[0, 1]))
            per_sym_max_ic_with_existing[sym] = max(ics) if ics else float("nan")

        rows.append({
            "candidate": cand,
            "description": desc,
            "BCH_present": per_sym_present.get("BCHUSDT"),
            "LDO_present": per_sym_present.get("LDOUSDT"),
            "TRX_present": per_sym_present.get("TRXUSDT"),
            "ALGO_present": per_sym_present.get("ALGOUSDT"),
            "BCH_max_ic_existing14": round(per_sym_max_ic_with_existing.get("BCHUSDT", float("nan")), 4),
            "LDO_max_ic_existing14": round(per_sym_max_ic_with_existing.get("LDOUSDT", float("nan")), 4),
            "TRX_max_ic_existing14": round(per_sym_max_ic_with_existing.get("TRXUSDT", float("nan")), 4),
            "ALGO_max_ic_existing14": round(per_sym_max_ic_with_existing.get("ALGOUSDT", float("nan")), 4),
            "max_ic_overall": round(
                max([v for v in per_sym_max_ic_with_existing.values() if not np.isnan(v)] or [float("nan")]),
                4,
            ),
            "ic_carve_out_eligible": "YES (Category 2 composed)",
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_c_eng_feature_screening.csv", index=False)
    print(df.to_string(index=False))
    return df


# ---------- Axis D — 3-symbol universe restoration WITHOUT ALGO ----------


def axis_d_3sym_restoration() -> pd.DataFrame:
    """3-symbol BCH+LDO+TRX restoration: drop ALGO from /045 + /050 trade rosters.

    Hypothesis: regime_momentum_signed_5d's rank-14/14 in /050 may be due to ALGO universe
    inclusion diluting its signal. Test by computing IS Sharpe of the bundle WITHOUT ALGO.

    Note: this is the OPPOSITE of axis b1 (LDO removal). Axis d removes ALGO instead. The
    iter-v3/028 BASELINE was 3-sym BCH+LDO+TRX (no ALGO), so this is essentially asking
    "what does iter-v3/050's bundle look like if we remove the ALGO addition?"
    """
    print("\n[axis_d] 3-symbol universe restoration WITHOUT ALGO")
    rows = []
    for label, report in [
        ("iter-v3/028 BASELINE (3-sym; no per-sym ATR; no primitive 10)", REPORT_028),
        ("iter-v3/045 (4-sym + per-sym ATR)", REPORT_045),
        ("iter-v3/050 seed=42 (4-sym + per-sym ATR + primitive 10)", REPORT_050),
    ]:
        is_t, oos_t = _load_trades(report)

        # 4-sym (with ALGO) Sharpe (or 3-sym for iter-v3/028)
        is_sh_with_algo, oos_sh_with_algo = _monthly_sharpe_from_trades(
            pd.concat([is_t, oos_t], ignore_index=True), OOS_CUTOFF_MS
        )

        # Drop ALGO trades; recompute Sharpe
        is_no_algo = is_t[is_t["symbol"] != "ALGOUSDT"]
        oos_no_algo = oos_t[oos_t["symbol"] != "ALGOUSDT"]
        is_sh_no_algo, oos_sh_no_algo = _monthly_sharpe_from_trades(
            pd.concat([is_no_algo, oos_no_algo], ignore_index=True), OOS_CUTOFF_MS
        )

        n_is_algo = int((is_t["symbol"] == "ALGOUSDT").sum())
        n_oos_algo = int((oos_t["symbol"] == "ALGOUSDT").sum())
        is_algo_pnl = float(is_t.loc[is_t["symbol"] == "ALGOUSDT", "weighted_pnl"].sum())
        oos_algo_pnl = float(oos_t.loc[oos_t["symbol"] == "ALGOUSDT", "weighted_pnl"].sum())

        rows.append({
            "iteration": label,
            "n_is_algo": n_is_algo,
            "n_oos_algo": n_oos_algo,
            "is_algo_pnl": round(is_algo_pnl, 4),
            "oos_algo_pnl": round(oos_algo_pnl, 4),
            "is_sharpe_with_algo": round(is_sh_with_algo, 4),
            "is_sharpe_no_algo": round(is_sh_no_algo, 4),
            "is_sharpe_delta_no_algo": round(is_sh_no_algo - is_sh_with_algo, 4),
            "oos_sharpe_with_algo": round(oos_sh_with_algo, 4),
            "oos_sharpe_no_algo": round(oos_sh_no_algo, 4),
            "oos_sharpe_delta_no_algo": round(oos_sh_no_algo - oos_sh_with_algo, 4),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_d_3sym_restoration.csv", index=False)
    print(df.to_string(index=False))
    return df


# ---------- regime_momentum importance investigation ----------


def regime_momentum_importance_investigation() -> pd.DataFrame:
    """Compare regime_momentum_signed_5d importance across iter-v3/028 (3-sym; rank?) vs
    iter-v3/050 (4-sym; rank 14/14 portfolio).

    Per /050 diary: regime_momentum_signed_5d ranks 14/14 portfolio AND 14/14 LDO at /050.
    At /028 (its first multi-seed CONFIRMATION-MERGE) it carried IS lift +0.13. Investigate
    whether ALGO universe inclusion dilutes its signal.
    """
    print("\n[importance] regime_momentum_signed_5d importance: /028 vs /050")
    rows = []
    for label, report in [("iter-v3/028 (3-sym)", REPORT_028), ("iter-v3/050 (4-sym; seed 42)", REPORT_050)]:
        portfolio_csv = report / "in_sample" / "model_importance_last_month_portfolio.csv"
        if not portfolio_csv.exists():
            print(f"  {label}: MISSING {portfolio_csv}")
            continue
        df = pd.read_csv(portfolio_csv)
        # Find regime_momentum_signed_5d row
        if "feature" in df.columns:
            feat_col = "feature"
        elif df.columns[0] == "Unnamed: 0":
            feat_col = "Unnamed: 0"
        else:
            feat_col = df.columns[0]
        rm_rows = df[df[feat_col] == "regime_momentum_signed_5d"]
        if rm_rows.empty:
            print(f"  {label}: regime_momentum_signed_5d not found")
            continue
        # Rank within importance (ascending = highest importance = rank 1)
        df_sorted = df.sort_values(by="importance" if "importance" in df.columns else df.columns[1], ascending=False).reset_index(drop=True)
        rank = int(df_sorted[df_sorted[feat_col] == "regime_momentum_signed_5d"].index[0]) + 1
        n_total = len(df_sorted)
        importance = float(rm_rows.iloc[0]["importance"] if "importance" in rm_rows.columns else rm_rows.iloc[0, 1])
        top_importance = float(df_sorted.iloc[0]["importance"] if "importance" in df_sorted.columns else df_sorted.iloc[0, 1])
        rows.append({
            "iteration": label,
            "rank": rank,
            "n_total_features": n_total,
            "importance": round(importance, 1),
            "top_importance": round(top_importance, 1),
            "importance_pct_of_top": round(100.0 * importance / top_importance, 2) if top_importance > 0 else float("nan"),
        })

    # Per-symbol importance at iter-v3/050
    print(f"\n  iter-v3/050 per-symbol regime_momentum_signed_5d ranks:")
    for sym in SYMBOLS:
        per_sym_csv = REPORT_050 / "in_sample" / f"model_importance_last_month_{sym}.csv"
        if not per_sym_csv.exists():
            continue
        df = pd.read_csv(per_sym_csv)
        feat_col = "feature" if "feature" in df.columns else df.columns[0]
        df_sorted = df.sort_values(by="importance" if "importance" in df.columns else df.columns[1], ascending=False).reset_index(drop=True)
        rm_rows = df_sorted[df_sorted[feat_col] == "regime_momentum_signed_5d"]
        if rm_rows.empty:
            continue
        rank = int(rm_rows.index[0]) + 1
        n_total = len(df_sorted)
        importance = float(rm_rows.iloc[0]["importance"] if "importance" in rm_rows.columns else rm_rows.iloc[0, 1])
        top_importance = float(df_sorted.iloc[0]["importance"] if "importance" in df_sorted.columns else df_sorted.iloc[0, 1])
        rows.append({
            "iteration": f"iter-v3/050 {sym}",
            "rank": rank,
            "n_total_features": n_total,
            "importance": round(importance, 1),
            "top_importance": round(top_importance, 1),
            "importance_pct_of_top": round(100.0 * importance / top_importance, 2) if top_importance > 0 else float("nan"),
        })

    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT_DIR / "regime_momentum_importance.csv", index=False)
    print(df_out.to_string(index=False))
    return df_out


# ---------- Driver ----------


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {OUT_DIR}")
    print(f"OOS cutoff: 2025-03-24 (ms={OOS_CUTOFF_MS})\n")

    df_a = axis_a_ldo_attribution()
    df_b = axis_b_subaxis_ranking()
    df_c = axis_c_eng_feature_screening()
    df_d = axis_d_3sym_restoration()
    df_imp = regime_momentum_importance_investigation()

    # Quick summary
    print("\n" + "=" * 80)
    print("EDA SUMMARY (see synthesis.md for full ranking)")
    print("=" * 80)
    print(f"\nAxis A — LDO removal: see axis_a_ldo_attribution.csv ({len(df_a)} iterations)")
    print(f"Axis B — sub-axis ranking: see axis_b_subaxis_ranking.csv ({len(df_b)} sub-axes)")
    print(f"Axis C — eng feature screening: see axis_c_eng_feature_screening.csv ({len(df_c)} candidates)")
    print(f"Axis D — 3-sym restoration: see axis_d_3sym_restoration.csv ({len(df_d)} iterations)")
    print(f"regime_momentum importance: see regime_momentum_importance.csv ({len(df_imp)} cells)")


if __name__ == "__main__":
    main()

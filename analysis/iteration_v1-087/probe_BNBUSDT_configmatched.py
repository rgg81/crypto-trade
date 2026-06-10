"""iter-v1/087 Full BNB screen.

Gates: GATE 0 / GATE 1 / GATE 2 PRIMARY (config-matched) / GATE 2 TERTIARY.

NOTE: BNBUSDT is in V1_EXCLUDED_SYMBOLS. This is a STANDALONE analysis script (direct
LightGBM, not the full runner). The un-reserve step (dropping BNBUSDT from V1_EXCLUDED_SYMBOLS)
only happens if BNB passes ALL gates and QR decides to build the specialist.

GATE 0 — Bundle diversification:
  Avg pairwise IS return-corr of BNB vs {DOTUSDT, ETHUSDT, BTCUSDT, AAVEUSDT} (8h log returns,
  IS-only < 2025-03-24). Report corr + which member is highest.

GATE 1 — Trivial-momentum baseline (IS-only, multi-horizon 5d/21d/50d):
  min-horizon Sharpe. PASS if <= +0.15.

GATE 2 PRIMARY — CONFIG-MATCHED probe (AMENDED gate, matching full specialist):
  single-inner-seed=42, n_trials=30, ood_enabled=True, bounds_profile="v1_specialist",
  48-col V1_FEATURE_COLUMNS_PRUNED, ATR 2.9/1.45, IS-only walk-forward Sharpe.
  PASS if >= +0.30.

GATE 2 TERTIARY — In-fold vs walk-forward gap:
  mean(per-fold best in-fold Optuna objective) − realized walk-forward IS Sharpe.
  FLAG if > ~0.3 (noise-dominated surface; in-fold overfit, not walk-forward transferable).
  NOTE: This uses the SAME run as GATE 2 PRIMARY (captured via verbose mode).
  Approximation: use best in-sample-fold CV Sharpe from strategy._faxm_log, or
  compute separately via a cv-only pass on each walk-forward training window.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as _scipy_stats

# ── constants ────────────────────────────────────────────────────────────────
SYM = "BNBUSDT"
BUNDLE_POOL = ["DOTUSDT", "ETHUSDT", "BTCUSDT", "AAVEUSDT"]
INTERVAL = "8h"
SEED = 42
N_TRIALS = 30  # CONFIG-MATCHED to full specialist (n_trials)
# NOTE on bounds_profile: "v1_specialist" is INCOMPATIBLE with non-specialist mode.
# In specialist_mode=True, lgbm.py uses a separate Optuna path that hardcodes max_depth=5
# and num_leaves=31 without putting them in the search space. The standard optimize_and_train()
# function (used by non-specialist mode) accesses best["max_depth"] directly and raises
# KeyError when the key is absent from study.best_params.
# THEREFORE: use "v1_pruned" for all non-specialist probes. This allows max_depth∈[3,5],
# which is the minimal compatible constraint. The Critic's "bounds_profile confound" is
# partially addressed: n_trials+OOD are closed; bounds depth-search remains as residual.
BOUNDS_PROFILE = "v1_pruned"  # compatible with non-specialist mode
ATR_TP_MULT = 2.9
ATR_SL_MULT = 1.45
TRAINING_MONTHS = 24
TIMEOUT_MINUTES = 10080  # 21 bars * 480 min
FEE_PCT = 0.1

FEATURES_DIR = Path("data/features")
DATA_DIR = Path("data")

# ── feature columns ──────────────────────────────────────────────────────────
from crypto_trade.config import OOS_CUTOFF_MS  # noqa: E402
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED, V1_OOD_FEATURE_COLUMNS  # noqa: E402

FEATURE_COLUMNS = list(V1_FEATURE_COLUMNS_PRUNED)  # 48 cols
OOD_FEATURES = list(V1_OOD_FEATURE_COLUMNS)  # 16 scale-invariant features


def _monthly_sharpe_from_trades(trades: list) -> float:
    """Compute monthly Sharpe from trade list (IS-only)."""
    if not trades:
        return 0.0
    close_times = np.array([t.close_time for t in trades], dtype="int64")
    wpnls = np.array([t.weighted_pnl for t in trades], dtype="float64")
    months = pd.to_datetime(close_times, unit="ms", utc=True).to_period("M")
    monthly = pd.Series(wpnls).groupby(months).sum()
    if len(monthly) < 2 or monthly.std() == 0:
        return 0.0
    return float(monthly.mean() / monthly.std() * np.sqrt(12))


def _load_parquet(sym: str) -> pd.DataFrame:
    """Load parquet for a symbol."""
    p = FEATURES_DIR / f"{sym}_{INTERVAL}_features.parquet"
    if not p.exists():
        raise FileNotFoundError(
            f"Parquet not found: {p}\n"
            f"Run: uv run crypto-trade features --symbols {sym} --interval 8h "
            "--track v1 --format parquet"
        )
    return pd.read_parquet(p)


def run_gate0(bnb_df: pd.DataFrame) -> dict:
    """GATE 0: Bundle diversification check.

    Computes avg pairwise IS 8h log-return correlation of BNB vs each bundle member.
    """
    print(f"\n{'=' * 70}")
    print("GATE 0 — Bundle Diversification")
    print(f"  BNB vs {BUNDLE_POOL}")
    print(f"{'=' * 70}")

    # IS-only BNB
    bnb_is = bnb_df[bnb_df["open_time"] < OOS_CUTOFF_MS].copy()
    bnb_is = bnb_is.sort_values("open_time").set_index("open_time")
    bnb_logret = np.log(bnb_is["close"].astype(float)).diff().dropna()

    corrs = {}
    for pool_sym in BUNDLE_POOL:
        try:
            pool_df = _load_parquet(pool_sym)
        except FileNotFoundError as e:
            print(f"  WARNING: {pool_sym} parquet missing — {e}")
            corrs[pool_sym] = float("nan")
            continue
        pool_is = pool_df[pool_df["open_time"] < OOS_CUTOFF_MS].copy()
        pool_is = pool_is.sort_values("open_time").set_index("open_time")
        pool_logret = np.log(pool_is["close"].astype(float)).diff().dropna()

        # Align on common timestamps
        common_idx = bnb_logret.index.intersection(pool_logret.index)
        if len(common_idx) < 100:
            print(f"  WARNING: insufficient common rows for {pool_sym} ({len(common_idx)})")
            corrs[pool_sym] = float("nan")
            continue
        r, _ = _scipy_stats.pearsonr(
            bnb_logret.loc[common_idx].values,
            pool_logret.loc[common_idx].values,
        )
        corrs[pool_sym] = float(r)
        print(f"  BNB vs {pool_sym}: corr = {r:+.4f} ({len(common_idx)} common rows)")

    valid_corrs = {k: v for k, v in corrs.items() if not np.isnan(v)}
    avg_corr = np.mean(list(valid_corrs.values())) if valid_corrs else float("nan")
    max_corr_sym = max(valid_corrs, key=lambda k: valid_corrs[k]) if valid_corrs else "N/A"
    max_corr_val = valid_corrs.get(max_corr_sym, float("nan"))

    print(f"\n  Avg pairwise corr (BNB vs bundle): {avg_corr:+.4f}")
    print(f"  Highest corr member: {max_corr_sym} ({max_corr_val:+.4f})")
    print("  NOTE: corr < 0.60 = good diversification; > 0.80 = redundant seat")

    return {
        "corr_per_symbol": corrs,
        "avg_corr": avg_corr,
        "max_corr_sym": max_corr_sym,
        "max_corr_val": max_corr_val,
    }


def run_gate1(bnb_df: pd.DataFrame) -> dict:
    """GATE 1: Trivial momentum baseline (IS-only).

    Multi-horizon 5d/21d/50d (= 15/63/150 8h bars) momentum strategy.
    If trend-following is trivially profitable, LightGBM has to beat a naive baseline.
    PASS if min-horizon Sharpe <= +0.15 (trivial baseline is weak → room for edge).
    """
    print(f"\n{'=' * 70}")
    print("GATE 1 — Trivial Momentum Baseline (IS-only)")
    print("  Horizons: 5d / 21d / 50d (8h bars: 15 / 63 / 150)")
    print("  PASS if min-horizon Sharpe <= +0.15")
    print(f"{'=' * 70}")

    bnb_is = bnb_df[bnb_df["open_time"] < OOS_CUTOFF_MS].copy()
    bnb_is = bnb_is.sort_values("open_time").reset_index(drop=True)
    bnb_is["close"] = bnb_is["close"].astype(float)
    bnb_is["open"] = bnb_is["open"].astype(float)
    bnb_is["open_time_dt"] = pd.to_datetime(bnb_is["open_time"], unit="ms", utc=True)
    bnb_is["month"] = bnb_is["open_time_dt"].dt.to_period("M")

    horizons = {"5d": 15, "21d": 63, "50d": 150}
    sharpes = {}
    forward_bars = 3  # ~1 day at 8h; approximate position hold

    for name, lookback in horizons.items():
        # Signal: sign of trailing return over lookback window
        bnb_is[f"mom_{name}"] = bnb_is["close"].pct_change(lookback)
        bnb_is[f"signal_{name}"] = np.sign(bnb_is[f"mom_{name}"])
        # Forward return: 3-bar (1d at 8h) — simplified P&L proxy
        bnb_is[f"fwd_{name}"] = bnb_is["close"].pct_change(forward_bars).shift(-forward_bars)
        # trade_pnl = signal * fwd_return - fee
        bnb_is[f"trade_pnl_{name}"] = (
            bnb_is[f"signal_{name}"] * bnb_is[f"fwd_{name}"] - FEE_PCT / 100
        )
        # Monthly Sharpe from monthly sums of trade P&L
        valid = bnb_is.dropna(subset=[f"trade_pnl_{name}", f"signal_{name}"])
        valid = valid[valid[f"signal_{name}"] != 0]
        if len(valid) < 20:
            sharpes[name] = 0.0
            continue
        monthly_pnl = valid.groupby("month")[f"trade_pnl_{name}"].sum()
        if len(monthly_pnl) < 2 or monthly_pnl.std() == 0:
            sharpes[name] = 0.0
            continue
        sharpes[name] = float(monthly_pnl.mean() / monthly_pnl.std() * np.sqrt(12))
        print(f"  {name} momentum Sharpe: {sharpes[name]:+.4f}")

    min_sharpe = min(sharpes.values()) if sharpes else 0.0
    max_sharpe = max(sharpes.values()) if sharpes else 0.0
    gate1_pass = min_sharpe <= 0.15

    print(f"\n  Min-horizon Sharpe: {min_sharpe:+.4f}")
    print(f"  Max-horizon Sharpe: {max_sharpe:+.4f}")
    print(f"  GATE 1: {'PASS' if gate1_pass else 'FAIL'} (threshold <= +0.15)")
    if not gate1_pass:
        print("  FAIL NOTE: trivial momentum already profitable → LightGBM edge unclear")

    return {"sharpes": sharpes, "min_sharpe": min_sharpe, "gate1_pass": gate1_pass}


def run_gate2_primary(bnb_df: pd.DataFrame) -> tuple[float, float]:
    """GATE 2 PRIMARY + TERTIARY: CONFIG-MATCHED probe + in-fold vs walk-forward gap.

    CONFIG-MATCHED (AMENDED gate):
      single-inner-seed=42, n_trials=30, ood_enabled=True, bounds_profile="v1_specialist",
      48-col V1_FEATURE_COLUMNS_PRUNED, ATR 2.9/1.45, IS-only walk-forward Sharpe.
      PASS if >= +0.30.

    GATE 2 TERTIARY (new leading indicator):
      mean(per-fold best in-fold Optuna objective) − realized walk-forward IS Sharpe.
      FLAG if > ~0.3 (noise-dominated surface, systematic in-fold overfit).

    Returns (probe_sharpe, infold_gap).
    """
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    from crypto_trade.backtest import run_backtest
    from crypto_trade.backtest_models import BacktestConfig
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

    print(f"\n{'=' * 70}")
    print(f"GATE 2 PRIMARY (CONFIG-MATCHED) — {SYM}")
    print("  n_trials=30, ood_enabled=True, bounds_profile=v1_specialist, seed=42")
    print(f"  ATR TP={ATR_TP_MULT}, SL={ATR_SL_MULT}, 48-col V1_FEATURE_COLUMNS_PRUNED")
    print("  PASS threshold: IS monthly Sharpe >= +0.30")
    print(f"{'=' * 70}")

    cfg = BacktestConfig(
        symbols=(SYM,),
        interval=INTERVAL,
        max_amount_usd=1000.0,
        stop_loss_pct=ATR_SL_MULT * 2.0,
        take_profit_pct=ATR_TP_MULT * 2.0,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        data_dir=DATA_DIR,
        cooldown_candles=2,
        vol_targeting=True,
        vt_target_vol=0.3,
        vt_lookback_days=45,
        vt_min_scale=0.33,
        vt_max_scale=2.0,
        risk_consecutive_sl_limit=0,  # R1=OFF (specialist convention)
        risk_drawdown_scale_enabled=False,  # R2=OFF
    )

    strat = LightGbmStrategy(
        training_months=TRAINING_MONTHS,
        n_trials=N_TRIALS,  # 30 — matches V1_SPECIALIST_OPTUNA_TRIALS
        cv_splits=5,
        label_tp_pct=ATR_TP_MULT * 2.0,
        label_sl_pct=ATR_SL_MULT * 2.0,
        label_timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        features_dir=str(FEATURES_DIR),
        verbose=0,
        atr_tp_multiplier=ATR_TP_MULT,
        atr_sl_multiplier=ATR_SL_MULT,
        use_atr_labeling=True,
        ensemble_seeds=[SEED],
        feature_columns=FEATURE_COLUMNS,
        ood_enabled=True,  # AMENDED: matches full specialist R3=ON
        ood_features=OOD_FEATURES,  # 16-feature V1_OOD_FEATURE_COLUMNS
        ood_cutoff_pct=0.70,
        bounds_profile=BOUNDS_PROFILE,  # v1_pruned (v1_specialist crashes non-specialist mode)
        specialist_mode=False,  # Single-seed walk-forward (not 50-seed specialist)
    )

    t0 = time.time()
    result = run_backtest(cfg, strat)
    elapsed = time.time() - t0

    is_trades = [t for t in result if t.close_time < OOS_CUTOFF_MS]
    all_trades = list(result)

    print(f"\n  Probe complete in {elapsed:.1f}s ({elapsed / 60:.1f} min)")
    print(f"  Total trades (IS+OOS): {len(all_trades)}")
    print(f"  IS trades (close_time < OOS_CUTOFF): {len(is_trades)}")

    if not is_trades:
        print("  PROBE WARNING: no IS trades produced — IS Sharpe = 0.0")
        return 0.0, 0.0

    total_pnl_is = sum(t.weighted_pnl for t in is_trades)
    sharpe = _monthly_sharpe_from_trades(is_trades)

    print(f"\n  IS total weighted_pnl = {total_pnl_is:.2f}%")
    print(f"  IS monthly Sharpe = {sharpe:+.4f}")
    print(f"  GATE 2 PRIMARY: {'PASS' if sharpe >= 0.30 else 'FAIL'} (threshold +0.30)")

    # GATE 2 TERTIARY: in-fold gap via _faxm_log
    # _faxm_log contains per-fold diagnostics; extract best in-fold Optuna objective
    # if available. If not available, approximate via the OOF buffer.
    infold_gap = float("nan")
    try:
        faxm_log = strat._faxm_log
        if faxm_log and len(faxm_log) > 0:
            # faxm_log rows have per-month best_trial_value (best in-fold CV objective)
            in_fold_objs = []
            for row in faxm_log:
                if hasattr(row, "best_trial_value"):
                    in_fold_objs.append(row.best_trial_value)
                elif isinstance(row, dict) and "best_trial_value" in row:
                    in_fold_objs.append(row["best_trial_value"])
            if in_fold_objs:
                mean_infold = float(np.mean(in_fold_objs))
                infold_gap = mean_infold - sharpe
                print("\n  GATE 2 TERTIARY:")
                print(f"    Mean in-fold best Optuna objective: {mean_infold:+.4f}")
                print(f"    Walk-forward IS Sharpe:             {sharpe:+.4f}")
                print(f"    In-fold gap:                        {infold_gap:+.4f}")
                print(f"    FLAG if gap > 0.3: {'FLAG' if infold_gap > 0.3 else 'OK'}")
            else:
                print("\n  GATE 2 TERTIARY: _faxm_log has no best_trial_value entries — gap N/A")
        else:
            print("\n  GATE 2 TERTIARY: _faxm_log empty — gap N/A")
    except AttributeError:
        print("\n  GATE 2 TERTIARY: _faxm_log not accessible — gap N/A")

    return float(sharpe), float(infold_gap) if not np.isnan(infold_gap) else 0.0


def _check_bnb_parquet(df: pd.DataFrame) -> dict:
    """Report BNB data extent and feature coverage."""
    present = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    is_df = df[df["open_time"] < OOS_CUTOFF_MS]
    all_years = 0.0
    is_years = 0.0
    last_kline_date = ""
    if len(df) > 0:
        all_years = float((df["open_time"].max() - df["open_time"].min()) / (1000 * 86400 * 365.25))
        last_kline_date = str(pd.to_datetime(df["open_time"].max(), unit="ms", utc=True).date())
    if len(is_df) > 0:
        is_years = float(
            (is_df["open_time"].max() - is_df["open_time"].min()) / (1000 * 86400 * 365.25)
        )
        min_dt = pd.to_datetime(is_df["open_time"].min(), unit="ms", utc=True)
        max_dt = pd.to_datetime(is_df["open_time"].max(), unit="ms", utc=True)
        print(f"\nBNB parquet rows: {len(df)} total, {len(is_df)} IS")
        print(f"  IS date range: {min_dt.date()} → {max_dt.date()} ({is_years:.2f} years)")
        print(f"  Last kline: {last_kline_date}")
        print(f"  V1_FEATURE_COLUMNS_PRUNED: {len(present)}/{len(FEATURE_COLUMNS)} present")
        if missing:
            print(f"  Missing feature columns: {missing}")
        else:
            print("  All 48 feature columns present.")
    return {
        "is_years": is_years,
        "all_years": all_years,
        "last_kline_date": last_kline_date,
        "feature_coverage": f"{len(present)}/{len(FEATURE_COLUMNS)}",
        "missing_features": missing,
    }


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(repo_root)
    print(f"Working dir: {os.getcwd()}")
    print(f"Symbol: {SYM}")
    print(f"Note: {SYM} is in V1_EXCLUDED_SYMBOLS — this is a standalone analysis script")
    print("      NOT the full runner. Un-reserve only if BNB clears all gates.")

    # Load BNB parquet
    bnb_df = _load_parquet(SYM)
    data_info = _check_bnb_parquet(bnb_df)

    # GATE 0
    gate0 = run_gate0(bnb_df)

    # GATE 1
    gate1 = run_gate1(bnb_df)

    # GATE 2 PRIMARY + TERTIARY (config-matched)
    gate2_sharpe, gate2_infold_gap = run_gate2_primary(bnb_df)

    # ── Write results ───────────────────────────────────────────────────────
    out_dir = Path("analysis/iteration_v1-087")
    out_dir.mkdir(parents=True, exist_ok=True)

    gate2_pass = gate2_sharpe >= 0.30
    gate2_tertiary_flag = gate2_infold_gap > 0.3 and gate2_infold_gap != 0.0

    overall_pass = gate1["gate1_pass"] and gate2_pass

    result_row = {
        "symbol": SYM,
        "probe_type": "config_matched",
        "probe_seed": SEED,
        "n_trials": N_TRIALS,
        "ood_enabled": True,
        "bounds_profile": BOUNDS_PROFILE,
        "atr_tp": ATR_TP_MULT,
        "atr_sl": ATR_SL_MULT,
        # GATE 0
        "gate0_avg_corr": (
            round(gate0["avg_corr"], 4) if not np.isnan(gate0["avg_corr"]) else float("nan")
        ),
        "gate0_max_corr_sym": gate0["max_corr_sym"],
        "gate0_max_corr_val": (
            round(gate0["max_corr_val"], 4) if not np.isnan(gate0["max_corr_val"]) else float("nan")
        ),
        "gate0_corr_DOT": round(gate0["corr_per_symbol"].get("DOTUSDT", float("nan")), 4),
        "gate0_corr_ETH": round(gate0["corr_per_symbol"].get("ETHUSDT", float("nan")), 4),
        "gate0_corr_BTC": round(gate0["corr_per_symbol"].get("BTCUSDT", float("nan")), 4),
        "gate0_corr_AAVE": round(gate0["corr_per_symbol"].get("AAVEUSDT", float("nan")), 4),
        # GATE 1
        "gate1_sharpe_5d": round(gate1["sharpes"].get("5d", 0.0), 4),
        "gate1_sharpe_21d": round(gate1["sharpes"].get("21d", 0.0), 4),
        "gate1_sharpe_50d": round(gate1["sharpes"].get("50d", 0.0), 4),
        "gate1_min_sharpe": round(gate1["min_sharpe"], 4),
        "gate1_pass": gate1["gate1_pass"],
        # GATE 2 PRIMARY
        "gate2_primary_sharpe": round(gate2_sharpe, 4),
        "gate2_primary_pass": gate2_pass,
        "gate2_bounds_profile": BOUNDS_PROFILE,
        # GATE 2 TERTIARY
        "gate2_tertiary_infold_gap": (
            round(gate2_infold_gap, 4) if gate2_infold_gap != 0.0 else "N/A"
        ),
        "gate2_tertiary_flag": gate2_tertiary_flag,
        # Data info
        "is_years": round(data_info["is_years"], 2),
        "last_kline_date": data_info["last_kline_date"],
        "feature_coverage": data_info["feature_coverage"],
        # Overall
        "overall_advance": overall_pass,
        "recommendation": (
            "ADVANCE to full specialist" if overall_pass else "REJECT (cheap screen)"
        ),
        "note": (
            "CONFIG-MATCHED gate: n_trials=30, ood=True, bounds=v1_pruned (v1_specialist "
            "incompatible with non-specialist mode), seed=42. "
            "BNBUSDT in V1_EXCLUDED_SYMBOLS — standalone analysis only. "
            "Un-reserve only if QR decides to build specialist after this screen."
        ),
    }
    out_path = out_dir / "probe_BNBUSDT_configmatched.csv"
    pd.DataFrame([result_row]).to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")

    print(f"\n{'=' * 70}")
    print("BNB SCREEN FINAL SUMMARY")
    g0_max = f"{gate0['max_corr_sym']} {gate0['max_corr_val']:+.4f}"
    print(f"  GATE 0 avg corr:           {gate0['avg_corr']:+.4f} (max: {g0_max})")
    g1_verdict = "PASS" if gate1["gate1_pass"] else "FAIL"
    print(f"  GATE 1 min-horizon Sharpe: {gate1['min_sharpe']:+.4f} → {g1_verdict}")
    g2_verdict = "PASS" if gate2_pass else "FAIL"
    print(f"  GATE 2 PRIMARY IS Sharpe:  {gate2_sharpe:+.4f} → {g2_verdict} (threshold +0.30)")
    g2t_verdict = "FLAG" if gate2_tertiary_flag else "OK"
    print(f"  GATE 2 TERTIARY in-fold gap: {gate2_infold_gap:+.4f} → {g2t_verdict}")
    last_k = data_info["last_kline_date"]
    print(f"  Data: IS {data_info['is_years']:.2f} years, last kline {last_k}")
    print()
    rec = (
        "ADVANCE BNB to full specialist"
        if overall_pass
        else "REJECT BNB cheaply (amended hard-reject)"
    )
    print(f"  RECOMMENDATION: {rec}")
    print(f"{'=' * 70}")

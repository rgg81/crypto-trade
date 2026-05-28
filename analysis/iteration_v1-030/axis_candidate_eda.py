"""iter-v1/030 — Phase 1 axis-candidate EDA.

Evaluates the 5 ELIGIBLE axis families for the /030 EXPLORATION slot per QR
mandate (LM Master /029 §7 routing for /030 = NEW-axis-from-UNUSED-family at
single-seed EXPLORATION budget; cohort-coverage axis CLOSED).

The 5 candidates, with the mechanism-potential signal computed for each:

  1. Sample-weighting (AFML Ch.4 inverse-concurrency + sample-uniqueness)
       Signal: per-(sym, month) avg concurrent-label-overlap on baseline IS.
       Higher overlap = more potential gain from inverse-concurrency weighting.

  2. Meta-labeling layer (López de Prado AFML Ch.3)
       Signal: IS losing trades count + identifiability proxy (regime, BTC
       trend, win-rate gap). Higher identifiable-loss share = more potential.

  3. Trend-scanning labeling (López de Prado AFML Ch.5)
       Signal: baseline IS month-trades hitting TIMEOUT (vs SL/TP). Higher
       timeout rate = more potential gain from adaptive labels.

  4. Fractional differentiation features (AFML Ch.5)
       Signal: ADF p-value on top-5 V1_FEATURE_COLUMNS_PRUNED feature
       categories on baseline IS. Lower stationarity = more potential lift.
       (Note: V1_FEATURE_COLUMNS_PRUNED was selected for ADF stationarity
       at α=0.05 — so we expect LOW potential here.)

  5. DOT salvage at REDUCED budget (ENSEMBLE_SIZE=3 + n_trials=18)
       Signal: /029-projected wall-clock under reduced budget via label-rate
       scaling per `feedback_v1_label_rate_wall_clock_scaling.md`.

Outputs (committed to analysis/iteration_v1-030/):
  - candidate_1_sample_weighting.csv
  - candidate_2_meta_labeling.csv
  - candidate_3_trend_scanning.csv
  - candidate_4_fracdiff.csv
  - candidate_5_dot_salvage_walltime.csv
  - axis_candidate_summary.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

IS_TRADES = REPO / "reports-v1/iteration_v1-baseline/in_sample/trades.csv"
OOS_TRADES = REPO / "reports-v1/iteration_v1-baseline/out_of_sample/trades.csv"

SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
KLINE_INTERVAL = "8h"
KLINE_MS = 8 * 3600 * 1000

# Per src/crypto_trade/strategies/ml/lgbm.py:152, label_timeout_minutes = 4320.
# 4320 / 480 = 9 candles at 8h cadence.
LABEL_HORIZON_BARS = 9

# Per src/crypto_trade/features_v1/__init__.py:89-133.
V1_FEATURE_COLUMNS_PRUNED_FAMILIES = {
    # Family name -> representative feature label for ADF probe.
    # We compute ADF on the underlying RAW transform (kline-derived), not the
    # pruned column itself, to probe the underlying signal stationarity.
    "stat_log_return_1": "log_return",
    "mom_rsi_14": "rsi_14",
    "vol_atr_14": "atr_14",
    "trend_adx_14": "adx_14",
    "vol_volume_pctchg_5": "volume_pctchg_5",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def load_trades(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # open_time / close_time are epoch ms in baseline trades.csv
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df["month"] = df["open_time"].dt.to_period("M").astype(str)
    df["pnl_sign"] = np.where(df["net_pnl_pct"] > 0, 1, -1)
    # direction is -1 (short) / 1 (long) in baseline trades.csv
    df["direction_label"] = np.where(df["direction"].astype(int) > 0, "long", "short")
    return df


def load_klines(symbol: str) -> pd.DataFrame:
    p = REPO / f"data/{symbol}/{KLINE_INTERVAL}.csv"
    df = pd.read_csv(p)
    df["open_time"] = pd.to_datetime(df["open_time"].astype("int64"), unit="ms")
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df


# =============================================================================
# Candidate 1 — Sample-weighting (AFML Ch.4 inverse-concurrency)
# =============================================================================
def candidate_1_sample_weighting(is_trades: pd.DataFrame) -> dict:
    """Compute label-window concurrency on the TRAINING-SAMPLE side (every IS
    candle is a training row whose label spans [t, t+H] forward).

    AFML Ch.4 §4.5: avg uniqueness = (1/N) * sum_i (1/c_t) over candles t in
    label i's window. With label horizon H=9 (8h × 9 = 72h = 3 days) at 8h
    cadence, consecutive training rows share ~89% of their label windows.

    Mean training-sample concurrency is approximately equal to H (=9) when the
    training set is dense (every candle). Lower per-sample uniqueness means
    more potential gain from inverse-concurrency weighting (reduces redundancy
    in the loss surface).

    We compute the training-set concurrency on baseline IS span PER SYMBOL,
    using the kline grid (not just realized trades).
    """
    print("\n=== Candidate 1 — Sample-weighting (training-set label concurrency) ===")
    rows = []
    for sym in SYMBOLS:
        klines = load_klines(sym)
        # IS span: from 2022-01-01 to 2025-03-23 (OOS cutoff)
        is_klines = klines[
            (klines["open_time"] >= pd.Timestamp("2022-01-01"))
            & (klines["open_time"] < pd.Timestamp("2025-03-24"))
        ]
        n_candles = len(is_klines)
        if n_candles < LABEL_HORIZON_BARS + 1:
            continue
        # Training-set concurrency at candle t = number of label windows whose
        # [start, start + H] interval covers t. With dense training set this
        # is min(H, t - 0, N - t).
        # Average across interior candles: H (the horizon).
        # For an honest measurement, simulate over the dense IS grid.
        H = LABEL_HORIZON_BARS
        # Vectorized: for each candle t (0..N-1), concurrency_t = min(t+1, H, N-t)
        idx = np.arange(n_candles)
        concur = np.minimum(np.minimum(idx + 1, H), n_candles - idx)
        rows.append({
            "symbol": sym,
            "n_candles_is": n_candles,
            "label_horizon_bars": H,
            "concurrency_mean": float(concur.mean()),
            "concurrency_p50": float(np.median(concur)),
            "concurrency_p90": float(np.quantile(concur, 0.90)),
            "avg_uniqueness": float((1.0 / concur).mean()),
            "frac_unique_below_0p5": float((1.0 / concur < 0.5).mean()),
        })
    df = pd.DataFrame(rows)
    out_csv = OUT_DIR / "candidate_1_sample_weighting.csv"
    df.to_csv(out_csv, index=False)
    print("  Per-symbol training-set concurrency:")
    for r in rows:
        print(f"    {r['symbol']}: n_candles={r['n_candles_is']} mean_concurrency={r['concurrency_mean']:.2f} avg_uniqueness={r['avg_uniqueness']:.3f}")
    mean_concurrency_avg = float(df["concurrency_mean"].mean())
    mean_uniqueness_avg = float(df["avg_uniqueness"].mean())
    summary = {
        "label_horizon_bars": LABEL_HORIZON_BARS,
        "n_symbols": len(df),
        "mean_concurrency_mean": mean_concurrency_avg,
        "mean_avg_uniqueness": mean_uniqueness_avg,
        "potential_signal": ("STRONG" if mean_uniqueness_avg < 0.20 else
                             ("MODERATE" if mean_uniqueness_avg < 0.50 else "WEAK")),
    }
    print(f"  -> avg uniqueness {mean_uniqueness_avg:.3f}; potential: {summary['potential_signal']}")
    return summary


# =============================================================================
# Candidate 2 — Meta-labeling layer (AFML Ch.3)
# =============================================================================
def candidate_2_meta_labeling(is_trades: pd.DataFrame) -> dict:
    """Meta-labeling reaches potential when LOSING trades are systematically
    identifiable.

    Signal: count IS losing trades, then test if losses concentrate in
    identifiable regimes (per-symbol direction, BTC-trend bucket, exit-reason).
    Higher concentration = more meta-labeling potential.
    """
    print("\n=== Candidate 2 — Meta-labeling ===")
    n_total = len(is_trades)
    n_loss = (is_trades["net_pnl_pct"] < 0).sum()
    win_rate = (is_trades["net_pnl_pct"] > 0).mean()

    # Per-symbol direction loss concentration
    rows = []
    for sym in SYMBOLS:
        for direction in ("long", "short"):
            sub = is_trades[
                (is_trades["symbol"] == sym) & (is_trades["direction_label"] == direction)
            ]
            if len(sub) == 0:
                continue
            wr = float((sub["net_pnl_pct"] > 0).mean())
            n_loss_cell = int((sub["net_pnl_pct"] < 0).sum())
            rows.append({
                "symbol": sym,
                "direction": direction,
                "n_trades": int(len(sub)),
                "n_loss": n_loss_cell,
                "wr": wr,
                "pnl_per_trade": float(sub["net_pnl_pct"].mean()),
                "loss_share_of_total": float(n_loss_cell / n_loss if n_loss else 0),
            })
    df_cells = pd.DataFrame(rows)
    df_cells = df_cells.sort_values("loss_share_of_total", ascending=False)

    # Exit-reason identifiability: do losses concentrate in SL vs timeout?
    exit_loss_concentration = {}
    for reason in ("stop_loss", "timeout", "take_profit"):
        sub = is_trades[is_trades["exit_reason"] == reason]
        if len(sub) == 0:
            continue
        wr = float((sub["net_pnl_pct"] > 0).mean())
        n_loss_cell = int((sub["net_pnl_pct"] < 0).sum())
        exit_loss_concentration[reason] = {
            "n_trades": int(len(sub)),
            "wr": wr,
            "n_loss": n_loss_cell,
            "loss_share": float(n_loss_cell / n_loss if n_loss else 0),
        }
    print("  Exit-reason loss concentration:")
    for k, v in exit_loss_concentration.items():
        print(f"    {k}: n={v['n_trades']} wr={v['wr']:.1%} loss_share={v['loss_share']:.1%}")

    # Worst (sym, direction) cells — these are meta-labeling targets
    worst_cells = df_cells.head(5)
    print("  Worst (sym, direction) cells:")
    for _, r in worst_cells.iterrows():
        print(f"    {r['symbol']} {r['direction']}: n={r['n_trades']} wr={r['wr']:.1%} pnl/tr={r['pnl_per_trade']:+.2%} loss_share={r['loss_share_of_total']:.1%}")

    out_csv = OUT_DIR / "candidate_2_meta_labeling.csv"
    df_cells.to_csv(out_csv, index=False)

    # Headline: what fraction of losses concentrate in the WORST 30% of cells?
    df_cells_sorted = df_cells.sort_values("wr")
    cum_loss = df_cells_sorted["loss_share_of_total"].cumsum()
    # Top-3 worst cells's loss share
    top3_loss_share = float(df_cells.head(3)["loss_share_of_total"].sum())
    summary = {
        "n_total_trades": int(n_total),
        "n_loss": int(n_loss),
        "is_win_rate": float(win_rate),
        "n_cells_with_wr_below_30pct": int((df_cells["wr"] < 0.30).sum()),
        "loss_share_in_below_30pct_cells": float(
            df_cells[df_cells["wr"] < 0.30]["loss_share_of_total"].sum()
        ),
        "top3_worst_cells_loss_share": top3_loss_share,
        "stop_loss_wr": exit_loss_concentration.get("stop_loss", {}).get("wr", 0.0),
        "stop_loss_loss_share": exit_loss_concentration.get("stop_loss", {}).get("loss_share", 0.0),
        "timeout_wr": exit_loss_concentration.get("timeout", {}).get("wr", 0.0),
        "timeout_loss_share": exit_loss_concentration.get("timeout", {}).get("loss_share", 0.0),
    }
    print(f"  -> top-3 worst (sym,dir) cells carry {summary['top3_worst_cells_loss_share']:.1%} of total IS losses")
    print(f"  -> identifiability {'HIGH' if summary['top3_worst_cells_loss_share'] >= 0.35 else 'MODERATE'}")
    return summary


# =============================================================================
# Candidate 3 — Trend-scanning labeling (AFML Ch.5)
# =============================================================================
def candidate_3_trend_scanning(is_trades: pd.DataFrame) -> dict:
    """Trend-scanning labels are adaptive — they replace fixed triple-barrier
    timeout with a regime-aware barrier that can stretch in trending regimes.

    Signal: baseline IS month-trades hitting TIMEOUT vs SL/TP. Timeout trades
    are the ones for which adaptive labeling could yield improvement; trades
    hitting SL/TP were resolved by barriers and would change only if barrier
    placement changes.
    """
    print("\n=== Candidate 3 — Trend-scanning ===")
    exit_counts = is_trades["exit_reason"].value_counts()
    total = len(is_trades)
    exit_shares = (exit_counts / total).to_dict()

    rows = []
    for reason in ("stop_loss", "timeout", "take_profit"):
        sub = is_trades[is_trades["exit_reason"] == reason]
        wr = float((sub["net_pnl_pct"] > 0).mean()) if len(sub) else 0.0
        avg_pnl = float(sub["net_pnl_pct"].mean()) if len(sub) else 0.0
        rows.append({
            "exit_reason": reason,
            "n_trades": int(len(sub)),
            "share": float(exit_counts.get(reason, 0) / total),
            "wr": wr,
            "avg_net_pnl_pct": avg_pnl,
        })
    # Per-symbol timeout breakdown
    sym_rows = []
    for sym in SYMBOLS:
        sub = is_trades[is_trades["symbol"] == sym]
        sym_total = len(sub)
        if sym_total == 0:
            continue
        sym_tmo = (sub["exit_reason"] == "timeout").sum()
        sym_tmo_wr = float(
            (sub[sub["exit_reason"] == "timeout"]["net_pnl_pct"] > 0).mean()
        ) if sym_tmo else 0.0
        sym_rows.append({
            "symbol": sym,
            "n_trades": int(sym_total),
            "n_timeout": int(sym_tmo),
            "timeout_share": float(sym_tmo / sym_total),
            "timeout_wr": sym_tmo_wr,
        })
    df = pd.DataFrame(rows)
    df_sym = pd.DataFrame(sym_rows)
    out_csv = OUT_DIR / "candidate_3_trend_scanning.csv"
    df.to_csv(out_csv, index=False)
    df_sym.to_csv(OUT_DIR / "candidate_3_trend_scanning_per_symbol.csv", index=False)

    timeout_share = exit_shares.get("timeout", 0.0)
    timeout_wr = (
        float((is_trades[is_trades["exit_reason"] == "timeout"]["net_pnl_pct"] > 0).mean())
        if (is_trades["exit_reason"] == "timeout").any() else 0.0
    )
    timeout_pnl = (
        float(is_trades[is_trades["exit_reason"] == "timeout"]["net_pnl_pct"].mean())
        if (is_trades["exit_reason"] == "timeout").any() else 0.0
    )
    print(f"  Exit shares: SL={exit_shares.get('stop_loss',0):.1%} timeout={timeout_share:.1%} TP={exit_shares.get('take_profit',0):.1%}")
    print(f"  Timeout WR: {timeout_wr:.1%}; avg PnL: {timeout_pnl:+.2%}")
    if not df_sym.empty:
        print(f"  Per-symbol timeout share range: {df_sym['timeout_share'].min():.1%} to {df_sym['timeout_share'].max():.1%}")

    summary = {
        "timeout_share": float(timeout_share),
        "timeout_wr": timeout_wr,
        "timeout_avg_pnl": timeout_pnl,
        "stop_loss_share": float(exit_shares.get("stop_loss", 0.0)),
        "take_profit_share": float(exit_shares.get("take_profit", 0.0)),
        "potential_signal": "STRONG" if timeout_share >= 0.30 else ("MODERATE" if timeout_share >= 0.20 else "WEAK"),
    }
    print(f"  -> potential: {summary['potential_signal']}")
    return summary


# =============================================================================
# Candidate 4 — Fractional differentiation (AFML Ch.5)
# =============================================================================
def adf_pvalue(series: pd.Series) -> float:
    """Augmented Dickey-Fuller p-value (statsmodels)."""
    from statsmodels.tsa.stattools import adfuller
    s = series.dropna()
    if len(s) < 50:
        return float("nan")
    try:
        result = adfuller(s, autolag="AIC", regression="c")
        return float(result[1])
    except Exception as exc:  # noqa: BLE001
        print(f"    ADF failed: {exc}")
        return float("nan")


def candidate_4_fracdiff() -> dict:
    """ADF stationarity check on top-5 feature families.

    Lower ADF p-value = MORE stationary = LESS potential gain from frac-diff.
    Higher ADF p-value = LESS stationary = MORE potential gain.

    NB: V1_FEATURE_COLUMNS_PRUNED was pre-selected for ADF stationarity at
    α=0.05 per features_v1/__init__.py comment. Expect LOW potential.
    """
    print("\n=== Candidate 4 — Fractional differentiation ===")

    rows = []
    for sym in SYMBOLS:
        klines = load_klines(sym)
        # Cap at 2024-12-31 (within IS window)
        cutoff_ms = pd.Timestamp("2024-12-31").value // 10**6
        klines = klines[klines["open_time"] <= pd.Timestamp("2024-12-31")]
        if len(klines) < 200:
            continue
        close = klines["close"]
        high = klines["high"]
        low = klines["low"]
        volume = klines["volume"]

        # 1. Raw close price (expect HIGH p-value = NON-stationary)
        adf_close = adf_pvalue(close)

        # 2. Log-return (expect LOW p-value = stationary)
        log_ret = np.log(close / close.shift(1))
        adf_logret = adf_pvalue(log_ret)

        # 3. RSI-14 (bounded [0,100], expect LOW)
        delta = close.diff()
        up = delta.where(delta > 0, 0).rolling(14).mean()
        down = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = up / down.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        adf_rsi = adf_pvalue(rsi)

        # 4. ATR-14 (expect MODERATE — scale-variant)
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        adf_atr_raw = adf_pvalue(atr)
        adf_natr = adf_pvalue(atr / close)  # Normalized ATR

        # 5. Volume %-change-5
        vol_pctchg = volume.pct_change(5).replace([np.inf, -np.inf], np.nan)
        adf_vol = adf_pvalue(vol_pctchg)

        rows.append({
            "symbol": sym,
            "adf_p_close_raw": adf_close,
            "adf_p_log_return": adf_logret,
            "adf_p_rsi_14": adf_rsi,
            "adf_p_atr_14_raw": adf_atr_raw,
            "adf_p_natr_14": adf_natr,
            "adf_p_volume_pctchg_5": adf_vol,
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "candidate_4_fracdiff.csv", index=False)

    # Compute means across symbols.
    pruned_feature_p = float(df[["adf_p_log_return", "adf_p_rsi_14", "adf_p_natr_14", "adf_p_volume_pctchg_5"]].mean().mean())
    print(f"  Avg ADF p-value (close_raw, NON-pruned, NON-stationary):       {df['adf_p_close_raw'].mean():.4f}")
    print(f"  Avg ADF p-value (log_return, pruned, stationary):              {df['adf_p_log_return'].mean():.4f}")
    print(f"  Avg ADF p-value (rsi_14, pruned, stationary):                  {df['adf_p_rsi_14'].mean():.4f}")
    print(f"  Avg ADF p-value (natr_14, pruned, stationary):                 {df['adf_p_natr_14'].mean():.4f}")
    print(f"  Avg ADF p-value (volume_pctchg_5, pruned, stationary):         {df['adf_p_volume_pctchg_5'].mean():.4f}")
    print(f"  Avg ADF p-value over PRUNED features: {pruned_feature_p:.4f}")
    n_nonstationary = int((df[["adf_p_log_return", "adf_p_rsi_14", "adf_p_natr_14", "adf_p_volume_pctchg_5"]] > 0.05).sum().sum())

    summary = {
        "avg_adf_p_close_raw": float(df["adf_p_close_raw"].mean()),
        "avg_adf_p_pruned_features": pruned_feature_p,
        "n_pruned_features_nonstationary_at_alpha_05": n_nonstationary,
        "potential_signal": "WEAK" if pruned_feature_p < 0.05 else ("MODERATE" if pruned_feature_p < 0.20 else "STRONG"),
    }
    print(f"  -> potential: {summary['potential_signal']} (pruned features pre-selected for stationarity)")
    return summary


# =============================================================================
# Candidate 5 — DOT-salvage at REDUCED budget (3/18 mirror of /029)
# =============================================================================
def candidate_5_dot_salvage_walltime() -> dict:
    """Project /029-DOT wall-clock under reduced 3/18 budget via label-rate
    scaling per `feedback_v1_label_rate_wall_clock_scaling.md`.

    Scaling formula:
      expected_wall_clock = precedent_wall_clock × (current_label_count / precedent_label_count) ×
                            (current_ensemble × current_trials) / (precedent_ensemble × precedent_trials)

    Precedents:
      /028 LTC: 10 ENSEMBLE × 35 trials × ~2146 labels/window = ~30-40 min INSIDE 2h cap
      /029 DOT: 10 × 35 × ~4342 labels/window = projected ~2.5h, BREACHED 2h cap

    Salvage:
      /030-DOT: 3 × 18 × ~4342 labels/window
    """
    print("\n=== Candidate 5 — DOT salvage at REDUCED budget ===")
    # From /029 log (Trial 0 - Trial 34 timing analysis):
    # /029 ran ~10080 (10 seeds × 35 trials × 24 months ≈ 8400 base) but actually ran
    # at ENSEMBLE_SIZE=10 + n_trials=35 + ~52 months walk-forward = ~20160 trials
    # in 7204s = 2.80 trials/sec = 173 trials/min.
    # /028 LTC ran at 10/35 in ~30-40 min = ~636 trials/min (3.7× faster).
    # /029 label rate 4342, /028 label rate 2146 → 2.02× higher → roughly explains
    # the 3.7× slowdown after accounting for tree depth.
    #
    # The 5-step scaling computation per `feedback_v1_label_rate_wall_clock_scaling.md`:
    #
    # Step 1 — Precedent iteration:
    #     /029 DOT @ ENSEMBLE_SIZE=10 + n_trials=35 = ran 2h before cap-hit at month
    #     5 / 53 walk-forward (10% complete; 20160 trials emitted).
    # Step 2 — Precedent label count:
    #     /029 baseline log: labels: 2624 long + 1718 short = 4342/window
    # Step 3 — Current iteration expected label count:
    #     /030 DOT same triple-barrier config (atr_sl=1.75, atr_tp=3.5) = ~4342/window
    #     (label rate UNCHANGED — only ENSEMBLE_SIZE × n_trials change).
    # Step 4 — Scaling factor:
    #     /030 budget = 3 × 18 = 54 trial-units
    #     /029 budget = 10 × 35 = 350 trial-units
    #     Compute-fraction = 54 / 350 = 0.154
    #     /029 actual wall-clock at 10% walk-forward = 7204s
    #     /029 projected FULL walk-forward = 7204 / 0.10 = 72040s ≈ 20.0h at 10/35.
    #     /030 projected FULL walk-forward = 72040 × 0.154 = 11094s ≈ 3.08h at 3/18.
    # Step 5 — Sanity check:
    #     3.08h > 2h cap. SALVAGE STILL BREACHES CAP at default settings.

    precedent = {
        "iter": "iter-v1/029",
        "ensemble_size": 10,
        "n_trials": 35,
        "label_count_per_window_long": 2624,
        "label_count_per_window_short": 1718,
        "label_count_per_window_total": 4342,
        "wall_clock_seconds_at_cap_hit": 7204,
        "walk_forward_pct_complete_at_cap_hit": 0.10,  # month 5 of ~53
    }
    # Project /029 full walk-forward
    projected_029_full_seconds = precedent["wall_clock_seconds_at_cap_hit"] / precedent["walk_forward_pct_complete_at_cap_hit"]
    projected_029_full_hours = projected_029_full_seconds / 3600

    # Reduced-budget projection
    # Compute-fraction = (3 × 18) / (10 × 35) = 0.154
    # Wall-clock scales with ENSEMBLE_SIZE × n_trials × labels (labels unchanged).
    salvage_compute_fraction = (3 * 18) / (10 * 35)
    salvage_projected_seconds = projected_029_full_seconds * salvage_compute_fraction
    salvage_projected_minutes = salvage_projected_seconds / 60
    salvage_projected_hours = salvage_projected_seconds / 3600

    # Compare to /028 LTC precedent (10/35 at LTC label rate = 2146)
    # at ~30-40 min total wall-clock = ~2100-2400s.
    ltc_028_projected_at_3_18 = 2400 * salvage_compute_fraction  # ~370s = 6 min

    print(f"  Precedent /029 DOT @ 10/35: 7204s at 10% walk-forward = projected {projected_029_full_hours:.1f}h full run")
    print(f"  Salvage compute-fraction: (3 × 18) / (10 × 35) = {salvage_compute_fraction:.3f}")
    print(f"  /030-salvage projected wall-clock: {salvage_projected_seconds:.0f}s = {salvage_projected_minutes:.0f} min ≈ {salvage_projected_hours:.2f}h")
    print(f"  Cross-check vs /028 LTC at 3/18: ~{ltc_028_projected_at_3_18:.0f}s = ~{ltc_028_projected_at_3_18/60:.0f} min (LTC 2146 labels vs DOT 4342)")

    fits_cap = salvage_projected_hours < 2.0
    fits_90min = salvage_projected_minutes < 90
    summary = {
        "precedent_iter": "/029 DOT",
        "precedent_budget": "10/35",
        "precedent_wall_clock_at_cap_hit_h": precedent["wall_clock_seconds_at_cap_hit"] / 3600,
        "precedent_walk_forward_pct_at_cap_hit": precedent["walk_forward_pct_complete_at_cap_hit"],
        "projected_029_full_hours": projected_029_full_hours,
        "salvage_budget": "3/18",
        "salvage_compute_fraction": salvage_compute_fraction,
        "salvage_projected_minutes": salvage_projected_minutes,
        "salvage_projected_hours": salvage_projected_hours,
        "fits_2h_cap": fits_cap,
        "fits_90min_target": fits_90min,
        "potential_signal": ("FEASIBLE" if fits_90min else
                             ("MARGINAL" if fits_cap else "INFEASIBLE")),
    }
    rows = [summary]
    pd.DataFrame(rows).to_csv(OUT_DIR / "candidate_5_dot_salvage_walltime.csv", index=False)
    print(f"  -> {summary['potential_signal']}: fits 90min={fits_90min}, fits 2h cap={fits_cap}")
    return summary


# =============================================================================
# Summary
# =============================================================================
def write_summary(
    c1: dict, c2: dict, c3: dict, c4: dict, c5: dict
) -> None:
    """Aggregate axis-candidate summary with mechanism-potential signals."""
    rows = [
        {
            "candidate": "1_sample_weighting",
            "family": "sample-weighting (NEW; UNUSED in v1)",
            "primary_signal": f"mean_concurrency={c1['mean_concurrency_mean']:.2f} (H={c1['label_horizon_bars']})",
            "secondary": f"avg_uniqueness={c1['mean_avg_uniqueness']:.3f}",
            "potential": c1["potential_signal"],
            "wallclock_risk": "LOW (no new feature compute; only loss-weights)",
            "structural_fit": "Orthogonal mechanism class; bypasses Pool A LEARNED-NEG family rule",
        },
        {
            "candidate": "2_meta_labeling",
            "family": "meta-labeling (NEW; UNUSED in v1)",
            "primary_signal": f"top3_worst_cells_loss_share={c2['top3_worst_cells_loss_share']:.1%}",
            "secondary": f"is_win_rate={c2['is_win_rate']:.1%}",
            "potential": "STRONG" if c2["top3_worst_cells_loss_share"] >= 0.35 else "MODERATE",
            "wallclock_risk": "MODERATE (M2 classifier trains on M1 outcomes; smaller dataset)",
            "structural_fit": "Orthogonal mechanism class; bypasses Pool A LEARNED-NEG family rule",
        },
        {
            "candidate": "3_trend_scanning",
            "family": "labeling (REPEAT NEW sub-type; UNUSED in v1)",
            "primary_signal": f"timeout_share={c3['timeout_share']:.1%}",
            "secondary": f"timeout_wr={c3['timeout_wr']:.1%}",
            "potential": c3["potential_signal"],
            "wallclock_risk": "HIGH (changes label distribution → label-rate scaling risk like /029)",
            "structural_fit": "Labeling axis; risks /015 cycle-2 n_eff barrier-curve replay",
        },
        {
            "candidate": "4_fracdiff",
            "family": "feature-family (transformation; NEW kernel)",
            "primary_signal": f"avg_adf_p_pruned_features={c4['avg_adf_p_pruned_features']:.4f}",
            "secondary": f"n_nonstationary_at_alpha_05={c4['n_pruned_features_nonstationary_at_alpha_05']}",
            "potential": c4["potential_signal"],
            "wallclock_risk": "MODERATE (fracdiff coefficients computed; new columns add to Pool A)",
            "structural_fit": "NEW feature family to Pool A → STRUCTURALLY DISQUALIFIED per pool_a_new_feature_lneg rule unless multi-seed",
        },
        {
            "candidate": "5_dot_salvage_at_3_18",
            "family": "per-cohort (REPEAT — cohort-coverage CLOSED at /029)",
            "primary_signal": f"projected_wall_clock={c5['salvage_projected_minutes']:.0f}min",
            "secondary": f"compute_fraction={c5['salvage_compute_fraction']:.3f}",
            "potential": c5["potential_signal"],
            "wallclock_risk": ("LOW" if c5["fits_90min_target"] else "HIGH"),
            "structural_fit": "Cohort-coverage CLOSED per LM Master /029 §7; doesn't count as NEW family",
        },
    ]
    df = pd.DataFrame(rows)
    out = OUT_DIR / "axis_candidate_summary.csv"
    df.to_csv(out, index=False)
    print("\n=== Final axis candidate summary ===")
    print(df.to_string(index=False))
    print(f"\nCSV written to: {out}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    print(f"REPO: {REPO}")
    print(f"OUT_DIR: {OUT_DIR}")
    is_trades = load_trades(IS_TRADES)
    print(f"Loaded {len(is_trades)} IS trades")

    c1 = candidate_1_sample_weighting(is_trades)
    c2 = candidate_2_meta_labeling(is_trades)
    c3 = candidate_3_trend_scanning(is_trades)
    c4 = candidate_4_fracdiff()
    c5 = candidate_5_dot_salvage_walltime()
    write_summary(c1, c2, c3, c4, c5)


if __name__ == "__main__":
    main()

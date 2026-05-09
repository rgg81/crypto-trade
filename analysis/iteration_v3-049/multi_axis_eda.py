"""iter-v3/049 — multi-axis EDA for the LAST EXPLORATION before iter-v3/050 CONFIRMATION.

Per `feedback_v3_axis_selection_quant_discipline.md` (established 2026-05-09 at iter-v3/044):
QR must do EDA-driven axis selection BEFORE brief write. Orchestrator may suggest 5 SEED
candidate axes (per Critic FINAL `55fbadb` recommendation #2 of iter-v3/048):

  (a) NEW labeling architecture variant (per-symbol vol-conditioned timeout)
  (b) NEW model architecture (CatBoost head-to-head with LightGBM at 14-feature stack)
  (c) Per-symbol features that pass IS-axis pre-validation (TRX-specific kurtosis-momentum)
  (d) Drawdown-brake risk primitive (orthogonal-to-existing per_symbol_cap)
  (e) ADX-conditional regime gate variant (NOT TRX SHORT block — that was EDA-falsified)

Only (a), (c), (d), (e) lend themselves to direct EDA (b) is theoretical-only — covered in
companion synthesis.md). For each, we either ELIMINATE the candidate or ADVANCE it to brief.

Inputs: iter-v3/045 PROMISING anchor (single-seed; IS +0.7459 / OOS +3.5259) trades + parquets
Outputs:
  - axis_a_vol_horizon.csv      (vol-regime distribution + horizon predictor)
  - axis_c_trx_kurt_momentum.csv (per-symbol importance + per-direction PnL contribution)
  - axis_d_drawdown_brake.csv   (per-symbol drawdown trajectory + threshold sweep)
  - axis_e_adx_conditional.csv  (per-symbol IS PnL × ADX bucket)
  - synthesis.md                (markdown ranking)
  - candidate_axes_ranking.md   (final selected axis + 5 candidates ranked)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANCHOR_REPORT = Path("reports-v3/iteration_v3-045")
FEATURES_DIR = Path("data/features_v3")
DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v3-049")
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")

# ---------- Helpers ----------


def _wilder_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder ADX (mirrors src/crypto_trade/strategies/ml/risk_v2.py:_compute_adx)."""
    n = len(high)
    if n < 2 * period + 1:
        return np.full(n, np.nan)
    up_move = np.diff(high, prepend=high[0])
    down_move = np.diff(-low, prepend=-low[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])

    def _wilder(series: np.ndarray) -> np.ndarray:
        out = np.full_like(series, np.nan, dtype=np.float64)
        if n < period:
            return out
        out[period - 1] = np.sum(series[:period])
        for i in range(period, n):
            out[i] = out[i - 1] - (out[i - 1] / period) + series[i]
        return out

    atr_w = _wilder(tr)
    plus_dm_w = _wilder(plus_dm)
    minus_dm_w = _wilder(minus_dm)
    with np.errstate(invalid="ignore", divide="ignore"):
        plus_di = 100.0 * plus_dm_w / atr_w
        minus_di = 100.0 * minus_dm_w / atr_w
        dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = np.full(n, np.nan, dtype=np.float64)
    first_valid = 2 * period - 1
    if first_valid < n:
        adx[first_valid] = np.nanmean(dx[period - 1 : first_valid + 1])
        for i in range(first_valid + 1, n):
            if not np.isnan(dx[i]) and not np.isnan(adx[i - 1]):
                adx[i] = ((adx[i - 1] * (period - 1)) + dx[i]) / period
    return adx


def _load_trades_with_features(anchor_dir: Path) -> pd.DataFrame:
    """Load IS+OOS trades, attach feature snapshots at trade open bar."""
    is_t = pd.read_csv(anchor_dir / "in_sample" / "trades.csv")
    is_t["sample"] = "IS"
    oos_t = pd.read_csv(anchor_dir / "out_of_sample" / "trades.csv")
    oos_t["sample"] = "OOS"
    trades = pd.concat([is_t, oos_t], ignore_index=True)
    # feature lookup: trade.open_time aligns with bar.close_time
    enriched = []
    for sym, sub in trades.groupby("symbol"):
        if sym not in SYMBOLS:
            continue
        feat_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        if not feat_path.exists():
            print(f"[WARN] missing parquet for {sym}; skipping")
            continue
        df = pd.read_parquet(feat_path)
        # Compute ADX from raw OHLC (not in parquet)
        raw_path = DATA_DIR / sym / "8h.csv"
        if raw_path.exists():
            raw = pd.read_csv(raw_path)
            raw_idx = raw.set_index("open_time")
            joined = df.set_index("open_time").join(
                raw_idx[["high", "low", "close"]].rename(
                    columns={"high": "_h", "low": "_l", "close": "_c"}
                ),
                how="left",
            )
            adx_arr = _wilder_adx(joined["_h"].values, joined["_l"].values, joined["_c"].values, period=14)
            df = df.copy()
            df["adx_14"] = adx_arr
        # Merge: trade.open_time = bar.close_time
        merged = sub.merge(
            df,
            left_on="open_time",
            right_on="close_time",
            how="left",
            suffixes=("", "_bar"),
        )
        if merged["adx_14"].isna().sum() > 0:
            n_missing = merged["adx_14"].isna().sum()
            print(f"[INFO] {sym}: {n_missing}/{len(merged)} trades missing ADX (warmup)")
        enriched.append(merged)
    out = pd.concat(enriched, ignore_index=True)
    return out


# ---------- Axis (a): vol-conditioned labeling horizon ----------


def axis_a_vol_horizon(trades: pd.DataFrame) -> pd.DataFrame:
    """How does trade exit reason / WR vary by vol regime?

    Hypothesis: high-vol regimes hit barriers faster (more SL/TP, fewer timeouts);
    low-vol regimes have more timeouts with poor edge. Adaptive timeout could help.
    """
    rows = []
    # Use range_realized_vol_50 as the vol regime indicator.
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")].copy()
        if "range_realized_vol_50" not in sub.columns or len(sub) < 10:
            continue
        # Per-symbol vol terciles
        vol = sub["range_realized_vol_50"].astype(float)
        try:
            sub["vol_tercile"] = pd.qcut(vol, 3, labels=["lo", "mid", "hi"], duplicates="drop")
        except ValueError:
            sub["vol_tercile"] = "all"
        for tercile, grp in sub.groupby("vol_tercile", observed=True):
            n = len(grp)
            if n < 3:
                continue
            wr = (grp["net_pnl_pct"] > 0).mean() * 100
            avg_pnl = grp["net_pnl_pct"].mean()
            sum_pnl = grp["net_pnl_pct"].sum()
            timeout_rate = (grp["exit_reason"] == "timeout").mean() * 100
            sl_rate = (grp["exit_reason"] == "stop_loss").mean() * 100
            tp_rate = (grp["exit_reason"] == "take_profit").mean() * 100
            rows.append({
                "symbol": sym,
                "vol_tercile": tercile,
                "n_trades_IS": n,
                "WR_pct": round(wr, 1),
                "avg_net_pnl_pct": round(avg_pnl, 3),
                "sum_net_pnl_pct": round(sum_pnl, 3),
                "timeout_rate_pct": round(timeout_rate, 1),
                "stop_loss_rate_pct": round(sl_rate, 1),
                "take_profit_rate_pct": round(tp_rate, 1),
                "vol_min": round(vol[grp.index].min(), 4),
                "vol_max": round(vol[grp.index].max(), 4),
            })
    return pd.DataFrame(rows)


# ---------- Axis (c): TRX-specific kurtosis-momentum feature ----------


def axis_c_trx_kurt_momentum(trades: pd.DataFrame) -> pd.DataFrame:
    """Test: TRX-specific feature `ret_kurt_50_signed_momentum = ret_5d × sign(ret_kurt_50 - 3.0)`

    This is per-symbol equivalent of `regime_momentum_signed_5d` but using kurtosis regime.
    Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` IS-pre-validation requirement,
    we must check: does this feature have positive IS Sharpe contribution at TRX (the
    IS-axis bottleneck)? Score: per-symbol Spearman rank correlation of feature value
    vs forward returns at trade open bars.

    Method: at each TRX trade open bar, compute the candidate feature value, then look
    at the realized trade pnl_pct. If feature has positive Spearman rho with pnl_pct,
    it has predictive content; report rho per symbol.
    """
    rows = []
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")].copy()
        if "ret_kurt_50" not in sub.columns or len(sub) < 15:
            continue
        # Feature definition: 5-day return aligned with sign of (kurtosis - 3.0)
        # We'll compute ret_5d at trade open bar from parquet.  At trade open, the
        # bar.close is the most recent close. We compute log_close - log_close.shift(15).
        feat_path = FEATURES_DIR / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(feat_path)
        df = df.sort_values("open_time").reset_index(drop=True)
        log_close = np.log(df["close"].astype(float).clip(lower=1e-12))
        ret_5d = log_close - log_close.shift(15)
        kurt = df["ret_kurt_50"]
        # Excess-kurtosis: positive => fat-tailed regime. Sign(kurt - 3) is direction-flip.
        kurt_sign = np.sign(kurt - 3.0)
        df["ret_kurt_50_signed_momentum"] = ret_5d * kurt_sign
        # also try a simpler variant: ret_5d × sign(skew)
        if "ret_skew_50" in df.columns:
            df["ret_skew_50_signed_momentum"] = ret_5d * np.sign(df["ret_skew_50"])
        # Merge feature value at trade open bar
        sub = sub.merge(
            df[["close_time", "ret_kurt_50_signed_momentum", "ret_skew_50_signed_momentum"]
                if "ret_skew_50_signed_momentum" in df.columns
                else ["close_time", "ret_kurt_50_signed_momentum"]
            ],
            left_on="open_time",
            right_on="close_time",
            how="left",
            suffixes=("", "_y"),
        )
        # Spearman rank correlation of feature with pnl_pct (signed by trade direction)
        # The feature should predict trade direction; multiply by trade direction to get
        # feature alignment with trade thesis.
        for fname in ["ret_kurt_50_signed_momentum", "ret_skew_50_signed_momentum"]:
            if fname not in sub.columns:
                continue
            ok = sub[[fname, "net_pnl_pct", "direction"]].dropna()
            if len(ok) < 10:
                continue
            # Aligned feature score: feature × trade direction
            aligned = ok[fname] * ok["direction"]
            from scipy.stats import spearmanr  # noqa: PLC0415
            try:
                rho_aligned, p_aligned = spearmanr(aligned, ok["net_pnl_pct"])
            except Exception:
                rho_aligned, p_aligned = float("nan"), float("nan")
            try:
                rho_raw, p_raw = spearmanr(ok[fname], ok["net_pnl_pct"])
            except Exception:
                rho_raw, p_raw = float("nan"), float("nan")
            # Hit-rate when feature sign matches trade direction
            sign_match = (np.sign(ok[fname]) == ok["direction"]).astype(int)
            wr_match = ok.loc[sign_match == 1, "net_pnl_pct"].apply(lambda x: x > 0).mean() if (sign_match == 1).any() else float("nan")
            wr_nomatch = ok.loc[sign_match == 0, "net_pnl_pct"].apply(lambda x: x > 0).mean() if (sign_match == 0).any() else float("nan")
            n_match = int((sign_match == 1).sum())
            n_nomatch = int((sign_match == 0).sum())
            rows.append({
                "symbol": sym,
                "feature": fname,
                "n_trades": len(ok),
                "spearman_rho_aligned": round(rho_aligned, 3) if not np.isnan(rho_aligned) else None,
                "spearman_p_aligned": round(p_aligned, 3) if not np.isnan(p_aligned) else None,
                "spearman_rho_raw": round(rho_raw, 3) if not np.isnan(rho_raw) else None,
                "spearman_p_raw": round(p_raw, 3) if not np.isnan(p_raw) else None,
                "WR_when_sign_matches_dir_pct": round(wr_match * 100, 1) if not np.isnan(wr_match) else None,
                "n_match": n_match,
                "WR_when_sign_diverges_dir_pct": round(wr_nomatch * 100, 1) if not np.isnan(wr_nomatch) else None,
                "n_nomatch": n_nomatch,
            })
    return pd.DataFrame(rows)


# ---------- Axis (d): per-symbol drawdown brake ----------


def axis_d_drawdown_brake(trades: pd.DataFrame) -> pd.DataFrame:
    """Simulate per-symbol drawdown brake at thresholds {-15%, -20%, -25%}.

    Mechanism: when a symbol's running cumulative weighted_pnl crosses a -X% drawdown
    from its running peak, halve trade size for the next 27 candles (~9 days at 8h).
    Equivalent to the v1 R2 mechanism but at the per-symbol layer.

    Method: simulate naively on iter-v3/045 IS trades (assume size halving = pnl halving
    for braked-window trades). Report: trade-roster preservation, IS PnL impact,
    IS Sharpe impact (using daily PnL aggregation).

    Note: this is a NAIVE simulation — actual implementation would interact with
    primitive 10 + ATR labeling. Treat the numbers as upper-bound estimates.
    """
    rows = []
    BRAKE_DURATION_CANDLES = 27  # ~9 days at 8h
    BRAKE_DURATION_MS = BRAKE_DURATION_CANDLES * 8 * 3600 * 1000
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")].copy()
        if len(sub) < 10:
            continue
        sub = sub.sort_values("close_time").reset_index(drop=True)
        wpnl = sub["weighted_pnl"].values
        ts = sub["close_time"].values  # close_time of each closed trade
        cumpnl = np.cumsum(wpnl)
        peak = np.maximum.accumulate(cumpnl)
        dd = peak - cumpnl  # absolute drawdown in weighted_pnl units (not pct)
        # Convert dd to pct of (peak + small): if peak=0, treat dd_pct as 100% if dd>0
        # Actually use absolute units: thresholds in weighted_pnl scale (1 unit = ~1% of $1000 pos).
        # iter-v3/045 IS final cumPnL by sym: BCH=23.62, LDO=54.55, TRX=-7.28, ALGO=-34.05
        # Use thresholds of {-5, -10, -15, -20} in weighted_pnl units (mid-symbol-scale).
        for thr_wpnl in [5, 10, 15, 20]:
            # Naive sim: when dd >= thr_wpnl crosses, halve next 27-candle window pnl
            modified = wpnl.copy()
            i = 0
            n_braked = 0
            n_brake_fires = 0
            while i < len(wpnl):
                if dd[i] >= thr_wpnl:
                    # Brake fires after this trade closes; subsequent trades in window halved
                    fire_t = ts[i]
                    n_brake_fires += 1
                    j = i + 1
                    while j < len(wpnl) and (ts[j] - fire_t) <= BRAKE_DURATION_MS:
                        modified[j] = wpnl[j] * 0.5
                        n_braked += 1
                        j += 1
                    i = j  # skip ahead to avoid duplicate brakes within same window
                else:
                    i += 1
            sum_orig = wpnl.sum()
            sum_mod = modified.sum()
            # Approx daily Sharpe: daily PnL summary not exposed here; report per-trade std proxy
            std_orig = np.std(wpnl) if len(wpnl) > 1 else 1.0
            std_mod = np.std(modified) if len(modified) > 1 else 1.0
            sharpe_proxy_orig = wpnl.mean() / std_orig if std_orig > 0 else 0
            sharpe_proxy_mod = modified.mean() / std_mod if std_mod > 0 else 0
            rows.append({
                "symbol": sym,
                "threshold_wpnl": thr_wpnl,
                "n_brake_fires": n_brake_fires,
                "n_braked_trades": n_braked,
                "n_braked_pct": round(n_braked / len(wpnl) * 100, 1),
                "wpnl_orig": round(sum_orig, 2),
                "wpnl_modified": round(sum_mod, 2),
                "wpnl_delta": round(sum_mod - sum_orig, 2),
                "sharpe_proxy_orig": round(sharpe_proxy_orig, 3),
                "sharpe_proxy_modified": round(sharpe_proxy_mod, 3),
                "max_dd_observed_wpnl": round(dd.max(), 2),
            })
    return pd.DataFrame(rows)


# ---------- Axis (e): ADX-conditional regime gate ----------


def axis_e_adx_conditional(trades: pd.DataFrame) -> pd.DataFrame:
    """For each symbol, stratify trade WR/PnL by ADX bucket at trade-open bar.

    Mechanism candidate: when symbol's own ADX < threshold (low-trend regime), block
    all signals for that symbol. Different from BTC-regime gate (iter-v3/022) which
    conditioned on cross-asset BTC drawdown / vol stress.

    Test: do low-ADX trades have negative-EV per symbol? If yes for the IS-axis
    bottleneck symbols (TRX, ALGO), an ADX-conditional gate could lift IS Sharpe
    without harming OOS.
    """
    rows = []
    bins = [0, 15, 20, 25, 30, 100]
    labels = ["<15", "15-20", "20-25", "25-30", ">=30"]
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")].copy()
        if "adx_14" not in sub.columns:
            continue
        sub = sub.dropna(subset=["adx_14"])
        if len(sub) < 10:
            continue
        sub["adx_bucket"] = pd.cut(sub["adx_14"], bins=bins, labels=labels, include_lowest=True)
        for bucket, grp in sub.groupby("adx_bucket", observed=True):
            n = len(grp)
            if n < 1:
                continue
            wr = (grp["net_pnl_pct"] > 0).mean() * 100
            avg_pnl = grp["net_pnl_pct"].mean()
            sum_pnl = grp["net_pnl_pct"].sum()
            sum_wpnl = grp["weighted_pnl"].sum()
            n_long = int((grp["direction"] == 1).sum())
            n_short = int((grp["direction"] == -1).sum())
            rows.append({
                "symbol": sym,
                "adx_bucket": str(bucket),
                "n_trades_IS": n,
                "n_long": n_long,
                "n_short": n_short,
                "WR_pct": round(wr, 1),
                "avg_net_pnl_pct": round(avg_pnl, 3),
                "sum_net_pnl_pct": round(sum_pnl, 3),
                "sum_weighted_pnl": round(sum_wpnl, 2),
                "adx_min": round(grp["adx_14"].min(), 2),
                "adx_max": round(grp["adx_14"].max(), 2),
            })
    df_out = pd.DataFrame(rows)
    # Also output OOS counterfactual: blocking adx<X would cost what OOS PnL?
    rows_oos = []
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")].copy()
        if "adx_14" not in sub.columns:
            continue
        sub = sub.dropna(subset=["adx_14"])
        if len(sub) < 5:
            continue
        for thr in [15, 18, 20, 22, 25]:
            blocked = sub[sub["adx_14"] < thr]
            kept = sub[sub["adx_14"] >= thr]
            rows_oos.append({
                "symbol": sym,
                "adx_threshold": thr,
                "n_blocked_OOS": len(blocked),
                "wpnl_blocked_OOS": round(blocked["weighted_pnl"].sum(), 2),
                "n_kept_OOS": len(kept),
                "wpnl_kept_OOS": round(kept["weighted_pnl"].sum(), 2),
                "wpnl_total_OOS": round(sub["weighted_pnl"].sum(), 2),
                "OOS_cost_of_blocking": round(blocked["weighted_pnl"].sum(), 2),
            })
    df_oos = pd.DataFrame(rows_oos)
    df_oos.to_csv(OUT_DIR / "axis_e_adx_conditional_oos.csv", index=False)
    return df_out


# ---------- Axis (a) extension: vol-conditioned timeout simulation ----------


def axis_a_horizon_simulation(trades: pd.DataFrame) -> pd.DataFrame:
    """Counter-factual: how many TIMEOUT trades end IS in low-vol vs high-vol bars?

    If timeouts are concentrated in low-vol bars AND they are net-negative,
    a longer horizon there could let TPs hit. If timeouts are concentrated
    in high-vol bars AND they are net-negative, a SHORTER horizon could
    cap losses. Either way, we need to know:
      - n_timeout per (symbol, vol_tercile)
      - net_pnl of timeout trades per (symbol, vol_tercile)
    """
    rows = []
    for sym in SYMBOLS:
        sub = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")].copy()
        if "range_realized_vol_50" not in sub.columns or len(sub) < 10:
            continue
        try:
            sub["vol_tercile"] = pd.qcut(
                sub["range_realized_vol_50"].astype(float), 3,
                labels=["lo", "mid", "hi"], duplicates="drop"
            )
        except ValueError:
            continue
        for tercile, grp in sub.groupby("vol_tercile", observed=True):
            for reason in ("timeout", "stop_loss", "take_profit"):
                gg = grp[grp["exit_reason"] == reason]
                n = len(gg)
                if n == 0:
                    continue
                avg_pnl = gg["net_pnl_pct"].mean()
                sum_pnl = gg["net_pnl_pct"].sum()
                wr = (gg["net_pnl_pct"] > 0).mean() * 100
                rows.append({
                    "symbol": sym,
                    "vol_tercile": str(tercile),
                    "exit_reason": reason,
                    "n_trades": n,
                    "avg_net_pnl_pct": round(avg_pnl, 3),
                    "sum_net_pnl_pct": round(sum_pnl, 3),
                    "WR_pct": round(wr, 1),
                })
    return pd.DataFrame(rows)


# ---------- Main ----------


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    print("[iter-v3/049 EDA] loading iter-v3/045 trades + features...")
    trades = _load_trades_with_features(ANCHOR_REPORT)
    print(f"[iter-v3/049 EDA] enriched trades: {len(trades)} rows")

    print("\n=== Axis (a) — vol-conditioned labeling horizon ===")
    df_a = axis_a_vol_horizon(trades)
    df_a.to_csv(OUT_DIR / "axis_a_vol_horizon.csv", index=False)
    print(df_a.to_string())

    print("\n=== Axis (a) extension — timeout-by-vol-tercile ===")
    df_a2 = axis_a_horizon_simulation(trades)
    df_a2.to_csv(OUT_DIR / "axis_a_timeout_by_vol.csv", index=False)
    print(df_a2.to_string())

    print("\n=== Axis (c) — TRX-specific kurtosis-momentum signed feature ===")
    df_c = axis_c_trx_kurt_momentum(trades)
    df_c.to_csv(OUT_DIR / "axis_c_trx_kurt_momentum.csv", index=False)
    print(df_c.to_string())

    print("\n=== Axis (d) — per-symbol drawdown brake threshold sweep ===")
    df_d = axis_d_drawdown_brake(trades)
    df_d.to_csv(OUT_DIR / "axis_d_drawdown_brake.csv", index=False)
    print(df_d.to_string())

    print("\n=== Axis (e) — per-symbol ADX-bucket IS attribution ===")
    df_e = axis_e_adx_conditional(trades)
    df_e.to_csv(OUT_DIR / "axis_e_adx_conditional.csv", index=False)
    print(df_e.to_string())

    # Per-symbol IS WR + PnL summary (for ranking)
    print("\n=== Anchor IS per-symbol baseline (iter-v3/045) ===")
    base_rows = []
    for sym in SYMBOLS:
        sub_is = trades[(trades["symbol"] == sym) & (trades["sample"] == "IS")]
        sub_oos = trades[(trades["symbol"] == sym) & (trades["sample"] == "OOS")]
        base_rows.append({
            "symbol": sym,
            "IS_n": len(sub_is),
            "IS_WR_pct": round((sub_is["net_pnl_pct"] > 0).mean() * 100, 1) if len(sub_is) else 0,
            "IS_sum_net_pnl_pct": round(sub_is["net_pnl_pct"].sum(), 2) if len(sub_is) else 0,
            "IS_sum_wpnl": round(sub_is["weighted_pnl"].sum(), 2) if len(sub_is) else 0,
            "OOS_n": len(sub_oos),
            "OOS_WR_pct": round((sub_oos["net_pnl_pct"] > 0).mean() * 100, 1) if len(sub_oos) else 0,
            "OOS_sum_net_pnl_pct": round(sub_oos["net_pnl_pct"].sum(), 2) if len(sub_oos) else 0,
            "OOS_sum_wpnl": round(sub_oos["weighted_pnl"].sum(), 2) if len(sub_oos) else 0,
        })
    df_base = pd.DataFrame(base_rows)
    df_base.to_csv(OUT_DIR / "anchor_baseline.csv", index=False)
    print(df_base.to_string())

    print(f"\n[iter-v3/049 EDA] outputs written to {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

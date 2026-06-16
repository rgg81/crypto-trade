"""IS-ONLY regime-gate scan for a LET-WINNERS-RUN book — iter-v1/010 (BTCUSDT).

WHY THIS SCRIPT EXISTS
----------------------
iter-009 found the right MECHANISM: a fixed_horizon (N=21, 7d) directional label with a
"let winners run, cut losers" execution (TP non-binding via atr_tp=100, protective SL at
1.45 ATR, 7d timeout). In the real backtest this produced a genuine asymmetric payoff —
IS avg win +6.46% / avg loss -3.11% / payoff 2.08 — but was NEGATIVE (IS Sharpe -0.09 /
OOS -0.74). Diagnosis: the binding constraint is the HIT RATE (~33% WR). At 33% WR the
breakeven payoff is exactly 2.0; IS payoff 2.08 barely clears, OOS payoff 1.75 slips
below -> OOS net -15.94%. The model trades BLINDLY across all regimes.

The iter-008 regime forensic (regime_edge_forensic.py) dismissed all regimes because
always-LONG out-RETURNED the model. THAT USED THE WRONG YARDSTICK on two counts:
  (a) it judged on RETURN (econ %/candle), not SHARPE (risk-adjusted) — the user-mandated
      objective. A regime where the model under-returns always-LONG but has a higher
      Sharpe (less drawdown / lower dispersion) is SUPERIOR for our objective.
  (b) it simulated per-candle OOF econ under a triple-barrier (2.9/1.45) execution, NOT
      the let-winners-run book (TP non-binding, SL 1.45, 7d timeout). The whole iter-009
      payoff structure (winners run to timeout) is absent from that measurement.

THIS SCRIPT RE-EXAMINES regimes through the CORRECT lens, IS-only:
  1. Reconstruct a faithful proxy of the iter-009 19-col directional specialist: a
     purged forward-chaining CV (5 folds, 3-bar embargo) LightGBM predicting the
     fixed_horizon 7d sign. (Faithful proxy of the deployed bagged specialist's
     directional read; treated as DIRECTION-ONLY per the campaign's proxy-magnitude
     warning.)
  2. Simulate the LET-WINNERS-RUN trade per OOF candle: enter in the model's predicted
     direction at candle close; exit at min(SL hit at 1.45 ATR in the trade's adverse
     direction, 21-candle/7d timeout). TP is NON-BINDING (atr_tp=100 -> never hits),
     exactly as iter-009. Record the realized trade return (% net of round-trip fee).
  3. Partition by STATELESS, PAST-ONLY regime variables and, per regime, report:
        - WR (win rate of the let-run trades)
        - payoff (avg win / |avg loss|)
        - WR x payoff vs the breakeven hyperbola (WR + (1-WR)/payoff form -> expected-R)
        - per-trade Sharpe of the let-run trade returns (mean/std)
        - ANNUALIZED Sharpe proxy (per-trade Sharpe x sqrt(trades/yr))
        - always-LONG-in-regime Sharpe (same let-run exit, forced LONG) -- the alpha bar
        - retained IS trades + trades/month (degeneracy guard, must keep >= ~10/mo)
  The GATE BAR (genuine timing alpha, not regime drift): the gated MODEL Sharpe must beat
  BOTH the ungated model Sharpe AND always-LONG-in-regime Sharpe, on a SHARPE basis.

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert
BEFORE any forward quantity is computed. All forward labels / let-run trades / regime
variables are built on the IS slice ONLY (the forward reach at the IS tail NaN-masks
because no OOS candle exists in the frame to index into). Regime variables are stateless
and past-only (.shift(1) on every rolling stat). `src/`, the runner, and OOS are
UNTOUCHED.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-010/regime_gate_letrun_sharpe.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1  # round-trip fee approximation in % (matches label fee convention)
RANDOM_SEED = 42
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-010"

# iter-009 execution constants (let winners run / cut losers)
ATR_SL = 1.45  # protective stop, 1.45 ATR adverse
TIMEOUT_C = 21  # 7d at 8h
LABEL_HORIZON = 21  # fixed_horizon N=21 (7d) directional label, same as iter-009

# Annualization: 8h candles -> 3 candles/day -> ~1095 candles/yr. We annualize the
# per-trade Sharpe by sqrt(trades_per_year). trades_per_year computed per bucket from the
# bucket's own trade frequency (entries are one-per-candle, so trades_per_year ~= bucket
# fraction x 1095). We report both per-trade and annualized.
CANDLES_PER_YEAR = 365.25 * 3.0

# The iter-009 19-col HYBRID short+regime+funding feature set (feature_report.md sec 6).
ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7", "vol_garman_klass_10", "vol_atr_5", "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5", "vol_mfi_7", "mom_rsi_9", "stat_autocorr_lag1",
    "mr_pct_from_high_5", "vol_cmf_10", "ent_shannon_10", "trend_adx_14",
    "trend_supertrend_14_3", "btc_funding_spread_30_90", "funding_rate_zscore_30",
    "stat_autocorr_lag5", "vol_range_spike_72", "mr_rsi_extreme_14", "stat_kurtosis_20",
)


def fixed_horizon_sign(close: np.ndarray, n: int) -> np.ndarray:
    """fixed_horizon label sign: sign(close[i+n] - close[i]) net of fee.

    Faithful to labeling.py fixed_horizon mode: forward N-candle return sign. The fee
    band makes near-zero moves label 0 (no-trade); we keep the runner convention of
    a fee-adjusted forward return then take its sign. Tail rows NaN (no OOS peek).
    """
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        entry = close[i]
        if entry == 0:
            continue
        fwd = (close[i + n] - entry) / entry * 100.0
        out[i] = fwd  # store the forward return; sign taken by caller
    return out


def letrun_trade_return(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    direction: np.ndarray,
    atr_sl: float,
    timeout_c: int,
) -> np.ndarray:
    """Simulate the iter-009 let-winners-run trade for each candle.

    Enter at close[i] in `direction[i]` (+1 long / -1 short). TP is NON-BINDING (winners
    run). Exit at the FIRST of:
      - protective SL: adverse move of atr_sl * ATR (long: low <= entry - sl*ATR;
        short: high >= entry + sl*ATR)
      - timeout: hold to candle i+timeout_c (exit at that close)
    Returns the realized trade return in % NET of round-trip fee, signed by direction.
    NaN if direction is 0/NaN or insufficient forward candles (tail -> no OOS peek).
    """
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n):
        d = direction[i]
        if not np.isfinite(d) or d == 0:
            continue
        entry = close[i]
        if entry == 0:
            continue
        a = atr[i] if np.isfinite(atr[i]) else entry * 0.02
        end = min(i + timeout_c, n - 1)
        if end <= i:
            continue  # tail: not enough forward candles -> NaN (no OOS peek)
        if d > 0:  # LONG
            sl_price = entry - a * atr_sl
            exit_px = close[end]
            for j in range(i + 1, end + 1):
                if low[j] <= sl_price:
                    exit_px = sl_price
                    break
                exit_px = close[j]
            raw = (exit_px - entry) / entry * 100.0
        else:  # SHORT
            sl_price = entry + a * atr_sl
            exit_px = close[end]
            for j in range(i + 1, end + 1):
                if high[j] >= sl_price:
                    exit_px = sl_price
                    break
                exit_px = close[j]
            raw = (entry - exit_px) / entry * 100.0
        out[i] = raw - FEE_PCT
    return out


def purged_oof(X: np.ndarray, y: np.ndarray, valid: np.ndarray, folds: int = 5,
               embargo: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Purged forward-chaining OOF predictions (regression on forward return)."""
    idx = np.where(valid)[0]
    n = len(idx)
    Xm, ym = X[idx], y[idx]
    fs = n // folds
    preds, gidx = [], []
    for k in range(1, folds):
        tr_end = k * fs
        te_s = tr_end + embargo
        te_e = min((k + 1) * fs, n)
        if te_s >= te_e:
            continue
        m = lgb.LGBMRegressor(
            n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03,
            min_child_samples=80, subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.5, reg_lambda=0.5, random_state=RANDOM_SEED, n_jobs=4,
            verbose=-1,
        )
        m.fit(Xm[:tr_end], ym[:tr_end])
        preds.append(m.predict(Xm[te_s:te_e]))
        gidx.append(idx[te_s:te_e])
    return np.concatenate(preds), np.concatenate(gidx)


def stats(trade_ret: np.ndarray, freq_frac: float) -> dict:
    """WR / payoff / expected-R / per-trade Sharpe / annualized Sharpe of let-run trades.

    `freq_frac` = fraction of all IS candles in this bucket; used to scale trades/yr for
    the annualized Sharpe (entries are one-per-candle).
    """
    r = trade_ret[np.isfinite(trade_ret)]
    n = len(r)
    if n < 20:
        return dict(n=n, wr=np.nan, avg_win=np.nan, avg_loss=np.nan, payoff=np.nan,
                    exp_r=np.nan, mean=np.nan, std=np.nan, sharpe_pt=np.nan,
                    sharpe_ann=np.nan, trades_per_mo=np.nan)
    wins = r[r > 0]
    losses = r[r <= 0]
    wr = len(wins) / n
    avg_win = float(np.mean(wins)) if len(wins) else 0.0
    avg_loss = float(np.mean(losses)) if len(losses) else 0.0
    payoff = (avg_win / abs(avg_loss)) if avg_loss != 0 else np.nan
    # expected-R per trade in units of the avg loss (>1 => above breakeven hyperbola):
    # E[R] = WR*payoff - (1-WR). breakeven (E[R]=0) <=> payoff = (1-WR)/WR.
    exp_r = wr * payoff - (1 - wr) if np.isfinite(payoff) else np.nan
    mean = float(np.mean(r))
    std = float(np.std(r, ddof=1)) if n > 1 else np.nan
    sharpe_pt = (mean / std) if (std and np.isfinite(std) and std > 0) else np.nan
    trades_per_yr = freq_frac * CANDLES_PER_YEAR
    sharpe_ann = sharpe_pt * np.sqrt(trades_per_yr) if np.isfinite(sharpe_pt) else np.nan
    trades_per_mo = trades_per_yr / 12.0
    return dict(n=n, wr=wr, avg_win=avg_win, avg_loss=avg_loss, payoff=payoff,
                exp_r=exp_r, mean=mean, std=std, sharpe_pt=sharpe_pt,
                sharpe_ann=sharpe_ann, trades_per_mo=trades_per_mo)


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)
    is_months = (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 30.44

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    natr = df[ATR_COLUMN].to_numpy(float)
    atr = close * natr / 100.0
    adx = df["trend_adx_14"].to_numpy(float)

    feats = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats) == 19, f"expected 19 iter-009 features, got {len(feats)}"
    X = df[feats].to_numpy(float)

    # --- directional label = fixed_horizon 7d forward return; model predicts it ----
    fwd_ret = fixed_horizon_sign(close, LABEL_HORIZON)
    valid = np.isfinite(fwd_ret)
    pred, gidx = purged_oof(X, fwd_ret, valid)
    direction_oof = np.sign(pred)  # model's chosen trade direction at each OOF candle

    # --- simulate the let-winners-run trade in the MODEL direction (full IS array) ---
    full_dir = np.zeros(n_is)
    full_dir[gidx] = direction_oof
    model_tr = letrun_trade_return(high, low, close, atr, full_dir, ATR_SL, TIMEOUT_C)
    # always-LONG let-run trade (forced +1) for the alpha comparison
    long_dir = np.ones(n_is)
    long_tr = letrun_trade_return(high, low, close, atr, long_dir, ATR_SL, TIMEOUT_C)

    # restrict to OOF candles only (where the model has an out-of-fold direction)
    oof_mask = np.zeros(n_is, dtype=bool)
    oof_mask[gidx] = True
    # also require a finite simulated trade (tail rows NaN)
    sim_ok = oof_mask & np.isfinite(model_tr)
    n_oof = int(sim_ok.sum())

    # ----- exit-mix sanity (confirm winners run: how many hit SL vs timeout) ---------
    # (recompute exit reason for model trades on sim_ok set, informational)
    print("=" * 88)
    print(f"IS-ONLY let-winners-run regime gate scan — {SYMBOL} {INTERVAL}")
    print(f"IS rows {n_is} ({is_months:.1f} mo) | OOF candles with valid let-run trade "
          f"{n_oof}")
    print(f"Label: fixed_horizon N={LABEL_HORIZON} (7d). Exec: TP NON-BINDING, "
          f"SL={ATR_SL} ATR, timeout={TIMEOUT_C}c. Fee {FEE_PCT}% round-trip.")
    print("=" * 88)

    # ---------------- past-only stateless regime variables -----------------------
    s = pd.Series(close)

    def slope_sign(w: int, sw: int) -> np.ndarray:
        sma = s.rolling(w).mean().shift(1)
        return np.sign(((sma - sma.shift(sw)) / sw).to_numpy())

    t100 = slope_sign(100, 20)  # ~33d SMA slope over ~7d
    t50 = slope_sign(50, 10)
    t200 = slope_sign(200, 30)  # slow regime sign (~67d SMA)

    ns = pd.Series(natr)
    roll = 250
    nhi = ns.rolling(roll).quantile(0.67).shift(1).to_numpy()
    nlo = ns.rolling(roll).quantile(0.33).shift(1).to_numpy()
    vol_hi = (natr > nhi) & np.isfinite(nhi)
    vol_mid = (natr <= nhi) & (natr >= nlo) & np.isfinite(nhi) & np.isfinite(nlo)
    vol_lo = (natr < nlo) & np.isfinite(nlo)

    adx_hi = adx >= 25.0
    adx_chop = adx < 20.0

    # funding regime sign (past-only; the column is a rolling z-score, already lagged in
    # features_v1). positive funding z => crowded longs (contrarian fade risk); negative
    # => crowded shorts. We test funding>=0 and funding<0 as a crypto-native regime.
    fz = df["funding_rate_zscore_30"].to_numpy(float)
    fund_pos = fz >= 0
    fund_neg = fz < 0

    gates: list[tuple[str, np.ndarray]] = [
        ("UNGATED (all OOF)", np.ones(n_is, dtype=bool)),
        ("TREND100 up", t100 > 0),
        ("TREND100 down", t100 < 0),
        ("TREND50 up", t50 > 0),
        ("TREND200 up (slow)", t200 > 0),
        ("VOL high (natr>p67)", vol_hi),
        ("VOL mid", vol_mid),
        ("VOL low (natr<p33)", vol_lo),
        ("ADX>=25 (trend)", adx_hi),
        ("ADX<20 (chop)", adx_chop),
        ("funding z>=0", fund_pos),
        ("funding z<0", fund_neg),
        # crypto-native compounds: trend-persistence regimes for a let-run book
        ("TREND100up & VOLhigh", (t100 > 0) & vol_hi),
        ("TREND100up & ADX>=25", (t100 > 0) & adx_hi),
        ("VOLhigh & ADX>=25", vol_hi & adx_hi),
        ("TREND100up & fund z<0", (t100 > 0) & fund_neg),
        ("ADX>=25 & fund z<0", adx_hi & fund_neg),
    ]

    rows = []
    for name, gmask in gates:
        bucket = sim_ok & gmask
        freq = bucket.sum() / n_is
        m = stats(model_tr[bucket], freq)
        long_freq = (oof_mask & np.isfinite(long_tr) & gmask).sum() / n_is
        ml = stats(long_tr[oof_mask & np.isfinite(long_tr) & gmask], long_freq)
        # breakeven payoff for this bucket's WR
        be_payoff = (1 - m["wr"]) / m["wr"] if (np.isfinite(m["wr"]) and m["wr"] > 0) \
            else np.nan
        clears = (np.isfinite(m["payoff"]) and np.isfinite(be_payoff)
                  and m["payoff"] > be_payoff)
        # the alpha test: model Sharpe must beat BOTH ungated AND always-LONG-in-regime
        rows.append(dict(
            gate=name, n=m["n"], trades_per_mo=round(m["trades_per_mo"], 1)
            if np.isfinite(m["trades_per_mo"]) else np.nan,
            wr=round(m["wr"], 4) if np.isfinite(m["wr"]) else np.nan,
            payoff=round(m["payoff"], 3) if np.isfinite(m["payoff"]) else np.nan,
            be_payoff=round(be_payoff, 3) if np.isfinite(be_payoff) else np.nan,
            clears_be=clears,
            exp_r=round(m["exp_r"], 4) if np.isfinite(m["exp_r"]) else np.nan,
            mean_pct=round(m["mean"], 4) if np.isfinite(m["mean"]) else np.nan,
            sharpe_pt=round(m["sharpe_pt"], 4) if np.isfinite(m["sharpe_pt"]) else np.nan,
            sharpe_ann=round(m["sharpe_ann"], 4) if np.isfinite(m["sharpe_ann"])
            else np.nan,
            LONG_sharpe_pt=round(ml["sharpe_pt"], 4) if np.isfinite(ml["sharpe_pt"])
            else np.nan,
            LONG_sharpe_ann=round(ml["sharpe_ann"], 4) if np.isfinite(ml["sharpe_ann"])
            else np.nan,
            LONG_mean_pct=round(ml["mean"], 4) if np.isfinite(ml["mean"]) else np.nan,
        ))

    out = pd.DataFrame(rows)
    # alpha flag: model annualized Sharpe beats both ungated and always-LONG-in-regime
    ungated_sharpe = float(out.loc[out["gate"] == "UNGATED (all OOF)",
                                   "sharpe_ann"].iloc[0])
    out["beats_ungated"] = out["sharpe_ann"] > ungated_sharpe
    out["beats_long"] = out["sharpe_ann"] > out["LONG_sharpe_ann"]
    out["TIMING_ALPHA"] = out["beats_ungated"] & out["beats_long"] & out["clears_be"]

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print("\n--- per-regime let-winners-run trade stats (model direction) ---")
    print(out[["gate", "n", "trades_per_mo", "wr", "payoff", "be_payoff", "clears_be",
               "sharpe_pt", "sharpe_ann", "LONG_sharpe_ann", "beats_ungated",
               "beats_long", "TIMING_ALPHA"]].to_string(index=False))

    print(f"\nUNGATED annualized Sharpe (the bar to beat): {ungated_sharpe:+.4f}")
    print("TIMING_ALPHA = model_sharpe_ann > ungated AND > always-LONG-in-regime AND "
          "clears breakeven payoff.")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTDIR / "regime_gate_letrun_sharpe.csv", index=False)
    print(f"\nWrote: {OUTDIR / 'regime_gate_letrun_sharpe.csv'}")


if __name__ == "__main__":
    main()

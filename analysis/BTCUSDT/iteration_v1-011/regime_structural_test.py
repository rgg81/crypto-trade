"""IS-ONLY structural-vs-reducible confirmation for the BTC long-edge collapse — iter-v1/011.

longedge_stability.py established the headline: across EVERY training-window config (180/365/545/
730d rolling + expanding) AND every complexity config (19/16/8-col, strong-reg), the let-run LONG
edge is positive in exactly 6/9 IS ~6-month sub-periods (frac_pos == 0.667 INVARIANT) and negative
in the SAME 3 sub-periods (2022 H1, 2022 H2, 2025 Q1). No lever moves frac_pos. That is the
signature of a STRUCTURAL regime dependence, not reducible overfit.

This script confirms it on two axes, IS-ONLY:

  1. IS the frac_pos == 0.667 / negative-in-bear pattern SEED-ROBUST? Re-run the expanding-window
     19-col model at 5 seeds; report per-sub-period LONG Sharpe sign-agreement across seeds. If the
     SAME sub-periods go negative across all seeds, the regime dependence is structural (not a basin
     artifact). If signs flip seed-to-seed, it's lottery noise.

  2. Is the long-edge sign EXPLAINED BY REGIME? Condition the let-run LONG book on a stateless,
     past-only TREND regime (200-candle SMA slope sign = bull/bear) and on a NATR vol tercile, and
     report LONG Sharpe + WR in each. If the long edge is strongly positive in BULL and negative/
     absent in BEAR (structural directional-beta dependence), the collapse is a regime artifact:
     the model's "long skill" is just trend-following that only pays in an up-trend. This directly
     tests the crypto-native reflexivity thesis — a let-winners-run long book is a trend-persistence
     bet that structurally requires an up-trending regime.

  3. SIZING IMPLICATION (IS-only, descriptive): if the long edge is regime-bound to BULL, what does
     a regime-aware long-bias variant look like in-sample — LONG let-run book restricted to the BULL
     regime vs the full ungated book? (Reported as a candidate direction, NOT a tuned recommendation;
     no threshold is fit to maximize anything — the regime is the stateless 200-SMA slope sign.)

OOS-VIGILANCE (HARD): strict `open_time < OOS_CUTOFF_MS` filter + leak-guard assert BEFORE any
forward quantity; expanding walk-forward trains only on candles strictly before each test window
minus an embargo >= label horizon; regime variables are stateless & past-only (`.shift(1)` on every
rolling stat). `src/`, runner, OOS UNTOUCHED. Nothing fit/selected against OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-011/regime_structural_test.py
"""

from __future__ import annotations

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000
SYMBOL = "BTCUSDT"
PARQUET = Path("data/features") / f"{SYMBOL}_8h_features.parquet"
ATR_COLUMN = "vol_natr_21"
FEE_PCT = 0.1
ATR_SL = 1.45
N_LABEL = 9
CANDLES_PER_DAY = 3.0
CANDLES_PER_YEAR = 365.25 * CANDLES_PER_DAY
EMBARGO_C = N_LABEL + 3
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-011"
SEEDS = (42, 123, 456, 789, 1001)

ITER009_FEATURES: tuple[str, ...] = (
    "trend_adx_7",
    "vol_garman_klass_10",
    "vol_atr_5",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5",
    "vol_mfi_7",
    "mom_rsi_9",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
    "vol_cmf_10",
    "ent_shannon_10",
    "trend_adx_14",
    "trend_supertrend_14_3",
    "btc_funding_spread_30_90",
    "funding_rate_zscore_30",
    "stat_autocorr_lag5",
    "vol_range_spike_72",
    "mr_rsi_extreme_14",
    "stat_kurtosis_20",
)
BASE_PARAMS = dict(
    n_estimators=300,
    max_depth=4,
    num_leaves=15,
    learning_rate=0.03,
    min_child_samples=80,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.5,
    reg_lambda=0.5,
    n_jobs=4,
    verbose=-1,
)


def fwd_return(close, n):
    out = np.full(len(close), np.nan)
    for i in range(len(close) - n):
        if close[i] != 0:
            out[i] = (close[i + n] - close[i]) / close[i] * 100.0
    return out


def letrun(high, low, close, atr, direction, atr_sl, timeout_c):
    n = len(close)
    out = np.full(n, np.nan)
    for i in range(n):
        d = direction[i]
        if not np.isfinite(d) or d == 0 or close[i] == 0:
            continue
        entry = close[i]
        a = atr[i] if np.isfinite(atr[i]) else entry * 0.02
        end = min(i + timeout_c, n - 1)
        if end <= i:
            continue
        if d > 0:
            sl = entry - a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if low[j] <= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (ex - entry) / entry * 100.0
        else:
            sl = entry + a * atr_sl
            ex = close[end]
            for j in range(i + 1, end + 1):
                if high[j] >= sl:
                    ex = sl
                    break
                ex = close[j]
            raw = (entry - ex) / entry * 100.0
        out[i] = raw - FEE_PCT
    return out


def expanding_wf(X, y, ot_days, valid, params, seed, min_train_days=365.0, step_days=30.0):
    n = len(X)
    embargo_days = EMBARGO_C / CANDLES_PER_DAY
    t0 = ot_days.min()
    ts = t0 + min_train_days + embargo_days
    preds, idx = [], []
    while ts < ot_days.max():
        te = ts + step_days
        tc = ts - embargo_days
        tr = valid & (ot_days < tc) & (ot_days >= t0)
        tem = valid & (ot_days >= ts) & (ot_days < te)
        if tr.sum() >= 200 and tem.sum() > 0:
            m = lgb.LGBMRegressor(random_state=seed, **params)
            m.fit(X[tr], y[tr])
            preds.append(m.predict(X[tem]))
            idx.append(np.where(tem)[0])
        ts = te
    if not idx:
        return np.zeros(n), np.zeros(n, dtype=bool)
    p = np.concatenate(preds)
    g = np.concatenate(idx)
    d = np.zeros(n)
    d[g] = np.sign(p)
    oof = np.zeros(n, dtype=bool)
    oof[g] = True
    return d, oof


def ann_sharpe(r, n_total, min_n=12):
    r = r[np.isfinite(r)]
    if len(r) < min_n:
        return np.nan, np.nan, len(r)
    mean, std = float(np.mean(r)), float(np.std(r, ddof=1))
    if std <= 0:
        return np.nan, float(np.mean(r > 0)), len(r)
    return (
        (mean / std) * np.sqrt(len(r) / n_total * CANDLES_PER_YEAR),
        float(np.mean(r > 0)),
        len(r),
    )


def subperiods(ot_days, oof, period_days=182.5):
    t0 = ot_days[oof].min()
    t1 = ot_days[oof].max()
    bounds = []
    edge = t0
    while edge < t1:
        bounds.append((edge, edge + period_days))
        edge += period_days
    return bounds


def main() -> None:
    df_full = pd.read_parquet(PARQUET)
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    natr = df[ATR_COLUMN].to_numpy(float)
    atr = close * natr / 100.0
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    feats = [c for c in ITER009_FEATURES if c in df.columns]
    assert len(feats) == 19
    X = df[feats].to_numpy(float)
    y = fwd_return(close, N_LABEL)
    valid = np.isfinite(y)
    long_dir = np.ones(n_is)
    longbook = letrun(high, low, close, atr, long_dir, ATR_SL, N_LABEL)

    # stateless past-only regime variables
    s = pd.Series(close)
    sma200 = s.rolling(200).mean().shift(1)
    trend_bull = ((sma200 - sma200.shift(20)) > 0).to_numpy()  # 200-SMA rising = bull
    natr_s = pd.Series(natr)
    natr_p67 = natr_s.rolling(250).quantile(0.67).shift(1).to_numpy()
    natr_p33 = natr_s.rolling(250).quantile(0.33).shift(1).to_numpy()
    vol_hi = natr > natr_p67
    vol_lo = natr < natr_p33

    # ============ 1. SEED ROBUSTNESS of the sub-period sign pattern ============
    print("=" * 100)
    print("1. SEED ROBUSTNESS of per-sub-period LONG Sharpe sign (expanding WF, 19-col, 5 seeds)")
    print("   structural if the SAME sub-periods are negative across all seeds")
    print("=" * 100)
    # reference bounds from seed 42
    d42, oof42 = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, 42)
    bounds = subperiods(ot_days, oof42)
    per_seed_signs = {}
    per_seed_sharpe = {}
    for seed in SEEDS:
        d, oof = expanding_wf(X, y, ot_days, valid, BASE_PARAMS, seed)
        mb = letrun(high, low, close, atr, d, ATR_SL, N_LABEL)
        signs, sharpes = [], []
        for lo, hi in bounds:
            m = oof & (d > 0) & np.isfinite(mb) & (ot_days >= lo) & (ot_days < hi)
            sann, _, nn = ann_sharpe(mb[m], n_is)
            sharpes.append(sann)
            signs.append(
                1 if (np.isfinite(sann) and sann > 0) else (0 if np.isfinite(sann) else -9)
            )
        per_seed_signs[seed] = signs
        per_seed_sharpe[seed] = sharpes
    starts = [str(pd.to_datetime(lo * 86400_000, unit="ms").date()) for lo, _ in bounds]
    print(f"  {'sub-period':12s} " + " ".join(f"s{s:<5d}" for s in SEEDS) + "  agree?")
    rows1 = []
    for k, st in enumerate(starts):
        vals = [per_seed_sharpe[s][k] for s in SEEDS]
        signs = [per_seed_signs[s][k] for s in SEEDS]
        pos = sum(1 for v in signs if v == 1)
        valid_seeds = sum(1 for v in signs if v != -9)
        agree = (
            "ALL+"
            if pos == valid_seeds and valid_seeds > 0
            else ("ALL-" if pos == 0 and valid_seeds > 0 else "MIXED")
        )
        vstr = " ".join(f"{v:+.2f}" if np.isfinite(v) else " nan " for v in vals)
        print(f"  {st:12s} {vstr}  {agree}")
        rows1.append(
            dict(
                sub_period=st,
                **{
                    f"seed_{s}": round(per_seed_sharpe[s][k], 3)
                    if np.isfinite(per_seed_sharpe[s][k])
                    else np.nan
                    for s in SEEDS
                },
                agreement=agree,
            )
        )
    # frac_pos per seed
    print("\n  frac_pos per seed (sub-periods with positive LONG Sharpe):")
    for s in SEEDS:
        fp = np.mean([1 if v == 1 else 0 for v in per_seed_signs[s] if v != -9])
        print(f"    seed {s:5d}: frac_pos={fp:.3f}")
    pd.DataFrame(rows1).to_csv(OUTDIR / "seed_subperiod_signs.csv", index=False)

    # ============ 2. LONG edge conditioned on REGIME (seed 42) ============
    print("\n" + "=" * 100)
    print("2. LONG let-run edge conditioned on stateless past-only REGIME (expanding WF, seed 42)")
    print("   structural-beta if LONG edge is strong in BULL, negative/absent in BEAR")
    print("=" * 100)
    mb42 = letrun(high, low, close, atr, d42, ATR_SL, N_LABEL)
    base_long = oof42 & (d42 > 0) & np.isfinite(mb42)
    regimes = [
        ("ALL (ungated LONG)", np.ones(n_is, dtype=bool)),
        ("TREND bull (200SMA up)", trend_bull),
        ("TREND bear (200SMA dn)", ~trend_bull),
        ("VOL high (natr>p67)", vol_hi),
        ("VOL low (natr<p33)", vol_lo),
        ("BULL & VOL-low", trend_bull & vol_lo),
        ("BEAR & VOL-high", (~trend_bull) & vol_hi),
    ]
    rows2 = []
    for name, rmask in regimes:
        m = base_long & rmask
        sann, wr, nn = ann_sharpe(mb42[m], n_is)
        # always-LONG comparator on same regime candles
        alm = oof42 & np.isfinite(longbook) & rmask
        al_sann, al_wr, _ = ann_sharpe(longbook[alm], n_is)
        tpm = round(nn / n_is * CANDLES_PER_YEAR / 12, 1)
        rows2.append(
            dict(
                regime=name,
                long_n=nn,
                trades_per_mo=tpm,
                long_sharpe_ann=round(sann, 3) if np.isfinite(sann) else np.nan,
                long_wr=round(wr, 3) if np.isfinite(wr) else np.nan,
                always_long_sharpe=round(al_sann, 3) if np.isfinite(al_sann) else np.nan,
                model_beats_long=bool(
                    np.isfinite(sann) and np.isfinite(al_sann) and sann > al_sann
                ),
            )
        )
        ss = f"{sann:+.3f}" if np.isfinite(sann) else "  nan"
        ws = f"{wr:.3f}" if np.isfinite(wr) else " nan"
        als = f"{al_sann:+.3f}" if np.isfinite(al_sann) else "  nan"
        print(
            f"  {name:24s} n={nn:4d} tpm={tpm:5.1f}  LONG_S={ss}  WR={ws}  alwaysLONG={als}  "
            f"model>LONG={bool(np.isfinite(sann) and np.isfinite(al_sann) and sann > al_sann)}"
        )
    pd.DataFrame(rows2).to_csv(OUTDIR / "longedge_by_regime.csv", index=False)

    # ============ 3. SIZING IMPLICATION — regime-restricted long book vs full ============
    print("\n" + "=" * 100)
    print("3. SIZING IMPLICATION (IS-only descriptive) — full model book vs BULL-restricted")
    print("=" * 100)
    rows3 = []
    full_m = oof42 & np.isfinite(mb42)
    fs, fwr, fn = ann_sharpe(mb42[full_m], n_is)
    rows3.append(
        dict(
            variant="full model book (both sides, ungated)",
            n=fn,
            sharpe_ann=round(fs, 3),
            wr=round(fwr, 3),
            trades_per_mo=round(fn / n_is * CANDLES_PER_YEAR / 12, 1),
        )
    )
    bull_m = oof42 & np.isfinite(mb42) & trend_bull
    bs, bwr, bn = ann_sharpe(mb42[bull_m], n_is)
    rows3.append(
        dict(
            variant="model book restricted to BULL regime",
            n=bn,
            sharpe_ann=round(bs, 3),
            wr=round(bwr, 3),
            trades_per_mo=round(bn / n_is * CANDLES_PER_YEAR / 12, 1),
        )
    )
    # long-only in bull (drop shorts entirely, trade long only when 200SMA up)
    lbull_m = oof42 & (d42 > 0) & np.isfinite(mb42) & trend_bull
    lbs, lbwr, lbn = ann_sharpe(mb42[lbull_m], n_is)
    rows3.append(
        dict(
            variant="LONG-only restricted to BULL regime",
            n=lbn,
            sharpe_ann=round(lbs, 3),
            wr=round(lbwr, 3),
            trades_per_mo=round(lbn / n_is * CANDLES_PER_YEAR / 12, 1),
        )
    )
    for r in rows3:
        print(
            f"  {r['variant']:42s} n={r['n']:4d} tpm={r['trades_per_mo']:5.1f}  "
            f"S={r['sharpe_ann']:+.3f}  WR={r['wr']:.3f}"
        )
    pd.DataFrame(rows3).to_csv(OUTDIR / "sizing_implication.csv", index=False)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(
        f"\nWrote: {OUTDIR / 'seed_subperiod_signs.csv'}, {OUTDIR / 'longedge_by_regime.csv'}, "
        f"{OUTDIR / 'sizing_implication.csv'}"
    )


if __name__ == "__main__":
    main()

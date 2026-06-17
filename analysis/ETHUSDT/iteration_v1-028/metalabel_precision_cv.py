"""iter-v1/028 Phase 2 (CORE) — Meta-labeling precision study, IS-ONLY, purged+embargo CV.

The decisive design experiment. From horizon_and_concentration.py we learned: ETH's edge is
trend-persistent; a binding TP kills it. So we KEEP the let-winners-run execution and instead
add a META (M2) filter that vetoes the low-success entries — raising win-rate + profit-factor
+ the WINNER FRACTION (the de-concentration the user wants), without truncating winners.

Setup (López de Prado AFML Ch.3 meta-labeling, IS-only):
  PRIMARY (M1): the deterministic trend-state direction (+1 if close>SMA200 else -1) +
                conviction gate (strength >= q40). This is the iter-027 primary, UNCHANGED.
  TARGET (M2):  binary label = 1 if the trend-state trade's 14d realized NET return > 0.
  M2 FEATURES:  crypto-native regime/positioning set (funding z, OI delta, basis z, taker
                ratio, Hurst, ADX, vol, RSI) — the features that should separate winning vs
                losing trend entries.
  CV:           purged K-fold with embargo (gap = horizon candles) on the IS trade series.
  METRIC:       compare {RAW trend book} vs {M2-filtered book at threshold t} on:
                win-rate, profit-factor, n_trades, top1/top2 share, per-trade Sharpe.

The look-ahead discipline: M2 is fit ONLY on training folds; the test-fold trades are scored
with the held-out model; labels purged within `gap` of the test boundary on BOTH sides; an
embargo of 1% of T. ALL rows are IS (open_time < OOS_CUTOFF_MS, horizon-safe). No OOS touched.

Outputs: metalabel_precision_cv.csv  (and prints the headline comparison)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    load_full_for_label_horizon,
    trend_state_dir,
    trend_strength_atr_norm,
)

OUT = Path(__file__).parent
HORIZON = 42  # 14d
ROUND_TRIP_COST = 0.0014
TRADES_PER_YEAR = 365.0 / 14.0

# Crypto-native M2 feature set (all past-only, in the parquet, scale-invariant)
M2_FEATURES = [
    "funding_rate_zscore_30",
    "funding_rate_zscore_90",
    "btc_funding_spread_30_90",
    "oi_delta_30_z90",
    "oi_price_divergence_30",
    "basis_zscore_30",
    "long_short_zscore_30",
    "vol_taker_buy_ratio",
    "hurst_100",
    "trend_adx_14",
    "vol_natr_21",
    "mom_rsi_9",
    "regime_momentum_signed_5d",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
]


def realized_net_14d(full: pd.DataFrame, entry_idx: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Let-winners-run 14d-timeout net return (no binding TP — matches baseline execution)."""
    close = full["close"].values
    out = np.empty(len(entry_idx), dtype=float)
    for k, i in enumerate(entry_idx):
        e = close[i]
        exit_close = close[min(i + HORIZON, len(close) - 1)]
        out[k] = direction[k] * (exit_close / e - 1.0) - ROUND_TRIP_COST
    return out


def purged_kfold_indices(n: int, k: int, gap: int, embargo: int):
    """Yield (train_idx, test_idx) for contiguous-block K-fold with purge gap + embargo."""
    fold_sizes = [n // k + (1 if x < n % k else 0) for x in range(k)]
    bounds = np.cumsum([0] + fold_sizes)
    for f in range(k):
        t0, t1 = bounds[f], bounds[f + 1]
        test_idx = np.arange(t0, t1)
        # purge: remove training rows within `gap` of the test block on both sides;
        # embargo: additionally remove `embargo` rows AFTER the test block.
        lo = max(0, t0 - gap)
        hi = min(n, t1 + gap + embargo)
        train_mask = np.ones(n, dtype=bool)
        train_mask[lo:hi] = False
        train_idx = np.where(train_mask)[0]
        yield train_idx, test_idx


def book_stats(net: np.ndarray, tag: str) -> dict:
    cs = concentration_stats(net)
    wins = net[net > 0].sum()
    losses = -net[net < 0].sum()
    pf = (wins / losses) if losses > 0 else np.inf
    return {
        "book": tag,
        "n_trades": cs["n_trades"],
        "win_rate": cs["win_rate"],
        "n_winners": cs["n_winners"],
        "profit_factor": pf,
        "sum_net": cs["net_sum"],
        "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(net, TRADES_PER_YEAR),
        "top1_share_of_net": cs["top1_share_of_net"],
        "top2_share_of_net": cs["top2_share_of_net"],
    }


def main() -> None:
    full = load_full_for_label_horizon()
    n_all = len(full)

    ts = trend_state_dir(full, 200).astype(int)
    strength = trend_strength_atr_norm(full, 200, 14).values
    is_mask = full["open_time"].values < OOS_CUTOFF_MS
    q40 = np.nanquantile(strength[is_mask & np.isfinite(strength)], 0.40)

    # Entries: IS, horizon-safe, conviction-gated, post-SMA-warmup.
    fut_open = pd.Series(full["open_time"].values).shift(-HORIZON).values
    horizon_safe = (full["open_time"].values < OOS_CUTOFF_MS) & (fut_open < OOS_CUTOFF_MS)
    conv = np.isfinite(strength) & (strength >= q40)
    entry = np.where(is_mask & horizon_safe & conv & (ts != 0))[0]
    entry = entry[entry >= 200]

    # Drop entries with any NaN M2 feature.
    feat = full.loc[entry, M2_FEATURES].copy()
    valid = feat.notna().all(axis=1).values
    entry = entry[valid]
    feat = feat[valid].reset_index(drop=True)
    dirs = ts[entry]
    net = realized_net_14d(full, entry, dirs)
    y = (net > 0).astype(int)  # M2 target: did the trend trade win?
    n = len(entry)
    print(f"IS meta-labeling sample: {n} trend-state entries, base win-rate {y.mean():.3f}")

    # Purged CV M2 out-of-fold probabilities.
    gap = HORIZON  # one symbol => gap = timeout_candles
    embargo = max(1, int(0.01 * n))
    oof_proba = np.full(n, np.nan)
    X = feat.values
    for tr, te in purged_kfold_indices(n, k=5, gap=gap, embargo=embargo):
        if len(np.unique(y[tr])) < 2:
            continue
        clf = LGBMClassifier(
            n_estimators=200, max_depth=3, num_leaves=15, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.7, min_child_samples=20,
            reg_alpha=0.1, reg_lambda=0.1, random_state=42, verbosity=-1,
            scale_pos_weight=float((y[tr] == 0).sum()) / max(1, (y[tr] == 1).sum()),
        )
        clf.fit(X[tr], y[tr])
        oof_proba[te] = clf.predict_proba(X[te])[:, 1]

    ok = ~np.isnan(oof_proba)
    print(f"OOF coverage: {ok.sum()}/{n}")

    rows = [book_stats(net[ok], "RAW_trend_book (no M2)")]
    # Sweep M2 threshold; report each filtered book.
    for thr in [0.45, 0.50, 0.55, 0.60, 0.65]:
        keep = ok & (oof_proba >= thr)
        if keep.sum() < 20:
            rows.append({"book": f"M2>={thr:.2f}", "n_trades": int(keep.sum()), "note": "too_few"})
            continue
        rows.append(book_stats(net[keep], f"M2>={thr:.2f}"))

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "metalabel_precision_cv.csv", index=False)
    pd.set_option("display.width", 230)
    pd.set_option("display.max_columns", 30)
    print("\n=== Meta-labeling (M2) precision filter, purged+embargo OOF CV, IS-only ===")
    print(out.to_string(index=False))

    # Precision lift table: at each threshold, what fraction kept + WR among kept.
    print("\n=== M2 calibration (does higher P(win) -> higher realized WR?) ===")
    cal = []
    for lo, hi in [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]:
        b = ok & (oof_proba >= lo) & (oof_proba < hi)
        if b.sum() >= 10:
            cal.append({"proba_bin": f"[{lo:.1f},{hi:.1f})", "n": int(b.sum()),
                        "realized_WR": float((net[b] > 0).mean()),
                        "mean_net": float(net[b].mean())})
    caldf = pd.DataFrame(cal)
    caldf.to_csv(OUT / "metalabel_calibration.csv", index=False)
    print(caldf.to_string(index=False))


if __name__ == "__main__":
    main()

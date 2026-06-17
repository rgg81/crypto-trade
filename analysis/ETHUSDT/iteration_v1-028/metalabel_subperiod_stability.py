"""iter-v1/028 Phase 2 — Sub-period stability of the M2 precision lift (IS-only).

The OOS fingerprint test: a lift that only exists in 2020-2021 is useless for OOS
(2025-03+). Split the IS trend-state trade series into chronological sub-periods and
report, in EACH, the RAW vs M2-filtered (thr=0.45) win-rate / profit-factor / per-trade
Sharpe / concentration. Use the SAME purged-CV OOF probabilities from the full IS fit
(re-derived here for self-containment).

Crucially also report the MOST-RECENT IS sub-period (2024-06 .. 2025-03) — the closest
analogue to OOS regime.

ALL IS-only. Outputs: metalabel_subperiod_stability.csv + m2_feature_importance.csv
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
from metalabel_precision_cv import (  # noqa: E402
    HORIZON,
    M2_FEATURES,
    ROUND_TRIP_COST,
    TRADES_PER_YEAR,
    purged_kfold_indices,
    realized_net_14d,
)

OUT = Path(__file__).parent


def book_row(net: np.ndarray, tag: str, period: str) -> dict:
    cs = concentration_stats(net)
    wins = net[net > 0].sum()
    losses = -net[net < 0].sum()
    pf = (wins / losses) if losses > 0 else np.inf
    return {
        "period": period, "book": tag, "n": cs["n_trades"], "win_rate": cs["win_rate"],
        "profit_factor": pf, "sum_net": cs["net_sum"],
        "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(net, TRADES_PER_YEAR),
        "top2_share_of_net": cs["top2_share_of_net"],
    }


def main() -> None:
    full = load_full_for_label_horizon()
    ts = trend_state_dir(full, 200).astype(int)
    strength = trend_strength_atr_norm(full, 200, 14).values
    is_mask = full["open_time"].values < OOS_CUTOFF_MS
    q40 = np.nanquantile(strength[is_mask & np.isfinite(strength)], 0.40)
    fut_open = pd.Series(full["open_time"].values).shift(-HORIZON).values
    horizon_safe = (full["open_time"].values < OOS_CUTOFF_MS) & (fut_open < OOS_CUTOFF_MS)
    conv = np.isfinite(strength) & (strength >= q40)
    entry = np.where(is_mask & horizon_safe & conv & (ts != 0))[0]
    entry = entry[entry >= 200]
    feat = full.loc[entry, M2_FEATURES].copy()
    valid = feat.notna().all(axis=1).values
    entry = entry[valid]
    feat = feat[valid].reset_index(drop=True)
    dirs = ts[entry]
    net = realized_net_14d(full, entry, dirs)
    y = (net > 0).astype(int)
    n = len(entry)
    open_times = full["open_time"].values[entry]
    dates = pd.to_datetime(open_times, unit="ms")

    # OOF probabilities (purged + embargo), identical recipe to the core study.
    gap = HORIZON
    embargo = max(1, int(0.01 * n))
    oof = np.full(n, np.nan)
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
        oof[te] = clf.predict_proba(X[te])[:, 1]
    ok = ~np.isnan(oof)

    # Chronological sub-periods (calendar-year-ish + the recent OOS-fingerprint window).
    periods = [
        ("2020", "2020-01-01", "2021-01-01"),
        ("2021", "2021-01-01", "2022-01-01"),
        ("2022", "2022-01-01", "2023-01-01"),
        ("2023", "2023-01-01", "2024-01-01"),
        ("2024H1", "2024-01-01", "2024-07-01"),
        ("2024H2_2025Q1_RECENT", "2024-07-01", "2025-03-24"),
    ]
    thr = 0.45
    rows = []
    for pname, a, b in periods:
        m = ok & (dates >= pd.Timestamp(a)) & (dates < pd.Timestamp(b))
        if m.sum() < 15:
            rows.append({"period": pname, "book": "RAW", "n": int(m.sum()), "note": "too_few"})
            continue
        rows.append(book_row(net[m], "RAW", pname))
        mf = m & (oof >= thr)
        if mf.sum() >= 10:
            rows.append(book_row(net[mf], f"M2>={thr}", pname))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "metalabel_subperiod_stability.csv", index=False)
    pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30)
    print("=== M2 lift sub-period stability (IS-only, thr=0.45) ===")
    print(out.to_string(index=False))

    # M2 feature importance (full IS fit) — confirm broad, not single-feature.
    clf_full = LGBMClassifier(
        n_estimators=200, max_depth=3, num_leaves=15, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.7, min_child_samples=20,
        reg_alpha=0.1, reg_lambda=0.1, random_state=42, verbosity=-1,
        scale_pos_weight=float((y == 0).sum()) / max(1, (y == 1).sum()),
    )
    clf_full.fit(X, y)
    imp = pd.DataFrame({"feature": M2_FEATURES, "gain": clf_full.booster_.feature_importance("gain")})
    imp["gain_share"] = imp["gain"] / imp["gain"].sum()
    imp = imp.sort_values("gain_share", ascending=False).reset_index(drop=True)
    imp.to_csv(OUT / "m2_feature_importance.csv", index=False)
    print("\n=== M2 feature importance (full IS fit; broad => robust) ===")
    print(imp.to_string(index=False))


if __name__ == "__main__":
    main()

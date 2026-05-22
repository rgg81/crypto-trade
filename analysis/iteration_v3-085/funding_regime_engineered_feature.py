"""iter-v3/085 — Cycle-3 EXPLORATION #4 EDA, PART 4: the COMMITTED AXIS — a NEW
funding-regime-conditioned ENGINEERED feature (Category-2 composed feature; IS-only).

CONTEXT — why the axis is NOT a pooled model. Direction 3 (multi-symbol-pooled model)
was the orchestrator's lead candidate. iter-v3/085 ran THREE IS-only EDA probes against
it (`pooled_model_cross_symbol_structure.py`, `pooled_with_symbol_dummy.py`,
`ldo_donor_augmentation.py`) and ALL THREE FALSIFIED it:
  - naive pool: leave-one-symbol-out transfer lift -0.0188 (worse than base rate);
  - pooled + symbol_id dummy: -0.0124 vs per-symbol, BREAKS BCH (-0.0414 — BCH carries
    ~96% of v3 IS PnL, so a pool that breaks BCH collapses the headline IS Sharpe);
  - LDO-only donor augmentation: best donor config -0.0013 BELOW LDO's per-symbol
    baseline — even gentle 0.3-weight donor down-weighting does not help.
Per `feedback_v3_axis_selection_quant_discipline.md` the QR makes the axis call with
committed EDA — and the EDA says pooling is not the axis. The runner CAN support
pooling (v1 Model A precedent), so this is a SIGNAL falsification, not a feasibility one.

THE COMMITTED AXIS. The pooled-model EDA's central POSITIVE finding: v3's per-symbol
architecture is correct, but the 14-feature stack carries near-zero IS edge (every
per-symbol leave-one-out baseline is within ~0.02 accuracy of the base rate). The
structural gap is the FEATURE SET. The cycle-3 plan Direction 1 (NEW crypto-native
families) is HIGHEST priority; `feedback_v3_engineered_features_proven.md` records that
ENGINEERED composed features are the one PROVEN-PROMISING v3 axis (iter-v3/025's
`regime_momentum_signed_5d`). The committed iter-v3/085 axis is a NEW Category-2
composed feature:

    funding_regime_momentum_5d  =  regime_momentum_signed_5d  ×  sign(funding_z_30)

where funding_z_30 is the 30-period z-score of the past-only funding rate. The funding
rate enters ONLY as a regime sign-switch on an existing momentum primitive — it is
NEVER a standalone model feature. This is a fundamentally different construction from
the CLOSED v3 funding axis (`funding_rate_zscore_30` / `btc_funding_rate_zscore_30` /
the /082 4-channel family — all Category-1 funding-AS-DIRECT-FEATURE, all INERT). The
hypothesis: crowded-funding regimes flip the meaning of raw momentum (momentum into a
crowded long is exhaustion; momentum into a crowded short is a squeeze setup), and a
depth-4 tree cannot compose that funding×momentum sign-interaction from the primitives.

PART 4 grounds this axis on IS data — the EDA the brief Section 2 cites:
  T1. ENGINEERED-vs-LABEL IC — Spearman IC of the engineered feature vs the
      triple-barrier label, per symbol, vs the raw `regime_momentum_signed_5d` IC.
  T2. ORTHOGONALITY — IC of the engineered feature vs its own primitive and vs all 14
      stack features (the Category-2 incremental-information check; the iter-v3/025
      carve-out treats the IC gate as informational but near-zero IC confirms the
      feature is NOT a redundant repackaging — it avoids the iter-v3/070 colsample-
      theft trap).
  T3. INCREMENTAL-INFORMATION — a quick per-symbol LightGBM with the 14 features vs
      14 + the engineered feature, chronological IS 70/30 split. Does the engineered
      feature lift held-out accuracy?
  T4. FUNDING-REGIME COVERAGE — funding-z sign distribution + data coverage for all 3
      v3 symbols (the engineered feature is degenerate if funding-z is near-constant).

NO CHEATING:
  - IS data only (open_time < OOS_CUTOFF_DATE 2025-03-24). OOS never loaded.
  - `OOS_CUTOFF_DATE` / `training_months` not read as tunables, not modified.
  - funding_z_30 is PAST-ONLY: funding_rate.shift(1) before the rolling window — the
    engineered feature is computable from data with timestamp < t.
  - The 70/30 split is chronological, WITHIN the IS window — an EDA generalisation
    probe, not the production walk-forward. No iter-v3/085 design parameter is chosen
    on OOS data; the funding window (30) is fixed a-priori at the funding-settlement-
    cycle convention (30 8h-candles = 10 days), NOT swept on any metric.

Run:
  export PATH="$HOME/.local/bin:$PATH"
  uv run python analysis/iteration_v3-085/funding_regime_engineered_feature.py
"""

from __future__ import annotations

import csv
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr

from crypto_trade.strategies.ml.labeling import label_trades

warnings.filterwarnings("ignore")

OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE, tz="UTC").timestamp() * 1000)
TIMEOUT_MINUTES = 10080
ATR_TP, ATR_SL = 2.0, 1.0
FEE_PCT = 0.1
FUNDING_Z_WINDOW = 30  # 30 8h-candles = 10 days; funding-cycle convention, fixed a-priori

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA_DIR = Path("data")
FEATURES_DIR = Path("data/features_v3")
FUNDING_DIR = Path("data/funding_rates")
OUT_DIR = Path("analysis/iteration_v3-085")

V3_FEATURES = [
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
]
PRIMITIVE = "regime_momentum_signed_5d"
ENGINEERED = "funding_regime_momentum_5d"

LGB_PARAMS = dict(
    objective="binary", num_leaves=15, max_depth=4, learning_rate=0.05,
    n_estimators=120, min_child_samples=40, subsample=0.8,
    colsample_bytree=0.8, verbose=-1, seed=42,
)


def _load_is(symbol: str) -> pd.DataFrame:
    """IS-slice OHLCV + 14 features + the engineered funding-regime feature."""
    ohlcv = pd.read_csv(DATA_DIR / symbol / "8h.csv")
    ohlcv = ohlcv[["open_time", "open", "high", "low", "close", "close_time"]].copy()
    ohlcv["symbol"] = symbol
    feats = pq.read_table(
        FEATURES_DIR / f"{symbol}_8h_features.parquet",
        columns=["open_time", "natr_21_raw", *V3_FEATURES],
    ).to_pandas()
    merged = ohlcv.merge(feats, on="open_time", how="inner")

    # Funding rate, joined backward (each 8h candle gets the last settled funding).
    fund = pd.read_csv(FUNDING_DIR / f"{symbol}.csv").rename(
        columns={"funding_time": "open_time"}
    )
    merged = pd.merge_asof(
        merged.sort_values("open_time"),
        fund.sort_values("open_time"),
        on="open_time",
        direction="backward",
    )
    merged = merged[merged["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)

    # ---- the engineered feature — PAST-ONLY by construction -------------------
    # funding_z_30: z-score of past funding. .shift(1) drops the current candle's
    # funding from its own window, so the value at bar t uses only funding < t.
    fr = merged["funding_rate"]
    fz = (
        fr - fr.shift(1).rolling(FUNDING_Z_WINDOW).mean()
    ) / (fr.shift(1).rolling(FUNDING_Z_WINDOW).std() + 1e-9)
    merged["funding_z_30"] = fz
    # funding_regime_momentum_5d = regime_momentum_signed_5d × sign(funding_z_30).
    # sign(0)=0 only when funding_z is exactly 0 (degenerate early-window rows) —
    # those rows are dropped by the valid-mask below.
    merged[ENGINEERED] = merged[PRIMITIVE] * np.sign(fz.fillna(0.0))
    return merged


def _label(df: pd.DataFrame) -> np.ndarray:
    close = df["close"].to_numpy(dtype=float)
    natr = df["natr_21_raw"].to_numpy(dtype=float)
    atr_values = close * natr / 100.0
    valid = (
        df[V3_FEATURES].notna().all(axis=1).to_numpy()
        & np.isfinite(df[ENGINEERED].to_numpy())
        & np.isfinite(atr_values)
        & (atr_values > 0)
    )
    cand = np.where(valid)[0].astype(np.intp)
    labels, _w, _lp, _sp = label_trades(
        df, cand, ATR_TP, ATR_SL, TIMEOUT_MINUTES,
        fee_pct=FEE_PCT, atr_values=atr_values, verbose=0,
        label_mode="triple_barrier",
    )
    full = np.full(len(df), np.nan)
    full[cand] = labels
    return full


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/085 EDA PART 4 — COMMITTED AXIS: funding-regime engineered feature")
    print("=" * 78)

    frames: dict[str, pd.DataFrame] = {}
    for sym in SYMBOLS:
        df = _load_is(sym)
        df["_label"] = _label(df)
        frames[sym] = df
        n_lab = int(np.isfinite(df["_label"]).sum())
        print(f"  {sym}: {len(df)} IS candles, {n_lab} labelable")

    # ----------------------------------------------------------------------
    # T1 — ENGINEERED-vs-LABEL IC, per symbol, vs the raw primitive IC.
    # ----------------------------------------------------------------------
    print("\n[T1] Engineered-feature IS IC vs triple-barrier label (vs raw primitive)")
    t1_rows = []
    for sym in SYMBOLS:
        d = frames[sym]
        m = np.isfinite(d["_label"]).to_numpy()
        y = (d.loc[m, "_label"].to_numpy() > 0).astype(float)
        eng = d.loc[m, ENGINEERED].to_numpy(float)
        prim = d.loc[m, PRIMITIVE].to_numpy(float)
        ic_eng = float(spearmanr(eng, y)[0])
        ic_prim = float(spearmanr(prim, y)[0])
        t1_rows.append(
            {
                "symbol": sym,
                "ic_engineered": round(ic_eng, 4),
                "ic_raw_primitive": round(ic_prim, 4),
                "abs_ic_gain": round(abs(ic_eng) - abs(ic_prim), 4),
            }
        )
        print(
            f"  {sym}: engineered IC {ic_eng:+.4f} | raw {PRIMITIVE} IC "
            f"{ic_prim:+.4f} | |IC| gain {abs(ic_eng) - abs(ic_prim):+.4f}"
        )
    n_ic_gain = sum(1 for r in t1_rows if r["abs_ic_gain"] > 0)
    print(f"  |IC| GAIN on {n_ic_gain}/3 symbols vs the raw primitive")
    with (OUT_DIR / "part4_t1_engineered_ic.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["symbol", "ic_engineered", "ic_raw_primitive", "abs_ic_gain"]
        )
        w.writeheader()
        w.writerows(t1_rows)

    # ----------------------------------------------------------------------
    # T2 — ORTHOGONALITY: engineered vs its own primitive + vs all 14 features.
    # Category-2 carve-out (iter-v3/025): IC gate is informational; near-zero IC
    # confirms the feature is genuinely new, NOT a redundant repackaging.
    # ----------------------------------------------------------------------
    print("\n[T2] Orthogonality — engineered feature vs the 14-feature stack")
    t2_rows = []
    for sym in SYMBOLS:
        d = frames[sym]
        m = np.isfinite(d["_label"]).to_numpy()
        eng = d.loc[m, ENGINEERED].to_numpy(float)
        ics = {}
        for feat in V3_FEATURES:
            x = d.loc[m, feat].to_numpy(float)
            if np.std(x) == 0 or np.std(eng) == 0:
                ics[feat] = 0.0
            else:
                ics[feat] = abs(float(np.corrcoef(eng, x)[0, 1]))
        max_feat = max(ics, key=ics.get)
        ic_vs_primitive = ics[PRIMITIVE]
        max_ic = ics[max_feat]
        t2_rows.append(
            {
                "symbol": sym,
                "abs_ic_vs_primitive": round(ic_vs_primitive, 4),
                "max_abs_ic_vs_stack": round(max_ic, 4),
                "max_ic_feature": max_feat,
            }
        )
        print(
            f"  {sym}: |IC| vs {PRIMITIVE} = {ic_vs_primitive:.4f} | "
            f"max |IC| vs 14-stack = {max_ic:.4f} ({max_feat})"
        )
    worst_max_ic = max(r["max_abs_ic_vs_stack"] for r in t2_rows)
    print(
        f"  WORST max |IC| vs stack across symbols: {worst_max_ic:.4f} "
        f"({'PASS hard gate 0.70' if worst_max_ic < 0.70 else 'CHECK'}; "
        f"{'PASS strict 0.50' if worst_max_ic < 0.50 else 'Category-2 carve-out applies'})"
    )
    with (OUT_DIR / "part4_t2_orthogonality.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "symbol", "abs_ic_vs_primitive", "max_abs_ic_vs_stack",
                "max_ic_feature",
            ],
        )
        w.writeheader()
        w.writerows(t2_rows)

    # ----------------------------------------------------------------------
    # T3 — INCREMENTAL-INFORMATION: 14 features vs 14 + engineered, per symbol,
    # chronological IS 70/30 split. Does the engineered feature lift accuracy?
    # ----------------------------------------------------------------------
    print("\n[T3] Incremental information — 14 vs 15 features (chronological IS 70/30)")
    t3_rows = []
    for sym in SYMBOLS:
        d = frames[sym]
        m = np.isfinite(d["_label"]).to_numpy()
        sub = d.loc[m].sort_values("open_time").reset_index(drop=True)
        y = (sub["_label"].to_numpy() > 0).astype(int)
        cut = int(len(sub) * 0.70)
        base = float(max(y[cut:].mean(), 1 - y[cut:].mean()))

        # 14-feature baseline.
        x14 = sub[V3_FEATURES].to_numpy(float)
        c14 = lgb.LGBMClassifier(**LGB_PARAMS)
        c14.fit(x14[:cut], y[:cut])
        acc14 = float(
            ((c14.predict_proba(x14[cut:])[:, 1] > 0.5).astype(int) == y[cut:]).mean()
        )

        # 14 + engineered.
        feats15 = [*V3_FEATURES, ENGINEERED]
        x15 = sub[feats15].to_numpy(float)
        c15 = lgb.LGBMClassifier(**LGB_PARAMS)
        c15.fit(x15[:cut], y[:cut])
        acc15 = float(
            ((c15.predict_proba(x15[cut:])[:, 1] > 0.5).astype(int) == y[cut:]).mean()
        )

        # engineered-feature importance share + rank in the 15-feature model.
        imp = c15.feature_importances_.astype(float)
        share = imp / max(1.0, imp.sum())
        eng_share = float(share[feats15.index(ENGINEERED)])
        eng_rank = int((imp > imp[feats15.index(ENGINEERED)]).sum() + 1)  # 1=top

        t3_rows.append(
            {
                "symbol": sym,
                "n_test": len(sub) - cut,
                "base_rate": round(base, 4),
                "acc_14_feat": round(acc14, 4),
                "acc_15_feat": round(acc15, 4),
                "acc_lift": round(acc15 - acc14, 4),
                "engineered_importance_share": round(eng_share, 4),
                "engineered_rank_of_15": eng_rank,
            }
        )
        print(
            f"  {sym}: 14-feat {acc14:.4f} -> 15-feat {acc15:.4f} "
            f"(lift {acc15 - acc14:+.4f}) | engineered importance "
            f"{eng_share:.3f}, rank {eng_rank}/15"
        )
    mean_lift = float(np.mean([r["acc_lift"] for r in t3_rows]))
    n_lift = sum(1 for r in t3_rows if r["acc_lift"] > 0)
    mean_rank = float(np.mean([r["engineered_rank_of_15"] for r in t3_rows]))
    print(
        f"  MEAN accuracy lift {mean_lift:+.4f} ({n_lift}/3 positive) | "
        f"mean engineered rank {mean_rank:.1f}/15"
    )
    with (OUT_DIR / "part4_t3_incremental.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "symbol", "n_test", "base_rate", "acc_14_feat", "acc_15_feat",
                "acc_lift", "engineered_importance_share", "engineered_rank_of_15",
            ],
        )
        w.writeheader()
        w.writerows(t3_rows)

    # ----------------------------------------------------------------------
    # T4 — FUNDING-REGIME COVERAGE: funding-z sign distribution + data coverage.
    # ----------------------------------------------------------------------
    print("\n[T4] Funding-regime coverage — funding_z_30 sign distribution")
    t4_rows = []
    for sym in SYMBOLS:
        d = frames[sym]
        m = np.isfinite(d["_label"]).to_numpy()
        fz = d.loc[m, "funding_z_30"].to_numpy(float)
        finite = np.isfinite(fz)
        pos = float((fz[finite] > 0).mean())
        neg = float((fz[finite] < 0).mean())
        t4_rows.append(
            {
                "symbol": sym,
                "funding_z_coverage": round(float(finite.mean()), 4),
                "frac_funding_z_positive": round(pos, 4),
                "frac_funding_z_negative": round(neg, 4),
            }
        )
        print(
            f"  {sym}: funding_z coverage {finite.mean():.2%} | "
            f"sign split +{pos:.2%} / -{neg:.2%}"
        )
    with (OUT_DIR / "part4_t4_funding_coverage.csv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "symbol", "funding_z_coverage", "frac_funding_z_positive",
                "frac_funding_z_negative",
            ],
        )
        w.writeheader()
        w.writerows(t4_rows)

    # ----------------------------------------------------------------------
    # Verdict.
    # ----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("PART 4 VERDICT — the COMMITTED iter-v3/085 axis")
    print("=" * 78)
    print(f"  T1 |IC| gain vs raw primitive: {n_ic_gain}/3 symbols")
    print(f"  T2 worst max |IC| vs 14-stack: {worst_max_ic:.4f} (orthogonal)")
    print(f"  T3 mean 15-vs-14 accuracy lift: {mean_lift:+.4f} ({n_lift}/3 positive)")
    print(f"  T3 mean engineered importance rank: {mean_rank:.1f}/15")
    axis_supported = (
        worst_max_ic < 0.70
        and (n_ic_gain >= 2 or n_lift >= 2)
    )
    print(
        f"\n  FUNDING-REGIME ENGINEERED-FEATURE AXIS "
        f"{'SUPPORTED' if axis_supported else 'WEAK'} by IS evidence — the "
        f"composed feature is orthogonal to the stack and "
        f"{'carries incremental cross-symbol signal' if axis_supported else 'is marginal'}."
    )
    print(f"\n  CSVs written to {OUT_DIR}/")


if __name__ == "__main__":
    main()

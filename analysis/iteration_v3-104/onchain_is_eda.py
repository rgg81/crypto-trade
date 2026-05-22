"""iter-v3/104 — deep multi-angle IS-only EDA — ON-CHAIN NETWORK-ACTIVITY edge source.

THE AXIS. iter-v3/104's new edge source is on-chain network activity — a
genuinely non-price-derived information layer. Funding rates (/019/023/024/082/085),
perp-spot basis (/086), and the OI/funding/basis derivatives panel (/093) are all
CLOSED for v3. Liquidation snapshots were probed at the data-feasibility step and
found NOT obtainable (Binance removed `data.binance.vision .../liquidationSnapshot/`;
`/fapi/v1/allForceOrders` returns HTTP 400). On-chain network-activity is the
feasible new source — see `fetch_onchain.py` docstring for the full feasibility log.

THE CANDIDATE FEATURE (one variable, per the v3 one-variable EXPLORATION discipline):
    `btc_adract_growth_14d` — the 14-day log-growth of BTC active-address count,
    z-scored over a trailing 90-day window. BTC active-address growth is a
    canonical on-chain demand/regime proxy: rising address activity = expanding
    network demand (risk-on); contracting activity = retreating demand (risk-off).
    Because the entire v3 altcoin book (BCH+LDO+TRX) is BTC-regime-driven, BTC's
    on-chain activity is used as a CROSS-ASSET REGIME BROADCAST — the same design
    as the incumbent `btc_ret_14d` cross-asset feature, but sourced from the
    blockchain instead of from price, so it is genuinely orthogonal information.

This script ALSO measures the per-own-chain variants (bch on Bitcoin-Cash L1,
trx on Tron L1) and the TxCnt-based variants, so the brief can select the single
strongest candidate on IS-predictive evidence — but only ONE goes into the brief.

LOOK-AHEAD DISCIPLINE — the load-bearing design:
    A daily on-chain metric for UTC day D aggregates all blocks of day D and is
    only knowable after 24:00 UTC on D. We assign day D's metric to the FIRST 8h
    candle whose open_time is strictly AFTER D's 24:00 close — i.e. a +1-day
    publication lag, then a forward-fill onto the 8h grid. Concretely: the
    on-chain value carried at 8h bar t is the metric of the most recent UTC day
    that had FULLY CLOSED before t's open_time. No same-day or future on-chain
    information can enter bar t. This is implemented in `attach_onchain()` and
    asserted by `_assert_causal()`.

IS-ONLY: every row entering any IC / sign-stability / importance / redundancy
computation has open_time < OOS_CUTOFF_MS. The post-cutoff OOS is NEVER read.

Evidence standard is IS-PREDICTIVE (the /102 lesson — a held-out-tail OOS-leaning
proxy does not predict the multi-seed IS fit). All four screens — directional IC
vs the /059 triple-barrier label, IS sub-period (half + quartile) sign-stability,
IS-fold LightGBM gain-importance, and incumbent redundancy — are strictly IS-only
and directly predictive of what a multi-seed IS Optuna fit consumes.

Outputs (analysis/iteration_v3-104/):
    T1_is_panel_summary.csv      — per-symbol IS row counts, on-chain coverage
    T2_onchain_directional_ic.csv — feature->label Spearman IC, per symbol + agg
    T3_subperiod_stability.csv   — half-split + quartile sign-stability
    T4_incumbent_redundancy.csv  — max |Spearman IC| vs the 14 incumbents
    T5_isfold_importance.csv     — IS-fold LightGBM gain-rank of 15
    T6_screen_verdict.csv        — consolidated GO / NO-GO verdict per candidate
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from crypto_trade.strategies.ml.labeling import label_trades  # noqa: E402

# ---------------------------------------------------------------------------
# Sacred constants — IMMUTABLE. Identical to config.py.
# ---------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC
ATR_TP, ATR_SL = 2.0, 1.0  # /059 triple-barrier multipliers
TIMEOUT_MIN = 21 * 8 * 60  # 21 candles * 8h — /059 timeout = 10080 min
FEE_PCT = 0.1

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
# Map each symbol to its own base chain (None if no own L1).
OWN_CHAIN = {"BCHUSDT": "bch", "LDOUSDT": None, "TRXUSDT": "trx"}

INCUMBENTS = [
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
]

ROOT = Path(__file__).resolve().parents[2]
FEAT_DIR = ROOT / "data" / "features_v3"
KLINE_DIR = ROOT / "data"
ONCHAIN_DIR = ROOT / "data" / "onchain"
OUT = Path(__file__).resolve().parent
EIGHT_H_MS = 8 * 60 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000

# Hard redundancy gate (v3 Critic Check 4 — IC < 0.7 between feature families).
REDUNDANCY_GATE = 0.70


# ---------------------------------------------------------------------------
# On-chain feature construction — past-only, publication-lagged.
# ---------------------------------------------------------------------------
def load_onchain(asset: str) -> pd.DataFrame:
    """Load the raw daily on-chain series for one asset."""
    df = pd.read_csv(ONCHAIN_DIR / f"{asset}_daily.csv", parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_daily_features(asset: str) -> pd.DataFrame:
    """Build the candidate on-chain features at DAILY resolution.

    Each feature is computed strictly past-only on the daily series:
      - <metric>_growth_14d : log(metric_D / metric_{D-14})
      - <metric>_growth_14d z-scored over a trailing 90-day window, shifted by
        1 day so day D's own value never enters its own z-score denominator.

    The returned frame is keyed by `date` (the UTC day the metric describes).
    The publication lag onto the 8h grid is applied later in attach_onchain().
    """
    raw = load_onchain(asset)
    out = pd.DataFrame({"date": raw["date"]})
    for metric in ("AdrActCnt", "TxCnt"):
        if metric not in raw.columns:
            continue
        s = raw[metric].astype(float).clip(lower=1.0)  # guard log of 0
        g14 = np.log(s / s.shift(14))
        # Trailing 90-day z-score; .shift(1) so day D excluded from its own stats.
        roll = g14.shift(1).rolling(90, min_periods=60)
        z = (g14 - roll.mean()) / roll.std()
        tag = "adract" if metric == "AdrActCnt" else "txcnt"
        out[f"{asset}_{tag}_growth_14d"] = g14
        out[f"{asset}_{tag}_growth_14d_z90"] = z
    return out


def attach_onchain(kl: pd.DataFrame, daily_feats: list[pd.DataFrame]) -> pd.DataFrame:
    """As-of merge daily on-chain features onto the 8h kline grid with a
    +1-day publication lag.

    Day D's metric is knowable only after 24:00 UTC on D. We therefore make
    day D's row available from timestamp (D's 24:00) onward by setting the
    merge key to `date + 1 day` (00:00 UTC of D+1) and using a backward as-of
    merge: 8h bar t receives the metric of the most recent day whose
    (date + 1 day) <= t.open_time. Because t.open_time is strictly increasing
    on the 8h grid and the on-chain key is (D's close), bar t can only ever see
    days that fully closed before it.
    """
    df = kl.copy()
    # Force nanosecond resolution on both sides — merge_asof requires the join
    # keys to have an identical datetime dtype.
    df["_ts"] = pd.to_datetime(df["open_time"], unit="ms").astype("datetime64[ns]")
    df = df.sort_values("_ts").reset_index(drop=True)
    for feats in daily_feats:
        f = feats.copy()
        # Publication-available timestamp = 00:00 UTC of D+1 (i.e. D's 24:00).
        f["_avail"] = (f["date"] + pd.Timedelta(days=1)).astype("datetime64[ns]")
        f = f.drop(columns=["date"]).sort_values("_avail").reset_index(drop=True)
        df = pd.merge_asof(
            df, f, left_on="_ts", right_on="_avail", direction="backward"
        )
        df = df.drop(columns=["_avail"])
    return df.drop(columns=["_ts"])


def _assert_causal(kl: pd.DataFrame, daily: pd.DataFrame, col: str, asset: str) -> None:
    """Adversarial causality check: re-attach with 60 future on-chain days
    deleted; the in-IS feature column must be byte-identical. If deleting
    future on-chain data changes any past feature value, there is a leak.
    """
    full = attach_onchain(kl, [daily])
    cut_daily = daily.iloc[:-60].copy()  # drop the 60 most-recent days
    cut = attach_onchain(kl, [cut_daily])
    mask = kl["open_time"] < OOS_CUTOFF_MS
    # Compare only rows the truncation cannot legitimately affect: those whose
    # open_time predates the earliest deleted day's publication time.
    last_kept_avail = (cut_daily["date"].max() + pd.Timedelta(days=1))
    safe = mask & (pd.to_datetime(kl["open_time"], unit="ms") <= last_kept_avail)
    a = full.loc[safe, col].to_numpy()
    b = cut.loc[safe, col].to_numpy()
    both = ~(np.isnan(a) | np.isnan(b))
    diff = np.abs(a[both] - b[both]).max() if both.any() else 0.0
    assert diff == 0.0, f"{asset}/{col}: CAUSALITY LEAK max_abs_diff={diff}"


# ---------------------------------------------------------------------------
# Triple-barrier label — byte-identical to /059 (ATR 2.0/1.0, 21-candle timeout).
# ---------------------------------------------------------------------------
def compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Wilder ATR — past-only. Matches the v3 labeling ATR."""
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close),
                                           np.abs(low - prev_close)))
    atr = np.full(len(tr), np.nan)
    if len(tr) > period:
        atr[period] = tr[1 : period + 1].mean()
        for i in range(period + 1, len(tr)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def label_panel(kl: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Run the /059 triple-barrier label over the full kline panel.

    Returns a frame with open_time, label (1/-1), and `signed_pnl` = the
    direction-aware net PnL the label implies (long_pnl if label==1 else
    short_pnl). The directional IC is computed against `signed_pnl`'s sign-
    weighted continuous form so the screen tests genuine predictive direction.
    """
    df = kl.copy()
    df["symbol"] = symbol
    if "close_time" not in df.columns:
        df["close_time"] = df["open_time"] + EIGHT_H_MS - 1
    atr = compute_atr(df, 14)
    valid = np.where(~np.isnan(atr))[0]
    labels, weights, long_pnl, short_pnl = label_trades(
        master=df,
        candidate_indices=valid,
        tp_pct=ATR_TP,
        sl_pct=ATR_SL,
        timeout_minutes=TIMEOUT_MIN,
        fee_pct=FEE_PCT,
        atr_values=atr,
    )
    res = pd.DataFrame({
        "open_time": df["open_time"].to_numpy()[valid],
        "label": labels,
        "long_pnl": long_pnl,
        "short_pnl": short_pnl,
    })
    # The forward triple-barrier outcome best summarized for an IC test as the
    # signed best-direction PnL: a feature is predictive if it correlates with
    # which direction (and how strongly) the next 21 candles reward.
    res["fwd_signed"] = res["long_pnl"] - res["short_pnl"]
    return res


# ---------------------------------------------------------------------------
# Main EDA.
# ---------------------------------------------------------------------------
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # Build daily on-chain features once per asset.
    daily_btc = build_daily_features("btc")
    daily_bch = build_daily_features("bch")
    daily_trx = build_daily_features("trx")
    daily_by_asset = {"btc": daily_btc, "bch": daily_bch, "trx": daily_trx}

    # The candidate feature columns we will screen. BTC variants are the
    # cross-asset broadcast (apply to every symbol); own-chain variants apply
    # only to the symbol whose chain they describe.
    btc_cands = ["btc_adract_growth_14d_z90", "btc_txcnt_growth_14d_z90"]

    t1_rows, t2_rows, t3_rows, t4_rows, t5_rows = [], [], [], [], []

    # Per-symbol assembled panels (IS-masked), kept for the IS-fold importance.
    panels: dict[str, pd.DataFrame] = {}

    for sym in SYMBOLS:
        kl = pd.read_csv(KLINE_DIR / sym / "8h.csv")
        feat = pd.read_parquet(FEAT_DIR / f"{sym}_8h_features.parquet")
        # Merge incumbents onto the kline frame by open_time.
        feat_cols = ["open_time"] + [c for c in INCUMBENTS if c in feat.columns]
        kl = kl.merge(feat[feat_cols], on="open_time", how="left")

        # On-chain feeds for this symbol: BTC broadcast + own chain (if any).
        feeds = [daily_btc]
        own = OWN_CHAIN[sym]
        if own is not None:
            feeds.append(daily_by_asset[own])
        kl_oc = attach_onchain(kl, feeds)

        # Candidate columns present for THIS symbol.
        sym_cands = list(btc_cands)
        if own is not None:
            sym_cands += [f"{own}_adract_growth_14d_z90", f"{own}_txcnt_growth_14d_z90"]

        # Causality assertions — adversarial leak check on every candidate.
        for c in btc_cands:
            _assert_causal(kl, daily_btc, c, "btc")
        if own is not None:
            for tag in ("adract", "txcnt"):
                _assert_causal(kl, daily_by_asset[own],
                               f"{own}_{tag}_growth_14d_z90", own)

        # Labels (full panel) then IS mask.
        lab = label_panel(kl, sym)
        kl_oc = kl_oc.merge(lab[["open_time", "fwd_signed"]], on="open_time", how="left")
        is_mask = kl_oc["open_time"] < OOS_CUTOFF_MS
        panel = kl_oc.loc[is_mask].reset_index(drop=True)
        panels[sym] = panel

        # T1 — panel summary.
        cov = {}
        for c in sym_cands:
            cov[c] = float(panel[c].notna().mean())
        t1_rows.append({
            "symbol": sym, "is_rows": int(is_mask.sum()),
            "is_first": pd.to_datetime(panel["open_time"].min(), unit="ms").date(),
            "is_last": pd.to_datetime(panel["open_time"].max(), unit="ms").date(),
            "label_coverage": float(panel["fwd_signed"].notna().mean()),
            "min_oc_coverage": round(min(cov.values()), 4),
        })

        # T2 — directional Spearman IC vs the /059 triple-barrier fwd_signed.
        for c in sym_cands:
            sub = panel[[c, "fwd_signed"]].dropna()
            if len(sub) < 50:
                ic, p = np.nan, np.nan
            else:
                ic, p = spearmanr(sub[c], sub["fwd_signed"])
            t2_rows.append({"symbol": sym, "candidate": c, "n": len(sub),
                            "ic": round(float(ic), 5) if ic == ic else np.nan,
                            "p_value": round(float(p), 5) if p == p else np.nan})

        # T3 — IS sub-period sign-stability: half-split and quartile.
        for c in sym_cands:
            sub = panel[[c, "fwd_signed", "open_time"]].dropna().reset_index(drop=True)
            if len(sub) < 100:
                continue
            n = len(sub)
            halves, quarts = [], []
            for k in range(2):
                seg = sub.iloc[k * n // 2 : (k + 1) * n // 2]
                if len(seg) >= 30:
                    halves.append(np.sign(spearmanr(seg[c], seg["fwd_signed"])[0]))
            for k in range(4):
                seg = sub.iloc[k * n // 4 : (k + 1) * n // 4]
                if len(seg) >= 25:
                    quarts.append(np.sign(spearmanr(seg[c], seg["fwd_signed"])[0]))
            t3_rows.append({
                "symbol": sym, "candidate": c,
                "half_signs": "".join("+" if s > 0 else "-" for s in halves),
                "quartile_signs": "".join("+" if s > 0 else "-" for s in quarts),
                "half_stable": len(set(halves)) == 1,
                "quartile_stable": len(set(quarts)) == 1,
            })

        # T4 — incumbent redundancy: max |Spearman IC| vs the 14 incumbents.
        present_inc = [c for c in INCUMBENTS if c in panel.columns]
        for c in sym_cands:
            best_ic, best_inc = 0.0, ""
            for inc in present_inc:
                sub = panel[[c, inc]].dropna()
                if len(sub) < 50:
                    continue
                r = abs(spearmanr(sub[c], sub[inc])[0])
                if r == r and r > best_ic:
                    best_ic, best_inc = r, inc
            t4_rows.append({
                "symbol": sym, "candidate": c,
                "max_abs_ic_vs_incumbent": round(best_ic, 4),
                "nearest_incumbent": best_inc,
                "passes_0.70_gate": best_ic < REDUNDANCY_GATE,
            })

    # T5 — IS-fold LightGBM gain-importance: for each symbol fit a depth-4
    # LightGBM (the v3 architecture) on 14 incumbents + ONE candidate, on a
    # chronological 70/30 IS split. The gain rank of the candidate among 15 is
    # the direct IS-predictive test — does the tree allocate split capacity?
    try:
        import lightgbm as lgb
        have_lgb = True
    except ImportError:
        have_lgb = False

    if have_lgb:
        for sym in SYMBOLS:
            panel = panels[sym]
            present_inc = [c for c in INCUMBENTS if c in panel.columns]
            own = OWN_CHAIN[sym]
            sym_cands = list(btc_cands)
            if own is not None:
                sym_cands += [f"{own}_adract_growth_14d_z90",
                              f"{own}_txcnt_growth_14d_z90"]
            # Binary direction target from the /059 label sign.
            y_all = (panel["fwd_signed"] > 0).astype(int)
            for cand in sym_cands:
                cols = present_inc + [cand]
                df = panel[cols + ["fwd_signed"]].dropna().reset_index(drop=True)
                if len(df) < 200:
                    t5_rows.append({"symbol": sym, "candidate": cand,
                                    "gain_rank_of_15": np.nan, "gain_share_pct": np.nan,
                                    "n_train": len(df), "note": "panel too thin"})
                    continue
                y = (df["fwd_signed"] > 0).astype(int)
                X = df[cols]
                split = int(len(df) * 0.70)
                model = lgb.LGBMClassifier(
                    num_leaves=15, max_depth=4, n_estimators=200,
                    learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                    random_state=42, n_jobs=1, verbose=-1,
                )
                model.fit(X.iloc[:split], y.iloc[:split])
                gains = pd.Series(model.booster_.feature_importance(
                    importance_type="gain"), index=cols)
                ranked = gains.sort_values(ascending=False)
                rank = list(ranked.index).index(cand) + 1
                share = 100.0 * gains[cand] / gains.sum() if gains.sum() > 0 else 0.0
                t5_rows.append({
                    "symbol": sym, "candidate": cand,
                    "gain_rank_of_15": rank,
                    "gain_share_pct": round(float(share), 4),
                    "n_train": split, "above_parity_6.67pct": share > 100.0 / 15,
                    "note": "",
                })

    # Write tables.
    pd.DataFrame(t1_rows).to_csv(OUT / "T1_is_panel_summary.csv", index=False)
    t2 = pd.DataFrame(t2_rows)
    t2.to_csv(OUT / "T2_onchain_directional_ic.csv", index=False)
    pd.DataFrame(t3_rows).to_csv(OUT / "T3_subperiod_stability.csv", index=False)
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_incumbent_redundancy.csv", index=False)
    t5 = pd.DataFrame(t5_rows)
    t5.to_csv(OUT / "T5_isfold_importance.csv", index=False)

    # T6 — consolidated verdict. A candidate is GO only if, across all
    # applicable symbols: |IC| meaningfully non-zero AND sign-consistent, AND
    # quartile-sign-stable on the IS engine, AND passes the 0.70 redundancy
    # gate, AND the IS-fold LightGBM allocates ABOVE-PARITY gain (not INERT).
    verdict_rows = []
    all_cands = sorted(set(t2["candidate"]))
    for cand in all_cands:
        ic_rows = t2[t2["candidate"] == cand]
        mean_abs_ic = float(np.nanmean(np.abs(ic_rows["ic"])))
        signs = set(np.sign(ic_rows["ic"].dropna()))
        sign_consistent = len(signs) == 1
        t3c = pd.DataFrame(t3_rows)
        t3c = t3c[t3c["candidate"] == cand]
        # IS-engine symbols carry ~99% of /059 IS PnL: BCH + TRX.
        eng = t3c[t3c["symbol"].isin(["BCHUSDT", "TRXUSDT"])]
        quart_stable_engine = bool(eng["quartile_stable"].all()) if len(eng) else False
        t4c = t4[t4["candidate"] == cand]
        redundancy_ok = bool(t4c["passes_0.70_gate"].all()) if len(t4c) else False
        t5c = t5[t5["candidate"] == cand]
        if len(t5c):
            eng5 = t5c[t5c["symbol"].isin(["BCHUSDT", "TRXUSDT"])]
            above_parity_engine = bool(
                eng5["above_parity_6.67pct"].fillna(False).all()
            ) if len(eng5) else False
            best_rank = float(np.nanmin(t5c["gain_rank_of_15"]))
        else:
            above_parity_engine, best_rank = False, np.nan
        go = (mean_abs_ic >= 0.02 and sign_consistent and quart_stable_engine
              and redundancy_ok and above_parity_engine)
        verdict_rows.append({
            "candidate": cand,
            "mean_abs_ic": round(mean_abs_ic, 5),
            "ic_sign_consistent": sign_consistent,
            "quartile_stable_on_engine": quart_stable_engine,
            "redundancy_ok": redundancy_ok,
            "isfold_above_parity_engine": above_parity_engine,
            "best_gain_rank_of_15": best_rank,
            "VERDICT": "GO" if go else "NO-GO",
        })
    pd.DataFrame(verdict_rows).to_csv(OUT / "T6_screen_verdict.csv", index=False)

    # Console summary.
    print("=== T1 IS panel summary ===")
    print(pd.DataFrame(t1_rows).to_string(index=False))
    print("\n=== T2 directional IC ===")
    print(t2.to_string(index=False))
    print("\n=== T3 sub-period sign-stability ===")
    print(pd.DataFrame(t3_rows).to_string(index=False))
    print("\n=== T4 incumbent redundancy ===")
    print(t4.to_string(index=False))
    print("\n=== T5 IS-fold LightGBM gain-importance ===")
    print(t5.to_string(index=False))
    print("\n=== T6 consolidated verdict ===")
    print(pd.DataFrame(verdict_rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

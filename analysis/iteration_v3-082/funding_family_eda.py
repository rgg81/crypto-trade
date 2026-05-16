"""iter-v3/082 EDA — Funding-rate FEATURE FAMILY (cycle-3 EXPLORATION #1, Direction 1).

STRICTLY IS-ONLY. Every computation in this script is masked to open_time <
OOS_CUTOFF_MS (2025-03-24). No OOS column is read, ranked, or filtered on. The
QR sees OOS only in Phase 7. (feedback_no_cheating.md Vector 1+2.)

PURPOSE
-------
Cycle-3 plan Direction 1: bring a NEW crypto-native feature family into v3. v3's
14-feature stack is entirely price/return/vol/regime from OHLCV — zero crypto-
native alpha. The 8h candle is exactly one Binance funding-settlement period.

The funding-rate AXIS has a closed precedent: iter-v3/019/023/024 added a SINGLE
feature `funding_rate_zscore_30` (a rolling z-score) and it ranked 14/14 across
all 3 symbols at every Optuna budget. PERMANENTLY CLOSED at catalog level.

This EDA asks a DIFFERENT question. The /019/023/024 z-score discards the two
properties the literature says carry funding's predictive content:
  - SIGN + LEVEL of funding (persistent crowding) — a z-score is mean-zero by
    construction, so it cannot encode "funding has been positive for 30 bars".
  - FUNDING-PRICE DIVERGENCE (price stalls while funding stays extended — the
    "crowded at the high" reversal signature; Phemex/CFB 2024, MDPI 14(2)346).
A z-score of funding answers only "is funding unusual vs its own recent mean".

This EDA constructs a 5-feature funding FAMILY that encodes sign, level,
persistence, momentum, and funding-price divergence — and tests, IS-only:
  T1. Family-vs-label IC (triple-barrier label proxy) — does ANY family member
      carry signed predictive content the single z-score lacked?
  T2. Intra-family + cross-family IC — is the family orthogonal to the 14
      anchor features (Critic Check 4, |IC| < 0.70)? Is it internally diverse?
  T3. Conditional information — IS-only, does conditioning on the family member
      separate the forward-return distribution (the test the single z-score
      FAILED)?
  T4. Baseline-trade attribution — on the /081 IS trade roster, do the funding
      family values at entry separate winners from losers? This is the
      EDA-driven axis-justification per feedback_v3_axis_selection_quant_discipline.md.
  T5. ADF stationarity of every family member (Critic Check 5).
  T6. Holding-time orthogonality argument (feedback_v3_is_oos_regime_divergence.md):
      a feature axis touches no barrier — but per /076 it can still load the
      regime factor via trade SELECTION. T6 measures the family's marginal
      correlation with the IS/OOS calendar label as the necessary (not
      sufficient) screen; the conditional test is pre-registered for Phase 6.

OUTPUT — all tables printed and written to analysis/iteration_v3-082/:
  t1_family_label_ic.csv
  t2_ic_matrix.csv
  t3_conditional_separation.csv
  t4_baseline_trade_attribution.csv
  t5_adf.csv
  t6_regime_marginal_corr.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

OUT = Path("analysis/iteration_v3-082")
OUT.mkdir(parents=True, exist_ok=True)

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — SACRED, immutable
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
FEATURES_DIR = Path("data/features_v3")
FUNDING_DIR = Path("data/funding_rates")

# The 14 anchor features (BASELINE_V3.md /059) — orthogonality target for T2.
ANCHOR_14 = (
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

# Funding-window constants. 8h cadence: 3 bars/day.
W_MOM = 3  # 1-day funding momentum (sum of last 3 settlements)
W_PERSIST = 9  # 3-day sign-persistence window
W_DIV = 6  # 2-day window for funding-price divergence
ATR_TP, ATR_SL, TIMEOUT = 2.0, 1.0, 21  # v3 triple-barrier params (BASELINE_V3.md)


# =====================================================================
# Funding FAMILY construction — all past-only, look-ahead-clean.
# =====================================================================
def build_funding_family(kline: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    """Merge funding into kline and build the 5-member funding family.

    Look-ahead discipline (identical convention to funding_v3.py): the funding
    rate AT bar t SETTLED at candle open_time T (broadcast ~5 min before the 8h
    boundary), so rate[t] is knowable at bar t open. Every rolling stat that
    feeds a feature is .shift(1)-lagged so bar t's own rate never enters its
    own rolling denominator/window — EXCEPT where the raw rate[t] level itself
    is the feature (sign/level), which is past-only by the broadcast convention.
    """
    k = kline.copy()
    f = funding.copy()
    f["open_time_aligned"] = (f["funding_time"] // 60_000) * 60_000
    k["open_time_aligned"] = (k["open_time"] // 60_000) * 60_000
    m = k.merge(f[["open_time_aligned", "funding_rate"]], on="open_time_aligned", how="left").drop(
        columns=["open_time_aligned"]
    )
    m.index = k.index
    r = m["funding_rate"].astype(float)

    out = pd.DataFrame(index=k.index)
    out["open_time"] = k["open_time"].values

    # --- F1: funding_sign_persist_9 ---------------------------------------
    # Net sign agreement over the trailing 9 settlements (3 days). Encodes
    # CROWDING DIRECTION + PERSISTENCE — the property a mean-zero z-score
    # structurally cannot carry. Range ~[-1, +1]. Past-only: .shift(1) so the
    # window is [t-9, t-1]; bar t's own settlement is excluded.
    sign = np.sign(r)
    out["funding_sign_persist_9"] = sign.shift(1).rolling(W_PERSIST, min_periods=W_PERSIST).mean()

    # --- F3: funding_momentum_3 -------------------------------------------
    # 1-day funding momentum = rate[t] minus rate[t-3] (one day earlier).
    # Rising funding into a position = leverage building. rate[t] is past-only
    # by broadcast; rate[t-3] trivially so.
    out["funding_momentum_3"] = r - r.shift(W_MOM)

    # --- F4: funding_accel_3 ----------------------------------------------
    # Funding ACCELERATION = momentum[t] - momentum[t-3]. Second difference.
    # Captures inflection in leverage build (BIS WP 1087: carry SHOCKS, not
    # carry levels, predict liquidation jumps). Past-only by F3 construction.
    mom = r - r.shift(W_MOM)
    out["funding_accel_3"] = mom - mom.shift(W_MOM)

    # --- F5: funding_price_divergence_6 -----------------------------------
    # The "crowded at the high" reversal signature, CONTINUOUS form. Trailing
    # 6-bar cumulative funding z-scored against its own 60-bar history, MINUS
    # the 6-bar price return z-scored against its own 60-bar history. When
    # funding crowding is extended but price is NOT making matching progress,
    # the divergence is large — the unwind setup. A continuous z-difference is
    # strictly more informative than the 3-valued sign difference and gives
    # LightGBM a real split gradient. Both legs .shift(1)-lagged → past-only.
    cum_fund = r.shift(1).rolling(W_DIV, min_periods=W_DIV).sum()
    cf_z = (cum_fund - cum_fund.rolling(60, min_periods=60).mean()) / (
        cum_fund.rolling(60, min_periods=60).std(ddof=1).replace(0, np.nan)
    )
    logc = np.log(k["close"].astype(float))
    price_ret_6 = (logc - logc.shift(W_DIV)).shift(1)
    pr_z = (price_ret_6 - price_ret_6.rolling(60, min_periods=60).mean()) / (
        price_ret_6.rolling(60, min_periods=60).std(ddof=1).replace(0, np.nan)
    )
    out["funding_price_divergence_6"] = (cf_z - pr_z).clip(-10.0, 10.0)

    return out


# FAMILY — pruned to 4 genuinely-diverse members. The EDA's first pass exposed
# funding_sign_persist_9 ~ funding_level_ewm_9 at intra-IC 0.91 (BCH) / 0.92
# (TRX) — near-collinear. Per the iter-v3/070-era lesson + feedback_v3_
# engineered_features_dont_stack.md, two near-collinear features waste
# colsample_bytree picks. funding_level_ewm_9 is DROPPED (the signed EWM level
# is dominated by the sign-persistence measure, which is the cleaner
# crowding-direction encoding and the one the literature emphasises).
FAMILY = (
    "funding_sign_persist_9",  # crowding direction + persistence
    "funding_momentum_3",  # 1-day funding momentum
    "funding_accel_3",  # funding acceleration (carry SHOCK; BIS WP 1087)
    "funding_price_divergence_6",  # funding-price divergence (reversal setup)
)


# =====================================================================
# Triple-barrier label proxy — IS-only. Used for IC tests T1/T3.
# Past-only barriers (ATR from past data) — same convention as the runner's
# labeller; this is a SCREEN proxy (fixed ATR multipliers, no Optuna).
# =====================================================================
def triple_barrier_label(df: pd.DataFrame) -> pd.Series:
    """Signed first-touch label: +1 TP-up, -1 TP-down, 0 timeout.

    ATR(14) computed on PAST data. For each bar t, scan forward up to TIMEOUT
    bars; first barrier touched sets the label sign. This labels the LONG-side
    forward distribution (the screen proxy); the production labeller is
    direction-aware, but a signed first-touch proxy is the standard IC screen.
    """
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()
    n = len(close)

    # ATR(14) — Wilder, past-only
    tr = np.maximum(
        high[1:] - low[1:],
        np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])),
    )
    tr = np.concatenate([[np.nan], tr])
    atr = pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()

    label = np.full(n, np.nan)
    for t in range(n):
        if np.isnan(atr[t]) or t + TIMEOUT >= n:
            continue
        entry = close[t]
        tp = entry + ATR_TP * atr[t]
        sl = entry - ATR_SL * atr[t]
        lab = 0
        for j in range(t + 1, min(t + 1 + TIMEOUT, n)):
            if high[j] >= tp:
                lab = 1
                break
            if low[j] <= sl:
                lab = -1
                break
        label[t] = lab
    return pd.Series(label, index=df.index)


def spearman(a: pd.Series, b: pd.Series) -> float:
    m = a.notna() & b.notna()
    if m.sum() < 100:
        return np.nan
    return float(a[m].rank().corr(b[m].rank()))


# =====================================================================
# MAIN
# =====================================================================
def main() -> None:
    print("=" * 78)
    print("iter-v3/082 EDA — Funding-rate FEATURE FAMILY (Direction 1, cycle-3 #1)")
    print("STRICTLY IS-ONLY (open_time < 2025-03-24). No OOS column read.")
    print("=" * 78)

    fam_by_sym: dict[str, pd.DataFrame] = {}
    label_by_sym: dict[str, pd.Series] = {}
    anchor_by_sym: dict[str, pd.DataFrame] = {}

    for sym in SYMBOLS:
        pq = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        fund = pd.read_csv(FUNDING_DIR / f"{sym}.csv")
        # IS mask — the only place the cutoff is applied; everything downstream
        # is IS-only by construction.
        pq_is = pq[pq["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        fam = build_funding_family(pq_is, fund)
        fam_by_sym[sym] = fam
        label_by_sym[sym] = triple_barrier_label(pq_is)
        anchor_by_sym[sym] = pq_is[list(ANCHOR_14)].reset_index(drop=True)
        cov = fam[list(FAMILY)].notna().mean()
        print(f"\n[{sym}] IS rows={len(pq_is)}  family non-NaN coverage:")
        for c in FAMILY:
            print(f"    {c:32s} {cov[c] * 100:5.1f}%")

    # -----------------------------------------------------------------
    # T1 — Family-vs-label IC (triple-barrier label proxy)
    # The single z-score's univariate rank-IC was 0.04-0.05 (diary /019).
    # Does ANY family member beat that materially?
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T1 — Funding-family vs triple-barrier-label Spearman IC (IS-only)")
    print("  (reference: /019 single funding_rate_zscore_30 univariate IC ~0.04-0.05)")
    print("=" * 78)
    t1_rows = []
    for sym in SYMBOLS:
        fam, lab = fam_by_sym[sym], label_by_sym[sym]
        row = {"symbol": sym}
        print(f"\n  [{sym}]")
        for c in FAMILY:
            ic = spearman(fam[c], lab)
            row[c] = ic
            flag = "  <-- |IC| materially > z-score baseline" if abs(ic) > 0.06 else ""
            print(f"    {c:32s} IC={ic:+.4f}{flag}")
        t1_rows.append(row)
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "t1_family_label_ic.csv", index=False)
    # Pooled IC across the 3 symbols
    print("\n  POOLED (3-symbol stacked) IC:")
    pooled_fam = pd.concat([fam_by_sym[s] for s in SYMBOLS], ignore_index=True)
    pooled_lab = pd.concat([label_by_sym[s] for s in SYMBOLS], ignore_index=True)
    for c in FAMILY:
        ic = spearman(pooled_fam[c], pooled_lab)
        print(f"    {c:32s} pooled IC={ic:+.4f}")

    # -----------------------------------------------------------------
    # T2 — IC matrix: intra-family + cross-family (vs 14 anchor)
    # Critic Check 4: |IC_pearson| < 0.70 between new and existing families.
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T2 — IC orthogonality: family vs 14 anchor features (Critic Check 4)")
    print("  hard gate |IC| < 0.70; strict target < 0.50")
    print("=" * 78)
    t2_rows = []
    for sym in SYMBOLS:
        fam, anc = fam_by_sym[sym], anchor_by_sym[sym]
        print(f"\n  [{sym}] max |IC| of each family member vs the 14 anchor features:")
        for c in FAMILY:
            ics = {a: spearman(fam[c], anc[a]) for a in ANCHOR_14}
            ics = {k: v for k, v in ics.items() if v == v}
            if not ics:
                continue
            amax = max(ics, key=lambda k: abs(ics[k]))
            t2_rows.append(
                {
                    "symbol": sym,
                    "family_feature": c,
                    "max_ic_anchor": amax,
                    "max_abs_ic": abs(ics[amax]),
                }
            )
            gate = "PASS" if abs(ics[amax]) < 0.70 else "FAIL"
            strict = "(< 0.50 strict OK)" if abs(ics[amax]) < 0.50 else "(>= 0.50)"
            print(f"    {c:32s} max|IC|={abs(ics[amax]):.3f} vs {amax:24s} {gate} {strict}")
        # intra-family
        print(f"  [{sym}] intra-family max |IC| (diversity check):")
        intra = []
        for i, a in enumerate(FAMILY):
            for b in FAMILY[i + 1 :]:
                ic = spearman(fam[a], fam[b])
                if ic == ic:
                    intra.append((a, b, ic))
        for a, b, ic in sorted(intra, key=lambda x: -abs(x[2]))[:3]:
            print(f"    {a:28s} ~ {b:28s} IC={ic:+.3f}")
    pd.DataFrame(t2_rows).to_csv(OUT / "t2_ic_matrix.csv", index=False)

    # -----------------------------------------------------------------
    # T3 — Conditional separation: does the family member SEPARATE the
    # forward-return distribution? This is the test the single z-score
    # FAILED (rank 14/14 = the model could not split usefully on it).
    # Forward return = log(close[t+TIMEOUT]/close[t]) — IS-only.
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T3 — Conditional fwd-return separation by funding-family terciles (IS-only)")
    print("  fwd return = 21-bar log return; measures top-tercile minus bottom-tercile")
    print("=" * 78)
    t3_rows = []
    for sym in SYMBOLS:
        pq = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        pq_is = pq[pq["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        logc = np.log(pq_is["close"].astype(float))
        fwd = logc.shift(-TIMEOUT) - logc  # forward 21-bar return
        fam = fam_by_sym[sym]
        print(f"\n  [{sym}]")
        for c in FAMILY:
            v = fam[c]
            m = v.notna() & fwd.notna()
            if m.sum() < 300:
                continue
            vv, ff = v[m], fwd[m]
            q1, q2 = vv.quantile(1 / 3), vv.quantile(2 / 3)
            bot = ff[vv <= q1].mean()
            top = ff[vv >= q2].mean()
            sep = top - bot
            t3_rows.append(
                {
                    "symbol": sym,
                    "feature": c,
                    "bot_tercile_fwd": bot,
                    "top_tercile_fwd": top,
                    "separation": sep,
                }
            )
            flag = "  <-- monotone separation" if abs(sep) > 0.012 else ""
            print(f"    {c:32s} bot={bot:+.4f}  top={top:+.4f}  sep={sep:+.4f}{flag}")
    pd.DataFrame(t3_rows).to_csv(OUT / "t3_conditional_separation.csv", index=False)

    # -----------------------------------------------------------------
    # T4 — Baseline-trade attribution (the EDA-driven axis justification).
    # On the /081 IS trade roster, do funding-family values at ENTRY
    # separate winning trades from losing trades? Per-symbol + per-side.
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T4 — /081 IS-trade winner/loser separation by funding family at entry")
    print("  (the bottleneck the axis must target — feedback_v3_axis_selection)")
    print("=" * 78)
    trades = pd.read_csv("reports-v3/iteration_v3-081/in_sample/trades.csv")
    # trades.csv `open_time` is the ENTRY-CANDLE close_time (ends ...999); the
    # entry candle's open_time = trade.open_time - 8h + 1ms. The trade is
    # decided on features computed at that entry candle (past-only).
    bar_ms = 28_800_000
    t4_rows = []
    for sym in SYMBOLS:
        tr = trades[trades["symbol"] == sym].copy()
        if len(tr) < 10:
            print(f"\n  [{sym}] only {len(tr)} IS trades — skipped")
            continue
        tr["entry_open_time"] = tr["open_time"] - bar_ms + 1
        fam = fam_by_sym[sym].copy()
        # map each trade's entry-candle open_time to family values at entry
        merged = tr.merge(
            fam, left_on="entry_open_time", right_on="open_time", how="left", suffixes=("", "_fam")
        )
        win = merged["net_pnl_pct"] > 0
        print(f"\n  [{sym}]  {len(merged)} IS trades, win rate {win.mean() * 100:.1f}%")
        for c in FAMILY:
            if c not in merged or merged[c].notna().sum() < 10:
                continue
            wv = merged.loc[win, c].mean()
            lv = merged.loc[~win, c].mean()
            gap = wv - lv
            t4_rows.append(
                {
                    "symbol": sym,
                    "feature": c,
                    "winner_mean": wv,
                    "loser_mean": lv,
                    "gap": gap,
                    "n_trades": len(merged),
                }
            )
            flag = (
                "  <-- winner/loser separation"
                if abs(gap) > 1e-9 and (abs(gap) / (abs(lv) + 1e-9) > 0.25)
                else ""
            )
            print(f"    {c:32s} winners={wv:+.4f}  losers={lv:+.4f}  gap={gap:+.4f}{flag}")
    pd.DataFrame(t4_rows).to_csv(OUT / "t4_baseline_trade_attribution.csv", index=False)

    # -----------------------------------------------------------------
    # T5 — ADF stationarity of each family member (Critic Check 5).
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T5 — ADF stationarity (Critic Check 5; p < 0.05 rejects unit root)")
    print("=" * 78)
    t5_rows = []
    for sym in SYMBOLS:
        fam = fam_by_sym[sym]
        print(f"\n  [{sym}]")
        for c in FAMILY:
            s = fam[c].dropna()
            if len(s) < 200:
                continue
            try:
                p = adfuller(s, autolag="AIC")[1]
            except Exception:  # noqa: BLE001
                p = np.nan
            t5_rows.append(
                {
                    "symbol": sym,
                    "feature": c,
                    "adf_p": p,
                    "stationary": (p is not None and p < 0.05),
                }
            )
            print(f"    {c:32s} ADF p={p:.2e}  {'STATIONARY' if p < 0.05 else 'NON-STATIONARY'}")
    pd.DataFrame(t5_rows).to_csv(OUT / "t5_adf.csv", index=False)

    # -----------------------------------------------------------------
    # T6 — Marginal regime-label correlation (necessary, not sufficient).
    # IS/OOS calendar label is constant 0 within IS — so the within-IS
    # proxy is the bull-month label (the /077 reframing: IS bull months
    # are the drag stratum). Correlate each family member with a within-IS
    # bull-regime indicator. A near-zero corr is the MARGINAL screen; the
    # CONDITIONAL (SHAP-vs-regime) test is pre-registered for Phase 6.
    # -----------------------------------------------------------------
    print("\n" + "=" * 78)
    print("T6 — Marginal corr with within-IS bull-regime label (/077 reframing)")
    print("  necessary not sufficient — conditional SHAP test pre-registered Phase 6")
    print("=" * 78)
    t6_rows = []
    for sym in SYMBOLS:
        pq = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        pq_is = pq[pq["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
        # bull-regime proxy: 270-bar SMA slope on close > 0 (past-only, .shift(1))
        logc = np.log(pq_is["close"].astype(float))
        sma = logc.rolling(270, min_periods=270).mean()
        bull = (sma.diff() > 0).astype(float).shift(1)
        fam = fam_by_sym[sym]
        print(f"\n  [{sym}]")
        for c in FAMILY:
            ic = spearman(fam[c], bull)
            t6_rows.append({"symbol": sym, "feature": c, "regime_marginal_ic": ic})
            flag = "  <-- |corr| elevated; conditional test critical" if (abs(ic) > 0.30) else ""
            print(f"    {c:32s} marginal regime IC={ic:+.4f}{flag}")
    pd.DataFrame(t6_rows).to_csv(OUT / "t6_regime_marginal_corr.csv", index=False)

    print("\n" + "=" * 78)
    print("EDA COMPLETE — tables written to analysis/iteration_v3-082/")
    print("=" * 78)


if __name__ == "__main__":
    main()

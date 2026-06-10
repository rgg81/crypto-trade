"""iter-v1/086 BUNDLE DIVERSIFICATION + STRUCTURE PRE-SCREEN (IS-only).

USER DIRECTIVE (2026-06-10): "next, pick a symbol with less correlation with the
symbols we have chosen for the bundle." Live bundle = BUNDLE-002 (tag v0.v1-082) =
{DOTUSDT, ETHUSDT, BTCUSDT, AAVEUSDT}. Rank the eligible candidate universe by LOW
8h log-return correlation with the bundle basket so the NEXT v1 SPECIALIST mines a
diversifying symbol.

STRICTLY IS-ONLY: every series is truncated to open_time < OOS_CUTOFF (2025-03-24).
OOS is NEVER read for selection. Correlations + GATE 1 are computed on IS bars only.

This intersects TWO criteria:
  (NEW)   diversification  — avg pairwise corr vs bundle, corr vs EW-bundle, and
          max single-member corr (flag a candidate that is low on average but
          tightly coupled to ONE member, which would not actually diversify).
  (carry) GATE 1 structure-eligibility from the /084-085 NEGATIVE-trivial-baseline
          selector (feedback_v1_negative_trivial_baseline_selector): trivial
          TS-momentum IS Sharpe over {5d=15bar, 21d=63bar, 50d=150bar}, fee-adj
          (0.05%/side, turnover-aware). gate1_pass = (min-horizon <= +0.15).
          The CRV lesson: a low GATE-1 baseline is the structural-headroom signal
          the ML head needs (a high trivial baseline means trend already captures
          the move, leaving no residual edge for the model). GATE 2 (LightGBM probe
          + label-IC) is DEFERRED to the next iteration's screen so this script does
          NOT compete with the running /085 UNI backtest for CPU.

GATE 1 replicated EXACTLY from analysis/iteration_v1-085/structure_prescreen_op.py:
  trivial_mom_sharpe(close, n): sign(close.pct_change(n)).shift(1) * bar_ret,
  fee 0.0005/side turnover-aware, annualized by sqrt(3*365).

ELIGIBLE UNIVERSE = USDT-perp with >=4y IS-eligible 8h data, MINUS:
  bundle members {DOT, ETH, BTC, AAVE}
  V1_EXCLUDED_SYMBOLS {SOL, XRP, DOGE, NEAR, BCH, LDO, TRX, BNB}
  already-FAILED mines {LINK, LTC, ATOM, ICP, FIL, CRV}
  UNIUSDT (mid-flight in /085)
  + obvious non-tradeable / delisted-collapse / settled / leveraged-token noise.
"""

import datetime as dt
import os

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (src/crypto_trade/config.py)
BARS_PER_DAY = 3
ANN = np.sqrt(BARS_PER_DAY * 365.0)
FEE = 0.0005  # 0.05% per side, turnover-aware (GATE 1)
HORIZONS = {"5d": 15, "21d": 63, "50d": 150}
MIN_IS_YEARS = 4.0
DATA_ROOT = "data"
OUT_DIR = "analysis/iteration_v1-086"

BUNDLE = ["DOTUSDT", "ETHUSDT", "BTCUSDT", "AAVEUSDT"]

V1_EXCLUDED = {"SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
               "BCHUSDT", "LDOUSDT", "TRXUSDT", "BNBUSDT"}
FAILED_MINES = {"LINKUSDT", "LTCUSDT", "ATOMUSDT", "ICPUSDT", "FILUSDT", "CRVUSDT"}
MIDFLIGHT = {"UNIUSDT"}

# Non-tradeable / delisted-collapse / settled / leveraged / stable noise to skip.
JUNK = {
    "LENDUSDT", "BZRXUSDT", "SRMUSDT", "DEFIUSDT", "YFIIUSDT", "BTSUSDT",
    "TOMOUSDT", "HNTUSDT", "BTCSTUSDT", "XEMUSDT", "DOTECOUSDT", "AKROUSDT",
    "REEFUSDT", "LINAUSDT", "STMXUSDT", "DENTUSDT", "RAYUSDT", "FTTUSDT",
    "CVCUSDT", "OCEANUSDT", "BELUSDT", "FLMUSDT", "RLCUSDT", "BLZUSDT",
    "LUNAUSDT",  # depeg collapse — non-stationary
}


# Tradeability gate: a candidate is only useful if it was still actively trading
# right up to the IS cutoff (so it is live-tradeable now and its IS-tail correlation
# is real, not a stale frozen-price artifact). UNFI/REN/OMG delisted from Binance
# futures BEFORE the cutoff -> their last IS bars have zero volume. Require the last
# nonzero-volume bar to land within DELIST_GRACE_MS of the cutoff.
DELIST_GRACE_MS = 30 * 86400 * 1000  # 30 days


def last_nonzero_vol_ms(sym: str) -> int | None:
    p = os.path.join(DATA_ROOT, sym, "8h.csv")
    if not os.path.isfile(p):
        return None
    df = pd.read_csv(p, usecols=["open_time", "volume"])
    df = df[df["open_time"] < OOS_CUTOFF_MS]
    nz = df[df["volume"].astype(float) > 0]
    if len(nz) == 0:
        return None
    return int(nz["open_time"].max())


def load_is_close(sym: str) -> pd.DataFrame | None:
    """IS-only (open_time < cutoff) open_time + close for a symbol, or None.

    Drops zero-volume (delisted-frozen) tail bars so correlation uses only
    real trading bars.
    """
    p = os.path.join(DATA_ROOT, sym, "8h.csv")
    if not os.path.isfile(p):
        return None
    df = pd.read_csv(p, usecols=["open_time", "close", "volume"])
    df = df[(df["open_time"] < OOS_CUTOFF_MS) & (df["volume"].astype(float) > 0)].copy()
    if len(df) < 200:
        return None
    df = df.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, f"OOS leak in {sym}!"
    return df[["open_time", "close"]]


def is_years(df: pd.DataFrame) -> float:
    return (df["open_time"].max() - df["open_time"].min()) / 1000 / 86400 / 365.25


def trivial_mom_sharpe(close: pd.Series, n: int) -> float:
    """Replicated EXACTLY from /085 structure_prescreen."""
    mom = close.pct_change(n)
    pos = np.sign(mom).shift(1)
    bar_ret = close.pct_change()
    gross = pos * bar_ret
    turnover = pos.diff().abs().fillna(0.0)
    net = (gross - FEE * turnover).dropna()
    if net.std(ddof=1) == 0 or len(net) < 30:
        return float("nan")
    return float(net.mean() / net.std(ddof=1) * ANN)


def discover_universe() -> list[str]:
    """USDT 8h symbols with >=4y IS-eligible start, minus all exclusion sets."""
    need_start = OOS_CUTOFF_MS - int(MIN_IS_YEARS * 365.25 * 86400 * 1000)
    excl = set(BUNDLE) | V1_EXCLUDED | FAILED_MINES | MIDFLIGHT | JUNK
    cands = []
    for d in sorted(os.listdir(DATA_ROOT)):
        if not d.endswith("USDT") or d in excl:
            continue
        p = os.path.join(DATA_ROOT, d, "8h.csv")
        if not os.path.isfile(p):
            continue
        try:
            with open(p) as f:
                f.readline()
                first = f.readline().strip().split(",")[0]
                if not first:
                    continue
                ot = int(first)
        except Exception:
            continue
        if ot <= need_start:
            cands.append(d)
    return cands


def main() -> None:
    # --- bundle log-return series (IS-only), aligned on open_time ---
    bundle_ret = {}
    for s in BUNDLE:
        df = load_is_close(s)
        assert df is not None, f"bundle member {s} has no IS data!"
        r = np.log(df["close"]).diff()
        bundle_ret[s] = pd.Series(r.values, index=df["open_time"].values)
    bundle_df = pd.DataFrame(bundle_ret).dropna()
    # equal-weight bundle return = mean of member log-returns at each timestamp
    ew_bundle = bundle_df.mean(axis=1)
    print(f"bundle aligned IS bars: {len(bundle_df)}  "
          f"({dt.datetime.utcfromtimestamp(bundle_df.index.min()/1000).date()} "
          f"-> {dt.datetime.utcfromtimestamp(bundle_df.index.max()/1000).date()})")

    universe = discover_universe()
    print(f"eligible candidate universe (>=4y IS, post-exclusion): {len(universe)}")

    delist_floor = OOS_CUTOFF_MS - DELIST_GRACE_MS
    rows = []
    skipped_delisted = []
    for sym in universe:
        # tradeability gate — must still be trading near the cutoff
        lnz = last_nonzero_vol_ms(sym)
        if lnz is None or lnz < delist_floor:
            skipped_delisted.append(sym)
            continue
        df = load_is_close(sym)
        if df is None:
            continue
        yrs = is_years(df)
        if yrs < MIN_IS_YEARS:
            continue
        close = df["close"].astype(float).reset_index(drop=True)
        cand_ret = pd.Series(np.log(close).diff().values, index=df["open_time"].values)

        # align candidate to each bundle member on COMMON timestamps
        per_member = {}
        for m in BUNDLE:
            j = pd.concat([cand_ret, bundle_ret[m]], axis=1, join="inner").dropna()
            if len(j) < 200:
                per_member[m] = np.nan
            else:
                per_member[m] = float(np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1])
        member_vals = {k: v for k, v in per_member.items() if np.isfinite(v)}
        if len(member_vals) < len(BUNDLE):
            # insufficient overlap with some member -> skip (can't trust the avg)
            continue
        avg_pair = float(np.mean(list(member_vals.values())))
        max_member = max(member_vals, key=member_vals.get)
        max_member_corr = member_vals[max_member]

        # corr vs equal-weight bundle on common timestamps
        je = pd.concat([cand_ret, ew_bundle], axis=1, join="inner").dropna()
        corr_ew = (float(np.corrcoef(je.iloc[:, 0], je.iloc[:, 1])[0, 1])
                   if len(je) >= 200 else np.nan)

        # GATE 1 — trivial TS-mom Sharpe (IS-only)
        s5 = trivial_mom_sharpe(close, HORIZONS["5d"])
        s21 = trivial_mom_sharpe(close, HORIZONS["21d"])
        s50 = trivial_mom_sharpe(close, HORIZONS["50d"])
        triv_min = float(np.nanmin([s5, s21, s50]))
        gate1_pass = bool(triv_min <= 0.15)

        rows.append({
            "symbol": sym,
            "avg_pairwise_corr_vs_bundle": round(avg_pair, 4),
            "corr_vs_ew_bundle": round(corr_ew, 4) if np.isfinite(corr_ew) else np.nan,
            "max_single_member_corr": round(max_member_corr, 4),
            "max_member": max_member.replace("USDT", ""),
            "corr_DOT": round(per_member["DOTUSDT"], 4),
            "corr_ETH": round(per_member["ETHUSDT"], 4),
            "corr_BTC": round(per_member["BTCUSDT"], 4),
            "corr_AAVE": round(per_member["AAVEUSDT"], 4),
            "is_years": round(yrs, 2),
            "triv_s5": round(s5, 3), "triv_s21": round(s21, 3), "triv_s50": round(s50, 3),
            "trivial_baseline_min_horizon": round(triv_min, 3),
            "gate1_pass": gate1_pass,
        })

    if skipped_delisted:
        print(f"SKIPPED (delisted / no trading within 30d of cutoff): "
              f"{', '.join(sorted(skipped_delisted))}")
    res = pd.DataFrame(rows).sort_values("avg_pairwise_corr_vs_bundle").reset_index(drop=True)
    out_csv = os.path.join(OUT_DIR, "bundle_diversification_corr.csv")
    res.to_csv(out_csv, index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print(f"\nfull ranked table written: {out_csv}  ({len(res)} candidates)\n")
    cols = ["symbol", "avg_pairwise_corr_vs_bundle", "corr_vs_ew_bundle",
            "max_single_member_corr", "max_member", "is_years",
            "trivial_baseline_min_horizon", "gate1_pass"]
    print("=== TOP 12 LOWEST-CORRELATION ELIGIBLE CANDIDATES (asc by avg pairwise) ===")
    print(res.head(12)[cols].to_string(index=False))

    # recommended pick: lowest avg bundle corr that ALSO passes GATE 1 + >=4y
    elig = res[res["gate1_pass"]].reset_index(drop=True)
    print("\n=== GATE-1-PASSING (trivial min <= +0.15), asc by avg pairwise corr ===")
    print(elig.head(12)[cols].to_string(index=False))
    if len(elig):
        pick = elig.iloc[0]
        print(f"\nRECOMMENDED NEXT PICK: {pick['symbol']}")
        print(f"  avg_pairwise_corr_vs_bundle = {pick['avg_pairwise_corr_vs_bundle']}  "
              f"corr_vs_ew_bundle = {pick['corr_vs_ew_bundle']}  "
              f"max_single_member = {pick['max_single_member_corr']} ({pick['max_member']})")
        print(f"  is_years = {pick['is_years']}  "
              f"trivial_min = {pick['trivial_baseline_min_horizon']}  GATE1 PASS")


if __name__ == "__main__":
    main()

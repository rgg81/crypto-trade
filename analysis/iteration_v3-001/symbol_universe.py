"""iter-v3/001 — symbol universe analysis (IS-only).

Selects 4 symbols for the v3 (rigor) track from outside ``V3_EXCLUDED_SYMBOLS``.

Outputs (all written to this directory):

- ``symbol_candidates.csv``  — per-candidate Gate 1 (data quality) and Gate 2
  (return regime) statistics computed on IS-only data (close_time < 2025-03-24).
- ``pairwise_correlation.csv`` — pairwise Pearson correlations of 8h log-return
  for every candidate vs every other candidate (IS-only).
- ``v3_universe_summary.csv``  — the 4 symbols proposed in the brief, plus a
  4x4 correlation block.

Design notes:

- This script is QR scope. It NEVER reads OOS data (close_time ≥ 2025-03-24).
- The script is reproducible — given the same kline CSVs it produces the same
  numerical output. No randomness, no shuffle, no train/test split.
- Listing-date floor is 2022-09-24 — i.e. ≥ 6 months before the first OOS
  candle's required training-window start (2023-03-24 = 2025-03-24 minus 24
  months). Symbols listed after 2022-09-24 cannot generate IS metrics for the
  earliest OOS-eligible months.
- The candidate pool is curated by sector before this script runs (see the
  ``CANDIDATES`` list below). The point of the script is to verify Gate 1+2
  evidence numerically, NOT to discover new candidates.
- v1 + v2 + delisted symbols (MATIC ended 2024-09; EOS ended 2025-05) are
  pre-excluded.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OOS_CUTOFF = pd.Timestamp("2025-03-24", tz="UTC")
LISTING_FLOOR = pd.Timestamp("2022-09-24", tz="UTC")  # >= 6 months before training-window start

V3_EXCLUDED_SYMBOLS = (
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    "BNBUSDT",
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
)

# Curated by sector (see brief Section 3 for taxonomy):
#   PoW majors:       BCHUSDT, ETCUSDT
#   DeFi blue-chips:  MKRUSDT, CRVUSDT, UNIUSDT, AAVEUSDT*
#   Infra / staking:  GRTUSDT, LDOUSDT, INJUSDT
#   Old-cap L1:       TRXUSDT, ATOMUSDT*
#   Smart-contract L1 alt: AVAXUSDT*
#   PoS staking:      EGLDUSDT, KAVAUSDT
#   Privacy/payments: XLMUSDT, XTZUSDT, DASHUSDT, ICPUSDT
#   DeFi (other):     SNXUSDT, COMPUSDT, YFIUSDT, MKRUSDT
#   Old PoW:          BCHUSDT, ETCUSDT, ZRXUSDT
#   *: dead-pathed in v2 — included for transparency, not for inclusion in final pick.
CANDIDATES = [
    "BCHUSDT", "ETCUSDT",
    "MKRUSDT", "CRVUSDT", "UNIUSDT", "AAVEUSDT", "SNXUSDT", "COMPUSDT", "YFIUSDT", "SUSHIUSDT",
    "GRTUSDT", "LDOUSDT", "INJUSDT",
    "TRXUSDT", "ATOMUSDT", "AVAXUSDT",
    "EGLDUSDT", "KAVAUSDT", "RUNEUSDT",
    "XLMUSDT", "XTZUSDT", "DASHUSDT", "ICPUSDT", "HBARUSDT",
    "ZRXUSDT", "FILUSDT", "ALGOUSDT", "MKRUSDT",
    "GALAUSDT", "MANAUSDT", "SANDUSDT", "ENJUSDT", "IMXUSDT",
    "VETUSDT", "NEOUSDT", "CHZUSDT",
    "JASMYUSDT", "FLOWUSDT", "RVNUSDT",
    "DYDXUSDT", "OPUSDT",
]
CANDIDATES = sorted(set(CANDIDATES) - set(V3_EXCLUDED_SYMBOLS))

DATA_DIR = Path(__file__).parent.parent.parent / "data"
OUT_DIR = Path(__file__).parent


def load_klines_is(symbol: str) -> pd.DataFrame | None:
    """Load IS-only 8h klines for *symbol*. Returns None if file missing or empty."""
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if len(df) == 0:
        return None
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    is_df = df[df["close_time"] < OOS_CUTOFF].copy()
    if len(is_df) == 0:
        return None
    # numeric coercion
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        if c in is_df.columns:
            is_df[c] = pd.to_numeric(is_df[c], errors="coerce")
    is_df = is_df.sort_values("close_time").reset_index(drop=True)
    return is_df


def gate1_data_quality(df: pd.DataFrame) -> dict[str, float | str]:
    """Gate 1 — data quality. Returns first/last close_time, n_candles, max gap, %coverage."""
    expected_step = pd.Timedelta(hours=8)
    diffs = df["close_time"].diff().dropna()
    max_gap = diffs.max() if len(diffs) > 0 else pd.Timedelta(0)
    expected_n = int(((df["close_time"].iloc[-1] - df["close_time"].iloc[0]) / expected_step) + 1)
    coverage_pct = 100.0 * len(df) / expected_n if expected_n > 0 else 0.0
    n_gaps_gt_1d = int((diffs > pd.Timedelta(days=1)).sum())
    return {
        "first_close": df["close_time"].iloc[0].strftime("%Y-%m-%d"),
        "last_close": df["close_time"].iloc[-1].strftime("%Y-%m-%d"),
        "is_n_candles": int(len(df)),
        "is_expected_n_candles": int(expected_n),
        "is_coverage_pct": round(coverage_pct, 2),
        "is_max_gap_hours": round(max_gap.total_seconds() / 3600.0, 2),
        "is_n_gaps_gt_1d": n_gaps_gt_1d,
    }


def gate2_return_regime(df: pd.DataFrame) -> dict[str, float]:
    """Gate 2 — return regime. Computes 8h log-return statistics (mean, std, skew, kurtosis,
    annualised vol, max drawdown over IS, daily-equivalent volume proxy)."""
    log_close = np.log(df["close"].astype(float))
    ret = log_close.diff().dropna()

    # 8h * 3 = 24h, * 365 = 1095 obs/year
    annual_factor = np.sqrt(365 * 3)
    sigma_annual = float(ret.std() * annual_factor)
    mu_annual = float(ret.mean() * 365 * 3)

    # Max drawdown in IS — running peak vs trough on cumulative log-return
    cum = ret.cumsum()
    running_max = cum.cummax()
    drawdown = cum - running_max
    max_dd = float(drawdown.min())
    max_dd_pct = float(np.exp(max_dd) - 1.0) * 100.0

    daily_vol_usdt = float(df["quote_volume"].astype(float).sum() / max(len(df) / 3.0, 1))

    return {
        "is_ret_mean_8h": round(float(ret.mean()) * 1e4, 4),  # bps per 8h
        "is_ret_std_8h": round(float(ret.std()) * 1e2, 4),  # pct per 8h
        "is_ret_skew": round(float(ret.skew()), 4),
        "is_ret_kurt": round(float(ret.kurtosis()), 4),
        "is_sigma_annual_pct": round(sigma_annual * 100, 2),
        "is_mu_annual_pct": round(mu_annual * 100, 2),
        "is_max_dd_pct": round(max_dd_pct, 2),
        "is_avg_daily_quote_vol_musdt": round(daily_vol_usdt / 1e6, 2),
    }


def listing_filter(first_close: str) -> bool:
    return pd.Timestamp(first_close, tz="UTC") <= LISTING_FLOOR


def main() -> None:
    print(f"OOS_CUTOFF: {OOS_CUTOFF}")
    print(f"LISTING_FLOOR: {LISTING_FLOOR}")
    print(f"V3_EXCLUDED_SYMBOLS: {V3_EXCLUDED_SYMBOLS}")
    print(f"Candidates evaluated: {len(CANDIDATES)}")
    print()

    # Pre-excluded — surface for the brief table:
    pre_excluded_v2_dead_paths = {"AAVEUSDT", "AVAXUSDT", "ATOMUSDT", "OPUSDT"}

    rows = []
    is_returns: dict[str, pd.Series] = {}
    for sym in CANDIDATES:
        df = load_klines_is(sym)
        if df is None:
            print(f"[skip] {sym} — no IS data")
            continue

        gate1 = gate1_data_quality(df)
        gate2 = gate2_return_regime(df)

        passes_listing = listing_filter(gate1["first_close"])
        gate1["passes_listing_floor"] = passes_listing
        gate1["v2_dead_path"] = sym in pre_excluded_v2_dead_paths

        # IS log-return for correlation matrix (downstream)
        log_close = np.log(df["close"].astype(float))
        ret = log_close.diff().dropna()
        ret.index = df["close_time"].iloc[1:].values  # type: ignore
        is_returns[sym] = ret

        row = {"symbol": sym, **gate1, **gate2}
        rows.append(row)

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values(
        ["passes_listing_floor", "v2_dead_path", "is_sigma_annual_pct"],
        ascending=[False, True, False],
    )
    df_out.to_csv(OUT_DIR / "symbol_candidates.csv", index=False)
    print(f"wrote {OUT_DIR / 'symbol_candidates.csv'} — {len(df_out)} rows")

    # Pairwise IS-period correlation matrix
    valid_syms = sorted(is_returns.keys())
    aligned = pd.concat([is_returns[s].rename(s) for s in valid_syms], axis=1)
    aligned = aligned.dropna(how="any")  # only periods where ALL candidates have data
    corr = aligned.corr(method="pearson")
    corr.to_csv(OUT_DIR / "pairwise_correlation.csv")
    print(f"wrote {OUT_DIR / 'pairwise_correlation.csv'} — {corr.shape}")
    print(f"  aligned IS rows: {len(aligned)} (intersection across all candidates)")

    # Proposed v3 universe — 4 symbols spanning distinct sectors:
    #   PoW major: BCHUSDT (Bitcoin Cash, fork of BTC, no v1/v2 overlap)
    #   DeFi blue-chip: MKRUSDT (Maker/Sky CDP, RWA narrative, oldest DeFi token by tenure)
    #   Liquid staking infra: LDOUSDT (Lido — entirely new sector for the project)
    #   Old-cap DPoS / stablecoin rail: TRXUSDT (Tron — distinct from any v1/v2 symbol)
    proposed = ["BCHUSDT", "MKRUSDT", "LDOUSDT", "TRXUSDT"]
    proposed = [s for s in proposed if s in valid_syms]

    sub_rows = []
    for sym in proposed:
        sub_rows.append(df_out[df_out["symbol"] == sym].iloc[0].to_dict())
    summary = pd.DataFrame(sub_rows)

    # 4x4 correlation block
    proposed_corr = corr.loc[proposed, proposed]

    # also compute correlation of each proposed symbol against representative
    # v1 (BTCUSDT) + v2 (SOLUSDT) symbols using the SAME IS-aligned window —
    # we have to recompute since BTCUSDT and SOLUSDT are excluded from the
    # candidate scan above. This is a cross-track diversification check.
    cross_check_syms = ["BTCUSDT", "SOLUSDT"]
    cross_returns: dict[str, pd.Series] = {}
    for sym in cross_check_syms:
        df_c = load_klines_is(sym)
        if df_c is None:
            continue
        log_close = np.log(df_c["close"].astype(float))
        ret = log_close.diff().dropna()
        ret.index = df_c["close_time"].iloc[1:].values  # type: ignore
        cross_returns[sym] = ret

    cross_corr_rows = []
    for sym in proposed:
        row = {"symbol": sym}
        for cs in cross_check_syms:
            if cs not in cross_returns:
                row[f"corr_vs_{cs}"] = np.nan
                continue
            joined = pd.concat([is_returns[sym], cross_returns[cs]], axis=1).dropna()
            row[f"corr_vs_{cs}"] = round(float(joined.iloc[:, 0].corr(joined.iloc[:, 1])), 4)
        cross_corr_rows.append(row)
    cross_corr_df = pd.DataFrame(cross_corr_rows)

    summary.to_csv(OUT_DIR / "v3_universe_summary.csv", index=False)
    proposed_corr.to_csv(OUT_DIR / "v3_universe_correlation.csv")
    cross_corr_df.to_csv(OUT_DIR / "v3_universe_cross_track_correlation.csv", index=False)
    print(f"wrote {OUT_DIR / 'v3_universe_summary.csv'} — proposed universe")
    print(f"wrote {OUT_DIR / 'v3_universe_correlation.csv'} — within-universe pairwise")
    print(f"wrote {OUT_DIR / 'v3_universe_cross_track_correlation.csv'} — vs v1/v2")
    print()
    print("=== Proposed v3 universe ===")
    print(summary[[
        "symbol", "first_close", "last_close", "is_n_candles", "is_coverage_pct",
        "is_sigma_annual_pct", "is_max_dd_pct", "is_avg_daily_quote_vol_musdt",
        "v2_dead_path",
    ]].to_string(index=False))
    print()
    print("=== Within-universe IS correlation (Pearson, 8h log-returns) ===")
    print(proposed_corr.round(4).to_string())
    print()
    print("=== Cross-track diversification check ===")
    print(cross_corr_df.to_string(index=False))


if __name__ == "__main__":
    main()

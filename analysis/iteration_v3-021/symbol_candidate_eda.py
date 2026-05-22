"""iter-v3/021 symbol candidate EDA — Gate 1 + Gate 2 + structural complementarity.

Evaluates candidate NEW symbols against:
  Gate 1 (data quality): Binance Futures listing date, IS+OOS coverage %, gap days
  Gate 2 (liquidity): avg daily quote volume IS, min daily volume, weekend continuity
  Structural complementarity: correlation with BCH/LDO/TRX, vol regime, cap

Output:
  - per-candidate IS/OOS coverage + liquidity stats
  - per-candidate correlation with each of BCH/LDO/TRX (8h returns)
  - per-candidate volatility regime (8h log-return std, 24h NATR)
  - composite score = 0.30·complementarity + 0.30·data_quality + 0.25·liquidity + 0.15·trade_rate_proxy
  - ranking CSV: analysis/iteration_v3-021/symbol_candidate_ranking.csv

Reads only IS-window data for ranking. OOS coverage IS reported but is NOT used
for selection (that would contaminate). The IS-only ranking is the QR's input
for top-2 candidate selection.

Inputs (read-only):
  data/{SYMBOL}/8h.csv — 8h klines

Outputs (committed):
  analysis/iteration_v3-021/symbol_candidate_ranking.csv
  analysis/iteration_v3-021/per_candidate_correlations.csv
  analysis/iteration_v3-021/per_candidate_liquidity.csv
  analysis/iteration_v3-021/per_candidate_volatility.csv
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis" / "iteration_v3-021"

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 UTC (sacred constant)

# IS evaluation window approximate bounds. The v3 runner uses a rolling
# walk-forward of TRAINING_MONTHS=24 months, so the EARLIEST month we can
# evaluate IS at is approximately 24 months after each symbol's listing. For
# this EDA we use a fixed reference IS evaluation window from 2023-04-01 to
# OOS_CUTOFF_DATE 2025-03-24 — symbols that don't cover this full window
# fail Gate 1.
IS_EVAL_START_MS = int(datetime(2023, 4, 1, tzinfo=timezone.utc).timestamp() * 1000)
IS_EVAL_END_MS = OOS_CUTOFF_MS  # 2025-03-24

# Existing v3 universe (BASELINE_V3.md):
BASELINE_SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")

# Candidate pool — excludes V3_EXCLUDED_SYMBOLS + project_tried_symbols.md
# exclusions (DOGE, SOL, XRP, NEAR — already evaluated 2026-04-21).
# MKR also excluded (dropped at iter-v3/013).
CANDIDATES = (
    "AVAXUSDT",
    "ADAUSDT",
    "ATOMUSDT",
    "FILUSDT",
    "ALGOUSDT",
    "HBARUSDT",
    "VETUSDT",
    "POLUSDT",  # Polygon (replaced MATIC late 2024)
    "ARBUSDT",  # Arbitrum (~2 years history at IS start)
    "OPUSDT",  # Optimism
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_klines(symbol: str) -> pd.DataFrame:
    """Read 8h klines for *symbol* into a typed DataFrame.

    CSV format: header row + 11 columns (open_time, open, high, low, close,
    volume, close_time, quote_volume, trades, taker_buy_volume,
    taker_buy_quote_volume).
    """
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing data: {path}")

    df = pd.read_csv(
        path,
        dtype={
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float,
            "quote_volume": float,
            "taker_buy_volume": float,
            "taker_buy_quote_volume": float,
        },
    )
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    df["trades"] = df["trades"].astype(np.int64)
    df["dt"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    return df


def gate1_data_quality(df: pd.DataFrame, symbol: str) -> dict:
    """Gate 1 — data quality + coverage.

    Returns coverage % over IS+OOS window, gap days, listing date, etc.
    """
    first_ms = int(df["open_time"].iloc[0])
    last_ms = int(df["open_time"].iloc[-1])
    first_dt = datetime.fromtimestamp(first_ms / 1000, tz=timezone.utc)
    last_dt = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc)

    # Coverage of IS evaluation window
    is_mask = (df["open_time"] >= IS_EVAL_START_MS) & (df["open_time"] < IS_EVAL_END_MS)
    is_n = int(is_mask.sum())
    is_expected = (IS_EVAL_END_MS - IS_EVAL_START_MS) // (8 * 3600 * 1000)
    is_coverage_pct = 100.0 * is_n / max(is_expected, 1)

    # Coverage of OOS window (informational; NOT used for selection)
    oos_mask = df["open_time"] >= IS_EVAL_END_MS
    oos_n = int(oos_mask.sum())

    # Gap detection — IS window only
    is_df = df.loc[is_mask].copy()
    if len(is_df) > 1:
        delta_ms = is_df["open_time"].diff().dropna()
        expected_8h = 8 * 3600 * 1000
        # Anything bigger than 1.5x expected is a gap
        gap_count = int((delta_ms > 1.5 * expected_8h).sum())
        # Total gap duration (h)
        gap_total_ms = int(((delta_ms - expected_8h).clip(lower=0)).sum())
        gap_total_h = gap_total_ms / (3600 * 1000)
    else:
        gap_count = 0
        gap_total_h = 0.0

    # Sufficient pre-IS history for 24-month training window?
    pre_is_months = (IS_EVAL_START_MS - first_ms) / (1000 * 86400 * 30.4375)
    has_24mo_pretrain = pre_is_months >= 24.0

    return {
        "symbol": symbol,
        "first_kline_dt": first_dt.date().isoformat(),
        "last_kline_dt": last_dt.date().isoformat(),
        "pre_is_months": round(pre_is_months, 2),
        "has_24mo_pretrain": has_24mo_pretrain,
        "is_coverage_pct": round(is_coverage_pct, 2),
        "is_n_klines": is_n,
        "oos_n_klines": oos_n,
        "gap_count_is": gap_count,
        "gap_total_hours_is": round(gap_total_h, 2),
        "gate1_pass": (
            has_24mo_pretrain
            and is_coverage_pct >= 99.0
            and gap_count <= 5
        ),
    }


def gate2_liquidity(df: pd.DataFrame, symbol: str) -> dict:
    """Gate 2 — IS-window liquidity stats."""
    is_mask = (df["open_time"] >= IS_EVAL_START_MS) & (df["open_time"] < IS_EVAL_END_MS)
    is_df = df.loc[is_mask].copy()
    if len(is_df) == 0:
        return {
            "symbol": symbol,
            "is_avg_daily_qvol_usd": 0.0,
            "is_median_daily_qvol_usd": 0.0,
            "is_min_daily_qvol_usd": 0.0,
            "is_p10_daily_qvol_usd": 0.0,
            "weekend_share_pct": 0.0,
            "gate2_pass": False,
        }

    # 8h candle quote_volume → daily by summing 3 consecutive
    is_df["date"] = is_df.index.date
    daily_qvol = is_df.groupby("date")["quote_volume"].sum()

    avg = float(daily_qvol.mean())
    med = float(daily_qvol.median())
    p10 = float(daily_qvol.quantile(0.10))
    p90 = float(daily_qvol.quantile(0.90))
    mn = float(daily_qvol.min())

    # Weekend share — Sat/Sun
    is_df["dow"] = is_df.index.dayofweek
    weekend_qvol_share = (
        is_df.loc[is_df["dow"].isin([5, 6]), "quote_volume"].sum()
        / max(is_df["quote_volume"].sum(), 1.0)
    )

    # Gate 2 pass: avg daily quote vol > $20M AND p10 > $5M (typical Binance
    # Futures liquidity floor for "viable for size at notional ≥ $1M").
    gate2_pass = bool(avg > 2.0e7 and p10 > 5.0e6)

    return {
        "symbol": symbol,
        "is_avg_daily_qvol_usd": round(avg, 0),
        "is_median_daily_qvol_usd": round(med, 0),
        "is_p10_daily_qvol_usd": round(p10, 0),
        "is_p90_daily_qvol_usd": round(p90, 0),
        "is_min_daily_qvol_usd": round(mn, 0),
        "weekend_share_pct": round(100 * weekend_qvol_share, 2),
        "gate2_pass": gate2_pass,
    }


def compute_returns(df: pd.DataFrame) -> pd.Series:
    """8h log returns indexed by open_time."""
    s = pd.Series(np.log(df["close"].values), index=df.index)
    return s.diff().dropna()


def compute_natr(df: pd.DataFrame, period: int = 21) -> float:
    """Mean of NATR(period) on IS window — proxy for symbol vol regime."""
    is_mask = (df["open_time"] >= IS_EVAL_START_MS) & (df["open_time"] < IS_EVAL_END_MS)
    sub = df.loc[is_mask].copy()
    if len(sub) < period + 2:
        return 0.0
    h = sub["high"].values
    l = sub["low"].values
    c = sub["close"].values
    prev_c = np.r_[np.nan, c[:-1]]
    tr = np.maximum.reduce([h - l, np.abs(h - prev_c), np.abs(l - prev_c)])
    atr = pd.Series(tr).rolling(period, min_periods=period).mean().values
    natr = atr / c * 100.0
    return float(np.nanmean(natr))


def correlations(candidate_df: pd.DataFrame, baseline_returns: dict[str, pd.Series]) -> dict:
    """Pearson correlation of candidate 8h returns vs each baseline symbol on IS window.

    Lower mean |corr| = better diversification = stronger structural complement.
    """
    is_mask = (candidate_df["open_time"] >= IS_EVAL_START_MS) & (candidate_df["open_time"] < IS_EVAL_END_MS)
    cand_returns = compute_returns(candidate_df.loc[is_mask])
    out: dict[str, float] = {}
    for sym, base_ret in baseline_returns.items():
        # Align on common index
        joined = pd.concat([cand_returns, base_ret], axis=1, join="inner").dropna()
        if len(joined) < 100:
            out[f"corr_{sym}"] = float("nan")
        else:
            c = float(joined.iloc[:, 0].corr(joined.iloc[:, 1]))
            out[f"corr_{sym}"] = round(c, 4)
    abs_vals = [abs(v) for v in out.values() if not np.isnan(v)]
    out["mean_abs_corr_baseline"] = round(float(np.mean(abs_vals)) if abs_vals else float("nan"), 4)
    out["max_abs_corr_baseline"] = round(float(np.max(abs_vals)) if abs_vals else float("nan"), 4)
    return out


def trade_rate_proxy(natr_pct: float) -> dict:
    """Rough estimate of trades/month from a NATR proxy.

    Uses the v3 ATR labeling (tp=2.0 ATR, sl=1.0 ATR) and triple-barrier hit-rate
    heuristic: a candle with NATR_pct N has ~ 10*N% chance of barrier hit per
    candle at typical 21-bar timeout. Times 90 candles/month yields trades/month.

    This is a NOMINAL proxy, NOT a forecast — actual trade rate depends on the
    7-gate risk stack which dominates emission. The proxy is informational only.
    """
    # 8h candles, ~90 per month
    candles_per_month = 90.0
    # NATR in % → barrier-hit prob per candle (rough heuristic)
    p_hit_per_candle = min(0.25, natr_pct / 100.0 * 2.5)
    raw_trades_per_month = candles_per_month * p_hit_per_candle
    # 7-gate stack typically retains ~30-40% of raw signals (iter-v3/018 anchor:
    # BCH 65 IS / 11.6mo = 5.6/mo, LDO 22/11.6 = 1.9/mo, TRX 90/11.6 = 7.8/mo;
    # with NATR BCH ~3.5%, LDO ~6.8%, TRX ~3.0%; back-calc gate retention ≈ 0.30)
    gate_retention = 0.30
    return {
        "natr_21_is_pct": round(natr_pct, 4),
        "raw_trades_per_month_proxy": round(raw_trades_per_month, 2),
        "gate_retained_trades_per_month_proxy": round(raw_trades_per_month * gate_retention, 2),
    }


def cap_band(symbol: str) -> str:
    """Rough cap band from common knowledge (informational only)."""
    large = {"AVAXUSDT", "ADAUSDT", "ATOMUSDT", "FILUSDT", "ARBUSDT", "OPUSDT"}
    mid = {"ALGOUSDT", "HBARUSDT", "VETUSDT", "POLUSDT"}
    if symbol in large:
        return "LARGE"
    if symbol in mid:
        return "MID"
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load baseline 3-symbol returns for correlation reference
    baseline_returns: dict[str, pd.Series] = {}
    for sym in BASELINE_SYMBOLS:
        bdf = load_klines(sym)
        is_mask = (bdf["open_time"] >= IS_EVAL_START_MS) & (bdf["open_time"] < IS_EVAL_END_MS)
        baseline_returns[sym] = compute_returns(bdf.loc[is_mask])

    # 2. Per-candidate evaluation
    g1_rows: list[dict] = []
    g2_rows: list[dict] = []
    corr_rows: list[dict] = []
    vol_rows: list[dict] = []

    for sym in CANDIDATES:
        df = load_klines(sym)

        g1 = gate1_data_quality(df, sym)
        g2 = gate2_liquidity(df, sym)
        corr_d = correlations(df, baseline_returns)
        natr_pct = compute_natr(df, period=21)
        tr_proxy = trade_rate_proxy(natr_pct)

        g1_rows.append(g1)
        g2_rows.append(g2)

        corr_row = {"symbol": sym, **corr_d}
        corr_rows.append(corr_row)

        vol_row = {"symbol": sym, **tr_proxy, "cap_band": cap_band(sym)}
        vol_rows.append(vol_row)

    # 3. Compute composite score
    g1_df = pd.DataFrame(g1_rows)
    g2_df = pd.DataFrame(g2_rows)
    corr_df = pd.DataFrame(corr_rows)
    vol_df = pd.DataFrame(vol_rows)

    # Score components (each 0..1):
    #   - data_quality: 1.0 if gate1_pass + has full 24mo pretrain; else partial
    #   - liquidity: log10(avg_daily_qvol)/log10(1e9) capped to [0,1]
    #   - complementarity: 1 - mean_abs_corr_baseline (lower corr = higher score)
    #   - trade_rate_proxy: gate_retained_trades_per_month / 8 (clip 0..1)
    rank_df = g1_df.merge(g2_df, on="symbol").merge(corr_df, on="symbol").merge(vol_df, on="symbol")

    rank_df["score_data_quality"] = (
        rank_df["gate1_pass"].astype(int).astype(float) * 0.7
        + (rank_df["is_coverage_pct"] / 100.0).clip(0, 1) * 0.3
    )
    rank_df["score_liquidity"] = (
        np.log10(rank_df["is_avg_daily_qvol_usd"].clip(lower=1e6))
        / np.log10(1e9)
    ).clip(0, 1)
    rank_df["score_complementarity"] = (1.0 - rank_df["mean_abs_corr_baseline"].clip(0, 1))
    rank_df["score_trade_rate"] = (
        rank_df["gate_retained_trades_per_month_proxy"] / 8.0
    ).clip(0, 1)

    rank_df["composite_score"] = (
        0.30 * rank_df["score_complementarity"]
        + 0.30 * rank_df["score_data_quality"]
        + 0.25 * rank_df["score_liquidity"]
        + 0.15 * rank_df["score_trade_rate"]
    )

    # Sort by composite descending. Tiebreak by mean_abs_corr_baseline asc.
    rank_df = rank_df.sort_values(
        ["composite_score", "mean_abs_corr_baseline"],
        ascending=[False, True],
    ).reset_index(drop=True)

    rank_df["rank"] = rank_df.index + 1

    # 4. Write outputs
    cols_order = [
        "rank",
        "symbol",
        "composite_score",
        "score_complementarity",
        "score_data_quality",
        "score_liquidity",
        "score_trade_rate",
        "first_kline_dt",
        "pre_is_months",
        "has_24mo_pretrain",
        "is_coverage_pct",
        "is_n_klines",
        "oos_n_klines",
        "gap_count_is",
        "gap_total_hours_is",
        "gate1_pass",
        "is_avg_daily_qvol_usd",
        "is_median_daily_qvol_usd",
        "is_p10_daily_qvol_usd",
        "is_min_daily_qvol_usd",
        "weekend_share_pct",
        "gate2_pass",
        "corr_BCHUSDT",
        "corr_LDOUSDT",
        "corr_TRXUSDT",
        "mean_abs_corr_baseline",
        "max_abs_corr_baseline",
        "natr_21_is_pct",
        "raw_trades_per_month_proxy",
        "gate_retained_trades_per_month_proxy",
        "cap_band",
    ]
    rank_df[cols_order].to_csv(ANALYSIS_DIR / "symbol_candidate_ranking.csv", index=False)

    # Detail CSVs
    g1_df.to_csv(ANALYSIS_DIR / "per_candidate_data_quality.csv", index=False)
    g2_df.to_csv(ANALYSIS_DIR / "per_candidate_liquidity.csv", index=False)
    corr_df.to_csv(ANALYSIS_DIR / "per_candidate_correlations.csv", index=False)
    vol_df.to_csv(ANALYSIS_DIR / "per_candidate_volatility.csv", index=False)

    # Print summary
    print("=" * 90)
    print("iter-v3/021 Symbol Candidate EDA — IS-only Gate 1+2 + structural complementarity")
    print("=" * 90)
    print(f"IS evaluation window: 2023-04-01 → 2025-03-24")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (sacred; informational only)")
    print(f"Baseline universe: {BASELINE_SYMBOLS}")
    print(f"Candidates evaluated: {len(CANDIDATES)} ({CANDIDATES})")
    print()
    print(rank_df[["rank", "symbol", "composite_score", "gate1_pass", "gate2_pass",
                   "is_coverage_pct", "is_avg_daily_qvol_usd",
                   "mean_abs_corr_baseline", "natr_21_is_pct"]].to_string(index=False))
    print()
    print("Top-2 recommendation for QR brief:")
    top2 = rank_df.head(2)
    for _, row in top2.iterrows():
        print(
            f"  #{int(row['rank'])}: {row['symbol']} "
            f"(composite={row['composite_score']:.3f}, "
            f"corr={row['mean_abs_corr_baseline']:.3f}, "
            f"qvol_avg=${row['is_avg_daily_qvol_usd']/1e6:.1f}M, "
            f"NATR={row['natr_21_is_pct']:.2f}%)"
        )

    print()
    print(f"Outputs:")
    for fn in sorted(ANALYSIS_DIR.glob("*.csv")):
        print(f"  {fn.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

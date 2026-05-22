"""iter-v3/101 EDA #1 — signal characterization + sample-weighting axis design.

PURPOSE (design EDA, NOT a GO/NO-GO kill gate):
  Cycle 4 (iter-v3/093-100) killed 6 axes at the EDA on the SAME binding
  constraint: the thin per-symbol 8h triple-barrier feature->label signal of the
  v3 altcoin universe (BCH/LDO/TRX). The /100 closeout's standing recommendation
  is a SAMPLE-WEIGHTING / TRAINING-OBJECTIVE axis — the one frame untouched by
  /094-/100 (symbols, features, model arch, label class structure, regime split
  all closed). This EDA characterizes that axis with a genuine quantitative
  basis so iter-v3/101 can DESIGN it, not rubber-stamp it.

KEY CODEBASE FACT (verified at src/crypto_trade/strategies/ml/lgbm.py:400-408 and
  run_baseline_v3.py:1844-1869 common_kwargs): the v3 baseline runner does NOT
  pass `sample_uniqueness=True` nor `time_decay_half_life`. The model's
  `sample_weight` is ONLY `label_trades`' magnitude weight = |net-of-fee PnL of
  the labeled direction|, normalized to [1, 10]. AFML-Ch.4 uniqueness weighting
  (`compute_sample_uniqueness`, ALREADY in labeling.py) is wired into lgbm.py but
  DISABLED by default. So this axis is genuinely un-tested in v3.

ANGLES (multi-angle — this is the deep-analysis step):
  A. Concurrency / uniqueness structure of the 21-candle triple-barrier label.
  B. Magnitude-weight distribution: is the current [1,10] weight informative or
     near-degenerate?  Does net-PnL magnitude predict directional skill?
  C. Held-out-fold horse race: pooled-CV-IC of the 14-feature stack vs the /059
     label, weighted by each candidate scheme.
  D. Per-symbol decomposition (BCH 95.76% IS concentration is the fragility flag).

STRICT IS-ONLY: every row has open_time < OOS_CUTOFF_MS = 1742774400000.
OOS is NEVER read. OOS_CUTOFF_DATE / training_months are NOT touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from crypto_trade.strategies.ml.labeling import (  # noqa: E402
    compute_sample_uniqueness,
    label_trades,
)

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE
SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
DATA = REPO / "data" / "features_v3"
OUT = Path(__file__).resolve().parent

# /059 canonical label spec (BASELINE_V3.md Code Configuration)
ATR_TP, ATR_SL = 2.0, 1.0
TIMEOUT_MIN = 10080  # 21 candles at 8h
ATR_COL = "natr_21_raw"
FEE_PCT = 0.1
INTERVAL_MIN = 480

# /059 canonical 14-feature stack (BASELINE_V3.md)
V3_FEATURES = [
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
]


def load_is(sym: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA / f"{sym}_8h_features.parquet")
    df = df[df["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    return df


def make_labels(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Replicate labeling.py:label_trades exactly for the /059 spec."""
    indices = np.arange(len(df))
    atr_vals = df[ATR_COL].to_numpy(dtype=np.float64)
    # ATR labeling: tp_pct/sl_pct become ATR multipliers when atr_values is set.
    labels, weights, long_pnls, short_pnls = label_trades(
        df,
        indices,
        ATR_TP,  # tp_pct -> ATR multiplier (use_atr path)
        ATR_SL,  # sl_pct -> ATR multiplier
        TIMEOUT_MIN,
        fee_pct=FEE_PCT,
        atr_values=atr_vals,
        verbose=0,
        label_mode="triple_barrier",
    )
    return labels, weights, long_pnls, short_pnls


# ----------------------------------------------------------------------------
# ANGLE A — concurrency / uniqueness structure
# ----------------------------------------------------------------------------
def angle_a(rows: list[dict]) -> None:
    print("\n=== ANGLE A — label concurrency / AFML-Ch.4 uniqueness structure ===")
    for sym in SYMBOLS:
        df = load_is(sym)
        n = len(df)
        idx = np.arange(n)
        open_arr = df["open_time"].to_numpy(dtype=np.int64)
        sym_arr = df["symbol"].to_numpy()
        uniq = compute_sample_uniqueness(idx, TIMEOUT_MIN, open_arr, sym_arr)
        # concurrency = number of overlapping labels at each candle's window
        # 21-candle horizon -> at most ~21 concurrent labels per candle
        rows.append(
            {
                "angle": "A_uniqueness",
                "symbol": sym,
                "n_candles": n,
                "uniq_mean": round(float(uniq.mean()), 4),
                "uniq_min": round(float(uniq.min()), 4),
                "uniq_p10": round(float(np.percentile(uniq, 10)), 4),
                "uniq_p90": round(float(np.percentile(uniq, 90)), 4),
                "uniq_std": round(float(uniq.std()), 4),
                # effective sample size if we weight by uniqueness
                "ess_frac": round(float(uniq.sum() / n), 4),
            }
        )
        print(
            f"  {sym}: uniq mean={uniq.mean():.3f} std={uniq.std():.3f} "
            f"[p10={np.percentile(uniq, 10):.3f}, p90={np.percentile(uniq, 90):.3f}] "
            f"ESS-frac={uniq.sum() / n:.3f}"
        )
    print("  READ: uniq mean ~1/21 is the fully-overlapping floor; ESS-frac is the")
    print("  fraction of independent samples. Low ESS-frac => the 21-candle label")
    print("  is heavily redundant and uniqueness weighting has real leverage.")


# ----------------------------------------------------------------------------
# ANGLE B — magnitude-weight informativeness
# ----------------------------------------------------------------------------
def angle_b(rows: list[dict]) -> None:
    print("\n=== ANGLE B — magnitude-weight (|net PnL|) informativeness ===")
    for sym in SYMBOLS:
        df = load_is(sym)
        labels, weights, long_pnls, short_pnls = make_labels(df)
        # the labeled direction's net PnL (pre-normalization magnitude)
        labeled_pnl = np.where(labels == 1, long_pnls, short_pnls)
        best_edge = np.maximum(long_pnls, short_pnls)  # best achievable net edge
        # does the runner's [1,10] weight separate winners from losers?
        # winner = the labeled direction's realized barrier PnL > 0
        winner = labeled_pnl > 0
        valid = ~np.isnan(weights) & ~np.isnan(labeled_pnl)
        w = weights[valid]
        win = winner[valid]
        be = best_edge[valid]
        # tercile analysis: top vs bottom weight tercile win rate
        order = np.argsort(w)
        t = len(w) // 3
        lo_win = win[order[:t]].mean()
        hi_win = win[order[-t:]].mean()
        # what fraction of candles have NO tradeable edge (best_edge <= 0)?
        edge_free_frac = float((be <= 0).mean())
        rows.append(
            {
                "angle": "B_magnitude",
                "symbol": sym,
                "weight_mean": round(float(w.mean()), 3),
                "weight_std": round(float(w.std()), 3),
                "weight_cv": round(float(w.std() / w.mean()), 3),
                "win_rate_lo_tercile": round(float(lo_win), 4),
                "win_rate_hi_tercile": round(float(hi_win), 4),
                "win_rate_spread": round(float(hi_win - lo_win), 4),
                "edge_free_frac": round(edge_free_frac, 4),
                "best_edge_mean": round(float(be.mean()), 4),
            }
        )
        print(
            f"  {sym}: weight CV={w.std() / w.mean():.3f} | "
            f"win-rate lo-tercile={lo_win:.3f} hi-tercile={hi_win:.3f} "
            f"spread={hi_win - lo_win:+.3f} | edge-free-frac={edge_free_frac:.3f}"
        )
    print("  READ: a POSITIVE win-rate spread (hi-tercile beats lo) means the")
    print("  magnitude weight already concentrates on edge-bearing candles; a flat")
    print("  or negative spread means the current weight is near-uninformative and")
    print("  a re-designed weight (uniqueness + edge-floor) has headroom.")


def main() -> None:
    print("=" * 78)
    print("iter-v3/101 EDA #1 — signal characterization + sample-weighting design")
    print("STRICT IS-ONLY: open_time < OOS_CUTOFF_MS =", OOS_CUTOFF_MS)
    print("=" * 78)
    rows: list[dict] = []
    angle_a(rows)
    angle_b(rows)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "T1_signal_weight_characterization.csv", index=False)
    print(f"\nWROTE {OUT / 'T1_signal_weight_characterization.csv'}")


if __name__ == "__main__":
    main()

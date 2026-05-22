"""iter-v3/102 — EDA Script 1: formulaic-alpha feature->label IC + past-only audit.

DELIVERABLE
-----------
For the v3-portable WorldQuant-101 alpha basket (alpha_lib.ALPHA_REGISTRY),
on the BCH/LDO/TRX 8h panel, STRICTLY IS-ONLY:
  T1  IS panel summary (rows, date span, long-label fraction) per symbol.
  T2  Per-(alpha, symbol) feature->label SPEARMAN IC vs the /059 triple-barrier
      label, computed WALK-FORWARD-FAITHFUL: the label is built on the full
      panel (so the 21-bar forward scan can see post-cutoff bars for the LAST
      few IS rows — exactly as labeling.py does), then the IS mask is applied,
      then the IC is the Spearman corr of the (past-only) alpha at bar t with
      the {+1 long / -1 short} label of bar t.  This is the SAME directional-IC
      measure /096/098 used; a small |IC| is the thin-signal v3 baseline.
  T3  Past-only adversarial audit: each alpha is recomputed on a panel
      TRUNCATED 50 bars early; the overlap region must be bit-identical (the
      LdP look-ahead test).  An alpha that changes is look-ahead-contaminated
      and is DISQUALIFIED from the basket.

NO-CHEATING
-----------
- OOS_CUTOFF_MS = 1742774400000 (2025-03-24).  Every row entering an IC
  computation has open_time < OOS_CUTOFF_MS.  The real OOS is NEVER touched.
- The triple-barrier label replicates labeling.py:label_trades EXACTLY: ATR
  multipliers (2.0, 1.0), timeout 10080 min = 21 candles, fee 0.1%, natr_21_raw
  as the ATR source.  The label is built on the FULL panel then IS-masked (the
  forward scan for the last IS rows legitimately reads post-cutoff candles —
  that is how the production labeler works; it is NOT a feature look-ahead).
- 24-month listing burn-in dropped per symbol (matches the runner warmup).

RUN:  uv run python analysis/iteration_v3-102/alpha_ic_eda.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alpha_lib import ALPHA_NOTES, ALPHA_REGISTRY  # noqa: E402

# --------------------------------------------------------------------------
# Immutable constants — IDENTICAL to the /098 EDA + labeling.py production.
# --------------------------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE, never touched
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080  # 21 candles at 8h — the /059 canonical label
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-102")
MS_PER_DAY = 24 * 60 * 60 * 1000


# ==========================================================================
# Triple-barrier labeling — faithful replication of labeling.py:label_trades
# (identical to the /098 EDA; TIMEOUT_MIN is the /059 21-candle horizon).
# ==========================================================================
def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with tb_label (+1 long / -1 short) and tb_pnl (labeled-side
    net-of-fee PnL).  Replicates the /059 production triple-barrier rule.
    """
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
    pnls = np.full(n, np.nan, dtype=np.float64)

    for i in range(n):
        entry = close[i]
        if entry <= 0:
            continue
        atr = (natr[i] / 100.0) * entry if np.isfinite(natr[i]) else entry * 0.02
        tp_dist = atr * TP_MULT
        sl_dist = atr * SL_MULT
        long_tp, long_sl = entry + tp_dist, entry - sl_dist
        short_tp, short_sl = entry - tp_dist, entry + sl_dist
        deadline = close_time[i] + timeout_ms

        long_result = short_result = 0
        long_step = short_step = -1
        last_close = entry
        j = i + 1
        while j < n:
            if close_time[j] > deadline:
                if long_result == 0:
                    long_result, long_step = -2, j
                if short_result == 0:
                    short_result, short_step = -2, j
                break
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_result == 0:
                if lo <= long_sl:
                    long_result, long_step = -1, j
                elif h >= long_tp:
                    long_result, long_step = 1, j
            if short_result == 0:
                if h >= short_sl:
                    short_result, short_step = -1, j
                elif lo <= short_tp:
                    short_result, short_step = 1, j
            if long_result != 0 and short_result != 0:
                break
            j += 1
        else:
            if long_result == 0:
                long_result, long_step = -2, n
            if short_result == 0:
                short_result, short_step = -2, n

        fwd_ret = (last_close - entry) / entry * 100.0 if entry != 0 else 0.0
        tp_pnl_pct = tp_dist / entry * 100.0
        sl_pnl_pct = sl_dist / entry * 100.0

        def side_pnl(result: int, signed_fwd: float) -> float:
            if result == 1:
                return tp_pnl_pct - FEE_PCT
            if result == -1:
                return -sl_pnl_pct - FEE_PCT
            return signed_fwd - FEE_PCT

        long_pnl = side_pnl(long_result, fwd_ret)
        short_pnl = side_pnl(short_result, -fwd_ret)
        long_tp_hit = long_result == 1
        short_tp_hit = short_result == 1
        if long_tp_hit and not short_tp_hit:
            lab = 1
        elif short_tp_hit and not long_tp_hit:
            lab = -1
        elif long_tp_hit and short_tp_hit:
            lab = 1 if long_step <= short_step else -1
        else:
            lab = 1 if fwd_ret >= 0 else -1
        labels[i] = lab
        pnls[i] = long_pnl if lab == 1 else short_pnl

    out["tb_label"] = labels
    out["tb_pnl"] = pnls
    return out


def load_full_panel(symbol: str) -> pd.DataFrame:
    """Load a symbol's feature parquet, sort, return the FULL panel (the IS
    mask is applied by the caller after labeling)."""
    df = pd.read_parquet(DATA_DIR / f"{symbol}_8h_features.parquet")
    return df.sort_values("open_time").reset_index(drop=True)


def is_window(symbol: str) -> tuple[int, int]:
    """Return (burnin_end_ms, OOS_CUTOFF_MS) — the IS window for `symbol`."""
    df = load_full_panel(symbol)
    first_ms = int(df["open_time"].min())
    return first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY, OOS_CUTOFF_MS


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/102 EDA Script 1 — formulaic-alpha feature->label IC")
    print("Basket: v3-portable WorldQuant-101 time-series-pure alphas")
    print(f"Label: /059 triple-barrier, {TIMEOUT_MIN}-min = 21-candle timeout")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every IC row IS-only")
    print("=" * 78)

    alpha_names = list(ALPHA_REGISTRY.keys())

    # ---- build per-symbol IS panels with alphas + label ----
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    for sym in SYMBOLS:
        full = load_full_panel(sym)
        # build every alpha on the FULL panel (past-only) BEFORE masking
        for name, fn in ALPHA_REGISTRY.items():
            full[name] = fn(full).astype(float)
        # /059 triple-barrier label on the FULL panel
        full = triple_barrier_label(full)
        # IS mask: 24-month burn-in <= t < OOS cutoff
        first_ms = int(full["open_time"].min())
        burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
        is_mask = (full["open_time"] >= burnin_end) & (
            full["open_time"] < OOS_CUTOFF_MS
        )
        isd = full[is_mask].copy().reset_index(drop=True)
        isd["symbol"] = sym
        panels[sym] = isd
        t1_rows.append(
            {
                "symbol": sym,
                "is_rows": len(isd),
                "is_first": str(
                    pd.to_datetime(isd["open_time"].min(), unit="ms").date()
                ),
                "is_last": str(
                    pd.to_datetime(isd["open_time"].max(), unit="ms").date()
                ),
                "long_label_frac": round(
                    float((isd["tb_label"] == 1).mean()), 4
                ),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_is_panel_summary.csv", index=False)
    print("\nT1 — IS panel summary (post-24mo-burnin, IS-only):")
    print(t1.to_string(index=False))

    # ---- T2: per-(alpha, symbol) directional Spearman IC vs the label ----
    # IC = Spearman corr of alpha_t (past-only) with the {+1,-1} label of bar t.
    print("\nT2 — formulaic-alpha feature->label Spearman IC (IS-only):")
    print("  IC = corr(alpha_t, tb_label_t); tb_label in {+1 long, -1 short}.")
    t2_rows = []
    for name in alpha_names:
        per_sym_ic = {}
        cov_frac = {}
        for sym in SYMBOLS:
            d = panels[sym]
            a = d[name]
            lab = d["tb_label"].astype(float)
            valid = a.notna() & lab.notna() & np.isfinite(a)
            n_valid = int(valid.sum())
            cov_frac[sym] = round(n_valid / len(d), 3) if len(d) else 0.0
            if n_valid < 100 or a[valid].nunique() < 5:
                per_sym_ic[sym] = np.nan
                continue
            ic = a[valid].rank().corr(lab[valid].rank())
            per_sym_ic[sym] = ic
        ics = [v for v in per_sym_ic.values() if pd.notna(v)]
        mean_abs = float(np.mean([abs(v) for v in ics])) if ics else np.nan
        # sign agreement: do all symbols' ICs share a sign?
        signs = {np.sign(v) for v in ics if abs(v) > 1e-6}
        sign_consistent = len(signs) == 1 and len(ics) == len(SYMBOLS)
        t2_rows.append(
            {
                "alpha": name,
                "note": ALPHA_NOTES[name],
                "ic_BCH": round(per_sym_ic["BCHUSDT"], 4)
                if pd.notna(per_sym_ic["BCHUSDT"])
                else np.nan,
                "ic_LDO": round(per_sym_ic["LDOUSDT"], 4)
                if pd.notna(per_sym_ic["LDOUSDT"])
                else np.nan,
                "ic_TRX": round(per_sym_ic["TRXUSDT"], 4)
                if pd.notna(per_sym_ic["TRXUSDT"])
                else np.nan,
                "mean_abs_ic": round(mean_abs, 4)
                if pd.notna(mean_abs)
                else np.nan,
                "sign_consistent_3sym": sign_consistent,
                "min_coverage_frac": min(cov_frac.values()),
            }
        )
    t2 = pd.DataFrame(t2_rows).sort_values(
        "mean_abs_ic", ascending=False, na_position="last"
    )
    t2.to_csv(OUT / "T2_alpha_label_ic.csv", index=False)
    print(t2.to_string(index=False))
    print(
        "\n  Reference: the 14 incumbent V3_FEATURE_COLUMNS have thin IC "
        "(/096: +0.025 BCH / +0.029 TRX).  An alpha is IC-interesting if its "
        "mean |IC| is at least comparable AND its sign is 3-symbol consistent."
    )

    # ---- T3: past-only adversarial audit (the LdP look-ahead test) ----
    # Recompute each alpha on a panel truncated 50 bars early; the overlap must
    # be bit-identical.  Any alpha that changes is look-ahead-contaminated.
    print("\nT3 — past-only adversarial audit (truncate-50-bars, bit-identity):")
    TRUNC = 50
    t3_rows = []
    for sym in SYMBOLS:
        full = load_full_panel(sym)
        truncated = full.iloc[: len(full) - TRUNC].copy()
        for name, fn in ALPHA_REGISTRY.items():
            a_full = fn(full).astype(float).to_numpy()
            a_trunc = fn(truncated).astype(float).to_numpy()
            overlap = len(truncated)
            ov_full = a_full[:overlap]
            ov_trunc = a_trunc[:overlap]
            both_nan = np.isnan(ov_full) & np.isnan(ov_trunc)
            both_val = ~np.isnan(ov_full) & ~np.isnan(ov_trunc)
            max_abs_diff = (
                float(np.nanmax(np.abs(ov_full[both_val] - ov_trunc[both_val])))
                if both_val.any()
                else 0.0
            )
            nan_mismatch = int((~both_nan & ~both_val).sum())
            t3_rows.append(
                {
                    "symbol": sym,
                    "alpha": name,
                    "max_abs_diff_overlap": max_abs_diff,
                    "nan_pattern_mismatch": nan_mismatch,
                    "past_only_ok": max_abs_diff < 1e-9 and nan_mismatch == 0,
                }
            )
    t3 = pd.DataFrame(t3_rows)
    t3.to_csv(OUT / "T3_past_only_audit.csv", index=False)
    n_fail = int((~t3["past_only_ok"]).sum())
    print(t3.to_string(index=False))
    print(
        f"\n  -> {n_fail}/{len(t3)} (alpha, symbol) cells FAIL the past-only "
        f"bit-identity audit.  A failing alpha is look-ahead-contaminated and "
        f"is DISQUALIFIED from the /102 axis basket."
    )

    print("\n" + "=" * 78)
    print("Script 1 done.  Outputs: T1_is_panel_summary.csv, "
          "T2_alpha_label_ic.csv, T3_past_only_audit.csv")
    print("Next: alpha_redundancy_eda.py (IC sign-stability + |IC| vs the 14 "
          "incumbents).")
    print("=" * 78)


if __name__ == "__main__":
    main()

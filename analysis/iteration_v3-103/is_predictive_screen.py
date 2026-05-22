"""iter-v3/103 — EDA Script 2: IS-PREDICTIVE screen of the candidate basket.

THE /102-CORRECTED SELECTION CRITERION
--------------------------------------
iter-v3/102 selected alpha032 on a held-out-tail single-classifier accuracy
proxy (T6 dShACC). The /102 closeout (Critic Recommendation 2) ruled that proxy
does NOT predict the multi-seed Optuna IS fit — it optimises an OOS-leaning
statistic. /103's selection evidence is built to be IS-PREDICTIVE:

  T1  IS panel summary (rows, span, long-label fraction).
  T2  Per-(candidate, symbol) directional Spearman IC vs the /059 triple-barrier
      label, STRICTLY IS-ONLY. The proven v3 directional-IC measure.
  T3  SIGN-CONSISTENCY across all 3 symbols. alpha032's IS IC flipped sign
      (BCH -0.0255 / LDO +0.0413 / TRX +0.0395 -> sign_consistent=False) yet was
      selected anyway. A genuinely IS-predictive feature must carry the SAME
      directional meaning on every symbol of a pooled-discipline universe.
  T4  IS SUB-PERIOD STABILITY. Each symbol's IS window is split into an early
      half and a late half (chronological). The IC sign must hold in BOTH halves
      per symbol. This is an IN-SAMPLE stability test — it never touches the
      post-cutoff OOS — and it is the direct antidote to the /102 held-out-tail
      trap: instead of asking "does it work on a withheld tail" it asks "is the
      IS relationship itself stable", which is what a multi-seed IS Optuna fit
      actually consumes.

A candidate ADVANCES only if it is sign-consistent (T3) AND sub-period-stable
(T4) AND has a non-trivial mean |IC| (T2). The horse-race / held-out-tail
methodology is deliberately NOT used.

NO-CHEATING
-----------
OOS_CUTOFF_MS = 1742774400000 (2025-03-24). Every row entering any IC or
stability computation has open_time < OOS_CUTOFF_MS. The post-cutoff OOS is
NEVER read. The triple-barrier label is built on the FULL panel then IS-masked
(the 21-bar forward scan for the last few IS rows legitimately reads
post-cutoff candles — that is exactly how labeling.py:label_trades works; it is
NOT a feature look-ahead, identical to the /102 EDA convention).

RUN:  uv run python analysis/iteration_v3-103/is_predictive_screen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate_lib import CANDIDATE_REGISTRY  # noqa: E402

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 — IMMUTABLE
TRAINING_MONTHS = 24
TIMEOUT_MIN = 10080  # 21 candles at 8h — the /059 canonical label
TP_MULT = 2.0
SL_MULT = 1.0
FEE_PCT = 0.1
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
DATA_DIR = Path("data/features_v3")
OUT = Path("analysis/iteration_v3-103")
MS_PER_DAY = 24 * 60 * 60 * 1000


def triple_barrier_label(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with tb_label (+1 long / -1 short). Faithful replication of
    labeling.py:label_trades — identical to the /102 EDA implementation."""
    out = df.reset_index(drop=True).copy()
    n = len(out)
    high = out["high"].to_numpy(dtype=np.float64)
    low = out["low"].to_numpy(dtype=np.float64)
    close = out["close"].to_numpy(dtype=np.float64)
    close_time = out["close_time"].to_numpy(dtype=np.int64)
    natr = out["natr_21_raw"].to_numpy(dtype=np.float64)
    timeout_ms = TIMEOUT_MIN * 60 * 1000

    labels = np.zeros(n, dtype=np.int64)
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
    out["tb_label"] = labels
    return out


def load_full_panel(symbol: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / f"{symbol}_8h_features.parquet")
    return df.sort_values("open_time").reset_index(drop=True)


def spearman_ic(feat: pd.Series, lab: pd.Series) -> tuple[float, int]:
    """directional Spearman IC of a past-only feature vs the {+1,-1} label.
    Returns (ic, n_valid). NaN ic if too few valid / too few distinct values."""
    valid = feat.notna() & lab.notna() & np.isfinite(feat)
    n_valid = int(valid.sum())
    if n_valid < 100 or feat[valid].nunique() < 5:
        return np.nan, n_valid
    ic = feat[valid].rank().corr(lab[valid].rank())
    return float(ic), n_valid


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/103 EDA Script 2 — IS-PREDICTIVE screen of composed-feature basket")
    print(f"OOS_CUTOFF_MS = {OOS_CUTOFF_MS} (2025-03-24) — every row strictly IS-only")
    print(f"Label: /059 triple-barrier, {TIMEOUT_MIN}-min = 21-candle timeout")
    print("=" * 78)

    cand_names = list(CANDIDATE_REGISTRY.keys())

    # ---- build per-symbol IS panels: candidates + label, then IS-mask --------
    panels: dict[str, pd.DataFrame] = {}
    t1_rows = []
    for sym in SYMBOLS:
        full = load_full_panel(sym)
        for name, (fn, _note) in CANDIDATE_REGISTRY.items():
            full[name] = fn(full).astype(float)
        full = triple_barrier_label(full)
        first_ms = int(full["open_time"].min())
        burnin_end = first_ms + TRAINING_MONTHS * 30 * MS_PER_DAY
        is_mask = (full["open_time"] >= burnin_end) & (full["open_time"] < OOS_CUTOFF_MS)
        isd = full[is_mask].copy().reset_index(drop=True)
        isd["symbol"] = sym
        panels[sym] = isd
        t1_rows.append(
            {
                "symbol": sym,
                "is_rows": len(isd),
                "is_first": str(pd.to_datetime(isd["open_time"].min(), unit="ms").date()),
                "is_last": str(pd.to_datetime(isd["open_time"].max(), unit="ms").date()),
                "long_label_frac": round(float((isd["tb_label"] == 1).mean()), 4),
            }
        )
    t1 = pd.DataFrame(t1_rows)
    t1.to_csv(OUT / "T1_is_panel_summary.csv", index=False)
    print("\nT1 — IS panel summary (post-24mo-burnin, IS-only):")
    print(t1.to_string(index=False))

    # ---- T2 + T3: per-symbol directional IC + sign-consistency --------------
    print("\nT2/T3 — directional Spearman IC (IS-only) + 3-symbol sign-consistency:")
    t2_rows = []
    for name in cand_names:
        ics: dict[str, float] = {}
        covs: dict[str, float] = {}
        for sym in SYMBOLS:
            d = panels[sym]
            ic, n_valid = spearman_ic(d[name], d["tb_label"].astype(float))
            ics[sym] = ic
            covs[sym] = round(n_valid / len(d), 3) if len(d) else 0.0
        valid_ics = [v for v in ics.values() if pd.notna(v)]
        mean_abs = float(np.mean([abs(v) for v in valid_ics])) if valid_ics else np.nan
        signs = {int(np.sign(v)) for v in valid_ics if abs(v) > 1e-6}
        sign_consistent = len(signs) == 1 and len(valid_ics) == len(SYMBOLS)
        t2_rows.append(
            {
                "candidate": name,
                "ic_BCH": round(ics["BCHUSDT"], 4) if pd.notna(ics["BCHUSDT"]) else np.nan,
                "ic_LDO": round(ics["LDOUSDT"], 4) if pd.notna(ics["LDOUSDT"]) else np.nan,
                "ic_TRX": round(ics["TRXUSDT"], 4) if pd.notna(ics["TRXUSDT"]) else np.nan,
                "mean_abs_ic": round(mean_abs, 4) if pd.notna(mean_abs) else np.nan,
                "sign_consistent_3sym": sign_consistent,
                "min_coverage_frac": min(covs.values()),
            }
        )
    t2 = pd.DataFrame(t2_rows).sort_values("mean_abs_ic", ascending=False)
    t2.to_csv(OUT / "T2_is_directional_ic.csv", index=False)
    print(t2.to_string(index=False))

    # ---- T4: IS sub-period stability (early half vs late half, IS-only) -----
    # The IC sign must hold in BOTH chronological halves of the IS window, per
    # symbol. This is an IN-SAMPLE stability test (the post-cutoff OOS is never
    # touched) — the /102-corrected antidote to the held-out-tail proxy.
    print("\nT4 — IS sub-period stability (early-half vs late-half IC sign, IS-only):")
    t4_rows = []
    for name in cand_names:
        per_sym = {}
        all_stable = True
        for sym in SYMBOLS:
            d = panels[sym]
            mid = len(d) // 2
            early = d.iloc[:mid]
            late = d.iloc[mid:]
            ic_e, _ = spearman_ic(early[name], early["tb_label"].astype(float))
            ic_l, _ = spearman_ic(late[name], late["tb_label"].astype(float))
            stable = (
                pd.notna(ic_e)
                and pd.notna(ic_l)
                and abs(ic_e) > 1e-6
                and abs(ic_l) > 1e-6
                and np.sign(ic_e) == np.sign(ic_l)
            )
            per_sym[sym] = (ic_e, ic_l, stable)
            all_stable = all_stable and stable
        t4_rows.append(
            {
                "candidate": name,
                "ic_early_BCH": round(per_sym["BCHUSDT"][0], 4)
                if pd.notna(per_sym["BCHUSDT"][0])
                else np.nan,
                "ic_late_BCH": round(per_sym["BCHUSDT"][1], 4)
                if pd.notna(per_sym["BCHUSDT"][1])
                else np.nan,
                "ic_early_LDO": round(per_sym["LDOUSDT"][0], 4)
                if pd.notna(per_sym["LDOUSDT"][0])
                else np.nan,
                "ic_late_LDO": round(per_sym["LDOUSDT"][1], 4)
                if pd.notna(per_sym["LDOUSDT"][1])
                else np.nan,
                "ic_early_TRX": round(per_sym["TRXUSDT"][0], 4)
                if pd.notna(per_sym["TRXUSDT"][0])
                else np.nan,
                "ic_late_TRX": round(per_sym["TRXUSDT"][1], 4)
                if pd.notna(per_sym["TRXUSDT"][1])
                else np.nan,
                "stable_BCH": per_sym["BCHUSDT"][2],
                "stable_LDO": per_sym["LDOUSDT"][2],
                "stable_TRX": per_sym["TRXUSDT"][2],
                "all_3sym_stable": all_stable,
            }
        )
    t4 = pd.DataFrame(t4_rows)
    t4.to_csv(OUT / "T4_is_subperiod_stability.csv", index=False)
    print(t4.to_string(index=False))

    # ---- combined screen verdict --------------------------------------------
    print("\n" + "=" * 78)
    print("IS-PREDICTIVE SCREEN VERDICT (sign-consistent AND sub-period-stable):")
    t2_idx = t2.set_index("candidate")
    t4_idx = t4.set_index("candidate")
    verdict_rows = []
    for name in cand_names:
        sc = bool(t2_idx.loc[name, "sign_consistent_3sym"])
        st = bool(t4_idx.loc[name, "all_3sym_stable"])
        mic = t2_idx.loc[name, "mean_abs_ic"]
        advances = sc and st and pd.notna(mic) and mic >= 0.020
        verdict_rows.append(
            {
                "candidate": name,
                "mean_abs_ic": mic,
                "sign_consistent": sc,
                "subperiod_stable": st,
                "ADVANCES": advances,
            }
        )
        flag = "ADVANCES" if advances else "rejected"
        print(f"  {name:34s}  |IC|={mic:.4f}  sign={sc!s:5s}  stable={st!s:5s}  -> {flag}")
    pd.DataFrame(verdict_rows).to_csv(OUT / "T2T4_screen_verdict.csv", index=False)
    print("=" * 78)


if __name__ == "__main__":
    main()

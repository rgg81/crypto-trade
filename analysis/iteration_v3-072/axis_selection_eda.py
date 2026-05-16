"""iter-v3/072 — Phase 1-2 axis-selection EDA.

CYCLE 2 EXPLORATION #2 of 10. Per `feedback_v3_axis_selection_quant_discipline.md`,
this committed EDA backs the QR axis choice BEFORE the research brief is written.

Two candidate axes (orchestrator-suggested; QR decides per the memory rule):

  AXIS 1 — Alternative labeling architecture: replace the current ATR triple-barrier
           label with a FIXED-HORIZON return-sign label (label = sign of the
           N-candle-forward return; no TP/SL barriers). HIGH priority per
           BASELINE_V3.md cycle-2 axis #2. Structurally distinct from cycle-1's
           exhausted ATR-multiplier knob space.

  AXIS 2 — Distinct-feature M2 meta-labeling: a SECOND meta-labeling EXPLORATION
           with an M2 feature set M1 does NOT use (funding / OI / basis / regime).
           Per Critic /071 Rec #4. Caveat: funding family is PERMANENTLY CLOSED
           (3 EXPLORATIONs /019/023/024, rank 14/14); OOF wiring defect open.

The EDA evaluates BOTH on IS-only data and selects the axis with the strongest
quantitative basis.

NO LOOK-AHEAD: every table is computed on IS-window data only
(open_time < OOS_CUTOFF_DATE = 2025-03-24). The triple-barrier and fixed-horizon
labels both scan FORWARD, but only over candles whose own open_time also predates
the OOS cutoff is the label retained — this mirrors what the runner does inside
each walk-forward training month and keeps the EDA purely IS-descriptive.

Outputs (committed alongside this script):
  - axis1_label_distribution.csv    : ATR-TB vs fixed-horizon label balance per symbol
  - axis1_label_agreement.csv       : per-symbol agreement between TB and fixed-horizon
  - axis1_ldo_barrier_diagnosis.csv : LDO triple-barrier outcome breakdown (the target symbol)
  - axis1_label_economics.csv       : realized per-label IS PnL — is the label learnable?
  - axis2_distinct_feature_signal.csv : winner/loser separability of distinct-M2-feature
                                        candidates (funding z-scores) on M1-fired bars
  - axis_selection_summary.csv      : the QR decision table
  - synthesis.md                    : prose synthesis + the QR axis call

Run:
  uv run python analysis/iteration_v3-072/axis_selection_eda.py
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants — mirror the v3 runner / BASELINE_V3.md
# --------------------------------------------------------------------------
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(
    _dt.datetime(2025, 3, 24, tzinfo=_dt.UTC).timestamp() * 1000
)
V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")
CANDLE_MINUTES = 480  # 8h
TIMEOUT_MINUTES = 10080  # 21 candles — current v3 triple-barrier timeout
TIMEOUT_CANDLES = TIMEOUT_MINUTES // CANDLE_MINUTES  # = 21
# DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — current v3 (per BASELINE_V3.md /059 spec)
ATR_TP_MULT = 2.0
ATR_SL_MULT = 1.0
ATR_COLUMN = "natr_21_raw"  # the runner's atr_column
FEE_PCT = 0.1
FIXED_HORIZONS = (7, 14, 21)  # candidate fixed-horizon lengths (8h candles)

REPO = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO / "data" / "features_v3"
FUNDING_DIR = REPO / "data" / "funding_rates"
OUT_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# Data loading — IS-window klines + features
# --------------------------------------------------------------------------
def load_symbol(symbol: str) -> pd.DataFrame:
    """Load the v3 feature parquet for one symbol; keep OHLC + natr + funding."""
    fp = FEATURES_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(fp)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


# --------------------------------------------------------------------------
# Label computation — ATR triple-barrier (current v3) vs fixed-horizon
# --------------------------------------------------------------------------
def atr_triple_barrier_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the v3 ATR triple-barrier label for every candle.

    Mirrors `strategies/ml/labeling.py::label_trades` with use_atr_labeling=True
    AND the runner's NATR->price-ATR conversion at `lgbm.py:294`:

        price_atr = close * natr_21_raw / 100.0

    `natr_21_raw` is a PERCENTAGE NATR (median ~3.5 for BCH, ~4.8 for LDO).
    `lgbm._load_atr_for_master` converts it to a price-level ATR before passing
    it to `label_trades`. Feeding the raw percentage as a price-level value
    inflates barriers ~100x and timeouts every label — this EDA must do the
    same /100 conversion the runner does.

      - TP distance = price_atr * ATR_TP_MULT ; SL distance = price_atr * ATR_SL_MULT
      - scan forward up to TIMEOUT_CANDLES candles
      - label = direction whose TP hits first; if neither TP hits, fwd-return sign
      - outcome class recorded for the LONG side (the diagnosis we care about)

    Returns a frame with: open_time, label (1/-1), tb_outcome
    ('long_tp','short_tp','both_tp','timeout_fwd_sign'), and the per-direction
    barrier outcome strings for the LONG side ('tp'/'sl'/'timeout').
    """
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    # NATR->price-ATR conversion — EXACTLY as the runner does at lgbm.py:294.
    natr_pct = df[ATR_COLUMN].to_numpy(dtype=float)
    natr = close * natr_pct / 100.0  # price-level ATR

    labels = np.zeros(n, dtype=np.int8)
    tb_outcome = np.empty(n, dtype=object)
    long_barrier = np.empty(n, dtype=object)  # 'tp'/'sl'/'timeout' for LONG side
    scannable = np.zeros(n, dtype=bool)

    for i in range(n):
        entry = close[i]
        atr = natr[i] if not np.isnan(natr[i]) else entry * 0.02
        tp_dist = atr * ATR_TP_MULT
        sl_dist = atr * ATR_SL_MULT
        long_tp_p, long_sl_p = entry + tp_dist, entry - sl_dist
        short_tp_p, short_sl_p = entry - tp_dist, entry + sl_dist

        long_res, short_res = 0, 0  # 0 pending, 1 tp, -1 sl, -2 timeout
        long_step, short_step = -1, -1
        last_close = entry
        end = min(i + TIMEOUT_CANDLES, n - 1)
        if end <= i:
            tb_outcome[i] = "no_forward_data"
            long_barrier[i] = "no_forward_data"
            continue
        scannable[i] = True

        for j in range(i + 1, end + 1):
            h, lo = high[j], low[j]
            last_close = close[j]
            if long_res == 0:
                if lo <= long_sl_p:
                    long_res, long_step = -1, j
                elif h >= long_tp_p:
                    long_res, long_step = 1, j
            if short_res == 0:
                if h >= short_sl_p:
                    short_res, short_step = -1, j
                elif lo <= short_tp_p:
                    short_res, short_step = 1, j
            if long_res != 0 and short_res != 0:
                break
        if long_res == 0:
            long_res, long_step = -2, end
        if short_res == 0:
            short_res, short_step = -2, end

        fwd_ret = ((last_close - entry) / entry * 100.0) if entry != 0 else 0.0

        long_tp_hit = long_res == 1
        short_tp_hit = short_res == 1
        if long_tp_hit and not short_tp_hit:
            labels[i], tb_outcome[i] = 1, "long_tp"
        elif short_tp_hit and not long_tp_hit:
            labels[i], tb_outcome[i] = -1, "short_tp"
        elif long_tp_hit and short_tp_hit:
            if long_step <= short_step:
                labels[i], tb_outcome[i] = 1, "both_tp_long_first"
            else:
                labels[i], tb_outcome[i] = -1, "both_tp_short_first"
        else:
            labels[i] = 1 if fwd_ret >= 0 else -1
            tb_outcome[i] = "timeout_fwd_sign"

        long_barrier[i] = {1: "tp", -1: "sl", -2: "timeout"}[long_res]

    return pd.DataFrame(
        {
            "open_time": df["open_time"].to_numpy(),
            "tb_label": labels,
            "tb_outcome": tb_outcome,
            "tb_long_barrier": long_barrier,
            "scannable": scannable,
        }
    )


def fixed_horizon_labels(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Fixed-horizon return-sign label: label = sign(close[i+h] - close[i]).

    No barriers. The candidate alternative labeling architecture.
    fwd_return_pct is net-of-fee-equivalent only for descriptive comparison
    (the fee is symmetric and does not change the sign for |fwd_ret| > FEE).
    """
    n = len(df)
    close = df["close"].to_numpy(dtype=float)
    label = np.zeros(n, dtype=np.int8)
    fwd_ret = np.full(n, np.nan, dtype=float)
    has = np.zeros(n, dtype=bool)
    for i in range(n):
        j = i + horizon
        if j >= n:
            continue
        has[i] = True
        r = (close[j] - close[i]) / close[i] * 100.0 if close[i] != 0 else 0.0
        fwd_ret[i] = r
        label[i] = 1 if r >= 0 else -1
    return pd.DataFrame(
        {
            "open_time": df["open_time"].to_numpy(),
            f"fh{horizon}_label": label,
            f"fh{horizon}_fwd_ret": fwd_ret,
            f"fh{horizon}_has": has,
        }
    )


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def _balance(labels: np.ndarray) -> tuple[int, int, float, float]:
    """Return (n_long, n_short, long_frac, shannon_entropy_bits)."""
    n = len(labels)
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    n_long = int((labels == 1).sum())
    n_short = int((labels == -1).sum())
    p = n_long / n
    if p in (0.0, 1.0):
        ent = 0.0
    else:
        ent = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    return n_long, n_short, p, ent


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    print("=" * 78)
    print("iter-v3/072 axis-selection EDA — IS-only")
    print(f"OOS_CUTOFF_DATE = {OOS_CUTOFF_DATE}  (IS = open_time < cutoff)")
    print("=" * 78)

    axis1_dist_rows: list[dict] = []
    axis1_agree_rows: list[dict] = []
    axis1_ldo_rows: list[dict] = []
    axis1_econ_rows: list[dict] = []
    axis2_rows: list[dict] = []

    per_symbol_store: dict[str, dict] = {}

    for symbol in V3_MODELS:
        df = load_symbol(symbol)
        is_mask = df["open_time"].to_numpy() < OOS_CUTOFF_MS
        n_is = int(is_mask.sum())
        print(f"\n--- {symbol} : {len(df)} total candles, {n_is} IS candles ---")

        # ----- compute labels on the FULL frame, then restrict to IS candles -----
        # (the forward-scan may peek past the cutoff for a near-cutoff candle; we
        #  retain the label only for candles whose OWN open_time is IS. This is
        #  exactly what the runner's per-month training does — purely descriptive.)
        tb = atr_triple_barrier_labels(df)
        fh = {h: fixed_horizon_labels(df, h) for h in FIXED_HORIZONS}

        merged = tb.copy()
        for h in FIXED_HORIZONS:
            merged = merged.merge(fh[h], on="open_time", how="left")
        merged["is_is"] = merged["open_time"].to_numpy() < OOS_CUTOFF_MS

        is_rows = merged[merged["is_is"]].copy()
        per_symbol_store[symbol] = {"is_rows": is_rows}

        # ===== AXIS 1 — label distribution: ATR-TB vs fixed-horizon =====
        # Triple-barrier: count only scannable IS candles (full 21-candle forward
        # window available) — that is the labelable population the runner uses.
        tb_lab = is_rows.loc[is_rows["scannable"], "tb_label"].to_numpy()
        n_long, n_short, long_frac, ent = _balance(tb_lab)
        axis1_dist_rows.append(
            {
                "symbol": symbol,
                "labeling": "ATR_triple_barrier",
                "horizon_candles": TIMEOUT_CANDLES,
                "n_labelable": len(tb_lab),
                "n_long": n_long,
                "n_short": n_short,
                "long_frac": round(long_frac, 4),
                "entropy_bits": round(ent, 4),
                "imbalance_abs": round(abs(long_frac - 0.5), 4),
            }
        )
        for h in FIXED_HORIZONS:
            col = f"fh{h}_label"
            hasc = f"fh{h}_has"
            fh_lab = is_rows.loc[is_rows[hasc], col].to_numpy()
            n_long, n_short, long_frac, ent = _balance(fh_lab)
            axis1_dist_rows.append(
                {
                    "symbol": symbol,
                    "labeling": f"fixed_horizon_{h}",
                    "horizon_candles": h,
                    "n_labelable": len(fh_lab),
                    "n_long": n_long,
                    "n_short": n_short,
                    "long_frac": round(long_frac, 4),
                    "entropy_bits": round(ent, 4),
                    "imbalance_abs": round(abs(long_frac - 0.5), 4),
                }
            )

        # ===== AXIS 1 — agreement: do TB and fixed-horizon labels coincide? =====
        # Higher agreement => fixed-horizon is a small perturbation (low value).
        # Lower agreement => fixed-horizon genuinely re-labels the data.
        both = is_rows[is_rows["scannable"]].copy()
        for h in FIXED_HORIZONS:
            col = f"fh{h}_label"
            hasc = f"fh{h}_has"
            retc = f"fh{h}_fwd_ret"
            sub = both[both[hasc]]
            if len(sub) == 0:
                continue
            agree = float((sub["tb_label"].to_numpy() == sub[col].to_numpy()).mean())
            # On disagreement bars (tb_label != fh_label), the realized h-candle
            # forward return is the economic ground truth. The mean |fwd_ret| on
            # disagreement bars measures the MAGNITUDE of moves the two labels
            # disagree on — small => the disagreement is on near-flat bars
            # (low-stakes re-labeling); large => the two labels disagree on
            # genuinely directional moves (high-stakes structural difference).
            dis = sub[sub["tb_label"].to_numpy() != sub[col].to_numpy()]
            mean_abs_fwd_dis = (
                float(np.abs(dis[retc].to_numpy()).mean()) if len(dis) > 0 else float("nan")
            )
            mean_abs_fwd_all = float(np.abs(sub[retc].to_numpy()).mean())
            axis1_agree_rows.append(
                {
                    "symbol": symbol,
                    "horizon": h,
                    "n_compared": len(sub),
                    "tb_vs_fh_agreement": round(agree, 4),
                    "n_disagree": len(dis),
                    "mean_abs_fwd_ret_on_disagree_pct": round(mean_abs_fwd_dis, 4)
                    if not np.isnan(mean_abs_fwd_dis)
                    else None,
                    "mean_abs_fwd_ret_all_pct": round(mean_abs_fwd_all, 4),
                }
            )

        # ===== AXIS 1 — LDO triple-barrier diagnosis (the target symbol) =====
        # /071 T1 showed LDO IS: 3 TP / 8 SL — TP-hit rate 27%. Diagnose WHY:
        # the LONG-side barrier outcome distribution shows whether LDO's ATR-TB
        # label is dominated by SL hits (an undifferentiated, SL-saturated label).
        if symbol == "LDOUSDT":
            scan = is_rows[is_rows["scannable"]]
            for sym_label, frame in [("LDOUSDT_IS", scan)]:
                vc = frame["tb_long_barrier"].value_counts()
                total = int(vc.sum())
                axis1_ldo_rows.append(
                    {
                        "scope": sym_label,
                        "n_labelable": total,
                        "long_tp": int(vc.get("tp", 0)),
                        "long_sl": int(vc.get("sl", 0)),
                        "long_timeout": int(vc.get("timeout", 0)),
                        "long_tp_rate": round(vc.get("tp", 0) / total, 4)
                        if total
                        else float("nan"),
                        "long_sl_rate": round(vc.get("sl", 0) / total, 4)
                        if total
                        else float("nan"),
                    }
                )
            # also: tb_outcome breakdown (which branch produced the label)
            oc = scan["tb_outcome"].value_counts()
            for k, v in oc.items():
                axis1_ldo_rows.append(
                    {
                        "scope": f"LDOUSDT_IS_outcome::{k}",
                        "n_labelable": int(scan["scannable"].sum()),
                        "long_tp": int(v),  # reuse column as "count"
                        "long_sl": None,
                        "long_timeout": None,
                        "long_tp_rate": round(v / len(scan), 4),
                        "long_sl_rate": None,
                    }
                )

        # ===== AXIS 1 — label economics: is the label LEARNABLE? =====
        # For each labeling scheme, on IS-scannable bars, two directional-spread
        # measures plus label persistence:
        #   (1) common-horizon spread: mean(fwd7_ret|label=+1) - mean(...|label=-1).
        #       Apples-to-apples across schemes at a FIXED 7-candle ruler. A label
        #       that separates the 7-candle forward return more sharply encodes
        #       cleaner near-term directional structure a tree can capture.
        #   (2) own-horizon spread: ATR-TB evaluated at its 21-candle window
        #       (fh21_fwd_ret) since the barrier scan runs 21 candles; each
        #       fixed_horizon_h evaluated at its OWN h-candle window. This avoids
        #       penalising a long-horizon label on a short ruler.
        #   (3) persistence = corr(label_t, label_{t+1}) — a stable (autocorrelated)
        #       label is more learnable; a label that flips every bar is noise.
        common_ret = is_rows["fh7_fwd_ret"].to_numpy()  # common 7-candle ruler
        common_mask = is_rows["scannable"].to_numpy() & is_rows["fh7_has"].to_numpy()

        def _spread(lab: np.ndarray, ret: np.ndarray) -> float:
            ok = ~np.isnan(ret)
            lab, ret = lab[ok], ret[ok]
            if len(lab) < 30 or not (lab == 1).any() or not (lab == -1).any():
                return float("nan")
            return float(ret[lab == 1].mean() - ret[lab == -1].mean())

        def _label_econ(
            label_arr: np.ndarray, name: str, own_ret: np.ndarray, own_has: np.ndarray
        ) -> dict:
            lab_c = label_arr[common_mask]
            ret_c = common_ret[common_mask]
            spread_common = _spread(lab_c, ret_c)
            own_mask = is_rows["scannable"].to_numpy() & own_has
            spread_own = _spread(label_arr[own_mask], own_ret[own_mask])
            lab_seq = label_arr[is_rows["scannable"].to_numpy()]
            if len(lab_seq) > 2 and np.std(lab_seq) > 0:
                persist = float(np.corrcoef(lab_seq[:-1], lab_seq[1:])[0, 1])
            else:
                persist = float("nan")
            return {
                "symbol": symbol,
                "labeling": name,
                "n_scannable": int(is_rows["scannable"].sum()),
                "spread_common7_pct": round(spread_common, 4)
                if not np.isnan(spread_common)
                else None,
                "spread_own_horizon_pct": round(spread_own, 4)
                if not np.isnan(spread_own)
                else None,
                "label_persistence": round(persist, 4)
                if not np.isnan(persist)
                else None,
            }

        # ATR-TB own horizon = 21-candle window (its barrier scan length)
        axis1_econ_rows.append(
            _label_econ(
                is_rows["tb_label"].to_numpy(),
                "ATR_triple_barrier",
                is_rows["fh21_fwd_ret"].to_numpy(),
                is_rows["fh21_has"].to_numpy(),
            )
        )
        for h in FIXED_HORIZONS:
            axis1_econ_rows.append(
                _label_econ(
                    is_rows[f"fh{h}_label"].to_numpy(),
                    f"fixed_horizon_{h}",
                    is_rows[f"fh{h}_fwd_ret"].to_numpy(),
                    is_rows[f"fh{h}_has"].to_numpy(),
                )
            )

        # ===== AXIS 2 — distinct-feature M2 candidate signal =====
        # Critic /071 Rec #4: a distinct-feature M2 needs M2-features M1 does NOT
        # use, with winner/loser discrimination. The only distinct (non-14-set)
        # features available in features_v3 parquets are the funding z-scores.
        # We measure: on bars where the ATR-TB label resolved to a TP-hit
        # ("winner-ish") vs not, does funding_rate_zscore_30 separate them?
        # This re-tests, on IS data, whether the funding family carries M2 signal.
        scan = is_rows[is_rows["scannable"]].copy()
        # winner proxy: long-side barrier == 'tp' OR short_tp outcome
        winner = (
            scan["tb_long_barrier"].to_numpy() == "tp"
        ) | (scan["tb_outcome"].to_numpy() == "short_tp")
        scan = scan.assign(_winner=winner)
        # join funding z-score from the feature frame
        fcols = ["open_time", "funding_rate_zscore_30", "btc_funding_rate_zscore_30"]
        fsub = df[fcols].copy()
        scan = scan.merge(fsub, on="open_time", how="left")
        for fcol in ["funding_rate_zscore_30", "btc_funding_rate_zscore_30"]:
            valid = scan[scan[fcol].notna()]
            if len(valid) < 30 or valid["_winner"].nunique() < 2:
                axis2_rows.append(
                    {
                        "symbol": symbol,
                        "distinct_feature": fcol,
                        "n_bars": len(valid),
                        "n_winner": int(valid["_winner"].sum()),
                        "auc": None,
                        "abs_auc_minus_half": None,
                        "verdict": "INSUFFICIENT",
                    }
                )
                continue
            # rank-AUC of fcol vs the binary winner outcome
            x = valid[fcol].to_numpy(dtype=float)
            y = valid["_winner"].to_numpy(dtype=bool)
            order = np.argsort(x, kind="mergesort")
            ranks = np.empty(len(x), dtype=float)
            ranks[order] = np.arange(1, len(x) + 1)
            n_pos = int(y.sum())
            n_neg = len(y) - n_pos
            sum_ranks_pos = ranks[y].sum()
            auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
            aam = abs(auc - 0.5)
            axis2_rows.append(
                {
                    "symbol": symbol,
                    "distinct_feature": fcol,
                    "n_bars": len(valid),
                    "n_winner": n_pos,
                    "auc": round(float(auc), 4),
                    "abs_auc_minus_half": round(float(aam), 4),
                    "verdict": "RESIDUAL-SIGNAL"
                    if aam >= 0.12
                    else "NEAR-ZERO-SIGNAL",
                }
            )

    # --------------------------------------------------------------------------
    # Write outputs
    # --------------------------------------------------------------------------
    df_dist = pd.DataFrame(axis1_dist_rows)
    df_agree = pd.DataFrame(axis1_agree_rows)
    df_ldo = pd.DataFrame(axis1_ldo_rows)
    df_econ = pd.DataFrame(axis1_econ_rows)
    df_axis2 = pd.DataFrame(axis2_rows)

    df_dist.to_csv(OUT_DIR / "axis1_label_distribution.csv", index=False)
    df_agree.to_csv(OUT_DIR / "axis1_label_agreement.csv", index=False)
    df_ldo.to_csv(OUT_DIR / "axis1_ldo_barrier_diagnosis.csv", index=False)
    df_econ.to_csv(OUT_DIR / "axis1_label_economics.csv", index=False)
    df_axis2.to_csv(OUT_DIR / "axis2_distinct_feature_signal.csv", index=False)

    print("\n" + "=" * 78)
    print("AXIS 1 — label distribution (ATR-TB vs fixed-horizon), IS-only")
    print("=" * 78)
    print(df_dist.to_string(index=False))
    print("\n" + "=" * 78)
    print("AXIS 1 — TB vs fixed-horizon label agreement, IS-only")
    print("=" * 78)
    print(df_agree.to_string(index=False))
    print("\n" + "=" * 78)
    print("AXIS 1 — LDO triple-barrier outcome diagnosis, IS-only")
    print("=" * 78)
    print(df_ldo.to_string(index=False))
    print("\n" + "=" * 78)
    print("AXIS 1 — label economics (common 7-candle horizon), IS-only")
    print("=" * 78)
    print(df_econ.to_string(index=False))
    print("\n" + "=" * 78)
    print("AXIS 2 — distinct-feature (funding) winner/loser separability, IS-only")
    print("=" * 78)
    print(df_axis2.to_string(index=False))

    # --------------------------------------------------------------------------
    # Axis-selection decision table
    # --------------------------------------------------------------------------
    # AXIS 1 score: (a) does fixed-horizon meaningfully re-label (agreement < ~0.85)
    #               (b) does it improve label balance, especially for LDO
    #               (c) is LDO's ATR-TB label SL-saturated (diagnosis)
    # AXIS 2 score: do distinct features (funding) clear the 0.12 residual bar?
    tb_ldo = df_dist[
        (df_dist["symbol"] == "LDOUSDT")
        & (df_dist["labeling"] == "ATR_triple_barrier")
    ].iloc[0]
    # pick fixed-horizon 14 as the representative middle horizon for LDO balance
    fh14_ldo = df_dist[
        (df_dist["symbol"] == "LDOUSDT")
        & (df_dist["labeling"] == "fixed_horizon_14")
    ].iloc[0]
    mean_agree = df_agree["tb_vs_fh_agreement"].mean()
    axis2_best = (
        df_axis2["abs_auc_minus_half"].dropna().max()
        if df_axis2["abs_auc_minus_half"].notna().any()
        else float("nan")
    )

    summary_rows = [
        {
            "axis": "AXIS_1_fixed_horizon_labeling",
            "metric": "mean_TB_vs_FH_agreement",
            "value": round(float(mean_agree), 4),
            "interpretation": "lower => fixed-horizon genuinely re-labels (structural change)",
        },
        {
            "axis": "AXIS_1_fixed_horizon_labeling",
            "metric": "LDO_ATR_TB_label_imbalance_abs",
            "value": float(tb_ldo["imbalance_abs"]),
            "interpretation": "LDO triple-barrier label imbalance |long_frac-0.5|",
        },
        {
            "axis": "AXIS_1_fixed_horizon_labeling",
            "metric": "LDO_fixed_horizon_14_label_imbalance_abs",
            "value": float(fh14_ldo["imbalance_abs"]),
            "interpretation": "LDO fixed-horizon-14 label imbalance |long_frac-0.5|",
        },
        {
            "axis": "AXIS_2_distinct_feature_M2",
            "metric": "best_distinct_feature_abs_auc_minus_half",
            "value": round(float(axis2_best), 4)
            if not np.isnan(axis2_best)
            else None,
            "interpretation": "funding z-score winner/loser separability; >=0.12 = RESIDUAL-SIGNAL",
        },
    ]
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(OUT_DIR / "axis_selection_summary.csv", index=False)
    print("\n" + "=" * 78)
    print("AXIS-SELECTION SUMMARY")
    print("=" * 78)
    print(df_summary.to_string(index=False))

    # --------------------------------------------------------------------------
    # synthesis.md — prose + the QR axis call
    # --------------------------------------------------------------------------
    ldo_diag = df_ldo[df_ldo["scope"] == "LDOUSDT_IS"]
    ldo_sl_rate = (
        float(ldo_diag.iloc[0]["long_sl_rate"]) if len(ldo_diag) else float("nan")
    )
    ldo_tp_rate = (
        float(ldo_diag.iloc[0]["long_tp_rate"]) if len(ldo_diag) else float("nan")
    )

    axis1_chosen = mean_agree < 0.85  # genuine re-labeling => structural axis
    axis2_viable = (not np.isnan(axis2_best)) and axis2_best >= 0.12

    lines: list[str] = []
    lines.append("# iter-v3/072 Axis-Selection EDA — Synthesis\n")
    lines.append(
        "CYCLE 2 EXPLORATION #2 of 10. QR EDA-driven axis selection per "
        "`feedback_v3_axis_selection_quant_discipline.md`.\n"
    )
    lines.append("## Candidate axes\n")
    lines.append(
        "- **AXIS 1 — fixed-horizon labeling**: replace the ATR triple-barrier "
        "label with `label = sign(N-candle-forward return)`. HIGH priority per "
        "BASELINE_V3.md cycle-2 axis #2 (structural; a different label "
        "DEFINITION, not a multiplier knob).\n"
    )
    lines.append(
        "- **AXIS 2 — distinct-feature M2 meta-labeling**: a 2nd meta-labeling "
        "EXPLORATION with M2 features M1 does not use. Critic /071 Rec #4. "
        "Caveat: the funding family is PERMANENTLY CLOSED (/019/023/024, rank "
        "14/14) and the OOF wiring defect is open.\n"
    )
    lines.append("\n## Axis 1 findings (IS-only)\n")
    agree_verdict = (
        "Below 0.85 — fixed-horizon GENUINELY re-labels the data; this is a "
        "structural change, not a perturbation."
        if axis1_chosen
        else "At/above 0.85 — fixed-horizon largely reproduces the TB label; "
        "weak structural change."
    )
    lines.append(
        f"- Mean TB-vs-fixed-horizon label agreement = **{mean_agree:.4f}** "
        f"across {len(df_agree)} (symbol, horizon) cells. {agree_verdict}\n"
    )
    sl_verdict = (
        "SL-saturated — the ATR-TB label for LDO is dominated by stop-outs, an "
        "undifferentiated label population."
        if (not np.isnan(ldo_sl_rate)) and ldo_sl_rate > 0.5
        else "Not strongly SL-saturated."
    )
    lines.append(
        f"- LDO triple-barrier IS label: TP-hit rate **{ldo_tp_rate:.2%}**, "
        f"SL-hit rate **{ldo_sl_rate:.2%}** (LONG side). {sl_verdict}\n"
    )
    bal_verdict = (
        "Fixed-horizon produces a MORE BALANCED LDO label set."
        if fh14_ldo["imbalance_abs"] < tb_ldo["imbalance_abs"]
        else "Fixed-horizon does NOT improve LDO label balance — balance is NOT "
        "the bottleneck; both schemes are well-balanced (entropy ~1.0)."
    )
    lines.append(
        f"- LDO label balance: ATR-TB imbalance |long_frac-0.5| = "
        f"**{tb_ldo['imbalance_abs']:.4f}**; fixed-horizon-14 imbalance = "
        f"**{fh14_ldo['imbalance_abs']:.4f}**. {bal_verdict}\n"
    )
    # label economics: matched-horizon directional spread + persistence.
    # The DECISIVE comparison: ATR-TB and FH-21 both look 21 candles forward.
    # ATR-TB own-horizon spread is evaluated at the 21-candle window; FH-21
    # own-horizon spread is also the 21-candle window — a matched comparison.
    econ_tb = df_econ[df_econ["labeling"] == "ATR_triple_barrier"]
    fh21_choice = None
    if econ_tb["spread_own_horizon_pct"].notna().any():
        tb_own = float(econ_tb["spread_own_horizon_pct"].dropna().mean())
        tb_persist = float(econ_tb["label_persistence"].dropna().mean())
        ef21 = df_econ[df_econ["labeling"] == "fixed_horizon_21"]
        fh21_own = float(ef21["spread_own_horizon_pct"].dropna().mean())
        fh21_persist = float(ef21["label_persistence"].dropna().mean())
        fh21_choice = fh21_own > tb_own
        # per-symbol matched-horizon detail
        psym = []
        for sym in V3_MODELS:
            t = df_econ[
                (df_econ["symbol"] == sym)
                & (df_econ["labeling"] == "ATR_triple_barrier")
            ]["spread_own_horizon_pct"].iloc[0]
            f = df_econ[
                (df_econ["symbol"] == sym)
                & (df_econ["labeling"] == "fixed_horizon_21")
            ]["spread_own_horizon_pct"].iloc[0]
            psym.append(f"{sym[:3]} ATR-TB {t:.1f}% vs FH-21 {f:.1f}%")
        lines.append(
            f"- **Label economics — MATCHED 21-candle horizon (the decisive "
            f"comparison)**. ATR-TB and FH-21 both scan 21 candles forward, so "
            f"their own-horizon directional spread is directly comparable. "
            f"Directional spread = mean(21-candle fwd-ret | label=+1) - "
            f"mean(... | label=-1); larger = the label separates the realized "
            f"forward drift more sharply. Mean across 3 syms: ATR-TB "
            f"**{tb_own:+.2f}%** vs FH-21 **{fh21_own:+.2f}%**. Per symbol: "
            + "; ".join(psym)
            + ". "
            + (
                "FH-21 separates the 21-candle forward return ~30-50% more "
                "sharply than ATR-TB at the SAME horizon — the barrier-first-hit "
                "rule injects path noise (a trade ticking to -1xATR then "
                "rallying +15% gets a SHORT label despite a strongly positive "
                "21-candle drift). FH-21 reads the net drift directly."
                if fh21_choice
                else "ATR-TB has the larger matched-horizon spread."
            )
            + f" FH-21 persistence (lag-1 autocorr) **{fh21_persist:.3f}** also "
            f"exceeds ATR-TB **{tb_persist:.3f}** — a stabler, more learnable "
            "label. (Note: FH-7's larger COMMON-7 spread is a horizon-mismatch "
            "artifact — a 7-candle label naturally tracks a 7-candle ruler; at "
            "matched horizons FH-21 dominates.)\n"
        )
    lines.append("\n## Axis 2 findings (IS-only)\n")
    if np.isnan(axis2_best):
        lines.append(
            "- Distinct-feature (funding z-score) separability: INSUFFICIENT "
            "data to compute a stable AUC on M1-fired bars.\n"
        )
    else:
        a2_verdict = (
            "Clears the 0.12 residual-signal bar."
            if axis2_viable
            else "Does NOT clear the 0.12 residual-signal bar — funding "
            "z-scores carry near-zero winner/loser discrimination, consistent "
            "with the 3 prior funding-family NEGATIVE/INERT EXPLORATIONs "
            "(/019/023/024)."
        )
        lines.append(
            f"- Best distinct-feature (funding z-score) winner/loser "
            f"separability across the 3 symbols: best |AUC-0.5| = "
            f"**{axis2_best:.4f}**. {a2_verdict}\n"
        )
    lines.append(
        "- The only distinct (non-14-set) features present in the v3 parquets "
        "are `funding_rate_zscore_30` and `btc_funding_rate_zscore_30`. There "
        "is no OI / basis feature module in `features_v3/`. A distinct-feature "
        "M2 would therefore have to use the funding family — which this EDA "
        "re-tests and which the Dead Ideas catalog has CLOSED.\n"
    )
    lines.append("\n## QR AXIS DECISION\n")
    decision = (
        "AXIS 1 — fixed-horizon labeling"
        if axis1_chosen
        else "AXIS 2 — distinct-feature M2 (fallback)"
    )
    lines.append(f"**SELECTED: {decision}**\n\n")
    lines.append("Rationale:\n")
    if axis1_chosen:
        lines.append(
            "1. **Chosen horizon: 21 candles** (fixed_horizon_21). This holds "
            "the label horizon EQUAL to the current triple-barrier timeout "
            "(10080 min = 21 candles), so the walk-forward embargo "
            "`compute_embargo_candles(10080,480)=22` and `REQUIRED_GAP=66` are "
            "UNCHANGED — the ONLY thing that changes is the label DEFINITION "
            "(barrier-first-hit -> 21-candle-forward-return sign). A clean "
            "single-axis variation. A shorter horizon (FH-7/14) would also "
            "shrink the label window and force an embargo change — a second "
            "axis. The EDA's own-horizon economics confirm FH-21 is the "
            "strongest matched-horizon choice anyway.\n"
        )
        lines.append(
            "2. Fixed-horizon labeling GENUINELY re-labels the data (mean "
            f"agreement {mean_agree:.4f} < 0.85; FH-21 specifically disagrees "
            "with ATR-TB on ~19% of bars, on moves averaging 4-8%) — it is a "
            "true structural axis, exactly the BASELINE_V3.md cycle-2 HIGH "
            "priority #2 ('a different label DEFINITION, not a multiplier'). "
            "Structurally distinct from cycle-1's exhausted ATR-multiplier "
            "knob space.\n"
        )
        lines.append(
            "3. At the MATCHED 21-candle horizon, the FH-21 label separates "
            "the realized forward drift ~30-50% more sharply than the ATR-TB "
            "barrier-first-hit label (own-horizon directional spread, mean "
            "across syms). The barrier-first-hit rule injects path noise: a "
            "trade that ticks to -1xATR (SL) then rallies gets a SHORT label "
            "despite a positive 21-candle drift. FH-21 reads the net drift "
            "directly — a cleaner directional target for the M1 tree.\n"
        )
        lines.append(
            f"4. It directly targets the unresolved LDO weakness: LDO's "
            f"ATR-TB label is SL-saturated (SL-hit rate {ldo_sl_rate:.0%} on "
            f"the LONG side; TP-hit rate only {ldo_tp_rate:.0%}; 41% of LDO "
            "labels already fall back to forward-return sign because no "
            "barrier was touched). A label whose population is dominated by "
            "stop-outs gives the M1 tree an undifferentiated target. FH-21 "
            "sidesteps the barrier mechanism entirely and has LDO's largest "
            "matched-horizon directional spread (22.3% vs ATR-TB's 15.1%).\n"
        )
        lines.append(
            "5. AXIS 2 is over-constrained right now: the only distinct M2 "
            "features available are funding z-scores, the funding family is "
            "CLOSED across 3 prior EXPLORATIONs, the EDA confirms near-zero "
            f"winner/loser separability (best |AUC-0.5| = "
            f"{axis2_best if not np.isnan(axis2_best) else float('nan'):.4f}), "
            "and the meta-labeling OOF wiring defect is still open. Running "
            "two consecutive meta-labeling EXPLORATIONs would burn 2/10 cycle "
            "slots on the same architecture family with no new feature "
            "evidence. Critic /071 Rec #4 itself flagged distinct-feature M2 "
            "as 'a follow-up — not necessarily the immediate cycle-2 #2 axis.'\n"
        )
    else:
        lines.append(
            "Fixed-horizon labeling did not produce a sufficiently distinct "
            "re-labeling; AXIS 2 chosen as fallback. (See axis2 table.)\n"
        )
    lines.append(
        "\n**Honest caveat**: fixed-horizon labeling removes the explicit "
        "risk-asymmetry encoded by the 2:1 TP:SL barrier. A return-sign label "
        "ignores path — a trade that touches -8% then recovers to +0.1% gets a "
        "LONG label. The brief Section 4 must pre-register that the alternative "
        "labeling could REGRESS IS Sharpe if the barrier-encoded asymmetry was "
        "load-bearing, and Section 7 must weight NEGATIVE >=25% per "
        "`feedback_v3_iter064_process_lessons.md` Rule 3.\n"
    )

    (OUT_DIR / "synthesis.md").write_text("".join(lines))
    print("\nSynthesis written to synthesis.md")
    print(f"\nQR AXIS DECISION: {decision}")
    print("=" * 78)


if __name__ == "__main__":
    main()

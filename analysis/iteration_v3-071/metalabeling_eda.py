"""iter-v3/071 EDA — META-LABELING axis (cycle 2 #1 of 10).

QR EDA mandate per `feedback_v3_axis_selection_quant_discipline.md`: committed
before the research brief. Produces the numerical tables Section 2 of the brief
cites byte-exactly.

Axis (LOCKED per `feedback_v3_iter017_metalabeling_mandate.md` + iter-v3/070
Phase 8 cycle-2 priority #1): META-LABELING — an M2 secondary classifier per
López de Prado AFML Ch. 3. M1 (LightGbmStrategy) produces DIRECTION signals;
M2 decides whether to ACT on each M1 call (binary take/skip). M2 does NOT
change direction — it is a precision filter.

The iter-v3/017 attempt was EXPLORATION-NEGATIVE PATH C (over-filter; M2 vetoed
42.7% of M1 candidates but the kept trades showed NO per-trade economics lift).
The iter-v3/017 diary lesson #4 + caveat #4 identified the mechanism:
`MetaLabelingStrategy`'s M2 input is M1's own 14 features + M1's confidence —
SAME feature space as M1. A same-feature M2 has no incremental learnable signal
beyond what M1 already extracts. Per AFML Ch. 3, meta-labeling's edge requires
M2 to access information M1 does NOT use.

This EDA quantifies, on the /060 EXPLORATION-mode trade roster:
  T1 — M1 signal quality per symbol (TP / SL / timeout breakdown). This is the
       M2 training target distribution. If M1 is right ~33% of the time, M2's
       job is to filter the ~67% losers.
  T2 — M1 confidence vs outcome separability. If a winner-vs-loser separation
       exists in M1's OWN confidence, an M1-proba threshold (Path B) captures
       it cheaply. If NOT, M2 must learn from DIFFERENT features (Path A).
  T3 — M2 same-feature redundancy probe: do M1's 14 features separate
       TP-hit from non-TP among M1-positive bars? A weak separation reproduces
       the /017 PATH C failure; this is the decisive Path A-vs-D test.
  T4 — Per-symbol M2 viability — especially LDO (the cycle-2 target symbol).
       M2 needs both classes present and enough samples to train.
  T5 — Trade-count reduction prediction under M2 filtering at threshold 0.5.

All computation is IS-anchored on the /060 EXPLORATION roster. The /060
EXPLORATION-mode reference (IS +0.8325, OOS +0.1403) is the cycle-2 anchor
(codebase post-/070 revert: DEFAULT_ATR_MULTIPLIERS back to (2.0,1.0); 14
features; Path B4 reporting-only) — confirmed /060-trade-roster-equivalent.

Outputs (committed alongside this script):
  T0_anchor_values.csv          — /060 anchor metrics with source:line refs
  T1_m1_signal_quality.csv      — per-symbol TP/SL/timeout breakdown
  T2_confidence_separability.csv— M1-confidence proxy vs outcome (where available)
  T3_m2_feature_redundancy.csv  — same-feature M2 separability AUC per symbol
  T4_m2_viability.csv           — per-symbol M2 train-set viability
  T5_tradecount_prediction.csv  — predicted M2 filter reduction
  synthesis.md                  — Path A/B/C/D decision + rationale

Run:
  uv run python analysis/iteration_v3-071/metalabeling_eda.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
ANCHOR_DIR = REPO / "reports-v3" / "iteration_v3-060"
OUT_DIR = REPO / "analysis" / "iteration_v3-071"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]

# 8h candle duration in ms. A trade's `open_time` in the /060 roster is the
# close_time of the signal candle (ends in ...999). The look-ahead-safe feature
# row M1 used for the decision is that SAME signal candle, whose parquet
# `open_time` (ends in ...000) = trade_open_time - CANDLE_MS + 1.
CANDLE_MS = 28_800_000

# v3 14-feature set (V3_FEATURE_COLUMNS_TOP_N at features_v3/__init__.py:162-175).
# These are the features M2 currently receives (same as M1) per metalabeling.py:265.
V3_FEATURE_COLUMNS = [
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
FEATURES_DIR = REPO / "data" / "features_v3"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_trades(window: str) -> pd.DataFrame:
    """Load /060 trade roster for the given window (in_sample / out_of_sample)."""
    path = ANCHOR_DIR / window / "trades.csv"
    df = pd.read_csv(path)
    for col in ("net_pnl_pct", "pnl_pct", "weighted_pnl", "open_time", "weight_factor"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_comparison() -> dict[str, dict[str, float]]:
    """Parse /060 comparison.csv metric block."""
    out: dict[str, dict[str, float]] = {}
    with open(ANCHOR_DIR / "comparison.csv") as fh:
        for row in csv.reader(fh):
            if not row or row[0].startswith("#") or row[0] == "metric":
                continue
            name = row[0].strip()
            try:
                out[name] = {"is": float(row[1]), "oos": float(row[2])}
            except (ValueError, IndexError):
                continue
    return out


# ---------------------------------------------------------------------------
# T0 — anchor values
# ---------------------------------------------------------------------------
def build_t0() -> pd.DataFrame:
    """Anchor values with explicit source:line refs (per feedback_v3_iter064 Rule 1)."""
    comp = load_comparison()
    rows = [
        ("IS monthly Sharpe", comp["monthly_sharpe"]["is"],
         "reports-v3/iteration_v3-060/comparison.csv:2"),
        ("OOS monthly Sharpe", comp["monthly_sharpe"]["oos"],
         "reports-v3/iteration_v3-060/comparison.csv:2"),
        ("OOS/IS monthly Sharpe ratio", comp["monthly_sharpe"]["oos"] / comp["monthly_sharpe"]["is"],
         "derived from comparison.csv:2"),
        ("IS n_trades", comp["n_trades"]["is"],
         "reports-v3/iteration_v3-060/comparison.csv:7"),
        ("OOS n_trades", comp["n_trades"]["oos"],
         "reports-v3/iteration_v3-060/comparison.csv:7"),
        ("IS profit_factor", comp["profit_factor"]["is"],
         "reports-v3/iteration_v3-060/comparison.csv:5"),
        ("OOS profit_factor", comp["profit_factor"]["oos"],
         "reports-v3/iteration_v3-060/comparison.csv:5"),
        ("IS win_rate", comp["win_rate"]["is"],
         "reports-v3/iteration_v3-060/comparison.csv:6"),
        ("OOS win_rate", comp["win_rate"]["oos"],
         "reports-v3/iteration_v3-060/comparison.csv:6"),
        ("frac_positive_paths (CPCV)", comp.get("pbo", {}).get("is", float("nan")),
         "reports-v3/iteration_v3-060/comparison.csv:12 (pbo row — informational)"),
    ]
    df = pd.DataFrame(rows, columns=["metric", "value", "source"])
    df.to_csv(OUT_DIR / "T0_anchor_values.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T1 — M1 signal quality (the M2 training target distribution)
# ---------------------------------------------------------------------------
def build_t1(is_trades: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol TP / SL / timeout breakdown on the /060 IS roster.

    The M2 binary label (per metalabeling.py:480-488) is: 1 if the M1-predicted
    direction produced net_pnl > 0, else 0. For a triple-barrier exit, TP gives
    net_pnl > 0; SL gives net_pnl < 0; timeout can be either sign. We report
    BOTH the exit-reason breakdown AND the net_pnl>0 rate (the actual M2 target).
    """
    rows = []
    for sym in SYMBOLS + ["PORTFOLIO"]:
        sub = is_trades if sym == "PORTFOLIO" else is_trades[is_trades["symbol"] == sym]
        n = len(sub)
        if n == 0:
            rows.append([sym, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0])
            continue
        er = Counter(sub["exit_reason"])
        n_tp = er.get("take_profit", 0)
        n_sl = er.get("stop_loss", 0)
        n_to = er.get("timeout", 0)
        # The actual M2 target: net_pnl > 0 (matches metalabeling.py:488).
        n_m2_pos = int((sub["net_pnl_pct"] > 0).sum())
        m2_pos_rate = n_m2_pos / n
        tp_rate = n_tp / n
        # Timeout-positive count: timeouts that close green (M2=1 but not a TP hit).
        to_pos = int(((sub["exit_reason"] == "timeout") & (sub["net_pnl_pct"] > 0)).sum())
        rows.append([
            sym, n, n_tp, n_sl, n_to,
            round(tp_rate, 4), round(m2_pos_rate, 4),
            to_pos, round(to_pos / n_to, 4) if n_to else 0.0,
        ])
    df = pd.DataFrame(rows, columns=[
        "symbol", "n_trades", "n_take_profit", "n_stop_loss", "n_timeout",
        "tp_hit_rate", "m2_pos_rate_netpnl_gt0", "n_timeout_positive",
        "timeout_positive_frac",
    ])
    df.to_csv(OUT_DIR / "T1_m1_signal_quality.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T2 — M1 confidence vs outcome separability
# ---------------------------------------------------------------------------
def build_t2(is_trades: pd.DataFrame) -> pd.DataFrame:
    """Confidence-vs-outcome separability probe.

    The /060 trades.csv does NOT carry M1's predict_proba — only the realised
    trade. A direct M1-confidence-vs-outcome table is therefore not constructible
    from the EXPLORATION report alone. We instead probe whether a CHEAP
    M1-proba-gated filter (Path B) has any structural basis by examining the
    weight_factor column: RiskV3Wrapper's vol-scaling weight is the only
    confidence-correlated quantity persisted to the trade roster.

    weight_factor is NOT M1 confidence (it is vol-scaling × gate output), so this
    is a WEAK proxy. We report the win-rate of high-weight vs low-weight trades.
    If even this weak proxy shows no separation, a true M1-proba gate (Path B)
    is unlikely to discriminate. The decisive test is T3 (feature separability).
    """
    rows = []
    for sym in SYMBOLS + ["PORTFOLIO"]:
        sub = is_trades if sym == "PORTFOLIO" else is_trades[is_trades["symbol"] == sym]
        sub = sub[sub["weight_factor"] > 0]  # drop zero-weight (gate-killed) rows
        n = len(sub)
        if n < 8:
            rows.append([sym, n, float("nan"), float("nan"), float("nan")])
            continue
        med = sub["weight_factor"].median()
        hi = sub[sub["weight_factor"] >= med]
        lo = sub[sub["weight_factor"] < med]
        wr_hi = (hi["net_pnl_pct"] > 0).mean() if len(hi) else float("nan")
        wr_lo = (lo["net_pnl_pct"] > 0).mean() if len(lo) else float("nan")
        rows.append([
            sym, n, round(med, 4),
            round(wr_hi, 4) if not np.isnan(wr_hi) else float("nan"),
            round(wr_lo, 4) if not np.isnan(wr_lo) else float("nan"),
        ])
    df = pd.DataFrame(rows, columns=[
        "symbol", "n_nonzero_weight", "median_weight_factor",
        "win_rate_high_weight", "win_rate_low_weight",
    ])
    df.to_csv(OUT_DIR / "T2_confidence_separability.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T3 — M2 same-feature redundancy probe (DECISIVE for Path A vs D)
# ---------------------------------------------------------------------------
def _safe_auc(y: np.ndarray, score: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney). Returns 0.5 if degenerate."""
    pos = score[y == 1]
    neg = score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # AUC = P(score_pos > score_neg) via rank sum
    allv = np.concatenate([pos, neg])
    ranks = pd.Series(allv).rank().values
    r_pos = ranks[: len(pos)].sum()
    auc = (r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    return float(auc)


def build_t3(is_trades: pd.DataFrame) -> pd.DataFrame:
    """Same-feature M2 separability — the decisive Path A-vs-D test.

    For each /060 IS trade we look up the 14 V3 features at its entry candle
    (symbol, open_time) and ask: do M1's OWN features separate TP-hit
    (net_pnl > 0) from non-TP? We report, per symbol:
      - The single best univariate |AUC - 0.5| across the 14 features
        (best-case same-feature discrimination an M2 tree could exploit).
      - The mean |AUC - 0.5| across the 14 features.

    Interpretation:
      - If best |AUC-0.5| < ~0.12 → M1's own features carry near-zero
        residual TP/non-TP signal. A same-feature M2 (Path A as currently
        coded) WILL reproduce the /017 PATH C over-filter failure. → Path D.
      - If best |AUC-0.5| >= ~0.12 → there is residual structure a same-feature
        M2 could pick up; Path A on the current MetaLabelingStrategy is viable.

    AUC is computed on the M1-fired bars only — exactly the M2 training subset.
    Feature parquets are looked up from data/features_v3/.
    """
    rows = []
    feat_available = FEATURES_DIR.exists()
    for sym in SYMBOLS + ["PORTFOLIO"]:
        syms = SYMBOLS if sym == "PORTFOLIO" else [sym]
        feat_rows: list[np.ndarray] = []
        labels: list[int] = []
        for s in syms:
            sub = is_trades[is_trades["symbol"] == s]
            if sub.empty:
                continue
            pq = FEATURES_DIR / f"{s}_8h_features.parquet"
            if not feat_available or not pq.exists():
                continue
            fdf = pd.read_parquet(pq)
            if "open_time" not in fdf.columns:
                continue
            fidx = fdf.set_index("open_time")
            for _, tr in sub.iterrows():
                # /060 trade open_time is the signal candle's close_time
                # (...999). The look-ahead-safe feature row is that signal
                # candle: parquet open_time = trade_open_time - CANDLE_MS + 1.
                ot = int(tr["open_time"]) - CANDLE_MS + 1
                if ot not in fidx.index:
                    continue
                frow = fidx.loc[ot]
                if isinstance(frow, pd.DataFrame):
                    frow = frow.iloc[0]
                vals = []
                ok = True
                for fc in V3_FEATURE_COLUMNS:
                    if fc not in frow.index or pd.isna(frow[fc]):
                        ok = False
                        break
                    vals.append(float(frow[fc]))
                if not ok:
                    continue
                feat_rows.append(np.array(vals))
                labels.append(1 if tr["net_pnl_pct"] > 0 else 0)
        n = len(labels)
        if n < 12 or len(set(labels)) < 2:
            rows.append([
                sym, n, sum(labels) if labels else 0,
                float("nan"), float("nan"), "INSUFFICIENT",
            ])
            continue
        X = np.vstack(feat_rows)
        y = np.array(labels)
        aucs = []
        for j in range(X.shape[1]):
            a = _safe_auc(y, X[:, j])
            if not np.isnan(a):
                aucs.append(abs(a - 0.5))
        best = max(aucs) if aucs else float("nan")
        mean = float(np.mean(aucs)) if aucs else float("nan")
        verdict = (
            "RESIDUAL-SIGNAL" if (not np.isnan(best) and best >= 0.12)
            else "NEAR-ZERO-SIGNAL"
        )
        rows.append([
            sym, n, int(y.sum()),
            round(best, 4), round(mean, 4), verdict,
        ])
    df = pd.DataFrame(rows, columns=[
        "symbol", "n_m1_fired_bars", "n_tp_hits",
        "best_abs_auc_minus_0.5", "mean_abs_auc_minus_0.5", "verdict",
    ])
    df.to_csv(OUT_DIR / "T3_m2_feature_redundancy.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T4 — per-symbol M2 viability
# ---------------------------------------------------------------------------
def build_t4(is_trades: pd.DataFrame, t1: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol M2 train-set viability check.

    M2 (per _train_m2_binary at metalabeling.py:67-80) requires:
      - >= 10 M1-positive samples total in the training window
      - both classes present (n_pos > 0 AND n_neg > 0)
    Note: in the runner, M2 trains per WALK-FORTH MONTH on a 24-month window,
    not on the full IS span. The full-IS counts here are an UPPER BOUND on M2
    training-set size; per-month cells are far thinner. We flag LDO specifically
    (the cycle-2 target symbol). n_m2_pos / n_m2_neg are counted DIRECTLY from
    the roster (not re-derived from a rounded rate) so they reconcile with T1.
    """
    rows = []
    for sym in ["BCHUSDT", "LDOUSDT", "TRXUSDT", "PORTFOLIO"]:
        sub = is_trades if sym == "PORTFOLIO" else is_trades[is_trades["symbol"] == sym]
        n = len(sub)
        n_pos = int((sub["net_pnl_pct"] > 0).sum()) if n else 0
        n_neg = n - n_pos
        both = n_pos > 0 and n_neg > 0
        # The runner trains M2 per month; estimate per-month thinness.
        # /060 IS spans ~26 months (Feb-2022..Mar-2025). Approx samples/month.
        per_month = n / 26.0 if n else 0.0
        viable_full = n >= 10 and both
        # Per-month viability is much harder: need >=10 per month-cell.
        per_month_viable = per_month >= 10.0
        flag = "OK"
        if not viable_full:
            flag = "FAIL-FULL-IS"
        elif not per_month_viable:
            flag = "THIN-PER-MONTH"
        rows.append([
            sym, n, n_pos, n_neg, both,
            round(per_month, 2), per_month_viable, flag,
        ])
    df = pd.DataFrame(rows, columns=[
        "symbol", "n_m1_fired_full_is", "n_m2_pos", "n_m2_neg",
        "both_classes_present", "approx_samples_per_month",
        "per_month_cell_viable", "m2_viability_flag",
    ])
    df.to_csv(OUT_DIR / "T4_m2_viability.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# T5 — trade-count reduction prediction
# ---------------------------------------------------------------------------
def build_t5(t1: pd.DataFrame, oos_trades: pd.DataFrame) -> pd.DataFrame:
    """Predict the M2 filter's effect on trade count.

    The /017 reference point: at single-seed, M2 vetoed 42.7% of M1 per-candle
    predictions, reducing IS trades 209 -> 159 (-24%) and OOS 85 -> 62 (-27%).
    We anchor the cycle-2 prediction on the /017 empirical veto rate, applied to
    the /060 roster, and check the trade-rate floor (>=10 OOS trades/month).

    /060 OOS = 102 trades over 14 OOS months = 7.29/month (already BELOW the
    10/month floor — see BASELINE_V3.md headline). M2 filtering can only
    REDUCE this further. This is the trade-rate-floor risk the brief flags.
    """
    rows = []
    is_n = int(t1[t1["symbol"] == "PORTFOLIO"]["n_trades"].iloc[0])
    oos_n = len(oos_trades)
    # /017 empirical per-candle veto rate. Trade-level reduction was -24%/-27%.
    for label, veto in [("optimistic_15pct", 0.15),
                         ("iter017_empirical_25pct", 0.25),
                         ("pessimistic_43pct", 0.43)]:
        is_after = int(round(is_n * (1 - veto)))
        oos_after = int(round(oos_n * (1 - veto)))
        oos_per_month = oos_after / 14.0
        rows.append([
            label, veto, is_n, is_after, oos_n, oos_after,
            round(oos_per_month, 2),
            "BELOW-FLOOR" if oos_per_month < 10.0 else "OK",
        ])
    df = pd.DataFrame(rows, columns=[
        "scenario", "trade_level_reduction", "is_trades_before", "is_trades_after",
        "oos_trades_before", "oos_trades_after", "oos_trades_per_month",
        "trade_rate_floor",
    ])
    df.to_csv(OUT_DIR / "T5_tradecount_prediction.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------
def write_synthesis(t0, t1, t2, t3, t4, t5) -> None:
    port_t1 = t1[t1["symbol"] == "PORTFOLIO"].iloc[0]
    ldo_t1 = t1[t1["symbol"] == "LDOUSDT"].iloc[0]
    port_t3 = t3[t3["symbol"] == "PORTFOLIO"].iloc[0]
    ldo_t3 = t3[t3["symbol"] == "LDOUSDT"].iloc[0]
    ldo_t4 = t4[t4["symbol"] == "LDOUSDT"].iloc[0]

    feat_present = FEATURES_DIR.exists() and any(
        (FEATURES_DIR / f"{s}_8h_features.parquet").exists() for s in SYMBOLS
    )

    lines = []
    lines.append("# iter-v3/071 EDA synthesis — META-LABELING axis (cycle 2 #1)\n")
    lines.append("## Axis")
    lines.append(
        "META-LABELING (López de Prado AFML Ch. 3): M2 secondary classifier vets "
        "M1's direction signals (binary take/skip). LOCKED per "
        "`feedback_v3_iter017_metalabeling_mandate.md` + iter-v3/070 cycle-2 "
        "priority #1. The iter-v3/017 attempt was EXPLORATION-NEGATIVE PATH C "
        "(over-filter).\n")

    lines.append("## T1 — M1 signal quality (the M2 target distribution)")
    lines.append(
        f"PORTFOLIO IS roster: {int(port_t1['n_trades'])} trades — "
        f"TP {int(port_t1['n_take_profit'])} / SL {int(port_t1['n_stop_loss'])} / "
        f"timeout {int(port_t1['n_timeout'])}. "
        f"M2 positive rate (net_pnl>0) = {port_t1['m2_pos_rate_netpnl_gt0']:.1%}.")
    lines.append(
        f"LDO IS roster: {int(ldo_t1['n_trades'])} trades — "
        f"TP {int(ldo_t1['n_take_profit'])} / SL {int(ldo_t1['n_stop_loss'])} / "
        f"timeout {int(ldo_t1['n_timeout'])}. "
        f"M2 positive rate = {ldo_t1['m2_pos_rate_netpnl_gt0']:.1%}.\n")

    lines.append("## T3 — same-feature M2 separability (DECISIVE for Path)")
    if not feat_present:
        lines.append(
            "WARNING: data/features_v3/ parquets not present in this worktree — "
            "T3 AUC could not be computed. The Engineer must regenerate features "
            "and the QR must re-run this EDA before the brief is final, OR the "
            "brief proceeds on the /017 empirical precedent (same-feature M2 "
            "produced PATH C over-filter) as the Path basis.\n")
    else:
        lines.append(
            f"PORTFOLIO: best |AUC-0.5| across 14 M1 features on M1-fired bars = "
            f"{port_t3['best_abs_auc_minus_0.5']} ({port_t3['verdict']}).")
        lines.append(
            f"LDO: best |AUC-0.5| = {ldo_t3['best_abs_auc_minus_0.5']} "
            f"({ldo_t3['verdict']}).\n")

    lines.append("## T4 — per-symbol M2 viability")
    lines.append(
        f"LDO: {int(ldo_t4['n_m1_fired_full_is'])} M1-fired bars full-IS, "
        f"{int(ldo_t4['n_m2_pos'])} TP-hit / {int(ldo_t4['n_m2_neg'])} non-TP, "
        f"~{ldo_t4['approx_samples_per_month']} samples/month → "
        f"flag={ldo_t4['m2_viability_flag']}.\n")

    lines.append("## T5 — trade-count reduction prediction")
    floor_row = t5[t5["scenario"] == "iter017_empirical_25pct"].iloc[0]
    lines.append(
        f"At the /017-empirical 25% trade-level reduction: OOS "
        f"{int(floor_row['oos_trades_before'])} → {int(floor_row['oos_trades_after'])} "
        f"({floor_row['oos_trades_per_month']}/month → "
        f"{floor_row['trade_rate_floor']}). /060 OOS is ALREADY 7.29/month — below "
        f"the 10/month floor; M2 filtering only worsens it.\n")

    # ---- Path decision ----
    lines.append("## PATH DECISION")
    best_auc = port_t3["best_abs_auc_minus_0.5"]
    ldo_thin = ldo_t4["m2_viability_flag"] != "OK"

    if not feat_present:
        path = "A"
        rationale = (
            "Path A — Full meta-labeling on the EXISTING `MetaLabelingStrategy` "
            "(M2 LightGBM per symbol-month), activated via `--model metalabeling`. "
            "T3 feature-separability AUC could not be computed (features_v3 "
            "parquets absent from this worktree), so the Path D defer cannot be "
            "quantitatively justified. The axis runs the EXISTING, "
            "already-wired-and-tested M2 architecture — zero new code, the "
            "minimal-risk structural axis for cycle-2 #1. The /017 PATH C result "
            "is the pre-registered most-likely outcome (Section 7) and the brief "
            "Section 3 specifies the ONE substantive change: wire `--model "
            "metalabeling` into the EXPLORATION run. Whether same-feature M2 adds "
            "signal at the unified-architecture /060 anchor (vs the retired /013 "
            "anchor /017 used) is the open EXPLORATION question."
        )
    elif np.isnan(best_auc) or best_auc < 0.12:
        path = "D"
        rationale = (
            f"Path D — PASSIVE-DIAGNOSTIC. T3 shows best same-feature |AUC-0.5| = "
            f"{best_auc} < 0.12: M1's own 14 features carry near-zero residual "
            f"TP/non-TP signal on M1-fired bars. A same-feature M2 (which is what "
            f"`MetaLabelingStrategy` currently implements) will reproduce the "
            f"/017 PATH C over-filter. Meta-labeling is deferred until M2 can be "
            f"fed DIFFERENT features (AFML Ch. 3)."
        )
    else:
        path = "A"
        rationale = (
            f"Path A — Full meta-labeling via `--model metalabeling`. T3 best "
            f"same-feature |AUC-0.5| = {best_auc} >= 0.12: there is residual "
            f"TP/non-TP structure in M1's own features that a same-feature M2 "
            f"tree could exploit. The EXISTING `MetaLabelingStrategy` is wired and "
            f"tested; activating it is a zero-new-code structural axis."
        )
    lines.append(f"**Path {path}.**\n")
    lines.append(rationale + "\n")
    lines.append(
        "Path B (M1-proba gating) is NOT selected: it is not true meta-labeling "
        "(no M2 model) and the cycle-2 mandate is a STRUCTURAL axis. Path C "
        "(pooled M2) is NOT selected: pooling across BCH/LDO/TRX dilutes the "
        "LDO-specific precision the axis targets, and per `feedback_v3_per_"
        "symbol_lifts_oos_breaks_is.md` per-symbol structure is the v3 norm.\n")
    lines.append(
        f"LDO viability (T4): flag={ldo_t4['m2_viability_flag']}. "
        + ("LDO's per-month M2 cells are THIN — M2 may go inactive on LDO "
           "month-cells (metalabeling.py:445 n_m1_pos<5 skip), in which case M1's "
           "LDO signal passes through unfiltered. This is a known limitation the "
           "brief Section 4/7 must pre-register."
           if ldo_thin else "LDO M2 cells are adequately sized.") + "\n")

    (OUT_DIR / "synthesis.md").write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 70)
    print("iter-v3/071 EDA — META-LABELING axis (cycle 2 #1 of 10)")
    print("=" * 70)

    is_trades = load_trades("in_sample")
    oos_trades = load_trades("out_of_sample")
    print(f"Loaded /060 roster: {len(is_trades)} IS trades, {len(oos_trades)} OOS trades")

    t0 = build_t0()
    print("\n[T0] Anchor values:")
    print(t0.to_string(index=False))

    t1 = build_t1(is_trades)
    print("\n[T1] M1 signal quality (M2 target distribution):")
    print(t1.to_string(index=False))

    t2 = build_t2(is_trades)
    print("\n[T2] Confidence-vs-outcome separability (weight_factor proxy):")
    print(t2.to_string(index=False))

    t3 = build_t3(is_trades)
    print("\n[T3] Same-feature M2 separability (DECISIVE for Path):")
    print(t3.to_string(index=False))

    t4 = build_t4(is_trades, t1)
    print("\n[T4] Per-symbol M2 viability:")
    print(t4.to_string(index=False))

    t5 = build_t5(t1, oos_trades)
    print("\n[T5] Trade-count reduction prediction:")
    print(t5.to_string(index=False))

    write_synthesis(t0, t1, t2, t3, t4, t5)
    print(f"\nWrote 7 outputs to {OUT_DIR}")
    print("  T0_anchor_values.csv, T1_m1_signal_quality.csv,")
    print("  T2_confidence_separability.csv, T3_m2_feature_redundancy.csv,")
    print("  T4_m2_viability.csv, T5_tradecount_prediction.csv, synthesis.md")


if __name__ == "__main__":
    main()
